# MÔ TẢ VẬN HÀNH — HÌNH THỞ 3.0: NHỊP NGHỈ THEO DNA 3 PROJECT (2026-07-08)

> **TRẠNG THÁI: user duyệt + CODE XONG 2026-07-08** (pytest 258/258, cổng số §6 ĐẠT,
> draft **`SCRIPT_VOICE_20260707_132450_V5`** — ⏸ chờ cổng TAI). Bước HỌC (máy thuần,
> 0 API): quét 464 điểm cắt + 52 ô thở của 3 project editor SP1-001/003/004, tự đối
> chiếu script gốc (95% verified). Artifact bền: `pause_dna.json` +
> `pause_dna_rows_SP1-00X.json` (project root; bản pipeline đọc:
> `~\AutoEdit\library\space\pause_dna.json`). Thay khung cho đợt 1+1.5
> (`MO_TA_VAN_HANH_HINH_THO_2.md` — giữ làm lịch sử); gộp "phương án A thở sâu".
> **2 điều chỉnh khi chạy thật (ghi tại chỗ trong §3/§5):** trần chèn 13%→15%;
> trần thở validator vốn đã 6s sẵn (không phải nâng 3→6 như dự tính).

## 1. DNA đo được (đã lọc nhiễu: gap ≥8s = ranh giới section/montage, loại)

### 1a. Điểm cắt theo loại vị trí — NGHE RA = nghỉ nguồn + gap chèn

| Loại (gộp 3 project, 464 điểm) | Mật độ cắt | Nghỉ nguồn TTS | Gap chèn p50 | **NGHE RA p25 / p50 / p75 / p90** |
|---|---|---|---|---|
| **Kết câu** `.?!` (n=336) | **4,9/phút** (~50% số câu script) | 0,85s | 0,63s | **1,28 / 1,55 / 1,90 / 2,73s** |
| **Kết mệnh đề** `,;:—` (n=109) | **1,6/phút** | 0,60s | 0,37s | **0,76 / 0,95 / 1,19 / 1,39s** |
| Giữa mệnh đề thật (n=19) | 0,28/phút | 0,78s | 0,40s | 0,87 / 1,12 / 1,83s |

- Cả 3 project HỘI TỤ: kết câu p50 = 1,78 / 1,51 / 1,50s — đây là chữ ký nhịp của editor.
- KHÔNG điểm cắt nào nghe ra <0,5s. Spacing giữa các điểm cắt: trung vị 7–8,6s.
- Editor cắt ~50% ranh giới câu; nửa còn lại TTS của editor tự nghỉ ~0,85s (voice ta
  chỉ ~0,5s — khoảng cách còn lại này ghi backlog, chưa xử đợt này).
- Giữa mệnh đề = 4% số điểm, KHÔNG ngẫu nhiên: trước cú đấm ("cosmic house ‖1,03s‖
  **But one.**"), nhịp liệt kê ("rovers across Mars, ‖ dropped a probe…, ‖ photographed
  Pluto"), câu chốt hook. → quyết định NGHĨA, thuộc NÃO, không cho máy tự do.
- Tổng chèn sạch: +8,3% (004) · +8,6% (003) · +16,8% (001 — phần hook nhịp chậm) →
  khung đích **+8–13%**, trần thiết kế 13%.

### 1b. Ô thở ≥1,5s (52 ô sạch sau lọc)

| | SP1-001 | SP1-003 | SP1-004 |
|---|---|---|---|
| Mật độ | 1,34/phút¹ | 0,61/phút | 0,65/phút |
| Độ dài p50 / max | 3,23 / 6,93s | 2,40 / 7,13s | 2,13 / 7,57s |
| Tại ranh giới chương | (script không có ts) | **6/6 chương** | **6/8 chương** |

¹ 001 chỉ đo được đoạn hook+ch1-2 (voice phần sau nằm track khác) — hook thở dày là tự nhiên.

- Hình trong ô (đo 003, §NHIP-NGHI): ô SÂU nhất đều **giữ hình cũ + J-cut 0,17–0,4s
  trước voice**; shot riêng chỉ ở ô trung bình (3/18); J-cut lead trung vị ~0,3s = đúng
  số đợt 1 đang dùng.

## 2. Vì sao thay khung (đợt 1+1.5 → 3.0)

Đợt 1+1.5 chọn **top-N điểm/phút** (1,9+1,9) và δ nhỏ (0,4–0,7 / 0,2–0,4) → Jupiter V3
có 25 điểm nghe ra ~0,9–1,3s, còn lại ~60 ranh giới câu đứng ở 0,5s. Editor: **một nửa
số câu là điểm dừng thật 1,3–1,9s, mệnh đề chọn lọc là nửa nhịp ~1s** — cái nền 0,5s
đều đều của ta chính là cảm giác "AI đọc liền mạch" user chấm ở cổng TAI. Khung mới:
**mọi ranh giới đủ khóa là ứng viên; mật độ và ĐỘ SÂU lấy từ phân bố DNA, không phải
hằng số bịa.**

## 3. Thiết kế SINH — máy thuần, 0 call NÃO (`cutter/pause.py` viết lại ruột)

**Nguồn số:** `pause_dna.json` đọc từ folder niche của thư viện (cạnh `dna.json`,
cùng pattern loader `library/dna.py`, **fail-open**: thiếu file → dùng hằng pooled
ghi trong code = chính bảng §1a).

**2 khóa an toàn GIỮ NGUYÊN** (bất di bất dịch): khóa dấu (theo script gốc trong
beat.text) + khóa nghỉ thật (alignment ≥0,3s). Giữa mệnh đề: máy KHÔNG BAO GIỜ tự chọn.

**Chọn điểm & lượng giãn (quantile-rank mapping):**
1. **Tầng câu:** ứng viên = ranh giới beat kết `.?!` đạt 2 khóa (Jupiter: 7,6/phút — dư).
   Chọn K_câu = round(phút × 4,9) điểm, ưu tiên nghỉ-nguồn-dài trước (giữ ngữ điệu voice).
   Điểm hạng r/K (theo nghỉ nguồn) nhận **target nghe-ra = quantile r tương ứng của
   phân bố kết câu DNA** (nội suy p10→p90: 1,06→2,73) → δ = target − nghỉ nguồn,
   clamp **[0,15 · 1,1]**. Trần 1,1 để gap timeline ≤1,2s — không giẫm vùng J-cut/ducking
   của tầng thở; phần sâu hơn thuộc tầng thở NÃO (§4).
2. **Tầng mệnh đề:** ứng viên = ranh giới beat kết `,;:—–` đạt 2 khóa. K_mđ =
   round(phút × 1,6), mapping lên phân bố mệnh đề (p10→p90: 0,66→1,39), δ clamp
   **[0,15 · 0,7]**.
3. **Guard:** 2 điểm được giãn cách nhau ≥3s (chống 2 câu cụt liền nhau cùng phồng);
   bỏ spacing 12s/6s cũ — mật độ giờ do K quản. Beat cuối + beat có breathing_after:
   vẫn loại. Trần tổng chèn (thở + giãn máy) = **15% × duration nguồn** — chạm trần
   thì bỏ điểm ưu tiên thấp. *(Chỉnh 13→15 sau run Jupiter: voice ta nghỉ nền nông
   hơn TTS editor ~0,35s/điểm nên cần chèn nhiều hơn editor trung vị để ĐẠT CÙNG mức
   nghe-ra; 13% bị tầng câu ăn hết → tầng mệnh đề chỉ còn 1/16 điểm. 15% vẫn trong
   khung editor 8,3–16,8%.)*
4. Cùng field `micro_pause_after` — cơ chế hạ nguồn (cắt giữa lặng, chèn gap, coverage,
   split_window) **không đổi**. RO_PER_MIN/CLAUSE_* (đợt 1/1.5) nghỉ hưu.

**Ước lượng Jupiter V4:** ~50 điểm câu (δ tb ~0,7) + ~16 mệnh đề (δ tb ~0,35) ≈ +41s
+ thở đạo diễn ~36s ≈ **+13% / video 599s → ~676s** — nằm trong khung editor.

## 4. Thiết kế NÃO — 2 quyết định nghĩa, +0 call (mở rộng schema call `direct` sẵn có)

**4a. Thở sâu có chủ đích** (= phương án A đã duyệt, số chốt theo DNA §1b):
- Foundation hình thở sửa hướng dẫn đạo diễn: ô thở **ít hơn nhưng sâu hơn** — mật độ
  đích ~0,7/phút (hiện 1,45), dải 1,5–6s (hiện 1,5–3), trong đó 1–2 ô/10 phút được
  phép 3,5–6s tại: **ranh giới chương (DNA: 12/14 chương có ô)** · sau mặc khải lớn ·
  sau câu mở hook · sau câu hỏi khán giả.
- Validator direct-ingest: trần breathing_after nâng lên 6,0s; Pydantic chặn >6.
- Hình trong ô sâu: cơ chế sẵn có (giữ hình + J-cut 0,3s) — ĐÚNG mẫu editor, không
  footage riêng (bằng chứng §1b).

**4b. Câu đinh** (chop tu từ — phiên bản beat-level, P2 tối giản):
- Director được đánh dấu ≤3 điểm/10 phút `rhetorical_pause` tại **ranh giới beat
  KHÔNG dấu** (loại beat hiện chiếm ~10/112, chưa bao giờ được giãn) — chỉ ở hook/kết/
  trước twist. Máy chỉ chấp nhận nếu nghỉ nguồn ≥0,3s; δ = clamp(1,0 − nghỉ, 0,2–0,6)
  (nghe ra ~0,9–1,2s theo DNA giữa-mệnh-đề).
- Chop word-level TRONG beat (như editor cắt "…house ‖ But one"): **KHÔNG làm đợt này**
  — đòi cutter cắt sub-beat, đụng coverage/overlay dây chuyền. Ghi backlog, mở nếu TAI đòi.

## 5. RÀ CHỒNG CHÉO (P5)

| Tầng cùng quản | Kết quả rà |
|---|---|
| **Ducking nhạc `MIN_BREATH=1.0`** | **NGƯỢC CHIỀU — phải sửa cùng lúc:** δ câu đại trà 0,5–1,1 → gap timeline 0,6–1,2s, nếu giữ 1.0 nhạc nở/nép theo TỪNG CÂU (phập phồng). **Nâng MIN_BREATH → 1,5**: micro tối đa 1,2 < 1,5 nuốt sạch ✓; mọi breathing đạo diễn ≥1,5 vẫn nở ✓. Hành vi nhạc editor tại ô thở chưa đo — backlog |
| **Cửa kỹ thuật phễu (`funnel.py:52,185` dùng `beat_dur` trần)** | **LỖ HỔNG SẴN CÓ, thở sâu khuếch đại:** clip phải phủ beat + thở + micro nhưng cửa chỉ so beat_dur. Sửa: `need_dur = beat_dur + breathing_after + micro_pause_after` (cut chạy TRƯỚC source nên số đã có) cho cả cửa loại lẫn DURATION_BONUS. Rà consumer: `funnel.py` 2 chỗ + `prompts.py` in duration — hành vi đổi CÓ CHỦ ĐÍCH, per-beat lẫn batch dùng chung `_finish_scoring` ✓ |
| J-cut (`J_CUT_MIN_BREATH=1.2` trên `breathing_dur`) | micro trần 1,1 (+0,1 assembler = 1,2 biên) nhưng J-cut chỉ đọc field breathing_dur — micro không bao giờ J-cut ✓ không đổi code. Ô thở sâu 3,5–6s: J-cut sẵn có áp luôn ✓ |
| split_window / coverage / total_end / segment cuối | cùng field micro/breathing → công thức đợt 1 tự đúng; segment cuối ép 0 giữ ✓ |
| Validator direct-ingest (trần breathing) | trần VỐN ĐÃ 1,5–6s sẵn (kiểm code khi làm — dự tính "nâng 3→6" sai) → chỉ sửa HƯỚNG DẪN đồng bộ 2 chỗ: schema.py description + live.py bảng ràng buộc (ít-sâu-đúng chương); thêm `MAX_RHETORICAL_PER_CHAPTER=1` cho câu đinh |
| Overlay/text/SFX/nhạc theo timeline | cursor điền lại sau cut ✓ ("ổ bug kinh điển" đã phòng M4); video dài +13% — nhạc loop/crossfade cơ chế sẵn ✓ |
| DNA validator Mảnh B (cpm, std shot) | video dài ra ~13%, số cut giữ → cpm giảm ~12% (Jupiter 10,5 → ~9,3, khung [4,7–18,8] ✓); std shot tăng nhẹ vì shot kéo qua điểm giãn — fail-open, quan sát run thật |
| Luật đợt 1+1.5 (docstring pause.py, MO_TA_2, test) | khung top-N nghỉ hưu — sửa docstring + đánh dấu MO_TA_2 superseded + viết lại test theo khung mới; **regression bất biến giữ nguyên Ý: giữa mệnh đề không dấu máy KHÔNG BAO GIỜ tự giãn** (câu đinh phải qua NÃO + validator) |
| Chạy lại stage cut | plan mới vẫn pure + deterministic (mapping theo rank, không random); ghi đè toàn bộ field mỗi lần ✓ |
| Máy khác/kênh khác thiếu pause_dna.json | loader fail-open → hằng pooled trong code (bảng §1a) — pipeline không bao giờ chết vì thiếu DNA |

## 6. Cổng kiểm (P4)

- **pytest:** mapping đúng quantile + K theo phút · caps δ/tổng-chèn · guard 3s ·
  2 khóa giữ (regression: không dấu + lặng dài → máy không giãn) · câu đinh cần cả
  cờ NÃO lẫn nghỉ nguồn · ducking ngưỡng mới · funnel cộng breathing+micro ·
  deterministic · FULL suite.
- **Cổng số (chạy lại Jupiter → V5):** phân bố nghe-ra tại ranh giới câu của draft:
  p50 ∈ [1,3–1,8] · mật độ điểm dừng máy ≥1,0s ≈ 4,5–5,5/phút · tổng chèn +8–15% ·
  0 điểm giãn máy tại ranh giới không dấu. Số in ra log cut + report.
  **KẾT QUẢ 2026-07-08: ĐẠT** — 49 câu + 13 mệnh đề (+52,8s máy): nghe-ra câu
  p25/50/75 = 1,29/**1,55**/1,74 (DNA editor 1,28/1,55/1,90 — p50 trùng từng số) ·
  mệnh đề p50 0,95 = DNA · dừng máy ≥1s 5,4/phút · tổng +14,3% · 0 điểm không dấu ·
  78/78 segment draft khớp plan. (Tổng mật độ 6,9/phút hơi dày hơn editor ~6,4 vì 15
  ô thở direct CŨ còn dày 1,45/phút — hướng dẫn mới chỉ áp cho video direct sau.)
- **Cổng TAI user:** V4 vs V3 vs bản gốc editor. Claude KHÔNG tự phán đạt.

## 7. Không làm đợt này (backlog d2/hình thở)

1. Chop word-level trong beat ("But one") — nếu TAI đòi.
2. Shot riêng đầu ô trung bình (3/18) + chuỗi trình chiếu — đợt 2 cũ.
3. Nâng sàn nghỉ các câu KHÔNG được chọn (~0,85s editor-uncut vs 0,5s ta) — cân nhắc
   sau khi nghe V4 (đắt: +nhiều giây, có thể ì).
4. Đo hành vi NHẠC editor tại ô thở (ducking DNA).
5. Pacing knob per-channel/per-video (C) — chờ DNA kho 100 video; RO/K densities khi
   đó đọc theo niche.
