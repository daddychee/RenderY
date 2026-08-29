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
