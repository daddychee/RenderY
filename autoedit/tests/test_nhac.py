# -*- coding: utf-8 -*-
"""Kho nhạc Epidemic + đường âm lượng — theo bộ tiêu chí user duyệt 06/09."""
import pathlib
import tempfile

import pytest

from autoedit.offline.nhac_mix import cat_lap, duong_am_luong
from autoedit.sotra import db as sdb, nhac


@pytest.fixture
def conn():
    return sdb.mo(pathlib.Path(tempfile.mkdtemp()) / "t.db")


def _track(i=1, **d):
    """Track JSON theo đúng khuôn Epidemic đo được 06/09."""
    goc = {"id": i, "title": f"Track {i}", "length": 195, "bpm": 90,
           "energyLevel": "medium", "hasVocals": False, "isSfx": False,
           "publicSlug": "x",
           "moods": [{"displayTag": "Suspense"}, {"displayTag": "Dark"}],
           "genres": [{"displayTag": "Minimalism"}],
           "creatives": {"mainArtists": [{"name": "A"}]},
           "stems": {"full": {"lqMp3Url": "https://cdn/x.mp3"}}}
    goc.update(d)
    return goc


def test_parse_track_quy_mood_noi_bo():
    r = nhac.parse_track(_track())
    assert r["id"] == "epidemic:1"
    assert r["mood"] == "tense"                    # Suspense -> vocab nội bộ
    assert r["mood_goc"] == "suspense, dark"       # gốc giữ nguyên, không mất tin
    assert r["url_nghe"] == "https://cdn/x.mp3" and r["bpm"] == 90


def test_sfx_khong_vao_kho_nhac():
    assert nhac.parse_track(_track(isSfx=True)) is None


def test_hut_upsert_khong_trung(conn):
    tai = lambda url: {"entities": {"tracks": {"1": _track(1), "2": _track(2)}}}
    assert nhac.hut_epidemic(conn, moods="suspense", so_trang=1, tai=tai) == 2
    assert nhac.hut_epidemic(conn, moods="suspense", so_trang=1, tai=tai) == 0
    assert conn.execute("SELECT COUNT(*) FROM nhac").fetchone()[0] == 2


def test_de_xuat_cham_diem_va_ly_do(conn):
    nhac.them_nhac(conn, nhac.parse_track(_track(1)))                    # tense/medium/90
    nhac.them_nhac(conn, nhac.parse_track(
        _track(2, moods=[{"displayTag": "Dreamy"}], energyLevel="low", bpm=60)))
    conn.commit()
    dx = nhac.de_xuat(conn, mood="tense", energy="medium", bpm_muc_tieu=90)
    assert dx[0]["id"] == "epidemic:1" and dx[0]["diem"] > dx[1]["diem"]
    assert "tense" in dx[0]["ly_do"]               # editor thấy VÌ SAO máy đưa


def test_co_loi_bi_chan_mac_dinh(conn):
    nhac.them_nhac(conn, nhac.parse_track(_track(1, hasVocals=True)))
    conn.commit()
    assert nhac.de_xuat(conn, mood="tense") == []
    assert len(nhac.de_xuat(conn, mood="tense", cho_phep_loi=True)) == 1


def test_chong_lap_track_da_len_final(conn):
    nhac.them_nhac(conn, nhac.parse_track(_track(1)))
    conn.execute("INSERT INTO su_kien(clip_id, tap, loai) VALUES(?,?,?)",
                 ("epidemic:1", "LI099", "len_final"))
    conn.commit()
    dx = nhac.de_xuat(conn, mood="tense", kenh="LI")
    assert "đã dùng" in dx[0]["ly_do"] and dx[0]["diem"] < 10


# ---------------------------------------------------------- đường âm lượng
def test_ducking_ha_truoc_cau_nha_sau_cau():
    khoi = [{"v0": 5.0, "v1": 9.0, "tho": 8.0, "tho_them": 0.0}]
    kf = duong_am_luong(khoi)
    d = dict(kf)
    assert d[0.0] == 0.9                           # mở chương nhạc to
    assert d[4.7] == 0.9 and d[5.0] == 0.25        # hạ 0.3s trước câu
    assert d[9.0] == 0.25 and d[9.4] == 0.9        # nhả 0.4s sau câu


def test_tho_ngan_khong_nhap_nho():
    """2 câu cách nhau 0.5s: nhạc GIỮ THẤP, không kịp lên rồi xuống."""
    khoi = [{"v0": 0.0, "v1": 4.0, "tho": 0.5, "tho_them": 0.0},
            {"v0": 4.5, "v1": 8.0, "tho": 2.0, "tho_them": 0.0}]
    kf = duong_am_luong(khoi)
    giua = [v for t, v in kf if 4.0 < t < 4.5]
    assert not any(v == 0.9 for v in giua), "không được nhô lên trong khe 0.5s"


def test_ducking_tinh_tren_truc_timeline_co_tho_them():
    """tho_them dịch mốc voice -> keyframe phải theo trục TIMELINE, không phải audio."""
    khoi = [{"v0": 0.0, "v1": 3.0, "tho": 1.0, "tho_them": 2.0},
            {"v0": 4.0, "v1": 7.0, "tho": 0.0, "tho_them": 0.0}]
    d = dict(duong_am_luong(khoi))
    assert d[6.0] == 0.25                          # câu 2 vào tại 4+2=6 trên timeline


def test_cat_lap_track_ngan_hon_chuong():
    ra = cat_lap(dai_nhac_s=195.0, dai_chuong_s=400.0)
    assert ra == [(0.0, 195.0), (195.0, 195.0), (390.0, 10.0)]
    assert cat_lap(200.0, 150.0) == [(0.0, 150.0)]  # track dài hơn: cắt cụt
    assert cat_lap(0, 100) == []


# ---------------------------------------------------------- API
def test_api_nhac_de_xuat_va_chon(tmp_path, monkeypatch):
    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    import json as _json

    from fastapi.testclient import TestClient

    from autoedit.offline import runner as orun
    from autoedit.web import server

    # hợp đồng giả có mood + framing
    d = tmp_path / "proj"
    d.mkdir()
    hd = {"ma_tap": "LI100", "nguoi_tao": "", "offset": 0, "khoi": [
        {"v0": 0, "v1": 4, "tho": 1, "tho_them": 0, "mood": "tense"},
        {"v0": 5, "v1": 9, "tho": 0, "tho_them": 0, "mood": "tense"}],
        "hinh": [], "framing": {"than": 3.0}}
    (d / "offline.json").write_text(_json.dumps(hd), encoding="utf-8")
    monkeypatch.setattr(server, "PROJECTS_DIR", tmp_path)

    c = sdb.mo()
    nhac.them_nhac(c, nhac.parse_track(_track(1)))       # tense/medium/90
    c.commit()
    c.close()
    # chặn nhánh "kho mỏng -> tự hút": test không được chạm mạng thật
    monkeypatch.setattr(nhac, "hut_epidemic", lambda *a, **k: 0)
    tc = TestClient(server.app)
    r = tc.get("/api/offline/proj/nhac")
    assert r.status_code == 200
    j = r.json()
    assert j["mood"] == "tense" and j["energy"] == "high"   # thân 3.0s -> high
    assert j["tracks"][0]["id"] == "epidemic:1"

    r = tc.post("/api/offline/proj/nhac/chon", json={"id": "epidemic:1"})
    assert r.status_code == 200 and r.json()["nhac"]["tieu_de"] == "Track 1"
    hd2 = orun.doc(d)
    assert hd2["nhac"]["id"] == "epidemic:1"
    # sự kiện duoc_chon đã ghi (vòng phản biện dùng sau)
    c = sdb.mo()
    assert c.execute("SELECT COUNT(*) FROM su_kien WHERE clip_id='epidemic:1' "
                     "AND loai='duoc_chon'").fetchone()[0] == 1
    c.close()
    # bỏ nhạc
    r = tc.post("/api/offline/proj/nhac/chon", json={"id": ""})
    assert r.status_code == 200 and orun.doc(d).get("nhac") is None


def test_quy_mood_chuong_chu_tu_do():
    """Bug 06/09: chương ra mood "sober" (GLM tả tự do) — không quy đổi được
    thì không hút nổi track nào, modal trống."""
    assert nhac.quy_mood_chuong("sober") == "tense"
    assert nhac.quy_mood_chuong("Somber") == "sad"
    assert nhac.quy_mood_chuong("tense") == "tense"
    assert nhac.quy_mood_chuong("weird-mood") == "weird-mood"   # lạ: giữ nguyên
