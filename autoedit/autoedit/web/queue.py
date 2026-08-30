"""Hàng đợi job dựng video — SQLite, BỀN qua restart.

Vì sao không dùng `BackgroundTasks` của CRM OUTLIERY (xem docs/TICH_HOP_CRM.md):
1. Nó chạy trong CHÍNH tiến trình uvicorn 1 worker phục vụ cả 6 app phụ — job dựng
   video ~24 phút sẽ nghẹt threadpool của toàn hệ thống.
2. Registry của nó là dict in-memory, MẤT KHI RESTART — mà runbook công ty ghi rõ
   "sửa code xong phải Stop rồi Start lại tác vụ".
3. Không có giới hạn đồng thời.

Thiết kế:
- 1 bảng `jobs` trong SQLite riêng (không lẫn với sổ kho footage của padoma).
- Worker nhận job bằng UPDATE...WHERE status='queued' có điều kiện — chống 2 worker
  cùng nhận 1 job mà không cần lock ứng dụng.
- MAX_WORKERS = 2 (đo thật 30/08/2026: 4 job ffmpeg song song chỉ nhanh hơn tuần tự
  1.5× vì ffmpeg đã tự đa luồng; RAM còn 15.4GB; còn 6 app khác đang phục vụ team).
- Job mồ côi (status='running' mà server vừa khởi động) được trả về hàng đợi.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

MAX_WORKERS = 2          # đo thật — xem docstring
STALE_AFTER = 4 * 3600   # job 'running' quá 4 tiếng coi như chết (job thường ~24 phút)

# Ước tính thời gian từng stage (giây) cho ĐẾM NGƯỢC — đo trên video 20 phút/434 câu.
# Dùng làm mốc ban đầu; sau vài job thật thì lấy trung bình lịch sử thay vào.
STAGE_SECONDS = {
    "align": 2, "direct": 90, "enrich": 30, "cut": 60, "music": 20,
    "source": 900, "rank": 120, "assemble": 240, "report": 5,
    "compose": 30,   # gom kết quả ra NAS (đo thật: NAS ghi 362 MB/s)
}
TOTAL_SECONDS = sum(STAGE_SECONDS.values())

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    job_folder   TEXT NOT NULL,          -- folder chương trên NAS
    project_id   TEXT NOT NULL DEFAULT '',
    nguoi        TEXT NOT NULL DEFAULT '',   -- X-Remote-User (SSO từ CRM)
    status       TEXT NOT NULL DEFAULT 'queued',  -- queued|running|done|failed|canceled
    stage        TEXT NOT NULL DEFAULT '',   -- stage đang chạy
    created_at   TEXT NOT NULL,
    started_at   TEXT,
    finished_at  TEXT,
    error        TEXT,
    seen         INTEGER NOT NULL DEFAULT 0, -- 0 = xong mà user CHƯA XEM -> badge CRM
    opts         TEXT NOT NULL DEFAULT '{}'  -- JSON tuỳ chọn (niche, align_backend...)
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_nguoi ON jobs(nguoi, seen);
"""


def db_path(root: Optional[Path] = None) -> Path:
    return Path(root or Path.cwd()) / "jobs.db"


def connect(path: Optional[Path] = None) -> sqlite3.Connection:
    """Mở sổ hàng đợi. WAL để worker ghi không chặn web đọc."""
    p = Path(path) if path else db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Job:
    id: int
    job_folder: str
    project_id: str
    nguoi: str
    status: str
    stage: str
    created_at: str
    started_at: Optional[str]
    finished_at: Optional[str]
    error: Optional[str]
    seen: int
    opts: dict

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Job":
        d = dict(row)
        try:
            d["opts"] = json.loads(d.get("opts") or "{}")
        except json.JSONDecodeError:
            d["opts"] = {}
        return cls(**d)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["eta"] = self.eta()
        d["progress"] = self.progress()
        return d

    # ---------------------------- đếm ngược --------------------------------
    def progress(self) -> float:
        """% hoàn thành 0..1, tính theo THỜI LƯỢNG các stage đã xong (không phải số stage
        — stage `source` chiếm 64% thời gian, đếm đầu stage sẽ sai nặng)."""
        if self.status == "done":
            return 1.0
        if self.status in ("queued", "failed", "canceled") or not self.stage:
            return 0.0
        done = 0
        for name, secs in STAGE_SECONDS.items():
            if name == self.stage:
                return min(done / TOTAL_SECONDS, 0.99)
            done += secs
        return 0.0

    def eta(self) -> Optional[int]:
        """Giây còn lại, None nếu chưa chạy/đã xong."""
        if self.status != "running" or not self.started_at:
            return None
        p = self.progress()
        if p <= 0:
            return TOTAL_SECONDS
        try:
            t0 = datetime.fromisoformat(self.started_at)
        except ValueError:
            return None
        elapsed = (datetime.now(timezone.utc) - t0).total_seconds()
        # Ước theo tiến độ thật; kẹp về ước tính tĩnh khi tiến độ còn quá nhỏ
        remain = elapsed / p - elapsed if p > 0.05 else TOTAL_SECONDS - elapsed
        return max(int(remain), 0)


# ------------------------------ thao tác ------------------------------------
def add_job(conn: sqlite3.Connection, job_folder: str, nguoi: str = "",
            opts: Optional[dict] = None) -> int:
    """Xếp 1 job vào hàng đợi. Trả job id."""
    folder = str(job_folder).strip()
    if not folder:
        raise ValueError("Thiếu đường dẫn folder job")
    cur = conn.execute(
        "INSERT INTO jobs (job_folder, nguoi, created_at, opts) VALUES (?, ?, ?, ?)",
        (folder, nguoi, _now(), json.dumps(opts or {}, ensure_ascii=False)))
    conn.commit()
    return int(cur.lastrowid)


def get_job(conn: sqlite3.Connection, job_id: int) -> Optional[Job]:
    row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return Job.from_row(row) if row else None


def list_jobs(conn: sqlite3.Connection, nguoi: str = "", limit: int = 50) -> list[Job]:
    """Job mới nhất trước. `nguoi` rỗng = mọi người (dùng cho trang quản trị)."""
    if nguoi:
        rows = conn.execute("SELECT * FROM jobs WHERE nguoi=? ORDER BY id DESC LIMIT ?",
                            (nguoi, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [Job.from_row(r) for r in rows]


def claim_next(conn: sqlite3.Connection) -> Optional[Job]:
    """Worker nhận job kế tiếp. None nếu hàng đợi rỗng hoặc đã đủ MAX_WORKERS.

    Nhận bằng UPDATE...WHERE status='queued' — SQLite serialize ghi nên 2 worker
    không thể cùng nhận 1 job; `cursor.rowcount` cho biết ai thắng.
    """
    running = conn.execute(
        "SELECT COUNT(*) c FROM jobs WHERE status='running'").fetchone()["c"]
    if running >= MAX_WORKERS:
        return None
    row = conn.execute(
        "SELECT id FROM jobs WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
    if row is None:
        return None
    cur = conn.execute(
        "UPDATE jobs SET status='running', started_at=? WHERE id=? AND status='queued'",
        (_now(), row["id"]))
    conn.commit()
    if cur.rowcount == 0:
        return None            # worker khác nhận trước
    return get_job(conn, row["id"])


def set_stage(conn: sqlite3.Connection, job_id: int, stage: str) -> None:
    conn.execute("UPDATE jobs SET stage=? WHERE id=?", (stage, job_id))
    conn.commit()


def finish(conn: sqlite3.Connection, job_id: int, ok: bool,
           error: str = "", project_id: str = "") -> None:
    """Đóng job. seen=0 -> badge CRM đếm job xong mà user chưa xem."""
    conn.execute(
        "UPDATE jobs SET status=?, finished_at=?, error=?, seen=0,"
        " project_id=COALESCE(NULLIF(?,''), project_id) WHERE id=?",
        ("done" if ok else "failed", _now(), error[:2000], project_id, job_id))
    conn.commit()


def cancel(conn: sqlite3.Connection, job_id: int) -> bool:
    """Huỷ job CHƯA chạy. Job đang chạy không huỷ được (tiến trình con đã spawn)."""
    cur = conn.execute(
        "UPDATE jobs SET status='canceled', finished_at=? WHERE id=? AND status='queued'",
        (_now(), job_id))
    conn.commit()
    return cur.rowcount > 0


def mark_seen(conn: sqlite3.Connection, nguoi: str) -> int:
    """User đã xem kết quả -> tắt badge. Trả số job vừa đánh dấu."""
    cur = conn.execute(
        "UPDATE jobs SET seen=1 WHERE nguoi=? AND seen=0 AND status IN ('done','failed')",
        (nguoi,))
    conn.commit()
    return cur.rowcount


def count_unseen(conn: sqlite3.Connection, nguoi: str = "") -> int:
    """Số job xong mà chưa xem — CRM đọc để hiện badge sidebar."""
    if nguoi:
        row = conn.execute(
            "SELECT COUNT(*) c FROM jobs WHERE nguoi=? AND seen=0 AND status IN ('done','failed')",
            (nguoi,)).fetchone()
    else:
        row = conn.execute(
            "SELECT COUNT(*) c FROM jobs WHERE seen=0 AND status IN ('done','failed')").fetchone()
    return int(row["c"])


def requeue_orphans(conn: sqlite3.Connection, stale_after: int = STALE_AFTER) -> int:
    """Trả job mồ côi về hàng đợi. Gọi lúc server khởi động.

    Server bị Stop/Start (runbook: 'sửa code xong phải Stop rồi Start') sẽ giết tiến
    trình con, để lại job kẹt 'running' vĩnh viễn. Ở đây KHÔNG đoán tiến trình còn
    sống hay không — cứ khởi động lại là mọi job 'running' đều mồ côi, vì worker
    sống trong chính tiến trình này.
    """
    cur = conn.execute(
        "UPDATE jobs SET status='queued', started_at=NULL, stage='' WHERE status='running'")
    conn.commit()
    return cur.rowcount


def stats(conn: sqlite3.Connection) -> dict:
    """Tóm tắt cho trang chủ: đếm theo trạng thái + vị trí hàng đợi."""
    rows = conn.execute("SELECT status, COUNT(*) c FROM jobs GROUP BY status").fetchall()
    out = {r["status"]: r["c"] for r in rows}
    out["queued"] = out.get("queued", 0)
    out["running"] = out.get("running", 0)
    out["workers"] = MAX_WORKERS
    return out


def wait_ahead(conn: sqlite3.Connection, job_id: int) -> Optional[int]:
    """Ước giây phải CHỜ trước khi job này bắt đầu (job đang xếp hàng).

    Chia số job phía trước cho số worker rảnh — thô nhưng đủ để nhân sự biết
    'khoảng 1 tiếng nữa' thay vì nhìn màn hình trống.
    """
    job = get_job(conn, job_id)
    if job is None or job.status != "queued":
        return None
    ahead = conn.execute(
        "SELECT COUNT(*) c FROM jobs WHERE status='queued' AND id < ?", (job_id,)
    ).fetchone()["c"]
    running = conn.execute(
        "SELECT COUNT(*) c FROM jobs WHERE status='running'").fetchone()["c"]
    # (job phía trước + job đang chạy) chia đều cho worker
    luot = (ahead + running + MAX_WORKERS - 1) // MAX_WORKERS
    return max(luot, 1) * TOTAL_SECONDS if (ahead or running) else 0
