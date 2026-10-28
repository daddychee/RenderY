"""Drama thoại + luật tài sản khuôn Padoma qua API treatment (user chốt 27/10).

Đồ giả thay LLM / Seedvis — không mạng. Mẫu kịch bản dùng chung với
`test_treatment_drama.py` (đã qua máy kiểm của Padoma).
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from PIL import Image

from autoedit.treatment import drama
from autoedit.treatment.app import _LENH_BREAKDOWN_DRAMA, tao_app
from autoedit.treatment.kho import Kho
from test_treatment_drama import KICH_BAN

MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64


class VeAnhGia:
    """Ghi lại mọi lượt vẽ; ảnh ra ĐÚNG tỉ lệ được xin để soát tấm gộp."""

    CO = {"1:1": (300, 300), "9:16": (270, 480), "16:9": (480, 270)}

    def __init__(self):
        self.goi = []

    def gen_anh(self, prompt, dich, ref=None, model=None, ti_le=None):
        self.goi.append({"prompt": prompt, "dich": dich, "ref": list(ref or []), "model": model, "ti_le": ti_le})
        dich.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", self.CO.get(ti_le, (480, 270)), (90, 90, 90)).save(dich)
        return dich


class VeVideoGia:
    def __init__(self):
        self.goi = []

    def bat_dau_ref(self, prompt, anh, giay, model=None):
        self.goi.append({"prompt": prompt, "anh": list(anh), "giay": giay, "model": model})
        return "task-drama-1"

    def trang_thai(self, tid):
        return {"status": "succeeded", "video_url": "https://vi-du/" + tid + ".mp4"}

    def tai_ve(self, url, dich):
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(MP4)
        return dich


def _canh_dung(than):
    """LLM giả, lượt PHẦN CHUNG của cảnh."""
    return {"look": "Soft window light.", "truc": "Tasha frame left, Marcus frame right.", "nen": "air vents",
            "tieng": {"Tasha": "Tasha's voice: a woman of about 28.",
                      "Marcus": "Marcus's voice: a man of about 45."}}


def _clip_dung(than):
    """LLM giả, lượt MỘT clip: viết chữ cho ĐÚNG số shot đã breakdown ("- Shot k")."""
    n = sum(1 for d in than.splitlines() if d.startswith("- Shot "))
    return {"truc": "Tasha frame left.", "y": "The audience must feel it.", "size": "", "giu": "her cardigan",
            "shots": [{"lap": f"Tasha on the left {k}", "cach": "quiet", "mat": "still", "am": ""}
                      for k in range(n)]}


def _bd_dung(than):
    """LLM giả, lượt BREAKDOWN một clip: mỗi câu thoại "[k]" một shot, mã xen nhau."""
    n = sum(1 for d in than.splitlines() if d.startswith("["))
    return {"shots": [{"t": f"shot {k}", "co": ("CU", "MS")[k % 2], "goc": ("ots", "eye")[k % 2],
                       "cd": "static", "cau": [k], "ly_do": "theo Hình"} for k in range(n)]}


class KyThuatGia:
    def __init__(self, clip=None, bd=None):
        self.canh, self.clip, self.bd = [], [], []
        self.tra, self.tra_bd = clip, bd

    def drama_canh(self, than):
        self.canh.append(than)
        return _canh_dung(than)

    def drama_clip(self, than):
        self.clip.append(than)
        return self.tra(than) if self.tra else _clip_dung(than)

    def drama_breakdown(self, than):
        self.bd.append(than)
        return self.tra_bd(than) if self.tra_bd else _bd_dung(than)


class SinhAssetGia:
    def __init__(self):
        self.goi = []

    def sinh_asset_2(self, muc, tong):
        self.goi.append(dict(muc))
        if muc["loai"] == "nhan_vat":
            return {"chu": "LLM REWROTE", "tieng": muc["ten"] + "'s voice: calm."}
        return {"chu": "A small hospital room with a window. Light: grey daylight from the window.", "tieng": ""}

    def sinh_asset(self, muc, tong):         # đường cũ, tập khuôn ""
        return {"chu": "old chu", "pr": "old pr"}


def _bo(tmp_path, kt=None, vv=None, va=None, sa=None):
    kho = Kho(tmp_path / "kho" / "k.db")
    app = tao_app(kho, ky_thuat=kt or KyThuatGia(), ve_video=vv or VeVideoGia(),
                  ve_anh=va or VeAnhGia(), sinh_asset=sa or SinhAssetGia())
    c = TestClient(app)
    c.headers.update({"X-Remote-User": "minh", "X-Remote-Actions": "sua"})
    return kho, c


def _tap_drama(c):
    assert c.post("/api/tap", json={"ma": "D1", "ten": "Hộp nhẫn", "loai": "drama"}).status_code == 200
    r = c.post("/api/tap/D1/drama", json={"text": KICH_BAN})
    assert r.status_code == 200, r.text
    return r.json()


def _clip(kho, ch="C1", i=0, j=0):
    return kho.doc("D1", ch)["dong"][i]["canh"][j]


def _bd(c, ch="C1", i=0):
    """Breakdown cảnh drama — bước bắt buộc trước Create Prompt, như narration."""
    r = c.post(f"/api/tap/D1/{ch}/dong/{i}/breakdown")
    assert r.status_code == 200 and not r.json()["loi"], r.text
    return r.json()


# ═══════ tạo tập ═══════════════════════════════════════════════════════════════
def test_tap_moi_qua_api_la_khuon_2_drama_mang_loai(tmp_path):
    kho, c = _bo(tmp_path)
    c.post("/api/tap", json={"ma": "N1", "ten": "narration"})
    c.post("/api/tap", json={"ma": "D1", "ten": "drama", "loai": "drama"})
    assert kho.kieu_tap("N1") == {"loai": "", "khuon": "2"}
    assert kho.kieu_tap("D1") == {"loai": "drama", "khuon": "2"}
    assert {t["ma"]: t["loai"] for t in c.get("/api/tap").json()} == {"N1": "", "D1": "drama"}
    assert c.post("/api/tap", json={"ma": "X", "ten": "x", "loai": "phim-ma"}).status_code == 400


def test_tap_cu_giu_khuon_cu(tmp_path):
    kho, _ = _bo(tmp_path)
    kho.tao_tap("SE001", "cũ")
    assert kho.kieu_tap("SE001") == {"loai": "", "khuon": ""}


# ═══════ dán kịch bản ═══════════════════════════════════════════════════════════
def test_dan_kich_ban_tao_chuong_clip_va_so(tmp_path):
    kho, c = _bo(tmp_path)
    r = _tap_drama(c)
    assert r["chuong"] == 2 and r["clip"] == 3 and r["bo"] == 0
    assert [x["ma"] for x in kho.ds_chuong("D1")] == ["C1", "C2"]
    p1 = _clip(kho)
    assert p1["pm"] == "P001" and p1["gi"] == "15" and p1["ts"] == ["noi01", "nv01", "nv02"] and p1["id"]
    so = {x["ma"]: x for x in kho.ds_so("D1")}
    assert so["nv01"]["chu"].startswith("Beautiful Black woman") and so["nv01"]["tieng"].startswith("nữ 28")
    assert so["noi01"]["yc"].startswith("phòng bệnh riêng")
    assert kho.doc("D1", "C1")["outline"].startswith("Phần 1")


def test_dan_kich_ban_loi_tra_400_kem_loi_va_khong_ghi_gi(tmp_path):
    kho, c = _bo(tmp_path)
    c.post("/api/tap", json={"ma": "D1", "ten": "x", "loai": "drama"})
    r = c.post("/api/tap/D1/drama", json={"text": KICH_BAN.replace("Máy: Grok 15s\nKhung: Tasha\nHình: cận",
                                                                     "Máy: Grok 20s\nKhung: Tasha\nHình: cận")})
    assert r.status_code == 400 and "P002" in r.json()["detail"]
    assert kho.ds_chuong("D1") == [] and kho.ds_so("D1") == []


def test_dan_kich_ban_drama_vao_tap_narration_bi_chan(tmp_path):
    _, c = _bo(tmp_path)
    c.post("/api/tap", json={"ma": "N1", "ten": "x"})
    assert c.post("/api/tap/N1/drama", json={"text": KICH_BAN}).status_code == 400


def test_dan_lai_giu_ma_do_dai_va_chu_nguoi_dung_viet(tmp_path):
    kho, c = _bo(tmp_path)
    _tap_drama(c)
    p1 = _clip(kho)
    assert c.patch(f"/api/tap/D1/C1/canh/{p1['id']}", json={"truong": {"gi": "10"}}).status_code == 200
    so = kho.ds_so("D1")
    for x in so:
        if x["ma"] == "noi01":
            x["chu"] = "A private hospital room. Light: window."
        if x["ma"] == "nv01":
            x["tieng"] = "Tasha's voice: a woman of about 28."
    kho.luu_so("D1", so + [{"ma": "hop", "loai": "dao_cu", "ten": "hộp nhẫn", "chu": "red box"}])
    r = c.post("/api/tap/D1/drama", json={"text": KICH_BAN.replace("Five minutes.", "Five minutes, sir.")})
    assert r.status_code == 200
    moi = _clip(kho)
    assert moi["id"] == p1["id"] and moi["gi"] == "10" and "Five minutes, sir." in moi["t"]
    so = {x["ma"]: x for x in kho.ds_so("D1")}
    assert so["noi01"]["chu"] == "A private hospital room. Light: window.", "chữ EN người dùng đã viết phải còn"
    assert so["nv01"]["tieng"] == "Tasha's voice: a woman of about 28.", "giọng tiếng Anh đã chốt phải còn"
    assert "hop" in so, "asset người dùng thêm tay không bị xoá"


def test_do_dai_chi_nhan_6_10_15(tmp_path):
    kho, c = _bo(tmp_path)
    _tap_drama(c)
    p1 = _clip(kho)
    assert c.patch(f"/api/tap/D1/C1/canh/{p1['id']}", json={"truong": {"gi": "8"}}).status_code == 400
    assert c.patch(f"/api/tap/D1/C1/canh/{p1['id']}", json={"truong": {"gi": "6"}}).status_code == 200
    assert _clip(kho)["gi"] == "6"


# ═══════ viết prompt theo CẢNH ═══════════════════════════════════════════════════
def test_viet_prompt_canh_phan_chung_mot_luot_roi_moi_clip_mot_luot(tmp_path):
    """Kiểm thử 28/10 (L1): một lượt cho cả cảnh 5 clip quá 180 s 2/2 lần. Phần
    chung (ánh sáng, trục, nền, giọng) MỘT lượt — giống nhau ở mọi clip — rồi mỗi
    clip một lượt riêng chỉ mang clip của nó."""
    kt = KyThuatGia()
    kho, c = _bo(tmp_path, kt=kt)
    _tap_drama(c)
    _bd(c)
    r = c.post("/api/tap/D1/C1/dong/0/prompt-drama")
    assert r.status_code == 200, r.text
    assert r.json()["viet"] == 2 and r.json()["loi"] == []
    assert len(kt.canh) == 1 and len(kt.clip) == 2
    assert "CẦN CÂU GIỌNG: Tasha, Marcus" in kt.canh[0]
    b1 = next(x for x in kt.clip if "### P001" in x)
    assert "[0] Marcus (gằn, buộc tội): \"Only you were in this room.\"" in b1
    assert "P002" not in b1, "lượt clip chỉ mang clip của nó"
    assert "TRỤC CẢNH: Tasha frame left, Marcus frame right." in b1
    so = {x["ma"]: x for x in kho.ds_so("D1")}
    assert so["nv01"]["tieng"] == "Tasha's voice: a woman of about 28."
    assert so["nv01_d2"]["tieng"] == "Tasha's voice: a woman of about 28.", "đổi đồ không đổi giọng"
    p1 = _clip(kho)
    pd = json.loads(p1["pd"])
    assert pd["truc"] == "Tasha frame left." and pd["look"] == "Soft window light."
    p = c.get(f"/api/tap/D1/C1/canh/{p1['id']}/prompt").json()["video"]
    assert 'SPEAKER: Marcus. LINE: "Only you were in this room."' in p
    assert "Marcus's voice: a man of about 45." in p and "-15s)" in p
    assert "Marcus frame right" not in p, "trục chung chỉ làm mốc, không gửi máy dựng"


def test_cac_clip_cua_canh_viet_song_song(tmp_path):
    import threading
    rao = threading.Barrier(2, timeout=5)

    def cho_nhau(than):
        rao.wait()               # chạy lần lượt thì lượt đầu đứng chờ tới hết giờ
        return _clip_dung(than)
    kho, c = _bo(tmp_path, kt=KyThuatGia(cho_nhau))
    _tap_drama(c)
    _bd(c)
    r = c.post("/api/tap/D1/C1/dong/0/prompt-drama").json()
    assert r["viet"] == 2 and r["loi"] == [], r


def test_cau_vi_tri_nhac_nguoi_ngoai_khung_thi_khong_luu_clip(tmp_path):
    """Kiểm thử 28/10 (L4): câu trục chung nhắc người không có trong clip — Grok
    vẽ người theo câu đó. P002 chỉ có Tasha trong khung."""
    def nhac(than):
        return dict(_clip_dung(than), truc="Tasha frame left, Marcus's shoulder in the right foreground.")
    kho, c = _bo(tmp_path, kt=KyThuatGia(nhac))
    _tap_drama(c)
    _bd(c)
    r = c.post("/api/tap/D1/C1/dong/0/prompt-drama").json()
    assert r["viet"] == 1 and any("P002" in x and "Marcus" in x for x in r["loi"]), r
    assert _clip(kho).get("pd") and not _clip(kho, j=1).get("pd")


def test_viet_mot_clip_dung_lai_phan_chung_khong_dung_clip_khac(tmp_path):
    kt = KyThuatGia()
    kho, c = _bo(tmp_path, kt=kt)
    _tap_drama(c)
    _bd(c)
    r = c.post(f"/api/tap/D1/C1/canh/{_clip(kho, j=1)['id']}/prompt-drama")
    assert r.status_code == 200 and r.json()["viet"] == 1, r.text
    assert len(kt.canh) == 1 and len(kt.clip) == 1, "cảnh chưa có phần chung: viết phần chung trước"
    assert not _clip(kho).get("pd")
    p2 = _clip(kho, j=1)["pd"]
    r = c.post(f"/api/tap/D1/C1/canh/{_clip(kho)['id']}/prompt-drama")
    assert r.json()["viet"] == 1 and len(kt.canh) == 1 and len(kt.clip) == 2, "phần chung dùng lại"
    assert _clip(kho, j=1)["pd"] == p2, "clip khác không bị đụng"
    assert json.loads(_clip(kho)["pd"])["look"] == "Soft window light."


def test_viet_prompt_LLM_tra_lech_so_shot_thi_clip_do_khong_luu(tmp_path):
    """Shot là của Breakdown (người dựng duyệt mã). LLM viết chữ cho thiếu một shot
    thì chữ shot sau trôi sang khung shot trước — không lưu."""
    def sai(than):
        r = _clip_dung(than)
        if "### P001" in than:
            r["shots"] = r["shots"][:1]
        return r
    kho, c = _bo(tmp_path, kt=KyThuatGia(sai))
    _tap_drama(c)
    _bd(c)
    r = c.post("/api/tap/D1/C1/dong/0/prompt-drama").json()
    assert r["viet"] == 1 and any("P001" in x and "shot" in x for x in r["loi"]), r
    assert not _clip(kho).get("pd") and _clip(kho, j=1).get("pd")


# ═══════ Breakdown drama: shot + mã cỡ/góc/máy của treatment (user chốt 28/10) ═══════
def test_breakdown_canh_drama_moi_clip_mot_luot_ghi_shot_ma(tmp_path):
    kt = KyThuatGia()
    kho, c = _bo(tmp_path, kt=kt)
    _tap_drama(c)
    r = c.post("/api/tap/D1/C1/dong/0/breakdown")
    assert r.status_code == 200, r.text
    assert r.json()["so_clip"] == 2 and r.json()["loi"] == []
    assert len(kt.bd) == 2
    b1 = next(x for x in kt.bd if "### P001" in x)
    assert "Hình: shot 1 qua vai Tasha" in b1 and "[1] Tasha" in b1 and "P002" not in b1
    sh = json.loads(_clip(kho)["sh"])
    assert [(s["t"], s["co"], s["goc"], s["cd"], s["cau"]) for s in sh] == [
        ("shot 0", "CU", "ots", "static", [0]), ("shot 1", "MS", "eye", "static", [1])]
    assert "ly_do" not in sh[0], "lý do chỉ để LLM nghĩ, không lưu"


def test_breakdown_ma_la_ve_mac_dinh_nhu_narration(tmp_path):
    def la(than):
        r = _bd_dung(than)
        r["shots"][0].update(co="XL", goc="dutch", cd="orbit")      # orbit: Grok xoay 360 hỏng 2/2
        return r
    kho, c = _bo(tmp_path, kt=KyThuatGia(bd=la))
    _tap_drama(c)
    _bd(c)
    s0 = json.loads(_clip(kho)["sh"])[0]
    assert (s0["co"], s0["goc"], s0["cd"]) == ("MS", "eye", "")


def test_breakdown_chia_thoai_sai_hay_qua_nhieu_shot_thi_khong_luu_clip_do(tmp_path):
    def sai(than):
        r = _bd_dung(than)
        if "### P002" in than:
            r["shots"][0]["cau"] = [5]                               # trỏ câu không có
        else:
            r["shots"] += [dict(r["shots"][0], cau=[]), dict(r["shots"][0], cau=[])]   # 4 shot cho 6 giây
        return r
    kho, c = _bo(tmp_path, kt=KyThuatGia(bd=sai))
    _tap_drama(c)
    c.patch(f"/api/tap/D1/C1/canh/{_clip(kho)['id']}", json={"truong": {"gi": "6"}})
    r = c.post("/api/tap/D1/C1/dong/0/breakdown").json()
    assert r["so_clip"] == 0, r
    assert any("P001" in x and "6 giây" in x for x in r["loi"]) and any("P002" in x for x in r["loi"])
    assert not _clip(kho).get("sh") and not _clip(kho, j=1).get("sh")


def test_breakdown_lai_mot_clip_bo_prompt_clip_do_khong_dung_clip_khac(tmp_path):
    kho, c = _bo(tmp_path)
    _tap_drama(c)
    _bd(c)
    c.post("/api/tap/D1/C1/dong/0/prompt-drama")
    p2 = (_clip(kho, j=1)["pd"], _clip(kho, j=1)["sh"])
    r = c.post(f"/api/tap/D1/C1/canh/{_clip(kho)['id']}/breakdown")
    assert r.status_code == 200 and r.json()["so_clip"] == 1, r.text
    assert not _clip(kho).get("pd"), "shot đổi: prompt viết theo shot cũ phải viết lại"
    assert (_clip(kho, j=1)["pd"], _clip(kho, j=1)["sh"]) == p2


def test_lenh_breakdown_drama_may_doi_co_thi_ma_la_co_luc_bat_dau():
    """Đợt 0 (28/10): "đẩy vào chậm tới cận" ghi CU -> Grok mở ngay ở cận, gần như
    không đẩy; ghi cỡ lúc BẮT ĐẦU (MCU) thì đẩy vào thật."""
    assert "cỡ LÚC BẮT ĐẦU" in _LENH_BREAKDOWN_DRAMA
    assert "đẩy vào tới cận → MCU + push_in" in _LENH_BREAKDOWN_DRAMA


def test_viet_prompt_chua_breakdown_thi_chan_khong_goi_LLM(tmp_path):
    kt = KyThuatGia()
    kho, c = _bo(tmp_path, kt=kt)
    _tap_drama(c)
    r = c.post(f"/api/tap/D1/C1/canh/{_clip(kho)['id']}/prompt-drama")
    assert r.status_code == 400 and "Breakdown" in r.json()["detail"]
    r = c.post("/api/tap/D1/C1/dong/0/prompt-drama").json()
    assert r["viet"] == 0 and len(r["loi"]) == 2 and all("Breakdown" in x for x in r["loi"])
    assert kt.canh == [] and kt.clip == []


def test_prompt_ghep_cau_dau_shot_tu_ma_cua_nguoi_dung_va_lap(tmp_path):
    """Mục 3 (user 28/10): clip drama bỏ mất cỡ/góc/máy treatment đã xây. Câu đầu
    mỗi shot giờ Python ghép từ MÃ, bằng đúng bảng chữ đã đo của narration."""
    kt = KyThuatGia()
    kho, c = _bo(tmp_path, kt=kt)
    _tap_drama(c)
    _bd(c)
    c.post("/api/tap/D1/C1/dong/0/prompt-drama")
    b1 = next(x for x in kt.clip if "### P001" in x)
    assert "- Shot 1 · close-up, over-the-shoulder shot" in b1, "LLM viết chữ theo khung đã chọn"
    p1 = _clip(kho)
    assert json.loads(p1["sh"])[0]["lap"] == "Tasha on the left 0"
    assert all("khung" not in s and "cau" not in s for s in json.loads(p1["pd"])["shots"])
    p = c.get(f"/api/tap/D1/C1/canh/{p1['id']}/prompt").json()["video"]
    assert ("s), close-up, over-the-shoulder shot, from behind a second person's shoulder in the "
            "foreground: Tasha on the left 0. The camera holds perfectly still.\n") in p
    assert "s), medium shot, eye level: Tasha on the left 1. The camera holds perfectly still.\n" in p


def test_lap_nhac_nguoi_ngoai_khung_thi_khong_luu_clip(tmp_path):
    def nhac(than):
        r = _clip_dung(than)
        if "### P002" in than:
            r["shots"][0]["lap"] = "Tasha on the left, Marcus blurred behind her"
        return r
    kho, c = _bo(tmp_path, kt=KyThuatGia(nhac))
    _tap_drama(c)
    _bd(c)
    r = c.post("/api/tap/D1/C1/dong/0/prompt-drama").json()
    assert r["viet"] == 1 and any("P002" in x and "Marcus" in x for x in r["loi"]), r


def test_sua_ma_shot_qua_hop_canh(tmp_path):
    kho, c = _bo(tmp_path)
    _tap_drama(c)
    _bd(c)
    c.post("/api/tap/D1/C1/dong/0/prompt-drama")
    ma = _clip(kho)["id"]
    sh = json.loads(_clip(kho)["sh"])

    def gui(x):
        return c.patch(f"/api/tap/D1/C1/canh/{ma}", json={"truong": {"sh": json.dumps(x)}}).status_code
    sh[1]["cd"] = "push_in"
    assert gui(sh) == 200
    assert c.get("/api/tap/D1/C1/cu").json()[ma]["prompt"] is False, "đổi máy không cần LLM viết lại"
    assert "The camera pushes in slowly" in c.get(f"/api/tap/D1/C1/canh/{ma}/prompt").json()["video"]
    sh[1]["co"] = "WS"
    assert gui(sh) == 200
    assert c.get("/api/tap/D1/C1/cu").json()[ma]["prompt"] is True, "đổi cỡ: chữ viết theo khung cũ"
    assert gui([dict(sh[0], co="XL"), sh[1]]) == 400
    assert gui([dict(sh[0], cau=[1]), dict(sh[1], cau=[0])]) == 400, "thoại sai thứ tự"
    assert gui([dict(sh[0], la=1), sh[1]]) == 400
    assert gui({"co": "CU"}) == 400
    assert json.loads(_clip(kho)["sh"])[1]["co"] == "WS"


def test_doc_chuong_tra_moc_thoai_cau_dau_shot(tmp_path):
    kho, c = _bo(tmp_path)
    _tap_drama(c)
    x = c.get("/api/tap/D1/C1").json()["dong"][0]["canh"][0]
    assert x["ns"] == 0 and x["moc"] == [] and x["dau_shot"] == []
    _bd(c)
    x = c.get("/api/tap/D1/C1").json()["dong"][0]["canh"][0]
    assert x["ns"] == 2 and x["moc"][0][0] == 0 and x["moc"][-1][1] == 15
    assert x["thoai"][0] == {"ten": "Marcus", "cach": "gằn, buộc tội", "cau": "Only you were in this room.",
                             "nghi": False}
    assert x["dau_shot"][0] == ("close-up, over-the-shoulder shot, from behind a second person's shoulder "
                                "in the foreground. The camera holds perfectly still.")


def test_doi_giay_thi_prompt_doi_moc_khong_goi_LLM(tmp_path):
    kt = KyThuatGia()
    kho, c = _bo(tmp_path, kt=kt)
    _tap_drama(c)
    _bd(c)
    c.post("/api/tap/D1/C1/dong/0/prompt-drama")
    p1 = _clip(kho)
    c.patch(f"/api/tap/D1/C1/canh/{p1['id']}", json={"truong": {"gi": "10"}})
    p = c.get(f"/api/tap/D1/C1/canh/{p1['id']}/prompt").json()["video"]
    assert "-10s)" in p and "-15s)" not in p and len(kt.canh) == 1 and len(kt.clip) == 2


# ═══════ gen video drama: ảnh tham chiếu, không khung đầu ════════════════════════
def _ve_du_ref(kho, ma=("noi01", "nv01", "nv02")):
    for m in ma:
        p = kho.duong_ref("D1", m, ".png")
        p.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (64, 48)).save(p)


def test_gen_video_drama_gui_ref_theo_ts_dung_giay_khong_can_anh_duyet(tmp_path):
    vv = VeVideoGia()
    kho, c = _bo(tmp_path, vv=vv)
    _tap_drama(c)
    _bd(c)
    c.post("/api/tap/D1/C1/dong/0/prompt-drama")
    _ve_du_ref(kho)
    p1 = _clip(kho)
    c.patch(f"/api/tap/D1/C1/canh/{p1['id']}", json={"truong": {"gi": "10"}})
    r = c.post(f"/api/tap/D1/C1/canh/{p1['id']}/video", json={})
    assert r.status_code == 200, r.text
    g = vv.goi[0]
    assert [p.stem for p in g["anh"]] == ["noi01", "nv01", "nv02"], "nơi chốn trước, nhân vật theo Khung"
    assert g["giay"] == 10 and g["model"] == "grok-imagine-video-1.5"
    assert g["prompt"] == c.get(f"/api/tap/D1/C1/canh/{p1['id']}/prompt").json()["video"], \
        "thấy gì gửi nấy"
    assert _clip(kho)["vid"] == "task-drama-1"
    assert c.post(f"/api/tap/D1/C1/canh/{p1['id']}/video-kiem").json()["trang_thai"] == "xong"


def test_gen_video_drama_thieu_tam_nhan_vat_thi_chan_khong_ton_tien(tmp_path):
    vv = VeVideoGia()
    kho, c = _bo(tmp_path, vv=vv)
    _tap_drama(c)
    _bd(c)
    c.post("/api/tap/D1/C1/dong/0/prompt-drama")
    _ve_du_ref(kho, ("noi01", "nv01"))
    p1 = _clip(kho)
    r = c.post(f"/api/tap/D1/C1/canh/{p1['id']}/video", json={})
    assert r.status_code == 400 and "Marcus" in r.json()["detail"] and not vv.goi


def test_gen_video_drama_chua_viet_prompt_thi_chan(tmp_path):
    vv = VeVideoGia()
    kho, c = _bo(tmp_path, vv=vv)
    _tap_drama(c)
    _ve_du_ref(kho)
    r = c.post(f"/api/tap/D1/C1/canh/{_clip(kho)['id']}/video", json={})
    assert r.status_code == 400 and not vv.goi


# ═══════ dán lại SAU khi đã có prompt/video (kiểm thử editor 28/10) ═════════════════
BOT_CAU = KICH_BAN.replace('\nThoại: Tasha (sững rồi nhỏ mà chắc): "I went for water. Five minutes."', "")


def _co_video(kho, c, j=0):
    _bd(c)
    c.post("/api/tap/D1/C1/dong/0/prompt-drama")
    _ve_du_ref(kho)
    ma = _clip(kho, j=j)["id"]
    assert c.post(f"/api/tap/D1/C1/canh/{ma}/video", json={}).status_code == 200
    assert c.post(f"/api/tap/D1/C1/canh/{ma}/video-kiem").json()["trang_thai"] == "xong"
    return ma


def test_dan_lai_bot_cau_thoai_thi_bo_prompt_cu_va_bao_clip_doi(tmp_path):
    kho, c = _bo(tmp_path)
    _tap_drama(c)
    _bd(c)
    c.post("/api/tap/D1/C1/dong/0/prompt-drama")
    p1 = _clip(kho)
    r = c.post("/api/tap/D1/drama", json={"text": BOT_CAU})
    assert r.status_code == 200, r.text
    assert r.json()["doi"] == ["P001"] and r.json()["mat_prompt"] == ["P001"]
    assert not _clip(kho).get("pd") and _clip(kho, j=1).get("pd"), "clip không đổi giữ prompt"
    assert not _clip(kho).get("sh") and _clip(kho, j=1).get("sh"), "shot trỏ câu đã mất: breakdown lại"
    assert c.get(f"/api/tap/D1/C1/canh/{p1['id']}/prompt").json()["video"] == ""


def test_pd_cu_tro_cau_khong_con_thi_khong_chet(tmp_path):
    """Dữ liệu dán lại trước bản sửa: `pd` trỏ câu đã mất -> IndexError -> 500 ở mọi
    đường dựng prompt (xem prompt, gen video, đánh dấu cũ)."""
    kho, c = _bo(tmp_path)
    _tap_drama(c)
    _bd(c)
    c.post("/api/tap/D1/C1/dong/0/prompt-drama")
    d = kho.doc("D1", "C1")
    d["dong"][0]["canh"][0]["t"] = d["dong"][0]["canh"][0]["t"].split("\nThoại: Tasha")[0]
    kho.luu("D1", "C1", d["dong"], d["outline"], "minh")
    ma = _clip(kho)["id"]
    assert c.get(f"/api/tap/D1/C1/canh/{ma}/prompt").status_code == 200
    assert c.get("/api/tap/D1/C1/cu").status_code == 200
    _ve_du_ref(kho)
    assert c.post(f"/api/tap/D1/C1/canh/{ma}/video", json={}).status_code == 400


def test_video_drama_danh_dau_cu_khi_chu_clip_doi_sau_lan_gen(tmp_path):
    kho, c = _bo(tmp_path)
    _tap_drama(c)
    ma = _co_video(kho, c)
    cu = c.get("/api/tap/D1/C1/cu").json()
    assert cu[ma] == {"prompt": False, "anh": False, "video": False}
    r = c.post("/api/tap/D1/drama", json={"text": KICH_BAN.replace("Five minutes.", "Five minutes, sir.")})
    assert r.json()["doi"] == ["P001"] and r.json()["mat_prompt"] == []
    assert _clip(kho).get("sh"), "thoại giữ số câu, người nói: giữ mã người dựng đã chọn"
    cu = c.get("/api/tap/D1/C1/cu").json()
    assert cu[ma]["video"] is True and cu[ma]["prompt"] is True, "chữ clip đổi: prompt và video đều cũ"
    assert cu[_clip(kho, j=1)["id"]] == {"prompt": False, "anh": False, "video": False}
    c.post("/api/tap/D1/C1/dong/0/prompt-drama")
    assert c.get("/api/tap/D1/C1/cu").json()[ma]["prompt"] is False


def test_video_drama_danh_dau_cu_khi_doi_giay_hay_ve_lai_tam(tmp_path):
    kho, c = _bo(tmp_path)
    _tap_drama(c)
    ma = _co_video(kho, c)
    c.patch(f"/api/tap/D1/C1/canh/{ma}", json={"truong": {"gi": "10"}})
    assert c.get("/api/tap/D1/C1/cu").json()[ma]["video"] is True
    c.patch(f"/api/tap/D1/C1/canh/{ma}", json={"truong": {"gi": "15"}})
    assert c.get("/api/tap/D1/C1/cu").json()[ma]["video"] is False
    import os
    p = kho.duong_ref("D1", "nv02", ".png")
    os.utime(p, (p.stat().st_mtime + 60, p.stat().st_mtime + 60))
    assert c.get("/api/tap/D1/C1/cu").json()[ma]["video"] is True, "vẽ lại tấm: video dựng từ tấm cũ"


# ═══════ tài sản khuôn 2 ════════════════════════════════════════════════════════
def test_ref_nhan_vat_khuon_2_can_roi_toan_than_roi_ghep_tam_4_3(tmp_path):
    va = VeAnhGia()
    kho, c = _bo(tmp_path, va=va)
    _tap_drama(c)
    r = c.post("/api/tap/D1/so/nv01/ref-sinh")
    assert r.status_code == 200, r.text
    can, toan = va.goi
    assert can["ti_le"] == "1:1" and can["model"] == "gpt-image-2" and not can["ref"]
    assert "very large sharp close-up portrait of the face" in can["prompt"]
    assert "Beautiful Black woman about 28" in can["prompt"]
    assert toan["ti_le"] == "9:16" and toan["ref"] == [can["dich"]], "toàn thân SỬA TỪ ảnh cận"
    assert "Same person as in the image" in toan["prompt"]
    tam = Image.open(kho.ref_dang_co("D1", "nv01"))
    assert abs(tam.width / tam.height - 4 / 3) < 0.01


def test_ref_noi_chon_16_9_do_vat_1_1_nen_trang(tmp_path):
    va = VeAnhGia()
    kho, c = _bo(tmp_path, va=va)
    _tap_drama(c)
    so = kho.ds_so("D1")
    for x in so:
        if x["ma"] == "noi01":
            x["chu"] = "A private hospital room."
    kho.luu_so("D1", so + [{"ma": "hop", "loai": "dao_cu", "ten": "hộp", "chu": "a small red velvet ring box"}])
    assert c.post("/api/tap/D1/so/noi01/ref-sinh").status_code == 200
    assert c.post("/api/tap/D1/so/hop/ref-sinh").status_code == 200
    noi, hop = va.goi
    assert noi["ti_le"] == "16:9" and "No people" in noi["prompt"] and "A private hospital room." in noi["prompt"]
    assert hop["ti_le"] == "1:1" and "pure white seamless background" in hop["prompt"]


def test_ref_noi_chon_chua_co_chu_tieng_anh_thi_chan(tmp_path):
    _, c = _bo(tmp_path)
    _tap_drama(c)
    r = c.post("/api/tap/D1/so/noi01/ref-sinh")
    assert r.status_code == 400 and "Sinh Asset" in r.json()["detail"]


def test_ref_tap_cu_van_di_duong_cu(tmp_path):
    va = VeAnhGia()
    kho, c = _bo(tmp_path, va=va)
    kho.tao_tap("SE001", "cũ")
    kho.luu_so("SE001", [{"ma": "a", "loai": "nhan_vat", "ten": "A", "chu": "x", "pr": "OLD PROMPT"}])
    assert c.post("/api/tap/SE001/so/a/ref-sinh").status_code == 200
    assert [g["prompt"] for g in va.goi] == ["OLD PROMPT"] and va.goi[0]["ti_le"] is None


def test_viet_ho_so_khuon_2_drama_giu_cum_kich_ban_lay_giong(tmp_path):
    sa = SinhAssetGia()
    kho, c = _bo(tmp_path, sa=sa)
    _tap_drama(c)
    so = kho.ds_so("D1")
    for x in so:
        x["yc"] = x["yc"] or "y"
    kho.luu_so("D1", so)
    assert c.post("/api/tap/D1/so/nv01/sinh").status_code == 200
    x = {y["ma"]: y for y in kho.ds_so("D1")}["nv01"]
    assert x["chu"].startswith("Beautiful Black woman"), "cụm của kịch bản là nguồn, LLM không viết đè"
    assert x["tieng"] == "Tasha's voice: calm."
    assert x["pr"].startswith("Realistic photograph, a very large sharp close-up") and "Beautiful Black woman" in x["pr"]
    assert c.post("/api/tap/D1/so/noi01/sinh").status_code == 200
    n = {y["ma"]: y for y in kho.ds_so("D1")}["noi01"]
    assert n["chu"].startswith("A small hospital room") and n["pr"].startswith("Cinematic film still")


def test_rut_giay_lam_shot_qua_day_thi_bao(tmp_path):
    """Clip đã viết prompt 2 shot cho 15 giây, rút còn 6 thì vẫn vừa (2 × 2,5);
    clip 3 shot rút còn 6 thì không đủ chỗ — trang phải nhắc viết lại."""
    def ba_shot(than):
        r = _bd_dung(than)
        r["shots"].append({"t": "im", "co": "WS", "goc": "eye", "cd": "static", "cau": [], "ly_do": ""})
        return r
    kho, c = _bo(tmp_path, kt=KyThuatGia(bd=ba_shot))
    _tap_drama(c)
    _bd(c)
    p1 = _clip(kho)
    assert c.get("/api/tap/D1/C1").json()["dong"][0]["canh"][0]["day"] is False
    c.patch(f"/api/tap/D1/C1/canh/{p1['id']}", json={"truong": {"gi": "6"}})
    x = c.get("/api/tap/D1/C1").json()["dong"][0]["canh"][0]
    assert x["ns"] == 3 and x["day"] is True


# ═══════ narration khuôn 2: ảnh đánh số kèm lời dặn lấy gì, bỏ gì ══════════════
def test_prompt_anh_narration_khuon_2_danh_so_anh_va_dan_bo_dai_chu(tmp_path):
    """Tấm nhân vật khuôn Padoma có dải chữ "FICTIONAL CHARACTER SHEET…" và một người
    chụp hai lần — prompt cảnh phải dặn bỏ dải chữ, không thì model vẽ chữ / đẻ hai người."""
    from autoedit.treatment.tai_san import LOI_REF
    kho, c = _bo(tmp_path)
    c.post("/api/tap", json={"ma": "N1", "ten": "narration"})
    kho.luu_so("N1", [{"ma": "cap", "loai": "nhan_vat", "ten": "thuyền trưởng", "chu": "x"},
                      {"ma": "tau", "loai": "dao_cu", "ten": "tàu", "chu": "y"}])
    c.post("/api/tap/N1/chuong", json={"ma": "H"})
    c.put("/api/tap/N1/H", json={"outline": "", "dong": [
        {"en": "Voice.", "vi": "", "het": 0, "canh": [{"t": "a", "pa": "The captain climbs.", "ts": ["cap", "tau"]}]}]})
    ma = kho.doc("N1", "H")["dong"][0]["canh"][0]["id"]
    p = c.get(f"/api/tap/N1/H/canh/{ma}/prompt").json()["anh"]
    assert "Image 1" not in p, "chưa có ref thì không đánh số ảnh nào"
    for m in ("cap", "tau"):
        f = kho.duong_ref("N1", m, ".png"); f.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (8, 6)).save(f)
    p = c.get(f"/api/tap/N1/H/canh/{ma}/prompt").json()["anh"]
    assert LOI_REF["nhan_vat"].format(i=1) in p and LOI_REF["dao_cu"].format(i=2) in p
    assert p.index("The captain climbs.") < p.index("Image 1"), "câu KHUNG/pa vẫn đứng đầu (đo 27/09)"
    kho.tao_tap("CU", "cũ")
    kho.luu_so("CU", [{"ma": "cap", "loai": "nhan_vat", "ten": "x", "chu": "x"}])
    kho.luu("CU", "H", [{"en": "V.", "vi": "", "het": 0, "canh": [{"t": "a", "pa": "P.", "ts": ["cap"]}]}], "", "minh")
    f = kho.duong_ref("CU", "cap", ".png"); f.parent.mkdir(parents=True, exist_ok=True); Image.new("RGB", (8, 6)).save(f)
    ma2 = kho.doc("CU", "H")["dong"][0]["canh"][0]["id"]
    assert "Image 1" not in c.get(f"/api/tap/CU/H/canh/{ma2}/prompt").json()["anh"], "tập cũ giữ prompt cũ"


def test_trang_ghep_cung_loi_dan_anh_nhu_may_chu():
    """Trang tự ghép prompt ảnh (ghepPromptAnh) — CÙNG LUẬT với `_prompt_anh`: chữ
    lời dặn chép y hệt, đánh số theo đúng danh sách ảnh sẽ gửi, chỉ tập khuôn 2."""
    from autoedit.treatment.app import TRANG
    from autoedit.treatment.tai_san import LOI_REF
    h = TRANG.read_text(encoding="utf-8")
    for loai, chu in LOI_REF.items():
        assert json.dumps(chu, ensure_ascii=False) in h, loai
    i = h.index("function ghepPromptAnh(")
    assert "loiRef(x)" in h[i:h.index("\n}", i)]
    j = h.index("function loiRef(")
    than = h[j:h.index("\n}", j)]
    assert "anhSeGui(x)" in than and 'TAP_KHUON !== "2"' in than
