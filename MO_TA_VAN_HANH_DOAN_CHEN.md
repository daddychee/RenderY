# MÔ TẢ VẬN HÀNH — ĐOẠN CHÈN Δ (NHIP-M2)

> Gói CẮT THEO NHỊP NHẠC, mốc M2 (`BAN_GIAO_NHIP_NHAC.md` §3, §7). Viết 2026-07-20.
> Trạng thái: ✅ **ĐÓNG TRỌN — CỔNG MẮT USER DUYỆT 2026-07-20** (draft
> `RD89_OMAN_10MIN_20260720_V2`: Δ 188,42→208,42s đúng 20,00s, video phủ kín 0 hở,
> voice sau Δ khớp từng chữ số với project.json, ambient dừng đúng mép vào Δ). pytest 661.

---

## 1. Làm gì

Editor **khai đoạn chèn** (montage không voice giữa bài — vd 20s "thiên nhiên hùng vĩ"
giữa chương 3 và 4) → máy **chèn Δ giây vào timeline**, mọi thứ phía sau (voice, nhạc,
chart, card, overlay, SFX) **tự dịch đúng**, không trượt sync (bug NAM CHÂM).

**Phạm vi M2 (cố ý):** chỉ cơ chế chèn + dịch. Trong Δ máy đặt **slug giữ chỗ**
("EDITOR ĐẮP FOOTAGE") — footage thật là M4 (project editor đưa) / M5 (khai bằng lời);
nhạc editor đưa thay từ điểm chèn (phương án B) là M3. Độ dài Δ **editor quyết**,
không trần (user chốt 2026-07-19).

## 2. Editor dùng thế nào

```bash
autoedit insert <project> --after-beat 57 --dur 20 --note "montage thiên nhiên"
autoedit insert <project> --after-chapter 3 --dur 25   # = sau beat CUỐI chương 3
autoedit insert <project>                              # liệt kê đã khai
autoedit insert <project> --remove 57                  # xóa
# rồi chạy lại: cut -> music (nếu music-sync) -> source -> assemble
```

- Δ nằm **SAU** hình thở + giãn nghỉ của beat đó: voice → thở (ambient như cũ) → **Δ** → voice kế.
- Khai lại cùng beat = SỬA (mỗi beat 1 Δ). Cấm sau **beat cuối** video (outro không có
  voice sau — mọi `total_end` của assembler dựa segment cuối; editor tự kéo đuôi trong CapCut).
- Beat không kết câu → máy CẢNH BÁO (Δ sẽ ngắt giữa ý nói) nhưng không chặn — editor quyết.

## 3. Chạy ở đâu — MỘT chỗ sinh timeline (vì sao không dịch tay)

Δ tiêu thụ tại `cutter/timeline.py` (`plan_segments`/`apply_timeline` — cursor cộng thêm
`insert_after`), đúng khuyến nghị BAN_GIAO §7b: timeline sinh ở đúng một chỗ, nên
`beat.timeline_*` / `seg.timeline_*` phía sau Δ **tự đúng** → 10/14 chỗ đọc tọa độ trong
assembler + toàn bộ tầng đọc thẳng `beat.timeline_start` (chart PiP, info-card, overlay,
kinetic — bẫy im lặng §7d.1) không phải sửa dòng nào. Dịch tay 14 chỗ là chắc chắn sót.

Chuỗi: `project.inserts` (lệnh `insert` ghi) → `run_cut` validate + build map →
`plan_segments(beats, inserts)` (beat có Δ kết thúc run) → cursor cộng Δ →
`VoiceSegment.insert_after` → `coverage_windows` sinh **cửa sổ insert riêng**
(`CoverWindow.insert=True`, KHÔNG phải ô thở) → assembler đặt **slug** lấp Δ
(chống NAM CHÂM, editor thấy Δ ngay trên timeline).

## 4. Bốn chỗ xử lý tay (§7c bàn giao) — đã làm gì

| §7c | Xử lý |
|---|---|
| 1. Hình trong Δ | M2: slug giữ chỗ. Lưới beat cắt nhịp trong Δ = M4/M5 (khi có footage thật) |
| 2. Kế hoạch nhạc ÔI THIU | Δ chỉ có tác dụng khi chạy lại `cut` — `run_cut` VỐN gọi `mark_music_stale()` mỗi lần → plan cũ tự xóa, không đường nào lọt accent cũ |
| 3. Mẫu số pacing | `run_assemble` trừ tổng Δ khỏi `total_end` trước khi gọi `_warn_pacing_dna` (slug vốn không vào `placed_shots` — tiền lệ giữ nguyên) |
| 4. Ambient nuốt Δ | `breath_slots` cắt ô ambient tại mép VÀO Δ — Δ không nhận ambient (1 clip không loop phủ Δ dài = im lặng nửa ô; trong Δ nhạc là chủ đạo) |

## 5. RÀ CHỒNG CHÉO (P5) — các tầng cùng quản vùng Δ

| Tầng | Đụng không? | Kết luận |
|---|---|---|
| Cổng `windows[0].start == 0` (§7a) | Δ luôn SAU một beat → không bao giờ ở đầu video | cổng giữ nguyên, không ngược chiều |
| `check_coverage_invariants` | Cửa sổ insert liền khít trong chuỗi windows → phủ kín như cũ | invariant TỰ canh Δ (hở là chết ngay) |
| `split_breath_shots` | Ô thở của chính beat mang Δ vẫn chẻ như cũ; cửa sổ Δ có `breathing_dur=0` → guard tự bỏ qua | không đụng |
| `apply_j_cuts` | Ô thở ≥1,2s mà KẾ là Δ → **KHÔNG J-cut** (guard mới): J-cut nghĩa là "shot kế vào trước khi voice quay lại", sau Δ không phải voice; và Δ phải giữ ĐÚNG độ dài khai | luật mới, khai ở đây |
| `snap_to_accents` | Mép VÀO/RA Δ **MIỄN snap** (guard mới): snap co/giãn Δ lệch số editor khai. Footage trong Δ cắt theo beat là việc M4 | luật mới, khai ở đây |
| M-CHANGE (`music_boundaries`) | Mép Δ vào danh sách edges → ranh giới chương ngay sau Δ tự neo vào mép RA Δ (đổi nhạc đúng lúc Δ kết thúc) | thuận chiều; nền sẵn cho M3 phương án B |
| Nhạc theo chương (§7e) | Chương i phủ tới `bounds[i+1]` → Δ giữa/cuối chương **tự được nhạc chương đó phủ kín** | không phải làm gì |
| Ducking F8 | Gap voice quanh Δ ≥ MIN_BREATH → nhạc **NỞ 0.5 suốt Δ** (không voice) | cộng hưởng — đúng ý "nhạc chủ đạo" |
| Ambient C1/S2 | Ô ambient cắt tại mép vào Δ (mục 4.4) — phần thở TRƯỚC Δ vẫn có ambient như cũ | luật mới, khai ở đây |
| Drone S1 | Loop suốt video phủ cả Δ (space/life-in); deepsea gate-cảnh đọc beat → Δ không có beat → không bed trong Δ | chấp nhận M2 (Δ chưa có footage); xem lại ở M4 |
| Hook SFX S3 / credit VD4 / Ken Burns | Slug không vào `cuts_log`/`credit_log`/`kb_log` (như slug needs_human) | không đụng |
| Pacing DNA | Mẫu số trừ Δ (mục 4.3) | đã xử lý |
| Chart PiP / info-card / overlay / kinetic (§7d.1) | Đọc `beat.timeline_start` — cut đã dịch beat → tự đúng | không đụng (nhờ chèn ở tầng timeline) |
| Voice track | Đọc `seg.timeline_start` — tự đúng | không đụng |
| `_safe_add_segment` nuốt overlap (§7d.3) | Không thêm loại segment audio mới ở M2 | không kích hoạt |
| `total_end` (5 chỗ: assembler ×4, schedule, report) | Toàn bộ = `segment cuối.timeline_end + breathing` — Δ sau beat cuối bị CẤM nên luôn đúng | rà đủ, không sửa |
| `mark_music_stale` | `run_cut` gọi sẵn mỗi lần chạy | an toàn (§7c.2) |

**Tầng nào có thể ÂM THẦM LẬT Δ?** Chỉ 2 ứng viên: snap (co giãn mép) và J-cut (gặm mép)
— cả hai đã chặn bằng guard + test hồi quy. Ngược lại Δ không lật tầng nào: nó là cửa sổ
riêng, không mang breathing_dur nên mọi luật ô-thở tự né nó.

## 6. File : dòng

| File | Đổi |
|---|---|
| `project.py` | +`InsertSpec` · `Project.inserts` · `VoiceSegment.insert_after` (project cũ load bình thường) |
| `cutter/timeline.py` | `SegmentPlan.insert_after` · `plan_segments(beats, inserts)` · cursor cộng Δ |
| `cutter/runner.py` | validate (beat tồn tại/không cuối/dur>0) + warning + INDEX.txt hiện Δ |
| `packager/coverage.py` | `CoverWindow.insert` · cửa sổ Δ trong `coverage_windows` · guard J-cut + snap |
| `packager/assembler.py` | Δ → slug (`_fill_holes_with_slug`) + warning NHIP-M2 + pacing trừ Δ |
| `ambient/schedule.py` | `breath_slots` cắt ô tại mép vào Δ |
| `cli.py` | lệnh `insert` (khai / `--after-chapter` / `--remove` / liệt kê) |
| `tests/test_insert.py` | 10 test (timeline/coverage/J-cut/snap/ambient/schema) |

## 7. Cách kiểm (cổng)

- pytest: `.venv/Scripts/python.exe -m pytest -q` — **661 passed**.
- **Cổng MẮT user: ✅ DUYỆT 2026-07-20** ("duyệt xong M2"). Video kiểm: tái dùng
  `projects/rd89-oman-10min-20260720`, khai `insert --after-chapter 2 --dur 20` (beat 27)
  → cut (587→**607,3s**, đúng +20) → music → source (81 beat, 0 needs_human) → assemble
  → draft `E:\CapCut Drafts\RD89_OMAN_10MIN_20260720_V2`.

  Số đo trong `draft_content.json`: Δ tại **188,42→208,42s = đúng 20,00s** · video_l1
  **phủ kín, 0 hở/đè** · voice đầu sau Δ **208,418458s khớp TỪNG CHỮ SỐ** project.json ·
  6 info-card layer2 sau Δ rơi đúng `beat.timeline_start` mới · nhạc ch2 phủ hết Δ rồi
  crossfade ch3 tại 205,4s, **keyframe ducking nở 0.5 suốt Δ** → nép 0.2 khi voice vào ·
  ambient cuối trước Δ dừng tại **188,42 = đúng mép vào Δ**.

  ⚠ Lưu ý khi kiểm lại: chạy lại `music` làm plan cũ bị xóa (đúng thiết kế chống ôi
  thiu) nên **nhạc đổi bài** so bản trước — draft kiểm M2 là bản dựng LẠI hoàn toàn,
  không so tai được với V1/V13.
