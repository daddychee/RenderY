# L2 bổ sung: đạo diễn một phân cảnh phim (cú máy, góc máy, cảm xúc con vật, âm thanh)

Luật đạo diễn một phân cảnh phim (ý đạo diễn, cảm xúc con vật, âm thanh, cấp cả phim); đã thử thật và đạt. Đọc `00-chung.md` và `L2-phim-nhan-vat.md` trước. Với phim, file này thắng các câu cấm cú máy và chất điện ảnh ở `00-chung.md` mục 1, 3 và `chu-de/tien-su-khung-long.md` mục 3; lịch sử các đợt thử ở `KINH-NGHIEM-PROMPT.md` mục 12.

Nguồn: kiến thức đạo diễn và thiết kế âm thanh phổ thông (ngữ pháp hình ảnh của Spielberg trong Jurassic Park, nguyên tắc hồi hộp của Hitchcock, Walter Murch về số lớp tiếng, Gary Rydstrom làm tiếng khủng long từ thú thật, cách BBC Natural History dựng cảnh săn mồi); Dan Kieft `nguon/…ultra-realistic…`, `…14-prompt…` (prompt 7, 10, 13), `…aicameramovements…`, `…emotion-direction…`.

## 1. Trước khi viết prompt: bốn câu hỏi đạo diễn

Mỗi phân cảnh trả lời bằng một dòng, ghi vào kịch bản:

1. **Khán giả phải cảm thấy gì** ở cuối cảnh (thương, sợ thay, nhẹ nhõm, choáng ngợp)? Không phải "cảnh này có gì".
2. **Ai biết gì?** Hồi hộp = khán giả biết điều nhân vật chưa biết (thấy kẻ săn trước khi con mồi thấy). Bất ngờ = cả hai cùng không biết. Chọn một.
3. **Cảm xúc nhân vật đi từ đâu tới đâu**, cái gì kích hoạt chỗ đổi (một tiếng động, một cái bóng, một mùi).
4. **Khoảnh khắc nào là đỉnh cảnh**, rơi vào giây thứ mấy; hình, máy và tiếng cùng dồn về giây đó.

## 2. Góc máy và cú máy chọn theo ý kể chuyện

Tên cú máy và dạng viết bốn ý (Movement, Speed, Framing, End) lấy ở `00-chung.md` mục "Bảng cú máy". Bảng này nói **khi nào dùng**:

| Muốn khán giả cảm thấy | Góc, cỡ cảnh | Cú máy | Ghi chú |
|---|---|---|---|
| Nhân vật nhỏ bé, cô độc, dễ tổn thương | góc cao nhìn xuống, toàn cảnh, nhân vật nhỏ giữa khoảng trống | crane up kèm lùi ra; slow zoom out | khoảng trống quanh nhân vật là nội dung chính |
| Ở cùng nhân vật, thương nó | ngang tầm mắt **của con vật** (sát đất với con non), cận | low tracking, follow shot, reverse tracking cùng tốc độ | không bao giờ quay con non từ tầm mắt người |
| Kẻ mạnh, mối đe dọa, quyền lực | góc thấp ngước lên, ống kính rộng gần | tilt up từ chân lên đầu; dolly in chậm | con vật lấp khung, che trời |
| Bị rình | **góc nhìn của kẻ rình**: qua lá tiền cảnh mờ, con mồi nét ở xa | push past rất chậm, handheld thở nhẹ | khán giả ở trong đầu kẻ săn; kèm tiếng thở gần |
| Lộ diện (reveal) | bắt đầu ở chi tiết hay nhân vật nhỏ, kết ở thứ khổng lồ | crane up vượt ngọn cây; pan theo ánh mắt nhân vật; rack focus có kích hoạt | **dấu hiệu tới trước, con vật tới sau**: mặt nước rung, chim bay, tiếng bước, rồi mới thấy |
| Nhận ra điều gì (realization) | cận mặt | slow dolly in vào mặt; máy dừng khi nhân vật đứng sững | phản ứng trước, thứ gây phản ứng sau |
| Hỗn loạn, tấn công | cận, khung lệch, tiền cảnh quệt qua | chase shot, handheld giật, whip pan | shot ngắn 1 đến 2 giây; xen **một** toàn cảnh để đọc được ai ở đâu |
| Nhẹ nhõm, kết | trung rồi toàn | máy chậm lại, crane up rời nhân vật | tiếng môi trường trở lại |

Quy tắc dựng trong một phân cảnh:
- **Shot, shot đối (shot / reverse shot)** cho mọi cảnh hai phe: kẻ rình, con mồi, kẻ rình gần hơn, con mồi vẫn chưa biết. Giữ trục: máy ở một bên đường nối hai con vật suốt cảnh.
- Cảnh cảm xúc ưu tiên **một cú máy liền mà máy đổi vai qua từng mốc giây** (Dan Kieft prompt 7, 10): bám sau lưng, vòng ra trước mặt, nâng lên cao. Cảnh hành động ưu tiên nhiều shot hard cut.
- **Mỗi cảnh một cú máy có ý, tĩnh hay động đều được; không bắt máy động.** Các shot còn lại đơn giản. Máy chuyển động thì trả lời được "vì sao lúc này".
- Phim vẫn **chỉ hard cut** giữa các shot và giữa các phân cảnh.

## 3. Cảm xúc con vật: tả hành vi, không tả tên cảm xúc

Con vật không có lông mày hay khóe miệng; cảm xúc đọc được qua **thân, đầu, mắt, hơi thở, tiếng kêu, nhịp**. Viết theo `L2-phim-nhan-vat.md` mục 2.10: trạng thái đầu, **kích hoạt**, chuỗi 4 đến 6 hành vi theo thứ tự, cường độ, câu giữ trạng thái cuối. Bảng hành vi (rút từ tập tính chim non, bò sát, thú; dùng cho khủng long vì họ hàng gần chim):

| Cảm xúc | Hành vi nhìn thấy | Tiếng |
|---|---|---|
| Tò mò, vô tư | bước đều, đầu nghiêng ngó, mổ thử, đuôi nhấc | peep thưa, đều, thấp |
| Nhận ra bị lạc | dừng giữa bước, đầu quay phắt về phía sau, đứng sững một nhịp | peep ngừng |
| Lo âu | đầu giật trái phải liên tục, chớp mắt nhanh, bước một hướng rồi quay lại, xoay vòng nhỏ, thân hạ thấp, đuôi cụp | tiếng gọi **cao dần, dày dần**, mỗi tiếng xong ngừng lại nghe; không ai đáp |
| Sợ đứng hình | đông cứng giữa bước, ép sát đất, cổ rụt, mắt mở to không chớp, sườn phập phồng nhanh, run | im bặt; chỉ còn hơi thở gấp nhỏ |
| Hoảng loạn | chạy loạng choạng, vấp ngã, chân cào cát, ngoái đầu | tiếng ré chói, ngắt quãng |
| Rình mồi | **đầu giữ tuyệt đối ngang và yên trong khi thân trượt tới**; đặt từng bàn chân thật chậm, ngón xòe; đứng sững giữa bước khi con mồi ngẩng lên, một chân còn nhấc; mắt khóa, không chớp; đuôi cứng thẳng làm đối trọng; nấp sau mép lá | gần như không tiếng; một tiếng click họng khẽ; hơi thở mũi chậm |
| Sắp vồ | đầu hạ thẳng hàng với sống lưng, hông lún xuống, cơ đùi gồng, lông dựng nhẹ | im lặng hoàn toàn nửa giây trước cú bật |
| Mẹ nghe con kêu | đầu bật dậy, mắt mở lớn, lỗ mũi nở, thân chồm dậy trong một động tác | tiếng rống trầm vang bắt đầu |
| Bảo vệ, dọa | lao tới rồi **đứng chắn ngang thân**, đầu hạ thấp hướng về kẻ thù, giậm chân, quật đuôi, tiến một bước ép | rống dài, phì mũi mạnh |
| Kẻ săn bị đuổi | nhảy lùi, lông xù, thân hạ thấp, lùi vài bước còn ngoái nhìn, rồi quay đi | rít, tiếng kêu gắt ngắn |
| An toàn trở lại | con non chui dưới ngực mẹ giữa hai chân trước, run chậm dần; mẹ cúi mỏ chạm con | hơi thở chậm, tiếng ừ trầm trong họng, peep nhỏ dần đều lại |

Hai con vật khác cỡ: luôn ghi tỉ lệ bằng chữ và bằng vật so sánh trong cùng khung ("the hatchling is goose-sized and reaches only to the Troodon's knee; the Troodon reaches only to the mother's belly").

## 4. Âm thanh: viết thành khối riêng, theo từng mốc giây

Cách của Dan Kieft (prompt 13, video ultra-realistic), cộng nguyên tắc thiết kế âm thanh phim:

1. **Khối SOUND riêng cuối prompt, chia theo đúng các mốc giây hay shot của phần hình.** Không gộp thành một dòng "ambient sound".
2. **Ba lớp, mỗi thời điểm tối đa hai đến ba tiếng nổi** (Murch: quá ba lớp thì tai không tách được):
   - *Nền* (bed): tiếng nơi chốn liên tục: côn trùng đêm, nước sông, gió trong dương xỉ. Ghi một lần đầu khối, kèm "continuous under everything".
   - *Tiếng sự kiện* (foley, tiếng kêu): gắn vào **đúng hành động trong hình**, mỗi bước một tiếng ("each heavy footfall lands with a deep thud and a spray of wet sand").
   - *Tiếng nhấn chỉ khán giả nghe* (non-diegetic): sub-bass hit, tiếng rền trầm lớn dần (low drone swell), khoảng lặng chủ ý. Gắn vào **đúng khung hình** của đỉnh cảnh. Không xin giai điệu nhạc trong clip (nhạc mỗi clip một kiểu, ghép lại gãy); nhạc nền cả phim làm ở hậu kỳ.
3. **Mỗi tiếng tả đủ bốn thứ**: nguồn, chất (wet, dry, hollow, raspy, resonant), khoảng cách (close to the microphone, far off across the flats, muffled behind the ferns), độ lớn và không gian (small in the open air, echoing off the water).
4. **Tiếng con vật tiền sử tả bằng thú thật** (cách Rydstrom làm Jurassic Park): con non = "like a gosling's peep mixed with a baby crocodile's chirp"; Troodon = "a dry throat click like a cassowary, a raspy hiss like a goose"; mẹ = "a deep resonant bellow, part elephant rumble, part foghorn, felt in the chest". Không viết suông "dinosaur sound", "roar".
5. **Im lặng là sự kiện**: côn trùng **ngừng bặt** khi kẻ săn xuất hiện ("the insect chorus cuts out all at once"); nửa giây chết trước cú vồ; tiếng môi trường **trở lại dần** khi nguy hiểm qua. Đây là cách rẻ nhất để có hồi hộp.
6. **Tiếng đi trước hình** ở cảnh lộ diện: tiếng cành gãy ngoài khung, tiếng bước nặng, rồi nhân vật quay đầu, rồi máy mới cho thấy.
7. **Tiếng gây ra hình**: bước chân mẹ làm cát nảy, máy rung; tiếng rống làm kẻ săn giật lùi.
8. Cuối khối ghi rõ: "No narration, no voice, no melodic music; only the location sound, the animal sounds and the low-frequency accents described above." Lời bình do ai33 đọc, ghép sau.
9. Ký hiệu: tiếng trong ngoặc nhọn `<...>` như `00-chung` mục 4; tiếng nhấn ghi chữ "non-diegetic" ngay trong ngoặc.

Hậu kỳ vẫn cần (ghi cho editor khi đã thử xong): một lớp nền môi trường liền cho cả đoạn cùng địa điểm để che chỗ nối, nhạc nền một bản cho cả phim, hạ nhạc khi có lời bình.

## 5. Khung prompt một phân cảnh phim

Khung 7 khối, quy tắc viết và hai mẫu: `mau-prompt-phim-dien-anh.md` (một nguồn cho web và skill).

## 6. Cấp cả phim: nhịp, nối cảnh, lời bình

- **Trộn cách dựng:** khoảng một nửa phân cảnh là một cú máy liền máy đổi vai (chuyển hồi, cảm xúc, kết; không dùng cho móc mở phim), một nửa là 4 đến 6 shot hard cut (gặp gỡ, rình, đối đầu, hành động).
- **Máy tĩnh là một lựa chọn có ý:** mỗi cảnh một cú máy có ý, tĩnh hay động đều được. Cảnh thiết lập có thể là khung tĩnh dưới 8 giây nếu bố cục tự kể (khung trong khung, bóng đổ, nhân vật là chấm nhỏ); máy động khi có ý (đẩy vào mắt, lùi lộ cỡ, pan lộ kẻ rình).
- **Móc mở phim 30 đến 40 giây, mọi phim:** khung đầu đã ở giữa biến cố (kẻ đe dọa và nạn nhân cùng trong khung, không cảnh dựng, không đời thường trước), đích trú thấy trước giây 10, 4 đến 6 lần suýt chết nặng dần rồi thoát có giá; nhiều shot cắt nhanh, không thoại, lời bình hay tựa. Chi tiết gần vẫn dùng nhưng nằm trong hiểm nguy đang xảy ra, không phải cực cận yên trước nguy. Công thức và bảng kiểm: `kien-thuc/moc-mo-phim.md` của thư mục `skill lam phim`. **Cảnh cuối rời nhân vật:** crane up tới khi nhân vật chỉ còn là chấm nhỏ, hay khung tĩnh với nhân vật đã là chấm nhỏ.
- **Khung cuối cảnh trước gài cho khung đầu cảnh sau**, ghi vào kịch bản của cả hai cảnh. Cần liền mạch tuyệt đối (cùng tư thế, vị trí) thì khung đầu là khung clip (Gen tiếp) kèm câu nối ở `mau-prompt-phim-dien-anh.md`.
- **Cầu nối bằng tiếng:** tiếng cuối cảnh trước được cảnh sau trả lời. Tiếng nền cùng nơi, cùng giờ viết cùng một câu ở mọi cảnh.
- **Màu và ánh sáng đi theo ảnh nơi chốn, chữ chỉ giữ:** mỗi nơi chốn một ảnh chiếu sáng lại đúng giờ của cảnh làm khung đầu (app chọn bản nét hay mờ theo cỡ cảnh); [LOOK] theo giờ ở `khoi-anh-sang-phim.md` (mặc định Trung tính ở `khoi-mau-phim.md`). Công cụ kiểm chặn các chữ hỏng da, số ống kính, câu cấm flare ở cảnh ngược sáng.
- **Số lượng và tỉ lệ thống nhất cả phim:** chốt trong bảng tài sản rồi chép nguyên câu `SIZE:` vào mọi cảnh có từ hai nhân vật.
- **Chuỗi nhân quả:** nhịp kết quả nào cũng có nhịp nguyên nhân nhìn thấy được ngay trước nó; thiếu thì sửa kịch bản, không sửa prompt.
- **Lời bình nhường chỗ cho hình và tiếng:** cảnh tiếng dày tối đa 1 từ một giây, đặt ở đoạn yên; cảnh thiết lập tới 2,5 từ một giây. Lời bình nói điều hình không nói được (thời gian, lý do, điều sắp tới).
- **Thời lượng clip:** luật ở `phien-1b-phan-canh.md` của skill `/lam-phim` trong thư mục `skill lam phim` (15 giây là chính, 10 giây khi cảnh thật ngắn; 20 đến 30 giây khi editor yêu cầu). Phim `Clip: 30s` (Mango): cảnh 30 giây là chính, một khoảnh khắc liền, cắt theo chuyện, không chia hai nửa ở giây 15 (`phan-canh-30s.md` của skill `/bien-kich`).
- **Gen 1 bản mỗi phân cảnh;** chưa ưng thì gen thêm từng bản (độ lệch giữa các bản là của model).

## 7. Thủ pháp điện ảnh: ở kho thủ pháp (Spec 34)

Thủ pháp có câu prompt, lỗi đã biết và clip mẫu nằm ở trang **Kho thủ pháp** trên web (mã TP cố định); `skill lam phim` chọn theo bảng `kien-thuc/tu-web/the-loai-thu-phap.md`, tra một mã ở bản xuất `kien-thuc/tu-web/kho-thu-phap.md`.
Cách chọn: mỗi cảnh một thủ pháp đắt có ý (hay không có), chọn theo cột "dùng khi" khớp ý đồ cảnh, ưu tiên thủ pháp đạt; kịch bản ghi `Thủ pháp đắt: TPxx <tên> vì …`.

## 8. Nhân vật là người (đã làm hai phim: `the-last-signal`, `born-a-wolf`)

Khung 7 khối và khối SOUND dùng nguyên. Cảm xúc lấy từ thư viện 25 cảm xúc (`L2-phim-nhan-vat.md` mục 2.10) thay bảng hành vi con vật; thoại và câu tả giọng theo `L2-phim-nhan-vat.md` mục 2.7; bộ ảnh người theo `L2-phim-nhan-vat.md` mục 2.1 (toàn thân bỏ phần đầu). Trong [SOUND] thêm lớp thoại, mỗi câu gắn mốc giây; hơi thở, tiếng vải, bước chân là thứ làm người "có mặt trong phòng".

## 9. Kế hoạch âm thanh hậu kỳ (ghi vào cuối `kich-ban.md`, đi theo gói dựng tới editor)

Tiếng trong clip đã có nền, tiếng sự kiện và tiếng nhấn. Editor làm thêm ba việc, skill viết sẵn chỉ dẫn:

1. **Nền môi trường liền**: mỗi đoạn cùng địa điểm và thời điểm một lớp nền kéo suốt dưới các clip (tả bằng chữ để editor tìm trong thư viện: "night insects, slow shallow river, light wind in ferns"), âm lượng thấp, để che chỗ nối giữa các clip.
2. **Nhạc nền một bản cho cả phim**: mô tả bản nhạc (nhịp, nhạc cụ, cảm xúc từng hồi), mốc vào, mốc ra, **các điểm nhấn trùng đỉnh cảnh** (giây nào của phân cảnh nào); im nhạc hẳn ở cảnh rình và nửa giây trước cú tấn công; hạ nhạc khi có lời bình.
3. **Lời bình**: mỗi phân cảnh đặt lời bình vào đoạn yên của cảnh (ghi giây bắt đầu), không đè lên tiếng nhấn và khoảng lặng.
Kèm các mẹo hậu kỳ đã ghi ở bản editor (hạt phim nhẹ, mờ mép, thanh đen, cắt bỏ slow motion thừa).
