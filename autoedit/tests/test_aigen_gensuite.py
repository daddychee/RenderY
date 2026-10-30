"""GensuiteClient — video Muse qua Gensuite (user 30/10: chọn nhà khi bấm gen video). Cùng hình dạng
với LightvisualClient phần video để `_VeVideo` đổi nhà không đổi nơi gọi. Mọi HTTP đi qua
`client._session`: phiên giả, không mạng, không khoá thật.

Đo thật 30/10 (người giao việc): Muse không có khung đầu, chỉ nhận 1–3 ảnh tham chiếu data URL
(≤ 8 MB/ảnh); gửi MỘT ảnh shot làm ref duy nhất thì khung 0 gần y ảnh đó. Luôn 10 s (20/30/60 s là
nhiều khúc 10 s nối cứng). Gửi sát nhau -> 429 `retryAfterSeconds`. Không có lệnh liệt kê job.
"""

from __future__ import annotations

import base64

import pytest

from autoedit.aigen import gensuite as mgs
from autoedit.aigen.client import AigenError
from autoedit.aigen.gensuite import GensuiteClient
from test_aigen_seedvis import PhienGia, _Tra

BASE = "https://supabase-staging.gensuite.site/functions/v1/api-v1"
UUID = "3f1c2a9e-0000-4000-8000-00000000abcd"


@pytest.fixture(autouse=True)
def _khong_so_goi(monkeypatch):
    """Sổ gọi nền POST về gateway thật của máy — test không ghi vào sổ của prod."""
    from autoedit import so_goi_nen

    monkeypatch.setattr(so_goi_nen, "ghi", lambda *a, **kw: None)


@pytest.fixture
def ngu(monkeypatch):
    ds = []
    monkeypatch.setattr(mgs.time, "sleep", lambda s: ds.append(s))
    return ds


def _may(kich_ban):
    c = GensuiteClient(api_key="gsk_test_khoa", base_url=BASE)
    c._session = PhienGia(kich_ban)
    return c


def _anh(tmp_path, ten="dau.png"):
    from PIL import Image

    p = tmp_path / ten
    Image.new("RGB", (64, 36), (120, 80, 40)).save(p)
    return p


def _nhan(id_=UUID):
    return _Tra(202, {"batchId": "b1", "items": [{"id": id_, "status": "queued"}]})


def test_khong_co_khoa_thi_chet_co_chi_dan():
    with pytest.raises(AigenError, match="General"):
        GensuiteClient(api_key="")


def test_i2v_gui_anh_dau_lam_ref_duy_nhat_muse_10s(tmp_path):
    c = _may([_nhan()])
    anh = _anh(tmp_path)
    tid = c.gen_video_i2v("Nia blinks once.", anh, giay=10, am=False, model="grok-imagine-video-1.5")
    assert tid == mgs.TIEN_TO_TASK + UUID, "mã task mang tiền tố riêng: app biết nhà khi hỏi trạng thái"
    g = c._session.goi[0]
    assert g["method"] == "POST" and g["url"] == BASE + "/videos"
    assert g["headers"]["Authorization"] == "Bearer gsk_test_khoa"
    t = g["json"]
    assert {k: t[k] for k in ("videoModel", "prompt", "ratio", "durationSeconds", "outputCount")} == {
        "videoModel": "muse", "prompt": "Nia blinks once.", "ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
        "durationSeconds": 10, "outputCount": 1}, "model Grok của app không đi sang: Gensuite chỉ có Muse"
    assert t["referenceImageUrls"] == ["data:image/png;base64," + base64.b64encode(anh.read_bytes()).decode()]


def test_ref_toi_da_ba_anh(tmp_path):
    c = _may([_nhan()])
    anh = [_anh(tmp_path, f"{k}.png") for k in range(4)]
    c.gen_video_ref("Image 1 is the room.", anh[:3], giay=10)
    t = c._session.goi[0]["json"]
    assert len(t["referenceImageUrls"]) == 3 and t["prompt"] == "Image 1 is the room."
    with pytest.raises(AigenError, match="3 ảnh"):
        c.gen_video_ref("p", anh, giay=10)
    with pytest.raises(AigenError, match="3 ảnh"):
        c.gen_video_ref("p", [], giay=10)
    assert len(c._session.goi) == 1, "sai số ảnh thì không gửi"


def test_khong_phai_10s_thi_bao_khong_gui(tmp_path):
    """Prompt nói N giây mà video 10 s là lệch nhịp: nơi gọi phải ghép prompt cho 10 s."""
    c = _may([])
    for g in (6, 15, 30):
        with pytest.raises(AigenError, match="10 giây"):
            c.gen_video_i2v("p", _anh(tmp_path), giay=g)
    assert c._session.goi == []


def test_prompt_qua_5000_ky_tu_bao_ro_khong_tu_cat(tmp_path):
    c = _may([_nhan()])
    with pytest.raises(AigenError, match="5.001 ký tự"):
        c.gen_video_i2v("x" * 5001, _anh(tmp_path), giay=10)
    assert c._session.goi == []
    c.gen_video_i2v("x" * 5000, _anh(tmp_path), giay=10)
    assert len(c._session.goi[0]["json"]["prompt"]) == 5000


def test_anh_qua_8mb_bao_ro(tmp_path, monkeypatch):
    c = _may([])
    monkeypatch.setattr(mgs, "ANH_TOI_DA_BYTE", 100)
    with pytest.raises(AigenError, match="8 MB"):
        c.gen_video_i2v("p", _anh(tmp_path), giay=10)
    assert c._session.goi == []


def test_429_doi_retry_after_roi_gui_lai(tmp_path, ngu):
    c = _may([_Tra(429, {"error": "RATE_LIMITED", "message": "video_rate_limited", "retryAfterSeconds": 15}),
              _nhan()])
    assert c.gen_video_i2v("p", _anh(tmp_path), giay=10) == mgs.TIEN_TO_TASK + UUID
    assert len(c._session.goi) == 2 and ngu == [15]


def test_429_mai_thi_dung_co_tran(tmp_path, ngu):
    c = _may([_Tra(429, {"error": "RATE_LIMITED", "retryAfterSeconds": 15})] * 10)
    with pytest.raises(AigenError, match="429"):
        c.gen_video_i2v("p", _anh(tmp_path), giay=10)
    assert 1 < len(c._session.goi) <= 5 and len(ngu) == len(c._session.goi) - 1


@pytest.mark.parametrize("ma", [402, 500, 502])
def test_post_loi_khac_bao_ngay_khong_gui_lai(tmp_path, ngu, ma):
    """402 hết credit; 5xx thì có thể job ĐÃ tạo — không có lệnh liệt kê job, gửi lại là mất dấu
    một job và có thể trả tiền hai lần. Báo, để người bấm lại."""
    c = _may([_Tra(ma, {"error": "INSUFFICIENT_CREDITS" if ma == 402 else "boom", "message": "x"}), _nhan()])
    with pytest.raises(AigenError, match=str(ma)) as e:
        c.gen_video_i2v("p", _anh(tmp_path), giay=10)
    assert len(c._session.goi) == 1 and not ngu
    if ma == 402:
        assert "credit" in str(e.value)


def test_nop_khong_tra_id_thi_bao(tmp_path):
    c = _may([_Tra(202, {"batchId": "b1", "items": []})])
    with pytest.raises(AigenError, match="id"):
        c.gen_video_i2v("p", _anh(tmp_path), giay=10)


@pytest.mark.parametrize("tra,mong", [
    ({"status": "queued", "progress": 0}, {"status": "queued"}),
    ({"status": "processing", "progress": 40}, {"status": "processing"}),
    ({"status": "success", "downloadUrl": "https://scontent.xx.fbcdn.net/v/a.mp4?x=1"},
     {"status": "succeeded", "video_url": "https://scontent.xx.fbcdn.net/v/a.mp4?x=1"}),
    ({"status": "success", "downloadUrl": None, "outputs": [{"downloadUrl": "https://scontent.xx.fbcdn.net/b.mp4"}]},
     {"status": "succeeded", "video_url": "https://scontent.xx.fbcdn.net/b.mp4"}),
    ({"status": "failed", "error": "content blocked", "providerMessage": "policy"},
     {"status": "failed", "loi": "content blocked"}),
    ({"status": "failed", "error": None, "providerMessage": "policy"}, {"status": "failed", "loi": "policy"}),
    ({"status": "cancelled"}, {"status": "cancelled", "loi": "cancelled"}),
])
def test_trang_thai_cung_hinh_dang_hai_nha_kia(tra, mong):
    c = _may([_Tra(200, dict(tra, id=UUID))])
    assert c.trang_thai_video(mgs.TIEN_TO_TASK + UUID) == mong
    g = c._session.goi[0]
    assert g["method"] == "GET" and g["url"] == f"{BASE}/videos/{UUID}", "bỏ tiền tố trước khi hỏi"


def test_xong_ma_khong_co_duong_tai_thi_bao_loi_khong_quen_ma():
    """Trả `failed` là route quên mã -> mất video đã dựng. Ném lỗi: mã còn trong kho, hỏi lại được."""
    c = _may([_Tra(200, {"id": UUID, "status": "success", "downloadUrl": None, "outputs": []})])
    with pytest.raises(AigenError, match="downloadUrl"):
        c.trang_thai_video(mgs.TIEN_TO_TASK + UUID)


def test_hoi_trang_thai_429_khong_thu_lai_mang_ma(ngu):
    """Như Lightvisual: trang hỏi lại sau 20 s; route thấy `ma` 429 thì trả 'đang'."""
    c = _may([_Tra(429, {"error": "RATE_LIMITED", "retryAfterSeconds": 15})])
    with pytest.raises(AigenError) as e:
        c.trang_thai_video(mgs.TIEN_TO_TASK + UUID)
    assert getattr(e.value, "ma", None) == 429 and len(c._session.goi) == 1 and not ngu


def test_hoi_trang_thai_502_thi_cho_roi_hoi_lai(ngu):
    c = _may([_Tra(502, {"error": "bad gateway"}), _Tra(200, {"id": UUID, "status": "processing"})])
    assert c.trang_thai_video(mgs.TIEN_TO_TASK + UUID) == {"status": "processing"}
    assert len(c._session.goi) == 2 and ngu


def test_tai_video_khong_gui_khoa_sang_cdn(tmp_path):
    """Link tải nằm ở fbcdn: gửi kèm Bearer là đem khoá Gensuite cho bên thứ ba."""
    c = _may([_Tra(200, b"MP4DATA")])
    ra = c.tai_video("https://scontent.xx.fbcdn.net/v/a.mp4?x=1", tmp_path / "v" / "a.mp4")
    assert ra.read_bytes() == b"MP4DATA"
    g = c._session.goi[0]
    assert g["url"] == "https://scontent.xx.fbcdn.net/v/a.mp4?x=1"
    assert "Authorization" not in (g["headers"] or {})


def test_tai_video_hong_thi_bao(tmp_path):
    c = _may([_Tra(403, b"expired")])
    with pytest.raises(AigenError, match="403"):
        c.tai_video("https://scontent.xx.fbcdn.net/v/a.mp4", tmp_path / "a.mp4")
