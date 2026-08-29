# MÔ TẢ VẬN HÀNH — SFX CHỦ THỂ 3 TẦNG (chủ thể vs phông nền)

> Ngày đóng code: 2026-07-18. Trạng thái: 🔄 CHỜ CỔNG TAI (draft `..._V9`).
> Nguồn: user chê 5 ca ở cổng TAI RD-89 đợt 2.

---

## 1. Vấn đề — máy nghe theo PHÔNG NỀN, không theo CHỦ THỂ

User chê (RD-89 "Oman"): *b099 footage sóng biển nhưng SFX tiếng gió · b008 lâu đài
nhưng tiếng phố · b019 người đi bộ không xe cộ nhưng tiếng xe · b033 người nhưng tiếng
gió · b061 quả chanh nhưng tiếng chợ.* Kèm yêu cầu: **ưu tiên SFX dễ nghe (thiên nhiên,
động vật) hơn SFX khó chịu (urban_street)**.

**Chẩn đoán ban đầu SAI, đo mới ra đúng.** Giả thuyết đầu là "khớp nhầm qua câu tả
`description`" — sổ Postgres cho thấy **cả 5 ca khớp qua `tags`**, và `subject` thì
ĐÚNG cả 5:

| Beat | subject (ĐÚNG) | từ trong `tags` gây khớp nhầm | kind sai |
|---|---|---|---|
| b008 | Sultan Qaboos Grand Mosque | `cityscape` | urban_street |
| b019 | man walking desert | `dirt road` | urban_street |
| b033 | Omani men | `desert` | wind |
| b061 | lemons | `market` | market |
| b099 | sunset beach | `beach`, `sand` | wind |

Gốc bệnh: `db_subject_lookup` **gộp phẳng** `subject + tags + description` thành 1 chuỗi
rồi dò từ khóa. `tags` là **danh sách bối cảnh** — GLM liệt kê mọi thứ nhìn thấy, không
phân biệt **chủ thể** với **phông nền**. Quả chanh nằm ở chợ → tag `market` → kêu tiếng chợ.

## 2. Giải — 3 tầng

```
TẦNG 1  subject QUYẾT ĐỊNH      subject khớp bảng luật -> lấy luôn (chủ thể thật)
   ↓ (subject mù chữ)
TẦNG 2  tags CỨU, trừ kind ỒN   tags khớp -> lấy, TRỪ NOISY_KINDS (đòi đích danh)
   ↓ (vẫn không ra)
TẦNG 3  NÃO chấm (tùy chọn)     --sfx-llm: 1 call/mẻ, chỉ ca 2 tầng trên bó tay
```

**NOISY_KINDS** (`schedule.py`) — hiện thực ý *"ưu tiên tiếng dễ nghe"*: `urban_street`,
`market`, `subway`, `plane`, `racecar`, `stadium`, `motorboat`, `snowmobile`, `escalator`.
KHÔNG phải cửa loại — chỉ là **ngưỡng bằng chứng cao hơn**: kind ồn phải đích danh trong
`subject` mới kêu, không được suy từ tag bối cảnh. Tiếng thiên nhiên KHÔNG bao giờ vào
danh sách này (sai cũng dễ nghe).

## 3. Dùng thế nào

```bash
autoedit assemble <project>              # tầng 1+2 (LUÔN bật, không cần cờ)
autoedit assemble <project> --sfx-llm     # + tầng 3 NÃO chấm ca mù chữ
autoedit run <project> --sfx-llm
```

Tầng 3 mặc định TẮT. Bật thì tốn ~1 call NÃO/mẻ (không phải 1 call/cảnh).
`subject_sfx_log::source` = `kho` (bảng luật) | `llm` (NÃO chấm) — soi được ở report.

## 4. Số đo thật RD-89 (120 lượt gốc)

| Bản | Cấu hình | Kết quả |
|---|---|---|
| V4/V5 | trước sửa | 120 lượt · **urban_street 51 (42%)** · 5 ca user chê |
| V6 | tầng 1+2 | 93 lượt · urban_street 34 · im 20 (mù chữ) |
| V9 | tầng 1+2+3 | **119 lượt · urban_street 35 · wind 37 · llm điền 19** |

5 ca user chê sau sửa: b099 `wind`→**ocean** · b008 `urban_street`→**im** ·
b019 `urban_street`→**wind** · b061 `market`→**im** · b033 giữ `wind` (xem §5).

## 5. Ca CỐ Ý KHÔNG SỬA

**b033 "Omani men" (cận mặt người) vẫn ra `wind`.** subject mù chữ → tag `desert` cứu →
`wind` không thuộc NOISY_KINDS nên được cứu. Giữ nguyên có chủ đích: người Oman đứng
giữa sa mạc nghe tiếng gió là hợp lý; đo cả RD-89 chỉ **1 ca** cận-cảnh-người dạng này
→ không đẻ luật riêng cho 1 ca (P2). User chê ca này ở bản cũ khi nó nằm giữa loạt sai khác.

## 6. BẪY tầng 3 — RÀNG BUỘC CỨNG PHẢI ĐẶT VÀO CODE, ĐỪNG TRÔNG VÀO PROMPT

Đây là bài học đắt nhất của gói này, **2 vòng chạy thật mới ra**:

1. **Vòng 1** — cho NÃO chọn trong MỌI kind có file → nó vơ cả kind **kỹ thuật/UI**:
   `"opening soda can"→click`, `"Omani men in traditional dress"→default`,
   `"woman tending plants"→bird`. → chặn `NON_SUBJECT_KINDS` (default/click/whoosh/
   impact/hit/swell/riser/drone).
2. **Vòng 2** — thêm luật *"vật đứng yên không phát ra tiếng đó"* vào prompt, dặn rất kỹ.
   **VẪN LỌT**: `"Oman gate"→car_interior`. → chặn `INTERIOR_KINDS` (car_interior/
   plane_cabin/subway/escalator/stadium/racecar) **bằng code**.

> **Luật rút ra:** kind nội thất/đặc thù chỉ đúng khi nhìn thấy ĐÍCH DANH — mà thấy đích
> danh thì **bảng luật đã bắt được rồi**, không rơi xuống tầng 3. Cho NÃO chọn = mời nó
> suy diễn. Prompt lo phần NGHĨA MỀM, code giữ RÀNG BUỘC CỨNG.

Chống bịa khác (đã có test): NÃO trả `id` ngoài mẻ → bỏ; trả kind ngoài kho → bỏ; lỗi
mạng/parse → `{}` fail-open, bảng luật giữ nguyên quyết định, KHÔNG chặn assemble.

## 6b. VÒNG 3 — CỠ CẢNH QUYẾT ĐỊNH NGUỒN TIẾNG (user chê 3/19 ca NÃO)

User duyệt 16/19 ca tầng 3, chê đúng 3: *b039 người gọi điện→chợ · b074 mở lon nước→
splash · b063 đèn bí ngô→fire*. Đo ra quy luật **tách sạch**:

| | cỡ cảnh | user |
|---|---|---|
| 15 ca | `aerial` / `wide` | **DUYỆT hết** |
| 4 ca | `medium` / `close_up` | **3/4 bị chê** |

Cảnh RỘNG thấy được cả không gian → tiếng không gian đúng. Cảnh HẸP khung hình chỉ có
**một người/một vật** → tiếng phải phát ra từ CHÍNH chủ thể, không phải từ không gian
quanh nó (khung hình không có cái chợ; ngọn nến trong bí ngô không kêu; mở lon ≠ té nước).

**Hai lớp chặn** (prompt đã thua 1 lần ở vòng 2 nên không tin prompt một mình):
- `SPATIAL_KINDS` + `allowed_for_shot()` — kind tiếng KHÔNG GIAN bị loại khỏi danh sách
  cho phép khi cảnh hẹp. Mù cỡ cảnh → coi như HẸP (đo RD-89: 0/119 ca mù, nhánh này chỉ
  gặp ở dữ liệu hỏng — thà siết).
- Prompt luật 6 viết lại thành luật CỨNG kèm đúng 3 ca thật + câu tự kiểm *"thứ phát ra
  tiếng này có NẰM TRONG KHUNG HÌNH và đang ĐỘNG không?"*

**📌 Lỗ hổng KIẾN TRÚC phát hiện kèm (quan trọng hơn 3 ca):** quyết định của NÃO trước
đây **không đi qua các luật an toàn** mà đường bảng luật phải tuân. b063 lộ ra điều này:
luật fire-cận-cảnh (tai V7) vốn chặn đúng ca đó, nhưng NÃO gán thẳng nên lách được. Đã
vá — nhánh `src="llm"` giờ chạy lại luật fire y như đường bảng luật. **Luật chung: mọi
luật an toàn phải áp cho CẢ HAI đường, nếu không NÃO thành cửa sau.**

**Giá phải trả (chấp nhận có ý thức):** b152 *"man in traditional hat shopping"* (medium,
→market) user thấy ỔN nhưng cũng bị chặn theo. Luật cỡ cảnh không phân biệt được "người
ĐANG mua bán" với "người tình cờ đứng ở chợ" — mất 1 ca đúng để chặn 3 ca sai. Muốn cứu
thì thêm `shopping/vendor/bargaining` vào `subject_rules.yaml` (bảng luật bắt trước, khỏi
xuống tầng 3).

Kết quả V10: **13 ca NÃO, toàn cảnh rộng** — đúng nhóm user đã duyệt.

## 7. RÀ CHỒNG CHÉO (P5)

| Tầng cùng quản | Có bị đụng không |
|---|---|
| `subject_rules.yaml` (bảng từ khóa per-niche) | **KHÔNG sửa file** — chỉ đổi CÁCH đọc (trường nào tin trước). Bảng giữ nguyên cho mọi niche. |
| `choose_subject_files` / `list_variants` | **KHÔNG** — vẫn nhận kind rồi chọn biến thể như cũ. Tầng 3 đi qua ĐÚNG chokepoint đó (kể cả `--no-epidemic`). |
| Ambient ô thở (`resolve_slot_subject`) | **CÓ, cùng chiều** — dùng chung `_kind_from_lookup` nên ô thở cũng hết kêu theo phông nền. |
| Hook SFX S3 / drone S1 | **KHÔNG** — khác vai (UI/nền), `NON_SUBJECT_KINDS` chặn NÃO lấn sang. |
| Luật fire-cận-cảnh (tai V7) | **KHÔNG** — nằm trong `_kind_of`, áp cho cả 2 đường subject/tags. |
| `--no-epidemic` (2026-07-18) | **KHÔNG ngược chiều** — `kinds_with_files` đọc qua `list_variants` nên kind bị loại hết file cũng không được NÃO chọn. |

**Ngược chiều tầng cũ?** Không. Cùng chiều luật tách-kind-theo-loài
(`sfx-animal-wildlife-do-phan-giai-loai`) và lưới loài Epidemic — cả ba đều chống
"một rổ trộn nhiều nghĩa".

**Tầng nào ÂM THẦM LẬT được tầng mới?** Đã rà: `db_subject_lookup` đổi từ 2-tuple sang
3-tuple. Mọi caller `subject_kind(*lookup(...))` bằng unpack `*` sẽ đẩy `subject` vào
chỗ `rules` → gom hết qua helper `_kind_from_lookup`, và helper CHẤP NHẬN CẢ 2-tuple
(lookup cũ trong test) → `subject=None` → hành vi cũ y nguyên.

## 8. CÒN NGỎ

- **Cổng TAI chưa qua** — user nghe `..._V9` (đã có lại nhạc 16/16 chương).
- Vài ca tầng 3 còn đáng ngờ, chờ tai phán: b039 *woman on phone*→market ·
  b074 *opening soda can*→splash · b063 *jack-o'-lantern*→fire · b057 *medieval castle*→wind.
- Chưa đo tầng 3 trên niche khác (deepsea/space) — luật đọc `subject` là chung, nhưng
  NOISY_KINDS đang nghiêng theo life-in.
