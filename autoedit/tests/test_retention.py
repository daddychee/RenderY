"""retention/ — đọc đường cong từ ảnh chụp + luật điều chỉnh hồ sơ nhịp.

Ảnh test TỔNG HỢP dựng đúng phong cách YouTube Studio với đủ bẫy đã lường:
gridline xám, đường cong xanh ngọc, chấm legend NGOÀI khung, dải bôi xanh
nhạt đầu hook, vạch đỏ 0:00, dải xám "thông thường" — parser phải chỉ ăn
đường xanh ngọc TRONG khung.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from PIL import Image

from autoedit.retention.doc_anh import AnhKhongDoDuoc, doc_duong_cong
from autoedit.retention.phan_tich import ap_vao_ho_so, phan_tich

XANH = (49, 168, 201)         # đường "Video này"
XAM_KE = (235, 235, 235)      # gridline
W, H = 800, 320
Y100, Y0 = 30, 290            # gridline 100% và 0%
XL, XR = 40, 760


def _pct_to_y(p: float) -> int:
    return int(Y0 - p * (Y0 - Y100))


def _ve_anh(tmp_path, ham_pct, ten="chart.png"):
    """Vẽ biểu đồ giả: ham_pct(x_frac) -> retention 0..1."""
    a = np.full((H, W, 3), 255, dtype=np.uint8)
    for p in (0.0, 1 / 3, 2 / 3, 1.0):                    # 4 gridline như YouTube
        a[_pct_to_y(p), XL:XR + 1] = XAM_KE
    # dải xám "thông thường" (band nhạt quanh đường cong)
    for x in range(XL, XR + 1):
        f = (x - XL) / (XR - XL)
        y = _pct_to_y(min(1.0, ham_pct(f) + 0.06))
        a[y:y + 14, x] = (222, 222, 222)
    # bẫy: chấm legend xanh NGOÀI khung (trên gridline 100%)
    a[8:16, 12:20] = XANH
    # bẫy: dải bôi xanh NHẠT đầu hook + vạch đỏ 0:00
    a[Y100:Y0, XL:XL + 18] = (225, 238, 248)
    a[Y100:Y0, XL] = (200, 60, 80)
    # đường cong thật (dày 3px)
    for x in range(XL, XR + 1):
        f = (x - XL) / (XR - XL)
        y = _pct_to_y(ham_pct(f))
        a[max(0, y - 1):y + 2, x] = XANH
    f = tmp_path / ten
    Image.fromarray(a).save(f)
    return f


def test_doc_duong_cong_khop_ham_goc(tmp_path):
    ham = lambda f: 0.30 + 0.70 * math.exp(-6 * f)        # decay kiểu YouTube
    dc = doc_duong_cong(_ve_anh(tmp_path, ham))
    assert len(dc) == 200 and dc[0][0] == 0.0 and dc[-1][0] == 1.0
    sai = [abs(p - ham(x)) for x, p in dc]
    assert max(sai) < 0.05                                # lệch < 5 điểm %
    assert dc[0][1] > 0.9                                 # mở màn ~100%


def test_doc_duong_cong_tut_nhanh_thi_van_do_duoc(tmp_path):
    """Bug 04/09 (bao boi Trinh Ngoc Hai): video hook yeu tut that xuong ~70%
    ngay trong vai giay dau — day la DU LIEU THAT, khong phai anh bi cat.
    Dinh 100% van phai xuat hien dau do trong 10% dau (khong phai dung cot 0)."""
    ham = lambda f: max(0.30, 1.0 - 8.0 * f)              # cham 100% dung 1 khoanh
                                                          # roi 30% ngay trong ~9% dau
    dc = doc_duong_cong(_ve_anh(tmp_path, ham))
    diem_5pct = next(p for x, p in dc if x >= 0.05)
    assert diem_5pct < 0.70                               # da tut sau — khong bi tu choi
    assert max(p for x, p in dc if x <= 0.10) > 0.90       # nhung dinh 100% van co trong 10% dau


def test_doc_duong_cong_anh_trang_bao_ro(tmp_path):
    f = tmp_path / "trang.png"
    Image.fromarray(np.full((100, 200, 3), 255, dtype=np.uint8)).save(f)
    with pytest.raises(AnhKhongDoDuoc, match="đường kẻ ngang"):
        doc_duong_cong(f)


def test_doc_duong_cong_anh_cat_that_bi_bao(tmp_path):
    """Anh CAT MAT dau (khong phai video tut nhanh): dinh cao nhat trong 10%
    dau van thap ro rang duoi 90% — day moi la truong hop can chan."""
    ham = lambda f: 0.60 - 0.30 * f                        # KHONG co dinh 100% dau
    with pytest.raises(AnhKhongDoDuoc, match="bị cắt"):
        doc_duong_cong(_ve_anh(tmp_path, ham))


def test_doc_duong_cong_thieu_duong_xanh(tmp_path):
    a = np.full((H, W, 3), 255, dtype=np.uint8)
    for p in (0.0, 1.0):
        a[_pct_to_y(p), XL:XR + 1] = XAM_KE
    f = tmp_path / "khong_xanh.png"
    Image.fromarray(a).save(f)
    with pytest.raises(AnhKhongDoDuoc, match="màu xanh"):
        doc_duong_cong(f)


# ------------------------------------------------------------------ phan_tich
def _cong(ham, n=200):
    return [(i / (n - 1), ham(i / (n - 1))) for i in range(n)]


def test_phan_tich_hook_yeu():
    # tụt sập 30s đầu như ảnh user gửi 04/09: rơi thẳng về ~36% rồi trôi chậm
    dc = _cong(lambda f: 0.15 + 0.85 * math.exp(-80 * f))
    kq = phan_tich(dc, dai_s=1705)                        # 28:25
    assert kq["giu_30s"] < 0.55
    assert kq["dieu_chinh"]["hook_kieu"] == "no"
    assert any("NỔ" in ln for ln in kq["bao_cao"])


def test_phan_tich_decay_cao_rut_chu_ky():
    # hook ổn nhưng thân chảy máu đều: mất ~2.6 điểm %/phút
    dc = _cong(lambda f: 1.0 - 0.75 * f)
    kq = phan_tich(dc, dai_s=1705)
    assert kq["decay_pm"] > 2.5
    assert kq["dieu_chinh"]["bung_he_so_chu_ky"] == 0.75
    assert "hook_kieu" not in kq["dieu_chinh"]            # hook tốt thì không đổi


def test_phan_tich_giu_tot_khong_dieu_chinh():
    dc = _cong(lambda f: 1.0 - 0.25 * f)                  # 30s ~99%, mất ~0.9đ/phút
    kq = phan_tich(dc, dai_s=1705)
    assert kq["dieu_chinh"] == {}


def test_phan_tich_diem_tut_cuc_bo():
    def ham(f):                                            # sụt 12 điểm quanh 50%
        nen = 0.9 - 0.2 * f
        return nen - 0.12 / (1 + math.exp(-80 * (f - 0.5)))
    kq = phan_tich(_cong(ham), dai_s=1200)
    assert kq["diem_tut"], "phải bắt được cú sụt giữa bài"
    t, m = kq["diem_tut"][0]
    assert abs(t - 600) < 90 and m > 5                     # đúng quãng, đúng cỡ


# ------------------------------------------------------------------ ap_vao_ho_so
class _HS:
    hook_kieu = "leo"
    bung_chu_ky_s = 270.0


def _project_tai(tmp_path):
    from types import SimpleNamespace
    chuong = tmp_path / "TAP01" / "C1"
    chuong.mkdir(parents=True)
    return SimpleNamespace(inputs=SimpleNamespace(
        original_script_path=str(chuong / "script.txt")))


def test_ap_vao_ho_so_chinh_hook_va_chu_ky(tmp_path):
    import json
    p = _project_tai(tmp_path)
    (tmp_path / "TAP01" / "retention.json").write_text(json.dumps({
        "dai_s": 1705, "bao_cao": ["tổng quan", "hook yếu"],
        "dieu_chinh": {"hook_kieu": "no", "bung_he_so_chu_ky": 0.75}}),
        encoding="utf-8")
    hs = _HS()
    ra = ap_vao_ho_so(p, hs)
    assert hs.hook_kieu == "no"
    assert hs.bung_chu_ky_s == pytest.approx(202.5)
    assert ra and "hook yếu" in " ".join(ra)


def test_ap_vao_ho_so_khong_file_im_lang(tmp_path):
    hs = _HS()
    assert ap_vao_ho_so(_project_tai(tmp_path), hs) == []
    assert hs.hook_kieu == "leo"                           # không đổi gì
