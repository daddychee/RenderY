# MÔ TẢ VẬN HÀNH — LUẬT WORLD-LOCK (giữ mọi hình trong thế giới của niche)

> User chốt 2026-07-14 (DS3-084 "Womb Cannibalism"). Áp cho niche khai trong
> `director/live.py::WORLD_LOCK` — hiện chỉ **deepsea**. Niche khác fail-open (không đụng).

---

## 1. Vấn đề

Deepsea DS3-084 (230 beat): nhiều beat nói về chủ thể biển nhưng HÌNH rời khỏi thế giới
dưới nước sang con người / đất liền / y khoa:

- **Nhóm concept sai thế giới** (NÃO tự viết concept ngoài niche): b21 "working row of
  needle teeth in a small open mouth" → phễu tải **miệng người cực cận**; b59 "researcher
  looking at a specimen jar, lab moment" → **nhà khoa học lab**; b41 lab rót chất lỏng;
  b46 nhóm nghiên cứu; b107 nhìn kính hiển vi; b186/b208 người trên cồn cát / nhìn biển.
- **Nhóm route entity ảnh người** (script chủ đích nói về người → NÃO route entity đúng
  luật `_SOURCING_RULES`): b213-217 "something like it happens in **people** too — doctors
  call it vanishing twin syndrome … ultrasound" → **ảnh siêu âm người**.
- **Gốc thượng nguồn**: outline ch2 `central_subject` = "sand tiger shark embryos … **and
  the researchers who study them**" — NÃO tự mời con người vào thế giới chủ đề, nên veto
  `thuc_the_sai` của phễu KHÔNG bắn (nó đo vs central_subject đã có "researchers").

**Khác lỗi "bán thuốc"** ([[ban-thuoc-voice-ke-an-du]] / `MO_TA_VAN_HANH_BAN_THUOC.md`):
bán thuốc = script MƯỢN ẨN DỤ domain ngoài, HÌNH minh họa nghĩa đen "cỗ xe chở nghĩa".
World-lock = script kể chuyện **THẬT** ngoài thế giới niche (người, y học, đất liền), nhưng
với niche này khán giả tới để XEM thế giới đó → HÌNH vẫn phải ở lại thế giới niche. Hai luật
BỔ NHAU, không thay nhau.

Phễu (sourcer → ranker) là người-theo-lệnh của concept → **sửa tầng director**, không đẻ
luật lật ở phễu (đúng bài học bán thuốc §5 + [[filter-overload-guard]]).

## 2. Luật

**THẾ GIỚI HÌNH của niche là HẰNG SỐ.** Với niche khóa (deepsea = dưới nước/đại dương):

- Mọi `visual_concept` và `central_subject` PHẢI ở trong thế giới đó — kể cả khi câu script
  chủ đích nói về con người / y học / đất liền / đời sống người xem.
- Kho/Pexels KHÔNG có đúng chủ thể → rơi về **NỀN NICHE** (nước tối len ánh sáng, đàn cá
  nhỏ, đáy biển, bóng loài săn mồi, chính loài đang nói), KHÔNG rơi về người/lab.
  Bland-đúng-thế-giới THẮNG specific-sai-thế-giới (WRONG-vs-BLAND).
- `sourcing_route`: KHÔNG route `entity` (ảnh thật) cho người/sự kiện y khoa/đời sống đất
  liền dù script nêu tên. Route `entity` CHỈ cho thực thể THẬT là sinh vật/vật thể biển
  (một loài cá mập cụ thể, xác tàu đắm, tàu lặn/ROV, nhà khoa học biển trên tàu/dưới nước).
- `central_subject` mỗi chương KHÔNG được mời người ngoài thế giới vào (cấm
  "...and the researchers who study them" nếu họ ở lab đất liền).

## 3. Thực thi ở đâu

| # | Chỗ | Nội dung |
|---|---|---|
| 1 | `director/live.py::WORLD_LOCK` | registry data-driven: niche → {world, fillers, off_world}. Thêm niche = thêm 1 entry, không sửa code luật |
| 2 | `director/live.py::world_lock_block()` | sinh khối luật; fail-open niche không khai → '' |
| 3 | `director/live.py::build_direct_context` | chèn khối vào direct_context.md (đường sâu — đường chính) sau bán-thuốc, trước OUTPUT |
| 4 | `director/runner.py` | chèn `world_lock_block(niche)` vào `library_context` (đường direct cũ — parity) |

Không đụng schema, không đụng phễu, không config file mới (registry nằm trong code cùng
kiểu SUBJECT_RULES built-in).

## 4. RÀ CHỒNG CHÉO (P5)

| Tầng cùng quản "hình nào cho câu này" | Quan hệ với world-lock |
|---|---|
| Luật bán-thuốc (`_BAN_THUOC_BLOCK`, prompts.py) | **BỔ NHAU** — bán thuốc gác ẩn dụ-mượn-ngoài, world-lock gác chuyện-thật-ngoài-niche. World-lock THÊM khối, không sửa/xóa bán-thuốc (test khẳng định cả 2 cùng có). Không ngược chiều |
| `_SOURCING_RULES` (route entity cho người/sự kiện thật) | **World-lock THU HẸP** cho niche khóa: entity chỉ cho thực thể BIỂN. Đây là ghi đè CÓ CHỦ ĐÍCH cấp niche, không phải mâu thuẫn — luật chung vẫn đúng cho space/travel |
| `_CONTEXT_COHERENCE` (neo central_subject, ngoại lệ "thực thể THẬT") | CÙNG CHIỀU — world-lock chỉ SIẾT ngoại lệ "thực thể thật" xuống "thực thể biển thật" cho niche khóa |
| Pass 1 central_subject | CÙNG CHIỀU — world-lock cấm central_subject mời người đất liền vào (cùng tinh thần bán-thuốc cấm central_subject chứa tu từ) |
| Ranker veto `thuc_the_sai` (đo vs central_subject/video_subject) | KHÔNG lật — world-lock sửa THƯỢNG NGUỒN (concept + central_subject sạch) → veto tự chảy đúng. KHÔNG thêm luật veto "người" ở phễu (tránh tầng dưới âm thầm lật + filter-overload-guard 2-veto) |
| C5 vision gate (soi kho local) | KHÔNG đụng — vẫn soi subject_match như cũ; concept sạch thì pool local đúng thế giới |
| Sàn niche ở phễu (đề xuất trong điều tra) | **KHÔNG làm** (user chốt chỉ tầng đạo diễn 2026-07-14). Ghi backlog §6 nếu sau này concept sạch mà kho vẫn thiếu → phễu vẫn có thể rơi người |
| Lưới máy `ban_thuoc_warnings` (direct-ingest) | KHÔNG đụng — vẫn chạy; world-lock không đẻ lưới mới (là luật prompt, không cửa loại) |

**Kết luận:** world-lock chỉ ghi đè CÓ CHỦ ĐÍCH `_SOURCING_RULES` cho niche khóa (đúng
thiết kế), không tầng nào âm thầm lật nó, không ngược chiều bán-thuốc.

## 5. Cổng kiểm chứng

- pytest FULL **494/494** (+3: deepsea sinh khối đúng luật · fail-open niche không khóa +
  chuẩn hóa hoa/thường · chèn đúng chỗ direct_context.md và không lật bán-thuốc).
- Retrofit DS3-084 (đang chờ): re-source beat bệnh (b17-24 + b41/46/59/107/186/208 +
  b213-217) qua phễu thật, giữ nguyên dur beat (mốc cắt/nhạc không đổi) → re-pick breath →
  assemble `_V3`. Nhóm b213-217 đổi route entity→stock/local, concept → phôi cá mập/womb
  tối/đàn cá.
- **Cổng MẮT user: CHỜ** (draft _V3).

## 6. Còn ngỏ / backlog (không tự làm)

- **Sàn niche ở phễu**: nếu video mới có concept sạch nhưng kho thật sự thiếu đúng chủ thể,
  phễu vẫn có thể rơi về người (Pexels broad/thematic). Chưa làm (user chốt chỉ tầng đạo
  diễn). Cân nhắc nếu cổng mắt video MỚI còn lọt người.
- **Niche khác**: travel/space chưa khai world-lock. Khi có bằng chứng cần (vd travel lọt
  cảnh sai xứ) → thêm 1 entry WORLD_LOCK.
