"""Bàn kịch bản — tầng web (cổng riêng 9119) + dịch cột tiếng Việt.

Cách ly với dây chuyền dựng (user chốt 15/09): app này KHÔNG import
`autoedit.web.server`, không đụng `jobs.db`, không đọc NAS. Chạy tiến trình
riêng nên sập cũng không kéo theo 9118 đang có người dựng.

Danh tính lấy từ header CRM `X-Remote-User` — cùng quy ước với 9118 để sau này
đặt sau cùng một cổng gác là chạy được ngay, nhưng không dùng chung mã.

Hai chỗ test khoá chặt vì mất dữ liệu là mất công người viết:
  1. Người thứ hai lưu đè khi người thứ nhất đang giữ -> phải bị CHẶN (409),
     và chương phải còn nguyên chữ của người thứ nhất.
  2. Dịch hỏng (hết tiền / mạng chết) -> KHÔNG được xoá hay ghi đè bản tiếng Anh.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.kichban.app import tao_app
from autoedit.kichban.kho import Kho


class DichGia:
    """Bộ dịch giả — test không chạm mạng, không tốn tiền GLM."""

    def __init__(self, hong: bool = False):
        self.hong = hong
        self.da_goi: list[list[str]] = []

    def dich(self, cau: list[str]) -> list[str]:
        if self.hong:
            raise RuntimeError("GLM hết hạn mức")
        self.da_goi.append(list(cau))
        return ["VI:" + c for c in cau]


@pytest.fixture()
def bo(tmp_path):
    kho = Kho(tmp_path / "kichban.db")
    dich = DichGia()
    app = tao_app(kho, dich=dich)
    c = TestClient(app)
    c.headers.update({"X-Remote-User": "haint"})
    c.post("/api/tap", json={"ma": "SH011", "ten": "Đồ uống sau 60"})
    c.post("/api/tap/SH011/chuong", json={"ma": "H"})
    return c, kho, dich


def _nguoi(c, ten):
    """Client thứ hai — mô phỏng người khác đang mở cùng tập."""
    c2 = TestClient(c.app)
    c2.headers.update({"X-Remote-User": ten})
    return c2


# ------------------------------- trang + tập --------------------------------
def test_trang_chu_tra_ve_giao_dien(bo):
    c, _, _ = bo
    r = c.get("/")
    assert r.status_code == 200 and "<title>" in r.text


def test_suc_khoe(bo):
    c, _, _ = bo
    assert c.get("/health").json()["ok"] is True


def test_tao_tap_va_chuong(bo):
    c, _, _ = bo
    assert [t["ma"] for t in c.get("/api/tap").json()] == ["SH011"]
    c.post("/api/tap/SH011/chuong", json={"ma": "C1"})
    assert [x["ma"] for x in c.get("/api/tap/SH011").json()] == ["H", "C1"]


def test_ten_chuong_sai_quy_uoc_bi_tu_choi_co_loi_ro(bo):
    c, _, _ = bo
    r = c.post("/api/tap/SH011/chuong", json={"ma": "Hook"})
    assert r.status_code == 400 and "H, C1" in r.json()["detail"]


def test_khong_co_header_nguoi_dung_thi_khong_duoc_ghi(bo):
    c, _, _ = bo
    khach = TestClient(c.app)          # không gửi X-Remote-User
    r = khach.put("/api/tap/SH011/H", json={"dong": [], "outline": ""})
    assert r.status_code == 401


# --------------------------------- nạp / lưu --------------------------------
def test_nap_kich_ban_dan_vao(bo):
    c, _, _ = bo
    r = c.post("/api/tap/SH011/H/nap", json={"text": "A one.\nB two.\n\nC three.\n"})
    assert r.status_code == 200
    d = c.get("/api/tap/SH011/H").json()["dong"]
    assert [x["en"] for x in d] == ["A one.", "B two.", "C three."]
    assert d[1]["het"] == 1


def test_luu_roi_doc_lai(bo):
    c, _, _ = bo
    dong = [{"en": "A", "vi": "", "het": 0}]
    c.put("/api/tap/SH011/H", json={"dong": dong, "outline": "• mở"})
    d = c.get("/api/tap/SH011/H").json()
    assert d["dong"] == dong and d["outline"] == "• mở"


# --------------------------------- khoá -------------------------------------
def test_giu_chuong_va_nguoi_khac_thay_ai_dang_giu(bo):
    c, _, _ = bo
    assert c.post("/api/tap/SH011/H/giu").status_code == 200
    assert _nguoi(c, "thanhdn").get("/api/tap/SH011").json()[0]["ai_giu"] == "haint"


def test_nguoi_thu_hai_khong_giu_duoc(bo):
    c, _, _ = bo
    c.post("/api/tap/SH011/H/giu")
    assert _nguoi(c, "thanhdn").post("/api/tap/SH011/H/giu").status_code == 409


def test_nguoi_thu_hai_luu_de_bi_chan_va_chu_con_nguyen(bo):
    c, _, _ = bo
    c.post("/api/tap/SH011/H/giu")
    c.put("/api/tap/SH011/H", json={"dong": [{"en": "của haint", "vi": "", "het": 0}],
                                    "outline": ""})
    r = _nguoi(c, "thanhdn").put(
        "/api/tap/SH011/H", json={"dong": [{"en": "đè", "vi": "", "het": 0}], "outline": ""})
    assert r.status_code == 409
    assert c.get("/api/tap/SH011/H").json()["dong"][0]["en"] == "của haint"


def test_nha_khoa_thi_nguoi_khac_vao_duoc(bo):
    c, _, _ = bo
    c.post("/api/tap/SH011/H/giu")
    c.post("/api/tap/SH011/H/nha")
    assert _nguoi(c, "thanhdn").post("/api/tap/SH011/H/giu").status_code == 200


# --------------------------------- xuất .txt --------------------------------
def test_txt_mot_chuong_sach(bo):
    c, _, _ = bo
    c.post("/api/tap/SH011/H/nap", json={"text": 'So the ""diet"" label.\nB.\n'})
    r = c.get("/api/tap/SH011/H/txt")
    assert r.headers["content-type"].startswith("text/plain")
    assert r.text == 'So the "diet" label.\nB.\n'


def test_txt_toan_bo_ghep_dung_thu_tu_chuong(bo):
    c, _, _ = bo
    for ma in ("E", "C10", "C2"):
        c.post(f"/api/tap/SH011/chuong", json={"ma": ma})
    for ma, t in (("H", "hook.\n"), ("C2", "hai.\n"), ("C10", "muoi.\n"), ("E", "ket.\n")):
        c.post(f"/api/tap/SH011/{ma}/nap", json={"text": t})
    assert c.get("/api/tap/SH011/txt").text == "hook.\n\nhai.\n\nmuoi.\n\nket.\n"


def test_txt_cot_tieng_viet(bo):
    c, _, _ = bo
    c.put("/api/tap/SH011/H", json={"dong": [{"en": "A", "vi": "Một", "het": 0}],
                                    "outline": ""})
    assert c.get("/api/tap/SH011/H/txt?cot=vi").text == "Một\n"


# --------------------------------- dịch -------------------------------------
def test_dich_chi_dich_dong_con_thieu(bo):
    c, _, dich = bo
    c.put("/api/tap/SH011/H", json={"dong": [
        {"en": "A", "vi": "đã dịch tay", "het": 0},
        {"en": "B", "vi": "", "het": 0}], "outline": ""})
    c.post("/api/tap/SH011/H/dich")
    d = c.get("/api/tap/SH011/H").json()["dong"]
    assert d[0]["vi"] == "đã dịch tay", "không đụng dòng người đã sửa tay"
    assert d[1]["vi"] == "VI:B"
    assert dich.da_goi == [["B"]], "chỉ gửi dòng thiếu, không gửi cả chương"


def test_dich_hong_thi_khong_mat_chu(tmp_path):
    kho = Kho(tmp_path / "k.db")
    c = TestClient(tao_app(kho, dich=DichGia(hong=True)))
    c.headers.update({"X-Remote-User": "haint"})
    c.post("/api/tap", json={"ma": "SH011", "ten": "x"})
    c.post("/api/tap/SH011/chuong", json={"ma": "H"})
    c.put("/api/tap/SH011/H", json={"dong": [{"en": "A", "vi": "", "het": 0}],
                                    "outline": ""})
    r = c.post("/api/tap/SH011/H/dich")
    assert r.status_code == 502 and "hết hạn mức" in r.json()["detail"]
    assert c.get("/api/tap/SH011/H").json()["dong"][0]["en"] == "A"


# --------------------------------- bản lùi ----------------------------------
def test_lui_ve_ban_cu_qua_api(bo):
    c, _, _ = bo
    c.put("/api/tap/SH011/H", json={"dong": [{"en": "cũ", "vi": "", "het": 0}], "outline": ""})
    c.put("/api/tap/SH011/H", json={"dong": [{"en": "mới", "vi": "", "het": 0}], "outline": ""})
    ban = c.get("/api/tap/SH011/H/ban-cu").json()
    assert len(ban) == 2 and ban[0]["dong"][0]["en"] == "mới"
    c.post("/api/tap/SH011/H/lui", json={"id": ban[-1]["id"]})
    assert c.get("/api/tap/SH011/H").json()["dong"][0]["en"] == "cũ"


# ----------------------------- cách ly production ---------------------------
def test_khong_dinh_gi_toi_day_chuyen_dung():
    """Cấm import ngược vào tầng dựng: `kichban` phải đứng riêng để sập không kéo
    theo 9118. Ngoại lệ DUY NHẤT: `web.chapters` (luật tên chương H/C1/E)."""
    import pathlib
    import re

    goc = pathlib.Path(__file__).resolve().parents[1] / "autoedit" / "kichban"
    xau = []
    for f in goc.glob("*.py"):
        for m in re.findall(r"^\s*(?:from|import)\s+(autoedit[\w.]*)",
                            f.read_text(encoding="utf-8"), re.M):
            if not m.startswith(("autoedit.kichban", "autoedit.web.chapters")):
                xau.append(f"{f.name}: {m}")
    assert not xau, f"kichban đang import vào tầng dựng: {xau}"


def test_api_toi_tra_ve_nguoi_dang_dang_nhap(bo):
    """Trang phải biết mình là ai để phân biệt khoá của mình với khoá người khác."""
    c, _, _ = bo
    assert c.get("/api/toi").json()["nguoi"] == "haint"
    assert TestClient(c.app).get("/api/toi").json()["nguoi"] == ""
