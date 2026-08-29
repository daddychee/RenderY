# A1 — CHIA BEAT & CHƯƠNG (đơn vị dựng nhỏ nhất và ý lớn)

> **Vị trí:** kỹ năng NÃO **ĐẦU TIÊN** của cả pipeline — mọi foundation khác đều làm việc
> TRÊN beat/chương mà a1 chia ra. Chia sai ở đây thì pacing ([[d1-pacing]]), hình thở
> ([[d2-hinh-tho]]), chọn footage (phễu [[c5-loc-xep-hang]]) đều hỏng theo.
> Không có nguyên văn user riêng — chưng cất từ FOUNDATION.md cũ (§6.2, Tóm tắt bước 1)
> + code thật đang chạy. **Trạng thái phần 3: DỰ KIẾN 🔸.**

---

## 1. Là gì

Đọc script → chia 2 tầng:
- **Chương** = một Ý LỚN, có mini-arc riêng: *setup → phát triển → payoff*. Video ngắn
  thường 2–6 chương; **hook (những câu đầu) thường là chương riêng**.
- **Beat** = một Ý NHỎ / một mệnh đề — đơn vị dựng nhỏ nhất, thường 2–8 giây thoại
  (~5–20 từ). Mỗi beat nhận đúng 1 quyết định hình ảnh (route, concept, cỡ cảnh…).

Luật vàng: **beat dài NGHỊCH với năng lượng** — đoạn dồn dập chia beat ngắn, đoạn chiêm
nghiệm để beat dài. Ranh giới beat phải rơi vào chỗ NGẮT TỰ NHIÊN của lời nói (hết câu,
hết mệnh đề — từ có dấu câu), không bao giờ cắt đôi một cụm từ.

**Ràng buộc ỐNG sống còn (NT4):** NÃO chỉ trả **word index** (từ thứ mấy đến từ thứ mấy);
mọi timestamp do ỐNG tính từ alignment. Beat/chương phải phủ kín script — không hở,
không đè, không sót từ.

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Năng lượng đoạn** | Cao → beat ngắn (nhiều quyết định hình/phút); thấp → beat dài, một hình đứng lâu. |
| **Dấu câu / nhịp thoại thật** | Ranh giới beat = từ kết thúc câu/mệnh đề; voice đọc thật có chỗ nghỉ ở đâu là tín hiệu mạnh nhất. |
| **Mini-arc của chương** | Câu payoff không được dính chung beat với câu setup — payoff cần beat riêng để được nhấn (thở, overlay…). |
| **Độ dài video & niche** | Video dài → chương nhiều hơn; nhịp beat trung bình mỗi niche khác nhau (facts nhanh, chill travel chậm) → số DNA. |
| **Beat quá vụn** | Beat < ~2s không đủ chỗ cho 1 hình đứng — thà gộp vào beat bên cạnh. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

### Luồng chạy (2 pass — ĐÃ CHẠY hôm nay trong `director/`)

1. **Pass 1 — outline toàn cục:** đọc TOÀN script → chia chương (mini-arc, hook = chương
   riêng), gán mood/energy/music-hint/central_subject mỗi chương, chọn 1–3 motif
   ([[a3-open-loop-callback]]). Chương phủ kín toàn bộ từ [0..n], không hở/đè.
2. **Pass 2 — chia beat TỪNG chương:** trong ngữ cảnh TOÀN VĂN script (cache), chia beat
   phủ kín chương, beat sau chạm beat trước. Mỗi beat quyết luôn route/concept/cỡ cảnh/
   thở/shot_count (các foundation khác cấp luật).
3. **Hậu xử lý bằng máy (không AI):** tính giây từ word index (NT4) → gộp beat quá ngắn
   → bỏ hình thở rơi giữa cụm từ → hàng loạt validator cảnh báo (phủ kín, 3-cùng-cỡ-cảnh,
   nhịp thở, mật độ overlay, ranh giới rơi vào từ nội suy).

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Chia chương mini-arc, hook riêng, phủ kín script | prompt pass 1 (`outline_system`) + `validator.check_coverage` | (a)+(c) | ✅ đã có |
| Beat = 1 mệnh đề 2–8s, dài nghịch energy | prompt pass 2 (`beats_system`) | (a)+(c) | ✅ đã có |
| Ranh giới tại từ có dấu câu, không cắt đôi cụm | prompt (luật breathing boundary) + `enforce_breathing_pauses` + `check_boundary_interpolated` (cảnh báo từ nội suy) | (a) | ✅ đã có |
| Gộp beat quá vụn | `validator.merge_short_beats` (máy, sau LLM) | (a) | ✅ đã có |
| NÃO không sinh timestamp | word index + `compute_beat_times` + Pydantic (NT4) | (a) | ✅ đã có — bất biến, KHÔNG nới |
| Nhịp beat/số chương theo niche | thống kê từ video viral niche → tinh prompt | (d) | ❌ Phase B |
| L2b sâu: Claude Code TỰ chia beat đọc foundation này thay prompt cứng | thay `_pass1/_pass2` prompt bằng phiên đọc foundation | (c) | ❌ Phase C — a1 chính là "ruột" thay prompt |

**→ Backlog code rút ra: KHÔNG có mục mới.** a1 là foundation hiếm hoi mà code ỐNG đã đủ —
giá trị của file này là làm "ruột" cho L2b sâu + chỗ treo số DNA.

## 4. Cạm bẫy / ranh giới

- **Chia beat theo THỜI LƯỢNG thay vì theo Ý.** "Cứ 5s cắt một beat" = nhịp chết. Beat là
  đơn vị NGHĨA; thời lượng chỉ là hệ quả của năng lượng.
- **Ranh giới rơi giữa cụm từ** — bug thật đã gặp (hình thở chèn giữa "nông | thôn"):
  mọi ranh giới có chèn lặng PHẢI ở từ có dấu câu kết thúc mệnh đề.
- **Payoff dính setup.** Câu đắt nhất chương bị nhét chung beat với câu dẫn → mất chỗ nhấn
  (không thở được, overlay chen chúc). Payoff luôn đáng một beat riêng.
- **Tin timestamp của LLM** — cấm tuyệt đối (NT4). Chỉ word index.
- **Beat vụn hàng loạt khi script rời rạc** — merge_short_beats là lưới cuối, nhưng gốc là
  NÃO phải dám để beat dài khi ý kéo dài (một hình đắt giữ 5–6s là bình thường).

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Độ dài beat trung bình + phân bố (theo vị trí: hook/thân/kết) của video viral niche | tinh luật "2–8s" thành số thật per-niche |
| Số chương điển hình theo độ dài video | mồi cho pass 1 |
| Nhịp "payoff được nhấn thế nào" (thở? overlay? đổi nhạc?) | nối sang [[d2-hinh-tho]], [[b3-pattern-interrupt]] |
