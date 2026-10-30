"""Chọn NHÀ gen video khi bấm nút (user 30/10): Seedvis / Lightvisual / Gensuite (Muse).

Không truyền nhà thì y như cũ (Grok đi Lightvisual khi két có khoá, còn lại Seedvis). Chọn nhà chưa có
khoá -> lỗi rõ chỉ chỗ cấp ở General, KHÔNG tự đổi sang nhà khác (luật cứng 5). Gensuite luôn 10 s:
prompt và độ dài gửi đi ghép lại theo 10 s, độ dài người dựng chọn trong kho giữ nguyên.
Két giả, client giả — không mạng, không khoá thật.
"""

from __future__ import annotations

import itertools
import pathlib
import re

import pytest

import autoedit.treatment.app as mapp
from autoedit.aigen.client import ArkClient
from autoedit.aigen.gensuite import GensuiteClient
from autoedit.aigen.lightvisual import LightvisualClient
from autoedit.aigen.seedvis import SeedvisClient
from autoedit.treatment import dich as mdich
from test_treatment_drama_api import _clip
from test_treatment_drama_shot_api import VeVideoI2v, _dan_duyet, _san

GS_URL = "https://supabase-staging.gensuite.site/functions/v1/api-v1"
LV = {"id": "api-lv", "key": "LV_k", "base_url": "https://lightvisual.studio/v1", "nha": "lightvisual"}
LV2 = dict(LV, id="api-lv2", key="LV_2")
GS = {"id": "api-gs", "key": "GS_k", "base_url": GS_URL, "nha": "gensuite"}
GS2 = dict(GS, id="api-gs2", key="GS_2")
SV_VIDEO = {"id": "api-sv", "key": "sv_video", "base_url": "https://seedvis.com/api/v1", "nha": "seedvis"}
SV = {"key": "sv_k", "base_url": "https://seedvis.com/api/v1", "model": "gpt-image-2"}
GROK = "grok-imagine-video-1.5"
URL_TAI = {"lv": "https://lightvisual.studio/v1/videos/{}/content", "sv": "https://cdn.seedvis.com/{}.mp4",
           "gs": "https://scontent.xx.fbcdn.net/{}.mp4", "ark": "https://ark/{}.mp4"}


def _viec(*khoa):
    """Hình dạng thật của `doc_ket_viec`: khoá đầu ở ngoài + `ds` đủ danh sách."""
    return {"key": khoa[0]["key"], "base_url": khoa[0]["base_url"], "model": "xai/" + GROK, "ds": list(khoa),
            "che_do": "rotate"}


def _ket(monkeypatch, **viec):
    monkeypatch.setattr(mdich, "doc_ket_viec", lambda v="dich": dict(viec.get(v) or {}))


@pytest.fixture
def goi(monkeypatch):
    """Ghi (nhà, hàm, khoá, đối số đầu, kw) thay vì gọi mạng; vòng xoay khoá bắt đầu lại mỗi test."""
    ds = []
    monkeypatch.setattr(mapp._VeVideo, "_LUOT", itertools.count(), raising=False)
    monkeypatch.setattr(mapp._VeVideo, "_VONG", {}, raising=False)
    for lop, nha, tien_to in ((LightvisualClient, "lv", "lv_job_"), (SeedvisClient, "sv", "sv-"),
                              (GensuiteClient, "gs", "gs_"), (ArkClient, "ark", "ark-")):
        for ham in ("gen_video_i2v", "gen_video_ref", "trang_thai_video", "tai_video"):
            def gia(self, *a, _n=nha, _h=ham, _t=tien_to, **kw):
                ds.append((_n, _h, self._key, a[0] if a else None, kw))
                if _h == "trang_thai_video":
                    return {"status": "succeeded", "video_url": URL_TAI[_n].format(a[0])}
                return f"{_t}{len(ds)}" if _h.startswith("gen_") else "ok"
            monkeypatch.setattr(lop, ham, gia, raising=False)
    return ds


def _nhk(goi):
    return [(n, h, k) for n, h, k, _, _ in goi]


def test_dung_code_cua_cay_dang_test():
    goc = pathlib.Path(__file__).resolve().parents[1]
    assert pathlib.Path(mapp.__file__).resolve().is_relative_to(goc), mapp.__file__


# ═══════ _VeVideo: nhà tường minh ══════════════════════════════════════════════════
def test_chon_nha_tuong_minh_moi_nha_mot_duong(monkeypatch, goi):
    _ket(monkeypatch, gen_video=_viec(LV, GS), gen_canh=SV)
    v = mapp._VeVideo()
    ra = [v.bat_dau("p", "a.png", 10, False, model=GROK, nha="gensuite"),
          v.bat_dau("p", "a.png", 6, False, model=GROK, nha="lightvisual"),
          v.bat_dau("p", "a.png", 6, False, model=GROK, nha="seedvis"),
          v.bat_dau_ref("p", ["a.png"], 10, model=GROK, nha="gensuite")]
    assert _nhk(goi) == [("gs", "gen_video_i2v", "GS_k"), ("lv", "gen_video_i2v", "LV_k"),
                         ("sv", "gen_video_i2v", "sv_k"), ("gs", "gen_video_ref", "GS_k")]
    assert ra == ["gs_1@api-gs", "lv_job_2@api-lv", "sv-3", "gs_4@api-gs"], "mã Gensuite mang id khoá như Lightvisual"
    assert goi[2][4]["model"] == GROK, "Seedvis chạy Grok của shot drama"


def test_ket_that_bon_khoa_ba_nha_moi_nha_xoay_trong_khoa_cua_minh(monkeypatch, goi, tmp_path):
    """Két thật 30/10 18:03: gen_video = lightvisual, lightvisual, gensuite, seedvis (chế độ rotate).
    Seedvis chọn tay đi khoá seedvis của gen_video và mã mang id khoá đó (hỏi đúng tài khoản);
    không chọn nhà thì y cũ — Grok xoay hai khoá Lightvisual, Omni và task Seedvis cũ đi gen_canh."""
    _ket(monkeypatch, gen_video=_viec(LV, LV2, GS, SV_VIDEO), gen_canh=SV)
    v = mapp._VeVideo()
    ra = [v.bat_dau("p", "a.png", 6, False, model=GROK, nha="lightvisual"),
          v.bat_dau("p", "a.png", 10, False, model=GROK, nha="gensuite"),
          v.bat_dau("p", "a.png", 6, False, model=GROK, nha="lightvisual"),
          v.bat_dau("p", "a.png", 6, False, model=GROK, nha="seedvis"),
          v.bat_dau("p", "a.png", 6, False, model=GROK),
          v.bat_dau("p", "a.png", 8, True, model="Omni-Flash")]
    assert _nhk(goi) == [("lv", "gen_video_i2v", "LV_k"), ("gs", "gen_video_i2v", "GS_k"),
                         ("lv", "gen_video_i2v", "LV_2"), ("sv", "gen_video_i2v", "sv_video"),
                         ("lv", "gen_video_i2v", "LV_k"), ("sv", "gen_video_i2v", "sv_k")], \
        "gửi Gensuite xen giữa không làm lệch vòng Lightvisual"
    assert ra[3] == "sv-4@api-sv" and ra[5] == "sv-6", "Seedvis gen_canh như cũ: mã không gắn khoá"
    goi.clear()
    for tid in (ra[3], "0b6c9e1f-seedvis"):
        v.tai_ve(v.trang_thai(tid)["video_url"], tmp_path / "a.mp4")
    assert [(n, h, k, a) for n, h, k, a, _ in goi][::2] == [
        ("sv", "trang_thai_video", "sv_video", "sv-4"), ("sv", "trang_thai_video", "sv_k", "0b6c9e1f-seedvis")]
    assert [n for n, _, _ in _nhk(goi)] == ["sv"] * 4


def test_khong_truyen_nha_nhu_cu_khoa_gensuite_dung_dau_khong_bi_dem_lam_seedvis(monkeypatch, goi):
    """Két cụm gắn khoá Gensuite vào `gen_video` cạnh Lightvisual: khoá đó đứng đầu thì `_may()` cũ
    đem nó bọc ArkClient. Không truyền nhà: Grok -> Lightvisual, Omni -> Seedvis khoá ảnh, như cũ."""
    _ket(monkeypatch, gen_video=_viec(GS, LV), gen_canh=SV)
    v = mapp._VeVideo()
    v.bat_dau("p", "a.png", 6, False, model=GROK)
    v.bat_dau("p", "a.png", 8, True, model="Omni-Flash")
    v.trang_thai("0b6c9e1f-seedvis")
    assert _nhk(goi) == [("lv", "gen_video_i2v", "LV_k"), ("sv", "gen_video_i2v", "sv_k"),
                         ("sv", "trang_thai_video", "sv_k")]
    assert v.giay == 8


def test_chon_nha_chua_co_khoa_bao_ro_chi_cho_cap(monkeypatch, goi):
    v = mapp._VeVideo()
    _ket(monkeypatch, gen_video=_viec(LV), gen_canh=SV)
    with pytest.raises(RuntimeError, match="Gensuite.*General.*gen_video"):
        v.bat_dau("p", "a.png", 10, False, model=GROK, nha="gensuite")
    _ket(monkeypatch, gen_video=_viec(GS), gen_canh=SV)
    with pytest.raises(RuntimeError, match="Lightvisual.*General.*gen_video"):
        v.bat_dau("p", "a.png", 6, False, model=GROK, nha="lightvisual")
    _ket(monkeypatch, gen_video=_viec(GS), gen_canh={"key": "ark_k", "base_url": "https://ark.bytepluses.com/api/v3"})
    with pytest.raises(RuntimeError, match="Seedvis.*General"):
        v.bat_dau_ref("p", ["a.png"], 6, model=GROK, nha="seedvis")
    with pytest.raises(RuntimeError, match="nhà"):
        v.bat_dau("p", "a.png", 6, False, model=GROK, nha="veo")
    assert goi == [], "không tự đổi sang nhà khác (luật cứng 5)"


def test_lightvisual_chi_chay_grok(monkeypatch, goi):
    _ket(monkeypatch, gen_video=_viec(LV, GS), gen_canh=SV)
    with pytest.raises(RuntimeError, match="Grok"):
        mapp._VeVideo().bat_dau("p", "a.png", 8, True, model="Omni-Flash", nha="lightvisual")
    assert goi == []


def test_hoi_va_tai_gensuite_dung_khoa_ghi_tren_task(monkeypatch, goi, tmp_path):
    """Đúng chuỗi route video-kiem: trang_thai(vid) rồi tai_ve(video_url)."""
    _ket(monkeypatch, gen_video=_viec(LV, GS, GS2), gen_canh=SV)
    v = mapp._VeVideo()
    r = v.trang_thai("gs_abc@api-gs2")
    v.tai_ve(r["video_url"], tmp_path / "a.mp4")
    assert [(n, h, k, a) for n, h, k, a, _ in goi] == [
        ("gs", "trang_thai_video", "GS_2", "gs_abc"),
        ("gs", "tai_video", "GS_2", "https://scontent.xx.fbcdn.net/gs_abc.mp4")], "mã bỏ @id, url bỏ dấu nhà"


def test_task_seedvis_lightvisual_dang_do_van_hoi_nhu_truoc(monkeypatch, goi, tmp_path):
    _ket(monkeypatch, gen_video=_viec(GS, LV), gen_canh=SV)
    v = mapp._VeVideo()
    for tid in ("lv_job_1@api-lv", "0b6c9e1f-seedvis"):
        v.tai_ve(v.trang_thai(tid)["video_url"], tmp_path / "a.mp4")
    assert _nhk(goi) == [("lv", "trang_thai_video", "LV_k"), ("lv", "tai_video", "LV_k"),
                         ("sv", "trang_thai_video", "sv_k"), ("sv", "tai_video", "sv_k")]


def test_go_khoa_gensuite_ma_con_task_thi_bao_ro(monkeypatch, goi):
    _ket(monkeypatch, gen_video=_viec(LV), gen_canh=SV)
    with pytest.raises(RuntimeError, match="Gensuite.*General"):
        mapp._VeVideo().trang_thai("gs_abc@api-gs")
    assert goi == [], "không đem hỏi nhầm nhà khác"


def test_nha_co_khoa_cho_trang_khong_lam_lech_vong(monkeypatch, goi):
    _ket(monkeypatch, gen_video=_viec(LV, LV2, GS), gen_canh=SV)
    v = mapp._VeVideo()
    assert v.nha_co_khoa == [{"ma": "seedvis", "co": True, "ly_do": ""},
                             {"ma": "lightvisual", "co": True, "ly_do": ""},
                             {"ma": "gensuite", "co": True, "ly_do": ""}]
    v.bat_dau("p", "a.png", 6, False, model=GROK)
    assert v.nha_co_khoa
    v.bat_dau("p", "a.png", 6, False, model=GROK)
    assert [k for _, _, k in _nhk(goi)] == ["LV_k", "LV_2"], "hỏi nhà nào có khoá không xoay vòng"
    _ket(monkeypatch, gen_video=_viec(LV), gen_canh={})
    ds = {x["ma"]: x for x in v.nha_co_khoa}
    assert ds["lightvisual"]["co"] and not ds["seedvis"]["co"] and not ds["gensuite"]["co"]
    assert "General" in ds["seedvis"]["ly_do"] and "gen_video" in ds["gensuite"]["ly_do"]


# ═══════ route: nhà đi theo nút bấm, Gensuite ghép lại 10 s ═══════════════════════
class VeVideoNha(VeVideoI2v):
    nha_co_khoa = [{"ma": "seedvis", "co": True, "ly_do": ""},
                   {"ma": "lightvisual", "co": False, "ly_do": "Chưa có khoá Lightvisual — Owner cấp ở General"},
                   {"ma": "gensuite", "co": True, "ly_do": ""}]

    def bat_dau(self, prompt, anh, giay, am, model=None, nha=None):
        self.goi.append({"prompt": prompt, "anh": anh, "giay": giay, "am": am, "model": model, "nha": nha})
        return "task-shot-1"

    def bat_dau_ref(self, prompt, anh, giay, model=None, nha=None):
        self.goi.append({"prompt": prompt, "anh": list(anh), "giay": giay, "model": model, "nha": nha})
        return "task-drama-1"


def test_shot_gui_gensuite_prompt_va_do_dai_10s_giay_cua_shot_giu_nguyen(tmp_path):
    vv = VeVideoNha()
    kho, c = _san(tmp_path, vv=vv)
    _dan_duyet(c)
    p1 = _clip(kho)
    ds = c.get(f"/api/tap/D1/C1/canh/{p1['id']}/shot").json()
    k = next(k for k, x in enumerate(ds) if x["giay"] != 10)
    goc = f"/api/tap/D1/C1/canh/{p1['id']}/shot/{ds[k]['sid']}"
    c.post(goc + "/anh")
    c.post(goc + "/duyet")
    pr = c.get(goc + "/prompt").json()
    cu = f"for the full {pr['giay']} seconds"
    assert cu in pr["video"]
    r = c.post(goc + "/video", json={"nha": "gensuite"})
    assert r.status_code == 200, r.text
    g = vv.goi[-1]
    assert (g["nha"], g["giay"]) == ("gensuite", 10)
    assert g["prompt"] == pr["video"].replace(cu, "for the full 10 seconds")
    assert c.get(f"/api/tap/D1/C1/canh/{p1['id']}/shot").json()[k]["giay"] == pr["giay"], "độ dài người dựng chọn giữ nguyên"
    assert c.post(goc + "/video-kiem").json()["trang_thai"] == "xong"
    assert c.post(goc + "/video", json={"nha": "seedvis"}).status_code == 200
    g = vv.goi[-1]
    assert (g["nha"], g["giay"], g["prompt"]) == ("seedvis", pr["giay"], pr["video"])
    c.post(goc + "/video-kiem")
    r = c.post(goc + "/video", json={"nha": "veo"})
    assert r.status_code == 400 and "Gensuite" in r.json()["detail"] and len(vv.goi) == 2


def test_clip_narration_gensuite_10s_prompt_tay_lech_giay_thi_chan(tmp_path):
    from test_treatment_video import _bo

    vv = VeVideoNha()
    c, kho, ma = _bo(tmp_path, vv)
    goc = f"/api/tap/SE001/H/canh/{ma}"
    r = c.post(goc + "/video", json={"nha": "gensuite"})
    assert r.status_code == 200, r.text
    g = vv.goi[-1]
    assert (g["nha"], g["giay"]) == ("gensuite", 10) and "for the full 10 seconds" in g["prompt"]
    c.post(goc + "/video-kiem")
    tay = "Slow push in. Continue this camera move for the full 8 seconds.\nEN motion"
    kho.sua_canh("SE001", "H", ma, lambda x: x.update(pvt=tay), "thu")
    r = c.post(goc + "/video", json={"nha": "gensuite"})
    assert r.status_code == 400 and "8 giây" in r.json()["detail"] and "10" in r.json()["detail"], r.text
    assert len(vv.goi) == 1, "prompt sửa tay không tự sửa lặng lẽ, không gửi"
    assert c.post(goc + "/video", json={"nha": "seedvis"}).status_code == 200
    assert vv.goi[-1]["prompt"] == tay and vv.goi[-1]["nha"] == "seedvis"


def test_clip_drama_ca_clip_gensuite_moc_giay_toi_10(tmp_path):
    vv = VeVideoNha()
    kho, c = _san(tmp_path, vv=vv)
    p1 = _clip(kho)
    kho.sua_canh("D1", "C1", p1["id"], lambda x: x.update(gi="15"), "minh")
    r = c.post(f"/api/tap/D1/C1/canh/{p1['id']}/video", json={"nha": "gensuite"})
    assert r.status_code == 200, r.text
    g = vv.goi[-1]
    assert (g["nha"], g["giay"]) == ("gensuite", 10)
    assert re.findall(r"-(\d+(?:\.\d+)?)s\)", g["prompt"])[-1] == "10", g["prompt"]
    assert _clip(kho)["gi"] == "15"


def test_route_bao_nha_nao_co_khoa(tmp_path):
    from test_treatment_video import _bo

    c, _, _ = _bo(tmp_path, VeVideoNha())
    assert c.get("/api/cau-hinh/nha-video").json() == {"nha": VeVideoNha.nha_co_khoa}
    c, _, _ = _bo(tmp_path / "cu", VeVideoI2v())
    assert c.get("/api/cau-hinh/nha-video").json() == {"nha": []}, "bộ dựng không báo nhà: trang gửi như cũ"
