"""Test NHIP-M2 — đoạn chèn Δ editor khai (MO_TA_VAN_HANH_DOAN_CHEN.md).

Δ chèn ở ĐÚNG MỘT CHỖ sinh timeline (cutter/timeline.py) — beat/segment phía sau
tự dịch; coverage sinh cửa sổ insert riêng (slug giữ chỗ M2); J-cut/snap/ambient
không được đụng vào Δ (độ dài editor khai phải giữ ĐÚNG).
"""

from __future__ import annotations

import pytest

from autoedit.ambient.schedule import breath_slots
from autoedit.cutter import timeline as tl
from autoedit.packager import coverage as cov
from autoedit.project import Beat, InsertSpec, SearchQueries, VoiceSegment


def _beat(beat_id: int, start: float, end: float, breathing=0.0,
          ts=None, te=None) -> Beat:
    return Beat(
        beat_id=beat_id, chapter=1, text=f"beat {beat_id}.", start_word=0, end_word=1,
        start=start, end=end, timeline_start=ts, timeline_end=te,
        energy="medium", mood="m", visual_level="literal", visual_concept="c",
        shot_size="medium", search_queries=SearchQueries(specific=["q"]),
        breathing_after=breathing,
    )


def _seg(seg_id, ts, te, beat_ids, breathing=0.0, insert=0.0) -> VoiceSegment:
    return VoiceSegment(
        segment_id=seg_id, path=f"segments/seg_{seg_id:03d}.wav",
        source_start=ts, source_end=te, timeline_start=ts, timeline_end=te,
        beat_ids=beat_ids, breathing_after=breathing, insert_after=insert,
    )


# ===================== timeline (hệ tọa độ kép) ===============================
def test_insert_splits_run_and_shifts_following_beats():
    beats = [_beat(0, 0.0, 2.0), _beat(1, 2.0, 4.0), _beat(2, 4.0, 6.0),
             _beat(3, 6.0, 8.0)]
    plans = tl.apply_timeline(tl.plan_segments(beats, inserts={1: 20.0}))
    assert len(plans) == 2                      # Δ kết thúc run dù beat 1 không thở
    assert plans[0].insert_after == 20.0
    # SOURCE bất biến — ổ bug kinh điển
    assert plans[1].source_start == 4.0 and plans[1].source_end == 8.0
    assert plans[1].timeline_start == pytest.approx(24.0)
    bt = tl.map_beats_to_timeline(beats, plans)
    assert bt[1] == (2.0, 4.0)                                 # trước Δ: không dịch
    assert bt[2] == (pytest.approx(24.0), pytest.approx(26.0))  # sau Δ: +20
    assert bt[3] == (pytest.approx(26.0), pytest.approx(28.0))


def test_insert_stacks_after_breathing_and_micro():
    beats = [_beat(0, 0.0, 2.0, breathing=3.0), _beat(1, 2.0, 4.0)]
    beats[0].micro_pause_after = 0.0
    plans = tl.apply_timeline(tl.plan_segments(beats, inserts={0: 10.0}))
    # thứ tự trên timeline: voice -> thở 3.0 -> Δ 10.0 -> voice kế
    assert plans[0].breathing_after == 3.0 and plans[0].insert_after == 10.0
    assert plans[1].timeline_start == pytest.approx(2.0 + 3.0 + 10.0)


def test_insert_on_last_beat_forced_zero():
    beats = [_beat(0, 0.0, 2.0), _beat(1, 2.0, 4.0)]
    plans = tl.apply_timeline(tl.plan_segments(beats, inserts={1: 5.0}))
    # beat cuối luôn 0 cả ba (total_end downstream dựa segment cuối)
    assert plans[-1].insert_after == 0.0
    assert plans[-1].timeline_end == 4.0


# ===================== coverage ===============================================
def test_coverage_insert_window_contiguous_and_flagged():
    beats = [_beat(0, 0.0, 2.0, breathing=3.0, ts=0.0, te=2.0),
             _beat(1, 4.0, 6.0, ts=25.0, te=27.0)]
    segs = [_seg(1, 0.0, 2.0, [0], breathing=3.0, insert=20.0),
            _seg(2, 25.0, 27.0, [1])]
    ws = cov.coverage_windows(beats, segs)
    # [voice+thở 0-5] [Δ 5-25] [voice 25-27] — liền khít, Δ flag insert
    assert [(w.start, w.end, w.insert) for w in ws] == [
        (0.0, 5.0, False), (5.0, 25.0, True), (25.0, 27.0, False)]
    assert ws[1].beat_id == 0 and ws[1].breathing_dur == 0.0
    assert cov.check_coverage_invariants(ws, 27.0) == []


def test_j_cut_skipped_before_insert():
    beats = [_beat(0, 0.0, 2.0, breathing=2.0, ts=0.0, te=2.0),
             _beat(1, 4.0, 6.0, ts=14.0, te=16.0)]
    segs = [_seg(1, 0.0, 2.0, [0], breathing=2.0, insert=10.0),
            _seg(2, 14.0, 16.0, [1])]
    ws = cov.apply_j_cuts(cov.coverage_windows(beats, segs))
    # thở 2.0 >= J_CUT_MIN_BREATH nhưng kế là Δ -> KHÔNG J-cut (Δ giữ đúng độ dài khai)
    assert ws[0].end == 4.0 and ws[1].start == 4.0 and ws[1].duration == 10.0
    assert cov.check_coverage_invariants(ws, 16.0) == []


def test_snap_exempts_insert_edges():
    ws = [cov.CoverWindow(0, 0.0, 5.0), cov.CoverWindow(0, 5.0, 25.0, insert=True),
          cov.CoverWindow(1, 25.0, 30.0)]
    st = cov.snap_to_accents(ws, targets=[5.15, 25.15], hook_end=0.0,
                             tol=0.30, lead=0.08, cap_ratio=1.0)
    assert st["snapped"] == 0                   # cả 2 mép quanh Δ đều miễn
    assert ws[1].start == 5.0 and ws[1].end == 25.0


def test_split_breath_shots_leaves_insert_window_untouched():
    # beat 0 có pick shot thở VÀ đoạn chèn: ô thở vẫn chẻ như cũ, Δ đi qua nguyên vẹn
    beats = [_beat(0, 0.0, 2.0, breathing=3.0, ts=0.0, te=2.0),
             _beat(1, 4.0, 6.0, ts=15.0, te=17.0)]
    segs = [_seg(1, 0.0, 2.0, [0], breathing=3.0, insert=10.0),
            _seg(2, 15.0, 17.0, [1])]
    ws = cov.split_breath_shots(cov.coverage_windows(beats, segs), {0: [0.0]})
    assert [(w.start, w.end, w.breath_shot, w.insert) for w in ws] == [
        (0.0, 2.5, False, False), (2.5, 5.0, True, False),
        (5.0, 15.0, False, True), (15.0, 17.0, False, False)]
    assert cov.check_coverage_invariants(ws, 17.0) == []


# ===================== ambient không nuốt Δ (BAN_GIAO §7c.4) ==================
def test_breath_slots_exclude_insert():
    segs = [_seg(1, 0.0, 10.0, [0], breathing=4.0, insert=20.0),
            _seg(2, 34.0, 40.0, [1])]
    slots = breath_slots(segs)
    # ô ambient = phần thở [10,14]; Δ [14,34] KHÔNG nhận ambient (nhạc chủ đạo)
    assert len(slots) == 1
    assert (slots[0].start, slots[0].end) == (10.0, 14.0)


def test_breath_slots_without_insert_unchanged():
    segs = [_seg(1, 0.0, 10.0, [0], breathing=4.0), _seg(2, 14.0, 20.0, [1])]
    slots = breath_slots(segs)
    assert len(slots) == 1 and (slots[0].start, slots[0].end) == (10.0, 14.0)


# ===================== schema =================================================
def test_insert_spec_roundtrip_and_legacy_segment_loads():
    spec = InsertSpec(after_beat=57, dur=20.0, note="montage thiên nhiên")
    assert InsertSpec.model_validate(spec.model_dump()) == spec
    # project.json cũ (không có insert_after) load được, mặc định 0
    old = VoiceSegment.model_validate({
        "segment_id": 1, "path": "segments/seg_001.wav", "source_start": 0.0,
        "source_end": 2.0, "timeline_start": 0.0, "timeline_end": 2.0})
    assert old.insert_after == 0.0
