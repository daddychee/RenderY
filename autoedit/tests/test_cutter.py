"""Test M4 — hệ tọa độ kép (RA_SOAT 3.3, bắt buộc), silence snap, integration ffmpeg."""

from __future__ import annotations

import math
import shutil
import struct
import wave
from pathlib import Path

import pytest

from autoedit.cutter import silence as sil
from autoedit.cutter import timeline as tl
from autoedit.cutter.runner import run_cut
from autoedit.project import Beat, SearchQueries, Stage, StageStatus, Word, create_project

BR = 3.0  # breathing test


def _beat(beat_id: int, start: float, end: float, breathing=False) -> Beat:
    return Beat(
        beat_id=beat_id, chapter=1, text=f"beat {beat_id}", start_word=0, end_word=1,
        start=start, end=end, energy="medium", mood="m", visual_level="literal",
        visual_concept="c", shot_size="medium",
        search_queries=SearchQueries(specific=["q"]), breathing_after=breathing,
    )


# ===================== hệ tọa độ kép (3.3) — pure =============================
def test_no_breathing_single_segment_timeline_equals_source():
    beats = [_beat(0, 0.0, 2.0), _beat(1, 2.0, 5.0)]
    plans = tl.apply_timeline(tl.plan_segments(beats))
    assert len(plans) == 1
    assert plans[0].source_start == 0.0 and plans[0].source_end == 5.0
    assert plans[0].timeline_start == 0.0 and plans[0].timeline_end == 5.0
    bt = tl.map_beats_to_timeline(beats, plans)
    assert bt[0] == (0.0, 2.0) and bt[1] == (2.0, 5.0)


def test_one_breathing_shifts_following_beats_only():
    beats = [_beat(0, 0.0, 2.0), _beat(1, 2.0, 4.0, breathing=True),
             _beat(2, 4.0, 6.0), _beat(3, 6.0, 8.0)]
    plans = tl.apply_timeline(tl.plan_segments(beats))
    assert len(plans) == 2
    # SOURCE bất biến — ổ bug kinh điển nằm ở đây
    assert plans[1].source_start == 4.0 and plans[1].source_end == 8.0
    # TIMELINE: segment 2 dịch đúng +3s
    assert plans[1].timeline_start == pytest.approx(4.0 + BR)
    bt = tl.map_beats_to_timeline(beats, plans)
    assert bt[0] == (0.0, 2.0) and bt[1] == (2.0, 4.0)          # trước hình thở: không dịch
    assert bt[2] == (pytest.approx(7.0), pytest.approx(9.0))    # sau: +3
    assert bt[3] == (pytest.approx(9.0), pytest.approx(11.0))
    # beat sau hình thở vẫn giữ nguyên SOURCE trên object beat
    assert beats[2].start == 4.0 and beats[2].end == 6.0


def test_multiple_breathing_accumulates():
    beats = [_beat(0, 0.0, 2.0, breathing=True), _beat(1, 2.0, 4.0, breathing=True),
             _beat(2, 4.0, 6.0)]
    plans = tl.apply_timeline(tl.plan_segments(beats))
    assert len(plans) == 3
    bt = tl.map_beats_to_timeline(beats, plans)
    assert bt[2] == (pytest.approx(4.0 + 2 * BR), pytest.approx(6.0 + 2 * BR))


def test_breathing_on_last_beat_adds_no_gap():
    beats = [_beat(0, 0.0, 2.0), _beat(1, 2.0, 4.0, breathing=True)]
    plans = tl.apply_timeline(tl.plan_segments(beats))
    assert len(plans) == 1
    assert plans[0].breathing_after == 0.0
    assert plans[0].timeline_end == 4.0


def test_invariants_total_and_no_overlap():
    beats = [_beat(0, 0.0, 3.0, breathing=True), _beat(1, 3.0, 5.5),
             _beat(2, 5.5, 7.0, breathing=True), _beat(3, 7.0, 10.0)]
    plans = tl.apply_timeline(tl.plan_segments(beats))
    total_source = sum(p.duration for p in plans)
    total_breathing = sum(p.breathing_after for p in plans)
    assert plans[-1].timeline_end == pytest.approx(total_source + total_breathing)
    for a, b in zip(plans, plans[1:]):
        assert b.source_start >= a.source_end          # không đè source
        assert b.timeline_start == pytest.approx(a.timeline_end + a.breathing_after)


def test_map_beats_requires_applied_timeline():
    beats = [_beat(0, 0.0, 2.0)]
    plans = tl.plan_segments(beats)
    with pytest.raises(ValueError, match="apply_timeline"):
        tl.map_beats_to_timeline(beats, plans)


# ===================== silence ================================================
FFMPEG_STDERR_SAMPLE = """\
[silencedetect @ 0x600] silence_start: 1.95833
[silencedetect @ 0x600] silence_end: 2.45833 | silence_duration: 0.5
[silencedetect @ 0x600] silence_start: 8.1
[silencedetect @ 0x600] silence_end: 8.41667 | silence_duration: 0.316667
size=N/A time=00:00:27.40 bitrate=N/A speed= 851x
"""


def test_parse_silencedetect():
    assert sil.parse_silencedetect(FFMPEG_STDERR_SAMPLE) == [
        (1.95833, 2.45833), (8.1, 8.41667)]
    assert sil.parse_silencedetect("no silence here") == []


def test_snap_to_silence():
    silences = [(1.9, 2.5), (8.1, 8.4)]
    # ranh giới 2.05 nằm trong khoảng lặng -> kéo về điểm giữa nhưng kẹp trong cửa sổ
    t, snapped = sil.snap_to_silence(2.05, silences, window=0.2)
    assert snapped and t == pytest.approx(2.2, abs=0.06)  # mid=2.2
    # ngoài cửa sổ -> giữ nguyên
    t, snapped = sil.snap_to_silence(5.0, silences, window=0.2)
    assert not snapped and t == 5.0
    # gần 2 khoảng -> chọn gần hơn
    t, snapped = sil.snap_to_silence(8.05, [(7.8, 7.95), (8.1, 8.4)], window=0.2)
    assert snapped and t >= 8.05  # khoảng (8.1,8.4) gần hơn về phía giữa kẹp cửa sổ


# ===================== integration (ffmpeg thật) ==============================
needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="cần ffmpeg")


def _write_tone_wav(path: Path, spec: list[tuple[float, bool]], rate: int = 48000) -> None:
    """Sinh WAV: spec = [(giây, có_tiếng)] — tone 440Hz hoặc im lặng."""
    frames = bytearray()
    for dur, voiced in spec:
        n = int(dur * rate)
        for i in range(n):
            v = int(12000 * math.sin(2 * math.pi * 440 * i / rate)) if voiced else 0
            frames += struct.pack("<h", v)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))


@pytest.fixture
def cut_project(tmp_path):
    """Project giả lập đã qua direct: voice 2s tiếng + 0.5s lặng + 2.5s tiếng."""
    script = tmp_path / "script.txt"
    script.write_text("a b", encoding="utf-8")
    voice = tmp_path / "voice.wav"
    _write_tone_wav(voice, [(2.0, True), (0.5, False), (2.5, True)])
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    p.transcript = [Word(text="a", start=0.0, end=2.0), Word(text="b", start=2.5, end=5.0)]
    p.beats = [_beat(0, 0.0, 2.1, breathing=True), _beat(1, 2.4, 5.0)]
    p.stages[Stage.ALIGN].status = StageStatus.DONE
    p.stages[Stage.DIRECT].status = StageStatus.DONE
    p.save()
    return p


@needs_ffmpeg
def test_run_cut_end_to_end(cut_project):
    from autoedit.project import Project, ffprobe_duration

    run_cut(cut_project)
    saved = Project.load(cut_project.project_dir)
    assert saved.stages[Stage.CUT].status == StageStatus.DONE
    assert len(saved.segments) == 2
    pdir = Path(saved.project_dir)

    s1, s2 = saved.segments
    # vùng nghỉ transcript (2.1 -> 2.4, gap 0.3 < tail+lead) -> chia 60/40 trong vùng
    assert 2.1 <= s1.source_end <= 2.4
    assert s2.source_start >= s1.source_end   # được hở, cấm đè
    assert s2.source_start <= 2.4              # không phạm khởi âm từ sau (beat 1 start 2.4)
    # hệ tọa độ kép trên kết quả thật. SHOT THỞ 2.0: ô NÃO 3.0 đạt ngưỡng -> máy kéo
    # sâu = hold 0.5 + footage f=0.5 (ô duy nhất) = 0.5 + 5.3 = 5.8s; base giữ số NÃO
    assert saved.beats[0].breathing_base == pytest.approx(BR)
    assert saved.beats[0].breathing_after == pytest.approx(5.8)
    assert s2.timeline_start == pytest.approx(s1.timeline_end + 5.8)
    assert saved.beats[1].timeline_start == pytest.approx(
        saved.beats[1].start + (s2.timeline_start - s2.source_start), abs=1e-3
    )
    # file thật tồn tại, duration đúng kế hoạch
    for s in (s1, s2):
        f = pdir / s.path
        assert f.is_file()
        assert ffprobe_duration(f) == pytest.approx(s.source_end - s.source_start, abs=0.05)
    assert (pdir / "segments" / "INDEX.txt").is_file()
    assert saved.voice_master_path  # master WAV đã tạo


@needs_ffmpeg
def test_run_cut_rerun_overwrites_clean(cut_project):
    from autoedit.project import Project

    run_cut(cut_project)
    p2 = Project.load(cut_project.project_dir)
    run_cut(p2)
    saved = Project.load(cut_project.project_dir)
    seg_files = sorted((Path(saved.project_dir) / "segments").glob("*.wav"))
    assert len(seg_files) == len(saved.segments) == 2  # không nhân đôi


def test_run_cut_requires_direct(cut_project):
    cut_project.stages[Stage.DIRECT].status = StageStatus.PENDING
    cut_project.save()
    with pytest.raises(RuntimeError, match="direct"):
        run_cut(cut_project)


# ============== giãn nghỉ máy — hình thở 3.0 (DNA nhịp nghỉ, pure) ============
from autoedit.cutter import pause as pz  # noqa: E402


def _pbeat(bid, start, end, text, breathing=0.0, rhet=False) -> Beat:
    b = _beat(bid, start, end)
    b.text, b.breathing_after, b.rhetorical_pause = text, breathing, rhet
    return b


def test_micro_pause_never_stretches_mid_clause():
    """Regression nỗi lo user 2026-07-08: lặng dài nhưng KHÔNG CÓ DẤU (giữa mệnh đề)
    và KHÔNG có cờ câu đinh của đạo diễn → máy tuyệt đối không giãn."""
    beats = [_pbeat(0, 0.0, 30.0, "the storm keeps growing"),
             _pbeat(1, 30.6, 60.0, "bigger than Jupiter itself"),
             _pbeat(2, 60.6, 90.0, "and it never stops.")]
    assert pz.plan_micro_pauses(beats) == {}  # beat 2 kết câu nhưng là beat cuối


def test_rhetorical_pause_needs_flag_and_real_gap():
    """Câu đinh: cờ NÃO trên beat không dấu → ngắt δ = clamp(1.0 − nghỉ, 0.2-0.6);
    cờ mà voice đọc liền (khóa nghỉ thật) → máy tự bỏ."""
    beats = [_pbeat(0, 0.0, 30.0, "every room in our cosmic house", rhet=True),   # gap 0.6
             _pbeat(1, 30.6, 33.0, "but one before the fall", rhet=True),         # gap 0.1 — liền
             _pbeat(2, 33.1, 90.0, "ends.")]
    got = pz.plan_micro_pauses(beats)
    assert got == {0: pytest.approx(0.4)}   # 1.0 − 0.6
    assert 1 not in got


def test_sentence_lock_and_single_point_maps_to_p50():
    """Khóa 2 giữ: kết câu nhưng nghỉ <0.3s → bỏ. 1 điểm chọn → rank giữa → target
    = p50 DNA (1.55) → δ = 1.55 − nghỉ."""
    beats = [_pbeat(0, 0.0, 30.0, "First idea."),      # gap 0.1 — quá ngắn
             _pbeat(1, 30.1, 60.0, "Second idea."),     # gap 0.5 — đạt
             _pbeat(2, 60.5, 90.0, "tail no punct")]
    got = pz.plan_micro_pauses(beats)
    assert list(got) == [1]
    assert got[1] == pytest.approx(1.05)    # 1.55 − 0.5


def test_clause_tier_target_and_guard_3s():
    """Tầng mệnh đề map lên phân bố riêng (p50 0.95); guard 3s chặn điểm dính điểm câu."""
    beats = [_pbeat(0, 0.0, 20.0, "First sentence."),      # câu — δ = 1.55 − 0.6 = 0.95
             _pbeat(1, 20.6, 22.5, "blocked by guard,"),   # pt 22.5, cách 2.5s < 3 — chặn
             _pbeat(2, 23.0, 28.0, "far enough now,"),     # pt 28, cách 8s — δ = 0.95 − 0.4
             _pbeat(3, 28.4, 60.0, "tail")]
    got = pz.plan_micro_pauses(beats)
    assert got[0] == pytest.approx(0.95)
    assert 1 not in got
    assert got[2] == pytest.approx(0.55)
    assert pz.plan_micro_pauses(beats) == got  # deterministic


def test_quantile_mapping_orders_by_natural_pause():
    """Quantile-rank mapping: điểm voice tự nghỉ dài nhận nghe-ra sâu hơn điểm nghỉ
    ngắn; δ không vượt trần 1.1; deterministic."""
    beats, t = [], 0.0
    for i in range(10):
        gap = 0.375 if i % 2 == 0 else 0.75   # số nhị phân chính xác — cộng dồn không nhiễu
        beats.append(_pbeat(i, t, t + 15.0, f"Sentence {i}."))
        t += 15.0 + gap
    got = pz.plan_micro_pauses(beats)
    assert len(got) == 9                                   # đủ ứng viên, K cho phép hết
    assert all(0.15 <= v <= 1.10 + 1e-9 for v in got.values())
    assert got[0] == pytest.approx(0.685, abs=0.011)       # rank thấp nhất → p10 1.06 − 0.375
    assert len(set(got.values())) >= 4                     # mapping trải phổ, không đơn điệu
    nghe_ngan = [0.375 + got[i] for i in (0, 2, 4, 6, 8)]  # điểm nghỉ nguồn ngắn
    nghe_dai = [0.75 + got[i] for i in (1, 3, 5, 7)]       # điểm nghỉ nguồn dài
    assert max(nghe_ngan) <= min(nghe_dai) + 1e-9          # thứ bậc theo ngữ điệu voice
    assert pz.plan_micro_pauses(beats) == got


def test_budget_cap_counts_breathing():
    """Trần ngân sách 13% duration tính CẢ thở đạo diễn — thở ăn hết thì máy nhịn."""
    beats = [_pbeat(0, 0.0, 20.0, "A.", breathing=6.0),
             _pbeat(1, 20.6, 25.0, "B."),                  # gap 0.6, cách điểm thở 5s ≥ 3
             _pbeat(2, 25.6, 45.0, "C.")]
    assert pz.plan_micro_pauses(beats) == {}               # budget 45×0.13 − 6 < 0
    beats[0].breathing_after = 1.5
    got = pz.plan_micro_pauses(beats)
    assert got == {1: pytest.approx(0.95)}                 # budget 4.35 → giữ (1.55 − 0.6)


def test_pause_dna_loader_fails_open_and_plan_honors_dna():
    """Thiếu niche/file → POOLED_DNA; dna truyền vào đổi anchors thì δ đổi theo."""
    assert pz.load_pause_dna(None) is pz.POOLED_DNA
    assert pz.load_pause_dna("niche-khong-ton-tai-xyz") is pz.POOLED_DNA
    beats = [_pbeat(0, 0.0, 30.0, "First idea."),
             _pbeat(1, 30.5, 60.0, "tail no punct")]
    flat = {**pz.POOLED_DNA,
            "sent": {**pz.POOLED_DNA["sent"], "anchors": [0.8, 0.8, 0.8, 0.8, 0.8]}}
    got = pz.plan_micro_pauses(beats, dna=flat)
    assert got == {0: pytest.approx(0.3)}                  # 0.8 − 0.5


def test_micro_pause_inserts_timeline_gap():
    beats = [_beat(0, 0.0, 2.0), _beat(1, 2.0, 4.0), _beat(2, 4.0, 6.0)]
    beats[0].micro_pause_after = 0.5
    plans = tl.apply_timeline(tl.plan_segments(beats))
    assert len(plans) == 2
    assert plans[0].micro_pause_after == 0.5
    assert plans[1].timeline_start == pytest.approx(2.5)
    bt = tl.map_beats_to_timeline(beats, plans)
    assert bt[1] == (pytest.approx(2.5), pytest.approx(4.5))
    assert beats[1].start == 2.0  # SOURCE bất biến


def test_micro_pause_on_last_beat_adds_no_gap():
    beats = [_beat(0, 0.0, 2.0)]
    beats[0].micro_pause_after = 0.5
    plans = tl.apply_timeline(tl.plan_segments(beats))
    assert plans[0].micro_pause_after == 0.0 and plans[0].timeline_end == 2.0


# ===================== SHOT THỞ 2.0 — kéo sâu ô (MO_TA_SHOT_THO §6.2A) =========
def _b(bid, start, end, breathing=0.0, chapter=1):
    b = _beat(bid, start, end)
    b.breathing_after = breathing
    b.chapter = chapter
    return b


def test_plan_breath_depth_maps_qualifying_holes():
    """Ô đạt ngưỡng nhận đích [hold+4.0, hold+cap]; rank NÃO sâu hơn -> đích sâu hơn;
    ô dưới ngưỡng + beat cuối video KHÔNG đụng."""
    beats = [
        _b(0, 0.0, 10.0, breathing=2.5),              # giữa chương, đạt
        _b(1, 12.5, 20.0, breathing=1.5),             # cuối chương (b2 chương 2), đạt
        _b(2, 21.5, 30.0, breathing=2.0, chapter=2),  # nông -> không
        _b(3, 32.0, 40.0, breathing=3.0, chapter=2),  # beat cuối video -> không
    ]
    got = pz.plan_breath_depth(beats)
    assert set(got) == {0, 1}
    # n=2: b1 rank nông (NÃO 1.5) -> f=0.25 -> footage 4.5; b0 (2.5) -> f=0.75 -> 6.8
    assert got[1] == pytest.approx(5.0) and got[0] == pytest.approx(7.3)
    assert beats[2].breathing_after == 2.0  # plan là pure — không mutate


def test_plan_breath_depth_idempotent_via_base_reset():
    """Bẫy chạy lại cut: reset về base -> plan ra Y HỆT, không cộng dồn."""
    beats = [_b(0, 0.0, 10.0, breathing=2.5), _b(1, 12.5, 20.0, chapter=1),
             _b(2, 21.5, 30.0, breathing=6.0, chapter=2)]
    by_id = {b.beat_id: b for b in beats}
    pz.reset_breathing_to_base(beats)                 # backfill base từ số NÃO cũ
    assert beats[0].breathing_base == 2.5
    first = pz.plan_breath_depth(beats)
    assert set(first) == {0}                          # b2 cuối video không nhận
    for bid, sec in first.items():
        by_id[bid].breathing_after = sec
    pz.reset_breathing_to_base(beats)                 # lần cut sau
    assert beats[0].breathing_after == 2.5            # về đúng số NÃO
    assert pz.plan_breath_depth(beats) == first


# ============ ngắt nhịp trong voice -> hình thở + chống vứt voice (05/09) =====
def test_tieng_trong_vung_tinh_dung():
    from autoedit.cutter.runner import _tieng_trong_vung

    sil = [(2.0, 4.0)]
    assert _tieng_trong_vung(2.0, 4.0, sil) == pytest.approx(0.0)   # lặng sạch
    assert _tieng_trong_vung(1.5, 4.0, sil) == pytest.approx(0.5)   # 0.5s tiếng đầu
    assert _tieng_trong_vung(2.0, 4.0, []) == pytest.approx(2.0)    # không silence = toàn tiếng


@needs_ffmpeg
def test_ngat_nhip_sach_thanh_hinh_tho(tmp_path):
    """User 05/09: người đọc ngắt >=1s (đo SẠCH tiếng) -> breathing_after ĐÚNG độ
    dài ngắt, timeline chèn lại y nguyên (LI100 từng vứt 305s, chèn lại 181s)."""
    from autoedit.cutter.runner import run_cut
    from autoedit.project import Project

    script = tmp_path / "s.txt"; script.write_text("a b", encoding="utf-8")
    voice = tmp_path / "v.wav"
    _write_tone_wav(voice, [(2.0, True), (2.0, False), (2.0, True)])
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    p.transcript = [Word(text="a", start=0.0, end=2.0), Word(text="b", start=4.0, end=6.0)]
    p.beats = [_beat(0, 0.0, 2.0), _beat(1, 4.0, 6.0)]
    p.stages[Stage.ALIGN].status = StageStatus.DONE
    p.stages[Stage.DIRECT].status = StageStatus.DONE
    p.save()

    run_cut(p)
    saved = Project.load(p.project_dir)
    assert saved.beats[0].breathing_after == pytest.approx(2.0, abs=0.15)
    assert any("ngắt nhịp trong voice" in w
               for w in saved.stages[Stage.CUT].warnings)
    a, b = saved.segments
    # timeline giữa 2 segment hở đúng bằng ngắt (thở) — không co video
    assert b.timeline_start - a.timeline_end == pytest.approx(
        saved.beats[0].breathing_after + saved.beats[0].micro_pause_after, abs=0.05)


@needs_ffmpeg
def test_gap_co_tieng_khong_vut_voice(tmp_path):
    """Bug 05/09 (câu 5s mất 2-3s voice): vùng "nghỉ theo transcript" mà CÓ TIẾNG
    (align sót từ) thì CẤM vứt — lấy trọn vào segment sau, tổng voice giữ nguyên."""
    from autoedit.cutter.runner import run_cut
    from autoedit.project import Project

    script = tmp_path / "s.txt"; script.write_text("a b", encoding="utf-8")
    voice = tmp_path / "v.wav"
    _write_tone_wav(voice, [(6.0, True)])          # tiếng LIỀN 6s — transcript lại hở 2-4s
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    p.transcript = [Word(text="a", start=0.0, end=2.0), Word(text="b", start=4.0, end=6.0)]
    p.beats = [_beat(0, 0.0, 2.0, breathing=True), _beat(1, 4.0, 6.0)]
    p.stages[Stage.ALIGN].status = StageStatus.DONE
    p.stages[Stage.DIRECT].status = StageStatus.DONE
    p.save()

    run_cut(p)
    saved = Project.load(p.project_dir)
    tong = sum(sg.source_end - sg.source_start for sg in saved.segments)
    assert tong == pytest.approx(6.0, abs=0.25)    # KHÔNG mất 2s "gap" có tiếng
    assert any("TIẾNG" in w for w in saved.stages[Stage.CUT].warnings)
    # gap bẩn KHÔNG được nhận là ngắt chủ động
    assert saved.beats[0].breathing_after != pytest.approx(2.0, abs=0.1)
