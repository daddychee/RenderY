# Hướng dẫn làm phim drama (bản 2026-10-02)

## Hướng phim

- Khán giả: tệp drama da đen Mỹ (nhiều nữ).
- **4 phút đầu đúng format:** nạn nhân (thường là bà hay ông, mặc giản dị) bị sỉ nhục bằng lời, nói thật mà không ai tin; nữ chính vào khoảng 1:30; trả tựa và thumbnail trước phút 4. Không hồi tưởng, không trận, không chứng cứ bằng hình.
- **Sau phút 4 là phim thật:** 2–2,5 phút một cú lật, nhân quả chặt, hành động chỉ ở đáy, giải cứu, xử cuối. Khán giả biết trước bí mật chính; bất ngờ chỉ ở mạch phụ.
- Thoại là xương; nâng chất bằng cú máy kiểu phim truyền hình.

## Các bước

1. Mở chat mới ở thư mục này, gõ `/bien-kich-drama <ý tưởng>` (để trống thì Claude đề xuất).
2. **Hỏi lượt 1:** phim mẫu, tựa, thumbnail; Claude đưa 3 ý, chọn 1.
3. **Hỏi lượt 2:** độ dài, nạn nhân mở phim, cặp chính, bí mật, kẻ ác, trận, mức Seedance (khuyên 100%; *chỉ nhân viên* có thêm 30 giây Mango).
4. **Duyệt dàn ý:** xem tựa, phút trả tựa, Mở phim, cụm tiếng Anh nhân vật (tuổi, tóc, đồ nghèo hay giàu thấy rõ).
5. Claude viết và soát **phần 1**, gộp ra `kich-ban.md` rồi **dừng**. Dán vào web (**Phim mới**, loại Drama thoại), gen thử, xem.
6. Ổn thì bảo "viết tiếp". Mỗi lần có phần mới, Claude gộp lại; dán bằng **Dán lại kịch bản**.
7. Chat đầy (Claude báo) thì mở chat mới: `/bien-kich-drama <mã> tiếp`.

Muốn viết liền không dừng sau phần 1: dặn lúc duyệt dàn ý.

## Phim drama gen bằng Grok (`/bien-kich-grok`)

Dùng khi muốn gen cả phim bằng Grok (bản RenderY: Seedvis, 108 credit mỗi clip, 6/10/15 giây cùng giá). Các bước y như trên, gõ `/bien-kich-grok <ý tưởng>` (chat đầy: `/bien-kich-grok <mã> tiếp`). Khác phim Seedance:
- Mọi clip ghi `Máy: Grok 15s`; không hỏi mức Seedance. Dán vào treatment (tạo tập loại **2 = Drama có thoại**), chọn độ dài thật từng clip ở hộp clip (6/10/15 giây).
- Grok làm hỏng hành động: không đánh nhau, xô ngã, lôi kéo, ngã. Cao trào bằng lời, giấy tờ, điện thoại, mặt người; chạm nhẹ một động tác thì được (tát một cái, nắm cổ tay, giật tờ giấy).
- Mỗi clip tối đa 4 người rõ mặt; đám đông chỉ thấy lưng hay mờ phía sau.
- Trong nhà không cầm ô, mưa chỉ ngoài cửa kính; cảnh đêm ghi chữ "đêm" ở tiêu đề cảnh.
- Phim cần cảnh đánh, đám đông, sinh vật: dùng `/bien-kich-drama` (Seedance).
- Luật clip Grok: `kien-thuc/grok-drama.md`.

## File

- Phim ở `F:\gen_video_data\phim\<mã>\`: `kich-ban.md` (bản để dán), `BAN-GIAO.md` (đang ở đâu, đã dặn gì), `kich-ban/00-dan-y.md`, `kich-ban/phan-NN.md`.
- Luật câu chuyện: `kien-thuc/khung/drama-da-den.md`. Luật clip: `kien-thuc/drama-thoai.md`.
- Công cụ: `cong-cu/dan_y_drama.py` (kiểm dàn ý, phần đầu phim), `cong-cu/kiem_drama.py` (kiểm clip, gộp).

## Sửa sau khi dán

- Phần chưa dán: bảo Claude sửa, Claude giao trợ lý soát rồi gộp lại.
- Phần đã dán: sửa trên web. Chèn hay bỏ clip làm lệch mã các clip sau, cân nhắc trước.

## Phim cũ

- Phim drama khuôn cũ (`the-shop-girl`, `thu-drama-thoai`, `thu-drama-kho`) không làm tiếp được; phải làm lại dàn ý theo khuôn mới. `the-shop-girl` đã có bản chuyển khuôn ở `thu-drama-moi` (còn thiếu dẫn sai ở phần 3, 5, 7).
- Phim không phải drama: vẫn dùng `/bien-kich` như cũ.
- Không dùng Codex: chỉ sửa skill ở `.claude/`.

## Chi phí gen mỗi 10 phút

Seedance 100%: khoảng 3.350 credit (43.600đ). Mức 75%: khoảng 2.650 credit. 30 giây Mango (*chỉ nhân viên*): khoảng 6.500 credit (84.500đ).
