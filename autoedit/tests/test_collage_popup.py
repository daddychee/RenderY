"""Collage — "VOX · Pop-up 2.5D": tách lưu THEO CẢNH, máy gắn ⚠ chỗ không chắc, người sửa
bằng CÚ BẤM rồi dựng lại đúng cảnh đó (user chốt 06/10/2026, cách A: dựng thẳng, sửa sau).

Vì sao phải lưu + sửa được: tách tự động chạy lại ra Y HỆT (đo 5 cảnh thật: đúng ~3/5) — bấm
dựng lại vô ích; sản phẩm cuối là video nên chỗ cắt sai phải có đường người sửa.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("torch")

from autoedit.collage import mau, tach  # noqa: E402
from autoedit.collage.hang_doi import HangDoi  # noqa: E402
from autoedit.collage.kho_tach import KhoTach  # noqa: E402

CO_FFMPEG = shutil.which("ffmpeg") is not None


def _anh(tmp_path, ten="canh.png", w=200, h=120, seed=0):
    from PIL import Image
    r = np.random.default_rng(seed)
    a = (r.random((h // 8 + 1, w // 8 + 1, 3)) * 255).astype(np.uint8)
    p = tmp_path / ten
    Image.fromarray(a).resize((w, h), Image.BICUBIC).save(p)
    return p


def _vat(h=120, w=200):
    m = np.zeros((h, w), bool)
    m[30:, 70:130] = True
    return m


def _kq(h=120, w=200, co=None):
    m = _vat(h, w)
    return tach.KetQuaTach([(m, 5.0)], np.full((h, w, 3), 0.5, np.float32),
                           np.full((h, w), 30.0, np.float32), co or [])


# ═══════ kho tách theo cảnh ═════════════════════════════════════════════════
def test_kho_tach_ghi_doc_lai_dung_va_bo_khi_anh_doi(tmp_path):
    kt = KhoTach(tmp_path / "collage")
    rgb = np.zeros((120, 200, 3), np.float32)
    kt.ghi("SE001/c1", "bam-anh-1", _kq(co=["mep_yeu"]), rgb, diem=None)
    kq = kt.doc("SE001/c1", "bam-anh-1")
    assert len(kq.vat) == 1 and (kq.vat[0][0] == _vat()).all() and kq.vat[0][1] == 5.0
    assert kq.co == ["mep_yeu"]
    assert kt.doc("SE001/c1", "bam-anh-KHAC") is None, "vẽ lại ảnh cảnh -> bản tách cũ bỏ"
    tt = kt.thong_tin("SE001/c1")
    assert tt["co"] == ["mep_yeu"] and tt["so_vat"] == 1 and Path(tt["xem"]).exists()


def test_kho_tach_chan_nhan_doc_hai(tmp_path):
    kt = KhoTach(tmp_path / "collage")
    with pytest.raises(ValueError):
        kt.thu_muc("../../Windows/x")


# ═══════ tách theo điểm bấm ═══════════════════════════════════════════════════
class _SamGhi:
    def __init__(self, ds):
        self.ds, self.goi = ds, []

    def tach(self, rgb, pts, nhan=None):
        self.goi.append((pts, nhan))
        return self.ds


def test_tach_theo_diem_gui_ca_diem_am_va_chon_phuong_an_diem_cao():
    h, w = 120, 200
    m_dung, m_sai = _vat(), np.zeros((h, w), bool)
    m_sai[:60] = True
    sam = _SamGhi([(m_sai, 0.5), (m_dung, 0.93)])
    z = np.full((h, w), 30.0, np.float32)
    z[m_dung] = 6.0
    diem = [{"x": 100, "y": 80, "dau": 1}, {"x": 20, "y": 20, "dau": 0}]
    kq = tach.tach_theo_diem(np.zeros((h, w, 3), np.float32), z, diem, sam=sam,
                             va_nen=lambda a, mk: a, uoc_do_sau=lambda x: z)
    assert sam.goi[0] == ([[100, 80], [20, 20]], [1, 0])
    assert len(kq.vat) == 1 and (kq.vat[0][0] == m_dung).all() and kq.vat[0][1] == 6.0
    assert kq.co == [], "người đã bấm thì không gắn cờ"


def test_tach_tu_dong_gan_co_khi_khong_chac():
    h, w = 120, 200
    m = _vat()
    z = np.full((h, w), 30.0, np.float32)
    z[m] = 5.0
    kq = tach.tach_lop(np.zeros((h, w, 3), np.float32), z, sam=_SamGhi([(m, 0.6)]),
                       va_nen=lambda a, mk: a, uoc_do_sau=lambda x: z)
    assert len(kq.vat) == 1 and "diem_sam_thap" in kq.co


# ═══════ mẫu Pop-up ═══════════════════════════════════════════════════════════
@pytest.mark.skipif(not CO_FFMPEG, reason="máy không có ffmpeg")
def test_popup_dung_tach_luu_san_va_ghi_video(tmp_path):
    kt = KhoTach(tmp_path / "collage")
    p = _anh(tmp_path)
    kt.ghi("SE001/c1", mau.bam_anh(p), _kq(), np.zeros((120, 200, 3), np.float32))
    goi = []

    def khong_duoc_tach(*a, **k):
        goi.append(1)
        raise AssertionError("đã có bản tách lưu sẵn thì không tách lại")

    ra = tmp_path / "ra.mp4"
    mau.dung_popup(p, 1.0, "push_in", ra, "SE001/c1", kt, W=160, H=96, fps=12,
                   uoc_do_sau=lambda x: np.full(x.shape[:2], 30.0, np.float32), tach_lop=khong_duoc_tach)
    assert ra.stat().st_size > 0 and not goi


@pytest.mark.skipif(not CO_FFMPEG, reason="máy không có ffmpeg")
def test_popup_khong_co_vat_thi_lui_ve_chieu_sau_va_luu_co(tmp_path):
    kt = KhoTach(tmp_path / "collage")
    p = _anh(tmp_path)
    ra = tmp_path / "ra.mp4"
    mau.dung_popup(p, 1.0, "", ra, "SE001/c1", kt, W=160, H=96, fps=12,
                   uoc_do_sau=lambda x: np.full(x.shape[:2], 30.0, np.float32),
                   tach_lop=lambda rgb, z, **k: tach.KetQuaTach([], rgb, z, ["khong_tach_duoc_vat"]))
    assert ra.stat().st_size > 0
    assert kt.thong_tin("SE001/c1")["co"] == ["khong_tach_duoc_vat"]


@pytest.mark.skipif(not CO_FFMPEG, reason="máy không có ffmpeg")
def test_popup_co_diem_bam_thi_tach_lai_theo_diem_va_ghi_de(tmp_path):
    kt = KhoTach(tmp_path / "collage")
    p = _anh(tmp_path)
    kt.ghi("SE001/c1", mau.bam_anh(p), _kq(co=["mep_yeu"]), np.zeros((120, 200, 3), np.float32))
    diem = [{"x": 100, "y": 80, "dau": 1}]
    mau.dung_popup(p, 1.0, "", tmp_path / "ra.mp4", "SE001/c1", kt, diem=diem, W=160, H=96, fps=12,
                   uoc_do_sau=lambda x: np.full(x.shape[:2], 30.0, np.float32),
                   tach_theo_diem=lambda rgb, z, d, **k: _kq())
    tt = kt.thong_tin("SE001/c1")
    assert tt["co"] == [] and tt["diem"] == diem, "bản sửa tay đè bản tự động, giữ lại điểm đã bấm"


# ═══════ hàng đợi + nhà Vox ═══════════════════════════════════════════════════
def test_hang_doi_mang_theo_diem_bam(tmp_path):
    hd = HangDoi(tmp_path / "hd.db")
    d = [{"x": 1, "y": 2, "dau": 1}]
    ma = hd.tao(nguoi="an", model="VOX-popup", giay=2, cd="", anh="a.png", nhan="SE001/c1", diem=d)
    assert json.loads(hd.doc(ma)["diem"]) == d


def test_hang_doi_cu_khong_co_cot_diem_van_mo_duoc(tmp_path):
    import sqlite3
    p = tmp_path / "cu.db"
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE viec(id TEXT PRIMARY KEY, nguoi TEXT, model TEXT, giay REAL, cd TEXT, anh TEXT, "
              "nhan TEXT, trang_thai TEXT, tao REAL, bat_dau REAL, xong_luc REAL, ra TEXT, loi TEXT)")
    c.commit(); c.close()
    hd = HangDoi(p)
    ma = hd.tao(nguoi="an", model="VOX-popup", giay=2, cd="", anh="a.png", nhan="x/y", diem=[])
    assert hd.doc(ma)["diem"] == "[]"


def test_tho_chon_mau_theo_model(tmp_path, monkeypatch):
    from autoedit.collage import tho
    goi = []
    monkeypatch.setattr(mau, "dung_video", lambda *a, **k: goi.append("chieu_sau"))
    monkeypatch.setattr(mau, "dung_popup", lambda *a, **k: goi.append(("popup", k.get("diem"))))
    for model, diem in (("VOX-chieu-sau", "[]"), ("VOX-popup", '[{"x": 1, "y": 2, "dau": 1}]')):
        tho.dung_mac_dinh({"id": "vox-1", "model": model, "anh": str(tmp_path / "vao.png"), "giay": 1.0,
                           "cd": "", "nhan": "SE001/c1", "diem": diem}, goc=tmp_path / "collage")
    assert goi == ["chieu_sau", ("popup", [{"x": 1, "y": 2, "dau": 1}])]
