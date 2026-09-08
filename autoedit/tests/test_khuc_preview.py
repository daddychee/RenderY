"""Khúc preview hỏng thì KHÔNG được cache vĩnh viễn (user báo 08/09).

Triệu chứng: chương C5 tập LI089 — bấm lần lượt qua 42 miếng thì **22 miếng
preview đen**, đúng 22 miếng đó, lặp lại y hệt, chờ 2s vẫn đen; nhưng nhảy
THẲNG vào một miếng thì nó hiện bình thường.

Đo ra gốc: các khúc đen đều là FILE HỎNG — `ffprobe` báo `Invalid NAL unit` và
không đếm nổi frame, trong khi khúc tốt đếm bình thường. Quét cả kho:
**27/305 khúc hỏng, toàn bộ là ref của LI089**, sinh trong khoảng 09:57–16:16,
nhiều cái đúng phút tôi dừng máy chủ để nâng cấp.

Nguyên nhân: `khuc_clip` ghi ffmpeg THẲNG vào file cache, rồi lần sau chỉ kiểm
`size > 0` là tin. ffmpeg bị giết giữa chừng (restart, timeout, hết đĩa) để lại
file dở nhưng khác rỗng — cache tin nó MÃI MÃI, và preview đen không lời giải
thích (BH1: fail-open phải rung chuông).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _video_that(f: Path, giay: float = 2.0) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", f"color=c=red:s=320x180:d={giay}", "-pix_fmt", "yuv420p",
                    str(f)], check=True)


@pytest.fixture
def kho(tmp_path, monkeypatch):
    """Sổ tra tạm + một clip ref có toạ độ."""
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    goc = tmp_path / "ref.mp4"
    _video_that(goc, 4.0)
    conn = sdb.mo()
    sdb.them_clip(conn, {"id": "ref:T:1.0-2.5", "nguon": "ref", "tap": "T",
                         "tieu_de": "thu", "path_local": str(goc), "t0": 1.0, "t1": 2.5})
    conn.commit()
    yield conn, tmp_path
    conn.close()


def _hop_le(f: Path) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(f)],
                       capture_output=True, text=True)
    return r.returncode == 0 and bool(r.stdout.strip()) and not r.stderr.strip()


def test_cat_binh_thuong_ra_khuc_doc_duoc(kho):
    from autoedit.sotra.media import khuc_clip

    conn, _ = kho
    f = khuc_clip(conn, "ref:T:1.0-2.5")
    assert f is not None and f.is_file()
    assert _hop_le(f), "khúc vừa cắt mà ffprobe đọc không được"


def test_khuc_HONG_khong_duoc_de_lai_o_cache(kho, monkeypatch):
    """ffmpeg "thành công" nhưng ra file rác -> KHÔNG được để lại file nào ở
    đường dẫn cache, nếu không lần sau cache tin nó mãi mãi."""
    from autoedit.sotra import media

    conn, _ = kho
    that = subprocess.run

    def gia(cmd, *a, **k):
        if cmd and cmd[0] == "ffmpeg":
            dich = Path(cmd[-1])
            dich.write_bytes(b"\x00\x01rac khong phai video" * 400)   # file dở
            return subprocess.CompletedProcess(cmd, 0, b"", b"")
        return that(cmd, *a, **k)

    monkeypatch.setattr(media.subprocess, "run", gia)
    f = khuc = media.khuc_clip(conn, "ref:T:1.0-2.5")
    assert f is None, "trả về file rác"
    conn2, tmp = kho[0], kho[1]
    con = list((tmp / "so_tra" / "prev_cache").glob("*.mp4"))
    assert not con, f"còn file hỏng nằm lại trong cache: {[x.name for x in con]}"


def test_ffmpeg_chet_giua_chung_khong_de_lai_gi(kho, monkeypatch):
    """Đúng cảnh 08/09: máy chủ bị dừng lúc luồng hâm cache đang cắt."""
    from autoedit.sotra import media

    conn, tmp = kho
    that = subprocess.run

    def gia(cmd, *a, **k):
        if cmd and cmd[0] == "ffmpeg":
            Path(cmd[-1]).write_bytes(b"\x00" * 5000)      # ghi dở rồi bị giết
            return subprocess.CompletedProcess(cmd, 255, b"", b"killed")
        return that(cmd, *a, **k)

    monkeypatch.setattr(media.subprocess, "run", gia)
    assert media.khuc_clip(conn, "ref:T:1.0-2.5") is None
    con = list((tmp / "so_tra" / "prev_cache").glob("*.mp4"))
    assert not con, f"file dở nằm lại: {[x.name for x in con]}"


def test_khuc_da_co_thi_KHONG_cat_lai(kho, monkeypatch):
    """Cắt lại mỗi lần xem là mất hết ý nghĩa của cache."""
    from autoedit.sotra import media

    conn, _ = kho
    f1 = media.khuc_clip(conn, "ref:T:1.0-2.5")
    assert f1 is not None
    goi = []
    that = subprocess.run
    monkeypatch.setattr(media.subprocess, "run",
                        lambda cmd, *a, **k: (goi.append(cmd[0]), that(cmd, *a, **k))[1])
    f2 = media.khuc_clip(conn, "ref:T:1.0-2.5")
    assert f2 == f1 and "ffmpeg" not in goi


# ------------------------------------------------- dọn khúc hỏng đã lỡ cache

def test_don_khuc_hong_chi_xoa_cai_hong(kho):
    from autoedit.sotra.media import don_khuc_hong, khuc_clip

    conn, tmp = kho
    tot = khuc_clip(conn, "ref:T:1.0-2.5")
    cache = tmp / "so_tra" / "prev_cache"
    xau = cache / "ref_HONG.mp4"
    xau.write_bytes(b"\x00\x01khong phai video" * 300)

    assert don_khuc_hong(xoa=False) == 1, "chế độ thử đếm sai"
    assert xau.is_file(), "thử mà đã xoá"
    assert don_khuc_hong(xoa=True) == 1
    assert not xau.exists() and tot.is_file(), "xoá nhầm khúc tốt"
