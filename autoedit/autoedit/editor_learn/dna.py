"""Quét DNA âm thanh 1 draft editor thật — ĐỌC-ONLY (S4/M5, MO_TA_SFX_HOAN_THIEN §4b.1).

Bê 2 phép đo đã hiệu chuẩn khớp 100% số công bố trên 3 draft SP1 (PB10 doc §5/§7):
- PB13 (scripts_phan_tich_pb13_sfx_vol_voice.py — giữ nguyên logic): đoạn >40s =
  nhạc/drone đặt cả bài; SFX cục bộ chia ngữ cảnh voice (≥60% trùng = đè voice,
  ≤15% = không voice); median từng nhóm, tách whoosh riêng.
- PB11 whoosh: cut = TẬP start segment của track video CHÍNH (nhiều segment nhất,
  bỏ t≈0); "sát cut" = đầu whoosh cách cut gần nhất ≤0.5s; "cut trong whoosh" =
  tồn tại cut a ≤ c ≤ b (inclusive — whoosh bắt đầu ĐÚNG tại cut vẫn tính).

Hồ sơ cộng dồn editor_dna.json (cạnh ambient root, vd F:\\AutoEdit\\editor_dna.json):
mỗi draft 1 entry — chạy lại CÙNG draft là THAY entry, không cộng đôi. Pooled median
chỉ để ĐỐI CHIẾU SUBJECT_VOL/SUBJECT_BREATH_VOL trên báo cáo — KHÔNG tự đổi hằng
(V10 user chốt bằng tai; luật đứng: volume chỉ đổi khi user yêu cầu).
"""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from autoedit.ambient.library import ambient_root

SEC = 1_000_000
SFX_SEG_MAX = 40.0   # đoạn ≤40s = SFX/ambient cục bộ; dài hơn = nhạc/drone đặt cả bài
NEAR_CUT_S = 0.5
VOICE_HINTS = ("voice", "hook", "space - ", "spcae", "pscae")
WHOOSH_HINTS = ("whoosh", "swoosh", "woosh", "swish", "vụt", "vujt")
PROFILE_FILE = "editor_dna.json"


def db(v: float) -> float:
    return 20 * math.log10(v) if v > 0 else float("-inf")


def _merge(iv: list[tuple[float, float]]) -> list[list[float]]:
    out: list[list[float]] = []
    for s, e in sorted(iv):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def _overlap(a0: float, a1: float, iv: list[list[float]]) -> float:
    return sum(max(0.0, min(a1, e) - max(a0, s)) for s, e in iv)


def load_draft(draft_dir: Path) -> dict:
    return json.loads((Path(draft_dir) / "draft_content.json").read_text(encoding="utf-8"))


def audio_name_map(d: dict) -> dict[str, str]:
    return {a["id"]: (a.get("name") or "") for a in d["materials"].get("audios", [])}


def voice_tracks(d: dict, name_of: dict[str, str]) -> list[dict]:
    """Track voice = ≥60% segment mang tên gợi ý voice; không có -> track nhiều segment nhất.

    GIỮ NGUYÊN quirk của bản đo gốc để số khớp PB13 công bố (regression M5):
    SP1-001 track voice chỉ phủ nửa đầu video (nửa sau nằm track tên khác);
    SP1-004 fallback lẫn vài segment SFX (PB12 đã ghi chú — không đổi kết luận).
    DNA dùng để SO GIỮA các draft nên phép đo phải cố định, không "sửa cho đúng hơn".
    """
    auds = [t for t in d["tracks"] if t.get("type") == "audio" and t.get("segments")]
    if not auds:
        return []

    def voiceness(t: dict) -> float:
        n = sum(1 for s in t["segments"]
                if any(h in name_of.get(s.get("material_id"), "").lower() for h in VOICE_HINTS))
        return n / len(t["segments"])

    vt = [t for t in auds if voiceness(t) >= 0.6]
    return vt or [max(auds, key=lambda t: len(t["segments"]))]


@dataclass
class DraftDNA:
    """Số đo 1 draft — vols giữ THÔ (list) để pooled median cộng dồn được."""

    draft: str
    scanned_at: str
    duration_s: float
    voice_span: tuple[float, float]
    n_voice_tracks: int
    keyframed_segments: int
    music_vols: list[float] = field(default_factory=list)
    # PB13 — vols theo ngữ cảnh voice, ĐÃ TÁCH whoosh ra nhóm riêng
    sfx_vols: dict[str, list[float]] = field(default_factory=dict)         # voiced/novoice/mixed
    whoosh_ctx_vols: dict[str, list[float]] = field(default_factory=dict)  # nt., riêng whoosh
    # PB11 — whoosh toàn draft vs cut track video chính
    whoosh_n: int = 0
    whoosh_durs: list[float] = field(default_factory=list)
    whoosh_vols: list[float] = field(default_factory=list)
    cuts_n: int = 0
    whoosh_near_cut: int = 0
    cuts_inside_whoosh: int = 0

    def whoosh_per_min(self) -> float:
        """Mật độ whoosh theo PHÚT VIDEO (PB11: ~1/phút, không tính theo voice span)."""
        return self.whoosh_n / (self.duration_s / 60) if self.duration_s > 0 else 0.0


def scan_draft(draft_dir: Path) -> DraftDNA:
    draft_dir = Path(draft_dir)
    d = load_draft(draft_dir)
    name_of = audio_name_map(d)
    dna = DraftDNA(
        draft=draft_dir.name, scanned_at=date.today().isoformat(),
        duration_s=d.get("duration", 0) / SEC, voice_span=(0.0, 0.0),
        n_voice_tracks=0, keyframed_segments=0,
        sfx_vols={"voiced": [], "novoice": [], "mixed": []},
        whoosh_ctx_vols={"voiced": [], "novoice": [], "mixed": []},
    )
    auds = [t for t in d["tracks"] if t.get("type") == "audio" and t.get("segments")]
    if not auds:
        return dna
    vtracks = voice_tracks(d, name_of)
    dna.n_voice_tracks = len(vtracks)
    vint = _merge([(s["target_timerange"]["start"] / SEC,
                    (s["target_timerange"]["start"] + s["target_timerange"]["duration"]) / SEC)
                   for t in vtracks for s in t["segments"]])
    v_start, v_end = vint[0][0], vint[-1][1]
    dna.voice_span = (v_start, v_end)

    # --- PB13: nhạc >40s + SFX theo ngữ cảnh voice (logic giữ nguyên script gốc) ---
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
                dna.keyframed_segments += 1
            if dur > SFX_SEG_MAX:
                dna.music_vols.append(vol)
                continue
            if a1 < v_start or a0 > v_end:   # intro/outro ngoài vùng voice
                continue
            frac = _overlap(a0, a1, vint) / dur if dur else 1.0
            cls = "voiced" if frac >= 0.6 else ("novoice" if frac <= 0.15 else "mixed")
            bucket = dna.whoosh_ctx_vols if any(h in nm for h in WHOOSH_HINTS) else dna.sfx_vols
            bucket[cls].append(vol)

    # --- PB11: whoosh (mọi track audio) vs cut track video chính ---
    wh: list[tuple[float, float, float]] = []
    for t in auds:
        for s in t["segments"]:
            nm = name_of.get(s.get("material_id"), "").lower()
            if any(h in nm for h in WHOOSH_HINTS):
                a0 = s["target_timerange"]["start"] / SEC
                wh.append((a0, a0 + s["target_timerange"]["duration"] / SEC,
                           s.get("volume", 1.0)))
    dna.whoosh_n = len(wh)
    dna.whoosh_durs = [b - a for a, b, _ in wh]
    dna.whoosh_vols = [v for _, _, v in wh]

    vids = [t for t in d["tracks"] if t.get("type") == "video" and t.get("segments")]
    if vids and wh:
        main = max(vids, key=lambda t: len(t["segments"]))
        cuts = sorted(c for c in {s["target_timerange"]["start"] / SEC for s in main["segments"]}
                      if c > 0.01)
        dna.cuts_n = len(cuts)
        if cuts:
            dna.whoosh_near_cut = sum(
                1 for a, _, _ in wh if min(abs(a - c) for c in cuts) <= NEAR_CUT_S)
            dna.cuts_inside_whoosh = sum(
                1 for a, b, _ in wh if any(a <= c <= b for c in cuts))
    return dna


# ---------------- hồ sơ cộng dồn ----------------

def default_profile_path(root_override: str | Path | None = None) -> Path:
    return ambient_root(root_override).parent / PROFILE_FILE


def load_profile(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        return {"version": 1, "drafts": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def update_profile(path: Path, dna: DraftDNA) -> dict:
    """Thay/thêm entry theo tên draft rồi ghi lại — idempotent khi học lại cùng draft."""
    profile = load_profile(path)
    profile["drafts"][dna.draft] = asdict(dna)
    Path(path).write_text(
        json.dumps(profile, ensure_ascii=False, indent=1), encoding="utf-8")
    return profile


def pooled_stats(profile: dict) -> dict:
    """Median gộp mọi draft đã học — đối chiếu SUBJECT_VOL (voiced) / SUBJECT_BREATH_VOL
    (novoice) / nhạc. Trả {} khi chưa có gì."""
    drafts = profile.get("drafts", {})
    out: dict = {"n_drafts": len(drafts)}
    for key, src in (("voiced", "sfx_vols"), ("novoice", "sfx_vols")):
        vols = [v for e in drafts.values() for v in e.get(src, {}).get(key, [])]
        out[key] = {"n": len(vols), "median": statistics.median(vols) if vols else None}
    music = [v for e in drafts.values() for v in e.get("music_vols", [])]
    out["music"] = {"n": len(music), "median": statistics.median(music) if music else None}
    return out
