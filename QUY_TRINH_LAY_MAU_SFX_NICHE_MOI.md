# QUY TRÌNH LẤY MẪU SFX CHO NICHE MỚI

> Đúc từ đợt deepsea 2026-07-13 (`MO_TA_VAN_HANH_SFX_LOAI.md` + `MO_TA_VAN_HANH_HOOK_SFX.md`
> + `PHAN_TICH_HOOK_SFX_EDITOR_DEEPSEA.md`) và tiền lệ space mượn số 2026-07-14.
> Niche mới (travel, ...) đi đủ B1→B6; đường tắt "mượn số" ở B5b — chỉ khi user chốt.

## 0. Toàn cảnh — 4 tầng SFX per-niche máy đang dựng

| Tầng | Là gì | Số liệu lấy từ đâu |
|---|---|---|
| C1 ambient | tiếng môi trường ô thở (vol 1.0) + nền trong voice (0.32) | kho `F:\AutoEdit\ambient\<niche>` theo scene GLM |
| S1 drone/bed | nền dài (deepsea "ục ục" 0.25, chỉ cảnh dưới nước; space drone 0.15) | editor-learn + cổng tai |
| S2 chủ thể | tiếng theo CHỦ THỂ trên hình trong voice (0.18 = -15dB) | sheet loài editor → `subject_rules.yaml` |
| S3 hook | hit/whoosh/click tại CUT trong hook (0.2 🔸) | **đo draft editor — B4 dưới đây** |

**Trạng thái gate S3 theo niche** (`schedule.py::HOOK_SFX_NICHES`):

| Niche | Gate | Số liệu |
|---|---|---|
| deepsea | ✅ BẬT | đo thật 23 draft (4,8/ph · bám CUT 48% · vol editor 0,56) |
| space | ✅ BẬT 2026-07-14 | 🔸 MƯỢN deepsea (user chốt "2 niche gần giống") — đo riêng thì thay |
| travel / niche mới | ⛔ TẮT | chưa đo — đi quy trình này |

## B1 — Học draft editor (luật đứng có sẵn)

`autoedit editor-learn <draft> --niche <n>` cho MỌI project editor mới vào — COPY-only:
sfx vào staging (người sort), nhạc vào staging `music_editor`, DNA báo-cáo-không-đổi-hằng.
Chi tiết + 4 bẫy: memory `editor-learn-standing-rule`.

## B2 — Sheet chủ thể → `subject_rules.yaml` (tầng S2)

1 sheet editor → 1 yaml trong folder kho niche (THAY TRỌN built-in, không merge).
Bài học precision bắt buộc (`MO_TA_VAN_HANH_SFX_LOAI.md`):
- keyword là **CỤM có ngữ cảnh**, KHÔNG bare word (bare `swirl` từng ăn nhầm "green
  smoke swirling" — khói KHÔNG phải nước);
- trước khi chốt: chạy thử match trên 1 video đã dựng (soi `subject_sfx_log` giả lập)
  → soi tay từng hit mới.

## B3 — Nạp kho ambient per-niche

`scripts\nap_hook_sfx.py` (sửa 3 hằng NICHE/SRC/FOLDER_KIND) hoặc manifest tay
`ambient_manifest.yaml`. Máy tự normalize C4 (WAV PCM 48k) + ghi records
`ambient_library.yaml` (truy license). File gốc editor giữ nguyên.
**KHÔNG nạp `~/AutoEdit/sfx` toàn cục** — kho đó là rotation overlay-SFX MỌI niche,
tiếng vị niche này sẽ lọt video niche khác.

## B4 — ĐO hook editor (READ-ONLY, ~2 phút/20 draft)

```
uv run python "..\scripts\do_hook_editor.py" <niche> "<root draft 1>" ["<root 2>" ...]
```
Cần ≥~15 draft có TCF `topic + chapter video.txt` (thiếu TCF → hook fallback 60s, số nhiễu).
Đọc 4 số, chép vào `PHAN_TICH_HOOK_SFX_EDITOR_<NICHE>.md`:

1. **Mật độ**: SFX/phút hook vs body (deepsea 4,8 vs 1,6 = 3×) → `HOOK_SFX_PM`.
2. **Bám mốc**: % SFX trong ±0,25s quanh CUT vs quanh TEXT — quyết định KIẾN TRÚC (B5).
3. **Volume median editor** → số máy = editor × 0,36 (quy tương quan lớp PB10,
   0,18/0,5), luôn đánh 🔸 tới cổng tai.
4. **Lead**: % tiếng TRƯỚC cut 0–200ms ("whoosh-vào-hit") → giữ/chỉnh `HOOK_WHOOSH_LEAD`.

## B5 — Quyết gate + hằng số

- **Bám CUT** (kiểu deepsea 48%): thêm niche vào `HOOK_SFX_NICHES`
  (`autoedit/ambient/schedule.py`) — 1 dòng, phần còn lại tự chạy nếu kho có file.
- **Bám TEXT** (kiểu space theo PB12): KHÔNG bật S3 bám cut — nhu cầu đó thuộc
  overlay-SFX bám text (đã có) + backlog chapter-title whoosh/swell.
- Số đo lệch số deepsea đang dùng chung (`HOOK_SFX_PM/VOL/GAP/CLICK_CAP/LEAD`) →
  lúc đó mới tách hằng per-niche (dict theo niche), KHÔNG tách trước (P2).
- **Số đo editor là điểm XUẤT PHÁT, không phải đích — cổng tai user đè được.** Tiền lệ:
  mật độ hook đo 4,8/ph nhưng tai V4 chê dày đặc → máy chạy 1,44/ph (×0,30). Video công
  ty mix nhiều lớp khác kênh tham chiếu; luôn dựng video kiểm trước khi tin số đo.

### B5b — Đường tắt MƯỢN SỐ (tiền lệ space 2026-07-14)

Niche mới gần giống niche đã đo + **user chốt** → bật gate mượn nguyên số + nạp kho
(18 file hook dùng chung được vì là tiếng cinematic chung) — bắt buộc: đánh 🔸 tại
hằng số + block 📌 vào `MO_TA_VAN_HANH_HOOK_SFX.md` + rà chồng chéo riêng niche đó
(mẫu: §3b file trên). Có số đo riêng → thay, gỡ 🔸.

## B6 — Video kiểm + cổng tai (user — máy không tự phán)

Rà chồng chéo P5 các lớp âm TRƯỚC khi dựng (mẫu bảng: MO_TA_VAN_HANH_HOOK_SFX §3/§3b).
Dựng 1 video kiểm → user nghe: mật độ hook, từng loại tiếng có "khớp hình" không,
volume từng lớp (mỗi lớp = 1 hằng số, chê chỉnh 1 dòng). Đạt → ghi NHAT_KY + memory.
