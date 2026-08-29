# MÔ TẢ VẬN HÀNH — KEN BURNS v1 (f2): ảnh entity hết đứng yên

> Trạng thái: user CHỐT THAM SỐ + duyệt 2026-07-09 ("ảnh đang download ở google về đang để
> đứng yên... keyframe đầu và cuối: đầu 100%, cuối zoom 120-130%") → code cùng lượt.
> Foundation: `f2-ken-burns-punch-in.md` §3 — gói (b treo) "mở khi gặp video thật có beat
> entity" chính thức MỞ. Tham số user THAY dự kiến cũ 105→115%.

## 1. Luật

- **Chỉ ảnh** (route entity — ảnh Google/Serper). Video có chuyển động thật — không đụng (cạm bẫy f2 §4).
- Keyframe scale trên segment ảnh ở `video_l1`: **t=0 → 100%**, **t=cuối-1ms → 120–130%**
  (zoom-in về tâm, deterministic crc32 theo tên ảnh cho đa dạng giữa các ảnh — cùng khuôn seed shot thở 2.0).
- Punch-in: VẪN treo (f2 §3 — overlay+SFX đang phủ nhu cầu nhấn).

## 2. Code chạm

- `packager/assembler.py::_place_video_l1` nhánh photo: `seg.add_keyframe(uniform_scale, 0, 1.0)`
  + `(want_us − EDGE_GUARD_US, zoom)` — pycapcut tự chuyển uniform_scale → KFTypeScaleX với
  cờ `uniform_scale` bật. EDGE_GUARD 1ms tái dùng từ ducking F8.
- Ảnh `source_timerange` luôn bắt đầu 0 → **không dính bẫy time_offset theo-file-nguồn** của
  bài học ducking ([[capcut-volume-keyframe]] chỉ áp audio + source_start > 0).
- Report: 1 dòng "Ken Burns f2: N ảnh".

## 3. Rà chồng chéo (P5)

| Tầng | Kết luận |
|---|---|
| Chart PiP / info-card / overlay text / SFX | đặt ngoài `_place_video_l1` — không đụng (card nửa màn KHÔNG bị zoom) |
| Shot thở | pool chỉ video (`media_type='video'`) — không có ảnh, không đụng |
| Validator pacing Mảnh B | đếm segment thực đặt, keyframe không đổi số segment |
| C1–C5 | keyframe nằm TRONG dict segment — không đụng content id / path / compact write |
| Ảnh <sàn 1280px | F5 Lớp 2 đã chặn từ phễu — ảnh nào tới đây cũng ≥1280px; 130% trên nền đó là mức user chấp nhận (đồng bộ quyết định 480p viral: chất lượng đổi lấy chuyển động) |
| Bẫy hiển thị keyframe (bài học F8 V6) | CapCut có RENDER scale keyframe pycapcut ghi không → **cổng mắt video dựng thử** — Claude không tự báo đạt |

## 4. Cổng

pytest: ảnh có đúng 2 keyframe scale (0→1.0, cuối−1ms→[1.20;1.30], deterministic), video 0
keyframe. Cổng mắt: video SP012 dựng lại — user xem 6 ảnh entity có trôi zoom không.
