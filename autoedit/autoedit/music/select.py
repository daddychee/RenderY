"""Chọn nhạc theo CHƯƠNG — THU_VIEN_NHAC mục 5.

Input: chương (mood/energy/music_hint + dải timeline) + index thư viện. Lọc cứng
(instrumental + đủ dài/loopable + chưa dùng trong video) → chấm điểm (mood/energy/tempo)
→ chọn bài hợp nhất, không lặp trong 1 video. Trả [(chapter_id, track, start_offset)].
"""

from __future__ import annotations

from autoedit.music.library import MOOD, _norm

# mood chương (free-text LLM) -> vocabulary nhạc đóng
_MOOD_SYNONYMS: dict[str, set] = {
    "warm": {"hopeful", "peaceful", "romantic"}, "inviting": {"hopeful", "peaceful"},
    "calm": {"peaceful"}, "relaxed": {"peaceful"}, "gentle": {"peaceful", "dreamy"},
    "reflective": {"nostalgic", "peaceful"}, "emotional": {"nostalgic", "sad"},
    "melancholic": {"sad", "nostalgic"}, "bittersweet": {"nostalgic", "hopeful"},
    "tense": {"tense", "suspenseful"}, "anticipatory": {"suspenseful"},
    "urgent": {"tense"}, "anxious": {"tense"}, "ominous": {"dark", "mysterious"},
    "grim": {"dark"}, "grand": {"epic"}, "triumphant": {"epic", "uplifting"},
    "joyful": {"happy"}, "fun": {"playful", "happy"}, "light": {"playful", "hopeful"},
    "curious": {"mysterious"}, "wonder": {"dreamy", "hopeful"},
    "motivational": {"inspiring", "determined", "uplifting"},
    "confident": {"determined"}, "relatable": {"hopeful", "peaceful"},
    # PB4: GLM tag footage đồ ăn khăng khăng 2 từ này (fail cả feedback-retry)
    "cozy": {"peaceful", "nostalgic"}, "appetizing": {"happy", "playful"},
    # Mẻ nạp deepsea 2026-07-13: phim tài liệu biển sâu — GLM khăng khăng 12 từ này
    # (~300/8994 cảnh fail 4-retry; educational 151 + creepy 105 áp đảo)
    "educational": {"serious"}, "informative": {"serious"}, "scientific": {"serious"},
    "creepy": {"dark", "scary"}, "protective": {"determined"}, "serene": {"peaceful"},
    "neutral": {"peaceful"}, "nautical": {"mysterious"}, "strange": {"mysterious"},
    "interesting": {"mysterious"}, "historical": {"nostalgic"}, "busy": {"playful"},
    # Mẻ nạp life-in 2026-07-15: documentary quốc gia/văn hóa — GLM khăng khăng 21 từ
    # này (104/770 cảnh mẻ 1 fail 4-retry; spiritual 21 + lively 19 + traditional 15
    # + cultural 14 + everyday 12 áp đảo — tiền lệ PB4/deepsea)
    "spiritual": {"peaceful"}, "sacred": {"peaceful", "serious"},
    "lively": {"playful", "uplifting"}, "vibrant": {"playful", "uplifting"},
    "energetic": {"playful", "uplifting"}, "dynamic": {"determined"},
    "traditional": {"nostalgic"}, "cultural": {"nostalgic"}, "authentic": {"nostalgic"},
    "vintage": {"nostalgic"}, "everyday": {"peaceful"}, "urban": {"playful"},
    "crowded": {"playful"}, "festive": {"happy", "playful"},
    "opulent": {"epic"}, "luxurious": {"epic"}, "futuristic": {"epic", "mysterious"},
    "respectful": {"serious"}, "efficient": {"determined"}, "helpful": {"hopeful"},
    "artistic": {"dreamy"},
    # Mẻ 4 life-in 2026-07-15: đuôi thứ hai (51 cảnh fail; desolate 12 + elegant 6).
    # Từ chỉ-1-lần không map — validator đã mềm: mood lạ bị BỎ khi còn mood hợp lệ.
    "desolate": {"sad", "dark"}, "elegant": {"peaceful", "romantic"},
    "exclusive": {"epic"}, "glamorous": {"epic", "romantic"},
    "scenic": {"peaceful", "dreamy"}, "nighttime": {"mysterious"},
    "night": {"mysterious"}, "historic": {"nostalgic"}, "patriotic": {"epic",
    "inspiring"}, "natural": {"peaceful"}, "organic": {"peaceful"},
    "solemn": {"serious"}, "powerful": {"epic", "determined"}, "isolated": {"mysterious"},
}


def _chapter_moods(chapter: dict) -> set:
    """Suy tập mood vocab từ chapter.mood + music_hint (free-text)."""
    text = f"{chapter.get('mood', '')} {chapter.get('music_hint', '')}".lower()
    toks = {t for t in _norm(text).split("_") if t}
    out: set = set()
    for t in toks:
        if t in MOOD:
            out.add(t)
        out |= _MOOD_SYNONYMS.get(t, set())
    return out


# ---------------------------------------------------------------------------
# ĐỘ DỒN (drive) — thay tín hiệu `energy` librosa (rms.mean/rms.max = độ PHẲNG,
# hiệu chuẩn 2026-07-14 trên 29 bài NHỊP NHANH user tuyển tai: đo 0 bài "high",
# nhạc punchy điểm THẤP hơn drone — ngược chiều). Tín hiệu đứng được:
# mood (tai người gán) > beat_tier (nhịp rõ) > bpm (đã gấp về [70,150), yếu nhất).
# ---------------------------------------------------------------------------
_MOOD_DRIVE = {
    "tense": 0.95, "angry": 0.95, "epic": 0.9, "scary": 0.85, "determined": 0.8,
    "suspenseful": 0.65, "playful": 0.6, "happy": 0.6, "dark": 0.55,
    "uplifting": 0.55, "inspiring": 0.55, "mysterious": 0.45, "serious": 0.45,
    "hopeful": 0.4, "nostalgic": 0.3, "dreamy": 0.2, "romantic": 0.2,
    "sad": 0.15, "peaceful": 0.1,
}
_WANT_DRIVE = {"low": 0.2, "medium": 0.5, "high": 0.85}
_WANT_INTENSITY = {"low": 0.35, "medium": 0.65, "high": 1.0}  # energy_curve trong-bài 0-1


def _track_drive(track: dict) -> float:
    """Độ dồn 0-1 của bài: mood 0.6 + beat_tier 0.25 + bpm 0.15."""
    ds = [_MOOD_DRIVE[m] for m in track.get("mood", []) if m in _MOOD_DRIVE]
    mood_d = max(ds) if ds else 0.5
    tier = {"A": 1.0, "B": 0.5}.get(track.get("beat_tier"), 0.0)
    bpm_n = min(1.0, max(0.0, ((track.get("bpm") or 100.0) - 70.0) / 80.0))
    return 0.6 * mood_d + 0.25 * tier + 0.15 * bpm_n


def _entry_span(chapter_energy: str, track: dict):
    """Đoạn nhạc sẽ VÀO theo energy chương — cùng logic _start_offset (bpm/độ dồn
    đổi theo đoạn trong bài: chấm bài tại đoạn dùng thật, không chấm trung bình)."""
    secs = track.get("sections") or {}
    if chapter_energy == "high" and secs.get("drop"):
        return secs["drop"]
    if chapter_energy == "medium" and secs.get("build"):
        return secs["build"]
    return secs.get("intro")


def _entry_intensity(track: dict, span) -> float:
    """Cường độ energy_curve (chuẩn hóa TRONG bài — so đoạn-với-đoạn cùng bài mới
    hợp lệ) tại đoạn vào nhạc. Trả -1 nếu thiếu dữ liệu."""
    curve = track.get("energy_curve") or []
    dur = track.get("duration_sec") or 0
    if not curve or not span or dur <= 0 or span[1] <= span[0]:
        return -1.0
    step = dur / len(curve)
    vals = [v for i, v in enumerate(curve)
            if i * step < span[1] and (i + 1) * step > span[0]]
    return sum(vals) / len(vals) if vals else -1.0


def _score(chapter: dict, track: dict) -> float:
    want = _chapter_moods(chapter)
    tmood = set(track.get("mood", []))
    mood_s = len(want & tmood) / len(want) if want else 0.0
    ce = chapter.get("energy", "medium")
    drive_s = 1.0 - abs(_track_drive(track) - _WANT_DRIVE.get(ce, 0.5))
    inten = _entry_intensity(track, _entry_span(ce, track))
    entry_s = 1.0 - abs(inten - _WANT_INTENSITY.get(ce, 0.65)) if inten >= 0 else 0.5
    return 0.6 * mood_s + 0.25 * drive_s + 0.15 * entry_s


def select_music(chapters: list[dict], index: list[dict], used: set | None = None,
                 usage: dict | None = None) -> list[dict]:
    """Trả [{chapter_id, file, start_offset, score, track}] — 1 bài/chương, không lặp trong video.
    usage: {file: số lần đã dùng video trước} -> phạt mềm để ĐA DẠNG giữa các video."""
    used = set() if used is None else used
    usage = usage or {}
    picks = []
    for ch in chapters:
        ch_len = max(0.0, ch.get("timeline_end", 0) - ch.get("timeline_start", 0))
        cands = [
            t for t in index
            if t.get("vocals", "instrumental") in ("instrumental", "vocal_samples")
            and t["file"] not in used
            and (t.get("loopable", True) or t.get("duration_sec", 0) >= ch_len)
        ]
        if not cands:  # hết bài chưa dùng -> cho phép tái dùng (đỡ thiếu nhạc)
            cands = [t for t in index
                     if t.get("vocals", "instrumental") in ("instrumental", "vocal_samples")]
        if not cands:
            continue
        # điểm + phạt mềm bài đã dùng nhiều (đa dạng giữa video), tối đa -0.2
        def _ranked(t):
            penalty = min(0.2, 0.04 * usage.get(t["file"], 0))
            return _score(ch, t) - penalty
        best = max(cands, key=_ranked)
        used.add(best["file"])
        picks.append({
            "chapter_id": ch.get("chapter_id"),
            "file": best["file"],
            "start_offset": _start_offset(ch, best),   # M-N3: canh vào nhạc theo sections
            "score": round(_score(ch, best), 3),
            "track": best,
        })
    return picks


def _start_offset(chapter: dict, track: dict) -> float:
    """Canh điểm bắt đầu nhạc theo năng lượng chương (THU_VIEN mục 5):
    chương cao trào -> vào ngay đoạn 'drop' (mạnh nhất); chương lắng -> 'intro' (êm)."""
    secs = track.get("sections") or {}
    energy = chapter.get("energy", "medium")
    if energy == "high" and secs.get("drop"):
        return float(secs["drop"][0])
    if energy == "medium" and secs.get("build"):
        return float(secs["build"][0])
    return 0.0   # low / không có section -> bắt đầu từ intro
