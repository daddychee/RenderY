"""Nhịp — hồ sơ theo niche + bộ đo (Đợt 1, V2).

Số trong hồ sơ đến từ ĐO THẬT 03/09 (5 video Fern/WUFO, 2 thước hội tụ) — test
khoá các bất biến của số đo, không khoá giá trị lẻ để user còn chỉnh JSON tay.
"""

from __future__ import annotations

import json

import pytest

from autoedit.nhip.do import (
    dinh_bung,
    duong_cong,
    thong_ke_doan,
)
from autoedit.nhip.profile import HoSoNhip, ghi_mau, nap


# ------------------------------- hồ sơ ---------------------------------------
def test_nap_ho_so_dong_goi():
    hs = nap("investigate")
    assert hs.hook_kieu == "leo"          # điều tra GÂY CĂNG DẦN, không nổ (đo Hansa)
    assert hs.than_trung_vi < nap("life-in").than_trung_vi  # điều tra dày hơn doc


def test_niche_la_roi_ve_mac_dinh():
    hs = nap("niche-chua-ton-tai")
    assert hs.ten == "niche-chua-ton-tai"
    assert hs.than_trung_vi == nap("_mac_dinh").than_trung_vi


def test_chu_ky_bung_tu_so_do():
    """5/5 video đo được chu kỳ 3,1-5,0 phút — hồ sơ nào cũng phải nằm quanh đó."""
    for niche in ("life-in", "investigate", "_mac_dinh"):
        assert 180 <= nap(niche).bung_chu_ky_s <= 330


def test_gian_cach_tai_dung_theo_user():
    """User chốt 03/09: một cảnh AI dùng lại phải cách ≥60s."""
    assert nap("life-in").gian_cach_tai_dung_s >= 60


def test_file_json_de_len_dong_goi(tmp_path):
    (tmp_path / "life-in.json").write_text(json.dumps(dict(
        than_trung_vi=4.2, than_ty_le_nhanh=0.2, than_ty_le_hold=0.3,
        hook_kieu="em", hook_trung_vi=2.0, hook_ty_le_nhanh=0.3,
    )), encoding="utf-8")
    hs = nap("life-in", thu_muc=tmp_path)
    assert hs.than_trung_vi == 4.2 and hs.hook_kieu == "em"


def test_json_hong_bao_ro_khong_am_tham_ve_mac_dinh(tmp_path):
    """Người vừa chỉnh tay số mà thấy video y như cũ sẽ không hiểu vì sao —
    file hỏng phải NỔ với tên file, không lặng lẽ rơi về mặc định."""
    (tmp_path / "life-in.json").write_text("{ hong", encoding="utf-8")
    with pytest.raises(ValueError, match="life-in.json"):
        nap("life-in", thu_muc=tmp_path)


def test_so_vo_nghia_bi_chan(tmp_path):
    (tmp_path / "x.json").write_text(json.dumps(dict(
        than_trung_vi=99.0, than_ty_le_nhanh=0.5, than_ty_le_hold=0.2,
        hook_kieu="no", hook_trung_vi=1.0, hook_ty_le_nhanh=0.7,
    )), encoding="utf-8")
    with pytest.raises(ValueError, match="than_trung_vi"):
        nap("x", thu_muc=tmp_path)


def test_hook_kieu_la_bi_chan():
    hs = HoSoNhip(ten="t", than_trung_vi=3, than_ty_le_nhanh=.3, than_ty_le_hold=.2,
                  hook_kieu="bay", hook_trung_vi=1, hook_ty_le_nhanh=.5)
    assert any("hook_kieu" in x for x in hs.kiem())


def test_ghi_mau_khong_de_file_co_san(tmp_path):
    (tmp_path / "life-in.json").write_text('{"cua": "toi"}', encoding="utf-8")
    ghi_mau(tmp_path)
    assert json.loads((tmp_path / "life-in.json").read_text(encoding="utf-8")) == {"cua": "toi"}
    assert (tmp_path / "investigate.json").is_file()


# ------------------------------- bộ đo ---------------------------------------
def test_thong_ke_doan_co_ban():
    # 4 shot: 2s, 2s, 3s, 3s trong cửa sổ 10s
    tk = thong_ke_doan([2.0, 4.0, 7.0], 0.0, 10.0)
    assert tk.so_shot == 4
    assert tk.trung_vi == pytest.approx(2.5)
    assert tk.ty_le_nhanh == pytest.approx(0.5)
    assert tk.ty_le_hold == 0.0


def test_thong_ke_it_du_lieu_tra_none():
    assert thong_ke_doan([5.0], 0.0, 10.0) is None
    assert thong_ke_doan([], 0.0, 10.0) is None


def test_thong_ke_chi_lay_cat_trong_cua_so():
    """Điểm cắt ngoài [t0, t1) không được lọt vào — tách hook/thân dựa vào đây."""
    tk = thong_ke_doan([1.0, 5.0, 50.0, 99.0], 0.0, 10.0)
    assert tk.so_shot == 3          # mốc 0,1,5,10 -> 3 shot; 50/99 bị loại


def test_duong_cong_dem_dung():
    # 60 cắt rải đều trong 120s -> mọi cửa sổ 60s đều ~30 cắt/phút
    cat = [i * 2.0 for i in range(1, 60)]
    cong = duong_cong(cat, 120.0)
    assert all(28 <= v <= 31 for _, v in cong)


def test_dinh_bung_bat_duoc_dot_tang():
    """Nền 6 cắt/phút, một đợt 20 — đúng khuôn re-hook đo được ở Fern/WUFO."""
    cong = [(t * 15.0, 6.0) for t in range(40)]
    for i in range(18, 21):
        cong[i] = (cong[i][0], 20.0)
    bung = dinh_bung(cong)
    assert len(bung) == 1
    assert 260 <= bung[0][0] <= 300


def test_dinh_bung_khong_bao_dong_gia_tren_nen_phang():
    cong = [(t * 15.0, 8.0) for t in range(40)]
    assert dinh_bung(cong) == []


def test_dinh_bung_gop_dinh_sat_nhau():
    """Hai đỉnh cách <90s là cùng MỘT đợt — không đếm đôi."""
    cong = [(t * 15.0, 5.0) for t in range(40)]
    cong[10] = (150.0, 20.0)
    cong[13] = (195.0, 18.0)        # cách 45s — cùng đợt
    assert len(dinh_bung(cong)) == 1
