# Ngân sách và bảng phân clip (luật 7–9, Spec 40 C)

Đọc ở bước dàn ý của skill `/bien-kich`, cùng `phan-canh.md` (luật 1–6, loại clip). Viết bảng phân clip **trước khi viết cảnh**, khớp ngân sách, lệch dưới 10%; dư thì cắt theo luật 9 ngay trên bảng. Kiểm: `python cong-cu/dem_phan_canh.py kich-ban/00-nhip.md` (chưa có cảnh thì máy đếm theo bảng).

**7. Ngân sách clip.** Cả phim khoảng **6 clip mỗi phút** độ dài đề bài ("Dài: N phút"), chia theo % từng hồi ở mục Ba hồi. Lệch quá 20% thì máy cảnh báo.
- **Phim `Clip: 30s`** (dòng đầu `00-nhip.md`; luật cảnh ở `phan-canh-30s.md`): mọi số clip ở luật 7–8 tính bằng **đơn vị 15 giây** (cảnh 30s = 2, cảnh 10s hay 15s = 1). Ngân sách **4,5 đơn vị mỗi phút** (khoảng 2,25 cảnh 30s; phim 30 phút khoảng 68 cảnh): phần dư chỉ để cắt đầu, đuôi shot, không để bù clip hỏng (clip hỏng thì Tách cảnh chạy Seedvis).
- Chia trong hồi theo mức: mức 1–2 khoảng 1–2 clip, mức 3 khoảng 2–3, mức 4–5 khoảng 3–5 (kể cả `lớn`, `sau đỉnh`); nhịp có khoảnh khắc chạm tính như mức 4–5; cú lật lớn nhất và `nối` tính thêm. Nhịp nào cũng có ít nhất một clip.
- Cắt cho vừa ngân sách ở đoạn yên (luật 9), không cắt ở khoảnh khắc chạm và cú lật. Còn dưới ngân sách thì dành phần dư cho hai chỗ này trước.

**8. Bảng phân clip.** Trong `00-nhip.md` mục `## Bảng phân clip` ngay sau bảng nhịp; khi viết riêng một hồi thì đặt ở đầu file hồi, trước `# Hồi n`.

```
## Bảng phân clip
Ngân sách hồi 2: 6 × 20 × 50% = 60; bảng: 58.
| Nhịp | Mức | Việc | Clip theo loại | Điểm chạm và thủ pháp | Lý do vượt trần |
|---|---|---|---|---|---|
| N12 | 2 | cô giáo nhận lớp mới | việc 1 | | |
| N13 | 4 | lá thư báo tin con trai mất | việc 1, sau đỉnh 1, đe dọa 1, nối 1 | mất con (thương); chủ nợ bám theo | |
| N14 | 3 | ba lần giằng co đổi thế | việc 4 | cảnh đánh có quá trình | mỗi pha đổi thế là một việc |
```

- **Việc:** các thay đổi tình thế của nhịp, ngăn bằng `;`. **Clip theo loại:** `<loại> <số>` ngăn bằng dấu phẩy, khớp số cảnh của nhịp.
- **Phim `Clip: 30s`:** Clip theo loại ghi **số cảnh**; cảnh hai khối ghi hai loại nối bằng `+`; cảnh không phải 30s ghi thêm giây: `việc+sau đỉnh 1, việc 2, nối 1 15s` (máy đọc ra việc 5, sau đỉnh 1, nối 1 đơn vị). Cột Cảnh của bảng nhịp và cột Clip của bảng Phần ghi số **đơn vị**.
- **Điểm chạm và thủ pháp:** khoảnh khắc khán giả phải cảm thấy (từ cột Cảm xúc khán giả, bảng Gieo và gặt, mô típ) và cách kể dùng ở nhịp đó (lời hứa lặp, hồi tưởng…). Mục nào ghi ở đây phải có clip giữ.
- **Nhịp ghé nơi khác rồi quay về** (quan sát ở A rồi đánh ở B, ra đèo rồi về hang): bảng tính sẵn clip `nối` cả đi và về.
- **Trần clip `việc` mỗi nhịp:** mức 1–2 tối đa 2, mức 3 tối đa 3, mức 4–5 tối đa 4. Các loại khác không tính vào trần. Vượt trần thì ghi lý do ở cột cuối, không thì máy cảnh báo. Phim 30s: trần tính bằng đơn vị (mức 1–2 tối đa 1 cảnh 30s việc, mức 3 tối đa 1,5, mức 4–5 tối đa 2).
- **Bảng Phần** (`## Phần` cuối `00-nhip.md`): mỗi phần khoảng 7 phút (5–9; phút = clip / 6, khoảng 42 clip; phim 30s: phút = đơn vị / 4,5, khoảng 32 đơn vị, khoảng 15 cảnh), cắt ở ranh giới nhịp, không trùm hai hồi (hồi dưới 5 phút gộp với phần kề thì phần ghi hai hồi); nhịp nào cũng thuộc đúng một phần.

**9. Thứ tự cắt khi dư.**
1. Gộp các clip `việc` chỉ là động tác ở nhịp mức 1–3 vào clip kề (thành shot).
2. Bỏ `đệm` ở nhịp mức 1–3, và `sau đỉnh` ở nhịp mức 1–3 không có khoảnh khắc lớn.
- **Không cắt** (cảnh đắt, cảnh chạm khán giả, cảnh làm rõ cao trào): `lớn`, `lật`, `sau đỉnh` của nhịp mức 4–5 hay của khoảnh khắc lớn, `đe dọa`, `nối`, clip giữ một mục của bảng soát, clip mang điểm chạm hay thủ pháp ở bảng phân clip. Cắt tới đây vẫn dư thì giữ, ghi lý do dưới dòng ngân sách.
