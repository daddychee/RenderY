"""Test MUSIC SYNC M1 (M-STAGE) — stage `music` giữa cut→source.

Gate M1 (MO_TA_VAN_HANH_MUSIC_SYNC.md §4): cùng input -> chọn ĐÚNG bài như đường cũ;
neo offset accent/downbeat; stale khi cut chạy lại; assemble đọc plan (offset nguyên
vẹn, không đếm usage đôi) và fallback đường cũ khi không có plan.
"""

from __future__ import annotations

import json
import math
import shutil
import struct
import subprocess
import wave
from pathlib import Path

import pytest

from autoedit.music.plan import (
    ANCHOR_WIN,
    MUSIC_XFADE,
    SNAP_LEAD,
    anchor_offset,
    chapters_with_time,
    mark_music_stale,
    run_music,
)
from autoedit.project import (
    Beat,
    MusicPlanEntry,
    Project,
    SearchQueries,
    ShotPick,
    Stage,
    StageRecord,
    StageStatus,
    VoiceSegment,
    Word,
    create_project,
)


# ===================== anchor_offset (pure) ===================================
def test_anchor_tier_a_uu_tien_downbeat():
    track = {"beat_tier": "A", "downbeats": [10.0, 14.0], "accents": [11.4]}
    # cắt chương cách đầu segment 3s (XFADE) -> vị trí trong bài tại cắt = 8.5+3 = 11.5
    off, note = anchor_offset(8.5, 3.0, track)
    # downbeat 10.0 (|Δ|=1.5 ≤ 2) thắng dù accent 11.4 gần hơn — tier A ưu tiên downbeat
    assert off == pytest.approx(10.0 - SNAP_LEAD - 3.0)
    assert "downbeat" in note


def test_anchor_tier_b_chi_accent():
    track = {"beat_tier": "B", "downbeats": [10.0], "accents": [11.4]}
    off, note = anchor_offset(8.5, 3.0, track)
    assert off == pytest.approx(11.4 - SNAP_LEAD - 3.0) and "accent" in note


def test_anchor_tier_c_va_ngoai_cua_so_giu_nguyen():
    assert anchor_offset(8.5, 3.0, {"beat_tier": "C", "accents": [11.4]})[0] == 8.5
    # không mục tiêu trong ±ANCHOR_WIN -> giữ offset section
    track = {"beat_tier": "B", "accents": [11.5 + ANCHOR_WIN + 0.1]}
    assert anchor_offset(8.5, 3.0, track)[0] == 8.5


def test_anchor_khong_am():
    # target quá gần đầu bài: offset kẹp 0 (không được âm)
    off, _ = anchor_offset(0.0, 3.0, {"beat_tier": "B", "accents": [1.2]})
    assert off == 0.0


# ===================== fixtures project + lib =================================
def _beat(beat_id, ch, ts, te) -> Beat:
    return Beat(
        beat_id=beat_id, chapter=ch, text=f"b{beat_id}", start_word=0, end_word=1,
        start=ts, end=te, timeline_start=ts, timeline_end=te,
        energy="medium", mood="m", visual_level="literal", visual_concept="c",
        shot_size="medium", search_queries=SearchQueries(specific=["q"]),
    )


def _project_after_cut(tmp_path) -> Project:
    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    p.outline = {"chapters": [
        {"chapter_id": 1, "mood": "calm", "energy": "medium"},
        {"chapter_id": 2, "mood": "urgent", "energy": "medium"},
    ]}
    p.beats = [_beat(0, 1, 0.0, 10.0), _beat(1, 2, 10.0, 20.0)]
    p.segments = [VoiceSegment(segment_id=1, path="segments/seg_001.wav",
                               source_start=0.0, source_end=20.0,
                               timeline_start=0.0, timeline_end=20.0, beat_ids=[0, 1])]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT):
        p.stages[st].status = StageStatus.DONE
    p.save()
    return p


def _lib(tmp_path, tracks: list[dict]) -> Path:
    from autoedit.music.library import _save_index
    lib = tmp_path / "musiclib"
    (lib / "tracks").mkdir(parents=True)
    base = {"vocals": "instrumental", "duration_sec": 60.0, "loopable": True,
            "energy": 0.5, "tempo_class": "medium", "beat_tier": "C",
            "accents": [], "downbeats": [], "sections": {}}
    _save_index(lib, [{**base, **t} for t in tracks])
    return lib


def _make_wav(path: Path, seconds: float) -> None:
    rate = 48000
    frames = bytearray()
    for i in range(int(seconds * rate)):
        frames += struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i / rate)))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(bytes(frames))


# ===================== run_music ==============================================
def test_run_music_chon_dung_bai_nhu_duong_cu(tmp_path):
    """Gate M1: stage music phải chọn Y HỆT select_music đường cũ (cùng input)."""
    from autoedit.music.library import load_usage
    from autoedit.music.select import select_music

    p = _project_after_cut(tmp_path)
    lib = _lib(tmp_path, [{"file": "peace.mp3", "mood": ["peaceful", "hopeful"]},
                          {"file": "tense.mp3", "mood": ["tense", "dark"]}])
    # đường cũ (như assemble tự chọn hôm nay)
    from autoedit.music.library import _load_index
    old = select_music(chapters_with_time(p), _load_index(lib), usage={})
    old_files = {pk["chapter_id"]: pk["file"] for pk in old}
    assert old_files == {1: "peace.mp3", 2: "tense.mp3"}   # sanity: calm->peace, urgent->tense

    p = run_music(p, lib)
    assert {e.chapter_id: e.file for e in p.music_plan} == old_files
    assert p.stages[Stage.MUSIC].status == StageStatus.DONE
    # usage đếm Ở STAGE MUSIC (assemble dùng plan sẽ không đếm nữa)
    assert load_usage(lib) == {"peace.mp3": 1, "tense.mp3": 1}
    # resume được: load lại từ đĩa vẫn còn plan
    assert Project.load(p.project_dir).music_plan[0].file == "peace.mp3"


def test_run_music_neo_offset_accent(tmp_path):
    p = _project_after_cut(tmp_path)
    # ch2 bắt đầu 10s -> nhạc vào sớm XFADE=3 -> vị trí bài tại cắt = 0+3; accent 3.5 trong ±2
    lib = _lib(tmp_path, [{"file": "a.mp3", "mood": ["peaceful"]},
                          {"file": "b.mp3", "mood": ["tense"], "beat_tier": "B",
                           "accents": [3.5, 30.0]}])
    p = run_music(p, lib)
    by_ch = {e.chapter_id: e for e in p.music_plan}
    assert by_ch[2].file == "b.mp3"
    assert by_ch[2].start_offset == pytest.approx(3.5 - SNAP_LEAD - MUSIC_XFADE)
    assert by_ch[1].start_offset == 0.0            # tier C giữ nguyên


def test_run_music_doi_cut_xong(tmp_path):
    p = _project_after_cut(tmp_path)
    p.stages[Stage.CUT] = StageRecord()            # cut chưa done
    lib = _lib(tmp_path, [{"file": "a.mp3", "mood": ["peaceful"]}])
    with pytest.raises(RuntimeError, match="cut"):
        run_music(p, lib)


# ===================== stale khi cut chạy lại =================================
def test_mark_music_stale():
    p_dict = dict(project_id="x", title="x", created_at="t", project_dir="/tmp/x",
                  inputs=dict(script_path="s", voice_path="v", original_script_path="s",
                              original_voice_path="v", script_text="a"))
    p = Project.model_validate(p_dict)
    assert mark_music_stale(p) is None             # chưa từng chạy music -> không có gì xóa
    p.music_plan = [MusicPlanEntry(chapter_id=1, file="a.mp3")]
    p.stages[Stage.MUSIC] = StageRecord(status=StageStatus.DONE)
    msg = mark_music_stale(p)
    assert msg and "music_plan" in msg
    assert p.music_plan == [] and p.stages[Stage.MUSIC].status == StageStatus.PENDING


# ===================== assemble đọc plan / fallback (ffmpeg) ==================
needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="cần ffmpeg")


def _make_clip(path: Path, seconds: float) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", f"testsrc=duration={seconds}:size=320x240:rate=30",
         "-pix_fmt", "yuv420p", str(path)],
        check=True, capture_output=True, timeout=120,
    )


@pytest.fixture
def fake_profile(tmp_path):
    from autoedit.packager.machine import MachineProfile
    root = tmp_path / "com.lveditor.draft"
    root.mkdir()
    return MachineProfile(
        donor_name="donor", capcut_root=str(root), capcut_app_version="8.1.1",
        content_overrides={
            "platform": {"os": "mac"}, "last_modified_platform": {"os": "mac"},
            "new_version": "173.0.0", "version": 360000, "draft_type": "video",
            "function_assistant_info": {}, "mixed_track_mode_on": False,
            "smart_ads_info": {}, "uneven_animation_template_info": {},
        },
        meta_template={"draft_name": "donor", "draft_cover": ""},
    )


def _assemble_ready_project(tmp_path) -> tuple[Project, Path]:
    """Project 1 chương đủ điều kiện assemble + lib nhạc có 1 bài wav thật."""
    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir(); _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    (pdir / "assets").mkdir(); _make_clip(pdir / "assets" / "b000.mp4", 5.0)
    p.transcript = [Word(text="a", start=0.0, end=4.0)]
    p.beats = [_beat(0, 1, 0.0, 4.0)]
    p.segments = [VoiceSegment(segment_id=1, path="segments/seg_001.wav",
                               source_start=0.0, source_end=4.0,
                               timeline_start=0.0, timeline_end=4.0, beat_ids=[0])]
    p.shots = [ShotPick(beat_id=0, status="ok", source="local",
                        asset_path="assets/b000.mp4", asset_key="local:1")]
    p.outline = {"chapters": [{"chapter_id": 1, "mood": "calm", "energy": "medium"}]}
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    lib = tmp_path / "musiclib"
    (lib / "tracks").mkdir(parents=True)
    _make_wav(lib / "tracks" / "t1.wav", 12.0)
    from autoedit.music.library import _save_index
    _save_index(lib, [{"file": "t1.wav", "mood": ["peaceful"], "vocals": "instrumental",
                       "duration_sec": 12.0, "loopable": True, "energy": 0.5,
                       "tempo_class": "medium", "beat_tier": "B", "accents": [2.08],
                       "downbeats": [], "sections": {}}])
    return p, lib


@needs_ffmpeg
def test_assemble_dung_plan_offset_nguyen_ven(tmp_path, fake_profile):
    """Có music_plan -> assemble đặt đúng bài + đúng offset đã neo, KHÔNG đếm usage."""
    from autoedit.music.library import load_usage
    from autoedit.packager.assembler import run_assemble

    p, lib = _assemble_ready_project(tmp_path)
    p.music_plan = [MusicPlanEntry(chapter_id=1, file="t1.wav", start_offset=2.0,
                                   beat_tier="B", anchor_note="accent 2.08s")]
    p.stages[Stage.MUSIC] = StageRecord(status=StageStatus.DONE)
    p.save()
    run_assemble(p, fake_profile, music_lib=lib)

    saved = Project.load(p.project_dir)
    info = json.loads((Path(saved.draft_path) / "draft_info.json").read_text())
    tracks = {t["name"]: t for t in info["tracks"]}
    m_seg = tracks["music"]["segments"][0]
    assert m_seg["source_timerange"]["start"] == 2_000_000   # offset plan giữ nguyên (µs)
    assert saved.music_selections == {"1": "t1.wav"}
    assert load_usage(lib) == {}                              # stage music đếm, assemble KHÔNG
    assert any("music_plan" in w for w in saved.stages[Stage.ASSEMBLE].warnings)


@needs_ffmpeg
def test_assemble_khong_plan_fallback_duong_cu(tmp_path, fake_profile):
    """Không có plan -> assemble tự chọn như cũ + đếm usage (đường cũ nguyên vẹn)."""
    from autoedit.music.library import load_usage
    from autoedit.packager.assembler import run_assemble

    p, lib = _assemble_ready_project(tmp_path)
    run_assemble(p, fake_profile, music_lib=lib)

    saved = Project.load(p.project_dir)
    assert saved.music_selections == {"1": "t1.wav"}          # tự chọn như cũ
    assert load_usage(lib) == {"t1.wav": 1}                   # usage đếm ở assemble như cũ


# ===================== M2 M-VOL: volume nhạc theo zone hook/body ==============
def test_hook_duck_for_theo_niche():
    from autoedit.packager.ducking import HOOK_DUCK_DEFAULT, hook_duck_for
    assert hook_duck_for("space") == 0.35
    assert hook_duck_for("deepsea") == 0.30
    assert hook_duck_for(None) == HOOK_DUCK_DEFAULT
    assert hook_duck_for("travel") == HOOK_DUCK_DEFAULT


def _project_2_chapters(tmp_path) -> tuple[Project, Path]:
    """Project 2 chương (hook 0-7 gồm ô thở 4-7; body 7-11) + lib 1 bài wav."""
    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir()
    _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    _make_wav(pdir / "segments" / "seg_002.wav", 4.0)
    (pdir / "assets").mkdir(); _make_clip(pdir / "assets" / "b000.mp4", 8.0)
    _make_clip(pdir / "assets" / "b001.mp4", 5.0)
    p.transcript = [Word(text="a", start=0.0, end=4.0)]
    b0 = _beat(0, 1, 0.0, 4.0); b0.breathing_after = 3.0
    p.beats = [b0, _beat(1, 2, 7.0, 11.0)]
    p.segments = [
        VoiceSegment(segment_id=1, path="segments/seg_001.wav", source_start=0.0,
                     source_end=4.0, timeline_start=0.0, timeline_end=4.0,
                     beat_ids=[0], breathing_after=3.0),
        VoiceSegment(segment_id=2, path="segments/seg_002.wav", source_start=7.0,
                     source_end=11.0, timeline_start=7.0, timeline_end=11.0, beat_ids=[1]),
    ]
    p.shots = [ShotPick(beat_id=0, status="ok", source="local",
                        asset_path="assets/b000.mp4", asset_key="local:1"),
               ShotPick(beat_id=1, status="ok", source="local",
                        asset_path="assets/b001.mp4", asset_key="local:2")]
    p.outline = {"chapters": [{"chapter_id": 1, "mood": "calm", "energy": "medium"},
                              {"chapter_id": 2, "mood": "calm", "energy": "medium"}]}
    p.niche = "space"
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    lib = tmp_path / "musiclib"
    (lib / "tracks").mkdir(parents=True)
    _make_wav(lib / "tracks" / "t1.wav", 12.0)
    from autoedit.music.library import _save_index
    _save_index(lib, [{"file": "t1.wav", "mood": ["peaceful"], "vocals": "instrumental",
                       "duration_sec": 12.0, "loopable": True, "energy": 0.5,
                       "tempo_class": "medium", "beat_tier": "C", "accents": [],
                       "downbeats": [], "sections": {}}])
    return p, lib


@needs_ffmpeg
def test_assemble_m_vol_hook_to_body_giu(tmp_path, fake_profile):
    """Music-sync bật (có plan) + niche space: nhạc chương hook volume tĩnh 0.35,
    body giữ 0.2; keyframe ducking hook nép 0.35 (không tụt về 0.2), nở ≤0.5."""
    from autoedit.packager.assembler import run_assemble

    p, lib = _project_2_chapters(tmp_path)
    p.music_plan = [MusicPlanEntry(chapter_id=1, file="t1.wav", beat_tier="C"),
                    MusicPlanEntry(chapter_id=2, file="t1.wav", beat_tier="C")]
    p.stages[Stage.MUSIC] = StageRecord(status=StageStatus.DONE)
    p.save()
    run_assemble(p, fake_profile, music_lib=lib)

    saved = Project.load(p.project_dir)
    info = json.loads((Path(saved.draft_path) / "draft_info.json").read_text())
    tracks = {t["name"]: t for t in info["tracks"]}
    hook_seg = tracks["music"]["segments"][0]     # ch1 (hook) trên track music
    body_seg = tracks["music2"]["segments"][0]    # ch2 trên track music2
    assert hook_seg["volume"] == pytest.approx(0.35)
    assert body_seg["volume"] == pytest.approx(0.2)
    # ducking zone: hook có ô thở 4-7s -> keyframe nép 0.35 nở >0.35 (không dùng 0.2)
    kf = [k for k in hook_seg["common_keyframes"] if k["property_type"] == "KFTypeVolume"]
    assert kf, "hook thiếu keyframe ducking"
    vols = [pt["values"][0] for pt in kf[0]["keyframe_list"]]
    assert min(vols) == pytest.approx(0.35) and max(vols) > 0.35
    assert max(vols) <= 0.5 + 1e-6


# ===================== M3 M-ACCENT snap (pure) ================================
def _win(bid, s, e, breathing=0.0, breath_shot=False, j_cut=False):
    from autoedit.packager.coverage import CoverWindow
    return CoverWindow(beat_id=bid, start=s, end=e, breathing_dur=breathing,
                       breath_shot=breath_shot, j_cut_start=j_cut)


def test_snap_hook_thang_ca_j_cut():
    from autoedit.packager import coverage as cov
    ws = [_win(0, 0.0, 3.7, breathing=1.7), _win(1, 3.7, 8.0, j_cut=True),
          _win(2, 8.0, 12.0), _win(3, 12.0, 16.0), _win(4, 16.0, 20.0),
          _win(5, 20.0, 24.0), _win(6, 24.0, 28.0)]
    # hook_end=10: mép 3.7 (J-cut) + 8.0 trong hook; accent 4.03 -> target 3.95
    st = cov.snap_to_accents(ws, [4.03], hook_end=10.0, tol=0.30, lead=0.08,
                             cap_ratio=0.15)
    assert st["snapped"] == 1 and st["hook"] == 1
    assert ws[0].end == pytest.approx(3.95) and ws[1].start == pytest.approx(3.95)
    assert ws[0].breathing_dur == pytest.approx(1.95)   # phần thở giãn theo mép
    assert cov.check_coverage_invariants(ws, 28.0) == []


def test_snap_body_j_cut_mien_va_tran_uu_tien():
    from autoedit.packager import coverage as cov
    # 7 cửa sổ = 6 mép, cap 15% -> quota max(1, floor(0.9)) = 1
    ws = [_win(0, 0.0, 4.0), _win(1, 4.0, 8.0, j_cut=True), _win(2, 8.0, 12.0),
          _win(3, 12.0, 16.0), _win(4, 16.0, 20.0), _win(5, 20.0, 24.0),
          _win(6, 24.0, 28.0)]
    # hook_end=0 (toàn body). accent 4.2 gần mép J-cut 4.0 -> MIỄN; accent 12.3 -> mép 12.0
    st = cov.snap_to_accents(ws, [4.2, 12.3], hook_end=0.0, tol=0.30, lead=0.08,
                             cap_ratio=0.15)
    assert st["snapped"] == 1 and st["body"] == 1
    assert ws[1].start == 4.0                            # J-cut giữ nguyên (body)
    assert ws[3].start == pytest.approx(12.22)           # 12.3 - 0.08
    assert cov.check_coverage_invariants(ws, 28.0) == []


def test_snap_mien_mep_giua_mieng_tho_va_exempt():
    from autoedit.packager import coverage as cov
    ws = [_win(0, 0.0, 4.0), _win(0, 4.0, 7.0, breath_shot=True),
          _win(0, 7.0, 10.0, breath_shot=True), _win(1, 10.0, 14.0)]
    st = cov.snap_to_accents(ws, [7.2, 10.15], hook_end=0.0, tol=0.30, lead=0.08,
                             cap_ratio=1.0, exempt={round(10.0, 2)})
    # mép 7.0 giữa 2 miếng thở MIỄN; mép 10.0 exempt (M-CHANGE) -> không snap gì
    assert st["snapped"] == 0
    assert ws[2].start == 7.0 and ws[3].start == 10.0


def test_snap_khong_pha_min_shot():
    from autoedit.packager import coverage as cov
    ws = [_win(0, 0.0, 1.0), _win(1, 1.0, 1.4), _win(2, 1.4, 10.0), _win(3, 10.0, 14.0)]
    # accent 1.55 -> target 1.47; mép 1.4 dịch tới 1.47 làm cửa sổ 1 còn 0.47s < MIN_SHOT
    # 0.7 (lo = 1.0+0.7 = 1.7 > 1.47) -> KHÔNG snap; mép 1.0 cách 0.47 > tol
    st = cov.snap_to_accents(ws, [1.55], hook_end=100.0, tol=0.30, lead=0.08,
                             cap_ratio=1.0)
    assert st["snapped"] == 0 and ws[2].start == 1.4


# ===================== M3 M-CHANGE + chiếu accent (pure) ======================
def test_music_boundaries_neo_mep_gan_nhat():
    from autoedit.music.plan import music_boundaries
    chs = [{"timeline_start": 0.0}, {"timeline_start": 61.0}, {"timeline_start": 150.0}]
    bounds, anchored = music_boundaries(chs, edges=[59.8, 100.0, 155.0])
    assert bounds[0] == 0.0 and anchored[0] is False
    assert bounds[1] == 59.8 and anchored[1] is True     # |59.8-61| = 1.2 <= 2
    assert bounds[2] == 150.0 and anchored[2] is False   # gần nhất 155 cách 5 > 2


def test_timeline_accents_chieu_dung_toa_do(tmp_path):
    from autoedit.music.plan import timeline_accents
    p = _project_after_cut(tmp_path)   # ch1 ts=0, ch2 ts=10
    p.music_plan = [MusicPlanEntry(chapter_id=1, file="a.mp3", start_offset=2.0, beat_tier="B"),
                    MusicPlanEntry(chapter_id=2, file="b.mp3", start_offset=5.0, beat_tier="B")]
    rows = [{"file": "a.mp3", "beat_tier": "B", "accents": [2.5, 30.0]},
            {"file": "b.mp3", "beat_tier": "B", "accents": [8.0, 9.5]}]
    # ch1: P=2.0+min(3,0)=2.0 -> accent 2.5 tại t=0+(2.5-2.0)=0.5 (30.0 -> 28 > hi=10 loại)
    # ch2: P=5.0+min(3,10)=8.0 -> accent 8.0 tại t=10.0; 9.5 tại 11.5
    assert timeline_accents(p, rows) == [0.5, 10.0, 11.5]
    # boundary ch2 dời về 9.4 (M-CHANGE): accent chiếu theo boundary mới
    assert timeline_accents(p, rows, boundaries=[0.0, 9.4]) == [0.5, 9.4, 10.9]
    # tier C: không target
    rows[1]["beat_tier"] = "C"
    assert timeline_accents(p, rows) == [0.5]


def test_timeline_beats_chieu_toa_do_va_strength(tmp_path):
    """NHIP-M1: beat_times+beat_strength chiếu lên timeline — cùng bất biến P như
    timeline_accents; tier C bỏ; record cũ thiếu strength -> 0.0 (vẫn cắt được)."""
    from autoedit.music.plan import timeline_beats
    p = _project_after_cut(tmp_path)   # ch1 ts=0, ch2 ts=10
    p.music_plan = [MusicPlanEntry(chapter_id=1, file="a.mp3", start_offset=2.0, beat_tier="B"),
                    MusicPlanEntry(chapter_id=2, file="b.mp3", start_offset=5.0, beat_tier="C")]
    rows = [{"file": "a.mp3", "beat_tier": "B",
             "beat_times": [2.5, 3.0, 30.0], "beat_strength": [0.9, 0.4, 1.0]},
            {"file": "b.mp3", "beat_tier": "C", "beat_times": [1.0], "beat_strength": [1.0]}]
    # ch1: P=2.0+min(3,0)=2.0 -> (0.5, 0.9), (1.0, 0.4); 30.0 -> 28 > hi=10 loại; ch2 tier C bỏ
    assert timeline_beats(p, rows) == [(0.5, 0.9), (1.0, 0.4)]
    # boundary ch1 dời (M-CHANGE) -> beat chiếu theo boundary mới, y hệ accent
    assert timeline_beats(p, rows, boundaries=[0.4, 10.0]) == [(0.9, 0.9), (1.4, 0.4)]
    # record cũ thiếu beat_strength / lệch độ dài -> strength 0 cả bài
    rows[0]["beat_strength"] = [0.9]
    assert timeline_beats(p, rows) == [(0.5, 0.0), (1.0, 0.0)]


def test_timeline_accents_m_grid_hook_dung_downbeat(tmp_path):
    """M4 M-GRID: sync_targets='grid' -> HOOK (chương đầu) lấy downbeat thay accent;
    body giữ accent; tier B không downbeat rơi về accent."""
    from autoedit.music.plan import timeline_accents
    p = _project_after_cut(tmp_path)
    p.music_plan = [MusicPlanEntry(chapter_id=1, file="a.mp3", start_offset=2.0, beat_tier="A"),
                    MusicPlanEntry(chapter_id=2, file="b.mp3", start_offset=5.0, beat_tier="B")]
    rows = [{"file": "a.mp3", "beat_tier": "A", "accents": [2.5], "downbeats": [3.0, 5.0]},
            {"file": "b.mp3", "beat_tier": "B", "accents": [8.0], "downbeats": []}]
    p.music_sync_targets = "grid"
    # hook: downbeats 3.0/5.0 - P(2.0) -> 1.0, 3.0; body: accent 8.0 - P(8.0) -> 10.0
    assert timeline_accents(p, rows) == [1.0, 3.0, 10.0]
    p.music_sync_targets = "accent"                     # mặc định: accent như cũ
    assert timeline_accents(p, rows) == [0.5, 10.0]


# ===================== M3 e2e: snap + M-CHANGE trong draft (ffmpeg) ===========
def _project_m3(tmp_path) -> tuple[Project, Path]:
    """2 chương space: ch1 beat0 (0-4, thở 3 -> J-cut mép 6.7); ch2 3 beat 7-13.
    Track tier B accent: 5.45 (-> timeline 9.15) + 2.62 (không dùng)."""
    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir()
    _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    _make_wav(pdir / "segments" / "seg_002.wav", 6.0)
    (pdir / "assets").mkdir()
    for bid in range(4):
        _make_clip(pdir / "assets" / f"b{bid:03d}.mp4", 8.0)
    p.transcript = [Word(text="a", start=0.0, end=4.0)]
    b0 = _beat(0, 1, 0.0, 4.0); b0.breathing_after = 3.0
    p.beats = [b0, _beat(1, 2, 7.0, 9.0), _beat(2, 2, 9.0, 10.5), _beat(3, 2, 10.5, 13.0)]
    p.segments = [
        VoiceSegment(segment_id=1, path="segments/seg_001.wav", source_start=0.0,
                     source_end=4.0, timeline_start=0.0, timeline_end=4.0,
                     beat_ids=[0], breathing_after=3.0),
        VoiceSegment(segment_id=2, path="segments/seg_002.wav", source_start=7.0,
                     source_end=13.0, timeline_start=7.0, timeline_end=13.0,
                     beat_ids=[1, 2, 3]),
    ]
    p.shots = [ShotPick(beat_id=b, status="ok", source="local",
                        asset_path=f"assets/b{b:03d}.mp4", asset_key=f"local:{b}")
               for b in range(4)]
    p.outline = {"chapters": [{"chapter_id": 1, "mood": "calm", "energy": "medium"},
                              {"chapter_id": 2, "mood": "calm", "energy": "medium"}]}
    p.niche = "space"
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.music_plan = [MusicPlanEntry(chapter_id=1, file="t1.wav", beat_tier="C"),
                    MusicPlanEntry(chapter_id=2, file="t1.wav", start_offset=0.0,
                                   beat_tier="B")]
    p.stages[Stage.MUSIC] = StageRecord(status=StageStatus.DONE)
    p.save()

    lib = tmp_path / "musiclib"
    (lib / "tracks").mkdir(parents=True)
    _make_wav(lib / "tracks" / "t1.wav", 20.0)
    from autoedit.music.library import _save_index
    _save_index(lib, [{"file": "t1.wav", "mood": ["peaceful"], "vocals": "instrumental",
                       "duration_sec": 20.0, "loopable": True, "energy": 0.5,
                       "tempo_class": "medium", "beat_tier": "B",
                       "accents": [2.62, 5.45], "downbeats": [], "sections": {}}])
    return p, lib


@needs_ffmpeg
def test_assemble_m3_snap_va_m_change(tmp_path, fake_profile):
    """e2e M3: mép J-cut 6.7 thành điểm đổi nhạc (M-CHANGE, exempt snap); mép 9.0 snap
    về accent 9.15-0.08=9.07 (quota floor(3*0.15)->1); nhạc ch2 vào theo boundary 6.7."""
    from autoedit.packager.assembler import run_assemble

    p, lib = _project_m3(tmp_path)
    run_assemble(p, fake_profile, music_lib=lib)

    saved = Project.load(p.project_dir)
    warns = saved.stages[Stage.ASSEMBLE].warnings
    assert any(w.startswith("M-ACCENT: snap 1/3") for w in warns), warns
    assert any(w.startswith("M-CHANGE: 1/1") for w in warns), warns
    info = json.loads((Path(saved.draft_path) / "draft_info.json").read_text())
    tracks = {t["name"]: t for t in info["tracks"]}
    starts = sorted(s["target_timerange"]["start"] for s in tracks["video_l1"]["segments"])
    # ch2: P = 0 + min(3, 7) = 3.0 -> accent 5.45 tại boundary 6.7 + (5.45-3.0) = 9.15
    assert 9_070_000 in starts                       # mép 9.0 snap -> 9.07 (lead 80ms)
    assert 6_700_000 in starts                       # mép J-cut giữ (exempt M-CHANGE)
    # M-CHANGE space: nhạc ch2 (music2) vào tại boundary - xfade = 6.7 - 3.0 = 3.7
    m2 = tracks["music2"]["segments"][0]
    assert m2["target_timerange"]["start"] == 3_700_000
    # bất biến P: offset dùng = P - xfade = 3.0 - 3.0 = 0.0 -> source bắt đầu 0
    assert m2["source_timerange"]["start"] == 0
    # nhạc ch1 kết thúc đúng boundary 6.7
    m1 = tracks["music"]["segments"][0]
    assert m1["target_timerange"]["start"] + m1["target_timerange"]["duration"] == 6_700_000


@needs_ffmpeg
def test_assemble_khong_plan_volume_phang_cu(tmp_path, fake_profile):
    """Music-sync TẮT (không plan): mọi clip nhạc volume 0.2 + ducking nép 0.2 —
    nguyên trạng đã qua cổng tai V10 (kể cả khi có niche)."""
    from autoedit.packager.assembler import run_assemble

    p, lib = _project_2_chapters(tmp_path)
    run_assemble(p, fake_profile, music_lib=lib)

    saved = Project.load(p.project_dir)
    info = json.loads((Path(saved.draft_path) / "draft_info.json").read_text())
    tracks = {t["name"]: t for t in info["tracks"]}
    for name in ("music", "music2"):
        for seg in tracks[name]["segments"]:
            assert seg["volume"] == pytest.approx(0.2)
    kf = [k for s in tracks["music"]["segments"] for k in s["common_keyframes"]
          if k["property_type"] == "KFTypeVolume"]
    assert kf and min(pt["values"][0] for pt in kf[0]["keyframe_list"]) == pytest.approx(0.2)
