# MÔ TẢ VẬN HÀNH — MUSIC SYNC: nhạc nền dẫn dắt cắt cảnh (user duyệt gói 2026-07-13)

> Bối cảnh: user đặt bài "chuyển cảnh theo beat nhạc như editor thật (nhất là hook)".
> Nghiên cứu 3 vòng trên dữ liệu thật (26 draft editor công ty space+deepsea + 30 video
> kênh top space, ~11.000 điểm cắt — memory `editor-music-sync-study`): **không ai cắt
> theo lưới nhịp đều, kể cả hook** (giả thuyết 70% hook theo nhịp: cần lift ≥1,6, đo được
> 0,86). "Theo nhạc" thật = 4 hành vi đo được → gói 4 cơ chế + 1 cửa thử nghiệm.
> User duyệt hướng này 2026-07-13; luật J-cut và hook=chương 0 đã chốt cùng ngày.

## 1. Bốn cơ chế + một cửa thử nghiệm

| # | Tên | Cơ chế | Số liệu gốc | Code dự kiến |
|---|---|---|---|---|
| 1 | **M-VOL** — volume nhạc theo vùng+niche | Nhạc ở **hook (chương 0) TO hơn thân bài** theo tỷ lệ DNA niche; thân bài GIỮ số đã qua cổng tai V10 (duck 0.2 / breath 0.5). Ducking F8 nhận mức theo zone thay hằng số. | Editor: space hook 0.377 / body 0.076 (ratio ~5×, ride keyframe 29/38); deepsea 0.474 / 0.355 (ratio ~1,3×, to đều) | `packager/ducking.py` + `assembler.py` (hằng → hàm zone-aware) |
| 2 | **M-STAGE** — stage `music` mới giữa `cut` và `source` | Chọn bài per-chapter SỚM (thuật toán `select_music()` giữ nguyên 100%), ghi `music_selections` + `music_plan` (grid/accent map trên timeline) vào project.json (NT1). `assemble` đọc nếu có; **không có → tự chọn như cũ** (đường cũ nguyên vẹn = fallback). Neo offset: `src_offset` lượng tử về accent/downbeat gần nhất để điểm nhấn đầu tiên rơi đúng cắt đầu chương. | Editor thật chọn nhạc trước rồi dựng (user xác nhận); máy cần accent map trước source/assemble | `music/plan.py` (mới) + `cli.py` + `project.py::PIPELINE_ORDER` |
| 3 | **M-ACCENT** — accent-snap có lead | Mép cửa sổ video nằm trong ±`SNAP_TOL` (0,3s) của **accent mạnh** (thưa ~0,3/s, KHÔNG phải grid đều) → trượt về `accent − SNAP_LEAD`. Trần `SNAP_CAP` 15% tổng cut; ưu tiên khi chạm trần: hook > mép vào ô thở > body. CHỈ dịch video — voice WAV không đụng (hệ tọa độ kép). **Luật J-cut (user duyệt):** hook snap thắng (cắt thẳng); body J-cut thắng (mép thuộc J-cut miễn snap). | Editor space body: cut trúng accent ±100ms = 14% vs nền 7% (lift 2,0, z+7,2); kênh top: khóa pha yếu **TRƯỚC** beat 120–175ms (~10% cut, "whoosh vào hit") → cần lead | `packager/coverage.py` (bước snap sau J-cut, trước place) |
| 4 | **M-CHANGE** — đổi nhạc neo vào cut | Điểm sang nhạc chương mới đặt ĐÚNG một mép cắt video (tìm cut gần ranh giới chương nhất trong ±2s). Kiểu chuyển theo niche: deepsea đổi thẳng (xfade ngắn), space giữ crossfade 3s + ride volume. | Deepsea: 174 lần đổi-nhạc-trùng-cut ±150ms; space: 4 (toàn crossfade) | `packager/assembler.py::_add_music_by_chapter` |
| 5 | **M-GRID** — thử nghiệm, mặc định TẮT | Flag `--sync-targets grid`: hook dùng downbeat làm tập mục tiêu snap thay accent (máy móc dùng chung M-ACCENT). Dựng đúng 1 video kiểm để CỔNG MẮT phân xử trực giác "cắt theo nhịp" — không tranh luận lý thuyết. | Trực giác user; dữ liệu 2 nguồn nói không, nhưng chi phí thử ~0 khi đã có hạ tầng | flag trong `music/plan.py` |

## 2. Hạ tầng M0 — analyzer nhịp/accent cho MỌI bài nhạc

- Mở rộng `music/analyze.py`: thêm `beat_times[]`, `downbeats[]` (ước lượng pha mạnh),
  `accents[]` (onset mạnh percentile 70, min-gap 1s), `beat_quality` → **tier A/B/C**:
  A nhịp rõ (full sync) / B yếu (chỉ accent) / C ambient trôi (**TẮT sync — chạy y như
  hôm nay, fail-open**; quan trọng: deepsea nhiều ambient, librosa tự "bịa" grid ~120BPM
  cho cả nhạc không nhịp — bẫy đã ghi memory).
- Ghi vào `music_index.json` (schema thêm field, PRESERVE các field cũ).
- **Tự chạy khi `music-import` + khi nạp nhạc editor (editor-learn/staging)** — luật user:
  mọi bài nhạc mới đều phải có grid. Backfill 1 lần: `autoedit music-analyze --regrid`
  cho pool hiện có (~128 bài). In phân bố quality để chốt ngưỡng tier (🔸).
- NT4 sạch: mọi timestamp từ tín hiệu librosa, LLM không sinh số nào.

## 3. Rà chồng chéo (P5 — từng tầng cùng quản)

- **Voice WAV / silence-snap ±200ms / ONSET_GUARD (cutter):** KHÔNG đụng — sync chỉ dịch
  mép VIDEO; audio segment giữ nguyên từng sample.
- **`check_coverage_invariants`:** mép chung 2 cửa sổ dịch CÙNG NHAU → không hở/đè;
  giữ `round()` µs (vết bug SegmentOverlap 1µs).
- **J-cut hình thở 2.0:** NGƯỢC CHIỀU thật — đã chốt luật ưu tiên (bảng trên). Thứ tự
  trong assemble: coverage → split breath shots → J-cut → **snap** (snap biết mép nào
  thuộc J-cut để miễn/đè theo zone).
- **Hình thở 3.0 / micro-pause (CUT):** chạy TRƯỚC music → grid tính trên timeline cuối.
  RÀNG BUỘC: chạy lại `cut` → timeline đổi → **bắt buộc chạy lại `music`** (đánh dấu
  stale trong project.json, stage order chặn).
- **Ducking F8:** envelope vẫn theo voice segment; M-VOL chỉ đổi MỨC duck/breath theo
  zone tại 1 chỗ; keyframe time_offset theo FILE NGUỒN giữ nguyên (vết capcut-volume-keyframe).
- **Shot thở 1–3 miếng:** mép VÀO ô thở được snap (nhạc 0.5 nghe rõ — đáng nhất);
  mép GIỮA các miếng: đợt sau, không thuộc gói này.
- **Chữ ký pacing NÃO (§6b):** KHÔNG in grid/accent cho NÃO. M-ACCENT không thêm/bớt cut
  (chỉ dịch ≤0,3s) → không đụng pacing. M-GRID (thử nghiệm) có thể thêm cut → chỉ trong
  video kiểm, không vào mặc định.
- **Viral ledger / trần / REF / PEAK:** chỉ quan tâm pick, không quan tâm mốc — dịch mép
  ≤0,3s không đổi pick nào.
- **Ken Burns f2 + punch-in:** keyframe scale tính theo duration segment — mép dịch làm
  duration đổi nhẹ → tính keyframe SAU snap (kiểm bằng test).
- **SFX/whoosh theo cut:** đặt SAU snap để whoosh ôm mép mới.
- **Music usage/diversity + luân phiên track music/music2:** giữ nguyên; M-CHANGE chỉ
  dịch điểm bắt đầu segment nhạc ≤2s.
- **Report M7:** thêm khối "MUSIC SYNC": bài/chương + tier, % cut snap theo zone,
  volume vùng — cho cổng mắt/tai đối chiếu.

## 4. Milestones (P4 — mỗi mốc: FULL pytest + NHAT_KY + git commit + chờ user)

| Mốc | Nội dung | Cổng |
|---|---|---|
| M0 | Analyzer beat/accent/tier + backfill pool + auto khi nạp nhạc mới | pytest (grid track thật, tier, idempotent); chưa đổi video nào |
| M1 | Stage `music` + fallback + neo `src_offset` vào accent | pytest: cùng input → chọn ĐÚNG bài như đường cũ; schema mới đọc/ghi |
| M2 | M-VOL zone volume + ducking zone-aware | pytest + **video kiểm cổng TAI** |
| M3 | M-ACCENT snap + M-CHANGE neo đổi nhạc + report metrics | pytest (invariants sau snap, J-cut luật, trần 15%) + **video kiểm cổng MẮT+TAI** |
| M4 | (tùy chọn) M-GRID 1 video thử nghiệm | cổng mắt phân xử |

Toàn gói sau cờ `--music-sync` (hoặc bật theo niche profile), **mặc định TẮT** tới khi
M2/M3 qua cổng.

## 5. Số 🔸 (chỉnh khi có bằng chứng — khởi điểm)

`SNAP_TOL = 0.30s` · `SNAP_LEAD = 0.08s` (dải knob 0–0.12; nguồn: kênh top lệch trước
beat 120–175ms nhưng có thể lẫn trễ detector) · `SNAP_CAP = 15%` · `ACCENT_MIN_GAP = 1.0s`
· `ACCENT_PCTL = 70` · ngưỡng tier A/B/C: chốt sau khi backfill in phân bố quality ·
volume hook khởi điểm: space duck 0.35 / deepsea 0.30 (body giữ 0.2/0.5 đã qua tai V10;
tỷ lệ hook/body theo DNA, mức tuyệt đối chỉnh ở cổng TAI M2) · cửa sổ neo M-CHANGE ±2s.

> **Kết quả backfill M0 (2026-07-13, 128 bài):** ngưỡng khởi điểm B≥1.3 / A≥2.0 cho
> A=76 · B=50 · C=2; quality min 1.28 / p25 1.58 / median 2.19 / p75 2.98 / max 7.13.
> ⚠ Vài bài ambient deepsea đặt tên tay ("nền deepsea trầm sợ" q=2.09, "dưới nước 4"
> q=2.08) lọt tier A — vô hại với gói mặc định (M-ACCENT chỉ dùng accent, có ở cả A/B)
> nhưng M-GRID thử nghiệm chỉ nên chạy trên A thật. Pool có vài cặp file trùng nội dung
> khác tên (bản editor đặt tên Việt) — chuyện cũ của pool, không thuộc gói này.
>
> **✅ CHỐT ngưỡng (Claude tự chốt theo ủy quyền user 2026-07-13 "tính toán cẩn thận
> mọi biến, tự chốt"):** giữ **B≥1.3**, nâng **A≥2.2**. Căn cứ: dải 2.0-2.2 của pool =
> ambient tên tay + dreamy nhẹ (không nên grid-cut); dải 2.2-2.5 = tense/mysterious có
> nhịp thật. Chi phí sai lệch bất đối xứng: ambient-lọt-A hại M-GRID/neo-downbeat,
> nhịp-thật-rơi-B chỉ mất downbeat (accent của nhạc có nhịp vốn nằm trên beat mạnh).
> Tier C giữ 1.3 vì B chỉ dùng accent (= swell thật trên ambient, min-gap 1s tự giới
> hạn) và không bài nào accent <1.5/phút — snap có trần 15% tự bảo vệ.

## 6. 📌 LỆCH SO VỚI BẢN GỐC

- **§2 "tự chạy khi nạp nhạc editor (editor-learn/staging)" — KHÔNG code riêng (chốt
  2026-07-13, M0):** nhạc staging `music_editor/<draft>/` chưa có index và chưa vào phễu
  chọn; bài CHỈ trở thành chọn-được khi vào pool qua `music-import` — mà import nay LUÔN
  đo grid (kể cả record cũ thiếu grid tự nâng cấp). Luật "mọi bài nhạc mới đều phải có
  grid" vẫn kín ở đúng cái cổng duy nhất có người tiêu thụ; đo ở staging là đo mồ côi.
