"""Chuẩn hóa footage trước khi vào draft (bài học CapCut 6.6).

Stock đa nguồn lung tung VFR/HEVC/10-bit làm CapCut lag/lỗi -> mọi video về
H.264 yuv420p CFR 30fps. Ảnh giữ nguyên. Skip nếu đã transcode (mtime mới hơn).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from autoedit.project import ffprobe_duration

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm"}

# V1 (2026-07-09, MO_TA_VAN_HANH_NANG_CAP_V123): khung hình chuẩn 16:9 — clip lệch quá
# ngưỡng bị CẮT TÂM về 16:9 ngay lúc normalize (đo SP012: 44/442 asset lệch -> viền đen).
AR_TARGET = 16 / 9
AR_TOLERANCE = 0.03  # lệch tương đối cho phép (viral 852x478=1.782 giữ nguyên; 1.896 thì cắt)


def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTS


def ffprobe_dims(path: Path) -> "tuple[int, int] | None":
    """(width, height) stream hình đầu tiên qua ffprobe. None nếu lỗi (fail-open)."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        w, h = out.stdout.strip().splitlines()[0].split("x")[:2]
        w, h = int(w), int(h)
        return (w, h) if w > 0 and h > 0 else None
    except Exception:
        return None


def crop_16x9_vf(width: int, height: int) -> "str | None":
    """Chuỗi filter `crop=w:h` cắt TÂM về 16:9, hoặc None nếu trong ngưỡng ±3%.
    Cắt thẳng MỌI mức lệch kể cả 2.9:1 (user duyệt V1 — viền đen tệ hơn phần hình mất).
    Kích thước ra luôn CHẴN (yuv420p bắt buộc)."""
    ar = width / height
    if abs(ar / AR_TARGET - 1) <= AR_TOLERANCE:
        return None
    if ar > AR_TARGET:  # rộng hơn (2:1, 2.4:1...) -> cắt 2 bên
        new_w = min(round(height * AR_TARGET / 2) * 2, width - width % 2)
        return f"crop={new_w}:{height - height % 2}"
    new_h = min(round(width / AR_TARGET / 2) * 2, height - height % 2)  # hẹp hơn -> cắt trên dưới
    return f"crop={width - width % 2}:{new_h}"


def cover_scale(width: int, height: int) -> float:
    """Hệ số uniform_scale để hình PHỦ kín khung 16:9 (V1 nhánh ẢNH — ảnh không cắt
    file, phủ bằng scale; ảnh 16:9 -> 1.0 = hành vi cũ)."""
    ar = width / height
    return round(max(ar / AR_TARGET, AR_TARGET / ar), 4)


def normalize_audio(src: Path, dst: Path) -> Path:
    """Audio nén (mp3...) -> WAV PCM 48kHz. MP3 VBR có duration header ước lượng,
    CapCut đo lại lệch vài chục ms so với sổ đăng ký -> bắt relink (bài học 12/06).
    WAV thì mọi cách đo đều ra cùng một số."""
    if dst.is_file() and dst.stat().st_mtime >= src.stat().st_mtime:
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src),
         "-ar", "48000", "-c:a", "pcm_s16le", str(dst)],
        capture_output=True, text=True, timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Normalize audio {src.name} thất bại: {result.stderr[-300:]}")
    return dst


def normalize_image(src: Path, dst: Path) -> Path:
    """Ảnh -> JPEG baseline, BỎ EXIF (orientation EXIF làm CapCut đọc kích thước
    khác sổ đăng ký -> bắt relink). -map_metadata -1 xóa sạch metadata."""
    if dst.is_file() and dst.stat().st_mtime >= src.stat().st_mtime:
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src),
         "-map_metadata", "-1", "-q:v", "2", str(dst)],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Normalize ảnh {src.name} thất bại: {result.stderr[-300:]}")
    return dst


def has_audio_stream(path: Path) -> bool:
    """File có stream audio thật không — CapCut khó chịu khi material khai sai."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=codec_type", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=30,
    )
    return result.returncode == 0 and "audio" in result.stdout


def normalize_video(src: Path, dst: Path, crop_16x9: bool = True) -> Path:
    """Transcode H.264 yuv420p CFR 30fps + faststart + CẮT TÂM về 16:9 nếu lệch >3%
    (V1). Idempotent theo mtime — project cũ muốn ăn crop phải xóa folder norm.
    crop_16x9=False cho asset TỰ RENDER có tỉ lệ chủ đích (chart PiP, info-card dọc)."""
    if dst.is_file() and dst.stat().st_mtime >= src.stat().st_mtime:
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    dims = ffprobe_dims(src) if crop_16x9 else None
    vf = crop_16x9_vf(*dims) if dims else None  # probe lỗi -> không crop (fail-open)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src)]
    if vf:
        cmd += ["-vf", vf]
    result = subprocess.run(
        cmd + ["-c:v", "libx264", "-preset", "fast", "-crf", "20",
               "-pix_fmt", "yuv420p", "-r", "30", "-vsync", "cfr",
               "-c:a", "aac", "-b:a", "192k",
               "-movflags", "+faststart", str(dst)],
        capture_output=True, text=True, timeout=1800,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Transcode {src.name} thất bại: {result.stderr[-300:]}")
    if ffprobe_duration(dst) is None:
        raise RuntimeError(f"Transcode {src.name}: file ra không đọc được")
    return dst
