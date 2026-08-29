"""Stage ENRICH (P2B) — LLM sinh dữ kiện BỔ SUNG, TÁCH khỏi pass trích xuất.

Chạy SAU direct, TRƯỚC cut (chỉ annotate beat, không đổi word range/timestamp).
- Req 4: biểu đồ số bổ sung — web-grounded (số thật + nguồn), gắn graphic_spec
  data_origin=supplementary, layout=half, approved=False.
- Req 6: thẻ chữ bullet — info_card approved=False.
Mọi bổ sung CHƯA duyệt -> KHÔNG render (gate người duyệt qua enrich_review.json).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from autoedit.director import prompts, validator
from autoedit.director.client import DirectorClient, Usage
from autoedit.director.schema import EnrichmentPlan
from autoedit.project import (
    ChartDatum,
    CostEntry,
    GraphicSpec,
    InfoCard,
    Project,
    Stage,
    StageRecord,
    StageStatus,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_enrich(project: Project, client: DirectorClient, max_per_60s: float = 1.0,
               use_web: bool = False) -> Project:
    direct = project.stages.get(Stage.DIRECT)
    if direct is None or direct.status != StageStatus.DONE or not project.beats:
        raise RuntimeError("Stage direct chưa xong — chạy `autoedit direct` trước.")

    words = project.transcript
    beats = project.beats
    brief, channel = project.inputs.brief, project.inputs.channel
    record = StageRecord.running()
    project.stages[Stage.ENRICH] = record
    project.save()

    def track(usage: Usage, what: str) -> None:
        project.cost_log.append(CostEntry(
            stage=f"enrich/{what}", model=client.model,
            input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
            usd=usage.usd, at=_now(),
        ))

    try:
        plan = _ask_enrich(client, words, beats, brief, channel, track, record, use_web)
    except Exception as exc:
        record.status = StageStatus.FAILED
        record.error = str(exc)
        project.cost_total_usd = round(sum(c.usd for c in project.cost_log), 6)
        project.save()
        raise

    # Budget: ~max_per_60s bổ sung / 60s thoại — giữ confidence cao trước
    speech = (beats[-1].end - beats[0].start) if beats else 0.0
    cap = max(1, round(speech / 60.0 * max_per_60s))
    items = sorted(
        plan.enrichments,
        key=lambda e: 0 if _conf(e) == "high" else 1,
    )
    if len(items) > cap:
        record.warnings.append(
            f"LLM đề xuất {len(items)} bổ sung > trần {cap} (~{max_per_60s}/60s) — "
            f"giữ {cap} confidence cao nhất"
        )
        items = items[:cap]

    by_id = {b.beat_id: b for b in beats}
    applied = []
    for e in items:
        b = by_id.get(e.beat_id)
        if b is None:
            continue
        if e.kind == "chart" and e.chart is not None:
            c = e.chart
            b.graphic_spec = GraphicSpec(
                chart_type=c.chart_type, title=c.title, unit=c.unit, layout="half",
                data=[ChartDatum(label=d.label, value=d.value) for d in c.data],
                source_note=c.source_note, data_origin="supplementary", approved=False,
            )
            content = [f"{d.label}: {d.value}{c.unit}" for d in c.data]
            applied.append((b.beat_id, "chart", c.title, content, c.source_note, c.rationale, c.confidence))
        elif e.kind == "info_card" and e.info_card is not None:
            ic = e.info_card
            b.info_card = InfoCard(
                title=ic.title, bullets=ic.bullets, source_note=ic.source_note,
                approved=False,
            )
            applied.append((b.beat_id, "info_card", ic.title, list(ic.bullets), ic.source_note, ic.rationale, ic.confidence))

    _write_enrich_review(project, applied)
    if applied:
        record.warnings.append(
            f"⚠ {len(applied)} nội dung BỔ SUNG cần DUYỆT trước khi render — xem "
            "enrich_review.json, đặt approved=true cho mục muốn giữ rồi chạy lại từ source"
        )
    project.cost_total_usd = round(sum(c.usd for c in project.cost_log), 6)
    record.status = StageStatus.DONE
    record.completed_at = _now()
    project.save()
    return project


def _conf(e) -> str:
    obj = e.chart if e.kind == "chart" else e.info_card
    return getattr(obj, "confidence", "medium") if obj else "medium"


def _ask_enrich(client, words, beats, brief, channel, track, record, use_web=False) -> EnrichmentPlan:
    system = prompts.enrich_system(brief, channel, use_web=use_web)
    user = prompts.enrich_user(words, beats)
    # mặc định: kiến thức nội tại (1 call rẻ). use_web: tra web (đắt) cho số có nguồn.
    ask = client.complete_grounded if use_web else client.complete
    plan, usage = ask(system, user, EnrichmentPlan)
    track(usage, "propose")
    errors = validator.check_enrichments(plan, beats)
    if errors:
        feedback = "FIX these and re-output the EnrichmentPlan:\n- " + "\n- ".join(errors)
        plan, usage = ask(system, user + "\n\n" + feedback, EnrichmentPlan)
        track(usage, "propose_retry")
        errors2 = validator.check_enrichments(plan, beats)
        if errors2:
            # giữ các mục hợp lệ, bỏ mục lỗi (không chặn cả stage)
            bad = {int(e.split()[1]) for e in errors2 if e.split()[1].isdigit()}
            plan = EnrichmentPlan(
                enrichments=[e for j, e in enumerate(plan.enrichments) if j not in bad]
            )
            record.warnings.append(
                "enrich còn lỗi sau retry — bỏ mục lỗi: " + "; ".join(errors2)
            )
    return plan


def _write_enrich_review(project: Project, applied: list) -> None:
    """File review riêng, cờ ⚠ — người duyệt đặt approved=true trước khi render."""
    data = {
        "project": project.project_id,
        "huong_dan": "Mỗi mục dưới là nội dung BỔ SUNG do LLM sinh. Kiểm tra số/nguồn, "
        "rồi mở project.json đặt beat tương ứng approved=true (graphic_spec/info_card) "
        "để render; sai thì sửa data hoặc bỏ. Chạy lại: autoedit source ... && assemble.",
        "items": [
            {
                "beat_id": bid, "kind": kind, "title": title,
                "content": content,            # bullets (card) hoặc điểm dữ liệu (chart)
                "source_note": src, "rationale": rat, "confidence": conf,
                "approved": False,
            }
            for (bid, kind, title, content, src, rat, conf) in applied
        ],
    }
    (Path(project.project_dir) / "enrich_review.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
