"""Collage — MÁY TỰ BIÊN ĐẠO nhịp + camera (user chốt 07/10/2026: bỏ ô camera, "máy tự lên nhịp và camera").

Luật lấy từ lỗi ĐO THẬT ở bản thử "Những thành phố mơ màng" (3 video user duyệt 07/10):
- lớp chưa tới lượt phải NẤP HẲN (nóc thành phố từng ló lên trước khi tảng đá trồi);
- vật bị mép ảnh cắt cụt (tảng đá) KHÔNG được lộ đường cắt (tính tay lệch 45 px -> máy tự giải);
- lúc camera GIỮ, vật đứng riêng (chữ tiêu đề) hoặc nằm trọn trong khung hoặc ra hẳn — không cắt ngang;
- không có khoảng chết dài (video lỗi 18:26: 7/10 giây gần đứng yên).
Hình học tổng hợp theo đúng hộp bao các lớp của ảnh thật đó (1920x1080, phóng 1,15).
"""

from __future__ import annotations

import numpy as np
import pytest

from autoedit.collage import bien_dao as bd

W, H, S0 = 1920, 1080, 1.15


def _vat(x0, y0, x1, y1, z, cham=(), lo_lung=False):
    return bd.Vat(X=((x0 + x1) / 2 - 960) * S0, Y=((y0 + y1) / 2 - 540) * S0, nw=(x1 - x0) / 2 * S0,
                  nh=(y1 - y0) / 2 * S0, Z0=z, cham={k: k in cham for k in ("trai", "phai", "tren", "duoi")},
                  lo_lung=lo_lung)


def _thanh_pho():
    return [_vat(400, 805, 1520, 1080, 7.0, ("duoi",)),            # 0 tảng đá — bị đáy ảnh cắt cụt
            _vat(515, 440, 1420, 862, 6.8),                         # 1 thành phố đứng trên đá
            _vat(918, 444, 1122, 752, 6.7),                         # 2 cây thông giữa thành phố
            _vat(512, 108, 1408, 494, 4.5),                         # 3 chữ tiêu đề
            _vat(1690, 680, 1790, 780, 16.0, lo_lung=True)]         # 4 hành tinh


def _hop(v, kh, i, t):
    return bd.hop_man(v, kh.cam(t), kh.anims[i](t), W, H)


def test_vai_tro_theo_vi_tri():
    vai = bd.vai_tro(_thanh_pho(), W, H)
    assert vai[0] == ("de", None)
    assert vai[1] == ("tren", 0), "thành phố đứng trên tảng đá -> trồi từ sau đá"
    assert vai[2] == ("tren", 1), "cây đứng trong thành phố"
    assert vai[3][0] == "roi", "chữ ở trên cao -> rơi xuống"
    assert vai[4][0] == "troi"


@pytest.mark.parametrize("style", bd.STYLE)
def test_thu_tu_vao_de_truoc_chu_sau_va_xong_som(style):
    kh = bd.lap(_thanh_pho(), 8.0, style, W, H)
    t0 = kh.gio_vao
    assert t0[0] < t0[1] < t0[2] < t0[3], t0
    assert max(t0[:4]) <= 0.45 * 8.0


@pytest.mark.parametrize("style", bd.STYLE)
def test_chua_toi_luot_thi_nap_han_ngoai_khung(style):
    vs = _thanh_pho()
    kh = bd.lap(vs, 8.0, style, W, H)
    for i in range(4):
        for t in (0.0, kh.gio_vao[i] - 0.01):
            if t < 0:
                continue
            x0, y0, x1, y1 = _hop(vs[i], kh, i, t)
            ngoai = x1 <= 0 or x0 >= W or y1 <= 0 or y0 >= H or (x1 - x0) < 3
            assert ngoai, f"lớp {i} ló ra lúc t={t:.2f} trước giờ vào {kh.gio_vao[i]:.2f}: {(x0, y0, x1, y1)}"


@pytest.mark.parametrize("style", bd.STYLE)
def test_cuoi_clip_moi_lop_ve_dung_cho(style):
    kh = bd.lap(_thanh_pho(), 8.0, style, W, H)
    for i in range(4):
        ox, oy, r, s, dz = kh.anims[i](8.0)
        assert abs(ox) < 1 and abs(oy) < 1 and abs(r) < 0.1 and abs(s - 1) < 0.01 and abs(dz) < 0.01


@pytest.mark.parametrize("style", bd.STYLE)
def test_camera_giu_khong_lo_duong_cat_khong_cat_ngang_chu(style):
    vs = _thanh_pho()
    kh = bd.lap(vs, 8.0, style, W, H)
    assert kh.giu, "phải có ít nhất một đoạn camera giữ ở vật chính"
    for a, b in kh.giu:
        for t in np.arange(a, b, 1 / 30):
            x0, y0, x1, y1 = _hop(vs[0], kh, 0, t)
            assert y1 >= H + 4, f"t={t:.2f}: đáy tảng đá (bị ảnh cắt cụt) lộ {H - y1:.0f}px"
            x0, y0, x1, y1 = _hop(vs[3], kh, 3, t)
            trong = x0 >= 0 and y0 >= 0 and x1 <= W and y1 <= H
            ngoai = y1 <= 0 or y0 >= H or x1 <= 0 or x0 >= W
            assert trong or ngoai, f"t={t:.2f}: chữ tiêu đề bị cắt ngang {(x0, y0, x1, y1)}"


@pytest.mark.parametrize("style", bd.STYLE)
def test_nen_khong_lo_mep(style):
    kh = bd.lap(_thanh_pho(), 8.0, style, W, H)
    for t in np.arange(0, 8.0, 1 / 30):
        assert bd.nen_phu_khung(kh.cam(t), W, H), f"t={t:.2f}: nền lộ mép"


@pytest.mark.parametrize("style", bd.STYLE)
def test_khong_co_khoang_chet_dai(style):
    kh = bd.lap(_thanh_pho(), 8.0, style, W, H)
    nhip = sorted(kh.nhip)
    assert len(nhip) >= 5
    khoang = np.diff([0.0] + nhip + [8.0])
    assert khoang.max() <= 2.5, f"khoảng không có nhịp mới dài {khoang.max():.1f} s: {nhip}"


@pytest.mark.parametrize("style", bd.STYLE)
def test_clip_ngan_van_dung(style):
    vs = _thanh_pho()
    kh = bd.lap(vs, 2.5, style, W, H)
    assert all(t <= 2.5 for t in kh.nhip)
    for i in range(4):
        ox, oy, r, s, dz = kh.anims[i](2.5)
        assert abs(oy) < 2 and abs(s - 1) < 0.02, "clip ngắn: lớp vẫn kịp vào chỗ"


def test_vat_chinh_to_thi_day_may_vao_nhung_khong_cat_dau():
    """Cô gái KeyVisual cao 80% khung: đòi 'nằm trọn' thì camera không vào được chút nào. Luật: đẩy vào
    (to lên >= 15%), được cắt phía DƯỚI, KHÔNG cắt đầu (mép trên vật chính luôn trong khung)."""
    v = [_vat(596, 75, 1375, 824, 5.5)]
    kh = bd.lap(v, 6.0, "collage", W, H)
    assert bd.vai_tro(v, W, H)[0][0] == "bat"
    assert kh.giu
    nghi = bd.hop_man(v[0], (0, 0, 0, 1, 0, 0), (0, 0, 0, 1, 0), W, H)
    a, b = kh.giu[0]
    x0, y0, x1, y1 = _hop(v[0], kh, 0, (a + b) / 2)
    assert (y1 - y0) >= 1.15 * (nghi[3] - nghi[1]), "camera phải vào gần vật chính"
    assert y0 >= 0, "không cắt đầu"
    assert 0.2 * W < (x0 + x1) / 2 < 0.8 * W


def test_vat_chinh_sat_day_khong_duoc_keo_lo_duong_cat():
    """Vật chính nằm ngay trên tảng đá bị đáy ảnh cắt cụt: ngắm thẳng giữa vật là kéo lộ đáy đá ->
    máy phải chịu ngắm lệch / zoom vừa phải để đường cắt vẫn dưới khung."""
    vs = [_vat(300, 980, 1620, 1080, 7.0, ("duoi",)),             # đá mỏng 100 px sát đáy
          _vat(760, 760, 1160, 990, 6.8)]                          # vật chính thấp, đứng trên đá
    # tính trước: ngắm thẳng giữa vật ở zoom 1,6 thì đáy đá lên tới y~928 (lộ 150 px) -> luật PHẢI ra tay
    kh = bd.lap(vs, 8.0, "collage", W, H)
    assert kh.giu
    for a, b in kh.giu:
        for t in np.arange(a, b, 1 / 15):
            assert _hop(vs[0], kh, 0, t)[3] >= H + 4, f"t={t:.2f}: lộ đường cắt đáy đá"


def test_lop_dung_tren_trui_sau_lop_do():
    vs = _thanh_pho()
    kh = bd.lap(vs, 8.0, "collage", W, H)
    t = kh.gio_vao[1] + 0.1                                        # thành phố đang trồi
    assert vs[1].Z0 + kh.anims[1](t)[4] > vs[0].Z0, "đang trồi thì phải ở SAU tảng đá"



def test_do_sau_theo_vai_tro_khong_theo_model():
    """Đo thật 07/10: model độ sâu xếp chữ tiêu đề SAU thành phố và tảng đá TRƯỚC nhất (ảnh đồ hoạ).
    Bản thử user duyệt: chữ trước nhất, cây trước thành phố, thành phố trước đá; vật lơ lửng xa."""
    vs = _thanh_pho()
    z = bd.do_sau_theo_vai(vs, bd.vai_tro(vs, W, H))
    assert z[3] < z[2] < z[1] < z[0], z
    assert z[4] > z[0], "vật lơ lửng ở xa hơn mọi lớp chính"


def test_giu_o_tieu_de_thi_thanh_pho_ben_duoi_van_hien_mot_phan():
    """Đo thật 07/10: luật 'trọn trong khung hoặc ra hẳn' áp cho mọi vật -> lúc giữ ở tiêu đề, máy đẩy
    thành phố ra HẲN khỏi khung, chữ đứng trơ giữa trời. Bản duyệt: thành phố hiện một phần bên dưới.
    Luật chỉ áp cho vật nằm TRÊN vật chính."""
    vs = _thanh_pho()
    c = bd.giai_camera(vs, 3, W, H)
    assert c is not None
    x0, y0, x1, y1 = bd.hop_man(vs[1], c, bd.NGHI, W, H)
    thay = max(0.0, min(y1, H) - max(y0, 0)) / (y1 - y0)
    assert thay > 0.2, f"thành phố chỉ còn {thay:.0%} trong khung"



def _thanh_pho_du():
    """Như ảnh thật: thêm cột tháp nhỏ trên thành phố + sao băng nhỏ chạm mép phải (đều là vật NHỎ)."""
    return _thanh_pho() + [_vat(698, 438, 776, 602, 6.5), _vat(1736, 348, 1920, 518, 7.0, ("phai",))]


@pytest.mark.parametrize("style", bd.STYLE)
def test_vat_nho_khong_chiem_luot_tieu_de_vao_kip(style):
    """Đo thật 07/10: cột tháp + sao băng mỗi thứ chiếm một lượt -> tiêu đề vào lúc 3,4 s (bản duyệt
    2,05 s), hiện ~0,7 s thì camera đã vọt đi đẩy nó ra khỏi khung."""
    kh = bd.lap(_thanh_pho_du(), 8.0, style, W, H)
    assert kh.gio_vao[3] <= 2.5, f"tiêu đề vào lúc {kh.gio_vao[3]:.2f} s"


@pytest.mark.parametrize("style", bd.STYLE)
def test_giu_toan_canh_it_nhat_1_2_giay_truoc_cu_camera_dau(style):
    vs = _thanh_pho_du()
    kh = bd.lap(vs, 8.0, style, W, H)
    cam_dau = min(t for t in kh.nhip if t > max(kh.gio_vao))
    assert cam_dau - max(kh.gio_vao) >= 1.2 - 1e-6
    khoang = np.diff([0.0] + sorted(kh.nhip) + [8.0])
    assert khoang.max() <= 2.5, f"có đoạn chết {khoang.max():.1f} s"
