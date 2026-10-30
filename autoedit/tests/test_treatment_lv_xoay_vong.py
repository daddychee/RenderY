"""Nhiều tài khoản Lightvisual cho video Grok (user duyệt 30/10, phương án A — xoay vòng).

Owner gán nhiều khoá vào Treatment › `gen_video` bằng nút "+ key" ở General. Mỗi lượt gửi đi một
khoá theo vòng; mã task mang id khoá két (`lv_job_x@api-002`) để lúc hỏi / tải đi ĐÚNG tài khoản —
hỏi nhầm tài khoản là mất video đã trả tiền. Két giả, client giả — không mạng, không khoá thật.
"""

from __future__ import annotations

import itertools
import pathlib

import pytest

import autoedit.treatment.app as mapp
from autoedit.aigen.client import AigenError
from autoedit.aigen.lightvisual import LightvisualClient
from autoedit.aigen.seedvis import SeedvisClient
from autoedit.treatment import dich as mdich

LV_URL = "https://lightvisual.studio/v1"
LV1 = {"id": "api-001", "key": "LV_1", "base_url": LV_URL, "nha": "lightvisual"}
LV2 = {"id": "api-002", "key": "LV_2", "base_url": LV_URL, "nha": "lightvisual"}
SV_VIDEO = {"id": "api-003", "key": "sv_video", "base_url": "https://seedvis.com/api/v1", "nha": "seedvis"}
GEN_CANH = {"key": "sv_canh", "base_url": "https://seedvis.com/api/v1", "model": "gpt-image-2"}
GROK = "grok-imagine-video-1.5"


def _viec(*khoa, che_do="xoay_vong"):
    """Hình dạng thật của `doc_ket_viec`: khoá đầu ở ngoài + `ds` đủ danh sách + `che_do`."""
    return {"key": khoa[0]["key"], "base_url": khoa[0]["base_url"], "model": "xai/" + GROK,
            "ds": list(khoa), "che_do": che_do}


class _So(list):
    """Sổ lời gọi; `hong[hàm]` = các khoá trả 404 cho hàm đó."""
    hong: dict


@pytest.fixture
def goi(monkeypatch):
    """Ghi (khoá, hàm, đối số đầu) thay vì gọi mạng; vòng xoay bắt đầu lại từ đầu mỗi test."""
    ds = _So()
    ds.hong = {}
    monkeypatch.setattr(mapp._VeVideo, "_LUOT", itertools.count(), raising=False)

    def gia(ham, tien_to):
        def chay(self, *a, **kw):
            ds.append((self._key, ham, a[0] if a else None))
            if self._key in ds.hong.get(ham, ()):
                raise AigenError(f"Lightvisual HTTP 404: không thấy task ({self._key})")
            if ham == "trang_thai_video":
                return {"status": "succeeded", "video_url": f"{LV_URL}/videos/{a[0]}/content"}
            return f"{tien_to}{len(ds)}" if ham.startswith("gen_") else "ok"
        return chay
    for lop, tien_to in ((LightvisualClient, "lv_job_"), (SeedvisClient, "sv_")):
        for ham in ("gen_video_i2v", "gen_video_ref", "trang_thai_video", "tai_video"):
            monkeypatch.setattr(lop, ham, gia(ham, tien_to))
    return ds


def _ket(monkeypatch, gen_video):
    monkeypatch.setattr(mdich, "doc_ket_viec",
                        lambda v="dich": dict({"gen_video": gen_video, "gen_canh": GEN_CANH}.get(v) or {}))


def test_dung_code_cua_cay_dang_test():
    goc = pathlib.Path(__file__).resolve().parents[1]
    assert pathlib.Path(mapp.__file__).resolve().is_relative_to(goc), mapp.__file__


def test_hai_khoa_xoay_vong_va_ma_task_mang_id_khoa(monkeypatch, goi):
    _ket(monkeypatch, _viec(LV1, LV2))
    v = mapp._VeVideo()
    ra = [v.bat_dau("p", "a.png", 6, False, model=GROK)]
    assert v.credit is None, "hỏi số dư không được làm lệch vòng"
    ra += [v.bat_dau_ref("p", ["a.png"], 10, model=GROK), v.bat_dau("p", "a.png", 6, False, model=GROK),
           v.bat_dau_ref("p", ["a.png"], 6, model=GROK)]
    assert [k for k, _, _ in goi] == ["LV_1", "LV_2", "LV_1", "LV_2"]
    assert ra == ["lv_job_1@api-001", "lv_job_2@api-002", "lv_job_3@api-001", "lv_job_4@api-002"]
    assert not any("LV_" in x for x in ra), "mã task chỉ mang id két, không mang giá trị khoá"


def test_hoi_va_tai_dung_khoa_ghi_tren_task(monkeypatch, goi, tmp_path):
    """Đúng chuỗi của route video-kiem: trang_thai(vid) rồi tai_ve(video_url)."""
    _ket(monkeypatch, _viec(LV1, LV2))
    v = mapp._VeVideo()
    r = v.trang_thai("lv_job_x@api-002")
    v.tai_ve(r["video_url"], tmp_path / "a.mp4")
    assert goi == [("LV_2", "trang_thai_video", "lv_job_x"),
                   ("LV_2", "tai_video", f"{LV_URL}/videos/lv_job_x/content")], "mã gửi đi bỏ phần @id, url bỏ #id"


def test_vid_cu_khong_mang_khoa_thi_hoi_khoa_dau(monkeypatch, goi, tmp_path):
    """Task gửi trước bản này (chưa có @id) vẫn về: hỏi khoá đầu như trước."""
    _ket(monkeypatch, _viec(LV1, LV2))
    v = mapp._VeVideo()
    v.bat_dau("p", "a.png", 6, False, model=GROK)                # vòng đã chạy sang khoá 2
    goi.clear()
    r = v.trang_thai("lv_job_cu")
    v.tai_ve(r["video_url"], tmp_path / "a.mp4")
    assert [(k, h) for k, h, _ in goi] == [("LV_1", "trang_thai_video"), ("LV_1", "tai_video")]


def test_khoa_da_thu_hoi_thi_thu_lan_luot_khoa_con_lai(monkeypatch, goi):
    _ket(monkeypatch, _viec(LV1, LV2))
    goi.hong["trang_thai_video"] = {"LV_1"}
    v = mapp._VeVideo()
    assert v.trang_thai("lv_job_x@api-009")["video_url"].endswith("#api-002"), "tải bằng khoá đã nhận task"
    assert [k for k, _, _ in goi] == ["LV_1", "LV_2"]
    goi.hong["trang_thai_video"] = {"LV_1", "LV_2"}
    with pytest.raises(AigenError, match="404"):
        v.trang_thai("lv_job_x@api-009")
    goi.clear()
    with pytest.raises(AigenError):
        v.trang_thai("lv_job_x@api-001")
    assert [k for k, _, _ in goi] == ["LV_1"], "còn khoá ghi trên task thì CHỈ hỏi khoá đó"


def test_go_het_khoa_lightvisual_thi_bao_ro_khong_hoi_nham_seedvis(monkeypatch, goi):
    _ket(monkeypatch, dict(GEN_CANH, model=GROK))
    with pytest.raises(RuntimeError, match="General"):
        mapp._VeVideo().trang_thai("lv_job_x@api-001")
    assert goi == []


def test_du_phong_luon_khoa_dau(monkeypatch, goi):
    _ket(monkeypatch, _viec(LV1, LV2, che_do="du_phong"))
    v = mapp._VeVideo()
    ra = [v.bat_dau("p", "a.png", 6, False, model=GROK) for _ in range(3)]
    assert [k for k, _, _ in goi] == ["LV_1"] * 3
    assert all(x.endswith("@api-001") for x in ra)


def test_khoa_seedvis_trong_gen_video_khong_vao_vong(monkeypatch, goi):
    _ket(monkeypatch, _viec(LV1, SV_VIDEO, LV2))
    v = mapp._VeVideo()
    ra = [v.bat_dau("p", "a.png", 6, False, model=GROK) for _ in range(4)]
    ra.append(v.bat_dau("p", "a.png", 8, True, model="Omni-Flash"))
    assert [k for k, _, _ in goi] == ["LV_1", "LV_2", "LV_1", "LV_2", "sv_canh"], \
        "Grok xoay hai khoá Lightvisual; Omni đi khoá ảnh như cũ"
    assert ra[-1] == "sv_5", "task Seedvis không gắn id khoá"


def test_doc_ket_viec_tra_du_danh_sach_khoa_va_che_do(monkeypatch):
    import requests

    class _R:
        status_code = 200

        @staticmethod
        def json():
            return {"gen_video": {"khoa": [LV1, LV2], "che_do": "xoay_vong", "model": "xai/" + GROK}}

    monkeypatch.setattr(requests, "get", lambda url, **kw: _R())
    cd = mdich.doc_ket_viec("gen_video")
    assert cd["key"] == "LV_1" and [k["id"] for k in cd["ds"]] == ["api-001", "api-002"]
    assert cd["che_do"] == "xoay_vong"
