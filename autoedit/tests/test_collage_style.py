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
