"""Backend faster-whisper chạy CPU — đủ cho dev (video 10 phút mất vài phút).

Phòng lỗi (RA_SOAT_LOGIC Stage 1):
- 1.2 Whisper ảo giác khi lặng dài -> vad_filter=True (chỉ align phần có tiếng)
- 1.3 File dài tràn bộ nhớ -> faster-whisper tự stream theo segment trên CPU;
  chưa cần chunk thủ công ở Phase 0 (video 10-15 phút). Ghi chú lại nếu lên 30-40p.
"""

from __future__ import annotations

import os
from pathlib import Path

from autoedit.align.base import RawWord


def _default_cpu_threads() -> int:
    """Số nhân CPU cho ctranslate2: dùng nhiều nhân (máy 14700K có 20 nhân) nhưng
    cap 16 để không chiếm hết máy. Tăng tốc THUẦN — không đổi kết quả align."""
    return min(16, os.cpu_count() or 4)


class FasterWhisperAligner:
    """Aligner dùng faster-whisper local. Model mặc định `small` (cân bằng tốc độ/độ chính xác CPU).

    Tối ưu CPU (phương án B): chạy đa nhân (cpu_threads) + beam_size=1 (greedy, nhanh hơn
    beam search; ta đã có SCRIPT để matcher đối chiếu nên sai sót decode được sửa lại).
    """

    def __init__(
        self,
        model_size: str = "small",
        language: str | None = "auto",
        cpu_threads: int | None = None,
        beam_size: int = 1,
    ) -> None:
        self.model_size = model_size
        # "auto"/None -> whisper tự nhận diện ngôn ngữ (script công ty có cả EN lẫn VI)
        self.language = None if language in (None, "auto") else language
        self.cpu_threads = cpu_threads or _default_cpu_threads()
        self.beam_size = beam_size
        self._model = None  # lazy: tải model lần đầu transcribe

    def _ensure_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel  # import chậm, để trong hàm

            self._model = WhisperModel(
                self.model_size, device="cpu", compute_type="int8",
                cpu_threads=self.cpu_threads,
            )
        return self._model

    def transcribe(self, audio_path: Path) -> list[RawWord]:
        model = self._ensure_model()
        segments, _info = model.transcribe(
            str(audio_path),
            language=self.language,
            word_timestamps=True,
            vad_filter=True,  # 1.2: bỏ khoảng lặng, tránh ảo giác
            beam_size=self.beam_size,  # B: greedy nhanh hơn, matcher bù sai sót decode
        )
        words: list[RawWord] = []
        for seg in segments:
            for w in seg.words or []:
                words.append(RawWord(text=w.word.strip(), start=w.start, end=w.end))
        return words
