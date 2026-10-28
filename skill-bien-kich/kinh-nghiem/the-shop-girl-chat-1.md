# Kinh nghiệm chat 1 · phim the-shop-girl (2026-10-01)

Chat làm dàn ý cả phim và phần 1 bằng `/bien-kich-drama`. Mục đích file: chủ dự án dùng để sửa skill, khung, trợ lý cho tốt hơn. Ghi theo thứ tự thời gian: mỗi mục là điều agent làm chưa tốt (hoặc thiếu), chủ dự án phản biện hay nâng cấp thế nào, agent sửa ra sao, và đề xuất sửa skill.

---

## 0. Model trợ lý và mức suy nghĩ

- **Sự cố:** máy chủ báo `unrecognized_model` với dòng `model: claude-sonnet-5-5` trong frontmatter `viet-phan-drama.md`, `soat-phan-drama.md`.
- **Sửa:** đổi thành `model: sonnet`, giữ `effort: medium`. Gọi thử hai trợ lý: cả hai tự báo `claude-sonnet-5-5`, khớp trường `model` trong transcript trợ lý. Claude Code 2.1.280.
- **Hạn chế:** chat chính không gõ được `/effort` (lệnh của người dùng). Frontmatter ghi medium; người dùng tự gõ `/effort` để xác nhận.
- **Đề xuất:** dùng bí danh (`sonnet`, `opus`) trong frontmatter trợ lý, không dùng ID đầy đủ.

---

## 1. Ý tưởng ban đầu bỏ mất mô-típ thắng của phim gốc

- **Agent làm:** đề xuất 3 ý (A "ngôi mộ không bia", B "tài xế của sếp", C "hợp đồng trả nợ"), khuyên A. Ý A mở bằng cô gái nghèo vừa chôn mẹ bị đuổi khỏi nghĩa trang; bà lão là bà nội giàu của nam chính.
- **Chủ dự án phản biện:** thích A, nhưng **thumbnail phải là cô gái ăn mặc hơi sang trọng giúp một bà lão nghèo khổ** như phim gốc "Kind Lady Defends An Old Woman Being Insulted, Unaware Her Son Is A Billionaire CEO". Phim đó viral vì mô-típ đầu phim, dễ đồng cảm, đang là mô-típ thắng.
- **Bài học:** tựa và thumbnail là sản phẩm. Mô-típ mở của phim mẫu đang thắng (ai giúp ai, trông thế nào, quan hệ bí mật với kẻ quyền lực) phải được giữ, chỉ đổi tình huống cụ thể. Agent đã đề xuất ý mà không hỏi phim đang nhắm tựa, thumbnail nào.
- **Hệ quả kéo theo:** khi bà lão thành **mẹ** CEO, nữ chính không thể là cháu ruột thất lạc của bà nữa (sẽ thành họ hàng với nam chính). Agent phải thiết kế lại bí mật: mẹ nữ chính là người cứu nam chính khỏi đám cháy.
- **Đề xuất sửa skill:**
  - Bảng hỏi bước 1 thêm câu đầu tiên: "Phim mẫu, tựa và thumbnail anh/chị nhắm là gì? Mô-típ mở nào phải giữ?"
  - Mỗi ý đề xuất phải ghi một dòng thumbnail (ai, mặc gì, đang làm gì) và một tựa mẫu kiểu YouTube.
  - Khi đổi quan hệ gia đình, rà ngay xung đột huyết thống giữa cặp chính.

---

## 2. Tình huống mở thiếu thực tế (vay ngân hàng làm bia mộ)

- **Agent làm:** nữ chính vừa chôn mẹ, mặc váy đẹp nhất của mẹ lên ngân hàng xin vay tiền làm bia mộ, gặp bà lão bị sỉ nhục ở sảnh ngân hàng.
- **Chủ dự án phản biện:** hỏi có vô lý không: ở Mỹ làm bia mộ có tốn tiền không, có phải đi vay không? Phim gốc cô gái chỉ giúp bà cụ cái bánh, hợp lý hơn.
- **Agent xác nhận:** bia mộ ở Mỹ khoảng 1.000–3.000 USD; người nghèo có chật vật, nhưng không ai lên ngân hàng vay riêng khoản đó. Gượng.
- **Bài học:** mỗi tình huống phải qua phép thử "ở Mỹ ngoài đời có ai làm vậy không" (chi phí, thủ tục, cơ quan, luật). Phim dựng ở Mỹ thì kiến thức đời sống Mỹ phải đúng.
- **Đề xuất sửa skill:** thêm bước tự soát "thực tế đời sống Mỹ" cho dàn ý: tiền bạc, bệnh viện, trường học, cảnh sát, tòa án, thuê nhà, CPS.

---

## 3. Chép tình huống của phim gốc (cái bánh) thay vì chép thủ pháp

- **Agent làm:** sau mục 2, đổi sang cảnh tiệm bánh: cô gái mua bánh sinh nhật cho mộ mẹ, bà lão thiếu 2 đô, cô đưa bánh cho bà. Đây gần y tình tiết phim gốc.
- **Chủ dự án phản biện:** không muốn liên quan bánh, khán giả xem quá nhiều trên YouTube; cần mới mẻ hơn. **"Copy ở đây chỉ là copy thủ pháp."**
- **Agent sửa:** tách thủ pháp ("người tử tế bênh người trông nghèo đang bị làm nhục trước đám đông, liều mất phần mình, không biết người đó là ai") khỏi tình huống. Đề xuất 3 tình huống mới (tiệm trang sức bị vu ăn cắp; nhà thuốc thiếu tiền thuốc tim; trạm xe buýt dưới mưa), mỗi cái có điểm mạnh và yếu. Chủ dự án chọn tiệm trang sức: nữ chính là nhân viên mặc đồng phục vest đen, đúng "hơi sang trọng" của thumbnail.
- **Bài học:** mục kho đã ghi rõ "không lặp lại y cách này", vậy mà agent vẫn lặp. Agent phải đối chiếu tình huống đề xuất với mục "Cách phim gốc" của kho trước khi đưa ra.
- **Đề xuất sửa skill:**
  - Bước 1 ghi luật: "Chép thủ pháp, không chép tình huống. Mỗi ý đề xuất đối chiếu với `Cách phim gốc` của các mục kho liên quan; trùng nơi, trùng vật, trùng hành động chính thì đổi."
  - Gợi ý thêm: chọn nơi để nữ chính có lý do mặc đẹp (thumbnail) và có lý do mất việc (động cơ thỏa thuận).

---

## 4. Thiếu hành động: thêm xô xát và đánh tay đôi nhờ Seedance

- **Chủ dự án nâng cấp:** đầu phim cần tình tiết căng thẳng, xô xát hơn; cả phim cần vài tình huống võ thuật, đánh tay đôi. Lý do: Seedance cho nhiều "đất diễn" hơn, đây là cách làm nội dung mới và hấp dẫn hơn bản gốc (phim gốc gần như toàn thoại).
- **Agent sửa:**
  - Cho nữ chính lý do biết đánh: cha là huấn luyện viên quyền anh, phòng tập của cha thành một nơi trong phim.
  - Đặt 4 trận, mỗi trận gắn với một mốc lật: tiệm (mở phim), hầm xe (~35%), nhà kho (đáy), con tin dao ở xử cuối.
- **Bài học:** khung `drama-da-den` rút từ phim thoại thuần nên không nhắc hành động. Với Seedance, hành động là lợi thế cạnh tranh.
- **Đề xuất sửa khung, skill:**
  - Khung `drama-da-den` thêm mục "Hành động (Seedance)": 3–4 trận tay đôi mỗi phim, đặt ở mở phim, giữa hồi 2, đáy, xử cuối. Mỗi trận phải lật thế hay lộ tính cách, không đánh cho có.
  - Bảng hỏi thêm câu: "Phim có cảnh hành động không, mấy trận, ai biết đánh và vì sao?"

---

## 5. Xô xát rồi đuổi việc phải hợp lý, đủ phân cảnh

- **Chủ dự án yêu cầu:** cảnh xô xát dẫn đến đuổi việc phải diễn ra hợp lý, tránh gượng; tính toán để đủ phân cảnh.
- **Agent sửa:** viết chuỗi nhân quả, mỗi bước leo thang có lý do. Gerald sợ lần kiểm tra đầu tiên → chiều VIP bằng mọi giá → không chịu đợi 20 phút lấy băng camera → Simone vu → Gerald cho vệ sĩ ra tay → nữ chính **chỉ ra đòn một lần, khi bà lão bị đẩy ngã** (che người, không đánh trước) → nữ chính lật lời vu bằng chi tiết đã gieo (khóa vòng lỏng) → Simone vu lần hai "cô ta nhét vào tay áo tôi" → Gerald **có cớ** đuổi việc để giữ ghế.
- **Cái giá:** cú lật "đó là mẹ tôi" dời tới phút 8–9, muộn hơn khung (4%, khoảng 3 phút). Lời hứa ở tựa (nữ chính bênh bà lão) vẫn giao ở khoảng 3 phút.
- **Lỗi nhỏ của agent:** ghi vào dàn ý "đã thống nhất" chuyện dời cú lật trước khi chủ dự án đồng ý. Đã sửa câu đó ở bản sau.
- **Bài học:** cảnh mở có xô xát cần khoảng 8–10 phút, không phải 3. Mỗi hành vi của kẻ ác phải có lý do sợ hay lợi.
- **Đề xuất sửa khung:** ghi rõ cú của tựa có hai lớp. Lớp hành động trong tựa ("bênh bà lão") giao trước 4%. Lớp lộ thân phận ("con bà là tỷ phú") được dời tới khoảng 12–14% khi cảnh mở có xô xát.

---

## 6. "Dẫn sai" (misdirection): thủ pháp chủ chốt của niche

- **Chủ dự án nêu:** khán giả niche này xem vì điểm chạm, cú lật, đặc biệt là bất ngờ. Biên kịch giỏi dẫn người xem nghĩ tình huống tiếp theo là A, rồi sự thật lại là B; đạo diễn Hollywood rất giỏi việc này. Chủ dự án nhờ đặt tên.
- **Agent đặt tên:** **misdirection**, gọi chung là **"dẫn sai"**. Các dạng con:
  - **red herring** (manh mối giả);
  - **setup – subversion** (gài khuôn quen rồi bẻ);
  - **double reversal** (lật xong bị lật ngược).
- **Agent làm:** soát chi tiết các mục kho của hai phim nguồn, rồi áp 9 chỗ dẫn sai vào dàn ý:
  1. Gã đội mũ quay clip trong tiệm: khán giả đoán CEO giả dạng, thật ra là Lance, em họ phản diện.
  2. Lật xong bị giật lại (KB294): vòng rơi từ tay áo Simone, Simone lập tức vu "cô ta nhét vào".
  3. Kẻ ác tự đặt cược (KB309): Gerald cược nuốt ghim tên; Damon đặt ghim lên quầy đòi cược.
  4. Evelyn trở mặt ở vỉa hè: khán giả chờ cảm ơn, bà siết tay hỏi lạnh "ai đưa cái này cho cô?".
  5. Manh mối giả về kẻ đốt nhà: Evelyn đáng ngờ (bà ký giấy đuổi bảo mẫu), Vivian tử tế; lật ở N20.
  6. Kế thoát thành bẫy (KB221): Nia khai đang bị kiện tội hành hung để khỏi cưới; Evelyn mừng.
  7. Đồ của kẻ vu mới giả (KB300): váy Nia là độc bản, váy Simone là hàng nhái.
  8. Trùng danh xưng (KB308): quà gửi "Mrs. Hale", Tricia nhận vơ.
  9. Chỗ dựa quay lưng (KB302): Vivian gọi nhân chứng, nhân chứng khai chống bà.
- **Bài học:** dàn ý bản đầu chỉ có cú lật tuyến tính (biết trước hướng), không có dẫn sai.
- **Đề xuất sửa skill, khung, công cụ:**
  - Khung thêm mục "Dẫn sai": mỗi phần 10 phút ít nhất 1 chỗ (khán giả đoán A, sự thật B), ghi `**Dẫn sai:**` trong cột Việc của bảng mốc. B phải khớp mọi chi tiết đã gieo (xem lại thấy hợp lý).
  - Kho: gắn nhãn "dẫn sai" cho các mục KB294, KB300, KB302, KB308, KB309, KB221, KB220, KB303 để tra nhanh.
  - `kiem_drama.py` hoặc soát dàn ý có thể đếm số dẫn sai mỗi phần (máy đếm được).

---

## 7. Logic chặt: lỗ hổng tình tiết và liên tục hình ảnh

- **Chủ dự án nêu:** phim AI rất dễ thiếu logic: tình huống, tình tiết, cả cảnh đánh nhau. Ví dụ bị tát má trái nhưng clip sau không tả rõ, AI vẽ thành má phải (vì tả để viết prompt ảnh). Dàn ý phải thật chặt.
- **Agent rà lại và tìm ra lỗ hổng thật trong dàn ý của chính mình:**
  - Lance đứng nhìn dì mình (Evelyn) bị sỉ nhục mà không can → thêm động cơ: hắn quay clip bê bối để hại Damon đúng ngày kiểm tra.
  - Tricia là vợ Lance, nhưng Lance đi tiệc với Simone → đổi Tricia thành em gái Lance.
  - Jaylen bị đuổi học vì nợ học phí: trường công ở Mỹ miễn phí → đổi thành mất nhà thì CPS đưa Jaylen đi (Nia là người giám hộ).
  - Vì sao quản lý, khách VIP không nhận ra mẹ chủ; vì sao bà mặc nghèo và vào đúng tiệm này → tập đoàn mới mua chuỗi 3 tháng, bà tránh báo chí, ngày giỗ chồng bà đi xe buýt như hồi nghèo, đồng hồ chết máy.
  - Động cơ của người sắp đặt (vì sao ép cưới thay vì nói thẳng) → không có chứng cứ, Vivian nắm nửa hội đồng, họ Hale che chắn cho Nia.
  - Chứng cứ cơ thể rõ ràng: người cứu bỏng **lòng** bàn tay (bế qua cửa cháy), kẻ châm lửa bỏng **mu** bàn tay phải (xăng bắn ngược).
  - Huy hiệu khắc "D.H." đổi nghĩa: N26 bị dùng để buộc tội "mẹ cô ăn cắp đêm cháy", N29 thành bằng chứng minh oan.
  - Lance mang dao vào tiệc có an ninh → đổi thành dao ăn trên bàn tiệc.
  - Nữ chính nghèo có đồng hồ thông minh để bấm định vị khi bị bắt → gieo: Damon tặng sau vụ hầm xe.
- **Agent thêm vào dàn ý hai mục mới:**
  - **Lý do nền:** giải thích mọi điều "vì sao" của tình huống chính.
  - **Sổ liên tục:** lịch ngày từng mốc; bảng vết thương (ai, vết gì, bên trái hay phải **của chính nhân vật**, từ mốc nào tới mốc nào); đường đi của từng vật (huy hiệu, vòng, đồng hồ, thẻ tên, nhẫn, găng…); bảng ai biết gì, lúc nào.
- **Trợ lý soát phần 1 còn bắt thêm:** Damon nói "You made a bet" mà không có cách nào biết vụ cược → thêm câu Gerald tự khoe. Tức là lỗi "ai biết gì" xảy ra cả ở cấp clip.
- **Bài học:** dàn ý bản đầu của agent có ít nhất 8 lỗ logic mà agent không tự thấy cho tới khi được nhắc.
- **Đề xuất sửa skill:**
  - Mẫu `00-dan-y.md` bắt buộc có `## Lý do nền` và `## Sổ liên tục` (ngày, vết thương trái/phải, đường đi vật, ai biết gì).
  - Trước khi báo duyệt, chat chính tự rà logic theo danh sách:
    - mỗi nhân vật có mặt mà không hành động thì vì sao;
    - quan hệ gia đình có mâu thuẫn không;
    - đời sống Mỹ có đúng không;
    - mỗi chứng cứ có gieo trước không;
    - mỗi vật xuất hiện có lý do ở đó không;
    - ai biết điều gì, từ lúc nào.
  - Trợ lý viết và soát: mỗi clip có vết thương hay vật thì ghi rõ bên trái, phải trong `Khung:` và đối chiếu Sổ liên tục. Cảnh đánh ghi tay nào, chân nào, hướng nào.
  - `kiem_drama.py`: nhắc khi một clip nhắc vết thương mà không ghi "trái" hay "phải" (máy đếm được).

---

## 8. Chủ động làm nội dung hấp dẫn hơn nhờ Seedance

- **Chủ dự án yêu cầu:** suy nghĩ cẩn trọng, tư vấn thêm điều làm kịch bản hấp dẫn hơn, vì Seedance có nhiều đất diễn.
- **Agent đề xuất 8 điểm; chủ dự án chọn 1–7, bỏ 8:**
  1. **Lửa thành sợi chỉ xuyên phim**: kẻ ác đốt nhà kho ở đáy; nam chính sợ lửa từ năm chín tuổi vẫn lao vào bế nữ chính ra, như năm xưa mình được bế. Hành động lớn nhất phim trả đúng vết thương nhân vật.
  2. **Hồi tưởng chia 4 mảnh, mỗi mảnh đổi nghĩa**: người cứu → đôi tay không mặt → bóng người cầm can → lộ mặt kẻ châm lửa. Dẫn sai bằng hình.
  3. **Người sắp đặt "kêu sói"**: giả ngất ở N09, ngất thật ở N25; nam chính tưởng giả nên đứng yên, nữ chính làm hồi sức tim cứu. **Vá luôn một lỗ logic:** người sắp đặt hôn mê nên ở N26 không có mặt để bênh nữ chính.
  4. **Bộ ba trận với cùng một đối thủ (Rocco)**: thắng bất ngờ → thua → nữ chính tự thắng trận cuối; nam chính chỉ cứu cô khỏi lửa, không cứu khỏi đàn ông. Nữ chính mạnh, chia đất diễn công bằng.
  5. **Livestream làm vũ khí rồi phản đòn**: kẻ ác livestream làm nhục, cú lật xảy ra ngay trên sóng, bình luận đổi chiều. Hiện đại, lạ hơn phim gốc.
  6. **Găng tay của kẻ ác**: luôn đeo găng nơi đông người, chỉ tháo khi khoe sẹo nhận công; lộ lớn thì bị buộc tháo. Gieo rẻ mà hiệu quả.
  7. **Cảnh dạy võ có tán tỉnh**: nữ chính dạy nam chính đấm bao, chạm tay sửa thế. Seedance làm cảnh vận động tốt hơn cảnh ngồi nói.
  8. *(Bỏ)* Đoạn mở 15 giây nhảy trước cao trào rồi "3 tháng trước": rủi ro hé kết quả, thêm 2–3 clip.
- **Bài học:** các điểm này lẽ ra phải có ngay ở bản dàn ý đầu, không đợi chủ dự án hỏi.
- **Đề xuất sửa skill, khung:**
  - Khung thêm mục "Lợi thế Seedance":
    - vết thương cũ của nhân vật thành cảnh hành động trả nợ ở đáy;
    - hồi tưởng chia mảnh cho bí mật chính;
    - đối thủ tay chân lặp 3 trận leo thang;
    - một sự kiện có đám đông hay livestream;
    - một cảnh vận động thay cảnh ngồi nói trong đoạn chung mái.
  - Bước 2 tự rà: "Mỗi phần có ít nhất một cảnh vận động hay hành động không?"

---

## 9. Quy trình, công cụ, token

- **Mẫu lời giao soát:** chat chính thêm vào lời giao `soat-phan-drama` yêu cầu "tóm tắt từng cảnh 2–3 dòng (ai, mốc, cảm xúc đỉnh) và số clip 15 giây". Nhờ đó chat chính báo được mà không phải đọc file phần. Đề xuất đưa vào mẫu lời giao trong SKILL.md.
- **Ước credit:** công cụ chưa in tổng giây và ước credit. Phần 1: 620 giây × 5 × 1,1 ≈ 3.410 credit. Đề xuất `kiem_drama.py` in thêm tổng giây, số clip 10/15 giây, ước credit theo mức.
- **Bảng hỏi chưa đủ một lượt:** câu 3–6 (cặp chính, bí mật, kẻ ác, nợ đầu phim) không được trả lời riêng. Cuộc bàn ý tưởng kéo dài 5 vòng, các câu đó được chốt ngầm theo mặc định agent đưa. Đề xuất: bảng hỏi tách hai lượt, lượt 1 chốt mô-típ, thumbnail, ý tưởng; lượt 2 mới hỏi cặp chính, bí mật, kẻ ác.
- **Ghi lại cả file dàn ý:** do sửa gần hết bảng mốc nên chat chính ghi lại cả file một lần, các lần sau sửa bằng Edit. Chấp nhận được, nhưng nên tránh bằng cách làm đủ logic ngay từ bản đầu.
- **Phần dài hơn 10 phút:** phần 1 dài 620 giây (10 phút 20), 48 clip, 4,8 clip/phút. Trong khuôn.
- **Trợ lý viết tự thêm chi tiết logic:** Evelyn quay lại lấy đồng hồ bỏ quên nên vào đúng lúc Damon xem camera; cảnh sát chỉ có tiếng và ánh đèn. Tốt, nên giữ tinh thần này trong mô tả trợ lý.

---

## Tóm tắt đề xuất (để sửa nhanh)

1. Bảng hỏi: hỏi phim mẫu, tựa, thumbnail và mô-típ mở phải giữ trước tiên; tách hai lượt.
2. Luật "chép thủ pháp, không chép tình huống": đối chiếu với `Cách phim gốc` của kho.
3. Soát thực tế đời sống Mỹ.
4. Khung `drama-da-den` thêm: Hành động (3–4 trận), Dẫn sai (≥1 mỗi phần), Lợi thế Seedance, cú của tựa hai lớp.
5. Mẫu dàn ý bắt buộc có `Lý do nền` và `Sổ liên tục`; chat chính tự rà logic theo danh sách trước khi báo duyệt.
6. Trợ lý viết, soát: ghi trái/phải của chính nhân vật cho vết thương và vật; kiểm "ai biết gì" từng câu thoại.
7. `kiem_drama.py`: in tổng giây, số clip 15 giây, ước credit; nhắc vết thương thiếu trái/phải; đếm dẫn sai mỗi phần.
8. Mẫu lời giao soát có yêu cầu tóm tắt từng cảnh và số clip 15 giây.
9. Frontmatter trợ lý dùng bí danh model (`sonnet`).
10. Đặt tên chung: **dẫn sai** (misdirection) cùng các dạng con red herring, setup–subversion, double reversal.

---

## 10. Bổ sung sau phiên: "drama thoại" và "drama da đen", lỗ hổng cảnh đánh

- **Chủ dự án hỏi:** phim là drama da đen, sao hệ thống nhận là drama thoại; có nhầm không, có ảnh hưởng chất lượng không?
- **Giải thích:** không nhầm. Hai nhãn đo hai thứ khác nhau.
  - `Thể loại: drama-da-den` là nội dung: chọn khung và kho thủ pháp.
  - `Loại phim: drama_thoai` là cách dựng và gen trên web (Spec 44): khuôn cảnh, clip, máy Seedance hay Veo.
  - Gây hiểu nhầm vì chữ "drama" có ở cả hai nhãn, và skill `/bien-kich-drama` được mô tả là "drama thoại".
- **Lỗ hổng phát hiện:**
  - `kien-thuc/drama-thoai.md` và trợ lý `viet-phan-drama` không có hướng dẫn viết cảnh đánh. Hướng dẫn đó ở `kien-thuc/tran-danh.md`, chỉ skill `/bien-kich` dùng.
  - Phim drama có hành động (mục 4) sẽ thiếu mẫu trận.
- **Đã làm:** BAN-GIAO.md của phim dặn: phần 3, 5, 7 (có trận) thì trợ lý viết và trợ lý soát đọc thêm `tran-danh.md` (đúng mục cần).
- **Đề xuất sửa:**
  - Đổi tên dòng `Loại phim:` thành `Kiểu dựng:` hay tương tự để khỏi lẫn với thể loại (sửa ở web và công cụ, repo chính).
  - `drama-thoai.md` thêm mục ngắn "Cảnh đánh trong drama thoại", trỏ tới `tran-danh.md`.
  - Mô tả `viet-phan-drama` và `soat-phan-drama`: phần có trận thì đọc `tran-danh.md`. Mỗi đòn ghi ai, tay hay chân nào (trái/phải của chính nhân vật), hướng nào, trúng đâu, vị trí từng người.

---

## 11. Sau khi gen phần 1 (02/10): ngoại hình bà lão và mở đầu video

Chủ dự án gen xong 48 clip phần 1 trên web, xem lại và thấy hai lỗi. (Lỗi ngoại hình cặp chính bị web đoán sai tuổi, đồ, nét ghi riêng ở `the-shop-girl-mo-ta-nhan-vat.md`.)

### 11a. Bà lão "nghèo" mà trông không nghèo

- **Agent làm:** cụm NV02 Evelyn ghi "worn brown wool cardigan coat over a plain cream blouse, an old canvas tote bag". Chữ "worn", "old" quá nhẹ: ảnh ra một bà cụ ăn mặc gọn gàng, tử tế.
- **Chủ dự án phản biện:** quần áo chưa thể hiện sự nghèo khó, phải gen lại tài sản. Drama làm mọi việc phải "quá lên": khán giả phải nhìn ảnh là thấy ngay bà nghèo, thì cú lật "con bà là tỷ phú" mới đắt.
- **Agent sửa:** viết lại cụm, mỗi món đồ có một dấu nghèo nhìn thấy được. Mũ len bạc màu thủng một bên, áo khoác sờn rộng thùng thình rách túi, hai cúc khác màu, vá khuỷu tay, váy hoa bạc màu, tất len dày cũ, giày đen nứt hở đế, túi vải sờn ghim kim băng; người gầy yếu, da nhiều nếp nhăn, mắt mệt. Giữ logic cũ: ngày giỗ chồng bà mặc lại đồ thời còn nghèo. Thêm **dạng 2 từ N06** (áo cashmere, ngọc trai), vì mẹ CEO về sau không thể mặc đồ rách cả phim.
- **Bài học:** với vai nghèo (hay vai giàu, vai sang), cụm tiếng Anh phải ghi **dấu nhìn thấy được** (vá, sờn, rách, nứt, bạc màu, kim băng), không ghi tính từ chung ("worn", "old", "simple"). Nhân vật đổi thân phận giữa phim thì có dạng 2 ngay từ dàn ý.
- **Đề xuất sửa skill:** luật cụm cố định thêm câu: "Vai nghèo hay giàu: mỗi món đồ một dấu nhìn thấy được; quá lên một bậc so với đời thật". Bước 3 duyệt báo cụm ngoại hình cặp chính và người bị làm nhục cho chủ dự án xem trước khi viết phần.

### 11b. Mở đầu video chậm, chưa kịch tính

- **Agent làm:** phần 1 đi theo thứ tự thời gian. Họp sáng (Gerald dọa kiểm tra), tin nhắn viện phí, giấu dây chuyền, bà lão vào thay pin; tới phút 2 mới vu, phút 4–6 mới xô xát, phút 8–9 mới lật "đó là mẹ tôi". Sỉ nhục còn "lịch sự": đổ túi, lôi đi khám người.
- **Chủ dự án phản biện:** mở màn chưa hấp dẫn, chưa kịch tính như mong đợi. Vào phim phải đẩy cao trào luôn, có giành giật, xô xát ngay từ đầu để khán giả bị cuốn. Điều cần giải thích thì dùng hồi tưởng hoặc lời nghĩ. **Nhưng** bản đầu cũng có đoạn chưa setup bối cảnh đủ cho khán giả hiểu hết, nên vẫn phải thêm cảnh làm rõ; chỗ cảm xúc cần đẩy thì thêm một phân cảnh.
- **Agent sửa (dàn ý N01–N05):**
  - N01 (0–1,5 phút): mở thẳng giữa trận. Simone và Rocco giành giật túi của bà; túi rách, Simone dẫm vỡ kính ảnh chồng bà; Gerald hét một câu thay cả cảnh họp ("ông Hale tới trong một tiếng nữa"); Simone tát bà (má trái), hắt cà phê đá lên đầu bà; đám đông cười, quay điện thoại. Chữ "Hai mươi phút trước".
  - N02: hồi tưởng dựng nền rõ từng việc (ai là ai, vì sao bà ở tiệm, vòng tuột vào tay áo Simone thế nào), kết bằng Rocco giật túi, nối khớp hình với clip đầu. Khán giả biết bà vô tội **trước** khi Nia bênh, nên ức hơn.
  - N03: về hiện tại, Nia chắn và nhận cú tát thay bà, rồi trận ngắn. N04: đuổi cả hai ra vỉa hè đang mưa. N05: lật "đó là mẹ tôi" ở ~10 phút, Damon bắt Gerald xin lỗi trước đám đông vừa cười.
  - Điều nhân vật giấu (nợ viện, em trai) chuyển thành lời nghĩ. Mỗi đỉnh cảm xúc một clip riêng (bà nhặt kính ảnh chồng, Nia nhận cú tát, Damon lau mặt mẹ). Phần 1 từ 10 lên khoảng 11,5 phút.
- **Cái giá:** gen lại gần trọn phần 1 (khoảng 3.500–3.800 credit). Web ghép clip cũ theo độ giống chữ khi Dán lại kịch bản, nên clip giữ nguyên ý thì giữ nguyên chữ cũ để cứu được ảnh, video đã gen.
- **Bài học:**
  - "Cú của tựa" không chỉ là lúc nữ chính bênh: khán giả niche này cần thấy **sự làm nhục cực độ ở giây đầu**. Dựng nền theo thứ tự thời gian là cách kể chậm nhất.
  - "Quá lên" là chuẩn của drama: tát, hắt nước, dẫm đồ kỷ niệm, ném ra mưa trước đám đông; kẻ ác bị trả trước đúng đám đông đó.
  - Mở giữa trận không được làm khán giả lạc: phải có hồi tưởng dựng nền đủ rõ, báo mốc thời gian dễ nhận, nối hình khớp.
  - Bài học này chỉ lộ ra khi xem video thật. Nên gen thử phần 1 trước khi viết các phần sau (đúng cách chủ dự án đang làm).
- **Đề xuất sửa skill, khung:**
  - Khung `drama-da-den` và bước 2 dàn ý: N01 mở giữa trận ở giây đầu (làm nhục "quá lên", có giành giật hay xô xát), rồi hồi tưởng "X phút trước" dựng nền; khán giả biết nạn nhân vô tội trước khi nữ chính bênh.
  - Bước 2 tự rà trước khi báo duyệt: "30 giây đầu có ai bị tổn thương chưa? Khán giả có hiểu ai là ai, vì sao ở đây không? Mỗi đỉnh cảm xúc có clip riêng không?"
  - Trợ lý viết: mỗi đỉnh cảm xúc một clip riêng; hồi tưởng ghi rõ ở tiêu đề cảnh và clip đầu.

### 11c. Nữ chính phải cứu bà ngay trong đoạn mở

- **Agent làm (bản viết lại lần một):** C001 mở giữa trận (giành túi, tát, hắt cà phê) nhưng Nia chỉ đứng trong đám đông; cắt sang hồi tưởng 14 clip; tới P021 (~phút 4) Nia mới lao ra chắn.
- **Chủ dự án phản biện:** Nia phải cứu bà cụ ngay trong phần mở đầu, như vậy mới giữ chân được khán giả.
- **Agent sửa:** C001 thêm hai clip: Nia lao vào nhận cú tát thay bà (má trái của Nia), rồi chộp cổ tay Simone giữa không trung ("Lần thứ hai thì không"), dừng hình, mới lên "Hai mươi phút trước". Hồi tưởng gọn còn khoảng 10 clip. C003 mở từ đúng khung Nia giữ tay Simone, bỏ cú tát cũ. Nia chỉ đỡ, chưa đánh; cú ra đòn thật để lúc Rocco đẩy bà ngã.
- **Bài học:** mở giữa trận mà nhân vật chính chưa hành động thì vẫn là "khán giả chờ". Đoạn mở phải có cả nạn nhân bị làm nhục **và** người hùng ra tay (cảnh thumbnail) trước phút 1; cắt sang hồi tưởng ngay ở đỉnh căng (cliffhanger), khán giả xem hồi tưởng vì muốn biết chuyện gì xảy ra sau đó. Hồi tưởng càng dài, cú cắt càng phải mạnh.
- **Đề xuất sửa khung, skill:** khung `drama-da-den` mục mở phim: "Trước phút 1: làm nhục cực độ + nữ chính ra tay (cảnh thumbnail) + dừng hình ở đỉnh căng; hồi tưởng dựng nền tối đa khoảng 2 phút." Bước 2 tự rà: "Cảnh thumbnail rơi vào giây thứ mấy?"

### 11d. Người yếu thế không thắng bằng sức

- **Agent làm:** trận N03 (cả dàn ý và hai bản phần 1): Nia né cú túm, **vặn tay phải Rocco ra sau lưng, ép mặt hắn xuống quầy kính**, giữ hắn trong lúc nói chuyện. Lý do biết đánh: cha là huấn luyện viên quyền anh. Trận N13 còn dựa vào đó ("Rocco đã biết thế vặn tay của cô").
- **Chủ dự án phản biện:** nữ chính là người yếu thế; một cô gái mảnh khảnh vặn tay được gã vệ sĩ to gấp đôi là không logic.
- **Agent sửa:** Nia không bao giờ đè Rocco bằng sức. Rocco túm vai, cô thoát bằng một thế gỡ tay (xoay về phía ngón cái của hắn, cha dạy), kéo bà ra sau lưng mình. Rocco lao tới lần nữa, Nia né; hắn dẫm vũng cà phê đá Simone hắt ở N01 trên sàn đá bóng, trượt, đập trán phải vào cạnh quầy, choáng. Thắng nhờ nhanh trí và đồ đã gieo, không ai "đánh" Rocco. Vết của Rocco đổi từ "băng cổ tay phải" thành "rách trán phải"; N13 sửa theo và đánh dấu cần bàn lại.
- **Bài học:**
  - "Biết võ" chỉ cho người yếu thế **kỹ năng thoát và né**, không cho sức thắng người to hơn. Khán giả drama đồng cảm với người bị dồn; nữ chính đè được gã khổng lồ thì mất thế yếu, mất đồng cảm, và trông giả.
  - Người yếu thế thắng bằng: nhanh trí, địa hình (sàn trơn, cửa, cầu thang), đồ đã gieo, kẻ ác tự hại vì hung hăng, đồng minh bất ngờ, hay người hùng tới đúng lúc. Mỗi cách phải gieo trước (vũng cà phê phải thấy rõ ở clip hắt).
  - Kiểm logic cảnh đánh bằng câu hỏi: "Ngoài đời, người cỡ này làm được đòn này với người cỡ kia không?" Đây là cùng một phép thử "đời thật có ai làm vậy không" ở mục 2, áp cho cơ thể.
- **Đề xuất sửa skill, khung:**
  - Khung `drama-da-den` mục Hành động: "Nữ chính là người yếu thế: không thắng đàn ông to hơn bằng sức (vặn, đè, quật, đấm gục). Chỉ thoát, né, nhanh trí, dùng địa hình và đồ đã gieo; kẻ ác ngã vì chính sự hung hăng của hắn."
  - Trợ lý viết và soát drama: soát mỗi đòn theo cỡ người hai bên (chiều cao, cân nặng ở Cụm cố định); đòn của người nhỏ trúng người to phải có lý do ngoài sức.
  - Dàn ý: mỗi trận ghi một dòng "thắng nhờ gì" và chỗ đã gieo cái đó.
