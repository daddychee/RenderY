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

from factcheck.app import tao_app
from factcheck.kho import Kho


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
def test_dung_rieng_duoc_khong_can_renderY():
    """Factcheck là MỘT THƯ MỤC ĐỘC LẬP (user chốt 18/09: "đóng gói tool trong một
    folder tên là Factcheck"). Chỉ được đụng `autoedit` ở ĐÚNG MỘT chỗ: đọc két
    khoá khi tình cờ chạy cạnh RenderY — và chỗ đó phải nằm trong try/except để
    mang thư mục này đi máy khác vẫn chạy.
    """
    import pathlib
    import re

    goc = pathlib.Path(__file__).resolve().parents[1] / "factcheck"
    xau = []
    for f in goc.glob("*.py"):
        chu = f.read_text(encoding="utf-8")
        for m in re.finditer(r"^(\s*)(?:from|import)\s+(autoedit[\w.]*)", chu, re.M):
            thut, ten = m.group(1), m.group(2)
            if not ten.startswith("autoedit.web.ket_v3"):
                xau.append(f"{f.name}: {ten} — chỉ được phép két khoá")
            elif not thut:
                xau.append(f"{f.name}: {ten} import ở đầu file — phải nằm trong try/except")
    assert not xau, xau


def test_api_toi_tra_ve_nguoi_dang_dang_nhap(bo):
    """Trang phải biết mình là ai để phân biệt khoá của mình với khoá người khác."""
    c, _, _ = bo
    assert c.get("/api/toi").json()["nguoi"] == "haint"
    assert TestClient(c.app).get("/api/toi").json()["nguoi"] == ""


# --------------------------- tin header hay không ---------------------------
def test_chi_tin_header_khi_co_co_va_loopback(tmp_path, monkeypatch):
    """Luật bảo mật của cụm OUTLIERY (docs/bao-mat-internet.md, GD1): app tin
    `X-Remote-*` vô điều kiện thì ai cũng curl một cái là thành người khác. Chỉ
    tin khi CÓ CỜ `KICHBAN_TRUST_PROXY=1` VÀ client là loopback — cổng CRM đã
    vứt header giả do người ngoài gửi lên.

    Mặc định (không đặt cờ) vẫn tin, để chạy tay trên máy mình không vướng; cờ
    này để BẬT chế độ nghiêm khi đặt sau proxy.
    """
    from factcheck.app import tao_app as _tao

    kho = Kho(tmp_path / "k.db")
    c = TestClient(_tao(kho), client=("10.0.0.9", 5000))   # KHÔNG phải loopback
    c.headers.update({"X-Remote-User": "ke-gia-mao"})

    monkeypatch.setenv("KICHBAN_TRUST_PROXY", "1")
    assert c.get("/api/toi").json()["nguoi"] == "", "ngoài loopback thì không tin header"
    r = c.post("/api/tap", json={"ma": "X", "ten": "x"})
    assert r.status_code == 401

    monkeypatch.delenv("KICHBAN_TRUST_PROXY")
    assert c.get("/api/toi").json()["nguoi"] == "ke-gia-mao", "chưa bật cờ thì giữ đường cũ"


def test_co_xuong_may_chu_chay_that(tmp_path, monkeypatch):
    """uvicorn cần một chỗ bám: `start-all.ps1` gọi `app:tao_app_mac_dinh --factory`.
    Dùng factory chứ không phải biến APP sẵn ở module — biến sẵn nghĩa là chỉ
    IMPORT thôi đã mở SQLite, và cả suite test sẽ đẻ ra DB thật trong thư mục nhà.
    """
    from factcheck import app as mapp

    monkeypatch.setenv("KICHBAN_DB", str(tmp_path / "k.db"))
    a = mapp.tao_app_mac_dinh()
    assert TestClient(a).get("/health").json()["ok"] is True
    assert (tmp_path / "k.db").exists()


# ------------------- danh tinh khi CHUA nap vao cong CRM ---------------------
def test_chua_khai_ten_thi_chi_xem(bo):
    """Chạy thẳng trên LAN (chưa qua CRM) thì không có X-Remote-User. Chưa khai
    tên = chỉ xem — thà chặn còn hơn để hai người ghi đè nhau vô danh."""
    c, _, _ = bo
    khach = TestClient(c.app)
    assert khach.get("/api/toi").json()["nguoi"] == ""
    assert khach.put("/api/tap/SH011/H", json={"dong": [], "outline": ""}).status_code == 401


def test_khai_ten_roi_lam_viec_duoc(bo):
    c, _, _ = bo
    khach = TestClient(c.app)
    assert khach.post("/api/toi", json={"nguoi": "thanhdn"}).json()["nguoi"] == "thanhdn"
    assert khach.get("/api/toi").json()["nguoi"] == "thanhdn", "tên phải sống qua request sau"
    assert khach.put("/api/tap/SH011/H",
                     json={"dong": [{"en": "A", "vi": "", "het": 0}], "outline": ""}
                     ).status_code == 200


def test_ten_khai_duoc_chuan_hoa(bo):
    """Tên là KHOÁ CHƯƠNG nên phải ổn định: bỏ dấu, hạ chữ, chỉ giữ chữ-số-._- —
    cùng khuôn tên CRM gửi xuống ('Nguyễn Văn A' -> 'nguyenvana')."""
    c, _, _ = bo
    khach = TestClient(c.app)
    assert khach.post("/api/toi", json={"nguoi": " Hải NT "}).json()["nguoi"] == "haint"
    # Dấu chấm GIỮ LẠI vì tên thật hay có ('nguyen.van.a'); dấu gạch chéo thì bỏ.
    # Tên chỉ nằm trong giá trị DB, không ghép vào đường dẫn, nên '..' vô hại.
    assert khach.post("/api/toi", json={"nguoi": "a b/../c"}).json()["nguoi"] == "ab..c"


def test_ten_rong_bi_tu_choi(bo):
    c, _, _ = bo
    assert TestClient(c.app).post("/api/toi", json={"nguoi": "  "}).status_code == 400


def test_header_crm_thang_ten_tu_khai(bo):
    """Khi nào nối vào CRM: danh tính thật phải đè tên tự khai, không thì ai cũng
    mượn được tên người khác mặc dù hệ đã biết họ là ai."""
    c, _, _ = bo
    khach = TestClient(c.app)
    khach.post("/api/toi", json={"nguoi": "muon-ten"})
    khach.headers.update({"X-Remote-User": "haint"})
    assert khach.get("/api/toi").json()["nguoi"] == "haint"


# ------------------------------- khoá LLM -----------------------------------
def test_lay_khoa_glm_tu_ket_truoc_roi_moi_den_env(monkeypatch):
    """MỘT CỬA KHOÁ (luật cụm, docs/APPS.md bước 5): khoá do Owner nhập ở
    General › API Keys, app hỏi két qua loopback — app KHÔNG giữ sổ khoá riêng,
    KHÔNG đọc .env. Bàn kịch bản dùng lại đúng cấp phát của RenderY (`cham_footage`,
    nhà glm) vì nó LÀ công cụ của RenderY; chép khoá sang chỗ khác là đẻ sổ thứ hai.

    Két tắt/chưa cấp phát -> rơi về biến môi trường (chạy tay trên máy dev).
    """
    from factcheck import dich as mdich

    monkeypatch.setattr(mdich, "_khoa_tu_ket", lambda: ("KHOA-KET", "glm-5.3"))
    monkeypatch.setenv("GLM_API_KEY", "KHOA-ENV")
    assert mdich.DichGLM().key == "KHOA-KET", "có két thì dùng két"

    monkeypatch.setattr(mdich, "_khoa_tu_ket", lambda: ("", ""))
    assert mdich.DichGLM().key == "KHOA-ENV", "két câm thì rơi về env"


def test_ket_hong_khong_giet_ban_kich_ban(monkeypatch):
    """Gateway chết / không có mạng: vẫn mở được bàn kịch bản, chỉ nút Dịch lại
    báo lỗi. Cột tiếng Anh mới là thứ phải sống."""
    from factcheck import dich as mdich

    def _no(): raise RuntimeError("gateway chết")
    monkeypatch.setattr(mdich, "_khoa_tu_ket", _no)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    assert mdich.DichGLM().key == ""


# ------------------------------- citation API --------------------------------
class KiemGia:
    """Bộ kiểm giả — không mạng, không tốn lượt LLM."""

    def __init__(self, ket="dung"):
        self.ket, self.da_kiem = ket, []

    def __call__(self, doan, **kw):
        from factcheck.kiem import KetQua, Nguon, chu_ky

        self.da_kiem.append(doan)
        n = Nguon(url="https://www.cdc.gov/x", ten="CDC", trich="y",
                  song=True, khop=True, luc="16/09/2026 09:00")
        _ = chu_ky
        return KetQua(doan=doan, ket=self.ket, ly_do="lý do", nguon=[n],
                      truy_van="tra gì đó")


@pytest.fixture()
def bo_kiem(tmp_path):
    kho = Kho(tmp_path / "k.db")
    kiem = KiemGia()
    c = TestClient(tao_app(kho, dich=DichGia(), kiem=kiem))
    c.headers.update({"X-Remote-User": "haint"})
    c.post("/api/tap", json={"ma": "SH011", "ten": "x"})
    c.post("/api/tap/SH011/chuong", json={"ma": "H"})
    c.post("/api/tap/SH011/H/nap", json={"text": "The WHI found a higher risk.\nB.\n"})
    return c, kho, kiem


def test_kiem_mot_doan_roi_doc_lai(bo_kiem):
    c, _, kiem = bo_kiem
    r = c.post("/api/tap/SH011/H/kiem", json={"doan": "The WHI found a higher risk."})
    assert r.status_code == 200
    b = r.json()
    assert b["ket"] == "dung" and b["chu_ky"] and b["nguon"][0]["hang"] == 1
    assert kiem.da_kiem == ["The WHI found a higher risk."]
    ds = c.get("/api/tap/SH011/H/citation").json()
    assert len(ds) == 1 and ds[0]["chu_ky"] == b["chu_ky"]


def test_kiem_doan_rong_bi_tu_choi(bo_kiem):
    c, _, _ = bo_kiem
    assert c.post("/api/tap/SH011/H/kiem", json={"doan": "   "}).status_code == 400


def test_chua_khai_ten_thi_khong_duoc_kiem(bo_kiem):
    """Kiểm là tốn tiền — phải biết ai bấm."""
    c, _, _ = bo_kiem
    assert TestClient(c.app).post("/api/tap/SH011/H/kiem",
                                  json={"doan": "x"}).status_code == 401


def test_nguoi_khac_dang_giu_chuong_thi_khong_kiem_duoc(bo_kiem):
    c, _, _ = bo_kiem
    c.post("/api/tap/SH011/H/giu")
    c2 = TestClient(c.app)
    c2.headers.update({"X-Remote-User": "thanhdn"})
    assert c2.post("/api/tap/SH011/H/kiem", json={"doan": "x"}).status_code == 409


def test_bo_kiem_chua_bat_thi_bao_ro(tmp_path):
    kho = Kho(tmp_path / "k.db")
    c = TestClient(tao_app(kho))
    c.headers.update({"X-Remote-User": "haint"})
    c.post("/api/tap", json={"ma": "SH011", "ten": "x"})
    c.post("/api/tap/SH011/chuong", json={"ma": "H"})
    assert c.post("/api/tap/SH011/H/kiem", json={"doan": "x"}).status_code == 503


def test_xoa_the_citation(bo_kiem):
    c, _, _ = bo_kiem
    b = c.post("/api/tap/SH011/H/kiem", json={"doan": "The WHI found a higher risk."}).json()
    assert c.request("DELETE", f"/api/tap/SH011/H/citation/{b['chu_ky']}").status_code == 200
    assert c.get("/api/tap/SH011/H/citation").json() == []
