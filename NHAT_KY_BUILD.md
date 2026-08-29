# NHẬT KÝ BUILD — TOOL EDIT PADOMA

> **Nguồn sự thật tiến độ.** Sau mỗi milestone/feature/fix: cập nhật bảng + thêm 1 entry.
> Chỗ lệch PRD → tin file này. Đọc kèm: `CLAUDE.md` (nguyên tắc), `BAN_DO_TRI_THUC.md` (nguồn code).

---

## Bảng milestone

| # | Nội dung | Trạng thái | Test | Ngày |
|---|---|---|---|---|
| Phiên 0 | Dựng khung nền + bản đồ tri thức | ✅ ĐẠT | — (chưa code) | 2026-07-01 |
| Phiên 1 | Bàn hướng đi + chốt roadmap Phase A–E (ghi PRD) | ✅ ĐẠT | — (design) | 2026-07-01 |
| A0 | Copy autoedit→padoma làm codebase mới + setup env | ✅ ĐẠT | 145/146 (1 Mac-only) | 2026-07-01 |
| A1 | Port Mac→Windows (path/textutil/osascript) | ✅ ĐẠT | 146/146 + register-machine OK | 2026-07-01 |
| A2 | demo-draft + port C1–C5 nếu cần | ✅ ĐẠT | cổng mắt: user OK | 2026-07-01 |
| A3 | make 1 video ngắn end-to-end | ✅ ĐẠT | cổng mắt: user "project này đã tốt" (draft SAMPLES_20260701_094253 + report.html) | 2026-07-01 |
| B1 | direct qua Claude Code (subscription, bỏ API key) | ✅ ĐẠT | pytest 151/151 + direct thật exit 0 (3 chương/8 beat) | 2026-07-01 |
| B2 | Buồng lái hội thoại L2b (skill /dung-video) | ✅ ĐẠT | editor thử thật: dựng trọn 1 hook tiếng Việt Pha1+2 OK | 2026-07-01 |
| B3 | Fix bug SegmentOverlap 1µs (assemble) — video tiếng Việt "hook Ai Cập" chạy trọn Pha 1+2 | ✅ ĐẠT | pytest 15/15 assembler (+1 regression) · draft CapCut sinh OK | 2026-07-01 |
| F0 | Chốt HỆ THỐNG FOUNDATION: danh mục 17 file + khuôn 5 phần + lộ trình 5 bước (design, chưa code) | ✅ ĐẠT | — (user chốt 4 câu hỏi; ghi chép gốc lưu `foundation/GHI_CHEP_GOC.md`) | 2026-07-02 |
| F1 | Foundation đợt 1: d1-pacing + d2-hinh-tho (bản sửa 2 pha + sàn) + b1-mood-tone | ✅ ĐẠT | cổng mắt: user duyệt cả 3 file (2026-07-02) | 2026-07-02 |
| F2 | Foundation đợt 2: c5-loc-xep-hang ✅ DUYỆT (4 nguyên tắc phễu ĐÓNG BĂNG) → c2-an-du-veto ✅ DUYỆT → c7-shot-variety ✅ DUYỆT (bản sửa: góc máy chỉ-cộng) | ✅ ĐỢT 2 XONG | cổng mắt: user duyệt cả 3 file (2026-07-02) | 2026-07-02 |
| F3 | Foundation đợt 3 — khép NHÓM C: c1 ✅ → c4 ✅ → c3 ✅ → c6 ✅ DUYỆT bản gọn-1-luật (10/18 foundation xong, spec phễu ĐỦ) | ✅ ĐẠT | cổng mắt: user duyệt cả 4 file (c6: 2026-07-03) | 2026-07-03 |
| F4 | MÔ TẢ VẬN HÀNH khung phễu c5 (`MO_TA_VAN_HANH_PHEU_C5.md`) | ✅ ĐẠT | cổng mắt: user DUYỆT mô tả 2026-07-03 | 2026-07-03 |
| F5 | CODE khung phễu c5 (M1 ranker + M2 nối sourcer) + giảm ảnh (Lớp 1 video-first routing + Lớp 2 sàn phân giải) | ✅ ĐẠT | pytest 178/178 · re-run Ai Cập: 17/17 VIDEO 0 ảnh (trước 12 ảnh mờ) · **cổng mắt: user duyệt draft _V3 (2026-07-03)** | 2026-07-03 |
| F6 | shot_count: nhiều footage/beat (mô tả duyệt → code 3 chỗ chạm + fix bug đè-tên-file) | ✅ ĐẠT | pytest 187/187 (10 mới) · draft _V5: 19 segment, tiling khít, timeline không đổi · **cổng mắt: user duyệt V5 (2026-07-04)** | 2026-07-04 |
| F7 | Foundation đợt CUỐI: viết hết 8 file còn lại trong 1 đợt (a1 chia beat · a2 chức năng đoạn · a3 open loop · b3 pattern interrupt · d3 loại cắt · e1 sound design · f1 text/typo · f2 ken burns) → **18/18 foundation HOÀN TẤT** | ✅ ĐẠT | **cổng mắt: user DUYỆT cả 8 file (2026-07-04)** | 2026-07-04 |
| F8 | Ducking keyframe (backlog 1 của e1): mô tả DUYỆT → M1 test v2 (RAMP 2.5s theo user) → M2 `ducking.py` + wire → V6 **user bắt lỗi keyframe không hiện** → điều tra (REAL73 + ma trận v3): `time_offset` tính theo SOURCE, không phải đầu clip → fix cộng src0 → **_V7** | ✅ ĐẠT | pytest **196/196** · **cổng mắt+tai: user duyệt V7 (2026-07-04)** — chấm keyframe hiện đúng 6-8s + nghe phồng cả 2 chỗ; 4 tham số giữ v1 (0.2/0.5/2.5s/1s) | 2026-07-04 |
| F9 | **L2b sâu** (lộ trình F0 bước 3): phiên sống đọc 12 foundation nhóm đạo diễn thay prompt cứng — mô tả vận hành `MO_TA_VAN_HANH_L2B_SAU.md` (3 mảnh: direct-context → phiên đạo diễn → direct-ingest gác) + **RÀ CHỒNG CHÉO logic toàn pipeline theo yêu cầu user: tìm 4 mâu thuẫn thật (§4b), gói vá M0** | ✅ TRỌN BỘ M1+M0+M2+M3+M4 — cổng mắt beats ĐẠT + **cổng mắt draft CapCut ĐẠT (user duyệt 2026-07-04)**. Video travel Thụy Sĩ end-to-end bằng đường sâu: draft `SCRIPT_20260704_041750` | 206/206 (M2 thêm 7) | 2026-07-04 |
| P5 | **Luật mới vào CLAUDE.md:** nguyên tắc hành động P5 "Rà chồng chéo & vùng ảnh hưởng" — mô tả vận hành phải có mục rà chồng chéo; trước mọi fix phải grep consumer + cùng-pattern; mỗi fix có regression test + full suite | ✅ ĐẠT | — (luật, không code) | 2026-07-04 |
| PB1 | **Phase B mở màn** (lộ trình F0 bước 4): GOM phần 5 của 18 foundation thành spec schema tag GLM — `MO_TA_VAN_HANH_TAG_GLM.md` (schema 8 field GLM + 4 nhóm field code-thuần, mood dùng chung 19 vocab nhạc, GLM-4.6V native thay haiku, mẻ thử trước đại trà, rà chồng chéo 8 tầng, lộ trình PB1–PB5) | ✅ ĐẠT — user duyệt spec + xác nhận vision GLM-4.6 (đã chạy thành công ở project nhan ban) | — (spec) | 2026-07-04 |
| PB2 | **Code schema tag mới + GLMVisionTagger**: `vision.py` (AssetTags mới + GLM native tagger + đo màu code thuần) · `db.py` (5 cột mới + migrate + luật re-tag thiếu scene_type) · `indexer.py` (frame rút 1 lần, màu fail-open) · `cli.py` (`--engine glm\|claude` + `--angle`) · GLM_API_KEY vào .env | ✅ ĐẠT — user xác nhận bằng cách giao folder nguồn PB3 | pytest **215/215** (9 mới) + smoke GLM thật 1 call tag đúng schema | 2026-07-04 |
| PB3 | **Mẻ thử tag niche `space`** (nguồn `E:\PROJECT NHAN BAN\SPACE 1\SP1 - 003\materials`, draft đọc-only): 46 file chọn tay → 5 folder con tiếng Việt trong `~\AutoEdit\library\space` → tag GLM-4.6V `--angle` **46/46 vào db**. Tìm ra + fix 2 bug hạ tầng: **(B1) GLM schema-echo** (chép nguyên schema thay vì tag, ngẫu nhiên theo call dù temp=0 — fix 2 lớp chống echo vào `vision.py` + regression test) · **(B2) song song 1 key bị bigmodel cắt kết nối** (fix: frame 960px + 3 luồng/key + so le + **multi-key** `GLM_API_KEY_2..9` round-robin — user cấp 2 key). **Cost thật: ~$0.0016/asset** (2.376 in/101 out) · 13,7s/asset @ 3 key 9 luồng | ✅ ĐẠT — **cổng mắt: user duyệt PB3 (2026-07-04)**; camera_angle theo luật c7 + số liệu yếu → KHÔNG tag đại trà (flag `--angle` giữ cho mẻ thử sau) | pytest **216/216** (1 regression chống echo) | 2026-07-04 |
| PB4 | **Ống nạp draft CapCut + đa luồng vào production**: `ingest.py` (đọc `draft_content.json` ĐỌC-ONLY → cắt ffmpeg theo mép editor + C4 `-an` → tag → db cột §3b `source_video/scene_start/scene_index/has_voice/duration/wxh/fps`) · `indexer.py::tag_jobs` (3 luồng/key, multi-key round-robin, SQLite main thread) · `vision.py` (shrink 960 fail-open TRONG tagger, `glm_api_keys`, video <2s = 1 frame, **feedback-retry** nhét lỗi validation cho GLM tự sửa, 400 hiện body) · mood validator dịch qua `_MOOD_SYNONYMS` nhạc · CLI `library-ingest` (+`--dry-run`) · **CHẠY THẬT SP1 - 003: 237 cảnh cắt (999MB) / 236 tag vào db** — 1 clip aliens bị bigmodel contentFilter 1301 chặn vĩnh viễn | ✅ ĐẠT — **cổng mắt: user duyệt 2 đợt (2026-07-06)**: "cắt đúng cảnh, mượt" + duyệt các mục còn lại; xác nhận cảnh cắt từ đúng project nguồn của user | pytest **229/229** (13 mới) | 2026-07-06 |
| PB5 | **Thống kê DNA đợt 1** (0 token, chạy lại được khi thêm draft): `library/dna.py::compute_dna` (d1 pacing: cut/phút + phân bố shot + hold ≥5s + 4 khúc vị trí + 45s đầu · d2 thở: ô = voice trống ≥1s, tần suất/độ dài/footage/chuỗi · c7: % cỡ cảnh + nhịp đặc tả + chuỗi 3-shot · c6: scene_type/subject lặp + hook mở) + `ingest.read_timeline` + `DraftScene.target_start/duration` + CLI `library-dna`. **Chạy thật space**: bảng `PB5_DNA_SPACE.txt` — 8,3 cut/phút, trung vị shot 7s, hold 81%, 1,47 ô thở/phút thoại (trung vị 1,5s), wide 79%, 1 close-up/39 shot, chữ ký galaxy/nebula/stargazing | ✅ ĐẠT — **cổng mắt: user duyệt PB5 (2026-07-07)**. Phase B đợt 1 (PB1→PB5) ĐÓNG TRỌN | pytest **231/231** (2 mới) | 2026-07-07 |
| PB6 | **Giảm frame vision** (user chốt 2026-07-07, sửa spec §3a): video **<10s = 1 frame GIỮA clip**, ≥10s giữ 2 frame (khoảng 10–15s xếp bên 2 frame cho an toàn). Đo thật 1-frame: **1.307 in/79 out ≈ $0,00093/asset (rẻ hơn 42%)**. So sánh mù 24 cảnh đủ dạng vs tag 2-frame cũ: scene_type 19/24 · shot_size 23/24 · has_people 24/24 · mood giao 23/24 → `PB6_SO_SANH_1FRAME.html` (lệch tô đỏ) | ✅ ĐẠT — **cổng mắt: user duyệt PB6 (2026-07-07)**: "footage khớp >90% so với gọi 2 frame" — luật 1-frame chính thức chạy cho mọi mẻ nạp sau | pytest **231/231** | 2026-07-07 |
| PB7 | **Vá duration local→phễu** (phiên tự động 4h, user cho phép làm trước duyệt sau): `sourcer/local.py::_row_to_candidate` mang `duration` từ db vào ứng viên — trước đây bị đánh rơi → cửa clip-quá-ngắn (`MIN_DURATION_RATIO`) + điểm khớp-độ-dài (`DURATION_BONUS`) của phễu c5 MÙ với footage local (Pexels thì có). Né bẫy loại-oan: asset cũ duration=0/NULL → KHÔNG gắn key | ✅ ĐẠT — **user duyệt 2026-07-08** | pytest **233/233** (2 regression mới) | 2026-07-07 |
| PB8 | **Đo khớp query director ↔ tag GLM kho space** (phân tích read-only 0 token, phiên tự động): 24 query giả lập tier specific qua phễu thật → trúng 16/24; 8 trượt = 2 loại: kho thiếu cảnh thật (rocket/moon/aurora... — Pexels vớt, đúng vai trò) + **từ chuyển-động ("rotating"/"timelapse") AND-trượt oan vì GLM tag frame TĨNH** → bài học prompt director khi dựng video space, KHÔNG sửa code. Kèm: đóng còn-ngỏ PB4 (clip aliens tag TAY qua ống production → kho nạp **237/237**; phát hiện ⚠ ANTHROPIC_API_KEY hết hạn 401) + nháp `MO_TA_VAN_HANH_DNA_D1.md` chờ duyệt | ✅ ĐẠT — **user duyệt 2026-07-08**; khoảng trống c4 chuyển thành việc kế tiếp (§C4) | — (phân tích, không code) | 2026-07-07 |
| PB9 | **Đợt nạp 2 kho space** (user giao 2026-07-07): SP1-001 **125/125** + SP1-004 **257/257** → kho space **665 asset** (3 draft + folder rời). 3 cảnh GLM chịu thua (SSLEOF dai + validation 4-retry) tag TAY qua ống production (tiền lệ PB4). Sự cố job nền phiên cũ chạy đôi SP1-001 — db không hỏng (UNIQUE path + resume), memory `leftover-background-job-check`. DNA 3-draft `PB9_DNA_SPACE_3DRAFT.txt` + **dna.json tự sinh** (code DNA-D1.B). So PB5: ổn định cut/phút·trung vị ô thở; đổi mạnh wide/close-up; **hook ĐẢO CHIỀU** (n=6→25); std shot từng VỠ vì mega-segment 839s → **user chốt luật: shot >30s bỏ qua không đếm (mọi niche)** — `MEGA_SHOT_S` + đếm riêng + regression; DNA sạch: **std 3,09s · 9,4 cut/phút** | ✅ XONG — user đã quyết outlier; còn đọc so sánh chi tiết khi rảnh | pytest **240/240** (1 regression mega-segment) | 2026-07-07 |
| DNA-D1.B | **Consumer DNA đầu tiên — đợt 1 (Mảnh B)**: `MO_TA_VAN_HANH_DNA_D1.md` DUYỆT (câu 1-2 user: ≥3 draft + DNA niche thắng heuristic; câu 3-4 ủy quyền: giữ ngưỡng §2c + B trước A sau) → code: `dna.py::save_dna/load_dna/check_pacing` · `library-dna` ghi `dna.json` (đóng còn-ngỏ (4) PB5) · `Project.niche` + run_source ghi (NT1) · assembler gom shot THỰC ĐẶT → `_warn_pacing_dna` cảnh báo vào record.warnings/report (fail-open, không bao giờ chặn assemble). Chi tiết §DNA-D1.B | ✅ ĐẠT — **cổng mắt qua 2026-07-08** (user xem SPACE-E2E, phán OK). Mảnh A đợt riêng (mở được sau c4) | pytest **239/239** (6 mới + 2 assert) | 2026-07-07 |
| PA-BATCH | **Phễu c5 chấm batch** (user chốt sau khi DỪNG run 65s/beat: "làm luôn PA 1+2+3, sonnet thôi, tắt thinking"): PA-1 gom ≤10 beat stock/local liền nhau cùng chương → 1 call NÃO (`rank_batch`/`rank_beat_prescored`, fallback 2 nấc về per-beat) · PA-2 `MAX_THINKING_TOKENS=0` chỉ đường rank + ly_do ≤12 từ + sonnet trần · PA-3 pool ≤1 auto-pick 0 call. Run thật verify: **112 beat = 12 call · 0 fallback · ~89-91 tok/verdict (trước ~195) · ~25s/beat (trước 65s)**. Chi tiết §PA-BATCH + `MO_TA_VAN_HANH_PHEU_BATCH.md` | ✅ ĐẠT cổng số — chất lượng chọn soi chung cổng mắt SPACE-E2E | pytest **245/245** (4+1 mới) | 2026-07-07 |
| SPACE-E2E | **Video space đầu tiên trọn ống L2b sâu + phễu batch** (input `D:\SPACE 3 - 007`, 112 beat/3 chương): source 112/112 (0 needs_human, veto nghĩa 9%) → assemble draft `SCRIPT_VOICE_20260707_132450` (3 slow-mo b29/b49/b69, nhạc 3 chương, 14 overlay) → report.html. **Validator DNA Mảnh B nổ lần đầu: im ĐÚNG** (std 1,92 ≥ sàn 1,55; 10,5 cpm trong [4,7–18,8]). Quan sát: local chỉ 9/112 — bước THU không thấy local (44 vs 1685 ứng viên), đúng khoảng trống c4 đã hoãn. Chi tiết §SPACE-E2E | ✅ **cổng mắt ĐẠT (user duyệt 2026-07-08)** — footage/slow-mo/DNA đều OK (đã xem qua V5→V7 nhiều lần) | — (run thật) | 2026-07-07 |
| HINH-THO-2 | **Hình thở 2.0 đợt 1** (user duyệt phân tích SP1-003 + chốt "code luôn"): giãn nghỉ máy `cutter/pause.py` (2 khóa an toàn nghĩa câu: dấu câu `.?!` + nghỉ thật ≥0,3s; ~1,9 điểm/phút, δ 0,4–0,7s, 0 call NÃO) + J-cut `coverage.apply_j_cuts` (ô thở ≥1,2s: shot kế vào sớm 0,3s trước voice — mẫu 14/18 SP1-003). Field mới `micro_pause_after` tách khỏi breathing đạo diễn; ducking/validator/total_end rà đủ (MO_TA_HINH_THO_2 §4). Chạy thật Jupiter: 18 điểm giãn +11,1s, 6/6 mẫu đúng kết câu; 15/15 J-cut đúng resume−0,3s → draft `SCRIPT_VOICE_20260707_132450_V2` | ✅ đóng — cổng TAI đợt 1 "đạt một phần" → nâng cấp thành HINH-THO-3 (đã ĐẠT trọn) | pytest **254/254** (9 mới) | 2026-07-08 |
| HINH-THO-3 | **Hình thở 3.0** (`MO_TA_VAN_HANH_HINH_THO_3.md` user DUYỆT): HỌC DNA nhịp nghỉ 3 project (464 điểm cắt + 52 ô thở, tự đối chiếu script gốc 95% verified → `pause_dna.json`) → `cutter/pause.py` viết lại: **quantile-rank mapping** thay top-N (K=4,9 câu + 1,6 mệnh đề/phút, δ theo rank nghỉ nguồn trên anchor DNA p10–p90, 2 khóa an toàn giữ nguyên, trần 15% — 13% bóp chết tầng mệnh đề vì voice ta nghỉ nền nông hơn TTS editor ~0,35s) + NÃO 0 call: `rhetorical_pause` câu đinh ≤1/chương + hướng dẫn thở "ÍT nhưng SÂU" · chồng chéo sửa cùng: ducking MIN_BREATH 1,5 + funnel `_need_dur`. Jupiter: 49+13 điểm, **nghe-ra câu p50 1,55 = DNA editor trùng số**, mệnh đề 0,95 = DNA, +14,3% → draft **V5** | ✅ ĐẠT TRỌN — cổng số §6 + **cổng TAI user ĐẠT (2026-07-08)** | pytest **258/258** | 2026-07-08 |
| SHOT-THO | **Shot thở — footage riêng cho ô hết ý/cuối chương** (`MO_TA_VAN_HANH_SHOT_THO.md`; user chỉ ra sau khi xem V5 + DNA xác nhận ~25% ô editor: giữ 0,4–0,9s → CẮT sang footage khác im lặng 1–5s; **đính chính** kết luận cũ "ô sâu không footage riêng" = style riêng SP1-003): ngưỡng ô ≥2,5s mọi nơi / ≥1,5s cuối chương / beat cuối video không · giữ hình 0,5s rồi cắt, shot thở phủ tới ĐÚNG mép voice kế (bỏ J-cut tại ô này — **luật lật có chủ đích** của rà 2026-07-04 #1) · chọn MÁY THUẦN 0 call từ kho local: cùng mood clip trước +2/tag, khác cỡ cảnh +1, đủ dài +1,5, chưa dùng +0,5, wide/aerial +0,5, chỉ cộng điểm không cửa loại · `BreathShot` vào project.json (NT1/NT5) · funnel need_dur: ô ≥2,5 chỉ cần thoại+0,5 (hết giết oan clip ngắn). Jupiter: **7/7 ô pick** (6/7 khớp mood; b105 mood sad kho không có → rơi về cỡ cảnh) → draft **V6** | ❌ **cổng MẮT V6: CHƯA ĐẠT nghĩa "thở"** (footage ~2s, 100% 1 footage) → SHOT-THO-2 | pytest **270/270** (12 mới) | 2026-07-08 |
| SHOT-THO-2 | **Shot thở 2.0 — kéo sâu ô 4–10s + đa dạng 1–3 miếng** (MO_TA_SHOT_THO §6; user chốt footage 4–10s + tách DNA voice-nghỉ/hình-thở 2 LỚP RIÊNG, cách làm giao Claude): gốc rễ = NÃO cho breathing bậc 0,5 trần 3,0 trong khi ô editor chạy 2,4→12,3s (**4 ô 8,4–12,3s từng bị lọc nhầm "nhiễu ≥8s"**) · `plan_breath_depth` quantile-map ở CUT (NÃO quyết chỗ + rank thô, máy map độ sâu lên `pooled.breath` của niche, fail-open hằng space) · **bẫy idempotent**: `Beat.breathing_base` — mỗi cut reset về số NÃO gốc rồi mới plan · 1–3 miếng theo ngưỡng + seed crc32 (KHÔNG hash() — bị salt) + guard pool thiếu clip dài → nâng k · miếng 2/3 chấm mood NỐI với miếng trước (chuỗi) · miếng cuối luôn chạm mép voice kế (nuốt pick hụt giữa chừng) · fix luôn **bẫy tên draft điền-lỗ-trống** (cắn 2 lần): version = max+1 + regression. Jupiter re-cut: 7 ô → 4,5–9,0s (+25,9s video), re-pick **9 miếng/7 ô** (b008 2 miếng 4,2+3,0 · b063 đơn 8,5s · b105 2 miếng) → draft **V7** | ✅ cổng số ĐẠT (7/7 ô đúng miếng/mép/file/thứ tự ±1 frame · 8/8 ô nông giữ J-cut · 129 segment 0 hở · +25,9s đúng kéo) + ✅ **cổng MẮT user DUYỆT V7 (2026-07-08)** + cổng TAI hình thở 3.0 ĐẠT (2026-07-08) — cụm hình thở/shot thở ĐÓNG TRỌN | pytest **278/278** (8 mới) | 2026-07-08 |
| C4 | **C4 từ vựng kho — controlled vocabulary cho query local** (mở từ khoảng trống SPACE-E2E: kho 665 asset nhưng THU chỉ 44 vs 1685 Pexels, local thắng 9/112; PB8: trượt oan vì query "ngôn ngữ Pexels" + từ chuyển động, GLM tag frame tĩnh). Thiết kế 3 mảnh 0 call thêm: (1) direct_context.md chở khối TỪ VỰNG KHO (db.vocab_for_niche: scene_type + top tags/subject kèm đếm + 3 lời dặn) · (2) tách `queries.local` khỏi specific (schema + validator ≤4 từ, optional fail-open) · (3) local.py match tier local trước (broad/thematic vẫn cấm — giữ bài học 20/06, geo-gate nguyên) + **vá bug niche rơi**: lệnh `source` đứng riêng không --niche → local/signature/shot thở TẮT IM LẶNG (skill Pha 2 gọi đúng kiểu này) → fallback `inputs.channel` + đếm local-hit vào report. `MO_TA_VAN_HANH_C4_TU_VUNG.md` | ✅ mô tả DUYỆT + **M1 CODE XONG** (7 file; smoke: context in từ vựng kho 665 asset) + **M2 CỔNG SỐ ĐẠT** (same-input, same-beats với baseline: local vào pool **15→45 beat (3×)** · ứng viên local **44→178 (4×)** · kho thắng **9→15 pick** · Pexels 1685→1645 · needs_human 0 · fallback niche C4 nổ đúng production · DNA validator im ĐÚNG, dna.json load từ F:) → draft `SCRIPT_VOICE_20260708_070124` + ✅ **M3 CỔNG MẮT ĐẠT (user duyệt 2026-07-08**: 15 pick local OK · b109 slow-mo OK · draft mở từ kho F: OK**) — C4 ĐÓNG TRỌN M1+M2+M3** | pytest **285/285** (7 mới) | 2026-07-08 |
| KHO-F | **Move kho footage C:→F:** (user chốt trước đợt nạp viral): robocopy 699 file/4,4GB → `F:\AutoEdit\library` (0 fail, verify từng file) · `set-library-root` (machine.json — mọi consumer qua `resolve_library_root`, rà đủ: source/assemble-DNA/pause_dna/breath/library-*) · db update **665 path + 55 usage key** (REPLACE prefix; folder_path tương đối không đụng — geo-gate an toàn) · verify: search/dna.json/pause_dna load từ F: OK, 0 file chết · bản C: backup `library.pre-F-backup` **ĐÃ XÓA 2026-07-08** (sau M3 đạt, parity 698 file/4,41GB) · cache.db + music/sfx vẫn ở C: (nhẹ) | ✅ XONG — assemble M2 chạy sau move đọc DNA từ F: bình thường | — (hạ tầng, verify tay từng bước) | 2026-07-08 |
| C8-VIRAL | **Luật bản quyền cắt nguồn viral → foundation c8** (user giao nguyên văn 2026-07-08, TRƯỚC mẻ nạp viral): 5 luật — miếng ≤10s/chuẩn 6s · tách tiếng (✅ PB4 có sẵn) · cấm 2 cảnh liền kề 1 nguồn/1 video · zoom mất logo/chữ · trần 8%/nguồn/video + rải nguồn. Chưng cất `foundation/c8-cat-nguon-viral.md` (file 19, nhóm C) + nguyên văn vào GHI_CHEP_GOC §BỔ SUNG. Phân rã: 2 gói code — **gói NẠP** (bóp 6s giữa + crop-zoom ~112% nướng + db source_class/source_duration) PHẢI xong trước mẻ nạp; **gói CHỌN** (gate liền kề cạnh P7 + trần 8% cộng dồn mọi đường dùng + điểm rải mềm = rank, không veto chất lượng mới). **Fail-safe: viral chưa có gate → không vào pool.** User chốt cùng ngày: (a) "2 frame liên tiếp" = 2 cảnh kề trong NGUỒN, cấm cùng xuất hiện DÙ ĐẶT XA NHAU trên timeline mình (gate ở phễu); (b) **luật 6 mới — sàn 2s:** cảnh CapCut tách <2s bị BỎ tại ống nạp TRƯỚC vision (áp mọi mẻ nạp) | ✅ foundation GHI XONG (5+1 luật, 0 câu hỏi mở) — gói NẠP đã code: xem C8-NAP; gói CHỌN còn ⏸ | — (luật) | 2026-07-08 |
| SP012-E2E | **Video space #2 fresh direct trọn đường sâu** (input `F:\SPACE\Voice + content SP012` — bài "Far side of the Moon" 23,5 phút/3.233 từ): ghép 4 mp3 → voice.mp3 · new --channel space · align · direct-context lần đầu đủ CẢ từ vựng kho (C4) + chữ ký pacing (DNA Mảnh A) · NÃO dò kho 34 query trước khi viết queries.local · đạo diễn 239 beat/9 chương (20 ô thở 51s "ÍT nhưng SÂU" · 2 câu đinh [664]/[2890] · 6 entity · 184 beat có tier local · 3 chart · 35 overlay) · ingest vòng 1: 7 lỗi (6 beat >10s + 1 ô thở [2945] voice không nghỉ) → sửa theo gợi ý máy → PASS 235 beat | ✅ Pha 1 user DUYỆT beats → **Pha 2 CHẠY TRỌN 2026-07-08**: cut (giãn nghỉ DNA 140 điểm +94s · kéo sâu 13 ô thở +46,5s · 19 shot thở · **câu đinh sống ĐẦU TIÊN** [664] "four billion years ‖ and never stopped", điểm 2 Sahara fail-safe tự bỏ đúng) → source 235/235 (phễu: chết kỹ thuật 2% · veto nghĩa 3% · **local-first C4: 175/229 beat có kho trong pool, kho thắng 24 pick** · 2 pexels tải treo tự né) → assemble draft **`CONTENT_ENGLISH_20260708_091258`** (25,8 phút · 271 segment video · 18 shot thở · nhạc 9 chương crossfade + ducking 15 clip · 3 chart PiP+SFX · 35 overlay+SFX · 18 beat clip ngắn kéo slow-mo) → report.html. **Validator DNA Mảnh B im ĐÚNG** (đo lại từ draft: 10,5 cpm ∈ [4,7–18,8] · std 2,25 ≥ 1,55) | ✅ **CẢ 3 CỔNG ĐẠT (user duyệt 2026-07-09):** TAI câu đinh [664] "footage chọn ok, duyệt" + mắt video + DNA Mảnh A đi ké (duyệt chung) — SP012-E2E ĐÓNG TRỌN. User giao tiếp: video đầu tiên DÙNG VIRAL (→ C8-CHON) + Ken Burns ảnh Google (→ KEN-BURNS) | — (run thật) | 2026-07-09 |
| DNA-D1.A | **Consumer DNA đợt 2 (Mảnh A)** — khối "CHỮ KÝ PACING NICHE" vào direct_context.md (NÃO đọc DNA trước khi direct; 2 điều kiện kích hoạt đã đạt: Mảnh B qua cổng mắt + dna.json 3-draft). Chi tiết thi công `MO_TA_VAN_HANH_DNA_D1.md §6`: `dna_block` cùng khuôn `vocab_block` C4 (in live từ dna.json, fail-open 3 nấc, 0 đổi CLI) · 4 dòng số (9,4 cpm · shot 6,2±3,1s · hold 67% · hook45 4,8s) · điểm lệch §6b (BỎ dòng ô thở — P5: ngược chiều "ÍT nhưng SÂU" + máy hình thở 3.0 đã tự lo vi nghỉ) **user DUYỆT 2026-07-08** | ✅ **mô tả DUYỆT + CODE XONG** (smoke: khối in đúng số F: 9,4cpm·6,2±3,1s·67%·hook 4,8s NHANH; echo CLI ✓) — chi tiết §DNA-D1.A. **Cổng mắt ĐẠT 2026-07-09** (đi ké SP012 — user duyệt video, đo thật 10,5cpm/std 2,25 trong vùng DNA) — Mảnh A ĐÓNG | pytest **286/286** (1 mới) | 2026-07-08 |
| C8-NAP | **Gói NẠP viral (gói 1/2 của c8)** — `MO_TA_VAN_HANH_C8_NAP.md` user DUYỆT 2026-07-08 (kèm 2 điểm ủy quyền: zoom khởi điểm 112% · cảnh 6–10s giữ nguyên). Delta 7 điểm trên ống PB4: sàn 2s `MIN_SCENE_S=2.0` (MỌI mẻ, đếm too_short không bỏ âm thầm) · viral bóp >10s còn **6s KHÚC GIỮA** · **crop-zoom 112% nướng chết** (`_zoom_vf`, tên clip mang `_z112` — đổi % là cắt+tag lại) · db 2 cột `source_class`/`source_duration` (665 asset cũ tự = own) · **fail-safe 4 hàm** (`search_assets`/`videos_for_niche`/`signature_assets`/`vocab_for_niche` + thống kê kho dna.py chặn viral tới khi có gói CHỌN) · **CASE-preserve chống re-index lật nhãn viral→own** · CLI `--source-class own\|viral`. Quét 9 draft user (`E:\CapCut Drafts`): 1364 cảnh → bỏ 155 <2s · bóp 226 · ~1200 clip/~$1,2 vision. **Mẻ thử Destiny 45 cảnh: lỗi 0** (1 lỗi tag GLM mood tự đậu khi resume), 2 clip bóp 6s đúng số học, ffprobe 852×478≈nguồn/yuv420p/30fps, db 45 viral + fail-safe verify sạch cả 3 đường trên db thật | ✅ CODE + MẺ THỬ + cổng mắt ĐẠT + **MẺ NẠP FULL 9 DRAFT XONG 2026-07-09** (69 phút): **1209 asset viral** vào db (kho space 665→**1874**) · bỏ sàn 2s 155 · bóp 6s giữa 226 (đúng dự tính) · 6 lỗi lẻ → 0 (1 clip cụt do kill job cắt lại + 1 retry đậu + **4 clip GLM lì mood tag TAY** tiền lệ PB9: Claude xem frame tự điền). Sự cố nuốt nhầm draft kiểm-tra `0709` của user → dừng job, dọn 10 clip + 10 dòng db, đổi sang danh sách chỉ định cứng. Nguồn 480p (854×480 cả 9): **user CHỐT 2026-07-09 CHẤP NHẬN** — tỉ lệ footage viral trong 1 video không nhiều. C8-NAP ĐÓNG TRỌN. Chi tiết §C8-NAP | pytest **291/291** (5 mới) | 2026-07-09 |
| C8-CHON | **Gói CHỌN viral (gói 2/2 của c8)** — `MO_TA_VAN_HANH_C8_CHON.md` (user duyệt trước "duyệt các đề xuất khác... thử dựng luôn"): `sourcer/viral.py::ViralLedger` — 2 gate PHÁP LÝ cùng loại geo-gate PA2: **luật 3** cấm cảnh `scene_index ±1` cùng nguồn DÙ ĐẶT XA NHAU + **luật 5** trần 8%×source_duration cộng dồn TRỌN duration clip (bảo thủ; thiếu mẫu số = chặn luôn) + điểm rải mềm (sort nguồn ít-dùng lên trước, không phải cửa loại — filter-overload-guard nguyên vẹn). Gate ở THU (`_gather_candidates`) + **RE-CHECK tại vòng pick** (bắt ca PA-1 batch gather-trước-pick-sau) + ghi sổ sau tải thành công; `_row_to_candidate` mang 4 field nhãn. Gỡ `_NO_VIRAL` khỏi search/vocab/signature/dna — **GIỮ ở `videos_for_niche`: shot thở ĐÓNG với viral** (P5 catch: 1209 clip mới sort mới-nhất-trước sẽ chiếm trọn pool 500, lật shot thở 2.0). Report thêm dòng "viral c8: X cảnh/Y nguồn · gate chặn Z". **RUN THẬT SP012 re-source: 30 cảnh viral / 8 nguồn / 29 beat, không nguồn nào sát trần** (max Bigbang 62s/138s · NASA-PLUTO 45s/281s) · **gate chặn 208 lượt** · local thắng 34 pick (V1: 24) · phễu khỏe (2%/4%/0 needs_human) → draft **`CONTENT_ENGLISH_20260708_091258_V2`**, validator DNA im ĐÚNG (10,5 cpm · std 2,25) | ✅ **ĐÓNG TRỌN — cổng mắt ĐẠT (user 2026-07-09: "beat 42–73 chất lượng tốt... project dựng tốt")**. Cụm c8 NẠP+CHỌN hoàn tất: pipeline mặc định có viral trong phễu | pytest **296/296** | 2026-07-09 |
| KEN-BURNS | **Ken Burns v1 (f2)** — user chốt tham số 2026-07-09 (ảnh Google đứng yên → keyframe đầu 100%, cuối 120–130%; THAY dự kiến 105→115% của foundation): `_place_video_l1` nhánh photo thêm 2 keyframe `uniform_scale` pycapcut (t=0→1.0, t=cuối−1ms→zoom; EDGE_GUARD tái dùng ducking F8); zoom cuối deterministic crc32 theo tên ảnh (khuôn seed shot thở 2.0). CHỈ ảnh — video có chuyển động thật (cạm bẫy f2 §4); ảnh source_start=0 nên né bẫy time_offset-theo-nguồn của ducking. Chart PiP/info-card/overlay không đụng. `MO_TA_VAN_HANH_KEN_BURNS.md`. **RUN THẬT: V2 in "Ken Burns f2: 6 ảnh zoom 100%→123/130/120/126/127/120%"** — beat entity 15·16·74·76·78·200 | ✅ **ĐÓNG — cổng mắt ĐẠT (user 2026-07-09: "Ken Burns 6 ảnh entity: ok")** — keyframe scale pycapcut RENDER ĐÚNG trong CapCut, ảnh mặc định không bao giờ đứng yên | pytest **296/296** | 2026-07-09 |
| D1-BACKUP | **Backup kho F: → D:** (bước 1 roadmap "D → C có nhịp thở → scale"): robocopy `F:\AutoEdit\library` → `D:\AutoEdit_backup\library` (**1914 file / 5,10 GB**, 0 fail, 65s) + trọn folder `C:\Users\NBPC\AutoEdit` → `D:\AutoEdit_backup\AutoEdit_C` (64 file / 249 MB — cache.db + music/sfx + machine.json, rộng hơn scope gốc "chỉ cache.db" vì rẻ). **Chọn D: có chủ đích:** rà đĩa vật lý trước — E: và F: CÙNG 1 ổ WD HDD (Disk 0) → backup sang E: vô nghĩa; D: nằm NVMe (Disk 1) khác ổ; S: là NAS công ty (`\\192.168.1.213\padoma 8`) không tự ghi. Kiểm job nền sót TRƯỚC khi copy cache.db (memory leftover-background-job-check): sạch | ✅ XONG — verify parity byte 2 phía KHỚP (5.477.181.763 B + 261.543.150 B) · cache.db backup mở read-only integrity **ok**, đủ 3 bảng (library_assets 9282 · asset_usage 2226 · search_cache 2283) | — (hạ tầng, verify tay) | 2026-07-09 |
| D4-D5 | **User quyết 2026-07-09: D4 BỎ.** Hệ KHÔNG cần `ANTHROPIC_API_KEY` (NÃO đi Claude Code subscription — cc_client còn pop key khỏi env con; vision đi GLM; key chỉ cho 2 fallback chưa dùng `--engine api`/`--engine claude` và đã chết 401) → **xóa key khỏi .env** + sửa .env.example + autoedit/CLAUDE.md Bước 4 — **đừng hỏi lại**. D5 git: user hoãn LÚC ĐẦU vì tưởng D5 = commit GitHub tốn thời gian → sau khi làm rõ là git LOCAL, user mở lại CÙNG NGÀY (xem dòng D5-GIT). Chi tiết §D4-D5 | ✅ CHỐT | pytest **296/296** sau khi xóa key (không test nào phụ thuộc) | 2026-07-09 |
| D5-GIT | **Bật git LOCAL** (user chốt lại 2026-07-09 sau khi rõ D5 ≠ GitHub): `git init` tại root project + `.gitignore` loại `.env` (key) / `.venv` (590MB) / `autoedit/projects/` (29,6GB output) → **commit gốc `890c68b`** = 173 file / 42.646 dòng (code + docs + foundation + capcut_test + voice test, trạng thái pytest 296/296 sau c8+Ken Burns). Identity local `PADOMA <padoma.content8@gmail.com>`. **Luật mới vào CLAUDE.md P4:** sau mỗi milestone → commit mốc khôi phục; **KHÔNG remote/KHÔNG push GitHub** | ✅ XONG — verify: staged không có .env/.venv/projects (grep), file lớn nhất 5,1MB, `git status` sạch sau commit | — (hạ tầng) | 2026-07-09 |
| D2 | **Đường `direct` cũ ăn khối kho** (đóng còn-ngỏ chung từ C4 + DNA Mảnh A — fallback lệch đường chính): `run_direct` tính `vocab_block` + `dna_block` (tái dùng NGUYÊN 2 hàm của live.py — import lười tránh vòng live↔runner) từ `inputs.channel` → chèn vào `beats_system` **CHỈ pass 2** (nơi quyết `queries.local` + độ dài beat/shot_count; pass outline không đụng — không viết query, không đặt độ dài). **0 đổi CLI** — cả `direct` lẫn `run` (pipeline full) tự hưởng qua channel, không đổi chữ ký caller nào (né vết bug B2 quên-caller). Fail-open 3 nấc y đường sâu: không channel / kho rỗng / không dna.json → prompt y như cũ. Chi tiết §D2 | ✅ XONG — **NHÓM D ĐÓNG TRỌN** | pytest **297/297** (1 mới: outline sạch · pass 2 đủ 2 khối · ổn định giữa chương · fail-open) · smoke thật: vocab 1874 asset + DNA 3 draft render đúng | 2026-07-09 |
| V123 | **Gói nâng cấp từ 3 vấn đề user thấy ở SP012_V2** (`MO_TA_VAN_HANH_NANG_CAP_V123.md` user DUYỆT 2026-07-09; bằng chứng: 44/442 asset lệch 16:9 · luật entity 0-1/video viết cho niche đời sống · rank_log b11 NÃO tự viết "trên sao Hỏa" vẫn chấm 8/10): **V1** crop tâm 16:9 tại `normalize_video` (lệch >3%; `crop_16x9=False` cho chart PiP + info-card DỌC — P5 catch suýt vỡ card 960×1080; ảnh KHÔNG crop file → Ken Burns keyframe `cover→cover×zoom`, ảnh 16:9 y cũ) · **V2** entity mở 3 nhóm cho facts/space (máy móc có tên + sự kiện thật + thiên thể đích danh, ngân sách 3-8/video; sửa CẢ foundation c1 + _SOURCING_RULES + memory video-first-routing) · **V3** `Outline.video_subject` = PHẠM VI (được phép đa chủ thể — giải lo ngại user; fail-open project cũ) chảy tới prompt phễu + veto `thuc_the_sai` thêm sai-thiên-thể + "khớp hành động không gỡ tội"; 3c vision gate DỜI sang C đợt 5 kèm nguyên tắc chống-quá-tay. Commit `16e278b`/`9352b61`/`9fa10e2`. Chi tiết §V123 | ✅ M1+M2+M3 XONG · **M4 video kiểm ĐÃ DỰNG** (user chốt: test ~10 phút từ voice SP012): input cắt tại hết chương 4 outline cũ (word 1302 / 555s, kết trọn câu) → project `script-20260709-071612` fresh direct ĐƯỜNG SÂU (direct cũ FAIL: chương ~424 từ vượt trần 600s subprocess ×3 attempt — còn ngỏ mới cho L1) → 95 beat/4 chương ingest PASS lần 1 · source 95/95 (pexels 72 · **entity 8/8 ảnh thật** · local 15 · viral 14 cảnh gate chặn 57) → draft **`SCRIPT_20260709_071612`** (623,8s · 2 chart PiP + 1 info-card + 8 overlay + KB 8 ảnh). **Cổng SỐ đạt: norm 104/104 video 16:9 (file "lệch" duy nhất = info-card dọc — đúng thiết kế) · video_subject vào outline · DNA validator im ĐÚNG** · ✅ **CỔNG MẮT ĐẠT (user 2026-07-09: "đã ok, pass qua cả 3 vấn đề" — hết viền đen · 8 entity thật + Ken Burns · không sai nghĩa) — V123 ĐÓNG TRỌN M1+M2+M3+M4** | pytest **302/302** (M1 +3 · V3 +2; e2e Ken Burns cập nhật cover 4:3; norm 320×240→320×180) | 2026-07-09 |
| C-ĐỢT-1 | **C6 drop-list + C3 so màu cảnh báo + C7 lệnh pause-dna** (`MO_TA_VAN_HANH_C_DOT_1.md` user duyệt hướng 2026-07-09: C6 chốt "Cách 1 — Drop-list" · C3 chỉ-cảnh-báo · C7 đồng ý đề xuất): **C6** `_strip_motion_terms` trong `sourcer/local.py` bỏ từ camera/chuyển-động trước AND-match (GLM tag frame TĨNH không bao giờ có "rotating"; bỏ sạch token → giữ query gốc; KHÔNG sửa prompt kèm — né 2-tầng-cùng-quản) — benchmark PB8 re-run: `spiral galaxy rotating` 0→80 · `stars timelapse` 0→604 · `universe zoom out` 0→742 · `astronaut floating` 2→19, **20 query khác không đổi 1 số** (PB8 §D) · **C3** `sourcer/colorcheck.py` đo V/S/hue mọi footage đã chọn (PIL/ffmpeg, 0 token, ~35s/110 file) so TRUNG VỊ chương, outlier = lệch tuyệt đối **+ robust z MAD ≥3,5** (đo thật V123: ngưỡng tuyệt đối đơn bắn oan 53/110 vì space vốn xen kẽ xám/rực → MAD đưa về **8/110**; hue leave-one-out chống outlier tự đầu độc chuẩn) — CHỈ warning, fail-open, gọi cuối `run_source` · **C7** `library/pause_scan.py` + CLI `pause-dna` (adapt `learn_pause_dna.py` CỨU từ scratchpad phiên cũ; cache transcript 16 file cứu về `F:\...\space\pause_scan_cache\`) + vá 3 bài học §6.2C (montage ≥4 nhát/>20s thay lọc phăng ≥8s · tách lớp thở hold≤1,2+footage≥1,5 · xuất `pooled.breath` đo được, khóa chính sách k KHÔNG xuất — in `k_dist` cho người xem, backlog §6.5) + **GUARD không đè bản duyệt** (ghi `.new.json`; `--force` tự backup) — regression 3 draft SP1 thật: kinds+holes khớp TUYỆT ĐỐI bản hiện hành (97/102·205/213·140/149 y §HOC-DNA-NHIP). Commit 3 mốc riêng | ✅ CODE XONG cả 3 · **VIDEO KIỂM ĐÃ DỰNG** (re-source + assemble trên CHÍNH project `script-20260709-071612` — beats/cut giữ nguyên để khác biệt truy được về C6/C3; V1 backup `project.json.bak-truoc-c-dot-1`): draft **`SCRIPT_20260709_071612_V2`** — nguồn pick V1→V2: local **15→21** (+6; 7 beat chuyển sang kho: 27·34·60·66·68·83·87) · pexels 72→66 · entity 8 y nguyên · needs_human 0 · viral 19 cảnh/8 nguồn gate chặn 66 · phễu khỏe (3%/5%) · **C3 bắn 12 cảnh báo/110 footage** (5 sáng-hơn-chương + 7 lệch tông) · ✅ **ĐÓNG TRỌN — cổng mắt qua video kiểm GỘP V3 (user duyệt 2026-07-09, xem KIEM-V3)** | pytest **317/317** (C6 +2 · C3 +8 · C7 +5) | 2026-07-09 |
| C-ĐỢT-2 | **C4 tone cấp video + D3 nới trần local** (`MO_TA_VAN_HANH_C_DOT_2.md` — user duyệt CÓ ĐIỀU KIỆN "tính kỹ chồng chéo, không làm loạn hệ thống thì tiếp tục" → Claude rà lần 2, **CẮT 2 điểm chảy** khỏi nháp: ~~phễu thấy tone~~ (2 tầng cùng quản mood — NÃO phạt đúp footage) + ~~nhạc thấy tone~~ (thêm từ tone vào `want` PHA LOÃNG điểm `|want∩track|/|want|`)): **C4** = phát hiện `Outline.tone` ĐÃ có từ pass 1 nhưng 0 consumer → chỉ siết THƯỢNG NGUỒN: luật mood-chạm-tone vào beats_system (direct cũ, tone sẵn trong outline_json) + bảng ràng buộc live.py (đường sâu) + card "Tone video" trên report (fail-open) — 0 hành vi máy đổi · **D3** = `LOCAL_TOTAL_CAP=10` tách trần TỔNG khỏi limit per-query (giữ 5; số 5 cũ gánh 2 vai từ hồi kho 282 — kho 1874 + C6 mở recall làm query đầu nuốt hết suất); mọi cửa (geo/viral/P7/veto) chạy y nguyên từng ứng viên. Commit `1a3ce89` + `ceeb6f1` | ✅ **ĐÓNG TRỌN — video kiểm GỘP V3 (xem KIEM-V3): cổng TAI nhạc theo tone ĐẠT + local sau D3 ĐẠT (user duyệt 2026-07-09)** | pytest **321/321** (C4 +3 · D3 +1) | 2026-07-09 |
| KIEM-V3 | **Video kiểm GỘP C đợt 1+2** (user chốt "dựng SP012 10' theo đề xuất" — so chuỗi V1→V2→V3 cùng beats): re-source + assemble + report trên CHÍNH project `script-20260709-071612` (V2 backup `project.json.bak-truoc-v3`) → draft **`SCRIPT_20260709_071612_V3`**. Lần đầu kho local chạy đủ 3 nâng cấp: C6 + D3 trần 10 + **102 clip tag lại**. Số: local thắng **20** (V2: 21 — số giữ nhưng THÀNH PHẦN sạch: **4 pick sai-nghĩa biến mất** — clip Pluto rời b32/b33/b60, Destiny nhà-sao rời b68, thay bằng Pexels đúng nghĩa; video NASA-PLUTO giờ chỉ còn ở b72 = cảnh tàu thăm dò cho ý Luna 3, ĐÚNG nội dung thật; 8 local thắng mới hợp lý b01/b10/b18/b21/b26/b35/b47/b89) · picks đổi V2→V3: 45/95 · pexels 67 · entity 8 · needs_human 0 · phễu 1085 ứng viên (chết kỹ thuật 3% · veto nghĩa 8% · sàn trả lại 0) · viral c8: 11 cảnh/7 nguồn, gate chặn 48 · **C3: 9 cảnh báo/110** (V2: 12; 3 rơi vào shot thở "sáng hơn hẳn" — lớp có thể oan-có-chủ-đích) · card **Tone video** (C4) lần đầu trên report: "quiet awe..." · nhạc 4 chương uplifting→hopeful→peaceful→tense · 13 beat clip ngắn slow-mo (nặng nhất b54 0,48x · b65 0,45x) | ✅ **CỔNG MẮT + TAI ĐẠT (user 2026-07-09):** b10/b54 (2 pick Destiny mới, lớp không-ground-truth) "đều ok" · chất footage ok · C3 "duyệt qua, không quá quan trọng" · footage slow-mo ok · "phần nhạc tôi thấy ổn" — **C đợt 1+2 ĐÓNG TRỌN** | — (run thật, code không đổi — pytest 321/321 re-run xanh) | 2026-07-09 |
| C-ĐỢT-3-M1 | **C1 ambient — PB10 + kho + M1 thư viện/lệnh nạp** (`MO_TA_VAN_HANH_C1_AMBIENT.md` user duyệt 2026-07-10; 2 quyết định user cùng ngày: kho ở **`F:\AutoEdit\ambient\<niche>\` THEO NICHE** "dễ nhớ khi có nhiều niche" + **tái dùng SFX editor thật cả 3 project**): **PB10** giải phẫu âm thanh 3 draft SP1 → `PB10_AM_THANH_3_DRAFT_EDITOR.md` (6 lớp + volume chuẩn: nhạc 0.05–0.1 CHỒNG 2–4 lớp · ambient cảnh 0.2–0.4 · drone nền chạy SUỐT video · whoosh ×20–30 · video bật tiếng gốc ~100% — máy vô tình khớp default 1.0) → `AMBIENT_VOL=0.4` từ đoán thành số đo + brief từ khóa theo đồ editor thật · **MÓT KHO EDITOR** (COPY-only, không đụng draft gốc): 16 ambient + **19 SFX ngắn** + 43 hold (`raw\tu_editor_chua_phan_loai\` — lửa/sôi/rocket/whoosh dài... chờ C5/whoosh-standalone) + 16 file NHẠC không copy (ngoài scope, chờ user gọi) · user tải **29 file Artlist** đặt tên "từ khóa - tên gốc" → manifest máy sinh, 8 file 29–56s < chuẩn 60s vẫn dùng (ô thở ≤10,5s) · **M1 CODE**: `ambient/library.py` (kind = 14 scene_type GLM + `default` · biến thể khớp CHẶT `^kind(_n).wav$` sort theo SỐ · root suy `library_root` CHA machine.json 0-config · records `ambient_library.yaml` TÁCH manifest input · nguồn ngoài folder niche KHÔNG move · **fix bug dual-kind**: dọn raw giữa vòng lặp làm kind 2 mất file → dọn SAU vòng + regression) + CLI `ambient-import`/`ambient-list` (fail-open kho rỗng = tầng tắt) · **NẠP THẬT 47/47 ambient 0 lỗi** (space 12 · default 8 · interior 8 · mountain_desert 8 · sky_cloud 6 · urban_street 2 · nature_forest_field 2 · people_activity 1 — đồ editor đứng biến thể ĐẦU vì proven trên video thật) + **19 SFX editor vào kho C:** (whoosh 4→**15** · impact 2→4 · ding 3→6 · keyboard 1→3 · pop 3→4) | ✅ M0+M1 XONG — kế tiếp M2 (lập lịch ô thở + chọn theo scene_type + wire assemble + card report) → M3 draft V4 cổng TAI | pytest **329/329** (+8 test_ambient) | 2026-07-10 |
| C-ĐỢT-3-M2 | **C1 ambient M2 — lập lịch + chọn + wire assemble + V4** : `ambient/schedule.py` (3 tham số 🔸 `AMBIENT_VOL=0.4`/`AMB_MIN=3.0`/`AMB_FADE=1.0` — số PB10; `breath_slots` DÙNG CHUNG `ducking.merge_voice_intervals` = 1 nguồn sự thật với F8, ô ≥3s + ô kết video, beat mang ô = beat cuối segment trước ô; `resolve_scene` miếng shot thở ĐẦU → pick local → mù; `db_scene_lookup` chỉ tra `local:`; `choose_files` xoay vòng biến thể theo kind, thiếu → default, thiếu nốt → bỏ ô + note) · assembler `_add_ambient` SAU `_duck_music` (track audio `ambient` riêng, volume tĩnh + `add_fade` 2 mép, cắt từ đầu file, file ngắn hơn ô → phủ được tới đâu ghi note; fail-open 4 nấc: không niche/kho chưa có/db hỏng/kho rỗng — `niche_path`+`scene_lookup` tiêm được cho test, KHÔNG đụng cache.db thật) · `project.ambient_log` field mới (NT1/NT5) · report bảng "Ambient ô thở" + hint chỉnh AMBIENT_VOL trước · 1 bug bắt trong test: note "mù tag" không bao giờ in (mù đi thẳng kind default nên nhánh `used==kind` nuốt) — fix tách 3 nhánh note · **RUN THẬT SP012 → draft `SCRIPT_20260709_071612_V4`** (project.json backup `bak-truoc-v4`): **ambient 7/7 ô** — 5 ô scene `space` xoay đúng 5 biến thể (toàn đồ editor: ù ù vũ trụ/deep space/Dark Space...) · b38 `abstract_texture` → default ĐÚNG thiết kế · b79 `sky_cloud` | ✅ M2 XONG — V4 lên cổng tai, kết quả ở dòng C-ĐỢT-3-M3 | pytest **339/339** (+10 test_ambient_schedule) | 2026-07-10 |
| C-ĐỢT-3-M3 | **Cổng TAI V4 + chốt tham số + backup — C ĐỢT 3 ĐÓNG TRỌN**: user nghe V4 2026-07-10, verdict "sfx bị chìm trong nền nhạc — KHÔNG hạ volume sfx, chỉnh về 0dB" → `AMBIENT_VOL` 0.4→**1.0 (0dB)**, `AMB_MIN=3.0s`/`AMB_FADE=1.0s` giữ nguyên, `BREATH_VOL` nhạc không đổi. **BÀI HỌC PB10**: số ambient editor 0.2–0.4 KHÔNG áp thẳng được — nhạc nền của HỌ chỉ 0.05–0.1 còn nhạc máy nở tới 0.5; tham chiếu volume editor phải quy theo TƯƠNG QUAN giữa các lớp, không bê số tuyệt đối. Sửa 3 chỗ: hằng số schedule.py · MO_TA_C1 §4/§6/§8 · hint report ĐỔI CHIỀU (KHÔNG hạ ambient khi dày; lệch cảnh → xem tag/kho). **BACKUP D: bổ sung** (đóng còn-ngỏ M1): `F:\AutoEdit\ambient` → `D:\AutoEdit_backup\ambient` MỚI (138 file / 2,18 GB) + refresh `AutoEdit_C` (22 file mới — 19 SFX editor + cache.db) + refresh `library` (28 file) — verify parity file+byte cả 3 kho KHỚP | ✅ **C ĐỢT 3 ĐÓNG TRỌN** — 3 tham số chốt bằng tai user · kế tiếp theo roadmap: C đợt 4 (C2 punch-in) · backlog chờ user chọn: drone nền toàn video / whoosh standalone | pytest **339/339** re-run sau đổi volume | 2026-07-10 |
| C-ĐỢT-3b-M0 | **SFX hoàn thiện — duyệt mô tả + M0 kho + PB11** (`MO_TA_VAN_HANH_SFX_HOAN_THIEN.md` user DUYỆT 2026-07-10 với 2 điều chỉnh: subject-SFX TRONG voice OK "editor thật vẫn làm thế" volume đặt **-4dB (0.63)** · thêm **S4 `editor-learn`** luật đứng lâu dài: mỗi project editor mới vào phải HỌC + LƯU sfx/music để tái dùng — memory `editor-learn-standing-rule`): gói S1 drone nền + S2 subject-SFX (cái "wow": kho local ĐÃ có vision tag subject/tags/description = mắt editor; bảng từ khóa map chủ thể→tiếng, 0 token) + S3 whoosh + S4 editor-learn · **M0 KHO**: `SUBJECT_KINDS` (fire/rocket/explosion/rumble/water/signal) + kind `drone` vào AMBIENT_KINDS → nạp **+30 biến thể** từ hold editor (fire 8 gồm "sôi sục mặt trời"/boiling dual-kind · rocket 4 · explosion 3 · rumble 5 · water 3 · signal 1 · drone 6 — drone TRÁNH 5 bản đã làm biến thể space ô thở, lấy ù ù điện ảnh/amvien/sâu lắng + 3 Artlist loop); kho space giờ 77 biến thể/15 kind · **PB11 đo whoosh 3 draft** (PB10 doc §5): **LẬT giả thuyết whoosh-bám-cut** — 23–40 whoosh/video (~1/phút) vs 120–263 cut, sát cut ≤0,5s chỉ 20–30%, median dài 1,7–3,5s volume 0,18–0,32 → luật S3 v1: đặt ở chuyển CHƯƠNG + vào/ra ô thở, KHÔNG theo cut thường | ✅ M0 XONG — kế tiếp M1 (S1 drone bed) → M2 (S2 subject) → M3 draft V5 cổng TAI | pytest **340/340** (+1 kind mới) | 2026-07-10 |
| C-ĐỢT-3b-M1M2 | **S1 drone nền + S2 subject-SFX + draft V5** (user duyệt cả gói "duyệt, bạn hãy làm"): **S1** `choose_drone` crc32 seed project (1 drone/video, deterministic) + `_add_drone` track `drone` riêng — loop nối đuôi file 2-4' phủ video 10', mép nối fade `SEAM_FADE=0.3s` chống click, fade vào 2s/ra 3s, `DRONE_VOL=0.15` 🔸 (quy TƯƠNG QUAN PB10, không bê số tuyệt đối — bài học V4) · **S2 mức 1 (ô thở)**: `resolve_slot_subject` + `choose_files` nâng chuỗi ưu tiên **chủ thể > loại cảnh > default** (sửa NGAY TRONG choose_files, 1 chỗ quyết — P5) · **S2 mức 2 (trong voice)**: `subject_kind` bảng SUBJECT_RULES khớp TỪ NGUYÊN ("sunset" không ăn "sun") + `db_subject_lookup` (subject+tags+description = mắt vision kho; stock → `visual_concept` proxy) + `subject_beat_slots` trần chống loạn (≤6/video · không 2 beat liền kề · ≤2/kind · skip beat đồ họa `_beat_has_priority_visual` · beat <3s bỏ · cắt `SUBJ_MAX=10s`) + `_add_subject_sfx` track ambient `SUBJECT_VOL=0.63` (-4dB user đặt) · `project.drone_log`+`subject_sfx_log` + report 2 mục mới · **BUG BẮT KHI DỰNG V5 + FIX**: hệ tọa độ kép lệch ~50ms — ô thở C1 (mốc SEGMENT voice, kết 60,515s) lấn đầu tiếng chủ thể b11 (mốc WORD beat, 60,464s) → SegmentOverlap bỏ cả tiếng; fix XÉN ĐẦU ≤1s né ô thở + regression test · **RUN THẬT → draft `SCRIPT_20260709_071612_V5`** (bak-truoc-v5; draft V5 hỏng đã xóa dựng lại điền lỗ tên): drone_5 (Deep Sub Drone Artlist) phủ 624s/6 đoạn · **6/6 tiếng chủ thể** (b11 rocket xén đầu ✓ · b15 rocket · b18 fire kho · b22 fire · b56 water · b72 signal kho) · ô thở 7/7 trong đó **4 ô chủ thể THẮNG cảnh** (b20 sun+flares→fire · b46 probe antenna→signal · b91 solar surface→fire — kiểm db ĐÚNG nghĩa; **b79 RANH GIỚI**: sunrise trên mây tag "sun"→fire, chờ tai user, lệch thì thêm luật trừ sunrise/sunset) | ✅ M1+M2 XONG — V5 lên cổng tai, kết quả dòng M3a | pytest **350/350** (+10: S1 3 · S2 6 · regression xén đầu 1) | 2026-07-10 |
| C-ĐỢT-3b-M3a | **Cổng TAI V5 lần 1 + 2 fix gốc → draft V6**: user phán — **drone nền DUYỆT ✅** (`DRONE_VOL=0.15` chốt) · 3 lỗi: b20 fire TRÀN sang footage tên lửa (02:21:22) · b22 footage MẶT TRĂNG nghe lửa + b56 DUNG NHAM nghe nước · 5:21 signal tràn qua mốc kết tàu thăm dò (05:25:09) → truy 2 gốc: **(1) tiếng không bám MIẾNG footage** — fix: ô thở cắt theo mốc kết miếng 1 (`first_piece_end` từ `BreathShot.dur`; chỉ cắt tiếng CHỦ THỂ, tiếng loại-cảnh vẫn phủ trọn ô) + beat nhiều shot cắt theo mép shot 1 (TÁI DÙNG `coverage.split_window` — không đẻ luật chia thứ 2, P5) · **(2) concept-proxy đoán sai footage thật** — `visual_concept` tả Ý ĐỊNH của NÃO, không phải footage stock ĐÃ pick → **BỎ nhánh concept, S2 chỉ tin tag vision kho**; trade-off: rớt cả 2 tiếng rocket đúng-tình-cờ (b11/b15), in-voice 6→3 tiếng — C5 đợt 5 gánh thêm việc vision-tag pick stock để mở lại · +3 regression (concept-not-used · cắt miếng · cắt shot 1) · **RUN THẬT → draft `SCRIPT_20260709_071612_V6`** (bak-truoc-v6; V5 GIỮ NGUYÊN cho user so): b20 fire 3,6/9,0s dừng đúng trước tên lửa · b46 signal 4,2/7,7s dừng đúng mốc 05:24,8 · b22/b56 IM (đúng thiết kế) · in-voice 3 tiếng toàn kho: b18 fire (hệ mặt trời) · b23 fire (nhật thực — kiểm db đúng) · b72 signal · b79 sunrise→fire VẪN CÒN (ranh giới, chờ user phán tiếp) | ✅ **CỔNG TAI V6 lần 2 (user 2026-07-10): tiếng-bám-miếng ĐẠT "đã dừng đúng, duyệt" · b79 sunrise→fire DUYỆT (không cần luật trừ) · "3 tiếng chủ thể là ít"** — user hiểu do bỏ concept, hỏi tư vấn bước tiếp → đề xuất M3b C5-lite (vision tag pick stock) | pytest **353/353** (+3 regression) | 2026-07-10 |
| GLM-ZAI | **GLM chuyển server QUỐC TẾ api.z.ai** (user phát hiện trên máy khác: server TQ `open.bigmodel.cn` hay lỗi, z.ai ít lỗi + nhanh): audit toàn project — mọi call GLM đi qua ĐÚNG 1 cửa `vision.py::GLMVisionTagger._post` (indexer/ingest/stock_tags/CLI đều dùng chung) → đo thật CÙNG key cùng call: **z.ai 0,7s vs bigmodel 2,2s (~3x)**; bằng chứng sống: job tag-stock 75 asset trên bigmodel kẹt >15' phải kill, chạy lại qua z.ai xong ~2' — nghi các bug SSLEOF/RemoteDisconnected (PB3) một phần do server TQ · code: `glm_api_url()` mặc định z.ai, env `GLM_API_URL` đè để quay về TQ · sửa CLAUDE.md §5 (3 quy tắc) + memory glm-46v-tag-lessons | ✅ XONG | pytest 362/362 (+1 test env override) | 2026-07-10 |
| C-ĐỢT-3b-M3bM4 | **M3b vision-tag pick stock + M4 whoosh → draft V7** (user chốt phương án A "làm luôn vision để tag cho chuẩn" + lưu tag tái dùng + tính sẵn vòng học editor): **M3b** bảng `cache.db::stock_tags` (asset_key PK — pexels/entity id ổn định → LƯU VĨNH VIỄN, video sau cache hit, chi phí giảm về 0; nền C5 đợt 5 + editor-learn vì project.json giữ asset_key từng beat) · `library/stock_tags.py::tag_project_stock` (GLMVisionTagger sẵn có, multi-key ≤3 luồng/key, fail-open từng asset lẫn cả tầng) · wire cuối `run_source` SAU picks chốt (KHÔNG lật phễu/ranker — phễu không đọc stock_tags) + CLI `tag-stock` · `db_scene_lookup`/`db_subject_lookup` mở rộng tra stock_tags · **TAG THẬT SP012: 74/75 pick** (~$0.07, 1 fail contentFilter-kiểu-mood fail-open) · **M4** `whoosh_slots` = chuyển CHƯƠNG (kind `swell` DÀI dâng trước 2s — tên tránh glob lỏng `whoosh*` nuốt vào kind cũ, P5 catch) + VÀO ô thở (whoosh ngắn chớm 0,5s; mốc từ CHÍNH breath_slots — 1 nguồn sự thật) · mốc gần <5s chương thắng · `WHOOSH_VOL=0.5`🔸 quy tương quan · KHÔNG fallback demo · kho +swell×8 +riser (hold editor) · **PHỄU VISION BẮT 3 BUG BẢNG TỪ KHÓA trước cổng tai** (kiểm tag thật V7 lần 1): b08 "solar panels" dính từ `solar`→lửa SAI · b15 rocket phụt lửa ra fire (fire xét trước rocket) · b20 "impact craters" TĨNH dính `impact`→nổ SAI → **SUBJECT_RULES v2: cụ thể trước generic sau (rocket/explosion/rumble/signal/water/fire), BỎ 2 từ bẫy solar+impact** (+5 regression) · **draft `SCRIPT_20260709_071612_V7`** (bak-truoc-v7, V7 lỗi đã xóa dựng lại): subject-SFX 3→**6 tiếng TOÀN vision thật** (b04 water biển đêm · b12 rocket Artemis · b15 rocket · b18 fire hệ mặt trời · b23 fire nhật thực · b55 explosion núi lửa phun — ca "dung nham nghe tiếng nước" V5 giờ vision nhìn đúng) · whoosh **10/10** mốc (7 ô thở + 3 chương = ~1/phút đúng PB11) · ô thở/drone giữ nguyên V6 | ✅ M3b+M4 XONG — V7 lên cổng tai, kết quả dòng M3c | pytest **362/362** (+2: stock_tags 3 test, whoosh 4 test, SUBJECT_RULES 1) | 2026-07-10 |
| C-ĐỢT-3b-M3c | **Cổng TAI V7 lần 3 + 5 luật tinh chỉnh → draft V8** (user 2026-07-10: "**volume của sfx tôi thấy đạt, không cần sửa**" — CHỐT WHOOSH_VOL 0.5/SUBJECT_VOL 0.63/DRONE_VOL 0.15; 4 lỗi nội dung): **(1)** b04 biển đêm nghe tiếng nước RÓT → tách kind **`ocean`** khỏi `water` (kho water = rót/sôi từ hold editor; keys ocean/sea/wave/waves; bỏ từ trần "water" — họ hàng từ bẫy solar/impact); kho CHƯA có file sóng → beat biển IM thà-im-hơn-sai, **cần mua "gentle ocean waves"** · **(2)** b12 ảnh Artemis kêu tiếng rocket → **ẢNH (entity/Ken Burns) KHÔNG SFX** (check IMAGE_EXTS) · **(3)** whoosh auto tại mốc chương SAI — editor gắn whoosh với **TEXT CHAPTER hiện lên** → BỎ swell khỏi whoosh_slots (chỉ còn VÀO ô thở), backlog "chapter-title card + swell đi cùng" (khuôn overlay-SFX sẵn), swell ×8 nằm kho chờ · **(4)** tiếng lửa auto khi có mặt trời SAI — editor chỉ đặt khi quay CẬN → luật `subject_kind(text, shot_size)`: fire qua "sun" đòi close_up/extreme_close_up (vision đã tag shot_size sẵn 2 bảng; lookup đổi trả (text, shot_size)) · **(5)** V8 lần 1 lộ thêm b42 "volcanic rock formations" AERIAL nham NGUỘI kêu lửa → "lava" rời nhóm lửa-thật, cũng đòi cận · **draft `SCRIPT_20260709_071612_V8`** (bak-truoc-v8): 5 tiếng chủ thể sạch (b15 rocket bay · b23 nhật thực CẬN · b55 núi lửa phun · b72 tín hiệu · b74 rocket phóng đêm — kiểm db từng ca) + b04 ocean im có note · b79 sunrise → tiếng GIÓ sky_cloud (đẹp hơn fire) · b91 solar-surface-cận GIỮ sôi · b18/b20/b42 im đúng · whoosh 7/7 chỉ ô thở | ✅ fix xong — V8 lên cổng tai lần 4, kết quả dòng M3d | pytest **363/363** (+3 regression: image-skip · sun-cận · ocean-split/lava) | 2026-07-10 |
| C-ĐỢT-3b-M3d | **PB12 + BỎ TRỌN whoosh auto → draft V9** (tai V8: user đính chính — whoosh đang auto vào mốc HÌNH THỞ, nghi sai, "kiểm tra xem editor có làm thế không, tôi đang nghĩ sẽ bỏ"): **PB12 đo 3 draft** — mốc vào ô thở lấy từ khoảng nghỉ ≥1,5s trên track VOICE THẬT của editor: **0/88 whoosh nằm quanh mốc vào ô thở (0% cả 3 draft)**; ngược lại 40–70% whoosh bám mốc TEXT hiện lên (xác nhận đúng lời user "chapter 2: the moon lên hình → whoosh theo"). PB11 "khúc chuyển lớn = ô thở" là SUY DIỄN SAI — bài học: **PB đo tương quan với CUT chưa đủ, phải đo với thứ nghi ngờ trực tiếp** (voice-gap, text) trước khi viết luật · **BỎ TRỌN S3 auto**: gỡ `whoosh_slots`/`WhooshSlot`/`_add_whoosh`/hằng số/3 test (field `whoosh_log` GIỮ cho project.json cũ load + chapter-card backlog dùng lại; assemble dọn log cũ) · whoosh đúng kiểu editor máy ĐÃ CÓ một nửa = overlay-SFX bám text; nửa còn thiếu = **backlog: chapter-title card + whoosh/swell** (kho swell ×8 + whoosh ×15 chờ) · **draft `SCRIPT_20260709_071612_V9`** (bak-truoc-v9): ambient 7/7 + drone + 5 tiếng chủ thể y V8, KHÔNG còn whoosh auto | ✅ BỎ xong — **draft V9 CHỜ CỔNG TAI cuối** (đạt là ĐÓNG S1-S2, còn M5 editor-learn) | pytest **360/360** (−3 test whoosh gỡ theo code) | 2026-07-10 |
| C-ĐỢT-3b-M3e | **PB13 + volume SFX theo NGỮ CẢNH VOICE → draft V10** (user sau V9: "sfx khi có voice để -15dB, không voice (hình thở) để -10dB; tốt nhất học project editor thật xem sfx ở mỗi đoạn có/không voice để âm lượng thế nào, sau đó học vào project mới"): **PB13 đo 3 draft editor** (PB10 doc §7; script GIỮ TRONG REPO `autoedit/scripts_phan_tich_pb13_sfx_vol_voice.py` — M5 editor-learn bê vào làm module, project editor mới vào → cập nhật số) — SFX = đoạn ≤40s không phải voice/nhạc, ngữ cảnh theo % trùng khoảng voice (≥60% = đè voice, ≤15% = không voice): **SFX đè voice median -11…-15.6dB · SFX không voice -10…-11.6dB → TRỰC GIÁC USER KHỚP SỐ EDITOR** (đề xuất -15/-10 nằm trong dải, đúng chiều "không voice to hơn ~3-5dB") · CHỐT `SUBJECT_VOL=0.18` (-15dB trong voice, thay 0.63) + hằng số MỚI `SUBJECT_BREATH_VOL=0.32` (-10dB tiếng chủ thể THẮNG Ô THỞ — điều kiện `used_kind==subject_kind`, cùng ngữ nghĩa luật cắt-theo-miếng-1) · **ambient LOẠI CẢNH GIỮ 0dB** (verdict V4 KHÔNG lật — pad dài cùng phổ nhạc từng chìm ở 0.4 dưới nhạc-nở 0.5; tiếng chủ thể giàu transient xuyên nền tốt hơn) · rà chồng chéo MO_TA §6: rủi ro nuốt-tiếng = nhạc máy (0.2 voice/0.5 nở) TO hơn hẳn nhạc editor (0.06–0.10) — SFX -15dB sẽ ngồi NGANG nhạc thay vì trên như mix editor; nếu tai V10 nghe chìm thì núm chỉnh là NHẠC, không nâng SFX lại · editor-learn M5 spec (MO_TA §4b) cộng thêm DNA volume-theo-ngữ-cảnh-voice · **draft `SCRIPT_20260709_071612_V10`** (V9 giữ so): kiểm db 12 seg track ambient — 5 cảnh 1.0 · 2 chủ-thể-ô-thở 0.32 (signal 320,6s + fire 605,8s) · 5 trong-voice 0.18 · drone 0.15 y nguyên | ✅ **CỔNG TAI V10 ĐẠT (user 2026-07-10: "V10 đã ổn") → S1 DRONE + S2 SUBJECT-SFX + C1 AMBIENT ĐÓNG TRỌN** — còn M5 `editor-learn` (cổng pytest, không cần tai) là hết C đợt 3b; xong M5 → backup D: | pytest **360/360** (regression subject-ô-thở 0.32 thêm vào test cắt-miếng; neo 0.18 test cũ) | 2026-07-10 |
| C-ĐỢT-3b-M5 | **S4 `autoedit editor-learn <draft> --niche <n> [--dry-run]` — đóng quy trình mót-kho PB10 thành 1 lệnh lặp lại được (COPY-only, luật đứng 2026-07-10)**: module MỚI `editor_learn/` (`dna.py` quét + `mine.py` mót) · **DNA**: bê PB13 NGUYÊN logic (đoạn >40s = nhạc/drone; SFX chia ngữ cảnh voice ≥60% trùng = đè / ≤15% = không voice; tách whoosh) + PB11 hiệu chuẩn trên 3 draft tới khi khớp 100% số công bố — định nghĩa chốt: **cut = TẬP start segment track video CHÍNH (bỏ t≈0) · sát-cut = đầu whoosh ≤0,5s · cut-trong-whoosh INCLUSIVE a≤c≤b** (strict lệch 17→15, 4→3) · hồ sơ cộng dồn `F:\AutoEdit\editor_dna.json` (1 entry/draft, học lại = THAY không cộng đôi; pooled median đối chiếu SUBJECT_VOL/SUBJECT_BREATH_VOL — **CHỈ BÁO CÁO, không tự đổi hằng**, verdict V10 giữ) · **MÓT**: danh tính = TÊN MATERIAL không phải tên file đĩa (SFX kho CapCut nằm đĩa dưới HASH md5 — bug bắt khi chạy thật, dedup sót 22 file) · phân loại tên theo precedent mót tay (whoosh ≤4s / >4s = swell · subject EN+VN+plural, "fireworks"→explosion "rumbling"→rumble · UI pop/keyboard/ding/impact · scene storm→mountain_desert, crowd→people_activity... · đặt >40s không keyword = **NHẠC → staging `F:\AutoEdit\music_editor\<draft>\`, KHÔNG vào pool chọn nhạc** · còn lại hold) · "Clip ghép" compound-clip skip như voice (chứa voice trộn sẵn — chính là nửa sau voice SP1-001) · dedup 2 chiều stem (material + file đĩa) vs records/manifest chờ/hold/staging; bug 2: `Path.stem` cắt mù `.(1424901)` → 2 SFX CapCut trùng danh tính, dedup oan cả 2 chiều (fix chỉ cắt đuôi audio thật; 1 bản trùng staging đã dọn) · guard tên đụng khuôn `<kind>.wav` → tiền tố "editor - " (list_variants không nuốt file thô) · manifest đúng schema `ambient-import`/`sfx-import`, provenance `editor:<draft>` · **CHẠY THẬT 3 draft SP1**: dedup bắt 38–44 đã-biết/draft, mới thật = **15 bài nhạc (97MB staging, trùng cross-draft giữ 1 bản)** + 2 hold (SP001.MP3, 12.mp3); pooled 3 draft: **voiced 0.24 (-12,3dB) · novoice 0.32 (-9,9dB) = ĐÚNG SUBJECT_BREATH_VOL** — số máy V10 nằm giữa dải editor | ✅ **M5 XONG → C ĐỢT 3b ĐÓNG TRỌN (S1+S2+C1+S4)** — regression 3 draft SP1 ra ĐÚNG số PB10/PB11/PB13 · backup D: đã refresh (AutoEdit_C + ambient + music_editor MỚI + editor_dna.json) | pytest **372/372** (+12: DNA fixture/draft-rỗng/profile-idempotent/mine copy-manifest/rerun-0-mới/dry-run/collision-guard/hash-name/classify-rules/regression SP1×3) | 2026-07-10 |
| EL-SP1-012 | **`editor-learn` chạy draft MỚI ĐẦU TIÊN ngoài bộ hiệu chuẩn — SP1-012 "mặt tối Mặt Trăng" 25,5'** (user đưa project, "học luôn để kiểm tra"; lưu ý: user trỏ path `SP1 - 004` nhưng draft đó ĐÃ học sáng nay, folder mới thật là `SP1 - 012` thêm 11:00 — xác minh bằng text materials: 004 = corona Mặt Trời khớp content txt, 012 = tidal locking/Artemis II): DNA — nhạc 0.09 · **SFX đè voice n=41 median 0.18 = ĐÚNG SUBJECT_VOL** · whoosh 34 (~1,3/phút, dur 2,75s, vol 0.21, sát-cut 6/34) khớp dải PB11; pooled 4 draft voiced 0.21 (-13,6dB) / novoice 0.33 (-9,6dB) — số máy V10 vẫn giữa dải · **1 BUG BẮT + FIX**: "Chuo City, Yamanashi" (địa danh trong tên file côn trùng đêm Nhật) dính keyword "city" → urban_street SAI; thêm rule `nature_forest_field` (insect/cricket/forest) TRƯỚC urban_street, KHÔNG thêm từ "nature" (giữ gió về sky_cloud) +2 assert regression · mót: 11 ambient (explosion 4 · rocket 3 · nature 2 · signal 1 · sky_cloud 1) + 1 whoosh + 2 nhạc staging + 5 hold · dedup 27 đã-biết cross-draft; chạy lại = 0 mới (46 đã-biết) cả TRƯỚC lẫn SAU import · **ĐÃ NẠP LUÔN**: `ambient-import` 11/11 (kho space: explosion 7 · rocket 7 · nature_forest_field 4 · signal 2...) + `sfx-import` 1/1 (whoosh ×16) | ✅ vòng học project-mới chạy trọn end-to-end lần đầu | pytest **372/372** (+2 assert trong classify-rules) | 2026-07-10 |
| NẠP-KHO-0710 | **Nạp kho theo duyệt user (data-only, 0 dòng code): 17 nhạc editor vào POOL + ocean ×10** — (1) 17 bài staging `music_editor\` copy vào `music\tracks\` tên quy ước `SP1-xxx - <tên gốc> __mood` (artist = mã draft giữ nguồn gốc; mood MÁY MAP từ tên tiếng Việt — bảng ở §NẠP-KHO-0710, user chỉnh bằng đổi tên/overrides.yaml; "2 3 được" KHÔNG đoán được → không mood, chờ user đặt) → `music-import` 39 bài 0 lỗi (22 cũ + 17), staging GIỮ NGUYÊN làm hồ sơ mót · (2) user mua "gentle ocean waves" về `F:\AutoEdit\ambient\ocean waves\` → manifest tên riêng `ocean_waves_2026-07-10.yaml` (né đè .done.yaml cũ) → `ambient-import` 10/10 kind **`ocean` ×10** — beat biển HẾT IM (đóng nợ V8 mục 1); file nguồn giữ nguyên ngoài niche folder; file dài nhiều phút an toàn (scheduler chỉ cắt lát từ đầu, chỉ file NGẮN hơn ô mới cần loop = đường drone) · backup D: refresh (ambient +22 file · AutoEdit_C +19) · **user chốt design chapter-title (backlog)**: đơn giản, dạng basic, FONT VIẾT HOA, dễ nhìn | ✅ XONG — nhạc editor vào pool sẽ đi ké cổng TAI video kiểm C đợt 4 (nếu mood lệch, núm chỉnh = tên file `__mood`) | data-only, không đổi code — pytest không đụng (372 giữ nguyên) | 2026-07-10 |
| C-ĐỢT-4-PB14 | **PB14: đo punch-in trên 4 draft editor TRƯỚC khi code (MO_TA_VAN_HANH_C_DOT_4.md user duyệt; bài học PB12 whoosh)** — script repo `scripts_phan_tich_pb14_punch_in.py` quét keyframe scale mọi track video + dò punch-bằng-cắt (2 segment cùng material nguồn nối tiếp scale nhảy ≥5%): **(B) punch-bằng-cắt = 0 tuyệt đối cả 4 draft** · **(A) keyframe giữa clip**: track PHỦ toàn pop-in/out animation overlay (0.01→nền — máy đã có lớp này); track CHÍNH chỉ **5–7 cú zoom thật / ~104 phút (~0,06/phút)**, mức TO x1.27–x1.94 (không phải 10–20% foundation), ramp 0.7–2.5s hoặc drift 4–5s, vị trí = khoảnh khắc drama (hook 13s, reveal) — sát TEXT ≤0.5s chỉ ~40%, không có pattern máy bám được · **VERDICT đề xuất: KHÔNG code punch-in auto** (giống số phận whoosh PB12: luật đặt sẽ là suy diễn; 1-2 cú/video editor tự thêm 30 giây việc tay; đúng f2 §4 "rắc đều = nhiễu") — cú zoom hiếm này ghi vào f2 làm tri thức · foundation f2 đã vá block "📌 LỆCH SO VỚI BẢN GỐC" (luật ghi-lệch user chốt 2026-07-10, memory foundation-deviation-rule): Ken Burns đóng 120-130% ≠ dự kiến 105-115%, hiện trạng keyframe outdated | ✅ **USER DUYỆT verdict 2026-07-10 ("duyệt theo ý bạn") → C ĐỢT 4 ĐÓNG bằng kết luận đo, KHÔNG code punch-in auto** — kế tiếp: đợt 5 C5 vision gate; video kiểm đợt 5 gánh luôn cổng TAI nhạc editor | data-only + script đo (không đụng pipeline) — pytest 372 giữ nguyên | 2026-07-10 |
| C-ĐỢT-5-M1M2 | **C5 vision gate top-pick — mô tả duyệt + code M1+M2** (`MO_TA_VAN_HANH_C5_VISION_GATE.md` user DUYỆT 2026-07-10, chốt cả 3: soi lead-pick **MỌI beat qua phễu** (PA-A) · **C3 quyền-trừ-điểm ĐÓNG — giữ warning-only vĩnh viễn, xóa backlog** · code luôn): tầng gác CUỐI lần đầu nhìn FRAME THẬT ngay trước chốt pick — bắt lớp lỗi chữ-nói-dối b60 / không-ground-truth b68 / stock "đỏ rực không chữ mars" (3c V123) · **M1** `ranker/visiongate.py`: `GateVerdict` (subject/mood yes\|no\|unsure + seen/reason tiếng Việt cho editor) + `VisionGate` GLM-4.6V 1 frame GIỮA 960px, đủ bộ bài học PB3/PB4 (chống schema-echo 2 lớp · feedback-retry · thinking OFF · api.z.ai) · **M2** cắm vòng pick `_pick_by_funnel`: CHỈ soi ứng viên sắp thành shot CHÍNH, budget 2 verdict/beat — subject "no" lần 1 = demote thử ứng viên kế, lần 2 = GIỮ bản điểm phễu CAO NHẤT + warning SOÁT TAY (đúng nguyên tắc user V123 §3c: không needs_human mới, không cửa loại thứ 3); "unsure" = pass (phân vân không veto, y c2); **mood "no" = warning-only** (filter-overload-guard); fail-open mọi lỗi + TẮT gate sau 3 lỗi (GLM sập không kéo lê ~95 beat); ứng viên bị chê KHÔNG ghi sổ P7/ledger (beat sau vẫn dùng được, file tải rồi nằm lại assets/ làm alternate) · log `vision_gate` vào rank_log + dòng tổng stage RANK + card report "C5 vision gate" (bảng cho user phán trúng/oan từng dòng → quyết nâng mood lên demote hay giữ) · CLI `source` tự tạo gate khi bật phễu (thiếu GLM key = tắt + hành vi cũ nguyên vẹn); đường heuristic không-brain + entity + shot thở + extra_shots KHÔNG soi · ước tính SP012: ~105 call ≈ $0.10 + 5-10 phút/video | ✅ M1+M2 XONG — kế tiếp **M3 video kiểm SP012 → V11** (re-source cùng input, cổng MẮT C5 trúng/oan + cổng TAI ké 17 nhạc editor + ocean ×10 lần đầu chạy thật) | pytest **385/385** (+13: unit visiongate 7 · tích hợp gate-trong-phễu 6) | 2026-07-10 |
| C-ĐỢT-5-M3 | **Video kiểm V11 — 3 lần chạy source + 2 gói vá gate theo đo thật**: **lần 1** (soi mọi beat PA-A) gate CHẾT 3 lỗi thoáng qua đầu run (1 timeout + 2×429/1305) → 92 beat không soi; vá **lì đòn** (commit `3df984a`): xoay 3 GLM key theo attempt + backoff 429 4-12s + tắt theo 3 lỗi LIÊN TIẾP reset-khi-thành-công + smoke-test bắt thêm **bệnh echo-schema dai 4/4 lần** (GLM chép schema thay vì trả verdict, ~36s/ca) → vá retry chìa-lại-example. **Lần 2** gate sống 0 lỗi nhưng ĐO pace 30s/beat → cả run ~48' vs 31' không-gate (+17'); user hỏi "job này là gì, có nên bỏ?" → đưa số đo + 3 option → **USER CHỐT cùng ngày: BỎ schema block khỏi prompt (echo biến mất, call còn 3-6s) + THU SCOPE về CHỈ soi pick KHO LOCAL** (`GATE_SOURCES=("local",)`, mở lại PA-A = thêm "pexels") — commit `eab93b3`, pytest 388/388, MO_TA vá block 📌 ĐIỀU CHỈNH. **Lần 3 (chính thức)**: 95/95 ok · **gate soi 22 · pass 19 · DEMOTE 3 · giữ-dù-nghi 0 · mood-warning 0 · lỗi 0** — 3 ca chê đọc đều có lý (b63 clip trường-hấp-dẫn MẶT TRỜI cho beat Mặt Trăng — đúng lớp b60 chữ-nói-dối · b70 người ngắm trời sao lệch ý beat · b89 hạt nhân nguyên tử ≠ hai điểm sáng không gian), cả 3 demote sang ứng viên kế êm · phễu 1083 ứng viên/3%/5%/sàn 0/needs_human 0 · local thắng 19 · viral 12 cảnh/7 nguồn · pace ~20s/beat (gate local-only chỉ +2', $0.02) → assemble **draft `SCRIPT_20260709_071612_V11`** (bak-truoc-v11): **nhạc 4 chương TOÀN bài editor mới nạp** (SP1-003 deep dark/nhẹ nhàng vô tận/căng dần 2 + SP1-001 căng dần — pool 39 lần đầu ra trận) · ambient 7/7 · drone 624s · 6 SFX chủ thể · 12 beat slow-mo · KB 8 ảnh · report card C5 lần đầu hiện | ✅ **CỔNG MẮT + TAI ĐẠT (user 2026-07-10: "mọi thứ đã ok, duyệt qua") → C ĐỢT 5 ĐÓNG TRỌN = HẾT NHÓM C.** Quan sát user: **"gate chọn lại chưa ngon lắm nhưng chấp nhận được"** — gạt trúng nhưng ứng viên THAY chỉ tốt bằng pool; theo dõi video sau, dồn ca thay-xoàng mới cải thiện bước chọn-thay. Mood-warning giữ nguyên hiện trạng (0 ca phát ra, chưa có dữ liệu phán) | pytest **388/388** (+1 test scope local-only; run thật 3 lần) | 2026-07-10 |
| YTREF-M0 | **Mô tả vận hành: nạp video YouTube THAM KHẢO + ĐIỂM NHÔ + TAG BỐI CẢNH** (`MO_TA_VAN_HANH_YTREF_DIEM_NHO.md` **DUYỆT TRỌN 2026-07-10** — user chèn việc này TRƯỚC A1/scale): quy trình = editor tải 3–6 video YouTube liên quan chủ đề (GIỮ tên file YTDown chứa YouTube ID, vd bộ `F:\SPACE\MOON VIDEO YOUTUBE THAM KHAO` 3 video 1080p) → CapCut **TÁCH CẢNH TỰ ĐỘNG** (editor KHÔNG tuyển tay, ~2'/video) → `library-ingest --source-class viral` (ống PB4/C8-NAP nguyên, luật c8 nguyên: ledger kề ±1 + trần 8% + zoom 112% + -an). Máy tự: rút ID từ tên material → yt-dlp lấy **heatmap Most Replayed** (bê thuật toán `peaks.py` từ tool ME OutlierY của user — chân/đỉnh, NMS 20s, primary/secondary, BỎ minor; module mới `library/ytpeaks.py`; dep mới yt-dlp pin version; fail-open toàn tầng) → gắn cờ cảnh giao cửa sổ [foot, apex+1s] vào **2 cột db mới `peak_value`/`peak_type`** → phễu **`PEAK_BONUS=0.5`** trong `_diem_may`. **3 quyết định chốt:** (1) cảnh >20s BỎ — bug CapCut dò trượt chuyển cảnh, `VIRAL_DROP_S=20` đếm too_long, NGOẠI LỆ cảnh có điểm nhô → cắt **6s NEO ĐỈNH** (cả cảnh 10–20s điểm nhô cũng neo đỉnh thay khúc giữa); (2) trần >20s áp **MỌI mẻ viral từ nay**, cũ không hồi tố; (3) PEAK_BONUS=0.5 ủy quyền Claude chốt (max giữ bất biến c5: spread máy 2.0→2.5 < NGHIA_W 3.0, phẳng primary+secondary, 🔸 chỉnh sau video kiểm) — bonus phải chảy CẢ 2 đường rank per-beat + batch PA-1. **GỘP gói TAG BỐI CẢNH §3i** (user duyệt "chất lượng đầu ra tốt nhất, chấp nhận tag lại"): nền 2a/2b có sẵn, nối 3 khoảng trống — source_title = **tiêu đề THẬT yt-dlp** thay stem tên file cụt · **section_hint** map scene→YouTube chapter (ca 5-hành-tinh/5-quốc-gia mỗi chương 1 thực thể) · flag **`--topic`** mọi mẻ own/viral (ca video-1-hòn-đảo, tên file mã số); RANH GIỚI GIỮ: luật không-đoán 2b làm phanh + transcript câu-theo-câu KHÔNG dùng (vết b60 b-roll) + stock_tags/C5 gate KHÔNG đổi (mắt độc lập bắt tag nói dối); A/B mù ~40 cảnh MOON 2 cách kiểu PB6 trong M2. **Transcript chốt KHÔNG cần cho footage** (tool lấy transcript của user để dành cho feature phân tích kịch bản sau). Gia cố kèm: scene_index đánh theo (nguồn, source_start) thay timeline toàn cục — rà consumer dna d1/c7 khi code. Bẫy phải nhớ: `_row_to_candidate` PHẢI mang 2 cột mới (vết PB7 duration rơi). **BỔ SUNG cùng ngày (user chốt): MỌI nguồn viral từ nay PHẢI kèm URL/YouTube ID** (tên file hoặc urls.txt) → viral hưởng trọn tag bối cảnh + cờ điểm nhô y ytref (1 đường nạp duy nhất; thiếu ID → nạp được + warning). **SMOKE KIỂM THẬT trước code** (yt-dlp 2026.07.04/uvx, bộ MOON): heatmap **3/3** video (100 điểm/video, đỉnh thật 13:04 value 1.00) · chapters **1/3** (TY9dnrbQano 6 chương The Moon/Far Side/Cube/Lava/Water — đúng ca mỗi-chương-một-chủ-đề; 2/3 không có → fail-open bắt buộc) · duration file↔YouTube lệch <0,5s/21' (0,03% ≪ ngưỡng 3%) · tiêu đề thật sạch hơn stem cụt | ✅ **M0 DUYỆT TRỌN + SMOKE ĐẠT — KẾ TIẾP: M1** (ytpeaks + pytest + smoke URL thật) → M2 (delta ingest + tag bối cảnh + A/B + mẻ thử MOON, cổng mắt kép) → M3 (bonus phễu + report + video kiểm SP012→V12, cổng mắt+tai). Sau đạt: NHAT_KY + memory + BAN_DO_TRI_THUC + backup D: + git mốc | — (mô tả, chưa code — pytest 388/388 giữ) | 2026-07-10 |
| YTREF-M1 | **`library/ytpeaks.py` — dò đỉnh Most Replayed + rút YouTube ID + đối chiếu duration** (spec §3b/§3c/§3d): thuật toán dò đỉnh BÊ NGUYÊN từ tool ME OutlierY (`me/peaks.py` — copy tool nằm trong project, dòng mới BAN_DO_TRI_THUC nhóm B): local maxima CÓ dốc lên foot+apex · NMS ≥20s · primary ≥85%/secondary 55-84%/minor BỎ mặc định · **mở rộng `fetch_video_info`**: 1 call yt-dlp trả kèm **title THẬT + chapters chuẩn hóa** (nền tag bối cảnh §3i cho M2) — fail-open toàn tầng (mọi lỗi → `.error` + peaks rỗng, KHÔNG raise; không heatmap/chapters vẫn giữ title = ca 2/3 video M0) · **`resolve_youtube_id`** 3 nấc: khuôn YTDown `_Media_<id>_\d+_` → token 11 ký tự đứng riêng lấy CUỐI → `urls.txt` (`<tên file> = <url>`, parse v=/youtu.be/shorts/embed/live/ID trần, dòng hỏng bỏ qua) — trade-off spec chấp nhận + ghi thành test: chữ thường ĐÚNG-11-ký-tự đứng riêng rút nhầm (vd "khong-co-id") → tầng duration §3d chặn hạ nguồn · **`duration_mismatch`** lệch >3% (`DUR_TOL`) hoặc thiếu số → bảo thủ KHÔNG gắn cờ · dep MỚI `yt-dlp==2026.7.4` PIN đúng bản smoke M0 (YouTube đổi format thì bump có chủ đích) · **SMOKE URL THẬT ĐẠT** (`python -m autoedit.library.ytpeaks TY9dnrbQano`): title "What China Found on The Moon" sạch (stem cũ cụt "…on-the-Fa") · 6 chapters đúng M0 · 5 đỉnh primary/secondary top **13:04 value 1.00 khớp mắt M0** · heatmap thật lưu fixture `tests/data/ytref_TY9dnrbQano.json` → test chạy KHÔNG cần mạng | ✅ M1 XONG (cổng pytest + smoke ĐẠT) — chờ user xác nhận sang **M2** (delta ingest 3a→3g + tag bối cảnh §3i + A/B mù ~40 cảnh + mẻ thử MOON, cổng MẮT kép) | pytest **404/404** (+16 test_ytpeaks: detect giả lập 5 · heatmap thật 1 · fetch 3 · ID/urls 6 · duration 1) | 2026-07-10 |
| YTREF-M2-CODE | **Delta ingest 3a→3g + tag bối cảnh §3i — CODE + PYTEST XONG** (user chốt M1 + "tiếp tục M2" 2026-07-10; đồng thời HÚT TRỌN tri thức tool ME trước khi user xóa folder → memory `me-outliery-strategy` + BAN_DO trỏ chỗ mới + .gitignore): **db** 2 cột `peak_value REAL`/`peak_type TEXT` NULL=không cờ (khuôn migrate PB2; upsert vào nhóm CASE-preserve source_video='' — re-index thường KHÔNG xóa cờ, +test DROP COLUMN→migrate lại) · **ingest** `VIRAL_DROP_S=20` đếm `too_long` công khai + `youtube_infos_for` (1 call/video, fail-open từng nguồn, warning thiếu-ID theo luật mọi-mẻ-viral-kèm-ID) + `apply_viral_rules` THUẦN (dry-run/test gọi được): gắn cờ cảnh giao [foot, apex+1s] (1 đỉnh nhiều cảnh = nhiều cờ) · §3d lệch duration >3% bỏ cờ cả video + warning · >20s bỏ TRỪ có cờ → 6s NEO ĐỈNH clamp biên · 10-20s neo đỉnh nếu cờ/khúc giữa y cũ · **§3g** `scene_index` = thứ tự source_start TRONG TỪNG nguồn (list vẫn thứ tự timeline cho dna); **dna.py join đổi scene_index → (source_video, scene_start)** — bền cả 2 scheme, draft nạp trước fix vẫn khớp (+regression UPDATE index+100 dna vẫn ra số) · **§3i** TagJob +`section_hint`/`topic` → `_tag_instruction` 2 block mới CÙNG BẬC source_title (hint rỗng = prompt Y HỆT cũ, có test equality) → 2 engine GLM/Claude + Protocol; ingest truyền title THẬT yt-dlp (fallback stem y cũ) + chapter chứa điểm-giữa-miếng-cắt-SAU-bóp; CLI `--topic` mọi mẻ own/viral · **CLI dry-run viral soi thật**: ID/title/heatmap/đỉnh/chapters từng video + số bỏ-bóp-cờ trước khi tốn tiền; real-run in dòng "điểm nhô: X cảnh/Y đỉnh/Z video" + warnings · rà P5: `stock_tags` gọi positional không đụng · ledger đọc db không đổi code · bug bắt trong test: key dict infos phải `str(Path)` (Windows backslash) — production 2 phía cùng `str(s.source)` nhất quán · **SMOKE SỐNG 3 video MOON thật qua chính `youtube_infos_for`: 3/3 ID + title thật + heatmap (17/1/5 đỉnh) + chapters (9/0/6)** — lưu ý M0 đếm 1/3 có chapters, giờ 2/3 (YouTube thêm?), fail-open gánh | ✅ CODE M2 XONG — **CHỜ EDITOR tạo draft CapCut MOON** (kéo 3 video F:\SPACE\MOON VIDEO YOUTUBE THAM KHAO → TÁCH CẢNH tự động → lưu, ~2'/video) rồi mới chạy được: dry-run soi số → **A/B mù ~40 cảnh 2 cách tag** (user phán) → mẻ thật theo cách thắng → cổng MẮT kép đối chiếu đồ thị Most Replayed | pytest **412/412** (+8: rules cờ/bỏ/neo 1 · §3d mismatch 1 · §3g interleave 1 · e2e ytref db+title+section 1 · thiếu-ID 1 · --topic 1 · db migrate+preserve 1 · prompt §3i 1) | 2026-07-10 |
| YTREF-M2-FIX-ĐINH | **Fix cửa sổ điểm nhô theo cổng mắt user ("cắt không đúng đỉnh, đặc biệt video nhiều điểm nhô")** — A/B mù đã chạy 39/40 cảnh (1 ca GLM khăng khăng mood ngoài vocab ở CÁCH B, fail-open đúng thiết kế; script vá fail-open từng cảnh sau lần chạy 1 chết cả mẻ) + trang đối chiếu 13 clip điểm nhô → user soi ra lỗi. **TRUY GỐC:** cửa sổ gắn cờ `[foot, apex+1s]` bê từ tool ME ôm cả DỐC LÊN (đo thật fixture: dốc 9–45,6s ngay ở video ÍT đỉnh; video 17 đỉnh cờ 144/288 = 50% cảnh) — tool ME dùng cửa sổ để CẮT CLIP MỚI chân→đỉnh, ytref GẮN CỜ CẢNH CÓ SẴN nên ngữ nghĩa phải là "cảnh chứa khoảnh khắc đỉnh". **FIX 2 chỗ:** (1) cửa sổ cờ = **BIN ĐỈNH ±1s** `[apex−1, apex_end+1]` (`Peak.apex_end` MỚI = end_time bin, thuật toán dò GIỮ NGUYÊN; heatmap 100 bin ~9-15s, value đo trên bin; foot giữ làm thông tin) · (2) neo bóp 6s = **GIỮA BIN** `(apex+apex_end)/2` thay mép trái bin. MO_TA §3e/§3f vá 2 block 📌 ĐIỀU CHỈNH (luật ghi-lệch). **Số sau fix:** cờ 144→**67** · 4→**3** · 8→**9** (bin kéo dài sau apex vớt thêm cảnh đúng); trang đối chiếu v2 (`--peaks-only` MỚI trong script — tái sinh 0 GLM sau mỗi lần chỉnh luật) 13 clip: tự kiểm 5/5 mốc China nằm ĐÚNG đỉnh (785s=đỉnh 13:04 · 409-418=6:50 · 594=9:52), hết cảnh chân dốc | ✅ fix xong — **user phán lại cổng mắt (2)** trên `AB_TAG_MOON\diem_nho_doi_chieu.html` + cổng (1) bảng A/B tag vẫn treo (bảng tag KHÔNG đổi, không tốn lại GLM) | pytest **412/412** (test rules viết lại theo bin + regression cảnh-chân-dốc-KHÔNG-cờ + apex_end 2 test ytpeaks) | 2026-07-11 |
| YTREF-M2-TRIO | **User duyệt "cắt đã đúng đỉnh" + chốt luật mới: điểm nhô = 3 FOOTAGE TỪ ĐỈNH VỀ TRƯỚC** (vd đỉnh 60s → footage đắt ~4x-60s, build-up liên quan trực tiếp; "về luật không được lấy liền kề thì với điểm nhô có thể bỏ qua, vẫn lấy 3 nhưng đặt khác vị trí"): **(1) trio flagging** `apply_viral_rules` — trio = cảnh CHỨA đỉnh (giữa bin) + 2 cảnh LIỀN TRƯỚC cùng nguồn (`PEAK_RUNUP_N=3` · hở >3s `PEAK_CHAIN_GAP_S` = đứt chuỗi dừng lùi · cảnh SAU đỉnh KHÔNG cờ · cảnh dính 2 đỉnh giữ value cao) · **(2) neo cắt 6s SÁT ĐỈNH 1 công thức** `tail=min(apex_mid+3, hết cảnh)`: cảnh chứa đỉnh ôm giữa bin (y v2), cảnh build-up lấy 6s CUỐI dẫn vào đỉnh · **(3) ledger MIỄN luật kề ±1 cho cảnh mang cờ** (`viral.py::blocks` tách trùng/kề; trùng-chính-nó + trần 8% + rải nguồn ÁP NGUYÊN) · **(4) `_row_to_candidate` mang peak_value/peak_type** (làm sớm thay vì chờ M3 — ledger cần đọc; đóng luôn vết PB7) · MO_TA 📌 ĐIỀU CHỈNH 2 (§3e) + dòng ViralLedger bảng rà chồng chéo; điểm theo dõi M3: 2 cảnh cùng trio rơi 2 beat liền kề timeline → cân nhắc giãn-beat, chưa siết trước · **Số cờ sau trio: 51=17đỉnh×3 · 3=1×3 · 15=5×3 — chuỗi giữ trọn mọi đỉnh**; đối chiếu v3 tái sinh (`--peaks-only`) | ✅ code xong — **cổng MẮT kép treo user**: (1) bảng A/B tag `ab_tag_moon.html` (không đổi) · (2) điểm nhô v3 `diem_nho_doi_chieu.html` (trio build-up) → đạt cả 2 thì mẻ nạp thật ~500 cảnh | pytest **413/413** (trio test thay test bin · ledger miễn-kề +1 · provenance +2 cột peak) | 2026-07-11 |
| YTREF-M2-ĐÓNG | **Cổng MẮT KÉP ĐẠT + mẻ nạp thật 3 draft MOON → M2 ĐÓNG TRỌN**: **(1) điểm nhô v3 trio user DUYỆT** ("lần này cắt đã đúng đỉnh") · **(2) A/B mù 39 cảnh user chấm từng dòng → giải mù mapping.json: CÁCH MỚI (bối cảnh) THẮNG 10-11 / CŨ 2-3 / HÒA 25-26** — mới thắng cả vùng KHÔNG chapters (title+topic gánh: 7 dòng đầu Artemis) lẫn vùng section_hint (The Cube ×2, Lava); cũ thắng lẻ tẻ không thành cụm = không vùng nào TỆ ĐI; ghi chú user dòng 26 xác nhận vai trò `--topic` (footage chung chung được neo về chủ đề); 1 dòng mơ hồ ("24: phải" sau khi 24 đã hòa — nhiều khả năng là dòng 40) kết cục không đổi → **CHỐT tag bối cảnh là mặc định mọi mẻ viral** · **MẺ THẬT** `library-ingest space "<draft>" --source-class viral --topic "the Moon, lunar exploration"` ×3 tuần tự (kiểm job nền sót trước — luật leftover-check): **cắt 493 · tag 488/493 vào db** (kho space → 2362 asset) · quá ngắn <2s bỏ 165 · >20s bỏ 19 · bóp 6s 49 · **cờ điểm nhô 67/69 vào db** (Artemis 51/51 · Dark-Side 3/3 · China 13/15 — khớp trio lý thuyết trừ 2) · rerun idempotent vớt 1/6 cảnh GLM bướng (PB4: 8/8 lần trả mood 'educational/scientific/historic' ngoài vocab 19 từ) — **CÒN NGỎ 5 cảnh không tag, trong đó 2 mang cờ China** (fail-open đúng thiết kế, không ép; muốn vớt nốt = tag tay hoặc chờ nới vocab mood); db KHÔNG lưu source_title (title chỉ nuôi prompt vision — đúng §3i) | ✅ **M2 ĐÓNG TRỌN** — kế tiếp **M3**: `PEAK_BONUS=0.5` trong `_diem_may` chảy CẢ 2 đường rank (per-beat + batch PA-1) + report (dòng nạp + ⭐ pick điểm nhô) + video kiểm SP012→V12 cổng MẮT+TAI (theo dõi kèm: trio 2 cảnh kề beat lộ nguồn · mood-warning C5 · 🔸 calibrate bonus); **backup D: cần refresh sau mẻ nạp lớn** (robocopy §D1) | data-only (mẻ nạp, 0 dòng code) — pytest 413/413 giữ | 2026-07-11 |
| YTREF-M3 | **PEAK_BONUS=0.5 vào phễu + report ⭐ + VIDEO KIỂM V12 DỰNG XONG** (backup D: refresh TRƯỚC khi code — library +493 file/777MB đúng mẻ MOON + cache.db, 0 FAIL; lưu ý robocopy chạy qua Git Bash bị nuốt cờ `/E`→"E:/" exit 16 — phải chạy PowerShell): **code** — `PEAK_BONUS=0.5` trong `_diem_may` (`ranker/funnel.py`) cắm ĐÚNG 1 chỗ `_finish_scoring` mà CẢ 2 đường rank cùng đi qua (per-beat `rank_beat` + batch PA-1 `rank_beat_prescored` — P5 grep xác nhận 1 call site duy nhất), spread máy 2.0→**2.5** vẫn < NGHIA_W 3.0 (test bất biến GIA CỐ: "worse" ăn trọn spread mới KỂ CẢ cờ điểm nhô vẫn phải thua 1 điểm nghĩa) · `ShotPick.peak` MỚI set lúc pick THẬT (sau C5 gate demote/ledger re-check — không phải top-1 phễu) → report bảng beat đánh dấu **⭐** + chú giải đếm shot chính · `ViralLedger.peak_picks` đếm trong `add()` (phủ lead + shot phụ + đường heuristic) → dòng viral c8 nối "· pick điểm nhô: N" (2 số đếm 2 thứ — nhãn ghi rõ tránh hiểu nhầm); dòng nạp ingest đã có từ M2 · rà P5: không consumer nào parse chuỗi warning cũ; project.json cũ thiếu key `peak` → pydantic default False an toàn · **VIDEO KIỂM V12** (re-source + assemble + report CHÍNH project SP012 95 beat, beats/cut GIỮ NGUYÊN, `bak-truoc-v12`; kiểm job nền sót: sạch): 95/95 ok · phễu 1180 ứng viên / chết kỹ thuật 3% / veto nghĩa 3% / sàn 0 / needs_human 0 · **kho MOON mới RA TRẬN: 12 cảnh** (Artemis 5+4 · China 3) trong viral c8 **15 cảnh/5 nguồn**, gate chặn 60 · **pick điểm nhô: 1** (⭐ b33 bề mặt Mặt Trăng aerial Artemis II) · **KHÔNG có 2 beat kề nhau cùng nguồn MOON** → điểm theo dõi trio-kề-beat-lộ-nguồn KHÔNG xảy ra ở video này · C5 gate soi 23 / pass 17 / demote 4 / giữ-dù-nghi 1 (b63 chê cả 2 top-pick — SOÁT TAY) / mood-warning 1 (b19) / lỗi 0 · local thắng 19 · picks đổi V11→V12 50/95 (NÃO chấm fresh — cùng cỡ V2→V3 45/95) · draft **`SCRIPT_20260709_071612_V12`**, report ⭐ hiện đúng | ✅ **CỔNG MẮT+TAI ĐẠT (user 2026-07-11: "tôi duyệt V12. duyệt M3.") → M3 ĐÓNG = YTREF ĐÓNG TRỌN CẢ GÓI (M0→M3)**. PEAK_BONUS giữ 0.5 (user duyệt không yêu cầu chỉnh — 1/15 pick viral mang cờ chấp nhận; 🔸 theo dõi video sau, dồn bằng chứng chìm/lấn mới chỉnh). Backlog còn treo: hồi tố re-tag 1874 asset cũ ~$2 · 5 cảnh MOON PB4 chưa tag · trần riêng pick-điểm-nhô/nguồn (chỉ mở khi có bằng chứng). Kế tiếp roadmap: **A1 video space mới (SP013...)** → nhóm B | pytest **417/417** (+4: bonus per-beat · batch PA-1 · ledger đếm · report ⭐; + gia cố bất biến spread<nghĩa) | 2026-07-11 |
| TCF-M1 | **File `topic + chapter video.txt` — tag bối cảnh cho project CÔNG TY (own)** (`MO_TA_VAN_HANH_TOPIC_CHAPTER_FILE.md` user DUYỆT 2026-07-11; gốc: user soi ra own chưa hưởng bối cảnh như viral ytref §3i — trước đó Claude hiểu nhầm đề xuất re-class own→viral, user bác + chốt luật memory `own-vs-viral-phan-loai`: class do người nạp KHAI, công ty KHÔNG áp trần 8%): editor đặt file vào NGAY folder draft (own = nguồn chính · viral = fallback khi YouTube trống) — dòng trước chapter đầu = tiêu đề (vào ô `topic`, **stem material GIỮ nguyên** làm source_title), dòng `M:SS Tên` = chapter (format YouTube copy từ mô tả video, **≥2 dòng mới dùng chia đoạn**, 1 dòng = rơi về chỉ-tiêu-đề) · **BẪY 2 HỆ QUY CHIẾU bắt từ lúc soi code**: own map chapter theo TIMELINE draft (`target_start`), viral theo FILE NGUỒN (`scene.start`) — test riêng từng đường, test own cố ý đặt giây nguồn/timeline lệch hẳn để map nhầm là rớt · ưu tiên: CLI `--topic` ĐÈ file (explicit thắng + warning khi khác), own thiếu cả 2 → warning nhắc; viral YouTube > file > stem · dry-run soi file trước khi tốn tiền (in tiêu đề + số chapter + 2 mẫu) · **📌 chỉnh theo file THẬT editor** (đã đặt sẵn ở SP1-012): dung nạp dòng nhãn `Topic video:`/`chapter` — bỏ nhãn, không cắt oan tiêu đề bắt đầu "Chapter..." · **DRY-RUN SP1-012 THẬT SẠCH**: 247 cảnh/1533s, tiêu đề rút đúng "What's Behind the Moon...", 7 chapter parse đủ | ✅ code + pytest + dry-run xong — **chờ user soi số dry-run (cổng M1)** rồi quyết **M2 hồi tố**: núm ép re-tag (needs_index đang skip asset đã tag) + re-tag `nap` 619 + `signature` 1108 (~$2; địa danh 6.300 KHÔNG re-tag) | pytest **425/425** (+8: parser 3 [format chuẩn · format THẬT SP1-012 · thiếu/1-chapter] · e2e own-timeline-frame 1 · CLI-đè-file 1 · own-thiếu-topic-warning 1 · viral-fallback-source-frame 1 · viral-YouTube-thắng-file 1) | 2026-07-11 |
| TCF-M2a | **Núm `--retag` + RE-TAG THẬT BÀI ĐẦU TIÊN (SP1-001) — đo lỗi + thời gian theo yêu cầu user** (user duyệt M1 "duyệt qua" + chỉ định bài): `--retag` ép tag lại cảnh đã có db (bỏ check needs_index; clip TÁI DÙNG không cắt lại — đo thật cắt mới 0/120; upsert đè tag cũ; chạy đúng --source-class mẻ gốc) + test 3 nhịp nạp→resume-skip→retag (fix fake_cut test ghi đè file làm mtime mới — bản thật tái dùng) · **SỐ ĐO SP1-001** (video 26,8', file topic+chapter THẬT editor đặt sẵn: tiêu đề + 8 chapter parse chuẩn): 120 cảnh **tag lại 118, LỖI 2** (PB4 quen: GLM khăng khăng mood 'busy' ngoài vocab 19 từ — 2 cảnh ĐÁM ĐÔNG/THÀNH PHỐ rush-hour NY + chân người đi bộ, 'busy' đúng nghĩa thật nhưng vocab nhạc không có; fail-open giữ tag cũ) · **TỔNG 181 GIÂY (3'01\")** = **~6,8s/phút video** (~1,5s/cảnh, 3 key × 3 luồng) ≈ $0,11 · db giữ 2362 (đè, không thêm dòng) · mẫu 5 tag soi ngẫu nhiên: subject/desc cụ thể sạch | ✅ đo xong — **ngoại suy hồi tố trọn kho: nap 619 + signature 1108 = 1.727 asset ≈ ~43' GLM + ~$1,6** — chờ user gật chạy cả kho (draft nào editor đặt thêm file topic+chapter thì hưởng trọn chapter, không thì vẫn hưởng prompt title/topic mới) | pytest **426/426** (+1 retag 3-nhịp) | 2026-07-11 |
| TCF-M2b | **HỒI TỐ TRỌN KHO PROJECT CÔNG TY XONG — 3/3 draft SP1** (user gật "làm tiếp trọn kho"): re-tag SP1-003 (236 cảnh/tag 233/lỗi 3) + SP1-004 (250/244/6) tuần tự sau SP1-001 (120/118/2) — **tổng 606 cảnh, tag lại 595, lỗi 11** (fail-open GIỮ tag cũ, kho không mất gì: 8 mood-ngoài-vocab PB4 + 2 'busy' đám đông + 1 contentFilter 1301 cảnh alien), cả 3 draft đều có file topic+chapter editor đặt sẵn · **thời gian 743s (12'23") cho ~80' video = ~9,3s/phút video** (~$0,55) · db giữ 2362 (đè không thêm dòng) · soi mẫu: cảnh thực thể ra TÊN RIÊNG ("Parker Solar Probe" đúng video corona), cảnh abstract giữ trung thực ("space visualization" — luật không-đoán) · backup D: AutoEdit_C refresh (F: không đổi — cắt mới 0) · **SCOPE CORRECTION so con số duyệt ban đầu (1.727)**: `signature` 1.108 soi ra là kho TRAVEL retirement-abroad (không phải space như Claude ước lúc tư vấn) — file stock lẻ, folder ground-truth rất rõ (`signature/NGHỈ HƯU/NGƯỜI GIÀ TRAVEL`), tag 2026-06-16 đã tốt sẵn, KHÔNG có topic/chapter để hưởng → **BỎ, đỡ ~$1 vô ích** + khỏi code núm retag cho đường index | ✅ M2b ĐÓNG — **CÒN NGỎ (chưa làm, cần user gọi): (1) viral CŨ 1.209 asset** (Astrum/Destiny/OpenDown... tag trước ytref) — re-tag hứa hẹn nhất còn lại: tự tra YouTube title+chapters + HỒI TỐ CỜ ĐIỂM NHÔ, NHƯNG luật cắt đổi giữa 2 đời (bóp-giữa→neo-đỉnh, sàn 1s→2s) làm tên clip lệch → cần mô tả vận hành riêng trước khi làm; **(2) 46 asset space lẻ** (vũ trụ/người ngắm sao...) folder ground-truth gánh, bỏ | data-only (mẻ re-tag, dùng code M2a) — pytest 426/426 giữ | 2026-07-11 |
| SP1-014 | **Chạy thật A1 — video space MỚI SP1-014 (Artemis 2), lần đầu trọn gói: nạp nguồn + dựng L2b sâu cùng phiên.** Nạp 4 draft Artemis (dry-run soi ID/heatmap trước): 924→1.032 cảnh viral vào kho (cờ điểm nhô 56 cảnh/4 video, 4 lỗi tag fail-open), kho space 2.640→3.280. ⚠ PHÁT HIỆN INPUT: `voice 1.mp3` là file LẠC (Chapter 1 bài cực Mặt Trời) — quy luật voice N=Chapter N ⇒ **Hook+Ch1 Artemis THIẾU audio** (memory `sp1-014-voice1-thieu`); xử: dựng bản SẠCH ch2→end (script cắt tại token 856, voice 2-10 = 2.625,6s, align 96,9%). Đạo diễn phiên sống 12 chương/244 beat → máy gác trả 146 lỗi (ước 0,39s/từ sai, voice thật ~0,45s/từ) → script hậu xử lý chia theo timestamp thật 454 beat → pass vòng 3; bản ch2-end dịch bằng script (word index −856) pass ngay: **410 beat**. Source 2h19′ (408 beat): local-first 190/389 beat có ứng viên kho · kho thắng 53 pick · viral 51 cảnh/6 nguồn · gate chặn 2.395 lượt · ⭐8 pick điểm nhô · 2 beat needs_human. Assemble 35′: nhạc 10 chương theo mood + ducking + ambient 29/29 ô thở + 44 overlay + 2 chart + 1 info-card + Ken Burns 17 ảnh. **Draft `SP1_014_ARTEMIS_2_CH2_END_20260711_042901`** + report.html. Số đo B1 (máy): ingest 4 nguồn ~50′ · align 5′ · đạo diễn+gác ~37′ (song song ingest) · cut 45″ · source 2h19′ · assemble 35′ — tổng lệnh→draft **3h56′**. | 🔄 CHỜ CỔNG MẮT user (draft ch2→end) + CHỜ user bổ sung voice 1 đúng để dựng bản full | direct-ingest 410 beat pass · pipeline exit 0 toàn tuyến | 2026-07-11 |
| REF | **Gói REF — ưu tiên NGUỒN VIDEO MẪU CỦA BÀI (user chốt sau bug generic-footage SP1-014).** `source --ref <folder>` (khai 1 lần, dính project.json): chèn pool ≤6 cảnh/beat match NỚI trúng ≥1 từ CHỈ trong tập nguồn mẫu · REF_BONUS 1,0 điểm máy (thắng khi nghĩa ngang, không lật nổi 1 điểm nghĩa=3,0) · trần viral 15% riêng nguồn mẫu (nguồn khác 8%), luật kề/rải mềm giữ nguyên. + luật CHỮ skill dựng-video: NICHE-ANCHOR concept + thứ tự ingest-trước-direct-context + specific=ngôn-ngữ-Pexels. Vá SP1-014: re-source 12 beat lỗi per-beat (ledger nạp lại sổ) → 10/12 sang cảnh kho Artemis (b003 sơ đồ tàu, b019 Orion, b090 lắp ráp SLS); b018 Pexels thắng đúng quyền phễu; b091 khôi phục pick cũ (CÒN NGỎ soát tay). **Draft `SP1_014_ARTEMIS_2_CH2_END_20260711_042901_V2`** + report.html mới. Mô tả vận hành + rà chồng chéo: `MO_TA_VAN_HANH_REF.md`. | 🔄 CHỜ CỔNG MẮT user (draft _V2, soi kỹ ch1-2) | 4 pytest hồi quy mới · FULL 429 pass · re-assemble exit 0 | 2026-07-11 |
| SP1-014-FULL | **Dựng bản FULL SP1-014 (user bổ sung voice1 đúng — 371s, transcribe khớp nguyên văn hook Artemis).** Concat voice 1→10 = 2.996,8s → project `sp1-014-artemis-2-full-20260711-092216` → align 6′42″ (6.821 từ, 206 nội suy = 97,0%) → **dịch draft NGƯỢC**: ch1-2 từ `.bak` bản gốc + ch3-12 từ draft ch2-end shift +856 (chapter +2) + **vá 12/12 concept/queries REF theo start_word** → fix-pass 464 beat (chia 6, thở 43) → ingest pass **462 beat** → cut 35″ → **source `--ref` 3h09′**: 458 ok/2 graphic/2 needs_human (b416-417 "shadowed crater" = đúng 2 beat 362-363 cũ +54) · nguồn: local 141/pexels 300/entity 18 · **131/462 pick từ 4 video mẫu (REF hết công suất — bản cũ chỉ 53 pick kho)** · viral 152 cảnh/7 nguồn, nguồn top 296s SÁT trần 15% (bản 8% cũ chỉ cho 159s) · gate chặn 4.131 lượt · ⭐16 điểm nhô → assemble 30′33″ (nhạc 12 chương + ducking + ambient 32/32 ô thở + 52 overlay + 2 chart + 1 info-card + Ken Burns 18 ảnh + 2 lỗ hở b416-417 editor đắp) → report OK. **Draft `SP1_014_ARTEMIS_2_FULL_20260711_092216`**. Tổng máy voice→draft **~3h48′**. ⚠ QUAN SÁT: 12 beat vùng lỗi cũ lần này chỉ 3 REF/9 Pexels (phễu chấm nghĩa độc lập mỗi lần — đúng quyền thiết kế REF-không-đè-nghĩa; toàn video thì kho thắng lớn) — cổng mắt soi kỹ ch2-3, nếu còn generic thì re-source per-beat như đợt vá. | 🔄 CHỜ CỔNG MẮT user (draft FULL — soi kỹ ch2-3 + b294 sáng lệch chương + 2 beat needs_human 416-417) | data-only (code REF giữ nguyên) · pipeline exit 0 toàn tuyến · pytest 429 giữ | 2026-07-11 |
| DEEPSEA-1 | **Mở chiến dịch niche deepsea + lệnh mới `tcf-gen`** (user giao 3 folder `E:\PROJECT NHAN BAN\{DEEPSEA 1, DEEP SEA 5, DEEP SEA 3}` = 27 folder con → **25 draft own hợp lệ ~902′**; loại 1 rỗng + 1 bản sao MD5). User chốt: **máy TỰ SINH title+chapter từ voice** (không điền tay, không duyệt từng cái) — sổ theo dõi xuyên phiên `KE_HOACH_NAP_DEEPSEA.md` (root) để /clear xong chạy tiếp. Làm: (1) `library-init deepsea` + profile điền sẵn; (2) **lệnh `tcf-gen`** (`library/tcf_gen.py`): voice track → transcribe cache CHUNG pause_scan_cache (pause-dna dùng lại) → words dời source→TIMELINE → 1 call NÃO (cc_client, thinking off) đặt title + chọn chapter TRONG các mốc block 45s cho sẵn (NT4 — mốc lệch >1 block = bỏ; <2 chapter sau snap = lỗi to; transcript <200 từ = từ chối sinh mù). Bẫy draft editor xử: material `name` ≠ file đĩa → resolve theo basename `path` (vd `voi ds 1.mp3` → `voi ds 1_TRIM_7.mp3`). Chạy thật DS1-050: title "Every Layer of the Ocean Has a Stranger Squid Than the Last" + 10 chapter chuẩn timeline. | ✅ tcf-gen ĐẠT (DS1-050 kiểm tay OK) · 🔄 mẻ 24 draft còn lại đang chạy nền — trạng thái từng draft xem `KE_HOACH_NAP_DEEPSEA.md` | pytest **434/434** (5 mới test_tcf_gen.py) | 2026-07-12 |
| DEEPSEA-2 | **Nạp deepsea bước 3→8 ĐÓNG TRỌN trong 1 ngày** (sổ `KE_HOACH_NAP_DEEPSEA.md`): TCF 24 draft (2 bẫy voice vá: name≠file đĩa → basename `path`; placeholder `Resources/local` → `_resolve_rel`) · quyết trùng: DS1-053 = DS-53 v2 cùng tập (loại), DS1_074 Clip ghép (hoãn) → **ingest 23 draft = kho deepsea 8.981 asset** (99,85%; fix ingest path chết `D:/`→`materials/<basename>`; 12 mood tài liệu educational/creepy... vào `_MOOD_SYNONYMS` tiền lệ PB4, retry vớt +295) · **DNA per-niche trả công rõ**: 11,9 cut/ph · shot p50 4,63s · close-up 20% vs space 9,4/6,2s/2,5%; pause-DNA kết câu 4,2/ph nghe-ra p50 2,41s · chèn +20,3% · thở p50 2,76s (thống nhất resolver voice: `voice_files_of` map path đĩa, cache TCF↔pause-dna chung 1 lượt transcribe) · **editor-learn 23 draft** (vá `resolve_media` fallback basename) → import **57 ambient (ocean 27) + 28 SFX**, rerun 0-mới ✅, backup D: refresh · CÒN: cổng TAI 90 nhạc staging + bàn routing entity + video kiểm (bước 9-10) | ✅ bước 3-8 ĐÓNG — chờ cổng TAI nhạc + video kiểm | pytest **436/436** (regression: placeholder path · dead-path fallback · mood deepsea) | 2026-07-13 |
| MUSIC-SYNC-M0 | **Gói MUSIC SYNC mở màn (mô tả `MO_TA_VAN_HANH_MUSIC_SYNC.md` user duyệt 2026-07-13; nền tảng = nghiên cứu 26 draft editor + 30 video kênh top, memory `editor-music-sync-study`) — M0 analyzer nhịp/accent cho MỌI bài nhạc:** `music/analyze.py` thêm `analyze_rhythm` (beat_times · downbeats ước lượng pha nhóm-4 · accents pctl 70 min-gap 1s · beat_quality = onset-tại-beat/nền chống bẫy librosa bịa grid ~120BPM) → **tier A (nhịp rõ, full sync) / B (yếu, chỉ accent) / C (ambient, TẮT sync — beat_times bịa KHÔNG lưu, fail-open)**; `analyze_track` gộp rhythm cùng 1 lượt load; import cache-hit vẫn tự NÂNG CẤP record cũ thiếu grid; `regrid_index` + CLI `music-analyze [--regrid]` · **backfill thật 128 bài: A=76 B=50 C=2, quality min 1.28/median 2.19/max 7.13** — ⚠ vài ambient deepsea tên tay lọt A (q~2.08) → đề xuất nâng A≥2.2, CHỜ user chốt ngưỡng 🔸 · 📌 LỆCH MO_TA §2: không đo ở staging music_editor (mồ côi — cổng duy nhất vào phễu là music-import, nay luôn đo) | ✅ M0 XONG — chờ user chốt ngưỡng tier + duyệt sang M1 (stage `music` giữa cut→source) | pytest **441/441** (+5 rhythm: click 120BPM=A đúng chu kỳ 0,5s · drone=C không giữ grid bịa · import idempotent · nâng cấp record cũ · regrid) | 2026-07-13 |
| MUSIC-SYNC-M1 | **Chốt ngưỡng tier + M-STAGE: stage `music` OPTIONAL giữa cut→source (user ủy quyền "tự chốt, quyết định tiếp"):** tier CHỐT **B≥1.3 / A≥2.2** (dải 2.0-2.2 pool = ambient tên tay + dreamy nhẹ; chi phí sai bất đối xứng — regrid pool: **A=61 B=65 C=2**) · `Stage.MUSIC` + `MusicPlanEntry`/`music_plan` (project.py) · `music/plan.py`: `run_music` = `select_music` NGUYÊN VẸN 100% + neo offset ±2s về downbeat(A)/accent(B) trừ SNAP_LEAD 0.08 + min(XFADE, timeline_start) chương sau (điểm nhấn rơi đúng CẮT CHƯƠNG, không phải đầu segment nhạc) + usage đếm tại stage · stale: `run_cut` gọi `mark_music_stale` (timeline đổi → plan XÓA + stage về pending) · assemble: có plan dùng nguyên file+offset KHÔNG chọn lại/KHÔNG đếm usage đôi, không plan = đường cũ từng dòng nguyên vẹn · CLI `music` (hàm `music_cmd` — bẫy trùng tên tham số `--music` của run) + `run --music-sync` mặc định TẮT · `done()` .get chống KeyError project.json cũ · `MUSIC_XFADE`+`chapters_with_time` dời assembler→plan.py (2 nơi cùng cần, tránh 2 bản lệch P5) | ✅ M1 XONG — kế tiếp M2 M-VOL (cổng TAI cần video kiểm + user) | pytest **451/451** (+10 plan: 4 anchor thuần · chọn Y HỆT đường cũ · neo accent · đòi cut done · stale · 2 e2e assemble plan-đúng-offset-µs/fallback-đếm-usage) | 2026-07-13 |
| MUSIC-SYNC-M2 | **M-VOL: volume nhạc theo zone hook/body + ducking zone-aware (chỉ khi có music_plan — mặc định TẮT = nguyên trạng V10):** ducking.py bảng 🔸 HOOK_DUCK space 0.35/deepsea 0.30/default 0.30 + hook_duck_for(niche) · _lay_music nhận volume · _add_music_by_chapter: chương ĐẦU timeline (hook=chương 0 user chốt) volume tĩnh theo niche · _duck_music: envelope RIÊNG zone hook, clip phân zone theo TRUNG ĐIỂM, warning "M-VOL hook nép X tới Ys" · body giữ 0.2/0.5 V10, BREATH_VOL/RAMP/MIN_BREATH không đổi · video kiểm dựng sẵn: SP012 music+assemble thật → draft **SCRIPT_20260709_071612_V13** (4/4 chương neo accent/downbeat, ch4 tier A downbeat 22.89s) | ✅ ĐẠT CỔNG TAI (user nghe V13 "mọi thứ có vẻ ổn" 2026-07-13) | pytest **454/454** (+3 M-VOL: map niche · e2e hook 0.35/body 0.2 + keyframe nép đúng zone · e2e không plan 0.2 phẳng) | 2026-07-13 |
| MUSIC-SYNC-M3 | **M-ACCENT snap + M-CHANGE neo đổi nhạc (chỉ khi có music_plan):** vòng 3 kiểm giả thuyết user "nhạc nhanh cắt beat rõ hơn" trên dữ liệu cũ → null cả tier A/tempo nhanh (editor 0.96-1.02, kênh top 0.85-0.89) = KHÔNG tính lại cho space/deepsea, travel = ngữ pháp montage CHƯA đo (cửa: tier A + M-GRID + knob niche) · coverage.py `snap_to_accents` (mép chung → accent−80ms, tol 0.3, trần 15% ưu tiên hook>vào-ô-thở>body, hook thắng J-cut / body J-cut miễn, MIN_SHOT 0.7 giữ, miễn giữa-miếng-thở) + field j_cut_start · plan.py `music_boundaries` (đổi nhạc neo mép cắt ±2s) + `timeline_accents` (bất biến P) + 🔸 M_CHANGE_XFADE deepsea 0.5/space 3.0 · assembler wire sau J-cut trước invariant; boundaries + xfade niche + offset giữ P vào _add_music_by_chapter · draft kiểm **SCRIPT_20260709_071612_V14**: snap 3/105 (body −50..−35ms) + M-CHANGE 3/3 + M-VOL hook 0.35 | ✅ ĐẠT CỔNG MẮT+TAI (user duyệt V14 2026-07-13) | pytest **461/461** (+7 M3) | 2026-07-13 |
| MUSIC-SYNC-M4 | **Đóng gói: cờ M-GRID thử nghiệm + report + make.** `music --sync-targets grid` (field `music_sync_targets` project.json): HOOK snap theo DOWNBEAT (tier A; B rỗng rơi về accent) — công tắc kiểm trực giác "cắt theo lưới nhịp", ĐỂ DÀNH cho video TRAVEL đầu tiên (vòng 3 đã chứng minh space/deepsea không cần; travel = ngữ pháp montage chưa đo) · report M7 khối "Nhạc nền theo chương — MUSIC SYNC" (bài/tier/offset/neo per chương) · `make --music-sync` pass-through (bug OptionInfo né sẵn) · CÁCH DÙNG: space dựng mới thêm `--music-sync` (đã qua 2 cổng V13+V14); deepsea video kiểm sắp tới BẬT để check tai hook 0.30 + đổi-nhạc-thẳng 0.5s (CHƯA nghe); travel chờ nguồn đo | ✅ GÓI MUSIC SYNC ĐÓNG (M-GRID chờ video travel) | pytest **462/462** (+1 M-GRID) | 2026-07-13 |
| SHOT-THO-3 | **Shot thở 3.0 — LIÊN TỤC CHỦ THỂ** (user 2026-07-13 xác nhận SAI LOGIC TỪ ĐẦU sau khi gặp lại ở DS5-083 đúng lỗi từng thấy ở space): luật chọn đổi hẳn — BỎ "đắt"/wide-aerial + mood-chủ-đạo → **chủ thể trùng clip liền trước +3,0/token (trần 9,0)** · khác cỡ cảnh nâng 2,0 · mood hạ 0,5 phụ trợ · token nền niche (>25% pool: underwater/ocean...) không tính, đo runtime tự thích nghi niche · neo CỐ ĐỊNH mọi miếng trong ô "tiếp tục là cá mập" (bỏ chuỗi-mood-nối 2.0) · neo = db local theo path / `visual_concept` cho stock-gen. Kèm 2 bug ngầm lộ ở DS5-083: **mood câm** (`_mood_set` không split mood ghép `awe_urgent_cautionary` → 29/31 miếng note "mood —", máy chỉ còn dài+wide/aerial → thuyền cá→orca, sói→asteroid, domino→pterodactyl) + **pool đói** (`videos_for_niche` trần 500 mới-index-nhất = 6% kho deepsea 7.940 video own). Tài liệu viết lại: `MO_TA_VAN_HANH_SHOT_THO.md §7` + 📌 LỆCH `foundation/d2-hinh-tho.md` | ✅ ĐÓNG TRỌN (DS5-083 dựng lại: 31/31 miếng dur khớp bản cũ, cổng số §7.4 đạt; **cổng MẮT user DUYỆT 2026-07-13**) | pytest **474/474** (+6 test breath mới, 3 hồi quy tái hiện bug trước-fix) | 2026-07-13 |
| BAN-THUOC | **Luật "bán thuốc" — VOICE kể ẩn dụ, HÌNH kể câu chuyện (mọi niche, `MO_TA_VAN_HANH_BAN_THUOC.md`).** User xác nhận lỗi hệ thống (space + DS5-083): script mượn ẩn dụ domain ngoài (Jenga/domino) hoặc nói-với-người-xem → NÃO minh họa nghĩa đen ("tall wooden Jenga tower") thay vì kể tiếp câu chuyện chương; 11/270 beat DS5-083 bệnh trong khi 45/56 beat metaphorical NÃO TỰ nghĩ đều đúng in-world → bệnh chỉ phát khi script mang sẵn ẩn dụ. 3 lỗ vá: pass 1 nhét "(Jenga tower metaphor)" vào central_subject (đầu độc neo) · pass 2 ngoại lệ ABSTRACT + từ điển ẩn dụ generic xúi off-world · **đường sâu mù hoàn toàn** (direct_context.md 0 luật, skill còn ngoại lệ "ẩn dụ chủ đích vẫn generic"). Sửa 5 chỗ: prompts.py (2 qualifier từ điển + pass 1 cấm tu từ trong central_subject + SCRIPT-SIDE METAPHOR RULE/direct-address pass 2) · `_BAN_THUOC_BLOCK` tự sinh trong direct_context.md · skill dung-video · 📌 LỆCH foundation/c2. Kèm lưới máy `ban_thuoc_warnings` ở direct-ingest (0-token-trùng, gọt số nhiều, entity/graphic miễn, **warning-only** — FP bình thường: DS5-083 kêu 32/soi tay 0 cần sửa). Retrofit DS5-083: khử độc central_subject ch1 + viết lại 11 concept + re-source lẻ qua phễu c5 thật (seed ledger 137 pick viral + REF, P7 giữ) 11/11 ok → re-pick breath 31 miếng dur khớp 100% (b048 nautilus→great white; b050 lộ concept nhiễm "title-card opener" → gọt, kho không seagrass nên về fox như bản đã duyệt) → assemble _V2. | ✅ ĐÓNG TRỌN (**cổng MẮT user DUYỆT 2026-07-13** trên draft _V2; adherence prompt đo tiếp ở video dựng mới kế — lưới máy báo sớm ở direct-ingest) | pytest **478/478** (+4: 2 prompt mang luật · 1 hồi quy lưới Jenga-trong-chương-cá-mập · 1 fail-open) | 2026-07-13 |
| PORTABLE | **Draft PORTABLE + folder xuất `E:\CapCut Drafts` (`MO_TA_VAN_HANH_PORTABLE.md`).** Gốc: SP1-014 copy sang máy editor → footage "Không thể tải xuống tài liệu" KHÔNG cho relink (path tuyệt đối máy gốc chết + check_flag 63487 pycapcut = combo "cloud thiếu" — khớp AutoClone §B4/mục 15; audio flag 3 relink được nên sống). Giải: bắt chước draft NATIVE — path content → placeholder toàn cục `##_draftpath_placeholder_0E685133-…_##/materials/…` (quét 401 file draft Mac+Win: 1 GUID duy nhất) + check_flag video → 62978047 + sổ meta file_Path `./materials/…` link theo TÊN. Cổng mắt ĐẠT 2 MÁY (bản test `_PORTABLE` + máy editor thật). Hồi tố tay SP1-014 FULL + SP1-017 trên F: (backup `_backup_json_truoc_portable`). Code: `_to_portable` TỰ ĐỘNG trong `package_draft` (trả cây mới — caller re-package được) + `machine.json::draft_out_root` + CLI `set-draft-root` (máy này đã đặt `E:\CapCut Drafts`; donor/cover vẫn theo capcut_root). Bàn giao editor = copy nguyên folder, KHÔNG relink; nhớ xóa bản hỏng cũ trước (C5). | ✅ ĐÓNG (cổng mắt 2 máy user xác nhận 2026-07-13) — CapCut máy này muốn thấy draft mới: Settings → Draft location → `E:\CapCut Drafts` | pytest **469/469** (+4 packager: portable-cross-machine regression · out_root tự tạo+cover donor · set-draft-root persist · embed theo placeholder; +1 assembler sổ `./materials/`) | 2026-07-13 |
| SFX-LOAI-A | **SFX theo LOÀI/HÀNH ĐỘNG per-niche — Milestone A (sheet 41 dòng editor deepsea, `MO_TA_VAN_HANH_SFX_LOAI.md` + `PHAN_TICH_SFX_EDITOR_DEEPSEA.md`).** User duyệt 3 đề xuất A/B/C; A+lõi B làm trước: (1) `subject_rules.yaml` per-niche THAY TRỌN SUBJECT_RULES built-in (niche mới = editor điền 1 sheet → 1 yaml, 0 code; space không yaml = 0 đổi hành vi) · (2) `subject_kind()` match CỤM TỪ word-boundary ("sperm whale" ≠ "humpback whale", "sunset" vẫn không ăn "sun") + `rules=` luồn qua resolve_slot_subject/subject_beat_slots/assembler · (3) `niche_kinds()` mở validation import theo yaml · (4) mine.py classify nhận rules per-niche (học lại không phình hold) + fix `_kw` số dán đuôi ("cá nhà táng2"/"Water Whoosh2" — \b không ăn) · (5) NẠP KHO deepsea 28 file + re-kind 2: whale_sperm 6 · whale_humpback 9 · whale_blue 3 · whale_orca 1 · attack 4 · splash 5 (ocean_14/21 re-kind — tiếng cá voi thở không phải pad sóng) · default +2 (dưới nước 4/Dưới nước 2 rút khỏi staging nhạc — bị classify NHẠC >40s); hold 323→301. Bảng deepsea CỐ Ý không dùng bare sea/ocean/whale/predator (1919/10.618 asset — chống kêu loạn); đo thật 3.000 asset: 454 match, loài trước hành động ("killer whale attacking" → tiếng orca). Rerun editor-learn DS1_046+DS3_017 dry-run = 0-mới ✓. CÒN: milestone C mật độ (user chốt thân bài = 50% hook) + ~8 file thiếu chờ folder `D:\Sounds Edit` máy editor (orca kêu!) | ✅ A ĐÓNG (cổng tai đi ké video kiểm deepsea kế — chung cổng music-sync hook 0.30) | pytest **481/481** (+3: phrase per-niche · yaml kinds+import · classify rules+số dán) | 2026-07-13 |
| HOOK-SFX | **S3-HOOK: hit/whoosh/click tại CUT trong hook — deepsea (`MO_TA_VAN_HANH_HOOK_SFX.md` + `PHAN_TICH_HOOK_SFX_EDITOR_DEEPSEA.md`).** ĐO TRƯỚC 23 draft editor: hook median **4,8 SFX/phút = 3× thân bài**, 0/23 draft hook trống, bám CUT 48% ±0,25s (TEXT 3% — deepsea NGƯỢC PB12 space → luật per-niche `HOOK_SFX_NICHES=("deepsea",)`, PB12 KHÔNG lật), 13% lead 0-200ms trước cut. Code: `hook_sfx_slots()` pure (click TẠI cut vào ẢNH trần 4 + impact TẠI cut-accent M-SNAP + whoosh TRƯỚC cut 80ms; chỉ BÙ tới 4,8/ph — đếm S2/C1/UI-sfx vào mật độ; gap 3s) + `_add_hook_sfx` cuối chuỗi audio (track sfx, UI-SFX giữ chỗ, xoay biến thể seed crc32, không fade-in giữ attack, fail-open mọi nấc) + `cuts_log` từ `_place_video_l1` + truyền `music_accents` + field `hook_sfx_log`. Kho: nạp 18 file editor vào **ambient per-niche** (impact 7 · whoosh 6 · click 5) — CỐ Ý không vào ~/AutoEdit/sfx toàn cục (rotation overlay mọi niche); `AMBIENT_KINDS += HOOK_SFX_KINDS`. Vol **0,2 🔸** (quy tương quan PB10: editor 0,56 × 0,18/0,5). | ✅ CODE ĐÓNG — dựng V4 DS5-083, **CỔNG TAI user CHỜ** (5 lớp hook: voice·nhạc 0,30·bed 0,25·S2/C1·S3) | pytest **490/490** (+5: density/gap/kinds · click-cap+busy · bounds · wire places · niche gate) | 2026-07-13 |
| SFX-NUOC-DONG | **Gói nước-động (từ 4 vấn đề user nêu trên DS5-083 V3 — chẩn đoán ghi memory `ds5-083-4-van-de-sfx-lap`):** kind `water_churn` MỚI 10 file bubble/gurgle (folder editor "Nước động") + `ocean` thêm 8 cụm mặt-biển-động (choppy · rough sea(s) · stormy sea/ocean · surf · foam(y) — đo kho 10.618 asset trước khi thêm, "surf" word-boundary không dính "surface") + `tag-stock` lại 4 pick stock fail của DS5-083 → **b43 ra tag "turbulent ocean waves crashing" → kind `ocean`** (lỗi thật của b43 = THIẾU TAG VISION chứ không phải thiếu keyword). Đo precision trên 270 pick thật: bỏ bare `swirl/swirling` (b220 "green smoke swirling" ăn nhầm bubble foley) → cụm 2 chiều (swirling sand / sediment swirling). Sau gói: DS5-083 +6 beat có tiếng mới (b43 ocean + 5 water_churn đều qua "bubbles" thật). **0 dòng code đổi** — thuần data yaml + kho. CÒN NGỎ: b75/b142 fail GLM "mood ngoài vocabulary" sau 4-retry → asset vĩnh viễn mù tag, lỗ chờ quyết | ✅ ĐÓNG DATA (tai đi ké video kiểm deepsea; seabird b85 user tự nghe lại V3 — máy ĐÃ đặt đúng 560.8s vol 0.18) | pytest **485/485** (0 code đổi, suite nguyên) | 2026-07-13 |
| SFX-LOAI-C | **Milestone C: GỠ TRẦN S2 match-driven + bed ục ục GATE CẢNH + nạp SOUNDEFFECT (`MO_TA_VAN_HANH_SFX_LOAI.md §5+5b`).** User đổi chốt mật độ: "KHÔNG có mật độ — footage phù hợp là để sfx" → bỏ SUBJ_CAP/không-kề/≤2-lần-kind (áp cả space; giữ ảnh/đồ họa/beat-ngắn/SUBJ_MAX). Bed "ục ục": đo 23 draft editor = `dưới nước 4` + 2 biến thể → kind `drone` deepsea, 🔸 vol 0.25; **user sửa nhận định cùng ngày: KHÔNG loop cả bài — sheet nói CHỈ CẢNH DƯỚI NƯỚC** → `bed_intervals()` gate theo scene pick từng beat (`DRONE_SCENE_BY_NICHE deepsea=underwater`, gộp beat liền, `BED_MIN 6s`, mù db = tắt; đo lại 23 draft xác nhận 383 đoạn/gap thật). Nạp `F:\DEEPSEA\SOUNDEFFECT` 37 file (orca KÊU +2 · underwater 13 · nature_water 2 vá 2 lỗ scene fallback 8.498+923 asset · signal/ocean/fire/humpback) + seabird tách ocean. Sheet **39/41 dòng có tiếng**. Smoke DS5-083: bed 33 run phủ 67% đúng dải editor. | ✅ C ĐÓNG CODE (cổng TAI chờ video kiểm: 4 lớp bed 0.25 🔸 + loài không trần + nhạc + M-VOL hook 0.30) | pytest **485/485** (+3 gate: merge/min · 2 run vol 0.25 · mù tag tắt; hồi quy trần-đảo-chiều + space loop giữ) | 2026-07-13 |
| HOOK-SFX-SPACE | **S3-HOOK mở cho SPACE — MƯỢN số deepsea 🔸 (user chốt 2026-07-14: "2 niche gần giống nhau; sau này space có số liệu rồi sẽ áp dụng số liệu của space") + chuẩn hóa QUY TRÌNH lấy mẫu SFX niche mới.** (1) Nạp kho `F:\AutoEdit\ambient\space` đúng 18 file cùng nguồn editor `F:\DEEPSEA\SOUNDEFFECT` (impact 7 · whoosh 6 · click 5, qua manifest — records truy license). (2) `HOOK_SFX_NICHES = ("deepsea", "space")` + 📌 comment mượn số; test gate niche-off đổi space→travel + hồi quy `"space" in hook_sfx_niches()`. (3) 📌 LỆCH + **§3b rà chồng chéo riêng space** vào `MO_TA_VAN_HANH_HOOK_SFX.md` (điểm căng duy nhất: PB12 đo space whoosh bám TEXT — S3 bám CUT là làm KHÁC editor space, cổng tai trọng tài; click sẽ NỔ THẬT vì space nhiều ảnh Ken Burns ≠ deepsea V4 0 click; 4/6 whoosh vị nước "Underwater Whoosh" trong video vũ trụ — chê thì lọc file). (4) **`QUY_TRINH_LAY_MAU_SFX_NICHE_MOI.md`** B1→B6 (editor-learn → sheet→yaml → nạp kho → ĐO hook → quyết gate/hằng số → cổng tai; B5b đường tắt mượn số) + bảo tồn 2 script scratchpad vào **`scripts\`** (`do_hook_editor.py` tổng quát hóa nhận `<niche> <roots...>` — smoke DS1-050 khớp số cũ; `nap_hook_sfx.py` template 3 hằng) | ✅ CODE ĐÓNG — hiệu lực từ video SPACE dựng mới kế tiếp (cổng TAI đi ké, KHÔNG dựng lại video cũ) | pytest **490/490** (test gate sửa + 1 assert hồi quy) | 2026-07-14 |
| HOOK-SFX-V4-TAI | **CỔNG TAI V4 DS5-083: MẬT ĐỘ RỚT — `HOOK_SFX_PM` còn 30% (4,8 → 1,44/phút, CẢ 2 niche).** User nghe hook V4: "chỉ có tiếng whoosh với impact xuất hiện dày đặc làm khó chịu; giảm tần suất 2 tiếng này ở cả space và deepsea xuống 30% so với hiện tại". Cơ chế: whoosh+impact sinh từ deficit theo `HOOK_SFX_PM` → hạ 1 hằng phủ cả 2 niche (số dùng chung); click KHÔNG đổi (luật riêng bám ảnh trần 4 — hook V4 không có click); vol 0,2 🔸 giữ (chưa có phán quyết riêng). Số đo editor 4,8 GIỮ trong PHAN_TICH — bài học ghi vào QUY_TRINH B5: **số đo editor là điểm xuất phát, cổng tai đè**. Test: density case 250s (round 1,44×250/60=6) + hồi quy "hook 60s giờ bù 1 tiếng (trước: 5)" + wire hook 90s. Kiểm V5 thật: hook 154s S3 **10 → 3 tiếng = đúng 30%** (impact 3 tại cut-accent 21,1/62,5/75,3s — accent ưu tiên ăn hết deficit nên whoosh 0; click 0 hook không ảnh) | ✅ ĐÓNG TRỌN — **cổng TAI _V5 user DUYỆT 2026-07-14** ("duyệt qua v5"; các 🔸 nghe chung cổng này — S3 0,2 · bed 0,25 · M-VOL 0,30 — qua ở mức hiện tại, chỉnh nếu sau chê) | pytest **490/490** | 2026-07-14 |
| DS3-084 | **Video deepsea MỚI "Womb Cannibalism" (cá mập hổ cát ăn thịt trong tử cung) — music-sync, đường sâu fan-out 6 chương.** Voice 19:38/2479 từ/6 chương → **230 beat**/33 ô thở/timeline 21:49. Đạo diễn = 6 agent Claude Code SONG SONG (ch6=546 từ > ~424 timeout `direct`) + normalizer python (coerce schema + tách beat >10s + cap 1 rhetorical/chương + xóa query graphic) → direct-ingest vòng 2 pass. **Source `--ref F:\DEEPSEA\VIDEO MAU\DS084`**: 183 ok/7 graphic/40 needs_human · kho thắng 39 · viral c8 46 cảnh/8 nguồn · pexels 116 · entity 32. **BUG FIX phẫu thuật:** `subject_beat_slots` crash `Path(None)` khi beat needs_human có ShotPick asset_path=None (ảnh entity hỏng) — DS5-083 có 0 needs_human nên chưa lộ; guard `or not pick.asset_path` 1 dòng (P5: chỉ dòng này thiếu, consumer khác đã guard). **Draft `E:\CapCut Drafts\DS3_084_WOMB_CANNIBALISM_20260713_224919_V2`** (folder crash đầu dời recycle_bin). Thời gian: align 103s · direct fan-out ~5-6′ (có retry connection-closed) · cut 16s · source ~42′ (~32s/beat) · assemble 50s · lõi ~50′ | ✅ **ĐÓNG TRỌN — user DUYỆT 2026-07-14** (draft _V2; 40 needs_human editor tự đắp) | pytest **491/491** (+1 regression `test_subject_beat_slots_skips_none_asset_path`) | 2026-07-14 |
| CARD-DEEP | **Đường sâu 0 info_card (DS5-083 + DS3-084 + SP1-017 đều 0, mọi bài direct cũ đều có) — vá tầng dạy, KHÔNG dựng lại DS3-084 (user chốt).** Nguyên nhân: đường sâu không ăn `prompts.py` (_INFO_CARD_RULES 19 dòng + "mỗi chương NÊN ≥1 card/chart") — `direct_context.md` chỉ in TRẦN "≤2 card/chương", SKILL không nhắc chữ card nào → đạo diễn phiên sống + agent fan-out không biết công cụ tồn tại (ống dưới nhận card ngon: schema/validator/render/assemble đủ). Fix: ① `live.py::_CONG_CU_HINH_BLOCK` vào direct_context MỌI video sâu (bản RÚT GỌN 13 dòng — user cảnh báo nhồi lệnh là LLM rơi lệnh; format chi tiết đã nằm trong description schema.py) ② SKILL fan-out ghim ví dụ `info_card` dict nguyên văn + bước tóm tắt thêm "0 card = bất thường, soi lại". Kèm AUDIT tải LLM: phần LUẬT direct_context chỉ ~1,4k tok (transcript chiếm 82-92%) — không quá tải; tải thật nằm ở 12 foundation ~22,6k tok/phiên đạo diễn (bằng chứng rơi lệnh: card 0, overlay chuỗi trần); phễu batch/GLM nhẹ; **đồng hồ token đang MÙ** (rank_log median 4 tok, cost_log 1 entry out 200k = số rác — backlog sửa ghi token) | ✅ CODE ĐÓNG — hiệu lực từ video sâu kế tiếp (cổng mắt đi ké; DS3-084 KHÔNG dựng lại) | pytest **501/501** (+1 `test_direct_context_cong_cu_hinh_block`) | 2026-07-14 |
| FOOTAGE-084 | **DS3-084 footage "hết" ở 18:36 (voice 21:30) + 40 needs_human/bài — điều tra ra 2 BUG NỀN có từ đầu + gói 3 fix, user chốt "tool tự điền hết".** BUG A (mất sync): assembler chừa LỖ HỞ needs_human trên track video chính, nhưng **main track CapCut là track NAM CHÂM — mở draft là dồn sạch lỗ, ghi đè draft_content.json** (bằng chứng: draft_info.json tool ghi end=21:48/27 lỗ 187s ĐÚNG vs draft_content.json CapCut ghi lại 11:58 end=18:42/0 lỗ) → footage sau lỗ đầu (b84@8:49) trượt tích lũy -187s. BUG B (needs_human oan): `db.search_assets` cắt TOP-limit theo ORDER cố định TRƯỚC, luật P7 đã-dùng lọc SAU → video 230 beat lặp query 'shark', 5 dòng đầu cạn là mọi beat sau trắng tay dù kho match 1000 (26/39 beat); +2 bug anh em cùng pattern: top kho deepsea theo indexed_at = TOÀN VIRAL (mẻ viral nạp sau chiếm đầu bảng) & lọc người-world-lock sau cap. FIX ① used/viral/người lọc TRONG SQL trước limit (`search_assets`/`signature_assets` + 3 `find_*_candidates` + nền lót graphic). FIX ② `_fill_holes_with_slug`: mọi lỗ còn sót trên video_l1 lấp ảnh "EDITOR: ĐẮP FOOTAGE" (giữ sync, editor thấy ô cần đắp). FIX ③ SÀN NICHE `_floor_pick`: beat mọi route đầu hàng → thang 3 nấc heuristic KHÔNG-NÃO từ kho own (query gốc → đuôi danh từ → vocab kho; world-lock gạt cảnh có người WRONG-vs-BLAND; nhãn `source="floor"` + warning để editor soát). Retrofit: `retrofit_floor.py` đắp **39/39 beat, 0 needs_human** → **draft `..._V5` video_l1 306 seg phủ kín 0→21:48.97, 0 lỗ, 0 slug cần dùng**, overlay 22 text giữ nguyên. Ghi chú: Opus 4.8 KHÔNG phải nguyên nhân (bug nền có từ đầu; bài 230 beat 1 chủ thể chỉ là chất xúc tác lộ bug) | ✅ **ĐÓNG TRỌN — cổng mắt _V5 user DUYỆT 2026-07-14** (39 floor + 22 overlay qua) | pytest **500/500** (+6: exclude-used local/signature · slug needs_human · slug asset hỏng · sàn 3 test) | 2026-07-14 |
| OVERLAY-084 | **DS3-084 mất TRẮNG overlay text — điều tra + retrofit + vá gốc (3 việc user duyệt).** Nguyên nhân: 6 agent fan-out trả `overlays` dạng CHUỖI TRẦN (`"2 wombs"`) thay vì dict; `assemble_director_draft.py::norm_overlay` loại êm mọi non-dict (0 warning) → 25 overlay/24 beat rơi hết (DS5-083 38 dict chuẩn nên không dính). ① Vá normalizer: coerce chuỗi→dict (kind digit→stat, anchor=đầu beat) + đếm in `coerce/DROPPED` (cấm loại êm) + fix anh-em split-beat nhân đôi overlays sang cả 2 nửa (lọc theo nửa chứa anchor). ② Ghim SKILL `dung-video`: mục "Fan-out chương dài" — block SCHEMA BẮT BUỘC phải kèm ví dụ overlays dict nguyên văn + trỏ normalizer template. ③ `retrofit_overlays.py`: 25 chuỗi → **23 overlay** vào project.json (anchor = từ trùng token trong range beat gốc, fallback đầu beat; 2 bỏ do trùng text liền kề; backup `.bak_truoc_overlay_retrofit`) → assemble **draft `..._V4`** (né bẫy base-trẻ-hơn-V3 bằng pre-create folder base rỗng rồi xóa): **22 text + 22 SFX lên draft** (1 rơi đúng luật beat 14 có chart) + report lại | 🔄 **CỔNG MẮT _V4 CHỜ** (chỉ soi 22 overlay — world-lock _V3 user đã duyệt trước) | pytest **494/494** · normalizer rerun 25 coerce/0 drop · draft_content _V4 track text 22 segment | 2026-07-14 |
| TEMPO-MAP | **Nâng cấp nhịp độ theo feedback đạo diễn hình ảnh ("video đều đều" — LLM nhận cấu trúc 3 hồi, rule nhịp theo hồi + shuffle tempo), user duyệt hướng + chốt "tự suy nghĩ và code, tính toán kỹ".** Chẩn đoán 3 lỗ: fan-out dispatch không có dòng tempo (agent mù nhau ra nhịp trung bình) · trong chương không có luật nhịp theo vị trí · cảnh báo "đều" chỉ chạy SAU assemble. **T1 (dạy):** `ChapterPlan.tempo_curve` 5 curve (fast_settle hook — luật hook nhanh THẮNG "mở chậm" của ĐDHA / slow_build_slow thân / build / dense / calm) + block TEMPO MAP vào direct_context (shuffle: cấm 3 chương liền kề cùng curve; nhanh/chậm TƯƠNG ĐỐI quanh DNA niche) + SKILL ghim dòng TEMPO vào dispatch fan-out + prompts pass 1 đường cũ + d1-pacing cập nhật. **T2 (gác):** `validator.check_tempo_map` warning-only tại direct-ingest CẢ 2 đường (① phẳng giữa chương max/min<1.3 ② đều tăm tắp std/med<0.25 ③ khai-vs-thực theo curve + shuffle + chưa khai). **NHẠC — nạp 29 bài `E:\NHỊP NHANH` (pool 128→156, 1 Impera trùng parser tự gộp) → LỘ ROOT CAUSE: energy librosa = rms.mean/rms.max = độ PHẲNG (29 bài tai-nhanh đo 0 high, dreamy đo "beat" 118-145/phút) → DRIVE SCORE thay hẳn:** mood 0.6 + beat_tier 0.25 + bpm 0.15, chấm bài TẠI ĐOẠN SẼ VÀO (`entry_intensity` energy_curve trong-bài — ý user "1 bài nhiều đoạn bpm khác nhau"). Commit `c501213`(mốc an toàn)→`c13b020`(drive)→`4aeadfc`(tempo map). N2 đổi-nhạc-theo-đoạn CHƯA code (chờ tempo map qua cổng mắt). Còn ngỏ: cặp trùng audio khác tên `SP1-003 - căng dần nhịp cuốn`=`căng dần nhịp cuốn` (2 mẻ) — select có thể lấy cả 2 trong 1 video. **KIỂM TAI 2026-07-14: dựng lại DS3-084 chỉ rerun music+assemble (footage/overlay _V5 giữ nguyên) → draft `..._V6`: 6/6 chương đổi bài (4/6 từ mẻ NHỊP NHANH), 6/6 offset neo accent/downbeat, 5/5 điểm đổi nhạc neo cut.** Sự cố giữa chừng: **ổ E: đầy 100%** (assemble chết Errno 28, bản _V6 chép dở 121MB đã xóa) — user tự dọn draft cũ còn ~54GB; bẫy version né bằng pre-create folder base rỗng → ra đúng _V6 | ✅ **NHẠC DRIVE SCORE — cổng TAI user DUYỆT 2026-07-14 trên DS3-084 _V6** ("nghe đã ổn") · 🔄 tempo_curve CHỜ CỔNG MẮT video sâu DỰNG MỚI (outline 084 cũ chưa có curve, 6 chương đều "medium" — bản _V6 chưa kiểm được phần này) | pytest **508/508** (+3 drive +4 tempo) | 2026-07-14 |
| TOC-3B-DL | **Tải Pexels song song kiểu WARM-UP** (user chốt "làm luôn" ngay sau TOC-SOURCE — xác nhận .env có 10 key Pexels; tải = link CDN không ăn quota search): chunk vừa có verdict NÃO → `_prefetch_plan` chọn top-điểm-NÃO-thuần mỗi beat (chỉ stock có url; né veto/đã-dùng/ledger lúc lập kế hoạch) → `_DlPool` 4 luồng tải TRƯỚC vào đúng tên đích (`_stock_dest` tách chung `_materialize`); `_TimedStock.download` thêm KHÓA THEO ĐÍCH + tái dùng file nằm sẵn ffprobe đọc được (file cụt → None → tải lại, không bao giờ nhận rác). **PICK KHÔNG ĐỔI** — warm-up trượt chỉ phí file mồ côi, fallback 4.7/P7/ledger nguyên vẹn (ghi sổ vẫn chỉ tại pick). Knob `AUTOEDIT_DL_PARALLEL` (0 = tắt; conftest tắt trong suite chống nhiễu đếm). Perf thêm `dl_reuse` đo tỉ lệ warm-up trúng (kỳ vọng ≥60-70%). Dự đoán cộng dồn: SP1-cỡ source ~40-55′, DS5-cỡ ~25-35′ | ✅ CODE ĐÓNG — cổng SỐ chung video thật kế tiếp | pytest **529/529** (3 mới: reuse wrapper + prefetch plan + e2e parity) | 2026-07-15 |
| TOC-SOURCE | **Gói tăng tốc TOC-1..4 (source + đo giờ)** — user giao TỰ QUYẾT 2026-07-15 ("logic khó hiểu, tự quyết hộ; KHÔNG ảnh hưởng nhiều chất lượng chọn footage; bước đơn giản dùng sonnet cho rẻ") sau điều tra 3 bài (NHAT_KY_TOC_DO): source = 49-84% tổng, trong đó NÃO **viết output** ≈ 78% source DS5-083 (43-57 call × 10-12k token out, tuần tự) — thủ phạm chính: prompt bắt echo `asset_key` = nguyên path F:\ tới 165 ký tự trong TỪNG verdict (50-65% output). Nguyên tắc: **chỉ tối ưu ỐNG DẪN, logic chấm/veto/sàn KHÔNG đụng.** **TOC-1** id ngắn `a`+crc32-8hex trong hội thoại NÃO (`prompts.alias_of/build_alias_maps`, funnel dịch ngược, id lạ fail-open nhánh "bỏ sót", đụng độ → giữ nguyên key, cùng asset = cùng mã xuyên beat) · **TOC-2** 3 call NÃO batch bay song song lookahead (`_plan_chunks` tĩnh y luật PA-1 + `_pump_rank`/`_resolve_rank`; gather MAIN thread — sqlite; P7+C8 vốn re-check tại pick nên không thủng; knob `AUTOEDIT_RANK_PARALLEL`, =1 là tuần tự cũ; `cc_client._log` thêm lock) · **TOC-3** normalize NỀN trong source (`_Prenorm` 2 worker ffmpeg → `media/norm/<tên>` đúng path assemble mtime-skip; ghi `part_*`→`os.replace` chống file cụt; fail-open; KHÔNG đụng chart PiP/info-card crop=False; knob `AUTOEDIT_PRENORM=0`, conftest tắt trong test) · **TOC-4** đo giờ tự động (`StageRecord.running()` started_at 9 stage + `record.perf` source: rank_calls/rank_call_s/rank_wait_s/download_s/prenorm_n/stage_s) · **model:** CLI vốn đã sonnet toàn bộ; SKILL.md ghim fan-out agent đạo diễn spawn `model:"sonnet"`. Dự đoán: DS5-cỡ source 117′→~30-40′ + assemble 20′→~5-8′; SP1-cỡ 6h→~2h. `MO_TA_VAN_HANH_TOC_DO_SOURCE.md` (rà chồng chéo đủ) + 📌 lệch ghi vào MO_TA_PHEU_BATCH | ✅ CODE ĐÓNG — **cổng SỐ chờ video thật kế tiếp** (perf tự ghi, so theo MO_TA §4); chất lượng chọn soi chung cổng mắt video đó (điểm lệch duy nhất: prev_pick_note ranh chunk cũ 1-2 chunk) | pytest **526/526** (11 mới: 5 alias TOC-1 + 4 lookahead/plan TOC-2 + 2 prenorm TOC-3 + 1 perf TOC-4, tính gộp) | 2026-07-15 |
| FOOTAGE-SPEED-090 | **Footage video chạy 0.9× (chậm 10%)** — user chốt 2026-07-15 (phạm vi: TẤT CẢ video footage track L1, local + Pexels; knob chỉnh được): `assembler.py` hằng `FOOTAGE_SPEED = 0.9` + `_place_video_l1` nhánh clip-đủ-dài đổi từ (source=want, speed=None) → (source=None, speed=0.9). **Điểm mấu chốt chống bug (đọc source pycapcut trước khi code):** truyền CẢ source lẫn speed thì pycapcut TÍNH LẠI target = round(source/speed) → lệch 1µs mép beat = SegmentOverlap (họ bug round/int cũ) — nên CHỈ truyền speed, pycapcut tự tính source = 0.9×target, **target giữ nguyên tuyệt đối** → timeline/cut/music-sync/S3-HOOK không suy chuyển. Ngưỡng đủ-dài hạ `avail ≥ want` → `avail ≥ 0.9×want` (băng giữa hết warning slow-mo); clip ngắn hơn giữ nguyên nhánh kéo giãn cũ (speed < 0.9). CHỈ video — ảnh/Ken Burns/chart/info-card/slug không đụng. Knob: `--footage-speed` (0.5–2.0) trên `assemble` + `run` (truyền tường minh né bug OptionInfo B2), 1.0 = hành vi cũ nguyên vẹn. Rà chồng chéo: phễu lọc độ dài chỉ bảo thủ hơn (cần ít nguồn hơn 10%); footage có audio thì tiếng chậm theo pitch −10% (nhánh slow-mo cũ đã vậy, không phải hành vi mới — cổng tai soi) | ✅ CODE ĐÓNG — cổng MẮT video kiểm CHỜ USER (10% chậm có khựng ở cảnh action nhanh không) | pytest **515/515** (1 regression mới: speed 0.9 + target khít µs + ảnh 1.0 + clip ngắn fallback + knob 1.0) | 2026-07-15 |
| LIFE-IN-NAP-XONG | **Đêm tự động 2026-07-14→15 (user ngủ, chốt "tự động hết + lưu sfx/music/dna"): NẠP TRỌN NICHE LIFE-IN bước 0→9.** Kho: **10.222 asset / 44 draft (99,5%)** + ambient 93 + SFX 48 + nhạc +85 (pool 241, map mood tường minh `scripts\stage_music_life_in.py`, 3 tên mù chờ tai) + `pause_dna.json` (42 draft: KET_CAU 2,88/ph p50 1,1s · 388 ô thở p50 2,43s) + `dna.json` (10,2 cut/phút · shot p50 4,07s · hold 34% · close-up 7% · chữ ký urban/landmark/people). **4 bug tìm-fix trong đêm, mỗi cái có regression test:** ① tcf-gen fallback ≤3 track (REAL72 avcodec + REAL79 nhạc thắng điểm lai) ② ghim ngôn ngữ prompt (3 draft title tiếng Việt) ③ mood documentary 2 TẦNG: +35 synonym (21+14) + validator mềm bỏ-từ-lạ-khi-còn-mood-hợp-lệ (1 từ lạ từng đánh rớt cả asset = vô hình với phễu; 104+51 cảnh fail → retry vớt 183) ④ `cuts_per_min` rơi 0 khi mega chồng nhiều track (80.148s > timeline 75.642s, hiệu âm — validator Mảnh B tự tắt oan) → fallback tổng shot thật. CÒN NGỎ: 54 cảnh lỗi lì (21 contentFilter 1301 REAL82/86) + 3 nhạc tên mù + bước 10 video kiểm chờ user | ✅ bước 0-9 ĐÓNG TRỌN — cổng mắt/tai video kiểm CHỜ USER | pytest **514/514** | 2026-07-15 |
| LIFE-IN-KHOI-DONG | **Nạp niche life-in khởi động** (sổ `KE_HOACH_NAP_LIFE_IN.md`; nguồn `E:\PROJECT NHAN BAN\REAL LIFE`, TẤT CẢ own): bước 0-1 profile ✅ (phiên trước) · **bước 2 khảo sát ĐÓNG**: 48 folder/~315GB → **danh sách ingest user chốt 44 draft ~1.261 phút (1,4× deepsea)** — loại REAL17 rỗng + hoãn 3 "phim nướng" REAL48/55/59 (main track = 1 file xuất sẵn 25-31ph chiếm 95-96% timeline, cùng họ DS1_074; đã quét seg >5ph TOÀN BỘ main track); xóa nghi vấn 6 draft nhiều file đĩa (timeline 440-562 cut chuẩn) · **bước 3 tcf-gen mẻ 1 (8 draft): 4 đạt + LÒI BUG chọn track voice** — `voice_files_of` max-segment chọn nhầm track nhạc/SFX ở draft voice-ít-cắt (REAL06/10/13/21 transcript 0 từ) → **FIX tiêu chí lai `số_segment × tổng_duration`**, kiểm 74 draft 2 niche: deepsea 26/26 GIỮ NGUYÊN track (pause-dna/TCF cũ an toàn), REAL đổi đúng 11 ca sai; max-duration đơn thuần bị bác bằng chứng DS-53 v2 (nhạc 43ph thắng voice 38ph) + REAL32 (bed 1 seg 30ph). Phụ: REAL18 NÃO trượt ngôn ngữ (title tiếng Việt dù transcript Anh + prompt đã dặn) → rerun --force | 🔄 mẻ 1 rerun 4 draft + REAL18 force đang chạy; còn 36 draft (mẻ 2-6) → ING/EL/DNA sau | pytest **511/511** (+3 regression voice track) | 2026-07-14 |
| BAN-GIAO | **Giải pháp bàn giao máy editor** (user chốt: KHÔNG đóng gói phần mềm — copy project + cài VSCode/Claude Code, editor làm mọi việc bằng prompt, user theo dõi vài tháng; tri thức fix lỗi trên máy editor PHẢI chảy về máy gốc): **`HUONG_DAN_CAI_DAT_MAY_EDITOR.md`** 6 phần — A checklist copy máy gốc (project + xuất memory `BAN_GIAO\memory_goc` + kho `F:\AutoEdit` 76GB GIỮ mtime/ký tự ổ + `~\AutoEdit` 1.3GB cache.db tag vision + 2 project tham khảo tùy chọn; 2 quyết định user: key API chung↔tách · tài khoản Claude riêng cho editor) · B cài nền tay (Python/Node/git/ffmpeg/VSCode/**Claude Code CLI global bắt buộc** vì pipeline gọi `claude -p`/CapCut 8.8.0 + donor trống) · C bootstrap 12 bước Claude Code TỰ cài (uv sync → nạp memory_goc vào memory máy mới → rewrite path cache.db nếu kho lệch ổ (tiền lệ KHO-F: library_assets + asset_usage + ambient yaml) → set-library-root/set-draft-root → register-machine → flag → FULL pytest → smoke `voice test travel` new/align/direct-context) · D kênh tri thức `BAN_GIAO\` (nhật ký máy editor + mirror memory_moi + `git bundle` chuyển code không-GitHub; sync Drive/USB; lệnh user merge trên máy gốc) · E editor dùng hằng ngày (/dung-video · prompt thêm niche · dán lỗi nguyên văn) · F sự cố biết trước. Kèm: scaffold `BAN_GIAO\` (NHAT_KY_MAY_EDITOR.md khuôn entry + memory_moi\) + **CLAUDE.md §7 luật máy editor** (gate `BAN_GIAO\MAY_EDITOR.flag` — máy gốc không flag nên luật trơ) + .gitignore 3 dòng (flag/bundle/memory_goc) | ✅ DOCS XONG — chờ user duyệt; cổng thật = bootstrap chạy trên máy editor ngày bàn giao | — (docs, không code; pytest không đổi) | 2026-07-14 |
| BAN-GIAO-2 | **v2 kho F: DÙNG CHUNG qua mạng + BỘ CÀI 1 folder** (user chốt: kết nối ổ F máy gốc cho máy editor — dữ liệu niche tập trung, editor cùng lưu footage mới 1 nơi, khỏi copy 76GB): hướng dẫn VIẾT LẠI v2 — A share toàn ổ F: (account editor riêng, map đúng chữ **F:** để path cache.db khớp nguyên trạng — hết luôn bẫy rewrite + bẫy mtime vì không copy file) + máy gốc Sleep=Never/mạng dây + 3 lệnh làm tươi bộ cài + QUY ƯỚC TẠM nạp kho/nhạc chỉ trên máy gốc (cache.db/music/sfx còn ghim `~\AutoEdit` local — grep xác nhận không override được) · B cài tay rút còn 6 việc (map F: + copy bộ cài + Node + VSCode + Claude Code + CapCut; python/git/ffmpeg để Claude Code tự winget C1) · C bootstrap sửa theo (C5 đổi thành KIỂM chữ ổ, cấm rewrite; C7 draft PHẢI ổ local; C11 thêm kiểm library-search qua mạng) · D sync qua chính ổ F: `F:\BAN_GIAO_TU_EDITOR\<editor>` (Drive/USB thành dự phòng) · F thêm 4 sự cố mạng/ổ F + mục editor Ở XA quay về copy-kho v1 · **G nâng cấp bước 2 CHỜ DUYỆT**: dời cache.db+music+sfx lên F: dùng chung (root từ machine.json + backup tự động trước mẻ nạp; lý do chưa làm: SQLite trên SMB = vùng cảnh báo ghi-đồng-thời, cần cổng test riêng). **BỘ CÀI dựng thật `F:\BO_CAI_MAY_EDITOR\`** (F: trống 810GB): `DOC_DAU_TIEN.md` + `tool edit padoma\` (kèm .env/.git/memory_goc tươi) + `AutoEdit_C\` 1.3GB | ✅ DOCS + BỘ CÀI XONG — cổng thật = bootstrap trên máy editor; PHẦN G chờ user duyệt | — (docs + copy, không code) | 2026-07-15 |
| G1-SO-CHUNG | **Sổ + nhạc + SFX dùng chung trên F:\AutoEdit (user DUYỆT G 2026-07-15; G2 db-server ĐÃ QUYẾT làm — user có VPS Ubuntu+SSH, chờ chốt kiến trúc vị trí đặt).** Code: `machine.py` thêm field `data_root` + `set_data_root`/`resolve_data_root` (đúng khuôn resolve_library_root: override > env `AUTOEDIT_DATA_ROOT` > machine.json > `~\AutoEdit` — máy chưa set KHÔNG đổi hành vi) · `db.py` `DEFAULT_DB_PATH = <data_root>/cache.db` + connect `timeout=30` (chờ khóa khi máy khác đang ghi qua SMB thay vì nổ ngay) + **`backup_cache_db()`** chụp sổ vào `<data_root>/backup/` giữ 10 bản · `music/library.py::MUSIC_ROOT` + `sfx/library.py::SFX_ROOT` theo data_root (LÚC IMPORT — đổi root xong mở process mới) · `cli.py` lệnh **`set-data-root`** + vá 4 default ghim cứng `~/AutoEdit/music` (music-init/import/analyze/list → None + resolve MUSIC_ROOT) + backup chèn trước `conn = db.connect()` ở `library-index` + `library-ingest`. **Chuyển dữ liệu máy gốc:** music 249 file/2,8GB + sfx 187 file/150MB + cache.db 164MB → `F:\AutoEdit` robocopy 0 fail → `set-data-root F:\AutoEdit` → verify đọc từ F: **34.196 asset · 5.167 usage · 241 bài nhạc · 136 SFX** → C: cũ niêm phong `C:\Users\NBPC\AutoEdit.pre-G1-backup` (xóa sau khi chạy ổn vài tuần). Hướng dẫn lên **v3**: bộ cài chỉ còn 1 folder project (bỏ AutoEdit_C) · GLM key RIÊNG mỗi editor (user chốt — bộ cài để trống, bootstrap C2 nhắc điền) · bootstrap C6 thêm set-data-root · luật A4.3 mới: 2 máy không chạy 2 mẻ NẠP cùng lúc, giai đoạn đầu 1 job/lúc; editor TỰ nạp kho/nhạc (gỡ quy ước tạm) | ✅ ĐÓNG TRỌN trên máy gốc — pytest **531/531 chạy 2 lần** (trước flip = hành vi cũ nguyên vẹn + sau flip = cấu hình mới sạch); ghi chú: vỏ rỗng `F:\AutoEdit\library\cache.db` (0MB, sót KHO-F 07/07) để nguyên — không consumer nào trỏ tới | pytest **531/531** (+2: resolver 4-nấc ưu tiên · backup tạo/prune/None) | 2026-07-15 |
| G2-M0 | **Mô tả vận hành G2 — sổ lên PostgreSQL máy gốc (LAN)** (user chốt cùng ngày: editor cùng văn phòng cùng LAN → server đặt MÁY GỐC, không VPS — độ trễ <1ms vs 20-80ms/query × hàng nghìn query/video, máy gốc đằng nào phải bật vì kho file; **VPS đổi vai = backup offsite pg_dump**, mảnh M5). Đo phạm vi: ~32 điểm SQL/10 file + 49 chỗ đặc sản SQLite/11 file (?, INSERT OR REPLACE, executescript, PRAGMA, Row, lower() Unicode tự cắm, LIKE mù hoa-thường). Kiến trúc chọn: **LỚP ĐỆM 2 LƯNG** — resolver `db_url` (env AUTOEDIT_DB_URL > machine.json > rỗng = SQLite G1) + shim psycopg; 531 test cũ giữ SQLite y nguyên + bộ test parity 2 lưng; kho FILE trên F: không đổi. Lộ trình M1 lớp đệm → M2 dựng server + di trú verify đếm 100% → M3 máy gốc flip + 1 video thật → M4 editor vào + test ghi song song + GỠ luật 1-job → M5 pg_dump→VPS; đường lui mọi mảnh = xóa db_url về SQLite G1 (đóng băng làm mốc). Rà chồng chéo §5: data_root GIỮ (quản file + fallback), backup G1 giữ cho lưng SQLite, luật 1-job chỉ gỡ SAU M4 sửa hướng dẫn + §7 cùng lúc, luật LỌC-TRONG-SQL gác bằng parity, không đụng logic chấm/veto/pick | ✅ **DUYỆT 2026-07-15** — user ủy quyền ("kiểm tra kỹ, tự quyết cẩn trọng") + chốt: **BỎ hẳn VPS** · PGDATA ban đầu `F:\QQ SQL` → Claude rà vòng 2 bắt 2 rủi ro (ổ SHARE quyền ghi = editor xóa nhầm được qua mạng; E:/F: CÙNG đĩa vật lý = giành I/O với kho + backup chết chùm) → **user ĐỔI sang `D:\QQ SQL` cùng ngày** (hướng TỐT HƠN: D: không share → khỏi khóa NTFS; khác đĩa kho → không giành I/O; dump đảo chiều sang `F:\AutoEdit\backup\pg\` vẫn 2-đĩa-khác-nhau; đổi lúc chưa cài gì = 0 chi phí). Rà vòng 2 (mô tả §8) còn chốt cách xử 6 bẫy code: lower() Unicode ('TƯ TRỊ' vào parity) · LIKE lower() 2 vế · autocommit shim · tie-break `id` (áp cả 2 lưng, qua FULL pytest) · password plaintext machine.json chấp nhận trong LAN · conn main-thread giữ. M1 code kế tiếp | — (mô tả) | 2026-07-15 |
| G2-M1 | **Lớp đệm 2 lưng ĐÓNG CODE — sổ chạy được cả SQLite lẫn Postgres, production CHƯA đổi gì (chưa máy nào trỏ db_url).** `machine.py`: field `db_url` + `set_db_url`/`resolve_db_url` (override > env `AUTOEDIT_DB_URL` > machine.json > rỗng = SQLite G1; khác data_root: đọc MỖI LẦN connect, không phải hằng import → xóa db_url là process mới về SQLite ngay). `db.py::connect(db_path=None, db_url=None)`: không tham số → resolver; **db_path tường minh → LUÔN SQLite** (chốt an toàn: 531 test cũ + script di trú không bao giờ bị kéo sang sổ thật kể cả máy đã flip — có test guard riêng); shim `PgConnection` bọc psycopg (dịch `?`→`%s` · dict_row truy cập theo tên · autocommit → `conn.commit()` no-op, lỗi 1 lệnh không làm độc transaction · executescript/executemany qua cursor) + `_pg_schema()` DỊCH từ `_SCHEMA` nguồn-duy-nhất (id → IDENTITY; **REAL → DOUBLE PRECISION — bẫy MỚI bắt khi code: REAL của PG là float 4-byte ~7 chữ số, mtime epoch ~1.7e9 mất sạch phần lẻ → needs_index so 1e-6 sẽ bắt vision-tag lại oan CẢ KHO**) + `_migrate` 2 nhánh (PRAGMA / information_schema). Rà 32 điểm SQL: 4 chỗ `INSERT OR REPLACE` (pexels · entity serper/cse · stock_tags) → viết lại `ON CONFLICT ... DO UPDATE` NGAY TẠI CALLSITE (cả 2 lưng hiểu, SQLite ≥3.24 — khỏi shim đoán conflict-target bằng parse SQL); tie-break **`, id DESC`** vào 4 query chọn lọc (search_assets/videos_for_niche/signature_assets/find_ref_candidates — §8.6 hòa điểm đổi pick sau flip); LIKE giữ nguyên (2 vế đã lower sẵn từ trước); còn lại thuần placeholder — shim gánh, 6 file sourcer/dna/schedule không phải sửa SQL. CLI **`set-db-url`** (+ `--clear` = đường lui 1 lệnh, thử kết nối ngay khi set). Dep `psycopg[binary]` vào pyproject (import trong hàm — máy SQLite không đụng). **Test parity `test_db_parity.py`** chạy CÙNG bộ thao tác 2 lưng qua fixture param (PG cần env `AUTOEDIT_TEST_PG_URL` db test RIÊNG — cố ý KHÔNG dùng AUTOEDIT_DB_URL tránh trỏ nhầm sổ thật; vắng server = skip): ca 'TƯ TRỊ' lower Unicode · mtime precision · upsert-2-lần · autocommit ghi-rồi-đọc · ON CONFLICT search_cache · tie-break id · exclude_paths/own_only/no_people · move/delete/count. Vùng ảnh hưởng đã rà: mọi caller connect() (test đều truyền path tường minh hoặc vá nguyên hàm — test_director_live:328) · không còn truy cập row theo số thứ tự · `except sqlite3.OperationalError` stock_tags giữ (PG luôn có bảng từ connect) · backup_cache_db giữ nguyên vai lưng SQLite (§5) | ✅ CODE ĐÓNG — **cổng M1 ĐẠT: FULL pytest 541 pass / 8 skip, 0 sửa test cũ** (531 cũ + 10 mới; 8 skip = ca parity lưng PG chờ server M2). Kế tiếp M2: cài PostgreSQL PGDATA `D:\QQ SQL` + migrate_g2.py — CẦN USER: password PG + xác nhận subnet văn phòng | pytest **541/541** (+10: 1 resolver db_url + 8 parity ×2 lưng + 1 guard db_path-tường-minh) | 2026-07-15 |
| LIFE-IN-DOT2 | **Nạp đợt 2 life-in: +12 draft (REAL77a + 11 kênh AMAZING nhập chung — user chốt 2026-07-16; bỏ phim nướng REAL48/55/59/69)** — quy trình y đợt 1 (sổ `KE_HOACH_NAP_LIFE_IN.md §ĐỢT 2`): pg_dump backup trước mẻ → tcf-gen 12/12 đạt 1 lần → rà trùng (REAL77a = CÙNG BÀI REAL77 chapter khớp giây → vẫn nạp, dedup nguồn-khúc tự lo, chỉ 15 trùng) → ingest 3 mẻ + vòng vớt: **kho life-in 16.305 asset (+4.143, lỗi lì 8 = 0,2%: 2 compound hỏng + 2 contentFilter 1301 + 4 validation/mạng)** → editor-learn 12/12 0 lỗi → ambient-import 33 (**animal_wildlife 6→14 + wind 15 + urban_street 21 — lấp gap RD-89**) + sfx-import 49 + nhạc `scripts\stage_music_amazing.py` 76 bài (map mood tường minh; 2 SKIP trùng; DST theo resolver MUSIC_ROOT sau G1, KHÔNG Path.home) → music-import **pool 317 bài/0 lỗi** → library-dna 56 draft (**10,8 cut/phút** · shot p50 4,2s · hold 35% · CU 1/15,8 — AMAZING kéo dày nhẹ, chữ ký vẫn urban) + pause-dna 54 draft --force sau khi so .new.json (KET_CAU 2,69/ph p50 1,08s · 538 hình thở · tool tự backup). Kèm: commit fix HOOK_SFX life-in (schedule.py) sót từ 2026-07-15 | ✅ NẠP ĐÓNG — video kiểm cổng mắt+tai vẫn CHỜ USER (bước 10 đợt 1) | pytest 541 pass/0 fail | 2026-07-16 |
| TU-NAP | **LUẬT TỰ NẠP video mẫu — mọi máy, mọi bài** (user chốt 2026-07-16: "các máy editor và máy gốc sau này chạy phải tự động nạp — kho asset công ty càng ngày càng nhiều"). Bối cảnh: soi sổ PG phát hiện mẻ DS084 (bài DS3-084, 13/07) CHƯA BAO GIỜ nạp — project khai `--ref F:\DEEPSEA\VIDEO MAU\DS084` nhưng `library_assets` 0 cảnh từ 10 video mẫu (dò cả theo tên file) → REF chạy RỖNG không báo lỗi, bài dựng bằng kho chung (khớp ghi chép "sàn 39/39"); nguyên nhân: quyết định bỏ-nạp hôm đó chỉ nằm trong hội thoại (đã clear), không thành văn. Luật mới SỬA CÙNG LÚC 3 nguồn (P5): **SKILL `/dung-video`** thêm mục "LUẬT TỰ NẠP" (có folder mẫu + draft tách cảnh → TỰ `library-ingest <niche> <draft> --source-class viral` TỪNG video TRƯỚC direct-context, không hỏi; thiếu draft video nào hỏi đúng video đó; class vẫn do NGƯỜI khai own-vs-viral; sửa luôn câu bị động "editor đã nạp" ở PHA 2) + **HUONG_DAN A4.3-4** (máy editor cùng luật) + **MO_TA_VAN_HANH_REF.md** (ghi điều kiện tiên quyết: chưa nạp = --ref rỗng im lặng). Rà chồng chéo: khuyến cáo "tránh 2 mẻ NẠP cùng niche cùng lúc" GIỮ NGUYÊN (so le khi biết, không chặn); thứ tự SP1-014 ingest-trước-direct-context GIỮ NGUYÊN (luật mới chỉ ép chạy bước đó); own-vs-viral không vênh (mẫu kênh khác mặc định viral, editor khai own khi là video công ty). Còn ngỏ: mẻ DS084 nạp bù (chờ user) | ✅ LUẬT GHI XONG (không code — 0 dòng pipeline đổi) | pytest không đổi (**549/549**) | 2026-07-16 |
| BOOST | **BOOST cảnh dạng X khán giả thích (VD3) M1 tầng phễu**: khai 2 tầng `source --boost "X@scope"` (per-video, dính inputs như --ref) + **`audience_bias` niche_profile.yaml NỐI DÂY** (field Stage-4 chết nay tiêu thụ, lọc TODO, merge trong run_source = chokepoint chống bug B2); scope all(mặc định)/hook/ch\<N\> tính PER-BEAT tại 2 call site (né staleness TOC-2); chèn ≤6 cảnh KHO/beat (`find_boost_candidates` — 3 cửa file/geo-PA2/used-trước-limit y find_ref, bọc ledger.gate) + **BOOST_BONUS 1,0** 🔸 nhãn `is_boost` chokepoint sau dedup (vết PB7), **CHỈ kho local — cảnh X kho ĐÈ cảnh X Pexels** (editor thật né Pexels); cộng dồn REF (trade-off lật-1-điểm-nghĩa user chấp nhận, bất biến MACHINE_MAX_SPREAD giữ); sàn niche ưu tiên X ở nấc vét (= "đoạn không kiếm được footage"); tầng ĐO: `ShotPick/ExtraShot.boost_hit` + warning đếm match. `MO_TA_VAN_HANH_BOOST.md` (rà chồng chéo P5 đủ 10 tầng TRƯỚC khi code). **M2 tầng NÃO (user xác nhận cùng ngày):** `boost_block` — khối SỞ THÍCH KHÁN GIẢ (4 luật: đan X vào hook/chêm/generic · neo bối cảnh chương · không ép beat có thực thể · query theo từ vựng kho) vào direct_context (đường sâu) + library_context pass-2 (đường cũ, D2 cùng 1 hàm) — KHÔNG đụng prompts.py; `direct-context --boost` (= khai đúng thời điểm, CLI echo khối); SKILL /dung-video PHA 1 bước 3 + PHA 2 nhắc tầng ĐO | ✅ CODE ĐÓNG M1 phễu + M2 NÃO — video số đo CHỜ; backlog trừ-điểm-Pexels ghi memory | pytest M1 **570/570** (+9) → M2 **572/572** (+2 director_live, parity PG thật) | 2026-07-17 |
| GHI-CONG | **Ghi công kênh nguồn (VD4) M1+M2**: cột `source_channel` trong sổ (`library-ingest --channel` explicit thắng · mẻ viral có YouTube ID TỰ lấy kênh yt-dlp · backfill kho cũ `channel-set`/`channel-audit`, so prefix Python NÉ LIKE) + luật preserve rỗng-không-đè (resume/retag không xóa backfill); kênh chảy DB→ứng viên→ShotPick/ExtraShot/BreathShot→project.json (NT1); **`assemble --credit`** đặt TÊN KÊNH 1/4 góc màn hình (crc32 deterministic, track text `credit` riêng, span = đúng miếng L1; slug/chart/card không credit). **Sửa kèm bug anh em: REF `LIKE` prefix Windows trên PG (`\` = ký tự escape) → REF rỗng im lặng sau flip — thay `substr` 2 lưng như nhau**, regression parity chạy THẬT trên PG. Audit sổ thật: **164 folder nguồn/3 niche đều CHƯA có kênh** → `BAO_CAO_CHANNEL_AUDIT_2026-07-17.txt` chờ user/editor điền | ✅ CODE ĐÓNG M1+M2 (commit e068b74 + e5c8eb2) — 🔄 góc credit ±0.72/±0.80 size 8 CHỜ CỔNG MẮT · kho chờ điền kênh | pytest **560/560 0 skip** (+11 test, parity PG thật) | 2026-07-17 |
| G2-M4 | **Máy editor ĐẦU TIÊN vào sổ Postgres qua LAN + GỠ LUẬT 1-JOB — nhiều máy dựng song song được.** User tự cài tool lên máy editor (bộ cài F:) rồi giao tiếp M4. ① Máy gốc pre-check: service Running/Automatic · `listen_addresses='*'` · pg_hba `192.168.1.0/24 scram` · firewall rule Enabled · **kết nối qua hostname `DESKTOP-98SCPHI` đi đúng đường LAN 192.168.1.214** (không loopback — chứng minh DSN hostname sống trước khi đưa editor). ② Hướng dẫn 1 file cho Claude Code máy editor tự chạy (`F:\AutoEdit\scripts\HUONG_DAN_M4_MAY_EDITOR.md`, sau M4 thay bằng C6b chính thức): ping hostname → kiểm bootstrap → `set-db-url "host=DESKTOP-98SCPHI ..."` (tự test kết nối) → vế editor test song song. ③ **`scripts\test_ghi_song_song.py`** (mới, đứng ngoài package): db `autoedit_test` KHÔNG đụng sổ thật, ghi qua ĐÚNG shim (`db.connect(db_url=...)`), barrier 2 máy tự đồng bộ qua chính PG, mỗi máy 200 INSERT khóa riêng + 100 UPSERT tranh chấp CÙNG khóa, verify chéo cuối; chạy thử 2-process trên máy gốc trước khi làm thật; `--cleanup` dọn bảng. ④ Gỡ luật 1-job SỬA CÙNG LÚC (đúng kế hoạch chống 2-nguồn-luật-vênh): HUONG_DAN A4.3 (luật mới: chỉ còn khuyến cáo nhẹ tránh 2 mẻ NẠP cùng NICHE — vì file kho, không vì sổ) + C6b (bước set-db-url bootstrap, password HỎI USER không nằm trong repo) + PHẦN E (dựng song song ĐƯỢC) + PHẦN F (3 sự cố mới: connection refused/hostname · database is locked = máy chưa set-db-url · malformed chỉ còn ở mốc lui) + PHẦN G (tiến độ) + CLAUDE.md §7 (bỏ câu "chỉ 1 job mỗi lúc"). 📌 LỆCH cổng gốc (ghi MO_TA §4): thay "2 mẻ nạp + 2 video cùng lúc" bằng test ghi tổng hợp CÓ TRANH CHẤP KHÓA — đụng độ sổ mạnh hơn; video song song thật = theo dõi vận hành, sự cố PHẦN F đỡ. Vùng ảnh hưởng đã rà: script mới đứng ngoài package (0 dòng code pipeline đổi); temp guide chứa password trên F: đã xóa sau khi đạt | ✅ **CỔNG M4 ĐẠT: 600 lệnh ghi ĐỒNG THỜI 2 máy 0 lỗi** — máy gốc thấy đủ 200/200 dòng máy editor (ghi thật qua LAN), khóa tranh chấp `shared` không hỏng (last-write editor thắng); dọn `m4_test` xong. Kế tiếp M5: pg_dump hằng ngày + dọn pre-G1-backup | pytest không đổi (**549/549** — script test đứng ngoài package, 0 dòng code pipeline đổi) | 2026-07-16 |
| G2-M3 | **Máy gốc FLIP sang PostgreSQL + dựng 1 VIDEO THẬT trọn trên PG — SỔ THẬT GIỜ LÀ POSTGRES.** ① Trước flip: `--verify-only` xác nhận PG vẫn khớp 100% (cache.db đóng băng từ M2). ② `set-db-url "host=localhost..."` vào machine.json; smoke process mới: backend postgres + 4 niche count khớp SQLite + search khớp; FULL pytest **549/549 sau flip** (chốt an toàn M1 chạy thật — test vẫn SQLite tạm dù máy flip). SQLite `F:\AutoEdit\cache.db` = mốc lui (đường lui `set-db-url --clear`). ③ pg_dump mốc trước mẻ ghi lớn → `F:\AutoEdit\backup\pg\` (17,5MB). ④ **Video thật DS1-086 "Vì sao orca không giết người"** (deepsea, music-sync, `--ref F:\DEEPSEA\VIDEO MAU\DS086`): user giao "chạy thẳng không dừng". Nạp viral 10 draft mẫu (+1.503 cảnh tag GLM vào PG, deepsea 10.618→12.166, ~58'); new+align (3.935 từ khớp 98,7%, 3,8'); direct-context; **fan-out 11 agent sonnet song song** (11 chương, 343 beat) + script gộp DS086 (coerce drift: overlay dài/lệch-anchor, graphic-diagram→card, breathing snap về nghỉ thật + khử 2-liên-tiếp — 22 lỗi ingest sửa TRỌN bằng normalizer, 0 sửa tay agent); direct-ingest **298 beat, 34 ô thở, 11 info_card, route 281 local/11 graphic/6 entity** (MỌI chương có neo thị giác — khác 3 bài fan-out đầu ra 0 card; 14 warning "nghi bán thuốc" soi tay = false-positive đúng world-lock); cut 23,2s; music 11 chương đổi bài 8 neo accent; source `--ref` **50,3' 0 lỗi db** (kho thắng 83, viral 70 cảnh/11 nguồn, sàn niche 27 beat, dl_reuse 149/~51%, perf tự ghi); assemble 143s → draft `E:\CapCut Drafts\DS1_086_ORCA_20260716_024058` (portable placeholder 0 path cứng, 676 materials); report. **CỔNG M3 SỐ ĐẠT: sổ Postgres ghi đúng qua shim suốt 298 beat** — +325 asset_usage (5.167→5.492, P7 chống lặp) + 319 search_cache (ON CONFLICT) + 167 stock_tags; 4 đường ghi (usage/cache/tags/nạp-viral) 0 lỗi. | ✅ **M3 ĐÓNG TRỌN — user DUYỆT cổng MẮT+TAI draft DS1-086 2026-07-16** ("đã ổn"). Kế tiếp M4: editor vào LAN (set-db-url hostname `DESKTOP-98SCPHI` thay IP DHCP) + test ghi song song 2 máy + gỡ luật 1-job (sửa hướng dẫn + CLAUDE.md §7 cùng lúc) | pytest **549/549** (sau flip, không đổi) | 2026-07-16 |
| G2-M2 | **Dựng server PostgreSQL + DI TRÚ dữ liệu — SỔ THẬT VẪN LÀ SQLITE (PG mới chỉ là bản sao đã verify; M3 mới flip).** User đưa password + đi ngủ giao tự chạy. **Server:** PostgreSQL 17.10-2 (EDB) PGDATA `D:\QQ SQL`, service `postgresql-x64-17` Running/Automatic + sc failure restart 60s×3; khóa LAN đúng kế hoạch: pg_hba `host all all 192.168.1.0/24 scram-sha-256` + firewall Windows rule "PostgreSQL autoedit LAN" TCP 5432 CHỈ subnet văn phòng (máy gốc IP 192.168.1.214, KHÔNG mở internet); role `autoedit`; db `autoedit` (sổ) + `autoedit_test` (CHỈ cho parity — fixture TRUNCATE) tạo `TEMPLATE template0 ENCODING UTF8` **locale ICU 'und'** → lower() chuẩn Unicode thật (psql console in 'tu tr?' chỉ là codepage hiển thị — parity 'TƯ TRỊ' chứng minh đúng). **Chướng ngại điều-khiển-từ-xa đã vượt:** UAC secure desktop vô hình với remote (Start-Process RunAs tự cancel) → đường thang máy Task Manager "Run new task + admin"; winget install trong phiên elevated lỗi -1978335212 → `winget download` thường + chạy exe unattended trực tiếp. **Di trú `scripts\migrate_g2.py`** (chạy lúc 0 job, kiểm process python/ffmpeg trước): nguồn `db.connect(db_path=F:\AutoEdit\cache.db)` LUÔN-SQLite (guard M1) → đích `db.connect(db_url=...)`; PRE-FLIGHT quét typeof từng cột + NUL byte (PG từ chối \x00) TRƯỚC khi ghi → copy 4 bảng **GIỮ NGUYÊN id** (IDENTITY BY DEFAULT; max_id 34.198 > count 34.196 = có dòng đã xóa, không được đánh lại số) + `setval` sequence → verify 3 tầng. DSN dạng KEYWORD `host=... password=...` (password chứa `@!#` phá URL userinfo — không dùng dạng postgresql://). **CỔNG M2 ĐẠT TRỌN (6,9s):** ① đếm khớp 100%/4 bảng (**34.196 asset · 5.167 usage · 4.555 search_cache · 1.205 stock_tags**) ② so mẫu ngẫu nhiên seed-89 **500 dòng/bảng × từng cột = lệch 0** (mtime DOUBLE PRECISION giữ nguyên phần lẻ — bẫy M1 được chứng minh trên data thật) ③ **20 truy vấn chọn lọc thật 2 lưng giống hệt** (count/videos_for_niche/signature/search × 4 niche deepsea·life-in·retirement-abroad·space, thứ tự khớp nhờ tie-break id DESC). Script có `--verify-only` (kiểm lại cổng) + `--wipe` (copy lại từ đầu — PG chỉ là bản sao). Vùng ảnh hưởng: 0 dòng code pipeline đổi (script mới đứng ngoài); password KHÔNG nằm trong file nào của repo (chỉ truyền CLI lúc chạy); tạm file cài chứa password đã xóa | ✅ **CỔNG M2 ĐẠT** — parity 8 ca hết skip chạy thật trên server. Kế tiếp **M3 (CHỜ USER)**: máy gốc `set-db-url` flip + dựng 1 video thật trên PG + so pick, cổng mắt đi ké; db_url máy gốc dùng localhost được, M4 editor cần địa chỉ LAN (ưu tiên hostname — IP 192.168.1.214 là DHCP) | pytest **549/549, 0 skip** (8 parity PG trước skip nay xanh trên server thật; 0 test mới — script di trú được verify bằng chính cổng số của nó) | 2026-07-15 |
| NHAC-SFX-LI | **Nạp lại kho NHẠC + SFX life-in từ bàn giao 5 editor (522 file) + LUẬT POOL NHẠC THEO NICHE** (user chốt 2026-07-17: life-in CHỈ dùng nhạc life-in, không dùng sang niche khác; SFX dùng chung được): `music/library.py::music_root_for` — có `music\<niche>\tracks\` là niche CHỈ dùng pool riêng, chưa có = pool chung như cũ; lệnh `music --niche` MỚI (stage chạy TRƯỚC source, project.niche chưa có) + assemble resolve theo project.niche sau load + `make` truyền đủ; pool chung 321 bài GIỮ NGUYÊN (deepsea/space đang dùng — không có dấu vết nhận diện bài life-in trong index); pool riêng `F:\AutoEdit\music\life-in` 116 bài (117 file DAT+Thịnh `__mood`, sửa 4 typo, grid tier A=105/B=10/C=1) + 72 bài NAM KHÔNG mood → `staging_cho_mood\` + danh sách gửi NAM đặt tên lại; SFX: kho cũ 165 wav + raw 127 → backup `ambient_life-in_truoc_nap_20260717`, GIỮ 7 impact/click (hook life-in đang BẬT mà mẻ mới chỉ có whoosh — lệch chủ đích, đã báo), nạp **299 entry / 44 kind 0 lỗi** (tổng 306 wav/47 kind) — **TÁCH KIND THEO LOÀI (user chốt, đóng điều tra RD-89)**: camel·goat·horse·dog·monkey·penguin·whale·eagle·vulture·crow·pigeon·seagull·bird + gió tách `wind` vs `snowstorm` (biến thể xoay mù — trộn là sa mạc dính bão tuyết) + market tách urban_street + plane/plane_cabin·subway·boat/motorboat/ship·stadium·racecar·volcano(cụm-phun-trào)·ice·snow_walk·splash...; subject_rules.yaml VIẾT LẠI; 21 file loại có lý do (Flipping/Typewriter chờ chốt tầng dùng, Flamingo 0 file thật, 4 breathing người, 2 trộn-2-tiếng, 1 .mov) + khử 15 trùng giữa editor; sửa kèm bug anh em OptionInfo: `make`→assemble thiếu `credit` → bật ghi công VD4 ngoài ý muốn | ✅ CODE + KHO ĐÓNG — 🔄 cổng TAI video life-in mới CHỜ USER · NAM 72 bài chờ mood · đặt hàng thêm: determined 0 / suspenseful 1 / romantic 2 nhạc; food·people_activity·interior·flamingo 0 SFX | pytest **576/576 0 skip** (+4 test_music_root_niche, parity PG thật) | 2026-07-17 |
| REF-CHUONG | **REF THEO CHƯƠNG (VD2 audit custom-prompt) — folder mẫu chia folder con `Chapter N`, ưu tiên REF scope theo chương beat đang dựng** (user yêu cầu 2026-07-18, ví dụ thật `F:\LIFE IN\VIDEO MAU\AMZ10000`: 3 video gốc + Chapter 1/2/3; **user chốt chế độ MỀM** qua câu hỏi cứng-vs-mềm — chỉ TƯỚC chèn+bonus, KHÔNG đẻ cửa loại, giữ foundation filter-overload-guard): `local.py::ref_chapter_scan` quét sổ 1 lần lúc vào source (substr không LIKE — vết PG escape; đọc PATH trong sổ KHÔNG quét đĩa) nhận segment `chapter\|chuong\|chương\|ch`+số NGAY DƯỚI prefix --ref (fullmatch — tên có hậu tố = mẫu chung; prefix mang separator cuối nên ch1 không nuốt ch10) → map treo `ViralLedger.ref_chapter_prefixes` + `ref_excludes(chapter)` (KHÔNG đổi chữ ký hàm nào — ledger vốn luồn sẵn, khởi tạo đúng 1 chỗ đã grep) → `find_ref_candidates(exclude_prefixes=…)` chặn suất CHÈN + nhãn `is_ref` scoped theo `beat.chapter` tại chokepoint `_gather_candidates`; số chương = `chapter_id` outline (cùng quy ước `chN` của BOOST); trần 15% GIỮ CẢ MẺ (`_cap_ratio` không đọc map); map rỗng = ref phẳng y cũ (tương thích ngược, test cũ 0 sửa); tầng ĐO: warning `REF theo chương (mềm): ch1=…, chung=…` + cảnh báo folder chương lệch outline. `MO_TA_VAN_HANH_REF.md §6` (rà chồng chéo trước khi code) + SKILL /dung-video (LUẬT TỰ NẠP + PHA 2) + HUONG_DAN A4.4: ⚠ xếp video vào folder chương TRƯỚC khi làm draft tách cảnh | ✅ CODE ĐÓNG — 🔄 chạy thật bài AMZ10000 CHỜ (mẻ mẫu chưa nạp sổ; nạp theo LUẬT TỰ NẠP rồi source --ref là tự ăn) | pytest **581/581 0 skip** (+3 test_sourcer: scan parse/exclude chèn/is_ref mềm-vẫn-trong-pool · +1 parity PG backslash ×2 lưng) | 2026-07-18 |
| NHIP-M0 | **GÓI CẮT THEO NHỊP NHẠC — M0: lưu ĐỘ MẠNH beat/accent vào thư viện nhạc + đo lại 433 bài.** Bối cảnh: user dựng tay project mẫu `E:\CapCut Drafts\0719` (13 cut, 152 BPM, **13/13 rơi trong ±0,09s của một beat**) yêu cầu copy cách editor thật; đã làm lưới beat `music/minihook.py` + 4 draft thử `MINIHOOK_1..4` từ 4 bài `E:\NHỊP NHANH\ĐÀN DỒN DẬP NHỊP NHANH` — **user DUYỆT "4 project đã ổn" 2026-07-19**. ★ **LUẬT ĐỨNG: hai hệ cắt KHÔNG trộn** — vùng CÓ voice thì NGHĨA quyết mép cắt (nhạc chỉ snap ≤15%), vùng KHÔNG voice thì NHỊP quyết 100%; bằng chứng ~11.000 cut/26 draft editor: video CÓ LỜI thì editor KHÔNG cắt theo lưới nhịp (lift 0,86 < 1,6) — `0719` không mâu thuẫn vì nó là video KHÔNG LỜI. **M0 làm gì:** `onset_strength` vốn được tính rồi **VỨT** ở 3 chỗ (`analyze.py:101` · `_pick_accents` · script thử) → mọi nơi cần "beat này mạnh hay yếu" phải **NẠP LẠI file nhạc**; nay lưu `beat_strength` + `accent_strength` vào index (`music/analyze.py` `_rhythm_from_signal`/`_pick_accents`, `RHYTHM_KEYS` `music/library.py:24`), `_pick_accents` trả tuple 2 mảng SONG SONG và **sort lại theo THỜI GIAN** (greedy vốn duyệt theo độ mạnh giảm dần). **🐛 BẪY suýt dính:** điều kiện nâng cấp record cũ chỉ hỏi `"beat_tier" not in obj` — mà **cả 433 bài ĐỀU đã có `beat_tier`**, chỉ thiếu độ mạnh → **toàn pool LỌT LƯỚI**, đo lại vẫn báo thành công nhưng dữ liệu không có; vá `or "beat_strength" not in obj`; bài học: hỏi **"có KEY không"** chứ không hỏi "có giá trị không" (tier C hợp lệ khi có key mà mảng rỗng — nếu không sẽ đo lại mãi). Rà P5: `_pick_accents` chỉ có **1 call site** (đã sửa); mọi consumer đọc index theo TÊN TRƯỜNG nên thêm trường mới không đổi hành vi tầng nào. **Đo thật:** `F:\AutoEdit\music` 317 bài/151s + `F:\AutoEdit\music\life-in` 116 bài/54s, backup `music_index.pre_strength_20260719.json` cả 2 folder; kiểm chứng bằng máy: **0 field cũ đổi giá trị** · accents đổi THỨ TỰ nhưng **KHÔNG đổi tập hợp** · **0 bài lệch độ dài** 2 mảng · độ mạnh trải 0,17→1,00 trung vị 0,29, **~20% beat mạnh ≥1,5× trung vị** (đủ thưa làm mốc, đủ dày để luôn có cái gần chỗ cần). **★ Số đo phủ nhận mẫu beat CỨNG:** `HOOK_PATTERN` + khoá 8 beat cho ra 152 BPM→3,2s · 172→2,8s · **89→5,4s** · 136→3,5s (chênh ~2×) — tai người cảm nhận shot theo GIÂY không theo số beat → M1 phải nhắm khoảng THỜI GIAN rồi quy ngược ra số beat | ✅ **M0 ĐÓNG** — 🔄 **M1 hình thở TIẾP THEO** (user chốt BỎ trần 3 miếng/ô: "cho phép sáng tạo theo beat nhạc"); user chốt kèm: nhạc đoạn chèn = **phương án B** (thay luôn nhạc chương từ điểm chèn về sau) · độ dài đoạn chèn **editor quyết** · footage làm cách (b) project editor đưa TRƯỚC. Bàn giao đầy đủ: **`BAN_GIAO_NHIP_NHAC.md`** | pytest **640/640, 11 skipped** (+5 test_music_rhythm: 2 mảng song song · accent sort theo thời gian · tier C rỗng cùng lúc · **hồi quy record-có-tier-thiếu-độ-mạnh** · regrid ghi được field mới) | 2026-07-19 |
| NHIP-M1 | **CẮT NHỊP Ở Ô HÌNH THỞ — mép giữa các miếng shot thở hạ cánh trên BEAT THẬT** (`MO_TA_VAN_HANH_NHIP_O_THO.md`). **Khoảng nhắm ĐO CHỐT** (việc treo §4a bàn giao): draft `0719` đoạn khoá 5 shot **3,13–3,23s** + **246 miếng thở thật editor** (deepsea+life-in `pause_dna.json::breath_measured.pieces_k2plus`, k≥2, ≥1s) p50 **2,86s** p25–p90 2,2–4,1 → `BREATH_TARGET_SHOT=3.0s`, số beat/miếng `k=max(2, round(3.0/period))` (89 BPM→4 beat 2,7s · 152→8 · 172→9 — hết bệnh co giãn 2× theo BPM), sàn miếng = `min_piece` DNA 1,5 (hằng-chết cũ nay dùng thật ở đường beat). **Kiến trúc HAI TẦNG:** ① SOURCE (`breath.py::_beat_map` + nhánh lưới trong `pick_breath_shots`) tính lưới trên boundary DỰ ĐOÁN (=timeline_start chương) → chốt SỐ MIẾNG + pick clip (bẫy ① NAM CHÂM: chỉ source biết kho còn clip), record `BreathShot.beat_cut=True`, note `[lưới beat]`; ② ASSEMBLE (`coverage.py::retime_breath_grid`, gọi SAU M-CHANGE+snap) tính LẠI mép trên boundary THẬT — M-CHANGE dời điểm đổi nhạc ≤2s thì lưới source lệch theo (lệch 1 beat là tai nghe ra, bug b08/b09) — số miếng GIỮ NGUYÊN, lưới thiếu mốc (hiếm) → ô giữ mép cũ đếm `kept`; dur retimed ghi ngược vào `project.breath_shots` (NT1; `first_piece_end` SFX chủ thể đọc đúng số mới). Hạ cánh beat MẠNH ±2 **tái dùng `beat_grid` nguyên vẹn** (pattern đều k — ô thở là vùng tĩnh, mẫu 0719 đoạn khoá cũng đều); chiếu nhạc→timeline: `plan.py::timeline_beats` cùng bất biến P như `timeline_accents` (record thiếu strength → 0, vẫn cắt được). **BỎ TRẦN 3 MIẾNG (user chốt): ở đường beat** — lưới quyết số miếng (ô 10s @109 BPM ra 4); đường DNA (không music-sync) GIỮ trần 1-3 vì `k_fractions` chỉ có mẫu editor k=2,3 — muốn bỏ nốt phải hỏi lại (tồn đọng). Điều kiện bật per-ô TỰ ĐỘNG: có `music_plan` + tier ≠ C + ≥2 beat trong ô; thiếu gì → đường DNA cũ nguyên vẹn (fail-open cả lỗi đọc index). **Rà chồng chéo P5** (bảng đủ trong MO_TA §5): luật loại snap mép-giữa-miếng GIỮ NGUYÊN nhưng ý nghĩa ĐẢO (đã nằm trên beat, snap accent−80ms sẽ kéo lệch — bẫy ③ khai rõ, có comment tại chỗ); mép VÀO/RA ô vẫn snap như cũ, retime chạy sau nên tôn trọng; M-CHANGE không bao giờ neo vào mép sẽ-bị-retime (mép chương ≤0,3s luôn thắng mép giữa-miếng ≥1,2s); hook SFX/pacing DNA warning-only theo dõi ở cổng tai | ✅ **CODE ĐÓNG** — 🔄 **CHỜ CỔNG TAI/MẮT USER** trên video thật music-sync (M6 lộ trình); sau đó mới sang M2 đoạn chèn | pytest **650/650, 11 skipped** (+10: 4 breath grid nhắm-theo-giây/hạ-cánh-mạnh/**hồi quy bỏ-trần-4-miếng**/fail-open · 1 timeline_beats · 3 retime · 2 source lưới-beat/DNA-fallback) | 2026-07-19 |
| RD89-10MIN | **Video kiểm M1: RD89 Oman bản 10 phút** (`projects/rd89-oman-10min-20260720`, user yêu cầu 2026-07-20): copy RD-89, cắt hết chương 5 (beat 0-80, timeline 587s ≈ 9,8'), TÁI DÙNG beats đã duyệt (không direct lại) → cut → music (pool life-in, 5 chương 4 tier A neo downbeat, ch1/2/4 trùng bài V13) → source 81/81 (0 needs_human · REF `F:\LIFE IN\VIDEO MAU\REAL 89` dính từ inputs · local thắng 34 · viral 46 cảnh/10 nguồn gate chặn 19) → assemble → draft **`E:\CapCut Drafts\RD89_OMAN_10MIN_20260720`** + report. **📌 LỆCH CÓ CHỦ ĐÍCH (user chốt qua AskUser):** DNA life-in mới (nạp 07-16) anchors ô thở [2,2..3,5s] → quantile map kẹp p90 làm **đuôi ô sâu KHÔNG với tới được** (editor life-in thật có ô max 10,6s, 20% ô k≥2) → bản 10' chỉ có 2 ô 1-miếng = M1 câm; V13 tai user duyệt vốn dựng bằng DNA POOLED space TRƯỚC khi life-in có pause_dna → **user chốt "ô sâu như V13"**: cut với `niche=""` tạm (DNA pooled cả 2 tầng, y trạng thái V13) rồi trả `niche=life-in` → 3 ô sâu beat 8 (7,7s) / 10 (4,2s) / 65 (5,3s). **🐛 BUG THẬT M1 BẮT ĐƯỢC (fix commit c04def1):** beat 65 footage 5,3s/12 beat ra 1 miếng — mốc dự kiến idx 6 HỢP LỆ nhưng hạ-cánh-beat-MẠNH ±2 nhảy trúng beat 3,92s > trần đuôi 3,8 → `beat_grid` break nuốt mất nhát cắt; fix: `breath_cuts` LOẠI beat vượt trần đuôi TRƯỚC khi vào lưới (chỉ đường ô thở, mini-hook đã duyệt không đụng) + 1 regression; re-pick riêng breath shots (không re-source), dọn 5 file mồ côi. **Kết quả đo trong DRAFT CUỐI:** beat 65 mép giữa 2 miếng **lệch 0,2ms so beat nhạc thật** (retime dời mép từ dự đoán source 2,06→3,62s = bằng chứng tầng-2 BẮT BUỘC, M-CHANGE dời nhạc ~1,5s); beat 10 = 1 miếng 4,2s (cắt sẽ đẻ miếng 0,97 < sàn — đúng ngữ nghĩa); beat 8 fallback DNA vì **vùng nhạc LOOP** (bài ch1 hết 160,8s, ô cần 163-171s — tồn đọng "loop không mô hình hoá" đã ghi bàn giao §10, nay có ca thật đầu tiên). Warning: `NHIP-M1: retime 1/2 ô` · M-ACCENT 12/85 · M-CHANGE 4/4 | ✅ **CỔNG TAI USER DUYỆT 2026-07-20 ("tôi nghe đạt, duyệt bước này") — M1 ĐÓNG TRỌN, kế tiếp M2 đoạn chèn** (BAN_GIAO §7 đã rà sẵn). TỒN ĐỌNG mới: ① thiết kế "đuôi sâu" DNA (niche anchors nông mất hẳn ô sâu — cần user chốt luật) ② loop nhạc chưa mô hình hoá (ca thật beat 8) | pytest **651/651, 11 skipped** (+1 hồi quy trần đuôi) | 2026-07-20 |
| NHIP-M2 | **ĐOẠN CHÈN Δ — chèn vào timeline, mọi tầng dịch đúng** (`MO_TA_VAN_HANH_DOAN_CHEN.md`). Editor khai bằng lệnh mới **`autoedit insert <project> --after-beat N --dur S`** (hoặc `--after-chapter N` = sau beat cuối chương; `--remove`; không tham số = liệt kê; khai lại cùng beat = SỬA) → ghi `project.inserts` → chạy lại cut→music→source→assemble. **Kiến trúc = khuyến nghị §7b bàn giao:** Δ tiêu thụ ở ĐÚNG MỘT CHỖ sinh timeline (`cutter/timeline.py` — beat có Δ kết thúc run, cursor cộng Δ SAU thở+giãn) → `beat.timeline_*`/`seg.timeline_*` phía sau tự dịch → 10/14 chỗ assembler + toàn bộ tầng đọc thẳng `beat.timeline_start` (chart PiP/info-card/overlay/kinetic — bẫy im lặng §7d.1) **không sửa dòng nào**. Coverage sinh **cửa sổ insert RIÊNG** (`CoverWindow.insert=True`, KHÔNG phải ô thở) — M2 lấp bằng **slug giữ chỗ** (chống NAM CHÂM, editor thấy Δ ngay; footage thật = M4/M5, nhạc editor = M3). **4 chỗ tay §7c:** ① hình trong Δ = slug (lưới beat để M4) ② nhạc ôi thiu: `run_cut` vốn gọi `mark_music_stale` — Δ chỉ có tác dụng qua cut nên không đường nào lọt ③ pacing: trừ tổng Δ khỏi mẫu số `_warn_pacing_dna` ④ ambient: `breath_slots` CẮT ô tại mép vào Δ (1 clip không loop phủ Δ dài = im lặng nửa ô; trong Δ nhạc chủ đạo). **Luật mới khai rõ (P5, bảng đủ MO_TA §5):** mép VÀO/RA Δ **MIỄN snap accent** + ô thở kề trước Δ **KHÔNG J-cut** (Δ phải giữ ĐÚNG độ dài editor khai — snap/J-cut sẽ co giãn Δ); cấm Δ sau beat CUỐI (5 chỗ `total_end` đều dựa segment cuối — rà đủ, không sửa chỗ nào); cổng `windows[0].start==0` (§7a) giữ nguyên vì Δ luôn SAU một beat; M-CHANGE tự neo điểm đổi nhạc vào mép RA Δ (nền sẵn cho M3 phương án B); ducking: gap quanh Δ không voice → nhạc **NỞ 0.5 suốt Δ** (cộng hưởng); nhạc chương i phủ tới `bounds[i+1]` nên Δ **tự được phủ kín** (§7e — không làm gì). Beat không kết câu → cảnh báo (Δ ngắt giữa ý) nhưng không chặn. **VIDEO KIỂM (2026-07-20):** tái dùng `projects/rd89-oman-10min-20260720` — khai `insert --after-chapter 2 --dur 20` (beat 27) → cut (timeline 587→**607,3s**, đúng +20; cut chạy với `niche=""` tạm để giữ DNA pooled ô sâu như V13 rồi trả `niche=life-in`) → music (5 chương tier A, plan cũ tự xóa đúng thiết kế nên **nhạc ch1/3/5 đổi bài** — bản dựng lại hoàn toàn, không phải V1 đã duyệt tai) → source 81 beat 0 needs_human → assemble draft **`RD89_OMAN_10MIN_20260720_V2`**. **Số đo trong draft_content.json:** Δ nằm **188,42→208,42s đúng 20,00s** · video_l1 **phủ kín 0 hở/đè** · voice segment đầu sau Δ = **208,418458s khớp TỪNG CHỮ SỐ** với project.json · 6 info-card layer2 sau Δ rơi đúng `beat.timeline_start` mới · nhạc ch2 phủ hết Δ rồi crossfade ch3 tại 205,4s với **keyframe ducking nở 0.5 suốt Δ** rồi nép 0.2 khi voice vào · ambient cuối trước Δ dừng tại **188,42 = đúng mép vào Δ** (không tràn) | ✅ **CỔNG MẮT USER DUYỆT 2026-07-20 ("duyệt xong M2") — M2 ĐÓNG TRỌN**, kế tiếp **M3** (nhạc editor đưa cho đoạn chèn, phương án B: thay luôn nhạc chương từ điểm chèn về sau) | pytest **661/661, 11 skipped** (+10 test_insert: chèn-dịch-source-bất-biến · Δ xếp sau thở · beat-cuối-ép-0 · cửa sổ insert liền khít · **hồi quy J-cut/snap không đụng Δ** · ambient cắt trước Δ · schema cũ load) | 2026-07-20 |
| NHIP-M3 | **NHẠC EDITOR ĐƯA CHO ĐOẠN CHÈN Δ — phương án B** (`MO_TA_VAN_HANH_NHAC_DOAN_CHEN.md`). Editor thêm cờ **`--music <file>`** vào lệnh `insert` → bài đó **THAY** nhạc chương từ mép VÀO Δ tới **HẾT CHƯƠNG** (tầm phủ user chốt 2026-07-20 qua AskUser; phương án A "chỉ trong Δ rồi trả về" đã BÁC từ 07-19 vì 2 lần chuyển nhạc trong vài chục giây nghe rối). File nằm ngoài kho cũng được, chuẩn hóa WAV như nhạc kho (C4); **kiểm file tồn tại NGAY lúc khai** (path sai mà im tới assemble = loại lỗi "hỏng-mà-vẫn-chạy"). **★ PHÁ BẤT BIẾN CÓ CHỦ ĐÍCH "1 chương = 1 bài":** user nghi ngờ bất biến này nên **ĐO LẠI 14/14 project** trong `projects/` — số bài = số chương, không sót cái nào (khóa ở `select.py:131` "1 bài/chương" + `MusicPlanEntry.chapter_id` + `pick_by_ch`). Làm rõ chỗ dễ nhầm: hệ thống **CHỌN** nhạc theo CẢM XÚC từng đoạn rất tinh vi (`_score` mood/music_hint; `_entry_span`/`_start_offset` vào thẳng `drop` cho chương cao trào, `intro` cho chương lắng) nhưng **RANH GIỚI ĐỔI BÀI** vẫn trùng ranh giới chương — hai thứ khác nhau. M3 phá bất biến ĐÚNG MỘT CHỖ: `music_spans()` chẻ chương mang Δ-có-nhạc thành 2 nhịp nhạc; chương không có Δ-nhạc → **1 span, tọa độ Y HỆT đường cũ**. **2 BẪY TỌA ĐỘ tự nêu trước khi code rồi tự kiểm:** ① track `music`/`music2` luân phiên theo **CHỈ SỐ SPAN** không phải chỉ số chương — span lẻ chèn giữa mà đếm theo chương thì 2 đoạn liền nhau rơi CÙNG track → crossfade 3s đè → `SegmentOverlap` mà `_safe_add_segment` **nuốt im lặng** (§7d.3); kiểm RD89 thật: 6 span ra music/music2 xen kẽ, **0 đoạn đè** ② **bất biến P KHÔNG áp cho span Δ** — `P = start_offset + min(XFADE, timeline_start)` giả định segment bắt đầu ở ĐẦU chương, mà span Δ bắt đầu GIỮA chương và `start_offset` là của bài CŨ → áp vào sẽ nhảy vào điểm vô nghĩa giữa bài lạ; span Δ vào từ đầu bài. **Rà chồng chéo P5** (bảng đủ MO_TA §6): M-CHANGE tự neo mép RA Δ (nền M2, thuận chiều) · `usage` KHÔNG đếm bài editor (không thuộc kho, đếm vào bẩn sổ) · `music_selections` key `"<ch>Δ"` để bài editor không đè mất tên bài gốc trong report · Δ không `--music` → M2 nguyên vẹn (có test). **Kiểm chạy thật** `rd89-oman-10min-20260720`: `insert_edges` ra **188,4185→208,4185** khớp TỪNG CHỮ SỐ số đo cổng mắt M2; chưa `--music` → 5 span = 5 chương (hồi quy bằng 0); có `--music` → span Δ phủ **188,42→208,42 = đúng 20,00s** rồi ch3 quay lại nhạc kế hoạch | 🔄 **CODE ĐÓNG — CHỜ CỔNG TAI USER** (Claude không tự báo đạt). TỒN ĐỌNG ghi sẵn: ① `timeline_accents`/`timeline_beats` chưa biết span Δ (chưa hại vì mép Δ miễn snap + Δ chưa có footage; **sẽ thành thật ở M4/M5**) ② bài editor chưa đo `beat_times`/`beat_strength` vì ngoài kho — M4 cắt hình theo nhịp trong Δ sẽ cần ③ bài editor trùng bài chương khác → nghe lặp, chưa cảnh báo | pytest **670/670, 11 skipped** (+9 test_music_insert: mép Δ theo segment-không-phải-beat · chẻ span tới hết chương · **hồi quy không-Δ-nhạc không chẻ** · liền mạch 0 hở/đè · 2 Δ cùng chương · span vụn <0,2s bỏ · schema M2 load được) | 2026-07-20 |
| NHIP-M4 | **CẮT Δ THEO NHỊP BÀI EDITOR — 🔄 ĐANG DỞ, NHỊP CHƯA ĐẠT CỔNG TAI** (`BAN_GIAO_M4_NHIP_DANG_DO.md`). User nghe V3: *"nhịp dựng nhanh nhưng 2 footage đầu để thời lượng quá dài (4:12-4:32)"* — Δ 30s chỉ có 1 slug đứng im trong khi nhạc 89 BPM dồn dập. **3 phần đã làm:** ① `InsertSpec.music_beats/_beat_strength/_bpm/_tier` đo librosa NGAY LÚC KHAI (bài editor ngoài kho, không có record music_index — tồn đọng M3 #2) ② `coverage.insert_grid_cuts()` + `split_insert_windows()` chẻ Δ theo lưới beat, tái dùng `beat_grid` đã duyệt; miếng giữ cờ `insert=True` nên mọi luật né-Δ của M2 (J-cut/snap/ambient/pacing) tự né từng miếng ③ assembler nối dây + warning báo số hình/độ dài. **🐛 BUG NAM CHÂM BIẾN THỂ MỚI (user bắt qua ảnh CapCut, 4 draft liên tiếp V5-V8):** 11 ô giữ chỗ của Δ đáng lẽ ở 4:12 hiện ra ở **9:47 chồng lên voice seg_055-058**. Root cause: slug add SAU toàn bộ footage → trong `draft_content.json` nằm CUỐI danh sách segment dù `target_timerange.start` ghi đúng 252s; **CapCut duyệt track TUẦN TỰ** → gặp segment "đi lùi" thì dồn cả cụm xuống cuối. Track phủ kín 0 hở, invariant pass, mốc đúng — **không cần lỗ hở vẫn dính nam châm**. Trước M4 không lộ vì 1 Δ = 1 slug ở cuối video (thứ tự add trùng thứ tự thời gian). Fix `c1d88f4`: sort `video_l1` theo start sau khi lấp slug + regression. **★★ BÀI HỌC ĐẮT NHẤT: phép kiểm bằng script MÙ với lớp bug này** — đọc JSON rồi `sort` theo start thì LUÔN thấy đúng, nên tôi báo "đã đúng" **3 lần** và user phải tự mở CapCut bác **3 lần**; còn đổ cho "đọc file đang ghi"/"CapCut ghi đè"/"user mở nhầm draft" (đều sai). LUẬT: kiểm draft phải xét **THỨ TỰ segment** không chỉ giá trị mốc; file đúng mà CapCut sai thì **TIN CAPCUT** (luật này VỐN CÓ ở memory `capcut-main-track-nam-cham-va-san-niche`, tôi đọc mà không áp dụng). **Nhịp — 2 vòng đều CHƯA ĐẠT:** vòng 1 ép `k=round(target/period)`=4 + hạ-cánh-beat-mạnh ±2→±1→0 (user: *"nhiều footage không rơi đúng nhịp"*); đo ra mọi mép TRÙNG beat 0,0ms nhưng **3/10 mép rơi beat YẾU** (0,18-0,22 vs trung vị 0,29) vì bài "End of an Era" nhịp mạnh **CHU KỲ 3** còn lưới k=4 → lệch pha (đúng lớp lỗi b08/b09). Vòng 2 `9fa01dc`: `_meter_k` đo chu kỳ nhịp mạnh thật (thử m 2..8 × mọi pha, lấy strength tb cao nhất; lấy m NGẮN NHẤT trong nhóm ~ngang điểm vì m=6 chỉ là bội của m=3) rồi k = bội số gần target → **được cả hai: mép rơi beat mạnh VÀ lưới đều**, không phải đánh đổi; 📌 LỆCH M1: `INSERT_TARGET_SHOT` 3,0→**2,0s** (user chốt — ô thở dùng 3,0s p50 editor thật, còn Δ là montage chủ đích trên nhạc dồn dập, nhanh hơn là Ý ĐỒ). V10 đo được: 15 hình đều 2,00s · kc beat 3,3,3... · lệch 0,0ms · strength tb mép 0,364→**0,465** (+28%) · beat yếu 3/10→2/14 · thứ tự segment tăng dần ✅ | 🔄 **Δ VÀO ĐÚNG VỊ TRÍ 4:12 — USER DUYỆT MẮT**; ❌ **NHỊP CHƯA ĐẠT TAI** (user V10: *"chuyển footage vẫn chưa đúng nhịp beat chuyển. có lẽ tôi và bạn đã nhầm ở đâu đó"*) → dừng để clear chat. **4 GIẢ THUYẾT cho phiên sau** (bàn giao §4): ⭐ lưới beat librosa KHÔNG đều — kc beat dao động **0,650-0,696s (46ms)**, mẫu `0,674/0,674/0,650` lặp = làm tròn theo hop_length → cắt mỗi 3 beat **sai số CỘNG DỒN** · mép vào Δ lệch −302ms (cố định theo chỗ voice dứt) · **chưa áp `SNAP_LEAD` 80ms** (editor thật cắt TRƯỚC beat 120-175ms — thử rẻ nhất) · tai user bám **Ô NHỊP** không phải beat lẻ. **Việc đầu tiên: xuất CLICK-TRACK cho user nghe đối chiếu** — click lệch tai user = lỗi tầng ĐO NHỊP, không phải tầng cắt | pytest **681/681, 11 skipped** (+12: lưới nhắm-giây/hạ-cánh-beat-thật/fail-open/chẻ-cửa-sổ/liền-khít · **hồi quy thứ-tự-segment** · **hồi quy khóa-chu-kỳ-nhịp** · nhịp-3 rơi beat mạnh) | 2026-07-20 |
| NHIP-M4b | **LƯỚI Δ = CÔNG THỨC TỪ DOWNBEAT MADMOM (foundation e2) — CHỜ CỔNG TAI V11.** User dừng phiên trước bằng câu *"tôi và bạn đã nhầm ở đâu đó"* → phiên này KHỚP FOUNDATION TRƯỚC KHI CODE (đúng bàn giao §5): user học + chốt nguyên văn **luật chuyển footage theo phách** — nhịp 4/4 chuyển ở phách **1 và 3**, nhịp 3/4 chuyển ở phách **1**, luôn phách LẺ; mốc tính bằng **CÔNG THỨC** `Offset + n×Bar` chứ KHÔNG cộng dồn beat đo (`foundation/e2-chuyen-footage-theo-phach.md` — file foundation ĐẦU TIÊN sinh từ M4). Xác nhận GT1 bàn giao: lưới beat librosa dao động 46ms, cắt mỗi 3 beat = sai số CỘNG DỒN → mép trôi khỏi nhịp tai. Phát hiện kèm: hàm downbeat librosa cũ nhóm CỨNG 4 beat (`beats[phase::4]`) trong khi `_meter_k` đo bài này nhịp 3 — HAI TẦNG CÙNG HỆ CÃI NHAU, downbeat cũ sai toàn bộ trên bài nhịp 3. **Giải pháp user chốt: madmom lo PHA, công thức lo LƯỚI** (user đòi "ít rủi ro nhất, tự động hoàn toàn" → madmom DBNDownBeat RNN là chuẩn giới MIR, kháng phách nghịch/trống nhẹ — thay vì tự chế dò-pha-mạnh dễ trật). Đo thật "End of an Era": **meter 3 · 68 downbeat · bar 2,000s** = trùng khít target 2,0s user chốt (1 hình = 1 ô nhịp). Hạ tầng: cài MSVC Build Tools (winget) + madmom **pin git rev 27f032e (0.17.dev0** — PyPI 0.16.1 chết numpy 2 `np.float`); khai CHÍNH THỨC pyproject (user chốt máy editor cũng cài MSVC — HUONG_DAN C1b/C3 mới; `uv sync` trần build OK, setuptools tự tìm MSVC) + `[tool.uv.extra-build-dependencies]` + hatchling `allow-direct-references`. Code: `analyze_downbeats()` (madmom, gọi 1 lần lúc khai Δ) → `InsertSpec.music_downbeats/_meter` → `insert_grid_cuts()` nhánh công thức: bước = bội của (bar | nửa-bar) gần target, pha neo downbeat đầu trong Δ, sàn 1,5s nhân bội (bội nào cũng rơi phách lẻ — không phá luật); fallback librosa nguyên vẹn (project cũ/madmom lỗi). BẪY đã né: `analyze_rhythm` librosa cũng có key `downbeats` (nhóm-4 SAI) — kết quả madmom giữ DICT RIÊNG không trộn. Vì sao công-thức không dính b08/b09 (từng cấm `b0+n*period`): bug đó pha+period từ beat librosa; nay pha=RNN, period=trung vị bar madmom. V11 đo: thứ tự segment tăng dần ✅ · **lệch mốc vs công thức 0,0ms cả 15 mốc** (hết trôi) · mốc cách downbeat madmom 0-10ms (jitter đo của madmom — công thức mượt hơn downbeat thô). Rà P5: 1 caller duy nhất (assembler) đã nối; `_meter_k`/`beat_grid` mini-hook/M1 CHƯA port e2 (chỉ port khi nghe lệch — P2); mép Δ miễn snap giữ nguyên. **✅ V11 CỔNG TAI DUYỆT** (user: *"đã chuyển đúng theo foundation"*). **→ A′ SHUFFLE RUN+HOLD cùng ngày (e2 §5, user gật sau tư vấn):** user chê V11 *"các footage đang khá đều nhau"* — muốn shuffle như editor thật (dài ngắn xen kẽ, vẫn phách 1&3). Nghiên cứu craft (LBB/SoundOnSound/Murch — user dặn HỌC TỪ EDITOR GIỎI, mẫu 0719 là user tự làm không lấy làm chuẩn): editor giỏi KHÔNG random trần mà **"biến thiên có chủ đích": pattern → phá → trả thưởng** ("3 nhát nhanh, giữ 1 hình đã mắt, quay lại nhanh"; cả đoạn có HÌNH DẠNG: nhanh vào — giữ giữa — siết cuối). Mã hóa `_shaped_pattern`: shot = BỘI của unit lưới (phách lẻ BẤT BIẾN, lưới công thức 0ms giữ nguyên — shuffle chỉ quyết mỗi shot mấy unit); RUN 2-4 hình 1-unit + HOLD 2-unit thưa (3-unit ≤1 lần/Δ) + giữa 2 HOLD ≥2 RUN + mở/KẾT bằng RUN + HOLD ưu tiên đầu nhóm 4 ô nhịp (đệm ≤2 RUN); seed cố định crc32(beat, tên bài) = dựng lại Y HỆT, cờ `insert --shuffle-seed/--pace fast|medium|slow`; ô HOLD dùng ảnh slug RIÊNG "HOLD — CẢNH RỘNG/NHIỀU CHI TIẾT" (truyền luật content cho editor — máy không biết hình sẽ đắp); 2 bug tự bắt khi rà: vòng pattern nuốt mốc cuối (mất shot đuôi 1,71s — vá thêm biên sau shot chót) + script kiểm nhầm "place**hold**er" chứa "hold" (draft vốn đúng). V12 đo: 13 hình `2,3│2·2·2│4H│2·2·2│4H│2·2·2│1,7`, mọi mốc khóa lưới, thứ tự segment tăng dần, 2 ô HOLD đúng ảnh riêng | ✅ V11 tai DUYỆT · ✅ **V12 (shuffle) CỔNG TAI DUYỆT 2026-07-21 — M4 PHẦN NHỊP ĐÓNG TRỌN** (còn ngỏ: footage THẬT trong Δ — cần user chỉ nguồn; tồn đọng M3 #1 timeline_accents chưa biết span Δ — PHẢI sửa khi làm footage thật) | pytest **689/689, 11 skipped** (+5 M4b, +3 A′: has-holds-run-open-close · deterministic-seed · shaped-pattern-grammar; regression GT1 đổi thành lưới-khóa-bội-step) | 2026-07-21 |
| NHIP-M4c | **FOOTAGE THẬT TRONG Δ (thay slug) + SỬA TỒN ĐỌNG M3 #1** (`MO_TA_VAN_HANH_FOOTAGE_DOAN_CHEN.md`). User chốt nguồn LAI qua AskUser: clip **folder editor đưa** (`insert --footage <folder>`) dùng TRƯỚC — thiếu thì **KHO đắp bù theo PROMPT editor** (`--prompt "thiên nhiên hùng vĩ liên quan Oman và hình ảnh phụ nữ"`, KHÔNG tự suy từ chương); cỡ cảnh GLM tag. **Lúc khai** (fail fast y nhạc M3): folder copy `media/insert/` prefix crc8 (chống đè trùng tên — họ bug F6) + GLM tag từng file; prompt được NÃO dịch 2-6 query tiếng Anh khớp vocab kho C4 in ra ngay, NÃO lỗi → kho đắp TẮT (ô thiếu giữ slug). **Kiến trúc 3 tầng:** ① `cov.insert_grids` — DỜI logic mốc+seed từ assembler về 1 chỗ, source+assemble cùng gọi (số ô/mốc tự khớp, hết bản sao logic); ② SOURCE `sourcer/insert_fill.py::pick_insert_footage` chạy SAU pick beat/thở (used_in_video đầy đủ — không giành clip của beat): cờ HOLD qua `insert_hold_flags` (luật A′ ≥1,5× trung vị, CÙNG HÀM với ảnh slug hold — 1 luật 2 nơi), gán editor trước (HOLD←wide/aerial, RUN←close/medium, 4 nấc ưu tiên + quét vét lệch cỡ), kho đắp ô trống (video đủ dài, không lặp trong Δ, P7 log usage; clip editor KHÔNG log — y luật nhạc M3), còn thiếu → slug; ghi `footage_picks` theo **INDEX Ô** (không mốc tuyệt đối — cut chạy lại timeline dịch nhưng index ổn định); ③ ASSEMBLE đọc pick theo index → `_place_video_l1` như footage thường, hỏng/hụt → slug, số ô ≠ số pick → warning "chạy lại source". Δ vẫn NGOÀI pacing/cuts_log/credit (luật M2). **Tồn đọng M3 #1 SỬA XONG:** `timeline_accents`/`timeline_beats` đi theo `music_spans()` — span Δ dùng downbeat madmom/beat+strength bài editor đo lúc khai (P=0 tại mép span), accent bài KẾ HOẠCH không còn phát mốc trong vùng đã bị thay nhạc; project không Δ-nhạc → tọa độ Y HỆT (test hồi quy 0). **V13 RD89 đo trong draft:** Δ 4:12, 30s, 13 ô (2 HOLD): kho đắp **13/13, 0 slug**, 2 HOLD nhận aerial+wide đúng e2 §5, thứ tự segment tăng dần ✅, mốc vs lưới công thức **0,0ms cả 13 ô**, mép RA khớp; nhạc/lưới y V12 (không re-run cut/music/source toàn phần — pick Δ PHẪU THUẬT theo tiền lệ re-pick breath). ⚠ CÒN NGỎ: đường Δ fill **không qua geo-gate/world-lock** (query "women traditional" kéo 1 clip Vietnam vào ô 0 — cổng mắt sẽ phán; chê thì nối geo-gate vào `_library_pool`) | 🔄 **CODE ĐÓNG — V13 CHỜ CỔNG MẮT+TAI USER** (Claude không tự báo đạt); đường --footage folder editor CHƯA có mẻ thật (pytest phủ) | pytest **703/703, 11 skipped** (+14 test_insert_footage: hold-flags · grids=seed-assembler · query-validation/fake-client · ingest copy+tag/fail-open · pick HOLD-được-wide · kho-đắp+usage · fail-open-chưa-cut · tier-C-1-ô · schema-M4b-load · accents/beats span-Δ ×3 + hồi quy không-Δ) | 2026-07-21 |
| NHIP-M4d | **CỔNG LOCATION cho Δ + folder `HINH THO` trong mẻ video mẫu** (user chốt 2026-07-21 sau khi bác V13 vì Δ dính clip Vietnam/Bosnia/Djibouti; MO_TA_VAN_HANH_FOOTAGE_DOAN_CHEN.md cập nhật). ① **Cổng location** (`insert_fill.foreign_location`): geo-gate PA2 chỉ gác cây "Khu Vực..." — mẻ nạp `nap\EXxxx` phi-địa-lý LỌT HẾT, nhưng tên nước nằm ngay trong TÊN VIDEO NGUỒN → luật mới cho pool Δ: siêu dữ liệu nhắc tên QUỐC GIA script không nhắc → loại (match TOKEN có đệm — "oman"⊄"romance", "viet nam"⊄"soviet name"; ~200 nước + biến thể); clip không nhãn → QUA (chỉ chặn ca chắc chắn, triết lý c5); kèm passes_geo cũ; CHỈ áp pool Δ, phễu beat giữ nguyên. ② **HINH THO** — hệ thống folder user chốt: `VIDEO MAU\<mẻ>\HINH THO\{chapter N | Mini Hook | gốc=chung}` = footage DÀNH RIÊNG Δ/mini-hook; `local.ref_hinhtho_scan` đọc PATH sổ (substr PG-safe, cùng bẫy xếp-folder-trước-khi-làm-draft); `ledger.ref_hinhtho_prefixes` → `ref_excludes` tước CHÈN+bonus mọi beat thường (MỀM y REF chương — search vẫn chấm, trần 15% cả mẻ); `ref_chapter_scan` đếm HINH THO key riêng (không phồng "chung"); **ưu tiên Δ 4 tầng**: ①--footage ②HINH THO đúng-chương+chung (xếp scene CHẴN trước LẺ — 2 pick liên tiếp không kề trong nguồn, giảm nhẹ rủi ro "kề" bản quyền vì Δ chưa qua ledger) ③prompt-kho qua cổng location + LOẠI vùng đặt chỗ chương-khác/Mini-Hook (bug V14 lần đầu: Δ ch3 vớt lại 13 cảnh HINH THO ch1 qua query "oman" — đặt chỗ thành hư danh, vá + hồi quy) ④slug. Mini Hook: nhận diện + để dành (user chốt — tính năng chèn mini-hook đầu video làm sau). **Vận hành kèm:** video Oman 2GB Downloads → `RD89\HINH THO\chapter 1` + sửa path draft tách cảnh 133 chỗ (string replace, không đụng id C1); nạp mẻ 132 cảnh (66 wide/11 aerial/53 medium/2 close_up; 8 lỗi GLM 400 → chạy lại vét sạch); khai Δ mới 20s sau chương 1 (beat 8). **V15 đo trong draft:** Δ ch1 **HINH THO 9/9 ô** (1 HOLD) · Δ ch3 kho 13/13 **cổng chặn 55 ứng viên vietnam...** · 0 tên nước lạ · 0 rò vùng đặt chỗ · mọi mốc 0,0ms · thứ tự segment tăng dần; nhạc chương đổi bài so V12 (timeline +20s → plan dựng lại, đúng thiết kế) | 🔄 **CODE ĐÓNG — V15 CHỜ CỔNG MẮT+TAI USER**. Giới hạn khai rõ: cổng chỉ bắt TÊN NƯỚC (Everest/Hạ Long không bắt); clip bikini match "women" → mắt phán, chê thì nâng danh sách địa danh/vision gate. CÒN NGỎ: mini-hook đầu video · Δ chưa qua ledger trần/kề (mới giảm nhẹ chẵn/lẻ) · 2 Δ cùng bài nhạc → nghe lặp chưa cảnh báo (M3 #3) | pytest **710/710, 11 skipped** (+7: foreign_location token/khớp-oan · pool-gate chặn djibouti · scan cây HINH THO + đếm riêng · ref_excludes phủ HINH THO · ưu tiên HINH THO trước kho · **hồi quy vùng-đặt-chỗ-không-rò** · scene chẵn/lẻ) | 2026-07-21 |
| TINTUC-E2E | **Video kiểm end-to-end ĐẦU TIÊN trên máy này — kênh mới `tin-tuc` (núi lửa Indonesia, folder TEST-TOOL) qua /dung-video đường sâu.** Sửa lỗi môi trường trước khi dựng: `claude` KHÔNG có trong PATH (Claude Code bản native installer nằm `%USERPROFILE%\.local\bin\claude.exe` nhưng PATH registry user thiếu folder đó → `cc_client` FileNotFoundError "Không tìm thấy 'claude'") → thêm vào PATH user, 0 dòng code đổi, verify `claude -p` non-interactive chạy subscription OK. Pipeline: new/align (494 từ, 9 nội suy) → direct-context (kho `tin-tuc` RỖNG — khối từ vựng bỏ, fail-open đúng thiết kế) → tự đạo diễn **7 chương/45 beat** (1 chart bar Indonesia 130 vs Japan 110 · 5 info-card · 2 kinetic · 7 overlay · 6 ô thở ~1/43s; quirk alignment: sau [430]"source." voice KHÔNG nghỉ — Whisper dán "The" vào liền → ô thở sâu 3.5s dồn về [457]"path." nghỉ thật 3,02s) → ingest PASS vòng 2 (vòng 1: 2 beat >10s chia đôi tại ranh mệnh đề; 16 warning "bán thuốc" soi tay = false-positive, concept đều trong thế giới núi lửa/Indonesia) → cut 28 segment (+5,6s giãn nghỉ DNA · 4 ô thở kéo sâu 4,6-8,7s → timeline 274,5s) → source **45/45 = 100% Pexels** (kho rỗng, 0 needs_human) → assemble draft `SCRIPT1_20260805_072653` (2 slow-mo b19 0.83x/b35 0.76x; **KHÔNG nhạc — kho music `~\AutoEdit\music` máy này rỗng**) → report | ✅ **cổng mắt user ĐẠT 2026-08-05** ("đạt" — CapCut mở OK, không relink). Việc treo máy này: kho footage + nhạc tin-tuc chưa nạp | — (run thật, 0 dòng code pipeline đổi) | 2026-08-05 |
| SFX-EPI-3T | **SFX EPIDEMIC + SFX CHỦ THỂ 3 TẦNG + nâng mức -8/-5dB — CỔNG TAI V11 DUYỆT.** ① `epidemic-sfx` tải SFX trả phí Epidemic qua MCP vào kho ambient per-niche (tái dùng nguyên `import_from_manifest`, KHÔNG đẻ đường ghi kho thứ 2); 6 BẪY đo thật (key FREE search được KHÔNG tải được · `term` phải LỒNG trong `query` nếu không server LẶNG LẼ trả list mặc định · link 60s · key 30 ngày · file gốc 24bit/96k · **title dài trùng 60 ký tự đầu → FILE ĐÈ NHAU**, dính thật market_8/9+boat_9/10, vá bằng slug gắn `id[:8]`, dọn 4 file trùng khỏi kho 346→342) + LƯỚI LOÀI `title_matches` chống penguin→ngỗng/vịt-đồ-chơi (tái lập RD-89); `--no-epidemic` bật/tắt MỖI LẦN DỰNG tại chokepoint `list_variants` (1 chỗ, cả 4 tầng SFX theo). **BÀI HỌC: nạp kind theo NHU CẦU BÀI (`subject_sfx_log`), không theo độ mỏng kho** — mẻ đầu nạp 6 kind mỏng nhất → 0/115 lượt dùng. ② **SFX CHỦ THỂ 3 TẦNG** (user chê 5 ca cổng TAI đợt 2): gốc bệnh `db_subject_lookup` GỘP PHẲNG subject+tags+description — `tags` là DANH SÁCH BỐI CẢNH (GLM liệt kê mọi thứ thấy, không phân biệt chủ thể với phông nền) → chanh-trong-chợ kêu tiếng chợ. Chẩn đoán ĐẦU sai (đoán `description`), ĐO sổ mới ra: 5/5 khớp qua `tags`, `subject` ĐÚNG cả 5. Tầng 1 `subject` quyết định · tầng 2 `tags` cứu TRỪ `NOISY_KINDS` (hiện thực ý user *ưu tiên tiếng dễ nghe hơn urban_street* — kind ồn đòi ĐÍCH DANH, không phải cửa loại mà là ngưỡng bằng chứng) · tầng 3 `--sfx-llm` NÃO chấm ca bảng luật MÙ CHỮ, 1 CALL/MẺ, fail-open. ③ **VÒNG 3** (user chê 3/19 ca NÃO): đo ra quy luật TÁCH SẠCH — 15 ca cảnh RỘNG duyệt hết, 4 ca cảnh HẸP chê 3/4 → `SPATIAL_KINDS`+`allowed_for_shot()` chặn tiếng KHÔNG GIAN trên cảnh hẹp (khung hình chỉ có 1 người/1 vật thì tiếng phải từ CHÍNH chủ thể). **★★ LỖ HỔNG KIẾN TRÚC phát hiện kèm: quyết định NÃO KHÔNG đi qua LUẬT AN TOÀN mà đường bảng luật phải tuân** — b063 đèn bí ngô lách được luật fire-cận-cảnh (tai V7). Đã vá. LUẬT CHUNG: thêm đường LLM song song → mọi luật an toàn áp CẢ HAI đường, không thì LLM thành CỬA SAU. ④ Nâng `SUBJECT_VOL` 0.18→0.40 (-15→-8dB) + `SUBJECT_BREATH_VOL` 0.32→0.56 (-10→-5dB) — user nói "-8dB" nhưng có HAI mức theo ngữ cảnh voice, nâng lẻ mức trong-voice sẽ VƯỢT mức khoảng-thở (ngược logic, giọng bị lấn) → HỎI user, chốt nâng cả hai giữ khoảng cách 3dB. 📌 LỆCH BẢN GỐC: cao hơn số đo editor PB13 ~7dB — TAI USER ĐÈ SỐ ĐO (tiền lệ DS5-083). Rà P5: 5 chỗ IN SỐ CỨNG trong chuỗi báo cáo đã sửa (không sửa = báo cáo nói dối) + 2 pytest ghim số trần (ĐÚNG chức năng) | ✅ **CỔNG TAI V11 DUYỆT 2026-07-18** (RD-89 Oman; V4→V11 8 bản). Số đo: urban_street 51/120 (42%) → 35 · wind 37 · NÃO điền 13 ca toàn cảnh rộng. Sửa kèm: chạy lại stage `music` (RD-89 mất nhạc 16/16 chương do pool đổi sau nạp đợt 2) | pytest **624/624 0 skip** (+52: 31 epidemic · 12 subject_llm · 9 ba-tầng/hồi-quy) | 2026-07-18 |

## 2026-08-05 — TINTUC-E2E: video kiểm đầu tiên trên máy này (kênh tin-tuc) + fix PATH claude

**Cái gì đổi.** Không đổi dòng code nào. (1) Fix môi trường: thêm `%USERPROFILE%\.local\bin`
vào PATH user (registry) — Claude Code bản native installer đặt `claude.exe` ở đó nhưng
PATH thiếu → mọi lệnh pipeline gọi NÃO chết ngay tại `cc_client.py` FileNotFoundError.
(2) Dựng trọn 1 video kiểm 4p35 kênh `tin-tuc` (núi lửa Indonesia) qua /dung-video đường sâu:
7 chương/45 beat → draft `SCRIPT1_20260805_072653`.

**Vì sao.** User báo lỗi "Không tìm thấy 'claude'" rồi giao dựng video test đầu tiên trên
máy này. Kênh `tin-tuc` là niche MỚI: kho footage rỗng + kho nhạc rỗng → video này chạy
100% Pexels và không nhạc — đúng fail-open thiết kế, đồng thời là mốc so sánh khi kho
tin-tuc được nạp sau này.

**Verify.** `claude -p` non-interactive trả lời OK (subscription, không API key) · ingest
PASS (vòng 2, sau khi chia 2 beat >10s) · source 45/45, 0 needs_human · assemble 0 lỗi ·
**cổng mắt user ĐẠT 2026-08-05** (CapCut mở draft OK, không relink). Lưu ý vận hành đã ghi
vào bảng: alignment quirk sau [430] (Whisper dán "The" vào câu trước — ô thở phải dời),
2 clip slow-mo b19/b35 editor nên swap.

**Việc treo cho máy này:** nạp kho footage + nhạc niche tin-tuc; PATH fix chỉ hiệu lực
terminal mới (đã dặn user).

## 2026-07-19 — NHỊP-M0: lưu độ mạnh beat/accent + đo lại 433 bài (mở đường cắt theo nhịp nhạc)

**Cái gì đổi.** Thư viện nhạc nay lưu thêm 2 trường: `beat_strength` (độ mạnh tại từng beat)
và `accent_strength` (độ mạnh từng accent), chuẩn hoá 0-1 trong bài. Sửa 4 chỗ:
`music/analyze.py::_rhythm_from_signal` (+`beat_strength`), `::_pick_accents` (trả tuple 2
mảng, **sort lại theo THỜI GIAN**), `music/library.py:24` `RHYTHM_KEYS` (+2 tên trường),
`::_import_entries` (điều kiện nâng cấp record cũ). Đã đo lại toàn bộ **433 bài**.

**Vì sao.** User dựng tay project mẫu `E:\CapCut Drafts\0719` yêu cầu tool copy cách editor
thật cắt theo nhịp. Đã làm lưới beat (`music/minihook.py`) + 4 draft thử — **user duyệt
2026-07-19**. Nhưng lưới beat cần biết "beat này mạnh hay yếu" mà hệ thống **không lưu**:
`onset_strength` được tính rồi **VỨT** ở 3 chỗ, nên script thử phải **nạp lại file nhạc**
mỗi lần chạy. Cái duy nhất có là `energy_curve` **8 số cho cả bài** = ~21 giây/số — hỏi
"giây 88 mạnh hay yếu" chỉ nhận được trung bình cả dải 84-105s. M0 vá đúng lỗ này.

**🐛 Bẫy suýt dính — điều kiện nâng cấp record cũ.** `_import_entries` chỉ hỏi
`"beat_tier" not in obj`. Mà **cả 433 bài ĐỀU đã có `beat_tier`** (nạp từ MUSIC SYNC M0
2026-07-13), chỉ thiếu độ mạnh → **toàn pool lọt lưới**: đo lại vẫn chạy, vẫn báo thành
công, dữ liệu không có. Vá `or "beat_strength" not in obj`.
**Luật rút ra:** hỏi **"có KEY không"**, KHÔNG hỏi "có giá trị không" — tier C hợp lệ khi
có key mà mảng rỗng; hỏi giá trị thì tier C bị đo lại mãi mãi.

**Vùng ảnh hưởng đã rà (P5).** `_pick_accents` chỉ có **1 call site** (`analyze.py:134`,
đã sửa) — đổi chữ ký an toàn. Mọi consumer (`select.py` chọn bài, `plan.py::anchor_offset`
neo offset, `plan.py::timeline_accents` sinh mốc snap, `_track_drive` chấm độ dồn) đọc index
**theo TÊN TRƯỜNG**, không theo vị trí → thêm trường mới **không đổi hành vi tầng nào**.
Kiểm chứng bằng máy sau khi đo: **0 field cũ đổi giá trị** · `accents` đổi THỨ TỰ nhưng
**KHÔNG đổi tập hợp** (0 bài thêm/mất accent) · **0 bài lệch độ dài** giữa 2 mảng.

**Verify.** `F:\AutoEdit\music` 317 bài/151s (313 có độ mạnh, 4 tier C ambient rỗng đúng ý
đồ) + `F:\AutoEdit\music\life-in` 116 bài/54s (115, 1 tier C). Backup
`music_index.pre_strength_20260719.json` cả 2 folder. Độ mạnh trải **0,17→1,00**, trung vị
0,29, **~20% beat mạnh ≥1,5× trung vị** — đủ thưa để làm mốc cắt, đủ dày để lúc nào cũng có
một beat mạnh gần chỗ muốn cắt.

**★ Số đo phủ nhận mẫu beat CỨNG.** `HOOK_PATTERN=(3,5,5,3,4,4,5,4)` + khoá 8 beat (copy từ
`0719`) cho ra shot: 152 BPM→3,2s · 172→2,8s · **89→5,4s** ⚠ · 136→3,5s — chênh gần **2×**.
Tai người cảm nhận shot theo **GIÂY**, không theo số beat. M1 phải nhắm khoảng THỜI GIAN
rồi quy ngược ra số beat (nhạc chậm dùng ít beat hơn). Khoảng nhắm **chưa chốt** — đo ở M1.

**Số pytest: 640/640, 11 skipped** (nền 635 + 5 mới trong `test_music_rhythm.py`: 2 mảng
song song · accent sort theo thời gian · tier C rỗng cùng lúc · **hồi quy record-có-tier-
thiếu-độ-mạnh** · regrid ghi được field mới).

**Kế tiếp: M1 — cắt nhịp ở HÌNH THỞ.** Chọn làm trước đoạn chèn vì hình thở **đã có sẵn
trong mọi video** → không chèn gì → không đụng bug NAM CHÂM, không dịch toạ độ, không làm
ôi thiu kế hoạch nhạc; là **phép thử rẻ** cho lưới beat trong bài thật. Đo được: 367 ô thở
/15 project, trung vị 4,0s, **22% dài ≥6s**. User chốt **BỎ trần 3 miếng/ô**.
→ Bàn giao đầy đủ (lộ trình M0-M6, mọi file:dòng đã rà, 3 bẫy M1, vùng ảnh hưởng M2,
footage M4/M5, tồn đọng): **`BAN_GIAO_NHIP_NHAC.md`**.

---

> **PHASE A HOÀN TẤT (2026-07-01):** skeleton dựng-từ-đầu chạy trọn trên Windows, LLM qua
> Claude Code subscription. Pipeline new→align→direct→cut→source→assemble→report OK, draft
> CapCut mở/xem được (cổng mắt user OK).
>
> **▶ BƯỚC KẾ TIẾP ĐÃ CHỐT (2026-07-01, CHƯA LÀM): NÃO-CÁCH = "L2b sâu".** Cho Claude Code
> TỰ đọc transcript + `FOUNDATION.md` để chỉ đạo (pacing/hình thở/cỡ cảnh/mood/tiết chế overlay),
> THAY prompt cứng của autoedit director. Lý do chọn: thượng nguồn của NÃO-GÌ (director tả concept
> trước → sourcer mới tìm footage); dùng kiến thức đã có; lift chất lượng mọi video ngay; đúng mạch
> Level 2. Phase B (DNA niche = NÃO-GÌ) làm SAU khi NÃO-CÁCH khá + ống ổn. (User compact chat tại đây.)
>
> **▶ CẬP NHẬT 2026-07-02 (§F0) — kế hoạch trên được TINH LẠI:** trước khi làm L2b sâu, xây bộ
> `foundation/` (mỗi kỹ năng edit 1 file, danh mục 17 file đã khóa). L2b sâu sau đó sẽ đọc bộ
> foundation MỚI này thay vì `FOUNDATION.md` cũ. Bước kế tiếp thực tế = viết foundation đợt 1
> (pacing → hình thở → mood&tone). Chi tiết + lộ trình 5 bước: §F0.

> **▶ BƯỚC KẾ TIẾP — USER CHỐT 2026-07-09: trình tự "D → C có nhịp thở → scale", chi tiết ở
> `DINH_HUONG_VIEC_TIEP_THEO.md` §TRÌNH TỰ ĐÃ CHỐT.** Nâng cấp full tính năng TRƯỚC, scale SAU;
> kỷ luật: mỗi 1–2 tính năng C dựng 1 video thật làm cổng mắt/tai (video kiểm = video sản xuất).
> **CẬP NHẬT 2026-07-09 (cùng ngày): NHÓM D ĐÓNG TRỌN.** D1 backup ✅ · D5 git local ✅
> (commit gốc `890c68b`, KHÔNG remote/push — user từng hoãn vì tưởng là GitHub, đã làm rõ)
> · D4 key BỎ (hệ không cần ANTHROPIC_API_KEY, đã xóa khỏi .env — đừng hỏi lại) · D2 ✅
> (direct cũ ăn khối vocab C4 + DNA).
>
> **▶ TRẠNG THÁI 2026-07-10 (mới nhất): NHÓM C ĐÓNG TRỌN — cả 5 đợt.** Đợt 5 C5 vision
> gate đóng bằng video kiểm **V11** (cổng MẮT + TAI user duyệt 2026-07-10: "mọi thứ đã ok,
> duyệt qua"; nhạc editor 4 chương lần đầu ra trận đạt tai). **Quan sát user ghi lại:
> "cổng gate CHỌN LẠI chưa ngon lắm nhưng chấp nhận được"** — gate GẠT trúng (3/3 ca chê
> đều có lý) nhưng ỨNG VIÊN THAY chỉ tốt bằng pool còn lại; THEO DÕI các video sau, nếu
> dồn ca thay-xoàng thì cân nhắc cải thiện bước chọn-thay (vd demote ưu tiên nguồn khác).
> Gate chốt hình hài: CHỈ soi pick KHO LOCAL (`GATE_SOURCES`) · không schema block ·
> xoay 3 key · tắt theo 3 lỗi liên tiếp · +2'/video. pytest **388/388**.
> **VIỆC KẾ TIẾP (roadmap user chốt — sang NHÓM A/B, xem DINH_HUONG):**
> 1. **A1 ★ video space kế tiếp (SP013...)** — user đưa folder content+voice; mỗi video
>    vừa là sản phẩm vừa ĐO thời-gian-người từng khâu (chính là B1, tiền đề quyết B2).
> 2. **B2 Level 1 batch** khi có số đo B1 → **B3 niche 2** (checklist memory
>    multi-niche-isolation-audit: nạp kho + library-dna + pause_dna niche đó; nhạc pool
>    chung chỉ tách nếu tai chê) → **B4 learning loop** cột `approved`.
> 3. Backlog chất lượng chờ user gọi: **chapter-title card + whoosh/swell đi cùng**
>    (design đã chốt: đơn giản/basic/VIẾT HOA/dễ nhìn; kho swell ×8 + whoosh ×16 chờ) ·
>    drone theo mood chương · nhạc "2 3 được" chờ đặt mood · k_dist shot thở khi học
>    thêm draft editor.
> 4. Còn ngỏ kỹ thuật treo: (a) **direct cũ timeout chương dài** ~424 từ vượt trần 600s
>    `claude -p` — sửa khi làm B2/L1 (bump timeout hoặc chẻ chương thành nhiều call);
>    (b) cropdetect viền-nướng-pixel cho MẺ NẠP viral sau; (c) sau mẻ nạp lớn chạy lại
>    2 lệnh robocopy backup D: (§D1-BACKUP); (d) echo Ken Burns CLI in "100%→X%" theo
>    zoom tương đối (cosmetic — keyframe thật là cover→cover×zoom); (e) `pause_dna.new.json`
>    space (số đo thô C7) để tham khảo — bản duyệt giữ nguyên, KHÔNG cần làm gì;
>    (f) origin-vào-phễu đã BỎ theo user — chỉ mở lại nếu ca sai-nghĩa từ kho dồn thêm.

Ký hiệu: ✅ đạt · 🔄 đang chạy · ⏸ hoãn/chờ.

---

## Template 1 entry (copy khi ghi milestone mới)

```
## §N — <tên milestone> (YYYY-MM-DD)
- **Cái gì đổi:** <file/hàm cụ thể>
- **Vì sao:** <lý do / quyết định / trade-off>
- **Verify:** <pytest nào xanh + số test> · <cổng mắt CapCut: user xác nhận chưa?>
- **Ghi chú / còn ngỏ:** <TODO, rủi ro, link memory [[...]]>
```

---

## §0 — Phiên 0: dựng khung nền + bản đồ tri thức (2026-07-01)

- **Cái gì đổi:** tạo folder `tool edit padoma` + 4 file nền:
  - `CLAUDE.md` — hiến pháp làm việc (P1–P4, NT1–NT5 thích nghi dựng-từ-đầu, luật CapCut
    C1–C5 bê nguyên, bảng provider, hệ thống ghi chép).
  - `BAN_DO_TRI_THUC.md` — bản đồ trỏ tới nguồn code ở `autoedit` (xương sống dựng-từ-đầu)
    + `nhan ban` (luật CapCut + API mới + ghi chép). Verdict copy/adapt/learn từng mục.
  - `PRD.md` — skeleton, phần logic để nhãn 🔸 ĐANG BÀN.
  - `NHAT_KY_BUILD.md` — file này.
- **Vì sao:** "link" kiến thức sẵn có sang project mới để phiên sau AI không đọc lại cả
  project cũ; dựng sẵn hệ thống ghi chép để mỗi thay đổi về sau đều được theo dõi + chuyển giao.
- **Quyết định chốt với user:** tool mới = DỰNG VIDEO MỚI TỪ ĐẦU (không phải nhân bản);
  vẫn xuất CapCut draft (luật C1–C5 áp dụng); code = tham chiếu quyết định từng module;
  lần này chỉ khung tối thiểu để bàn tiếp (chưa .env/launcher/code).
- **Verify:** chưa có pytest (chưa code). Cổng kiểm: 4 file đọc được, đường dẫn bản đồ trỏ đúng.
- **Còn ngỏ / bước sau:**
  1. **Bàn logic** để điền `PRD.md` (input/output, pipeline stages, data model, milestone).
  2. Hoãn tới khi chốt logic: `.env.example`, 3 launcher .bat, `KINH_NGHIEM_CHUNG.md` +
     `RA_SOAT_LOGIC.md` riêng, cấu trúc code + `pyproject.toml`, copy module theo bản đồ.

---

## §1 — Phiên 1: bàn hướng đi + chốt roadmap (2026-07-01)

- **Cái gì đổi:** điền `PRD.md` — §1 (2 chế độ + luận điểm foundation), §3 (giữ pipeline autoedit +
  kiến trúc tách ỐNG/NÃO), §8 (roadmap Phase A–E + bảng chi tiết Phase A), §9 (3 module khó + hình thở).
- **Quyết định chốt với user (qua hỏi-đáp):**
  1. **2 chế độ dùng:** edit toàn bộ · edit một phần (nối tiếp draft editor làm dở 10–15').
  2. **Luận điểm cốt lõi:** edit phải có tư duy đạo diễn → cần foundation từng kỹ năng + DNA niche.
  3. **Bắt đầu = skeleton biết đi trước** (không phải foundation trước) — vì cần pipeline tiêu thụ
     để kiểm chứng foundation.
  4. **Codebase = copy autoedit sang padoma làm project mới** (tiến hóa độc lập, không đụng gốc).
- **Phát hiện quan trọng:** autoedit KHÔNG phải khung dở — nó là pipeline dựng-từ-đầu ĐÃ hoàn chỉnh,
  ~125 pytest, CLI đủ stage, có sẵn hướng dẫn setup Windows. → Phase A phần lớn là **port + kiểm
  chứng**, không phải code mới. Rủi ro chính: autoedit gốc là Mac; bằng chứng CapCut-Windows ở `nhan ban`.
- **Verify:** chưa có pytest mới (mới design + doc). Cổng kiểm: PRD/NHAT_KY đọc được, khớp bàn bạc.
- **Còn ngỏ / bước sau:** thực thi A0 (copy + `uv sync` + pytest). Cần user cung cấp 1 script+voice
  ngắn cho A3 (hoặc dùng `samples/` của autoedit). Sau A0 xanh → đề xuất `git init` (mốc khôi phục).

---

## §A0 — Copy codebase + setup env (2026-07-01)

- **Cái gì đổi:** copy `⟪AE⟫..\autoedit` → `padoma\autoedit` + `⟪AE⟫..\capcut_test` → `padoma\capcut_test`
  (robocopy, loại `.venv/.git/.pytest_cache/projects/__pycache__`). Giữ cấu trúc 2 folder để path
  tương đối `parents[2]/capcut_test` trong `cli.py` vẫn đúng. `uv sync` tái tạo `.venv`.
- **Vì sao:** codebase mới độc lập cho padoma (quyết định Phiên 1).
- **Verify:** Python 3.11.9 + uv 0.11.21. `autoedit --help` OK. **pytest 145/146 xanh** — 1 fail duy nhất
  `test_make_launcher_creates_executable` là **Mac-only** (kiểm bit thực thi `.command` bash; Windows
  dùng `.bat`). Cổng pytest ĐẠT.
- **Còn ngỏ:** A1 — port Mac→Windows: (1) `machine.py` CapCut path (đang hardcode Mac ~/Movies), (2)
  skip/guard test launcher `.command` trên Windows, (3) `textutil` (rtf→txt). Sau đó `register-machine`.

---

## §A1 — Port Mac→Windows (2026-07-01)

- **Cái gì đổi:**
  - `packager/machine.py`: `DEFAULT_CAPCUT_ROOT` → hàm `_default_capcut_root()` theo OS
    (Windows: `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft`; Mac giữ `~/Movies/...`).
    Thêm `import os, platform`.
  - `tests/test_make.py`: guard `assert S_IXUSR` bằng `if os.name != "nt"` (bit thực thi `.command`
    chỉ có ở Mac/Linux; Windows dùng `.bat`).
- **Vì sao:** điều kiện tiên quyết để `register-machine` tìm được draft CapCut trên Windows.
- **Verify:** **pytest 146/146 xanh** (hết fail Mac-only). `register-machine` chạy OK — auto chọn donor
  `GL26__VIETNAM_V10`, CapCut **8.7.0** (new_version 173.0.0), root Windows đúng. Cổng A1 ĐẠT.
- **⚠ Còn ngỏ / rủi ro cho A2:** donor auto-chọn `GL26__VIETNAM_V10` là **draft do tool `nhan ban`
  sinh** (không phải draft CapCut tạo tay nguyên bản). register-machine chỉ trích platform/version
  (an toàn), nhưng nếu **A2 (demo-draft) mở CapCut lỗi** → nghi donor đầu tiên: bảo user tạo 1 draft
  CapCut mới tinh (mở CapCut → new project → lưu) rồi `register-machine --donor <đó>`.
  Ngoài ra CapCut ở đây là **8.7.0** (bài học `nhan ban` là 8.8.0) — theo dõi khác biệt nếu có.
- **Chưa làm (P2 — chỉ làm khi cần):** `textutil` rtf→txt (script test là `.txt` nên bỏ qua).

---

## §A2 — Cổng mắt CapCut đầu tiên: demo-draft (2026-07-01)

- **Cái gì đổi:** không sửa code — chạy `autoedit demo-draft --overwrite` sinh `PADOMA_AUTOEDIT_DEMO`
  vào folder CapCut.
- **Verify (CỔNG MẮT — user xác nhận):** user báo **"mọi thứ đã ổn"** → draft mở được, không crash,
  preview không đen, đủ 2 shot video + voice + nhạc + text, không đòi relink.
- **Kết luận quan trọng:** **packager autoedit chạy tốt trên CapCut Windows 8.7.0** — KHÔNG cần port
  luật C1–C5 từ `nhan ban` (ít nhất ở mức demo). Donor tool-sinh (`GL26__VIETNAM_V10`) dùng được.
  Rủi ro donor coi như đã loại ở mức demo.
- **Còn ngỏ:** A3 — chạy full `make` trên video thật (`samples/`), cổng mắt draft đầy đủ + report.html.

---

## §A3 (dở) — Chạy full make trên samples/ (2026-07-01)

- **Cái gì đổi:** chạy `autoedit make samples --channel retirement-abroad`. Tạo project
  `projects/samples-20260701-094253`.
- **Kết quả:** **align ✅ done** (whisper chạy tốt trên Windows — timestamp + transcript.json OK).
  **direct ❌ failed:** `AuthenticationError 401 invalid x-api-key` → **ANTHROPIC_API_KEY trong
  `.env` (copy từ autoedit) đã hết hạn/không hợp lệ**. KHÔNG phải lỗi model.
- **KẸT — cần user:** cung cấp `ANTHROPIC_API_KEY` hợp lệ (ghi vào
  `padoma\autoedit\.env`). Có thể cũng cần refresh `PEXELS_API_KEY`/`SERPER_API_KEY` khi tới source.
- **Resume:** sau khi có key, chạy LẠI `autoedit make samples ...` (hoặc `run projects/<id>`) → tự
  bỏ qua align (đã done), chạy tiếp direct→cut→source→assemble→report. Pipeline resume theo project.json.

---

## §1b — PIVOT: NÃO chạy qua Claude Code (không API key) (2026-07-01)

- **Quyết định user:** LLM (director + brain) chạy **qua Claude Code / subscription**, bỏ đường
  `ANTHROPIC_API_KEY` metered. Lý do: (1) đã có tài khoản Claude editor dùng hằng ngày; (2) tùy biến
  bằng hội thoại; (3) fix-cứng-API phát nhiều máy hay lỗi vặt. Chi tiết PRD §6.
- **Hệ quả:** khớp tách ỐNG/NÃO. Bước `direct` (và các bước LLM sau) KHÔNG gọi `anthropic` SDK nữa
  mà đi qua Claude Code (`claude -p` headless hoặc Agent SDK). ỐNG (align/cut/assemble/package) giữ Python.
- **Ảnh hưởng A3:** không unblock bằng API key nữa. Kế hoạch mới: spike Level 1 — reroute `direct`
  qua Claude Code → vừa đóng A3 vừa chứng minh đường mới chạy end-to-end.
- **CHƯA chốt:** Level 1 (đổi cơ chế gọi LLM) vs Level 2 (NÃO = skills/subagents editor điều khiển).
  Đang hỏi user thứ tự đi. Rủi ro cần verify khi thiết kế: trần usage, structured output qua claude -p, AUP.

---

## §1c — CHỐT: đi Level 2 trước, Level 1 sau (2026-07-01)

- **Quyết định user:** đi **Level 2 trước** (NÃO = skills/subagents Claude Code, editor điều khiển hội
  thoại), **Level 1 sau**. Lý do chiến lược: Level 2 = chế độ **học/tinh chỉnh** (mò ra luật đúng theo
  niche); Level 1 = chế độ **sản xuất hàng loạt** (đóng băng luật đã chín). Trigger chuyển: 1 niche
  chạy trơn ~20–30 video + editor fix hết lỗi.
- **Ba trụ kiến trúc để L2→L1 mượt (không phí công):**
  1. **ỐNG xây 1 lần dùng cả 2 level** — align/cut/source/assemble/package = Python thuần, gọi độc lập,
     ranh giới `project.json` (NT1). L2 (Claude Code nhạc trưởng) và L1 (pipeline tự động) gọi cùng ỐNG.
  2. **Mọi quyết định NÃO của L2 (+ chỗ editor sửa) ghi vào `project.json`** → là bản thiết kế cho
     director L1. Chuyển level = đóng băng luật đã học, KHÔNG viết lại.
  3. **NT4 giữ cả 2 level** — Claude Code chỉ quyết nghĩa (word index/concept), timestamp do ỐNG +
     Pydantic gác. L2 hội thoại tự do vẫn không đẻ draft sai giờ.
- **Nhánh nhỏ trong L2 (đề xuất, chốt khi làm viên gạch đầu):** nhạc trưởng = **Claude Code (L2b)** —
  editor làm việc trong 1 phiên Claude Code, Claude Code đọc script → quyết beat/footage → gọi ỐNG →
  ghi project.json. (Không phải L2a "Python shell claude -p".)
- **Viên gạch đầu (kế hoạch, CHƯA làm — chờ user gật):** tách `direct` làm đôi → (a) lệnh xuất ngữ
  cảnh đạo diễn (transcript+timestamp) cho Claude Code đọc; (b) lệnh nhận quyết định đạo diễn (JSON) →
  Pydantic validate → ghi project.json. Claude Code làm phần giữa. Xong `direct` → cut→source→assemble→
  report (toàn ỐNG). Vừa đóng A3, vừa mở L2b; sau thay phần giữa bằng `claude -p` = có Level 1. Xem [[level2-first-then-level1]].

---

## §B1 — Viên gạch đầu Level 2: director qua Claude Code (2026-07-01)

- **Cái gì đổi:**
  - MỚI `autoedit/director/cc_client.py` — `ClaudeCodeDirectorClient` cắm vào Protocol
    `DirectorClient` (không đụng runner/schema/validator/prompts). Gọi `node cli.js -p
    --output-format json --json-schema <schema> --tools "" --model <m>`, prompt qua stdin,
    parse `structured_output` → Pydantic; token từ `usage`.
  - `cli.py::direct` thêm `--engine` (mặc định **claude-code**; `api` = đường cũ). Bỏ import
    cứng ClaudeDirectorClient, chọn backend theo engine.
  - MỚI `tests/test_cc_client.py` — 5 test giả lập subprocess (parse structured_output +
    usage; xoá ANTHROPIC_API_KEY khỏi env con; lỗi exit/is_error; complete_grounded raise).
- **Vì sao:** thực thi quyết định Level-2-trước ([[level2-first-then-level1]]). Đây là "đường
  ống chung" cả 2 level. Cắm qua Protocol có sẵn = phẫu thuật (P3), không đập pipeline.
- **Verify:** **pytest 151/151** (146 cũ + 5 mới). **direct thật exit 0** trên
  `samples-20260701-094253` (đã align): 3 chương, 8 beat, không 401. Warnings chỉ là chất
  lượng (lạm dụng hình thở/overlay) — để tinh chỉnh Level 2 sau.
- **Bẫy Windows đã fix (chi tiết [[claude-code-subprocess-windows]]):** shim `.CMD` bị cmd.exe
  parse lại vỡ JSON → gọi thẳng `node cli.js`; `errors="replace"` chống UnicodeDecodeError
  nuốt stderr; KHÔNG `--bare` (ép API key); xoá ANTHROPIC_API_KEY khỏi env con.
- **Còn ngỏ:** (1) A3 tiếp: cut→source→assemble→report — **source cần PEXELS/SERPER key** (khác
  đường Claude Code, là API stock riêng). (2) `enrich --web` chưa hỗ trợ qua Claude Code
  (complete_grounded raise) — chỉ cần khi bật web-grounded, không chặn A3. (3) Chất lượng
  director (hình thở/overlay) tinh sau. (4) Lớp hội thoại L2b thật (skill editor điều khiển)
  xây LÊN TRÊN ống này ở bước sau.

## §B2 — Buồng lái hội thoại L2b: skill /dung-video (2026-07-01)

- **Cái gì đổi:**
  - MỚI `.claude/skills/dung-video/SKILL.md` — buồng lái để editor điều khiển pipeline BẰNG
    HỘI THOẠI. 2 pha có cổng duyệt: Pha 1 (new→align→direct→tóm tắt beat→DỪNG) · vòng chỉnh
    (editor góp ý → cập nhật `inputs.brief` project.json → chạy lại direct) · Pha 2 (cut→source→
    assemble→report). Cổng duyệt TRƯỚC khi tải footage = tiết kiệm đúng chỗ.
  - VÁ BUG: `cli.py::run` gọi `direct(...)` thiếu `engine` → typer OptionInfo rơi nhánh `else` =
    API key = 401. Sửa: `direct(project_dir, model=director_model, engine="claude-code")`. (make
    đã truyền director_model tường minh nên chuỗi make→run→direct nay thông qua claude-code.)
- **Vì sao:** hiện thực lựa chọn "buồng lái L2b" — khung để editor dùng + dạy tool (chế độ học
  Level 2). Lever hội thoại thật = duyệt/chỉnh beat qua brief rồi re-run direct.
- **Verify:** pytest 151/151; `run` smoke OK (nạp + nhận diện stage done). Cơ chế re-run direct
  theo brief mới: xác nhận qua đọc code (runner đọc `project.inputs.brief`; lệnh `direct` gọi
  run_direct vô điều kiện → re-run được). **Cổng nghiệm thu thật = editor gõ `/dung-video` thử**
  (skill hội thoại không test bằng pytest).
- **Còn ngỏ:** (1) editor thử skill trên máy → phản hồi. (2) Đây mới là L2b "nông" (đạo diễn vẫn
  là prompt autoedit chạy qua claude -p; editor chỉnh qua brief). L2b "sâu" (Claude Code TỰ đọc
  transcript + FOUNDATION quyết beat, thay prompt cứng) là Phase C. (3) Chất lượng director
  (hình thở/overlay) tinh sau. (4) `enrich --web` chưa qua Claude Code.

---

## §B3 — Fix bug SegmentOverlap 1µs khi assemble (2026-07-01)

- **Bối cảnh:** editor chạy `/dung-video` dựng phần HOOK 1 video tiếng Việt (niche facts about
  countries, folder `E:\CapCut Drafts\RD70-1\Voice\viet nam`, voice `hook.mp3` 48.7s). Pha 1
  (4 chương/17 beat) duyệt OK. Sang Pha 2, `assemble` sập.
- **Cái gì đổi:** `packager/assembler.py::_build_content` (video_l1) — đổi
  `want_us = int(w.duration*SEC)` + `Timerange(int(w.start*SEC), want_us)` thành
  `start_us = round(w.start*SEC)` + `want_us = round(w.end*SEC) - start_us` +
  `Timerange(start_us, want_us)`.
- **Root cause:** `int()` CẮT CỤT tích số thực. `4.18*1_000_000 = 4179999.9999...` → `int` =
  **4179999**, trong khi mép beat trước (beat 1) kết thúc ở **4180000** → beat 2 bắt đầu sớm
  1µs → 2 video segment đè nhau → pycapcut `SegmentOverlap`. `coverage_windows` (float) vẫn
  liền mạch nên invariant PASS — bug chỉ lộ ở tầng đổi sang microsecond nguyên. Fix: `round()`
  cả 2 mép + tính want từ 2 mép đã round → kề nhau khít trong không gian số nguyên.
- **Vì sao lọt lưới:** test assembler cũ toàn dùng mốc TRÒN (0.0/2.0/4.0) → không kích hoạt
  truncation. Timeline thật từ align luôn có số lẻ (1.64, 4.18...).
- **Verify:** thêm `test_run_assemble_fractional_boundaries_no_overlap` (mốc 1.64/4.18 tái hiện
  lỗi cũ, assert video segment kề nhau khít). pytest `tests/test_assembler.py` **15/15 pass**.
  Draft sinh OK: `VIETNAM_HOOK_AI_CAP_20260701_110429`. **Cổng mắt CapCut = editor tự mở kiểm.**
- **Còn ngỏ:** cùng kiểu `int(...*SEC)` còn ở `_add_pip_charts`, info-card, overlay (khác track,
  1 segment/beat nên chưa đè) — nếu sau này gặp overlap tương tự thì áp cùng cách `round()`.

---

## §F0 — Chốt hệ thống FOUNDATION (danh mục + khuôn + lộ trình) (2026-07-02)

- **Cái gì đổi:** phiên bàn bạc thuần (không code). MỚI `foundation/GHI_CHEP_GOC.md` — lưu
  NGUYÊN VĂN lời user đọc 8 foundation (pacing, hình thở, chuyển cảnh, ducking, mood&tone,
  sound design, shot variety, text/typo) + danh mục khóa. Đây là nguyên liệu gốc để viết
  các file foundation (transcript chat sẽ bị dọn, không dựa vào nó).
- **Vì sao (bối cảnh):** user đổi hướng — TRƯỚC khi làm "L2b sâu", phải xây **hệ thống
  foundation cho từng kỹ năng edit nhỏ**: nó là gì → yếu tố ảnh hưởng → cách làm thực tế
  Ở PROJECT NÀY. Bộ foundation này chính là "ruột" mới của director (L2b sâu = Claude Code
  đọc foundation để chỉ đạo, thay prompt cứng autoedit).
- **Quyết định chốt với user:**
  1. **Kiến trúc tri thức 2 tầng:** Foundation (viết 1 lần, mọi niche — định nghĩa CHIỀU nào
     quan trọng + cơ chế) ↔ **DNA niche** (số liệu cụ thể per-niche, học ở Phase B từ footage
     CẮT RA từ video viral + project cũ của editor — khác project cũ vốn có thư viện sẵn).
     Foundation KHÔNG chứa số liệu niche; phần 5 chỉ định nghĩa TÊN tín hiệu cần học.
  2. **Danh mục khóa 17 file** (từ ~22 mục gốc, bảng đầy đủ ở `foundation/GHI_CHEP_GOC.md`):
     A (3): chia beat · chức năng đoạn · open loop/callback. B (2): mood&tone · pattern
     interrupt. C (7): phân tuyến nguồn · ẩn dụ+veto nghĩa+**veto mood C2b mới** · ngữ cảnh
     chuỗi · từ khóa tìm · lọc/xếp hạng · footage chữ ký · **shot variety (mới)**. D (3):
     **pacing TRÙM** (nuốt B2 đường-cong-năng-lượng + D1 độ-dài-shot + quyết định cắt-tại-
     nghỉ-voice) · **hình thở** (file riêng theo lệnh user, note rõ là một phần pacing) ·
     loại cắt+transition (D2+F4 cũ gộp). E (1): **sound design TRÙM** (gồm ducking). F (2):
     **text/typo/motion-graphics TRÙM** (F1+F3, lớp nghĩa 2–3) · ken burns/punch-in.
  3. **Khuôn 5 phần/file:** Là gì · Yếu tố ảnh hưởng · Cách làm THỰC TẾ ở project này ·
     Cạm bẫy · Học gì từ DNA niche. **Phần 3 viết dạng "dự kiến 🔸"** (user chọn), chốt dần
     khi chạy thật Level 2.
  4. **Phần 3b "Phân rã năng lực" (từ cảnh báo user):** foundation viết bằng ngôn-ngữ-editor;
     vài câu nói có thể = rất nhiều code. Mỗi luật phải dịch thành: (a) đã có sẵn (trỏ module)
     / (b) cần code mới ỐNG / (c) NÃO quyết lúc chạy / (d) cần dữ liệu DNA. Gom (b) toàn bộ
     = backlog code có căn cứ; gom (d) = spec schema tag Phase B.
  5. **Phạm vi (Claude tự quyết theo ủy quyền user):** foundation CHỈ cho kỹ năng NÃO. Kỹ
     thuật ỐNG (C1–C5, transcode C4) KHÔNG viết foundation riêng — đã có 2 nguồn sự thật
     (CLAUDE.md + code/pytest), thêm bản thứ 3 sẽ trôi lệch khi code đổi → bug. Cầu nối:
     phần 3 trỏ tới ràng buộc ỐNG liên quan (vd pacing → NT4 timestamp).
- **Lộ trình 5 bước đã chốt:** (0) khóa danh mục ✅ → (1) ghi nhật ký+memory ✅ (entry này)
  → (2) viết foundation theo ĐỢT 2–3 file, user duyệt từng file; **đợt 1: pacing → hình thở
  → mood&tone**; nguồn = GHI_CHEP_GOC + rút lý thuyết `FOUNDATION.md` cũ (kho quarry, không
  xóa) → (3) nối vào NÃO = L2b sâu đọc foundation thay prompt cứng, kiểm trên video thật →
  (4) Phase B: GOM MỌI PHẦN 5 thành spec schema tag GLM TRƯỚC khi tag (tag lại = rất đắt
  token, PRD §9.1) → xây ống nạp/tách cảnh/tag/thống kê per-niche.
- **Verify:** không có code → không pytest. Cổng kiểm: user chốt 4 câu hỏi (vị trí các mục
  gộp · phần 3 "dự kiến" · phạm vi ủy quyền · đợt 1) — 2026-07-02.
- **Còn ngỏ / điểm treo mang theo:** (1) mức dB ducking — học DNA hoặc quyết sau (user dặn
  note); (2) schema tag GLM BẮT BUỘC có cỡ cảnh + góc máy (không có → luật shot variety
  chết); (3) lớp nghĩa 2–3 của text cần SỐ LIỆU THẬT web-grounded — phụ thuộc `enrich --web`
  qua Claude Code chưa giải (§B1); (4) số liệu hình thở theo niche (tần suất/độ dài) từ DNA.
  Memory: [[foundation-system-catalog]].
- **BỔ SUNG 2026-07-02 (user):** thêm **CỔNG DUYỆT VẬN HÀNH** — với tính năng user không chắc
  code xử lý được, Claude phải MÔ TẢ KỸ cách hệ thống sẽ chạy (phần 3 + 3b của file foundation),
  user đọc duyệt rồi MỚI code tính năng đó. Áp cho mọi mục ❌/(b) trong bảng phân rã năng lực.

---

## §F1 — Foundation đợt 1: d1-pacing (bản nháp chờ duyệt) (2026-07-02)

- **Cái gì đổi:** MỚI `foundation/d1-pacing.md` — file foundation đầu tiên theo khuôn 5 phần
  + bảng 3b phân rã năng lực. Phần 3 = mô tả vận hành DỰ KIẾN 🔸 để user duyệt.
- **Phát hiện quan trọng khi đọc code (P1):** `Beat.shot_count` được LLM quyết (prompt pass 2)
  và lưu vào project.json nhưng **KHÔNG stage nào tiêu thụ** — sourcer chọn đúng 1 footage/beat
  (`ShotPick` theo beat_id), assembler đặt 1 asset phủ nguyên beat. → "cut nhanh 0.5–1s/shot"
  của pacing hiện KHÔNG thể xảy ra. Đây là tính năng code lớn nhất rút ra từ foundation pacing.
- **Backlog code rút từ 3b (chờ user duyệt mô tả vận hành từng cái trước khi code):**
  (1) thực thi shot_count (sourcer n footage/beat + assembler chia cửa sổ); (2) pacing
  validator (thống kê độ dài shot, cảnh báo "cắt đều tăm tắp", ngưỡng từ DNA).
- **Đã có sẵn phục vụ pacing (không code lại):** luật đường sóng + độ dài beat nghịch energy
  + ranh giới ở từ có dấu câu (`director/prompts.py` pass 1+2); snap mép cắt vào lặng ±200ms
  (`cutter/silence.py`); cơ chế `breathing_after` (thuộc hình thở).
- **Verify:** cổng mắt tri thức — **d1-pacing: user ĐÃ ĐỌC VÀ DUYỆT (2026-07-02)**. Chưa code → chưa pytest.
- **d2-hinh-tho (viết tiếp cùng ngày, chờ duyệt):** phát hiện code — ô thở hiện được footage
  beat cuối KÉO DÀI phủ (`packager/coverage.py` cờ `is_breathing_tail` đã chừa sẵn, chưa ai
  dùng) → "footage đắt riêng cho ô thở" + "chuỗi nhiều footage/ô thở" là 2 tính năng chưa có.
  Mục "chuỗi nhiều footage" dùng CHUNG cơ chế chia-cửa-sổ với thực thi shot_count của pacing
  (code 1 lần dùng 2 nơi). Cảnh báo mật độ thở gộp vào pacing validator.
- **Vòng duyệt d2 (2026-07-02):** user bác 2 điểm, đã sửa: (1) KHÔNG giữ số prompt làm mặc
  định universal — số trong foundation chỉ là VÍ DỤ; độ dài thở = **quyết định 2 PHA**
  (direct đặt ý định [min–max] theo kho-footage-đắt + sức-chịu-khán-giả → source tìm hình →
  chốt số cuối) → kéo theo điều chỉnh thứ tự stage (chốt thở SAU source); số fix cứng trong
  prompt sẽ GỠ khi L2b sâu. (2) luật "hình xoàng → bỏ thở" chỉ áp TỪNG Ô — thêm **SÀN
  ≥1 ô thở/video + thang cứu hộ 3 nấc** (nới tìm → thăng vị trí dự phòng → giữ ô tốt nhất
  + cờ needs_human), validator kiểm thủng sàn. Nguyên văn user: `GHI_CHEP_GOC.md §2`.
- **b1-mood-tone (viết cùng ngày, chờ duyệt):** hiện trạng code — mood chương/beat + nhạc
  chọn theo tag mood/energy ĐÃ CÓ (`music/select.py`, tag `__mood` tên file); CHƯA có field
  tone cấp video; CHƯA có chấm mood footage. Thiết kế C2b 2 lớp rẻ-trước-đắt-sau: (1) **so
  màu NỘI BỘ đoạn** bằng histogram (code thuần, rẻ — bắt đúng 2 lỗi ví dụ user: clip lệch
  màu giữa đoạn) → đáng code sớm nhất; (2) vision GLM-4V chấm frame CHỈ cho beat mood-nhạy-
  cảm (tiết kiệm call). Chốt non-goal: tool KHÔNG color-grade, chỉ chọn footage sẵn màu hợp.
  Backlog: field tone + luật kiểm lệch tone; so màu histogram; chấm mood vision (sau phễu c5).
- **User duyệt b1-mood-tone (2026-07-02)** + **CHỐT NON-GOAL: tool KHÔNG chỉnh màu (color
  grade)** — chỉ CHỌN footage sẵn màu hợp mood; chỉnh màu = việc editor 20% cuối (đã ghi PRD §7).
- **User duyệt d2-hinh-tho bản sửa (2026-07-02) → ĐỢT 1 HOÀN TẤT (3/3 file).**

---

## §F2 — Foundation đợt 2: c5-loc-xep-hang trọng tài phễu (2026-07-02)

- **Cái gì đổi:** MỚI `foundation/c5-loc-xep-hang.md` — trọng tài duy nhất của phễu chọn
  footage; 4 nguyên tắc phễu viết thành phần 3 (duyệt file = ĐÓNG BĂNG 4 nguyên tắc);
  kiến trúc phễu 5 bước (thu → veto 2 cửa → chấm rẻ-trước-đắt-sau → sàn 3 + chọn → ghi
  kill-log); bảng trọng số khởi điểm 🔸 (nghĩa ×3 > mood ×2.5 > variety/độ dài ×1.5 >
  P7/chữ ký ×1).
- **Hiện trạng code đã tra:** sourcer chọn heuristic (local thắng · relevance · clip ≥1.2×
  beat · phạt mềm lặp P7 · lưu 3 alternates) — các heuristic này BỌC LẠI thành chiều điểm
  trong phễu, không vứt. `ranker/` package RỖNG, ghi chú sẵn "vision rank là Phase 1" →
  đúng chỗ đặt khung phễu. Veto cứng watermark đã có (`entity.py`).
- **Backlog code rút ra:** (1) khung phễu core trong `ranker/` (veto 2 cửa + trọng số +
  sàn + kill-log, chạy được ngay với chiều rẻ); (2) đầu chấm nghĩa NÃO (hiện "tin query mù",
  chưa ai kiểm kết quả tìm vs concept beat); (3) report kill-count. Đầu chấm mood/variety
  cắm sau (phụ thuộc backlog b1 + tag Phase B).
- **Verify:** cổng mắt — **user DUYỆT c5 (2026-07-02) → 4 NGUYÊN TẮC PHỄU ĐÓNG BĂNG**
  (2 veto cứng sai-nghĩa + watermark/hỏng; còn lại điểm trọng số; sàn pool 3; kill-log
  theo luật; nghĩa>mood>nhịp>đẹp. Luật meta: foundation mới KHÔNG thêm veto thứ 3 —
  muốn nâng phải sửa c5 + user duyệt). **User DUYỆT c2-an-du-veto (2026-07-02).**
- **c2-an-du-veto (đã duyệt):** MỚI `foundation/c2-an-du-veto.md` — 3 cấp độ hình ảnh +
  bất đối xứng + trần cụ thể + ngoại lệ thực thể thật. Phát hiện: prompts.py ĐÃ nhúng gần
  hết lý thuyết (central_subject, 60/30/10, specificity ceiling, "boring but correct");
  Beat đã có đủ field (`project.py:218-223`); route entity đã chạy. Thiếu DUY NHẤT: kiểm
  kết quả tìm vs concept ("tin query mù") = backlog #2 của c5, KHÔNG mở mục mới. Tiêu chí
  veto sai nghĩa giữ HẸP 3 dạng (chủ đề khác hẳn / thực thể sai / trần cụ thể ngược);
  nhạt-mà-đúng = điểm thấp, không veto; phân vân → không veto.
- **c7-shot-variety (✅ user DUYỆT bản sửa 2026-07-02 → ĐỢT 2 HOÀN TẤT 3/3):** MỚI
  `foundation/c7-shot-variety.md` — chiều điểm ×1.5,
  xét theo CHUỖI shot THẬT đã chọn (không phải chuỗi ý định) → lý do phễu tuần tự. Phát
  hiện code: ý định `shot_size` + ngữ pháp vai + cấm-3-liên-tiếp + chuỗi vắt chương ĐÃ CÓ
  (prompts/validator/runner); thư viện local ĐÃ tag shot_size (`library/vision.py` + DB)
  NHƯNG `sourcer/local.py` ĐÁNH RƠI tag khi gom ứng viên; GÓC MÁY chưa ai tag. **Sửa theo
  góp ý user (2026-07-02, nguyên văn ở GHI_CHEP_GOC §6): "cỡ cảnh quan trọng hơn" — cỡ cảnh
  = tín hiệu CHÍNH; góc máy hạ xuống phụ CHỈ-CỘNG** (có tag tin cậy → cộng nhẹ; thiếu/trùng
  → KHÔNG trừ, không bao giờ là lý do loại); schema tag GLM: cỡ cảnh BẮT BUỘC, góc TÙY CHỌN
  thử mẻ nhỏ đo tin cậy → không tin thì BỎ HẲN. Backlog nhỏ mới: nối tag shot_size từ DB
  vào dict ứng viên local (vài dòng, làm cùng khung phễu).
- **Còn ngỏ:** bàn đợt 3 (còn 12 file — đếm lại từ bảng khóa GHI_CHEP_GOC, không phải 11:
  A1–A3, B3, C1, C3, C4, C6, D3, E1, F1-text, F2-ken-burns) — Claude đề xuất thứ tự ưu
  tiên theo cái gì chặn pipeline nhiều nhất: đợt 3 = khép nhóm C (c1→c4→c3→c6) để đủ
  tiêu chí cho khung phễu c5. → **User ĐỒNG Ý thứ tự đợt 3 (2026-07-02).**

---

## §F3 — Foundation đợt 3: khép nhóm C — c1 → c4 → c3 → c6 (2026-07-02, đang chạy 🔄)

- **User duyệt thứ tự đợt 3:** c1-phan-tuyen-nguon → c4-tu-khoa-tim → c3-ngu-canh-chuoi
  → c6-footage-chu-ky. Lý do: 4 file này là 4 mảnh tiêu chí còn thiếu của khung phễu c5
  (backlog code lớn nhất) — xong nhóm C = spec phễu ĐỦ → viết mô tả vận hành khung phễu
  cho user duyệt (CỔNG DUYỆT VẬN HÀNH) → mới code.
- **c1-phan-tuyen-nguon (🔄 chờ user duyệt):** MỚI `foundation/c1-phan-tuyen-nguon.md` —
  route là quyết định ĐẦU TIÊN mỗi beat (entity/stock/local_library/graphic); với phễu c5,
  c1 = bước THU (quyết "phễu hút từ vòi nào"), KHÔNG phải luật chấm/veto. Không có nguyên
  văn user riêng (nhóm C sinh từ bàn bạc) — chưng cất từ code thật: `_SOURCING_RULES`
  trong `director/prompts.py` (4 tuyến + ví dụ Trump + luật chart bar/line/pie + layout
  full/half + ngân sách ~1 graphic/60s) và dispatch 3 nhánh `sourcer/runner.py::run_source`
  (entity cache+watermark→needs_human, KHÔNG rơi về stock; graphic render chart/nền lót;
  stock|local chung nhánh: local-first P6 + geo-gate PA2 + 3 tầng query + phạt mềm P7).
  3b: gần hết (a) đã có; bước THU của phễu = một phần backlog #1 c5, KHÔNG mở mục mới;
  (d) Phase B: tỉ lệ tuyến theo niche, kho local thật, entity lặp lại. Cạm bẫy chính:
  entity cạn cấm tự rơi về stock; chart half phải route≠graphic (bug 15/06); phân tuyến
  không được thành veto thứ 3.
- **User sửa bản nháp c1 (2026-07-02, nguyên văn ở GHI_CHEP_GOC §8):** "stock = tuyến mặc
  định" là LOGIC PROJECT CŨ. Project này: tải rất nhiều project (~100 ban đầu), hệ thống
  học + cắt footage từ đó (tag vision) → **local_library = tuyến CHÍNH, stock = BỔ TRỢ**;
  đa niche (space, deepsea, travel), không phải niche nghỉ hưu. → Đã sửa c1 (bảng tuyến,
  yếu tố kho, 3b thêm dòng "đảo mặc định local-first khi L2b sâu", cạm bẫy "bê logic cũ");
  memory mới [[footage-source-local-first]].
- **c1 DUYỆT (2026-07-02, bản sửa local-first).** Foundation done: 7/18.
- **c4-tu-khoa-tim (🔄 chờ user duyệt):** MỚI `foundation/c4-tu-khoa-tim.md` — query =
  BẢN DỊCH visual_concept sang ngôn ngữ của TỪNG kho (local = vocabulary tag GLM;
  Pexels = keyword matcher ≤4 từ) và chỉ là PHỎNG ĐOÁN — phễu chấm ứng viên thật, cấm
  tin query mù. 3 tầng specific→broad→thematic = thang nới NGHĨA (càng tụt càng nhạt,
  không được sai — bất đối xứng c2). Chưng cất từ code thật: `_QUERY_RULES` (prompts.py
  195–207), `pexels.py::search_tiered` (ngưỡng 5/tầng, cache SQLite, xoay key 429,
  landscape ~1080p), `local.py::find_local_candidates` (CHỈ tầng specific — bug 20/06
  sai địa danh; geo-gate PA2), `db.search_assets` (LIKE AND-match 5 trường). 3b: KHÔNG
  mở mục code mới — việc (b) duy nhất "query local theo controlled vocabulary của schema
  tag" thuộc gói chốt schema tag GLM (điểm treo) + mô tả vận hành phễu; nâng cấp engine
  match chỉ khi số liệu Phase B cho thấy LIKE trượt nhiều. Cạm bẫy chính: tin query mù;
  cho local match tầng generic để "tăng local-hit" (chỉ được nới qua vocabulary tag);
  sinh query cứu beat cạn (cạn → needs_human).
- **c4 DUYỆT (2026-07-03).** Foundation done: 8/18.
- **c3-ngu-canh-chuoi (🔄 chờ user duyệt):** MỚI `foundation/c3-ngu-canh-chuoi.md` —
  hiệu ứng Kuleshov: nghĩa một shot do HÀNG XÓM quyết → đầu chấm nghĩa phải nhìn cửa sổ
  vài beat, không chấm câu trong chân không. c3 KHÔNG thêm veto (luật meta c5 — chỉ 2
  veto); nó tinh chiều khớp nghĩa (×3.0) + variety (×1.5) bằng ngữ cảnh chuỗi. Làn riêng
  vs c7 (c7 lo lặp CỠ CẢNH; c3 lo lặp/lệch NGHĨA). Giải pháp RẺ chốt trong file: ngữ cảnh
  XUÔI lo ở DIRECT (nơi thấy cả script — `_DIRECTOR_ROLE` Kuleshov + central_subject
  `_CONTEXT_COHERENCE` + motif pass 1 đã chạy); ngữ cảnh LÙI 1 beat lo lúc chọn (mở rộng
  P7 dedup từ "trùng file" sang "gần-trùng-cảnh" + cộng nối-mạch). KHÔNG phá thế tuần tự
  của phễu (c5 đóng băng) → không tối ưu toàn chuỗi. 3b: toàn bộ (b) là THUỘC TÍNH của
  đầu chấm nghĩa (backlog #2 c5) — thêm đầu vào "footage beat N−1" + cờ ranh-giới-chương,
  KHÔNG mở mục mới. Cạm bẫy: biến ngữ cảnh chuỗi thành veto thứ 3 (cấm); phạt "khựng" ở
  ranh giới chương (chỉ phạt trong lòng chương); gánh context XUÔI vào phễu tuần tự.
- **c3 DUYỆT (2026-07-03).** Foundation done: 9/18.
- **⚠ User dặn khi duyệt c3 (LƯU Ý XUYÊN SUỐT — memory [[filter-overload-guard]]):** "nếu
  các yêu cầu, chiến lược chọn footage chồng chéo nhau mà rắc rối, có thể làm AI loạn và
  chọn sai, bỏ sót footage cần. quá nhiều bộ lọc có thể dẫn đến AI loại đi nhiều footage
  quan trọng." → Chính là lý do c5 đóng băng: chỉ 2 veto, mọi tiêu chí khác = ĐIỂM (rank,
  không loại), sàn pool 3 + tự hạ cấp, kill-log bắt over-filter. Foundation mới mặc định
  đóng góp là chiều ĐIỂM, KHÔNG đẻ cửa loại; tiêu chí GỘP vào 1 điểm/beat, không nhân thành
  nhiều cổng nối tiếp. Mô tả vận hành phễu phải nêu rõ tách FILTER (2 veto) khỏi RANK.
- **c6-footage-chu-ky (🔄 chờ user duyệt — file CUỐI nhóm C):** MỚI `foundation/c6-footage-chu-ky.md`
  — chữ ký = bản sắc kênh xuyên nhiều video; đóng góp phễu = chiều điểm THẤP NHẤT (×1.0,
  ngang P7) + cơ chế TIÊM (không phải lọc). Là minh chứng luật filter-overload: chữ ký chỉ
  CỘNG + TIÊM-SÀN (hook ≥1 shot chữ ký NẾU kho có — họ "sàn" với hình thở), KHÔNG có cửa
  loại "thiếu chữ ký". 3 lớp: signature/ (folder có sẵn, geo luôn qua) · audience_bias
  (ô niche_profile.yaml — ⚠ CÓ Ô NHƯNG CHƯA NỐI, đang TODO placeholder, sourcer chưa đọc) ·
  motif (pass 1, thuộc c3). Phân biệt hàng xóm: c1=nguồn, c3=motif nối mạch 1 video, c6=bản
  sắc xuyên video. 3b: điểm chữ ký + tiêm hook + nối audience_bias đều cắm khung phễu c5,
  KHÔNG mục mới; (d) Phase B mới có bộ chữ ký thật để điền signature/+audience_bias, trước
  đó chạy "no-op êm". Cạm bẫy #1: biến chữ ký thành bộ lọc (đúng cảnh báo user).
- **c6 VIẾT LẠI (2026-07-03) — user chỉnh định nghĩa:** bản đầu tôi hiểu chữ ký = "bản sắc
  riêng của KÊNH" (branding). User sửa: **chữ ký NICHE = loại footage video ĐỐI THỦ dùng
  NHIỀU → chứng tỏ khán giả thích xem → YouTube index làm siêu dữ liệu niche.** Nguồn: project
  editor thật (thường 10 phút đầu) + video viral tải về → đưa vào CapCut tách cảnh — chính
  là ~100 project của kho local ([[footage-source-local-first]]). Cách phân tích đã bàn
  (tách cảnh → tag → ĐẾM TẦN SUẤT) = cách rút signature. Hệ quả viết vào file: (1) chữ ký
  là số ĐẾM ĐƯỢC, data-driven — cạm bẫy mới "tự nghĩ ra chữ ký thay vì rút từ dữ liệu";
  (2) kho local vốn đã nghiêng chữ ký từ gốc → route local-first tự mang chữ ký vào, càng
  không cần cưỡng chế bằng cửa loại; (3) ở beat CHÊM (nghĩa lỏng) chữ ký tự nhiên thành
  tiêu chí dẫn, ở beat NEO vẫn dưới nghĩa/mood/nhịp. Cơ chế phễu GIỮ NGUYÊN: điểm + tiêm-sàn
  hook, không lọc. 🔄 chờ duyệt bản sửa.
- **c6 sửa lần 2 (2026-07-03) — user lo AI ưu tiên chữ ký tràn lan:** câu mở "tập loại
  footage LẶP LẠI NHIỀU NHẤT + ba lý do quan trọng" dễ dạy AI chỉ ưu tiên chọn loại đối
  thủ hay dùng → BỎ. Thay bằng khung ⚠ "Giới hạn vai trò": chữ ký chỉ có 2 chỗ đứng hẹp
  (tiêm-sàn HOOK + SLOT CHÊM); tần suất chỉ dùng OFFLINE Phase B để nhận diện cái gì vào
  signature/, KHÔNG phải luật runtime "lặp nhiều = chọn nhiều". Sửa luôn hàng tần suất ở
  Phần 2 + thêm cạm bẫy "Ưu tiên chữ ký tràn lan": thân bài/beat neo → nghĩa/mood/nhịp
  dẫn, chữ ký không có tiếng nói.
- **c6 sửa lần 3 (2026-07-03) — user yêu cầu ĐƠN GIẢN HÓA:** "logic quá nhiều dễ làm AI
  loạn... không cần chấm điểm nhiều bước cầu kỳ" → VIẾT LẠI GỌN: bỏ hẳn chiều điểm chữ ký
  ×1.0, bỏ 3 lớp, bỏ nối audience_bias (ô trong niche_profile.yaml vẫn nằm đó nhưng c6
  KHÔNG dùng nữa). Còn **đúng 1 luật**: beat HOOK hoặc SLOT CHÊM → gom ứng viên từ
  `signature/` TRƯỚC, có hàng hợp nghĩa thì dùng, không có thì gom bình thường. Không điểm,
  không lọc, veto nghĩa c2 vẫn áp. 3b co còn 4 dòng — (b) duy nhất: vài dòng ưu tiên folder
  signature/ khi gom local cho hook/chêm. Hệ quả cho khung phễu c5: BỚT 1 chiều điểm
  (chữ ký ×1.0 xóa khỏi bảng trọng số dự kiến).
- **c6 DUYỆT (2026-07-03, bản gọn-1-luật) → NHÓM C XONG.** Foundation done: 10/18. Spec
  phễu ĐỦ (c5 khung + c1 nguồn + c4 query + c2 veto + c3 chuỗi + c7 variety + c6 chữ ký).
- **F4 mở (2026-07-03):** viết `MO_TA_VAN_HANH_PHEU_C5.md` (CỔNG DUYỆT VẬN HÀNH) — phễu
  4 bước/beat: B1 THU (local trước + luật c6 hook/chêm gom signature/ trước + Pexels bù)
  → B2 LỌC đúng 2 cửa (hỏng kỹ thuật máy lọc; sai nghĩa nghiêm trọng do NÃO đánh nhãn
  nhưng chấm chung B3, không call riêng) → B3 CHẤM: NÃO **đúng 1 call/beat** (input có
  footage beat N−1 + cờ mở chương — luật c3; output verdict + điểm nghĩa/mood + lý do 1
  câu, Pydantic) rồi máy cộng điểm nhẹ (variety/độ dài/P7) thành 1 ĐIỂM TỔNG, cộng một
  phát không vòng lặp → B4 CHỌN top-1 + sàn 3 tự nới + needs_human mềm. Kill-log % chết
  theo cửa. Đợt này KHÔNG làm: controlled vocabulary, shot_count, audience_bias, mood C2b,
  sàn hình thở. Thành công = pytest (veto 3 dạng, sàn nới, điểm máy không lật nghĩa,
  kill-log) + chạy 1 video mẫu + cổng mắt. **User DUYỆT mô tả 2026-07-03** → F5 mở: code
  theo ĐÚNG mô tả trong `MO_TA_VAN_HANH_PHEU_C5.md` (nguồn sự thật thiết kế phễu — đọc
  file đó trước khi code), milestone 1 = `ranker/` + pytest, milestone 2 = nối sourcer,
  mỗi milestone báo cáo + chờ user xác nhận (P4, không nhảy cóc).

---

## §F5-M1 — Code khung phễu c5, milestone 1: module `ranker/` (2026-07-03)

- **Cái gì đổi:** MỚI 3 file trong `autoedit/ranker/` (trước đó là package rỗng chừa sẵn):
  - `schema.py` — Pydantic output NÃO (`CandidateVerdict`: id/verdict/veto_type/diem_nghia/
    diem_mood/ly_do; `BeatRankResponse`) + kết quả phễu (`BeatRankResult`: chosen + ranked +
    kill_log + warnings + tokens). `SERIOUS_VETO_TYPES` = đúng 3 dạng c2, đóng băng.
  - `prompts.py` — `RANK_SYSTEM` (luật veto hẹp 3 dạng, phân vân KHÔNG veto, chấm nghĩa theo
    mạch c3 + tha ranh giới chương, ly_do 1 câu tiếng Việt) + `build_rank_prompt` (beat +
    central_subject + footage beat N−1 + cờ mở chương + danh sách ứng viên).
  - `funnel.py` — `rank_beat()`: B2 cửa kỹ thuật (watermark flag + video ngắn <0.5× beat =
    cần slow-mo quá 2×; ảnh không duration LUÔN qua) → B3 NÃO đúng 1 call (protocol
    `RankBrain` = `DirectorClient.complete`, `ClaudeCodeDirectorClient` cắm thẳng; NÃO bỏ
    sót ứng viên → điểm trung tính 5/5 + warning, KHÔNG loại) + điểm máy cộng 1 phát
    (variety c7 ±0.5, thiếu tag = 0 không trừ · đủ-dài ≥1.2× +0.5 · P7 chưa-dùng +0.5) →
    B4 sàn 3 tự nới (veto ngoài 3 dạng trả lại với −100 → luôn xếp sau hàng ok) + chọn
    top-1, pool trống → needs_human mềm. Kill-log 5 số/beat: thu/hong_ky_thuat/veto_nghia/
    tra_lai_san/con_lai.
- **Quyết định kỹ thuật đáng nhớ:**
  1. **Bất biến "điểm máy không lật nghĩa" khóa bằng hằng số:** `MACHINE_MAX_SPREAD` (2.0)
     < `NGHIA_W` (3.0 = chênh 1 điểm nghĩa) + pytest gác — sau này chỉnh trọng số mà phá
     bất biến là test đỏ ngay.
  2. Cửa "quá ngắn" định nghĩa theo assembler thật: assembler cứu clip ngắn bằng slow-mo
     (`speed = avail/want`), nên chỉ giết ca cần slow-mo quá 2× (dur < 0.5× beat).
  3. Sort ổn định theo điểm giảm dần → hòa điểm giữ nguyên thứ tự relevance của bước THU.
- **Verify:** `tests/test_ranker.py` **15/15** phủ đúng tiêu chí §5 mô tả vận hành: veto
  3 dạng bị loại hẳn + all-veto-serious → needs_human · sàn 3 nới đúng lúc (không nới khi
  pool đủ; all-veto-thường → chọn best demoted + cảnh báo soát tay) · điểm máy không lật
  nghĩa (case cực đoan: nghĩa 8 điểm-máy-tệ-nhất vẫn thắng nghĩa 7 điểm-máy-full) · cửa kỹ
  thuật + kill-log đếm đúng · NÃO đúng 1 call/beat + usage log · bỏ-sót-trung-tính · ranked
  sorted + ly_do nổi lên. **Full suite 167/167** (152 cũ không vỡ). Chưa cổng mắt (module
  chưa nối pipeline — cổng mắt thuộc milestone 2).
- **Còn ngỏ (milestone 2 — nối sourcer, CHỜ USER XÁC NHẬN M1 trước):** (1) `_source_stock`
  gọi `rank_beat` thay chọn-thô (giữ 4.7 download-hỏng-thử-tiếp: materialize theo thứ tự
  ranked); (2) luật c6: beat HOOK/CHÊM gom `signature/` trước; (3) nối tag `shot_size` từ
  DB local vào dict ứng viên (c7 — local.py đang đánh rơi); (4) trích `central_subject` từ
  `project.outline` + prev_pick_note/chapter_open khi lặp beat; (5) ghi kill-log tổng vào
  project.json + report "% chết theo cửa"; (6) chạy thật 1 video mẫu + cổng mắt.

---

## §F5-M2 — Nối phễu c5 vào sourcer + CLI + report (2026-07-03)

- **User xác nhận M1 (2026-07-03)** + yêu cầu bỏ luật commit git trong CLAUDE.md (chưa muốn
  dùng git — đã sửa P4, mốc khôi phục = nhật ký này, KHÔNG đề xuất git init lại).
- **Cái gì đổi (6 chỗ chạm, đúng mô tả vận hành):**
  - `library/db.py` +`signature_assets()` — asset `category='signature'` của niche (c6).
  - `sourcer/local.py` — ứng viên local MANG THEO tag `shot_size`/`mood` từ DB (fix bug
    đánh-rơi-tag ghi ở foundation c7); +`find_signature_candidates()` (chỉ gom khi
    hook/chêm, file phải còn tồn tại).
  - `sourcer/runner.py` — `run_source(..., brain=None)`: có brain → `_pick_by_funnel()`
    (B1 THU: signature-first cho HOOK/CHÊM + local + Pexels, khử trùng; gọi `rank_beat`;
    tải theo THỨ TỰ ĐIỂM, giữ 4.7 tải-hỏng-thử-tiếp; note = ly_do NÃO; mạch c3: cập nhật
    prev_pick_note/prev_shot_size cho beat sau, route entity/graphic cũng cập nhật);
    không brain → heuristic Phase 0 NGUYÊN VẸN (test cũ + đường thoát --no-rank).
    Cuối stage: `project.rank_log` (dump BeatRankResult/beat) + StageRecord RANK ghi
    kill-log tổng "% chết theo cửa" + CostEntry stage="rank" (token NÃO, usd=0 subscription).
  - `project.py` — +field `rank_log: list[dict]` (NT1; reset mỗi lần re-run source).
  - `cli.py::source` — `--rank/--no-rank` (mặc định BẬT) + `--rank-model`; dựng
    `ClaudeCodeDirectorClient` làm brain (guard OptionInfo khi `run()` gọi trực tiếp —
    bài học bug B2); in kill-log tổng sau khi xong.
  - `report/runner.py` — bảng beat +cột "Vì sao chọn (NÃO)"; +bảng "Phễu chọn footage
    (kill-log)" per-beat + hàng tổng + chú thích luật nới-cửa.
- **Verify:** +6 test tích hợp trong `test_sourcer.py` (FakeRankBrain đọc asset_key từ
  prompt): chọn theo điểm NÃO không theo thứ tự + rank_log/kill-log/cost ghi sổ · veto
  nghiêm trọng rơi xuống ứng viên kế + all-veto → needs_human · tải hỏng lấy điểm kế
  (4.7 giữ) · hook gom signature ĐỨNG ĐẦU prompt + central_subject + beat thường KHÔNG
  gom + mạch c3 (prompt beat sau mang footage beat trước + cờ mở chương) · slot chêm gom
  signature · local mang shot_size/mood. **Full suite 173/173** (167 cũ không vỡ).
- **Chạy thật (hook Ai Cập `vietnam-hook-ai-cap-20260701-110429`, re-source + assemble +
  report):** 17/17 beat ok — 5 beat stock qua phễu (12 entity route riêng). Kill-log tổng:
  thu 96 ứng viên · chết kỹ thuật 0 · veto nghĩa 9 (9%) · trả sàn 0. NÃO ~75s/call, ly_do
  tiếng Việt đọc hiểu ngay (vd b9: "Kim tự tháp Giza Necropolis — 'Necropolis' khớp trực
  tiếp chủ đề hầm mộ chương mới"). Draft MỚI (NT5): `VIETNAM_HOOK_AI_CAP_20260701_110429_V2`.
  report.html có cột "Vì sao chọn (NÃO)" + bảng kill-log. ⚠ vận hành: 17 beat ≈ >10 phút
  → chạy `source` từ Claude Code phải để background/detached (trần Bash tool 10 phút).
- **Còn ngỏ:** (1) **CỔNG MẮT user** — mở draft `_V2` + report.html, so footage phễu chọn
  vs bản chọn-thô cũ → F5 chỉ ĐẠT khi user duyệt; (2) beat 15 concept "close-up bàn chân
  bộ hành" pool không có close-up thật → NÃO lấy expressway "hợp ngữ cảnh nhất" — hành vi
  đúng thiết kế (chọn tốt nhất trong pool) nhưng đáng xem ở cổng mắt.

---

## §F5-M3 — Giảm ảnh: Lớp 1 (định tuyến video-first) + Lớp 2 (sàn phân giải) (2026-07-03)

- **Bối cảnh (user phát hiện qua cổng mắt V2):** video Ai Cập ra 12/17 footage là ẢNH, rất
  mờ. Điều tra cơ chế: KHÔNG phải lỗi phễu — phễu chỉ chạm 5 beat stock. 12 beat kia bị
  **đạo diễn định tuyến `entity`** ở stage direct (luật cũ: "google được → ảnh thật"), mà
  tuyến entity **chỉ tải ẢNH** (Serper/CSE Images, không có đường video). Serper KHÔNG lọc
  size → trả cả ảnh 250×187; tuyến entity KHÔNG có sàn phân giải. Đo thật: 10/12 ảnh <1280px
  (nhỏ nhất 250×187 → phóng 1080p ×5.7 = nát). User: "rất ít khi dùng ảnh — hạn chế tối đa".
- **Chốt với user:** làm **Lớp 1 + Lớp 2** trước (Lớp 3 "entity tìm cả video" để sau).
- **Lớp 1 — SỬA LUẬT ĐỊNH TUYẾN** (`director/prompts.py::_SOURCING_RULES`): thêm nguyên tắc
  **DEFAULT TO VIDEO / video-first**; entity thu hẹp còn ĐÚNG 3 ca "video không thể thật":
  người-cụ-thể-cần-mặt · sự-kiện/văn-bản-có-ngày · hiện-vật-duy-nhất-phải-thấy-đúng-bản.
  **Địa danh/thành phố/landmark/cảnh = KHÔNG BAO GIỜ lý do dùng entity** → route stock video
  + specificity ceiling (cận cảnh giấu bối cảnh / concept generic-mà-đúng). Giữ ví dụ Trump
  (chương trình visa → metaphor lừa dối → entity) NHƯNG thêm phản-ví-dụ "kim tự tháp/khu ổ
  chuột = ĐỊA DANH → stock video, không ảnh". Test phân biệt: "video đại diện có LỪA DỐI
  khán giả không, hay chỉ generic?" — generic-mà-đúng luôn chấp nhận (bất đối xứng WRONG/BLAND).
- **Lớp 2 — SÀN PHÂN GIẢI ảnh** (`sourcer/entity.py`): hằng `MIN_IMAGE_WIDTH=1280` (ảnh hẹp
  hơn = "hỏng kỹ thuật", CÙNG HỌ watermark/quá-ngắn — KHÔNG phải veto nghĩa thứ 3, không phá
  c5). 3 tầng: (1) **metadata** — Serper trả sẵn `imageWidth`, CSE trả `image.width` →
  `filter_and_rank_images` loại ảnh <sàn TRƯỚC khi tải (rẻ) + xếp ảnh TO hơn lên trước (nét
  hơn); (2) **backstop sau-tải** — `image_width()` (Pillow, fail-open nếu đo lỗi) trong
  `_download_image`: metadata thiếu/sai → đo pixel thật, mờ thì raise → caller thử ảnh khác
  (tái dùng đúng đường "thử ảnh kế" của bug HTML 19/06); (3) **cache** — `_source_entity` lọc
  ảnh cache cũ mờ. Gộp CSE về dùng chung `filter_and_rank_images` (bớt lặp). Chú ý cửa "file
  <10KB" đứng TRƯỚC cửa phân giải: ảnh mờ mà nhẹ-byte bị loại sớm như "hỏng"; ảnh thật
  250px/13KB thì qua 10KB → cửa phân giải bắt đúng.
- **Verify:** +5 pytest (`test_sourcer.py`): `image_width` đo đúng + fail-open · filter loại
  <sàn + ưu tiên ảnh to + giữ khi width=0 · `_download_image` backstop raise "phân giải thấp"
  (ảnh nhiễu >10KB, 600px) + ảnh 2000px qua · Serper lọc theo `imageWidth` ở metadata. **Full
  suite 178/178.** Lớp 1 là prompt → không pytest, verify bằng re-run video thật (đo route).
- **KẾT QUẢ ĐO THẬT (re-run video Ai Cập, 2026-07-03):** re-direct → **`sourcing_route:
  {'stock': 17}`** — TẤT CẢ 17 beat lật sang video, **0 entity** (trước: 12 ảnh). Đạo diễn
  đẩy toàn bộ địa danh Ai Cập (Cairo, Al-Qarafa, Garbage City) + cả xác ướp Saqqara sang
  stock video + specificity ceiling (vd xác ướp mèo → "close-up linen-wrapped cat mummies";
  bia mộ → "extreme close-up ancient weathered stone"). re-source qua phễu: **17/17 video
  Pexels, 0 ảnh** (kill-log: thu 433 ứng viên, chết kỹ thuật 0, veto nghĩa 44=10%, sàn 0).
  Draft mới `..._V3`. Vì 0 beat entity nên Lớp 2 (sàn phân giải) chưa bị kích hoạt lần này —
  nó là lưới an toàn cho video tương lai CÓ beat entity thật (người/sự kiện).
  ⚠ dọn dẹp: 12 .jpg lần entity cũ còn nằm rác trong `assets/` (không beat nào tham chiếu) —
  file mồ côi, có thể xóa tay; không ảnh hưởng draft.
- **Còn ngỏ:** (1) **CỔNG MẮT user** — mở draft `..._V3` + report.html, xác nhận footage
  video hợp lý (đặc biệt beat xác ướp/hiện vật giờ là video đại diện thay ảnh); (2) Lớp 3
  (entity tìm cả video) CHƯA làm — Lớp 1+2 đã giải quyết ca này, để dành khi gặp video thật
  cần trộn ảnh-người + video; (3) `MIN_IMAGE_WIDTH=1280` số khởi điểm, chỉnh theo cổng mắt.

---

## §F6 — shot_count: nhiều footage/beat (2026-07-03)

- **Bối cảnh:** F5 xong (cổng mắt V3 đạt), user chọn milestone kế = thực thi `shot_count`
  (khe pacing lớn nhất d1: `Beat.shot_count` LLM quyết nhưng KHÔNG stage nào đọc → beat 6s
  luôn là 1 hình giữ 6s, không cắt nhanh được). Viết `MO_TA_VAN_HANH_SHOT_COUNT.md` (CỔNG
  DUYỆT VẬN HÀNH) → **user DUYỆT** → code.
- **Cái gì đổi (3 chỗ chạm + schema, đúng mô tả):**
  - `project.py`: +`ExtraShot` (asset_path/key/source/note) + `ShotPick.extra_shots` (shot
    2..N; rỗng = 1 shot — preserve-by-default, mọi chỗ đọc `asset_path` = shot 1 chạy y cũ).
  - `packager/coverage.py`: +`MIN_SHOT_DUR=0.7` + `split_window(start,end,n)` — chia cửa sổ
    n khoảng ĐỀU, mép con dùng CHUNG float → `round(mép*SEC)` khớp → không SegmentOverlap
    (tái dùng bài học [[assemble-segment-overlap-rounding]]).
  - `sourcer/runner.py`: `_shot_count_target(beat)` = min(shot_count LLM, floor(dur/sàn),
    pool) — beat có info-card/chart-half → ép 1 (layout riêng). `_pick_by_funnel` lấy TOP-N
    clip khác nhau từ `ranked` (1 call NÃO như cũ, chỉ lấy nhiều clip hơn), clip chính =
    ShotPick + phần còn lại = extra_shots; cả N vào used_in_video (P7); mạch c3 dùng clip
    CUỐI làm hàng xóm N−1; giữ 4.7 tải-hỏng-thử-tiếp.
  - `packager/assembler.py`: tách `_place_video_l1()` (đặt 1 clip vào 1 khoảng, giữ nguyên
    normalize + slow-mo + full-frame); vòng video_l1 gom `[chính]+extra_shots` → `split_window`
    → đặt từng clip. Bất biến phủ kín KHÔNG đổi (tổng N khoảng = cửa sổ beat cũ).
  - `report/runner.py`: cột footage ghi "N shot" khi >1.
- **Phạm vi (hẹp, tránh phình):** CHỈ route stock/local (đường phễu); entity/graphic/info-card
  giữ 1 shot. KHÔNG làm đợt này: chuỗi nhiều-footage cho ô-thở (d2, dùng chung split_window,
  cắm sau) · khoảng con dài-ngắn khác nhau · chấm NÃO riêng từng shot con · pacing validator.
- **Verify:** +9 pytest — `split_window` (n=1 nguyên, chia đều liền khít, mốc lẻ khớp
  microsecond) · `_shot_count_target` (kẹp sàn/pool/shot_count, info-card→1) · funnel lấy N
  clip khác nhau + vào used_in_video · pool cạn kẹp N · shot_count=1 không extras · assembler
  đặt N segment tiling cửa sổ 6s không hở/đè, 3 material khác nhau. **Full suite 187/187.**
- **Chạy thật:** project Ai Cập có 2 beat `shot_count=2` (b9 sa mạc 2.5s, b11 xác ướp mèo
  1.9s). Re-source: log đúng "beat 9/11: 2 shot nối tiếp". **BUG PHÁT HIỆN QUA CHẠY THẬT:**
  2 clip cùng beat có CÙNG TÊN FILE (`_materialize` đặt tên theo `visual_concept` — giống
  nhau mọi clip cùng beat) → clip 2 GHI ĐÈ clip 1, cả 2 ShotPick trỏ 1 file. **Fix:** thêm
  hash asset_key vào tên file `b009_<slug>_<uid6>.mp4`. pytest cũ lọt vì chỉ assert file
  tồn tại + key khác, KHÔNG assert asset_path khác → thêm assert `len(set(paths))==N`.
  Full suite 187/187 sau fix. Re-source lần cuối (tên phân biệt) đang chạy → assemble → cổng mắt.
- **Còn ngỏ:** (1) CỔNG MẮT draft multi-shot (b9/b11 phải là 2 clip KHÁC nhau nối tiếp);
  (2) LLM hiện dùng shot_count RẤT ít (2/17 beat)
  — nếu muốn nhịp cắt nhanh hơn ở đoạn năng lượng cao thì tinh prompt pass 2 sau (không thuộc
  đợt này); (3) `MIN_SHOT_DUR=0.7` chỉnh theo cổng mắt.

---

## §F7 — Foundation đợt CUỐI: 8 file trong 1 đợt (2026-07-04 — user DUYỆT cả 8 ✅, bộ 18/18 KHÓA)

- **User quyết:** V5 đạt → "làm nốt foundation quan trọng, làm hết trong 1 lần rồi tính
  tiếp" — bỏ nhịp 2-3 file/đợt, viết trọn 8 file còn lại (a1, a2, a3, b3, d3, e1, f1, f2).
  Nguồn: `GHI_CHEP_GOC.md` (e1, f1 có nguyên văn user; §3 ducking) + quarry
  `⟪AE⟫..\FOUNDATION.md` (nhóm A/B3/D3/F2 không có nguyên văn — chưng cất, ghi rõ nguồn
  trong từng file) + soi code thật (validator/music/sfx/overlay/silence/motifs).
- **8 file mới (đúng khuôn 5 phần + 3b; xuyên suốt [[filter-overload-guard]] — KHÔNG file
  nào đẻ cửa loại mới, KHÔNG thêm chiều điểm nào vào phễu c5):**
  - `a1-chia-beat-chuong` — kỹ năng NÃO đầu pipeline; 2 pass + hậu xử lý máy ĐÃ đủ,
    backlog 0 mục; giá trị = "ruột" L2b sâu + chỗ treo số DNA (độ dài beat/niche).
  - `a2-chuc-nang-doan` — vai HOOK/setup/payoff/chêm quyết phân biệt đối xử; vai đang
    chạy NGẦM qua vị trí+prompt; CHỦ ĐỘNG không đẻ field `role` (tránh phình); backlog 0.
  - `a3-open-loop-callback` — loop thuộc script (tool chỉ nhận diện, không spoil, dồn đồ
    đắt lúc đóng); motif đã có mức Ý (pass 1); callback lặp-footage = ngoại lệ P7 CÓ ĐÁNH
    DẤU — treo chủ đích, P7 giữ nguyên; backlog 0 (2 mục (b) đều treo).
  - `b3-pattern-interrupt` — interrupt = NHỊP PHÂN BỔ công cụ đã có, không phải hiệu ứng
    mới; vũ khí đã đủ (overlay/chart/kinetic/thở/đổi-nhạc/multi-shot); thiếu duy nhất cái
    nhìn tổng → phép quét trống->60s/chen<5s GỘP vào pacing validator (backlog d1), không
    mở mục riêng.
  - `d3-loai-cat-transition` — foundation "ĐỪNG LÀM": 100% hard cut hiện tại là ĐÚNG luật
    95%; cut-on-word + snap-lặng + cutaway + montage đã có; J/L-cut + whip/blur + match
    cut đều treo chờ DNA chứng minh cần; backlog 0.
  - `e1-sound-design-nhac` — TRÙM E, nguyên văn user; nhạc-theo-chương + SFX-bám-sự-kiện
    + im-lặng-chiến-lược đã có; **backlog 2 mục MỚI (duy nhất cả đợt): (1) ducking
    keyframe** (voice→nhạc nép -12…-18dB 🔸, thở→nở, ramp mép — điểm treo dB giữ nguyên,
    cần mô tả vận hành duyệt trước khi code) **· (2) ambient-cho-hình-thở** (sau Phase B,
    cần tag loại-cảnh + kho ambient — thêm 1 trường vào spec tag GLM).
  - `f1-text-typo-motion-graphics` — TRÙM F1+F3, nguyên văn user (lớp nghĩa 2–3); lớp 1
    (ghim voice) đã đủ: 7 kind + style map + kinetic + card/chart + density validators;
    lớp 2–3 KHÔNG mở mục code — đi qua ống enrich supplementary + cổng duyệt CÓ SẴN khi
    L2b sâu (Claude Code có web) → điểm treo §B1 tự giải ở Phase C; luật sắt "không nguồn
    → không hiện".
  - `f2-ken-burns-punch-in` — file nhỏ nhất, ưu tiên THẤP CÓ CHỦ ĐÍCH: sau video-first
    (F5) ảnh là ngoại lệ hiếm; ảnh tĩnh + sàn 1280px chạy được tới khi gặp video thật có
    beat entity; Ken Burns/punch-in đều treo (keyframe transform pycapcut — cổng duyệt
    vận hành khi mở); backlog 0.
- **Tổng hợp toàn đợt:** 18/18 foundation ĐÃ VIẾT (10 đã duyệt + 8 chờ). Backlog code mới
  CHỈ 2 mục (ducking · ambient-thở) + 1 phép quét gộp d1 — đúng tinh thần user "logic quá
  nhiều dễ làm AI loạn": phần lớn file kết luận "code đã đủ / chủ động không làm".
  Spec tag GLM Phase B cộng dồn: cỡ cảnh BẮT BUỘC (c7) · góc máy tùy chọn thử (c7) ·
  mood (b1) · **loại-cảnh cho ambient (e1, MỚI)**.
- **Verify:** viết tri thức, không code → không pytest. **Cổng mắt: user duyệt 8 file.**
- **Còn ngỏ:** sau khi 8 file duyệt → tính bước kế (ứng viên: ducking keyframe (cổng duyệt
  vận hành) · pacing validator (d1+b3) · L2b sâu đọc bộ foundation · Phase B chốt schema tag).

---

## §F8 — Ducking keyframe: mô tả vận hành (2026-07-04, chờ user duyệt 🔄)

- **User quyết:** duyệt cả 8 file F7 → "tiếp tục ducking keyframe" (backlog 1 của e1).
  Theo đúng luật e1: chạm assembler → CỔNG DUYỆT VẬN HÀNH trước khi code.
- **Khảo sát (không đoán):** (1) pycapcut CÓ SẴN `AudioSegment.add_keyframe(offset_µs,
  volume)` → `KFTypeVolume`, nội suy tuyến tính — pipeline chưa từng dùng keyframe;
  (2) lịch voice/thở lấy từ `project.segments` (timeline_start/end + breathing_after) —
  không cần dò waveform; (3) nhạc đặt theo chương trên `music`/`music2` crossfade 3s —
  ducking chèn keyframe SAU khi nhạc đặt xong, không sửa logic chọn/đặt nhạc.
- **Sản phẩm:** `MO_TA_VAN_HANH_DUCKING.md` — 4 bước vận hành; 4 tham số điểm treo 🔸
  (DUCK_VOL=0.20 giữ mức hôm nay · BREATH_VOL=0.50 ~+8dB · RAMP=0.4s · NGƯỠNG_THỞ=1.0s
  chống pumping); 2 behavior CapCut chưa chắc (mốc time_offset; keyframe×volume×fade)
  → M1 = draft test nhỏ bisect trước khi wire.
- **Cổng P4:** M1 draft test (👁 mắt) → M2 code+pytest → M3 V6 project thật (👂 tai user
  chốt tham số).
- **M1 ĐẠT (2026-07-04):** user duyệt draft test; giữa chừng user chỉnh RAMP 1s→**2.5s**
  ("fade muốn dài hơn 2 giây") → sinh `ducking-kf-test-v2` (không đè v1 — C5). 3 behavior
  chốt (memory [[capcut-volume-keyframe]]): offset keyframe từ ĐẦU CLIP · keyframe ĐÈ
  volume tĩnh (giá trị tuyệt đối) · fade/crossfade sống chung keyframe.
- **M2 XONG:** `packager/ducking.py` (hàm thuần: merge_voice_intervals nuốt nghỉ <1s
  chống pumping · build_envelope dốc CỐ ĐỊNH — thở ngắn chỉ phồng một phần · 
  segment_keyframes neo mép clip, round() µs, lùi 1ms khỏi mép cuối) + `_duck_music`
  trong assembler chạy SAU khi nhạc đặt xong (chung cả 2 nhánh --music/thư viện; clip
  trọn trong voice → 0 keyframe, volume tĩnh lo). **pytest 196/196 (9 test mới:**
  8 pure test_ducking.py + 1 assert tích hợp trong end-to-end).
- **M3 build:** draft `VIETNAM_HOOK_AI_CAP_..._V6` — ducking trên 3 clip nhạc; video này
  2 khoảng thở thật (~2s tại 6-8s → nở 0.32; ~3.5s tại 24.6-28.1s → nở 0.41 — một phần,
  đúng luật dốc cố định vì thở ngắn hơn 2×RAMP); 2 track crossfade cho cùng đường volume
  tại cùng mốc (kiểm JSON).
- **🐛 V6: USER BẮT LỖI keyframe không hiện (2026-07-04)** — bài học đắt nhất F8:
  - User click clip nhạc 1: 2 chấm tròn hóa ra là NÚM FADE 3s (3.0s/10.4s), keyframe
    KHÔNG hiển thị. Kết luận M1 "offset tính từ đầu clip" là SAI — clip đối chứng draft
    test lấy nhạc từ ĐẦU bài (source=0) nên 2 cách hiểu trùng nhau, không phân định.
  - Điều tra: quét máy tìm `KFTypeVolume` → thấy `REAL73 PROJECT` (draft người làm tay)
    → diff: schema segment GIỐNG HỆT, chỉ khác format id/string_value → ma trận v3
    (format × fade, 4 clip) → cả 4 KHÔNG hiện → format VÔ CAN.
  - Chốt thủ phạm bằng số V6: clip src=158.77s (kf 0-13s NGOÀI dải source → lờ) vs clip
    Ziv src=0 (kf trong dải). **`time_offset` = thời gian trong FILE NGUỒN.**
  - Fix 1 dòng wire: `add_keyframe(source_start + offset, vol)`. pytest 196/196. Draft
    **_V7**: kiểm JSON cả 3 clip kf nằm trong dải source. Memory
    [[capcut-volume-keyframe]] viết lại (kèm bài học thiết kế draft test: biến phân định
    phải nằm ở clip đối chứng; hỏi cổng mắt từng câu YES/NO).
  - **✅ V7 ĐẠT (user duyệt mắt+tai 2026-07-04):** chấm keyframe hiện đúng 6.0/7.0/8.0s
    trên clip 1, nghe phồng cả 2 khoảng thở. **F8 KHÉP.** 4 tham số giữ v1: DUCK_VOL=0.2,
    BREATH_VOL=0.5, RAMP=2.5s, MIN_BREATH=1.0 (hằng số đầu `packager/ducking.py` — tai
    chê lúc nào chỉnh lúc đó; số dB chuẩn chốt bằng DNA Phase B).
- **Còn ngỏ sau F8 (ứng viên bước kế — user chọn):** (1) **pacing validator** (gom
  d1 + quét gap b3 + d2); (2) **L2b sâu** — Claude Code phiên sống đọc bộ 18 foundation
  thay prompt cứng (mục tiêu lớn nhất, tự giải điểm treo §B1 lớp nghĩa 2-3); (3) **Phase B**
  chốt schema tag GLM (cỡ cảnh + mood + loại-cảnh-ambient + góc máy thử) → mở khóa kho
  local + ambient; (4) ambient-cho-hình-thở (backlog 2 của e1 — CẦN Phase B trước).

---

## §F9 — L2b sâu: mô tả vận hành (2026-07-04, chờ user duyệt 🔄)

- **User quyết:** sau F8, giao Claude chọn hướng → chọn **L2b sâu** (đúng lộ trình 5 bước
  §F0, bước 3: foundation 18/18 xong → nối vào NÃO; Phase B để sau, pacing validator chưa
  có số DNA nên để sau).
- **Khảo sát (P1, đọc code thật):** `direct` hiện = 2 pass prompt cứng (`prompts.py` ~450
  dòng) qua `cc_client` subprocess; validator battery + hậu xử lý nằm ở `runner.py` (tái
  dùng nguyên vẹn được); schema `BeatDraft/Outline` đủ, KHÔNG sửa. Skill `/dung-video`
  hiện chỉnh beat qua vòng brief → re-run direct cả video (chậm, không phẫu thuật).
- **Sản phẩm:** `MO_TA_VAN_HANH_L2B_SAU.md` — 3 mảnh: (1) lệnh mới `direct-context` xuất
  transcript đánh số `[i]word`; (2) phiên sống đọc **12/18 foundation nhóm đạo diễn**
  (a1 a2 a3 b1 b3 c1 c2 c4 d1 d2 d3 f1 — KHÔNG đọc c3/c5/c6/c7/e1/f2 vì đã code trong
  ống/phễu hoặc treo, tránh [[filter-overload-guard]]) → viết `director_draft.json` đúng
  schema cũ; (3) lệnh mới `direct-ingest` chạy nguyên battery validator + hậu xử lý cũ,
  lỗi → trả về phiên sửa (vòng retry hội thoại), pass → ghi project.json. NT4 giữ: phiên
  chỉ trả word index. Đường `direct` cũ GIỮ NGUYÊN (fallback + xương L1).
- **Cổng P4:** M1 duyệt mô tả → M2 code 2 lệnh ỐNG + pytest → M3 cập nhật skill + chạy
  thật + cổng mắt beats → M4 Pha 2 + cổng mắt draft.
- **⚠ Input test mới (user dặn 2026-07-04):** bài Ai Cập RẤT ÍT nguồn footage → video test
  từ giờ dùng folder `voice test travel` (Thụy Sĩ: `hook.mp3` + `chapter 1 Zurich.mp3` +
  `chapter 2 Bern.mp3` + `chapter 3 Lucerne.mp3` + `content english.txt`; `manifest.json`
  rỗng — không phải của autoedit). Pipeline chỉ nhận **1 file voice** (`_pick_input`) →
  khi test phải ghép 4 mp3 → 1 `voice.mp3` bằng ffmpeg concat, đúng thứ tự hook→1→2→3.
  Memory: [[test-input-travel-switzerland]].
- **RÀ CHỒNG CHÉO LOGIC (user yêu cầu 2026-07-04, "hệ thống phức tạp khó tự check"):** rà
  từng tầng quyết định (prompt/foundation → validator chặn → hậu xử lý âm thầm → phễu →
  assembler), kết quả đầy đủ ở `MO_TA_VAN_HANH_L2B_SAU.md §4b`. **4 mâu thuẫn thật:**
  (1) multi-shot chia đều CẢ Ô THỞ (coverage window beat cuối segment gồm thở + F6 split
  đều) → nhát cắt giữa im lặng, ngược d2 — bom hẹn giờ chưa nổ vì V5 không trúng ca này;
  (2) validator ÉP hook có thở nhưng `enforce_breathing_pauses` có thể ÂM THẦM xóa đúng
  thở đó (2 tầng lật nhau đúng kiểu user lo); (3) `merge_short_beats` gộp beat <1.5s
  nhưng VỨT overlay/graphic của beat ngắn không dấu vết; (4) khe hở thở 0<x<1.5s lọt
  validator (message nói cấm) + dưới ngưỡng ducking 1.0s → im lơ lửng nhạc không nở.
  Cụm ĐÃ KIỂM không mâu thuẫn: query-vs-phễu (2 lớp cùng chiều), variety 2 tầng, ducking
  ×fade×crossfade (F8), mood chương-vs-beat (vênh tiềm năng, backlog b1). **Chốt:** thêm
  gói **M0 vá nền** (3 fix nhỏ #1#3#4) + ingest xử #2 bằng lỗi-kèm-gợi-ý; thiết kế L2b sâu
  bổ sung **BẢNG RÀNG BUỘC CỨNG sinh từ hằng số code** trong `direct_context.md` — nguyên
  tắc mới: *foundation quản Ý, bảng ràng buộc quản SỐ* (cùng họ [[filter-overload-guard]]).

---

## §P5 — Luật "Rà chồng chéo & vùng ảnh hưởng" vào CLAUDE.md (2026-07-04)

- **Cái gì đổi:** `CLAUDE.md` §2 đổi "BỐN" → "NĂM NGUYÊN TẮC HÀNH ĐỘNG", thêm **P5** với
  3 luật: (1) tính năng/luật mới → mô tả vận hành BẮT BUỘC có mục "Rà chồng chéo" (liệt kê
  các tầng cùng quản thứ sắp đụng, trả lời "ngược chiều?" + "tầng nào âm thầm lật tầng
  nào?" — mẫu chuẩn `MO_TA_VAN_HANH_L2B_SAU.md §4b`); (2) sửa code/fix bug → grep MỌI
  consumer + chỗ cùng-pattern TRƯỚC khi sửa, sửa cùng hoặc ghi "còn ngỏ", không im lặng;
  (3) cổng hồi quy: mỗi fix ≥1 regression test tái hiện bug + chạy FULL suite + báo cáo
  milestone có mục "vùng ảnh hưởng đã rà".
- **Vì sao (user yêu cầu 2026-07-04, "sau này tôi không cần nhắc lại"):** đợt rà F9 tìm ra
  4 mâu thuẫn thật giữa các tầng → cần cơ chế TỰ LẶP LẠI cho mọi tính năng sau. Kèm bệnh
  "fix bug cũ sinh bug mới" do không tính hết vùng ảnh hưởng — bằng chứng lịch sử: bug B2
  (`run` gọi direct thiếu `engine` → rơi về API 401, caller bị quên), bug F6 (2 clip cùng
  beat đè tên file — consumer assumption), B3 (`int()` truncation còn anh em ở PiP/overlay
  ghi "còn ngỏ").
- **Verify:** thay đổi tài liệu, không pytest. Hiệu lực từ milestone kế (M0 của F9 sẽ là
  lần đầu áp: mỗi fix kèm regression test + mục vùng-ảnh-hưởng trong báo cáo).
- **Ghi chú:** KHÔNG tạo memory riêng cho luật này — CLAUDE.md tự nạp mỗi phiên, thêm bản
  thứ 2 sẽ trôi lệch (đúng nguyên tắc 1-nguồn-sự-thật đã dùng ở F0 cho kỹ thuật ỐNG).

---

## §F9-M0 — Vá nền 3 chồng chéo (2026-07-04, user duyệt M1 xong ✅)

- **Cái gì đổi (3 fix §4b, mỗi fix + 1 regression test tái hiện bug trước-fix):**
  1. **#1 multi-shot né ô thở** — `coverage.py::split_window` thêm tham số `tail`:
     chỉ chia đều phần THOẠI `[start, end-tail]`, shot cuối kéo dài phủ trọn ô thở
     (d2: ô thở = 1 hình giữ). `CoverWindow.is_breathing_tail` (bool) → field mới
     `breathing_dur` (giây) + property giữ tên cũ cho chỗ đọc. `assembler.py` truyền
     `tail=w.breathing_dur`. Trước fix: cửa sổ (0,7) thoại 3s + thở 4s, n=2 → cắt tại
     3.5s = GIỮA im lặng. Test: `test_split_window_tail_keeps_cuts_out_of_breathing`.
  2. **#3 merge không vứt quyết định** — `validator.py::merge_short_beats`: overlays
     cộng dồn CẢ 2 chiều (anchor vẫn trong range gộp), chiều gộp-vào-SAU giữ
     `max(breathing)` (trước fix rơi về 0); chart/card/text-sequence của beat ngắn vẫn
     rơi (host chỉ chứa 1) nhưng giờ có NOTE báo rõ, hết im lặng. Test:
     `test_merge_short_beats_keeps_overlays_and_breathing`.
  3. **#4 cấm khe thở (0,1.5)** — `check_v2_rules` siết đúng thông báo: 0 hoặc
     [1.5, 6]; thêm hằng `MIN/MAX_BREATHING_SEC` (M2 sẽ in vào bảng ràng buộc cứng
     của `direct_context.md`). Trước fix 0.8s lọt qua. Test:
     `test_v2_breathing_rejects_gap_below_min`.
- **Vùng ảnh hưởng đã rà (P5 lần đầu áp nguyên bộ):** `split_window` chỉ 1 caller thật
  (assembler:132; `tail` mặc định 0 → n=1 và caller khác giữ nguyên hành vi);
  `is_breathing_tail` không ai construct từ ngoài coverage.py, chỗ đọc chạy qua property;
  `_shot_count_target` (sourcer) đã kẹp N theo THOẠI `beat.end-beat.start` → nhất quán
  với fix #1, không sửa; shot cuối dài hơn → `_place_video_l1` tự slow-mo + warning (hành
  vi sẵn có, chủ đích); `merge_short_beats` chỉ runner:141 gọi, chạy TRƯỚC
  `enforce_breathing_pauses` → thở chuyển chỗ sai có lưới bắt; thở max cả 2 chiều là
  1 giá trị/beat nên không tạo ca "2 thở liền" mới; `check_v2_rules` 3 caller (runner
  retry cũ + ingest tương lai + test) — LLM trả (0,1.5) giờ bị retry đúng như message
  hứa; schema `breathing_after_sec` không có constraint số (validator là chỗ gác duy
  nhất, không trùng tầng).
- **Còn ngỏ (ghi công khai, không im lặng):** (a) #2 hook-thở-bị-xóa-lén xử ở **M2**
  bằng lỗi-kèm-gợi-ý tại ingest (đúng thiết kế §4b, đường cũ giữ nguyên P3); (b) merge
  beat ngắn mang chart/card: chọn BÁO-và-rơi thay vì merge (2 chart/beat không hợp lệ) —
  cực hiếm vì chart cần beat 4-8s đứng hình.
- **Verify:** FULL suite `uv run pytest -q` = **199/199 pass** (196 cũ + 3 mới), 52s.
  3 test mới đều fail trên code trước-fix (bounds chia đều/breathing rơi/0.8 lọt).

---

## §F9-M2 — 2 lệnh ỐNG cho đường phiên sống (2026-07-04 ✅)

- **Cái gì đổi:**
  1. **`autoedit/director/live.py` (module MỚI):** mảnh 1 `build/write_direct_context`
     — ghi `direct_context.md` (transcript `[i]word` tái dùng `prompts.numbered_words`,
     thời lượng thoại, brief/channel, **BẢNG RÀNG BUỘC CỨNG sinh từ hằng số code** —
     đổi hằng là bảng đổi theo, chống vênh Ý-vs-SỐ §4b); mảnh 3 `run_direct_ingest` —
     parse `director_draft.json` (wrapper `DirectorDraft` = `Outline` + `chapters[
     chapter_id, beats: BeatDraft]`, schema cũ KHÔNG sửa), chạy nguyên battery
     `beat_errors` + mới `check_breathing_placement`; lỗi → trả danh sách, **KHÔNG ghi
     gì**; pass → kẹp trần visual/chương → `drafts_to_beats` → `finalize_beats` → ghi
     `project.beats/outline` + `beats.json`, stage direct DONE ($0 API).
  2. **`validator.py`:** hàm mới `check_breathing_placement` (vá #2 §4b: thở tại chỗ
     voice không nghỉ <0.3s = LỖI kèm gap đo được + gợi ý ≤3 từ có nghỉ thật gần đó;
     CẢ CHƯƠNG không có chỗ nghỉ → trả [] hạ về hành-vi-cũ, tránh kẹt vòng sửa) + hằng
     số hóa `MAX_QUERY_WORDS=4`, `MAX_CHARTS/CARDS_PER_CHAPTER=2` (bảng ràng buộc in
     từ đây, check_v2_rules/enforce_chapter_visual_limits dùng cùng nguồn).
  3. **`runner.py`:** extract hậu xử lý thành `drafts_to_beats` + `finalize_beats` +
     public hóa `beat_errors`/`write_beats_review` — 2 đường direct DÙNG CHUNG 1 code,
     sửa 1 chỗ ăn cả 2 (chống lệch đôi tương lai). `run_direct` hành vi y nguyên.
  4. **`cli.py`:** 2 lệnh mới `direct-context` / `direct-ingest` (ingest lỗi → in
     danh sách + exit 1). Đường `direct` cũ KHÔNG đụng (P3).
- **Vùng ảnh hưởng đã rà:** `_beat_errors`/`_write_beats_review` chỉ runner dùng (grep
  toàn repo trước khi đổi tên); extract hậu xử lý — caller duy nhất là `run_direct`,
  6 test runner cũ pass nguyên xác nhận hành vi không đổi; `enforce_chapter_visual_limits`
  đổi default sang hằng (giá trị y cũ = 2); message check_v2_rules giữ nguyên chuỗi
  ("maximum is 4") — test cũ khớp; ingest KHÔNG đặt stage RUNNING trước validate (khác
  run_direct) để "lỗi → không ghi gì" đúng cam kết doc.
- **Verify:** FULL suite = **206/206 pass** (199 + 7 mới trong `test_director_live.py`),
  51s. 7 test = đúng cổng M2 doc §6: format `[i]word` + bảng từ hằng số; chặn draft hở
  coverage (không ghi gì, không beats.json); chặn chapter lệch outline; chặn schema sai;
  **chặn thở-sai-chỗ kèm gợi ý `[5]w5` rồi sửa-theo-gợi-ý → pass, hook GIỮ được thở**
  (nghịch lý #2 chết tại đây); draft sạch → beats `model_dump` **BẰNG NHAU TỪNG FIELD**
  với đường `run_direct` cũ + `cost_log` rỗng. Smoke: `--help` 2 lệnh OK.

---

## §F9-M3 — Skill đường sâu + chạy thật video travel Thụy Sĩ (2026-07-04, chờ cổng mắt 🔄)

- **Cái gì đổi:**
  1. **`.claude/skills/dung-video/SKILL.md` viết lại Pha 1 sang đường SÂU:** đọc 12
     foundation nhóm đạo diễn (a1 a2 a3 b1 b3 c1 c2 c4 d1 d2 d3 f1 — CẤM 6 file còn lại,
     [[filter-overload-guard]]) 1 lần/phiên → `direct-context` → tự đạo diễn viết
     `director_draft.json` → `direct-ingest` (vòng lỗi = hội thoại). Ghi tường minh 2 luật
     chống vênh: nhịp nhanh → shot_count 2–3 KHÔNG đẻ beat <1.5s; d2 2-pha CHƯA code —
     chỉ đặt 1 số `breathing_after_sec` tại từ voice nghỉ thật. VÒNG CHỈNH đổi: sửa ĐÚNG
     beat trong draft + ingest lại (không re-run cả video). Đường `direct` cũ ghi rõ là
     fallback.
  2. **Input travel:** `voice test travel/script.txt` (hook + ch1–3, bỏ dòng nhãn — script
     là ground truth của matcher) + `voice.mp3` = ffmpeg concat 4 mp3 (`-c copy`, cùng codec
     mp3 44.1kHz) = 337.1s. Project `autoedit/projects/script-20260704-041750`, align 860 từ
     (22 nội suy).
  3. **Chạy đối chứng cùng 1 project:** direct CŨ → `beats_old.json` (47 beat, $3.45,
     **kèm lỗi ship: 2 beat >10s chương 2 không sửa nổi sau retry, 2 cặp thở liên tiếp,
     24 overlay + 6 info-card**) → direct SÂU: phiên đọc 12 foundation + direct_context.md,
     viết draft 59 beat/6 chương → **ingest PASS VÒNG ĐẦU, 0 lỗi, $0 API** (8/8 vị trí thở
     trúng chỗ voice nghỉ thật ≥0.3s — không bị xóa lén, vá #2 chạy thật; 0 beat >10s;
     0 beat bị gộp). Chỉ 4 warning ranh-giới-từ-nội-suy (cutter snap lặng xử lý).
- **So sánh 2 bản (đặt cạnh nhau cho cổng mắt):** sâu 59 beat avg 5.2s (cũ 47 avg 6.6s,
  max 10.5s VI PHẠM); thở sâu 8 ô giãn đều ~40s (cũ 9 ô có 2 cặp dính); overlay sâu 16 +
  1 card (cũ 24 + 6 card — dày, PowerPoint-risk); level sâu 54 literal/5 associative
  (travel showcase, c2 bất đối xứng), cũ 32/12/3 metaphorical; route cả 2 100% stock;
  0 chart cả 2 (script không có cặp số so sánh — đúng, không bịa).
- **Vùng ảnh hưởng đã rà:** M3 KHÔNG đổi code Python — chỉ skill (md) + chạy pipeline;
  thứ tự chạy giữ an toàn dữ liệu: beats_old.json lưu XONG mới ingest đè beats.json;
  project.json cuối = bản sâu (đúng bản sẽ đi tiếp M4).
- **Verify:** pytest không đổi (206/206, không code mới); cổng M3 = **CỔNG MẮT — user
  duyệt beats bản sâu (`beats.json`), Claude Code KHÔNG tự báo đạt.** Đạt cổng → M4 Pha 2
  (cut→source→assemble→report) trên chính project này.

---

## §F9-M4 — Pha 2 video travel: draft CapCut từ beats đường sâu (2026-07-04 ✅ CỔNG MẮT ĐẠT — user duyệt cùng ngày, F9 đóng trọn M1→M4)

- **User duyệt cổng mắt beats M3** ("duyệt. bạn hãy tiếp tục") → chạy Pha 2 trên chính
  project `script-20260704-041750`, KHÔNG đổi code:
  1. **cut:** 8 segment voice + 7 khoảng thở chèn timeline, voice 334.1s → timeline 355.1s
     (ô thở outro sau từ cuối do assembler phủ hình, không chèn gap).
  2. **source:** 59/59 beat OK từ Pexels, **0 needs_human**. Phễu c5 khỏe: thu 1370 ứng
     viên, chết kỹ thuật 21 (1%), veto nghĩa 173 (12%), trả-lại-sàn 0.
  3. **assemble:** draft `%LOCALAPPDATA%\...\com.lveditor.draft\SCRIPT_20260704_041750`
     (tên mới NT5). 2 beat clip ngắn phải slow-mo phủ (b27 0.37x, b44 0.71x — editor nên
     swap); nhạc 6 chương đổi bài theo mood + crossfade 3s; ducking nở 0.5/nép 0.2 ramp
     2.5s; 1 info-card layer2; 16 overlay + 16 SFX.
  4. **report:** `projects/script-20260704-041750/report.html`.
- **Vùng ảnh hưởng:** không đổi code — chạy pipeline thuần; draft tên mới không đè.
- **Verify:** cổng M4 = **CỔNG MẮT draft CapCut — user mở CapCut kiểm (preview không đen,
  không đòi relink, nghe ducking/nhạc/SFX), Claude Code KHÔNG tự báo đạt.** Điểm cần user
  soi kỹ: 2 beat slow-mo (b27, b44), ô thở outro cuối video, info-card 4 ngôn ngữ (~110s).

---

## §PB1 — Phase B mở màn: spec schema tag GLM (2026-07-04, chờ user duyệt 🔄)

- **User quyết:** sau F9 đóng trọn, chọn hướng **Phase B** (bước duy nhất còn lại của lộ
  trình F0; động lực: video travel chạy 100% Pexels trong khi local-first là tuyến CHÍNH
  nhưng kho local = 0). Milestone đầu đúng F0 bước 4: chốt spec tag TRƯỚC khi tag (tag lại
  = rất đắt token, PRD §9.1).
- **Khảo sát (P1, đọc trước):** gom nguyên văn phần 5 của CẢ 18 foundation; soi code thật:
  ống M3.5 ĐÃ CÓ (`library-index` walk→tag→cache.db, skip mtime, search LIKE, signature_assets)
  nhưng tagger là **Claude haiku** (CLAUDE.md §5 chốt GLM-4.6V native); nhạc ĐÃ CÓ vocabulary
  mood ĐÓNG 19 từ (`music/library.py::MOOD`) + map synonyms từ mood chương free-text.
- **Sản phẩm:** `MO_TA_VAN_HANH_TAG_GLM.md` (CỔNG DUYỆT VẬN HÀNH). Quyết định thiết kế chính:
  1. **Schema tag GLM = 8 field:** giữ 6 (subject/description/shot_size/has_people/tags +
     mood NÂNG từ free-text → enum đóng **dùng đúng 19 mood của nhạc**, khỏi đẻ vocabulary
     thứ 4); THÊM 2: `scene_type` enum 14 giá trị (e1 ambient + c6 đếm chữ ký) BẮT BUỘC +
     `camera_angle` CHỈ MẺ THỬ (c7: đo tin cậy rồi mới quyết giữ/bỏ).
  2. **Tách GLM khỏi code-thuần (0 token):** màu chủ đạo/sáng/bão hòa (b1 C2b) đo bằng
     PIL/numpy trên chính frame đã rút; duration/fps ffprobe; has_voice từ transcript nguồn
     (d2); provenance (source_video/scene_start/scene_index).
  3. **Đối chiếu đủ 18 phần 5:** schema ĐỦ — nhóm số liệu còn lại (route ratio c1, literal
     c2, hook a2, mật độ chữ f1, dB ducking e1...) đọc từ DRAFT NGUỒN + transcript, không
     cần thêm field vision nào ("tag 1 lần đủ" như d2/b1 yêu cầu).
  4. **Nguồn nạp:** draft CapCut editor (đọc-only, cắt ffmpeg C4) là chính; video viral đi
     qua CapCut tách cảnh (đúng lời user ở c6) — tự-tách PySceneDetect để sau 🔸.
  5. **Chống phình ([[filter-overload-guard]]):** tag mới KHÔNG veto thứ 3, KHÔNG chiều điểm
     mới đợt này (nối đầu chấm mood = mô tả vận hành riêng sau); chủ động KHÔNG thêm
     motion/energy/thẩm mỹ (chưa có người tiêu thụ định danh).
  6. **Token:** mẻ thử 30–50 cảnh (cổng mắt chất lượng tag + đo cost thật) TRƯỚC đại trà;
     cache mtime giữ + luật re-tag khi thiếu field bắt buộc mới.
- **Rà chồng chéo (P5):** 8 tầng ghi trong spec §6 — đáng nhớ: mood 3 tầng hiện có (chọn
  vocab tầng cuối, không map mới); phễu c5 đóng băng không đổi 1 dòng; cột mới KHÔNG vào
  search LIKE (search cũ không đổi kết quả); audience_bias c6 đã cắt — ống nạp không hồi sinh.
- **Lộ trình Phase B:** PB1 spec (👁) → PB2 GLMVisionTagger + schema + migrate (pytest) →
  PB3 mẻ thử 1 project nguồn (👁 + đo cost + chốt camera_angle) → PB4 ống nạp draft + nạp
  đại trà niche đầu → PB5 thống kê DNA đợt 1 (d1/d2/c7/c6).
- **Verify:** spec, chưa code → chưa pytest. Cổng PB1 = **user duyệt `MO_TA_VAN_HANH_TAG_GLM.md`**,
  đặc biệt 5 điểm treo 🔸 §9 (danh sách scene_type; mood 19 từ; tách cảnh qua CapCut; niche
  đầu; GLM_API_KEY).
- **Còn ngỏ:** mọi thứ sau PB1 chờ duyệt. Ngoài lề F9: 2 beat slow-mo (b27 0.37x, b44 0.71x)
  của draft travel là việc editor swap tay, không phải code.
- **PB1 ĐẠT (2026-07-04):** user duyệt spec + xác nhận vision = GLM-4.6 (đã chạy thành công
  ở project nhan ban) → mở PB2.

---

## §PB2 — Code schema tag mới + GLMVisionTagger (2026-07-04, ✅ user xác nhận)

- **Cái gì đổi (code theo ĐÚNG spec `MO_TA_VAN_HANH_TAG_GLM.md`):**
  1. **`library/vision.py` (viết lại):** `AssetTags` mới — thêm `scene_type` (Literal 14,
     BẮT BUỘC) + `camera_angle` (Literal 5, mặc định `unknown` — chỉ tag khi `--angle` mẻ
     thử) + `mood` NÂNG free-text → `list[str]` 1–2 từ, validator ép ⊆ `music.library.MOOD`
     (import thẳng — 1 nguồn sự thật, đổi vocab nhạc là schema footage đổi theo);
     `preview_images()` (rút frame/ảnh 1 LẦN dùng chung vision + đo màu);
     `measure_colors()` (dominant/brightness/saturation bằng PIL thuần — lớp rẻ C2b b1,
     0 token); `_tag_instruction()` chung 2 engine; **`GLMVisionTagger`** — endpoint NATIVE
     bigmodel + `thinking: disabled` + schema-in-system + `_clean_json` + retry 4× backoff
     (copy/adapt từ `nhan ban autoclone/director/client.py::_glm_vision_native`, `_post`
     tách riêng để test stub); `ClaudeVisionTagger` giữ làm fallback, refactor dùng chung
     instruction + nhận `images`.
  2. **`library/db.py`:** 5 cột mới (`scene_type/camera_angle/dominant_color/brightness/
     saturation`) + `_migrate` tổng quát hóa (bảng cột→DDL, idempotent); `upsert_asset`
     ghi đủ; `needs_index` thêm luật spec §5.1: dòng thiếu `scene_type` → tag lại dù mtime
     không đổi (asset cũ tự nâng cấp schema).
  3. **`library/indexer.py`:** rút frame 1 lần → đo màu (fail-open cùng họ image_width
     F5-M3: frame hỏng → tagger tự rút, màu để rỗng) → truyền `images` cho tagger;
     mood list nối `', '` vào cột TEXT cũ.
  4. **`cli.py::library-index`:** `--engine glm|claude` (mặc định glm — CLAUDE.md §5),
     `--model` theo engine, `--angle` cho mẻ thử c7.
  5. **`.env`:** copy `GLM_API_KEY` từ `nhan ban/content-engine/autocontent/.env`.
- **Vùng ảnh hưởng đã rà (P5):** consumer `AssetTags.mood` duy nhất là indexer (join
  chuỗi); `ranker/prompts.py` chỉ đọc `shot_size` (không parse mood) → đổi format an toàn;
  `sourcer/local.py` pass-through string; cột mới KHÔNG vào `search_assets` LIKE (kết quả
  search cũ không đổi — test cũ pass nguyên); FakeTagger là tagger giả duy nhất (grep
  `def tag(`) → cập nhật signature `images=`; 8 chỗ construct `AssetRecord` trong
  test_sourcer dùng default field mới → không vỡ; phễu c5 không đổi 1 dòng.
- **Verify:** FULL suite **215/215** (206 cũ + 9 mới trong `test_library.py`: mood vocab +
  chuẩn hóa/camera_angle default · measure_colors đỏ-tươi/xám-tối/rỗng · GLM parse code-fence
  · retry content-rỗng rồi ok · bỏ cuộc sau 4 lần · migrate DB schema cũ thêm đủ cột +
  needs_index bắt dòng thiếu scene_type · re-tag khi scene_type rỗng · indexer ghi màu+field
  mới (ảnh JPEG thật) · fail-open bytes giả). Smoke `--help` OK. **Smoke GLM THẬT 1 call:**
  ảnh PIL xanh → tag đúng schema (scene_type `abstract_texture`, mood `dreamy` trong vocab,
  camera_angle `unknown` đúng lệnh, folder_context vào tags) — endpoint + key + parse thông.
- **Còn ngỏ:** (1) cổng PB2 = user xác nhận → mở **PB3 mẻ thử**: user chỉ folder 1 project
  nguồn (niche đầu) → `library-init` + tag 30–50 cảnh `--angle --limit` → cổng mắt chất
  lượng tag + đo cost thật + chốt giữ/bỏ camera_angle; (2) ống nạp draft CapCut nguồn
  (PB4) chưa làm — mẻ thử PB3 dùng footage rời/folder có sẵn qua đường `library-index`
  hiện có; (3) `library-search` CLI chưa in cột mới (chỉnh khi cần soi tag ở PB3).

## §PB3 — Mẻ thử tag niche space + 2 bug hạ tầng GLM (2026-07-04, ✅ user duyệt cổng mắt 2026-07-04; camera_angle chốt BỎ khỏi tag đại trà theo luật c7)

- **Setup mẻ thử:** user giao folder nguồn space `E:\PROJECT NHAN BAN\SPACE 1\SP1 - 003`
  (draft CapCut — ĐỌC-ONLY theo spec §2, media nằm ở `materials\`). Chọn tay **46 file đủ
  dạng** (clip space, bầu trời đêm ranh giới sky/space, người ngắm sao, ẩn dụ bánh-mì/kiến/
  bóng-bay, 4 chân dung nhà khoa học, .mov/.webp/jpg nhỏ) → copy vào
  `~\AutoEdit\library\space\` chia **5 folder con TIẾNG VIỆT** (vũ trụ / bầu trời đêm /
  người ngắm sao / ẩn dụ / nhà khoa học) để test luôn cầu ngôn ngữ folder→tag tiếng Anh.
  Script mẻ thử ở scratchpad (KHÔNG đụng package): đa luồng + multi-key + gom usage token
  + sinh `PB3_XEM_TAG.html`; dùng đúng building block production (`_candidates`/`needs_index`/
  `preview_images`/`measure_colors`/`GLMVisionTagger.tag`).
- **Bug B1 — GLM schema-echo (fix vào PRODUCTION `vision.py` + regression test):**
  GLM-4.6V thỉnh thoảng CHÉP NGUYÊN JSON SCHEMA thay vì trả instance (đúng 428 token out),
  NGẪU NHIÊN theo call kể cả temperature=0 (server không deterministic — cùng body, lần 1
  echo lần 2 đúng). Retry mù không cứu nổi khi đen (4/4 echo). **Probe chứng minh: trước
  fix 0/8 call thoát; sau fix 6/6 pass.** Fix 2 lớp trong `GLMVisionTagger.tag`: (1) ví dụ
  instance đúng (build từ chính `AssetTags` — schema đổi là example đổi theo) chèn cuối
  system; (2) user text đổi "Tag the asset." → nói rõ trả INSTANCE, "Do NOT output the
  schema itself". Regression test `test_glm_tagger_schema_echo_retries_and_prompt_hardened`
  (StubGLM ghi body, tái hiện echo→retry→ok + soi 2 lớp chống echo có mặt).
- **Bug B2 — song song 1 key bị bigmodel cắt kết nối:** 6 luồng/key → SSLEOF +
  RemoteDisconnected hàng loạt (payload 2 frame 1280px ~1MB/request, nhiều upload tranh
  băng thông, request chậm bị gateway drop; tuần tự 10 call liền thì SẠCH). Fix ở script
  mẻ thử: **frame thu 960px/q80 trước khi gửi** (83–175KB/request, frame gốc vẫn đo màu)
  + **3 luồng/key** + so le khởi động + **multi-key round-robin** (`GLM_API_KEY_2..9`,
  key phải KHÁC TÀI KHOẢN bigmodel — cùng tài khoản chung trần). User cấp 2 key
  (2026-07-04), cả 3 sống. Kết quả: 9 luồng chạy 35/37 ✓ + 2 lỗi mạng thoáng qua → vét
  pass 2 sạch 46/46.
- **Số đo THẬT (quyết định cấu hình PB4):** trung bình **2.376 token in / 101 out /asset**
  (2 frame 960px + schema + example) ≈ **$0.0016/asset** ($0.6/$1.8 per Mtok) → 1.000 asset
  ≈ $1,6. Tốc độ **13,7s/asset** @ 3 key 9 luồng (480s/35 asset, gồm cả retry) → ước 300
  footage ≈ 60–70 phút. Echo-burn trước fix: mỗi echo 428 token out ≈ 4× tiền out bình thường.
- **Tag sơ bộ (soi db, CHƯA phải cổng mắt):** vũ trụ 21/21 `space`; người ngắm sao 10/10
  `has_people=1`; chân dung 4/4 people + happy/inspiring; ẩn dụ đúng hướng (kiến→
  `animal_wildlife`, bóng bay→`other`+playful; bánh mì→`interior` chứ KHÔNG `food` — user
  soi thêm); mood 100% trong vocab 19 từ; **camera_angle sơ bộ YẾU**: 2 clip có "low-angle"
  trong TÊN FILE bị tag `eye_level` (chỉ 1 low_angle bắt đúng), space clip `unknown` đúng
  lệnh — nghiêng về BỎ, chờ user chốt.
- **Vùng ảnh hưởng đã rà (P5):** fix B1 chỉ đổi PROMPT bên trong `GLMVisionTagger.tag`
  (interface `tag()` không đổi → indexer/CLI/script không sửa); `ClaudeVisionTagger`
  (structured output, không có bug này) không đụng; test stub cũ pass nguyên — FULL suite
  **216/216**. Frame 960px + đa luồng CHỈ ở script mẻ thử — `extract_frames` production
  giữ 1280px, quyết định chính thức (960? 1 frame? luồng?) thuộc PB4 kèm test.
- **Còn ngỏ:** (1) **CỔNG MẮT PB3** = user soi `PB3_XEM_TAG.html` (46 asset, media +
  badge tag); (2) user chốt GIỮ/BỎ `camera_angle`; (3) PB4: đưa đa luồng + multi-key +
  shrink 960 vào `indexer.py` chính thức kèm test; (4) cân nhắc 1 frame/clip như nhan ban
  (nửa payload/tiền — đổi lại mất thông tin clip biến đổi theo thời gian); (5) 2 file
  bánh mì không ra `food` — nếu user thấy sai ở cổng mắt thì thêm hint vào instruction.

---

## §PB4 — Ống nạp draft CapCut + đa luồng/multi-key vào production (2026-07-04, ✅ user duyệt cổng mắt trọn 2026-07-06; user chốt tiếp tục niche space, chưa mở niche khác)

- **Cái gì đổi:**
  1. **`library/ingest.py` (MỚI)** — ống nạp loại 1 spec TAG_GLM §2: `read_draft_scenes`
     (parse `draft_content.json` ĐỌC-ONLY: resolve placeholder path, mọi track video,
     bỏ material thiếu file/cache CapCut/cảnh <1s/trùng khúc; **voice = track audio NHIỀU
     segment nhất** — voice bị chém theo script thành hàng trăm khúc, nhạc vài khúc dài;
     `has_voice` = voice phủ ≥25% cảnh, không track audio = -1 chưa biết) → `cut_scene`
     (ffmpeg `-ss` TRƯỚC `-i` seek chính xác + C4 H.264 CFR 30fps yuv420p + **`-an`** bỏ
     audio nguồn; ảnh JPEG bỏ EXIF; tên clip DETERMINISTIC theo (nguồn+khúc) → tự dedup)
     → `ingest_draft` (clip vào `<niche>/nap/<tên draft>/`, tag qua máy chung, resume).
     **Chốt điểm treo spec §2**: mọi segment video/photo có file nguồn = ASSET, trừ 4 loại bỏ trên.
  2. **`indexer.py`** — máy tag song song `tag_jobs` DÙNG CHUNG index-folder + ống nạp:
     3 luồng/key (PB3-B2), round-robin tagger, stagger đợt đầu (CLI truyền 2s, test 0),
     SQLite CHỈ ghi main thread; `_probe_meta` (§3b duration/wxh/fps, fail-open 0);
     folder `nap/` KHÔNG đưa tên project làm folder_context (tránh "SP1 - 003" vào tags).
  3. **`vision.py`** — `shrink_for_api` 960px/q80 fail-open áp NGAY TRONG `GLMVisionTagger.tag`;
     `glm_api_keys()` (GLM_API_KEY+_2..9); video <2s rút 1 frame (spec §3a); **feedback-retry**:
     retry sau lỗi validation NHÉT CHÍNH LỖI vào prompt cho GLM tự sửa (retry mù không cứu
     nổi model "khăng khăng"); HTTP 400 hiện body (contentFilter đọc được ở kill-log).
  4. **`db.py`** — 8 cột mới §3b + migrate; upsert CASE **giữ provenance ống nạp** khi
     re-index thường (P5: 2 đường ghi cùng 1 dòng). **`music/select.py`** — thêm 2 synonym
     `cozy`/`appetizing`; mood validator footage dịch qua `_MOOD_SYNONYMS` SẴN CÓ trước khi
     bác (không đẻ tầng map mới — đúng rà chồng chéo spec §6).
  5. **`cli.py`** — lệnh mới `library-ingest <niche> <draft>` (+`--dry-run`, `--limit`,
     resume); `library-index` multi-key; `library-search` in thêm scene_type/duration/voice.
- **Chạy thật SP1 - 003** (6,3GB materials): dry-run 244 segment → 237 cảnh; cắt 237 clip
  = **999MB / 29,9 phút footage** từ 100 file nguồn; tag 5 pass (pass 1: 230 + pass 2: 4 +
  pass 5: 2) → **236/237 vào db**. Còn 1: clip aliens hologram bị **bigmodel contentFilter
  1301 (level 2) chặn vĩnh viễn mọi key** — không tag được bằng GLM (file gốc PB3 tag OK vì
  frame khác). Phân bố tag: space×186, sky_cloud×13, interior×8...; wide×187; has_voice
  234 voice/2 thở (video thoại dày đặc — đúng); duration 1,1–34,2s trung vị 7,1s; mood
  mysterious×203/epic×167. `library-search "galaxy spiral"` / `"telescope"` ra hàng thật
  kèm cột mới. Đường resume chứng minh sống: pass 2-5 cắt lại 0, chỉ tag file thiếu.
- **Vì sao:** PB4 spec §8; số đo PB3 quyết định cấu hình (960px/3 luồng/key/multi-key);
  camera_angle BỎ khỏi tag đại trà (luật c7 + user duyệt PB3). `-an` vì audio nguồn là
  voice/nhạc video gốc, không tái dùng (e1 lấy ambient từ SFX library).
- **Vùng ảnh hưởng đã rà (P5):** `index_niche` nhận 1 tagger HOẶC list (test cũ pass nguyên);
  `search_assets`/`local.py` đọc theo tên cột + `.get()` → cột mới vô hại, KHÔNG vào LIKE;
  8 chỗ construct `AssetRecord` dùng default; phễu c5 không đổi 1 dòng; StubGLM snapshot
  body (tagger giờ mutate giữa attempt); `nap/` vẫn nằm trong `_candidates` để move/prune
  không xóa oan dòng ống nạp; upsert CASE chống re-index xóa provenance (có test).
- **Verify:** FULL suite **229/229** (13 test mới: multi-key round-robin · nap không context ·
  provenance CASE · migrate 8 cột · read_draft_scenes lọc/resolve/voice/-1 · cut_scene C4
  idempotent · ingest e2e + resume + limit · shrink fail-open · tagger gửi frame 960 ·
  1 frame <2s · feedback-retry · 400 body · mood synonym). Kill-log nạp + search thật ở trên.
  **Cổng mắt PB4 (user, CHƯA đạt): soi `PB4_XEM_NAP.html`** — 236 cảnh + badge, sắp theo timeline.
- **Ghi chú / còn ngỏ:** (1) clip aliens content-filter → **ĐÓNG 2026-07-07 (phiên tự
  động): tag TAY** — Claude Code nhìn frame giữa clip bằng mắt mình rồi đưa AssetTags qua
  đúng ống `ingest_draft` (ManualTagger, pydantic validate, đủ cột truy vết has_voice=1 ·
  scene_index=49 · duration 6,9s) → **kho nạp 237/237 trọn**. Engine claude 401 (key
  ANTHROPIC hết hạn trong .env — báo user, KHÔNG tự thay);
  (2) nguồn space hiện chỉ có SP1 - 003 — kho `E:\PROJECT NHAN BAN` còn 9 draft niche khác
  (DEEPSEA 1/5, AMAZING, REAL LIFE×4, EX×2) chờ user chốt nạp; (3) 5 material thiếu file
  trong draft nguồn (editor xóa?) — bỏ qua đúng; (4) cắt tuần tự trước tag (~15'/draft) —
  đủ nhanh, chưa cần song song hóa cắt; (5) memory [[glm-46v-tag-lessons]] đã cập nhật.

---

## §PB5 — Thống kê DNA đợt 1: pacing · thở · cỡ cảnh · chữ ký (2026-07-06, ✅ user duyệt cổng mắt 2026-07-07 — Phase B đợt 1 PB1→PB5 đóng trọn)

- **Cái gì đổi:** `library/dna.py` MỚI (`compute_dna(conn, niche, draft_dirs) -> dict`, thuần
  code 0 token, gộp được nhiều draft); `ingest.py` lộ `read_timeline` (MỌI segment video
  timeline kể cả cảnh ống nạp bỏ — nhịp cắt thật cần đủ 244 chứ không phải 237) +
  `DraftScene` mang `target_start/target_duration` (khớp cảnh↔ô thở bằng overlap ≥0,5s,
  sửa từ thiết kế đầu map index bị lệch); CLI `library-dna <niche> --draft <folder>...`.
  Ngưỡng đặt tên hằng: HOLD_S=5 · MIN_BREATH_S=1 · HOOK_S=45.
- **Số thật space (SP1 - 003, lưu `PB5_DNA_SPACE.txt`):** 8,3 cut/phút · shot trung vị
  6,98s (lệch chuẩn 3,11) · hold ≥5s = 81% (niche chậm-ngắm) · 4 khúc vị trí gần phẳng,
  45s đầu shot DÀI HƠN (8,75s) · 39 ô thở/26,6 phút thoại = 1,47 ô/phút, trung vị 1,5s
  max 8,7s, footage thở = space wide · wide 79%/medium 18%, 1 close-up mỗi 39 shot ·
  chữ ký: galaxy×19, spiral galaxy×18, galaxy cluster×14, nebula×9, stargazing...
- **Vì sao:** PB5 spec §8; mọi số có người tiêu thụ định danh ở phần 5 của d1/d2/c7/c6.
  Bảng chỉ là THAM CHIẾU đọc — chưa nối vào validator/prompt nào (rà chồng chéo: 0 tầng
  runtime đụng, phễu/di rect không đổi 1 dòng; nối số vào d1 validator/b1... là mô tả
  vận hành riêng SAU PB5 như spec đã ghi).
- **Verify:** FULL **231/231** (2 mới: `read_timeline` shots+voice · `compute_dna` e2e số
  kiểm tay). Cổng mắt PB5 (user): đọc `PB5_DNA_SPACE.txt` — cách đo đúng ý chưa.
- **Còn ngỏ:** (1) "ô thở sau LOẠI câu nào" cần transcript nguồn — đợt sau; (2) chức năng
  đoạn (hook/thân/cao trào/kết) đang XẤP XỈ bằng 4 khúc vị trí — muốn chuẩn cần NÃO đọc
  transcript; (3) 1 draft = mẫu mỏng — user gom thêm project space rồi chạy lại 1 lệnh;
  (4) DNA chưa ghi file máy-đọc (dna.yaml) — làm khi có consumer đầu tiên (sau PB5).

---

## §PB6 — Giảm frame vision: <10s = 1 frame giữa clip (2026-07-07, ✅ user duyệt cổng mắt 2026-07-07)

- **Cái gì đổi:** `vision.py::preview_images` — luật frame theo thời lượng: video **<10s →
  1 frame GIỮA clip** (`extract_frames n=1` = timestamp 1/2), **≥10s → giữ 2 frame**
  (khoảng 10–15s user viết "≥15s giữ 2 frame" nhưng chưa nói 10–15s — xếp bên 2 frame cho
  an toàn chất lượng, đã báo user). Spec `MO_TA_VAN_HANH_TAG_GLM.md` §3a cập nhật kèm ngày chốt.
- **Vì sao:** user hỏi giảm 2 frame → 1 frame tiết kiệm chi phí; đo thật 1-frame =
  **1.307 in / 79 out ≈ $0,00093/asset — rẻ hơn 42%** (không phải 50% vì prompt cứng ~580
  token không đổi). Kho space hiện 183/236 cảnh <10s → mẻ tương tự tiết kiệm ~40%/mẻ.
- **Verify:** so sánh mù 24 cảnh <10s đủ dạng (script scratchpad `pb6_1frame.py`, KHÔNG ghi
  db): tag 1-frame vs tag 2-frame cũ trong db — scene_type 19/24 · shot_size 23/24 ·
  has_people 24/24 · mood giao 23/24 → `PB6_SO_SANH_1FRAME.html` (lệch tô đỏ). pytest FULL
  **231/231** (test `test_preview_images_one_frame_under_10s` cập nhật ngưỡng
  [(1.5,1),(8.0,1),(9.9,1),(10.0,2),(15.0,2)]). **Cổng mắt: user duyệt 2026-07-07 —
  "footage khớp >90% so với gọi 2 frame"**.
- **Còn ngỏ:** (1) asset đã tag GIỮ NGUYÊN, không tag lại — luật chỉ áp mẻ nạp sau;
  (2) nếu sau này thấy 1-frame yếu ở dạng clip nào → hạ ngưỡng (vd <5s) là đổi 1 số trong
  `preview_images`.

---

## §PB7 — Vá duration local candidate → phễu c5 (2026-07-07, phiên tự động — CHỜ USER DUYỆT SAU)

- **Cái gì đổi:** `sourcer/local.py::_row_to_candidate` gắn thêm key `duration` (float, từ
  cột db PB4) khi `row["duration"] > 0`. Cả `find_local_candidates` lẫn
  `find_signature_candidates` hưởng chung (cùng dùng hàm này).
- **Vì sao:** bug thật lộ khi rà pipeline sau PB6 — phễu c5 tiêu thụ `duration` ở 2 chỗ
  (`funnel.py` cửa kỹ thuật loại clip < beat×0,5 + điểm máy +0,5 khi clip ≥ beat×1,2;
  `ranker/prompts.py` in duration cho NÃO) nhưng ứng viên local KHÔNG mang key này —
  chỉ Pexels có. Hệ quả: clip nạp 1,1s vẫn có thể được chọn cho beat 8s. Trước PB4 db
  chưa có cột duration nên không ai thấy; giờ 236 cảnh nạp có duration thật.
- **Vùng ảnh hưởng đã rà (P5):** mọi consumer của candidate dict đọc duration qua
  `.get()` + chịu None (`funnel.py:65,146` · `prompts.py:66`); `cli.py:1064` đọc dòng db
  không phải candidate. Bẫy cùng-pattern: asset CŨ (PB3, trước migrate) duration=0 →
  nếu truyền 0 thẳng, cửa kỹ thuật loại oan TẤT CẢ asset cũ (0 < mọi beat_dur) → chỉ gắn
  key khi >0. Pexels tự truyền `float(v.get("duration", 0))` = 0 nếu API thiếu — hành vi
  cũ giữ nguyên, không đụng (ghi nhận, không sửa lan).
- **Verify:** FULL **233/233** (2 regression mới: `test_local_candidates_carry_duration`
  + `test_local_candidates_no_duration_key_when_unknown`). Không cổng mắt (fix máy).
- **Còn ngỏ:** `has_voice`/`scene_type` cũng nằm trong db nhưng CHƯA ai tiêu thụ ở phễu —
  để dành cho consumer DNA (d2/c6), không gắn trước (P2).

---

## §C4 — Đóng 6 cổng chờ + C4 từ vựng kho: mô tả DUYỆT + M1 CODE XONG (2026-07-08) ⏸ chờ M2/M3

- **6 phán quyết user (2026-07-08, một lượt):** cổng TAI hình thở 3.0 ĐẠT · PB7 duyệt ·
  PB8 duyệt · cổng mắt SPACE-E2E ĐẠT (footage/slow-mo/DNA "giúp hay nhiễu" đều OK) →
  kéo theo DNA-D1.B Mảnh B đóng cổng mắt + HINH-THO-2 đóng (đã nâng cấp thành 3.0).
  **Toàn bộ cụm hình thở/shot thở/DNA Mảnh B/phễu batch nay ĐÓNG TRỌN, 0 cổng nợ.**
- **Cái gì đổi:** viết `MO_TA_VAN_HANH_C4_TU_VUNG.md` — controlled vocabulary cho query
  local (foundation c4 phần 3b/5 đã treo sẵn, nay tag GLM production 665 asset đủ điều kiện
  mở). 3 mảnh: (1) direct_context.md chở TỪ VỰNG KHO (máy thuần từ db) + 3 lời dặn mã hóa
  bài học PB8; (2) tách `queries.local` khỏi `specific` (2 kho 2 ngôn ngữ — chốt câu hỏi
  foundation c4 để ngỏ); (3) local.py match tier local trước + đo local-hit mỗi run.
- **Phát hiện bug kèm (sẽ vá cùng gói):** lệnh `source` đứng riêng với `--niche` rỗng →
  `find_local_candidates`/signature/shot thở đều TẮT IM LẶNG; skill `/dung-video` Pha 2
  gọi `source <dir>` không truyền niche — editor theo skill nguyên văn sẽ mất local
  (SPACE-E2E sống vì phiên đó truyền tay). Anh em bug B2 quên-consumer. Fix: fallback
  `project.inputs.channel`.
- **Đã cân nhắc và LOẠI (ghi trong mô tả §3):** stoplist từ-chuyển-động phía ỐNG (chồng
  lọc — sửa tại nguồn NÃO sạch hơn) · nới AND→OR match (tái phạm bug 20/06 sai-thành-phố-
  cùng-nước, foundation c4 cấm rõ).
- **User DUYỆT + M1 CODE XONG (2026-07-08 cùng ngày):**
  - `library/db.py::vocab_for_niche` (SQL + Counter, lowercase tag để gộp, bỏ stopword) ·
    `director/live.py::vocab_block` + `build_direct_context(niche=, conn=)` (fail-open 3 nấc:
    không niche / kho rỗng / db lỗi → bỏ khối) · `project.py::SearchQueries.local` +
    `schema.py::SearchQueriesDraft.local` (optional, description = hướng dẫn LLM) ·
    `validator.py` gác local ≤4 từ (getattr vì duck-typed) · `sourcer/local.py` match
    `queries.local + queries.specific` (geo-gate giữ nguyên) · `sourcer/runner.py` fallback
    `niche = niche or channel` tại chokepoint + `local_stats` keyed beat_id (re-gather không
    đếm đôi) → dòng "local-first (C4): X/Y beat · kho thắng Z pick" vào record.warnings ·
    `cli.py::direct-context --niche` + echo có/không khối từ vựng.
  - **1 test cũ lật CÓ CHỦ ĐÍCH:** `test_stock_route_downloads_and_records` assert
    `saved.niche is None` (hành vi "không --niche → không ghi") → nay assert fallback
    `== "kenh-test"` + warning — chính là hành vi bug niche-rơi được vá.
  - **Verify:** FULL pytest **285/285** (7 mới: vocab đếm/rỗng · context 3 nấc fail-open ·
    legacy SearchQueries không local · validator ≤4 từ tier local · tier local match +
    regression PB8 "rotating" trượt · geo-gate vẫn gác tier local · local-first stats +
    fallback regression). **Smoke thật:** `direct-context` Jupiter → fallback niche='space'
    từ channel ✓, khối từ vựng in từ kho 665 asset ✓ — lộ luôn tin mới: sau nạp PB9 kho có
    rocket×11 / launch×10 / eclipse×11 / satellite×14 (các query PB8 từng trượt HẲN giờ có hàng).
- **M2 CHẠY THẬT (2026-07-08 cùng ngày, user duyệt chạy trọn):** project mới
  `script-voice-20260708-070124` cùng input, **tái dùng alignment** (cùng voice + model —
  word index y hệt → port draft ĐÃ DUYỆT, so táo-với-táo mức beat). Phiên sống probe kho
  bằng `library-search` (0 token) → phát hiện kho TRỐNG jupiter/europa (đúng luật: beat
  đặc thù để local RỖNG) → điền `queries.local` cho **48/113 beat** + 2 câu đinh (2.30/3.24)
  → ingest pass → cut (62 giãn; 2 câu đinh máy TỰ BỎ vì voice không nghỉ thật — fail-safe
  đúng thiết kế, chưa có mẫu câu đinh sống) → source 112/112.
  **CỔNG SỐ (so cùng thước rank_log với baseline):**
  | Số đo | Baseline E2E | C4-M2 |
  |---|---|---|
  | Beat có local trong pool đã chấm | 15/112 | **45/112 (3×)** — THU-level 50/112 |
  | Ứng viên local / Pexels | 44 / 1685 | **178** / 1645 |
  | Local THẮNG | 9 | **15** |
  | needs_human · sàn trả lại | 0 · 0 | 0 · 0 |
  Win-rate local khi lọt pool giảm 60%→33% — tier local kéo thêm ứng viên NHẠT-mà-đúng,
  phễu vẫn chuộng Pexels đặc-thù ở beat Jupiter/Europa: ĐÚNG bất đối xứng WRONG-vs-BLAND.
  Beat thắng mới toàn nhóm kho phủ thật: 3 (volcanic eruption) · 39 (mission control) ·
  51/53 (solar flare/plasma) · 84 (magnetic field) · 100/103/109 (spacecraft/probe/sunrise).
  6 slow-mo (0,69–0,99x — 4 cái ~1x không đáng kể; soi b109 0,69x ở cổng mắt).
  DNA validator im ĐÚNG (dna.json load từ F: verify tay). Draft **`SCRIPT_VOICE_20260708_070124`**.
- **Còn ngỏ:** M3 = cổng mắt user (chất lượng 15 pick local + 6 chỗ slow-mo). Câu đinh chưa
  có mẫu sống (2 điểm bị khóa nghỉ-thật bỏ) — thấy ở video có voice nghỉ tại chỗ đinh.
  Dài hạn ghi ở MO_TA §6 (bảng đồng nghĩa, limit=5, prompt direct cũ, niche 2 geo+vocab).

---

## §SHOT-THO-2 — Kéo sâu ô thở 4–10s + đa dạng 1–3 miếng (2026-07-08) ✅ user DUYỆT V7

- **Nguồn:** cổng mắt V6 user phán CHƯA ĐẠT: footage thở "chỉ chạy auto để 2 giây, chưa
  đúng nghĩa thở" (editor: 1 footage thở 4–10s), 100% ô chỉ 1 footage — cần 1–3 footage
  đa dạng, thời lượng đa dạng, số theo niche. User cũng chỉ ra bảng DNA lần đầu TRỘN ô
  voice-nghỉ với ô hình thở → tách 2 lớp; cách làm giao Claude quyết.
- **Gốc rễ:** NÃO director cho breathing bậc 0,5s trần thực tế 3,0s (Jupiter 5×2,5+2×3,0)
  → footage = ô−0,5 = 2,0–2,5s đều. Ô sâu thật editor: liên tục 2,4→12,3s — **4 ô
  8,4–12,3s từng bị bộ lọc "nhiễu ≥8s" che nhầm** (có ô 9,8s ngay trước "Chapter 4"),
  khớp lời editor. Số miếng đo được: đa số 1 (kể cả đơn 7,7s/12,1s), ô rất sâu 2–3.
- **Cái gì đổi:**
  - `cutter/pause.py`: `BREATH_POOLED` (anchors footage [4,0 4,5 5,3 6,8 8,5] p10–p90,
    cap 10, k_thresholds [5,5 8,5], fractions miếng đầu dài nhất) + `load_breath_dna`
    (block `pooled.breath` pause_dna.json niche, fail-open) + `plan_breath_depth`
    (quantile-map rank NÃO→độ sâu, dùng lại `_target`) + `reset_breathing_to_base`.
  - `project.py`: `Beat.breathing_base` (số NÃO gốc — **bẫy idempotent**: không reset thì
    chạy lại cut budget micro trừ theo số ĐÃ KÉO → co micro oan) + `BreathShot.dur`.
  - `cutter/runner.py`: reset base → plan micro (budget theo base — đúng editor: 8–13%
    chèn giãn đo từ rows KHÔNG gồm holes) → plan depth → warning tổng kéo.
  - `sourcer/breath.py`: `_pieces` (k theo ngưỡng + seed `crc32(project_id:beat_id)` —
    KHÔNG dùng `hash()` builtin vì bị salt mỗi process; guard k=1 mà pool không clip đủ
    dài → nâng k=2 né slow-mo xấu) · miếng 2/3 chấm mood NỐI miếng trước (chuỗi) · P7
    xuyên miếng · tên file `bXXX_breath{i}_*`.
  - `packager/coverage.py`: `split_breath_shots(windows, {beat_id: [dur]})` — k cửa sổ
    liền khít, **cửa sổ cuối luôn chạm mép voice kế** (nuốt sai số + pick hụt giữa chừng).
  - `packager/assembler.py`: specs + hàng đợi miếng theo thứ tự list; **fix bẫy tên
    draft điền-lỗ-trống** (`_next_version` = max+1, cắn 2 lần rồi) + regression test.
- **Vùng ảnh hưởng đã rà (P5):** budget micro (base — không đổi so V5/V6, verify 62 điểm
  y cũ) · validator NÃO 1,5–6s = trần số GỐC, số cuối máy map có thể >6 (ghi MO_TA §6.3)
  · funnel thấy số đã kéo ≥2,5 → nhánh conservative cuối-chương tự biến mất · ducking
  nở dài hơn tự nhiên (RAMP 2,5 < ô min 4,5) · SFX/overlay/nhạc anchor word/beat tự tính
  lại khi assemble · test cut end-to-end cũ assert gap=3,0 NÃO — sửa CÓ CHỦ ĐÍCH theo
  luật mới (assert base=3,0 + breathing=5,8).
- **Verify:** FULL pytest **278/278** (8 mới). Jupiter: re-cut 7 ô → 4,5–9,0s (+25,9s,
  micro 62 điểm y cũ) → re-pick **9 miếng/7 ô** (b008 cuối ch1: 2 miếng 4,2+3,0 ·
  b063 cuối ch2: đơn 8,5s · b105: 2 miếng 3,6+2,6) → draft
  **`SCRIPT_VOICE_20260707_132450_V7`** (tên đúng V7 nhờ fix max+1 dù lỗ V4 còn đó).
  Cổng số: 7/7 ô đúng số miếng/dur/file/thứ tự, mép giữ = hết voice+0,5 ±1 frame, miếng
  cuối chạm đúng mép voice kế · 8/8 ô nông giữ J-cut 0,3 · 129 segment video 0 hở/đè.
- **Còn ngỏ:** b105 miếng 1 vẫn clip trạm điện (kho space không có mood sad — soi ở cổng
  mắt, nếu nhạt → backlog NÃO chấm shortlist) · luật k mới có 3 điểm dữ liệu editor
  (nửa DNA nửa interview) — đo lại khi có thêm project · scan DNA niche mới phải tách
  2 lớp ô + không lọc phăng ≥8s (MO_TA §6.2C) · usage kênh log lần 2 khi re-pick
  (đếm mềm, chấp nhận).
- **Trạng thái:** ✅ **user DUYỆT V7 (2026-07-08)** — shot thở 2.0 ĐÓNG (kể cả b105
  trạm điện qua được mắt). Còn mở: cổng TAI hình thở 3.0 (nhịp nghỉ V7 vs bản editor —
  chưa nghe riêng) + backlog §6.5 MO_TA (outro cuối video, NÃO chấm shortlist nếu cần,
  report.html vẽ shot thở, đo phân bố k thêm, đóng gói tool scan DNA niche).

---

## §SHOT-THO — Footage riêng cho ô thở hết ý/cuối chương (2026-07-08) — cổng MẮT V6 CHƯA ĐẠT → §SHOT-THO-2

- **Nguồn:** user xem V5, chỉ ra ô thở dài chỉ "để footage trước chạy tiếp" trong khi
  editor để 1 footage KHÁC (không voice) cùng mood khác cỡ cảnh. Soi lại
  `pause_dna_rows_SP1-00X.json::shot_offsets`: đúng — ~25% ô (nhất là hết ý/cuối chương)
  editor giữ hình cũ 0,4–0,9s → CẮT sang footage khác chạy im lặng 1–5s → voice vào trên
  footage đó (SP1-004 ô cuối chương 5,3/4,0/3,9s; SP1-001 ô 6,1s im lặng 5,2s).
  **ĐÍNH CHÍNH tri thức cũ:** "ô sâu = giữ hình, không footage riêng" chỉ là style
  SP1-003 (memory [[sp1-003-breathing-pattern]] đã sửa). User chốt: 100% ô đạt ngưỡng +
  chọn máy thuần (phương án a). Thiết kế: `MO_TA_VAN_HANH_SHOT_THO.md`.
- **Cái gì đổi:**
  - `packager/coverage.py`: `BREATH_SHOT_MIN=2.5 / _CHAPTER=1.5 / HOLD=0.5` +
    `breath_shot_beat_ids` (beat cuối video không nhận) + `split_breath_shots` (chẻ cửa
    sổ thành [thoại+0,5 giữ] + [shot thở]; cửa sổ giữ còn breathing 0,5 < 1,2 → TỰ thoát
    `apply_j_cuts`, không if riêng) + `CoverWindow.breath_shot`.
  - `sourcer/breath.py` MỚI: pool = `db.videos_for_niche` (mới) + geo-gate PA2; điểm
    mood trùng clip liền trước +2/tag (clip stock không tag → dịch `beat.mood` qua
    `_MOOD_SYNONYMS`) · khác cỡ cảnh +1 (trùng = 0, vẫn chọn — đúng lời user) · đủ dài
    +1,5 · chưa dùng kênh +0,5 · wide/aerial +0,5 (proxy "đắt"); loại DUY NHẤT = P7
    used_in_video (filter-overload-guard: không đẻ cửa loại). Copy `assets/bXXX_breath_*`,
    log usage, ghi `project.breath_shots` (model `BreathShot` mới — NT1/NT5).
  - `sourcer/runner.py`: gọi sau khi mọi beat có clip (mood hàng xóm đã biết).
  - `ranker/funnel.py::_need_dur`: ô ≥2,5 → clip beat chỉ phủ thoại+0,5 (shot thở gánh
    phần sau; ô cuối-chương 1,5–2,5 phễu không biết hàng xóm → giữ conservative).
  - `packager/assembler.py`: `breath_ids` từ picks THẬT (pick hụt → ô tự về hành vi cũ,
    2 tầng không lệch nhau được); cửa sổ breath đặt 1 clip nguyên ô.
- **LUẬT LẬT (P5):** rà 2026-07-04 #1 "ô thở = 1 hình giữ, nhát cắt không rơi giữa im
  lặng" bị lật CÓ CHỦ ĐÍCH tại ô đạt ngưỡng (bằng chứng DNA + mắt user); ô dưới ngưỡng
  giữ luật cũ. Ghi ở MO_TA §3 + comment coverage.py.
- **Verify:** FULL pytest **270/270** (12 mới: 4 coverage + 7 breath + 1 ranker regression
  "clip 4s từng bị giết oan ở ô 5s giờ sống"). **Jupiter V6 cổng số ĐẠT:** 7/7 ô đạt
  ngưỡng có shot thở (vd b008: giữ tới 47,68 = hết voice+0,5 → `b008_breath_nasa...`
  chạy tới 49,68 = ĐÚNG mép voice kế, không J-cut) · khác clip liền trước 7/7 · 8/8 ô
  nông giữ J-cut 0,3 y cũ · 0 mối nối hở/đè (127 segment video) · 6/7 khớp mood (b105
  mood `sad` — kho space không có clip sad, máy rơi về cỡ cảnh/độ dài → chọn clip trạm
  điện, ĐIỂM ĐÁNG SOI ở cổng mắt; nếu nhạt → backlog NÃO chấm shortlist).
- **Ghi chú / còn ngỏ:** draft đầu bị đặt tên `_V4` (điền lỗ trống tên do V4 orphan đã
  xóa) → dựng lại thành **V6**, xóa V4 mới. Backlog MO_TA §5: ô cuối video · ô >6s
  montage-lite · NÃO chấm "đắt" · report.html vẽ shot thở · nhạc tại ô.
- **Trạng thái: ⏸ chờ cổng MẮT user V6** (kèm cổng TAI hình thở 3.0 vẫn mở).

---

## §HOC-DNA-NHIP — HỌC DNA nhịp nghỉ 3 project + hình thở 3.0 CODE XONG (2026-07-08) ⏸ chờ cổng TAI V5/V6

- **User chốt "đồng ý chạy"** phương pháp §NHIP-NGHI → bước HỌC chạy xong cùng ngày
  (máy thuần 0 API, ~25ph: transcribe 9 file voice 001/004 + cache 003 tái dùng).
- **Script HỌC:** `learn_pause_dna.py` (scratchpad phiên này) — nâng cấp từ
  `scan_editor_cuts.py` cũ: quét cả 3 project + **tự đối chiếu script gốc** (khớp 3 từ
  ngữ cảnh, đọc ký tự giữa 2 từ quanh điểm cắt — thay việc đối chiếu tay) + đo ô thở/
  J-cut/spacing/tỷ lệ chèn. Verified 95% (97/102 · 205/213 · 140/149); bắt được cả
  whisper BỊA dấu chấm ("cosmic house ‖ But one" — script không có chấm).
- **Artifact bền (project root):** `pause_dna.json` (DNA gộp + per-project) +
  `pause_dna_rows_SP1-00X.json` (3 file, từng điểm cắt + ô thở). Nhiễu đã lọc: gap ≥8s
  = ranh giới section/montage (004 có ô "57,7s" thật ra là section; 001 voice nửa sau
  video nằm track khác — chỉ đo được đoạn hook+ch1-2).
- **DNA chốt (464 điểm cắt + 52 ô thở):** kết câu 4,9/phút nghe-ra p50 1,55s (3 project
  hội tụ 1,78/1,51/1,50) · kết mệnh đề 1,6/phút p50 0,95s · giữa mệnh đề 0,28/phút =
  quyết định nghĩa · ô thở 0,6–0,8/phút p50 2,1–3,2s max ~7s, 12/14 chương có ô ·
  chèn tổng +8,3–16,8% · editor cắt ~50% ranh giới câu, nửa còn lại TTS editor tự nghỉ
  0,85s (ta 0,5s — backlog).
- **Thiết kế đã viết: `MO_TA_VAN_HANH_HINH_THO_3.md`** — SINH: quantile-rank mapping
  máy thuần theo DNA (K=4,9/phút câu + 1,6/phút mệnh đề, δ clamp, trần chèn 13%, 2 khóa
  giữ nguyên); NÃO +0 call: thở sâu 3,5–6s (phương án A gộp vào) + câu đinh beat-level;
  3 chỗ phải sửa cùng lúc: ducking MIN_BREATH 1.0→1.5 (kẻo phập phồng theo câu), cửa
  phễu cộng breathing+micro vào need_dur, validator trần thở 3→6s đồng bộ foundation.
- **User DUYỆT ("tính toán cẩn thận và làm") + CODE XONG cùng ngày:**
  - `cutter/pause.py` viết lại ruột: `load_pause_dna` (đọc `~\AutoEdit\library\<niche>\
    pause_dna.json` cạnh dna.json, fail-open về POOLED_DNA — cut chạy trước source nên
    video mới dùng pooled) + quantile-rank mapping (`_target` nội suy anchor p10–p90,
    `_pick_tier` chọn nghỉ-dài-trước + guard 3s); thứ tự câu đinh NÃO → câu → mệnh đề;
    trần ngân sách tính cả thở. `cutter/runner.py` log 3 tầng.
  - NÃO: `Beat.rhetorical_pause` + `BeatDraft.rhetorical_pause` (schema description =
    hướng dẫn LLM) + map ở director/runner + `MAX_RHETORICAL_PER_CHAPTER=1` (validator)
    + bảng ràng buộc live.py thêm dòng câu đinh + hướng dẫn thở "ÍT nhưng SÂU" (schema
    + live). Trần thở validator VỐN đã 1,5–6s (dự tính "nâng 3→6" sai — đã ghi MO_TA).
  - Chồng chéo sửa cùng lúc: ducking `MIN_BREATH` 1.0→1.5 (packager/ducking.py);
    funnel `_need_dur` = beat + breathing + micro (cửa kỹ thuật + DURATION_BONUS,
    funnel.py — vá lỗ hổng sẵn có PB7 chưa thấy).
  - **2 bài học chạy thật:** (1) BUDGET 13% bị tầng câu ăn hết (δ thực ~0,95 vì voice
    ta nghỉ nền nông hơn TTS editor ~0,35s) → tầng mệnh đề chết đói 1/16 điểm → nâng
    15% (vẫn trong khung editor 8,3–16,8%); (2) test quantile dính nhiễu float cộng
    dồn 0,35 xáo hạng nhóm nghỉ-bằng-nhau → fixture dùng số nhị phân chính xác 0,375/0,75.
  - **Verify:** FULL pytest **258/258** (7 test pause viết lại + 1 funnel regression).
    **Cổng số §6 MO_TA_3: ĐẠT** — Jupiter: 49 câu + 13 mệnh đề (+52,8s), nghe-ra câu
    p50 **1,55 = DNA editor trùng từng số** (p25 1,29/1,28 · p75 1,74/1,90), mệnh đề
    p50 0,95 = DNA, 0 điểm không dấu, +14,3% ≤ 15%, 78/78 mối nối draft khớp plan.
  - **Draft: `SCRIPT_VOICE_20260707_132450_V5`** (V4 là orphan của 1 lần chạy bị
    PowerShell `Select -First` giết pipeline giữa chừng — đã xóa; bài học: đừng cắt
    stream lệnh dài đang chạy). Câu đinh + thở sâu NÃO chưa có trong V5 (direct Jupiter
    chạy từ trước) — sẽ thấy ở video direct mới.
- **Trạng thái: ⏸ chờ cổng TAI user** — so V5 với V3 và bản gốc editor SP1-003.

---

## §NHIP-NGHI — Chẩn đoán "nghe ra" toàn cục: khung top-N SAI so với editor (2026-07-08) ⏸ đã chốt phương pháp → xem §HOC-DNA-NHIP

- **Bối cảnh:** user duyệt phương án A (thở sâu NÃO chọn + vá cửa phễu funnel.py chưa cộng
  breathing — xem tư vấn cùng ngày) NHƯNG xem lại SP1-003 thấy editor "cắt nhẹ rất nhiều,
  không cần hết câu/mệnh đề, thường <1s" → yêu cầu HỌC 3 project rồi tính phương pháp,
  không loại trừ gọi thêm LLM. Kiểm 2 ví dụ user trên draft: đúng hướng — câu chốt hook
  bị chop 5 nhát nhẹ 0,13–0,43s (timecode CapCut min:s:frame dễ đọc nhầm số tuyệt đối).
- **SỐ MỚI QUYẾT ĐỊNH (tính "NGHE RA" = nghỉ nguồn + gap chèn tại 213 điểm cắt SP1-003):**
  | Loại | Nghỉ nguồn TTS editor | Gap chèn | NGHE RA trung vị (p25–p75) |
  |---|---|---|---|
  | Kết câu (153) | 0,82s | 0,60s | **1,47s (1,25–1,79)** |
  | Kết mệnh đề (46) | 0,56s | 0,37s | **0,96s (0,73–1,06)** |
  | Giữa mệnh đề (14→3 thật) | ~0,55s | ~0,2s | 0,89s |
  KHÔNG có điểm cắt nào nghe ra <0,5s. Tổng chèn 137,7s ≈ **+8,4% duration nguồn**.
- **Chẩn đoán:** voice ta nghỉ kết câu tự nhiên ~0,5s; editor = 1,47s tại PHẦN LỚN ranh
  giới câu (5,2 điểm/phút), không phải top-N. Khung đợt 1+1.5 (chọn 1,9/phút mỗi tầng)
  đúng hướng nhưng SAI KHUNG: cái tạo cảm giác "không liền mạch" là MỌI câu đều có nhịp
  dừng thật, phân tầng theo loại dấu — không phải vài điểm được giãn đậm.
- **Tư vấn đã gửi user (chi tiết trong chat, chờ chốt):** HỌC 3 project (SP1-001/003/004,
  máy thuần 0 API, script quét tái dùng + transcript cache) ra `pause_dna.json` per-niche
  → SINH bằng quantile mapping máy thuần thay khung top-N (2 khóa an toàn giữ) → NÃO chỉ
  2 quyết định nghĩa (thở sâu A + câu đinh chop hook/kết, gói vào call direct, +0 call).
  Rà lớn phải xử: **ducking MIN_BREATH=1.0 sẽ phập phồng khi δ câu ~0,7–1,2s**; duration
  +8–12%; đề xuất GỘP phương án A vào cùng đợt "hình thở 3.0".

---

## §D2-DOI-CHIEU — Đối chiếu script gốc 14 điểm nghi + thiết kế đợt 1.5 (2026-07-08) ⏸ CHỜ USER DUYỆT

- **Làm gì:** việc tiếp #1 của §D2-QUET-CAT — đối chiếu 14 điểm "giữa mệnh đề" với
  script gốc `E:\PROJECT NHAN BAN\SPACE 1\SP1 - 003\CONTENT ENGLISH\SP1-003 - CONTENT.txt`
  (bảng từng điểm: `MO_TA_VAN_HANH_HINH_THO_2.md §6.1`).
- **Kết quả — nghi ngờ whisper-mất-dấu ĐÚNG 11/14:** 10 điểm thật ra là KẾT MỆNH ĐỀ
  (script có `,` `:` `—` — whisper vừa mất dấu vừa nuốt liên từ and/or/because/is);
  1 điểm là KẾT CÂU (ranh giới tiêu đề chương 4); chỉ 3 điểm giữa-mệnh-đề THẬT — cả 3
  trong CÙNG 1 câu chốt hook (42–47s file 1), editor cắt vụn 1 câu dài có chủ đích =
  thủ pháp tu từ 1,4%, KHÔNG code (P2).
- **Bảng 3 tầng CHỐT:** kết câu 154 (72,3%, gap 0,60) · **kết mệnh đề 56 (26,3%, gap
  0,37/p90 0,53)** · giữa mệnh đề thật 3 (1,4%). → 98,6% điểm cắt editor nằm ở ranh
  giới CÓ DẤU trong script: khóa dấu câu đúng hướng, chỉ cần mở rộng sang dấu mệnh đề.
- **Khả thi trên data ta (Jupiter 10,3ph):** 20/112 beat kết `,;:` (1,94/phút — vừa
  khớp mật độ editor 1,9/phút, KHÔNG cần cắt trong lòng beat), 16 đạt khóa nghỉ ≥0,3s
  (4 beat gap=0 tự loại).
- **Thiết kế đợt 1.5 đã viết** (`MO_TA_VAN_HANH_HINH_THO_2.md §6.2–6.4`): tầng mệnh đề
  chọn SAU tầng câu, khóa dấu `,;:—–` + khóa nghỉ ≥0,3s, δ=clamp(nghỉ, 0,2–0,4),
  CLAUSE_PER_MIN=1,9, spacing ≥6s, cùng field `micro_pause_after` (hạ nguồn 0 đổi).
  Rà chồng chéo: lật CÓ CHỦ ĐÍCH luật đợt 1 "kết mệnh đề không bao giờ giãn" — phải
  sửa đồng bộ 3 chỗ (MO_TA §2 + docstring pause.py + test fixture); giữa mệnh đề
  (không dấu) VẪN khóa tuyệt đối.
- **User DUYỆT + CODE XONG (2026-07-08 cùng ngày):**
  - `cutter/pause.py`: thêm `CLAUSE_END/_ends_clause` + helper `_pick` (2 tầng dùng
    chung logic chọn); tầng câu chọn trước y nguyên, tầng mệnh đề lấp sau (δ 0,2–0,4,
    1,9/phút, spacing 6s). Docstring lật luật đồng bộ. `cutter/runner.py`: log tách
    2 tầng ("N kết câu + M kết mệnh đề").
  - Sửa đồng bộ 3 chỗ ngược chiều: MO_TA §2 (ghi chú lật luật) + docstring + fixture
    `test_micro_pause_never_stretches_mid_clause` (bỏ dấu phẩy — ý regression giữa-mệnh-đề
    GIỮ NGUYÊN). 3 test mới: chọn đúng dấu + δ clamp · khóa nghỉ thật · thứ tự tầng +
    spacing 6s + deterministic.
  - **Verify:** FULL pytest **257/257**. Chạy thật Jupiter: 25 điểm (18 kết câu — y hệt
    đợt 1, tầng cũ không bị lấn ✓ + 7 kết mệnh đề mới, δ đều 0,4), tổng chèn +13,9s.
    Soi tay 7/7 điểm mới đều kết `,` vế nghĩa trọn. Draft **`SCRIPT_VOICE_20260707_132450_V3`**
    (tên mới NT5): 41 segment voice / 40 mối nối = 15 thở + 25 giãn khớp plan từng cái.
  - **Ghi nhận (không phải bug, không sửa):** gap draft = δ plan + đúng 0,1s ở MỌI mối
    nối — do luật assembler "target ngắn hơn source ≥3 frame" (bài học CapCut 6.8,
    3 frame @30fps = 0,1s), có từ trước đợt 1; start mọi segment khớp plan tuyệt đối,
    phần trim là lặng. Số "nghe ra" thực tế = δ + lặng giữ 2 mép + 0,1s.
- **Trạng thái: ⏸ chờ cổng TAI user** — so V3 với V2 và với bản gốc editor.

---

## §D2-QUET-CAT — Quét điểm cắt voice editor SP1-003: XONG, ra 3 tầng cắt (2026-07-08)

- **Bối cảnh:** user chấm cổng TAI đợt 1: "hình thở ĐÃ TỐT HƠN, đạt các điểm đã nhắc,
  NHƯNG không bằng bản gốc editor — nghi editor KHÔNG CHỈ cắt khi hết câu/mệnh đề."
- **Cách quét:** transcribe 7 file voice SP1-003 bằng faster-whisper → chiếu 213 điểm
  cắt cùng-file lên chữ. Artifact bền: `D2_QUET_CAT_SP1003.json` (project root — đủ
  ngữ cảnh 6 từ hai bên mỗi điểm). Bẫy đã né: so material theo TÊN file, không theo id
  (CapCut nhân bản material id cho cùng 1 mp3).
- **KẾT QUẢ — nghi ngờ user ĐÚNG, editor cắt 3 TẦNG có thứ bậc gap:**
  | Vị trí cắt | n | % | Gap chèn trung vị | Ta (đợt 1) |
  |---|---|---|---|---|
  | Kết câu `.?!` | 153 | 72% | 0,60s (p90 1,23) | ✅ đã làm (δ 0,4–0,7) |
  | **Kết mệnh đề `,;:`** | **46** | **22%** | **0,37s (p90 0,53)** | ❌ **THIẾU — tầng chính cần thêm** |
  | Giữa mệnh đề | 14 | 6,6% | 0,29s | 🔸 nghi phần lớn là whisper THIẾU DẤU CÂU + ranh giới tiêu đề chương ("...away. Chapter 1 The") — cần script gốc đối chiếu |
- **Đọc thêm từ 14 điểm giữa-mệnh-đề:** vài cái giống nhịp LIỆT KÊ ("never travel to
  them ‖ send a message to them"), vài cái rõ ràng whisper mất dấu ("Step back and
  breathe ‖ this part..."). KHÔNG code theo data nhiễu (P1) — đối chiếu script gốc trước.
- **VIỆC TIẾP (đợt 1.5, làm sau clear):**
  1. **Script gốc ĐÃ CÓ (user thêm 2026-07-08)** ở `E:\PROJECT NHAN BAN\SPACE 1\<SP1 - 001|003|004>\CONTENT ENGLISH\*.txt`
     → đối chiếu 14 điểm giữa-mệnh-đề + kiểm lại phân loại whisper (kiểm tra nhanh 1 điểm
     đã xác nhận hướng: "the universe ‖ it is not empty" thật ra script có DẤU PHẨY —
     whisper mất dấu → điểm đó là kết mệnh đề). Xong đối chiếu mới chốt luật.
  2. Thiết kế thêm tầng **kết mệnh đề** vào `cutter/pause.py`: δ nhỏ ~0,2–0,4s, mật độ
     ~1,6/phút (46/29,5ph), spacing ngắn hơn tầng câu — bổ sung MO_TA_VAN_HANH_HINH_THO_2.md
     (mục đợt 1.5) → user duyệt → code + pytest + dựng lại Jupiter V3 cho cổng TAI.
  3. Script quét tái dùng được cho SP1-001/004 khi cần (transcript cache ở scratchpad cũ:
     `...\129fe827-...\scratchpad\sp1003_cut_scan\`).

---

## §HINH-THO-2 — Hình thở 2.0 đợt 1: giãn nghỉ máy + J-cut (2026-07-08) ⏸ chờ cổng mắt+TAI

- **Cái gì đổi** (user chốt "tiến hành code luôn" sau khi duyệt phân tích §D2-PHAN-TICH;
  thiết kế + rà chồng chéo: `MO_TA_VAN_HANH_HINH_THO_2.md`):
  1. **Giãn nghỉ máy** — `cutter/pause.py::plan_micro_pauses` (pure, 0 call NÃO):
     chọn ~1,9 điểm/phút voice qua **2 khóa an toàn nghĩa câu** (user hỏi đích danh):
     khóa dấu câu (beat.text kết `.?!` — kết mệnh đề/giữa mệnh đề KHÔNG BAO GIỜ giãn)
     + khóa nghỉ thật (alignment đo ≥0,3s). Ưu tiên nghỉ-dài, cách nhau ≥12s. δ =
     clamp(nghỉ, 0,4–0,7s) → nghe ~0,7–1,1s. Field mới `Beat/VoiceSegment/SegmentPlan
     .micro_pause_after` (máy điền ở cut, reset mỗi lần chạy — không cộng dồn, tách
     hẳn `breathing_after` đạo diễn).
  2. **J-cut** — `coverage.py::apply_j_cuts`: ô thở ≥1,2s → mép video với cửa sổ kế
     lùi sớm 0,3s (shot kế vào TRƯỚC voice — mẫu 14/18 SP1-003); tầng micro không
     bao giờ J-cut; chỉ đụng video, voice/nhạc nguyên.
- **Vùng ảnh hưởng đã rà (P5, bảng đủ trong MO_TA §4):** ducking nuốt gap ≤0,7s
  (MIN_BREATH=1.0) — không phập phồng; split_window multi-shot dùng `tail_dur` =
  breathing+micro; segment cuối ép cả 2 = 0 (total_end 4 chỗ cũ vẫn đúng); validator
  direct-ingest không đụng; test integration cũ (7s cửa sổ thở) cập nhật theo J-cut 6,7s.
- **Verify:** FULL pytest **254/254** (9 mới — có regression đích danh nỗi lo user:
  lặng dài giữa mệnh đề KHÔNG được giãn). Chạy thật Jupiter: 18 điểm giãn (+11,1s,
  δ 0,44–0,70), 34 segment voice, 6/6 mẫu soi tay đúng kết câu trọn nghĩa; **15/15 ô
  thở trong draft có mép video đúng resume−0,3s** (kiểm bằng đọc draft_content).
  Draft mới: `SCRIPT_VOICE_20260707_132450_V2`.
- **Cổng TAI user (2026-07-08): ĐẠT MỘT PHẦN** — "đã tốt hơn, đạt các điểm đã nhắc,
  tuy nhiên KHÔNG BẰNG bản gốc editor" → mở đợt 1.5: quét điểm cắt editor (§D2-QUET-CAT).
- **Còn ngỏ (đợt 2 — backlog d2):** footage riêng cho ô thở (hiếm, 3/18) · chuỗi
  trình chiếu · sàn + cứu hộ 3 nấc · RO_PER_MIN=1,9 chỉnh theo DNA khi đo kho 100 video.

---

## §D2-PHAN-TICH — Mổ xẻ hình thở SP1-003 (mẫu user chỉ định) → đảo ưu tiên backlog d2 (2026-07-08)

- **User giao:** học kỹ SP1-003 — "editor cắt voice ra rất nhiều đoạn, nghe ngắt nghỉ
  phù hợp; voice AI đọc liền mạch kiểu AI" — tính xem ta làm được chất lượng tương tự không.
- **Số đo (track voice 225 segment / 29,5 phút, đọc-only draft_content.json):**
  editor banh voice ra chèn nghỉ ở 221/224 mối nối, nguồn cắt LIỀN 210/211 (không bỏ chữ).
  Phân bố (7,5 khoảng/phút): 26 <0,3s · 121 [0,3–0,7) · 56 [0,7–1,5) · 18 thở [1,5–7,1s].
  Hình trong 18 ô thở dài: **14 = giữ hình cũ + J-cut shot kế vào sớm 0,1–0,6s trước
  voice** · 3 shot riêng đầu ô · 1 phủ thụ động (= kiểu autoedit hiện tại).
- **Voice AI của ta đã có sẵn** 17,5 nghỉ/phút ≥0,3s (trung vị 0,52s) nhưng đều + ngắn
  (13 cái 0,7–1,5s; 2 cái ≥1,5s /10,3 phút) → thiếu TẦNG nghỉ rõ + thở chủ đích.
- **Kết luận đảo ưu tiên:** ~85–90% cảm giác thở = xử lý VOICE (giãn nghỉ sẵn có theo
  phân bố DNA) + J-cut — máy thuần 0 call NÃO; "footage đắt riêng" chỉ 3/18 → đẩy xuống
  đợt 2. DNA d2 ngưỡng ≥1s đang MÙ tầng vi nghỉ → hạ ngưỡng khi đo kho mới. Chi tiết +
  điểm kiểm chứng (alignment vs silencedetect): memory `sp1-003-breathing-pattern`.
- **Trạng thái:** phân tích xong, CHƯA code — chờ viết mô tả vận hành "hình thở 2.0" user duyệt.

---

## §SPACE-E2E — Video space đầu tiên chạy trọn ống L2b sâu + phễu batch (2026-07-07) ⏸ chờ cổng mắt

- **Input:** `D:\SPACE 3 - 007` (hook + chương 1-2 của video 5 chương về 4 mặt trăng
  Galilean; user giao rút gọn cho nhanh). Voice 619s · script 1725 từ · 112 beat ·
  3 chương (Hook 0-130 · Io 131-958 · Europa 959-1724) · 14 overlay · 1 bar-chart ·
  1 info_card · 16 ô thở. Beats user DUYỆT ("duyệt, hãy dựng tiếp").
- **Source (phễu batch, run thật đầu tiên):** 112/112 beat OK, **0 needs_human**.
  **12 call batch** (22:09→22:47, ~42 phút cả tải+transcode ≈ 25s/beat) · **0 fallback**
  per-beat · thu 1912 ứng viên · chết kỹ thuật 10 (0%) · veto nghĩa 173 (9%) · sàn 3
  trả lại 0. Cổng số §PA-BATCH: ≤15 call ✓.
- **Quan sát QUAN TRỌNG — local chỉ thắng 9/112:** KHÔNG phải phễu chê kho (local lọt
  pool 15 beat, thắng 9 = 60%) mà bước THU gần như không tìm thấy local: 44 ứng viên
  local vs 1685 Pexels toàn video, dù kho space có 665 asset. Nguyên nhân = query
  free-text tiếng Anh không khớp tag GLM — đúng khoảng trống **c4 controlled vocabulary
  đã chủ động hoãn** (MO_TA_PHEU_C5 §4). Kho local muốn thành nguồn CHÍNH
  ([[footage-source-local-first]]) thì c4 là việc kế tiếp có ăn nhất.
- **Assemble:** ✓ draft `SCRIPT_VOICE_20260707_132450` (tên mới, NT5). 3 clip ngắn kéo
  slow-mo (b29 0.61x · b49 0.88x · b69 0.77x — editor nên swap); nhạc 3 chương đổi theo
  mood + ducking ramp 2.5s; 14 text + 14 SFX + 1 chart PiP + 1 info-card lên layer2.
- **Validator DNA Mảnh B — LẦN NỔ ĐẦU TIÊN, im ĐÚNG (verify bằng tái lập tay):**
  dna.json load OK (niche=space); video đo std shot 1,92s ≥ sàn 1,55 (½×3,09) và
  10,5 cut/phút trong khung [4,7–18,8] → 0 cảnh báo; không có chuỗi "validator lỗi"
  trong project.json. Video dựng ra NẰM ĐÚNG vùng DNA nhịp space (DNA 9,4 cpm).
- **Report:** ✓ `projects/script-voice-20260707-132450/report.html`.
- **Cổng mắt (user, CHƯA chấm):** CapCut mở draft không đen/không relink · chất lượng
  chọn footage của phễu batch · 3 chỗ slow-mo · cảnh báo DNA "giúp hay nhiễu".

---

## §PA-BATCH — Phễu c5 chấm batch: 1 call/~10 beat thay 1 call/beat (2026-07-07)

- **Cái gì đổi:** theo `MO_TA_VAN_HANH_PHEU_BATCH.md` (user chốt cùng ngày sau khi thấy
  run thật quá chậm + DỪNG run giữa chừng): **PA-1** `runner._prefetch_batch` gom ≤10 beat
  stock/local liền nhau cùng chương → `funnel.rank_batch` 1 call (`BatchRankResponse`) →
  cache verdict → `rank_beat_prescored` tiêu thụ tuần tự (điểm máy + sàn 3 chung
  `_finish_scoring` với đường cũ). **PA-2** `cc_client(thinking=False)` (env
  `MAX_THINKING_TOKENS=0`, chỉ đường rank) + `ly_do ≤12 từ`; sonnet là trần model phễu.
  **PA-3** pool ≤1 sau cửa kỹ thuật → auto-pick 0 call.
- **Vì sao:** đo 45 call thật video space: trung vị 65s/beat (112 beat ≈ 2h); output
  3.906 token/call mà JSON thật ~700-900 (~75% thinking) + phí node mỗi call. User chỉ
  đích danh thiết kế 1-call/beat không scale.
- **Vùng ảnh hưởng đã rà (P5, chi tiết MO_TA §3):** P7 chống lặp trong chunk = máy gác
  ở vòng tải (không tin LLM); veto/sàn/điểm máy dùng chung code cũ (test bất biến
  batch=per-beat); kill-log/rank_log/cost giữ schema per-beat; fallback 2 nấc (chunk lỗi
  → cả chunk per-beat; NÃO quên 1 beat → beat đó per-beat); heuristic + entity/graphic
  không đụng. Sự kiện kèm: **dừng run source giữa chừng an toàn** (stage RUNNING không
  DONE → chạy lại từ đầu stage, Pexels cache SQLite nên 0 phí query lại).
- **Verify:** FULL **245/245** (4 test mới). Cổng số chạy thật + cổng mắt: chung run
  video space (§SPACE-E2E khi xong).
- **ĐÃ ĐÓNG còn-ngỏ 1 (run thật 22:05–~22:15 cùng ngày, 3 chunk đầu):**
  `MAX_THINKING_TOKENS=0` ĂN THẬT — output ~89–91 token/verdict (call#1: 9 beat/176
  verdict/15,7k tok; call#2: 10 beat/156 verdict/14,2k tok) vs ~195 token/verdict baseline
  → gần thuần JSON, hết thinking. `ly_do` trung vị 11 từ (max 15). Nhịp: 20 beat đầu
  ~10 phút ≈ **30s/beat** (gồm tải+transcode) vs 65s/beat cũ. Veto mẫu soi tay đúng dạng
  nghiêm trọng (mây/bãi biển Trái Đất bị loại khỏi beat Jupiter).
- **Còn ngỏ:** pool beat sau trong chunk cạn do beat trước tiêu trùng — hiếm, needs_human đỡ.

---

## §PB9 — Đợt nạp 2 kho space: SP1-001 + SP1-004 → 665 asset + DNA 3-draft (2026-07-07)

- **Nạp:** SP1-001 125/125 (125 clip phiên trước cắt sẵn — chỉ tag) · SP1-004 257/257
  (cắt mới 257 clip). Bỏ khi đọc draft (đúng luật ống nạp):
  SP1-001 thiếu file 2 · trùng 3; SP1-004 thiếu file 6 · quá ngắn 2 · trùng 5.
  2 pass vớt lỗi mạng (SSLEOF do 2 job giành key + mạng lẻ) vớt 15; **3 cảnh lì tag TAY**
  qua đúng ống `ingest_draft` (tiền lệ PB4 aliens; ManualTagger chỉ nhận 3 path định trước,
  path lạ raise): rush-hour NYC (urban_street/wide/tense) · Sun_nohw 9
  (space/extreme_close_up/epic+dark) · electricity-substation (other/aerial/serious).
- **Sự cố đã xử:** job ingest SP1-001 phiên TRƯỚC còn sống sau clear chat → 2 process
  cùng tag + giành 3 GLM key (nhiều SSLEOF oan). Db KHÔNG hỏng: UNIQUE(path) + resume
  gộp kết quả, soát 0 dòng trùng. Bài học → memory `leftover-background-job-check`
  (soát process sót trước khi chạy job nền dài).
- **DNA 3-draft vs 1-draft (PB5 đã duyệt — GIỮ cả 2 artifact để so):**
  | Số đo | PB5 (1 draft) | PB9 (3 draft) | Đọc |
  |---|---|---|---|
  | Cut/phút | 8,3 | 7,8 | ỔN ĐỊNH ✓ |
  | Trung vị shot | 6,98s | 6,2s | ổn định |
  | Trung vị ô thở | 1,5s | 1,57s (1,82 ô/phút) | ỔN ĐỊNH ✓ |
  | Hold ≥5s | 81% | 67% | giảm vừa |
  | Wide | 79% | 59% | **đổi mạnh** — kho đa cỡ cảnh hơn |
  | Close-up | 1/39,3 shot | 1/8,3 shot | **đổi mạnh** |
  | Hook 45s trung vị | 8,75s (n=6!) | **4,8s (n=25)** | **ĐẢO CHIỀU** — hook NHANH hơn thân → mâu thuẫn "hook chậm vs heuristic hook nhanh" ở MO_TA_DNA_D1 §3 TỰ TAN (n=6 quá mỏng, đúng lý do user đòi ≥3 draft) |
  | Lệch chuẩn shot | 3,11s | **32,94s** | **VỠ vì outlier** — xem dưới |
  | Chủ thể chữ ký | galaxy/nebula/stargazing | +sun/solar system/space probe/solar flare | SP1-004 chuyên Mặt Trời — kho rộng chủ đề hơn |
- **✅ USER CHỐT LUẬT OUTLIER (2026-07-07): shot >30s BỎ QUA không đếm, MỌI niche.**
  (Bối cảnh: mega-segment **839s** — clip compilation `SPACE-01 p2` SP1-001 — thổi std
  3,11→32,94s → validator Mảnh B sẽ kêu oan "đều tăm tắp" với mọi video bình thường.)
  Code: `dna.py::MEGA_SHOT_S = 30.0` — shot >30s không vào shot_len/hold/quarter/hook,
  ĐẾM RIÊNG `pacing.mega_segments {n, total_s}` (không mất dấu); `cuts_per_min` tính trên
  thời lượng ĐÃ TRỪ mega (14 phút compilation không phải nhịp cắt); CLI in dòng
  "Mega-segment >30s: N khúc" khi có. Regression test tái hiện bug 839s
  (`test_compute_dna_excludes_mega_segments`). FULL pytest **240/240**.
  **Số sạch (artifact + dna.json đã chạy lại):** std 32,94 → **3,09s** (≈ PB5 3,11 —
  nhịp cắt space ỔN ĐỊNH thật qua 3 draft); cut/phút 7,8 → **9,4**; trung bình shot
  7,94 → 6,65s; các trung vị giữ nguyên. Validator hết nguy cơ kêu oan.
- **✅ USER CHỐT TIẾP (2026-07-07): ô thở >60s BỎ QUA như shot, mọi niche** (đóng còn-ngỏ
  d2 ngay trong ngày). Code: `MEGA_BREATH_S = 60.0` — gap >60s không vào thống kê d2
  (kể cả footage-trong-ô-thở + shot/ô), đếm riêng `breathing.mega_windows`; CLI in dòng
  riêng. Regression `test_compute_dna_excludes_mega_breath_windows`. FULL **241/241**.
  Số sạch: mean ô thở 10,81 → **3,11s** · max 842 → 57,7s · trung vị 1,55s (ổn định).
  Artifact + dna.json đã chạy lại lần cuối.
- **Verify:** db đếm 665 = 237 (SP1-003) + 46 (folder rời) + 125 + 257; 0 path trùng;
  dna.json sinh tự động bởi code DNA-D1.B (lần chạy production đầu tiên ✓).

---

## §DNA-D1.B — Consumer DNA đầu tiên, đợt 1: dna.json + pacing validator Mảnh B (2026-07-07)

- **Cái gì đổi:** theo `MO_TA_VAN_HANH_DNA_D1.md` ĐÃ DUYỆT (câu 1-2 user chốt: kích hoạt
  ≥3 draft + DNA niche THẮNG heuristic chung khi vênh; câu 3-4 user ủy quyền: GIỮ ngưỡng
  §2c + làm B TRƯỚC A SAU). Code đợt 1 (4 file):
  1. `library/dna.py` + 3 hàm thuần: `save_dna` (ghi `<niche>/dna.json` kèm measured_at +
     source_drafts) · `load_dna` (thiếu/hỏng → None, fail-open) · `check_pacing` (2 tín
     hiệu §2c: đều-tăm-tắp std < ½ DNA · mật độ ngoài [½×, 2×] DNA → 0-2 dòng cảnh báo).
  2. `cli.py::library-dna` bước cuối gọi `save_dna` (đóng "còn ngỏ (4)" §PB5).
  3. `project.py::Project` + field `niche` (Optional, project cũ load bình thường);
     `sourcer/runner.py::run_source` ghi `project.niche = niche or None` (NT1 truy vết).
  4. `packager/assembler.py`: `_place_video_l1` trả bool → gom shot THỰC ĐẶT trên video_l1
     (`placed_shots`) → `_warn_pacing_dna` cuối assemble so với dna.json → `record.warnings`
     (report.html tự hiện qua ống có sẵn `report/runner.py:185`). Bọc try/except: validator
     phụ lỗi gì cũng chỉ ra 1 dòng cảnh báo, KHÔNG bao giờ chặn assemble.
- **Vì sao:** DNA PB5 đang nằm chết trong bảng đọc tay — đây là consumer đầu tiên làm nó
  LÀM VIỆC. B trước A: B chỉ-đọc, 0 chồng chéo (rà 5 tầng trong MO_TA §3); A đụng prompt
  NÃO nên chờ B qua cổng mắt + dna.json 3-draft (PB9).
- **Vùng ảnh hưởng đã rà (P5):** `_build_content`/`_place_video_l1` chỉ 1 caller (grep);
  chỉ 1 chỗ add_segment "video_l1" nên placed_shots không sót nguồn nào; field `niche` mới
  — pydantic default None nên project.json cũ load nguyên; `library-dna` thêm side-effect
  ghi file (mkdir parents, niche gõ sai chỉ tạo folder rỗng vô hại); tests dùng db/library
  tmp_path — chạy song song ingest PB9 an toàn.
- **Verify:** FULL **239/239** (6 test mới: round-trip dna.json · load thiếu/hỏng→None ·
  2 tín hiệu kêu đúng · sạch/suy-biến im lặng · integration run_assemble thật ra đúng 2
  cảnh báo qua env AUTOEDIT_LIBRARY_ROOT; +2 assert niche trong test_sourcer).
  **Cổng mắt (chưa qua):** dựng 1 video space thật → user đọc cảnh báo trong report —
  "số này giúp hay nhiễu".
- **Còn ngỏ:** (1) Mảnh A (nạp khối DNA vào direct-context L2b sâu) — đợt riêng, sau cổng
  mắt B; *(→ ĐÃ LÀM 2026-07-08, xem §DNA-D1.A)* (2) dna.json space hiện CHƯA tồn tại —
  sinh tự động khi chạy B9.4 `library-dna` 3 draft; (3) ngưỡng §2c đặt lỏng chủ ý —
  siết/nới sau vài video thật.

---

## §DNA-D1.A — Consumer DNA đợt 2: khối CHỮ KÝ PACING vào direct-context (2026-07-08)

- **Cái gì đổi:** theo `MO_TA_VAN_HANH_DNA_D1.md §6` (chi tiết thi công, user DUYỆT
  2026-07-08 kèm điểm lệch §6b):
  1. `director/live.py::dna_block(niche, library_root=None)` — cùng khuôn `vocab_block`
     C4: in LIVE từ `<library>/<niche>/dna.json` qua `load_dna` (tự mới sau mỗi
     `library-dna`), fail-open 3 nấc (không niche / không dna.json / JSON hỏng hoặc số
     suy biến → `""`). Nội dung: 4 dòng số (cut/phút kèm ngưỡng validator Mảnh B sẽ soi
     · shot trung vị±std · hold ≥5s · hook45, chữ NHANH/KHÔNG-nhanh in ĐỘNG theo so sánh
     hook vs thân) + luật "DNA niche thắng heuristic" + **câu cấm §6b: KHÔNG chỉnh hình
     thở theo khối này** (thay cho dòng ô thở bị BỎ — 1,81 ô/phút đếm cả vi nghỉ mà máy
     hình thở 3.0 đã tự lo, in ra sẽ ngược chiều "ÍT nhưng SÂU").
  2. `build_direct_context` chèn khối SAU từ vựng kho, TRƯỚC "## OUTPUT". 0 đổi CLI —
     dùng chung `--niche`/`eff_niche` của C4; echo thêm dòng "DNA pacing: ✓/—".
- **Vì sao:** NÃO được lái TRƯỚC bằng đúng số mà validator Mảnh B đo SAU (cùng đọc 1
  dna.json, cùng chiều) — thay vì chỉ bị cảnh báo hậu kiểm.
- **Vùng ảnh hưởng đã rà (P5):** `dna_block` chỉ 1 caller (`build_direct_context`);
  consumer của context = phiên sống + skill /dung-video (đọc file, thêm khối = thêm tri
  thức, không đổi schema output); **test cũ `test_direct_context_vocab_block_fail_open`
  gọi `niche="space"` sẽ ăn dna.json THẬT từ F: trên máy này → thêm env
  AUTOEDIT_LIBRARY_ROOT=tmp_path cách ly** (cùng pattern test_assembler); đường `direct`
  cũ không đụng (vẫn thiếu vocab+DNA — còn ngỏ chung từ C4).
- **Verify:** FULL **286/286** (1 test mới `test_direct_context_dna_block_fail_open`:
  fail-open 3 nấc + đủ 4 dòng số + câu cấm §6b + thứ tự vocab→DNA→OUTPUT). Smoke thật:
  `direct-context` project M2 --niche space → khối in đúng số F: (9.4 cpm · 6.2±3.09s ·
  67% · 4.8s NHANH). **Cổng mắt (chưa qua):** đi ké video MỚI fresh direct — user đọc
  khối + xem video, phán "giúp hay nhiễu". Claude không tự báo đạt.
- **Còn ngỏ:** hằng trong khối là số đọc — nếu sau đợt nạp viral DNA đổi mạnh, chỉ cần
  chạy lại `library-dna` là khối tự mới, không sửa code.

---

## §C8-NAP — Gói NẠP viral: luật bản quyền nướng vào clip lúc nạp (2026-07-08)

- **Cái gì đổi:** theo `MO_TA_VAN_HANH_C8_NAP.md` (user DUYỆT 2026-07-08 "duyệt theo ý bạn"):
  1. `library/ingest.py`: `MIN_SCENE_S` 1.0→**2.0** (c8 luật 6 — MỌI mẻ nạp) · hằng
     `VIRAL_MAX_S=10 / VIRAL_SAFE_S=6 / VIRAL_ZOOM=1.12` · `DraftScene.source_duration`
     (đọc từ material duration của draft) · `ingest_draft(source_class=)`: viral bóp cảnh
     >10s còn 6s KHÚC GIỮA (start dịch (dur−6)/2, đếm `stats["squeezed_6s"]`) ·
     `cut_scene(zoom=)` + `_zoom_vf` (crop tâm /1.12 + scale về ~cỡ gốc số chẵn, NƯỚNG
     vào clip cả video lẫn ảnh) · `scene_clip_name(zoom=)` → suffix `_z112` (đổi % zoom
     = tên mới = cắt+tag lại, không tái dùng clip zoom cũ).
  2. `library/db.py`: 2 cột mới `source_class TEXT DEFAULT 'own'` + `source_duration REAL`
     (schema + `_migrate` idempotent — 665 asset cũ TỰ thành own, 0 dòng migrate) ·
     `upsert_asset` CASE-preserve 2 cột theo `excluded.source_video=''` (re-index thường
     KHÔNG lật viral→own) · hằng `_NO_VIRAL` gắn vào 4 hàm: `search_assets` (phễu local)
     / `videos_for_niche` (pool shot thở) / `signature_assets` / `vocab_for_niche`
     (TỪ VỰNG KHO — không dạy NÃO đồ chưa dùng được).
  3. `library/dna.py`: thống kê kho c6/c7 cùng filter `_NO_VIRAL` (phân bố khớp pool).
  4. `cli.py library-ingest`: `--source-class own|viral` (validate) + dry-run in số bóp
     + echo "Viral c8: bóp X · zoom 112% · fail-safe chưa vào phễu".
- **Vì sao:** luật an toàn pháp lý (kênh không bị đập gậy bản quyền) đứng TRƯỚC luật chất
  lượng; nướng 1 lần lúc nạp = mọi consumer sau hưởng sẵn, không xử lý lại ở assembler.
  Luật 3 (cấm cảnh liền kề) + luật 5 (trần 8%) = gói CHỌN riêng — dữ liệu đã đủ từ gói
  này (`source_video/scene_index/source_duration`), KHÔNG cần nạp lại.
- **Vùng ảnh hưởng đã rà (P5):** đổi chữ ký `cut_scene` → 2 fake trong test cập nhật cùng;
  `index_niche` re-scan folder `nap/` = tầng nguy hiểm nhất (âm thầm lật nhãn) → chặn bằng
  CASE-preserve + regression riêng; `read_timeline`/DNA pacing đọc MỌI segment nên sàn 2s
  không lệch DNA (nhưng CẤM đưa draft viral vào `library-dna` — nhịp tách cảnh ≠ nhịp dựng);
  `paths_for_niche`/prune GIỮ mọi class (dọn file chết phải thấy viral); filter-overload-guard
  nguyên vẹn (fail-safe là loại theo class tạm thời, không phải veto chất lượng thứ 3).
- **Verify:** FULL **291/291** (5 test mới: sàn 2s tái hiện bug sàn-1s-cho-qua · zoom vf+tên
  clip+own-không-đổi · bóp 6s giữa+nhãn db+own untouched · fail-safe 4 hàm · chống lật nhãn).
  **Mẻ thử thật Destiny - Solar System 45 cảnh:** dry-run khớp quét (46 cảnh <2s bỏ trước
  vision), lỗi 0 (1 lỗi tag GLM mood 'intense' ngoài vocab 19 từ → resume tự đậu), 2 clip
  bóp 6s đúng số học (scene 41: 292,5s · scene 45: 320,5s), ffprobe 852×478 ≈ nguồn
  854×480 / yuv420p / 30fps CFR, db thật: 45 viral (source_duration 724s đúng) + fail-safe
  sạch 3 đường (search 0 viral · pool thở 641 video 0 viral · vocab = 665 own). **Cổng mắt
  (chưa qua):** user mở 3–4 clip kiểm logo mất chưa / khúc giữa tự nhiên — Claude không tự báo.
- **Mẻ nạp full 9 draft (2026-07-09, 69 phút + vá lỗi):** 1209 asset viral / kho space 1874.
  Từng draft (cảnh vào · bỏ <2s · bóp 6s): Anomalies 122·1·52 — Astrum Pluto 155·5·41 —
  Astrum Sun 113·3·21 — Astrum Jupiter 168·5·45 — Destiny 97·46·6 — Hubble 132·4·15 —
  Kosmo 85·3·11 — NASA PLUTO 119·52·14 — Bigbang 218·36·21. 6 lỗi → 0: 1 clip cụt
  moov-atom (kill job giữa lúc ffmpeg ghi → `cut_scene` tái dùng file >0 byte; rà cả folder
  chỉ 1 clip, xóa + resume cắt lại) · 1 retry đậu · 4 clip GLM lì mood ngoài vocab
  (cold/analytical/educational) → **tag TAY tiền lệ PB9**: Claude rút frame giữa, xem, tự
  điền tag qua đúng ống (đo màu/meta code thuần + provenance tính lại từ draft, script
  `tag_tay_4clip.py`). **Sự cố `0709`:** job quét-folder nuốt nhầm draft kiểm-tra-mắt của
  user (10 material = clip kho) → dừng kịp, dọn 10 clip zoom-chồng-zoom + 10 dòng db;
  luật mới: mẻ nạp chỉ định danh sách draft tường minh, KHÔNG quét folder.
- **Còn ngỏ:** gói CHỌN (gate liền kề + trần 8% cộng dồn MỌI đường dùng kể cả shot thở +
  điểm rải mềm) — mô tả vận hành riêng TRƯỚC lần dựng đầu dùng viral. Nguồn 480p (cả 9
  file gốc 854×480, F5 sàn phân giải chỉ áp ẢNH): đã nêu 2 đường (tải lại 1080p re-ingest
  vs chấp nhận) — **user CHỐT 2026-07-09: CHẤP NHẬN 480p**, lý do tỉ lệ footage viral
  trong 1 video không nhiều; nếu sau này chê mềm thì tải 1080p đè tên cũ + xóa nap folder
  viral + re-ingest (~$1,2/69', draft tách cảnh dùng lại nguyên).
  1 nguồn = 1 draft tách cảnh (2 draft cùng nguồn làm scene_index đánh lại từ 1).
  `cut_scene` tái dùng file >0 byte kể cả file cụt — nếu còn kill job giữa chừng, rà
  moov-atom folder đang cắt dở. [[viral-copyright-cut-rules]]

---

## §D1-BACKUP — Backup kho F: sang ổ vật lý khác (2026-07-09)

- **Cái gì đổi:** không đổi code — hạ tầng. 2 lệnh robocopy `/E /COPY:DAT /DCOPY:T /MT:8`:
  1. `F:\AutoEdit\library` → `D:\AutoEdit_backup\library` — 1914 file / 5,10 GB, 0 fail.
  2. `C:\Users\NBPC\AutoEdit` → `D:\AutoEdit_backup\AutoEdit_C` — 64 file / 249 MB
     (cache.db 77 MB + music/sfx + machine.json — backup trọn folder thay vì mỗi cache.db
     theo scope gốc, vì chỉ thêm ~170 MB mà đủ luôn nhạc/SFX đã tải).
- **Vì sao:** kho 1874 asset space (own + viral, tag vision đã trả tiền) đang CHỈ 1 BẢN
  từ khi xóa `library.pre-F-backup` trên C:. Mất F: = mất trắng. **Phát hiện quan trọng
  khi chọn đích: E: và F: là 2 partition CÙNG 1 ổ WD HDD 3,7 TB (Disk 0)** — backup
  E:↔F: không chống được chết đĩa. D: nằm trên NVMe Kingston (Disk 1, cùng đĩa C:),
  trống 457 GB → đúng nghĩa ổ vật lý khác. S: là NAS Synology công ty — đích tốt hơn nữa
  (chống mất cả máy) nhưng là kho chung, chưa tự ý ghi; user muốn thì copy thêm 1 lệnh.
- **Verify:** parity `Get-ChildItem -Force` 2 phía KHỚP từng byte (library
  5.477.181.763 B / AutoEdit_C 261.543.150 B) · cache.db bản backup mở read-only
  `PRAGMA integrity_check` = **ok**, 3 bảng đọc được (library_assets 9282 · asset_usage
  2226 · search_cache 2283). Trước khi copy db sống: kiểm process nền sót theo memory
  [[leftover-background-job-check]] — sạch, không job ffmpeg/ingest nào đang ghi.
- **Còn ngỏ:** backup là SNAPSHOT chết — sau mỗi mẻ nạp lớn (viral đợt 2, niche mới)
  chạy lại đúng 2 lệnh robocopy trên là xong (incremental, chỉ copy file mới/đổi; muốn
  xóa file thừa ở backup theo nguồn thì đổi `/E` → `/MIR`). Chưa đặt lịch tự động —
  kho đổi theo mẻ nạp chứ không đổi hằng ngày, chạy tay sau mẻ nạp là đủ.

---

## §D4-D5 — Quyết định user: BỎ D4 (xóa ANTHROPIC_API_KEY) + HOÃN D5 (git) (2026-07-09)

- **Cái gì đổi:** không đổi code — cấu hình + ghi chép:
  1. Xóa `ANTHROPIC_API_KEY` (hết hạn 401) khỏi `autoedit/.env`, thay bằng comment giải
     thích; `.env.example` + `autoedit/CLAUDE.md` Bước 4 sửa theo (bỏ khỏi template setup).
  2. CLAUDE.md gốc P4: dòng "KHÔNG dùng git" thêm "xác nhận lại 2026-07-09" + mốc khôi
     phục bổ sung backup D:.
  3. `DINH_HUONG_VIEC_TIEP_THEO.md`: D4 → BỎ, D5 → HOÃN, cả hai ghi "KHÔNG hỏi lại user".
- **Vì sao:** user hỏi "hệ có cần key không, chưa cần thì xóa để lần sau đỡ hỏi lại".
  Rà consumer (P5) xác nhận KHÔNG cần: NÃO đi Claude Code subscription (`cc_client.py:104`
  còn chủ động pop key khỏi env con để ép subscription), vision production đi GLM. Key chỉ
  phục vụ 2 fallback chưa dùng: `--engine api` (`director/client.py:82`) + `--engine claude`
  (`library/vision.py:358`) — và key đã chết 401 từ PB8 nên fallback vốn không chạy được.
  D5 git: user "chưa muốn commit lên github vội" → giữ nguyên luật KHÔNG git 2026-07-03.
- **Vùng ảnh hưởng đã rà (P5):** grep toàn codebase `ANTHROPIC_API_KEY|anthropic` — ngoài
  2 fallback trên chỉ còn: `test_cc_client.py` (tự set key giả bằng monkeypatch, không đọc
  .env) + uv.lock/pyproject (dependency `anthropic` GIỮ NGUYÊN — 2 fallback vẫn import
  được, chỉ thiếu key khi gọi thật). Không nơi nào crash vì key vắng mặt lúc load .env
  (python-dotenv chỉ nạp biến có mặt).
- **Verify:** FULL pytest sau khi xóa key (xem số ở dòng bảng) — chứng minh không test nào
  phụ thuộc key trong .env.
- **Còn ngỏ:** nếu sau này cần fallback `--engine api`/`--engine claude` → user cấp key
  mới điền lại 1 dòng `.env` là xong (5 phút).
- **CẬP NHẬT CÙNG NGÀY:** phần D5 của entry này hết hiệu lực — user nói rõ đã hiểu nhầm
  D5 = "commit lên GitHub tốn thời gian"; khi rõ là git LOCAL trên máy → user đề nghị mở
  lại. Đã bật: xem §D5-GIT (commit gốc `890c68b`, KHÔNG remote/push).

---

## §D5-GIT — Bật git LOCAL làm mốc khôi phục (2026-07-09)

- **Cái gì đổi:** `git init` tại root `tool edit padoma` + `.gitignore` mới (loại `.env`
  chứa key Pexels/GLM/Google/Serper · `.venv` 590MB · `autoedit/projects/` 29,6GB output
  dựng video · cache pytest/pycache) → commit gốc **`890c68b`**: 173 file / 42.646 dòng
  (toàn bộ code autoedit + tests + 18+1 foundation + docs mô tả vận hành + NHAT_KY +
  capcut_test + voice test travel). Identity local repo: `PADOMA <padoma.content8@gmail.com>`
  (không đụng git config global của máy). **CLAUDE.md P4 sửa luật:** "KHÔNG dùng git" →
  "git LOCAL đã bật: commit mốc sau mỗi milestone; KHÔNG remote, KHÔNG push GitHub".
- **Vì sao:** user từng tắt git 2026-07-03 và sáng nay hoãn D5 — hóa ra do hiểu nhầm D5
  là commit lên GitHub (chậm, phải upload). Làm rõ: git local chỉ ghi mốc trên ổ C:, vài
  giây, không mạng → user đề nghị mở lại. Điểm khôi phục giờ có 3 tầng: NHAT_KY (ngữ
  cảnh) + git local (code/docs từng mốc) + backup D: (kho footage + db).
- **Vùng ảnh hưởng đã rà (P5):** `.gitignore` chỉ ảnh hưởng git, không đụng runtime;
  kiểm staged TRƯỚC commit: không có `.env`/`.venv`/`projects/`, file lớn nhất 5,1MB
  (voice test) — không nuốt nhầm media nặng; `autoedit/.gitignore` cũ (bê từ project gốc)
  vẫn nằm trong repo, không mâu thuẫn với `.gitignore` root.
- **Verify:** `git log --oneline` = 1 commit `890c68b` · `git status --short` sạch ·
  grep `git ls-files` không ra file nhạy cảm. pytest không cần (không đổi code).
- **Còn ngỏ:** thói quen mới cho MỌI phiên sau — xong milestone thì commit cùng lúc với
  cập nhật NHAT_KY. Backup kho F: (media/db) vẫn là robocopy D: — git không quản media.

---

## §D2 — Đường `direct` cũ ăn khối kho: vocab C4 + DNA Mảnh A vào pass 2 (2026-07-09)

- **Cái gì đổi:** 3 chỗ chạm + 1 test:
  1. `director/prompts.py::beats_system` — thêm tham số `library_context` (nối cuối
     system prompt pass 2, sau brief block).
  2. `director/runner.py::run_direct` — tính `vocab_block(niche)` + `dna_block(niche)`
     MỘT LẦN (niche = `inputs.channel`, import lười từ live.py vì live import ngược
     runner) → truyền xuống `_pass2_chapter` → `beats_system`.
  3. `director/live.py` — docstring ghi 2 hàm khối giờ phục vụ CẢ 2 đường.
  4. Test: `FakeClient` ghi thêm `systems` + `test_run_direct_pass2_gets_vocab_and_dna_blocks`
     (outline KHÔNG khối · pass 2 đủ CẢ 2 khối · ổn định giữa chương · fail-open không channel;
     cách ly db thật bằng monkeypatch `db.connect` + AUTOEDIT_LIBRARY_ROOT=tmp).
- **Vì sao:** từ C4/DNA-D1.A, đường sâu được dạy từ vựng kho + chữ ký pacing nhưng
  fallback `direct` cũ (cũng là xương L1 batch sau này) vẫn mù kho → NÃO viết query
  "ngôn ngữ Pexels" + pacing heuristic. Giờ 2 đường cùng đọc 1 nguồn (db.vocab_for_niche
  + dna.json) — kho đổi thì cả 2 tự mới, không sửa 2 nơi. CHỈ pass 2 vì đó là nơi duy
  nhất quyết queries.local + độ dài beat/shot_count; pass outline không viết query,
  không đặt độ dài — nhét thêm chỉ tốn token/nhiễu.
- **Vùng ảnh hưởng đã rà (P5):** consumer `beats_system` chỉ có runner (grep);
  `run_direct` có 2 caller — `cli.direct` + `cli.run` (pipeline full, vết bug B2) — cả 2
  tự hưởng qua `inputs.channel`, 0 đổi chữ ký; test cũ chạy channel rỗng → fail-open,
  không phải sửa test nào; vocab_block tự mở db.connect() mỗi lần direct (y hệt hành vi
  direct-context khi không truyền conn — nhất quán); cùng-pattern đã soát: pass enrich
  KHÔNG cần khối (không viết query stock/local, không quyết pacing) — chủ đích bỏ qua.
- **Verify:** FULL pytest **297/297** (1 mới). Smoke dữ liệu THẬT: vocab in
  "1874 asset: 1850 video / 24 ảnh" + DNA "3 draft — 82.6 phút · 643 shot", outline
  pass sạch khối. Cổng mắt: không cần riêng — khối là đúng nội dung đã qua cổng mắt
  SP012 (đường sâu); đường cũ chỉ ăn ké khi fallback/L1.
- **Còn ngỏ:** pass outline không có khối (chủ đích — mở lại nếu sau này muốn NÃO chia
  chương theo hook45 DNA). L1 batch (B2) sau này dùng run_direct là hưởng sẵn.

---

## §V123 — Gói nâng cấp V1+V2+V3 từ 3 vấn đề SP012_V2 (2026-07-09)

- **Cái gì đổi:** theo `MO_TA_VAN_HANH_NANG_CAP_V123.md` (user duyệt trọn gói + 4 điểm
  ủy quyền cùng ngày). 3 milestone code, mỗi cái 1 commit git:
  1. **V1 (`16e278b`)** — `transcode.py`: `ffprobe_dims` + `crop_16x9_vf` (cắt TÂM,
     ngưỡng 3%, ép chẵn) + `cover_scale`; `normalize_video(-vf crop)` với cờ
     `crop_16x9=False` cho 2 caller asset tự render (chart PiP 1920×1080 + info-card
     DỌC 960×1080 — **P5 catch trong lúc code: quên cờ này là crop vỡ card**).
     `assembler._place_video_l1`: ảnh không crop file — Ken Burns `cover→cover×zoom`,
     ảnh ngắn scale tĩnh `ClipSettings`; ảnh 16:9 cover=1.0 y hệt cũ.
  2. **V2 (`9352b61`)** — prompt-only: `_SOURCING_RULES` + `foundation/c1` thêm 3 nhóm
     entity (máy móc/phương tiện ĐƯỢC ĐẶT TÊN · sự kiện thật chương trình có tên ·
     thiên thể/địa hình đích danh có ảnh thật) + ngân sách theo niche (đời sống 0-1,
     facts 3-8); địa danh Trái Đất vẫn cấm. Memory `video-first-routing` sửa cùng.
  3. **V3 (`9fa10e2`)** — `Outline.video_subject` (PHẠM VI, đa chủ thể OK, default ""
     fail-open); `outline_system` + `## OUTPUT` direct_context yêu cầu điền;
     `RANK_SYSTEM` veto thuc_the_sai + sai thiên thể + "action/pose similarity does
     NOT redeem"; wiring `sourcer/runner` → `rank_batch`/`rank_beat` → 2 build prompt.
- **Vì sao:** 3 vấn đề user THẤY BẰNG MẮT ở draft SP012_V2, mỗi cái đã truy ra gốc bằng
  dữ liệu: (1) 44/442 asset lệch 16:9 (Pexels điện ảnh 2:1–2.9:1) → viền đen; (2) luật
  entity viết cho niche đời sống chặn máy móc/sự kiện thật của space; (3) rank_log b11:
  NÃO biết "sao Hỏa" từ slug mà vẫn chấm 8/10 vì veto không có "sai thiên thể" + thiếu
  phạm vi video. Thiết kế 3a đổi theo lo ngại user: video_subject = PHẠM VI, neo phán
  vẫn là central_subject CHƯƠNG → video đa hành tinh không bị veto oan.
- **Vùng ảnh hưởng đã rà (P5):** bảng 12 tầng trong mô tả; thêm 2 catch lúc code:
  info-card/chart qua normalize_video phải tắt crop; test e2e Ken Burns dùng ảnh 4:3
  (320×240) nên assert start-scale đổi 1.0→cover 4/3 (đúng thiết kế, không phải vỡ).
  3c vision gate KHÔNG code — dời C đợt 5 kèm nguyên tắc: chỉ soi top-pick, demote thử
  1 lần, cạn lấy best + warning (user: "quá khó thì bỏ, editor chỉnh tay").
- **Verify:** FULL pytest **302/302** (V1 +3: ngưỡng/tâm/chẵn + cover + cờ crop; V3 +2:
  prompt/veto wording + wiring qua run_source — họ bug "niche rơi"). Cổng số M1: norm
  clip test 320×240 → 320×180 đo bằng ffprobe.
- **Còn ngỏ:** 🔄 **M4 video kiểm — cổng MẮT user, Claude không tự báo đạt.** Lưu ý khi
  chạy: project cũ phải XÓA `media/norm/` mới ăn crop V1; V2+V3a chỉ thể hiện ở video
  đạo diễn MỚI (SP012 re-source giữ outline cũ → chỉ kiểm được V1+V3b). Backlog: ffmpeg
  `cropdetect` viền-nướng-trong-pixel cho MẺ NẠP viral sau.
- **M4 THI CÔNG (cùng ngày — user chốt "test ~10 phút, đủ cả V1/V2/V3"):** input =
  voice SP012 cắt tại ranh giới chương gần 10' (word 1302 = 555,2s, kết trọn câu; script
  = join transcript[0..1302]) → project `script-20260709-071612` --channel space.
  **Phát hiện quan trọng: đường `direct` cũ CHẾT với chương dài** — chương 2 (~424 từ,
  ~40 beat/call) vượt trần 600s của subprocess `claude -p` cả 3 attempt (mỗi attempt
  10' → stage fail sau ~30'). Đường SÂU không sao (phiên sống không giới hạn) → còn ngỏ
  cho L1/B2: bump timeout HOẶC chẻ chương >N từ thành nhiều call. Chuyển đường sâu:
  em đạo diễn 95 beat/4 chương (8 entity V2: Orion·walkout·SLS·crew·farside-LRO·Luna 3·
  Apollo 8·Chang'e-4 + video_subject V3 + 2 chart + 1 info-card + text_sequence + câu
  đinh [1290]) — **ingest PASS lần đầu**, cut 66 seg (+59,5s DNA thở), source 95/95
  0 needs_human (phễu: 1091 ứng viên · chết kỹ thuật 3% · veto nghĩa 5% · local-first
  76/87 beat có kho trong pool, thắng 15 · viral 14 cảnh/7 nguồn gate chặn 57 · entity
  8/8 ảnh THẬT licensing_flag đủ) → draft `SCRIPT_20260709_071612` + report.html.
  **Cổng SỐ V123 đạt:** norm 104/104 video 16:9 (còn lại duy nhất file dọc 960×1080 =
  info-card — ĐÚNG thiết kế giữ khung) · outline.video_subject điền + chảy vào phễu ·
  Ken Burns 8 ảnh (echo CLI vẫn in "100%→X%" theo zoom tương đối — cosmetic, keyframe
  thật đã cover→cover×zoom) · DNA validator im ĐÚNG.

---

## §C-DOT-1 — C đợt 1: C6 drop-list + C3 so màu cảnh báo + C7 lệnh pause-dna (2026-07-09)

- **Cái gì đổi:** theo `MO_TA_VAN_HANH_C_DOT_1.md` (user duyệt hướng trước khi code:
  C6 chốt "Cách 1 — Drop-list" · C3 chỉ-cảnh-báo · C7 đồng ý đề xuất). 3 mục, mỗi mục
  1 commit mốc, thứ tự C6 → C3 → C7:
  1. **C6** — `sourcer/local.py::_strip_motion_terms` + `_MOTION_PHRASES`/`_MOTION_WORDS`:
     bỏ từ camera/chuyển-động ("rotating", "timelapse", cụm "zoom out"...) khỏi query
     TRƯỚC khi `search_assets` AND-match (GLM tag từ frame TĨNH — kho không bao giờ có
     mấy từ này, PB8 2b). Bỏ sạch token → giữ query gốc. CHỈ đường kho local (tier
     local+specific); Pexels + lệnh debug `library-search` giữ thô; KHÔNG sửa prompt
     NÃO kèm (né 2-tầng-cùng-quản §6b DNA Mảnh A). 1 assert test cũ đổi CÓ CHỦ ĐÍCH
     (nó tài liệu hóa đúng bug PB8 "== []").
  2. **C3** — `sourcer/colorcheck.py` mới + gọi cuối `run_source` (fail-open try/except):
     đo V/S/hue mọi footage đã chọn (shots + extra + breath; đo trực tiếp file assets/
     bằng `preview_images`+`measure_colors` sẵn có — 1 điều kiện đo thống nhất). Outlier
     = 2 điều kiện ĐỒNG THỜI: |ΔV|≥0,25 / |ΔS|≥0,30 **và** robust z = |Δ|/MAD ≥ 3,5;
     hue ≥60° so tông chủ đạo leave-one-out (R≥0,5). Chương <3 footage bỏ qua. CHỈ ghi
     `record.warnings` — không điểm, không veto.
  3. **C7** — `library/pause_scan.py` + CLI `autoedit pause-dna <niche> --draft ...
     --script ... [--language] [--force]`: adapt `learn_pause_dna.py` (CỨU từ scratchpad
     phiên 632c11ff trước khi Windows dọn Temp — giờ nằm ở project root + đã vào git),
     rows/holes/reconcile GIỮ NGUYÊN thuật toán; MỚI: montage ≥4 nhát hoặc >20s (thay
     lọc phăng ≥8s), tách lớp thở hold≤1,2+footage≥1,5, xuất `pooled.breath` đo được
     (anchors cần ≥5 ô; k_thresholds/k_fractions/min_piece KHÔNG xuất — loader fallback
     hằng space, in `k_dist` cho người xem = backlog §6.5 "đo phân bố k"), guard không
     đè bản duyệt (ghi `pause_dna.new.json`; `--force` backup rồi đè). Cache transcript
     16 file cứu về `F:\AutoEdit\library\space\pause_scan_cache\` (mất là tốn ~25').
- **Vì sao:** bước 1 lộ trình "D → C có nhịp thở → scale" user chốt. C6 = footage nhà
  có sẵn mà đi tải Pexels (PB8 đo 3 query trượt oan); C3 = 2 ví dụ lỗi màu user nêu ở
  b1; C7 = scan DNA đang là script 1 lần nằm folder tạm, niche 2 (B3) sẽ cần lệnh.
- **Verify:** pytest **317/317** (C6 +2 · C3 +8 · C7 +5, FULL suite sau mỗi mục) ·
  **C6 cổng số:** benchmark PB8 24 query re-run trên kho 1874 asset — `spiral galaxy
  rotating` 0→80 · `stars timelapse` 0→604 · `universe zoom out` 0→742 · `astronaut
  floating` 2→19 · **20 query khác TRƯỚC=SAU không đổi 1 số** (ghi PB8 §D) · **C3 cổng
  số:** dry-run project `script-20260709-071612` thật: 110 footage/4 chương/35s → 8 cảnh
  báo (lần đầu 53 → thêm điều kiện MAD; toàn ca đáng ngờ thật: clip sáng lọt chương tối,
  lệch tông 210° vs 51°...) · **C7 regression:** chạy lệnh trên đúng 3 draft SP1 (cache
  hit 16/16, 0 transcribe) — `pooled.kinds` + `holes` + per-project **khớp TUYỆT ĐỐI**
  bản `pause_dna.json` hiện hành (verified 97/102 · 205/213 · 140/149 y §HOC-DNA-NHIP);
  guard chạy đúng (bản duyệt nguyên vẹn, số thô ra `.new.json` — breath thô [1.7..12.1]
  vs bản duyệt [4.0..8.5] minh chứng block duyệt = đo + interview, guard là ĐÚNG thiết kế).
  **Cổng MẮT: ĐẠT 2026-07-09 qua video kiểm GỘP V3 (xem §KIEM-V3) — C đợt 1 ĐÓNG TRỌN.**
- **Vùng ảnh hưởng đã rà:** C6 — caller `search_assets` chỉ có find_local_candidates
  (pipeline, gồm viral-vào-phễu; gate ViralLedger chạy SAU nên không lách) + CLI debug
  (giữ thô) + tests; chỉ TĂNG recall, phễu/geo-gate/veto y nguyên. C3 — không quyết gì
  nên không lật/bị lật tầng mood nào (NÃO mood · phễu c5 · C5 vision tương lai); chạy
  sau mọi pick, không đụng P7/ledger/usage. C7 — tool offline; consumer load_pause_dna/
  load_breath_dna fail-open → test round-trip chống sai-schema-rơi-về-hằng-im-lặng.
- **Còn ngỏ:** (1) ~~video kiểm~~ ĐÃ DỰNG `SCRIPT_20260709_071612_V2` — cổng mắt user
  2026-07-09: C3 "không quan trọng lắm, editor thấy lệch tự thay" (b001/b019 oan-chấp-nhận
  -được) → GIỮ NGUYÊN warning-only, KHÔNG chỉnh ngưỡng, hạ ưu tiên "cho quyền trừ điểm"
  ở C đợt 5; C6 user nêu b60/b68 footage kho không hợp nội dung → ĐIỀU TRA XONG (xem
  §C6-DIEU-TRA dưới); (2) luật k shot thở vẫn hằng space — nạp thêm project editor rồi
  xem `k_dist` lệnh pause-dna in ra (backlog §6.5). Memory: [[c-dot-1-c6-c3-c7]].

### §C6-DIEU-TRA — b60/b68 footage kho sai nghĩa: C6 VÔ CAN, lỗi ở tầng TAG + phễu mù nguồn gốc (2026-07-09)

- **User nêu (cổng mắt V2):** b60 clip từ bài Pluto không liên quan Mặt Trăng; b68 clip
  "nhiều ngôi nhà dưới trời sao" không hợp concept kính thiên văn. Hỏi: phương pháp lấy
  từ kho có gì chưa tốt so với Pexels?
- **Truy vết b60:** query NÃO viết `moon dark`/`half lit moon` (KHÔNG có từ chuyển động
  → drop-list C6 không đụng). Clip `NASA - PLUTO__000166533_z112` được GLM tag lúc nạp:
  `subject: "moon"`, description *"Full moon against a dark night sky"*, tags [moon,
  lunar...] — **GLM nhìn 1 frame tĩnh khối cầu xám rỗ nửa sáng và đoán là Mặt Trăng**.
  AND-match trúng vì tag nói "moon"; phễu NÃO chỉ được xem description+shot_size+duration
  +source (prompts.py — KHÔNG có tên file/nguồn) → chấm "Cận cảnh Mặt Trăng — khớp trực
  tiếp"; veto sai-thiên-thể V3 không nổ vì nó đọc CHỮ, chữ nói moon. Sự thật duy nhất
  nằm ở TÊN NGUỒN `NASA - PLUTO` — tầng duy nhất không ai được xem.
- **Truy vết b68:** clip Destiny GLM tả "European Southern Observatory's telescopes
  under starry night sky" — mắt user thấy nhà dân. Cùng loài: tag vision đoán sai nội
  dung từ 1 frame.
- **C6 vô can — 3 bằng chứng:** (1) query 2 beat không có từ chuyển động, drop-list
  không đổi chúng; (2) **V1 (trước C6) cũng dính cùng loại lỗi**: đã pick PLUTO ở b033
  + b072, Destiny ở b054; (3) V1 rank_log b60: CHÍNH clip Pluto đó trong pool, NÃO chấm
  6/10 kèm ghi chú *"đúng thực thể"*(!) — thua chỉ vì P7 đã-dùng-chỗ-khác. C6 mở van
  local đúng thiết kế (15→21 pick) → loại lỗi tag-sai LỘ RA dày hơn, không phải C6 tạo lỗi.
- **Đây chính là ca "3c vision gate" đã dời về C đợt 5** (MO_TA V123 §V3-3c: "hình đỏ
  rực không có chữ mars") — kèm 1 lỗ mới phát hiện: phễu không được xem NGUỒN GỐC clip
  dù dữ liệu có sẵn (`source_video`/folder) và ở ca này slug TIẾT LỘ rõ.
- **Phương án đã trình user:** (a) đưa `origin=<tên video nguồn>` vào prompt phễu;
  (b) C5 vision gate giữ lịch đợt 5; (c) editor swap.
- **USER CHỐT (cùng ngày, sau khi hỏi rủi ro NÃO + cách chống tag nhầm tương lai):**
  **BỎ (a)** (lo NÃO xử thêm 1 biến — Claude đồng thuận: giá trị thấp vì chỉ là băng dán
  cho clip cũ, tệ nhất của (a) chỉ là rơi về Pexels nhưng không đáng rủi ro loại oan) ·
  **LÀM 2a+2b** vá prompt tag cho mẻ nạp TƯƠNG LAI · **kiểm tra + xử kho cũ đã tag nhầm**.
- **2a+2b ĐÃ CODE (commit `ceeb6f1`):** `_tag_instruction` thêm (2b) luật không-đoán-thiên-thể
  LUÔN bật (không chắc → 'planet'/'cratered surface'/'celestial body') + (2a) block
  `source_title` (tiêu đề FILE video nguồn qua kênh riêng TagJob → ingest; KHÁC folder
  ground-truth — tiêu đề = gợi ý chủ đề, tên vô nghĩa GLM tự bỏ). Comment cũ "tên project
  nguồn không phải ground truth" VẪN ĐÚNG cho folder_context — không đảo quyết định cũ.
- **CHIẾN DỊCH TAG LẠI KHO CŨ (user: "pluto mà tag mặt trăng thì xóa"):** quét db theo
  luật "tiêu đề nguồn nêu đúng 1 thiên thể ≠ thiên thể trong tag" (trừ earth — cảnh so
  sánh hợp lệ) → **102/1828 clip xung đột** (Jupiter→moon 16, Astrum-Pluto→moon 14...).
  KHÔNG xóa mù chữ 'moon' (video Jupiter có mặt trăng CỦA Jupiter thật) → tag lại 102
  clip bằng GLM + prompt mới (~$0,10): **92 ok lần 1 · 7 ok retry · 3 clip lì → PB9 tay**
  (Claude xem frame: 2 diagram giáo dục + 1 so-sánh Mặt Trăng/Io/Trái Đất — mood
  'educational' ngoài vocab là bệnh lì cũ). Kết quả: clip b60 `NASA - PLUTO__000166533`
  từ subject "moon"/"Full moon..." → **"celestial body"/"A small, cratered planet" +
  tag "Pluto"** — query `moon dark` không còn kéo nó vào beat Mặt Trăng. Xung đột từ-vựng
  còn 32/102 = mô tả TRUNG THỰC (Pluto and its moon **Charon** · diagram quỹ đạo nêu tên
  các hành tinh · sun flare thật) — spot-check xác nhận, KHÔNG xử thêm. Backup cache.db
  → D: đã làm mới sau chiến dịch (luật D1). Ca b68 (Destiny/ESO) KHÔNG thuộc lớp này
  (tiêu đề "Solar System" không nêu thiên thể — không có ground truth) → đúng lớp C5
  vision gate đợt 5 / editor swap.

## §KIEM-V3 — Video kiểm GỘP C đợt 1+2: SP012 10' bản V3 (2026-07-09)

- **Cái gì làm:** user chốt "dựng SP012 10' theo đề xuất" → re-source + assemble + report
  trên CHÍNH project `script-20260709-071612` (beats/cut GIỮ NGUYÊN — khác biệt truy được
  về tầng source; V2 backup `project.json.bak-truoc-v3` + `report.html.bak-truoc-v3`)
  → draft **`SCRIPT_20260709_071612_V3`** (không đè V2, NT5). Kiểm job nền sót trước khi
  chạy (leftover-background-job-check): sạch.
- **Vì sao:** 1 video gác CẢ 2 đợt (C6+C3+C7 và C4+D3) + lần đầu kho local chạy với
  102 clip đã tag lại — so chuỗi V1→V2→V3 cùng input là bằng chứng sạch nhất.
- **Số đo (so V2):** local thắng 21→**20** nhưng THÀNH PHẦN sạch hẳn: **4 pick sai-nghĩa
  biến mất** — clip Pluto rời b32/b33/**b60**, Destiny nhà-sao rời **b68** (toàn bộ về
  Pexels đúng nghĩa); chiều ngược lại video NASA-PLUTO giờ CHỈ dùng ở b72 = cảnh tàu
  thăm dò (New Horizons) cho ý Luna 3 — kho được dùng ĐÚNG nội dung thật; 8 local thắng
  mới hợp lý (b01 timelapse người ngắm trời · b10/b54 Destiny · b18/b23 eclipse · b21
  mission control · b26/b35 trăng-thành-phố...). Picks đổi V2→V3: 45/95. Phễu: 1085 ứng
  viên · chết kỹ thuật 3% · veto nghĩa 8% · sàn trả lại 0 · needs_human 0. Viral c8:
  11 cảnh/7 nguồn, không nguồn nào sát trần, gate chặn 48. **C3: 9 cảnh báo/110** (V2 12);
  3 rơi vào shot thở "sáng hơn hẳn". Card **Tone video** (C4) lần đầu hiện trên report.
  Nhạc 4 chương: uplifting→hopeful→peaceful→tense. 13 beat clip ngắn slow-mo. 1 cảnh báo
  "NÃO bỏ sót local" b19 (lớp đã biết PA-1). Assemble/report exit 0.
- **Verify — CỔNG MẮT + TAI user ĐẠT (2026-07-09):** b10/b54 (2 pick Destiny mới, lớp
  không-ground-truth cần soi nhất) "đều ok" · "chất lượng footage ok" · C3 "không quá
  quan trọng nên tôi duyệt qua" (giữ warning-only, không đầu tư thêm — nhất quán phán
  V2) · footage slow-mo "vẫn ok" · "phần nhạc tôi thấy ổn" → **C đợt 1+2 ĐÓNG TRỌN.**
  Code không đổi trong bước này (pytest 321/321 re-run xanh khi đóng mốc).
- **Vùng ảnh hưởng đã rà:** không sửa code — chỉ run + docs; project V2 khôi phục được
  từ 2 file .bak.
- **Còn ngỏ:** lớp shot-thở bị C3 bắn "sáng hơn hẳn" (b010/b020/b079) có thể là oan-có-
  chủ-đích (shot thở vốn cố ý đổi nhịp) — nếu lặp lại ở video sau thì cân nhắc C3 bỏ qua
  breath_shots; ghi nhận, KHÔNG làm ngay (C3 user đã hạ ưu tiên).

---

## §C-DOT-3-M1 — C1 ambient: PB10 giải phẫu âm thanh editor + kho + M1 thư viện (2026-07-10)

- **Cái gì làm:** (1) **PB10** — parse `draft_content.json` 3 draft editor `E:\PROJECT NHAN
  BAN\SPACE 1\SP1 - 001/003/004` (26–30'/video), gom audio theo tên file, tách voice →
  `PB10_AM_THANH_3_DRAFT_EDITOR.md`: kiến trúc 6 lớp + bảng volume chuẩn + bảng đối chiếu
  máy-vs-editor. (2) **Mót kho editor** (user yêu cầu tái dùng SFX thật): COPY 16 ambient
  + 19 SFX ngắn + 43 hold, KHÔNG đụng draft gốc; nhạc cảm xúc (16 file tên Việt) không
  copy — ngoài scope. (3) **M1**: module `ambient/library.py` + CLI `ambient-import`/
  `ambient-list` + 8 pytest; nạp thật 47 ambient (Artlist 29 + editor 16 + 2 dual) và
  19 SFX editor vào kho SFX C:.
- **Vì sao:** e1 backlog #2 (ambient cứu "chết hình" ô thở) đã đủ điều kiện (kho tag
  `scene_type`); PB10 biến mọi tham số âm lượng từ đoán thành SỐ ĐO editor thật; đồ
  editor proven trên video nên đứng biến thể đầu.
- **Số đo:** PB10 — nhạc editor 0.02–0.17 chồng 2–4 lớp · drone nền 0.05–0.17 suốt video
  · ambient cảnh 0.2–0.4 (bão 0.55–0.69) · whoosh 20–30 lần/video · video giữ tiếng gốc
  130/130·236/238·255/256 @1.0. Kho sau nạp: 47 biến thể/8 kind; SFX whoosh 4→15.
- **Verify:** pytest **329/329** (8 mới: import in-place/nguồn-ngoài/kind-sai/append/
  dual-kind regression/khớp-chặt/fail-open/root-suy); `ambient-import` thật 47/47 lỗi 0,
  chạy lại báo "không thấy manifest" đúng thiết kế (đã dọn `.done.yaml`); `ambient-list`
  + `sfx-list` khớp số kỳ vọng; kiểm folder: 47 wav + records + raw/ 45 nguồn + hold 43.
- **Vùng ảnh hưởng đã rà:** module MỚI 0 consumer hiện hữu (M2 mới wire vào assemble —
  hành vi assemble hôm nay CHƯA đổi); SFX editor vào kho C: là THÊM BIẾN THỂ cho rotation
  whoosh/impact/ding/keyboard/pop hiện có (overlay/chart tự hưởng, không đổi code — chất
  âm mới sẽ nghe ở video kiểm V4); draft editor E: chỉ đọc; `normalize_audio` tái dùng
  y nguyên (C4).
- **Bug bắt được trước khi nạp:** dual-kind (1 file thô → 2 kind cùng manifest) hỏng vì
  kind 1 dọn raw NGAY TRONG vòng lặp → kind 2 "không thấy file"; fix dọn SAU vòng +
  regression `test_dual_kind_same_source_file`.
- **Còn ngỏ:** 43 file hold (lửa/sôi mặt trời, rocket, whoosh dài, riser trắng...) chờ
  C5 subject-ambient / whoosh-standalone; 16 file nhạc editor chưa nạp thư viện nhạc
  (user gọi thì làm); backup D: chưa cover `F:\AutoEdit\ambient` + kho SFX C: mới —
  chạy lại robocopy sau khi C đợt 3 đóng.

---

## §C-DOT-3b-M5 — S4 `editor-learn`: học SFX + nhạc từ draft editor thành 1 lệnh (2026-07-10)

- **Cái gì làm:** module MỚI `autoedit/editor_learn/` — `dna.py` (quét DNA âm thanh
  ĐỌC-only: PB13 bê nguyên logic + PB11 whoosh-vs-cut + hồ sơ cộng dồn
  `F:\AutoEdit\editor_dna.json`) + `mine.py` (mót file COPY-only → manifest
  `ambient-import`/`sfx-import`, nhạc staging `F:\AutoEdit\music_editor\<draft>\`,
  hold `raw\tu_editor_chua_phan_loai\`) + CLI `editor-learn` + 12 pytest. Chạy thật
  3 draft SP1 + refresh backup D:.
- **Vì sao:** luật đứng user 2026-07-10 — mỗi project editor mới vào là máy PHẢI học
  sfx+music; quy trình mót tay PB10 phải lặp lại được, phép đo PB13 phải thành module
  để project mới cập nhật số cộng dồn.
- **Hiệu chuẩn PB11 (phải thử mới ra):** cut = tập START segment track video CHÍNH
  (bỏ t≈0) — đúng 120/232/263; "cut trong whoosh" INCLUSIVE `a≤c≤b` (whoosh bắt đầu
  ĐÚNG tại cut vẫn tính — strict ra 15/12/3 sai với bản công bố 17/12/4); mật độ
  whoosh chia PHÚT VIDEO không chia voice-span. Quirk voice-track GIỮ NGUYÊN có chủ
  đích (SP1-001 track voice chỉ phủ nửa đầu, SP1-004 fallback lẫn SFX — PB12 đã ghi):
  DNA để SO GIỮA các draft nên phép đo phải cố định, docstring `voice_tracks` ghi rõ.
- **2 bug bắt nhờ chạy thật (dry-run trước, real sau):** (1) dedup theo tên FILE ĐĨA
  bỏ sót 22 file — SFX kho CapCut nằm đĩa dưới tên hash md5, tên MATERIAL mới có nghĩa
  → danh tính + tên copy đổi sang tên material; (2) `Path.stem` cắt mù `.(1424901)`
  làm 2 SFX CapCut "Whoosh sound effect.(1424899/1424901)" TRÙNG danh tính → dedup oan
  2 chiều (899 chép trùng vào staging dù đã ở hold — đã dọn; 901 bị bỏ sót) → `norm_name`
  chỉ cắt đuôi khi là đuôi audio thật + regression.
- **Verify:** pytest **372/372** FULL suite; regression 3 draft SP1 ra ĐÚNG số công bố
  (PB13: nhạc 0.10/0.09/0.06, đè-voice 45·0.25 / 33·0.28 / 33·0.17, không-voice 1·1.00 /
  1·0.26 / 12·0.32; PB11: whoosh 40/25/23, dur 1.70/3.47/2.13, vol 0.32/0.18/0.20,
  cut 120/232/263, sát-cut 10/5/7, cut-trong 17/12/4); chạy lại cùng draft → 0 đề xuất
  mới (44/37/44 đã-biết) + hồ sơ không cộng đôi; pooled 3 draft voiced 0.24 (-12,3dB) /
  novoice 0.32 (-9,9dB) — SUBJECT_BREATH_VOL trúng số, SUBJECT_VOL 0.18 nằm dải editor.
- **Vùng ảnh hưởng đã rà:** module MỚI — pipeline dựng video KHÔNG đổi 1 dòng
  (assemble/source/ambient schedule nguyên vẹn, 360 test cũ xanh); file copy vào folder
  niche là file thô chưa chuẩn hóa → `list_variants` khớp chặt `^kind(_n).wav$` không
  nuốt (guard "editor - " cho tên đụng khuôn + test); manifest sinh ĐÚNG schema
  import sẵn có (không sửa importer); nhạc staging NGOÀI pool `~/AutoEdit/music`
  (music select không nhìn thấy — không lật hệ mood); volume constants CHỈ so sánh
  trên báo cáo, không ghi (V10 không bị lật); draft editor chỉ ĐỌC + copy ra.
- **Còn ngỏ:** file SFX nằm lẫn TRONG track voice fallback (vd "tàu vũ trụ.aac" SP1-003)
  bị skip như voice khi mót — đồ đó đợt này đã mót tay từ trước nên không sót thật;
  draft tương lai nếu editor trộn SFX vào track voice thì lệnh sẽ bỏ qua (fail-soft,
  DNA vẫn đo được, user rà tay bằng --dry-run); vòng học "máy đặt gì → editor giữ/xóa/đổi
  gì" (đối chiếu draft editor-sửa với ambient_log/subject_sfx_log) chưa làm — chờ có
  draft editor sửa thật.

---

## §EL-SP1-012 — editor-learn học draft mới đầu tiên: SP1-012 "mặt tối Mặt Trăng" (2026-07-10)

- **Cái gì làm:** chạy trọn vòng học project-editor-mới lần đầu trên draft NGOÀI bộ hiệu
  chuẩn: `editor-learn` (dry-run → thật → rerun 0-mới) → `ambient-import` 11/11 →
  `sfx-import` 1/1 → rerun sau import vẫn 0-mới → backup D: refresh.
- **Xác minh danh tính draft trước khi học (P1):** user trỏ `SP1 - 004` + content
  "scariest-air-around-the-sun" nhưng 004 ĐÃ học sáng nay (draft không đổi từ 06/07);
  folder mới thật = `SP1 - 012` (thêm 11:00 hôm nay, gom từ `D:\CapCut Drafts\SP1-012`,
  thiếu 1 PNG — không ảnh hưởng audio). Soi text materials: 004 = corona Mặt Trời
  (khớp content txt), 012 = mặt tối Mặt Trăng (tidal locking, Artemis II).
- **DNA SP1-012:** nhạc n=12 median 0.09 · **SFX đè voice n=41 median 0.18 = ĐÚNG
  SUBJECT_VOL** · không-voice n=1 (1.00, mẫu lẻ) · whoosh 34 ~1,3/phút dur 2,75s vol
  0.21 — mọi số nằm trong dải PB10/PB11/PB13. Pooled 4 draft: voiced 0.21 (-13,6dB) /
  novoice 0.33 (-9,6dB) — SUBJECT_VOL/SUBJECT_BREATH_VOL vẫn giữa dải, không đổi hằng.
- **1 bug bắt nhờ dry-run + fix:** 2 file "【Japanese nature sound】Autumn Insect...
  Chuo City, Yamanashi Prefecture" → urban_street vì keyword "city" ăn TÊN ĐỊA DANH.
  Kho có sẵn kind `nature_forest_field` (SCENE_TYPES GLM) mà `_SCENE_RULES` thiếu →
  thêm rule (insect/cricket/forest) TRƯỚC urban_street; chủ ý KHÔNG thêm từ "nature"
  — "Wind sound effects (nature, breeze...)" phải rơi xuống sky_cloud (+2 assert).
  Anh em cùng pattern (P5): từ khóa scene khác dính tên riêng — chưa thấy ca thật,
  ghi ngỏ; chốt chặn cuối vẫn là soi manifest bằng --dry-run trước khi import.
- **Verify:** pytest 372/372 FULL; kho space sau nạp: explosion 7 · rocket 7 ·
  nature_forest_field 4 · signal 2 · sky_cloud 7 · whoosh sfx ×16; nhạc staging
  `music_editor\SP1 - 012\` 2 bài (tăng dần, khoa học nhịp nhanh); hold +5
  (volcano magma, glitch, ship, science mặt tối.mp4, 爆炸); editor_dna.json 4 draft.
- **Vùng ảnh hưởng đã rà:** sửa đúng 1 tuple `_SCENE_RULES` trong mine.py — consumer
  duy nhất là `classify()`; kind mới nằm sẵn trong AMBIENT_KINDS nên ambient-import
  không cần sửa; DNA/regression 3 draft SP1 không đụng (số y nguyên).
- **Còn ngỏ:** SFX không-voice của 012 chỉ 1 mẫu vol 1.00 — chưa đủ dữ liệu kết luận
  gì; "science mặt tối.mp4" trong hold là video-có-tiếng editor dùng làm nhạc nền,
  chờ phân loại tay.

---

## §NẠP-KHO-0710 — nạp 17 nhạc editor vào pool + ocean waves ×10 (2026-07-10)

- **Cái gì làm (user duyệt cả 2, data-only không đổi code):** (1) copy 17 bài từ staging
  `F:\AutoEdit\music_editor\<draft>\` vào `C:\Users\NBPC\AutoEdit\music\tracks\` theo quy
  ước `Artist - Title __mood` với artist = mã draft (SP1-001…SP1-012) để giữ nguồn gốc,
  rồi `music-import` → **pool 22 → 39 bài, 0 lỗi** (librosa đo BPM/energy/sections đủ 17).
  Staging GIỮ NGUYÊN (hồ sơ mót + dedup rerun editor-learn). (2) 10 file WAV user mua ở
  `F:\AutoEdit\ambient\ocean waves\` → `ambient-import` 10/10 → kind **`ocean` ×10**
  (chuẩn hóa WAV PCM 48k) — đóng nợ V8 mục 1 "beat biển thà-im-hơn-sai chờ mua file".
- **Mood MÁY MAP từ tên tiếng Việt (user chỉnh nếu sai — đổi tên file `__mood` rồi chạy
  lại `music-import`, hoặc overrides.yaml):** căng dần/căng đét → tense (+suspenseful) ·
  căng dần nhịp cuốn → tense+determined · khoa học + bao la → epic+mysterious · lắng đọng
  → nostalgic+peaceful · êm → peaceful · deep → dark+mysterious · hy vọng →
  hopeful+inspiring · nhẹ nhàng vô tận (×2) / cảnh đẹp êm ái → peaceful+dreamy · sâu thẳm,
  sợ → dark+scary · êm + sợ → mysterious+suspenseful · khoa học nhịp nhanh →
  determined+mysterious · tăng dần → suspenseful+epic · **"2 3 được" = KHÔNG mood**
  (tên không nói gì — vẫn vào pool, chỉ đấu bằng energy/tempo, chờ user đặt mood).
- **Kỹ thuật đáng nhớ:** manifest ocean đặt tên riêng `ocean_waves_2026-07-10.yaml`
  vì `_move_overwrite` sẽ đè `ambient_manifest.done.yaml` cũ trong raw/ (mất hồ sơ nạp
  trước) · file ambient DÀI nhiều phút an toàn — scheduler cắt lát từ đầu file, chỉ file
  NGẮN hơn ô mới cần loop (đường riêng của drone) · 2 record cũ trong index mang mood
  UNION từ file anh em cùng base "Artist - Title" (hành vi `manifest_from_tracks` có sẵn
  từ 14/06, không phải lỗi nạp).
- **Rà chồng chéo (nhạc mới đụng hệ mood):** nhạc editor vào pool = thêm ứng viên cho
  `select_music` (mood 0.6 + energy 0.25 + tempo 0.15), KHÔNG đụng tầng khác; rủi ro duy
  nhất = mood máy-map lệch tai → nhạc lệch chương. Chốt chặn: đi ké cổng TAI video kiểm
  C đợt 4; núm chỉnh là TÊN FILE `__mood`, không phải code.
- **User chốt cùng lúc (backlog chapter-title card + whoosh/swell):** title **đơn giản,
  dạng basic, font VIẾT HOA, dễ nhìn** — ghi để dùng khi làm tính năng (sau C đợt 4/5).
- **Backup D: refresh:** ambient +22 file (10 ocean chuẩn hóa + 10 nguồn + records) ·
  AutoEdit_C +19 (17 mp3 + index + manifest). robocopy exit 1 = copy OK.

---

## §C-DOT-4-PB14 — đo punch-in 4 draft editor, verdict chờ user (2026-07-10)

- **Vì sao đo trước:** foundation f2 §5 ghi "có punch-in không, ở đâu" là câu hỏi CHƯA ĐO;
  whoosh auto từng chết vì suy diễn (PB12: 0/88). MO_TA_VAN_HANH_C_DOT_4 §1 (user duyệt)
  chốt M0 = PB14.
- **Cách đo** (`autoedit/scripts_phan_tich_pb14_punch_in.py`, đọc-only): quét mọi track
  video 4 draft SP1-001/003/004/012 — (A) segment có keyframe scale GIỮA clip (cách mép
  >0.5s; mép = Ken Burns/fade); (B) punch-bằng-cắt = 2 segment liền kề cùng material,
  nguồn nối tiếp ≤0.3s, scale tĩnh nhảy ≥5%. Mỗi cú đối chiếu: sát mốc TEXT hiện lên
  (≤0.5s/≤1s) + nằm trong voice. Ảnh (photo) loại — đó là chuyện Ken Burns.
- **Số:** (B) = 0 tuyệt đối cả 4 draft. (A) track phủ = pop-in/out animation overlay
  (kf 0.01→nền trong <1s — lớp máy ĐÃ CÓ ở overlay/style). (A) track CHÍNH: SP1-001 2 cú
  (13s hook + 210s, 1.00→1.75 trong 0.7–1.1s) · SP1-004 2 cú (43s 1.00→1.94 ramp 2.5s ·
  115s 1.00→1.27 drift 4.4s) · SP1-012 2 cú (315s Clip ghép đa-móc · 996s GRAIL 1.00→1.18
  drift 4.5s) · SP1-003 0 cú track chính. Tổng **5–7 cú / ~104 phút ~ 0,06/phút**; sát
  TEXT ≤0.5s chỉ 3/7; đa số trong voice.
- **Đọc số:** cú "punch 10–20% bám từ khóa" như foundation dự kiến KHÔNG tồn tại trong
  ngôn ngữ editor này. Cái có thật là **zoom-drama HIẾM** (1–2 cú/video 26'), mức to
  x1.3–1.9, đặt theo NGHĨA khoảnh khắc (hook, twist) — không có tín hiệu bề mặt
  (text/cut/voice-gap) đủ mạnh để máy bám.
- **Verdict đề xuất (chờ user):** KHÔNG code punch-in auto — n=7 mà viết luật là rắc-đều
  sai chỗ (f2 §4); editor thêm tay 1–2 cú lúc tinh chỉnh rẻ hơn rủi ro. Đợt 4 đóng bằng
  kết luận đo (như whoosh), tri thức ghi vào f2 block LỆCH; sang đợt 5 C5 vision gate,
  video kiểm đợt 5 gánh luôn cổng TAI nhạc editor.
- **Vùng ảnh hưởng:** 0 dòng code pipeline đổi; chỉ thêm script đo + vá docs (f2 block
  LỆCH — thi hành luật ghi-lệch user chốt hôm nay, memory `foundation-deviation-rule`).
- **USER DUYỆT verdict cùng ngày ("duyệt theo ý bạn") → C ĐỢT 4 ĐÓNG.** Không code
  punch-in auto; cú zoom-drama hiếm để editor thêm tay lúc tinh chỉnh. Kế tiếp: C đợt 5.

---

## Ghi chú hệ thống memory

Memory files (quyết định/bug sâu) lưu ở:
`C:\Users\NBPC\.claude\projects\c--Users-NBPC-Documents-Claude-Projects-tool-edit-padoma\memory\`
(tự sinh khi bắt đầu làm việc trong folder này). Frontmatter YAML (name/description/type) +
1 dòng index vào `MEMORY.md`, cross-link `[[tên]]` — giống hệ thống project `nhan ban`.

## §C5-GATE — C đợt 5: vision gate top-pick, code M1+M2 (2026-07-10)

- **Cái gì đổi:** mô tả `MO_TA_VAN_HANH_C5_VISION_GATE.md` (user duyệt cùng ngày, chốt
  PA-A soi mọi beat + C3 đóng warning-only) → M1 `ranker/visiongate.py` (GateVerdict +
  VisionGate, tái dùng nguyên đồ nghề vision.py: extract_frames/shrink 960/schema-echo/
  feedback-retry/api.z.ai) → M2 cắm `_pick_by_funnel` (runner.py) + field `vision_gate`
  trong BeatRankResult + dòng tổng RANK + card report + CLI source tự tạo gate.
- **Vì sao:** mọi tầng gác chủ thể hiện đọc CHỮ; lớp lỗi b60 (tag nói dối từ nạp kho),
  b68 (nguồn không ground truth) và ca 3c stock chỉ bắt được bằng nhìn FRAME THẬT.
  Đặt tại pick (sau _materialize) vì đó là chỗ duy nhất file đã nằm trên đĩa mà quyết
  định còn đổi được.
- **Luật vận hành (user chốt từ V123 §3c + filter-overload-guard):** soi CHỈ lead ·
  budget 2 verdict/beat · subject "no" lần 1 demote, lần 2 giữ điểm cao nhất + SOÁT TAY ·
  unsure = pass · mood chỉ warning · fail-open, tắt sau 3 lỗi · KHÔNG ghi sổ P7/ledger
  cho ứng viên bị chê.
- **Vùng ảnh hưởng đã rà:** caller `run_source` = CLI (đã tiêm gate) + test (helper thêm
  param, default None = hành vi cũ — 1 call trực tiếp line 400 không gate vẫn đúng);
  consumer `rank_log` = report (dùng .get, project cũ an toàn); M3b stock_tags chạy SAU
  picks nên chỉ tag pick cuối (asset bị gate loại không tốn call tag); shot thở/entity/
  graphic/heuristic-không-brain không đi qua gate. Chồng chéo mood (tầng 5) đã né bằng
  warning-only.
- **Verify:** pytest FULL **385/385** (+7 unit: parse/echo/feedback-retry/give-up-4/
  shrink-960/prompt-đủ-ngữ-cảnh/format-lạ; +6 tích hợp: pass-giữ-pick · demote-đổi-pick
  + P7-không-ô-nhiễm · 2-fail-giữ-best · mood-warning-only · pool-1-bị-chê-vẫn-pick ·
  fail-open-tắt-sau-3-lỗi). Test đầu viết sai (gate phán theo claim nên beat 2 vẫn bị
  chê — hành vi đúng, assert sai) → thêm `only_beat` cho FakeGate.
- **Còn ngỏ:** M3 video kiểm SP012 → V11 (cổng MẮT C5 + cổng TAI nhạc editor/ocean đi ké);
  sau video kiểm: user phán trúng/oan để quyết nâng mood-warning lên demote; nếu gate
  trượt ca slug-tiết-lộ thì mở lại việc đưa source_video vào prompt NÃO (đã chủ động
  KHÔNG làm đợt này — lý do trong mô tả §5).


---

## 2026-07-11 — SP1-014: chạy thật A1 trọn gói (nạp Artemis + dựng L2b sâu) — draft ch2→end chờ cổng mắt

- **Cái gì đổi:** không code mới — lần chạy THẬT đầu tiên trọn quy trình trên video space mới 44′:
  4 mẻ `library-ingest` viral (topic "Artemis 2, return to the Moon") + pipeline
  new→align→direct-context→(phiên đạo diễn)→direct-ingest→cut→source→assemble→report.
- **Sự cố input tìm ra (quan trọng nhất phiên):** `voice 1.mp3` trong `F:\SPACE\Voice + content SP014`
  là Chapter 1 của bài KHÁC (cực Mặt Trời) → Hook+Ch1 Artemis không có audio. Triệu chứng nhận biết:
  align <95% + nghìn từ nội suy nén vào chục giây đầu + hàng loạt merged-short-beat 0s ở chương đầu.
  Chi tiết + cách dựng lại bản full: memory `sp1-014-voice1-thieu`.
- **Bài học đạo diễn bài dài:** LLM không được ước thời lượng beat từ số từ — voice SP014 đọc ~0,45s/từ
  (ước 0,39 → 146 beat quá 10s). Chuẩn mới: viết beat theo Ý, rồi script hậu xử lý chia theo
  timestamp THẬT của transcript (điểm câu + nghỉ ≥0,3s) trước khi nộp direct-ingest
  (`scratchpad fix_beats.py` / `migrate_draft.py` — nên cân nhắc đưa vào repo thành lệnh chính thức).
  Draft đạo diễn theo word index nên DI CHUYỂN được giữa project cùng script (NT4 trả công).
- **Verify:** direct-ingest pass (410 beat, chỉ warning); cut/source/assemble/report exit 0;
  draft `SP1_014_ARTEMIS_2_CH2_END_20260711_042901` sinh trong CapCut folder; backup D: đã chạy.
- **Số pytest:** không chạy (không đổi code repo — chỉ chạy pipeline + script scratchpad).
- **Vùng ảnh hưởng đã rà:** không sửa code repo; 2 script hậu xử lý chỉ ghi `director_draft.json`
  của 2 project SP1-014, mọi luật gác vẫn do direct-ingest quyết.
- **Còn ngỏ:** (1) user bổ sung voice 1 đúng → dựng bản FULL (~20′ máy + source); (2) cổng mắt+tai
  draft ch2→end; (3) 2 beat needs_human (b362-363, ~2596-2608s) editor tự đắp; (4) 22 cảnh cảnh báo
  so màu C3 trong report — soi khi xem draft.



---

## 2026-07-11 — REF: ưu tiên nguồn video mẫu của bài + vá 12 beat generic SP1-014 — chờ cổng mắt _V2

- **Bug (user phát hiện trên draft SP1-014):** beat thiết kế/sản xuất Artemis (ch1-2) chọn Pexels
  generic dù kho có 61 cảnh assembly/cleanroom Artemis từ chính 4 video mẫu. Truy 4 tầng đồng phạm
  (memory `sp1-014-generic-footage-bug`): concept đạo diễn generic · C4 vocab top-30 giấu từ ngách
  (assembly hạng 102 < ngưỡng top-30 ≥178) · ingest xong SAU direct-context · phễu không chấm niche-fit.
- **Cái gì đổi (user chốt 2 luật, duyệt mô tả trước khi code — `MO_TA_VAN_HANH_REF.md`):**
  `sourcer/viral.py` (REF_CAP_RATIO 0,15 + `_cap_ratio` theo prefix khai, so không phân hoa-thường) ·
  `sourcer/local.py` (`find_ref_candidates` OR-match ≤6/beat CHỈ trong tập ref, geo-gate giữ) ·
  `sourcer/runner.py` (chèn sau local/trước Pexels, ledger vẫn gác; đánh dấu `is_ref` 1 chỗ duy nhất) ·
  `ranker/funnel.py` (REF_BONUS 1,0 🔸 trong `_diem_may` — chảy cả 2 đường rank) ·
  `project.py`+`cli.py` (`--ref` dính vào inputs.ref_sources, guard OptionInfo bug B2) ·
  skill `dung-video` (luật NICHE-ANCHOR + thứ tự ingest + hướng dẫn --ref).
- **Vì sao thiết kế vậy:** cả 3 tác dụng đều NỚI/ĐIỂM, không đẻ cửa loại (filter-overload-guard);
  bonus 1,0 cố ý không đè nghĩa (b018 thua 6,0 điểm nghĩa → Pexels thắng là ĐÚNG quyền phễu);
  người KHAI --ref, máy không suy từ tên (luật own-vs-viral).
- **Vá SP1-014 (script scratchpad resource_ref.py + resource_fix2.py):** 10/12 beat sang cảnh kho;
  bài học: tier specific là NGÔN NGỮ PEXELS — vòng 1 thay hết bằng ngôn ngữ niche làm b011/b091
  rỗng pool; niche-anchor đặt ở CONCEPT + tier local. b091 giữ pick generic cũ (Pexels cạn quota
  giờ + kho bão hòa kề/P7) — editor soát tay.
- **Verify:** 4 pytest hồi quy mới (trần 15% + case-insensitive · OR-match/ẩn dụ-không-chèn ·
  glue is_ref + bonus · nhãn ledger không rơi); FULL suite 429 pass; re-assemble + report exit 0;
  draft _V2 tên mới (C5), needs_human về đúng 2 beat gốc (362-363).
- **Vùng ảnh hưởng đã rà:** mọi chỗ khởi tạo ViralLedger (chỉ runner + test, default () giữ hành vi
  cũ) · caller run_source/source() (run gọi thiếu cờ → sticky từ project.json) · candidate dict thêm
  key is_ref (chỉ _diem_may đọc — additive) · message trần đổi "8%"→"{ratio:.0%}" (test cũ vẫn khớp).
- **Còn ngỏ:** b091 generic · F2 (vocab theo scene_type) + F3 (điểm niche-fit phễu) để ngỏ nếu bug
  tái diễn · bất đối xứng C5 gate không soi Pexels · cân nhắc đưa re-source-per-beat thành lệnh chính thức.



## 2026-07-11 — SP1-014 FULL: voice1 đúng đã về — dựng trọn bài 12 chương / 462 beat, REF chạy hết công suất — chờ cổng mắt

- **Cái gì đổi:** user cung cấp `voice1.MP3` mới (371s) thay file lạc → kiểm bằng transcribe 60s
  (khớp nguyên văn hook script — bài học `sp1-014-voice1-thieu` áp dụng đúng) → concat 1→10
  (2.996,8s) → project MỚI `sp1-014-artemis-2-full-20260711-092216` → dựng trọn theo đúng lộ trình
  memory: align → dịch draft ngược (ch1-2 từ .bak gốc, ch3-12 shift +856, vá 12/12 concept REF)
  → ingest 462 beat → cut → source --ref → assemble → report. KHÔNG sửa code — data-only.
- **Vì sao dựng lại TOÀN BỘ thay vì đắp thêm hook+ch1** (user hỏi giữa chừng, đã giải thích):
  timestamp/beat_id toàn video lệch khi thêm 6′ audio vào đầu; luật trần/kề/P7 là luật TOÀN video;
  và quan trọng nhất — bản ch2-end được source TRƯỚC khi có gói REF (chỉ 12 beat vá tay), dựng full
  cho CẢ 462 beat hưởng REF. User chốt "tiếp tục dựng full, không thay đổi gì".
- **Số đo:** align 6′42″ · ingest ~0″ · cut 35″ · source 3h09′06″ (~24,6s/beat — chậm hơn bản cũ
  20,5s/beat do pool thêm ứng viên REF + C5 soi nhiều pick kho hơn) · assemble 30′33″ · tổng máy
  ~3h48′. Kết quả: 458 ok / 2 graphic / 2 needs_human (b416-417 "shadowed crater" — trùng 2 beat
  362-363 của bản cũ, nhất quán).
- **REF hết công suất toàn video:** 131/462 pick (28%) từ 4 video mẫu của bài (bản cũ pre-REF: 53
  pick kho toàn tuyến); nguồn top dùng 296s — SÁT trần 15% (trần 8% cũ chỉ cho 159s); gate chặn
  4.131 lượt (kề/trần) — luật pháp lý vẫn nghiêm.
- **⚠ Quan sát cho cổng mắt:** 12 beat vùng lỗi generic cũ lần này phễu chấm lại độc lập → chỉ 3
  pick REF (b073 sơ đồ tàu, b133 lắp ráp, b144 module Artemis II), 9 beat Pexels thắng điểm nghĩa
  (concept đã neo-niche nên Pexels trả về cũng sát chủ đề hơn trước). ĐÚNG thiết kế REF-không-đè-nghĩa;
  nếu mắt user vẫn chê generic → re-source per-beat (đường vá đã có script) hoặc mới cân nhắc F3.
  Thêm: b294 bị C3 báo sáng lệch chương (0,74 vs trung vị 0,21) — soi lại.
- **Verify:** pipeline exit 0 toàn tuyến; draft `SP1_014_ARTEMIS_2_FULL_20260711_092216` + report.html;
  pytest không đụng (429 giữ nguyên, không sửa code).

---

## 2026-07-13 — PORTABLE: draft copy sang máy editor mở được, không relink + folder xuất E:\CapCut Drafts

- **Bug (user báo):** SP1-014 FULL bàn giao (F:\SPACE\PROJECT TOOL CHAY XONG) copy sang máy editor,
  đã relink: sfx/nhạc hiện đủ, riêng FOOTAGE báo **"Không thể tải xuống tài liệu"**. Máy gốc mở tốt.
- **Root cause (đối chiếu kho AutoClone §B4 + mục 15 REAL71 — khớp 100%):** path media tuyệt đối
  máy gốc chết trên máy editor; audio `check_flag=3` → "thiếu local" → cho relink; video pycapcut
  `check_flag=63487` + path không resolve → CapCut xếp "cloud material thiếu" → không cho relink.
- **User chọn PHƯƠNG ÁN B (placeholder — vì nhiều editor, draft để folder khác nhau):** bằng chứng
  gom trước: GUID placeholder là **hằng số toàn cục CapCut** `0E685133-18CE-45ED-8CB8-2904A212EC80`
  (quét 401 file draft Mac + Windows editor → 1 GUID duy nhất); draft native để video placeholder +
  flag 62978047, audio flag 1; meta file_Path `./` tương đối; fold_path stale vô hại.
- **Hồi tố tay (script scratchpad `portable_hoa*.py`):** SP1-014 FULL (1110 path + 592 flag × 7 file
  gồm .bak/template-2.tmp/Timelines — chặn CapCut khôi phục path cũ) + SP1-017 (720 path + 383 flag);
  0 file thiếu theo path mới; backup JSON gốc `<draft>_backup_json_truoc_portable\`. **Cổng mắt ĐẠT
  2 MÁY** (user 2026-07-13): bản `_PORTABLE` máy này + máy editor thật "hoạt động tốt, không lỗi".
- **Vào pipeline (user chốt "project sau này lưu E:\CapCut Drafts + sửa luôn lỗi"):**
  `packager.py::_to_portable` (thuần — trả cây mới, caller giữ path tuyệt đối để re-package) chạy
  TỰ ĐỘNG trong `package_draft`; sổ meta `file_Path` → `./materials/<tên>` + link registry theo TÊN
  (tên duy nhất nhờ dedupe `_embed_media`); `machine.json::draft_out_root` + `out_root()` +
  CLI `set-draft-root` (đã chạy: `E:\CapCut Drafts`); assembler `_next_version` soi out_root;
  donor/cover vẫn theo `capcut_root`. Mô tả + rà chồng chéo: `MO_TA_VAN_HANH_PORTABLE.md`.
- **Verify:** pytest **FULL 469/469** (+4 packager mới trong đó 1 regression tái hiện đúng bug
  path-tuyệt-đối-trong-content, +1 assembler cập nhật sổ `./materials/`); set-draft-root ghi
  machine.json xác nhận.
- **Vùng ảnh hưởng đã rà:** caller `package_draft` (assembler + demo-draft + cli:1691) đều hưởng;
  reader draft (ingest/editor-learn/tcf_gen) đã placeholder-aware sẵn; luật C2 không ngược (placeholder
  = dạng ĐÚNG thứ 2); test `no_silent_overwrite` giữ (nhờ _to_portable thuần); `_next_version` đổi
  root đếm — series `_V*` cũ trên C: không đếm tiếp (chấp nhận, đã ghi mô tả).
- **Còn ngỏ:** (1) CapCut máy này cần trỏ Draft location → `E:\CapCut Drafts` mới thấy draft mới
  (user tự làm, 1 lần); (2) draft test cũ trong com.lveditor.draft (SCRIPT_*, CH2_END…) chưa portable —
  cần bàn giao cái nào thì chạy script scratchpad `portable_hoa_v2.py <folder>`; (3) khi có video mới
  đầu tiên dựng xong → cổng mắt đi ké: mở từ E:\CapCut Drafts + thử copy máy khác.

---

### 2026-07-12 — SP1-017 "Edge of the Universe" DỰNG XONG BẢN FULL (35′/11 chương/324 beat) — CHỜ CỔNG MẮT

- **Cái gì:** Dựng mới end-to-end video space "What is at the edge of the universe" từ
  `F:\SPACE\Voice + content SP017` (8 voice → ghép 1 = 2097s/34:57) + 5 video mẫu REF
  `F:\SPACE\VIDEO MAU\SP1-017` (draft tách cảnh sẵn ở `E:\CapCut Drafts`). Draft ra:
  `SP1_017_EDGE_OF_THE_UNIVERSE_20260711_233818`.
- **Vì sao làm khác:** đường sâu L2b, nhưng 7/11 chương >424 từ (vùng timeout `autoedit direct`
  claude -p 600s) → KHÔNG dùng direct tự động. Thay: tự viết outline → **fan-out 11 agent song
  song** (mỗi agent đạo diễn 1 chương theo word-range + spec chung có luật NICHE-ANCHOR) → ghép
  + kiểm coverage → direct-ingest. Đạo diễn ~4′ wall-clock thay vì hàng giờ.
- **3 lỗi ingest sửa 1 lượt python:** route agent nhầm 'metaphorical' (=visual_level) → local_library;
  76 query >4 từ → bỏ stopword+cắt; 11 beat >10s do đo TIMESTAMP thật (khe lặng lớn, vd 7,88s
  giữa "…simple."/"To reach…") → tách rơi đúng khe + gắn hình thở. Ingest PASS 324 beat, $0 API.
- **Bug assemble:** 1 file Pexels download đứt (b055 norm cụt 1,3MB "moov atom not found"); raw
  `assets/` tốt (7,65MB) → `normalize_video()` tái tạo. Assemble timeout foreground 2′ → chạy nền.
- **Verify (thời gian máy):** voice 1s · align 334s (nội suy 2,5%) · library-ingest 5 mẫu 873 cảnh
  1547s (2 fail vision) · direct-context 1s · đạo diễn 11 agent ~4′ · cut 25s (236 seg + 25 thở) ·
  **source --ref --niche space 18556s (~5h9′, lâu nhất — phễu 324 beat qua Claude Code)** ·
  assemble 1297s (41 overlay + 41 SFX + nhạc 11 chương + ambient 21 ô + drone + Ken Burns 8 ảnh) ·
  report 1s. Tổng ~6h. Source: viral 108 cảnh (5 mẫu vào mạnh), kho thắng 106, 1 beat cần người,
  37 cảnh báo màu C3. pytest KHÔNG đụng (chỉ chạy pipeline, không sửa code). **CHỜ user soi CapCut.**

## 2026-07-13 — MUSIC-SYNC-M0: analyzer nhịp/accent + tier A/B/C cho pool nhạc — pytest 441/441, chờ chốt ngưỡng

**Cái gì đổi:**
- `music/analyze.py`: `_rhythm_from_signal` (dùng chung 1 lượt load audio) → `beat_times`,
  `downbeats` (ước lượng pha: nhóm 4 beat, pha có onset tổng lớn nhất), `accents`
  (onset pctl ≥70, greedy mạnh-trước, min-gap 1s — đúng phương pháp nghiên cứu lift 2.01),
  `beat_quality` (onset-tại-beat / onset-nền), `beat_tier` A/B/C. Tier C: beat_times bịa
  của librosa KHÔNG lưu (bẫy ~120BPM cho ambient — memory editor-music-sync-study).
  Public `analyze_rhythm(path)` cho backfill. Số 🔸 đặt cạnh nhau đầu file.
- `music/library.py`: import cache-hit tự NÂNG CẤP record cũ thiếu grid (chỉ đo rhythm,
  giữ nguyên energy/sections cũ — PRESERVE); lỗi rhythm → thiếu beat_tier = downstream
  coi như C (fail-open). `regrid_index()` backfill toàn index. Hằng `ANALYSIS_KEYS`/`RHYTHM_KEYS`.
- `cli.py`: lệnh mới `music-analyze [--regrid]` — in từng bài (tier/quality/số beat/accent)
  + phân bố quality để chốt ngưỡng.

**Vì sao:** M0 của gói MUSIC SYNC (MO_TA user duyệt 2026-07-13): mọi cơ chế M1-M4 cần
accent/grid map sẵn trong index; luật user "mọi bài nhạc mới đều phải có grid".

**Vùng ảnh hưởng đã rà:** `analyze_track` chỉ có 1 consumer (`library._import_entries`,
key-list đã mở rộng); index thêm field → `select.py`/`music-list`/assembler đọc theo key,
bỏ qua field lạ; naming/manifest không đổi. 📌 LỆCH MO_TA §2 (ghi vào MO_TA §6): KHÔNG
đo ở staging `music_editor/` — bài chỉ chọn-được khi qua `music-import` (cổng đó nay luôn đo).

**Verify:** pytest FULL **441/441** (+5 mới `test_music_rhythm.py`: click 120BPM → tier A,
chu kỳ đo 0,5s±0,06, downbeat ⊂ beat, accent đúng min-gap · drone sine → C + không giữ grid
bịa · import thêm grid + idempotent (monkeypatch cấm analyze lại) · nâng cấp record cũ
PRESERVE energy_curve · regrid ghi xuống index). Backfill thật `music-analyze --regrid`
**128 bài: A=76 B=50 C=2**, quality min 1.28 / p25 1.58 / median 2.19 / p75 2.98 / max 7.13.

**Còn ngỏ (chờ user):** (1) chốt ngưỡng tier 🔸 — ambient deepsea tên tay ("nền deepsea
trầm sợ" 2.09, "dưới nước 4" 2.08) lọt A; vô hại gói mặc định (M-ACCENT dùng accent, có ở
cả A/B) nhưng M-GRID chỉ nên chạy A thật → đề xuất giữ B≥1.3, nâng A≥2.2. (2) pool có vài
cặp file trùng nội dung khác tên (bản editor tên Việt) — chuyện cũ của pool, ghi nhận thôi.
(3) duyệt sang M1: stage `music` giữa cut→source + fallback đường cũ.

## 2026-07-13 — MUSIC-SYNC-M1: chốt ngưỡng tier + stage `music` giữa cut→source — pytest 451/451

**User ủy quyền:** "tính toán cẩn thận mọi biến ảnh hưởng chất lượng video, tự chốt và
quyết định tiếp" → Claude chốt 2 biến, code M1.

**Biến 1 — ngưỡng tier CHỐT: B≥1.3, A≥2.2** (từ 2.0; ghi vào MO_TA §5 + `analyze.py`).
Căn cứ soi dải 1.9-2.5 pool thật: 2.0-2.2 = ambient tên tay ("dưới nước 4" 2.08, "nền
deepsea trầm sợ" 2.09) + dreamy nhẹ; 2.2-2.5 = tense/mysterious nhịp thật. Chi phí sai
bất đối xứng: ambient-lọt-A hại neo-downbeat/M-GRID; nhịp-thật-rơi-B chỉ mất downbeat.
Kiểm thêm: không bài nào accent <1.5/phút → snap ở tier B luôn có mục tiêu thật, trần
15% tự bảo vệ. Regrid lại pool ngưỡng mới: **A=61 B=65 C=2** (15 bài 2.0-2.2 rời A xuống B, đúng nhóm ambient/dreamy nhắm tới).

**Biến 2 — neo offset:** cửa sổ ±ANCHOR_WIN=2s quanh offset section cũ (GIỮ nghĩa
drop/build của _start_offset); target trừ SNAP_LEAD 0.08s ("whoosh vào hit"); chương
sau trừ thêm min(XFADE, timeline_start) vì nhạc vào sớm crossfade — điểm nhấn rơi đúng
CẮT CHƯƠNG chứ không phải đầu segment nhạc. Tier A ưu tiên downbeat rồi accent; B chỉ
accent; C giữ nguyên (sync tắt).

**Cái gì đổi (M-STAGE):**
- `project.py`: `Stage.MUSIC` ("music", OPTIONAL) vào PIPELINE_ORDER giữa CUT–SOURCE;
  model `MusicPlanEntry` (chapter_id/file/start_offset/beat_tier/score/anchor_note);
  field `music_plan` (rỗng = assemble tự chọn như cũ).
- `music/plan.py` MỚI: `run_music` (đòi CUT done; `select_music` NGUYÊN VẸN 100% +
  neo offset + đếm usage tại stage); `mark_music_stale`; nhận luôn `MUSIC_XFADE` +
  `chapters_with_time` DỜI TỪ assembler (2 nơi cùng cần — 2 bản sẽ lệch, P5).
- `cutter/runner.py`: cuối run_cut gọi `mark_music_stale` — timeline đổi → plan xóa +
  stage music về pending + warning. KHÔNG BAO GIỜ dùng được plan cũ trên timeline mới.
- `packager/assembler.py`: `_add_music_by_chapter` có plan → dùng nguyên file+offset,
  KHÔNG chọn lại, KHÔNG đếm usage (stage music đếm rồi — tránh đếm đôi); không plan →
  fallback đường cũ từng dòng nguyên vẹn (usage đếm ở assemble như cũ).
- `cli.py`: lệnh `music` (đổi tên hàm `music_cmd` — bẫy trùng tên tham số `--music`
  của `run` che mất hàm); `run --music-sync` chèn stage (mặc định TẮT); `done()` đổi
  `.get` (project.json cũ thiếu key "music" — chống KeyError).

**Vùng ảnh hưởng đã rà:** grep `stages[` toàn repo — chỉ `done()` cli đọc key động
(đã vá), mọi chỗ khác đọc key vừa ghi; `MUSIC_XFADE`/`_chapters_with_time` chỉ assembler
tiêu thụ (alias import giữ tên cũ); report đọc `music_selections` — assemble vẫn ghi cả
2 nhánh; direct-rerun đổi outline → buộc cut-rerun (timeline mất) → stale phủ luôn ca này.

**Verify:** pytest FULL **451/451** (+10 `test_music_plan.py`: 4 anchor thuần (A ưu tiên
downbeat/B accent/C+ngoài-cửa-sổ giữ nguyên/kẹp 0) · run_music chọn Y HỆT select_music
đường cũ + usage đếm tại stage + resume từ đĩa · neo offset accent trừ lead+xfade ·
đòi cut done · mark_music_stale · 2 e2e ffmpeg: assemble theo plan đúng offset µs +
không đếm usage / fallback không plan chọn như cũ + đếm usage). Smoke `autoedit music
--help` OK.

**Kế tiếp:** M2 M-VOL (volume nhạc hook theo zone/niche + ducking zone-aware) — có
cổng TAI cần user; M3 M-ACCENT snap + M-CHANGE.

## 2026-07-13 — MUSIC-SYNC-M2: M-VOL volume nhạc theo zone hook/body + ducking zone-aware — pytest 454/454, CHỜ CỔNG TAI

**Cái gì đổi (M-VOL — chỉ kích hoạt khi có `music_plan`, mặc định TẮT = nguyên trạng V10):**
- `packager/ducking.py`: bảng 🔸 `HOOK_DUCK = {space: 0.35, deepsea: 0.30}` + default
  0.30 + `hook_duck_for(niche)` (đo editor: space hook 0.377/body 0.076; deepsea
  0.474/0.355; thân bài GIỮ 0.2/0.5 đã qua tai V10).
- `packager/assembler.py`: `_lay_music` nhận `volume` (mặc định 0.2 như cũ);
  `_add_music_by_chapter` — chương ĐẦU timeline (hook, user chốt hook=chương 0) đặt
  volume tĩnh theo niche khi có plan; `_duck_music` — envelope RIÊNG cho zone hook
  (nép cao hơn), clip nhạc phân zone theo TRUNG ĐIỂM (hook seg phủ [0, đầu ch2); body
  vào sớm XFADE nên trung điểm ≥ hook_end), warning ghi "M-VOL hook nép X tới Ys".
- Không plan → 1 envelope duck 0.2 + volume 0.2 phẳng — từng dòng như cũ.

**Rà chồng chéo:** BREATH_VOL 0.5/RAMP 2.5/MIN_BREATH 1.5 KHÔNG đổi (2 zone chung);
keyframe time_offset theo FILE NGUỒN giữ nguyên (capcut-volume-keyframe); ambient/drone/
subject-SFX volume không đụng; đường `--music` 1-file không zone (override tay);
video 1 chương = toàn hook (hiếm, chấp nhận). Empty-check `segment_keyframes` so với
duck ĐÚNG ZONE của clip — clip hook nằm trọn trong voice giữ volume tĩnh 0.35, không rác keyframe.

**Verify:** pytest FULL **454/454** (+3: `hook_duck_for` map/default · e2e 2 chương niche
space có plan → hook seg volume 0.35 + keyframe nép 0.35 nở ≤0.5, body seg 0.2 · e2e
không plan → mọi clip 0.2 phẳng kể cả có niche). Chạy thật SP012: stage `music` 4/4
chương neo accent/downbeat (ch4 tier A neo downbeat 22.89s, lead 0.08s) — draft video
kiểm cổng TAI ở entry dưới.

**⚠ CỔNG TAI CHƯA QUA — Claude không tự phán.** User nghe draft kiểm: (1) nhạc hook có
to hơn thân bài tự nhiên không (space 0.35 vs 0.2); (2) điểm nhấn nhạc rơi đúng cắt đầu
chương có "vào" không; (3) bài chọn theo usage tiến hóa (khác V12) có hợp mood không.

**Video kiểm cổng TAI đã dựng sẵn:** SP012 chạy `music` + `assemble` thật → draft
**`SCRIPT_20260709_071612_V13`** (so với V12 cũ cùng project). Verify máy: warning
"nhạc: 4 chương, theo music_plan" + "M-VOL hook nép 0.35 tới 61s" + ducking 7 clip.
Bài chọn KHÁC V12 (ch1 "7 __mysterious" thay "SP1-001 khoa học+bao la") — do usage
tiến hóa qua nhiều lần assemble (phạt mềm đa dạng, đúng thiết kế select cũ). User nghe:
hook to 0.35 vs body 0.2 · điểm nhấn tại cắt chương 61s/155s/384s · mood 4 bài.

## 2026-07-13 — MUSIC-SYNC-M3: M-ACCENT snap + M-CHANGE neo đổi nhạc — pytest 461/461, draft V14 CHỜ CỔNG MẮT+TAI

**Cổng TAI M2 ĐẠT** (user nghe V13 "mọi thứ có vẻ ổn" 2026-07-13). User hỏi thêm: nhạc
nhanh/nhiều đoạn chuyển (travel) thì cắt theo beat rõ hơn — có tính lại không? **Vòng 3
trên dữ liệu cũ:** editor 8.674 cut chia theo tier/tempo — tier A lift 0.96, nhanh
<0.45s lift 1.02, giao A+nhanh 0.99 (đều null); kênh top 1.233 cut 0.85-0.89. → KHÔNG
cần tính lại cho space/deepsea; trực giác user = ngữ pháp MONTAGE/TRAVEL (niche CHƯA đo,
cửa chờ: tier A + M-GRID + knob niche). Ghi memory editor-music-sync-study vòng 3.

**Cái gì đổi (M3 — chỉ khi có music_plan; mặc định TẮT nguyên trạng):**
- `music/plan.py`: 🔸 SNAP_TOL 0.3 / SNAP_CAP 15% / M_CHANGE_WIN ±2s / M_CHANGE_XFADE
  deepsea 0.5s (đổi gần-thẳng, 174 lần đo) space giữ 3.0; `music_boundaries` (điểm đổi
  nhạc chương neo mép cắt video gần nhất ±2s); `timeline_accents` (accent bài đã chọn
  chiếu lên timeline qua BẤT BIẾN P = start_offset + min(XFADE, ts) — đúng cả khi
  boundary dời/xfade đổi; pass đầu bài, không unwrap loop).
- `packager/coverage.py`: field `j_cut_start` (apply_j_cuts đánh dấu) + `snap_to_accents`
  — trượt mép CHUNG về accent−lead nếu ≤ tol; luật user: hook snap thắng (kể cả J-cut),
  body J-cut miễn; miễn mép giữa miếng thở + mép đã neo M-CHANGE; trần 15% ưu tiên
  hook > vào-ô-thở > body (cùng hạng: dịch ít trước); 2 cửa sổ quanh mép ≥ MIN_SHOT 0.7;
  mép vào ô thở giữ hình ≥0.2s sau voice; breathing/micro_dur co giãn theo mép (multi-shot
  vẫn chỉ chia phần thoại). Video-only — voice WAV không đụng (hệ tọa độ kép).
- `packager/assembler.py`: run_assemble chèn M-CHANGE→snap SAU apply_j_cuts TRƯỚC
  invariant check + đặt footage (Ken Burns/SFX/overlay tính sau mép mới — thứ tự MO_TA §3);
  `_add_music_by_chapter` nhận boundaries: seg nhạc theo boundary + xfade niche, offset
  điều chỉnh giữ P (accent vẫn rơi đúng điểm đổi nhạc).

**Vùng ảnh hưởng đã rà:** snap chạy trước `check_coverage_invariants` (bất biến kiểm
SAU dịch mép); `split_window` vẫn chỉ chia phần thoại (tail co giãn theo mép); ducking M2
phân zone theo trung điểm — boundary dời ≤2s rơi giữa crossfade, không đổi zone clip;
CoverWindow thêm field mặc định False — mọi constructor cũ chạy nguyên; overlay/SFX neo
theo word/voice không theo mép video.

**Verify:** pytest FULL **461/461** (+7: snap hook-thắng-J-cut · body-J-cut-miễn+trần
ưu tiên · miễn giữa-miếng-thở+exempt · không phá MIN_SHOT · music_boundaries ±2s ·
timeline_accents đúng tọa độ (cả boundary dời + tier C) · e2e draft: mép 9.0→9.07 đúng
µs, nhạc ch2 vào boundary−xfade, offset giữ P, warning M-ACCENT/M-CHANGE).
**Draft kiểm: `SCRIPT_20260709_071612_V14`** — M-ACCENT snap 3/105 mép (body, dịch
−50..−35ms; ít vì SP012 nhiều mép J-cut body miễn + accent thưa), M-CHANGE 3/3 điểm đổi
nhạc neo cut, M-VOL hook 0.35 giữ. **CHỜ CỔNG MẮT+TAI — Claude không tự phán.**


## 2026-07-13 — MUSIC-SYNC-M4/đóng gói: cổng MẮT+TAI M3 ĐẠT (V14) + cờ M-GRID + report

**M3 ĐẠT** (user duyệt V14). Đóng gói phần còn lại:
- **Cờ M-GRID (M4):** `autoedit music <dir> --sync-targets grid` → field
  `music_sync_targets` trong project.json; `timeline_accents` cho HOOK lấy downbeats
  (tier A) thay accents. Mặc định "accent" — hành vi đã qua cổng không đổi. Dùng khi:
  video TRAVEL đầu tiên (trực giác user "nhạc nhanh cắt theo nhịp rõ" — vòng 3 bác cho
  space/deepsea nhưng travel chưa đo; cổng MẮT phân xử, không tranh luận lý thuyết).
- **Report M7:** music_plan có → bảng "MUSIC SYNC" (chương/mood/bài/tier/offset/neo) thay
  bảng nhạc thường; không plan → bảng cũ nguyên vẹn.
- **make --music-sync:** pass-through xuống run() (truyền tường minh — bug OptionInfo).
- Vùng ảnh hưởng: field mới default "accent" — project.json cũ load bình thường
  (pydantic default); report nhánh cũ giữ nguyên khi không plan.
- **Verify:** pytest FULL **462/462** (+1: grid hook dùng downbeat, body giữ accent,
  B-không-downbeat rơi về accent, default accent như cũ).

**TRẠNG THÁI GÓI MUSIC SYNC: ĐÓNG** (4 cơ chế chạy sau `--music-sync`, mặc định TẮT).
Cách dùng theo niche: **space** = bật được ngay (2 cổng V13/V14 đạt) · **deepsea** =
video kiểm chiến dịch deepsea sắp tới BẬT `--music-sync` để cổng TAI nghe hook 0.30 +
đổi-nhạc-gần-thẳng 0.5s (hai số này CHƯA được tai kiểm) · **travel** = khi có draft
editor/video mẫu travel: đo lại (~15′ script cũ) + video kiểm `--sync-targets grid`.


## 2026-07-13 — LUẬT ĐỨNG music-sync theo niche + SP1-017 ĐẠT cổng mắt

**User chốt 2 việc:**
1. **Luật đứng bật music-sync theo niche** (memory `music-sync-niche-default`):
   **space mặc định BẬT** — prompt dựng giữ nguyên format cũ, không cần ghi flag;
   ghi "không music-sync" mới tắt. Đường hội thoại: Claude tự chạy `autoedit music`
   sau `cut`. **Deepsea**: bật từ VIDEO KIỂM chiến dịch deepsea (= cổng TAI cho hook
   0.30 + đổi-nhạc-gần-thẳng 0.5s — 2 số chưa nghe), qua rồi mới thành mặc định.
   **Travel/niche mới**: tắt tới khi đo dữ liệu editor/kênh top (~15′ script cũ);
   travel = ứng viên đầu thử `--sync-targets grid`.
2. **SP1-017 "Edge of the Universe": CỔNG MẮT ĐẠT** (user "đã ok") — bàn giao editor
   thật hoàn thiện. KHÔNG dựng lại bản music-sync (draft trong tay editor; gói ra đời
   sau bản dựng). Bảng milestone SP1-017: ✅.

## 2026-07-13 — TCF-FILE-NGUỒN: cổng duration cho chapter YouTube + tcf-gen mode file nguồn — pytest 466/466

**User phát hiện lỗ hổng thật:** video mẫu tải về editor hay CẮT BỎ đoạn → không khớp
bản YouTube → chapter yt-dlp map giây file TRƯỢT MỐC (section_hint sai mọi cảnh sau
điểm cắt). Cờ điểm nhô ĐÃ có cổng duration (§3d) nhưng chapter dùng mù (ingest.py:505
cũ) — đúng mẫu "bug anh em cùng pattern" P5. User hỏi thay hẳn bằng tcf-gen → chốt:
GATE + FALLBACK (chapter tác giả = ground truth khi file khớp; máy sinh chỉ gánh khi trượt).

**Cái gì đổi** (mô tả: `MO_TA_VAN_HANH_TCF_FILE_NGUON.md`, chỉ nhánh viral/mẫu — own không đổi):
- `ingest.yt_chapter_gate`: chapter YouTube qua CÙNG cổng `duration_mismatch` >3% với
  cờ điểm nhô (2 cổng độc lập, không đụng logic peak) — trượt = bỏ + warning. Title
  GIỮ NGUYÊN (không phụ thuộc timeline).
- `tcf_gen.source_chapters` (mode FILE NGUỒN — đóng mục CÒN NGỎ từ hôm TCF): transcribe
  CHÍNH file mẫu → block 45s giây FILE → NÃO Sonnet (cùng SYSTEM/snap NT4 với tcf-gen own)
  → `[{start_time,end_time,title}]` đúng khuôn YTVideoInfo.chapters (`_chapter_at` đọc
  thẳng). Cache 2 tầng bền `SRC__<file>.words.json`/`.tcf.json` trong pause_scan_cache.
- Ưu tiên hint mới: yt (duration khớp) → file bối cảnh editor → tcf-gen file nguồn
  (client NÃO tạo LƯỜI — mẻ bình thường không import claude/whisper); mọi lỗi fail-open
  hint "" như trước. Dry-run in "⚠ TRƯỢT MỐC (sẽ bỏ → tcf file nguồn)" per video.

**Vùng ảnh hưởng đã rà:** consumer `info.chapters` chỉ 2 chỗ (ingest + dry-run echo) —
gate cả 2; cache key `SRC__` tách khỏi `label__` pause-dna; `--retag` ăn hint mới =
hồi tố được; own path nguyên vẹn.

**Verify:** pytest FULL **466/466** (+4: source_blocks gom block · source_chapters đúng
khuôn + cache NÃO không gọi lại + map bằng chính `_chapter_at` · ít lời <200 từ không
sinh mù · yt_chapter_gate lệch 10% bỏ + warning, khớp giữ, không-chapter không warning rác).

---

## 2026-07-13 — SHOT THỞ 3.0: LIÊN TỤC CHỦ THỂ (user xác nhận sai logic từ đầu — cả space lẫn deepsea)

**Cái gì đổi:** luật chọn footage cho ô hình thở viết lại (`sourcer/breath.py`). User xem
DS5-083 gặp lại đúng lỗi ở space → chốt: KHÔNG nhặt theo "đắt/điểm nhô" nữa; nhặt footage
LIÊN QUAN footage liền trước ô — **TIẾP TỤC CHỦ THỂ** (cá mập → vẫn cá mập), chỉ **ĐỔI CỠ
CẢNH** cho đỡ nhàm.

**Vì sao (3 gốc rễ đo được trên DS5-083, 31 miếng):**
1. Điểm chọn cũ KHÔNG có tiêu chí chủ thể — "liên quan" chỉ đo bằng mood (2,0/tag).
2. **BUG mood câm:** director trả mood ghép `awe_urgent_cautionary`, `_mood_set` chỉ split
   dấu phẩy → 29/31 miếng note "mood —" → máy chỉ còn "đủ dài + wide/aerial + khác cỡ",
   bonus wide/aerial (proxy "đắt") thành tiêu chí dẫn dắt: thuyền cá→orca aerial,
   sói→asteroid flyover, domino→pterodactyl, phố mất điện→mực, rừng→hàm megalodon.
3. **BUG pool đói:** `videos_for_niche` trần 500 clip mới-index-nhất — kho deepsea 7.940
   video own → pool chỉ thấy 6%, chủ thể nạp sớm không bao giờ được cân.

**Cách sửa:** điểm mới = **chủ thể +3,0/token trùng** (trần 3 token; token hóa subject+tags
kho, bỏ stopword; token NỀN NICHE >25% pool không tính — đo runtime từ pool thật, tự thích
nghi niche, pool <40 không demote) · khác cỡ cảnh +2,0 (nâng từ 1,0 — cơ chế đổi vị chính
trong cùng chủ thể) · đủ dài +1,5 · mood +0,5/tag phụ trợ (fix `_mood_set` split thêm
`_`/`/`) · chưa dùng +0,5 · **BỎ wide/aerial**. Neo chủ thể CỐ ĐỊNH cho mọi miếng trong ô
(bỏ chuỗi-mood-nối 2.0 — làm chủ thể trôi); cỡ cảnh vẫn so miếng liền trước. Neo: clip
local → tra db theo path (kể cả ảnh/viral); stock/gen → `visual_concept`. `videos_for_niche`
500→50k (lấy trọn kho). Timing hold 0,5 / k miếng / mép voice kế GIỮ NGUYÊN 2.0.

**Tài liệu viết lại (yêu cầu user):** `MO_TA_VAN_HANH_SHOT_THO.md` **§7 mới** (vấn đề +
luật + bảng điểm + RÀ CHỒNG CHÉO + cổng kiểm) + 📌 hết-hiệu-lực tại §2c;
`foundation/d2-hinh-tho.md` **📌 LỆCH SO VỚI BẢN GỐC** (mọi câu "footage đắt cho ô thở"
đọc theo luật mới, bản gốc giữ đối chiếu); docstring breath.py/BreathShot/runner.

**Rà chồng chéo (tóm tắt — đủ ở MO_TA §7.3):** luật user 2026-07-08 (mood chủ đạo + ưu
tiên đắt) LẬT CÓ CHỦ ĐÍCH bởi chính user; PEAK_BONUS ytref không đụng (chỉ chảy phễu
thoại); chặn viral trong pool shot thở GIỮ; `_mood_set` chỉ breath dùng — music
`_chapter_moods` đã split `_` sẵn, vision validator raise to tiếng → không anh em cùng
pattern sót; assembler/coverage/ducking/report không đụng (chỉ ĐIỂM chọn đổi, BreathShot
schema giữ, note đổi format nhưng report không parse note).

**Verify:** pytest FULL **474/474** (+6 test breath, 3 hồi quy tái hiện bug trước-fix:
mood ghép câm · sói-thua-asteroid · neo trôi miếng 2; +generic-demote/sàn pool/subject-token).
**CHỜ:** dựng lại DS5-083 (re-pick breath + re-assemble, KHÔNG re-source cả video) làm
cổng số §7.4 + cổng MẮT user — Claude không tự phán.
**CẬP NHẬT cùng ngày:** DS5-083 dựng lại xong (31/31 miếng dur khớp bản cũ) — **cổng MẮT
user DUYỆT 2026-07-13** ("phần hình thở tôi check đã ok"). SHOT-THO-3 ĐÓNG TRỌN.

---

## 2026-07-13 — BAN-THUOC: luật "VOICE kể ẩn dụ — HÌNH kể câu chuyện" (mọi niche) + retrofit DS5-083

**Cái gì đổi:** user xác nhận lỗi "bán thuốc" (minh họa nghĩa đen của chữ thay vì kể câu
chuyện chương — gặp ở space, lặp ở DS5-083 b014-b019/b024/b048: script ví von tháp Jenga
→ tool tải clip Jenga thật từ Pexels). Chốt luật đứng scope CHẶT: mọi thủ pháp tu từ
(ẩn dụ/ví von/giả định/nói-với-người-xem) → `visual_concept` Ở LẠI thế giới
video_subject/central_subject, diễn ẩn dụ bằng hình TRONG thế giới đó; chỉ rời khi content
nói thực thể/sự kiện THẬT. Chi tiết + bảng thực thi + rà chồng chéo:
`MO_TA_VAN_HANH_BAN_THUOC.md`; 📌 LỆCH tại `foundation/c2-an-du-veto.md` (cấp metaphorical
định nghĩa lại = ẩn dụ thị giác TỰ THÊM diễn in-world).

**Vì sao (3 gốc rễ đo được):** (1) pass 1 tự đầu độc neo — central_subject ch1 chứa
"(Jenga tower metaphor)"; (2) pass 2 có luật campfire→SUN nhưng ngoại lệ "central_subject
ABSTRACT được giữ vật bề mặt" mở cửa ("food web" đọc là abstract) + từ điển ẩn dụ generic
(dominoes/chess/coins) xúi đi off-world; (3) đường SÂU — đường dựng chính — mù hoàn toàn:
direct_context.md không có dòng coherence nào, skill dung-video còn cấp giấy phép "beat
ẨN DỤ CHỦ ĐÍCH vẫn generic". Bằng chứng then chốt: 45/56 beat metaphorical NÃO TỰ nghĩ
đều tự neo in-world đúng — bệnh CHỈ phát khi script mang sẵn ẩn dụ → hạ nguồn (sourcer/
ranker/breath đều trung thành với concept) không cần đổi, KHÔNG thêm luật lật ở phễu.

**Sửa:** 5 chỗ luật (prompts.py ×3 khối + live.py `_BAN_THUOC_BLOCK` + SKILL.md) + lưới
máy `ban_thuoc_warnings` ở direct-ingest (0-token-trùng video_subject+central_subject,
gọt số nhiều, entity/graphic miễn, **warning-only** giữ filter-overload-guard; điểm mù
đã biết: central_subject nhiễm ẩn dụ thì lưới mù — pass 1 gác tầng đó).

**Retrofit DS5-083 (cổng mắt của fix):** khử độc central_subject ch1 → viết lại concept
11 beat (b014-b020, b024-b025, b048, b109) → re-source LẺ qua phễu c5 thật (scratchpad
`ban_thuoc_step2_resource.py`: seed ViralLedger 137 pick viral hiện có + REF prefix, P7
trừ pick cũ beat bệnh, mạch c3 nối từ hàng xóm thật, C5 gate bật) → 11/11 ok, toàn bộ về
thế giới cá mập/đại dương (b048 domino→great white close-up) → re-pick breath 31 miếng
**dur khớp 100%** (b048 hết nautilus-qua-token-"chain" → battle-scarred great white) →
assemble _V2 + report. Lưới máy quét cả 270 beat: kêu 32, soi tay 0 cần sửa thêm (toàn
diễn-đạt-khác-từ hoặc nội dung thật — FP đúng như thiết kế warning-only). Phát hiện kèm:
concept b050 nhiễm chữ sản xuất "title-card opener" làm breath nhặt asset intro-text →
gọt concept (kho không có seagrass nên b050 về clip fox như bản user đã duyệt — còn ngỏ
data hygiene kho); b065/066/176/177 concept mô tả CHART thay cảnh — ghi nhận MO_TA §7,
chưa sửa.

**Vùng ảnh hưởng đã rà:** 2 tầng NGƯỢC CHIỀU buộc sửa cùng lượt (từ điển ẩn dụ + ngoại lệ
skill — nếu không prompt tự mâu thuẫn); ranker/V3/C5/REF/C4/shot-thở-3.0 đều cùng chiều
hoặc người-theo-lệnh, không tầng nào lật; đường direct cũ ăn luật prompt nhưng KHÔNG có
lưới máy (fallback, ghi còn ngỏ).

**Verify:** pytest FULL **478/478** (+4: 2 prompt mang luật + 1 hồi quy lưới máy bắt
Jenga-trong-chương-cá-mập/miễn-entity-graphic/khớp-số-nhiều + 1 fail-open không neo).
**CHỜ:** cổng MẮT user trên draft _V2 (11 beat theo mốc phút đã gửi) — Claude không tự
phán; adherence prompt đo thật ở video dựng mới kế tiếp (lưới máy là chỉ báo sớm).
**CẬP NHẬT cùng ngày:** **cổng MẮT user DUYỆT 2026-07-13** ("duyệt bước này") → BAN-THUOC
ĐÓNG TRỌN; draft hiện hành của DS5-083 = bản **_V2**. Còn theo dõi: adherence prompt ở
video dựng mới kế tiếp (mọi niche) + 3 cờ editor soát tay đã khai (b019 mood/b020 C5 chê/
ô thở b050 fox — pick có từ bản đã duyệt trước, không phải hồi quy).

### 2026-07-13 — SFX-LOAI-A: kind loài per-niche + nạp 28 tiếng cá voi từ sheet editor (deepsea)

**Cái gì đổi:** `subject_rules.yaml` per-niche (thay trọn SUBJECT_RULES khi tồn tại) + `subject_kind()` match cụm từ + `niche_kinds()` cho import + mine.py classify per-niche & fix `_kw` số dán đuôi; kho deepsea +28 file (whale_sperm/humpback/blue/orca · attack · splash · default) + re-kind ocean_14/21→splash; dọn hold 323→301, staging nhạc bỏ 2 pad, sfx staging bỏ 3 whoosh attack + thêm Water Whoosh (DS3_008).
**Vì sao:** user so bài máy với editor thật — SFX hiện trường quá ít; phân tích ra 21/41 tiếng đắt nhất nằm hold không kind, bảng match sinh cho space không có từ vựng loài (PHAN_TICH_SFX_EDITOR_DEEPSEA.md). Sheet editor = ground truth; user duyệt A/B/C, mật độ chốt "thân bài = 50% hook" (làm milestone C).
**Verify:** pytest FULL **481/481** (+3 test mới, regression word-boundary/space giữ) · ambient-import 28/28 lỗi 0 · smoke 3.000 asset tag thật → 454 match đúng ưu tiên loài-trước-hành-động · rerun editor-learn DS1_046 + DS3_017 dry-run **0-mới**. Cổng TAI chưa — đi ké video kiểm deepsea (chung cổng music-sync hook 0.30, user chốt "volume music ở hook tính sau").
**Vùng ảnh hưởng đã rà:** C1 ô thở cùng chiều (subject>scene>default nguyên vẹn) · S2 volume/trần KHÔNG đổi ở A · music-sync hook to có thể che tiếng loài (kiểm chung 1 cổng tai) · editor-learn cập nhật cùng gói · space/travel không đổi. Chi tiết: `MO_TA_VAN_HANH_SFX_LOAI.md §3`.

### 2026-07-13 — SFX-LOAI-C: gỡ trần S2 (match-driven) + bed ục ục drone deepsea + nạp 37 file SOUNDEFFECT

**Cái gì đổi:** (1) `subject_beat_slots` BỎ trần SUBJ_CAP/không-kề/≤2-lần-kind — user chốt "không có mật độ, thấy footage phù hợp là để sfx phù hợp" (đổi chốt 50%-hook trước đó; áp CẢ space); giữ ảnh/đồ họa/beat-ngắn skip + SUBJ_MAX. (2) Điều tra "ục ục cả bài" trên 23 draft editor → `dưới nước 4` (13 draft, phủ 45-60%, vol 0.32-0.56) + Dưới nước 2 + Scuba Diving = kind `drone` deepsea 3 biến thể, 🔸 `DRONE_VOL_BY_NICHE["deepsea"]=0.25` (space giữ 0.15). (3) Nạp `F:\DEEPSEA\SOUNDEFFECT` 37 file: orca KÊU +2 · humpback +5 · signal +5 · ocean +5 (2 file sheet thiếu) · fire +4 · **underwater 13** · nature_water 2. (4) Vá 2 lỗ scene fallback: scene `underwater` 8.498 asset + `nature_water` 923 mà kho 0 file → ô thở dưới nước trước nay rơi hết về default. (5) seabird tách khỏi ocean (re-kind ocean_17/23).
**Verify:** pytest FULL **482/482** (test caps viết lại thành hồi quy đảo chiều: beat kề + kind lặp GIỜ PHẢI có tiếng; +test drone_vol niche) · import 37/37 lỗi 0 · smoke: seagulls→seabird, killer whales attacking→whale_orca (loài trước hành động), drone 3 file vol 0.25. Sheet: **39/41 dòng có tiếng trong kho** (2 còn lại có bản tương đương). Cổng TAI CHƯA — video kiểm deepsea gánh chung 4 lớp (bed 0.25 + loài không trần + nhạc + M-VOL hook 0.30).
**Vùng ảnh hưởng đã rà:** gỡ trần áp chung space (bảng match space hẹp → tăng ít, drone space 0.15 nguyên) · underwater/nature_water/drone KHÔNG vào subject_rules (spam S2) — chỉ C1 fallback + S1 · sourcer/breath.py có SUBJ_CAP RIÊNG (token shot thở) không liên quan · music_editor/sfx staging không đổi thêm. `MO_TA_VAN_HANH_SFX_LOAI.md §5-6`.

### 2026-07-13 — SFX-LOAI-C2: bed ục ục GATE THEO CẢNH underwater (user sửa nhận định — không loop cả bài)

**Cái gì đổi:** user sửa chốt cùng ngày: bed "ục ục" theo sheet editor CHỈ đặt trên CẢNH DƯỚI NƯỚC, không phải loop suốt video. (1) `bed_intervals()` mới (schedule.py): đơn vị beat trọn (voice + thở, tới timeline_start beat kế), pick scene ∈ gate → vào run, beat liền gộp, run < `BED_MIN=6s` bỏ; (2) `DRONE_SCENE_BY_NICHE={"deepsea": ("underwater",)}` — space/travel không gate, loop y cũ; (3) `_add_drone` loop file trong TỪNG run (fade 2s/3s mỗi run), mù cache.db → tầng TẮT (bed đè cảnh mặt biển tệ hơn không bed), `drone_log` + report thêm covered_s/runs/gate.
**Vì sao:** đo lại 23 draft editor xác nhận chốt mới: bed = 383 ĐOẠN (median 40s), phủ 13–98%/bài, gap thật 4–630s tại cảnh mặt biển/bản đồ/người — không draft nào loop nguyên bài trừ DS-53 (98%).
**Verify:** pytest FULL **485/485** (+3: bed_intervals merge/min · _add_drone gate 2 run + vol 0.25 + khoảng giữa trống · mù tag → tắt + warning; regression space loop giữ) · smoke DS5-083 THẬT: 33 run, phủ 1260/1876s = **67%**, run median 25.8s — đúng dải editor; 63 beat cảnh không-dưới-nước hết bị bed đè. Cổng TAI vẫn chờ video kiểm (4 lớp).
**Vùng ảnh hưởng đã rà:** space/travel loop y cũ (gate rỗng) · C1 ô thở underwater CHỒNG bed trong ô thở cảnh dưới nước (editor cũng chồng — tai quyết) · bed đọc scene từ PICK ≠ C1 đọc miếng shot thở (lệch hiếm, shot thở 3.0 liên tục chủ thể) · report/runner đọc drone_log key mới có default — draft cũ không vỡ. `MO_TA_VAN_HANH_SFX_LOAI.md §5b`.

### 2026-07-13 — SFX-NUOC-DONG: kind water_churn + ocean mở rộng + tag lại 4 pick stock fail (từ 4 vấn đề user nêu trên DS5-083 V3)

**Cái gì đổi:** user xem V3 nêu 4 vấn đề (chẩn đoán đầy đủ: memory `ds5-083-4-van-de-sfx-lap`) → duyệt 2 gói làm, 2 giữ nguyên. Gói này (vấn đề "cảnh sóng/nước động không tiếng"): (1) `subject_rules.yaml` deepsea thêm kind **`water_churn`** (bubble/gurgle foley) + nạp 10 file folder editor "Nước động" (kho deepsea 133 file/24 kind); (2) `ocean` thêm 8 cụm mặt-biển-động: choppy · rough sea/seas · stormy sea/ocean · surf · foam/foamy (đo kho 10.618 asset TRƯỚC khi thêm — lớn nhất bubbles 67, không nguy cơ overload; "surf" \b không dính "surface"); (3) `tag-stock` DS5-083 → vá 2/4 pick stock mù tag (lỗi thật của b43: M3b vision FAIL nên S2 mù — tag mới "turbulent ocean waves crashing" ra `ocean` bằng keyword CŨ).
**Vì sao:** b43 user thấy sóng không tiếng sóng; kho vốn có 28 file ocean — thiếu ở tag + từ vựng nước-động. Match-driven đã chốt ở SFX-LOAI-C nên chỉ cần data.
**Verify:** ambient-import 10/10 lỗi 0 · quét 270 pick DS5-083 bằng code path thật (`db_subject_lookup`+`subject_kind` rules mới): +6 beat có tiếng mới → soi text đầy đủ từng hit: 5 ĐÚNG (bubbles/sediment thật), **1 SAI (b220 "green smoke swirling" ăn bare `swirl`) → siết ngay: bỏ bare swirl/swirling, thay cụm 2 chiều** (swirling water/sand/sediment/current + chiều ngược) → quét lại 5/5 đúng, b220 out · pytest FULL **485/485** (0 code đổi — thuần data yaml+kho, không commit git).
**Vùng ảnh hưởng đã rà:** editor-learn mine classify dùng chung yaml — file editor tên "Bubbling/Gurgling" nay route `water_churn` thay vì hold (đúng chủ đích §1.4) · space/travel không yaml riêng → 0 đổi · `underwater`/`nature_water` vẫn CỐ Ý ngoài subject_rules (chống spam S2) · thứ tự ưu tiên: water_churn đặt SAU ocean (cảnh mặt biển thắng) TRƯỚC water/default.
**Còn ngỏ:** b75/b142 (và mọi asset tương lai cùng bệnh) fail GLM 4-retry vì "mood ngoài vocabulary" → asset mù tag VĨNH VIỄN, S2/C1 mù theo — cần quyết: validator mood nên LỌC mood lạ (giữ phần tag đúng) thay vì loại cả asset? Chờ user. Vấn đề #1 (seabird b85): máy ĐÃ đặt `seabird.wav` 560.8–568.2s vol 0.18 — user tự nghe lại V3, không đổi volume. Vấn đề #4 (lặp cùng-nguồn-khác-cảnh): user chốt GIỮ NGUYÊN, không thêm luật cooldown.

### 2026-07-13 — HOOK-SFX: tầng S3-HOOK hit/whoosh/click tại cut trong hook (deepsea) + dựng V4

**Cái gì đổi:** (1) ĐO 23 draft editor deepsea (`PHAN_TICH_HOOK_SFX_EDITOR_DEEPSEA.md`, script scratchpad `do_hook_editor.py`): hook median 4,8 SFX/phút = 3× body, 0/23 hook trống, **bám CUT video 48% ±0,25s — TEXT 3%** (ngược PB12 space → luật per-niche, PB12 không lật), 13% lead 0-200ms, top loại = hiện trường nước + camera click + BOOM + whoosh. (2) Code tầng S3-HOOK (`MO_TA_VAN_HANH_HOOK_SFX.md`): `hook_sfx_slots()` pure trong schedule.py (click bám cut-vào-ẢNH trần 4, đặt cả khi đủ mật độ · impact tại cut-accent · whoosh trước cut 80ms · chỉ BÙ tới `HOOK_SFX_PM=4,8` đếm cả S2/C1/UI-sfx · gap 3s) + `_add_hook_sfx` assembler (cuối chuỗi audio, track sfx, xoay biến thể crc32, không fade-in, fail-open) + `cuts_log` param `_place_video_l1` + hoist `music_accents` + field `project.hook_sfx_log`. (3) Nạp 18 file editor → kho **ambient per-niche deepsea** (impact 7 · whoosh 6 · click 5; `AMBIENT_KINDS += HOOK_SFX_KINDS`) — cố ý KHÔNG vào kho sfx toàn cục.
**Vì sao:** vấn đề #3 user nêu (hook chỉ 1 layer ục ục); user duyệt thiết kế "theo ý bạn" + "làm gói hook trước sau đó dựng lại v4".
**Verify:** pytest FULL **490/490** (+5) · dựng lại DS5-083 → draft **_V4** (xem entry số bên dưới khi assemble xong). **CỔNG TAI user CHỜ** — 5 lớp hook cùng kêu: voice · nhạc M-VOL 0,30 · bed 0,25 · S2/C1 · S3 0,2 🔸.
**Vùng ảnh hưởng đã rà:** đủ 8 tầng trong MO_TA §3 (PB12/S2C1/S1+M-VOL/M-SNAP/overlay-chart-sfx/kho toàn cục/subject_rules/space-travel) — không tầng nào lật; space/travel 0 đổi (gate niche, regression giữ).

### 2026-07-14 — HOOK-SFX-SPACE: mở S3-HOOK cho space (mượn số deepsea 🔸) + quy trình lấy mẫu SFX niche mới

**Cái gì đổi:** (1) Kho `F:\AutoEdit\ambient\space` nạp đúng 18 file hook cùng nguồn editor `F:\DEEPSEA\SOUNDEFFECT` (impact 7 · whoosh 6 · click 5 — qua `import_from_manifest`, normalize C4, records truy license). (2) `schedule.py::HOOK_SFX_NICHES = ("deepsea", "space")` + 📌 comment mượn số; test `test_add_hook_sfx_gate_niche_off` đổi niche-tắt space→travel + assert hồi quy `"space" in hook_sfx_niches()`. (3) `MO_TA_VAN_HANH_HOOK_SFX.md`: block 📌 LỆCH đầu file + **§3b rà chồng chéo riêng space**. (4) Chuẩn hóa quy trình cho niche sau: **`QUY_TRINH_LAY_MAU_SFX_NICHE_MOI.md`** (B1 editor-learn → B2 sheet→subject_rules.yaml → B3 nạp kho per-niche → B4 ĐO hook → B5 quyết gate + hằng số / B5b mượn số → B6 cổng tai) + bảo tồn script scratchpad vào repo **`scripts\do_hook_editor.py`** (tổng quát hóa `<niche> <root...>`, smoke DS1-050 ra đúng số đợt đo gốc) + **`scripts\nap_hook_sfx.py`** (template 3 hằng NICHE/SRC/FOLDER_KIND).
**Vì sao:** user chốt 2026-07-14: "áp dụng gói hook này cho cả space vì 2 niche gần giống nhau; sau này space có số liệu rồi sẽ áp dụng số liệu của space" + "kiểm tra lại công việc lấy mẫu sfx này cho các niche khác sau này sẽ làm như thế nào".
**Verify:** pytest FULL **490/490** · `library_status(space)` = impact 7/whoosh 6/click 5 · smoke script đo trên DS1-050 khớp số đợt đo gốc. Hiệu lực từ video SPACE dựng mới kế tiếp — KHÔNG dựng lại video cũ; **cổng TAI đi ké video space kế** (điểm nghe: click-vào-ảnh lần đầu nổ thật + 4/6 whoosh vị nước + S3 0,2 🔸 chồng mix hook space đã duyệt V13/V14).
**Vùng ảnh hưởng đã rà (§3b MO_TA):** PB12 = điểm căng duy nhất (S3 bám CUT ≠ hành vi đo được của editor space bám TEXT — user biết và chốt mượn, cổng tai trọng tài; PB12 bản thân không lật, overlay-SFX bám text vẫn chạy y cũ); overlay-SFX space dày → S3 tự bù ít đi (đếm busy + gap 3s); deepsea 0 đổi hành vi (số dùng chung y nguyên); travel vẫn tắt chờ đo.

### 2026-07-14 — HOOK-SFX-V4-TAI: cổng tai V4 rớt mật độ → HOOK_SFX_PM còn 30% (1,44/ph) + dựng _V5

**Cái gì đổi:** `HOOK_SFX_PM` 4,8 → **1,44** (schedule.py, 1 hằng dùng chung nên phủ CẢ deepsea + space); click GIỮ NGUYÊN luật riêng (bám cut-vào-ảnh, trần 4 — hook V4 không có click nên ngoài khiếu nại); vol 0,2 🔸 giữ (user chưa phán riêng volume). 3 test cập nhật: density 250s (round 1,44×250/60 = 6 tiếng, giữ coverage impact/whoosh-lead/gap) + **hồi quy tái hiện trước-fix** "hook 60s giờ bù 1 tiếng (trước: 5 — dày đặc)" + wire hook 90s (đích 2 = click@12 + impact@8, cut thường KHÔNG whoosh vì deficit hết). Warning assembler ghi rõ "mật độ còn 30% số editor — cổng tai V4". 📌 block vào `MO_TA_VAN_HANH_HOOK_SFX.md` + bài học vào `QUY_TRINH_LAY_MAU_SFX_NICHE_MOI.md` B5: **số đo editor là điểm XUẤT PHÁT, cổng tai user đè** (mix video công ty nhiều lớp khác kênh tham chiếu).
**Vì sao:** user nghe hook V4 DS5-083: "tiếng sfx ở hook không phù hợp — chỉ có tiếng whoosh với impact xuất hiện dày đặc làm khó chịu; giảm tần suất 2 tiếng này ở cả 2 niche xuống 30% so với hiện tại".
**Verify:** pytest FULL **490/490** · dựng lại DS5-083 → draft **`DS5_083_OCEAN_WITHOUT_SHARKS_20260713_030358_V5`**: hook 154s S3 = **3 tiếng (V4: 10) = đúng 30%** — impact 3 tại cut-accent 21,1s / 62,5s / 75,3s (~1,2/phút, thưa hẳn), whoosh 0 (impact-accent ưu tiên ăn hết deficit), click 0 (hook không ảnh). **CHỜ TAI V5.**
**Vùng ảnh hưởng đã rà:** chỉ 1 hằng mật độ đổi — click/vol/gap/lead/track/xoay-biến-thể y nguyên; S2/C1/S1/bed/nhạc không đụng (S3 vẫn đếm chúng vào busy); space chưa dựng video nào với S3 nên không có draft phải dựng lại; test gate travel giữ.

### 2026-07-14 — DS3-084 "Womb Cannibalism" (deepsea) DỰNG XONG + fix bug crash Path(None) khi có needs_human

**Cái gì đổi (bug fix phẫu thuật):** `ambient/schedule.py::subject_beat_slots` dòng ~407 — thêm guard `or not pick.asset_path` trước `Path(pick.asset_path)`. Bug: beat **needs_human** có ShotPick (record tồn tại) nhưng `asset_path=None` (ảnh entity tải hỏng) → `Path(None)` ném `TypeError: expected str... not NoneType` → **assemble CRASH sau 588s** ở `_add_subject_sfx`.
**Vì sao lộ bây giờ:** DS5-083 có **0 needs_human** (kho DS083 phủ đủ) nên chưa bao giờ chạm nhánh này; DS3-084 có **40 needs_human** (nhiều beat entity: nhà khoa học có tên, Minto Coalfield, IUCN listing — ảnh wiki/instagram/facebook tải hỏng) → lần đầu tiên `subject_beat_slots` gặp shot asset_path=None.
**Vùng ảnh hưởng đã rà (P5):** grep MỌI consumer `.asset_path` — assembler.py:215/224 đã guard `not shot.asset_path`, colorcheck/report/stock_tags/cli đều `if ... asset_path`; **CHỈ dòng 409 subject_beat_slots thiếu guard** (schedule.py:251/356/367 khác dùng `b.asset_path` có guard sẵn). Fix 1 dòng, không đụng consumer khác.
**Verify:** pytest FULL **491/491** (+1 regression `test_subject_beat_slots_skips_none_asset_path` tái hiện crash trước-fix: shot path=None → bỏ qua, không ném) · re-assemble exit 0 (50s) · draft sinh OK.

**Bài (deepsea, music-sync BẬT):** voice 1177,8s (19:38) / 2479 từ / 6 chương / **230 beat** / 33 ô thở / timeline 1309s (21:49). Nguồn: `F:\DEEPSEA\VOICE + CONTENT\DS3 - 084`. Mẫu `--ref F:\DEEPSEA\VIDEO MAU\DS084` (10 phim cá mập hổ cát/lemon/great white). Nội dung: cá mập hổ cát ăn thịt đồng loại trong tử cung (adelphophagy + oophagy) → sinh 1 pup/bên, mẹ nuôi bằng trứng 9-12 tháng → Critically Endangered.
**Draft hiện hành = `E:\CapCut Drafts\DS3_084_WOMB_CANNIBALISM_20260713_224919_V2`** (folder crash đầu dời `.recycle_bin/..._INCOMPLETE_CRASH`; _V2 = bản đủ sau fix, project.json trỏ đúng). Music-sync 6 chương neo accent/downbeat lead 0,08s + M-VOL hook nép 0,3 tới 271s + xfade 0,5s.
**Source:** 230 beat — route 183 ok / 7 graphic / **40 needs_human** (kho thắng 39 · pexels 116 · entity 32 · chart 3); viral c8 46 cảnh/8 nguồn (gate chặn 630 lượt); C4 local-first 121/190 beat có ứng viên kho. **CỔNG MẮT + CỔNG TAI CÒN CHỜ** (user kiểm draft _V2).

**Đường đạo diễn (fan-out 6 chương song song, đường sâu vì ch6 = 546 từ > ~424 timeout `direct`):** normalizer python coerce schema + tách beat >10s (transcript timing) + cap 1 rhetorical/chương + xóa query cho graphic-route. **BÀI HỌC:** agent đạo diễn hay chết "Connection closed mid-response" ở chương dài — re-dispatch idempotent (ghi cùng file), 2 chương phải chạy lại; direct-ingest vòng 1 báo 9 lỗi cứng → normalizer vá → vòng 2 pass (chỉ warning bán-thuốc/same-shot-size, warning-only).

**Thời gian các bước:** new 1s · align 103s · direct-context 0s · direct (fan-out 6 agent ~5-6′ có retry) · cut 16s · music ~0s · **source ~42′ (194→230 nhảy nhanh cuối; ~32s/beat, chậm hơn DS5-083 26s vì nhiều pexels coastal/lab mới)** · assemble 50s (lần 2, sau fix) · report 0s. Wall pipeline lõi ~50′ (chưa kể debug bug + pytest).

### 2026-07-14 — LUẬT WORLD-LOCK (giữ mọi hình trong thế giới niche) + retrofit DS3-084 _V3

**Cái gì đổi:** luật cấp NICHE mới `WORLD_LOCK` (data-driven, `director/live.py`) — niche khai trong dict (hiện chỉ **deepsea**) thì MỌI `visual_concept`/`central_subject` phải ở trong thế giới hình của niche (deepsea = dưới nước/đại dương), KỂ CẢ khi script chủ đích nói về người/y học/đất liền. `world_lock_block()` sinh khối luật → chèn vào `direct_context.md` (đường sâu — sau bán-thuốc, trước OUTPUT) + `library_context` đường direct cũ (`runner.py`, parity). Fail-open: niche không khai → '' (space/travel y như cũ). 3 cửa luật đóng: (1) concept sai thế giới, (2) route `entity` ảnh người/y-khoa, (3) `central_subject` mời người ngoài thế giới vào ("...and the researchers who study them"). Kho thiếu đúng chủ thể → rơi về NỀN NICHE (nước tối/đàn cá/cá mập), KHÔNG rơi về người (WRONG-vs-BLAND).
**Vì sao:** user chốt 2026-07-14 (DS3-084): b17-24 "phôi cá mập" → miệng người/nhện; b59/b42/b47/b108 nghiên cứu cá mập → lab/nhà khoa học; b187/b209 abstract → người cồn cát/hoàng hôn; b213-217 "in people/vanishing twin/ultrasound" → ảnh siêu âm người. KHÁC lỗi bán-thuốc (mượn ẩn dụ) — đây là script kể chuyện THẬT ngoài niche, HÌNH vẫn phải kể bằng thế giới niche vì khán giả deepsea tới để xem đại dương.
**Verify:** pytest FULL **494/494** (+3: deepsea sinh đúng luật · fail-open niche không khóa + chuẩn hóa hoa/thường · chèn đúng chỗ + KHÔNG lật bán-thuốc). Rà chồng chéo đầy đủ: `MO_TA_VAN_HANH_WORLD_LOCK.md` §4.
**Vùng ảnh hưởng đã rà (P5):** world-lock BỔ NHAU bán-thuốc (thêm khối, không thay); GHI ĐÈ CÓ CHỦ ĐÍCH `_SOURCING_RULES` cho niche khóa (entity chỉ cho thực thể biển); KHÔNG thêm veto ở phễu (giữ filter-overload-guard 2-veto, user chốt chỉ tầng đạo diễn); ranker/C5-gate không đụng — sửa thượng nguồn thì concept sạch tự chảy đúng.

**Retrofit DS3-084 (rewrite tay + re-source phễu thật, giữ dur beat):** 18 beat bệnh + central_subject ch2 khử độc "researchers who study them". B1 rewrite concept/route (entity→local b214/216/217; giữ graphic b215 đổi nền dưới nước). B2 re-source qua phễu c5 thật → 7 beat needs_human (kho không có "shark embryo/womb" literal). B3 nới query về NỀN NICHE (deep sea/fish school/shark swimming — pool free thật) → 3 beat được. **B4: 4 beat cuối NÃO veto hết footage generic-in-world** (thiếu luật world-lock ở phễu — ĐÚNG dự báo §6) → chạy heuristic Phase 0 (brain=None) lấy top local free = filler hợp lệ. Kết: **0 needs_human, 18/18 in-world** (underwater/shark/jellyfish/denticle-diagram/dark-water; 0 người/lab/siêu âm lọt). Breath re-pick dur KHÔNG đổi (timeline/music-sync an toàn) → assemble → **draft `..._V3`** (rename từ base để version trực quan; content_id/draft_id KHÁC _V2, fix `draft_fold_path`, project.json trỏ _V3).
**Bài học retrofit:** re-source vài beat vào video đã dày footage → P7 "used" vắt cạn pool (10 cands/beat, 7 đã dùng); query filler phải RỘNG + khác góc mỗi beat; NÃO veto generic-in-world → dùng heuristic path cho beat filler thuần nền. **CỔNG MẮT _V3 CÒN CHỜ** (soi 18 beat + b213-217 hình phôi thay siêu âm).

### 2026-07-14 — OVERLAY-084: DS3-084 mất trắng overlay text — điều tra + retrofit _V4 + vá gốc

**Cái gì đổi:** ① `projects/ds3-084.../assemble_director_draft.py` (normalizer fan-out, giờ là TEMPLATE cho bài sau): `norm_overlay()` coerce overlay CHUỖI TRẦN → dict (kind: có chữ số→stat, còn lại→keyword; anchor fallback = đầu beat) + biến đếm `OV_COERCED/OV_DROPPED` in cuối run — CẤM loại êm; vá luôn bug anh-em: `split_long_beats` dict(bt) nông nhân đôi overlays sang CẢ 2 nửa → lọc theo nửa chứa anchor. ② `.claude/skills/dung-video/SKILL.md`: mục mới "Fan-out chương dài — block SCHEMA BẮT BUỘC" (ví dụ overlays dict nguyên văn + trỏ normalizer template). ③ `projects/ds3-084.../retrofit_overlays.py`: gom 25 chuỗi từ ch1..6_draft.json → neo anchor = từ TRÙNG token trong range beat gốc (map số→chữ: 50→fifty; fallback đầu beat) → tìm beat project.json chứa anchor → `resolve_overlay()` điền phần hình → **23 overlay ghi vào project.json** (2 bỏ do trùng text beat liền kề: '50 → 2', '1 m'; backup `project.json.bak_truoc_overlay_retrofit`).

**Vì sao:** user báo "toàn bộ bài DS3-084 không xuất hiện overlay text". Điều tra: 6 agent fan-out CÓ sinh 25 overlay nhưng dạng chuỗi trần (drift schema — prompt dispatch thiếu ví dụ dict); normalizer `if not isinstance(o, dict): return None` nuốt êm 100% → project.json 0 overlay → assembler không tạo track text. DS5-083 cùng đường fan-out nhưng agent trả dict chuẩn nên không dính — bài học NHAT_KY_TOC_DO "block SCHEMA BẮT BUỘC" đúng nhưng CHƯA đủ chi tiết tới field lồng nhau.

**Verify:** rerun normalizer đã vá = **25 coerce / 0 DROPPED** (regression tái hiện: trước vá 25 rơi êm) · retrofit in đủ 23 mapping (soi mắt: anchor trúng từ đắt — 'WEAPON'@1157, 'denticles'@1298, '2.2'@1531...) · assemble **`E:\CapCut Drafts\DS3_084_WOMB_CANNIBALISM_20260713_224919_V4`**: "overlay: 22 text + 22 SFX đã đặt lên draft" (1 rơi ĐÚNG luật: beat 14 có chart → 1-lớp-chữ) · `draft_content.json` _V4: track text 22 segment / materials.texts 22 · report.html chạy lại · pytest FULL **494/494**.

**Vùng ảnh hưởng đã rà (P5):** project.json CHỈ thêm `overlays` vào 23 beat — start/end/timeline/asset/music không đụng → cut/source/music-sync an toàn, KHÔNG re-source; `director_draft.json` bị normalizer rerun ghi lại (file trung gian, project.json vẫn là nguồn sự thật — 223 beat trước-ingest vs 230 sau-ingest là bình thường); consumer overlays duy nhất = `_add_overlays` assembler (anchor toàn cục + hệ tọa độ kép, đã kiểm); bẫy version draft: base không tồn tại (đã rename _V3) → assemble sẽ ghi TÊN BASE trẻ hơn V3 — né bằng pre-create folder base rỗng cho `_next_version` ra _V4 rồi xóa folder rỗng. **CỔNG MẮT _V4 CHỜ USER** (chỉ cần soi 22 overlay — hình world-lock _V3 user đã duyệt, timeline không đổi).

### 2026-07-14 — FOOTAGE-084: footage hết ở 18:36 + 40 needs_human — 2 bug nền + gói 3 fix "tool tự điền hết"

**Cái gì đổi:** ① `library/db.py::search_assets` + `signature_assets`: thêm `exclude_paths` (P7 đã-dùng) + `own_only` (gạt viral) + `no_people` — cả 3 lọc TRONG SQL/cursor **TRƯỚC** nhát cắt limit; `sourcer/local.py` 3 hàm `find_local/ref/signature_candidates` nhận `used_keys` (+`own_only`/`no_people` cho local) truyền xuống; `runner.py::_gather_candidates` + nền-lót graphic truyền `used_in_video`. ② `packager/assembler.py`: loop đặt video gom `holes` (needs_human + asset hỏng + breath fail) → `_fill_holes_with_slug` lấp ảnh `_editor_slug.jpg` ("EDITOR: ĐẮP FOOTAGE Ở ĐÂY", matplotlib DejaVu) đúng khoảng — KHÔNG vào placed_shots/cuts_log/kb_log; fail thì warning to, không giết draft. ③ `runner.py::_floor_pick` + `_floor_ladder`: sau khi mọi route trả needs_human → thang 3 nấc heuristic không-NÃO từ kho own (①query gốc qua đường find_local_candidates chuẩn geo-gate/C6/used-exclusion ②rút query về ĐUÔI danh từ ③top-10 subject_words vocab kho); niche trong `WORLD_LOCK` gạt has_people trong SQL, niche thường chỉ ưu tiên; sort: soft_penalty P7 → duration-fit → người; pick `source="floor"` + note nấc + lý do gốc + warning/beat + dòng tổng kết.

**Vì sao:** user báo voice 21:30 nhưng footage hết 18:36 (dính từ _V2) + chốt "40 beat 1 bài là lớn, tool phải tự điền hết". Điều tra: (A) tool ghi draft ĐÚNG (draft_info.json end 21:48, 27 lỗ needs_human 187s đúng thiết kế) nhưng **CapCut mở draft là DỒN sạch lỗ trên main track (track nam châm) rồi ghi đè draft_content.json** → mọi footage sau b84@8:49 trượt dần khỏi voice, cuối trượt -187s; bug nền có từ đầu, chưa lộ vì bài trước 0-2 lỗ sát cuối. (B) 26/39 needs_human oan vì `search_assets` LIMIT-trước-lọc-used (b204 query 'shark' kho match 1000 vẫn trắng tay); khi code sàn lộ tiếp 2 anh em: top kho theo indexed_at DESC = 100% viral (100/100 dòng 'shark' đầu) và lọc người sau cap — cùng họ "lọc-sau-cắt". Opus 4.8 không phải nguyên nhân — chỉ là chất xúc tác (nhiều beat 1 chủ thể → query hội tụ 'shark' → 5 suất/query cạn sớm).

**Verify:** pytest FULL **500/500** (+6 regression: exclude-used local + signature tái hiện trắng-tay-oan · slug needs_human giữa video: track liền khít 0→11s, slug đúng ô 6.7-9.0, ảnh không Ken Burns · test asset-hỏng cũ đổi kỳ vọng theo hành vi mới slug · sàn đắp nấc-2 + world-lock gạt người + kho rỗng giữ needs_human) · retrofit DS3-084: **39/39 beat floor-pick, 0 needs_human** (35 trúng nấc 1 ngay sau fix ① — chứng minh bug LIMIT là gốc; b181/187 nấc 3; backup `project.json.bak_truoc_floor_retrofit`) · assemble **draft `E:\CapCut Drafts\DS3_084_WOMB_CANNIBALISM_20260713_224919_V5`** (pre-create base rỗng → _next_version ra V5 → xóa): video_l1 **306 segment phủ kín 0→21:48.97, 0 gap, 0 slug cần dùng**, overlay 22 text + 22 SFX giữ nguyên, report.html chạy lại.

**Vùng ảnh hưởng đã rà (P5):** mọi param mới đều optional — caller cũ (`cli.py search`, breath, tests cũ) giữ nguyên hành vi; sàn chạy SAU khi phễu/route đầu hàng nên không lật pick nào của NÃO/C5; viral né hẳn (own_only — sàn không đụng pháp lý c8/ledger); `wins` C4 không đếm floor (metric local-first trung thực); slug không nhiễu pacing DNA/S3-HOOK/Ken Burns; `_source_graphic` route giữ status "graphic" (không qua sàn — chủ đích); quét anh em cùng pattern LIMIT-trước-lọc: search_assets ✓ signature_assets ✓ ref (lọc trong vòng gom) ✓ nền-lót graphic ✓ — `videos_for_niche` (pool shot thở) có trần 500 riêng NHƯNG lọc used tại chỗ pick, không cùng dạng, để nguyên. **CỔNG MẮT _V5 CHỜ USER**: soi 39 beat nguồn 'floor' trên report (filler in-world, nhiều clip megalodon/great-white — khác loài chủ thể là chấp nhận được với filler, chê thì swap) + 22 overlay (chưa qua cổng từ _V4; _V4 bỏ, dùng _V5).

### 2026-07-14 — BAN-GIAO: giải pháp bàn giao máy editor (hướng dẫn cài đặt + kênh tri thức chung + luật §7)

**Cái gì đổi:** ① **`HUONG_DAN_CAI_DAT_MAY_EDITOR.md`** — file hướng dẫn trọn gói 6 phần: A (máy gốc chuẩn bị: bảng 5 thứ phải mang + lệnh robocopy + 2 quyết định user về key API/tài khoản Claude) · B (cài nền tay trên máy editor: Python 3.11+/Node/git/ffmpeg/VSCode/Claude Code extension **VÀ CLI npm global** — bắt buộc vì `cc_client.py` gọi `claude -p` qua PATH/CapCut + donor trống) · C (12 bước Claude Code TỰ cài từ prompt bootstrap: uv sync → nạp `BAN_GIAO\memory_goc` vào memory máy mới → rewrite path `cache.db` nếu kho không ở `F:\` → set-library-root/set-draft-root → register-machine → tạo flag → FULL pytest → smoke `voice test travel`) · D (kênh tri thức `BAN_GIAO\`) · E (editor dùng hằng ngày) · F (8 sự cố biết trước). ② Scaffold `BAN_GIAO\`: `NHAT_KY_MAY_EDITOR.md` (khuôn entry) + `memory_moi\` (mirror memory sinh trên máy editor). ③ **CLAUDE.md §7** — luật máy editor, gate bằng file `BAN_GIAO\MAY_EDITOR.flag` (bootstrap C9 tạo; máy gốc không có flag → luật trơ): mỗi fix = ghi chép §6 + mirror memory_moi + entry nhật ký editor + `git bundle`. ④ `.gitignore` +3 dòng: flag (commit là luật bật nhầm máy gốc khi merge bundle) + `*.bundle` (nhị phân) + `memory_goc/` (xuất tạm ngày bàn giao).

**Vì sao:** user chốt 2026-07-14: hệ thống chạy tốt trên máy này, bàn giao cho editor vận hành ở máy họ; KHÔNG đóng gói phần mềm (đã thử — nhiều bug); editor cài Claude Code + gõ prompt như máy gốc; fix lỗi bên đó phải vào bản đồ tri thức chung (file trên máy editor → copy về / Google Drive) để user kiểm tra vài tháng đầu.

**Điểm kỹ thuật đáng nhớ khi thiết kế:** (a) `~\AutoEdit\cache.db` lưu path TUYỆT ĐỐI `F:\...` của ~9.000 asset đã tag (đắt tiền GLM) → kho trên máy editor phải giữ đúng `F:\AutoEdit`, lệch ổ thì rewrite theo tiền lệ KHO-F (library_assets.path + source_video + asset_usage.asset_key + ambient yaml); (b) copy kho phải GIỮ mtime (robocopy) — mtime lệch là indexer coi là file đổi → tag lại tốn tiền; (c) code KHÔNG hardcode path máy (chỉ machine.json + ~/AutoEdit) — grep xác minh; (d) memory Claude Code nằm ngoài project (`~\.claude\projects\<slug>\memory`) và slug phụ thuộc path project từng máy → phải xuất vào `BAN_GIAO\memory_goc` rồi bootstrap nạp vào memory dir của máy mới; (e) chuyển code 2 chiều không GitHub (luật user) → `git bundle` 1 file, máy gốc `git fetch <bundle>` + review diff.

**Verify:** docs-only — pytest không đổi (508/508 mốc TEMPO-MAP vẫn là mốc test hiện hành). Cổng thật của milestone này = prompt bootstrap chạy trót lọt trên máy editor ngày bàn giao (C1→C12). Vùng ảnh hưởng đã rà (P5): CLAUDE.md §7 gate bằng flag nên máy gốc không đổi hành vi; .gitignore 3 dòng mới không che file đang track; không đụng code/pipeline.

### 2026-07-15 — BAN-GIAO-2: kho F: dùng chung qua mạng + bộ cài 1 folder `F:\BO_CAI_MAY_EDITOR`

**Cái gì đổi:** ① `HUONG_DAN_CAI_DAT_MAY_EDITOR.md` VIẾT LẠI v2 theo user chốt "kết nối ổ F máy tôi cho máy editor": share toàn ổ F: (account editor riêng, map đúng chữ **F:**) thay copy kho 76GB → path trong cache.db khớp nguyên trạng mọi máy, hết bẫy rewrite + bẫy mtime-tag-lại (footage không copy = cùng 1 file); máy gốc Sleep=Never + mạng dây gigabit (source = 85% thời gian pipeline, Wi-Fi chậm 3–4×); PHẦN B rút còn 6 việc cài tay (python/git/ffmpeg → Claude Code tự winget ở C1); C5 đổi từ "rewrite path" thành "KIỂM chữ ổ, cấm rewrite"; C7 draft PHẢI ổ LOCAL máy editor; C11 thêm kiểm `library-search` qua mạng; PHẦN D sync `BAN_GIAO` qua chính ổ F: (`F:\BAN_GIAO_TU_EDITOR\<editor>`, robocopy /XF flag) — Drive/USB xuống dự phòng; PHẦN F +4 sự cố mạng + mục editor Ở XA (không LAN → quay về copy-kho v1 từ git). ② **QUY ƯỚC TẠM** (A4.3): nạp kho/nhạc CHỈ trên máy gốc — grep xác nhận `cache.db`/`music`/`sfx` ghim cứng `~\AutoEdit` local (db.py:15, music/library.py:23, sfx/library.py:18, KHÔNG có override) → sổ tag local từng máy là snapshot, editor nạp là sổ lệch nhau. ③ **PHẦN G — nâng cấp bước 2 CHỜ USER DUYỆT:** dời cache.db+music+sfx lên `F:\AutoEdit` dùng chung (root dữ liệu từ machine.json + backup tự động cache.db trước mỗi mẻ nạp); lý do chưa code: SQLite trên SMB = vùng nhà-sản-xuất-cảnh-báo khi GHI đồng thời — luật 1-job-mỗi-lúc + backup làm rủi ro chấp nhận được nhưng cần user duyệt + cổng test riêng. ④ **BỘ CÀI dựng thật** tại `F:\BO_CAI_MAY_EDITOR\` (F: trống 810GB — editor kéo qua mạng sau khi map, khỏi USB): `DOC_DAU_TIEN.md` (thứ tự làm + prompt bootstrap nguyên văn) + `tool edit padoma\` (project trừ .venv/projects/2-folder-lề, KÈM `.env` + `.git` + `BAN_GIAO\memory_goc` xuất tươi) + `AutoEdit_C\` (cache.db + music + sfx 1.3GB).

**Vì sao:** user 2026-07-15: "để dữ liệu niche được lưu tập trung... editor cùng nhau lưu các footage mới vào cùng 1 nơi... đỡ phải copy nhiều" + "copy cho tôi một bộ cài đặt vào 1 folder... cài vscode và claude code, sau đó yêu cầu claude code cài hết phần còn lại".

**Verify:** docs + copy, không code — pytest không đổi. Bộ cài verify: `.env` có mặt trong bản copy + memory_goc đủ file + cache.db đúng cỡ (xem log robocopy ngay dưới milestone này). Vùng ảnh hưởng đã rà (P5): không đụng code; hướng dẫn v1 vẫn lấy lại được từ git (commit `4eefe1d`) cho ca editor-ở-xa; CLAUDE.md §7 + .gitignore giữ nguyên từ BAN-GIAO.

### 2026-07-15 — G1-SO-CHUNG: cache.db + nhạc + SFX dùng chung trên F:\AutoEdit (set-data-root) + chuyển dữ liệu máy gốc

**Cái gì đổi:** ① `packager/machine.py`: field `MachineProfile.data_root` + `set_data_root()` + `resolve_data_root(override, profile_path)` — 4 nấc ưu tiên đúng khuôn `resolve_library_root` (override > env `AUTOEDIT_DATA_ROOT` > machine.json > `~\AutoEdit`); máy chưa set → mặc định cũ, KHÔNG đổi hành vi. ② `library/db.py`: `DEFAULT_DB_PATH = resolve_data_root() / "cache.db"` (lúc import) + `sqlite3.connect(db_path, timeout=30)` (sổ trên ổ mạng — máy khác đang ghi thì chờ khóa 30s thay vì nổ "database is locked" sau 5s) + `backup_cache_db(db_path, keep=10)` chụp vào `<data_root>/backup/cache-<ts>.db` + prune. ③ `music/library.py::MUSIC_ROOT` = `resolve_data_root()/"music"`, `sfx/library.py::SFX_ROOT` = `.../"sfx"` — hằng lúc import, mọi default-arg consumer đi theo, KHÔNG đổi chữ ký hàm nào. ④ `cli.py`: lệnh `set-data-root` (warning nếu chưa thấy cache.db/music/sfx tại đích) + 4 lệnh music-init/import/analyze/list bỏ default ghim cứng `Path("~/AutoEdit/music")` (bẫy: default typer đánh giá lúc import, MUSIC_ROOT động cũng vô dụng nếu không vá đây) + backup gọi trước `conn = db.connect()` ở `library-index`/`library-ingest`. ⑤ Chuyển dữ liệu: robocopy music/sfx + copy cache.db → `F:\AutoEdit` (cạnh library/ + ambient/ có sẵn) → `set-data-root F:\AutoEdit` → C: cũ đổi tên `AutoEdit.pre-G1-backup` (backup nguội — tránh mơ hồ 2 bản sống). ⑥ Hướng dẫn v3 + DOC bộ cài: bỏ AutoEdit_C, GLM key riêng (trống trong bộ cài), C6 set-data-root, F 3 sự cố sổ chung mới, G ghi trạng thái G1 xong + G2 đã quyết chờ kiến trúc.

**Vì sao:** user duyệt PHẦN G ("tôi duyệt G, nhưng vẫn cần G2... có sẵn vps ubuntu... tính toán cẩn thận vì bước di chuyển này rất dễ bị lỗi"): editor tự nạp kho/nhạc từ máy họ, mọi máy thấy ngay, sổ đã-dùng + viral ledger thống nhất (chống 2 editor lặp footage nhau). GLM key riêng mỗi editor (user chốt cùng phiên) gỡ lý do cũ của luật 1-job; sổ chung SMB là lý do mới giữ luật lúc đầu.

**Verify:** pytest FULL **531/531 × 2 lần** — TRƯỚC flip (data_root chưa set = chứng minh hành vi cũ nguyên vẹn, 529 nền + 2 test mới) và SAU flip (cấu hình F: sạch). Đọc thật sau flip: DB `F:\AutoEdit\cache.db` 34.196 asset + 5.167 usage · MUSIC_ROOT `F:\AutoEdit\music` 241 bài · SFX_ROOT `F:\AutoEdit\sfx` 136 file. Copy 0 FAILED (249+187 file). Kiểm không có job đang chạy trước khi flip (Get-Process python/uv trống — RD-89 đã xong phần máy).

**Vùng ảnh hưởng đã rà (P5):** grep toàn package `~/AutoEdit`/`AutoEdit` — mọi consumer đi qua 3 hằng (DEFAULT_DB_PATH/MUSIC_ROOT/SFX_ROOT) hoặc resolve_library_root (đã F: từ KHO-F) hoặc dẫn xuất library_root (ambient root, editor_dna, music_editor staging — tự theo F:); 4 default typer ghim cứng là chỗ DUY NHẤT lách qua hằng — đã vá cùng (cùng-pattern: grep `Path("~/AutoEdit` = 0 kết quả còn lại trong package). Import cycle: machine.py chỉ import stdlib+pydantic, mọi `__init__.py` rỗng → db/music/sfx import module-level an toàn. Test cũ: mọi hàm nhận conn/lib_root tường minh → không phụ thuộc default; 531 xanh xác nhận. Còn ngỏ: hằng đọc LÚC IMPORT — process sống lâu đổi set-data-root không tự thấy (ghi rõ trong help lệnh + docstring); vỏ rỗng `F:\AutoEdit\library\cache.db` 0MB sót KHO-F để nguyên (không consumer, xóa lúc nào cũng được); G2 di trú db-server = milestone riêng CÓ CỔNG TEST, chưa đụng.

### 2026-07-17 — GHI-CONG: kênh nguồn footage vào sổ + backfill kho cũ + `assemble --credit` (VD4)

**Cái gì đổi:** ① `library/db.py`: cột `source_channel TEXT NOT NULL DEFAULT ''` (họ `source_*`; CỐ Ý không đặt `channel` — đã có 2 chỗ `channel` nghĩa KHÁC = kênh sản xuất: `Inputs.channel` + `asset_usage.channel`) vào `_SCHEMA` + `AssetRecord` + `_migrate` + `upsert_asset` với **luật preserve `excluded.source_channel=''` → GIỮ giá trị cũ** (khác khuôn CASE `source_video` — nếu theo khuôn cũ thì mỗi resume/retag không `--channel` là backfill mất trắng); 2 hàm mới `source_video_folders` (gom folder cha) + `set_source_channel` (so prefix ở PYTHON trên DISTINCT source_video rồi UPDATE giá trị chính xác — cố ý NÉ LIKE). ② `library/ytpeaks.py`: `YTVideoInfo.channel` + fetch đọc `data["channel"]/["uploader"]` (yt-dlp có sẵn, trước giờ bỏ qua). ③ `library/ingest.py`: `ingest_draft(channel="")` → extra `source_channel = channel or info.channel` (explicit thắng, cùng luật `--topic`; viral nhiều kênh trong 1 mẻ vẫn đúng từng nguồn). ④ `cli.py`: `library-ingest --channel` + dry-run in kênh + 2 lệnh `channel-audit`/`channel-set [--niche] [--dry-run]`. ⑤ **Fix bug anh em phát hiện khi rà (P5): `sourcer/local.py::find_ref_candidates` LIKE prefix — trên PostgreSQL `\` trong pattern LIKE là ký tự ESCAPE → prefix Windows `f:\space\...` match hụt = REF chạy RỖNG IM LẶNG trên máy đã flip PG** (SQLite không escape mặc định + test cũ dùng `F:/` nên không lộ) → thay `substr(lower(source_video),1,?)=?`; `_row_to_candidate` mang `source_channel` lên ứng viên (chống vết PB7 cột-rơi). ⑥ `project.py`: field `source_channel` vào `ShotPick`/`ExtraShot`/`BreathShot`; `runner.py` 4 điểm pick (funnel lead+extra · heuristic · sàn niche) + `breath.py` copy từ ứng viên — assemble KHÔNG mở sổ (NT1). ⑦ `overlay/text.py`: `x_override` (expose `transform_x` — card PiP đã dùng). ⑧ `packager/assembler.py`: `credit_log` gom (start, end, asset_rel) từng miếng L1 tại `_place_video_l1` + `_add_credit_overlays` (chỉ miếng có kênh; góc = `crc32(asset:mốc) % 4` deterministic — dựng lại ra đúng góc cũ, cùng khuôn seed Ken Burns/shot thở; track text `credit` riêng + `_safe_add_segment`; slug/chart/card không vào credit_log) + `run_assemble(credit=False)` ← CLI `assemble --credit`.

**Vì sao:** user chốt 2026-07-17 làm VD4 trước (từ audit 4 hướng editor custom prompt — memory [[audit-editor-custom-prompt-4-huong]]): mỗi footage cắt nguồn phải ghi vào sổ là của KÊNH nào, ghi được cả kho cũ, editor muốn ghi công thì bật tính năng → tên kênh hiện 1 trong 4 góc (random). Cột thêm càng sớm càng ít asset "mồ côi kênh".

**Verify:** pytest FULL **560/560, 0 skip** (M1 556 → M2 560; +11 test mới: preserve/backfill/audit + ingest --channel + viral auto-kênh + ytpeaks channel + **regression REF backslash chạy THẬT trên PG** qua `AUTOEDIT_TEST_PG_URL` → db `autoedit_test` + x_override + credit 3 ca). Chạy thật `channel-audit` trên sổ PG production (read-only): **164 folder nguồn (deepsea/life-in/space), 164 chưa có kênh** → `BAO_CAO_CHANNEL_AUDIT_2026-07-17.txt`. Commit `e068b74` (M1) + `e5c8eb2` (M2). **CỔNG MẮT CHƯA QUA:** vị trí 4 góc (±0.72, ±0.80) + size 8 là số v1 — cần 1 draft thật `--credit` cho user/editor nhìn CapCut rồi chỉnh.

**Vùng ảnh hưởng đã rà (P5):** đầy đủ trong `MO_TA_VAN_HANH_GHI_CONG_KENH.md §3` — tóm tắt: cột mới KHÔNG vào điểm/lọc phễu (ViralLedger gate theo source_video y cũ); `needs_index` không xét cột mới (backfill không kích re-tag oan cả kho); `move_asset` không đụng; track text tên riêng `credit` không đè `text`/`kinetic{k}`; các chỗ LIKE khác đã quét (search_assets term-là-TỪ an toàn; ViralLedger + runner.py:642 dùng `str.startswith` Python); cột TEXT không dính bẫy REAL→DOUBLE PRECISION của PG; máy editor ghi song song: migrate idempotent + UPDATE theo giá trị chính xác.

**Ghi chú / còn ngỏ:** kho cũ 164 folder chờ user/editor điền `channel-set` (folder own có thể bỏ trống — không cần tự ghi công mình); mẻ viral TƯƠNG LAI có YouTube ID thì kênh tự điền, khỏi làm gì; report.html chưa hiện cột kênh theo beat (thêm nếu editor cần soát); backfill TỰ ĐỘNG kênh cho folder VIDEO MAU cũ bằng yt-dlp (urls.txt/tên file có ID) = khả thi nhưng CHƯA làm — chờ user quyết; beat `graphic` nền lót không credit (v1). Memory [[ghi-cong-kenh-nguon]].

### 2026-07-17 — BOOST: cảnh dạng X khán giả thích (VD3) — M1 tầng phễu

**Cái gì đổi:** ① `project.py`: `Inputs.boosts` (dính theo project như ref_sources) + `ShotPick/ExtraShot.boost_hit` (tầng ĐO đọc từ project.json). ② `sourcer/local.py`: `find_boost_candidates` (CHỈ KHO, AND-match term qua search_assets, `BOOST_INJECT_CAP=6`, đủ 3 cửa file-tồn-tại/geo-gate-PA2/loại-đã-dùng-TRƯỚC-limit y find_local/find_ref) + `_row_to_candidate` mang thêm cột `tags` (nhãn match cần — chống vết PB7 cột-rơi). ③ `sourcer/runner.py`: `_parse_boosts` ("X@scope", scope lạ = all + warning) · `_audience_bias` (đọc niche_profile.yaml — **field Stage-4 có sẵn nhưng CHƯA AI TIÊU THỤ, nay nối dây**, lọc TODO, fail-open) · merge 2 nguồn TRONG run_source (chokepoint duy nhất — chống bug B2 `run` gọi thẳng) · `_boost_terms_for` scope tính PER-BEAT tại CẢ 2 call site batch/per-beat (không qua ctx — né staleness lookahead TOC-2) · chèn sau ref trước Pexels bọc `ledger.gate` · nhãn `is_boost` tại chokepoint SAU dedup (khuôn is_ref) CHỈ source local · sàn niche `_floor_pick` sort X lên đầu nấc vét + 3 điểm pick stamp boost_hit · warning tầng ĐO đếm lead/extra match. ④ `ranker/funnel.py`: `BOOST_BONUS = 1.0` 🔸 trong `_diem_may`, CỘNG DỒN với REF_BONUS; cố ý đứng NGOÀI `MACHINE_MAX_SPREAD` như REF (bonus Ý ĐỒ EDITOR ≠ điểm máy trung tính — bất biến test_ranker giữ nguyên). ⑤ `cli.py`: `source --boost` (khuôn --ref chống OptionInfo B2) + cảnh báo khai-muộn-sau-direct. ⑥ `MO_TA_VAN_HANH_BOOST.md` (kèm mục Rà chồng chéo P5 đầy đủ — rà TRƯỚC khi code theo yêu cầu user).

**Vì sao:** user chốt VD3 2026-07-17 sau 2 vòng bàn: khán giả niche thích cảnh dạng X (life-in: phụ nữ đẹp) — editor thật xen kẽ X cả bài đúng bối cảnh quốc gia, ĐẶC BIỆT đổ vào đoạn khó kiếm footage, và né Pexels. 3 chốt: khai 2 tầng (per-video + audience_bias niche) · cùng bonus 1,0 · term tiếng Anh theo từ vựng tag kho. Scope mặc định `all` KHÔNG tràn X vì bonus 1,0 thua 1 điểm nghĩa — X tự dồn vào beat generic/trống (đúng hành vi editor thật); phanh có sẵn: P7 + trần viral + nghĩa/veto/world-lock trên hết.

**Verify:** 9 pytest mới (khối BOOST test_sourcer.py): parse scope/dedupe/scope-lạ-warning · scope per-beat · geo-gate chặn X sai nước (vết PA2) + used-trước-limit (vết DS3-084) + tags lên ứng viên · nhãn chokepoint SỐNG SAU DEDUP (ứng viên vào bằng đường local vẫn ăn nhãn — vết PB7/REF) + Pexels match chữ KHÔNG ăn + _diem_may cộng đúng + cộng dồn REF · chèn khi query trượt (kịch bản "đoạn khó kiếm footage") + đối chứng không-khai-không-chèn · ledger.gate chặn viral vượt trần ngay đường chèn · heuristic pick mang boost_hit · sàn ưu tiên X thắng cả ưu-tiên-không-người + đối chứng hành vi cũ · audience_bias đọc YAML/lọc TODO/fail-open. FULL suite **570/570** (parity PG thật qua AUTOEDIT_TEST_PG_URL).

**Vùng ảnh hưởng đã rà (P5, TRƯỚC khi code — chi tiết MO_TA_VAN_HANH_BOOST.md §3):** veto nghĩa/world-lock ĐƯỢC PHÉP lật boost (đúng thiết kế); ledger không thủng; geo-gate áp cho chèn; batch PA-1 scope per-beat; signature_first không ngược chiều; bất biến ranker giữ; TOC-3b warm-up trượt vô hại; shot thở/ambient/SFX/nhạc/P7 không đụng; đường heuristic chèn-có-bonus-không (y REF).

**Ghi chú / còn ngỏ:** 🔄 M2 tầng NÃO chờ user duyệt M1; timing: khai --boost SAU direct chỉ ăn tầng phễu (CLI tự nhắc chạy lại direct), audience_bias thì không dính timing (niche biết từ đầu). Video số đo thật (life-in --boost "beautiful woman") chờ chạy. Backlog TRỪ ĐIỂM TOÀN CỤC Pexels — user chốt ghi nhớ, làm khi có số ĐO (memory `pexels-tru-diem-toan-cuc-backlog`). report.html chưa hiện cột X theo beat. Memory [[audience-bias-boost]].

**M2 tầng NÃO (cùng ngày, user xác nhận):** `director/live.py::boost_block(project, niche, library_root=None)` — import lười `_parse_boosts`/`_audience_bias` từ sourcer.runner (1 nguồn luật cho cả 2 tầng, không chép công thức); khối in danh sách X kèm scope tiếng Việt (cả bài/hook/chương N) + 4 luật đạo diễn; chèn vào `build_direct_context` (sau DNA, trước TEMPO MAP) + `director/runner.py` join vào library_context pass-2 (khuôn D2 — đường cũ tự ăn); `cli.py::direct-context --boost` persist inputs (khuôn chống OptionInfo B2) + echo "khối SỞ THÍCH trong context"; SKILL /dung-video: PHA 1 bước 3 dạy khai --boost NGAY tại direct-context (+ audience_bias cho sở thích bền của niche), PHA 2 nhắc đọc dòng BOOST tầng ĐO. KHÔNG đụng prompts.py (luật [[duong-sau-mu-luat-prompts-py]]). Verify: +2 test test_director_live (khối fail-open per-video/per-niche/scope + đường cũ cùng hàm); FULL **572/572** parity PG thật.

### 2026-07-17 — NHAC-SFX-LI: nạp lại nhạc + SFX life-in (bàn giao 5 editor) + pool nhạc theo niche

**Cái gì đổi:** ① `music/library.py::music_root_for(niche)` — `music\<niche>\tracks\` tồn tại → niche CHỈ dùng pool riêng (KHÔNG rơi về pool chung, nhạc không lẫn 2 chiều); chưa có → pool chung. ② `cli.py`: lệnh `music` thêm `--niche` (stage chạy TRƯỚC source nên project.niche thường chưa có — phải truyền tay; resolve --lib > --niche/project.niche > pool chung, echo pool đang dùng); `assemble` dời resolve music_lib xuống SAU `Project.load` → tự theo `project.niche`; `make` truyền `niche=` vào music_cmd + **sửa kèm bug anh em OptionInfo phát hiện khi rà P5: make→assemble thiếu `credit` → nhận OptionInfo truthy → bật ghi công VD4 ngoài ý muốn từ commit VD4** (sửa `credit=False` tường minh). ③ Kho nhạc life-in `F:\AutoEdit\music\life-in\`: 117 file DAT+Thịnh copy vào tracks (4 typo mood sửa khi copy: peachful×2/sirious/misterious), import 116 bài 0 lỗi (2 file cùng base gộp), grid **tier A=105/B=10/C=1** — MUSIC SYNC dùng được ngay; tag ngoài bảng bị bỏ đúng luật: carefree/dramatic/exciting/love/powerful/sexy; **72 bài NAM không mood → `staging_cho_mood\` + `DANH_SACH_CHO_MOOD_NAM.txt`** (không nạp mù, không tự đoán). Pool chung 321 bài GIỮ NGUYÊN. ④ Kho SFX life-in: cũ (165 wav + raw 127 + records) → `backup\ambient_life-in_truoc_nap_20260717\`; GIỮ 7 impact/click (hook đang bật, mẻ mới chỉ có whoosh 5); `subject_rules.yaml` VIẾT LẠI (loài trước cảnh, bản Oman vào backup); manifest 299 entry sinh bằng script phân loại theo tên (folder mặc định + override từng file, khử 15 trùng giữa editor, 21 loại có lý do — trong đó phát hiện folder "Wild peanuts" = 3 file LẠC ĐÀ thật, đơn hàng số 1); `ambient-import` **299/299 0 lỗi → 306 wav / 47 kind**. ⑤ Docs: `MO_TA_VAN_HANH_NHAC_THEO_NICHE.md` mới (kèm Rà chồng chéo P5) + HUONG_DAN_EDITOR_GOM_SFX_NHAC PHẦN 4 (pool đúng niche + hết staging loài) + HUONG_DAN_NAP_NICHE_MOI (input mục 5 nhạc riêng + bước cấu hình).

**Vì sao:** user 2026-07-17: editor đã gom nhạc/SFX life-in về `F:\THU VIEN NHAC + SFX\LIFE IN` (5 editor, folder lộn xộn mỗi người một kiểu) — yêu cầu xóa toàn bộ nhạc+SFX life-in cũ, index kho mới, và LUẬT ĐỨNG: life-in chỉ dùng nhạc life-in (SFX dùng chung được). User chốt 3 câu qua AskUser: giữ pool chung (không nhận diện được bài life-in trong 321 bài — xóa là deepsea/space mất nhạc) · TÁCH KIND THEO LOÀI (đóng điều tra treo RD-89 lạc-đà-tiếng-chim) · nhạc NAM không mood để riêng chờ đặt tên (đúng luật không-tự-đoán).

**Verify:** pytest FULL **576/576, 0 skip** (+4 `test_music_root_niche.py`: pool riêng dùng riêng / niche khác về chung / không niche về chung / folder thiếu tracks không tính — parity PG thật qua AUTOEDIT_TEST_PG_URL). Import thật: nhạc 116/117 0 lỗi + `music-analyze` A=105; ambient 299/299 0 lỗi, `library_status` khớp manifest từng kind. **CỔNG TAI CHƯA QUA:** cần dựng 1 video life-in mới nghe nhạc pool riêng + SFX loài.

**Vùng ảnh hưởng đã rà (P5, chi tiết MO_TA §4):** 2 đường tự-chọn nhạc (stage music + assemble fallback) cùng qua `music_root_for` — không ngược chiều, `--music`/`--music-lib` tay vẫn thắng; ca lệch pool (music không --niche trên project mới → plan pool chung, assemble pool riêng) = warning mềm "thiếu file — bỏ" + chống bằng make/HUONG_DAN, không thêm state (P2); usage per-pool không nhiễm chéo; music-import/analyze/list nhận --lib nên trỏ pool nào cũng được; SFX kind mới khai toàn bộ qua subject_rules.yaml = 0 code (`niche_kinds()` tự nhận), C1/S2/S3/editor-learn không tầng nào lật; draft cũ không hỏng (media đã copy vào draft, portable); scene pool trống (food/people_activity/mountain_desert/sky_cloud...) → ô thở rơi default 2 file (thà im còn hơn sai — ghi đơn đặt hàng).

**Ghi chú / còn ngỏ:** NAM đặt tên 72 bài rồi máy gốc nhập bổ sung (`DANH_SACH_CHO_MOOD_NAM.txt`); đặt hàng nhạc: determined 0 · suspenseful 1 · romantic 2 · nostalgic 4 · inspiring 4; đặt hàng SFX: food 0 (đơn cũ +5 chưa về) · people_activity 0 · interior 0 · flamingo 0 thật · penguin/vulture/crow/ski/snowmobile/escalator 1 file; Flipping 7 + Typewriter 3 nằm nguyên folder nguồn chờ user chốt tầng dùng (backlog chapter-title/overlay); 4 file breathing người → editor đặt tay; niche khác muốn dùng SFX mẻ này (whale/seagull/ocean cho deepsea) → nạp thêm từ cùng folder nguồn. Memory [[music-pool-theo-niche]] + [[life-in-nhac-sfx-dot2]].

### 2026-07-18 — NẠP life-in ĐỢT 3 (29 project EX2xx) + vá bug tcf-gen voice-track TẦNG 3

**Cái gì đổi:** ① NẠP tài nguyên own từ 29 project editor life-in (`E:\PROJECT NHAN BAN\EX\BÀI TỐT` 13 + `BÀI THƯỜNG` 16) vào kho chung. 2 pha: `tcf-gen life-in --draft ...` (sinh `topic + chapter video.txt` từ voice) → `library-ingest life-in <draft> --source-class own` (cắt cảnh mép editor + GLM vision tag). Kết quả **25/29 project nạp trọn ~3099 cảnh, db life-in 16583→20346**; 16 lỗi tag GLM (0,5%) lành tính = HTTP 400 contentFilter + validation AssetTags trên cảnh bộ tộc bán-khỏa-thân (EX274/EX302 Korowai) — GLM tự chặn, cảnh vẫn trong kho chỉ mù tag. ② **FIX bug tcf-gen (commit 1c8ee58):** `library/tcf_gen.py::timeline_blocks` trả `None` khi candidate VƯỢT số track audio (KHÁC `[]` = track có nhưng nhạc/SFX bị faster-whisper VAD lọc sạch → 0 từ); `generate_tcf` đổi `for cand in range(3)` + `if not cand_blocks: break` → `while True` cand++ với None→break (hết track) / []→thử track kế im lặng / ≥MIN_WORDS→nhận. Bỏ trần 3 track cứng (track nhạc 0-từ transcribe rất nhanh nên không tốn thêm).

**Vì sao:** Pha A đợt 1 chết 12/25 project "transcript 0 từ". Đào root cause (mổ track): voice của các project này là AUDIO GỐC trong `.mp4` nguồn (`Bai NNN EX.mp4`, 1518-1815s gần trọn video, chỉ 1-3 seg) → điểm lai `seg×dur` thua nhạc mp3 nhiều-seg → xếp hạng 1-2. Vòng cũ gặp track nhạc hạng 0 (VAD lọc sạch → `timeline_blocks` trả `[]`) → `break` NGAY (tưởng "hết track") → không bao giờ tới track voice. Đây là TẦNG 3 của chuỗi bug voice-track (tầng 1+2 commit 794b2d7 fallback ≤3 track vẫn có tail này vì test cũ REAL79 cho track nhạc 1 từ thay vì 0). User chốt "vá heuristic" qua AskUser.

**Verify:** pytest FULL **574/574 (+2 regression), 11 skip** (test mới: `top-tracks-empty-music` tái hiện đúng EX247 nhạc→[]/voice hạng 2; `all-tracks-empty-stops` chống lặp vô hạn `while True` khi mọi track rỗng→None→raise). Chạy lại thật: tcf-gen 10/11 fix (EX247 → "track hạng 2, 3413 từ" → 12 chapter "Amazon Tribes"); ingest 25/25 exit 0, 0 Traceback.

**Vùng ảnh hưởng đã rà (P5):** `timeline_blocks` chỉ 2 consumer — `generate_tcf` (đã sửa) + 2 test cũ (dùng candidate hợp lệ, trả list, không dính nhánh None mới). `pause-dna`/`editor-learn` dùng `voice_files_of` (= candidates[0], KHÔNG đổi). Đổi return type list→Optional[list] chỉ ảnh hưởng caller đã rà.

**Ghi chú / còn ngỏ (user cần kiểm/re-export trên máy editor):** 4 project không nạp được — EX291/EX299 (BÀI TỐT) + EX215/EX257 (BÀI THƯỜNG) THIẾU `draft_content.json` (EX215 chỉ có `.bak`, materials rỗng); EX281 (BÀI THƯỜNG) ingest OK 14 cảnh nhưng KHÔNG có TCF vì file voice `.aac` HỎNG THẬT (ffmpeg chỉ giải mã 21/1432s, avcodec_send_packet lỗi) → nạp mù chủ đề. Memory [[life-in-nap-dot3-ex2xx]] + [[voice-track-hybrid-score]] (tầng 3).
