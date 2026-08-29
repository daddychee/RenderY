# MÔ TẢ VẬN HÀNH — C ĐỢT 2: C4 tone cấp video · D3 nới local limit

> **Trạng thái: USER DUYỆT CÓ ĐIỀU KIỆN 2026-07-09** ("tính kỹ chồng chéo/làm loạn hệ
> thống — không lỗi thì tiếp tục") → Claude rà lại lần 2 và **CẮT 2 điểm chảy** khỏi
> nháp đầu (chính là 2 chỗ có nguy cơ "làm khó bộ lọc" user lo — xem §C4 Rà chồng chéo).
> Theo roadmap: C đợt 2 = C4 + D3 → code → 1 video kiểm.

---

## C4 — Tone cấp video chảy xuống các tầng (b1 backlog #1)

**Hiện trạng (đã soi code 2026-07-09 — MỚI so với lúc viết b1):**
- `Outline.tone` ("Thái độ của video với chủ đề") **ĐÃ TỒN TẠI** trong schema pass 1
  (`director/schema.py:43`) và nằm sẵn trong `project.json["outline"]["tone"]` — điểm
  b1 ghi "field chưa có" đã lỗi thời từ khi có đường sâu.
- Vấn đề THẬT: tone **không chảy đi đâu cả** (0 consumer): pass 2 gán mood beat không
  được nhắc tone · nhạc (`music/select.py::_chapter_moods`) chỉ đọc chapter.mood +
  music_hint · phễu chấm footage chỉ thấy mood/energy beat + central/video_subject.

**Thiết kế CHỐT (rà lần 2 theo yêu cầu user) — chỉ siết THƯỢNG NGUỒN, 1 tầng quản:**
1. **Pass 2 thấy tone:** chèn 1 dòng vào beats_system (cả đường sâu `live.py` lẫn
   direct cũ — D2 đã cho 2 đường ăn chung khối): *"TONE VIDEO: <tone>. Mood mỗi
   chương/beat phải CHẠM tone này; mood đổi theo mạch content là CÓ CHỦ ĐÍCH, nhưng
   không được lệch thái độ tổng."* — luật NÃO tự kiểm (loại (c) trong b1 §3b), máy
   không phán ngữ nghĩa.
2. **Report:** in tone video ở đầu report để editor đối chiếu khi duyệt draft.

**2 điểm chảy trong nháp đầu bị CẮT sau rà lần 2** (đúng nỗi lo "làm khó bộ lọc"):
- ~~Phễu thấy tone~~ — CẮT: mood beat đã được gán DƯỚI trần tone ở pass 2; phễu chấm
  theo beat.mood là đã thừa hưởng tone. Nhét tone thẳng vào prompt phễu = 2 tầng cùng
  quản 1 thứ (vết luật §6b DNA Mảnh A), NÃO có thể phạt đúp footage → veto nghĩa tăng,
  local vừa lên 21 pick lại tụt. Chấm-tone-trực-tiếp là việc C2b/C5 đợt 5 (có vision).
- ~~Nhạc thấy tone~~ — CẮT: điểm nhạc = |want∩track|/|want|, thêm từ tone vào `want`
  PHA LOÃNG điểm track đang khớp mood chương (want={epic} khớp 1.0 → thêm 1 từ thành
  0.5) → ranking nhạc đổi khó đoán. b1 vốn ghi "Nhạc phục vụ tone ✅ cơ chế có (qua
  mood)" — nhạc thừa hưởng tone qua mood chương là đủ.

**Rà chồng chéo (P5) sau khi cắt:** mood 4 tầng (pass 1 chương → pass 2 beat → nhạc
theo mood → phễu chấm mood clip) — C4 chỉ đứng TRÊN CÙNG chuỗi (chỗ GÁN mood), mọi
tầng dưới nhận mood-đã-chạm-tone qua đường CŨ, 0 hành vi máy đổi, 0 prompt máy nào
khác đổi → không tầng nào âm thầm lật, không cửa loại mới (filter-overload-guard).
KHÔNG validator máy cho tone (máy không đo được "thái độ"). Fail-open: project cũ
outline thiếu tone → prompt y cũ.

**Cổng kiểm:** pytest (tone chảy vào prompt pass 2 khi outline có · nhạc suy vocab từ
tone · fail-open project không tone) + video kiểm C đợt 2: cổng TAI (nhạc các chương có
cùng một "thái độ" không) + mắt tổng thể. Claude không tự phán.

---

## D3 — Nới trần ứng viên local (còn ngỏ cũ, giờ mới chín nhờ C6)

**Hiện trạng (đã soi):** `find_local_candidates(limit=5)` — số 5 đang gánh CẢ HAI vai:
limit mỗi query trong `search_assets` VÀ **trần TỔNG** (`results[:limit]`) cho toàn bộ
ứng viên local của 1 beat. Thời điểm đặt: kho 282 asset. Giờ kho **1874** + C6 vừa mở
recall (query 80–742 khớp — PB8 §D) → trần tổng 5 thành nút thắt: query đầu tiên chiếm
gần hết suất, các query sau gần như vô nghĩa.

**Đề xuất:** nới TRẦN TỔNG 5 → **10** (per-query GIỮ 5). Vì sao 10: pool phễu hiện
~12,5 ứng viên/beat (đo V2: 1094/87) — local tối đa 10 giữ pool ≤ ~20/beat, prompt
batch PA-1 thêm ~5 dòng/beat (chấp nhận, theo dõi qua cost_log); đủ chỗ cho 2–4 query
× vài suất thay vì query đầu nuốt hết.

**Rà chồng chéo (P5):** (a) mọi cửa hiện có chạy Y NGUYÊN trên từng ứng viên (geo-gate
PA2 · ViralLedger c8 · P7 · cửa kỹ thuật + veto phễu) — thêm ứng viên không thêm cửa;
(b) phễu là ĐIỂM, pool giàu hơn chỉ cho trọng tài nhiều lựa chọn (filter-overload OK);
(c) shot thở KHÔNG đụng (pool riêng `videos_for_niche` 500); (d) cán cân local↔Pexels
nghiêng thêm về kho — chính là thứ video kiểm C đợt 2 phải soi bằng mắt; (e) **điều
kiện tiên quyết ĐÃ đạt hôm nay**: tăng suất local chỉ an toàn SAU khi vá tag thiên thể
(2a+2b + re-tag 102 clip) — không thì nhân thêm xác suất lộ ca kiểu b60.

**Cổng kiểm:** pytest (trần tổng mới · per-query giữ 5 · dedup/geo y cũ · regression
hành vi cũ khi kho nghèo) + video kiểm chung với C4.

---

## Cổng chung C đợt 2

1. Code C4 → FULL pytest → commit mốc; D3 → FULL pytest → commit mốc.
2. **1 video kiểm** (nhịp roadmap): đề xuất tái dùng voice SP012 10' (so được với V2
   hôm nay) HOẶC bài space mới nếu anh có — cổng TAI nhạc-theo-tone + mắt footage local.
3. Đạt → C đợt 2 ĐÓNG → C đợt 3 (C1 ambient cho ô thở, cổng TAI riêng).
