# C6 — FOOTAGE CHỮ KÝ NICHE (footage đối thủ dùng nhiều = khán giả thích = YouTube index)

> **Vị trí:** file CUỐI nhóm C. **Định nghĩa (lời user 2026-07-03):** chữ ký niche = loại
> footage mà **các video đối thủ sử dụng nhiều** → chứng tỏ khán giả niche thích xem →
> **YouTube index làm siêu dữ liệu niche**. Học từ dữ liệu, không tự nghĩ ra.
> **Cơ chế: ĐƠN GIẢN TỐI ĐA (user yêu cầu) — đúng 1 luật, KHÔNG chấm điểm, KHÔNG lọc.**
> Phân làn: [[c1-phan-tuyen-nguon]] = nguồn; [[c3-ngu-canh-chuoi]] = motif trong 1 video;
> c6 = footage chuẩn niche học từ đối thủ. **Trạng thái phần 3: DỰ KIẾN 🔸.**

---

## 1. Là gì

Chữ ký niche = loại footage đặc trưng của niche, học từ video đối thủ / video viral —
khán giả niche thích xem, YouTube index làm siêu dữ liệu niche.

**Nguồn dữ liệu (đúng logic đã bàn ở [[footage-source-local-first]]):** project CapCut của
editor thật (thường là **10 phút đầu** video) + **video viral tải về, đưa vào project CapCut
để tách cảnh** → chính là ~100 project nguồn của kho local. Phase B tách cảnh → vision tag
→ đếm: loại lặp nhiều nhất xuyên đối thủ = chữ ký → điền thư mục `library/<niche>/signature/`.

**Hệ quả:** kho local được XÂY từ chính nguồn đối thủ/viral → **vốn đã nghiêng về chữ ký
từ gốc**. Route local-first (c1) tự mang chữ ký vào video. c6 chỉ cần thêm đúng 1 luật nhỏ
ở 2 vị trí (dưới đây) — không cần cơ chế gì cầu kỳ hơn.

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Vị trí beat** | Chỉ 2 chỗ chữ ký có tiếng nói: **HOOK** (mấy beat đầu — dữ liệu "10 phút đầu" của đối thủ nghiêng hẳn về đây) và **SLOT CHÊM** (`visual_anchor=false` — nghĩa lỏng, prompt đã dặn rót "audience-retention footage"). Mọi beat khác: nghĩa/mood/nhịp dẫn như thường, chữ ký không tham gia. |
| **Kho `signature/` có gì** | Có hàng hợp nghĩa → dùng; rỗng/không hợp → bỏ qua êm, không ép, không loại footage khác. |
| **Niche** | Mỗi niche một bộ chữ ký rút từ dữ liệu đối thủ của niche đó, không dùng chéo. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

**Đúng 1 luật:**

> Khi gom ứng viên cho beat **HOOK** hoặc beat **SLOT CHÊM**: lấy từ `signature/` **trước**,
> nếu có hàng hợp nghĩa thì dùng; không có thì gom bình thường như mọi beat khác. Hết.

- Không có "điểm chữ ký", không cộng trừ, không bước chấm riêng — chữ ký chỉ là **thứ tự
  ưu tiên nguồn** tại 2 vị trí đó (giống `signature/` vốn đã luôn qua geo-gate trong
  `local.py` — cùng tinh thần: ưu ái nhẹ, không cưỡng chế).
- Veto nghĩa (c2) vẫn áp bình thường: shot chữ ký sai nghĩa vẫn chết veto.
- Tần suất "đối thủ dùng nhiều" chỉ dùng **OFFLINE Phase B** để biết cái gì bỏ vào
  `signature/` — KHÔNG phải luật runtime "lặp nhiều = chọn nhiều".

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Thư mục `signature/` | scaffold `library/profile.py` tạo sẵn; luôn qua geo-gate (`local.py`) | (a) | ✅ có sẵn |
| Ý định rót vào slot chêm | prompt: `visual_anchor=false` → "audience-retention footage" | (a) | ✅ có trong prompt |
| **Hook + slot chêm gom `signature/` trước** | vài dòng trong bước gom ứng viên local: nếu beat là hook/chêm → query thêm folder `signature/` lên đầu danh sách | **(b)** | ❌ code mới NHỎ, gắn khung phễu c5, KHÔNG mục mới |
| Bộ chữ ký thật | Phase B: tách cảnh ~100 project + viral → tag → đếm → điền `signature/` | (d) | ❌ Phase B — trước đó luật chạy "no-op êm" |

## 4. Cạm bẫy / ranh giới

- **Biến chữ ký thành bộ lọc.** Không có cửa loại "thiếu chữ ký" — footage không chữ ký
  vẫn cạnh tranh bình thường ([[filter-overload-guard]]).
- **Ưu tiên chữ ký tràn lan.** Chữ ký chỉ có tiếng nói ở hook + slot chêm; thân bài, beat
  neo → không tham gia. Đừng suy "đối thủ dùng nhiều = mình chọn càng nhiều càng tốt".
- **Tự nghĩ ra chữ ký thay vì rút từ dữ liệu.** Chưa có Phase B → `signature/` rỗng → luật
  no-op. Đừng bịa danh sách "chắc niche này thích X".
- **Ép khi kho rỗng.** "Ưu tiên nếu có" ≠ "bắt buộc phải có". Rỗng → bỏ qua êm.

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Loại footage lặp nhiều nhất xuyên ~100 project đối thủ (10 phút đầu) + video viral | điền `library/<niche>/signature/` — nền của cả luật |
| Hook đối thủ mở bằng loại shot nào | biết `signature/` nên chứa gì cho hook |
