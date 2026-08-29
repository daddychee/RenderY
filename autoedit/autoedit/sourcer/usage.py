"""Usage log + phạt mềm chống trùng footage (P7).

Luật cứng DUY NHẤT: không lặp cùng clip trong cùng MỘT video (caller tự lọc
bằng used_in_video). Giữa các video cùng kênh: chỉ phạt mềm khi xếp ứng viên —
asset chưa dùng đứng trước asset đã dùng; hệ số chỉnh được, không cấm.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone


def log_usage(conn: sqlite3.Connection, channel: str, asset_key: str, video_id: str) -> None:
    conn.execute(
        "INSERT INTO asset_usage (channel, asset_key, video_id, used_at) VALUES (?,?,?,?)",
        (channel, asset_key, video_id, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def times_used(conn: sqlite3.Connection, channel: str, asset_key: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM asset_usage WHERE channel = ? AND asset_key = ?",
        (channel, asset_key),
    ).fetchone()
    return row["n"]


def soft_penalty_sort(
    conn: sqlite3.Connection, channel: str, candidates: list[dict],
) -> list[dict]:
    """Xếp lại ứng viên: ít dùng trước, giữ thứ tự relevance trong cùng nhóm.

    candidates: list dict có 'asset_key'. Stable sort -> relevance được bảo toàn.
    """
    if not channel:
        return candidates
    return sorted(candidates, key=lambda c: times_used(conn, channel, c["asset_key"]))
