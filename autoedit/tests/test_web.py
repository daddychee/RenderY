"""Test bảng điều khiển web (RenderY R8) — không bật server thật.

Web bind LAN mà trang Cài đặt đọc/ghi .env chứa API key, nên test khoá chặt 3 thứ:
whitelist key (không cho ghi biến lạ), chống chèn dòng .env, và xác thực token.
"""

from __future__ import annotations

import json

import pytest

from autoedit.web import server as srv


@pytest.fixture
def env_file(tmp_path, monkeypatch):
    """Trỏ ROOT sang tmp để không đụng .env thật."""
    monkeypatch.setattr(srv, "ROOT", tmp_path)
    monkeypatch.setattr(srv, "PROJECTS_DIR", tmp_path / "projects")
    monkeypatch.setattr(srv, "JOBS_DIR", tmp_path / ".web_jobs")
    return tmp_path / ".env"


def _project(root, pid, stages: dict, **kw):
    d = root / "projects" / pid
    d.mkdir(parents=True)
    (d / "project.json").write_text(json.dumps({
        "project_id": pid, "title": kw.get("title", pid), "created_at": "2026-08-30",
        "stages": stages, "beats": kw.get("beats", []), "shots": kw.get("shots", []),
        "draft_path": kw.get("draft_path", ""),
    }), encoding="utf-8")
    return d


# ------------------------------ đọc project ---------------------------------
def test_doc_project_va_dem_stage(env_file, tmp_path):
    _project(tmp_path, "ch01", {
        "align": {"status": "done"}, "cut": {"status": "done"},
        "source": {"status": "running"}, "assemble": {"status": "pending"}})
    info = srv._read_project(tmp_path / "projects" / "ch01")
    assert info["done"] == 2 and info["total"] == 4
    assert info["failed"] == []


def test_gom_loi_va_canh_bao(env_file, tmp_path):
    _project(tmp_path, "ch01", {
        "align": {"status": "done", "warnings": ["lệch duration"]},
        "source": {"status": "failed", "error": "hết hạn mức"}})
    info = srv._read_project(tmp_path / "projects" / "ch01")
    assert info["failed"] == ["source"]
    assert info["warnings"] == ["lệch duration"]
    assert info["stages"]["source"]["error"] == "hết hạn mức"


def test_project_json_hong_khong_lam_do_ca_danh_sach(env_file, tmp_path):
    _project(tmp_path, "tot", {"align": {"status": "done"}})
    bad = tmp_path / "projects" / "hong"
    bad.mkdir()
    (bad / "project.json").write_text("{khong phai json", encoding="utf-8")
    assert srv._read_project(bad) is None
    assert [p["project_id"] for p in srv._list_projects()] == ["tot"]


def test_thu_muc_projects_chua_ton_tai(env_file, tmp_path):
    assert srv._list_projects() == []


# ------------------------------ .env ----------------------------------------
def test_ghi_env_giu_nguyen_dong_khac(env_file):
    env_file.write_text("# ghi chú\nPEXELS_API_KEY=cu\nBIEN_KHAC=giu\n", encoding="utf-8")
    saved = srv._write_env({"PEXELS_API_KEY": "moi"})
    txt = env_file.read_text(encoding="utf-8")
    assert saved == ["PEXELS_API_KEY"]
    assert "PEXELS_API_KEY=moi" in txt
    assert "# ghi chú" in txt and "BIEN_KHAC=giu" in txt


def test_them_key_chua_co(env_file):
    env_file.write_text("PEXELS_API_KEY=a\n", encoding="utf-8")
    srv._write_env({"PIXABAY_API_KEY": "b"})
    assert "PIXABAY_API_KEY=b" in env_file.read_text(encoding="utf-8")


def test_key_ngoai_whitelist_bi_bo(env_file):
    """Không cho ai đó ghi biến lạ vào .env qua web."""
    env_file.write_text("PEXELS_API_KEY=a\n", encoding="utf-8")
    assert srv._write_env({"BIEN_LA": "x", "PATH": "/hack"}) == []
    txt = env_file.read_text(encoding="utf-8")
    assert "BIEN_LA" not in txt and "/hack" not in txt


def test_chong_chen_dong_env(env_file):
    """Giá trị chứa xuống dòng = chèn biến tuỳ ý -> phải bỏ."""
    env_file.write_text("PEXELS_API_KEY=a\n", encoding="utf-8")
    assert srv._write_env({"PEXELS_API_KEY": "x\nANTHROPIC_API_KEY=trom"}) == []
    assert "trom" not in env_file.read_text(encoding="utf-8")


def test_gia_tri_rong_la_giu_nguyen(env_file):
    env_file.write_text("PEXELS_API_KEY=giu\n", encoding="utf-8")
    assert srv._write_env({"PEXELS_API_KEY": "  "}) == []
    assert "PEXELS_API_KEY=giu" in env_file.read_text(encoding="utf-8")


def test_ghi_atomic_khong_de_lai_file_tam(env_file):
    env_file.write_text("PEXELS_API_KEY=a\n", encoding="utf-8")
    srv._write_env({"PEXELS_API_KEY": "b"})
    assert not (env_file.parent / ".env.tmp").exists()


def test_doc_env_bo_qua_comment(env_file):
    env_file.write_text("# c\n\nA=1\nB = 2 \nkhong-co-dau-bang\n", encoding="utf-8")
    assert srv._read_env() == {"A": "1", "B": "2"}


def test_job_request_3_phuong_an_mac_dinh_stock():
    """User 05/09: 3 phuong an dung — mac dinh PA1 stock (khong AI, khong ref),
    hanh vi y het truoc khi co tinh nang (khong doi gi voi team dang dung)."""
    r = srv.JobRequest(folder="x")
    assert r.phuong_an == "stock"
    assert r.kenh_ref == ""
    assert r.aigen is False


def test_doc_tooltip_hop_le():
    assert srv._doc_tooltip(["0:00=119", "0:31=71%", "4:19=40"]) == [
        (0.0, 119.0), (31.0, 71.0), (259.0, 40.0)]


def test_doc_tooltip_rong_tra_rong():
    assert srv._doc_tooltip([]) == []


def test_doc_tooltip_thieu_dau_bang_bao_loi():
    with pytest.raises(ValueError, match="thiếu dấu"):
        srv._doc_tooltip(["0:31 71"])


def test_doc_tooltip_phan_tram_khong_hop_le_bao_loi():
    with pytest.raises(ValueError, match="phần trăm"):
        srv._doc_tooltip(["0:31=abc"])


def test_doc_tooltip_gio_phut_giay():
    assert srv._doc_tooltip(["1:02:15=50"]) == [(3735.0, 50.0)]


# ------------------------------ module Kênh Ref (05/09) ----------------------
class _ReqCRM:
    """Request giả QUA CRM: loopback + trust proxy + header vai."""

    def __init__(self, vai=""):
        self.headers = {"x-forwarded-host": "crm.local", "x-remote-role": vai}
        self.query_params = {}
        self.client = type("C", (), {"host": "127.0.0.1"})()


def test_nghien_cuu_kenh_qua_crm_theo_vai(monkeypatch):
    """Qua CRM: manager/owner/admin được nghiên cứu, editor(viewer/leader) KHÔNG."""
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    assert srv._duoc_nghien_cuu_kenh(_ReqCRM("manager")) is True
    assert srv._duoc_nghien_cuu_kenh(_ReqCRM("owner")) is True
    assert srv._duoc_nghien_cuu_kenh(_ReqCRM("admin")) is True
    assert srv._duoc_nghien_cuu_kenh(_ReqCRM("leader")) is False
    assert srv._duoc_nghien_cuu_kenh(_ReqCRM("viewer")) is False


def test_nghien_cuu_kenh_ngoai_crm_thi_mo(monkeypatch):
    """Chạy trực tiếp không qua cổng CRM (dev/máy chủ): mở — đúng khuôn is_admin."""
    monkeypatch.delenv("RENDERY_TRUST_PROXY", raising=False)
    r = _ReqCRM("")
    r.headers = {}
    assert srv._duoc_nghien_cuu_kenh(r) is True


def test_api_kenh_them_trung_bao_409(monkeypatch, tmp_path):
    """Kênh đã có trong thư viện -> 409 chỉ sang nút Đo lại, không đo đè."""
    from fastapi import HTTPException

    import autoedit.kenh.hoso as mh
    monkeypatch.setattr(mh, "resolve_data_root", lambda *a, **k: tmp_path)
    monkeypatch.delenv("RENDERY_WEB_TOKEN", raising=False)
    from autoedit.kenh.hoso import HoSoKenh
    HoSoKenh(ten="fern-tv", so_video_hoi_tu=1).ghi()
    r = _ReqCRM("")
    r.headers = {}
    with pytest.raises(HTTPException) as e:
        srv.api_kenh_them(srv.KenhRequest(link="https://youtube.com/@x", ten="fern tv"), r)
    assert e.value.status_code == 409


def test_api_kenh_them_bat_buoc_ten_phong_cach(monkeypatch, tmp_path):
    """User 05/09: thu vien can TEN doc duoc — thieu ten -> 422, khong lay slug link."""
    from fastapi import HTTPException

    import autoedit.kenh.hoso as mh
    monkeypatch.setattr(mh, "resolve_data_root", lambda *a, **k: tmp_path)
    monkeypatch.delenv("RENDERY_WEB_TOKEN", raising=False)
    r = _ReqCRM("")
    r.headers = {}
    with pytest.raises(HTTPException) as e:
        srv.api_kenh_them(srv.KenhRequest(link="https://youtube.com/@fern-tv"), r)
    assert e.value.status_code == 422
    assert "tên phong cách" in str(e.value.detail).lower()


def test_api_kenh_list_tra_thu_vien(monkeypatch, tmp_path):
    import autoedit.kenh.hoso as mh
    monkeypatch.setattr(mh, "resolve_data_root", lambda *a, **k: tmp_path)
    monkeypatch.delenv("RENDERY_WEB_TOKEN", raising=False)
    from autoedit.kenh.hoso import HoSoKenh
    HoSoKenh(ten="fern-tv", so_video_hoi_tu=2, than_trung_vi=2.1).ghi()
    r = _ReqCRM("")
    r.headers = {}
    d = srv.api_kenh_list(r)
    assert [k["ten"] for k in d["kenh"]] == ["fern-tv"]
    assert d["kenh"][0]["than_trung_vi"] == 2.1


def test_che_secret():
    assert srv._mask("PEXELS_API_KEY", "abcdefghijklmnop") == "abcd…nop"
    assert srv._mask("PEXELS_API_KEY", "ngan") == "…"
    assert srv._mask("ENVATO_EMAIL", "a@b.c") == "a@b.c"   # email không phải secret


# ------------------------------ xác thực ------------------------------------
class _Req:
    def __init__(self, token=None, query=None):
        self.headers = {"x-rendery-token": token} if token else {}
        self.query_params = query or {}


def test_khong_dat_token_thi_mo(monkeypatch):
    monkeypatch.delenv("RENDERY_WEB_TOKEN", raising=False)
    srv._require_auth(_Req())          # không raise


def test_co_token_thi_bat_buoc(monkeypatch):
    from fastapi import HTTPException

    monkeypatch.setenv("RENDERY_WEB_TOKEN", "bimat")
    with pytest.raises(HTTPException) as e:
        srv._require_auth(_Req())
    assert e.value.status_code == 401
    with pytest.raises(HTTPException):
        srv._require_auth(_Req(token="sai"))
    srv._require_auth(_Req(token="bimat"))                    # header đúng
    srv._require_auth(_Req(query={"token": "bimat"}))         # query đúng


# ------------------------------ job -----------------------------------------
def test_khong_chay_2_job_cung_project(env_file, monkeypatch):
    from fastapi import HTTPException

    monkeypatch.setattr(srv.threading, "Thread",
                        lambda **kw: type("T", (), {"start": lambda s: None})())
    srv._jobs.clear()
    srv._start_job("ch01", ["run", "x"])
    with pytest.raises(HTTPException) as e:
        srv._start_job("ch01", ["run", "x"])
    assert e.value.status_code == 409
    srv._jobs.clear()


def test_job_xong_thi_chay_lai_duoc(env_file, monkeypatch):
    monkeypatch.setattr(srv.threading, "Thread",
                        lambda **kw: type("T", (), {"start": lambda s: None})())
    srv._jobs.clear()
    srv._start_job("ch01", ["run", "x"])
    srv._jobs["ch01"]["status"] = "done"
    assert srv._start_job("ch01", ["run", "x"])["status"] == "running"
    srv._jobs.clear()
