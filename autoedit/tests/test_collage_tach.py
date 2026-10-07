"""Collage — TÁCH LAYER TỰ ĐỘNG (không ai bấm điểm) cho mẫu "VOX · Pop-up 2.5D".

Đo trên 5 cảnh thật SE001 (06/10/2026): mảng gần theo độ sâu -> điểm gợi ý -> SAM 2 (3 phương
án) -> giữ phương án có MÉP GÃY ĐỘ SÂU rõ nhất -> LaMa vá nền. Tách đúng người họp báo, tháp
tàu ngầm, vai tiền cảnh; cảnh tàu trên biển bị bắt nhầm MẶT BIỂN (gần dần về đáy khung, chạm
cả mép trái lẫn phải) -> luật loại mặt phẳng nền; tên lửa nhìn từ trên: không vật nào -> lùi
về "Chiều sâu" + gắn cờ (luật dự án: đánh dấu chỗ không chắc để review có trọng điểm).

Test ở đây dùng dữ liệu tổng hợp + SAM/LaMa GIẢ — không tải model.
"""

from __future__ import annotations

import numpy as np

from autoedit.collage import tach


def _nen_doc(h=120, w=200):
    """Độ chênh (0 xa .. 1 gần) tăng dần về đáy — như mặt đất/mặt biển."""
    return np.linspace(0.0, 0.6, h, dtype=np.float32)[:, None].repeat(w, 1)


def _vat(h=120, w=200, y0=30, y1=120, x0=70, x1=130):
    m = np.zeros((h, w), bool)
    m[y0:y1, x0:x1] = True
    return m


def test_buoc_mep_cao_o_vat_that_thap_o_mat_phang_nen():
    v = _nen_doc()
    m = _vat()
    v_vat = v.copy()
    v_vat[m] = 0.95                                     # vật nổi hẳn lên
    assert tach.buoc_mep(m, v_vat) > 0.3
    mat_bien = np.zeros_like(m)
    mat_bien[70:] = True                                # nửa dưới = mặt biển, độ sâu chuyển DẦN
    assert tach.buoc_mep(mat_bien, v) < 0.08


def test_loai_mask_cham_ca_mep_trai_lan_phai():
    v = _nen_doc()
    bien = np.zeros((120, 200), bool)
    bien[60:] = True
    v2 = v.copy(); v2[bien] += 0.4                      # kể cả có bước nhảy (đường chân trời)
    assert not tach.hop_le(bien, 0.9, v2), "chạm trái + phải = mặt phẳng nền, không phải vật"
    vat = _vat()
    v3 = v.copy(); v3[vat] = 0.95
    assert tach.hop_le(vat, 0.9, v3), "vật chạm đáy khung (người, tháp tàu) vẫn hợp lệ"


def test_loai_mask_qua_nho_qua_lon_hoac_diem_sam_thap():
    v = np.zeros((120, 200), np.float32)
    nho = _vat(y0=50, y1=53, x0=90, x1=93)
    lon = _vat(y0=0, y1=118, x0=2, x1=198)
    vua = _vat()
    for m in (nho, lon, vua):
        v[m] = 0.9
    assert not tach.hop_le(nho, 0.9, v)
    assert not tach.hop_le(lon, 0.9, v)
    assert not tach.hop_le(vua, 0.3, v), "SAM tự chấm thấp"


def test_loai_mask_manh_nhu_vanh_cung():
    """Đo thật 07/10 (quả cam khung 9:16): SAM ra VÀNH VỎ cam hình cung — mép gãy độ sâu rõ nên thắng,
    bật lên một mình thành vệt cong lơ lửng. Đo 8 ảnh: mảnh sai dày 0,040 (vành) / 0,063 (dải biển),
    vật đúng mỏng nhất 0,104 -> loại dưới 0,08 (bề dày lớn nhất / cạnh dài hộp bao)."""
    h, w = 120, 200
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot(yy - 110, xx - 100)
    cung = (r > 70) & (r < 76) & (yy < 105)                     # vành cung dày 6 px, dài ~150 px
    v = np.zeros((h, w), np.float32)
    v[cung] = 0.9
    assert tach.buoc_mep(cung, v) > tach.BUOC_MEP_TOI_THIEU, "mép rõ — chỉ luật độ dày mới chặn được"
    assert not tach.hop_le(cung, 0.9, v)
    nguoi = _vat(y0=20, y1=110, x0=90, x1=115)                  # người đứng: dày 12,5 / dài 90 = 0,14
    v2 = np.zeros((h, w), np.float32); v2[nguoi] = 0.9
    assert tach.hop_le(nguoi, 0.9, v2)


def test_lam_sach_lap_lo_va_giu_mang_lon_nhat():
    m = _vat()
    m[60:70, 90:100] = False                            # lỗ giữa
    m[5:8, 5:8] = True                                  # đốm lẻ
    s = tach.lam_sach(m)
    assert s[65, 95] and not s[6, 6]


def test_diem_goi_y_nam_trong_mang_gan():
    v = _nen_doc() * 0.3
    vat = _vat()
    v[vat] = 0.9
    nhom = tach.diem_goi_y(v)
    assert nhom, "phải thấy ít nhất một mảng gần"
    # vật PHẲNG to (ảnh cắt dán) không "nhô" so với ô quét -> do nhóm mảng GẦN phía sau bắt (07/10)
    assert any(all(vat[y, x] for x, y in g) for g in nhom), nhom


def test_diem_goi_y_nguoi_dung_tren_mat_dat_gan():
    """Đo thật 07/10 ảnh KeyVisual: cô gái đứng trên mặt cỏ + cây bút cũng GẦN máy -> ngưỡng Otsu
    gộp người + đất thành MỘT mảng, điểm gợi ý rơi vào cây bút -> 0 vật. Gợi ý phải theo độ NHÔ
    so với xung quanh: mặt đất dốc đều không nhô, người dựng lên thì nhô."""
    h, w = 120, 200
    v = np.zeros((h, w), np.float32)
    v[50:] = np.linspace(0.45, 0.95, h - 50, dtype=np.float32)[:, None]   # mặt đất gần dần về đáy
    nguoi = _vat(y0=15, y1=100, x0=92, x1=112)                             # người đứng, chân chạm đất
    v[nguoi] = 1.0
    nhom = tach.diem_goi_y(v)
    assert nhom, "phải thấy người"
    assert all(nguoi[y, x] for x, y in nhom[0]), f"điểm gợi ý rơi ra ngoài người: {nhom[0]}"


class _SamGia:
    """Trả 3 phương án cố định — phương án thứ 2 là vật thật."""

    def __init__(self, ds):
        self.ds = ds

    def tach(self, rgb, pts):
        return self.ds


def test_tach_lop_chon_phuong_an_mep_gay_ro_nhat_va_va_nen():
    h, w = 120, 200
    rgb = np.random.default_rng(0).random((h, w, 3)).astype(np.float32)
    vat = _vat()
    z = np.full((h, w), 30.0, np.float32)
    z[vat] = 5.0
    bien = np.zeros((h, w), bool); bien[60:] = True
    sam = _SamGia([(bien, 0.9), (vat, 0.85), (vat & (np.arange(h)[:, None] < 60), 0.4)])
    da_va = []

    def lama(rgb_, m):
        da_va.append(m.copy())
        return rgb_ * 0 + 0.5

    kq = tach.tach_lop(rgb, z, sam=sam, va_nen=lama, uoc_do_sau=lambda x: np.full((h, w), 30.0, np.float32))
    assert len(kq.vat) == 1
    m, z_vat = kq.vat[0]
    assert (m == vat).all() and z_vat == 5.0
    assert da_va and da_va[0][vat].all(), "LaMa vá đúng chỗ vật vừa nhấc ra (có nới mép)"
    assert np.allclose(kq.nen, 0.5) and not kq.co


def test_tach_lop_khong_co_vat_thi_gan_co_de_lui_ve_chieu_sau():
    h, w = 120, 200
    rgb = np.zeros((h, w, 3), np.float32)
    z = np.full((h, w), 30.0, np.float32)
    kq = tach.tach_lop(rgb, z, sam=_SamGia([]), va_nen=lambda a, m: a, uoc_do_sau=lambda x: z)
    assert kq.vat == [] and "khong_tach_duoc_vat" in kq.co
