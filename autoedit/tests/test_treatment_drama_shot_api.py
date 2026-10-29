"""Drama mỗi shot một video + ảnh dàn cảnh qua API treatment (user chốt 29/10, spec
`docs/SPEC_DONG_NHAT_PHOI_CANH.md`). Đồ giả thay LLM / Seedvis — không mạng.

Luồng: Breakdown (cấp `sid`, `co_mat`) -> Viết prompt cảnh (bố cục ben/phong/cho/dan)
-> vẽ + duyệt ảnh dàn cảnh -> từng shot: vẽ ảnh (mảnh cắt) -> duyệt -> video i2v.
"""

from __future__ import annotations

import json
import os
import re


from test_treatment_drama_api import (MP4, KyThuatGia, VeAnhGia, VeVideoGia, _bd, _bo, _clip, _tap_drama,
                                      _ve_du_ref)


def _canh_bo_cuc(than):
    """LLM giả, phần chung CÓ bố cục — `tren` không phải giá trị `ben` hợp lệ."""
    return {"look": "Soft window light.", "truc": "Tasha left, Marcus right.", "nen": "air vents",
            "tieng": {"Tasha": "Tasha's voice: a woman of about 28.", "Marcus": "Marcus's voice: a man of about 45."},
            "ben": {"Tasha": "trai", "Marcus": "phai", "Ma": "tren"},
            "phong": {"Tasha": "the large window and white blinds", "Marcus": "the white wall with a monitor"},
            "cho": "Tasha stands by the window, Marcus by the bed, to Tasha's right.",
            "dan": "Wide shot from the door side: Tasha on the left by the window, Marcus on the right by the bed."}


def _bd_co_mat(than):
    """LLM giả, Breakdown: mỗi câu một shot; shot chẵn qua vai có hai người (một tên bịa)."""
    n = sum(1 for d in than.splitlines() if d.startswith("["))
    return {"shots": [{"t": f"shot {k}", "co": ("CU", "MS")[k % 2], "goc": ("ots", "eye")[k % 2], "cd": "static",
                       "cau": [k], "co_mat": (["Tasha", "Marcus", "Ghost"], ["Tasha"])[k % 2]}
                      for k in range(n)]}


class KyThuatBoCuc(KyThuatGia):
    def __init__(self):
        super().__init__(bd=_bd_co_mat)

    def drama_canh(self, than):
        self.canh.append(than)
        return _canh_bo_cuc(than)


class VeVideoI2v(VeVideoGia):
    def bat_dau(self, prompt, anh, giay, am, model=None):
        self.goi.append({"prompt": prompt, "anh": anh, "giay": giay, "am": am, "model": model})
        return "task-shot-1"


def _san(tmp_path, va=None, vv=None):
    """Tập drama đã Breakdown + Viết prompt cảnh + có tấm asset."""
    kho, c = _bo(tmp_path, kt=KyThuatBoCuc(), va=va, vv=vv)
    _tap_drama(c)
    _ve_du_ref(kho)
    _bd(c)
    r = c.post("/api/tap/D1/C1/dong/0/prompt-drama")
    assert r.status_code == 200 and r.json()["viet"] == 2, r.text
    return kho, c


def _dan_duyet(c):
    assert c.post("/api/tap/D1/C1/dong/0/dan-canh").status_code == 200
    assert c.post("/api/tap/D1/C1/dong/0/dan-canh/duyet").status_code == 200


# ═══════ Breakdown + PATCH sh ═════════════════════════════════════════════════════
def test_breakdown_cap_sid_rieng_va_co_mat_chi_nguoi_co_tam(tmp_path):
    kho, c = _bo(tmp_path, kt=KyThuatBoCuc())
    _tap_drama(c)
    _bd(c)
    sh = json.loads(_clip(kho)["sh"])
    assert all(re.fullmatch(r"s[0-9a-f]{6}", s["sid"]) for s in sh) and len({s["sid"] for s in sh}) == 2
    assert sh[0]["co_mat"] == ["Tasha", "Marcus"], "tên bịa 'Ghost' phải bị lọc"
    p2 = json.loads(_clip(kho, j=1)["sh"])
    assert p2[0]["co_mat"] == ["Tasha"], "clip một người: LLM không ghi thì lấy người đó"


def test_patch_sh_cap_sid_cho_shot_thieu_giu_sid_cu_va_chan_sai(tmp_path):
    kho, c = _bo(tmp_path, kt=KyThuatBoCuc())
    _tap_drama(c)
    _bd(c)
    p1 = _clip(kho)
    sh = json.loads(p1["sh"])
    giu = sh[0]["sid"]
    sh[1].pop("sid")
    url = f"/api/tap/D1/C1/canh/{p1['id']}"
    assert c.patch(url, json={"truong": {"sh": json.dumps(sh)}}).status_code == 200
    moi = json.loads(_clip(kho)["sh"])
    assert moi[0]["sid"] == giu and re.fullmatch(r"s[0-9a-f]{6}", moi[1]["sid"]) and moi[1]["sid"] != giu
    for sai in ({"sid": "../x"}, {"gi": "7"}, {"co_mat": "Tasha"}, {"sid": giu}):
        x = [dict(moi[0]), dict(moi[1], **sai)]
        assert c.patch(url, json={"truong": {"sh": json.dumps(x)}}).status_code == 400, sai


# ═══════ phần chung mang bố cục ═══════════════════════════════════════════════════
def test_viet_prompt_canh_luu_bo_cuc_vao_pd_moi_clip(tmp_path):
    kho, _ = _san(tmp_path)
    for j in (0, 1):
        pd = json.loads(_clip(kho, j=j)["pd"])
        assert pd["ben"] == {"Tasha": "trai", "Marcus": "phai"}, "giá trị ngoài BEN bị bỏ"
        assert pd["phong"]["Marcus"].startswith("the white wall") and pd["cho"] and pd["dan"]


# ═══════ ảnh dàn cảnh ═════════════════════════════════════════════════════════════
def test_dan_canh_chua_viet_prompt_canh_thi_chua_ve_duoc(tmp_path):
    kho, c = _bo(tmp_path, kt=KyThuatBoCuc())
    _tap_drama(c)
    _ve_du_ref(kho)
    g = c.get("/api/tap/D1/C1/dong/0/dan-canh").json()
    assert g["san"] is False and g["co_anh"] is False and g["nguoi"] == ["Tasha", "Marcus"]
    r = c.post("/api/tap/D1/C1/dong/0/dan-canh")
    assert r.status_code == 400 and "Viết prompt cảnh" in r.json()["detail"]


def test_ve_dan_canh_tao_truong_doan_gan_td_va_gui_noi_chon_roi_moi_nguoi(tmp_path):
    va = VeAnhGia()
    kho, c = _san(tmp_path, va=va)
    p1 = _clip(kho)
    r = c.post("/api/tap/D1/C1/dong/0/dan-canh")
    assert r.status_code == 200, r.text
    td = "td_" + p1["id"]
    assert r.json()["td"] == td and {x["ma"]: x["loai"] for x in kho.ds_so("D1")}[td] == "truong_doan"
    assert _clip(kho)["td"] == td and _clip(kho, j=1)["td"] == td
    g = va.goi[-1]
    assert [p.stem for p in g["ref"]] == ["noi01", "nv01", "nv02"] and g["ti_le"] == "16:9"
    xem = c.get("/api/tap/D1/C1/dong/0/dan-canh").json()
    assert xem["co_anh"] and not xem["duyet"] and xem["prompt"] == g["prompt"] and not xem["cu"]
    assert xem["cat"]["Tasha"][0] < xem["cat"]["Marcus"][0], "khung mặc định theo ben: Tasha trái, Marcus phải"


def test_duyet_dan_canh_het_hieu_luc_khi_ve_lai(tmp_path):
    kho, c = _san(tmp_path)
    _dan_duyet(c)
    assert c.get("/api/tap/D1/C1/dong/0/dan-canh").json()["duyet"] is True
    t = kho.ref_dang_co("D1", "td_" + _clip(kho)["id"])
    os.utime(t, (t.stat().st_atime, t.stat().st_mtime + 5))       # = vẽ lại
    assert c.get("/api/tap/D1/C1/dong/0/dan-canh").json()["duyet"] is False


def test_cat_kiem_bien_va_ghi_vao_moi_clip_cua_canh(tmp_path):
    kho, c = _san(tmp_path)
    url = "/api/tap/D1/C1/dong/0/dan-canh/cat"
    for sai in ({"Ghost": [0, 0, 0.5, 0.5]}, {"Tasha": [0.5, 0, 0.4, 0.5]}, {"Tasha": [0, 0, 0.05, 0.5]},
                {"Tasha": [0, 0, 1.2, 0.5]}, {"Tasha": [0, 0, True, 0.5]}, {}):
        assert c.put(url, json={"cat": sai}).status_code == 400, sai
    assert c.put(url, json={"cat": {"Tasha": [0.05, 0.2, 0.45, 0.6]}}).status_code == 200
    for j in (0, 1):
        assert json.loads(_clip(kho, j=j)["pd"])["cat"] == {"Tasha": [0.05, 0.2, 0.45, 0.6]}
    assert c.get("/api/tap/D1/C1/dong/0/dan-canh").json()["cat"]["Tasha"] == [0.05, 0.2, 0.45, 0.6]
    # viết lại MỘT clip dùng lại phần chung cũ: khung người dựng kéo còn nguyên
    assert c.post(f"/api/tap/D1/C1/canh/{_clip(kho)['id']}/prompt-drama").status_code == 200
    assert json.loads(_clip(kho)["pd"])["cat"]["Tasha"] == [0.05, 0.2, 0.45, 0.6]


# ═══════ ảnh từng shot ════════════════════════════════════════════════════════════
def test_anh_shot_can_dan_canh_da_duyet(tmp_path):
    kho, c = _san(tmp_path)
    p1 = _clip(kho)
    sid = json.loads(p1["sh"])[0]["sid"]
    url = f"/api/tap/D1/C1/canh/{p1['id']}/shot/{sid}/anh"
    assert "dàn cảnh" in c.post(url).json()["detail"]
    c.post("/api/tap/D1/C1/dong/0/dan-canh")
    assert "chưa duyệt" in c.post(url).json()["detail"]


def test_anh_shot_gui_manh_cat_roi_tam_theo_co_mat_dung_prompt_trang_thay(tmp_path):
    va = VeAnhGia()
    kho, c = _san(tmp_path, va=va)
    _dan_duyet(c)
    p1 = _clip(kho)
    sh = json.loads(p1["sh"])
    for k, s in enumerate(sh):
        r = c.post(f"/api/tap/D1/C1/canh/{p1['id']}/shot/{s['sid']}/anh")
        assert r.status_code == 200, r.text
        g = va.goi[-1]
        assert g["ref"][0].name == f"{p1['id']}-{s['sid']}-cat.png" and g["ref"][0].exists()
        assert [p.stem for p in g["ref"][1:]] == [{"Tasha": "nv01", "Marcus": "nv02"}[n] for n in s["co_mat"]]
        assert g["prompt"] == c.get(f"/api/tap/D1/C1/canh/{p1['id']}/shot/{s['sid']}/prompt").json()["anh"]
        assert kho.duong_anh("D1", f"{p1['id']}-{s['sid']}").exists()
    ds = c.get(f"/api/tap/D1/C1/canh/{p1['id']}/shot").json()
    assert [x["co_anh"] for x in ds] == [True, True] and not any(x["duyet"] for x in ds)
    assert ds[0]["chu_the"] == "Marcus", "qua vai: máy hướng tới người nói ở xa"
    # Shot qua vai mà chữ shot không có "Qua vai X": thẻ shot nhắc người dựng chọn Máy hướng tới.
    assert any("Qua vai X" in n for n in ds[0]["nhac"]) and ds[1]["nhac"] == []


def test_mot_shot_hai_nguoi_khong_qua_vai_gui_nguyen_anh_dan_canh(tmp_path):
    va = VeAnhGia()
    kho, c = _san(tmp_path, va=va)
    _dan_duyet(c)
    p1 = _clip(kho)
    sh = json.loads(p1["sh"])
    sh[0]["goc"] = "eye"
    assert c.patch(f"/api/tap/D1/C1/canh/{p1['id']}", json={"truong": {"sh": json.dumps(sh)}}).status_code == 200
    c.post(f"/api/tap/D1/C1/canh/{p1['id']}/shot/{sh[0]['sid']}/anh")
    assert va.goi[-1]["ref"][0] == kho.ref_dang_co("D1", "td_" + p1["id"])


# ═══════ duyệt + video từng shot ══════════════════════════════════════════════════
def test_video_shot_qua_cong_duyet_gui_i2v_dung_giay_roi_tai_ve(tmp_path):
    vv = VeVideoI2v()
    kho, c = _san(tmp_path, vv=vv)
    _dan_duyet(c)
    p1 = _clip(kho)
    sid = json.loads(p1["sh"])[1]["sid"]
    goc = f"/api/tap/D1/C1/canh/{p1['id']}/shot/{sid}"
    assert c.post(goc + "/video").status_code == 400, "chưa có ảnh"
    c.post(goc + "/anh")
    r = c.post(goc + "/video")
    assert r.status_code == 400 and "chưa được duyệt" in r.json()["detail"] and not vv.goi
    assert c.post(goc + "/duyet").status_code == 200
    r = c.post(goc + "/video")
    assert r.status_code == 200 and r.json()["vid"] == "task-shot-1"
    g, pr = vv.goi[-1], c.get(goc + "/prompt").json()
    assert g["anh"] == kho.duong_anh("D1", f"{p1['id']}-{sid}") and g["model"] == "grok-imagine-video-1.5"
    assert g["giay"] == pr["giay"] and g["prompt"] == pr["video"]
    assert c.get(f"/api/tap/D1/C1/canh/{p1['id']}/shot").json()[1]["dang"] is True
    assert c.post(goc + "/video-kiem").json()["trang_thai"] == "xong"
    assert kho.duong_video("D1", f"{p1['id']}-{sid}").read_bytes() == MP4
    x = c.get(f"/api/tap/D1/C1/canh/{p1['id']}/shot").json()[1]
    assert x["co_video"] and not x["dang"] and x["duyet"]
    assert c.get(goc + "/video").status_code == 200


def test_ve_lai_anh_shot_xoa_dau_duyet(tmp_path):
    kho, c = _san(tmp_path)
    _dan_duyet(c)
    p1 = _clip(kho)
    sid = json.loads(p1["sh"])[0]["sid"]
    goc = f"/api/tap/D1/C1/canh/{p1['id']}/shot/{sid}"
    c.post(goc + "/anh")
    c.post(goc + "/duyet")
    assert c.get(f"/api/tap/D1/C1/canh/{p1['id']}/shot").json()[0]["duyet"] is True
    c.post(goc + "/anh")
    assert c.get(f"/api/tap/D1/C1/canh/{p1['id']}/shot").json()[0]["duyet"] is False


def test_trang_cu_tu_luu_khong_xoa_trang_thai_shot(tmp_path):
    """`ss` là trường MÁY: tab JS cũ gửi cả chương thiếu `ss` thì dấu duyệt shot vẫn còn."""
    kho, c = _san(tmp_path)
    _dan_duyet(c)
    p1 = _clip(kho)
    sid = json.loads(p1["sh"])[0]["sid"]
    c.post(f"/api/tap/D1/C1/canh/{p1['id']}/shot/{sid}/anh")
    c.post(f"/api/tap/D1/C1/canh/{p1['id']}/shot/{sid}/duyet")
    d = kho.doc("D1", "C1")
    for x in d["dong"][0]["canh"]:
        x.pop("ss", None)
    kho.luu_tu_trang("D1", "C1", d["dong"], d["outline"], "minh")
    assert json.loads(_clip(kho)["ss"])[sid]["duyet"] == "1"


def test_video_ca_clip_cu_khong_gui_anh_dan_canh(tmp_path):
    """Đường cũ (một video nhiều shot) đánh số ảnh theo `ts`: `td` không được chen vào."""
    vv = VeVideoI2v()
    kho, c = _san(tmp_path, vv=vv)
    c.post("/api/tap/D1/C1/dong/0/dan-canh")
    p1 = _clip(kho)
    assert c.post(f"/api/tap/D1/C1/canh/{p1['id']}/video").status_code == 200
    assert [p.stem for p in vv.goi[-1]["anh"]] == ["noi01", "nv01", "nv02"]


def test_shot_chua_co_sid_hien_rong_va_khong_dung_duoc(tmp_path):
    kho, c = _san(tmp_path)
    p1 = _clip(kho)
    sh = [{k: v for k, v in s.items() if k != "sid"} for s in json.loads(p1["sh"])]

    def va(y):
        y["sh"] = json.dumps(sh)
    kho.sua_canh("D1", "C1", p1["id"], va, "minh")
    assert [x["sid"] for x in c.get(f"/api/tap/D1/C1/canh/{p1['id']}/shot").json()] == ["", ""]
    assert c.post(f"/api/tap/D1/C1/canh/{p1['id']}/shot/s000000/anh").status_code == 404


def test_ham_moi_khong_che_ham_nguoi_dung_cua_module(tmp_path):
    """Hàm lồng trùng tên `_nguoi` từng che `_nguoi(request)` của module: `/api/toi` 500
    và trang không biết ai đang dùng (trợ lý B bắt được trong Chrome, 29/10)."""
    _, c = _bo(tmp_path)
    r = c.get("/api/toi")
    assert r.status_code == 200 and r.json()["nguoi"] == "minh"
