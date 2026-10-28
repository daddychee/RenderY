# Bàn giao sang repo chính: web tả ảnh nhân vật drama theo Cụm cố định (2026-10-01)

Bối cảnh: phim the-shop-girl (drama_thoai). Web tả ảnh cặp chính sai và kém xinh: Damon 35 thành 45 tóc bạc; Nia sai tuổi, sai màu đồ, có quầng mắt, da không đều. Phía skill đã sửa xong: kịch bản drama giờ có phần đầu gồm `## Nhân vật và bối cảnh` và `## Cụm cố định` (Mã NVxx | Tên (she/he) | Cụm tiếng Anh 30–60 từ | Ghi chú; đổi đồ lớn thì thêm dòng cùng mã, Tên `…, dạng 2`). Đã thử bằng `_phan_dau`, `cum_nhan_vat`, `app/kiem_drama.kiem` trên `F:\gen_video_data\phim\the-shop-girl\kich-ban.md`: web đọc đủ 18 dòng, 0 LỖI. Ngoài ra phải sửa thêm ở web các việc dưới đây.

## Việc 1 (cần làm trước khi gen lại ảnh the-shop-girl): bỏ khuyết điểm cho cặp chính drama
- `app/bang_tai_san.py` dòng ~316, prompt bảng tài sản: "`mo_ta` … người có 2 đến 3 khuyết điểm cụ thể". Đây là nguồn của "under-eye bags, uneven skin".
- Đề xuất: phim drama (`loai_phim.la_drama`) thì nhân vật có cụm mở bằng `Beautiful`/`Handsome` (hay cặp chính, người khán giả thương) không thêm khuyết điểm về da, mắt, tuổi. Khuyết điểm nhỏ để ảnh trông như người thật (nếu cần) chỉ ở tóc con, nếp áo. Kẻ ác giữ luật cũ.
- Tra xem luật này có nguồn ở file nguyên tắc (`L2-phim-nhan-vat.md` mục "2. Bắt buộc có") không; nếu có thì sửa ở đó cho drama.

## Việc 2 (nên làm cùng): `mo_ta` và `nhan_dang` theo cụm của kịch bản
- Dòng ~311–314: `nhan_dang` 20 đến 35 từ, "rút từ `mo_ta`"; cụm có thì chép nguyên, nhưng "chỗ trái `mo_ta` thì theo `mo_ta`". Vậy nếu web tả `mo_ta` lệch (tuổi, màu đồ) thì cụm thua. Field ở dòng ~104 cũng ghi 20–35 từ.
- Đề xuất: khi Cụm cố định có cụm cho dạng đó, `mo_ta` phải giữ nguyên tuổi, tóc, màu đồ, dấu riêng của cụm (chỉ thêm nền xám, ánh sáng); bỏ câu "trái thì theo `mo_ta`". Nới trần `nhan_dang` tới khoảng 60 từ khi chép từ cụm (hay rút cụm còn ≤35 từ nhưng giữ tuổi, tóc, màu đồ, dấu riêng).

## Việc 3 (không gấp): đưa luật kiểm phần đầu vào `app/kiem_drama.py`
- Skill đang kiểm bằng `skill bien kich/cong-cu/dau_drama.py` (của thư mục skill, vì `cong-cu/kiem_drama.py` là bản chép). Luật: LỖI khi thiếu `## Nhân vật và bối cảnh`, thiếu bảng `## Cụm cố định` có dòng NV, dòng NV thiếu cụm hay thiếu tuổi, tên ở `Có mặt:`/`Khung:` không có cụm; NHẮC khi cụm có eye bags, wrinkle, uneven skin, greying.
- Đưa vào `app/kiem_drama.py` thì web cũng báo khi editor dán kịch bản thiếu cụm. Khi đó chạy `kiem-chung/dong_bo_skill_phim.py` và báo bên skill bỏ `dau_drama.py` phần kiểm (giữ phần chép).

## Sau khi sửa
- Phim the-shop-girl trên web: **Dán lại kịch bản** với `kich-ban.md` mới, lập lại bảng tài sản, xem mô tả Nia (NV01) và Damon (NV03) trước khi gen ảnh.
- Không sửa thư mục `skill bien kich` từ repo chính (trừ lệnh đồng bộ).
