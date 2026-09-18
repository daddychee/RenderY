r"""Luật TÊN CHƯƠNG H / C<số> / E — bản độc lập của Factcheck.

Trước khi đóng gói, chỗ này `import autoedit.web.chapters`. Nay Factcheck đứng
riêng nên chép về — 15 dòng regex, rẻ hơn nhiều so với buộc cả tool vào dây
chuyền dựng chỉ vì một hàm.

Chép là đẻ ra nguy cơ hai luật lệch nhau, nên có test đối chiếu
(`tests/test_kho.py::test_luat_ten_chuong_khop_voi_ban_goc`): khi nào máy còn
thấy `autoedit.web.chapters` thì nó so từng tên một; không thấy thì bỏ qua.

Thứ tự là H -> C1..Cn -> E. Sắp theo TÊN là sai cả hai đầu ("E" trước "H",
"C10" trước "C2") — dựng nhầm thứ tự chương thì phải dựng lại cả tập.
"""

from __future__ import annotations

import re

_HOOK = re.compile(r"^H$", re.IGNORECASE)
_CHAP = re.compile(r"^C(\d+)$", re.IGNORECASE)
_END = re.compile(r"^E$", re.IGNORECASE)


def phan_tich_ten(ten: str) -> tuple[str, int, str] | None:
    """Tên -> (mã chuẩn, thứ tự, nhãn đọc được). None nếu sai quy ước."""
    t = (ten or "").strip()
    if _HOOK.match(t):
        return "H", 0, "Hook"
    if _END.match(t):
        return "E", 999_999, "Kết"
    m = _CHAP.match(t)
    if m:
        so = int(m.group(1))
        # C0 vô nghĩa (Hook đã là mở đầu) — coi như sai quy ước, báo người sửa
        if so >= 1:
            return f"C{so}", so, f"Chương {so}"
    return None
