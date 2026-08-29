# E2 — CHUYỂN FOOTAGE THEO PHÁCH (lưới nhịp cho vùng không voice)

> **Vị trí:** lớp con của [[e1-sound-design-nhac]] — khi footage phải "nhảy theo nhạc"
> (đoạn chèn Δ, mini-hook, ô thở có nhạc mạnh). Ăn khớp: [[d1-pacing]] (nhịp dựng),
> [[d3-loai-cat-transition]] (mép cắt). User chốt nguyên văn 2026-07-21 sau 4 phiên
> M4 nhịp chưa đạt tai (bàn giao `BAN_GIAO_M4_NHIP_DANG_DO.md`).
> **Trạng thái: ĐÃ CHỐT — đang chờ cổng tai V11 xác nhận lần đầu.**

---

## 1. Là gì (nguyên văn user, 2026-07-21)

> "bài có 4 ô nhịp thì thường editor sẽ chuyển footage ở nhịp 1 và 3. còn nếu bài có
> 3 ô nhịp, thì editor sẽ chuyển vào các ô nhịp 1. lặp đi lặp lại như vậy. editor sẽ
> chuyển vào các phách lẻ (phách mạnh thường là phách lẻ)."

| Loại nhịp | Chuyển footage tại | Bước lưới cơ bản |
|---|---|---|
| **4/4** (4 phách/ô) | phách **1 và 3** mỗi ô | nửa ô nhịp (2 phách) |
| **3/4** (3 phách/ô) | phách **1** mỗi ô | 1 ô nhịp (3 phách) |

**Luật phách LẺ:** không bao giờ cắt vào phách chẵn/phách nhẹ. Bước lưới được phép
nhân BỘI SỐ khi shot quá ngắn (sàn 1,5s) — mọi bội của nửa-bar vẫn rơi phách 1/3,
mọi bội của bar vẫn rơi phách 1 → thưa hơn nhưng không bao giờ phá luật.

## 2. Mốc thời gian tính bằng CÔNG THỨC, không cộng dồn beat đo

Foundation toán (user đưa 2026-07-21, phiên bàn phương pháp luận):

```
Bar_Duration = (60 / BPM) × số_phách_mỗi_ô
mốc[n]       = Offset + n × bước        (bước = Bar hoặc Bar/2 theo bảng trên)
```

3 biến cần: **BPM** · **số phách/ô (meter 3|4)** · **Offset** (giây phách "1" đầu tiên).

**VÌ SAO không dùng thẳng beat librosa:** beat_times librosa dao động ~46ms (làm tròn
khung phân tích) → cắt "mỗi k beat" là CỘNG DỒN sai số, mép trôi dần khỏi nhịp — đây
chính là lỗi tai user nghe suốt V6–V10 (GT1). Lưới công thức đều tuyệt đối, không trôi.

## 3. Ai đo 3 biến — madmom, không phải librosa

| Biến | Công cụ | Vì sao |
|---|---|---|
| Offset (pha) + danh sách downbeat | **madmom** RNN (`analyze_downbeats`) | librosa MÙ pha; hàm cũ nhóm cứng 4 beat → sai toàn bộ trên bài nhịp 3. madmom học từ data thật, kháng phách nghịch/trống nhẹ |
| meter 3\|4 | **madmom** (`beats_per_bar=[3,4]`) | librosa không trả time signature |
| BPM/Bar | trung vị khoảng cách downbeat madmom | trung vị chống jitter đo |

Đo thật "Romeo - End of an Era": meter 3, 68 downbeat, bar 2,000s, BPM 90 — khớp
target 2,0s/hình user chốt (1 hình = 1 ô nhịp).

**Phân vai chuẩn: madmom lo PHA, công thức lo LƯỚI.** Không tầng nào tự đoán.

## 4. Nơi luật này sống trong code

- `music/analyze.py::analyze_downbeats` — đo madmom (gọi 1 lần lúc khai Δ, ~10-30s).
- `project.py::InsertSpec.music_downbeats/music_meter` — lưu kết quả đo.
- `packager/coverage.py::insert_grid_cuts` — nhánh lưới công thức (có downbeats+meter)
  / fallback lưới librosa cũ (project cũ, madmom lỗi) — fail-open, không chặn dựng.
- Cài đặt madmom (cần MSVC): `HUONG_DAN_CAI_DAT_MAY_EDITOR.md` mục madmom.

## 5. A′ — SHUFFLE thời lượng: RUN + HOLD (user gật 2026-07-21)

User nghe V11 (lưới đều 2,0s): *"các footage đang khá đều nhau, tôi muốn nhịp chuyển có
shuffle hơn — random thời lượng, có footage dài, có footage ngắn, vẫn chuyển vào phách
1 và 3"*. Nghiên cứu craft editor giỏi (nguồn dưới) → **không random trần, mà "biến
thiên có chủ đích"**:

> "Ba nhát cắt nhanh tạo năng lượng, giữ MỘT hình đã mắt, quay lại cắt nhanh" —
> pattern trước, phá pattern sau, trả thưởng. Cả đoạn có HÌNH DẠNG: nhanh lúc vào,
> giữ ở giữa, siết về cuối.

**Ngữ pháp máy (mã hóa ở `coverage._shaped_pattern`):**
- Thời lượng shot = BỘI của unit lưới (unit = bar nhịp 3 / nửa-bar nhịp 4) → mọi mốc
  vẫn phách LẺ, lưới vẫn công thức 0ms — A′ chỉ quyết MỖI SHOT MẤY UNIT.
- **RUN** = 2-4 shot 1-unit liên tiếp (theo pace) · **HOLD** = 1 shot 2-unit (1 lần/Δ
  được 3-unit nếu Δ ≥12 unit) · giữa 2 HOLD luôn ≥2 RUN · **mở và KẾT Δ bằng RUN**
  (siết nhịp dồn về lúc voice quay lại) · HOLD ưu tiên đầu nhóm 4 ô nhịp (~đầu câu
  nhạc, đệm ≤2 RUN để tới ranh giới).
- **Seed cố định** crc32(beat, tên bài) → dựng lại Y HỆT; `insert --shuffle-seed N`
  đổi cách xáo; `--pace fast|medium|slow` chỉnh mật độ hold (editor biết nhạc+nội dung).
- **Nội dung hình do editor**: ô HOLD dùng ảnh slug RIÊNG "HOLD — CẢNH RỘNG/NHIỀU CHI
  TIẾT" (craft: hình dài cần cảnh đáng ngắm; hình ngắn = cận/chi tiết).

Nguồn craft: LBB "More than just cutting to the beat" · SoundOnSound "Video Editing —
Music Promos" · StudioBinder (Murch: nhịp = 70% editing) · darkskiesfilm (thời lượng
theo lượng thông tin trong hình).

## 6. Rà chồng chéo (P5)

- **Mép Δ miễn snap/J-cut (M2)**: giữ nguyên — lưới chỉ chẻ BÊN TRONG Δ, 2 mép ngoài
  vẫn theo luật M2. Không ngược chiều.
- **`_meter_k` + `beat_grid` (mini-hook/M1/ô thở)**: vẫn dùng lưới beat librosa —
  CHƯA áp foundation này (chỗ đó có voice/ô ngắn, khác bài toán). Khi nào nghe lệch
  mới port, đừng sửa trước (P2).
- **`timeline_accents/timeline_beats` chưa biết span Δ** (tồn đọng M3 #1): không đụng —
  mép Δ vẫn miễn snap nên chưa hại.
- **Hai hệ cắt KHÔNG trộn** (luật đứng M4): voice = NGHĨA, không-voice = NHỊP — foundation
  này chỉ áp vùng KHÔNG voice. Không đổi.
