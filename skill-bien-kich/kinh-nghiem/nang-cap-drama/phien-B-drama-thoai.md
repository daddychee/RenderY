# Phiên B · nâng `drama-thoai.md` kiểu phim truyền hình (đợt 1, chạy song song A, C)

**Đọc:** `kinh-nghiem/nang-cap-drama/00-ke-hoach.md` trọn; `kien-thuc/drama-thoai.md` trọn. Khi cần biết công cụ web kiểm gì: Grep `LỖI\|NHẮC` trong `cong-cu/kiem_drama.py` (không đọc trọn). Có thể đọc 2 clip mẫu trong `F:\gen_video_data\phim\the-shop-girl\kich-ban\phan-01.md` (Grep `^### P0` lấy offset) để thấy cách viết hiện tại; không đọc cả file.

**Chỉ sửa:** `kien-thuc/drama-thoai.md`.

**Làm:**
1. Thêm mục **Ngôn ngữ máy kiểu phim truyền hình** theo kế hoạch mục 5: mỗi kỹ thuật một dòng, ghi khi nào dùng và viết vào `Hình:` thế nào. Sửa clip mẫu ở mục 1 (hay thêm một mẫu) cho thấy vòng phản ứng sau câu bom và góc quyền.
2. Thêm mục **Cảnh hành động** (thay việc trỏ `tran-danh.md`): người yếu thế (kế hoạch mục 3.5), mỗi đòn ghi ai, tay hay chân trái/phải của chính nhân vật, hướng, trúng đâu, ai đứng đâu; shot rộng cho vị trí, cận cho đòn; vẫn có thoại; đòn của người nhỏ trúng người to phải có lý do ngoài sức (đối chiếu dáng ở Cụm cố định).
3. Nâng **lời nghĩ và lời tự kể** thành công cụ chính (kế hoạch mục 2.2, 2.6): điều nhân vật giấu, câu giải thích điều phi lý, nỗi khổ giấu kín nói bằng lời nghĩ; gieo và gặt phải nghe được. Không tạo loại dòng mới: khuôn dòng là giao ước với web (`Thoại:`, `Lời nghĩ:`), lời tự kể viết bằng `Lời nghĩ:` trên hình.
4. Vết thương, vật ghi trái/phải của chính nhân vật ở `Hình:` mọi clip có chúng, đối chiếu dòng `vết`, `vật` của bảng Gieo và gặt.
5. Mục 1 đoạn "Máy lo": `dan_y_drama.py` thay `dau_drama.py` (lệnh `dau`, `phan`, xem kế hoạch mục 8). Mục 7 Ghi chú nối thêm dòng `- Gieo, gặt: G01 P003, G04 P021`.
6. Giữ mọi luật còn đúng (máy Seedance/Veo, trần từ, trục, cảm xúc ba nhịp); bỏ câu trùng hay lỗi thời. Không đưa luật câu chuyện vào đây (của khung, phiên A).

**Trần:** ≤ 6.500 token (`python cong-cu/muc_luc.py kien-thuc/drama-thoai.md`). Luật mới phải hợp giới hạn Seedance: shot ít nhất 2,5 giây, 3–5 shot mỗi clip 15 giây, chỉ cắt thẳng.

**Xong:** ghi `kinh-nghiem/nang-cap-drama/bao-cao-B.md` (≤ 15 dòng): tên và số các mục thật, token, điều lệch kế hoạch. Không ghi NHAT-KY, không chép `.agents/`, `.codex/`, không commit.
