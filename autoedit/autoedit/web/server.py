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


@app.get("/api/me")
def api_me(request: Request):
    """Danh tính + quyền hiện tại — frontend dùng để hiện tên và bật/tắt nút."""
    _require_auth(request)
    nguoi = current_user(request)
    vai = current_role(request)
    return {"nguoi": nguoi, "vai": vai, "qua_crm": behind_crm(request),
            # owner xem/huỷ được job của mọi người; vai khác chỉ job của mình
            "xem_het": is_admin(request)}


def _trong_nas(p: Path) -> Path:
    """Ép đường dẫn phải NẰM TRONG gốc NAS. Raise HTTPException nếu không.

    Nhân sự dán đường dẫn tự do nên đây là rào duy nhất — không chặn thì bơm được
    đường dẫn bất kỳ vào worker (worker chạy lệnh trên thư mục đó).
    """
    try:
        real = Path(p).expanduser().resolve()
        real.relative_to(NAS_ROOT.resolve())
    except (ValueError, OSError):
        raise HTTPException(422, f"Đường dẫn phải nằm trong {NAS_ROOT}")
    return real


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
            if j.status == "queued":
                d["wait_ahead"] = q.wait_ahead(conn, j.id)
            rows.append(d)
        return {"jobs": rows, "stats": q.stats(conn),
                "unseen": q.count_unseen(conn, nguoi), "nguoi": nguoi}
    finally:
        conn.close()


class JobRequest(BaseModel):
    folder: str
    niche: str = ""
    align_backend: str = "auto"
    no_sub: bool = False


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

    conn = _queue_conn()
    try:
        jid = q.add_job(conn, str(folder), nguoi=current_user(request),
                        opts={"niche": req.niche, "align_backend": req.align_backend,
                              "no_sub": req.no_sub})
        job = q.get_job(conn, jid)
        return {"job": job.to_dict(), "wait_ahead": q.wait_ahead(conn, jid)}
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
