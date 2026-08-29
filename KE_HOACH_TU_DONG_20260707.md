# KẾ HOẠCH TỰ ĐỘNG 4H — 2026-07-07 (user vắng 2–4h, duyệt sau)

> **Bối cảnh:** user đi việc khác 2–4h, cho phép Claude Code tự chạy các bước KHÔNG cần
> duyệt trước (cổng pytest) hoặc duyệt-sau-được (artifact để sẵn). User sẽ clear chat để
> đỡ tràn token — **phiên mới đọc file này + NHAT_KY_BUILD.md để làm tiếp.**
> Cách resume: mở file này, tìm block đầu tiên chưa ✅, đọc mục "còn lại" của block đó.

## LUẬT KHÔNG ĐƯỢC PHÁ (kể cả khi tự động)
- KHÔNG tự báo đạt cổng mắt — chỉ để sẵn artifact, user phán khi quay lại.
- KHÔNG git. KHÔNG đụng draft CapCut nguồn (đọc-only). KHÔNG nạp niche khác ngoài space.
- KHÔNG gọi API tốn tiền hàng loạt (chỉ cho phép ≤2 call vision lẻ cho clip aliens).
- Mỗi block xong: cập nhật trạng thái ở đây + entry NHAT_KY nếu là code/fix.

## CÁC BLOCK (làm tuần tự, block sau không phụ thuộc block trước trừ khi ghi rõ)

### Block 1 — PB7: vá duration local candidate → phễu c5 (CODE, cổng pytest, duyệt sau)
Trạng thái: ✅ XONG (pytest 233/233, 2 regression mới; NHAT_KY §PB7 đã ghi — chờ user duyệt sau)
- Bug thật đã tìm ra hôm nay: `sourcer/local.py::_row_to_candidate` KHÔNG mang `duration`
  từ db vào ứng viên → cửa kỹ thuật phễu (loại clip ngắn hơn beat × ratio, `funnel.py`)
  + điểm may duration-fit MÙ với footage local; Pexels thì có duration.
- Bẫy phải né: asset cũ (PB3, trước migrate) có duration=0/NULL → nếu truyền 0 thẳng,
  cửa kỹ thuật sẽ LOẠI OAN mọi asset cũ (0 < mọi beat_dur). Chỉ gắn key khi duration > 0.
- Việc: rà vùng ảnh hưởng (P5: mọi consumer của candidate dict) → sửa `_row_to_candidate`
  → ≥2 regression test (có duration / duration=0 không bị loại oan) → FULL pytest → NHAT_KY §PB7.

### Block 2 — PB8: báo cáo khớp query↔tag kho space (PHÂN TÍCH read-only, 0 token)
Trạng thái: ✅ XONG — `PB8_KHOP_QUERY_TAG.txt`: 16/24 query trúng qua phễu thật; 8 trượt
chia 2 loại (kho thiếu cảnh thật = Pexels vớt, OK · từ chuyển-động "rotating/timelapse"
AND-trượt oan vì GLM tag frame tĩnh → bài học prompt director, KHÔNG sửa code)
- Mục tiêu: de-risk bước "dựng video space end-to-end" — kiểm tra query kiểu director
  (tier specific tiếng Anh) có TÌM THẤY 236 cảnh nạp không.
- Việc: script scratchpad — (a) thống kê vocab subject/tags/scene_type trong db space;
  (b) chạy ~20 query giả lập kiểu director qua `find_local_candidates` → hit-rate,
  query nào 0 kết quả, vì sao; (c) xuất `PB8_KHOP_QUERY_TAG.txt` cho user đọc khi về.
- KHÔNG sửa code production ở block này — chỉ đo + báo cáo.

### Block 3 — Việc vặt còn ngỏ PB4: tag clip aliens bị contentFilter (≤2 call vision lẻ)
Trạng thái: ✅ XONG — kho nạp **237/237 trọn**. Engine claude bị 401 (⚠ **key ANTHROPIC
trong `.env` HẾT HẠN** — báo user, không tự thay) → chuyển tag TAY: Claude Code nhìn frame
giữa clip bằng mắt mình, đưa AssetTags qua đúng ống `ingest_draft` (pydantic validate,
đủ truy vết has_voice=1 · scene_index=49 · duration 6,9s). NHAT_KY §PB4 còn-ngỏ (1) đã đóng.

### Block 4 — NHÁP mô tả vận hành consumer DNA đầu tiên: d1 pacing validator (DOC, chờ duyệt)
Trạng thái: ✅ XONG — `MO_TA_VAN_HANH_DNA_D1.md` (NHÁP): 2 mảnh (A nạp DNA vào
direct-context L2b sâu · B pacing validator chỉ-cảnh-báo) + dna.json + rà chồng chéo 5 tầng
(tìm ra 1 mâu thuẫn thật: heuristic "hook nhanh" vs DNA space hook shot DÀI HƠN 8,75s) +
4 câu hỏi chốt cho user. KHÔNG code.

### Block 5 — Chốt sổ cuối phiên
Trạng thái: ✅ XONG — mọi block cập nhật; NHAT_KY thêm dòng PB7 + PB8; báo cáo dưới đây.

## ĐỢT NẠP 2 — PB9 (user gom thêm 2 draft, giao 2026-07-07: "lập luôn kế hoạch để chạy")

Nguồn mới trong `E:\PROJECT NHAN BAN\SPACE 1`: **SP1 - 001** (dry-run: 125 cảnh, nguồn gốc
thiếu 142/278 file khi gom — chỉ nạp được phần có mặt; DNA pacing vẫn ĐỦ vì read_timeline
đọc draft_content.json không cần file) · **SP1 - 004** (dry-run: 257 cảnh, đủ file).
Tổng 382 cảnh ≈ ~2h máy + ~$0,4 GLM (luật 1-frame PB6).

- [x] B9.1 ✅ SP1-001: 125/125 vào db (phiên trước cắt sẵn 125 clip; phát hiện job nền
      phiên cũ CÒN SỐNG chạy đôi — db không hỏng nhờ UNIQUE path + resume; memory
      `leftover-background-job-check`)
- [x] B9.2 ✅ SP1-004: 257/257 vào db (cắt mới 257, tag 240 + vớt 15 + 2 tay)
- [x] B9.3 ✅ 2 pass vớt + 3 cảnh lì (SSLEOF dai/validation) tag TAY qua ống production
      (tiền lệ PB4 aliens): rush-hour NYC · Sun_nohw 9 · electricity-substation.
      **Kho space TRỌN 665 asset.**
- [x] B9.4 ✅ `PB9_DNA_SPACE_3DRAFT.txt` (giữ PB5 1-draft để so) + **dna.json tự sinh**
      (code DNA-d1 đợt 1 mới — xem NHAT_KY §DNA-D1.B)
- [x] B9.5 ✅ NHAT_KY §PB9; so DNA: cut/phút + trung vị ô thở ỔN ĐỊNH · wide 79→59% +
      close-up 1/39→1/8.3 đổi mạnh · **hook ĐẢO CHIỀU** (8.75s n=6 → 4.8s n=25, mâu thuẫn
      MO_TA §3 tự tan) · lệch chuẩn shot từng VỠ 3.11→32.94s vì mega-segment 839s →
      **USER CHỐT 2026-07-07: shot >30s bỏ qua không đếm, mọi niche** — đã code
      (`MEGA_SHOT_S`, đếm riêng, regression test, 240/240) + chạy lại artifact/dna.json:
      **std 3,09s · 9,4 cut/phút** (sạch, validator hết kêu oan).

## VIỆC KHÔNG LÀM (chờ user, ghi để phiên sau khỏi tự ý)
- ~~Nạp thêm draft space: CHẶN~~ → MỞ 2026-07-07: user gom SP1-001 + SP1-004, đang chạy PB9.
- Dựng video space end-to-end: CHẶN — cần script + voice space từ user.
- Nối số DNA vào code (d1/d2/c6/b1): CHẶN — DNA n=1 + mô tả chưa duyệt.

## BÁO CÁO CHO USER (phiên tự động kết thúc ~1,5h — 4/4 block xong, không còn việc an toàn để tự làm tiếp)

**Đã làm (không đụng luật nào):**
1. **PB7 — vá bug duration** (`sourcer/local.py`): ứng viên local giờ mang duration vào
   phễu c5 (cửa clip-quá-ngắn + điểm khớp-độ-dài hết mù). Né bẫy loại-oan asset cũ
   (duration=0 → không gắn key). pytest **233/233** (2 regression mới). → **anh duyệt sau**.
2. **PB8 — đo khớp query↔tag** (0 token): 16/24 query director giả lập trúng kho nạp qua
   phễu thật. 8 trượt: kho thiếu cảnh thật (OK, Pexels vớt) + từ chuyển-động AND-trượt oan
   (GLM tag frame tĩnh) → bài học prompt director. → **anh đọc `PB8_KHOP_QUERY_TAG.txt`**.
3. **Kho nạp 237/237 TRỌN**: clip aliens (contentFilter GLM) đã tag TAY — Claude nhìn frame
   giữa clip, đưa tag qua đúng ống production, đủ truy vết. → anh có thể soi bằng
   `library-search space aliens`.
4. **Nháp mô tả consumer DNA đầu tiên**: `MO_TA_VAN_HANH_DNA_D1.md` — chưa code, chờ anh
   duyệt + trả lời 4 câu hỏi cuối file (quan trọng nhất: DNA niche vênh heuristic chung
   thì bên nào thắng).

**⚠ ANTHROPIC_API_KEY hết hạn (401):** user chốt 2026-07-07 "**chưa cần dùng tới**" —
không thay, không nhắc lại; engine vision claude coi như tắt tới khi user tự đổi ý.

**Chờ anh quyết khi quay lại:** duyệt PB7 · đọc PB8 · duyệt/chỉnh MO_TA_VAN_HANH_DNA_D1 ·
gom thêm draft space (đường găng — mọi bước DNA đợi ≥3 draft) · thay ANTHROPIC_API_KEY (tùy).
