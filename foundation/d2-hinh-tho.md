# D2 — HÌNH THỞ (breathing room / negative space)

> **Vị trí: là MỘT PHẦN của [[d1-pacing]]** — pacing quyết nhịp chung và CHỖ nào cần chậm lại;
> hình thở là kỹ thuật cụ thể để chậm: **voice im nhưng hình vẫn chạy**. Đứng file riêng vì có
> luật chọn footage + bộ số liệu DNA riêng. Liên quan: [[e1-sound-design-nhac]] (ambient là thứ
> giữ ô thở "sống"; nhạc nền to lên khi voice im) · [[c6-footage-chu-ky]] (ô thở hay dùng
> footage chữ ký niche).
> **Trạng thái phần 3: DỰ KIẾN 🔸 — user duyệt mô tả vận hành rồi mới code phần thiếu.**
> Nguyên văn lời user: `GHI_CHEP_GOC.md §2`.

---

> ## 📌 LỆCH SO VỚI BẢN GỐC (user chốt 2026-07-13)
>
> **Luật CHỌN footage cho ô thở ĐỔI HẲN.** Bản gốc file này xoay quanh "footage ĐẮT
> tiếp tục trình chiếu" (§1, §2 bảng, §3 bước 2, §3b, §4 "đủ đắt đứng một mình") —
> chạy thật ở cả space lẫn deepsea (DS5-083) cho thấy **tool không chấm nổi "độ đắt"
> nên nhặt sai chủ thể** (sói tuyết → asteroid, phố mất điện → mực khổng lồ...).
> User xác nhận sai logic từ đầu và chốt luật mới:
>
> **Shot thở nhặt footage LIÊN QUAN footage liền trước ô — TIẾP TỤC CHỦ THỂ, chỉ ĐỔI
> CỠ CẢNH cho đỡ nhàm** (cảnh trước là cá mập → hình thở tiếp tục cá mập, khác cỡ).
> Không nhặt theo "đắt"/wide-aerial/điểm nhô nữa. Kho không có cùng chủ thể → rơi về
> cùng mood/khác cỡ (chấp nhận, không bỏ ô).
>
> Mọi câu "footage đắt cho ô thở" phía dưới đọc theo luật mới. Cơ chế + bảng điểm:
> `MO_TA_VAN_HANH_SHOT_THO.md §7`. Bản gốc giữ nguyên để đối chiếu.

## 1. Là gì

Hình thở = **khoảng voice ngừng nói nhưng hình vẫn chạy** — footage đắt tiếp tục trình chiếu
để bổ nghĩa, làm rõ, hoặc cho khán giả thỏa mãn/thấm đoạn voice vừa rồi. Nếu voice nói tiếp
ngay sau một câu nặng, cảm xúc bị cắt ngang; chính khoảng lặng làm câu đó "ghim" vào người xem.
Biết khi nào im lặng là dấu hiệu của editor giỏi.

Hai kiểu dùng chính (từ ví dụ gốc của user):
- **Thở cảm xúc:** sau câu có sức nặng — *"...và đó là lần cuối tôi gặp ông."* → 2.5s shot bàn
  tay ông pha trà (B-roll chậm) + tiếng nước rót + piano một nốt ngân.
- **Thở trình chiếu:** sau câu mở chủ đề — *"hôm nay chúng ta đến thăm Việt Nam xinh đẹp..."*
  → dừng voice, chiếu chuỗi footage signature: lúa Sapa, Hà Giang, vịnh Hạ Long, Ninh Bình...
  → **1 ô thở có thể là 1 HOẶC NHIỀU footage**, miễn hợp DNA niche và đoạn thoại đó.

## 2. Yếu tố ảnh hưởng

| Yếu tố | Tác động |
|---|---|
| **Sức nặng câu voice trước đó** | chỉ thở sau câu đáng thở: kết luận, câu đắt, cảm xúc, mở chủ đề — không thở sau câu chuyển/setup |
| **Kho footage đắt khả dụng cho đoạn đó** | quyết NGẮN HAY DÀI (yếu tố #1): nhiều footage đắt/signature → thở dài kiểu trình chiếu được; ít → ngắn; không có gì đủ đắt đứng một mình → cân nhắc bỏ ô này (shot nhạt = "chết hình"; nhưng có SÀN toàn video, §3) |
| **Sức chịu của khán giả tại điểm đó** | quyết NGẮN HAY DÀI (yếu tố #2): thở bao lâu mà khán giả vẫn chấp nhận ở lại nghe — theo sức nặng câu trước, vị trí trong video, gu khán giả niche (tham chiếu DNA). Mọi con số (1–15s, chill 30s...) chỉ là VÍ DỤ, không phải luật |
| **Vai chương** (hook / thân) | hook thường thở ngắn sau cú punch để đòn "cắm", thân thưa hơn — xu hướng, KHÔNG phải số cứng |
| **Mật độ thở trước đó** | không hai ô liền nhau; nhồi nhiều → video ì |
| **Lớp âm thanh** | ô thở cần ambient thật (gió, bước chân, nước) + nhạc nền dâng lên — không thì thành khoảng câm như lỗi |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN, chờ user duyệt

### Ai quyết cái gì (tách ỐNG/NÃO, NT4)

- **NÃO quyết:** ĐÂU thở (sau beat nào — word index, bắt buộc tại từ kết câu/mệnh đề),
  BAO LÂU (`breathing_after` giây, theo vai chương + số DNA), và HÌNH GÌ (concept footage
  đắt / chuỗi signature — phần chưa có, xem 3b).
- **ỐNG tính:** chèn khoảng `breathing_after` vào timeline sau segment voice
  (`cutter/timeline.py` gom beat thành run, cursor cộng dồn); cửa sổ phủ footage kéo dài
  qua ô thở, không hở hình (`packager/coverage.py`, cờ `is_breathing_tail`).

### Luồng chạy dự kiến (end-to-end) — QUYẾT ĐỊNH 2 PHA

> Độ dài ô thở KHÔNG chốt được ở bước direct — vì lúc đó chưa biết tìm được bao nhiêu footage
> đắt. Nó là quyết định 2 pha: direct đặt Ý ĐỊNH → source tìm hình → kết quả tìm CHỐT số cuối.

1. **Direct — đặt Ý ĐỊNH thở:** NÃO đọc foundation này + DNA niche (khi có) → chọn các vị trí
   ĐÁNG thở (word index, bắt buộc tại từ kết câu/mệnh đề `. ? ! : —`), mỗi vị trí gán: loại
   (cảm xúc / trình chiếu) + **khoảng đề xuất [min–max] giây**, KHÔNG fix một số cứng. Suy
   luận từ 2 câu hỏi: (i) đoạn này nhiều footage đắt tiềm năng không, (ii) khán giả tại điểm
   đó chịu thở bao lâu vẫn ở lại nghe. Đề xuất DƯ vài vị trí dự phòng (xếp hạng) cho thang
   cứu hộ bước 3. *Mọi con số trong foundation chỉ là ví dụ; các số fix cứng trong
   `director/prompts.py` hiện tại (hook 1.5–2.5s, thân 3–5s...) là luật cũ autoedit — sẽ GỠ
   khi L2b sâu đọc foundation này, vì fix cứng làm video khô khan.*
2. **Source — tìm hình cho ô thở (CHƯA CÓ — tính năng chính):** sourcer tìm footage đắt theo
   concept: 1 shot (thở cảm xúc) hoặc chuỗi 2–4 shot signature (thở trình chiếu), tiêu chí
   "đứng một mình được". **Kết quả tìm CHỐT độ dài cuối trong [min–max]:** nhiều shot đẹp →
   về phía max; 1 shot khá → phía min; không gì đủ đắt → ô này chết (sang bước 3, không chết
   âm thầm).
3. **SÀN HÌNH THỞ + thang cứu hộ (chống gỡ sạch):** video KHÔNG được về 0 ô thở. Sàn mặc
   định: ≥1 ô/video; tần suất chuẩn hơn lấy từ DNA niche. Khi một ô chết vì thiếu hình, cứu
   theo 3 nấc: (a) nới query / tìm thư viện signature niche; (b) thăng hạng vị trí thở dự
   phòng (danh sách xếp hạng từ bước 1); (c) cả video sắp thủng sàn → GIỮ ô tốt nhất với
   footage đỡ-tệ-nhất + cắm cờ `needs_human` để editor thay hình bằng mắt — thà cắm cờ còn
   hơn video khô không nhịp.
4. **Cut (ỐNG):** chèn `breathing_after` ĐÃ CHỐT vào timeline. **Hệ quả pipeline:** vì số
   chốt SAU source, thứ tự stage phải điều chỉnh (bước chốt thở nằm giữa source và cut, hoặc
   cut chạy lại sau source) — chi tiết trong bản mô tả vận hành của backlog 1, duyệt trước khi code.
5. **Âm thanh trong ô thở:** nhạc nền dâng (ducking ngược) + ambient khớp footage — cơ chế
   thuộc [[e1-sound-design-nhac]], không code ở đây.
6. **Kiểm sau dựng:** pacing validator ([[d1-pacing]] 3b mục 2) kiểm CẢ HAI chiều: lạm dụng
   (nhiều ô liền/quá dày) VÀ thủng sàn (0 ô, hoặc dưới tần suất tối thiểu của niche).

### 3b. PHÂN RÃ NĂNG LỰC — từng câu foundation → tool cần gì

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật (ngôn ngữ editor) | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Thở SAU câu có sức nặng, tại chỗ nghỉ tự nhiên | NÃO đặt breathing_after theo word index tại từ kết mệnh đề | (a)+(c) | ✅ đã có (prompt pass 2 + `Beat.breathing_after`) |
| Chèn khoảng voice-im vào timeline, hình vẫn phủ kín | cutter chèn gap + coverage kéo cửa sổ qua ô thở | (a) | ✅ đã có (`cutter/timeline.py` + `coverage.py`) |
| Thở ngắn hay dài = theo kho footage đắt + sức chịu khán giả (số chỉ là ví dụ, không fix cứng) | quyết định 2 PHA: direct đặt khoảng [min–max] → source chốt số theo hình tìm được thật | (c)+(b)+(d) | ❌ chưa có — thuộc backlog 1; số fix cứng trong prompt cũ sẽ GỠ khi L2b sâu |
| **Video vẫn PHẢI có hình thở — không được gỡ sạch** | sàn ≥1 ô/video (tần suất chuẩn từ DNA) + thang cứu hộ 3 nấc: nới tìm → thăng vị trí dự phòng → giữ ô tốt nhất + cờ needs_human; validator kiểm thủng sàn | (b)+(c) | ❌ chưa có — thiết kế chung backlog 1 |
| **Footage ĐẮT RIÊNG cho ô thở** (không tái dùng hình beat) | NÃO tả concept riêng cho ô thở → sourcer tìm → assembler đổi shot tại mép segment (`is_breathing_tail`) | **(b)** | ❌ **CHƯA CÓ — tính năng code chính của hình thở.** Hiện footage beat cuối bị kéo dài phủ ô thở |
| **1 ô thở = nhiều footage** (chuỗi signature trình chiếu) | mở rộng mục trên: concept ô thở = danh sách 2–4 shot, assembler chia cửa sổ thở | **(b)** | ❌ chưa có — chung tính năng "chia cửa sổ" với thực thi shot_count ([[d1-pacing]] 3b mục 1) |
| Footage phải "đủ đắt đứng một mình", shot nhạt = chết hình | NÃO chấm "độ đắt" (chuyển động, chi tiết, cinematic, signature); Level 2 editor kiểm mắt | (c)+(d) | 🔸 luật định tính + tiêu chí signature từ DNA |
| Ô thở kèm ambient + nhạc dâng | lớp âm thanh của ô thở | — | → [[e1-sound-design-nhac]] (ducking ngược + ambient); ❌ chưa có, ghi backlog bên đó |
| Đừng lạm dụng — gia vị, không phải món chính | luật mật độ trong prompt + pacing validator cảnh báo | (a)+(b) | 🔸 luật prompt ✅; validator ❌ (gộp pacing validator) |
| Số liệu thở của niche (tần suất/độ dài/loại hình) | hồ sơ DNA nạp vào direct | (d) | ❌ Phase B |

**→ Backlog code rút ra (chờ user duyệt mô tả vận hành từng cái trước khi code):**
1. **Hình thở hoàn chỉnh = quyết định 2 pha + footage riêng + sàn/cứu hộ** — direct đặt ý
   định [min–max] → sourcer tìm footage đắt → chốt độ dài → assembler đổi shot tại
   `is_breathing_tail` (cờ có sẵn, chưa ai dùng) → thang cứu hộ khi thiếu hình. Kéo theo
   điều chỉnh thứ tự stage (chốt thở sau source) — điểm cần thiết kế kỹ nhất.
2. **Chuỗi nhiều footage trong 1 ô thở** — làm CHUNG với "chia cửa sổ shot_count" của
   [[d1-pacing]] (cùng một cơ chế assembler chia 1 cửa sổ thành n đoạn — code 1 lần dùng 2 nơi).
3. Cảnh báo mật độ thở + thủng sàn — gộp vào **pacing validator** (không code riêng).

## 4. Cạm bẫy / ranh giới

- **Chết hình:** để ô thở trên shot nhạt → khán giả tưởng lỗi. Không có footage đủ đắt thì
  THÀ KHÔNG THỞ Ô ĐÓ — hạ breathing_after về 0 tốt hơn thở trên hình xoàng. **NHƯNG luật này
  chỉ áp cho TỪNG Ô — không bao giờ được đưa cả video về 0 ô thở** (sàn + thang cứu hộ §3;
  user chốt: "trong một video vẫn phải có hình thở").
- **Lạm dụng:** nhồi nhiều ô thở làm video ì. Gia vị, không phải món chính. Phân vân → ít mà đặt đúng chỗ.
- **Thở giữa mệnh đề:** chèn im lặng giữa cụm từ ("không ngừng | tăng") nghe như lỗi kỹ thuật —
  ranh giới bắt buộc ở từ kết câu/mệnh đề (luật đã cứng trong prompt).
- **Thở sau câu setup/chuyển:** phí nhịp — chỉ thở sau câu ĐÁNG thở.
- **Ô thở câm:** voice im + không ambient + nhạc không dâng = "khoảng chân không", tai nghe
  như lỗi → luôn phối với [[e1-sound-design-nhac]].
- **Ranh giới với [[d1-pacing]]:** pacing quyết video cần chậm Ở ĐÂU; hình thở chỉ là MỘT
  cách chậm (hold shot dài KHÔNG cắt voice vẫn là pacing, không phải hình thở).

## 5. Học gì từ DNA niche (Phase B)

User chốt: *"khi chúng ta học nhiều video, sẽ có số liệu về hình thở của niche."* Nguồn: project
cũ editor (khoảng timeline không voice nhưng có hình) + video viral (transcript có khoảng trống
dài + cảnh vẫn chạy). Tín hiệu cần trích:

| Tín hiệu | Dùng để |
|---|---|
| Tần suất ô thở (số ô / phút thoại) theo niche | tham chiếu cho ý định direct + định SÀN tối thiểu của validator |
| Phân bố độ dài ô thở (min/median/max) theo niche | trả lời câu hỏi "khán giả niche này chịu thở bao lâu" — căn khoảng [min–max] của ý định |
| Ô thở đặt sau LOẠI câu nào (kết luận / mở chủ đề / cảm xúc) | NÃO chọn đúng chỗ theo gu niche |
| Loại footage trong ô thở (signature? toàn cảnh? cận đặc tả?) + 1 hay chuỗi nhiều shot | NÃO tả concept hình cho ô thở |
| Ambient đi kèm loại footage nào | chung với [[e1-sound-design-nhac]] |

Schema tag cảnh (Phase B) phục vụ hình thở: **cảnh có voice hay không + độ dài + mô tả nội
dung/cỡ cảnh** (chung schema với pacing và shot variety — tag 1 lần đủ).
