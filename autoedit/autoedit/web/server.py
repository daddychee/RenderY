"""Bảng điều khiển RenderY — xem trạng thái + chạy pipeline từ trình duyệt.

KHÔNG dựng lại hàng đợi job: `project.json` ĐÃ là hàng đợi bền (StageRecord ghi
status/started_at/completed_at/error xuống đĩa, `run` tự bỏ qua stage đã DONE).
Server này chỉ đọc file đó và gọi lại CLI có sẵn — tắt server giữa chừng thì lần
sau chạy tiếp từ đúng stage đang dở.

Job chạy trong thread riêng + ghi log ra file, nên đóng trình duyệt không giết job.

⚠ Bind 0.0.0.0 = mọi máy trong LAN vào được, mà trang Cài đặt ĐỌC/GHI .env chứa
API key. Đặt RENDERY_WEB_TOKEN trong .env để bật xác thực (khuyến nghị khi mở LAN).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]      # thư mục autoedit/ (chứa .env, projects/)
PROJECTS_DIR = ROOT / "projects"
JOBS_DIR = ROOT / ".web_jobs"

# Gốc NAS. Nhân sự DÁN đường dẫn thư mục tập (mỗi tập một mã: LI001, SH042, IN002...)
# nằm rải theo series, nên không cố định được một INBOX. Chỉ chặn: đường dẫn phải
# NẰM TRONG gốc này — ngoài ra là tuỳ ý.
NAS_ROOT = Path(os.getenv("RENDERY_NAS", r"F:\OutlierY Nas 2"))
# Kết quả giao ngay trong thư mục tập (`<tập>/RenderY/Compose Timeline/`) để nhân sự
# copy cả cụm về máy — xem compose.thu_muc_giao().
OUTBOX_TEN = "Compose Timeline"

# Key được phép sửa qua web. Whitelist: tránh ai đó ghi biến lạ vào .env.
SETTINGS_KEYS = [
    "PEXELS_API_KEY", "PIXABAY_API_KEY",
    "ENVATO_EMAIL", "VECTEEZY_EMAIL",
    "GLM_API_KEY", "ANTHROPIC_API_KEY", "SERPER_API_KEY",
    "RENDERY_WEB_TOKEN",
]
SECRET_KEYS = {k for k in SETTINGS_KEYS if k.endswith(("_KEY", "_TOKEN"))}

@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Khởi động worker nền + trả job mồ côi về hàng đợi."""
    from autoedit.web import worker

    n = worker.start(ROOT, JOBS_DIR, ROOT / "jobs.db")
    print(f"[queue] {n} worker sẵn sàng · NAS: {NAS_ROOT}", flush=True)
    yield
    worker.stop()


app = FastAPI(title="RenderY", lifespan=_lifespan)
_jobs: dict[str, dict] = {}          # project_id -> {status, stage, started_at, log}
_jobs_lock = threading.Lock()


# ------------------------------ xác thực ------------------------------------
def _require_auth(request: Request) -> None:
    """Bật khi có RENDERY_WEB_TOKEN. Không đặt = mở (hợp lý khi bind 127.0.0.1).

    Request ĐI QUA CRM đã được CRM xác thực (session cookie ký số + phân quyền
    app theo bộ phận×level) — không đòi token nữa, vì trong iframe của CRM thì
    query `?token=` không tồn tại và người dùng cũng không có gì để nhập.
    """
    token = os.getenv("RENDERY_WEB_TOKEN", "").strip()
    # Miễn token cho request ĐI QUA CRM — nhận ra bằng X-Forwarded-Host (CRM luôn gửi),
    # KHÔNG phải chỉ vì client là loopback: mọi thứ chạy trên máy chủ đều loopback,
    # miễn theo loopback là mở toang cho bất kỳ tiến trình nào trên máy.
    if not token or behind_crm(request):
        return
    sent = request.headers.get("x-rendery-token") or request.query_params.get("token", "")
    if sent != token:
        raise HTTPException(401, "Sai hoặc thiếu token (đặt RENDERY_WEB_TOKEN trong .env)")


def _loopback(request: Request) -> bool:
    host = (request.client.host if request.client else "") or ""
    return host in ("127.0.0.1", "::1", "localhost")


def _trust_proxy(request: Request) -> bool:
    """Có được tin header danh tính không?

    CHỈ TIN khi bật cờ VÀ client là loopback — CRM proxy từ 127.0.0.1 và đã tự loại
    header giả mạo (`app_proxy.py:48` vứt x-remote-user/role do người dùng gửi lên).
    Truy cập thẳng từ LAN không qua CRM thì header do người gọi tự đặt, không tin được.
    """
    return os.getenv("RENDERY_TRUST_PROXY", "").strip() == "1" and _loopback(request)


def current_user(request: Request) -> str:
    """Tên nhân sự từ SSO của CRM OUTLIERY (header X-Remote-User).

    CRM gửi tên đã CHUẨN HOÁ ASCII ("Nguyễn Văn A" -> "nguyenvana", app_proxy.py:58)
    vì header HTTP không nhận tiếng Việt có dấu. Đây là danh tính RenderY dùng để
    tách job giữa các nhân sự.
    """
    if _trust_proxy(request):
        return (request.headers.get("x-remote-user") or "").strip()
    return ""


def current_role(request: Request) -> str:
    """Vai từ CRM qua X-Remote-Role.

    OUTLIERY-V3 (`nen/iam/iam.py:vai_cho_app`) trả: admin | manager | leader | viewer
    — SUY TỪ HÀNH ĐỘNG user được phép, không map theo tên. Hệ cũ dùng 'owner'.
    """
    if _trust_proxy(request):
        return (request.headers.get("x-remote-role") or "").strip().lower()
    return ""


# Vai được xem/huỷ việc của MỌI người. 'admin' là V3; 'owner' giữ cho hệ cũ và
# cho lúc chạy trực tiếp không qua cổng.
_VAI_TOAN_QUYEN = {"admin", "owner"}


def is_admin(request: Request) -> bool:
    return current_role(request) in _VAI_TOAN_QUYEN


def behind_crm(request: Request) -> bool:
    """Đang chạy sau reverse proxy của CRM OUTLIERY?

    CRM gửi X-Forwarded-Host (app_proxy.py:126) — dùng để biết mình đang nhúng chứ
    KHÔNG tự dựng tiền tố URL: CRM đã viết lại mọi đường dẫn tuyệt đối trong HTML/JS
    thành `/app/<slug>/...` cho các tiền tố app khai trong `tien_to` (app_proxy.py:74).
    Trang chỉ cần dùng đường dẫn tuyệt đối `/api/...` là CRM lo phần còn lại.
    """
    return bool(request.headers.get("x-forwarded-host")) and _trust_proxy(request)


# ------------------------------ đọc project ---------------------------------
def _read_project(pdir: Path) -> Optional[dict]:
    """Tóm tắt 1 project cho danh sách. None nếu project.json hỏng/thiếu."""
    f = pdir / "project.json"
    if not f.is_file():
        return None
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    stages = d.get("stages") or {}
    done = sum(1 for s in stages.values() if s.get("status") == "done")
    failed = [k for k, s in stages.items() if s.get("status") == "failed"]
    warns = [w for s in stages.values() for w in (s.get("warnings") or [])]
    return {
        "project_id": d.get("project_id", pdir.name),
        "title": d.get("title", ""),
        "created_at": d.get("created_at", ""),
        "dir": str(pdir),
        "stages": {k: {"status": v.get("status", "pending"), "error": v.get("error"),
                       "warnings": v.get("warnings") or []}
                   for k, v in stages.items()},
        "done": done,
        "total": len(stages),
        "failed": failed,
        "warnings": warns,
        "draft_path": d.get("draft_path") or "",
        "report_path": d.get("report_path") or "",
        "beats": len(d.get("beats") or []),
        "shots": len(d.get("shots") or []),
    }


def _list_projects() -> list[dict]:
    if not PROJECTS_DIR.is_dir():
        return []
    out = []
    for pdir in sorted(PROJECTS_DIR.iterdir(), reverse=True):
        if pdir.is_dir():
            info = _read_project(pdir)
            if info:
                out.append(info)
    return out


# ------------------------------ chạy job ------------------------------------
def _run_job(project_id: str, args: list[str]) -> None:
    """Chạy CLI trong tiến trình con, log ra file. Chạy trong thread riêng."""
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = JOBS_DIR / f"{project_id}.log"
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    try:
        with open(log_path, "w", encoding="utf-8") as log:
            proc = subprocess.run([sys.executable, "-m", "autoedit.cli"] + args,
                                  cwd=str(ROOT), env=env, stdout=log,
                                  stderr=subprocess.STDOUT, text=True)
        ok = proc.returncode == 0
    except Exception as exc:                       # lỗi spawn — vẫn phải cập nhật trạng thái
        ok = False
        log_path.write_text(f"Không chạy được: {exc}\n", encoding="utf-8")
    with _jobs_lock:
        job = _jobs.get(project_id)
        if job is not None:
            job["status"] = "done" if ok else "failed"
            job["finished_at"] = datetime.now(timezone.utc).isoformat()


def _start_job(project_id: str, args: list[str]) -> dict:
    with _jobs_lock:
        cur = _jobs.get(project_id)
        if cur and cur["status"] == "running":
            raise HTTPException(409, f"{project_id} đang chạy — đợi xong hoặc xem log")
        job = {"status": "running", "args": args, "log": f"{project_id}.log",
               "started_at": datetime.now(timezone.utc).isoformat(), "finished_at": None}
        _jobs[project_id] = job
    threading.Thread(target=_run_job, args=(project_id, args), daemon=True).start()
    return job


# ------------------------------ .env ----------------------------------------
def _env_path() -> Path:
    return ROOT / ".env"


def _read_env() -> dict[str, str]:
    p = _env_path()
    if not p.is_file():
        return {}
    out: dict[str, str] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip()
    return out


def _write_env(updates: dict[str, str]) -> list[str]:
    """Ghi .env: sửa dòng có sẵn, thêm dòng mới, GIỮ NGUYÊN mọi dòng khác + comment.

    Ghi atomic (temp + replace): .env chứa mọi API key, crash giữa chừng là mất sạch.
    """
    p = _env_path()
    lines = p.read_text(encoding="utf-8").splitlines() if p.is_file() else []
    saved: list[str] = []
    for key, val in updates.items():
        if key not in SETTINGS_KEYS:
            continue                                  # whitelist: bỏ key lạ
        if "\n" in val or "\r" in val:
            continue                                  # chống chèn dòng .env tuỳ ý
        val = val.strip()
        if not val:
            continue                                  # rỗng = không đổi (muốn xoá thì sửa file)
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}="):
                lines[i] = f"{key}={val}"
                break
        else:
            lines.append(f"{key}={val}")
        os.environ[key] = val                         # áp dụng ngay, khỏi restart
        saved.append(key)
    if saved:
        tmp = p.with_suffix(".env.tmp")
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.replace(tmp, p)
    return saved


def _mask(key: str, val: str) -> str:
    if key not in SECRET_KEYS or not val:
        return val
    return f"{val[:4]}…{val[-3:]}" if len(val) > 10 else "…"


# ------------------------------ API -----------------------------------------
@app.get("/api/projects")
def api_projects(request: Request):
    _require_auth(request)
    with _jobs_lock:
        jobs = {k: dict(v) for k, v in _jobs.items()}
    return {"projects": _list_projects(), "jobs": jobs}


@app.get("/api/project/{project_id}")
def api_project(project_id: str, request: Request):
    _require_auth(request)
    info = _read_project(PROJECTS_DIR / project_id)
    if info is None:
        raise HTTPException(404, "Không thấy project")
    with _jobs_lock:
        info["job"] = dict(_jobs.get(project_id) or {})
    return info


class RunRequest(BaseModel):
    stage: str = ""          # rỗng = chạy cả pipeline (`run`)
    align_backend: str = "auto"


@app.post("/api/run/{project_id}")
def api_run(project_id: str, req: RunRequest, request: Request):
    _require_auth(request)
    pdir = PROJECTS_DIR / project_id
    if not (pdir / "project.json").is_file():
        raise HTTPException(404, "Không thấy project")
    if req.stage and not req.stage.replace("-", "").isalpha():
        raise HTTPException(422, "Tên stage không hợp lệ")
    args = [req.stage or "run", str(pdir)]
    if not req.stage:
        args += ["--align-backend", req.align_backend]
    return _start_job(project_id, args)


@app.get("/api/log/{project_id}", response_class=HTMLResponse)
def api_log(project_id: str, request: Request):
    _require_auth(request)
    p = JOBS_DIR / f"{project_id}.log"
    if not p.is_file():
        return HTMLResponse("(chưa có log)", media_type="text/plain")
    # Đọc phần đuôi: log stage source có thể rất dài
    text = p.read_text(encoding="utf-8", errors="replace")
    return HTMLResponse(text[-20_000:], media_type="text/plain")


@app.get("/api/settings")
def api_settings(request: Request):
    _require_auth(request)
    env = _read_env()
    return {"settings": [{"key": k, "value": _mask(k, env.get(k, "")),
                          "set": bool(env.get(k)), "secret": k in SECRET_KEYS}
                         for k in SETTINGS_KEYS]}


class SettingsRequest(BaseModel):
    values: dict[str, str]


@app.post("/api/settings")
def api_save_settings(req: SettingsRequest, request: Request):
    _require_auth(request)
    return {"saved": _write_env(req.values)}


@app.get("/api/ket")
def api_ket(request: Request):
    """Két V3 có nối được không, việc nào đã có khoá (KHÔNG lộ giá trị khoá)."""
    _require_auth(request)
    from autoedit.web.ket_v3 import trang_thai

    return trang_thai()


@app.get("/api/sources")
def api_sources(request: Request):
    """Nguồn footage nào đang dùng được — cùng dữ liệu với lệnh `sub-status`.

    Nhìn ĐỦ BA nơi khoá có thể đến, đúng thứ tự ưu tiên thật lúc chạy job:
    két V3 (General › API Keys) -> biến môi trường (start-all.ps1) -> `.env`.
    Chỉ nhìn `.env` thì báo "thiếu" trong khi job vẫn chạy được — sai lệch nguy
    hiểm hơn là không báo gì.
    """
    _require_auth(request)
    from autoedit.sourcer.pexels import collect_pexels_keys
    from autoedit.sourcer.pixabay import collect_pixabay_keys
    from autoedit.sourcer.subscription import SITES, profile_exists
    from autoedit.web.ket_v3 import nap_env

    try:
        nap_env()            # đổ khoá từ két vào os.environ (fail-open)
    except Exception:
        pass
    env = {**_read_env(), **os.environ}

    def _nguon(ten, keys, bien, tu_ket):
        return {"name": ten, "ready": bool(keys), "need": bien,
                "nguon": "két V3" if tu_ket else ("cấu hình máy" if keys else "")}

    try:
        ket_viec = (__import__("autoedit.web.ket_v3", fromlist=["doc_ket"])
                    .doc_ket().get("tim_footage") or {})
        nha_ket = {(k.get("nha") or "").lower() for k in (ket_viec.get("khoa") or [])}
    except Exception:
        nha_ket = set()

    out = [
        _nguon("pexels", collect_pexels_keys(env), "PEXELS_API_KEY", "pexels" in nha_ket),
        _nguon("pixabay", collect_pixabay_keys(env), "PIXABAY_API_KEY", "pixabay" in nha_ket),
    ]
    for site, cfg in SITES.items():
        co_mail = bool(env.get(cfg["env"], "").strip())
        co_phien = profile_exists(site)
        thieu = []
        if not co_mail:
            thieu.append(cfg["env"])
        if not co_phien:
            thieu.append("đăng nhập trình duyệt")
        out.append({"name": site, "ready": co_mail and co_phien,
                    "need": " + ".join(thieu),
                    "nguon": "tài khoản (không dùng khoá API)"})
    return {"sources": out}


# ------------------------------ hàng đợi ------------------------------------
def _queue_conn():
    from autoedit.web import queue as q

    return q.connect(ROOT / "jobs.db")


@app.get("/health")
def health():
    """Liveness cho trang sức khỏe nền (B1 giám sát 31/08) — tách khỏi /api/me
    (endpoint auth). Không đụng dữ liệu, không cần danh tính."""
    return {"trang_thai": "ok", "app": "rendery"}


@app.get("/api/suc-khoe")
def api_suc_khoe():
    """Sức khỏe SÂU (B3 giám sát nền 31/08) — khuôn JSON của tầng nền
    {app, trang_thai, mo_dun[]}; check nổ thành module 'loi', không 500."""
    mo_dun = []

    def them(ten, ham):
        try:
            tt, ct = ham()
        except Exception as e:  # noqa: BLE001 — lỗi check là dữ liệu
            tt, ct = "loi", f"{type(e).__name__}: {e}"
        mo_dun.append({"ten": ten, "trang_thai": tt, "chi_tiet": ct})

    def _so_hang_doi():
        """SỔ có đọc được không — hạ tầng, KHÔNG dính tới job nào hỏng.

        Tách khỏi `viec-hong` (03/09) vì gộp làm một thì lẫn hai chuyện khác hẳn:
        sổ hỏng = nộp việc không vào, cả app đứng, phải sửa ngay; job hỏng = nhân
        sự nhập sai / hết tiền API / mạng chập — chuyện thường ngày, không phải
        app hỏng. Gộp chung thì GLM hết tiền cũng kéo module hạ tầng sang đỏ, và
        canary kiểm "sổ đọc được" báo SAI trong khi sổ vẫn đọc tốt.
        """
        conn = _queue_conn()
        try:
            dem = dict(conn.execute(
                "SELECT status, COUNT(*) FROM jobs GROUP BY status").fetchall())
        finally:
            conn.close()
        return "ok", (f"{dem.get('running', 0)} đang dựng / {dem.get('queued', 0)} chờ "
                      f"/ {dem.get('done', 0)} xong / {dem.get('failed', 0)} lỗi")

    def _viec_hong():
        """Job hỏng phải NÂNG TRẠNG THÁI, không chỉ in ra con số.

        LỖI THẬT 03/09 (Owner hỏi "sao rendery lỗi mà app không báo"): nhân sự
        nhắn tay qua chat là job dựng chết vì GLM hết tiền, trong khi health vẫn
        xanh — vì hàm này ĐỌC RA `failed` rồi vẫn trả "ok" cứng. Lúc đó DB có
        4/7 job hỏng (57%) mà tab giám sát im lặng suốt.

        Xét job MỚI (24h) chứ không phải tổng tích lũy: job hỏng tuần trước đã
        xử lý xong thì không được kêu mãi, còn hỏng hôm nay là chuyện đang cần
        người nhìn. Có hỏng mà vẫn còn job chạy được → cảnh báo; hỏng HẾT (không
        job nào xong) → lỗi, vì đó là hệ đứt chứ không phải một job xấu.
        """
        conn = _queue_conn()
        try:
            dem = dict(conn.execute(
                "SELECT status, COUNT(*) FROM jobs GROUP BY status").fetchall())
            moi = dict(conn.execute(
                "SELECT status, COUNT(*) FROM jobs "
                "WHERE created_at >= datetime('now', '-1 day') "
                "GROUP BY status").fetchall())
            loi_cuoi = conn.execute(
                "SELECT substr(COALESCE(error, ''), 1, 120) FROM jobs "
                "WHERE status = 'failed' ORDER BY id DESC LIMIT 1").fetchone()
        finally:
            conn.close()
        chay, cho = dem.get("running", 0), dem.get("queued", 0)
        chung = (f"{chay} đang dựng / {cho} chờ / {dem.get('done', 0)} xong "
                 f"/ {dem.get('failed', 0)} lỗi")
        hong, xong = moi.get("failed", 0), moi.get("done", 0)
        if not hong:
            return "ok", chung
        # lý do gọn một dòng — người trực nhìn là biết đi sửa cái gì
        vi_sao = " ".join((loi_cuoi[0] if loi_cuoi else "").split())[:90]
        muc = "loi" if xong == 0 else "canh_bao"
        ct = f"{hong} job hỏng trong 24h"
        ct += " (không job nào xong)" if xong == 0 else f" / {xong} xong"
        if vi_sao:
            ct += f" — {vi_sao}"
        return muc, ct

    def _nas():
        if not NAS_ROOT.is_dir():
            return "loi", f"gốc NAS {NAS_ROOT} không đọc được — nộp/dựng job chết"
        return "ok", f"gốc NAS đọc được ({NAS_ROOT})"

    them("hang-doi", _so_hang_doi)     # hạ tầng: sổ đọc được không
    them("viec-hong", _viec_hong)      # vận hành: job của người dùng có hỏng không
    them("nas", _nas)
    nang = {"ok": 0, "canh_bao": 1, "loi": 2}
    tong = max((m["trang_thai"] for m in mo_dun), key=nang.get)
    return {"app": "rendery", "trang_thai": tong, "mo_dun": mo_dun}


@app.get("/api/me")
def api_me(request: Request):
    """Danh tính + quyền hiện tại — frontend dùng để hiện tên và bật/tắt nút."""
    _require_auth(request)
    nguoi = current_user(request)
    vai = current_role(request)
    return {"nguoi": nguoi, "vai": vai, "qua_crm": behind_crm(request),
            # owner xem/huỷ được job của mọi người; vai khác chỉ job của mình
            "xem_het": is_admin(request)}


# Nhân sự thấy NAS qua Ổ MẠNG, máy chủ thấy qua ổ đĩa — cùng một chỗ, khác đường.
# CRM gán chữ ổ theo thứ tự share (`to-chuc/src/main.py:_NAS_CHU_O = "YZXWVU"`):
# NAS1 = Y:, Video = Z:. Đường UNC cũng nhận vì có người copy kiểu đó.
_TIEN_TO_NAS = ("z:", r"\\192.168.1.250\video")


def doi_duong_dan(tho: str) -> Path:
    """Đường dẫn nhân sự dán -> đường dẫn máy chủ hiểu.

    `Z:\\Life In\\US\\LI093` -> `F:\\OutlierY Nas 2\\Life In\\US\\LI093`.
    Đã đúng gốc rồi thì giữ nguyên.
    """
    s = (tho or "").strip().strip('"').replace("/", "\\")
    thap = s.lower()
    for tien_to in _TIEN_TO_NAS:
        if thap.startswith(tien_to):
            con_lai = s[len(tien_to):].lstrip("\\")
            return NAS_ROOT / con_lai if con_lai else NAS_ROOT
    return Path(s)


def _trong_nas(p: "Path | str") -> Path:
    """Ép đường dẫn phải NẰM TRONG gốc NAS. Raise HTTPException nếu không.

    Nhân sự dán đường dẫn tự do nên đây là rào duy nhất — không chặn thì bơm được
    đường dẫn bất kỳ vào worker (worker chạy lệnh trên thư mục đó).
    """
    duong = doi_duong_dan(str(p))
    try:
        real = duong.expanduser().resolve()
        real.relative_to(NAS_ROOT.resolve())
    except (ValueError, OSError):
        raise HTTPException(
            422, f"Đường dẫn phải nằm trong NAS. Máy chủ thấy NAS ở {NAS_ROOT}; "
                 f"ổ mạng Z:\\ của bạn cũng được (tự quy đổi).")
    return real


# ------------------------- AIGEN: cổng duyệt ảnh (V2 Đợt 2) -------------------
def _aigen_pdir(project_id: str) -> Path:
    pdir = PROJECTS_DIR / project_id
    if not (pdir / "project.json").is_file() and not (pdir / "aigen_duyet.json").is_file():
        raise HTTPException(404, f"Không thấy project {project_id}")
    return pdir


@app.get("/mockup")
def trang_mockup(request: Request):
    """Mockup user duyet 04/09 — dat canh code lam chuan so (index.html phai khop)."""
    _require_auth(request)
    return FileResponse(Path(__file__).parent / "static" / "mockup_de_xuat.html")


@app.get("/duyet")
def trang_duyet(request: Request):
    _require_auth(request)
    return FileResponse(Path(__file__).parent / "static" / "duyet.html")


@app.get("/api/aigen/{project_id}")
def api_aigen_phien(project_id: str, request: Request):
    _require_auth(request)
    from autoedit.aigen.duyet import PhienDuyet

    phien = PhienDuyet.doc(_aigen_pdir(project_id))
    if phien is None:
        raise HTTPException(404, "Project này không có phiên duyệt aigen")
    from dataclasses import asdict

    return asdict(phien)


@app.get("/api/aigen/{project_id}/anh/{ten_file}")
def api_aigen_anh(project_id: str, ten_file: str, request: Request):
    _require_auth(request)
    # chặn ../ — chỉ file NẰM TRONG projects/<id>/aigen/
    if "/" in ten_file or "\\" in ten_file or ".." in ten_file:
        raise HTTPException(400, "Tên file không hợp lệ")
    f = _aigen_pdir(project_id) / "aigen" / ten_file
    if not f.is_file():
        raise HTTPException(404, "Không thấy ảnh")
    return FileResponse(f)


class ChonAnh(BaseModel):
    ma_motif: str
    file: str
    chon: Optional[bool] = None
    ghi_chu: str = ""


@app.post("/api/aigen/{project_id}/chon")
def api_aigen_chon(project_id: str, req: ChonAnh, request: Request):
    _require_auth(request)
    from autoedit.aigen.duyet import PhienDuyet

    pdir = _aigen_pdir(project_id)
    phien = PhienDuyet.doc(pdir)
    if phien is None:
        raise HTTPException(404, "Không có phiên duyệt")
    if not phien.chon(req.ma_motif, req.file, req.chon, req.ghi_chu):
        raise HTTPException(404, f"Không thấy motif {req.ma_motif}")
    phien.ghi(pdir)
    return {"ok": True}


class GenAnhReq(BaseModel):
    giu: list[str] = []            # ma các motif được tick (CỔNG 1)


class QuyetReq(BaseModel):
    """CỔNG 1 (UI mới 04/09): mỗi cảnh 1 trong 3 đường."""

    quyet: dict[str, str] = {}     # ma -> "gen" | "ref" | "bo"
    ref_anh: dict[str, str] = {}   # ma -> base64/dataURL ảnh editor tự đưa


@app.post("/api/aigen/{project_id}/quyet")
def api_aigen_quyet(project_id: str, req: QuyetReq, request: Request):
    """Quyết 3 đường/cảnh: gen ảnh AI ($) · ảnh của tôi ($0, đi thẳng chốt) · bỏ.

    Motif "bỏ" rời phiên (beat giữ needs_human, editor đắp tay). Motif "ref" nhận
    ảnh editor đưa làm phương án CHỌN SẴN. Chỉ nhóm "gen" mới đốt tiền ảnh — chạy
    nền; không có "gen" nào thì phiên sang cho_duyet ngay (chốt là gen video)."""
    _require_auth(request)
    import base64 as _b64

    from autoedit.aigen.duyet import THU_MUC_ANH, PhienDuyet, PhuongAn

    pdir = _aigen_pdir(project_id)
    phien = PhienDuyet.doc(pdir)
    if phien is None:
        raise HTTPException(404, "Không có phiên duyệt")
    if phien.trang_thai != "cho_gen_anh":
        raise HTTPException(400, f"Phiên đang ở {phien.trang_thai} — không quyết được")
    hop_le = {m.ma for m in phien.motif}
    la = set(req.quyet) - hop_le
    if la:
        raise HTTPException(422, f"Motif lạ: {', '.join(sorted(la))}")

    gen: list[str] = []
    giu_motif = []
    for m in phien.motif:
        duong = req.quyet.get(m.ma, "bo")      # không quyết = bỏ (không đốt tiền ngầm)
        if duong == "bo":
            continue
        if duong == "ref":
            b64 = (req.ref_anh.get(m.ma) or "").split(",", 1)[-1]
            if not b64:
                raise HTTPException(422, f"Cảnh {m.ma} chọn 'ảnh của tôi' nhưng chưa đính ảnh")
            anh_dir = pdir / THU_MUC_ANH
            anh_dir.mkdir(exist_ok=True)
            ten = f"{m.ma}_ref.png"
            try:
                (anh_dir / ten).write_bytes(_b64.b64decode(b64))
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(422, f"Ảnh cảnh {m.ma} không đọc được: {exc}")
            m.phuong_an = [PhuongAn(file=ten, chon=True)]   # chọn sẵn — $0
        else:
            gen.append(m.ma)
        giu_motif.append(m)
    if not giu_motif:
        phien.motif = []
        phien.trang_thai = "da_gen_video"      # đóng phiên — không dùng AI
        phien.ghi(pdir)
        return {"ok": True, "trang_thai": phien.trang_thai,
                "ghi_chu": "không cảnh nào dùng AI — phiên đóng, beat đắp tay"}
    phien.motif = giu_motif
    if not gen:
        phien.trang_thai = "cho_duyet"         # toàn ảnh ref — sang thẳng bước chốt
        phien.ghi(pdir)
        return {"ok": True, "trang_thai": phien.trang_thai,
                "ghi_chu": "không tốn tiền ảnh — sang thẳng bước chốt gen video"}
    phien.trang_thai = "dang_gen_anh"
    phien.ghi(pdir)
    import threading

    from autoedit.aigen.motif import gen_anh_phuong_an

    def _chay():
        try:
            msg = gen_anh_phuong_an(pdir, gen)
            print(f"[aigen] {project_id}: {msg}", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[aigen] {project_id} LỖI gen ảnh: {exc}", flush=True)
            p2 = PhienDuyet.doc(pdir)
            if p2 is not None and p2.trang_thai == "dang_gen_anh":
                p2.trang_thai = "cho_gen_anh"
                p2.ghi(pdir)

    threading.Thread(target=_chay, daemon=True, name=f"aigen-quyet-{project_id}").start()
    return {"ok": True, "trang_thai": phien.trang_thai,
            "ghi_chu": f"đang gen ảnh {len(gen)} cảnh (~20s/ảnh)"}


@app.post("/api/aigen/{project_id}/gen-anh")
def api_aigen_gen_anh(project_id: str, req: GenAnhReq, request: Request):
    """CỔNG 1 -> 2: editor tick motif đáng tiền, bấm Gen ảnh. Chạy NỀN (~20s/ảnh)."""
    _require_auth(request)
    from autoedit.aigen.duyet import PhienDuyet

    pdir = _aigen_pdir(project_id)
    phien = PhienDuyet.doc(pdir)
    if phien is None:
        raise HTTPException(404, "Không có phiên duyệt")
    if phien.trang_thai != "cho_gen_anh":
        raise HTTPException(400, f"Phiên đang ở {phien.trang_thai} — không gen ảnh được")
    if not req.giu:
        raise HTTPException(400, "Chưa tick motif nào — tick ít nhất 1 cảnh đáng gen")
    phien.trang_thai = "dang_gen_anh"
    phien.ghi(pdir)
    import threading

    from autoedit.aigen.motif import gen_anh_phuong_an

    def _chay():
        try:
            msg = gen_anh_phuong_an(pdir, req.giu)
            print(f"[aigen] {project_id}: {msg}", flush=True)
        except Exception as exc:  # noqa: BLE001 — quay về cho_gen_anh cho tick lại
            print(f"[aigen] {project_id} LỖI gen ảnh: {exc}", flush=True)
            p2 = PhienDuyet.doc(pdir)
            if p2 is not None and p2.trang_thai == "dang_gen_anh":
                p2.trang_thai = "cho_gen_anh"
                p2.ghi(pdir)

    threading.Thread(target=_chay, daemon=True, name=f"aigen-anh-{project_id}").start()
    return {"ok": True, "trang_thai": phien.trang_thai,
            "ghi_chu": f"đang gen ảnh cho {len(req.giu)} motif (~20s/ảnh) — F5 trang này"}


@app.post("/api/aigen/{project_id}/chot")
def api_aigen_chot(project_id: str, request: Request):
    """Chốt phiên -> trạng thái da_chot. Bước gen video đọc trạng thái này."""
    _require_auth(request)
    from autoedit.aigen.duyet import PhienDuyet

    pdir = _aigen_pdir(project_id)
    phien = PhienDuyet.doc(pdir)
    if phien is None:
        raise HTTPException(404, "Không có phiên duyệt")
    if phien.trang_thai != "cho_duyet":
        raise HTTPException(400, f"Phiên đang ở {phien.trang_thai} — chưa chốt được")
    ok, ly_do = phien.du_de_chot()
    if not ok:
        raise HTTPException(400, ly_do)
    phien.trang_thai = "da_chot"
    phien.ghi(pdir)
    # Chuỗi sau-chốt (gen video Seedance -> vào shots -> dựng lại assemble) chạy
    # NỀN — editor đóng tab được, kết quả là draft mới + trạng thái da_gen_video.
    import threading

    from autoedit.aigen.hoan_thien import chay_sau_chot

    def _chay():
        try:
            msg = chay_sau_chot(pdir)
            print(f"[aigen] {project_id}: {msg}", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[aigen] {project_id} LỖI: {exc}", flush=True)

    threading.Thread(target=_chay, daemon=True, name=f"aigen-{project_id}").start()
    return {"ok": True, "trang_thai": phien.trang_thai,
            "ghi_chu": "đang gen video nền — theo dõi trạng thái phiên"}


@app.get("/api/kiem-tap")
def api_kiem_tap(request: Request, duong_dan: str = ""):
    """Kiểm thư mục tập nhân sự vừa dán: có RenderY chưa, mấy chương, thiếu gì.

    Báo TRƯỚC khi xếp hàng — đừng để chờ 24 phút rồi mới biết thiếu voice.
    """
    _require_auth(request)
    from autoedit.web.chapters import THU_MUC_CON, tom_tat

    duong_dan = (duong_dan or "").strip().strip('"')
    if not duong_dan:
        return {"nas": str(NAS_ROOT), "san_sang": False, "chuong": [],
                "loi": [f"Dán đường dẫn thư mục tập (ví dụ: {NAS_ROOT}\\Investigate\\IN002)"]}

    tap = _trong_nas(Path(duong_dan))
    if not tap.is_dir():
        return {"nas": str(NAS_ROOT), "san_sang": False, "chuong": [],
                "duong_dan": str(tap), "loi": [f"Không thấy thư mục: {tap}"]}

    d = tom_tat(tap)
    d["nas"] = str(NAS_ROOT)
    d["thu_muc_con"] = THU_MUC_CON
    return d


@app.get("/api/jobs")
def api_jobs(request: Request, all_users: bool = False):
    """Job của mình (hoặc mọi người nếu vai owner + all_users=1)."""
    _require_auth(request)
    from autoedit.web import queue as q

    nguoi = current_user(request)
    xem_het = all_users and is_admin(request)
    conn = _queue_conn()
    try:
        jobs = q.list_jobs(conn, nguoi="" if (xem_het or not nguoi) else nguoi)
        rows = []
        for j in jobs:
            d = j.to_dict()
            # V2: job có phiên duyệt ảnh AI? -> UI hiện nút Duyệt trên thẻ job
            duyet = []
            for pid in (j.project_id or "").split(","):
                pid = pid.strip()
                if pid and (PROJECTS_DIR / pid / "aigen_duyet.json").is_file():
                    try:
                        import json as _json

                        tt = _json.loads((PROJECTS_DIR / pid / "aigen_duyet.json")
                                         .read_text(encoding="utf-8")).get("trang_thai")
                        duyet.append({"project_id": pid, "trang_thai": tt})
                    except Exception:  # noqa: BLE001
                        pass
            d["duyet"] = duyet
            # UI mới: 6 đốt tiến độ / chương (voice-beat-cắt-nguồn-AI-ráp) + tên chương
            chuongs = []
            for pid in (j.project_id or "").split(","):
                pid = pid.strip()
                pj = PROJECTS_DIR / pid / "project.json"
                if not pid or not pj.is_file():
                    continue
                try:
                    import json as _json

                    pd = _json.loads(pj.read_text(encoding="utf-8"))
                    st = pd.get("stages", {})

                    def _s(*ten):
                        cac = [st.get(t, {}).get("status") for t in ten]
                        if any(c == "failed" for c in cac):
                            return "loi"
                        if all(c == "done" for c in cac):
                            return "ok"
                        if any(c == "running" for c in cac):
                            return "run"
                        return "im"
                    ai_tt = next((x["trang_thai"] for x in duyet
                                  if x["project_id"] == pid), "")
                    ai = ("ok" if ai_tt == "da_gen_video" else
                          "run" if ai_tt in ("dang_gen_anh", "da_chot") else
                          "cho" if ai_tt in ("cho_gen_anh", "cho_duyet") else
                          "ok" if st.get("source", {}).get("status") == "done" else "im")
                    chuongs.append({
                        "project_id": pid, "ten": pd.get("title", pid),
                        "aigen_tt": ai_tt,
                        "dot": [_s("align"), _s("direct"), _s("cut"),
                                _s("source", "rank"), ai, _s("assemble")]})
                except Exception:  # noqa: BLE001
                    pass
            d["chuongs"] = chuongs
            try:                     # retention của tập (server ghi lúc nộp)
                import json as _json

                rf = Path(j.job_folder) / "retention.json"
                if rf.is_file():
                    d["retention"] = " · ".join(
                        _json.loads(rf.read_text(encoding="utf-8")).get("bao_cao", []))
            except Exception:  # noqa: BLE001
                pass
            if j.status == "queued":
                d["wait_ahead"] = q.wait_ahead(conn, j.id)
            rows.append(d)
        return {"jobs": rows, "stats": q.stats(conn),
                "unseen": q.count_unseen(conn, nguoi), "nguoi": nguoi}
    finally:
        conn.close()


def _doc_mmss(chuoi: str) -> float:
    """'28:25' -> 1705s; '1:02:15' -> 3735s. Sai định dạng thì ValueError tiếng Việt."""
    phan = (chuoi or "").strip().split(":")
    if not (2 <= len(phan) <= 3) or not all(p.isdigit() for p in phan):
        raise ValueError("nhập thời lượng tập cũ dạng mm:ss (vd 28:25)")
    phan = [int(p) for p in phan]
    giay = phan[-1] + phan[-2] * 60 + (phan[0] * 3600 if len(phan) == 3 else 0)
    if giay <= 60:
        raise ValueError("thời lượng tập cũ phải > 1 phút")
    return float(giay)


class JobRequest(BaseModel):
    folder: str
    niche: str = ""
    align_backend: str = "auto"
    no_sub: bool = False
    aigen: bool = False        # user 04/09: cổng tắt/bật AI gen khi nộp job
    # RETENTION (user 04/09): ảnh chụp biểu đồ giữ chân tập CŨ + thời lượng nó
    retention_anh_b64: str = ""    # dataURL/base64 PNG-JPG; rỗng = không dùng
    retention_dai: str = ""        # "28:25" hoặc "1:02:15"


@app.post("/api/jobs")
def api_add_job(req: JobRequest, request: Request):
    """Xếp 1 thư mục TẬP vào hàng đợi (job = cả tập, gồm nhiều chương)."""
    _require_auth(request)
    from autoedit.web import queue as q
    from autoedit.web.chapters import doc_chuong

    folder = _trong_nas(Path((req.folder or "").strip().strip('"')))
    if not folder.is_dir():
        raise HTTPException(404, f"Không thấy thư mục: {folder}")

    # Chặn ở đây thay vì để worker chạy 24 phút rồi mới báo
    chuong, loi = doc_chuong(folder)
    if loi:
        raise HTTPException(422, " · ".join(loi[:4]))
    if not chuong:
        raise HTTPException(422, "Không tìm thấy chương nào (H / C1 / C2 / E)")

    # RETENTION: đo ảnh NGAY lúc nộp — ảnh hỏng thì báo liền cho người đứng đó,
    # không để 20 phút sau worker mới kêu. Kết quả ghi retention.json ở folder
    # TẬP: mọi chương cùng đọc khi ép nhịp (cutter -> ap_vao_ho_so).
    bao_cao_ret = ""
    if req.retention_anh_b64:
        import base64 as _b64
        import json as _json

        from autoedit.retention.doc_anh import AnhKhongDoDuoc
        from autoedit.retention.phan_tich import TEN_FILE as _RET, phan_tich_anh
        try:
            dai_s = _doc_mmss(req.retention_dai)
            raw = req.retention_anh_b64.split(",", 1)[-1]   # bỏ đầu dataURL nếu có
            anh = folder / "retention.png"
            anh.write_bytes(_b64.b64decode(raw))
            kq = phan_tich_anh(anh, dai_s)
            (folder / _RET).write_text(
                _json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
            bao_cao_ret = " · ".join(kq["bao_cao"])
        except (AnhKhongDoDuoc, ValueError) as exc:
            raise HTTPException(422, f"Ảnh retention không đo được: {exc}")

    conn = _queue_conn()
    try:
        jid = q.add_job(conn, str(folder), nguoi=current_user(request),
                        opts={"niche": req.niche, "align_backend": req.align_backend,
                              "no_sub": req.no_sub, "aigen": req.aigen})
        job = q.get_job(conn, jid)
        return {"job": job.to_dict(), "wait_ahead": q.wait_ahead(conn, jid),
                "retention": bao_cao_ret}
    finally:
        conn.close()


@app.post("/api/jobs/{job_id}/cancel")
def api_cancel_job(job_id: int, request: Request):
    _require_auth(request)
    from autoedit.web import queue as q

    conn = _queue_conn()
    try:
        job = q.get_job(conn, job_id)
        if job is None:
            raise HTTPException(404, "Không thấy job")
        nguoi = current_user(request)
        if nguoi and job.nguoi != nguoi and not is_admin(request):
            raise HTTPException(403, "Chỉ huỷ được job của mình")
        if not q.cancel(conn, job_id):
            raise HTTPException(409, "Job đã chạy — không huỷ được")
        return {"ok": True}
    finally:
        conn.close()


@app.post("/api/jobs/seen")
def api_mark_seen(request: Request):
    """User đã xem kết quả -> tắt badge trên CRM."""
    _require_auth(request)
    from autoedit.web import queue as q

    conn = _queue_conn()
    try:
        return {"marked": q.mark_seen(conn, current_user(request))}
    finally:
        conn.close()


@app.get("/api/badge")
def api_badge(request: Request, nguoi: str = ""):
    """CRM gọi để lấy số job xong chưa xem -> hiện badge sidebar."""
    _require_auth(request)
    from autoedit.web import queue as q

    conn = _queue_conn()
    try:
        return {"unseen": q.count_unseen(conn, nguoi or current_user(request))}
    finally:
        conn.close()


@app.get("/api/ketqua/{job_id}")
def api_ketqua(job_id: int, request: Request):
    """Thư mục kết quả trên NAS + tóm tắt từng chương — nhân sự copy về máy."""
    _require_auth(request)
    from autoedit.web import queue as q

    conn = _queue_conn()
    try:
        job = q.get_job(conn, job_id)
    finally:
        conn.close()
    if job is None:
        raise HTTPException(404, "Không thấy job")

    from autoedit.web.compose import thu_muc_giao

    dest = thu_muc_giao(Path(job.job_folder))
    if not dest.is_dir():
        return {"san_sang": False, "duong_dan": str(dest),
                "loi": "Chưa có kết quả (job chưa xong hoặc chưa giao được)."}
    chuong = []
    for d in sorted(dest.iterdir()):
        if d.is_dir():
            chuong.append({
                "ten": d.name,
                "co_draft": (d / "draft").is_dir(),
                "footage": len(list((d / "footage").rglob("*")))
                           if (d / "footage").is_dir() else 0,
            })
    doc = dest / "DOC_TRUOC.txt"
    return {"san_sang": True, "duong_dan": str(dest), "chuong": chuong,
            "doc_truoc": doc.read_text(encoding="utf-8") if doc.is_file() else ""}


@app.get("/api/joblog/{job_id}", response_class=HTMLResponse)
def api_job_log(job_id: int, request: Request):
    _require_auth(request)
    p = JOBS_DIR / f"job_{job_id}.log"
    if not p.is_file():
        return HTMLResponse("(chưa có log)", media_type="text/plain")
    return HTMLResponse(p.read_text(encoding="utf-8", errors="replace")[-20_000:],
                        media_type="text/plain")


@app.get("/", response_class=HTMLResponse)
def index():
    p = Path(__file__).parent / "static" / "index.html"
    if not p.is_file():
        return HTMLResponse("<h1>RenderY</h1><p>Thiếu static/index.html</p>", status_code=500)
    return FileResponse(p)
