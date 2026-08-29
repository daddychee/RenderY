# MÔ TẢ VẬN HÀNH — C ĐỢT 3: C1 AMBIENT CHO Ô THỞ

> **Trạng thái: CHỜ ANH DUYỆT — chưa code.** Backlog #2 của [[e1-sound-design-nhac]],
> điều kiện "sau Phase B" ĐÃ ĐỦ: kho đã tag `scene_type` (enum 14 loại, thiết kế sẵn
> "phục vụ ambient e1"). Nguyên văn user (GHI_CHEP_GOC §5): *"Ambient là thứ khiến hình
> thở không bị 'chết'... tai người nghe khoảng lặng tuyệt đối như lỗi."*

---

## 1. Bài toán

Ô thở hiện chỉ có **nhạc nở** (ducking F8: 0.2→0.5). Chưa có lớp ambient — tiếng môi
trường khớp cảnh (rền vũ trụ, gió, sóng) làm khoảng thở "sâu" thay vì chỉ "to nhạc lên".

C1 v1 = **ô thở đủ dài được thêm 1 clip ambient khớp loại-cảnh footage đang chiếu**,
trên track audio riêng, fade 2 mép. Chỉ ô thở — room-tone toàn video để sau (đúng e1).

## 2. Nguyên liệu đã khảo sát (không phải đoán)

| Thứ | Ở đâu | Kết luận |
|---|---|---|
| Loại cảnh footage | `vision.py::SceneType` — enum 14 loại, ĐÃ tag trên cả kho (space: 1874/1874, trong đó `space` 1399 · `abstract_texture` 101 · `interior` 83 · `sky_cloud` 70 · `mountain_desert` 68...) | Tra `cache.db` theo path/asset_key — **không tốn call vision mới** |
| Lúc nào là ô thở | `ducking.merge_voice_intervals(segments)` — F8 đang dùng | **DÙNG CHUNG lịch với ducking** — 1 nguồn sự thật, ambient và nhạc-nở không bao giờ lệch nhau |
| Footage trong ô | `project.breath_shots` (beat mang ô, miếng theo thứ tự, source local); ô không có shot thở = giữ hình pick beat trước | Biết chính xác từ project.json |
| Khuôn thư viện | `sfx/library.py`: file phẳng `<kind>_<n>.wav` + manifest yaml (license Artlist) + `normalize_audio` WAV 48k (luật C4) | Copy/adapt — anh đã quen quy trình manifest Cowork |
| Đặt vào draft | Track audio mới `ambient` + volume tĩnh + `add_fade` (nhạc đang dùng y vậy) | **0 behavior CapCut mới** → không cần draft test; KHÔNG keyframe trên ambient → không dính bẫy time_offset nguồn |

## 3. Cách vận hành (chạy trong assemble, SAU nhạc + ducking)

1. **Lịch ô thở** = gap giữa các đoạn voice từ `merge_voice_intervals` (+ khoảng thở kết
   video). Chỉ giữ ô **≥ `AMB_MIN`** — ô ngắn fade chưa kịp nghe đã hết, thành rác.
2. **Loại cảnh của ô**: ô có shot thở → `scene_type` của **miếng ĐẦU** (tra cache.db);
   ô giữ-hình → `scene_type` pick của beat đó nếu local; pick stock (Pexels/entity)
   không có tag → fallback.
3. **Chọn file**: `F:\AutoEdit\ambient\<niche>\<scene_type>.wav` — cấu trúc **THEO NICHE**
   (user chốt 2026-07-10 khi xếp kho: "dễ nhớ khi có nhiều niche"; khớp `library\<niche>\`
   và e1 "ambient theo gu niche"). Folder lấy theo `project.niche`; root suy từ
   `machine.json::library_root` cha — 0 config mới. Project không niche / folder không
   tồn tại → tầng tắt (fail-open). Nhiều biến thể `_2`, `_3` xoay vòng theo thứ tự ô. Không có file khớp → `default.wav` (anh chọn âm đại
   diện niche). Không có nốt default → **bỏ qua ô đó** (nhạc nở vẫn lo, không có chỗ nào
   im lặng tuyệt đối). Thư viện RỖNG → toàn bộ tầng tắt, draft y hệt hôm nay (fail-open).
4. **Đặt clip** track `ambient`: phủ đúng khoảng ô, volume `AMBIENT_VOL`, fade in/out
   `AMB_FADE` (fade-out kết thúc ĐÚNG lúc voice vào lại — cùng triết lý "chữ đầu phải rõ"
   của F8). **1 ambient / 1 ô** — ô nhiều miếng khác cảnh vẫn 1 âm (2 ambient trong 6s
   loạn hơn là lệch nhẹ). Cắt từ đầu file nguồn (file Artlist vài phút ≫ ô 4,5–10,5s).
5. **Ghi record + card report**: mỗi ô — thời điểm, dài, scene_type, file, hay lý do bỏ
   (mù tag/thiếu file) — editor kiểm tai có đích.

## 4. Tham số — ĐÃ CHỐT ở cổng TAI V4 (2026-07-10)

| Tham số | Chốt | Vì sao |
|---|---|---|
| `AMBIENT_VOL` | **1.0 (0dB)** ✅ | v1 = 0.4 (theo số editor PB10) **bị nhạc-nở nuốt** — tai user V4: "sfx chìm trong nền nhạc, không hạ volume sfx". Số editor 0.2–0.4 không áp thẳng được vì nhạc nền của HỌ chỉ 0.05–0.1, còn nhạc máy nở tới 0.5. KHÔNG hạ số này khi thấy dày — chỉnh tầng khác |
| `AMB_MIN` | **3.0s** ✅ | ô máy-kéo shot thở 4,5–10,5s đều dính; nghỉ kết câu DNA ~1,55s KHÔNG dính (đúng ý — đó là nhịp voice, không phải chỗ trải ambient) |
| `AMB_FADE` | **1.0s** ✅ | ambient vào/ra êm, không "bật công tắc" |
| Volume nhạc | **KHÔNG đổi** | `BREATH_VOL` 0.5 giữ nguyên — user xác nhận ở cổng tai |

## 5. KHÔNG làm đợt này

- Không room-tone toàn video, không ambient lúc voice nói (e1 để sau).
- Không riser/impact mới — kỷ luật SFX bám-sự-kiện giữ nguyên.
- Không đụng chọn nhạc, ducking, phễu footage, shot thở (chỉ ĐỌC breath_shots).
- Không tag vision cho stock — mù tag đi đường fallback, không tốn call.
- Không đo LUFS — vẫn nhân volume như toàn hệ.

## 6. Rà chồng chéo (P5) — các tầng CÙNG QUẢN âm thanh ở ô thở

| Tầng | Ngược chiều? | Ai lật ai? |
|---|---|---|
| **Ducking F8** (nhạc nở 0.5 cùng chỗ) | Không — cùng chiều "lấp ô thở" | Không lật nhau: DÙNG CHUNG `merge_voice_intervals` nên không có ô nhạc-nở-mà-thiếu-ambient do lệch lịch. Rủi ro thật = **CỘNG DỒN mức âm** (nhạc 0.5 + ambient) → cổng TAI V4 phán: KHÔNG dày, ngược lại ambient 0.4 còn bị nuốt → chốt 0dB |
| **Crossfade nhạc chương 3s** | Không | Ô thở cuối chương = 2 clip nhạc fade + ambient cùng lúc (3 nguồn). Khác track, code nhạc 0 sửa — chỉ mức tổng cần tai kiểm |
| **SFX overlay/chart** | Không | SFX neo `anchor_word` = nằm TRONG lúc voice nói, không rơi vào ô thở; track `sfx` riêng — 0 đụng |
| **Shot thở (hình)** | Không | Ambient chỉ ĐỌC breath_shots; máy shot thở không biết ambient tồn tại. Ô 2–3 miếng khác scene_type → lấy miếng đầu (chấp nhận lệch nhẹ nửa sau ô) |
| **Hình thở 3.0 vi nghỉ** | Không | Vi nghỉ <1.5s đã bị F8 nuốt vào voice liền mạch; `AMB_MIN` 3.0 còn cao hơn → ambient không phập phồng theo câu |
| **Voice** | Không | Ambient chỉ trong ô + fade-out chạm mép voice — chữ đầu sau ô không bị che |
| **Phễu footage / c5** | Không đụng gì | 0 filter mới, 0 prompt đổi ([[filter-overload-guard]] sạch) — ambient đứng SAU source, chỉ tiêu thụ kết quả |

Kết luận rà: không tầng nào bị lật; điểm duy nhất cần mắt-tai người = mức âm cộng dồn ở ô thở.

## 7. Việc ANH cần làm trước cổng tai (M0 — gom file Artlist)

Niche space chỉ cần **3–5 file** là phủ hầu hết ô (75% kho là cảnh `space`):

| File | Âm gợi ý | Ưu tiên |
|---|---|---|
| `space` | space drone / deep hum rền vũ trụ | **BẮT BUỘC** (phủ ~75%) |
| `default` | âm đại diện niche (có thể = 1 bản space khác) | **BẮT BUỘC** (lưới fallback) |
| `sky_cloud`, `mountain_desert` | gió thoáng / gió cao nguyên (2 tên có thể cùng 1 file) | nên có |
| `interior` | room tone nhẹ | tùy anh |

Nhập bằng lệnh mới `autoedit ambient-import` (manifest yaml y hệ sfx — giữ artlist_url
truy license, tự chuẩn hóa WAV PCM 48k thành `<scene_type>_<n>.wav` trong
`F:\AutoEdit\ambient\<niche>\`, file gốc tên dài dọn vào `raw\` giữ truy vết). Brief
paste cho Cowork: `F:\AutoEdit\ambient\COWORK_BRIEF.md`. Từ khóa + số volume tham chiếu
đã đối chiếu 3 draft editor thật: xem `PB10_AM_THANH_3_DRAFT_EDITOR.md`.
**M0 ĐÃ XONG 2026-07-10:** 29 file (space 6 · interior 8 · default 5 · mountain_desert 5
· sky_cloud 5 · +2 dòng dual nature_forest_field) + `ambient_manifest.yaml` máy sinh sẵn
tại `F:\AutoEdit\ambient\space\`. Thứ tự nạp: biến thể hợp-space trước (control room
trước room-tone đời thường; drone trung tính trước dark texture).

## 8. Cổng theo P4

| Milestone | Nội dung | Cổng |
|---|---|---|
| **M1** | Thư viện ambient + lệnh import + fail-open khi rỗng | pytest |
| **M2** | Lập lịch ô + chọn ambient + wire assemble + card report | FULL pytest |
| **M3** | Re-assemble project SP012 → draft **V4** (beats + picks giữ nguyên, chỉ thêm tầng ambient — so thẳng được với V3 hôm qua) | 👂 **ĐẠT 2026-07-10** — verdict: ambient 0.4 chìm trong nhạc → chốt `AMBIENT_VOL=1.0` (0dB), 2 tham số kia giữ. C đợt 3 ĐÓNG |
