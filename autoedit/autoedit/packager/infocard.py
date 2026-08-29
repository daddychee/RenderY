"""Render thẻ chữ nửa màn (info-card) ra video mp4 — Phase 2B Req 6.

Footage chạy nửa trái, thẻ này phủ nửa PHẢI: title đậm trên + 3-5 bullet fade-in tuần
tự (_ease) + footer disclaimer 'Minh hoạ'. Canvas 960x1080 (nửa khung, cao trọn).
matplotlib Agg -> H.264 yuv420p CFR 30fps (chuẩn CapCut 6.6). Tái dùng style charts.py.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from autoedit.packager.charts import ACCENT, FPS, THEMES, _ease
from autoedit.project import InfoCard

BG = THEMES["dark"]["BG"]
TEXT = THEMES["dark"]["TEXT"]
SUBTLE = THEMES["dark"]["SUBTLE"]

BULLET_STAGGER_SEC = 0.45        # cách nhau giữa các bullet fade-in
BULLET_GROW_SEC = 0.5            # thời gian fade 1 bullet

# Tone gradient nền (đáy) — chọn theo title cho đa dạng, hợp tone content
TONE_PALETTE = [
    "#7a5c00",  # vàng/gold (như ảnh mẫu)
    "#0a4f4f",  # teal
    "#5c1a1a",  # crimson
    "#2a1a5c",  # tím
    "#1a4d2e",  # xanh lá
    "#5c3a00",  # cam đất
]


def _pick_accent(card: InfoCard) -> str:
    """Màu tone: dùng card.accent nếu có, không thì chọn ổn định theo title (đa dạng)."""
    if card.accent:
        return card.accent
    h = sum(ord(c) for c in card.title) % len(TONE_PALETTE)
    return TONE_PALETTE[h]


def _draw_background(ax, accent: str) -> None:
    """Nền gradient (tối trên -> tone dưới) + lưới ô mờ — kiểu ảnh mẫu user."""
    import numpy as np
    from matplotlib.colors import to_rgb

    top, bot = to_rgb(BG), to_rgb(accent)
    h = 256
    grad = np.empty((h, 1, 3))
    for i in range(h):
        t = i / (h - 1)                 # 0 ở trên (origin upper) -> 1 ở dưới
        grad[i, 0] = [top[c] * (1 - t) + bot[c] * t for c in range(3)]
    ax.imshow(grad, extent=(0, 1, 0, 1), aspect="auto", origin="upper", zorder=0)
    for gx in [k / 12 for k in range(1, 12)]:
        ax.axvline(gx, color="#ffffff", alpha=0.10, lw=1, zorder=1)
    for gy in [k / 14 for k in range(1, 14)]:
        ax.axhline(gy, color="#ffffff", alpha=0.10, lw=1, zorder=1)


def render_info_card(card: InfoCard, duration_sec: float, out_path: Path) -> Path:
    """Render card -> mp4 960x1080 dài duration_sec. Nền gradient+lưới, tone theo content."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FFMpegWriter, FuncAnimation

    plt.rcParams["font.family"] = "DejaVu Sans"
    accent = _pick_accent(card)
    fig = plt.figure(figsize=(9.6, 10.8), dpi=100, facecolor=BG)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    _draw_background(ax, accent)

    # ----- title (wrap cho khỏi tràn 960px) -----
    title_lines = textwrap.wrap(card.title, 16) or [card.title]
    ax.text(0.5, 0.95, "\n".join(title_lines), ha="center", va="top", color="#ffffff",
            fontsize=46, fontweight="bold", zorder=5)

    # ----- bullets: layout CO GIÃN để 3-5 bullet (kể cả wrap 2 dòng) không tràn footer -----
    bullets = card.bullets[:5]
    wrapped = [textwrap.wrap(b, 24) or [b] for b in bullets]
    top = 0.92 - 0.085 * len(title_lines) - 0.04   # ngay dưới title
    bottom = 0.11                                    # chừa chỗ footer
    total_lines = sum(len(w) for w in wrapped)
    gap_units = 0.55 * len(bullets)                  # khoảng cách giữa các bullet (theo line_h)
    line_h = min(0.052, (top - bottom) / max(1, total_lines + gap_units))
    gap = line_h * 0.55
    fs = max(20, min(32, int(line_h * 1080 * 0.62)))  # font co theo line_h
    artists = []
    y = top
    for i, w in enumerate(wrapped):
        dot = ax.text(0.07, y, "●", ha="left", va="top", color=ACCENT[i % len(ACCENT)],
                      fontsize=fs * 0.9, zorder=5)
        txt = ax.text(0.14, y, "\n".join(w), ha="left", va="top", color=TEXT,
                      fontsize=fs, zorder=5, linespacing=1.1)
        artists.append((dot, txt, i))
        y -= line_h * len(w) + gap

    # ----- footer disclaimer (bắt buộc) -----
    if card.source_note:
        ax.text(0.5, 0.04, card.source_note, ha="center", va="bottom", color="#e0e0e8",
                fontsize=18, zorder=5)

    stagger = int(BULLET_STAGGER_SEC * FPS)
    grow = int(BULLET_GROW_SEC * FPS)
    total_frames = max(int(duration_sec * FPS), stagger * len(bullets) + grow + FPS)

    def update(f):
        for dot, txt, i in artists:
            start = i * stagger
            a = _ease(min(1.0, max(0.0, f - start) / grow)) if f >= start else 0.0
            dot.set_alpha(a)
            txt.set_alpha(a)
        return [a for tup in artists for a in tup[:2]]

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    writer = FFMpegWriter(
        fps=FPS, codec="libx264",
        extra_args=["-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "20"],
    )
    anim = FuncAnimation(fig, update, frames=total_frames, blit=False)
    anim.save(str(out_path), writer=writer)
    plt.close(fig)
    return out_path
