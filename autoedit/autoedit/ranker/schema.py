"""Schema Pydantic cho khung phễu c5 — output NÃO chấm + kết quả rank 1 beat.

Thiết kế đã duyệt: MO_TA_VAN_HANH_PHEU_C5.md (2026-07-03). NÃO gọi ĐÚNG 1 lần/beat,
trả verdict + điểm nghĩa/mood + lý do 1 câu cho MỖI ứng viên. Veto CHỈ 3 dạng c2;
mọi thứ khác là điểm, không phải cửa loại ([[filter-overload-guard]]).
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# 3 dạng veto nghĩa NGHIÊM TRỌNG (c2 — đóng băng, không thêm dạng thứ 4).
# Veto ngoài 3 dạng này = "tự hạ cấp": bị loại nhưng được trả lại pool khi thủng sàn 3.
SERIOUS_VETO_TYPES = ("chu_de_khac_han", "thuc_the_sai", "nguoc_tran_cu_the")


class CandidateVerdict(BaseModel):
    """Phán quyết của NÃO cho 1 ứng viên footage."""

    # TOC-1: id = MÃ NGẮN của ứng viên trong prompt (alias crc32 — prompts.alias_of);
    # funnel dịch về asset_key. Description đi vào --json-schema để NÃO chép đúng mã.
    id: str = Field(description="the candidate's id code exactly as given in the prompt")
    verdict: Literal["ok", "veto"]
    veto_type: Literal["", "chu_de_khac_han", "thuc_the_sai", "nguoc_tran_cu_the", "khac"] = ""
    diem_nghia: int = Field(ge=0, le=10)  # khớp nghĩa beat (đã xét mạch c3)
    diem_mood: int = Field(ge=0, le=10)
    ly_do: str                            # 1 câu tiếng Việt — editor đọc hiểu ngay


class BeatRankResponse(BaseModel):
    """Output NÃO cho cả beat — đúng 1 call, 1 danh sách phán quyết."""

    verdicts: list[CandidateVerdict]


class BeatVerdicts(BaseModel):
    """Phán quyết cho 1 beat trong batch (PA-1 2026-07-07)."""

    beat_id: int
    verdicts: list[CandidateVerdict]


class BatchRankResponse(BaseModel):
    """Output NÃO cho CẢ CHUỖI beat — 1 call/chunk (~10 beat) thay 1 call/beat.

    Máy vẫn gác toàn bộ luật cứng sau khi nhận (P7 chống lặp, sàn 3, veto hẹp) —
    batch chỉ gom bước CHẤM, không chuyển quyền quyết cho LLM."""

    beats: list[BeatVerdicts]


class RankedCandidate(BaseModel):
    """1 ứng viên sau khi chấm xong — ghi vào project.json/report được."""

    asset_key: str
    diem_nghia: int
    diem_mood: int
    diem_may: float
    diem_tong: float
    verdict: str          # ok | veto
    veto_type: str = ""
    ly_do: str = ""
    demoted: bool = False  # bị veto lý-do-thường nhưng được trả lại vì thủng sàn 3


class BeatRankResult(BaseModel):
    """Kết quả phễu cho 1 beat: chọn ai + kill-log + cả bảng điểm (report)."""

    beat_id: int
    chosen_key: Optional[str] = None   # asset_key thắng; None = needs_human
    chosen_ly_do: str = ""
    needs_human: bool = False
    ranked: list[RankedCandidate] = Field(default_factory=list)  # xếp theo điểm giảm dần
    kill_log: dict[str, int] = Field(default_factory=dict)
    # thu | hong_ky_thuat | veto_nghia | tra_lai_san | con_lai
    # C5 vision gate (đợt 5): mỗi lượt soi lead-pick ghi 1 dict
    # {asset_key, subject_match, mood_match, seen, action} — action:
    # pass | mood_warning | demote | giu_du_nghi_sai (user phán trúng/oan từ đây)
    vision_gate: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
