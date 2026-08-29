# -*- coding: utf-8 -*-
# PB13 — volume SFX editor theo ngữ cảnh CÓ VOICE vs KHÔNG VOICE (đọc-only 3 draft SP1)
# SFX = đoạn audio đặt ≤40s, không phải voice/nhạc/drone (nhạc+drone đặt cả bài, đoạn dài).
import json
import math
import statistics as stx
from pathlib import Path

DRAFTS = [
    r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 001",
    r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 003",
    r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 004",
]
SEC = 1_000_000
VOICE_HINTS = ("voice", "hook", "space - ", "spcae", "pscae")
WHOOSH = ("whoosh", "swoosh", "woosh", "swish", "vụt", "vujt")
SFX_SEG_MAX = 40.0   # đoạn ≤40s = SFX/ambient cục bộ; dài hơn = nhạc/drone (PB10: đặt cả bài)


def db(v):
    return 20 * math.log10(v) if v > 0 else float("-inf")


def merge(iv):
    out = []
    for s, e in sorted(iv):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def overlap(a0, a1, iv):
    return sum(max(0.0, min(a1, e) - max(a0, s)) for s, e in iv)


def stats(vols):
    if not vols:
        return "—"
    med = stx.median(vols)
    q = sorted(vols)
    lo, hi = q[len(q) // 4], q[(3 * len(q)) // 4]
    return f"n={len(vols)} median {med:.2f} ({db(med):+.1f}dB) | IQR {lo:.2f}–{hi:.2f}"


for folder in DRAFTS:
    d = json.loads((Path(folder) / "draft_content.json").read_text(encoding="utf-8"))
    name_of = {a["id"]: (a.get("name") or "") for a in d["materials"].get("audios", [])}
    auds = [t for t in d["tracks"] if t.get("type") == "audio" and t.get("segments")]

    def voiceness(t):
        n = sum(1 for s in t["segments"]
                if any(h in name_of.get(s.get("material_id"), "").lower() for h in VOICE_HINTS))
        return n / len(t["segments"])

    vtracks = [t for t in auds if voiceness(t) >= 0.6]
    if not vtracks:
        vtracks = [max(auds, key=lambda t: len(t["segments"]))]
    vint = merge([(s["target_timerange"]["start"] / SEC,
                   (s["target_timerange"]["start"] + s["target_timerange"]["duration"]) / SEC)
                  for t in vtracks for s in t["segments"]])
    v_start, v_end = vint[0][0], vint[-1][1]

    groups = {"voiced": [], "novoice": [], "mixed": []}
    music_vols, kf_count = [], 0
    for t in auds:
        if t in vtracks:
            continue
        for s in t["segments"]:
            nm = name_of.get(s.get("material_id"), "").lower()
            if any(h in nm for h in VOICE_HINTS):
                continue
            a0 = s["target_timerange"]["start"] / SEC
            dur = s["target_timerange"]["duration"] / SEC
            a1 = a0 + dur
            vol = s.get("volume", 1.0)
            if s.get("common_keyframes"):
                kf_count += 1
            if dur > SFX_SEG_MAX:
                music_vols.append(vol)
                continue
            if a1 < v_start or a0 > v_end:   # intro/outro ngoài vùng voice — không phải ô thở
                continue
            frac = overlap(a0, a1, vint) / dur if dur else 1.0
            cls = "voiced" if frac >= 0.6 else ("novoice" if frac <= 0.15 else "mixed")
            groups[cls].append((vol, dur, nm))

    print("=" * 96)
    print(f"{Path(folder).name} | voice {len(vtracks)} track, phủ {v_start:.0f}–{v_end:.0f}s | seg có keyframe: {kf_count}")
    print(f"  nhạc/drone (đoạn >40s):        {stats(music_vols)}")
    for cls, label in (("voiced", "SFX ĐÈ VOICE (≥60% trùng)"), ("novoice", "SFX KHÔNG VOICE (≤15% trùng)"),
                       ("mixed", "SFX lai (15–60%)")):
        rows = groups[cls]
        vols = [v for v, _, _ in rows]
        no_wh = [v for v, _, nm in rows if not any(h in nm for h in WHOOSH)]
        print(f"  {label:31}: {stats(vols)}")
        print(f"  {'':31}  (bỏ whoosh: {stats(no_wh)})")
        top = sorted(rows, key=lambda r: -r[0])[:4]
        names = " · ".join(f"{nm[:26]} {v:.2f}" for v, _, nm in top)
        print(f"  {'':31}  to nhất: {names}")
