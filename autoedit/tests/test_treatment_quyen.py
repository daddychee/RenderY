"""Treatment — PHÂN QUYỀN: L2 chỉ xem, Manager/Owner mới thêm sửa (user 23/09).

Khuôn Permissions v2 của cụm (DE.md mục 14, `apps/ai-agent` làm mẫu): gateway
tính quyền rồi tiêm cờ `X-Remote-Actions`; **app CHỈ TIN CỜ, không tự tính lại**
(luật ghim #2) và **thiếu header → rỗng → fail-closed**.

Nên ở đây không có chỗ nào đọc level rồi tự suy. Muốn mở cho một người cụ thể
dưới L4 thì Owner tick lẻ ở trang Permissions — chảy sang ngay lượt sau, không
phải sửa code.

Cửa gác đặt ở TẦNG GHI của máy chủ, không phải ở chỗ ẩn nút: người xem mở tab
cũ, bấm lưu, vẫn phải bị chặn.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho


class DichGia:
    def dich(self, cau):
        return ["VI:" + c for c in cau]


@pytest.fixture()
def kho(tmp_path):
    return Kho(tmp_path / "k.db")


def _khach(app, ten: str, hanh_dong: str = "") -> TestClient:
    """Client mang đúng bộ cờ gateway phát cho vai đó."""
    c = TestClient(app)
    c.headers.update({"X-Remote-User": ten, "X-Remote-Actions": hanh_dong})
    return c


@pytest.fixture()
def bo(kho):
    app = tao_app(kho, dich=DichGia())
    chu = _khach(app, "owner", "sua,quan_tri")
    chu.post("/api/tap", json={"ma": "SH011", "ten": "x"})
    chu.post("/api/tap/SH011/chuong", json={"ma": "H"})
    chu.post("/api/tap/SH011/H/nap", json={"text": "A one.\nB two.\n"})
    return app, chu


# ------------------------------- người xem ----------------------------------
def test_L2_van_XEM_duoc_het(bo):
    """Chỉ xem không có nghĩa là mù: vẫn đọc được kịch bản, bản dịch, nguồn."""
    app, _ = bo
    xem = _khach(app, "nhanvien")
    assert xem.get("/api/tap").status_code == 200
    assert xem.get("/api/tap/SH011").status_code == 200
    d = xem.get("/api/tap/SH011/H").json()
    assert [x["en"] for x in d["dong"]] == ["A one.", "B two."]
    assert xem.get("/api/tap/SH011/H/txt").status_code == 200


def test_L2_khong_sua_duoc_gi(bo):
    """Mọi đường GHI đều đóng — kể cả khi mở tab cũ rồi bấm."""
    app, _ = bo
    xem = _khach(app, "nhanvien")
    assert xem.put("/api/tap/SH011/H",
                   json={"dong": [], "outline": "đè"}).status_code == 403
    assert xem.post("/api/tap/SH011/H/nap", json={"text": "đè"}).status_code == 403
    assert xem.post("/api/tap", json={"ma": "X1", "ten": "x"}).status_code == 403
    assert xem.post("/api/tap/SH011/chuong", json={"ma": "C1"}).status_code == 403
    assert xem.post("/api/tap/SH011/H/dich").status_code == 403
    assert xem.post("/api/tap/SH011/H/giu").status_code == 403


def test_L2_bam_luu_thi_chu_nguoi_khac_con_nguyen(bo):
    app, chu = bo
    _khach(app, "nhanvien").put("/api/tap/SH011/H",
                                json={"dong": [{"en": "đè", "vi": "", "het": 0}],
                                      "outline": ""})
    assert chu.get("/api/tap/SH011/H").json()["dong"][0]["en"] == "A one."


# --------------------------- Manager / Owner --------------------------------
def test_co_co_sua_thi_lam_duoc(bo):
    app, _ = bo
    ql = _khach(app, "quanly", "sua")
    assert ql.put("/api/tap/SH011/H",
                  json={"dong": [{"en": "A one.", "vi": "", "het": 0}],
                        "outline": "• mở"}).status_code == 200
    assert ql.post("/api/tap/SH011/chuong", json={"ma": "C1"}).status_code == 200


# ------------------------------ fail-closed ---------------------------------
def test_thieu_header_co_thi_CHI_XEM(bo):
    """Luật cụm: thiếu cờ → rỗng → fail-closed. Vào thẳng cổng 9121 (không qua
    CRM) thì chỉ xem được, không sửa — thà chặn oan còn hơn mở toang."""
    app, _ = bo
    khach = TestClient(app)
    khach.headers.update({"X-Remote-User": "ai-do"})
    assert khach.get("/api/tap/SH011/H").status_code == 200
    assert khach.put("/api/tap/SH011/H",
                     json={"dong": [], "outline": ""}).status_code == 403


def test_app_KHONG_tu_tinh_quyen_theo_level(bo):
    """Cấm map theo level trong app (luật ghim #2): gateway gửi level cao mà
    không có cờ `sua` thì vẫn là người xem — vì ô tick lẻ của Owner nằm ở cờ."""
    app, _ = bo
    c = TestClient(app)
    c.headers.update({"X-Remote-User": "sep", "X-Remote-Level": "5",
                      "X-Remote-Role": "admin", "X-Remote-Actions": ""})
    assert c.put("/api/tap/SH011/H", json={"dong": [], "outline": ""}).status_code == 403


def test_trang_bao_ro_dang_o_che_do_chi_xem(bo):
    """Người xem phải BIẾT mình đang chỉ xem, không phải gõ xong mới thấy hỏng."""
    app, _ = bo
    assert _khach(app, "nhanvien").get("/api/toi").json()["sua_duoc"] is False
    assert _khach(app, "quanly", "sua").get("/api/toi").json()["sua_duoc"] is True
