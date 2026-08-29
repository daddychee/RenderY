"""Render biểu đồ động ra video mp4 — Phase 1 Nhóm B (P1.5).

matplotlib animation (Agg headless) → mp4 H.264 yuv420p CFR 30fps (chuẩn CapCut 6.6).
Nền tối + lưới ô; bar mọc 0→value, line vẽ trái→phải, rồi giữ frame cuối hết beat.
"""

from __future__ import annotations

from pathlib import Path

from autoedit.project import GraphicSpec

FPS = 30
GROW_SEC = 1.2                    # thời gian cột mọc / đường vẽ
ACCENT = ["#4ea8de", "#f4a259", "#80ed99", "#e76f51", "#c77dff", "#ffd166"]
# Hai theme: dark (mặc định, giữ look Phase 1) + light (cho đa dạng — Req 5)
THEMES = {
    "dark": dict(BG="#0d0d12", GRID="#2a2a35", TEXT="#f0f0f5", SUBTLE="#9a9aab"),
    "light": dict(BG="#f7f7fb", GRID="#d8d8e0", TEXT="#1a1a22", SUBTLE="#5a5a6a"),
}
# alias dark cho code/test cũ tham chiếu trực tiếp
BG = THEMES["dark"]["BG"]
GRID = THEMES["dark"]["GRID"]
TEXT = THEMES["dark"]["TEXT"]
SUBTLE = THEMES["dark"]["SUBTLE"]

# SFX theo loại chart (Req 2) — kind trong thư viện ~/AutoEdit/sfx
_CHART_SFX = {"bar": "chart_bar", "line": "chart_line", "pie": "chart_pie"}
CHART_SETTLE_SFX = "ding"        # tiếng chốt khi chart mọc xong


def _ease(t: float) -> float:
    """Ease-out cubic — mọc nhanh đầu, chậm cuối (mượt hơn tuyến tính)."""
    return 1 - (1 - t) ** 3


def _thin_xticks(ax, n: int, max_labels: int = 8) -> None:
    """>max_labels điểm: chỉ hiện nhãn mỗi k-th (giữ tick còn lại trống) cho khỏi chồng."""
    if n <= max_labels:
        return
    step = (n + max_labels - 1) // max_labels  # làm tròn lên
    for i, lbl in enumerate(ax.get_xticklabels()):
        if i % step != 0:
            lbl.set_visible(False)


def render_chart(spec: GraphicSpec, duration_sec: float, out_path: Path) -> Path:
    """Render spec → mp4 dài duration_sec. Trả về out_path."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FFMpegWriter, FuncAnimation

    plt.rcParams["font.family"] = "DejaVu Sans"  # hỗ trợ dấu tiếng Việt
    # rebind theme cục bộ — shadow hằng module để cả 3 nhánh + closure dùng đúng màu
    _t = THEMES.get(spec.theme, THEMES["dark"])
    BG, GRID, TEXT, SUBTLE = _t["BG"], _t["GRID"], _t["TEXT"], _t["SUBTLE"]
    is_half = spec.layout == "half"
    # CẢ HAI render 1920x1080 (cùng tỉ lệ canvas -> CapCut scale đoán được).
    # half sẽ bị PiP scale ~0.5 -> font render to ~1.7x cho dễ đọc khi thu nhỏ.
    figsize = (19.2, 10.8)
    fs_title = 56 if is_half else 34
    fs_label = 42 if is_half else 26
    fs_value = 50 if is_half else 30

    labels = [d.label for d in spec.data]
    values = [d.value for d in spec.data]
    vmax = max(values) if values else 1.0

    fig = plt.figure(figsize=figsize, dpi=100, facecolor=BG)
    ax = fig.add_subplot(111, facecolor=BG)
    ax.set_title(spec.title, color=TEXT, fontsize=fs_title, fontweight="bold", pad=24)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=SUBTLE, labelsize=fs_label, length=0)
    ax.set_ylim(0, vmax * 1.18)
    ax.grid(axis="y", color=GRID, linewidth=1)
    ax.set_axisbelow(True)

    grow_frames = int(GROW_SEC * FPS)
    total_frames = max(grow_frames + FPS, int(duration_sec * FPS))

    def fmt(v: float) -> str:
        s = f"{v:,.0f}" if v == int(v) else f"{v:,.2f}"
        return f"{spec.unit}{s}" if spec.unit and spec.unit not in ("%",) else f"{s}{spec.unit}"

    if spec.chart_type == "pie":
        # DONUT: lỗ giữa; slice quét theo kim đồng hồ từ 12h. Lỗ giữa hiện %
        # phần lớn nhất (vd "50%"). Tắt trục/lưới — donut không cần.
        ax.set_ylim(-1.25, 1.25)
        ax.set_xlim(-1.6, 1.6)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.grid(False)
        total = sum(values) or 1.0
        fracs = [v / total for v in values]  # tỉ trọng từng phần
        big = max(range(len(values)), key=lambda i: values[i])
        center_txt = ax.text(0, 0, "", ha="center", va="center", color=TEXT,
                             fontsize=fs_value * 1.4, fontweight="bold")
        # legend tên phần + giá trị, xếp dưới
        leg_txts = [
            ax.text(0, 0, "", ha="left", va="center", color=TEXT, fontsize=fs_label)
            for _ in values
        ]

        def update(f):
            prog = _ease(min(1.0, f / grow_frames))
            for w in list(ax.patches):
                w.remove()
            from matplotlib.patches import Wedge
            ang = 90.0  # bắt đầu 12h
            for i, fr in enumerate(fracs):
                sweep = fr * 360.0 * prog
                ax.add_patch(Wedge((0, 0), 1.0, ang - sweep, ang, width=0.42,
                                   facecolor=ACCENT[i % len(ACCENT)], edgecolor=BG, linewidth=3))
                ang -= fr * 360.0  # mép tiếp theo theo tỉ trọng đầy đủ (vị trí cố định)
            center_txt.set_text(f"{fracs[big] * 100 * prog:.0f}%")
            # legend: ô màu giả bằng ký tự ● + nhãn
            n = len(values)
            for i, lt in enumerate(leg_txts):
                y = -1.05 - i * 0.14
                lt.set_position((-0.55, y))
                lt.set_color(ACCENT[i % len(ACCENT)])
                share = "" if spec.unit == "%" else f" ({fracs[i] * 100:.0f}%)"
                lt.set_text(f"●  {labels[i]}: {fmt(values[i])}{share}")
            return [center_txt, *leg_txts, *ax.patches]
    elif spec.chart_type == "line":
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels)
        _thin_xticks(ax, len(labels))            # >8 điểm: thưa nhãn kẻo chồng
        (line,) = ax.plot([], [], color=ACCENT[0], linewidth=4, marker="o", markersize=10)
        # nhãn giá trị cuối: căn phải để mọc SANG TRÁI, không cắt mép khi điểm cuối ở rìa
        end_txt = ax.text(0, 0, "", color=TEXT, fontsize=fs_value, fontweight="bold",
                          ha="right", va="bottom")

        def update(f):
            prog = _ease(min(1.0, f / grow_frames))
            n = max(1, int(round(prog * len(values))))
            line.set_data(range(n), values[:n])
            if n >= 1:
                end_txt.set_position((n - 1 - 0.08, values[n - 1] + vmax * 0.04))
                end_txt.set_text(fmt(values[n - 1]))
            return line, end_txt
    else:  # bar
        x = range(len(labels))
        bars = ax.bar(x, [0] * len(values), color=ACCENT[: len(values)], width=0.6)
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels)
        vtexts = [ax.text(i, 0, "", ha="center", color=TEXT, fontsize=fs_value,
                          fontweight="bold") for i in x]

        def update(f):
            prog = _ease(min(1.0, f / grow_frames))
            for i, (bar, vt) in enumerate(zip(bars, vtexts)):
                h = values[i] * prog
                bar.set_height(h)
                vt.set_position((i, h + vmax * 0.03))
                vt.set_text(fmt(h))
            return [*bars, *vtexts]

    # nhãn trục (Req 5) — chỉ line/bar có trục mang nghĩa; pie đã tắt trục
    if spec.chart_type in ("line", "bar"):
        if spec.x_label:
            ax.set_xlabel(spec.x_label, color=TEXT, fontsize=fs_label, labelpad=12)
        if spec.y_label:
            ax.set_ylabel(spec.y_label, color=TEXT, fontsize=fs_label, labelpad=12)

    if spec.source_note:
        fig.text(0.5, 0.02, spec.source_note, ha="center", color=SUBTLE, fontsize=14)
    fig.tight_layout(rect=(0, 0.04, 1, 1))

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
