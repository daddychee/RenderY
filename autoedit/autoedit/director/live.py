"""Đường phiên sống L2b sâu (F9) — ỐNG xuất ngữ cảnh + nhận/gác draft đạo diễn.

Mảnh 1: `direct-context` — ghi direct_context.md (transcript đánh số `[i]word` + BẢNG
        RÀNG BUỘC CỨNG sinh TỪ HẰNG SỐ CODE, không chép tay — *foundation quản Ý,
        bảng này quản SỐ*, chốt rà chồng chéo 2026-07-04).
Mảnh 3: `direct-ingest` — đọc director_draft.json, chạy NGUYÊN battery validator của
        direct cũ + check_breathing_placement (lỗi kèm gợi ý thay xóa âm thầm — vá #2).
        Lỗi → trả danh sách, KHÔNG ghi gì (vòng retry = hội thoại). Pass → hậu xử lý
        Y HỆT đường cũ (runner.drafts_to_beats + finalize_beats), ghi beats + beats.json.

NT4: phiên chỉ trả word index — mọi timestamp tính từ transcript.
Đường `autoedit direct` cũ GIỮ NGUYÊN (fallback + xương L1) — từ D2 (2026-07-09) nó
tái dùng `vocab_block`/`dna_block` ở đây cho pass 2 (runner import lười, tránh vòng).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ValidationError

from autoedit.director import validator
from autoedit.director.prompts import numbered_words
from autoedit.director.runner import (
    beat_errors,
    drafts_to_beats,
    finalize_beats,
    write_beats_review,
)
from autoedit.director.schema import BeatDraft, Outline
from autoedit.packager.coverage import MIN_SHOT_DUR
from autoedit.project import Project, Stage, StageRecord, StageStatus

CONTEXT_FILE = "direct_context.md"
DRAFT_FILE = "director_draft.json"


# --------------------------- Mảnh 1: direct-context ---------------------------
# CÔNG CỤ HÌNH (2026-07-14): đường sâu không ăn prompts.py nên phải dạy tại đây.
# 05/09: user bỏ graphic tự render (card/chart xấu, không work) — block rút còn
# kinetic text; có nhả info_card/graphic_spec thì _resolve_* của runner gạt.
_CONG_CU_HINH_BLOCK = """\
## CÔNG CỤ HÌNH NGOÀI FOOTAGE — kinetic text (đừng bỏ quên)

- `text_sequence` (kinetic) — HIẾM, 1-2 lần/video ở câu chốt đắt nhất: chẻ chữ ĐANG NÓI
  thành 2-4 cụm verbatim liền mạch.
- `info_card`/`graphic_spec`: ĐÃ TẮT — luôn để null. Con số đáng nhấn dùng overlay.
Beat chuyển tiếp/setup: không gì cả."""


# Luật "bán thuốc" (user chốt 2026-07-13, DS5-083 b014 Jenga): đường sâu KHÔNG ăn
# prompts.py nên luật kể-chuyện-bằng-hình phải nằm ngay trong direct_context.md.
_BAN_THUOC_BLOCK = """\
## LUẬT KỂ CHUYỆN BẰNG HÌNH — chống "bán thuốc" (user chốt 2026-07-13)

**VOICE kể ẩn dụ — HÌNH kể câu chuyện.** Script TỰ mượn ẩn dụ/ví von/giả định từ domain
ngoài ("picture the ocean as a giant Jenga tower", domino…) hay nói trực tiếp với người
xem ("wherever you're watching from") → KHÔNG minh họa nghĩa đen của chữ. `visual_concept`
tiếp tục ở THẾ GIỚI của video_subject/central_subject, diễn ẩn dụ bằng hình TRONG thế giới
đó (tháp loài → rạn san hô tầng tầng đàn cá; "rút khối" → cá mập biến khỏi khung hình;
sụp đổ → đàn cá tan tác). Hình CHỈ rời thế giới chủ đề khi content nói về thực thể/sự kiện
THẬT đang là chủ đề (đầu bếp có tên, cảng cá, thành phố mất điện vì sứa).
- `central_subject` của outline KHÔNG được chứa thủ pháp tu từ của script — cấm kiểu
  "food web (Jenga tower metaphor)": nó đầu độc mọi neo hạ nguồn.
- `visual_level: metaphorical` = ẩn dụ THỊ GIÁC do MÌNH thêm, diễn trong thế giới chủ đề —
  không bao giờ = minh họa ẩn dụ có sẵn của script.
- direct-ingest sẽ liệt kê "⚠ nghi bán thuốc" cho beat có concept 0 chữ dính chủ đề
  (warning-only, có false-positive) — soi tay từng beat đó trước khi đi tiếp."""


# --------------------------- Luật WORLD-LOCK theo niche ------------------------
# User chốt 2026-07-14 (DS3-084 b17-24 "phôi cá mập" → miệng người/lab; b213-217 "in
# people/ultrasound" → ảnh siêu âm). KHÁC "bán thuốc": bán thuốc cấm mượn ẩn dụ domain
# ngoài; world-lock cấm RỜI THẾ GIỚI HÌNH của niche kể cả khi script CHỦ ĐÍCH nói về
# người/y học/đất liền — vì khán giả niche này tới để XEM thế giới đó (deepsea = đại dương).
# Data-driven: chỉ niche khai trong WORLD_LOCK bị khóa; niche khác (space/travel) trả '' →
# context y như cũ (không ép thế giới sai).
#
# schema mỗi entry:
#   world      = tên thế giới hình 1 dòng (dưới nước / đại dương sâu)
#   fillers    = cảnh nền quen thuộc để rơi về khi kho không có đúng chủ thể
#   off_world  = KIND thực thể vẫn được rời thế giới (thực thể THẬT là sinh vật/vật thể biển)
WORLD_LOCK: dict[str, dict[str, str]] = {
    "deepsea": {
        "world": "DƯỚI NƯỚC / đại dương sâu — mọi khung hình ở lại trong nước biển",
        "fillers": "cảnh biển sâu quen thuộc: nước tối len ánh sáng, đàn cá nhỏ bơi, "
                   "rạn/đáy biển, hạt lơ lửng, bóng loài săn mồi lướt qua, chính loài "
                   "cá mập/sinh vật đang nói (dù không đúng khoảnh khắc)",
        "off_world": "sinh vật/vật thể biển THẬT có tên (một loài cá mập cụ thể, xác tàu "
                     "đắm, tàu lặn/ROV, nhà khoa học BIỂN trên tàu/dưới nước) — người trên "
                     "đất liền/lab/ảnh y khoa KHÔNG bao giờ đủ điều kiện",
    },
}


def world_lock_block(niche: str) -> str:
    """Khối luật GIỮ THẾ GIỚI HÌNH của niche (world-lock). In vào direct_context.md
    (đường sâu) + library_context (đường direct cũ). Fail-open: niche không khai trong
    WORLD_LOCK → trả '' (không ép thế giới sai cho space/travel)."""
    lock = WORLD_LOCK.get((niche or "").strip().lower())
    if not lock:
        return ""
    return "\n".join([
        f"## LUẬT GIỮ THẾ GIỚI HÌNH — niche '{niche}' (user chốt 2026-07-14)",
        "",
        f"**THẾ GIỚI HÌNH CỦA NICHE = {lock['world']}.** Khán giả niche này tới để XEM "
        "thế giới đó. MỌI `visual_concept` và `central_subject` PHẢI ở trong thế giới này —"
        " kể cả khi câu script CHỦ ĐÍCH nói về con người, y học, đất liền, hay đời sống "
        "người xem. Đây KHÔNG phải lỗi 'bán thuốc' (mượn ẩn dụ) — đây là script kể chuyện "
        "THẬT ngoài thế giới niche, nhưng HÌNH vẫn phải kể bằng thế giới niche.",
        "- Ví dụ bệnh (DS3-084): câu \"one embryo develops teeth first\" → concept ĐÚNG = "
        "cận hàm/răng của chính loài cá mập, KHÔNG phải miệng người. Câu \"something like "
        "it happens in people too — doctors call it vanishing twin syndrome\" → HÌNH vẫn "
        "là phôi cá mập trong tử cung tối / bóng phôi mờ dần, KHÔNG phải ảnh siêu âm người.",
        f"- Khi kho/Pexels KHÔNG có đúng chủ thể (vd 'phôi cá mập nở') → rơi về NỀN NICHE, "
        f"KHÔNG rơi về người/lab: {lock['fillers']}. Bland-đúng-thế-giới THẮNG "
        "specific-sai-thế-giới (WRONG-vs-BLAND).",
        f"- `sourcing_route`: KHÔNG route `entity` (ảnh thật) cho người/sự kiện y khoa/đời "
        "sống đất liền dù script nêu tên. Route `entity` CHỈ dành cho: "
        f"{lock['off_world']}.",
        "- `central_subject` mỗi chương KHÔNG được mời người ngoài thế giới vào (cấm kiểu "
        "\"...and the researchers who study them\" nếu nhà nghiên cứu ở lab đất liền) — "
        "central_subject là thứ DƯỚI NƯỚC quay được.",
    ])


def hard_constraint_table() -> str:
    """Bảng ràng buộc CỨNG in từ hằng số code — máy gác đúng các số này ở ingest."""
    v = validator
    return "\n".join(
        [
            "| Ràng buộc | Giá trị (máy GÁC ở direct-ingest — không thương lượng) |",
            "|---|---|",
            f"| Thời lượng beat | {v.MIN_BEAT_SEC}–{v.MAX_BEAT_SEC:.0f}s. Ngắn hơn bị GỘP vào beat kề "
            f"(mất ý đồ) — muốn nhịp cắt NHANH dùng shot_count 2–3, KHÔNG đẻ beat ngắn |",
            f"| Hình thở (breathing_after_sec) | 0 hoặc {v.MIN_BREATHING_SEC}–{v.MAX_BREATHING_SEC:.0f}s; "
            f"CHỈ đặt tại từ mà voice có nghỉ thật ≥{v.MIN_BREATHING_PAUSE}s (sai chỗ bị trả lỗi kèm gợi ý). "
            "DNA editor: ÍT nhưng SÂU — ~1 ô/45-90s, cuối MỖI chương 2-5s, 1-2 lần/video 3.5-6s tại mặc khải lớn |",
            f"| Câu đinh (rhetorical_pause) | ≤{v.MAX_RHETORICAL_PER_CHAPTER}/chương, CHỈ beat kết GIỮA câu "
            "(không dấu) mà chỗ ngắt có sức nặng tu từ (vd '…cosmic house ‖ But one'); "
            "máy ngắt ~1s nếu voice nghỉ thật, sai chỗ máy tự bỏ |",
            "| Hook (chương đầu) | ≥1 hình thở sau punchline; KHÔNG BAO GIỜ 2 beat thở liên tiếp |",
            f"| Query stock | ≤{v.MAX_QUERY_WORDS} từ mỗi query |",
            f"| Chart + info-card | ≤{v.MAX_CHARTS_PER_CHAPTER} chart + ≤{v.MAX_CARDS_PER_CHAPTER} card "
            f"mỗi chương (cái thứ 3+ bị cắt) |",
            f"| Text overlay | ≤{v.OVERLAY_TEXT_MAX} ký tự (kind gõ máy name/place/quote: ≤{v.TYPING_TEXT_MAX}) |",
            f"| Shot con (shot_count>1) | ≥{MIN_SHOT_DUR}s mỗi shot — beat ngắn tự bị kẹp bớt shot |",
            "| Coverage | chapters phủ kín từ [0..cuối]; beats phủ kín đúng chương; index inclusive, "
            "beat kế = end_word trước + 1, không hở/không đè |",
            "| Timestamp | KHÔNG BAO GIỜ tự sinh — chỉ trả word index (0-based) trên transcript dưới đây |",
        ]
    )


def vocab_block(niche: str, conn=None) -> str:
    """Khối TỪ VỰNG KHO LOCAL (C4 controlled vocabulary): in từ vựng THẬT của kho để
    NÃO viết `search_queries.local` trúng từ kho nói — thay vì đoán bằng "ngôn ngữ
    Pexels" (bài học PB8: từ chuyển động AND-trượt oan vì GLM tag frame tĩnh).
    Fail-open: không niche / kho rỗng / db lỗi -> trả '' (context y như cũ)."""
    if not niche:
        return ""
    try:
        from autoedit.library import db
        if conn is None:
            conn = db.connect()
        vocab = db.vocab_for_niche(conn, niche)
    except Exception:
        return ""
    if not vocab["total"]:
        return ""

    def fmt(pairs) -> str:
        return " · ".join(f"{w}×{n}" for w, n in pairs)

    return "\n".join([
        f"## TỪ VỰNG KHO LOCAL (niche '{niche}' — {vocab['total']} asset: "
        f"{vocab['videos']} video / {vocab['images']} ảnh)",
        "",
        "Kho local là nguồn CHÍNH. Với beat route stock/local, điền thêm "
        "`search_queries.local` theo 3 luật:",
        "1. 0-2 query, mỗi query 2-4 DANH TỪ CẢNH lấy ĐÚNG từ bảng dưới — kho AND-match "
        "từng từ, KHÔNG hiểu đồng nghĩa (tag ghi 'spacewalk' mà query 'astronaut floating' = trượt).",
        "2. KHÔNG dùng từ chuyển động/máy quay (rotating, timelapse, zoom...) — tag chấm từ "
        "frame TĨNH, không bao giờ chứa từ đó.",
        "3. Kho không phủ concept → để local RỖNG, Pexels lo — đừng sáng tác query để cứu. "
        "Từ đếm càng cao càng chắc có hàng.",
        "",
        f"- Loại cảnh: {fmt(vocab['scene_types'])}",
        f"- Tag hay gặp: {fmt(vocab['tags'])}",
        f"- Từ trong subject: {fmt(vocab['subject_words'])}",
    ])


def dna_block(niche: str, library_root=None) -> str:
    """Khối CHỮ KÝ PACING NICHE (DNA d1 Mảnh A — MO_TA_VAN_HANH_DNA_D1 §6): in số đo
    THẬT của niche từ dna.json (live — tự mới sau mỗi lần `library-dna`) để NÃO chọn
    độ dài beat/shot_count đúng chuẩn niche. KHÔNG in số ô thở (§6b: ngược chiều luật
    "ÍT nhưng SÂU" — vi nghỉ máy hình thở 3.0 đã tự lo theo pause_dna).
    Fail-open: không niche / không dna.json / số suy biến -> trả '' (context y như cũ)."""
    if not niche:
        return ""
    try:
        from autoedit.library.dna import load_dna
        from autoedit.library.profile import niche_dir, resolve_library_root

        dna = load_dna(niche_dir(niche, root=resolve_library_root(library_root)))
        p = dna["pacing"]
        cpm = p["cuts_per_min"]
        med, std = p["shot_len"]["median"], p["shot_len"]["std"]
        hold_share, hold_med = p["holds"]["share"], p["holds"]["median_s"]
        hook_med = p["hook45"]["median"]
        if not (cpm and med):
            return ""
    except Exception:
        return ""
    hook_vs = "cắt NHANH hơn thân" if hook_med < med else "KHÔNG nhanh hơn thân — đừng ép dồn cắt ở hook"
    return "\n".join([
        f"## CHỮ KÝ PACING NICHE '{niche}' (DNA đo từ {dna['drafts']} draft editor — "
        f"{dna['timeline_min']} phút · {p['shots']} shot)",
        "",
        "Số đo THẬT của niche — khi vênh heuristic chung, số này THẮNG (luật chốt "
        "2026-07-07). Dùng khi chọn độ dài beat + shot_count (shot con ≈ trung vị shot). "
        "KHÔNG chỉnh hình thở theo khối này — nhịp nghỉ đã có lớp máy lo riêng theo DNA "
        "nghỉ của editor.",
        "",
        f"- Mật độ cắt: {cpm} cut/phút (validator sau assemble cảnh báo nếu ra ngoài "
        f"[{cpm / 2:.1f}; {cpm * 2:.1f}])",
        f"- Độ dài shot: trung vị {med}s · lệch chuẩn {std}s — xen kẽ dài/ngắn, đừng đều tăm tắp",
        f"- Hold ≥5s: {hold_share:.0%} số shot, trung vị {hold_med}s — niche này KHÔNG ngại shot dài",
        f"- Hook 45s đầu: trung vị {hook_med}s — {hook_vs}",
    ])


def boost_block(project: Project, niche: str = "", library_root=None) -> str:
    """Khối SỞ THÍCH KHÁN GIẢ (BOOST — MO_TA_VAN_HANH_BOOST.md): in yêu cầu cảnh dạng X
    (inputs.boosts per-video + audience_bias của niche) để NÃO chủ động đan X vào
    concept — tầng mạnh nhất của gói (bonus phễu 1,0 KHÔNG cứu nổi concept viết
    generic — bài học b018 REF). Fail-open: không khai gì / lỗi đọc -> '' (context
    y như cũ). Import lười sourcer.runner để tái dùng parse + audience_bias (1 nguồn
    luật cho cả 2 tầng NÃO/phễu)."""
    try:
        from autoedit.library.profile import resolve_library_root
        from autoedit.sourcer.runner import _audience_bias, _parse_boosts
        specs = _parse_boosts(
            list(project.inputs.boosts)
            + _audience_bias(niche, resolve_library_root(library_root)))
    except Exception:
        return ""
    if not specs:
        return ""
    scope_vn = {"all": "cả bài", "hook": "hook"}
    khai = " · ".join(f"'{t}' ({scope_vn.get(sc, 'chương ' + sc[2:])})" for t, sc in specs)
    return "\n".join([
        "## SỞ THÍCH KHÁN GIẢ (BOOST — người khai; phễu đã tự cộng điểm cảnh kho match)",
        "",
        f"Khán giả kênh này THÍCH xem: {khai}.",
        "Khi viết visual_concept + search_queries:",
        "1. Chủ động ĐAN chủ thể này vào HOOK và các beat chêm/nghỉ/generic (beat không",
        "   có thực thể/sự kiện cụ thể phải kể) — editor giỏi đổ cảnh khán giả thích vào",
        "   đúng những đoạn khó kiếm footage.",
        "2. NEO theo bối cảnh chương: chương nói về Pháp -> 'woman walking parisian",
        "   street', KHÔNG bê chủ thể lạc thế giới/quốc gia của đoạn (world-lock +",
        "   geo-gate vẫn trên hết).",
        "3. Beat có thực thể/sự kiện cụ thể phải kể -> kể thứ đó, ĐỪNG ép chủ thể sở",
        "   thích vào.",
        "4. Query của beat đan X viết theo TỪ VỰNG KHO phía trên để phễu match được",
        "   cảnh kho thật.",
    ])


_TEMPO_MAP_BLOCK = "\n".join([
    "## TEMPO MAP — nhịp độ theo cấu trúc hồi (feedback đạo diễn hình ảnh, user duyệt 2026-07-14)",
    "",
    "Video 'đều đều' = lỗi nặng nhất về nhịp. Ở outline, MỖI chương PHẢI khai `tempo_curve`",
    "— đường nhịp TRONG chương (menu đóng):",
    "- `fast_settle` — vào nhanh → lắng dần. MẶC ĐỊNH cho chương HOOK (luật hook nhanh THẮNG",
    "  — không mở chậm ở chương 1).",
    "- `slow_build_slow` — mở chậm → giữa dồn dần → kết thả. Curve chuẩn cho chương THÂN.",
    "- `build` — dồn dần đều tới cuối. Chương dẫn vào cao trào.",
    "- `dense` — dày đặc gần suốt, kết bằng 1 hold. Chương cao trào.",
    "- `calm` — chậm đều, ít cắt. Chương kết / chương lặng chủ đích.",
    "Luật:",
    "1. SHUFFLE chống đều: KHÔNG 3 chương liền kề cùng curve; video ≥4 chương dùng ≥3 loại.",
    "2. Nhanh/chậm là TƯƠNG ĐỐI quanh trung vị shot trong khối DNA niche phía trên (nếu",
    "   có) — đừng đẩy cả video ra ngoài dải cut/phút của niche.",
    "3. THỰC THI nhanh = beat ngắn dần (nhưng ≥ sàn, xem bảng) + shot_count 2–3 khi beat đủ",
    "   dài; chậm = beat dài + hình thở. Máy sẽ đối chiếu curve khai vs độ dài beat thật",
    "   (ingest cảnh báo 'khai một đằng làm một nẻo').",
    "4. Fan-out chương dài: prompt dispatch mỗi chương PHẢI chứa dòng tempo của chương đó",
    "   (vai hồi + curve + cách thực thi) — agent con không tự thấy tempo map toàn cục.",
])


def build_direct_context(project: Project, niche: str = "", conn=None) -> str:
    """Nội dung direct_context.md — 'hệ tọa độ' duy nhất phiên sống được phép dùng (NT4)."""
    align = project.stages.get(Stage.ALIGN)
    if align is None or align.status != StageStatus.DONE or not project.transcript:
        raise RuntimeError(
            "Stage align chưa xong hoặc transcript rỗng — chạy `autoedit align` trước."
        )
    words = project.transcript
    lines = [
        f"# DIRECT CONTEXT — {project.project_id}",
        "",
        f"- Voice: {words[-1].end:.1f}s thoại · {len(words)} từ (index 0..{len(words) - 1})",
    ]
    if project.inputs.brief:
        lines.append(f"- Brief: {project.inputs.brief}")
    if project.inputs.channel:
        lines.append(f"- Channel: {project.inputs.channel}")
    lines += [
        "",
        "## BẢNG RÀNG BUỘC CỨNG (sinh tự động từ hằng số code)",
        "",
        hard_constraint_table(),
        "",
        _CONG_CU_HINH_BLOCK,
        "",
        _BAN_THUOC_BLOCK,
        "",
    ]
    wl = world_lock_block(niche)
    if wl:
        lines += [wl, ""]
    vb = vocab_block(niche, conn=conn)
    if vb:
        lines += [vb, ""]
    db_ = dna_block(niche)
    if db_:
        lines += [db_, ""]
    bb = boost_block(project, niche)
    if bb:
        lines += [bb, ""]
    lines += [_TEMPO_MAP_BLOCK, ""]
    lines += [
        "## OUTPUT",
        "",
        f"Viết `{DRAFT_FILE}` vào folder project — đúng schema đường direct cũ "
        "(`director/schema.py`): "
        '`{"outline": {tone, motifs, video_subject, chapters: [ChapterPlan...]}, '
        '"chapters": [{"chapter_id": n, "beats": [BeatDraft...]}]}`. '
        "`video_subject` (V3) = PHẠM VI chủ thể cả video trong 1 dòng, được phép nhiều "
        'chủ thể ("the Moon and its far side" / "all 8 planets — one per chapter") — '
        "phễu dùng làm vòng ngoài chặn footage sai thực thể. "
        "`tone` (C4/b1) = THÁI ĐỘ cả video, là HẰNG SỐ: mood mỗi chương/beat phải "
        "CHẠM tone này — mood đổi theo mạch content là có chủ đích (buồn → hy vọng "
        "tốt), nhưng không được lệch sang thái độ trái với tone. "
        f"Rồi chạy: `autoedit direct-ingest <project_dir>` — lỗi sẽ được liệt kê để sửa, "
        "pass thì beats được ghi vào project.json.",
        "",
        "## TRANSCRIPT (từ đánh số `[i]word`, 0-based)",
        "",
        numbered_words(words),
        "",
    ]
    return "\n".join(lines)


def write_direct_context(project: Project, niche: str = "", conn=None) -> Path:
    path = Path(project.project_dir) / CONTEXT_FILE
    path.write_text(build_direct_context(project, niche=niche, conn=conn), encoding="utf-8")
    return path


# --------------------------- Mảnh 3: direct-ingest ----------------------------
class ChapterDraft(BaseModel):
    """Beats 1 chương trong director_draft.json — beats tái dùng BeatDraft y nguyên."""

    chapter_id: int
    beats: list[BeatDraft]


class DirectorDraft(BaseModel):
    """File director_draft.json phiên sống nộp — outline tái dùng schema cũ y nguyên."""

    outline: Outline
    chapters: list[ChapterDraft]


def validate_draft(draft: DirectorDraft, words) -> list[str]:
    """Nguyên battery của direct cũ (beat_errors) + check thở-đúng-chỗ. Rỗng = pass."""
    errors = validator.check_coverage(
        [(c.start_word, c.end_word) for c in draft.outline.chapters], 0, len(words) - 1
    )
    if errors:
        return [f"outline: {e}" for e in errors]

    want_ids = [c.chapter_id for c in draft.outline.chapters]
    got_ids = [ch.chapter_id for ch in draft.chapters]
    if got_ids != want_ids:
        return [
            f"chapters phải khớp outline theo đúng thứ tự: outline={want_ids}, draft={got_ids}"
        ]

    plan_by_id = {c.chapter_id: c for c in draft.outline.chapters}
    hook_id = want_ids[0]
    out: list[str] = []
    for ch in draft.chapters:
        plan = plan_by_id[ch.chapter_id]
        ch_errors = beat_errors(
            ch.beats, plan.start_word, plan.end_word, words, is_hook=(ch.chapter_id == hook_id)
        )
        # Nâng cấp so đường cũ (vá #2): thở sai chỗ = LỖI kèm gợi ý chỗ nghỉ thật,
        # thay vì để enforce_breathing_pauses xóa âm thầm sau này.
        ch_errors.extend(
            validator.check_breathing_placement(ch.beats, words, plan.start_word, plan.end_word)
        )
        out.extend(f"chương {ch.chapter_id}: {e}" for e in ch_errors)
    return out


def ban_thuoc_warnings(outline: dict, beats: list) -> list[str]:
    """Lưới đỡ máy cho luật "bán thuốc" (warning-only, KHÔNG chặn — filter-overload-guard):
    beat stock/local mà visual_concept 0 token trùng video_subject + central_subject chương
    → nghi minh họa nghĩa đen ẩn dụ của script. False-positive chấp nhận được (concept diễn
    đạt bằng từ khác, vd "city blackout" cho chương sứa) — đây là danh sách SOI TAY.
    Route entity/graphic miễn (thực thể thật/chart được phép rời thế giới chủ đề).
    Mù khi central_subject bị nhiễm chính ẩn dụ đó — tầng prompt pass 1 gác chỗ ấy."""
    from autoedit.sourcer.breath import _subject_tokens

    def _norm(tokens: set[str]) -> set[str]:
        # gọt số nhiều tiếng Anh thô ("sharks"->"shark") — 2 vế cùng gọt nên vẫn khớp nhau
        return {t[:-1] if len(t) > 3 and t.endswith("s") else t for t in tokens}

    subs = {c.get("chapter_id"): c.get("central_subject") or ""
            for c in (outline or {}).get("chapters", [])}
    video_subject = (outline or {}).get("video_subject") or ""
    out: list[str] = []
    for b in beats:
        if b.sourcing_route not in ("stock", "local_library"):
            continue
        anchor = _norm(_subject_tokens(video_subject, subs.get(b.chapter, "")))
        if not anchor:
            continue
        if not (_norm(_subject_tokens(b.visual_concept)) & anchor):
            out.append(
                f"nghi 'bán thuốc' b{b.beat_id:03d}: concept "
                f"'{(b.visual_concept or '')[:60]}' 0 chữ dính video_subject/"
                f"central_subject — nếu câu này là ẩn dụ/ví von/nói-với-người-xem thì "
                f"hình phải ở lại thế giới chủ đề (soi tay, warning-only)")
    return out


def run_direct_ingest(project: Project, draft_path: Path | None = None) -> tuple[Project, list[str]]:
    """Trả (project, errors). errors rỗng = beats đã ghi, stage direct DONE.
    Có lỗi → KHÔNG ghi gì vào project.json (phiên sửa draft rồi nộp lại)."""
    align = project.stages.get(Stage.ALIGN)
    if align is None or align.status != StageStatus.DONE or not project.transcript:
        raise RuntimeError(
            "Stage align chưa xong hoặc transcript rỗng — chạy `autoedit align` trước."
        )
    path = Path(draft_path) if draft_path else Path(project.project_dir) / DRAFT_FILE
    if not path.exists():
        raise RuntimeError(
            f"Không thấy {path} — phiên sống phải viết draft trước (xem {CONTEXT_FILE})."
        )

    try:
        draft = DirectorDraft.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        return project, [
            "schema " + ".".join(str(p) for p in e["loc"]) + f": {e['msg']}"
            for e in exc.errors()
        ]

    words = project.transcript
    errors = validate_draft(draft, words)
    if errors:
        return project, errors

    # -------- pass → hậu xử lý Y HỆT direct cũ (dùng chung code với runner) --------
    record = StageRecord.running()
    project.stages[Stage.DIRECT] = record
    all_drafts: list[tuple[int, BeatDraft]] = []
    for ch in draft.chapters:
        clipped, clip_notes = validator.enforce_chapter_visual_limits(ch.beats)
        record.warnings.extend(clip_notes)
        all_drafts.extend((ch.chapter_id, d) for d in clipped)

    beats = drafts_to_beats(all_drafts, words)
    hook_chapter = draft.outline.chapters[0].chapter_id
    beats, post_notes = finalize_beats(beats, words, hook_chapter)
    record.warnings.extend(post_notes)

    project.beats = beats
    project.outline = draft.outline.model_dump(mode="json")
    # Lưới đỡ "bán thuốc": chỉ cảnh báo, không chặn ingest (soi tay từng beat nghi)
    record.warnings.extend(ban_thuoc_warnings(project.outline, beats))
    # TEMPO MAP: cảnh báo nhịp lúc sửa còn rẻ (trước footage) — warning-only
    record.warnings.extend(validator.check_tempo_map(project.outline, beats))
    record.status = StageStatus.DONE
    record.completed_at = datetime.now(timezone.utc).isoformat()
    project.save()
    write_beats_review(project)
    return project, []
