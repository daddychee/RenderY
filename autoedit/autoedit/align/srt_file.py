"""Backend align đọc file .srt có sẵn — KHÔNG cần Whisper.

Voice của user luôn kèm .srt (trích từ kịch bản gốc, đã có timestamp). Đọc thẳng
file đó nhanh hơn và chính xác hơn nhận dạng lại: chữ trong .srt là chữ THẬT của
kịch bản, không phải chữ Whisper đoán.

.srt cho timestamp theo CÂU, còn matcher cần theo TỪ -> chia đều thời lượng câu cho
các từ trong câu. Sai số trong câu không quan trọng: matcher chỉ dùng RawWord làm MỎ NEO
để khớp với script gốc, và stage cut sau đó ĐO LẠI khởi âm thật bằng silencedetect
(cutter/runner.py:_onset_in_zone). Mốc câu — thứ duy nhất cần chính xác — lấy nguyên từ .srt.
"""

from __future__ import annotations

import re
from pathlib import Path

from autoedit.align.base import RawWord

# "00:01:23,456 --> 00:01:25,789" — dấu thập phân là ',' (chuẩn SRT) hoặc '.' (biến thể)
_TIME_LINE = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})"
)


def _to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000


def parse_srt(text: str) -> list[tuple[float, float, str]]:
    """Đọc .srt -> [(start, end, câu)]. Bỏ qua block hỏng thay vì chết cả file."""
    out: list[tuple[float, float, str]] = []
    # Block cách nhau bằng dòng trống; \r để chịu được file CRLF của Windows
    for block in re.split(r"\r?\n\s*\r?\n", text.strip()):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        for i, line in enumerate(lines):
            m = _TIME_LINE.search(line)
            if not m:
                continue
            start = _to_seconds(*m.group(1, 2, 3, 4))
            end = _to_seconds(*m.group(5, 6, 7, 8))
            # Mọi dòng sau dòng thời gian là lời thoại (câu dài xuống dòng trong .srt)
            caption = " ".join(lines[i + 1:]).strip()
            if caption and end > start:
                out.append((start, end, caption))
            break
    return out


def words_from_captions(captions: list[tuple[float, float, str]]) -> list[RawWord]:
    """Chia đều thời lượng mỗi câu cho các từ trong câu."""
    words: list[RawWord] = []
    for start, end, caption in captions:
        tokens = caption.split()
        if not tokens:
            continue
        slot = (end - start) / len(tokens)
        for i, tok in enumerate(tokens):
            w_start = start + i * slot
            words.append(RawWord(text=tok, start=w_start, end=w_start + slot))
    return words


class SrtAligner:
    """Aligner đọc .srt cạnh file voice. Cùng interface với FasterWhisperAligner."""

    def __init__(self, srt_path: Path | None = None) -> None:
        self.srt_path = srt_path

    def find_srt(self, audio_path: Path) -> Path | None:
        """.srt cùng tên với voice, hoặc file .srt duy nhất trong cùng thư mục."""
        if self.srt_path:
            return self.srt_path if self.srt_path.is_file() else None
        same_name = audio_path.with_suffix(".srt")
        if same_name.is_file():
            return same_name
        found = sorted(audio_path.parent.glob("*.srt"))
        return found[0] if len(found) == 1 else None

    def transcribe(self, audio_path: Path) -> list[RawWord]:
        path = self.find_srt(audio_path)
        if path is None:
            raise FileNotFoundError(
                f"Không thấy .srt cho {audio_path.name}. Đặt file .srt cùng tên cạnh voice, "
                f"chỉ đường dẫn bằng --srt, hoặc dùng --backend whisper để nhận dạng lại."
            )
        # utf-8-sig: .srt xuất từ Windows/CapCut hay có BOM
        captions = parse_srt(path.read_text(encoding="utf-8-sig"))
        if not captions:
            raise ValueError(
                f"{path.name} không có block nào đọc được — file rỗng hoặc sai định dạng SRT "
                f"(cần dòng '00:00:01,000 --> 00:00:03,000' rồi tới lời thoại)."
            )
        return words_from_captions(captions)
