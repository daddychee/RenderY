"""Test M6 — coverage windows (pure) + assemble integration (ffmpeg testsrc)."""

from __future__ import annotations

import json
import math
import shutil
import struct
import subprocess
import wave
from pathlib import Path

import pytest

from autoedit.packager import coverage as cov
from autoedit.project import (
    Beat,
    Project,
    SearchQueries,
    ShotPick,
    Stage,
    StageStatus,
    VoiceSegment,
    Word,
    create_project,
)


def _beat(beat_id, ts, te, breathing=0.0) -> Beat:
    return Beat(
        beat_id=beat_id, chapter=1, text=f"b{beat_id}", start_word=0, end_word=1,
        start=ts, end=te, timeline_start=ts, timeline_end=te,  # đơn giản: offset 0 cho seg đầu
        energy="medium", mood="m", visual_level="literal", visual_concept="c",
        shot_size="medium", search_queries=SearchQueries(specific=["q"]),
        breathing_after=breathing,
    )


def _seg(seg_id, ts, te, beat_ids, breathing=0.0) -> VoiceSegment:
    return VoiceSegment(
        segment_id=seg_id, path=f"segments/seg_{seg_id:03d}.wav",
        source_start=ts, source_end=te, timeline_start=ts, timeline_end=te,
        beat_ids=beat_ids, breathing_after=breathing,
    )


# ===================== coverage (pure) ========================================
def test_coverage_single_segment_no_breathing():
    beats = [_beat(0, 0.0, 2.0), _beat(1, 2.0, 5.0)]
    segs = [_seg(1, 0.0, 5.0, [0, 1])]
    ws = cov.coverage_windows(beats, segs)
    assert [(w.beat_id, w.start, w.end) for w in ws] == [(0, 0.0, 2.0), (1, 2.0, 5.0)]
    assert cov.check_coverage_invariants(ws, 5.0) == []


def test_coverage_breathing_tail_and_lead_silence():
    # segment 2 bắt đầu 7.0 nhưng beat 2 nói từ 7.4 (lead silence 0.4 trong segment)
    beats = [_beat(0, 0.0, 2.0), _beat(1, 2.0, 4.0),
             Beat(**{**_beat(2, 7.4, 9.0).model_dump()})]
    segs = [_seg(1, 0.0, 4.0, [0, 1], breathing=3.0), _seg(2, 7.0, 9.0, [2])]
    ws = cov.coverage_windows(beats, segs)
    # beat 1 (cuối seg 1) phủ luôn hình thở tới 7.0; beat 2 phủ từ mép segment 7.0
    assert ws[1].end == 7.0 and ws[1].is_breathing_tail
    assert ws[1].breathing_dur == 3.0  # multi-shot cần biết ô thở dài bao nhiêu để né
    assert ws[2].start == 7.0 and ws[2].end == 9.0
    assert cov.check_coverage_invariants(ws, 9.0) == []


def test_coverage_invariants_detect_gap():
    ws = [cov.CoverWindow(0, 0.0, 2.0), cov.CoverWindow(1, 2.5, 5.0)]
    assert any("hở/đè" in e for e in cov.check_coverage_invariants(ws, 5.0))


def test_coverage_requires_timeline():
    b = _beat(0, 0.0, 2.0)
    b.timeline_start = None
    with pytest.raises(ValueError, match="chưa có timeline"):
        cov.coverage_windows([b], [_seg(1, 0.0, 2.0, [0])])


# ===================== J-cut + giãn nghỉ máy (hình thở 2.0, pure) =============
def test_coverage_micro_tail_extends_window_no_j_cut():
    beats = [_beat(0, 0.0, 2.0), _beat(1, 2.5, 4.0)]
    segs = [_seg(1, 0.0, 2.0, [0]), _seg(2, 2.5, 4.0, [1])]
    segs[0].micro_pause_after = 0.5
    ws = cov.apply_j_cuts(cov.coverage_windows(beats, segs))
    assert ws[0].end == 2.5 and ws[0].micro_dur == 0.5 and ws[0].tail_dur == 0.5
    assert not ws[0].is_breathing_tail          # micro KHÔNG phải hình thở đạo diễn
    assert ws[1].start == 2.5                   # tầng micro không bao giờ J-cut
    assert cov.check_coverage_invariants(ws, 4.0) == []


def test_j_cut_shifts_video_boundary_into_breath():
    beats = [_beat(0, 0.0, 2.0), _beat(1, 4.0, 6.0)]
    segs = [_seg(1, 0.0, 2.0, [0], breathing=2.0), _seg(2, 4.0, 6.0, [1])]
    ws = cov.apply_j_cuts(cov.coverage_windows(beats, segs))
    # mép chung 4.0 lùi sớm 0.3 — shot kế vào TRƯỚC khi voice nói lại (mẫu SP1-003)
    assert ws[0].end == pytest.approx(3.7) and ws[1].start == pytest.approx(3.7)
    assert ws[0].breathing_dur == pytest.approx(1.7)  # phần thở còn trên shot giữ
    assert cov.check_coverage_invariants(ws, 6.0) == []


def test_j_cut_skips_short_breath():
    beats = [_beat(0, 0.0, 2.0), _beat(1, 3.0, 5.0)]
    segs = [_seg(1, 0.0, 2.0, [0], breathing=1.0), _seg(2, 3.0, 5.0, [1])]
    ws = cov.apply_j_cuts(cov.coverage_windows(beats, segs))
    assert ws[1].start == 3.0  # 1.0s < J_CUT_MIN_BREATH — giữ nguyên


# ===================== shot thở (MO_TA_VAN_HANH_SHOT_THO, pure) ===============
def test_breath_shot_beat_ids_thresholds():
    """Ngưỡng: >=2.5s mọi nơi; 1.5-2.5s chỉ cuối chương; beat cuối video không bao giờ."""
    b0 = _beat(0, 0.0, 2.0, breathing=2.5)                    # giữa chương, đủ sâu
    b1 = _beat(1, 5.0, 7.0, breathing=1.5)                    # cuối chương (b2 chương 2)
    b2 = _beat(2, 9.0, 11.0, breathing=1.5); b2.chapter = 2   # giữa chương, nông
    b3 = _beat(3, 13.0, 15.0, breathing=2.4); b3.chapter = 2  # nông + không cuối chương
    b4 = _beat(4, 17.0, 19.0, breathing=6.0); b4.chapter = 2  # beat cuối video
    assert cov.breath_shot_beat_ids([b0, b1, b2, b3, b4]) == {0, 1}


def test_split_breath_shots_and_j_cut_exemption():
    """Ô có shot thở: chẻ tại hết-voice+0.5; cửa sổ thở phủ TỚI mép voice kế (không
    J-cut tại đây — shot thở đã là 'hình mới vào trước voice'); ô không pick giữ J-cut."""
    beats = [_beat(0, 0.0, 2.0, breathing=3.0), _beat(1, 5.0, 7.0, breathing=2.0),
             _beat(2, 9.0, 11.0)]
    segs = [_seg(1, 0.0, 2.0, [0], breathing=3.0), _seg(2, 5.0, 7.0, [1], breathing=2.0),
            _seg(3, 9.0, 11.0, [2])]
    ws = cov.apply_j_cuts(cov.split_breath_shots(cov.coverage_windows(beats, segs),
                                                 {0: [0.0]}))
    # beat 0: [0, 2.5] giữ hình (breathing còn HOLD=0.5 -> tự thoát J-cut) + [2.5, 5] shot thở
    assert (ws[0].start, ws[0].end, ws[0].breathing_dur) == (0.0, 2.5, 0.5)
    assert not ws[0].breath_shot and ws[1].breath_shot
    assert (ws[1].start, ws[1].end) == (2.5, 5.0)
    assert ws[2].start == 5.0                    # mép voice kế KHÔNG dịch
    # beat 1 không pick -> vẫn J-cut 0.3 như hình thở 2.0
    assert ws[2].end == pytest.approx(8.7) and ws[3].start == pytest.approx(8.7)
    assert cov.check_coverage_invariants(ws, 11.0) == []


def test_split_breath_shots_multi_pieces():
    """2.0: ô nhiều miếng — k cửa sổ liền khít theo dur, miếng CUỐI luôn chạm mép voice
    kế (nuốt sai số/pick hụt giữa chừng)."""
    beats = [_beat(0, 0.0, 2.0, breathing=7.5), _beat(1, 9.5, 11.0)]
    segs = [_seg(1, 0.0, 2.0, [0], breathing=7.5), _seg(2, 9.5, 11.0, [1])]
    ws = cov.split_breath_shots(cov.coverage_windows(beats, segs), {0: [4.06, 2.94]})
    assert [(w.start, w.end) for w in ws[:3]] == [(0.0, 2.5), (2.5, 6.56), (6.56, 9.5)]
    assert not ws[0].breath_shot and ws[1].breath_shot and ws[2].breath_shot
    # pick hụt miếng 2 (specs chỉ còn miếng 1) -> miếng 1 phủ dài tới mép voice kế
    ws2 = cov.split_breath_shots(cov.coverage_windows(beats, segs), {0: [4.06]})
    assert [(w.start, w.end) for w in ws2[:2]] == [(0.0, 2.5), (2.5, 9.5)]
    assert cov.check_coverage_invariants(cov.apply_j_cuts(ws), 11.0) == []


def test_split_breath_shots_skips_unpicked_and_shallow():
    """specs rỗng -> y nguyên; ô quá nông (< HOLD + MIN_SHOT_DUR) không chẻ."""
    beats = [_beat(0, 0.0, 2.0, breathing=1.0), _beat(1, 4.0, 6.0)]
    segs = [_seg(1, 0.0, 2.0, [0], breathing=1.0), _seg(2, 4.0, 6.0, [1])]
    base = cov.coverage_windows(beats, segs)
    assert cov.split_breath_shots(list(base), {}) == base
    assert cov.split_breath_shots(list(base), {0: [0.0]}) == base   # 1.0 < 0.5 + 0.7


# ===================== split_window (shot_count, pure) ========================
def test_split_window_single_returns_whole():
    assert cov.split_window(2.0, 5.0, 1) == [(2.0, 5.0)]
    assert cov.split_window(2.0, 5.0, 0) == [(2.0, 5.0)]  # phòng thủ n<=1


def test_split_window_tiles_evenly_and_adjacent():
    subs = cov.split_window(0.0, 6.0, 3)
    assert len(subs) == 3
    assert subs[0][0] == 0.0 and subs[-1][1] == 6.0
    # mép con sau == mép con trước (liền khít, không hở/đè)
    for a, b in zip(subs, subs[1:]):
        assert a[1] == b[0]
    # tổng độ dài = cả cửa sổ
    assert sum(e - s for s, e in subs) == pytest.approx(6.0)


def test_split_window_microsecond_adjacent_on_fractional():
    SEC = 1_000_000
    subs = cov.split_window(1.64, 4.18, 4)   # mốc lẻ như timeline thật
    # bất biến QUAN TRỌNG: round(mép*SEC) của khoảng sau khớp khoảng trước -> không SegmentOverlap
    for a, b in zip(subs, subs[1:]):
        assert round(a[1] * SEC) == round(b[0] * SEC)
    assert round(subs[0][0] * SEC) == round(1.64 * SEC)
    assert round(subs[-1][1] * SEC) == round(4.18 * SEC)


def test_split_window_tail_keeps_cuts_out_of_breathing():
    """Rà chồng chéo 2026-07-04 #1: multi-shot chia ĐỀU cả ô thở -> nhát cắt rơi
    giữa im lặng (trước fix: (0,7,n=2) cắt tại 3.5s trong khi thoại hết ở 3.0s)."""
    subs = cov.split_window(0.0, 7.0, 2, tail=4.0)   # thoại 0-3s, thở 3-7s
    assert subs == [(0.0, 1.5), (1.5, 7.0)]          # cắt tại 1.5s (trong thoại)
    # tổng quát: mọi mép TRONG phải nằm trong phần thoại, shot cuối phủ kín ô thở
    subs3 = cov.split_window(1.64, 9.18, 3, tail=2.5)
    speech_end = 9.18 - 2.5
    assert all(e <= speech_end + 1e-9 for _, e in subs3[:-1])
    assert subs3[-1][1] == 9.18
    for a, b in zip(subs3, subs3[1:]):               # vẫn liền khít (SegmentOverlap)
        assert a[1] == b[0]
    # tail=0 -> hành vi cũ y hệt
    assert cov.split_window(0.0, 6.0, 3, tail=0.0) == cov.split_window(0.0, 6.0, 3)


# ===================== integration (ffmpeg) ===================================
needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="cần ffmpeg")


def _make_clip(path: Path, seconds: float) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", f"testsrc=duration={seconds}:size=320x240:rate=30",
         "-pix_fmt", "yuv420p", str(path)],
        check=True, capture_output=True, timeout=120,
    )


def _make_wav(path: Path, seconds: float) -> None:
    rate = 48000
    frames = bytearray()
    for i in range(int(seconds * rate)):
        frames += struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i / rate)))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(bytes(frames))


@pytest.fixture
def fake_profile(tmp_path):
    """Machine profile giả với capcut_root tạm (tái dùng cách của test_packager)."""
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


@needs_ffmpeg
def test_run_assemble_pacing_dna_warnings(tmp_path, fake_profile, monkeypatch):
    """Mảnh B DNA d1: project có niche + dna.json -> cảnh báo pacing vào record.warnings.
    DNA dựng cố tình lệch cả 2 tín hiệu: std cao (video thật đều hơn ½) + cut/phút thấp."""
    from autoedit.library.dna import save_dna
    from autoedit.packager.assembler import run_assemble

    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir(); _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    _make_wav(pdir / "segments" / "seg_002.wav", 2.0)
    (pdir / "assets").mkdir(); _make_clip(pdir / "assets" / "b000.mp4", 8.0)
    _make_clip(pdir / "assets" / "b001.mp4", 4.0)

    p.transcript = [Word(text="a", start=0.0, end=4.0)]
    p.beats = [_beat(0, 0.0, 4.0, breathing=3.0), _beat(1, 7.0, 9.0)]
    p.segments = [_seg(1, 0.0, 4.0, [0], breathing=3.0), _seg(2, 7.0, 9.0, [1])]
    p.shots = [
        ShotPick(beat_id=0, status="ok", source="local", asset_path="assets/b000.mp4",
                 asset_key="local:1"),
        ShotPick(beat_id=1, status="ok", source="local", asset_path="assets/b001.mp4",
                 asset_key="local:2"),
    ]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.niche = "n1"
    p.save()

    lib_root = tmp_path / "library"
    monkeypatch.setenv("AUTOEDIT_LIBRARY_ROOT", str(lib_root))
    # shot đặt thật = [7.0, 2.0] (std 2.5, 13.3 cut/phút): DNA std 10 -> "đều tăm tắp";
    # DNA 2 cut/phút (ngưỡng [1;4]) -> "quá nhanh"
    save_dna({"pacing": {"cuts_per_min": 2.0, "shot_len": {"std": 10.0}}},
             lib_root / "n1", [])

    run_assemble(p, fake_profile)
    warns = Project.load(p.project_dir).stages[Stage.ASSEMBLE].warnings
    dna_warns = [w for w in warns if w.startswith("pacing DNA")]
    assert len(dna_warns) == 2
    assert any("đều tăm tắp" in w for w in dna_warns)
    assert any("nhanh" in w for w in dna_warns)
    assert not any("validator lỗi" in w for w in warns)


@needs_ffmpeg
def test_run_assemble_end_to_end(tmp_path, fake_profile):
    from autoedit.packager.assembler import run_assemble

    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)

    # voice segments thật
    (pdir / "segments").mkdir()
    _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    _make_wav(pdir / "segments" / "seg_002.wav", 2.0)
    # assets thật: 1 video + 1 ảnh
    (pdir / "assets").mkdir()
    _make_clip(pdir / "assets" / "b000.mp4", 8.0)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "testsrc=duration=0.1:size=320x240:rate=30",
                    "-frames:v", "1", str(pdir / "assets" / "b001.jpg")],
                   check=True, capture_output=True)

    p.transcript = [Word(text="a", start=0.0, end=4.0)]
    p.beats = [_beat(0, 0.0, 4.0, breathing=3.0), _beat(1, 7.0, 9.0)]
    p.beats[1].timeline_start, p.beats[1].timeline_end = 7.0, 9.0
    p.segments = [_seg(1, 0.0, 4.0, [0], breathing=3.0), _seg(2, 7.0, 9.0, [1])]
    p.shots = [
        ShotPick(beat_id=0, status="ok", source="pexels", asset_path="assets/b000.mp4",
                 asset_key="pexels:1"),
        ShotPick(beat_id=1, status="ok", source="entity", asset_path="assets/b001.jpg",
                 asset_key="entity:x", licensing_flag=True),
    ]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    music = tmp_path / "music.wav"; _make_wav(music, 12.0)
    run_assemble(p, fake_profile, music_path=music)

    saved = Project.load(p.project_dir)
    assert saved.stages[Stage.ASSEMBLE].status == StageStatus.DONE
    draft = Path(saved.draft_path)
    assert (draft / "draft_info.json").is_file()
    info = json.loads((draft / "draft_info.json").read_text())

    # 3 track đúng loại
    tracks = {t["name"]: t for t in info["tracks"]}
    assert set(tracks) == {"video_l1", "voice", "music"}
    # video L1: 2 segment phủ kín 0..9s (beat 0 phủ hình thở 4->7, J-cut lùi mép 0.3s
    # — hình thở 2.0: shot kế vào TRƯỚC khi voice nói lại)
    v_segs = tracks["video_l1"]["segments"]
    assert len(v_segs) == 2
    assert v_segs[0]["target_timerange"]["start"] == 0
    assert v_segs[0]["target_timerange"]["duration"] == 6_700_000  # 4s beat + 3s thở - 0.3 J-cut
    assert v_segs[1]["target_timerange"]["start"] == 6_700_000
    # voice: 2 segment đặt đúng timeline
    a_segs = tracks["voice"]["segments"]
    assert a_segs[1]["target_timerange"]["start"] == 7_000_000
    # video đã transcode chuẩn hóa + CẮT TÂM 16:9 (V1: testsrc 320x240 -> 320x180)
    from autoedit.packager.transcode import ffprobe_dims
    assert (pdir / "media" / "norm" / "b000.mp4").is_file()
    assert ffprobe_dims(pdir / "media" / "norm" / "b000.mp4") == (320, 180)
    # ảnh entity vào track dưới dạng photo material, has_audio khớp thực tế
    photo = [m for m in info["materials"]["videos"] if m.get("type") == "photo"]
    assert photo and photo[0]["has_audio"] is False
    # sổ đăng ký media trong meta là media CỦA TA, không phải của donor
    meta = json.loads((draft / "draft_meta_info.json").read_text())
    entries = [e for b in meta["draft_materials"] for e in b.get("value", [])]
    assert entries, "draft_materials không được rỗng"
    registered = {e["file_Path"] for e in entries}
    # sổ ghi TƯƠNG ĐỐI kiểu native (PORTABLE 13/07) — resolve về draft ra file thật
    assert all(p.startswith("./materials/") for p in registered)
    assert all((draft / p[2:]).is_file() for p in registered)
    metetypes = {e["metetype"] for e in entries}
    assert metetypes <= {"video", "photo", "music"} and "photo" in metetypes
    # local_material_id phải khớp id sổ đăng ký (bài học relink 12/06)
    reg_ids = {e["id"] for e in entries}
    for kind in ("videos", "audios"):
        for m in info["materials"][kind]:
            lmid = m.get("local_material_id", "")
            assert lmid == "" or lmid in reg_ids, f"{m.get('path')}: lmid lửng lơ"
    assert all(m.get("music_id", "") == "" for m in info["materials"]["audios"])
    # F8 ducking: khoảng thở 4->7s (3s >= MIN_BREATH) -> nhạc phải có keyframe volume,
    # nở >0.2 giữa thở, neo 0.2 khi voice (giá trị tuyệt đối — đè volume tĩnh)
    kf_lists = [k for s in tracks["music"]["segments"] for k in s["common_keyframes"]
                if k["property_type"] == "KFTypeVolume"]
    assert kf_lists, "nhạc thiếu keyframe ducking"
    vols = [p["values"][0] for p in kf_lists[0]["keyframe_list"]]
    assert max(vols) > 0.2 + 1e-6 and min(vols) == pytest.approx(0.2)
    # Ken Burns f2 v1 + V1 phủ khung: ẢNH có keyframe scale cover -> cover x 120-130%
    # (ảnh test 320x240 = 4:3 -> cover 4/3; ảnh 16:9 thì cover=1.0 = hành vi f2 gốc).
    # VIDEO không có scale keyframe (chuyển động thật — đã 16:9 nhờ crop ở normalize).
    from autoedit.packager.assembler import _ken_burns_zoom
    from autoedit.packager.transcode import cover_scale
    photo_ids = {m["id"] for m in info["materials"]["videos"] if m.get("type") == "photo"}
    photo_seg = next(s for s in v_segs if s["material_id"] in photo_ids)
    video_seg = next(s for s in v_segs if s["material_id"] not in photo_ids)
    scale_kf = [k for k in photo_seg["common_keyframes"]
                if k["property_type"] == "KFTypeScaleX"]
    assert scale_kf, "ảnh thiếu keyframe Ken Burns"
    pts = scale_kf[0]["keyframe_list"]
    cover = cover_scale(320, 240)  # 4:3 -> 1.3333
    assert len(pts) == 2 and pts[0]["time_offset"] == 0
    assert pts[0]["values"][0] == pytest.approx(cover, rel=1e-3)
    assert pts[1]["time_offset"] == photo_seg["target_timerange"]["duration"] - 1_000
    assert pts[1]["values"][0] == pytest.approx(
        round(cover * _ken_burns_zoom("b001.jpg"), 4))
    assert not [k for k in video_seg["common_keyframes"]
                if k["property_type"] == "KFTypeScaleX"], "video không được zoom nhân tạo"


@needs_ffmpeg
def test_footage_speed_090_video_only(tmp_path, fake_profile):
    """FOOTAGE_SPEED 0.9 (user chốt 2026-07-15): video chạy chậm 10% nhưng target
    GIỮ NGUYÊN mép beat (chỉ truyền speed cho pycapcut — truyền cả source lẫn speed
    sẽ bị tính lại target, lệch 1µs -> SegmentOverlap); ảnh giữ 1.0; clip ngắn vẫn
    slow-mo sâu hơn như cũ; --footage-speed 1.0 = hành vi cũ nguyên vẹn."""
    from autoedit.packager.assembler import run_assemble

    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.wav"; _make_wav(voice, 10.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir(); _make_wav(pdir / "segments" / "seg_001.wav", 10.0)
    (pdir / "assets").mkdir()
    _make_clip(pdir / "assets" / "b000.mp4", 8.0)   # dài: đủ nguồn cho 4s x 0.9
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "testsrc=duration=0.1:size=320x240:rate=30",
                    "-frames:v", "1", str(pdir / "assets" / "b001.jpg")],
                   check=True, capture_output=True)
    _make_clip(pdir / "assets" / "b002.mp4", 2.0)   # ngắn: 1.9s < 4s x 0.9

    p.transcript = [Word(text="a", start=0.0, end=10.0)]
    p.beats = [_beat(0, 0.0, 4.0), _beat(1, 4.0, 6.0), _beat(2, 6.0, 10.0)]
    p.segments = [_seg(1, 0.0, 10.0, [0, 1, 2])]
    p.shots = [
        ShotPick(beat_id=0, status="ok", source="local", asset_path="assets/b000.mp4",
                 asset_key="l:1"),
        ShotPick(beat_id=1, status="ok", source="entity", asset_path="assets/b001.jpg",
                 asset_key="e:1"),
        ShotPick(beat_id=2, status="ok", source="pexels", asset_path="assets/b002.mp4",
                 asset_key="p:1"),
    ]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    def _video_segs(project):
        info = json.loads((Path(project.draft_path) / "draft_info.json").read_text())
        segs = {t["name"]: t for t in info["tracks"]}["video_l1"]["segments"]
        return sorted(segs, key=lambda s: s["target_timerange"]["start"])

    run_assemble(p, fake_profile)
    saved = Project.load(p.project_dir)
    long_v, photo, short_v = _video_segs(saved)
    # video dài: speed 0.9, target GIỮ NGUYÊN mép beat, source = round(0.9 x target)
    assert long_v["speed"] == pytest.approx(0.9)
    assert long_v["target_timerange"] == {"start": 0, "duration": 4_000_000}
    assert long_v["source_timerange"]["duration"] == 3_600_000
    # ảnh: không đổi tốc độ (Ken Burns giữ nguyên hành vi)
    assert photo["speed"] == pytest.approx(1.0)
    # clip ngắn: vẫn kéo giãn phủ kín ô (slow-mo sâu hơn 0.9) + warning như cũ
    assert short_v["speed"] < 0.9
    assert short_v["target_timerange"] == {"start": 6_000_000, "duration": 4_000_000}
    assert any("kéo giãn slow-mo" in w
               for w in saved.stages[Stage.ASSEMBLE].warnings)

    # knob --footage-speed 1.0 = hành vi cũ nguyên vẹn: source = target, speed 1.0
    run_assemble(p, fake_profile, footage_speed=1.0)
    saved = Project.load(p.project_dir)
    long_v = _video_segs(saved)[0]
    assert long_v["speed"] == pytest.approx(1.0)
    assert long_v["source_timerange"]["duration"] == 4_000_000


def test_ken_burns_zoom_deterministic_in_range():
    """f2 v1: mức zoom cuối theo crc32 tên ảnh — deterministic (dựng lại ra đúng số),
    nằm trọn [1.20; 1.30], tên khác nhau cho số khác nhau (đa dạng)."""
    from autoedit.packager.assembler import _ken_burns_zoom

    zooms = {name: _ken_burns_zoom(name) for name in
             ("a.jpg", "b.jpg", "apollo17.jpg", "luna3.jpg", "b001.jpg")}
    assert all(1.20 <= z <= 1.30 for z in zooms.values())
    assert all(_ken_burns_zoom(n) == z for n, z in zooms.items())  # deterministic
    assert len(set(zooms.values())) > 1                            # có đa dạng


# ===================== V1: chuẩn 16:9 (crop tâm video + cover ảnh) ============
def test_crop_16x9_vf_thresholds_and_center():
    """V1: lệch ≤3% giữ nguyên (16:9 chuẩn + viral 852x478); rộng hơn cắt 2 bên,
    hẹp hơn cắt trên–dưới; kích thước ra luôn CHẴN."""
    from autoedit.packager.transcode import crop_16x9_vf

    assert crop_16x9_vf(1920, 1080) is None          # 16:9 chuẩn
    assert crop_16x9_vf(852, 478) is None            # viral 1.782 — trong ngưỡng 3%
    assert crop_16x9_vf(2048, 1080) == "crop=1920:1080"   # 1.9:1 (Pexels điện ảnh)
    assert crop_16x9_vf(2088, 720) == "crop=1280:720"     # 2.9:1 (ca b112 SP012)
    assert crop_16x9_vf(1440, 958) == "crop=1440:810"     # hẹp 1.5:1 -> cắt trên dưới
    assert crop_16x9_vf(320, 240) == "crop=320:180"       # 4:3
    assert crop_16x9_vf(855, 900) == "crop=854:480"       # số lẻ -> ép chẵn


def test_cover_scale_photo():
    """V1 nhánh ảnh: 16:9 -> 1.0 (hành vi f2 gốc); 4:3 và dọc -> hệ số phủ khung."""
    from autoedit.packager.transcode import cover_scale

    assert cover_scale(1920, 1080) == pytest.approx(1.0)
    assert cover_scale(320, 240) == pytest.approx(4 / 3, rel=1e-3)
    assert cover_scale(2956, 3000) == pytest.approx(1.8043, rel=1e-3)  # ảnh dọc SP012
    assert cover_scale(2560, 1339) == pytest.approx(1.0755, rel=1e-3)  # ảnh 1.91:1


@needs_ffmpeg
def test_normalize_video_crop_flag(tmp_path):
    """V1: crop_16x9 mặc định BẬT (footage); TẮT cho asset tự render (chart PiP 1920x1080
    thì 2 đường như nhau, nhưng card DỌC 960x1080 phải giữ nguyên khung dọc)."""
    from autoedit.packager.transcode import ffprobe_dims, normalize_video

    card = tmp_path / "card.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "testsrc=duration=0.5:size=960x1080:rate=30",
         "-pix_fmt", "yuv420p", str(card)],
        check=True, capture_output=True, timeout=120,
    )
    kept = normalize_video(card, tmp_path / "norm_keep" / card.name, crop_16x9=False)
    assert ffprobe_dims(kept) == (960, 1080)   # card dọc giữ nguyên (info-card)
    cropped = normalize_video(card, tmp_path / "norm_crop" / card.name)
    assert ffprobe_dims(cropped) == (960, 540)  # footage dọc bị cắt tâm về 16:9


@needs_ffmpeg
def test_run_assemble_fractional_boundaries_no_overlap(tmp_path, fake_profile):
    """REGRESSION: mốc beat lẻ (1.64, 4.18) từng gây SegmentOverlap 1us vì int()
    cắt cụt 4.18*SEC=4179999.9999 -> 4179999 < mép beat trước 4180000. Fix: round().
    """
    from autoedit.packager.assembler import run_assemble

    script = tmp_path / "s.txt"; script.write_text("a b c")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir(); _make_wav(pdir / "segments" / "seg_001.wav", 4.18)
    (pdir / "assets").mkdir()
    for i in range(3):
        _make_clip(pdir / "assets" / f"b00{i}.mp4", 6.0)

    # 3 beat cùng 1 segment, ranh giới lẻ khiến int() truncation lệch 1us (bug cũ)
    p.transcript = [Word(text="a", start=0.0, end=4.18)]
    p.beats = [_beat(0, 0.0, 1.64), _beat(1, 1.64, 4.18), _beat(2, 4.18, 6.0)]
    p.segments = [_seg(1, 0.0, 6.0, [0, 1, 2])]
    p.shots = [
        ShotPick(beat_id=i, status="ok", source="pexels",
                 asset_path=f"assets/b00{i}.mp4", asset_key=f"pexels:{i}")
        for i in range(3)
    ]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    run_assemble(p, fake_profile)   # KHÔNG được raise SegmentOverlap
    saved = Project.load(p.project_dir)
    assert saved.stages[Stage.ASSEMBLE].status == StageStatus.DONE
    info = json.loads((Path(saved.draft_path) / "draft_info.json").read_text())
    v_segs = {t["name"]: t for t in info["tracks"]}["video_l1"]["segments"]
    v_segs.sort(key=lambda s: s["target_timerange"]["start"])
    assert len(v_segs) == 3
    # kề nhau khít, KHÔNG đè: mỗi seg bắt đầu đúng chỗ seg trước kết thúc
    prev_end = 0
    for s in v_segs:
        tr = s["target_timerange"]
        assert tr["start"] == prev_end, "video segment hở/đè"
        prev_end = tr["start"] + tr["duration"]


@needs_ffmpeg
def test_run_assemble_multi_shot_splits_window(tmp_path, fake_profile):
    """F5 shot_count: 1 beat có extra_shots -> N segment video NỐI TIẾP tiling cửa sổ beat,
    liền khít không hở/đè, tổng = cửa sổ (tổng thời lượng draft không đổi)."""
    from autoedit.packager.assembler import run_assemble
    from autoedit.project import ExtraShot

    script = tmp_path / "s.txt"; script.write_text("a")
    voice = tmp_path / "v.wav"; _make_wav(voice, 6.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir(); _make_wav(pdir / "segments" / "seg_001.wav", 6.0)
    (pdir / "assets").mkdir()
    for i in range(3):
        _make_clip(pdir / "assets" / f"b000_{i}.mp4", 6.0)

    p.transcript = [Word(text="a", start=0.0, end=6.0)]
    p.beats = [_beat(0, 0.0, 6.0)]           # 1 beat 6s
    p.segments = [_seg(1, 0.0, 6.0, [0])]
    p.shots = [ShotPick(
        beat_id=0, status="ok", source="pexels",
        asset_path="assets/b000_0.mp4", asset_key="pexels:0",
        extra_shots=[
            ExtraShot(asset_path="assets/b000_1.mp4", asset_key="pexels:1", source="pexels"),
            ExtraShot(asset_path="assets/b000_2.mp4", asset_key="pexels:2", source="pexels"),
        ],
    )]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    run_assemble(p, fake_profile)
    saved = Project.load(p.project_dir)
    info = json.loads((Path(saved.draft_path) / "draft_info.json").read_text())
    v_segs = {t["name"]: t for t in info["tracks"]}["video_l1"]["segments"]
    v_segs.sort(key=lambda s: s["target_timerange"]["start"])
    assert len(v_segs) == 3                   # 3 shot cho 1 beat
    prev_end = 0
    for s in v_segs:
        tr = s["target_timerange"]
        assert tr["start"] == prev_end, "shot con hở/đè"
        prev_end = tr["start"] + tr["duration"]
    assert prev_end == 6_000_000              # tiling đúng cả cửa sổ 6s
    # 3 material khác nhau (3 clip riêng)
    used = {s["material_id"] for s in v_segs}
    assert len(used) == 3


@needs_ffmpeg
def test_run_assemble_places_breath_shot(tmp_path, fake_profile):
    """Shot thở tích hợp: ô 3s có pick -> 3 segment video [0,4.5][4.5,7][7,9] liền khít,
    KHÔNG J-cut tại mép voice kế (7.0), shot thở là material riêng."""
    from autoedit.packager.assembler import run_assemble
    from autoedit.project import BreathShot

    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir()
    _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    _make_wav(pdir / "segments" / "seg_002.wav", 2.0)
    (pdir / "assets").mkdir()
    _make_clip(pdir / "assets" / "b000.mp4", 6.0)
    _make_clip(pdir / "assets" / "b000_breath.mp4", 4.0)
    _make_clip(pdir / "assets" / "b001.mp4", 4.0)

    p.transcript = [Word(text="a", start=0.0, end=4.0)]
    p.beats = [_beat(0, 0.0, 4.0, breathing=3.0), _beat(1, 7.0, 9.0)]
    p.segments = [_seg(1, 0.0, 4.0, [0], breathing=3.0), _seg(2, 7.0, 9.0, [1])]
    p.shots = [
        ShotPick(beat_id=0, status="ok", source="local",
                 asset_path="assets/b000.mp4", asset_key="local:a"),
        ShotPick(beat_id=1, status="ok", source="local",
                 asset_path="assets/b001.mp4", asset_key="local:b"),
    ]
    p.breath_shots = [BreathShot(beat_id=0, asset_path="assets/b000_breath.mp4",
                                 asset_key="local:c")]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    run_assemble(p, fake_profile)
    saved = Project.load(p.project_dir)
    info = json.loads((Path(saved.draft_path) / "draft_info.json").read_text())
    v_segs = {t["name"]: t for t in info["tracks"]}["video_l1"]["segments"]
    v_segs.sort(key=lambda s: s["target_timerange"]["start"])
    assert len(v_segs) == 3
    bounds = [(s["target_timerange"]["start"],
               s["target_timerange"]["start"] + s["target_timerange"]["duration"])
              for s in v_segs]
    # giữ hình 0.5s sau hết voice (4.0) -> cắt 4.5; shot thở phủ tới ĐÚNG mép voice 7.0
    assert bounds == [(0, 4_500_000), (4_500_000, 7_000_000), (7_000_000, 9_000_000)]
    assert len({s["material_id"] for s in v_segs}) == 3   # shot thở là clip riêng


@needs_ffmpeg
def test_run_assemble_places_multi_breath_pieces(tmp_path, fake_profile):
    """2.0: ô 7.5s với 2 miếng (4.06 + 2.94) -> 4 segment video liền khít, miếng cuối
    chạm ĐÚNG mép voice kế, 2 miếng là 2 material khác nhau, theo đúng thứ tự list."""
    from autoedit.packager.assembler import run_assemble
    from autoedit.project import BreathShot

    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir()
    _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    _make_wav(pdir / "segments" / "seg_002.wav", 2.0)
    (pdir / "assets").mkdir()
    _make_clip(pdir / "assets" / "b000.mp4", 6.0)
    _make_clip(pdir / "assets" / "b000_breath1.mp4", 5.0)
    _make_clip(pdir / "assets" / "b000_breath2.mp4", 4.0)
    _make_clip(pdir / "assets" / "b001.mp4", 4.0)

    p.transcript = [Word(text="a", start=0.0, end=4.0)]
    p.beats = [_beat(0, 0.0, 4.0, breathing=7.5), _beat(1, 11.5, 13.5)]
    p.segments = [_seg(1, 0.0, 4.0, [0], breathing=7.5), _seg(2, 11.5, 13.5, [1])]
    p.shots = [
        ShotPick(beat_id=0, status="ok", source="local",
                 asset_path="assets/b000.mp4", asset_key="local:a"),
        ShotPick(beat_id=1, status="ok", source="local",
                 asset_path="assets/b001.mp4", asset_key="local:b"),
    ]
    p.breath_shots = [
        BreathShot(beat_id=0, asset_path="assets/b000_breath1.mp4",
                   asset_key="local:c", dur=4.06),
        BreathShot(beat_id=0, asset_path="assets/b000_breath2.mp4",
                   asset_key="local:d", dur=2.94),
    ]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    run_assemble(p, fake_profile)
    saved = Project.load(p.project_dir)
    info = json.loads((Path(saved.draft_path) / "draft_info.json").read_text())
    v_segs = {t["name"]: t for t in info["tracks"]}["video_l1"]["segments"]
    v_segs.sort(key=lambda s: s["target_timerange"]["start"])
    bounds = [(s["target_timerange"]["start"],
               s["target_timerange"]["start"] + s["target_timerange"]["duration"])
              for s in v_segs]
    assert bounds == [(0, 4_500_000), (4_500_000, 8_560_000),
                      (8_560_000, 11_500_000), (11_500_000, 13_500_000)]
    assert len({s["material_id"] for s in v_segs}) == 4   # mỗi miếng 1 clip riêng


def test_next_version_takes_max_plus_one_not_gap(tmp_path):
    """Bẫy tên draft (cắn 2 lần): xóa _V4 xong bản mới KHÔNG được điền lỗ thành _V4
    'trẻ hơn V6' — version kế = max hiện có + 1."""
    from autoedit.packager.assembler import _next_version

    base = "SCRIPT_X"
    (tmp_path / base).mkdir()
    for v in (2, 3, 5, 6):                    # V4 đã bị xóa (lỗ trống)
        (tmp_path / f"{base}_V{v}").mkdir()
    assert _next_version(tmp_path, base) == 7
    assert _next_version(tmp_path, "SCRIPT_KHAC") == 2   # chưa có version nào


@needs_ffmpeg
def test_run_assemble_never_overwrites_creates_v2(tmp_path, fake_profile):
    """RA_SOAT 7.1: chạy lại sinh draft MỚI _V2, không đè (CapCut cache draft_id)."""
    from autoedit.packager.assembler import run_assemble

    script = tmp_path / "s.txt"; script.write_text("a")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir(); _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    (pdir / "assets").mkdir(); _make_clip(pdir / "assets" / "b000.mp4", 8.0)
    p.transcript = [Word(text="a", start=0.0, end=4.0)]
    p.beats = [_beat(0, 0.0, 4.0)]
    p.segments = [_seg(1, 0.0, 4.0, [0])]
    p.shots = [ShotPick(beat_id=0, status="ok", source="pexels",
                        asset_path="assets/b000.mp4", asset_key="pexels:1")]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    run_assemble(p, fake_profile)
    first = Project.load(p.project_dir).draft_path
    p2 = Project.load(p.project_dir)
    run_assemble(p2, fake_profile)
    second = Project.load(p.project_dir).draft_path
    assert first != second and second.endswith("_V2")
    assert Path(first).is_dir() and Path(second).is_dir()  # bản cũ còn nguyên


@needs_ffmpeg
def test_run_assemble_places_overlays(tmp_path, fake_profile):
    """P1.3: overlay text + SFX đặt đúng timeline (anchor_word + offset beat)."""
    from autoedit.overlay.style import resolve_overlay
    from autoedit.packager.assembler import run_assemble

    script = tmp_path / "s.txt"; script.write_text("a b c")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir()
    _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    _make_wav(pdir / "segments" / "seg_002.wav", 2.0)
    (pdir / "assets").mkdir(); _make_clip(pdir / "assets" / "b000.mp4", 8.0)
    sfx = tmp_path / "cash.wav"; _make_wav(sfx, 0.5)

    # 2 segment có hình thở 3s giữa -> beat 1 có offset +3 trên timeline.
    # overlay ở beat 1 (anchor word source 5.0) -> timeline 5.0 + offset 3.0 = 8.0s
    p.transcript = [Word(text="a", start=0.0, end=2.0), Word(text="b", start=2.0, end=4.0),
                    Word(text="c", start=5.0, end=7.0)]
    b0 = _beat(0, 0.0, 4.0, breathing=3.0)   # source/timeline 0-4, hình thở 3s
    b1 = _beat(1, 5.0, 7.0); b1.timeline_start, b1.timeline_end = 7.0, 9.0  # offset +2
    b1.overlays = [resolve_overlay("$2", "price", 2)]  # anchor word 2, source 5.0s
    p.beats = [b0, b1]
    p.segments = [_seg(1, 0.0, 4.0, [0], breathing=3.0), _seg(2, 5.0, 7.0, [1])]
    p.segments[1].timeline_start, p.segments[1].timeline_end = 7.0, 9.0
    p.shots = [ShotPick(beat_id=0, status="ok", source="pexels", asset_path="assets/b000.mp4", asset_key="x"),
               ShotPick(beat_id=1, status="ok", source="pexels", asset_path="assets/b000.mp4", asset_key="y")]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    run_assemble(p, fake_profile, sfx_fallback=sfx)
    saved = Project.load(p.project_dir)
    info = json.loads((Path(saved.draft_path) / "draft_info.json").read_text())
    tracks = {t["name"]: t for t in info["tracks"]}
    assert "text" in tracks and "sfx" in tracks
    txt = tracks["text"]["segments"]
    assert len(txt) == 1
    # overlay timeline = word source 5.0 + offset (7.0-5.0=2.0) = 7.0s
    assert txt[0]["target_timerange"]["start"] == 7_000_000
    assert txt[0]["common_keyframes"]  # có animation keyframe
    assert tracks["sfx"]["segments"][0]["target_timerange"]["start"] == 7_000_000


@needs_ffmpeg
def test_run_assemble_places_pip_chart(tmp_path, fake_profile):
    """P1.5b: chart layout=half -> track layer2 PiP scale 0.5 + dời phải, footage L1 vẫn chạy."""
    from autoedit.packager.assembler import run_assemble

    script = tmp_path / "s.txt"; script.write_text("a")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir(); _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    (pdir / "assets").mkdir()
    _make_clip(pdir / "assets" / "b000.mp4", 8.0)
    _make_clip(pdir / "assets" / "b000_chartpip.mp4", 6.0)  # chart render sẵn

    p.transcript = [Word(text="a", start=0.0, end=4.0)]
    b0 = _beat(0, 0.0, 4.0)
    b0.graphic_asset = "assets/b000_chartpip.mp4"  # chart PiP
    p.beats = [b0]
    p.segments = [_seg(1, 0.0, 4.0, [0])]
    p.shots = [ShotPick(beat_id=0, status="ok", source="pexels",
                        asset_path="assets/b000.mp4", asset_key="x")]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    run_assemble(p, fake_profile)
    saved = Project.load(p.project_dir)
    info = json.loads((Path(saved.draft_path) / "draft_info.json").read_text())
    tracks = {t["name"]: t for t in info["tracks"]}
    assert "layer2" in tracks and "video_l1" in tracks  # cả 2 track video
    pip = tracks["layer2"]["segments"]
    assert len(pip) == 1
    assert pip[0]["target_timerange"]["start"] == 0
    assert pip[0]["target_timerange"]["duration"] == 4_000_000  # phủ ô beat
    clip = pip[0]["clip"]
    assert abs(clip["scale"]["x"] - 0.5) < 1e-6 and abs(clip["scale"]["y"] - 0.5) < 1e-6
    assert clip["transform"]["x"] > 0  # dời sang phải


@needs_ffmpeg
def test_run_assemble_text_sequence(tmp_path, fake_profile):
    """P2A Req3: text_sequence -> mỗi cụm 1 text segment, xếp chồng y khác nhau, hold tới hết beat."""
    from autoedit.packager.assembler import run_assemble
    from autoedit.project import TextPhrase, TextSequence

    script = tmp_path / "s.txt"; script.write_text("a b c")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir(); _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    (pdir / "assets").mkdir(); _make_clip(pdir / "assets" / "b000.mp4", 8.0)

    p.transcript = [Word(text="Việt", start=0.0, end=1.0), Word(text="Nam", start=1.0, end=2.0),
                    Word(text="rẻ", start=2.0, end=4.0)]
    b0 = _beat(0, 0.0, 4.0)
    b0.text_sequence = TextSequence(
        phrases=[TextPhrase(text="Việt Nam", anchor_word=0), TextPhrase(text="rẻ nhất", anchor_word=2)],
        background="plate",
    )
    p.beats = [b0]
    p.segments = [_seg(1, 0.0, 4.0, [0])]
    p.shots = [ShotPick(beat_id=0, status="ok", source="pexels",
                        asset_path="assets/b000.mp4", asset_key="x")]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    run_assemble(p, fake_profile)
    info = json.loads((Path(Project.load(p.project_dir).draft_path) / "draft_info.json").read_text())
    tracks = {t["name"]: t for t in info["tracks"]}
    # mỗi cụm trên 1 track kinetic riêng (chồng thời gian)
    assert "kinetic0" in tracks and "kinetic1" in tracks
    s0 = tracks["kinetic0"]["segments"][0]
    s1 = tracks["kinetic1"]["segments"][0]
    assert s0["target_timerange"]["start"] == 0              # cụm 1 tại đầu beat
    assert s1["target_timerange"]["start"] == 2_000_000      # cụm 2 tại từ "rẻ" (2s)
    # cả 2 giữ tới hết beat (4s)
    for s in (s0, s1):
        assert s["target_timerange"]["start"] + s["target_timerange"]["duration"] == 4_000_000
    # xếp chồng: transform_y khác nhau
    assert s0["clip"]["transform"]["y"] != s1["clip"]["transform"]["y"]


@needs_ffmpeg
def test_run_assemble_info_card_approved_gate(tmp_path, fake_profile):
    """P2B Req6: info-card CHỈ đặt lên layer2 khi approved; chưa duyệt -> bỏ qua."""
    from autoedit.packager.assembler import run_assemble
    from autoedit.project import InfoCard

    def build(approved):
        script = tmp_path / f"s{approved}.txt"; script.write_text("a")
        voice = tmp_path / f"v{approved}.wav"; _make_wav(voice, 5.0)
        p = create_project(script, voice, out_dir=tmp_path / f"proj{approved}")
        pdir = Path(p.project_dir)
        (pdir / "segments").mkdir(); _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
        (pdir / "assets").mkdir()
        _make_clip(pdir / "assets" / "b000.mp4", 8.0)
        _make_clip(pdir / "assets" / "b000_card.mp4", 6.0)
        b0 = _beat(0, 0.0, 4.0)
        b0.info_card = InfoCard(title="t", bullets=["a", "b", "c"], approved=approved)
        b0.info_card_asset = "assets/b000_card.mp4"
        p.beats = [b0]
        p.segments = [_seg(1, 0.0, 4.0, [0])]
        p.shots = [ShotPick(beat_id=0, status="ok", source="pexels",
                            asset_path="assets/b000.mp4", asset_key="x")]
        for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
            p.stages[st].status = StageStatus.DONE
        p.save()
        run_assemble(p, fake_profile)
        info = json.loads((Path(Project.load(p.project_dir).draft_path) / "draft_info.json").read_text())
        return {t["name"]: t for t in info["tracks"]}

    # chưa duyệt -> không có layer2
    assert "layer2" not in build(False)
    # đã duyệt -> card trên layer2, scale 0.5 full-height portrait, đẩy phải
    tracks = build(True)
    assert "layer2" in tracks
    seg = tracks["layer2"]["segments"][0]
    assert abs(seg["clip"]["scale"]["x"] - 1.0) < 1e-6     # full nửa phải (portrait fit cao)
    assert seg["clip"]["transform"]["x"] > 0               # đẩy sang phải
    # footage L1 GIỮ NGUYÊN (không dịch) -> hết card không lỗi
    l1 = tracks["video_l1"]["segments"][0]
    assert l1["clip"]["transform"]["x"] == 0


@needs_ffmpeg
def test_card_beat_suppresses_overlays(tmp_path, fake_profile):
    """P2B: beat có card/chart -> BỎ overlay text + SFX overlay (ưu tiên card/chart)."""
    from autoedit.overlay.style import resolve_overlay
    from autoedit.packager.assembler import run_assemble
    from autoedit.project import InfoCard

    script = tmp_path / "s.txt"; script.write_text("a")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir(); _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    (pdir / "assets").mkdir()
    _make_clip(pdir / "assets" / "b000.mp4", 8.0)
    _make_clip(pdir / "assets" / "b000_card.mp4", 6.0)
    sfx = tmp_path / "cash.wav"; _make_wav(sfx, 0.5)

    p.transcript = [Word(text="a", start=0.0, end=4.0)]
    b0 = _beat(0, 0.0, 4.0)
    b0.overlays = [resolve_overlay("$2", "price", 0)]      # có overlay
    b0.info_card = InfoCard(title="t", bullets=["a", "b", "c"], approved=True)  # nhưng có card
    b0.info_card_asset = "assets/b000_card.mp4"
    p.beats = [b0]
    p.segments = [_seg(1, 0.0, 4.0, [0])]
    p.shots = [ShotPick(beat_id=0, status="ok", source="pexels",
                        asset_path="assets/b000.mp4", asset_key="x")]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    run_assemble(p, fake_profile, sfx_fallback=sfx)
    info = json.loads((Path(Project.load(p.project_dir).draft_path) / "draft_info.json").read_text())
    tracks = {t["name"]: t for t in info["tracks"]}
    # overlay bị bỏ -> không có track text (chỉ card trên layer2)
    assert "text" not in tracks
    assert "layer2" in tracks


@needs_ffmpeg
def test_run_assemble_adds_chart_sfx(tmp_path, fake_profile):
    """P2A Req2: beat có chart -> track sfx có tiếng grow + ding tại timeline chart."""
    from autoedit.packager.assembler import run_assemble
    from autoedit.project import ChartDatum, GraphicSpec

    script = tmp_path / "s.txt"; script.write_text("a")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir(); _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    (pdir / "assets").mkdir()
    _make_clip(pdir / "assets" / "b000.mp4", 8.0)
    _make_clip(pdir / "assets" / "b000_chartpip.mp4", 6.0)
    sfx = tmp_path / "whoosh.wav"; _make_wav(sfx, 1.5)

    b0 = _beat(0, 0.0, 4.0)
    b0.graphic_asset = "assets/b000_chartpip.mp4"       # half chart PiP
    b0.graphic_spec = GraphicSpec(chart_type="bar", title="t",
                                  data=[ChartDatum(label="x", value=1),
                                        ChartDatum(label="y", value=2)])
    p.beats = [b0]
    p.segments = [_seg(1, 0.0, 4.0, [0])]
    p.shots = [ShotPick(beat_id=0, status="ok", source="pexels",
                        asset_path="assets/b000.mp4", asset_key="x")]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    run_assemble(p, fake_profile, sfx_fallback=sfx)
    info = json.loads((Path(Project.load(p.project_dir).draft_path) / "draft_info.json").read_text())
    tracks = {t["name"]: t for t in info["tracks"]}
    assert "sfx" in tracks and "layer2" in tracks
    sfx_segs = tracks["sfx"]["segments"]
    assert len(sfx_segs) == 2                            # grow + ding
    starts = sorted(s["target_timerange"]["start"] for s in sfx_segs)
    assert starts[0] == 0                                # grow tại đầu chart
    assert starts[1] == int(1.2 * 1_000_000)            # ding cuối grow (GROW_SEC)


@needs_ffmpeg
def test_run_assemble_skips_broken_asset(tmp_path, fake_profile):
    """1 asset hỏng (svg/không chuyển mã được) -> BỎ QUA + cảnh báo, KHÔNG sập cả draft."""
    from autoedit.packager.assembler import run_assemble

    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir(); _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    (pdir / "assets").mkdir()
    _make_clip(pdir / "assets" / "b001.mp4", 8.0)
    (pdir / "assets" / "b000.svg").write_text("<svg>not a real image</svg>")  # hỏng

    p.transcript = [Word(text="a", start=0.0, end=2.0), Word(text="b", start=2.0, end=4.0)]
    p.beats = [_beat(0, 0.0, 2.0), _beat(1, 2.0, 4.0)]
    p.segments = [_seg(1, 0.0, 4.0, [0, 1])]
    p.shots = [
        ShotPick(beat_id=0, status="ok", source="entity", asset_path="assets/b000.svg"),
        ShotPick(beat_id=1, status="ok", source="pexels", asset_path="assets/b001.mp4"),
    ]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    run_assemble(p, fake_profile)   # KHÔNG được raise
    saved = Project.load(p.project_dir)
    assert saved.stages[Stage.ASSEMBLE].status == StageStatus.DONE
    info = json.loads((Path(saved.draft_path) / "draft_info.json").read_text())
    v_segs = {t["name"]: t for t in info["tracks"]}["video_l1"]["segments"]
    # svg beat 0 bị bỏ NHƯNG ô của nó được lấp SLUG (main track CapCut không cho hở)
    assert len(v_segs) == 2
    mats = {m["id"]: m for m in info["materials"]["videos"]}
    slug_segs = [s for s in v_segs
                 if mats[s["material_id"]]["path"].endswith("_editor_slug.jpg")]
    assert len(slug_segs) == 1 and slug_segs[0]["target_timerange"]["start"] == 0
    assert any("BỎ QUA" in w or "hỏng" in w for w in saved.stages[Stage.ASSEMBLE].warnings)


@needs_ffmpeg
def test_run_assemble_fills_needs_human_hole_with_slug(tmp_path, fake_profile):
    """Regression bug DS3-084 footage lệch -187s: beat needs_human để LỖ HỞ trên
    video_l1 — main track CapCut là track nam châm, mở draft là dồn mọi segment về
    trước, footage sau lỗ trượt khỏi voice. Fix: mọi lỗ lấp bằng slug -> track
    LIỀN KHÍT phủ tới hết timeline, mốc đặt sống sót khi CapCut mở."""
    from autoedit.packager.assembler import run_assemble

    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.wav"; _make_wav(voice, 5.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    pdir = Path(p.project_dir)
    (pdir / "segments").mkdir(); _make_wav(pdir / "segments" / "seg_001.wav", 4.0)
    _make_wav(pdir / "segments" / "seg_002.wav", 2.0)
    (pdir / "assets").mkdir(); _make_clip(pdir / "assets" / "b000.mp4", 8.0)
    _make_clip(pdir / "assets" / "b002.mp4", 4.0)

    p.transcript = [Word(text="a", start=0.0, end=4.0)]
    # beat 1 needs_human nằm GIỮA (7-9s), beat 2 có asset theo sau (9-11s):
    # trước fix lỗ 7-9 hở -> CapCut dồn beat 2 về 7s (mất sync)
    p.beats = [_beat(0, 0.0, 4.0, breathing=3.0), _beat(1, 7.0, 9.0), _beat(2, 9.0, 11.0)]
    p.segments = [_seg(1, 0.0, 4.0, [0], breathing=3.0), _seg(2, 7.0, 11.0, [1, 2])]
    p.shots = [
        ShotPick(beat_id=0, status="ok", source="local", asset_path="assets/b000.mp4",
                 asset_key="local:1"),
        ShotPick(beat_id=1, status="needs_human", source="none", note="phễu trắng"),
        ShotPick(beat_id=2, status="ok", source="local", asset_path="assets/b002.mp4",
                 asset_key="local:2"),
    ]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.save()

    run_assemble(p, fake_profile)
    saved = Project.load(p.project_dir)
    info = json.loads((Path(saved.draft_path) / "draft_info.json").read_text())
    v_segs = sorted({t["name"]: t for t in info["tracks"]}["video_l1"]["segments"],
                    key=lambda s: s["target_timerange"]["start"])
    # LIỀN KHÍT: không lỗ hở nào giữa các segment, phủ 0 -> 11s
    prev_end = 0
    for s in v_segs:
        assert s["target_timerange"]["start"] == prev_end, "video_l1 còn lỗ hở!"
        prev_end = s["target_timerange"]["start"] + s["target_timerange"]["duration"]
    assert prev_end == 11_000_000
    # đúng 1 slug tại ô beat 1 (7-9s, J-cut lùi mép vào 0.3s -> 6.7-9.0)
    mats = {m["id"]: m for m in info["materials"]["videos"]}
    slug_segs = [s for s in v_segs
                 if mats[s["material_id"]]["path"].endswith("_editor_slug.jpg")]
    assert len(slug_segs) == 1
    assert slug_segs[0]["target_timerange"]["start"] == 6_700_000
    assert slug_segs[0]["target_timerange"]["duration"] == 2_300_000
    # slug là ảnh: has_audio=False, KHÔNG keyframe Ken Burns
    assert mats[slug_segs[0]["material_id"]]["has_audio"] is False
    assert not slug_segs[0].get("common_keyframes")
    # cảnh báo nói rõ đã lấp + beat nào
    warns = saved.stages[Stage.ASSEMBLE].warnings
    assert any(w.startswith("slug: lấp 1 ô trống") and "beat 1" in w for w in warns)
    # pacing DNA không đếm slug: 2 shot thật (b000 + b002)
    assert not any("slug" in w and "pacing" in w for w in warns)


@needs_ffmpeg
def test_run_assemble_requires_source(tmp_path, fake_profile):
    from autoedit.packager.assembler import run_assemble

    script = tmp_path / "s.txt"; script.write_text("a")
    voice = tmp_path / "v.wav"; _make_wav(voice, 1.0)
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    with pytest.raises(RuntimeError, match="source"):
        run_assemble(p, fake_profile)


# ===================== VD4: ghi công kênh nguồn (--credit) =====================
def test_build_text_overlay_x_override_defaults_center():
    """x_override đặt text vào góc (transform_x); không truyền -> giữa màn y hành vi cũ."""
    from autoedit.overlay.text import build_text_overlay

    seg = build_text_overlay("Kênh A", 0, 1_000_000, anim="none",
                             y_override=-0.80, x_override=0.72)
    assert seg.clip_settings.transform_x == 0.72
    assert seg.clip_settings.transform_y == -0.80
    seg2 = build_text_overlay("t", 0, 1_000_000)
    assert seg2.clip_settings.transform_x == 0.0


def test_credit_overlays_channel_segments_only_corner_deterministic():
    """--credit: CHỈ miếng có kênh gắn text (track 'credit' riêng, KHÔNG viền — user
    chốt cổng mắt v1), span đúng miếng, góc deterministic crc32; đủ cả 3 loại pick
    (shot chính + extra + shot thở); tổng kết vào warnings cho report."""
    from pycapcut import ScriptFile

    from autoedit.packager.assembler import (
        CREDIT_ALPHA, CREDIT_PREFIX, CREDIT_Y, SEC, _add_credit_overlays, _credit_pos)
    from autoedit.project import BreathShot, ExtraShot, StageRecord

    class P:
        shots = [ShotPick(beat_id=0, asset_path="assets/a.mp4",
                          source_channel="Kurzgesagt",
                          extra_shots=[ExtraShot(asset_path="assets/b.mp4",
                                                 source_channel="Astrum")]),
                 ShotPick(beat_id=1, asset_path="assets/c.mp4")]     # không kênh
        breath_shots = [BreathShot(beat_id=1, asset_path="assets/d.mp4",
                                   source_channel="Kurzgesagt")]

    script = ScriptFile(1920, 1080, fps=30)
    record = StageRecord.running()
    log = [(0.0, 2.0, "assets/a.mp4"), (2.0, 3.5, "assets/b.mp4"),
           (3.5, 5.0, "assets/c.mp4"), (5.0, 8.0, "assets/d.mp4")]
    _add_credit_overlays(script, P(), record, log)

    segs = script.tracks["credit"].segments
    assert len(segs) == 3                        # c.mp4 không kênh -> bỏ qua
    spans = [(s.target_timerange.start, s.target_timerange.duration) for s in segs]
    assert spans == [(0, 2 * SEC), (2 * SEC, 1_500_000), (5 * SEC, 3 * SEC)]
    assert _credit_pos("assets/a.mp4", 0.0, "Astrum") == _credit_pos(
        "assets/a.mp4", 0.0, "Astrum")           # deterministic — dựng lại ra đúng chỗ cũ
    for s in segs:
        assert abs(s.clip_settings.transform_y) == CREDIT_Y
        assert s.clip_settings.transform_x != 0.0
        assert s.border is None                  # user chốt: không viền/hiệu ứng
        assert s.text.startswith(CREDIT_PREFIX)  # "Credit: Tên Kênh" (user chốt)
        assert s.style.alpha == CREDIT_ALPHA     # chữ mờ 50%
    assert any("ghi công (--credit): 3/4" in w for w in record.warnings)


def test_credit_pos_long_name_stays_on_screen():
    """Regression cổng mắt v1 2026-07-17 (tên kênh mất chữ): neo TÂM x cố định ±0.72
    làm tên dài tràn nửa chữ ra ngoài màn. v2: mép NGOÀI chữ = 1 - CREDIT_MARGIN —
    tên càng dài tâm càng lùi vào trong, mọi tên đều nằm trọn màn."""
    from autoedit.packager.assembler import (
        CREDIT_MARGIN, CREDIT_SIZE, _CREDIT_PX_PER_SIZE_CHAR, _credit_pos)

    ngan = "Astrum"
    dai = "Kurzgesagt - In a Nutshell"

    def haft(text):
        return CREDIT_SIZE * len(text) * _CREDIT_PX_PER_SIZE_CHAR / 2 / 960

    for text in (ngan, dai):
        # tìm 1 seed rơi góc PHẢI để kiểm mép; mọi góc đối xứng qua dấu
        for i in range(16):
            x, y = _credit_pos(f"assets/x{i}.mp4", 0.0, text)
            if x > 0:
                break
        assert x > 0
        # mép ngoài chữ (tâm + nửa bề rộng ước lượng) không vượt 1 - margin
        assert x + haft(text) <= 1.0 - CREDIT_MARGIN + 1e-9
    # tên dài phải lùi TÂM vào trong sâu hơn tên ngắn
    xs = {}
    for text in (ngan, dai):
        for i in range(16):
            x, _ = _credit_pos(f"assets/x{i}.mp4", 0.0, text)
            if x > 0:
                xs[text] = x
                break
    assert xs[dai] < xs[ngan]


def test_credit_overlays_no_channel_warns_not_crashes():
    """--credit bật nhưng kho chưa điền kênh: KHÔNG track credit, 1 warning chỉ đường
    (channel-set / --channel) — không giết assemble."""
    from pycapcut import ScriptFile

    from autoedit.packager.assembler import _add_credit_overlays
    from autoedit.project import StageRecord

    class P:
        shots = [ShotPick(beat_id=0, asset_path="assets/a.mp4")]
        breath_shots = []

    script = ScriptFile(1920, 1080, fps=30)
    record = StageRecord.running()
    _add_credit_overlays(script, P(), record, [(0.0, 2.0, "assets/a.mp4")])
    assert "credit" not in script.tracks
    assert any("0 segment có kênh nguồn" in w for w in record.warnings)



# ===================== NHIP-M1: retime_breath_grid ============================
def _bw(bid, s, e, breath=False, bdur=0.0):
    return cov.CoverWindow(beat_id=bid, start=s, end=e, breath_shot=breath,
                           breathing_dur=bdur)


def test_retime_doi_mep_giua_mieng_ve_beat_that():
    """Mép GIỮA 2 miếng ô beat_cut dời về beat thật (boundary M-CHANGE đã chốt);
    mép VÀO/RA ô + số miếng GIỮ NGUYÊN; liền khít không hở (bẫy ① NAM CHÂM)."""
    ws = [_bw(0, 0.0, 10.0, bdur=0.5),
          _bw(0, 10.0, 13.2, breath=True), _bw(0, 13.2, 16.0, breath=True),
          _bw(1, 16.0, 20.0)]
    # beat period 0,5 trong ô (10..16) -> k=6, mốc dự kiến idx 6 = local 3.5
    pts = [(round(10.0 + (i + 1) * 0.5, 4), 0.5) for i in range(11)]
    st = cov.retime_breath_grid(ws, pts, {0})
    assert st["retimed"] == 1 and st["kept"] == 0
    assert ws[1].end == ws[2].start == 13.5          # trên beat thật, mép CHUNG 1 float
    assert st["durs"][0] == [3.5, 2.5]
    assert (ws[1].start, ws[2].end) == (10.0, 16.0)  # mép vào/ra ô không đụng
    assert not cov.check_coverage_invariants(ws, 20.0)


def test_retime_luoi_thieu_moc_giu_mep_cu():
    """Lưới không đủ mốc cho số miếng đã pick (m < n−1) -> ô GIỮ mép cũ (off-beat
    nhưng lành — không được đổi số miếng vì clip đã pick ở source)."""
    ws = [_bw(0, 10.0, 13.2, breath=True), _bw(0, 13.2, 16.0, breath=True)]
    st = cov.retime_breath_grid(ws, [(11.0, 0.5)], {0})   # 1 beat -> không lưới được
    assert st == {"retimed": 0, "kept": 1, "durs": {}}
    assert ws[0].end == 13.2 and ws[1].start == 13.2


def test_retime_bo_qua_o_ngoai_ids_va_o_1_mieng():
    """Ô đường DNA (không beat_cut) + ô 1 miếng: không đụng gì."""
    ws = [_bw(0, 10.0, 13.2, breath=True), _bw(0, 13.2, 16.0, breath=True),
          _bw(1, 20.0, 25.0, breath=True)]
    pts = [(round(10.0 + (i + 1) * 0.5, 4), 0.5) for i in range(30)]
    st = cov.retime_breath_grid(ws, pts, {1})             # beat 0 ngoài ids; beat 1 chỉ 1 miếng
    assert st == {"retimed": 0, "kept": 0, "durs": {}}
    assert ws[0].end == 13.2
