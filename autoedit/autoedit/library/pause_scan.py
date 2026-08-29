"""C7 — scan DNA nhịp nghỉ editor -> pause_dna.json per-niche (lệnh `autoedit pause-dna`).

Đóng gói từ `learn_pause_dna.py` (scratch 2026-07-08, NHAT_KY §HOC-DNA-NHIP) — thuật
toán rows/holes/đối-chiếu-script GIỮ NGUYÊN để số ra khớp bản DNA space hiện hành.
Phần MỚI theo bài học MO_TA_SHOT_THO §6.2C (lý do DNA bị hiểu sai lần đầu):
  1. KHÔNG lọc phăng ô ≥8s — nhận diện MONTAGE riêng (≥4 nhát cắt trong ô hoặc ô >20s);
  2. TÁCH lớp ô theo cách phủ: hold (nhát cắt đầu sau hết voice) ≤1,2s + footage ≥1,5s
     = lớp HÌNH THỞ; ô không nhát cắt = voice-nghỉ (passive), không vào lớp thở;
  3. xuất block `pooled.breath` ĐO ĐƯỢC cho `load_breath_dna` (anchors/hold/cap) +
     `pooled.breath_measured` (phân bố k, quantiles) cho NGƯỜI xem — các khóa CHÍNH SÁCH
     (k_thresholds/k_fractions/min_piece) không xuất, loader tự fallback hằng space
     (luật k "nửa DNA nửa interview", mới 3 điểm dữ liệu — backlog §6.5 đo dần).

Consumer: cutter/pause.py::load_pause_dna + load_breath_dna (fail-open) — sai schema là
rơi về hằng IM LẶNG, nên có test round-trip save→load. File niche ĐÃ có (bản duyệt) thì
KHÔNG đè mặc định: ghi pause_dna.new.json cạnh bên; --force mới đè (tự backup trước).
"""

from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Callable, Optional

SENT_P = ".?!"
CLAUSE_P = ",;:—–"
HOLE_MIN_S = 1.5          # ô ≥1,5s mới đáng đo (y script gốc)
MONTAGE_CUTS = 4          # §6.2C: ≥4 nhát cắt trong ô = montage, loại khỏi lớp thở
MONTAGE_DUR_S = 20.0      # §6.2C: ô >20s = section/montage
BREATH_MAX_HOLD = 1.2     # §6.2C: hold ≤1,2s -> nhát cắt sát mép voice = hình thở
BREATH_MIN_FOOTAGE = 1.5  # §6.2C: footage ≥1,5s mới là "footage riêng"
MIN_ANCHOR_N = 5          # <5 ô thở đo được -> không xuất anchors (loader fallback)

WordsFn = Callable[[str], Optional[list[dict]]]   # tên file voice -> [{text,start,end}]


def sanitize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def draft_label(draft_dir: Path) -> str:
    """'SP1 - 001' -> 'SP1-001' — khớp tên cache transcript đã có từ scan 2026-07-08."""
    return re.sub(r"\s+", "", draft_dir.name)


def _normw(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def _script_tokens(txt: str) -> list[tuple[str, int, int]]:
    toks = []
    for m in re.finditer(r"[A-Za-z0-9''’\-]+", txt):
        n = _normw(m.group(0))
        if n:
            toks.append((n, m.start(), m.end()))
    return toks


def _reconcile_kind(truoc: str, sau: str, kind_whisper: str, txt: str, toks) -> tuple[str, bool]:
    """Đối chiếu script gốc (vá whisper mất dấu/nuốt liên từ): khớp 3 từ ngữ cảnh TRƯỚC
    điểm cắt, tìm từ đầu phần SAU trong ≤6 token kế, đọc ký tự GIỮA -> dấu thật."""
    b = [w for w in (_normw(x) for x in truoc.split()) if w][-3:]
    a = [w for w in (_normw(x) for x in sau.split()) if w][:3]
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


def _chapter_times(txt: str) -> list[int]:
    return [int(m.group(1)) * 60 + int(m.group(2))
            for m in re.finditer(r"(?m)^\s*(\d{1,2}):(\d{2})\s+CHAPTER", txt)]


def _quantiles(arr: list[float]) -> dict:
    s = sorted(arr)
    n = len(s)
    if n == 0:
        return {}
    q = lambda p: round(s[min(n - 1, int(n * p))], 2)  # noqa: E731 — y script gốc
    return {"n": n, "p10": q(0.10), "p25": q(0.25), "p50": q(0.50),
            "p75": q(0.75), "p90": q(0.90), "min": round(s[0], 2), "max": round(s[-1], 2)}


def _resolve_rel(path_str: str) -> str:
    """Path material -> path TƯƠNG ĐỐI dưới folder draft. Placeholder CapCut -> phần
    sau `_##/` (vd Resources/local/x.mp3); còn lại -> materials/<basename>.
    (Mẻ deepsea 2026-07-13: material `name` ≠ file đĩa + voice ngoài materials/.)"""
    p = (path_str or "").replace("\\", "/")
    if "_##/" in p:
        return p.split("_##/", 1)[1]
    return f"materials/{Path(p).name}" if p else ""


def _audio_track_score(t: dict) -> float:
    return len(t["segments"]) * sum(s["target_timerange"]["duration"]
                                    for s in t["segments"])


def voice_track_candidates(draft_content: dict) -> list[tuple[list[dict], dict[str, str]]]:
    """Mọi track audio xếp theo điểm lai giảm dần (kèm map material→path) — cho
    tcf-gen fallback sang track kế khi track điểm cao nhất hóa ra nhạc (REAL72/79
    2026-07-14: nhạc trải dài ≈ voice VÀ nhiều segment hơn → điểm lai vẫn thua)."""
    mats = {a["id"]: _resolve_rel(a.get("path") or a.get("name") or "")
            for a in draft_content["materials"].get("audios", [])}
    tracks = sorted((t for t in draft_content["tracks"] if t["type"] == "audio"),
                    key=_audio_track_score, reverse=True)
    return [(sorted(t["segments"], key=lambda s: s["target_timerange"]["start"]), mats)
            for t in tracks]


def voice_files_of(draft_content: dict) -> tuple[list[dict], dict[str, str]]:
    """(segments đã sort của track audio ĐIỂM CAO NHẤT = số segment × tổng thời lượng,
    map material_id->path TƯƠNG ĐỐI dưới draft — theo `path` đĩa, KHÔNG theo `name` vì
    draft editor hay lệch name↔file; material không path -> fallback name y cũ).

    Điểm lai vì mỗi tiêu chí đơn đều chọn nhầm ở kho thật (đo 74 draft 2 niche
    2026-07-14): max-segment nhầm nhạc/SFX vụn ở draft voice-ít-cắt (REAL06: nhạc
    19 seg/3,8ph thắng voice 11 seg/27ph); max-duration nhầm nhạc/bed trải dài
    (DS-53 v2: nhạc 18 seg/43ph thắng voice 115 seg/38ph; REAL32: bed 1 seg/30ph
    thắng voice 397 seg/26ph). Điểm lai giữ deepsea 26/26 draft y cũ."""
    return voice_track_candidates(draft_content)[0]


def scan_draft(draft_dir: Path, script_text: str, get_words: WordsFn,
               echo=lambda s: None) -> dict:
    """Quét 1 draft editor -> rows (điểm cắt cùng-file) + holes + spacing + tỷ lệ chèn.

    Thuật toán y `learn_pause_dna.py` (regression khớp số DNA space hiện hành).
    script_text rỗng -> phân loại kind theo whisper-only (script_verified=False).
    """
    dc = json.loads((draft_dir / "draft_content.json").read_text(encoding="utf-8"))
    segs, mats = voice_files_of(dc)
    usage = Counter(mats[s["material_id"]] for s in segs)
    vfiles = [nm for nm, c in usage.items() if c >= 2]
    echo(f"  voice track: {len(segs)} seg | file >=2 seg: {vfiles}")

    words: dict[str, list[dict]] = {}
    for nm in vfiles:
        w = get_words(nm)
        if w:
            words[nm] = w

    toks = _script_tokens(script_text) if script_text else []

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
        kind, verified = (_reconcile_kind(truoc, sau, kind_w, script_text, toks)
                          if toks else (kind_w, False))
        rows.append({
            "file": nm, "cut_s": round(cut, 2), "tl_s": round(tl_end, 2),
            "kind": kind, "kind_whisper": kind_w, "script_verified": verified,
            "gap_chen": round(tgap, 2), "nghi_nguon": round(w1["start"] - w0["end"], 2),
            "nghe_ra": round(max(tgap, 0) + max(w1["start"] - w0["end"], 0), 2),
            "truoc": truoc, "sau": sau,
        })

    # mọi mối nối (kể cả khác file) — spacing + tỷ lệ chèn
    all_gaps, all_pos = [], []
    for a, b in zip(segs, segs[1:]):
        tl_end = (a["target_timerange"]["start"] + a["target_timerange"]["duration"]) / 1e6
        all_gaps.append(b["target_timerange"]["start"] / 1e6 - tl_end)
        all_pos.append(tl_end)
    spacing = [round(y - x, 2) for x, y in zip(all_pos, all_pos[1:])]

    # ô ≥1,5s + offset các nhát cắt video bên trong (KHÔNG lọc ≥8s — §6.2C.1)
    vids = [t for t in dc["tracks"] if t["type"] == "video"]
    vsegs = (sorted(max(vids, key=lambda t: len(t["segments"]))["segments"],
                    key=lambda s: s["target_timerange"]["start"]) if vids else [])
    holes = []
    for s1, s2 in zip(segs, segs[1:]):
        hs = (s1["target_timerange"]["start"] + s1["target_timerange"]["duration"]) / 1e6
        he = s2["target_timerange"]["start"] / 1e6
        if he - hs < HOLE_MIN_S:
            continue
        offs = [round(v["target_timerange"]["start"] / 1e6 - hs, 2) for v in vsegs
                if hs - 0.05 <= v["target_timerange"]["start"] / 1e6 < he - 0.05]
        holes.append({"tl_s": round(hs, 2), "dur": round(he - hs, 2), "shot_offsets": offs})

    chapters = _chapter_times(script_text) if script_text else []
    for h in holes:
        h["at_chapter"] = any(h["tl_s"] - 2 <= c <= h["tl_s"] + h["dur"] + 2 for c in chapters)

    tl_start = segs[0]["target_timerange"]["start"] / 1e6
    tl_end_all = (segs[-1]["target_timerange"]["start"]
                  + segs[-1]["target_timerange"]["duration"]) / 1e6
    tl_span = tl_end_all - tl_start
    insert_total = sum(max(g, 0) for g in all_gaps)
    src_total = tl_span - insert_total
    echo(f"  {len(rows)} điểm cắt cùng-file | phân loại: "
         f"{dict(Counter(r['kind'] for r in rows))} | "
         f"script_verified {sum(1 for r in rows if r['script_verified'])}/{len(rows)}")
    echo(f"  ô >={HOLE_MIN_S}s: {len(holes)} | chèn {insert_total:.1f}s / nguồn "
         f"{src_total:.1f}s = +{insert_total / src_total * 100:.1f}%")

    return {"rows": rows, "holes": holes, "spacing": spacing,
            "tl_minutes": round(tl_span / 60, 2), "src_minutes": round(src_total / 60, 2),
            "insert_total_s": round(insert_total, 1),
            "insert_ratio_pct": round(insert_total / src_total * 100, 1),
            "n_sent_script": len(re.findall(r"[.?!]+", script_text)) if script_text else 0,
            "n_clause_script": len(re.findall(r"[,;:]|—|–", script_text)) if script_text else 0,
            "n_chapters_ts": len(chapters)}


# --------------------------- lớp hình thở (§6.2C — phần MỚI) ---------------------------
def split_breath_layer(holes: list[dict]) -> dict:
    """Tách ô theo cách phủ: breath (hold ≤1,2 + footage ≥1,5) · montage (≥4 nhát/>20s)
    · passive (không nhát cắt = voice-nghỉ) · other (nhát cắt xa mép/footage cụt)."""
    breath, montage, passive, other = [], [], [], []
    for h in holes:
        offs = sorted(h["shot_offsets"])
        if not offs:
            passive.append(h)
            continue
        if len(offs) >= MONTAGE_CUTS or h["dur"] > MONTAGE_DUR_S:
            montage.append(h)
            continue
        hold, footage = offs[0], h["dur"] - offs[0]
        if hold <= BREATH_MAX_HOLD and footage >= BREATH_MIN_FOOTAGE:
            pieces = [round(b - a, 2) for a, b in zip(offs, offs[1:])] + \
                     [round(h["dur"] - offs[-1], 2)]
            breath.append({**h, "hold": hold, "footage": round(footage, 2),
                           "k": len(offs), "pieces": pieces})
        else:
            other.append(h)
    return {"breath": breath, "montage": montage, "passive": passive, "other": other}


def _breath_blocks(all_holes: list[dict]) -> tuple[dict, dict]:
    """(pooled.breath cho loader, pooled.breath_measured cho người xem)."""
    layers = split_breath_layer(all_holes)
    br = layers["breath"]
    measured = {
        "n_breath": len(br), "n_montage": len(layers["montage"]),
        "n_passive": len(layers["passive"]), "n_other": len(layers["other"]),
        "footage": _quantiles([x["footage"] for x in br]),
        "hold": _quantiles([x["hold"] for x in br]),
        "k_dist": dict(sorted(Counter(x["k"] for x in br).items())),
        "pieces_k2plus": [x["pieces"] for x in br if x["k"] >= 2],
    }
    block: dict = {"note": "đo bởi pause-dna (C7); k_thresholds/k_fractions/min_piece "
                           "KHÔNG xuất — loader fallback hằng space (luật k nửa DNA "
                           "nửa interview, xem breath_measured.k_dist)"}
    if len(br) >= MIN_ANCHOR_N:
        f = sorted(x["footage"] for x in br)
        pick = lambda p: round(f[min(len(f) - 1, int(len(f) * p))], 1)  # noqa: E731
        block["footage_anchors"] = [pick(p) for p in (0.10, 0.25, 0.50, 0.75, 0.90)]
        block["footage_cap"] = round(f[-1] * 2) / 2
        block["hold"] = round(_quantiles([x["hold"] for x in br])["p50"], 1)
    return block, measured


def compute_pause_dna(per_draft: dict[str, dict], meta_note: str = "") -> dict:
    """Gộp kết quả scan_draft nhiều draft -> dict pause_dna.json (per-project + pooled)."""
    dna: dict = {"projects": {}, "pooled": {}}
    for pname, r in per_draft.items():
        stats = {"tl_minutes": r["tl_minutes"], "src_minutes": r["src_minutes"],
                 "insert_total_s": r["insert_total_s"],
                 "insert_ratio_pct": r["insert_ratio_pct"],
                 "n_sent_script": r["n_sent_script"],
                 "n_clause_script": r["n_clause_script"],
                 "spacing": _quantiles(r["spacing"]), "kinds": {}}
        for kind in ("KET_CAU", "KET_MENH_DE", "GIUA_MENH_DE"):
            rows = [x for x in r["rows"] if x["kind"] == kind]
            stats["kinds"][kind] = {
                "per_min": round(len(rows) / r["tl_minutes"], 2),
                "gap_chen": _quantiles([x["gap_chen"] for x in rows]),
                "nghi_nguon": _quantiles([x["nghi_nguon"] for x in rows]),
                "nghe_ra": _quantiles([x["nghe_ra"] for x in rows]),
            }
        holes = r["holes"]
        leads = [round(h["dur"] - max(h["shot_offsets"]), 2)
                 for h in holes if h["shot_offsets"]]
        stats["holes"] = {
            "per_min": round(len(holes) / r["tl_minutes"], 2),
            "dur": _quantiles([h["dur"] for h in holes]),
            "at_chapter": sum(1 for h in holes if h["at_chapter"]),
            "jcut_lead": _quantiles(leads),
            "passive": sum(1 for h in holes if not h["shot_offsets"]),
        }
        dna["projects"][pname] = stats

    all_rows = [x for r in per_draft.values() for x in r["rows"]]
    tl_all = sum(r["tl_minutes"] for r in per_draft.values())
    src_all = sum(r["src_minutes"] for r in per_draft.values())
    ins_all = sum(r["insert_total_s"] for r in per_draft.values())
    pooled = {"tl_minutes": round(tl_all, 1),
              "insert_ratio_pct": round(ins_all / (src_all * 60) * 100, 1), "kinds": {}}
    for kind in ("KET_CAU", "KET_MENH_DE", "GIUA_MENH_DE"):
        rows = [x for x in all_rows if x["kind"] == kind]
        pooled["kinds"][kind] = {
            "per_min": round(len(rows) / tl_all, 2),
            "gap_chen": _quantiles([x["gap_chen"] for x in rows]),
            "nghi_nguon": _quantiles([x["nghi_nguon"] for x in rows]),
            "nghe_ra": _quantiles([x["nghe_ra"] for x in rows]),
        }
    all_holes = [h for r in per_draft.values() for h in r["holes"]]
    pooled["holes"] = {
        "per_min": round(len(all_holes) / tl_all, 2),
        "dur": _quantiles([h["dur"] for h in all_holes]),
        "at_chapter": sum(1 for h in all_holes if h["at_chapter"]),
        "n": len(all_holes),
    }
    pooled["breath"], pooled["breath_measured"] = _breath_blocks(all_holes)
    dna["pooled"] = pooled
    dna["meta"] = {"date": date.today().isoformat(), "tool": "autoedit pause-dna (C7)",
                   "note": ("nghe_ra = nghi_nguon + gap_chen; điểm cắt cùng-file; "
                            "kind đối chiếu script gốc khi có --script. " + meta_note).strip()}
    return dna


def save_pause_dna(dna: dict, niche_d: Path, force: bool = False) -> tuple[Path, str]:
    """Ghi pause_dna.json — GUARD bản đã duyệt: file có sẵn + không force -> ghi
    pause_dna.new.json; force -> backup pause_dna.backup-<ngày>.json rồi đè.
    Trả (path đã ghi, 'fresh'|'new'|'forced')."""
    niche_d.mkdir(parents=True, exist_ok=True)
    target = niche_d / "pause_dna.json"
    if target.exists() and not force:
        out = niche_d / "pause_dna.new.json"
        status = "new"
    elif target.exists():
        shutil.copy2(target, niche_d / f"pause_dna.backup-{date.today().isoformat()}.json")
        out, status = target, "forced"
    else:
        out, status = target, "fresh"
    out.write_text(json.dumps(dna, ensure_ascii=False, indent=1), encoding="utf-8")
    return out, status


def make_whisper_words(draft_dir: Path, cache_dir: Path, language: str = "en") -> WordsFn:
    """WordsFn mặc định: cache bền <niche>/pause_scan_cache/<label>__<file>.words.json,
    miss -> transcribe faster-whisper small (import lười — có cache thì 0 nặng).
    Nhận path TƯƠNG ĐỐI dưới draft (từ voice_files_of) hoặc tên trần (-> materials/);
    cache key theo BASENAME nên tcf-gen + pause-dna dùng chung 1 lượt transcribe."""
    label = draft_label(draft_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    aligner = None

    def get_words(name: str) -> Optional[list[dict]]:
        nonlocal aligner
        if not name:
            return None
        cache = cache_dir / f"{label}__{sanitize(Path(name).name)}.words.json"
        if cache.exists():
            return json.loads(cache.read_text(encoding="utf-8"))
        path = draft_dir / name if "/" in name else draft_dir / "materials" / name
        if not path.exists():
            return None
        if aligner is None:
            from autoedit.align.whisper_local import FasterWhisperAligner
            aligner = FasterWhisperAligner(model_size="small", language=language)
        ws = aligner.transcribe(path)
        out = [{"text": w.text, "start": w.start, "end": w.end} for w in ws]
        cache.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        return out

    return get_words
