"""Stage 2 — Direct: điều phối 2 pass LLM, validate, ghi beats vào project.json.

Pass 1: toàn script -> Outline (chương/mood/motif) — hiểu toàn cục (Kuleshov, 2.5)
Pass 2: từng chương -> beats, kèm outline + beat cuối chương trước làm ngữ cảnh
Retry: tối đa 1 lần/pass/chương, kèm mô tả lỗi cụ thể; vẫn lỗi -> warning (đã chốt với user)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from autoedit.director import prompts
from autoedit.director.client import DirectorClient, Usage
from autoedit.director.schema import BeatDraft, ChapterBeats, Outline
from autoedit.director import validator
from autoedit.overlay.style import resolve_overlay
from autoedit.project import (
    Beat,
    CostEntry,
    Project,
    Stage,
    StageRecord,
    StageStatus,
)


# Voice ngắn hơn ngưỡng này -> GỘP outline về MỘT chương trước khi sang pass 2.
# Hook/End thường 20-60s: chia 3-4 chương là logic của video 20 phút áp nhầm, tốn
# 3-4 lượt LLM cho cùng một ý và làm tempo phẳng (chính validator kêu "các chương
# cùng một nhịp"). Đo 30/08 trên hook LI093 34s: 3 chương -> 6 lượt gọi.
NGUONG_MOT_CHUONG_GIAY = 120.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _gop_mot_chuong(outline: Outline, words) -> Outline:
    """Gộp mọi chương của outline thành 1, giữ nguyên tone/motif/chủ thể toàn cục.

    Không bỏ pass 1: nó cho tone, motifs, video_subject — thứ pass 2 cần. Chỉ bỏ
    việc CẮT VỤN một đoạn ngắn thành nhiều chương.
    """
    chs = outline.chapters
    if len(chs) <= 1:
        return outline
    dau = chs[0]
    gop = dau.model_copy(update={
        "chapter_id": dau.chapter_id,
        "start_word": min(c.start_word for c in chs),
        "end_word": max(c.end_word for c in chs),
        # tiêu đề chương đầu thường đã là tiêu đề của cả đoạn ngắn
        "title": dau.title,
    })
    return outline.model_copy(update={"chapters": [gop]})


def run_direct(project: Project, client: DirectorClient, on_progress=None,
               gop_chuong_ngan: bool = True) -> Project:
    """on_progress(done, total, label): gọi theo tiến độ (pass 1 + mỗi chương) cho CLI in."""
    align = project.stages.get(Stage.ALIGN)
    if align is None or align.status != StageStatus.DONE or not project.transcript:
        raise RuntimeError(
            "Stage align chưa xong hoặc transcript rỗng — chạy `autoedit align` trước."
        )

    def _progress(done, total, label):
        if on_progress:
            on_progress(done, total, label)

    words = project.transcript
    n = len(words)
    brief, channel = project.inputs.brief, project.inputs.channel
    # D2: đường direct cũ ăn CÙNG 2 khối tri thức kho với đường sâu — tái dùng nguyên
    # hàm của live.py (import lười vì live import ngược runner). Chỉ vào pass 2: đó là
    # nơi quyết queries.local (vocab C4) + độ dài beat/shot_count (DNA Mảnh A).
    # Fail-open sẵn trong 2 hàm: không channel / kho rỗng / không dna.json -> "".
    from autoedit.director.live import (
        boost_block, dna_block, vocab_block, world_lock_block)

    niche = channel or ""
    # BOOST: đường cũ ăn CÙNG khối sở-thích-khán-giả với đường sâu (khuôn D2)
    library_context = "\n\n".join(
        b for b in (world_lock_block(niche), vocab_block(niche), dna_block(niche),
                    boost_block(project, niche)) if b
    ) or None

    record = StageRecord.running()
    project.stages[Stage.DIRECT] = record
    project.save()

    total_usage = Usage()

    def track(usage: Usage, what: str) -> None:
        total_usage.input_tokens += usage.input_tokens
        total_usage.output_tokens += usage.output_tokens
        project.cost_log.append(
            CostEntry(
                stage=f"direct/{what}",
                model=client.model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                usd=usage.usd,
                at=_now(),
            )
        )

    try:
        # ------------------- Pass 1: outline -------------------------------
        _progress(0, 1, "đọc toàn script, chia chương")
        outline = _pass1_outline(client, words, brief, channel, track, record)

        # Đoạn NGẮN (hook/end): gộp về 1 chương — xem NGUONG_MOT_CHUONG_GIAY.
        thoi_luong = float(getattr(words[-1], "end", 0) or 0) if words else 0.0
        if (gop_chuong_ngan and thoi_luong
                and thoi_luong < NGUONG_MOT_CHUONG_GIAY and len(outline.chapters) > 1):
            cu = len(outline.chapters)
            outline = _gop_mot_chuong(outline, words)
            record.warnings.append(
                f"voice {thoi_luong:.0f}s < {NGUONG_MOT_CHUONG_GIAY:.0f}s — gộp "
                f"{cu} chương về 1 (đỡ {cu - 1} lượt gọi LLM, tránh tempo phẳng)"
            )

        # ------------------- Pass 2: beats từng chương ---------------------
        outline_json = outline.model_dump_json(indent=1)
        # TOÀN VĂN script làm ngữ cảnh CACHE cho mọi chương (cơ chế lõi học từ PyLLM):
        # model quyết keyword/footage khi đã đọc CẢ video -> câu ẩn dụ/dẫn dắt hiểu đúng
        # chủ thể thật. Khối giống nhau mọi chương -> cache ghi 1 lần, đọc lại ~0.1x giá.
        script_context = prompts.full_script_context(words)
        all_drafts: list[tuple[int, BeatDraft]] = []  # (chapter_id, draft)
        prev_summary: str | None = None
        hook_id = outline.chapters[0].chapter_id
        n_ch = len(outline.chapters)
        for ci, ch in enumerate(outline.chapters, start=1):
            title = (ch.title or f"chương {ch.chapter_id}")[:40]
            _progress(ci, n_ch, f"chia beat: {title}")
            drafts = _pass2_chapter(
                client, words, outline_json, ch.chapter_id, ch.start_word, ch.end_word,
                prev_summary, brief, channel, track, record,
                is_hook=(ch.chapter_id == hook_id),
                central_subject=ch.central_subject, script_context=script_context,
                library_context=library_context,
            )
            all_drafts.extend((ch.chapter_id, d) for d in drafts)
            last = drafts[-1]
            prev_summary = (
                f'text: "{_text_of(words, last.start_word, last.end_word)}" | '
                f"concept: {last.visual_concept} | shot_size: {last.shot_size}"
            )
    except Exception as exc:
        record.status = StageStatus.FAILED
        record.error = str(exc)
        project.cost_total_usd = round(sum(c.usd for c in project.cost_log), 6)
        project.save()
        raise

    # ------------------- Hậu xử lý (code thuần) ----------------------------
    beats = drafts_to_beats(all_drafts, words)
    hook_chapter = outline.chapters[0].chapter_id if outline.chapters else None
    beats, post_notes = finalize_beats(beats, words, hook_chapter)
    record.warnings.extend(post_notes)

    project.beats = beats
    project.outline = outline.model_dump(mode="json")
    # TEMPO MAP: cùng lưới cảnh báo nhịp với direct-ingest (warning-only)
    record.warnings.extend(validator.check_tempo_map(project.outline, beats))
    project.cost_total_usd = round(sum(c.usd for c in project.cost_log), 6)
    record.status = StageStatus.DONE
    record.completed_at = _now()
    project.save()

    write_beats_review(project)
    return project


# ----------------------------------------------------------------------------
# Hậu xử lý DÙNG CHUNG cho 2 đường direct: LLM subprocess (run_direct) và
# phiên sống L2b sâu (direct-ingest, xem director/live.py). Sửa logic ở đây = sửa cả 2.
def drafts_to_beats(all_drafts: list[tuple[int, BeatDraft]], words) -> list[Beat]:
    """(chapter_id, BeatDraft) -> Beat: timestamp DUY NHẤT từ transcript (NT4)."""
    beats: list[Beat] = []
    for beat_id, (chapter_id, d) in enumerate(all_drafts):
        start, end = validator.compute_beat_times(d.start_word, d.end_word, words)
        beats.append(
            Beat(
                beat_id=beat_id,
                chapter=chapter_id,
                text=_text_of(words, d.start_word, d.end_word),
                start_word=d.start_word,
                end_word=d.end_word,
                start=start,
                end=end,
                energy=d.energy,
                mood=d.mood,
                sourcing_route=d.sourcing_route,
                visual_anchor=d.visual_anchor,
                visual_level=d.visual_level,
                visual_concept=d.visual_concept,
                shot_size=d.shot_size,
                search_queries=d.search_queries.model_dump(),
                entity_queries=d.entity_queries,
                breathing_after=d.breathing_after_sec,
                rhetorical_pause=getattr(d, "rhetorical_pause", False),
                shot_count=d.shot_count,
                overlays=[
                    resolve_overlay(o.text, o.kind, o.anchor_word, o.duration_sec)
                    for o in d.overlays
                ],
                graphic_spec=_resolve_graphic_spec(d.graphic_spec),
                text_sequence=_resolve_text_sequence(d.text_sequence),
                info_card=_resolve_info_card(d.info_card),
            )
        )
    return beats


def finalize_beats(beats: list[Beat], words, hook_chapter) -> tuple[list[Beat], list[str]]:
    """Gộp beat ngắn + bỏ thở sai chỗ + các warning chất lượng. Trả (beats, notes)."""
    notes: list[str] = []
    beats, merge_notes = validator.merge_short_beats(beats, words)
    notes.extend(merge_notes)
    # Bỏ hình thở rơi vào chỗ nói liền mạch (cắt đôi cụm từ — bug 13/06)
    beats, breath_notes = validator.enforce_breathing_pauses(beats, words)
    notes.extend(breath_notes)
    notes.extend(validator.check_graphic_ratio(beats))
    notes.extend(validator.check_consecutive_shot_size(beats))
    notes.extend(validator.check_breathing_rhythm(beats, hook_chapter))
    notes.extend(validator.check_overlay_density(beats))
    notes.extend(validator.check_boundary_interpolated(beats, words))
    return beats, notes


# ----------------------------------------------------------------------------
def _pass1_outline(client, words, brief, channel, track, record) -> Outline:
    system = prompts.outline_system(brief, channel)
    user = prompts.outline_user(words)
    outline, usage = client.complete(system, user, Outline)
    track(usage, "outline")

    errors = validator.check_coverage(
        [(c.start_word, c.end_word) for c in outline.chapters], 0, len(words) - 1
    )
    if errors:
        feedback = "Chapter word ranges are invalid:\n- " + "\n- ".join(errors)
        outline, usage = client.complete(system, user + "\n\n" + _retry_block(feedback), Outline)
        track(usage, "outline_retry")
        errors = validator.check_coverage(
            [(c.start_word, c.end_word) for c in outline.chapters], 0, len(words) - 1
        )
        if errors:
            raise RuntimeError(
                "Outline vẫn lỗi coverage sau retry: " + "; ".join(errors)
            )
    return outline


def _pass2_chapter(
    client, words, outline_json, chapter_id, lo, hi,
    prev_summary, brief, channel, track, record,
    is_hook: bool = False,
    central_subject: str | None = None,
    script_context: str | None = None,
    library_context: str | None = None,
) -> list[BeatDraft]:
    system = prompts.beats_system(brief, channel, library_context)

    def ask(feedback: str | None) -> ChapterBeats:
        user = prompts.beats_user(
            words, outline_json, chapter_id, lo, hi, prev_summary, feedback,
            central_subject=central_subject,
        )
        # Video dài gọi LLM nhiều lần -> dễ trúng lỗi tạm thời (overload/mạng/JSON lệch).
        # Retry vài lần để 1 hiccup KHÔNG giết cả stage direct (phải dựng lại từ đầu).
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                result, usage = client.complete(system, user, ChapterBeats, context=script_context)
                track(usage, f"beats_ch{chapter_id}" + ("_retry" if feedback else ""))
                return result
            except Exception as exc:
                last_exc = exc
                record.warnings.append(
                    f"chương {chapter_id}: gọi LLM lỗi lần {attempt + 1}/3 ({exc}) — thử lại"
                )
                time.sleep(2 ** attempt)
        raise last_exc  # hết 3 lần vẫn lỗi -> để stage fail rõ ràng

    result = ask(None)
    errors = beat_errors(result.beats, lo, hi, words, is_hook)
    if errors:
        result2 = ask("- " + "\n- ".join(errors))
        errors2 = beat_errors(result2.beats, lo, hi, words, is_hook)
        if not errors2:
            beats, clip_notes = validator.enforce_chapter_visual_limits(result2.beats)
            record.warnings.extend(clip_notes)
            return beats
        # vẫn lỗi sau retry: nhận bản ít lỗi hơn + warning (phương án đã chốt)
        best, best_errors = (
            (result2.beats, errors2) if len(errors2) < len(errors) else (result.beats, errors)
        )
        record.warnings.append(
            f"chương {chapter_id}: beats còn lỗi sau retry — " + "; ".join(best_errors)
        )
        beats, clip_notes = validator.enforce_chapter_visual_limits(best)
        record.warnings.extend(clip_notes)
        return beats
    beats, clip_notes = validator.enforce_chapter_visual_limits(result.beats)
    record.warnings.extend(clip_notes)
    return beats


def beat_errors(drafts: list[BeatDraft], lo: int, hi: int, words, is_hook: bool = False) -> list[str]:
    errors = validator.check_coverage([(d.start_word, d.end_word) for d in drafts], lo, hi)
    if not errors:  # chỉ check duration khi index hợp lệ
        errors = validator.find_long_beats(
            [(d.start_word, d.end_word) for d in drafts], words
        )
    errors.extend(validator.check_v2_rules(drafts))
    errors.extend(validator.check_chapter_breathing(drafts, is_hook))
    errors.extend(validator.check_overlays(drafts))
    errors.extend(validator.check_graphic_specs(drafts))
    errors.extend(validator.check_text_sequences(drafts))
    errors.extend(validator.check_info_cards(drafts))
    return errors


def _retry_block(feedback: str) -> str:
    return "YOUR PREVIOUS ATTEMPT HAD ERRORS — fix ALL of them this time:\n" + feedback


def _text_of(words, lo: int, hi: int) -> str:
    return " ".join(w.text for w in words[lo : hi + 1])


def _resolve_graphic_spec(draft):
    """GraphicSpecDraft -> GraphicSpec (giữ layout LLM chọn: full/half)."""
    if draft is None:
        return None
    from autoedit.project import ChartDatum, GraphicSpec

    return GraphicSpec(
        chart_type=draft.chart_type, title=draft.title, unit=draft.unit, layout=draft.layout,
        data=[ChartDatum(label=d.label, value=d.value) for d in draft.data],
        source_note=draft.source_note,
        x_label=draft.x_label, y_label=draft.y_label,
    )


def _resolve_info_card(draft):
    """DirectInfoCardDraft -> InfoCard (approved=True vì từ director, không phải enrich)."""
    if draft is None:
        return None
    from autoedit.project import InfoCard
    return InfoCard(
        title=draft.title,
        bullets=draft.bullets,
        source_note=draft.source_note,
        approved=True,
    )


def _resolve_text_sequence(draft):
    """TextSequenceDraft -> TextSequence (code điền phần hình: nền plate mặc định)."""
    if draft is None:
        return None
    from autoedit.project import TextPhrase, TextSequence

    return TextSequence(
        phrases=[TextPhrase(text=p.text, anchor_word=p.anchor_word) for p in draft.phrases],
        background="footage",  # chỉ viền đen outline (như overlay thường) — sạch, không khối đen
    )


# ----------------------------------------------------------------------------
def write_beats_review(project: Project) -> None:
    """beats.json — bản dễ đọc cho người review bằng mắt (bài kiểm tra M3)."""
    data = {
        "project": project.project_id,
        "cost_total_usd": project.cost_total_usd,
        "outline": project.outline,
        "warnings": project.stages[Stage.DIRECT].warnings,
        "beats": [
            {
                "beat_id": b.beat_id,
                "chapter": b.chapter,
                "time": f"{b.start:.2f}s -> {b.end:.2f}s ({b.end - b.start:.1f}s)",
                "text": b.text,
                "energy": b.energy,
                "mood": b.mood,
                "sourcing_route": b.sourcing_route,
                "visual_anchor": b.visual_anchor,
                "visual_level": b.visual_level,
                "visual_concept": b.visual_concept,
                "shot_size": b.shot_size,
                "search_queries": b.search_queries.model_dump(),
                "entity_queries": b.entity_queries,
                "breathing_after": b.breathing_after,
                "shot_count": b.shot_count,
                "overlays": [
                    f"{o.text!r} [{o.kind}] @từ {o.anchor_word} ({o.anim}/{o.sfx_kind})"
                    for o in b.overlays
                ],
                "graphic_spec": (
                    f"{b.graphic_spec.chart_type} '{b.graphic_spec.title}': "
                    + ", ".join(f"{d.label}={d.value}{b.graphic_spec.unit}" for d in b.graphic_spec.data)
                    if b.graphic_spec else None
                ),
                "text_sequence": (
                    " | ".join(f"@{p.anchor_word} {p.text!r}" for p in b.text_sequence.phrases)
                    if b.text_sequence else None
                ),
                "info_card": (
                    f"{b.info_card.title!r}: " + " / ".join(b.info_card.bullets)
                    if b.info_card else None
                ),
            }
            for b in project.beats
        ],
    }
    (Path(project.project_dir) / "beats.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
