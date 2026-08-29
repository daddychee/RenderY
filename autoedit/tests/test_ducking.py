"""Test F8 — ducking: lịch keyframe volume nhạc (pure).

Kịch bản chuẩn: duck=0.2, BREATH_VOL=0.5, RAMP=2.5s, slope=0.12/s.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from autoedit.packager import ducking

SEC = 1_000_000


def _seg(a, b):
    return SimpleNamespace(timeline_start=a, timeline_end=b)


# ===================== merge_voice_intervals ==================================
def test_merge_swallows_short_gaps():
    segs = [_seg(0.0, 5.0), _seg(5.5, 10.0), _seg(12.0, 15.0)]
    assert ducking.merge_voice_intervals(segs, min_gap=1.0) == [(0.0, 10.0), (12.0, 15.0)]


def test_merge_sorts_unsorted_input():
    segs = [_seg(12.0, 15.0), _seg(0.0, 5.0)]
    assert ducking.merge_voice_intervals(segs) == [(0.0, 5.0), (12.0, 15.0)]


# ===================== build_envelope =========================================
def test_envelope_long_gap_full_plateau():
    env = ducking.build_envelope([(0.0, 10.0), (20.0, 30.0)], 30.0, duck=0.2)
    assert ducking.envelope_at(env, 5.0) == pytest.approx(0.2)     # giữa voice: nép
    assert ducking.envelope_at(env, 10.0) == pytest.approx(0.2)    # mép voice: còn nép
    assert ducking.envelope_at(env, 15.0) == pytest.approx(ducking.BREATH_VOL)  # mặt bằng nở
    # giữa ramp lên (10 -> 12.5): tại 11.25 đi được nửa dốc
    assert ducking.envelope_at(env, 11.25) == pytest.approx(0.2 + (ducking.BREATH_VOL - 0.2) / 2)
    # ramp xuống kết thúc ĐÚNG lúc voice vào lại
    assert ducking.envelope_at(env, 20.0) == pytest.approx(0.2)


def test_envelope_short_gap_partial_swell_fixed_slope():
    # gap 3s < 2*RAMP -> r=1.5s, đỉnh 0.2 + 0.12*1.5 = 0.38 (phồng nhẹ, KHÔNG dốc gắt)
    env = ducking.build_envelope([(0.0, 10.0), (13.0, 20.0)], 20.0, duck=0.2)
    peak = ducking.envelope_at(env, 11.5)
    assert peak == pytest.approx(0.38)
    assert peak < ducking.BREATH_VOL


def test_envelope_head_and_tail_swell():
    env = ducking.build_envelope([(4.0, 10.0)], 16.0, duck=0.2)
    assert ducking.envelope_at(env, 0.0) == pytest.approx(ducking.BREATH_VOL)  # nhạc dạo đầu nở
    assert ducking.envelope_at(env, 4.0) == pytest.approx(0.2)                 # nép đúng lúc voice vào
    assert ducking.envelope_at(env, 16.0) == pytest.approx(ducking.BREATH_VOL)  # thở kết video giữ nở


def test_envelope_tiny_tail_stays_ducked():
    env = ducking.build_envelope([(0.0, 10.0)], 10.5, duck=0.2)
    assert ducking.envelope_at(env, 10.4) == pytest.approx(0.2)


# ===================== segment_keyframes ======================================
def test_segment_inside_voice_no_keyframes():
    env = ducking.build_envelope([(0.0, 30.0)], 30.0, duck=0.2)
    assert ducking.segment_keyframes(env, 5 * SEC, 10 * SEC, duck=0.2) == []


def test_segment_over_gap_gets_anchored_keyframes():
    env = ducking.build_envelope([(0.0, 10.0), (20.0, 30.0)], 30.0, duck=0.2)
    kfs = ducking.segment_keyframes(env, 5 * SEC, 20 * SEC, duck=0.2)   # clip 5..25s
    offs = [o for o, _ in kfs]
    assert kfs[0] == (0, pytest.approx(0.2))                # neo mép đầu clip
    assert offs == sorted(offs) and len(offs) == len(set(offs))  # tăng dần, không trùng
    assert all(0 <= o <= 20 * SEC - ducking.EDGE_GUARD_US for o in offs)  # kẹp trong clip
    # điểm gãy toàn cục 12.5s (đỉnh nở) -> offset 7.5s tính từ đầu clip
    assert (round(7.5 * SEC), pytest.approx(ducking.BREATH_VOL)) in [(o, v) for o, v in kfs]


def test_segment_inside_breath_plateau_gets_flat_breath():
    # clip nằm trọn trong mặt bằng nở -> 2 keyframe mức NỞ (đè volume tĩnh 0.2)
    env = ducking.build_envelope([(0.0, 10.0), (30.0, 40.0)], 40.0, duck=0.2)
    kfs = ducking.segment_keyframes(env, 14 * SEC, 3 * SEC, duck=0.2)
    assert kfs and all(v == pytest.approx(ducking.BREATH_VOL) for _, v in kfs)
