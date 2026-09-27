"""SeedvisClient — cùng hình dạng với ArkClient, chạy trên API Seedvis v2.0.

User chốt 27/09: "Hãy đấu nối hạ tầng với seedvis. Tôi không dùng seedance nữa."
Đo cùng ngày: ảnh có mặt người ModelArk từ chối thì Seedvis nhận; 4 ref Nano
Banana Pro neo đủ nhận dạng, 2752×1536.

Mọi HTTP đi qua `client._session` nên test thay phiên giả, không chạm mạng.
"""

from __future__ import annotations

import json

import pytest

from autoedit.aigen.client import AigenError
from autoedit.aigen.seedvis import SeedvisClient, giay_hop_le

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


class _Tra:
    def __init__(self, status, body, headers=None):
        self.status_code = status
        self._body = body
        self.headers = headers or {}
        self.content = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.text = "" if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False)

    def json(self):
        if isinstance(self._body, bytes):
            raise ValueError("bytes")
        return self._body


class PhienGia:
    """Ghi lại mọi lượt gọi; trả theo kịch bản xếp sẵn."""

    def __init__(self, kich_ban):
        self.kich_ban = list(kich_ban)
        self.goi = []

    def request(self, method, url, json=None, headers=None, timeout=None):
        self.goi.append({"method": method, "url": url, "json": json, "headers": headers})
        return self.kich_ban.pop(0)

    def get(self, url, headers=None, timeout=None):
        self.goi.append({"method": "GET", "url": url, "headers": headers})
        return self.kich_ban.pop(0)


def _may(kich_ban, **kw):
    c = SeedvisClient(api_key="sv_live_test", **kw)
    c._session = PhienGia(kich_ban)
    return c


# ═══════ độ dài video theo model, không phải hằng số 15 ═══════════════════════
def test_giay_hop_le_ep_ve_muc_model_nhan():
    assert giay_hop_le(15) == 8 and giay_hop_le(8) == 8
    assert giay_hop_le(7) == 6 and giay_hop_le(5) == 4 and giay_hop_le(3) == 4


def test_client_bao_giay_toi_da_cua_no():
    assert _may([]).giay == 8


def test_khong_co_khoa_thi_chet_co_chi_dan():
    with pytest.raises(AigenError, match="General"):
        SeedvisClient(api_key="")


# ═══════ ảnh: Nano Banana, 16:9, upscale 2k, ref inline ═══════════════════════
def test_gen_anh_co_ref_di_endpoint_google_voi_data_url(tmp_path):
    ref = tmp_path / "ref.png"
    ref.write_bytes(PNG)
    c = _may([
        _Tra(200, {"id": "j1", "status": "completed", "is_final": True,
                   "outputs": [{"type": "image", "url": "https://cdn/x.png"}]}),
        _Tra(200, b"ANH"),
    ])
    ra = c.gen_anh("a scene", tmp_path / "out" / "a.png", ref=[ref])
    assert ra.read_bytes() == b"ANH"
    g = c._session.goi[0]
    assert g["url"].endswith("/google/v1beta/interactions") and g["method"] == "POST"
    assert g["json"]["model"] == "GEM_PIX_2" and g["json"]["input"] == "a scene"
    assert g["json"]["aspect_ratio"] == "16:9" and g["json"]["upscale_image"] == "2k"
    assert g["json"]["mode"] == "image-to-image"
    assert g["json"]["reference_images"][0].startswith("data:image/png;base64,")
    assert g["headers"]["Authorization"] == "Bearer sv_live_test"
    assert "Idempotency-Key" in g["headers"]
    assert "sv_live_test" not in g["url"], "không bao giờ để khoá trong URL"


def test_gen_anh_khong_ref_la_text_to_image(tmp_path):
    c = _may([_Tra(200, {"id": "j", "status": "completed", "is_final": True,
                         "outputs": [{"url": "https://cdn/x.png"}]}), _Tra(200, b"A")])
    c.gen_anh("p", tmp_path / "a.png")
    j = c._session.goi[0]["json"]
    assert j["mode"] == "text-to-image" and "reference_images" not in j


def test_gen_anh_202_thi_DI_THEO_next_url_khong_gui_lai(tmp_path):
    """queued/processing là THÀNH CÔNG. Gửi lại là job mới, trừ credit lần nữa."""
    c = _may([
        _Tra(202, {"id": "j2", "status": "processing", "is_final": False,
                   "next": {"action": "poll", "url": "https://seedvis.com/api/v1/developer/generations/j2?wait=30",
                            "after_seconds": 0}}),
        _Tra(200, {"data": {"id": "j2", "status": "processing", "is_final": False,
                            "next": {"url": "https://seedvis.com/api/v1/developer/generations/j2?wait=30",
                                     "after_seconds": 0}}}),
        _Tra(200, {"data": {"id": "j2", "status": "completed", "is_final": True,
                            "outputs": [{"url": "https://cdn/y.png"}]}}),
        _Tra(200, b"Y"),
    ])
    c.gen_anh("p", tmp_path / "b.png")
    goi = c._session.goi
    assert [g["method"] for g in goi] == ["POST", "GET", "GET", "GET"], (
        "một POST duy nhất; còn lại là poll theo next.url rồi tải")
    assert goi[1]["url"].endswith("/developer/generations/j2?wait=30")


def test_gen_anh_job_hong_thi_nem_loi_co_ma(tmp_path):
    c = _may([_Tra(200, {"id": "j", "status": "failed", "is_final": True,
                         "error": {"code": "content_policy", "message": "bi chan"}})])
    with pytest.raises(AigenError, match="content_policy"):
        c.gen_anh("p", tmp_path / "a.png")


def test_http_400_KHONG_thu_lai_429_thi_thu_lai(tmp_path, monkeypatch):
    import autoedit.aigen.seedvis as sv
    monkeypatch.setattr(sv.time, "sleep", lambda *_: None)
    c = _may([_Tra(400, {"code": "invalid_image", "message": "x"})])
    with pytest.raises(AigenError, match="HTTP 400"):
        c.gen_anh("p", tmp_path / "a.png")
    assert len(c._session.goi) == 1
    c2 = _may([_Tra(429, {"code": "rate_limit_exceeded"}, {"Retry-After": "0"}),
               _Tra(200, {"id": "j", "status": "completed", "is_final": True,
                          "outputs": [{"url": "https://cdn/z.png"}]}), _Tra(200, b"Z")])
    c2.gen_anh("p", tmp_path / "c.png")
    g = c2._session.goi
    assert g[0]["headers"]["Idempotency-Key"] == g[1]["headers"]["Idempotency-Key"], (
        "retry phải mang CÙNG Idempotency-Key — không thì thành job thứ hai")


# ═══════ video i2v: Omni Flash / Veo, tối đa 8 s ═══════════════════════════════
def test_gen_video_nop_image_to_video_duration_theo_model(tmp_path):
    anh = tmp_path / "canh.png"
    anh.write_bytes(PNG)
    c = _may([_Tra(202, {"data": {"id": "v1", "status": "queued", "is_final": False}})])
    tid = c.gen_video_i2v("Camera pushes in.", anh, giay=15, am=False)
    assert tid == "v1"
    j = c._session.goi[0]["json"]
    assert c._session.goi[0]["url"].endswith("/developer/generations")
    assert j["model"] == "Omni-Flash" and j["mode"] == "image-to-video"
    assert j["duration"] == "8s", "15 s không có ở Omni/Veo — ép về 8s"
    assert j["image"].startswith("data:image/png;base64,") and j["aspect_ratio"] == "16:9"


def test_doi_model_video_qua_ket(tmp_path):
    anh = tmp_path / "canh.png"
    anh.write_bytes(PNG)
    c = _may([_Tra(202, {"data": {"id": "v2", "status": "queued", "is_final": False}})],
             model_video="Veo-3.1")
    c.gen_video_i2v("p", anh, giay=6)
    assert c._session.goi[0]["json"]["model"] == "Veo-3.1"
    assert c._session.goi[0]["json"]["duration"] == "6s"


def test_trang_thai_video_tra_hinh_dang_nhu_ArkClient():
    c = _may([
        _Tra(200, {"data": {"id": "v", "status": "processing", "is_final": False}}),
        _Tra(200, {"data": {"id": "v", "status": "completed", "is_final": True,
                            "outputs": [{"type": "video", "url": "https://cdn/v.mp4"}]}}),
        _Tra(200, {"data": {"id": "v", "status": "failed", "is_final": True,
                            "error": {"code": "content_policy", "message": "chan"}}}),
    ])
    assert c.trang_thai_video("v") == {"status": "processing"}
    assert c.trang_thai_video("v") == {"status": "succeeded", "video_url": "https://cdn/v.mp4"}
    r = c.trang_thai_video("v")
    assert r["status"] == "failed" and "content_policy" in r["loi"]
    assert all(g["url"].endswith("/developer/generations/v?wait=30") for g in c._session.goi)


def test_tai_video_ghi_file(tmp_path):
    c = _may([_Tra(200, b"MP4")])
    p = c.tai_video("https://cdn/v.mp4", tmp_path / "v" / "a.mp4")
    assert p.read_bytes() == b"MP4"
