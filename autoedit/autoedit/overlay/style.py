"""Map kind overlay -> phần HÌNH (vị trí, animation, SFX, cỡ chữ).

Nguyên tắc xuyên dự án: LLM quyết NGHĨA, code quyết MECHANIC. LLM chỉ phân loại
overlay thành kind; bảng dưới đây đảm bảo mỗi loại có treatment nhất quán, đẹp.
"""

from __future__ import annotations

from autoedit.project import Overlay

# kind -> (position, anim, sfx_kind, size)
_KIND_STYLE: dict[str, dict] = {
    # giá/số tiền: pop dưới màn hình + tiếng cash ("$2 breakfast")
    "price": dict(position="lower_third", anim="pop", sfx_kind="cash", size=18.0),
    # từ khóa nhấn: chữ to giữa màn + impact ("FREE", "ILLEGAL")
    "keyword": dict(position="center", anim="pop", sfx_kind="impact", size=24.0),
    # số liệu lẻ + nhãn: trượt lên dưới màn ("45 ngày miễn visa")
    "stat": dict(position="lower_third", anim="slide_up", sfx_kind="pop", size=16.0),
    # mục danh sách/bước: trượt lên, nhẹ ("Bước 1")
    "list_item": dict(position="lower_third", anim="slide_up", sfx_kind="pop", size=15.0),
    # Phase 2A Req 1 — GÕ MÁY + tiếng bàn phím:
    # tên người/tổ chức: gõ máy giữa màn
    "name": dict(position="center", anim="typing", sfx_kind="keyboard", size=22.0),
    # tên địa danh: gõ máy dưới màn (lower-third như phụ đề địa danh)
    "place": dict(position="lower_third", anim="typing", sfx_kind="keyboard", size=18.0),
    # trích dẫn ngắn: gõ máy giữa màn
    "quote": dict(position="center", anim="typing", sfx_kind="keyboard", size=20.0),
}
DEFAULT = _KIND_STYLE["stat"]

VALID_KINDS = tuple(_KIND_STYLE)


def resolve_overlay(text: str, kind: str, anchor_word: int, duration_sec: float = 2.0) -> Overlay:
    """Dựng Overlay đầy đủ: NGHĨA từ LLM + HÌNH suy từ kind."""
    style = _KIND_STYLE.get(kind, DEFAULT)
    return Overlay(
        text=text,
        kind=kind,
        anchor_word=anchor_word,
        duration_sec=duration_sec,
        position=style["position"],
        anim=style["anim"],
        sfx_kind=style["sfx_kind"],
        size=style["size"],
    )
