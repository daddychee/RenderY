r"""TRIM XONG NHƯNG IMPORT KHÔNG ĂN — pexels/pixabay/kho bỏ qua toạ độ trim.

User báo 17/09: *"Vẫn gặp lỗi khi trim video: Mặc dù đã trim xong nhưng khi import
thì đoạn trim lại không được import."*

Trim KHÔNG cắt file (đúng thiết kế sổ tra: "chỉ ghi toạ độ"). Nó đẻ ra một clip con
`<id mẹ>#<t0>-<t1>` mang `t0`/`t1`, rồi lúc dựng draft `relocate` phải cắt đúng khúc
đó ra `assets`. `ref` và `envato` làm đúng (`cat_clip`), nhưng:

    pexels   -> `_tai(url, dich)`      tải NGUYÊN file, không cắt
    pixabay  -> `_tai(url, dich)`      tải NGUYÊN file, không cắt
    kho      -> `shutil.copy2`         chép NGUYÊN file, không cắt

`dung_draft` đặt segment `Timerange(t0_us, dai_us)` KHÔNG kèm `source_timerange`,
tức luôn phát từ giây 0 của file trong assets. File chưa cắt -> ra đúng đoạn đầu
clip gốc, không phải khúc người dựng chọn.

ĐO TRÊN 86 CHƯƠNG ĐANG CÓ (17/09) — miếng đang dùng khúc đã trim:

    envato   85  cắt đúng          ref      84  cắt đúng
    pexels   47  BỎ QUA TRIM       pixabay  16  BỎ QUA TRIM       kho   2  BỎ QUA TRIM

= 65 miếng đang sai.

Kèm theo: `_pexels_goc`/`_pixabay_goc` lấy mã clip bằng `cid.split(":")[1]` nên với
id đã trim thì mã mang theo cả `#0.00-10.00` — URL ăn may vì HTTP cắt phần `#`,
nhưng đó là may chứ không phải đúng.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _mp4(dich: Path, giay: float) -> Path:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", f"testsrc=size=160x90:rate=15:duration={giay}",
                    "-pix_fmt", "yuv420p", str(dich)], check=True)
    return dich


def _dai(f: Path) -> float:
    from autoedit.project import ffprobe_duration

    return ffprobe_duration(f) or 0.0


def _hd(cid: str, nguon: str) -> dict:
    return {"offset": 0.0,
            "khoi": [{"v0": 0.0, "v1": 3.0, "tho": 0.0}],
            "hinh": [{"t0": 0.0, "dur": 3.0, "khoi_goc": 0, "chon": 0,
                      "uv": [{"id": cid, "nguon": nguon, "tieu_de": "thu"}]}]}


@pytest.fixture
def kho(tmp_path):
    from autoedit.sotra import db as sdb

    c = sdb.mo(tmp_path / "kho" / "sotra.db")
    yield c, sdb
    c.close()


def _chay(tm, tmp_path, conn, hd):
    proj = tmp_path / "proj"
    proj.mkdir(exist_ok=True)
    video, _ids, warns, _du = tm.relocate(proj, hd, conn, lambda m: None)
    return video, warns


def test_pexels_da_trim_phai_CAT_dung_khuc(tmp_path, kho, monkeypatch):
    """Clip gốc 10s, người dựng chọn khúc 3–7s -> file trong assets phải ~4s."""
    from autoedit.offline import thay_mau as tm

    conn, sdb = kho
    goc = _mp4(tmp_path / "goc.mp4", 10)
    cid = "pexels:777#3.00-7.00"
    sdb.them_clip(conn, {"id": cid, "nguon": "pexels", "tieu_de": "thu [3.0-7.0s]",
                         "t0": 3.0, "t1": 7.0, "dai_s": 4.0})
    conn.commit()
    monkeypatch.setattr(tm, "_pexels_goc", lambda c: "http://x/goc.mp4")
    monkeypatch.setattr(tm, "_tai", lambda url, dich: dich.write_bytes(goc.read_bytes()))
    monkeypatch.setattr(tm.time, "sleep", lambda *a: None)

    video, _w = _chay(tm, tmp_path, conn, _hd(cid, "pexels"))
    assert 0 in video, "không lấy được file nào"
    assert _dai(video[0]) == pytest.approx(4.0, abs=0.5), (
        f"file trong assets dài {_dai(video[0]):.1f}s — nguyên clip gốc, trim bị bỏ")


def test_pixabay_da_trim_phai_CAT_dung_khuc(tmp_path, kho, monkeypatch):
    from autoedit.offline import thay_mau as tm

    conn, sdb = kho
    goc = _mp4(tmp_path / "goc2.mp4", 10)
    cid = "pixabay:888#6.00-9.00"
    sdb.them_clip(conn, {"id": cid, "nguon": "pixabay", "tieu_de": "thu [6.0-9.0s]",
                         "t0": 6.0, "t1": 9.0, "dai_s": 3.0})
    conn.commit()
    monkeypatch.setattr(tm, "_pixabay_goc", lambda c: "http://x/goc.mp4")
    monkeypatch.setattr(tm, "_tai", lambda url, dich: dich.write_bytes(goc.read_bytes()))
    monkeypatch.setattr(tm.time, "sleep", lambda *a: None)

    video, _w = _chay(tm, tmp_path, conn, _hd(cid, "pixabay"))
    assert 0 in video
    assert _dai(video[0]) == pytest.approx(3.0, abs=0.5), (
        f"file trong assets dài {_dai(video[0]):.1f}s — trim bị bỏ")


def test_kho_da_trim_phai_CAT_dung_khuc(tmp_path, kho):
    """Nguồn `kho` (clip cũ đã nằm trên ổ) cũng đang chép nguyên file."""
    from autoedit.offline import thay_mau as tm

    conn, sdb = kho
    goc = _mp4(tmp_path / "goc3.mp4", 8)
    cid = "kho:tap1:canh.mp4#2.00-5.00"
    sdb.them_clip(conn, {"id": cid, "nguon": "kho", "tieu_de": "canh [2.0-5.0s]",
                         "path_local": str(goc), "t0": 2.0, "t1": 5.0, "dai_s": 3.0})
    conn.commit()

    video, _w = _chay(tm, tmp_path, conn, _hd(cid, "kho"))
    assert 0 in video
    assert _dai(video[0]) == pytest.approx(3.0, abs=0.5), (
        f"file trong assets dài {_dai(video[0]):.1f}s — trim bị bỏ")


def test_CHUA_trim_thi_giu_nguyen_ca_clip(tmp_path, kho, monkeypatch):
    """Không có t0/t1 -> vẫn lấy nguyên clip như cũ (không tự cắt bừa)."""
    from autoedit.offline import thay_mau as tm

    conn, sdb = kho
    goc = _mp4(tmp_path / "goc4.mp4", 6)
    cid = "pexels:999"
    sdb.them_clip(conn, {"id": cid, "nguon": "pexels", "tieu_de": "nguyen clip"})
    conn.commit()
    monkeypatch.setattr(tm, "_pexels_goc", lambda c: "http://x/goc.mp4")
    monkeypatch.setattr(tm, "_tai", lambda url, dich: dich.write_bytes(goc.read_bytes()))
    monkeypatch.setattr(tm.time, "sleep", lambda *a: None)

    video, _w = _chay(tm, tmp_path, conn, _hd(cid, "pexels"))
    assert 0 in video
    assert _dai(video[0]) == pytest.approx(6.0, abs=0.5)


def test_ma_clip_KHONG_mang_theo_duoi_trim(tmp_path):
    """`_pexels_goc`/`_pixabay_goc` phải bỏ đuôi `#t0-t1` trước khi gọi API —
    nay đang ăn may vì HTTP tự cắt phần sau dấu `#`."""
    from autoedit.offline import thay_mau as tm

    goi = {}
    import urllib.request

    class R:
        def read(self):
            return b'{"video_files": [{"height": 1080, "link": "http://x/a.mp4"}]}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def gia(req, timeout=0):
        goi["url"] = req.full_url if hasattr(req, "full_url") else str(req)
        return R()

    import unittest.mock as um

    with um.patch.object(urllib.request, "urlopen", gia):
        tm._pexels_goc("pexels:34914524#0.00-10.00")
    assert "#" not in goi["url"], f"mã clip mang theo đuôi trim: {goi['url']}"
    assert goi["url"].rstrip("/").endswith("34914524"), goi["url"]


def test_MIENG_DAP_THEM_cung_ton_trong_trim(tmp_path, kho, monkeypatch):
    """`lay_du` (miếng đắp thêm cho clip ngắn, chốt 13/09) lấy file bằng đường
    RIÊNG — sửa đường chính mà quên đường này là nửa số miếng vẫn sai."""
    from autoedit.offline import thay_mau as tm

    conn, sdb = kho
    goc = _mp4(tmp_path / "goc5.mp4", 10)
    cid = "pexels:555#1.00-4.00"
    sdb.them_clip(conn, {"id": cid, "nguon": "pexels", "tieu_de": "du [1.0-4.0s]",
                         "t0": 1.0, "t1": 4.0, "dai_s": 3.0})
    conn.commit()
    monkeypatch.setattr(tm, "_pexels_goc", lambda c: "http://x/goc.mp4")
    monkeypatch.setattr(tm, "_tai", lambda url, dich: dich.write_bytes(goc.read_bytes()))
    monkeypatch.setattr(tm.time, "sleep", lambda *a: None)

    f = tm.lay_du(conn, tmp_path, 0, [{"id": cid, "tieu_de": "du"}], 3.0, lambda m: None)
    assert f is not None and f.is_file()
    assert _dai(f) == pytest.approx(3.0, abs=0.5), (
        f"miếng đắp thêm dài {_dai(f):.1f}s — trim bị bỏ")
