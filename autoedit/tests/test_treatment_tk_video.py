"""Tick tài khoản gen video theo CHƯƠNG (haint 03/11): hai tài khoản Lightvisual xoay vòng, một cái hết
gói là cứ hai lượt hỏng một — bấm hai lần. Mỗi chương tick tài khoản nào được dùng; mỗi ô có trạng thái
gen được hay không, tự đọc lại lúc 0h và 12h. Tài khoản đã tick mà đỏ thì máy tự bỏ qua (user chọn).
Lightvisual `/balance` (miễn phí) trả hạn gói từ 03/11; Seedvis đọc credit; Gensuite chưa có cách đọc.
Két giả, client giả — không mạng, không khoá thật.
"""

from __future__ import annotations

import itertools
import time

import pytest

import autoedit.treatment.app as mapp
from autoedit.aigen.client import AigenError
from autoedit.aigen.lightvisual import LightvisualClient
from autoedit.aigen.seedvis import SeedvisClient
from test_treatment_drama_api import _clip
from test_treatment_drama_shot_api import VeVideoI2v, _dan_duyet, _san
from test_treatment_gensuite import GS, LV, LV2, SV, SV_VIDEO, GROK, _ket, _viec


def _luc(ngay, gio, phut=0):
    return time.mktime((2026, 11, ngay, gio, phut, 0, 0, 0, -1))


@pytest.fixture
def tk(monkeypatch):
    """Số dư giả theo khoá + đếm số lần đọc; trạng thái đọc rồi bắt đầu trống mỗi test."""
    so = {"LV_k": {"credit": 0, "het_goi": _luc(3, 11, 30), "goi": "Grok Vô Hạn 1 ngày"},
          "LV_2": {"credit": 0, "het_goi": _luc(1, 11, 17), "goi": "Grok Vô Hạn 1 ngày"},
          "sv_video": {"credit": 500}}
    doc = []

    def tai_khoan(self):
        doc.append(self._key)
        return dict(so[self._key])
    monkeypatch.setattr(LightvisualClient, "tai_khoan", tai_khoan, raising=False)
    monkeypatch.setattr(SeedvisClient, "tai_khoan", tai_khoan)
    monkeypatch.setattr(mapp._VeVideo, "_TT", {}, raising=False)
    monkeypatch.setattr(mapp._VeVideo, "_LUOT", itertools.count(), raising=False)
    monkeypatch.setattr(mapp._VeVideo, "_VONG", {}, raising=False)
    _ket(monkeypatch, gen_video=_viec(LV, LV2, SV_VIDEO, GS), gen_canh=SV)
    return so, doc


def _tt(v, luc):
    return {x["id"]: (x["xanh"], x["chu"]) for x in v.tk_video(bay_gio=luc)}


def test_trang_thai_tung_tai_khoan(tk):
    v = mapp._VeVideo()
    ds = v.tk_video(bay_gio=_luc(3, 10))
    assert [(x["id"], x["nha"], x["ten"]) for x in ds] == [
        ("api-lv", "lightvisual", "Lightvisual · api-lv"), ("api-lv2", "lightvisual", "Lightvisual · api-lv2"),
        ("api-sv", "seedvis", "Seedvis · api-sv"), ("api-gs", "gensuite", "Gensuite · api-gs")]
    tt = _tt(v, _luc(3, 10))
    assert tt["api-lv"] == (True, "gói tới 11:30")
    assert tt["api-lv2"][0] is False and "hết gói" in tt["api-lv2"][1] and "01/11" in tt["api-lv2"][1]
    assert tt["api-sv"] == (True, "còn 500 cr")
    assert tt["api-gs"][0] is None, "Gensuite không đọc được số dư: chưa rõ, vẫn dùng được"


def test_doc_lai_luc_0h_va_12h_het_goi_doi_do_dung_gio(tk):
    so, doc = tk
    v = mapp._VeVideo()
    v.tk_video(bay_gio=_luc(3, 10))
    n = len(doc)
    assert _tt(v, _luc(3, 11))["api-lv"][0] is True and len(doc) == n, "trong cùng nửa ngày: không đọc lại"
    t = _tt(v, _luc(3, 11, 45))["api-lv"]
    assert t[0] is False and "hết gói lúc 11:30" in t[1] and len(doc) == n, "biết trước giờ hết: đổi đỏ ngay"
    so["LV_k"]["het_goi"] = _luc(4, 11, 30)              # mua gói mới lúc 11:50
    assert _tt(v, _luc(3, 11, 55))["api-lv"][0] is False and len(doc) == n, "chưa tới 12h thì chưa biết"
    assert _tt(v, _luc(3, 12, 1))["api-lv"] == (True, "gói tới 11:30 04/11") and len(doc) == 2 * n
    _tt(v, _luc(3, 23, 59))
    assert len(doc) == 2 * n
    _tt(v, _luc(4, 0, 1))
    assert len(doc) == 3 * n, "qua 0h đọc lại"
    v.tk_video(moi=True, bay_gio=_luc(4, 0, 2))
    assert len(doc) == 4 * n, "nút Kiểm lại: đọc ngay"


def test_gui_hong_vi_het_tien_danh_do_toi_moc_doc_lai(tk, monkeypatch):
    def hong(self, *a, **kw):
        raise AigenError("Lightvisual HTTP 402: {\"error\":\"Số dư không đủ cho request này\"}")
    monkeypatch.setattr(LightvisualClient, "gen_video_i2v", hong)
    so, _ = tk
    v = mapp._VeVideo()
    v.tk_video(bay_gio=_luc(3, 10))
    with pytest.raises(AigenError):
        v.bat_dau("p", "a.png", 6, False, model=GROK, nha="lightvisual", khoa="api-lv")
    t = _tt(v, _luc(3, 10, 30))["api-lv"]
    assert t[0] is False and "hết tiền" in t[1], "gói còn hạn mà gửi báo hết tiền: tin lỗi gửi"
    so["LV_k"]["het_goi"] = _luc(4, 11, 30)
    assert _tt(v, _luc(3, 12, 1))["api-lv"] == (True, "gói tới 11:30 04/11"), "qua mốc 12h: đọc lại, hết đỏ"


def test_task_hong_vi_het_tien_cung_danh_do(tk, monkeypatch):
    monkeypatch.setattr(LightvisualClient, "trang_thai_video",
                        lambda self, ma: {"status": "failed", "loi": "Số dư không đủ cho request này"})
    so, _ = tk
    so["LV_2"]["het_goi"] = _luc(3, 11, 17)
    v = mapp._VeVideo()
    v.tk_video(bay_gio=_luc(3, 10))
    assert v.trang_thai("lv_job_9@api-lv2")["status"] == "failed"
    tt = _tt(v, _luc(3, 10, 5))
    assert tt["api-lv2"][0] is False and "hết tiền" in tt["api-lv2"][1]
    assert tt["api-lv"][0] is True, "chỉ đánh đỏ đúng khoá đã nhận task"


def test_bat_dau_theo_khoa_chi_dinh(tk, monkeypatch):
    gui = []
    monkeypatch.setattr(LightvisualClient, "gen_video_i2v", lambda self, *a, **kw: gui.append(self._key) or "lv_job_1")
    v = mapp._VeVideo()
    assert v.bat_dau("p", "a.png", 6, False, model=GROK, nha="lightvisual", khoa="api-lv2") == "lv_job_1@api-lv2"
    assert v.bat_dau("p", "a.png", 6, False, model=GROK, nha="lightvisual", khoa="api-lv2") == "lv_job_1@api-lv2"
    assert gui == ["LV_2", "LV_2"], "chỉ định khoá thì không xoay vòng"


# ═══════ route: tick theo chương + gửi ═════════════════════════════════════════════════
class VeVideoTk(VeVideoI2v):
    """Bốn tài khoản; khoá trong `het` gửi là hỏng 402 và tự đánh đỏ như bộ thật."""

    def __init__(self):
        super().__init__()
        self.tk = [{"id": "a", "nha": "lightvisual", "ten": "Lightvisual · a", "xanh": True, "chu": "gói tới 11:30"},
                   {"id": "b", "nha": "lightvisual", "ten": "Lightvisual · b", "xanh": False, "chu": "hết gói lúc 11:17 01/11"},
                   {"id": "c", "nha": "seedvis", "ten": "Seedvis · c", "xanh": True, "chu": "còn 500 cr"},
                   {"id": "d", "nha": "gensuite", "ten": "Gensuite · d", "xanh": None, "chu": "chưa rõ"}]
        self.het, self.kiem = set(), 0

    def tk_video(self, moi=False):
        self.kiem += bool(moi)
        return [dict(x) for x in self.tk]

    def bat_dau(self, prompt, anh, giay, am, model=None, nha=None, khoa=None):
        if khoa in self.het:
            next(x for x in self.tk if x["id"] == khoa).update(xanh=False, chu="hết tiền lúc 11:00")
            raise RuntimeError("Lightvisual HTTP 402: Số dư không đủ")
        self.goi.append({"prompt": prompt, "giay": giay, "nha": nha, "khoa": khoa})
        return f"task-{len(self.goi)}@{khoa}"


def _shot(c, kho):
    _dan_duyet(c)
    p1 = _clip(kho)
    ds = c.get(f"/api/tap/D1/C1/canh/{p1['id']}/shot").json()
    goc = [f"/api/tap/D1/C1/canh/{p1['id']}/shot/{x['sid']}" for x in ds]
    for g in goc:
        c.post(g + "/anh")
        c.post(g + "/duyet")
    return goc


def test_chuong_luu_tick_va_tra_trang_thai(tmp_path):
    vv = VeVideoTk()
    kho, c = _san(tmp_path, vv=vv)
    r = c.get("/api/tap/D1/C1/tk-video")
    assert r.status_code == 200, r.text
    assert r.json()["tick"] == [] and [x["id"] for x in r.json()["ds"]] == ["a", "b", "c", "d"]
    assert not any(x["tick"] for x in r.json()["ds"])
    r = c.put("/api/tap/D1/C1/tk-video", json={"tick": ["c", "a", "zz"]})
    assert r.status_code == 200, r.text
    assert r.json()["tick"] == ["a", "c"], "đúng thứ tự két, bỏ khoá không còn"
    assert [x["id"] for x in c.get("/api/tap/D1/C1/tk-video").json()["ds"] if x["tick"]] == ["a", "c"]
    assert c.get("/api/tap/D1/C2/tk-video").json()["tick"] == [], "mỗi chương một bộ tick"
    assert c.post("/api/tap/D1/C1/tk-video/doc-lai").status_code == 200 and vv.kiem == 1
    c.headers.update({"X-Remote-Actions": ""})
    assert c.put("/api/tap/D1/C1/tk-video", json={"tick": ["a"]}).status_code == 403


def test_chuong_co_tick_bo_qua_tai_khoan_do_va_xoay_vong(tmp_path):
    vv = VeVideoTk()
    kho, c = _san(tmp_path, vv=vv)
    goc = _shot(c, kho)
    c.put("/api/tap/D1/C1/tk-video", json={"tick": ["a", "b", "c"]})
    for g in goc:
        assert c.post(g + "/video", json={"nha": "gensuite"}).status_code == 200
        c.post(g + "/video-kiem")
    assert len(goc) >= 2
    assert [(x["khoa"], x["nha"]) for x in vv.goi] == [[("a", "lightvisual"), ("c", "seedvis")][k % 2]
                                                        for k in range(len(goc))], \
        "b đỏ: bỏ qua; chương có tick thì nhà theo tài khoản, không theo hộp chọn"
    c.put("/api/tap/D1/C1/tk-video", json={"tick": ["b"]})
    r = c.post(goc[0] + "/video")
    assert r.status_code == 409 and "Lightvisual · b" in r.json()["detail"] and "hết gói" in r.json()["detail"]
    c.put("/api/tap/D1/C1/tk-video", json={"tick": []})
    assert c.post(goc[0] + "/video", json={"nha": "lightvisual"}).status_code == 200
    assert (vv.goi[-1]["nha"], vv.goi[-1]["khoa"]) == ("lightvisual", None), "không tick: như cũ"


def test_gui_hong_het_tien_tu_sang_tai_khoan_ke(tmp_path):
    vv = VeVideoTk()
    kho, c = _san(tmp_path, vv=vv)
    goc = _shot(c, kho)
    vv.het = {"a"}
    c.put("/api/tap/D1/C1/tk-video", json={"tick": ["a", "c"]})
    r = c.post(goc[0] + "/video")
    assert r.status_code == 200, r.text
    assert [x["khoa"] for x in vv.goi] == ["c"] and r.json()["vid"].endswith("@c"), "một lần bấm, một task"
    vv.het = {"c"}
    c.post(goc[0] + "/video-kiem")
    r = c.post(goc[0] + "/video")
    assert r.status_code == 409 and "Seedvis · c" in r.json()["detail"] and len(vv.goi) == 1


def test_gensuite_tick_thi_gui_10s(tmp_path):
    vv = VeVideoTk()
    kho, c = _san(tmp_path, vv=vv)
    goc = _shot(c, kho)
    c.put("/api/tap/D1/C1/tk-video", json={"tick": ["d"]})
    assert c.post(goc[0] + "/video").status_code == 200
    assert (vv.goi[-1]["nha"], vv.goi[-1]["giay"]) == ("gensuite", 10)
