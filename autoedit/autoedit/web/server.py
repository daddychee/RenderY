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
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]      # thư mục autoedit/ (chứa .env, projects/)
PROJECTS_DIR = ROOT / "projects"
JOBS_DIR = ROOT / ".web_jobs"

# Key được phép sửa qua web. Whitelist: tránh ai đó ghi biến lạ vào .env.
SETTINGS_KEYS = [
    "PEXELS_API_KEY", "PIXABAY_API_KEY",
    "ENVATO_EMAIL", "VECTEEZY_EMAIL",
    "GLM_API_KEY", "ANTHROPIC_API_KEY", "SERPER_API_KEY",
    "RENDERY_WEB_TOKEN",
]
SECRET_KEYS = {k for k in SETTINGS_KEYS if k.endswith(("_KEY", "_TOKEN"))}

app = FastAPI(title="RenderY")
_jobs: dict[str, dict] = {}          # project_id -> {status, stage, started_at, log}
_jobs_lock = threading.Lock()


# ------------------------------ xác thực ------------------------------------
def _require_auth(request: Request) -> None:
    """Bật khi có RENDERY_WEB_TOKEN. Không đặt = mở (hợp lý khi bind 127.0.0.1)."""
    token = os.getenv("RENDERY_WEB_TOKEN", "").strip()
    if not token:
        return
    sent = request.headers.get("x-rendery-token") or request.query_params.get("token", "")
    if sent != token:
        raise HTTPException(401, "Sai hoặc thiếu token (đặt RENDERY_WEB_TOKEN trong .env)")


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


@app.get("/api/sources")
def api_sources(request: Request):
    """Nguồn footage nào đang dùng được — cùng dữ liệu với lệnh `sub-status`."""
    _require_auth(request)
    from autoedit.sourcer.pexels import collect_pexels_keys
    from autoedit.sourcer.pixabay import collect_pixabay_keys
    from autoedit.sourcer.subscription import SITES, profile_exists

    env = _read_env()
    out = [
        {"name": "pexels", "ready": bool(collect_pexels_keys(env)), "need": "PEXELS_API_KEY"},
        {"name": "pixabay", "ready": bool(collect_pixabay_keys(env)), "need": "PIXABAY_API_KEY"},
    ]
    for site, cfg in SITES.items():
        out.append({"name": site,
                    "ready": bool(env.get(cfg["env"], "").strip()) and profile_exists(site),
                    "need": f"{cfg['env']} + đăng nhập trình duyệt"})
    return {"sources": out}


@app.get("/", response_class=HTMLResponse)
def index():
    p = Path(__file__).parent / "static" / "index.html"
    if not p.is_file():
        return HTMLResponse("<h1>RenderY</h1><p>Thiếu static/index.html</p>", status_code=500)
    return FileResponse(p)
