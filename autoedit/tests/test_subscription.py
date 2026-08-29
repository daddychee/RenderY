"""Test nguồn subscription (Envato/Vecteezy) — không mở trình duyệt thật.

Trọng tâm là PHANH: user chốt "tự động nhưng có phanh" vì tải dồn dập dễ bị coi là
bot, mà hậu quả là mất tài khoản đang trả tiền. Test khoá 4 lớp phanh:
trần clip/giờ, nghỉ ngẫu nhiên, dừng ngay khi gặp challenge, dừng khi fail liên tiếp.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoedit.sourcer.subscription import (
    MAX_PER_HOUR,
    MIN_VIDEO_BYTES,
    SITES,
    BlockedError,
    RateLimiter,
    RateLimitError,
    SubscriptionClient,
    available_sites,
    profile_exists,
    search_url,
)


# ------------------------------ RateLimiter ---------------------------------
def test_duoi_tran_thi_qua():
    rl = RateLimiter(max_per_hour=3)
    for _ in range(2):
        rl.check(now=100.0)
        rl.record(now=100.0)
    rl.check(now=100.0)   # lần thứ 3 vẫn dưới trần


def test_cham_tran_thi_chan():
    rl = RateLimiter(max_per_hour=2)
    rl.record(now=100.0)
    rl.record(now=100.0)
    with pytest.raises(RateLimitError, match="2 clip/giờ"):
        rl.check(now=100.0)


def test_cua_so_truot_nha_dan_khong_reset_cuc():
    """Sau 1 giờ các mốc cũ rụng dần -> không bị dồn cục đầu giờ như reset theo giờ tròn."""
    rl = RateLimiter(max_per_hour=2)
    rl.record(now=0.0)
    rl.record(now=10.0)
    with pytest.raises(RateLimitError):
        rl.check(now=100.0)
    rl.check(now=3601.0)      # mốc t=0 đã quá 1 giờ -> nhả 1 suất
    assert rl.used <= 2


def test_nghi_ngau_nhien_khong_deu():
    """Nhịp đều đặn là dấu hiệu bot rõ nhất -> phải ngẫu nhiên."""
    slept: list[float] = []
    rl = RateLimiter(pause_range=(1.0, 5.0))
    for _ in range(20):
        rl.pause(sleep=slept.append)
    assert all(1.0 <= s <= 5.0 for s in slept)
    assert len(set(slept)) > 1        # không phải hằng số


def test_mac_dinh_co_tran():
    assert RateLimiter().max_per_hour == MAX_PER_HOUR > 0


# ------------------------------ search_url ----------------------------------
def test_link_search_encode_dung():
    url = search_url("envato", "ancient rome ruins")
    assert "ancient+rome+ruins" in url and url.startswith("https://elements.envato.com")


def test_link_search_giu_loc_ngang_cua_envato():
    assert "orientation=horizontal" in search_url("envato", "x")


def test_nguon_la_bao_loi():
    with pytest.raises(ValueError, match="Nguồn lạ"):
        search_url("artlist", "x")   # Artlist đã bỏ khỏi RenderY


def test_moi_site_deu_co_du_cau_hinh():
    for site, cfg in SITES.items():
        assert {"search", "login", "env"} <= set(cfg)
        assert "{q}" in cfg["search"]


# ------------------------------ profile -------------------------------------
def test_profile_rong_coi_nhu_chua_login(tmp_path):
    (tmp_path / ".browser_profiles" / "envato").mkdir(parents=True)
    assert profile_exists("envato", tmp_path) is False


def test_profile_co_du_lieu_la_da_login(tmp_path):
    d = tmp_path / ".browser_profiles" / "envato"
    d.mkdir(parents=True)
    (d / "Cookies").write_bytes(b"x")
    assert profile_exists("envato", tmp_path) is True


def test_available_can_ca_email_va_profile(tmp_path):
    d = tmp_path / ".browser_profiles" / "envato"
    d.mkdir(parents=True)
    (d / "Cookies").write_bytes(b"x")

    # có profile nhưng chưa khai email -> chưa dùng được
    assert available_sites({}, tmp_path) == []
    assert available_sites({"ENVATO_EMAIL": "a@b.c"}, tmp_path) == ["envato"]
    # khai email nguồn chưa login -> vẫn không có
    assert available_sites({"VECTEEZY_EMAIL": "a@b.c"}, tmp_path) == []


# --------------------------- SubscriptionClient -----------------------------
def test_khoi_tao_nguon_la_bao_loi():
    with pytest.raises(ValueError):
        SubscriptionClient("artlist")


def test_source_name_de_dinh_tuyen_download():
    assert SubscriptionClient("envato").SOURCE_NAME == "envato"


def test_blocked_thi_moi_lan_goi_sau_deu_dung_ngay(tmp_path):
    """Gặp challenge = dừng hẳn. Thử lại chỉ tự tố cáo thêm."""
    c = SubscriptionClient("envato", profiles_root=tmp_path)
    c.blocked = True
    with pytest.raises(BlockedError, match="đã dừng phiên"):
        c.download("https://elements.envato.com/x", tmp_path / "a.mp4")


def test_cham_tran_thi_khong_mo_trinh_duyet(tmp_path):
    """Phanh chặn TRƯỚC khi mở trang — không tốn một request nào."""
    rl = RateLimiter(max_per_hour=1)
    rl.record()
    c = SubscriptionClient("envato", profiles_root=tmp_path, limiter=rl)
    c._context = lambda: pytest.fail("không được mở trình duyệt khi đã chạm trần")
    with pytest.raises(RateLimitError):
        c.download("https://elements.envato.com/x", tmp_path / "a.mp4")


def test_fail_lien_tiep_thi_dung_nguon(tmp_path, monkeypatch):
    """3 lần hỏng liên tiếp -> nghi bị chặn mềm -> dừng, đừng cố thêm."""
    c = SubscriptionClient("envato", profiles_root=tmp_path)

    class _Page:
        def goto(self, *a, **k): pass
        def title(self): return "ok"
        def query_selector(self, sel): return None
        def close(self): pass
        def wait_for_timeout(self, ms): pass
        def expect_download(self, timeout=None): raise RuntimeError("nút đâu")

    monkeypatch.setattr(c, "_context", lambda: type("C", (), {"new_page": lambda s: _Page()})())

    for _ in range(2):
        with pytest.raises(RuntimeError):
            c.download("https://x", tmp_path / "a.mp4")
    assert c.blocked is False
    with pytest.raises(BlockedError, match="liên tiếp"):
        c.download("https://x", tmp_path / "a.mp4")
    assert c.blocked is True


def test_gap_challenge_dung_ngay_va_dong_nguon(tmp_path, monkeypatch):
    c = SubscriptionClient("envato", profiles_root=tmp_path)

    class _Page:
        def goto(self, *a, **k): pass
        def title(self): return "Just a moment..."
        def query_selector(self, sel): return None
        def close(self): pass

    monkeypatch.setattr(c, "_context", lambda: type("C", (), {"new_page": lambda s: _Page()})())
    with pytest.raises(BlockedError, match="captcha"):
        c.download("https://x", tmp_path / "a.mp4")
    assert c.blocked is True


def test_search_tra_ve_candidate_dung_shape(tmp_path, monkeypatch):
    """Phải cùng shape với PexelsClient để MultiStockClient dùng chung."""
    from autoedit.project import SearchQueries

    c = SubscriptionClient("envato", profiles_root=tmp_path)
    monkeypatch.setattr(c, "_search_one", lambda q: [{
        "asset_key": "envato:abc123", "url": "https://elements.envato.com/x-abc123",
        "media_type": "video", "duration": 0.0, "width": 0, "height": 0,
        "description": "clip", "source": "envato",
    }])
    got = c.search_tiered(SearchQueries(specific=["rome"]))
    assert len(got) == 1 and got[0]["source"] == "envato"
    assert got[0]["asset_key"].startswith("envato:")


def test_search_khu_trung_giua_cac_tier(tmp_path, monkeypatch):
    from autoedit.project import SearchQueries

    c = SubscriptionClient("envato", profiles_root=tmp_path)
    monkeypatch.setattr(c, "_search_one", lambda q: [
        {"asset_key": "envato:same", "url": "u", "source": "envato"}])
    got = c.search_tiered(SearchQueries(specific=["a"], broad=["b"], thematic=["c"]))
    assert len(got) == 1


def test_search_1_query_hong_khong_giet_tier(tmp_path, monkeypatch):
    from autoedit.project import SearchQueries

    c = SubscriptionClient("envato", profiles_root=tmp_path)

    def flaky(q):
        if q == "xau":
            raise RuntimeError("selector đổi")
        return [{"asset_key": f"envato:{q}", "url": "u", "source": "envato"}]

    monkeypatch.setattr(c, "_search_one", flaky)
    got = c.search_tiered(SearchQueries(specific=["xau", "tot"]))
    assert [g["asset_key"] for g in got] == ["envato:tot"]


def test_search_gap_challenge_thi_dung_va_giu_ket_qua_da_co(tmp_path, monkeypatch):
    from autoedit.project import SearchQueries

    c = SubscriptionClient("envato", profiles_root=tmp_path)
    calls = []

    def block_sau_lan_dau(q):
        calls.append(q)
        if len(calls) == 1:
            return [{"asset_key": "envato:1", "url": "u", "source": "envato"}]
        raise BlockedError("challenge")

    monkeypatch.setattr(c, "_search_one", block_sau_lan_dau)
    got = c.search_tiered(SearchQueries(specific=["a", "b", "c"]))
    assert [g["asset_key"] for g in got] == ["envato:1"]   # giữ cái đã tìm được
    assert c.blocked is True
    assert len(calls) == 2                                  # dừng ngay, không thử "c"


def test_blocked_thi_search_tra_rong_ngay(tmp_path):
    from autoedit.project import SearchQueries

    c = SubscriptionClient("envato", profiles_root=tmp_path)
    c.blocked = True
    c._search_one = lambda q: pytest.fail("không được search khi đã bị chặn")
    assert c.search_tiered(SearchQueries(specific=["x"])) == []


def test_download_nhan_ca_dict_lan_url(tmp_path, monkeypatch):
    """Runner truyền dict candidate; gọi tay truyền URL trần."""
    c = SubscriptionClient("envato", profiles_root=tmp_path)
    seen = []

    class _Page:
        def goto(self, url, **k): seen.append(url)
        def title(self): return "Just a moment"   # dừng sớm, chỉ cần biết URL
        def query_selector(self, sel): return None
        def close(self): pass

    monkeypatch.setattr(c, "_context", lambda: type("C", (), {"new_page": lambda s: _Page()})())
    for arg in ({"url": "https://a"}, "https://b"):
        c.blocked = False
        with pytest.raises(BlockedError):
            c.download(arg, tmp_path / "x.mp4")
    assert seen == ["https://a", "https://b"]


def test_file_qua_nho_bi_xoa_va_bao_loi(tmp_path, monkeypatch):
    """Bị chặn hay dính bản preview đều ra file tí hon -> không được coi là thành công."""
    c = SubscriptionClient("envato", profiles_root=tmp_path)
    dest = tmp_path / "a.mp4"

    class _Info:
        value = type("D", (), {"save_as": staticmethod(lambda p: Path(p).write_bytes(b"x" * 10))})()

    class _Ctx:
        def __enter__(self): return _Info()
        def __exit__(self, *a): return False

    class _Page:
        def goto(self, *a, **k): pass
        def title(self): return "ok"

        def query_selector(self, sel):
            if "challenges.cloudflare.com" in sel:
                return None      # không bị chặn
            return type("B", (), {"click": lambda s: None})()

        def wait_for_timeout(self, ms): pass
        def expect_download(self, timeout=None): return _Ctx()
        def close(self): pass

    monkeypatch.setattr(c, "_context", lambda: type("C", (), {"new_page": lambda s: _Page()})())
    with pytest.raises(RuntimeError, match="quá nhỏ"):
        c.download("https://x", dest)
    assert not dest.exists()
    assert MIN_VIDEO_BYTES > 10
