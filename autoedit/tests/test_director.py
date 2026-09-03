"""Test Stage 2 Direct (M3) — validator thuần + runner với client giả (không API)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from autoedit.director.client import Usage
from autoedit.director.runner import run_direct
from autoedit.director.schema import (
    BeatDraft,
    ChapterBeats,
    ChapterPlan,
    Outline,
    SearchQueriesDraft,
)
from autoedit.director import validator
from autoedit.project import Beat, Stage, StageStatus, Word, create_project


def _words(texts_with_times: list[tuple[str, float, float]]) -> list[Word]:
    return [Word(text=t, start=s, end=e) for t, s, e in texts_with_times]


# 12 từ, mỗi từ 0.5s — tổng 6s
WORDS = _words([(f"w{i}", i * 0.5, i * 0.5 + 0.5) for i in range(12)])


# ============================= validator =====================================
def test_coverage_ok():
    assert validator.check_coverage([(0, 4), (5, 8), (9, 11)], 0, 11) == []


def test_coverage_detects_gap_overlap_bounds():
    assert any("gap" in e for e in validator.check_coverage([(0, 4), (6, 11)], 0, 11))
    assert any("overlap" in e for e in validator.check_coverage([(0, 5), (4, 11)], 0, 11))
    assert any("must start" in e for e in validator.check_coverage([(1, 11)], 0, 11))
    assert any("must end" in e for e in validator.check_coverage([(0, 10)], 0, 11))


def test_compute_beat_times_from_transcript():
    assert validator.compute_beat_times(2, 5, WORDS) == (1.0, 3.0)
    with pytest.raises(ValueError, match="ngoài transcript"):
        validator.compute_beat_times(0, 99, WORDS)


def test_find_long_beats():
    issues = validator.find_long_beats([(0, 11)], WORDS, max_sec=5.0)  # 6s > 5s
    assert len(issues) == 1 and "split" in issues[0]
    assert validator.find_long_beats([(0, 5)], WORDS, max_sec=5.0) == []


def _beat(beat_id, chapter, sw, ew, shot_size="medium") -> Beat:
    s, e = validator.compute_beat_times(sw, ew, WORDS)
    return Beat(
        beat_id=beat_id, chapter=chapter, text="x", start_word=sw, end_word=ew,
        start=s, end=e, energy="medium", mood="m", visual_level="literal",
        visual_concept="c", shot_size=shot_size, search_queries=["q"],
    )


def test_merge_short_beats_into_previous():
    beats = [_beat(0, 1, 0, 7), _beat(1, 1, 8, 9)]  # beat 1 = 1.0s < 1.5s
    merged, notes = validator.merge_short_beats(beats, WORDS)
    assert len(merged) == 1
    assert merged[0].end_word == 9 and merged[0].end == 5.0
    assert merged[0].beat_id == 0
    assert any("into previous" in n for n in notes)


def test_merge_short_beat_not_across_chapters():
    beats = [_beat(0, 1, 0, 7), _beat(1, 2, 8, 9)]  # khác chương -> không merge
    merged, notes = validator.merge_short_beats(beats, WORDS)
    assert len(merged) == 2
    assert any("alone in chapter" in n for n in notes)


def test_merge_short_beats_keeps_overlays_and_breathing():
    """Rà chồng chéo 2026-07-04 #3: merge vứt overlay của beat ngắn + gộp-vào-sau
    rơi hình thở — quyết định đạo diễn mất không dấu vết."""
    from autoedit.project import Overlay

    ov_host = Overlay(text="$400", kind="price", anchor_word=2)
    ov_short = Overlay(text="$1M", kind="price", anchor_word=9)
    # chiều gộp-vào-TRƯỚC: overlay của beat ngắn phải theo sang beat gộp
    beats = [
        _beat(0, 1, 0, 7).model_copy(update={"overlays": [ov_host]}),
        _beat(1, 1, 8, 9).model_copy(update={"overlays": [ov_short]}),  # 1.0s < 1.5s
    ]
    merged, _ = validator.merge_short_beats(beats, WORDS)
    assert len(merged) == 1
    assert [o.text for o in merged[0].overlays] == ["$400", "$1M"]
    # anchor vẫn nằm trong range gộp (assembler canh giờ theo word index)
    assert all(merged[0].start_word <= o.anchor_word <= merged[0].end_word
               for o in merged[0].overlays)

    # chiều gộp-vào-SAU (beat ngắn ĐẦU chương): overlay + hình thở phải giữ max
    ov_first = Overlay(text="One.", kind="keyword", anchor_word=0)
    beats = [
        _beat(0, 1, 0, 1).model_copy(  # 1.0s < 1.5s, mang thở 2s
            update={"overlays": [ov_first], "breathing_after": 2.0}),
        _beat(1, 1, 2, 9),
    ]
    merged, _ = validator.merge_short_beats(beats, WORDS)
    assert len(merged) == 1
    assert [o.text for o in merged[0].overlays] == ["One."]
    assert merged[0].breathing_after == 2.0  # trước fix: rơi mất về 0.0


def test_consecutive_shot_size_warning():
    beats = [_beat(i, 1, i, i, "close_up") for i in range(3)]
    assert len(validator.check_consecutive_shot_size(beats)) == 1
    beats[1] = _beat(1, 1, 1, 1, "wide")
    assert validator.check_consecutive_shot_size(beats) == []


def test_boundary_interpolated_warning():
    words = [w.model_copy() for w in WORDS]
    words[5] = words[5].model_copy(update={"interpolated": True})
    beats = [_beat(0, 1, 0, 5)]
    warnings = validator.check_boundary_interpolated(beats, words)
    assert len(warnings) == 1 and "nội suy" in warnings[0]


# ============================= v2 rules (P1, P5) =============================
def test_v2_query_max_4_words():
    bad = _draft(0, 5, search_queries=_queries(specific=["luxury gold card velvet surface spotlight"]))
    errors = validator.check_v2_rules([bad])
    assert len(errors) == 1 and "maximum is 4" in errors[0]
    assert validator.check_v2_rules([_draft(0, 5)]) == []


def test_v2_local_query_word_cap_c4():
    """C4: tier local gác chung luật ≤4 từ; local rỗng (mặc định draft cũ) hợp lệ."""
    bad = _draft(0, 5, search_queries=SearchQueriesDraft(
        specific=["man walking street"], broad=["city walk"], thematic=["urban life"],
        local=["spiral galaxy deep space nebula"]))
    errors = validator.check_v2_rules([bad])
    assert len(errors) == 1 and "(local)" in errors[0] and "maximum is 4" in errors[0]
    ok = _draft(0, 5, search_queries=SearchQueriesDraft(
        specific=["man walking street"], broad=["city walk"], thematic=["urban life"],
        local=["spiral galaxy"]))
    assert validator.check_v2_rules([ok]) == []


def test_v2_entity_requires_entity_queries():
    bad = _draft(0, 5, sourcing_route="entity", entity_queries=[])
    assert any("entity_queries is empty" in e for e in validator.check_v2_rules([bad]))
    ok = _draft(0, 5, sourcing_route="entity",
                entity_queries=["trump gold card announcement"])
    assert validator.check_v2_rules([ok]) == []


def test_v2_entity_queries_only_for_entity_route():
    bad = _draft(0, 5, sourcing_route="stock", entity_queries=["trump gold card"])
    assert any("only for route entity" in e for e in validator.check_v2_rules([bad]))


def test_v2_graphic_route_no_stock_queries():
    bad = _draft(0, 5, sourcing_route="graphic")
    assert any("graphic" in e for e in validator.check_v2_rules([bad]))
    ok = _draft(0, 5, sourcing_route="graphic",
                search_queries=SearchQueriesDraft(specific=[], broad=[], thematic=[]))
    assert validator.check_v2_rules([ok]) == []


def test_v2_graphic_route_allows_thematic_background():
    """Graphic được kèm nền generic ở tier thematic (chốt với user 11/06)."""
    ok = _draft(0, 5, sourcing_route="graphic",
                search_queries=SearchQueriesDraft(
                    specific=[], broad=[], thematic=["dark texture background"]))
    assert validator.check_v2_rules([ok]) == []


def test_graphic_spec_validator():
    from autoedit.director.schema import ChartDatumDraft, GraphicSpecDraft

    def draft_with(gs, route="graphic"):
        return _draft(0, 5).model_copy(update={"graphic_spec": gs, "sourcing_route": route})

    good = GraphicSpecDraft(chart_type="bar", title="x", data=[
        ChartDatumDraft(label="VN", value=400), ChartDatumDraft(label="Mỹ", value=2500)])
    assert validator.check_graphic_specs([draft_with(good)]) == []
    # <2 điểm dữ liệu -> lỗi
    one = GraphicSpecDraft(chart_type="bar", title="x", data=[ChartDatumDraft(label="VN", value=400)])
    assert any("≥2 điểm" in e for e in validator.check_graphic_specs([draft_with(one)]))
    # có chart nhưng route != graphic -> lỗi
    assert any("route=" in e for e in validator.check_graphic_specs([draft_with(good, route="stock")]))


def test_enforce_breathing_pauses_drops_mid_phrase():
    """Bug 13/06: hình thở chỗ nói liền mạch (gap~0) phải bị bỏ."""
    words = [
        Word(text="không", start=0.0, end=0.5),
        Word(text="ngừng", start=0.5, end=1.0),
        Word(text="tăng.", start=1.0, end=1.5),    # gap 0.0 sau 'ngừng' -> giữa cụm
        Word(text="Vậy", start=2.2, end=2.6),       # gap 0.7 sau 'tăng.' -> nghỉ thật
        Word(text="điều", start=2.6, end=3.0),
    ]
    mid_phrase = _beat(0, 1, 0, 1).model_copy(update={"breathing_after": 3.0})  # end 'ngừng'
    natural = _beat(1, 1, 2, 2).model_copy(update={"breathing_after": 3.0})     # end 'tăng.'
    out, notes = validator.enforce_breathing_pauses([mid_phrase, natural], words)
    assert out[0].breathing_after == 0.0  # bỏ vì giữa cụm
    assert out[1].breathing_after == 3.0  # giữ vì có nghỉ 0.7s
    assert any("cắt đôi cụm" in n for n in notes)


def test_graphic_ratio_warning():
    """27s thoại: 2 graphic -> cảnh báo, 1 graphic -> không."""
    def beat_with_route(i, route):
        b = _beat(i, 1, i, i + 1)
        return b.model_copy(update={"sourcing_route": route})

    two_graphic = [beat_with_route(0, "graphic"), beat_with_route(2, "graphic"),
                   beat_with_route(4, "stock")]  # ~3s thoại, ngưỡng 1
    assert len(validator.check_graphic_ratio(two_graphic)) == 1
    one_graphic = [beat_with_route(0, "graphic"), beat_with_route(2, "stock")]
    assert validator.check_graphic_ratio(one_graphic) == []
    assert validator.check_graphic_ratio([]) == []


def test_v2_breathing_range():
    bad = _draft(0, 5)
    bad = bad.model_copy(update={"breathing_after_sec": 9.0})
    assert any("out of range" in e for e in validator.check_v2_rules([bad]))
    ok = bad.model_copy(update={"breathing_after_sec": 2.0})
    assert validator.check_v2_rules([ok]) == []


def test_v2_breathing_rejects_gap_below_min():
    """Rà chồng chéo 2026-07-04 #4: thông báo nói '0 hoặc 1.5-6' nhưng code cũ
    cho 0.8s lọt qua — im lơ lửng dưới ngưỡng ducking, nhạc không nở."""
    base = _draft(0, 5)
    gap = base.model_copy(update={"breathing_after_sec": 0.8})
    assert any("out of range" in e for e in validator.check_v2_rules([gap]))
    # biên hợp lệ: 0 (không thở), đúng sàn 1.5, đúng trần 6.0
    for sec in (0.0, 1.5, 6.0):
        ok = base.model_copy(update={"breathing_after_sec": sec})
        assert validator.check_v2_rules([ok]) == []


def test_overlay_resolve_style_from_kind():
    from autoedit.overlay.style import resolve_overlay
    ov = resolve_overlay("$2", "price", 3)
    assert ov.position == "lower_third" and ov.anim == "pop" and ov.sfx_kind == "cash"
    kw = resolve_overlay("FREE", "keyword", 5)
    assert kw.position == "center" and kw.sfx_kind == "impact" and kw.size == 24.0


def test_overlay_validator_anchor_and_length():
    from autoedit.director.schema import OverlayDraft

    def draft_with(ov):
        d = _draft(0, 5)
        return d.model_copy(update={"overlays": [ov]})

    out_of_range = draft_with(OverlayDraft(text="$2", kind="price", anchor_word=99))
    assert any("ngoài beat" in e for e in validator.check_overlays([out_of_range]))
    too_long = draft_with(OverlayDraft(text="x" * 30, kind="stat", anchor_word=3))
    assert any("dài" in e for e in validator.check_overlays([too_long]))
    ok = draft_with(OverlayDraft(text="$2", kind="price", anchor_word=3))
    assert validator.check_overlays([ok]) == []
    # typing kind (place) cho phép tới 24 ký tự
    long_place = draft_with(OverlayDraft(text="x" * 23, kind="place", anchor_word=3))
    assert validator.check_overlays([long_place]) == []


def test_text_sequence_validator():
    from autoedit.director.schema import TextPhraseDraft, TextSequenceDraft

    def draft_with(phrases):
        d = _draft(0, 5)
        return d.model_copy(update={
            "text_sequence": TextSequenceDraft(
                phrases=[TextPhraseDraft(text=t, anchor_word=a) for t, a in phrases])
        })

    ok = draft_with([("Việt Nam", 0), ("rẻ nhất", 3)])
    assert validator.check_text_sequences([ok]) == []
    # cụm đầu không ở đầu beat
    bad_start = draft_with([("Nam", 1), ("rẻ", 3)])
    assert any("đầu beat" in e for e in validator.check_text_sequences([bad_start]))
    # anchor không tăng
    not_inc = draft_with([("a", 0), ("b", 0)])
    assert any("TĂNG" in e for e in validator.check_text_sequences([not_inc]))
    # chỉ 1 cụm
    one = draft_with([("a", 0)])
    assert any("2-4 cụm" in e for e in validator.check_text_sequences([one]))


def test_overlay_density_warning():
    b = [_beat(i, 1, i, i + 1) for i in range(3)]
    b = [x.model_copy(update={"start": float(i), "end": float(i) + 1}) for i, x in enumerate(b)]
    from autoedit.overlay.style import resolve_overlay
    b[0] = b[0].model_copy(update={"overlays": [resolve_overlay("a", "stat", 0)]})
    assert validator.check_overlay_density(b) == []  # 1 overlay/~3s ok
    many = [resolve_overlay(str(i), "stat", 0) for i in range(5)]
    b[1] = b[1].model_copy(update={"overlays": many})
    assert any("lạm dụng" in w for w in validator.check_overlay_density(b))


def test_chapter_breathing_errors():
    # 2 hình thở liên tiếp -> lỗi retry
    d1 = _draft(0, 2).model_copy(update={"breathing_after_sec": 2.0})
    d2 = _draft(3, 5).model_copy(update={"breathing_after_sec": 2.0})
    assert any("two" in e for e in validator.check_chapter_breathing([d1, d2], is_hook=False))
    # hook không có hình thở -> lỗi retry
    clean = [_draft(0, 2), _draft(3, 5)]
    assert any("HOOK" in e for e in validator.check_chapter_breathing(clean, is_hook=True))
    assert validator.check_chapter_breathing(clean, is_hook=False) == []


def test_breathing_rhythm_warnings():
    def b(i, ch, s, e, br=0.0):
        x = _beat(i, ch, min(s, 11), min(e, 11))
        return x.model_copy(update={"breathing_after": br, "start": float(s), "end": float(e)})

    # hook không hình thở -> cảnh báo
    beats = [b(0, 1, 0, 5), b(1, 1, 5, 10), b(2, 2, 10, 20, br=3.0)]
    assert any("hook" in w for w in validator.check_breathing_rhythm(beats, hook_chapter=1))
    # hook có hình thở + thưa -> sạch
    beats = [b(0, 1, 0, 5, br=2.0), b(1, 1, 5, 10), b(2, 2, 10, 40, br=3.0)]
    assert validator.check_breathing_rhythm(beats, hook_chapter=1) == []
    # 2 hình thở liên tiếp -> lạm dụng
    beats = [b(0, 1, 0, 5, br=2.0), b(1, 1, 5, 30, br=2.0), b(2, 1, 30, 35)]
    assert any("liên tiếp" in w for w in validator.check_breathing_rhythm(beats, hook_chapter=None))
    # 2 hình thở cách <15s -> cảnh báo
    beats = [b(0, 1, 0, 5, br=2.0), b(1, 1, 5, 10), b(2, 1, 10, 12, br=2.0), b(3, 1, 12, 14)]
    assert any("<15s" in w for w in validator.check_breathing_rhythm(beats, hook_chapter=None))


def test_legacy_beat_search_queries_coerced():
    """project.json schema cũ (list phẳng) vẫn load được — resume không vỡ."""
    b = _beat(0, 1, 0, 5)  # helper dùng search_queries=["q"] dạng cũ
    assert b.search_queries.specific == ["q"]
    assert b.sourcing_route == "stock" and b.visual_anchor is True


# ============================= runner ========================================
SCRIPT_12 = " ".join(f"w{i}" for i in range(12))

GOOD_OUTLINE = Outline(
    tone="serious",
    motifs=["clock"],
    chapters=[
        ChapterPlan(chapter_id=1, title="Hook", start_word=0, end_word=5,
                    mood="urgent", energy="high", music_hint="tense", summary="s1",
                    central_subject="thing one"),
        ChapterPlan(chapter_id=2, title="Body", start_word=6, end_word=11,
                    mood="warm", energy="medium", music_hint="calm", summary="s2",
                    central_subject="thing two"),
    ],
)


def _queries(**kw) -> SearchQueriesDraft:
    return SearchQueriesDraft(
        specific=kw.get("specific", ["man walking street"]),
        broad=kw.get("broad", ["city walk"]),
        thematic=kw.get("thematic", ["urban life"]),
    )


def _draft(s: int, e: int, i: int = 0, **kw) -> BeatDraft:
    return BeatDraft(
        start_word=s, end_word=e, energy="medium", mood="warm",
        sourcing_route=kw.get("sourcing_route", "stock"),
        visual_anchor=kw.get("visual_anchor", True),
        visual_level="literal", visual_concept="man walking on street",
        shot_size="medium" if i % 2 == 0 else "wide",
        search_queries=kw.get("search_queries", _queries()),
        entity_queries=kw.get("entity_queries", []),
    )


def _drafts(*ranges: tuple[int, int]) -> ChapterBeats:
    """Beats hợp lệ cho 1 chương: beat cuối mang hình thở 2s (thỏa luật hook + nhịp)."""
    beats = [_draft(s, e, i) for i, (s, e) in enumerate(ranges)]
    beats[-1] = beats[-1].model_copy(update={"breathing_after_sec": 2.0})
    return ChapterBeats(beats=beats)


class FakeClient:
    """Client giả: trả kịch bản định sẵn theo thứ tự gọi, đếm số lần gọi."""

    model = "fake-model"

    def __init__(self, responses: list[BaseModel]):
        self._responses = list(responses)
        self.calls: list[str] = []

    def complete(self, system: str, user: str, output_model: type,
                 context: str | None = None) -> tuple[BaseModel, Usage]:
        self.calls.append(output_model.__name__)
        self.contexts = getattr(self, "contexts", [])
        self.contexts.append(context)
        self.systems = getattr(self, "systems", [])
        self.systems.append(system)
        out = self._responses.pop(0)
        assert isinstance(out, output_model), f"kịch bản sai thứ tự: {type(out)}"
        return out, Usage(input_tokens=1000, output_tokens=500)


@pytest.fixture
def project(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text(SCRIPT_12, encoding="utf-8")
    voice = tmp_path / "voice.mp3"
    voice.write_bytes(b"fake")
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    p.transcript = WORDS
    p.stages[Stage.ALIGN].status = StageStatus.DONE
    p.save()
    return p


def test_run_direct_happy_path(project):
    client = FakeClient([GOOD_OUTLINE, _drafts((0, 2), (3, 5)), _drafts((6, 8), (9, 11))])
    # transcript giả chỉ 6 giây -> sẽ bị gộp về 1 chương; test này kiểm
    # tra luồng NHIỀU chương nên tắt gộp (xem NGUONG_MOT_CHUONG_GIAY).
    run_direct(project, client, gop_chuong_ngan=False)

    from autoedit.project import Project

    saved = Project.load(project.project_dir)
    assert saved.stages[Stage.DIRECT].status == StageStatus.DONE
    assert len(saved.beats) == 4
    # timestamp tính từ transcript, không phải từ LLM
    assert saved.beats[0].start == 0.0 and saved.beats[0].end == 1.5
    assert saved.beats[3].end == 6.0
    assert saved.beats[0].text == "w0 w1 w2"
    assert [b.chapter for b in saved.beats] == [1, 1, 2, 2]
    # cost: 3 lần gọi x (1000 in + 500 out)
    assert len(saved.cost_log) == 3
    assert saved.cost_total_usd > 0
    assert saved.outline["chapters"][0]["title"] == "Hook"
    # beats.json cho người review
    review = json.loads((Path(project.project_dir) / "beats.json").read_text())
    assert len(review["beats"]) == 4


def test_pass2_receives_full_script_context_cached(project):
    """Cơ chế lõi (học từ PyLLM): pass beat phải thấy TOÀN VĂN script làm ngữ cảnh,
    còn pass outline thì KHÔNG (nó tự đọc full trong user). Khối context giống nhau giữa
    các chương -> cùng prefix -> cache đọc lại rẻ."""
    client = FakeClient([GOOD_OUTLINE, _drafts((0, 2), (3, 5)), _drafts((6, 8), (9, 11))])
    run_direct(project, client)

    # contexts[0] = outline (None); contexts[1..2] = 2 chương (đều có full script)
    assert client.contexts[0] is None
    assert client.contexts[1] and client.contexts[2]
    # toàn văn -> chứa cả từ đầu (w0) lẫn từ cuối (w11), giống nhau giữa các chương
    for ctx in client.contexts[1:]:
        assert "[0]w0" in ctx and "[11]w11" in ctx
    assert client.contexts[1] == client.contexts[2]  # ổn định -> cache hit


def test_run_direct_retries_bad_chapter_beats(project):
    bad = _drafts((0, 2), (4, 5))  # gap: thiếu từ 3
    client = FakeClient([
        GOOD_OUTLINE,
        bad, _drafts((0, 2), (3, 5)),          # chương 1: lỗi rồi sửa
        _drafts((6, 8), (9, 11)),               # chương 2: sạch
    ])
    # transcript giả chỉ 6 giây -> sẽ bị gộp về 1 chương; test này kiểm
    # tra luồng NHIỀU chương nên tắt gộp (xem NGUONG_MOT_CHUONG_GIAY).
    run_direct(project, client, gop_chuong_ngan=False)
    assert client.calls == ["Outline", "ChapterBeats", "ChapterBeats", "ChapterBeats"]

    from autoedit.project import Project

    saved = Project.load(project.project_dir)
    assert saved.stages[Stage.DIRECT].status == StageStatus.DONE
    assert len(saved.beats) == 4
    # retry thành công -> không có warning coverage
    assert not any("còn lỗi" in w for w in saved.stages[Stage.DIRECT].warnings)


def test_run_direct_keeps_best_after_failed_retry(project):
    bad = _drafts((0, 2), (4, 5))
    client = FakeClient([GOOD_OUTLINE, bad, bad, _drafts((6, 8), (9, 11))])
    run_direct(project, client)

    from autoedit.project import Project

    saved = Project.load(project.project_dir)
    assert saved.stages[Stage.DIRECT].status == StageStatus.DONE
    assert any("còn lỗi" in w for w in saved.stages[Stage.DIRECT].warnings)


def test_run_direct_requires_align(project):
    project.stages[Stage.ALIGN].status = StageStatus.PENDING
    project.save()
    with pytest.raises(RuntimeError, match="align"):
        run_direct(project, FakeClient([]))


def test_run_direct_outline_failure_marks_stage_failed(project):
    bad_outline = GOOD_OUTLINE.model_copy(
        update={"chapters": [GOOD_OUTLINE.chapters[0]]}  # không phủ kín 12 từ
    )
    client = FakeClient([bad_outline, bad_outline])  # lỗi cả retry
    with pytest.raises(RuntimeError, match="coverage"):
        run_direct(project, client)

    from autoedit.project import Project

    saved = Project.load(project.project_dir)
    assert saved.stages[Stage.DIRECT].status == StageStatus.FAILED
    assert saved.cost_log  # tiền đã tốn vẫn được ghi lại


def test_beats_system_has_tone_rule_c4():
    """C4/b1: pass 2 phải mang luật mood-chạm-tone (giá trị tone nằm sẵn trong
    outline_json ngữ cảnh pass 2 — luật chỉ cần bảo NÃO dùng nó)."""
    from autoedit.director import prompts

    s = prompts.beats_system()
    assert "CONSTANT attitude" in s and "mood" in s


# ---------------- TEMPO MAP (2026-07-14) — check_tempo_map warning-only ----------------
def _tbeat(bid, ch, start, dur):
    """Beat với thời lượng đặt tay — check_tempo_map chỉ đọc chapter + start/end."""
    return Beat(beat_id=bid, chapter=ch, text="x", start_word=0, end_word=1,
                start=start, end=start + dur, energy="medium", mood="m",
                visual_level="literal", visual_concept="c", shot_size="medium")


def _tchapters(durs_by_ch: dict, curves: dict | None = None):
    """Trả (outline, beats) từ {chương: [độ dài beat...]}."""
    outline = {"chapters": [{"chapter_id": ch, "tempo_curve": (curves or {}).get(ch, "")}
                            for ch in sorted(durs_by_ch)]}
    beats, t, bid = [], 0.0, 0
    for ch in sorted(durs_by_ch):
        for d in durs_by_ch[ch]:
            beats.append(_tbeat(bid, ch, t, d)); t += d; bid += 1
    return outline, beats


def test_tempo_map_flat_and_deu_tam_tap():
    """Regression 'video đều đều' (feedback ĐDHA): mọi chương cùng trung vị + beat
    đều tăm tắp -> phải kêu cả ① phẳng giữa chương lẫn ② đều trong chương + chưa khai."""
    outline, beats = _tchapters({1: [3.0] * 6, 2: [3.0] * 6})
    warns = validator.check_tempo_map(outline, beats)
    assert any("tempo phẳng giữa chương" in w for w in warns)
    assert any("đều tăm tắp" in w for w in warns)
    assert any("chưa khai tempo_curve" in w for w in warns)


def test_tempo_map_song_that_im_lang():
    """Draft có sóng thật + khai đúng curve -> 0 warning (không warn-spam)."""
    outline, beats = _tchapters(
        {1: [2, 4, 2, 5, 3, 7], 2: [9, 8, 7, 6, 5, 4]},
        curves={1: "fast_settle", 2: "build"})
    assert validator.check_tempo_map(outline, beats) == []


def test_tempo_map_khai_vs_thuc():
    """③ khai 'build' nhưng beat DÀI dần về cuối -> phải kêu đúng chương."""
    outline, beats = _tchapters({1: [3, 3, 4, 4, 5, 6]}, curves={1: "build"})
    warns = validator.check_tempo_map(outline, beats)
    assert any("khai 'build'" in w and "chương 1" in w for w in warns)


def test_tempo_map_shuffle_3_lien_ke():
    """Shuffle chống đều: 3 chương liền kề cùng curve đã khai -> kêu."""
    outline, beats = _tchapters(
        {1: [2, 5, 3], 2: [4, 7, 5], 3: [3, 6, 9]},
        curves={1: "build", 2: "build", 3: "build"})
    warns = validator.check_tempo_map(outline, beats)
    assert any("3 chương liền kề" in w for w in warns)


def test_prompts_carry_ban_thuoc_rules():
    """Lỗi 'bán thuốc' (DS5-083 Jenga, user chốt 2026-07-13): pass 2 phải mang
    SCRIPT-SIDE METAPHOR RULE + direct-address; pass 1 cấm central_subject chứa
    thủ pháp tu từ; từ điển ẩn dụ bị khóa 2 qualifier (chỉ câu THƯỜNG + diễn in-world)."""
    from autoedit.director import prompts

    s2 = prompts.beats_system()
    assert "SCRIPT-SIDE METAPHOR RULE" in s2
    assert "Direct-address" in s2
    assert "NEVER illustrate the vehicle" in s2 or "do NOT illustrate its vehicle" in s2
    # từ điển ẩn dụ nằm trong _DIRECTOR_ROLE (cả 2 pass) — phải kèm 2 qualifier
    assert "ONLY for PLAIN lines" in s2
    s1 = prompts.outline_system()
    assert "central_subject must name the REAL subject ONLY" in s1
    assert "poisons every downstream" in s1  # phản-ví-dụ Jenga trong central_subject
    assert "ONLY for PLAIN lines" in s1


# ---------- GLM het tien + so tam giu tien do (su co 03/09) -------------------
def test_het_tien_bao_ngay_khong_thu_lai(monkeypatch):
    """z.ai tra HET TIEN duoi dang HTTP 429 (nhu qua tai) kem ma 1113. Cho bao lau
    cung vay — chi nap tien moi het. 03/09: nhan su chi thay 'GLM HTTP 429' roi tu
    chuyen sang lam tay, khong biet la het tien."""
    import urllib.error

    from autoedit.director.glm_client import GLMDirectorClient

    lan = {"n": 0}

    def gia_urlopen(req, timeout=None):
        # so_goi_nen.ghi() cũng gọi urlopen để ghi nhật ký — chỉ đếm lần gọi TỚI GLM
        if "/api/so-goi" in str(getattr(req, "full_url", req)):
            raise OSError("bo qua so ghi")
        lan["n"] += 1
        raise urllib.error.HTTPError(
            req.full_url, 429, "Too Many Requests", {},
            __import__("io").BytesIO(
                b'{"error":{"code":"1113","message":"Insufficient balance or no '
                b'resource package. Please recharge."}}'))

    monkeypatch.setattr("urllib.request.urlopen", gia_urlopen)
    c = GLMDirectorClient(api_key="k", retries=3)
    with pytest.raises(RuntimeError, match="HẾT TIỀN"):
        c._goi([{"role": "user", "content": "x"}])
    assert lan["n"] == 1, "hết tiền thì KHÔNG thử lại — chờ vô ích"


def test_429_qua_tai_van_thu_lai(monkeypatch):
    """Phân biệt với 429 THẬT (quá tải): cái đó chờ rồi gọi lại là qua."""
    import urllib.error

    from autoedit.director.glm_client import GLMDirectorClient

    lan = {"n": 0}

    def gia_urlopen(req, timeout=None):
        # so_goi_nen.ghi() cũng gọi urlopen để ghi nhật ký — chỉ đếm lần gọi TỚI GLM
        if "/api/so-goi" in str(getattr(req, "full_url", req)):
            raise OSError("bo qua so ghi")
        lan["n"] += 1
        raise urllib.error.HTTPError(
            req.full_url, 429, "Too Many Requests", {},
            __import__("io").BytesIO(b'{"error":{"message":"rate limit"}}'))

    monkeypatch.setattr("urllib.request.urlopen", gia_urlopen)
    monkeypatch.setattr("time.sleep", lambda s: None)
    c = GLMDirectorClient(api_key="k", retries=3)
    with pytest.raises(RuntimeError):
        c._goi([{"role": "user", "content": "x"}])
    assert lan["n"] == 3


def test_so_tam_giu_draft_tung_chuong(tmp_path):
    """03/09: GLM het tien o chuong 10/12 -> 9 chuong da chia beat bi vut sach."""
    from autoedit.director.runner import _So

    so = _So(tmp_path / "beats_tam.json")
    assert so.doc() == {}
    d = _drafts((0, 2), (3, 5)).beats
    so.ghi(1, list(d))
    so.ghi(2, list(d))
    lai = so.doc()
    assert set(lai) == {1, 2}
    assert [b.start_word for b in lai[1]] == [b.start_word for b in d]


def test_so_tam_hong_thi_chay_lai_tu_dau(tmp_path):
    """So hong thi BO, khong giet stage: chay lai ton tien con hon dung sai."""
    from autoedit.director.runner import _So

    p = tmp_path / "beats_tam.json"
    p.write_text("{ khong phai json", encoding="utf-8")
    assert _So(p).doc() == {}


def test_so_tam_xoa_duoc(tmp_path):
    from autoedit.director.runner import _So

    so = _So(tmp_path / "beats_tam.json")
    so.ghi(1, list(_drafts((0, 2)).beats))
    so.xoa()
    assert not (tmp_path / "beats_tam.json").exists()
    so.xoa()          # xoá lần hai không nổ


def test_chay_lai_chi_goi_LLM_cho_chuong_CON_THIEU(project, monkeypatch):
    """Vế QUAN TRỌNG NHẤT: nộp lại sau khi hết tiền phải BỎ QUA chương đã xong."""
    from autoedit.director.runner import _So

    # lần 1: chương 1 xong, chương 2 chết
    so = _So(Path(project.project_dir) / "beats_tam.json")
    so.ghi(1, list(_drafts((0, 2), (3, 5)).beats))

    goi = []

    class DemClient(FakeClient):
        def complete(self, system, user, output_model, context=None):
            goi.append(output_model.__name__)
            return super().complete(system, user, output_model, context)

    # chỉ còn Outline + ĐÚNG 1 lượt ChapterBeats cho chương 2
    client = DemClient([GOOD_OUTLINE, _drafts((6, 8), (9, 11))])
    run_direct(project, client, gop_chuong_ngan=False)

    assert goi.count("ChapterBeats") == 1, f"gọi lại chương đã xong: {goi}"
    from autoedit.project import Project

    saved = Project.load(project.project_dir)
    assert len(saved.beats) == 4          # đủ cả 2 chương
    assert not (Path(project.project_dir) / "beats_tam.json").exists()
