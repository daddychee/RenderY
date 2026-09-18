"""Fixture chung toàn suite."""

import pytest


@pytest.fixture(autouse=True)
def _no_prenorm(monkeypatch):
    """TOC-3: tắt normalize NỀN trong test suite — file 'video' trong test là bytes giả,
    để mặc định mỗi test sourcer sẽ spawn ffmpeg thật (chậm + noise). Test prenorm
    chuyên trách tự setenv bật lại + fake hàm normalize.
    TOC-3b: tắt luôn warm-up tải song song — thread nền làm số đếm download của các
    test cũ nhiễu ngẫu nhiên. Test TOC-3b chuyên trách tự bật lại."""
    monkeypatch.setenv("AUTOEDIT_PRENORM", "0")
    monkeypatch.setenv("AUTOEDIT_DL_PARALLEL", "0")


@pytest.fixture(autouse=True)
def _ho_so_ngach_rieng(monkeypatch, tmp_path):
    """QĐ18: mỗi test có kho HỒ SƠ NGÁCH riêng.

    Không có rào này thì `ngach.da_khai_nhan_vat()` đọc `F:\AutoEdit\ho_so_ngach`
    trên máy thật — hôm nào có người duyệt hồ sơ COOKING là
    `test_nhan_vat_ngach.py` đổi màu vì một file NGOÀI repo. Đúng cái bẫy "test
    xanh giả do dữ liệu thử sai". Test nào cần kho riêng thì vá đè lên fixture
    này (monkeypatch sau thắng).
    """
    from autoedit import ngach_ho_so

    monkeypatch.setattr(ngach_ho_so, "resolve_data_root",
                        lambda *a, **k: tmp_path / "_kho_test")
