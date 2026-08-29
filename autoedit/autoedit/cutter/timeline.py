"""Hệ tọa độ kép source_time / timeline_time — TRÁI TIM của M4 (RA_SOAT 3.3).

Ổ bug kinh điển: chèn hình thở làm trượt toàn bộ timestamp phía sau. Cách phòng:
- SOURCE time (trên voice master): bất biến, đến từ align. KHÔNG hàm nào ở đây sửa nó.
- TIMELINE time (trên draft): suy ra = source + tổng hình thở phía trước.
- Đơn vị cắt là "run": chuỗi beat liên tục giữa 2 điểm breathing — beat trong cùng
  run liền mạch cả 2 hệ, giữa 2 run có gap đúng bằng breathing trên timeline.

Mọi hàm pure — không ffmpeg, không I/O — để unit test bất biến.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from autoedit.project import Beat


@dataclass
class SegmentPlan:
    """Kế hoạch 1 segment (1 run beat). source_* set lúc plan; timeline_* set ở apply_timeline."""

    beat_ids: list[int]
    source_start: float
    source_end: float
    breathing_after: float = 0.0
    micro_pause_after: float = 0.0  # giãn nghỉ MÁY (hình thở 2.0) — gap nhỏ, cùng cơ chế
    insert_after: float = 0.0       # NHIP-M2: Δ đoạn chèn editor khai, SAU thở+giãn
    timeline_start: float = field(default=-1.0)
    timeline_end: float = field(default=-1.0)

    @property
    def duration(self) -> float:
        return self.source_end - self.source_start


def plan_segments(
    beats: list[Beat], inserts: dict[int, float] | None = None
) -> list[SegmentPlan]:
    """Gom beats thành runs theo breathing_after (GIÂY, LLM đạo diễn quyết theo vai
    chương — hook nghỉ ngắn dày hơn, thân bài thưa). Beat cuối video không thêm gap.

    inserts (NHIP-M2): {beat_id: Δ giây đoạn chèn} — beat có Δ kết thúc run của nó
    (kể cả không có thở/giãn), Δ nằm SAU thở+giãn. Beat cuối luôn 0 (như breathing)."""
    if not beats:
        return []
    inserts = inserts or {}
    plans: list[SegmentPlan] = []
    current: list[Beat] = []
    for i, beat in enumerate(beats):
        current.append(beat)
        is_last = i == len(beats) - 1
        if (beat.breathing_after > 0 or beat.micro_pause_after > 0 or is_last
                or inserts.get(beat.beat_id, 0.0) > 0):
            plans.append(
                SegmentPlan(
                    beat_ids=[b.beat_id for b in current],
                    source_start=current[0].start,
                    source_end=current[-1].end,
                    # segment cuối luôn 0 cả ba — total_end downstream dựa vào luật này
                    breathing_after=0.0 if is_last else beat.breathing_after,
                    micro_pause_after=0.0 if is_last else beat.micro_pause_after,
                    insert_after=0.0 if is_last else inserts.get(beat.beat_id, 0.0),
                )
            )
            current = []
    return plans


def apply_timeline(plans: list[SegmentPlan]) -> list[SegmentPlan]:
    """Điền timeline_* cho từng plan (mutate in place, trả lại chính list).

    Cursor timeline bắt đầu 0; mỗi segment chiếm đúng duration source của nó
    (cắt PCM giữ nguyên tốc độ), sau đó cursor cộng thêm breathing.
    LƯU Ý: hàm này KHÔNG sửa source_* — bất biến của hệ.
    """
    cursor = 0.0
    for plan in plans:
        plan.timeline_start = cursor
        plan.timeline_end = cursor + plan.duration
        # NHIP-M2: Δ đoạn chèn cộng vào cursor Ở ĐÂY (một chỗ duy nhất) — mọi tầng
        # đọc timeline_* phía sau (beat/segment/chart/card) tự dịch đúng, không dịch tay
        cursor = (plan.timeline_end + plan.breathing_after + plan.micro_pause_after
                  + plan.insert_after)
    return plans


def map_beats_to_timeline(
    beats: list[Beat], plans: list[SegmentPlan]
) -> dict[int, tuple[float, float]]:
    """Vị trí timeline của TỪNG beat — M6 đặt footage theo đây."""
    by_id = {b.beat_id: b for b in beats}
    result: dict[int, tuple[float, float]] = {}
    for plan in plans:
        if plan.timeline_start < 0:
            raise ValueError("plans chưa qua apply_timeline")
        offset = plan.timeline_start - plan.source_start
        for bid in plan.beat_ids:
            b = by_id[bid]
            result[bid] = (b.start + offset, b.end + offset)
    return result
