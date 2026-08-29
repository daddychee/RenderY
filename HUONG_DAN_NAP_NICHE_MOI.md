# HƯỚNG DẪN NẠP NICHE MỚI (checklist chống quên bước)

> Rút ra từ bài học **life-in** (RD-89 Oman, 2026-07-15): kho nạp đúng đường nhưng
> THIẾU 3 thứ ngầm → SFX nghe "toàn tiếng biển deepsea". Dùng file này để **giao cho
> Claude Code làm hộ** — bạn chỉ cần copy đoạn "CÂU LỆNH GIAO VIỆC" ở cuối.

---

## PHẦN A — Bạn chuẩn bị gì trước khi giao (INPUT)

1. **Tên niche** (vd `life-in`, `deepsea`, `space`).
2. **Folder video mẫu editor thật** của niche đó (càng nhiều draft càng chuẩn DNA).
   VD life-in dùng `E:\PROJECT NHAN BAN\REAL LIFE\REAL*` (44 draft).
3. **Niche này có music-sync không?** (space/deepsea = BẬT; niche mới = TẮT tới khi đo).
4. **Niche này có "world-lock" không?** (deepsea lock — mọi hình ở trong thế giới niche
   kể cả script nói về người/đất liền). Đa số niche đời sống KHÔNG lock.
5. **Niche này dùng NHẠC RIÊNG hay pool chung?** (life-in = RIÊNG từ 2026-07-17: có folder
   `F:\AutoEdit\music\life-in\tracks\` là niche CHỈ chọn nhạc trong đó, không đụng pool
   chung; niche chưa có folder riêng = pool chung như cũ — `music_root_for`).

Nếu bạn không rõ mục 3–4, cứ để Claude Code đề xuất theo mặc định — nó sẽ hỏi lại.

---

## PHẦN B — 7 BƯỚC Claude Code phải làm (checklist gác)

### 1. Học kho + DNA từ draft editor
- `autoedit editor-learn <draft> --niche <n>` cho MỖI draft mẫu → sinh
  `F:\AutoEdit\library\<niche>\dna.json` (nhịp/tốc độ/pacing) + `pause_dna.json` + tag asset.
- **Gác:** đọc `dna.json` xác nhận có đủ `pacing` (cuts_per_min, shot_len), `breathing`
  (scene_types), `signature`. Thiếu = học chưa đủ draft.

### 2. Nạp ambient/SFX hiện trường → `F:\AutoEdit\ambient\<niche>\`
- Nạp file field-sound. **KHÔNG chỉ nạp theo scene_type của video** (đây là gap life-in).
- **Gác 3 điều (BÀI HỌC LIFE-IN — quan trọng nhất):**
  - **(a) scene_type editor pick nhiều đã có file chưa?** Chạy đếm scene_type footage
    editor hay dùng, đối chiếu kind kho. `animal_wildlife` và `food` HAY BỊ 0 file dù
    editor dùng nhiều — kiểm riêng 2 cái này.
  - **(b) âm ĐẶC TRƯNG có kind gọi-được-độc-lập chưa?** Gió / chim / đám đông thường bị
    CHÔN trong scene bucket (vd gió chôn trong `sky_cloud`) → không gọi riêng được. Phải
    tách thành kind riêng (`wind`, `animal_wildlife`, `people_activity`).
  - **(c) mỗi kind ≥4-5 file** để không lặp tiếng. Pool mỏng → nghe lặp.
- Cần thì re-gán từ `raw/` theo NGHĨA (không tải mới) hoặc gom mẫu bổ sung.

### 3. Viết `subject_rules.yaml` — BƯỚC BẮT BUỘC, HAY QUÊN NHẤT
- File `F:\AutoEdit\ambient\<niche>\subject_rules.yaml` map chủ thể niche → kind tiếng.
- **THIẾU FILE NÀY = im lặng rơi về bảng SPACE** (chỉ ocean/water/fire) → mọi niche
  không-vũ-trụ nghe như biển. Đây LÀ root cause life-in.
- Khuôn: copy `subject_rules.yaml` của deepsea/life-in.
- **Thứ tự trong file = ưu tiên: LOÀI/cảnh đặc trưng ĐẶT ĐẦU** (lạc đà thắng gió generic).
- **Gác:** dry-run `subject_kind()` trên pick thật TRƯỚC assemble → xem phân bố kind.
  Nếu >50% ra 1 kind (nhất là ocean) = sai, chưa map đủ.

### 4. Kiểm `default.wav` + file scene_type thiếu
- Phải có `default*` trong kho (nền trung tính khi không khớp scene nào). life-in ban đầu
  thiếu → 4/6 ô thở IM. Chọn nền TRUNG TÍNH (gió/không khí), KHÔNG chọn tiếng biển.
- Scene_type editor hay pick mà kho thiếu → copy từ kind gần nghĩa.

### 5. Cấu hình bảng per-niche trong code (nếu niche cần)
- **Hook SFX:** thêm vào `HOOK_SFX_NICHES` (`schedule.py`) nếu muốn tiếng nhấn ở hook.
- **Drone nền:** `DRONE_SCENE_BY_NICHE` — chỉ bật nếu niche hợp tiếng ù nền (deepsea hợp,
  đời sống thường KHÔNG).
- **World-lock:** `WORLD_LOCK` (`director/live.py`) nếu niche cần khóa thế giới hình.
- **Music-sync mặc định:** ghi vào luật niche (space/deepsea BẬT sẵn).
- **Nhạc riêng niche** (nếu PHẦN A mục 5 = riêng): `autoedit music-init --lib
  F:\AutoEdit\music\<niche>` → copy nhạc có `__mood` vào `tracks\` → `music-import --lib
  ...` — 0 code, chỉ cần folder tồn tại. NHỚ: stage `music` chạy TRƯỚC source nên phải
  gọi `autoedit music <dir> --niche <n>` (project.niche lúc đó chưa có).

### 6. Chạy pytest FULL
- `uv run pytest` — phải PASS 100%. Sửa bảng code có thể vỡ test khác.

### 7. Cập nhật ghi chép
- `ambient_library.yaml` (đếm file kho), memory file niche, `MEMORY.md`.

---

## PHẦN C — Cổng nghiệm thu (BẠN làm, Claude Code KHÔNG tự duyệt)

- **Cổng TAI:** dựng 1 video mẫu → mở CapCut nghe. SFX có đúng bản chất cảnh không?
  (sa mạc phải nghe gió, phố phải nghe phố, KHÔNG phải toàn biển).
- **Cổng MẮT:** footage/pacing/overlay có hợp niche không.
- Nghe/thấy sai chỗ nào → báo tên cảnh, Claude Code chỉnh `subject_rules.yaml` hoặc thay file.

---

## CÂU LỆNH GIAO VIỆC (copy dán cho Claude Code)

```
Nạp niche mới "<TÊN NICHE>" theo HUONG_DAN_NAP_NICHE_MOI.md.
- Video mẫu editor: <ĐƯỜNG DẪN FOLDER>
- Music-sync: <bật/tắt — không rõ thì bạn đề xuất>
- World-lock: <có/không — không rõ thì bạn đề xuất>

Làm ĐỦ 7 bước phần B, ĐẶC BIỆT không quên:
(1) subject_rules.yaml (thiếu = rơi bảng space, nghe như biển)
(2) kiểm animal_wildlife/food có file chưa (hay bị 0)
(3) tách kind âm đặc trưng gió/chim/đám đông (đừng để chôn trong scene bucket)
(4) mỗi kind ≥4-5 file, có default.wav trung tính.
Dry-run subject_kind() trên pick thật trước khi assemble để tôi xem phân bố.
Xong chạy pytest full rồi báo tôi để nghe cổng tai.
```
