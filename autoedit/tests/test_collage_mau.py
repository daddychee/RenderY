"""Collage — mẫu "VOX · Chiều sâu" + THỢ dựng: ảnh đã duyệt + giây + mã camera -> mp4.

Cả Master Frame thành nền có độ sâu TỪNG PIXEL (Depth Anything V2 Small, Apache 2.0) —
camera theo mã `cd` của cảnh (cùng bảng mã treatment). Không cần tách layer nên chạy được
ngay cho cả đội; mẫu có tách layer để sau (P3).

Luật kiểm bắt buộc (skill collage-chuyen-dong): lộ mép = 0 ngoài cú lia vút.
Test KHÔNG tải model độ sâu thật: tiêm hàm ước độ sâu giả.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("torch")

from autoedit.collage import mau  # noqa: E402
from autoedit.collage.dung import Canh  # noqa: E402
from autoedit.collage.hang_doi import HangDoi  # noqa: E402
from autoedit.collage.tho import chay_mot  # noqa: E402

CO_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def do_sau_gia(rgb):
    """Trên xa (trời), dưới gần (đất) — đủ để có parallax mà không cần model."""
    h, w = rgb.shape[:2]
    return np.linspace(40.0, 4.0, h, dtype=np.float32)[:, None].repeat(w, 1)


def _anh(tmp_path, w=320, h=180):
    from PIL import Image
    r = np.random.default_rng(0)
    a = (r.random((h // 8 + 1, w // 8 + 1, 3)) * 255).astype(np.uint8)
    p = tmp_path / "canh.png"
    Image.fromarray(a).resize((w, h), Image.BICUBIC).save(p)
    return p


@pytest.mark.parametrize("cd", sorted(mau.MA_CAMERA))
def test_moi_ma_camera_deu_khong_lo_mep(tmp_path, cd):
    rgb = np.asarray(__import__("PIL.Image", fromlist=["Image"]).open(_anh(tmp_path)).convert("RGB"),
                     np.float32) / 255
    canh = Canh(rgb, do_sau_gia(rgb), W=160, H=90, zoom=mau.ZOOM)
    cam = mau.ke_hoach(cd, 4.0, canh)
    lo = mau.lo_mep_toi_da(canh, cam, 4.0, mien=mau.MIEN_LIA.get(cd))
    assert lo == 0.0, f"{cd}: lộ mép {lo:.3%}"


def test_ma_camera_la_bang_ma_cua_treatment():
    from autoedit.treatment.app import CD_CHU
    assert set(CD_CHU) <= set(mau.MA_CAMERA), "mã nào treatment bày ra thì Vox phải làm được"


def test_ma_la_hoac_rong_van_dung_duoc(tmp_path):
    rgb = np.zeros((90, 160, 3), np.float32)
    canh = Canh(rgb, do_sau_gia(rgb), W=160, H=90, zoom=mau.ZOOM)
    for cd in ("", "khong_co_ma_nay"):
        assert mau.lo_mep_toi_da(canh, mau.ke_hoach(cd, 3.0, canh), 3.0) == 0.0


@pytest.mark.skipif(not CO_FFMPEG, reason="máy không có ffmpeg/ffprobe")
def test_dung_video_ra_mp4_dung_so_giay(tmp_path):
    ra = tmp_path / "ra.mp4"
    mau.dung_video(_anh(tmp_path), 1.5, "truck_left", ra, W=160, H=90, fps=12, uoc_do_sau=do_sau_gia)
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "json", str(ra)], capture_output=True, text=True)
    assert abs(float(json.loads(p.stdout)["format"]["duration"]) - 1.5) < 0.15


@pytest.mark.skipif(not CO_FFMPEG, reason="máy không có ffmpeg/ffprobe")
def test_tho_lam_het_vong_mot_viec(tmp_path):
    hd = HangDoi(tmp_path / "hang_doi.db")
    tid = hd.tao(nguoi="an", model="VOX-chieu-sau", giay=1.0, cd="push_in",
                 anh=str(_anh(tmp_path)), nhan="SE001/c1")

    def dung(viec):
        ra = Path(tmp_path / f"{viec['id']}.mp4")
        mau.dung_video(Path(viec["anh"]), viec["giay"], viec["cd"], ra, W=160, H=90, fps=12,
                       uoc_do_sau=do_sau_gia)
        return ra

    assert chay_mot(hd, dung) is True
    v = hd.doc(tid)
    assert v["trang_thai"] == "xong" and Path(v["ra"]).stat().st_size > 0
    assert chay_mot(hd, dung) is False, "hết việc thì báo không làm gì"


def test_tho_ghi_hong_khi_dung_loi(tmp_path):
    hd = HangDoi(tmp_path / "hang_doi.db")
    tid = hd.tao(nguoi="an", model="VOX-chieu-sau", giay=1.0, cd="", anh="khong-co.png", nhan="x")

    def dung(viec):
        raise FileNotFoundError("không thấy ảnh cảnh")

    assert chay_mot(hd, dung) is True
    assert hd.doc(tid)["trang_thai"] == "hong" and "ảnh" in hd.doc(tid)["loi"]
