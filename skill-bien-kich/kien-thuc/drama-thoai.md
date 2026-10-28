# Drama thoại: khuôn, chọn máy, cách viết clip (Spec 44 B, C)

Nguồn sự thật cho skill `/bien-kich-drama`. Khuôn là giao ước với web: đổi khuôn phải đổi cả công cụ và web, không tự chế dòng mới.

**Máy lo, không cần nhớ:** `py -3 cong-cu/kiem_drama.py <file phần>` kiểm dòng `Máy:`, `Seedance:`, trần từ (Veo 18 từ, Seedance 3 từ mỗi giây gồm cả lời nghĩ), clip `Seedance 30s` (mỗi shot có số giây, cộng đủ 30), luật clip Veo, tên `Khung:` có ở `Có mặt:`, dòng thiếu; nhắc % Seedance, clip/phút, lời nghĩ. `py -3 cong-cu/dan_y_drama.py phan <file phần>` kiểm Cụm cố định (có tuổi, đủ tên), dòng `Gieo, gặt:`, nhắc vết thiếu trái/phải. Chạy cả hai tới hết LỖI; NHẮC thì sửa, hay giữ và ghi lý do vào báo cáo. File này chỉ ghi điều máy không kiểm được.

## 1. Khuôn file

- Thư mục phim `<THU_MUC_PHIM>/<mã>/kich-ban/`: `00-dan-y.md`, `phan-01.md`, `phan-02.md`… (hai chữ số). Mọi phần viết từ dòng `# Phần n · tên · 10 phút`. `phan-01.md` có thêm **phần đầu phim** ở trên, do `py -3 cong-cu/dan_y_drama.py dau <phim>/kich-ban` chép từ dàn ý: bốn dòng đầu, `## Nhân vật và bối cảnh` (bảng Nhân vật, `### Nơi`), `## Cụm cố định`. Web đọc để gen ảnh nhân vật; thiếu thì web tự đoán.
- **Cụm cố định** (`| Mã | Tên | Cụm tiếng Anh (nguyên văn) | Ghi chú |`): mọi nhân vật thấy trong khung (kể cả vai phụ một cảnh), mã `NV01`… theo thứ tự bảng Nhân vật, cột Tên là tên ở Khung kèm đại từ (she, he). Cụm tiếng Anh 30–60 từ, theo thứ tự: tuổi bằng số (`about 24`, `in his early thirties`), giới, dáng, da, nét mặt, tóc (màu, kiểu), đồ (màu, kiểu), dấu riêng có trái, phải của chính nhân vật (`on the left side of his neck`). Cột ngoại hình của bảng Nhân vật nói cùng điều bằng tiếng Việt, không trái nhau.
- **Drama da đen:** cặp chính và người khán giả thương đẹp, trẻ: cụm mở bằng `Beautiful`/`Handsome`, nam chính trông dưới 35, không tóc bạc, quầng mắt, nếp nhăn. Nét khó ưa chỉ cho kẻ ác. Hai người cùng giới, gần tuổi khác tóc, màu áo.
- **Thay đồ theo ngày, nơi, việc** (anh/chị dặn 02/10): người có mặt nhiều ngày không mặc một bộ suốt phim. Mỗi bộ một dòng cùng mã, Tên ghi `Nia (she), dạng 2`, cụm viết lại đủ mặt, tóc với đồ mới, Ghi chú ghi mọi mốc mặc bộ đó (`N10–N14, N19`) để mốc nào cũng có đúng một bộ. Đồ hợp logic: cùng ngày giữ một bộ (trừ khi có lý do như đi tiệc, bị ướt bùn); người nghèo ít đồ nên lặp lại bộ cũ, người giàu ít lặp; đồ ở nhà, đi làm, đi lễ, dạ tiệc khác nhau; đồ mượn, đồ cứu được nói lý do ở Ghi chú. Đồ bẩn, ướt trong một cảnh không thêm dạng, ghi ở `Hình:`.
- Cảnh `## Cxxx · nơi · lúc · Nxx`: nơi viết **y từng chữ** như cột Nơi của dàn ý (web lấy làm ảnh nơi chốn); lúc là sáng, trưa, chiều, tối, đêm; `Nxx` là mốc chính của dàn ý mà cảnh phục vụ. Mã C và mã P đánh liền cả phim.
- `Có mặt:` mọi người có trong cảnh, tên **y từng chữ** như cột Tên của dàn ý (`Grandma Ruth` không thành `Ruth`).
- Clip `### Pxxx · <việc>`: tên là việc của clip, một cụm ngắn.
- `Khung:` ghi **mọi người thấy trong hình**, kể cả vai qua vai hay bóng mờ ở mép khung (web gửi ảnh theo dòng này); người nói và người nghĩ phải có ở đây.
- `Hình:` tiếng Việt, một đoạn liền. Mỗi lượt thoại một dòng riêng **bắt đầu bằng `Thoại:`**, ngoặc kép thẳng; lời nghĩ `Lời nghĩ: Tên: "câu"`:

```
### P187 · Tasha hỏi chuyện tiền, Marcus lật bài
Máy: Seedance 15s
Khung: Tasha, Marcus
Hình: shot 1 qua vai Marcus góc cao nhìn xuống, vai anh ở mép phải, Tasha ngồi rõ nét bên trái khung, tay phải cầm tờ sao kê, môi run, mắt ngấn nước. Shot 2 qua vai Tasha góc thấp nhìn lên, Marcus đứng bên phải khung, cười khẩy, hàm bạnh. Shot 3 cận Marcus cúi xuống, máy đẩy vào rõ tới cận mặt khi anh nói chậm từng chữ.
Thoại: Tasha (nhỏ, run): "Where did the money go, Marcus? All of it?"
Thoại: Marcus (cười khẩy): "To my wife."
Thoại: Marcus (chậm, lạnh): "My real one. In Atlanta."

### P188 · Vòng phản ứng sau câu bom
Máy: Seedance 10s
Khung: Tasha, Marcus, Dee
Hình: shot 1 cận Tasha bên trái khung, môi hé, hơi thở nghẹn, tờ sao kê tuột khỏi tay phải. Shot 2 cận Marcus bên phải khung, khóe môi nhếch, nhìn xuống cô. Shot 3 Dee rõ nét tiền cảnh ở cửa bếp, tay trái bịt miệng, mắt mở to, Tasha và Marcus mờ phía sau; chuyển nét sang Tasha.

### P189 · Tasha nghĩ
Máy: Seedance 10s
Khung: Tasha
Hình: cận Tasha, môi khép, nuốt khan, nước mắt dâng lên rồi lăn xuống má trái. Máy đẩy vào chậm.
Lời nghĩ: Tasha: "Ten years. I signed everything he handed me."
```
- Cuối mỗi phần `## Ghi chú nối` (mục 7).

## 2. Chọn máy theo mức ở dòng `Seedance:` của dàn ý

- **`Seedance: 100%`** (mặc định): mọi clip `Seedance 10s` hay `Seedance 15s`.
- **`Seedance: 75%`**: `Veo 8s` **chỉ** cho clip 1 người trong khung nói 1 câu giọng trung tính (đưa tin, hỏi han, chuyển tiếp, chào, rời đi), động tác nhỏ, không đồ vật chính; khoảng 1 clip Veo trong 3 clip. Mọi clip khác Seedance.
- **`Seedance: 30s`** (*chỉ nhân viên*, chạy Mango): mọi clip `Seedance 30s`, viết theo mục 3 (clip 30 giây), khoảng 2 clip mỗi phút. Veo là LỖI; clip Seedance 10, 15 giây máy NHẮC, giữ khi có lý do.
- **Luôn Seedance**, ở mọi mức: clip phản ứng, lời nghĩ, câu đắt, cảm xúc rõ (khóc, sững, giận, run, nghẹn), từ 2 người trong khung, đồ vật chính (sao kê, hoa tai, nhẫn), hành động, chạm người. Veo diễn cảm xúc kém, hay hỏng đồ vật.
- Lưỡng lự thì Seedance.

## 3. Clip Seedance

1. **15 giây gộp 2–3 nhịp liền** (lượt nói, mặt người nghe, phản ứng) thành 3–5 shot nối bằng hard cut, mỗi shot ít nhất 2,5 giây. 10 giây cho 1–2 nhịp, 2–3 shot. **Clip 30 giây** (editor yêu cầu, hay phim toàn clip `Seedance 30s` chạy Mango): 4–6 nhịp, khoảng 8–9 shot 2,5–4,5 giây (clip trận: mục 9) ghi số giây `shot 1 (3 giây)`. Cắt như người dựng phim, không chia hai nửa: mỗi cắt có lý do (theo ánh nhìn, theo động tác, câu rồi mặt người nghe); mỗi shot ghi ai nói (`nói gằn`, câu đặt lên mặt người nghe thì `giọng X ngoài khung`). Đừng tách mỗi lượt hỏi–đáp ra một clip.
2. `Hình:` ghi `shot 1 …`, `shot 2 …`; mỗi shot: cỡ và góc (cận, trung, qua vai X), ai bên trái, ai bên phải, rồi nét mặt. Chỉ cắt thẳng, không mờ dần, không chồng mờ.
3. **Cảm xúc ghi rõ ở mọi clip:** nét mặt cụ thể và diễn biến (môi run rồi mím chặt; nước mắt dâng lên rồi lăn xuống; cười tắt dần, hàm siết); đỉnh cảm xúc theo ba nhịp ở mục 8. Chỉ ghi "sững", "cộc" thì clip ra mặt trống. Không viết "mắt đỏ" (máy vẽ tròng đỏ): "mắt ngấn nước". Khinh, mỉa ghi "mép nhếch một bên, mắt không cười, nhìn từ trên xuống" (chỉ ghi "khinh khỉnh" thì ra mặt cười thân thiện). Người trong `Khung:` mà không nói: tả họ làm gì (nghe, né mắt, siết tay).
4. **Giữ trục:** trong một cảnh, mỗi người giữ một bên khung (A trái, B phải); qua vai A thì vai A ở mép trái, B rõ nét bên phải. Người mới bước vào thì ghi bên nào.
5. **Cú máy theo khoảnh khắc** (thực đơn mục 8): ghi ngay trong shot đó (`shot 2 góc thấp sát đất, máy ngước lên từ giày tới mặt Leon`), không gom một cụm cuối `Hình:`. Mỗi clip Seedance ít nhất một shot có cú máy hay góc ở mục 8; tối đa hai cú máy động một clip (clip 30 giây khoảng 4), các shot còn lại đứng yên cho rõ mặt. Máy đứng yên trọn clip chỉ khi chủ ý (khoảng lặng, cực cận mắt). Máy cầm tay chỉ cho cảnh giằng co, đánh nhau.
6. Không tả lại mặt, tóc, áo (ảnh nhân vật gen theo Cụm cố định), chỉ ghi điều đã đổi (áo ướt, mắt sưng). Nền chỉ nêu khi có việc (cửa sổ mưa). Vật quan trọng gọi cùng một cụm mỗi lần (`chiếc hoa tai vàng hình giọt nước`).
7. **Vết, vật ghi trái/phải của chính nhân vật** (`má trái`, `tay phải cầm`) ở `Hình:` **mọi clip** thấy chúng, khớp dòng `vết`, `vật` của bảng Gieo và gặt; vết còn tới mốc ghi ở cột Gặt ở (`tới N06`).

## 4. Clip Veo (chỉ mức 75%)

- Một cú máy liền: không "cắt sang", không đổi góc. Câu đầu cỡ và góc, khung 1 người; cú máy ghi một cụm cuối: đứng yên, đẩy vào, lùi ra, lia chậm, máy lùi trước người đang đi (thực đơn nhiều shot mục 8 chỉ cho Seedance).
- Tả động tác nhỏ thấy được (đứng dậy, quay đi, mở cửa bước ra), giọng trung tính ở `(cách nói)` (bình thản, nhẹ, lễ phép).
- Câu ngắn dưới khoảng 10 từ: thêm một động tác sau câu (nhìn xuống, quay đi) để 8 giây không trống; editor cắt đuôi.

## 5. Thoại, tràng dài, lời nghĩ, lời tự kể

- Tiếng Anh Mỹ đời thường của niche, câu ngắn: trung vị 6 từ mỗi lượt. Khuôn một cảnh: hỏi–đáp cụt 1–7 từ, leo thang, **một tràng ở đỉnh** (kể tội, đạo lý, lời hứa), rồi câu chốt 2–5 từ.
- `(cách nói)`: 1–3 từ tiếng Việt về giọng lúc đó (`nhỏ, run`, `gằn`, `cười khẩy`); không tả giọng nền (web lấy ở dàn ý). Tên ở `Thoại:` y từng chữ như `Khung:`.
- **Tràng dài:** Seedance 15 giây, xen mặt người nghe làm shot giữa. Quá trần từ thì chia nhiều clip cùng người nói, ngắt ở chỗ ngắt câu, đổi cỡ giữa các clip (trung rồi cận).
- **Lời nghĩ là công cụ chính:** khán giả hiểu phim qua lời, không qua diễn xuất; điều quan trọng không ai nói ra thì nói bằng lời nghĩ: điều nhân vật giấu (bí mật, kế hoạch, hiểu lầm), câu giải thích điều phi lý (`Lời nghĩ: Damon: "Marry her today, and Grandma finally sees who she is."`), nỗi khổ giấu kín chỉ khán giả biết (viện phí, nợ). Mặt im, môi khép, giọng phủ; 10–18 từ; một dòng mỗi clip, không `Thoại:` cùng clip. **Không** dùng lời nghĩ gọi tên cảm xúc mặt đã cho thấy ("I'm so hurt"), nhắc lại điều vừa nói, hay tả việc đang thấy. Điều giấu mà có người tâm sự (bạn, người sắp đặt, người giữ cổng) thì nói thành thoại với họ: hay hơn lời nghĩ, cho diễn viên đối diễn. Máy nhắc quá 10% clip: bớt hay chuyển sang người tâm sự; giữ thì ghi lý do.
- **Lời tự kể** (nhân vật kể với khán giả: quá khứ, vì sao ở đây) cũng viết `Lời nghĩ:`, trên clip 15 giây không ai nói (đi, làm việc, nhìn vật), tới khoảng 35 từ; ở đầu cảnh hay chỗ nhảy thời gian.
- Cú lật xảy ra bằng thoại hay vật trước mặt người; lời nghĩ giải thích, không thay cú lật.
- **Gieo, gặt phải nghe được:** dòng G gieo hay gặt trong phần có thoại hay lời nghĩ gọi tên điều, vật đó (cùng cụm với bảng Gieo và gặt); hình chỉ xác nhận.

## 6. Nhịp một phần

- Khoảng 5 clip mỗi phút (mức 75% khoảng 5,5; phần clip 30 giây khoảng 2; máy đo). Một mốc lật khoảng 2 phút; mỗi mốc có shot rõ lúc lật (câu hay vật lộ ra) và mặt người bị lật.
- **Neo cảnh** (CLAUDE.md "Khán giả hiểu"): clip đầu cảnh có shot định vị (mục 8) và trong 15 giây đầu một câu nói được ai, quan hệ gì nếu chưa rõ, chuyện gì đang treo. Vào cảnh muộn, ra sớm, nhưng không bỏ neo.
- Đổi cảnh: cặp cảnh liền nhau nối được bằng "vì… nên…" **trên màn hình**: câu hay hình đầu cảnh mới nhắc hệ quả cảnh trước; nhảy thời gian, nơi thì câu thoại hay hình đầu cảnh cho biết. Cảnh đầu phần (từ phần 2) trả lời hay nhắc câu hỏi treo cuối phần trước.
- **Nhắc mạch:** mạch (bí ẩn, mẹ con, tình…) vắng quá khoảng 5 phút thì lúc quay lại một câu nhắc chuyện tới đâu. Nhân vật vào lần đầu được gọi tên kèm vai trong thoại. Mỗi cảnh một mạch chính.
- **Nhịp diễn:** mỗi cảnh ít nhất một nhịp không lời ở đỉnh (vòng phản ứng, biểu cảm ba nhịp, đẩy vào, đặc tả vật), hoặc clip 15 giây chừa 4–5 giây cho mặt (khoảng 25–35 từ thay vì 45). Máy ước % giây đang nói mỗi phần, đích 60–80%: dưới 60% khán giả thiếu ngữ cảnh (phim cũ 28–45%), trên 80% là gần toàn lời như phim đối thủ.

## 7. Ghi chú nối (cuối mỗi phần, tối đa 12 dòng, web bỏ qua)

```
## Ghi chú nối
- Mã cuối: P050 · C009 · N05
- <Nhân vật>: ở đâu, biết gì, vật đang giữ, vết hay áo đã đổi
- Bí mật: khán giả biết gì mà ai chưa biết
- Gieo, gặt: G01 P003, G04 P021   (mã G, clip gieo hay gặt trong phần)
- Ức chưa trả, việc treo cho mốc sau (Cho Nxx: …)
- Bên trái, bên phải của cặp chính ở cảnh cuối; câu cuối của phần
```

## 8. Thủ pháp điện ảnh (Seedance)

Quay như phim Mỹ (phim mẫu quay Veo nên máy tĩnh, đừng chép): mỗi khoảnh khắc một cách nhìn có ý đồ; viết đúng cụm in nghiêng ở `Hình:` (máy kiểm nhận cụm này). Cú lớn (dolly zoom, vòng, nâng cao) tối đa một lần mỗi cảnh, dolly zoom một lần mỗi phần.

**Luật viết:**
- Mỗi shot **một** động tác máy, chỉ ở shot từ 3 giây; shot ngắn hơn thì đứng yên.
- Cú cần thời gian (vòng, nâng cao, lùi xa, chuyển nét) đặt ở shot **không thoại** hay **sau câu thoại**; nói trong lúc máy vòng thì vòng nửa chừng.
- Người nói trong lúc máy đẩy vào thì mặt hướng về máy, chếch nghiêng; đừng ghi họ quay sang người ngoài khung (ra gáy tóc).
- Tilt từ tay lên mặt: ghi "chỉ nói khi mặt đã vào khung" (đạt).
- Shot trao vật (tháo, đưa, thả vào tay) đừng gắn cú máy: máy tách thêm một cắt và làm mất vật.
- Câu dài không đặt vào shot dưới 3 giây.

| Khoảnh khắc | Thủ pháp, viết ở `Hình:` | Mã kho |
|---|---|---|
| Mở cảnh, người mới vào | *trượt ngang* qua tiền cảnh (hoa, kệ, song sắt) mở ra cả hai người; *bám lưng* người bước vào nơi mới; *từ trên xuống* (bàn, mộ, giường) | TP35 |
| Có người ngoài chứng kiến, bị theo dõi | *qua cửa kính* từ ngoài phố nhìn vào; *khung trong khung* qua ô cửa tối | TP40 |
| Kẻ mạnh, người cứu bước vào | *góc thấp sát đất, máy ngước lên* từ giày tới mặt; bóng *ngược sáng* ở khung cửa | TP34, TP41 |
| Câu nặng ký | giữ cận người nghe đổi sắc, ngậm môi, `giọng X ngoài khung` (đạt) | TP47 |
| Tiếng báo trước (phanh, cửa, tiếng gọi) | *tiếng tới trước hình*: cận người nghe ngẩng lên vì tiếng, shot sau mới thấy nguồn, có sẵn từ khung đầu | TP11 |
| Đối đáp leo thang | qua vai có tiền cảnh mờ; kẻ đang thắng *góc thấp*, người bị nhục *góc cao*, đảo góc từ shot lật thế | TP23 |
| Vừa đi vừa nói, sải bước tới | *máy lùi* trước mặt người đang đi (một hay hai người), mặt rõ | TP36 |
| Câu đắt, nhận ra | *đẩy vào* rõ tới cận mặt người nói câu đắt hay người nghe; *zoom nhanh* vào mặt lúc phát hiện | TP18, TP45 |
| Người bị lật thế, sững | *dolly zoom* mặt người bị lật khi nghe câu bom, giọng người nói ngoài khung (đạt); kẻ ác thua: *góc cao* nhìn xuống (máy nâng ở cận cảnh ra yếu) | TP37 |
| Đỉnh cảm xúc riêng tư | *vòng từ* sau lưng ra trước mặt ở shot không thoại, nói ở shot sau; cực cận mắt đứng yên có chủ ý (đạt); *trong gương* | TP44, TP42 |
| Bí mật trong tay, vật đổi tình thế | đặc tả tay giấu vật *rõ nét tiền cảnh*, *chuyển nét* sang mặt người đã biết; vật vừa rơi *rõ nét tiền cảnh* ở *góc thấp sát đất*, người phía sau phản ứng | TP38 |
| Kết cảnh, bỏ lại một mình | sau câu cuối, *lùi ra* và *nâng lên*, người nhỏ dần giữa nơi chốn (đạt, rất đẹp) | TP19 |

Giữ từ luật cũ:
- **Shot định vị:** clip đầu cảnh hay khi người mới vào: `shot 1 trung rộng <nơi>, A bên trái, B bên phải` (kèm một thủ pháp mở cảnh ở trên).
- **Cỡ leo theo căng:** trung → qua vai → cận → đặc tả (mắt, tay, vật) khi tới câu đắt; hạ về trung khi hé (hài, ấm).
- **Vòng phản ứng sau câu bom** (bí mật lộ, lời buộc tội, cú vả mặt): clip `Seedance 10s` ngay sau, không thoại (clip phản ứng riêng duy nhất), 3 cận liền: người bị lật, kẻ ác, người chứng; mỗi cận một nét mặt khác (P188). Chỉ ở câu bom, không sau mọi câu.
- **Đám đông chứng kiến** ở cảnh làm nhục, vả mặt công khai: shot trung rộng mặt người xem, điện thoại giơ lên quay, hay *qua cửa kính*.
- **Đặc tả vật** mỗi lần gieo hay gặt: `shot n đặc tả <cụm vật>`.
- **Màn hình điện thoại** (WhatsApp): chỉ thấy khung chat và tên; nội dung tin đọc bằng lời nghĩ hay thành tiếng (máy vẽ chữ kém).
- **Biểu cảm ba nhịp** ở mỗi đỉnh cảm xúc, một clip riêng: trước (cố giữ), đỉnh (vỡ), sau (cố lấy lại), mỗi nhịp một shot, kèm cử chỉ nhỏ: nuốt khan, siết ngón, cắn môi, nhìn đi chỗ khác.
- **Thời tiết, ánh sáng** ở mốc lớn: một cụm ở `Hình:` (mưa ở đáy, nắng chiều ở cảnh khép).

## 9. Cảnh hành động

Số trận, cỡ, mốc và cách thắng do dàn ý chốt. Luôn Seedance, máy cầm tay. Không viết mềm: đòn đủ lấy đà, chạm, hậu quả, dư âm; người chính được trúng sượt, bị quật ngã, gượng dậy.
- **Khối trận:** mỗi trận một khối theo `tran-danh.md` mục Số clip và Khối thiết kế trận (đọc hai mục này khi phần có trận), dòng đầu `## Thiết kế trận T1: tên · cỡ · P045–P052`. Trận mở ở cảnh mới, khối đặt ngay trên dòng `## Cxxx` của cảnh đó; P045–P052 là mọi clip trận, liền nhau. Lối đánh, cú đỉnh tả bằng lời, không cần mã. Số T liền cả phim.
- **Vị trí:** clip đầu trận mở bằng shot trung rộng: ai đứng đâu (trái, phải), vật quanh (cạnh bàn, bậc thềm, đồ đã gieo); vị trí đổi thì thêm shot rộng.
- **Đòn:** mỗi đòn một shot cận: ai đánh, tay hay chân trái/phải **của chính người đánh**, hướng (vung ngang, đấm thẳng, đạp), trúng đâu (trái/phải của chính người bị đánh), bật về phía nào; đòn nặng kèm cận mặt. Clip 10 giây 1–2 đòn, 15 giây 2–3 đòn, 30 giây hai lần đổi thế, mỗi lần 2–4 đòn.
- **Clip trận 30 giây:** 12–14 shot, mỗi shot 2–3 giây (không theo 8–9 shot của mục 3), không ép cắt ở giây 15. Giữa clip một shot rộng cho thấy lại ai đứng đâu, đặt ở chỗ trận đổi thế. Shot cuối tả bằng chữ ai đứng đâu, cắt khi người chính còn đang làm một động tác, không đứng thở.
- **Kẻ đánh:** mỗi kẻ một dòng ở Cụm cố định, kiểu mũ áo khác hẳn nhau, mỗi kẻ một loại vũ khí; gọi đúng tên vũ khí ở mọi shot (hai kẻ giống nhau thì model nhân bản người, đổi vũ khí).
- **Người yếu thế** (nữ chính, người già, trẻ con) không thắng người to hơn bằng sức: đòn trúng người to hơn có lý do ngoài sức, ghi trong shot (né để kẻ ác lao vào cạnh bàn, sàn trơn, đồ đã gieo, bẻ cổ tay, đồng minh tới). Đối chiếu dáng ở Cụm cố định: người to cao không ngã vì một cú tát. Khớp dòng "thắng nhờ …" ở bảng Gieo và gặt.
- **Vẫn có thoại:** kẻ ác chế nhạo, người yếu thế câu chốt 2–5 từ; mỗi clip trận ít nhất một lượt.
