# -*- coding: utf-8 -*-
# PB14 — editor có PUNCH-IN trên video không? (đọc-only 4 draft SP1 — C đợt 4 M0)
# Đo 2 dạng punch có thể có:
#   (A) keyframe scale GIỮA clip (khác Ken Burns máy: keyframe chỉ ở 2 mép)
#   (B) punch-bằng-CẮT: 2 segment liền kề CÙNG material, nguồn nối tiếp, scale tĩnh nhảy ≥5%
# Tương quan từng cú với: TEXT hiện lên (≤0.5s/≤1s) + đang TRONG voice (nhấn từ khóa?)
import json
import statistics as stx
from pathlib import Path

DRAFTS = [
    r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 001",
    r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 003",
    r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 004",
    r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 012",
]
SEC = 1_000_000
VOICE_HINTS = ("voice", "hook", "space - ", "spcae", "pscae")
EDGE = 0.5      # keyframe cách mép ≤0.5s = mép (Ken Burns/fade); sâu hơn = GIỮA clip
JUMP_MIN = 0.05  # scale tĩnh nhảy ≥5% giữa 2 nửa cắt = punch-bằng-cắt


def merge(iv):
    out = []
    for s, e in sorted(iv):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def inside(t, iv):
    return any(s <= t <= e for s, e in iv)


def near(t, marks, tol):
    return any(abs(t - m) <= tol for m in marks)


for folder in DRAFTS:
    d = json.loads((Path(folder) / "draft_content.json").read_text(encoding="utf-8"))
    vids = {m["id"]: m for m in d["materials"].get("videos", [])}
    name_of_a = {a["id"]: (a.get("name") or "") for a in d["materials"].get("audios", [])}

    # mốc TEXT hiện lên (mọi track text) + khoảng voice (khuôn PB13)
    text_starts = [s["target_timerange"]["start"] / SEC
                   for t in d["tracks"] if t.get("type") == "text"
                   for s in t.get("segments", [])]
    auds = [t for t in d["tracks"] if t.get("type") == "audio" and t.get("segments")]
    vtracks = [t for t in auds if sum(
        1 for s in t["segments"]
        if any(h in name_of_a.get(s.get("material_id"), "").lower() for h in VOICE_HINTS)
    ) / len(t["segments"]) >= 0.6] or ([max(auds, key=lambda t: len(t["segments"]))] if auds else [])
    vint = merge([(s["target_timerange"]["start"] / SEC,
                   (s["target_timerange"]["start"] + s["target_timerange"]["duration"]) / SEC)
                  for t in vtracks for s in t["segments"]])

    n_seg = n_kf_edge = 0
    mid_events = []   # (target_t, jump_ratio, mô tả)  — dạng A: 1 cú = 1 SEGMENT có kf giữa
    cut_events = []   # (target_t, jump_ratio, mô tả)  — dạng B
    vtracks_video = [t for t in d["tracks"] if t.get("type") == "video" and t.get("segments")]
    main = max(vtracks_video, key=lambda t: len(t["segments"])) if vtracks_video else None
    for ti, t in enumerate(vtracks_video):
        tlab = "CHÍNH" if t is main else f"phủ#{ti}"
        prev = None
        for s in t["segments"]:
            mat = vids.get(s.get("material_id"), {})
            if mat.get("type") == "photo":
                prev = None
                continue  # punch-in C2 chỉ bàn VIDEO (ảnh = chuyện Ken Burns)
            n_seg += 1
            tt, sr = s["target_timerange"], s.get("source_timerange") or {"start": 0, "duration": tt["duration"]}
            t0, tdur = tt["start"] / SEC, tt["duration"] / SEC
            sdur = sr["duration"] / SEC

            # ---- dạng A: segment có keyframe scale giữa clip = 1 cú ----
            base_sc = ((s.get("clip") or {}).get("scale") or {}).get("x", 1.0)
            pts_all, has_mid = [], False
            for kf in s.get("common_keyframes") or []:
                if "scale" not in kf.get("property_type", "").lower():
                    continue
                for p in kf.get("keyframe_list") or []:
                    o = p["time_offset"] / SEC
                    v = p["values"][0] if p.get("values") else None
                    pts_all.append((o, v))
                    if EDGE < o < max(sdur, tdur) - EDGE:
                        has_mid = True
            if pts_all and not has_mid:
                n_kf_edge += 1
            if has_mid:
                pts_all.sort()
                vals = [v for _, v in pts_all if v]
                jump = (max(vals) / min(vals)) if vals and min(vals) > 0 else 0
                o_first = next(o for o, _ in pts_all if o > EDGE)
                tgt = t0 + (o_first - sr["start"] / SEC) * (tdur / sdur if sdur else 1.0)
                kf_txt = " ".join(f"{o:.1f}:{v:.2f}" if v is not None else f"{o:.1f}:?"
                                  for o, v in pts_all[:6])
                nm = mat.get("material_name", "") or mat.get("type", "?")
                mid_events.append((tgt, jump,
                                   f"[{tlab}] {nm[:30]} | nền {base_sc:.2f} | kf {kf_txt}"))

            # ---- dạng B: cắt đôi + scale tĩnh nhảy ----
            sc = ((s.get("clip") or {}).get("scale") or {}).get("x", 1.0)
            if prev is not None:
                p_s, p_sc = prev
                same_mat = p_s.get("material_id") == s.get("material_id")
                p_tt, p_sr = p_s["target_timerange"], p_s.get("source_timerange") or {}
                adj_target = abs((p_tt["start"] + p_tt["duration"]) - tt["start"]) / SEC < 0.1
                adj_source = p_sr and abs((p_sr["start"] + p_sr["duration"]) - sr["start"]) / SEC < 0.3
                if same_mat and adj_target and adj_source and p_sc > 0 \
                        and abs(sc - p_sc) / p_sc >= JUMP_MIN:
                    cut_events.append((t0, sc / p_sc, mat.get("material_name", "")[:36]))
            prev = (s, sc)

    def corr(events):
        if not events:
            return "—"
        ts = [t for t, _, _ in events]
        jumps = [j for _, j, _ in events if j]
        t05 = sum(1 for t in ts if near(t, text_starts, 0.5))
        t10 = sum(1 for t in ts if near(t, text_starts, 1.0))
        invoice = sum(1 for t in ts if inside(t, vint))
        jm = f"zoom x{stx.median(jumps):.2f}" if jumps else "zoom ?"
        return (f"n={len(events)} | {jm} | sát TEXT ≤0.5s: {t05} · ≤1s: {t10} | "
                f"trong voice: {invoice}")

    print("=" * 96)
    print(f"{Path(folder).name} | video-seg (video thật, mọi track video): {n_seg} | "
          f"text mốc: {len(text_starts)} | seg keyframe-scale chỉ-mép: {n_kf_edge}")
    print(f"  (A) keyframe scale GIỮA clip : {corr(mid_events)}")
    print(f"  (B) punch-bằng-CẮT (scale nhảy): {corr(cut_events)}")
    for label, evs in (("A", mid_events), ("B", cut_events)):
        for t, j, nm in evs[:6]:
            print(f"      [{label}] {t:7.1f}s x{j:.2f} {nm}")
    if len(mid_events) > 6 or len(cut_events) > 6:
        print(f"      ... (A còn {max(0, len(mid_events)-6)}, B còn {max(0, len(cut_events)-6)})")
