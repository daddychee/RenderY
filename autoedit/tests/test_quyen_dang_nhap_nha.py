"""Người dựng không bấm được nút đăng nhập Envato (user báo 09/09).

Gặp clip watermark thì phải đăng nhập lại Envato rồi Export lại. Nhưng nút đó
bị gác bởi `_duoc_nghien_cuu_kenh` = {admin, owner, manager} — cửa gác viết cho
việc KHÁC. Lý do của nó ghi ngay trong code: *"nghiên cứu kênh ref tốn tải
YouTube + lượt GLM, và chuẩn dựng là quyết định cấp quản lý"*. Đăng nhập Envato
thì **không tốn gì**, và đúng là việc người dựng cần làm ngay lúc gặp watermark.

Đo trên IAM của CRM: `haint` và `hieuvn` đều **level 2 — Vận hành – Sản xuất**,
tức người dựng. Nên họ bị chặn.

User chốt: tách cửa gác RIÊNG cho việc đăng nhập nhà cung cấp, KHÔNG đụng quyền
nghiên cứu kênh. Gác theo **level ≥ 2** (mô hình của chính CRM: 5 ban quản trị,
4 quản lý, 2 vận hành) và vẫn nhận vai làm đường lùi khi thiếu header level.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def tc(monkeypatch):
    from autoedit.web import server

    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    return TestClient(server.app, client=("127.0.0.1", 51001))


def _dau(vai: str = "", level: str = "") -> dict:
    h = {"X-Forwarded-Host": "crm.local", "X-Remote-User": "ai_do"}
    if vai:
        h["X-Remote-Role"] = vai
    if level:
        h["X-Remote-Level"] = level
    return h


def _req(vai: str = "", level: str = "", qua_crm: bool = True):
    """Request giả — `headers` phải KHÔNG PHÂN BIỆT HOA THƯỜNG như hàng thật.

    Bẫy vừa dính: dùng `dict` thường thì `headers.get("x-remote-level")` luôn
    trả None, `behind_crm` thành False, cửa gác mở toang — và test XANH VÌ LÝ DO
    SAI, không phải vì code đúng.
    """
    from starlette.datastructures import Headers

    h = _dau(vai, level) if qua_crm else {}
    return type("R", (), {
        "headers": Headers(h),
        "client": type("C", (), {"host": "127.0.0.1"})(),
    })()


def test_nguoi_dung_level_2_bam_duoc(tc):
    """Đúng ca haint/hieuvn: level 2, vai không thuộc nhóm quản lý."""
    from autoedit.web.server import duoc_dang_nhap_nha

    assert duoc_dang_nhap_nha(_req("viewer", "2")) is True


def test_vai_quan_ly_khong_co_level_van_bam_duoc(tc):
    """Header level thiếu (cổng cũ) -> vai vẫn là đường lùi."""
    from autoedit.web.server import duoc_dang_nhap_nha

    for vai in ("admin", "owner", "manager", "leader"):
        assert duoc_dang_nhap_nha(_req(vai)) is True, vai


def test_level_0_va_vai_la_thi_KHONG_bam_duoc(tc):
    """Khách vãng lai không được kích phiên trình duyệt trên server."""
    from autoedit.web.server import duoc_dang_nhap_nha

    assert duoc_dang_nhap_nha(_req("khach", "0")) is False


def test_ngoai_CRM_thi_mo(tc):
    """Chạy trực tiếp/dev không có SSO — y khuôn `is_admin`."""
    from autoedit.web.server import duoc_dang_nhap_nha

    assert duoc_dang_nhap_nha(_req(qua_crm=False)) is True


def test_api_dang_nhap_nhan_nguoi_dung_level_2(tc):
    r = tc.post("/api/phien/dang-nhap?nha=khong-co-that", headers=_dau("viewer", "2"))
    # qua được cửa quyền -> dừng ở kiểm tên nhà (422), KHÔNG phải 403
    assert r.status_code == 422, r.text


def test_api_dang_nhap_van_chan_khach(tc):
    r = tc.post("/api/phien/dang-nhap?nha=envato", headers=_dau("khach", "0"))
    assert r.status_code == 403


def test_quyen_nghien_cuu_kenh_KHONG_bi_noi_theo(tc):
    """Tách cửa gác: mở nút đăng nhập KHÔNG được kéo theo quyền hút nguồn/nạp
    ref — đó vẫn là quyết định cấp quản lý (user chốt 05/09)."""
    r = tc.post("/api/sotra/hut", json={"tu_khoa": ["x"]}, headers=_dau("viewer", "2"))
    assert r.status_code == 403, "người dựng vớ được cả quyền hút nguồn"
