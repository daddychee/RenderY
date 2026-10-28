# Phim Muse: khuôn, cái Muse làm được, cách viết clip (Spec 63 B, C)

Nguồn sự thật cho skill `/bien-kich-muse`. Mỗi clip là **một cú Muse 10 giây**: web viết prompt Muse thẳng từ clip, máy vẽ khung đầu (GPT Image 2) từ cùng ảnh nơi và tờ nhân vật cho mọi clip của cảnh, robot gen. Thoại giữ nguyên giọng Muse; lời nghĩ và lời ngoài hình do máy đọc (ai33, giọng nhân vật) rồi ghép sau. Khuôn là giao ước với web: không tự chế dòng mới.

**Máy lo, không cần nhớ:** `py -3 cong-cu/kiem_muse.py <file phần>` kiểm khuôn (`Loại phim: phim_muse`, mã liền, không dòng `Máy:`, tên `Khung:` có ở `Có mặt:`), một lượt mỗi clip (`Thoại:`, `Lời nghĩ:` hay `Lời ngoài hình:`), thoại 3–25 từ, lời nghĩ và lời ngoài hình tới 25 từ, người nói, người nghĩ có ở `Khung:`, người có lời ngoài hình không có ở `Khung:`, trần người trong khung; nhắc chữ bộ lọc, cú máy Muse không làm được, hai người mà máy động, sinh vật to, clip/phút (6), lời nghĩ quá 10%. `py -3 cong-cu/dan_y_drama.py phan <file phần>` kiểm Cụm cố định, dòng `Gieo, gặt:`, shot định vị đầu cảnh. Chạy cả hai tới hết LỖI; NHẮC thì sửa, hay giữ và ghi lý do. File này chỉ ghi điều máy không kiểm được.

## 1. Khuôn file

Thư mục, phần đầu phim, Cụm cố định (cả thay đồ theo ngày), tiêu đề cảnh `## Cxxx · nơi · lúc · Nxx`, `Có mặt:`, tên clip: **như `drama-thoai.md` mục 1** (đọc mục đó, bỏ ba clip mẫu). Khác drama:

```
# Phần 1 · Bó hoa cuối · 10 phút
## C003 · Bếp nhà Dee · đêm · N02
Có mặt: Dee, Hattie

### P014 · Dee hỏi chuyện chiếc nhẫn
Khung: Dee
Hình: cận vai Dee ngồi bên bàn bếp, đèn bàn ấm chiếu thẳng mặt, mắt nhìn về phía bà Hattie ngoài khung bên trái máy. Máy đẩy vào rất chậm.
Thoại: Dee (nghẹn, nhỏ): "You told me it was lost. You told me for ten years."

### P015 · Hattie im lặng
Khung: Hattie
Hình: cận vai Hattie, đèn bàn ấm chiếu mặt; mắt né sang bên rồi nhìn lại Dee ngoài khung, môi mím. Máy đứng yên.

### P016 · Dee nghĩ
Khung: Dee
Hình: cận Dee, môi khép, mắt ướt nhìn chiếc nhẫn trên bàn rồi ngước lên, hít một hơi dài như cố nuốt giận. Máy đứng yên.
Lời nghĩ: Dee (nhỏ, đau): "She kept it from me for ten years. Why?"
```

- Không dòng `Máy:`: mọi clip Muse 10 giây.
- `Khung:` mọi người thấy trong hình (web gửi ảnh và tờ nhân vật theo dòng này); để trống (`Khung:`) với clip không người (nơi, vật, sinh vật không tên).
- Mỗi clip tối đa **một** dòng lời: `Thoại:` (người trong khung nói), `Lời nghĩ:` (người trong khung nghĩ), hay `Lời ngoài hình: Tên (cách nói): "câu"` (người không thấy mặt nói: gọi từ phòng bên, qua điện thoại, trên clip không người; tên đó không ghi ở `Khung:`). `(cách nói)` 1–3 từ tiếng Việt.
- `Hình:` tiếng Việt, một đoạn liền, **một cú máy liền**: cỡ cảnh, ai ở đâu trong khung, mặt hướng về đâu, ánh sáng trên mặt, rồi một câu máy (`Máy đứng yên.`, `Máy đẩy vào rất chậm.`). Không cắt, không "shot 1, shot 2".

## 2. Muse làm tốt, Muse hỏng (đo 17–19/10)

**Tốt (chọn những cú này):** cận vai một người nói, kể cả nói nghẹn, khóc nhẹ; cận phản ứng không thoại; trung cảnh hai người máy đứng yên; toàn cảnh đông người không thoại; người ôm, dắt sinh vật tới cỡ ngựa; rồng phun lửa lên trời; đẩy vào chậm.

**Hỏng (tránh, viết cách khác):**
- Hai người cùng có thoại trong một clip: sai người nói, giọng lẫn. Người ngoài khung có câu mà trong khung có người khác: người trong khung nói thay.
- Câu 1–2 tiếng ("Why?", "No."): mất hay hai người nói chung. Câu cụt thì ghép thành 3 từ trở lên ("No. Not today.") hay để mặt nói.
- Góc rất thấp, rất cao, từ trên xuống; chuyển nét đồ vật sang người; máy lùi sang chỗ khác; cú nhiều bước; máy cầm tay rung.
- Toàn thân quay lưng (leo cầu thang, bước đi xa): đổi tóc, đổi người. Cần người rời đi thì cận mặt người ở lại nhìn theo.
- Cúi xuống, quay đi trong clip có thoại: mất mặt, Muse cho người khác nói.
- Đồ vật nhỏ, logo, hoa văn, chữ trên biển đổi màu, nhân đôi. Vật quan trọng gọi tên bằng lời, không bắt khán giả đọc chữ trên hình.
- Muse đôi khi tự cắt giữa clip: không viết được gì chặn, editor gen lại.

## 3. Đối đáp bằng clip lẻ

- **Mỗi lượt nói một clip** (shot, đối shot), web dựng ghép. Người nói ở `Khung:` một mình (cận vai), mặt hướng về người nghe ngoài khung, lệch máy ít ("nhìn về phía Hattie ngoài khung bên trái máy"). Giữ trái phải nhất quán cả cảnh: A nhìn sang trái máy thì B nhìn sang phải máy.
- Người nghe phản ứng = clip không thoại cận mặt người nghe (`Khung:` một tên). Câu đắt luôn có một clip phản ứng sau nó.
- Hỏi–đáp cụt: không gộp; mỗi câu một clip, câu dưới 3 từ thì thêm chữ hay chuyển thành phản ứng không lời.
- Tràng dài quá 25 từ: chia nhiều clip cùng người, ngắt ở chỗ ngắt câu, đổi cỡ (trung rồi cận) hay xen một clip mặt người nghe.
- Muốn thấy cả hai: clip **trung cảnh hai người, máy đứng yên**, một người nói (ghi cả hai ở `Khung:`), người kia `nghe, môi khép`. Dùng cho shot định vị, lúc trao vật, lúc ôm.
- Người không thấy mặt mà có câu (gọi từ phòng bên, điện thoại, giọng trên clip nơi chốn): dòng `Lời ngoài hình:`, `Hình:` tả người trong khung nghe, phản ứng (môi khép). Máy đọc câu bằng giọng đọc không lên được cảm xúc mạnh: câu ngắn, giọng thường; câu cần khóc, gào thì đưa người đó vào khung nói `Thoại:`.

## 4. Giữ mặt, ánh sáng

- **Cận vai là chính**; trung cảnh cho định vị, trao vật. Mặt nhìn về phía máy suốt clip (lệch ít về người nghe). Hành động trong clip thoại không làm mặt rời máy: không cúi nhìn cốc, không quay đi, không ngồi xuống. Việc như thế thành clip riêng không thoại, cú ngắn.
- **Đêm và ngược sáng:** `Hình:` ghi nguồn sáng ấm chiếu thẳng mặt (đèn bàn, đèn bếp, đèn đường trước mặt, ánh nến); không có thì da tối xám. Ngày cạnh cửa sổ: người quay mặt về cửa sổ, hay có đèn trong phòng chiếu mặt.
- Mọi clip của một cảnh cùng nơi, cùng giờ, cùng áo (web vẽ khung đầu chung nguồn); chỗ ngồi đứng của từng người giữ nguyên trừ khi có clip đứng dậy, đi.
- Khóc: "một hai giọt nước mắt", không mặt ướt đẫm (khung đầu người đang khóc bị chặn).

## 5. Lời nghĩ

- Muse không làm được môi khép mà có tiếng: clip lời nghĩ chỉ quay **mặt người đang nghĩ**, tiếng nghĩ máy ghép sau bằng giọng nhân vật. `Hình:` tả nét mặt, ánh mắt, hơi thở **theo ý câu nghĩ** (nghĩ "I can't let her see" thì nuốt khan, mỉm cười gượng), môi khép suốt clip, một người ở `Khung:`.
- Giọng đọc lời nghĩ không chỉnh được cảm xúc: câu nghĩ **cùng chiều cảm xúc với nét mặt** ở `Hình:` (mặt khóc nức nở mà câu nghĩ cứng rắn thì lệch).
- Câu nghĩ phải ngắn hơn đoạn mặt im: **tối đa khoảng 12 từ** (đọc dưới 4,5 giây) khi clip còn việc khác; `Hình:` cả clip là mặt im thì tới khoảng 18 từ.
- Dùng cho điều nhân vật giấu không có người tâm sự; không gọi tên cảm xúc mặt đã cho thấy. Có người tâm sự thì nói thành thoại với họ (`drama-thoai.md` mục 5 vẫn đúng ở đây).

## 6. Nhịp, thủ pháp một cú

- Khoảng 6 clip mỗi phút (máy đo). Mỗi cảnh: clip đầu định vị (trung rộng hay toàn: nơi, ai đứng đâu, máy đứng yên), rồi cận; đỉnh cảnh là câu đắt + clip phản ứng không lời.
- Neo cảnh, nối cảnh, nhắc mạch, gọi tên kèm vai: như `drama-thoai.md` mục 6 (bỏ phần % giây có lời: mỗi clip Muse một lượt).
- **Một cú mỗi clip**, chọn theo khoảnh khắc: đẩy vào rất chậm (câu đắt, lúc nhận ra), đứng yên (hai người, vật, phản ứng), lia chậm theo người đi ngang trong cùng chỗ, trượt ngang chậm (toàn cảnh đông người). Thủ pháp mạnh làm bằng chuỗi clip: **vòng phản ứng** = 2–3 clip cận ngắn không thoại của những người nghe sau câu bom; **lộ vật** = clip cận vật không người rồi clip mặt người thấy vật.
- Đặc tả vật (thư, tờ séc, chiếc nhẫn) là clip không người (`Khung:` trống), máy đứng yên hay đẩy vào chậm; chữ trên vật không cần đọc được.

## 7. Bộ lọc, hành động

Chặn một lần thì tài khoản đó mất cả ngày. Không viết đánh nhau, máu, vết thương mở, xác, đau đẻ, xô ngã, thú cắn. Xung đột thân thể (khi dàn ý buộc phải có): giằng đồ, tát chạm má, nắm cổ tay, đẩy cửa; ngã thì viết "trượt, va vào kệ". Đuổi bắt, trận: kể bằng mặt người chạy (cận, máy lia chậm), tiếng động, kết quả sau đó; không quay đòn. Sinh vật không to hơn ngựa, có vật so sánh trong khung.

## 8. Ghi chú nối

Như `drama-thoai.md` mục 7.
