"""Sửa riêng MỘT shot (user haint chốt 31/10): ô "Yêu cầu sửa" tiếng Việt, máy dịch, lời sửa lưu
theo shot và vào prompt ảnh lẫn video; nút "Sửa ảnh này" chỉnh từ ảnh hiện tại; mỗi lần vẽ / gen
lại giữ một bản trước (`-cu`) để quay lại. Khảo sát 30/10: 13 lượt Breakdown lại chỉ để sửa một
câu, bỏ phí ~38 ảnh + 18 video. Đồ giả thay LLM / Seedvis — không mạng.
"""

from __future__ import annotations

import json

from PIL import Image

from autoedit.treatment import drama
from test_treatment_drama_api import MP4, VeAnhGia, _bo, _clip, _tap_drama, _ve_du_ref
from test_treatment_drama_api import _bd
from test_treatment_drama_shot_api import KyThuatBoCuc, VeVideoI2v, _dan_duyet

SUA_EN = "Tasha is crying, tears on her cheeks."


class KyThuatSua(KyThuatBoCuc):
    def __init__(self):
        super().__init__()
        self.sua, self.en = [], SUA_EN

    def drama_sua(self, than):
        self.sua.append(than)
        return {"en": self.en}


class VeAnhDem(VeAnhGia):
    """Mỗi lượt vẽ một màu khác để phân biệt bản."""

    def gen_anh(self, prompt, dich, ref=None, model=None, ti_le=None):
        self.goi.append({"prompt": prompt, "dich": dich, "ref": list(ref or []), "model": model, "ti_le": ti_le})
        dich.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (480, 270), (10 * len(self.goi), 0, 0)).save(dich)
        return dich


class VeVideoDem(VeVideoI2v):
    """Mỗi lượt gửi một mã task riêng (như nhà thật) và một bản video riêng."""

    def __init__(self):
        super().__init__()
        self.lan = 0

    def bat_dau(self, prompt, anh, giay, am, model=None):
        super().bat_dau(prompt, anh, giay, am, model)
        return f"task-shot-{len(self.goi)}"

    def tai_ve(self, url, dich):
        self.lan += 1
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(MP4 + bytes([self.lan]))
        return dich


def _san(tmp_path, kt=None, va=None, vv=None):
    kho, c = _bo(tmp_path, kt=kt or KyThuatSua(), va=va or VeAnhDem(), vv=vv)
    _tap_drama(c)
    _ve_du_ref(kho)
    _bd(c)
    assert c.post("/api/tap/D1/C1/dong/0/prompt-drama").status_code == 200
    _dan_duyet(c)
    p1 = _clip(kho)
    sid = json.loads(p1["sh"])[1]["sid"]            # shot 2: MS, chỉ Tasha
    return kho, c, p1, sid, f"/api/tap/D1/C1/canh/{p1['id']}/shot/{sid}"


def _the(c, p1, sid):
    return next(x for x in c.get(f"/api/tap/D1/C1/canh/{p1['id']}/shot").json() if x["sid"] == sid)


def test_luu_loi_sua_may_dich_roi_vao_prompt_anh_va_video(tmp_path):
    kt = KyThuatSua()
    kho, c, p1, sid, goc = _san(tmp_path, kt=kt)
    r = c.post(goc + "/sua", json={"sua": "Tasha đang khóc"})
    assert r.status_code == 200, r.text
    assert r.json() == {"sua": "Tasha đang khóc", "sua_en": SUA_EN, "nhac": []}
    assert "Lời sửa: Tasha đang khóc" in kt.sua[-1] and "Trong khung: Tasha" in kt.sua[-1]
    s = next(x for x in json.loads(_clip(kho)["sh"]) if x["sid"] == sid)
    assert (s["sua"], s["sua_en"]) == ("Tasha đang khóc", SUA_EN)
    pr = c.get(goc + "/prompt").json()
    assert f"{drama.SUA_DAU} {SUA_EN}" in pr["anh"] and f"{drama.SUA_DAU} {SUA_EN}" in pr["video"]
    x = _the(c, p1, sid)
    assert (x["sua"], x["sua_en"], x["anh_cu"], x["video_cu"]) == ("Tasha đang khóc", SUA_EN, False, False)
    # shot khác không dính
    khac = json.loads(_clip(kho)["sh"])[0]["sid"]
    assert drama.SUA_DAU not in c.get(f"/api/tap/D1/C1/canh/{p1['id']}/shot/{khac}/prompt").json()["anh"]
    # câu tiếng Anh gọi tên người ngoài khung: nhắc (gọi tên là model vẽ thêm người đó), vẫn lưu
    kt.en = "Marcus stands behind Tasha."
    nhac = c.post(goc + "/sua", json={"sua": "Marcus đứng sau Tasha"}).json()["nhac"]
    assert len(nhac) == 1 and "Marcus" in nhac[0] and "không có trong khung" in nhac[0]
    # xoá = lưu rỗng, không gọi LLM
    n = len(kt.sua)
    assert c.post(goc + "/sua", json={"sua": "  "}).json() == {"sua": "", "sua_en": "", "nhac": []}
    assert len(kt.sua) == n and "sua_en" not in next(x for x in json.loads(_clip(kho)["sh"]) if x["sid"] == sid)


def test_sua_tay_cau_tieng_anh_qua_patch_sh(tmp_path):
    kho, c, p1, sid, goc = _san(tmp_path)
    sh = json.loads(_clip(kho)["sh"])
    sh[1]["sua_en"] = "Tasha looks down at her hands."
    r = c.patch(f"/api/tap/D1/C1/canh/{p1['id']}", json={"truong": {"sh": json.dumps(sh)}})
    assert r.status_code == 200, r.text
    assert "Tasha looks down at her hands." in c.get(goc + "/prompt").json()["anh"]
    sh[1]["sua_en"] = 3
    assert c.patch(f"/api/tap/D1/C1/canh/{p1['id']}", json={"truong": {"sh": json.dumps(sh)}}).status_code == 400


def test_khong_co_ham_dich_thi_503(tmp_path):
    class Cu(KyThuatBoCuc):
        pass

    kho, c, p1, sid, goc = _san(tmp_path, kt=Cu())
    assert c.post(goc + "/sua", json={"sua": "Tasha đang khóc"}).status_code == 503


def test_sua_anh_nay_chinh_tu_anh_hien_tai_giu_ban_cu_bo_duyet(tmp_path):
    va = VeAnhDem()
    kho, c, p1, sid, goc = _san(tmp_path, va=va)
    assert "chưa có ảnh" in c.post(goc + "/sua-anh").json()["detail"]
    c.post(goc + "/anh")
    assert "lời sửa" in c.post(goc + "/sua-anh").json()["detail"]
    c.post(goc + "/sua", json={"sua": "Tasha đang khóc"})
    c.post(goc + "/duyet")
    anh = kho.duong_anh("D1", f"{p1['id']}-{sid}")
    truoc = anh.read_bytes()
    r = c.post(goc + "/sua-anh")
    assert r.status_code == 200, r.text
    g = va.goi[-1]
    cu = anh.with_name(anh.stem + "-cu.png")
    assert g["ref"][0] == cu and cu.read_bytes() == truoc and anh.read_bytes() != truoc
    assert [p.stem for p in g["ref"][1:]] == ["nv01"] and g["dich"] == anh and g["ti_le"] == "16:9"
    s = next(x for x in json.loads(_clip(kho)["sh"]) if x["sid"] == sid)
    assert g["prompt"] == drama.prompt_sua_anh(s, {"Tasha": {}})
    x = _the(c, p1, sid)
    assert x["anh_cu"] and not x["duyet"]


def test_ve_lai_giu_ban_truoc_va_quay_lai_doi_cho_hai_ban(tmp_path):
    kho, c, p1, sid, goc = _san(tmp_path)
    assert c.post(goc + "/quay-lai", json={"loai": "anh"}).status_code == 400, "chưa có bản cũ"
    c.post(goc + "/anh")
    anh = kho.duong_anh("D1", f"{p1['id']}-{sid}")
    mot = anh.read_bytes()
    assert not _the(c, p1, sid)["anh_cu"]
    c.post(goc + "/anh")
    hai = anh.read_bytes()
    assert hai != mot and _the(c, p1, sid)["anh_cu"]
    c.post(goc + "/duyet")
    r = c.post(goc + "/quay-lai", json={"loai": "anh"})
    assert r.status_code == 200, r.text
    assert anh.read_bytes() == mot and not _the(c, p1, sid)["duyet"]
    c.post(goc + "/quay-lai", json={"loai": "anh"})
    assert anh.read_bytes() == hai, "bấm lần nữa là về lại"
    assert c.post(goc + "/quay-lai", json={"loai": "xx"}).status_code == 400


def test_quay_lai_lien_tay_van_doi_ma_chong_cache(tmp_path):
    """`anh_v` (và tem Storyboard) là giờ sửa tính bằng GIÂY: hai lần Quay lại trong cùng một giây
    mà mã không đổi thì trình duyệt hiện ảnh cũ trong bộ nhớ đệm (rendery-v2-91 đo bằng Chrome)."""
    kho, c, p1, sid, goc = _san(tmp_path)
    c.post(goc + "/anh")
    c.post(goc + "/anh")
    ma = [_the(c, p1, sid)["anh_v"]]
    for _ in range(3):
        assert c.post(goc + "/quay-lai", json={"loai": "anh"}).status_code == 200
        ma.append(_the(c, p1, sid)["anh_v"])
    assert all(b > a for a, b in zip(ma, ma[1:])), ma


def test_gen_lai_video_giu_ban_truoc_va_quay_lai(tmp_path):
    vv = VeVideoDem()
    kho, c, p1, sid, goc = _san(tmp_path, vv=vv)
    c.post(goc + "/anh")
    c.post(goc + "/duyet")
    v = kho.duong_video("D1", f"{p1['id']}-{sid}")
    for _ in range(2):
        assert c.post(goc + "/video").status_code == 200
        assert c.post(goc + "/video-kiem").json()["trang_thai"] == "xong"
    assert v.read_bytes() == MP4 + b"\x02" and _the(c, p1, sid)["video_cu"]
    assert c.post(goc + "/quay-lai", json={"loai": "video"}).status_code == 200
    assert v.read_bytes() == MP4 + b"\x01" and _the(c, p1, sid)["duyet"], "quay lại video không đụng duyệt ảnh"
