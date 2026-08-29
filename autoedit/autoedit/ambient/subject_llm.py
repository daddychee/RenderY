"""Tầng 3 — NÃO chấm kind tiếng chủ thể cho các cảnh BẢNG LUẬT MÙ CHỮ.

Vì sao cần (đo thật RD-89 2026-07-18, cổng TAI đợt 2):
Bảng `subject_rules.yaml` khớp TỪ KHÓA, nên `subject` viết chữ tự do là mù: "Omani
village", "residential neighborhood", "construction site", "Wakan Village landscape"
— cảnh phố THẬT nhưng không từ nào lọt bảng -> im lặng oan 20/120 lượt.

Tầng này CHỈ chạy cho phần đuôi đó (subject mù chữ), KHÔNG đụng ca bảng luật đã quyết:
- bảng luật khớp được -> tin bảng, không hỏi NÃO (rẻ + ổn định + đã qua cổng tai)
- 1 CALL cho CẢ MẺ (không phải 1 call/cảnh) — 20 cảnh ≈ 1 call
- NÃO chỉ được chọn trong DANH SÁCH KIND CÓ FILE THẬT trong kho, + "" = im.
  Không bịa kind mới (NT4 tinh thần: LLM quyết nghĩa, máy giữ ràng buộc).
- Fail-open TRỌN: lỗi mạng/parse/kind lạ -> giữ nguyên kết quả bảng luật, KHÔNG chết.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

MAX_BATCH = 60          # trần cảnh/call — quá dài thì NÃO đuối, chia mẻ
_SYSTEM = """Bạn chấm TIẾNG NỀN (SFX) hợp với từng cảnh video trong một video kể chuyện.

Với mỗi cảnh, chọn ĐÚNG MỘT kind tiếng từ DANH SÁCH CHO PHÉP, hoặc chuỗi rỗng "" nếu
không tiếng nào thật sự hợp.

LUẬT:
1. Tiếng phải là thứ NGHE ĐƯỢC TRONG CẢNH ĐÓ, phát ra từ CHỦ THỂ chính hoặc không gian
   bao quanh nó. Không chọn theo thứ chỉ được NHẮC TỚI trong mô tả.
   Ví dụ: cảnh cận quả chanh (mô tả có chữ "chợ") -> "" chứ KHÔNG phải tiếng chợ.
2. ƯU TIÊN TIẾNG DỄ NGHE (thiên nhiên, nước, gió, chim, động vật). Tiếng ồn đô thị
   (xe cộ, chợ, tàu điện, máy bay) CHỈ chọn khi cảnh THẬT SỰ có phương tiện/đám đông
   đang hoạt động — cảnh phố vắng, làng quê, toà nhà đứng yên thì đừng chọn tiếng xe.
3. THÀ IM CÒN HƠN SAI. Không chắc -> "". Im lặng LUÔN LUÔN an toàn hơn một tiếng lạc.
4. Cảnh quay trên cao (aerial) nhìn xuống địa hình: ưu tiên gió/thiên nhiên, không phải
   tiếng sinh hoạt dưới đất.
5. ĐỪNG CỐ ĐIỀN CHO ĐỦ. Phần lớn cảnh trong danh sách này ĐÁNG IM — chúng lọt vào đây
   chính vì không có tiếng nào rõ ràng. Chọn "" cho mọi cảnh mà bạn phải suy diễn:
   - vật thể/công trình đứng yên (cổng, pháo đài, toà nhà, tượng, bản đồ, đồ vật) -> ""
     (một cái cổng KHÔNG phát ra tiếng xe hơi; một pháo đài KHÔNG phát ra tiếng sóng)
   - cận cảnh người/đồ vật không có hành động gây tiếng -> ""
   - chỉ chọn tiếng gió/biển khi cảnh THẬT SỰ ngoài trời rộng, thấy được không gian đó
6. CỠ CẢNH QUYẾT ĐỊNH NGUỒN TIẾNG — luật quan trọng nhất:
   - Cảnh RỘNG (aerial/wide): thấy được cả không gian -> tiếng KHÔNG GIAN hợp lệ
     (gió, biển, máy móc công trường...).
   - Cảnh HẸP (close_up/medium): khung hình CHỈ CÓ một người/một vật. Tiếng phải phát ra
     từ CHÍNH CHỦ THỂ ĐÓ, do hành động của nó. TUYỆT ĐỐI không lấy tiếng của không gian
     xung quanh, dù mô tả có nhắc tới không gian đó.
     · "người phụ nữ nghe điện thoại" (mô tả có "chợ") -> "" — khung hình không có cái chợ
     · "đèn bí ngô, ánh nến" -> "" — ngọn nến trong bí ngô KHÔNG kêu thành tiếng
     · "bàn tay mở lon nước" -> "" — mở lon không phải tiếng té nước
     · "người đàn ông đang mua bán, mặc cả" -> tiếng chợ ĐƯỢC (chính chủ thể tạo ra nó)
   Câu hỏi tự kiểm cho cảnh hẹp: "thứ phát ra tiếng này có NẰM TRONG KHUNG HÌNH và đang
   ĐỘNG không?" Không -> "".

Trả về mảng `picks`, mỗi phần tử gồm `id` (đúng id đã cho) và `kind`."""


class _Pick(BaseModel):
    id: int
    kind: str = ""


class _Picks(BaseModel):
    picks: list[_Pick] = Field(default_factory=list)


def scene_line(idx: int, subject: str, tags: str, shot_size: str) -> str:
    """1 dòng mô tả cảnh cho NÃO. subject ĐỨNG TRƯỚC (chủ thể chính), tags là bối cảnh."""
    bits = [f"[{idx}] chủ thể: {subject or '(không rõ)'}"]
    if shot_size:
        bits.append(f"cỡ cảnh: {shot_size}")
    if tags:
        bits.append(f"bối cảnh: {tags[:200]}")
    return " | ".join(bits)


def score_unmatched(scenes: list[dict], kinds: list[str], client) -> dict[int, str]:
    """scenes = [{"id", "subject", "tags", "shot_size"}] (CHỈ ca bảng luật mù chữ).
    kinds = kind CÓ FILE THẬT trong kho. Trả {id: kind} — thiếu id nào = giữ nguyên cũ.

    Fail-open: mọi lỗi -> {} (bảng luật giữ nguyên quyết định)."""
    if not scenes or not kinds:
        return {}
    allowed = sorted(set(kinds))
    out: dict[int, str] = {}
    for i in range(0, len(scenes), MAX_BATCH):
        chunk = scenes[i:i + MAX_BATCH]
        user = "\n".join([
            "DANH SÁCH KIND CHO PHÉP (chỉ được chọn trong đây, hoặc \"\"):",
            ", ".join(allowed),
            "",
            f"CÁC CẢNH CẦN CHẤM ({len(chunk)}):",
            *[scene_line(s["id"], s.get("subject", ""), s.get("tags", ""),
                         s.get("shot_size", "")) for s in chunk],
        ])
        try:
            picks, _usage = client.complete(_SYSTEM, user, _Picks)
        except Exception:
            continue          # fail-open: mẻ này giữ bảng luật, mẻ sau vẫn thử
        shot_of = {s["id"]: s.get("shot_size", "") for s in chunk}
        for p in picks.picks:
            # chặn 3 kiểu bịa (NÃO quyết nghĩa, máy giữ ràng buộc):
            # id ngoài mẻ · kind ngoài kho · kind KHÔNG GIAN gán cho cảnh HẸP
            if p.id not in shot_of:
                continue
            if p.kind and p.kind not in allowed_for_shot(allowed, shot_of[p.id]):
                continue
            out[p.id] = p.kind
    return out


# Kind KHÔNG được cho NÃO chọn — chạy thật RD-89 2026-07-18 lộ ra: cho chọn MỌI kind
# có file thì NÃO vơ cả kind KỸ THUẬT lẫn kind quá đặc thù ("Oman gate"->car_interior,
# "woman tending plants"->bird, "opening soda can"->click, người mặc đồ->default).
# - default/ambient_*: kind KỸ THUẬT (nền chung), không phải tiếng chủ thể nghe được
# - click/whoosh/impact/hit: SFX GIAO DIỆN của tầng hook (S3), khác vai hoàn toàn
NON_SUBJECT_KINDS: frozenset[str] = frozenset({
    "default", "click", "whoosh", "impact", "hit", "swell", "riser", "drone",
})

# Kind NỘI THẤT/RẤT ĐẶC THÙ — chỉ đúng khi nhìn thấy ĐÍCH DANH, mà "nhìn thấy đích danh"
# thì bảng luật đã bắt được rồi (không rơi xuống tầng này). Để NÃO chọn = nó suy diễn:
# "Oman gate" -> car_interior đã lọt CẢ SAU KHI prompt dặn kỹ luật vật-đứng-yên
# (chạy thật RD-89 2026-07-18, 2 vòng). Bài học: ràng buộc cứng đặt vào CODE, đừng
# trông vào prompt — prompt chỉ lo phần nghĩa mềm.
INTERIOR_KINDS: frozenset[str] = frozenset({
    "car_interior", "plane_cabin", "subway", "escalator", "stadium", "racecar",
})

# Cỡ cảnh RỘNG — thấy được cả không gian nên tiếng KHÔNG GIAN mới hợp lệ.
WIDE_SHOTS: frozenset[str] = frozenset({"aerial", "wide", "extreme_wide", "establishing"})

# Kind tiếng KHÔNG GIAN — chỉ đúng khi cảnh RỘNG. Cảnh hẹp (close_up/medium) khung hình
# chỉ có 1 người/1 vật, tiếng phải phát ra từ CHÍNH chủ thể đó.
# Đo thật RD-89 vòng 3 (user chê 3/19 ca NÃO): 3 ca sai ĐỀU cảnh hẹp gán tiếng không gian
# — "woman on phone"(medium)->market vì tag có `market` · "jack-o'-lantern"(medium)->fire
# vì tag có `candlelight` · "opening soda can"(close_up)->splash. 15 ca cảnh rộng: user
# DUYỆT hết. Ranh giới cỡ cảnh tách sạch đúng/sai -> chặn được bằng code.
SPATIAL_KINDS: frozenset[str] = frozenset({
    "wind", "ocean", "urban_street", "market", "people_activity", "rain", "snowstorm",
    "nature_forest_field", "rumble", "underwater", "waterfall", "snowfall",
    "splash", "water", "stream", "ice", "volcano", "boat", "ship", "traffic",
})


def allowed_for_shot(kinds: list[str], shot_size: str) -> list[str]:
    """Kind NÃO được phép chọn cho 1 cảnh, theo cỡ cảnh. Cảnh rộng -> đủ; cảnh hẹp ->
    bỏ kind tiếng KHÔNG GIAN (xem SPATIAL_KINDS). shot_size rỗng (mù tag) -> coi như
    HẸP: thà siết còn hơn gán tiếng không gian cho cảnh không biết cỡ."""
    if shot_size in WIDE_SHOTS:
        return kinds
    return [k for k in kinds if k not in SPATIAL_KINDS]


def kinds_with_files(niche_path: Path, exclude_files=None) -> list[str]:
    """Kind CÓ ÍT NHẤT 1 file trong kho niche, TRỪ kind kỹ thuật/UI — danh sách NÃO
    được phép chọn. Đọc qua list_variants nên tôn trọng cả cờ --no-epidemic (cùng
    chokepoint). Lọc NON_SUBJECT_KINDS ở ĐÂY (phía máy) chứ không nhờ prompt dặn NÃO:
    ràng buộc cứng thì đặt vào code, prompt chỉ lo phần NGHĨA."""
    from autoedit.ambient.library import list_variants, niche_kinds
    blocked = NON_SUBJECT_KINDS | INTERIOR_KINDS
    return [k for k in niche_kinds(niche_path)
            if k not in blocked and list_variants(k, niche_path, exclude_files)]
