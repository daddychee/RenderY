"""Dựng text overlay cho draft CapCut — chuyển động bằng KEYFRAME thuần (an toàn).

Nguyên tắc P1 (CLAUDE.md): keyframe = toán trong JSON, không phụ thuộc gói cache
CapCut → không bao giờ bắt relink. Animation preset "đẹp" để Phase sau (sau derisk).

Vị trí dùng hệ chuẩn hóa CapCut: transform_y âm = xuống dưới (lower-third), dương = lên trên.
"""

from __future__ import annotations

from typing import Literal

from pycapcut import (
    ClipSettings,
    KeyframeProperty,
    TextBackground,
    TextBorder,
    TextIntro,
    TextSegment,
    TextStyle,
    Timerange,
)

Position = Literal["center", "lower_third", "upper"]
Anim = Literal["pop", "slide_up", "none", "typing"]

_POS_Y = {"center": 0.0, "lower_third": -0.62, "upper": 0.6}

SEC = 1_000_000           # micro giây CapCut
PER_CHAR_SEC = 0.06       # tốc độ gõ ~ mỗi ký tự (định thời lượng hiệu ứng + SFX)
TYPING_INTRO = TextIntro.打字机   # hiệu ứng gõ máy native CapCut (đã verify mở được)
# Trần (size × số ký tự) cho 1 dòng khỏi tràn khung 1920 — calib từ kinetic 10×21 vừa khung.
# Chữ dài tự co nhỏ; chữ ngắn ("$2","FREE") giữ nguyên size yêu cầu.
WIDTH_BUDGET = 200.0


def _fit_size(text: str, size: float) -> float:
    """Co cỡ chữ nếu dài quá khung (CapCut không auto-wrap/scale theo bề rộng)."""
    n = max(1, len(text))
    return min(size, WIDTH_BUDGET / n)


def build_text_overlay(
    text: str,
    start_us: int,
    duration_us: int,
    *,
    position: Position = "lower_third",
    anim: Anim = "pop",
    size: float = 15.0,
    color: tuple[float, float, float] = (1.0, 1.0, 1.0),
    y_override: float | None = None,
    x_override: float | None = None,
    bg_plate: bool = False,
    bordered: bool = True,
    alpha: float = 1.0,
) -> TextSegment:
    """1 text overlay có viền đen (dễ đọc trên mọi nền) + animation keyframe.
    y_override: ép vị trí dọc (Req 3 xếp chồng nhiều dòng); None = theo position.
    x_override: ép vị trí ngang (VD4 credit góc màn hình); None = giữa (hành vi cũ —
    transform_x pycapcut đã dùng cho card PiP, đây chỉ là expose cho text).
    bg_plate: nền chữ nhật mờ phía sau chữ cho nổi (Req 3 chữ chạy trên footage).
    bordered=False: chữ trơn không viền (VD4 credit — user chốt 2026-07-17).
    alpha <1: chữ mờ tĩnh — CHỈ dùng với anim="none" (pop/slide_up có keyframe
    alpha 0→1 riêng, sẽ đè mức tĩnh)."""
    ty = _POS_Y.get(position, 0.0) if y_override is None else y_override
    size = _fit_size(text, size)        # co nhỏ nếu chữ dài, khỏi tràn khung
    bg = (
        TextBackground(color="#000000", alpha=0.5, round_radius=0.12,
                       height=0.11, width=0.78)
        if bg_plate else None
    )
    seg = TextSegment(
        text,
        Timerange(start_us, duration_us),
        style=TextStyle(size=size, bold=True, color=color, align=1, alpha=alpha),
        border=(TextBorder(color=(0.0, 0.0, 0.0), width=60.0)  # outline cho dễ đọc
                if bordered else None),
        background=bg,
        clip_settings=ClipSettings(transform_x=x_override or 0.0, transform_y=ty),
    )
    _apply_anim(seg, anim, ty)
    return seg


def build_typing_overlay(
    text: str,
    start_us: int,
    duration_us: int,
    *,
    position: Position = "center",
    size: float = 18.0,
    color: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> tuple[TextSegment, int]:
    """GÕ MÁY bằng hiệu ứng NATIVE CapCut (TextIntro 打字机) — 1 segment + 1 animation,
    gọn và editor sửa được (đã verify CapCut tự resolve resource, không lỗi relink).
    Trả (segment, type_total_us) để assembler đặt SFX bàn phím trim đúng span gõ."""
    ty = _POS_Y.get(position, 0.0)
    n = max(1, len(text))
    size = _fit_size(text, size)        # co nhỏ nếu chữ dài, khỏi tràn khung
    # gõ xong trong ~70% duration để chữ đầy đủ đứng yên một lúc trước khi tắt
    type_total_us = max(1, min(int(n * PER_CHAR_SEC * SEC), int(duration_us * 0.7)))
    seg = TextSegment(
        text,
        Timerange(start_us, duration_us),
        style=TextStyle(size=size, bold=True, color=color, align=1),
        border=TextBorder(color=(0.0, 0.0, 0.0), width=60.0),
        clip_settings=ClipSettings(transform_y=ty),
    )
    seg.add_animation(TYPING_INTRO, type_total_us)   # hiệu ứng gõ máy native, dài = span gõ
    return seg, type_total_us


def _apply_anim(seg: TextSegment, anim: Anim, base_y: float) -> None:
    if anim == "pop":  # phình nhẹ rồi về 1.0 + fade-in (hợp số/giá đập vào mắt)
        seg.add_keyframe(KeyframeProperty.uniform_scale, "0s", 0.4)
        seg.add_keyframe(KeyframeProperty.uniform_scale, "0.15s", 1.12)
        seg.add_keyframe(KeyframeProperty.uniform_scale, "0.28s", 1.0)
        seg.add_keyframe(KeyframeProperty.alpha, "0s", 0.0)
        seg.add_keyframe(KeyframeProperty.alpha, "0.12s", 1.0)
    elif anim == "slide_up":  # trượt từ dưới lên + fade-in
        seg.add_keyframe(KeyframeProperty.position_y, "0s", base_y - 0.08)
        seg.add_keyframe(KeyframeProperty.position_y, "0.3s", base_y)
        seg.add_keyframe(KeyframeProperty.alpha, "0s", 0.0)
        seg.add_keyframe(KeyframeProperty.alpha, "0.2s", 1.0)
