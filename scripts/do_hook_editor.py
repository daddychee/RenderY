# -*- coding: utf-8 -*-
"""ĐO HOOK SFX từ draft editor 1 niche (READ-ONLY) — bước B4 QUY_TRINH_LAY_MAU_SFX_NICHE_MOI.md.

Chạy từ folder autoedit/ (cần package autoedit trong venv):
    uv run python "..\\scripts\\do_hook_editor.py" <niche> <root_draft_1> [<root_2> ...]
vd: uv run python "..\\scripts\\do_hook_editor.py" deepsea "E:\\PROJECT NHAN BAN\\DEEPSEA 1" "E:\\PROJECT NHAN BAN\\DEEP SEA 3"

Câu hỏi trả lời: hook editor có bao nhiêu SFX/phút (vs body), volume, bám CUT video
hay bám TEXT? → chép kết quả vào PHAN_TICH_HOOK_SFX_EDITOR_<NICHE>.md rồi mới quyết
gate (B5). Hook = từ 0 đến mở chương 2 trong TCF "topic + chapter video.txt" (fallback 60s).
Phân loại audio TÁI DÙNG mine.classify (subject_rules.yaml per-niche nếu có).

Bản gốc đo 23 draft deepsea 2026-07-13 (kết quả: 4.8 tiếng/phút hook, bám CUT 48%).
"""
import re
import statistics
import sys
from pathlib import Path

from autoedit.ambient.library import load_subject_rules, niche_dir
from autoedit.editor_learn.dna import SEC, load_draft
from autoedit.editor_learn.mine import classify, collect_audio_usage

if len(sys.argv) < 3:
    sys.exit("cach dung: do_hook_editor.py <niche> <root_draft_1> [<root_2> ...]")
NICHE = sys.argv[1]
ROOTS = [Path(p) for p in sys.argv[2:]]
SKIP: set[str] = set()  # tên folder draft bỏ (dup/compound/rỗng) — thêm tay khi soi thấy
TCF = "topic + chapter video.txt"
ANCHOR_S = 0.25  # cửa sổ bám mốc (báo cáo thêm 0.10)

rules = load_subject_rules(niche_dir(NICHE))

def hook_end_from_tcf(d: Path) -> float | None:
    f = d / TCF
    if not f.is_file():
        return None
    ts = []
    for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r"^\s*(\d+):(\d{2})\s+\S", line)
        if m:
            ts.append(int(m.group(1)) * 60 + int(m.group(2)))
    return float(ts[1]) if len(ts) >= 2 else None

def segs_of(d: dict, ttype: str):
    for t in d.get("tracks", []):
        if t.get("type") == ttype:
            for s in t.get("segments", []):
                tr = s["target_timerange"]
                yield t, s, tr["start"] / SEC, (tr["start"] + tr["duration"]) / SEC

rows = []
all_hook_names = {}
all_anchor = []          # (off_cut, off_text) per SFX hook
per_draft_lines = []

drafts = sorted(p for r in ROOTS if r.is_dir() for p in r.iterdir()
                if p.is_dir() and p.name.lower() not in SKIP
                and ((p / "draft_content.json").is_file() or (p / "draft_info.json").is_file()))

for dd in drafts:
    try:
        d = load_draft(dd)
    except Exception as e:
        per_draft_lines.append(f"{dd.name}: LOI load ({e})")
        continue
    uses = collect_audio_usage(dd, d)
    dest_of = {nm: classify(u, rules=rules) for nm, u in uses.items()}
    name_of = {}
    for a in d["materials"].get("audios", []):
        name_of[a["id"]] = a.get("name") or ""

    total_end = max((e for _, _, _, e in segs_of(d, "video")), default=0.0)
    if total_end <= 0:
        continue
    hk = hook_end_from_tcf(dd) or 60.0
    hk = min(hk, total_end)

    # mốc video cut (mọi track video) + mốc text
    cuts = sorted({s0 for _, _, s0, _ in segs_of(d, "video") if s0 > 0.05})
    texts = sorted({s0 for _, _, s0, _ in segs_of(d, "text")})

    ev_hook, ev_body = [], []
    for _, s, s0, e0 in segs_of(d, "audio"):
        nm_ = name_of.get(s.get("material_id"), "")
        dest, kind = dest_of.get(nm_, ("", ""))
        if dest not in ("sfx", "ambient", "hold"):
            continue
        if "elevenlabs" in nm_.lower():   # voice lọt lưới classify (không in_voice_track)
            continue
        seg_dur = e0 - s0
        if seg_dur > 45:      # bed/pad dài — không phải "SFX điểm" (drone đã có S1)
            continue
        item = (s0, seg_dur, dest, kind, s.get("volume"), name_of.get(s.get("material_id"), ""))
        (ev_hook if s0 < hk else ev_body).append(item)

    for s0, dur, dest, kind, vol, nm in ev_hook:
        oc = min((s0 - c for c in cuts), key=abs, default=None)
        ot = min((s0 - t for t in texts), key=abs, default=None)
        all_anchor.append((oc, ot))
        all_hook_names[nm] = all_hook_names.get(nm, 0) + 1

    hkm, bdm = hk / 60.0, (total_end - hk) / 60.0
    r = dict(name=dd.name, hk=hk, total=total_end,
             n_hook=len(ev_hook), n_body=len(ev_body),
             hook_pm=len(ev_hook) / hkm if hkm else 0,
             body_pm=len(ev_body) / bdm if bdm else 0,
             vols=[v for _, _, _, _, v, _ in ev_hook if isinstance(v, (int, float))],
             cuts_hook_pm=sum(1 for c in cuts if c < hk) / hkm if hkm else 0)
    rows.append(r)
    per_draft_lines.append(
        f"{dd.name:22s} hook {hk:5.0f}s | SFX hook {r['n_hook']:3d} ({r['hook_pm']:4.1f}/ph)"
        f" | body {r['n_body']:4d} ({r['body_pm']:4.1f}/ph) | cut hook {r['cuts_hook_pm']:4.1f}/ph")

print(f"=== {NICHE}: {len(rows)} draft do duoc ===")
for line in per_draft_lines:
    print(" ", line)

if rows:
    hp = [r["hook_pm"] for r in rows]; bp = [r["body_pm"] for r in rows]
    print(f"\nSFX/phut HOOK: median {statistics.median(hp):.2f} (min {min(hp):.1f} max {max(hp):.1f})")
    print(f"SFX/phut BODY: median {statistics.median(bp):.2f} (min {min(bp):.1f} max {max(bp):.1f})")
    vols = [v for r in rows for v in r["vols"]]
    if vols:
        print(f"volume SFX hook: median {statistics.median(vols):.2f} (n={len(vols)})")
    n0 = sum(1 for r in rows if r["n_hook"] == 0)
    print(f"draft hook KHONG SFX diem: {n0}/{len(rows)}")

print("\n=== top ten tieng trong hook (moi draft cong don) ===")
for nm, c in sorted(all_hook_names.items(), key=lambda x: -x[1])[:20]:
    print(f"  x{c:2d} {nm[:70]}")

def share(offs, w):
    v = [o for o in offs if o is not None]
    return (sum(1 for o in v if abs(o) <= w) / len(v) * 100) if v else 0.0

ocs = [a for a, _ in all_anchor]; ots = [b for _, b in all_anchor]
print(f"\n=== bam moc ({len(all_anchor)} SFX hook) ===")
print(f"  |offset toi CUT video| <=0.10s: {share(ocs, 0.10):.0f}%  <=0.25s: {share(ocs, 0.25):.0f}%")
print(f"  |offset toi TEXT     | <=0.10s: {share(ots, 0.10):.0f}%  <=0.25s: {share(ots, 0.25):.0f}%")
lead = [o for o in ocs if o is not None and -0.20 <= o < 0]
print(f"  SFX TRUOC cut 0-200ms (whoosh-vao-hit): {len(lead)} ({(len(lead)/len(ocs)*100) if ocs else 0:.0f}%)")
