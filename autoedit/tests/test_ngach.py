"""Ngách lấy từ DANH BẠ NỀN của CRM, không gõ tay nữa (user chốt 08/09).

Vì sao: ô Niche đang nhập tay tự do — hậu quả đo được là Library có CẢ
`Life In` LẪN `life-in`, hai thư mục cho cùng một ngách.

Khảo sát: sổ ngách nằm ở `D:\AI AGENT OUTLIERY\data\nen\danh_ba.db`, bảng
`ngach` (cột `ma`, `ten_chuan`, `trang_thai`, `ghi_chu`, `tao_luc`), 13 ngách.
KHÔNG có API HTTP, và KHÔNG có cột nào cho "cần địa danh".

Quyết định: đọc THẲNG file ở chế độ chỉ-đọc (QĐ12) · cờ "cần địa danh" đặt
trong RenderY (QĐ13) · ba ngách cần địa danh: LIFE IN, LIVING IN,
TRAVEL DOCUMENTARY (QĐ14).
"""

from __future__ import annotations

import sqlite3

import pytest

NGACH_THAT = [                      # sao y 13 dòng thật trong danh bạ 08/09
    ("N-COOKING", "COOKING", "khai_thac"),
    ("N-HEALTHY-EATING", "HEALTHY EATING", "khai_thac"),
    ("N-INVESTIGATION", "INVESTIGATION", "khai_thac"),
    ("N-LIFE-IN", "LIFE IN", "mo_rong"),
    ("N-LIVING-IN", "LIVING IN", "khai_thac"),
    ("N-OLD", "OLD", "khai_thac"),
    ("N-OLD-NEWBIE", "OLD NEWBIE", "duy_tri"),
    ("N-RETIREMENT", "RETIREMENT", "khai_thac"),
    ("N-WHAT-IF", "SCI-FI", "khai_thac"),
    ("N-SENIOR-HEALTH", "SENIOR HEALTH", "khai_thac"),
    ("N-SPACE", "SPACE", "khai_thac"),
    ("N-STORM", "STORM", "khai_thac"),
    ("N-TRAVEL-DOCUMENTA", "TRAVEL DOCUMENTARY", "khai_thac"),
]


@pytest.fixture
def danh_ba(tmp_path, monkeypatch):
    """Bản sao danh bạ nền — cùng schema, cùng dữ liệu thật."""
    f = tmp_path / "danh_ba.db"
    c = sqlite3.connect(f)
    c.execute("CREATE TABLE ngach(ma TEXT PRIMARY KEY, ten_chuan TEXT, "
              "trang_thai TEXT, ghi_chu TEXT, tao_luc TEXT)")
    c.executemany("INSERT INTO ngach(ma, ten_chuan, trang_thai) VALUES(?,?,?)",
                  NGACH_THAT)
    c.commit()
    c.close()
    monkeypatch.setenv("RENDERY_DANH_BA", str(f))
    return f


# ------------------------------------------------------------------ đọc sổ

def test_liet_ke_du_13_ngach(danh_ba):
    from autoedit import ngach

    ds = ngach.liet_ke()
    assert len(ds) == 13
    assert {x["ten"] for x in ds} >= {"LIFE IN", "COOKING", "TRAVEL DOCUMENTARY"}
    assert all(x["ma"].startswith("N-") for x in ds)


def test_doc_CHI_DOC_khong_duoc_ghi_vao_danh_ba(danh_ba):
    """Danh bạ là của app khác. Mở nhầm chế độ ghi là có ngày RenderY làm hỏng
    dữ liệu của cả tổ chức."""
    from autoedit import ngach

    conn = ngach._mo()
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO ngach(ma, ten_chuan) VALUES('N-X','X')")
    finally:
        conn.close()


def test_danh_ba_mat_thi_KHONG_giet_viec(tmp_path, monkeypatch):
    """CRM tắt / ổ D chưa gắn -> trả rỗng, KHÔNG ném lỗi. Nộp tập vẫn phải chạy
    được, nếu không thì một app khác chết là cả RenderY chết theo."""
    from autoedit import ngach

    monkeypatch.setenv("RENDERY_DANH_BA", str(tmp_path / "khong-co.db"))
    assert ngach.liet_ke() == []
    assert ngach.doc_duoc() is False


def test_doc_duoc_bao_dung_khi_co_so(danh_ba):
    from autoedit import ngach

    assert ngach.doc_duoc() is True


# --------------------------------------------------------- cờ cần địa danh

def test_ba_ngach_can_dia_danh(danh_ba):
    from autoedit import ngach

    for ten in ("LIFE IN", "LIVING IN", "TRAVEL DOCUMENTARY"):
        assert ngach.can_dia_danh(ten) is True, ten


def test_ngach_khac_KHONG_can_dia_danh(danh_ba):
    """Nấu ăn, sức khỏe người già... nội dung không gắn địa điểm."""
    from autoedit import ngach

    for ten in ("COOKING", "SENIOR HEALTH", "HEALTHY EATING", "SCI-FI", "OLD"):
        assert ngach.can_dia_danh(ten) is False, ten


def test_can_dia_danh_nhan_ca_MA_lan_TEN(danh_ba):
    from autoedit import ngach

    assert ngach.can_dia_danh("N-LIFE-IN") is True
    assert ngach.can_dia_danh("life in") is True          # thường/hoa đều được
    assert ngach.can_dia_danh("N-COOKING") is False


def test_ngach_LA_thi_van_doi_dia_danh(danh_ba):
    """Không biết ngách gì (bỏ trống, hoặc sổ hỏng) -> GIỮ luật cũ: bắt khai địa
    danh. Nới lỏng khi đang mù là mở lại đúng cái bẫy chợ-Trung-Quốc."""
    from autoedit import ngach

    assert ngach.can_dia_danh("") is True
    assert ngach.can_dia_danh("ngach-la-hoac-go-tay") is True


def test_doi_bo_can_geo_bang_env(danh_ba, monkeypatch):
    """QĐ13: cờ nằm ở RenderY nên phải sửa được mà không đụng danh bạ."""
    from autoedit import ngach

    monkeypatch.setenv("RENDERY_NGACH_GEO", "N-COOKING, TRAVEL DOCUMENTARY")
    assert ngach.can_dia_danh("COOKING") is True
    assert ngach.can_dia_danh("TRAVEL DOCUMENTARY") is True
    assert ngach.can_dia_danh("LIFE IN") is False          # đã bị thay khỏi bộ


# ------------------------------------------------------------ kiểm hợp lệ

def test_ngach_phai_CO_THAT_trong_danh_ba(danh_ba):
    from autoedit import ngach

    assert ngach.hop_le("LIFE IN") is True
    assert ngach.hop_le("N-LIFE-IN") is True
    assert ngach.hop_le("life-in") is False, "gõ tay kiểu cũ không còn được nhận"
    assert ngach.hop_le("") is False


def test_so_hong_thi_KHONG_chan_nop_tap(tmp_path, monkeypatch):
    """Không đọc được sổ thì không có cơ sở để bác — phải cho qua, nếu không
    CRM tắt là cả team đứng việc."""
    from autoedit import ngach

    monkeypatch.setenv("RENDERY_DANH_BA", str(tmp_path / "khong-co.db"))
    assert ngach.hop_le("bất kỳ") is True


# ------------------------------------------------------- API + form nộp tập

@pytest.fixture
def may_chu(danh_ba, tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from autoedit.web import queue as q, server

    monkeypatch.setattr(server, "ROOT", tmp_path)
    nas = tmp_path / "nas"
    tap = nas / "LI200"
    (tap / "RenderY").mkdir(parents=True)
    for ten in ("H", "C1", "E"):
        (tap / "RenderY" / f"{ten}.mp3").write_bytes(b"x" * 64)
        (tap / "RenderY" / f"{ten}.txt").write_text("xin chao", encoding="utf-8")
    monkeypatch.setattr(server, "_trong_nas", lambda p: tap)
    q.connect(tmp_path / "jobs.db").close()
    return TestClient(server.app), str(tap)


def test_api_ngach_tra_danh_sach_kem_co_geo(may_chu):
    tc, _ = may_chu
    r = tc.get("/api/ngach")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["doc_duoc"] is True and len(d["ngach"]) == 13
    theo_ten = {x["ten"]: x for x in d["ngach"]}
    assert theo_ten["LIFE IN"]["can_dia_danh"] is True
    assert theo_ten["COOKING"]["can_dia_danh"] is False


def test_nop_tap_ngach_LIFE_IN_thieu_dia_danh_bi_chan(may_chu):
    tc, folder = may_chu
    r = tc.post("/api/jobs", json={"folder": folder, "niche": "LIFE IN",
                                   "dia_danh": ""})
    assert r.status_code == 422 and "địa danh" in r.json()["detail"].lower()


def test_nop_tap_ngach_COOKING_KHONG_can_dia_danh(may_chu):
    """Đây là điều user muốn: ngách không gắn địa điểm thì khỏi khai."""
    tc, folder = may_chu
    r = tc.post("/api/jobs", json={"folder": folder, "niche": "COOKING",
                                   "dia_danh": ""})
    assert r.status_code == 200, r.text


def test_nop_tap_ngach_GO_TAY_bi_chan(may_chu):
    """`life-in` gõ tay chính là thứ đẻ ra hai thư mục trùng trong Library."""
    tc, folder = may_chu
    r = tc.post("/api/jobs", json={"folder": folder, "niche": "life-in",
                                   "dia_danh": "afghanistan"})
    assert r.status_code == 422 and "ngách" in r.json()["detail"].lower()


def test_nop_tap_thieu_ngach_bi_chan(may_chu):
    tc, folder = may_chu
    r = tc.post("/api/jobs", json={"folder": folder, "niche": "",
                                   "dia_danh": "afghanistan"})
    assert r.status_code == 422


def test_so_hong_thi_van_nop_duoc(may_chu, tmp_path, monkeypatch):
    """CRM tắt: không kiểm được ngách thì cho qua, nhưng địa danh vẫn phải khai
    (không biết ngách gì -> giữ luật cũ)."""
    tc, folder = may_chu
    monkeypatch.setenv("RENDERY_DANH_BA", str(tmp_path / "khong-co.db"))
    assert tc.post("/api/jobs", json={"folder": folder, "niche": "gì đó",
                                      "dia_danh": "afghanistan"}).status_code == 200
    assert tc.post("/api/jobs", json={"folder": folder, "niche": "gì đó",
                                      "dia_danh": ""}).status_code == 422


def test_giao_dien_chon_ngach_tu_danh_sach():
    """Ô Niche phải là DANH SÁCH CHỌN nạp từ /api/ngach, không còn gõ tự do."""
    from pathlib import Path

    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    assert "/api/ngach" in h, "form chưa nạp danh sách ngách"
    i = h.index('id="ns-niche"')
    the = h[max(0, i - 200):i]
    assert "<select" in the, "ô Niche vẫn là input gõ tay"


def test_giao_dien_an_o_dia_danh_theo_ngach():
    """Chọn ngách không cần địa danh thì ô địa danh không được đòi nữa."""
    from pathlib import Path

    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    assert "can_dia_danh" in h, "giao diện chưa dùng cờ cần-địa-danh"


def test_key_cai_dat_co_bo_ngach_geo():
    """QĐ13: cờ sửa được ở trang Cài đặt."""
    from autoedit.web.server import SETTINGS_KEYS

    assert "RENDERY_NGACH_GEO" in SETTINGS_KEYS
    assert "RENDERY_DANH_BA" in SETTINGS_KEYS
