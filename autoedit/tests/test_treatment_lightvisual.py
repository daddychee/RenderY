"""Chọn nhà dựng video (Owner chốt 29/10: "mặc định dùng ncc này để gen video"): khoá việc
`gen_video` trong két là Lightvisual thì video GROK đi Lightvisual; model khác (Omni/Veo của
narration) và task Seedvis đang dở vẫn đi Seedvis bằng khoá ảnh `gen_canh`. Không tự chuyển nhà
khi lỗi (luật cứng 5). Két giả, client giả — không mạng.
"""

from __future__ import annotations

import pathlib

import pytest

import autoedit.treatment.app as mapp
from autoedit.aigen.lightvisual import LightvisualClient
from autoedit.aigen.seedvis import SeedvisClient
from autoedit.treatment import dich as mdich

LV = {"key": "LV_k", "base_url": "https://lightvisual.studio/v1", "model": "xai/grok-imagine-video-1.5"}
SV = {"key": "sv_k", "base_url": "https://seedvis.com/api/v1", "model": "gpt-image-2"}


@pytest.fixture
def goi(monkeypatch):
    """Ghi lời gọi của hai nhà thay vì gọi mạng: (nhà, hàm, khoá, model)."""
    ds = []
    for lop, nha in ((LightvisualClient, "lv"), (SeedvisClient, "sv")):
        for ham in ("gen_video_i2v", "gen_video_ref", "trang_thai_video", "tai_video"):
            def gia(self, *a, _n=nha, _h=ham, **kw):
                ds.append((_n, _h, self._key, kw.get("model")))
                return {"status": "queued"} if _h == "trang_thai_video" else "id"
            monkeypatch.setattr(lop, ham, gia)
    return ds


def _ket(monkeypatch, **viec):
    monkeypatch.setattr(mdich, "doc_ket_viec", lambda v="dich": dict(viec.get(v) or {}))


def test_dung_code_cua_cay_dang_test():
    goc = pathlib.Path(__file__).resolve().parents[1]
    assert pathlib.Path(mapp.__file__).resolve().is_relative_to(goc), mapp.__file__


def test_grok_di_lightvisual_model_khac_va_anh_van_seedvis(monkeypatch, goi):
    _ket(monkeypatch, gen_video=LV, gen_canh=SV)
    v = mapp._VeVideo()
    v.bat_dau("p", "a.png", 6, False, model="grok-imagine-video-1.5")
    v.bat_dau_ref("p", ["a.png"], 10, model="grok-imagine-video-1.5")
    v.bat_dau("p", "a.png", 8, True, model="Omni-Flash")
    assert goi == [("lv", "gen_video_i2v", "LV_k", "grok-imagine-video-1.5"),
                   ("lv", "gen_video_ref", "LV_k", "grok-imagine-video-1.5"),
                   ("sv", "gen_video_i2v", "sv_k", "Omni-Flash")], "Omni đi Seedvis bằng khoá ảnh"


def test_task_nhan_nha_theo_ma_va_dia_chi_task_seedvis_dang_do_van_ve(monkeypatch, goi):
    _ket(monkeypatch, gen_video=LV, gen_canh=SV)
    v = mapp._VeVideo()
    v.trang_thai("lv_job_abc")
    v.trang_thai("0b6c9e1f-seedvis")
    v.tai_ve("https://lightvisual.studio/v1/videos/lv_job_abc/content", "x.mp4")
    v.tai_ve("https://cdn.seedvis.com/out/1.mp4", "y.mp4")
    assert [(n, h, k) for n, h, k, _ in goi] == [
        ("lv", "trang_thai_video", "LV_k"), ("sv", "trang_thai_video", "sv_k"),
        ("lv", "tai_video", "LV_k"), ("sv", "tai_video", "sv_k")]


def test_chua_gan_lightvisual_thi_nhu_cu(monkeypatch, goi):
    _ket(monkeypatch, gen_video=dict(SV, model="grok-imagine-video-1.5"), gen_canh=SV)
    v = mapp._VeVideo()
    v.bat_dau("p", "a.png", 6, False, model="grok-imagine-video-1.5")
    assert goi == [("sv", "gen_video_i2v", "sv_k", "grok-imagine-video-1.5")]


def test_go_khoa_lightvisual_ma_con_task_lv_thi_bao_ro_khong_hoi_nham_seedvis(monkeypatch, goi):
    _ket(monkeypatch, gen_canh=SV)
    with pytest.raises(RuntimeError, match="General"):
        mapp._VeVideo().trang_thai("lv_job_abc")
    assert goi == []


def test_so_du_video_khong_bao_0_khi_di_lightvisual(monkeypatch):
    """/balance của họ báo 0đ cả khi gói ngày đang chạy: hiện 0 là báo động giả."""
    _ket(monkeypatch, gen_video=LV, gen_canh=SV)
    assert mapp._VeVideo().credit is None
