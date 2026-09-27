"""Chọn MODEL ngay trong UI (Owner chốt 27/09), đè được theo cảnh.

Thứ tự ưu tiên: cảnh (`mda`/`mdv`) > tập (`model_anh`/`model_video`) > két.
Độ dài clip theo model video HIỆU LỰC — Omni Flash / Veo 8 s, Seedance 15/30 s,
ModelArk 15 s — vì lệnh LLM, prompt video và cảnh báo trên trang đều ăn theo.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment import dong as mdong
from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64


class VeGia:
    def __init__(self):
        self.goi = []

    def gen_anh(self, prompt, dich, ref=None, model=None):
        self.goi.append({"prompt": prompt, "ref": list(ref or []), "model": model})
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(PNG)
        return dich


class VeVideoGia:
    giay = 8
    giay_theo_model = {"Omni-Flash": 8, "Veo-3.1": 8, "seedance_2.5": 30}
    danh_sach = [{"id": "GEM_PIX_2", "label": "Nano Banana Pro", "type": "image", "status": "active"},
                 {"id": "gpt-image-2", "label": "GPT Image 2", "type": "image", "status": "active"},
                 {"id": "Omni-Flash", "label": "Omni Flash", "type": "video", "status": "active"},
                 {"id": "Veo-3.1", "label": "Veo 3.1", "type": "video", "status": "maintenance"},
                 {"id": "seedance_2.5", "label": "Seedance 2.5", "type": "video", "status": "active"}]
    credit = 6789

    def __init__(self):
        self.goi = []

    def bat_dau(self, prompt, anh, giay, am, model=None):
        self.goi.append({"prompt": prompt, "giay": giay, "model": model})
        return "task-1"

    def trang_thai(self, tid):
        return {"status": "succeeded", "video_url": "https://vi-du/" + tid + ".mp4"}

    def tai_ve(self, url, dich):
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(MP4)
        return dich


def _bo(tmp_path):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "K-129")
    ve, vv = VeGia(), VeVideoGia()
    c = TestClient(tao_app(kho, ve_anh=ve, ve_video=vv))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "Voice.", "vi": "", "het": 0,
         "canh": [{"t": "Cận bàn tay", "pa": "EN hand", "pv": "EN move", "duyet": "1"}]}]})
    return c, kho, ve, vv


def _ma(kho):
    return kho.doc("SE001", "H")["dong"][0]["canh"][0]["id"]


def _dat(kho, **k):
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0].update(k)
    kho.luu("SE001", "H", d, "", "thu")


# ═══════ kho: model theo TẬP, vá cột như `tong` ══════════════════════════════
def test_kho_giu_model_theo_tap(tmp_path):
    kho = Kho(tmp_path / "k.db")
    kho.tao_tap("SE001", "K-129")
    assert kho.mo_hinh_tap("SE001") == {"anh": "", "video": ""}
    kho.dat_mo_hinh_tap("SE001", anh="GEM_PIX_2", video="Omni-Flash")
    assert kho.mo_hinh_tap("SE001") == {"anh": "GEM_PIX_2", "video": "Omni-Flash"}
    kho.dat_mo_hinh_tap("SE001", anh="", video="Omni-Flash")   # xoá một cái = về két
    assert kho.mo_hinh_tap("SE001") == {"anh": "", "video": "Omni-Flash"}


def test_canh_giu_duoc_mda_mdv():
    assert "mda" in mdong.KHOA_CANH and "mdv" in mdong.KHOA_CANH
    d = mdong.ghi_canh({}, [{"id": "c1", "t": "x", "mda": "gpt-image-2", "mdv": "Veo-3.1"}])
    c = mdong.doc_canh(d)[0]
    assert (c["mda"], c["mdv"]) == ("gpt-image-2", "Veo-3.1")


# ═══════ thứ tự ưu tiên: cảnh > tập > két ═══════════════════════════════════
def test_khong_chon_gi_thi_KHONG_gui_model_bo_dung_tu_lay_ket(tmp_path):
    c, kho, ve, vv = _bo(tmp_path)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert ve.goi[0]["model"] is None, "không chọn thì để nhà tự lấy model trong két"


def test_model_theo_TAP_di_vao_luot_ve(tmp_path):
    c, kho, ve, vv = _bo(tmp_path)
    kho.dat_mo_hinh_tap("SE001", anh="gpt-image-2", video="Veo-3.1")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert ve.goi[0]["model"] == "gpt-image-2"
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/duyet")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/video")
    assert vv.goi[0]["model"] == "Veo-3.1"


def test_canh_DE_duoc_model_cua_tap(tmp_path):
    c, kho, ve, vv = _bo(tmp_path)
    kho.dat_mo_hinh_tap("SE001", anh="GEM_PIX_2", video="Omni-Flash")
    _dat(kho, mda="gpt-image-2", mdv="seedance_2.5")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert ve.goi[0]["model"] == "gpt-image-2"
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/duyet")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/video")
    assert vv.goi[0]["model"] == "seedance_2.5"


# ═══════ độ dài clip theo model video HIỆU LỰC ═══════════════════════════════
def test_do_dai_clip_theo_model_video_hieu_luc(tmp_path):
    """Seedance 2.5 = 30 s, Omni = 8 s. Prompt video, tham số gửi đi và lệnh LLM
    phải theo model của CHÍNH cảnh đó."""
    c, kho, ve, vv = _bo(tmp_path)
    _dat(kho, mdv="seedance_2.5")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/duyet")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/video")
    assert vv.goi[0]["giay"] == 30 and "full 30 seconds" in vv.goi[0]["prompt"]
    assert c.get("/api/cau-hinh/video?tap=SE001").json()["giay"] == 8, "tập vẫn 8 (Omni)"


# ═══════ endpoint cho UI ═════════════════════════════════════════════════════
def test_GET_mo_hinh_tra_danh_sach_dang_chon_credit_va_giay(tmp_path):
    c, kho, ve, vv = _bo(tmp_path)
    kho.dat_mo_hinh_tap("SE001", anh="GEM_PIX_2", video="")
    r = c.get("/api/tap/SE001/mo-hinh").json()
    assert r["chon"] == {"anh": "GEM_PIX_2", "video": ""}
    assert set(r["ket"]) == {"anh", "video"}, "nút 'theo két' phải nói rõ két đang cấp model nào"
    assert [m["id"] for m in r["danh_sach"] if m["type"] == "image"] == ["GEM_PIX_2", "gpt-image-2"]
    assert r["credit"] == 6789
    assert r["giay"]["Omni-Flash"] == 8 and r["giay"]["seedance_2.5"] == 30
    assert next(m for m in r["danh_sach"] if m["id"] == "Veo-3.1")["status"] == "maintenance"


def test_PUT_mo_hinh_ghi_theo_tap_va_can_quyen_sua(tmp_path):
    c, kho, ve, vv = _bo(tmp_path)
    assert c.put("/api/tap/SE001/mo-hinh", json={"anh": "gpt-image-2", "video": "Omni-Flash"}).status_code == 200
    assert kho.mo_hinh_tap("SE001") == {"anh": "gpt-image-2", "video": "Omni-Flash"}
    c.headers.update({"X-Remote-Actions": ""})
    assert c.put("/api/tap/SE001/mo-hinh", json={"anh": "", "video": ""}).status_code == 403
