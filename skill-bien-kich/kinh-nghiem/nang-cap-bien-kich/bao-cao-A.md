# Báo cáo phiên A · khung (2026-10-04)

- Đã làm: thêm `## 0. Hợp đồng khán giả` và `## 1. Nâng cấp điện ảnh` vào `kien-thuc/khung/fantasy-drama.md` và `kien-thuc/khung/sinh-vat-bao-ve.md`; đánh lại số mục; đoạn mở đầu mỗi file liệt kê các mục.
- Mục 0: câu "Chưa có bản editor nhập; skill hỏi ở bảng hỏi lượt 1", dòng `Trả tựa trước:`, 4 dòng tạm (lời hứa của tựa, vào trước, cảm xúc chờ, mất khán giả khi), mỗi dòng "(tạm, chờ editor)".
- `Trả tựa trước:` fantasy-drama là `6%`; sinh-vat-bao-ve là `6% (Cứu lần 1; phim 30 phút khoảng 1:48)`.
- Mục 1: 7 điều (phi lý một lý do nói ra, gieo và gặt, một lần đổi thế, khán giả biết trước và chỗ bất ngờ, thắng nhờ gì, vòng mở cuối phần 7 phút có KB282, khán giả chỉ có màn hình).
- Số mục mới, fantasy-drama: 0 Hợp đồng, 1 Nâng cấp, 2 Bảng đoạn, 3 Nhịp vùi dập và hé, 4 Khoảnh khắc lớn, cú lật, xả, kết, 5 Lựa chọn.
- Số mục mới, sinh-vat-bao-ve: 0, 1, 2 Bảng đoạn, 3 Nhịp, 4 Khoảnh khắc lớn, cú lật, xả, 5 Thoại (trước là 3b), 6 Kết mở cho series, 7 Lựa chọn. Trong file đã sửa các chỗ trỏ "mục 3b", "mục 4", "mục 3".
- Token (muc_luc.py), fantasy-drama: 3608 → 5163, mục 0–1 là 1477.
- Token, sinh-vat-bao-ve: 5732 → 5992, mục 0–1 là 1288.
- File khác trỏ số mục cũ (không sửa): `.claude/skills/bien-kich/chat-1-nhip-phan-clip.md:74` "Thang vùi dập theo mục 2 của khung" (nay là mục 3), bản chép ở `.agents/skills/bien-kich/chat-1-nhip-phan-clip.md:74`. Skill mới và trợ lý `viet-phan-bien-kich`, `soat-phan-bien-kich` trỏ "mục 0 và 1" và dòng `Trả tựa trước`, đã khớp.
- Lệch kế hoạch: để vừa 6.000 token, sinh-vat-bao-ve bỏ cột Phút của Bảng đoạn, thay bằng "Phút = % × độ dài phim (30 phút: 1% = 18 giây)".
- Cũng ở sinh-vat-bao-ve: bỏ vài lời giải thích (ngày chốt, "phim nguồn để 73% là quá muộn", tên file phân tích, nay chỉ trỏ thư mục), bỏ ý lặp. Không bỏ luật.
- Câu "Khán giả luôn biết điều kẻ ác không biết" chuyển từ mục Nhịp sang mục 1 điều 4.
- KB282 là mã của kho drama-da-den (hợp phim nhiều thoại). Hai khung chỉ dẫn nó làm một cách treo vòng mở.
