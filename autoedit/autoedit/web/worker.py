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
    except Exception as exc:
        # Fail-open (máy dev không có gateway vẫn chạy được bằng .env) NHƯNG phải
        # để lại vết: nuốt im thì khoá không tới nơi mà job vẫn chạy tiếp rồi chết
        # tận stage source — người đã nhập đủ khoá không hiểu vì sao (30/08).
        log.write(f"⚠ Không nạp được khoá từ két V3: {exc}\n")
        log.write("  -> dùng .env nếu có. Kiểm tra gateway 9000 và General › API Keys.\n")
        log.flush()
    env = dict(os.environ, PYTHONPATH=str(root),
               PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    project_id = ""
    proc = subprocess.Popen(
        [sys.executable, "-m", "autoedit.cli"] + args,
        cwd=str(root), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", bufsize=1)
    dem = 0
    for line in proc.stdout or []:
        log.write(line)
        log.flush()
        m = _STAGE_RE.search(line)
        if m:
            q.set_stage(conn, job_id, m.group(1).lower())
        elif "Tạo project:" in line:
            project_id = line.split(":")[-1].strip()
        # Dòng có nội dung -> đẩy lên UI. Ghi MỌI dòng thì mỗi job vài nghìn lượt
        # UPDATE; commit theo cụm 5 dòng là đủ mượt mà không đì SQLite.
        sach = line.strip()
        if sach and not sach.startswith(("━", "│", "└", "┌", "╰", "╭")):
            q.set_dong_cuoi(conn, job_id, sach)
            dem += 1
            if dem % 5 == 0:
                conn.commit()
    conn.commit()
    return proc.wait(), project_id


def run_one(conn, job: q.Job, root: Path, logs_dir: Path) -> None:
    """Chạy 1 job (có thể nhiều chương) tới khi xong.

    Mỗi CHƯƠNG là một lượt `make` riêng -> một draft riêng, đúng mô hình R4.

    Chương lỗi KHÔNG dừng cả tập: chạy nốt chương còn lại rồi báo rõ chương nào hỏng.
    Chương nào xong là GIAO NGAY ra Compose Timeline, không đợi chương chậm nhất.
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
    if opts.get("aigen"):
        extra += ["--aigen"]

    log_path = _log_path(logs_dir, job.id)
    ids: list[str] = []
    chuong_loi: list[str] = []
    canh_bao = ""
    try:
        chapters = chapters_of(folder)
        with open(log_path, "w", encoding="utf-8") as log:
            log.write(f"Job {job.id}: {folder}\n{len(chapters)} chương: "
                      f"{', '.join(c.name for c in chapters)}\n\n")
            # Giao DẦN: xoá kết quả lần trước một lần ở đây, rồi mỗi chương xong là
            # đổ ra ngay. 31/08 user hỏi "C7 C8 đã trả ra kết quả chưa?" — chúng dựng
            # xong từ lâu nhưng phải đợi C9 mới được giao.
            _don_giao(folder, log)
            tom_tat: list[dict] = []
            for i, ch in enumerate(chapters, start=1):
                log.write(f"\n{'=' * 70}\nCHƯƠNG {i}/{len(chapters)}: {ch.name}\n{'=' * 70}\n")
                log.flush()
                q.set_chuong(conn, job.id, f"{ch.name} ({i}/{len(chapters)})")
                code, pid = _run_cli(["make", str(ch)] + extra, root, log, conn, job.id)
                # CHỈ giao chương chạy XONG: project_id được in ngay lúc tạo project,
                # nên chương chết giữa chừng cũng có pid — giao ra là timeline dở.
                if pid and code == 0:
                    ids.append(pid)
                    _giao_ngay(root, folder, ch.name, pid, tom_tat,
                               xong_het=(i == len(chapters)), log=log)
                if code != 0:
                    # KHÔNG dừng cả tập: 31/08 chương cuối C9 chết vì Pexels trả 504
                    # mà H/C7/c8 đã dựng xong — huỷ hết thì nhân sự chẳng có gì làm.
                    # Chạy nốt chương còn lại, cuối cùng báo rõ chương nào hỏng.
                    chuong_loi.append(ch.name)
                    log.write(f"\n⚠ Chương {ch.name} lỗi (mã {code}) — bỏ qua, "
                              f"chạy tiếp chương sau.\n")
                    log.flush()

            # Chương cuối lỗi -> README vẫn đang ghi "ĐANG CHẠY". Viết lại lần cuối
            # cho khớp thực tế: đã dừng, đây là tất cả những gì có.
            if ids and chuong_loi:
                _chot_giao(folder, tom_tat, log)
            if not ids:
                canh_bao = "Không chương nào dựng xong — chưa giao được gì."
                log.write(f"⚠ {canh_bao}\n")
    except Exception as exc:                      # spawn hỏng — vẫn phải đóng job
        q.finish(conn, job.id, ok=False, error=f"Không chạy được: {exc}")
        return

    if chuong_loi:
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-700:]
        xong, loi = len(ids), ", ".join(chuong_loi)
        # Có chương xong thì vẫn GIAO -> báo 'lỗi một phần', không phải hỏng cả tập:
        # nhân sự làm trước phần đã xong, chỉ nộp lại chương hỏng.
        thong_bao = (
            f"{xong} chương đã xong và ĐÃ GIAO. Lỗi {len(chuong_loi)} chương: {loi}"
            f" — nộp lại tập này sẽ chỉ dựng chương lỗi.\n\nĐuôi log:\n{tail}"
            if xong else f"Mọi chương đều lỗi: {loi}\n\nĐuôi log:\n{tail}"
        )
        q.finish(conn, job.id, ok=bool(xong), project_id=",".join(ids), error=thong_bao)
        return

    q.finish(conn, job.id, ok=True, project_id=",".join(ids), error=canh_bao)


def _don_giao(folder: Path, log) -> None:
    """Xoá kết quả lần trước, MỘT LẦN trước khi giao dần."""
    try:
        from autoedit.web.compose import don_thu_muc_giao

        don_thu_muc_giao(folder)
    except Exception as exc:      # không dọn được thì vẫn dựng, chỉ ghi lại
        log.write(f"⚠ Không dọn được thư mục giao cũ: {exc}\n")
        log.flush()


def _giao_ngay(root: Path, folder: Path, ten_chuong: str, pid: str,
               tom_tat: list, xong_het: bool, log) -> None:
    """Đổ 1 chương vừa xong ra Compose Timeline — nhân sự dùng được ngay."""
    try:
        from autoedit.web.compose import compose_dan

        dest = compose_dan(folder, ten_chuong, root / "projects" / pid,
                           tom_tat, xong_het=xong_het)
        log.write(f"✓ Đã giao chương {ten_chuong}: {dest}\n")
    except Exception as exc:
        # Giao hỏng KHÔNG huỷ phần dựng: draft vẫn nằm trong projects/, lấy tay được.
        log.write(f"⚠ Chương {ten_chuong} dựng xong nhưng chưa giao được: {exc}\n")
    log.flush()


def _chot_giao(folder: Path, tom_tat: list, log) -> None:
    """Viết lại DOC_TRUOC.txt lần cuối khi job dừng mà chương cuối lỗi — nếu không
    README vẫn ghi 'ĐANG CHẠY' mãi, nhân sự tưởng còn chương sắp về."""
    try:
        from autoedit.web.compose import thu_muc_giao, write_readme

        write_readme(thu_muc_giao(folder), str(folder), tom_tat, xong_het=True)
    except Exception as exc:
        log.write(f"⚠ Không cập nhật được DOC_TRUOC.txt: {exc}\n")
        log.flush()


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
