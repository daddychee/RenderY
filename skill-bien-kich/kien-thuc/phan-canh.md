# Luật viết phân cảnh (bản 2, Spec 40 C)

Mỗi phân cảnh là **một clip** 10 hoặc 15 giây (20 đến 30 giây chỉ ở đoạn editor yêu cầu, mục Luật 1–6; phim `Clip: 30s`: `phan-canh-30s.md`). Việc chỉ được 2 giây trên màn hình là bị lướt; clip thừa làm phim lê thê. Số clip đi theo **mức** của nhịp, không theo độ chi tiết của bảng nhịp.

## Bước làm

1. **Bảng phân clip** (bước dàn ý, trước khi viết cảnh): ngân sách, bảng, thứ tự cắt ở `phan-clip.md` (luật 7–9).
2. **Viết cảnh** đúng theo bảng, từng phần.
3. **Chạy** `python cong-cu/dem_phan_canh.py <file hồi> --nhip <00-nhip.md>` (bản gộp bỏ `--nhip`) sau mỗi phần: sửa tới hết LỖI; mỗi CẢNH BÁO thì sửa hay ghi lý do.
4. **Soát** ngay sau khi viết mỗi phần: trợ lý soát theo `soat-phan-canh.md`, sửa tại chỗ.

## Khuôn một cảnh

```
## P07 · Tên ngắn · 15s · N03
- Mục đích kể chuyện: <loại> · <việc, một câu>  |  Bối cảnh, thời điểm: DD02 <tên nơi>, <giờ, thời tiết, ánh sáng>  |  Có mặt: NV01, NV09 (3 người), NV02 dạng 2 (chỉ thấy bóng), <câu SIZE khi có hai nhân vật khác cỡ>
- Ý đạo diễn: khán giả phải cảm thấy gì; đỉnh cảnh ở giây mấy
- Cách dựng: số shot, loại shot, hard cut; cú máy lớn nếu có
- Thủ pháp đắt: TPxx <tên> vì …  (mã ở `tu-web/the-loai-thu-phap.md`; không mã nào hợp thì "tự dựng: <tả ngắn>", không bịa mã; mã kho KBxx dùng ở cảnh ghi cuối dòng)
- Hành động theo nhịp: 0–4s <cỡ cảnh>: <việc thấy được> (tiếng: …) → 4–9s cận, *đẩy vào*: … → 9–15s …  (máy in nghiêng, mục Ngôn ngữ máy; thoại viết "trong ngoặc kép", tối đa 3 từ một giây của nhịp: câu dài thì kéo dài nhịp hay tách câu, không kéo sang shot sau)
- Khung cuối gài: <khung cuối>  |  Cầu nối tiếng sang P08: <…>
- Lời bình: không  (hoặc "câu đọc" (số từ, đặt ở giây …))
```

- Mã cảnh liền `P01`, `P02`… qua mọi hồi, không đuôi `-b`. Tiêu đề có thời lượng (`10s` hay `15s`; phim `Clip: 30s` thì `30s`, `phan-canh-30s.md`) và **đúng một** mã nhịp.
- Mỗi hồi mở bằng `# Hồi n: tên`, cuối hồi có `## Bảng trạng thái liên tục` và `## Để viết hồi sau`.
- Ba ô trên dòng đầu cách nhau đúng `  |  `.

## Chỗ ghi rõ để máy đếm

1. **Loại** (đầu ô Mục đích, trước ` · `): `việc`, `sau đỉnh`, `đe dọa` (luật 2), `nối` (luật 3), `đệm` (thời gian trôi, nơi nghỉ sau biến cố lớn), `lớn k/n <tên>` (clip k trong n clip của một khoảnh khắc lớn, ví dụ `lớn 1/2 lộ mặt`), `lật k/n` (cú lật lớn nhất, cả phim một chuỗi).
2. **Việc** (sau ` · `): một câu, một việc. Không dùng `;`. Không nối hai việc bằng "rồi", "và".
3. **Nơi** (đầu ô Bối cảnh): mã `DD01`, `DD02`… Cùng nơi thì cùng mã suốt phim. Clip nối đường đi ghi `DD02 → DD05 <tên đường>`. Clip loại khác chỉ có một mã.

## Luật 1–6

Luật 7–9 (ngân sách, bảng phân clip, thứ tự cắt, bảng Phần) ở `phan-clip.md`, đọc ở bước dàn ý.

**1. Một clip, một việc kể chuyện.** Việc là một **thay đổi tình thế** người xem nhận ra: biết thêm, mất, được, quyết. Việc không phải động tác.
- Một vế ở cột Sự kiện của bảng nhịp **không mặc nhiên là một clip**: đếm thay đổi tình thế, không đếm vế. Chi tiết hình (vật rơi, vết thương, một cái liếc) và các động tác cùng dẫn tới một thay đổi là **shot trong một clip**.
- Rượt đuổi, móc mở phim: mỗi clip một nấc nguy mới (tình thế xấu hẳn đi), 2 đến 4 động tác một clip.
- Clip việc mặc định 15 giây; 10 giây cho clip nối và việc thật ngắn. Việc quan trọng nhất của nhịp mức 4–5 được hai clip.
- **Clip 20 đến 30 giây chỉ khi editor yêu cầu** đúng đoạn (phim `Clip: 30s` khác: `phan-canh-30s.md`) (ghi vào lời giao trợ lý viết phần). Clip dài là clip **thêm**: 30 giây mang việc của hai clip 15 giây (6–10 shot hard cut), không giãn việc cũ cho đủ giây.
- Ví dụ: bảng nhịp ghi "thợ mỏ bị kẹt, gọi to, đèn tắt, nghe tiếng gõ, đào vách, thấy tay bạn": không phải sáu clip mà hai việc, `việc · thợ mỏ bị kẹt trong bóng tối` và `việc · anh đào thủng vách, thấy tay người bạn còn sống`; các động tác kia là shot.

**2. Sau đỉnh và đe dọa.** Sau đỉnh của **nhịp mức 4–5 hay khoảnh khắc lớn**: một clip `sau đỉnh` (mặt phản ứng, thân thể gục, người xung quanh sững lại), **mỗi đỉnh một clip**; clip đỉnh dừng ngay khi đỉnh xảy ra.
- Sau **cú lật** (bí mật lộ, lời buộc tội, phản bội) clip `sau đỉnh` là **vòng phản ứng**: 10 giây, không thoại, 3 cận liền: người bị lật, người gây ra, người chứng, mỗi cận một nét khác. Sinh vật không nói thì phản ứng bằng mắt (nheo, giãn đồng tử), tai (cụp, dựng), thân (lùi, xù lông, quẫy đuôi), cận đủ 3 giây.
- Nhịp mức 1–3 thì phản ứng là shot cuối của clip việc. Móc (`N01`) không có `sau đỉnh`: cảnh hạ nhịp ngay sau móc làm việc đó (`moc-mo-phim.md` mục 3).
- Kẻ đe dọa, đám đông hiện diện (đứng xa nhìn, bám theo, xì xào) là loại `đe dọa`, dùng được ở mọi mức, **mỗi nhịp tối đa một clip**.
- Ví dụ: `việc · lá thư báo tin con trai mất` → `sau đỉnh · người cha ngồi sụp xuống bậc cửa, lá thư rơi khỏi tay`; ở nhịp khác: `đe dọa · gã chủ nợ đứng cuối ngõ nhìn vào, quay đi`.

**3. Đổi nơi thì có clip nối.** Nơi A sang nơi B: chèn một clip `nối` 10 giây, không thoại, được mang lời bình. Toàn cảnh nơi B, hay đường đi từ A sang B khi có người bám theo, có việc gấp. Ví dụ: `nối · cô giáo ôm cặp vội qua cầu gỗ về trường, trời đã tối` · `DD03 → DD06 cầu gỗ`.

**4. Nói ra hoặc cho thấy.** Quyết định, bản án, lời hứa, lý do phải có câu thoại hay hình rõ. Hệ quả chỉ diễn bằng hình thì thêm một câu thoại ngắn nói ra. Lý do hành động có trước hành động. Ví dụ: `việc · ông trưởng làng tuyên: "Mai nó phải rời làng."`.

**5. Cảnh đánh cho thấy quá trình.** Mỗi pha đổi thế một clip; số clip, bậc, khối thiết kế trận ở `tran-danh.md`. Khi viết shot thêm:
- Máy cầm tay. Clip đầu trận mở bằng trung rộng: ai đứng đâu (trái, phải), vật quanh (vách, đồ đã gieo).
- Mỗi đòn một shot cận: tay, chân, móng trái hay phải **của chính người đánh**, hướng, trúng bên nào **của chính người bị đánh**. Clip 15 giây khoảng 2–3 đòn.
- Người yếu thế (trẻ con, người già, sinh vật non) không thắng kẻ to hơn bằng sức: lý do thấy trong shot (né cho địch lao vào vách, đồ đã gieo, đồng minh tới), khớp dòng `lật` "thắng nhờ …" ở bảng Gieo và gặt.

**6. Khoảnh khắc lớn cho nhiều clip.** Khoảnh khắc lớn cho **2 clip nối nhau**, clip sau đi tiếp, không lặp. Có hai loại, đều là `lớn`:
- **Khoảnh khắc hình:** lộ mặt, biến hình, cứu người, trả thù, nhử phần sau.
- **Khoảnh khắc chạm:** nhân vật chính chọn giữ hay bỏ người thân, mất người thân, nhận ra hay đoàn tụ người thân. Nhận ra bằng cột Cảm xúc khán giả (thương, xót, đau, vỡ òa) đi cùng một lựa chọn hay mất mát về người thân. **Mức bảng nhịp chấm thấp vẫn tính.** Khoảnh khắc chạm luôn có thêm một clip `sau đỉnh` vỡ bằng thân thể (khóc thành tiếng, ôm chặt, gục), không chỉ nét mặt hay khóc câm, dựng **biểu cảm ba nhịp**, mỗi nhịp một shot: trước (cố giữ), đỉnh (vỡ), sau (cố lấy lại), kèm cử chỉ nhỏ (nuốt khan, siết ngón, cắn môi, nhìn đi chỗ khác). Lựa chọn thì clip `lớn 1/2` là giằng xé thấy được (ôm lại, đẩy ra, tay run), `lớn 2/2` là quyết, có câu nói ra.
- Ví dụ: `lớn 1/2 lộ mặt · người lạ tháo mũ, là người anh mất tích` rồi `lớn 2/2 lộ mặt · em gái nhận ra anh, lao tới ôm`; `lớn 1/2 bán nhà · bà cụ ôm cột nhà, gỡ tay ra rồi lại ôm` → `lớn 2/2 bán nhà · bà ký giấy: "Bán đi."` → `sau đỉnh · bà gục vào vai con gái khóc thành tiếng`.

**Cú lật lớn nhất phim** là chuỗi **6 clip** (chỉ xuống 4 khi hồi đã chạm ngân sách):
1–2. **chạm đáy** hai clip: một clip ở cùng nhân vật đang tắt dần (người xem ở bên trong: chìm, ánh tắt, mắt khép), một clip người thân gào gọi hay gục xuống;
3. **nhớ lý do** (hồi tưởng, câu nói cũ);
4–5. **bùng** hai clip (dấu hiệu đầu, rồi phá ra);
6. **lộ diện**: hình mới trọn vẹn, người khác phản ứng, một câu nói ra (thoại; phim ít thoại thì lời bình).

**Không làm:** gộp hai nhịp cho đủ 15 giây (nhịp ngắn thì clip 10 giây); để nhịp 0 clip; lặp một clip hay tách một việc thành nhiều clip cho đủ số.

## Ngôn ngữ máy (Seedance)

Clip Seedance nhiều shot: mỗi khoảnh khắc một cách nhìn có ý đồ, chọn theo khoảnh khắc (đã thử ở phim drama). Viết ở ba ô: **Hành động theo nhịp** ghi cỡ cảnh rồi động tác máy in nghiêng (`4–9s cận, *đẩy vào*: …`); **Cách dựng** ghi cú lớn nếu có; **Thủ pháp đắt** ghi mã TP của cú chính (đủ ở `tu-web/kho-thu-phap.md`).

**Luật viết:**
- Mỗi shot **một** động tác máy, chỉ ở shot từ 3 giây; shot ngắn hơn máy đứng yên.
- Cú cần thời gian (vòng, nâng cao, lùi xa, chuyển nét) đặt ở shot **không thoại** hay **sau câu thoại**; nói trong lúc máy vòng thì vòng nửa chừng.
- Người nói lúc máy đẩy vào: mặt hướng về máy, chếch nghiêng, không quay sang người ngoài khung. Câu dài không đặt ở shot dưới 3 giây.
- Shot trao vật (tháo, đưa, thả vào tay, đút mồi) không gắn cú máy: máy tách thêm một cắt, mất vật.
- Cú lớn (dolly zoom, vòng, nâng cao) tối đa một lần mỗi **đoạn** (các clip liền cùng nơi, cùng lúc), không lặp ở hai đoạn liền; dolly zoom một lần mỗi phần.

| Khoảnh khắc | Cụm máy (in nghiêng) | Mã |
|---|---|---|
| Vào nơi mới | *bám lưng* người bước vào; *trượt ngang* qua tiền cảnh (lá, vách đá) mở ra cả nơi | TP35 |
| Bị theo dõi | *khung trong khung* qua khe cửa, kẽ lá | TP40 |
| Kẻ mạnh, sinh vật lớn, người cứu tới | *góc thấp, máy ngước lên* từ chân (móng) tới mặt; bóng *ngược sáng* ở cửa hang | TP34, TP41 |
| Đối đầu leo thang | qua vai; bên thắng *góc thấp*, bên thua *góc cao*, đảo góc từ shot lật thế; *chuyển nét* sang người nghe | TP23 |
| Đi cùng nhau | *máy lùi* trước mặt hai người (hay người và sinh vật) đang đi | TP36 |
| Nhận ra, quyết | *đẩy vào* tới cận mặt, mắt sinh vật; *zoom nhanh* lúc phát hiện | TP18, TP45 |
| Bị lật thế, sững | *dolly zoom* mặt người bị lật; kẻ ác thua: *góc cao* | TP37 |
| Đỉnh cảm xúc riêng | *vòng từ* sau lưng ra trước mặt, shot không thoại; *trong gương*, mặt nước | TP44, TP42 |
| Bí mật trong tay | đặc tả tay giấu vật *rõ nét tiền cảnh*, *chuyển nét* sang mặt người đã biết | TP38 |
| Bỏ lại một mình | *lùi ra* rồi *nâng lên*, người nhỏ dần giữa nơi chốn | TP19 |

**Dựng theo khoảnh khắc:**
- **Shot định vị:** clip đầu đoạn hay khi người mới vào: `shot 1 trung rộng <nơi>, A bên trái, B bên phải`, kèm một cụm mở đoạn ở bảng. Sau clip nối, clip kế vẫn cho ai đứng đâu.
- **Cỡ leo theo căng:** trung → qua vai → cận → đặc tả (mắt, tay, vật) khi tới đỉnh; hạ về trung khi hé (hài, ấm).
- Vòng phản ứng: luật 2. Biểu cảm ba nhịp: luật 6.
- **Đặc tả vật** mỗi lần gieo hay gặt (bảng Gieo và gặt): `shot n đặc tả <vật như Cụm cố định>`, đủ 2 giây, rõ trong khung.
- **Thời tiết, ánh sáng** ở nhịp lớn (mức 4–5, đáy, khép): ghi ở ô Bối cảnh, thời điểm (mưa ở đáy, nắng chiều ở cảnh khép), giữ suốt đoạn.

## Khán giả hiểu chỉ bằng màn hình

**Đoạn** như mục trên (là "cảnh" ở CLAUDE.md "Khán giả hiểu").
- **Neo:** trong 15 giây đầu mỗi đoạn, màn hình cho biết ở đâu (shot định vị), ai (lần đầu thì tên kèm vai, bằng thoại hay lời bình), chuyện gì đang treo. Vào muộn, ra sớm, không bỏ neo.
- **Nối:** hai đoạn liền nối được bằng "vì… nên…" trên màn hình. Cảnh đầu mỗi phần (từ phần 2) nhắc hay trả lời câu hỏi treo cuối phần trước.
- **Nhắc mạch:** nhịp có `(nhắc: …)` (mạch vắng quá 2 nhịp) thì đầu nhịp có một câu nhắc chuyện tới đâu, bằng thoại hay lời bình.
- **Đổi thế:** mỗi clip một lần đổi thế (luật 1); đoạn không đổi gì thì gộp hay cắt.
- **Ai biết gì:** không ai dùng điều chưa thấy, chưa nghe trên màn hình.
- **Lời và mặt:** lời (thoại, lời bình) mang điều hình không nói được (luật 4); cảm xúc để mặt, tay, thân sinh vật và cú máy diễn, không câu nào nói lại điều mặt vừa cho thấy. Câu đắt nhất đoạn có vài giây lặng sau nó: shot không thoại, cận người nghe (sau cú lật là vòng phản ứng, luật 2; cú máy ở bảng trên). Ví dụ: cô bé nói với rồng non "Tớ sẽ quay lại trước trăng tròn." rồi 3 giây cận mắt rồng chớp chậm, đầu dụi vào tay cô; không thêm "Nó tin mình rồi."
- **Trái, phải:** vết, vật ghi trái hay phải **của chính nhân vật** (vai trái, chân sau phải), giữ đúng ở mọi cảnh và ở Bảng trạng thái liên tục.

## Phim clip 30 giây

Phim `Clip: 30s`: đọc thêm `phan-canh-30s.md`. Phim 15s bỏ qua.
