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
# Nghiên cứu kênh ref (user 05/09): chỉ manager/owner — đo tốn tải YouTube +
# lượt GLM, và "chuẩn dựng" là quyết định cấp quản lý, không phải thói quen editor.
_VAI_NGHIEN_CUU_KENH = {"admin", "owner", "manager"}


def _duoc_nghien_cuu_kenh(request: Request) -> bool:
    """Ngoài CRM (chạy trực tiếp/dev, không có header vai) thì mở — đúng khuôn
    is_admin: 'owner giữ cho lúc chạy trực tiếp không qua cổng'."""
    if not behind_crm(request):
        return True
    return current_role(request) in _VAI_NGHIEN_CUU_KENH


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
            "xem_het": is_admin(request),
            "nghien_cuu_kenh": _duoc_nghien_cuu_kenh(request)}


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


# ═════════════════ MODULE KÊNH REF (user 05/09 — khuôn Author Extract) ══════
# Nghiên cứu kênh = việc LÀM MỘT LẦN có chủ đích (Func 1 Extractor), tách hẳn
# khỏi form nộp tập (Func 2 chỉ CHỌN từ thư viện). Đo chạy NỀN trên server —
# trạng thái in-memory; server restart giữa chừng thì mục "đang đo" biến mất,
# kênh chưa có hồ sơ -> bấm đo lại (đo vốn idempotent nhờ cache).
_kenh_dang_do: dict = {}          # slug -> {"tt": "dang_do"|"loi", "loi": str}
_kenh_lock = threading.Lock()


class KenhRequest(BaseModel):
    link: str
    ten: str = ""              # TÊN PHONG CÁCH editor đặt (bắt buộc, user 05/09)
    so_video: int = 5          # đo bao nhiêu video (1..8 — trần né YouTube chặn IP)


# ═════════════════ OFFLINE (Đợt 2 — user đặt tên 07/09) ═════════════════════
_offline_dang: dict = {}          # project_id -> {"tt": ..., "ghi_chu": ...}
_offline_lock = threading.Lock()


class OfflineRequest(BaseModel):
    avd_s: float = 0.0
    mo_dau_tap_s: float = 0.0
    kenh_ref: str = ""
    uu_tien_nguon: str = ""        # "" | ref | envato
    dia_danh: str = ""


def _gac_quyen_sua(request: Request, hd: dict) -> None:
    """AI TẠO sequence thì người đó mới được sửa (user chốt 08/09).

    Ngoài CRM (không có SSO) hoặc hợp đồng cũ chưa ghi người tạo -> mở, y khuôn
    is_admin: 'owner giữ cho lúc chạy trực tiếp không qua cổng'."""
    chu = (hd or {}).get("nguoi_tao") or ""
    if not chu or not behind_crm(request):
        return
    ai = current_user(request)
    if ai and ai != chu and not is_admin(request):
        raise HTTPException(403, f"Sequence này do «{chu}» tạo — chỉ người tạo "
                                 "(hoặc admin) được sửa")


def _pdir_offline(project_id: str) -> Path:
    import re as _re

    if not _re.fullmatch(r"[\w.-]{1,80}", project_id):
        raise HTTPException(422, "project_id không hợp lệ")
    d = PROJECTS_DIR / project_id
    if not d.is_dir():
        raise HTTPException(404, "Không thấy project")
    return d


@app.post("/api/offline/{project_id}/phan-tich")
def api_offline_phan_tich(project_id: str, req: OfflineRequest, request: Request):
    """Chạy phân tích Offline nền (cắt khối + 4 lớp + ứng viên Library)."""
    _require_auth(request)
    d = _pdir_offline(project_id)
    nguoi_tao = current_user(request)
    with _offline_lock:
        if _offline_dang.get(project_id, {}).get("tt") == "dang":
            raise HTTPException(409, "Đang phân tích dở")
        _offline_dang[project_id] = {"tt": "dang", "ghi_chu": ""}

    def _chay():
        from autoedit.offline import runner as orun
        try:
            hd = orun.phan_tich(d, avd_s=req.avd_s, mo_dau_tap_s=req.mo_dau_tap_s,
                                kenh_ref=req.kenh_ref, uu_tien_nguon=req.uu_tien_nguon,
                                dia_danh=req.dia_danh, nguoi_tao=nguoi_tao,
                                log=lambda m: print("[offline]", m, flush=True))
            with _offline_lock:
                _offline_dang[project_id] = {
                    "tt": "xong",
                    "ghi_chu": f"{len(hd['khoi'])} khối · "
                               + ("ĐỒNG KIỂM" if hd["dong_kiem"] else "AUTO")}
        except Exception as exc:  # noqa: BLE001
            with _offline_lock:
                _offline_dang[project_id] = {"tt": "loi", "ghi_chu": str(exc)[:200]}

    threading.Thread(target=_chay, daemon=True, name=f"offline-{project_id}").start()
    return {"ok": True, "ghi_chu": "đang phân tích nền"}


@app.get("/api/offline/{project_id}")
def api_offline_doc(project_id: str, request: Request):
    _require_auth(request)
    from autoedit.offline import runner as orun

    d = _pdir_offline(project_id)
    hd = orun.doc(d)
    with _offline_lock:
        tt = dict(_offline_dang.get(project_id, {}))
    if hd is None and not tt:
        raise HTTPException(404, "Chưa phân tích — POST /phan-tich trước")
    return {"hop_dong": hd, "tt": tt}


@app.put("/api/offline/{project_id}")
def api_offline_luu(project_id: str, request: Request, hd: dict):
    """Màn Offline lưu bản người chỉnh. Validate tối thiểu: voice bất biến."""
    _require_auth(request)
    from autoedit.offline import runner as orun

    d = _pdir_offline(project_id)
    cu = orun.doc(d)
    if cu is None:
        raise HTTPException(409, "Chưa có hợp đồng gốc")
    _gac_quyen_sua(request, cu)
    if len(hd.get("khoi") or []) == 0:
        raise HTTPException(422, "Hợp đồng rỗng")
    # voice bất biến: tổng thời lượng NÓI không được đổi so bản gốc
    def _noi(x):
        return round(sum(k["v1"] - k["v0"] for k in x["khoi"]), 1)
    if abs(_noi(hd) - _noi(cu)) > 0.5:
        raise HTTPException(422, "Tổng thời lượng NÓI thay đổi — voice là bất biến, "
                                 "chỉ im lặng được chèn/thu")
    from autoedit.offline import hinh as mhinh

    # thở đổi -> mốc voice dịch -> dời dải hình theo khối gốc (không để hình trôi)
    moc_cu = mhinh.moc_timeline(cu.get("khoi") or [])
    mhinh.dam_bao(hd)
    mhinh.dong_bo_sau_tho(hd, moc_cu)
    loi_hinh = mhinh.kiem(hd)
    orun.luu(d, hd)
    if loi_hinh:
        return {"ok": True, "canh_bao_hinh": loi_hinh}
    return {"ok": True}


class OfflineGenRequest(BaseModel):
    khoi: int
    so_anh: int = 2


@app.post("/api/offline/{project_id}/gen")
def api_offline_gen(project_id: str, req: OfflineGenRequest, request: Request):
    """⚡ Gen AI cho 1 khối (nền) — nguồn thứ 5, ảnh ghi vào Library."""
    _require_auth(request)
    d = _pdir_offline(project_id)
    khoa = f"{project_id}:gen{req.khoi}"
    with _offline_lock:
        if _offline_dang.get(khoa, {}).get("tt") == "dang":
            raise HTTPException(409, "Khối này đang gen dở")
        _offline_dang[khoa] = {"tt": "dang", "ghi_chu": f"gen khối {req.khoi + 1}..."}

    def _chay():
        from autoedit.offline.gen import gen_cho_khoi
        try:
            moi = gen_cho_khoi(d, req.khoi, so_anh=req.so_anh,
                               log=lambda m: print("[offline-gen]", m, flush=True))
            with _offline_lock:
                _offline_dang[khoa] = {"tt": "xong",
                                       "ghi_chu": f"+{len(moi)} ảnh AI vào khay"}
        except Exception as exc:  # noqa: BLE001
            with _offline_lock:
                _offline_dang[khoa] = {"tt": "loi", "ghi_chu": str(exc)[:200]}

    threading.Thread(target=_chay, daemon=True, name=khoa).start()
    return {"ok": True, "ghi_chu": "đang gen nền — ảnh tự rơi vào khay khối"}


class OfflineHinhRequest(BaseModel):
    thao_tac: str            # them | bo | keo_mep
    idx: int = -1
    tai_giay: float = 0.0
    dur: float = 0.0


@app.post("/api/offline/{project_id}/hinh")
def api_offline_hinh(project_id: str, req: OfflineHinhRequest, request: Request):
    """Thao tác DẢI HÌNH (08/09: tách hình/voice như phần mềm dựng)."""
    _require_auth(request)
    from autoedit.offline import hinh as mhinh
    from autoedit.offline import runner as orun

    d = _pdir_offline(project_id)
    hd = orun.doc(d)
    if hd is None:
        raise HTTPException(409, "Chưa phân tích")
    tho_co = 0.0
    if req.thao_tac == "them":
        j = mhinh.them_mieng(hd, req.tai_giay)
        if j < 0:
            raise HTTPException(422, "Không có miếng nào phủ mốc này")
    elif req.thao_tac == "bo":
        ok, tho_co = mhinh.bo_mieng(hd, req.idx)
        if not ok:
            raise HTTPException(422, "Không bỏ được (miếng cuối cùng?)")
    elif req.thao_tac == "keo_mep":
        if not mhinh.keo_mep(hd, req.idx, req.dur):
            raise HTTPException(422, "Không kéo được mép miếng cuối")
    else:
        raise HTTPException(422, "thao_tac lạ")
    loi = mhinh.kiem(hd)
    orun.luu(d, hd)
    # trả CẢ hợp đồng: thao tác 'bo' có thể đã co khoảng lặng -> voice đổi theo,
    # UI chỉ cập nhật hinh[] là vẽ dải voice CŨ — đúng kiểu bug "UI đánh lừa"
    return {"ok": True, "hop_dong": hd, "hinh": hd["hinh"], "loi": loi,
            "tho_co": tho_co}


@app.post("/api/offline/{project_id}/thay-mau")
def api_offline_thay_mau(project_id: str, request: Request):
    """THAY MÁU (Đợt 5): chương KHÓA SỔ -> tải bản thật + ráp draft CapCut (nền)."""
    _require_auth(request)
    d = _pdir_offline(project_id)
    khoa = f"{project_id}:thaymau"
    with _offline_lock:
        if _offline_dang.get(khoa, {}).get("tt") == "dang":
            raise HTTPException(409, "Đang thay máu dở")
        _offline_dang[khoa] = {"tt": "dang", "ghi_chu": "tải bản thật + ráp draft..."}

    def _chay():
        from autoedit.offline.thay_mau import thay_mau
        try:
            kq = thay_mau(d, log=lambda m: print("[thay-mau]", m, flush=True))
            with _offline_lock:
                _offline_dang[khoa] = {
                    "tt": "xong",
                    "ghi_chu": f"draft {Path(kq['draft']).name} · hình "
                               f"{kq['mieng_co_hinh']}/{kq['tong_mieng']} miếng"
                               + (f" · {len(kq['canh_bao'])} cảnh báo" if kq["canh_bao"] else "")}
        except Exception as exc:  # noqa: BLE001
            with _offline_lock:
                _offline_dang[khoa] = {"tt": "loi", "ghi_chu": str(exc)[:200]}

    threading.Thread(target=_chay, daemon=True, name=khoa).start()
    return {"ok": True, "ghi_chu": "đang thay máu nền — draft CapCut sẽ hiện khi xong"}


class TrimRequest(BaseModel):
    clip_id: str
    t0: float
    t1: float
    khoi: int = -1          # >=0: nạp thẳng vào miếng hình này
    luu_kho: bool = True    # ghi khúc vào Library (chỉ SỔ, không cắt file)


@app.post("/api/offline/{project_id}/luu-nhanh")
async def api_offline_luu_nhanh(project_id: str, request: Request):
    """AUTOSAVE lúc rời tab/đóng CRM — sendBeacon gửi body thô, không chờ kết quả.
    Cùng luật voice bất biến + gác quyền như PUT thường (user chốt 08/09)."""
    _require_auth(request)
    from autoedit.offline import runner as orun

    d = _pdir_offline(project_id)
    cu_hd = orun.doc(d)
    if cu_hd is None:
        raise HTTPException(409, "Chưa có hợp đồng")
    _gac_quyen_sua(request, cu_hd)
    try:
        hd = json.loads(await request.body())
    except Exception:  # noqa: BLE001
        raise HTTPException(422, "Body không hợp lệ")
    if not (hd.get("khoi") or []):
        raise HTTPException(422, "Hợp đồng rỗng")

    def _noi(x):
        return round(sum(k["v1"] - k["v0"] for k in x["khoi"]), 1)

    if abs(_noi(hd) - _noi(cu_hd)) > 0.5:
        raise HTTPException(422, "Voice bất biến")
    from autoedit.offline import hinh as mhinh

    mhinh.dam_bao(hd)
    mhinh.khit_mep(hd)
    orun.luu(d, hd)
    return {"ok": True}


@app.post("/api/offline/{project_id}/trim")
def api_offline_trim(project_id: str, req: TrimRequest, request: Request):
    """Trim ứng viên ở màn review -> ghi khúc vào Library (mốc in/out, KHÔNG
    cắt file — đúng nguyên tắc sổ tra không chứa file) + nạp vào miếng hình."""
    _require_auth(request)
    from autoedit.offline import runner as orun
    from autoedit.sotra import db as sdb

    d = _pdir_offline(project_id)
    if req.t1 - req.t0 < 0.4:
        raise HTTPException(422, "Khúc quá ngắn (tối thiểu 0.4s)")
    conn = sdb.mo()
    try:
        goc = conn.execute("SELECT * FROM clip WHERE id=?", (req.clip_id,)).fetchone()
        if goc is None:
            raise HTTPException(404, "Không thấy clip trong Library")
        g = dict(goc)
        # id khúc: <id gốc>#t0-t1 — truy ngược được về clip mẹ khi thay máu
        cid = f"{req.clip_id}#{req.t0:.2f}-{req.t1:.2f}"
        if req.luu_kho:
            sdb.them_clip(conn, {
                **{k: g.get(k, "") for k in ("nguon", "url_trang", "url_anh",
                                             "url_video", "path_local", "tap",
                                             *sdb.TRUC)},
                "id": cid, "tieu_de": f"{g.get('tieu_de', '')} [{req.t0:.1f}-{req.t1:.1f}s]",
                "t0": req.t0, "t1": req.t1, "dai_s": round(req.t1 - req.t0, 2),
                "tag_nguon": g.get("tag_nguon", "tieu_de")})
            sdb.ghi_su_kien(conn, cid, "nguoi_thay", tap=project_dir_ten(d),
                            chi_tiet=f"trim {req.t0:.1f}-{req.t1:.1f} từ {req.clip_id[:40]}")
            conn.commit()
    finally:
        conn.close()

    if req.khoi >= 0:
        hd = orun.doc(d)
        if hd is None:
            raise HTTPException(409, "Chưa phân tích")
        from autoedit.offline import hinh as mhinh

        hs = mhinh.dam_bao(hd)
        if not 0 <= req.khoi < len(hs):
            raise HTTPException(422, "Miếng không tồn tại")
        h = hs[req.khoi]
        moi = {"id": cid, "nguon": g.get("nguon", ""),
               "tieu_de": f"{g.get('tieu_de', '')} [{req.t0:.1f}-{req.t1:.1f}s]",
               "lop": "L1", "diem": 9.5, "url_anh": g.get("url_anh", ""),
               "url_video": g.get("url_video", ""), "geo": g.get("geo", ""),
               "dai_s": round(req.t1 - req.t0, 2)}
        h["uv"] = [moi] + [u for u in (h.get("uv") or []) if u["id"] != cid]
        h["chon"] = 0
        h["nguoi_sua"] = True
        orun.luu(d, hd)
    return {"ok": True, "clip_id": cid}


def project_dir_ten(d: Path) -> str:
    return d.name


@app.post("/api/offline/{project_id}/dich")
def api_offline_dich(project_id: str, request: Request):
    """Dịch tiếng Việt cho hợp đồng CŨ (phân tích trước 08/09 chưa có bản dịch)."""
    _require_auth(request)
    from autoedit.offline import dich as mdich
    from autoedit.offline import runner as orun

    d = _pdir_offline(project_id)
    hd = orun.doc(d)
    if hd is None:
        raise HTTPException(409, "Chưa phân tích")
    ban = mdich.dich_khoi([k.get("loi", "") for k in hd["khoi"]],
                          log=lambda m: print("[offline]", m, flush=True))
    if not ban:
        raise HTTPException(502, "Không dịch được (thiếu khoá GLM?)")
    for i, k in enumerate(hd["khoi"]):
        if i in ban:
            k["dich"] = ban[i]
    orun.luu(d, hd)
    return {"ok": True, "so_dong": len(ban)}


@app.get("/api/offline/{project_id}/voice")
def api_offline_voice(project_id: str, request: Request):
    """Voice master WAV cho màn Offline — PCM seek chính xác mẫu (bài học 06/09:
    MP3 currentTime lệch 50-250ms theo frame khiến 'khối trắng dính voice')."""
    _require_auth(request)
    d = _pdir_offline(project_id)
    f = d / "media" / "voice_master.wav"
    if not f.is_file():
        raise HTTPException(404, "Chưa có voice master — chạy align/cut trước")
    return FileResponse(f, media_type="audio/wav")


@app.post("/api/offline/{project_id}/khoa-so")
def api_offline_khoa(project_id: str, request: Request):
    """KHÓA SỔ chương (pha 2 duyệt xong) — thay máu (đợt 5) chỉ chạy chương khóa."""
    _require_auth(request)
    from autoedit.offline import runner as orun

    d = _pdir_offline(project_id)
    hd = orun.doc(d)
    if hd is None:
        raise HTTPException(409, "Chưa phân tích")
    _gac_quyen_sua(request, hd)
    hd["trang_thai"] = "khoa"
    orun.luu(d, hd)
    return {"ok": True, "ghi_chu": f"đã khóa sổ {len(hd['khoi'])} khối — chờ thay máu (đợt 5)"}


@app.post("/api/offline/{project_id}/kiem-mp4")
def api_offline_kiem(project_id: str, request: Request, dai_s: float = 15.0):
    """Xuất MP4 kiểm ranh (sync tuyệt đối — miễn nhiễm trễ RDP)."""
    _require_auth(request)
    from autoedit.offline import runner as orun

    d = _pdir_offline(project_id)
    f = d / f"kiem_ranh_{int(dai_s)}s.mp4"
    orun.xuat_kiem_mp4(d, f, dai_s=max(5.0, min(60.0, dai_s)))
    return FileResponse(f, media_type="video/mp4", filename=f.name)


# ═════════════════ SỔ TRA (Đợt 1 flow Đường Dây — user chốt 06/09) ═══════════
# Trang stock nội bộ: 1 ô tìm cho 4 nguồn. Db mở theo request (SQLite mở nhanh,
# tránh giữ connection xuyên thread của uvicorn).
_sotra_dang_hut: dict = {}        # {"tt": "dang"|"xong"|"loi", "ghi_chu": str}
_sotra_lock = threading.Lock()


class SoTraHutRequest(BaseModel):
    tu_khoa: list[str]
    nguon: list[str] = ["envato", "pexels", "pixabay"]
    so_trang: int = 1


@app.get("/api/sotra")
def api_sotra_tim(request: Request, q: str = "", nguon: str = "",
                  neo: int = 0, tap: str = "", limit: int = 60, offset: int = 0):
    """Ô tìm của trang Sổ Tra — mọi vai xem được."""
    _require_auth(request)
    from autoedit.sotra import db as _sdb

    conn = _sdb.mo()
    try:
        kq = _sdb.tim(conn, q=q, nguon=nguon, chi_neo=bool(neo), tap=tap,
                      limit=max(1, min(200, limit)), offset=max(0, offset))
        dem = _sdb.dem_theo_nguon(conn)
        dem["nhac"] = conn.execute(
            "SELECT COUNT(*) FROM nhac WHERE trang_thai != 'loai_tru'").fetchone()[0]
    finally:
        conn.close()
    with _sotra_lock:
        hut = dict(_sotra_dang_hut)
    return {"clips": kq, "dem": dem, "hut": hut}


@app.get("/api/sotra/clip")
def api_sotra_clip(request: Request, id: str):
    """Hồ sơ 1 clip + lịch sử sự kiện (hộp xem lớn)."""
    _require_auth(request)
    from autoedit.sotra import db as _sdb

    conn = _sdb.mo()
    try:
        r = conn.execute("SELECT * FROM clip WHERE id=?", (id,)).fetchone()
        if r is None:
            raise HTTPException(404, "Không thấy clip trong sổ")
        return {"clip": dict(r), "su_kien": _sdb.lich_su(conn, id)}
    finally:
        conn.close()


@app.get("/api/sotra/frame")
def api_sotra_frame(request: Request, id: str, vai: str = "dau"):
    """Frame đầu/cuối cho clip nguồn local (ref/kho) — rút lazy, cache vĩnh viễn."""
    _require_auth(request)
    from autoedit.sotra import db as _sdb
    from autoedit.sotra.media import frame_clip

    conn = _sdb.mo()
    try:
        f = frame_clip(conn, id, vai)
    finally:
        conn.close()
    if f is None:
        raise HTTPException(404, "Không rút được frame")
    return FileResponse(f, media_type="image/jpeg",
                        headers={"Cache-Control": "max-age=86400"})


@app.get("/api/sotra/video")
def api_sotra_video(request: Request, id: str):
    """Phát file local (ref/kho) cho hover-play — nguồn web dùng url_video thẳng."""
    _require_auth(request)
    from autoedit.sotra import db as _sdb

    conn = _sdb.mo()
    try:
        r = conn.execute("SELECT path_local FROM clip WHERE id=?", (id,)).fetchone()
    finally:
        conn.close()
    if r is None or not r[0] or not Path(r[0]).is_file():
        raise HTTPException(404, "Không có file local")
    return FileResponse(Path(r[0]), media_type="video/mp4")


@app.post("/api/sotra/clip/loi")
def api_sotra_clip_loi(request: Request, id: str):
    """UI báo link chết (ảnh/video không tải được) — đánh dấu, không xóa."""
    _require_auth(request)
    from autoedit.sotra import db as _sdb

    conn = _sdb.mo()
    try:
        conn.execute("UPDATE clip SET trang_thai='link_chet' WHERE id=?", (id,))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


@app.post("/api/sotra/hut")
def api_sotra_hut(req: SoTraHutRequest, request: Request):
    """Phiên hút — manager/owner; chạy nền 1 luồng rón rén."""
    _require_auth(request)
    if not _duoc_nghien_cuu_kenh(request):
        raise HTTPException(403, "Chỉ manager/owner được hút nguồn mới")
    tu_khoas = [t.strip() for t in req.tu_khoa if t.strip()][:40]
    if not tu_khoas:
        raise HTTPException(422, "Chưa có từ khóa nào")
    with _sotra_lock:
        if _sotra_dang_hut.get("tt") == "dang":
            raise HTTPException(409, "Đang có phiên hút chạy dở")
        _sotra_dang_hut.clear()
        _sotra_dang_hut.update({"tt": "dang", "ghi_chu": f"{len(tu_khoas)} từ khóa..."})

    def _chay():
        from autoedit.sotra import db as _sdb
        from autoedit.sotra.hut import phien_hut
        try:
            conn = _sdb.mo()
            try:
                kq = phien_hut(conn, tu_khoas, req.nguon,
                               so_trang=max(1, min(3, req.so_trang)),
                               log=lambda m: print("[sotra]", m, flush=True))
            finally:
                conn.close()
            with _sotra_lock:
                _sotra_dang_hut.update(
                    {"tt": "xong",
                     "ghi_chu": f"+{kq['moi']} mới · {kq['trung']} trùng"
                                + (f" · {len(kq['loi'])} lỗi" if kq["loi"] else "")})
        except Exception as exc:  # noqa: BLE001
            with _sotra_lock:
                _sotra_dang_hut.update({"tt": "loi", "ghi_chu": str(exc)[:200]})

    threading.Thread(target=_chay, daemon=True, name="sotra-hut").start()
    return {"ok": True, "ghi_chu": "đang hút nền — kết quả tự hiện thêm"}


class SoTraNapRefRequest(BaseModel):
    thu_muc: str                      # thư mục tập trên NAS (chứa *.mp4 [+ .srt])
    tap: str = ""
    quoc_gia: str = ""                # gắn cứng geo cấp tập
    doc_hinh: bool = True


_sotra_nap_ref: dict = {}


@app.get("/api/sotra/nap-ref")
def api_sotra_nap_ref_tt(request: Request):
    """Tiến độ phiên nạp ref (UI hỏi mỗi 3s)."""
    _require_auth(request)
    with _sotra_lock:
        return dict(_sotra_nap_ref) or {"tt": ""}


@app.post("/api/sotra/nap-ref")
def api_sotra_nap_ref(req: SoTraNapRefRequest, request: Request):
    """Cắt video ref trong thư mục tập thành CẢNH QUAY + đọc hình -> Library.

    Chạy nền vì tốn ~5 phút/tập (đo: quét scene 52' hết 78s, trích ảnh ~60s,
    đọc hình ~3 phút). Manager/owner mới được chạy — tốn tiền LLM thật.
    """
    _require_auth(request)
    if not _duoc_nghien_cuu_kenh(request):
        raise HTTPException(403, "Chỉ manager/owner được nạp ref")
    thu_muc = Path(req.thu_muc)
    if not thu_muc.is_dir():
        raise HTTPException(422, f"Không thấy thư mục «{req.thu_muc}»")
    if not any(thu_muc.rglob("*.mp4")):
        raise HTTPException(422, "Thư mục không có file .mp4 nào")
    with _sotra_lock:
        if _sotra_nap_ref.get("tt") == "dang":
            raise HTTPException(409, "Đang có phiên nạp ref chạy dở")
        _sotra_nap_ref.clear()
        _sotra_nap_ref.update({"tt": "dang", "ghi_chu": "đang quét cảnh..."})

    def _chay():
        from autoedit.sotra import db as _sdb
        from autoedit.sotra.hut import nap_ref_tap

        def _log(m):
            print("[sotra]", m, flush=True)
            with _sotra_lock:
                _sotra_nap_ref["ghi_chu"] = m.replace("sotra: ", "")

        try:
            conn = _sdb.mo()
            try:
                n = nap_ref_tap(conn, thu_muc, tap=req.tap,
                                quoc_gia=req.quoc_gia, doc_hinh=req.doc_hinh,
                                log=_log)
            finally:
                conn.close()
            with _sotra_lock:
                _sotra_nap_ref.update({"tt": "xong", "ghi_chu": f"+{n} cảnh vào Library"})
        except Exception as exc:  # noqa: BLE001
            with _sotra_lock:
                _sotra_nap_ref.update({"tt": "loi", "ghi_chu": str(exc)[:200]})

    threading.Thread(target=_chay, daemon=True, name="sotra-nap-ref").start()
    return {"ok": True, "ghi_chu": "đang nạp nền — mất ~5 phút mỗi tập"}


class NhacHutRequest(BaseModel):
    tu_khoa: str = ""
    moods: str = ""                   # slug Epidemic: suspense, dreamy...
    so_trang: int = 2


@app.get("/api/sotra/nhac")
def api_nhac_tim(request: Request, q: str = "", mood: str = "", limit: int = 40):
    """Tra kho nhạc — mọi vai xem/nghe được."""
    _require_auth(request)
    from autoedit.sotra import db as _sdb, nhac as _nhac

    conn = _sdb.mo()
    try:
        return {"tracks": _nhac.tim_nhac(conn, q=q, mood=mood, limit=limit)}
    finally:
        conn.close()


@app.post("/api/sotra/nhac/hut")
def api_nhac_hut(req: NhacHutRequest, request: Request):
    """Hút metadata Epidemic (không file, ~5s/2 trang) — manager/owner."""
    _require_auth(request)
    if not _duoc_nghien_cuu_kenh(request):
        raise HTTPException(403, "Chỉ manager/owner được hút nguồn")
    from autoedit.sotra import db as _sdb, nhac as _nhac

    conn = _sdb.mo()
    try:
        n = _nhac.hut_epidemic(conn, tu_khoa=req.tu_khoa, moods=req.moods,
                               so_trang=max(1, min(5, req.so_trang)))
    finally:
        conn.close()
    return {"ok": True, "moi": n}


def _mood_chuong(hd: dict) -> str:
    """Mood đa số các khối của chương — trục chính chọn nhạc (mood là trụ)."""
    from collections import Counter

    dem = Counter((k.get("mood") or "").strip().lower()
                  for k in hd.get("khoi") or [] if k.get("mood"))
    return dem.most_common(1)[0][0] if dem else ""


@app.get("/api/offline/{project_id}/nhac")
def api_offline_nhac(project_id: str, request: Request):
    """Đề xuất nhạc cho CHƯƠNG này (user chốt 06/09: nhạc theo chương).

    energy suy từ Framing: thân cắt nhanh (<3.5s) cần high, <5s medium, còn
    lại low. Kho chưa có track hợp mood -> tự hút 1 trang Epidemic theo mood.
    """
    _require_auth(request)
    from autoedit.offline import runner as orun
    from autoedit.sotra import db as _sdb, nhac as _nhac

    hd = orun.doc(_pdir_offline(project_id))
    if hd is None:
        raise HTTPException(409, "Chưa phân tích")
    mood = _nhac.quy_mood_chuong(_mood_chuong(hd))
    than = float((hd.get("framing") or {}).get("than") or 0)
    energy = "high" if 0 < than < 3.5 else ("medium" if than < 5 else "low")
    conn = _sdb.mo()
    try:
        # FLOW user chốt 06/09: nhạc CHẢY VÀO OFFLINE TRƯỚC — chương cần thì
        # hút theo mood của chương, track đọng lại thành kho; Library chỉ là
        # nơi xem cái đã tích tụ. Kho lớn từ nhu cầu thật, không trữ trước.
        co = conn.execute("SELECT COUNT(*) FROM nhac WHERE mood=? AND co_loi=0",
                          (mood,)).fetchone()[0] if mood else 0
        if mood and co < 40:                  # mood này còn mỏng -> hút tươi
            goc = _nhac._MOOD_NOI_BO.get(mood) or ()
            try:
                if goc:
                    _nhac.hut_epidemic(conn, moods=goc[0], so_trang=1)
                else:                         # mood lạ -> term search vẫn ăn
                    _nhac.hut_epidemic(conn, tu_khoa=mood, so_trang=1)
            except Exception:  # noqa: BLE001 — mạng hỏng thì dùng cái đang có
                pass
        dx = _nhac.de_xuat(conn, mood=mood, energy=energy,
                           kenh=(hd.get("ma_tap") or "")[:2])
    finally:
        conn.close()
    return {"mood": mood, "energy": energy, "tracks": dx,
            "dang_chon": hd.get("nhac") or None}


class NhacChonRequest(BaseModel):
    id: str = ""                      # "" = bỏ nhạc


@app.post("/api/offline/{project_id}/nhac/chon")
def api_offline_nhac_chon(project_id: str, req: NhacChonRequest, request: Request):
    """Gắn track cho chương -> hd['nhac'] + sự kiện duoc_chon."""
    _require_auth(request)
    from autoedit.offline import runner as orun
    from autoedit.sotra import db as _sdb

    d = _pdir_offline(project_id)
    hd = orun.doc(d)
    if hd is None:
        raise HTTPException(409, "Chưa phân tích")
    _gac_quyen_sua(request, hd)
    if not req.id:
        hd.pop("nhac", None)
        orun.luu(d, hd)
        return {"ok": True, "nhac": None}
    conn = _sdb.mo()
    try:
        r = conn.execute("SELECT * FROM nhac WHERE id=?", (req.id,)).fetchone()
        if r is None:
            raise HTTPException(404, "Không thấy track trong kho")
        t = dict(r)
        conn.execute("INSERT INTO su_kien(clip_id, tap, loai, ts) VALUES(?,?,?,?)",
                     (req.id, hd.get("ma_tap") or "",
                      "duoc_chon", datetime.now(timezone.utc).isoformat()))
        conn.commit()
    finally:
        conn.close()
    hd["nhac"] = {k: t[k] for k in ("id", "tieu_de", "nghe_si", "mood", "bpm",
                                    "energy", "dai_s", "url_nghe")}
    orun.luu(d, hd)
    return {"ok": True, "nhac": hd["nhac"]}


@app.get("/api/kenh")
def api_kenh_list(request: Request):
    """Thư viện kênh đã nghiên cứu + kênh đang đo — mọi vai xem được."""
    _require_auth(request)
    import dataclasses as _dc

    from autoedit.kenh.hoso import HoSoKenh, thu_muc_kenh

    # thu_muc_kenh("") = <root>/kenh (pathlib nuốt segment rỗng) — KHÔNG .parent
    # (bug bắt bởi test 05/09: .parent trỏ lên data root, danh sách luôn rỗng)
    goc = thu_muc_kenh("")
    ra = []
    if goc.is_dir():
        for d in sorted(goc.iterdir()):
            hs = HoSoKenh.doc(d.name) if d.is_dir() else None
            if hs is not None:
                mot = _dc.asdict(hs)
                # frame minh hoạ là file JPEG cạnh hoso.json, không nằm trong nó
                mot["so_frame"] = len(list((d / "frames").glob("f*.jpg")))
                ra.append(mot)
    with _kenh_lock:
        dang = {k: dict(v) for k, v in _kenh_dang_do.items()}
    return {"kenh": ra, "dang_do": dang,
            "nghien_cuu": _duoc_nghien_cuu_kenh(request)}


def _chay_do_kenh(link: str, ten: str, do_lai: bool = False,
                  so_video: int = 5, ten_phong_cach: str = "",
                  nguoi_tao: str = "") -> None:
    from autoedit.kenh.do_kenh import do_kenh

    try:
        do_kenh(link, ten=ten, do_lai=do_lai, so_video=so_video,
                ten_phong_cach=ten_phong_cach, nguoi_tao=nguoi_tao)
        with _kenh_lock:
            _kenh_dang_do.pop(ten, None)
        print(f"[kenh] «{ten}» đo xong", flush=True)
    except Exception as exc:  # noqa: BLE001 — trạng thái lỗi hiện trên UI
        with _kenh_lock:
            _kenh_dang_do[ten] = {"tt": "loi", "loi": str(exc)[:300]}
        print(f"[kenh] «{ten}» LỖI: {exc}", flush=True)


@app.post("/api/kenh")
def api_kenh_them(req: KenhRequest, request: Request):
    """Nghiên cứu kênh MỚI — chỉ manager/owner (qua CRM); đo chạy nền."""
    _require_auth(request)
    if not _duoc_nghien_cuu_kenh(request):
        raise HTTPException(403, "Chỉ manager/owner được nghiên cứu kênh mới")
    from autoedit.kenh.do_kenh import DoKenhError, slug_tu_link
    from autoedit.kenh.hoso import HoSoKenh

    from autoedit.kenh.do_kenh import SO_VIDEO_TRAN, slug_tu_ten

    # FRAMING BỘ-OUTLIER (Đợt 3): nhận NHIỀU link (mỗi dòng 1 video outlier;
    # link kênh vẫn nhận) — do_kenh tự tách + đo gộp median cả bộ
    link = (req.link or "").strip()
    if not link:
        raise HTTPException(422, "Dán link video outlier của ngách — mỗi dòng 1 link "
                                 "(link kênh cũng nhận)")
    ten_pc = (req.ten or "").strip()
    if not ten_pc:
        raise HTTPException(422, "Đặt tên phong cách (vd 'Fern chậm rãi') — thư viện "
                                 "cần tên đọc được, không dùng slug link")
    so_video = max(1, min(SO_VIDEO_TRAN, int(req.so_video or 5)))
    try:
        ten = slug_tu_ten(ten_pc)
    except DoKenhError as exc:
        raise HTTPException(422, str(exc))
    if HoSoKenh.doc(ten) is not None:
        raise HTTPException(409, f"Kênh «{ten}» đã có trong thư viện — dùng nút Đo lại nếu muốn đo mới")
    with _kenh_lock:
        if ten in _kenh_dang_do and _kenh_dang_do[ten].get("tt") == "dang_do":
            raise HTTPException(409, f"Kênh «{ten}» đang đo dở")
        _kenh_dang_do[ten] = {"tt": "dang_do"}
    threading.Thread(target=_chay_do_kenh,
                     args=(link, ten, False, so_video, ten_pc, current_user(request)),
                     daemon=True, name=f"kenh-{ten}").start()
    return {"ok": True, "ten": ten,
            "ghi_chu": f"đang tải + đo nền {so_video} video 360p (~vài phút) — F5 tab này"}


@app.get("/api/kenh/{ten}/frame/{so}")
def api_kenh_frame(ten: str, so: int, request: Request):
    """Frame minh hoạ cắt từ video gốc lúc đo (user 05/09) — mọi vai xem được."""
    _require_auth(request)
    import re as _re

    from autoedit.kenh.hoso import thu_muc_kenh

    if not _re.fullmatch(r"[\w.-]{1,80}", ten) or not 1 <= so <= 12:
        raise HTTPException(422, "Tham số không hợp lệ")
    f = thu_muc_kenh(ten) / "frames" / f"f{so}.jpg"
    if not f.is_file():
        raise HTTPException(404, "Không có frame này")
    return FileResponse(f, media_type="image/jpeg",
                        headers={"Cache-Control": "max-age=86400"})


@app.post("/api/kenh/{ten}/mo-ta")
def api_kenh_viet_lai_mo_ta(ten: str, request: Request):
    """Viết lại MÔ TẢ từ số đo đã cache — 1 lượt LLM, KHÔNG tải lại video.
    Dùng khi hồ sơ cũ thiếu mô tả hoặc muốn bản gọn hơn sau khi đổi prompt."""
    _require_auth(request)
    if not _duoc_nghien_cuu_kenh(request):
        raise HTTPException(403, "Chỉ manager/owner được viết lại mô tả")
    from autoedit.kenh.hoso import HoSoKenh
    from autoedit.kenh.mo_ta import sinh_mo_ta

    hs = HoSoKenh.doc(ten)
    if hs is None:
        raise HTTPException(404, "Không thấy kênh trong thư viện")
    try:
        hs.mo_ta = sinh_mo_ta(hs)
    except Exception as exc:  # noqa: BLE001 — lỗi LLM trả thẳng cho UI
        raise HTTPException(502, f"LLM không viết được mô tả: {exc}")
    hs.ghi()
    return {"ok": True, "mo_ta": hs.mo_ta}


@app.post("/api/kenh/{ten}/do-lai")
def api_kenh_do_lai(ten: str, request: Request):
    _require_auth(request)
    if not _duoc_nghien_cuu_kenh(request):
        raise HTTPException(403, "Chỉ manager/owner được đo lại kênh")
    from autoedit.kenh.hoso import HoSoKenh

    hs = HoSoKenh.doc(ten)
    if hs is None:
        raise HTTPException(404, "Không thấy kênh trong thư viện")
    if not hs.link:
        raise HTTPException(422, "Hồ sơ cũ không lưu link gốc — xoá kênh rồi nghiên cứu lại bằng link")
    with _kenh_lock:
        if _kenh_dang_do.get(ten, {}).get("tt") == "dang_do":
            raise HTTPException(409, "Kênh đang đo dở")
        _kenh_dang_do[ten] = {"tt": "dang_do"}
    # Giữ quy mô cũ (đo 8 video thì đo lại vẫn 8) — chỉ dùng tới khi kho video
    # trống (kênh đời cũ); kho có sẵn thì do_kenh phân tích thẳng, không tải.
    from autoedit.kenh.do_kenh import SO_VIDEO, SO_VIDEO_TRAN
    so_video = min(max(len(hs.nguon or []), SO_VIDEO), SO_VIDEO_TRAN)
    threading.Thread(target=_chay_do_kenh,
                     args=(hs.link, ten, True, so_video, hs.ten_phong_cach, hs.nguoi_tao),
                     daemon=True, name=f"kenh-{ten}").start()
    return {"ok": True, "ghi_chu": "đang đo lại nền"}


@app.delete("/api/kenh/{ten}")
def api_kenh_xoa(ten: str, request: Request):
    _require_auth(request)
    if not _duoc_nghien_cuu_kenh(request):
        raise HTTPException(403, "Chỉ manager/owner được xoá kênh")
    import re as _re
    import shutil as _shutil

    from autoedit.kenh.hoso import thu_muc_kenh

    if not _re.fullmatch(r"[\w.-]{1,80}", ten):
        raise HTTPException(422, "Tên kênh không hợp lệ")
    d = thu_muc_kenh(ten)
    if not d.is_dir():
        raise HTTPException(404, "Không thấy kênh")
    _shutil.rmtree(d, ignore_errors=True)
    return {"ok": True}


@app.get("/mockup")
def trang_mockup(request: Request):
    """Mockup user duyet 04/09 — dat canh code lam chuan so (index.html phai khop)."""
    _require_auth(request)
    return FileResponse(Path(__file__).parent / "static" / "mockup_de_xuat.html")


@app.get("/mockup-processing")
def trang_mockup_processing(request: Request):
    """Mockup Processing user duyệt 05/09 — đặt cạnh code làm chuẩn so (index.html phải khớp)."""
    _require_auth(request)
    return FileResponse(Path(__file__).parent / "static" / "mockup_processing.html")


@app.get("/api/report/{project_id}")
def api_report(project_id: str, request: Request):
    """report.html của 1 chương — dòng lịch sử Processing ấn vào mở ra luôn."""
    _require_auth(request)
    pdir = _aigen_pdir(project_id)
    try:
        rp = json.loads((pdir / "project.json").read_text(encoding="utf-8")).get("report_path")
    except Exception:  # noqa: BLE001
        rp = None
    if not rp or not Path(rp).is_file():
        raise HTTPException(404, "Chương này chưa có report.html")
    return FileResponse(rp)


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
            chi_phi = 0.0
            for pid in (j.project_id or "").split(","):
                pid = pid.strip()
                if pid and (PROJECTS_DIR / pid / "aigen_duyet.json").is_file():
                    try:
                        ph = json.loads((PROJECTS_DIR / pid / "aigen_duyet.json")
                                        .read_text(encoding="utf-8"))
                        tt = ph.get("trang_thai")
                        duyet.append({"project_id": pid, "trang_thai": tt})
                        # Tiền AI của job, cùng biểu giá UI Generation: ảnh
                        # $0.03/phương án (ảnh _ref editor tự đưa miễn phí),
                        # video $0.05/motif có ảnh chốt. Tính ở server để job
                        # XONG RỒI lịch sử vẫn còn số (UI cũ chỉ tính job sống).
                        for m in ph.get("motif", []):
                            pa = m.get("phuong_an", [])
                            chi_phi += 0.03 * sum(1 for p in pa
                                                  if "_ref" not in p.get("file", ""))
                            if tt == "da_gen_video" and any(p.get("chon") for p in pa):
                                chi_phi += 0.05
                    except Exception:  # noqa: BLE001
                        pass
            d["duyet"] = duyet
            d["chi_phi"] = round(chi_phi, 2)
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
                        "report_ok": bool(pd.get("report_path")
                                          and Path(pd["report_path"]).is_file()),
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


def _doc_mmss(chuoi: str, toi_thieu: float = 60.0) -> float:
    """'28:25' -> 1705s; '1:02:15' -> 3735s. Sai định dạng thì ValueError tiếng Việt."""
    phan = (chuoi or "").strip().split(":")
    if not (2 <= len(phan) <= 3) or not all(p.isdigit() for p in phan):
        raise ValueError("nhập thời lượng dạng mm:ss (vd 28:25)")
    phan = [int(p) for p in phan]
    giay = phan[-1] + phan[-2] * 60 + (phan[0] * 3600 if len(phan) == 3 else 0)
    if giay < toi_thieu:
        raise ValueError(f"thời lượng phải >= {toi_thieu:.0f}s")
    return float(giay)


def _doc_tooltip(dong: list[str]) -> list[tuple[float, float]]:
    """["0:31=71", "0:00=119%"] -> [(giay, phan_tram)] — editor gõ tay khi di
    chuột đọc tooltip trên YouTube Studio (ảnh không có nhãn trục để OCR)."""
    ra: list[tuple[float, float]] = []
    for d in dong:
        if "=" not in d:
            raise ValueError(f"tooltip '{d}' thiếu dấu '=' (vd 0:31=71)")
        mmss, pct = d.split("=", 1)
        giay = _doc_mmss(mmss, toi_thieu=0.0)
        pct = pct.strip().rstrip("%")
        if not pct.replace(".", "", 1).isdigit():
            raise ValueError(f"tooltip '{d}': phần trăm không hợp lệ")
        ra.append((giay, float(pct)))
    return ra


class JobRequest(BaseModel):
    folder: str
    # AI LÀM (user 05/09): vào thẳng (token, không qua CRM) thì không có SSO —
    # UI cho tự khai tên (localStorage) gửi kèm; có CRM thì header luôn thắng.
    nguoi: str = ""
    niche: str = ""
    align_backend: str = "auto"
    no_sub: bool = False
    aigen: bool = False        # user 04/09: cổng tắt/bật AI gen khi nộp job
    # 3 PHƯƠNG ÁN DỰNG (user 05/09): stock | ai | tu_quay — logic/phong cách khác
    # nhau, học từ kênh ref thay luật cứng. PA "ai" tự kéo aigen bật ở make.
    phuong_an: str = "stock"
    kenh_ref: str = ""         # link kênh YouTube ref (đo trong worker, cache theo kênh)
    # RETENTION (user 04/09): ảnh chụp biểu đồ giữ chân tập CŨ + thời lượng nó
    retention_anh_b64: str = ""    # dataURL/base64 PNG-JPG; rỗng = không dùng
    retention_dai: str = ""        # "28:25" hoặc "1:02:15"
    # TOOLTIP (04/09): editor di chuột đọc thêm 1-2 điểm "mm:ss=phần_trăm" khi
    # ảnh KHÔNG có nhãn trục để OCR đọc (vd ảnh gốc bị crop) — mỗi phần tử
    # "0:31=71" hoặc "0:31=71%". Rỗng = không dùng, OCR/fallback cũ tự lo.
    retention_tooltip: list[str] = []


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
            tooltip_giay = _doc_tooltip(req.retention_tooltip)
            raw = req.retention_anh_b64.split(",", 1)[-1]   # bỏ đầu dataURL nếu có
            anh = folder / "retention.png"
            anh.write_bytes(_b64.b64decode(raw))
            kq = phan_tich_anh(anh, dai_s, tooltip_giay=tooltip_giay or None)
            (folder / _RET).write_text(
                _json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
            bao_cao_ret = " · ".join(kq["bao_cao"])
        except (AnhKhongDoDuoc, ValueError) as exc:
            raise HTTPException(422, f"Ảnh retention không đo được: {exc}")

    conn = _queue_conn()
    try:
        jid = q.add_job(conn, str(folder),
                        nguoi=current_user(request) or req.nguoi.strip()[:40],
                        opts={"niche": req.niche, "align_backend": req.align_backend,
                              "no_sub": req.no_sub, "aigen": req.aigen,
                              "phuong_an": req.phuong_an, "kenh_ref": req.kenh_ref})
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
