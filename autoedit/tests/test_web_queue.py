"""Test API hàng đợi + SSO của web RenderY (tích hợp CRM).

Khoá 2 thứ dễ thành lỗ hổng:
- SSO: chỉ tin header X-Remote-User khi client là LOOPBACK (CRM proxy từ 127.0.0.1).
  Tin header từ LAN = ai cũng mạo danh được.
- Đường dẫn job: chỉ nhận folder NẰM TRONG _INBOX. Không chặn thì bơm được đường dẫn
  tuỳ ý vào worker (worker chạy lệnh trên folder đó).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoedit.web import server as srv


@pytest.fixture
def nas(tmp_path, monkeypatch):
    """Trỏ ROOT + NAS sang tmp để không đụng NAS thật."""
    inbox = tmp_path / "_INBOX"
    inbox.mkdir()
    monkeypatch.setattr(srv, "ROOT", tmp_path)
    monkeypatch.setattr(srv, "NAS_ROOT", tmp_path)
    monkeypatch.setattr(srv, "INBOX", inbox)
    monkeypatch.setattr(srv, "OUTBOX", tmp_path / "Compose Timeline")
    monkeypatch.setattr(srv, "JOBS_DIR", tmp_path / ".web_jobs")
    return inbox


def _job_folder(inbox: Path, ten: str, chuong=("ch01",), du=True) -> Path:
    d = inbox / ten
    for c in chuong:
        cd = d / c
        cd.mkdir(parents=True)
        (cd / "script.txt").write_text("xin chào", encoding="utf-8")
        if du:
            (cd / "voice.mp3").write_bytes(b"\x00" * 10)
    return d


class _Req:
    """Giả Request đủ dùng cho _require_auth + current_user."""

    def __init__(self, host="127.0.0.1", user=None, role=None, token=None,
                 fwd_host=None, query=None):
        self.client = type("C", (), {"host": host})()
        self.headers = {}
        if user:
            self.headers["x-remote-user"] = user
        if role:
            self.headers["x-remote-role"] = role
        if token:
            self.headers["x-rendery-token"] = token
        if fwd_host:
            self.headers["x-forwarded-host"] = fwd_host
        self.query_params = query or {}


# ------------------------------ SSO -----------------------------------------
def test_tin_header_khi_loopback_va_bat_co(monkeypatch):
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    assert srv.current_user(_Req(host="127.0.0.1", user="lam")) == "lam"
    assert srv.current_role(_Req(host="::1", role="Owner")) == "owner"


def test_KHONG_tin_header_tu_LAN(monkeypatch):
    """Truy cập thẳng từ LAN không qua CRM -> header do người gọi tự đặt."""
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    assert srv.current_user(_Req(host="192.168.1.99", user="giam-doc")) == ""
    assert srv.current_role(_Req(host="192.168.1.99", role="owner")) == ""


def test_KHONG_tin_header_khi_chua_bat_co(monkeypatch):
    monkeypatch.delenv("RENDERY_TRUST_PROXY", raising=False)
    assert srv.current_user(_Req(user="lam")) == ""


def test_khong_co_header_tra_rong(monkeypatch):
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    assert srv.current_user(_Req()) == ""


def test_ten_tieng_viet_da_duoc_CRM_chuyen_ASCII(monkeypatch):
    """CRM chuẩn hoá "Nguyễn Văn A" -> "nguyenvana" (app_proxy.py:58) vì header HTTP
    không nhận tiếng Việt có dấu. RenderY nhận đúng chuỗi đã chuẩn hoá đó."""
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    assert srv.current_user(_Req(user="nguyenvana")) == "nguyenvana"


# ------------------------------ sau CRM proxy -------------------------------
def test_nhan_biet_dang_chay_sau_CRM(monkeypatch):
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    assert srv.behind_crm(_Req(fwd_host="192.168.1.23:8000")) is True
    assert srv.behind_crm(_Req()) is False                    # mở trực tiếp
    assert srv.behind_crm(_Req(host="192.168.1.99", fwd_host="x")) is False


def test_qua_CRM_thi_KHONG_doi_token(monkeypatch):
    """Trong iframe CRM không có query ?token=, và người dùng cũng không có gì để
    nhập — CRM đã xác thực bằng session cookie + phân quyền app rồi."""
    monkeypatch.setenv("RENDERY_WEB_TOKEN", "bimat")
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    srv._require_auth(_Req(user="lam", fwd_host="192.168.1.23:8000"))   # không raise


def test_mo_TRUC_TIEP_van_doi_token(monkeypatch):
    """Truy cập thẳng từ LAN không qua CRM -> vẫn phải có token."""
    from fastapi import HTTPException

    monkeypatch.setenv("RENDERY_WEB_TOKEN", "bimat")
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    with pytest.raises(HTTPException) as e:
        srv._require_auth(_Req(host="192.168.1.99"))
    assert e.value.status_code == 401
    srv._require_auth(_Req(host="192.168.1.99", token="bimat"))         # đúng token thì qua


def test_LOOPBACK_khong_du_de_mien_token(monkeypatch):
    """Lỗ hổng bắt được khi chạy thật (30/08): miễn token theo _trust_proxy thì
    MỌI request từ 127.0.0.1 được miễn — mà mọi tiến trình trên máy chủ đều loopback.
    Phải đòi X-Forwarded-Host (CRM luôn gửi) mới miễn."""
    from fastapi import HTTPException

    monkeypatch.setenv("RENDERY_WEB_TOKEN", "bimat")
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    with pytest.raises(HTTPException) as e:
        srv._require_auth(_Req(host="127.0.0.1"))       # loopback nhưng KHÔNG qua CRM
    assert e.value.status_code == 401


def test_api_me_tra_danh_tinh_va_quyen(monkeypatch):
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    d = srv.api_me(_Req(user="lam", role="owner", fwd_host="crm:8000"))
    assert d == {"nguoi": "lam", "vai": "owner", "qua_crm": True, "xem_het": True}

    d2 = srv.api_me(_Req(user="hoa", role="viewer"))
    assert d2["xem_het"] is False and d2["qua_crm"] is False


# ------------------------------ _INBOX --------------------------------------
def test_liet_ke_folder_job(nas):
    _job_folder(nas, "LI070", chuong=("ch01", "ch02"))
    d = srv.api_inbox(_Req())
    assert d["ready"] is True
    assert [f["ten"] for f in d["folders"]] == ["LI070"]
    assert d["folders"][0]["chuong"] == ["ch01", "ch02"]
    assert d["folders"][0]["san_sang"]["ok"] is True


def test_bao_thieu_file_TRUOC_khi_xep_hang(nas):
    """Đừng để nhân sự chờ 24 phút rồi mới biết thiếu voice."""
    _job_folder(nas, "THIEU", du=False)
    f = srv.api_inbox(_Req())["folders"][0]
    assert f["san_sang"]["ok"] is False
    assert any("thiếu voice" in t for t in f["san_sang"]["thieu"])


def test_inbox_chua_ton_tai_bao_ro(nas, monkeypatch):
    monkeypatch.setattr(srv, "INBOX", nas.parent / "khong-co")
    d = srv.api_inbox(_Req())
    assert d["ready"] is False and "Chưa thấy" in d["loi"]


def test_bo_qua_file_le_va_thu_muc_an(nas):
    (nas / "ghi-chu.txt").write_text("x", encoding="utf-8")
    (nas / ".tam").mkdir()
    _job_folder(nas, "THAT")
    assert [f["ten"] for f in srv.api_inbox(_Req())["folders"]] == ["THAT"]


def test_folder_khong_chia_chuong_van_chay_duoc(nas):
    """Video 1 chương: file nằm thẳng trong folder job."""
    d = nas / "MOT-CHUONG"
    d.mkdir()
    (d / "script.txt").write_text("x", encoding="utf-8")
    (d / "voice.mp3").write_bytes(b"\x00")
    f = srv.api_inbox(_Req())["folders"][0]
    assert f["san_sang"]["ok"] is True and f["san_sang"]["so_chuong"] == 1


# ------------------------------ nộp job -------------------------------------
def test_nop_job_vao_hang_doi(nas):
    d = _job_folder(nas, "LI070")
    r = srv.api_add_job(srv.JobRequest(folder=str(d)), _Req())
    assert r["job"]["status"] == "queued"
    assert r["job"]["job_folder"] == str(d)


def test_CHAN_duong_dan_ngoai_INBOX(nas, tmp_path):
    """Không chặn thì bơm được đường dẫn tuỳ ý vào worker."""
    ngoai = tmp_path / "ngoai"
    ngoai.mkdir()
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as e:
        srv.api_add_job(srv.JobRequest(folder=str(ngoai)), _Req())
    assert e.value.status_code == 422


def test_chan_duong_dan_di_len_bang_dotdot(nas):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as e:
        srv.api_add_job(srv.JobRequest(folder=str(nas / ".." / ".." / "etc")), _Req())
    assert e.value.status_code == 422


def test_folder_khong_ton_tai_bao_404(nas):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as e:
        srv.api_add_job(srv.JobRequest(folder=str(nas / "khong-co")), _Req())
    assert e.value.status_code == 404


def test_job_ghi_ten_nguoi_nop(nas, monkeypatch):
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    d = _job_folder(nas, "LI070")
    r = srv.api_add_job(srv.JobRequest(folder=str(d)), _Req(user="lam"))
    assert r["job"]["nguoi"] == "lam"


def test_tuy_chon_di_kem_job(nas):
    d = _job_folder(nas, "LI070")
    r = srv.api_add_job(
        srv.JobRequest(folder=str(d), niche="life-in", no_sub=True), _Req())
    assert r["job"]["opts"]["niche"] == "life-in"
    assert r["job"]["opts"]["no_sub"] is True


# ------------------------------ xem / huỷ -----------------------------------
def test_chi_thay_job_cua_minh(nas, monkeypatch):
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    d = _job_folder(nas, "LI070")
    srv.api_add_job(srv.JobRequest(folder=str(d)), _Req(user="lam"))
    srv.api_add_job(srv.JobRequest(folder=str(d)), _Req(user="hoa"))

    assert len(srv.api_jobs(_Req(user="lam"))["jobs"]) == 1
    # owner xem được hết
    assert len(srv.api_jobs(_Req(user="sep", role="owner"), all_users=True)["jobs"]) == 2


def test_khong_huy_job_nguoi_khac(nas, monkeypatch):
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    from fastapi import HTTPException

    d = _job_folder(nas, "LI070")
    jid = srv.api_add_job(srv.JobRequest(folder=str(d)), _Req(user="lam"))["job"]["id"]
    with pytest.raises(HTTPException) as e:
        srv.api_cancel_job(jid, _Req(user="hoa"))
    assert e.value.status_code == 403
    assert srv.api_cancel_job(jid, _Req(user="lam"))["ok"] is True


def test_owner_huy_duoc_job_nguoi_khac(nas, monkeypatch):
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    d = _job_folder(nas, "LI070")
    jid = srv.api_add_job(srv.JobRequest(folder=str(d)), _Req(user="lam"))["job"]["id"]
    assert srv.api_cancel_job(jid, _Req(user="sep", role="owner"))["ok"] is True


# ------------------------------ badge ---------------------------------------
def test_badge_dem_job_xong_chua_xem(nas, monkeypatch):
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    from autoedit.web import queue as q

    d = _job_folder(nas, "LI070")
    jid = srv.api_add_job(srv.JobRequest(folder=str(d)), _Req(user="lam"))["job"]["id"]
    assert srv.api_badge(_Req(user="lam"))["unseen"] == 0     # chưa xong

    conn = q.connect(nas.parent / "jobs.db")
    q.finish(conn, jid, ok=True)
    conn.close()

    assert srv.api_badge(_Req(user="lam"))["unseen"] == 1
    srv.api_mark_seen(_Req(user="lam"))
    assert srv.api_badge(_Req(user="lam"))["unseen"] == 0


def test_badge_hoi_ho_ten_khac(nas, monkeypatch):
    """CRM gọi thay user -> truyền ?nguoi=<ten>."""
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    from autoedit.web import queue as q

    d = _job_folder(nas, "LI070")
    jid = srv.api_add_job(srv.JobRequest(folder=str(d)), _Req(user="lam"))["job"]["id"]
    conn = q.connect(nas.parent / "jobs.db")
    q.finish(conn, jid, ok=True)
    conn.close()
    assert srv.api_badge(_Req(), nguoi="lam")["unseen"] == 1
