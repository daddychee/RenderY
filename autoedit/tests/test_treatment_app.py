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

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho


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
    """Treatment là MỘT THƯ MỤC RIÊNG TRONG RenderY (user chốt 18/09) — không phải
    tool tách hẳn. Nó được dùng lại đồ của RenderY, nhưng CHỈ hai thứ đã khai:
    luật tên chương và két khoá. Đụng tới tầng dựng (`web.server`, `offline`,
    `packager`…) là sai: sập bên này không được kéo theo 9118.
    """
    import pathlib
    import re

    goc = pathlib.Path(__file__).resolve().parents[1] / "autoedit" / "treatment"
    cho_phep = ("autoedit.treatment", "autoedit.web.chapters", "autoedit.web.ket_v3")
    xau = []
    for f in goc.glob("*.py"):
        for m in re.findall(r"^\s*(?:from|import)\s+(autoedit[\w.]*)",
                            f.read_text(encoding="utf-8"), re.M):
            if not m.startswith(cho_phep):
                xau.append(f"{f.name}: {m}")
    assert not xau, f"treatment đang với sang tầng dựng: {xau}"


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
    from autoedit.treatment.app import tao_app as _tao

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
    from autoedit.treatment import app as mapp

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
def test_suc_khoe_sau_dung_khuon_cua_cum(bo):
    """`apps.json` khai `suc_khoe` thì PHẢI GIỮ LỜI: gateway đọc `trang_thai` +
    `mo_dun`, khai mà không trả lời được là bảng giám sát báo đỏ."""
    c, _, _ = bo
    b = c.get("/api/suc-khoe").json()
    assert b["trang_thai"] in ("ok", "canh_bao", "loi")
    ten = {m["ten"] for m in b["mo_dun"]}
    assert {"kho", "khoa_llm"} <= ten
    assert all(m["trang_thai"] in ("ok", "canh_bao", "loi") for m in b["mo_dun"])


def test_suc_khoe_bao_CANH_BAO_khi_thieu_khoa(tmp_path, monkeypatch):
    """Thiếu khoá thì tool vẫn mở được (nhập/chia dòng/copy vẫn chạy) — đó là
    CẢNH BÁO, không phải LỖI. Báo đỏ oan thì lần sau không ai nhìn bảng nữa.

    Phải BỊT CẢ HAI đường khoá: máy chạy test này có két thật của cụm, không bịt
    thì nó tìm ra khoá và test "thiếu khoá" xanh vì lý do sai.
    """
    from autoedit.treatment import dich as mdich

    monkeypatch.setattr(mdich, "doc_ket_viec", lambda: {})

    kho = Kho(tmp_path / "k.db")
    c = TestClient(tao_app(kho))
    b = c.get("/api/suc-khoe").json()
    assert b["trang_thai"] == "canh_bao"
    loi = [m for m in b["mo_dun"] if m["trang_thai"] == "loi"]
    assert not loi, loi


def test_suc_khoe_bao_LOI_khi_kho_hong(tmp_path):
    kho = Kho(tmp_path / "k.db")
    kho.cn.close()                      # mô phỏng kho không đọc được
    c = TestClient(tao_app(kho))
    b = c.get("/api/suc-khoe").json()
    assert b["trang_thai"] == "loi"
    assert any(m["ten"] == "kho" and m["trang_thai"] == "loi" for m in b["mo_dun"])


# ------------------- dịch theo LÔ (đo thật 23/09 trên SE001) -----------------
class DichDem:
    """Đếm số lượt gọi và kích thước từng lô."""

    def __init__(self, hong_o_lo: int = -1):
        self.lo: list[int] = []
        self.hong_o_lo = hong_o_lo

    def dich(self, cau):
        self.lo.append(len(cau))
        if len(self.lo) - 1 == self.hong_o_lo:
            raise RuntimeError("claude-sonnet-5 trả về không đọc được: Expecting ','")
        return ["VI:" + c for c in cau]


def _chuong_dai(c, so_dong=20):
    c.post("/api/tap/SH011/chuong", json={"ma": "C9"})
    c.post("/api/tap/SH011/C9/nap",
           json={"text": "\n".join(f"Line {i} of the script." for i in range(so_dong))})


def test_dich_chia_LO_chu_khong_goi_mot_phat_ca_chuong(tmp_path):
    """Đo thật 23/09 trên SE001: chương 20 dòng -> Claude trả JSON CỤT
    ("Expecting ',' delimiter") và cả chương mất trắng. Chương ngắn thì qua.
    Chia lô nhỏ thì mỗi lượt JSON ngắn, ít cụt hơn hẳn."""
    kho = Kho(tmp_path / "k.db")
    dem = DichDem()
    c = TestClient(tao_app(kho, dich=dem))
    c.headers.update({"X-Remote-User": "haint"})
    c.post("/api/tap", json={"ma": "SH011", "ten": "x"})
    _chuong_dai(c)
    assert c.post("/api/tap/SH011/C9/dich").json()["dich"] == 20
    assert len(dem.lo) > 1, "phải chia lô"
    assert max(dem.lo) <= 10, f"lô quá to: {dem.lo}"


def test_lo_hong_thi_GIU_phan_da_dich(tmp_path):
    """Hỏng lô thứ hai: 8 dòng lô đầu phải còn, không mất trắng cả chương."""
    kho = Kho(tmp_path / "k.db")
    c = TestClient(tao_app(kho, dich=DichDem(hong_o_lo=1)))
    c.headers.update({"X-Remote-User": "haint"})
    c.post("/api/tap", json={"ma": "SH011", "ten": "x"})
    _chuong_dai(c)
    b = c.post("/api/tap/SH011/C9/dich").json()
    assert 0 < b["dich"] < 20
    assert "loi" in b and b["loi"], "phải nói rõ vì sao dừng"
    d = c.get("/api/tap/SH011/C9").json()["dong"]
    assert sum(1 for x in d if x["vi"]) == b["dich"], "phần đã dịch phải được lưu"


def test_bam_lai_thi_dich_tiep_phan_con_thieu(tmp_path):
    kho = Kho(tmp_path / "k.db")
    hong = DichDem(hong_o_lo=1)
    c = TestClient(tao_app(kho, dich=hong))
    c.headers.update({"X-Remote-User": "haint"})
    c.post("/api/tap", json={"ma": "SH011", "ten": "x"})
    _chuong_dai(c)
    xong = c.post("/api/tap/SH011/C9/dich").json()["dich"]
    c2 = TestClient(tao_app(kho, dich=DichDem()))
    c2.headers.update({"X-Remote-User": "haint"})
    assert c2.post("/api/tap/SH011/C9/dich").json()["dich"] == 20 - xong
    d = c2.get("/api/tap/SH011/C9").json()["dong"]
    assert all(x["vi"] for x in d)
