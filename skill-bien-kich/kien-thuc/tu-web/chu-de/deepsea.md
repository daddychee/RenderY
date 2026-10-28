# Chủ đề: Deepsea và cảnh dưới nước

Điền 2026-09-18 từ `KINH-NGHIEM-PROMPT.md` mục 1, 7 và hướng dẫn cảnh dưới nước trong `prompt_llm.py`. Loại chính: L1.

## 1. Mục tiêu hình ảnh
Như footage tàu lặn hoặc thợ lặn quay: tương phản thấp, hơi đục có hạt lơ lửng, màu tự nhiên không grade, máy cầm tay hơi trôi, ngang tầm mắt cá, góc rộng. Một nguồn sáng duy nhất.

## 2. Bắt buộc có
- Sinh vật hiếm: bắt buộc đi đường ảnh keyframe (GPT Image 2 đúng loài ngay); gen thẳng ra sai loài ở cả hai model.
- Tiếng dưới nước tả đúng (muffled underwater ambience, soft bubbles).
- Ánh sáng "lit by a white light beam from outside the frame", không nhắc tàu lặn.

## 3. Cấm
- dramatic, golden, volumetric, god rays, cinematic lighting, crystal clear; chuyển động mượt như máy trên ray.
- Hai đèn chiếu cùng lúc; cá tự phát sáng quá mạnh ("giống AI").
- Nhắc "submersible" (cả tàu xuất hiện).

## 4. Khung prompt mẫu
Dòng chất hình dưới nước: "Documentary underwater footage, handheld diver camera, wide lens, low contrast, slightly hazy, muted natural blue-grey water, visibility fades with distance, fine particles drifting, not color graded." Cú máy gợi ý từ footage nhà đài: cá bơi thẳng về máy rồi lượn sang một bên; máy thấp ngửa lên, cá thành bóng in trên mặt nước; bám ngang thân khi cá lướt sát ống kính; cá đi xa dần vào màn nước mờ.

## 5. Veo và Seedance
- Cảnh tĩnh sinh vật từ keyframe: Veo (Seedance đứng yên như slide). Cá mập nhảy, cắn nhau: Seedance.

## 6. Nguồn và kiểm chứng
- 12/09 mốc 0 (sai loài), 13/09 `so_sanh_model.py` 31 clip, 8 khung footage nhà đài `kiem-chung/anh-tham-chieu/ca-map-mood/`.
- Tài liệu chuyên gia: chưa nạp.
