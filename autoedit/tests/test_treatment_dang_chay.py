"""Thanh "Đang chạy" + chặn bấm trùng (user chốt 29/10: "ấn nút generate all hoặc bất kỳ nút
nào thì cũng phải có thanh trạng thái... người dùng dễ đè việc của nhau").

Máy chủ ghi sổ nút gen nào đang chạy, ai bấm, ở clip nào — mọi tab hỏi `/dang-chay` thấy
chung. Cùng clip, cùng việc mà người khác đang làm thì 409 thay vì chạy lần hai (tốn credit
hai lần, kết quả sau đè kết quả trước). Generate All chạy thì chặn nút gen tay trong chương
đó, và ngược lại. Đồ giả, không mạng.
"""

from __future__ import annotations

import pathlib
import threading
import time

from fastapi.testclient import TestClient

import autoedit.treatment.app as mapp
from test_treatment_chay_chuong import URL as URL_CHAY, _bo2, _cho_xong as _cho_chuong
from test_treatment_drama_api import KyThuatGia, VeAnhGia, VeVideoGia, _clip, _tap_drama
from test_treatment_drama_shot_api import KyThuatBoCuc, VeVideoI2v, _dan_duyet, _san

DANG = "/api/tap/D1/dang-chay"


class VeCho(VeAnhGia):
    """Vẽ đứng ở cổng: request dừng giữa chừng để soi sổ việc đang chạy."""

    def __init__(self):
        super().__init__()
        self.vao, self.cong, self.so_vao = threading.Event(), threading.Event(), 0

    def gen_anh(self, prompt, dich, **kw):
        self.so_vao += 1
        self.vao.set()
        self.cong.wait(10)
        return super().gen_anh(prompt, dich, **kw)


class KtCho(KyThuatBoCuc):
    """Breakdown đứng ở cổng ĐÚNG lượt đầu; lượt sau chạy thẳng."""

    def __init__(self):
        super().__init__()
        self.vao, self.cong = threading.Event(), threading.Event()

    def drama_breakdown(self, than):
        if not self.vao.is_set():
            self.vao.set()
            self.cong.wait(10)
        return super().drama_breakdown(than)


def _nen(c, url, **kw):
    """POST ở luồng khác — request đứng ở cổng mà test vẫn hỏi tiếp được."""
    kq = {}
    t = threading.Thread(target=lambda: kq.setdefault("r", c.post(url, **kw)), daemon=True)
    t.start()
    return t, kq


def _nguoi(c, ten, sua=True):
    k = TestClient(c.app)
    k.headers.update({"X-Remote-User": ten, "X-Remote-Actions": "sua" if sua else ""})
    return k


def _cho(dk, giay=5.0):
    het = time.time() + giay
    while time.time() < het:
        if dk():
            return
        time.sleep(0.02)
    raise AssertionError("chờ quá giờ")


def _id(kho, pm):
    return next(c["id"] for dg in kho.doc("D1", "C1")["dong"] for c in dg.get("canh") or [] if c.get("pm") == pm)


def _sid(c, ma, k=0):
    return c.get(f"/api/tap/D1/C1/canh/{ma}/shot").json()[k]["sid"]


def test_dung_code_cua_cay_dang_test():
    goc = pathlib.Path(__file__).resolve().parents[1]
    assert pathlib.Path(mapp.__file__).resolve().is_relative_to(goc), mapp.__file__


def test_nut_ve_anh_shot_dang_chay_moi_tab_deu_thay_bam_trung_thi_409_clip_khac_van_chay(tmp_path):
    va = VeCho()
    va.cong.set()
    kho, c = _san(tmp_path, va=va)
    _dan_duyet(c)
    va.cong.clear(); va.vao.clear(); va.so_vao = 0
    p1, p2 = _clip(kho, j=0)["id"], _clip(kho, j=1)["id"]
    s1 = _sid(c, p1)
    lan = _nguoi(c, "lan")
    assert c.get(DANG).json() == {"viec": [], "chuong": [], "asset": None}
    t1, k1 = _nen(c, f"/api/tap/D1/C1/canh/{p1}/shot/{s1}/anh")
    assert va.vao.wait(5)
    try:
        v = lan.get(DANG).json()["viec"]
        assert len(v) == 1, v
        assert {x: v[0][x] for x in ("viec", "ten", "ch", "i", "ma", "sid", "nguoi")} == \
            {"viec": "anh", "ten": "vẽ ảnh", "ch": "C1", "i": 0, "ma": p1, "sid": s1, "nguoi": "minh"}
        assert v[0]["cho"] == "C1 · P001 · shot 1", "người đọc: mã P + số thứ tự shot, không phải mã sid"
        assert v[0]["giay"] >= 0
        # Cùng shot, người khác bấm: KHÔNG gọi Seedvis lần hai.
        r = lan.post(f"/api/tap/D1/C1/canh/{p1}/shot/{s1}/anh")
        assert r.status_code == 409 and "minh đang vẽ ảnh" in r.json()["detail"], r.text
        assert va.so_vao == 1
        # Clip khác: chạy song song như cũ.
        t2, k2 = _nen(lan, f"/api/tap/D1/C1/canh/{p2}/shot/{_sid(c, p2)}/anh")
        _cho(lambda: va.so_vao == 2)
        assert {(x["ma"], x["nguoi"]) for x in c.get(DANG).json()["viec"]} == {(p1, "minh"), (p2, "lan")}
    finally:
        va.cong.set()
    t1.join(10); t2.join(10)
    assert k1["r"].status_code == 200 and k2["r"].status_code == 200, (k1["r"].text, k2["r"].text)
    assert c.get(DANG).json()["viec"] == [], "xong thì rời sổ"


def test_viec_hong_van_roi_so_nguoi_xem_khong_vao_so(tmp_path):
    class VeHong(VeAnhGia):
        def gen_anh(self, prompt, dich, **kw):
            raise RuntimeError("Seedvis 500")

    kho, c = _san(tmp_path, va=VeHong())
    assert c.post("/api/tap/D1/C1/dong/0/dan-canh").status_code == 502
    assert c.get(DANG).json()["viec"] == []
    assert c.post("/api/tap/D1/C1/dong/0/dan-canh").status_code == 502, "bấm lại được, không kẹt 409"
    xem = _nguoi(c, "an", sua=False)
    assert xem.post("/api/tap/D1/C1/dong/0/dan-canh").status_code == 403
    assert c.get(DANG).json()["viec"] == []


def test_breakdown_ca_canh_chan_breakdown_va_viet_prompt_clip_trong_canh_do_canh_khac_van_chay(tmp_path):
    kt = KtCho()
    kho, c = _bo2(tmp_path, kt=kt)
    lan = _nguoi(c, "lan")
    t, k = _nen(c, "/api/tap/D1/C1/dong/0/breakdown")
    assert kt.vao.wait(5)
    try:
        v = lan.get(DANG).json()["viec"]
        assert [(x["viec"], x["i"], x["ma"]) for x in v] == [("breakdown", 0, "")], v
        p1 = _id(kho, "P001")
        for duoi in ("breakdown", "prompt-drama"):        # cả hai viết lại chữ của clip
            r = lan.post(f"/api/tap/D1/C1/canh/{p1}/{duoi}")
            assert r.status_code == 409 and "minh đang breakdown" in r.json()["detail"], (duoi, r.text)
        r = lan.post(f"/api/tap/D1/C1/canh/{_id(kho, 'P003')}/breakdown")
        assert r.status_code == 200, "cảnh khác không dính"
    finally:
        kt.cong.set()
    t.join(10)
    assert k["r"].status_code == 200, k["r"].text


def test_generate_all_chay_thi_chan_nut_tay_trong_chuong_va_thanh_hien_tien_do(tmp_path):
    va = VeCho()
    kho, c = _bo2(tmp_path, va=va)
    assert c.post(URL_CHAY).status_code == 200
    assert va.vao.wait(5)
    try:
        lan = _nguoi(c, "lan")
        g = lan.get(DANG).json()["chuong"]
        assert len(g) == 1 and g[0]["ch"] == "C1" and g[0]["nguoi"] == "minh" and g[0]["buoc"] == "dan", g
        assert {"xong", "tong", "loi", "giay"} <= set(g[0])
        for url in ("/api/tap/D1/C1/dong/0/dan-canh", f"/api/tap/D1/C1/canh/{_id(kho, 'P001')}/breakdown"):
            r = lan.post(url)
            assert r.status_code == 409 and "minh đang Generate All chương C1" in r.json()["detail"], (url, r.text)
    finally:
        va.cong.set()
    _cho_chuong(c)
    assert c.get(DANG).json()["chuong"] == []


def test_nut_tay_dang_chay_thi_chua_generate_all(tmp_path):
    va = VeCho()
    kho, c = _san(tmp_path, va=va)
    t, k = _nen(c, "/api/tap/D1/C1/dong/0/dan-canh")
    assert va.vao.wait(5)
    try:
        r = _nguoi(c, "lan").post(URL_CHAY)
        assert r.status_code == 409 and "minh đang vẽ ảnh dàn cảnh" in r.json()["detail"], r.text
    finally:
        va.cong.set()
    t.join(10)
    assert k["r"].status_code == 200


def test_gen_toan_bo_asset_va_ve_ref_le_chan_nhau(tmp_path):
    va = VeCho()
    kho, c = _bo2(tmp_path, kt=KyThuatGia(), va=va, tam=())
    lan = _nguoi(c, "lan")
    t, k = _nen(c, "/api/tap/D1/so/nv01/ref-sinh")
    assert va.vao.wait(5)
    try:
        v = lan.get(DANG).json()["viec"]
        assert [(x["viec"], x["ten"], x["ch"], x["ma"]) for x in v] == [("ref", "vẽ ảnh ref", "", "nv01")], v
        r = lan.post("/api/tap/D1/so/tat-ca", json={})
        assert r.status_code == 409 and "minh đang vẽ ảnh ref" in r.json()["detail"], r.text
    finally:
        va.cong.set()
    t.join(10)
    assert k["r"].status_code == 200, k["r"].text
    va.cong.clear(); va.vao.clear()
    assert c.post("/api/tap/D1/so/tat-ca", json={}).status_code == 200
    assert va.vao.wait(5)
    try:
        a = lan.get(DANG).json()["asset"]
        assert a["nguoi"] == "minh" and {"buoc", "xong", "tong", "loi", "giay"} <= set(a), a
        r = lan.post("/api/tap/D1/so/nv02/ref-sinh")
        assert r.status_code == 409 and "minh đang gen toàn bộ asset" in r.json()["detail"], r.text
    finally:
        va.cong.set()
    _cho(lambda: not c.get("/api/tap/D1/so/tat-ca").json()["viec"]["chay"], 10)


def test_video_dang_dung_thi_gui_lai_409_khong_tra_tien_hai_lan(tmp_path):
    vv = VeVideoI2v()
    kho, c = _san(tmp_path, vv=vv)
    _dan_duyet(c)
    p1 = _clip(kho)["id"]
    s1 = _sid(c, p1)
    goc = f"/api/tap/D1/C1/canh/{p1}/shot/{s1}"
    assert c.post(goc + "/anh").status_code == 200 and c.post(goc + "/duyet").status_code == 200
    assert c.post(goc + "/video").status_code == 200
    r = _nguoi(c, "lan").post(goc + "/video")
    assert r.status_code == 409 and "đang dựng video" in r.json()["detail"], r.text
    assert len(vv.goi) == 1
    # Clip drama dựng cả clip (đường Grok ảnh tham chiếu) — cùng luật.
    vg = VeVideoGia()
    kho2, c2 = _san(tmp_path / "b", vv=vg)
    p = _clip(kho2)["id"]
    assert c2.post(f"/api/tap/D1/C1/canh/{p}/video").status_code == 200
    r = c2.post(f"/api/tap/D1/C1/canh/{p}/video")
    assert r.status_code == 409 and "đang dựng video" in r.json()["detail"], r.text
    assert len(vg.goi) == 1
