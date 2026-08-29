# B3 — PATTERN INTERRUPT (phá khuôn định kỳ để giữ retention)

> **Vị trí:** luật NHỊP PHÂN BỔ cấp toàn video — KHÔNG phải một hiệu ứng mới. Nó điều phối
> các công cụ ĐÃ CÓ (overlay, chart, kinetic text, hình thở, đổi nhạc, multi-shot) sao cho
> không có khúc nào "phẳng" quá lâu. Anh em ruột với [[d1-pacing]] (pacing = đường sóng
> năng lượng; interrupt = mốc sự kiện trên đường sóng đó). Không có nguyên văn user riêng —
> chưng cất từ FOUNDATION.md cũ (§4.3). **Trạng thái phần 3: DỰ KIẾN 🔸.**

---

## 1. Là gì

Não người quen khuôn rất nhanh: xem ~30–60 giây cùng một kiểu trình bày (voice + footage
đều đều) là bắt đầu trôi. **Pattern interrupt = mỗi 30–60s có MỘT thứ phá khuôn:** một
con số nảy lên (overlay), một chart, chữ kinetic, một khoảng thở + ambient, đổi bài nhạc,
một chuỗi cắt nhanh (multi-shot), một khoảng IM LẶNG đột ngột. Khuôn bị phá → não tỉnh
lại → retention giữ được.

Điểm cốt lõi: **interrupt chỉ có tác dụng khi có PATTERN để phá.** Video nhồi hiệu ứng
liên tục thì không còn khuôn — mọi thứ đều "đặc biệt" nghĩa là không gì đặc biệt. Tiết chế
giữa các interrupt chính là thứ làm interrupt mạnh.

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Mật độ sự kiện hiện có** | Đoạn đã dày overlay/chart thì KHÔNG cần thêm; đoạn dài chỉ voice+footage đều mới là chỗ cần interrupt. |
| **Vai đoạn ([[a2-chuc-nang-doan]])** | Hook tự nó dày sự kiện; đoạn thân giải thích dài là vùng nguy hiểm nhất — thường 60s+ không có gì. |
| **Mood ([[b1-mood-tone]])** | Interrupt phải CÙNG tone: video trầm dùng thở + im lặng + đổi nhạc; không dùng hiệu ứng giật meme vào video nghiêm túc. |
| **Loại interrupt sẵn có trong kho** | Tool hiện có: overlay/kinetic/chart/info-card/thở/đổi-nhạc-chương/multi-shot/SFX. Không bịa loại mới. |
| **Niche** | Nhịp interrupt mỗi niche một khác (facts dày, chill travel thưa — khoảng thở CHÍNH LÀ interrupt của niche chill) → DNA. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

### Nhận thức quan trọng: tool ĐÃ có đủ "vũ khí" interrupt, chỉ thiếu CÁI NHÌN TỔNG

Từng công cụ đã có luật tiết chế RIÊNG (overlay ~1/8–12s nói, chart ≤1/60s, thở theo vai
chương, nhạc đổi theo chương, multi-shot theo shot_count). Cái CHƯA ai nhìn: **hợp các sự
kiện lại trên trục thời gian, có khúc nào >60s trống trơn không?** — và ngược lại, có khúc
nào 3 sự kiện chen nhau 5 giây không?

### Luồng dự kiến 🔸

1. **Lúc DIRECT (NÃO):** khi chia beat + gán overlay/thở/chart, NÃO giữ ý thức nhịp sự
   kiện — không dồn hết đồ chơi vào một chỗ, không để chương giải-thích-dài trống trơn.
   (L2b sâu đọc chính file này.)
2. **Lúc VALIDATE (máy, cảnh báo — KHÔNG cửa loại):** gom mốc thời gian mọi sự kiện đã
   quyết (overlay, chart, info-card, kinetic, thở, ranh giới chương=đổi nhạc, beat
   multi-shot) → quét: (i) khoảng trống > ~60s → cảnh báo "đoạn X–Y phẳng, cân nhắc
   1 interrupt"; (ii) ≥3 sự kiện trong ~5s → cảnh báo "chen chúc". Editor/NÃO tự quyết,
   máy không tự thêm bớt.

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Các LOẠI interrupt | overlay+SFX (`overlay/style.py`), chart, info-card, kinetic, thở, đổi nhạc theo chương (crossfade), multi-shot (F6) | (a) | ✅ đủ vũ khí — KHÔNG bịa loại mới |
| Tiết chế từng loại | luật prompt + `check_overlay_density`, `check_graphic_ratio`, `check_breathing_rhythm` | (a) | ✅ đã có (rời rạc) |
| Đặt interrupt ĐÚNG CHỖ, cùng tone | NÃO lúc direct (đọc file này ở L2b sâu) | (c) | 🔸 chạy ngầm qua các luật rời; dạy tường minh sau |
| **Quét nhịp TỔNG trên timeline (trống >60s / chen <5s) — cảnh báo** | GỘP vào **pacing validator** (backlog d1 đã mở) — thêm 1 phép quét sự kiện, không mở mục riêng | (b, gộp d1) | ❌ làm cùng pacing validator |
| Nhịp interrupt theo niche (facts dày, chill thưa) | số DNA → ngưỡng quét + mồi prompt | (d) | ❌ Phase B |

**→ Backlog code rút ra: KHÔNG mở mục mới** — phép quét nhịp tổng nhập vào pacing
validator (d1). Đây là ví dụ chuẩn của [[filter-overload-guard]]: foundation mới chỉ
thêm 1 cảnh báo đọc-cho-người, không thêm cửa loại/luật chấm nào vào phễu.

## 4. Cạm bẫy / ranh giới

- **Nhồi hiệu ứng = phá luôn khái niệm interrupt.** Không còn khuôn thì không có gì để
  phá; video thành TikTok loạn. Tiết chế là một nửa của kỹ thuật này.
- **Interrupt lệch tone** — chèn glitch/meme vào video tâm sự = giả trân (lỗi chết người
  của [[b1-mood-tone]]). Kho interrupt phải lọc theo tone video trước.
- **Đếm cơ học "cứ 45s bỏ 1 cái".** 30–60s là khoảng THAM CHIẾU, không phải lịch trình.
  Interrupt đặt theo Ý (sau ý nặng, chỗ chuyển) — con số chỉ để phát hiện đoạn bị bỏ quên.
- **Máy tự thêm interrupt.** Validator chỉ CẢNH BÁO; quyết định thêm gì vào đâu là của
  NÃO/editor. Máy tự chèn = mất kiểm soát tone.

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Khoảng cách trung bình giữa các "sự kiện" trong video viral niche | ngưỡng quét (60s chỉ là khởi điểm) |
| Loại interrupt niche ưa dùng (facts: overlay số; chill: thở+ambient; science: chart) | mồi cho NÃO chọn đúng vũ khí |
| Interrupt ở phút thứ mấy thì retention gãy (đọc retention graph nếu có) | tinh vị trí đặt theo dữ liệu thật |
