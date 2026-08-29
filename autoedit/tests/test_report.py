"""Test stage REPORT — report.html gom đúng việc CẦN XỬ LÝ + escape an toàn."""

from __future__ import annotations

from pathlib import Path

import pytest

from autoedit.project import (
    Beat,
    InfoCard,
    SearchQueries,
    ShotPick,
    Stage,
    StageStatus,
    VoiceSegment,
    create_project,
)
from autoedit.report.runner import run_report


def _beat(bid, ts, te, text="thoại", route="stock"):
    return Beat(
        beat_id=bid, chapter=1, text=text, start_word=0, end_word=1, start=ts, end=te,
        timeline_start=ts, timeline_end=te, energy="medium", mood="m", sourcing_route=route,
        visual_level="literal", visual_concept="c", shot_size="medium",
        search_queries=SearchQueries(specific=["beach aerial"]),
    )


def _project(tmp_path):
    script = tmp_path / "s.txt"; script.write_text("a")
    voice = tmp_path / "v.mp3"; voice.write_bytes(b"x")
    p = create_project(script, voice, out_dir=tmp_path / "proj")
    p.beats = [
        _beat(0, 0.0, 5.0, text="beat ok <script>"),       # có < > để test escape
        _beat(1, 5.0, 10.0, text="beat thiếu footage"),
        _beat(2, 10.0, 15.0, text="beat entity", route="entity"),
    ]
    p.beats[2].info_card = InfoCard(title="Visa", bullets=["a", "b", "c"], approved=False)
    p.shots = [
        ShotPick(beat_id=0, status="ok", source="pexels", asset_path="assets/b000.mp4",
                 alternates=["https://pexels.com/x", "https://pexels.com/y"]),
        ShotPick(beat_id=1, status="needs_human", source="none", note="hết fallback"),
        ShotPick(beat_id=2, status="ok", source="entity", asset_path="assets/b002.jpg",
                 licensing_flag=True, note="ảnh Wikipedia"),
    ]
    p.segments = [VoiceSegment(segment_id=1, path="segments/seg_001.wav", source_start=0.0,
                              source_end=15.0, timeline_start=0.0, timeline_end=15.0, beat_ids=[0, 1, 2])]
    p.music_selections = {"1": "Roie Shpigler - Northland.mp3"}
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT, Stage.SOURCE, Stage.RANK):
        p.stages[st].status = StageStatus.DONE
    p.stages[Stage.SOURCE].warnings.append("beat 1: không có asset")
    p.save()
    return p


def test_report_generates_html_with_action_items(tmp_path):
    p = _project(tmp_path)
    run_report(p)
    out = Path(p.project_dir) / "report.html"
    assert out.is_file()
    htm = out.read_text(encoding="utf-8")
    assert p.stages[Stage.REPORT].status == StageStatus.DONE
    # CẦN XỬ LÝ: 1 thiếu footage + 1 licensing + 1 enrich chưa duyệt = 3
    assert "CẦN XỬ LÝ (3)" in htm
    assert "beach aerial" in htm           # gợi ý từ khoá cho beat thiếu
    assert "Visa" in htm                    # enrich chờ duyệt
    assert "Northland" in htm               # nhạc
    # escape: '<script>' trong text không được render thành thẻ
    assert "<script>" not in htm and "&lt;script&gt;" in htm
    # C4 fail-open: project không outline/tone -> KHÔNG có card Tone
    assert "Tone video" not in htm


def test_report_shows_video_tone_c4(tmp_path):
    """C4/b1: outline có tone -> report in card 'Tone video' cho editor đối chiếu."""
    p = _project(tmp_path)
    p.outline = {"tone": "trầm lắng, kinh ngạc khoa học", "chapters": []}
    p.save()
    run_report(p)
    htm = (Path(p.project_dir) / "report.html").read_text(encoding="utf-8")
    assert "Tone video" in htm and "trầm lắng, kinh ngạc khoa học" in htm


def test_report_marks_peak_picks(tmp_path):
    """ytref §3h: pick mang cờ điểm nhô -> bảng beat đánh dấu ⭐ + dòng đếm;
    project không có cờ (mọi project cũ) -> report im lặng y cũ."""
    p = _project(tmp_path)
    run_report(p)
    htm = (Path(p.project_dir) / "report.html").read_text(encoding="utf-8")
    assert "⭐" not in htm and "pick điểm nhô" not in htm
    p.shots[0].peak = True
    p.save()
    run_report(p)
    htm = (Path(p.project_dir) / "report.html").read_text(encoding="utf-8")
    assert "⭐ b000.mp4" in htm and "pick điểm nhô: 1" in htm


def test_report_requires_source(tmp_path):
    p = _project(tmp_path)
    p.stages[Stage.SOURCE].status = StageStatus.PENDING
    p.save()
    with pytest.raises(RuntimeError, match="source"):
        run_report(p)
