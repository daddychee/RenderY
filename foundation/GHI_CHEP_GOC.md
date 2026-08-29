# GHI CHÉP GỐC — LỜI USER ĐỌC FOUNDATION (nguyên văn, 2026-07-01→02)

> **File này là NGUYÊN LIỆU GỐC để viết các file foundation.** Lưu nguyên văn lời user
> (ngôn ngữ user giao tiếp với editor hàng ngày) từ phiên bàn bạc 2026-07-01/02, vì
> transcript chat bị dọn theo thời gian. KHÔNG sửa lời trong file này — khi viết foundation
> thì trích từ đây. Danh mục đã khóa + quyết định gộp: xem cuối file + `NHAT_KY_BUILD.md §F0`.

---

## 1. Pacing (tiết tấu)

> Bản chất: Tốc độ thông tin/cảm xúc trôi qua theo thời gian. Có macro-pacing (nhịp toàn video: khi nào dồn dập, khi nào chậm lại) và micro-pacing (độ dài từng cut).
> Cách làm: Pacing không phải "cắt càng nhanh càng hay". Nó là đường sóng: dồn → thả → dồn. Đoạn thông tin nặng/cảm xúc → chậm lại cho khán giả thấm. Đoạn liệt kê/chuyển cảnh → nhanh. Nguyên tắc vàng: mỗi cut phải có lý do biến mất — hình còn thông tin thì giữ, đã "cạn nghĩa" thì cắt.
> Lưu ý: Lỗi phổ biến nhất của editor mới là cắt đều tăm tắp (mọi shot 2 giây) → khán giả mệt và tê, không còn cảm giác nhấn nhá. Pacing đều = không có pacing.
> Ví dụ: Video du lịch mạo hiểm. Đoạn "hành trình lên núi" → cut nhanh theo beat (0.5–1s/shot) tạo năng lượng. Vừa lên tới đỉnh → hold một shot toàn cảnh 5–6 giây, không cắt, voice im. Sự tương phản chậm/nhanh này chính là cái làm khoảnh khắc đỉnh núi "đắt".
> quan trọng nhất: trước khi dựng cần xem lại dna của niche, xem các video viral của niche mình dựng như thế nào. khi chúng ta đưa project của editor dựng chính vào để học, hoặc đưa video viral vào để học, hệ thống cần học được cách dựng pacing của chủ đề.

**Bổ sung (gộp vào Pacing theo lệnh user "hãy gộp vào pacing"):**

> Chuyển cảnh (footage) ở các đoạn nghỉ của voice như hết câu, dấu phảy,.... chức năng này đã có trong tool: "C:\Users\NBPC\Documents\Claude\Projects\code tool edit nhan ban". lưu ý là không phải cứ hết câu thì chuyển cảnh, bạn cần tìm hiểu kỹ

*(Ghi chú kỹ thuật đã tra: cái có sẵn ở `nhan ban` là snap mép cắt về khoảng lặng —
`autoclone\retime\snap.py::snap_cut_boundaries()` + `retime\silence.py::choose_silence_us()`,
ffmpeg silencedetect -35dB/≥0.15s, cửa sổ ±0.8s, bonus lặng dài 30% cap 0.5s, chống trùng
bằng `used` set, 41%→73% cắt khớp lặng. Đó là TINH CHỈNH mép cắt đã có; còn quyết định
CHỖ NGHỈ NÀO đáng cắt là quyết định đạo diễn mới — thuộc foundation Pacing này. Tương đương
snap đã có trong padoma qua `autoedit/cutter/silence.py`.)*

---

## 2. Hình thở (breathing room / negative space)

> Bản chất: Khoảng voice ngừng nói nhưng hình vẫn chạy (footage đắt tiếp tục trình chiếu) để bổ nghĩa, làm rõ, hoặc để khán giả thỏa mãn/thấm đoạn voice vừa rồi. Đây là dấu hiệu của editor giỏi — biết khi nào im lặng.
> Cách làm: Sau một câu voice có sức nặng hoặc một câu phù hợp để chèn thêm footage đắt phía sau (một kết luận, một câu đắt, một cảm xúc), để trống 1–15 giây voice (tùy chủ đề, như niche du lịch chill chill có đoạn hình thở tới 30 giây) và trải một shot hình mạnh + sound design môi trường/nhạc nền. Hình thở thường đi kèm âm thanh thật (ambient): tiếng gió, tiếng bước chân, tiếng thở → tạo cảm giác "sống".
> Lưu ý: Hình thở chỉ hiệu quả khi footage đủ đắt để đứng một mình. Nếu để khoảng thở trên một shot nhạt → thành "chết hình", khán giả tưởng lỗi. Đừng lạm dụng: nhồi quá nhiều khoảng thở làm video ì. Nó là gia vị, không phải món chính.
> Ví dụ: Video kể chuyện cá nhân. Voice: "...và đó là lần cuối tôi gặp ông." → cắt voice, để 2.5 giây trên shot bàn tay ông đang pha trà (B-roll quay chậm) + tiếng nước rót nhỏ + nhạc piano một nốt ngân. Chính khoảng lặng đó khiến câu vừa rồi "ghim" vào người xem. Nếu voice nói tiếp ngay, cảm xúc bị cắt ngang.
> ví dụ 2: hôm nay chúng ta sẽ đến thăm đất nước việt nam xinh đẹp với thiên nhiên tuyệt vời qua màn ảnh → dừng hình thở, chiếu các footage đẹp mang tính signature về việt nam như: cảnh lúa ở sapa, hà giang, cảnh vịnh hạ long, ninh bình,...

> hình thở có thể là 1 footage hoặc nhiều footage. miễn là phù hợp dna niche và đoạn thoại đó. khi chúng ta học nhiều video, sẽ có số liệu về hình thở của niche. đây là một foundation quan trọng, bạn cần lưu ý kỹ.

**Vị trí (user chốt 2026-07-02):** file RIÊNG, nhưng phải note rõ nó là MỘT PHẦN của pacing để ai đọc cũng hiểu.

**Góp ý của user khi duyệt bản nháp d2 (2026-07-02) — nguyên văn:**
> [về việc giữ số prompt làm mặc định universal] tôi thấy chưa hợp lý. ở foundation nó chỉ là ví dụ. chúng ta quyết định nghỉ ngắn hay dài phụ thuộc vào có nhiều footage đắt không, đoạn đó cần thở bao nhiêu lâu khán giả vẫn chấp nhận ở lại nghe. việc fix cứng hook 1.5-2.5 giây làm video bị khô khan. bạn cần tính toán lại phần này.
> [về luật "không có hình đắt thì thà không thở"] chấp nhận đề xuất, nhưng trong một video vẫn phải có hình thở, tính năng này có làm tool gỡ hết hình thở không, bạn cần tính toán cẩn thận.

→ Đã sửa vào `d2-hinh-tho.md`: (1) mọi con số = VÍ DỤ, không phải luật; quyết ngắn/dài =
**quyết định 2 PHA** — direct đặt ý định [min–max] theo (kho footage đắt + sức chịu khán giả)
→ source tìm hình → kết quả tìm chốt số cuối; số fix cứng trong prompt autoedit sẽ GỠ khi
L2b sâu. (2) **SÀN hình thở** ≥1 ô/video + thang cứu hộ 3 nấc (nới tìm → thăng vị trí dự
phòng → giữ ô tốt nhất + cờ needs_human) — luật "thà không thở" chỉ áp TỪNG Ô, không bao
giờ đưa cả video về 0.

---

## 3. Ducking — nâng/hạ nhạc nền theo voice

> Nâng/hạ âm lượng nhạc nền khi có voice và không có voice. khi voice bắt đầu nói thì nhạc nền bé lại. khi voice không nói (đoạn hình thở) thì nhạc nền to lên.
> mức hạ db bao nhiêu chúng ta sẽ học dna niche hoặc quyết định sau. bạn nhớ note lại

**Vị trí (chốt):** lớp con trong Sound Design & Nhạc. **Điểm treo: mức dB chưa chốt.**

---

## 4. Mood & Tone

> Bản chất: Tone = thái độ/giọng điệu tổng thể của video (nghiêm túc, hài hước, hoài niệm, năng lượng, gai góc...). Mood = cảm xúc tại từng đoạn mà người xem cảm thấy. Tone là hằng số của cả video; mood biến thiên theo mạch.
> Cách xây dựng: Mood/tone không nằm ở một thứ — nó là cộng hưởng của 5 tầng:
> 1. Nhạc & sound design — quyết định 60% cảm xúc. Đổi nhạc = đổi mood ngay cả khi hình không đổi.
> 2. Màu (color grade) — ấm/lạnh, tương phản cao/thấp, độ bão hòa.
> 3. Pacing — nhanh = phấn khích/căng; chậm = trầm/hoài niệm.
> 4. Voice (giọng đọc/tempo) — cách ngắt nghỉ, năng lượng giọng.
> 5. Chọn footage — góc máy, ánh sáng, chuyển động camera trong shot.
> Cách làm: Trước khi dựng một đoạn, chốt một từ khóa tone cho đoạn đó (ví dụ: "ấm áp – hoài niệm"). Mọi lựa chọn nhạc, màu, nhịp, transition đều phải "chạm" từ khóa đó. Đây là kim chỉ nam giữ video không bị lạc giọng. lưu ý tone của từng đoạn không nên lệch với tone cả bài.
> Lưu ý: Lỗi chết người là lệch tone: một video tâm sự sâu lắng mà chèn hiệu ứng "meme" giật đùng hoặc nhạc EDM → khán giả thấy giả trân. Tone phải nhất quán; mood được phép thay đổi có chủ đích (đang buồn → chuyển sang hy vọng ở cuối).
> Ví dụ: Cùng một footage đi bộ trong mưa. Ghép nhạc lo-fi + màu ấm hơi phai + pacing chậm → mood hoài niệm, bình yên. Đổi sang nhạc dồn dập + màu lạnh tương phản cao + cắt nhanh → mood cô đơn, ngột ngạt. Hình y hệt, cảm xúc trái ngược. Đó là quyền lực của editor.
> quan trọng: tham khảo dna niche để hiểu về tone của niche, dễ quyết định cho video.
> foundation về mood & tone được ứng dụng nhiều nhất trong chọn footage (màu sắc, bố cục phù hợp). ví dụ 1 lỗi: đoạn content đang buồn, u ám, các footage đều màu tối, tự nhiên có 1 footage lệch màu: sai mood. ví dụ 2: niche du lịch, các footage mở đầu đang tươi sáng, colorful mà tự dưng có 1 footage màu vintage: sai mood.

**Hệ quả kiến trúc (đã chốt trong bàn bạc):** đẻ ra **veto C2b — veto sai mood** trong nhóm C
(độc lập với veto sai nghĩa C2): footage đúng nghĩa nhưng sai màu/tông/năng lượng so với mood đoạn → loại.

---

## 5. Sound design & nhạc (bị coi nhẹ nhất, quan trọng nhất)

> Bản chất: Âm thanh làm 50% cảm xúc mà người xem không ý thức được. Gồm 3 lớp: nhạc nền, âm thanh thật/ambient (tiếng môi trường, foley), và hiệu ứng nhấn (whoosh, impact, riser).
> Cách làm: Xây theo lớp — voice ở trên cùng (rõ nhất), nhạc nền dưới (ducking: tự hạ khi có voice), ambient để lấp "khoảng trống chân không". Dùng riser (âm dâng dần) trước một cú reveal, impact/boom ngay điểm cắt mạnh, whoosh cho chuyển cảnh nhanh. Ambient là thứ khiến hình thở không bị "chết".
> ambient nên học dna niche để hiểu rõ niche mình dùng nhiều loại ambient gì, ví dụ: travel đầu video hay dùng tiếng nước chảy, tiếng sóng nếu cảnh trình chiếu đoạn đó là biển, suối,... khán giả thích nghe âm thanh dễ chịu. phân tích dna niche để biết footage video loại nào thì dùng ambient loại nào, khán giả niche đó thích ambient gì. ví dụ niche deepsea: khán giả thích nghe tiếng âm thanh dưới biển sâu.
> Lưu ý: Đừng để hoàn toàn im lặng thật trừ khi cố ý — tai người nghe khoảng lặng tuyệt đối như "lỗi". Luôn có một lớp ambient/room tone rất nhỏ. Ngược lại, đừng để nhạc át voice. Nhạc phải phục vụ tone, không phải "bài mình thích".
> Ví dụ: Cảnh mở hộp sản phẩm. Voice im, cận cảnh tay xé seal → foley tiếng giấy sột soạt (phóng đại lên) + một nốt nhạc chờ đợi + khi nắp mở ra thì "riser đạt đỉnh → impact nhẹ + nhạc bung". Cảm giác thỏa mãn đó 90% đến từ âm thanh, không phải hình.

**Vị trí (chốt):** foundation TRÙM cả nhóm E (thay E1–E4), Ducking là lớp con bên trong.

---

## 6. Shot variety (đa dạng cỡ cảnh & góc)

> Bản chất: Xen kẽ toàn cảnh – trung – cận – đặc tả và đổi góc để mắt không chán. Sự đa dạng tự nó tạo nhịp.
> Cách làm: Nguyên tắc "đổi cỡ cảnh hoặc đổi góc ≥30°" giữa hai shot liền kề → tránh jump cut và giữ tươi mắt. Cứ vài shot trung thì chèn một đặc tả (bàn tay, ánh mắt, chi tiết) để tạo texture.
> Lưu ý: Đừng dựng cả đoạn dài chỉ một cỡ cảnh (một góc talking head 2 phút = tử thần retention). Cận đặc tả là "gia vị" tạo cảm xúc — đừng bỏ quên.
> Ví dụ: Đoạn nấu ăn: toàn cảnh bếp (bối cảnh) → trung cảnh thái rau → đặc tả dao chạm thớt + tiếng "cạch" (foley) → cận mặt đầu bếp nếm thử. Bốn cỡ cảnh trong 8 giây → sống động, không nhàm.

**Vị trí (chốt):** file riêng trong nhóm C. **Ràng buộc pipeline: luật này xét theo CHUỖI shot
liền kề (cần biết cỡ cảnh/góc shot #n-1) → schema tag GLM (Phase B) BẮT BUỘC có trường
cỡ cảnh + góc máy, nếu không luật chết.**

**Góp ý của user khi duyệt c7 (2026-07-02) — nguyên văn:**
> tôi nghĩ chúng ta có thể hạ trọng số của góc máy, hoặc bỏ đi nếu khó không làm được, vì tôi sợ sẽ bị loại đi nhiều footage hay. cỡ cảnh quan trọng hơn.

→ Đã sửa `c7-shot-variety.md`: **cỡ cảnh = tín hiệu CHÍNH của variety; góc máy hạ xuống tín
hiệu phụ CHỈ-CỘNG** (có tag đáng tin → cộng nhẹ; thiếu tag/trùng góc → KHÔNG trừ, không bao
giờ là lý do loại). Schema tag GLM: cỡ cảnh BẮT BUỘC, góc máy TÙY CHỌN thử nghiệm — Phase B
đánh giá độ tin cậy tag góc, không tin cậy thì BỎ HẲN, variety chạy bằng cỡ cảnh.

---

## 7. Text, typography & motion graphics

> Bản chất: Chữ trên màn hình — từ caption, tiêu đề chương, tới số liệu, kinetic typography. Vừa truyền thông tin vừa là yếu tố nhịp điệu và tone.
> Cách làm: Chọn 1–2 font nhất quán cả video (một cho tiêu đề, một cho phụ). Chữ xuất hiện phải có animation nhẹ (fade/slide/scale in) — chữ "bụp" hiện thô rất kém sang. Timing chữ khớp voice: hiện đúng lúc nói tới từ đó. Với số liệu/từ khóa quan trọng → nhấn bằng chữ để "ghim".
> Lưu ý: Đừng nhồi chữ đầy màn (contrast kém, che hình). Đảm bảo tương phản chữ/nền (thêm shadow/box mờ nếu nền loạn). Giữ chữ đủ lâu để đọc hết (đọc thầm 1 lượt + 0.5s).
> Ví dụ: Voice nói "tăng 300%" → cùng lúc chữ "+300%" scale-in nảy nhẹ ở góc, màu nổi bật, kèm một tiếng "pop". Con số ghim vào đầu người xem mạnh hơn nhiều so với chỉ nghe.
> quan trọng: trong video nên có nhiều layer chữ mang lớp nghĩa thứ 2, thứ 3 để bổ nghĩa cho đoạn content. ví dụ: voice nói: việt nam là đất nước mà bạn có thể sinh sống với chi phí hợp lý nhất và an toàn nhất ở châu á, trung bình một người trưởng thành chi tiêu một tháng hết $1000. ngay đoạn cuối chi tiêu 1 tháng hết $1000, chúng ta có thể hiện chữ: hồng kông $2000 - singapore $2500. ví dụ 2: khi voice nói: "chi phí cho thực phẩm ở việt nam cũng rất dễ chịu" - màn hình sẽ hiển thị: "ăn sáng (phở) $2, cà phê $1.5"

**Vị trí (user chốt: "gộp vào nhóm f"):** foundation TRÙM nhóm F, nuốt F1 (caption/text nhấn) +
F3 (motion graphic). **Điểm treo: lớp nghĩa 2–3 cần SỐ LIỆU THẬT (web-grounded) — phụ thuộc
bài toán `enrich --web` qua Claude Code chưa giải (NHAT_KY §B1).**

---

## 8. Các làm rõ quan trọng khác của user (nguyên văn)

**Nguồn DNA niche ở project này:**
> ở project cũ có các footage dna niche. nhưng ở project mới này, các footage dna chính là các footage được cắt ra từ các video viral và các project cũ sẵn có.

**Nguồn footage CHÍNH = kho local học từ project, KHÔNG phải stock (2026-07-02, khi duyệt c1) — nguyên văn:**
> phần : "stock — kho stock (Pexels)" đang được ghi bản chất là: "Tuyến MẶC ĐỊNH của đa số beat. Chất lượng sống chết theo query." đây là logic của project cũ. project này là một hệ thống khác, như tôi đã nói từ ban đầu. chúng tôi sẽ tải rất nhiều project ( ban đầu có thể đến 100 project ), hệ thống sẽ học và lấy lại các footage từ trong project đó ( được tag vission ). project này cũng không thuộc niche nghỉ hưu, mà viết cho đa dạng niche: space, deepsea, travel

→ Đã sửa `c1-phan-tuyen-nguon.md`: **local_library = tuyến CHÍNH** (kho ~100 project +
video viral, cắt footage + tag vision ở Phase B); **stock = BỔ TRỢ** lấp chỗ kho chưa phủ;
luật route trong prompt autoedit ("local khi có niche profile", stock mặc định) là logic
cũ → ĐẢO mặc định khi L2b sâu. Đa niche: space, deepsea, travel.

**Pacing thay thế B2/D1 (đường cong năng lượng, độ dài shot):**
> về bản chất phần này là để thể hiện pacing. khi chúng ta tính foundation chuẩn về pacing, chúng ta sẽ tính toán kỹ thay thế phần này.

**Cảnh báo quan trọng nhất (2026-07-02) — về bản chất foundation:**
> foundation tôi viết cho bạn là ngôn ngữ mà tôi giao tiếp với editor hàng ngày, chúng ta cần phải tính toán cẩn thận để đưa vào ứng dụng trong tool này. vì trong 1 foundation vài câu nói nhưng nhiều khi cần code rất nhiều tính năng để xử lý foundation đó. bạn cần tính toán cẩn thận.

**Mối lo "lọc chồng lọc" (2026-07-02) — nguyên văn:**
> khi có quá nhiều luật, có thể việc chọn footage sẽ rất khó, rồi các bước sau sẽ loại đi các footage quan trọng, luật của các foundation lệch nhau làm loại nhiều footage. nên chúng ta cần tính kỹ việc này. trong trường hợp có bước nào loại mất nhiều footage chúng ta có thể cân nhắc loại bỏ để tránh lỗi.

→ Đề xuất của Claude (**USER ĐÃ DUYỆT 2026-07-02 — 4 nguyên tắc ĐÓNG BĂNG tại `c5-loc-xep-hang.md`**):
**4 nguyên tắc phễu chọn footage** — (1) chỉ 2 veto cứng: sai nghĩa nghiêm trọng + hỏng kỹ
thuật/watermark; mọi luật khác (mood/variety/pacing/chữ ký) là ĐIỂM có trọng số, chọn điểm
cao nhất; (2) sàn ứng viên ~3 — luật nào phá sàn tự hạ cấp thành trừ điểm; (3) log
`(footage, luật, lý do)` mỗi lần loại → report bảng "luật nào giết bao nhiêu %" → cắt luật
dựa số liệu thật; (4) ưu tiên khi vênh: nghĩa > mood > nhịp/variety > đẹp/chữ ký.
**c5-loc-xep-hang = trọng tài duy nhất của phễu; foundation khác chỉ đóng góp luật, không
tự quyền loại.** (Hiện trạng code: ranker rỗng; sourcer chỉ có veto watermark + thang
fallback specific→broad→thematic→needs_human — thiết kế này là cho tương lai C2/C2b/C7.)

→ Hệ quả: mỗi file foundation, phần 3 phải có **bảng "Phân rã năng lực"** — dịch từng câu
ngôn-ngữ-editor thành năng lực tool: (a) đã có sẵn (trỏ module) / (b) cần code mới ỐNG /
(c) NÃO quyết lúc chạy / (d) cần dữ liệu DNA (Phase B). Gom mọi dòng (b) = backlog code;
gom mọi dòng (d) = spec schema tag Phase B.

---

## DANH MỤC ĐÃ KHÓA (2026-07-02) — 17 file

Khuôn mỗi file 5 phần: **1. Là gì · 2. Yếu tố ảnh hưởng · 3. Cách làm THỰC TẾ ở project này
(kèm 3b. Phân rã năng lực) · 4. Cạm bẫy · 5. Học gì từ DNA niche.** Phần 3 viết dạng
**"dự kiến 🔸"**, chốt dần khi chạy thật Level 2. Phạm vi: chỉ kỹ năng NÃO (kỹ thuật ỐNG
C1–C5/transcode giữ ở CLAUDE.md, phần 3 chỉ trỏ tới).

| Nhóm | File | Ghi chú |
|---|---|---|
| A | a1-chia-beat-chuong · a2-chuc-nang-doan · a3-open-loop-callback | |
| B | b1-mood-tone · b3-pattern-interrupt | B2 đã gộp vào pacing |
| C | c1-phan-tuyen-nguon · c2-an-du-veto (gồm C2b veto mood) · c3-ngu-canh-chuoi · c4-tu-khoa-tim · c5-loc-xep-hang · c6-footage-chu-ky · c7-shot-variety · **c8-cat-nguon-viral (THÊM 2026-07-08 — luật bản quyền cắt nguồn, xem §BỔ SUNG cuối file)** | |
| D | d1-pacing (TRÙM: nuốt B2 + độ dài shot + quyết định cắt-tại-nghỉ-voice) · d2-hinh-tho (riêng, note là một phần pacing) · d3-loai-cat-transition (D2 cũ + F4 cũ) | |
| E | e1-sound-design-nhac (TRÙM E1–E4 cũ, gồm ducking) | |
| F | f1-text-typo-motion-graphics (TRÙM: F1+F3 cũ, lớp nghĩa 2–3) · f2-ken-burns-punch-in | |

**Đợt viết 1 (đã chốt):** d1-pacing → d2-hinh-tho → b1-mood-tone. Mỗi file user duyệt xong mới viết tiếp.

**Điểm treo mang theo:** (1) mức dB ducking; (2) schema tag GLM: cỡ cảnh BẮT BUỘC, góc máy
TÙY CHỌN thử mẻ nhỏ đo tin cậy (user hạ cấp khi duyệt c7, xem §6);
(3) lớp nghĩa 2–3 cần web data (`enrich --web`); (4) số liệu hình thở theo niche từ DNA.

---

## BỔ SUNG 2026-07-08 — LUẬT CẮT NGUỒN VIRAL (bản quyền) → foundation c8 MỚI

> User giao trước đợt nạp viral đầu tiên (danh mục 18 file +1 = 19). Nguyên văn:

> trước khi bắt đầu việc vission các footage từ video nguồn trên youtube. tôi cần nhắc bạn
> một vấn đề quan trọng để kênh youtube của chúng ta không bị "đập gậy vi phạm bản quyền"
> từ kênh đối thủ mà chúng ta cắt nguồn. quy tắc cắt của công ty như sau, bạn cần tính toán
> cẩn thận và đưa vào một foundation mới hay gì đó. để sau này khi cắt nguồn video đối thủ
> hoặc như hiện tại đang nói là lấy footage từ video viral:
>
> "Nguyên tắc cắt khi lấy footage của 1 video viral (video kênh khác trên youtube):
> - Độ dài Source tối đa 10s (phần lớn cut 6s đảm bảo an toàn)
> - Tách âm thanh chỉ lấy Source
> - trong 1 video của mình lấy từ 1 video đối thủ, không lấy 2 frame liên tiếp của video
>   đối thủ vào 1 video của mình
> - Zoom to để mất logo, chữ
> - trong 1 video của mình đang làm không được lấy quá nhiều footage của 1 video nguồn.
>   cụ thể không được lấy quá 8% footage của video nguồn đó (lấy càng ít nguồn từ 1 video
>   càng tốt, ưu tiên lấy từ nhiều video, mỗi video một ít)"

**Chốt thêm (user, cùng ngày 2026-07-08):** cách hiểu đúng luật "2 frame liên tiếp":

> ý này bạn nói là đúng: "cảnh 5 và cảnh 6 của video đối thủ không được cùng xuất hiện
> trong 1 video mình, dù đặt xa nhau". không được lấy dù đặt xa nhau trong video của mình.
> có 1 vấn đề nữa khi tách cảnh, tôi thấy capcut tách cả những cảnh chỉ dài 1 giây hoặc
> ngắn hơn 1 giây. tôi muốn loại bỏ luôn các cảnh dưới 2 giây để đỡ phải gọi vission.
