# -*- coding: utf-8 -*-
"""HỌC DNA nhịp nghỉ editor từ 3 project SP1-001/003/004 — hình thở 3.0 bước 1.

Mỗi project: transcribe voice (faster-whisper small, cache) → chiếu điểm cắt cùng-file
lên chữ → phân loại theo dấu whisper → ĐỐI CHIẾU SCRIPT GỐC tự động (vá whisper mất
dấu/nuốt liên từ — thuật toán: khớp 3 từ ngữ cảnh trước, đọc ký tự giữa 2 từ quanh điểm
cắt) → gộp phân bố NGHE RA / gap chèn / nghỉ nguồn theo loại + ô thở + J-cut + spacing
+ tỷ lệ chèn → pause_dna.json (project root) + rows per project.

Chạy: uv run python learn_pause_dna.py   (cwd = autoedit, cần faster-whisper trong env)
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"c:\Users\NBPC\Documents\Claude\Projects\tool edit padoma")
SCRATCH = Path(__file__).parent / "pause_dna"
SCRATCH.mkdir(parents=True, exist_ok=True)
OLD_CACHE = Path(r"C:\Users\NBPC\AppData\Local\Temp\claude"
                 r"\c--Users-NBPC-Documents-Claude-Projects-tool-edit-padoma"
                 r"\129fe827-6864-44f6-9f45-f89586490b49\scratchpad\sp1003_cut_scan")

PROJECTS = {
    "SP1-001": {
        "draft": Path(r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 001"),
        "script": Path(r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 001\CONTENT ENGLISH"
                       r"\scariest-place-above-below-the-sun - V2 THÊM TONE.txt"),
    },
    "SP1-003": {
        "draft": Path(r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 003"),
        "script": Path(r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 003\CONTENT ENGLISH"
                       r"\SP1-003 - CONTENT.txt"),
    },
    "SP1-004": {
        "draft": Path(r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 004"),
        "script": Path(r"E:\PROJECT NHAN BAN\SPACE 1\SP1 - 004\CONTENT ENGLISH"
                       r"\scariest-air-around-the-sun.txt"),
    },
}

SENT_P = ".?!"
CLAUSE_P = ",;:—–"
_ALIGNER = None


def sanitize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def get_words(pname: str, draft_dir: Path, name: str):
    cache = SCRATCH / f"{pname}__{sanitize(name)}.words.json"
    if cache.exists():
        return json.load(open(cache, encoding="utf-8"))
    old = OLD_CACHE / (name.replace(" ", "_") + ".words.json")
    if pname == "SP1-003" and old.exists():
        ws = json.load(open(old, encoding="utf-8"))
        json.dump(ws, open(cache, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"  cache cu: {name} ({len(ws)} tu)", flush=True)
        return ws
    path = draft_dir / "materials" / name
    if not path.exists():
        print(f"  BO QUA {name}: khong thay file trong materials", flush=True)
        return None
    global _ALIGNER
    if _ALIGNER is None:
        from autoedit.align.whisper_local import FasterWhisperAligner
        _ALIGNER = FasterWhisperAligner(model_size="small", language="en")
    print(f"  transcribing {name} ...", flush=True)
    ws = _ALIGNER.transcribe(path)
    out = [{"text": w.text, "start": w.start, "end": w.end} for w in ws]
    json.dump(out, open(cache, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"  transcribed: {name} ({len(out)} tu)", flush=True)
    return out


def normw(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def script_tokens(txt: str):
    toks = []
    for m in re.finditer(r"[A-Za-z0-9''’\-]+", txt):
        n = normw(m.group(0))
        if n:
            toks.append((n, m.start(), m.end()))
    return toks


def reconcile_kind(truoc: str, sau: str, kind_whisper: str, txt: str, toks):
    """Đối chiếu script gốc: khớp 3 từ ngữ cảnh TRƯỚC điểm cắt trong script,
    tìm từ đầu của phần SAU trong ≤6 token kế, đọc ký tự GIỮA → dấu thật.
    Trả (kind_final, verified)."""
    b = [normw(w) for w in truoc.split()]
    b = [w for w in b if w][-3:]
    a = [normw(w) for w in sau.split()]
    a = [w for w in a if w][:3]
    if not b or not a:
        return kind_whisper, False
    n = len(toks)
    for i in range(len(b) - 1, n):
        if [t[0] for t in toks[i - len(b) + 1: i + 1]] == b:
            for j in range(i + 1, min(i + 7, n)):
                if toks[j][0] in a:
                    between = txt[toks[i][2]: toks[j][1]]
                    if any(c in between for c in SENT_P):
                        return "KET_CAU", True
                    if any(c in between for c in CLAUSE_P) or re.search(r"\s-\s", between):
                        return "KET_MENH_DE", True
                    return "GIUA_MENH_DE", True
    return kind_whisper, False


def chapter_times(txt: str):
    return [int(m.group(1)) * 60 + int(m.group(2))
            for m in re.finditer(r"(?m)^\s*(\d{1,2}):(\d{2})\s+CHAPTER", txt)]


def quantiles(arr):
    s = sorted(arr)
    n = len(s)
    if n == 0:
        return {}
    q = lambda p: round(s[min(n - 1, int(n * p))], 2)
    return {"n": n, "p10": q(0.10), "p25": q(0.25), "p50": q(0.50),
            "p75": q(0.75), "p90": q(0.90), "min": round(s[0], 2), "max": round(s[-1], 2)}


def scan_project(pname: str, cfg: dict) -> dict:
    print(f"\n=== {pname} ===", flush=True)
    dc = json.load(open(cfg["draft"] / "draft_content.json", encoding="utf-8"))
    track = max((t for t in dc["tracks"] if t["type"] == "audio"),
                key=lambda t: len(t["segments"]))
    mats = {a["id"]: a.get("name", "") for a in dc["materials"].get("audios", [])}
    segs = sorted(track["segments"], key=lambda s: s["target_timerange"]["start"])
    usage = Counter(mats[s["material_id"]] for s in segs)
    vfiles = [nm for nm, c in usage.items() if c >= 2]
    print(f"  voice track: {len(segs)} seg | files >=2 seg: {vfiles}", flush=True)

    words = {}
    for nm in vfiles:
        w = get_words(pname, cfg["draft"], nm)
        if w:
            words[nm] = w

    txt = open(cfg["script"], encoding="utf-8").read()
    toks = script_tokens(txt)

    rows = []
    for a, b in zip(segs, segs[1:]):
        nm = mats[a["material_id"]]
        if nm != mats[b["material_id"]] or nm not in words:
            continue
        cut = (a["source_timerange"]["start"] + a["source_timerange"]["duration"]) / 1e6
        tl_end = (a["target_timerange"]["start"] + a["target_timerange"]["duration"]) / 1e6
        tgap = b["target_timerange"]["start"] / 1e6 - tl_end
        ws = words[nm]
        before = [w for w in ws if w["end"] <= cut + 0.08]
        after = [w for w in ws if w["start"] >= cut - 0.08 and w not in before]
        if not before or not after:
            continue
        w0, w1 = before[-1], after[0]
        t0 = w0["text"].rstrip("\"')")
        kind_w = ("KET_CAU" if t0.endswith(tuple(SENT_P))
                  else "KET_MENH_DE" if t0.endswith(tuple(",;:")) or t0.endswith(("-", "—", "–"))
                  else "GIUA_MENH_DE")
        truoc = " ".join(x["text"] for x in before[-6:])
        sau = " ".join(x["text"] for x in after[:6])
        kind, verified = reconcile_kind(truoc, sau, kind_w, txt, toks)
        rows.append({
            "file": nm, "cut_s": round(cut, 2), "tl_s": round(tl_end, 2),
            "kind": kind, "kind_whisper": kind_w, "script_verified": verified,
            "gap_chen": round(tgap, 2), "nghi_nguon": round(w1["start"] - w0["end"], 2),
            "nghe_ra": round(max(tgap, 0) + max(w1["start"] - w0["end"], 0), 2),
            "truoc": truoc, "sau": sau,
        })

    # mọi mối nối (kể cả khác file) — cho spacing + tỷ lệ chèn
    all_gaps, all_pos = [], []
    for a, b in zip(segs, segs[1:]):
        tl_end = (a["target_timerange"]["start"] + a["target_timerange"]["duration"]) / 1e6
        all_gaps.append(b["target_timerange"]["start"] / 1e6 - tl_end)
        all_pos.append(tl_end)
    spacing = [round(y - x, 2) for x, y in zip(all_pos, all_pos[1:])]

    # ô thở >=1.5s + hình bên trong (J-cut / shot riêng / thụ động)
    vids = [t for t in dc["tracks"] if t["type"] == "video"]
    vsegs = (sorted(max(vids, key=lambda t: len(t["segments"]))["segments"],
                    key=lambda s: s["target_timerange"]["start"]) if vids else [])
    holes = []
    for s1, s2 in zip(segs, segs[1:]):
        hs = (s1["target_timerange"]["start"] + s1["target_timerange"]["duration"]) / 1e6
        he = s2["target_timerange"]["start"] / 1e6
        if he - hs < 1.5:
            continue
        offs = [round(v["target_timerange"]["start"] / 1e6 - hs, 2) for v in vsegs
                if hs - 0.05 <= v["target_timerange"]["start"] / 1e6 < he - 0.05]
        holes.append({"tl_s": round(hs, 2), "dur": round(he - hs, 2), "shot_offsets": offs})

    chapters = chapter_times(txt)
    for h in holes:
        h["at_chapter"] = any(h["tl_s"] - 2 <= c <= h["tl_s"] + h["dur"] + 2 for c in chapters)

    tl_start = segs[0]["target_timerange"]["start"] / 1e6
    tl_end_all = (segs[-1]["target_timerange"]["start"]
                  + segs[-1]["target_timerange"]["duration"]) / 1e6
    tl_span = tl_end_all - tl_start
    insert_total = sum(max(g, 0) for g in all_gaps)
    src_total = tl_span - insert_total
    n_sent_script = len(re.findall(r"[.?!]+", txt))
    n_clause_script = len(re.findall(r"[,;:]|—|–", txt))

    print(f"  {len(rows)} diem cat cung-file | phan loai (da doi chieu script): "
          f"{dict(Counter(r['kind'] for r in rows))}", flush=True)
    print(f"  script_verified: {sum(1 for r in rows if r['script_verified'])}/{len(rows)}",
          flush=True)
    print(f"  o tho >=1.5s: {len(holes)} | chen tong {insert_total:.1f}s "
          f"/ nguon {src_total:.1f}s = +{insert_total / src_total * 100:.1f}%", flush=True)

    return {"rows": rows, "holes": holes, "spacing": spacing,
            "tl_minutes": round(tl_span / 60, 2), "src_minutes": round(src_total / 60, 2),
            "insert_total_s": round(insert_total, 1),
            "insert_ratio_pct": round(insert_total / src_total * 100, 1),
            "n_sent_script": n_sent_script, "n_clause_script": n_clause_script,
            "n_chapters_ts": len(chapters)}


def main():
    per_project, dna = {}, {"projects": {}, "pooled": {}}
    for pname, cfg in PROJECTS.items():
        r = scan_project(pname, cfg)
        per_project[pname] = r
        json.dump({k: r[k] for k in ("rows", "holes")},
                  open(ROOT / f"pause_dna_rows_{pname}.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    for pname, r in per_project.items():
        stats = {"tl_minutes": r["tl_minutes"], "src_minutes": r["src_minutes"],
                 "insert_total_s": r["insert_total_s"],
                 "insert_ratio_pct": r["insert_ratio_pct"],
                 "n_sent_script": r["n_sent_script"],
                 "n_clause_script": r["n_clause_script"],
                 "spacing": quantiles(r["spacing"]), "kinds": {}}
        for kind in ("KET_CAU", "KET_MENH_DE", "GIUA_MENH_DE"):
            rows = [x for x in r["rows"] if x["kind"] == kind]
            stats["kinds"][kind] = {
                "per_min": round(len(rows) / r["tl_minutes"], 2),
                "gap_chen": quantiles([x["gap_chen"] for x in rows]),
                "nghi_nguon": quantiles([x["nghi_nguon"] for x in rows]),
                "nghe_ra": quantiles([x["nghe_ra"] for x in rows]),
            }
        holes = r["holes"]
        leads = [round(h["dur"] - max(h["shot_offsets"]), 2)
                 for h in holes if h["shot_offsets"]]
        stats["holes"] = {
            "per_min": round(len(holes) / r["tl_minutes"], 2),
            "dur": quantiles([h["dur"] for h in holes]),
            "at_chapter": sum(1 for h in holes if h["at_chapter"]),
            "jcut_lead": quantiles(leads),
            "passive": sum(1 for h in holes if not h["shot_offsets"]),
        }
        dna["projects"][pname] = stats

    all_rows = [x for r in per_project.values() for x in r["rows"]]
    tl_all = sum(r["tl_minutes"] for r in per_project.values())
    src_all = sum(r["src_minutes"] for r in per_project.values())
    ins_all = sum(r["insert_total_s"] for r in per_project.values())
    pooled = {"tl_minutes": round(tl_all, 1),
              "insert_ratio_pct": round(ins_all / (src_all * 60) * 100, 1), "kinds": {}}
    for kind in ("KET_CAU", "KET_MENH_DE", "GIUA_MENH_DE"):
        rows = [x for x in all_rows if x["kind"] == kind]
        pooled["kinds"][kind] = {
            "per_min": round(len(rows) / tl_all, 2),
            "gap_chen": quantiles([x["gap_chen"] for x in rows]),
            "nghi_nguon": quantiles([x["nghi_nguon"] for x in rows]),
            "nghe_ra": quantiles([x["nghe_ra"] for x in rows]),
        }
    all_holes = [h for r in per_project.values() for h in r["holes"]]
    pooled["holes"] = {
        "per_min": round(len(all_holes) / tl_all, 2),
        "dur": quantiles([h["dur"] for h in all_holes]),
        "at_chapter": sum(1 for h in all_holes if h["at_chapter"]),
        "n": len(all_holes),
    }
    dna["pooled"] = pooled
    dna["meta"] = {"date": "2026-07-08", "model": "faster-whisper small",
                   "note": "nghe_ra = nghi_nguon + gap_chen; diem cat cung-file; "
                           "kind da doi chieu script goc (script_verified)"}
    json.dump(dna, open(ROOT / "pause_dna.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("\n================ DNA 3 PROJECT ================", flush=True)
    for pname, s in dna["projects"].items():
        print(f"\n{pname} ({s['tl_minutes']}ph, chen +{s['insert_ratio_pct']}%):", flush=True)
        for kind, k in s["kinds"].items():
            if k["nghe_ra"]:
                print(f"  {kind:12s} {k['per_min']:>4}/ph  nghe_ra p50={k['nghe_ra'].get('p50')} "
                      f"(p25={k['nghe_ra'].get('p25')} p75={k['nghe_ra'].get('p75')})", flush=True)
        h = s["holes"]
        print(f"  o tho: {h['per_min']}/ph, dur p50={h['dur'].get('p50')} max={h['dur'].get('max')}, "
              f"chuong {h['at_chapter']}, passive {h['passive']}", flush=True)
    print("\nPOOLED:", json.dumps(pooled["kinds"], ensure_ascii=False), flush=True)
    print("\nDone. pause_dna.json + pause_dna_rows_*.json da ghi vao project root.", flush=True)


if __name__ == "__main__":
    main()
