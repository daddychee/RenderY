"""Collage — ĐỘNG CƠ dựng 2.5D (thay After Effects, user chốt 06/10/2026).

Mọi thông số ở đây đã đo thật trên clip user duyệt (`ca1_sang_ca2.mp4`) và trên video
mẫu — xem `.claude/skills/collage-chuyen-dong/ky-thuat.md`. Động cơ chạy bằng torch:
CPU hôm nay, GPU khi nâng cấp mà KHÔNG sửa code (cùng một hàm, khác `thiet_bi`).

Camera: xo = F*(X*Z0 - tx)/(Z - Tz) + pan. Đứng yên (0,0,0,1,0,0) thì khung = ảnh gốc.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from autoedit.collage import nhip  # noqa: E402
from autoedit.collage.dung import Canh, Lop, dung_khung, so_mau  # noqa: E402

DUNG_YEN = (0.0, 0.0, 0.0, 1.0, 0.0, 0.0)          # tx, ty, Tz, F, pan_x, pan_y


def psnr(a, b):
    mse = float(np.mean((np.asarray(a, np.float64) - np.asarray(b, np.float64)) ** 2))
    return 99.0 if mse < 1e-12 else 10 * math.log10(1 / mse)


def nen_ngau_nhien(h, w, seed=0):
    r = np.random.default_rng(seed)
    # texture mượt (không nhiễu trắng) để nội suy song tuyến không làm lệch số đo
    tho = r.random((h // 8 + 2, w // 8 + 2, 3)).astype(np.float32)
    from PIL import Image
    return np.asarray(Image.fromarray((tho * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC),
                      np.float32) / 255


def the_vuong(h, w, mau, canh=20):
    """Mảnh RGBA (alpha thẳng) hình vuông `canh` px giữa khung h×w."""
    a = np.zeros((h, w, 4), np.float32)
    y0, x0 = h // 2 - canh // 2, w // 2 - canh // 2
    a[y0:y0 + canh, x0:x0 + canh, :3] = mau
    a[y0:y0 + canh, x0:x0 + canh, 3] = 1
    return a


def tam(img, mau):
    """Trọng tâm các pixel gần màu `mau` -> (x, y)."""
    d = np.abs(img - np.float32(mau)).sum(-1) < 0.15
    ys, xs = np.nonzero(d)
    assert len(xs), "không thấy vật trong khung"
    return xs.mean(), ys.mean()


# ------------------------------------------------------------------ nhịp
def test_lo_xo_toi_90_phan_tram_dung_t90():
    for zeta, t90 in ((0.62, 0.28), (0.85, 0.9), (0.95, 1.0)):
        f = nhip.lo_xo(zeta, t90)
        assert abs(f(t90) - 0.9) < 0.01
        assert f(0) == 0.0 and abs(f(20) - 1) < 1e-3


def test_vot_dau_dinh_toc_do_khop_so_do_vox():
    # demo Vox đo: đỉnh tốc độ 0,08–0,17 s trong cú ~0,85 s
    dinh = nhip.dinh_toc_do(nhip.VOT_DAU) * 0.85
    assert 0.08 <= dinh <= 0.17


def test_posterize_chat_bac_thoi_gian():
    assert nhip.posterize(0.49, 12) == pytest.approx(5 / 12)
    assert nhip.posterize(0.5, 12) == pytest.approx(6 / 12)


def test_giu_theo_chu_kep_1_den_2_2_giay():
    assert nhip.giu_theo_chu(0) == 1.0
    assert nhip.giu_theo_chu(18) == pytest.approx(1.33, abs=0.01)
    assert nhip.giu_theo_chu(500) == 2.2


# ------------------------------------------------------------------ dựng
def test_dung_yen_khung_khop_anh_goc():
    """Bù scale: camera đứng yên thì mọi lớp (ở mọi độ sâu) nằm đúng chỗ như ảnh gốc."""
    h, w = 120, 160
    nen = nen_ngau_nhien(h, w)
    vat = the_vuong(h, w, (1, 0, 0))
    c = Canh(nen, z=np.full((h, w), 30, np.float32), W=w, H=h, zoom=1.0)
    c.them(Lop(vat, Z0=4.0))
    img, lo = dung_khung(c, DUNG_YEN, 0.0)
    mong = nen * (1 - vat[..., 3:]) + vat[..., :3] * vat[..., 3:]
    assert psnr(img, mong) > 40
    assert lo == 0.0


def test_parallax_gan_chay_nhieu_xa_chay_it():
    """Camera DỊCH ngang tx: vật ở độ sâu Z dịch tx/Z px — gần chạy nhiều, xa chạy ít."""
    h, w = 120, 320
    c = Canh(np.zeros((h, w, 3), np.float32), z=np.full((h, w), 50, np.float32), W=w, H=h, zoom=1.0)
    # lệch dọc nhau: chồng khít thì vật gần che kín vật xa, không đo được vật xa
    c.them(Lop(np.roll(the_vuong(h, w, (1, 0, 0)), -30, 0), Z0=2.0))
    c.them(Lop(np.roll(the_vuong(h, w, (0, 1, 0)), 30, 0), Z0=20.0))
    a, _ = dung_khung(c, DUNG_YEN, 0.0)
    b, _ = dung_khung(c, (100.0, 0, 0, 1, 0, 0), 0.0)
    gan = tam(a, (1, 0, 0))[0] - tam(b, (1, 0, 0))[0]
    xa = tam(a, (0, 1, 0))[0] - tam(b, (0, 1, 0))[0]
    assert gan == pytest.approx(100 / 2, abs=1.0)
    assert xa == pytest.approx(100 / 20, abs=1.0)


def test_xa_ve_truoc_gan_ve_sau_bat_ke_thu_tu_khai_bao():
    """Collage 3 trạm 06/10: vẽ theo thứ tự khai báo -> trăng ở xa đè lên người ở gần."""
    h, w = 100, 100
    c = Canh(np.zeros((h, w, 3), np.float32), z=np.full((h, w), 50, np.float32), W=w, H=h, zoom=1.0)
    c.them(Lop(the_vuong(h, w, (1, 0, 0)), Z0=2.0))    # gần, khai báo TRƯỚC
    c.them(Lop(the_vuong(h, w, (0, 1, 0)), Z0=20.0))   # xa, khai báo SAU
    img, _ = dung_khung(c, DUNG_YEN, 0.0)
    assert np.allclose(img[50, 50], (1, 0, 0), atol=0.02)
    c.lop[1].tang = 1                                  # ép vật xa lên trên (vật nối cảnh)
    img, _ = dung_khung(c, DUNG_YEN, 0.0)
    assert np.allclose(img[50, 50], (0, 1, 0), atol=0.02)


def test_doi_tieu_cu_tren_tam_phang_chi_phong_deu():
    """Bài học v2 (user bác 'chỉ scale'): đổi F KHÔNG ra parallax — hai vật lệch nhau giữ nguyên tỉ lệ."""
    h, w = 160, 160
    c = Canh(np.zeros((h, w, 3), np.float32), z=np.full((h, w), 50, np.float32), W=w, H=h, zoom=1.0)
    gan = the_vuong(h, w, (1, 0, 0), 10); gan = np.roll(gan, -40, 1)
    xa = the_vuong(h, w, (0, 1, 0), 10); xa = np.roll(xa, 40, 1)
    c.them(Lop(gan, Z0=2.0))
    c.them(Lop(xa, Z0=20.0))
    b, _ = dung_khung(c, (0, 0, 0, 1.5, 0, 0), 0.0)
    xg, xx = tam(b, (1, 0, 0))[0] - w / 2, tam(b, (0, 1, 0))[0] - w / 2
    assert xg == pytest.approx(-40 * 1.5, abs=1.0) and xx == pytest.approx(40 * 1.5, abs=1.0)


def test_nen_co_do_sau_tung_pixel_lech_tang():
    """Nền nửa trái gần (Z=2), nửa phải xa (Z=20): trượt ngang thì hai nửa dịch khác nhau."""
    h, w = 100, 400
    nen = np.zeros((h, w, 3), np.float32)
    nen[45:55, 95:105] = (1, 0, 0)        # chấm đỏ nửa trái
    nen[45:55, 295:305] = (0, 0, 1)       # chấm xanh nửa phải
    z = np.full((h, w), 20, np.float32)
    z[:, :200] = 2
    c = Canh(nen, z=z, W=w, H=h, zoom=1.0)
    b, _ = dung_khung(c, (40.0, 0, 0, 1, 0, 0), 0.0)
    assert 100 - tam(b, (1, 0, 0))[0] == pytest.approx(40 / 2, abs=1.5)
    assert 300 - tam(b, (0, 0, 1))[0] == pytest.approx(40 / 20, abs=1.5)


def test_z_buffer_nui_che_vat_o_xa_hon():
    """Mảnh z_test ở Z=10: chỗ nền gần hơn (Z=3) che mảnh, chỗ nền xa hơn (Z=40) thì mảnh hiện."""
    h, w = 100, 100
    nen = np.full((h, w, 3), 0.2, np.float32)
    z = np.full((h, w), 40, np.float32)
    z[50:] = 3                            # nửa dưới là "núi" gần
    c = Canh(nen, z=z, W=w, H=h, zoom=1.0)
    vat = np.zeros((h, w, 4), np.float32)
    vat[20:80, 30:70] = (1, 1, 0, 1)
    c.them(Lop(vat, Z0=10.0, z_test=True))
    img, _ = dung_khung(c, DUNG_YEN, 0.0)
    assert np.allclose(img[30, 50], (1, 1, 0), atol=0.05)       # trên: mảnh hiện
    assert np.allclose(img[70, 50], (0.2, 0.2, 0.2), atol=0.05)  # dưới: núi che


def test_lo_mep_bang_0_khi_dung_yen_va_duong_khi_lia_qua_vung_du():
    h, w = 100, 100
    c = Canh(nen_ngau_nhien(h, w), z=np.full((h, w), 20, np.float32), W=w, H=h, zoom=1.2)
    _, lo0 = dung_khung(c, DUNG_YEN, 0.0)
    _, lo1 = dung_khung(c, (0, 0, 0, 1, 0, 30.0), 0.0)        # dư 10 px, lia 30 px
    assert lo0 == 0.0
    assert lo1 == pytest.approx(20 / 100, abs=0.02)


def test_anim_lop_lech_va_an():
    h, w = 100, 200
    c = Canh(np.zeros((h, w, 3), np.float32), z=np.full((h, w), 50, np.float32), W=w, H=h, zoom=1.0)
    c.them(Lop(the_vuong(h, w, (1, 0, 0)), Z0=5.0, anim=lambda t: (30.0 * t, 0.0, 0.0, 1.0, 0.0)))
    a, _ = dung_khung(c, DUNG_YEN, 0.0)
    b, _ = dung_khung(c, DUNG_YEN, 1.0)
    assert tam(b, (1, 0, 0))[0] - tam(a, (1, 0, 0))[0] == pytest.approx(30, abs=1.0)


def test_so_mau_motion_blur_theo_quang_dich():
    assert so_mau(0.3) == 1
    assert so_mau(12.0) > 1
    assert so_mau(10_000.0) == 16


@pytest.mark.skipif(not torch.cuda.is_available(), reason="máy chưa có GPU CUDA")
def test_gpu_ra_giong_cpu():
    h, w = 120, 160
    c = Canh(nen_ngau_nhien(h, w), z=np.full((h, w), 30, np.float32), W=w, H=h, zoom=1.1)
    c.them(Lop(the_vuong(h, w, (1, 0, 0)), Z0=4.0))
    a, _ = dung_khung(c, (50, 10, 0.5, 1.1, 3, -4), 0.0, thiet_bi="cpu")
    b, _ = dung_khung(c, (50, 10, 0.5, 1.1, 3, -4), 0.0, thiet_bi="cuda")
    assert psnr(a, b) > 45
