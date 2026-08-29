# MÔ TẢ VẬN HÀNH — GÓI TĂNG TỐC TOC-1..4 (source + đo giờ, 2026-07-15)

> **TRẠNG THÁI: code đóng, pytest 526/526 — CHỜ VIDEO KIỂM số thật.** User giao tự
> quyết 2026-07-15 với 2 ràng buộc: (1) KHÔNG ảnh hưởng nhiều chất lượng chọn footage,
> (2) bước đơn giản dùng sonnet cho rẻ. Nguyên tắc thiết kế: **chỉ tối ưu ỐNG DẪN
> (token, song song, cache) — logic chấm/veto/sàn/điểm máy KHÔNG đụng 1 dòng.**

## 0. Số đo dẫn tới quyết định (NHAT_KY_TOC_DO.md, 3 bài thật)

| Bài | source | call NÃO batch | token out NÃO | pexels tải |
|---|---:|---:|---:|---:|
| SP1-017 (kho mỏng) | 18.556s (84%) | 57 | 698k (12,3k/call) | 209 |
| DS5-083 (kho dày) | 7.032s (49%) | 43 | 441k (10,3k/call) | 147 |
| DS3-084 | — | 46 | 180k | 111 |

Ở ~80 tok/s, riêng NÃO **viết output** ≈ 78% source của DS5-083. Thủ phạm output phình:
prompt bắt `id = asset_key EXACTLY` mà asset_key kho local = nguyên path F:\ dài tới
**165 ký tự** (tb 40–66) — NÃO chép lại trong TỪNG verdict = 50–65% output token.

## 1. Bốn thay đổi

**TOC-1 — id ngắn trong hội thoại NÃO** (`prompts.alias_of/build_alias_maps` +
`funnel` dịch ngược): ứng viên vào prompt mang mã `a`+crc32-8hex thay asset_key;
verdict trả mã → funnel dịch về asset_key. Cùng asset ⇒ cùng mã ở mọi beat/mọi call
(NÃO vẫn thấy asset lặp giữa beat trong batch — tín hiệu "same asset" không mất).
Mã lạ/nguyên văn asset_key → giữ nguyên, rơi nhánh "NÃO bỏ sót" trung tính (fail-open
sẵn có). Đụng độ crc32 → ứng viên sau dùng nguyên asset_key làm id (đúng, chỉ dài).
Schema `CandidateVerdict.id` mang description để NÃO chép đúng mã. **Ước giảm 50–65%
output token/call + input gọn** → thời gian NÃO gần nửa.

**TOC-2 — 3 call NÃO batch bay song song** (`_plan_chunks` chia sẵn chunk tĩnh y luật
PA-1 + `_pump_rank` lookahead + `_resolve_rank`): gather ứng viên vẫn MAIN thread
(sqlite + used_in_video không thread-safe), worker CHỈ chạy `rank_batch` (thuần +
subprocess claude). Knob `AUTOEDIT_RANK_PARALLEL` (mặc định 3; =1 = tuần tự như cũ —
tắt nhanh khi subscription nghẽn). Batch lỗi → warning + rơi về 1 call/beat (lưới cũ).
`cc_client._log` thêm lock (2 thread cùng đếm → đè file log). **Wall NÃO ÷~3.**

**TOC-3 — normalize NỀN ngay trong source** (`_Prenorm`, 2 worker ffmpeg, knob
`AUTOEDIT_PRENORM=0` tắt): footage vừa nằm xuống `assets/` → transcode nền vào
`media/norm/<tên>` — ĐÚNG path assemble tìm, `transcode.py` mtime-skip ăn sẵn, draft
không đổi 1 bit. Ghi `part_<tên>` rồi `os.replace` — crash giữa chừng KHÔNG để file
norm cụt mang mtime hợp lệ (assemble sẽ nuốt file cụt nếu ghi thẳng). Lỗi → đếm + bỏ,
assemble tự normalize lại (fail-open). KHÔNG đụng chart PiP/info-card (chúng normalize
`crop_16x9=False` riêng — crop nhầm card dọc là vỡ layout). **Assemble ~20′ → vài phút.**

**TOC-3b — tải Pexels song song kiểu WARM-UP** (user chốt "làm luôn" 2026-07-15, .env
có 10 key Pexels; `_DlPool` 4 luồng, knob `AUTOEDIT_DL_PARALLEL=0` tắt): chunk vừa có
verdict NÃO → tải TRƯỚC ứng viên top-điểm-NÃO-thuần của từng beat (`_prefetch_plan`:
chỉ stock có url; né veto/đã-dùng/ledger tại lúc lập kế hoạch) vào ĐÚNG tên file đích
(`_stock_dest` — tách chung với `_materialize`). Vòng pick giữ NGUYÊN thứ tự/luật:
`_TimedStock.download` có KHÓA THEO ĐÍCH + tái dùng file đã nằm sẵn ffprobe đọc được;
file cụt → ffprobe None → tải lại. **PICK KHÔNG ĐỔI** — warm-up trượt (điểm máy ±2.5
lật top-1, P7 lấy mất...) chỉ phí 1 file mồ côi trong assets/, đường inline tự tải.
Lỗi warm-up nuốt êm — inline gánh (fallback 4.7 nguyên vẹn).

**TOC-4 — đo giờ tự động** (`StageRecord.running()` 9 stage + `record.perf` source):
`started_at` mọi stage; source ghi `rank_calls/rank_call_s/rank_wait_s/pexels_search_s/
downloads/download_s/prenorm_n/prenorm_s/stage_s` → NHAT_KY_TOC_DO hết bấm giờ tay.

**Model (yêu cầu user):** toàn CLI đã sonnet sẵn (`--rank-model`/`--director-model`
mặc định `claude-sonnet-4-6`) — không chỗ nào opus. Chỗ duy nhất chạy model phiên đắt
= fan-out agent đạo diễn → SKILL.md ghim `model: "sonnet"` khi spawn (khớp CLAUDE.md §5).

## 2. Rà chồng chéo (P5)

- **P7 chống lặp + gate pháp lý C8 (viral):** lookahead làm pool gather cũ đi ≤3 chunk
  — nhưng CẢ HAI luật vốn re-check TẠI PICK từ thời PA-1 (`used_in_video` skip +
  `ledger.blocks`) → **không thủng**; tệ nhất NÃO chấm vài ứng viên đã bị lấy (phí điểm,
  không sai luật).
- **Mạch c3 (Kuleshov):** TRONG chunk không đổi (NÃO tự chain như cũ). Ranh chunk:
  `prev_pick_note` cũ đi 1–2 chunk khi lookahead — chấp nhận, cùng bản chất xấp xỉ
  "NÃO đoán top-pick ≠ pick thật" đã có từ PA-1. Đây là chỗ DUY NHẤT chất lượng có thể
  lệch → soi ở video kiểm.
- **C5 vision gate / sàn niche / shot thở / M3b:** chạy tuần tự main thread như cũ,
  không đụng.
- **Phễu chấm điểm:** bất biến "batch vs per-beat cùng verdict = cùng kết quả" có
  regression test giữ; TOC-1 chỉ đổi TÊN GỌI ứng viên trong hội thoại, không đổi điểm.
- **Assemble:** đọc `media/norm` như cũ (mtime-skip có sẵn từ 6.6) — prenorm chỉ làm
  SỚM việc assemble sẽ làm, cùng hàm `normalize_video/normalize_image`, cùng tên file.
- **Resume/chạy lại source:** pick mới → file assets mới (mtime mới) → prenorm làm lại
  đúng file đó; file norm mồ côi vô hại (assemble chỉ tra tên chính xác).

## 3. Dự đoán (kiểm ở video tiếp theo, số perf tự ghi)

- DS5-083-cỡ (270 beat, kho dày): source 117′ → **~25–35′**, assemble 20′ → **~5–8′**.
- SP1-017-cỡ (324 beat, kho mỏng): source 5h09′ → **~40–55′** (TOC-3b gánh phần tải).
- (TOC-3b đã làm luôn cùng đợt — user chốt 2026-07-15, hết mục còn ngỏ tải song song.)

## 4. Cách kiểm sau video thật

`project.json → stages.source.perf` + `started_at/completed_at` từng stage. So:
`rank_call_s` tổng vs bài cũ (~5.500s DS5) · `rank_wait_s` (phải NHỎ hơn hẳn
`rank_call_s` = lookahead ăn) · `dl_reuse` vs `downloads` (tỉ lệ warm-up trúng —
kỳ vọng ≥60–70%) · warning "TOC-3 normalize nền: N asset" · thời gian assemble.
Token out call rank: kỳ vọng 10,3k → ~4–5k/call.

## 5. Rà chồng chéo bổ sung TOC-3b

- **Thứ tự fallback 4.7 (tải hỏng → ứng viên kế):** nguyên vẹn — warm-up lỗi nuốt êm,
  vòng pick inline tự tải + tự rơi ứng viên kế y cũ.
- **P7/ledger:** warm-up chỉ TẢI file, không ghi used/ledger — ghi sổ vẫn chỉ ở pick.
- **Khóa theo đích:** vòng pick đụng file warm-up đang tải dở → CHỜ khóa (không bao giờ
  2 luồng ghi 1 file); file cụt từ crash → ffprobe None → tải lại.
- **Resume:** file assets/ cũ hợp lệ giờ được TÁI DÙNG thay vì tải lại (đổi hành vi
  có chủ đích — nhanh hơn, cùng nội dung vì tên file khóa theo asset_key+beat).
- **10 key Pexels:** tải là link CDN trực tiếp không ăn quota search; 4 luồng an toàn.
