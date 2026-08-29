"""Thống kê DNA niche đợt 1 (PB5 — spec MO_TA_VAN_HANH_TAG_GLM §8).

Code THUẦN 0 token, chạy lại được khi thêm draft mới. Nguồn số: timeline draft nguồn
(ĐỌC-ONLY, qua `ingest.read_timeline`) + tag trong cache.db (khớp cảnh theo scene_index
của `read_draft_scenes`). Tín hiệu theo phần 5 của 4 foundation:
- d1 pacing: mật độ cắt/phút, phân bố độ dài shot, hold ≥HOLD_S, độ dài theo 4 khúc
  vị trí (xấp xỉ hook/thân/cao trào/kết — chưa có chức năng đoạn ngữ nghĩa) + 45s đầu.
- d2 thở: ô thở = khoảng voice trống ≥MIN_BREATH_S — tần suất/phút thoại, phân bố độ
  dài, footage trong ô thở, 1 hay chuỗi shot. (Ô thở "sau loại câu nào": cần transcript
  nguồn — đợt sau.)
- c7: % cỡ cảnh, nhịp đặc tả (mấy shot 1 close-up), chuỗi 3 cỡ cảnh điển hình.
- c6: scene_type/subject lặp nhiều nhất (gợi ý signature/) + hook mở bằng gì.
"""

from __future__ import annotations

import json
import sqlite3
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from autoedit.library.ingest import read_draft_scenes, read_timeline

HOLD_S = 5.0        # d1: shot ≥5s = cú hold
MIN_BREATH_S = 1.0  # d2: voice trống ≥1s mới tính ô thở
HOOK_S = 45.0       # c6/d1: "hook" xấp xỉ = 45 giây đầu
MEGA_SHOT_S = 30.0  # user chốt 2026-07-07 (PB9): shot >30s = mega-segment/compilation,
                    # BỎ QUA không đếm vào thống kê pacing (mọi niche) — 1 khúc 839s từng
                    # thổi lệch chuẩn 3,1→32,9s làm validator Mảnh B kêu oan. Đếm riêng.
MEGA_BREATH_S = 60.0  # user chốt 2026-07-07: ô thở >60s (vd đoạn draft thiếu voice 842s)
                      # cũng BỎ QUA như shot, mọi niche. Đếm riêng, không mất dấu.
_QUARTER_NAMES = ("Q1 (~hook)", "Q2 (thân)", "Q3 (thân/cao trào)", "Q4 (kết)")


def _stats(vals: list[float]) -> dict:
    if not vals:
        return {"n": 0, "mean": 0.0, "median": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    return {"n": len(vals), "mean": round(statistics.fmean(vals), 2),
            "median": round(statistics.median(vals), 2),
            "std": round(statistics.pstdev(vals), 2),
            "min": round(min(vals), 2), "max": round(max(vals), 2)}


def _gaps(voice: list[tuple[float, float]], end: float) -> list[tuple[float, float]]:
    """Khoảng trống voice trên timeline (ô thở ứng viên): (start, dur), gộp voice chồng lấn."""
    merged: list[list[float]] = []
    for v0, v1 in voice:
        if merged and v0 <= merged[-1][1] + 0.05:
            merged[-1][1] = max(merged[-1][1], v1)
        else:
            merged.append([v0, v1])
    out, cur = [], 0.0
    for v0, v1 in merged:
        if v0 - cur >= MIN_BREATH_S:
            out.append((cur, v0 - cur))
        cur = max(cur, v1)
    if end - cur >= MIN_BREATH_S:
        out.append((cur, end - cur))
    return out


def compute_dna(conn: sqlite3.Connection, niche: str, draft_dirs: list[Path]) -> dict:
    """Gộp thống kê DNA từ ≥1 draft nguồn + tag db. Trả dict (in bảng ở CLI)."""
    shot_durs: list[float] = []          # d1: segment video timeline (≤MEGA_SHOT_S)
    quarter_durs: list[list[float]] = [[], [], [], []]
    hook_durs: list[float] = []
    timeline_total = voice_total = 0.0
    mega_n, mega_s = 0, 0.0              # shot >30s: đếm riêng, không vào thống kê
    mega_b_n, mega_b_s = 0, 0.0          # ô thở >60s: như trên
    breaths: list[float] = []
    breath_scene_types: Counter = Counter()
    breath_shot_sizes: Counter = Counter()
    breath_shot_counts: list[int] = []   # d2: 1 hay chuỗi shot trong 1 ô thở
    ordered_sizes: list[str] = []        # c7: cỡ cảnh theo thứ tự timeline (mọi draft)
    hook_types: Counter = Counter()      # c6: hook mở bằng gì

    for draft in draft_dirs:
        shots, voice = read_timeline(draft)
        if not shots:
            continue
        end = max(t0 + d for t0, d in shots)
        timeline_total += end
        voice_total += sum(v1 - v0 for v0, v1 in voice)
        for t0, d in shots:
            if d > MEGA_SHOT_S:
                mega_n += 1
                mega_s += d
                continue
            shot_durs.append(d)
            quarter_durs[min(3, int(t0 / end * 4))].append(d)
            if t0 < HOOK_S:
                hook_durs.append(d)
        gaps = _gaps(voice, end) if voice else []
        mega_b_n += sum(1 for _, gd in gaps if gd > MEGA_BREATH_S)
        mega_b_s += sum(gd for _, gd in gaps if gd > MEGA_BREATH_S)
        gaps = [(g0, gd) for g0, gd in gaps if gd <= MEGA_BREATH_S]
        breaths.extend(d for _, d in gaps)

        # khớp cảnh đã tag -> dòng db theo (source_video, scene_start): bền qua đổi
        # scheme scene_index (ytref §3g đổi index timeline -> theo-nguồn; draft nạp
        # trước/sau fix đều khớp — index thì lệch scheme). Chỉ own draft (viral bóp
        # 6s làm scene_start db lệch draft, nhưng dna không quét draft viral).
        # cảnh "trong ô thở" = target range đè lên khoảng trống voice ≥0.5s
        scenes, _ = read_draft_scenes(draft)
        rows = {(r["source_video"], round(r["scene_start"], 3)): r for r in conn.execute(
            "SELECT * FROM library_assets WHERE niche=? AND folder_path=?",
            (niche, f"nap/{draft.name}"))}

        def _in_gap(sc, g0: float, gd: float) -> bool:
            s0, s1 = sc.target_start, sc.target_start + sc.target_duration
            return min(s1, g0 + gd) - max(s0, g0) >= 0.5

        for sc in scenes:
            row = rows.get((str(sc.source), round(sc.start, 3)))
            if row is None:
                continue
            ordered_sizes.append(row["shot_size"])
            if any(_in_gap(sc, g0, gd) for g0, gd in gaps):
                breath_scene_types[row["scene_type"]] += 1
                breath_shot_sizes[row["shot_size"]] += 1
            if sc.target_start < HOOK_S:
                hook_types[f'{row["scene_type"]}/{row["shot_size"]}'] += 1
        for g0, gd in gaps:
            n_in = sum(1 for sc in scenes if _in_gap(sc, g0, gd))
            breath_shot_counts.append(n_in)

    # c6/c7 từ db (mọi asset niche, kể cả folder rời — gồm viral từ gói CHỌN c8:
    # phân bố kho khớp pool phễu dùng được)
    all_rows = [dict(r) for r in conn.execute(
        "SELECT scene_type, shot_size, subject FROM library_assets WHERE niche=?", (niche,))]
    type_counts = Counter(r["scene_type"] for r in all_rows if r["scene_type"])
    subject_counts = Counter(r["subject"].strip().lower() for r in all_rows if r["subject"])
    size_counts = Counter(s for s in ordered_sizes if s)
    n_sized = sum(size_counts.values())
    n_cu = size_counts.get("close_up", 0) + size_counts.get("extreme_close_up", 0)
    chains = Counter("→".join(ordered_sizes[i:i + 3]) for i in range(len(ordered_sizes) - 2))
    holds = [d for d in shot_durs if d >= HOLD_S]

    return {
        "niche": niche, "drafts": len(draft_dirs),
        "timeline_min": round(timeline_total / 60, 1),
        "pacing": {
            "shots": len(shot_durs),
            # mật độ tính trên thời lượng ĐÃ TRỪ mega (14 phút compilation không phải nhịp cắt).
            # Mega chồng NHIỀU track (life-in 2026-07-15: 342 mega 80.148s > timeline 75.642s
            # → hiệu ÂM, cuts_per_min rơi 0 làm validator tự tắt) → fallback tổng shot thật.
            "cuts_per_min": round(len(shot_durs) / ((timeline_total - mega_s) / 60), 1)
                            if timeline_total - mega_s > 0
                            else (round(len(shot_durs) / (sum(shot_durs) / 60), 1)
                                  if shot_durs else 0),
            "mega_segments": {"n": mega_n, "total_s": round(mega_s, 1)},
            "shot_len": _stats(shot_durs),
            "holds": {"n": len(holds), "share": round(len(holds) / len(shot_durs), 2) if shot_durs else 0,
                      "median_s": round(statistics.median(holds), 2) if holds else 0},
            "by_quarter": {name: _stats(q) for name, q in zip(_QUARTER_NAMES, quarter_durs)},
            "hook45": _stats(hook_durs),
        },
        "breathing": {
            "voice_min": round(voice_total / 60, 1),
            "windows": len(breaths),
            "mega_windows": {"n": mega_b_n, "total_s": round(mega_b_s, 1)},
            "per_min_voice": round(len(breaths) / (voice_total / 60), 2) if voice_total else 0,
            "len": _stats(breaths),
            "scene_types": dict(breath_scene_types.most_common()),
            "shot_sizes": dict(breath_shot_sizes.most_common()),
            "shots_per_window": _stats([float(c) for c in breath_shot_counts if c > 0]),
        },
        "shot_grammar": {
            "distribution": {k: round(v / n_sized, 2) for k, v in size_counts.most_common()} if n_sized else {},
            "cu_cadence": round(n_sized / n_cu, 1) if n_cu else None,  # N shot thì 1 đặc tả
            "top_chains": chains.most_common(5),
        },
        "signature": {
            "top_scene_types": type_counts.most_common(8),
            "top_subjects": subject_counts.most_common(10),
            "hook_opens_with": hook_types.most_common(6),
        },
    }


# ---------------------------------------------------------------------------
# Consumer DNA d1 (MO_TA_VAN_HANH_DNA_D1 §2a + §2c) — dna.json + pacing validator
# ---------------------------------------------------------------------------
def save_dna(dna: dict, niche_d: Path, draft_dirs: list[Path]) -> Path:
    """§2a: ghi dna.json vào folder niche — DNA sống độc lập trong thư viện
    (lúc dựng video, draft nguồn ổ ngoài có thể không cắm)."""
    out = dict(dna)
    out["measured_at"] = datetime.now(timezone.utc).isoformat()
    out["source_drafts"] = [str(d) for d in draft_dirs]
    niche_d.mkdir(parents=True, exist_ok=True)
    path = niche_d / "dna.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_dna(niche_d: Path) -> dict | None:
    """Đọc dna.json của niche; thiếu file / JSON hỏng -> None (validator tự tắt, fail-open)."""
    path = niche_d / "dna.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def check_pacing(shot_durs: list[float], total_min: float, dna: dict) -> list[str]:
    """§2c Mảnh B: so shot thật của video vừa ráp với DNA niche -> 0-2 dòng cảnh báo.

    CHỈ cảnh báo, KHÔNG chặn (luật filter-overload-guard). Ngưỡng chốt 2026-07-07:
    (i) đều tăm tắp = lệch chuẩn < ½ DNA; (ii) mật độ ngoài [½×, 2×] DNA.
    DNA suy biến (std/cuts_per_min = 0, mẫu quá mỏng) -> tín hiệu đó tự tắt.
    """
    warns: list[str] = []
    pacing = dna.get("pacing", {})
    dna_std = pacing.get("shot_len", {}).get("std", 0) or 0
    dna_cpm = pacing.get("cuts_per_min", 0) or 0
    if len(shot_durs) >= 2 and dna_std > 0:
        std = statistics.pstdev(shot_durs)
        if std < dna_std / 2:
            warns.append(
                f"pacing DNA: shot đều tăm tắp (lệch chuẩn {std:.2f}s < ½ DNA {dna_std}s)"
                " — thiếu xen kẽ dài/ngắn kiểu editor, cân nhắc phá đều vài chỗ")
    if shot_durs and total_min > 0 and dna_cpm > 0:
        cpm = len(shot_durs) / total_min
        if not (dna_cpm / 2 <= cpm <= dna_cpm * 2):
            huong = "nhanh" if cpm > dna_cpm else "chậm"
            warns.append(
                f"pacing DNA: {cpm:.1f} cut/phút — cắt quá {huong} so với chuẩn niche "
                f"({dna_cpm} cut/phút, ngưỡng [{dna_cpm / 2:.1f}; {dna_cpm * 2:.1f}])")
    return warns
