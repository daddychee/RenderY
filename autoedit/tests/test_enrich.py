"""Test stage ENRICH (P2B) — gắn bổ sung approved=False + review file, bằng fake client."""

from __future__ import annotations

import json
from pathlib import Path

from autoedit.director.client import Usage
from autoedit.director.enrich import run_enrich
from autoedit.director.schema import (
    BeatEnrichment,
    ChartDatumDraft,
    EnrichmentPlan,
    InfoCardDraft,
    SupplementaryChartDraft,
)
from autoedit.project import (
    Beat,
    Project,
    SearchQueries,
    Stage,
    StageStatus,
    Word,
    create_project,
)


class FakeClient:
    """Fake: ghi nhận phương thức được gọi (complete = nội tại; complete_grounded = web)."""

    model = "fake"

    def __init__(self, plan):
        self.plan = plan
        self.complete_calls = 0
        self.grounded_calls = 0

    def complete(self, system, user, output_model):
        self.complete_calls += 1
        return self.plan, Usage(input_tokens=100, output_tokens=50)

    def complete_grounded(self, system, user, output_model):
        self.grounded_calls += 1
        return self.plan, Usage(input_tokens=300, output_tokens=50, web_searches=5)


def _beat(bid, s, e, route="stock"):
    return Beat(
        beat_id=bid, chapter=1, text=f"beat {bid}", start_word=0, end_word=1,
        start=s, end=e, energy="medium", mood="m", sourcing_route=route,
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


def test_enrich_attaches_unapproved_and_writes_review(tmp_path):
    plan = EnrichmentPlan(enrichments=[
        BeatEnrichment(beat_id=0, kind="chart", chart=SupplementaryChartDraft(
            chart_type="bar", title="Thuê nhà châu Á", unit="$",
            data=[ChartDatumDraft(label="Đà Nẵng", value=400),
                  ChartDatumDraft(label="Singapore", value=2000)],
            source_note="Numbeo 2026", rationale="bổ trợ so sánh", confidence="high")),
        BeatEnrichment(beat_id=1, kind="info_card", info_card=InfoCardDraft(
            title="Lợi ích", bullets=["Rẻ", "Đẹp", "An toàn"],
            rationale="nhấn ý", confidence="medium")),
    ])
    p = _project(tmp_path)
    run_enrich(p, FakeClient(plan))

    saved = Project.load(p.project_dir)
    assert saved.stages[Stage.ENRICH].status == StageStatus.DONE
    b0, b1 = saved.beats
    # chart bổ sung: supplementary, half, CHƯA duyệt
    assert b0.graphic_spec is not None
    assert b0.graphic_spec.data_origin == "supplementary"
    assert b0.graphic_spec.layout == "half"
    assert b0.graphic_spec.approved is False
    assert b0.graphic_spec.source_note == "Numbeo 2026"
    # info-card: chưa duyệt
    assert b1.info_card is not None and b1.info_card.approved is False
    # review file có 2 mục
    review = json.loads((Path(p.project_dir) / "enrich_review.json").read_text())
    assert len(review["items"]) == 2
    assert {i["kind"] for i in review["items"]} == {"chart", "info_card"}


def test_enrich_default_uses_internal_knowledge_not_web(tmp_path):
    """Mặc định: gọi complete (nội tại), KHÔNG complete_grounded (web)."""
    p = _project(tmp_path)
    fake = FakeClient(EnrichmentPlan(enrichments=[]))
    run_enrich(p, fake)  # use_web mặc định False
    assert fake.complete_calls >= 1 and fake.grounded_calls == 0


def test_enrich_web_flag_uses_grounded(tmp_path):
    """use_web=True: gọi complete_grounded (web search)."""
    p = _project(tmp_path)
    fake = FakeClient(EnrichmentPlan(enrichments=[]))
    run_enrich(p, fake, use_web=True)
    assert fake.grounded_calls >= 1 and fake.complete_calls == 0


def test_enrich_empty_plan_ok(tmp_path):
    """Plan rỗng là hợp lệ — không gắn gì, vẫn DONE."""
    p = _project(tmp_path)
    run_enrich(p, FakeClient(EnrichmentPlan(enrichments=[])))
    saved = Project.load(p.project_dir)
    assert saved.stages[Stage.ENRICH].status == StageStatus.DONE
    assert all(b.graphic_spec is None and b.info_card is None for b in saved.beats)


def test_enrich_requires_direct(tmp_path):
    import pytest
    p = _project(tmp_path)
    p.stages[Stage.DIRECT].status = StageStatus.PENDING
    p.save()
    with pytest.raises(RuntimeError, match="direct"):
        run_enrich(p, FakeClient(EnrichmentPlan(enrichments=[])))
