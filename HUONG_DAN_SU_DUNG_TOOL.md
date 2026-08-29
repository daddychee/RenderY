# HƯỚNG DẪN SỬ DỤNG TOOL — DỰNG 1 VIDEO (dành cho Editor)

> **Đưa file này cho editor.** Không cần biết code, không cần gõ lệnh dòng lệnh —
> mọi việc làm qua **trò chuyện với Claude Code**. Editor chỉ cần: đưa folder, đọc
> tóm tắt beat, góp ý, rồi mở CapCut kiểm.
>
> Tài liệu anh em (khi cần): `HUONG_DAN_CAI_DAT_MAY_EDITOR.md` (cài máy lần đầu) ·
> `HUONG_DAN_NAP_NICHE_MOI.md` + `HUONG_DAN_EDITOR_GOM_SFX_NHAC.md` (việc của máy gốc,
> editor không cần đụng) · `HUONG_DAN_COPY_MAY_GOC.md` (đồng bộ máy).

---

## 0. Tool này làm gì

Nhận **script (tiếng Anh) + voice đã lồng tiếng (mp3)** của 1 video → tool tự chia
nhịp/beat, tự đạo diễn hình ảnh, tự tải/cắt footage, tự ghép nhạc nền + SFX + chữ overlay
→ ra một **draft CapCut gần hoàn chỉnh**. Editor chỉ cần tinh chỉnh ~20% cuối rồi xuất video.

Toàn bộ quá trình có **2 cổng editor phải tự mắt xem xét**, tool không tự ý bỏ qua:
1. **Cổng duyệt beat** (trước khi tải footage — sửa rẻ, sửa ý)
2. **Cổng xem CapCut** (sau khi dựng xong — sửa tốn, kiểm bằng mắt/tai)

---

## 1. Chuẩn bị folder cho 1 video

Tạo 1 folder (tên tuỳ ý, vd `SP1-020`), bỏ vào đó:

| File | Bắt buộc | Ghi chú |
|---|---|---|
| Script `.txt` (hoặc `.rtf`/`.md`) | ✅ | Tiếng Anh, script đã lồng tiếng |
| Voice `.mp3` (hoặc `.wav`/`.m4a`) | ✅ | File giọng đọc ElevenLabs |
| Folder **video mẫu** (nếu có) | Tuỳ chọn | Video công ty/đối thủ dùng làm tham khảo hình ảnh — xem mục 4.1 |

Không cần đặt tên file đặc biệt (`script.txt`/`voice.mp3`) — chỉ cần đúng đuôi file, tool tự nhận diện.

---

## 2. Bắt đầu 1 phiên dựng video

1. Mở **Claude Code** trên máy, vào đúng folder project của tool (`tool edit padoma`).
2. Gõ `/dung-video` (hoặc chỉ cần nói "dựng video giúp tôi") rồi đưa:
   - **Đường dẫn folder** vừa chuẩn bị ở bước 1.
   - **Brief tự do** (không bắt buộc): niche/kênh, tông giọng, muốn nhấn mạnh gì.
     Vd: *"niche retirement-abroad, tông ấm áp hoài niệm, nhấn mạnh con số $1,200/tháng"*.

> Ví dụ gõ: *"Dựng video từ folder `F:\SCRIPTS\SP1-020`, kênh retirement-abroad, tông ấm áp."*

Claude Code sẽ tự lo hết phần kỹ thuật (tạo project, canh timestamp, đạo diễn beat...).
Editor không cần gõ lệnh `uv run autoedit ...` — đó là việc Claude Code tự chạy ngầm.

---

## 3. PHA 1 — Duyệt beat (cổng rẻ, sửa Ý trước khi tốn footage)

Sau vài phút, Claude Code trả về **bản tóm tắt**: số chương, tổng số beat, và với mỗi beat —
câu thoại ngắn, hình dự kiến, cỡ cảnh, có card/biểu đồ hay không, kèm cảnh báo (nếu có).

**Việc của editor:** đọc tóm tắt, rồi trả lời 1 trong 2:
- **"Duyệt"** → Claude Code chuyển sang PHA 2 (dựng draft, tốn thời gian + tải footage thật).
- **Góp ý cụ thể** → vd *"beat 7 sai chủ thể, hook cần thêm punch"*, *"chương 3 nhịp nhanh
  quá"*. Claude Code sửa đúng chỗ đó, dựng lại, gửi lại **phần khác biệt** (không dựng lại
  từ đầu). Lặp tới khi editor ưng — sửa lúc này gần như miễn phí (chưa tải footage).

⚠ **Claude Code sẽ KHÔNG tự chuyển sang PHA 2** nếu editor chưa nói "duyệt" — đây là quy tắc
cứng của tool, không phải Claude Code quên hỏi.

### 3.1. Muốn khai thêm sở thích khán giả (tuỳ chọn)
Biết khán giả kênh thích loại cảnh nào (vd "khán giả thích cảnh phụ nữ đẹp", "thích nhiều
cảnh động vật") → nói ngay ở bước này, càng sớm càng "ăn" trọn (đạo diễn viết ý beat có tính
tới cảnh đó, không chỉ chọn footage lúc sau). Xem chi tiết `MO_TA_VAN_HANH_BOOST.md`.

---

## 4. PHA 2 — Dựng draft CapCut (chậm, tải footage thật)

Chỉ chạy sau khi editor gõ "duyệt". Claude Code sẽ: cắt voice theo beat → tải/chọn footage
→ ghép nhạc nền + SFX + chữ overlay → sinh draft CapCut → sinh `report.html`.

Xong, Claude Code báo cho editor **2 thứ**:
- **Đường dẫn draft** — mở CapCut lên, draft mới sẽ xuất hiện trong danh sách.
- **`report.html`** — mở bằng trình duyệt, đọc mục 5 bên dưới.

**Việc của editor:** mở CapCut, xem draft — preview KHÔNG được đen, click vào footage KHÔNG
được đòi relink. Nếu đúng vậy → chuyển sang tinh chỉnh 20% cuối. Nếu sai → xem mục 6 (Sự cố).

### 4.1. Có video mẫu (tham khảo hình ảnh) thì sao?
Nếu folder đưa cho Claude Code có kèm **folder video mẫu** (video công ty/đối thủ, có draft
CapCut đã tách cảnh đi kèm) — Claude Code sẽ **tự nạp** các cảnh đó vào kho TRƯỚC khi đạo
diễn (không cần editor nhắc). Cảnh từ video mẫu sẽ được ưu tiên chèn vào bài đang dựng.
Nếu video mẫu chia theo `Chapter 1`, `Chapter 2`... thì cảnh trong đó chỉ ưu tiên đúng
chương tương ứng. Chi tiết: `MO_TA_VAN_HANH_REF.md`.

### 4.2. Ghi công kênh nguồn (tuỳ chọn)
Muốn mỗi miếng footage hiện tên kênh nguồn ở góc màn hình → nói *"bật ghi công kênh"* trước
khi dựng PHA 2. Chỉ hiện được với footage đã có tên kênh trong kho.

### 4.3. Tiếng động nền (SFX) — 2 công tắc mặc định TẮT
Tool có 2 tuỳ chọn SFX nâng cao **mặc định KHÔNG bật** (chủ động nói mới bật):
- Tiếng từ thư viện Epidemic Sound.
- AI chấm tiếng cho cảnh mà bảng luật thường không nhận ra tiếng gì.

Cách dùng đúng: **xem draft dựng xong trước**, nếu report/nghe thử thấy nhiều đoạn im tiếng
nền thì mới nói *"bật AI chấm tiếng rồi dựng lại"* — dựng lại đoạn ghép nhạc/SFX nhanh, không
phải tải lại footage từ đầu.

### 4.4. Đoạn chèn thêm giữa video (⚠ tính năng đang thử nghiệm)
Tool hỗ trợ chèn 1 đoạn ngắn (nhạc + hình riêng, không theo giọng đọc) vào giữa 2 beat hoặc
cuối 1 chương — cần nói rõ chèn ở đâu, dài bao lâu, muốn dùng nhạc/hình riêng gì. Tính năng
này còn đang hoàn thiện, dùng thử nói với Claude Code, đừng tự ý nếu chưa quen.

---

## 5. Đọc `report.html` — checklist việc tay 20% cuối

Report liệt kê theo thứ tự ưu tiên:

- **🔴 CẦN XỬ LÝ** — mục bắt buộc phải xem: beat thiếu footage (tool chưa tìm được cảnh
  phù hợp, editor tự đắp), footage cần kiểm bản quyền (ảnh thực thể/tin tức).
- **Chi tiết theo từng beat** — nguồn mỗi cảnh, cỡ cảnh, lý do chọn.
- **Nhạc nền theo chương**, **tiếng nền các ô thở**, **cảnh báo khác** (nếu có).

Không có mục 🔴 nào → coi như tool đã làm xong phần của mình, chuyển sang tinh chỉnh thẩm mỹ
trong CapCut như bình thường.

---

## 6. Sự cố thường gặp

| Hiện tượng | Việc của editor |
|---|---|
| Draft không thấy trong CapCut | Kiểm CapCut → Settings → Draft location có đúng trỏ tới folder xuất draft của tool không (thường `E:\CapCut Drafts`) |
| Preview đen / click footage bắt relink | **KHÔNG tự sửa, KHÔNG đè/xoá draft** — báo ngay cho máy gốc kèm tên draft, đây là lỗi kỹ thuật cần soi tay |
| Copy draft sang máy khác không mở được | Copy **nguyên cả folder** draft (không tách lẻ file), và **không đặt trùng tên** với draft đã có sẵn trên máy CapCut đích |
| Chạy giữa chừng bị ngắt (mất mạng, tắt máy) | Không sao — nói lại với Claude Code y hệt folder cũ, tool tự chạy tiếp từ bước đang dang dở, không mất phần đã xong |
| Muốn dựng lại beat 1 lần nữa dù đã duyệt | Cứ nói với Claude Code muốn sửa gì — không đè bản cũ, mỗi lần dựng ra draft **tên mới** |

---

## 7. Việc KHÔNG phải của editor

Những việc sau do **máy gốc** làm (editor không cần và không nên tự chạy):
- Mở niche/kênh mới trong kho (`HUONG_DAN_NAP_NICHE_MOI.md`).
- Gom nhạc nền/SFX nạp kho (`HUONG_DAN_EDITOR_GOM_SFX_NHAC.md` — phần LỌC FILE + ĐẶT TÊN
  vẫn có thể là việc editor, nhưng NẠP vào tool là máy gốc).
- Cài đặt lại máy, đồng bộ bản mới (`HUONG_DAN_CAI_DAT_MAY_EDITOR.md`, `HUONG_DAN_COPY_MAY_GOC.md`).

Nếu Claude Code báo lỗi thuộc nhóm này (vd "thiếu machine profile", "chưa đăng ký máy với
CapCut") → báo máy gốc, đừng tự đoán sửa.
