"""Test lấy khoá API từ két OUTLIERY-V3 — không gọi mạng thật.

Luật V3: khoá do Owner nhập ở General › API Keys, app hỏi qua loopback, KHÔNG đọc
.env. Test khoá 3 thứ: đổi đúng tên biến theo nhà cung cấp, fail-open khi gateway
tắt (máy dev vẫn chạy được bằng .env), và KHÔNG BAO GIỜ lộ giá trị khoá ra ngoài.
"""

from __future__ import annotations

import pytest

from autoedit.web import ket_v3


@pytest.fixture(autouse=True)
def _sach(monkeypatch):
    """Xoá cache + biến môi trường giữa các test."""
    ket_v3._cache.update(luc=0.0, data={})
    for b in ("ANTHROPIC_API_KEY", "LLM_API_KEY", "LLM_PROVIDER", "L3_MODEL",
              "RANK_MODEL", "PEXELS_API_KEY", "PIXABAY_API_KEY", "SERPER_API_KEY"):
        monkeypatch.delenv(b, raising=False)


def _gia_ket(monkeypatch, data):
    monkeypatch.setattr(ket_v3, "doc_ket", lambda force=False: data)


def _muc(key="sk-x", nha="anthropic", model=""):
    return {"khoa": [{"id": "k1", "key": key, "loai": "llm", "nha": nha}],
            "che_do": "mot_khoa", "model": model}


# ------------------------------ đọc két -------------------------------------
def test_gateway_tat_thi_tra_rong(monkeypatch):
    """Fail-open: máy dev không có gateway vẫn chạy được bằng .env."""
    import requests

    def boom(*a, **k):
        raise requests.RequestException("gateway tắt")

    monkeypatch.setattr("requests.get", boom)
    assert ket_v3.doc_ket(force=True) == {}


def test_gateway_tra_loi_khong_lam_no(monkeypatch):
    class _R:
        ok = False

        @staticmethod
        def json():
            return {"loi": "chi loopback"}

    monkeypatch.setattr("requests.get", lambda *a, **k: _R())
    assert ket_v3.doc_ket(force=True) == {}


def test_cache_khong_goi_lai_trong_TTL(monkeypatch):
    goi = []

    class _R:
        ok = True

        @staticmethod
        def json():
            goi.append(1)
            return {"chia_beat": _muc()}

    monkeypatch.setattr("requests.get", lambda *a, **k: _R())
    ket_v3.doc_ket(force=True)
    ket_v3.doc_ket()
    ket_v3.doc_ket()
    assert len(goi) == 1


def test_gui_token_noi_bo_khi_co_bien(monkeypatch):
    """CRM 05/09: route phát khoá đòi X-Noi-Bo = OUTLIERY_TOKEN_NOI_BO (cả cụm
    chung một giá trị từ start-all). Không có biến (máy dev) -> không gửi header."""
    bat = {}

    class _R:
        ok = True

        @staticmethod
        def json():
            return {"chia_beat": _muc()}

    def _get(url, headers=None, timeout=None):
        bat["headers"] = headers or {}
        return _R()

    monkeypatch.setattr("requests.get", _get)
    monkeypatch.setenv("OUTLIERY_TOKEN_NOI_BO", "bi-mat-cum")
    ket_v3.doc_ket(force=True)
    assert bat["headers"] == {"X-Noi-Bo": "bi-mat-cum"}

    monkeypatch.delenv("OUTLIERY_TOKEN_NOI_BO")
    ket_v3.doc_ket(force=True)
    assert bat["headers"] == {}


# ------------------------------ nap_env -------------------------------------
def test_gen_canh_dat_ark_key(monkeypatch):
    import os

    monkeypatch.delenv("ARK_API_KEY", raising=False)
    _gia_ket(monkeypatch, {"gen_canh": _muc(key="ark-xyz", nha="seedream")})
    dat = ket_v3.nap_env()
    assert "ARK_API_KEY" in dat
    assert os.environ["ARK_API_KEY"] == "ark-xyz"


def test_arkclient_hoi_ket_truoc_env(monkeypatch):
    """ArkClient: két là nguồn sự thật — có két thì .env/env không được thắng."""
    import autoedit.aigen.client as mc

    monkeypatch.setenv("ARK_API_KEY", "ark-cu-trong-env")
    monkeypatch.setattr("autoedit.web.ket_v3.khoa_cua_viec",
                        lambda viec: ("ark-tu-ket", "") if viec == "gen_canh" else ("", ""))
    assert mc.ArkClient()._key == "ark-tu-ket"


def test_arkclient_ket_tat_roi_ve_env(monkeypatch):
    import autoedit.aigen.client as mc

    monkeypatch.setenv("ARK_API_KEY", "ark-tu-env")
    monkeypatch.setattr("autoedit.web.ket_v3.khoa_cua_viec",
                        lambda viec: ("", ""))
    assert mc.ArkClient()._key == "ark-tu-env"


def test_anthropic_dat_dung_bien(monkeypatch):
    import os

    _gia_ket(monkeypatch, {"chia_beat": _muc(key="sk-ant-1", nha="anthropic",
                                             model="claude-sonnet-5")})
    dat = ket_v3.nap_env()
    assert "ANTHROPIC_API_KEY" in dat
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-1"
    assert os.environ["L3_MODEL"] == "claude-sonnet-5"


def test_glm_di_duong_openai_compatible(monkeypatch):
    import os

    _gia_ket(monkeypatch, {"cham_footage": _muc(key="glm-key", nha="GLM (z.ai)",
                                                model="glm-4.6")})
    ket_v3.nap_env()
    assert os.environ["LLM_API_KEY"] == "glm-key"
    assert os.environ["LLM_PROVIDER"] == "glm"
    assert os.environ["RANK_MODEL"] == "glm-4.6"
    # Mọi code GLM trong repo đọc GLM_API_KEY, KHÔNG đọc LLM_API_KEY. Thiếu biến này
    # thì két có khoá mà job vẫn báo "Thiếu GLM_API_KEY" và tắt vision gate (30/08).
    assert os.environ["GLM_API_KEY"] == "glm-key"


def test_nhieu_khoa_glm_thanh_key_phu(monkeypatch):
    """Khoá thứ 2+ đi GLM_API_KEY_2..9 — nhiều khoá = nhiều luồng song song."""
    import os

    for b in ("GLM_API_KEY_2", "GLM_API_KEY_3"):
        os.environ.pop(b, None)
    muc = _muc(key="k1", nha="glm", model="glm-5.3")
    muc["khoa"] = [{"nha": "glm", "key": "k1"}, {"nha": "glm", "key": "k2"}]
    _gia_ket(monkeypatch, {"chia_beat": muc})
    ket_v3.nap_env()
    assert os.environ["GLM_API_KEY"] == "k1"
    assert os.environ["GLM_API_KEY_2"] == "k2"
    assert "GLM_API_KEY_3" not in os.environ


def test_khoa_phu_khac_nha_thi_bo_qua(monkeypatch):
    """Trộn nhà khác vào cùng việc -> không nhét nhầm key nhà khác vào GLM_API_KEY_n."""
    import os

    os.environ.pop("GLM_API_KEY_2", None)
    muc = _muc(key="k1", nha="glm")
    muc["khoa"] = [{"nha": "glm", "key": "k1"}, {"nha": "deepseek", "key": "ds"}]
    _gia_ket(monkeypatch, {"chia_beat": muc})
    ket_v3.nap_env()
    assert "GLM_API_KEY_2" not in os.environ


def test_deepseek_nhan_dung_provider(monkeypatch):
    import os

    _gia_ket(monkeypatch, {"chia_beat": _muc(key="ds", nha="DeepSeek")})
    ket_v3.nap_env()
    assert os.environ["LLM_PROVIDER"] == "deepseek"


def test_hai_viec_hai_nha_khac_nhau(monkeypatch):
    """Đúng phương án user chốt: Anthropic cho chia beat, GLM cho chấm footage."""
    import os

    _gia_ket(monkeypatch, {
        "chia_beat": _muc(key="sk-ant", nha="anthropic", model="claude-sonnet-5"),
        "cham_footage": _muc(key="glm-k", nha="glm", model="glm-4.6"),
    })
    ket_v3.nap_env()
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant"
    assert os.environ["LLM_API_KEY"] == "glm-k"
    assert os.environ["L3_MODEL"] == "claude-sonnet-5"
    assert os.environ["RANK_MODEL"] == "glm-4.6"


def test_ket_rong_thi_KHONG_dung_den_env(monkeypatch):
    """Két chưa cấp phát -> giữ nguyên .env, không xoá key đang dùng được."""
    import os

    monkeypatch.setenv("ANTHROPIC_API_KEY", "tu-env")
    _gia_ket(monkeypatch, {})
    assert ket_v3.nap_env() == []
    assert os.environ["ANTHROPIC_API_KEY"] == "tu-env"


def test_viec_khong_co_khoa_thi_bo_qua(monkeypatch):
    import os

    monkeypatch.setenv("LLM_API_KEY", "tu-env")
    _gia_ket(monkeypatch, {"cham_footage": {"khoa": [], "model": "x"}})
    assert ket_v3.nap_env() == []
    assert os.environ["LLM_API_KEY"] == "tu-env"


def test_khoa_rong_khong_ghi_de(monkeypatch):
    import os

    monkeypatch.setenv("ANTHROPIC_API_KEY", "tu-env")
    _gia_ket(monkeypatch, {"chia_beat": _muc(key="", nha="anthropic")})
    ket_v3.nap_env()
    assert os.environ["ANTHROPIC_API_KEY"] == "tu-env"


# ------------------------------ khoá stock ----------------------------------
def _stock(*cap):
    """cap = (nha, key)... -> mục tim_footage."""
    return {"khoa": [{"id": f"k{i}", "key": k, "loai": "stock", "nha": n}
                     for i, (n, k) in enumerate(cap)], "che_do": "xoay_vong"}


def test_pexels_pixabay_dat_dung_bien(monkeypatch):
    import os

    _gia_ket(monkeypatch, {"tim_footage": _stock(("pexels", "px-1"),
                                                 ("pixabay", "pb-1"))})
    dat = ket_v3.nap_env()
    assert os.environ["PEXELS_API_KEY"] == "px-1"
    assert os.environ["PIXABAY_API_KEY"] == "pb-1"
    assert set(dat) == {"PEXELS_API_KEY", "PIXABAY_API_KEY"}


def test_nhieu_khoa_cung_nha_thi_NOI_de_nhan_han_muc(monkeypatch):
    """Pexels ~200 query/giờ/khoá — nhiều khoá phải nối, không đè lên nhau."""
    import os

    _gia_ket(monkeypatch, {"tim_footage": _stock(("pexels", "a"), ("pexels", "b"),
                                                 ("pexels", "c"))})
    ket_v3.nap_env()
    assert os.environ["PEXELS_API_KEY"] == "a,b,c"

    from autoedit.sourcer.pexels import collect_pexels_keys
    assert collect_pexels_keys(os.environ) == ["a", "b", "c"]


def test_nha_stock_la_thi_bo_qua(monkeypatch):
    import os

    _gia_ket(monkeypatch, {"tim_footage": _stock(("unsplash", "u-1"))})
    assert ket_v3.nap_env() == []
    assert "PEXELS_API_KEY" not in os.environ


def test_chua_cap_khoa_stock_thi_giu_env(monkeypatch):
    import os

    monkeypatch.setenv("PEXELS_API_KEY", "tu-env")
    _gia_ket(monkeypatch, {"tim_footage": {"khoa": []}})
    assert ket_v3.nap_env() == []
    assert os.environ["PEXELS_API_KEY"] == "tu-env"


# ------------------------------ khoá serp (entity) --------------------------
def test_serper_dat_dung_bien(monkeypatch):
    """tim_tu_lieu (Serper.dev) -> SERPER_API_KEY — route entity hết needs_human."""
    import os

    _gia_ket(monkeypatch, {"tim_tu_lieu": {"khoa": [
        {"id": "k1", "key": "srp-1", "loai": "serp", "nha": "serper"}]}})
    dat = ket_v3.nap_env()
    assert os.environ["SERPER_API_KEY"] == "srp-1"
    assert dat == ["SERPER_API_KEY"]


def test_nha_serp_khac_thi_bo_qua(monkeypatch):
    """serpapi/searchapi chưa có client trong pipeline — không nhét nhầm biến."""
    import os

    _gia_ket(monkeypatch, {"tim_tu_lieu": {"khoa": [
        {"id": "k1", "key": "sa-1", "loai": "serp", "nha": "serpapi"}]}})
    assert ket_v3.nap_env() == []
    assert "SERPER_API_KEY" not in os.environ


# ------------------------------ khoa_cua_viec -------------------------------
def test_lay_khoa_va_model_cua_viec(monkeypatch):
    _gia_ket(monkeypatch, {"chia_beat": _muc(key="abc", model="m1")})
    assert ket_v3.khoa_cua_viec("chia_beat") == ("abc", "m1")
    assert ket_v3.khoa_cua_viec("khong-co") == ("", "")


# ------------------------------ KHÔNG lộ khoá -------------------------------
def test_trang_thai_KHONG_lo_gia_tri_khoa(monkeypatch):
    """UI chỉ được biết CÓ khoá hay chưa — giá trị không bao giờ ra khỏi app."""
    _gia_ket(monkeypatch, {"chia_beat": _muc(key="sk-ant-BIMAT", model="m")})
    st = ket_v3.trang_thai()
    assert st["noi_duoc"] is True
    assert st["viec"]["chia_beat"] == {"co_khoa": True, "model": "m"}
    assert "sk-ant-BIMAT" not in str(st)


def test_trang_thai_khi_ket_tat(monkeypatch):
    _gia_ket(monkeypatch, {})
    st = ket_v3.trang_thai()
    assert st["noi_duoc"] is False and st["viec"] == {}
