# Grok drama: hai luật, máy, clip, cỡ cảnh, hành động (Spec 69)

Nguồn sự thật cho `/bien-kich-grok`: kịch bản drama thoại gen cả phim bằng Grok (108 credit mỗi video). Thay mục 2, 3, 4, 8, 9 của `drama-thoai.md`; mục 1 (khuôn file), 5 (thoại, lời nghĩ), 6 (nhịp), 7 (ghi chú nối) đọc ở `drama-thoai.md`, dùng chung. Grok mạnh ở một người nói, giữ mặt; yếu ở cú máy, hành động thân thể, đông người, đồ nhỏ, ô, cảnh tối trong nhà. **Mục 0 đứng trên mọi mục khác.**

**Máy lo, không cần nhớ:** `py -3 cong-cu/kiem_drama.py <file phần>` nhận kịch bản Grok khi có clip `Máy: Grok …`: LỖI clip không phải `Grok 10s`/`Grok 15s` (Veo, Seedance), trần 3 từ mỗi giây; NHẮC chữ hành động nặng, `Khung:` quá 4 người, ô trong cảnh trong nhà, đám đông có mặt rõ, clip/phút, lời nghĩ. NHẮC "clip Grok không có cú máy hay góc có ý đồ" là của bản chép cũ: **giữ, không sửa** (mục 0, luật 2). `py -3 cong-cu/dan_y_drama.py phan <file phần>` NHẮC hai luật: cảnh thiếu khối đầu cảnh, clip đầu cảnh thiếu người có mặt, cú máy động, đặc tả, shot định vị giữa cảnh, người có mặt nói mà không có ở `Khung:`. NHẮC thì sửa, hay giữ và ghi lý do vào báo cáo.

## 0. Hai luật (anh/chị chốt 30/10)

Treatment dựng **mỗi shot một video Grok** rồi nối cắt cứng: tiếng của shot nào phát trọn trên hình shot đó, không tràn sang shot kề. Đo cùng một lời thoại (DM002 C1): bản viết kiểu cũ có 12/39 shot thoại để câu phát trên mặt người khác; bản viết theo hai luật 0/37, máy đứng yên 62/62. Chất lượng điện ảnh xếp sau hai luật này.

**Luật 1. Tiếng của ai thì hình người đó.**
- Shot có thoại: trong khung **chỉ người nói** (ghi "trong khung chỉ có X"), hoặc **qua vai người nghe** (ghi "qua vai Y": lưng, vai Y mờ ở mép khung, X rõ mặt). Mỗi shot một người nói.
- Phản ứng của người nghe là **shot im riêng** sau câu ("môi khép, không nói"). Không đặt câu lên cận người nghe.
- Người nói ngoài khung chỉ khi người đó **vắng mặt thật** (điện thoại, loa, sau cánh cửa đóng): không ghi ở `Khung:`, cách nói ghi `(điện thoại)`, `(qua loa)`. Người có mặt trong cảnh thì nói trong khung.
- Shot thoại ghi hướng nhìn: "mắt nhìn <người nghe> bên trái/phải khung, không nhìn ống kính".

**Luật 2. Phối cảnh đúng.**
- **Máy đứng yên mọi shot**, ghi "máy đứng yên". Không đẩy vào, lùi ra, lia, vòng, nâng, máy ngước, bám, chuyển nét.
- Cỡ cảnh: toàn (theo hướng máy dàn cảnh), trung, cận, qua vai; góc thấp, góc cao được. Không đặc tả đồ vật, không cực cận mắt, không cận hai người trở lên.
- **Chuỗi hành động** (đưa vật, bước tới, đứng dậy, ném đồ, nắm tay) là **một shot toàn theo hướng máy dàn cảnh, một cú liền**: ghi đúng cụm "một cú liền" (treatment đặt 10 giây). Không bẻ thành nhiều shot nhỏ.
- Clip đầu cảnh mở bằng shot toàn thấy **mọi người có mặt**, đúng chỗ ở dòng `Mở cảnh:`. Giữa cảnh không có shot định vị mới.
- **Người vào giữa cuộc thì mở cảnh mới cùng nơi, cùng buổi**: tiêu đề `## C…` y nơi, y buổi cảnh trước. Clip đầu cảnh mới mở bằng shot người vào: "toàn theo hướng máy dàn cảnh, máy đứng yên, một cú liền: X đã đứng trong khung cửa <cửa nào, bên nào khung>, thấy trọn người, mặt rõ; X đi … tới đứng <chỗ>; <người cũ> giữ nguyên chỗ; không ai nói". Treatment vẽ shot này trên ảnh dàn cảnh cảnh trước, X đứng ở cửa (vẽ X ở chỗ mới thì video ra hai X). Mỗi cảnh một người vào.
- Người rời đi: cảnh sau cùng nơi, cùng buổi, `Có mặt:` không còn người đó; việc rời ở shot toàn cuối cảnh trước (một cú liền) hay ngoài khung.

**Khối đầu cảnh**, ngay dưới `Có mặt:`, trước clip đầu (treatment đưa cả khối vào prompt dàn cảnh):

```
## C002 · Nhà hàng Grand Sovereign · trưa · N02
Có mặt: Hattie, Brooke, Evelyn, Nia
Mở cảnh: Hattie trái · Brooke giữa · Evelyn phải
Vào: Nia từ cửa kính cuối phòng bên phải, tới đứng giữa Hattie và Brooke
Máy dàn cảnh: nhìn dọc phòng ăn về phía cuối phòng; tường kính bên trái, cửa kính ra vào ở cuối phòng bên phải; bàn số 9 của Hattie sát tường kính
Tóm tắt: Nia mang hộp thuốc bà để quên xuống, làm chứng bà ở 1801; Brooke ném tiền, gọi bảo vệ.
Vai: Hattie, khách Suite 1801, điềm tĩnh. Brooke, trưởng phục vụ. Evelyn, khách bàn bên. Nia, chị dọn phòng, sáng nay dọn phòng 1801.
Tiến trình:
1. (N02) Nia vào với hộp thuốc, làm chứng; Brooke và Evelyn mỉa; Brooke ném tiền, báo bảo vệ đang tới.
Kết cảnh: tiếng giày vang ở cửa; Nia quay đầu nhìn về phía cửa kính.

### P008 · N02 lật: Nia vào
Máy: Grok 15s
Khung: Brooke, Hattie, Evelyn, Nia
Hình: toàn theo hướng máy dàn cảnh, máy đứng yên, một cú liền: Nia đã đứng trong khung cửa kính đang mở ở cuối phòng bên phải khung, thấy trọn người, mặt rõ, tay phải cầm hộp thuốc nhỏ; Nia đi giữa các bàn tới đứng cạnh bàn, giữa Hattie và Brooke; Hattie ngồi bàn bên trái khung quay đầu nhìn Nia, Brooke đứng giữa khung, Evelyn ở bàn bên phải khung, ba người giữ nguyên chỗ; không ai nói.

### P009 · Nia làm chứng bà là khách 1801
Máy: Grok 15s
Khung: Nia, Hattie, Brooke
Hình: shot 1 qua vai Hattie, máy đứng yên: lưng, vai và tóc Hattie mờ ở mép trái khung, Nia đứng bên phải khung rõ mặt, nói ấm, rõ, mắt nhìn xuống bà, không nhìn ống kính. Shot 2 cận Brooke, trong khung chỉ có Brooke, máy đứng yên: lông mày nhướn, nói lạnh, mắt nhìn Nia bên trái khung, không nhìn ống kính. Shot 3 cận Nia, trong khung chỉ có Nia, máy đứng yên: cằm nâng lên, không lùi, môi khép; không nói.
Thoại: Nia (ấm, rõ): "Ma'am, you left your blood pressure pills in 1801."
Thoại: Brooke (lạnh): "And who are you to speak at my table?"
```

- `Có mặt:`, `Mở cảnh:`, `Vai:` chỉ ghi người có mặt ở cảnh này. `Mở cảnh:` là chỗ lúc cảnh mở; cảnh nối tiếp thì người cũ giữ y chỗ cảnh trước. `Vào:` chỉ ở cảnh mở bằng người vào. `Máy dàn cảnh:` chép y nhau ở mọi cảnh cùng nơi, cùng buổi.

## 2. Máy

- Mọi clip `Máy: Grok 15s` (bản RenderY, user chốt 27/10): clip là nhóm shot để viết prompt; treatment dựng mỗi shot một video 6 hay 10 giây (shot "một cú liền" 10 giây), người dựng chỉnh trên trang. Trần 3 từ mỗi giây tính theo clip (15 giây 45 từ). Clip chỉ một nhịp hay phản ứng không thoại: ghi `(ngắn)` cuối tên clip. Dàn ý không có dòng `Seedance:`, không clip 20–30 giây.

## 3. Clip Grok

1. **Clip gộp 2–3 nhịp liền** (lượt nói, mặt người nghe, phản ứng) thành 3–5 shot, mỗi shot ít nhất 2,5 giây. Đừng tách mỗi lượt hỏi–đáp ra một clip.
2. `Hình:` viết `shot 1 …`, mỗi shot: cỡ, góc, "máy đứng yên", ai trong khung (mục 0), ai bên trái, ai bên phải, hướng nhìn, nét mặt và diễn biến; giữ trục cả cảnh; vết, vật ghi trái/phải của chính nhân vật ở mọi clip thấy chúng; không tả lại mặt, tóc, áo. Không viết "mắt đỏ" (viết "mắt ngấn nước"); khinh thì "mép nhếch một bên, mắt không cười, nhìn từ trên xuống".
3. **Số người:** `Khung:` tối đa 4 người rõ mặt; càng ít càng tự nhiên. Cảnh đông người nói: mỗi câu một shot của người nói (mục 0), không lia qua lại giữa nhiều người.
4. **Đám đông, khách khứa:** chỉ thấy lưng hay mờ phía sau, không cận, không đếm, không cho họ làm việc riêng. Chọn nơi ít người (nhà, bếp, văn phòng, xe) thay cho sảnh đông.
5. **Người nói ngoài khung:** chỉ người vắng mặt thật (mục 0, luật 1).
6. **Đồ theo ảnh, không theo chữ:** người đổi đồ (khoác áo người khác, cởi áo khoác, bỏ mũ) từ 3 cảnh trở lên thì Cụm cố định có dòng `dạng` cho cả người mặc và người cho mượn; ít hơn thì ghi ở `Hình:`. Phụ kiện nhỏ ít thôi (Grok hay đổi màu, làm mất); món quan trọng gọi cùng một cụm ở `Hình:` mọi clip thấy nó.
7. **Ánh sáng theo ảnh:** cảnh đêm ghi chữ `đêm` ở tiêu đề cảnh (web gửi ảnh đêm). Trong nhà tránh cận mặt khi chỉ một đèn nhỏ (da lốm đốm): cho nơi một nguồn sáng rõ (đèn trần, cửa sổ, đèn bếp).
8. **Mưa, ô:** mưa chỉ thấy ngoài kính, trong nhà khô; trong nhà không cầm ô, ô gập để ở cửa (Grok hay mở ô, vẽ hai ô).
9. **Lời nghĩ:** Grok mấp máy môi ở khoảng nửa số clip lời nghĩ; giữ ít (máy nhắc quá 10%), điều giấu mà có người tâm sự thì nói thành thoại. Shot lời nghĩ: trong khung chỉ người nghĩ.

## 8. Cỡ cảnh và góc (máy đứng yên)

Máy đứng yên mọi shot (mục 0): cảm xúc nâng bằng cỡ cảnh, góc, shot im đúng lúc, không bằng cú máy. Chọn theo khoảnh khắc:

| Khoảnh khắc | Viết ở `Hình:` |
|---|---|
| Mở cảnh | toàn theo hướng máy dàn cảnh: mọi người có mặt, ai trái ai giữa ai phải |
| Người vào | cảnh mới cùng nơi cùng buổi, mở bằng shot toàn một cú liền (mục 0) |
| Kẻ mạnh, người cứu vừa vào | shot sau shot người vào: cận người đó *góc thấp* |
| Đối đáp leo thang | *qua vai* người nghe; kẻ đang thắng *góc thấp*, người bị nhục *góc cao*, đảo góc ở shot lật thế |
| Câu đắt, nhận ra | cận người nói, máy đứng yên; shot im kế là cận người nghe |
| Người bị lật thế, sững | shot im cận người bị lật ngay sau câu (biểu cảm ba nhịp); kẻ ác thua *góc cao* |
| Trao vật, giật, ném, nắm tay, đứng dậy | toàn theo hướng máy dàn cảnh, một cú liền, mọi người giữ chỗ |
| Đỉnh cảm xúc riêng tư | cận người đó, shot im; nói ở shot sau |
| Kết cảnh, bỏ lại một mình | toàn theo hướng máy dàn cảnh, người ở lại đứng yên, người kia đi ra khỏi khung |

**Không dùng:** mọi cú máy động, đặc tả đồ vật, cực cận mắt, shot định vị giữa cảnh, cận hai người trở lên, rõ nét tiền cảnh hay chuyển nét (trừ vai mờ của qua vai), dolly zoom, máy cầm tay rung.

Giữ từ drama:
- **Cỡ leo theo căng:** trung → qua vai → cận khi tới câu đắt; hạ về trung khi hé.
- **Phản ứng sau câu bom:** shot im cận người bị lật (biểu cảm ba nhịp); mặt kẻ ác, người chứng là các shot im kế, mỗi shot một người. Cần dài hơn thì một clip không thoại tên có `(ngắn)`.
- **Biểu cảm ba nhịp** ở mỗi đỉnh cảm xúc: trước (cố giữ), đỉnh (vỡ), sau (cố lấy lại), kèm cử chỉ nhỏ: nuốt khan, siết ngón, cắn môi, nhìn đi chỗ khác.
- **Vật** mỗi lần gieo hay gặt: thấy rõ trong tay người ở shot trung, cận, hay trên bàn ở shot toàn, gọi cùng một cụm; không đặc tả riêng. **Điện thoại:** thấy máy trong tay, nội dung đọc bằng lời.
- **Người chứng kiến** cảnh làm nhục: một, hai người rõ mặt; còn lại lưng hay mờ phía sau, điện thoại giơ lên mờ.

## 9. Hành động thân thể

- **Không** trận đánh, xô ngã, lôi kéo, vật lộn, kéo lê, ngã, nhảy ra khỏi xe, đỡ người đứng lên ngồi xuống, lửa, phép (Grok làm hỏng, sai logic). Dàn ý mặc định 0 trận.
- Cao trào bằng **lời, vật** (giấy tờ, điện thoại, tiền, nhẫn), **người có quyền** (luật sư, cảnh sát, chủ nhà) và **phản ứng mặt**. Người yếu thế thắng nhờ chứng cứ, lời, đồng minh đã gieo.
- **Chạm nhẹ** được, một động tác mỗi clip: tát một cái, nắm cổ tay, giật tờ giấy, đặt tay lên vai, ném đồ xuống bàn. Viết thành shot toàn một cú liền (mục 0); ghi tay trái/phải của người làm, trúng đâu; shot sau cận mặt người bị chạm.
- **Việc nặng xảy ra ngoài khung hay giữa hai clip:** clip trước người còn đứng, clip sau đã ngồi dưới sàn; nghe bằng tiếng động ngoài khung và lời kể, không quay lúc đang xảy ra.
- Đứng dậy, ngồi xuống: một người, một lần trong clip, tự làm; không ai đỡ ai.
