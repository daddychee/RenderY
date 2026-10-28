# Phiên A · viết lại khung drama-da-den (đợt 1, chạy song song B, C)

**Đọc:** `kinh-nghiem/nang-cap-drama/00-ke-hoach.md` trọn; `kien-thuc/khung/drama-da-den.md` trọn. Cần xem một mã KB thì `py -3 cong-cu/doc_kho.py <mã>`; không đọc kho trọn, không đọc file kinh nghiệm khác (kế hoạch đã chắt).

**Chỉ sửa:** `kien-thuc/khung/drama-da-den.md` (được viết lại cả file).

**Làm:**
1. Đầu file thêm `## 0. Hợp đồng khán giả` (kế hoạch mục 2) và `## 1. Nâng cấp điện ảnh` (kế hoạch mục 3). Mỗi điểm một dòng luật, kèm chỗ đặt trong phim khi có. Giữ đúng hai tiêu đề này (phiên D trỏ tới).
2. Thay bảng đoạn bằng khung kế hoạch mục 4, theo % và phút; giữ mã KB hợp từng đoạn và cột "Việc với người xem". Mỗi mã KB còn giữ phải khớp định vị mới (đọc mã bằng `doc_kho.py` khi không chắc); mã nào kéo về format cũ (lặp vòng vả mặt thuần) thì bỏ hay hạ xuống tùy chọn.
3. Giữ và làm gọn: nhịp vùi dập và hé, khoảnh khắc lớn, cú lật, xả, kết, bảng thoại. Mục "Lựa chọn" gộp dòng còn hợp vào bảng đoạn, bỏ phần còn lại.
4. Câu mở file: khung nói cả khán giả muốn gì (không còn "chỉ nói thứ tự, tỉ lệ, nhịp").
5. Không lặp luật đã ở `kien-thuc/drama-thoai.md` (khuôn clip, máy, cú máy) hay luật máy đếm.

**Trần:** cả file ≤ 5.500 token, mục 0–1 ≤ 2.000 (trợ lý viết và soát đọc riêng hai mục này). Đo: `python cong-cu/muc_luc.py kien-thuc/khung/drama-da-den.md`.

**Xong:** ghi `kinh-nghiem/nang-cap-drama/bao-cao-A.md` (≤ 15 dòng): tên các mục thật kèm token từng mục, mục nào trợ lý viết nên đọc, mã KB đã bỏ, điều lệch kế hoạch. Không ghi NHAT-KY, không chép `.agents/`, `.codex/`, không commit.
