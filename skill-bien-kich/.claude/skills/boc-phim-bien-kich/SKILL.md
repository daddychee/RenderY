---
name: boc-phim-bien-kich
description: Bóc một phim YouTube thành bảng nhịp thô phủ kín cả phim và các mục thủ pháp biên kịch (khung, khoảnh khắc, thoại) theo định dạng nạp kho biên kịch (Spec 40 mục D). Dùng khi anh/chị đưa link phim YouTube để nhập kho biên kịch, hoặc gõ /boc-phim-bien-kich.
---

# Bóc phim YouTube vào kho biên kịch

Đối số: link YouTube, có thể kèm tên ngắn cho thư mục (`me-rong-1`) và mã thể loại kho (`drama-thoai`; không có thì mục vào "Chưa xếp"). 0 credit Seedvis. Làm nhẹ: không băm cả phim từng cảnh như Spec 24; mục tiêu là **không sót đoạn nào** (nhất là đoạn không lời) và rút ra thủ pháp dùng lại được.

Công cụ nằm cạnh file này (gọi là `$S`, đường dẫn đầy đủ). Mọi lệnh chạy bằng `py -3` thường, không cần thư viện Python thêm; cần `yt-dlp` và `ffmpeg`. Script chỉ in số và dòng lỗi.

Thư mục ra (gọi là `$R`): `py -3 $S/thu_muc.py <ten>` tạo và in đường dẫn (mặc định `F:\gen_video_data\kho-bien-kich\<ten>\`, đổi bằng `THU_MUC_KHO_BIEN_KICH` trong `.env` ở gốc thư mục). Tên đã có thư mục của phim khác thì hỏi tên khác.

**Việc xem hình giao hết cho trợ lý phụ (Agent).** Chat chính không Read ảnh, chỉ đọc chữ trợ lý phụ ghi ra.

## Bước 1. Tải phim và phụ đề

```
cd $R/tai-ve
yt-dlp -f "bv*[height<=480]+ba/b[height<=480]/b" --merge-output-format mp4 --write-info-json --write-thumbnail --convert-thumbnails jpg -o "phim.%(ext)s" <link>
yt-dlp --skip-download --write-auto-subs --write-subs --sub-langs "en,en-orig" --sub-format vtt -o "phim.%(ext)s" <link>
```

- Tải phim và phụ đề **hai lệnh riêng**; `--sub-langs "en.*"` kéo cả chục bản dịch và bị chặn 429.
- Phim không phải tiếng Anh: đổi `en` thành mã tiếng gốc (xem `language` trong `phim.info.json`).
- Không có phụ đề: máy chủ lấy transcriptapi (memory `lay-transcript-youtube`, không in key), lưu JSON vào `tai-ve/`; máy khác báo, chọn phim khác. Công cụ đọc được `.vtt`, `.srt`, `.json` (danh sách có `text`, `start`, `duration` hoặc `end`).
- Lấy thời lượng (giây, gọi là `$DAI`), tên, số view từ `phim.info.json` bằng một dòng Python, không đọc cả file.

## Bước 2. Khoảng không thoại

```
py -3 $S/khoang_khong_thoai.py tai-ve/phim.en.vtt --dai $DAI --ra khoang.json --thoai thoai.txt
```

In các khoảng không thoại từ 8 giây (cộng 90 giây đầu, 60 giây cuối), tổng giây xem dày; `thoai.txt` là thoại sạch có mốc giờ. Trợ lý phụ báo từ nhiễu mới (máy chép tiếng nhạc thành chữ, như "Heat") thì thêm vào `TU_NHIEU` trong script.

## Bước 3. Cắt khung và ghép lưới

```
py -3 $S/cat_khung.py tai-ve/phim.mp4 khoang.json . --day 2 --thua 10
```

Ghi `luoi/luoi_NNN.jpg` (4x3 ô, mỗi ô in mốc giờ vàng) và `luoi/muc-luc.txt` (mốc từng lưới, dày hay thưa). `--day` 1 đến 2 giây: phim ít thoại (xem dày trên 50% phim) dùng 2, phim nhiều thoại dùng 1,5.

## Bước 4. Trợ lý phụ xem và tả

Chia lưới thành phần khoảng 13 lưới (khoảng 5 đến 8 phút phim), mỗi phần một trợ lý phụ `general-purpose`, chạy song song trong một lượt. Ranh giới phần lấy từ `muc-luc.txt`. Lời giao mỗi trợ lý gồm:

- tên phim, thời lượng, đường dẫn `$R`, danh sách lưới của phần, cách đọc lưới (4 cột x 3 hàng, trái sang phải, mốc vàng góc trên trái), `thoai.txt` đọc trong phạm vi (được đọc từ đầu để nắm bối cảnh);
- phạm vi `m:ss` đến `m:ss`;
- ghi `$R/xem/phan-N.md`: bảng `| Mốc | Chuyện gì xảy ra (hình) | Thoại / âm | Khán giả cảm gì, biết gì hơn nhân vật, đang chờ gì |`, **mỗi dòng tối đa 20 giây, nối liền, phủ kín phạm vi, kể cả đoạn đen, chuyển cảnh, phong cảnh, chữ cuối**; tả ai, ở đâu, làm gì, cú máy đáng chú ý; mục "Khoảnh khắc đáng chú ý" (mốc + vì sao chạm); mục "Nhân vật và bối cảnh";
- chỉ tả theo hình và thoại, không suy diễn; không đưa tóm tắt nội dung phim cho trợ lý (để đo công cụ thật); ghi rõ nhân vật nói thật hay nói dối và ai tin, ai không (ăn mặc giản dị không phải "giả nghèo");
- trợ lý phần 1 xem thêm `tai-ve/phim.jpg` (thumbnail), ghi đầu file mục "Thumbnail": ai, đối đầu gì, chữ trên ảnh;
- trả lời chỉ 3 đến 5 dòng (đã ghi, số dòng, lưới có vấn đề), không chép bảng.

**Vá quãng thưa:** trợ lý phụ báo quãng nào "không có khung, tả theo thoại hay khung hai bên" thì gom các quãng đó vào `khoang-bu.json` (cùng dạng `khoang.json`), cắt `cat_khung.py ... bu --day 1.5 --thua 99999`, giao một trợ lý phụ xem `bu/luoi/` và sửa đúng các dòng đó trong `xem/phan-N.md`.

## Bước 5. Bảng nhịp thô và kiểm phủ kín

Ghép các phần thành `$R/bang-nhip-tho.md`: đầu file tên phim, link, thời lượng, số view, ngày bóc, mục "Lời hứa của tựa và thumbnail" (mỗi lời hứa một dòng, trả ở phút mấy, dòng bảng nào; chưa trả thì ghi "không trả"); rồi các bảng theo thứ tự; cuối file gộp "Khoảnh khắc đáng chú ý" và "Nhân vật và bối cảnh" (bỏ trùng giữa các phần). Ghép bằng script nhỏ, không chép tay.

```
py -3 $S/kiem_phu_kin.py bang-nhip-tho.md --dai $DAI
```

LỖI = quãng hơn 20 giây không dòng nào nhắc. Còn lỗi thì giao lại trợ lý phụ phần đó xem đúng các lưới của quãng lỗi (cắt dày hơn bằng `--day 1` nếu cần), sửa bảng, chạy lại tới **0 lỗi**. CẢNH BÁO (một dòng gộp hơn 60 giây) nên chia nhỏ nhưng không bắt buộc.

Soát nhanh: 90 giây đầu có tả mở màn không (ở đâu, ai, chuyện gì trước câu thoại đầu); mở màn không lời hay bị sót nhất.

## Bước 6. Bình luận khán giả (chỉ khi phim trên 1 triệu view)

Để **tìm** khoảnh khắc chạm, không làm điều kiện cho mục:

```
yt-dlp --skip-download --write-comments --extractor-args "youtube:max_comments=300,all,0,0;comment_sort=top" -o "tai-ve/binh-luan.%(ext)s" <link>
```

Lọc bình luận có mốc giờ hoặc nhiều lượt thích bằng script nhỏ (tối đa 40 dòng: lượt thích, mốc, 150 chữ đầu). Khoảnh khắc khán giả nhắc nhiều mà bảng tả sơ sài thì bổ sung.

## Bước 7. Bóc mục

Đọc `bang-nhip-tho.md` (một lần), rút ra mục theo ba nhóm:

- `khung`: cấu trúc cả phim, dùng ở bảng nhịp (thứ tự loại biến cố, nhịp vùi dập và hé, cách mở và đóng phim, chỗ đặt khoảnh khắc lớn, % thời gian).
- `khoanh_khac`: một cảnh hay một khoảnh khắc (cách gây sợ, thương, bất ngờ, ấm lòng trong một cảnh).
- `thoai`: cách dùng lời (ít lời mà nặng, lời lặp lại đổi nghĩa, im lặng thay lời...).

**Không** giới hạn số mục, **không** lọc "có ở hai phim". Viết mục nào có thể dùng lại cho phim khác cốt truyện.

Mỗi mục là một object JSON, đúng trường sau, không thêm trường lạ:

| Trường | Viết thế nào |
|---|---|
| `nhom` | `khung` / `khoanh_khac` / `thoai` |
| `hop_phim` | `it_thoai` / `nhieu_thoai` / `ca_hai` |
| `ten` | tên ngắn, không tên riêng, không chi tiết riêng của phim |
| `nguyen_ly` | bỏ hết tên riêng, sinh vật, đồ vật cụ thể vẫn đủ nghĩa; nói **vì sao khán giả phản ứng** |
| `cach_phim_goc` | phim nguồn làm thế nào, cụ thể, kèm mốc; kết câu "Không lặp lại y cách này." |
| `cach_khac` | danh sách **ít nhất 2** cách khác hẳn phim gốc (khác bối cảnh, khác đồ vật, khác giác quan), không phải biến thể nhỏ |
| `dat_o_dau` | đặt ở đâu trong phim (% hoặc đoạn), cần gieo gì trước |
| `dung_sai` | dùng sai thì hỏng thế nào (khán giả thấy gì) |
| `phim_nguon` | tên phim, giống nhau ở mọi mục của phim |
| `link` | link YouTube |
| `moc_gio` | `m:ss–m:ss` |

**Mỗi mục ghi đủ ba điều** trong trường sẵn có: `nguyen_ly` nói khán giả biết gì hơn nhân vật và vì thế đang chờ gì; `cach_phim_goc` ghi cả lời hứa nào của tựa hay thumbnail được trả ở đâu (`m:ss`), mục không dính tựa ghi "không trả lời hứa tựa"; `dat_o_dau` ghi phút trả lời hứa phải đạt. Mục `khung` dạng bảng đoạn: mỗi đoạn trong `cach_phim_goc` ghi mốc, khán giả biết gì, chờ gì.

Ghi cơ chế, không gán nhãn theo bề ngoài. Ví dụ phải tránh: "nhìn trộm qua cửa sổ" thành mọi phim đều nhìn trộm cửa sổ. Nguyên lý nói *cơ chế* (khán giả biết điều nhân vật chưa biết), cách khác đổi hẳn phương tiện (tiếng động phòng bên, vết chân trên tuyết, đồ vật bị xê dịch).

Ghi `$R/muc.json`, rồi kiểm (không nạp DB):

```
py -3 $S/kiem_muc.py $R/muc.json
```

Tới 0 lỗi. Mã thể loại (`the_loai`, không bắt buộc) ở `THE_LOAI` trong `luat_kho_bien_kich.py` (repo chính: `app/`, thư mục biên kịch: `cong-cu/`).

**Nạp kho (tự động, không hỏi):**

```
py -3 $S/nap_kho.py $R/muc.json --the-loai <mã>
```

Không có mã thể loại thì bỏ `--the-loai`. Máy chủ: script nạp thẳng vào kho, mục ở trạng thái chờ duyệt (trùng tên cùng phim thì bỏ qua, chạy lại không sao). Máy editor: script in dòng `MÁY EDITOR`, báo editor nhắn chủ dự án đúng dòng đó; `muc.json` đã nằm ở ổ chung, không gửi file.

## Báo cáo cuối

Ngắn: số khoảng không thoại, tổng giây xem dày; mở màn đã tả đủ chưa; số dòng bảng nhịp; số lỗi phủ kín (phải 0); số mục theo nhóm; đã nạp kho bao nhiêu mục mới (hay dòng MÁY EDITOR); đoạn nào trợ lý phụ báo khó xem.
