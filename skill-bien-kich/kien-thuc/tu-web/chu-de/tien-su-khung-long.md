# Chủ đề: Tiền sử, khủng long (tài liệu)

Lập 2026-09-18 tối cho Spec 22 (thể loại đầu tiên). Phim đầu `khung-long-01` đã gen 18/09: bản 1 theo file này ("quay từ hide", máy tĩnh, cấm điện ảnh) ra hình thật nhưng phẳng, đa số 3 sao; **bản 2 theo `../L2-dao-dien-phim.md` (điện ảnh, khối SOUND chi tiết) anh/chị nhận xét rất ổn cả hình và tiếng**. Anh/chị chốt 18/09: thể loại phim không cấm cú máy hay chất điện ảnh. Loại: L2 (câu chuyện có con vật xuyên suốt). Đọc `../00-chung.md`, `../L2-phim-nhan-vat.md`, `dong-vat.md` trước; file này chỉ ghi điều khác riêng cho khủng long.

## 1. Mục tiêu hình ảnh
Trông như tài liệu thiên nhiên hiện đại quay được khủng long thật ("quay từ hide"): ống kính dài từ xa, máy tĩnh hơi rung, màu phẳng chưa chỉnh, tốc độ thật, con vật làm việc thường (ăn, uống, nuôi con, nghỉ) nhiều hơn săn mồi. Rủi ro lớn nhất: ra hoạt hình hay CGI phim bom tấn vì model không có footage thật để bắt chước.

## 2. Bắt buộc có (giả thuyết)
- Chốt diện mạo từng loài bằng bộ ảnh trước khi gen cảnh nào (`../L2` mục 2.1); ảnh cận chất liệu **lấy mẫu từ loài thật**: da cá sấu, chân và cổ đà điểu, lông chim, mắt bò sát. Ghi rõ trong prompt ảnh ("skin like a crocodile's, dusty, scarred, not glossy").
- Kích cỡ so với vật quen trong khung (cây, tảng đá, con non) để model giữ tỷ lệ.
- Chuyển động có trọng lượng: "each step lands heavily, dust lifts, the ground vibration is felt in the camera", tốc độ thật.
- Chất hình như `dong-vat.md`: real-time speed, natural muted colour as captured, not colour graded, fine noise.
- Môi trường tiền sử tả bằng cây và địa hình cụ thể (dương xỉ, tuế, đầm lầy, bụi khô), không ghi "prehistoric" suông.

## 3. Cấm (chỉ còn áp khi anh/chị chọn phong cách "quay từ hide"; phim điện ảnh bỏ dòng đầu, giữ dòng hai và ba)
- "Jurassic", "epic", "cinematic lighting", "dramatic", "roar" cho mọi cảnh, khói bụi hoành tráng, cận cảnh mượt bay quanh con vật.
- Da bóng, mắt sáng "thủy tinh", răng lộ liên tục, tư thế phim quái vật.
- Người trong cảnh (thể loại này chưa có người; tiền sử có người làm sau với Higgsfield).

- **Nắng gắt, tia nắng xiên, sương phát sáng vàng** trong ảnh địa điểm và toàn cảnh (áp cả phim điện ảnh). Phim `the-last-signal` 18/09: hai ảnh GPT Image 2 với "low warm golden sun, backlit haze, god rays through the mist" anh/chị nhận xét "hơi ảo, lộ AI"; gen lại với "sun softened by thin high cloud and out of frame, no god rays, no light shafts, no lens flare, no glowing mist, natural muted colour, greens stay green" + "documentary photograph" thay "cinematic" thì ra như ảnh chụp thật nhưng anh/chị vẫn chê **cây xanh tươi quá**. Bản đạt: màu phim **tối, âm u, kịch tính** ("heavy brooding overcast sky, one thin band of dull orange low on the horizon, low-key, desaturated, foliage deep blackish green and olive, never bright green") và **gen bằng `/images/edits` với một ảnh đã ưng làm mẫu màu** ("match the colour grade, darkness, contrast and mood of the reference image exactly, but show a different place"); ảnh mẫu gửi lên phải thu nhỏ thành JPEG khoảng 1280 px (PNG 2,7 MB bị timeout khi gửi). Chưa thử trên video.

## 4. Khung prompt mẫu
Dùng mẫu `../L2` mục 4 với dòng chất hình của `dong-vat.md`; thêm câu kích cỡ và câu chất da. Ví dụ chưa gen: sẽ ghi sau phim đầu.

## 5. Veo và Seedance
Chưa có số liệu. Giả thuyết như L2: Veo cho cảnh tĩnh, rộng, có khung đầu; Seedance 2.5 cho hành động và nhiều shot.

## 6. Nguồn và kiểm chứng
- 18/09 `../../nguon/2026-09-18-dan-kieft-ai-filmmaking.md`: ví dụ khủng long và rừng tiền sử của tác giả (bảng cận chất liệu da, dòng mở "prehistoric jungle, natural lighting"). Chưa thử Seedvis.
- Phim đầu `khung-long-01` 18/09: dòng LOOK điện ảnh đã đạt (không ra CGI): "Cinematic natural-history feature film look: large-format camera, shallow depth of field, soft anamorphic falloff at the frame edges, fine film grain, deep shadows that still hold detail. Cold blue moonlit twilight with a faint silver rim light tracing the animals' outlines, thin mist low over the ground. The animals are physically real: dry, dusty, textured hide like a crocodile's, real bird feathers, small wet reptilian eyes, real weight in every step, no CGI sheen, no glossy skin, no glowing eyes." Tiếng: con non "like a gosling's peep mixed with a baby crocodile's chirp", Troodon "a dry throat click like a cassowary, a raspy goose-like hiss", mẹ "a deep resonant bellow, part elephant rumble, part foghorn". Lỗi bản 1 cần nhớ: Troodon ra nhỏ hơn con non khi không ghi tỉ lệ; đàn con ra ngựa vằn khi không gắn ảnh.
