# Phiên D · skill, hai trợ lý, nhật ký (đợt 2, sau A, B, C)

**Chỉ bắt đầu khi đã có** `bao-cao-A.md`, `bao-cao-B.md`, `bao-cao-C.md` trong `kinh-nghiem/nang-cap-drama/`. Thiếu thì dừng, báo anh/chị.

**Đọc:** `00-ke-hoach.md` mục 1, 6, 7, 9, 10 (offset bằng `python cong-cu/muc_luc.py`); ba báo cáo; `.claude/skills/bien-kich-drama/SKILL.md`; `.claude/agents/viet-phan-drama.md`, `.claude/agents/soat-phan-drama.md`; `CLAUDE.md`. Tên mục khung và drama-thoai lấy ở báo cáo A, B; chỉ Read một mục khi báo cáo chưa đủ.

**Chỉ sửa:** ba file skill, trợ lý ở trên (được viết lại cả file), `CLAUDE.md` (đúng dòng nhắc `dau_drama.py`, nếu có), `NHAT-KY.md`, và đúng các dòng trỏ số mục khung trong `kien-thuc/drama-thoai.md`.

**Phát sinh từ phiên A (phải làm):**
- Khung đổi số mục: 0 Hợp đồng khán giả, 1 Nâng cấp điện ảnh, 2 Bảng đoạn, 3 Nhịp vùi dập và hé, 4 Khoảnh khắc lớn, 5 Thoại. Grep `khung.*mục [0-9]` trong `drama-thoai.md`, SKILL, hai trợ lý; sửa mọi chỗ còn trỏ số cũ (nhịp từng là mục 2, thoại từng là mục 4). Trợ lý viết đọc khung mục 0, 1, 3; trợ lý soát mục 0–1.
- Khung thêm vai **nạn nhân mở phim** (thường là người sắp đặt, ăn mặc giản dị). Bảng hỏi lượt 2 hỏi: nạn nhân là ai, quan hệ với kẻ quyền lực, sự thật nào được mớm ở đầu phim. Bước 3 duyệt báo cụm tiếng Anh của nạn nhân (dấu nghèo thấy được, "quá lên").

**Phát sinh từ phiên C:** `dau_drama.py` đã xóa. Thay `dau_drama.py <thư mục>` bằng `dan_y_drama.py dau <thư mục>`, `dau_drama.py <file>` bằng `dan_y_drama.py phan <file>` (Grep `dau_drama` trong SKILL, hai trợ lý, `CLAUDE.md`). Phim thử `thu-drama-moi`: `kiem` ra 3 LỖI "phần 3, 5, 7 không có dẫn sai" là lỗ thật của dàn ý cũ, không vá; chỉ cần lệnh chạy đúng.

**Làm:**
1. `SKILL.md` theo kế hoạch mục 10: bảng hỏi hai lượt; mẫu dàn ý đúng mục 7 (cú pháp theo báo cáo C nếu C đã đổi); bước 2 đọc gì, tự soát điều máy không kiểm, `dan_y_drama.py kiem`; bước 3 duyệt; bước 4 lời giao viết, soát; mặc định dừng sau phần 1; bước 5 gộp bằng `dan_y_drama.py dau` và `phan`. Bỏ đoạn `gv2`, mọi chỗ nhắc `dau_drama.py`, `tran-danh.md`.
2. `viet-phan-drama.md`, `soat-phan-drama.md` theo kế hoạch mục 10 (đọc gì, không đọc gì, mục soát mới, báo cáo). Giữ frontmatter `model: sonnet`, `effort: medium`.
3. Kiểm chéo: mọi tên mục, lệnh, cột nhắc trong ba file khớp file thật (Grep); chạy `py -3 cong-cu/dan_y_drama.py kiem` và `doc` trên `F:\gen_video_data\phim\thu-drama-moi\kich-ban` để chắc lệnh trong SKILL chạy được.
4. Đo token ba file (đích: SKILL ≤ 4.500, mỗi trợ lý ≤ 2.500) và ước lại tổng đọc của chat chính bước 1–2, trợ lý viết (kế hoạch mục 9).
5. `NHAT-KY.md`: một mục ngày làm, gồm cả A, B, C, D (lấy từ báo cáo), số token trước và sau, ghi rõ `.agents/`, `.codex/`, `AGENTS.md` chưa chép, còn lệch.

**Xong:** ghi `bao-cao-D.md` (≤ 15 dòng) và báo anh/chị: số đo, chỗ còn lệch, việc kế (chép `.agents/`, `.codex/`; chọn ý tưởng phim mới, chạy `/bien-kich-drama`). Không commit.
