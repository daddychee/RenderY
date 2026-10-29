"""Nút "Chạy tới duyệt ảnh" của một chương drama (user chốt 29/10): Breakdown → Viết prompt
cảnh → vẽ ảnh dàn cảnh → MÁY TỰ DUYỆT dàn cảnh → vẽ ảnh khung đầu mọi shot; dừng ở duyệt
ảnh shot. Không duyệt shot hộ, không gọi video. Đồ giả thay LLM / Seedvis — không mạng.
"""

from __future__ import annotations

import itertools
import json
import pathlib
import threading
import time

import autoedit.treatment.app as mapp
from test_treatment_drama import KICH_BAN
from test_treatment_drama_api import VeAnhGia, VeVideoGia, _bo, _clip, _ve_du_ref
from test_treatment_drama_shot_api import KyThuatBoCuc, VeVideoI2v

# Chương C1 có HAI cảnh: C001 (Tasha, Marcus · P001 2 shot, P002 1 shot) và C002 BA người
# (P003 2 shot) — cảnh từ 3 người là chỗ khung cắt mặc định chưa tin (luật cứng 5).
CANH_3_NGUOI = '''## C002 · bếp nhà Tasha · trưa · N02
Có mặt: Tasha, Marcus, Ruth

### P003 · Marcus đứng chờ
Máy: Grok 10s
Khung: Tasha, Marcus, Ruth
Hình: shot 1 trung ba người bên bàn bếp. Shot 2 cận Marcus.
Thoại: Tasha (khẽ): "You came."
Thoại: Marcus (lạnh): "We need to talk."

## Ghi chú nối'''
HAI_CANH = (KICH_BAN.replace("## C002 ·", "## C003 ·").replace("### P003 ·", "### P004 ·")
            .replace("## Ghi chú nối", CANH_3_NGUOI, 1)
            .replace("| Marcus (he) | con trai bà Ruth | 45 tuổi, vest xám | nam 45 tuổi, trầm, gọn, giọng Atlanta |",
                     "| Marcus (he) | con trai bà Ruth | 45 tuổi, vest xám | nam 45 tuổi, trầm, gọn, giọng Atlanta |\n"
                     "| Ruth (she) | mẹ Marcus | 75 tuổi, tóc bạc | nữ 75 tuổi, yếu, khàn |")
            .replace("| NV02 | Marcus (he) |", "| NV03 | Ruth (she) | Elderly Black woman about 75, short silver "
                     "hair, lavender cardigan | |\n| NV02 | Marcus (he) |"))
TAM = ("noi01", "noi02", "nv01", "nv02", "nv03")
URL = "/api/tap/D1/C1/chay"


def _bo2(tmp_path, kt=None, va=None, vv=None, tam=TAM):
    kho, c = _bo(tmp_path, kt=kt or KyThuatBoCuc(), va=va, vv=vv)
    assert c.post("/api/tap", json={"ma": "D1", "ten": "Hộp nhẫn", "loai": "drama"}).status_code == 200
    r = c.post("/api/tap/D1/drama", json={"text": HAI_CANH})
    assert r.status_code == 200, r.text
    _ve_du_ref(kho, tam)
    return kho, c


def _cho_xong(c, giay=15.0):
    het = time.time() + giay
    while time.time() < het:
        v = c.get(URL).json()["viec"]
        if v and not v["chay"]:
            return v
        time.sleep(0.05)
    raise AssertionError("việc chạy chương chưa xong")


def _chay(c):
    r = c.post(URL)
    assert r.status_code == 200, r.text
    return _cho_xong(c)


def _clip_c1(kho):
    return [c for dg in kho.doc("D1", "C1")["dong"] for c in dg.get("canh") or []]


def _anh_shot(kho):
    """{(pm, sid): có ảnh} của mọi shot C1."""
    return {(c["pm"], s["sid"]): kho.duong_anh("D1", f"{c['id']}-{s['sid']}").exists()
            for c in _clip_c1(kho) for s in json.loads(c.get("sh") or "[]")}


def _dan(c, i):
    return c.get(f"/api/tap/D1/C1/dong/{i}/dan-canh").json()


def test_dung_code_cua_cay_dang_test():
    """Venv dùng chung giữa các cây: phải nạp `autoedit` của CHÍNH cây chứa test này."""
    goc = pathlib.Path(__file__).resolve().parents[1]
    assert pathlib.Path(mapp.__file__).resolve().is_relative_to(goc), mapp.__file__


def test_ke_hoach_dem_clip_anh_credit_phut_truoc_khi_bam(tmp_path):
    kho, c = _bo2(tmp_path)
    r = c.get(URL).json()
    assert r["viec"] is None
    k = r["ke_hoach"]
    # Shot của clip CHƯA Breakdown ước theo "shot N" ở dòng Hình: (P001 2, P002 không ghi -> 1, P003 2).
    assert {x: k[x] for x in ("dong", "clip", "breakdown", "prompt", "dan", "shot", "anh")} == \
        {"dong": 2, "clip": 3, "breakdown": 3, "prompt": 3, "dan": 2, "shot": 5, "anh": 7}
    assert k["model"] == "gpt-image-2" and k["credit"] == 7 * 5, "GPT Image 2 sửa từ ảnh: 5 cr/ảnh"
    assert k["phut"] == 4, "2 cảnh LLM chạy 2 một lúc (~3 phút) + 7 ảnh / 6 luồng"
    assert k["it_chac"] == [{"i": 1, "ten": "C002 · bếp nhà Tasha · trưa · N02", "nguoi": 3}]
    assert k["may_duyet"] == [] and k["cho_duyet"] == 0


def test_mot_lan_bam_toi_duyet_anh_shot_may_tu_duyet_dan_canh_khong_duyet_shot_khong_video(tmp_path):
    va, vv, kt = VeAnhGia(), VeVideoI2v(), KyThuatBoCuc()
    kho, c = _bo2(tmp_path, kt=kt, va=va, vv=vv)
    v = _chay(c)
    assert v["loi"] == [], v["loi"]
    for x in _clip_c1(kho):
        assert x.get("sh") and x.get("pd"), x["pm"]
    anh = _anh_shot(kho)
    assert len(anh) == 5 and all(anh.values()), anh
    assert all(not s["duyet"] for x in _clip_c1(kho)
               for s in c.get(f"/api/tap/D1/C1/canh/{x['id']}/shot").json()), "KHÔNG duyệt ảnh shot hộ"
    assert not vv.goi, "KHÔNG gọi video"
    for i in (0, 1):
        d = _dan(c, i)
        assert d["co_anh"] and d["duyet"] and d["may_duyet"], (i, d)
    # Luật cứng 5: kết quả liệt kê cảnh MÁY duyệt; cảnh 3 người đánh dấu.
    md = {x["i"]: x for x in v["may_duyet"]}
    assert set(md) == {0, 1} and md[1]["nguoi"] == 3 and md[0]["nguoi"] == 2
    assert md[0]["ten"].startswith("C001") and md[0]["td"] == _dan(c, 0)["td"] and not md[0]["co_san"]
    # Dấu máy nằm trong KHO (restart xong vẫn thấy); người bấm Duyệt thì thôi là dấu máy.
    assert [(x["i"], x["nguoi"]) for x in c.get(URL).json()["ke_hoach"]["may_duyet"]] == [(0, 2), (1, 3)]
    assert c.post("/api/tap/D1/C1/dong/1/dan-canh/duyet").status_code == 200
    assert _dan(c, 1)["duyet"] and not _dan(c, 1)["may_duyet"]
    assert [x["i"] for x in c.get(URL).json()["ke_hoach"]["may_duyet"]] == [0]
    # Không làm gì thêm: bấm lại báo đã tới bước duyệt ảnh shot, không gọi LLM/ảnh.
    n = (len(kt.bd), len(kt.canh), len(kt.clip), len(va.goi))
    r = c.post(URL)
    assert r.status_code == 400 and "duyệt ảnh shot" in r.json()["detail"]
    assert (len(kt.bd), len(kt.canh), len(kt.clip), len(va.goi)) == n


def test_bam_lai_chi_lam_phan_thieu_khong_breakdown_lai_khong_viet_lai(tmp_path):
    va, kt = VeAnhGia(), KyThuatBoCuc()
    kho, c = _bo2(tmp_path, kt=kt, va=va)
    _chay(c)
    sh = {x["pm"]: x["sh"] for x in _clip_c1(kho)}
    p3 = next(x for x in _clip_c1(kho) if x["pm"] == "P003")
    sid = json.loads(p3["sh"])[1]["sid"]
    kho.duong_anh("D1", f"{p3['id']}-{sid}").unlink()           # một ảnh shot mất
    assert c.get(URL).json()["ke_hoach"]["shot"] == 1
    n = (len(kt.bd), len(kt.canh), len(kt.clip), len(va.goi))
    v = _chay(c)
    assert v["loi"] == [] and v["may_duyet"] == []
    assert (len(kt.bd), len(kt.canh), len(kt.clip)) == n[:3], "không gọi LLM khi shot + prompt đã đủ"
    assert len(va.goi) == n[3] + 1 and va.goi[-1]["dich"].name == f"{p3['id']}-{sid}.png"
    assert {x["pm"]: x["sh"] for x in _clip_c1(kho)} == sh, "sid giữ nguyên"


def test_canh_da_co_bo_cuc_giu_khung_da_keo_va_duyet_cua_nguoi(tmp_path):
    kt = KyThuatBoCuc()
    kho, c = _bo2(tmp_path, kt=kt)
    assert c.post("/api/tap/D1/C1/dong/0/breakdown").status_code == 200
    assert c.post("/api/tap/D1/C1/dong/0/prompt-drama").json()["viet"] == 2
    assert c.post("/api/tap/D1/C1/dong/0/dan-canh").status_code == 200
    hop = [0.05, 0.2, 0.45, 0.6]
    assert c.put("/api/tap/D1/C1/dong/0/dan-canh/cat", json={"cat": {"Tasha": hop}}).status_code == 200
    assert c.post("/api/tap/D1/C1/dong/0/dan-canh/duyet").status_code == 200
    p2 = _clip(kho, j=1)
    pd2 = p2["pd"]
    n_canh = len(kt.canh)
    v = _chay(c)
    assert v["loi"] == [], v["loi"]
    assert len(kt.canh) == n_canh + 1, "chỉ cảnh CHƯA có bố cục mới viết phần chung"
    assert _clip(kho, j=1)["pd"] == pd2 and json.loads(_clip(kho)["pd"])["cat"]["Tasha"] == hop
    assert _dan(c, 0)["duyet"] and not _dan(c, 0)["may_duyet"], "người đã duyệt: không thành dấu máy"
    assert [x["i"] for x in v["may_duyet"]] == [1]


def test_clip_doi_chu_sau_breakdown_khong_breakdown_lai_ma_bao(tmp_path):
    kt = KyThuatBoCuc()
    kho, c = _bo2(tmp_path, kt=kt)
    assert c.post("/api/tap/D1/C1/dong/0/breakdown").status_code == 200
    p1 = _clip(kho)
    t = p1["t"].replace('\nThoại: Tasha (sững rồi nhỏ mà chắc): "I went for water. Five minutes."', "")
    assert c.patch(f"/api/tap/D1/C1/canh/{p1['id']}", json={"truong": {"t": t}}).status_code == 200
    n_bd = len(kt.bd)
    v = _chay(c)
    assert _clip(kho)["sh"] == p1["sh"], "Breakdown lại là mất ảnh / duyệt / video của shot"
    assert len(kt.bd) == n_bd + 1, "chỉ P003 chưa Breakdown"
    assert any("P001" in x["loi"] and "Breakdown lại bằng tay" in x["loi"] for x in v["loi"]), v["loi"]


def test_mot_clip_hong_mot_canh_thieu_tam_khong_giet_ca_chuong(tmp_path):
    class KtHong(KyThuatBoCuc):
        def drama_breakdown(self, than):
            if "### P001" in than:
                raise RuntimeError("LLM 500 <thử>")
            return super().drama_breakdown(than)

    vv = VeVideoGia()
    kho, c = _bo2(tmp_path, kt=KtHong(), vv=vv, tam=("noi01", "noi02", "nv01", "nv02"))   # thiếu tấm Ruth
    v = _chay(c)
    chu = " | ".join(x["ten"] + ": " + x["loi"] for x in v["loi"])
    assert "P001: breakdown hỏng: LLM 500 <thử>" in chu and "Ruth" in chu, chu
    anh = _anh_shot(kho)
    p2 = _clip(kho, j=1)
    assert [k for k, x in anh.items() if x] == [("P002", json.loads(p2["sh"])[0]["sid"])], "P002 vẫn tới ảnh shot"
    assert [x["i"] for x in v["may_duyet"]] == [0] and not _dan(c, 1)["co_anh"]
    assert not vv.goi


def test_nhieu_canh_song_song_khong_mat_truong_doan_trong_so(tmp_path):
    """`ve_dan_canh` đọc-vá-ghi CẢ sổ: hai cảnh vẽ cùng lúc mà không khoá thì cảnh ghi SAU
    cầm bản sổ đọc TRƯỚC khi cảnh kia ghi — mục `td` của cảnh kia mất."""
    kho, c = _bo2(tmp_path)
    doc, ghi, luot = kho.ds_so, kho.luu_so, itertools.count()

    def doc_cham(tap):
        ra = doc(tap)
        time.sleep(0.05)            # hai luồng đều đọc xong trước khi ai kịp ghi
        return ra

    def ghi_lech(tap, so):
        time.sleep(0.1 * next(luot))      # lượt ghi sau tới muộn hơn hẳn lượt trước
        ghi(tap, so)
    kho.ds_so, kho.luu_so = doc_cham, ghi_lech
    v = _chay(c)
    kho.ds_so, kho.luu_so = doc, ghi
    td = {x["ma"] for x in kho.ds_so("D1") if x["loai"] == "truong_doan"}
    assert td == {_dan(c, 0)["td"], _dan(c, 1)["td"]}, (td, v["loi"])

def test_het_credit_lien_3_lan_thi_dung_ve(tmp_path, monkeypatch):
    class VeHetTien(VeAnhGia):
        hong: list = []

        def gen_anh(self, prompt, dich, **kw):
            if not dich.stem.startswith("td_"):         # ảnh dàn cảnh qua, ảnh shot hết tiền
                self.hong.append(dich)
                raise RuntimeError("insufficient credits")
            return super().gen_anh(prompt, dich, **kw)

    monkeypatch.setattr(mapp, "LUONG_ANH_CHUONG", 1)
    va = VeHetTien()
    kho, c = _bo2(tmp_path, va=va)
    v = _chay(c)
    assert len(va.hong) == mapp.PHANH == 3, "5 shot mà chỉ gửi 3 lượt rồi dừng"
    assert any("Dừng" in x["ten"] for x in v["loi"]), v["loi"]


def test_llm_hong_lien_thi_dung_goi_llm(tmp_path, monkeypatch):
    class KtHetQuota(KyThuatBoCuc):
        def drama_breakdown(self, than):
            self.bd.append(than)
            raise RuntimeError("HTTP 429 API_KEY_QUOTA_EXHAUSTED")

    monkeypatch.setattr(mapp, "LUONG_LLM_CHUONG", 1)
    monkeypatch.setattr(mapp, "PHANH", 2)
    kt = KtHetQuota()
    kho, c = _bo2(tmp_path, kt=kt)
    v = _chay(c)
    assert len(kt.bd) == 2, "cảnh 1 hỏng 2 lượt liền -> cảnh 2 không gọi nữa"
    assert any("Dừng" in x["ten"] for x in v["loi"]), v["loi"]


def test_quyen_khoa_dang_chay_va_tap_narration(tmp_path):
    class VeCho(VeAnhGia):
        def __init__(self):
            super().__init__()
            self.cong = threading.Event()

        def gen_anh(self, prompt, dich, **kw):
            self.cong.wait(10)
            return super().gen_anh(prompt, dich, **kw)

    va = VeCho()
    kho, c = _bo2(tmp_path, va=va)
    xem = c.post(URL, headers={"X-Remote-Actions": ""})
    assert xem.status_code == 403
    kho.giu("D1", "C1", "lan")
    r = c.post(URL)
    assert r.status_code == 409 and "lan" in r.json()["detail"]
    kho.nha("D1", "C1", "lan")
    assert c.post(URL).status_code == 200
    try:
        r = c.post(URL)
        assert r.status_code == 409 and "đang Generate All chương C1" in r.json()["detail"], r.text
        r = c.put("/api/tap/D1/so", json={"so": kho.ds_so("D1")})
        assert r.status_code == 409 and "đang Generate All chương C1" in r.json()["detail"], r.text
        assert c.post("/api/tap/D1/drama", json={"text": HAI_CANH}).status_code == 409
        assert c.post("/api/tap/D1/so/tat-ca", json={}).status_code == 409
        v = c.get(URL).json()["viec"]
        assert v["chay"] and v["nguoi"] == "minh"
    finally:
        va.cong.set()
    _cho_xong(c)
    assert c.put("/api/tap/D1/so", json={"so": kho.ds_so("D1")}).status_code == 200
    assert c.post("/api/tap", json={"ma": "N1", "ten": "narration"}).status_code == 200
    kho.tao_chuong("N1", "C1")
    assert c.post("/api/tap/N1/C1/chay").status_code == 400


def test_asset_dang_gen_thi_chua_chay_chuong(tmp_path):
    class VeCho(VeAnhGia):
        def __init__(self):
            super().__init__()
            self.cong = threading.Event()

        def gen_anh(self, prompt, dich, **kw):
            self.cong.wait(10)
            return super().gen_anh(prompt, dich, **kw)

    va = VeCho()
    kho, c = _bo2(tmp_path, va=va, tam=("noi01",))
    assert c.post("/api/tap/D1/so/tat-ca", json={}).status_code == 200
    try:
        r = c.post(URL)
        assert r.status_code == 409 and "asset" in r.json()["detail"]
    finally:
        va.cong.set()
    het = time.time() + 10
    while c.get("/api/tap/D1/so/tat-ca").json()["viec"]["chay"] and time.time() < het:
        time.sleep(0.05)

