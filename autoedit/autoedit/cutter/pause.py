"""Giãn nghỉ máy theo DNA nhịp nghỉ editor — hình thở 3.0 (MO_TA_VAN_HANH_HINH_THO_3.md).

HỌC từ 464 điểm cắt của 3 project editor (SP1-001/003/004 — artifact pause_dna.json,
NHAT_KY §HOC-DNA-NHIP): editor biến ~50% ranh giới câu thành điểm dừng thật (nghe-ra
p50 1,55s), chọn lọc 1,6 điểm/phút kết mệnh đề thành nửa nhịp (p50 0,95s), tổng chèn
+8-13% duration. Khung top-N (đợt 1+1.5) nghỉ hưu — mật độ + độ sâu giờ lấy từ phân bố
DNA bằng QUANTILE-RANK MAPPING: điểm voice tự nghỉ dài hơn nhận target nghe-ra sâu hơn
(giữ ngữ điệu riêng của bài, chỉ nâng cả dàn lên tầm editor).

AN TOÀN NGHĨA CÂU — 2 khóa đồng thời, thiếu 1 là bỏ (bất di bất dịch):
1. Khóa dấu: beat.text kết dấu KẾT CÂU .?! (tầng câu, δ≤1,1) hoặc KẾT MỆNH ĐỀ ,;:—–
   (tầng mệnh đề, δ≤0,7). GIỮA MỆNH ĐỀ: máy KHÔNG BAO GIỜ tự chọn — chỉ đạo diễn
   đánh dấu rhetorical_pause (câu đinh ≤0,3 điểm/phút, vd "…cosmic house ‖ But one")
   và vẫn phải qua khóa 2.
2. Khóa nghỉ thật: voice có nghỉ tự nhiên >= MIN_NATURAL_GAP tại đúng chỗ đó
   (chỉ GIÃN nghỉ sẵn có, không tạo nghỉ từ hư không).

plan_micro_pauses là pure function (DNA truyền vào, load tách riêng) — deterministic,
chạy lại cut ra đúng một kết quả.
"""

from __future__ import annotations

import json

from autoedit.project import Beat

SENT_END = (".", "?", "!")
CLAUSE_END = (",", ";", ":", "—", "–")
_TRAIL = "\"')»”’"          # dấu bọc có thể đứng sau dấu kết câu/mệnh đề
MIN_NATURAL_GAP = 0.30       # khóa 2: nghỉ thật tối thiểu (giây)
GUARD_S = 3.0                # 2 điểm giãn (hoặc giãn vs thở) cách nhau tối thiểu
BUDGET_RATIO = 0.15          # trần tổng chèn thở+giãn / duration nguồn. DNA đo editor
                             # 8,3-16,8%; ta cần cao hơn trung vị editor vì voice ta nghỉ
                             # nền NÔNG hơn TTS editor ~0,35s/điểm (0,5 vs 0,85) — 13%
                             # từng bóp chết tầng mệnh đề (run Jupiter 2026-07-08)

# DNA pooled 3 project (pause_dna.json 2026-07-08) — fallback khi chưa biết niche /
# thiếu file. anchors = nghe-ra đích tại quantile [p10 p25 p50 p75 p90]; δ = đích - nghỉ.
# Trần δ câu 1,1: gap timeline ≤1,2 — không giẫm vùng J-cut (1,2) / ducking (1,5);
# phần sâu hơn thuộc tầng thở của đạo diễn.
POOLED_DNA = {
    "sent":   {"per_min": 4.92, "anchors": [1.06, 1.28, 1.55, 1.90, 2.73],
               "d_min": 0.15, "d_max": 1.10},
    "clause": {"per_min": 1.60, "anchors": [0.66, 0.76, 0.95, 1.19, 1.39],
               "d_min": 0.15, "d_max": 0.70},
    # câu đinh (NÃO đánh dấu beat KHÔNG dấu): nghe-ra đích ~1,0s (DNA giữa-mệnh-đề p50)
    "rhet":   {"per_min": 0.30, "target": 1.0, "d_min": 0.20, "d_max": 0.60},
}
_ANCHOR_F = [0.10, 0.25, 0.50, 0.75, 0.90]


def load_pause_dna(niche: str | None) -> dict:
    """Đọc pause_dna.json trong folder niche (cạnh dna.json) — FAIL-OPEN về POOLED_DNA.

    Cut chạy TRƯỚC source nên video mới thường chưa có project.niche → pooled (hiện
    chính là DNA space); chạy lại cut sau source thì file niche thắng.
    """
    if not niche:
        return POOLED_DNA
    try:
        from autoedit.library.profile import niche_dir, resolve_library_root

        path = niche_dir(niche, root=resolve_library_root(None)) / "pause_dna.json"
        kinds = json.loads(path.read_text(encoding="utf-8"))["pooled"]["kinds"]
        out = {tier: dict(cfg) for tier, cfg in POOLED_DNA.items()}
        for tier, kind in (("sent", "KET_CAU"), ("clause", "KET_MENH_DE")):
            q = kinds[kind]["nghe_ra"]
            out[tier]["anchors"] = [q["p10"], q["p25"], q["p50"], q["p75"], q["p90"]]
            out[tier]["per_min"] = kinds[kind]["per_min"]
        return out
    except Exception:
        return POOLED_DNA


# --- SHOT THỞ 2.0 (MO_TA_VAN_HANH_SHOT_THO.md §6) — LỚP RIÊNG với giãn nghỉ voice ---
# DNA lớp-hình-thở đo lại 2026-07-08 (tách khỏi lớp voice-nghỉ theo user chỉ ra):
# footage thật 1,7-12,1s, 4 ô 8,4-12,3s từng bị lọc nhầm "nhiễu ≥8s". Sàn 4s = user chốt
# theo editor; p50/p90 từ số đo. NÃO vẫn quyết CHỖ + rank thô; máy map độ sâu cuối.
BREATH_POOLED = {
    "footage_anchors": [4.0, 4.5, 5.3, 6.8, 8.5],  # p10-p90 GIÂY footage của ô
    "footage_cap": 10.0,
    "hold": 0.5,                 # giữ hình cũ trước nhát cắt (DNA 0,4-0,9)
    "k_thresholds": [5.5, 8.5],  # footage <5,5 -> 1 miếng; <8,5 -> {1,2}; còn lại {1,2,3}
    "k_fractions": {2: [0.58, 0.42], 3: [0.42, 0.33, 0.25]},  # miếng đầu dài nhất (mẫu editor)
    "min_piece": 1.5,
}


def load_breath_dna(niche: str | None) -> dict:
    """Block `pooled.breath` trong pause_dna.json của niche — FAIL-OPEN về BREATH_POOLED.

    Niche mới: scan DNA phải tách lớp ô (hold ≤1,2 + footage ≥1,5 = hình thở) và KHÔNG
    lọc phăng ô ≥8s (nhận diện montage riêng) — bài học space, MO_TA_SHOT_THO §6.2C.
    """
    if not niche:
        return BREATH_POOLED
    try:
        from autoedit.library.profile import niche_dir, resolve_library_root

        path = niche_dir(niche, root=resolve_library_root(None)) / "pause_dna.json"
        blk = json.loads(path.read_text(encoding="utf-8"))["pooled"]["breath"]
        out = dict(BREATH_POOLED)
        out.update(blk)
        # JSON key luôn là str -> đổi lại int cho k_fractions
        out["k_fractions"] = {int(k): v for k, v in out["k_fractions"].items()}
        return out
    except Exception:
        return BREATH_POOLED


def reset_breathing_to_base(beats: list[Beat]) -> None:
    """Reset breathing_after về số NÃO gốc trước khi plan — chạy lại cut không cộng dồn.

    breathing_base=0 mà breathing_after>0 = project cũ (trước 2.0) -> backfill base.
    """
    for b in beats:
        if b.breathing_base <= 0 and b.breathing_after > 0:
            b.breathing_base = b.breathing_after
        b.breathing_after = b.breathing_base


def plan_breath_depth(beats: list[Beat], dna: dict | None = None) -> dict[int, float]:
    """Kéo sâu ô đạt ngưỡng lên tầm editor — {beat_id: breathing_after MỚI}.

    Rank (breathing NÃO, cuối chương, vị trí) -> quantile-map lên footage_anchors
    (ô NÃO cho sâu hơn / cuối chương nhận đích sâu hơn). Số mới = hold + footage.
    Gọi SAU plan_micro_pauses (budget micro tính theo số NÃO — editor đo 8-13% chèn
    giãn KHÔNG gồm ô thở, rows/holes là 2 list riêng). Beat cuối video không bao giờ
    (predicate loại sẵn).
    """
    from autoedit.packager.coverage import breath_shot_beat_ids

    dna = dna or BREATH_POOLED
    ids = breath_shot_beat_ids(beats)
    if not ids:
        return {}
    pos = {b.beat_id: i for i, b in enumerate(beats)}

    def rank_key(bid: int):
        i = pos[bid]
        is_ch = i + 1 < len(beats) and beats[i + 1].chapter != beats[i].chapter
        return (beats[i].breathing_after, 1 if is_ch else 0, bid)

    order = sorted(ids, key=rank_key)
    out: dict[int, float] = {}
    for rank, bid in enumerate(order):
        f = (rank + 0.5) / len(order)
        footage = min(_target(f, dna["footage_anchors"]), dna["footage_cap"])
        out[bid] = round(dna["hold"] + footage, 2)
    return out


def _ends_sentence(text: str) -> bool:
    return text.rstrip().rstrip(_TRAIL).endswith(SENT_END)


def _ends_clause(text: str) -> bool:
    return text.rstrip().rstrip(_TRAIL).endswith(CLAUSE_END)


def _target(f: float, anchors: list[float]) -> float:
    """Nội suy tuyến tính nghe-ra đích theo rank fraction f∈[0,1] trên anchor p10-p90."""
    if f <= _ANCHOR_F[0]:
        return anchors[0]
    if f >= _ANCHOR_F[-1]:
        return anchors[-1]
    for i in range(len(_ANCHOR_F) - 1):
        if f <= _ANCHOR_F[i + 1]:
            w = (f - _ANCHOR_F[i]) / (_ANCHOR_F[i + 1] - _ANCHOR_F[i])
            return anchors[i] + (anchors[i + 1] - anchors[i]) * w
    return anchors[-1]


def _pick_tier(cands: list[tuple[float, int, float]], k_target: int,
               taken_pts: list[float], tier: dict) -> list[tuple[int, float, float, float]]:
    """Chọn ≤k_target điểm (nghỉ-nguồn-dài trước, guard GUARD_S) rồi map δ theo rank
    nghỉ nguồn trên phân bố nghe-ra DNA. Trả [(bid, pt, nghỉ, δ)] theo ưu tiên chọn."""
    cands.sort(key=lambda c: (-c[0], c[1]))          # (nghỉ, bid, pt)
    chosen: list[tuple[float, int, float]] = []
    for nghi, bid, pt in cands:
        if len(chosen) >= k_target:
            break
        if any(abs(pt - q) < GUARD_S for q in taken_pts):
            continue
        chosen.append((nghi, bid, pt))
        taken_pts.append(pt)
    n = len(chosen)
    delta_by_bid: dict[int, float] = {}
    for rank, (nghi, bid, _pt) in enumerate(sorted(chosen)):  # nghỉ ngắn → đích nông
        d = _target((rank + 0.5) / n, tier["anchors"]) - nghi
        delta_by_bid[bid] = round(min(max(d, tier["d_min"]), tier["d_max"]), 2)
    return [(bid, pt, nghi, delta_by_bid[bid]) for nghi, bid, pt in chosen]


def plan_micro_pauses(beats: list[Beat], dna: dict | None = None) -> dict[int, float]:
    """Chọn điểm giãn + lượng chèn δ (giây) — {beat_id: δ}.

    Thứ tự ưu tiên: câu đinh NÃO → tầng câu → tầng mệnh đề (câu đinh hiếm + quyết định
    nghĩa, không để tầng máy chặn chỗ). Trần ngân sách BUDGET_RATIO tính cả thở đạo
    diễn — chạm trần thì bỏ điểm ưu tiên thấp. Beat cuối + beat có breathing_after:
    không bao giờ được chọn.
    """
    if len(beats) < 2:
        return {}
    dna = dna or POOLED_DNA
    minutes = beats[-1].end / 60

    rhet_c: list[tuple[float, int, float]] = []
    sent_c: list[tuple[float, int, float]] = []
    clause_c: list[tuple[float, int, float]] = []
    for a, b in zip(beats, beats[1:]):
        if a.breathing_after > 0:
            continue
        gap = b.start - a.end
        if gap < MIN_NATURAL_GAP:
            continue
        item = (gap, a.beat_id, a.end)
        if _ends_sentence(a.text):
            sent_c.append(item)
        elif _ends_clause(a.text):
            clause_c.append(item)
        elif getattr(a, "rhetorical_pause", False):
            rhet_c.append(item)

    taken = [b.end for b in beats if b.breathing_after > 0]
    picked: list[tuple[int, float, float, float]] = []

    rhet = dna["rhet"]
    rhet_c.sort(key=lambda c: (-c[0], c[1]))
    # tối thiểu 1: cờ NÃO là quyết định nghĩa đã qua validator (≤1/chương) — video
    # ngắn không được nuốt cờ vì round(phút×0,3)=0
    for nghi, bid, pt in rhet_c[: max(1, round(minutes * rhet["per_min"]))]:
        if any(abs(pt - q) < GUARD_S for q in taken):
            continue
        d = round(min(max(rhet["target"] - nghi, rhet["d_min"]), rhet["d_max"]), 2)
        picked.append((bid, pt, nghi, d))
        taken.append(pt)

    picked += _pick_tier(sent_c, round(minutes * dna["sent"]["per_min"]), taken, dna["sent"])
    picked += _pick_tier(clause_c, round(minutes * dna["clause"]["per_min"]), taken,
                         dna["clause"])

    budget = beats[-1].end * BUDGET_RATIO - sum(b.breathing_after for b in beats)
    chosen: dict[int, float] = {}
    total = 0.0
    for bid, _pt, _nghi, d in picked:            # theo ưu tiên: rhet → câu → mệnh đề
        if total + d > budget:
            continue                             # điểm nhỏ hơn phía sau vẫn có thể vừa
        chosen[bid] = d
        total += d
    return chosen
