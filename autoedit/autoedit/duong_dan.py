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


def ten_draft_chuong(ma_tap: str, nhan_chuong: str, lui: str = "") -> str:
    r"""Tên thư mục draft của MỘT chương — `OFF_<tập>_<chương>` (việc 2, 11/09).

    Vì sao đổi (user 11/09): tên cũ `OFF_<project_id>` mang dấu thời gian, nên
    **phân tích lại một chương = project mới = draft mới**. Đo trên NAS 11/09:
    33 draft / 10.6 GB, 9 chương có bản trùng (LI096_Hai H sáu bản, LI103 C2 bốn
    bản). NAS chỉ cho copy nên nhân sự không dọn được, rất khó kiểm soát.
    Tên theo chương thì xuất lại ĐÈ đúng chỗ cũ (`package_draft(overwrite=True)`).

    Chuẩn hoá là BẮT BUỘC, không phải làm đẹp: `package_draft` chặn tên không
    khớp `^[A-Za-z0-9_-]+$` (packager.py:28), mà mã tập THẬT có dấu cách —
    `LI104 TOOL`, `LI093_Test tool` — nên không gom lại là Export **chết**.
    Ký tự cấm của Windows (`<>:"/\|?*`) cũng rơi vào cùng luật này.

    `lui`: khi không suy được tập/chương (đường dẫn lạ) thì lấy project_id —
    đúng hành vi cũ, không ném lỗi giữa lúc người dựng bấm Export.
    """
    import re

    def _gon(x: str) -> str:
        # mọi thứ ngoài [A-Za-z0-9_-] thành '_', rồi gộp '_' liền nhau
        return re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9_-]", "_", str(x or ""))).strip("_")

    tap, chuong = _gon(ma_tap), _gon(nhan_chuong)
    if tap and chuong:
        return f"OFF_{tap}_{chuong}"
    return f"OFF_{_gon(lui) or 'khong_ten'}"
