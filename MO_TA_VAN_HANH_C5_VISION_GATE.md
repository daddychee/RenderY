# MÔ TẢ VẬN HÀNH — C ĐỢT 5: C5 VISION GATE TOP-PICK (mood + đúng chủ thể)

> Trạng thái: **✅ USER DUYỆT 2026-07-10** — chốt cả 3: phạm vi soi = PA-A mọi beat qua
> phễu · C3 ĐÓNG giữ warning-only vĩnh viễn (xóa khỏi backlog) · bắt đầu code M1.
>
> **📌 ĐIỀU CHỈNH 2026-07-10 (cùng ngày, sau khi ĐO tốc độ ở video kiểm V11):**
> 1. **Phạm vi thu về PA-B: CHỈ soi pick KHO LOCAL** (user quyết sau số đo: gate mọi-beat
>    cộng ~17 phút/video — 48' vs 31' không-gate; local-only chỉ cộng ~2-4 phút và trúng
>    đúng lớp lỗi đã chứng minh b60/b68 — tag máy tự sinh). Hằng `GATE_SOURCES` trong
>    visiongate.py — muốn mở lại PA-A chỉ thêm `"pexels"`.
> 2. **BỎ khối schema khỏi prompt gate** (smoke test bắt bệnh GLM chép-schema dai 4/4 lần,
>    ~36s/ca; verdict chỉ 4 key nên example là đủ — pydantic vẫn gác). Call còn ~3-6s.
> 3. **Gate lì đòn** (V11 lần 1 chết 3 lỗi thoáng qua đầu run): xoay 3 GLM key theo attempt
>    + backoff 429 4-12s + tắt theo 3 lỗi LIÊN TIẾP (soi được lại là reset), timeout 30s.
> Nguồn đầu bài: `DINH_HUONG_VIEC_TIEP_THEO.md` NHÓM C dòng C5 + `MO_TA_VAN_HANH_NANG_CAP_V123.md`
> §V3-3c (dời về đợt 5) + NHAT_KY §C6-DIEU-TRA (ca b60/b68) + memory [[roadmap-d-c-scale]].

---

## 1. Bài toán — vì sao cần mắt vision ở phút chót

Mọi tầng gác "đúng chủ thể" hiện nay đều đọc **CHỮ** (tag/description/query), không ai nhìn
**ẢNH THẬT** của footage sắp vào video:

| Ca đã xảy ra (bằng chứng thật) | Tầng chữ nào bắt được? |
|---|---|
| b60: clip Pluto bị GLM tag lúc nạp là "moon" → NÃO chấm "khớp trực tiếp" | Không — chữ nói dối từ gốc. (Đã vá DATA bằng tag lại 102 clip, nhưng mẻ nạp SAU vẫn có thể sinh tag sai mới) |
| b68: clip Destiny GLM tả "đài thiên văn ESO" — mắt user thấy nhà dân; nguồn "Solar System" không có ground truth chữ | Không — **lớp không-ground-truth**, chỉ mắt nhìn frame mới biết |
| Ca 3c V123: ảnh/clip stock "đỏ rực" nhưng slug/description không có chữ "mars" | Không — veto `thuc_the_sai` V3 đọc chữ, chữ không tiết lộ |

**C5 = tầng gác CUỐI, lần đầu nhìn frame thật**, đặt đúng lúc footage vừa tải xong, ngay
trước khi chốt pick.

### Nguyên tắc user ĐÃ CHỐT từ trước (không bàn lại)
1. Chỉ soi **TOP-PICK** — không soi cả pool (V123 §3c, 2026-07-09).
2. Fail → demote, thử ứng viên kế **đúng 1 lần**; vẫn fail → lấy bản tốt nhất + warning
   editor chỉnh tay. **KHÔNG needs_human ồ ạt, KHÔNG thành cửa loại thứ 3.**
3. [[filter-overload-guard]]: gate mới đi dạng **warning trước** — quyền demote chỉ cho ca
   chắc chắn nhất (sai chủ thể rõ ràng); **mood đợt này chỉ warning**, nâng quyền sau khi
   user phán trúng/oan qua video kiểm.

---

## 2. Thiết kế

### 2a. Vị trí cắm — `_pick_by_funnel` (sourcer/runner.py), vòng tải shot

Sau khi `_materialize` tải xong ứng viên sắp thành **shot CHÍNH (lead)** của beat:

```
frame giữa file thật (1 frame, 960px — kỷ luật chi phí đã chốt PB6)
  → 1 call GLM-4.6V: "frame này có ĐÚNG chủ thể beat cần không? mood có khớp không?"
  → subject "yes"/"unsure"  → NHẬN pick (phân vân KHÔNG veto — y luật c2)
  → subject "no" lần 1      → DEMOTE: thử ứng viên điểm kế (cũng soi nốt — hết budget 2 call/beat)
  → subject "no" lần 2      → LẤY ứng viên #1 (điểm phễu cao nhất) + warning "editor soát tay"
  → mood "no"               → KHÔNG đổi pick, chỉ warning (đợt này)
  → GLM lỗi/timeout/thiếu key → NHẬN pick + warning (fail-open — gate là tối ưu, không giết stage)
```

- Chỉ soi **lead** — extra_shots (shot 2-3 cùng beat) + alternates + shot thở + entity route
  + chart/graphic: **không soi** (đúng nguyên tắc top-pick, giữ chi phí).
- Budget cứng **2 verdict/beat**. Ứng viên kế bị tải hỏng (4.7) → thử tiếp không tốn budget.
- Ứng viên bị gate từ chối: KHÔNG vào `used_in_video`/ledger C8 (file đã tải nằm lại
  `assets/` — thành alternate cho editor). Nếu 2-fail phải quay về nó → lúc đó mới ghi sổ.
- Pool 1 ứng viên (auto-pick PA-3): vẫn soi — fail thì không có ai thay, ra warning cho editor.

### 2b. Module mới `ranker/visiongate.py`

- **Schema Pydantic** (NT4 — validator cho mọi output LLM):
  ```
  subject_match: yes | no | unsure
  mood_match:    yes | no | unsure
  seen:   1 câu GLM tả frame THẬT SỰ có gì
  reason: 1 câu ngắn vì sao khớp/không
  ```
- **Prompt** đưa cho GLM: frame + beat text + visual_concept + mood + central_subject +
  video_subject + **description mà tag ĐANG TỰ NHẬN** (để GLM đối chất "chữ nói X, hình là Y").
  Luật trả lời: chỉ "no" khi **rõ ràng khác chủ thể/thực thể/bối cảnh**; nghi ngờ → "unsure".
- **Tái dùng nguyên bộ đồ nghề vision.py** (không viết lại): `glm_api_keys` · `extract_frames`
  (video, 1 frame giữa) · `image_to_jpeg` (ảnh) · `shrink_for_api` 960px · pattern `_post`
  native api.z.ai + thinking disabled + chống schema-echo (example instance) + feedback-retry
  khi JSON sai (đủ bộ bài học PB3/PB4/[[glm-46v-tag-lessons]]).
- Thiếu `GLM_API_KEY` → gate tự tắt cả stage + 1 warning duy nhất (hành vi cũ nguyên vẹn).

### 2c. Log + report (nuôi quyết định trúng/oan của user)

- `BeatRankResult` thêm field `vision_gate: list[dict]` — mỗi lần soi ghi
  `(asset_key, subject_match, mood_match, seen, action)`; tự persist vào `rank_log`
  trong project.json (đường sẵn có, NT5).
- Warning tổng kết stage kiểu phễu: `C5 gate: soi N · pass X · demote-đổi-pick Y ·
  2-fail-giữ-warning Z · mood-warning M · lỗi-fail-open E`.
- Report.html: card "C5 vision gate" liệt kê beat bị demote/warning kèm câu `seen` —
  editor nhảy đúng chỗ soát; user dùng chính bảng này phán trúng/oan để quyết nâng/hạ quyền.

---

## 3. Chi phí + thời gian (tính trên SP012 10', ~95 beat qua phễu)

| Khoản | Ước tính |
|---|---|
| Call GLM | ~95 lead + ~10-15% demote retry ≈ **105-110 call/video** |
| Tiền | × $0.00093/call (1 frame 960px, đo thật PB6) ≈ **~$0.10/video** |
| Thời gian | tuần tự trong vòng pick (không song song được — demote đổi pick ảnh hưởng P7/ledger beat sau), ~3-6s/call trên api.z.ai → **+5-10 phút/video** |

Video sau KHÔNG rẻ hơn (gate hỏi theo cặp frame×beat, không cache theo asset được như M3b).

## 4. RÀ CHỒNG CHÉO (P5) — "mood" đã 4 tầng, "chủ thể" đã 4 tầng, C5 là tầng thứ 5 của CẢ HAI

| Tầng cùng quản | Ngược chiều? | Ai lật ai? |
|---|---|---|
| **Chủ thể — 4 tầng chữ:** query NÃO (direct) · AND-match tag kho/Pexels · NÃO phễu veto `thuc_the_sai` V3 · C6 drop-list query | Không — cùng chiều, khác bằng chứng (chữ vs ảnh) | C5 **được phép lật pick phễu** (demote 1 lần — chủ đích, user chốt V123 §3c). Không tầng nào lật lại C5 vì nó đứng CUỐI, ngay trước ghi sổ |
| **Mood — 4 tầng:** NÃO đặt mood beat · phễu `diem_mood` ×2.5 · C3 so màu warning · C4 tone video | Nguy cơ chồng cao nhất → đợt này mood **warning-only, KHÔNG đụng điểm/pick** | Không ai lật ai — warning chỉ cộng thêm thông tin cho editor |
| Sàn 3 + kill-log phễu ([[filter-overload-guard]]) | C5 KHÔNG phải cửa loại thứ 3: không loại ai khỏi pool, không đổi kill-log phễu, chỉ đổi thứ tự tiêu thụ trong vòng tải + bounded 1 retry + luôn có pick | — |
| P7 chống lặp + C8 ledger viral | Vòng lặp hiện có đã re-check từng ứng viên trước khi nhận → demote sang ứng viên kế đi qua đúng cửa cũ; ứng viên bị gate chê không ghi sổ oan | — |
| M3b `stock_tags` (vision tag pick stock SAU source) | Không đụng: M3b chạy sau khi picks chốt, tag pick CUỐI CÙNG (sau demote) — còn tiết kiệm hơn vì không tag asset bị loại | — |
| Shot thở / entity route / chart / assembler / cutter | Không đi qua `_pick_by_funnel` hoặc không phải footage → gate không chạm | — |
| Cùng-pattern cần quét khi code (P5): 2 chỗ `_materialize`-rồi-nhận (đường phễu + đường heuristic không-brain) | Đường heuristic Phase 0 (không brain) KHÔNG gắn gate — gate cần beat concept từ NÃO; ghi rõ trong code | — |

**Ca không-ground-truth kiểu b68 (Destiny):** chính là ca C5 sinh ra để bắt — chữ sạch,
hình sai; chỉ frame thật mới lộ.

## 5. Hai quyết định đi kèm (chốt trong đợt này, ghi từ roadmap)

1. **Phạm vi soi — ✅ USER CHỐT 2026-07-10: PA-A, soi lead-pick MỌI beat qua phễu**
   (local + Pexels) — phủ cả 3 lớp ca đã thấy (b60 kho, b68 kho, "đỏ rực không chữ mars"
   stock). ~$0.10 + 5-10'/video. (PA-B chỉ-kho-local bị loại vì bỏ lọt lớp stock 3c.)
2. **C3 quyền-trừ-điểm — ✅ USER CHỐT 2026-07-10: ĐÓNG, giữ warning-only vĩnh viễn.** User đã 2 lần phán
   "không quan trọng lắm, editor thấy lệch tự thay" (V2 + V3). Không code gì; xóa khỏi backlog.
   (Mood-warning của C5 nếu sau này được nâng quyền sẽ gánh đúng vai này, có mắt vision xịn hơn so-màu.)

**KHÔNG làm đợt này (chống phình — filter-overload-guard):** đưa slug nguồn (`source_video`)
vào prompt NÃO phễu (lỗ §C6-DIEU-TRA). Lý do: slug kiểu "Bigbang"/"Solar System" không tả
nội dung từng cảnh → NÃO dễ veto oan theo nguồn; C5 nhìn frame thật là bằng chứng mạnh hơn
slug. Nếu video kiểm V4 vẫn lộ ca slug-tiết-lộ mà gate trượt → mở lại, làm riêng.

## 6. Milestones (P4 — từng bước, mỗi bước test + chờ xác nhận)

| # | Nội dung | Cổng |
|---|---|---|
| M1 | `ranker/visiongate.py`: schema + prompt + client GLM (stub `_post` test được) | pytest unit: parse verdict · unsure→pass · lỗi API→None · feedback-retry schema |
| M2 | Cắm vào `_pick_by_funnel` + log `vision_gate` + warning tổng + card report | pytest tích hợp: pass-giữ-pick · fail-demote-đổi-pick · 2-fail-giữ-#1+warning · mood-chỉ-warning · pool-1-fail-warning · ledger/P7 không ghi sổ oan · thiếu key = hành vi cũ. FULL suite. Commit mốc |
| M3 | **Video kiểm đợt 5:** SP012 re-source cùng input → draft **V11** (không đè V10, NT5). So picks với V10 (picks đứng từ V3) | **Cổng MẮT:** user phán từng demote/warning trúng hay oan (→ quyết nâng mood lên demote hay giữ). **CỔNG TAI đi ké:** 17 nhạc editor + ocean ×10 mới nạp pool lần đầu chạy thật |

Sau M3 đạt: cập nhật NHAT_KY + memory + backup D: → **HẾT NHÓM C** → sang nhóm B (Level 1 batch).
