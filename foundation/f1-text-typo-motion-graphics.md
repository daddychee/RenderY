# F1 — TEXT, TYPOGRAPHY & MOTION GRAPHICS (chữ trên màn — lớp nghĩa 2–3)

> **Vị trí:** foundation TRÙM nhóm F (nuốt F1 caption/text nhấn + F3 motion graphic cũ).
> Chữ vừa truyền thông tin vừa là nhịp ([[b3-pattern-interrupt]]) và tone ([[b1-mood-tone]]).
> Nguyên văn user: `GHI_CHEP_GOC.md §7`. **Trạng thái phần 3: DỰ KIẾN 🔸.
> Điểm treo: lớp nghĩa 2–3 cần SỐ LIỆU THẬT (web-grounded) — phụ thuộc `enrich --web`
> qua Claude Code chưa giải (NHAT_KY §B1).**

---

## 1. Là gì

Chữ trên màn hình — từ text nhấn, số liệu, tới kinetic typography. Luật nền (nguyên văn §7):

> Chọn 1–2 font nhất quán cả video. Chữ xuất hiện phải có animation nhẹ — chữ "bụp" hiện
> thô rất kém sang. Timing chữ khớp voice: hiện đúng lúc nói tới từ đó. Với số liệu/từ
> khóa quan trọng → nhấn bằng chữ để "ghim".

Và cái user nhấn mạnh nhất — **LỚP NGHĨA THỨ 2, THỨ 3** (chữ KHÔNG lặp lại voice mà
BỔ NGHĨA cho voice):

> voice nói: "trung bình một người trưởng thành chi tiêu một tháng hết $1000" → màn hình
> hiện: **hồng kông $2000 - singapore $2500**. voice nói: "chi phí thực phẩm ở việt nam
> rất dễ chịu" → màn hình: **ăn sáng (phở) $2, cà phê $1.5**.

Lớp 1 = chữ ghim lại điều voice VỪA nói ($1000 nảy lên). Lớp 2–3 = dữ kiện MỚI đặt cạnh
để so sánh/cụ thể hóa — khán giả nhận thêm thông tin mà voice không phải đọc ra. Đây là
thứ phân biệt video "có chữ" với video "chữ có nghĩa".

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Nội dung beat** | Có con số/từ khóa/danh sách đáng ghim không — đa số beat KHÔNG có chữ (tiết chế là luật). |
| **Timing voice** | Chữ hiện ĐÚNG từ đang nói (anchor theo word index — NT4); sớm = spoil, muộn = lạc. |
| **Nguồn số liệu (lớp 2–3)** | Dữ kiện mới phải THẬT và kiểm được — chữ sai số liệu là lỗi chí mạng ngang footage sai nghĩa (bất đối xứng c2 áp cho cả chữ). |
| **Tone video** | Font/anim/màu phải cùng tone; typewriter hợp tên người/địa danh, pop hợp giá tiền — mỗi KIND một bộ mặt. |
| **Nền đang chiếu** | Chữ phải đọc được: tương phản, không che chủ thể; nền loạn cần plate mờ (kinetic đã có). |
| **Niche (DNA)** | Mật độ chữ, kiểu font, kind ưa dùng — facts dày chữ, chill thưa. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

### Hiện trạng code — lớp 1 (ghim voice) đã chạy KHÁ ĐỦ; lớp 2–3 là khoảng trống

- **Overlay text nhấn:** 7 kind (price/keyword/stat/list_item/name/place/quote) — NÃO chỉ
  quyết NGHĨA (text + kind + anchor_word); code map phần HÌNH (`overlay/style.py`:
  position/anim/SFX/size — typewriter+keyboard cho name/place/quote, pop+impact cho
  keyword…). Timing = anchor_word khớp voice (NT4).
- **Kinetic typography:** `TextSequence` — chẻ câu thành 2–4 cụm hiện theo voice, plate
  mờ khi nền loạn; rất tiết chế (vài lần/video).
- **Thẻ chữ nửa màn:** `InfoCard` (bullet định tính) + **chart động** (`GraphicSpec`
  bar/line/pie, layout full/half) — đây chính là "motion graphics" F3 cũ.
- **Tiết chế bằng máy:** `check_overlay_density` (~1/8–12s nói), `check_graphic_ratio`
  (≤1 chart/60s), trần 2 card + 2 chart/chương (`enforce_chapter_visual_limits`).
- **Lớp nghĩa 2–3 đã có ĐƯỜNG ỐNG nhưng chưa có NGUỒN:** `enrich` sinh chart/info-card
  BỔ SUNG (data_origin=supplementary, BẮT BUỘC duyệt `enrich-approve` mới render) —
  nhưng web-grounded qua Claude Code chưa chạy (§B1) nên số liệu so-sánh-ngoài-script
  chưa lấy được tự động.

### Hướng dự kiến 🔸

1. **Lớp 1 giữ nguyên** — đủ dùng, kỷ luật density đúng.
2. **Lớp 2–3 = việc của L2b sâu, KHÔNG phải mục code mới:** khi NÃO là Claude Code phiên
   sống (có WebSearch), nó tự tra "chi phí Hồng Kông/Singapore" lúc direct → đổ vào đường
   ống enrich CÓ SẴN (supplementary + cổng duyệt). Điểm treo §B1 tự giải ở Phase C.
   Nguyên tắc sắt: **số liệu lớp 2–3 không có nguồn → KHÔNG hiện** — thà thiếu chữ còn
   hơn chữ bịa; mọi supplementary đều qua duyệt như hiện tại.
3. **Font/style nhất quán theo kênh:** hiện style cứng theo kind — bảng font/màu per-kênh
   (niche_profile) để sau, khi DNA cho biết gu.

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Chữ ghim từ khóa/số, hiện đúng lúc nói | Overlay 7 kind + anchor_word + style map | (a)+(c) | ✅ đã có |
| Chữ có anim nhẹ, không "bụp" | style map (pop/slide/typing) — code lo HÌNH | (a) | ✅ đã có |
| Kinetic theo voice, plate khi nền loạn | `TextSequence` | (a) | ✅ đã có |
| Danh sách/so sánh trực quan | InfoCard + GraphicSpec chart (full/half) | (a) | ✅ đã có |
| Tiết chế — đa số beat không chữ | density/ratio/chapter-limit validators | (a) | ✅ đã có |
| **Lớp nghĩa 2–3 (dữ kiện so sánh THẬT)** | đường ống enrich supplementary + cổng duyệt ĐÃ CÓ; nguồn số liệu = L2b sâu (Claude Code + WebSearch) | (c) qua ống (a) | 🔸 Phase C — KHÔNG mở mục code; điểm treo §B1 tự giải |
| Chữ sai số liệu = veto | quy tắc vận hành: supplementary luôn qua duyệt; không nguồn → không hiện | (c) | 🔸 luật cho L2b, ghi tại đây |
| Font/màu nhất quán theo kênh/niche | bảng style per-kênh trong niche_profile | (b nhỏ treo)+(d) | ⏸ chờ DNA cho gu font |
| Mật độ chữ theo niche | số DNA → chỉnh ngưỡng density | (d) | ❌ Phase B |

**→ Backlog code rút ra: KHÔNG mở mục mới.** Khoảng trống duy nhất (lớp 2–3) đi qua
đường ống enrich sẵn có khi L2b sâu; f1 ghi luật để lúc đó không bịa số.

## 4. Cạm bẫy / ranh giới

- **Chữ bịa số liệu** — lỗi chí mạng số 1 của lớp 2–3: "hồng kông $2000" mà sai thì tệ
  hơn không có chữ. Không nguồn → không hiện; luôn qua cổng duyệt supplementary.
- **Nhồi chữ đầy màn** — density validator là lưới, nhưng gốc là NÃO phải hiểu: chữ là
  gia vị ghim ý, không phải phụ đề. Đa số beat = không chữ.
- **Chữ lặp voice vô nghĩa.** Voice nói "rất rẻ" mà chữ hiện "RẤT RẺ" = lãng phí lớp
  nghĩa; hoặc ghim con số ($2), hoặc bổ nghĩa mới (lớp 2–3), không nhại.
- **Chữ đè chủ thể / tương phản kém** — vị trí theo kind đã né phần lớn; kinetic có plate;
  còn lại là việc mắt editor 20% cuối.
- **Mỗi kind một bộ mặt — đừng phá.** Style map cứng là TÍNH NĂNG (nhất quán), không phải
  thiếu tự do; đổi style = đổi trong map, không đổi từng overlay.

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Mật độ chữ/phút của video viral niche | chỉnh ngưỡng `check_overlay_density` theo niche |
| Kind ưa dùng (facts: stat/price; travel: place) | mồi cho NÃO chọn kind |
| Gu font/màu/anim của niche | bảng style per-kênh (mục (b) treo) |
| Video viral có dùng lớp nghĩa 2–3 không, kiểu gì | mẫu cho L2b sâu sinh supplementary đúng gu |
