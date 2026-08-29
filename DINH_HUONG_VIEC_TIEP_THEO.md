# ĐỊNH HƯỚNG VIỆC TIẾP THEO — bản đồ đầy đủ (2026-07-09)

> Claude rà toàn bộ backlog 18 foundation + mô tả vận hành + nhật ký sau khi V2 đóng trọn
> (c8 + Ken Burns + 3 video space end-to-end đã duyệt). Mỗi việc nhóm B/C lớn đều cần
> mô tả vận hành duyệt trước khi code (P4). ★ = Claude khuyên ưu tiên.

---

## ⭐ TRÌNH TỰ ĐÃ CHỐT (user duyệt 2026-07-09): "D → C có nhịp thở → scale"

> User chốt: nâng cấp full tính năng TRƯỚC, scale video SAU — theo phương án Claude tư vấn:
> **cứ mỗi 1–2 tính năng C phải dựng 1 video thật làm cổng mắt/tai** (video kiểm chính là
> video sản xuất được — 2 mục tiêu 1 công), KHÔNG code chay cả nhóm C một mạch.

| Bước | Việc | Cổng |
|---|---|---|
| **D — ✅ ĐÓNG TRỌN 2026-07-09** | D1 backup kho F: ✅ (D:\AutoEdit_backup — E: CÙNG đĩa vật lý F:, không dùng) · D5 git local ✅ (commit gốc `890c68b`; user từng hoãn vì tưởng D5 = commit GitHub, sau khi rõ là git LOCAL thì mở lại — KHÔNG remote/KHÔNG push; CLAUDE.md P4 đã sửa luật) · D4 key BỎ (hệ không cần ANTHROPIC_API_KEY — NÃO đi subscription, key hết hạn đã XÓA khỏi .env; chỉ cần nếu dùng fallback `--engine api`/`--engine claude`) · D2 ✅ (direct cũ ăn khối vocab C4 + DNA vào pass 2, pytest 297/297) | pytest ✅ |
| **V123 (chèn trước C — user yêu cầu 2026-07-09 từ 3 vấn đề SP012_V2)** | V1 crop 16:9 + V2 entity mở rộng + V3 video_subject/veto thiên thể — code 302/302 + video kiểm `SCRIPT_20260709_071612` — `MO_TA_VAN_HANH_NANG_CAP_V123.md` + NHAT_KY §V123 | ✅ **ĐÓNG TRỌN — cổng mắt ĐẠT cả 3 điểm (user 2026-07-09)** |
| C đợt 1 — **✅ ĐÓNG TRỌN 2026-07-09** | C6 drop-list từ chuyển động (user chốt thay bảng đồng nghĩa; PB8 3 query oan 0→80/604/742) + C3 so màu chỉ-cảnh-báo (MAD, user chốt giữ warning-only "editor thấy lệch tự thay") + C7 lệnh `pause-dna` (regression khớp tuyệt đối, guard không đè bản duyệt) — `MO_TA_VAN_HANH_C_DOT_1.md`, pytest 317/317 | ✅ cổng mắt ĐẠT qua video kiểm GỘP V3 (NHAT_KY §KIEM-V3) |
| C đợt 2 — **✅ ĐÓNG TRỌN 2026-07-09** | C4 tone chảy vào pass 2 (rà lần 2 cắt 2 điểm chảy rủi ro — phễu/nhạc) + D3 trần TỔNG local 10 — `MO_TA_VAN_HANH_C_DOT_2.md`, pytest 321/321. Cùng ngày: 2a/2b vá prompt tag thiên thể + tag lại 102 clip (b60 Pluto hết "moon") | ✅ video kiểm GỘP `SCRIPT_20260709_071612_V3`: 4 pick sai-nghĩa biến mất, cổng mắt+TAI ĐẠT (user 2026-07-09) |
| C đợt 3 + 3b — **✅ ĐÓNG TRỌN 2026-07-10** | C1 ambient ô thở (0dB chốt tai V4) + S1 drone + S2 subject-SFX (-15/-10dB PB13) + whoosh auto BỎ theo PB12 + M5 `editor-learn` (luật đứng, đã học 4 draft) — NHAT_KY §C-ĐỢT-3/3b | ✅ cổng TAI V10 đạt |
| C đợt 4 — **✅ ĐÓNG 2026-07-10 dạng KHÔNG-CODE** | PB14 đo 4 draft: 0 punch-bằng-cắt, 5-7 cú zoom-drama/104' không pattern → user duyệt "editor thêm tay, không code auto"; f2 vá block LỆCH | ✅ verdict đo |
| C đợt 5 — **✅ ĐÓNG TRỌN 2026-07-10 → HẾT NHÓM C** | C5 vision gate top-pick (`MO_TA_VAN_HANH_C5_VISION_GATE.md`): CHỈ soi pick KHO LOCAL (`GATE_SOURCES` — user thu từ PA-A sau đo tốc độ), không schema block, xoay 3 key, +2'/video; V11 gate soi 22/demote 3 trúng cả 3/lỗi 0; C3 quyền-trừ-điểm ĐÓNG warning-only vĩnh viễn. Quan sát user: "chọn lại chưa ngon lắm nhưng chấp nhận được" — theo dõi bước chọn-thay các video sau | ✅ cổng MẮT+TAI V11 đạt (nhạc editor 4 chương lần đầu ra trận) |
| **★ ĐANG LÀM: YTREF điểm nhô + tag bối cảnh (user chèn 2026-07-10 trước A1/scale)** | Nạp video YouTube tham khảo (CapCut tách cảnh tự động → ingest y viral c8) + cờ ĐIỂM NHÔ Most Replayed (yt-dlp heatmap, bê tool ME OutlierY của user) + gói TAG BỐI CẢNH (tiêu đề thật + YouTube chapters + flag --topic). **`MO_TA_VAN_HANH_YTREF_DIEM_NHO.md` DUYỆT TRỌN — chi tiết + bẫy ở NHAT_KY §YTREF-M0.** Còn lại: **M1** ytpeaks + pytest → **M2** delta ingest + A/B tag ~40 cảnh + mẻ thử bộ MOON (cổng mắt kép) → **M3** PEAK_BONUS phễu + video kiểm SP012→V12 (cổng mắt+tai) | mô tả ✅ · M1–M3 ⏸ |
| **★ KẾ TIẾP SAU YTREF: A1 + nhóm B** | **A1 video space kế tiếp (SP013...)** vừa sản xuất vừa đo B1 → **B2 Level 1 batch** (quyết bằng số đo B1, nhớ còn-ngỏ direct timeout chương dài) · **B3 niche 2** (checklist memory `multi-niche-isolation-audit`; tag bối cảnh YTREF là xương sống tag địa danh cho travel) · **B4 learning loop** | mô tả vận hành từng cái |

**Lý do trình tự** (đã tư vấn, user đồng ý): lỗi code cứng ít (pytest+P4/P5 đỡ); rủi ro thật là
(1) code dồn → video sai không truy được tầng nào, (2) tính năng C có thể làm video TỆ ĐI
(foundation treo có chủ đích "mở khi mắt thấy thiếu"), (3) rà chồng chéo phình khi hệ đổi
liên tục (riêng "mood" đã 4 tầng cùng quản). Nhịp thở video-kiểm giải cả 3.

---

---

## NHÓM A — SẢN XUẤT NGAY (0 code, dùng hệ có sẵn)

| # | Việc | Công | Được gì |
|---|---|---|---|
| **A1 ★** | **Video space kế tiếp (SP013, SP014...)** — quy trình y SP012, anh đưa folder content+voice | ~1 buổi/video | Video thật + ĐO thời-gian-người/video (tiền đề quyết B2) + lộ bug tần suất thấp + cụm viral/Ken Burns chai |
| A2 | Nạp viral đợt 2 (anh tách cảnh nguồn mới) | 1 lệnh/draft, ~$0,001/cảnh | Kho viral dày thêm; quy trình đã chai, nạp theo DANH SÁCH chỉ định |
| A3 | Nạp kho own thêm (draft editor mới) + chạy lại `library-dna` | 1-2 lệnh/draft | DNA pacing/thở chính xác hơn (hiện 3 draft); kho own cạnh tranh lại viral |
| A4 | Nâng nét viral 1080p (tải lại 9 file đè tên cũ → re-ingest) | ~$1,2 + 1 giờ | Chỉ khi xem nhiều video thấy chê 480p — hiện user đã chấp nhận |

## NHÓM B — MỞ RỘNG QUY MÔ (hướng 200 video/tháng)

| # | Việc | Công | Ghi chú |
|---|---|---|---|
| **B1 ★** | Đo bottleneck qua 2–3 video A1 (thời gian người từng khâu: chuẩn bị input / phiên đạo diễn / duyệt beats / chờ máy / kiểm draft) | 0 (ghi chép khi chạy A1) | Điều kiện tiên quyết của B2 — không batch mù |
| B2 | **Level 1 — batch hóa**: tự động khâu tốn người nhất (dự đoán: phiên đạo diễn → `claude -p` + vòng validator tự sửa như direct-ingest; hàng đợi nhiều video) | LỚN, nhiều buổi + mô tả vận hành | Nền móng có sẵn: memory `claude-code-subprocess-windows` + `level2-first-then-level1` (3 trụ chuyển mượt) |
| B3 | Niche thứ 2 (travel / deepsea / facts-about-countries) | ~2-3 buổi | Cần: nạp kho niche + `library-dna` ≥3 draft + pause_dna niche đó (+ geo tree nếu travel). Foundation dùng chung hết |
| B4 | Learning loop `approved`: editor đánh dấu asset tốt → phễu ưu tiên (cột db CÓ SẴN, chưa ai ghi) | nhỏ-trung + thiết kế cách editor duyệt | Kho tự tốt lên theo thời gian |

## NHÓM C — CHẤT LƯỢNG DỰNG (backlog foundation còn treo — mở khi xem video thấy THIẾU)

| # | Việc | Nguồn | Công |
|---|---|---|---|
| C1 | **Ambient cho hình thở** (tiếng gió/sóng/vũ trụ thay im lặng trong ô thở — "im lặng tuyệt đối = lỗi trong tai khán giả") | e1 backlog #2 — điều kiện "sau Phase B" ĐÃ ĐỦ | trung |
| C2 | **Punch-in** nhấn từ khóa (zoom cú 10-20% bám anchor_word) | f2 §3 — giờ RẺ hơn vì keyframe scale đã verify render đúng; NHỚ bẫy time_offset theo nguồn khi áp lên VIDEO | trung |
| C3 | So màu nội bộ chương (cảnh báo footage lệch màu chủ đạo — `dominant_color` ĐÃ có trong db từ PB2) | b1 backlog #2 | nhỏ, code thuần |
| C4 | Tone cấp video (chặn mood beat lệch tone tổng) | b1 backlog #1 | nhỏ |
| C5 | Vision gate top-pick: mood + **ĐÚNG CHỦ THỂ** (3c của V123 dời về đây 2026-07-09 — lưới cho ca slug không tiết lộ, vd hình đỏ rực không có chữ "mars"). Nguyên tắc user chốt: chỉ soi TOP-PICK, fail thử 1 ứng viên kế, vẫn fail lấy best + warning editor chỉnh tay — KHÔNG thành cửa loại thứ 3 | b1 backlog #3 + MO_TA_NANG_CAP_V123 §V3-3c | trung, tốn call |
| C6 | Bảng đồng nghĩa concept↔tag (fix PB8: từ chuyển động "rotating/timelapse" AND-trượt oan vì GLM tag frame tĩnh) | PB8 còn ngỏ | nhỏ-trung |
| C7 | Shot thở 2.0 backlog §6.5: đo phân bố k khi thêm project editor + đóng gói tool scan DNA niche mới thành lệnh | MO_TA_SHOT_THO §6.5 | nhỏ |

## NHÓM D — TRẢ NỢ KỸ THUẬT / VẬN HÀNH

| # | Việc | Ghi chú | Công |
|---|---|---|---|
| **D1 ★** | **Backup kho F:** — **✅ XONG 2026-07-09**: `D:\AutoEdit_backup\library` (1914 file/5,10GB) + `AutoEdit_C` (cache.db+music/sfx). ⚠ E: cùng đĩa vật lý với F: — backup phải sang D:/NAS. Sau mẻ nạp lớn chạy lại 2 lệnh robocopy (NHAT_KY §D1-BACKUP) | mất F: = mất kho + mọi tag đã trả tiền vision | ~30 phút, robocopy |
| D2 | Đường `direct` cũ thiếu khối vocab C4 + DNA — **✅ XONG 2026-07-09**: run_direct chèn `vocab_block`+`dna_block` (tái dùng hàm live.py) vào pass 2 qua `inputs.channel`, 0 đổi CLI, fail-open y đường sâu (NHAT_KY §D2) | đã đóng | — |
| D3 | `local limit=5` — mỗi query local chỉ lấy 5 ứng viên; kho giờ 1874, cân nhắc nới | còn ngỏ cũ | nhỏ |
| D4 | ~~Thay ANTHROPIC_API_KEY~~ — **BỎ (user 2026-07-09)**: hệ KHÔNG cần key (NÃO đi Claude Code subscription, vision đi GLM); key hết hạn đã XÓA khỏi `.env`. Chỉ điền lại nếu sau này dùng fallback `--engine api` (director/client.py) hoặc `--engine claude` (vision.py) — KHÔNG hỏi lại user | đã đóng | — |
| D5 | Bật lại git — **✅ XONG 2026-07-09**: git LOCAL (user từng hoãn vì tưởng là GitHub; đã làm rõ). Commit gốc `890c68b`, .gitignore loại .env/.venv/projects (29,6GB). Luật mới CLAUDE.md P4: commit mốc sau mỗi milestone, KHÔNG remote/push | đã đóng | — |

---

## Thứ tự Claude khuyên (user toàn quyền đổi)

1. **D1 backup kho** (30 phút, chống mất trắng) → 2. **A1 ×2–3 video** (vừa ra sản phẩm vừa đo B1)
→ 3. **A2 viral đợt 2** khi có nguồn → 4. quyết **B2 Level 1** bằng số đo B1 → nhóm C mở dần
theo cái MẮT THẤY THIẾU khi xem video thật (đúng triết lý f2: "mở khi nhu cầu đến, không làm ngay").
