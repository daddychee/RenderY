# MÔ TẢ VẬN HÀNH — C8 GÓI NẠP: nạp footage viral theo luật bản quyền

> Trạng thái: ✅ user DUYỆT + CODE XONG 2026-07-08 (pytest 291/291, mẻ thử Destiny 45 cảnh
> lỗi 0 — NHAT_KY §C8-NAP) — ⏸ cổng mắt user: kiểm clip zoom/logo trước khi nạp full 9 draft.
> Luật gốc: `foundation/c8-cat-nguon-viral.md`
> (5+1 luật, user chốt 2026-07-08). Đây là gói 1/2 — gói NẠP (nướng luật vào clip lúc nạp).
> Gói 2 (CHỌN: gate liền kề + trần 8% + điểm rải) viết mô tả riêng TRƯỚC lần dựng đầu dùng viral.

---

## 0. Input thật — 9 draft tách cảnh user làm 2026-07-08 (`E:\CapCut Drafts`)

| Draft | Nguồn (1 file/draft) | Cảnh | <2s (bỏ) | 2–6s | 6–10s | >10s (bóp 6s) |
|---|---|---|---|---|---|---|
| Anomalies of the Milky Way | 135,0 phút | 123 | 1 | 24 | 46 | 52 |
| Astrum - Pluto | 31,0 phút | 160 | 5 | 59 | 55 | 41 |
| Astrum - Deepest Sun | 19,0 phút | 116 | 3 | 50 | 42 | 21 |
| Astrum Extra - Jupiter | 113,4 phút | 173 | 5 | 65 | 58 | 45 |
| Destiny - Solar System | 12,1 phút | 143 | 46 | 72 | 19 | 6 |
| Hubble Something Huge | 20,8 phút | 136 | 4 | 82 | 35 | 15 |
| Kosmo - Pluto Photos | 15,9 phút | 88 | 3 | 51 | 23 | 11 |
| NASA - PLUTO | 58,6 phút | 171 | 52 | 82 | 23 | 14 |
| Space Matters - Bigbang | 28,8 phút | 254 | 36 | 105 | 92 | 21 |
| **TỔNG** | | **1364** | **155 (11%)** | **590** | **393** | **226** |

→ sau lọc + bóp: **~1200 clip mới**, toàn bộ ≤10s, ước ~110 phút footage. Kho space: 665 → ~1865 asset.
Vision GLM 1 frame/clip (mọi clip ≤10s): **~$1,2**. File nguồn nằm `F:\SPACE\Niche space viral*\` — draft chỉ ĐỌC.

## 1. Cách chạy (không lệnh mới — thêm cờ vào lệnh cũ)

```
uv run autoedit library-ingest space "E:\CapCut Drafts\<tên draft>" --source-class viral
```

- Không có cờ → `own` như cũ (kho editor công ty). Mọi hành vi cũ giữ nguyên.
- `--dry-run` in trước khối lượng + số cảnh bị bóp/bỏ theo từng luật.

## 2. Delta code (7 điểm — tái dùng ống PB4 `library/ingest.py`, không viết ống mới)

| # | Luật c8 | Làm gì | Áp cho |
|---|---|---|---|
| 1 | Sàn 2s (luật 6) | `MIN_SCENE_S` 1.0 → **2.0** — bỏ TRƯỚC khi cắt/vision; đếm + in số bỏ (đã có `stats.too_short`, không bỏ âm thầm) | **MỌI mẻ nạp** (user chốt) |
| 2 | ≤10s, chuẩn 6s (luật 1) | Cảnh >10s → **bóp còn 6s KHÚC GIỮA** (start dịch (dur−6)/2). Cảnh 2–10s giữ nguyên (dưới trần user cho). `scene_start` ghi db = start ĐÃ dịch (đúng sự thật clip) | chỉ `viral` |
| 3 | Zoom mất logo (luật 4) | ffmpeg **crop tâm ~112% + scale về cỡ gốc, NƯỚNG CHẾT vào clip** (không làm ở assembler — clip trong kho phải sạch sẵn). Vision tag SAU zoom → tag đúng hình dùng thật | chỉ `viral` |
| 4 | Tách âm (luật 2) | ✅ đã có sẵn — `-an` trong `cut_scene` từ PB4 | mọi mẻ |
| 5 | Nhãn nguồn gốc | db thêm 2 cột (ALTER idempotent): `source_class TEXT DEFAULT 'own'` + `source_duration REAL` (tổng giây file nguồn — mẫu số trần 8% cho gói CHỌN). 665 asset cũ tự = `own` nhờ default, 0 dòng migrate | schema chung |
| 6 | **Fail-safe c8** | 4 hàm đọc kho thêm `AND source_class != 'viral'`: `search_assets` (phễu local) · `videos_for_niche` (pool shot thở) · `signature_assets` · `vocab_for_niche` (khối TỪ VỰNG KHO — không dạy NÃO viết query trúng asset chưa dùng được). Gỡ ở 3 hàm pool KHI gói CHỌN xong | tới khi có gói CHỌN |
| 7 | Chống lật nhãn | `upsert_asset` CASE-preserve thêm `source_class`/`source_duration` — re-index thường (index_niche quét folder) KHÔNG được đè viral→own âm thầm | schema chung |

Luật 3 (cấm 2 cảnh liền kề) + luật 5 (trần 8% + điểm rải) = gói CHỌN — dữ liệu đã đủ từ gói này
(`source_video` + `scene_index` + `source_duration`), không cần nạp lại.

## 3. Rà chồng chéo (P5 — "đụng ai?")

| Tầng | Đụng? | Kết luận |
|---|---|---|
| DNA pacing (`read_timeline`) | Không — đọc MỌI segment kể cả cảnh bị bỏ | Sàn 2s không lệch DNA. **Cấm đưa 9 draft viral vào `library-dna`** (nhịp tách cảnh ≠ nhịp dựng editor) |
| Thống kê kho trong `dna.py` (scene_type/shot_size toàn niche) | Có — viral vào sẽ trộn phân bố | Thêm cùng filter fail-safe cho nhất quán |
| TỪ VỰNG KHO (C4) → NÃO | Có — nếu in từ viral mà phễu chặn → NÃO viết query trúng asset không dùng được | Đã chặn ở delta #6 (`vocab_for_niche`) |
| `index_niche` re-scan folder `nap/` | **Nguy hiểm nhất** — upsert default `own` sẽ LẬT nhãn viral âm thầm → lách gate pháp lý | Đã chặn ở delta #7 (CASE-preserve) |
| filter-overload-guard (2 veto) | Không — fail-safe là loại tạm thời theo class, gate cuối là PHÁP LÝ (cùng loại geo-gate), không phải veto chất lượng thứ 3 | Nguyên vẹn |
| Asset cũ 1–2s đã trong db (nạp sàn 1s trước đây) | Không đụng — sàn 2s chỉ áp mẻ MỚI, không purge db | Giữ nguyên |
| Tên clip deterministic / resume | Không — bóp 6s đổi (start,dur) → tên phản ánh khúc đã bóp, dedup/resume vẫn đúng | OK |

**Cạm bẫy ghi sổ:** 1 nguồn = 1 draft tách cảnh. Nếu sau này tách 1 video nguồn thành 2 draft,
`scene_index` đánh lại từ 1 → gate liền kề (gói CHỌN) mù ranh giới giữa 2 draft.

## 4. Mẻ thử + cổng (P4)

1. pytest: sàn 2s, bóp 6s giữa, zoom kích thước ra, fail-safe 4 hàm, CASE-preserve nhãn (+ full suite).
2. **Mẻ thử `--limit 12` trên "Destiny - Solar System"** (nhiều cảnh <2s nhất → test sàn tốt nhất).
3. **Cổng mắt user:** mở 3–4 clip trong `space/nap/Destiny...` — logo/chữ nguồn ĐÃ MẤT chưa (112% đủ chưa — chưa đủ thì tăng %)? khúc giữa cắt có tự nhiên không?
4. Đạt → chạy nền full 9 draft (**sau khi SP012 assemble xong** — đỡ tranh ffmpeg/CPU), báo số liệu từng draft.

## 5. Câu hỏi mở

Không — 2 điểm tôi tự chốt, anh phủ quyết được ở cổng mắt: (a) zoom khởi điểm **112%**;
(b) cảnh 6–10s **giữ nguyên độ dài** (dưới trần 10s user cho, không ép hết về 6s).
