"""Một chương lỗi KHÔNG được giết cả tập.

31/08 (job LI093): chương cuối C9 chết vì Pexels trả 504 Gateway Timeout. H, C7, c8
đã dựng xong draft nhưng job bị đánh 'failed' và KHÔNG giao gì — nhân sự chờ 20 phút
để nhận về con số không, rồi nộp lại thì cả 3 chương xong xuôi lại dựng từ đầu.
"""

from __future__ import annotations

from pathlib import Path

from autoedit.web import queue as q
from autoedit.web import worker


def _job(tmp_path, so_chuong=3):
    """Job thật trong DB + thư mục chương giả."""
    conn = q.connect(tmp_path / "jobs.db")
    tap = tmp_path / "LI093"
    for ten in [f"C{i}" for i in range(1, so_chuong + 1)]:
        (tap / "RenderY" / ten).mkdir(parents=True)
    jid = q.add_job(conn, str(tap), nguoi="thanhtran")
    return conn, tap, q.get_job(conn, jid)


def _gia_lap(monkeypatch, ket_qua: dict[str, int], da_chay: list):
    """_run_cli giả: trả mã lỗi theo tên chương. ket_qua = {'C2': 1} -> C2 hỏng."""
    def gia(args, root, log, conn, job_id):
        ten = Path(args[1]).name
        da_chay.append(ten)
        ma = ket_qua.get(ten, 0)
        return ma, f"{ten.lower()}-20260831-000000"      # pid in ra NGAY khi tạo project

    monkeypatch.setattr(worker, "_run_cli", gia)


def _bo_compose(monkeypatch, giao: list):
    """Chặn khâu giao ra NAS, chỉ ghi lại chương nào ĐƯỢC giao."""
    def gia_giao(root, folder, ten_chuong, pid, tom_tat, xong_het, log):
        giao.append(pid)
        tom_tat.append({"ten": ten_chuong})

    monkeypatch.setattr(worker, "_giao_ngay", gia_giao)
    monkeypatch.setattr(worker, "_don_giao", lambda folder, log: None)
    monkeypatch.setattr(worker, "_chot_giao", lambda folder, tom_tat, log: None)


def test_chuong_loi_van_chay_tiep_cac_chuong_sau(tmp_path, monkeypatch):
    conn, tap, job = _job(tmp_path)
    da_chay, giao = [], []
    _gia_lap(monkeypatch, {"C2": 1}, da_chay)
    _bo_compose(monkeypatch, giao)

    worker.run_one(conn, job, tmp_path, tmp_path / "logs")

    assert da_chay == ["C1", "C2", "C3"]          # KHÔNG dừng ở C2
    sau = q.get_job(conn, job.id)
    assert sau.status == "done"                    # có chương xong -> vẫn giao được
    assert "C2" in (sau.error or "")               # nhưng phải nói rõ chương nào hỏng


def test_chuong_loi_khong_bi_giao_ra(tmp_path, monkeypatch):
    """project_id được in NGAY lúc tạo project, nên chương chết giữa chừng cũng có
    pid — giao ra là timeline DỞ nằm lẫn với timeline thật."""
    conn, tap, job = _job(tmp_path)
    da_chay, giao = [], []
    _gia_lap(monkeypatch, {"C2": 1}, da_chay)
    _bo_compose(monkeypatch, giao)

    worker.run_one(conn, job, tmp_path, tmp_path / "logs")

    assert not any("c2" in g for g in giao), f"chương lỗi bị giao: {giao}"
    assert len(giao) == 2


def test_moi_chuong_deu_loi_thi_job_that_bai(tmp_path, monkeypatch):
    conn, tap, job = _job(tmp_path, so_chuong=2)
    da_chay = []
    _gia_lap(monkeypatch, {"C1": 1, "C2": 1}, da_chay)
    _bo_compose(monkeypatch, [])

    worker.run_one(conn, job, tmp_path, tmp_path / "logs")

    sau = q.get_job(conn, job.id)
    assert sau.status == "failed"
    assert "C1" in sau.error and "C2" in sau.error


def test_moi_chuong_xong_thi_khong_bao_loi(tmp_path, monkeypatch):
    conn, tap, job = _job(tmp_path)
    _gia_lap(monkeypatch, {}, [])
    _bo_compose(monkeypatch, [])

    worker.run_one(conn, job, tmp_path, tmp_path / "logs")

    sau = q.get_job(conn, job.id)
    assert sau.status == "done" and not sau.error


# ------------------------- giao dần từng chương ------------------------------
def test_giao_ngay_khi_chuong_xong_khong_doi_ca_tap(tmp_path, monkeypatch):
    """31/08 user hỏi 'C7 C8 đã trả ra kết quả chưa?' — chúng dựng xong từ lâu nhưng
    bước giao chỉ chạy MỘT LẦN ở cuối job, nên phải đợi chương chậm nhất."""
    conn, tap, job = _job(tmp_path, so_chuong=3)
    thu_tu = []

    def gia_giao(root, folder, ten_chuong, pid, tom_tat, xong_het, log):
        thu_tu.append((ten_chuong, xong_het))
        tom_tat.append({"ten": ten_chuong})

    monkeypatch.setattr(worker, "_giao_ngay", gia_giao)
    monkeypatch.setattr(worker, "_don_giao", lambda folder, log: None)
    monkeypatch.setattr(worker, "_chot_giao", lambda folder, tom_tat, log: None)
    _gia_lap(monkeypatch, {}, [])

    worker.run_one(conn, job, tmp_path, tmp_path / "logs")

    # giao NGAY sau mỗi chương, theo đúng thứ tự
    assert [t for t, _ in thu_tu] == ["C1", "C2", "C3"]
    # chỉ chương CUỐI mới đánh dấu 'xong hết' -> README trước đó ghi ĐANG CHẠY
    assert [x for _, x in thu_tu] == [False, False, True]


def test_chuong_cuoi_loi_thi_chot_lai_readme(tmp_path, monkeypatch):
    """C3 lỗi -> README đang ghi 'ĐANG CHẠY' vì C2 chưa phải chương cuối. Phải viết
    lại lần cuối, không thì nhân sự tưởng còn chương sắp về."""
    conn, tap, job = _job(tmp_path, so_chuong=3)
    da_chot = []

    monkeypatch.setattr(worker, "_giao_ngay",
                        lambda root, folder, ten, pid, tt, xong_het, log: tt.append({"ten": ten}))
    monkeypatch.setattr(worker, "_don_giao", lambda folder, log: None)
    monkeypatch.setattr(worker, "_chot_giao",
                        lambda folder, tom_tat, log: da_chot.append(len(tom_tat)))
    _gia_lap(monkeypatch, {"C3": 1}, [])

    worker.run_one(conn, job, tmp_path, tmp_path / "logs")

    assert da_chot == [2]      # chốt lại với 2 chương đã giao


def test_don_thu_muc_giao_mot_lan_truoc_khi_chay(tmp_path, monkeypatch):
    """Dọn kết quả lần trước đúng MỘT lần: dọn mỗi chương là xoá chương vừa giao."""
    conn, tap, job = _job(tmp_path, so_chuong=3)
    so_lan_don = []

    monkeypatch.setattr(worker, "_don_giao",
                        lambda folder, log: so_lan_don.append(1))
    monkeypatch.setattr(worker, "_giao_ngay",
                        lambda root, folder, ten, pid, tt, xong_het, log: None)
    monkeypatch.setattr(worker, "_chot_giao", lambda folder, tom_tat, log: None)
    _gia_lap(monkeypatch, {}, [])

    worker.run_one(conn, job, tmp_path, tmp_path / "logs")

    assert so_lan_don == [1]
