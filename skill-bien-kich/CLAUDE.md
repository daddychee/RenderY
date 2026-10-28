# Agent biên kịch phim AI (Padoma)

> **Bản RenderY** — chép 28/10/2026 từ `E:\PADOMA GenVid App\GEN VIDEO\GEN VIDEO\skill bien kich` (user chốt 27/10).
> - **Chỉ `/bien-kich-grok` đã nối với treatment.** Mọi clip ghi `Máy: Grok 15s`; độ dài thật (6/10/15 giây, cùng giá
>   108 credit Seedvis) người dựng chọn từng clip trên treatment. `kich-ban.md` dán vào treatment (AI Generation, cổng
>   9121): tạo tập loại **2 = Drama có thoại**, dán ở màn Kịch bản; phần viết thêm thì **⇪ Dán lại kịch bản**.
> - `/bien-kich`, `/bien-kich-drama`, `/bien-kich-muse`, `/boc-phim-bien-kich` còn nguyên bản Padoma, nói tới web của Padoma — chưa dùng với treatment.
> - Không chép theo: `.env`, `bi-mat/`, `.git/`, `.agents/`, `.codex/`, `NHAT-KY.md`. Không có khoá YouTube (`lay_binh_luan.py` không chạy).
> - `.env`: chép `.env.example` (phim ở `F:\AutoEdit\bien_kich\phim`). Treatment kiểm khuôn bằng bản chép `autoedit/treatment/kiem_drama.py` — đổi khuôn thì đổi cả hai.
> - Phần dưới đây là chữ gốc của Padoma; chỗ nói "web", "Phim mới" thì hiểu là treatment.

Thư mục này viết kịch bản phim AI bằng skill `/bien-kich` (biên kịch rồi người dựng, Spec 40 của repo GEN VIDEO). Kết quả là `kich-ban.md`, anh/chị dán vào trang **Phim mới** trên web (hay **Dán lại kịch bản** khi phim đã tạo). Ở đây không gen, không viết prompt video, không gọi web hay DB, không có key Seedvis. Phim drama nhiều thoại (loại `drama_thoai`, clip Seedance, mức 75% có Veo, Spec 44) dùng `/bien-kich-drama`, cùng kho và `cong-cu/kiem_drama.py`. Phim drama gen cả phim bằng Grok (loại `drama_thoai`, mọi clip `Grok 10s|15s`, tránh hành động nặng, Spec 69) dùng `/bien-kich-grok`, cùng `cong-cu/kiem_drama.py` (tự nhận chế độ Grok). Phim Muse (loại `phim_muse`, mỗi clip một cú Muse 10 giây, Spec 63, chỉ nhân viên) dùng `/bien-kich-muse`, `cong-cu/kiem_muse.py`. Việc phụ: `/boc-phim-bien-kich <link YouTube>` bóc phim mẫu thành mục kho biên kịch (`muc.json` ở `<THU_MUC_KHO_BIEN_KICH>/<tên>/`, chủ dự án nạp lên web). Ngôn ngữ làm việc: tiếng Việt.

## Logic (mọi thể loại)

Mọi người, mọi vật ở mỗi cảnh trả lời được "vì sao ở đây, vì sao làm thế"; người ở nơi hợp thân phận thật, ở nơi lạ thì có lý do hợp tính, nói thành lời. Một lý do kẹt, không chồng trùng hợp. Soát điều này trước khi đưa ý, dàn ý, phần.

## Khán giả hiểu, diễn viên có đất diễn (mọi thể loại)

1. **Khán giả chỉ có màn hình.** Người viết có dàn ý trong đầu, khán giả thì không. Trước mỗi cảnh hỏi: người chưa đọc dàn ý có biết đang ở đâu, vì sao, chuyện gì đang treo, cảnh trước dẫn tới đây thế nào không? Thiếu thì thêm một câu.
2. **Lời cho thông tin, mặt cho cảm xúc.** Không nói lại điều mặt đã cho thấy; câu đắt nhất cảnh có vài giây lặng sau nó.

Drama nhiều thoại: cách làm chi tiết ở `drama-thoai.md` mục 5, 6.

## Đọc gì

- Làm phim: bảng bước trong `/bien-kich`, rồi đúng file bước và tài liệu file đó ghi.
- File dài: `python cong-cu/muc_luc.py <file>` lấy offset từng mục rồi Read đúng mục.
- Không đọc `kien-thuc/tu-web/PHIEN-BAN.md`, `kien-thuc/kho/PHIEN-BAN.md` trừ khi được hỏi. Không đọc cả kho: đọc mục lục rồi `cong-cu/doc_kho.py <mã>`.

## Chỗ để

- **Bản chép, không sửa tay:** `kien-thuc/tu-web/`, `kien-thuc/kho/`, thư viện hành động `kien-thuc/thu-vien-hanh-dong.md`, `cong-cu/luat_kich_ban.py`, `cong-cu/luat_kho_bien_kich.py`, `cong-cu/kiem_drama.py`, `cong-cu/kiem_muse.py`, `cong-cu/muc_luc.py`, skill `boc-phim-bien-kich/` (cả `.claude/` và `.agents/`). Chúng do công cụ đồng bộ của repo chính ghi (từ trang web và file nguyên tắc). Muốn đổi thì báo chủ dự án sửa ở nguồn rồi chép lại.
- **Của thư mục này:** skill `.claude/skills/bien-kich/`, `.claude/skills/bien-kich-drama/`, trợ lý `.claude/agents/` (`viet-phan-bien-kich`, `soat-phan-bien-kich`, `viet-phan-drama`, `soat-phan-drama`, `viet-phan-muse`, `soat-phan-muse`, `viet-phan-grok`, `soat-phan-grok`), `.claude/skills/bien-kich-muse/`, `.claude/skills/bien-kich-grok/`; không chép sang `.agents/`, `.codex/` (không dùng Codex). `kien-thuc/drama-thoai.md`, `kien-thuc/grok-drama.md`, `kien-thuc/muse-phim.md`, `kien-thuc/phan-canh.md`, `soat-phan-canh.md`, `tran-danh.md`, `moc-mo-phim.md`, `khung/`, các script khác trong `cong-cu/`.
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

Không đọc to, không in, không chép `.env` đi đâu. Key YouTube Data API v3 (máy chủ): file trong `YT_KEYS_FILE` của `.env` (`bi-mat/youtube-data-v3.md`, git bỏ qua), mỗi dòng một key; script tự đọc, xoay key khi hết hạn mức, không in key. "Lấy comment video YouTube": `py -3 cong-cu/lay_binh_luan.py <link|mã>... --ra <thư mục>` (số liệu video và mọi bình luận, trả lời; ra `<mã>.json` và `<mã>.txt` xếp theo lượt thích). Lời thoại: transcriptapi (memory `lay-transcript-youtube` của repo chính).
