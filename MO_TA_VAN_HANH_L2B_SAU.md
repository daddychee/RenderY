# MÔ TẢ VẬN HÀNH — L2b SÂU: ĐẠO DIỄN ĐỌC BỘ FOUNDATION THAY PROMPT CỨNG

> **Tài liệu CỔNG DUYỆT VẬN HÀNH** (2026-07-04). User đọc → duyệt → mới code.
> Đây là **bước 3 của lộ trình 5 bước đã chốt ở §F0**: foundation viết xong (18/18) →
> nối vào NÃO. Mục tiêu: bước `direct` không chạy bằng prompt cứng của autoedit nữa,
> mà do **Claude Code phiên sống** (trong buồng lái `/dung-video`) đọc bộ foundation +
> transcript rồi TỰ đạo diễn — editor góp ý trực tiếp từng beat bằng hội thoại.

---

## 1. Hiện tại vs sau khi làm

**Hiện tại (L2b nông):** bước `direct` gọi Claude qua subprocess với prompt cứng
(`director/prompts.py` — ~450 dòng luật tiếng Anh viết từ FOUNDATION.md cũ). Editor muốn
chỉnh phải nói qua `brief` → chạy lại direct CẢ video → chờ → xem lại. Foundation 18 file
vừa viết KHÔNG ai tiêu thụ.

**Sau khi làm (L2b sâu):** trong `/dung-video`, chính phiên Claude Code đọc bộ foundation
+ transcript → tự viết outline + beats → nộp cho ỐNG kiểm và ghi sổ. Editor chỉnh kiểu
"beat 5 đổi concept sang chợ đêm" → phiên sửa ĐÚNG beat đó → nộp lại. Không re-run cả video.

**Cái KHÔNG đổi (NT4 + P3):** phiên sống chỉ trả **word index + concept** — timestamp
vẫn do ỐNG tính, toàn bộ validator hiện có vẫn gác y nguyên. Đường `autoedit direct` cũ
GIỮ NGUYÊN làm đường nhanh/fallback (và là xương của Level 1 sau này).

## 2. Ba mảnh vận hành

```
ỐNG xuất ngữ cảnh ──► NÃO phiên sống đạo diễn ──► ỐNG nhận + gác + ghi sổ
 (direct-context)       (đọc foundation, viết JSON)      (direct-ingest)
```

### Mảnh 1 — `autoedit direct-context <project_dir>` (ỐNG, lệnh mới nhỏ)

Sau `align`, lệnh này ghi `direct_context.md` vào folder project:
- Transcript dạng **từ đánh số `[i]word`** (0-based, đúng format prompt cũ dùng) + tổng
  thời lượng voice + brief/channel editor đã khai.
- **BẢNG RÀNG BUỘC CỨNG** — in tự động TỪ HẰNG SỐ CODE (không chép tay, không trôi lệch):
  beat 1.5–10s · thở 0 hoặc 1.5–6s, chỉ tại từ kết câu có nghỉ thật ≥0.3s · query ≤4 từ ·
  hook phải có ≥1 thở, không 2 thở liền · ≤2 chart + ≤2 card/chương · overlay ≤20 ký tự
  (gõ máy ≤24) · shot con ≥0.7s. Đây là chốt chống vênh **Ý vs SỐ** (xem §4b).
- Vì sao cần: phiên đọc thẳng `project.json` sẽ ngốn context (mỗi từ kèm timestamp);
  file này gọn, và word index là "hệ tọa độ" duy nhất NÃO được phép dùng (NT4).

### Mảnh 2 — NÃO = phiên sống đạo diễn (skill `/dung-video` cập nhật, KHÔNG code Python)

Pha 1 của skill đổi thành:
1. Đọc **12 file foundation nhóm đạo diễn** (1 lần mỗi phiên làm việc, không phải mỗi video):
   `a1` chia beat · `a2` chức năng đoạn · `a3` open loop · `b1` mood&tone · `b3` pattern
   interrupt · `c1` phân tuyến nguồn · `c2` ẩn dụ+veto · `c4` từ khóa tìm · `d1` pacing ·
   `d2` hình thở · `d3` loại cắt · `f1` text/typo.
   **KHÔNG đọc 6 file còn lại** (`c3/c5/c6/c7` = luật phễu source ĐÃ CODE trong ranker;
   `e1` ducking/nhạc đã code trong ống; `f2` đang treo) — tránh loạn [[filter-overload-guard]].
2. Đọc `direct_context.md` → đạo diễn **từng chương một** (như 2 pass cũ: outline trước,
   beat sau) → viết ra file `director_draft.json` trong folder project.
3. Format file = ĐÚNG schema hiện có (`director/schema.py`, không sửa):
   ```json
   { "outline": { tone, motifs, chapters: [...] },
     "chapters": [ { "chapter_id": 1, "beats": [ ...BeatDraft như cũ... ] } ] }
   ```
4. **Foundation quản Ý — bảng ràng buộc quản SỐ** (luật chống vênh, rút từ rà soát §4b):
   foundation nói "số chỉ là ví dụ" (đúng — user chốt ở F1), nhưng máy gác bằng số cứng.
   Phiên TUÂN SỐ trong bảng của `direct_context.md`; foundation chỉ định hướng nghĩa/nhịp.
   Hai chỗ dễ vênh nhất, skill sẽ ghi tường minh:
   - Muốn nhịp cắt NHANH → dùng `shot_count` 2–3, **KHÔNG đẻ beat <1.5s** (máy sẽ gộp lại
     → ý đồ pacing mất).
   - Hình thở: schema hiện tại = **1 số** `breathing_after_sec`; luật 2-pha [min–max] của
     d2 **CHƯA code** — đừng làm theo phần đó. Chỉ đặt thở ở từ kết câu có nghỉ thật.

### Mảnh 3 — `autoedit direct-ingest <project_dir>` (ỐNG, lệnh mới — người gác cổng)

Đọc `director_draft.json` rồi chạy **nguyên battery kiểm tra của direct cũ, không viết
luật mới**:
1. Pydantic parse (schema y hệt đường cũ).
2. Validator: coverage từ-không-hở-không-đè · beat quá dài · luật v2 · overlay/graphic/
   info-card/text-sequence hợp lệ. **Thêm 1 kiểm tra nâng cấp:** hình thở đặt ở chỗ voice
   KHÔNG nghỉ (<0.3s) → trả **LỖI kèm khoảng nghỉ đo được + gợi ý vài từ có nghỉ thật gần
   đó** để phiên đặt lại — thay vì xóa âm thầm như đường cũ (chống nghịch lý "máy ép hook
   có thở rồi máy khác lặng lẽ xóa thở", xem §4b). Nếu cả chương không có chỗ nghỉ nào →
   hạ xuống warning + xóa như cũ (không kẹt vòng lặp).
3. **Có lỗi → in danh sách lỗi + exit ≠ 0, KHÔNG ghi gì.** Phiên sống đọc lỗi, sửa file,
   nộp lại — vòng retry giờ là hội thoại (thay retry máy 1 lần của đường cũ).
4. Pass → hậu xử lý Y HỆT direct cũ (tính timestamp từ word index, gộp beat ngắn, bỏ thở
   rơi chỗ nói liền, kẹp trần visual/chương, warnings) → ghi `project.beats` + `outline`
   + `beats.json`, stage direct = done. Pipeline sau (cut→source→…) chạy như mọi khi,
   **không biết beats đến từ đường nào**.

## 3. Vòng chỉnh của editor (giá trị chính của Level 2)

- Editor xem tóm tắt beat → góp ý bằng lời ("hook thiếu punch", "beat 7 sai chủ thể").
- Phiên đối chiếu foundation liên quan → sửa đúng chỗ trong `director_draft.json` →
  `direct-ingest` lại → tóm tắt diff cho editor ("chỉ beat 7 đổi, còn lại giữ nguyên").
- Chỗ editor sửa + lý do được phiên ghi lại trong hội thoại — sau này Phase B/L1 đóng băng
  các luật đã học từ chính các lần sửa này (trụ 2 của [[level2-first-then-level1]]).

## 4. Chi phí & rủi ro (nói thẳng)

| Điểm | Đánh giá |
|---|---|
| Token | Đọc 12 foundation ≈ 1 lần/phiên làm việc; đạo diễn chạy trong phiên chính (subscription) thay 4 call subprocess. Chấp nhận được cho chế độ HỌC. |
| Phiên đếm word index lệch | Rủi ro thật. Lưới: `direct_context.md` in sẵn `[i]word` + validator coverage CHẶN CỨNG ở ingest — sai là bị trả về, không lọt vào project.json. Dự kiến 1–2 vòng sửa/video là bình thường. |
| Chất lượng so đường cũ | Chưa biết — chính là thứ milestone chạy-thật đo (mục 6). Đường cũ còn nguyên, thua thì lùi không mất gì. |
| Foundation nhiều luật làm phiên loạn | Ràng buộc CỨNG (coverage, trần overlay/graphic, thở-chỗ-lặng) máy gác hết; foundation chỉ là tri thức mềm hướng dẫn Ý. Sai Ý → editor bắt ở cổng duyệt beat như mọi khi. |

## 4b. KẾT QUẢ RÀ CHỒNG CHÉO LOGIC toàn pipeline (2026-07-04, theo yêu cầu user)

Đã rà từng tầng quyết định (prompt/foundation → validator chặn → hậu xử lý âm thầm →
phễu source → assembler) tìm chỗ **2 luật cùng quản 1 thứ mà ngược chiều**. Kết quả:

**✅ Các cụm ĐÃ KIỂM, cùng chiều, KHÔNG sửa:**
- Direct chọn query/concept (c1/c2/c4) rồi phễu chấm lại (c2/c3/c5/c7): trùng nhưng cùng
  hướng — query là phỏng đoán, phễu là trọng tài (đã đóng băng ở c4/c5). Phòng thủ 2 lớp,
  không phải mâu thuẫn.
- Shot variety 2 tầng: validator cảnh báo trên Ý đạo diễn, phễu cộng điểm trên chuỗi THẬT
  — cùng chiều chống lặp, không tầng nào chặn tầng nào.
- Ducking × fade × crossfade nhạc: đã kiểm thật ở F8 (sống chung, 2 track nhận cùng
  envelope). Ngưỡng nở-thở 1.0s < thở hợp lệ 1.5s — nhất quán.
- Mood: nhạc theo mood CHƯƠNG, footage theo mood BEAT — có thể vênh nếu đạo diễn cho beat
  lệch mood chương, nhưng chỉ ở mức "chưa ai kiểm" (backlog b1 Phase B), không phải 2 luật
  đánh nhau. Ghi nhận, chưa làm.

**⚠ 4 chỗ CHỒNG CHÉO THẬT tìm thấy (đúng kiểu user lo — pacing là cụm dày nhất):**

| # | Mâu thuẫn | Hậu quả nếu không sửa | Vá |
|---|---|---|---|
| 1 | **Multi-shot cắt vào Ô THỞ:** cửa sổ phủ beat cuối segment GỒM cả ô thở (`coverage.py`), mà F6 chia đều cửa sổ cho N shot (`assembler.py`) → beat có `shot_count>1` + thở dài sẽ có nhát cắt RƠI GIỮA im lặng — ngược d2 "ô thở = 1 hình giữ" | Chưa nổ (V5 hai beat multi-shot không có thở) — bom hẹn giờ; L2b sâu dùng shot_count nhiều hơn sẽ giẫm | **M0:** chỉ chia phần THOẠI, shot cuối kéo dài phủ trọn ô thở |
| 2 | **Hai tầng thở lật nhau:** validator ÉP hook có ≥1 thở (chặn cứng) NHƯNG `enforce_breathing_pauses` có thể ÂM THẦM xóa đúng cái thở đó (voice không nghỉ ≥0.3s tại vị trí ấy) → hook 0 thở dù luật cứng đòi, không ai báo | Tool "tự quyết rồi tự lật", đúng ví dụ user nêu | **Ingest** (mảnh 3 bước 2): thở-sai-chỗ = LỖI trả về kèm gợi ý chỗ nghỉ thật — phiên sửa có dữ liệu, không bị xóa lén. Đường cũ giữ nguyên (P3) |
| 3 | **Merge beat ngắn VỨT quyết định:** beat <1.5s bị gộp nhưng chỉ giữ metadata beat dài → **overlay/graphic của beat ngắn biến mất im lặng** (punchline "One." kèm overlay "$1M" → overlay bay); gộp-vào-sau còn rơi cả hình thở | Quyết định đạo diễn mất không dấu vết — L2b sâu editor sẽ hỏi "overlay tôi duyệt đâu?" | **M0:** merge cộng dồn overlays (anchor vẫn nằm trong range gộp) + giữ max breathing cả 2 chiều |
| 4 | **Khe hở thở 0<x<1.5s:** thông báo validator nói "0 hoặc 1.5–6" nhưng code cho qua 0.8s → chèn 0.8s im lơ lửng, DƯỚI ngưỡng ducking 1.0s nên nhạc cũng không nở — nửa nạc nửa mỡ | Hiếm nhưng khó hiểu khi xảy ra | **M0:** siết code khớp thông báo — cấm (0, 1.5) |

**Kết luận thiết kế rút ra (áp vào mảnh 1+2):** nguồn vênh lớn nhất của L2b sâu là
**foundation nói "số là ví dụ" vs validator gác số cứng** → tách rạch ròi: *foundation
quản Ý, bảng ràng buộc (sinh từ hằng số code) quản SỐ* — cùng họ với bài học
[[filter-overload-guard]] (tách LỌC khỏi RANK ở phễu).

## 5. Cái gì CHƯA làm đợt này (tránh phình)

| Để sau | Vì sao |
|---|---|
| Lớp nghĩa 2–3 của text (f1, cần web) | bước kế TỰ NHIÊN sau khi direct sâu ổn — phiên sống có sẵn web, nhưng đợt này chỉ thay chỗ prompt cứng, không mở thêm nghề mới |
| Hình thở 2 pha [min–max] + sàn thở/cứu hộ (d2) | cần đổi schema + sourcer — tính năng riêng, cắm sau |
| Gỡ/viết lại `director/prompts.py` | KHÔNG đụng — đường cũ là fallback + xương L1 |
| Số DNA niche trong foundation phần 5 | Phase B |

## 6. Xác định THÀNH CÔNG trước khi code (P4)

Milestone nhỏ, mỗi bước báo cáo + chờ user:
1. **M1 = user duyệt tài liệu này** (gồm cả 4 vá chồng chéo ở §4b — duyệt 1 lần).
2. **M0 — vá nền 3 fix code** (§4b #1 #3 #4, mỗi fix vài dòng + pytest tái hiện lỗi
   trước-fix): chạy trước để L2b sâu đứng trên nền sạch. Báo cáo số pytest rồi mới sang M2.
3. **M2 — code ỐNG:** `direct-context` (kèm bảng ràng buộc cứng) + `direct-ingest` (kèm
   kiểm thở-sai-chỗ §4b #2) + pytest (xuất đúng format từ đánh số; ingest CHẶN draft hở
   coverage/thở sai chỗ; draft sạch → beats + timestamp khớp y đường cũ xử lý). Chưa đụng skill.
4. **M3 — cập nhật skill `/dung-video` + chạy thật:** video test MỚI ở folder
   `voice test travel` (Thụy Sĩ: hook + Zurich + Bern + Lucerne — nhiều nguồn footage
   hơn bài Ai Cập). Chuẩn bị input: **ghép 4 mp3 → 1 voice.mp3** (ffmpeg concat, đúng
   thứ tự hook→ch1→ch2→ch3) vì pipeline nhận 1 file voice. Chạy direct đường CŨ trước
   (lưu `beats_old.json` đối chứng) → chạy đường SÂU → đặt 2 bản cạnh nhau cho user so
   (route mix, nhịp beat, thở, overlay). **Cổng mắt: user duyệt beats bản sâu.**
5. **M4 — Pha 2 video travel:** cut→source→assemble→report → **cổng mắt draft CapCut.**

---

> **Chờ user duyệt tài liệu này.** Duyệt → M0 (vá 3 chỗ chồng chéo + pytest, báo cáo) →
> M2 (2 lệnh ỐNG + pytest, báo cáo) → mới sang M3. Không nhảy cóc.
