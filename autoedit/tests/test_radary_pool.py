# -*- coding: utf-8 -*-
"""Đọc POOL của Radary — CHỈ ĐỌC, gộp mọi workspace cùng một mã ngách.

Đo thật trên `radary.db` (18/09): cột `workspaces.ngach` chứa ĐÚNG MÃ của danh
bạ CRM (`N-003`, `N-SENIOR-HEALTH`), nên khớp thẳng không phải dò tên. Nhưng
**một mã có NHIỀU workspace**: N-003 có ws 52 (`X FILE`, rỗng) và ws 53
(`X FILE — US`, 35 kênh / 675 video). Đọc một cái là có ngày vớ phải cái rỗng
rồi kết luận "ngách không có pool". Luật ở đây: gộp.
"""
from __future__ import annotations

import sqlite3

import pytest

from autoedit import radary


def _lam_db(f, ws, ch, vd):
    """Dựng radary.db giả — ĐÚNG tên cột đã đo trên kho thật."""
    c = sqlite3.connect(str(f))
    c.executescript("""
        CREATE TABLE workspaces(id INTEGER PRIMARY KEY, org_id INT, name TEXT,
            tz TEXT, config TEXT, created_ts INT, market TEXT, ngach TEXT);
        CREATE TABLE channels(id INTEGER PRIMARY KEY, workspace_id INT, yt_id TEXT,
            title TEXT, uploads_playlist TEXT, active INT, favorite INT);
        CREATE TABLE videos(id INTEGER PRIMARY KEY, workspace_id INT, yt_id TEXT,
            channel_yt_id TEXT, channel_title TEXT, title TEXT, pub_ts INT,
            duration_s INT, tier INT, fail INT, pushed INT, last_vph REAL,
            confirm_due INT, dead INT, thumb_ck TEXT);
    """)
    c.executemany("INSERT INTO workspaces(id,name,market,ngach) VALUES(?,?,?,?)", ws)
    c.executemany("INSERT INTO channels(id,workspace_id,title) VALUES(?,?,?)", ch)
    c.executemany("INSERT INTO videos(id,workspace_id,title,tier,pub_ts) VALUES(?,?,?,?,?)", vd)
    c.commit()
    c.close()
    return f


@pytest.fixture()
def kho(tmp_path, monkeypatch):
    """Kho GIẢ. Mọi test phải đi qua đây — không test nào chạm kho thật."""
    f = tmp_path / "radary.db"
    _lam_db(
        f,
        ws=[(52, "X FILE", "", "N-003"),          # y kho thật: ws rỗng ĐỨNG TRƯỚC
            (53, "X FILE — US", "TT-US", "N-003"),
            (34, "SENIOR HEALTH — US", "TT-US", "N-SENIOR-HEALTH")],
        ch=[(1, 53, "Kênh A"), (2, 53, "Kênh B"), (3, 34, "Kênh khác")],
        vd=[(1, 53, "How Duct Tape Is Made", 0, 100),
            (2, 53, "Why Do Batteries Eventually Die?", 3, 200),
            (3, 53, "Every Type of Yogurt Explained", 1, 300),
            (4, 34, "Best exercise for seniors", 2, 400)],
    )
    monkeypatch.setenv("RENDERY_RADARY", str(f))
    return f


def test_KHONG_test_nao_dung_kho_that(kho, monkeypatch):
    """Rào đầu tiên: đường đang dùng phải là kho giả, không phải ổ D."""
    assert radary.duong_radary() == kho
    assert "AI AGENT OUTLIERY" not in str(radary.duong_radary())


def test_gop_moi_workspace_cung_mot_ma(kho):
    p = radary.pool("N-003")
    assert p["kenh"] == 2
    assert p["video"] == 3
    assert {w["id"] for w in p["ws"]} == {52, 53}


def test_ws_rong_dung_truoc_KHONG_nuot_mat_ws_co_data(kho):
    """Bẫy thật của N-003: ws 52 rỗng có id NHỎ HƠN ws 53 có data."""
    p = radary.pool("N-003")
    assert p["video"] == 3, "đọc trúng ws rỗng rồi bỏ cuộc"


def test_ngach_khac_khong_lan_sang(kho):
    p = radary.pool("N-003")
    assert "Best exercise for seniors" not in p["tieu_de"]
    assert radary.pool("N-SENIOR-HEALTH")["video"] == 1


def test_tieu_de_tra_ve_du(kho):
    p = radary.pool("N-003")
    assert set(p["tieu_de"]) == {"How Duct Tape Is Made",
                                 "Why Do Batteries Eventually Die?",
                                 "Every Type of Yogurt Explained"}


def test_tran_tieu_de_uu_tien_tier_cao(kho):
    """Kho thật có ngách 10.450 video — nhồi hết vào prompt LLM là vỡ."""
    p = radary.pool("N-003", tran=2)
    assert len(p["tieu_de"]) == 2
    assert p["tieu_de"][0] == "Why Do Batteries Eventually Die?"   # tier 3
    assert p["video"] == 3, "trần chỉ cắt danh sách, KHÔNG được cắt số đếm"


def test_ma_khong_co_pool_thi_rong_chu_khong_no(kho):
    p = radary.pool("N-KHONG-CO")
    assert p["doc_duoc"] is True
    assert p["video"] == 0 and p["kenh"] == 0 and p["tieu_de"] == []


def test_ma_rong_tra_ve_rong(kho):
    assert radary.pool("")["video"] == 0


def test_khong_phan_biet_hoa_thuong(kho):
    assert radary.pool("n-003")["video"] == 3


def test_file_khong_ton_tai_thi_FAIL_OPEN(tmp_path, monkeypatch):
    """Radary tắt / ổ D chưa gắn KHÔNG được kéo RenderY chết theo (y `ngach.py`)."""
    monkeypatch.setenv("RENDERY_RADARY", str(tmp_path / "khong-co.db"))
    assert radary.doc_duoc() is False
    p = radary.pool("N-003")
    assert p["doc_duoc"] is False and p["video"] == 0


def test_db_hong_thi_FAIL_OPEN(tmp_path, monkeypatch):
    f = tmp_path / "rac.db"
    f.write_bytes(b"day khong phai sqlite")
    monkeypatch.setenv("RENDERY_RADARY", str(f))
    assert radary.doc_duoc() is False
    assert radary.pool("N-003")["video"] == 0


def test_thieu_bang_thi_FAIL_OPEN(tmp_path, monkeypatch):
    """Radary đổi cấu trúc bảng -> RenderY câm lặng chứ không nổ giữa mặt user."""
    f = tmp_path / "thieu.db"
    c = sqlite3.connect(str(f))
    c.execute("CREATE TABLE workspaces(id INTEGER PRIMARY KEY, ngach TEXT)")
    c.commit()
    c.close()
    monkeypatch.setenv("RENDERY_RADARY", str(f))
    assert radary.pool("N-003")["video"] == 0


def test_ket_noi_CHI_DOC__khong_co_duong_nao_ghi_vao_kho_radary(kho):
    """Luật của user: không ghi/xoá/sửa sổ thật của app khác. `mode=ro` là rào."""
    conn = radary._mo()
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("DELETE FROM videos")
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO workspaces(id,ngach) VALUES(999,'X')")
    finally:
        conn.close()
