# -*- coding: utf-8 -*-
"""Quét điểm cắt voice của editor SP1-003: transcribe voice bằng faster-whisper
rồi chiếu từng điểm cắt (source time) lên chữ — editor cắt sau TỪ gì, trước TỪ gì."""
import json, sys, os
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
DRAFT = Path(r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 003")
OUT = Path(__file__).parent / "sp1003_cut_scan"
OUT.mkdir(exist_ok=True)

d = json.load(open(DRAFT / "draft_content.json", encoding="utf-8"))
track = next(t for t in d["tracks"] if t["type"] == "audio" and len(t["segments"]) > 100)
mats = {a["id"]: a.get("name", "") for a in d["materials"].get("audios", [])}
segs = sorted(track["segments"], key=lambda s: s["target_timerange"]["start"])

# file voice = material có >=2 segment (junction cùng file mới phân tích được)
from collections import Counter
usage = Counter(mats[s["material_id"]] for s in segs)
voice_files = [n for n, c in usage.items() if c >= 2]
print("file voice can transcribe:", voice_files, flush=True)

from autoedit.align.whisper_local import FasterWhisperAligner
al = FasterWhisperAligner(model_size="small", language="en")
words_by_file = {}
for name in voice_files:
    cache = OUT / (name.replace(" ", "_") + ".words.json")
    if cache.exists():
        words_by_file[name] = json.load(open(cache, encoding="utf-8"))
        print(f"cache: {name} ({len(words_by_file[name])} tu)", flush=True)
        continue
    path = DRAFT / "materials" / name
    if not path.exists():
        print(f"BO QUA {name}: khong thay file", flush=True)
        continue
    ws = al.transcribe(path)
    words_by_file[name] = [{"text": w.text, "start": w.start, "end": w.end} for w in ws]
    json.dump(words_by_file[name], open(cache, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"transcribed: {name} ({len(ws)} tu)", flush=True)

# ---- chiếu điểm cắt lên chữ ----
SENT, CLAUSE = (".", "?", "!"), (",", ";", ":")
rows = []
for a, b in zip(segs, segs[1:]):
    # CapCut nhân bản material (nhiều id cho cùng 1 file) — so theo TÊN file
    name = mats[a["material_id"]]
    if name != mats[b["material_id"]] or name not in words_by_file:
        continue
    cut = (a["source_timerange"]["start"] + a["source_timerange"]["duration"]) / 1e6
    tgap = (b["target_timerange"]["start"] - a["target_timerange"]["start"] - a["target_timerange"]["duration"]) / 1e6
    ws = words_by_file[name]
    before = [w for w in ws if w["end"] <= cut + 0.08]
    after = [w for w in ws if w["start"] >= cut - 0.08 and w not in before]
    if not before or not after:
        continue
    w0, w1 = before[-1], after[0]
    t = w0["text"].rstrip("\"')")
    kind = "KET_CAU" if t.endswith(SENT) else ("KET_MENH_DE" if t.endswith(CLAUSE) or t.endswith(("-", "—")) else "GIUA_MENH_DE")
    natural = round(w1["start"] - w0["end"], 2)
    ctx_b = " ".join(x["text"] for x in before[-6:])
    ctx_a = " ".join(x["text"] for x in after[:6])
    rows.append({"file": name, "cut_s": round(cut, 2), "kind": kind, "gap_chen": round(tgap, 2),
                 "nghi_tu_nhien": natural, "truoc": ctx_b, "sau": ctx_a})

json.dump(rows, open(OUT / "cut_points.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
c = Counter(r["kind"] for r in rows)
print("\n=== PHAN LOAI", len(rows), "DIEM CAT CUNG FILE ===", flush=True)
print(dict(c), flush=True)
print("done", flush=True)
