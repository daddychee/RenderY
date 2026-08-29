# MÔ TẢ VẬN HÀNH — C đợt 3b: SFX HOÀN THIỆN (S1 drone + S2 subject-SFX + S3 whoosh)

> Trạng thái: **USER DUYỆT 2026-07-10** với 2 điều chỉnh: (1) subject-SFX TRONG voice
> OK — "editor thật vẫn làm thế", volume đặt **-4dB** trước, cao quá sẽ yêu cầu hạ sau;
> (2) thêm **S4 `editor-learn`**: mỗi lần user đưa project CapCut editor thật mới vào,
> máy phải HỌC + LƯU sfx/music họ dùng để tái sử dụng (yêu cầu đứng lâu dài).
> Bối cảnh: C1 ambient ô thở ĐÓNG (AMBIENT_VOL 0dB). User 2026-07-10: "sfx vào hình thở
> khá ổn nhưng chưa wow — editor thật xem footage đó LÀ GÌ để đưa sfx phù hợp; có nên
> làm nốt các phần sfx còn lại không?"

## 1. Soi PB10: máy còn thiếu gì so với editor

| Lớp editor (PB10) | Máy hiện có? | Đợt này |
|---|---|---|
| 1. Nhạc cảm xúc chồng 2–4 lớp | 1 lớp/chương (hệ nhạc riêng) | **KHÔNG đụng** — đụng hệ nhạc, foundation riêng sau |
| 2. Drone nền chạy SUỐT video 0.05–0.17 | ❌ chưa có | **S1** |
| 3. Ambient khớp cảnh + KHỚP CHỦ THỂ (mặt trời→tiếng sôi) | C1 mới khớp LOẠI CẢNH (14 scene_type), chưa khớp chủ thể | **S2 — cái "wow"** |
| 4. Whoosh chuyển động ×20–30/video | chỉ khi có overlay | **S3** (sau PB11 đo vị trí) |
| 5. SFX UI/data bám đồ họa | ✅ có (track sfx) | giữ nguyên |
| 6. Impact/rumble bám sự kiện | một phần (impact theo overlay) | gộp vào S2 (sự kiện = chủ thể) |

## 2. S2 — SFX theo CHỦ THỂ trên hình (làm trước, vì là cái user muốn)

**Nguồn sự thật "footage đó là gì":**
- Footage **local** → cache.db `subject`+`tags`+`description` (GLM vision đã tag —
  ĐÚNG mô hình editor nhìn hình; vd "sun boiling", "asteroid field", "rocket launch").
- Footage **stock/entity**: ~~`visual_concept` proxy~~ **BỎ sau cổng tai V5 2026-07-10**
  (b22 footage mặt trăng nghe lửa, b56 dung nham nghe nước — concept NÃO tả Ý ĐỊNH,
  không phải footage THẬT đã pick). Stock KHÔNG có tiếng chủ thể cho tới **C5 đợt 5**
  (vision tag pick thật — C5 gánh thêm việc mở lại tầng này).

**Tiếng bám MIẾNG footage (cổng tai V5 — b20 fire tràn sang footage tên lửa, b46 signal
tràn qua mốc kết tàu thăm dò):** ô thở nhiều miếng → tiếng chủ thể DỪNG ở mốc kết miếng 1
(`BreathShot.dur`); beat nhiều shot → tiếng dừng ở mép chia shot 1 (`split_window` dùng
chung với assembler). Tiếng LOẠI CẢNH vẫn phủ trọn ô (các miếng thường cùng cảnh).

**4 luật tinh chỉnh từ cổng tai V7 (user 2026-07-10):**
1. **Ảnh (entity/Ken Burns) KHÔNG SFX** — ảnh đứng yên mà kêu tiếng rocket là sai (b12).
2. **Mặt trời/lava → tiếng lửa CHỈ khi CẬN CẢNH** (`shot_size` ∈ close_up/extreme_close_up
   — vision đã tag sẵn cả 2 bảng); lửa ĐANG CHÁY thật (fire/burning/boiling/flame) thì cỡ
   nào cũng kêu. Editor gốc chỉ đặt tiếng sôi khi quay cận mặt trời. (b18 hệ-mặt-trời-wide
   im · b79 sunrise → tiếng gió sky_cloud · b91 solar-surface-cận giữ sôi · b42 nham NGUỘI
   aerial im.)
3. **Kind `ocean` tách khỏi `water`** — biển cần tiếng SÓNG nhẹ, kind water của kho là
   rót/sôi (b04 biển đêm nghe tiếng rót = sai); kho chưa có file ocean → beat biển IM,
   cần mua "gentle ocean waves" (Artlist).
4. **Volume cả 3 tầng user CHỐT ĐẠT** — WHOOSH_VOL 0.5 / SUBJECT_VOL 0.63 / DRONE_VOL 0.15.
   → **NÂNG CẤP 2026-07-10 (sau V9): volume tiếng chủ thể theo NGỮ CẢNH VOICE** — user
   đề xuất -15dB (có voice) / -10dB (ô thở), PB13 đo 3 draft editor XÁC NHẬN khớp
   (đè voice -11…-15.6dB, không voice -10…-11.6dB — PB10 doc §7). Chốt
   `SUBJECT_VOL=0.18` + `SUBJECT_BREATH_VOL=0.32`; ambient LOẠI CẢNH giữ 0dB (verdict V4).

**Map chủ thể → tiếng: BẢNG TỪ KHÓA controlled-vocab** (v1 deterministic, 0 token, học
bài C4/C6 — không thêm tầng LLM):

| kind mới (kho ambient) | từ khóa match (subject/tags/concept, EN) | nguồn file (43 hold editor) |
|---|---|---|
| `fire` | sun, solar, fire, burning, boiling, lava, flame | lửa, sôi sục mặt trời, boiling water, flamethrower, bonfire (~6) |
| `rocket` | rocket, launch, spacecraft launch, missile, thrust | rocket ignition, rocket launch, rockets missiles (~4) |
| `explosion` | explosion, meteor, impact, asteroid hit, collision | explosion ×2, meteorite storm, fireworks rocket (~4) |
| `rumble` | earthquake, rumble, collapse, debris, avalanche | rumble ×3, earth rumbling, debris avalanche (~5) |
| `water` | water, ocean wave, pouring, rain | pour hot water, boiling water, 水倒入杯中 (~3) |
| `signal` | satellite, signal, transmission, radar | tàu vũ trụ tín hiệu (1) |

Match theo thứ tự bảng, từ khóa là **từ nguyên** (word-boundary, không substring —
"sunset" không ăn "sun"... thực ra ăn: dùng `\b` — "sunset" chứa từ "sunset" ≠ "sun").

**Đặt ở đâu — 2 mức:**
1. **Ô thở (nâng C1):** sửa NGAY TRONG `choose_files` — thêm nấc ưu tiên
   `subject-kind > scene_type > default` (1 chỗ quyết duy nhất, KHÔNG thêm tầng mới đè
   C1). Ô thở chiếu mặt trời sôi → nghe tiếng sôi thay vì drone space chung chung.
2. **Beat thường có match mạnh (TRONG lúc voice — như editor):** 1 tiếng khi chủ thể
   lên hình (đầu beat), dài ≤ min(beat, `SUBJ_MAX=10s`), fade 2 mép, volume
   `SUBJECT_VOL` 🔸 (thấp hơn ô thở — không che voice). **Trần chống loạn** (học
   filter-overload + rải-mềm c8): tối đa `SUBJ_CAP=6`/video 🔸, không 2 beat liền kề,
   mỗi kind ≤2 lần/video; beat chart/info-card/graphic SKIP (đồ họa đang chiếm hình).

Track: đặt chung track `ambient` (bản chất là ambient theo chủ thể); track `sfx` giữ
nguyên vai UI/overlay.

## 3. S1 — Drone nền toàn video

- 1 file kind `drone` chạy suốt video: fade in 2s đầu / fade out 3s cuối, file ngắn hơn
  video thì LOOP nối đuôi (file editor 2–4 phút, video 10–26 phút).
- Chọn file: deterministic crc32 theo tên project (khuôn seed shot thở) — mỗi video 1
  drone, video khác nhau nghe khác nhau.
- Volume `DRONE_VOL` 🔸 khởi điểm **0.15**: quy TƯƠNG QUAN (bài học V4): editor drone
  0.05–0.17 ≈ ngang nhạc họ 0.05–0.1 → nhạc máy lúc voice 0.2 → drone ngang/dưới mức đó.
  KHÔNG ducking riêng v1 (editor chạy phẳng suốt; đã có fade 2 đầu).
- Kho: kind `drone` nạp từ hold (Whoosh Swells dùng cho S3; drone lấy: amvien + vài
  bản deep-space đã có ở kind space → copy sang `drone_n.wav`, file rõ nguồn).

## 4. S3 — Whoosh auto: ĐÃ BỎ TRỌN (PB12, 2026-07-10)

Lịch sử 2 lần lật bằng số đo:
- **PB11** lật "whoosh bám cut" → luật v1 đặt ở chuyển chương + vào ô thở.
- **Tai V7** user bỏ swell chương; **tai V8** user nghi luôn whoosh-vào-ô-thở →
  **PB12 đo**: mốc vào ô thở voice thật của editor vs whoosh — **0/88 whoosh (0% cả
  3 draft)**. Editor KHÔNG BAO GIỜ whoosh khi vào hình thở. 40–70% whoosh của họ bám
  **TEXT hiện lên** (đúng lời user).
- **Hiện trạng:** máy đã có overlay-SFX (text overlay hiện → có tiếng kèm) = nửa mẫu
  editor. **Backlog:** chapter-title card + whoosh/swell đi cùng (khuôn overlay-SFX sẵn);
  kho `swell` ×8 + `whoosh` ×15 chờ. KHÔNG còn whoosh auto nào khác.

## 4a. M3b — vision-tag footage STOCK đã pick (user chốt phương án A, 2026-07-10)

**Vì sao:** tai V6 "3 tiếng chủ thể là ít" — kho local có mắt vision, còn ~70 pick
stock/entity mù → subject-SFX chỉ phủ ~20% beat. Fix đúng nguyên tắc "editor xem footage
LÀ GÌ": GLM-4.6V nhìn frame THẬT của từng pick.

**Cách chạy:**
1. Cuối `run_source` (SAU khi picks + shot thở + C3 chốt): gom `asset_key` stock/entity
   (bỏ `local:`/`chart:`, dedup), bỏ key ĐÃ có trong bảng → tag phần còn lại
   (GLMVisionTagger sẵn có: 960px, chống schema-echo, luật không-đoán tên thiên thể,
   multi-key ≤3 luồng/key). Video 1 frame giữa (<10s) hoặc 2 frame; ảnh entity 1 ảnh.
2. **LƯU VĨNH VIỄN** `cache.db::stock_tags` (asset_key PK → subject/description/
   scene_type/tags/mood/shot_size + model + tagged_at) — pexels/entity id ổn định nên
   video sau tái dùng MIỄN PHÍ, chi phí giảm dần về 0 (~$0.001/asset lần đầu).
3. `db_subject_lookup`/`db_scene_lookup` mở rộng: key `local:` tra library_assets như cũ;
   key khác tra stock_tags — bảng chưa có (db cũ) → "" fail-open y nguyên hành vi hiện tại.
4. CLI `autoedit tag-stock <project>` chạy tay cho project cũ / retag.
- Fail-open MỌI nấc: thiếu GLM key / mất mạng / contentFilter 1301 từng asset → skip +
  warning, pipeline chạy tiếp (asset đó mù như trước).

**Vòng học tương lai (user 2026-07-10 — "editor sửa xong đưa lại cho máy học"):** thiết kế
đã tính sẵn — `project.json` giữ `asset_key` + `ambient_log`/`subject_sfx_log`/`drone_log`
từng beat, draft đặt track tên riêng (`ambient`/`drone`/`sfx`); khi bản editor-sửa quay
lại, S4 `editor-learn` đối chiếu được "máy đặt gì → editor giữ/xóa/đổi gì" và tag trong
stock_tags vẫn tra được theo asset_key. KHÔNG cần làm gì thêm bây giờ.

**Rà chồng chéo M3b:** tag chạy SAU khi picks chốt → không thể lật quyết định phễu/ranker
(và phễu KHÔNG đọc stock_tags — tránh 2-tầng-cùng-quản mood/nghĩa với NÃO rank); C3 so
màu đo code thuần, không đụng; search_cache/asset_usage khác bảng; ambient ô thở HƯỞNG
thêm (pick stock có scene_type → bớt ca "mù tag → default").

## 4b. S4 — `editor-learn`: học SFX + nhạc từ project editor mới (user yêu cầu 2026-07-10)

> **ĐÓNG M5 2026-07-10** — module `autoedit/editor_learn/` (`dna.py` + `mine.py`), lệnh
> `autoedit editor-learn <folder draft> --niche <n> [--dry-run]`, pytest 372/372, chạy
> thật 3 draft SP1 (chi tiết + 2 bug chạy-thật: NHAT_KY §C-DOT-3b-M5).

Đóng quy trình mót-kho thủ công (PB10) thành **1 lệnh lặp lại được**:
`autoedit editor-learn <folder draft editor>` (COPY-only, không đụng file gốc):
1. **Quét DNA âm thanh** `draft_content.json`: đếm lớp (nhạc/drone/ambient/sfx), volume
   từng lớp, whoosh đặt đâu so với cut — cộng dồn vào hồ sơ DNA (PB10/PB11 là bản đầu).
   **Gồm cả DNA volume-theo-ngữ-cảnh-voice (PB13, user 2026-07-10):** SFX đè voice vs
   SFX trong khoảng nghỉ voice, median mỗi nhóm — phép đo đã có sẵn ở
   `autoedit/scripts_phan_tich_pb13_sfx_vol_voice.py`, editor-learn bê vào làm module;
   project mới nạp thêm → số cộng dồn in kèm `SUBJECT_VOL`/`SUBJECT_BREATH_VOL` hiện tại
   để đối chiếu — **CHỈ BÁO CÁO, không tự đổi hằng** (V10 chốt bằng tai; luật đứng:
   volume chỉ đổi khi user yêu cầu). Hồ sơ: `F:\AutoEdit\editor_dna.json` (1 entry/draft,
   học lại cùng draft = thay entry, không cộng đôi).
2. **Mót file audio**: phân loại theo luật (voice/music/ambient/sfx/hold — luật đã dùng
   PB10) → sinh manifest cho `ambient-import`/`sfx-import`; **nhạc COPY về staging
   `F:\AutoEdit\music_editor\<tên project>\`** (KHÔNG vào pool chọn nhạc — tránh lật hệ
   nhạc mood; user gọi thì nạp). Chốt khi làm: **danh tính file = TÊN MATERIAL** (SFX
   kho CapCut nằm trên đĩa dưới tên hash md5 — copy ra kho mang tên material); "Clip
   ghép" (compound clip — chứa voice trộn sẵn) skip như voice; dedup 2 chiều stem vs
   records/manifest chờ/hold/staging; nhạc trùng giữa các draft giữ 1 bản.
3. **Báo cáo**: học được gì mới (file mới/kind mới/số DNA lệch bản cũ) + lệnh nạp tiếp.

Cổng: pytest + regression — chạy lại trên 3 draft SP1 phải ra ĐÚNG số PB10 đã biết.
✅ ĐẠT: PB13 (nhạc 0.10/0.09/0.06 · đè-voice 45·0.25/33·0.28/33·0.17 · không-voice
1·1.00/1·0.26/12·0.32) + PB11 (whoosh 40/25/23 · cut 120/232/263 · sát-cut 10/5/7 ·
cut-trong 17/12/4 — INCLUSIVE a≤c≤b, hiệu chuẩn mới ra). Pooled 3 draft: voiced 0.24
(-12,3dB) / novoice 0.32 (-9,9dB) — số máy V10 nằm giữa dải editor.

**Rà chồng chéo S4 (P5):**

| Tầng CÙNG QUẢN | Ngược chiều? | Ai lật ai? |
|---|---|---|
| Thư viện ambient (C1/S2 đọc `list_variants`) | Không | file thô copy vào folder niche CHƯA chuẩn hóa — `list_variants` khớp chặt `^kind(_n).wav$` không nuốt; tên đụng khuôn → tiền tố "editor - " (guard + test). Chỉ khi user chạy `ambient-import` file mới thành biến thể |
| Kho SFX (overlay/chart rotation) | Không | file vào staging `sfx\tu_editor\` RIÊNG, ngoài glob `<kind>*.wav` của SFX_ROOT; chỉ `sfx-import` mới nạp |
| Hệ nhạc (mood/select) | Không | staging `music_editor` NGOÀI pool `~/AutoEdit/music` — music select không nhìn thấy; user gọi mới nạp (đúng chủ đích tránh lật hệ mood) |
| Volume đã chốt V10 (SUBJECT_VOL/BREATH/DRONE/AMBIENT) | Không | editor-learn CHỈ in đối chiếu, không ghi hằng — không tầng nào âm thầm đổi mix |
| Draft editor gốc | Không đụng | ĐỌC-only + copy ra; không ghi 1 byte vào folder draft (test COPY-only snapshot) |
| Pipeline dựng video | Không đụng | module mới 0 consumer; 360 test cũ xanh nguyên |

## 5. Tham số (🔸 = tai user chốt ở cổng TAI V5)

| Tham số | v1 | Ghi chú |
|---|---|---|
| `SUBJECT_VOL` | ~~0.63 (-4dB)~~ → **0.18 (-15dB)** — user đặt + PB13 xác nhận, sau V9 2026-07-10 🔸 | tiếng chủ thể TRONG voice; editor thật đè voice -11…-15.6dB (PB10 §7) |
| `SUBJECT_BREATH_VOL` | **0.32 (-10dB)** — user đặt + PB13, 2026-07-10 🔸 | tiếng chủ thể THẮNG Ô THỞ (không voice); editor -10…-11.6dB; ambient LOẠI CẢNH vẫn 1.0 (V4) |
| `SUBJ_MAX` | 10s 🔸 | editor đặt khúc 5–35s; máy v1 gọn hơn |
| `SUBJ_CAP` | 6/video 🔸 | + không liền kề + ≤2 lần/kind |
| `DRONE_VOL` | **0.15** ✅ | user DUYỆT cổng tai V5 2026-07-10 ("drone nền suốt video: ok duyệt"); quy tương quan PB10, KHÔNG bê số tuyệt đối (bài học V4) |
| `AMBIENT_VOL`/`AMB_MIN`/`AMB_FADE` | 1.0/3.0/1.0 | ĐÃ CHỐT V4 — không mở lại |

## 6. Rà chồng chéo (P5) — các tầng CÙNG QUẢN âm thanh

| Tầng | Ngược chiều? | Ai lật ai? |
|---|---|---|
| **C1 ambient ô thở** | Không | S2 mức-ô-thở sửa TRONG `choose_files` (thêm nấc ưu tiên) — 1 chỗ quyết, không có tầng thứ 2 âm thầm đổi file. Note ghi rõ "subject 'fire' thắng scene 'space'" trên report |
| **Ducking F8 / nhạc nở 0.5** | Không | S2-trong-voice + S1 drone là lớp MỚI cộng vào mix → rủi ro duy nhất = TỔNG MỨC ÂM (voice + nhạc 0.2 + drone 0.15 + subject 0.7 cục bộ) — giao cổng TAI V5; núm chỉnh: SUBJECT_VOL, DRONE_VOL (2 số mới), KHÔNG đụng 3 số đã chốt |
| **SFX overlay/chart (track sfx)** | Không | khác track, khác vai (UI vs môi trường); beat có đồ họa thì S2 SKIP nên không bao giờ kêu đè nhau |
| **Voice** | CÓ RỦI RO | S2 kêu TRONG lúc nói — đỡ bằng: volume thấp + fade + trần 6 + word-boundary match (không match nhầm) + skip beat đồ họa. Tai V5 phán cuối |
| **Shot thở / phễu footage / c8 viral** | Không đụng | chỉ ĐỌC picks + cache.db; 0 filter mới vào phễu ([[filter-overload-guard]] sạch) |
| **Hệ nhạc (chọn bài/crossfade)** | Không đụng | drone là track riêng; nhạc chồng-lớp KHÔNG làm đợt này |
| **Report/editor** | Không | thêm bảng "SFX chủ thể + drone" — editor tắt được từng clip trong CapCut |

Kết luận rà: không tầng nào bị lật; 2 điểm giao tai người = tổng mức âm + subject-SFX
trong voice có che lời không.

**Rà bổ sung cho nâng cấp volume-2-ngữ-cảnh (2026-07-10, sau V9):** (1) verdict V4
"ambient 0dB" KHÔNG bị lật — chỉ tiếng CHỦ THỂ thắng ô mới xuống -10dB, loại CẢNH giữ
0dB (điều kiện `used_kind == subject_kind` — cùng điều kiện với luật cắt-theo-miếng-1,
1 ngữ nghĩa); (2) tầng có thể ÂM THẦM NUỐT tiếng mới = **nhạc nở 0.5 trong ô thở**
(-10dB = 0.32 < 0.5) và **nhạc 0.2 khi voice** (-15dB = 0.18 ngồi ngang nhạc) — editor
mix được vì nhạc họ chỉ 0.06–0.10; nếu tai V10 nghe chìm thì núm chỉnh là NHẠC, không
nâng SFX ngược lại; (3) 2 ô thở cùng video giờ có thể lệch loudness (cảnh 0dB vs chủ
thể -10dB) — chủ đích theo số PB13, tai V10 phán.

## 7. Milestones (P4)

| Milestone | Nội dung | Cổng |
|---|---|---|
| **M0** | Nạp 43 hold vào kinds mới (manifest máy sinh, user không phải tải gì) + PB11 đo whoosh | pytest import + số PB11 |
| **M1** | S1 drone bed (loop + fade + seed) | pytest |
| **M2** | S2 subject-SFX (bảng map + 2 mức đặt + trần + report) | FULL pytest |
| **M3** | Re-assemble SP012 → **draft V5** (so thẳng V4) | 👂 cổng TAI: chốt SUBJECT_VOL/DRONE_VOL/trần |
| **M3b** | Vision-tag pick stock (bảng `stock_tags` + wire source + CLI `tag-stock`) — user chốt A 2026-07-10 | pytest + tag thật SP012 |
| **M4** | S3 whoosh theo luật PB11 — GỘP M3b+M4 vào **draft V7**, 1 lần nghe | 👂 cổng TAI V7 |
| **M5** | S4 lệnh `editor-learn` (quét DNA + mót file + manifest, COPY-only) | pytest + regression 3 draft SP1 ra đúng số PB10 |
