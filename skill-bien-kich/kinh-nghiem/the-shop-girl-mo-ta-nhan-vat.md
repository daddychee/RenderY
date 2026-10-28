# Lỗi mô tả nhân vật khi gen phần 1 · the-shop-girl (2026-10-01)

## Hiện tượng
Dán `kich-ban.md` (drama_thoai) lên web, bảng tài sản tự đoán mô tả ảnh nhân vật và đoán sai so với bảng Nhân vật của dàn ý:
- Damon (nam chính, dàn ý 35): web ghi "Black man about 45, close-cropped black hair greying at temples, short trimmed beard, charcoal tailored suit… slight eye bags, uneven skin on forehead". Nhãn "Damon, owner charcoal suit". Có lẽ đoán từ "ông Hale", "owner".
- Nia (nữ chính, dàn ý 24, vest đen, dây chuyền vàng): web ghi 26, vest navy, dây chuyền bạc, "faint under-eye bags, slightly uneven skin, a loose strand of hair".
- Cặp chính của drama da đen (khán giả nữ đông) bị vẽ già, kém xinh. Chủ dự án phải tự viết lại mô tả.

## Nguyên nhân (đã tra)
- Skill `/bien-kich-drama`: bảng `## Nhân vật` chỉ nằm trong `kich-ban/00-dan-y.md` (cột tiếng Việt, một câu). `kiem_drama.py gop` lấy phần đầu phim của `phan-01.md` + từ `# Phần` trở đi; phần đầu `phan-01.md` chỉ có 4 dòng (tên, Loại phim, Seedance, Thể loại). `kien-thuc/drama-thoai.md` mục 6 dặn clip không tả mặt, tóc, áo ("web lấy từ ảnh nhân vật"). Vậy web không có nguồn ngoại hình nào.
- Skill `/bien-kich` không bị: có bảng `## Cụm cố định` (Mã NV | Tên | Cụm tiếng Anh: tuổi, giới, tóc màu kiểu, áo màu, dấu riêng), xem `.claude/skills/bien-kich/chat-1-nhip-phan-clip.md` dòng 55 và 75.
- Web (repo chính, chỉ đọc, KHÔNG sửa) đã đọc phần đầu kịch bản cho cả drama:
  - `app/dan_drama.py` `chia_phan`: `dau` = các dòng trước `# Phần` đầu tiên.
  - `app/bang_tai_san.py` `_phan_dau` (dòng ~198): lấy mục `Nhân vật và bối cảnh` của phần đầu (hàm `_muc`), đưa vào prompt khung cảnh và bảng tài sản với tiêu đề "## Nhân vật và bối cảnh (phần đầu kịch bản)" (dòng ~245, ~361).
  - `cum_nhan_vat` (dòng ~188): đọc bảng `Cụm cố định` của phần đầu, dòng có cột `Mã` bắt đầu `NV` và cột bắt đầu bằng `Cụm` → nguồn `nhan_dang` (Spec 34 K7).
  - Cần xác nhận: `_muc` đọc tiêu đề nào chính xác; `app/kiem_drama.py` (`tach`, dòng ~103–117) có chấp nhận bảng, mục `##` trong phần đầu không (không báo LỖI); mã NV trên web lấy từ bảng hay web tự cấp.
- Phần "quầng mắt, da không đều" có thể do prompt hệ thống của web chủ ý thêm cho ảnh thật; nếu vậy thì đó là việc của repo chính, chỉ ghi lại báo chủ dự án.

## Hướng sửa (để chat sửa skill quyết)
- Dàn ý drama có bảng `## Cụm cố định` (Mã NVxx | Tên | Cụm tiếng Anh) theo đúng định dạng web đọc, bên cạnh hoặc thay bảng Nhân vật hiện tại; cột giọng giữ ở bảng Nhân vật.
- Phần đầu `phan-01.md` (trợ lý viết chép từ dàn ý) mang luôn mục đó, để `gop` đưa vào `kich-ban.md`.
- Cụm cặp chính: tuổi đúng, nét đẹp hợp thể loại (drama da đen: cặp chính trẻ, đẹp, phong độ; nam chính trông dưới 35), tóc, đồ theo màu, dấu riêng có trái/phải của chính nhân vật. Không ghi quầng mắt, da xấu cho cặp chính.
- Nhân vật đổi đồ lớn giữa phim (Nia váy đỏ ở N11, Lance từ N10): xem web có hỗ trợ dạng/nhiều dòng một mã như `/bien-kich` không.
- `kiem_drama.py` (của thư mục này): nhắc khi phần đầu thiếu bảng Cụm cố định, hay dòng NV thiếu tuổi.
- Bảng hỏi bước 1 hoặc bước 3 duyệt: báo cụm ngoại hình cặp chính cho anh/chị duyệt.

## Cụm đã soạn tay cho phim này (mẫu)
- Nia: "Beautiful Black woman about 24, slim and graceful, warm deep brown skin with a soft healthy glow, oval face with high cheekbones, large dark almond-shaped eyes with long lashes, … short soft natural curly hair in a rounded tapered cut that frames her face, … soft ivory silk blouse with a small tie-bow at the neck under a fitted black jewellery shop uniform vest, a thin gold chain with a small round St Christopher medal"
- Damon: "Handsome Black man in his early thirties, tall and athletic with broad shoulders, … short tapered fade haircut with a crisp line-up and a well-groomed short boxed beard; … tailored charcoal grey three-piece suit, crisp white shirt open at the collar, … a faint old burn scar on the left side of his neck"
