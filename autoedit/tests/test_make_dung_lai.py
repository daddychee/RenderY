"""Chương đã dựng xong thì nộp lại KHÔNG dựng lại từ đầu.

31/08: C9 chết vì Pexels 504; nộp lại tập thì H/C7/c8 đã có draft cũng dựng lại —
~15 phút và tiền API cho việc đã làm xong.

Nhưng tái dùng SAI còn tệ hơn chạy lại: writer sửa kịch bản rồi nộp lại mà nhận về
draft cũ thì hỏng âm thầm, không ai biết. Nên điều kiện phải chặt.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from autoedit.cli import _project_cu_dung_duoc


def _lam_chuong(tmp_path, ten="H"):
    ch = tmp_path / "tap" / "RenderY" / ten
    ch.mkdir(parents=True)
    (ch / "script.txt").write_text("xin chao", encoding="utf-8")
    (ch / "voice.mp3").write_bytes(b"fake")
    return ch


def _lam_project(out, ch, *, co_draft=True, tao_sau=True):
    """Project trỏ về thư mục chương `ch`. tao_sau=True -> tạo SAU khi sửa nguồn."""
    pd = out / "h-20260831-000000"
    (pd / "draft").mkdir(parents=True)
    tao = datetime.now(timezone.utc) + (timedelta(minutes=5) if tao_sau
                                        else timedelta(minutes=-5))
    (pd / "project.json").write_text(json.dumps({
        "schema_version": 1, "project_id": "h-20260831-000000", "title": "H",
        "created_at": tao.isoformat(), "project_dir": str(pd),
        "inputs": {"script_path": str(ch / "script.txt"), "voice_path": str(ch / "voice.mp3"),
                   "script_text": "xin chao",
                   "original_script_path": str(ch / "script.txt"),
                   "original_voice_path": str(ch / "voice.mp3")},
        "draft_path": str(pd / "draft") if co_draft else None,
        "stages": {}, "transcript": [], "beats": [], "cost_log": [],
    }), encoding="utf-8")
    return pd


def test_dung_lai_khi_da_co_draft(tmp_path):
    ch = _lam_chuong(tmp_path)
    out = tmp_path / "projects"
    _lam_project(out, ch)
    assert _project_cu_dung_duoc(ch, out) is not None


def test_khong_dung_lai_khi_chua_co_draft(tmp_path):
    """Chương dựng dở (C9 chết giữa chừng) -> phải dựng lại, không giao bản dở."""
    ch = _lam_chuong(tmp_path)
    out = tmp_path / "projects"
    _lam_project(out, ch, co_draft=False)
    assert _project_cu_dung_duoc(ch, out) is None


def test_khong_dung_lai_khi_writer_sua_kich_ban(tmp_path):
    """Điều kiện QUAN TRỌNG NHẤT: nguồn đổi sau khi dựng -> draft cũ đã lỗi thời."""
    ch = _lam_chuong(tmp_path)
    out = tmp_path / "projects"
    _lam_project(out, ch, tao_sau=False)      # project tạo TRƯỚC, nguồn sửa SAU
    assert _project_cu_dung_duoc(ch, out) is None


def test_khong_lay_project_cua_chuong_khac(tmp_path):
    """Mỗi chương một project riêng — lấy nhầm là ghép sai timeline."""
    h = _lam_chuong(tmp_path, "H")
    c1 = _lam_chuong(tmp_path, "C1")
    out = tmp_path / "projects"
    _lam_project(out, h)
    assert _project_cu_dung_duoc(c1, out) is None


def test_draft_bi_xoa_thi_khong_dung_lai(tmp_path):
    """project.json còn ghi draft_path nhưng người ta đã xoá thư mục draft."""
    ch = _lam_chuong(tmp_path)
    out = tmp_path / "projects"
    pd = _lam_project(out, ch)
    import shutil
    shutil.rmtree(pd / "draft")
    assert _project_cu_dung_duoc(ch, out) is None


def test_khong_co_project_nao(tmp_path):
    ch = _lam_chuong(tmp_path)
    assert _project_cu_dung_duoc(ch, tmp_path / "khong-ton-tai") is None


def test_project_json_hong_thi_bo_qua(tmp_path):
    ch = _lam_chuong(tmp_path)
    out = tmp_path / "projects"
    (out / "hong").mkdir(parents=True)
    (out / "hong" / "project.json").write_text("{ khong phai json", encoding="utf-8")
    assert _project_cu_dung_duoc(ch, out) is None      # không vỡ, chỉ bỏ qua
