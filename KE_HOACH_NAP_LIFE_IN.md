# KẾ HOẠCH NẠP NICHE LIFE-IN — sổ theo dõi xuyên phiên

> **Mục đích file này:** Claude Code sau khi /clear đọc file này là chạy tiếp được ngay,
> không cần hỏi lại. Cập nhật bảng trạng thái SAU MỖI bước/draft xong. User nhắc "chạy tiếp
> life-in" = mở file này → làm mục 🔄/⏸ đầu tiên chưa xong.
> Mẫu đúc từ `KE_HOACH_NAP_DEEPSEA.md` (đã đóng trọn 2026-07-13).

---

## ✅ ĐÊM TỰ ĐỘNG 2026-07-14→15 HOÀN TẤT (không còn job nền)

Toàn bộ bước 0→9 ĐÓNG. Kho life-in: **10.222 asset / 44 draft** (99,5%) + ambient 93 +
SFX 48 + nhạc pool +85 (241 tổng) + `pause_dna.json` + `dna.json` (10,2 cut/phút).
Việc còn lại: (a) 👂 user nghe 3 bài nhạc staging tên mù (SLOW JAPAN/SUMO/chill music##);
(b) CÒN NGỎ 54 cảnh lỗi lì (21 contentFilter 1301 REAL82/86 + 33 khác — tag tay nếu cần,
tiền lệ PB9); (c) bước 10 video kiểm CHỜ user đưa script+voice.

## 🔄 ĐỢT 2 — 2026-07-16: +12 draft (REAL77a + 11 AMAZING)

**User chốt 2026-07-16:** (a) 11 draft `E:\PROJECT NHAN BAN\AMAZING` (kênh AMAZING — facts
quốc gia, phong cách grid/MC/logo riêng) **NHẬP CHUNG vào life-in** (chấp nhận DNA pha 2
phong cách, đổi lấy kho footage quốc gia dùng chung); (b) phim nướng **REAL48/55/59/69 BỎ
QUA** (REAL69 mới soi 2026-07-16: track#0 = 27 seg, 1 file REAL69.mp4 27' = 95%).
REAL17 vẫn rỗng. → REAL LIFE 50 folder = 44 đã nạp + 4 nướng + 1 rỗng + **REAL77a MỚI**.

Khảo sát đợt 2 (scratchpad/survey_new.py): 12 draft đều dựng chuẩn 280–488 cut/draft,
~28–31'/bài (~350' tổng); seg full-length chỉ là LOGO.png/nền — không phải nướng. Lưu ý:
vài draft AMZ cắt từ chính file xuất (`Bài AMZ20.mp4`) → clip có đồ họa burned-in, tiền lệ
REAL07/REAL17.mp4 "vô hại". Backup sổ PG trước mẻ: `F:\AutoEdit\backup\pg\autoedit_pre_nap_dot2_20260716.dump` (19,6 MB).

| # | Bước đợt 2 | Trạng thái |
|---|---|---|
| 1 | pg_dump backup trước mẻ | ✅ 2026-07-16 |
| 2 | tcf-gen 12 draft | ✅ 2026-07-16: 12/12 đạt 1 lần (12-15 chapter/bài). Title: REAL77a Samoa · AM32 Germany · AMZ35 Argentina · AMZ38 Hungary · AMZ40 Netherlands · AMZ42 Cape Verde · AMZ33 France · AM19 Norway · AMZ20 Georgia · AMZ31 Croatia · AMZ45 Mauritius · AMZ999 Czech |
| 3 | Rà title trùng với 44 cũ | ✅ 2026-07-16: **REAL77a = CÙNG BÀI REAL77** (chapter khớp từng giây 0:47/3:03/4:35, cùng voice, bản dựng lại 385 vs 327 seg) → VẪN NẠP: dedup cùng-nguồn-cùng-khúc tự loại phần trùng, chỉ footage mới vào kho. AMZ42 Cape Verde ≠ REAL83, AMZ40 Netherlands ≠ REAL35 (bài khác góc) → giữ cả, tiền lệ đợt 1 |
| 4 | library-ingest 12 draft | 🔄 **Mẻ 1 ✅ 2026-07-16** (REAL77a 327c/1 lỗi + AM32 367c/3 lỗi — 0 lỗi mood mới, từ điển đủ cho kênh AMAZING; db 12.162→12.852; REAL77a dedup chỉ 15 → bản dựng lại dùng nguồn khác REAL77, đáng nạp; lỗi lì: 1 validation + 2 compound hỏng + 1 contentFilter 1301). **Mẻ 2 ✅** (AMZ35 345c/0 · AMZ38 408c/0 · AMZ40 379c/2 · AMZ42 425c/0 · AMZ33 341c/1 — db 14.747). **Mẻ 3 ✅** (AM19 322c/1 · AMZ20 352c/1 · AMZ31 254c/0 · AMZ45 307c/0 · AMZ999 325c/0). **Vòng vớt ✅ 2026-07-16: +1 cảnh → ĐÓNG, kho life-in CHỐT 16.305 asset** (+4.143 đợt 2). CÒN NGỎ 8 lỗi lì (0,2%): 2 compound hỏng (AM32) + 2 contentFilter 1301 (AM32 ảnh 'beateuhse'/AMZ20) + 4 validation/mạng lì (REAL77a·AMZ40×2·AMZ33) — tag tay nếu cần, tiền lệ PB9 |
| 5 | editor-learn 12 draft | ✅ 2026-07-16: 12/12, 0 lỗi. Mót: 33 ambient + 1 SFX + 78 nhạc staging + ~31 hold. editor_dna.json cộng dồn 83 draft |
| 6 | nhạc/ambient mót được → import tiền lệ | ✅ 2026-07-16: ambient-import 33/33 (**animal_wildlife 6→14** + wind 15 + urban_street 21 + people_activity 11 — lấp đúng gap RD-89) + sfx-import 49 (gom cả tồn staging cũ: whoosh 63/swell 38/impact 28). Nhạc: `scripts\stage_music_amazing.py` (map mood tường minh 78 bài, khuôn đợt 1 nhưng DST theo resolver MUSIC_ROOT sau G1) → **76 COPY vào pool** + 2 SKIP (Scarlett trùng-bài-khác-tên y đợt 1 · Seine River trùng nội bộ 2 draft) + 0 tên mù; music-import **317 bài / 0 lỗi** (pool cũ 241) |
| 7 | compute-dna + pause-dna lại (báo số trước/sau) | ✅ 2026-07-16: library-dna 56 draft/1.606,9': **10,8 cut/phút** (cũ 10,2) · shot p50 4,2s (4,07) · hold 35% (34) · medium 49/wide 29/aerial 16/close-up 6 (51/26/16/7) · CU 1/15,8 shot (13,9) — AMAZING kéo dày nhẹ, chữ ký vẫn urban, drift nhỏ. pause-dna 54 draft (loại REAL72/79 y đợt 1): so .new.json ổn → **--force đè, backup tự động**: KET_CAU 2,69/ph p50 1,08s (cũ 2,88/1,1) · KET_MENH_DE 0,7/ph 0,58s · 702 ô ≥1,5s (538 hình thở, footage p50 2,47s) · k={1:430, 2:95, 3:13} |
| 8 | sổ + memory + commit | ✅ 2026-07-16: memory `life-in-onboarding` cập nhật đợt 2 + MEMORY.md + NHAT_KY_BUILD `LIFE-IN-DOT2` + pytest **541 pass/0 fail + parity PG 17/17 (đủ cổng 549)** + commit mốc |

**ĐỢT 2 ĐÓNG TRỌN 2026-07-16.** Video kiểm cổng mắt+tai của niche (bước 10 đợt 1) vẫn CHỜ USER.

## Niche là gì (user mô tả 2026-07-14)

Phim tài liệu về nhiều **quốc gia, bộ tộc, hòn đảo, khu biệt lập**. Mỗi video kể facts về
(các) quốc gia được nhắc tới. Nhóm cảnh lặp lại: **phong cảnh, con người, văn hóa, cuộc
sống, địa lý, lịch sử** của quốc gia đó.

**Khán giả = nam giới lớn tuổi.** Sở thích footage:
- Cảnh đẹp thiên nhiên hùng vĩ, danh lam thắng cảnh ấn tượng.
- **Phụ nữ xinh đẹp / sexy** của các quốc gia được nhắc tới (audience_bias mạnh).
- Với bộ tộc / hòn đảo kỳ lạ: **văn hóa & phong tục hiếm gặp** (thứ ít khi được thấy) +
  **động vật đặc trưng** của quốc gia.

## Quyết định đã chốt (user, 2026-07-14)

1. **Slug niche = `life-in`** (kiểu gạch-nối, đồng bộ 'retirement-abroad'). Folder kho:
   `F:\AutoEdit\library\life-in\`. Tham số CLI khắp pipeline: `--niche life-in`.
2. **KHÔNG world-lock** (user chốt) — documentary quốc gia trải rộng (phố/người/đồ ăn/
   landmark/động vật), khóa sớm dễ chặn oan. Để mở như space/travel. Thêm sau NẾU video
   kiểm lộ cảnh lạc thế giới.
3. **Nguồn kho = draft editor công ty**, folder: `E:\PROJECT NHAN BAN\REAL LIFE`.
   → TẤT CẢ là `own` (không trần 8%, không gate kề — luật own-vs-viral). ⚠ Niche NHIỀU
   project → chạy theo mẻ, ghi sổ này, cẩn thận token cửa sổ chat.
4. Số âm thanh per-niche (HOOK_DUCK, HOOK_SFX, drone, xfade nhạc) hiện **fail-open về
   số mặc định** — đủ chạy. CHỈ tinh chỉnh ở video kiểm khi user nghe thấy cần (P2 không
   hard-code sớm).
5. **User chốt 2026-07-14 (trước khi đi ngủ): TỰ ĐỘNG toàn bộ phần còn lại qua đêm**,
   gồm cả ingest GLM dài + "lưu sfx, music (nhạc nền), dna niche vào hệ thống".
   Thứ tự máy chạy (tối ưu việc-nhanh-trước): tcf-gen 36 draft còn lại → rà title trùng
   (tự quyết bảo thủ: chỉ loại khi RÕ cùng tập — title cùng chủ đề + duration lệch ≤2%,
   ghi sổ mọi ca loại) → editor-learn 40 draft + ambient-import + sfx-import →
   pause-dna (cache transcribe sẵn) → nhạc staging: gán mood TỪ TÊN như deepsea, bài
   tên rõ mood vào pool + music-import; **bài tên mơ hồ GIỮ STAGING chờ tai user**
   (pool nhạc CHUNG mọi niche — không đoán prior mood life-in bừa) → ingest 40 draft
   TUẦN TỰ theo mẻ (dài, chạy tới đâu ghi sổ tới đó) → library-dna khi ingest đủ.
   Mỗi mốc: cập nhật sổ + commit. Lỗi lẻ: ghi sổ chạy tiếp, KHÔNG dừng cả đêm.

## Trạng thái đã làm

| # | Bước | Lệnh / việc | Trạng thái |
|---|---|---|---|
| 0 | `library-init life-in` | Tạo folder `F:\AutoEdit\library\life-in\` (signature/ + entity/ + niche_profile.yaml mẫu) | ✅ 2026-07-14 |
| 1 | Điền `niche_profile.yaml` | ✅ Kiểm 2026-07-14 (phiên sau): file ĐÃ TỒN TẠI trên đĩa, UTF-8 đúng, nội dung khớp khối soạn sẵn bên dưới (phiên trước ghi được trước khi reject) | ✅ 2026-07-14 |
| 2 | Khảo sát folder `REAL LIFE` | ✅ Khảo sát SÂU xong 2026-07-14 (script `scratchpad/survey_life_in.py`, kết quả §Khảo sát bên dưới): 48 folder → **đề xuất danh sách ingest 44 draft, ~1.261 phút (~21h)**; loại REAL17 (rỗng) + ⛔ hoãn REAL48/55/59 (phim nướng — main track = 1 file xuất sẵn chiếm 95-96% timeline, kiểu DS1_074); MD5 không trùng | ✅ 2026-07-14 |
| 3 | `tcf-gen` mỗi draft | ✅ **ĐÓNG 2026-07-14: 44/44 TCF.** Lệnh: `cd autoedit; uv run autoedit tcf-gen life-in --draft "E:\PROJECT NHAN BAN\REAL LIFE\<REALxx>" ...` (idempotent — có TCF thì skip). **Mẻ 1 (8 draft): 4 đạt + lòi bug chọn track voice → FIX xong** (memory `voice-track-hybrid-score`, pytest 511/511, user duyệt): `voice_files_of` điểm lai seg×duration thay max-segment — 11 draft REAL từng sẽ dính đều khỏi. REAL18 NÃO trượt title tiếng Việt (transcript Anh) → rerun `--force`. Mẻ 2 (36): 34 đạt + REAL72/79 cần fix tầng 2 = fallback track ≤3 ứng viên khi transcript <200 từ/transcribe lỗi (commit 794b2d7, pytest 513/513) + ghim ngôn ngữ prompt (REAL18/70/86 trượt tiếng Việt → force lại đạt cả) | ✅ 2026-07-14 |
| 4 | Rà title trùng → chốt danh sách ingest | ✅ 2026-07-14: 4 cặp cùng quốc gia (Cambodia 29/79 · India 07/27 · Indonesia 41/63 · Philippines 18/84) đều BÀI KHÁC (title khác góc + duration lệch >2%) → GIỮ CẢ theo tiền lệ remake deepsea. **Danh sách ingest CHỐT = 44 draft, 0 loại thêm** | ✅ 2026-07-14 |
| 5 | `library-ingest` từng draft (nền) | ✅ **ĐÓNG 2026-07-15: 44/44 draft, kho 10.222 asset (99,5%), còn ngỏ 54 lỗi lì** (21 contentFilter 1301 + 1 HTTP 1210 + 3 mood-toàn-lạ + ~29 mạng lì — tag tay nếu cần, tiền lệ PB9). Lịch sử: mẻ 1 770 cảnh/104 lỗi mood-vocab → vá 21 từ documentary quốc gia vào `_MOOD_SYNONYMS` (spiritual/lively/traditional/cultural/everyday... — tiền lệ PB4, commit 3f6bec2, pytest 513/513). Retry mẻ 1 vớt 101/104 (còn 3 lì) + mẻ 2 xong 2026-07-15: **13/44 draft, db 1.977 asset, ~17 lỗi lì cộng dồn**. Mẻ 3 xong: **23/44 draft, db 3.577 asset** (~44 lỗi lì cộng dồn, REAL53 = 11). Mẻ 4 xong: **33/44 draft, db 6.591** (+59 lỗi, lộ đuôi mood thứ 2 → vá 2 tầng commit 481a970: +14 synonym + validator mềm bỏ-từ-lạ-khi-còn-mood-hợp-lệ). **Mẻ 5 XONG 2026-07-15: CẢ 44/44 DRAFT ĐÃ INGEST — kho 10.140 asset** (vượt deepsea 8.981). **Retry XONG: vớt 82 cảnh → kho CHỐT 10.222 asset (99,5%). Bước 5 ĐÓNG 2026-07-15.** CÒN NGỎ 54 lỗi lì (0,5%): 21 contentFilter 1301 vĩnh viễn (tập trung REAL82/86 — cảnh bộ tộc/phụ nữ nghi bị bigmodel chặn oan, tag tay nếu cần — tiền lệ PB9) + 1 HTTP 1210 + 3 mood-lạ-toàn-phần (professional/industrial/abundant) + ~29 lỗi mạng lì. Lỗi lì khác đã thấy: 1 contentFilter 1301 (REAL28) + 1 HTTP 400 code 1210 (REAL13) — vớt cuối như deepsea | 🔄 DỞ |
| 6 | `compute-dna` + `pause-dna` | ✅ **ĐÓNG TRỌN 2026-07-15** — compute-dna 44 draft: `dna.json` **10,2 cut/phút** (sau fix mega-chồng-track, commit kèm) · shot p50 4,07s · hold 34% · close-up 7% (1/13,9 shot) · medium 51%/wide 26%/aerial 16% · chuỗi medium×3 áp đảo · chữ ký urban_street/urban_landmark/people_activity · hook mở urban medium/aerial. So deepsea (11,9cpm/4,63s/45%/20% close-up) + space (9,4/6,2s/67%): life-in nằm giữa, ít đặc tả, nhiều aerial — DNA per-niche trả công. **pause-dna ✅**: 42 draft (loại REAL72/79 — pause-dna dùng candidates[0], 2 draft này track #0 là nhạc)/1.202 phút, chèn +2,8% → `pause_dna.json`: KET_CAU 2,88/ph nghe-ra p50 1,1s · KET_MENH_DE 0,78/ph 0,58s · 496 ô ≥1,5s (388 hình thở, footage p50 2,43s, k={1:297, 2:84, 3:7}) — NÔNG + DÀY hơn deepsea (4,2/ph 2,41s) đúng chất kể facts. `dna.json` (compute-dna) CHỜ ingest xong | ✅ 2026-07-15 |
| 7 | `editor-learn` từng draft | ✅ **ĐÓNG 2026-07-15: 44/44 draft 0 lỗi.** Mót: 93 ambient + 48 SFX + 112 nhạc (staging `F:\AutoEdit\music_editor\REALxx\`, 40 draft) + hold chưa phân loại; DNA âm cộng dồn editor_dna.json | ✅ 2026-07-15 |
| 8 | Ambient life-in | ✅ **ĐÓNG 2026-07-15: ambient-import 93/93 + sfx-import 48/48, 0 lỗi.** Kho `F:\AutoEditmbient\life-in`: ocean 28 · sky_cloud 13 · urban_street 12 · fire 12 · nature_forest_field 8 · explosion 7 · water 4 · people_activity 3 · mountain_desert 3 · rumble 2 · space 1. SFX kho chung: whoosh 45 · swell 27 · impact 19 · ding 10 · pop 9 · keyboard 7 | ✅ 2026-07-15 |
| 9 | Nhạc editor vào pool | ✅ ĐÓNG 2026-07-15 (music-import 241 bài / 0 lỗi) (user chốt "lưu music vào hệ thống" — theo tiền lệ deepsea mood-từ-tên): **112 file staging → 85 bài COPY vào pool** (map mood tường minh từng bài: `scripts\stage_music_life_in.py` — prefix editor SAD/EPIC/DOCUMENT/folk/travel/light/CLASSICAL ưu tiên, còn lại nghĩa title) + **34 SKIP** (10 file voice RD*/mp4 lọt lưới mót · 4 preset 'Các kiểu cài sẵn' · 6 stems Lars Bork · 9 trùng pool/variant tránh cặp-trùng-khác-tên · 5 khác) + **3 tên mù GIỮ STAGING chờ tai user: SLOW JAPAN.mp3 · SUMO.mp3 · chill music##...aac**. | 🔄 DỞ |
| 10 | 1 video kiểm cổng mắt + tai → mới scale | ⏸ **SẴN SÀNG — user sẽ đưa script+voice ở phiên mới.** Phiên dựng lưu ý: ① `--niche life-in` (kho 10.222 asset + dna.json + pause_dna.json tự ăn) ② **KHÔNG bật --music-sync** — luật đứng music-sync-niche-default: niche mới TẮT tới khi đo ③ kiểm dung lượng `E:\CapCut Drafts` trước assemble (ổ E từng đầy 100%, lúc đo còn ~54GB) ④ sau cổng mắt mới bàn: world-lock cần không · số âm thanh per-niche · N2 đổi-nhạc-theo-đoạn | ⏸ CHỜ USER |

## Khảo sát folder REAL LIFE (2026-07-14, bước 2 — ĐÃ XONG)

**Thô:** 48 folder con `REAL04`…`REAL91` (số nhảy cóc — chỉ 48/91 project đưa sang), tổng
~315 GB. Tất cả là draft CapCut xuất bằng tool "gom" (mỗi folder có `_BAO_CAO_THIEU.txt`;
phần thiếu chủ yếu mp3/png lặt vặt, media chính đã convert/trim gọn vào folder). Media path
gốc trỏ `C:/Users/PADOMA/`, `D:/EX/` = path chết — nhưng draft đã dùng placeholder
`##_draftpath_placeholder_<GUID>_##/materials/` (portable), resolve theo basename như deepsea.

**Sâu** (đọc draft_content 47 draft — script `scratchpad/survey_life_in.py`):
- **Loại/hoãn 4:**
  - `REAL17` ⛔ RỖNG (không draft_content.json, 0 media).
  - `REAL48`, `REAL55`, `REAL59` ⛔ HOÃN — **"phim nướng"**: main track có 1 segment
    24,8–30,7 phút = file video xuất sẵn chiếm 95–96% timeline (logo/overlay đè lên).
    Không có giá trị cắt/DNA, ingest sẽ ra 1-2 clip khổng lồ. Cùng họ DS1_074 deepsea.
    Đã quét TOÀN BỘ main track mọi draft tìm segment >5 phút — chỉ đúng 3 draft này dính.
- **44 draft còn lại HỢP LỆ, ~1.261 phút (~21h)** — gấp 1,4× deepsea (902′). MD5
  draft_content không trùng cặp nào. Duration 20,8–35,4′/draft.
- **6 draft từng nghi "bất thường số file"** (REAL79/82/83/84/86/91, 200–661 file đĩa)
  → XÓA NGHI VẤN: timeline 440–562 cut = dựng chuẩn, file nhiều chỉ là clip cắt sẵn.
- **2 phong cách dựng** trong kho (ảnh hưởng DNA bước 6 — chọn draft đại diện cân cả 2):
  nhóm cắt dày (330–562 cut/video, ~3,5s/shot: REAL04/07/24/32/49/52/53...) vs nhóm cắt
  thưa từ ít file nguồn dài (24–76 cut, shot TB 22–63s: REAL06/10/21/28/29/36/76...).
- **Compound lẻ tẻ** (material "combination"/path rỗng): rải rác 1–34 cái/draft (nhiều
  nhất REAL77/78 = 34, REAL86 = 31) — KHÔNG phải draft compound toàn phần; ingest sẽ
  skip từng file như deepsea (13 lỗi lì 0,15%), warning-only, không chặn.
- Voice: mọi draft có audio track; đa số voice chia khúc theo chương (segment dài nhất
  2–8′), vài draft voice 1 file trọn (REAL04/32/76: 20–30′). tcf-gen xử được cả hai.

### Bảng trạng thái 48 draft (TCF = title+chapter · ING = ingest · EL = editor-learn)

| Draft | Phút | TCF | ING | EL | Ghi chú |
|---|---|---|---|---|---|
| REAL04 | 21,9 | ✅ | ✅ 304c/1 lỗi lì | ✅ | "Japan: The Country Living in 2050..." 12 ch |
| REAL06 | 27,5 | ✅ | ✅ 47c/0 | ✅ | cắt thưa · "Iran: What No One Tells You About Life Inside the Country" 12 ch |
| REAL07 | 23,9 | ✅ | ✅ 373c/1 | ✅ | "India: The Civilization the World Is About to Depend On" 13 ch (file voice tên REAL17.mp4 — editor tái dùng, vô hại) |
| REAL10 | 27,7 | ✅ | ✅ 36c/2 | ✅ | cắt thưa · "Life Inside Qatar: The Desert Kingdom..." 12 ch |
| REAL13 | 29,2 | ✅ | ✅ 39c/0 | ✅ | "Brunei: The Oil Kingdom Where Gas Costs Less Than Water" 13 ch |
| REAL17 | — | ⛔ | ⛔ | ⛔ | RỖNG |
| REAL18 | 29,9 | ✅ | ✅ 44c/0 | ✅ | "The Philippines: 7,641 Islands, One Extraordinary Nation" 13 ch (force lần 2 — lần 1 NÃO trượt tiếng Việt) |
| REAL21 | 24,8 | ✅ | ✅ 27c/0 | ✅ | cắt thưa · "Inside North Korea 2026: What Life Is Really Like" 12 ch |
| REAL24 | 30,5 | ✅ | ✅ 495c/3 | ✅ | "14 Mind-Blowing Facts About Mongolia..." 15 ch |
| REAL27 | 26,3 | ✅ | ✅ 46c/2 | ✅ | India (facts) 15 ch |
| REAL28 | 20,8 | ✅ | ✅ 28c/1 | ✅ | cắt thưa · Taiwan 11 ch |
| REAL29 | 24,6 | ✅ | ✅ 26c/0 | ✅ | cắt thưa · Cambodia 12 ch |
| REAL32 | 29,9 | ✅ | ✅ 436c/7 | ✅ | Colombia 11 ch |
| REAL35 | 25,1 | ✅ | ✅ 93c/0 | ✅ | Netherlands 12 ch |
| REAL36 | 29,0 | ✅ | ✅ 28c/0 | ✅ | cắt thưa · Uganda 14 ch |
| REAL40 | 26,6 | ✅ | ✅ 33c/1 | ✅ | Sri Lanka 12 ch |
| REAL41 | 28,6 | ✅ | ✅ 56c/0 | ✅ | Indonesia 12 ch |
| REAL48 | 26,1 | ⛔ | ⛔ | ⛔ | phim nướng (seg 24,8′ = 95%) |
| REAL49 | 26,8 | ✅ | ✅ 397c/7 | ✅ | Kyrgyzstan 13 ch |
| REAL51 | 29,4 | ✅ | ✅ 55c/0 | ✅ | Vanuatu 13 ch |
| REAL52 | 31,0 | ✅ | ✅ 455c/6 | ✅ | Bahrain 14 ch |
| REAL53 | 28,6 | ✅ | ✅ 450c/11 | ✅ | Yemen 14 ch |
| REAL54 | 27,8 | ✅ | ✅ 56c/1 | ✅ | Hong Kong 13 ch |
| REAL55 | 30,9 | ⛔ | ⛔ | ⛔ | phim nướng (seg 29,6′ = 96%) |
| REAL56 | 26,0 | ✅ | ✅ 35c/1 | ✅ | Venezuela 14 ch |
| REAL57 | 28,6 | ✅ | ✅ 62c/0 | ✅ | Jordan 14 ch |
| REAL58 | 30,1 | ✅ | ✅ 414c/12 | ✅ | Monaco 14 ch |
| REAL59 | 31,9 | ⛔ | ⛔ | ⛔ | phim nướng (seg 30,7′ = 96%) |
| REAL62 | 30,2 | ✅ | ✅ 443c/5 | ✅ | Tajikistan 13 ch |
| REAL63 | 31,0 | ✅ | ✅ 40c/0 | ✅ | Indonesia (bài 2) 12 ch |
| REAL64 | 29,2 | ✅ | ✅ 408c/12 | ✅ | Kuwait 14 ch |
| REAL65 | 31,3 | ✅ | ✅ 50c/0 | ✅ | UAE 15 ch |
| REAL67 | 27,3 | ✅ | ✅ 57c/0 | ✅ | Lebanon 13 ch |
| REAL70 | 31,8 | ✅ | ✅ 437c/9 | ✅ | Egypt 15 ch (force lần 2 — lần 1 tiếng Việt) |
| REAL71 | 34,0 | ✅ | ✅ 501c/8 | ✅ | Turkmenistan 13 ch |
| REAL72 | 24,8 | ✅ | ✅ 293c/9 | ✅ | Azerbaijan 14 ch (fallback track — track#0 nhạc wav hỏng avcodec) |
| REAL74 | 31,0 | ✅ | ✅ 430c/4 | ✅ | Paraguay 14 ch |
| REAL75 | 29,8 | ✅ | ✅ 34c/0 | ✅ | Faroe Islands 14 ch |
| REAL76 | 27,2 | ✅ | ✅ 39c/0 | ✅ | cắt thưa · Thailand 13 ch |
| REAL77 | 30,3 | ✅ | ✅ 327c/1 | ✅ | 34 combo lẻ · Samoa 15 ch |
| REAL78 | 28,9 | ✅ | ✅ 300c/2 | ✅ | 34 combo lẻ · Tonga 15 ch |
| REAL79 | 29,1 | ✅ | ✅ 387c/0 | ✅ | Cambodia (bài 2) 14 ch (fallback track — nhạc thắng điểm lai) |
| REAL81 | 29,8 | ✅ | ✅ 345c/0 | ✅ | Algeria 13 ch |
| REAL82 | 30,3 | ✅ | ✅ 427c/14 | ✅ | Laos 14 ch |
| REAL83 | 31,4 | ✅ | ✅ 465c/1 | ✅ | Cape Verde 15 ch |
| REAL84 | 29,0 | ✅ | ✅ 408c/1 | ✅ | Philippines (bài 2) 13 ch |
| REAL86 | 35,4 | ✅ | ✅ 406c/13 | ✅ | Waorani/Ecuador 14 ch (force lần 2 — lần 1 tiếng Việt) |
| REAL91 | 34,5 | ✅ | ✅ 446c/1 | ✅ | Morocco 14 ch |

## Kiểm chứng "44 video mà chỉ 10.222 asset?" (user hỏi 2026-07-15 — ĐÃ ĐỐI CHIẾU ĐỦ 44 DRAFT)

Timeline có **13.507 segment video** → db 10.222 = **KHÔNG tag thiếu**, rơi đúng 3 cửa luật:
- **1.940 cảnh TRÙNG (14,4%)** — dedup cùng-nguồn-cùng-khúc: editor life-in tái dùng b-roll
  rất nhiều (REAL86: 232, REAL91: 145, REAL84: 123, REAL82: 122...). Kho chỉ giữ 1 bản,
  KHÔNG mất footage.
- **975 cảnh <2s** — sàn c8 luật 6 (flash cut, user chốt 2026-07-08, áp mọi mẻ).
- **314 file thiếu trên đĩa** — tool "gom" không copy được (khớp `_BAO_CAO_THIEU.txt`).
→ Ứng viên hợp lệ 10.278, đã tag 10.222 (**99,5%**, hụt 56 = 54 lỗi lì đã ghi còn ngỏ).
So deepsea: 10,0 asset/phút vs life-in 8,1/phút — khác biệt do (a) tỷ lệ trùng cao,
(b) 14 draft phong cách cắt thưa (shot 22-63s) chỉ ra 26-93 asset/draft.

## Nội dung niche_profile.yaml chờ ghi (bước 1)

Lần sau ghi nguyên khối này vào `F:\AutoEdit\library\life-in\niche_profile.yaml`:

```yaml
niche: life-in
description: 'Phim tài liệu về nhiều quốc gia, bộ tộc, hòn đảo, khu biệt lập. Mỗi
  video kể facts về (các) quốc gia được nhắc tới. Nhóm cảnh lặp lại: phong cảnh, con
  người, văn hóa, cuộc sống, địa lý, lịch sử của quốc gia đó. Khán giả = nam giới lớn
  tuổi: ưa footage phụ nữ xinh đẹp/sexy của quốc gia, cảnh đẹp thiên nhiên hùng vĩ,
  và với bộ tộc/hòn đảo kỳ lạ thì thích văn hóa/phong tục hiếm gặp + động vật đặc trưng.'
safe_pool:
- beautiful landscape scenery
- majestic nature aerial
- famous landmark travel
- beautiful woman country
- local people culture
- traditional tribe ritual
- exotic wildlife
audience_bias:
- beautiful woman smiling
- scenic nature aerial
- cultural festival dance
- rare tribal custom
banned: []
```

> Ghi chú: `safe_pool` = tier thematic khi bí footage; `audience_bias` = loại cảnh đổ vào
> slot visual_anchor=false (footage khán giả ưa, KHÔNG phải cảnh chính). User chốt audience
> bias mạnh về "phụ nữ xinh đẹp quốc gia" — giữ trong 2 danh sách này để phễu ưu tiên.

## Điểm ngỏ / lưu ý (P5)

- **CHẠY 2 CỬA SỔ CHAT CÙNG DỰ ÁN → xung đột.** Bug 2026-07-14: 2 cửa sổ chat Claude
  cùng chạy → tool write/bash bị reject giữa chừng. Trước khi chạy ingest/index dài, kiểm
  process sót (memory `leftover-background-job-check`) + tránh mở 2 phiên thao tác cùng lúc.
- Bước 5 ingest + bước 6 pause-dna hay dính 2 bẫy voice của draft editor (name≠file đĩa +
  placeholder path chết `D:/`/`E:/`) — deepsea đã vá bằng resolve theo basename `path`.
  Xem KE_HOACH_NAP_DEEPSEA.md §"Điểm ngỏ" trước khi chạy.
- Draft kiểu "Clip ghép/compound" (timeline chính chỉ 2 clip gộp path rỗng) → HOÃN, xử
  riêng (deepsea bỏ DS1_074 kiểu này).
- Nhạc pool CHUNG mọi niche — editor-learn nạp vào staging, tai chê mới tách pool.
- DNA/pause-DNA chưa có → fail-open về POOLED_DNA (số space) — an toàn, nhưng dựng video
  kiểm sau khi có DNA riêng mới đại diện đúng nhịp niche.

## Tài liệu liên quan

- Quy trình niche mới đầy đủ: `QUY_TRINH_LAY_MAU_SFX_NICHE_MOI.md` (B1→B6).
- Mẫu nạp niche đã đóng: `KE_HOACH_NAP_DEEPSEA.md`.
- Bản đồ mọi điểm hard-code niche trong code: xem báo cáo agent trong phiên 2026-07-14
  (các file chính: `packager/ducking.py` HOOK_DUCK · `ambient/schedule.py` DRONE/HOOK_SFX ·
  `music/plan.py` M_CHANGE_XFADE · `director/live.py` WORLD_LOCK · `library/profile.py`).
