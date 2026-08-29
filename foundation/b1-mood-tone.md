# B1 — MOOD & TONE

> **Vị trí:** nhóm B (định hướng cảm xúc) — foundation "kim chỉ nam" mà mọi tầng khác phải
> chạm vào. Đẻ ra **veto C2b (sai mood)** trong [[c2-an-du-veto]], thực thi qua trọng tài phễu
> [[c5-loc-xep-hang]]. Liên quan: [[e1-sound-design-nhac]] (nhạc = 60% cảm xúc) ·
> [[d1-pacing]] (nhanh/chậm là 1 tầng của mood) · [[c7-shot-variety]].
> **Trạng thái phần 3: DỰ KIẾN 🔸 — user duyệt mô tả vận hành rồi mới code phần thiếu.**
> Nguyên văn lời user: `GHI_CHEP_GOC.md §4`.

---

## 1. Là gì

- **Tone** = thái độ/giọng điệu tổng thể của video (nghiêm túc, hài hước, hoài niệm, năng
  lượng, gai góc...). **Hằng số của cả video** — đổi giữa chừng = lạc giọng.
- **Mood** = cảm xúc người xem cảm thấy tại TỪNG ĐOẠN. **Biến thiên theo mạch**, và được phép
  đổi **có chủ đích** (đang buồn → chuyển hy vọng ở cuối).

Mood/tone không nằm ở một thứ — nó là **cộng hưởng của 5 tầng**:

| Tầng | Vai trò |
|---|---|
| 1. Nhạc & sound design | quyết định **60% cảm xúc** — đổi nhạc = đổi mood ngay cả khi hình không đổi |
| 2. Màu (color grade) | ấm/lạnh, tương phản cao/thấp, độ bão hòa |
| 3. Pacing | nhanh = phấn khích/căng; chậm = trầm/hoài niệm |
| 4. Voice | cách ngắt nghỉ, năng lượng giọng — *ở tool này là DỮ KIỆN đầu vào (voice có sẵn), không phải biến điều khiển: mood phải đọc THEO voice* |
| 5. Chọn footage | góc máy, ánh sáng, chuyển động camera trong shot |

Ví dụ neo (quyền lực của editor): cùng một footage đi bộ trong mưa — lo-fi + màu ấm phai +
chậm = **hoài niệm, bình yên**; nhạc dồn + màu lạnh tương phản cao + cắt nhanh = **cô đơn,
ngột ngạt**. Hình y hệt, cảm xúc trái ngược.

## 2. Yếu tố ảnh hưởng

| Yếu tố | Tác động |
|---|---|
| **Từ khóa tone của đoạn** | cơ chế trung tâm: chốt 1 từ khóa (vd "ấm áp – hoài niệm") TRƯỚC khi dựng đoạn; mọi lựa chọn nhạc/màu/nhịp/transition/footage phải "chạm" từ khóa đó |
| **Tone cả bài** | trần của mood đoạn: mood biến thiên nhưng KHÔNG lệch tone bài |
| **Voice có sẵn** | giọng đọc là dữ kiện — mood đoạn phải khớp năng lượng giọng, không cãi lại |
| **Niche** | mỗi niche có tone baseline riêng (tài chính: tối giản, sang; du lịch: tươi sáng colorful) — tham khảo DNA để quyết nhanh |
| **Mạch content** | nội dung đoạn quyết mood đoạn (buồn/hy vọng/căng) — mood đổi theo mạch, có chủ đích |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN, chờ user duyệt

### Ai quyết cái gì

- **NÃO quyết toàn bộ phần nghĩa:** tone video (1 từ khóa, chốt trước khi dựng) · mood mỗi
  chương/beat · kiểm "mood đoạn có lệch tone bài không". Mood/tone là ngữ nghĩa thuần — ỐNG
  không quyết gì, chỉ thực thi hệ quả (chọn track nhạc theo tag, chấm điểm footage).
- **Hiện trạng dữ liệu:** `Beat.mood` + outline chương (mood/energy/music hint) đã có;
  **CHƯA có field tone cấp video** — brief đang gánh tạm.

### Luồng chạy dự kiến (end-to-end)

1. **Chốt TONE VIDEO trước khi dựng:** NÃO đọc brief + tone baseline của niche (DNA, khi có)
   → ghi 1 từ khóa tone vào project.json (field mới, code nhỏ). Đây là "hiến pháp cảm xúc"
   của video.
2. **Direct pass 1:** gán mood + energy + music hint cho từng chương (đã chạy hôm nay). Thêm
   luật khi L2b sâu: mỗi mood chương phải tự kiểm "có chạm tone video không" — lệch thì hoặc
   đổi mood, hoặc báo editor (mood đổi CÓ CHỦ ĐÍCH thì được, đổi vì quên thì không).
3. **Mood chảy xuống từng tầng:**
   - **Nhạc (✅ đã có):** chọn track theo tag mood/energy từ thư viện (`music/select.py`,
     tag trong tên file `__mood`), nhạc đổi tại ranh giới chương.
   - **Pacing (✅ liên kết sẵn):** energy chương/beat điều khiển độ dài beat ([[d1-pacing]]).
   - **Footage — chấm mood ứng viên (❌ tính năng chính):** xem mục C2b dưới.
   - **Màu (⏸ không grade chủ động):** tool KHÔNG color-grade; đường duy nhất là CHỌN footage
     sẵn màu hợp mood (qua C2b). Grade tay = việc editor ở 20% cuối.
   - **Voice:** đọc theo, không điều khiển.
4. **C2b — chấm mood footage khi lọc:** footage đúng nghĩa nhưng sai màu/tông/năng lượng so
   với mood đoạn → **trừ điểm RẤT nặng** (theo 4 nguyên tắc phễu [[c5-loc-xep-hang]]: không
   veto tuyệt đối để tránh rỗng pool; pool đủ thì footage lệch mood không bao giờ thắng).
   Muốn chấm được phải "NHÌN" footage — 2 lớp, rẻ trước đắt sau:
   - **Lớp rẻ (code thuần, không LLM): so màu NỘI BỘ đoạn** — trích màu chủ đạo/độ sáng/độ
     bão hòa mỗi ứng viên (ffmpeg/histogram) rồi so với các footage ĐÃ CHỌN của cùng chương
     → bắt đúng 2 lỗi ví dụ của user (1 clip sáng lọt đoạn u ám; 1 clip vintage lọt đoạn
     colorful) mà không cần hiểu nghĩa, vì bản chất lỗi là LỆCH TƯƠNG ĐỐI so với xung quanh.
   - **Lớp đắt (vision GLM-4V, luật §5 CLAUDE.md):** xem frame ứng viên, chấm "chạm từ khóa
     tone không" — CHỈ chạy cho beat mood-nhạy-cảm (mood mạnh: buồn sâu, cao trào cảm xúc)
     để tiết kiệm call; không quét đại trà.
5. **Kiểm sau dựng:** report liệt kê bảng chương → mood → nhạc đã chọn → footage bị trừ điểm
   mood (kill-count của phễu) — editor liếc là thấy đoạn nào lệch.

### 3b. PHÂN RÃ NĂNG LỰC — từng câu foundation → tool cần gì

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật (ngôn ngữ editor) | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Chốt 1 từ khóa tone trước khi dựng, làm kim chỉ nam | field tone cấp video trong project.json + NÃO chốt từ brief/DNA | (b)+(c) | ❌ field chưa có — code nhỏ; brief gánh tạm |
| Mood từng chương, nhạc đổi theo chương, mọi yếu tố cùng kéo 1 mood | direct pass 1 (mood/energy/music hint) + thư viện nhạc lọc tag mood/energy | (a) | ✅ đã có (prompt pass 1 + `music/select.py`) |
| Mood đoạn không lệch tone bài; đổi mood phải có chủ đích | NÃO tự kiểm khi gán mood + ghi lý do đổi mood vào project.json | (c) | 🔸 chưa có luật tường minh — thêm khi L2b sâu |
| **C2b: footage đúng nghĩa nhưng sai màu/tông → gần như không được chọn** | trừ điểm rất nặng trong phễu [[c5-loc-xep-hang]] (không veto tuyệt đối) | (b)+(c) | ❌ chưa có — chờ chốt 4 nguyên tắc phễu |
| 1 footage lệch màu giữa đoạn = sai mood (2 ví dụ của user) | **so màu nội bộ đoạn** bằng histogram/ffmpeg giữa các footage cùng chương — code thuần, rẻ, không LLM | (b) | ❌ chưa có — **đáng làm sớm nhất** vì rẻ mà bắt đúng lỗi user nêu |
| Footage phải "chạm" từ khóa tone (góc máy/ánh sáng/chuyển động) | vision GLM-4V chấm frame ứng viên — CHỈ beat mood-nhạy-cảm (tiết kiệm call) | (b)+(d) | ❌ chưa có — cần thiết kế chi phí; đại trà thì đợi tag DNA Phase B |
| Màu (color grade) chủ động | KHÔNG làm — tool chỉ chọn footage sẵn màu hợp; grade = editor 20% cuối | — | ⏸ non-goal (chốt để khỏi phình scope) |
| Nhạc phục vụ tone, không phải "bài mình thích" | thư viện nhạc có tag mood + NÃO chọn theo từ khóa tone | (a)+(c) | ✅ cơ chế có; chất lượng chọn tinh ở Level 2 |
| Tone baseline của niche | hồ sơ DNA: từ khóa tone + bảng màu chủ đạo của niche | (d) | ❌ Phase B |

**→ Backlog code rút ra (chờ user duyệt mô tả vận hành từng cái trước khi code):**
1. **Field tone cấp video** + luật NÃO kiểm mood-không-lệch-tone (code nhỏ + prompt/foundation).
2. **So màu nội bộ đoạn** (histogram màu chủ đạo giữa footage cùng chương, cảnh báo/trừ điểm
   footage lệch) — code thuần rẻ, độc lập, làm sớm được.
3. **Chấm mood bằng vision GLM** cho beat mood-nhạy-cảm — thiết kế sau khi có phễu c5 + cân chi phí.

## 4. Cạm bẫy / ranh giới

- **Lệch tone = lỗi chết người:** video tâm sự sâu lắng + hiệu ứng meme/nhạc EDM = giả trân.
  Tone nhất quán là bất khả xâm phạm; chỉ MOOD được đổi, và phải có chủ đích.
- **1 footage lệch màu giết cả đoạn** — lỗi không nằm ở footage đó "xấu" mà ở nó LỆCH so với
  xung quanh; kiểm tương đối, không kiểm tuyệt đối.
- **Nhạc theo gu cá nhân** thay vì theo tone — nhạc là tầng mạnh nhất (60%), chọn sai là đổ cả đoạn.
- **Nhầm tone với mood:** tone không được đổi; thấy "cần đổi tone giữa video" nghĩa là đã chia
  chương sai hoặc script có vấn đề — báo editor, đừng lặng lẽ đổi.
- **Đừng grade màu hộ editor** — ranh giới scope: tool chọn hình đúng màu, không sửa màu hình.
- **Ranh giới với [[e1-sound-design-nhac]]:** file này quyết TỪ KHÓA cảm xúc; chọn track/ambient
  /SFX cụ thể thế nào là việc của sound design.

## 5. Học gì từ DNA niche (Phase B)

User chốt: *"tham khảo dna niche để hiểu về tone của niche, dễ quyết định cho video."* Nguồn:
video viral đối thủ + project cũ editor. Tín hiệu cần trích:

| Tín hiệu | Dùng để |
|---|---|
| Từ khóa tone phổ biến của niche (vd du lịch chill: "tươi sáng – thư thái") | NÃO chốt tone video nhanh, khỏi mò |
| Bảng màu chủ đạo theo niche + theo vị trí video (mở đầu tươi sáng...) | chuẩn so màu cho C2b + lớp rẻ histogram |
| Mood arc phổ biến (mở thế nào, chuyển mood ở đâu, kết thế nào) | direct pass 1 gán mood chương đúng gu niche |
| Genre/mood nhạc hay dùng theo niche + theo đoạn | chung với [[e1-sound-design-nhac]] |
| Loại footage (ánh sáng/chuyển động/góc) đi với mood nào | tiêu chí chấm mood footage |

Schema tag cảnh (Phase B) phục vụ mood&tone: **màu chủ đạo + độ sáng + độ bão hòa + mood ước
lượng của cảnh** (cùng lượt tag với độ dài cảnh/cỡ cảnh/góc — tag 1 lần đủ cho pacing +
shot variety + mood).
