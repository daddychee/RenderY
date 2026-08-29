# MÔ TẢ VẬN HÀNH — CỔNG CHAPTER YOUTUBE + TCF MODE FILE NGUỒN (user duyệt 2026-07-13)

> Bối cảnh: user phát hiện video mẫu/viral tải về nhiều khi bị editor CẮT BỎ đoạn →
> không khớp bản YouTube → chapter yt-dlp map theo giây file nguồn bị TRƯỢT MỐC
> (section_hint sai cho mọi cảnh sau điểm cắt). Cờ điểm nhô ĐÃ có cổng duration
> (ytpeaks §3d) nhưng chapter thì CHƯA — cùng bệnh, khác consumer (P5 anh em của bug).
> User hỏi "thay hẳn bằng tcf-gen?" → chốt: KHÔNG thay hẳn (chapter tác giả = ground
> truth ngữ nghĩa tốt khi file khớp), mà GATE + FALLBACK.

## 1. Hành vi mới (chỉ nhánh viral/mẫu của ingest — own KHÔNG đổi)

| Tầng | Trước | Sau |
|---|---|---|
| Title | yt-dlp | GIỮ NGUYÊN (title không phụ thuộc timeline — editor cắt kiểu gì cũng đúng) |
| Cờ điểm nhô | gate duration >3% (§3d) | GIỮ NGUYÊN |
| Chapter YouTube | dùng mù theo giây file | **qua CÙNG cổng duration**: file lệch YouTube >3% (hoặc thiếu số đối chiếu) → chapter = RÁC, bỏ + warning |
| Fallback chapter | file bối cảnh editor (ctx) | ctx GIỮ; hết ctx → **tcf-gen mode FILE NGUỒN**: transcribe voice của CHÍNH file mẫu → NÃO chia chapter theo giây FILE THẬT (không bao giờ trượt) |

Ưu tiên chapter mới: **yt-dlp (chỉ khi duration khớp) → file bối cảnh editor → tcf-gen
file nguồn**. (Thứ tự yt↔ctx giữ nguyên như code §3i-2 hiện hành — chỉ THÊM cổng + đuôi.)

## 2. tcf-gen mode FILE NGUỒN (`tcf_gen.source_chapters`)

- Transcribe CẢ file media (faster-whisper small, `language="en"` — voice mẫu các niche
  đều tiếng Anh; cần khác thì mở param sau) → block ~45s theo GIÂY FILE → 1 call NÃO
  (Sonnet, cùng SYSTEM/schema/snap NT4 với tcf-gen own — mốc phải nằm trong danh sách).
- Trả `[{start_time, end_time, title}]` — ĐÚNG khuôn `YTVideoInfo.chapters` để
  `_chapter_at` đọc thẳng, không thêm đường parse mới.
- **Cache 2 tầng bền** trong `<niche>/pause_scan_cache/`: `SRC__<file>.words.json`
  (transcribe) + `SRC__<file>.tcf.json` (kết quả NÃO) → re-ingest/retag 0 call, 0 transcribe.
- Video ít lời (<200 từ — nhạc không lời): raise → caller fail-open, hint "" như cũ.

## 3. Rà chồng chéo (P5)

- **Cờ điểm nhô:** cùng hàm `duration_mismatch` nhưng 2 cổng ĐỘC LẬP (peak gate ở
  `apply_viral_rules`, chapter gate ở `ingest_draft`) — không đụng logic peak.
- **Nhánh own:** không đụng — chapter own theo TIMELINE draft (file editor / tcf-gen own).
- **`--retag`:** chạy lại ăn hint mới → hồi tố được cho mẻ đã nạp sai (nếu cần).
- **Cache key:** prefix `SRC__` tách khỏi key draft `label__` của pause-dna — không đè.
- **Fail-open toàn tầng:** yt-dlp lỗi / transcribe lỗi / NÃO lỗi / ít lời → hint "" (tag
  mù đoạn như trước 2026-07-11), mẻ nạp không chặn — y văn hóa ytref §3c.
- **Chi phí:** 1 lần/video mẫu (~9,3s transcribe/phút video + 1 call NÃO); chỉ tốn khi
  chapter yt KHÔNG dùng được VÀ không có file bối cảnh editor.
- **Consumer `info.chapters`:** chỉ 2 chỗ — `ingest_draft` (gate ở đây) + dry-run echo
  cli (thêm dòng cảnh báo trượt). Không còn chỗ nào khác (đã grep).
- **NÃO trong ingest:** client tạo LƯỜI (chỉ khi thật sự cần sinh) — mẻ nạp bình thường
  (yt khớp/có ctx) không import claude/whisper.

## 4. Số 🔸

`DUR_TOL = 3%` (dùng chung số §3d đã chốt — 1 nguồn số, không đẻ hằng mới) ·
`BLOCK_S = 45s` / `MIN_WORDS = 200` (dùng chung tcf-gen own) · model NÃO: sonnet.
