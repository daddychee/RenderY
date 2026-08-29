# A2 — CHỨC NĂNG ĐOẠN (mỗi chương/beat có một VAI, vai quyết cách đối xử)

> **Vị trí:** tầng nghĩa nằm NGAY TRÊN [[a1-chia-beat-chuong]] — a1 chia ra đơn vị,
> a2 gán VAI cho đơn vị đó. Vai là đầu vào cho gần như mọi quyết định dựng: nhịp thở
> ([[d2-hinh-tho]]), footage đắt để đâu, nhạc đổi lúc nào ([[e1-sound-design-nhac]]),
> chữ ký tiêm chỗ nào ([[c6-footage-chu-ky]]).
> Không có nguyên văn user riêng — chưng cất từ FOUNDATION.md cũ (§6.1–6.2) + code thật.
> **Trạng thái phần 3: DỰ KIẾN 🔸.**

---

## 1. Là gì

Tool KHÔNG viết script — script là input. Nhưng để dựng đúng, NÃO phải **nhận diện mỗi
đoạn đang làm nhiệm vụ gì** trong video, vì cùng một câu chữ mà vai khác → dựng khác:

**Vai cấp CHƯƠNG:**
- **HOOK** (mở đầu, thường chương 1): quyết ~50% retention trong 5–10s đầu. Nhịp đấm —
  footage MẠNH NHẤT không để dành, thở ngắn 1.5–2.5s ngay sau punchline, chữ ký niche
  xuất hiện sớm (khán giả nhận diện "đúng video của mình" trong 3s đầu).
- **THÂN** (mỗi ý lớn một chương): mini-arc setup → phát triển → payoff; nhịp lên xuống
  theo ý; thở thưa (~1 lần/30–60s) đặt sau ý nặng nhất.
- **TRƯỚC CAO TRÀO / CAO TRÀO / KẾT:** chậm lại trước đỉnh (calm before storm), đỉnh dồn
  dập, kết thả lỏng. (Đường sóng này thuộc [[d1-pacing]] — a2 chỉ gán NHÃN đoạn.)

**Vai cấp BEAT (trong chương):**
- **setup / dẫn** — không thở sau nó, không overlay, hình chỉ cần đúng-không-sai;
- **punchline / payoff** — chỗ tiêu tiền: thở, overlay số liệu, footage đắt nhất;
- **chuyển tiếp / chêm** (`visual_anchor=false`) — slot tự do cho footage giữ chân
  ([[c6-footage-chu-ky]] gom signature/ ở đây).

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Vị trí trong video** | Chương 1 = hook gần như mặc định; chương cuối = kết. Vị trí là tín hiệu vai rẻ nhất. |
| **Nội dung câu chữ** | Câu hỏi/nghịch lý/stakes = hook-material; "nhưng đó chưa phải điều điên rồ nhất" = re-hook; câu kết luận = payoff. |
| **Mini-arc trong chương** | Vai beat suy ra từ chỗ đứng trong arc: đầu chương thiên setup, cuối chương thiên payoff. |
| **Niche** | Nhịp hook (bao nhiêu giây, mấy cú đấm), tần suất re-hook — mỗi niche một kiểu → DNA. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

### Hiện trạng: vai đã chạy NGẦM, chưa có nhãn tường minh

Code hôm nay đối xử theo vai ở 3 chỗ, đều suy từ VỊ TRÍ:
1. **Hook = chương đầu tiên** (`hook_id = chapters[0]`): pass 2 nhận cờ `is_hook` → luật
   thở kiểu đấm 1.5–2.5s (prompt); phễu c5 gom `signature/` cho beat hook (luật c6).
2. **Vai beat setup/punchline chạy trong prompt:** luật thở "chỉ sau punchline thật, không
   bao giờ sau câu setup/transition" — NÃO tự nhận diện lúc chia beat, không lưu nhãn.
3. **Chêm** = `visual_anchor=false` (nhãn tường minh duy nhất đang có).

**Hướng dự kiến 🔸: GIỮ NGUYÊN cách này** — vai là thứ NÃO nhận diện lúc direct rồi thể
hiện ngay ra quyết định (thở/overlay/anchor), KHÔNG cần đẻ field `role` mới trong schema
trừ khi L2b sâu cho thấy cần (thêm nhãn = thêm chỗ LLM sai + thêm validator — phình).

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Hook = chương riêng, nhịp đấm, thở ngắn sau punchline | `chapters[0]` + cờ `is_hook` + luật thở HOOK trong prompt pass 2 + `check_breathing_rhythm(hook)` | (a) | ✅ đã có |
| Thân: thở thưa sau ý nặng nhất, mini-arc | prompt pass 1 (mini-arc) + luật thở BODY + `check_chapter_breathing` | (a)+(c) | ✅ đã có |
| Setup/transition không nhận thở/overlay | luật trong prompt pass 2 (NÃO nhận diện vai lúc chia) | (c) | ✅ đang chạy ngầm |
| Beat chêm là slot tự do | `visual_anchor=false` + c6 gom signature | (a) | ✅ đã có |
| Hook nhận footage mạnh nhất, không để dành | NÃO lúc direct (concept đắt cho hook) + phễu c5 xếp signature lên đầu | (c) | 🔸 chạy qua prompt, tinh ở L2b sâu |
| Re-hook mỗi 2–3 phút (video dài) | thuộc SCRIPT (input) — tool chỉ NHẬN DIỆN câu re-hook để đối xử như mini-hook | (c) | 🔸 khi gặp video dài; KHÔNG mở mục code |
| Nhãn `role` tường minh trong schema | CHỈ mở nếu L2b sâu chứng minh cần | (b treo) | ⏸ chủ động KHÔNG làm — tránh phình |
| Nhịp hook/re-hook theo niche | đo từ video viral | (d) | ❌ Phase B |

**→ Backlog code rút ra: KHÔNG có mục mới.** Giá trị a2 = dạy L2b sâu nhận diện vai,
không phải đẻ schema.

## 4. Cạm bẫy / ranh giới

- **Đối xử mọi đoạn như nhau** — lỗi gốc của edit máy móc: setup cũng thở, payoff cũng
  chỉ 1 hình nhạt. Toàn bộ giá trị của a2 là SỰ PHÂN BIỆT ĐỐI XỬ.
- **Để dành footage đắt cho cuối video.** Hook mà nhạt là không còn ai xem tới footage
  đắt. Hook ăn trước.
- **Lấn sân script.** Thấy script thiếu re-hook/open-loop mà tự "dựng bù" bằng hiệu ứng
  → giả trân. Script yếu là việc của người viết; tool dựng đúng những gì script có.
- **Đẻ nhãn vai tường minh quá sớm** — thêm field = thêm chỗ sai + thêm luật đối chiếu
  ([[filter-overload-guard]]). Vai sống trong quyết định (thở/overlay/anchor), không
  cần sống trong schema.

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Cấu trúc hook video viral niche (mấy giây, mấy cú đấm, chữ ký xuất hiện giây thứ mấy) | tinh luật hook trong prompt/L2b |
| Vị trí + cách nhấn payoff (thở? nhạc? chữ?) | phân bổ "chỗ tiêu tiền" theo niche |
| Tỉ lệ beat chêm / beat neo | cân slot tự do cho footage giữ chân |
