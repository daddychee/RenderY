"""Schema output LLM đạo diễn — validate bằng Pydantic qua messages.parse().

LLM CHỈ trả word index (inclusive, trên transcript M2). Timestamp do
validator.compute_beat_times() tính — nguyên tắc bất di bất dịch #2.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Energy = Literal["low", "medium", "high"]
# TEMPO MAP (2026-07-14, feedback đạo diễn hình ảnh): đường nhịp TRONG chương.
# "" = draft cũ/đường cũ chưa khai — mọi tầng sau fail-open.
TempoCurve = Literal["", "slow_build_slow", "build", "dense", "fast_settle", "calm"]
VisualLevel = Literal["literal", "associative", "metaphorical"]
ShotSize = Literal["wide", "medium", "close_up", "extreme_close_up", "aerial"]
SourcingRoute = Literal["entity", "stock", "local_library", "graphic"]


# --------------------------- Pass 1: Outline ---------------------------------
class ChapterPlan(BaseModel):
    """1 chương (ý lớn) — mini-arc setup -> phát triển -> payoff."""

    chapter_id: int
    title: str = Field(description="Tên ngắn gọn của chương")
    start_word: int = Field(description="Word index đầu chương (inclusive)")
    end_word: int = Field(description="Word index cuối chương (inclusive)")
    mood: str = Field(description="Mood chủ đạo, vd warm_inviting, urgent_dark")
    energy: Energy
    music_hint: str = Field(description="Gợi ý nhạc nền cho chương (mood/BPM/tông)")
    tempo_curve: TempoCurve = Field(
        default="",
        description="Đường NHỊP trong chương (tempo map): slow_build_slow (mở chậm→giữa "
        "dồn→kết thả, chương thân) | build (dồn dần, dẫn vào cao trào) | dense (dày đặc, "
        "kết 1 hold — chương cao trào) | fast_settle (vào nhanh→lắng — chương HOOK) | "
        "calm (chậm đều — chương kết/lặng). Nhanh/chậm TƯƠNG ĐỐI quanh trung vị DNA niche. "
        "Không cho 3 chương liền kề cùng curve.",
    )
    summary: str = Field(description="1-2 câu tóm ý chương")
    central_subject: str = Field(
        description="CHỦ THỂ THẬT của chương, dạng QUAY ĐƯỢC cụ thể — cái chương này THỰC SỰ "
        "nói về, đằng sau mọi lớp tu từ bề mặt (vd chương mở bằng ẩn dụ 'bếp lửa' nhưng giải "
        "thích vành nhật hoa Mặt Trời → central_subject='Mặt Trời / bề mặt & khí quyển Mặt Trời'). "
        "Đây là MỎ NEO để chọn footage cho các câu ẩn dụ/dẫn dắt — keyword phải mạch lạc với nó, "
        "không bám chữ bề mặt."
    )


class Outline(BaseModel):
    """Output pass 1 — đọc toàn script, hiểu toàn cục trước khi chia beat."""

    tone: str = Field(description="Thái độ của video với chủ đề")
    motifs: list[str] = Field(description="1-3 hình ảnh motif lặp có chủ đích xuyên video")
    video_subject: str = Field(
        default="",
        description="V3: PHẠM VI chủ thể của CẢ video, 1 dòng, ĐƯỢC PHÉP nhiều chủ thể "
        "(vd 'the Moon and its far side' / 'all 8 planets — one per chapter'). Phễu dùng "
        "làm vòng ngoài bắt footage sai thực thể (ca b11: sao Hỏa lọt video Mặt Trăng); "
        "neo phán vẫn là central_subject từng chương. Optional — draft cũ thiếu vẫn chạy.",
    )
    chapters: list[ChapterPlan]


# --------------------------- Pass 2: Beats -----------------------------------
class SearchQueriesDraft(BaseModel):
    """Query stock 3 tier (P5). MỖI QUERY TỐI ĐA 4 TỪ — Pexels là keyword matching."""

    specific: list[str] = Field(
        description="2-3 query cụ thể, 3-4 words each: subject + action/context (+ shot modifier)"
    )
    broad: list[str] = Field(
        description="1-2 query rộng, 2 words each — fallback khi specific nghèo kết quả"
    )
    thematic: list[str] = Field(
        description="1-2 query chủ đề niche của video — lưới an toàn cuối"
    )
    local: list[str] = Field(
        default_factory=list,
        description="C4 — 0-2 query cho KHO LOCAL: 2-4 DANH TỪ CẢNH lấy ĐÚNG từ mục "
        "TỪ VỰNG KHO trong direct_context.md (kho AND-match từng từ, không hiểu đồng "
        "nghĩa). KHÔNG động từ chuyển động (rotating/timelapse/zoom — tag chấm từ frame "
        "tĩnh). Kho không phủ concept hoặc context không có mục từ vựng → để RỖNG.",
    )


OverlayKind = Literal["price", "keyword", "list_item", "stat", "name", "place", "quote"]


class OverlayDraft(BaseModel):
    """1 overlay chữ/số LLM đề xuất cho beat (Phase 1 Nhóm A). LLM chỉ quyết NGHĨA."""

    text: str = Field(
        description="Chữ NGẮN hiện lên (≤20 ký tự): chính con số/từ, KHÔNG phải cả câu. "
        "Vd '$2', 'FREE', '45 ngày', 'Bước 1'. Giữ NGÔN NGỮ của script."
    )
    kind: OverlayKind = Field(
        description="price (giá/số tiền) | keyword (từ khóa nhấn 1-2 từ) | "
        "stat (số liệu + đơn vị) | list_item (mục danh sách/bước) | "
        "name (tên người/tổ chức, hiệu ứng gõ máy) | place (tên địa danh, gõ máy) | "
        "quote (trích dẫn NGẮN ≤24 ký tự, gõ máy)"
    )
    anchor_word: int = Field(
        description="Word index TRONG beat — overlay hiện đúng lúc nói từ này"
    )
    duration_sec: float = Field(default=2.0, description="Giây hiển thị (1.5-3)")


class ChartDatumDraft(BaseModel):
    label: str = Field(description="Nhãn ngắn, ngôn ngữ của script (vd 'Việt Nam', '2024')")
    value: float = Field(description="Số THẬT lấy từ script")


class GraphicSpecDraft(BaseModel):
    """Biểu đồ động cho beat so sánh/xu hướng (Nhóm B). LLM trích số thật từ script."""

    chart_type: Literal["bar", "line", "pie"] = Field(
        description="bar = so sánh các hạng mục ($700 vs $3000); line = xu hướng theo thời gian "
        "(% qua các năm); pie = TỈ TRỌNG các phần trong MỘT tổng thể (vd thuê nhà chiếm 50% lương "
        "hưu, phần còn lại 50%) — chỉ dùng pie khi các phần CỘNG LẠI thành 1 tổng (100% hoặc 1 ngân sách)"
    )
    title: str = Field(description="Tiêu đề biểu đồ, ngắn, ngôn ngữ script")
    unit: str = Field(default="", description="Đơn vị: '$', '%', '$/tháng'... (rỗng nếu không)")
    layout: Literal["full", "half"] = Field(
        default="full",
        description="full = biểu đồ chiếm CẢ KHUNG (route=graphic, không footage) — khi con số "
        "LÀ khoảnh khắc. half = biểu đồ NỬA PHẢI khung, footage chạy nửa trái (route=stock/"
        "entity/local + visual_concept tả cảnh nền) — khi có cảnh đáng xem song song số liệu.",
    )
    data: list[ChartDatumDraft] = Field(description="≥2 điểm dữ liệu, số thật từ script")
    source_note: str = Field(default="", description="Ghi chú nguồn nhỏ (optional)")
    x_label: str = Field(
        default="",
        description="Tiêu đề trục X, ngôn ngữ script (CHỈ line/bar có trục mang nghĩa, "
        "vd 'Tuần', 'Năm', 'Độ sâu (ft)'). Rỗng nếu không cần.",
    )
    y_label: str = Field(
        default="", description="Tiêu đề trục Y, ngôn ngữ script (vd 'Chi phí ($)'). Rỗng nếu không cần."
    )


class TextPhraseDraft(BaseModel):
    text: str = Field(description="Cụm chữ VERBATIM từ script (vd 'Việt Nam')")
    anchor_word: int = Field(description="Word index nơi cụm BẮT ĐẦU được nói (trong beat)")


class TextSequenceDraft(BaseModel):
    """Chữ chạy theo voice từng cụm (Req 3). LLM chỉ chẻ cụm + anchor; code lo hình."""

    phrases: list[TextPhraseDraft] = Field(
        description="2-4 cụm verbatim liền mạch, theo THỨ TỰ nói; cụm đầu anchor = từ đầu beat"
    )


class DirectInfoCardDraft(BaseModel):
    """Thẻ bullet split-screen sinh ngay trong pass direct (không cần enrich/duyệt thêm)."""

    title: str = Field(description="Tiêu đề ngắn 2-4 từ, ngôn ngữ script")
    bullets: list[str] = Field(description="3-5 bullet ≤40 ký tự mỗi bullet, ngôn ngữ script")
    source_note: str = Field(default="Minh hoạ")


class BeatDraft(BaseModel):
    """1 beat do LLM đề xuất — chưa có timestamp, chỉ word index. Schema v2 (P1-P8)."""

    start_word: int = Field(description="Word index đầu beat (inclusive)")
    end_word: int = Field(description="Word index cuối beat (inclusive)")
    energy: Energy
    mood: str
    sourcing_route: SourcingRoute = Field(
        description="P1 — quyết định ĐẦU TIÊN: entity (thực thể thật, ảnh thật) | "
        "stock (cảnh generic) | local_library | graphic (số liệu, không search stock)"
    )
    visual_anchor: bool = Field(
        description="P4 — false nếu beat ý trừu tượng/chuyển tiếp: slot tự do cho "
        "footage thư viện niche, concept chỉ cần đúng chủ đề + mood"
    )
    visual_level: VisualLevel
    visual_concept: str = Field(
        description="Cảnh quay được bằng máy quay thật, danh từ cụ thể, tiếng Anh. "
        "Route graphic: mô tả placeholder graphic cho editor."
    )
    shot_size: ShotSize
    search_queries: SearchQueriesDraft = Field(
        description="Query stock 3 tier, mỗi query ≤4 từ. Route entity: để rỗng cả 3 tier. "
        "Route graphic: specific/broad rỗng, CHỈ điền thematic 1-2 query nền generic "
        "lót dưới graphic (vd 'dark texture background')."
    )
    entity_queries: list[str] = Field(
        default_factory=list,
        description="CHỈ khi sourcing_route=entity: 1-3 query Google Images tìm ảnh "
        "thật của đúng thực thể, vd 'trump gold card announcement'",
    )
    breathing_after_sec: float = Field(
        default=0.0,
        description="GIÂY hình thở (khoảng không thoại, footage đẹp) sau beat này. "
        "0 = không. DNA editor (3 video mẫu): ÍT nhưng SÂU — ~1 ô mỗi 45-90s; cuối "
        "MỖI chương 2-5s (12/14 chương mẫu có ô); hook 2-5s sau câu mở/punchline; "
        "1-2 lần/video được 3.5-6s tại mặc khải lớn nhất hoặc sau câu hỏi khán giả. "
        "Tối đa 6.",
    )
    rhetorical_pause: bool = Field(
        default=False,
        description="CÂU ĐINH (hiếm — tối đa 1/chương, chỉ hook/kết/trước twist): beat "
        "kết thúc GIỮA câu (không dấu .?!,;:) mà chỗ ngắt tạo sức nặng tu từ — vd "
        "'…every room in our cosmic house ‖ But one.' Máy sẽ ngắt ~1s TẠI RANH GIỚI "
        "BEAT nếu voice có nghỉ thật; sai chỗ máy tự bỏ. Beat kết dấu câu/phẩy KHÔNG "
        "cần cờ này (máy tự xử).",
    )
    shot_count: int = Field(
        default=1,
        description="Số shot trong beat — quyết theo năng lượng và sức nặng hình; "
        "một hình đắt giữ trọn beat dài là bình thường",
    )
    overlays: list[OverlayDraft] = Field(
        default_factory=list,
        description="0-1 overlay chữ/số cho beat (hiếm khi 2). TIẾT CHẾ: chỉ thêm khi "
        "beat có con số/giá đáng nhấn, từ khóa đắt, hoặc mục danh sách. Đa số beat = [].",
    )
    graphic_spec: Optional[GraphicSpecDraft] = Field(
        default=None,
        description="CHỈ khi beat SO SÁNH ≥2 số hoặc XU HƯỚNG theo thời gian (vd thuê nhà "
        "$400 VN vs $2500 Mỹ; chi phí tăng % qua các năm). Khi đó BẮT BUỘC "
        "sourcing_route=graphic. Một con số lẻ thì dùng overlay, KHÔNG graphic_spec.",
    )
    text_sequence: Optional[TextSequenceDraft] = Field(
        default=None,
        description="HIẾM — chỉ khi câu CHỐT mạnh đáng cho chữ chạy theo voice từng cụm "
        "(kinetic). Chẻ chữ ĐANG NÓI của beat thành 2-4 cụm verbatim liền mạch. KHÔNG đi "
        "cùng graphic_spec. Đa số beat = null.",
    )
    info_card: Optional[DirectInfoCardDraft] = Field(
        default=None,
        description="Thẻ bullet split-screen: footage chạy nửa TRÁI, thẻ chữ nửa PHẢI. "
        "Dùng khi beat có 2-5 điểm định tính đáng liệt kê (ưu điểm, điều cần biết, bước). "
        "KHÔNG dùng cho beat có 1 con số (dùng overlay) hay so sánh số (dùng graphic_spec). "
        "MUTUAL EXCLUSION: không đi cùng graphic_spec hoặc text_sequence — chọn 1. "
        "GIỚI HẠN per chương: tối đa 2 card (code tự bỏ bớt nếu vượt). Đa số beat = null.",
    )


class ChapterBeats(BaseModel):
    """Output pass 2 cho 1 chương."""

    beats: list[BeatDraft]


# ============ Stage ENRICH (P2B) — sinh dữ kiện BỔ SUNG, tách khỏi pass trích xuất ====
Confidence = Literal["high", "medium"]


class SupplementaryChartDraft(BaseModel):
    """Biểu đồ BỔ SUNG (Req 4) — số KHÔNG có trong script, LLM tra web lấy số THẬT."""

    chart_type: Literal["bar", "line", "pie"]
    title: str = Field(description="Tiêu đề ngắn, ngôn ngữ script")
    unit: str = Field(default="", description="Đơn vị: '$', '%'...")
    data: list[ChartDatumDraft] = Field(
        description="≥2 điểm; có thể gồm số TỪ SCRIPT + số tra web. Số TRÒN, minh hoạ"
    )
    source_note: str = Field(
        default="Số liệu minh hoạ",
        description="Nhãn hiển thị: 'Số liệu minh hoạ'/'Ước tính' khi dùng kiến thức nội tại; "
        "nếu thật sự tra web thì ghi nguồn thật (vd 'Numbeo 2026'). KHÔNG bịa nguồn. Không rỗng.",
    )
    rationale: str = Field(description="1 câu: vì sao số này bổ trợ voice (cho người review)")
    confidence: Confidence = Field(description="Chỉ đề xuất khi đủ tự tin; không chắc thì ĐỪNG")


class InfoCardDraft(BaseModel):
    """Thẻ chữ bullet bổ nghĩa đoạn (Req 6)."""

    title: str = Field(description="Tiêu đề thẻ NGẮN 2-4 từ")
    bullets: list[str] = Field(description="3-5 bullet, mỗi bullet ≤ ~40 ký tự")
    source_note: str = Field(default="Minh hoạ", description="Nhãn disclaimer")
    rationale: str = Field(description="1 câu vì sao thẻ này bổ trợ đoạn")
    confidence: Confidence


class BeatEnrichment(BaseModel):
    """1 đề xuất bổ sung gắn vào 1 beat sẵn có (không đổi beat/timestamp)."""

    beat_id: int = Field(description="beat_id sẵn có để gắn bổ sung")
    kind: Literal["chart", "info_card"]
    chart: Optional[SupplementaryChartDraft] = None
    info_card: Optional[InfoCardDraft] = None


class EnrichmentPlan(BaseModel):
    """Output stage enrich — có thể RỖNG (không beat nào thực sự cần bổ sung)."""

    enrichments: list[BeatEnrichment] = Field(
        default_factory=list,
        description="0..N đề xuất. RỖNG là đáp án tốt nếu không cần bổ sung.",
    )
