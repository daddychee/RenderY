"""Test nguồn Pixabay + MultiStockClient (RenderY) — fake HTTP, không gọi mạng.

Pixabay là nguồn free thứ hai, chạy bù khi Pexels nghèo ứng viên hoặc hết hạn mức.
Test khoá: parse đúng shape API Pixabay, lọc landscape, cache theo provider,
xoay key khi 429, và luật ưu tiên nguồn của MultiStockClient.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoedit.library import db
from autoedit.project import SearchQueries
from autoedit.sourcer.pixabay import (
    MultiStockClient,
    PixabayClient,
    _pick_video_file,
    collect_pixabay_keys,
)


@pytest.fixture
def conn(tmp_path):
    return db.connect(tmp_path / "cache.db")


def _hit(hid: int, w: int = 1920, h: int = 1080, dur: int = 12) -> dict:
    return {
        "id": hid,
        "duration": dur,
        "pageURL": f"https://pixabay.com/videos/id-{hid}/",
        "videos": {
            "large": {"url": f"https://cdn/{hid}_large.mp4", "width": w, "height": h},
            "medium": {"url": f"https://cdn/{hid}_med.mp4", "width": w // 2, "height": h // 2},
        },
    }


class _FakeResp:
    def __init__(self, payload=None, status=200):
        self._payload = payload if payload is not None else {"hits": []}
        self.status_code = status
        self.ok = status == 200

    def json(self):
        return self._payload


# ---------------------------- _pick_video_file ------------------------------
def test_chon_ban_gan_1080p():
    hit = {"videos": {
        "tiny": {"url": "t", "width": 640, "height": 360},
        "large": {"url": "l", "width": 1920, "height": 1080},
        "huge": {"url": "h", "width": 3840, "height": 2160},
    }}
    assert _pick_video_file(hit)["url"] == "l"


def test_loai_clip_doc_va_vuong():
    """Timeline 16:9 — clip dọc/vuông bị loại ngay từ khâu chọn file."""
    assert _pick_video_file({"videos": {"a": {"url": "a", "width": 1080, "height": 1920}}}) is None
    assert _pick_video_file({"videos": {"a": {"url": "a", "width": 1080, "height": 1080}}}) is None


def test_thieu_field_khong_no():
    assert _pick_video_file({}) is None
    assert _pick_video_file({"videos": {"a": {"width": 100}}}) is None


# ------------------------------ search --------------------------------------
def test_search_tra_ve_candidate_dung_shape(monkeypatch, conn):
    client = PixabayClient(["k1"], conn=conn)
    monkeypatch.setattr(client, "_http_get", lambda q: {"hits": [_hit(77)]})

    got = client.search_tiered(SearchQueries(specific=["ocean wave"]))

    assert len(got) == 1
    c = got[0]
    assert c["asset_key"] == "pixabay:77"       # sổ nguồn gốc: truy ngược được clip
    assert c["source"] == "pixabay"
    assert c["url"] == "https://cdn/77_large.mp4"
    assert c["media_type"] == "video"
    assert c["duration"] == 12.0
    assert (c["width"], c["height"]) == (1920, 1080)


def test_khong_trung_lap_giua_cac_tier(monkeypatch, conn):
    client = PixabayClient(["k1"], conn=conn)
    monkeypatch.setattr(client, "_http_get", lambda q: {"hits": [_hit(1)]})
    got = client.search_tiered(SearchQueries(specific=["a"], broad=["b"], thematic=["c"]))
    assert len(got) == 1


def test_cache_theo_provider_khong_dam_pexels(monkeypatch, conn):
    """Pexels và Pixabay dùng chung bảng cache -> phải tách bằng cột provider."""
    conn.execute(
        "INSERT INTO search_cache (provider, query, response, cached_at) "
        "VALUES ('pexels', 'sea', ?, '2026-01-01')", ('{"videos": []}',))
    conn.commit()

    client = PixabayClient(["k1"], conn=conn)
    monkeypatch.setattr(client, "_http_get", lambda q: {"hits": [_hit(5)]})
    got = client.search_tiered(SearchQueries(specific=["sea"]))

    assert [c["asset_key"] for c in got] == ["pixabay:5"]  # không đọc nhầm cache pexels
    row = conn.execute(
        "SELECT response FROM search_cache WHERE provider='pixabay' AND query='sea'"
    ).fetchone()
    assert row is not None  # đã ghi cache riêng


def test_lan_hai_doc_cache_khong_goi_mang(monkeypatch, conn):
    client = PixabayClient(["k1"], conn=conn)
    calls = []
    monkeypatch.setattr(client, "_http_get", lambda q: (calls.append(q), {"hits": [_hit(9)]})[1])
    client.search_tiered(SearchQueries(specific=["reef"]))
    client.search_tiered(SearchQueries(specific=["reef"]))
    assert len(calls) == 1


# ------------------------------ xoay key ------------------------------------
def test_429_chuyen_sang_key_sau(monkeypatch, conn):
    client = PixabayClient(["k1", "k2"], conn=conn)
    seen = []

    def fake_get(url, params, timeout):
        seen.append(params["key"])
        return _FakeResp(status=429) if params["key"] == "k1" else _FakeResp({"hits": [_hit(3)]})

    monkeypatch.setattr("autoedit.sourcer.pixabay.requests.get", fake_get)
    assert client._http_get("x") == {"hits": [_hit(3)]}
    assert seen == ["k1", "k2"]
    assert 0 in client.exhausted


def test_moi_key_het_han_muc_tra_none(monkeypatch, conn):
    """Trả None -> caller bật rate_limited, ngừng gọi mạng phần còn lại run."""
    client = PixabayClient(["k1"], conn=conn)
    monkeypatch.setattr("autoedit.sourcer.pixabay.requests.get",
                        lambda url, params, timeout: _FakeResp(status=429))
    assert client._http_get("x") is None

    monkeypatch.setattr(client, "_http_get", lambda q: None)
    assert client.search_tiered(SearchQueries(specific=["x"])) == []
    assert client.rate_limited is True


def test_loi_mang_khong_giet_stage(monkeypatch, conn):
    import requests as _rq
    client = PixabayClient(["k1"], conn=conn)

    def boom(url, params, timeout):
        raise _rq.RequestException("mạng chập")

    monkeypatch.setattr("autoedit.sourcer.pixabay.requests.get", boom)
    assert client._http_get("x") == {}       # rỗng, KHÔNG raise
    assert client.rate_limited is False      # không nhầm là hết hạn mức


# --------------------------- MultiStockClient -------------------------------
class _FakeStock:
    def __init__(self, name, items, rate_limited=False):
        self.SOURCE_NAME = name
        self.items = items
        self.rate_limited = rate_limited
        self.downloaded = []

    def search_tiered(self, queries):
        return list(self.items)

    def download(self, candidate, dest):
        self.downloaded.append(candidate["asset_key"])
        return dest


def _cand(src, i):
    return {"asset_key": f"{src}:{i}", "source": src, "url": f"u{i}"}


def test_nguon_sau_chay_khi_nguon_truoc_ngheo():
    a = _FakeStock("pexels", [_cand("pexels", 1)])
    b = _FakeStock("pixabay", [_cand("pixabay", 2)])
    got = MultiStockClient([a, b]).search_tiered(SearchQueries(specific=["x"]))
    assert [c["asset_key"] for c in got] == ["pexels:1", "pixabay:2"]


def test_nguon_truoc_du_giau_thi_bo_qua_nguon_sau():
    """Đủ MIN_CANDIDATES_PER_TIER (5) -> khỏi gọi nguồn sau, tiết kiệm hạn mức."""
    a = _FakeStock("pexels", [_cand("pexels", i) for i in range(5)])
    b = _FakeStock("pixabay", [_cand("pixabay", 9)])
    got = MultiStockClient([a, b]).search_tiered(SearchQueries(specific=["x"]))
    assert len(got) == 5
    assert all(c["source"] == "pexels" for c in got)


def test_download_dinh_tuyen_dung_nguon(tmp_path):
    a = _FakeStock("pexels", [])
    b = _FakeStock("pixabay", [])
    multi = MultiStockClient([a, b])
    multi.download(_cand("pixabay", 7), tmp_path / "x.mp4")
    assert a.downloaded == [] and b.downloaded == ["pixabay:7"]


def test_rate_limited_chi_khi_moi_nguon_het():
    a = _FakeStock("pexels", [], rate_limited=True)
    b = _FakeStock("pixabay", [], rate_limited=False)
    assert MultiStockClient([a, b]).rate_limited is False
    b.rate_limited = True
    assert MultiStockClient([a, b]).rate_limited is True


def test_khong_co_client_bao_loi():
    with pytest.raises(ValueError):
        MultiStockClient([])


def test_close_dong_client_giu_tai_nguyen():
    """Nguồn subscription giữ cửa sổ trình duyệt — phải đóng khi xong stage."""
    closed = []

    class _WithClose(_FakeStock):
        def close(self):
            closed.append(self.SOURCE_NAME)

    a = _FakeStock("pexels", [])                 # API thuần, không có close()
    b = _WithClose("envato", [])
    MultiStockClient([a, b]).close()
    assert closed == ["envato"]


def test_close_mot_client_loi_van_dong_cac_client_con_lai():
    closed = []

    class _Boom(_FakeStock):
        def close(self): raise RuntimeError("trình duyệt treo")

    class _Ok(_FakeStock):
        def close(self): closed.append(self.SOURCE_NAME)

    MultiStockClient([_Boom("envato", []), _Ok("vecteezy", [])]).close()
    assert closed == ["vecteezy"]


# ------------------------------ collect keys --------------------------------
def test_gom_key_nhieu_kieu_khai():
    env = {"PIXABAY_API_KEY": "k1, k2", "PIXABAY_API_KEY_2": "k3", "PIXABAY_API_KEY_3": "k1"}
    assert collect_pixabay_keys(env) == ["k1", "k2", "k3"]  # khử trùng, giữ thứ tự


def test_khong_khai_key_tra_rong():
    assert collect_pixabay_keys({}) == []
