# MÔ TẢ VẬN HÀNH — HÌNH THỞ 2.0 ĐỢT 1: GIÃN NGHỈ MÁY + J-CUT (2026-07-08)

> **TRẠNG THÁI: user chốt "tiến hành code luôn"** (2026-07-08) sau khi duyệt phân tích
> SP1-003 + trả lời câu hỏi an toàn nghĩa câu. Tài liệu này ghi thiết kế + rà chồng chéo
> để chuyển giao; code cùng ngày. Đợt 2 (footage riêng cho ô thở, chuỗi trình chiếu,
> sàn + cứu hộ) vẫn theo backlog d2, CHƯA làm.
>
> **Đợt 1.5 (tầng kết mệnh đề) — thiết kế ở §6 dưới, user DUYỆT + code xong 2026-07-08
> (pytest 257/257, draft V3 — NHAT_KY §D2-DOI-CHIEU), ⏸ chờ cổng TAI.**
> Cổng TAI đợt 1 đạt một phần ("tốt hơn nhưng không bằng editor") → quét 213 điểm cắt
> SP1-003 (NHAT_KY §D2-QUET-CAT) + đối chiếu script gốc → editor có TẦNG THỨ HAI ta
> chưa làm: giãn tại KẾT MỆNH ĐỀ. §6 lật có-bằng-chứng một luật của §2.

## 1. Số đo nền (3 draft space, đọc-only; chi tiết NHAT_KY §D2-PHAN-TICH)

| Draft | Nghỉ chèn/phút | Trung vị | Tầng 0,7–1,5s /phút | Thở ≥1,5s /phút |
|---|---|---|---|---|
| SP1-003 | 7,5 | 0,53s | 1,9 | 0,61 |
| SP1-001 | 8,1 | 0,70s | 2,7 | 1,41 |
| SP1-004 | 5,9 | 0,57s | 1,45 | 0,80 |

Voice AI của ta đã có sẵn tầng 0,3–0,7s (17,5 nghỉ/phút tự nhiên) — cái THIẾU là tầng
"nghỉ rõ" 0,7–1,5s (~1,9/phút) và J-cut ở mép ô thở (14/18 ô của SP1-003).

## 2. AN TOÀN NGHĨA CÂU (câu hỏi user) — 2 khóa đồng thời, cả hai từ máy

Điểm giãn CHỈ được chọn khi **CẢ HAI** điều kiện:
1. **Khóa dấu câu:** beat.text kết thúc bằng `.` `?` `!` (script gốc có dấu — máy biết
   chắc vị trí kết CÂU, không phải đoán từ khoảng lặng). Kết mệnh đề (`,` `:` `;` `—`)
   và giữa mệnh đề: KHÔNG BAO GIỜ giãn.
   > **Đợt 1.5 (2026-07-08, user duyệt) LẬT MỘT NỬA luật này có bằng chứng:** kết
   > mệnh đề ĐƯỢC giãn theo tầng riêng δ nhỏ 0,2–0,4s (§6 — editor cắt 56/213 điểm
   > tại dấu mệnh đề). GIỮA MỆNH ĐỀ (không dấu) vẫn cấm tuyệt đối.
2. **Khóa nghỉ thật:** alignment đo voice có nghỉ tự nhiên ≥0,3s tại đúng chỗ đó
   (AI voice đã tự ngắt — ta chỉ GIÃN, không tạo nghỉ từ hư không).

Đo thật video Jupiter: 7 khoảng lặng "giữa mệnh đề" (vd "Jupiter | and", "deadly |
never") — đúng loại nguy hiểm user lo — đều bị khóa 1 loại tự động. 78 điểm kết-câu
đạt cả 2 khóa (7,6/phút) → chỉ cần chọn ~20 (1,9/phút): dư dả.

## 3. Thiết kế

**A. Giãn nghỉ máy** (`cutter/pause.py::plan_micro_pauses` — pure, 0 call NÃO, chạy
đầu stage cut):
- Ứng viên = ranh giới beat đạt 2 khóa §2, beat trước không có breathing_after.
- Mật độ đích `RO_PER_MIN = 1.9` điểm/phút voice (trung vị 3 draft). Chọn ưu tiên
  nghỉ-tự-nhiên-dài trước (voice đã tự ngắt đậm = chỗ đáng ngắt đậm), khoảng cách
  ≥12s với nhau và với mọi điểm breathing.
- Lượng chèn δ = clamp(nghỉ tự nhiên, 0,4–0,7s) → nghe ra ~0,7–1,1s (cộng phần lặng
  giữ lại 2 mép cắt ~0,42s) — đúng tầng đích.
- Ghi vào `Beat.micro_pause_after` (field MỚI, máy điền — tách khỏi `breathing_after`
  của đạo diễn). Cutter cắt run tại đó y như breathing (cắt GIỮA khoảng lặng theo
  máy đo khởi âm sẵn có — không dính chữ), chèn gap δ lên timeline.

**B. J-cut mép ô thở** (`coverage.py::apply_j_cuts`, assembler gọi sau coverage_windows):
- Cửa sổ có `breathing_dur ≥ 1,2s`: mép video với cửa sổ kế lùi sớm **0,3s** — shot
  kế vào TRƯỚC khi voice nói lại (mẫu 14/18 SP1-003); ô nhỏ nhất vẫn còn ≥0,9s hình giữ.
- Chỉ dịch VIDEO; voice/nhạc không đổi. Tầng micro (δ ≤0,7s) không bao giờ bị J-cut.

## 4. RÀ CHỒNG CHÉO (P5)

| Tầng cùng quản | Kết quả rà |
|---|---|
| Ducking nhạc (`ducking.merge_voice_intervals`, MIN_BREATH=1.0) | gap timeline micro ≤0,7s < 1,0 → nhạc NUỐT, không phập phồng. J-cut chỉ đụng video. KHÔNG đụng |
| Validator direct-ingest (breathing tại từ có nghỉ ≥0,3s) | micro là việc SAU ingest (stage cut), field riêng — không đụng luật đạo diễn |
| Coverage phủ kín (`check_coverage_invariants`) | cửa sổ cuối segment kéo dài thêm δ (như breathing); J-cut dịch mép CHUNG 2 cửa sổ → liền khít giữ nguyên; test bất biến mới |
| `split_window` multi-shot (tail không chia vào ô thở) | tail = breathing_dur + micro_dur — nhát cắt con không rơi vào khoảng lặng |
| total_end (4 chỗ assembler đọc segment cuối) | plan_segments ép breathing=micro=0 cho segment cuối (luật cũ giữ) → công thức cũ vẫn đúng |
| Overlay/SFX/nhạc theo beat.timeline_* | cut điền lại timeline SAU khi chèn micro → tự đúng (cơ chế cursor sẵn có, "ổ bug kinh điển" đã phòng từ M4) |
| DNA Mảnh B (std shot, cpm) | shot dài thêm ~δ ở điểm giãn, J-cut ±0,3s — nhiễu nhỏ, fail-open |
| Chạy lại stage cut (đè sạch) | plan_micro_pauses ghi đè TOÀN BỘ field mỗi lần chạy (reset 0 rồi điền) — deterministic, không cộng dồn |

## 5. Cổng kiểm (P4)

- pytest: khóa dấu câu (KHÔNG chọn giữa mệnh đề dù lặng dài — regression cho đúng nỗi
  lo user) · khóa nghỉ thật · mật độ + khoảng cách · timeline chèn gap đúng + bất biến
  phủ kín · J-cut dịch mép đúng + không đụng micro · FULL suite.
- Chạy lại video Jupiter (cut → assemble → report): phân bố nghỉ sau giãn phải mọc
  tầng 0,7–1,5s ~1,9/phút; số điểm giãn in ra report/log.
- **Cổng mắt + TAI user:** nghe draft mới — nghỉ có tự nhiên hơn không, có chỗ nào
  ngắt sai nghĩa không. Claude KHÔNG tự phán đạt.

---

# ĐỢT 1.5 — TẦNG KẾT MỆNH ĐỀ (2026-07-08, user duyệt — CODE XONG, chờ cổng TAI)

## 6.1 Bằng chứng: đối chiếu 213 điểm cắt SP1-003 với script gốc

Quét whisper (§D2-QUET-CAT) ra 14 điểm "giữa mệnh đề" đáng ngờ. Đối chiếu từng điểm
với script gốc `E:\PROJECT NHAN BAN\SPACE 1\SP1 - 003\CONTENT ENGLISH\SP1-003 - CONTENT.txt`:

| # | Whisper nghe | Script gốc thật | Phân loại lại |
|---|---|---|---|
| 1 | "universe ‖ it is not empty" | "universe, **and** it is not empty" | KẾT MỆNH ĐỀ (mất `,`) |
| 5 | "every direction ‖ then it fades" | "direction, **and** then it fades" | KẾT MỆNH ĐỀ |
| 6 | "what we see. The ‖ universe" | "we see**:** the observable universe" | KẾT MỆNH ĐỀ (`:`) |
| 7 | "the diameter ‖ to end" | "the diameter, **end** to end" | KẾT MỆNH ĐỀ |
| 8 | "Reach The Edge ‖ Even Given Forever" | tiêu đề C4 "edge, even given forever" | KẾT MỆNH ĐỀ |
| 9 | "Even Given Forever ‖ see why" | hết tiêu đề `.` + "To see why," | KẾT CÂU (ranh giới tiêu đề) |
| 10 | "travel to them ‖ send a message" | "them, **or** send a message" | KẾT MỆNH ĐỀ |
| 11 | "breathe ‖ this part" | "breathe, **because** this part" | KẾT MỆNH ĐỀ |
| 12 | "at a time ‖ let it work" | "time, **and** let it work" | KẾT MỆNH ĐỀ |
| 13 | "assumption that ‖ the biggest scales" | "that**,** on the biggest scales," | KẾT MỆNH ĐỀ |
| 14 | "be observed ‖ where this story" | "observed **—** is where this story" | KẾT MỆNH ĐỀ (`—`) |
| 2,3,4 | "past it ‖ not a monster" · "distance ‖ can reach" · "reach in ‖ take everything" | câu chốt hook 42–47s, KHÔNG có dấu | GIỮA MỆNH ĐỀ THẬT |

(Whisper vừa mất dấu vừa nuốt liên từ ngắn — and/or/because/is — nên quét thô phân loại nhầm.)

**Bảng 3 tầng CHỐT sau đối chiếu (213 điểm cắt cùng-file):**

| Vị trí cắt | n | % | Gap chèn trung vị (p90) |
|---|---|---|---|
| Kết câu `.?!` | 154 | 72,3% | 0,60s (1,23) — ✅ đợt 1 đã làm |
| **Kết mệnh đề `,;:—`** | **56** | **26,3%** | **0,37s (0,53)** — ❌ tầng này cần thêm |
| Giữa mệnh đề thật | 3 | 1,4% | ~0,2s — thủ pháp tu từ, KHÔNG làm |

→ **98,6% điểm cắt editor nằm ở ranh giới CÓ DẤU trong script.** Khóa dấu câu đợt 1
đúng hướng — chỉ MỞ RỘNG sang dấu mệnh đề, tuyệt đối không nới sang giữa mệnh đề
(3 điểm còn lại đều trong CÙNG 1 câu hook kịch tính — editor cắt vụn 1 câu dài có
chủ đích ở ranh giới ngữ điệu; 1,4% không đáng code, P2).

## 6.2 Thiết kế tầng kết mệnh đề (`cutter/pause.py`, mở rộng `plan_micro_pauses`)

Giữ nguyên khung 2 khóa; thêm TẦNG 2 chọn SAU tầng câu:

| | Tầng CÂU (đợt 1 — không đổi) | Tầng MỆNH ĐỀ (mới) |
|---|---|---|
| Khóa dấu | beat.text kết `.?!` | beat.text kết `,` `;` `:` `—` `–` |
| Khóa nghỉ thật | ≥0,3s | ≥0,3s (như nhau — editor cắt tại nghỉ nguồn p10=0,4s) |
| δ chèn | clamp(nghỉ, 0,4–0,7) | **clamp(nghỉ, 0,2–0,4)** (gap editor trung vị 0,37/p90 0,53) |
| Nghe ra | ~0,7–1,1s | ~0,65–0,85s → THỨ BẬC câu > mệnh đề giữ đúng |
| Mật độ | RO_PER_MIN=1,9/phút | CLAUSE_PER_MIN=1,9/phút (56/29,5ph) |
| Spacing | ≥12s | **≥6s** (với nhau + với mọi điểm câu/breathing đã chọn) |
| Ưu tiên | nghỉ dài trước | nghỉ dài trước (như nhau) |

- **Thứ tự chọn:** tầng câu chọn xong TRƯỚC (y nguyên đợt 1) → tầng mệnh đề lấp vào
  giữa với spacing ngắn hơn. Vì sao 6s: editor 213 điểm/29,5ph ≈ 8,3s/điểm trung bình;
  12s cho tầng mệnh đề sẽ bóp chết nó vì luôn kẹt giữa 2 điểm câu.
- **Cùng field `micro_pause_after`** — cơ chế hạ nguồn (cắt giữa khoảng lặng, chèn gap
  timeline, coverage, ducking, split_window) dùng lại NGUYÊN, vì δ ≤0,4 nằm dưới mọi
  ngưỡng đã rà đợt 1. Không field mới, không đổi schema.
- Beat cuối + beat có breathing_after: vẫn loại (luật cũ).
- **Data kiểm khả thi (Jupiter 10,3ph):** 20 beat kết mệnh đề (1,94/phút — vừa khớp
  mật độ đích), 16 đạt khóa nghỉ ≥0,3s (4 beat gap=0 tự loại — không có lặng thì không
  cắt được, an toàn tự nhiên). Ước sau spacing: ~10–14 điểm mới, tổng 2 tầng ≈ 3/phút.

## 6.3 RÀ CHỒNG CHÉO đợt 1.5 (P5)

| Tầng cùng quản | Kết quả rà |
|---|---|
| **Luật đợt 1 "kết mệnh đề KHÔNG BAO GIỜ giãn"** (§2 file này + docstring pause.py + test `test_micro_pause_never_stretches_mid_clause`) | **NGƯỢC CHIỀU CHỦ ĐỘNG — lật có bằng chứng** (56 điểm editor). Sửa CẢ 3 CHỖ cùng lúc kẻo tài liệu ngược code. Giữa mệnh đề (không dấu) VẪN khóa tuyệt đối — ý regression của user giữ nguyên, chỉ đổi fixture |
| Ducking (MIN_BREATH=1.0) | δ mệnh đề ≤0,4 < 0,7 đợt 1 < 1,0 → nhạc nuốt hết, không phập phồng. KHÔNG đụng |
| J-cut (ngưỡng breathing ≥1,2s) | micro cả 2 tầng ≤0,7 → không bao giờ J-cut. KHÔNG đụng |
| split_window / coverage / total_end / segment cuối | cùng field micro_pause_after → mọi công thức đợt 1 tự đúng; test bất biến cũ phủ luôn |
| Validator direct-ingest | không đụng (micro là stage cut, field máy) |
| Nhịp tổng thể / DNA Mảnh B | tổng thêm ~+4–6s/10ph (14×~0,35) — nhỏ hơn đợt 1 (+11s); std shot nhiễu nhỏ, fail-open |
| Chạy lại stage cut | plan ghi đè toàn bộ field mỗi lần — deterministic giữ nguyên |

## 6.4 Cổng kiểm đợt 1.5 (P4)

- pytest mới: chọn đúng dấu mệnh đề · δ clamp 0,2–0,4 · tầng câu ưu tiên trước +
  spacing 6s · **regression giữ: giữa mệnh đề (không dấu) vẫn không bao giờ giãn dù
  lặng dài** · deterministic. FULL suite sau đó.
- Chạy lại Jupiter cut→assemble → draft **V3** (tên mới NT5): đếm điểm mới 2 tầng,
  soi tay ≥5 điểm mệnh đề đúng dấu `,;:` trong script.
- **Cổng TAI user:** so V3 với V2 và với bản gốc editor. Claude KHÔNG tự phán đạt.
