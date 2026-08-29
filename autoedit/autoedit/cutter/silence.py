"""Silence detection — chống cắt cụt từ (RA_SOAT 3.1).

Ranh giới beat từ alignment lệch ±50ms là thường; cắt thẳng có thể phạm vào phụ âm
cuối. Giải pháp: dò các khoảng lặng của master WAV một lần (ffmpeg silencedetect),
rồi snap mỗi ranh giới CẮT vào điểm giữa khoảng lặng gần nhất trong cửa sổ ±200ms.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

NOISE_DB = "-35dB"
MIN_SILENCE_SEC = 0.15
SNAP_WINDOW_SEC = 0.2

_RE_START = re.compile(r"silence_start:\s*([0-9.]+)")
_RE_END = re.compile(r"silence_end:\s*([0-9.]+)")


def parse_silencedetect(stderr: str) -> list[tuple[float, float]]:
    """Parse stderr của ffmpeg silencedetect thành list (start, end)."""
    starts = [float(m) for m in _RE_START.findall(stderr)]
    ends = [float(m) for m in _RE_END.findall(stderr)]
    # file kết thúc trong im lặng -> silence_start cuối không có end: bỏ qua cặp lẻ
    return list(zip(starts, ends))


def detect_silences(
    wav: Path, noise: str = NOISE_DB, min_sec: float = MIN_SILENCE_SEC
) -> list[tuple[float, float]]:
    result = subprocess.run(
        ["ffmpeg", "-i", str(wav), "-af", f"silencedetect=noise={noise}:d={min_sec}",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=300,
    )
    # silencedetect ghi ra stderr kể cả khi thành công
    return parse_silencedetect(result.stderr)


def snap_to_silence(
    t: float, silences: list[tuple[float, float]], window: float = SNAP_WINDOW_SEC
) -> tuple[float, bool]:
    """Snap ranh giới t vào ĐIỂM GIỮA khoảng lặng gần nhất giao với [t-window, t+window].

    Trả (t', snapped). Không có khoảng lặng nào trong cửa sổ -> giữ nguyên (t, False).
    """
    best: tuple[float, float] | None = None  # (khoảng cách tới KHOẢNG lặng, điểm snap)
    for s, e in silences:
        if e < t - window or s > t + window:
            continue
        # chọn theo khoảng cách tới khoảng lặng (0 nếu t nằm trong) — KHÔNG theo điểm
        # giữa, kẻo ranh giới bị kéo lùi về khoảng lặng trước đó và cắt phạm vào từ
        dist = max(0.0, s - t, t - e)
        mid = (s + e) / 2
        # điểm snap: giữa khoảng lặng, kẹp vào trong cửa sổ để không trôi xa
        point = min(max(mid, t - window), t + window)
        if best is None or dist < best[0]:
            best = (dist, point)
    if best is None:
        return t, False
    return best[1], True
