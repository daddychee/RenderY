# Chủ đề: Động vật (hành vi, tài liệu thiên nhiên)

Điền 2026-09-18 từ `KINH-NGHIEM-PROMPT.md` mục 7, 11 và Spec 18; sửa ở phiên tổng 18/09. Loại: L1 (khoảnh khắc hành vi) và L2 (câu chuyện động vật, đợt thử A "đại bàng nuôi con" chưa chạy).

## 1. Mục tiêu hình ảnh
Cái đắt là **hành vi** (quật đuôi, săn mồi, sinh con), không phải cú máy. Trông như footage nhà đài: từ xa, ống kính dài, cỡ toàn, máy đứng yên hơi rung, tốc độ thật.

## 2. Bắt buộc có
- Kịch bản ba nhịp có mốc giây (Seedance 2.5): trạng thái trước, cú đánh, hậu quả gộp lặng lại. "ONE continuous shot, no cuts" ngay trước dòng thời gian.
- Cơ chế vật lý tả bằng động từ ("the water bulges directly beneath the seal, the orca's black tail flukes burst up from right under it").
- Dấu hiệu loài giữ khi rút gọn ("black-and-white orca"), nếu không model ra loài khác.
- "Real-time speed, no slow motion".
- Keyframe (nếu dùng) chỉ có con mồi, trạng thái trước cú đánh. Mặc định gen thẳng.
- Phản ứng con mồi tả bằng chuỗi động từ cơ thể theo thứ tự (freezes, ears perked, bolts), như đạo diễn cảm xúc ở `../L2-phim-nhan-vat.md` mục 2.10 nhưng chỉ lấy điều nhìn thấy.
- Câu chuyện có con vật xuyên suốt (L2, đại bàng nuôi con): con vật cần bộ ảnh tham chiếu như nhân vật người, trong đó **ảnh cận chất liệu da, lông** bắt buộc, nền xám. Xem `../L2-phim-nhan-vat.md` mục 2.1; L2 được xen cỡ cảnh và cận cảnh từ ảnh tham chiếu, khác với khoảnh khắc một cú máy dưới đây.

## 3. Cấm
- Mẫu "Long take + thủ pháp" (hành động dồn về cuối).
- Với khoảnh khắc một cú máy: cận cảnh mượt, đổi góc, zoom (dấu hiệu AI). Bọt nước, phun quá to.
- Số khối mốc giây: **3 khối là số đã đạt** (4 sao, 17/09); 5 khối một dòng bị cắt cảnh ở ranh khối 1/1 lần nhưng kèm keyframe hỏng, chưa kết luận. 5 khối ba dòng và 8 shot chờ đợt B (`../cho-kiem-chung.md`); tới lúc đó LLM vẫn viết 3 khối.

## 4. Khung prompt mẫu
Spec 18 mục C (mẫu 4 sao, khoảng 120 từ, `KINH-NGHIEM-PROMPT.md` mục 11). Bản "prompt Seedance đủ" (`../00-chung.md` mục 4) chờ đợt B.

## 5. Veo và Seedance
- Hành động: Seedance 2.5 (mốc giây điều khiển được nhịp; Veo đứng hình hoặc méo).
- Câu chuyện nhiều phân cảnh (L2): chưa thử, xem `../L2-phim-nhan-vat.md`.

## 6. Nguồn và kiểm chứng
- 17/09 `kiem-chung/khoanh_khac_dong_vat.py`, 2 vòng, 4 clip, 4 sao ở vòng 2; đề bài 80, 81 làm đối chứng hỏng. 17/09 đề bài 87, 89, 103, 109 qua app 4 đến 5 sao với cùng cấu trúc.
- 18/09 `../../nguon/2026-09-18-dan-kieft-ai-filmmaking.md`: ảnh cận chất liệu da cho sinh vật (ví dụ khủng long của tác giả), chưa thử.
