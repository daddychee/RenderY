"""Test API hàng đợi + SSO của web RenderY (tích hợp CRM).

Khoá 2 thứ dễ thành lỗ hổng:
- SSO: chỉ tin header X-Remote-User khi client là LOOPBACK (CRM proxy từ 127.0.0.1).
  Tin header từ LAN = ai cũng mạo danh được.
- Đường dẫn job: nhân sự DÁN tự do (mỗi tập một mã, nằm rải theo series) nên rào duy
  nhất là "phải nằm trong gốc NAS". Không chặn thì bơm được đường dẫn bất kỳ vào
  worker (worker chạy lệnh trên thư mục đó).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoedit.web import server as srv


@pytest.fixture
def nas(tmp_path, monkeypatch):
    """Trỏ ROOT + gốc NAS sang tmp để không đụng NAS thật."""
    monkeypatch.setattr(srv, "ROOT", tmp_path)
    monkeypatch.setattr(srv, "NAS_ROOT", tmp_path)
    monkeypatch.setattr(srv, "JOBS_DIR", tmp_path / ".web_jobs")
    return tmp_path


def _job_folder(nas_root: Path, ten: str, chuong=("H", "C1"), du=True) -> Path:
    """Thư mục tập đúng quy ước: <tập>/RenderY/{H,C1,...}."""
    from autoedit.web.chapters import THU_MUC_CON

    d = nas_root / ten
    for c in chuong:
        cd = d / THU_MUC_CON / c
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
    d = srv.api_me(_Req(user="lam", role="admin", fwd_host="crm:9000"))
    assert d == {"nguoi": "lam", "vai": "admin", "qua_crm": True, "xem_het": True,
                 "nghien_cuu_kenh": True}   # admin duoc nghien cuu kenh ref (05/09)

    d2 = srv.api_me(_Req(user="hoa", role="viewer"))
    assert d2["xem_het"] is False and d2["qua_crm"] is False


def test_nhan_ca_vai_admin_cua_V3_lan_owner_cua_he_cu(monkeypatch):
    """OUTLIERY-V3 (`iam.vai_cho_app`) trả admin|manager|leader|viewer — SUY TỪ
    HÀNH ĐỘNG, không map theo tên. Hệ cũ trả 'owner'. Nhận cả hai."""
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    assert srv.is_admin(_Req(user="a", role="admin")) is True
    assert srv.is_admin(_Req(user="a", role="owner")) is True
    for vai in ("manager", "leader", "viewer", ""):
        assert srv.is_admin(_Req(user="a", role=vai or None)) is False


# --------------------------- kiểm thư mục tập -------------------------------
def test_kiem_tap_liet_ke_chuong_dung_thu_tu(nas):
    """Nhân sự dán đường dẫn tập -> thấy ngay các chương H → C1..Cn → E."""
    d = _job_folder(nas, "IN002", chuong=("E", "C2", "H", "C1"))
    r = srv.api_kiem_tap(_Req(), duong_dan=str(d))
    assert r["san_sang"] is True and r["tap"] == "IN002"
    assert [c["ma"] for c in r["chuong"]] == ["H", "C1", "C2", "E"]


def test_kiem_tap_bao_thieu_file_TRUOC_khi_xep_hang(nas):
    """Đừng để nhân sự chờ 24 phút rồi mới biết thiếu voice."""
    d = _job_folder(nas, "THIEU", du=False)
    r = srv.api_kiem_tap(_Req(), duong_dan=str(d))
    assert r["san_sang"] is False
    assert any("thiếu voice" in x for x in r["loi"])


def test_kiem_tap_bao_thieu_thu_muc_RenderY(nas):
    (nas / "LI001").mkdir()
    r = srv.api_kiem_tap(_Req(), duong_dan=str(nas / "LI001"))
    assert r["san_sang"] is False
    assert any("RenderY" in x for x in r["loi"])


def test_kiem_tap_bao_ten_chuong_sai_quy_uoc(nas):
    """Tên cũ như 'ch01', 'clue 1' bị từ chối rõ ràng thay vì xếp sai lặng lẽ."""
    from autoedit.web.chapters import THU_MUC_CON

    d = _job_folder(nas, "LI001", chuong=("H",))
    (d / THU_MUC_CON / "ch01").mkdir()
    r = srv.api_kiem_tap(_Req(), duong_dan=str(d))
    assert any("ch01" in x and "sai quy ước" in x for x in r["loi"])


def test_kiem_tap_khong_nhap_gi(nas):
    r = srv.api_kiem_tap(_Req(), duong_dan="")
    assert r["san_sang"] is False and r["loi"]


def test_kiem_tap_thu_muc_khong_ton_tai(nas):
    r = srv.api_kiem_tap(_Req(), duong_dan=str(nas / "khong-co"))
    assert r["san_sang"] is False and any("Không thấy" in x for x in r["loi"])


def test_kiem_tap_bo_nhay_kep_khi_copy_tu_Explorer(nas):
    """Explorer 'Copy as path' cho chuỗi có nháy kép — phải chịu được."""
    d = _job_folder(nas, "IN002")
    assert srv.api_kiem_tap(_Req(), duong_dan=f'"{d}"')["san_sang"] is True


# --------------------------- quy đổi ổ mạng ---------------------------------
def test_doi_o_mang_Z_sang_duong_may_chu(nas):
    """Nhân sự thấy NAS qua ổ Z:, máy chủ thấy ở F:\\OutlierY Nas 2 — cùng một chỗ.
    Lỗi thật user gặp 30/08: dán 'Z:\\Life In\\US\\LI093' bị báo ngoài NAS."""
    _job_folder(nas, "LI093")
    got = srv.doi_duong_dan(r"Z:\LI093")
    assert got == nas / "LI093"
    assert srv.api_kiem_tap(_Req(), duong_dan=r"Z:\LI093")["san_sang"] is True


def test_doi_ca_chu_thuong_va_dau_gach_xuoi(nas):
    _job_folder(nas, "LI093")
    for tho in (r"z:\LI093", "Z:/LI093", r'"Z:\LI093"'):
        assert srv.doi_duong_dan(tho) == nas / "LI093", tho


def test_doi_duong_UNC(nas):
    """Có người copy kiểu \\\\192.168.1.250\\Video\\... thay vì ổ đã map."""
    _job_folder(nas, "LI093")
    assert srv.doi_duong_dan(r"\\192.168.1.250\Video\LI093") == nas / "LI093"


def test_duong_may_chu_giu_nguyen(nas):
    d = _job_folder(nas, "LI093")
    assert srv.doi_duong_dan(str(d)) == d


def test_chi_rieng_Z_khong_kem_gi(nas):
    assert srv.doi_duong_dan("Z:") == nas
    assert srv.doi_duong_dan("Z:\\") == nas


def test_o_mang_KHAC_van_bi_chan(nas):
    """Y: là share NAS1 — KHÔNG phải nơi để tập, vẫn phải chặn."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as e:
        srv.api_add_job(srv.JobRequest(folder=r"Y:\gi-do"), _Req())
    assert e.value.status_code == 422


# ------------------------------ nộp job -------------------------------------
def test_nop_job_vao_hang_doi(nas):
    d = _job_folder(nas, "LI070")
    r = srv.api_add_job(srv.JobRequest(folder=str(d)), _Req())
    assert r["job"]["status"] == "queued"
    assert r["job"]["job_folder"] == str(d)


def test_CHAN_duong_dan_ngoai_goc_NAS(nas, monkeypatch, tmp_path_factory):
    """Nhân sự dán đường dẫn TỰ DO -> rào duy nhất là 'phải nằm trong gốc NAS'.
    Không chặn thì bơm được đường dẫn bất kỳ vào worker (worker chạy lệnh trên đó).
    """
    from fastapi import HTTPException

    ngoai = tmp_path_factory.mktemp("ngoai-nas")   # thư mục NGOÀI gốc NAS
    with pytest.raises(HTTPException) as e:
        srv.api_add_job(srv.JobRequest(folder=str(ngoai)), _Req())
    assert e.value.status_code == 422
    # cả API kiểm cũng phải chặn, đừng để lộ cây thư mục ngoài NAS
    with pytest.raises(HTTPException):
        srv.api_kiem_tap(_Req(), duong_dan=str(ngoai))


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
    assert len(srv.api_jobs(_Req(user="sep", role="admin"), all_users=True)["jobs"]) == 2


def test_khong_huy_job_nguoi_khac(nas, monkeypatch):
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    from fastapi import HTTPException

    d = _job_folder(nas, "LI070")
    jid = srv.api_add_job(srv.JobRequest(folder=str(d)), _Req(user="lam"))["job"]["id"]
    with pytest.raises(HTTPException) as e:
        srv.api_cancel_job(jid, _Req(user="hoa"))
    assert e.value.status_code == 403
    assert srv.api_cancel_job(jid, _Req(user="lam"))["ok"] is True


def test_admin_huy_duoc_job_nguoi_khac(nas, monkeypatch):
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    d = _job_folder(nas, "LI070")
    jid = srv.api_add_job(srv.JobRequest(folder=str(d)), _Req(user="lam"))["job"]["id"]
    assert srv.api_cancel_job(jid, _Req(user="sep", role="admin"))["ok"] is True


# ------------------------------ badge ---------------------------------------
def test_badge_dem_job_xong_chua_xem(nas, monkeypatch):
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    from autoedit.web import queue as q

    d = _job_folder(nas, "LI070")
    jid = srv.api_add_job(srv.JobRequest(folder=str(d)), _Req(user="lam"))["job"]["id"]
    assert srv.api_badge(_Req(user="lam"))["unseen"] == 0     # chưa xong

    conn = q.connect(nas / "jobs.db")
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
    conn = q.connect(nas / "jobs.db")
    q.finish(conn, jid, ok=True)
    conn.close()
    assert srv.api_badge(_Req(), nguoi="lam")["unseen"] == 1


# ------------------------- tiến trình hiện trên UI ---------------------------
def test_ghi_chuong_dang_dung(tmp_path):
    """Job nhiều chương chạy tuần tự — không ghi chương thì thanh tiến trình lùi
    về 0 mỗi chương mà nhân sự không hiểu vì sao."""
    from autoedit.web import queue as q

    conn = q.connect(tmp_path / "j.db")
    jid = q.add_job(conn, "F:/x", nguoi="a")
    q.set_chuong(conn, jid, "C2 (2/5)")
    assert q.get_job(conn, jid).chuong == "C2 (2/5)"
    assert q.get_job(conn, jid).to_dict()["chuong"] == "C2 (2/5)"


def test_ghi_dong_log_cuoi(tmp_path):
    """30/08: job chạy 20 phút mà UI chỉ ghi 'đang chạy' — không phân biệt được
    CHẬM với TREO. Dòng log gần nhất trả lời đúng câu hỏi đó."""
    from autoedit.web import queue as q

    conn = q.connect(tmp_path / "j.db")
    jid = q.add_job(conn, "F:/x", nguoi="a")
    q.set_dong_cuoi(conn, jid, "  [3/10] beat 2 [stock] steaming plov")
    conn.commit()
    assert "beat 2" in q.get_job(conn, jid).dong_cuoi


def test_dong_log_qua_dai_bi_cat(tmp_path):
    from autoedit.web import queue as q

    conn = q.connect(tmp_path / "j.db")
    jid = q.add_job(conn, "F:/x", nguoi="a")
    q.set_dong_cuoi(conn, jid, "x" * 5000)
    conn.commit()
    assert len(q.get_job(conn, jid).dong_cuoi) <= 300


def test_them_cot_vao_db_cu(tmp_path):
    """DB đang chạy trên máy chủ ĐÃ CÓ dữ liệu: CREATE TABLE IF NOT EXISTS không
    đụng bảng cũ, nên thiếu ALTER là máy chủ vỡ ngay ở SELECT sau khi cập nhật."""
    from autoedit.web import queue as q

    import sqlite3

    p = tmp_path / "cu.db"
    cu = sqlite3.connect(str(p))
    cu.executescript("""
        CREATE TABLE jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, job_folder TEXT NOT NULL,
            project_id TEXT NOT NULL DEFAULT '', nguoi TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'queued', stage TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT, error TEXT,
            seen INTEGER NOT NULL DEFAULT 0, opts TEXT NOT NULL DEFAULT '{}');
        INSERT INTO jobs (job_folder, created_at) VALUES ('F:/cu', '2026-08-30T00:00:00Z');
    """)
    cu.commit()
    cu.close()

    conn = q.connect(p)          # phải migrate được, không vỡ
    job = q.get_job(conn, 1)
    assert job.job_folder == "F:/cu"      # dữ liệu cũ còn nguyên
    assert job.chuong == "" and job.dong_cuoi == ""
    q.set_chuong(conn, 1, "H (1/3)")
    assert q.get_job(conn, 1).chuong == "H (1/3)"


def test_uoc_tinh_align_tinh_ca_whisper():
    """Chương thiếu .srt thì align phải nhận dạng giọng — trước 30/08 ước tính 2 giây
    là của đường đọc .srt, đếm ngược sẽ hứa sai với nhân sự."""
    from autoedit.web import queue as q

    assert q.STAGE_SECONDS["align"] >= 60


def _dat_job(nas_root, status, error="", tuoi_ngay=0):
    """Nhét một job vào hàng đợi với tuổi tự chọn (ngày trước hôm nay)."""
    from autoedit.web import queue as q
    conn = q.connect(nas_root / "jobs.db")
    with conn:
        conn.execute(
            "INSERT INTO jobs (job_folder, project_id, nguoi, status, stage, "
            "created_at, error) VALUES (?,?,?,?,?, datetime('now', ?), ?)",
            (str(nas_root / "tap"), "p1", "tt", status, "",
             f"-{tuoi_ngay} day", error))
    conn.close()


def test_health_job_hong_phai_NANG_TRANG_THAI_khong_chi_in_so(nas):
    """SỰ CỐ 03/09 (Owner hỏi "sao rendery lỗi mà app không báo").

    Nhân sự phải nhắn tay qua chat báo job dựng chết vì GLM hết tiền, trong khi
    tab giám sát vẫn xanh — vì `_hang_doi` ĐỌC RA số job `failed` rồi vẫn trả
    "ok" cứng. Lúc đó DB có 4/7 job hỏng (57%) mà hệ im lặng suốt.

    Ghim ba mức: không hỏng → ok · hỏng nhưng vẫn có job xong → cảnh báo ·
    hỏng mà KHÔNG job nào xong → lỗi (hệ đứt, không phải một job xấu)."""
    from fastapi.testclient import TestClient
    tc = TestClient(srv.app)

    def _hd():
        b = tc.get("/api/suc-khoe").json()
        return next(m for m in b["mo_dun"] if m["ten"] == "viec-hong")

    _dat_job(nas, "done")
    assert _hd()["trang_thai"] == "ok"

    _dat_job(nas, "failed", error="GLM HẾT TIỀN (mã 1113)")
    m = _hd()
    assert m["trang_thai"] == "canh_bao", m
    assert "1113" in m["chi_tiet"], "phải nói LÝ DO, không chỉ đếm số"

    # xóa job done → chỉ còn hỏng
    from autoedit.web import queue as q
    conn = q.connect(nas / "jobs.db")
    with conn:
        conn.execute("DELETE FROM jobs WHERE status='done'")
    conn.close()
    assert _hd()["trang_thai"] == "loi", "hỏng hết mà không báo lỗi = hệ đứt lặng lẽ"


def test_health_job_hong_CU_khong_keu_mai(nas):
    """Job hỏng tuần trước đã xử lý xong thì không được kêu mãi — nếu không,
    người trực quen mắt với màu đỏ và bỏ qua lỗi THẬT hôm nay."""
    from fastapi.testclient import TestClient
    tc = TestClient(srv.app)
    _dat_job(nas, "failed", error="lỗi cũ", tuoi_ngay=5)
    b = tc.get("/api/suc-khoe").json()
    m = next(x for x in b["mo_dun"] if x["ten"] == "viec-hong")
    assert m["trang_thai"] == "ok", m
    so = next(x for x in b["mo_dun"] if x["ten"] == "hang-doi")
    assert "1 lỗi" in so["chi_tiet"], "vẫn hiện tổng tích lũy để tra cứu"


def test_so_hang_doi_KHONG_do_khi_job_nguoi_dung_hong(nas):
    """Hai chuyện KHÁC HẲN, phải là hai module:
      · sổ hỏng   = nộp việc không vào, cả app đứng — hạ tầng, sửa ngay
      · job hỏng  = nhân sự nhập sai / hết tiền API / mạng chập — chuyện thường

    Gộp làm một thì GLM hết tiền cũng kéo module hạ tầng sang đỏ, và canary kiểm
    'sổ đọc được' báo SAI trong khi sổ vẫn đọc tốt (sự cố 03/09)."""
    from fastapi.testclient import TestClient
    tc = TestClient(srv.app)

    _dat_job(nas, "failed", error="GLM HẾT TIỀN (mã 1113)")
    b = tc.get("/api/suc-khoe").json()
    mods = {m["ten"]: m for m in b["mo_dun"]}

    assert mods["hang-doi"]["trang_thai"] == "ok", \
        "sổ vẫn đọc được — job hỏng KHÔNG được kéo hạ tầng sang đỏ"
    assert mods["viec-hong"]["trang_thai"] != "ok", \
        "job hỏng phải nâng trạng thái ở module vận hành"


def test_so_hang_doi_do_khi_db_that_su_hong(nas, monkeypatch):
    """Ngược lại: sổ hỏng THẬT thì module hạ tầng phải đỏ."""
    from fastapi.testclient import TestClient
    tc = TestClient(srv.app)

    def vo(*a, **k):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(srv, "_queue_conn", vo)
    b = tc.get("/api/suc-khoe").json()
    m = next(x for x in b["mo_dun"] if x["ten"] == "hang-doi")
    assert m["trang_thai"] == "loi", m
