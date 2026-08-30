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
    for b in ("ANTHROPIC_API_KEY", "LLM_API_KEY", "LLM_PROVIDER",
              "L3_MODEL", "RANK_MODEL"):
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


# ------------------------------ nap_env -------------------------------------
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
