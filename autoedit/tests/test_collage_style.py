"""Collage — 3 STYLE user chốt 07/10/2026 (đã duyệt bằng 3 video thử "Những thành phố mơ màng"):

  collage    "Collage art": giữ ảnh, lớp trồi kiểu Rockefeller, 30 hình/giây + nhoè chuyển động.
  black_grid "Black Grid" : nền tối có lưới, lớp cắt viền giấy + bóng, 12 hình/giây (xuất 24), hạt + nhấp nháy.
  non_grid   "Non-Grid"   : như Black Grid nhưng GIỮ nền ảnh.
Test dùng độ sâu / SAM / LaMa GIẢ.
"""

from __future__ import annotations

import json
import shutil
import subprocess

import numpy as np
import pytest

pytest.importorskip("torch")

from autoedit.collage import mau, phong  # noqa: E402

CO_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
W, H = 192, 108


def test_vien_giay_kem_ngoai_vat_va_bong_lech():
    a = np.zeros((80, 80), np.float32)
    a[30:50, 30:50] = 1
    rgb = np.zeros((80, 80, 3), np.float32)
    rgb[..., 2] = 1
    mau_, al = phong.vien_giay(rgb, a, seed=1)
    assert al[40, 40] > 0.99 and np.allclose(mau_[40, 40], (0, 0, 1), atol=0.02), "trong vật giữ nguyên"
    vien = al[40, 53] > 0.9 and np.allclose(mau_[40, 53], phong.KEM, atol=0.05)
    assert vien, "ngay ngoài mép vật là viền giấy kem"
    assert al[62, 66] > 0.05 and mau_[62, 66].max() < 0.1, "bóng đổ đen lệch xuống-phải"
    assert al[18, 18] < 0.02, "xa vật trong suốt"


def test_nen_luoi_toi_co_duong_ke():
    n = phong.nen_luoi(120, 200)
    assert n.mean() < 0.15 and n[0, :].mean() > n[30, :].mean() + 0.005, "nền tối, hàng kẻ sáng hơn"


def test_hau_ky_khong_tran_va_vox_co_hat():
    img = np.full((H, W, 3), 0.5, np.float32)
    a = phong.hau_ky(img, 0, 0.0, "collage")
    b = phong.hau_ky(img, 0, 0.0, "black_grid")
    assert 0 <= a.min() and a.max() <= 1 and 0 <= b.min() and b.max() <= 1
    assert b.std() > a.std(), "Black Grid hạt đậm hơn Collage art"


# ═══════ dựng thật bằng ffmpeg, model giả ═════════════════════════════════════
def _anh(tmp_path, ten, seed, w=320, h=180):
    from PIL import Image
    r = np.random.default_rng(seed)
    a = (r.random((h // 8 + 1, w // 8 + 1, 3)) * 255).astype(np.uint8)
    p = tmp_path / ten
    Image.fromarray(a).resize((w, h), Image.BICUBIC).save(p)
    return p


class _Sam:
    def tach_khung(self, rgb, k):
        m = np.zeros(rgb.shape[:2], bool)
        x0, y0, x1, y1 = k
        m[y0 + 2:y1 - 2, x0 + 2:x1 - 2] = True
        return m


def _giay_va_so_khung(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries",
                        "stream=nb_read_frames,r_frame_rate:format=duration", "-of", "json", str(p)],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    return float(j["format"]["duration"]), int(j["streams"][0]["nb_read_frames"]), j["streams"][0]["r_frame_rate"]


def _khung_khac(p):
    f = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "rawvideo", "-pix_fmt", "gray",
                                      "-"], capture_output=True).stdout, np.uint8).reshape(-1, H, W).astype(np.int16)
    return sum(1 for i in range(1, len(f)) if np.abs(f[i] - f[i - 1]).mean() > 0.5)


@pytest.mark.skipif(not CO_FFMPEG, reason="máy không có ffmpeg")
@pytest.mark.parametrize("style,fps", [("collage", "30/1"), ("black_grid", "24/1"), ("non_grid", "24/1")])
def test_dung_style_chuoi_hai_anh_dung_giay_dung_fps(tmp_path, style, fps):
    ds = [{"anh": str(_anh(tmp_path, "a.png", 0)), "giay": 1.5, "khung_lop": [[0.3, 0.4, 0.7, 1.0]]},
          {"anh": str(_anh(tmp_path, "b.png", 1)), "giay": 1.0, "khung_lop": []}]
    ra = tmp_path / "ra.mp4"
    mau.dung_style(ds, ra, W=W, H=H, style=style, sam=_Sam(),
                   uoc_do_sau=lambda x: np.full(x.shape[:2], 20.0, np.float32), va_nen=lambda a, m: a * 0 + 0.3)
    giay, n, r = _giay_va_so_khung(ra)
    assert abs(giay - 2.5) < 0.15 and r == fps
    if style != "collage":
        assert _khung_khac(ra) <= n // 2 + 2, "12 hình/giây xuất 24: mỗi hình lặp 2 khung"


def test_tho_dung_style_dung_khung(tmp_path, monkeypatch):
    from autoedit.collage import tho
    goi = []
    monkeypatch.setattr(mau, "dung_style", lambda ds, ra, **k: goi.append((ds, k.get("W"), k.get("H"), k.get("style"))))
    ch = {"anh": [{"anh": "a.png", "giay": 2.0, "khung_lop": [[0, 0, 1, 1]]}], "khung": "9:16", "style": "non_grid"}
    tho.dung_mac_dinh({"id": "vox-1", "model": "VOX-style", "anh": str(tmp_path / "a.png"), "giay": 2, "cd": "",
                       "nhan": "", "chuoi": json.dumps(ch)}, goc=tmp_path / "collage")
    assert goi == [(ch["anh"], 1080, 1920, "non_grid")]



def test_bong_do_khong_cuon_sang_mep_doi_dien():
    """Đo thật 07/10: bóng đổ dịch bằng phép CUỘN -> bóng tảng đá sát đáy ảnh hiện ở mép TRÊN, hộp bao
    lớp phủ cả khung -> camera Black Grid không tìm được cú nào (đứng im cả clip)."""
    a = np.zeros((80, 80), np.float32)
    a[60:, 10:70] = 1                                       # vật chạm đáy ảnh
    _, al = phong.vien_giay(np.zeros((80, 80, 3), np.float32), a, seed=1)
    assert al[:20].max() < 0.01, "mép trên không được có bóng"
    b = np.zeros((80, 80), np.float32)
    b[10:50, 60:] = 1                                       # vật chạm mép phải
    _, al = phong.vien_giay(np.zeros((80, 80, 3), np.float32), b, seed=1)
    assert al[:, :20].max() < 0.01, "mép trái không được có bóng"


# ═══════ nhập PSD: dùng THẲNG layer người cắt (user chốt 08/10) ══════════════════════════════════════
def _psd_canh(tmp_path, lo_nen=False):
    """Canvas 192x108 từ dưới lên: Nen · 'Chu' (dải cao giữa trời — luật vai trò xếp 'rơi', GẦN) ·
    'De' (khối to chạm đáy — luật vai trò xếp 'đế', XA). PSD bảo De nằm TRÊN Chu -> De phải gần hơn."""
    pytest.importorskip("psd_tools")
    from PIL import Image
    from psd_tools import PSDImage
    from psd_tools.api.layers import PixelLayer

    p = PSDImage.new("RGB", (W, H), color=(0, 0, 0))
    nen = Image.new("RGBA", (W, H), (40, 80, 160, 255))
    if lo_nen:
        nen.paste((0, 0, 0, 0), (60, 60, 130, 108))
    p.append(PixelLayer.frompil(nen, p, "Nen", 0, 0))
    p.append(PixelLayer.frompil(Image.new("RGBA", (90, 14), (250, 250, 250, 255)), p, "Chu", 4, 50))
    p.append(PixelLayer.frompil(Image.new("RGBA", (110, 50), (200, 40, 40, 255)), p, "De", 58, 40))
    duong = tmp_path / "a.psd"
    p.save(str(duong))
    return duong


class _SamCam:
    """Nhánh PSD KHÔNG được gọi máy cắt."""

    def __getattr__(self, ten):
        raise AssertionError(f"nhánh PSD gọi máy cắt: {ten}")


def test_psd_lop_gan_xa_theo_thu_tu_xep_chong_cua_psd(tmp_path):
    canh, _ = mau._canh_psd(_psd_canh(tmp_path), [1, 2], 3.0, "non_grid", W, H, va_nen=lambda a, m: a, seed=0)
    z = [L.Z0 for L in canh.lop]
    assert len(z) == 2 and z[1] < z[0], f"De nằm trên Chu trong PSD -> phải gần hơn (Z nhỏ hơn), ra {z}"


def test_psd_nen_trong_duoc_va(tmp_path):
    vao = []

    def va(a, m):
        vao.append(m.copy())
        return a * 0 + 0.5

    canh, _ = mau._canh_psd(_psd_canh(tmp_path, lo_nen=True), [1, 2], 3.0, "non_grid", W, H, va_nen=va, seed=0)
    # vá ở độ phân giải GỐC rồi mới phóng — đo thật 08/10: vá sau khi phóng 3 lần (3840x2160) LaMa đòi 29,7 GB, chết
    assert vao and vao[0].shape == (H, W), "LaMa chạy ở cỡ PSD gốc, không ở cỡ đã phóng"
    assert vao[0][80, 90] and not vao[0][10, 10], "chỉ vá đúng chỗ nền trống"
    k = canh.PW // W                                                 # PSD nhỏ được phóng trước khi dựng
    assert np.allclose(canh.nen[80 * k, 90 * k], 0.5, atol=0.02)


@pytest.mark.skipif(not CO_FFMPEG, reason="máy không có ffmpeg")
def test_dung_style_anh_psd_dung_layer_khong_goi_may_cat(tmp_path, monkeypatch):
    """Ảnh .psd có psd_lop -> dựng từ layer (không thì Pillow mở PSD thành ảnh PHẲNG, mất hết layer)."""
    goi, that = [], mau._canh_psd
    monkeypatch.setattr(mau, "_canh_psd", lambda *a, **k: goi.append(a[1]) or that(*a, **k))
    ds = [{"anh": str(_psd_canh(tmp_path)), "giay": 1.0, "khung_lop": [], "psd_lop": [1, 2]}]
    ra = tmp_path / "ra.mp4"
    mau.dung_style(ds, ra, W=W, H=H, style="black_grid", sam=_SamCam(),
                   uoc_do_sau=lambda x: np.full(x.shape[:2], 20.0, np.float32), va_nen=lambda a, m: a)
    giay, n, r = _giay_va_so_khung(ra)
    assert goi == [[1, 2]] and abs(giay - 1.0) < 0.15 and r == "24/1"


def _chu_hai_net():
    """Hai 'chữ cái' trắng cao 20 px, cách nhau khe 8 px (như khoảng giữa hai chữ)."""
    a = np.zeros((60, 120), np.float32)
    a[20:40, 30:50] = 1
    a[20:40, 58:78] = 1
    rgb = np.ones((60, 120, 3), np.float32)
    return rgb, a


def test_chu_dan_len_dai_giay_lien_khong_vien_tung_net():
    """Đo thật PSD Toyota 08/10 (Non-Grid): viền giấy bao TỪNG NÉT chữ -> chữ nhỏ nhoè, khó đọc. Layer chữ
    phải dán lên MỘT dải giấy kem liền (kiểu Vox), chữ giữ màu."""
    rgb, a = _chu_hai_net()
    mau_, al = mau._dai_giay_chu(rgb * 0.1, a)                       # chữ TỐI
    assert al[30, 54] > 0.9, "khe giữa hai chữ được lấp thành dải giấy"
    assert np.allclose(mau_[30, 54], phong.KEM, atol=0.05), "chữ tối -> giấy kem"
    assert np.allclose(mau_[30, 40], 0.1, atol=0.02), "trong nét chữ giữ màu chữ"
    assert al[5, 5] < 0.05, "xa chữ vẫn trong suốt"


def test_chu_sang_dan_len_giay_toi_cho_doc_duoc():
    """Đo thật PSD Toyota 08/10: chữ TRẮNG dán lên giấy kem -> gần như không đọc được. Chữ sáng -> giấy tối."""
    rgb, a = _chu_hai_net()
    mau_, al = mau._dai_giay_chu(rgb, a)                             # chữ TRẮNG
    assert mau_[30, 54].max() < 0.2 and np.allclose(mau_[30, 40], 1, atol=0.02), "chữ trắng trên giấy tối"


@pytest.mark.parametrize("style", ["non_grid", "black_grid", "collage"])
def test_psd_layer_chu_dan_dai_giay_moi_style(tmp_path, monkeypatch, style):
    """Mọi style đều có viền trắng (user chốt 08/10: "bản chất collage art là có viền trắng quanh element") ->
    layer chữ ở mọi style dán dải giấy, không viền từng nét."""
    from autoedit.collage import psd as mpsd
    duong = _psd_canh(tmp_path)
    that = mpsd.doc
    monkeypatch.setattr(mpsd, "doc", lambda n: {**(d := that(n)), "lop": [dict(x, chu=x["ten"] == "Chu")
                                                                       for x in d["lop"]]})
    goi = []
    monkeypatch.setattr(mau, "_dai_giay_chu", lambda m, a: goi.append(a.shape) or (m, a))
    mau._canh_psd(duong, [1, 2], 3.0, style, W, H, va_nen=lambda a, m: a, seed=0)
    assert len(goi) == 1, "chỉ layer chữ được dán dải giấy"


@pytest.mark.parametrize("style", ["collage", "non_grid"])
def test_moi_style_deu_co_vien_trang_quanh_element(tmp_path, monkeypatch, style):
    """User chốt 08/10: "bản chất collage art là sẽ có viền trắng xung quanh element" -> Collage art cũng có viền
    sticker (trước chỉ Black Grid / Non-Grid có)."""
    goi = []
    that = phong.vien_giay
    monkeypatch.setattr(phong, "vien_giay", lambda *a, **k: goi.append(1) or that(*a, **k))
    mau._canh_psd(_psd_canh(tmp_path), [1, 2], 3.0, style, W, H, va_nen=lambda a, m: a, seed=0)
    assert len(goi) == 2, "mỗi element một viền trắng"


def _bac_thang(a: np.ndarray) -> float:
    """Độ răng cưa của mép chéo: mỗi hàng lấy vị trí alpha cắt 0,5 (nội suy), lệch khỏi đường thẳng khớp nhất."""
    x = []
    for hang in a:
        i = int(np.argmax(hang >= 0.5))
        x.append(i - 1 + (0.5 - hang[i - 1]) / max(hang[i] - hang[i - 1], 1e-6) if 0 < i else np.nan)
    y = np.arange(len(x), dtype=np.float64)
    x = np.asarray(x)
    ok = ~np.isnan(x)
    k = np.polyfit(y[ok], x[ok], 1)
    return float(np.sqrt(np.mean((x[ok] - np.polyval(k, y[ok])) ** 2)))


def test_psd_nho_phong_len_mep_khong_rang_cua():
    """User báo 08/10 (PSD PayPal 1280 px, Collage art): viền răng cưa rất nhiều — alpha sắc cạnh 1280 px bị
    phóng ~2,8 lần chỉ bằng nội suy tuyến tính -> mỗi điểm ảnh gốc thành một bậc thang. Mép phải đều."""
    import torch
    n = 48
    yy, xx = np.mgrid[0:n, 0:n]
    a = (xx > 0.6 * yy + 8).astype(np.float32)                     # mép chéo sắc cạnh
    rgb = np.zeros((n, n, 3), np.float32)
    rgb[a > 0] = (0.9, 0.1, 0.1)                                     # ngoài vật: màu RÁC đen
    thuong = torch.nn.functional.interpolate(torch.from_numpy(a)[None, None], scale_factor=3, mode="bilinear",
                                             align_corners=False)[0, 0].numpy()
    m3, a3 = mau._lam_muot(rgb, a, 3)
    assert a3.shape == (3 * n, 3 * n) and m3.shape == (3 * n, 3 * n, 3)
    cu, moi = _bac_thang(thuong[6:-6]), _bac_thang(a3[6:-6])
    assert moi < 0.5 * cu, f"bậc thang {cu:.2f} px -> {moi:.2f} px"
    vien = (a3 > 0.1) & (a3 < 0.9)
    assert m3[vien][:, 0].min() > 0.8, "mép không ám màu rác đen của vùng trong suốt"


def test_psd_do_phan_giai_thap_duoc_phong_truoc_khi_dung(tmp_path):
    canh, _ = mau._canh_psd(_psd_canh(tmp_path), [1, 2], 3.0, "collage", W, H, va_nen=lambda a, m: a, seed=0)
    assert canh.PW == 2 * W, "PSD cỡ bằng khung xuất (phóng tới 1,15 x 1,6) -> làm việc ở 2 lần"


# ═══════ viền trắng kiểu sticker: tròn, liền khối, dày đều (user chốt 08/10) ═════════════════════════
def _do_day_vien(al_vien: np.ndarray, a: np.ndarray, buoc: int = 6) -> list[float]:
    """Độ dày viền đo theo nhiều hướng từ tâm vật: từ mép vật (a>=0,5) tới mép viền (alpha>=0,5)."""
    cy, cx = (np.array(np.nonzero(a >= 0.5)).mean(1))
    ra = []
    for goc in np.arange(0, 360, buoc):
        dy, dx = np.sin(np.radians(goc)), np.cos(np.radians(goc))
        r = np.arange(0, 200, 0.25)
        ys, xs = (cy + r * dy).astype(int), (cx + r * dx).astype(int)
        ok = (ys >= 0) & (ys < a.shape[0]) & (xs >= 0) & (xs < a.shape[1])
        ys, xs, r = ys[ok], xs[ok], r[ok]
        vat, vien = a[ys, xs] >= 0.5, al_vien[ys, xs] >= 0.5
        if vat.any() and vien.any():
            ra.append(r[np.nonzero(vien)[0].max()] - r[np.nonzero(vat)[0].max()])
    return ra


def test_vien_trang_day_deu_khong_nham_nho():
    """User 08/10 (ảnh Non-Grid nhóm CIA): viền trắng nham nhở — viền cộng nhiễu ±2,2 px giả giấy xé.
    Muốn viền tròn liền khối: dày ĐỀU quanh vật, không phụ thuộc hạt ngẫu nhiên."""
    yy, xx = np.mgrid[0:120, 0:120]
    a = (((yy - 60) ** 2 + (xx - 60) ** 2) < 30 ** 2).astype(np.float32)
    rgb = np.zeros((120, 120, 3), np.float32)
    _, al1 = phong.vien_giay(rgb, a, seed=1)
    _, al2 = phong.vien_giay(rgb, a, seed=7)
    vien1 = np.where(a < 0.5, al1, 0)
    day = _do_day_vien(vien1, a)
    assert np.std(day) < 0.8 and 5.5 < np.mean(day) < 8.5, f"dày {np.mean(day):.1f} ± {np.std(day):.2f} px"
    assert np.abs(al1 - al2).max() < 1e-6, "viền không phụ thuộc hạt ngẫu nhiên"


def test_vien_trang_lien_khoi_lap_khe_hep():
    """Hai phần vật cách khe 6 px (như tay và súng): viền lấp kín khe thành một mảng liền."""
    a = np.zeros((80, 120), np.float32)
    a[20:60, 20:57] = 1
    a[20:60, 63:100] = 1
    _, al = phong.vien_giay(np.zeros((80, 120, 3), np.float32), a, seed=1)
    assert al[40, 60] > 0.95, "khe hẹp giữa hai phần được viền lấp liền"


def test_vien_trang_mep_ngoai_tron_khong_bac_thang():
    """Vật có mép chéo bậc thang (cắt độ phân giải thấp): mép ngoài của viền phải trơn."""
    n = 90
    yy, xx = np.mgrid[0:n, 0:n]
    a = (xx > (0.6 * yy).astype(int) * 1.0 + 30).astype(np.float32)   # bậc thang 1 px
    _, al = phong.vien_giay(np.zeros((n, n, 3), np.float32), a, seed=1)
    ngoai = 1 - al                                                     # mép ngoài viền = nơi al cắt 0,5
    assert _bac_thang(1 - ngoai[10:-10]) < 0.2
