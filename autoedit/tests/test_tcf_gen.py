"""tcf-gen — sinh 'topic + chapter video.txt' từ voice (KE_HOACH_NAP_DEEPSEA.md bước 2)."""

import json

import pytest

from autoedit.library.ingest import read_draft_context
from autoedit.library.tcf_gen import (
    TCFChapter,
    TCFOut,
    _snap_chapters,
    generate_tcf,
    render_tcf,
    timeline_blocks,
)


def _seg(mat_id, t_start, t_dur, s_start=0.0, s_dur=0.0):
    return {"material_id": mat_id,
            "target_timerange": {"start": int(t_start * 1e6), "duration": int(t_dur * 1e6)},
            "source_timerange": {"start": int(s_start * 1e6), "duration": int(s_dur * 1e6)}}


def _write_draft(tmp_path, audio_segs, audios):
    dc = {"tracks": [{"type": "audio", "segments": audio_segs},
                     {"type": "video", "segments": []}],
          "materials": {"audios": audios}}
    d = tmp_path / "DS TEST 1"
    d.mkdir(exist_ok=True)
    (d / "draft_content.json").write_text(json.dumps(dc), encoding="utf-8")
    return d


def test_timeline_blocks_maps_source_to_timeline_via_path_basename(tmp_path):
    """Bẫy draft editor: material name ≠ file đĩa → resolve theo basename của path;
    words dời từ source-time sang timeline-time."""
    words = [{"text": "hello", "start": 10.0, "end": 10.4},
             {"text": "world", "start": 10.5, "end": 11.0}]
    # segment lấy nguồn 10.0-11.0 của file TRIM, đặt lên timeline tại 100.0
    d = _write_draft(
        tmp_path, [_seg("a1", 100.0, 1.0, 10.0, 1.0)],
        [{"id": "a1", "name": "voi ds 1.mp3",
          "path": "D:/CapCut Drafts/OLD/materials/voi ds 1_TRIM_7.mp3"}])
    got = {}
    blocks = timeline_blocks(
        d, lambda nm: got.setdefault("nm", nm) and words if nm else None)
    assert got["nm"] == "materials/voi ds 1_TRIM_7.mp3"  # theo path, KHÔNG theo name
    assert len(blocks) == 1
    assert blocks[0]["start"] == pytest.approx(100.0)   # timeline, không phải 10.0
    assert blocks[0]["text"] == "hello world"


def test_timeline_blocks_resolves_placeholder_path(tmp_path):
    """Bẫy 2 (DS-53 v2): path placeholder ##_draftpath_placeholder_GUID_##/Resources/
    local/x.mp3 — voice ngoài materials/ → resolve phần sau _##/ về folder draft."""
    words = [{"text": "abyss", "start": 0.0, "end": 0.5}]
    d = _write_draft(
        tmp_path, [_seg("a1", 0.0, 0.5, 0.0, 0.5)],
        [{"id": "a1", "name": "1.mp3",
          "path": "##_draftpath_placeholder_0E68-ABCD_##/Resources/local/1a97.mp3"}])
    got = {}
    blocks = timeline_blocks(d, lambda nm: got.setdefault("nm", nm) and words)
    assert got["nm"] == "Resources/local/1a97.mp3"
    assert blocks and blocks[0]["text"] == "abyss"


def test_snap_forces_first_chapter_to_zero_and_drops_invented_marks():
    allowed = [0.0, 45.0, 90.0, 135.0]
    chapters = [TCFChapter(start="0:02", title="Intro"),      # snap 0 -> ép 0:00
                TCFChapter(start="1:33", title="Giữa"),        # 93 -> snap 90
                TCFChapter(start="9:59", title="Bịa")]         # xa mọi block -> bỏ
    out = _snap_chapters(chapters, allowed)
    assert out == [(0.0, "Intro"), (90.0, "Giữa")]


def test_generate_tcf_end_to_end_and_ingest_can_parse(tmp_path, monkeypatch):
    """Happy path: draft giả → client giả → file TCF đúng format parser ingest."""
    monkeypatch.setattr("autoedit.library.tcf_gen.MIN_WORDS", 4)
    monkeypatch.setattr("autoedit.library.tcf_gen.BLOCK_S", 2.0)  # 4s voice -> 2 block
    words = [{"text": w, "start": i * 0.5, "end": i * 0.5 + 0.4}
             for i, w in enumerate("the giant squid hides in the deep trench".split())]
    d = _write_draft(tmp_path, [_seg("a1", 0.0, 4.0, 0.0, 4.0)],
                     [{"id": "a1", "name": "v.mp3", "path": "X:/old/materials/v.mp3"}])

    class FakeClient:
        def complete(self, system, user, output_model):
            assert "[0:00]" in user and "[0:02]" in user
            return TCFOut(title="Giant Squid of the Deep",
                          chapters=[TCFChapter(start="0:00", title="Intro"),
                                    TCFChapter(start="0:02", title="The Trench")]), None

    out, status = generate_tcf(d, FakeClient(), lambda nm: words)
    assert status == "fresh" and out.name == "topic + chapter video.txt"
    ctx = read_draft_context(d)
    assert ctx.topic == "Giant Squid of the Deep"
    assert [c["title"] for c in ctx.chapters] == ["Intro", "The Trench"]
    # chạy lại không --force -> skip, không gọi LLM
    out2, status2 = generate_tcf(d, None, lambda nm: None)
    assert status2 == "skip" and out2 == out


def _write_draft_music_beats_voice(tmp_path):
    """Draft mẫu REAL79: track nhạc điểm lai CAO HƠN track voice (nhiều seg + trải dài)."""
    music_segs = [_seg("m", i * 45.0, 45.0, 0.0, 45.0) for i in range(37)]
    voice_segs = [_seg("v", i * 120.0, 120.0, i * 120.0, 120.0) for i in range(2)]
    dc = {"tracks": [{"type": "audio", "segments": music_segs},
                     {"type": "audio", "segments": voice_segs},
                     {"type": "video", "segments": []}],
          "materials": {"audios": [{"id": "m", "name": "music.wav", "path": "music.wav"},
                                   {"id": "v", "name": "voice.mp3", "path": "voice.mp3"}]}}
    d = tmp_path / "REAL TEST"
    d.mkdir(exist_ok=True)
    (d / "draft_content.json").write_text(json.dumps(dc), encoding="utf-8")
    return d


class _FallbackClient:
    def complete(self, system, user, output_model):
        return TCFOut(title="Country X", chapters=[
            TCFChapter(start="0:00", title="Intro"),
            TCFChapter(start="1:00", title="Body")]), None


_VOICE_WORDS = [{"text": w, "start": i * 30.0, "end": i * 30.0 + 0.4}
                for i, w in enumerate("life in the strangest country on earth".split())]


def test_generate_tcf_fallback_when_top_track_is_music(tmp_path, monkeypatch):
    """Regression REAL79 2026-07-14: track nhạc thắng điểm lai → transcript <MIN_WORDS
    → tcf-gen tự thử track hạng kế (voice thật), KHÔNG chết mù."""
    monkeypatch.setattr("autoedit.library.tcf_gen.MIN_WORDS", 4)
    monkeypatch.setattr("autoedit.library.tcf_gen.BLOCK_S", 30.0)
    d = _write_draft_music_beats_voice(tmp_path)
    words_for = lambda nm: (_VOICE_WORDS if "voice" in nm
                            else [{"text": "la", "start": 0.0, "end": 0.4}])
    out, status = generate_tcf(d, _FallbackClient(), words_for)
    assert status == "fresh"
    assert "Country X" in out.read_text(encoding="utf-8")


def test_generate_tcf_fallback_when_top_tracks_are_empty_music(tmp_path, monkeypatch):
    """Regression EX247 2026-07-18: voice trong .mp4 ÍT-cắt tụt hạng dưới 2 track nhạc;
    faster-whisper VAD lọc sạch nhạc -> 0 từ -> [] (KHÔNG phải None). Code cũ `break` khi
    [] (tưởng hết track) -> chết mù dù voice ở hạng 2. Nay phân biệt []=nhạc-rỗng (thử kế)
    với None=hết-track (dừng)."""
    monkeypatch.setattr("autoedit.library.tcf_gen.MIN_WORDS", 4)
    monkeypatch.setattr("autoedit.library.tcf_gen.BLOCK_S", 30.0)
    # 3 track: 2 nhạc điểm-lai-cao (nhiều seg) + voice .mp4 hạng 2 (2 seg, trải dài)
    m1 = [_seg("m1", i * 30.0, 30.0, 0.0, 30.0) for i in range(11)]
    m2 = [_seg("m2", i * 45.0, 45.0, 0.0, 45.0) for i in range(8)]
    voice = [_seg("v", i * 700.0, 700.0, i * 700.0, 700.0) for i in range(2)]
    dc = {"tracks": [{"type": "audio", "segments": m1},
                     {"type": "audio", "segments": m2},
                     {"type": "audio", "segments": voice},
                     {"type": "video", "segments": []}],
          "materials": {"audios": [
              {"id": "m1", "name": "music1.mp3", "path": "music1.mp3"},
              {"id": "m2", "name": "music2.mp3", "path": "music2.mp3"},
              {"id": "v", "name": "Bai 247 EX.mp4", "path": "Bai 247 EX.mp4"}]}}
    d = tmp_path / "EX247 TEST"
    d.mkdir(exist_ok=True)
    (d / "draft_content.json").write_text(json.dumps(dc), encoding="utf-8")
    # nhạc -> [] (VAD sạch), voice .mp4 -> transcript đủ
    words_for = lambda nm: (_VOICE_WORDS if "Bai 247" in nm else [])
    out, status = generate_tcf(d, _FallbackClient(), words_for)
    assert status == "fresh"
    assert "Country X" in out.read_text(encoding="utf-8")


def test_generate_tcf_fallback_when_top_track_transcribe_crashes(tmp_path, monkeypatch):
    """Regression REAL72 2026-07-14: file track điểm cao hỏng (avcodec nổ) → không
    chết cả draft, thử track hạng kế."""
    monkeypatch.setattr("autoedit.library.tcf_gen.MIN_WORDS", 4)
    monkeypatch.setattr("autoedit.library.tcf_gen.BLOCK_S", 30.0)
    d = _write_draft_music_beats_voice(tmp_path)

    def words_for(nm):
        if "music" in nm:
            raise RuntimeError("[Errno 50531338] avcodec_send_packet()")
        return _VOICE_WORDS

    out, status = generate_tcf(d, _FallbackClient(), words_for)
    assert status == "fresh"
    assert "Country X" in out.read_text(encoding="utf-8")


def test_generate_tcf_refuses_thin_transcript(tmp_path):
    """Transcript quá ngắn = nghi sai track voice → lỗi rõ, không sinh TCF mù."""
    d = _write_draft(tmp_path, [_seg("a1", 0.0, 1.0, 0.0, 1.0)],
                     [{"id": "a1", "name": "v.mp3", "path": "v.mp3"}])
    with pytest.raises(RuntimeError, match="từ"):
        generate_tcf(d, None, lambda nm: [{"text": "hi", "start": 0.0, "end": 0.3}])
    assert not (d / "topic + chapter video.txt").exists()


def test_generate_tcf_all_tracks_empty_stops_not_loops(tmp_path):
    """Mọi track audio VAD ra rỗng ([]) -> timeline_blocks cuối trả None (hết track) ->
    vòng while THOÁT + raise, KHÔNG lặp vô hạn (bảo hiểm cho `while True` mới)."""
    d = _write_draft_music_beats_voice(tmp_path)  # 2 track audio
    with pytest.raises(RuntimeError, match="từ"):
        generate_tcf(d, None, lambda nm: [])  # mọi track: 0 từ
    assert not (d / "topic + chapter video.txt").exists()


def test_render_tcf_matches_ingest_parser(tmp_path):
    txt = render_tcf("Deep Sea Mysteries", [(0.0, "Intro"), (95.0, "The Abyss")])
    d = tmp_path / "D1"
    d.mkdir()
    (d / "topic + chapter video.txt").write_text(txt, encoding="utf-8")
    ctx = read_draft_context(d)
    assert ctx.topic == "Deep Sea Mysteries"
    assert [c["title"] for c in ctx.chapters] == ["Intro", "The Abyss"]
    assert ctx.chapters[0]["start_time"] == 0 and ctx.chapters[1]["start_time"] == 95


# ===================== mode FILE NGUỒN (MO_TA_VAN_HANH_TCF_FILE_NGUON.md) =====
def test_source_blocks_gom_theo_block():
    from autoedit.library.tcf_gen import BLOCK_S, source_blocks
    words = [{"text": "a", "start": 0.0}, {"text": "b", "start": 10.0},
             {"text": "c", "start": BLOCK_S + 1}, {"text": "d", "start": BLOCK_S + 2}]
    bl = source_blocks(words)
    assert [b["start"] for b in bl] == [0.0, BLOCK_S + 1]
    assert bl[0]["text"] == "a b" and bl[1]["text"] == "c d"


class _FakeClient:
    def __init__(self, out):
        self.out = out
        self.calls = 0

    def complete(self, system, user, schema):
        self.calls += 1
        return self.out, {"input_tokens": 1}


def _write_words_cache(cache_dir, media_name, n_words=250, gap=1.0):
    from autoedit.library.pause_scan import sanitize
    cache_dir.mkdir(parents=True, exist_ok=True)
    words = [{"text": f"w{i}", "start": i * gap, "end": i * gap + 0.4}
             for i in range(n_words)]
    (cache_dir / f"SRC__{sanitize(media_name)}.words.json").write_text(
        json.dumps(words), encoding="utf-8")


def test_source_chapters_khuon_ytinfo_va_cache(tmp_path):
    """Chapter theo giây FILE, đúng khuôn YTVideoInfo.chapters (end = start kế);
    lần 2 ăn cache kết quả — KHÔNG gọi NÃO lại."""
    from autoedit.library.tcf_gen import TCFChapter, TCFOut, source_chapters

    cache = tmp_path / "pause_scan_cache"
    media = tmp_path / "mau video.mp4"; media.touch()
    _write_words_cache(cache, media.name)          # words sẵn -> không cần whisper
    out = TCFOut(title="Mẫu Space", chapters=[
        TCFChapter(start="0:00", title="Mở đầu"),
        TCFChapter(start="1:30", title="Thân bài"),   # snap về block 90s
    ])
    client = _FakeClient(out)
    chs = source_chapters(media, cache, lambda: client)
    assert [c["title"] for c in chs] == ["Mở đầu", "Thân bài"]
    assert chs[0]["start_time"] == 0.0 and chs[0]["end_time"] == chs[1]["start_time"]
    assert chs[1]["end_time"] is None
    # map bằng _chapter_at của ingest (cùng khuôn — không đường parse mới)
    from autoedit.library.ingest import _chapter_at
    assert _chapter_at(chs, 100.0) == "Thân bài"
    # lần 2: cache tcf.json -> factory không được gọi
    def _boom():
        raise AssertionError("cache hit thì không tạo NÃO")
    chs2 = source_chapters(media, cache, _boom)
    assert chs2 == chs and client.calls == 1


def test_source_chapters_it_loi_khong_sinh_mu(tmp_path):
    from autoedit.library.tcf_gen import source_chapters

    cache = tmp_path / "pause_scan_cache"
    media = tmp_path / "nhac khong loi.mp4"; media.touch()
    _write_words_cache(cache, media.name, n_words=50)   # <MIN_WORDS
    with pytest.raises(RuntimeError, match="ít lời"):
        source_chapters(media, cache, lambda: _FakeClient(None))


def test_yt_chapter_gate_duration_lech():
    """Editor cắt bỏ đoạn -> duration lệch >3% -> chapter BỎ + warning; khớp -> giữ.
    Không chapter -> không đụng (không warning rác)."""
    from types import SimpleNamespace

    from autoedit.library.ingest import yt_chapter_gate
    from autoedit.library.ytpeaks import YTVideoInfo

    ch = [{"title": "Intro", "start_time": 0.0, "end_time": 60.0}]
    scenes = [SimpleNamespace(source="F:/a.mp4", source_duration=600.0),
              SimpleNamespace(source="F:/b.mp4", source_duration=540.0),
              SimpleNamespace(source="F:/c.mp4", source_duration=600.0)]
    infos = {
        "F:/a.mp4": YTVideoInfo(video_id="x", duration=600.0, chapters=list(ch)),
        "F:/b.mp4": YTVideoInfo(video_id="y", duration=600.0, chapters=list(ch)),  # lệch 10%
        "F:/c.mp4": YTVideoInfo(video_id="z", duration=600.0),                     # không chapter
    }
    ok, warns = yt_chapter_gate(scenes, infos)
    assert ok == {"F:/a.mp4"}
    assert len(warns) == 1 and "b.mp4" in warns[0] and "mốc trượt" in warns[0]
