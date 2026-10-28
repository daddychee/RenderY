---
name: bien-kich-muse
description: Viết kịch bản phim Muse (loại phim_muse, Spec 63; mỗi clip một cú Muse 10 giây, một người nói, khung đầu chung nguồn): bảng hỏi, dàn ý, anh/chị duyệt, trợ lý viết và soát từng phần 10 phút, gộp ra kich-ban.md dán vào trang Phim mới. Dùng khi anh/chị nói "phim Muse", "kịch bản cho Muse", hoặc gõ /bien-kich-muse.
model: claude-opus-5-5
---

# Biên kịch phim Muse: từ đề bài tới `kich-ban.md`

Mức suy nghĩ medium (khác thì `/effort medium`). Đối số: ý tưởng phim (bước 1), hay `<mã> tiếp`: đọc `BAN-GIAO.md` của phim, làm tiếp bước ghi ở đó. Phim Muse là loại chỉ nhân viên dùng.

Luật câu chuyện ở khung thể loại (`kien-thuc/khung/drama-da-den.md` hay `fantasy-drama.md`); khuôn và cách viết clip ở `kien-thuc/muse-phim.md`. Máy kiểm: `cong-cu/dan_y_drama.py` (dàn ý, phần đầu phim, Cụm cố định, dòng Gieo, gặt; dùng chung với drama), `cong-cu/kiem_muse.py` (clip, bản chép của web).

**Kết quả:** `<THU_MUC_PHIM>/<mã>/kich-ban.md` (`.env`; mã chữ thường, gạch nối), gộp từ `kich-ban/00-dan-y.md`, `phan-01.md`…, không sửa tay. Anh/chị dán vào **Phim mới** (web tự nhận loại Phim Muse từ dòng `Loại phim:`).

**Token:** chat chính không Read `phan-NN.md`; dàn ý Read đúng mục (`python cong-cu/muc_luc.py`); sửa bằng Edit. Quá 20 trợ lý trong một chat thì cập nhật `BAN-GIAO.md`, báo anh/chị mở chat mới gõ `/bien-kich-muse <mã> tiếp`.

## Bước 1. Bảng hỏi, hai lượt

**Thể loại hợp Muse:** drama thoại (drama da đen), fantasy có sinh vật tới cỡ ngựa. Ý tưởng hành động, đánh nhau, quái vật khổng lồ: nói nhẹ "Muse chặn cảnh đánh và làm hỏng sinh vật to, phim này hợp Seedance (`/bien-kich-drama`, `/bien-kich`)", rồi đề xuất bản bớt hành động hay đổi skill. Đọc trọn khung thể loại trước lượt 1. Mỗi câu kèm gợi ý mặc định.

**Lượt 1:** phim mẫu (tựa, link) và mô-típ mở phải giữ; tựa, thumbnail đã có chưa. Claude đề xuất 3 ý, mỗi ý: tựa tiếng Anh, thumbnail (ai, mặc gì, làm gì), phút trả tựa (không quá 4), khác phim mẫu ở đâu. Chép thủ pháp, không chép tình huống. Ý nào cũng sống bằng **mặt người nói và nghe** (Muse mạnh ở cận một người), không cần cảnh động.

**Lượt 2, sau khi chốt ý:**
1. Độ dài 30–70 phút (mặc định 30).
2. Nạn nhân mở phim (drama) hay người mở phim (fantasy): ai, sự thật nào được mớm ở đầu phim.
3. Cặp chính (tên Mỹ, tuổi, nghề, vết thương cũ); nỗi khổ giấu. Fantasy: sinh vật (loài, cỡ không quá ngựa, màu một câu).
4. Bí mật khán giả biết trước: gì, vỡ khoảng 65–85%.
5. Kẻ ác từng vòng: Claude đề xuất 3–5 người, xử tăng bậc **bằng lời, giấy tờ, người có quyền** (không đánh).
6. Xung đột thân thể: mặc định không; cần thì chỉ mức `muse-phim.md` mục 7.

**Phim thử dưới 10 phút:** một lượt hỏi, thêm phim phải kiểm được gì (ghi `## Yêu cầu phim thử` cuối dàn ý); một kẻ ác, một phần.

## Bước 2. Dàn ý `kich-ban/00-dan-y.md`

Đọc thêm: `muse-phim.md` mục 1–3; `kien-thuc/kho/<thể loại>/muc-luc-khoanh-khac.md`, `muc-luc-thoai.md` một lần. Mã khung có sẵn trong khung. Không đọc chi tiết kho.

Khuôn như dàn ý drama (mục tiêu đề, cột giữ đúng, `dan_y_drama.py` đọc), khác bốn dòng đầu (không dòng `Seedance:`):

```
# <Tên phim>
Loại phim: phim_muse
Thể loại: drama-da-den · Độ dài: 30 phút · Tỉ lệ: 16:9

## Tựa và thumbnail
Tựa: … / Thumbnail: … / Phim mẫu: … · Thủ pháp giữ: … · Khác phim mẫu ở: … / Trả tựa ở: N03
## Logline
## Bí mật khán giả biết trước
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
## Gieo và gặt
| Mã | Loại | Điều | Gieo ở (bằng gì) | Gặt ở |
## Phần
| Phần | Tên | Mốc | Phút |
```

- **Mốc, Mở phim, Gieo và gặt, Phần, Cụm cố định** viết như `/bien-kich-drama` bước 2 (`.claude/skills/bien-kich-drama/SKILL.md`, Read đúng mục "Bước 2" khi chưa quen). Mốc lật khoảng 2 phút; mỗi phần ít nhất một `dẫn sai` gặt trong phần.
- **Nơi ít, ở lâu:** mỗi nơi một ảnh nơi chốn web vẽ, mọi clip của cảnh vẽ khung đầu từ ảnh đó. Phần 10 phút dùng 3–6 nơi; nơi tối thì Một câu tả ghi nguồn sáng (đèn bàn, đèn đường).
- **Cụm cố định:** mọi người thấy trong khung; mỗi bộ đồ một dòng `dạng`, Ghi chú ghi mốc mặc (tờ nhân vật vẽ theo dòng này).

**Tự soát điều máy không kiểm:** như `/bien-kich-drama` bước 2 (format 4 phút đầu, ai đứng yên vì sao, hệ quả hợp đời sống Mỹ, vì sao người, vật ở đó, khán giả hiểu chỉ bằng màn hình); thêm: không mốc nào cần đánh, ngã, máu, sinh vật to hơn ngựa; cú lật nào cũng làm được bằng câu nói, giấy tờ, vật đưa ra trước mặt người. Rồi `py -3 cong-cu/dan_y_drama.py kiem <phim>/kich-ban` tới hết LỖI.

## Bước 3. Duyệt

Báo anh/chị tối đa 18 dòng: tựa, thumbnail, phút trả tựa; logline; Mở phim tóm 3 dòng; nguyên cụm tiếng Anh của cặp chính; bí mật; kẻ ác; nơi; số mốc, phần; mốc lớn. Sửa theo ý anh/chị, rồi ghi `BAN-GIAO.md` (khuôn như `/bien-kich-drama` bước 3: Dàn ý đã duyệt, bảng Phần, Đề xuất bài học). Mã ba chữ số; P, C đầu của phần sau là mã cuối phần trước cộng một.

## Bước 4. Viết rồi soát từng phần

**Mặc định dừng sau phần 1:** viết, soát, gộp (bước 5), báo anh/chị dán thử và xem; viết phần 2 khi anh/chị bảo. Lần lượt (viết n, soát n, rồi n+1), gọi Agent chờ kết quả.

Viết, `subagent_type: viet-phan-muse`:
```
Phim <mã>, thư mục <phim>/. Viết phần <n>: mốc <Nxx–Nyy>, <phút> phút, mã bắt đầu P<…>, C<…>.
File: <phim>/kich-ban/phan-<nn>.md (mới). Phần trước: <phim>/kich-ban/phan-<nn-1>.md | không có. Khung thể loại: kien-thuc/khung/<…>.md
Điều anh/chị dặn (nguyên văn từ BAN-GIAO.md): <…>
```

Soát, `subagent_type: soat-phan-muse`:
```
Phim <mã>, thư mục <phim>/. Soát phần <n>: <phim>/kich-ban/phan-<nn>.md, mốc <Nxx–Nyy>. Khung thể loại: kien-thuc/khung/<…>.md
Phần trước: <phim>/kich-ban/phan-<nn-1>.md | không có. Báo cáo của trợ lý viết: <dòng lệch dàn ý, NHẮC còn giữ>.
```

Sau mỗi trợ lý, tự chạy `py -3 cong-cu/kiem_muse.py <file phần>` và `py -3 cong-cu/dan_y_drama.py phan <file phần>`; còn LỖI thì giao lại đúng trợ lý đó kèm dòng lỗi. Cập nhật bảng Phần. Đổi cốt truyện thì hỏi anh/chị trước phần kế; lệch nhỏ thì sửa dàn ý.

## Bước 5. Gộp

1. `py -3 cong-cu/dan_y_drama.py dau <phim>/kich-ban`, `py -3 cong-cu/kiem_muse.py gop <phim>/kich-ban -o <phim>/kich-ban.md`, rồi `py -3 cong-cu/dan_y_drama.py phan <phim>/kich-ban.md`: hết LỖI.
2. Báo anh/chị tối đa 10 dòng: dòng tóm tắt từng phần (công cụ ước chi khung đầu + máy đọc lời nghĩ, lời ngoài hình; Muse không tốn credit, thoại giữ giọng Muse), NHẮC giữ và vì sao, điều cần quyết.
3. Ghi `BAN-GIAO.md` (đã gộp tới phần nào).

**Sửa sau khi dán:** phần chưa dán thì giao `soat-phan-muse` danh sách sửa, rồi gộp lại; phần đã dán thì sửa trên web. Điều đáng nhớ ghi `BAN-GIAO.md` mục "Đề xuất bài học".
