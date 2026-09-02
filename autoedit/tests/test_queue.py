"""Test hàng đợi job (RenderY — tích hợp CRM).

Hàng đợi phải BỀN qua restart: CRM runbook ghi rõ "sửa code xong phải Stop rồi Start
lại tác vụ", nên mất hàng đợi khi restart là mất việc của nhân sự. Test khoá:
nhận job không tranh chấp, trần MAX_WORKERS, trả job mồ côi, và đếm ngược.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

import pytest

from autoedit.web import queue as q


@pytest.fixture
def conn(tmp_path):
    c = q.connect(tmp_path / "jobs.db")
    yield c
    c.close()


# ------------------------------ thêm / đọc ----------------------------------
def test_them_job_va_doc_lai(conn):
    jid = q.add_job(conn, r"\\NAS\Video\RenderY\_INBOX\LI070", nguoi="lam",
                    opts={"niche": "life-in"})
    job = q.get_job(conn, jid)
    assert job.status == "queued" and job.nguoi == "lam"
    assert job.opts == {"niche": "life-in"}
    assert job.stage == "" and job.started_at is None


def test_folder_rong_bao_loi(conn):
    with pytest.raises(ValueError, match="Thiếu đường dẫn"):
        q.add_job(conn, "   ")


def test_job_khong_ton_tai_tra_none(conn):
    assert q.get_job(conn, 999) is None


def test_liet_ke_moi_nhat_truoc(conn):
    for i in range(3):
        q.add_job(conn, f"/f/{i}", nguoi="lam")
    assert [j.job_folder for j in q.list_jobs(conn)] == ["/f/2", "/f/1", "/f/0"]


def test_loc_theo_nguoi(conn):
    q.add_job(conn, "/a", nguoi="lam")
    q.add_job(conn, "/b", nguoi="hoa")
    assert [j.nguoi for j in q.list_jobs(conn, nguoi="hoa")] == ["hoa"]
    assert len(q.list_jobs(conn)) == 2          # rỗng = mọi người


# ------------------------------ nhận job ------------------------------------
def test_nhan_job_theo_thu_tu_vao(conn):
    a = q.add_job(conn, "/a")
    b = q.add_job(conn, "/b")
    assert q.claim_next(conn).id == a
    assert q.claim_next(conn).id == b


def test_hang_doi_rong_tra_none(conn):
    assert q.claim_next(conn) is None


def test_ton_trong_tran_max_workers(conn):
    """Quá MAX_WORKERS job đang chạy -> không nhận thêm, dù hàng đợi còn."""
    for _ in range(q.MAX_WORKERS + 2):
        q.add_job(conn, "/x")
    nhan = [q.claim_next(conn) for _ in range(q.MAX_WORKERS + 2)]
    assert sum(1 for j in nhan if j is not None) == q.MAX_WORKERS
    assert q.MAX_WORKERS == 2                    # đo thật 30/08/2026


def test_xong_1_job_thi_nhan_duoc_job_ke(conn):
    for _ in range(q.MAX_WORKERS + 1):
        q.add_job(conn, "/x")
    dau = [q.claim_next(conn) for _ in range(q.MAX_WORKERS)]
    assert q.claim_next(conn) is None            # đã đầy
    q.finish(conn, dau[0].id, ok=True)
    assert q.claim_next(conn) is not None        # nhả 1 suất


def test_hai_worker_khong_cung_nhan_1_job(conn, tmp_path):
    """Chống tranh chấp — 2 worker song song, mỗi job chỉ 1 người nhận."""
    for _ in range(2):
        q.add_job(conn, "/x")
    got: list = []
    lock = threading.Lock()

    def worker():
        c = q.connect(tmp_path / "jobs.db")
        j = q.claim_next(c)
        if j is not None:
            with lock:
                got.append(j.id)
        c.close()

    ts = [threading.Thread(target=worker) for _ in range(6)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert len(got) == len(set(got))             # không id nào bị nhận 2 lần
    assert len(got) <= q.MAX_WORKERS


# ------------------------------ kết thúc ------------------------------------
def test_finish_thanh_cong(conn):
    jid = q.add_job(conn, "/a", nguoi="lam")
    q.claim_next(conn)
    q.finish(conn, jid, ok=True, project_id="li070-20260830")
    job = q.get_job(conn, jid)
    assert job.status == "done" and job.project_id == "li070-20260830"
    assert job.finished_at and job.seen == 0     # chưa xem -> badge sáng


def test_finish_that_bai_giu_loi(conn):
    jid = q.add_job(conn, "/a")
    q.claim_next(conn)
    q.finish(conn, jid, ok=False, error="thiếu voice")
    job = q.get_job(conn, jid)
    assert job.status == "failed" and "thiếu voice" in job.error


def test_finish_khong_xoa_project_id_cu(conn):
    """project_id rỗng ở lần ghi sau không được xoá giá trị đã có."""
    jid = q.add_job(conn, "/a")
    q.finish(conn, jid, ok=True, project_id="p1")
    q.finish(conn, jid, ok=True, project_id="")
    assert q.get_job(conn, jid).project_id == "p1"


def test_huy_job_chua_chay(conn):
    jid = q.add_job(conn, "/a")
    assert q.cancel(conn, jid) is True
    assert q.get_job(conn, jid).status == "canceled"


def test_khong_huy_duoc_job_dang_chay(conn):
    """Tiến trình con đã spawn — huỷ trong sổ là nói dối."""
    jid = q.add_job(conn, "/a")
    q.claim_next(conn)
    assert q.cancel(conn, jid) is False
    assert q.get_job(conn, jid).status == "running"


# ------------------------------ badge ---------------------------------------
def test_dem_job_xong_chua_xem(conn):
    for _ in range(2):
        jid = q.add_job(conn, "/a", nguoi="lam")
        q.finish(conn, jid, ok=True)
    q.finish(conn, q.add_job(conn, "/b", nguoi="hoa"), ok=False)

    assert q.count_unseen(conn, "lam") == 2
    assert q.count_unseen(conn, "hoa") == 1      # job lỗi cũng cần báo
    assert q.count_unseen(conn) == 3


def test_job_dang_cho_khong_tinh_vao_badge(conn):
    q.add_job(conn, "/a", nguoi="lam")
    assert q.count_unseen(conn, "lam") == 0


def test_xem_roi_thi_tat_badge(conn):
    jid = q.add_job(conn, "/a", nguoi="lam")
    q.finish(conn, jid, ok=True)
    assert q.mark_seen(conn, "lam") == 1
    assert q.count_unseen(conn, "lam") == 0


def test_xem_cua_nguoi_khac_khong_anh_huong(conn):
    q.finish(conn, q.add_job(conn, "/a", nguoi="lam"), ok=True)
    q.mark_seen(conn, "hoa")
    assert q.count_unseen(conn, "lam") == 1


# ------------------------------ mồ côi --------------------------------------
def test_tra_job_mo_coi_ve_hang_doi(conn):
    """Server Stop/Start giết tiến trình con -> job kẹt 'running' vĩnh viễn."""
    jid = q.add_job(conn, "/a")
    q.claim_next(conn)
    q.set_stage(conn, jid, "source")
    assert q.requeue_orphans(conn) == 1

    job = q.get_job(conn, jid)
    assert job.status == "queued"
    assert job.started_at is None and job.stage == ""   # dọn sạch để chạy lại từ đầu


def test_khong_dung_den_job_da_xong(conn):
    q.finish(conn, q.add_job(conn, "/a"), ok=True)
    q.add_job(conn, "/b")
    assert q.requeue_orphans(conn) == 0


# ------------------------------ đếm ngược -----------------------------------
def test_tien_do_tinh_theo_THOI_LUONG_khong_phai_so_stage(conn):
    """Stage `source` chiếm 64% thời gian — đếm đầu stage sẽ sai nặng."""
    jid = q.add_job(conn, "/a")
    q.claim_next(conn)

    q.set_stage(conn, jid, "cut")        # xong align+direct+enrich = 122/1467s
    p_cut = q.get_job(conn, jid).progress()
    q.set_stage(conn, jid, "rank")       # xong thêm cả source (900s)
    p_rank = q.get_job(conn, jid).progress()

    assert 0.05 < p_cut < 0.15           # mới ~8%, dù đã qua 3/9 stage
    assert p_rank > 0.7                  # qua source là nhảy vọt


def test_tien_do_bien():
    from types import SimpleNamespace

    def job(**kw):
        d = dict(id=1, job_folder="/a", project_id="", nguoi="", status="queued",
                 stage="", created_at="", started_at=None, finished_at=None,
                 error=None, seen=0, opts={})
        d.update(kw)
        return q.Job(**d)

    assert job(status="done").progress() == 1.0
    assert job(status="queued").progress() == 0.0
    assert job(status="failed", stage="cut").progress() == 0.0
    assert job(status="running", stage="stage-la").progress() == 0.0


def test_eta_chi_co_khi_dang_chay(conn):
    jid = q.add_job(conn, "/a")
    assert q.get_job(conn, jid).eta() is None        # đang xếp hàng
    q.claim_next(conn)
    q.set_stage(conn, jid, "source")
    assert q.get_job(conn, jid).eta() is not None
    q.finish(conn, jid, ok=True)
    assert q.get_job(conn, jid).eta() is None        # đã xong


def test_eta_giam_theo_thoi_gian_da_chay(conn):
    jid = q.add_job(conn, "/a")
    q.claim_next(conn)
    q.set_stage(conn, jid, "rank")                   # ~75% xong
    # giả lập đã chạy 10 phút
    t0 = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    conn.execute("UPDATE jobs SET started_at=? WHERE id=?", (t0, jid))
    conn.commit()
    eta = q.get_job(conn, jid).eta()
    assert 0 <= eta < q.TOTAL_SECONDS                # còn ít hơn tổng


# ------------------------------ chờ hàng đợi --------------------------------
def test_uoc_thoi_gian_cho_khi_xep_hang(conn):
    for _ in range(q.MAX_WORKERS):
        q.claim_next(conn) if q.add_job(conn, "/x") else None
    cho = q.add_job(conn, "/cho")
    assert q.wait_ahead(conn, cho) >= q.TOTAL_SECONDS


def test_job_dau_tien_khong_phai_cho(conn):
    assert q.wait_ahead(conn, q.add_job(conn, "/a")) == 0


def test_job_dang_chay_khong_co_wait(conn):
    jid = q.add_job(conn, "/a")
    q.claim_next(conn)
    assert q.wait_ahead(conn, jid) is None


# ------------------------------ thống kê ------------------------------------
def test_thong_ke(conn):
    q.add_job(conn, "/a")
    q.claim_next(conn)
    q.add_job(conn, "/b")
    st = q.stats(conn)
    assert st["running"] == 1 and st["queued"] == 1
    assert st["workers"] == q.MAX_WORKERS


def test_thong_ke_so_rong(conn):
    st = q.stats(conn)
    assert st["queued"] == 0 and st["running"] == 0


# ------------------------------ chia chương ---------------------------------
def _chuong(d, ten, script=True, voice=True):
    c = d / ten
    c.mkdir(parents=True)
    if script:
        (c / "script.txt").write_text("x", encoding="utf-8")
    if voice:
        (c / "voice.mp3").write_bytes(b"\x00")
    return c


def test_worker_lay_chuong_DUNG_THU_TU_H_C_E(tmp_path):
    """`chapters_of` phải theo thứ tự H → C1..Cn → E, không phải A-Z.

    Mỗi chương 1 lượt `make` -> 1 draft riêng, rồi gộp theo đúng thứ tự này.
    Sai thứ tự = dựng lại cả tập. (Chi tiết nhận diện tên: test_chapters.py)
    """
    from autoedit.web.chapters import THU_MUC_CON
    from autoedit.web.worker import chapters_of

    job = tmp_path / "IN002"
    for ten in ("E", "C10", "C2", "H", "C1"):
        _chuong(job / THU_MUC_CON, ten)
    assert [c.name for c in chapters_of(job)] == ["H", "C1", "C2", "C10", "E"]


def test_worker_bo_qua_thu_muc_sai_quy_uoc(tmp_path):
    """`footage/`, `.tam/`, tên cũ `ch01` — không phải chương, bỏ qua."""
    from autoedit.web.chapters import THU_MUC_CON
    from autoedit.web.worker import chapters_of

    job = tmp_path / "IN002"
    _chuong(job / THU_MUC_CON, "H")
    _chuong(job / THU_MUC_CON, "ch01")          # tên cũ, sai quy ước
    (job / THU_MUC_CON / "footage").mkdir()
    (job / THU_MUC_CON / ".tam").mkdir()
    assert [c.name for c in chapters_of(job)] == ["H"]


def test_hai_worker_cung_luc_khong_vuot_tran(tmp_path):
    """RÀ 02/09 (hệ kiểm logic OUTLIERY): đếm running và UPDATE nằm NGOÀI một
    câu lệnh → hai worker cùng đọc running=1, cả hai thấy còn suất, cùng claim
    hai job KHÁC nhau = 3 job chạy song song, vượt trần MAX_WORKERS.

    Hậu quả thật: mỗi job dựng cả tập (ffmpeg + LLM). Vượt trần là máy chủ
    nghẽn — nhìn từ ngoài chỉ thấy "dựng chậm", không ai truy ra nguyên nhân.

    Test ép ĐÚNG khoảnh khắc đó (hai connection cùng đọc trước khi ai ghi),
    không dựa vào may rủi của thread — race hiếm khi lộ nếu chạy tự nhiên.
    """
    duong = tmp_path / "jobs.db"
    c0 = q.connect(duong)
    for i in range(4):
        q.add_job(c0, f"/tap{i}")
    c0.execute("UPDATE jobs SET status='running', started_at=? WHERE id=1",
               (q._now(),))          # đã 1 job chạy → còn đúng 1 suất
    c0.commit()
    c0.close()

    # Ép ĐÚNG khoảnh khắc: cả hai worker ĐỌC trước khi bất kỳ ai GHI.
    # Chèn rào vào giữa bước đếm và bước UPDATE của claim_next.
    ca, cb = q.connect(duong), q.connect(duong)
    rao_doc = threading.Barrier(2)
    ket = []

    def worker(conn):
        goc = conn.execute

        def execute_cham(sql, *a, **k):
            r = goc(sql, *a, **k)
            if "COUNT(*)" in sql and "running" in sql:
                rao_doc.wait(timeout=5)   # cả hai đọc xong mới cho ai ghi
            return r

        conn.execute = execute_cham
        try:
            ket.append(q.claim_next(conn))
        finally:
            conn.execute = goc

    ts = [threading.Thread(target=worker, args=(c,)) for c in (ca, cb)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=10)
    try:
        dang_chay = ca.execute(
            "SELECT COUNT(*) c FROM jobs WHERE status='running'").fetchone()["c"]
    finally:
        ca.close()
        cb.close()
    assert dang_chay <= q.MAX_WORKERS, (
        f"{dang_chay} job running > trần {q.MAX_WORKERS} — claim_next có race")
    # Điều quan trọng là KHÔNG VƯỢT TRẦN. Worker thua cuộc trả None và sẽ gọi
    # lại ở vòng sau — chấp nhận được, rẻ hơn nhiều so với khoá tường minh.
    assert sum(1 for x in ket if x is not None) <= 1
