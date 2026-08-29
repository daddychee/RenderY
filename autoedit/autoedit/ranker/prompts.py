"""Prompt NÃO chấm ứng viên footage — đúng 1 call/beat (B3 khung phễu c5).

Luật nội dung lấy từ foundation đã duyệt: c2 (veto hẹp 3 dạng, phân vân KHÔNG veto),
c3 (nghĩa theo mạch — nhìn footage beat N−1, tha ranh giới chương), b1 (mood).
"""

from __future__ import annotations

import zlib

from autoedit.project import Beat

RANK_SYSTEM = """You are the footage REFEREE for one beat of a YouTube video. You receive
the beat's script sentence, its visual intent, the footage chosen for the PREVIOUS beat,
and a list of candidate footage. For EVERY candidate return: verdict, scores, one reason.

VETO RULES — a veto is allowed ONLY for these 3 SERIOUS meaning errors (set veto_type):
1. "chu_de_khac_han" — the footage shows a completely different topic than the beat.
2. "thuc_the_sai"    — wrong real entity: wrong person, wrong country/city, wrong
   landmark, wrong PLANET / celestial body / space setting (V3, the b11 lesson: Mars
   footage in a Moon video IS this veto). Judge against the CHAPTER's central_subject
   first; the VIDEO SUBJECT line (when given) is the outer boundary — an entity outside
   BOTH is wrong. Action/pose similarity does NOT redeem a wrong entity: astronauts
   walking is still a veto if they are walking on the wrong world.
3. "nguoc_tran_cu_the" — the footage contradicts a CONCRETE claim in the script
   (script says "empty streets", footage shows a crowd).
Anything else — bland, mood mismatch, repetitive framing, too generic — is NOT a veto:
verdict "ok" with a LOW score. When unsure, do NOT veto; score low instead.
Never invent a 4th veto reason. If you still feel forced to veto outside the 3 forms,
use veto_type "khac" (it will be treated as a demotion, not a hard kill).

SCORING (0-10 integers):
- diem_nghia: how well the footage MEANS what the beat says. Judge in CONTEXT: meaning
  flows across neighbouring shots (Kuleshov) — a candidate that continues the previous
  shot's subject coherently scores higher; a candidate that jars mid-chapter scores lower.
  If the beat OPENS A NEW CHAPTER, a visual break is fine — do not punish discontinuity.
  Anchor to central_subject when given: boring-but-correct beats spectacular-but-off.
- diem_mood: does the footage's feel (light, color, motion) match the beat's mood?

OUTPUT: one verdict per candidate, id = the candidate's short id code EXACTLY as given
(e.g. "a1b2c3d4"). The SAME id appearing under several beats IS the same footage.
"ly_do" = tiếng Việt, TỐI ĐA 12 TỪ (PA-2: output dài làm chậm phễu — đủ để editor
hiểu vì sao, không viết văn).
"""

RANK_BATCH_SYSTEM = RANK_SYSTEM + """
BATCH MODE — you receive a SEQUENCE of beats from ONE chapter, in playback order.
Judge them IN ORDER, maintaining the Kuleshov chain: assume the candidate you score
highest ("ok") for beat N becomes the PREVIOUS footage of beat N+1.
Do NOT let the same asset win two beats — if one asset fits several beats, give it the
top score only where it fits best and score it lower elsewhere (code enforces no-repeat
anyway, but your scores decide which alternate each beat falls back to).
Return verdicts for EVERY candidate of EVERY beat, grouped by beat_id.
"""


# --- TOC-1 (2026-07-15): id NGẮN thay asset_key trong hội thoại NÃO -------------------
# asset_key kho local = nguyên path F:\... (đo 3 bài: tb 40-66, max 165 ký tự ≈ 40-55
# token) bị NÃO chép lại trong TỪNG verdict → ~50-65% output token của call rank.
# Alias crc32 8-hex: thuần hàm theo asset_key — cùng asset ⇒ cùng alias ở mọi beat/mọi
# call (NÃO vẫn thấy asset lặp giữa các beat trong batch); funnel dịch ngược về asset_key.
def alias_of(key: str) -> str:
    return "a" + format(zlib.crc32(key.encode("utf-8")), "08x")


def build_alias_maps(cand_lists: "list[list[dict]]") -> tuple[dict, dict]:
    """(key→alias, alias→key) cho 1 call NÃO. Đụng độ crc32 (~0 xác suất): ứng viên
    sau giữ nguyên asset_key làm id — dài nhưng đúng. Prompt builder và funnel PHẢI
    dùng chung hàm này trên cùng danh sách để dịch khớp nhau."""
    key2alias: dict[str, str] = {}
    alias2key: dict[str, str] = {}
    for cands in cand_lists:
        for c in cands:
            key = c["asset_key"]
            if key in key2alias:
                continue
            a = alias_of(key)
            if a in alias2key and alias2key[a] != key:
                a = key  # đụng độ -> id = chính asset_key (fail-safe, không sai nghĩa)
            key2alias[key] = a
            alias2key[a] = key
    return key2alias, alias2key


def _candidate_lines(cands: list[dict], key2alias: dict) -> list[str]:
    """Khối ứng viên dùng chung 2 builder — 1 chỗ duy nhất quyết định format dòng id."""
    lines = []
    for i, c in enumerate(cands, start=1):
        desc = c.get("description", "") or "(no description)"
        extras = []
        if c.get("shot_size"):
            extras.append(f"shot_size={c['shot_size']}")
        if c.get("duration") is not None:
            extras.append(f"duration={c['duration']:.1f}s")
        extras.append(f"source={c.get('source', '?')}")
        lines.append(f"{i}. id: {key2alias[c['asset_key']]}\n   {desc} ({', '.join(extras)})")
    return lines


def build_batch_rank_prompt(
    items: list[tuple[Beat, list[dict]]],
    central_subject: str = "",
    prev_pick_note: str = "",
    chapter_open_first: bool = False,
    video_subject: str = "",
) -> str:
    """Ghép user prompt cho 1 chunk beat (PA-1). items = [(beat, ứng viên ĐÃ qua cửa kỹ thuật)]."""
    key2alias, _ = build_alias_maps([cands for _, cands in items])
    lines = [f"SEQUENCE OF {len(items)} BEATS (one chapter, playback order)."]
    if video_subject:
        lines.append(f"VIDEO SUBJECT (outer scope for entity vetoes): {video_subject}")
    if central_subject:
        lines.append(f"Chapter central_subject: {central_subject}")
    if chapter_open_first:
        lines.append("The FIRST beat OPENS A NEW CHAPTER — visual break from previous shot is fine.")
    if prev_pick_note:
        lines.append(f"Footage chosen BEFORE this sequence: {prev_pick_note}")
    else:
        lines.append("No previous footage (start of video).")
    for beat, cands in items:
        lines.append(f"\n=== BEAT #{beat.beat_id} — script sentence:\n{beat.text}")
        lines.append(f"Visual intent: {beat.visual_concept} (level: {beat.visual_level}, "
                     f"mood: {beat.mood}, energy: {beat.energy})")
        lines.append(f"CANDIDATES ({len(cands)}):")
        lines += _candidate_lines(cands, key2alias)
    lines.append("\nReturn beats[] — one entry per beat_id, one verdict per candidate "
                 "(id = the candidate's id code).")
    return "\n".join(lines)


def build_rank_prompt(
    beat: Beat,
    candidates: list[dict],
    central_subject: str = "",
    prev_pick_note: str = "",
    chapter_open: bool = False,
    video_subject: str = "",
) -> str:
    """Ghép user prompt cho 1 beat. prev_pick_note = mô tả footage đã chọn beat N−1."""
    key2alias, _ = build_alias_maps([candidates])
    lines = [
        f"BEAT #{beat.beat_id} — script sentence:\n{beat.text}",
        f"Visual intent: {beat.visual_concept} (level: {beat.visual_level}, "
        f"mood: {beat.mood}, energy: {beat.energy})",
    ]
    if video_subject:
        lines.append(f"VIDEO SUBJECT (outer scope for entity vetoes): {video_subject}")
    if central_subject:
        lines.append(f"Chapter central_subject: {central_subject}")
    if chapter_open:
        lines.append("This beat OPENS A NEW CHAPTER — visual break from previous shot is fine.")
    if prev_pick_note:
        lines.append(f"Footage chosen for PREVIOUS beat: {prev_pick_note}")
    else:
        lines.append("No previous footage (first beat).")

    lines.append(f"\nCANDIDATES ({len(candidates)}):")
    lines += _candidate_lines(candidates, key2alias)

    lines.append("\nReturn one verdict per candidate (id = the candidate's id code).")
    return "\n".join(lines)
