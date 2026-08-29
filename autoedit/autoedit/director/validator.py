"""Validator output LLM đạo diễn — pure functions, test không cần API.

Phòng lỗi RA_SOAT Stage 2:
- 2.2: compute_beat_times là NƠI DUY NHẤT sinh timestamp (từ transcript M2)
- 2.3: merge beat ngắn (code), beat dài -> retry feedback
- 2.4: coverage — phủ kín, không gap, không overlap
"""

from __future__ import annotations

from autoedit.project import Beat, Word

MIN_BEAT_SEC = 1.5
MAX_BEAT_SEC = 10.0
MIN_BREATHING_SEC = 1.5   # hình thở hợp lệ: 0 (không) hoặc [1.5, 6] — cấm khe (0, 1.5)
MAX_BREATHING_SEC = 6.0   # (khe (0,1.5) đã có tầng giãn máy hình thở 3.0 lo; ducking nở từ 1.5)
MAX_RHETORICAL_PER_CHAPTER = 1  # câu đinh (hình thở 3.0): DNA editor 0,28 điểm/phút ≈ 1/chương
MAX_QUERY_WORDS = 4       # Pexels keyword matching — query dài = nghèo kết quả
MAX_CHARTS_PER_CHAPTER = 2
MAX_CARDS_PER_CHAPTER = 2


# --------------------------- coverage (2.4) ----------------------------------
def check_coverage(ranges: list[tuple[int, int]], lo: int, hi: int) -> list[str]:
    """Kiểm tra dãy (start_word, end_word) inclusive phủ kín [lo, hi].

    Trả về list mô tả lỗi (rỗng = hợp lệ). Dùng chung cho chapters và beats.
    """
    errors: list[str] = []
    if not ranges:
        return [f"empty: no ranges cover [{lo}..{hi}]"]
    for i, (s, e) in enumerate(ranges):
        if s > e:
            errors.append(f"range {i}: start_word {s} > end_word {e}")
    if ranges[0][0] != lo:
        errors.append(f"first range starts at {ranges[0][0]}, must start at {lo}")
    if ranges[-1][1] != hi:
        errors.append(f"last range ends at {ranges[-1][1]}, must end at {hi}")
    for i in range(1, len(ranges)):
        prev_end, cur_start = ranges[i - 1][1], ranges[i][0]
        if cur_start > prev_end + 1:
            errors.append(
                f"gap: words [{prev_end + 1}..{cur_start - 1}] not covered "
                f"(between range {i - 1} and {i})"
            )
        elif cur_start <= prev_end:
            errors.append(
                f"overlap: range {i} starts at {cur_start} but range {i - 1} "
                f"already ends at {prev_end}"
            )
    return errors


# --------------------------- timestamp (2.2) ---------------------------------
def compute_beat_times(start_word: int, end_word: int, transcript: list[Word]) -> tuple[float, float]:
    """Nơi DUY NHẤT sinh timestamp cho beat: tra transcript theo word index."""
    if not (0 <= start_word <= end_word < len(transcript)):
        raise ValueError(
            f"word index ngoài transcript: [{start_word}..{end_word}], "
            f"transcript có {len(transcript)} từ"
        )
    return transcript[start_word].start, transcript[end_word].end


def beat_duration(start_word: int, end_word: int, transcript: list[Word]) -> float:
    s, e = compute_beat_times(start_word, end_word, transcript)
    return e - s


# --------------------------- duration (2.3) ----------------------------------
def find_long_beats(
    ranges: list[tuple[int, int]], transcript: list[Word], max_sec: float = MAX_BEAT_SEC
) -> list[str]:
    """Mô tả các beat quá dài — đưa vào retry feedback cho LLM tự chia lại."""
    issues = []
    for i, (s, e) in enumerate(ranges):
        dur = beat_duration(s, e, transcript)
        if dur > max_sec:
            issues.append(
                f"beat {i} (words [{s}..{e}]) lasts {dur:.1f}s > {max_sec:.0f}s — "
                "split it into smaller beats"
            )
    return issues


def merge_short_beats(
    beats: list[Beat], transcript: list[Word], min_sec: float = MIN_BEAT_SEC
) -> tuple[list[Beat], list[str]]:
    """Beat ngắn hơn min_sec: merge vào beat liền kề cùng chương (ưu tiên beat trước).

    Giữ metadata của beat dài hơn trong cặp merge, NHƯNG không vứt quyết định đạo diễn
    của beat ngắn (rà chồng chéo 2026-07-04 #3): overlays cộng dồn (anchor vẫn nằm trong
    range gộp), hình thở giữ max cả 2 chiều — thở chuyển chỗ sai sẽ bị
    enforce_breathing_pauses bắt ở bước sau. Trả (beats mới, notes).
    """
    notes: list[str] = []
    result: list[Beat] = []
    i = 0
    while i < len(beats):
        beat = beats[i]
        dur = beat.end - beat.start
        if dur >= min_sec:
            result.append(beat)
            i += 1
            continue

        prev_ok = result and result[-1].chapter == beat.chapter
        next_ok = i + 1 < len(beats) and beats[i + 1].chapter == beat.chapter
        if prev_ok:
            host = result[-1]
            merged = host.model_copy(
                update={
                    "end_word": beat.end_word,
                    "text": f"{host.text} {beat.text}",
                    "end": beat.end,
                    # beat ngắn là ĐUÔI mới của run -> giữ hình thở của nó
                    # (vd punchline "One." 0.2s mang pause 2s — không được rơi mất)
                    "breathing_after": max(host.breathing_after, beat.breathing_after),
                    "overlays": host.overlays + beat.overlays,
                }
            )
            result[-1] = merged
            notes.append(f"merged short beat ({dur:.1f}s) '{beat.text[:30]}...' into previous")
            notes.extend(_dropped_visual_notes(beat))
            i += 1
        elif next_ok:
            nxt = beats[i + 1]
            merged = nxt.model_copy(
                update={
                    "start_word": beat.start_word,
                    "text": f"{beat.text} {nxt.text}",
                    "start": beat.start,
                    "breathing_after": max(beat.breathing_after, nxt.breathing_after),
                    "overlays": beat.overlays + nxt.overlays,
                }
            )
            beats[i + 1] = merged
            notes.append(f"merged short beat ({dur:.1f}s) '{beat.text[:30]}...' into next")
            notes.extend(_dropped_visual_notes(beat))
            i += 1
        else:  # beat đơn độc trong chương — giữ nguyên, chỉ ghi chú
            result.append(beat)
            notes.append(f"short beat ({dur:.1f}s) kept (alone in chapter {beat.chapter})")
            i += 1
    # đánh lại beat_id liên tục
    return [b.model_copy(update={"beat_id": k}) for k, b in enumerate(result)], notes


def _dropped_visual_notes(beat: Beat) -> list[str]:
    """Chart/card/text-sequence của beat ngắn KHÔNG merge được (host chỉ chứa 1) —
    báo rõ thay vì rơi im lặng. Cực hiếm (chart/card cần beat 4-8s đứng hình)."""
    dropped = [
        name
        for name, val in (
            ("graphic_spec", beat.graphic_spec),
            ("info_card", beat.info_card),
            ("text_sequence", beat.text_sequence),
        )
        if val is not None
    ]
    if not dropped:
        return []
    return [
        f"merged short beat '{beat.text[:30]}...' had {'/'.join(dropped)} — DROPPED "
        "(beat liền kề chỉ chứa được 1), editor kiểm lại nếu cần"
    ]


# --------------------------- quy tắc v2 (P1, P5) ------------------------------
def check_v2_rules(drafts) -> list[str]:
    """Lỗi vi phạm Footage Sourcing v2 — đưa vào retry feedback cho LLM.

    drafts: list[BeatDraft] (duck-typed để test dễ).
    """
    errors: list[str] = []
    for i, d in enumerate(drafts):
        q = d.search_queries
        # P5: mọi query stock ≤4 từ (C4: tier local gác chung luật; getattr vì duck-typed)
        for tier_name, queries in (("specific", q.specific), ("broad", q.broad),
                                   ("thematic", q.thematic), ("local", getattr(q, "local", []))):
            for query in queries:
                if len(query.split()) > MAX_QUERY_WORDS:
                    errors.append(
                        f"beat {i}: query '{query}' ({tier_name}) has "
                        f"{len(query.split())} words — maximum is {MAX_QUERY_WORDS}"
                    )
        # P1: route entity phải có entity_queries, không sinh stock query
        if d.sourcing_route == "entity":
            if not d.entity_queries:
                errors.append(
                    f"beat {i}: sourcing_route=entity but entity_queries is empty — "
                    "provide 1-3 Google Images queries for the real entity"
                )
        else:
            if d.entity_queries:
                errors.append(
                    f"beat {i}: entity_queries given but sourcing_route="
                    f"{d.sourcing_route} — entity_queries only for route entity"
                )
        # P1: route graphic không search stock
        if d.sourcing_route == "graphic" and (q.specific or q.broad):
            errors.append(
                f"beat {i}: sourcing_route=graphic must not have stock queries — "
                "describe a graphic placeholder instead"
            )
        # Hình thở: 0 (không) hoặc 1.5-6s — khớp đúng thông báo (rà chồng chéo 2026-07-04 #4)
        sec = getattr(d, "breathing_after_sec", None)
        if sec is not None and not (
            sec == 0.0 or MIN_BREATHING_SEC <= sec <= MAX_BREATHING_SEC
        ):
            errors.append(
                f"beat {i}: breathing_after_sec={sec} out of range — must be 0 (none) "
                "or 1.5-6 seconds"
            )
    # Câu đinh (hình thở 3.0): ≤MAX_RHETORICAL_PER_CHAPTER. Cờ đặt trên beat kết dấu
    # vô hại (pause.py xét dấu trước cờ — máy tự xử tầng câu/mệnh đề), không cần chặn.
    rhet_idx = [i for i, d in enumerate(drafts) if getattr(d, "rhetorical_pause", False)]
    if len(rhet_idx) > MAX_RHETORICAL_PER_CHAPTER:
        errors.append(
            f"beats {rhet_idx}: {len(rhet_idx)} rhetorical_pause in one chapter — max "
            f"{MAX_RHETORICAL_PER_CHAPTER}, keep only the single strongest mid-sentence break"
        )
    return errors


OVERLAY_TEXT_MAX = 20
TYPING_TEXT_MAX = 24      # name/place/quote gõ máy — giữ ngắn cho gọn màn


def check_graphic_specs(drafts) -> list[str]:
    """Lỗi graphic_spec -> retry: cần ≥2 data, route phải = graphic (P1.5a full)."""
    errors: list[str] = []
    for i, d in enumerate(drafts):
        gs = getattr(d, "graphic_spec", None)
        if gs is None:
            continue
        if len(gs.data) < 2:
            errors.append(f"beat {i}: graphic_spec cần ≥2 điểm dữ liệu (chart so sánh/xu hướng)")
        if gs.chart_type == "pie" and any(d.value <= 0 for d in gs.data):
            errors.append(
                f"beat {i}: pie cần mọi phần > 0 (tỉ trọng âm/0 vô nghĩa) — "
                "dùng bar nếu chỉ so sánh 2 con số rời"
            )
        layout = getattr(gs, "layout", "full")
        if layout == "full" and d.sourcing_route != "graphic":
            errors.append(
                f"beat {i}: chart layout=full nhưng route={d.sourcing_route} — "
                "full chiếm cả khung, phải route=graphic"
            )
        if layout == "half" and d.sourcing_route == "graphic":
            errors.append(
                f"beat {i}: chart layout=half nhưng route=graphic — half cần footage nền, "
                "đặt route=stock/entity/local + visual_concept tả cảnh"
            )
    return errors


def check_info_cards(drafts) -> list[str]:
    """Lỗi info_card trong pass direct -> retry: format + mutual exclusion."""
    errors: list[str] = []
    for i, d in enumerate(drafts):
        ic = getattr(d, "info_card", None)
        if ic is None:
            continue
        if not ic.title.strip():
            errors.append(f"beat {i}: info_card thiếu title")
        if not (3 <= len(ic.bullets) <= 5):
            errors.append(f"beat {i}: info_card cần 3-5 bullet (có {len(ic.bullets)})")
        if any(len(b) > 40 for b in ic.bullets):
            errors.append(f"beat {i}: info_card có bullet >40 ký tự — giữ ngắn gọn")
        if getattr(d, "graphic_spec", None) is not None:
            errors.append(f"beat {i}: info_card KHÔNG đi cùng graphic_spec — chọn 1")
        if getattr(d, "text_sequence", None) is not None:
            errors.append(f"beat {i}: info_card KHÔNG đi cùng text_sequence — chọn 1")
    return errors


def enforce_chapter_visual_limits(
    drafts, max_charts: int = MAX_CHARTS_PER_CHAPTER, max_cards: int = MAX_CARDS_PER_CHAPTER
) -> tuple[list, list[str]]:
    """Bỏ chart/card thứ 3+ trong chương (post-LLM clip, không retry LLM).

    Ưu tiên giữ cái xuất hiện trước; trả (drafts đã clip, ghi chú).
    """
    notes: list[str] = []
    chart_count = card_count = 0
    result = []
    for i, d in enumerate(drafts):
        has_chart = getattr(d, "graphic_spec", None) is not None
        has_card = getattr(d, "info_card", None) is not None
        updates = {}
        if has_chart:
            if chart_count >= max_charts:
                updates["graphic_spec"] = None
                notes.append(f"beat {i}: bỏ chart thứ {chart_count + 1} (giới hạn {max_charts}/chương)")
            else:
                chart_count += 1
        if has_card:
            if card_count >= max_cards:
                updates["info_card"] = None
                notes.append(f"beat {i}: bỏ card thứ {card_count + 1} (giới hạn {max_cards}/chương)")
            else:
                card_count += 1
        result.append(d.model_copy(update=updates) if updates else d)
    return result, notes


def check_enrichments(plan, beats) -> list[str]:
    """Lỗi EnrichmentPlan -> retry: beat_id tồn tại, chart data≥2 + nguồn, card 3-5 bullet,
    không gắn chart lên beat đã có graphic_spec, mỗi beat tối đa 1 bổ sung."""
    errors: list[str] = []
    ids = {b.beat_id for b in beats}
    by_id = {b.beat_id: b for b in beats}
    seen: set[int] = set()
    for j, e in enumerate(plan.enrichments):
        if e.beat_id not in ids:
            errors.append(f"enrich {j}: beat_id={e.beat_id} không tồn tại")
            continue
        if e.beat_id in seen:
            errors.append(f"enrich {j}: beat {e.beat_id} đã có bổ sung khác — mỗi beat tối đa 1")
        seen.add(e.beat_id)
        if e.kind == "chart":
            c = e.chart
            if c is None:
                errors.append(f"enrich {j}: kind=chart nhưng thiếu chart")
                continue
            if len(c.data) < 2:
                errors.append(f"enrich {j}: chart cần ≥2 điểm dữ liệu")
            if c.chart_type == "pie" and any(d.value <= 0 for d in c.data):
                errors.append(f"enrich {j}: pie cần mọi phần > 0")
            if not c.source_note.strip():
                errors.append(f"enrich {j}: chart BỔ SUNG bắt buộc có source_note (nguồn web)")
            if by_id[e.beat_id].graphic_spec is not None:
                errors.append(f"enrich {j}: beat {e.beat_id} đã có graphic_spec — không thêm chart")
        elif e.kind == "info_card":
            ic = e.info_card
            if ic is None:
                errors.append(f"enrich {j}: kind=info_card nhưng thiếu info_card")
                continue
            if not (3 <= len(ic.bullets) <= 5):
                errors.append(f"enrich {j}: info_card cần 3-5 bullet (có {len(ic.bullets)})")
            if any(len(b) > 40 for b in ic.bullets):
                errors.append(f"enrich {j}: bullet quá dài (>40 ký tự) — giữ ngắn gọn")
            if not ic.title.strip():
                errors.append(f"enrich {j}: info_card thiếu title")
    return errors


def check_overlays(drafts) -> list[str]:
    """Lỗi overlay -> retry feedback: anchor ngoài beat, text quá dài."""
    errors: list[str] = []
    for i, d in enumerate(drafts):
        for ov in getattr(d, "overlays", []):
            if not (d.start_word <= ov.anchor_word <= d.end_word):
                errors.append(
                    f"beat {i}: overlay '{ov.text}' anchor_word={ov.anchor_word} "
                    f"ngoài beat [{d.start_word}..{d.end_word}]"
                )
            # typing (name/place/quote) cho phép tới 24 ký tự; còn lại 20
            cap = TYPING_TEXT_MAX if ov.kind in ("name", "place", "quote") else OVERLAY_TEXT_MAX
            if len(ov.text) > cap:
                errors.append(
                    f"beat {i}: overlay text '{ov.text}' dài {len(ov.text)} ký tự "
                    f"> {cap} — chỉ ghi con số/từ/tên ngắn, không cả câu"
                )
    return errors


def check_text_sequences(drafts) -> list[str]:
    """Lỗi text_sequence -> retry: 2-4 cụm, anchor trong beat + TĂNG dần, cụm đầu = đầu beat,
    KHÔNG đi cùng graphic_spec."""
    errors: list[str] = []
    for i, d in enumerate(drafts):
        ts = getattr(d, "text_sequence", None)
        if ts is None:
            continue
        ph = ts.phrases
        if not (2 <= len(ph) <= 4):
            errors.append(f"beat {i}: text_sequence cần 2-4 cụm (có {len(ph)})")
        if getattr(d, "graphic_spec", None) is not None:
            errors.append(f"beat {i}: text_sequence KHÔNG đi cùng graphic_spec — chọn 1")
        prev = None
        for k, p in enumerate(ph):
            if not (d.start_word <= p.anchor_word <= d.end_word):
                errors.append(
                    f"beat {i}: cụm '{p.text}' anchor={p.anchor_word} ngoài beat "
                    f"[{d.start_word}..{d.end_word}]"
                )
            if prev is not None and p.anchor_word <= prev:
                errors.append(
                    f"beat {i}: anchor cụm '{p.text}'={p.anchor_word} phải TĂNG so với cụm trước ({prev})"
                )
            prev = p.anchor_word
        if ph and ph[0].anchor_word != d.start_word:
            errors.append(
                f"beat {i}: cụm đầu '{ph[0].text}' anchor={ph[0].anchor_word} phải = đầu beat {d.start_word}"
            )
    return errors


def check_overlay_density(beats: list[Beat]) -> list[str]:
    """Cảnh báo (không retry) khi lạm dụng overlay — quá ~1/8s thoại."""
    n = sum(len(b.overlays) for b in beats)
    if not beats or n == 0:
        return []
    speech = beats[-1].end - beats[0].start
    allowed = max(1, int(speech // 8))
    if n > allowed:
        return [
            f"{n} overlay trên {speech:.0f}s thoại (ngưỡng ~{allowed}) — lạm dụng, "
            "video đầy chữ trông rẻ; cân nhắc bớt"
        ]
    return []


def check_chapter_breathing(drafts, is_hook: bool) -> list[str]:
    """Lỗi nhịp hình thở TRONG 1 chương — đưa vào retry feedback (chốt với user 11/06:
    hook cần hình thở sau punch; không bao giờ 2 hình thở liên tiếp)."""
    errors: list[str] = []
    for i in range(len(drafts) - 1):
        if drafts[i].breathing_after_sec > 0 and drafts[i + 1].breathing_after_sec > 0:
            errors.append(
                f"beats {i} and {i + 1} both have breathing_after_sec > 0 — never two "
                "breathing gaps in a row; keep only the one after the stronger idea"
            )
    if is_hook and len(drafts) >= 2 and not any(d.breathing_after_sec > 0 for d in drafts):
        errors.append(
            "this is the HOOK chapter but no beat has breathing_after_sec > 0 — add a "
            "short 1.5-2.5s pause after the strongest punchline/shocking number so it lands"
        )
    return errors


def check_breathing_rhythm(beats: list[Beat], hook_chapter: int | None) -> list[str]:
    """Cảnh báo nhịp hình thở (không retry — chuyện tinh chỉnh, người quyết).

    - Hook không có hình thở nào -> punch không kịp ngấm (góp ý của user 11/06)
    - Bất kỳ đâu: 2 hình thở trong <15s thoại -> nghi lạm dụng
    - 2 beat liên tiếp đều có hình thở -> nghi lạm dụng
    """
    warnings: list[str] = []
    if hook_chapter is not None:
        hook_beats = [b for b in beats if b.chapter == hook_chapter]
        if hook_beats and not any(b.breathing_after > 0 for b in hook_beats):
            warnings.append(
                f"hook (chương {hook_chapter}) không có hình thở nào — punch/số liệu "
                "sốc không có khoảng ngấm, cân nhắc thêm 1.5-2.5s sau punchline"
            )
    last_breath_end: float | None = None
    for i, b in enumerate(beats):
        if b.breathing_after <= 0:
            continue
        if i + 1 < len(beats) and beats[i + 1].breathing_after > 0:
            warnings.append(
                f"beat {b.beat_id} và {beats[i + 1].beat_id} đều có hình thở liên tiếp — lạm dụng"
            )
        if last_breath_end is not None and b.end - last_breath_end < 15.0:
            warnings.append(
                f"2 hình thở cách nhau <15s thoại (quanh beat {b.beat_id}) — cân nhắc bỏ bớt"
            )
        last_breath_end = b.end
    return warnings


# --------------------------- chất lượng khác ---------------------------------
def check_graphic_ratio(beats: list[Beat], max_per_60s: int = 1) -> list[str]:
    """Graphic = giờ công editor. Quá ~1 graphic/60s thoại → cảnh báo (không retry)."""
    if not beats:
        return []
    n_graphic = sum(1 for b in beats if b.sourcing_route == "graphic")
    speech_sec = beats[-1].end - beats[0].start
    allowed = max(1, -(-int(speech_sec) // 60) * max_per_60s)  # làm tròn lên theo phút
    if n_graphic > allowed:
        return [
            f"{n_graphic} beat graphic trên {speech_sec:.0f}s thoại (ngưỡng ~{allowed}) — "
            "editor sẽ tốn nhiều giờ công; cân nhắc chuyển bớt sang stock + text overlay"
        ]
    return []


MIN_BREATHING_PAUSE = 0.3  # giây nghỉ tối thiểu trong transcript để được hình thở


def enforce_breathing_pauses(
    beats: list[Beat], transcript: list[Word], min_gap: float = MIN_BREATHING_PAUSE
) -> tuple[list[Beat], list[str]]:
    """Bỏ hình thở rơi vào chỗ NÓI LIỀN MẠCH (cắt giữa cụm từ/từ — bug 13/06).

    Hình thở = chỗ cắt voice + chèn im. Chỉ hợp lệ khi giữa từ cuối beat và từ kế
    có khoảng nghỉ thật (≥min_gap). Chỗ gap~0 = giữa cụm -> bỏ, 2 beat nhập 1 segment.
    """
    notes: list[str] = []
    out: list[Beat] = []
    for b in beats:
        if b.breathing_after > 0 and b.end_word + 1 < len(transcript):
            gap = transcript[b.end_word + 1].start - transcript[b.end_word].end
            if gap < min_gap:
                last = transcript[b.end_word].text
                nxt = transcript[b.end_word + 1].text
                notes.append(
                    f"beat {b.beat_id}: bỏ hình thở giữa cụm '{last}|{nxt}' "
                    f"(nghỉ {gap:.2f}s < {min_gap}s — sẽ cắt đôi cụm từ)"
                )
                b = b.model_copy(update={"breathing_after": 0.0})
        out.append(b)
    return out, notes


def check_breathing_placement(
    drafts, transcript: list[Word], lo: int, hi: int, min_gap: float = MIN_BREATHING_PAUSE
) -> list[str]:
    """LỖI khi hình thở đặt ở chỗ voice KHÔNG nghỉ — kèm gap đo được + gợi ý từ có
    nghỉ thật gần đó, để phiên sống ĐẶT LẠI thay vì bị xóa âm thầm (rà chồng chéo
    2026-07-04 #2: validator ép hook có thở, enforce_breathing_pauses lại lặng lẽ xóa).

    Chỉ dùng ở đường direct-ingest. Nếu CẢ CHƯƠNG [lo, hi] không có chỗ nghỉ nào
    ≥min_gap → trả [] (hạ về hành vi cũ: enforce_breathing_pauses xóa + note,
    tránh kẹt vòng sửa không lối ra).
    """
    pause_words = [
        w for w in range(lo, min(hi + 1, len(transcript) - 1))
        if transcript[w + 1].start - transcript[w].end >= min_gap
    ]
    if not pause_words:
        return []
    errors: list[str] = []
    for i, d in enumerate(drafts):
        sec = getattr(d, "breathing_after_sec", 0.0)
        if sec <= 0 or d.end_word + 1 >= len(transcript):
            continue
        gap = transcript[d.end_word + 1].start - transcript[d.end_word].end
        if gap >= min_gap:
            continue
        nearest = sorted(pause_words, key=lambda w: abs(w - d.end_word))[:3]
        hints = ", ".join(
            f"[{w}]{transcript[w].text} (pause {transcript[w + 1].start - transcript[w].end:.2f}s)"
            for w in nearest
        )
        errors.append(
            f"beat {i}: breathing_after_sec={sec} but voice does NOT pause after word "
            f"[{d.end_word}]{transcript[d.end_word].text} (gap {gap:.2f}s < {min_gap}s — "
            f"the cut would split a phrase). Move the beat boundary/breathing to a word "
            f"with a real pause, e.g.: {hints}"
        )
    return errors


def check_consecutive_shot_size(beats: list[Beat], limit: int = 3) -> list[str]:
    """FOUNDATION: không cho phép `limit` beat liên tiếp cùng cỡ cảnh."""
    warnings = []
    run, run_start = 1, 0
    for i in range(1, len(beats)):
        if beats[i].shot_size == beats[i - 1].shot_size:
            run += 1
            if run == limit:
                warnings.append(
                    f"{limit} beat liên tiếp cùng cỡ cảnh '{beats[i].shot_size}' "
                    f"(beat {run_start}..{i})"
                )
        else:
            run, run_start = 1, i
    return warnings


# ---- TEMPO MAP (2026-07-14, MO_TA_VAN_HANH_TEMPO_MAP.md §2) — warning-only,
# chạy tại direct-ingest LÚC SỬA CÒN RẺ (check_pacing sau assemble giữ làm lưới cuối)
TEMPO_FLAT_RATIO = 1.3   # trung vị beat max/min giữa các chương < 1.3 -> "tempo phẳng"
TEMPO_STD_MIN = 0.25     # std/median độ dài beat trong chương < 0.25 -> "đều tăm tắp"
TEMPO_SLACK = 0.95       # biên 5% cho so sánh khai-vs-thực (tránh warn-spam vì lệch vụn)
_TEMPO_MIN_BEATS = 6     # chương ít beat hơn -> bỏ qua khai-vs-thực (chia 3 khúc quá noisy)


def check_tempo_map(outline: dict, beats: list[Beat]) -> list[str]:
    """3 lưới tempo map: ① phẳng giữa chương ② đều trong chương ③ khai-vs-thực
    (+ khai thiếu / shuffle). CHỈ cảnh báo, KHÔNG chặn (filter-overload-guard)."""
    import statistics

    warnings: list[str] = []
    durs: dict[int, list[float]] = {}
    for b in beats:
        d = b.end - b.start
        if d > 0:
            durs.setdefault(b.chapter, []).append(d)

    chapters = (outline or {}).get("chapters", [])
    curves = {c.get("chapter_id"): c.get("tempo_curve", "") for c in chapters}

    # khai thiếu (draft mới phải khai; draft cũ re-ingest chấp nhận warning này)
    if chapters and all(not v for v in curves.values()):
        warnings.append("tempo map: outline chưa khai tempo_curve chương nào — "
                        "xem block TEMPO MAP trong direct_context.md")
    # shuffle: 3 chương liền kề cùng curve đã khai
    ids = [c.get("chapter_id") for c in chapters]
    for i in range(2, len(ids)):
        cs = [curves.get(ids[j], "") for j in (i - 2, i - 1, i)]
        if cs[0] and cs[0] == cs[1] == cs[2]:
            warnings.append(f"tempo map: 3 chương liền kề {ids[i-2]}-{ids[i]} cùng curve "
                            f"'{cs[0]}' — shuffle chống đều")
            break

    # ① tempo phẳng giữa chương (≥2 chương đủ beat)
    meds = {ch: statistics.median(ds) for ch, ds in durs.items() if len(ds) >= 3}
    if len(meds) >= 2:
        lo, hi = min(meds.values()), max(meds.values())
        if lo > 0 and hi / lo < TEMPO_FLAT_RATIO:
            warnings.append(
                f"tempo phẳng giữa chương: trung vị beat mọi chương xấp xỉ nhau "
                f"({lo:.1f}–{hi:.1f}s, tỉ lệ {hi / lo:.2f} < {TEMPO_FLAT_RATIO}) — các chương "
                "cùng một nhịp, xem lại tempo map")

    # ② đều tăm tắp trong chương
    for ch in sorted(durs):
        ds = durs[ch]
        if len(ds) < 3:
            continue
        med = statistics.median(ds)
        if med > 0 and statistics.pstdev(ds) / med < TEMPO_STD_MIN:
            warnings.append(
                f"chương {ch} đều tăm tắp: beat lệch chuẩn {statistics.pstdev(ds):.2f}s "
                f"/ trung vị {med:.1f}s — thiếu xen kẽ dài/ngắn")

    # ③ khai một đằng làm một nẻo (chia chương 3 khúc theo thứ tự beat)
    med_all = statistics.median([d for ds in durs.values() for d in ds]) if durs else 0
    for ch in sorted(durs):
        curve, ds = curves.get(ch, ""), durs[ch]
        if not curve or len(ds) < _TEMPO_MIN_BEATS:
            continue
        k = len(ds) // 3
        m1, m2, m3 = (statistics.median(ds[:k]), statistics.median(ds[k:-k]),
                      statistics.median(ds[-k:]))
        bad = ""
        if curve == "build" and m3 > m1 * TEMPO_SLACK:
            bad = f"beat cuối chương ({m3:.1f}s) không ngắn dần so với đầu ({m1:.1f}s)"
        elif curve == "fast_settle" and m1 > m3 * TEMPO_SLACK:
            bad = f"beat mở chương ({m1:.1f}s) không nhanh hơn cuối ({m3:.1f}s)"
        elif curve == "slow_build_slow" and m2 > min(m1, m3) * TEMPO_SLACK:
            bad = f"khúc giữa ({m2:.1f}s) không dồn hơn hai đầu ({m1:.1f}/{m3:.1f}s)"
        elif curve == "dense" and med_all and statistics.median(ds) > med_all:
            bad = f"trung vị {statistics.median(ds):.1f}s > nền video {med_all:.1f}s — chưa dày"
        elif curve == "calm" and med_all and statistics.median(ds) < med_all:
            bad = f"trung vị {statistics.median(ds):.1f}s < nền video {med_all:.1f}s — chưa thả"
        if bad:
            warnings.append(f"chương {ch} khai '{curve}' nhưng {bad}")
    return warnings


def check_boundary_interpolated(beats: list[Beat], transcript: list[Word]) -> list[str]:
    """Ranh giới beat rơi vào từ nội suy (M2) → timestamp kém tin cậy, M4 cần biết."""
    warnings = []
    for b in beats:
        flags = []
        if transcript[b.start_word].interpolated:
            flags.append(f"từ đầu [{b.start_word}]")
        if transcript[b.end_word].interpolated:
            flags.append(f"từ cuối [{b.end_word}]")
        if flags:
            warnings.append(
                f"beat {b.beat_id}: ranh giới tại từ nội suy ({', '.join(flags)}) — "
                "điểm cắt voice nên dò lại bằng silence detection"
            )
    return warnings
