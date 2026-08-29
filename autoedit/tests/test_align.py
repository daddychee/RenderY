"""Test Stage 1 Align (M2) — matcher thuần logic + runner với aligner giả.

Không gọi model thật trong pytest (chậm, tải model); chạy thật bằng
`autoedit align` trên voice mẫu — xem KE_HOACH bài kiểm tra M2.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoedit.align.base import RawWord
from autoedit.align.matcher import match_script_to_whisper, normalize_token
from autoedit.align.runner import run_align
from autoedit.project import Stage, StageStatus, create_project


def _rw(text: str, start: float, end: float) -> RawWord:
    return RawWord(text=text, start=start, end=end)


# ----------------------------- matcher --------------------------------------
def test_normalize_token():
    assert normalize_token("Hello,") == "hello"
    assert normalize_token("(world)") == "world"
    assert normalize_token("$2") == "$2"


def test_perfect_match_keeps_whisper_timestamps():
    script = "Vietnam is cheap"
    whisper = [_rw("Vietnam", 0.0, 0.5), _rw("is", 0.5, 0.7), _rw("cheap", 0.7, 1.2)]
    r = match_script_to_whisper(script, whisper)
    assert r.match_ratio == 1.0
    assert [w.text for w in r.words] == ["Vietnam", "is", "cheap"]
    assert r.words[2].start == 0.7 and r.words[2].end == 1.2
    assert not any(w.interpolated for w in r.words)


def test_punctuation_and_case_still_match():
    script = "Hello, World!"
    whisper = [_rw("hello", 0.0, 0.4), _rw("world", 0.5, 1.0)]
    r = match_script_to_whisper(script, whisper)
    assert r.match_ratio == 1.0
    # giữ nguyên chữ gốc của script (ground truth)
    assert [w.text for w in r.words] == ["Hello,", "World!"]


def test_misrecognized_word_interpolated_between_anchors():
    """1.1: Whisper nghe sai 'Hanoi' thành 'annoy' -> từ đó nội suy giữa 2 neo."""
    script = "I love Hanoi very much"
    whisper = [
        _rw("I", 0.0, 0.2),
        _rw("love", 0.2, 0.6),
        _rw("annoy", 0.6, 1.0),  # sai
        _rw("very", 1.0, 1.4),
        _rw("much", 1.4, 1.8),
    ]
    r = match_script_to_whisper(script, whisper)
    hanoi = r.words[2]
    assert hanoi.text == "Hanoi"
    assert hanoi.interpolated
    # nội suy phải nằm giữa neo trước (love end=0.6) và neo sau (very start=1.0)
    assert 0.6 <= hanoi.start < hanoi.end <= 1.0
    # các từ khác giữ timestamp whisper
    assert r.words[3].start == 1.0
    assert r.match_ratio == pytest.approx(4 / 5)


def test_extra_script_words_at_end_interpolated_to_audio_duration():
    """Voice thiếu câu cuối -> từ cuối script nội suy tới hết file, có cảnh báo ratio."""
    script = "one two three four"
    whisper = [_rw("one", 0.0, 0.3), _rw("two", 0.3, 0.6)]
    r = match_script_to_whisper(script, whisper, audio_duration=2.0)
    assert [w.interpolated for w in r.words] == [False, False, True, True]
    assert r.words[3].end == pytest.approx(2.0)
    assert r.match_ratio == 0.5


def test_timestamps_monotonic_non_overlapping_gap():
    script = "a b c d e"
    whisper = [_rw("a", 0.0, 0.2), _rw("e", 2.0, 2.2)]
    r = match_script_to_whisper(script, whisper)
    starts = [w.start for w in r.words]
    assert starts == sorted(starts)
    # 3 từ nội suy chia đều khoảng (0.2, 2.0)
    assert r.words[1].start == pytest.approx(0.2)
    assert r.words[3].end == pytest.approx(2.0)


def test_empty_whisper_raises():
    with pytest.raises(ValueError, match="không trả từ nào"):
        match_script_to_whisper("hello", [])


# ----------------------------- runner ---------------------------------------
class FakeAligner:
    def __init__(self, words: list[RawWord]):
        self._words = words

    def transcribe(self, audio_path: Path) -> list[RawWord]:
        assert Path(audio_path).is_file()
        return self._words


@pytest.fixture
def project(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("Vietnam is cheap", encoding="utf-8")
    voice = tmp_path / "voice.mp3"
    voice.write_bytes(b"fake")
    return create_project(script, voice, out_dir=tmp_path / "projects")


def test_run_align_writes_transcript_and_stage(project):
    aligner = FakeAligner([_rw("Vietnam", 0.0, 0.5), _rw("is", 0.5, 0.7), _rw("cheap", 0.7, 1.2)])
    run_align(project, aligner)

    from autoedit.project import Project

    saved = Project.load(project.project_dir)
    assert saved.stages[Stage.ALIGN].status == StageStatus.DONE
    assert saved.stages[Stage.ALIGN].completed_at
    assert saved.stages[Stage.ALIGN].warnings == []
    assert len(saved.transcript) == 3
    assert (Path(project.project_dir) / "transcript.json").is_file()


def test_run_align_warns_on_low_match_ratio(project):
    # chỉ 1/3 từ khớp -> cảnh báo 0.1
    aligner = FakeAligner([_rw("Vietnam", 0.0, 0.5), _rw("xxx", 0.5, 0.7), _rw("yyy", 0.7, 1.2)])
    run_align(project, aligner)
    warnings = project.stages[Stage.ALIGN].warnings
    assert any("lệch nhau" in w for w in warnings)


def test_run_align_failure_marks_stage_failed(project):
    class BoomAligner:
        def transcribe(self, audio_path):
            raise RuntimeError("model nổ")

    with pytest.raises(RuntimeError):
        run_align(project, BoomAligner())

    from autoedit.project import Project

    saved = Project.load(project.project_dir)
    assert saved.stages[Stage.ALIGN].status == StageStatus.FAILED
    assert "model nổ" in saved.stages[Stage.ALIGN].error
