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
def test_khong_tro_vao_o_da_xoa(html):
    """Đo 16/09 trên Chrome: console nổ 6 lần `Cannot set properties of null` vì
    `vePhai()` còn trỏ vào #cDoan — ô đó đã bị thay khi dựng thẻ citation thật.
    Test xanh vẫn không thấy: lỗi này chỉ hiện khi mở trình duyệt."""
    import re as _re
    co = set(_re.findall(r'id="([\w-]+)"', html))
    goi = set(_re.findall(r'getElementById\("([\w-]+)"\)', html))
    assert goi <= co, f"trang gọi id không tồn tại: {sorted(goi - co)}"
def test_nhan_hien_thi_la_Treatment(html):
    """User đổi tên tool 23/09: Factcheck -> Treatment. Nhãn trên trang phải đổi
    theo, không để tên cũ sót lại ở chỗ người dùng nhìn thấy."""
    assert "<title>Treatment" in html
    assert "· Treatment" in html
    assert "Factcheck" not in html and "factcheck" not in html


# ------------------- sửa 23/09 theo yêu cầu user ----------------------------
def test_o_nguon_tu_dien_giong_treatment(html):
    """User chốt 23/09: "không cần dùng LLM để tìm Citation nữa, team sẽ tự tìm"
    và "Citation giống cơ chế của treatment, có ô để điền thông tin"."""
    assert "ctOo" in html, "phải có ô nhập nguồn cho từng dòng"
    assert "/kiem" not in html, "bỏ hẳn đường kiểm chứng tự động"
    assert "Kiểm đoạn này" not in html


def test_khong_con_o_khoa_LLM_cho_citation(html):
    """Bỏ phần cài khoá phục vụ tra nguồn tự động."""
    assert "s-serper" not in html and "Serper" not in html


def test_co_gom_cum_va_bang_mau(html):
    """Gom câu thành cụm + tô màu (user chốt 23/09)."""
    assert "gomCum" in html and "boCum" in html
    for m in ("#d9a94c", "#3fae63", "#4c8fe0", "#a274d6", "#e08b4c", "#dd6b9a"):
        assert m in html, m


def test_bam_dong_co_truyen_phim_shift(html):
    """Gom cụm nhiều dòng = bấm dòng đầu, giữ Shift bấm dòng cuối. Đo trên Chrome
    23/09: quên truyền `event.shiftKey` thì Shift vô tác dụng và chỉ tô được MỘT
    dòng — nhìn qua tưởng chạy đúng."""
    assert "event.shiftKey" in html


def test_khong_con_tab_cai_dat_khoa(html):
    """Luật General (user chốt 23/09): khoá do Owner đặt ở General › API Keys,
    app KHÔNG có cửa sửa khoá — kể cả vai cao nhất."""
    for x in ("pane-s", "tb-s", "napCaiDat", "luuCaiDat", "s-key", "/api/cai-dat"):
        assert x not in html, x
