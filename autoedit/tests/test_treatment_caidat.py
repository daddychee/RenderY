"""Treatment — khoá LLM lấy từ KÉT của General, app KHÔNG giữ sổ khoá riêng.

User chốt 23/09: *"Add setting vào khối general của CRM... theo đúng rule của
General"*. Luật General (`docs/APPS.md` bước 5): khoá do **Owner** nhập ở
**General › API Keys**, app hỏi qua loopback theo SLUG CỦA CHÍNH NÓ; mọi cửa
sửa khoá bên trong app phải đóng.

Nên tab ⚙ cũ bị gỡ, bảng `cai_dat` bị gỡ. Đổi model/nhà cung cấp = việc của
Owner trên General, không phải việc của app.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho


@pytest.fixture()
def c(tmp_path):
    cl = TestClient(tao_app(Kho(tmp_path / "k.db")))
    cl.headers.update({"X-Remote-User": "haint", "X-Remote-Actions": "sua"})
    return cl


# --------------------------- cửa sửa khoá đã đóng ---------------------------
def test_khong_con_duong_sua_khoa_trong_app(c):
    """App không được giữ sổ khoá riêng — cửa cũ phải đóng hẳn, kể cả Owner."""
    assert c.get("/api/cai-dat").status_code == 404
    assert c.post("/api/cai-dat", json={"llm_key": "x"}).status_code == 404


# ------------------------------- đọc từ két ---------------------------------
def test_lay_khoa_model_va_DIA_CHI_tu_ket(monkeypatch):
    """Đường A (Owner chốt 23/09): két trả kèm `base_url` nên đổi nhà cung cấp ở
    General là app gọi đúng địa chỉ mới — không còn bảng nhà chép trong app."""
    from autoedit.treatment import dich as mdich

    monkeypatch.setattr(mdich, "doc_ket_viec", lambda: {
        "key": "sk-mwapi", "model": "claude-sonnet-5",
        "base_url": "https://api.mwapi.dev/v1"})
    m = mdich.LLM()
    assert m.key == "sk-mwapi"
    assert m.model == "claude-sonnet-5"
    assert m.url == "https://api.mwapi.dev/v1/chat/completions"


def test_doi_nha_cung_cap_thi_doi_luon_dia_chi(monkeypatch):
    from autoedit.treatment import dich as mdich

    monkeypatch.setattr(mdich, "doc_ket_viec", lambda: {
        "key": "sk-grok", "model": "grok-4.6",
        "base_url": "https://api2.apisuper.cloud/v1"})
    assert mdich.LLM().url == "https://api2.apisuper.cloud/v1/chat/completions"


def test_ket_chua_cap_phat_thi_bao_ro_di_dau_ma_cap(monkeypatch):
    """Câu lỗi phải chỉ đúng chỗ Owner bấm, không nêu tên biến kỹ thuật."""
    from autoedit.treatment import dich as mdich

    monkeypatch.setattr(mdich, "doc_ket_viec", lambda: {})
    with pytest.raises(mdich.DichLoi, match="General"):
        mdich.LLM().dich(["x"])


def test_dia_chi_goc_duoc_tu_noi_duoi_openai():
    from autoedit.treatment.dich import dia_chi_chat

    assert dia_chi_chat("https://api.mwapi.dev/v1") == "https://api.mwapi.dev/v1/chat/completions"
    assert dia_chi_chat("https://api.z.ai/api/paas/v4/chat/completions") ==         "https://api.z.ai/api/paas/v4/chat/completions"


def test_tham_so_rieng_cua_glm_khong_gui_cho_nha_khac():
    """`reasoning_effort` là tham số RIÊNG của GLM (với GLM là bắt buộc), nhưng
    cổng khác trả 400. Chỉ gửi khi model là glm."""
    from autoedit.treatment.dich import than_goi

    assert "reasoning_effort" in than_goi("glm-5.3", "he", "than")
    assert "reasoning_effort" not in than_goi("claude-sonnet-5", "he", "than")


def test_bao_loi_goi_dung_TEN_MODEL(monkeypatch):
    import requests

    from autoedit.treatment import dich as mdich

    monkeypatch.setattr(mdich, "doc_ket_viec", lambda: {
        "key": "k", "model": "claude-sonnet-5", "base_url": "https://api.mwapi.dev/v1"})

    class _R:
        status_code, text = 402, "het han muc"

    monkeypatch.setattr(requests, "post", lambda *a, **k: _R())
    with pytest.raises(mdich.DichLoi) as e:
        mdich.LLM().dich(["x"])
    assert "claude-sonnet-5" in str(e.value)


def test_hoi_ket_theo_SLUG_CUA_CHINH_APP(monkeypatch):
    """Đo thật 23/09: cấp phát đúng rồi mà app vẫn báo "chưa cấp" — vì nó đi nhờ
    `web/ket_v3` của RenderY, module đó ghi cứng `SLUG = "rendery"`. Két trả cấp
    phát của RenderY, trong đó không có việc `dich` -> rỗng.

    Treatment phải hỏi ĐÚNG slug của nó.
    """
    import requests

    from autoedit.treatment import dich as mdich

    da_goi = {}

    class _R:
        status_code = 200

        @staticmethod
        def json():
            return {"dich": {"khoa": [{"key": "sk-mwapi",
                                       "base_url": "https://api.mwapi.dev/v1"}],
                             "model": "claude-sonnet-5"}}

    def _get(url, **kw):
        da_goi["url"] = url
        return _R()

    monkeypatch.setattr(requests, "get", _get)
    cd = mdich.doc_ket_viec()
    assert da_goi["url"].endswith("/api/cau-hinh/api-khoa/treatment"), da_goi["url"]
    assert cd["key"] == "sk-mwapi" and cd["model"] == "claude-sonnet-5"
    assert cd["base_url"] == "https://api.mwapi.dev/v1"
