"""Test module nhạc — chọn theo mood chương (pure logic) + map vocab."""

from __future__ import annotations

from autoedit.music.library import _map_tags, MOOD
from autoedit.music.select import _chapter_moods, select_music


def _track(file, mood, energy=0.5, tempo="medium", vocals="instrumental", dur=180.0):
    return {"file": file, "mood": mood, "energy": energy, "tempo_class": tempo,
            "vocals": vocals, "duration_sec": dur, "loopable": True}


def _chapter(cid, mood, energy="medium", start=0.0, end=60.0, hint=""):
    return {"chapter_id": cid, "mood": mood, "energy": energy, "music_hint": hint,
            "timeline_start": start, "timeline_end": end}


def test_select_matches_mood():
    index = [_track("peace.mp3", ["peaceful", "hopeful"]),
             _track("tense.mp3", ["tense", "dark"]),
             _track("happy.mp3", ["happy", "playful"])]
    picks = select_music([_chapter(1, "warm_inviting")], index)
    assert picks[0]["file"] == "peace.mp3"      # warm->hopeful/peaceful
    picks = select_music([_chapter(1, "urgent_dark")], index)
    assert picks[0]["file"] == "tense.mp3"


def test_select_no_repeat_within_video():
    index = [_track("a.mp3", ["peaceful"]), _track("b.mp3", ["peaceful"])]
    picks = select_music([_chapter(1, "calm"), _chapter(2, "calm")], index)
    assert {p["file"] for p in picks} == {"a.mp3", "b.mp3"}   # 2 chương -> 2 bài khác


def test_select_skips_vocals():
    index = [_track("voc.mp3", ["peaceful"], vocals="female_vocals"),
             _track("inst.mp3", ["peaceful"], vocals="instrumental")]
    picks = select_music([_chapter(1, "calm")], index)
    assert picks[0]["file"] == "inst.mp3"        # bỏ nhạc có lời


def test_start_offset_high_energy_uses_drop():
    from autoedit.music.select import _start_offset
    track = {"sections": {"intro": [0, 10], "build": [10, 40], "drop": [40, 70], "outro": [70, 90]}}
    assert _start_offset({"energy": "high"}, track) == 40.0   # cao trào -> drop
    assert _start_offset({"energy": "medium"}, track) == 10.0  # vừa -> build
    assert _start_offset({"energy": "low"}, track) == 0.0      # lắng -> intro


def test_usage_penalty_prefers_less_used():
    index = [_track("often.mp3", ["peaceful"]), _track("rare.mp3", ["peaceful"])]
    # cùng mood; often.mp3 đã dùng nhiều -> chọn rare.mp3
    picks = select_music([_chapter(1, "calm")], index, usage={"often.mp3": 5})
    assert picks[0]["file"] == "rare.mp3"


def test_drive_high_energy_prefers_ro_nhip():
    """Regression bug thang energy (2026-07-14): 2 bài CÙNG mood, chương cao trào phải
    chọn bài nhịp rõ (tier A, bpm cao) thay vì ambient trôi (tier C) — code cũ chấm
    energy librosa (độ phẳng) nên tie/chọn sai."""
    ambient = _track("ambient.mp3", ["mysterious"])
    ambient.update({"beat_tier": "C", "bpm": 118.0})
    don = _track("don.mp3", ["mysterious"])
    don.update({"beat_tier": "A", "bpm": 140.0})
    picks = select_music([_chapter(1, "curious", energy="high")], [ambient, don])
    assert picks[0]["file"] == "don.mp3"


def test_drive_low_energy_prefers_em():
    """Chiều ngược: chương lắng chọn bài êm (dreamy tier C) thay bài dồn (tense tier A)."""
    don = _track("don.mp3", ["tense"])
    don.update({"beat_tier": "A", "bpm": 140.0})
    em = _track("em.mp3", ["dreamy"])
    em.update({"beat_tier": "C", "bpm": 118.0})
    # mood chương không khớp bài nào -> drive quyết
    picks = select_music([_chapter(1, "neutral_documentary", energy="low")], [don, em])
    assert picks[0]["file"] == "em.mp3"


def test_entry_intensity_low_chapter_avoids_loud_intro():
    """Per-section (user 2026-07-14: bpm đổi theo đoạn trong bài): chương lắng vào nhạc
    ở intro -> bài intro ồn (curve đầu cao) thua bài intro êm, dù mood/tier/bpm y hệt."""
    loud_intro = _track("loud.mp3", ["peaceful"])
    loud_intro.update({"beat_tier": "B", "bpm": 90.0, "duration_sec": 80.0,
                       "energy_curve": [0.95, 0.9, 0.9, 0.85, 0.9, 0.9, 0.85, 0.9],
                       "sections": {"intro": [0, 10], "drop": [40, 50]}})
    soft_intro = _track("soft.mp3", ["peaceful"])
    soft_intro.update({"beat_tier": "B", "bpm": 90.0, "duration_sec": 80.0,
                       "energy_curve": [0.3, 0.5, 0.7, 0.9, 1.0, 0.8, 0.5, 0.3],
                       "sections": {"intro": [0, 10], "drop": [40, 50]}})
    picks = select_music([_chapter(1, "calm", energy="low")], [loud_intro, soft_intro])
    assert picks[0]["file"] == "soft.mp3"


def test_chapter_moods_synonyms():
    assert "tense" in _chapter_moods({"mood": "urgent_anticipatory"})
    assert _chapter_moods({"mood": "warm"}) & {"hopeful", "peaceful"}
    assert "epic" in _chapter_moods({"mood": "grand_triumphant"})


def test_manifest_from_filenames(tmp_path):
    from autoedit.music.naming import manifest_from_tracks

    td = tmp_path / "tracks"; td.mkdir()
    for name in [
        "Roie Shpigler - Northland __peaceful __hopeful.mp3",   # đa mood
        "Daniel Magen - Wish You Were Here __nostalgic.mp3",    # base trùng ↓
        "Daniel Magen - Wish You Were Here __peaceful.mp3",     # -> gộp union mood, 1 entry
        "Ziv Moran - EVERGREEN - Short version __uplifting.mp3",  # -> skip
        "Foo - Bar __weirdtag.mp3",                              # tag lạ
    ]:
        (td / name).touch()
    entries, unknown = manifest_from_tracks(td)

    by_title = {e["title"]: e for e in entries}
    assert set(by_title["Northland"]["mood"]) == {"peaceful", "hopeful"}
    assert by_title["Northland"]["artist"] == "Roie Shpigler"
    # base trùng -> 1 entry, union mood
    wish = [e for e in entries if e["title"] == "Wish You Were Here"]
    assert len(wish) == 1 and set(wish[0]["mood"]) == {"nostalgic", "peaceful"}
    # short version bị bỏ
    assert not any("Short version" in e["file"] for e in entries)
    # tag lạ -> báo, không vào mood
    assert "weirdtag" in unknown


def test_map_tags_to_vocab():
    sink = set()
    assert _map_tags(["Peaceful", "up-beat"], MOOD, sink) == ["peaceful"]
    assert "up_beat" in sink                      # tag lạ -> sink để báo
