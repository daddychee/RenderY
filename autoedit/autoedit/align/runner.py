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
# CHẶN lúc nộp tập (user chốt 17/09: "nên kiểm trước khi chạy"). Ngưỡng lấy từ số
# đo 119 chương đang có, KHÔNG tự đặt: 3 chương ở 6,9–11,3% mất 4–9 khối lời mỗi
# chương; chương kế tiếp là 56% và không mất khối nào. Giữa 11% và 56% không có
# chương nào -> chặn ở 50% bắt đúng 3 ca thảm hoạ, không chặn oan ai. Đem 0.95 đi
# chặn thì chặn 44/119 chương (37%) mà phần lớn chỉ mất 0–1 khối.
KHOP_CHAN = 0.50
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


def la_phu_de(srt_path) -> bool:
    """File `.srt` này ĐỌC RA ĐƯỢC phụ đề không (có ít nhất một dòng thời gian)?

    Vì sao cần (haint báo 18/09): LI042_Hai có `C2.srt`…`E.srt` mà ruột là CHỮ
    KỊCH BẢN, không một dòng `00:00:01,000 --> 00:00:03,000` nào. `make` thấy
    đuôi .srt là tin ngay, align chết từng chương; chỉ H (không có .srt) sống
    nhờ whisper. Đây là hỏng CHẮC CHẮN, khác hẳn "đo không được" — nên cổng
    dùng nó để CHẶN, còn `do_khop_srt` vẫn fail-open như cũ.

    Đọc utf-8-sig y như `SrtAligner` để không chặn oan file lành có BOM.
    """
    from pathlib import Path as _P

    from autoedit.align.srt_file import parse_srt

    f = _P(srt_path)
    if not f.is_file():
        return False
    try:
        return bool(parse_srt(f.read_text(encoding="utf-8-sig", errors="replace")))
    except OSError:
        return False


def do_khop_srt(script_text: str, srt_path) -> float | None:
    """Tỉ lệ từ script khớp thẳng vào `.srt` — KIỂM TRƯỚC KHI CHẠY.

    Dùng đúng hai thứ đã có: `parse_srt` + `match_script_to_whisper`. Không gọi
    whisper, không gọi LLM -> đo được ngay lúc người dựng còn đứng đó, thay vì để
    worker chạy hết rồi mới lộ ra khối mất lời.

    Trả None khi KHÔNG đo được (thiếu file, srt hỏng, script rỗng) — cổng gọi nó
    phải MỞ, đúng khuôn các cổng khác: không đo được thì đừng chặn người ta.
    """
    from pathlib import Path as _P

    from autoedit.align.matcher import match_script_to_whisper
    from autoedit.align.srt_file import parse_srt, words_from_captions

    f = _P(srt_path)
    if not (script_text or "").strip() or not f.is_file():
        return None
    try:
        cap = parse_srt(f.read_text(encoding="utf-8", errors="replace"))
        words = words_from_captions(cap)
        if not words:
            return None
        return round(match_script_to_whisper(script_text, words).match_ratio, 4)
    except Exception:  # noqa: BLE001 — đo hỏng thì mở cửa, không chặn oan
        return None
