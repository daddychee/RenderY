# MÔ TẢ VẬN HÀNH — BOOST: cảnh dạng X khán giả thích (user chốt 2026-07-17)

> Bối cảnh (VD3 audit editor custom prompt): khán giả niche thích xem cảnh dạng X
> (life-in: phụ nữ đẹp; niche khác: động vật, cảnh đẹp...). Editor thật xen kẽ X cả
> bài ở chỗ khéo (đúng bối cảnh quốc gia đoạn đang nói), ĐẶC BIỆT đổ X vào đoạn khó
> kiếm footage, và né Pexels — ưu tiên nguồn khán giả thích (kho viral/mẫu đã nạp).
> User chốt 3 điểm 2026-07-17: khai 2 tầng (per-video + niche) · cùng bonus 1,0 ·
> term tiếng Anh theo từ vựng tag kho.

## 1. Khai báo — NGƯỜI khai, máy không suy

**2 nguồn, cùng cú pháp `X@scope`** (scope: `all` mặc định | `hook` | `ch<N>`; X =
tiếng Anh theo từ vựng tag kho — xem khối TỪ VỰNG KHO / `library-vocab`):

```
# per-video (dính vào project.json::inputs.boosts như --ref):
uv run autoedit source <project_dir> --boost "beautiful woman" --boost "aurora@hook"

# per-niche (mọi video của niche tự ăn): niche_profile.yaml
audience_bias:
  - beautiful woman
```
- `audience_bias` là field Stage-4 có sẵn nhưng chưa nối dây — gói này nối. Dòng
  bắt đầu `TODO` (scaffold) bị lọc.
- Merge 2 nguồn TRONG `run_source` (chokepoint duy nhất — chống bug B2 quên-consumer:
  `run` gọi thẳng run_source không qua CLI source).
- Scope lạ → coi như `all` + warning (không im lặng bỏ).
- ⚠ Khai `--boost` SAU khi direct đã chạy: NÃO viết concept chưa biết X — tầng chèn
  +bonus vẫn ăn, muốn trọn vẹn chạy lại direct (CLI tự nhắc).

## 2. Tác dụng (đều là CHÈN hoặc ĐIỂM — không đẻ cửa loại, luật filter-overload-guard)

| # | Tầng | Cơ chế | Code |
|---|---|---|---|
| 1 | THU | **Chèn pool**: ≤6 cảnh KHO match X (`BOOST_INJECT_CAP`, AND-match term qua search_assets), CHỈ beat trong scope; xếp sau ref, trước Pexels. 3 cửa y find_local/find_ref: file tồn tại + geo-gate PA2 + loại đã-dùng TRƯỚC limit. | `sourcer/local.py::find_boost_candidates` |
| 2 | CHỌN | **`BOOST_BONUS = 1.0`** 🔸 vào điểm máy; nhãn `is_boost` gắn 1 CHỖ DUY NHẤT tại chokepoint sau dedup (khuôn is_ref — vết PB7 nhãn rơi), **CHỈ ứng viên kho local** (cảnh X kho đè cảnh X Pexels — editor thật né Pexels). CỘNG DỒN với REF_BONUS. | `ranker/funnel.py::_diem_may` + `runner.py::_gather_candidates` |
| 3 | SÀN | Sàn niche (`_floor_pick` — đúng nghĩa đen "đoạn không kiếm được footage"): cảnh match X sort lên ĐẦU nấc vét, thắng cả ưu-tiên-không-người. | `sourcer/runner.py::_floor_pick` |
| 4 | ĐO | Warning cuối source: `BOOST tầng ĐO: n/N beat lead match...` + `ShotPick/ExtraShot.boost_hit` vào project.json — editor kiểm X có vào bài thật; số 🔸 chỉnh theo đây. | `runner.py::run_source` |
| 5 | NÃO | ✅ M2 (2026-07-17): `boost_block` — khối **SỞ THÍCH KHÁN GIẢ** vào direct_context (đường sâu) + `library_context` pass-2 (đường cũ, khuôn D2 — cùng 1 hàm, không có nguồn luật thứ 2); 4 luật: đan X vào hook/beat chêm/generic · NEO bối cảnh chương ('woman walking parisian street' khi chương nói Pháp) · KHÔNG ép vào beat có thực thể phải kể · query theo TỪ VỰNG KHO. `--boost` thêm trên lệnh `direct-context` (= đúng thời điểm khai, trước NÃO chạy). KHÔNG đụng prompts.py (luật đường-sâu-mù-prompts). SKILL /dung-video dạy khai từ PHA 1 bước 3. | `director/live.py::boost_block` + `director/runner.py` + `cli.py::direct-context` |

**Vì sao scope mặc định `all` mà không tràn X:** bonus 1,0 THUA 1 điểm nghĩa (3,0) —
beat nghĩa mạnh giữ footage đúng nghĩa; beat generic/trống (ứng viên ngang nghĩa) thì
X thắng → X tự dồn vào đúng chỗ khó kiếm footage, khớp hành vi editor thật.

## 3. Rà chồng chéo (P5 — làm TRƯỚC khi code, 2026-07-17)

- **Veto nghĩa c2 / world-lock / bán-thuốc:** ĐƯỢC PHÉP lật boost (nghĩa trên hết).
  Deepsea boost "woman" → veto giết, tầng ĐO báo 0 hit — editor tự thấy, không sửa luật.
- **Ledger C8:** chèn boost bọc `ledger.gate` y chèn REF (chèn ≠ miễn pháp lý); boost
  KHÔNG nới trần 8%/15%; re-check tại pick giữ nguyên. Có test hồi quy.
- **Geo-gate PA2:** `find_boost_candidates` lọc `passes_geo` y find_local/find_ref —
  phụ nữ phố Tokyo không vào bài Pháp (vết bug "video Hà Nội ra cảnh Hà Giang"). Có test.
- **Batch PA-1/TOC-2:** scope tính PER-BEAT tại cả 2 call site (khuôn `sig_first`) —
  KHÔNG qua ctx, né staleness lookahead.
- **Nhãn rơi theo dedup (vết PB7/REF):** is_boost gắn tại chokepoint SAU dedup;
  `_row_to_candidate` mang thêm cột `tags` để match. Có test tái hiện.
- **signature_first hook:** boost xếp SAU signature + local — không ngược chiều.
- **Bất biến `MACHINE_MAX_SPREAD < NGHIA_W`:** BOOST đứng NGOÀI spread như REF (bonus
  Ý ĐỒ EDITOR ≠ điểm máy trung tính). Trade-off user CHẤP NHẬN 2026-07-17: cảnh
  ref+boost+peak+máy (4,5) lật được chênh 1 điểm nghĩa TẠI scope editor đã tuyên bố
  muốn X; chênh 2 điểm nghĩa không lật nổi.
- **TOC-3b warm-up:** dự đoán tải thiếu điểm boost — trượt chỉ phí 1 file, PICK THẬT
  không đổi (y REF).
- **Đường heuristic (không NÃO):** chèn ăn, bonus không (funnel không chạy) — y REF.
- **Shot thở / ambient / SFX / nhạc / P7:** không đụng.

## 4. Kiểm chứng

- 9 pytest M1 (`tests/test_sourcer.py` khối BOOST): parse scope + per-beat scope +
  geo/used/kho-only + nhãn chokepoint sống dedup & Pexels không ăn + cộng dồn REF +
  chèn khi query trượt + ledger gate + heuristic boost_hit + sàn ưu tiên X +
  audience_bias TODO-filter fail-open.
- 2 pytest M2 (`tests/test_director_live.py`): khối SỞ THÍCH fail-open (inputs.boosts
  per-video + audience_bias YAML + scope hiển thị đúng + đứng trước OUTPUT) + đường
  cũ dùng chung boost_block (D2).
- FULL suite M1 570/570 → M2 **572/572** (parity PG thật) 2026-07-17.
- 🔄 Cổng số thật: chạy 1 bài life-in với `--boost "beautiful woman"` → nhìn dòng
  BOOST tầng ĐO + video kiểm mắt.

## 5. Số 🔸 (chỉnh khi có bằng chứng từ tầng ĐO)

`BOOST_BONUS = 1.0` · `BOOST_INJECT_CAP = 6` · chưa có trần mật độ X (cố ý — thêm
trần = thêm cửa loại; nhìn số ĐO vài bài rồi quyết)

## 6. Còn ngỏ

- **Video số đo thật**: 1 bài life-in `--boost "beautiful woman"` (khai tại
  direct-context) → nhìn dòng BOOST tầng ĐO + cổng mắt.
- **Trừ điểm toàn cục Pexels** — backlog user chốt, memory `pexels-tru-diem-toan-cuc-backlog`.
- report.html chưa hiện cột ⭐X theo beat (boost_hit đã nằm trong project.json).
