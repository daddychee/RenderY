"""Stage 1 — Align: chạy backend + đối chiếu script, ghi vào project.json.

Cảnh báo (không chặn, ghi vào stages.align.warnings để report hiển thị):
- 0.1 script/voice lệch >5% từ không khớp neo -> nghi writer sửa script sau khi gen voice
- 1.4 lệch duration transcript vs file -> nghi lệch tích lũy / voice thiếu đoạn
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from autoedit.align.base import Aligner
from autoedit.align.matcher import match_script_to_whisper
from autoedit.project import Project, Stage, StageRecord, StageStatus

MATCH_RATIO_MIN = 0.95   # 0.1: dưới mức này -> cảnh báo đỏ script/voice không khớp
TAIL_SILENCE_MAX = 3.0   # giây lặng cuối file chấp nhận được trước khi nghi thiếu đoạn


def run_align(project: Project, aligner: Aligner) -> Project:
    """Chạy align cho project, ghi transcript + trạng thái stage, save."""
    project_dir = Path(project.project_dir)
    voice_path = project_dir / project.inputs.voice_path

    record = StageRecord.running()
    project.stages[Stage.ALIGN] = record
    project.save()

    try:
        raw_words = aligner.transcribe(voice_path)
        result = match_script_to_whisper(
            project.inputs.script_text,
            raw_words,
            audio_duration=project.inputs.voice_duration_sec,
        )
    except Exception as exc:
        record.status = StageStatus.FAILED
        record.error = str(exc)
        project.save()
        raise

    if result.match_ratio < MATCH_RATIO_MIN:
        record.warnings.append(
            f"Script và voice lệch nhau: chỉ {result.match_ratio:.0%} từ khớp trực tiếp "
            f"(ngưỡng {MATCH_RATIO_MIN:.0%}). Kiểm tra writer có sửa script sau khi gen voice không."
        )

    duration = project.inputs.voice_duration_sec
    if duration and result.words:
        last_end = result.words[-1].end
        if last_end > duration + 0.5:
            record.warnings.append(
                f"Timestamp từ cuối ({last_end:.1f}s) vượt duration file ({duration:.1f}s) — lệch tích lũy?"
            )
        elif duration - last_end > TAIL_SILENCE_MAX:
            record.warnings.append(
                f"File dài hơn lời thoại {duration - last_end:.1f}s — voice có đoạn chưa align?"
            )

    project.transcript = result.words
    record.status = StageStatus.DONE
    record.completed_at = datetime.now(timezone.utc).isoformat()
    project.save()

    # transcript.json riêng cho người xem nhanh (project.json vẫn là nguồn sự thật)
    (project_dir / "transcript.json").write_text(
        json.dumps(
            {
                "match_ratio": round(result.match_ratio, 4),
                "warnings": record.warnings,
                "words": [w.model_dump() for w in result.words],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return project
