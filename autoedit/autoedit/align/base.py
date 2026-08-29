"""Interface Aligner — tách rời backend (CLAUDE.md: dev dùng faster-whisper CPU,
sau cắm WhisperX GPU hoặc Replicate API mà không sửa pipeline)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class RawWord:
    """1 từ do backend nhận dạng, timestamp tính bằng giây trên file voice gốc."""

    text: str
    start: float
    end: float


class Aligner(Protocol):
    """Backend nhận dạng + word timestamp. Mọi backend phải trả RawWord theo giây."""

    def transcribe(self, audio_path: Path) -> list[RawWord]: ...
