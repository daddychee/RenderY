"""Hồ Sơ Kênh (Đợt A) — đo kênh ref → hồ sơ 3 tầng, cache theo kênh.

Không mạng: hàm tải tiêm được (`tai=`); đo nhịp dùng video tổng hợp ffmpeg
(cắt cứng biết trước — đúng khuôn hiệu chuẩn nhip/do.py); nhạc dùng wav
tổng hợp có đoạn to/nhỏ biết trước.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from autoedit.kenh.do_kenh import (DoKenhError, _hook_kieu, do_kenh,
                                   do_nhac_ffmpeg, slug_tu_link)
from autoedit.kenh.hoso import HoSoKenh


# ------------------------------------------------------------ slug
def test_slug_kenh_handle():
    assert slug_tu_link("https://www.youtube.com/@fern-tv") == "fern-tv"
    assert slug_tu_link("https://youtube.com/@JohnnyHarris/videos") == "johnnyharris"


def test_slug_video_le():
    assert slug_tu_link("https://www.youtube.com/watch?v=-Gnrp_caPvo") == "video--Gnrp_caPvo"
    assert slug_tu_link("https://youtu.be/frr9AdZXrJc") == "video-frr9AdZXrJc"


def test_slug_link_rac_bao_loi():
    with pytest.raises(DoKenhError):
        slug_tu_link("???")


# ------------------------------------------------------------ hook kiểu
def test_hook_kieu_theo_ty_le():
    assert _hook_kieu(0.72, 2.1) == "no"      # Fern thật: 0.72/2.1 ≈ 0.34
    assert _hook_kieu(1.8, 2.5) == "leo"
    assert _hook_kieu(2.4, 2.5) == "em"
    assert _hook_kieu(0, 2.5) == ""           # thiếu số -> không đoán


# ------------------------------------------------------------ nhạc ffmpeg
def test_do_nhac_ffmpeg_bat_duoc_doan_to(tmp_path):
    """WAV 24s: 8s nhỏ + 8s TO + 8s nhỏ -> bucket giữa phải mạnh nhất."""
    f = tmp_path / "test.wav"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=8",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=8",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=8",
        "-filter_complex",
        "[0]volume=0.05[a];[1]volume=1.0[b];[2]volume=0.05[c];[a][b][c]concat=n=3:v=0:a=1",
        str(f)], check=True)
    kq = do_nhac_ffmpeg(f)
    assert len(kq["curve"]) == 12
    assert 0.25 < kq["vi_tri_drop"] < 0.75, f"drop phải ở GIỮA: {kq['vi_tri_drop']}"
    assert kq["do_dong"] > 10, "chênh 0.05 vs 1.0 volume phải ra dải động lớn"


def test_do_nhac_ffmpeg_file_cut_tra_rong(tmp_path):
    f = tmp_path / "hong.wav"
    f.write_bytes(b"khong phai wav")
    kq = do_nhac_ffmpeg(f)
    assert kq["curve"] == []                   # không nổ, trả rỗng để caller bỏ qua


# ------------------------------------------------------------ do_kenh + cache
def _video_cat_cung(dich: Path, ten: str, n_shot: int = 80, shot_s: float = 3.0):
    """Video tổng hợp n_shot cảnh màu khác nhau — điểm cắt biết trước, đủ dài
    (240s+) để qua lọc thời lượng và đo được hook/thân."""
    mau = ["red", "blue", "green", "yellow", "purple", "orange"]
    inputs, filters = [], []
    for i in range(n_shot):
        inputs += ["-f", "lavfi", "-t", str(shot_s),
                   "-i", f"color=c={mau[i % len(mau)]}:s=320x180:r=10"]
        filters.append(f"[{i}]")
    fc = "".join(filters) + f"concat=n={n_shot}:v=1:a=0[v]"
    f = dich / ten
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inputs
                   + ["-filter_complex", fc, "-map", "[v]", str(f)], check=True)
    return f


@pytest.fixture()
def cache_rieng(tmp_path, monkeypatch):
    """Trỏ cache kênh vào tmp — không đụng data root thật của máy."""
    import autoedit.kenh.hoso as mh
    monkeypatch.setattr(mh, "resolve_data_root", lambda *a, **k: tmp_path)
    return tmp_path


def test_do_kenh_do_that_va_cache(cache_rieng, tmp_path):
    video_dir = tmp_path / "vids"
    video_dir.mkdir()
    _video_cat_cung(video_dir, "v1.mp4")

    goi_tai = []

    def tai_gia(link, dich, so_video=3, log=None):
        goi_tai.append(link)
        import shutil
        ra = []
        for f in video_dir.glob("*.mp4"):
            d = dich / f.name
            shutil.copy2(f, d)
            ra.append(d)
        return ra

    hs = do_kenh("https://www.youtube.com/@test-kenh", tai=tai_gia)
    assert hs.ten == "test-kenh"
    assert hs.so_video_hoi_tu == 1
    # video cắt cứng 3s/shot -> trung vị thân phải quanh 3s (thước là cận dưới)
    assert 2.0 <= hs.than_trung_vi <= 4.5, hs.than_trung_vi
    assert HoSoKenh.doc("test-kenh") is not None    # đã cache

    # lần 2: CACHE HIT — không được gọi tải nữa (luật né chặn IP)
    hs2 = do_kenh("https://www.youtube.com/@test-kenh", tai=tai_gia)
    assert len(goi_tai) == 1, "cache hit vẫn tải lại = vi phạm luật né chặn IP"
    assert hs2.than_trung_vi == hs.than_trung_vi

    # --do-lai: chủ động đo mới -> được tải lại
    do_kenh("https://www.youtube.com/@test-kenh", do_lai=True, tai=tai_gia)
    assert len(goi_tai) == 2


def test_do_kenh_khong_video_nao_hoi_tu_bao_ro(cache_rieng, tmp_path):
    def tai_rong(link, dich, so_video=3, log=None):
        f = dich / "hong.mp4"
        f.write_bytes(b"khong phai video")
        return [f]

    with pytest.raises(DoKenhError, match="hội tụ"):
        do_kenh("https://www.youtube.com/@kenh-hong", tai=tai_rong)


# ------------------------------------------------------------ áp vào HoSoNhip
def test_ap_vao_nhip_chi_de_truong_co_so():
    from autoedit.nhip.profile import nap
    hs_nhip = nap("investigate")
    goc_chu_ky = hs_nhip.bung_chu_ky_s
    hk = HoSoKenh(ten="t", than_trung_vi=1.8, than_ty_le_nhanh=0.6,
                  than_ty_le_hold=0.1, hook_trung_vi=0.8, hook_ty_le_nhanh=0.9,
                  hook_kieu="no", bung_chu_ky_s=0.0)     # chu kỳ KHÔNG đo được
    hs_moi, log = hk.ap_vao_nhip(hs_nhip)
    assert hs_moi.than_trung_vi == 1.8
    assert hs_moi.hook_kieu == "no"
    assert hs_moi.bung_chu_ky_s == goc_chu_ky             # 0 = giữ số niche, không đè
    assert hs_nhip.than_trung_vi == 2.5                    # bản gốc frozen giữ nguyên
    assert log and "«t»" in log[0]
