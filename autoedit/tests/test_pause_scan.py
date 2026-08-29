"""C7 — lệnh pause-dna: scan DNA nhịp nghỉ editor (MO_TA_VAN_HANH_C_DOT_1.md §C7)."""

import json

from autoedit.library.pause_scan import (
    _breath_blocks,
    compute_pause_dna,
    save_pause_dna,
    scan_draft,
    split_breath_layer,
    voice_files_of,
)


def _seg(mat_id, t_start, t_dur, s_start=0.0, s_dur=0.0):
    return {"material_id": mat_id,
            "target_timerange": {"start": int(t_start * 1e6), "duration": int(t_dur * 1e6)},
            "source_timerange": {"start": int(s_start * 1e6), "duration": int(s_dur * 1e6)}}


def _write_draft(tmp_path, audio_segs, video_segs=(), voice_name="v.mp3"):
    dc = {"tracks": [{"type": "audio", "segments": audio_segs},
                     {"type": "video", "segments": list(video_segs)}],
          "materials": {"audios": [{"id": "a1", "name": voice_name}]}}
    d = tmp_path / "DRAFT 1"
    d.mkdir(exist_ok=True)
    (d / "draft_content.json").write_text(json.dumps(dc), encoding="utf-8")
    return d


def _atrack(mat_id, n_segs, total_s):
    """Track audio n_segs segment chia đều total_s giây, cùng 1 material."""
    dur = total_s / n_segs
    return {"type": "audio",
            "segments": [_seg(mat_id, i * dur, dur, i * dur, dur) for i in range(n_segs)]}


def test_voice_track_hybrid_score_life_in_few_long_segs():
    """Regression bug life-in 2026-07-14 (REAL06/10/13/21 transcript 0 từ): voice
    ít segment dài (11 seg/27ph) phải THẮNG nhạc/SFX nhiều segment ngắn (19 seg/3,8ph)
    — tiêu chí max-segment cũ chọn nhầm nhạc."""
    dc = {"tracks": [_atrack("music", 19, 3.8 * 60), _atrack("voice", 11, 27 * 60)],
          "materials": {"audios": [{"id": "music", "name": "m.mp3"},
                                   {"id": "voice", "name": "REAL - RD06.mp4"}]}}
    segs, mats = voice_files_of(dc)
    assert mats[segs[0]["material_id"]] == "materials/REAL - RD06.mp4"
    assert len(segs) == 11


def test_voice_track_hybrid_score_deepsea_many_segs_beats_long_music():
    """Ghim hành vi deepsea (DS-53 v2): voice nhiều segment (115 seg/38ph) phải THẮNG
    nhạc trải dài (18 seg/43ph) — max-duration đơn thuần sẽ chọn nhầm nhạc."""
    dc = {"tracks": [_atrack("voice", 115, 38 * 60), _atrack("music", 18, 43 * 60)],
          "materials": {"audios": [{"id": "voice", "name": "v.wav"},
                                   {"id": "music", "name": "m.wav"}]}}
    segs, mats = voice_files_of(dc)
    assert mats[segs[0]["material_id"]] == "materials/v.wav"
    assert len(segs) == 115


def test_voice_track_hybrid_score_bed_one_long_seg_loses():
    """Ghim mẫu REAL32: bed/ambient 1 segment trải 30ph phải THUA voice 397 seg/26ph."""
    dc = {"tracks": [_atrack("bed", 1, 30 * 60), _atrack("voice", 397, 26 * 60)],
          "materials": {"audios": [{"id": "bed", "name": "bed.wav"},
                                   {"id": "voice", "name": "v.wav"}]}}
    segs, mats = voice_files_of(dc)
    assert mats[segs[0]["material_id"]] == "materials/v.wav"


def test_rows_classified_and_reconciled_with_script(tmp_path):
    """Điểm cắt cùng-file phân loại theo dấu whisper + ĐỐI CHIẾU script gốc vá
    whisper-mất-dấu (bài học §HOC-DNA-NHIP: 'follows' không dấu nhưng script có ',')."""
    words = [
        {"text": "This", "start": 0.0, "end": 0.3}, {"text": "is", "start": 0.35, "end": 0.5},
        {"text": "one.", "start": 0.55, "end": 1.0},
        {"text": "But", "start": 1.4, "end": 1.6}, {"text": "two", "start": 1.65, "end": 1.8},
        {"text": "follows", "start": 1.85, "end": 2.2},   # whisper NUỐT dấu phẩy
        {"text": "then", "start": 2.5, "end": 2.7}, {"text": "three", "start": 2.75, "end": 3.0},
    ]
    audio = [_seg("a1", 0.0, 1.0, 0.0, 1.0),        # cut nguồn tại 1.0 (sau 'one.')
             _seg("a1", 1.6, 0.7, 1.4, 0.9),        # cut nguồn tại 2.3 (sau 'follows')
             _seg("a1", 3.2, 0.6, 2.45, 0.55)]
    d = _write_draft(tmp_path, audio)
    script = "This is one. But two follows, then three."
    r = scan_draft(d, script, lambda name: words if name == "materials/v.mp3" else None)
    assert [x["kind"] for x in r["rows"]] == ["KET_CAU", "KET_MENH_DE"]
    assert all(x["script_verified"] for x in r["rows"])
    # whisper-only (không script) -> 'follows' không dấu rơi về GIUA_MENH_DE
    r2 = scan_draft(d, "", lambda name: words if name == "materials/v.mp3" else None)
    assert [x["kind"] for x in r2["rows"]] == ["KET_CAU", "GIUA_MENH_DE"]
    assert not any(x["script_verified"] for x in r2["rows"])
    # nghe_ra = nghỉ nguồn + gap chèn (row 2: (2.5-2.2) + (3.2-2.3-... ) theo target)
    assert r["rows"][0]["nghe_ra"] == round((1.4 - 1.0) + (1.6 - 1.0), 2)


def test_split_breath_layer_62c():
    """§6.2C: tách 4 lớp — breath (hold ≤1,2 + footage ≥1,5) · montage (≥4 nhát hoặc
    >20s — KHÔNG lọc phăng ô ≥8s: ô 10s ít nhát vẫn là thở) · passive · other."""
    holes = [
        {"tl_s": 0, "dur": 6.0, "shot_offsets": [0.5]},              # breath k=1
        {"tl_s": 1, "dur": 10.0, "shot_offsets": [0.5, 4.0, 7.5]},   # breath k=3 (>8s SỐNG)
        {"tl_s": 2, "dur": 25.0, "shot_offsets": [0.5]},             # montage: >20s
        {"tl_s": 3, "dur": 10.0, "shot_offsets": [0.5, 2, 4, 6]},    # montage: 4 nhát
        {"tl_s": 4, "dur": 3.0, "shot_offsets": []},                 # passive (voice-nghỉ)
        {"tl_s": 5, "dur": 5.0, "shot_offsets": [2.0]},              # other: hold 2.0 >1.2
    ]
    ls = split_breath_layer(holes)
    assert [h["tl_s"] for h in ls["breath"]] == [0, 1]
    assert ls["breath"][0]["footage"] == 5.5 and ls["breath"][0]["k"] == 1
    assert ls["breath"][1]["k"] == 3 and ls["breath"][1]["pieces"] == [3.5, 3.5, 2.5]
    assert [h["tl_s"] for h in ls["montage"]] == [2, 3]
    assert [h["tl_s"] for h in ls["passive"]] == [4]
    assert [h["tl_s"] for h in ls["other"]] == [5]


def test_breath_block_needs_5_holes():
    """<5 ô thở -> KHÔNG xuất anchors (loader fallback hằng space, không học từ mẫu mỏng)."""
    holes = [{"tl_s": i, "dur": 6.0, "shot_offsets": [0.5]} for i in range(4)]
    block, measured = _breath_blocks(holes)
    assert "footage_anchors" not in block and measured["n_breath"] == 4
    block5, _ = _breath_blocks(holes + [{"tl_s": 9, "dur": 8.0, "shot_offsets": [0.5]}])
    assert block5["footage_anchors"][0] == 5.5 and block5["hold"] == 0.5


def _breath_draft(tmp_path):
    """6 seg voice cùng file, 5 ô gap 5/5,5/6/6,5/7s — mỗi ô 1 nhát cắt video tại +0,5.
    Từ cuối seg xen kẽ '.' / ',' để có đủ 2 kinds cho load_pause_dna."""
    words, audio, video = [], [], []
    t = 0.0
    gaps = [5.0, 5.5, 6.0, 6.5, 7.0]
    for i in range(6):
        s0 = i * 10.0
        punct = "." if i % 2 == 0 else ","
        words += [{"text": "word", "start": s0 + 0.5, "end": s0 + 2.0},
                  {"text": f"end{punct}", "start": s0 + 2.5, "end": s0 + 3.9}]
        audio.append(_seg("a1", t, 4.0, s0, 4.0))
        if i < 5:
            video.append(_seg("v", t + 4.0 + 0.5, gaps[i] - 0.5))
            t += 4.0 + gaps[i]
    return _write_draft(tmp_path, audio, video), words


def test_round_trip_loaders_read_saved_file(tmp_path, monkeypatch):
    """Cổng P5 chống fail-open-im-lặng: save_pause_dna xong load_pause_dna +
    load_breath_dna phải trả ĐÚNG số đã đo (sai schema là 2 loader rơi về hằng)."""
    from autoedit.cutter.pause import BREATH_POOLED, load_breath_dna, load_pause_dna
    from autoedit.library import profile

    d, words = _breath_draft(tmp_path)
    r = scan_draft(d, "", lambda name: words if name == "materials/v.mp3" else None)
    dna = compute_pause_dna({"D1": r})
    root = tmp_path / "library"
    out, status = save_pause_dna(dna, root / "t1")
    assert status == "fresh" and out.name == "pause_dna.json"

    monkeypatch.setattr(profile, "resolve_library_root", lambda x: root)
    br = load_breath_dna("t1")
    assert br["footage_anchors"] == [4.5, 5.0, 5.5, 6.0, 6.5]  # gaps − hold 0.5
    assert br["footage_cap"] == 6.5 and br["hold"] == 0.5
    assert br["k_fractions"] == BREATH_POOLED["k_fractions"]   # chính sách k giữ fallback
    pd = load_pause_dna("t1")
    q = dna["pooled"]["kinds"]["KET_CAU"]["nghe_ra"]
    assert pd["sent"]["anchors"] == [q["p10"], q["p25"], q["p50"], q["p75"], q["p90"]]
    assert pd["sent"]["per_min"] == dna["pooled"]["kinds"]["KET_CAU"]["per_min"]


def test_save_guard_never_silently_overwrites(tmp_path):
    """File niche ĐÃ có (bản duyệt tay như space) -> mặc định ghi .new.json, bản gốc
    nguyên vẹn; --force mới đè và phải backup trước."""
    niche_d = tmp_path / "space"
    niche_d.mkdir()
    (niche_d / "pause_dna.json").write_text('{"pooled": "DA_DUYET"}', encoding="utf-8")
    dna = {"pooled": {"x": 1}}
    out, status = save_pause_dna(dna, niche_d)
    assert status == "new" and out.name == "pause_dna.new.json"
    assert json.loads((niche_d / "pause_dna.json").read_text(encoding="utf-8"))["pooled"] == "DA_DUYET"
    out2, status2 = save_pause_dna(dna, niche_d, force=True)
    assert status2 == "forced" and out2.name == "pause_dna.json"
    backups = list(niche_d.glob("pause_dna.backup-*.json"))
    assert len(backups) == 1
    assert json.loads(backups[0].read_text(encoding="utf-8"))["pooled"] == "DA_DUYET"
    assert json.loads(out2.read_text(encoding="utf-8"))["pooled"] == {"x": 1}
