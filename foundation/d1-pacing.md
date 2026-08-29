# D1 — PACING (TIẾT TẤU) — foundation TRÙM nhóm nhịp

> **Vị trí:** foundation trùm, đã nuốt: B2 (đường cong năng lượng) + D1 cũ (độ dài shot) +
> quyết định "cắt tại chỗ nghỉ voice". **[[d2-hinh-tho]] là MỘT PHẦN của pacing** nhưng đứng
> file riêng vì có bộ tín hiệu DNA riêng. Liên quan: [[b1-mood-tone]] (pacing là 1 trong 5
> tầng tạo mood) · [[c7-shot-variety]] (đa dạng cỡ cảnh tự nó tạo nhịp).
> **Trạng thái phần 3: DỰ KIẾN 🔸 — user duyệt mô tả vận hành rồi mới code phần thiếu.**
> Nguyên văn lời user: `GHI_CHEP_GOC.md §1`.

---

## 1. Là gì

Pacing = **tốc độ thông tin/cảm xúc trôi qua theo thời gian**. Hai tầng:
- **Macro-pacing** — nhịp toàn video: khi nào dồn dập, khi nào chậm lại. Hình dạng chuẩn là
  **đường sóng dồn → thả → dồn**, không bao giờ phẳng: hook nhanh, thân lên-xuống theo từng ý,
  lặng trước cao trào, cao trào dày đặc, kết thả lỏng.
- **Micro-pacing** — độ dài từng cut/shot bên trong đoạn.

Pacing KHÔNG phải "cắt càng nhanh càng hay". Nó là **tương phản**: đoạn leo núi cắt 0.5-1s/shot
tạo năng lượng, lên tới đỉnh hold một toàn cảnh 5–6 giây voice im — chính tương phản chậm/nhanh
làm khoảnh khắc đỉnh "đắt". Không có tương phản = không có pacing.

## 2. Yếu tố ảnh hưởng

| Yếu tố | Tác động lên pacing |
|---|---|
| **Sức nặng của ý** (thông tin nặng/cảm xúc vs liệt kê/chuyển) | nặng → chậm cho thấm; liệt kê/chuyển → nhanh |
| **Chức năng đoạn** (hook / thân / cao trào / kết) | hook nhanh · thân lượn sóng · trước cao trào lặng · cao trào dày · kết thả |
| **Độ giàu nghĩa của footage** | nguyên tắc vàng: **mỗi cut phải có lý do biến mất** — hình còn thông tin thì giữ, cạn nghĩa thì cắt |
| **Năng lượng đoạn (energy)** | độ dài beat/shot tỉ lệ NGHỊCH với energy |
| **Nhịp voice** (chỗ nghỉ, dấu câu) | điểm cắt phải rơi vào chỗ nghỉ tự nhiên của voice — nhưng KHÔNG phải cứ hết câu là chuyển cảnh |
| **DNA niche** | mỗi niche có "chữ ký pacing" riêng — phải xem trước khi dựng (phần 5) |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN, chờ user duyệt

> 📌 **CẬP NHẬT 2026-07-14 — TEMPO MAP đã code (user duyệt, feedback đạo diễn hình ảnh):**
> outline PHẢI khai `tempo_curve` mỗi chương — menu: `fast_settle` (hook — luật hook nhanh
> THẮNG, không mở chậm chương 1) · `slow_build_slow` (thân) · `build` (dẫn cao trào) ·
> `dense` (cao trào) · `calm` (kết/lặng). SHUFFLE: không 3 chương liền kề cùng curve;
> ≥4 chương → ≥3 loại. Nhanh/chậm TƯƠNG ĐỐI quanh trung vị DNA niche (phần 5).
> Máy gác warning-only tại direct-ingest: tempo phẳng giữa chương / chương đều tăm tắp /
> khai-vs-thực. Luật đầy đủ tự in trong `direct_context.md` (block TEMPO MAP);
> fan-out phải kèm dòng tempo mỗi chương (SKILL). `MO_TA_VAN_HANH_TEMPO_MAP.md`.

### Ai quyết cái gì (tách ỐNG/NÃO, NT4)

- **NÃO quyết Ý NGHĨA** (không bao giờ sinh timestamp): ranh giới chương/beat theo **word
  index**, `energy` mỗi chương/beat, `shot_count` mỗi beat, `breathing_after` (giây thở —
  chi tiết ở [[d2-hinh-tho]]).
- **ỐNG tính THỜI GIAN**: word index → giây qua alignment (`Word.start/end`), snap mép cắt
  vào khoảng lặng thật, chia cửa sổ shot, ráp draft.

### Luồng chạy dự kiến (end-to-end)

1. **Nạp tri thức trước khi direct:** file foundation này + (khi có, Phase B) hồ sơ DNA
   niche với các con số pacing của niche (phần 5).
2. **Direct pass 1 — chương (macro):** NÃO chia chương, gán `energy/mood` theo hình đường
   sóng. *Đã chạy hôm nay* bằng luật cứng trong `director/prompts.py` ("Pacing must form a
   wave, never flat..."); khi L2b sâu, luật chuyển về file này để editor sửa được bằng lời.
3. **Direct pass 2 — beat (micro):** NÃO chia beat 2–8s theo word index, độ dài nghịch với
   energy; quyết `shot_count` (1 bình thường; 2–3 khi beat dài + đoạn dồn dập); ranh giới
   beat/thở CHỈ đặt ở từ kết thúc mệnh đề (dấu `. ? ! : —`) — *không phải cứ hết câu là cắt:
   chỉ cắt khi hình cạn nghĩa hoặc cần nhịp*.
4. **Cut (ỐNG):** word index → giây; snap mỗi mép cắt vào giữa khoảng lặng gần nhất trong
   ±200ms (`cutter/silence.py`, ffmpeg silencedetect −35dB/≥0.15s) — chống cắt cụt từ.
5. **Source + Assemble (ỐNG):** với beat `shot_count = n > 1` → lấy n footage (hoặc 1 footage
   cắt n khúc), assembler chia cửa sổ beat thành n đoạn micro-second (dùng `round()`, bài học
   [[assemble-segment-overlap-rounding]]). **← ĐÂY LÀ PHẦN CHƯA CÓ, xem 3b.**
6. **Kiểm pacing sau dựng:** thống kê độ dài shot toàn video → cảnh báo "pacing đều" (độ
   lệch chuẩn quá thấp = cắt đều tăm tắp) trong report. **← CHƯA CÓ, code nhỏ.**

### 3b. PHÂN RÃ NĂNG LỰC — từng câu foundation → tool cần gì

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật (ngôn ngữ editor) | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Đường sóng dồn→thả→dồn toàn video | NÃO gán energy khi chia chương theo luật foundation | (c) | ✅ đã có (prompt pass 1) |
| Ý nặng → chậm; liệt kê/chuyển → nhanh | độ dài beat tỉ lệ nghịch energy, NÃO quyết word index | (c) | ✅ đã có (prompt pass 2) |
| Điểm cắt rơi vào chỗ nghỉ voice, không cắt cụt từ | NÃO đặt ranh giới ở từ có dấu câu + ỐNG snap lặng ±200ms | (a) | ✅ đã có (`prompts.py` + `cutter/silence.py`) |
| Không phải cứ hết câu là chuyển cảnh | NÃO chỉ tách beat khi hình cạn nghĩa/cần nhịp, không tách máy móc theo câu | (c) | 🔸 luật viết ở đây, kiểm khi L2b sâu |
| **Cut nhanh 0.5–1s/shot ở đoạn dồn dập** | `shot_count` n>1 → sourcer lấy n footage + assembler chia beat thành n cửa sổ | **(b)** | ❌ **CHƯA CÓ — tính năng code LỚN NHẤT của pacing.** Hiện `shot_count` được LLM quyết nhưng sourcer/assembler bỏ qua: luôn 1 footage phủ nguyên beat |
| Mỗi cut phải có lý do biến mất (hình cạn nghĩa mới cắt) | NÃO đánh giá độ giàu nghĩa của visual_concept so với thoại khi quyết shot_count/độ dài | (c) | 🔸 dự kiến — luật định tính, Level 2 editor kiểm bằng mắt |
| Không cắt đều tăm tắp (pacing đều = không có pacing) | validator thống kê phân bố độ dài shot sau direct/assemble, cảnh báo nếu độ lệch chuẩn < ngưỡng | (b)+(d) | ❌ chưa có — code thống kê nhỏ; ngưỡng lấy từ DNA niche |
| Hold toàn cảnh 5–6s voice im ở khoảnh khắc đỉnh | = hình thở, cơ chế `breathing_after` | (a) | ✅ cơ chế có sẵn — chi tiết [[d2-hinh-tho]] |
| Xem DNA niche trước khi dựng | nạp hồ sơ pacing của niche vào bước direct | (d) | ❌ Phase B |

**→ Backlog code rút ra từ bảng (mỗi mục sẽ có bản mô tả vận hành riêng để user duyệt trước khi code):**
1. **Thực thi `shot_count`** — sourcer lấy n footage/beat + assembler chia cửa sổ (tính năng lớn, đụng 2 stage).
2. **Pacing validator** — thống kê độ dài shot + cảnh báo đều (code nhỏ, chỉ đọc project.json).

## 4. Cạm bẫy / ranh giới

- **Cắt đều tăm tắp** (mọi shot ~2s) — lỗi phổ biến nhất của editor mới: khán giả mệt và tê,
  mất cảm giác nhấn nhá.
- **Cắt máy móc theo dấu câu** — hết câu không đồng nghĩa phải chuyển cảnh; hình còn nghĩa thì giữ.
- **Nhầm pacing = tốc độ** — pacing là TƯƠNG PHẢN; toàn video nhanh cũng phẳng như toàn video chậm.
- **Beat thở rơi giữa mệnh đề** — chèn im lặng giữa cụm từ ("không ngừng | tăng") nghe như lỗi;
  ranh giới thở bắt buộc ở từ kết câu/mệnh đề.
- **Ranh giới với [[d2-hinh-tho]]:** pacing quyết NHỊP chung và CHỖ chậm lại; hình thở là kỹ
  thuật cụ thể "voice im + hình chạy" với luật chọn footage riêng — đọc file đó khi đặt khoảng thở.

## 5. Học gì từ DNA niche (Phase B)

Trước khi dựng một niche, hệ thống phải có **chữ ký pacing của niche** học từ (i) project cũ
của editor công ty (đọc draft → độ dài segment thật) và (ii) video viral đối thủ (tách cảnh →
độ dài cảnh). Tín hiệu cần trích:

| Tín hiệu | Dùng để |
|---|---|
| Phân bố độ dài shot **theo chức năng đoạn** (hook / thân / cao trào / kết) | NÃO chọn độ dài beat + shot_count đúng chuẩn niche |
| Mật độ cắt theo phút + độ lệch chuẩn độ dài shot | ngưỡng cảnh báo "đều quá" / "dày quá" của validator |
| Vị trí & độ dài các cú hold (shot ≥4–5s) | biết niche này hold ở đâu, dài bao nhiêu |
| Tỉ lệ đoạn nhanh/chậm toàn video (hình dạng đường sóng) | vẽ energy curve chuẩn niche cho pass 1 |

Schema tag cảnh (Phase B) phục vụ pacing: **độ dài cảnh + vị trí trong video + chức năng đoạn
ước lượng**. (Cỡ cảnh + góc máy cũng bắt buộc nhưng thuộc [[c7-shot-variety]].)
