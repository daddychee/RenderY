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

    def __init__(self, tra=None):
        super().__init__()
        self.do_vat, self.tra_dv = [], tra

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
