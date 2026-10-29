"""Nút "Gen toàn bộ asset" (user chốt 28/10: "làm giống padoma") + số dư credit.

Một lần bấm: LLM tìm đồ vật (luật bảng tài sản Padoma), LLM viết mô tả tiếng Anh
còn thiếu, rồi vẽ mọi asset chưa có ảnh — bộ đồ phụ sửa từ ảnh cận của bản gốc
(Padoma L2 mục 7 "PHIÊN BẢN NGƯỜI"). Chạy nền ở máy chủ; đồ giả, không mạng.
"""

from __future__ import annotations

import threading
import time

from fastapi.testclient import TestClient

from autoedit.treatment import app as mapp
from autoedit.treatment import tai_san as mtai_san
from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho
from test_treatment_drama_api import KyThuatGia, SinhAssetGia, VeAnhGia, VeVideoGia, _clip, _tap_drama


class KyThuatDoVat(KyThuatGia):
    """LLM giả lượt tìm đồ vật: trùng tên khác hoa thường thì gộp, mã clip lạ thì
    bỏ, mô tả chữ Việt thì bỏ."""

    def __init__(self, tra=None, ra=None):
        super().__init__()
        self.do_vat, self.tra_dv = [], tra
        self.ra, self.tra_ra = [], ra

    def tim_do_vat(self, than):
        self.do_vat.append(than)
        if self.tra_dv is not None:
            return self.tra_dv(than)
        if "P001" in than:
            return {"do_vat": [
                {"ten": "hộp nhẫn", "chu": "a small hinged ring box in deep red velvet", "clip": ["P001", "P999"]},
                {"ten": "Hộp Nhẫn", "chu": "duplicate", "clip": ["P002"]},
                {"ten": "giấy", "chu": "tờ giấy cũ", "clip": ["P001"]}]}
        return {"do_vat": []}

    def ra_do_vat(self, than):
        """Lượt rà cả tập: mặc định không gộp, không sửa."""
        self.ra.append(than)
        return self.tra_ra(than) if self.tra_ra else {"nhom": [], "sua": {}}


def _bo(tmp_path, kt=None, va=None, vv=None, sa=None):
    kho = Kho(tmp_path / "kho" / "k.db")
    app = tao_app(kho, ky_thuat=kt or KyThuatDoVat(), ve_video=vv or VeVideoGia(),
                  ve_anh=va or VeAnhGia(), sinh_asset=sa or SinhAssetGia())
    c = TestClient(app)
    c.headers.update({"X-Remote-User": "minh", "X-Remote-Actions": "sua"})
    return kho, c


def _cho_xong(c, tap="D1", giay=10):
    het = time.time() + giay
    while time.time() < het:
        v = c.get(f"/api/tap/{tap}/so/tat-ca").json()["viec"]
        if v and not v["chay"]:
            return v
        time.sleep(0.05)
    raise AssertionError("việc nền không xong")


# ═══════ kế hoạch ═══════════════════════════════════════════════════════════════
def test_ke_hoach_dem_dung_viec_va_credit_truoc_khi_bam(tmp_path):
    _, c = _bo(tmp_path)
    _tap_drama(c)
    r = c.get("/api/tap/D1/so/tat-ca").json()
    # nv01, nv02 gốc · nv01_d2 bộ đồ phụ · noi01, noi02 chưa có mô tả tiếng Anh
    assert r["ke_hoach"] == {"do_vat": True, "mo_ta": 2, "nhan_vat": 2, "phu": 1, "noi": 2, "dao_cu": 0,
                             "anh": 8, "credit": 2 * 9 + 10 + 2 * 4, "credit_du_phong": 8 * 4,
                             "phut": r["ke_hoach"]["phut"]}
    assert r["ke_hoach"]["phut"] >= 1
    assert r["viec"] is None and r["model"]["id"] == "gpt-image-2" and r["model"]["du_phong"] == "GEM_PIX_2"


# ═══════ chạy cả bộ ═════════════════════════════════════════════════════════════
def test_mot_lan_bam_tim_do_vat_viet_mo_ta_roi_ve_het(tmp_path):
    kt, va, sa = KyThuatDoVat(), VeAnhGia(), SinhAssetGia()
    kho, c = _bo(tmp_path, kt=kt, va=va, sa=sa)
    _tap_drama(c)
    r = c.post("/api/tap/D1/so/tat-ca", json={})
    assert r.status_code == 200, r.text
    v = _cho_xong(c)
    assert v["loi"] == [] and v["buoc"] == "xong" and v["nguoi"] == "minh"
    assert v["do_vat_moi"] == 1 and v["xong"] == v["tong"] == 6      # tiến độ đếm ASSET: 5 + hộp nhẫn
    # Mỗi chương một lượt LLM, chữ clip đi kèm mã clip.
    assert len(kt.do_vat) == 2 and "P001" in kt.do_vat[0] and "Hình:" in kt.do_vat[0]
    so = {x["ma"]: x for x in kho.ds_so("D1")}
    hop = so["do01"]
    assert hop["loai"] == "dao_cu" and hop["ten"] == "hộp nhẫn" and "red velvet" in hop["chu"]
    assert hop["yc"] == "hộp nhẫn", "thẻ asset không báo 'chưa có yêu cầu'"
    assert "pure white seamless background" in hop["pr"]
    assert not any(x["loai"] == "dao_cu" and x["ma"] != "do01" for x in so.values()), "trùng tên gộp, chữ Việt bỏ"
    assert "do01" in _clip(kho, j=0)["ts"] and "do01" in _clip(kho, j=1)["ts"], "gộp clip của mục trùng tên"
    assert "do01" not in _clip(kho, ch="C2")["ts"]
    # Nơi chốn có mô tả tiếng Anh nhờ LLM; nhân vật drama giữ cụm kịch bản.
    assert {m["ma"] for m in sa.goi} == {"noi01", "noi02"}
    assert "hospital room" in so["noi01"]["chu"] and "No people" in so["noi01"]["pr"]
    assert all(kho.ref_dang_co("D1", m) for m in ("nv01", "nv01_d2", "nv02", "noi01", "noi02", "do01"))
    assert all(g["model"] == "gpt-image-2" for g in va.goi)


def test_bo_do_phu_ve_sau_ban_goc_va_sua_tu_anh_can_cua_ban_goc(tmp_path):
    va = VeAnhGia()
    kho, c = _bo(tmp_path, va=va)
    _tap_drama(c)
    c.post("/api/tap/D1/so/tat-ca", json={})
    _cho_xong(c)
    dich = [g["dich"].name for g in va.goi]
    can_goc = dich.index("nv01__can.png")
    can_phu = dich.index("nv01_d2__can.png")
    assert can_goc < can_phu
    g = va.goi[can_phu]
    assert [p.name for p in g["ref"]] == ["nv01__can.png"]
    assert g["prompt"].startswith(mtai_san.PHIEN_BAN) and "grey hoodie" in g["prompt"]
    assert not va.goi[can_goc]["ref"], "bản gốc vẽ mới từ chữ"


def test_nut_ve_le_bo_do_phu_chua_co_mat_ban_goc_thi_chan(tmp_path):
    _, c = _bo(tmp_path)
    _tap_drama(c)
    r = c.post("/api/tap/D1/so/nv01_d2/ref-sinh")
    assert r.status_code == 400 and "nv01" in r.json()["detail"]
    assert c.post("/api/tap/D1/so/nv01/ref-sinh").status_code == 200
    assert c.post("/api/tap/D1/so/nv01_d2/ref-sinh").status_code == 200


def test_mot_asset_ve_hong_khong_giet_ca_bo_va_bam_lai_chi_lam_phan_thieu(tmp_path):
    class VeHong(VeAnhGia):
        def gen_anh(self, prompt, dich, ref=None, model=None, ti_le=None):
            if dich.name.startswith("noi02"):
                raise RuntimeError("503 model_maintenance")
            return super().gen_anh(prompt, dich, ref=ref, model=model, ti_le=ti_le)

    kt = KyThuatDoVat()
    kho, c = _bo(tmp_path, kt=kt, va=VeHong())
    _tap_drama(c)
    c.post("/api/tap/D1/so/tat-ca", json={})
    v = _cho_xong(c)
    assert [(x["ma"], "model_maintenance" in x["loi"]) for x in v["loi"]] == [("noi02", True)]
    assert v["xong"] == v["tong"] == 6 and kho.ref_dang_co("D1", "nv02")
    kh = c.get("/api/tap/D1/so/tat-ca").json()["ke_hoach"]
    assert (kh["do_vat"], kh["mo_ta"], kh["anh"], kh["noi"]) == (False, 0, 1, 1), "đã có đồ vật: không tìm lại"
    va = VeAnhGia()
    kho2 = kho
    c2 = TestClient(tao_app(kho2, ky_thuat=kt, ve_video=VeVideoGia(), ve_anh=va, sinh_asset=SinhAssetGia()))
    c2.headers.update({"X-Remote-User": "minh", "X-Remote-Actions": "sua"})
    c2.post("/api/tap/D1/so/tat-ca", json={})
    _cho_xong(c2)
    assert [g["dich"].name for g in va.goi] == ["noi02.png"] and len(kt.do_vat) == 2
    assert c2.post("/api/tap/D1/so/tat-ca", json={}).status_code == 400, "không còn gì để làm"


def test_dang_chay_thi_409_nguoi_xem_thi_403_model_la_thi_400(tmp_path):
    cho = threading.Event()

    class VeCho(VeAnhGia):
        def gen_anh(self, prompt, dich, ref=None, model=None, ti_le=None):
            cho.wait(5)
            return super().gen_anh(prompt, dich, ref=ref, model=model, ti_le=ti_le)

    kho, c = _bo(tmp_path, va=VeCho())
    _tap_drama(c)
    assert c.post("/api/tap/D1/so/tat-ca", json={"model": "Omni-Flash"}).status_code == 400
    assert c.post("/api/tap/D1/so/tat-ca", json={}).status_code == 200
    r = c.post("/api/tap/D1/so/tat-ca", json={})
    assert r.status_code == 409 and "minh" in r.json()["detail"]
    xem = TestClient(c.app)
    xem.headers.update({"X-Remote-User": "an", "X-Remote-Actions": ""})
    assert xem.post("/api/tap/D1/so/tat-ca", json={}).status_code == 403
    v = xem.get("/api/tap/D1/so/tat-ca").json()["viec"]
    assert v["chay"] is True, "người khác mở trang vẫn thấy tiến độ"
    # Trang ghi CẢ sổ bằng bản đang cầm: ghi lúc này là xoá đồ vật / mô tả máy vừa viết.
    r = c.put("/api/tap/D1/so", json={"so": kho.ds_so("D1")[:1]})
    assert r.status_code == 409 and "đợi xong" in r.json()["detail"]
    cho.set()
    _cho_xong(c)


def test_model_du_phong_nano_banana_di_tu_trang(tmp_path):
    va = VeAnhGia()
    _, c = _bo(tmp_path, va=va)
    _tap_drama(c)
    assert c.post("/api/tap/D1/so/tat-ca", json={"model": "GEM_PIX_2"}).status_code == 200
    assert _cho_xong(c)["model"] == "GEM_PIX_2"
    assert va.goi and all(g["model"] == "GEM_PIX_2" for g in va.goi)


def test_tap_cu_khuon_cu_khong_co_nut_nay(tmp_path):
    kho, c = _bo(tmp_path)
    kho.tao_tap("SE001", "cũ")
    kho.luu_so("SE001", [{"ma": "a", "loai": "nhan_vat", "ten": "A", "chu": "x", "pr": "OLD"}])
    r = c.post("/api/tap/SE001/so/tat-ca", json={})
    assert r.status_code == 400 and "từng asset" in r.json()["detail"]


def test_do_vat_khong_gan_qua_tran_anh_moi_clip(tmp_path):
    def nhieu(than):
        if "P001" not in than:
            return {"do_vat": []}
        return {"do_vat": [{"ten": f"đồ {k}", "chu": f"object number {k}", "clip": ["P001"]} for k in range(12)]}

    kho, c = _bo(tmp_path, kt=KyThuatDoVat(tra=nhieu))
    _tap_drama(c)
    c.post("/api/tap/D1/so/tat-ca", json={})
    _cho_xong(c)
    assert len(_clip(kho)["ts"]) == 10, "Grok nhận tối đa 10 ảnh tham chiếu"


def test_lenh_tim_do_vat_mang_luat_padoma():
    lenh = mapp._LENH_DO_VAT
    for chu in ("LẶP LẠI", "CẦN NHÌN RÕ", "NGUYÊN VĂN", "nền trắng", "THẤY RÕ"):
        assert chu in lenh, chu


# ═══════ số dư credit ═══════════════════════════════════════════════════════════
def test_so_du_nho_60_giay_moi_thi_hoi_lai_sau_10_giay(tmp_path, monkeypatch):
    class Dem:
        def __init__(self, so):
            self.so, self.hoi = so, 0

        @property
        def credit(self):
            self.hoi += 1
            return self.so

    va, vv = Dem(500), Dem(7888)
    kho = Kho(tmp_path / "k.db")
    c = TestClient(tao_app(kho, ve_anh=va, ve_video=vv))
    gio = [1000.0]
    monkeypatch.setattr(mapp, "_gio", lambda: gio[0])
    assert c.get("/api/so-du").json() == {"anh": 500, "video": 7888, "chung": False}
    gio[0] += 30
    vv.so = 7780
    assert c.get("/api/so-du").json()["video"] == 7888 and vv.hoi == 1, "trong 60 s: không hỏi Seedvis"
    gio[0] += 5
    assert c.get("/api/so-du?moi=1").json()["video"] == 7780 and vv.hoi == 2, "vừa gen xong: hỏi lại"
    gio[0] += 3
    c.get("/api/so-du?moi=1")
    assert vv.hoi == 2, "ép hỏi cũng không quá 10 s một lần"
    gio[0] += 61
    c.get("/api/so-du")
    assert vv.hoi == 3


def test_so_du_khong_phai_seedvis_thi_null(tmp_path):
    c = TestClient(tao_app(Kho(tmp_path / "k.db"), ve_anh=VeAnhGia(), ve_video=VeVideoGia()))
    assert c.get("/api/so-du").json() == {"anh": None, "video": None, "chung": True}


# ═══════ model vẽ asset theo General (user báo 28/10: "đổi model trong General mà tool vẫn GPT2") ═══
class VeAnhKet(VeAnhGia):
    """Bộ vẽ có model Owner cấp ở General › API Keys › Treatment › gen_canh."""

    def __init__(self, model_ket):
        super().__init__()
        self.model_ket = model_ket


def test_ve_asset_theo_model_general_khong_ghi_cung_gpt(tmp_path):
    va = VeAnhKet("GEM_PIX_2")
    _, c = _bo(tmp_path, va=va)
    _tap_drama(c)
    assert c.post("/api/tap/D1/so/nv01/ref-sinh").status_code == 200
    assert [g["model"] for g in va.goi] == ["GEM_PIX_2", "GEM_PIX_2"]


def test_ve_asset_tap_chon_model_thi_de_general(tmp_path):
    va = VeAnhKet("GEM_PIX_2")
    _, c = _bo(tmp_path, va=va)
    _tap_drama(c)
    assert c.put("/api/tap/D1/mo-hinh", json={"anh": "NARWHAL", "video": ""}).status_code == 200
    c.post("/api/tap/D1/so/nv01/ref-sinh")
    assert {g["model"] for g in va.goi} == {"NARWHAL"}


def test_gen_toan_bo_theo_model_general_credit_theo_model_do(tmp_path):
    va = VeAnhKet("GEM_PIX_2")
    _, c = _bo(tmp_path, va=va)
    _tap_drama(c)
    r = c.get("/api/tap/D1/so/tat-ca").json()
    assert r["model"]["id"] == "GEM_PIX_2" and r["model"]["du_phong"] == "gpt-image-2"
    assert r["ke_hoach"]["credit"] == 8 * 4, "Nano Banana Pro 4 credit mỗi ảnh"
    assert r["ke_hoach"]["credit_du_phong"] == 2 * 9 + 10 + 2 * 4, "dự phòng GPT: 4 tạo mới, 5 sửa"
    assert c.post("/api/tap/D1/so/tat-ca", json={}).status_code == 200
    _cho_xong(c)
    assert va.goi and {g["model"] for g in va.goi} == {"GEM_PIX_2"}


# ═══════ đồ vật có ẢNH người (user báo 29/10 DM002: thẻ nhân viên của Richard da đen vẽ ra
# người da trắng, báo đăng ảnh Nia ra người khác) ══════════════════════════════════════════
def _them_do(kho, *do):
    kho.luu_so("D1", kho.ds_so("D1") + [{"ma": m, "loai": "dao_cu", "ten": t, "chu": chu, "yc": t}
                                         for m, t, chu in do])


def test_ten_nhan_vat_trong_mo_ta_ngoai_ngoac_kep():
    ds = ["Tasha", "Marcus", "Mr. Whitaker"]
    assert mtai_san.nguoi_trong_chu('A staff badge with a small photo of Marcus and the name "MARCUS"', ds) == ["Marcus"]
    assert mtai_san.nguoi_trong_chu("a name tag 'TASHA', a card reading \"Tasha\"", ds) == [], "chữ IN trên đồ"
    assert mtai_san.nguoi_trong_chu("two photos: Mr. Whitaker beside Tasha, and Tasha's wedding portrait",
                                    ds) == ["Mr. Whitaker", "Tasha"], "đúng thứ tự xuất hiện, một lần mỗi người"
    assert mtai_san.nguoi_trong_chu("a marcus brand pen, a Marcusville map", ds) == [], "đúng chữ hoa, đúng trọn tên"


def test_ve_do_vat_co_anh_nhan_vat_gui_kem_mat_nguoi_do(tmp_path):
    va = VeAnhGia()
    kho, c = _bo(tmp_path, va=va)
    _tap_drama(c)
    _them_do(kho, ("do01", "Thẻ nhân viên", 'A laminated staff ID badge with a small photo of Marcus above the '
                   'name "MARCUS", edges scuffed.'))
    r = c.post("/api/tap/D1/so/do01/ref-sinh")
    assert r.status_code == 400 and "Marcus" in r.json()["detail"], "chưa có mặt Marcus thì vẽ là bịa người"
    assert c.post("/api/tap/D1/so/nv02/ref-sinh").status_code == 200
    assert c.post("/api/tap/D1/so/do01/ref-sinh").status_code == 200
    g = va.goi[-1]
    assert g["dich"].name == "do01.png" and [p.name for p in g["ref"]] == ["nv02__can.png"]
    assert mtai_san.ANH_NGUOI.format(i=1, ten="Marcus") in g["prompt"] and "pure white" in g["prompt"]
    # Đồ vật không có ảnh người: vẫn vẽ từ chữ, không ref.
    _them_do(kho, ("do02", "Hộp nhẫn", "a small hinged ring box in deep red velvet"))
    c.post("/api/tap/D1/so/do02/ref-sinh")
    assert va.goi[-1]["ref"] == []


def test_gen_toan_bo_ve_do_vat_co_nguoi_sau_mat_nguoi_do_va_tinh_gia_sua(tmp_path):
    def khung(than):
        if "P001" not in than:
            return {"do_vat": []}
        return {"do_vat": [{"ten": "khung ảnh", "chu": "a silver photo frame holding a photo of Tasha and Marcus "
                                                       "smiling, upright", "clip": ["P001"]}]}

    kt, va = KyThuatDoVat(tra=khung), VeAnhGia()
    kho, c = _bo(tmp_path, kt=kt, va=va)
    _tap_drama(c)
    assert "NHÂN VẬT" in mapp._LENH_DO_VAT
    c.post("/api/tap/D1/so/tat-ca", json={})
    v = _cho_xong(c)
    assert v["loi"] == []
    dau = kt.do_vat[0].split("P001")[0]
    assert "Tasha" in dau and "Marcus" in dau, "LLM biết tên nhân vật trước chữ clip"
    dich = [g["dich"].name for g in va.goi]
    k = dich.index("do01.png")
    assert k > max(dich.index("nv01__can.png"), dich.index("nv02__can.png"), dich.index("nv01_d2__can.png"))
    assert [p.name for p in va.goi[k]["ref"]] == ["nv01__can.png", "nv02__can.png"]
    # Kế hoạch: ảnh có người là ảnh SỬA (GPT 5 credit), không phải tạo mới (4).
    kho.xoa_ref("D1", "do01")
    assert c.get("/api/tap/D1/so/tat-ca").json()["ke_hoach"]["credit"] == 5


# ═══════ gộp đồ vật trùng cả tập (user báo 29/10 DM002: "Bàn cờ" / "Bàn cờ gỗ", 6 loại "đơn đào tạo") ═══
def test_gen_toan_bo_ra_ca_tap_gop_do_vat_trung_va_sua_mo_ta(tmp_path):
    def hai_chuong(than):
        if "P001" in than:
            return {"do_vat": [{"ten": "bàn cờ", "chu": "a wooden chess board with carved pieces", "clip": ["P001"]},
                               {"ten": "khung ảnh", "chu": "a silver photo frame with a smiling blonde woman",
                                "clip": ["P002"]}]}
        return {"do_vat": [{"ten": "bàn cờ gỗ", "chu": "a worn wooden chessboard", "clip": ["P003"]}]}

    def ra(than):
        return {"nhom": [[0, 2], [5, 1], [1, 1]],          # [5, 1] ngoài tầm, [1, 1] lặp: bỏ
                "sua": {"1": "a silver photo frame holding a photo of Tasha smiling beside Marcus",
                        "0": "tờ giấy chữ Việt", "9": "out of range"}}

    kt = KyThuatDoVat(tra=hai_chuong, ra=ra)
    kho, c = _bo(tmp_path, kt=kt)
    _tap_drama(c)
    c.post("/api/tap/D1/so/tat-ca", json={})
    v = _cho_xong(c)
    assert v["loi"] == [] and v["do_vat_moi"] == 2
    assert len(kt.ra) == 1 and "bàn cờ gỗ" in kt.ra[0] and "Tasha" in kt.ra[0] and "P003" in kt.ra[0]
    do = {x["ten"]: x for x in kho.ds_so("D1") if x["loai"] == "dao_cu"}
    assert set(do) == {"bàn cờ", "khung ảnh"}
    assert do["bàn cờ"]["chu"] == "a wooden chess board with carved pieces", "mô tả chữ Việt không nhận"
    assert "photo of Tasha" in do["khung ảnh"]["chu"] and "photo of Tasha" in do["khung ảnh"]["pr"]
    ban = do["bàn cờ"]["ma"]
    assert ban in _clip(kho)["ts"] and ban in _clip(kho, ch="C2")["ts"], "clip của mục bị gộp về mục giữ"


def test_ra_do_vat_qua_gio_thi_hoi_lai_mot_lan_hong_nua_thi_giu_danh_sach(tmp_path):
    def hai(than):
        if "P001" in than:
            return {"do_vat": [{"ten": "bàn cờ", "chu": "a wooden chess board", "clip": ["P001"]}]}
        return {"do_vat": [{"ten": "bàn cờ gỗ", "chu": "a worn wooden chessboard", "clip": ["P003"]}]}

    lan = []

    def ra(than):                   # DM002 29/10: hai trong bốn lượt quá 180 giây
        lan.append(1)
        if len(lan) == 1:
            raise RuntimeError("Read timed out. (read timeout=180)")
        return {"nhom": [[0, 1]], "sua": {}}

    kho, c = _bo(tmp_path, kt=KyThuatDoVat(tra=hai, ra=ra))
    _tap_drama(c)
    c.post("/api/tap/D1/so/tat-ca", json={})
    v = _cho_xong(c)
    assert len(lan) == 2 and v["loi"] == [] and v["do_vat_moi"] == 1

    def luon_hong(than):
        raise RuntimeError("Read timed out. (read timeout=180)")

    kho, c = _bo(tmp_path / "b", kt=KyThuatDoVat(tra=hai, ra=luon_hong))
    _tap_drama(c)
    c.post("/api/tap/D1/so/tat-ca", json={})
    v = _cho_xong(c)
    assert v["do_vat_moi"] == 2, "rà hỏng hẳn: vẫn lưu đồ vật, chỉ là chưa gộp"
    assert [x["ten"] for x in v["loi"]] == ["Gộp đồ vật trùng"]


def test_lenh_ra_do_vat_chi_gop_cung_mot_vat():
    lenh = mapp._LENH_RA_DO_VAT
    for chu in ("CÙNG MỘT", "KHÔNG gộp", '"nhom"', '"sua"', "ngoặc kép"):
        assert chu in lenh, chu


def test_ra_do_vat_tap_dang_co_gop_chuyen_ma_clip_va_xoa_anh_sai(tmp_path):
    def ra(than):
        return {"nhom": [[0, 1]], "sua": {"2": "a silver photo frame holding a photo of Tasha"}}

    kt = KyThuatDoVat(ra=ra)
    kho, c = _bo(tmp_path, kt=kt)
    _tap_drama(c)
    _them_do(kho, ("do01", "Bàn cờ", "a wooden chess board"), ("do02", "Bàn cờ gỗ", "a worn wooden chessboard"),
             ("do03", "Khung ảnh", "a silver photo frame with a smiling blonde woman"))
    for ch, ts in (("C1", ["do01"]), ("C2", ["do02", "do03"])):
        r = c.patch(f"/api/tap/D1/{ch}/canh/{_clip(kho, ch=ch)['id']}", json={"truong": {"ts": ts}})
        assert r.status_code == 200, r.text
    for m in ("nv01", "do01", "do02", "do03"):
        assert c.post(f"/api/tap/D1/so/{m}/ref-sinh").status_code == 200
    xem = TestClient(c.app)
    xem.headers.update({"X-Remote-User": "an", "X-Remote-Actions": ""})
    assert xem.post("/api/tap/D1/so/ra-do-vat").status_code == 403
    r = c.post("/api/tap/D1/so/ra-do-vat")
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "gop": [["do01", "do02"]], "sua": ["do03"], "xoa": ["do02"]}
    assert "P003" in kt.ra[0] and "Bàn cờ gỗ" in kt.ra[0]
    so = {x["ma"]: x for x in kho.ds_so("D1")}
    assert "do02" not in so and kho.ref_dang_co("D1", "do02") is None
    assert _clip(kho, ch="C2")["ts"] == ["do01", "do03"]
    assert "photo of Tasha" in so["do03"]["chu"] and "photo of Tasha" in so["do03"]["pr"]
    assert kho.ref_dang_co("D1", "do03") is None, "mô tả đổi: ảnh cũ vẽ sai người, Gen toàn bộ asset vẽ lại"
    assert kho.ref_dang_co("D1", "do01") is not None


def test_ra_do_vat_khi_dang_gen_toan_bo_thi_409(tmp_path):
    cho = threading.Event()

    class VeCho(VeAnhGia):
        def gen_anh(self, prompt, dich, ref=None, model=None, ti_le=None):
            cho.wait(5)
            return super().gen_anh(prompt, dich, ref=ref, model=model, ti_le=ti_le)

    kho, c = _bo(tmp_path, va=VeCho())
    _tap_drama(c)
    _them_do(kho, ("do01", "Bàn cờ", "a wooden chess board"))
    c.post("/api/tap/D1/so/tat-ca", json={})
    assert c.post("/api/tap/D1/so/ra-do-vat").status_code == 409
    cho.set()
    _cho_xong(c)
