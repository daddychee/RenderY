# MÔ TẢ VẬN HÀNH — LUẬT "BÁN THUỐC" (VOICE kể ẩn dụ — HÌNH kể câu chuyện)

> User chốt 2026-07-13 (thay đổi cách hiểu cấp "metaphorical" của foundation c2 — xem
> 📌 LỆCH trong `foundation/c2-an-du-veto.md`). Áp dụng MỌI NICHE, cả 2 đường direct
> (cũ prompts.py + sâu direct_context.md).

---

## 1. Vấn đề

Lỗi "bán thuốc" = **mô tả nghĩa đen của chữ thay vì kể câu chuyện thật của chapter/beat**.
Gặp ở space, lặp lại ở deepsea DS5-083 → lỗi thiết kế, không phải lỗi kho.

Bằng chứng DS5-083 (270 beat): script mượn ẩn dụ "Picture the ocean as a giant Jenga
tower" → NÃO đạo diễn sinh `visual_concept` = "tall wooden Jenga block tower on a table"
→ phễu trung thành tải đúng clip Jenga từ Pexels, note "khớp hoàn hảo ẩn dụ". Tổng 11 beat
bệnh: b014-b018 + b024-b025 (Jenga), b048 + b109 (domino), b019-b020 (nói-với-người-xem →
thị trấn biển/phòng ngủ 2h sáng). Đáng chú ý: 45/56 beat `metaphorical` còn lại NÃO làm
ĐÚNG (ẩn dụ tự nghĩ đều tự neo vào thế giới cá mập) — **bệnh chỉ phát khi CHÍNH SCRIPT
mang ẩn dụ từ domain ngoài** và NÃO minh họa "cỗ xe chở nghĩa" thay vì câu chuyện.

3 lỗ hổng đã vá:
1. **Pass 1 tự đầu độc neo**: outline ghi central_subject ch1 = "...food web **(Jenga
   tower metaphor)**" → luật "neo vào central_subject" trỏ thẳng vào Jenga.
2. **Pass 2 có kẽ hở**: ngoại lệ "central_subject ABSTRACT thì giữ vật bề mặt" ("food
   web" đọc là abstract → mở cửa); từ điển ẩn dụ generic (dominoes, chess...) khuyến
   khích đi ra ngoài thế giới niche.
3. **Đường SÂU mù hoàn toàn**: `direct_context.md` không có dòng coherence nào; skill
   dung-video còn có ngoại lệ "beat ẨN DỤ CHỦ ĐÍCH vẫn generic" = giấy phép cho bug.

Hạ nguồn (sourcer query → ranker chấm vs "Visual intent" → breath neo visual_concept)
đều là người-theo-lệnh → **sửa đúng tầng director, không đụng phễu**.

## 2. Luật

**VOICE kể ẩn dụ — HÌNH kể câu chuyện.**
- Script TỰ mượn ẩn dụ/ví von/giả định từ domain ngoài, HOẶC nói trực tiếp với người xem
  ("wherever you're watching from", "you at 2am") → `visual_concept` **Ở LẠI thế giới
  của video_subject/central_subject**, diễn ẩn dụ bằng hình TRONG thế giới đó (tháp loài
  → rạn tầng tầng đàn cá; "rút khối" → cá mập biến khỏi khung hình; sụp đổ → đàn cá tan).
  *(Scope CHẶT — gồm cả beat đời-sống-người-xem: user chốt khi flag b019.)*
- Hình CHỈ rời thế giới chủ đề khi content nói về **thực thể/sự kiện THẬT đang là chủ đề**
  (Gordon Ramsay, cảng cá, thành phố mất điện vì sứa). Thủ pháp tu từ KHÔNG BAO GIỜ đủ
  điều kiện.
- `central_subject` (pass 1) KHÔNG được chứa thủ pháp tu từ của script.
- `visual_level: metaphorical` = ẩn dụ THỊ GIÁC do đạo diễn thêm cho câu THƯỜNG, diễn
  trong thế giới chủ đề — không bao giờ = minh họa ẩn dụ có sẵn của script.
- Ngoại lệ ABSTRACT thu hẹp: chỉ khi CẢ VIDEO không có thế giới chủ đề quay được (video
  động lực thuần "opportunity is an open door") — niche PADOMA (space/deepsea/travel)
  không bao giờ rơi vào đây.

## 3. Thực thi ở đâu

| # | Chỗ | Nội dung |
|---|---|---|
| 1 | `director/prompts.py` `_DIRECTOR_ROLE` | từ điển ẩn dụ khóa 2 qualifier: chỉ câu THƯỜNG + diễn in-world |
| 2 | `director/prompts.py` pass 1 | central_subject cấm chứa thủ pháp tu từ (phản-ví-dụ Jenga) |
| 3 | `director/prompts.py` `_CONTEXT_COHERENCE` (pass 2) | SCRIPT-SIDE METAPHOR RULE + direct-address + thu hẹp ABSTRACT |
| 4 | `director/live.py` `_BAN_THUOC_BLOCK` | khối luật TỰ SINH trong direct_context.md (đường sâu — đường chính) |
| 5 | `.claude/skills/dung-video/SKILL.md` | thay ngoại lệ "ẩn dụ chủ đích vẫn generic" bằng luật mới |
| 6 | `director/live.py` `ban_thuoc_warnings` | lưới máy ở direct-ingest — xem §4 |
| — | `foundation/c2-an-du-veto.md` | 📌 LỆCH SO VỚI BẢN GỐC (nguyên văn gốc giữ) |

## 4. Lưới máy "nghi bán thuốc" (warning-only)

Chạy ở `direct-ingest` sau khi pass validator: beat route stock/local mà `visual_concept`
**0 token trùng** (video_subject + central_subject chương, gọt số nhiều "sharks"→"shark")
→ in "⚠ nghi bán thuốc b0XX" vào warnings. **KHÔNG chặn, KHÔNG loại** (filter-overload-guard
giữ — hệ chỉ có 2 veto). Route entity/graphic miễn.

- **False-positive là bình thường**: đo trên DS5-083 sau khi sửa, lưới kêu 32 beat, soi
  tay **0 beat cần sửa thêm** — toàn diễn-đạt-khác-từ ("great white"/"orca" vs "sharks",
  "plankton speck" vs "phytoplankton") hoặc nội dung thật (blackout sứa, surfer/seal
  nhận-nhầm-mồi, Farallon). Lưới là DANH SÁCH SOI TAY cho phiên sống, không phải phán quyết.
- **Điểm mù đã biết**: central_subject bị nhiễm chính ẩn dụ đó thì lưới mù (2 vế cùng
  chứa "jenga") — tầng gác chỗ ấy là luật pass 1 (#2). Hai tầng đỡ nhau, không thay nhau.
- Đường direct CŨ không có lưới máy (chỉ có luật prompt) — chấp nhận vì là fallback.

## 5. RÀ CHỒNG CHÉO (P5)

| Tầng cùng quản "hình nào cho câu này" | Quan hệ với luật mới |
|---|---|
| Pass 1 central_subject | CÙNG CHIỀU sau khi thêm luật cấm tu từ (#2) — trước đó là nguồn độc |
| Pass 2 concept/level/queries | CÙNG CHIỀU (#1/#3). Từ điển ẩn dụ TRƯỚC ĐÂY NGƯỢC CHIỀU → đã khóa qualifier, nếu không prompt tự mâu thuẫn |
| Skill dung-video (đường sâu) | Ngoại lệ ẩn dụ TRƯỚC ĐÂY NGƯỢC CHIỀU → đã thay (#5) |
| Sourcer queries | Người-theo-lệnh của concept — không lật |
| Ranker/đầu chấm nghĩa (chấm vs "Visual intent") | Người-theo-lệnh — concept sạch thì tự chảy đúng; KHÔNG thêm luật lật ở đây (tránh tầng dưới âm thầm lật tầng trên) |
| V3 video_subject veto / C5 vision gate | Vòng ngoài thực thể / soi kho local — không đụng |
| REF (sp1-014) + C4 từ vựng kho | CÙNG CHIỀU (kho/nguồn mẫu chính là thế giới niche) |
| Shot thở 3.0 (neo visual_concept cho pick stock) | HƯỞNG LỢI trực tiếp — b048 hết "domino→ốc anh vũ qua token chain" |
| Luật NICHE-ANCHOR (SP1-014) | CÙNG CHIỀU — luật mới đóng đúng cái cửa ngoại lệ của nó |

Không tầng nào còn ngược chiều; không tầng nào âm thầm lật quyết định tầng mới.

## 6. Cổng kiểm chứng

- pytest FULL **478/478** (+4: 2 test prompt mang luật, 1 hồi quy lưới máy bắt Jenga-trong-
  chương-cá-mập + miễn entity/graphic + khớp số nhiều, 1 fail-open không neo).
- Retrofit DS5-083: 11 beat re-source qua phễu c5 thật (ledger seed viral + REF nguyên
  luật), dur beat không đổi (mốc cắt/nhạc giữ nguyên) → re-pick breath (dur phải khớp
  100%) → re-assemble ra draft `..._V2`.
- **Cổng MẮT user: ✅ ĐẠT 2026-07-13** (user duyệt draft _V2 — 11 beat theo mốc phút).
- Adherence prompt thật sự chỉ đo được ở video DỰNG MỚI tiếp theo (mọi niche) — lưới máy
  §4 là chỉ báo sớm ngay tại direct-ingest. **Còn theo dõi** tại đó.

## 7. Còn ngỏ / backlog (không tự làm)

- b065/b066/b176/b177 DS5-083: `visual_concept` mô tả CHART thay vì cảnh footage (bệnh
  khác, nhẹ, không phải bán thuốc — footage vẫn đúng chủ đề). Ghi nhận, chưa sửa.
- Giảm false-positive lưới máy bằng cách cộng từ vựng kho niche vào anchor — chỉ làm nếu
  user thấy danh sách soi tay dài quá mức chịu được.
- Đường direct cũ: cân nhắc wire lưới máy nếu còn dùng thật ngoài fallback.
