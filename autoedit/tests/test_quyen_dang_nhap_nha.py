r"""Nhân sự không bấm được nút đăng nhập Envato — user báo 10/09/2026.

User: *"Nhân sự không ấn được vào envato do quyền đang set chỉ có của Manager"*.

ĐO THẬT 10/09 trên production, gọi endpoint với từng cấp:

```
level 2 vai editor  -> 200 OK   (được phép)
level 1 vai editor  -> chặn
level 0 vai ''      -> chặn
```

**Server KHÔNG chặn level 2** — cửa `duoc_dang_nhap_nha` đã sửa 09/09 đúng cho
haint/hieuvn (cả hai đều level 2 "Vận hành — Sản xuất").

Lỗi nằm ở GIAO DIỆN:

1. `/api/me` trả `nghien_cuu_kenh` nhưng **không trả `dang_nhap_nha`** — trang
   không biết người đang xem có quyền hay không.
2. Tooltip của chỉ báo phiên ghi cứng **"(manager)"** — sai sự thật với level 2,
   nên nhân sự đọc xong không dám bấm.

Đây là bẫy ngược với BH11: ở đó test xanh mà chức năng hỏng; ở đây chức năng
CHẠY ĐƯỢC mà giao diện bảo là không được, nên không ai dùng.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path):
    from autoedit.web import server

    monkeypatch.setattr(server, "_trust_proxy", lambda r: True)
    return TestClient(server.app)


def _me(client, level: int, vai: str = "editor") -> dict:
    # `X-Forwarded-Host` là dấu hiệu "đang chạy sau cổng CRM" (`behind_crm`);
    # thiếu nó thì mọi cửa đều MỞ (khuôn `is_admin`: chạy trực tiếp là dev).
    r = client.get("/api/me", headers={"X-Remote-User": "haint",
                                       "X-Forwarded-Host": "crm.outliery",
                                       "X-Remote-Level": str(level),
                                       "X-Remote-Role": vai})
    assert r.status_code == 200, r.text
    return r.json()


def test_api_me_TRA_quyen_dang_nhap_nha(client):
    """Giao diện phải biết mình có quyền hay không mới hiện đúng."""
    d = _me(client, 2)
    assert "dang_nhap_nha" in d, (
        "/api/me không trả `dang_nhap_nha` — trang đoán mò, đành ghi cứng "
        "'(manager)' và nhân sự level 2 không dám bấm")


def test_level_2_DUOC_dang_nhap_nha(client):
    """haint/hieuvn đều level 2 — phải được phép, đúng như cửa server đã mở."""
    assert _me(client, 2)["dang_nhap_nha"] is True


def test_level_1_KHONG_duoc(client):
    assert _me(client, 1, vai="")["dang_nhap_nha"] is False


def test_vai_manager_van_duoc_khi_cong_khong_gui_level(client):
    """Đường lùi cho cổng cũ: có vai mà không có header level."""
    assert _me(client, 0, vai="manager")["dang_nhap_nha"] is True


def test_UI_KHONG_ghi_cung_chu_manager():
    """Tooltip nói SAI là chức năng chết dù mã chạy được.

    Chỉ báo phiên là đường DUY NHẤT để đăng nhập lại Envato; ghi '(manager)'
    lên đó khiến người dựng level 2 tưởng không có quyền.
    """
    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    i = h.find('id="of-phien"')
    assert i > 0, "không tìm thấy chỉ báo phiên"
    assert "(manager)" not in h[i:i + 400], (
        "tooltip chỉ báo phiên vẫn ghi cứng '(manager)' — sai với level 2")


def test_UI_dung_quyen_that_de_hien(self_check=None):
    """Trang phải dùng `ME.dang_nhap_nha` chứ không đoán."""
    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    assert "dang_nhap_nha" in h, (
        "index.html không dùng quyền thật từ /api/me để hiện chỉ báo phiên")
