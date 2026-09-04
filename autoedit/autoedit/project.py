"""Khung project.json — nguồn sự thật duy nhất của mỗi video.

Nguyên tắc kiến trúc (CLAUDE.md):
1. Mọi stage đọc/ghi vào project.json. Resume được từ bất kỳ stage nào nhờ `stages`.
2. LLM không bao giờ sinh timestamp — timestamp luôn từ alignment (Word.start/end).

M0 chỉ điền `inputs` + `stages`. Các field output (transcript/beats/cost_log)
được định nghĩa sẵn nhưng để rỗng, milestone sau (M2/M3...) sẽ điền.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import unicodedata
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator

SCHEMA_VERSION = 1
PROJECT_FILENAME = "project.json"


# --------------------------------------------------------------------------- #
# Pipeline 7 stage (PRD mục 4)
# --------------------------------------------------------------------------- #
class Stage(str, Enum):
    ALIGN = "align"        # M2 — WhisperX/faster-whisper -> timestamp từng từ
    DIRECT = "direct"      # M3 — LLM đạo diễn chia beat
    ENRICH = "enrich"      # P2B — LLM sinh dữ kiện BỔ SUNG (chart web-grounded + info-card)
    CUT = "cut"            # M4 — cắt voice theo beat + hình thở
    MUSIC = "music"        # MUSIC SYNC M1 — chọn nhạc per-chapter TRƯỚC source/assemble (optional)
    SOURCE = "source"      # M5 — search & tải footage
    RANK = "rank"          # M5 — chấm điểm & chọn shot
    ASSEMBLE = "assemble"  # M1/M6 — ráp timeline -> CapCut draft
    REPORT = "report"      # M7 — report.html cho editor duyệt


# Thứ tự chạy chuẩn của pipeline (dùng cho resume sau này).
# ENRICH sau DIRECT (cần beats), trước CUT (chỉ annotate, không đổi word range).
# MUSIC sau CUT (cần timeline chương), trước SOURCE — OPTIONAL: bỏ qua thì assemble
# tự chọn nhạc như cũ (đường cũ nguyên vẹn). Chạy lại CUT -> music_plan bị xóa (stale).
PIPELINE_ORDER: list[Stage] = [
    Stage.ALIGN,
    Stage.DIRECT,
    Stage.ENRICH,
    Stage.CUT,
    Stage.MUSIC,
    Stage.SOURCE,
    Stage.RANK,
    Stage.ASSEMBLE,
    Stage.REPORT,
]


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class StageRecord(BaseModel):
    """Trạng thái 1 stage — cơ chế resume."""

    status: StageStatus = StageStatus.PENDING
    started_at: Optional[str] = None    # TOC-4: đo tốc độ tự động (NHAT_KY_TOC_DO)
    completed_at: Optional[str] = None
    error: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    # TOC-4: số đo chi tiết trong stage (source: rank_calls/rank_call_s/download_s...).
    # Project cũ không có key -> {} (fail-open).
    perf: dict = Field(default_factory=dict)

    @classmethod
    def running(cls) -> "StageRecord":
        """Record RUNNING đóng dấu giờ bắt đầu — mọi stage runner dùng chung (TOC-4)."""
        return cls(status=StageStatus.RUNNING,
                   started_at=datetime.now(timezone.utc).isoformat())


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
class Inputs(BaseModel):
    """Đầu vào của video, đã copy vào trong folder project (self-contained)."""

    # Đường dẫn tương đối tới bản copy trong project (vd "inputs/script.txt")
    script_path: str
    voice_path: str
    # Đường dẫn file gốc trước khi copy (để truy vết)
    original_script_path: str
    original_voice_path: str
    # Nội dung script đọc sẵn (script là ground truth cho align)
    script_text: str
    voice_duration_sec: Optional[float] = None
    # Creative brief + kênh (PRD 3.1) — optional ở M0
    brief: Optional[str] = None
    channel: Optional[str] = None
    # REF (user 2026-07-11): prefix folder/file NGUỒN MẪU CỦA BÀI — người dựng khai qua
    # `source --ref` (máy không suy từ tên file), dính theo project cho các lần chạy sau
    ref_sources: list[str] = []
    # BOOST (user 2026-07-17): cảnh dạng X khán giả thích, khai "X@scope" (scope:
    # all|hook|ch<N>, mặc định all) — per-video, cộng với audience_bias của niche
    # (niche_profile.yaml). Dính theo project như ref_sources. MO_TA_VAN_HANH_BOOST.md
    boosts: list[str] = []
    # AIGEN (user 2026-09-04): editor CHỌN khi nộp job — bật mới gom motif/gen ảnh
    # (mặc định TẮT: dựng thuần V1, beat thiếu hình để needs_human như cũ).
    aigen: bool = False


# --------------------------------------------------------------------------- #
# Output các stage sau (định nghĩa sẵn, M0 để rỗng)
# --------------------------------------------------------------------------- #
class Word(BaseModel):
    """1 từ CỦA SCRIPT GỐC với timestamp từ alignment — Stage 1 (M2).

    interpolated=True: Whisper không khớp được từ này, timestamp nội suy
    giữa 2 từ neo lân cận (tin cậy thấp hơn — stage cắt voice nên tránh
    đặt ranh giới beat ngay tại từ nội suy).
    """

    text: str
    start: float
    end: float
    interpolated: bool = False


class SearchQueries(BaseModel):
    """Query stock 3 tier (P5) — mỗi query ≤4 từ, tier sau chỉ chạy khi tier trước nghèo.

    C4: thêm tier `local` viết RIÊNG cho kho local theo từ vựng tag GLM (2 kho 2 ngôn
    ngữ — MO_TA_VAN_HANH_C4_TU_VUNG.md). Optional: rỗng = hành vi cũ (local ké specific).
    """

    specific: list[str] = Field(default_factory=list)  # 3-4 từ, kèm shot modifier
    broad: list[str] = Field(default_factory=list)     # 2 từ
    thematic: list[str] = Field(default_factory=list)  # chủ đề niche (safe_pool sau M3.5)
    local: list[str] = Field(default_factory=list)     # 2-4 danh từ TRÚNG vocab tag kho (C4)


class Overlay(BaseModel):
    """1 motion-graphic overlay (chữ/số) trên 1 beat — Phase 1 Nhóm A.

    LLM chỉ quyết phần NGHĨA (text, kind, anchor_word); code map kind -> phần
    HÌNH (position/anim/sfx/size) trong overlay/style.py. Timeline tính ở assemble.
    """

    text: str                 # chữ ngắn hiện lên: "$2", "FREE", "Bước 1"
    kind: str                 # price | keyword | list_item | stat
    anchor_word: int          # word index trong beat — canh thời điểm hiện
    duration_sec: float = 2.0
    position: str = "lower_third"   # center | lower_third | upper (code điền)
    anim: str = "pop"               # pop | slide_up | none (code điền)
    sfx_kind: str = "none"          # cash | impact | pop | riser | none (code điền)
    size: float = 16.0


class TextPhrase(BaseModel):
    """1 cụm chữ trong chuỗi kinetic (Req 3) — chữ verbatim + từ mở đầu để canh giờ."""

    text: str                 # cụm verbatim từ script: "Việt Nam"
    anchor_word: int          # word index nơi cụm BẮT ĐẦU được nói


class TextSequence(BaseModel):
    """Chuỗi chữ chạy theo voice từng cụm (Phase 2A Req 3) — kinetic typography.

    LLM chẻ chữ đang nói thành 2-4 cụm + anchor từng cụm; code lo HÌNH (xếp chồng,
    nền plate, slide-in). Các cụm xuất hiện lần lượt khớp voice, giữ tới hết beat.
    """

    phrases: list[TextPhrase] = Field(default_factory=list)
    background: str = "footage"     # footage (footage beat) | plate (nền mờ cho nổi chữ)
    position: str = "center"
    size: float = 10.0              # nhỏ hơn overlay thường để 3-4 dòng xếp chồng không đè
    hold: bool = True               # cụm giữ tới hết beat (xếp chồng) thay vì tắt


class ChartDatum(BaseModel):
    label: str
    value: float


class GraphicSpec(BaseModel):
    """Đặc tả biểu đồ động cho 1 beat — Phase 1 Nhóm B (P1.5).

    LLM trích SỐ THẬT từ script vào data; code render video chart. layout=full
    (chart cả khung, route=graphic) | half (chart PiP nửa khung, footage chạy dưới).
    """

    chart_type: str               # bar | line | pie
    title: str
    unit: str = ""                # vd "$", "%", "$/tháng"
    layout: str = "full"          # full | half
    data: list[ChartDatum] = Field(default_factory=list)
    source_note: str = ""
    x_label: str = ""             # tiêu đề trục X (line/bar có trục mang nghĩa)
    y_label: str = ""             # tiêu đề trục Y
    theme: str = "dark"           # dark | light (giữ dark mặc định)
    # P2B: phân biệt số TỪ SCRIPT vs số BỔ SUNG (LLM web-grounded). supplementary
    # mặc định CHƯA duyệt -> không render tới khi người duyệt (chống số sai lọt).
    data_origin: str = "script"   # script | supplementary
    approved: bool = True         # script: True; supplementary: False tới khi duyệt


class InfoCard(BaseModel):
    """Thẻ chữ nửa màn bổ sung nghĩa cho đoạn (P2B Req 6) — LLM sinh, luôn cần duyệt.

    Bullet định tính/định lượng bổ nghĩa voice (vd 'Không máy nén, không hoá chất').
    Footage chạy nửa trái, thẻ phủ nửa phải. source_note = nhãn 'Minh hoạ' bắt buộc.
    """

    title: str                              # tiêu đề ngắn: "Earth's Cool Secret"
    bullets: list[str] = Field(default_factory=list)   # 3-5 bullet ngắn
    data_origin: str = "supplementary"      # luôn supplementary (LLM sinh)
    source_note: str = "Minh hoạ"           # nhãn disclaimer bắt buộc hiện trên thẻ
    approved: bool = False                   # cổng người duyệt — chưa duyệt thì không render
    accent: str = ""                         # màu tone gradient nền (hex); rỗng = tự chọn theo title


class Beat(BaseModel):
    """1 beat dựng — Stage 2 (M3), schema Footage Sourcing v2 (PRD P1-P8).

    start/end (giây) LUÔN tính từ transcript theo word index — LLM không sinh timestamp.
    Phase 0 vẫn chưa có layer2/sfx/ambience (Phase 1).
    """

    beat_id: int
    chapter: int
    text: str                 # nguyên văn các từ script thuộc beat
    start_word: int           # index trên transcript (inclusive)
    end_word: int             # index trên transcript (inclusive)
    # HỆ TỌA ĐỘ KÉP (RA_SOAT 3.3): start/end là SOURCE time (trên voice gốc/master).
    # timeline_* là vị trí trên draft SAU khi cộng dồn hình thở — stage cut (M4) điền.
    start: float              # SOURCE: giây, tính từ transcript[start_word].start
    end: float                # SOURCE: giây, tính từ transcript[end_word].end
    timeline_start: Optional[float] = None  # TIMELINE: M4 điền, M6 đặt footage theo đây
    timeline_end: Optional[float] = None
    energy: str               # low | medium | high
    mood: str
    sourcing_route: str = "stock"   # entity | stock | local_library | graphic (P1)
    visual_anchor: bool = True      # False = slot tự do cho footage thư viện niche (P4)
    visual_level: str         # literal | associative | metaphorical
    visual_concept: str
    shot_size: str            # wide | medium | close_up | extreme_close_up | aerial
    search_queries: SearchQueries = Field(default_factory=SearchQueries)
    entity_queries: list[str] = Field(default_factory=list)  # chỉ khi route=entity
    breathing_after: float = 0.0  # GIÂY hình thở sau beat (0 = không); số CUỐI — SHOT THỞ 2.0: máy kéo sâu ở cut
    breathing_base: float = 0.0   # số NÃO GỐC — cut reset về đây rồi mới plan (chạy lại không cộng dồn/co micro oan)
    micro_pause_after: float = 0.0  # GIÂY giãn nghỉ MÁY sau beat (hình thở 2.0) — stage cut điền, KHÔNG phải LLM
    rhetorical_pause: bool = False  # câu đinh (hình thở 3.0): LLM đánh dấu beat KHÔNG dấu đáng ngắt ~1s; máy vẫn gác khóa nghỉ thật
    shot_count: int = 1
    overlays: list[Overlay] = Field(default_factory=list)  # Phase 1 Nhóm A
    graphic_spec: Optional[GraphicSpec] = None             # Phase 1 Nhóm B (P1.5)
    graphic_asset: Optional[str] = None  # P1.5b: chart half render sẵn (đặt PiP layer2)
    text_sequence: Optional[TextSequence] = None  # Phase 2A Req 3: chữ chạy theo voice
    info_card: Optional[InfoCard] = None     # P2B Req 6: thẻ chữ nửa màn (LLM sinh)
    info_card_asset: Optional[str] = None    # P2B: mp4 thẻ render sẵn (đặt nửa phải)

    @field_validator("search_queries", mode="before")
    @classmethod
    def _coerce_legacy_queries(cls, v):
        """project.json trước v2 lưu search_queries dạng list phẳng -> dồn vào specific."""
        if isinstance(v, list):
            return {"specific": v}
        return v

    @field_validator("breathing_after", mode="before")
    @classmethod
    def _coerce_legacy_breathing(cls, v):
        """Schema cũ lưu bool -> đổi sang giây (True = 3.0s mặc định cũ)."""
        if isinstance(v, bool):
            return 3.0 if v else 0.0
        return v


class InsertClip(BaseModel):
    """M4c: 1 file footage editor đưa cho Δ (`insert --footage <folder>`). Copy vào
    media/insert/ lúc khai (path TƯƠNG ĐỐI project_dir, prefix crc8 chống đè trùng tên
    — họ bug F6); cỡ cảnh GLM tag lúc khai, "" = tag lỗi (trung tính, vẫn dùng được)."""

    path: str
    shot_size: str = ""        # wide | medium | close_up | extreme_close_up | aerial | ""
    duration: float = 0.0      # giây (ảnh = 0)


class InsertPick(BaseModel):
    """M4c: footage chọn cho Ô THỨ i của lưới Δ — index list = index ô, KHÔNG lưu mốc
    tuyệt đối (cut chạy lại là timeline dịch; lưới chỉ phụ thuộc dur+nhịp+seed nên
    index ổn định). path rỗng = ô giữ slug (fail-open y M4b)."""

    path: str = ""             # editor: tương đối project_dir; kho/HINH THO: tuyệt đối
    source: str = ""           # editor | hinh_tho (M4d) | library | "" (slug)
    asset_key: str = ""        # kho: key sổ (P7 chống lặp); editor: rỗng
    shot_size: str = ""
    hold: bool = False         # ô HOLD (cảnh rộng) — report/INDEX hiện lại
    note: str = ""


class InsertSpec(BaseModel):
    """NHIP-M2 đoạn chèn: Δ giây editor KHAI chèn vào timeline SAU beat `after_beat`
    (sau cả hình thở/giãn nghỉ của beat đó). Độ dài editor quyết (user chốt 2026-07-19).
    Cut tiêu thụ ở cutter/timeline.py — MỘT chỗ sinh timeline duy nhất (BAN_GIAO §7b).
    Cấm sau beat cuối (không có voice sau — mọi total_end dựa segment cuối)."""

    after_beat: int
    dur: float
    note: str = ""             # editor ghi chú nội dung đoạn (report/INDEX hiện lại)
    music: str = ""            # NHIP-M3: đường dẫn TUYỆT ĐỐI bài editor đưa cho Δ (phương
                               # án B: thay nhạc chương từ mép vào Δ tới hết chương).
                               # Rỗng = Δ dùng nhạc chương như cũ (M2 nguyên vẹn).
    # NHIP-M4: nhịp bài editor ĐO LÚC KHAI (librosa) — bài nằm NGOÀI kho nên không có
    # record music_index để tra (tồn đọng M3 #2). Hệ tọa độ = giây tính từ ĐẦU FILE
    # nhạc; assemble đặt bài editor từ đầu bài tại mép Δ nên cộng mép Δ là ra timeline.
    # Rỗng (bài lỗi/không đo được) -> Δ giữ 1 clip như M3, fail-open không chặn dựng.
    music_beats: list[float] = Field(default_factory=list)
    music_beat_strength: list[float] = Field(default_factory=list)
    music_bpm: float = 0.0
    music_tier: str = ""       # A/B = cắt theo nhịp được; C (ambient) = không có lưới
    # NHIP-M4b (foundation e2, user chốt 2026-07-21): downbeat madmom (giây phách "1"
    # từ ĐẦU FILE nhạc) + số phách/ô nhịp (3|4). Có đủ 2 field -> lưới Δ dựng bằng
    # CÔNG THỨC đều từ downbeat (không cộng dồn beat librosa — GT1 lưới trôi 46ms).
    # Rỗng/0 (madmom lỗi, project cũ) -> rơi về lưới beat librosa như trước, fail-open.
    music_downbeats: list[float] = Field(default_factory=list)
    music_meter: int = 0
    # A′ shuffle RUN+HOLD (e2 §5): pace chỉnh mật độ hold (fast/medium/slow, rỗng =
    # medium); shuffle_seed 0 = tự crc32 từ (after_beat, tên bài) — dựng lại Y HỆT,
    # editor muốn xáo bài khác thì khai seed mới.
    music_pace: str = ""
    shuffle_seed: int = 0
    # M4c footage THẬT trong Δ (user chốt 2026-07-21: lai — folder editor trước, kho
    # đắp bù theo PROMPT editor khai; GLM tag cỡ cảnh). Mọi field rỗng = Δ giữ slug (M4b).
    footage_dir: str = ""      # folder gốc editor đưa (chỉ để truy vết — file đã copy)
    footage_prompt: str = ""   # prompt tiếng Việt cho kho đắp bù ("thiên nhiên hùng vĩ...")
    footage_queries: list[str] = Field(default_factory=list)  # NÃO dịch prompt lúc khai
    footage_clips: list[InsertClip] = Field(default_factory=list)
    footage_picks: list[InsertPick] = Field(default_factory=list)  # source ghi, assemble đọc


class VoiceSegment(BaseModel):
    """1 file voice đã cắt — Stage 3 (M4). Mang CẢ HAI hệ tọa độ (RA_SOAT 3.3).

    source_* : giây trên voice_master.wav (bất biến sau align)
    timeline_*: giây trên draft CapCut (= source + tổng hình thở phía trước)
    """

    segment_id: int
    path: str                  # tương đối với project_dir, vd "segments/seg_001.wav"
    source_start: float
    source_end: float
    timeline_start: float
    timeline_end: float
    beat_ids: list[int] = Field(default_factory=list)
    breathing_after: float = 0.0  # giây hình thở SAU segment này trên timeline
    micro_pause_after: float = 0.0  # giây giãn nghỉ MÁY sau segment (hình thở 2.0)
    insert_after: float = 0.0  # NHIP-M2: Δ đoạn chèn SAU thở+giãn của segment này


class ExtraShot(BaseModel):
    """1 clip PHỤ trong beat multi-shot (shot 2..N) — F5 shot_count. Clip chính vẫn ở
    ShotPick (shot 1) nên mọi chỗ đọc asset_path chạy y cũ (preserve-by-default)."""

    asset_path: str
    asset_key: str = ""
    source: str = ""
    source_channel: str = ""       # VD4 ghi công: kênh nguồn (copy từ ứng viên lúc pick)
    boost_hit: bool = False        # BOOST: shot match sở thích khán giả (tầng ĐO đếm)
    note: str = ""


class BreathShot(BaseModel):
    """Footage riêng phủ ô thở hết ý/cuối chương (MO_TA_VAN_HANH_SHOT_THO.md §2, §7).

    beat_id = beat MANG ô thở (breathing_after của nó). Máy chọn thuần từ kho local:
    3.0 — TIẾP TỤC CHỦ THỂ clip liền trước (token subject/tags), đổi cỡ cảnh cho đỡ
    nhàm; mood chỉ phụ trợ. Không pick được -> không có record -> assemble tự về hành
    vi cũ (giữ hình + J-cut)."""

    beat_id: int
    asset_path: str                # tương đối project_dir (assets/bXXX_breath_*.mp4)
    asset_key: str = ""
    source: str = "local"
    source_channel: str = ""       # VD4 ghi công: kênh nguồn (copy từ pool lúc pick)
    dur: float = 0.0               # GIÂY miếng này (2.0: 1 ô 1-3 miếng, thứ tự đặt = thứ tự list); 0 = phủ trọn ô (record v1)
    note: str = ""                 # lý do chọn (mood khớp/cỡ cảnh) — report + editor kiểm
    beat_cut: bool = False         # NHIP-M1: durs từ LƯỚI BEAT nhạc (assemble retime mép về beat thật)


class ShotPick(BaseModel):
    """Kết quả source cho 1 beat — Stage 4 (M5, chọn heuristic Phase 0).

    status: ok (có asset) | needs_human (P8 — hết thang fallback/thiếu API key)
            | graphic (placeholder cho editor, asset = nền generic nếu có)
    """

    beat_id: int
    status: str = "ok"             # ok | needs_human | graphic
    source: str = ""               # local | pexels | entity | none
    asset_path: Optional[str] = None   # tương đối project_dir (assets/...) — đã verify
    asset_key: str = ""            # khóa chống trùng: provider:id hoặc path local
    source_channel: str = ""       # VD4 ghi công: kênh nguồn footage (assemble --credit đọc)
    boost_hit: bool = False        # BOOST: pick match sở thích khán giả (tầng ĐO + report)
    licensing_flag: bool = False   # ⚠ route entity / nguồn cần người duyệt
    peak: bool = False             # ytref §3h: pick là cảnh điểm nhô Most Replayed (report ⭐)
    note: str = ""
    alternates: list[str] = Field(default_factory=list)  # URL/path phương án thay (report)
    extra_shots: list[ExtraShot] = Field(default_factory=list)  # shot 2..N (multi-shot); rỗng = 1 shot


class MusicPlanEntry(BaseModel):
    """MUSIC SYNC M1 (M-STAGE): 1 chương — bài chọn TRƯỚC assemble, offset đã neo accent.

    start_offset: điểm bắt đầu TRONG bài (giây) tại đầu segment nhạc — đã lượng tử về
    accent/downbeat gần section offset cũ để điểm nhấn rơi đúng cắt đầu chương (NT4:
    số từ tín hiệu librosa trong music_index, LLM không sinh). Assemble đọc nguyên,
    không chọn lại; không có plan -> assemble tự chọn như cũ."""

    chapter_id: int
    file: str
    start_offset: float = 0.0
    beat_tier: str = "C"           # tier bài lúc plan (M3 đọc để bật/tắt snap)
    score: float = 0.0
    anchor_note: str = ""          # neo vào đâu — report/debug cho editor kiểm


class CostEntry(BaseModel):
    """Log chi phí 1 lần gọi LLM (rủi ro #4 KE_HOACH_TRIEN_KHAI)."""

    stage: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    usd: float = 0.0
    at: str


# --------------------------------------------------------------------------- #
# Project — model gốc
# --------------------------------------------------------------------------- #
def _default_stages() -> dict[Stage, StageRecord]:
    return {stage: StageRecord() for stage in PIPELINE_ORDER}


class Project(BaseModel):
    schema_version: int = SCHEMA_VERSION
    project_id: str
    title: str
    created_at: str
    project_dir: str  # đường dẫn tuyệt đối của folder project

    inputs: Inputs
    stages: dict[Stage, StageRecord] = Field(default_factory=_default_stages)

    # Output điền dần qua các milestone:
    transcript: list[Word] = Field(default_factory=list)      # M2
    beats: list[Beat] = Field(default_factory=list)            # M3
    outline: Optional[dict] = None                             # M3 pass 1 (chương/mood/motif)
    voice_master_path: Optional[str] = None                    # M4: WAV 48kHz master
    segments: list[VoiceSegment] = Field(default_factory=list)  # M4
    inserts: list[InsertSpec] = Field(default_factory=list)     # NHIP-M2: đoạn chèn editor khai (lệnh `insert`)
    shots: list[ShotPick] = Field(default_factory=list)         # M5
    breath_shots: list[BreathShot] = Field(default_factory=list)  # M5: shot thở (MO_TA_SHOT_THO)
    niche: Optional[str] = None                                  # M5: kho local đã dùng (DNA d1 đọc)
    rank_log: list[dict] = Field(default_factory=list)          # F5: BeatRankResult dump/beat (kill-log + lý do)
    ambient_log: list[dict] = Field(default_factory=list)       # C1: mỗi ô thở — start/end/scene/file/note (report kiểm tai)
    drone_log: dict = Field(default_factory=dict)                # S1: drone nền — file/volume/loops/total_s
    subject_sfx_log: list[dict] = Field(default_factory=list)   # S2: tiếng chủ thể trong voice — start/beat/kind/file/source/note
    whoosh_log: list[dict] = Field(default_factory=list)        # S3 auto ĐÃ BỎ (PB12) — field giữ để project.json cũ load được; chapter-card backlog sẽ dùng lại
    hook_sfx_log: list[dict] = Field(default_factory=list)      # S3-HOOK: hit/whoosh/click tại cut trong hook — t/kind/file/note (MO_TA_HOOK_SFX)
    draft_path: Optional[str] = None                             # M6: folder draft CapCut
    report_path: Optional[str] = None                            # M7: report.html bàn giao editor
    music_selections: dict[str, str] = Field(default_factory=dict)  # chapter_id -> file nhạc đã chọn
    music_plan: list[MusicPlanEntry] = Field(default_factory=list)   # MUSIC SYNC M1 — stage music điền; rỗng = assemble tự chọn như cũ
    music_sync_targets: str = "accent"  # M4 M-GRID thử nghiệm: "grid" = hook snap theo DOWNBEAT (tier A) thay accent — mặc định accent
    use_epidemic_sfx: bool = False  # MẶC ĐỊNH TẮT (user chốt 2026-07-18): SFX Epidemic chỉ dùng khi editor gõ `assemble --epidemic`. Kho vẫn giữ file, bật là có ngay
    sfx_llm: bool = False           # `assemble --sfx-llm`: NÃO chấm kind tiếng cho beat bảng luật MÙ CHỮ (tầng 3, ambient/subject_llm.py)
    cost_log: list[CostEntry] = Field(default_factory=list)
    cost_total_usd: float = 0.0

    # ---- persistence -------------------------------------------------------
    def save(self, project_dir: Optional[Path] = None) -> Path:
        """Ghi project.json (indent 2, giữ Unicode). Trả về path file."""
        target_dir = Path(project_dir) if project_dir else Path(self.project_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / PROJECT_FILENAME
        path.write_text(
            json.dumps(self.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(cls, project_dir: Path | str) -> "Project":
        path = Path(project_dir) / PROJECT_FILENAME
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.model_validate(data)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def slugify(text: str) -> str:
    """Chuyển text -> ASCII slug an toàn cho path (bài học CapCut: path ASCII).

    Vd: "Việt Nam giá rẻ!" -> "viet-nam-gia-re".
    """
    # Bỏ dấu: NFKD rồi loại ký tự non-ASCII
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return ascii_text or "project"


def ffprobe_duration(path: Path) -> Optional[float]:
    """Lấy duration (giây) của file media qua ffprobe. Trả None nếu lỗi/thiếu ffprobe."""
    try:
        out = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if out.returncode != 0:
            return None
        return float(out.stdout.strip())
    except (FileNotFoundError, ValueError, subprocess.SubprocessError):
        return None


def _read_script_text(script_path: Path) -> str:
    """Đọc nội dung script. M0 chỉ hỗ trợ .txt; .docx để milestone sau."""
    suffix = script_path.suffix.lower()
    if suffix == ".docx":
        raise ValueError(
            "Script .docx chưa hỗ trợ ở M0 — chuyển sang .txt trước "
            "(đọc .docx sẽ làm ở milestone sau)."
        )
    return script_path.read_text(encoding="utf-8")


def create_project(
    script: Path | str,
    voice: Path | str,
    out_dir: Path | str = "projects",
    title: Optional[str] = None,
    brief: Optional[str] = None,
    channel: Optional[str] = None,
    now: Optional[datetime] = None,
    srt: Optional[Path | str] = None,
) -> Project:
    """Tạo folder project mới, copy inputs vào, ghi project.json.

    Args:
        script: file script (.txt) tiếng Anh.
        voice: file voice (.mp3/.wav) ElevenLabs.
        out_dir: thư mục chứa các project (mặc định ./projects).
        title: tên hiển thị; mặc định suy từ tên file script.
        now: cho test bơm thời gian cố định; mặc định UTC hiện tại.
        srt: file .srt kèm voice (tuỳ chọn) — copy vào project để align đọc thẳng.
    """
    script_path = Path(script).expanduser().resolve()
    voice_path = Path(voice).expanduser().resolve()
    if not script_path.is_file():
        raise FileNotFoundError(f"Không thấy file script: {script_path}")
    if not voice_path.is_file():
        raise FileNotFoundError(f"Không thấy file voice: {voice_path}")
    srt_path = Path(srt).expanduser().resolve() if srt else None
    if srt_path is not None and not srt_path.is_file():
        raise FileNotFoundError(f"Không thấy file .srt: {srt_path}")

    script_text = _read_script_text(script_path)

    now = now or datetime.now(timezone.utc)
    base_title = title or script_path.stem
    project_id = f"{slugify(base_title)}-{now.strftime('%Y%m%d-%H%M%S')}"

    project_dir = (Path(out_dir).expanduser().resolve() / project_id)
    inputs_dir = project_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)

    # Copy inputs vào project (self-contained, resume độc lập file gốc)
    dst_script = inputs_dir / f"script{script_path.suffix.lower()}"
    dst_voice = inputs_dir / f"voice{voice_path.suffix.lower()}"
    shutil.copy2(script_path, dst_script)
    shutil.copy2(voice_path, dst_voice)
    # .srt đặt CÙNG TÊN voice -> SrtAligner tự tìm thấy, project vẫn self-contained
    # (resume được sau khi folder gốc bị xoá/di chuyển).
    if srt_path is not None:
        shutil.copy2(srt_path, dst_voice.with_suffix(".srt"))

    inputs = Inputs(
        script_path=str(dst_script.relative_to(project_dir)),
        voice_path=str(dst_voice.relative_to(project_dir)),
        original_script_path=str(script_path),
        original_voice_path=str(voice_path),
        script_text=script_text,
        voice_duration_sec=ffprobe_duration(dst_voice),
        brief=brief,
        channel=channel,
    )

    project = Project(
        project_id=project_id,
        title=base_title,
        created_at=now.isoformat(),
        project_dir=str(project_dir),
        inputs=inputs,
    )
    project.save(project_dir)
    return project
