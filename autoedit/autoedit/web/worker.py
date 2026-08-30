"""Worker chạy job dựng video từ hàng đợi.

Mỗi job = 1 tiến trình con gọi `autoedit.cli make <folder>`, log ra file. Tiến trình
con (không phải thread) vì: job chạy ~24 phút và ngốn CPU; chạy trong tiến trình web
sẽ nghẹt request khác. Đây cũng là khuôn đã verify ở R8.

Worker thread poll hàng đợi mỗi POLL_SECONDS. Số worker = queue.MAX_WORKERS.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from autoedit.web import queue as q

POLL_SECONDS = 5
_STAGE_RE = re.compile(r"━━ \[\d+/\d+\] (\w+)")   # dòng tiến độ của lệnh `run`

_stop = threading.Event()
_threads: list[threading.Thread] = []


def _log_path(logs_dir: Path, job_id: int) -> Path:
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir / f"job_{job_id}.log"


def chapters_of(folder: Path) -> list[Path]:
    """Thư mục TẬP -> danh sách thư mục chương, ĐÚNG THỨ TỰ H → C1..Cn → E.

    Quy ước OUTLIERY: `<tập>/RenderY/{H,C1,C2,...,E}`. Sắp theo tên là sai cả hai
    đầu ("E" trước "H", "C10" trước "C2") nên dùng khoá thứ tự của chapters.py.
    """
    from autoedit.web.chapters import doc_chuong

    chuong, _ = doc_chuong(Path(folder))
    return [c.path for c in chuong]


def _run_cli(args: list[str], root: Path, log, conn, job_id: int) -> tuple[int, str]:
    """Chạy 1 lệnh CLI, ghi log, bắt stage + project_id. Trả (mã thoát, project_id)."""
    # Khoá API lấy từ két V3 (General › API Keys) — nguồn sự thật duy nhất; việc nào
    # két chưa cấp phát thì giữ .env, nên máy dev không cần gateway. Fail-open.
    try:
        from autoedit.web.ket_v3 import nap_env

        nap_env()
    except Exception:
        pass
    env = dict(os.environ, PYTHONPATH=str(root),
               PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    project_id = ""
    proc = subprocess.Popen(
        [sys.executable, "-m", "autoedit.cli"] + args,
        cwd=str(root), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", bufsize=1)
    for line in proc.stdout or []:
        log.write(line)
        log.flush()
        m = _STAGE_RE.search(line)
        if m:
            q.set_stage(conn, job_id, m.group(1).lower())
        elif "Tạo project:" in line:
            project_id = line.split(":")[-1].strip()
    return proc.wait(), project_id


def run_one(conn, job: q.Job, root: Path, logs_dir: Path) -> None:
    """Chạy 1 job (có thể nhiều chương) tới khi xong.

    Mỗi CHƯƠNG là một lượt `make` riêng -> một draft riêng, đúng mô hình R4. Chương
    lỗi thì DỪNG (chương sau vô nghĩa nếu chương trước hỏng), báo rõ chương nào.
    """
    folder = Path(job.job_folder)
    if not folder.is_dir():
        q.finish(conn, job.id, ok=False, error=f"Không thấy folder: {folder}")
        return

    opts = job.opts or {}
    extra: list[str] = []
    if opts.get("niche"):
        extra += ["--channel", str(opts["niche"])]
    if opts.get("align_backend"):
        extra += ["--align-backend", str(opts["align_backend"])]
    if opts.get("no_sub"):
        extra += ["--no-sub"]

    log_path = _log_path(logs_dir, job.id)
    ids: list[str] = []
    canh_bao = ""
    try:
        chapters = chapters_of(folder)
        with open(log_path, "w", encoding="utf-8") as log:
            log.write(f"Job {job.id}: {folder}\n{len(chapters)} chương: "
                      f"{', '.join(c.name for c in chapters)}\n\n")
            for i, ch in enumerate(chapters, start=1):
                log.write(f"\n{'=' * 70}\nCHƯƠNG {i}/{len(chapters)}: {ch.name}\n{'=' * 70}\n")
                log.flush()
                code, pid = _run_cli(["make", str(ch)] + extra, root, log, conn, job.id)
                if pid:
                    ids.append(pid)
                if code != 0:
                    tail = log_path.read_text(encoding="utf-8", errors="replace")[-800:]
                    q.finish(conn, job.id, ok=False, project_id=",".join(ids),
                             error=f"Chương {ch.name} lỗi (mã {code}). Đuôi log:\n{tail}")
                    return

            # Gom kết quả ra Compose Timeline — bước GIAO cho nhân sự.
            # Lỗi ở đây KHÔNG huỷ phần dựng đã xong: báo cảnh báo, giữ job là 'done'
            # để nhân sự còn lấy được từ project gốc.
            try:
                q.set_stage(conn, job.id, "compose")
                log.write(f"\n{'=' * 70}\nGIAO KẾT QUẢ\n{'=' * 70}\n")
                log.flush()
                dest = _compose(root, folder, ids, log)
                log.write(f"✓ Đã giao: {dest}\n")
            except Exception as exc:
                canh_bao = f"Dựng xong nhưng chưa giao được ra Compose Timeline: {exc}"
                log.write(f"⚠ {canh_bao}\n")
    except Exception as exc:                      # spawn hỏng — vẫn phải đóng job
        q.finish(conn, job.id, ok=False, error=f"Không chạy được: {exc}")
        return

    q.finish(conn, job.id, ok=True, project_id=",".join(ids), error=canh_bao)


def _compose(root: Path, folder: Path, project_ids: list[str], log) -> Path:
    """Gom kết quả các chương về `<tập>/RenderY/Compose Timeline/`."""
    from autoedit.web.compose import compose_job

    dirs = [root / "projects" / pid for pid in project_ids if pid]
    if not dirs:
        raise RuntimeError("không có project nào để giao")
    return compose_job(folder, dirs)


def _loop(root: Path, logs_dir: Path, db: Optional[Path]) -> None:
    """Vòng đời 1 worker: nhận job -> chạy -> lặp. Mỗi worker giữ connection riêng."""
    conn = q.connect(db)
    while not _stop.is_set():
        try:
            job = q.claim_next(conn)
        except Exception:
            job = None                            # sổ bận/khoá — thử lại lượt sau
        if job is None:
            _stop.wait(POLL_SECONDS)
            continue
        try:
            run_one(conn, job, root, logs_dir)
        except Exception as exc:                  # lỗi lạ — đóng job, worker sống tiếp
            try:
                q.finish(conn, job.id, ok=False, error=str(exc)[:2000])
            except Exception:
                pass


def start(root: Path, logs_dir: Path, db: Optional[Path] = None,
          workers: int = q.MAX_WORKERS) -> int:
    """Khởi động worker nền. Trả số worker đã chạy. Gọi 1 lần lúc server lên."""
    if _threads:
        return len(_threads)
    conn = q.connect(db)
    orphans = q.requeue_orphans(conn)             # server restart -> trả job kẹt về hàng đợi
    conn.close()
    _stop.clear()
    for i in range(max(1, workers)):
        t = threading.Thread(target=_loop, args=(root, logs_dir, db),
                             name=f"rendery-worker-{i + 1}", daemon=True)
        t.start()
        _threads.append(t)
    if orphans:
        print(f"[queue] trả {orphans} job mồ côi về hàng đợi (server vừa khởi động)",
              flush=True)
    return len(_threads)


def stop(timeout: float = 2.0) -> None:
    """Dừng worker (job đang chạy vẫn chạy tiếp ở tiến trình con)."""
    _stop.set()
    for t in _threads:
        t.join(timeout=timeout)
    _threads.clear()
