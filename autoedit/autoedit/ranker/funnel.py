"""Khung phễu c5 — B2 LỌC (2 cửa) → B3 CHẤM (NÃO 1 call + điểm máy) → B4 CHỌN (sàn 3).

Thiết kế đã duyệt: MO_TA_VAN_HANH_PHEU_C5.md. Bước B1 THU nằm ở sourcer (milestone 2).
Nguyên tắc đóng băng (c5): ĐÚNG 2 cửa loại (hỏng kỹ thuật + veto nghĩa nghiêm trọng);
mọi tiêu chí khác là ĐIỂM. Điểm MÁY cố tình nhỏ — không bao giờ lật được thứ tự nghĩa.
"""

from __future__ import annotations

from typing import Callable, Optional, Protocol

from autoedit.project import Beat
from autoedit.ranker.prompts import (
    RANK_BATCH_SYSTEM,
    RANK_SYSTEM,
    build_alias_maps,
    build_batch_rank_prompt,
    build_rank_prompt,
)
from autoedit.ranker.schema import (
    SERIOUS_VETO_TYPES,
    BatchRankResponse,
    BeatRankResponse,
    BeatRankResult,
    CandidateVerdict,
    RankedCandidate,
)

# --- Trọng số 🔸 VÍ DỤ (c5 đóng băng THỨ TỰ nghĩa > mood > nhịp; số chỉnh sau) --------
NGHIA_W = 3.0
MOOD_W = 2.5
# Điểm MÁY: mỗi chiều ±0.5. Tổng spread tối đa 2.5 < NGHIA_W (3.0 = chênh 1 điểm nghĩa)
# -> điểm máy KHÔNG BAO GIỜ lật ứng viên đúng-nghĩa xuống dưới ứng viên kém-nghĩa hơn.
VARIETY_BONUS = 0.5   # c7: cỡ cảnh KHÁC shot trước +0.5, TRÙNG -0.5, thiếu tag 0 (không trừ)
DURATION_BONUS = 0.5  # 4.4: clip đủ dài (>= 1.2x beat) phủ thoải mái
UNUSED_BONUS = 0.5    # P7: asset chưa dùng trên kênh này
PEAK_BONUS = 0.5      # ytref §3h: cảnh mang cờ điểm nhô Most Replayed — 🔸 phẳng
REF_BONUS = 1.0       # REF (user 2026-07-11): cảnh NGUỒN MẪU CỦA BÀI (khai --ref) — thắng
                      # khi nghĩa NGANG, cố ý KHÔNG lật nổi 1 điểm nghĩa (=3.0) — 🔸 phẳng
#                       primary+secondary, chỉnh sau video kiểm M3 nếu lấn/chìm
BOOST_BONUS = 1.0     # BOOST (user 2026-07-17): cảnh KHO match sở thích khán giả
                      # (--boost/audience_bias) — 🔸 phẳng. CỘNG DỒN với REF (user chấp
                      # nhận P5 2026-07-17: ref+boost+peak+máy = 4.5 lật được chênh
                      # 1 điểm nghĩa TẠI scope editor đã tuyên bố muốn X — hành vi muốn
                      # có; chênh 2 điểm nghĩa (6.0) vẫn không lật nổi, veto nghĩa vẫn gác)
MACHINE_MAX_SPREAD = 2 * VARIETY_BONUS + DURATION_BONUS + UNUSED_BONUS + PEAK_BONUS  # = 2.5
# REF_BONUS/BOOST_BONUS cố ý ĐỨNG NGOÀI spread trên: đó là bonus Ý ĐỒ EDITOR (người
# khai chủ động), khác họ điểm máy trung tính — bất biến test_ranker giữ nguyên.

PREFER_DURATION_RATIO = 1.2   # như sourcer/runner (4.4)
MIN_DURATION_RATIO = 0.5      # cửa kỹ thuật: cần slow-mo quá 2x mới phủ nổi beat -> hỏng
DEMOTE_PENALTY = 100.0        # trả-lại-sàn: trừ nặng -> luôn xếp SAU mọi ứng viên ok
POOL_FLOOR = 3                # sàn pool (c5 đóng băng)


class RankBrain(Protocol):
    """Cùng interface DirectorClient.complete — ClaudeCodeDirectorClient cắm thẳng."""

    def complete(self, system: str, user: str, output_model, context=None): ...


def _need_dur(beat: Beat) -> float:
    """Độ dài footage beat này phải phủ: voice + thở + giãn máy (hình thở 3.0 —
    cut chạy TRƯỚC source nên 2 field sau đã có; thiếu là clip ngắn lọt vào ô thở
    dài → slow-mo xấu đúng chỗ cần đẹp nhất).

    Ô thở >= BREATH_SHOT_MIN: shot thở riêng gánh phần ô sau HOLD (MO_TA_SHOT_THO §2)
    → clip beat chỉ cần phủ thoại + HOLD. Ô cuối-chương 1,5-2,5s cũng nhận shot thở
    nhưng phễu không biết hàng xóm → giữ conservative (tính đủ tail, chỉ thiệt nhẹ).
    Pick hụt → assembler giãn clip beat phủ ô (degrade sẵn có, có warning)."""
    from autoedit.packager.coverage import BREATH_SHOT_HOLD, BREATH_SHOT_MIN

    tail = beat.breathing_after + beat.micro_pause_after
    if beat.breathing_after >= BREATH_SHOT_MIN:
        tail = BREATH_SHOT_HOLD + beat.micro_pause_after
    return beat.end - beat.start + tail


def _technical_gate(beat: Beat, candidates: list[dict], kill: dict) -> list[dict]:
    """B2 cửa 1: hỏng kỹ thuật / watermark (máy, metadata thuần)."""
    beat_dur = _need_dur(beat)
    alive: list[dict] = []
    for c in candidates:
        dur = c.get("duration")
        too_short = (c.get("media_type") == "video" and dur is not None
                     and dur < beat_dur * MIN_DURATION_RATIO)
        if c.get("watermark") or too_short:
            kill["hong_ky_thuat"] += 1
            continue
        alive.append(c)
    return alive


def rank_beat(
    beat: Beat,
    candidates: list[dict],
    brain: RankBrain,
    *,
    central_subject: str = "",
    prev_pick_note: str = "",
    prev_shot_size: str = "",
    chapter_open: bool = False,
    times_used: Optional[Callable[[str], int]] = None,  # P7: asset_key -> số lần đã dùng
    video_subject: str = "",  # V3: phạm vi chủ thể video — vòng ngoài veto thực thể
) -> BeatRankResult:
    """Chạy phễu cho 1 beat trên danh sách ứng viên đã THU. NÃO gọi đúng 1 lần.
    PA-3 (2026-07-07): pool sau cửa kỹ thuật ≤1 → auto-pick, KHÔNG tốn call NÃO."""
    result = BeatRankResult(beat_id=beat.beat_id)
    kill = {"thu": len(candidates), "hong_ky_thuat": 0, "veto_nghia": 0,
            "tra_lai_san": 0, "con_lai": 0}
    result.kill_log = kill

    alive = _technical_gate(beat, candidates, kill)
    if not alive:
        result.needs_human = True
        result.warnings.append(f"beat {beat.beat_id}: pool trống sau cửa kỹ thuật")
        return result
    if len(alive) == 1:  # PA-3: chấm 1 ứng viên là vô nghĩa — chọn luôn
        return _finish_scoring(beat, alive, {}, result, kill,
                               prev_shot_size=prev_shot_size, times_used=times_used,
                               auto_note="(pool 1 sau cửa kỹ thuật — auto-pick, không gọi NÃO)")

    # --- B3: NÃO chấm — ĐÚNG 1 call cho cả beat ---------------------------------------
    user = build_rank_prompt(beat, alive, central_subject=central_subject,
                             prev_pick_note=prev_pick_note, chapter_open=chapter_open,
                             video_subject=video_subject)
    response, usage = brain.complete(RANK_SYSTEM, user, BeatRankResponse)
    result.input_tokens, result.output_tokens = usage.input_tokens, usage.output_tokens
    # TOC-1: NÃO trả id NGẮN (alias crc32) -> dịch về asset_key; id lạ/nguyên văn
    # asset_key giữ nguyên (fail-open — rơi vào nhánh "NÃO bỏ sót" điểm trung tính)
    _, alias2key = build_alias_maps([alive])
    by_id = {alias2key.get(v.id, v.id): v for v in response.verdicts}
    return _finish_scoring(beat, alive, by_id, result, kill,
                           prev_shot_size=prev_shot_size, times_used=times_used)


def rank_beat_prescored(
    beat: Beat,
    candidates: list[dict],
    verdicts_by_id: dict[str, CandidateVerdict],
    *,
    prev_shot_size: str = "",
    times_used: Optional[Callable[[str], int]] = None,
) -> BeatRankResult:
    """Phễu cho 1 beat với verdict ĐÃ CÓ từ call batch (PA-1) — không gọi NÃO nữa.
    Cùng đường B2→B3-máy→B4 với rank_beat: batch vs per-beat cho cùng verdict phải ra
    cùng kết quả (có regression test giữ bất biến này)."""
    result = BeatRankResult(beat_id=beat.beat_id)
    kill = {"thu": len(candidates), "hong_ky_thuat": 0, "veto_nghia": 0,
            "tra_lai_san": 0, "con_lai": 0}
    result.kill_log = kill

    alive = _technical_gate(beat, candidates, kill)
    if not alive:
        result.needs_human = True
        result.warnings.append(f"beat {beat.beat_id}: pool trống sau cửa kỹ thuật")
        return result
    if len(alive) == 1:  # PA-3
        return _finish_scoring(beat, alive, {}, result, kill,
                               prev_shot_size=prev_shot_size, times_used=times_used,
                               auto_note="(pool 1 sau cửa kỹ thuật — auto-pick, không gọi NÃO)")
    return _finish_scoring(beat, alive, verdicts_by_id, result, kill,
                           prev_shot_size=prev_shot_size, times_used=times_used)


def rank_batch(
    items: list[tuple[Beat, list[dict]]],
    brain: RankBrain,
    *,
    central_subject: str = "",
    prev_pick_note: str = "",
    chapter_open_first: bool = False,
    video_subject: str = "",  # V3: phạm vi chủ thể video — vòng ngoài veto thực thể
) -> tuple[dict[int, Optional[dict[str, CandidateVerdict]]], tuple[int, int], list[str]]:
    """PA-1: ĐÚNG 1 call NÃO cho cả chunk beat cùng chương (thay 1 call/beat).

    Trả (verdict_map theo beat_id, (in_tokens, out_tokens), warnings).
    - beat pool ≤1 sau cửa kỹ thuật: KHÔNG gửi NÃO (PA-3) → map = {} (prescored tự auto-pick).
    - beat NÃO quên trong response → map = None (caller rơi về rank_beat 1 call — fallback).
    """
    warnings: list[str] = []
    maps: dict[int, Optional[dict[str, CandidateVerdict]]] = {}
    ask: list[tuple[Beat, list[dict]]] = []
    for beat, candidates in items:
        kill_tmp = {"hong_ky_thuat": 0}
        alive = _technical_gate(beat, candidates, kill_tmp)
        if len(alive) <= 1:
            maps[beat.beat_id] = {}          # PA-3 / needs_human — prescored xử
        else:
            ask.append((beat, alive))
    if not ask:
        return maps, (0, 0), warnings

    user = build_batch_rank_prompt(ask, central_subject=central_subject,
                                   prev_pick_note=prev_pick_note,
                                   chapter_open_first=chapter_open_first,
                                   video_subject=video_subject)
    response, usage = brain.complete(RANK_BATCH_SYSTEM, user, BatchRankResponse)
    # TOC-1: dịch alias -> asset_key (cùng build_alias_maps với builder — khớp 1:1)
    _, alias2key = build_alias_maps([alive for _, alive in ask])
    got = {bv.beat_id: {alias2key.get(v.id, v.id): v for v in bv.verdicts}
           for bv in response.beats}
    for beat, _alive in ask:
        if beat.beat_id in got:
            maps[beat.beat_id] = got[beat.beat_id]
        else:
            maps[beat.beat_id] = None
            warnings.append(f"batch NÃO quên beat {beat.beat_id} — rơi về 1 call/beat")
    return maps, (usage.input_tokens, usage.output_tokens), warnings


def _finish_scoring(
    beat: Beat,
    alive: list[dict],
    by_id: dict[str, CandidateVerdict],
    result: BeatRankResult,
    kill: dict,
    *,
    prev_shot_size: str = "",
    times_used: Optional[Callable[[str], int]] = None,
    auto_note: str = "",
) -> BeatRankResult:
    """B3 điểm máy + B4 sàn 3 + chọn top-1 — dùng chung cho per-beat lẫn batch."""
    beat_dur = _need_dur(beat)
    scored: list[RankedCandidate] = []
    revivable: list[RankedCandidate] = []   # veto lý-do-thường -> trả lại khi thủng sàn
    for c in alive:
        v = by_id.get(c["asset_key"])
        if v is None:
            if auto_note:  # PA-3: pool 1 — điểm trung tính, không phải NÃO quên
                v = CandidateVerdict(id=c["asset_key"], verdict="ok", diem_nghia=5,
                                     diem_mood=5, ly_do=auto_note)
            else:  # NÃO bỏ sót -> điểm trung tính, KHÔNG loại (phân vân không veto)
                v = CandidateVerdict(id=c["asset_key"], verdict="ok", diem_nghia=5,
                                     diem_mood=5, ly_do="(NÃO bỏ sót — điểm trung tính)")
                result.warnings.append(f"beat {beat.beat_id}: NÃO bỏ sót {c['asset_key']}")
        used = times_used(c["asset_key"]) if times_used else 0
        may = _diem_may(c, beat_dur, prev_shot_size, used)
        tong = v.diem_nghia * NGHIA_W + v.diem_mood * MOOD_W + may
        rc = RankedCandidate(
            asset_key=c["asset_key"], diem_nghia=v.diem_nghia, diem_mood=v.diem_mood,
            diem_may=may, diem_tong=tong, verdict=v.verdict, veto_type=v.veto_type,
            ly_do=v.ly_do,
        )
        if v.verdict == "veto":
            kill["veto_nghia"] += 1
            if v.veto_type not in SERIOUS_VETO_TYPES:
                revivable.append(rc)
        else:
            scored.append(rc)

    # --- B4: sàn 3 tự nới + chọn top-1 -------------------------------------------------
    if len(scored) < POOL_FLOOR and revivable:
        for rc in revivable:
            rc.demoted = True
            rc.diem_tong -= DEMOTE_PENALTY
        kill["tra_lai_san"] = len(revivable)
        scored += revivable
        result.warnings.append(
            f"beat {beat.beat_id}: thủng sàn {POOL_FLOOR} — trả lại {len(revivable)} "
            "ứng viên veto-lý-do-thường (điểm trừ nặng)"
        )

    kill["con_lai"] = len(scored)
    # sort ổn định theo điểm giảm dần -> hòa điểm giữ thứ tự relevance của B1
    scored.sort(key=lambda rc: -rc.diem_tong)
    result.ranked = scored

    if not scored:
        result.needs_human = True
        result.warnings.append(f"beat {beat.beat_id}: pool trống sau veto nghĩa")
        return result

    top = scored[0]
    result.chosen_key = top.asset_key
    result.chosen_ly_do = top.ly_do
    if top.demoted:
        result.warnings.append(
            f"beat {beat.beat_id}: chọn từ hàng tự-hạ-cấp ({top.veto_type or 'khac'}) — nên soát tay"
        )
    return result


def _diem_may(c: dict, beat_dur: float, prev_shot_size: str, used: int) -> float:
    """Điểm MÁY (số học thuần): variety c7 + độ-dài-khớp + chưa-dùng-lại P7 + điểm nhô ytref
    + nguồn mẫu REF.
    Call site DUY NHẤT ở _finish_scoring — per-beat (rank_beat) lẫn batch PA-1
    (rank_beat_prescored) cùng đi qua đây (P5 ytref §3h: bonus chảy CẢ 2 đường)."""
    s = 0.0
    tag = (c.get("shot_size") or "").strip()
    if tag and prev_shot_size:  # thiếu tag -> 0, KHÔNG trừ (c7: không bao giờ là lý do loại)
        s += VARIETY_BONUS if tag != prev_shot_size else -VARIETY_BONUS
    dur = c.get("duration")
    if dur is not None and dur >= beat_dur * PREFER_DURATION_RATIO:
        s += DURATION_BONUS
    if used == 0:
        s += UNUSED_BONUS
    if c.get("peak_value"):  # ytref §3h: khán giả tua lại đoạn này trên video nguồn
        s += PEAK_BONUS
    if c.get("is_ref"):  # REF: cảnh từ nguồn mẫu của bài — editor đã khoanh đề tài
        s += REF_BONUS
    if c.get("is_boost"):  # BOOST: cảnh KHO match sở thích khán giả (nhãn ở _gather)
        s += BOOST_BONUS
    return s
