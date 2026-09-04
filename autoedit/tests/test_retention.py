"""retention/ — đọc đường cong từ ảnh chụp + luật điều chỉnh hồ sơ nhịp.

Ảnh test TỔNG HỢP dựng đúng phong cách YouTube Studio với đủ bẫy đã lường:
gridline xám, đường cong xanh ngọc, chấm legend NGOÀI khung, dải bôi xanh
nhạt đầu hook, vạch đỏ 0:00, dải xám "thông thường" — parser phải chỉ ăn
đường xanh ngọc TRONG khung.
"""

from __future__ import annotations

import math
import shutil

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from autoedit.retention.doc_anh import AnhKhongDoDuoc, doc_duong_cong
from autoedit.retention.phan_tich import ap_vao_ho_so, phan_tich

_CO_TESSERACT = shutil.which("tesseract") is not None or __import__("os").path.isfile(
    "C:/Program Files/Tesseract-OCR/tesseract.exe")

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


def _ve_anh_co_nhan(tmp_path, ham_pct, muc_pct, ten="chart_nhan.png"):
    """Như _ve_anh nhưng có NHÃN SỐ THẬT cạnh mỗi gridline (font Arial) — mô
    phỏng khuôn trục YouTube 0/40/80/120% cho phép ham_pct VƯỢT 1.0.
    muc_pct: giá trị % của từng gridline theo đúng thứ tự (0.0, 1/3, 2/3, 1.0)."""
    a = np.full((H, W + 90, 3), 255, dtype=np.uint8)
    for p, muc in zip((0.0, 1 / 3, 2 / 3, 1.0), muc_pct):
        a[_pct_to_y(min(p, 1.0)), XL:XR + 1] = XAM_KE
    for x in range(XL, XR + 1):
        f = (x - XL) / (XR - XL)
        y = _pct_to_y(min(1.2, max(0.0, ham_pct(f))))
        a[max(0, y - 1):y + 2, x] = XANH
    im = Image.fromarray(a)
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype("arial.ttf", 15)
    for p, muc in zip((0.0, 1 / 3, 2 / 3, 1.0), muc_pct):
        y = _pct_to_y(min(p, 1.0))
        d.text((XR + 6, y - 8), f"{muc:.0f}%", fill=(80, 80, 80), font=font)
    f = tmp_path / ten
    im.save(f)
    return f


@pytest.mark.skipif(not _CO_TESSERACT, reason="tesseract chưa cài trên máy này")
def test_doc_duong_cong_ocr_do_dung_diem_vuot_100pct(tmp_path):
    """Bug 04/09 (ảnh thật Trịnh Ngọc Hải thứ 2): điểm đầu 119% — retention CÓ
    THỂ vượt 100% (YouTube cho phép khi người xem tua lại). Neo cứng 'đầu=100%'
    SAI với ca này -> phải đọc nhãn % thật bằng OCR để hiệu chuẩn đúng."""
    ham = lambda f: 1.19 * math.exp(-5 * f) + 0.15    # đỉnh 119%, giống ảnh thật
    f = _ve_anh_co_nhan(tmp_path, ham, muc_pct=(0.0, 40.0, 80.0, 120.0))
    dc = doc_duong_cong(f)
    assert dc[0][1] > 1.10, f"phải đo được VƯỢT 100% (đỉnh thật 119%): {dc[0][1]:.2%}"
    sai = [abs(p - ham(x)) for x, p in dc]
    assert max(sai) < 0.08


@pytest.mark.skipif(not _CO_TESSERACT, reason="tesseract chưa cài trên máy này")
def test_doc_duong_cong_ocr_khong_doc_duoc_thi_roi_ve_fallback(tmp_path):
    """Ảnh không có nhãn số (như _ve_anh cũ, ảnh gốc Hải bị crop hẹp) -> OCR trả
    rỗng, code tự rơi về neo 'đầu~100%' cũ — không vỡ, chỉ kém chính xác hơn."""
    ham = lambda f: 0.30 + 0.70 * math.exp(-6 * f)
    dc = doc_duong_cong(_ve_anh(tmp_path, ham))
    assert dc[0][1] > 0.9                              # fallback vẫn hoạt động


def test_doc_duong_cong_tooltip_thay_the_khi_khong_co_nhan(tmp_path):
    """Ảnh không có nhãn trục (OCR không đọc gì) NHƯNG editor cung cấp tooltip
    ("giây → %" đọc trực tiếp trên YouTube Studio, đúng như tình huống thật
    04/09) -> phải neo đúng như trường hợp có nhãn, KHÔNG rơi về fallback
    'đầu~100%' kém chính xác — mô phỏng đúng ca vượt 100% (ảnh Hải thứ 2: 119%)."""
    ham = lambda f: 1.04 * math.exp(-5 * f) + 0.15    # ham(0)=1.19 đúng "119%"
    dai_s = 100.0
    tooltip_giay = [(0.0, 119.0), (25.0, ham(0.25) * 100)]
    dc = doc_duong_cong(_ve_anh(tmp_path, ham),
                        tooltip=[(g / dai_s, p) for g, p in tooltip_giay])
    assert dc[0][1] > 1.10, f"phải đo được VƯỢT 100% nhờ tooltip: {dc[0][1]:.2%}"
    sai = [abs(p - ham(x)) for x, p in dc]
    assert max(sai) < 0.08


def test_doc_duong_cong_tooltip_1_diem_khong_du_thi_bo_qua(tmp_path):
    """Chỉ 1 tooltip (không đủ 2 điểm khác % để suy tỷ lệ) -> bỏ qua, rơi về
    fallback cũ — không crash, không tự bịa tỷ lệ từ 1 điểm."""
    ham = lambda f: 0.30 + 0.70 * math.exp(-6 * f)
    dc = doc_duong_cong(_ve_anh(tmp_path, ham), tooltip=[(0.0, 119.0)])
    assert dc[0][1] > 0.9                               # vẫn chạy được (fallback)


def test_doc_duong_cong_khop_ham_goc(tmp_path):
    ham = lambda f: 0.30 + 0.70 * math.exp(-6 * f)        # decay kiểu YouTube
    dc = doc_duong_cong(_ve_anh(tmp_path, ham))
    assert len(dc) == 200 and dc[0][0] == 0.0 and dc[-1][0] == 1.0
    sai = [abs(p - ham(x)) for x, p in dc]
    assert max(sai) < 0.08                                # lệch < 8 điểm % (sai số resample/antialiasing tự nhiên)
    assert dc[0][1] > 0.9                                 # mở màn ~100%


def test_doc_duong_cong_tut_nhanh_thi_van_do_duoc(tmp_path):
    """Bug 04/09 (bao boi Trinh Ngoc Hai): video hook yeu tut that xuong ~70%
    ngay trong vai giay dau — day la DU LIEU THAT, khong phai anh bi cat.
    Dinh 100% van phai xuat hien dau do trong 10% dau (khong phai dung cot 0)."""
    ham = lambda f: 0.15 + 0.85 * math.exp(-25 * f)      # tut nhanh nhung khong
                                                          # che het gridline giua
    dc = doc_duong_cong(_ve_anh(tmp_path, ham))
    diem_5pct = next(p for x, p in dc if x >= 0.05)
    assert diem_5pct < 0.70                               # da tut sau — khong bi tu choi
    assert max(p for x, p in dc if x <= 0.10) > 0.90       # nhung dinh 100% van co trong 10% dau


def test_doc_duong_cong_anh_trang_bao_ro(tmp_path):
    f = tmp_path / "trang.png"
    Image.fromarray(np.full((100, 200, 3), 255, dtype=np.uint8)).save(f)
    with pytest.raises(AnhKhongDoDuoc, match="đường kẻ ngang"):
        doc_duong_cong(f)


def test_doc_duong_cong_nen_ngoai_chart_ngoi_xam_khong_lam_lech(tmp_path):
    """Bug 04/09 (bao boi Trinh Ngoc Hai): anh JPG that nen ngoai chart hoi nga
    xam (khong trang thuan 255) — code cu nhan nham CA VUNG NEN la 'gridline
    0%', keo x_r het chieu rong ANH thay vi chieu rong CHART, ty le phu duong
    xanh bi tinh hut con ~32% -> tu choi oan anh do duoc that su."""
    ham = lambda f: 1.0 - 0.7 * f
    a = np.full((H + 80, W + 200, 3), 238, dtype=np.uint8)   # nen NGOAI hoi xam
    ve = _ve_anh(tmp_path, ham, ten="tam.png")
    chart = np.asarray(Image.open(ve).convert("RGB"))
    a[40:40 + H, 100:100 + W] = chart                        # dan chart vao giua nen xam
    f = tmp_path / "that.png"
    Image.fromarray(a).save(f)
    dc = doc_duong_cong(f)
    sai = [abs(p - ham(x)) for x, p in dc]
    assert max(sai) < 0.08, f"nen xam lam lech phep do: sai toi da {max(sai):.2f}"


def test_doc_duong_cong_neo_100pct_bat_ke_diem_dau_that_su(tmp_path):
    """Danh doi user chot 04/09: neo diem dau LUON = 100% de tinh ty le % chinh
    xac (khong con doan so bac gridline) -> tool KHONG con phat hien duoc anh
    that su bi cat dau (moi diem dau deu tu dong quy ve 100%). Chap nhan duoc:
    do dung % tuyet doi quan trong hon cho nhip; editor van thay duong cong
    hop ly tren UI truoc khi Start sequence."""
    ham = lambda f: 0.60 - 0.30 * f                        # "cat dau" — khong co dinh that
    dc = doc_duong_cong(_ve_anh(tmp_path, ham))
    assert dc[0][1] == 1.0                                 # bi neo cung ve 100%, khong con nem loi


def test_doc_duong_cong_thieu_duong_xanh(tmp_path):
    a = np.full((H, W, 3), 255, dtype=np.uint8)
    for p in (0.0, 1 / 3, 2 / 3, 1.0):      # can >=3 gridline de qua duoc buoc do khung
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
# Dung HoSoNhip THAT (frozen dataclass) — bug 05/09: class gia mutable che mat
# FrozenInstanceError, retention + ep nhip cung am tham tat tren production.
def _hs_that():
    from autoedit.nhip.profile import nap
    return nap("investigate")          # hook_kieu="leo", bung_chu_ky_s=270.0


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
    hs = _hs_that()
    hs_moi, ra = ap_vao_ho_so(p, hs)
    assert hs_moi.hook_kieu == "no"
    assert hs_moi.bung_chu_ky_s == pytest.approx(202.5)
    assert hs.hook_kieu == "leo"                # ban goc frozen giu nguyen
    assert ra and "hook yếu" in " ".join(ra)


def test_ap_vao_ho_so_khong_file_im_lang(tmp_path):
    hs = _hs_that()
    hs_moi, log = ap_vao_ho_so(_project_tai(tmp_path), hs)
    assert log == [] and hs_moi is hs                      # không đổi gì
