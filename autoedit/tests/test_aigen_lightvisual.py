"""LightvisualClient — video Grok qua lightvisual.studio (Owner chốt 29/10: "mặc định dùng ncc
này để gen video"; ảnh vẫn GPT Image 2 ở Seedvis). Cùng hình dạng với SeedvisClient để
`_VeVideo` đổi nhà không đổi nơi gọi. Mọi HTTP đi qua `client._session`: phiên giả, không mạng.
"""

from __future__ import annotations

import base64
import json
import shutil
import subprocess

import pytest

from autoedit.aigen import lightvisual as mlv
from autoedit.aigen.client import AigenError
from autoedit.aigen.lightvisual import LightvisualClient
from test_aigen_seedvis import PNG, PhienGia, _Tra

BASE = "https://lightvisual.studio/v1"


def _may(kich_ban):
    c = LightvisualClient(api_key="LV_test_key", base_url=BASE)
    c._session = PhienGia(kich_ban)
    return c


def _anh(tmp_path, ten="dau.png"):
    from PIL import Image

    p = tmp_path / ten
    Image.new("RGB", (64, 36), (120, 80, 40)).save(p)
    return p


def test_khong_co_khoa_thi_chet_co_chi_dan():
    with pytest.raises(AigenError, match="General"):
        LightvisualClient(api_key="")


def test_i2v_gui_model_xai_720p_giay_grok_anh_dau_jpeg(tmp_path):
    c = _may([_Tra(200, {"id": "lv_job_a1", "status": "queued"})])
    tid = c.gen_video_i2v("Nia blinks once.", _anh(tmp_path), giay=12, am=False, model="grok-imagine-video-1.5")
    assert tid == "lv_job_a1"
    g = c._session.goi[0]
    assert g["method"] == "POST" and g["url"] == BASE + "/videos"
    assert g["headers"]["Authorization"] == "Bearer LV_test_key"
    t = g["json"]
    assert t["model"] == "xai/grok-imagine-video-1.5", "mã Seedvis của app -> mã lightvisual"
    assert t["seconds"] == 10 and t["resolution"] == "720p", "12 s ép về mức Grok 6/10/15"
    assert t["prompt"] == "Nia blinks once."
    assert t["image"]["url"].startswith("data:image/jpeg;base64,")
    assert "reference_images" not in t


def test_ref_doi_image_n_thanh_the_lightvisual_gui_moi_anh(tmp_path):
    c = _may([_Tra(200, {"id": "lv_job_b2", "status": "queued"})])
    anh = [_anh(tmp_path, "a.png"), _anh(tmp_path, "b.png")]
    c.gen_video_ref("Image 1 is the room. Image 2 is Nia; Image 12 stays.", anh, giay=6)
    t = c._session.goi[0]["json"]
    assert t["model"] == "xai/grok-imagine-video-1.5" and t["seconds"] == 6
    assert t["prompt"] == "<IMAGE_0> is the room. <IMAGE_1> is Nia; Image 12 stays."
    assert [x["url"][:23] for x in t["reference_images"]] == ["data:image/jpeg;base64,"] * 2
    assert "image" not in t


@pytest.mark.parametrize("tra,mong", [
    ({"status": "queued"}, {"status": "queued"}),
    ({"status": "processing", "progress": 40}, {"status": "processing"}),
    ({"status": "completed", "result": {"video_url": "/api/tenants/1/x/content"}},
     {"status": "succeeded", "video_url": BASE + "/videos/lv_job_c3/content"}),
    ({"status": "failed", "error": {"message": "nội dung bị chặn"}}, {"status": "failed", "loi": "nội dung bị chặn"}),
])
def test_trang_thai_cung_hinh_dang_seedvis(tra, mong):
    c = _may([_Tra(200, dict(tra, id="lv_job_c3"))])
    assert c.trang_thai_video("lv_job_c3") == mong
    assert c._session.goi[0]["url"] == BASE + "/videos/lv_job_c3"


def test_qua_tai_502_thi_cho_roi_goi_lai_khong_mat_credit(monkeypatch):
    ngu = []
    monkeypatch.setattr(mlv.time, "sleep", lambda s: ngu.append(s))
    c = _may([_Tra(502, {"error": {"message": "Hệ thống đang xử lý lượng lớn yêu cầu", "type": "model_unavailable"}}),
              _Tra(200, {"id": "lv_job_d4", "status": "queued"})])
    assert c.trang_thai_video("lv_job_d4") == {"status": "queued"}
    assert len(c._session.goi) == 2 and ngu, "502 quá tải: chờ rồi gọi lại"


def test_loi_khong_tam_thi_bao_ngay(monkeypatch):
    monkeypatch.setattr(mlv.time, "sleep", lambda s: None)
    c = _may([_Tra(401, {"error": {"message": "invalid key"}})])
    with pytest.raises(AigenError, match="401"):
        c.trang_thai_video("lv_job_e5")
    assert len(c._session.goi) == 1


def test_tai_video_kem_khoa_ghi_ra_file(tmp_path, monkeypatch):
    monkeypatch.setattr(mlv, "_ffmpeg", lambda: None)            # máy không có ffmpeg: giữ nguyên file
    c = _may([_Tra(200, b"MP4DATA")])
    ra = c.tai_video(BASE + "/videos/lv_job_f6/content", tmp_path / "v" / "a.mp4")
    assert ra.read_bytes() == b"MP4DATA"
    assert c._session.goi[0]["headers"]["Authorization"] == "Bearer LV_test_key"


def test_tai_video_bo_anh_bia_mjpeg_khong_encode_lai(tmp_path):
    """File lightvisual kèm một luồng ảnh bìa (đo 29/10): bỏ bằng chép luồng, hình + tiếng giữ nguyên."""
    ff = mlv._ffmpeg()
    if not ff:
        pytest.skip("máy không có ffmpeg")
    goc, bia = tmp_path / "goc.mp4", _anh(tmp_path, "bia.png")
    tam = tmp_path / "tam.mp4"
    subprocess.run([ff, "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=64x36:rate=24:duration=1",
                    "-f", "lavfi", "-i", "sine=duration=1", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(tam)],
                   check=True)
    subprocess.run([ff, "-v", "error", "-y", "-i", str(tam), "-i", str(bia), "-map", "0", "-map", "1", "-c", "copy",
                    "-c:v:1", "mjpeg", "-disposition:v:1", "attached_pic", str(goc)], check=True)
    c = _may([_Tra(200, goc.read_bytes())])
    ra = c.tai_video(BASE + "/videos/lv_job_g7/content", tmp_path / "ra.mp4")
    probe = shutil.which("ffprobe") or ff.replace("ffmpeg", "ffprobe")
    kq = subprocess.run([probe, "-v", "error", "-show_entries", "stream=codec_type,codec_name", "-of", "json", str(ra)],
                        capture_output=True, text=True, check=True)
    luong = [(s["codec_type"], s["codec_name"]) for s in json.loads(kq.stdout)["streams"]]
    assert luong == [("video", "h264"), ("audio", "aac")], luong


def test_ds_model_chi_video_tu_catalog():
    c = _may([_Tra(200, {"data": [
        {"canonical_id": "xai/grok-imagine-image-2.0", "display_name": "Grok Imagine Image 2.0",
         "capabilities": {"video": False}, "maintenance": "operational"},
        {"canonical_id": "xai/grok-imagine-video-1.5", "display_name": "Grok Imagine Video 1.5",
         "capabilities": {"video": True}, "maintenance": "operational"},
        {"canonical_id": "google/omni", "display_name": "Omni", "capabilities": {"video": True},
         "maintenance": "maintenance"}]})])
    assert c.ds_model() == [
        {"id": "xai/grok-imagine-video-1.5", "label": "Grok Imagine Video 1.5", "type": "video", "status": "active"},
        {"id": "google/omni", "label": "Omni", "type": "video", "status": "maintenance"}]


def test_data_url_jpeg_canh_dai_toi_da(tmp_path):
    from PIL import Image

    p = tmp_path / "to.png"
    Image.new("RGB", (3200, 1800)).save(p)
    import io

    b = base64.b64decode(mlv._data_url_jpeg(p).split(",", 1)[1])
    assert max(Image.open(io.BytesIO(b)).size) == 1600
