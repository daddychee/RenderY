"""Khung phễu chọn footage c5 (F5) — chấm + chọn + kill-log. Thiết kế: MO_TA_VAN_HANH_PHEU_C5.md."""

from autoedit.ranker.funnel import rank_beat
from autoedit.ranker.schema import BeatRankResponse, BeatRankResult, CandidateVerdict

__all__ = ["rank_beat", "BeatRankResponse", "BeatRankResult", "CandidateVerdict"]
