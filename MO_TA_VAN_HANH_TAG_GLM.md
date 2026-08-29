# MÔ TẢ VẬN HÀNH — SCHEMA TAG GLM + ỐNG NẠP KHO DNA (Phase B mở màn)

> **CỔNG DUYỆT VẬN HÀNH** (luật F0): user đọc duyệt file này rồi MỚI code.
> Vị trí lộ trình: F0 bước 4 — "GOM MỌI PHẦN 5 thành spec schema tag GLM TRƯỚC khi tag
> (tag lại = rất đắt token)". Nguồn: phần 5 của 18 file `foundation/` + PRD §9.1 + code
> thật (`library/vision.py`, `library/db.py`, `music/library.py`).
>
> **Vì sao phải chốt schema TRƯỚC:** tag ~100 project nguồn là khoản token lớn nhất
> Phase B. Thiếu 1 field bắt buộc = tag lại toàn kho. Thừa field = đốt token + AI loạn
> ([[filter-overload-guard]]). File này chốt "tag 1 lần đủ cho pacing + variety + mood +
> ambient + chữ ký".

---

## 1. Một lượt tag, hai sản phẩm

| Sản phẩm | Là gì | Ai tiêu thụ |
|---|---|---|
| **KHO LOCAL** | footage cắt từ project nguồn, tag xong nằm trong `cache.db` | phễu c5 (tuyến CHÍNH local-first — [[footage-source-local-first]]), luật c6 signature |
| **SỐ LIỆU DNA** | thống kê per-niche rút từ chính các cảnh đã tag + metadata | pacing validator (d1), sàn thở (d2), ngữ pháp cỡ cảnh (c7), mood arc (b1), dB ducking (e1)... |

Nguyên tắc: **mọi field chỉ được vào schema nếu có ≥1 người tiêu thụ ĐÃ ĐỊNH DANH**
(trỏ foundation). Không tag "phòng khi cần" (P2).

## 2. Nguồn nạp (3 loại)

1. **Project CapCut của editor công ty** — giàu nhất: `draft_content.json` cho SẴN mép cắt
   (segment + source range + file nguồn) + text/nhạc/SFX layer. Ống chỉ **ĐỌC** draft nguồn
   (không ghi → không đụng C1–C5), cắt clip bằng ffmpeg theo source range, chuẩn C4.
2. **Video viral đối thủ tải về** — theo lời user (c6): *"đưa vào CapCut tách cảnh"* → editor
   tách bằng CapCut, thành loại 1. 🔸 Điểm treo: có cần tool TỰ tách cảnh (PySceneDetect)
   không, hay đợt đầu 100% đi qua CapCut? **Đề xuất: đợt đầu chỉ nhận draft CapCut** — đúng
   quy trình editor đang làm, không thêm dependency; tự-tách để sau nếu khối lượng lớn.
3. **Folder footage rời** — đường `library-index` hiện có, giữ nguyên (folder = ground truth
   địa danh, đã chạy).

🔸 Cảnh nào thành ASSET vs chỉ ĐẾM thống kê (vd talking-head đối thủ không tái dùng được):
chốt ở milestone ống nạp (PB4), không thuộc schema.

## 3. SCHEMA TAG — phần lõi cần duyệt

### 3a. Field GLM chấm (1 call/asset; video <10s = 1 frame GIỮA clip, ≥10s = 2 frame — user chốt 2026-07-07, tiết kiệm ~35% cost vì cảnh cắt theo mép editor gần như đồng nhất)

| Field | Kiểu | Trạng thái | Foundation tiêu thụ |
|---|---|---|---|
| `subject` | str EN ngắn | GIỮ nguyên | c4 (search LIKE) |
| `description` | 1 câu EN | GIỮ nguyên | c4 search + NÃO chấm nghĩa phễu |
| `shot_size` | enum `wide/medium/close_up/extreme_close_up/aerial` | GIỮ — **BẮT BUỘC** | c7 (tín hiệu CHÍNH variety) + d1 chuỗi cỡ cảnh |
| `mood` | **NÂNG: free string → enum đóng** = đúng 19 mood của nhạc (`music/library.py::MOOD`), chọn 1–2 | SỬA | b1 (đầu chấm mood sau) + e1 (khớp nhạc) |
| `scene_type` | **MỚI** — enum đóng 14 giá trị: `nature_water / nature_forest_field / mountain_desert / sky_cloud / urban_street / urban_landmark / interior / people_activity / food / animal_wildlife / underwater / space / abstract_texture / other` | THÊM — **BẮT BUỘC** | e1 (chọn ambient theo loại cảnh) + c6 (đếm tần suất → signature/) + thống kê niche |
| `camera_angle` | enum `eye_level / low_angle / high_angle / overhead / unknown` | THÊM — **CHỈ MẺ THỬ** (c7 đã chốt: tag thử mẻ nhỏ → đo tin cậy → không tin thì BỎ HẲN field, không tag đại trà) | c7 (phụ, chỉ-cộng) |
| `has_people` | bool | GIỮ nguyên | lọc nhanh + thống kê |
| `tags` | 5–10 keyword EN | GIỮ nguyên | c4 (vocabulary thực tế nổi lên SAU khi tag ~100 project) |

**Vì sao mood lấy đúng 19 từ của nhạc:** mood đang tồn tại ở 3 tầng (chapter.mood free-text
→ map `_MOOD_SYNONYMS` → vocab nhạc đóng). Thêm footage mood mà đẻ vocabulary riêng =
tầng map thứ 4, đầu chấm mood b1 sau này phải phiên dịch chéo. Dùng chung 19 từ → footage ↔
chương ↔ nhạc so thẳng, 0 bảng map mới.

### 3b. Field đo bằng CODE THUẦN — 0 token (cùng lượt nạp, không GLM)

| Field | Cách đo | Foundation tiêu thụ |
|---|---|---|
| `duration / width / height / fps` | ffprobe (đã có sẵn hàm) | d1 pacing + cửa kỹ thuật phễu |
| `dominant_color` (hex) + `brightness` (0–1) + `saturation` (0–1) | PIL/numpy trên CHÍNH frame đã rút cho GLM (không decode 2 lần) | b1 — lớp RẺ C2b so màu histogram (đã thiết kế ở F1, giờ mới có chỗ chứa số) |
| `source_video` + `scene_start` + `scene_index` | ống nạp ghi khi cắt | truy vết + thống kê d1 (vị trí trong video) |
| `has_voice` (cảnh nguồn có thoại không) | so khoảng cảnh với transcript/segment voice của video nguồn | d2 — tần suất + độ dài ô thở của niche |

**Chủ động KHÔNG thêm** (chống phình): `motion` (độ chuyển động), `energy` footage, chấm
điểm thẩm mỹ — chưa có người tiêu thụ định danh trong 18 foundation. Muốn thêm sau = sửa
spec này + user duyệt lại.

## 4. Engine tag: GLM-4.6V native (thay Claude haiku)

- Theo CLAUDE.md §5: vision = **GLM-4.6V native** `https://open.bigmodel.cn/api/paas/v4/chat/completions`
  (KHÔNG Anthropic-compat — nuốt ảnh → bịa) + `"extra_body": {"thinking": {"type": "disabled"}}`
  (bài học `glm-api-lessons`). Cần `GLM_API_KEY` vào `.env` padoma (key đang ở project nhan ban).
- `GLMVisionTagger` cắm vào Protocol `VisionTagger` có sẵn — `ClaudeVisionTagger` GIỮ làm
  fallback (`library-index --engine claude`), giống mẫu engine của `direct`.
- Giữ nguyên: 2 frame/video (1/4 + 3/4), folder_context = ground truth địa danh, structured
  output Pydantic (GLM: parse JSON từ text + retry 1 lần nếu vỡ schema).

## 5. Chiến lược token (PRD §9.1 — "lưu ý cứng")

1. **Cache đã có:** `needs_index` theo mtime — tag đúng 1 lần/file. THÊM điều kiện: tag lại
   khi thiếu field bắt buộc mới (`scene_type=''`) → asset cũ (nếu có) tự nâng cấp, kho mới
   không ảnh hưởng.
2. **MẺ THỬ trước đại trà (PB3):** nạp 1 project nguồn → tag ~30–50 cảnh → user soi chất
   lượng tag bằng mắt (đúng/sai shot_size, scene_type, mood) + đo cost thật/asset → chốt
   camera_angle giữ hay bỏ → MỚI tag đại trà. 🔸 KHÔNG ước cost trước — đo từ mẻ thử.
3. Tag tuần tự + resume theo DB (idempotent sẵn); cần nhanh hơn thì song song hóa sau,
   không làm đợt này.

## 6. RÀ CHỒNG CHÉO (P5 — các tầng cùng quản thứ sắp đụng)

| Tầng hiện có | Đụng gì | Ngược chiều? Ai lật ai? |
|---|---|---|
| **Vocabulary mood 3 tầng** (chapter free-text → `_MOOD_SYNONYMS` → MOOD nhạc) | mood footage MỚI | KHÔNG ngược — chọn đúng vocab tầng cuối (19 từ), không đẻ map mới. Mood footage đợt này chỉ NẰM TRONG DB, chưa nối phễu → không tầng nào lật tầng nào. Nối đầu chấm mood = mô tả vận hành riêng sau (backlog b1). |
| **Phễu c5 ĐÓNG BĂNG** (2 veto, chiều điểm cố định) | tag mới | scene_type/mood/camera_angle KHÔNG thành veto thứ 3, KHÔNG thêm chiều điểm đợt này. Chỉ là dữ liệu. Phễu không đổi 1 dòng. |
| **`search_assets` LIKE 5 trường** (subject/description/tags/category/folder_path) | cột mới trong DB | Cột mới KHÔNG vào LIKE — kết quả search local hiện tại không đổi (regression: test search cũ phải pass nguyên). |
| **`local.py` dict ứng viên** (đã mang shot_size/mood từ F5-M2) | mood đổi thành enum | Giá trị mood giờ là từ trong 19-vocab thay vì free-text — NÃO phễu đọc note như cũ, không consumer nào parse mood theo format. Grep consumer khi code (P5). |
| **`needs_index` mtime** | field mới | Asset tag cũ không tự tag lại → thêm luật "thiếu scene_type → tag lại" (mục §5.1). Không có cách nào âm thầm giữ hàng cũ rỗng. |
| **`niche_profile.yaml::audience_bias`** | ống nạp | c6 bản gọn đã BỎ audience_bias — ống nạp KHÔNG nối gì vào ô này (tránh hồi sinh thứ user đã cắt). |
| **Luật CapCut C1–C5** | đọc draft nguồn | Chỉ ĐỌC draft editor, không ghi → C1/C3/C5 không kích hoạt. Clip cắt ra chuẩn hóa C4 (H.264 CFR 30fps) trước khi vào kho. |
| **Schema `AssetTags` chung 2 tagger** | GLM + Claude fallback | Đổi schema ăn cả 2 tagger + indexer + DB — khi code grep MỌI chỗ đọc `AssetTags`/cột DB (P5), sửa đồng bộ. |

## 7. Schema tag ĐỦ cho số liệu DNA chưa? (đối chiếu 18 phần 5)

| Nhóm số liệu | Cần gì | Có từ đâu |
|---|---|---|
| d1 pacing (phân bố độ dài shot theo vị trí, mật độ cắt, hold, energy curve) | độ dài + vị trí cảnh | metadata cảnh (§3b) — KHÔNG cần GLM |
| d2 thở (tần suất, phân bố độ dài, footage trong ô thở) | has_voice + duration + tag cảnh | §3b + §3a |
| c7 variety (phân bố cỡ cảnh, chuỗi điển hình, nhịp đặc tả) | shot_size theo thứ tự cảnh | §3a + scene_index |
| c6 chữ ký (loại footage lặp nhiều nhất → điền `signature/`) | đếm tần suất scene_type/subject OFFLINE | §3a (đúng luật c6: đếm offline, KHÔNG thành luật runtime) |
| b1 mood (bảng màu theo vị trí, mood arc) | dominant_color/brightness/saturation + mood | §3b + §3a |
| e1 (ambient theo loại cảnh; dB ducking; BPM nhạc) | scene_type; audio analysis draft nguồn | §3a; dB/BPM đọc từ NHẠC draft nguồn — milestone riêng, không thuộc tag footage |
| c1/c2/a2/a3/c3/f1/f2 (route ratio, literal/metaphor, hook, motif, mật độ chữ, Ken Burns) | map thoại↔footage + layer text/transform draft nguồn | đọc draft + transcript nguồn — milestone thống kê SAU, **không cần thêm field tag GLM nào** |

→ Kết luận: schema §3 là ĐỦ, "tag 1 lần đủ" đúng như d2/b1 yêu cầu. Các số liệu nhóm cuối
lấy từ draft nguồn chứ không phải từ vision.

## 8. Milestone Phase B (P4 — mỗi mốc 1 cổng, không nhảy cóc)

| Mốc | Nội dung | Cổng |
|---|---|---|
| **PB1** | Spec này | 👁 user duyệt file này |
| **PB2** | `GLMVisionTagger` + schema mới (`AssetTags` + cột DB migrate) + đo màu code thuần + luật re-tag thiếu field | pytest (fake GLM + histogram + migrate DB cũ) |
| **PB3** | MẺ THỬ: nạp 1 project nguồn user đưa → tag 30–50 cảnh (CÓ camera_angle) | 👁 user soi tag đúng/sai + cost thật + chốt giữ/bỏ camera_angle |
| **PB4** | Ống nạp draft CapCut nguồn (đọc segment → cắt ffmpeg C4 → tag → DB) + nạp đại trà niche đầu | pytest + 👁 kill-log nạp + `library-search` ra hàng thật |
| **PB5** | Thống kê DNA đợt 1 (d1 pacing + d2 thở + c7 cỡ cảnh + c6 tần suất signature) per-niche | pytest + 👁 user đọc bảng số liệu |

Sau PB5 mới bàn: nối đầu chấm mood vào phễu (b1), pacing validator ăn số DNA (d1),
ambient-thở (e1) — mỗi cái 1 mô tả vận hành riêng.

## 9. Điểm treo 🔸 — user chốt khi duyệt

1. **14 giá trị `scene_type`** (§3a) đủ cho space / deepsea / travel chưa? Thiếu loại nào
   anh hay dùng thì thêm NGAY BÂY GIỜ (thêm sau = tag lại).
2. **Mood footage = đúng 19 mood của nhạc** — đồng ý?
3. **Tách cảnh video viral:** đợt đầu 100% qua CapCut (editor tách, tool đọc draft) — đúng
   quy trình hiện tại của team không?
4. **Niche đầu tiên nạp** (travel?) + khi tới PB3 anh chỉ folder 1 project nguồn mẫu.
5. **`GLM_API_KEY`**: copy từ `.env` project nhan ban sang `.env` padoma (tôi làm ở PB2).
