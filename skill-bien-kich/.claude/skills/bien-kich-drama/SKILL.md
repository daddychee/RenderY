---
name: bien-kich-drama
description: Viết kịch bản phim drama nhiều thoại (loại drama_thoai, Spec 44, clip Seedance, mức 75% có Veo, mức 30s Mango): bảng hỏi, dàn ý, anh/chị duyệt, trợ lý viết và soát từng phần 10 phút, gộp ra kich-ban.md dán vào trang Phim mới. Dùng khi anh/chị nói "drama thoại", "phim drama da đen", "kịch bản drama nhiều thoại", hoặc gõ /bien-kich-drama.
model: claude-opus-5-5
---

# Biên kịch drama thoại: từ đề bài tới `kich-ban.md`

Mức suy nghĩ medium (khác thì `/effort medium`). Đối số: ý tưởng phim (bước 1), hay `<mã> tiếp`: đọc `BAN-GIAO.md` của phim, làm tiếp bước ghi ở đó.

Luật câu chuyện ở `kien-thuc/khung/drama-da-den.md`; khuôn, máy, clip ở `kien-thuc/drama-thoai.md`. Máy kiểm: `cong-cu/dan_y_drama.py` (dàn ý, Cụm cố định, Gieo, gặt), `cong-cu/kiem_drama.py` (clip, bản chép của web).

**Kết quả:** `<THU_MUC_PHIM>/<mã>/kich-ban.md` (`.env`; mã chữ thường, gạch nối), gộp từ `kich-ban/00-dan-y.md`, `phan-01.md`…, không sửa tay. Anh/chị dán vào **Phim mới**, loại Drama thoại (phim đã tạo: **Dán lại kịch bản**).

**Token:** chat chính không Read `phan-NN.md`; dàn ý Read đúng mục (`python cong-cu/muc_luc.py`); sửa bằng Edit. Quá 20 trợ lý trong một chat thì cập nhật `BAN-GIAO.md`, báo anh/chị mở chat mới gõ `/bien-kich-drama <mã> tiếp`.

## Bước 1. Bảng hỏi, hai lượt

Đọc trọn khung trước lượt 1. Mỗi câu kèm gợi ý mặc định.

**Lượt 1:** phim mẫu (tựa, link) và mô-típ mở phải giữ; tựa, thumbnail đã có chưa. Claude đề xuất 3 ý, mỗi ý: tựa tiếng Anh, thumbnail (ai, mặc gì, làm gì), phút trả tựa (không quá 4), khác phim mẫu ở đâu (nơi, vật, hành động chính). Chép thủ pháp, không chép tình huống. Nơi mở theo "Nơi mở hợp thân phận thật" (khung mục 0, điều 5): một lý do kẹt, không chồng trùng hợp.

**Lượt 2, sau khi chốt ý:**
1. Độ dài 60–80 phút (mặc định 70).
2. Nạn nhân mở phim: ai (thường là người sắp đặt, ăn mặc giản dị, không giả nghèo), quan hệ với kẻ quyền lực, sự thật nào được mớm ở đầu phim.
3. Cặp chính: nữ chính nghèo, kẻ quyền lực (tên Mỹ, tuổi, nghề, vết thương cũ); nỗi khổ nữ chính giấu.
4. Bí mật khán giả biết trước: gì, vỡ khoảng 65–85%.
5. Kẻ ác từng vòng: Claude đề xuất 3–5 người, xử tăng bậc.
6. Trận: mấy trận (0 được), cỡ (xô xát, chính, cuối: `tran-danh.md` mục Số clip), mốc nào, ai biết đánh và vì sao, người yếu thế thắng nhờ gì.
7. Mức Seedance: **100%** (khoảng 3.350 credit mỗi 10 phút), **75%** (clip một người nói câu trung tính dùng Veo, khoảng 2.650; Veo kém cảm xúc, hay gen lại) hay **30 giây Mango** (*chỉ nhân viên*; mọi clip `Seedance 30s`, khoảng 6.500 credit mỗi 10 phút, ~84.500đ). Khuyên 100%.

**Phim thử dưới 10 phút:** một lượt hỏi, thêm phim phải kiểm được gì (ghi `## Yêu cầu phim thử` cuối dàn ý); một kẻ ác, mốc 1–1,5 phút, một phần.

## Bước 2. Dàn ý `kich-ban/00-dan-y.md`

Đọc thêm: `drama-thoai.md` mục 1 (bỏ ba clip mẫu) và mục 6; `kien-thuc/kho/drama-da-den/muc-luc-khoanh-khac.md`, `muc-luc-thoai.md` một lần. Mã khung có sẵn trong khung. Không đọc mục lục `kho/chung/`, `kho/drama-thoai/`, không đọc chi tiết kho.

```
# <Tên phim>
Loại phim: drama_thoai
Seedance: 100%
Thể loại: drama-da-den · Độ dài: 70 phút · Tỉ lệ: 16:9

## Tựa và thumbnail
Tựa: <tựa YouTube tiếng Anh>
Thumbnail: <ai, mặc gì, đang làm gì>
Phim mẫu: <tựa, link> · Thủ pháp giữ: <…> · Khác phim mẫu ở: <nơi, vật, hành động chính>
Trả tựa ở: N03
## Logline
## Bí mật khán giả biết trước
<gì; khán giả biết ở Nxx; suýt lộ ở Nxx, Nxx; vỡ ở Nxx>
## Nhân vật và bối cảnh
| Tên (dùng ở Khung) | Vai | Tuổi, ngoại hình một câu | Giọng (tuổi, độ trầm, chất giọng) |
### Nơi
| Nơi (tên dùng ở tiêu đề cảnh) | Một câu tả |
## Cụm cố định
| Mã | Tên | Cụm tiếng Anh (nguyên văn) | Ghi chú |
## Kẻ ác từng vòng
| Kẻ ác | Vào ở | Bị xử ở | Bị xử thế nào (tăng bậc) |
## Mở phim (0–4 phút)
| Giây | Ai làm gì | Câu thoại hay lời nghĩ chính |
## Bảng mốc
| Mốc | Phút | Ngày | Đoạn khung | Việc (tối đa 2 câu) | Ức trả ở | Mã kho |
| N01 | 0–1,5 | Ngày 1 sáng | Format | … | N02 | KB196, KB283 |
## Gieo và gặt
| Mã | Loại | Điều | Gieo ở (bằng gì) | Gặt ở |
| G01 | lật | Bà nói quên ví, cháu đang mang tiền tới | N01, thoại bà | N03 |
## Phần
| Phần | Tên | Mốc | Phút |
```

- **Mốc:** đoạn và %, phút theo khung mục 2; mật độ, ức trả, vùi rồi hé theo mục 3. Việc tối đa 2 câu, logic để ở Gieo và gặt. Mã kho: mã khung, khoảnh khắc, thoại của mốc, cả phần khoảng 6 mã (trợ lý viết in đúng các mã này, mỗi mã khoảng 700 token).
- **Dòng `Seedance:`** theo câu 7: `100%`, `75%` hay `30s` (30 giây Mango: mọi clip `Máy: Seedance 30s`, viết theo `drama-thoai.md` mục 3).
- **Mở phim** theo khung mục 0 và đoạn Format. `Trả tựa ở:` trỏ mốc bắt đầu không quá phút 4.
- **Gieo và gặt:** loại `lật`, `dẫn sai`, `phi lý`, `vết`, `biết`, `vật`. Gieo ở mở bằng mã mốc; Gặt ở: `N05`, `N26, N29`, `tới N06` (vết), `—` (phi lý). Cú lật, chứng cứ, cách thắng đều gieo trước bằng lời hay vật gọi tên. Mỗi trận một dòng `lật` "thắng nhờ …". Vết ghi trái, phải của nhân vật. Mỗi phần ít nhất một `dẫn sai` gặt trong phần, chỉ ở mạch phụ.
- **Phần** 8–12 phút, cắt ở ranh giới mốc. **Phần đầu phim** (bốn dòng đầu, `Nhân vật và bối cảnh`, `Cụm cố định`) web đọc để gen ảnh: giữ đúng tiêu đề, cột. Tên tiếng Anh, một kiểu suốt phim.
- **Cụm cố định** theo `drama-thoai.md` mục 1; vai nghèo hay giàu mỗi món đồ một dấu thấy được, "quá lên"; thay đồ theo ngày, nơi, việc: mỗi bộ một dòng `dạng`, Ghi chú ghi các mốc mặc, lập ngay từ dàn ý.

**Tự soát điều máy không kiểm:** 4 phút đầu chỉ phục vụ format (không hồi tưởng, chứng cứ bằng hình, trận); ai có mặt mà đứng yên thì vì sao, nói thành lời; quan hệ gia đình khớp; hệ quả hợp đời sống Mỹ (tiền, luật, bệnh viện, CPS, cảnh sát), mỗi điều phi lý một câu lý do; vì sao người, vật ở đó (người giàu ở nơi nghèo phải có lý do hợp tính, nói thành lời); khán giả hiểu chỉ bằng màn hình (CLAUDE.md "Khán giả hiểu"): phim nhiều mạch thì mỗi mốc một mạch chính, mốc quay lại mạch đã vắng quá 2 mốc ghi cuối Việc `(nhắc: <điều>)`, vì trợ lý viết chỉ thấy mốc của phần ±1. Rồi `py -3 cong-cu/dan_y_drama.py kiem <phim>/kich-ban` tới hết LỖI (NHẮC: sửa, hay giữ có lý do).

## Bước 3. Duyệt

Báo anh/chị tối đa 18 dòng: tựa, thumbnail, phút trả tựa; logline; Mở phim tóm 3 dòng; mức Seedance; nguyên cụm tiếng Anh của nạn nhân mở phim và cặp chính (tuổi, tóc, đồ, dấu nghèo hay giàu đủ "quá lên"); bí mật; kẻ ác; trận; số mốc, phần; mốc lớn. Sửa theo ý anh/chị, rồi ghi `BAN-GIAO.md`:

```
# Bàn giao <mã>
Dàn ý: đã duyệt <ngày>. Điều anh/chị dặn: <…>
## Phần
| Phần | Mốc | Phút | P đầu | C đầu | Trạng thái |
| 1 | N01–N05 | 10 | P001 | C001 | chưa viết |
## Đề xuất bài học
```

Mã ba chữ số; P, C đầu của phần sau là mã cuối phần trước cộng một.

## Bước 4. Viết rồi soát từng phần

**Mặc định dừng sau phần 1:** viết, soát, gộp (bước 5), báo anh/chị gen thử và xem; viết phần 2 khi anh/chị bảo (dặn viết liền thì ghi vào BAN-GIAO). Lần lượt (viết n, soát n, rồi n+1), gọi Agent chờ kết quả.

Viết, `subagent_type: viet-phan-drama`:
```
Phim <mã>, thư mục <phim>/. Viết phần <n>: mốc <Nxx–Nyy>, <phút> phút, mã bắt đầu P<…>, C<…>.
File: <phim>/kich-ban/phan-<nn>.md (mới). Phần trước: <phim>/kich-ban/phan-<nn-1>.md | không có.
Điều anh/chị dặn (nguyên văn từ BAN-GIAO.md): <…>
Trận trong phần: T<n> cỡ <…> ở N<xx> | không có.
```

Soát, `subagent_type: soat-phan-drama`:
```
Phim <mã>, thư mục <phim>/. Soát phần <n>: <phim>/kich-ban/phan-<nn>.md, mốc <Nxx–Nyy>.
Phần trước: <phim>/kich-ban/phan-<nn-1>.md | không có. Báo cáo của trợ lý viết: <dòng lệch dàn ý, NHẮC còn giữ>.
```

Sau mỗi trợ lý, tự chạy `py -3 cong-cu/kiem_drama.py <file phần>` và `py -3 cong-cu/dan_y_drama.py phan <file phần>`; còn LỖI thì giao lại đúng trợ lý đó kèm dòng lỗi. Cập nhật bảng Phần. Đổi cốt truyện (mốc, kẻ ác, dòng Gieo và gặt) thì hỏi anh/chị trước phần kế; lệch nhỏ thì sửa dàn ý.

## Bước 5. Gộp

1. `py -3 cong-cu/dan_y_drama.py dau <phim>/kich-ban` (chép lại phần đầu phim), `py -3 cong-cu/kiem_drama.py gop <phim>/kich-ban -o <phim>/kich-ban.md`, rồi `py -3 cong-cu/dan_y_drama.py phan <phim>/kich-ban.md`: hết LỖI. Thiếu cụm thì thêm dòng vào dàn ý; lỗi clip thì giao trợ lý soát.
2. Báo anh/chị tối đa 10 dòng: dòng tóm tắt từng phần, NHẮC giữ và vì sao, điều cần quyết; tiền gen mỗi 10 phút theo mức (giá ở bước 1 câu 7).
3. Ghi `BAN-GIAO.md` (đã gộp tới phần nào).

**Sửa sau khi dán:** phần chưa dán thì giao `soat-phan-drama` danh sách sửa, rồi gộp lại; phần đã dán thì sửa nhỏ trên web. **Chèn trận vào phim đã dán** (anh/chị nhờ): giao `viet-phan-drama` viết clip trận kèm khối vào đúng chỗ của `phan-nn.md` (cảnh mới, mã tạm `P045-b`, `C009-b`), chạy `py -3 cong-cu/dan_y_drama.py danh-ma <phim>/kich-ban` (mã P, C liền cả phim), soát, gộp như bước 5, sửa bảng Phần, báo anh/chị bấm **Dán lại kịch bản** (web ghép theo nội dung: clip cũ giữ ảnh, video, sao). Điều đáng nhớ ghi `BAN-GIAO.md` mục "Đề xuất bài học".
