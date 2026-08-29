# MÔ TẢ VẬN HÀNH — C ĐỢT 1: C6 drop-list · C3 so màu cảnh báo · C7 lệnh pause-dna

> User duyệt hướng 2026-07-09 (chat tư vấn): C6 chốt "Cách 1 — Drop-list" · C3 duyệt
> chỉ-cảnh-báo · C7 đồng ý đề xuất. Thứ tự code: **C6 → C3 → C7**, mỗi mục FULL pytest
> + commit mốc. Cổng mắt chung: **1 video kiểm = voice SP012 cắt 10 phút đầu** (cùng
> input với draft `SCRIPT_20260709_071612` của V123 → so trực tiếp được khác biệt).

---

## C6 — DROP-LIST từ chuyển động khi AND-match kho local (fix PB8)

**Vấn đề (đo 2026-07-07, `PB8_KHOP_QUERY_TAG.txt`):** GLM tag từ 1–2 frame TĨNH nên kho
KHÔNG BAO GIỜ có tag chuyển động; query mang từ chuyển động AND-trượt oan: `spiral galaxy
rotating` = 0 khớp dù kho có 39 clip spiral galaxy; `stars timelapse` = 0 dù 170 clip stars.

**Thiết kế:**
- `sourcer/local.py`: hằng `_MOTION_PHRASES` (cụm: "zoom in/out", "slow motion", "time
  lapse", "fly through/over"...) + `_MOTION_WORDS` (từ đơn: rotating, spinning, orbiting,
  swirling, timelapse, hyperlapse, zoom(ing), panning, drifting, floating, flyover,
  flythrough, pulsing, flickering...) — CHỈ từ camera/chuyển động thời gian, KHÔNG đụng
  từ sự kiện có nghĩa (explosion, eruption... vẫn giữ).
- Hàm `_strip_motion_terms(q)`: bỏ cụm trước, từ đơn sau; **bỏ hết sạch token → giữ
  nguyên query gốc** (không match bừa). Áp trong `find_local_candidates` cho cả 2 tier
  local + specific trước khi gọi `db.search_assets`.
- `db.search_assets` GIỮ NGUYÊN (lệnh debug `library-search` cần thấy hành vi thô).

**Rà chồng chéo (P5):**
- Caller `search_assets`: chỉ `find_local_candidates` (pipeline — gồm cả viral vào phễu)
  + `library-search` (debug, giữ thô) + tests. Viral: gate pháp lý `ViralLedger` chạy SAU
  find_local_candidates → drop-list chỉ đưa thêm ứng viên vào trước gate, không lách luật.
- Tầng cùng quản query: khối TỪ VỰNG KHO C4 dạy NÃO viết queries.local theo vocab thật.
  **KHÔNG sửa prompt kèm theo** (tránh 2-tầng-cùng-quản — luật DNA Mảnh A §6b); máy lo
  1 chỗ deterministic. Ngược chiều? Không — drop-list chỉ TĂNG recall, phễu c5 vẫn là
  trọng tài, geo-gate PA2 + veto nghĩa vẫn gác từng ứng viên.
- Rủi ro chấp nhận: query sau khi bỏ từ thành rộng hơn ("universe zoom out"→"universe")
  → ứng viên generic vào pool, nhưng limit 5/query + NÃO chấm nghĩa xử tiếp.

**Cổng kiểm:** pytest (bỏ từ đơn/cụm; bỏ sạch → giữ nguyên; query không dính → no-op;
integration: asset "spiral galaxy" khớp query "spiral galaxy rotating") + **re-run
benchmark 24 query PB8 trên db thật**: 3 query trượt-oan phải >0; 5 query kho-thật-thiếu
phải VẪN = 0; 16 query cũ không đổi. Kết quả ghi bổ sung vào `PB8_KHOP_QUERY_TAG.txt`.

---

## C3 — So màu nội bộ chương, CHỈ CẢNH BÁO (b1 backlog #2)

**Vấn đề (foundation b1 §4):** 1 footage lệch màu giết cả đoạn — lỗi là LỆCH TƯƠNG ĐỐI
so với xung quanh, không phải footage xấu. 2 ví dụ user: clip sáng lọt đoạn u ám; clip
vintage lọt đoạn colorful.

**Thiết kế:**
- Module mới `sourcer/colorcheck.py`:
  - Đo màu footage ĐÃ CHỌN: local/viral/pexels/entity đều đo trực tiếp từ file trong
    `assets/` bằng `preview_images` + `measure_colors` có sẵn (PIL/ffmpeg thuần, 0 token)
    → (V sáng, S bão hòa, H hue). Đo 1 điều kiện thống nhất — không trộn số đo cũ trong db.
  - Bỏ qua asset mình render: chart (`chart:*`), chart PiP, info-card; bỏ pick không file.
  - Phạm vi so: shots + extra_shots + breath_shots, gom theo **chương** (beat.chapter).
    Chương <3 footage đo được → bỏ qua (không đủ "xung quanh" để so).
  - Luật outlier — 2 điều kiện ĐỒNG THỜI (chỉnh sau khi đo thật 110 footage V123:
    chỉ ngưỡng tuyệt đối → 53 cảnh báo oan vì space vốn xen kẽ xám/rực tự nhiên):
    (1) lệch tuyệt đối so TRUNG VỊ chương: |ΔV| ≥ 0,25 · |ΔS| ≥ 0,30;
    (2) lệch bất thường so ĐỘ TẢN tự nhiên của chương: robust z = |Δ|/MAD ≥ 3,5
    (MAD floor 0,02) — chương đa dạng tự nhiên thì im, chương đồng nhất mà 1 clip
    bật hẳn thì bắn đúng nó (đúng chữ b1 "lệch TƯƠNG ĐỐI so với xung quanh").
    Hue: lệch ≥ 60° so tông chủ đạo tính LEAVE-ONE-OUT từ các footage đủ màu khác
    (S màu chủ đạo ≥ 0,25; outlier không tự kéo tụt độ tập trung tông để thoát);
    chương không có tông chủ đạo (vector hue tản mác, R < 0,5) → bỏ xét hue.
    Đo lại V123 sau chỉnh: 8 cảnh báo / 110 footage — mức editor soi được.
- Gọi cuối `run_source` (sau breath_shots), bọc try/except **fail-open**: lỗi đo màu
  KHÔNG BAO GIỜ giết stage source — chỉ thêm warning "so màu C3 lỗi... bỏ qua".
- Output: dòng warning/outlier trong `record.warnings` (report + CLI hiển thị sẵn):
  `so màu C3 (chương N): bXXX <file> sáng hơn hẳn chương (0.82, trung vị 0.35) — soi lại`
  + 1 dòng tổng `so màu C3: đo N footage / M chương — K cảnh báo`.

**Rà chồng chéo (P5):** mood/màu hiện 3 tầng cùng quản (NÃO gán mood beat → phễu c5 chấm
tag mood → C5 vision gate tương lai). C3 **không quyết gì, không đổi điểm/pick** → không
ngược chiều tầng nào, không tầng nào lật được nó. Đường lên quyền trừ điểm để C đợt 5
(C2b/C5) sau khi có số thật từ video kiểm. Chạy SAU mọi pick → không đụng P7/ledger/usage.

**Cổng kiểm:** pytest thuần số (fixture V/S/H giả: bắt đúng outlier sáng/bão hòa/hue;
chương đồng màu → im; <3 footage → bỏ qua) + chạy standalone trên project
`script-20260709-071612` có sẵn xem cảnh báo có trỏ đúng chỗ. Cổng mắt: video kiểm —
user đối chiếu cảnh báo với mắt thật (cảnh báo nào trúng/oan → chỉnh ngưỡng).

---

## C7 — Đóng gói scan pause-DNA thành lệnh `autoedit pause-dna`

**Bối cảnh:** `learn_pause_dna.py` (scratch phiên 2026-07-08, đã cứu về project root)
sinh `pause_dna.json` mà `load_pause_dna`/`load_breath_dna` đang đọc — nhưng là script
1 lần, hardcode 3 project SP1, và CHƯA sinh block `pooled.breath` (block đó tay chỉnh).
Cache transcript 16 file đã cứu về `F:\AutoEdit\library\space\pause_scan_cache\`.

**Thiết kế:**
- Module mới `library/pause_scan.py` (adapt từ script): `scan_draft(draft_dir,
  script_text, get_words)` (words injectable cho test) + `compute_pause_dna(per_draft)`
  + `save_pause_dna(...)`. Logic rows/holes/reconcile-script giữ NGUYÊN thuật toán cũ
  (regression khớp số).
- **Vá 3 bài học §6.2C** khi tính block breath (phần MỚI so với script):
  1. KHÔNG lọc phăng ô ≥8s — **montage** = ≥4 nhát cắt trong ô HOẶC ô >20s → loại khỏi
     lớp thở, đếm riêng;
  2. **Tách lớp**: hold (nhát cắt đầu sau hết voice) ≤1,2s VÀ footage = dur−hold ≥1,5s
     = lớp hình thở; ô không nhát cắt = voice-nghỉ (passive), không vào lớp thở;
  3. Xuất `pooled.breath` ĐO ĐƯỢC: `footage_anchors` (p10–p90, cần ≥5 ô), `hold` (p50),
     `footage_cap` (max đo, làm tròn 0,5). **Các khóa chính-sách (k_thresholds,
     k_fractions, min_piece) KHÔNG xuất** — loader tự fallback hằng space (luật k đang
     "nửa DNA nửa interview", 3 điểm dữ liệu). Kèm `pooled.breath_measured`: phân bố k
     + quantiles đầy đủ để NGƯỜI xem quyết nâng cấp luật k (backlog §6.5 "đo phân bố k").
- CLI `pause-dna <niche> --draft <folder>... --script <txt>... [--language en] [--force]`
  (mẫu library-dna; draft/script ghép theo thứ tự; thiếu script → phân loại whisper-only
  + cảnh báo). Transcript cache bền: `<library>\<niche>\pause_scan_cache\`. Rows chi tiết
  ghi cùng chỗ cache. Help ghi rõ: **CẤM draft viral** (nhịp tách cảnh ≠ nhịp dựng — c8).
- **Guard không đè bản duyệt:** `pause_dna.json` niche ĐÃ tồn tại + không `--force` →
  ghi `pause_dna.new.json` cạnh bên + hướng dẫn so sánh; `--force` → backup
  `pause_dna.backup-<ngày>.json` rồi mới đè. (Block breath space đang là bản user duyệt
  tay chỉnh — máy không được lặng lẽ thay.)

**Rà chồng chéo (P5):** tool offline, không đụng pipeline dựng. Consumer duy nhất =
`load_pause_dna`/`load_breath_dna` (fail-open) → rủi ro là file sai schema RƠI VỀ hằng
IM LẶNG → test round-trip: save xong load phải ra đúng số. Guard-không-đè xử xung đột
với bản space đã duyệt. `library-dna` (dna.json) là file KHÁC, không đụng.

**Cổng kiểm:** pytest (draft giả + words giả: phân loại kind + reconcile script; montage
loại đúng; tách lớp thở đúng; round-trip save→load; guard không đè) + **regression số
thật**: chạy lệnh trên đúng 3 draft SP1 (cache transcript có sẵn, không tốn transcribe)
→ `pooled.kinds` phải khớp `pause_dna.json` hiện hành.

---

## Cổng chung sau 3 mục

1. FULL pytest sau từng mục + commit mốc git local (D5).
2. **Video kiểm** (user chốt): voice SP012 10 phút đầu, cùng input draft V123 →
   cổng mắt user soi: (a) local hit có tăng nhờ C6 không (xem dòng local-first C4),
   (b) cảnh báo C3 trúng hay oan. Claude KHÔNG tự phán đạt.
3. Đạt cổng mắt → C đợt 1 ĐÓNG → sang C đợt 2 (C4 tone + D3 nới local limit).
