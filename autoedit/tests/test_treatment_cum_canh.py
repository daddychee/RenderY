"""Cụm cảnh cùng phim trường (user chốt 29/10): cảnh liền nhau, cùng nơi, cùng buổi là MỘT cuộc
đang diễn ra — "nếu có người xuất hiện trong một cuộc trò chuyện có sẵn thì vị trí của những người
xuất hiện trước phải được đảm bảo". Đo DM002 C1: C003 vẽ độc lập ra căn phòng khác C002.

Cảnh sau trong cụm: LLM thấy bố cục cảnh trước, Python ép người cũ giữ chỗ; ảnh dàn cảnh SỬA từ
ảnh cảnh trước đã duyệt (cùng đội hình thì dùng lại nguyên ảnh). Đồ giả, không mạng.
"""

from __future__ import annotations

import pathlib

import autoedit.treatment.app as mapp
from autoedit.treatment import drama as md
from test_treatment_chay_chuong import HAI_CANH, TAM, _cho_xong, URL as URL_CHAY
from test_treatment_drama_api import VeAnhGia, _bo, _ve_du_ref
from test_treatment_drama_shot_api import KyThuatBoCuc

C2_CU = "## C002 · bếp nhà Tasha · trưa · N02"
CUM = HAI_CANH.replace(C2_CU, "## C002 · phòng VIP bệnh viện · sáng · N02")       # C001 + Ruth vào
CUM_CUNG_NGUOI = CUM.replace("Tasha, Marcus, Ruth", "Tasha, Marcus").replace("ba người", "hai người")


class KtCum(KyThuatBoCuc):
    """Cảnh C002 LLM giả cố tình xếp SAI chỗ người cũ (đảo trái/phải, đổi phông, đổi hàng)."""

    def drama_canh(self, than):
        if not than.startswith("CẢNH: C002"):
            return super().drama_canh(than)         # lớp cha tự ghi `canh`
        self.canh.append(than)
        return {"look": "Soft window light.", "truc": "Marcus left, Ruth centre, Tasha right.", "nen": "monitor beeps",
                "tieng": {"Ruth": "Ruth's voice: a woman of about 75."},
                "ben": {"Tasha": "phai", "Marcus": "trai", "Ruth": "giua"}, "hang": ["Marcus", "Ruth", "Tasha"],
                "phong": {"Tasha": "the bed", "Marcus": "the door", "Ruth": "the tall window"},
                "vi_tri": {"Ruth": "in the armchair at the foot of the bed"},
                "cho": "Ruth sits in the armchair.", "dan": "Wide shot from the door side."}


def _bo3(tmp_path, kich_ban=CUM, va=None):
    kt = KtCum()
    kho, c = _bo(tmp_path, kt=kt, va=va or VeAnhGia())
    assert c.post("/api/tap", json={"ma": "D1", "ten": "Hộp nhẫn", "loai": "drama"}).status_code == 200
    r = c.post("/api/tap/D1/drama", json={"text": kich_ban})
    assert r.status_code == 200, r.text
    _ve_du_ref(kho, TAM)
    return kho, c, kt


def _bd_va_prompt(c, *dong):
    for i in dong:
        assert c.post(f"/api/tap/D1/C1/dong/{i}/breakdown").status_code == 200
    for i in dong:
        r = c.post(f"/api/tap/D1/C1/dong/{i}/prompt-drama")
        assert r.status_code == 200, r.text


def _pd(kho, i):
    return md.doc_pd(kho.doc("D1", "C1")["dong"][i]["canh"][0]["pd"])


def _dan(c, i):
    return c.get(f"/api/tap/D1/C1/dong/{i}/dan-canh").json()


def test_dung_code_cua_cay_dang_test():
    goc = pathlib.Path(__file__).resolve().parents[1]
    assert pathlib.Path(mapp.__file__).resolve().is_relative_to(goc), mapp.__file__


def test_giu_cho_cu_ep_ben_vi_tri_phong_va_thu_tu_hang():
    cu = {"ben": {"Tasha": "trai", "Marcus": "phai"}, "hang": ["Tasha", "Marcus"],
          "vi_tri": {"Tasha": "by the window"}, "phong": {"tasha": "the blinds", "Marcus": "the wall"}}
    moi = {"ben": {"Tasha": "phai", "Marcus": "trai", "Ruth": "giua"}, "hang": ["Marcus", "Ruth", "Tasha"],
           "vi_tri": {"Ruth": "in the armchair"}, "phong": {"Tasha": "the bed", "Ruth": "the window"}}
    ra = md.giu_cho_cu(moi, cu, ["Tasha", "Marcus"])
    assert ra["ben"] == {"Tasha": "trai", "Marcus": "phai", "Ruth": "giua"}
    assert ra["hang"] == ["Tasha", "Ruth", "Marcus"], "người cũ giữ thứ tự cũ, người mới giữ chỗ LLM chèn"
    assert ra["vi_tri"] == {"Ruth": "in the armchair", "Tasha": "by the window"}
    assert ra["phong"] == {"Ruth": "the window", "Tasha": "the blinds", "Marcus": "the wall"}
    assert md.giu_cho_cu({"hang": ["Ruth"]}, cu, ["Marcus"])["hang"] == ["Ruth", "Marcus"], "LLM quên người cũ"


def test_prompt_dan_noi_giu_phong_giu_nguoi_cu_them_moi_bo_nguoi_roi():
    nguoi = [{"ten": "Tasha", "chu": "woman 28"}, {"ten": "Ruth · dạng 2", "chu": "woman 75."}]
    pd = {"vi_tri": {"Ruth": "in the armchair at the foot of the bed"}, "phong": {"Ruth": "the tall window"},
          "look": "Evening lamp light."}
    p = md.prompt_dan_noi(pd, nguoi, ["Tasha", "Marcus"], {"look": "Soft window light."})
    assert p.startswith("Image 1 is the master wide shot of this same room a few moments earlier.")
    assert "Image 2 is a" in p and "Image 3 is a" in p and "Image 4" not in p
    assert "Tasha stays exactly where they are in Image 1" in p
    assert "Marcus has left: remove Marcus" in p
    assert "Add Ruth in the armchair at the foot of the bed. Behind Ruth: the tall window." in p
    assert "Exactly one Tasha and one Ruth, nobody else." in p
    assert "Light now: Evening lamp light." in p
    assert "Light now" not in md.prompt_dan_noi(dict(pd, look="Soft window light."), nguoi, ["Tasha"],
                                                {"look": "Soft window light."})


def test_cum_la_canh_lien_nhau_cung_noi_cung_buoi(tmp_path):
    kho, c, _ = _bo3(tmp_path)
    assert _dan(c, 0)["truoc"] is None
    assert _dan(c, 1)["truoc"]["ten"].startswith("C001 · phòng VIP bệnh viện")
    kho2, c2, _ = _bo3(tmp_path / "khac", kich_ban=HAI_CANH)            # C002 ở bếp: cảnh mới
    assert _dan(c2, 1)["truoc"] is None
    kho3, c3, _ = _bo3(tmp_path / "toi", kich_ban=CUM.replace("phòng VIP bệnh viện · sáng · N02",
                                                              "phòng VIP bệnh viện · tối · N02"))
    assert _dan(c3, 1)["truoc"] is None, "khác buổi: cuộc khác"


def test_viet_prompt_canh_sau_thay_bo_cuc_canh_truoc_va_python_ep_giu_cho(tmp_path):
    kho, c, kt = _bo3(tmp_path)
    for i in (0, 1):
        assert c.post(f"/api/tap/D1/C1/dong/{i}/breakdown").status_code == 200
    r = c.post("/api/tap/D1/C1/dong/1/prompt-drama")
    assert r.status_code == 400 and "C001" in r.json()["detail"], "cảnh trước chưa viết: chưa biết chỗ người cũ"
    _bd_va_prompt(c, 0, 1)
    assert "CẢNH TRƯỚC CÙNG NƠI" in kt.canh[-1] and "- Tasha: ben=trai" in kt.canh[-1]
    assert "CẢNH TRƯỚC CÙNG NƠI" not in kt.canh[-2]
    p0, p1 = _pd(kho, 0), _pd(kho, 1)
    assert p1["ben"] == {"Tasha": "trai", "Marcus": "phai", "Ruth": "giua"}, "LLM đảo trái/phải: Python ép lại"
    assert p1["hang"] == ["Tasha", "Ruth", "Marcus"]
    assert p1["phong"]["Tasha"] == p0["phong"]["Tasha"] and p1["phong"]["Ruth"] == "the tall window"


def test_ve_dan_canh_sau_sua_tu_anh_canh_truoc_da_duyet(tmp_path):
    va = VeAnhGia()
    kho, c, _ = _bo3(tmp_path, va=va)
    _bd_va_prompt(c, 0, 1)
    r = c.post("/api/tap/D1/C1/dong/1/dan-canh")
    assert r.status_code == 400 and "vẽ và duyệt" in r.json()["detail"], r.text
    assert c.post("/api/tap/D1/C1/dong/0/dan-canh").status_code == 200
    assert c.post("/api/tap/D1/C1/dong/1/dan-canh").status_code == 400, "vẽ rồi mà chưa duyệt: chưa được"
    assert c.post("/api/tap/D1/C1/dong/0/dan-canh/duyet").status_code == 200
    n = len(va.goi)
    assert c.post("/api/tap/D1/C1/dong/1/dan-canh").status_code == 200
    g = va.goi[n]
    td0 = _dan(c, 0)["td"]
    assert g["ref"][0] == kho.ref_dang_co("D1", td0), "Image 1 = ảnh dàn cảnh cảnh trước"
    assert kho.ref_dang_co("D1", "noi01") not in g["ref"], "phòng lấy từ ảnh cảnh trước, không gửi tấm nơi chốn"
    assert len(g["ref"]) == 4, "ảnh trước + tấm Tasha, Marcus, Ruth"
    assert g["prompt"].startswith("Image 1 is the master wide shot of this same room")
    assert "Tasha and Marcus stay exactly where they are in Image 1" in g["prompt"] and "Add Ruth" in g["prompt"]
    d1 = _dan(c, 1)
    assert d1["co_anh"] and not d1["cu"] and d1["truoc"]["duyet"]
    # Ảnh cảnh trước vẽ lại: ảnh cảnh sau dựng trên ảnh cũ -> báo CŨ.
    import os
    import time
    p0 = kho.ref_dang_co("D1", td0)
    os.utime(p0, (time.time() + 5, time.time() + 5))
    assert _dan(c, 1)["cu"] is True


def test_cung_doi_hinh_dung_lai_nguyen_anh_khong_ton_credit(tmp_path):
    va = VeAnhGia()
    kho, c, _ = _bo3(tmp_path, kich_ban=CUM_CUNG_NGUOI, va=va)
    _bd_va_prompt(c, 0, 1)
    assert c.post("/api/tap/D1/C1/dong/0/dan-canh").status_code == 200
    assert c.post("/api/tap/D1/C1/dong/0/dan-canh/duyet").status_code == 200
    n = len(va.goi)
    assert c.post("/api/tap/D1/C1/dong/1/dan-canh").status_code == 200
    assert len(va.goi) == n, "không gọi máy vẽ"
    a0, a1 = (kho.ref_dang_co("D1", _dan(c, i)["td"]) for i in (0, 1))
    assert a0.read_bytes() == a1.read_bytes() and a0 != a1
    assert not _dan(c, 1)["duyet"], "ảnh của cảnh này vẫn chờ duyệt riêng"


def test_generate_all_cum_chay_lan_luot_canh_sau_dung_tren_anh_canh_truoc(tmp_path):
    va = VeAnhGia()
    kho, c, kt = _bo3(tmp_path, va=va)
    assert c.post(URL_CHAY).status_code == 200
    v = _cho_xong(c)
    assert v["loi"] == [], v["loi"]
    dau = [t.splitlines()[0][:12] for t in kt.canh]
    assert dau == ["CẢNH: C001 ·", "CẢNH: C002 ·"], "LLM cảnh sau đợi cảnh trước"
    td0 = _dan(c, 0)["td"]
    goi1 = [g for g in va.goi if g["dich"].name == _dan(c, 1)["td"] + ".png"]
    assert len(goi1) == 1 and goi1[0]["ref"][0] == kho.ref_dang_co("D1", td0)
    assert _dan(c, 0)["duyet"] and _dan(c, 1)["duyet"]
