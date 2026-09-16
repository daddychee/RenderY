"""Bàn kịch bản — TAB CÀI ĐẶT trong chính app (user chốt 16/09).

*"Tạm thời cho 1 tab cài đặt sẵn ở trong app này, chưa liên quan gì đến hệ
production đang chạy. Đến cuối tuần tôi sẽ ghép vào sau."*

Nên khoá LLM cho phần citation nằm trong `kichban.db` — KHÔNG đụng két OUTLIERY,
KHÔNG ghi `.env`, không chạm gì của 9118. Cuối tuần ghép vào két thì chỉ việc bỏ
trống ô này: thứ tự đọc là **cài đặt trong app -> két -> biến môi trường**, nên
két có khoá là nó tự thắng, không phải sửa code.

Hai luật về khoá, vì đây là mạng nội bộ và danh tính mới chỉ là tên tự khai:
  1. Đọc ra thì CHE (chỉ 4 ký tự cuối) — không API nào trả khoá thật.
  2. Chỉ nhận đúng vài khoá cấu hình đã khai; tên lạ bị từ chối.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.kichban.app import tao_app
from autoedit.kichban.kho import Kho


@pytest.fixture()
def c(tmp_path):
    cl = TestClient(tao_app(Kho(tmp_path / "k.db")))
    cl.headers.update({"X-Remote-User": "haint"})
    return cl


# ------------------------------- lưu / đọc ----------------------------------
def test_luu_roi_doc_lai_cai_dat(c):
    c.post("/api/cai-dat", json={"llm_url": "https://api2.apisuper.cloud",
                                 "llm_model": "grok-4.6",
                                 "llm_key": "sk-that-day-du-123456789"})
    d = c.get("/api/cai-dat").json()
    assert d["llm_url"] == "https://api2.apisuper.cloud"
    assert d["llm_model"] == "grok-4.6"


def test_doc_ra_thi_CHE_khoa(c):
    """Mạng nội bộ + danh tính là tên tự khai: không API nào được trả khoá thật."""
    c.post("/api/cai-dat", json={"llm_key": "sk-abcdefghijklmnop6789"})
    d = c.get("/api/cai-dat").json()
    assert "abcdefghij" not in str(d)
    assert d["llm_key"].endswith("6789") and "…" in d["llm_key"]


def test_khoa_cau_hinh_la_bi_tu_choi(c):
    """Whitelist — không cho biến ô cài đặt thành chỗ ghi gì cũng được."""
    assert c.post("/api/cai-dat", json={"duong_dan_nas": "F:/"}).status_code == 400


def test_chua_khai_ten_thi_khong_duoc_sua_cai_dat(c):
    assert TestClient(c.app).post("/api/cai-dat",
                                  json={"llm_model": "x"}).status_code == 401


def test_de_trong_thi_xoa_de_roi_ve_ket(c):
    """Cuối tuần ghép vào két: bỏ trống ô trong app là xong, không phải sửa code."""
    c.post("/api/cai-dat", json={"llm_key": "sk-1234567890"})
    c.post("/api/cai-dat", json={"llm_key": ""})
    assert c.get("/api/cai-dat").json()["llm_key"] == ""


# ------------------------------- địa chỉ gọi --------------------------------
def test_dia_chi_goc_duoc_tu_noi_duoi_openai():
    """User đưa `https://api2.apisuper.cloud` — đó là GỐC, chưa phải endpoint.
    Tự nối `/v1/chat/completions` thay vì bắt người dùng nhớ."""
    from autoedit.kichban.dich import dia_chi_chat

    assert dia_chi_chat("https://api2.apisuper.cloud") == \
        "https://api2.apisuper.cloud/v1/chat/completions"
    assert dia_chi_chat("https://api2.apisuper.cloud/") == \
        "https://api2.apisuper.cloud/v1/chat/completions"


def test_dia_chi_da_day_du_thi_giu_nguyen():
    from autoedit.kichban.dich import dia_chi_chat

    u = "https://api.z.ai/api/paas/v4/chat/completions"
    assert dia_chi_chat(u) == u
    assert dia_chi_chat("https://x.example/v1") == "https://x.example/v1/chat/completions"


# ------------------------------- thứ tự đọc ---------------------------------
def test_cai_dat_trong_app_THANG_ket_va_env(tmp_path, monkeypatch):
    from autoedit.kichban import dich as mdich

    kho = Kho(tmp_path / "k.db")
    kho.luu_cai_dat({"llm_key": "KHOA-APP", "llm_model": "grok-4.6",
                     "llm_url": "https://api2.apisuper.cloud"})
    monkeypatch.setattr(mdich, "_khoa_tu_ket", lambda: ("KHOA-KET", "glm-5.3"))
    monkeypatch.setenv("GLM_API_KEY", "KHOA-ENV")

    m = mdich.DichGLM(cai_dat=kho.doc_cai_dat())
    assert m.key == "KHOA-APP"
    assert m.model == "grok-4.6"
    assert m.url == "https://api2.apisuper.cloud/v1/chat/completions"


def test_bo_trong_o_app_thi_roi_ve_ket(tmp_path, monkeypatch):
    from autoedit.kichban import dich as mdich

    kho = Kho(tmp_path / "k.db")
    monkeypatch.setattr(mdich, "_khoa_tu_ket", lambda: ("KHOA-KET", "glm-5.3"))
    m = mdich.DichGLM(cai_dat=kho.doc_cai_dat())
    assert m.key == "KHOA-KET" and m.model == "glm-5.3"


# ------------------------------- nút Thử ------------------------------------
def test_nut_thu_bao_ket_qua(tmp_path):
    """Dán khoá xong phải BẤM THỬ ĐƯỢC NGAY — không thì lỗi chỉ lộ lúc đang kiểm
    chứng giữa chừng."""
    kho = Kho(tmp_path / "k.db")
    cl = TestClient(tao_app(kho, thu_llm=lambda cd: {"ok": True, "tra_loi": "chào"}))
    cl.headers.update({"X-Remote-User": "haint"})
    r = cl.post("/api/cai-dat/thu")
    assert r.status_code == 200 and r.json()["ok"] is True


def test_nut_thu_bao_loi_ro_khi_hong(tmp_path):
    def _hong(cd):
        raise RuntimeError("401 Unauthorized — sai khoá")

    cl = TestClient(tao_app(Kho(tmp_path / "k.db"), thu_llm=_hong))
    cl.headers.update({"X-Remote-User": "haint"})
    r = cl.post("/api/cai-dat/thu")
    assert r.status_code == 200 and r.json()["ok"] is False
    assert "sai khoá" in r.json()["loi"]


# ----------------- hai model cùng một nhà cung cấp (user 16/09) --------------
def test_chon_model_rieng_cho_dich_va_cho_kiem(c):
    """Nhà cung cấp này có cả grok-4.6 lẫn gpt-5.6. Dịch là việc rẻ và chạy nhiều
    (mỗi lần chẻ dòng lại gọi), kiểm chứng thì cần model khoẻ — nên tách hai ô."""
    c.post("/api/cai-dat", json={"llm_model": "grok-4.6", "dich_model": "gpt-5.6"})
    d = c.get("/api/cai-dat").json()
    assert d["llm_model"] == "grok-4.6" and d["dich_model"] == "gpt-5.6"


def test_de_trong_dich_model_thi_dung_chung_model_kiem(tmp_path):
    from autoedit.kichban import dich as mdich

    kho = Kho(tmp_path / "k.db")
    kho.luu_cai_dat({"llm_key": "K", "llm_model": "grok-4.6",
                     "llm_url": "https://api2.apisuper.cloud"})
    assert mdich.DichGLM(cai_dat=kho.doc_cai_dat()).model == "grok-4.6"


def test_dich_dung_dich_model_khi_co(tmp_path):
    from autoedit.kichban import dich as mdich

    kho = Kho(tmp_path / "k.db")
    kho.luu_cai_dat({"llm_key": "K", "llm_model": "grok-4.6", "dich_model": "gpt-5.6",
                     "llm_url": "https://api2.apisuper.cloud"})
    assert mdich.DichGLM(cai_dat=kho.doc_cai_dat(), viec="dich").model == "gpt-5.6"


def test_tham_so_rieng_cua_glm_khong_gui_cho_nha_khac(tmp_path):
    """`reasoning_effort` là tham số RIÊNG của GLM (bắt buộc với nó — thiếu thì
    nó nuốt hết token vào phần suy nghĩ). Gửi sang cổng trung gian chạy
    grok-4.6 / gpt-5.6 thì nhiều cổng trả 400. Chỉ gửi khi model là glm."""
    from autoedit.kichban.dich import than_goi

    assert "reasoning_effort" in than_goi("glm-5.3", "he", "than")
    assert "reasoning_effort" not in than_goi("grok-4.6", "he", "than")
    assert "reasoning_effort" not in than_goi("gpt-5.6", "he", "than")


def test_dat_dia_chi_moi_thi_KHONG_muon_khoa_cua_he(tmp_path, monkeypatch):
    """Đo thật 16/09: khai địa chỉ apisuper nhưng chưa dán khoá -> nó lấy khoá GLM
    của két gửi sang cổng mới, trả `403 Forbidden` — người dùng tưởng cổng hỏng.

    Địa chỉ và khoá phải đi CÙNG MỘT NGUỒN: đã khai địa chỉ riêng thì khoá cũng
    phải là khoá riêng, thiếu thì báo thẳng "chưa có khoá".
    """
    from autoedit.kichban import dich as mdich

    kho = Kho(tmp_path / "k.db")
    kho.luu_cai_dat({"llm_url": "https://api2.apisuper.cloud", "llm_model": "grok-4.6"})
    monkeypatch.setattr(mdich, "_khoa_tu_ket", lambda: ("KHOA-GLM-CUA-HE", "glm-5.3"))
    monkeypatch.setenv("GLM_API_KEY", "KHOA-ENV")

    m = mdich.DichGLM(cai_dat=kho.doc_cai_dat())
    assert m.key == "", "không được mượn khoá của hệ cho cổng khác"
    assert m.url.startswith("https://api2.apisuper.cloud")
