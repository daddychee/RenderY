"""SỔ TRA — trang stock nội bộ của team (Đợt 1 flow Đường Dây, user chốt 06/09).

Vai trò: MỘT ô tìm cho 4 nguồn (Envato/Pexels/Pixabay/Ref) — team đang làm việc
mở ra là thấy ngay source đã có, kèm nhãn "đã dùng ở tập nào" chống lặp.

Nguyên tắc khắc cột:
- Sổ giữ METADATA + từ khóa 7 trục, KHÔNG chứa file nguồn (Envato cấm re-stock,
  đĩa không phình): preview là cache tái tạo được, frames JPEG là thứ duy nhất
  giữ vĩnh viễn.
- id chính tắc `nguon:ma[:khuc]` là cho MÁY — bất biến, mọi truy xuất qua db;
  tên file trên đĩa là cho NGƯỜI — máy không bao giờ parse tên file.
- Điểm chất lượng KHÔNG phải cột tĩnh: chỉ sự kiện phản biện ngoài (người thay,
  lên final, retention) trong bảng su_kien — "thắng phễu" không được tính là tốt.
"""
