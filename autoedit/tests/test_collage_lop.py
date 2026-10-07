"""Collage — LỚP theo KHUNG người kéo (user chốt 07/10/2026: "máy đề xuất khung, người sửa").

Đo thật 07/10 trên ảnh "Những thành phố mơ màng": bấm điểm cho SAM vớ bậy trên ảnh đồ hoạ nhiều
mảnh; KHUNG (box prompt) ra đủ chữ/nhà/cây, SAM tự chấm 0,89–0,98. Lớp nào bị lớp trước che thì
VẼ BÙ phần bị che (không bù: cụm nhà thủng lỗ hình cây thông khi cây chưa vào).
Test dùng SAM/LaMa GIẢ — không tải model.
"""

from __future__ import annotations

import numpy as np

from autoedit.collage import lop


def _o(h=120, w=200, y0=0, y1=0, x0=0, x1=0):
    m = np.zeros((h, w), bool)
    m[y0:y1, x0:x1] = True
    return m


class _SamKhung:
    """SAM giả: trả mask đã định sẵn cho từng khung (cố tình tràn ra ngoài khung)."""

    def __init__(self, ds):
        self.ds, self.goi = ds, []

    def tach_khung(self, rgb, khung):
        self.goi.append(tuple(khung))
        return self.ds[len(self.goi) - 1]


def test_khung_ti_le_ra_pixel_va_kep_trong_anh():
    assert lop.khung_px([0.1, 0.2, 0.5, 1.2], 200, 100) == (20, 20, 100, 100)


def test_cat_theo_khung_khong_tran_ra_ngoai_khung_va_lap_lo():
    tran = _o(y0=10, y1=110, x0=10, x1=190)
    tran[50:60, 50:60] = False                              # lỗ giữa
    sam = _SamKhung([tran])
    ms = lop.cat_theo_khung(np.zeros((120, 200, 3), np.float32), [(40, 30, 120, 90)], sam)
    assert sam.goi == [(40, 30, 120, 90)]
    m = ms[0]
    assert not m[:30].any() and not m[:, :40].any() and not m[90:].any() and not m[:, 120:].any()
    assert m[55, 55], "lỗ trong vật phải lấp"


def test_lo_lung_la_vat_nho_DUNG_TACH_RIENG():
    """Đo thật 07/10: cây thông (1,42% khung) nằm giữa cụm nhà bị coi là 'lơ lửng' -> trôi như hành
    tinh thay vì trồi lên. Lơ lửng = nhỏ VÀ không dính lớp nào khác."""
    nha = _o(y0=40, y1=100, x0=40, x1=160)
    cay = _o(y0=30, y1=60, x0=95, x1=105)                  # nhỏ, nằm trong cụm nhà
    sao = _o(y0=5, y1=9, x0=180, x1=184)                    # nhỏ, đứng riêng giữa trời
    ds = [nha, cay, sao]
    assert lop.la_lo_lung(cay, ds) is False
    assert lop.la_lo_lung(sao, ds) is True
    assert lop.la_lo_lung(nha, ds) is False


def test_nen_va_lay_mau_tu_vung_sach_xung_quanh():
    """Đo thật 07/10: LaMa vá lỗ to giữa trời ra MẢNG XÁM sáng hơn trời thật (ảnh thành phố, quả cam).
    Giữ chi tiết LaMa vẽ, nhưng màu nền (tần số thấp) lấy từ vùng sạch xung quanh."""
    rgb = np.full((120, 200, 3), 0.2, np.float32)
    vat = _o(y0=30, y1=90, x0=60, x1=140)
    rgb[vat] = 0.9

    def lama_xam(a, m):
        out = a.copy()
        out[m] = 0.6                                        # mảng xám
        out[m & (np.arange(200)[None, :] % 10 < 5)] += 0.1  # chi tiết sọc
        return out

    nen = lop.nen_sach(rgb, [vat], lama_xam)
    trong = nen[45:75, 80:120]
    assert abs(float(trong.mean()) - 0.25) < 0.06, f"màu nền phải theo vùng sạch (~0,2), ra {trong.mean():.2f}"
    assert float(trong[..., 0].std()) > 0.03, "giữ chi tiết LaMa vẽ (sọc)"


def test_vung_chong_thuoc_lop_gan_hon():
    a, b = _o(y0=0, y1=60, x0=0, x1=100), _o(y0=40, y1=100, x0=50, x1=150)
    ra = lop.chia_vung([a, b], [7.0, 5.0])
    assert not (ra[0] & ra[1]).any()
    assert ra[1][50, 70] and not ra[0][50, 70], "chỗ chồng thuộc lớp GẦN (Z nhỏ)"


def test_ve_bu_phan_bi_lop_truoc_che_trong_duong_bao():
    """Cụm nhà thủng lỗ hình cây (cây đứng trước): bù lỗ đó; KHÔNG bù ra ngoài đường bao cụm nhà."""
    rgb = np.zeros((120, 200, 3), np.float32)
    nha = _o(y0=40, y1=100, x0=40, x1=160)
    cay = _o(y0=20, y1=90, x0=90, x1=110)                   # cây che giữa cụm nhà, ngọn nhô lên trời
    nha &= ~cay
    vao = []

    def lama(a, m):
        vao.append(m.copy())
        return a * 0 + 0.7

    ra = lop.ve_bu(rgb, [nha, cay], [6.8, 6.7], va_nen=lama)
    mau_nha, m_nha = ra[0]
    assert m_nha[60, 100], "lỗ hình cây trong cụm nhà được bù"
    assert not m_nha[25, 100], "ngọn cây nhô lên TRỜI không thuộc đường bao cụm nhà -> không bù"
    assert np.allclose(mau_nha[60, 100], 0.7)
    m_cay = ra[1][1]
    assert (m_cay == cay).all(), "cây đứng trước nhất, không có gì che -> giữ nguyên"


def test_de_xuat_khung_tu_mask_sam_ti_le_0_1():
    class _Sam:
        def tach(self, rgb, pts, nhan=None):
            return [(_o(y0=20, y1=110, x0=80, x1=130), 0.9)]

    z = np.full((120, 200), 30.0, np.float32)
    z[20:110, 80:130] = 5.0
    ds = lop.de_xuat_khung(np.zeros((120, 200, 3), np.float32), z, sam=_Sam())
    assert len(ds) == 1
    x0, y0, x1, y1 = ds[0]
    assert 0.35 < x0 < 0.41 and 0.12 < y0 < 0.18 and 0.64 < x1 < 0.70 and y1 > 0.9
