# -*- coding: utf-8 -*-
"""RenderY: job KHÔNG CÓ CHỦ (nguoi='') hiện cho MỌI người (05/09/2026).

SỰ CỐ: user báo "mất lịch sử, danh sách job trống trơn". Điều tra: jobs.db còn
đủ 17 job (KHÔNG mất) nhưng list_jobs(nguoi=X) chỉ khớp job của X — bỏ qua job
nguoi='' (job chạy trực tiếp / trước SSO / job hệ thống). Người đăng nhập tên
khác chủ job → thấy TRỐNG dù dữ liệu còn.

Job không có chủ vốn không thuộc riêng ai → phải hiện cho mọi người. Job CÓ chủ
vẫn chỉ chủ (và admin xem hết) thấy — giữ tính riêng tư.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autoedit.web import queue as q


def _db(tmp_path):
    conn = q.connect(tmp_path / "jobs.db")
    return conn


def _them(conn, nguoi):
    conn.execute("INSERT INTO jobs (job_folder, project_id, nguoi, status, stage, created_at) "
                 "VALUES (?,?,?,?,?,?)", ("F:/x", "", nguoi, "done", "", "2026-09-05"))
    conn.commit()


def test_nguoi_thay_job_cua_minh_VA_job_khong_chu(tmp_path):
    conn = _db(tmp_path)
    _them(conn, "thanhtran")     # job có chủ
    _them(conn, "")              # job không chủ (chạy trực tiếp)
    _them(conn, "nguoikhac")     # job người khác
    jobs = q.list_jobs(conn, nguoi="thanhtran")
    chu = sorted(j.nguoi for j in jobs)
    assert chu == ["", "thanhtran"], f"phải thấy job mình + job không chủ, được: {chu}"


def test_nguoi_moi_van_thay_job_khong_chu(tmp_path):
    """Người đăng nhập chưa từng có job vẫn thấy job hệ thống (hết TRỐNG TRƠN)."""
    conn = _db(tmp_path)
    _them(conn, "")
    _them(conn, "")
    jobs = q.list_jobs(conn, nguoi="nguoimoi")
    assert len(jobs) == 2, f"người mới phải thấy 2 job không chủ, được: {len(jobs)}"


def test_admin_xem_het_van_thay_tat_ca(tmp_path):
    conn = _db(tmp_path)
    _them(conn, "a"); _them(conn, "b"); _them(conn, "")
    assert len(q.list_jobs(conn, nguoi="")) == 3
