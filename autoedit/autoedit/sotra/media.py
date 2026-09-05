r"""Frame JPEG cho clip nguồn LOCAL (ref/kho) — rút LAZY, cache vĩnh viễn.

Envato/Pexels/Pixabay hotlink url_anh thẳng trong <img> nên không qua đây;
chỉ ref/kho (file trên đĩa, trình duyệt không tự đọc được) cần endpoint ảnh.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from autoedit.sotra import db as sdb


def frame_clip(conn, clip_id: str, vai: str = "dau") -> Path | None:
    """Trả path JPEG frame đầu/cuối — rút bằng ffmpeg lần đầu, cache frames/."""
    if vai not in ("dau", "cuoi"):
        return None
    r = conn.execute("SELECT * FROM clip WHERE id=?", (clip_id,)).fetchone()
    if r is None:
        return None
    c = dict(r)
    da = c.get(f"frame_{vai}") or ""
    if da and Path(da).is_file():
        return Path(da)
    video = Path(c.get("path_local") or "")
    if not video.is_file():
        return None
    t0, t1 = float(c.get("t0") or 0), float(c.get("t1") or 0)
    if t1 <= t0:                      # kho: cả file
        t0, t1 = 0.0, float(c.get("dai_s") or 0)
    ts = (t0 + 0.3) if vai == "dau" else max(t0 + 0.5, (t1 or t0 + 1) - 0.5)
    dich = sdb.goc_so_tra() / "frames" / sdb.ten_frame(clip_id, c.get("tieu_de", ""), vai)
    r2 = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", f"{ts:.2f}", "-i", str(video),
         "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "6", str(dich)],
        capture_output=True, timeout=90)
    if r2.returncode != 0 or not dich.is_file():
        return None
    conn.execute(f"UPDATE clip SET frame_{vai}=? WHERE id=?", (str(dich), clip_id))
    conn.commit()
    return dich
