# A3 — OPEN LOOP & CALLBACK/MOTIF (gieo — giữ — gặt bằng hình ảnh)

> **Vị trí:** kỹ năng giữ chân cấp TOÀN VIDEO — làm việc trên các chương/vai mà
> [[a1-chia-beat-chuong]] + [[a2-chuc-nang-doan]] đã chia. Phần hình ảnh (motif/callback)
> ăn khớp với luật chuỗi [[c3-ngu-canh-chuoi]] và là NGOẠI LỆ có chủ đích của luật
> chống-lặp P7. Không có nguyên văn user riêng — chưng cất từ FOUNDATION.md cũ (§2.4, §6.2)
> + code thật. **Trạng thái phần 3: DỰ KIẾN 🔸.**

---

## 1. Là gì

Hai kỹ thuật cùng một bản chất "gieo trước — gặt sau":

- **Open loop (thuộc SCRIPT):** gieo một câu hỏi/lời hứa đầu video ("cuối video bạn sẽ
  biết vì sao..."), trả lời ở cuối → khán giả ở lại. **Tool không viết script** — việc
  của tool là NHẬN DIỆN loop trong script để dựng đúng: (1) KHÔNG spoil bằng hình ảnh
  trước khi voice đóng loop; (2) khi loop ĐÓNG, đó chính là payoff lớn → dồn đồ đắt
  (thở, footage mạnh, nhấn nhạc — theo [[a2-chuc-nang-doan]]).
- **Motif & callback (thuộc EDIT — việc của tool):** một hình ảnh lặp lại CÓ CHỦ ĐÍCH
  xuyên video (đồng hồ, con đường, bàn tay) tạo tính thống nhất; callback = gọi lại đúng
  hình đầu video khi voice chạm lại ý cũ. Lặp có chủ đích ≠ lặp footage do lười — một cái
  là chữ ký nghệ thuật, cái kia là lỗi P7.

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Script có loop hay không** | Script không gieo thì tool không có gì để gặt — không ép. Nhận diện loop là việc đọc-hiểu của NÃO lúc pass 1. |
| **Motif phải CỤ THỂ quay được** | "sự tự do" không phải motif; "cánh chim trên biển" là motif. Motif trừu tượng → không tìm được footage lặp. |
| **Khoảng cách gieo–gặt** | Callback quá gần = khán giả chưa quên chưa có hiệu ứng; quá xa (video ngắn không sao, video dài cần nhắc lại giữa chừng). |
| **Kuleshov ([[c3-ngu-canh-chuoi]])** | Hình callback đứng cạnh voice MỚI → nghĩa MỚI — đó chính là cái hay: cùng hình, lần 2 mang nghĩa khác. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

### Hiện trạng code

- **Motif ĐÃ CHẠY nửa đường:** pass 1 chọn 1–3 motif xuyên video (`Outline.motifs`);
  pass 2 được lệnh "reuse the video motifs intentionally where they fit" → motif sống
  trong `visual_concept` của beat. NHƯNG xuống phễu, mỗi beat tìm footage ĐỘC LẬP →
  hai beat cùng motif "cánh chim" có thể ra hai clip chim KHÁC nhau — motif về Ý có,
  motif về HÌNH chưa chắc.
- **Callback đúng nghĩa (lặp CHÍNH footage đó) hiện BỊ CHẶN:** luật cứng P7
  `used_in_video` cấm một asset xuất hiện 2 lần trong video — đúng cho 99% trường hợp
  (chống lặp do lười), nhưng chặn luôn callback chủ đích.

### Hướng dự kiến 🔸 (KHÔNG code đợt này — đợi L2b sâu)

1. Motif-về-hình: khi NÃO chấm phễu (B3) đã có input "footage beat N−1" — mở rộng tự
   nhiên khi L2b sâu: beat mang motif thì nhắc NÃO "motif X đã dùng clip Y" để chấm
   ứng viên giống-Y cao hơn. Là TINH CHỈNH đầu chấm nghĩa (backlog #2 c5), không mở mục.
2. Callback: cho phép NÃO đánh dấu `callback` → sourcer TÁI DÙNG asset cũ (bỏ qua
   used_in_video cho đúng 1 lần đó, có log). Chỉ mở khi có video thật cần — giữ P7
   nguyên vẹn tới lúc đó.

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Chọn 1–3 motif xuyên video, cụ thể quay được | pass 1 `Outline.motifs` + pass 2 reuse | (a)+(c) | ✅ đã có (mức Ý) |
| Nhận diện open loop trong script, không spoil, dồn đồ đắt lúc đóng loop | NÃO đọc script pass 1 (đã đọc TOÀN văn) — thể hiện qua concept/thở/anchor, không cần field mới | (c) | 🔸 chạy ngầm qua prompt; dạy tường minh ở L2b sâu |
| Motif về HÌNH (các beat cùng motif ra footage đồng nhất) | tinh đầu chấm nghĩa phễu (thêm ngữ cảnh motif→clip đã dùng) | (b nhỏ, gộp backlog #2 c5) | ❌ đợi L2b sâu — KHÔNG mở mục mới |
| Callback lặp đúng footage cũ (ngoại lệ P7 có chủ đích) | cờ callback từ NÃO → sourcer tái dùng asset, ghi log | (b treo) | ⏸ chủ động CHƯA làm — P7 giữ nguyên tới khi có video thật cần |
| Niche nào hay gieo–gặt kiểu gì | đo từ video viral | (d) | ❌ Phase B |

**→ Backlog code rút ra: KHÔNG mở mục mới đợt này.** Hai việc (b) đều treo có chủ đích.

## 4. Cạm bẫy / ranh giới

- **Lặp footage do lười đội lốt "motif".** Motif là 1–3 hình được CHỌN từ pass 1 và ghi
  trong outline; lặp ngoài danh sách đó là lỗi P7, không phải nghệ thuật.
- **Spoil hình ảnh.** Script đang giấu twist mà footage đã chiếu đáp án (vd script úp mở
  "sinh vật bí ẩn", hình đã cho xem con mực khổng lồ) → loop chết. Beat trong vùng
  loop-đang-mở thiên associative/generic, giữ miếng cho lúc đóng.
- **Ép motif vào mọi video.** Video facts 60s không cần motif; ép = gượng. Motifs rỗng
  là output hợp lệ của pass 1.
- **Phá P7 tràn lan nhân danh callback.** Callback là ngoại lệ CÓ ĐÁNH DẤU, mỗi video
  nhiều nhất 1–2 lần; không thành cửa sau cho lặp footage.

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Video viral niche có dùng motif/callback không, mật độ bao nhiêu | quyết có dạy L2b dùng đậm hay bỏ qua |
| Loại motif điển hình của niche (space: trái đất từ xa; deepsea: ánh đèn trong bóng tối) | mồi danh sách motif cho pass 1 |
| Khoảng cách gieo–gặt điển hình | luật đặt callback theo độ dài video |
