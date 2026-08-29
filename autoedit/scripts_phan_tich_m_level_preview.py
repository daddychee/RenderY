"""M-LEVEL — phân tích + bản nghe thử: kiểm soát mức nhạc nền theo LOUDNESS ĐO THẬT.

Vấn đề (user 2026-07-14): volume nhạc đặt theo hằng số (nép 0.2 / thở 0.5 / hook 0.3)
mù với độ to thật của khúc nhạc đang phát → hình thở lúc quá to lúc quá nhỏ, nhạc dưới
voice thi thoảng vọt/chìm.

THƯỚC ĐO (hiệu chuẩn bằng 6 mốc tai user trên DS3-084 _V5, 2026-07-14): peak dBFS và
RMS thô KHÔNG tách được bé/vừa (2 bài nhạc khác phổ tần); **LUFS momentary (K-weighting
ITU BS.1770, cửa sổ 400ms) tách sạch**: BÉ = -24.8/-26.9/-25.9, VỪA = -22.1/-22.2/-18.3
→ band thở -22.5..-17.5 LUFS (lớp nhạc riêng).

Script KHÔNG đụng pipeline — đọc draft _V5, đo loudness khúc nhạc trong file gốc, dự
đoán mức phát = LUFS_nguồn + 20·log10(volume), rồi:
  1. Bảng thống kê từng ô thở (cả zone hook) + phân bố nhạc dưới voice.
  2. Render bản trộn OLD / A (band-clamp, user đã chọn A) cho các đoạn có mốc tai.

Chạy:  uv run python scripts_phan_tich_m_level_preview.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import lfilter

SEC = 1_000_000
SR = 48_000
BLK = 0.02                      # lưới phân tích/gain: 20ms
BLK_N = int(SR * BLK)
METER_WIN = 20                  # rolling 20 block = 400ms (momentary)

DRAFT = Path(r"E:\CapCut Drafts\DS3_084_WOMB_CANNIBALISM_20260713_224919_V5")
OUT = Path(__file__).parent / "projects" / "ds3-084-womb-cannibalism-20260713-224919" / "m_level_preview"

# band LUFS momentary của LỚP NHẠC (hiệu chuẩn 6 mốc tai user 2026-07-14)
BREATH_BAND = (-22.5, -17.5)
BREATH_CENTER = -20.0
VOICE_BAND = (-34.0, -24.0)     # phân bố _V5 đo thật: median -29.1 (draft đã duyệt tai)
VOICE_CENTER = -29.0            # ±5dB — chỉ bắt outlier "thi thoảng vọt/chìm", giữ swell
MIN_BREATH = 1.5                # đồng bộ ducking.MIN_BREATH
SILENCE_FLOOR = -50.0           # khúc nhạc lặng chủ đích: KHÔNG kéo lên
CORR_CAP = 12.0                 # trần bù ± dB
VOL_CAP = 2.0                   # trần multiplier (CapCut UI max +6dB)
SMOOTH_S = 2.0                  # làm mượt lượng bù (chống pumping)

EXCERPTS = [(95.0, 285.0), (395.0, 545.0)]   # phủ 6 mốc tai + cụm ô thở lệch

# K-weighting ITU BS.1770 @48k
_B1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
_A1 = [1.0, -1.69065929318241, 0.73248077421585]
_B2 = [1.0, -2.0, 1.0]
_A2 = [1.0, -1.99004745483398, 0.99007225036621]


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-9))


def undb(x):
    return 10 ** (x / 20)


# ---------------------------------------------------------------- đọc draft
def load_draft():
    d = json.loads((DRAFT / "draft_content.json").read_text(encoding="utf-8"))
    mats = {a["id"]: a for a in d["materials"]["audios"]}
    fades = {f["id"]: f for f in d["materials"].get("audio_fades", [])}
    segs = []
    for t in d["tracks"]:
        if t["type"] != "audio":
            continue
        for s in t["segments"]:
            path = mats[s["material_id"]]["path"]
            if "##_draftpath_placeholder" in path:
                path = str(DRAFT / path.split("_##/", 1)[1])
            kfs = []
            for grp in s.get("common_keyframes") or []:
                if grp.get("property_type") == "KFTypeVolume":
                    kfs = [(k["time_offset"], k["values"][0]) for k in grp["keyframe_list"]]
            fi = fo = 0
            for rid in s.get("extra_material_refs") or []:
                f = fades.get(rid)
                if f:
                    fi, fo = f.get("fade_in_duration", 0), f.get("fade_out_duration", 0)
            segs.append({
                "track": t.get("name"), "path": path,
                "t0": s["target_timerange"]["start"] / SEC,
                "dur": s["target_timerange"]["duration"] / SEC,
                "s0": s["source_timerange"]["start"] / SEC,
                "vol": s.get("volume", 1.0), "kfs": kfs,
                "fade_in": fi / SEC, "fade_out": fo / SEC,
            })
    return d, segs


_CACHE: dict[str, np.ndarray] = {}


def audio(path: str) -> np.ndarray:
    """float32 stereo 48k (C4 đã chuẩn hóa; lệch sample-rate thì nội suy)."""
    a = _CACHE.get(path)
    if a is None:
        data, sr = sf.read(path, dtype="float32", always_2d=True)
        if data.shape[1] == 1:
            data = np.repeat(data, 2, axis=1)
        if sr != SR:
            n = int(len(data) * SR / sr)
            t_old = np.linspace(0, 1, len(data))
            t_new = np.linspace(0, 1, n)
            data = np.stack([np.interp(t_new, t_old, data[:, c]) for c in range(2)], axis=1)
        _CACHE[path] = a = np.ascontiguousarray(data)
    return a


def gain_blocks(seg, n: int) -> np.ndarray:
    """Gain multiplier mỗi block 20ms của 1 segment: keyframe (theo giờ FILE NGUỒN,
    đè volume tĩnh — memory capcut-volume-keyframe) × fade 2 mép."""
    t_src = (seg["s0"] + (np.arange(n) + 0.5) * BLK) * SEC
    if seg["kfs"]:
        ts, vs = zip(*seg["kfs"])
        g = np.interp(t_src, ts, vs)
    else:
        g = np.full(n, seg["vol"])
    t_rel = (np.arange(n) + 0.5) * BLK
    if seg["fade_in"] > 0:
        g = g * np.clip(t_rel / seg["fade_in"], 0, 1)
    if seg["fade_out"] > 0:
        g = g * np.clip((seg["dur"] - t_rel) / seg["fade_out"], 0, 1)
    return g.astype(np.float32)


def k_lufs_blocks(x: np.ndarray, n: int) -> np.ndarray:
    """LUFS momentary mỗi block 20ms (K-weighting, rolling 400ms) của x stereo."""
    need = n * BLK_N
    if len(x) < need:
        x = np.pad(x, ((0, need - len(x)), (0, 0)))
    z = np.zeros(need)
    for c in range(x.shape[1]):
        y = lfilter(_B2, _A2, lfilter(_B1, _A1, x[:need, c].astype(np.float64)))
        z += y * y
    ms = z.reshape(n, BLK_N).mean(axis=1)
    k = np.ones(METER_WIN) / METER_WIN
    roll = np.convolve(np.pad(ms, (METER_WIN, METER_WIN), mode="edge"), k,
                       mode="same")[METER_WIN:-METER_WIN]
    return -0.691 + 10 * np.log10(np.maximum(roll, 1e-12))


# ------------------------------------------------- voice interval + vùng phân loại
def voice_intervals(segs):
    out = []
    for s in sorted((s for s in segs if s["track"] == "voice"), key=lambda s: s["t0"]):
        a, b = s["t0"], s["t0"] + s["dur"]
        if out and a - out[-1][1] < MIN_BREATH:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def region_grid(voice, total: float) -> np.ndarray:
    """Mỗi block 20ms: 1 = thở, 0 = voice."""
    n = int(total / BLK) + 1
    r = np.ones(n, dtype=np.int8)
    for a, b in voice:
        r[int(a / BLK):int(b / BLK) + 1] = 0
    return r


def smooth(x: np.ndarray, sec: float) -> np.ndarray:
    w = max(1, int(sec / BLK))
    k = np.ones(w) / w
    return np.convolve(np.pad(x, (w, w), mode="edge"), k, mode="same")[w:-w]


# ---------------------------------------------------- tính gain mới cho nhạc
def music_analysis(segs, region):
    """Mỗi segment nhạc: LUFS nguồn theo block → dự đoán mức phát → gain biến thể A/B.
    Zone HOOK (vol tĩnh >0.25, M-VOL đã qua cổng tai): CHỈ bù ở ô thở, voice giữ."""
    for seg in segs:
        if seg["track"] not in ("music", "music2"):
            continue
        n = int(seg["dur"] / BLK)
        a = audio(seg["path"])
        i0 = int(seg["s0"] * SR)
        src_lufs = k_lufs_blocks(a[i0:i0 + n * BLK_N], n)
        g_old = gain_blocks(seg, n)
        seg["g_old"] = g_old
        seg["hook"] = seg["vol"] > 0.25
        blk0 = int(seg["t0"] / BLK)
        reg = region[blk0:blk0 + n]
        if len(reg) < n:
            reg = np.pad(reg, (0, n - len(reg)), constant_values=1)
        pred = src_lufs + db(g_old)
        lo = np.where(reg == 1, BREATH_BAND[0], VOICE_BAND[0])
        hi = np.where(reg == 1, BREATH_BAND[1], VOICE_BAND[1])
        center = np.where(reg == 1, BREATH_CENTER, VOICE_CENTER)

        delta_a = np.where(pred > hi, hi - pred, np.where(pred < lo, lo - pred, 0.0))
        delta_b = center - pred
        for d_ in (delta_a, delta_b):
            d_[(d_ > 0) & (src_lufs < SILENCE_FLOOR)] = 0.0  # nhạc lặng chủ đích: không kéo
            if seg["hook"]:
                d_[reg == 0] = 0.0                           # hook: voice giữ M-VOL
            np.clip(d_, -CORR_CAP, CORR_CAP, out=d_)
        seg["g_a"] = np.clip(g_old * undb(smooth(delta_a, SMOOTH_S)), 0.0, VOL_CAP).astype(np.float32)
        seg["g_b"] = np.clip(g_old * undb(smooth(delta_b, SMOOTH_S)), 0.0, VOL_CAP).astype(np.float32)
        seg["src_lufs"] = src_lufs
        seg["reg"] = reg


def music_meter(segs, total: float, variant: str) -> np.ndarray:
    """Mức LUFS dự đoán của RIÊNG lớp nhạc toàn timeline (power-sum chỗ crossfade)."""
    n = int(total / BLK) + 1
    pw = np.zeros(n)
    for seg in segs:
        if "src_lufs" not in seg:
            continue
        g = seg[variant]
        blk0 = int(seg["t0"] / BLK)
        m = min(len(g), n - blk0)
        pw[blk0:blk0 + m] += 10 ** (seg["src_lufs"][:m] / 10) * g[:m] ** 2
    return 10 * np.log10(np.maximum(pw, 1e-12))


# ----------------------------------------------------------------- render trộn
def render(segs, w0: float, w1: float, variant: str) -> np.ndarray:
    n = int((w1 - w0) * SR)
    buf = np.zeros((n, 2), dtype=np.float32)
    for seg in segs:
        t0, t1 = seg["t0"], seg["t0"] + seg["dur"]
        if t1 <= w0 or t0 >= w1:
            continue
        nb = int(seg["dur"] / BLK)
        g = seg.get({"old": "g_old", "a": "g_a", "b": "g_b"}[variant],
                    seg.get("g_old"))
        if g is None:
            g = gain_blocks(seg, nb)
            seg["g_old"] = g
        a = audio(seg["path"])
        i0 = int(seg["s0"] * SR)
        src = a[i0:i0 + nb * BLK_N, :]
        gain = np.repeat(g, BLK_N)[:len(src), None]
        piece = src * gain
        off = int((t0 - w0) * SR)
        p0, p1 = max(0, -off), min(len(piece), n - off)
        if p1 > p0:
            buf[off + p0:off + p1] += piece[p0:p1]
    return buf


def main():
    d, segs = load_draft()
    total = d["duration"] / SEC
    voice = voice_intervals(segs)
    region = region_grid(voice, total)
    music_analysis(segs, region)

    meters = {v: music_meter(segs, total, f"g_{v}") for v in ("old", "a")}
    hook_end = max((s["t0"] + s["dur"] for s in segs
                    if s.get("hook") and s["track"] == "music"), default=0.0)
    edges = [0.0] + [t for ab in voice for t in ab] + [total]
    gaps = list(zip(edges[::2], edges[1::2])) if voice else []
    print(f"video {total:.0f}s | hook zone tới {hook_end:.0f}s | "
          f"band thở {BREATH_BAND} / voice {VOICE_BAND} (LUFS lớp nhạc)\n")
    print(f"{'ô thở':>18} | {'OLD':>6} | {'A':>6} | zone")
    for a, b in gaps:
        if b - a < MIN_BREATH or b > total:
            continue
        i0, i1 = int(a / BLK), int(b / BLK)
        row = [float(np.percentile(meters[v][i0:i1], 95)) for v in ("old", "a")]
        z = "hook" if b <= hook_end else ""
        flag = "" if BREATH_BAND[0] <= row[0] <= BREATH_BAND[1] else "  <-- OLD lệch"
        print(f"{a:7.1f}s–{b:7.1f}s | {row[0]:6.1f} | {row[1]:6.1f} | {z:4}{flag}")

    voiced = region[:len(meters["old"])] == 0
    print("\nnhạc dưới voice — phân bố LUFS (p5/p25/median/p75/p95) + % ngoài band:")
    for v in ("old", "a"):
        m = meters[v][:len(region)][voiced]
        m = m[m > -55]
        pct = [float(np.percentile(m, p)) for p in (5, 25, 50, 75, 95)]
        out_pct = 100 * np.mean((m < VOICE_BAND[0]) | (m > VOICE_BAND[1]))
        print(f"  {v.upper():>3}: " + " / ".join(f"{x:6.1f}" for x in pct) +
              f"  | ngoài band {out_pct:4.1f}%")

    OUT.mkdir(parents=True, exist_ok=True)
    outs = []
    for w0, w1 in EXCERPTS:
        for v in ("old", "a"):
            outs.append((OUT / f"{int(w0)}s-{int(w1)}s_{v.upper()}.wav",
                         render(segs, w0, w1, v)))
    trim = max(float(np.abs(b).max()) for _, b in outs)
    k = 0.99 / trim if trim > 0.99 else 1.0
    for p, buf in outs:
        sf.write(str(p), buf * k, SR, subtype="PCM_16")
    print(f"\nĐã ghi {len(outs)} file nghe thử vào {OUT}" +
          (f" (hạ chung {-db(np.array([k]))[0]:.1f} dB chống clip — so OLD/A vẫn chuẩn)" if k < 1 else ""))


if __name__ == "__main__":
    main()
