"""Ai NỘP TẬP — tra sai thì người khác thành chủ sequence (user báo 09/09).

Triệu chứng: tập `LI106_Hai` do **haint** (Hải) nộp, nhưng màn Offline ghi
`hieuvn` và Hải bị chặn "CHỈ XEM — sequence này do «hieuvn» nộp".

Đo trên dữ liệu thật, HAI lỗi chồng nhau:

1. Tra theo `project_id=?` KHÔNG BAO GIỜ khớp với job nộp cả tập: cột đó ghi
   **chuỗi nối 16 mã** (`h-2026...,c1-2026...,c2-...`), còn câu truy vấn so
   bằng dấu `=`.

2. Nhánh dự phòng lấy `thu_muc_nas.parent.parent.name` — đúng với bố cục thư
   mục con (`LI103/Rendery/H` -> `LI103`) nhưng SAI với bố cục phẳng
   (`LI106_Hai/RenderY` -> **`US`**). Rồi `job_folder LIKE '%US%'` khớp **16
   job của mọi tập**, lấy mới nhất -> job 27 của `hieuvn`, tập LI102.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest


def _jobs_db(f: Path, rows: list[tuple[str, str, str]]) -> sqlite3.Connection:
    """rows: (job_folder, nguoi, project_id) — theo thứ tự id tăng dần."""
    from autoedit.web import queue as q

    conn = q.connect(f)
    for folder, nguoi, pid in rows:
        cur = conn.execute(
            "INSERT INTO jobs(job_folder, nguoi, created_at, opts, project_id) "
            "VALUES(?,?,?,?,?)", (folder, nguoi, "2026-09-08T00:00:00", "{}", pid))
    conn.commit()
    return conn


def _project(tmp: Path, pid: str, script: str) -> Path:
    d = tmp / "projects" / pid
    d.mkdir(parents=True)
    (d / "project.json").write_text(json.dumps({
        "project_id": pid, "title": pid, "created_at": "2026-09-08T00:00:00",
        "project_dir": str(d),
        "inputs": {"script_path": script, "voice_path": script,
                   "original_script_path": script, "original_voice_path": script,
                   "script_text": "x"}}), encoding="utf-8")
    return d


NAS = r"F:\OutlierY Nas 2\Life In\US"


def test_bo_cuc_PHANG_khong_duoc_vo_nguoi_cua_tap_khac(tmp_path):
    """Đúng ca LI106_Hai: job của Hải không khớp `project_id`, và nhánh dự
    phòng phải KHÔNG được vớ job mới nhất của tập khác."""
    from autoedit.web.server import nguoi_nop_tap

    d = _project(tmp_path, "h-2026", rf"{NAS}\LI106_Hai\RenderY\H.txt")
    conn = _jobs_db(tmp_path / "jobs.db", [
        (rf"{NAS}\LI106_Hai", "haint", "h-2026,c1-2026,c2-2026"),
        (rf"{NAS}\LI102\Tool", "hieuvn", "h-9999"),          # job MỚI HƠN, tập khác
    ])
    try:
        assert nguoi_nop_tap(d, conn) == "haint"
    finally:
        conn.close()


def test_project_id_la_CHUOI_NOI_van_tra_dung_nguoi(tmp_path):
    """Job nộp cả tập ghi 16 mã nối bằng dấu phẩy — so bằng `=` là trượt."""
    from autoedit.web.server import nguoi_nop_tap

    d = _project(tmp_path, "c12-2026", rf"{NAS}\LI106_Hai\RenderY\C12.txt")
    conn = _jobs_db(tmp_path / "jobs.db", [
        (rf"{NAS}\LI106_Hai", "haint",
         ",".join(f"c{i}-2026" for i in range(1, 16)) + ",c12-2026"),
    ])
    try:
        assert nguoi_nop_tap(d, conn) == "haint"
    finally:
        conn.close()


def test_bo_cuc_THU_MUC_CON_van_chay_nhu_cu(tmp_path):
    from autoedit.web.server import nguoi_nop_tap

    d = _project(tmp_path, "h-2026", rf"{NAS}\LI103\Rendery\H\H.txt")
    conn = _jobs_db(tmp_path / "jobs.db", [
        (rf"{NAS}\LI103", "thanhdn", ""),
        (rf"{NAS}\LI102\Tool", "hieuvn", ""),
    ])
    try:
        assert nguoi_nop_tap(d, conn) == "thanhdn"
    finally:
        conn.close()


def test_khong_co_job_nao_thi_tra_rong(tmp_path):
    """Không tra ra thì trả rỗng — người GỌI quyết cách lùi, đừng đoán bừa."""
    from autoedit.web.server import nguoi_nop_tap

    d = _project(tmp_path, "h-2026", rf"{NAS}\LI999\RenderY\H.txt")
    conn = _jobs_db(tmp_path / "jobs.db", [(rf"{NAS}\LI102\Tool", "hieuvn", "")])
    try:
        assert nguoi_nop_tap(d, conn) == ""
    finally:
        conn.close()


def test_ten_tap_LA_TIEN_TO_cua_tap_khac_khong_bi_lan(tmp_path):
    """`LI10` không được vớ job của `LI106_Hai` — LIKE '%...%' là chỗ dễ lẫn."""
    from autoedit.web.server import nguoi_nop_tap

    d = _project(tmp_path, "h-2026", rf"{NAS}\LI10\RenderY\H.txt")
    conn = _jobs_db(tmp_path / "jobs.db", [
        (rf"{NAS}\LI106_Hai", "haint", ""),
    ])
    try:
        assert nguoi_nop_tap(d, conn) == ""
    finally:
        conn.close()
