r"""Frame JPEG cho clip nguồn LOCAL (ref/kho) — rút LAZY, cache vĩnh viễn.

Envato/Pexels/Pixabay hotlink url_anh thẳng trong <img> nên không qua đây;
chỉ ref/kho (file trên đĩa, trình duyệt không tự đọc được) cần endpoint ảnh.
"""

from __future__ import annotations

import os
import re
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


def khuc_clip(conn, clip_id: str) -> Path | None:
    """KHÚC preview nhỏ cho clip local có tọa độ — cắt 1 lần, cache vĩnh viễn.

    Vì sao (đo 06/09): shot ref bắt trình duyệt mở FILE GỐC 1GB 1080p trên NAS
    qua 2 tầng proxy — dò moov, Range seek, decode từ keyframe cách 4-7s → preview
    đơ. Envato mượt vì preview chỉ ~4MB. Khúc cắt sẵn 960px đưa ref về cùng
    hạng cân: ~0.5-1MB/khúc, lần đầu tốn ~2s ffmpeg rồi cache mãi.

    KHÔNG vi phạm luật "không cắt file": đây là CACHE PREVIEW (xóa được, dựng
    lại được), sổ vẫn chỉ ghi tọa độ; draft/thay máu vẫn cắt từ file gốc.
    """
    r = conn.execute("SELECT * FROM clip WHERE id=?", (clip_id,)).fetchone()
    if r is None:
        return None
    c = dict(r)
    video = Path(c.get("path_local") or "")
    t0, t1 = float(c.get("t0") or 0), float(c.get("t1") or 0)
    if not video.is_file() or t1 <= t0:
        return None
    dich = sdb.goc_so_tra() / "prev_cache" / (
        re.sub(r"[^\w-]", "_", clip_id) + ".mp4")
    if dich.is_file() and dich.stat().st_size > 0:
        return dich
    dich.parent.mkdir(parents=True, exist_ok=True)
    # Cắt ra FILE TẠM rồi mới đổi tên (user báo 08/09: 22/42 miếng preview đen).
    # Bản cũ ghi thẳng vào file cache và lần sau chỉ kiểm `size > 0` là tin.
    # ffmpeg bị giết giữa chừng — restart máy chủ, timeout, hết đĩa — để lại
    # file DỞ nhưng khác rỗng, thế là cache tin nó MÃI MÃI. Đo thật: 27/305
    # khúc trong kho hỏng (`Invalid NAL unit`), toàn bộ là ref của LI089, nhiều
    # cái đúng phút máy chủ bị dừng. Đổi tên là thao tác nguyên tử: chết giữa
    # chừng thì chỉ còn file .tmp, không ai nhầm nó là khúc thật.
    tam = dich.with_suffix(".tmp.mp4")
    tam.unlink(missing_ok=True)
    r2 = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}",
         "-i", str(video), "-vf", "scale=960:-2", "-c:v", "libx264",
         "-preset", "veryfast", "-crf", "26", "-c:a", "aac", "-b:a", "96k",
         "-movflags", "+faststart", "-y", str(tam)],
        capture_output=True, timeout=180)
    if r2.returncode != 0 or not doc_duoc(tam):
        tam.unlink(missing_ok=True)
        return None
    os.replace(tam, dich)
    return dich


def doc_duoc(f: Path) -> bool:
    """File video này có ĐỌC ĐƯỢC không? Rào duy nhất chặn khúc dở vào cache.

    Chỉ hỏi `format=duration` (rẻ, không giải mã cả file). File dở thì ffprobe
    trả mã lỗi hoặc kêu ra stderr — cả hai đều coi là hỏng.
    """
    if not f.is_file() or f.stat().st_size == 0:
        return False
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(f)],
            capture_output=True, text=True, timeout=30)
    except Exception:  # noqa: BLE001 — không probe được thì coi như hỏng
        return False
    return r.returncode == 0 and bool(r.stdout.strip()) and not r.stderr.strip()


def don_khuc_hong(xoa: bool = False) -> int:
    """Dọn khúc preview ĐÃ LỠ cache lúc còn hỏng. Trả số khúc hỏng.

    Bản vá ghi-tạm-rồi-đổi-tên chỉ chặn khúc hỏng MỚI; khúc đã nằm trong cache
    từ trước vẫn đen mãi cho tới khi bị xoá. `xoa=False` = chỉ đếm.
    """
    cache = sdb.goc_so_tra() / "prev_cache"
    if not cache.is_dir():
        return 0
    hong = [f for f in sorted(cache.glob("*.mp4")) if not doc_duoc(f)]
    if xoa:
        for f in hong:
            f.unlink(missing_ok=True)
    return len(hong)
