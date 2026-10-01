# -*- coding: utf-8 -*-
r"""Đã đăng nhập sẵn mà tool vẫn báo "chưa đăng nhập" (user báo 01/10/2026).

User: *"lỗi không đăng nhập Envato được"*. Đo thật bằng Chrome: nạp phiên đã
lưu rồi vào `account.envato.com/sign_in`, Envato KHÔNG chuyển hướng đi đâu cả
mà trả một trang khác hẳn:

    Hey there!
    You're already signed into your Envato account as taikhoansequoia.
    [Continue as taikhoansequoia]  [Sign out and sign in as another user]

URL vẫn nguyên `/sign_in`, và **không còn ô username** (đo: 0 ô).

Code cũ đoán "đã đăng nhập chưa" bằng URL:

    if "sign_in" not in page.url and "login" not in page.url:
        ghi("phiên cũ còn sống — khỏi đăng nhập")

nên nó kết luận CHƯA đăng nhập -> đi điền ô username -> không có ô -> ghi
"không tìm thấy ô đăng nhập" -> ngồi chờ 300s để URL rời `sign_in` (không bao
giờ rời) -> trả lỗi "Quá 300s chưa qua cửa đăng nhập (captcha chưa được bấm
trên desktop server?)".

Tức người dùng bấm nút, chờ 5 phút, ăn một câu báo lỗi về captcha trong khi
tài khoản vẫn đang đăng nhập. Nhật ký prod có đúng dấu vết: 4 lượt bấm, cả 4
đều "không tìm thấy ô đăng nhập — chờ người thao tác trên cửa sổ".
"""
from __future__ import annotations

from autoedit.sourcer import phien


def test_roi_khoi_trang_login_la_DA_VAO():
    assert phien.doc_trang_login("https://account.envato.com/", 0) == "da_vao"
    assert phien.doc_trang_login("https://elements.envato.com/x", 1) == "da_vao"


def test_con_o_email_thi_CAN_DIEN():
    assert phien.doc_trang_login(
        "https://account.envato.com/sign_in", 1) == "can_dien"


def test_O_TRANG_LOGIN_ma_KHONG_con_o_email_la_DA_DANG_NHAP():
    """Ca thật của Envato 01/10 — thứ làm người dùng chờ 300s rồi ăn lỗi."""
    assert phien.doc_trang_login(
        "https://account.envato.com/sign_in", 0) == "da_dang_nhap"


def test_epidemic_cung_dung_luat_do():
    assert phien.doc_trang_login(
        "https://www.epidemicsound.com/login/", 0) == "da_dang_nhap"


def test_KHONG_duoc_quay_lai_doan_bang_MOI_URL():
    """Rào chống hồi quy: `dang_nhap` không được kết luận chỉ bằng URL nữa."""
    import inspect

    src = inspect.getsource(phien.dang_nhap)
    assert "doc_trang_login" in src, (
        "dang_nhap không dùng hàm đọc trạng thái trang — quay lại đoán bằng URL "
        "là người dùng lại chờ 300s rồi ăn lỗi captcha giả")


def test_co_bo_chon_nut_tiep_tuc():
    """Trang «Hey there!» có nút Continue — phải bấm được, không thì vẫn kẹt."""
    assert getattr(phien, "O_NUT_TIEP", ""), "thiếu bộ chọn nút Continue as…"
