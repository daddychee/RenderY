r"""Suy TẬP và CHƯƠNG từ đường dẫn kịch bản — MỘT nơi duy nhất.

Bố cục thư mục con : `...\US\LI103\Rendery\H\H.txt`
Bố cục PHẲNG       : `...\US\LI089\RenderY\H.txt`

Mốc neo là thư mục `RenderY`: tập luôn là CHA của nó, chương thì nằm ngay dưới
(thư mục con) hoặc chính là TÊN FILE (phẳng).

Vì sao gom về đây: cùng một gốc "đếm lùi N cấp thư mục" đã nổ **ba lần** trong
hai ngày —
  08/09  16 chương gộp thành MỘT project (`_project_cu_dung_duoc` khớp theo cha)
  08/09  tab Offline hiện `US / RENDERY` thay vì `LI089`
  09/09  tra nhầm người nộp -> tập của Hải nhận Hiếu làm chủ
Mỗi lần lại một chỗ đếm cấp riêng. Nay ai cần thì gọi hàm ở đây.
"""

from __future__ import annotations

from pathlib import Path

TEN_THU_MUC_CHUONG = "rendery"     # thư mục chứa các chương, ngay dưới thư mục TẬP


def _phan(goc: str) -> list[str]:
    return [x for x in Path(str(goc).replace("\\", "/")).parts if x not in ("/", "")]


def thu_muc_tap_tu_script(goc: str) -> str:
    """Tên thư mục TẬP (LI106_Hai). Rỗng nếu không neo được."""
    if not goc:
        return ""
    phan = _phan(goc)
    for i, x in enumerate(phan):
        if x.lower() == TEN_THU_MUC_CHUONG and i >= 1:
            return phan[i - 1]
    return ""


def ma_tap_tu_script(goc: str) -> str:
    """Mã tập để gom nhóm trên UI — cắt 18 ký tự, có lối lùi cho đường dẫn lạ."""
    ten = thu_muc_tap_tu_script(goc)
    if ten:
        return ten[:18]
    phan = _phan(goc)
    return (phan[-3][:18] if len(phan) >= 3 else (phan[0] if phan else ""))


def nhan_chuong_tu_script(goc: str) -> str:
    """Nhãn chương (H, C12) — thư mục con lấy TÊN THƯ MỤC, phẳng lấy TÊN FILE."""
    if not goc:
        return ""
    p = Path(str(goc).replace("\\", "/"))
    return (p.stem.upper() if p.parent.name.lower() == TEN_THU_MUC_CHUONG
            else p.parent.name.upper())
