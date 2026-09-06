"""Test stage ENRICH — TẮT từ 05/09 (user bỏ graphic tự render).

Stage phải là NO-OP đúng nghĩa: không gọi LLM (không tốn tiền), không gắn
chart/card vào beat, nhưng vẫn DONE để pipeline `--enrich` cũ không gãy.
"""

from __future__ import annotations

from autoedit.director.enrich import run_enrich
from autoedit.project import (
    Beat,
    SearchQueries,
    Stage,
    StageStatus,
    Word,
    create_project,
)

import pytest


class FakeClient:
    """LLM bị gọi trong stage đã tắt = đốt tiền vô ích -> nổ ngay cho test bắt."""

    model = "fake"

    def complete(self, *a, **k):
        raise AssertionError("enrich đã tắt nhưng vẫn gọi LLM (complete)")

    def complete_grounded(self, *a, **k):
        raise AssertionError("enrich đã tắt nhưng vẫn gọi LLM (complete_grounded)")


def _beat(bid, s, e):
    return Beat(
        beat_id=bid, chapter=1, text=f"beat {bid}", start_word=0, end_word=1,
        start=s, end=e, energy="medium", mood="m", sourcing_route="stock",
        visual_level="literal", visual_concept="c", shot_size="medium",
        search_queries=SearchQueries(specific=["q"]),
    )


def _project(tmp_path):
    script = tmp_path / "s.txt"; script.write_text("a")
    voice = tmp_path / "v.mp3"; voice.write_bytes(b"x")
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    p.transcript = [Word(text="w", start=0.0, end=1.0)]
    p.beats = [_beat(0, 0.0, 60.0), _beat(1, 60.0, 120.0)]
    p.stages[Stage.ALIGN].status = StageStatus.DONE
    p.stages[Stage.DIRECT].status = StageStatus.DONE
    p.save()
    return p


def test_enrich_la_noop_khong_goi_llm(tmp_path):
    p = _project(tmp_path)
    saved = run_enrich(p, FakeClient())   # FakeClient nổ nếu bị gọi
    rec = saved.stages[Stage.ENRICH]
    assert rec.status == StageStatus.DONE
    assert any("đã tắt" in w for w in rec.warnings)
    # không gắn gì lên beat
    assert all(b.graphic_spec is None and b.info_card is None for b in saved.beats)
    # không ghi review file (không có gì để duyệt)
    assert not any((tmp_path / "projects").rglob("enrich_review.json"))


def test_enrich_van_doi_direct_xong(tmp_path):
    """Gate thứ tự stage giữ nguyên — gọi sớm phải báo lỗi rõ, không im lặng no-op."""
    script = tmp_path / "s.txt"; script.write_text("a")
    voice = tmp_path / "v.mp3"; voice.write_bytes(b"x")
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    with pytest.raises(RuntimeError, match="direct"):
        run_enrich(p, FakeClient())
