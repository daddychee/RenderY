# Phiên C · công cụ `dan_y_drama.py` (đợt 1, chạy song song A, B)

**Đọc:** `kinh-nghiem/nang-cap-drama/00-ke-hoach.md` mục 7, 8, 9 (dùng `python cong-cu/muc_luc.py` lấy offset); `cong-cu/dau_drama.py` trọn; `cong-cu/muc_luc.py` (cách ước token); test sẵn có của thư mục (Grep `def test_` trong `cong-cu/`) để theo cùng kiểu. `cong-cu/kiem_drama.py` là bản chép của web: được import hàm đọc, không sửa.

**Chỉ sửa:** `cong-cu/dan_y_drama.py` (mới), test của nó, xóa `cong-cu/dau_drama.py` khi lệnh mới đã thay đủ. Không sửa SKILL, trợ lý, `kien-thuc/` (phiên D và A, B làm).

**Làm:**
1. Viết `dan_y_drama.py` với 4 lệnh `kiem`, `doc`, `dau`, `phan` đúng kế hoạch mục 8. Giữ mọi kiểm và hành vi của `dau_drama.py` (chép phần đầu phim, LỖI và NHẮC về Cụm cố định, tên ở `Có mặt:`/`Khung:` có cụm, kiểm `kich-ban.md` đã gộp). Theo phong cách script của thư mục: chỉ in LỖI, NHẮC và một dòng tóm tắt.
2. Test: fixture nhỏ tự viết, phủ mỗi LỖI của `kiem` và `phan`, cắt đúng của `doc` (phần 1 có Mở phim; dòng `vết` còn hiệu lực sang phần sau).
3. Chạy thử trên dàn ý thật: chép `F:\gen_video_data\phim\the-shop-girl\kich-ban\00-dan-y.md` sang `F:\gen_video_data\phim\thu-drama-moi\kich-ban\00-dan-y.md` (không sửa phim the-shop-girl), chuyển sang khuôn mới: thêm Tựa và thumbnail, Mở phim, cột Ngày; dồn Lý do nền, Sổ liên tục, Ghi chú cảnh mở vào Gieo và gặt; rút cột Việc. Chuyển thô cũng được, mục đích là đo. Chạy `kiem`, rồi `doc` cho từng phần.

**Đo:** token dàn ý mới (không kể Cụm cố định) so với 18.838 của bản cũ; token đầu ra `doc` mỗi phần (đích ≤ 7.000).

**Xong:** ghi `kinh-nghiem/nang-cap-drama/bao-cao-C.md` (≤ 15 dòng): cú pháp lệnh thật, các LỖI và NHẮC đã cài, kết quả test, số đo, điều lệch kế hoạch (nếu khuôn ở mục 7 có chỗ máy khó đọc thì nói chỗ nào và đã đổi gì). Không ghi NHAT-KY, không chép `.agents/`, `.codex/`, không commit.
