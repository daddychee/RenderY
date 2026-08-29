# MÔ TẢ VẬN HÀNH — C8 GÓI CHỌN: gate pháp lý khi phễu chọn footage viral

> Trạng thái: user duyệt trước 2026-07-09 ("duyệt các đề xuất khác... thử dựng luôn video
> đầu tiên có dùng viral") → viết + code cùng lượt, cổng mắt = video dựng thử.
> Luật gốc: `foundation/c8-cat-nguon-viral.md` (luật 3 + 5). Gói 2/2 — sau gói NẠP (§C8-NAP).

## 1. Cái gì mở ra

Gỡ fail-safe `_NO_VIRAL` → 1209 asset viral vào phễu, ĐI QUA 2 gate pháp lý mới + 1 điểm rải:

| # | Luật | Gate | Cơ chế |
|---|---|---|---|
| 1 | Luật 3 — cấm 2 cảnh liền kề 1 nguồn trong 1 video mình, DÙ ĐẶT XA NHAU | **CỨNG** | `ViralLedger.blocks`: ứng viên viral có `scene_index ± 1` (cùng `source_video`) đã được pick ở BẤT KỲ beat nào → loại |
| 2 | Luật 5 — trần 8% thời lượng nguồn | **CỨNG** | cộng dồn TRỌN duration clip mỗi lần pick (đếm bảo thủ — clip chỉ chiếu 1 phần vẫn tính trọn); vượt `8% × source_duration` → loại. Thiếu `source_duration` → loại luôn (fail-safe mẫu số) |
| 3 | Luật 5 — ưu tiên rải nhiều nguồn | mềm | sort ổn định ứng viên viral theo giây-đã-lấy của nguồn (ít dùng lên trước) — KHÔNG phải cửa loại, NÃO vẫn chấm bình thường |

**`ViralLedger`** (module `sourcer/viral.py`): trạng thái theo 1 lần dựng — `{source_video:
scene_index đã dùng}` + `{source_video: giây đã lấy}`. Sống trọn `run_source` (source chạy
lại từ đầu mỗi lần → không cần persist).

## 2. Gate đặt ở ĐÂU (3 chỗ chạm + 1 chỗ đóng)

1. **THU (`_gather_candidates`)**: lọc `local_cands` viral bị blocks + sort rải — như geo-gate PA2.
2. **PICK (`_pick_by_funnel` vòng tải + đường heuristic)**: RE-CHECK trước khi tải — bắt
   ca PA-1 batch gather 10 beat MỘT LẦN rồi beat trước trong chunk pick mất cảnh hàng xóm
   (gather-time sạch nhưng pick-time đã phạm). Pick xong → `ledger.add`.
3. **`_row_to_candidate`** mang thêm 4 field: `source_class/source_video/scene_index/source_duration`.
4. **Shot thở: ĐÓNG với viral (quyết định ủy quyền #1)** — pool `videos_for_niche` sort
   mới-nhất-trước, 1209 clip viral vừa nạp sẽ CHIẾM GẦN TRỌN pool 500 → shot thở thành toàn
   viral 480p, lật hành vi shot thở 2.0 đã duyệt. Giữ `_NO_VIRAL` ở riêng hàm này; viral chỉ
   tranh ở beat thoại. (Hệ quả tốt: trần 8% chỉ cần cộng dồn ở phễu — mọi đường MỞ đều qua ledger.)

Gỡ `_NO_VIRAL` ở: `search_assets` (phễu local) · `vocab_for_niche` (TỪ VỰNG KHO — NÃO được
học từ vựng viral vì giờ dùng được) · `signature_assets` (viral không bao giờ category
signature — gỡ cho sạch) · thống kê kho `dna.py`.

## 3. Rà chồng chéo (P5)

| Tầng | Kết luận |
|---|---|
| filter-overload-guard (2 veto) | 2 gate cứng = PHÁP LÝ cùng loại geo-gate PA2, không phải veto chất lượng thứ 3; điểm rải là sort không phải cửa loại — nguyên vẹn |
| P7 `used_in_video` | không đổi — ledger là lớp RIÊNG chồng lên |
| PA-1 batch gather-trước-pick-sau | chính là lý do phải RE-CHECK ở vòng tải (chỗ chạm 2) |
| `_source_graphic` nền lót | không đụng — bg chỉ search tier thematic, local cần tier local/specific → viral không vào đường này |
| TỪ VỰNG KHO (C4) đổi nội dung | kho 665→1874, khối từ vựng in cho NÃO đổi theo — ĐÚNG chủ đích (NÃO viết query trúng kho viral) |
| Pexels fallback | beat bị gate chặn hết viral vẫn còn Pexels — không tăng needs_human |
| search_assets sort mới-nhất-trước | viral (nạp mới) nổi lên đầu THU local — chấp nhận v1, NÃO vẫn chấm; nếu cổng mắt thấy viral đè own → thêm ưu tiên own sau |

## 4. Cổng

- pytest: ledger (liền kề xa-nhau-vẫn-cấm · trần 8% cộng dồn · thiếu mẫu số · own miễn) ·
  THU lọc + re-check pick · shot thở vẫn 0 viral · test fail-safe cũ VIẾT LẠI theo hành vi mới.
- **Cổng mắt = video dựng thử** (SP012 re-source + assemble, draft tên mới): user xem viral
  được dùng ra sao + report đếm viral pick/nguồn.
