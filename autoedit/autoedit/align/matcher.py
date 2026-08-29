"""Đối chiếu transcript Whisper với script gốc — script là ground truth.

Phòng lỗi (RA_SOAT_LOGIC):
- 1.1 Whisper nhận sai tên riêng/từ hiếm -> alignment kiểu "mỏ neo": khớp các từ
  chắc chắn đúng (SequenceMatcher), nội suy timestamp cho từ giữa 2 neo.
- 0.2 ElevenLabs đọc khác văn bản ("$2" -> "two dollars") -> so khớp trên token
  đã chuẩn hóa; từ không khớp được thì nội suy chứ không vứt.

Kết quả: mỗi từ CỦA SCRIPT có timestamp; từ nội suy đánh dấu `interpolated=True`
để stage sau (cắt voice) biết tin cậy thấp hơn.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from autoedit.align.base import RawWord
from autoedit.project import Word

_PUNCT = re.compile(r"[^\w$%]+", re.UNICODE)


def normalize_token(token: str) -> str:
    """Chuẩn hóa 1 token để so khớp: thường hóa, bỏ dấu câu quanh từ."""
    return _PUNCT.sub("", token.lower())


def tokenize_script(text: str) -> list[str]:
    """Tách script thành token theo whitespace, giữ nguyên chữ gốc (ground truth)."""
    return text.split()


@dataclass
class MatchResult:
    words: list[Word]          # mỗi từ script, có timestamp
    match_ratio: float         # tỷ lệ từ script khớp neo trực tiếp (0..1)


def match_script_to_whisper(
    script_text: str,
    whisper_words: list[RawWord],
    audio_duration: float | None = None,
) -> MatchResult:
    """Gắn timestamp cho TỪNG TỪ của script từ transcript Whisper."""
    script_tokens = tokenize_script(script_text)
    if not script_tokens:
        return MatchResult(words=[], match_ratio=0.0)
    if not whisper_words:
        raise ValueError("Whisper không trả từ nào — voice rỗng hoặc nhận dạng hỏng?")

    norm_script = [normalize_token(t) for t in script_tokens]
    norm_whisper = [normalize_token(w.text) for w in whisper_words]

    # Mỏ neo: các block khớp chính xác giữa 2 chuỗi token chuẩn hóa
    matcher = SequenceMatcher(None, norm_script, norm_whisper, autojunk=False)
    anchor: dict[int, RawWord] = {}  # script index -> whisper word
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            si, wi = block.a + k, block.b + k
            if norm_script[si]:  # token rỗng (dấu câu thuần) không làm neo
                anchor[si] = whisper_words[wi]

    n = len(script_tokens)
    last_known_end = whisper_words[-1].end
    total_end = audio_duration if audio_duration else last_known_end

    words: list[Word] = []
    i = 0
    while i < n:
        if i in anchor:
            w = anchor[i]
            words.append(Word(text=script_tokens[i], start=w.start, end=w.end))
            i += 1
            continue
        # Gom cả cụm không khớp liên tiếp rồi nội suy tuyến tính giữa 2 neo
        j = i
        while j < n and j not in anchor:
            j += 1
        gap_start = words[-1].end if words else (anchor[j].start - 1.0 if j < n else 0.0)
        gap_start = max(gap_start, 0.0)
        gap_end = anchor[j].start if j < n else total_end
        gap_end = max(gap_end, gap_start)
        slot = (gap_end - gap_start) / (j - i)
        for k in range(i, j):
            s = gap_start + (k - i) * slot
            words.append(Word(text=script_tokens[k], start=s, end=s + slot, interpolated=True))
        i = j

    match_ratio = len(anchor) / n
    return MatchResult(words=words, match_ratio=match_ratio)
