# -*- coding: utf-8 -*-
"""Luật cắt ref theo CẢNH QUAY — số trong test là số đo thật trên
`ref 1.mp4` (52 phút/1GB) ngày 06/09, không phải số bịa."""
from autoedit.sotra.canh import Canh, cat_canh, gop_may_dong


def test_gop_moc_sat_nhau_thanh_mot():
    """Cụm 65-67s trong ref không phải dissolve mà là máy quay trên ô tô đang
    chạy — chẻ ra sẽ được 5 mẩu 0.5s vô dụng, nên phải GỘP."""
    moc = [10.0, 65.17, 65.5, 65.83, 66.17, 66.5, 80.0]
    g = gop_may_dong(moc)
    assert [round(t, 2) for t, _ in g] == [10.0, 65.17, 80.0]
    assert g[1][1] is True, "cụm trải 1.33s phải bị gắn cờ máy_động"
    assert g[0][1] is False and g[2][1] is False


def test_moc_le_khong_bi_gan_co_may_dong():
    assert [d for _, d in gop_may_dong([10.0, 30.0, 50.0])] == [False] * 3


def test_cum_dung_nguong_0_5s_van_gan_co():
    """Đo toàn file: 25 cụm gộp, cụm dài nhất ĐÚNG 0.5s. Ngưỡng cũ 1.5s (đặt
    theo 300s đầu) không bao giờ bật -> hạ về 0.5 và so >=."""
    assert gop_may_dong([10.0, 40.0, 40.5, 70.0])[1][1] is True


def test_bo_canh_ngan_va_che_canh_dai(monkeypatch):
    import autoedit.sotra.canh as m

    monkeypatch.setattr(m, "_thoi_luong", lambda v: 60.0)
    #        0-3s giữ | 3-4s BỎ (<2s) | 4-30s chẻ (26s) | 30-60s chẻ
    monkeypatch.setattr(m, "quet_moc", lambda v, n=0.3: [3.0, 4.0, 30.0])
    cs = cat_canh(__import__("pathlib").Path("x.mp4"))
    assert all(c.dai >= 2.0 for c in cs), "không được sót cảnh <2s"
    assert all(c.dai <= 12.0 + 1e-6 for c in cs), "không được sót cảnh >12s"
    assert not any(b.t0 < a.t1 - 1e-6 for a, b in zip(cs, cs[1:])), "chồng lấn"
    assert cs[0].t0 == 0.0 and abs(cs[-1].t1 - 60.0) < 1e-6, "phải phủ hết phim"


def test_che_deu_khong_sot_canh_qua_dai(monkeypatch):
    """Chẻ ĐÔI một lần không đủ: cảnh 25s -> 12.5s vẫn quá khung. Đo 06/09 sót
    12 cảnh (max 21.4s) vì lỗi này."""
    import autoedit.sotra.canh as m

    monkeypatch.setattr(m, "_thoi_luong", lambda v: 25.0)
    monkeypatch.setattr(m, "quet_moc", lambda v, n=0.3: [])
    cs = cat_canh(__import__("pathlib").Path("x.mp4"))
    assert len(cs) == 3 and all(c.dai <= 12.0 for c in cs)


def test_video_hong_tra_rong(monkeypatch):
    import autoedit.sotra.canh as m

    monkeypatch.setattr(m, "_thoi_luong", lambda v: 0.0)
    assert cat_canh(__import__("pathlib").Path("hong.mp4")) == []


def test_canh_dai_tinh_dung():
    assert Canh(2.0, 6.5).dai == 4.5
