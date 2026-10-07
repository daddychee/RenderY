"""Collage — CHUỖI 2–3 ảnh nối nhau thành MỘT video (user chốt 07/10/2026, tool VOX riêng).

Mỗi ảnh có giây riêng, mẫu riêng (Chiều sâu / Pop-up), camera riêng. Giữa hai ảnh là một
cú NỐI: lia vút (ảnh trước tăng tốc tới lúc cắt, ảnh sau vào vẫn đang lia rồi hãm — đúng
cách clip ca1→ca2 user đã duyệt) hoặc cắt thẳng. Lộ mép = 0 ngoài lúc lia (luật skill).
"""

from __future__ import annotations

import json
import shutil
import subprocess

import numpy as np
import pytest

pytest.importorskip("torch")

from autoedit.collage import mau, tach  # noqa: E402
from autoedit.collage.dung import Canh, dung_khung  # noqa: E402

CO_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
W, H = 160, 90


def do_sau_gia(rgb):
    h, w = rgb.shape[:2]
    return np.linspace(40.0, 4.0, h, dtype=np.float32)[:, None].repeat(w, 1)


def _rgb(seed=0, w=320, h=180):
    from PIL import Image
    r = np.random.default_rng(seed)
    a = (r.random((h // 8 + 1, w // 8 + 1, 3)) * 255).astype(np.uint8)
    return np.asarray(Image.fromarray(a).resize((w, h), Image.BICUBIC), np.float32) / 255


def _anh(tmp_path, ten, seed=0, w=320, h=180):
    from PIL import Image
    p = tmp_path / ten
    Image.fromarray((_rgb(seed, w, h) * 255).astype(np.uint8)).save(p)
    return p


def _hai_canh():
    return [Canh(r, do_sau_gia(r), W, H, zoom=mau.ZOOM) for r in (_rgb(0), _rgb(1))]


# ═══════ cú nối ═══════════════════════════════════════════════════════════════
def test_lia_len_anh_truoc_vut_di_anh_sau_vao_roi_ham():
    c = _hai_canh()
    cam = mau.ke_hoach_chuoi(c, [2.0, 2.0], ["static", "static"], ["lia_len"])
    (k0, x0), (k_cuoi, x_cuoi) = cam[0](0.0), cam[0](2.0 - 1e-6)
    assert abs(k0[5]) < 1 and not x0, "đầu ảnh 1 chưa lia"
    assert k_cuoi[5] > 0.6 * H and x_cuoi, "cuối ảnh 1 đã trượt quá nửa khung"
    (k_vao, x_vao), (k_het, x_het) = cam[1](0.0), cam[1](2.0)
    assert k_vao[5] < -0.6 * H and x_vao, "ảnh 2 vào khi còn đang lia"
    assert abs(k_het[5]) < 2 and abs(k_het[3] - 1) < 0.01 and not x_het, "ảnh 2 hãm về đứng yên"
    # cùng một chiều chạy qua điểm cắt: ảnh trôi XUỐNG suốt cú lia
    py0 = [cam[0](t)[0][5] for t in np.linspace(1.5, 2.0 - 1e-6, 8)]
    py1 = [cam[1](t)[0][5] for t in np.linspace(0.0, 0.4, 8)]
    assert all(b >= a for a, b in zip(py0, py0[1:])) and all(b >= a for a, b in zip(py1, py1[1:]))
    assert all(abs(cam[i](t)[0][4]) < 1e-9 for i in (0, 1) for t in (0.0, 1.0, 1.9)), "lia lên không lia ngang"


def test_anh_vao_giu_toc_do_lia_tai_diem_cat():
    """Đo thật 07/10 (chuỗi SE001 họp báo -> hành lang): hãm lò xo bắt đầu ở VẬN TỐC 0 nên ảnh vào
    lệch >1 khung mà không nhoè -> phản chiếu mép LỘN NGƯỢC hiện rõ (khung 90-96). Ảnh vào phải
    chạy tiếp ĐÚNG tốc độ lia lúc cắt rồi mới hãm; phóng lùi chậm hơn để mép phản chiếu nằm ngoài khung."""
    c = _hai_canh()
    cam = mau.ke_hoach_chuoi(c, [2.0, 2.0], ["static", "static"], ["lia_len"])
    dt = 1 / 120
    v_ra = (cam[0](2.0 - 1e-6)[0][5] - cam[0](2.0 - dt)[0][5]) / dt
    v_vao = (cam[1](dt)[0][5] - cam[1](0.0)[0][5]) / dt
    assert v_vao >= 0.6 * v_ra, f"vào {v_vao:.0f} px/s, ra {v_ra:.0f} px/s"


def test_giua_cu_lia_phan_thieu_la_anh_ke_ben_khong_phai_phan_chieu():
    """Đo thật 07/10 lần 2: giữ tốc độ vẫn còn chân người LỘN NGƯỢC ở khung 90 — phản chiếu mép
    không bao giờ sạch. Lúc lia, phần khung ảnh này không phủ phải là ẢNH KẾ BÊN nằm sát mép
    (trượt liền như cuộn phim). A đỏ, B xanh: lia lên -> B ở TRÊN A."""
    do, xanh = np.zeros((180, 320, 3), np.float32), np.zeros((180, 320, 3), np.float32)
    do[..., 0], xanh[..., 2] = 0.9, 0.9
    z = np.full((180, 320), 20.0, np.float32)
    c = [Canh(do, z, W, H, zoom=mau.ZOOM), Canh(xanh, z, W, H, zoom=mau.ZOOM)]
    cam = mau.ke_hoach_chuoi(c, [2.0, 2.0], ["static", "static"], ["lia_len"])
    for i, t in ((0, 2.0 - 0.12), (0, 2.0 - 1e-3), (1, 0.0), (1, 0.15)):
        img = mau.khung_chuoi(c, cam, i, t)
        tren, duoi = img[:6].mean((0, 1)), img[-6:].mean((0, 1))
        assert tren[2] > 0.8 and tren[0] < 0.1, f"ảnh {i} t={t}: mép trên phải là B xanh, ra {tren}"
        assert duoi[0] > 0.8 and duoi[2] < 0.1, f"ảnh {i} t={t}: mép dưới phải là A đỏ, ra {duoi}"


def test_lia_ngang_dung_truc_x():
    c = _hai_canh()
    cam = mau.ke_hoach_chuoi(c, [2.0, 2.0], ["static", "static"], ["lia_ngang"])
    assert cam[0](2.0 - 1e-6)[0][4] > 0.6 * W and cam[1](0.0)[0][4] < -0.6 * W


def test_cat_thang_khong_lia():
    c = _hai_canh()
    cam = mau.ke_hoach_chuoi(c, [2.0, 2.0], ["static", "static"], ["cat"])
    for i in (0, 1):
        for t in np.linspace(0, 2.0, 9):
            k, px = cam[i](t)
            assert abs(k[4]) < 1e-9 and abs(k[5]) < 1e-9 and not px


@pytest.mark.parametrize("noi", ["lia_len", "lia_ngang"])
def test_ngoai_luc_lia_khong_lo_mep(noi):
    c = _hai_canh()
    cam = mau.ke_hoach_chuoi(c, [1.2, 1.2], ["push_in", "truck_left"], [noi])
    for i in (0, 1):
        for t in np.linspace(0, 1.2, 13):
            k, phan_xa = cam[i](t)
            if not phan_xa:
                assert dung_khung(c[i], k, t)[1] == 0.0, f"ảnh {i} t={t:.2f}: lộ mép"


def test_anh_khac_ti_le_duoc_cat_giua_cho_vua_khung(tmp_path):
    p = _anh(tmp_path, "doc.png", w=180, h=225)                  # ảnh 4:5 đem dựng khung 16:9
    rgb = mau.doc_anh_khung(p, 1920, 1080)
    assert abs(rgb.shape[1] / rgb.shape[0] - 16 / 9) < 0.02 and rgb.shape[1] == 180


def test_diem_bam_doi_tu_ti_le_sang_pixel():
    assert mau.diem_pixel([{"x": 0.5, "y": 0.25, "dau": 1}], 320, 180) == [{"x": 160, "y": 45, "dau": 1}]


# ═══════ dựng thật: 2 ảnh -> 1 mp4 ════════════════════════════════════════════
def _giay(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(p)],
                       capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


@pytest.mark.skipif(not CO_FFMPEG, reason="máy không có ffmpeg")
def test_dung_chuoi_hai_anh_ra_mot_video_dung_tong_giay_va_luu_tach_theo_anh(tmp_path):
    from autoedit.collage.kho_tach import KhoTach
    kt = KhoTach(tmp_path / "collage")
    a1, a2 = _anh(tmp_path, "a1.png", 0), _anh(tmp_path, "a2.png", 1)

    def tach_gia(rgb, z, **k):
        m = np.zeros(rgb.shape[:2], bool)
        m[40:, 120:200] = True
        return tach.KetQuaTach([(m, 5.0)], rgb, z, ["mep_yeu"])

    ra = tmp_path / "ra.mp4"
    mau.dung_chuoi([{"anh": str(a1), "giay": 1.0, "mau": "chieu_sau", "cd": "push_in"},
                    {"anh": str(a2), "giay": 1.5, "mau": "popup", "cd": ""}],
                   ["lia_len"], ra, kt, W=W, H=H, fps=12, uoc_do_sau=do_sau_gia, tach_lop=tach_gia)
    assert abs(_giay(ra) - 2.5) < 0.15
    assert kt.thong_tin(mau.nhan_anh(a2))["co"] == ["mep_yeu"], "bản tách lưu THEO ẢNH, ▲ còn nguyên"
    assert kt.thong_tin(mau.nhan_anh(a1)) is None, "Chiều sâu không tách"


@pytest.mark.skipif(not CO_FFMPEG, reason="máy không có ffmpeg")
def test_dung_chuoi_co_diem_bam_thi_tach_lai_anh_do(tmp_path):
    from autoedit.collage.kho_tach import KhoTach
    kt = KhoTach(tmp_path / "collage")
    a1 = _anh(tmp_path, "a1.png", 0)
    nhan = []

    def theo_diem(rgb, z, d, **k):
        nhan.append(d)
        return tach.KetQuaTach([], rgb, z, [])

    mau.dung_chuoi([{"anh": str(a1), "giay": 1.0, "mau": "popup", "cd": "",
                     "diem": [{"x": 0.5, "y": 0.5, "dau": 1}]}], [], tmp_path / "ra.mp4", kt,
                   W=W, H=H, fps=12, uoc_do_sau=do_sau_gia, tach_theo_diem=theo_diem)
    assert nhan == [[{"x": 160, "y": 90, "dau": 1}]], "điểm tỉ lệ đổi sang pixel ảnh đã cắt khung"
    assert kt.thong_tin(mau.nhan_anh(a1))["diem"] == [{"x": 0.5, "y": 0.5, "dau": 1}]


# ═══════ hàng đợi + thợ ═══════════════════════════════════════════════════════
def test_hang_doi_mang_chuoi_va_tho_dung_chuoi(tmp_path, monkeypatch):
    from autoedit.collage import tho
    from autoedit.collage.hang_doi import HangDoi
    hd = HangDoi(tmp_path / "hd.db")
    chuoi = {"anh": [{"anh": "a.png", "giay": 2.0, "mau": "popup", "cd": ""},
                     {"anh": "b.png", "giay": 3.0, "mau": "chieu_sau", "cd": "push_in"}],
             "noi": ["lia_len"]}
    ma = hd.tao(nguoi="an", model="VOX-chuoi", giay=5.0, cd="", anh="a.png", nhan="", chuoi=chuoi)
    assert json.loads(hd.doc(ma)["chuoi"]) == chuoi
    goi = []
    monkeypatch.setattr(mau, "dung_chuoi", lambda ds, noi, ra, kt, **k: goi.append((ds, noi)))
    tho.dung_mac_dinh(hd.doc(ma), goc=tmp_path / "collage")
    assert goi == [(chuoi["anh"], chuoi["noi"])]


def test_hang_doi_cu_chua_co_cot_chuoi_van_mo_duoc(tmp_path):
    import sqlite3
    p = tmp_path / "cu.db"
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE viec(id TEXT PRIMARY KEY, nguoi TEXT, model TEXT, giay REAL, cd TEXT, anh TEXT, "
              "nhan TEXT, trang_thai TEXT, tao REAL, bat_dau REAL, xong_luc REAL, ra TEXT, loi TEXT, "
              "diem TEXT DEFAULT '[]')")
    c.commit(); c.close()
    from autoedit.collage.hang_doi import HangDoi
    hd = HangDoi(p)
    assert json.loads(hd.doc(hd.tao(nguoi="an", model="VOX-chuoi", giay=1, cd="", anh="a", nhan=""))["chuoi"]) == {}


# ═══════ khung chọn được (user chốt 07/10: ô chọn 16:9 / 4:5 / 9:16) ═════════════════
def test_bang_khung():
    assert mau.KHUNG == {"16:9": (1920, 1080), "4:5": (1080, 1350), "9:16": (1080, 1920)}


def test_tho_dung_dung_khung_cua_viec(tmp_path, monkeypatch):
    from autoedit.collage import tho
    goi = []
    monkeypatch.setattr(mau, "dung_chuoi", lambda ds, noi, ra, kt, **k: goi.append((k.get("W"), k.get("H"))))
    for khung, ra in (("4:5", (1080, 1350)), (None, (1920, 1080))):
        ch = {"anh": [{"anh": "a.png", "giay": 2.0, "mau": "chieu_sau", "cd": ""}], "noi": []}
        if khung:
            ch["khung"] = khung
        tho.dung_mac_dinh({"id": "vox-1", "model": "VOX-chuoi", "anh": str(tmp_path / "a.png"), "giay": 2,
                           "cd": "", "nhan": "", "chuoi": json.dumps(ch)}, goc=tmp_path / "collage")
        assert goi[-1] == ra, "việc cũ không có khung -> 16:9 như trước"


@pytest.mark.skipif(not CO_FFMPEG, reason="máy không có ffmpeg")
def test_doi_khung_thi_tach_lai_cung_khung_thi_dung_lai(tmp_path):
    """Bản tách làm trên ảnh ĐÃ CẮT KHUNG: đổi khung mà dùng lại mask cũ là lệch cỡ."""
    from autoedit.collage.kho_tach import KhoTach
    kt = KhoTach(tmp_path / "collage")
    a = _anh(tmp_path, "a.png", 0, w=320, h=400)
    goi = []

    def tach_gia(rgb, z, **k):
        goi.append(rgb.shape[:2])
        return tach.KetQuaTach([], rgb, z, ["khong_tach_duoc_vat"])

    ds = [{"anh": str(a), "giay": 0.5, "mau": "popup", "cd": ""}]
    for W_, H_ in ((160, 90), (72, 90), (72, 90)):
        mau.dung_chuoi(ds, [], tmp_path / "ra.mp4", kt, W=W_, H=H_, fps=12, uoc_do_sau=do_sau_gia, tach_lop=tach_gia)
    assert goi == [(180, 320), (400, 320)], f"tách lại khi đổi khung, dùng lại khi giữ khung: {goi}"
