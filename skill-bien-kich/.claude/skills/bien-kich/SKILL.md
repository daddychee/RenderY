---
name: bien-kich
description: Viết kịch bản phim AI loại thường (Spec 40, Seedance; fantasy-drama, sinh-vat-bao-ve và niche khác trừ drama thoại): bảng hỏi hai lượt, dàn ý `00-nhip.md` theo khung niche (tựa và thumbnail, bảng nhịp, bảng phân clip, Gieo và gặt, Phần), anh/chị duyệt, trợ lý viết rồi trợ lý soát từng phần khoảng 7 phút, gộp ra kich-ban.md dán vào trang Phim mới. Dùng khi anh/chị nói "biên kịch", "viết kịch bản", "phim mới", hoặc gõ /bien-kich.
model: claude-opus-5-5
---

# Biên kịch: từ đề bài tới `kich-ban.md`

Mức suy nghĩ medium (khác thì `/effort medium`). Đối số: ý tưởng phim (bước 1), hay `<mã> tiếp`: đọc `BAN-GIAO.md` của phim, làm tiếp bước ghi ở đó. Phim drama nhiều thoại dùng `/bien-kich-drama`.

Luật câu chuyện ở `kien-thuc/khung/<niche>.md` (mục 0 Hợp đồng khán giả, mục 1 Nâng cấp điện ảnh, rồi bảng đoạn, nhịp, khoảnh khắc); khuôn cảnh, ngôn ngữ máy ở `kien-thuc/phan-canh.md`; ngân sách clip ở `kien-thuc/phan-clip.md`. Máy kiểm: `cong-cu/dan_y.py` (dàn ý, Gieo và gặt, Phần), `dem_phan_canh.py` (clip), `kiem_kich_ban.py` (luật web, gộp).

**Kết quả:** `<THU_MUC_PHIM>/<mã>/kich-ban.md` (`.env`; mã chữ thường, gạch nối), gộp từ `kich-ban/00-nhip.md`, `hoi-1.md`…, không sửa tay. Anh/chị dán vào **Phim mới** (phim đã tạo: **Dán lại kịch bản**).

**Token:** chat chính không Read file hồi; `00-nhip.md` Read đúng mục (`python cong-cu/muc_luc.py`); sửa bằng Edit. Quá 20 trợ lý trong một chat thì cập nhật `BAN-GIAO.md`, báo anh/chị mở chat mới gõ `/bien-kich <mã> tiếp`.

## Bước 1. Bảng hỏi, hai lượt

Đọc trọn khung niche trước lượt 1. Mỗi câu kèm gợi ý mặc định.

**Lượt 1:** niche (tên khung trong `kien-thuc/khung/`; chưa có khung thì theo `tu-web/L2-dao-dien-phim.md` mục 6 và báo anh/chị); phim mẫu (tựa, link) và thủ pháp phải giữ; tựa, thumbnail đã có chưa. Khung mục 0 còn dòng "(tạm, chờ editor)" thì hỏi thêm ba câu: tựa hứa gì và khán giả chờ thấy nó lúc nào; cảm xúc họ chờ nhất; một điều không được làm. Claude đề xuất 3 ý, mỗi ý: tựa tiếng Anh, thumbnail (ai, làm gì), nhịp trả tựa (không muộn hơn dòng `Trả tựa trước` của khung), khác phim mẫu ở đâu (nơi, vật, hành động chính), móc theo `moc-mo-phim.md` mục 2. Chép thủ pháp, không chép tình huống. Người, vật ở nơi hợp thân phận; một lý do kẹt, không chồng trùng hợp (CLAUDE.md "Logic").

Câu cuối lượt 1: clip **15 giây** (Seedvis, mặc định) hay **30 giây** (Mango, chỉ nhân viên; 325 credit một cảnh, khoảng 4.225đ; 22–48 phút một clip, bộ lọc hay chặn nhưng web tự gen lại; phim 30 phút khoảng 68 cảnh, khoảng 22.000 credit). Chọn 30 thì ghi `Clip: 30s` ở dòng đầu dàn ý, luật ở `kien-thuc/phan-canh-30s.md`; phần `[…]` ở các khuôn dưới chỉ ghi khi phim 30s.

**Lượt 2, sau khi chốt ý:**
1. Độ dài (mặc định 30 phút); tiếng lời bình và giọng (mặc định tiếng Anh, `elevenlabs_vzUquQTlMvdV6PkeYguD`); thoại ít hay nhiều.
2. Nhân vật theo vai của khung (người che chở, được che chở; người, sinh vật, thứ quý…): tên, tuổi, ngoại hình một câu, vết thương cũ.
3. Bối cảnh, các nơi, thời điểm.
4. Khán giả biết trước điều gì, bất ngờ đặt ở đâu (khung mục 1).
5. Kẻ ác và thang vùi dập: Claude đề xuất theo khung.
6. Trận: mấy trận, cỡ, nhịp nào, người yếu thế thắng nhờ gì.
7. Kết, cảm xúc để lại; kết mở cho phần sau không.

**Phim tới 5 phút:** một lượt hỏi, một phần.

## Bước 2. Dàn ý `kich-ban/00-nhip.md`

**Đọc** (không đọc thêm): `kien-thuc/moc-mo-phim.md` trọn; `kien-thuc/phan-clip.md` trọn; `phan-canh.md` mục "Chỗ ghi rõ để máy đếm"; mục lục `muc-luc-khung.md`, `muc-luc-khoanh-khac.md`, `muc-luc-thoai.md` của `kien-thuc/kho/<niche>/` (không có thì `fantasy-drama/`) và `kien-thuc/kho/chung/`, một lần. Chi tiết kho chỉ in khi cần cân mã: `python cong-cu/doc_kho.py <mã> …`. Có trận: `tran-danh.md` mục "Số clip", "Bậc". Phim 30s: thêm `phan-canh-30s.md`.

```
# <Tên phim>
Thể loại: <niche> · Dài: 30 phút · Lời bình: <tiếng, giọng> · Thoại: <ít | nhiều>[ · Clip: 30s]
## Tựa và thumbnail
Tựa: <tựa YouTube tiếng Anh>
Thumbnail: <ai, mặc gì, đang làm gì>
Phim mẫu: <tựa, link> · Thủ pháp giữ: <…> · Khác phim mẫu ở: <nơi, vật, hành động chính>
Trả tựa ở: N02
## Logline
## Cảm xúc chủ đạo
## Khoảnh khắc chạm
- N07 · chạm · <hành vi nhỏ thấy được> · khán giả <cảm xúc> · gieo ở N03
## Ba hồi
- Hồi 1 (N01–N06, ~15%): <một câu>
## Bảng nhịp
| Mã | % | Loại | Cảnh | Sự kiện | Vì nhịp | Cảm xúc khán giả | Mức |
## Bảng phân clip
## Gieo và gặt
| Mã | Loại | Điều | Gieo ở (bằng gì) | Gặt ở |
| G01 | lật | Sinh vật nhớ tiếng còi của cô bé | N03, cô thổi còi | N24 |
## Thang vùi dập
| Lần | Nhịp | Mất gì (thấy được) | Nặng hơn lần trước vì | Tự chọn? |
## Mô típ
| Mô típ | Loại (thoại, vật, âm thanh) | Gieo ở | Lặp ở | Trả ở |
## Cụm cố định
| Mã | Tên | Cụm tiếng Anh (nguyên văn) | Ghi chú |
## Phần
| Phần | Hồi | Nhịp | Phút | Clip |
```

- **Khung giữ thứ tự và tỉ lệ:** đoạn, % mỗi hồi, nhịp vùi dập và hé, chỗ khoảnh khắc lớn, cú lật, xả, kết theo khung. Tình tiết, nhân vật, thế giới tự sáng tác. Mã nhịp `N01`… liên tục; `N01` là Móc (Loại `Móc`, mức 4, `moc-mo-phim.md` mục 3). Loại: `Móc`, `Thiết lập`, `Diễn biến`, `Ngoặt lòng`, `Trận`. Mức 1–5, không ba nhịp cùng mức liền nhau, đỉnh mức 5 một lần. Khoảnh khắc chạm viết trước bảng nhịp (`chạm`, `lớn`, đúng một `cú lật lớn nhất`).
- **Sự kiện** tối đa 2 câu; mã khung `KBxx` ghi cuối ô (`(KB01)`); logic để ở Gieo và gặt. Nhịp quay lại mạch đã vắng quá 2 nhịp: cuối Sự kiện ghi `(nhắc: <điều>)` (trợ lý viết chỉ thấy nhịp của phần ±1).
- **Bảng phân clip** theo `phan-clip.md` luật 7–9 (6 clip mỗi phút, phim 30s 4,5 đơn vị; mỗi hồi một dòng ngân sách); mã khoảnh khắc, thoại, TP ở cột "Điểm chạm và thủ pháp"; cả phần khoảng 6 mã kho (trợ lý viết in đúng các mã ghi ở bảng nhịp và bảng này, mỗi mã khoảng 700 token). Rồi điền lại cột Cảnh và % của bảng nhịp.
- **Gieo và gặt:** loại `lật`, `dẫn sai`, `phi lý`, `vết`, `biết`, `vật`. Gieo ở mở bằng mã nhịp; Gặt ở: `N05`, `N26, N29`, `tới N06` (vết), `—` (phi lý). Cú lật, cách thắng, chứng cứ đều gieo trước bằng thoại, lời bình hay vật thấy rõ. Mỗi trận một dòng `lật` "thắng nhờ …". Vết ghi trái, phải của chính nhân vật. Dẫn sai mỗi phần nên có, ở mạch phụ. Mô típ (vật, âm thanh, câu) lặp 3–4 lần, lần cuối trả ở lúc quyết định.
- **Cụm cố định:** mọi nhân vật (mã NV, số con, nét nhận dạng, đại từ ở cột Tên), mỗi dạng hay cỡ của nhân vật đổi hình (kèm câu SIZE), mọi vật ở Mô típ hay Gieo và gặt. Người: tuổi, giới, tóc, áo (màu), một dấu riêng; hai người cùng giới gần tuổi khác màu tóc và áo. Sinh vật: màu, số chân, số cánh. Trẻ em: không skinny, barefoot, dirty, rags, torn, blood. Đổi đồ theo ngày, nơi, việc: mỗi bộ một dòng `dạng`, Ghi chú ghi khoảng nhịp. Ghi chú ngắn (khoảng nhịp, câu SIZE): trợ lý viết đọc cả bảng mỗi phần.
- **Phần** khoảng 7 phút (5–9, khoảng 42 clip; phim 30s khoảng 32 đơn vị, khoảng 15 cảnh), cắt ở ranh giới nhịp, không trùm hai hồi (hồi dưới 5 phút gộp với phần kề).

**Tự soát điều máy không kiểm** (khung mục 0–1, CLAUDE.md): móc và nhịp trả tựa đúng lời hứa của tựa, không muộn hơn khung; mọi người, vật ở mỗi nhịp trả lời "vì sao ở đây"; ai có mặt mà đứng yên thì vì sao; mỗi điều phi lý một lý do nói ra; mỗi trận "thắng nhờ gì", đòn hợp cỡ; mỗi đoạn (các clip liền cùng nơi, cùng lúc) một lần đổi thế; khán giả hiểu chỉ bằng màn hình (sinh vật không nói thì điều quan trọng qua thoại người, lời bình hay hình rõ). Rồi chạy tới hết LỖI (CẢNH BÁO, NHẮC: sửa, hay giữ có lý do):
- `py -3 cong-cu/dan_y.py kiem <phim>/kich-ban`
- `py -3 cong-cu/dem_phan_canh.py <phim>/kich-ban/00-nhip.md`

## Bước 3. Duyệt

Báo anh/chị tối đa 18 dòng: tựa, thumbnail, nhịp trả tựa (phút); logline; móc tóm 2 dòng; khoảnh khắc chạm và cú lật lớn nhất; khán giả biết trước gì, bất ngờ ở đâu; kẻ ác, trận và "thắng nhờ"; cụm tiếng Anh của nhân vật chính; số nhịp, số clip mỗi hồi so ngân sách, số phần; phim 30s: số cảnh 30s, cảnh 15s xen (% giây), tiền (325 credit một cảnh 30s); CẢNH BÁO còn giữ. Sửa theo ý anh/chị, rồi ghi `BAN-GIAO.md`:

```
# Bàn giao <mã>
Dàn ý: đã duyệt <ngày>. Niche, độ dài, lời bình[, clip 30s (Mango)][, trận thử]. Điều anh/chị dặn: <…>
## Phần
| Phần | Hồi | Nhịp | Phút | P đầu | File | Trạng thái |
| 1 | 1 | N01–N06 | 6,5 | P01 | hoi-1.md mới | chưa viết |
## Đề xuất bài học
```

P đầu của phần sau là P cuối phần trước cộng một (điền khi phần trước xong).

## Bước 4. Viết rồi soát từng phần

**Mặc định dừng sau phần 1:** viết, soát, gộp (bước 5), báo anh/chị gen thử và xem; viết phần 2 khi anh/chị bảo (dặn viết liền thì ghi vào BAN-GIAO). Lần lượt, không song song (trợ lý thêm dòng Cụm cố định, mã nơi `DD`; phần sau cần trạng thái cuối phần trước). Gọi Agent, chờ kết quả.

Viết, `subagent_type: viet-phan-bien-kich`:
```
Phim <mã>, thư mục <phim>/. Viết phần <n>: hồi <h>, nhịp <Nxx–Nyy>, khoảng <số> clip, mã bắt đầu P<…>; <mở file kich-ban/hoi-h.md mới | viết tiếp kich-ban/hoi-h.md>.
Có trận: <T1 cỡ chính, N12 | không>. Có P01: <có | không>.
[Clip: 30s (đọc phan-canh-30s.md).]
Điều anh/chị dặn (nguyên văn từ BAN-GIAO.md): <…>
```

Soát, `subagent_type: soat-phan-bien-kich`:
```
Phim <mã>, thư mục <phim>/. Soát phần <n>: kich-ban/hoi-h.md, cảnh P<a>–P<b>, nhịp <Nxx–Nyy>.
Cảnh cuối trước phần: <Pc ở hoi-g.md | không có>. Báo cáo của trợ lý viết: <dòng lệch dàn ý, CẢNH BÁO còn giữ>.
[Clip: 30s (đọc phan-canh-30s.md).]
```

Sau mỗi trợ lý, tự chạy (còn LỖI thì giao lại đúng trợ lý đó kèm dòng lỗi):
- `py -3 cong-cu/dan_y.py phan <phim>/kich-ban/hoi-h.md --phan <n>`
- `py -3 cong-cu/dem_phan_canh.py <phim>/kich-ban/hoi-h.md --nhip <phim>/kich-ban/00-nhip.md`
- `py -3 cong-cu/kiem_kich_ban.py <phim> --dang-viet <h>`

Sau soát: `py -3 cong-cu/danh_lai_ma.py <phim>` (mã P liền, bỏ đuôi `-b`) rồi chạy lại ba lệnh. Cập nhật bảng Phần. Đổi cốt truyện (nhịp, kẻ ác, dòng Gieo và gặt) thì hỏi anh/chị trước phần kế; lệch nhỏ thì sửa `00-nhip.md` và cột Nhịp của các phần sau.

## Bước 5. Gộp

1. `py -3 cong-cu/kiem_kich_ban.py <phim>`: sạch LỖI thì máy gộp `kich-ban.md` (gồm các phần đã viết). LỖI thì giao trợ lý soát.
2. `py -3 cong-cu/dem_phan_canh.py <phim>/kich-ban.md`: không LỖI; CẢNH BÁO thì sửa hay ghi lý do vào `BAN-GIAO.md`.
3. Báo anh/chị tối đa 10 dòng: mỗi phần một dòng (nhịp, số clip, đỉnh), CẢNH BÁO giữ và vì sao, điều cần quyết. Ghi `BAN-GIAO.md` (đã gộp tới phần nào).

**Sửa sau khi dán:** phần chưa dán thì giao `soat-phan-bien-kich` danh sách sửa, rồi `danh_lai_ma.py` và gộp lại; phần đã dán thì sửa trên web (chèn, bỏ cảnh làm lệch mã: hỏi chủ dự án). Điều đáng nhớ ghi `BAN-GIAO.md` mục "Đề xuất bài học"; `kien-thuc/tu-web/`, `kien-thuc/kho/`, thư viện hành động là bản chép, không sửa.
