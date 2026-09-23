"""Bàn kịch bản — trang phục vụ ở `/` phải là trang THẬT, không phải bản mẫu.

Bản mẫu (scratchpad) mang dữ liệu giả nhúng thẳng trong JS để duyệt giao diện.
Nếu bản đó lọt lên máy chủ thì team gõ cả buổi rồi mất trắng khi đóng tab — nên
canh bằng test tĩnh: không còn mảng dữ liệu nhúng, và có gọi API thật.

Hai cơ chế đã đo tận tay ở bản mẫu, canh để không ai vô tình gỡ:
  - SỐ THỨ TỰ vẽ bằng CSS counter (`.en::before`), không nằm trong văn bản của
    trang. Đổi sang <span> là số lại dính vào bản copy đem đi ren voice — đúng
    nỗi khổ trên Google Sheet mà tool này sinh ra để chữa.
  - Dấu ✅❌🕐 đặt `user-select:none` vì cùng lý do.
"""

from __future__ import annotations

from pathlib import Path

import pytest

TRANG = (Path(__file__).resolve().parents[1]
         / "autoedit" / "treatment" / "static" / "treatment.html")


@pytest.fixture(scope="module")
def html() -> str:
    return TRANG.read_text(encoding="utf-8")


def test_khong_con_du_lieu_gia_nhung_trong_trang(html):
    for dau in ("var TAP = [", "var TAP=[", "Mossavar-Rahmani", "thanhdn đang sửa"):
        assert dau not in html, f"trang còn dữ liệu bản mẫu: {dau!r}"


def test_co_goi_api_that(html):
    for duong in ("/api/tap", "fetch("):
        assert duong in html, f"trang chưa gọi API: {duong!r}"


def test_co_giu_va_nha_khoa(html):
    """2-3 người làm cùng lúc: không giữ khoá thì hai người ghi đè nhau."""
    assert "/giu" in html and "/nha" in html


def test_co_tu_luu(html):
    assert "luuNgay" in html or "tuLuu" in html


def test_so_thu_tu_van_ve_bang_css_counter(html):
    assert "counter(dong)" in html
    assert "counter-increment:dong" in html.replace(" ", "")


def test_dau_hieu_khong_bi_boi_den(html):
    assert "user-select:none" in html.replace(" ", "")


def test_copy_lay_ban_txt_tu_may_chu(html):
    """Một luật một chỗ: bản copy phải là bản `/txt` do `dong.xuat()` sinh, không
    ghép lại bằng JS — hai đường ghép là hai kết quả lệch nhau."""
    assert "/txt" in html


# --------------------------- giai đoạn 2: citation ---------------------------
def test_co_nut_kiem_doan_boi_den(html):
    """Bôi đen đoạn -> nút nổi. Citation chạy THEO ĐOẠN người chọn (user chốt),
    không quét cả bài."""
    assert "Kiểm đoạn này" in html
    assert "selectionchange" in html


def test_co_goi_api_kiem_va_citation(html):
    assert "/kiem" in html and "/citation" in html


def test_danh_dau_dong_theo_the_citation(html):
    """Dòng nằm trong đoạn đã kiểm phải mang dấu ✅/❌ — nhìn là biết chương còn
    chỗ nào chưa kiểm."""
    for x in ("dau_citation", "✅", "❌", "🕐"):
        assert x in html, x


def test_hien_hang_nguon_va_bang_chung(html):
    """Thẻ phải nói rõ hạng nguồn và Python đã kiểm được gì — không chỉ ✅ suông."""
    assert "hang" in html and "link sống" in html


def test_khong_tro_vao_o_da_xoa(html):
    """Đo 16/09 trên Chrome: console nổ 6 lần `Cannot set properties of null` vì
    `vePhai()` còn trỏ vào #cDoan — ô đó đã bị thay khi dựng thẻ citation thật.
    Test xanh vẫn không thấy: lỗi này chỉ hiện khi mở trình duyệt."""
    import re as _re
    co = set(_re.findall(r'id="([\w-]+)"', html))
    goi = set(_re.findall(r'getElementById\("([\w-]+)"\)', html))
    assert goi <= co, f"trang gọi id không tồn tại: {sorted(goi - co)}"


def test_co_tab_cai_dat(html):
    """User chốt 16/09: tab cài đặt nằm TRONG app, chưa dính hệ production."""
    assert "Cài đặt" in html and "/api/cai-dat" in html
    assert "grok-4.6" in html and "gpt-5.6" in html, "gợi ý sẵn 2 model của nhà cung cấp"
    assert "api2.apisuper.cloud" in html
    assert "cai-dat/thu" in html, "phải có nút Thử — lỗi khoá không được lộ giữa chừng"


def test_co_o_khoa_serper(html):
    """Đứng riêng thì không đọc được két — khoá Serper phải đặt được tại chỗ."""
    assert "s-serper" in html and "Serper" in html


def test_nhan_hien_thi_la_Treatment(html):
    """User đổi tên tool 23/09: Factcheck -> Treatment. Nhãn trên trang phải đổi
    theo, không để tên cũ sót lại ở chỗ người dùng nhìn thấy."""
    assert "<title>Treatment" in html
    assert "· Treatment" in html
    assert "Factcheck" not in html and "factcheck" not in html
