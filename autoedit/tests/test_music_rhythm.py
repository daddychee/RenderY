"""Test MUSIC SYNC M0 — analyzer nhịp/accent + tier A/B/C (MO_TA_VAN_HANH_MUSIC_SYNC.md §2).

Audio tổng hợp: click 120BPM (nhịp rõ → tier A) vs drone sine (ambient → tier C — chống
bẫy librosa bịa grid ~120BPM, memory editor-music-sync-study). Import: thêm field grid,
cache idempotent, nâng cấp record cũ thiếu grid, regrid backfill.
"""

from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np
import pytest

from autoedit.music.analyze import ACCENT_MIN_GAP, analyze_rhythm

SR = 22050


def _write_wav(path: Path, y: np.ndarray) -> None:
    pcm = (np.clip(y, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def _click_track(dur: float = 20.0, bpm: float = 120) -> np.ndarray:
    """Metronome: xung sine 1kHz decay nhanh mỗi 60/bpm giây — nhịp rõ tuyệt đối."""
    y = np.zeros(int(dur * SR), dtype=np.float32)
    t = np.arange(int(0.03 * SR)) / SR
    burst = (np.sin(2 * np.pi * 1000 * t) * np.exp(-t * 200)).astype(np.float32)
    period = 60.0 / bpm
    k = 0
    while k * period + 0.05 < dur:
        i = int(k * period * SR)
        y[i:i + len(burst)] += burst
        k += 1
    return y * 0.8


def _drone(dur: float = 20.0) -> np.ndarray:
    """Sine 110Hz phẳng — không có nhịp thật (đại diện nhạc ambient deepsea)."""
    t = np.arange(int(dur * SR)) / SR
    return (0.3 * np.sin(2 * np.pi * 110 * t)).astype(np.float32)


def test_click_track_tier_a(tmp_path):
    f = tmp_path / "click.wav"
    _write_wav(f, _click_track())
    r = analyze_rhythm(f)
    assert r["beat_tier"] == "A"
    beats = r["beat_times"]
    assert len(beats) >= 16
    assert abs(float(np.median(np.diff(beats))) - 0.5) < 0.06   # 120BPM = 0.5s/beat
    # downbeat = tập con beat (ước lượng pha nhóm 4)
    assert r["downbeats"] and set(r["downbeats"]) <= set(beats)
    # accent thưa: đúng min-gap, không phải grid đều
    acc = r["accents"]
    assert acc and all(b - a >= ACCENT_MIN_GAP - 1e-6 for a, b in zip(acc, acc[1:]))


def test_drone_tier_c_khong_giu_grid_bia(tmp_path):
    f = tmp_path / "drone.wav"
    _write_wav(f, _drone())
    r = analyze_rhythm(f)
    assert r["beat_tier"] == "C"
    assert r["beat_times"] == []        # grid librosa bịa -> KHÔNG lưu
    assert r["downbeats"] == []


@pytest.fixture()
def lib(tmp_path):
    root = tmp_path / "music"
    (root / "tracks").mkdir(parents=True)
    _write_wav(root / "tracks" / "Test Artist - Click __peaceful.wav", _click_track())
    return root


def test_import_adds_grid_and_cache_idempotent(lib, monkeypatch):
    from autoedit.music import library as L

    res = L.import_from_filenames(lib)
    assert res.imported and not res.failed
    rec = L._load_index(lib)[0]
    assert rec["beat_tier"] == "A" and rec["mood"] == ["peaceful"]
    assert rec["energy_curve"]                       # field librosa cũ vẫn có

    # lần 2: cache hit -> KHÔNG gọi librosa lại
    def _boom(*a, **k):
        raise AssertionError("không được analyze lại khi cache đã đủ grid")

    monkeypatch.setattr(L, "analyze_track", _boom)
    monkeypatch.setattr(L, "analyze_rhythm", _boom)
    res2 = L.import_from_filenames(lib)
    assert res2.imported and not res2.failed
    rec2 = L._load_index(lib)[0]
    assert rec2["beat_times"] == rec["beat_times"]   # grid giữ nguyên


def test_import_nang_cap_record_thieu_grid(lib):
    from autoedit.music import library as L

    L.import_from_filenames(lib)
    # giả lập record cũ (trước MUSIC SYNC): xóa field nhịp khỏi index
    idx = L._index_path(lib)
    data = json.loads(idx.read_text(encoding="utf-8"))
    for k in L.RHYTHM_KEYS:
        data["tracks"][0].pop(k, None)
    idx.write_text(json.dumps(data), encoding="utf-8")
    curve_before = data["tracks"][0]["energy_curve"]

    res = L.import_from_filenames(lib)               # nạp lại -> tự bổ sung grid
    assert not res.failed
    rec = L._load_index(lib)[0]
    assert rec["beat_tier"] == "A"
    assert rec["energy_curve"] == curve_before       # PRESERVE field analyze cũ


def test_regrid_backfill(lib):
    from autoedit.music import library as L

    L.import_from_filenames(lib)
    rows, failed = L.regrid_index(lib)
    assert not failed and rows[0]["beat_tier"] == "A"
    assert L._load_index(lib)[0]["beat_tier"] == "A"   # đã ghi xuống index


# ---- ĐỘ MẠNH beat/accent (2026-07-19, cần cho mini-hook + lưới beat ô thở) ----

def test_beat_strength_song_song_beat_times(tmp_path):
    """Bất biến CỐT LÕI: hai mảng cùng độ dài, chuẩn hóa 0-1.

    Lệch độ dài -> beat_grid tra nhầm chỉ số -> cắt vào beat khác hẳn. minihook.py
    có phòng vệ (bỏ qua nếu lệch) nhưng khi đó mất luôn tính năng, im lặng.
    """
    f = tmp_path / "click.wav"
    _write_wav(f, _click_track())
    r = analyze_rhythm(f)
    st = r["beat_strength"]
    assert len(st) == len(r["beat_times"]) > 0
    assert all(0.0 <= v <= 1.0 for v in st)
    assert max(st) == 1.0                              # chuẩn hóa theo đỉnh trong bài


def test_accent_strength_song_song_va_theo_thu_tu_thoi_gian(tmp_path):
    """accents phải SORT THEO THỜI GIAN và accent_strength khớp từng phần tử.

    Bẫy: greedy chọn accent duyệt theo ĐỘ MẠNH giảm dần; quên sort lại theo thời gian
    thì hai mảng vẫn cùng độ dài nhưng LỆCH CẶP — sai âm thầm, không ai bắt.
    """
    f = tmp_path / "click.wav"
    _write_wav(f, _click_track())
    r = analyze_rhythm(f)
    acc, ast = r["accents"], r["accent_strength"]
    assert len(acc) == len(ast) > 0
    assert acc == sorted(acc)
    assert all(0.0 <= v <= 1.0 for v in ast)
    assert max(ast) == 1.0


def test_tier_c_do_manh_rong_cung_luc_voi_beat_times(tmp_path):
    """Tier C: beat_times rỗng (grid bịa) -> beat_strength PHẢI rỗng theo, không lệch."""
    f = tmp_path / "drone.wav"
    _write_wav(f, _drone())
    r = analyze_rhythm(f)
    assert r["beat_times"] == [] and r["beat_strength"] == []


def test_import_nang_cap_record_co_tier_nhung_thieu_do_manh(lib):
    """🐛 BẪY: record đã có beat_tier (nạp trước 2026-07-19) nhưng THIẾU độ mạnh.

    Điều kiện cũ chỉ hỏi `"beat_tier" not in obj` -> record này LỌT LƯỚI, không bao giờ
    được bổ sung độ mạnh. Cả pool 433 bài rơi vào đúng ca này.
    """
    from autoedit.music import library as L

    L.import_from_filenames(lib)
    idx = L._index_path(lib)
    data = json.loads(idx.read_text(encoding="utf-8"))
    for k in ("beat_strength", "accent_strength"):     # xóa ĐÚNG field mới, giữ beat_tier
        data["tracks"][0].pop(k, None)
    assert data["tracks"][0]["beat_tier"] == "A"       # tier vẫn còn -> điều kiện cũ bỏ qua
    idx.write_text(json.dumps(data), encoding="utf-8")

    res = L.import_from_filenames(lib)
    assert not res.failed
    rec = L._load_index(lib)[0]
    assert len(rec["beat_strength"]) == len(rec["beat_times"]) > 0


def test_regrid_luu_duoc_do_manh(lib):
    """regrid_index phải GHI XUỐNG được field mới — nếu thiếu tên trong RHYTHM_KEYS thì
    đo xong không lưu (backfill chạy rỗng im lặng, 433 bài coi như chưa đo)."""
    from autoedit.music import library as L

    L.import_from_filenames(lib)
    rows, failed = L.regrid_index(lib)
    assert not failed
    assert "beat_strength" in L.RHYTHM_KEYS and "accent_strength" in L.RHYTHM_KEYS
    on_disk = L._load_index(lib)[0]
    assert len(on_disk["beat_strength"]) == len(on_disk["beat_times"]) > 0
    assert len(on_disk["accent_strength"]) == len(on_disk["accents"]) > 0
