"""G2 parity — CÙNG thao tác sổ trên 2 lưng SQLite/Postgres phải cho CÙNG kết quả.

Lưng Postgres cần server test: đặt env AUTOEDIT_TEST_PG_URL trỏ 1 database RIÊNG
cho test (bảng bị TRUNCATE mỗi test — TUYỆT ĐỐI không trỏ sổ thật). Không đặt /
không kết nối được -> các ca pg SKIP, máy không có Postgres vẫn xanh nguyên suite.
Cố ý KHÔNG dùng AUTOEDIT_DB_URL cho test — tránh trỏ nhầm test vào sổ production.
"""

from __future__ import annotations

import os

import pytest

from autoedit.library import db
from autoedit.sourcer.usage import log_usage, times_used

PG_URL = os.environ.get("AUTOEDIT_TEST_PG_URL", "").strip()


def _pg_available() -> bool:
    if not PG_URL:
        return False
    try:
        db.connect(db_url=PG_URL).close()
        return True
    except Exception:
        return False


PG_OK = _pg_available()
_TABLES = ("library_assets", "asset_usage", "search_cache", "stock_tags")


@pytest.fixture(params=[
    "sqlite",
    pytest.param("pg", marks=pytest.mark.skipif(
        not PG_OK, reason="AUTOEDIT_TEST_PG_URL chưa đặt / không kết nối được")),
])
def conn(request, tmp_path):
    if request.param == "sqlite":
        c = db.connect(tmp_path / "cache.db")
    else:
        c = db.connect(db_url=PG_URL)
        # db test riêng — dọn sạch + reset id để tie-break dự đoán được
        c.execute(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY")
    yield c
    c.close()


def _rec(path: str, subject: str = "spiral galaxy", niche: str = "space",
         mtime: float = 1.0, mood: str = "epic", category: str = "nap",
         media_type: str = "video", has_people: bool = False,
         source_class: str = "own") -> db.AssetRecord:
    return db.AssetRecord(
        niche=niche, path=path, category=category, media_type=media_type,
        mtime=mtime, subject=subject, description="deep space nebula",
        shot_size="wide", mood=mood, scene_type="space", has_people=has_people,
        tags=["galaxy", "stars"], source_class=source_class)


def test_search_vietnamese_lower(conn):
    """§8.3: lower() Unicode — SQLite cắm hàm Python, Postgres phải chuẩn sẵn.
    'TƯ TRỊ' hoa phải khớp query 'tư trị' thường (và ngược lại) trên CẢ 2 lưng."""
    db.upsert_asset(conn, _rec("/lib/vn.mp4", subject="TƯ TRỊ SÂU THẲM"))
    assert [r["path"] for r in db.search_assets(conn, "space", "tư trị")] == ["/lib/vn.mp4"]
    # query viết hoa: term hạ chữ phía Python (backend-independent)
    assert [r["path"] for r in db.search_assets(conn, "space", "TƯ TRỊ")] == ["/lib/vn.mp4"]
    # không khớp bậy
    assert db.search_assets(conn, "space", "tự trị") == []


def test_upsert_twice_updates_not_duplicates(conn):
    """ON CONFLICT(path): upsert lại cùng path = update, không thêm dòng."""
    db.upsert_asset(conn, _rec("/lib/a.mp4", mood="epic"))
    db.upsert_asset(conn, _rec("/lib/a.mp4", mood="calm"))
    assert db.count_assets(conn, "space") == 1
    assert db.search_assets(conn, "space", "galaxy")[0]["mood"] == "calm"


def test_needs_index_mtime_precision(conn):
    """mtime epoch ~1.7e9 + phần lẻ µs: REAL 4-byte của PG mất phần lẻ -> tag lại
    oan cả kho. Schema PG phải là DOUBLE PRECISION để so 1e-6 vẫn đúng."""
    mt = 1752537600.123456
    db.upsert_asset(conn, _rec("/lib/mt.mp4", mtime=mt))
    assert db.needs_index(conn, "/lib/mt.mp4", mt) is False
    assert db.needs_index(conn, "/lib/mt.mp4", mt + 1.0) is True
    assert db.needs_index(conn, "/lib/chua-co.mp4", mt) is True


def test_usage_write_then_read(conn):
    """§8.5 autocommit: sqlite3 commit tường minh vs psycopg autocommit — ghi xong
    đọc lại NGAY trong cùng conn phải thấy, đếm đúng."""
    log_usage(conn, "kenh-a", "local:/lib/a.mp4", "vid-1")
    log_usage(conn, "kenh-a", "local:/lib/a.mp4", "vid-2")
    assert times_used(conn, "kenh-a", "local:/lib/a.mp4") == 2
    assert times_used(conn, "kenh-b", "local:/lib/a.mp4") == 0


def test_search_cache_upsert(conn):
    """Khuôn ON CONFLICT của search_cache (pexels/entity sau khi bỏ INSERT OR
    REPLACE): ghi đè cùng (provider, query) = update, 1 dòng."""
    sql = ("INSERT INTO search_cache (provider, query, response, cached_at) "
           "VALUES ('pexels', ?, ?, ?) ON CONFLICT(provider, query) DO UPDATE SET "
           "response=excluded.response, cached_at=excluded.cached_at")
    conn.execute(sql, ("shark", '{"v":1}', "t1"))
    conn.execute(sql, ("shark", '{"v":2}', "t2"))
    conn.commit()
    rows = conn.execute(
        "SELECT response, cached_at FROM search_cache WHERE provider='pexels' AND query=?",
        ("shark",)).fetchall()
    assert len(rows) == 1
    assert rows[0]["response"] == '{"v":2}' and rows[0]["cached_at"] == "t2"


def test_order_tiebreak_id_desc(conn):
    """§8.6: hòa (approved, indexed_at) -> id DESC tường minh, 2 lưng cùng thứ tự
    (mới-nạp-đứng-trước) — pick không đổi sau flip Postgres."""
    for p in ("/lib/t1.mp4", "/lib/t2.mp4", "/lib/t3.mp4"):
        db.upsert_asset(conn, _rec(p))
    conn.execute("UPDATE library_assets SET indexed_at = ?", ("2026-01-01T00:00:00",))
    conn.commit()
    order = [r["path"] for r in db.search_assets(conn, "space", "galaxy")]
    assert order == ["/lib/t3.mp4", "/lib/t2.mp4", "/lib/t1.mp4"]
    assert [r["path"] for r in db.videos_for_niche(conn, "space")] == order


def test_search_filters_and_exclude(conn):
    """Nhánh exclude_paths (duyệt cursor không LIMIT) + own_only + no_people
    (COALESCE) chạy giống nhau 2 lưng."""
    db.upsert_asset(conn, _rec("/lib/f1.mp4"))
    db.upsert_asset(conn, _rec("/lib/f2.mp4", has_people=True))
    db.upsert_asset(conn, _rec("/lib/f3.mp4", source_class="viral"))
    got = [r["path"] for r in db.search_assets(
        conn, "space", "galaxy", exclude_paths={"/lib/f3.mp4"})]
    assert got == ["/lib/f2.mp4", "/lib/f1.mp4"]
    assert [r["path"] for r in db.search_assets(conn, "space", "galaxy", no_people=True,
                                                own_only=True)] == ["/lib/f1.mp4"]


def test_move_delete_count(conn):
    """move_asset (UPDATE), delete_assets (executemany), count_assets."""
    db.upsert_asset(conn, _rec("/lib/m1.mp4"))
    db.upsert_asset(conn, _rec("/lib/m2.mp4"))
    db.move_asset(conn, "/lib/m1.mp4", "/lib/moi/m1.mp4", "signature", "signature")
    assert "/lib/moi/m1.mp4" in db.paths_for_niche(conn, "space")
    sig = db.signature_assets(conn, "space")
    assert [r["path"] for r in sig] == ["/lib/moi/m1.mp4"]
    assert db.delete_assets(conn, ["/lib/moi/m1.mp4", "/lib/m2.mp4"]) == 2
    assert db.count_assets(conn, "space") == 0


def test_ref_prefix_windows_backslash(conn, tmp_path):
    """Regression 2026-07-17: prefix --ref là path Windows `f:\\...` — bản LIKE cũ trên
    Postgres coi `\\` là ký tự ESCAPE của pattern -> match hụt, REF chạy RỖNG im lặng
    (SQLite không escape mặc định nên không lộ; test cũ dùng `F:/` càng không lộ).
    Fix substr: không pattern language, 2 lưng hành xử y nhau."""
    from autoedit.project import SearchQueries
    from autoedit.sourcer.local import find_ref_candidates

    f = tmp_path / "clip.mp4"
    f.write_bytes(b"v")
    rec = _rec(str(f), subject="spacecraft assembly cleanroom", source_class="viral")
    rec.source_video = r"F:\VIDEO MAU\SP1\a.mp4"
    rec.source_duration = 600.0
    rec.scene_index = 1
    rec.source_channel = "Astrum"
    db.upsert_asset(conn, rec)
    out = find_ref_candidates(conn, "space", (r"f:\video mau\sp1",),
                              SearchQueries(specific=["spacecraft assembly"]))
    assert [c["path"] for c in out] == [str(f)]
    # VD4: cột kênh nguồn phải lên ứng viên (chống vết PB7 cột-rơi)
    assert out[0]["source_channel"] == "Astrum"


def test_ref_chapter_scan_windows_backslash(conn, tmp_path):
    """VD2 REF theo chương: ref_chapter_scan dùng substr (không LIKE) — path Windows
    `f:\\...\\Chapter N\\...` phải ra map y nhau trên CẢ 2 lưng (vết LIKE-PG escape)."""
    from autoedit.sourcer.local import ref_chapter_scan

    f = tmp_path / "clip2.mp4"
    f.write_bytes(b"v")
    rec = _rec(str(f), subject="old town market", source_class="viral")
    rec.source_video = r"F:\VIDEO MAU\AMZ\Chapter 2\b.mp4"
    rec.source_duration = 600.0
    rec.scene_index = 1
    db.upsert_asset(conn, rec)
    mapping, counts = ref_chapter_scan(conn, "space", (r"f:\video mau\amz",))
    assert mapping == {2: ("f:\\video mau\\amz\\chapter 2\\",)}
    assert counts == {2: 1}


def test_source_channel_preserve_and_backfill(conn):
    """VD4 ghi công: (a) channel-set backfill so prefix ở PYTHON (né LIKE) + dry-run
    không ghi; (b) luật preserve — upsert source_channel RỖNG (resume/retag không
    --channel) GIỮ kênh backfill, giá trị mới đè được; (c) channel-audit gom folder."""
    r1 = _rec("/lib/c1.mp4")
    r1.source_video = r"F:\MAU\SP\a.mp4"
    r2 = _rec("/lib/c2.mp4")
    r2.source_video = r"F:\MAU\SP\b.mp4"
    r3 = _rec("/lib/c3.mp4")
    r3.source_video = r"E:\KHAC\c.mp4"
    for r in (r1, r2, r3):
        db.upsert_asset(conn, r)

    assert db.set_source_channel(conn, r"f:\mau\sp", "Astrum", dry_run=True) == 2
    assert conn.execute("SELECT source_channel FROM library_assets WHERE path = ?",
                        ("/lib/c1.mp4",)).fetchone()["source_channel"] == ""  # dry-run
    assert db.set_source_channel(conn, r"f:\mau\sp", "Astrum") == 2
    assert db.set_source_channel(conn, r"f:\mau\sp", "Astrum", niche="khac") == 0
    rows = {r["path"]: r["source_channel"] for r in conn.execute(
        "SELECT path, source_channel FROM library_assets")}
    assert rows == {"/lib/c1.mp4": "Astrum", "/lib/c2.mp4": "Astrum", "/lib/c3.mp4": ""}

    db.upsert_asset(conn, r1)  # re-upsert extra rỗng (resume) -> GIỮ kênh
    assert conn.execute("SELECT source_channel FROM library_assets WHERE path = ?",
                        ("/lib/c1.mp4",)).fetchone()["source_channel"] == "Astrum"
    r1.source_channel = "Kenh Moi"  # khai lại tường minh -> đè
    db.upsert_asset(conn, r1)
    assert conn.execute("SELECT source_channel FROM library_assets WHERE path = ?",
                        ("/lib/c1.mp4",)).fetchone()["source_channel"] == "Kenh Moi"

    from pathlib import Path as _P
    groups = {g["folder"]: g for g in db.source_video_folders(conn, niche="space")}
    mau = groups[str(_P(r"F:\MAU\SP\a.mp4").parent)]
    assert mau["assets"] == 2 and mau["channels"] == ["Astrum", "Kenh Moi"]
    khac = groups[str(_P(r"E:\KHAC\c.mp4").parent)]
    assert khac["channels"] == [""]  # chưa điền -> audit phải lộ ra


def test_connect_explicit_path_ignores_db_url(tmp_path, monkeypatch):
    """Chốt an toàn flip: db_path tường minh LUÔN được SQLite — máy đã trỏ Postgres
    (env/machine.json) không kéo 531 test cũ + script di trú sang sổ thật."""
    monkeypatch.setenv("AUTOEDIT_DB_URL", "postgresql://khong-ton-tai:1/x")
    c = db.connect(tmp_path / "x.db")  # không nổ kết nối = không nhìn env
    assert c.execute("SELECT 1").fetchone() is not None
    c.close()
