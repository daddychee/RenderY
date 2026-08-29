"""Phân tích KHÁCH QUAN 1 bản nhạc bằng librosa — THU_VIEN_NHAC mục 2/4.

Lấy thứ Artlist KHÔNG cung cấp: BPM (chống lỗi gấp đôi/nửa), energy + energy_curve,
sections (intro/build/drop/outro suy từ energy), loopable. Tag mood/genre lấy từ Cowork.
Tải sr thấp (22.05k mono) cho nhanh; lỗi -> trả mặc định an toàn (không chặn import).

MUSIC SYNC M0 (2026-07-13): thêm nhịp/accent cho MỌI bài — beat_times/downbeats/accents/
beat_quality → beat_tier A (nhịp rõ, full sync) / B (yếu, chỉ accent) / C (ambient, TẮT sync).
"""

from __future__ import annotations

from pathlib import Path

TEMPO_BANDS = [(70, "very_slow"), (90, "slow"), (110, "medium"),
               (135, "medium_fast"), (10_000, "fast")]

# 🔸 MUSIC SYNC M0 (MO_TA_VAN_HANH_MUSIC_SYNC.md §5) — ngưỡng tier chốt lại sau backfill
ACCENT_PCTL = 70          # onset mạnh = percentile 70 trở lên
ACCENT_MIN_GAP = 1.0      # giây — accent thưa, không phải grid đều
TIER_A_QUALITY = 2.2      # nhịp rõ (full sync) — 2.2 chốt sau backfill 2026-07-13: dải
                          # 2.0-2.2 của pool toàn ambient tên tay ("dưới nước 4" 2.08,
                          # "nền deepsea trầm sợ" 2.09) + dreamy nhẹ; 2.2-2.5 nhịp thật
TIER_B_QUALITY = 1.3      # nhịp yếu (chỉ accent)
MIN_BEATS = 16            # ít hơn -> không đủ grid tin được


def tempo_class(bpm: float) -> str:
    for hi, name in TEMPO_BANDS:
        if bpm < hi:
            return name
    return "fast"


def _fix_bpm(bpm: float) -> float:
    """Đưa BPM về dải nghe được [70,150) — librosa hay nhận gấp đôi/nửa."""
    if bpm <= 0:
        return 100.0
    while bpm < 70:
        bpm *= 2
    while bpm >= 150:
        bpm /= 2
    return round(bpm, 1)


def analyze_track(path: Path, n_buckets: int = 8) -> dict:
    """Trả dict: duration_sec, bpm, tempo_class, energy, energy_curve, sections, loopable."""
    import librosa
    import numpy as np

    y, sr = librosa.load(str(path), sr=22050, mono=True)
    dur = float(librosa.get_duration(y=y, sr=sr))

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    bpm = _fix_bpm(float(np.atleast_1d(tempo)[0]))

    rms = librosa.feature.rms(y=y)[0]
    energy = float(np.clip(rms.mean() / (rms.max() + 1e-9), 0, 1)) if rms.size else 0.5
    # energy_curve: chia n_buckets theo thời gian, RMS trung bình mỗi đoạn, chuẩn hóa 0-1
    curve = []
    if rms.size:
        chunks = np.array_split(rms, n_buckets)
        peak = rms.max() + 1e-9
        curve = [round(float(c.mean() / peak), 3) for c in chunks if c.size]

    sections = _sections_from_curve(curve, dur)
    # loopable: đầu và cuối năng lượng gần nhau -> nối vòng ít gợn
    loopable = bool(curve and abs(curve[0] - curve[-1]) < 0.25)

    out = {
        "duration_sec": round(dur, 2),
        "bpm": bpm,
        "tempo_class": tempo_class(bpm),
        "energy": round(energy, 3),
        "energy_curve": curve,
        "sections": sections,
        "loopable": loopable,
    }
    out.update(_rhythm_from_signal(y, sr))
    return out


def analyze_rhythm(path: Path) -> dict:
    """MUSIC SYNC M0: đo riêng nhịp/accent (backfill record cũ đã có energy_curve)."""
    import librosa

    y, sr = librosa.load(str(path), sr=22050, mono=True)
    return _rhythm_from_signal(y, sr)


def _rhythm_from_signal(y, sr) -> dict:
    """beat_times / downbeats / accents / beat_quality / beat_tier — NT4: mọi timestamp từ tín hiệu.

    Bẫy đã đo (memory editor-music-sync-study): librosa bịa grid ~120BPM cho cả nhạc
    ambient trôi -> beat_quality = onset-tại-beat / onset-nền để phân tier. Tier C = TẮT
    sync (pipeline chạy y như không có grid — fail-open, quan trọng cho deepsea ambient).
    """
    import librosa
    import numpy as np

    env = librosa.onset.onset_strength(y=y, sr=sr)
    _tempo, beats = librosa.beat.beat_track(onset_envelope=env, sr=sr, units="time")
    beats = np.asarray(beats, dtype=float)
    times = librosa.times_like(env, sr=sr)

    quality = 0.0
    if len(beats):
        idx = np.clip(np.searchsorted(times, beats), 0, len(env) - 1)
        quality = float(env[idx].mean() / (env.mean() + 1e-9))
    if len(beats) >= MIN_BEATS and quality >= TIER_B_QUALITY:
        tier = "A" if quality >= TIER_A_QUALITY else "B"
    else:
        tier = "C"

    # 🔸 MINI-HOOK/HÌNH THỞ (2026-07-19): độ mạnh TẠI TỪNG BEAT, chuẩn hóa 0-1 trong bài.
    # Trước đây env[idx] được tính rồi VỨT (chỉ giữ số vô hướng beat_quality) -> mọi nơi
    # cần "beat này mạnh hay yếu" phải NẠP LẠI file nhạc (scripts_thu_mini_hook.py).
    # Cắt vào beat YẾU kề beat MẠNH bị tai nghe là TRỄ MỘT NHỊP (bug b08/b09 user bắt).
    beat_strength: list[float] = []
    if len(beats):
        idx = np.clip(np.searchsorted(times, beats), 0, len(env) - 1)
        st = env[idx]
        peak = float(st.max()) or 1.0
        beat_strength = [round(float(v) / peak, 3) for v in st]

    downbeats = []
    if tier == "A" and len(beats) >= 8:
        # ước lượng pha mạnh: nhóm 4 beat, pha có onset tổng lớn nhất = downbeat
        idx = np.clip(np.searchsorted(times, beats), 0, len(env) - 1)
        strength = env[idx]
        phase = max(range(4), key=lambda p: float(strength[p::4].mean()))
        downbeats = [round(float(b), 3) for b in beats[phase::4]]

    accents, accent_strength = _pick_accents(env, times, sr)
    return {
        # tier C: grid librosa BỊA ra -> không lưu (fail-open, luật cũ). Độ mạnh đi kèm
        # beat_times nên phải rỗng CÙNG LÚC, nếu không hai mảng lệch độ dài.
        "beat_times": [round(float(b), 3) for b in beats] if tier != "C" else [],
        "beat_strength": beat_strength if tier != "C" else [],
        "downbeats": downbeats,
        "accents": accents,
        "accent_strength": accent_strength,
        "beat_quality": round(quality, 3),
        "beat_tier": tier,
    }


def analyze_downbeats(path: Path) -> dict:
    """NHIP-M4 (foundation e2, user chốt 2026-07-21): downbeat + số phách/ô nhịp bằng
    madmom RNN — trả {downbeats: [giây phách "1"], meter: 3|4}.

    Vì sao KHÔNG dùng librosa cho việc này: librosa đo tempo tốt nhưng MÙ PHA — hàm
    downbeat cũ ở `_rhythm_from_signal` nhóm CỨNG 4 beat, bài nhịp 3 ("End of an Era")
    ra downbeat sai hoàn toàn; beat_times còn dao động 46ms (làm tròn hop_length) nên
    cộng dồn là lưới trôi (GT1 bàn giao M4). madmom DBN học từ data thật, tự chọn
    nhịp 3 hay 4 (beats_per_bar), kháng phách nghịch/trống nhẹ.

    Đo thật "End of an Era": meter 3, 68 downbeat, bar 2,000s — khớp tai user.
    Chỉ gọi lúc KHAI Δ (1 lần/bài, ~10-30s RNN); assemble không đụng madmom.
    Lỗi gì cũng nổ exception cho caller quyết (cli fail-open về lưới librosa cũ)."""
    from madmom.features.downbeats import (DBNDownBeatTrackingProcessor,
                                           RNNDownBeatProcessor)

    act = RNNDownBeatProcessor()(str(path))
    db = DBNDownBeatTrackingProcessor(beats_per_bar=[3, 4], fps=100)(act)
    if db is None or not len(db):
        return {"downbeats": [], "meter": 0}
    meter = int(max(p for _, p in db))
    downs = [round(float(t), 3) for t, p in db if int(p) == 1]
    return {"downbeats": downs, "meter": meter}


def _pick_accents(env, times, sr) -> tuple[list[float], list[float]]:
    """Accent thưa: onset percentile ≥ ACCENT_PCTL, greedy mạnh-trước, min-gap 1s.
    (Cùng phương pháp với nghiên cứu 26 draft editor — lift 2.01 đo trên accent kiểu này.)

    Trả (thời điểm, ĐỘ MẠNH) — hai mảng SONG SONG cùng độ dài, sort theo thời gian.
    Độ mạnh chuẩn hóa 0-1 TRONG BÀI (như energy_curve; KHÔNG so được giữa hai bài).
    Trước 2026-07-19 hàm chỉ trả thời điểm -> mọi accent bị coi là bằng nhau, không
    phân biệt được "cao trào" với "gõ nhẹ" (cần cho lưới beat ở ô thở).
    """
    import librosa
    import numpy as np

    peaks = librosa.onset.onset_detect(onset_envelope=env, sr=sr, units="time",
                                       backtrack=False)
    peaks = np.asarray(peaks, dtype=float)
    if not len(peaks):
        return [], []
    pidx = np.clip(np.searchsorted(times, peaks), 0, len(env) - 1)
    strength = env[pidx]
    thr = np.percentile(strength, ACCENT_PCTL)
    cand = sorted(zip(peaks[strength >= thr], strength[strength >= thr]),
                  key=lambda t: -t[1])
    chosen: list[tuple[float, float]] = []
    for t, s in cand:
        if all(abs(t - c) >= ACCENT_MIN_GAP for c, _ in chosen):
            chosen.append((float(t), float(s)))
    chosen.sort()                                    # về thứ tự THỜI GIAN
    peak = max((s for _, s in chosen), default=0.0) or 1.0
    return ([round(t, 3) for t, _ in chosen],
            [round(s / peak, 3) for _, s in chosen])


def _sections_from_curve(curve: list[float], dur: float) -> dict:
    """Suy intro/build/drop/outro từ energy_curve (THU_VIEN mục 5 cần để canh cao trào)."""
    if not curve or dur <= 0:
        return {}
    n = len(curve)
    step = dur / n
    peak_i = max(range(n), key=lambda i: curve[i])      # đoạn năng lượng cao nhất = drop
    sec = {}
    sec["intro"] = [0.0, round(step, 2)]
    if peak_i > 1:
        sec["build"] = [round(step, 2), round(peak_i * step, 2)]
    sec["drop"] = [round(peak_i * step, 2), round(min((peak_i + 1) * step, dur), 2)]
    if peak_i < n - 1:
        sec["outro"] = [round((n - 1) * step, 2), round(dur, 2)]
    return sec
