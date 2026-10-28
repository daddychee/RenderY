# Agent biên kịch phim AI (Padoma)

Thư mục này viết kịch bản phim AI bằng skill `/bien-kich` (biên kịch rồi người dựng, Spec 40 của repo GEN VIDEO). Kết quả là `kich-ban.md`, anh/chị dán vào trang **Phim mới** trên web (hay **Dán lại kịch bản** khi phim đã tạo). Ở đây không gen, không viết prompt video, không gọi web hay DB, không có key Seedvis. Phim drama nhiều thoại (loại `drama_thoai`, clip Seedance, mức 75% có Veo, Spec 44) dùng `/bien-kich-drama`, cùng kho và `cong-cu/kiem_drama.py`. Việc phụ: `/boc-phim-bien-kich <link YouTube>` bóc phim mẫu thành mục kho biên kịch (`muc.json` ở `<THU_MUC_KHO_BIEN_KICH>/<tên>/`, chủ dự án nạp lên web). Ngôn ngữ làm việc: tiếng Việt.

## Đọc gì

- Làm phim: bảng bước trong `/bien-kich`, rồi đúng file bước và tài liệu file đó ghi.
- File dài: `python cong-cu/muc_luc.py <file>` lấy offset từng mục rồi Read đúng mục.
- Không đọc `kien-thuc/tu-web/PHIEN-BAN.md`, `kien-thuc/kho/PHIEN-BAN.md` trừ khi được hỏi. Không đọc cả kho: đọc mục lục rồi `cong-cu/doc_kho.py <mã>`.

## Chỗ để

- **Bản chép, không sửa tay:** `kien-thuc/tu-web/`, `kien-thuc/kho/`, thư viện hành động `kien-thuc/thu-vien-hanh-dong.md`, `cong-cu/luat_kich_ban.py`, `cong-cu/luat_kho_bien_kich.py`, `cong-cu/muc_luc.py`, skill `boc-phim-bien-kich/` (cả `.claude/` và `.agents/`). Chúng do công cụ đồng bộ của repo chính ghi (từ trang web và file nguyên tắc). Muốn đổi thì báo chủ dự án sửa ở nguồn rồi chép lại.
- **Của thư mục này:** skill (`.claude/skills/bien-kich/`, sửa xong chép y nguyên sang `.agents/skills/bien-kich/`; `.claude/skills/bien-kich-drama/` cũng chép sang `.agents/` (đổi Claude thành Codex); trợ lý `.claude/agents/` chỉ có ở `.claude/`), `kien-thuc/drama-thoai.md`, `kien-thuc/phan-canh.md`, `soat-phan-canh.md`, `tran-danh.md`, `moc-mo-phim.md`, `khung/`, các script khác trong `cong-cu/`.
- Kịch bản từng phim: `<THU_MUC_PHIM>/<mã>/` (`.env`).

## Kho biên kịch: bóc, nạp, duyệt, xuất

Kho là nơi `/bien-kich` đọc thủ pháp (`kien-thuc/kho/<thể loại>/`). Một phim mẫu đi 4 bước:

1. **Bóc:** `/boc-phim-bien-kich <link YouTube> <tên ngắn> <mã thể loại>` (mã ở `THE_LOAI` trong `cong-cu/luat_kho_bien_kich.py`, như `drama-thoai`; không rõ thì bỏ). Ra `<THU_MUC_KHO_BIEN_KICH>/<tên>/muc.json`.
2. **Nạp:** skill tự chạy `nap_kho.py` ở bước cuối. Máy chủ: nạp thẳng vào kho, mục ở trạng thái chờ duyệt. Máy editor: không nạp được (không có DB), editor nhắn chủ dự án thư mục và thể loại; chủ dự án nạp tay trên máy chủ, từ `D:\padoma\GEN VIDEO`: `py -3 kiem-chung/nap_kho_bien_kich.py <thư mục>\muc.json --the-loai <mã>`. Chạy lại cùng file không tạo trùng.
3. **Duyệt:** chủ dự án duyệt, sửa, xếp thể loại trên web, trang **Kho biên kịch** (`/kho-bien-kich`). Mục chưa duyệt hay "Chưa xếp" không sang skill.
4. **Xuất:** trên máy chủ, từ `D:\padoma\GEN VIDEO`: `py -3 kiem-chung/dong_bo_skill_bien_kich.py`. Lệnh ghi lại `kien-thuc/kho/`; từ đó `/bien-kich` mới thấy mục mới.

Sửa skill bóc phim thì sửa ở repo chính (`.claude/skills/boc-phim-bien-kich/`, chép sang `.agents/`), rồi `py -3 kiem-chung/dong_bo_skill_phim.py`.

## Máy editor và máy chủ

Máy chủ là máy mở thư mục này ở `D:\padoma\GEN VIDEO\skill bien kich`; mọi chỗ khác là máy editor.

- **Máy editor:** chỉ ghi vào `<THU_MUC_PHIM>/<mã>/` và `<THU_MUC_KHO_BIEN_KICH>/<tên>/` (bóc phim). Không sửa skill, khung, công cụ; không chạy git; không ghi `NHAT-KY.md`. Điều đáng nhớ thì ghi vào `BAN-GIAO.md` của phim, mục "Đề xuất bài học". Thấy lỗi trong skill hay công cụ thì báo editor nhắn chủ dự án. Không từ chối việc viết kịch bản, không bảo editor "sang máy chủ".
- **Máy chủ:** được sửa skill, khung, công cụ; cuối phiên có thay đổi thì ghi `NHAT-KY.md` (ngày, sửa gì). Không commit khi anh/chị chưa bảo.

## Token

- **Trần: không chat nào vượt 250.000 token**, tính riêng chat chính và từng trợ lý phụ; nhắm dưới 150.000. Tài liệu bắt đọc của một bước không quá 40.000 (riêng trợ lý viết phần có trận khoảng 47.000). Mỗi chat dừng ở ngưỡng ghi đầu file bước.
- Việc dài chia chat hay giao trợ lý phụ, nối bằng `BAN-GIAO.md` trong thư mục phim (đang ở đâu, đã chốt gì, việc kế), không nối bằng lịch sử chat.
- Sửa bằng Edit đúng chỗ, không ghi lại cả file. Script chỉ in kết quả và dòng lỗi.
- Thêm luật thì bỏ luật cũ đã lỗi thời hay trùng; luật nào máy đếm được thì viết vào `cong-cu/dem_phan_canh.py`.

## Bí mật

Không đọc to, không in, không chép `.env` đi đâu.
