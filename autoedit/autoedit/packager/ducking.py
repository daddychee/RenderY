"""F8 — Ducking v1: nhạc nép khi voice nói, nở ở khoảng hình thở (keyframe volume).

Lịch voice/thở lấy từ cấu trúc timeline ĐÃ BIẾT (project.segments) — không dò waveform.
Behavior CapCut kiểm bằng draft test ducking-kf-test-v2 (mắt user 2026-07-04, memory
capcut-volume-keyframe): offset keyframe tính từ ĐẦU CLIP, giá trị là mức TUYỆT ĐỐI
(đè volume tĩnh), fade/crossfade sống chung keyframe. Chi tiết: MO_TA_VAN_HANH_DUCKING.md.
"""

from __future__ import annotations

SEC = 1_000_000
EDGE_GUARD_US = 1_000  # keyframe cuối lùi 1ms khỏi mép clip (mép-đúng-µs chưa kiểm)

# 🔸 điểm treo (MO_TA_VAN_HANH_DUCKING.md mục 4) — chốt bằng tai user (V6) + DNA niche
BREATH_VOL = 0.5   # nhạc NỞ lúc thở (~+8dB so với mức nép 0.2)

# 🔸 M-VOL (MUSIC SYNC M2, MO_TA_VAN_HANH_MUSIC_SYNC.md §1): nhạc HOOK to hơn thân bài
# theo niche (đo editor: space hook 0.377/body 0.076; deepsea 0.474/0.355). Thân bài
# GIỮ 0.2/0.5 đã qua cổng tai V10. CHỈ áp khi music_plan có (music-sync bật) — mức
# tuyệt đối chỉnh ở cổng TAI M2.
HOOK_DUCK = {"space": 0.35, "deepsea": 0.30}
HOOK_DUCK_DEFAULT = 0.30


def hook_duck_for(niche: str | None) -> float:
    """Mức nhạc-nép trong voice ở HOOK theo niche (thân bài vẫn MUSIC_VOLUME 0.2)."""
    return HOOK_DUCK.get((niche or "").strip().lower(), HOOK_DUCK_DEFAULT)
RAMP = 2.5         # giây đi trọn nép->nở; dốc CỐ ĐỊNH (user chốt >2s, 2026-07-04)
MIN_BREATH = 1.5   # khoảng nghỉ ngắn hơn -> nhạc giữ mức nép (chống pumping).
                   # 1.0->1.5 (hình thở 3.0): giãn máy DNA lên tới gap 1,2s ở NHIỀU câu
                   # — giữ 1.0 là nhạc phập phồng theo câu; 1.5 = sàn breathing đạo diễn
                   # nên mọi ô thở thật vẫn nở.


def merge_voice_intervals(segments, min_gap: float = MIN_BREATH) -> list[tuple[float, float]]:
    """[(timeline_start, timeline_end)] các đoạn voice; nuốt khoảng nghỉ < min_gap."""
    out: list[list[float]] = []
    for a, b in sorted((s.timeline_start, s.timeline_end) for s in segments):
        if out and a - out[-1][1] < min_gap:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def build_envelope(
    voice: list[tuple[float, float]],
    total_end: float,
    duck: float,
    breath: float = BREATH_VOL,
    ramp: float = RAMP,
    min_gap: float = MIN_BREATH,
) -> list[tuple[float, float]]:
    """Đường volume nhạc toàn timeline: điểm gãy (giây, vol), nội suy tuyến tính giữa
    các điểm, ngoài 2 đầu giữ hằng. Dốc CỐ ĐỊNH (hết nép->nở trong `ramp` giây):
    khoảng thở ngắn hơn 2*ramp chỉ phồng một phần — không dốc gắt hơn để nhét đủ mức."""
    if not voice:
        return [(0.0, breath)]
    slope = (breath - duck) / ramp
    pts: list[tuple[float, float]] = []

    head = voice[0][0]                                # nhạc dạo trước câu đầu tiên
    if head >= min_gap:
        r = min(ramp, head)
        pts += [(0.0, duck + slope * r), (head - r, duck + slope * r)]
    pts.append((head, duck))

    for (_, b), (a2, _) in zip(voice, voice[1:]):     # khoảng thở giữa 2 đoạn voice
        r = min(ramp, (a2 - b) / 2)
        peak = duck + slope * r
        pts += [(b, duck), (b + r, peak), (a2 - r, peak), (a2, duck)]

    tail = voice[-1][1]                               # khoảng thở kết video: nở rồi
    pts.append((tail, duck))                          # giữ (fade-out nhạc lo phần cuối)
    if total_end - tail >= min_gap:
        r = min(ramp, total_end - tail)
        pts.append((tail + r, duck + slope * r))

    out: list[tuple[float, float]] = []               # khử điểm trùng (gap == 2*ramp...)
    for t, v in pts:
        if out and abs(t - out[-1][0]) < 1e-9:
            continue
        out.append((t, v))
    return out


def envelope_at(env: list[tuple[float, float]], t: float) -> float:
    """Giá trị đường volume tại giây t."""
    if t <= env[0][0]:
        return env[0][1]
    for (t0, v0), (t1, v1) in zip(env, env[1:]):
        if t <= t1:
            return v0 if t1 == t0 else v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return env[-1][1]


def segment_keyframes(
    env: list[tuple[float, float]], start_us: int, dur_us: int, duck: float
) -> list[tuple[int, float]]:
    """Keyframe (offset_µs từ đầu clip, vol tuyệt đối) cho 1 clip nhạc trên timeline.
    Trả [] nếu cả clip nằm ở mức nép — volume tĩnh của clip đã đúng, đỡ rác keyframe."""
    t0, t1 = start_us / SEC, (start_us + dur_us) / SEC
    pts = [(t0, envelope_at(env, t0))]
    pts += [p for p in env if t0 < p[0] < t1]
    pts.append((t1, envelope_at(env, t1)))
    if all(abs(v - duck) < 1e-6 for _, v in pts):
        return []
    out: list[tuple[int, float]] = []
    ceil_off = max(dur_us - EDGE_GUARD_US, 0)
    for t, v in pts:
        off = min(max(round((t - t0) * SEC), 0), ceil_off)  # round(): bài học 1µs
        if out and off <= out[-1][0]:
            continue
        out.append((off, v))
    return out
