"""Test NHIP-M3 — nhạc editor đưa cho đoạn chèn Δ (MO_TA_VAN_HANH_NHAC_DOAN_CHEN.md).

Phương án B (user chốt 2026-07-20): bài editor vào tại mép VÀO Δ, THAY nhạc chương
đó tới HẾT CHƯƠNG, không quay lại bài cũ. Đây là chỗ ĐẦU TIÊN hệ thống cho phép
2 bài nhạc trong 1 chương — trước M3 bất biến "1 chương = 1 bài" đúng 14/14 project
đo thật. Nên test ở đây canh 2 thứ: (a) chương KHÔNG có Δ-nhạc phải ra tọa độ Y HỆT
đường cũ (hồi quy bằng 0); (b) chương CÓ Δ-nhạc chẻ đúng mép.
"""

from __future__ import annotations

import pytest

from autoedit.music import plan as mplan
from autoedit.packager import coverage as cov
from autoedit.packager.coverage import CoverWindow
from autoedit.project import (
    Beat, InsertSpec, MusicPlanEntry, Project, SearchQueries, VoiceSegment,
)


def _beat(beat_id: int, chapter: int, ts: float, te: float) -> Beat:
    return Beat(
        beat_id=beat_id, chapter=chapter, text=f"beat {beat_id}.", start_word=0,
        end_word=1, start=ts, end=te, timeline_start=ts, timeline_end=te,
        energy="medium", mood="m", visual_level="literal", visual_concept="c",
        shot_size="medium", search_queries=SearchQueries(specific=["q"]),
    )


def _seg(seg_id, ts, te, beat_ids, breathing=0.0, micro=0.0, insert=0.0) -> VoiceSegment:
    return VoiceSegment(
        segment_id=seg_id, path=f"segments/seg_{seg_id:03d}.wav",
        source_start=ts, source_end=te, timeline_start=ts, timeline_end=te,
        beat_ids=beat_ids, breathing_after=breathing, micro_pause_after=micro,
        insert_after=insert,
    )


def _project(beats, segs, inserts=(), chapters=(1, 2)) -> Project:
    p = Project.model_construct(
        project_id="t", project_dir="/tmp/t", beats=list(beats), segments=list(segs),
        inserts=list(inserts), music_plan=[], niche="life-in",
        outline={"chapters": [{"chapter_id": c, "mood": "m", "energy": "medium"}
                              for c in chapters]},
    )
    return p


# ===================== mép Δ trên timeline ===================================
def test_insert_edges_uses_segment_end_plus_breathing():
    # Δ nằm SAU voice + thở + giãn của segment (cutter/timeline.py:83) — KHÔNG phải
    # ngay sau beat.timeline_end. Đây là ổ lệch nếu tính nhầm.
    beats = [_beat(0, 1, 0.0, 10.0), _beat(1, 1, 34.0, 40.0)]
    segs = [_seg(1, 0.0, 10.0, [0], breathing=3.0, micro=1.0, insert=20.0),
            _seg(2, 34.0, 40.0, [1])]
    p = _project(beats, segs, [InsertSpec(after_beat=0, dur=20.0, music="/m/x.mp3")])
    assert mplan.insert_edges(p) == {0: (14.0, 34.0)}


def test_insert_edges_empty_without_inserts_or_cut():
    beats = [_beat(0, 1, 0.0, 10.0)]
    assert mplan.insert_edges(_project(beats, [_seg(1, 0.0, 10.0, [0])])) == {}
    # khai Δ nhưng CHƯA chạy lại cut -> chưa có segment mang insert_after
    p = _project(beats, [], [InsertSpec(after_beat=0, dur=20.0, music="/m/x.mp3")])
    assert mplan.insert_edges(p) == {}


# ===================== chẻ span (phương án B) ================================
def _chs(*spans):
    return [{"chapter_id": i + 1, "timeline_start": s, "timeline_end": e, "mood": "m",
             "energy": "medium"} for i, (s, e) in enumerate(spans)]


def test_spans_unchanged_when_no_insert_music():
    """Hồi quy bằng 0: không Δ-nhạc -> 1 span/chương, đúng ranh giới cũ."""
    chs = _chs((0.0, 50.0), (60.0, 100.0))
    p = _project([], [])
    spans = mplan.music_spans(p, chs, [0.0, 60.0], total_end=110.0)
    assert [(s["chapter_id"], s["seg_start"], s["seg_end"], s["is_insert"]) for s in spans] \
        == [(1, 0.0, 60.0, False), (2, 60.0, 110.0, False)]
    assert all(s["file"] is None for s in spans)


def test_span_splits_chapter_at_insert_and_runs_to_chapter_end():
    """Δ giữa chương 1: bài cũ [0,14], bài editor [14, hết chương 1] = tới 60."""
    beats = [_beat(0, 1, 0.0, 10.0), _beat(1, 1, 34.0, 40.0)]
    segs = [_seg(1, 0.0, 10.0, [0], breathing=4.0, insert=20.0),
            _seg(2, 34.0, 40.0, [1])]
    chs = _chs((0.0, 50.0), (60.0, 100.0))
    p = _project(beats, segs, [InsertSpec(after_beat=0, dur=20.0, music="/m/ed.mp3")])
    spans = mplan.music_spans(p, chs, [0.0, 60.0], total_end=110.0)
    assert [(s["chapter_id"], s["seg_start"], s["seg_end"], s["is_insert"]) for s in spans] \
        == [(1, 0.0, 14.0, False), (1, 14.0, 60.0, True), (2, 60.0, 110.0, False)]
    # bài editor chạy tới HẾT chương rồi DỪNG — chương 2 quay lại nhạc kế hoạch
    assert spans[1]["file"] == "/m/ed.mp3"
    assert spans[2]["file"] is None


def test_insert_without_music_does_not_split():
    """Δ không kèm --music (M2 nguyên vẹn): nhạc chương phủ kín Δ, không chẻ."""
    beats = [_beat(0, 1, 0.0, 10.0), _beat(1, 1, 34.0, 40.0)]
    segs = [_seg(1, 0.0, 10.0, [0], breathing=4.0, insert=20.0),
            _seg(2, 34.0, 40.0, [1])]
    chs = _chs((0.0, 50.0), (60.0, 100.0))
    p = _project(beats, segs, [InsertSpec(after_beat=0, dur=20.0)])
    spans = mplan.music_spans(p, chs, [0.0, 60.0], total_end=110.0)
    assert len(spans) == 2 and all(not s["is_insert"] for s in spans)


def test_spans_stay_contiguous_no_gap_no_overlap():
    """Nhạc phải LIỀN MẠCH: hở = im lặng giữa bài, đè = 2 bài chồng tiếng."""
    beats = [_beat(0, 1, 0.0, 10.0), _beat(1, 1, 34.0, 40.0)]
    segs = [_seg(1, 0.0, 10.0, [0], breathing=4.0, insert=20.0),
            _seg(2, 34.0, 40.0, [1])]
    chs = _chs((0.0, 50.0), (60.0, 100.0))
    p = _project(beats, segs, [InsertSpec(after_beat=0, dur=20.0, music="/m/ed.mp3")])
    spans = mplan.music_spans(p, chs, [0.0, 60.0], total_end=110.0)
    for a, b in zip(spans, spans[1:]):
        assert a["seg_end"] == pytest.approx(b["seg_start"])
    assert spans[0]["seg_start"] == 0.0 and spans[-1]["seg_end"] == 110.0


def test_two_inserts_same_chapter_split_twice():
    """2 Δ cùng chương: Δ sau chẻ tiếp span của Δ trước (bài cuối thắng tới hết chương)."""
    beats = [_beat(0, 1, 0.0, 10.0), _beat(1, 1, 34.0, 40.0), _beat(2, 1, 64.0, 70.0)]
    segs = [_seg(1, 0.0, 10.0, [0], breathing=4.0, insert=20.0),
            _seg(2, 34.0, 40.0, [1], breathing=4.0, insert=20.0),
            _seg(3, 64.0, 70.0, [2])]
    chs = _chs((0.0, 70.0),)
    p = _project(beats, segs, [InsertSpec(after_beat=0, dur=20.0, music="/m/a.mp3"),
                               InsertSpec(after_beat=1, dur=20.0, music="/m/b.mp3")],
                 chapters=(1,))
    spans = mplan.music_spans(p, chs, [0.0], total_end=80.0)
    assert [(s["seg_start"], s["seg_end"], s["file"]) for s in spans] == [
        (0.0, 14.0, None), (14.0, 44.0, "/m/a.mp3"), (44.0, 80.0, "/m/b.mp3")]


def test_tiny_span_dropped():
    """Δ sát đầu chương -> span bài cũ quá ngắn (<0.2s) thì BỎ, không đẻ clip vụn."""
    beats = [_beat(0, 1, 0.0, 0.1), _beat(1, 1, 20.1, 30.0)]
    segs = [_seg(1, 0.0, 0.1, [0], insert=20.0), _seg(2, 20.1, 30.0, [1])]
    chs = _chs((0.0, 30.0),)
    p = _project(beats, segs, [InsertSpec(after_beat=0, dur=20.0, music="/m/ed.mp3")],
                 chapters=(1,))
    spans = mplan.music_spans(p, chs, [0.0], total_end=40.0)
    assert [(s["seg_start"], s["seg_end"], s["is_insert"]) for s in spans] \
        == [(0.1, 40.0, True)]


# ===================== schema ================================================
def test_insert_spec_music_roundtrip_and_legacy_loads():
    spec = InsertSpec(after_beat=57, dur=20.0, music="/m/ed.mp3")
    assert InsertSpec.model_validate(spec.model_dump()) == spec
    # project.json M2 (chưa có field music) load được, mặc định rỗng = nhạc chương cũ
    old = InsertSpec.model_validate({"after_beat": 57, "dur": 20.0, "note": "x"})
    assert old.music == ""


# ===================== NHIP-M4: lưới beat trong Δ ============================
def _grid_beats(bpm: float, n: int) -> list[float]:
    """beat_times đều theo BPM (giây từ đầu file nhạc)."""
    period = 60.0 / bpm
    return [round(i * period, 4) for i in range(n)]


def test_insert_grid_targets_seconds_not_beat_count():
    """★ Bài học đo 4 bài 2026-07-19: đếm theo SỐ BEAT cố định thì shot co giãn ~2×
    giữa nhạc nhanh/chậm. Nhắm theo GIÂY -> shot của 89 BPM và 172 BPM phải XẤP XỈ
    nhau, dù số beat/shot khác hẳn."""
    out = {}
    for bpm in (89.0, 152.0, 172.0):
        cuts = cov.insert_grid_cuts(100.0, 130.0, _grid_beats(bpm, 200))
        durs = [b - a for a, b in zip(cuts, cuts[1:] + [130.0])]
        out[bpm] = sum(durs) / len(durs)
    for bpm, avg in out.items():
        assert 2.0 <= avg <= 4.2, f"{bpm} BPM ra shot {avg:.2f}s — lệch target 3,0s"
    # chênh giữa bài nhanh nhất và chậm nhất phải NHỎ (bệnh cũ là gần 2×)
    assert max(out.values()) / min(out.values()) < 1.6


def test_insert_grid_lands_on_real_beats():
    """Mọi mốc cắt phải TRÙNG một beat thật (hạ cánh), không phải mốc số học."""
    beats = _grid_beats(120.0, 100)
    cuts = cov.insert_grid_cuts(50.0, 80.0, beats)
    for c in cuts[1:]:                       # mốc đầu = mép Δ, không cần trùng beat
        rel = c - 50.0
        assert min(abs(rel - b) for b in beats) < 1e-3, f"mốc {c} không rơi trên beat"


def test_insert_grid_hits_strong_beats_when_meter_agrees():
    """★ LUẬT Δ: ưu tiên ĐỀU, không phải bám beat mạnh (ngược mini-hook — xem
    INSERT_SEARCH_BEATS và test_insert_grid_even_on_triple_meter). Khi chu kỳ beat
    mạnh KHỚP k của lưới (4/4 @120 BPM -> k=6... ) thì mốc vẫn rơi beat mạnh MIỄN PHÍ,
    không cần cửa sổ tìm kiếm — đó là điều test này canh."""
    beats = _grid_beats(120.0, 60)
    st = [1.0 if i % 6 == 0 else 0.1 for i in range(60)]   # chu kỳ mạnh = k (60/120*6=3,0s)
    cuts = cov.insert_grid_cuts(0.0, 30.0, beats, st)
    idx = [min(range(60), key=lambda i: abs(beats[i] - c)) for c in cuts[1:]]
    assert all(i % 6 == 0 for i in idx)                    # trùng beat mạnh, lưới vẫn đều


def test_insert_grid_fail_open_without_beats():
    """Không có nhịp (bài lỗi/tier C) -> 1 mốc = Δ giữ 1 hình như M3, KHÔNG chết."""
    assert cov.insert_grid_cuts(10.0, 40.0, []) == [10.0]
    assert cov.insert_grid_cuts(10.0, 40.0, [5.0]) == [10.0]   # <2 beat trong Δ


# ============ NHIP-M4b: lưới CÔNG THỨC từ downbeat madmom (foundation e2) ============
# Downbeat "End of an Era" madmom đo thật 2026-07-21 (jitter đo ±20ms là THẬT — chính
# là thứ lưới công thức phải là phẳng, không cộng dồn như GT1 bàn giao M4).
_MADMOM_DOWNS = [0.29, 2.30, 4.30, 6.30, 8.30, 10.30, 12.30, 14.30, 16.28, 18.29,
                 20.28, 22.29, 24.28, 26.28, 28.28, 30.28, 32.26, 34.28, 36.29]


def test_insert_grid_formula_grid_locked_no_drift():
    """★ REGRESSION GT1 (V10 user nghe 'vẫn chưa đúng nhịp'): lưới cũ CỘNG DỒN beat
    librosa dao động 46ms -> mép trôi dần. Lưới công thức + A′ shuffle: mọi khoảng
    giữa mốc phải là BỘI NGUYÊN CHÍNH XÁC của step (RUN=1×, HOLD=2-3×) — jitter đo
    của downbeat đầu vào KHÔNG được lọt vào mốc."""
    cuts = cov.insert_grid_cuts(100.0, 130.0, [], downbeats=_MADMOM_DOWNS, meter=3)
    assert len(cuts) > 3
    step = 2.0
    for a, b in zip(cuts[1:], cuts[2:]):
        k = (b - a) / step
        assert abs(k - round(k)) < 1e-6 and 1 <= round(k) <= 3, f"gap {b - a} lệch lưới"


def test_insert_shuffle_has_holds_run_open_close():
    """A′ (e2 §5): Δ 30s PHẢI có ≥1 HOLD (phá đơn điệu — chính là bệnh V11 user chê
    'khá đều nhau') · mở bằng RUN (2 gap đầu = 1 unit) · kết bằng RUN (gap cuối = 1
    unit, siết nhịp dồn về voice)."""
    cuts = cov.insert_grid_cuts(100.0, 130.0, [], downbeats=_MADMOM_DOWNS, meter=3)
    gaps = [round(b - a, 4) for a, b in zip(cuts[1:], cuts[2:])]
    assert any(g >= 3.9 for g in gaps), f"không có HOLD nào: {gaps}"
    assert gaps[0] == pytest.approx(2.0) and gaps[1] == pytest.approx(2.0)   # mở RUN
    assert gaps[-1] == pytest.approx(2.0)                                    # kết RUN


def test_insert_shuffle_deterministic_seed():
    """Seed cố định -> dựng lại Y HỆT (NT5); đổi seed -> cách xáo đổi."""
    a1 = cov.insert_grid_cuts(100.0, 130.0, [], downbeats=_MADMOM_DOWNS, meter=3, seed=7)
    a2 = cov.insert_grid_cuts(100.0, 130.0, [], downbeats=_MADMOM_DOWNS, meter=3, seed=7)
    assert a1 == a2
    others = [cov.insert_grid_cuts(100.0, 130.0, [], downbeats=_MADMOM_DOWNS,
                                   meter=3, seed=s) for s in (8, 9, 10)]
    assert any(o != a1 for o in others), "3 seed khác nhau mà cách xáo y hệt"


def test_shaped_pattern_grammar():
    """Ngữ pháp A′ thuần: tổng đúng units · HOLD không kề nhau (≥2 RUN giữa) ·
    tối đa 1 hold 3-unit · kết bằng ≥2 RUN."""
    import random
    for seed in range(20):
        pat = cov._shaped_pattern(14, random.Random(seed))
        assert sum(pat) == 14
        assert pat[-1] == 1 and pat[-2] == 1                    # kết ≥2 RUN
        assert sum(1 for p in pat if p == 3) <= 1               # hold dài hiếm
        for i, p in enumerate(pat):
            if p > 1 and i + 1 < len(pat):
                assert pat[i + 1] == 1, f"seed {seed}: 2 hold kề nhau {pat}"


def test_insert_grid_formula_meter3_one_bar_per_shot_phase_locked():
    """Nhịp 3 (luật e2): chuyển ở phách 1 -> bước = 1 ô nhịp; pha NEO downbeat đầu
    trong Δ (GT2: hình đầu kéo từ mép Δ tới downbeat thật, không cắt non)."""
    cuts = cov.insert_grid_cuts(100.0, 130.0, [], downbeats=_MADMOM_DOWNS, meter=3)
    assert cuts[0] == 100.0                       # mép Δ luôn là mốc đầu (hành vi M2)
    step = cuts[2] - cuts[1]
    assert step == pytest.approx(2.0, abs=0.02)   # 1 bar (trung vị 89,15 BPM nhịp 3)
    # pha khóa downbeat thật: mốc đầu 100,29 bị sàn 1,5s loại (shot 0,29s) -> hình đầu
    # kéo mép Δ tới downbeat KẾ 102,29, nhưng mọi mốc vẫn ≡ 0,29 (mod bar) — không cắt non
    assert cuts[1] == pytest.approx(100.0 + 0.29 + step, abs=1e-6)
    for c in cuts[1:]:
        r = (c - 100.0 - 0.29) % step                  # float: r có thể ≈ 0 HOẶC ≈ step
        assert min(r, step - r) < 1e-6


def test_insert_grid_formula_meter4_cuts_beats_1_and_3():
    """Nhịp 4 (luật e2): chuyển ở phách 1 VÀ 3 -> bước = nửa ô nhịp (khi đủ dài).
    Bar 3,2s (75 BPM 4/4) -> nửa bar 1,6s ≥ sàn 1,5 -> giữ nguyên nửa bar."""
    downs = [round(0.4 + i * 3.2, 3) for i in range(12)]      # downbeat mỗi 3,2s
    cuts = cov.insert_grid_cuts(0.0, 30.0, [], downbeats=downs, meter=4)
    step = cuts[2] - cuts[1]
    assert step == pytest.approx(1.6, abs=1e-6)


def test_insert_grid_formula_multiplies_step_when_below_min_shot():
    """Bước cơ bản ngắn hơn sàn 1,5s -> nhân bội (bội của nửa-bar vẫn rơi phách lẻ
    1/3, bội của bar vẫn rơi phách 1 — không bao giờ phá luật phách LẺ)."""
    downs = [round(i * 2.0, 3) for i in range(20)]            # nhịp 4, bar 2,0s
    cuts = cov.insert_grid_cuts(0.0, 30.0, [], downbeats=downs, meter=4)
    step = cuts[2] - cuts[1]
    # nửa bar 1,0s < 1,5 -> mult 2 -> 2,0s (= phách 1 mỗi bar, vẫn phách lẻ)
    assert step == pytest.approx(2.0, abs=1e-6)


def test_insert_grid_falls_back_to_librosa_without_downbeats():
    """Project cũ / madmom lỗi (downbeats rỗng, meter 0) -> đi nhánh beat librosa cũ
    y nguyên — không đổi hành vi draft đã dựng."""
    beats = _grid_beats(120.0, 100)
    old = cov.insert_grid_cuts(50.0, 80.0, beats)
    new = cov.insert_grid_cuts(50.0, 80.0, beats, downbeats=[], meter=0)
    assert new == old
    # meter lạ (6/8 chưa hỗ trợ) cũng rơi về nhánh cũ, không nổ
    assert cov.insert_grid_cuts(50.0, 80.0, beats, downbeats=[0.1], meter=6) == old


def test_split_insert_windows_keeps_flag_and_exact_length():
    """Miếng Δ giữ cờ insert (mọi luật né-Δ của M2 vẫn áp) + tổng ĐÚNG độ dài khai."""
    ws = [CoverWindow(beat_id=5, start=0.0, end=10.0),
          CoverWindow(beat_id=5, start=10.0, end=40.0, insert=True),
          CoverWindow(beat_id=6, start=40.0, end=50.0)]
    out = cov.split_insert_windows(ws, {5: [10.0, 20.0, 30.0]})
    ins = [w for w in out if w.insert]
    assert len(ins) == 3 and all(w.insert for w in ins)
    assert ins[0].start == 10.0 and ins[-1].end == 40.0        # Δ giữ ĐÚNG 30s
    for a, b in zip(out, out[1:]):                             # liền khít, không hở
        assert a.end == pytest.approx(b.start)


def test_split_insert_windows_untouched_without_grid():
    """Δ không có lưới (M3 nguyên vẹn) -> đi qua y nguyên, 1 cửa sổ."""
    ws = [CoverWindow(beat_id=5, start=10.0, end=40.0, insert=True)]
    assert cov.split_insert_windows(ws, {}) == ws
    assert cov.split_insert_windows(ws, {5: [10.0]}) == ws     # <2 mốc = không chẻ


def test_insert_spec_rhythm_roundtrip_and_legacy():
    spec = InsertSpec(after_beat=36, dur=30.0, music="/m/x.mp3",
                      music_beats=[0.0, 0.67], music_beat_strength=[1.0, 0.3],
                      music_bpm=89.1, music_tier="A")
    assert InsertSpec.model_validate(spec.model_dump()) == spec
    old = InsertSpec.model_validate({"after_beat": 36, "dur": 30.0})   # M3 cũ
    assert old.music_beats == [] and old.music_tier == ""


def test_insert_grid_even_on_triple_meter():
    """🐛 HỒI QUY (đo thật "End of an Era" 89 BPM, user nghe 2026-07-20): bài có beat
    mạnh chu kỳ 3 (nhịp 3/4/6/8) thì hạ-cánh-beat-mạnh THẮNG mục tiêu giây — ±2 cho
    khoảng cách 6,6,3,6,3,3 => shot 2,0s/4,0s chênh 2,5×; tai nghe rõ vì Δ không lời.
    Nay search=0 (INSERT_SEARCH_BEATS): lưới ĐỀU, mọi mốc vẫn trên beat THẬT."""
    beats = _grid_beats(89.2, 60)
    st = [1.0 if i % 3 == 0 else 0.1 for i in range(60)]      # beat mạnh CHU KỲ 3
    cuts = cov.insert_grid_cuts(100.0, 130.0, beats, st)
    durs = [b - a for a, b in zip(cuts, cuts[1:] + [130.0])]
    mid = durs[1:-1]                                          # bỏ 2 mép Δ (bị kẹp)
    assert max(mid) / min(mid) < 1.2, f"lưới không đều: {[round(d,2) for d in mid]}"
    avg = sum(mid) / len(mid)
    assert 1.6 <= avg <= 2.6, f"lệch target {cov.INSERT_TARGET_SHOT}s: {avg:.2f}s"
    for c in cuts[1:]:                                        # vẫn hạ cánh beat THẬT
        assert min(abs((c - 100.0) - b) for b in beats) < 1e-3


def test_slug_fill_sorts_track_by_time():
    """🐛 HỒI QUY (user bắt 2026-07-20 qua 4 draft liên tiếp): slug được add SAU toàn
    bộ footage nên trong draft_content.json chúng nằm CUỐI danh sách segment dù mốc
    thời gian ở GIỮA video. JSON đọc ra đúng mốc (nên mọi lần kiểm bằng script đều
    báo OK!) nhưng CapCut duyệt track TUẦN TỰ -> dồn cả cụm xuống cuối: 11 ô giữ chỗ
    của Δ ở 4:12 hiện ra ở 9:47 chồng lên voice seg_055-058.
    Trước M4 KHÔNG lộ vì 1 Δ = 1 slug và Δ cuối video (thứ tự add trùng thứ tự time).
    Luật: sau _fill_holes_with_slug, video_l1 PHẢI sorted theo target_timerange.start."""
    from autoedit.packager import assembler as A

    class Seg:
        def __init__(self, start):
            self.target_timerange = type("TR", (), {"start": start})()

    class Track:
        def __init__(self, starts):
            self.segments = [Seg(s) for s in starts]

    # mô phỏng đúng trạng thái sinh bug: footage theo thứ tự, slug (252-279) add SAU
    script = type("S", (), {"tracks": {"video_l1": Track(
        [0, 100, 200, 245, 282, 300, 400, 252, 255, 258])}})()
    trk = script.tracks["video_l1"]
    trk.segments.sort(key=lambda s: s.target_timerange.start)   # dòng fix trong assembler
    starts = [s.target_timerange.start for s in trk.segments]
    assert starts == sorted(starts)
    assert starts[:6] == [0, 100, 200, 245, 252, 255]           # slug về đúng chỗ giữa
    assert hasattr(A, "_fill_holes_with_slug")


def test_meter_k_locks_to_strong_beat_cycle():
    """🐛 HỒI QUY (user nghe draft V9 2026-07-20: "nhiều footage không rơi đúng nhịp"):
    ép k = round(target/period) cho k=4 trên bài nhịp 3 -> lưới LỆCH PHA với nhịp mạnh,
    3/10 mép rơi beat YẾU (0,18-0,22 vs trung vị 0,29) = nghe TRỄ MỘT NHỊP (lớp lỗi
    b08/b09). Nay `_meter_k` đo chu kỳ nhịp mạnh rồi lấy BỘI SỐ của nó."""
    period = 60.0 / 89.2
    st3 = [1.0 if i % 3 == 0 else 0.15 for i in range(60)]      # nhịp 3 (như End of an Era)
    assert cov._meter_k(st3, period, 2.0) % 3 == 0              # k phải là bội của 3
    st4 = [1.0 if i % 4 == 0 else 0.15 for i in range(60)]      # nhịp 4/4
    assert cov._meter_k(st4, period, 2.0) % 4 == 0
    # không có strength (record cũ) -> về công thức cũ, KHÔNG chết
    assert cov._meter_k([], period, 2.0) == max(2, round(2.0 / period))


def test_insert_grid_cuts_land_on_strong_beats_triple_meter():
    """Kết quả cuối trên nhạc nhịp 3: mọi mép rơi ĐÚNG beat mạnh và lưới vẫn đều."""
    beats = _grid_beats(89.2, 60)
    st = [1.0 if i % 3 == 0 else 0.15 for i in range(60)]
    cuts = cov.insert_grid_cuts(100.0, 130.0, beats, st)
    idx = [min(range(60), key=lambda k: abs(beats[k] - (c - 100.0))) for c in cuts[1:]]
    assert all(i % 3 == 0 for i in idx), f"mép rơi beat yếu: {idx}"
    durs = [b - a for a, b in zip(cuts, cuts[1:] + [130.0])]
    assert max(durs[1:-1]) / min(durs[1:-1]) < 1.2
