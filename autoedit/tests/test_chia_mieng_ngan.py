r"""CLIP NGẮN HƠN MIẾNG -> ĐẮP MIẾNG THỨ HAI, không đông cứng (user chốt 13/09).

Đo thật trên 53 draft đã xuất (1.916 segment):

    ô FREEZE (clip ngắn hơn khối)   256 = 13,4% mọi segment
    freeze >= 2s                    127
    freeze >= 4s                     50
    trung vị 1,99s · p90 4,96s · DÀI NHẤT 8,88s

Gần 9 giây một tấm hình bất động. Tốc độ KHÔNG phải nguyên nhân: sàn `SPEED_MIN`
0.8 chặn rồi, cả 1.916 segment chỉ có 6 cái dưới 0,8x (thấp nhất 0,766).

User đã nói cách chữa từ 07/09: *"Tôi vẫn chấp nhận cho source đó vào. Tôi sẽ tùy
chỉnh bằng cách TẠO MỘT KHỐI NHỎ TRONG KHỐI LỚN vừa với source bằng cách add
shot."* Tool đang làm nửa vời — nhận clip ngắn nhưng phần thiếu thì đông cứng.

LUẬT "KHÔNG PHÁ KHỐI" LẤY TỪ FRAMING INSIGHT (user chốt 13/09), không tự đặt số:
`kenh/mo_ta.py` định nghĩa `ty_le_nhanh` = tỉ lệ shot **≤2s** của kênh. Vậy 2s
là ranh giới kênh tự coi là "cắt nhanh" -> KHÔNG được chẻ ra miếng ngắn hơn thế.
Kênh `godoc-travel-doc` đo thật: thân 4,73s, chỉ **6%** shot ≤2s, 38% shot ≥5s —
chẻ thành hai miếng 2s ở kênh này là phá nhịp, nên cả HAI phần đều phải ≥ 2s.
"""

from __future__ import annotations

import pytest


def test_clip_2s_trong_mieng_6s_thi_CHE():
    from autoedit.offline.thay_mau import chia_mieng

    kq = chia_mieng(dai_mieng=6.0, dai_clip=2.0)
    assert kq is not None
    phu, du = kq
    assert phu == pytest.approx(2.0 / 0.9, abs=0.01), "0.9x nên 2s clip phủ ~2,22s"
    assert du == pytest.approx(6.0 - phu, abs=0.01)
    assert phu + du == pytest.approx(6.0, abs=0.01), "hai phần phải khít miếng"


def test_phan_du_NGAN_hon_nguong_thi_KHONG_che():
    """Clip 5s trong miếng 6s: dư 0,44s. Chẻ ra một shot 0,44s là phá nhịp —
    freeze 0,44s thì gần như không ai thấy."""
    from autoedit.offline.thay_mau import chia_mieng

    assert chia_mieng(dai_mieng=6.0, dai_clip=5.0) is None


def test_phan_DAU_ngan_hon_nguong_thi_KHONG_che():
    """Clip 1,5s: phủ 1,67s < 2s. Chẻ thì phần đầu là shot nháy — kênh
    godoc-travel-doc chỉ 6% shot ≤2s."""
    from autoedit.offline.thay_mau import chia_mieng

    assert chia_mieng(dai_mieng=6.0, dai_clip=1.5) is None


def test_clip_du_dai_thi_KHONG_can_che():
    from autoedit.offline.thay_mau import chia_mieng

    assert chia_mieng(dai_mieng=4.0, dai_clip=9.0) is None


def test_nguong_LAY_TU_HO_SO_KENH_khong_dong_cung():
    """Kênh cắt nhanh thì ngưỡng phải hạ theo — số đến từ Framing Insight."""
    from autoedit.offline.thay_mau import chia_mieng

    # ngưỡng 2s: miếng 3,4s + clip 1,3s -> phủ 1,44s < 2s -> không chẻ
    assert chia_mieng(dai_mieng=3.4, dai_clip=1.3) is None
    # kênh nhịp nhanh (ngưỡng 1,2s) -> chẻ được
    kq = chia_mieng(dai_mieng=3.4, dai_clip=1.3, nguong=1.2)
    assert kq is not None and kq[0] == pytest.approx(1.44, abs=0.02)


def test_nguong_tu_ho_so_framing():
    """`nguong_chia` đọc hồ sơ kênh: ranh giới "cắt nhanh" là ≤2s (mo_ta.py),
    nhưng không được vượt nửa thân — kênh thân 3s thì chẻ 2+1 là phá."""
    from autoedit.offline.thay_mau import nguong_chia

    assert nguong_chia({}) == pytest.approx(2.0)
    assert nguong_chia({"than": 4.73}) == pytest.approx(2.0)
    assert nguong_chia({"than": 3.0}) == pytest.approx(1.5), "nửa thân"


def test_khong_bao_gio_tra_phan_am():
    from autoedit.offline.thay_mau import chia_mieng

    for dm, dc in ((2.0, 0.1), (0.5, 0.4), (6.0, 0.0), (1.0, 5.0)):
        kq = chia_mieng(dai_mieng=dm, dai_clip=dc)
        assert kq is None or (kq[0] > 0 and kq[1] > 0)
