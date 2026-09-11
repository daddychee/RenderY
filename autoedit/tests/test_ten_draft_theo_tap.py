r"""VIỆC 2 (11/09) — tên draft theo MÃ TẬP + CHƯƠNG, hết sinh bản mới.

User chốt 11/09: *"NAS đang khống chế cho nhân sự chỉ cop chứ không ghi đè, cho
nên mỗi lần xuất lại timeline của 1 chương là một lần tạo thêm bản mới, rất khó
kiểm soát."* → draft cũ **để lại dọn sau**, chỉ áp cho lần xuất mới.

ĐO THẬT 11/09 trước khi code:
* Tên hiện tại `OFF_<project_id>` (thay_mau.py) — project_id có dấu thời gian nên
  **phân tích lại chương = project mới = draft mới**. 9 chương đang bị:
  LI096_Hai H có 6 bản · LI103 C2 có 4 · LI105 H có 4 · LI103 C12 có 3.
  NAS: 33 draft / 10.6 GB, cỡ một nửa là bản trùng chương.
* 32 chương đang có draft trên NAS → đổi tên: **0 va chạm** (các bản trùng là
  project cũ KHÔNG có draft).
* `package_draft` chặn tên không ASCII: `^[A-Za-z0-9_\-]+$` (packager.py:28).
  Hai mã tập THẬT có dấu cách — `LI104 TOOL`, `LI093_Test tool` — nên
  `OFF_LI104 TOOL_C9` **raise PackageError**, Export chết. Chuẩn hoá là BẮT BUỘC.
* `thay_mau` gọi `package_draft(..., overwrite=True)` → xuất lại đè đúng chỗ cũ.

HAI CHỖ phải sửa CÙNG LÚC, nếu không cột "✓draft" báo sai âm thầm (BH5):
`offline/thay_mau.py` (nơi xuất) và `web/server.py:379` (nơi đi tìm).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoedit.duong_dan import ten_draft_chuong


# ───────────────────────── hàm suy tên: dùng chung MỘT chỗ ─────────────────────

def test_ten_co_ma_tap_va_nhan_chuong():
    assert ten_draft_chuong("LI106", "C2") == "OFF_LI106_C2"


def test_dau_cach_thanh_gach_duoi():
    """`package_draft` chặn khoảng trắng — không chuẩn hoá là Export CHẾT."""
    assert ten_draft_chuong("LI104 TOOL", "C9") == "OFF_LI104_TOOL_C9"
    assert ten_draft_chuong("LI093_Test tool", "H") == "OFF_LI093_Test_tool_H"


def test_ten_luon_qua_duoc_cua_ascii_cua_packager():
    from autoedit.packager.packager import _ASCII_NAME

    for tap, chuong in (("LI106", "C2"), ("LI104 TOOL", "C9"),
                        ("LI093_Test tool", "H"), ("LI104-TOOL", "E"),
                        ("Tập Việt", "C1"), ("", "")):
        ten = ten_draft_chuong(tap, chuong)
        assert _ASCII_NAME.match(ten), f"tên không qua cửa ASCII: {ten!r}"


def test_ky_tu_cam_cua_windows_bi_loai():
    for xau in ('<', '>', ':', '"', '/', chr(92), '|', '?', '*'):
        ten = ten_draft_chuong(f"LI1{xau}06", "C2")
        assert xau not in ten, f"còn ký tự cấm {xau!r} trong {ten!r}"


def test_khong_suy_duoc_thi_lui_ve_project_id():
    """Thiếu mã tập/nhãn chương thì phải có tên KHÁC RỖNG, không được ném lỗi."""
    ten = ten_draft_chuong("", "", lui="c2-20260908-112314")
    assert ten == "OFF_c2-20260908-112314"


def test_ten_on_dinh_giua_cac_lan_goi():
    """Cùng chương -> cùng tên -> xuất lại ĐÈ, không đẻ bản mới."""
    assert ten_draft_chuong("LI106", "C2") == ten_draft_chuong("LI106", "C2")


# ───────────────────── hai chỗ dùng phải khớp nhau ─────────────────────

def test_thay_mau_dung_ham_chung():
    s = Path("autoedit/offline/thay_mau.py").read_text(encoding="utf-8")
    assert "ten_draft_chuong" in s, "thay_mau chưa dùng hàm suy tên chung"
    assert 'ten = f"OFF_{project_dir.name}"' not in s, "vẫn còn tên cũ theo project_id"


def test_server_dung_ham_chung():
    """BH5: cột '✓draft' đi tìm phải khớp nơi xuất, không thì báo sai âm thầm."""
    s = Path("autoedit/web/server.py").read_text(encoding="utf-8")
    assert "ten_draft_chuong" in s, "server chưa dùng hàm suy tên chung"
    assert 'f"OFF_{d.name}"' not in s, "server vẫn đi tìm theo tên cũ"


def test_chi_mot_noi_dinh_nghia_tien_to_OFF():
    """Một khái niệm một hàm (BH4) — không rải `OFF_` khắp nơi.

    Quét file .py trong gói thay vì `git grep`: test phải chạy đúng ở CẢ dev lẫn
    production (cwd khác nhau, prod từng fail vì lý do đó chứ không phải vì mã).
    """
    goc = Path(__file__).resolve().parents[1] / "autoedit"
    bo_sot = []
    for f in goc.rglob("*.py"):
        if f.name == "duong_dan.py":          # nơi ĐỊNH NGHĨA duy nhất
            continue
        if 'OFF_{' in f.read_text(encoding="utf-8"):
            bo_sot.append(str(f.relative_to(goc)))
    assert not bo_sot, f"còn nơi tự ghép tên OFF_: {bo_sot}"


def test_dung_ma_tap_CHUAN_khong_lay_thu_muc_cha():
    r"""Do 11/09: `ma_tap_tu_script` lech `ma_tap_tu_duong_dan` 44/90 project.

    `ma_tap_tu_script` lay thu muc CHA cua `RenderY` -> ra `LI106_Hai` (con hau
    to) va `Tool` (khi duong dan la `...\LI102\Tool\RenderY\C1\C1.txt`). Lay
    nham thi hai chuong cung tap ra hai ten draft khac nhau - dung thu viec nay
    dang di chua.
    """
    from autoedit.sotra.db import ma_tap_tu_duong_dan

    for goc, mong in (
        (r"F:\OutlierY Nas 2\Life In\US\LI106_Hai\RenderY\C1.txt", "LI106"),
        (r"F:\OutlierY Nas 2\Life In\US\LI102\Tool\RenderY\C1\C1.txt", "LI102"),
        (r"F:\OutlierY Nas 2\Life In\US\LI104 TOOL\RenderY\C9\C9.txt", "LI104"),
    ):
        assert ma_tap_tu_duong_dan(goc) == mong, goc


def test_hai_chuong_cung_tap_ra_cung_tien_to():
    from autoedit.sotra.db import ma_tap_tu_duong_dan

    a = ten_draft_chuong(ma_tap_tu_duong_dan(r"F:\x\US\LI106_Hai\RenderY\C1.txt"), "C1")
    b = ten_draft_chuong(ma_tap_tu_duong_dan(r"F:\x\US\LI106_Hai\RenderY\C2.txt"), "C2")
    assert a == "OFF_LI106_C1" and b == "OFF_LI106_C2"

def test_hai_noi_khop_nhau_CA_KHI_thieu_nhan_chuong():
    """BH5 ca biên — bắt được 11/09 khi đối chiếu: `server` dùng
    `nhan or d.name` cho NHÃN HIỂN THỊ; nếu lấy luôn nhãn đó đặt tên draft thì
    thiếu nhãn -> server tìm `OFF_LI106_c9-2026...` còn thay_mau xuất
    `OFF_c9-2026...` -> cột "✓draft" báo sai âm thầm."""
    from autoedit.duong_dan import ten_draft_chuong as t

    assert t("LI106", "", lui="c9-x") == t("LI106", "", lui="c9-x")
    assert t("LI106", "", lui="c9-x") == "OFF_c9-x", "thiếu nhãn -> phải lùi hẳn"


def test_server_khong_dat_ten_bang_nhan_hien_thi():
    from pathlib import Path

    s = Path("autoedit/web/server.py").read_text(encoding="utf-8")
    assert "_tdc(_mtd(goc), nhan," not in s, (
        "đặt tên draft bằng `nhan` (đã `or d.name`) là lệch với thay_mau")
