r"""Việc C — vá 3 lỗ của cơ chế `link_chet` (đo thật 09/09/2026).

Cơ chế đang có LÀNH: clip bị gỡ khỏi Envato -> `trang_thai='link_chet'` ->
`sotra/tra.py:48` lọc `trang_thai='song'` nên khay gợi ý không bao giờ trồi nó
lên nữa. Ba lỗ dưới đây làm cơ chế đó gần như VÔ HIỆU trên đường Offline.

LỖ A — điều kiện đánh dấu không bao giờ đúng
    `offline/thay_mau.py` bắt lỗi rồi kiểm `"không tồn tại" in str(exc)`.
    Grep toàn repo: KHÔNG luồng nào ném chuỗi đó. Preview Envato chết trả
    `urllib.error.HTTPError` -> `str(exc)` là "HTTP Error 404: Not Found".
    Không khớp -> không đánh dấu -> lần dựng sau lại chọn, lại hỏng, lặp mãi.
    Chỉ nhánh "file rỗng" là thật sự chạy được.

LỖ B — clip chết vẫn nằm trong khay ĐÃ LƯU
    `offline/dung.py` `_hong()` mở đầu bằng `if u.get("nguon") != "ref"` ->
    chỉ quét clip ref. Clip envato `link_chet` nằm sẵn trong `uv[]` của hợp
    đồng cũ không bị quét ra. Đo trên 33 chương production: **9 miếng đang
    chọn clip đã `link_chet`**.

LỖ C — thiếu commit tại chỗ
    `UPDATE ... link_chet` không commit ngay. Hiện vẫn lọt nhờ `c.commit()` ở
    cuối `thay_mau`, nhưng khâu giữa ném lỗi là mất sạch dấu đã đánh.

KHÔNG vá lỗi mạng/timeout (`sourcer/tai_sach.py`): user chốt "fail 1 lần bỏ qua
luôn". Đánh `link_chet` vì mạng đứt là giết oan clip còn sống, mà repo KHÔNG có
đường gỡ cờ (grep: không chỗ nào set ngược về 'song').
"""

from __future__ import annotations

import sqlite3
import urllib.error

import pytest

from autoedit.offline import dung as mdung
from autoedit.offline import thay_mau as mtm


# ───────────────────────── LỖ A — nhận diện lỗi ─────────────────────────

def _loi_http(ma: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x/y.mp4", ma, "Not Found", {}, None)  # type: ignore[arg-type]


@pytest.mark.parametrize("ma", [404, 410])
def test_HTTP_404_410_phai_bi_danh_link_chet(ma):
    """Nguồn trả 'không còn nữa' -> đánh dấu. Đây là ca THẬT hay gặp nhất."""
    assert mtm.la_nguon_chet(_loi_http(ma)) is True, (
        f"HTTP {ma} là clip đã bị gỡ — phải đánh link_chet, không thì lần dựng "
        f"sau lại chọn đúng clip đó")


def test_file_rong_van_bi_danh_nhu_cu():
    """Hành vi cũ duy nhất đang chạy được — không được phá."""
    assert mtm.la_nguon_chet(RuntimeError("file rỗng")) is True


def test_thieu_preview_bi_danh():
    """Clip envato không có url_video: không còn đường nào lấy -> coi như chết."""
    assert mtm.la_nguon_chet(RuntimeError("thiếu preview")) is True


@pytest.mark.parametrize("ma", [429, 500, 502, 503])
def test_loi_TAM_THOI_KHONG_duoc_danh_link_chet(ma):
    """429/5xx là hết lượt hoặc nhà cung cấp trục trặc — clip vẫn sống.

    Đánh dấu ở đây là giết oan hàng loạt clip, mà KHÔNG có đường gỡ cờ.
    """
    assert mtm.la_nguon_chet(_loi_http(ma)) is False, (
        f"HTTP {ma} là lỗi tạm thời — đánh link_chet là giết oan clip còn sống")


def test_loi_mang_KHONG_duoc_danh_link_chet():
    """User chốt: fail vì mạng thì bỏ qua, không ghi sổ."""
    assert mtm.la_nguon_chet(urllib.error.URLError("timed out")) is False
    assert mtm.la_nguon_chet(TimeoutError("timed out")) is False


def test_loi_la_thi_KHONG_danh():
    """Không nhận ra thì cứ để clip sống — thà bỏ sót còn hơn giết oan."""
    assert mtm.la_nguon_chet(RuntimeError("chuyện gì đó khác")) is False


# ───────────────────────── LỖ B — quét khay mọi nguồn ─────────────────────────

def _kho(tmp_path):
    """DB nhỏ đúng schema thật."""
    from autoedit.sotra import db as sdb

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(sdb._SCHEMA)
    return conn


def _them(conn, cid, nguon, trang_thai="song", t0=0.0, t1=0.0):
    conn.execute(
        "INSERT INTO clip(id, nguon, tieu_de, trang_thai, t0, t1) VALUES(?,?,?,?,?,?)",
        (cid, nguon, f"clip {cid}", trang_thai, t0, t1))
    conn.commit()


def test_clip_ENVATO_chet_trong_khay_phai_bi_quet_ra(tmp_path):
    """Lỗ B: 9 miếng thật trên production đang chọn clip envato đã link_chet."""
    conn = _kho(tmp_path)
    _them(conn, "envato:song", "envato")
    _them(conn, "envato:chet", "envato", "link_chet")
    khay = [{"id": "envato:song", "nguon": "envato"},
            {"id": "envato:chet", "nguon": "envato"}]
    con = [u for u in khay if not mdung.clip_hong(conn, u)]
    assert [u["id"] for u in con] == ["envato:song"], (
        "clip envato link_chet vẫn nằm trong khay -> người dựng vẫn chọn được")


@pytest.mark.parametrize("nguon", ["envato", "pexels", "pixabay", "kho"])
def test_MOI_nguon_deu_bi_quet(tmp_path, nguon):
    conn = _kho(tmp_path)
    _them(conn, f"{nguon}:chet", nguon, "link_chet")
    assert mdung.clip_hong(conn, {"id": f"{nguon}:chet", "nguon": nguon}) is True


def test_clip_SONG_khong_bi_dung_toi(tmp_path):
    conn = _kho(tmp_path)
    _them(conn, "envato:ok", "envato")
    assert mdung.clip_hong(conn, {"id": "envato:ok", "nguon": "envato"}) is False


def test_ref_giu_nguyen_luat_rieng_phai_co_t1(tmp_path):
    """Ref là KHÚC cắt từ video dài: thiếu t1 là bản đời cũ, vẫn phải loại.

    Luật này chỉ đúng cho ref — nguồn khác không có t0/t1 là chuyện thường.
    """
    conn = _kho(tmp_path)
    _them(conn, "ref:cu", "ref", "song", t0=0.0, t1=0.0)
    _them(conn, "ref:moi", "ref", "song", t0=10.0, t1=16.0)
    # t0/t1 đọc từ MỤC TRONG KHAY (hợp đồng), không từ DB — khay đời cũ thiếu t1.
    assert mdung.clip_hong(conn, {"id": "ref:cu", "nguon": "ref"}) is True
    assert mdung.clip_hong(
        conn, {"id": "ref:moi", "nguon": "ref", "t0": 10.0, "t1": 16.0}) is False


def test_nguon_khac_KHONG_doi_hoi_t1(tmp_path):
    """Đừng đem luật của ref áp cho envato — envato không có t0/t1 là bình thường."""
    conn = _kho(tmp_path)
    _them(conn, "envato:ok", "envato", "song", t0=0.0, t1=0.0)
    assert mdung.clip_hong(conn, {"id": "envato:ok", "nguon": "envato"}) is False


def test_giu_cu_van_duoc_tha(tmp_path):
    """Miếng đang chọn đã vá cờ `giu_cu` thì thôi — không thì ghi lại vô hạn."""
    conn = _kho(tmp_path)
    _them(conn, "envato:chet", "envato", "link_chet")
    assert mdung.clip_hong(
        conn, {"id": "envato:chet", "nguon": "envato", "giu_cu": 1}) is False


def test_clip_KHONG_CO_trong_kho_coi_nhu_hong(tmp_path):
    conn = _kho(tmp_path)
    assert mdung.clip_hong(conn, {"id": "envato:la", "nguon": "envato"}) is True


def test_loai_tru_cung_bi_quet(tmp_path):
    """`loai_tru` (người bỏ) cũng không phải 'song' — cùng đường ra."""
    conn = _kho(tmp_path)
    _them(conn, "envato:bo", "envato", "loai_tru")
    assert mdung.clip_hong(conn, {"id": "envato:bo", "nguon": "envato"}) is True
