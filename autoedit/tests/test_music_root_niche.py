"""Test pool nhạc theo NICHE (user chốt 2026-07-17 — mở đầu life-in).

Luật: <music_root>/<niche>/tracks/ tồn tại -> niche CHỈ dùng pool riêng đó
(nhạc không lẫn 2 chiều giữa niche); chưa có -> pool chung như cũ.
"""

from __future__ import annotations

import autoedit.music.library as mlib


def _make_pool(root, niche=None):
    d = root / niche if niche else root
    (d / mlib.TRACKS_DIR).mkdir(parents=True, exist_ok=True)
    return d


def test_niche_co_pool_rieng_dung_rieng(tmp_path, monkeypatch):
    monkeypatch.setattr(mlib, "MUSIC_ROOT", tmp_path)
    _make_pool(tmp_path)                       # pool chung vẫn tồn tại
    pool = _make_pool(tmp_path, "life-in")
    assert mlib.music_root_for("life-in") == pool   # CHỈ pool riêng, không phải chung


def test_niche_chua_co_pool_ve_pool_chung(tmp_path, monkeypatch):
    monkeypatch.setattr(mlib, "MUSIC_ROOT", tmp_path)
    _make_pool(tmp_path)
    assert mlib.music_root_for("deepsea") == tmp_path   # niche khác chạy như cũ


def test_khong_niche_ve_pool_chung(tmp_path, monkeypatch):
    monkeypatch.setattr(mlib, "MUSIC_ROOT", tmp_path)
    assert mlib.music_root_for(None) == tmp_path
    assert mlib.music_root_for("") == tmp_path
    assert mlib.music_root_for("   ") == tmp_path


def test_folder_niche_thieu_tracks_khong_tinh(tmp_path, monkeypatch):
    """Regression: folder niche tồn tại nhưng CHƯA music-init (không có tracks/)
    -> chưa phải pool, vẫn dùng pool chung (tránh index rỗng làm video câm nhạc)."""
    monkeypatch.setattr(mlib, "MUSIC_ROOT", tmp_path)
    (tmp_path / "life-in").mkdir(parents=True)      # folder rỗng, không tracks/
    assert mlib.music_root_for("life-in") == tmp_path
