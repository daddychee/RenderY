# MÔ TẢ VẬN HÀNH — C4 TỪ VỰNG KHO (controlled vocabulary: query local nói đúng ngôn ngữ tag)

> Trạng thái: ✅ user DUYỆT 2026-07-08 → **M1 CODE XONG** (pytest 285/285) →
> **M2 CỔNG SỐ ĐẠT cùng ngày** (same-input, same-beats: local vào pool 15→45 beat (3×) ·
> ứng viên 44→178 (4×) · thắng 9→15 · needs_human 0 — chi tiết NHAT_KY §C4) →
> draft `SCRIPT_VOICE_20260708_070124`. ⏸ Còn M3 cổng mắt user.
> Nguồn nguyên tắc: `foundation/c4-tu-khoa-tim.md` (phần 3b/5 đã ghi sẵn việc này, treo chờ
> schema tag chốt — nay tag GLM đã chạy production 665 asset, đủ điều kiện mở).
> Đọc kèm: `PB8_KHOP_QUERY_TAG.txt` (số đo) · `MO_TA_VAN_HANH_PHEU_C5.md` §4 (khoảng trống đã hoãn).

---

## 1. Vì sao làm — bằng chứng

Kho local là nguồn CHÍNH theo định hướng ([[footage-source-local-first]]), nhưng run thật
SPACE-E2E cho thấy nó gần như **vô hình ở bước THU**:

| Số đo (SPACE-E2E, 112 beat) | Giá trị | Đọc |
|---|---|---|
| Ứng viên THU được | local **44** vs Pexels **1685** | kho 665 asset mà chỉ đóng góp 2,5% pool |
| Beat có local lọt pool | 15/112 (13%) | phần lớn beat không thấy kho |
| Local THẮNG khi lọt pool | 9/15 (**60%**) | phễu KHÔNG chê kho — cứ lọt là thắng quá nửa |

→ Nút thắt là **THU**, không phải phễu. PB8 đo nguyên nhân: 24 query giả lập chỉ trúng 16;
8 trượt = (a) kho thật sự thiếu cảnh (Pexels đúng vai trò vớt) + (b) **trượt oan** vì query
viết bằng "ngôn ngữ Pexels": từ chuyển động ("rotating"/"timelapse") làm AND-match trượt
trong khi kho có 39–170 clip đúng cảnh — GLM tag từ frame TĨNH, không bao giờ có từ chuyển động.

Gốc rễ (foundation c4 đã gọi tên): **hai kho nói hai ngôn ngữ, nhưng local đang "ké" bộ query
viết cho Pexels**, và NÃO viết query mà **không hề biết kho nói những từ gì**.

## 2. Thiết kế — 3 mảnh (0 call NÃO thêm, 0 tầng lọc mới)

### Mảnh 1 (ỐNG) — direct_context.md chở TỪ VỰNG KHO

`library/db.py` thêm hàm thuần `vocab_for_niche(conn, niche)` — 1 query SQL + Counter:
- phân bố `scene_type` (kèm số đếm) → NÃO biết kho phủ vùng cảnh nào;
- top ~30 `tags` + top ~30 từ trong `subject` (kèm số đếm, bỏ stopword in/with/a...) →
  NÃO biết từ nào TRÚNG là có hàng, từ nào viết ra cũng công cốc;
- tổng số asset video/ảnh.

`director/live.py::build_direct_context` thêm khối **"TỪ VỰNG KHO LOCAL (niche X)"** in bảng
trên + 3 lời dặn (mã hóa bài học PB8):
1. Query local = 2–4 **DANH TỪ cảnh** lấy từ bảng này; KHÔNG động từ chuyển động
   (rotating/timelapse/zoom) — tag chụp từ frame tĩnh.
2. Kho không phủ concept → **để local RỖNG**, Pexels lo — đừng sáng tác query cứu (cạm bẫy c4).
3. Từ đếm càng dày càng chắc ăn (galaxy×157 ≠ planet×11).

Fail-open: không có niche / db rỗng → bỏ khối, context y như cũ. Niche lấy từ
`project.inputs.channel` (skill đã truyền `--channel "<niche>"` khi `new`), cho phép
`--niche` ghi đè.

### Mảnh 2 (NÃO + schema) — tách `queries.local` khỏi `queries.specific`

Foundation c4 phần 3 đã treo đúng câu hỏi này ("có tách queries.local không — đổi schema Beat
là việc của gói phễu/L2b sâu"). **Chốt: TÁCH.** Lý do: specific đang phục vụ 2 chủ nhân kéo
2 hướng — phải chở địa danh + shot modifier cho Pexels, đồng thời phải trúng vocabulary tag
cho local. Gộp thì mỗi lần chỉ chiều được 1 bên (SPACE-E2E là bằng chứng bên local bị bỏ đói).

- `project.py::SearchQueries` + field `local: list[str] = []` (project.json cũ load nguyên —
  default rỗng; coercion legacy hiện có không đụng).
- `director/schema.py::SearchQueriesDraft` + field `local` (description = hướng dẫn LLM:
  0–2 query, mỗi query 2–4 danh từ từ mục TỪ VỰNG KHO; rỗng khi kho không phủ).
- `director/validator.py`: gác `≤ MAX_QUERY_WORDS` từ cho tier local (chung chỗ gác 3 tier
  cũ). KHÔNG gác "từ phải thuộc vocab" — mềm, query trượt thì phễu/Pexels lo
  ([[filter-overload-guard]]: không đẻ cửa loại mới).
- Đường direct cũ (fallback L1) không nhắc field mới → default rỗng → hành vi cũ y nguyên.

### Mảnh 3 (ỐNG) — local.py match tier local + vá bug niche + đo local-hit

- `sourcer/local.py::find_local_candidates`: duyệt `queries.local` TRƯỚC, rồi `queries.specific`
  (giữ nguyên — beat cũ/NÃO quên local vẫn có đường); broad/thematic VẪN CẤM local (bug 20/06).
  Geo-gate PA2 + check file tồn tại áp cho MỌI ứng viên như cũ. `limit` giữ 5 (P2 — đổi 1 biến
  một lần; nếu M2 đo thấy pool local vẫn mỏng mới bàn nâng).
- **Vá bug niche rơi (cùng gói vì cùng dây):** lệnh `source` đứng riêng với niche rỗng →
  local + signature + shot thở **tắt im lặng**; skill `/dung-video` Pha 2 gọi đúng kiểu này
  (SPACE-E2E sống sót vì phiên đó truyền `--niche space` tay). Fix: `source` (và
  `direct-context`) fallback `niche = --niche || project.inputs.channel`; in 1 dòng
  "niche=<x> (từ channel)" để nhìn thấy. Đây là anh em của bug B2 quên-consumer (P5).
- **Đo "đã local-first thật chưa"** (tín hiệu DNA c4 §5): `run_source` đếm
  `beat có local trong pool / tổng beat stock+local` + `local thắng / tổng pick` → ghi
  `record.notes` + hiện trong report.html (ống warnings/notes sẵn có). 0 phí, mỗi run tự báo.

## 3. Phương án đã cân nhắc và LOẠI

| Phương án | Vì sao loại |
|---|---|
| ỐNG lọc bỏ "từ chuyển động" khỏi query trước khi match local (stoplist) | Vá triệu chứng bằng 1 tầng chữa-query nữa — đúng kiểu chồng lọc [[filter-overload-guard]] cảnh báo. Sửa tại nguồn (NÃO biết vocab, không viết từ chuyển động) sạch hơn. Nếu M2 đo thấy vẫn trượt oan nhiều mới xét. |
| Nới AND-match thành OR/chấm-điểm-số-từ-trúng | Nguy hiểm đúng vết bug 20/06: "hanoi old quarter" trúng 2/3 từ vẫn kéo được clip Hà Giang (geo-gate chỉ chặn mức QUỐC GIA, không chặn sai thành phố cùng nước). Foundation c4 cấm rõ: "CHỈ nới qua vocabulary tag có kiểm soát, không qua LIKE generic". |
| Nhét vocab vào prompt đường direct cũ luôn | Đường cũ là fallback, prompt cứng đã dài; L2b sâu là đường chính. Làm khi có nhu cầu thật (P2). |

## 4. RÀ CHỒNG CHÉO (P5 — các tầng cùng quản "query & chọn local")

| Tầng hiện có | Đụng gì | Ngược chiều? / Ai lật ai? |
|---|---|---|
| Foundation c4 (NÃO đọc mỗi phiên) | Mô tả này HIỆN THỰC phần 3b/5 của chính nó | Cùng chiều. Sau khi code xong: cập nhật c4 phần 3 (bỏ nhãn 🔸 DỰ KIẾN mục local) |
| Luật "local CHỈ match tier specific" (bug 20/06) | NỚI CÓ CHỦ ĐÍCH: thêm tier `local` được match | Không tái phạm: tier local do NÃO viết RIÊNG theo vocab (không generic), geo-gate PA2 vẫn gác mọi ứng viên; broad/thematic vẫn cấm |
| Geo-gate PA2 | Không đổi | Vẫn có quyền loại ứng viên từ tier local — đúng vai trò, không phải lật |
| Phễu c5 + PA-BATCH (veto nghĩa, sàn 3, chấm batch) | Không đổi code | THU rộng hơn → phễu vẫn là người KIỂM (đúng cạm bẫy "đừng tin query mù"). Phễu có thể loại local vừa THU thêm — đúng thiết kế, không phải lật |
| PB7 duration + điểm shot_size/mood | Không đổi | Cùng chiều — ứng viên local mới vào phễu mang đủ tag để chấm công bằng |
| P7 used_in_video + usage soft-penalty | Không đổi | Local xuất hiện nhiều hơn → soft-penalty tự cân tái dùng, đúng vai trò |
| Signature c6 / shot thở breath.py | Không đụng (chọn theo tag, không theo query) | Nhưng HƯỞNG LÂY từ vá niche rỗng: skill chạy source không --niche sẽ hết tắt oan shot thở |
| Validator direct-ingest | Thêm gác ≤4 từ tier local | Cùng chiều bảng ràng buộc cứng |
| Đường direct cũ + project.json cũ | Field mới optional default rỗng | Hành vi cũ y nguyên (fail-open) |
| beats_review / report | Rà khi code: chỗ nào in search_queries thì in thêm local | Hiển thị, không logic |

Kết luận rà: 1 luật bị nới CÓ CHỦ ĐÍCH (local-chỉ-specific → thêm tier local có kiểm soát),
0 tầng ngược chiều, 0 tầng có thể lật âm thầm quyết định của tầng mới.

## 5. Milestone + cổng nghiệm thu (P4)

| # | Việc | Cổng |
|---|---|---|
| M1 | Code cả 3 mảnh (db.vocab_for_niche · khối vocab direct-context · schema local + validator · local.py tier local · vá niche fallback · đếm local-hit) | FULL pytest xanh; test mới: vocab đúng đếm/fail-open · context có/không khối · tier local match trước + geo-gate vẫn chạy · project cũ load nguyên · validator ≤4 từ · source fallback channel (regression bug niche rỗng) |
| M2 | Chạy thật SAME-INPUT: direct lại `D:\SPACE 3 - 007` qua phiên sống (context mới có vocab) → source → so baseline SPACE-E2E | **Cổng số:** local lọt pool / local thắng so với 15/112 · 9/112; kỳ vọng tăng RÕ ở beat kho có cảnh (galaxy/nebula/night sky dày); beat kho thiếu (Io volcano...) vẫn Pexels — ĐÚNG. Báo bảng số, user phán |
| M3 | Cổng mắt: user xem draft video M2 (chất lượng local được chọn) | User phán — Claude không tự chấm |

Ghi chú M2: direct lại = subscription (0 phí API), Pexels query trùng đã cache SQLite.
Cùng input → so táo-với-táo với baseline 44/1685 · 9/112.

## 6. Còn ngỏ (ghi trước, không làm trong gói này)

- Vocab đưa NÃO là top-N tần suất — chưa có nhóm đồng nghĩa (concept nói A tag ghi B).
  Bảng map đồng nghĩa = tín hiệu DNA c4 §5, chờ log nhiều run thật.
- `limit=5` ứng viên local/beat — đo M2 rồi mới bàn nâng.
- Prompt đường direct cũ chưa biết vocab (fallback, chấp nhận).
- Kho mới chỉ space; niche 2 (travel?) sẽ kiểm geo-gate + vocab chung sống ra sao.
