"""Đợt 2 (08/09) — preview là hàng TẠM của một tập, đóng job thì dọn.

User chốt: *"ngoài ref, tôi không cần lưu vĩnh viễn cái gì cả... stock nào đã
được download tức là đã được dùng thì giữ lại, nhưng phải đúng từ khóa"* và
*"user đóng job — xóa"*.

Nút thắt đo được 07/09: bảng `phien_hut` chỉ có (tu_khoa, nguon, so_moi,
so_trung, ts) — KHÔNG biết lượt hút thuộc tập nào, nên không có đường nào tìm
lại mà dọn. Cột `tam_tap` trên `clip` là dấu "hàng tạm của tập X".
"""

from __future__ import annotations

import pytest


@pytest.fixture
def conn(tmp_path, monkeypatch):
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    c = sdb.mo()
    yield c
    c.close()


def test_hut_lai_KHONG_duoc_xoa_path_local(conn, tmp_path):
    """Nhánh UPDATE của `them_clip` ghi đè MỌI cột bằng dữ liệu lượt hút, mà
    lượt hút không mang `path_local` — hút lại một clip ĐÃ TẢI là mất đường dẫn
    file 400MB nằm trên đĩa. Luật giữ/xoá của đợt 2 dựa vào đúng cột này."""
    from autoedit.sotra import db as sdb

    f = tmp_path / "da_tai.mp4"
    f.write_bytes(b"x" * 20)
    sdb.them_clip(conn, {"id": "envato:a", "nguon": "envato", "tieu_de": "cho kabul",
                         "path_local": str(f)})
    sdb.them_clip(conn, {"id": "envato:a", "nguon": "envato", "tieu_de": "cho kabul",
                         "url_video": "http://preview"})      # lượt hút sau
    r = conn.execute("SELECT path_local FROM clip WHERE id='envato:a'").fetchone()
    assert r["path_local"] == str(f), "hút lại đã xoá mất đường dẫn bản đã tải"


def test_them_clip_luu_tam_tap(conn):
    from autoedit.sotra import db as sdb

    sdb.them_clip(conn, {"id": "pexels:1", "nguon": "pexels", "tam_tap": "LI103"})
    r = conn.execute("SELECT tam_tap FROM clip WHERE id='pexels:1'").fetchone()
    assert r["tam_tap"] == "LI103"


def test_hut_lai_clip_VINH_VIEN_khong_bien_thanh_hang_tam(conn):
    """Clip đã nằm kho vĩnh viễn (ref, hoặc stock đã tải) mà lượt hút của tập
    sau chạm phải thì KHÔNG được đóng dấu tạm — đóng job là mất hàng thật."""
    from autoedit.sotra import db as sdb

    sdb.them_clip(conn, {"id": "pexels:1", "nguon": "pexels", "tieu_de": "cho"})
    sdb.them_clip(conn, {"id": "pexels:1", "nguon": "pexels", "tieu_de": "cho",
                         "tam_tap": "LI103"})
    r = conn.execute("SELECT tam_tap FROM clip WHERE id='pexels:1'").fetchone()
    assert r["tam_tap"] == "", "clip vĩnh viễn bị hạ xuống hàng tạm"


def test_phien_hut_dong_dau_tap(conn, monkeypatch):
    """Hút trong lúc dựng tập nào thì clip mới mang dấu tập đó, và sổ lượt hút
    cũng ghi lại — không có dấu thì sau này không tìm đường mà dọn."""
    from autoedit.sotra import hut

    monkeypatch.setattr(hut, "_BO_HUT", {"pexels": lambda tk, tr: [
        {"id": "pexels:9", "nguon": "pexels", "tieu_de": "kabul market"}]})
    monkeypatch.setattr(hut.time, "sleep", lambda *a: None)
    hut.phien_hut(conn, ["kabul market"], ["pexels"], ma_tap="LI103")

    r = conn.execute("SELECT tam_tap FROM clip WHERE id='pexels:9'").fetchone()
    assert r["tam_tap"] == "LI103"
    p = conn.execute("SELECT ma_tap FROM phien_hut").fetchone()
    assert p["ma_tap"] == "LI103"


def test_hut_khong_co_tap_thi_khong_dong_dau(conn, monkeypatch):
    """Hút nghiên cứu từ trang Sổ Tra (không gắn tập nào) vẫn vào kho như cũ."""
    from autoedit.sotra import hut

    monkeypatch.setattr(hut, "_BO_HUT", {"pexels": lambda tk, tr: [
        {"id": "pexels:9", "nguon": "pexels", "tieu_de": "kabul market"}]})
    monkeypatch.setattr(hut.time, "sleep", lambda *a: None)
    hut.phien_hut(conn, ["kabul market"], ["pexels"])

    r = conn.execute("SELECT tam_tap FROM clip WHERE id='pexels:9'").fetchone()
    assert r["tam_tap"] == ""


def test_dong_job_don_hang_tam_dung_pham_vi(conn, tmp_path):
    """Đóng job xoá hàng tạm CỦA TẬP ĐÓ và chỉ những clip CHƯA tải.

    Giữ lại: clip đã tải (`path_local`) vì "đã download tức là đã được dùng";
    clip của tập khác; clip vĩnh viễn không mang dấu tạm.
    """
    from autoedit.sotra import db as sdb

    f = tmp_path / "da_tai.mp4"
    f.write_bytes(b"x" * 20)
    sdb.them_clip(conn, {"id": "pexels:tam", "nguon": "pexels", "tam_tap": "LI103"})
    sdb.them_clip(conn, {"id": "pexels:datai", "nguon": "pexels", "tam_tap": "LI103",
                         "path_local": str(f)})
    sdb.them_clip(conn, {"id": "pexels:tapkhac", "nguon": "pexels", "tam_tap": "LI104"})
    sdb.them_clip(conn, {"id": "ref:LI103-r:0", "nguon": "ref", "tap": "LI103"})
    conn.commit()

    n = sdb.dong_job(conn, "LI103")
    con = {r[0] for r in conn.execute("SELECT id FROM clip")}
    assert n == 1
    assert con == {"pexels:datai", "pexels:tapkhac", "ref:LI103-r:0"}
    # FTS phải dọn theo, nếu không khay còn trả về clip đã xoá
    assert conn.execute("SELECT COUNT(*) FROM clip_fts WHERE id='pexels:tam'"
                        ).fetchone()[0] == 0


def test_dong_job_khong_dung_den_giay_phep(conn):
    """`giay_phep` là chứng từ đã trả tiền — dọn kho không được đụng."""
    from autoedit.sotra import db as sdb

    conn.execute("INSERT INTO giay_phep(clip_id, url_item, ten_file, ngay) "
                 "VALUES('envato:x','http://i','f.mp4','2026-09-01')")
    sdb.them_clip(conn, {"id": "envato:x", "nguon": "envato", "tam_tap": "LI103"})
    conn.commit()
    sdb.dong_job(conn, "LI103")
    assert conn.execute("SELECT COUNT(*) FROM giay_phep").fetchone()[0] == 1


def test_dong_job_giu_clip_DA_LEN_FINAL(conn):
    """Pexels/Pixabay tải thẳng vào assets của project chứ không đặt
    `path_local` trên clip — nên "đã được dùng" phải đọc từ sổ sự kiện
    `len_final`, nếu không clip vừa lên timeline đã bị dọn mất."""
    from autoedit.sotra import db as sdb

    sdb.them_clip(conn, {"id": "pexels:dung", "nguon": "pexels", "tam_tap": "LI103"})
    sdb.them_clip(conn, {"id": "pexels:thua", "nguon": "pexels", "tam_tap": "LI103"})
    sdb.ghi_su_kien(conn, "pexels:dung", "len_final", tap="LI103", vi_tri=1.0)
    conn.commit()

    assert sdb.dong_job(conn, "LI103") == 1
    con = {r[0] for r in conn.execute("SELECT id FROM clip")}
    assert con == {"pexels:dung"}


# --------------------------------------------------------------- API đóng job

@pytest.fixture
def may_chu(tmp_path, monkeypatch):
    """Máy chủ web với sổ hàng đợi + Sổ Tra RIÊNG trong tmp."""
    import json

    from fastapi.testclient import TestClient

    from autoedit.sotra import db as sdb
    from autoedit.web import queue as q, server

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    monkeypatch.setattr(server, "ROOT", tmp_path)
    pdir = tmp_path / "projects" / "h-test"
    pdir.mkdir(parents=True)
    (pdir / "offline.json").write_text(
        json.dumps({"ma_tap": "LI103", "khoi": [], "hinh": []}), encoding="utf-8")
    monkeypatch.setattr(server, "PROJECTS_DIR", pdir.parent)

    c = sdb.mo()
    sdb.them_clip(c, {"id": "pexels:tam", "nguon": "pexels", "tam_tap": "LI103"})
    c.commit()
    c.close()

    qc = q.connect(tmp_path / "jobs.db")
    jid = q.add_job(qc, str(tmp_path / "kho" / "LI103"), nguoi="")
    qc.execute("UPDATE jobs SET project_id=? WHERE id=?", ("h-test", jid))
    qc.commit()
    q.finish(qc, jid, ok=True)
    qc.close()
    return TestClient(server.app), jid, tmp_path


def test_api_dong_job_don_hang_tam(may_chu):
    from autoedit.sotra import db as sdb

    tc, jid, tmp = may_chu
    r = tc.post(f"/api/jobs/{jid}/dong")
    assert r.status_code == 200, r.text
    assert r.json()["so_clip_don"] == 1
    c = sdb.mo()
    assert c.execute("SELECT COUNT(*) FROM clip").fetchone()[0] == 0
    c.close()


def test_api_dong_job_lan_hai_khong_don_nua(may_chu):
    tc, jid, _ = may_chu
    assert tc.post(f"/api/jobs/{jid}/dong").status_code == 200
    r = tc.post(f"/api/jobs/{jid}/dong")
    assert r.status_code == 409


def test_api_dong_job_khong_co_thi_404(may_chu):
    tc, _, _ = may_chu
    assert tc.post("/api/jobs/9999/dong").status_code == 404


def test_giao_dien_co_nut_dong_job():
    from pathlib import Path

    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    assert "dongJob(" in h and "/dong" in h, "danh sách job ngoài Overview chưa có nút đóng"


def test_moi_ham_onclick_deu_ton_tai():
    """Máy này KHÔNG có Node (METHODOLOGY BH3) nên JS không chạy được trong
    test — gọi một hàm không tồn tại thì nút im lặng chết dưới tay người dùng.
    Rào tĩnh: mọi `onclick="ten(...)"` phải có `function ten(` trong file.

    Bắt được thật 08/09: nút "đóng job" gọi `toast()` — cả file chỉ có
    `toastOf()`, bấm là ReferenceError.
    """
    import re
    from pathlib import Path

    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    goi = set(re.findall(r'onclick="([A-Za-z_$][\w$]*)\(', h))
    goi |= set(re.findall(r"onclick=\?\"?([A-Za-z_$][\w$]*)\(", h))
    co = set(re.findall(r"(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(", h))
    co |= set(re.findall(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(", h))
    tu_khoa = {"if", "for", "while", "switch", "return", "typeof", "new"}
    thieu = sorted(goi - co - tu_khoa)
    assert not thieu, f"onclick gọi hàm không tồn tại: {thieu}"


# ------------------------------------------------- dọn kho một lần (việc 5)

def test_lech_tu_khoa_nhan_dien_dung():
    """Clip đã tải phải ĐÚNG TỪ KHOÁ đã hút, nếu không thì giữ lại vô nghĩa."""
    from autoedit.sotra.don_kho import lech_tu_khoa

    assert not lech_tu_khoa("Busy Outdoor Street Market", "street market")
    assert not lech_tu_khoa("Women Weaving Fabric", "women weaving")
    assert not lech_tu_khoa("Crowded markets in Kabul", "market")   # gốc từ
    assert lech_tu_khoa("Sixth street in New York City", "kabul bazaar")
    assert not lech_tu_khoa("bất kỳ", ""), "không có từ khoá thì không kết tội"


def test_don_preview_envato_giu_dung_thu_can_giu(conn, tmp_path):
    """Xoá dòng CHỈ-LÀ-PREVIEW; giữ clip đã tải, đã lên timeline, có giấy phép."""
    from autoedit.sotra import db as sdb
    from autoedit.sotra.don_kho import don_preview

    f = tmp_path / "a.mp4"
    f.write_bytes(b"x" * 20)
    sdb.them_clip(conn, {"id": "envato:preview", "nguon": "envato"})
    sdb.them_clip(conn, {"id": "envato:datai", "nguon": "envato", "path_local": str(f)})
    sdb.them_clip(conn, {"id": "envato:dadung", "nguon": "envato"})
    sdb.them_clip(conn, {"id": "envato:cogp", "nguon": "envato"})
    sdb.them_clip(conn, {"id": "pexels:1", "nguon": "pexels"})     # nguồn khác
    sdb.ghi_su_kien(conn, "envato:dadung", "len_final", tap="LI103")
    conn.execute("INSERT INTO giay_phep(clip_id, url_item, ten_file, ngay) "
                 "VALUES('envato:cogp','u','f.mp4','2026-09-01')")
    conn.commit()

    assert don_preview(conn, xoa=False) == 1, "chế độ thử không được đếm sai"
    assert conn.execute("SELECT COUNT(*) FROM clip").fetchone()[0] == 5, "thử mà đã xoá"
    assert don_preview(conn, xoa=True) == 1
    con = {r[0] for r in conn.execute("SELECT id FROM clip")}
    assert con == {"envato:datai", "envato:dadung", "envato:cogp", "pexels:1"}


def test_don_lech_tu_khoa_chi_dung_clip_DA_TAI(conn, tmp_path):
    """Chỉ soi clip đã tải: preview lệch từ khoá thì đằng nào cũng bị dọn."""
    from autoedit.sotra import db as sdb
    from autoedit.sotra.don_kho import don_lech_tu_khoa

    f = tmp_path / "a.mp4"
    f.write_bytes(b"x" * 20)
    sdb.them_clip(conn, {"id": "envato:khop", "nguon": "envato", "path_local": str(f),
                         "tieu_de": "Busy Street Market", "tu_khoa_hut": "street market"})
    sdb.them_clip(conn, {"id": "envato:lech", "nguon": "envato", "path_local": str(f),
                         "tieu_de": "Sixth street in New York", "tu_khoa_hut": "kabul bazaar"})
    conn.commit()

    assert don_lech_tu_khoa(conn, xoa=True) == 1
    con = {r[0] for r in conn.execute("SELECT id FROM clip")}
    assert con == {"envato:khop"}
