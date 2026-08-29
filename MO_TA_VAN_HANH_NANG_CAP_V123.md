# MÔ TẢ VẬN HÀNH — GÓI NÂNG CẤP V1+V2+V3 (từ 3 vấn đề user thấy ở SP012_V2)

> User nêu 2026-07-09 sau khi xem `CONTENT_ENGLISH_20260708_091258_V2`. Đã bàn + chốt
> hướng cùng ngày: V1 = crop 16:9 (phương án A) · V2 = mở rộng entity · V3 = 3a (thiết kế
> lại theo lo ngại đa-hành-tinh của user) + 3b; 3c dời sang C đợt 5 với nguyên tắc
> "quá khó thì bỏ qua, editor chỉnh tay". Trạng thái: **ĐÓNG TRỌN 2026-07-09 — M1+M2+M3
> code cùng ngày (302/302, commit `16e278b`/`9352b61`/`9fa10e2`) + M4 video kiểm
> `SCRIPT_20260709_071612` CỔNG MẮT ĐẠT cả 3 điểm (user: "đã ok, pass qua cả 3 vấn đề").**
> Chi tiết thi công: NHAT_KY §V123.

---

## Bằng chứng gốc (đo thật từ project SP012)

1. **Viền đen:** ffprobe 442 asset → **44 file (~10%) lệch 16:9** — 34 rộng hơn (viền
   trên–dưới, tệ nhất `b112` 2088×720 = 2.9:1), 10 hẹp hơn. Nguồn chính: Pexels bản
   "điện ảnh" 2048×1080 / 2:1 / 2.4:1. Code: `_pick_video_file` chỉ lọc ngang>dọc;
   `normalize_video` không đụng tỉ lệ khung; assembler đặt nguyên trạng → CapCut fit → hở.
2. **Entity hẹp:** `_SOURCING_RULES` + foundation c1 chỉ cho entity với người/sự kiện có
   ngày/hiện vật độc nhất, dặn "0-1 entity/video" — luật viết cho niche đời sống, sai cỡ
   với space (tàu, kính, sự kiện phóng, ảnh far side thật đều tìm chính xác được).
3. **b11 sao Hỏa:** rank_log ghi NÃO phễu TỰ VIẾT "đi bộ trên sao Hỏa" mà vẫn chấm
   nghĩa 8/10 → lỗi ở LUẬT: veto `thuc_the_sai` không có "sai thiên thể"; prompt phễu
   có central_subject chương nhưng không có phạm vi chủ thể VIDEO; và beat này đúng ra
   là sự kiện thật (crew walkout) phải đi entity — dính ngược về (2).

---

## V1 — Chuẩn 16:9 tại normalize (phương án A)

**Điểm chạm duy nhất cho video: `packager/transcode.py::normalize_video`.**
- Probe w×h trước khi transcode. Nếu |AR − 16/9| > **3%** → thêm `-vf crop` **cắt TÂM
  về 16:9** (rộng hơn → cắt 2 bên; hẹp hơn → cắt trên–dưới), số chẵn, KHÔNG upscale.
  Trong ngưỡng 3% (vd viral 852×478 = 1.782) → giữ nguyên như cũ.
- Cắt thẳng MỌI mức lệch, kể cả 2.9:1 (mất ~39% hai bên — đã khuyến nghị: bỏ ở phễu là
  đẻ cửa loại, phạm luật filter-overload-guard; viền đen tệ hơn phần hình bị cắt).
- Mọi đường placement hưởng tự động (beat 1-shot, multi-shot, shot thở) vì đều qua
  `_place_video_l1` → `normalize_video`.

**Ảnh (KHÔNG crop file — giữ nội dung tài liệu/poster): sửa tại assembler.**
- Tính hệ số phủ khung `c = max(AR/1.778, 1.778/AR)` từ w×h ảnh đã normalize.
- Ảnh có Ken Burns: keyframe scale đổi từ `1.0 → zoom` thành **`c → c×zoom`** (ảnh 16:9
  thì c=1, y hệt hôm nay). Ảnh quá ngắn không Ken Burns: đặt scale tĩnh = c.
- Bài học F8 giữ nguyên: keyframe ĐÈ scale tĩnh → ảnh Ken Burns chỉ dùng keyframe.

**Ngoài phạm vi đợt này (ghi còn ngỏ):** viền đen NƯỚNG TRONG PIXEL của nguồn
viral/NASA (file 16:9 nhưng pixel có bar) — chỉ bắt được bằng `ffmpeg cropdetect` ở
ống nạp; làm ở MẺ NẠP SAU, kho 1209 clip hiện tại không đụng (đụng = re-tag).

**⚠ Cache norm:** `normalize_video` idempotent theo mtime → project cũ re-assemble sẽ
TÁI DÙNG file norm chưa crop. Video kiểm phải xóa folder norm của project (hoặc dựng
project mới) trước khi chạy.

## V2 — Mở rộng tiêu chí entity (niche facts/space)

**2 chỗ sửa CÙNG nội dung** (đường sâu đọc foundation, direct cũ đọc prompt):
1. `foundation/c1-phan-tuyen-nguon.md` — bảng tuyến entity (§1) + yếu tố (§2).
2. `director/prompts.py::_SOURCING_RULES`.

**Thêm 3 nhóm được phép entity** (bên cạnh người/sự kiện có ngày/hiện vật):
- **Máy móc/phương tiện ĐƯỢC ĐẶT TÊN:** tàu vũ trụ, tên lửa, kính thiên văn, rover, vệ
  tinh, trạm (Orion, Saturn V, JWST, Chang'e 4...) — stock actor/CGI generic thay chúng
  là lừa người xem đúng nghĩa WRONG-vs-BLAND.
- **Sự kiện thật của chương trình không gian:** phóng, đổ bộ, spacewalk lịch sử, crew
  walkout (vd b11 = Artemis II walkout — có ảnh/footage báo chí thật).
- **Thiên thể/địa hình vũ trụ NÊU ĐÍCH DANH khi ảnh thật tồn tại:** far side, hố Tycho,
  South Pole–Aitken... (ảnh LRO/NASA thật > mô phỏng generic).

**Giữ nguyên:** địa danh du lịch/đời sống vẫn CẤM entity (luật cũ đúng cho travel);
entity cạn → needs_human, không rơi về stock; sàn phân giải ảnh 1280px (F5 Lớp 2);
veto c2 dạng ii vẫn gác thực thể sai. **Ngân sách entity đổi theo niche:** facts/space
~3–8 beat/video (thay "0-1"); niche đời sống giữ 0-1.

**Bản quyền (đã nêu với user):** ảnh Google quyền hỗn hợp — space đa phần NASA/ESA
public domain nên rủi ro thấp; cơ chế không đổi (entity đã dùng từ trước), chỉ tăng
tần suất. Ken Burns đã đóng nên ảnh không còn đứng yên.

## V3 — Phạm vi chủ thể video + vá luật veto (3a thiết kế lại + 3b)

**3a — `video_subject` = PHẠM VI, không phải chủ thể đơn** (giải lo ngại đa-hành-tinh):
- Schema `Outline` thêm field **`video_subject: str = ""`** (optional — project/draft cũ
  thiếu field vẫn chạy, fail-open). Đạo diễn điền 1 dòng, ĐƯỢC PHÉP số nhiều:
  "the Moon and its far side" / "all 8 planets — one per chapter".
- `outline_system` (direct cũ) + 1 câu trong `## OUTPUT` của direct_context (đường sâu)
  yêu cầu điền field này.
- Phễu (`sourcer/runner.py` → `rank_batch`/`rank_beat` → prompts) in thêm dòng
  `VIDEO SUBJECT (scope)`. **Luật phán theo THỨ TỰ NEO: chương trước, video sau** —
  ứng viên nhận diện được là thực thể NGOÀI central_subject chương VÀ ngoài phạm vi
  video → veto. Video đa hành tinh: chương Mars có central_subject Mars → footage Mars
  khớp CHƯƠNG → ok, không oan.
- Không có video_subject (project cũ) → không in dòng đó, phễu chạy y hệt hôm nay.

**3b — vá `RANK_SYSTEM` veto `thuc_the_sai`:** thêm "wrong planet / celestial body /
space setting" vào danh sách ví dụ + câu chốt: **"action/pose similarity does NOT
redeem a wrong entity"** (đúng ca b11: khớp hành động không gỡ tội sai sao Hỏa).

**3c — vision gate top-pick: DỜI sang C đợt 5** (ghi vào DINH_HUONG), với nguyên tắc
user chốt: chỉ soi TOP-PICK (không soi cả pool), fail → demote thử ứng viên kế đúng
1 lần, vẫn fail → lấy bản tốt nhất + warning cho editor (KHÔNG needs_human ồ ạt,
không thành cửa loại thứ 3).

---

## RÀ CHỒNG CHÉO (P5 — các tầng cùng quản)

| Tầng | Đụng gì | Ngược chiều? |
|---|---|---|
| **Ken Burns (KEN-BURNS đã đóng)** | V1-ảnh đổi keyframe start 1.0 → c | KHÔNG ngược — c=1 với ảnh 16:9 (đa số); regression giữ hành vi cũ cho 16:9 |
| **Ducking F8 / bẫy time_offset** | V1 không đổi time_offset nào; ảnh source_start=0 | không đụng |
| **Slow-mo kéo giãn (`_place_video_l1`)** | crop không đổi duration | không đụng |
| **filter-overload-guard (2 veto, điểm không cửa loại)** | V1 sửa ở transcode (máy, sau pick) — KHÔNG thêm cửa phễu; V3 mở rộng NỘI HÀM veto dạng 2, không thêm dạng mới | tuân thủ |
| **c2 veto / c1 route (foundation)** | V2 sửa chính c1; c2 dạng ii (thực thể sai) cùng chiều với V3b — 2 tầng cùng bắt 1 lỗi là chấp nhận (an toàn kép), không lật nhau | cùng chiều |
| **Geo-gate PA2 (lọc sai quốc gia local)** | V3b mở rộng veto ở NÃO — geo-gate là code lọc local, không giao nhau | không đụng |
| **PA-1/PA-2 phễu batch (token)** | V3 thêm 1-2 dòng prompt/call — không phình output (ly_do vẫn ≤12 từ) | không đụng |
| **Norm cache theo mtime** | V1 đổi output norm — project cũ tái dùng file cũ → video kiểm PHẢI dọn norm | ghi ở V1 |
| **`_zoom_vf` c8 (nạp viral)** | crop 16:9 nằm ở normalize (lúc DỰNG), zoom c8 nằm ở ingest (lúc NẠP) — 2 tầng khác nhau, không chồng | không đụng |
| **Memory `video-first-routing`** | V2 sửa luật "ảnh là ngoại lệ hiếm" → thành "hiếm THEO NICHE đời sống; facts/space 3-8" — PHẢI cập nhật memory khi đóng | cập nhật cùng M2 |
| **Consumer `project.outline` (report, ingest, validator)** | V3 thêm key mới — mọi consumer đọc bằng `.get` / schema optional → fail-open | không đụng |
| **Đường direct cũ** | D2 vừa đồng bộ — V2 (prompt) + V3 (schema/outline_system) sửa CẢ 2 đường cùng lúc trong cùng milestone | đồng bộ |

## VERIFY / CỔNG

- **M1 (V1):** pytest — hàm tính crop (rộng/hẹp/16:9/ngưỡng 3%) + Ken Burns c→c×zoom
  (ảnh 16:9 giữ nguyên = regression) + FULL suite. Cổng số: ffprobe folder norm của video
  kiểm = 100% 16:9.
- **M2 (V2):** sửa foundation + prompt (không logic code) — pytest FULL không vỡ.
- **M3 (V3):** pytest — schema optional (draft cũ thiếu field pass) + prompt phễu có/không
  video_subject + FULL suite.
- **M4 — VIDEO KIỂM chung (cổng MẮT user, Claude không tự báo đạt):** dựng 1 video
  (SP012 re-run sau khi dọn norm, HOẶC video space mới nếu user có input) — soi đúng 3
  thứ: (1) không còn viền đen; (2) entity thật xuất hiện ở beat máy móc/sự kiện;
  (3) không còn footage sai thiên thể. Mỗi M xong → commit git.

## ĐIỂM ỦY QUYỀN (Claude tự quyết nếu user không có ý kiến khi duyệt)

1. Ngưỡng lệch AR để crop: **3%**.
2. Crop thẳng mọi mức lệch kể cả 2.9:1 (không chặn ở phễu).
3. Ngân sách entity niche facts: **3–8 beat/video** (số khởi điểm, tinh theo DNA sau).
4. Video kiểm M4: SP012 re-run hay video mới — chờ user chọn khi tới M4.
