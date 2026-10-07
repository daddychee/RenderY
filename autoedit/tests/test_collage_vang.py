"""Collage — MỐC VÀNG: động cơ trong repo phải dựng lại ĐÚNG clip user đã duyệt.

Clip `F:\\AutoEdit\\collage_test\\out_CA\\ca1_sang_ca2.mp4` (user 06/10: "đã đáp ứng kỳ vọng").
Khung vàng trích từ chính bộ dựng thử đã ra clip đó (`collage_test/ca_chuyen_dong.py`,
hàm `khung(t)` trước grain) -> `F:\\AutoEdit\\collage\\vang\\`. Biên đạo dưới đây là bản
CHÉP NGUYÊN từ bộ dựng thử; chỉ động cơ là mới (torch thay cv2).

Dữ liệu nằm ngoài repo (ảnh + bản đồ độ sâu ~10 MB) -> máy không có thì bỏ qua.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from autoedit.collage.dung import Canh, Lop, dung_khung  # noqa: E402
from autoedit.collage.nhip import doan, lo_xo, muot  # noqa: E402

VANG = Path(r"F:\AutoEdit\collage\vang")
CA = Path(r"F:\AutoEdit\collage_test\out_CA")
pytestmark = pytest.mark.skipif(not (VANG / "ca1_ca2.json").exists() or not CA.exists(),
                                reason="máy không có dữ liệu mốc vàng ca1->ca2")

W, H = 1080, 1350
T_NOI = 4.35


def _rgba(p):
    from PIL import Image
    return np.asarray(Image.open(p).convert("RGBA"), np.float32) / 255


def _rgb(p):
    from PIL import Image
    return np.asarray(Image.open(p).convert("RGB"), np.float32) / 255


def dung_ca1_ca2():
    """Biên đạo ca1 (bưởi) -> ca2 (xe hồng), chép nguyên từ bộ dựng thử đã duyệt."""
    from scipy.ndimage import gaussian_filter

    d = gaussian_filter(np.load(CA / "ca1_dosau.npy"), 2, truncate=3.0)
    v = np.clip((d - np.percentile(d, 1)) / (np.percentile(d, 99.5) - np.percentile(d, 1)), 0, 1)
    Z1 = (1 / (v * (1 / 3.0 - 1 / 40.0) + 1 / 40.0)).astype(np.float32)
    ca1 = Canh(_rgb(CA / "ca1_nen.png"), Z1, W, H, zoom=1.12)
    cx, cy, r = np.load(CA / "ca1_buoi_hinh.npy")
    yy, xx = np.mgrid[0:ca1.PH, 0:ca1.PW]
    Z_che = Z1[(np.hypot(xx - cx, yy - cy) <= r) & (Z1 < 30)]
    z_buoi = float(min(np.percentile(Z_che, 90) * 1.25, 34))

    len_buoi, bat_nhom, ha_cam = lo_xo(0.78, 0.45), lo_xo(0.62, 0.28), lo_xo(0.85, 0.9)
    ham, ham_F = lo_xo(0.9, 0.45), lo_xo(0.95, 1.0)
    ca1.them(Lop(_rgba(CA / "ca1_buoi.png"), z_buoi, z_test=True,
                 anim=lambda t: (0, 400 * (1 - len_buoi(t - 0.1)), 0, 1, 0)))
    ca1.them(Lop(_rgba(CA / "ca1_nhom.png"), 2.7,
                 anim=lambda t: (0, 520 * (1 - bat_nhom(t - 0.55)), 0, 1 - 0.06 * (1 - bat_nhom(t - 0.55)), 0)))

    def cam1(t):
        h = ha_cam(t - 0.9)
        vut = doan(t, 3.75, T_NOI) ** 3
        return (120 * muot(doan(t, 2.2, T_NOI)), -300 + 450 * h, 0.25 * muot(doan(t, 2.3, 3.8)),
                1.0, 0.0, 200 - 350 * h + 1700 * vut)

    ca2 = Canh(_rgb(CA / "ca2_nen.png"), np.full((1500, 1200), 20.0, np.float32), W, H, zoom=1.15)

    def cam2(u):
        return (-150 + 300 * muot(doan(u, 0.5, 4.6)), 0.0, 0.3 * muot(doan(u, 0.6, 4.6)),
                1 + 0.15 * (1 - ham_F(u)), 0.0, -1500 * (1 - ham(u)))

    def anim_xe2(u):
        dz = -0.8 * muot(doan(u, 0.2, 4.6))
        tx, ty, tz, F, px, py = cam2(u)
        huy = -py * (3.4 + dz - tz) / (F * 3.4)
        return 0, 14 * math.sin(2 * math.pi * 0.55 * u) + huy, 2.2 * math.sin(2 * math.pi * 0.35 * u), 1, dz

    xe2 = ca2.them(Lop(_rgba(CA / "ca2_xe.png"), 3.4, anim=anim_xe2))

    def xe2_man_hinh(u):
        tx, ty, tz, F, px, py = cam2(u)
        ox, oy, _, m, dz = anim_xe2(u)
        Zc = xe2.Z0 + dz
        return (F * ((xe2.X + ox) * xe2.Z0 - tx) / (Zc - tz) + px,
                F * ((xe2.Y + oy) * xe2.Z0 - ty) / (Zc - tz) + py,
                xe2.anh.shape[1] * xe2.k * m * F * xe2.Z0 / (Zc - tz))

    def duong_xe1(t):
        if t < 2.9:
            return -2500, -300, 300, -10
        if t < 3.75:
            u = muot(doan(t, 2.9, 3.75))
            return -760 + 680 * u, -330 + 80 * u - 40 * math.sin(math.pi * u), 300 + 120 * u, -10 + 6 * u
        u = doan(t, 3.75, T_NOI) ** 1.6
        x2, y2, r2 = xe2_man_hinh(0.0)
        return -80 + (x2 + 80) * u, -250 + (y2 + 250) * u, 420 + (r2 - 420) * u, -4 + 4 * u

    def anim_xe1(t, Z=9.0):
        sx, sy, rong, goc = duong_xe1(t)
        tx, ty, tz, F, px, py = cam1(t)
        sc = F * Z / (Z - tz)
        return (((sx - px) * (Z - tz) / F + tx) / Z, ((sy - py) * (Z - tz) / F + ty) / Z, goc,
                rong / (xe2.anh.shape[1] * xe2.k * sc), 0)

    # vật nối cảnh: cố ý đè lên mọi thứ (bộ thử vẽ nó sau cùng)
    ca1.them(Lop(xe2.anh, 9.0, anim=anim_xe1, X=0.0, Y=0.0, k=xe2.k, tang=1))

    def khung(t):
        if t < T_NOI:
            return dung_khung(ca1, cam1(t), t, phan_xa=t > 3.75)
        u = t - T_NOI
        return dung_khung(ca2, cam2(u), u, phan_xa=abs(cam2(u)[5]) > 95)

    return khung, duong_xe1, xe2_man_hinh


@pytest.fixture(scope="module")
def ca1_ca2():
    return dung_ca1_ca2()


def _psnr(a, b):
    mse = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))
    return 99.0 if mse < 1e-12 else 10 * math.log10(1 / mse)


@pytest.mark.parametrize("t", json.loads((VANG / "ca1_ca2.json").read_text(encoding="utf-8"))["ts"]
                         if (VANG / "ca1_ca2.json").exists() else [])
def test_khung_khop_moc_vang(ca1_ca2, t):
    khung, _, _ = ca1_ca2
    img, lo = khung(t)
    vang = _rgb(VANG / f"ca1_ca2_{t:.2f}.png")
    assert img.shape == vang.shape
    assert _psnr(np.clip(img, 0, 1), vang) >= 38, f"t={t}: lệch mốc vàng"
    if not (3.75 < t < T_NOI + 0.45):               # ngoài lúc lia vút: không lộ mép
        assert lo == 0.0


def test_xe_noi_canh_trung_vi_tri_va_co(ca1_ca2):
    _, duong_xe1, xe2_man_hinh = ca1_ca2
    a = duong_xe1(T_NOI - 1e-9)[:3]
    b = xe2_man_hinh(0.0)
    assert np.allclose(a, b, atol=0.5)
