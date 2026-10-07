"""Nhịp chuyển động — mọi đường cong đều đo được, không đoán.

- `lo_xo`: bật–đậu kiểu pop-up (Rockefeller: bật ~0,3 s, đậu 1–1,5 s).
- `VOT_DAU`: easing kiểu Vox — đo demo createdaley: đỉnh tốc độ 0,08–0,17 s trong cú ~0,85 s.
"""

from __future__ import annotations

import math

import numpy as np


def lo_xo(zeta: float, t90: float):
    """Đáp ứng bước của lò xo tắt dần; omega chọn sao cho tới 90% đúng `t90` giây."""
    def x(t, w):
        if t <= 0:
            return 0.0
        wd = w * math.sqrt(1 - zeta ** 2)
        return 1 - math.exp(-zeta * w * t) * (math.cos(wd * t) + zeta * w / wd * math.sin(wd * t))

    lo, hi = 0.5, 300.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if x(t90, mid) < 0.9 else (lo, mid)
    return lambda t: x(t, lo)


def bezier(x1: float, y1: float, x2: float, y2: float):
    """Easing cubic-bezier như graph editor AE / CSS: (0,0)-(x1,y1)-(x2,y2)-(1,1)."""
    def f(u):
        u = min(max(u, 0.0), 1.0)
        lo, hi = 0.0, 1.0
        for _ in range(40):
            s = (lo + hi) / 2
            xs = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s ** 2 * x2 + s ** 3
            lo, hi = (s, hi) if xs < u else (lo, s)
        s = (lo + hi) / 2
        return 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s ** 2 * y2 + s ** 3
    return f


# bezier(0.35, 0, 0.05, 1) cho đỉnh 0,187 s — chậm hơn mẫu; (0.2, ...) cho 0,11 s
VOT_DAU = bezier(0.2, 0.0, 0.05, 1.0)


def dinh_toc_do(ease, n: int = 2000) -> float:
    """Vị trí (0..1) của đỉnh tốc độ trong một cú — để KIỂM easing khớp số đo."""
    v = np.diff([ease(i / n) for i in range(n + 1)])
    return float(np.argmax(v)) / n


def muot(u: float) -> float:
    """Đi đều hai đầu (cosine)."""
    return 0.5 - 0.5 * math.cos(math.pi * min(max(u, 0.0), 1.0))


def doan(t: float, a: float, b: float) -> float:
    return min(max((t - a) / (b - a), 0.0), 1.0)


def posterize(t: float, fps: float) -> float:
    """posterizeTime(fps) của AE: thời gian chặt thành bậc."""
    return math.floor(t * fps + 1e-9) / fps


def nhieu_muot(seed: int, tan_so: float, t: float, so_song: int = 4) -> float:
    """wiggle() của AE: tổng sóng sin pha ngẫu nhiên, biên độ ~[-1, 1]."""
    r = np.random.default_rng(seed)
    f = tan_so * r.uniform(0.5, 1.6, so_song)
    p = r.uniform(0, 2 * math.pi, so_song)
    return float(np.sum(np.sin(2 * math.pi * f * t + p)) / math.sqrt(so_song / 2))


def giu_theo_chu(so_ky_tu: int) -> float:
    """Thời gian camera đứng giữ ở một cụm chữ (Vox: nhiều chữ 2 s, ít chữ 1 s)."""
    return float(np.clip(0.7 + 0.035 * so_ky_tu, 1.0, 2.2))
