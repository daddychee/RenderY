"""504 phải được THỬ LẠI như mọi lỗi 5xx khác.

31/08: job LI093 chết ở chương C9 vì Pexels trả 504 Gateway Timeout, trong khi danh
sách retry chỉ liệt kê (500, 502, 503). 504 rơi xuống raise_for_status() -> vỡ job
sau 3 chương đã dựng xong. Cùng lúc vision.py và visiongate.py sót y hệt: ba bản sao
chép tay của cùng một danh sách.
"""

from __future__ import annotations

import inspect

from autoedit.httpx_ma import MA_THU_LAI, nen_thu_lai


def test_504_duoc_thu_lai():
    """Chính mã đã giết job LI093."""
    assert nen_thu_lai(504)


def test_du_cac_ma_5xx_tam_thoi():
    for ma in (500, 502, 503, 504, 529):
        assert nen_thu_lai(ma), ma


def test_429_va_408_duoc_thu_lai():
    assert nen_thu_lai(429) and nen_thu_lai(408)


def test_cloudflare_5xx():
    """520-524: Cloudflare báo origin chết/timeout — tạm, không phải lỗi mình."""
    for ma in range(520, 525):
        assert nen_thu_lai(ma), ma


def test_4xx_khong_thu_lai():
    """400/401/403/404 = yêu cầu sai; thử lại chỉ tổ chậm và che mất lỗi thật."""
    for ma in (400, 401, 403, 404, 422):
        assert not nen_thu_lai(ma), ma


def test_200_khong_nam_trong_danh_sach():
    assert not nen_thu_lai(200)


def test_khong_con_danh_sach_5xx_chep_tay():
    """Rào chặn: viết lại (500, 502, 503) ở đâu đó là sót 504 lần nữa."""
    from autoedit.library import vision
    from autoedit.ranker import visiongate
    from autoedit.sourcer import pexels

    for mod in (pexels, vision, visiongate):
        src = inspect.getsource(mod)
        assert "500, 502, 503)" not in src, (
            f"{mod.__name__} còn danh sách 5xx chép tay — dùng nen_thu_lai() "
            f"để 504 (và các mã tạm khác) không bị sót")
        assert "nen_thu_lai" in src, f"{mod.__name__} chưa dùng nen_thu_lai"
