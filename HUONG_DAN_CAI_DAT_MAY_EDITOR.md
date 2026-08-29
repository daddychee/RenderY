# HƯỚNG DẪN CÀI ĐẶT MÁY EDITOR — bàn giao TOOL EDIT PADOMA (v3 — kho + SỔ dùng chung trên F:)

> **Dùng khi:** bàn giao tool sang máy editor để VẬN HÀNH (dựng video, thêm niche, nạp kho).
> **Mô hình:** KHÔNG đóng gói phần mềm (đã thử — nhiều bug). Copy **bộ cài 1 folder** + cài
> VSCode/Claude Code, editor làm mọi việc bằng PROMPT. Máy gốc (user PADOMA) = CHUẨN tri thức;
> máy editor = vận hành; tri thức fix lỗi chảy về máy gốc qua `BAN_GIAO\` (PHẦN D).
> **v2 (2026-07-15):** kho footage `F:\AutoEdit` KHÔNG copy — dùng chung ổ F: máy gốc qua LAN.
> **v3 (2026-07-15, G1 ✅ XONG):** cả SỔ (cache.db) + nhạc + SFX cũng nằm chung `F:\AutoEdit`
> (`set-data-root`) — mọi máy cùng 1 sổ tag/sổ đã-dùng, **editor TỰ NẠP kho/nhạc được**.
> Key GLM: MỖI editor dùng key RIÊNG (user chốt 2026-07-15).

```
MÁY GỐC (PADOMA)                                MÁY EDITOR
  F:\AutoEdit = kho + sổ + nhạc + SFX ◄──map ổ F:──  đọc/dựng/NẠP chung 1 chỗ
  chuẩn tri thức     ──bộ cài 1 folder (1 lần)──►    vận hành hằng ngày bằng prompt
  nhận & gộp tri thức  ◄── F:\BAN_GIAO_TU_EDITOR ──  mỗi fix: nhật ký + memory + git bundle
```

Bộ cài dựng sẵn tại: **`F:\BO_CAI_MAY_EDITOR\`** (xem `DOC_DAU_TIEN.md` trong đó).
Mốc bàn giao: 2026-07-15 · pytest 531/531 (số tăng theo thời gian).

---

## PHẦN A — Chuẩn bị trên MÁY GỐC (user làm)

### A1. Share ổ F: cho máy editor (1 lần)

1. Tạo tài khoản Windows riêng cho editor trên máy gốc (Settings → Accounts → Other users →
   local account, vd `editor1` + mật khẩu) — an toàn hơn share Everyone.
2. Share TOÀN Ổ F: (bắt buộc cả ổ — path trong sổ tag là `F:\AutoEdit\...`, máy editor phải
   map đúng chữ `F:`): File Explorer → chuột phải ổ F: → Properties → Sharing →
   Advanced Sharing → tick Share this folder → Share name: `F` → Permissions: thêm `editor1`,
   tick **Change + Read** → OK.
3. Ghi lại tên máy gốc: chạy `hostname` trong terminal (vd `PADOMA-PC`) — máy editor cần để map.

### A2. Máy gốc phải LUÔN SẴN SÀNG khi editor làm việc

- Settings → System → Power: **Sleep = Never** (khi cắm điện). Máy gốc ngủ/tắt = job editor chết giữa chừng.
- Cả 2 máy nên cắm **mạng DÂY gigabit** (source đọc nhiều GB/video, chiếm ~85% thời gian pipeline —
  Wi-Fi chậm hơn 3–4 lần).

### A3. Làm tươi bộ cài (chạy lại nếu để lâu mới mang đi)

```powershell
# 1. Xuất memory mới nhất vào project
robocopy "$env:USERPROFILE\.claude\projects\c--Users-NBPC-Documents-Claude-Projects-tool-edit-padoma\memory" "C:\Users\NBPC\Documents\Claude\Projects\tool edit padoma\BAN_GIAO\memory_goc" /MIR
# 2. Project → bộ cài (LƯU Ý: sau đó sửa lại GLM_API_KEY trong bộ cài thành trống — key GLM riêng từng editor)
robocopy "C:\Users\NBPC\Documents\Claude\Projects\tool edit padoma" "F:\BO_CAI_MAY_EDITOR\tool edit padoma" /MIR /XD ".venv" "projects" "__pycache__" ".pytest_cache" "TOOL CẮT SIÊU DỮ LIỆU" "AB_TAG_MOON"
```
(Không còn bước copy cache.db/nhạc/SFX — v3 sổ + nhạc + SFX đã nằm chung `F:\AutoEdit`.)

### A4. Key + tài khoản + luật ghi chung (user chốt 2026-07-15)

1. **Key GLM: RIÊNG mỗi editor** — bộ cài để `GLM_API_KEY=` trống, bootstrap C2 sẽ dừng nhắc
   editor điền key của mình vào `autoedit\.env`. Pexels ×10 · Google CSE · Serper vẫn dùng chung.
2. **Tài khoản Claude:** editor CÓ SẴN — chỉ cần đăng nhập Claude Code trên máy họ (B4).
   `.env` KHÔNG cần ANTHROPIC_API_KEY (NÃO chạy qua subscription).
3. **Luật ghi sổ chung (G2 — cập nhật 2026-07-16, cổng M4 đạt):** sổ là **PostgreSQL trên
   máy gốc** (bootstrap C6 trỏ bằng `set-db-url`), ghi đồng thời nhiều máy an toàn →
   **luật "1 job mỗi lúc" ĐÃ GỠ** — các máy dựng video song song thoải mái. Còn giữ 1 khuyến
   cáo NHẸ: tránh 2 mẻ NẠP kho vào **CÙNG niche** đúng cùng lúc (không phải vì sổ — vì 2 mẻ
   cùng ghi file clip vào cùng folder kho trên F:; khác niche thì vô tư).
4. **LUẬT TỰ NẠP video mẫu (user chốt 2026-07-16, áp MỌI máy):** dựng bài có video mẫu →
   máy nào dựng máy đó TỰ chạy `library-ingest` mẻ mẫu TRƯỚC khi đạo diễn (chi tiết trong
   skill `/dung-video`) — kho asset chung của công ty dày lên theo từng bài, mọi máy dùng lại được.
   **REF THEO CHƯƠNG (2026-07-18):** trong folder mẫu được chia folder con `Chapter 1/2/…` —
   máy chỉ ưu tiên cảnh mẫu đó ở ĐÚNG chương ấy; video ngoài folder chương = mẫu chung cả bài.
   Xếp video vào folder chương TRƯỚC khi làm draft tách cảnh. Chi tiết `MO_TA_VAN_HANH_REF.md §6`.

---

## PHẦN B — Trên MÁY EDITOR: cài tay phần tối thiểu (~20–30 phút)

| # | Việc | Cách làm | Lưu ý |
|---|---|---|---|
| 1 | Map ổ mạng **F:** | File Explorer → This PC → ⋯ → Map network drive → Drive: **F:** → Folder: `\\<tên máy gốc>\F` → tick Reconnect at sign-in → đăng nhập `editor1` + tick Remember | BẮT BUỘC đúng chữ **F:** (máy đã có ổ F: riêng → đổi chữ ổ đó trong Disk Management trước). Kiểm: mở `F:\AutoEdit\library` thấy folder niche |
| 2 | Copy bộ cài | Mở `F:\BO_CAI_MAY_EDITOR\` (qua mạng luôn) → copy folder `tool edit padoma` → `C:\Users\<user>\Documents\Claude\Projects\` | Chỉ 1 folder — sổ/nhạc/SFX đã nằm chung trên F:, không phải chép gì thêm |
| 3 | Node.js LTS | nodejs.org | Bắt buộc — pipeline gọi ngầm `claude -p` (chạy trên node) |
| 4 | VSCode | code.visualstudio.com | |
| 5 | Claude Code | Extension "Claude Code" trong VSCode **VÀ** CLI global: `npm install -g @anthropic-ai/claude-code` → chạy `claude` → đăng nhập tài khoản CÓ SẴN của editor | **CLI global BẮT BUỘC**, không chỉ extension |
| 6 | CapCut | Cùng đời **8.8.0** với máy gốc nếu kiếm được installer; bản khác vẫn chạy nhưng cổng mắt draft ĐẦU phải soi kỹ | Cài xong: mở CapCut → tạo 1 project trống → lưu (donor cho C8) |

Python / git / ffmpeg **KHÔNG cần cài tay** — Claude Code tự cài ở bước C1 (winget).
Skill `/dung-video` nằm trong `.claude\skills\` của project — tự có.

---

## PHẦN C — Claude Code TỰ CÀI (bootstrap)

Mở VSCode → Open Folder → `tool edit padoma` → mở Claude Code → dán prompt:

```
Đây là MÁY EDITOR mới nhận bàn giao. Đọc HUONG_DAN_CAI_DAT_MAY_EDITOR.md, thực hiện
PHẦN C tuần tự từng bước. Bước nào fail → dừng, báo nguyên nhân + cách xử lý, KHÔNG nhảy bước.
```

**Các bước dưới đây viết cho Claude Code đọc và tự làm** (người ngồi cạnh chỉ xác nhận):

- **C1. Tiên quyết:** kiểm `node --version` · `claude --version` — thiếu → dừng, chỉ người làm
  PHẦN B (2 cái này phải cài tay). Rồi kiểm `python --version` (≥3.11) · `git --version` ·
  `ffmpeg -version` — thiếu cái nào TỰ CÀI qua winget (`winget install Python.Python.3.12` /
  `Git.Git` / `Gyan.FFmpeg`), xong mở lại terminal kiểm lại.
- **C1b. MSVC C++ Build Tools (BẮT BUỘC từ 2026-07-21 — madmom build từ nguồn):** kiểm
  `Test-Path "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"` —
  chưa có thì cài (~2-4GB, 10-30 phút):
  ```
  winget install --id Microsoft.VisualStudio.2022.BuildTools --accept-package-agreements --accept-source-agreements --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
  ```
  madmom = đo downbeat/nhịp cho lưới cắt Δ (foundation `e2-chuyen-footage-theo-phach.md`).
- **C2. Kiểm dữ liệu bàn giao:** `autoedit\.env` tồn tại · **`GLM_API_KEY=` đang TRỐNG →
  dừng, nhắc editor mở `autoedit\.env` điền key GLM RIÊNG của mình** (A4.1) rồi tiếp ·
  `BAN_GIAO\memory_goc\` có file .md · **ổ mạng**: `F:\AutoEdit\library` mở được có folder
  niche + `F:\AutoEdit\cache.db` + `music\` + `sfx\` tồn tại. F: không mở được → dừng, làm lại B1.
- **C3. Môi trường Python:** `pip install uv` (nếu thiếu) → trong `autoedit\`: `uv sync`
  (madmom build C ~1-2 phút lần đầu — setuptools tự tìm MSVC đã cài ở C1b, đo thật
  2026-07-21 không cần shell vcvars) → `uv run autoedit --help` phải in danh sách lệnh.
  Lỗi `Microsoft Visual C++ 14.0 or greater is required` = chưa làm C1b (hoặc cài xong
  chưa mở terminal mới); vẫn lỗi → chạy trong shell vcvars:
  `cmd /c ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul && uv sync"`.
  Kiểm madmom: `uv run python -c "import madmom; print(madmom.__version__)"` → `0.17.dev0`.
- **C4. Nạp memory bàn giao:** copy TOÀN BỘ file trong `BAN_GIAO\memory_goc\` (kể cả
  `MEMORY.md`) vào thư mục memory của CHÍNH BẠN trên máy này (đường dẫn memory ghi trong
  system prompt của bạn, mục Memory — tạo folder nếu chưa có). Thiếu bước này = "mất trí nhớ"
  toàn bộ bài học từ máy gốc.
- **C5. Kiểm chữ ổ kho:** kho PHẢI ở đúng `F:\AutoEdit` (ổ mạng map từ máy gốc). KHÔNG rewrite
  path trong cache.db ở mô hình dùng chung — map sai chữ ổ thì sửa map (B1), không sửa sổ.
- **C6.** `uv run autoedit set-library-root "F:\AutoEdit\library"` rồi
  `uv run autoedit set-data-root "F:\AutoEdit"` (kho file + nhạc + SFX dùng chung trên F:).
- **C6b. Trỏ SỔ về PostgreSQL máy gốc (G2 — sổ thật là Postgres từ 2026-07-16):**
  kiểm `ping DESKTOP-98SCPHI -4` có trả lời (hostname máy gốc — KHÔNG dùng IP, IP là DHCP) →
  `uv run autoedit set-db-url "host=DESKTOP-98SCPHI port=5432 dbname=autoedit user=autoedit password=<HỎI USER>"`
  (password KHÔNG ghi trong file này — hỏi user lúc cài; lệnh tự test kết nối ngay).
  Ping không resolve → dừng báo user. Muốn quay về SQLite cũ: `set-db-url --clear`.
  LƯU Ý: `F:\AutoEdit\cache.db` vẫn tồn tại = bản SQLite ĐÓNG BĂNG làm mốc lui, KHÔNG xóa.
- **C7.** HỎI người: xuất draft ra folder nào — PHẢI là ổ **LOCAL máy editor** còn trống ≥100GB
  (vd `D:\CapCut Drafts`), KHÔNG đặt trên ổ mạng F: → tạo folder →
  `uv run autoedit set-draft-root "<folder>"`.
- **C8. Đăng ký máy CapCut:** tìm draft mới nhất trong
  `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft` (project trống tạo ở B6) →
  `uv run autoedit register-machine --donor "<path folder draft>"` → phải thấy
  `✓ Machine profile đã lưu`.
- **C9. Bật luật máy editor:** tạo `BAN_GIAO\MAY_EDITOR.flag` (ngày cài + tên máy + tên editor).
  Từ đây CLAUDE.md §7 hiệu lực. File này KHÔNG commit (đã gitignore).
- **C10. FULL test:** trong `autoedit\`: `uv run pytest -q`. Mốc bàn giao: **549 pass**
  (2026-07-16; có thể cao hơn nếu máy gốc thêm test). Fail → 3 giả thuyết; nghi số 1: ffmpeg/PATH.
- **C11. Smoke test pipeline** (folder mẫu đi kèm project):
  ```
  uv run autoedit new --script "..\voice test travel\script.txt" --voice "..\voice test travel\voice.mp3" --channel travel
  ```
  → lấy `project_dir` → `uv run autoedit align <project_dir>` (lần ĐẦU tải model whisper
  ~500MB, cần mạng, hơi lâu — bình thường) → `uv run autoedit direct-context <project_dir>` →
  kiểm kho + sổ chung qua mạng: `uv run autoedit library-search` 1 query bất kỳ niche `deepsea`
  trả kết quả `F:\...` + `uv run autoedit music-list` liệt kê được pool nhạc.
  Không lỗi = pipeline + kho mạng + sổ chung sống.
- **C12. Ghi mốc:** entry "cài đặt máy editor xong" vào `BAN_GIAO\NHAT_KY_MAY_EDITOR.md` +
  `git commit`. Báo cáo tổng kết C1–C11 cho người.

---

## PHẦN D — Kênh tri thức chung (QUAN TRỌNG NHẤT về lâu dài)

**Nguyên tắc:** máy editor là máy VẬN HÀNH; máy gốc là CHUẨN. Mọi bug fix / luật mới trên máy
editor PHẢI chảy về máy gốc — kênh là folder `BAN_GIAO\`.

### D1. Trên máy editor — sau MỖI bug fix / luật mới (Claude Code tự làm, luật CLAUDE.md §7)

1. Bộ ghi chép chuẩn CLAUDE.md §6 (entry `NHAT_KY_BUILD.md` + memory file + `BAN_DO_TRI_THUC.md` nếu có nguồn mới).
2. **Mirror** memory file mới/sửa → copy nguyên file `.md` vào `BAN_GIAO\memory_moi\`.
3. Entry vào `BAN_GIAO\NHAT_KY_MAY_EDITOR.md` (khuôn trong file — vấn đề / root cause / fix / test / memory).
4. `git commit` → `git bundle create BAN_GIAO/padoma_editor.bundle --all` →
   **đẩy lên máy gốc qua chính ổ F:**:
   ```
   robocopy "BAN_GIAO" "F:\BAN_GIAO_TU_EDITOR\<tên editor>" /MIR /XF MAY_EDITOR.flag
   ```
   (Mất mạng → Google Drive/USB là kênh dự phòng.)

### D2. Trên máy gốc — user kiểm và gộp (xem `F:\BAN_GIAO_TU_EDITOR\<tên editor>\`)

1. Đọc `NHAT_KY_MAY_EDITOR.md` — nắm chuyện gì xảy ra bên đó.
2. Đọc từng file `memory_moi\` — ưng thì copy vào memory máy gốc + thêm dòng `MEMORY.md`.
3. Nhận code (nhờ Claude Code máy gốc làm, review từng diff):
   ```
   git fetch "F:\BAN_GIAO_TU_EDITOR\<tên editor>\padoma_editor.bundle" master:editor-master
   git diff master..editor-master     # review
   git merge editor-master            # khi ưng
   ```
4. Chiều ngược (máy gốc → máy editor): xem D3.

### D3. Cập nhật máy editor khi máy gốc nâng cấp (2 bước, ~2 phút/máy)

**Trên máy gốc (user chỉ cần nói 1 câu):** bảo Claude Code *"làm tươi bộ cài"* (A3) —
nó xuất memory + mirror project sang `F:\BO_CAI_MAY_EDITOR\tool edit padoma` + trắng GLM key.

**Trên từng máy editor (dán cho Claude Code):** *"Cập nhật tool từ bộ cài theo HUONG_DAN D3"*
— Claude Code chạy:
```powershell
robocopy "F:\BO_CAI_MAY_EDITOR\tool edit padoma" "C:\Users\<user>\Documents\Claude\Projects\tool edit padoma" /E /XD "BAN_GIAO" ".venv" "projects" /XF ".env"
```
rồi trong `autoedit\`: `uv run uv sync` (vài giây nếu thư viện không đổi) → nhắc editor
**mở phiên Claude Code MỚI** (đọc CLAUDE.md/skill bản mới).

**3 luật an toàn của lệnh trên — KHÔNG được đổi:**
- `/E` chứ KHÔNG BAO GIỜ `/MIR` — bộ cài không chứa `projects\`; `/MIR` sẽ XÓA SẠCH
  project video của editor.
- `/XD BAN_GIAO` — giữ nguyên `MAY_EDITOR.flag` + `NHAT_KY_MAY_EDITOR.md` + `memory_moi\`
  của máy editor (đè là MẤT nhật ký bàn giao). Memory máy gốc mới đến qua bundle/memory_goc
  khi cần, không qua đường này.
- `/XF .env` — giữ GLM key riêng đã điền của editor (bộ cài để trắng key).

> ⚠ **HỆ QUẢ của `/XF .env`: KEY MỚI KHÔNG TỰ SANG.** `.env` của editor được giữ nguyên,
> nên mọi biến MỚI thêm vào bộ cài phải **chép tay 1 dòng**. Cách kiểm nhanh sau update:
> ```powershell
> # so tên biến giữa bộ cài và máy mình (KHÔNG in giá trị key ra màn hình)
> $a = (Select-String -Path "F:\BO_CAI_MAY_EDITOR\tool edit padoma\autoedit\.env" -Pattern '^\w+=' ).Line -replace '=.*',''
> $b = (Select-String -Path ".\autoedit\.env" -Pattern '^\w+=').Line -replace '=.*',''
> Compare-Object $a $b | Where-Object SideIndicator -eq '<='   # biến có ở bộ cài mà máy mình THIẾU
> ```
> Thiếu biến nào thì mở `F:\BO_CAI_MAY_EDITOR\tool edit padoma\autoedit\.env`, copy đúng
> dòng đó sang `autoedit\.env` của mình.
> **Đợt 2026-07-18 có biến mới: `EPIDEMIC_API_KEY`** (key CHUNG, user chốt — khác GLM key
> riêng). Thiếu nó thì *dựng video vẫn chạy bình thường* (SFX Epidemic đã nằm sẵn trong kho
> `F:\AutoEdit\ambient\`), chỉ lệnh `epidemic-sfx` (nạp THÊM SFX mới) là báo thiếu key.
> Key Epidemic **hết hạn 30 ngày** (hiện tại tới 2026-08-16) — hết hạn thì máy gốc tạo key
> mới, làm tươi bộ cài, editor chép lại 1 dòng.

Khi nào cần chạy: khi máy gốc báo có nâng cấp ảnh hưởng máy editor (tính năng/luật/fix bug
pipeline). Không cần chạy theo từng commit lặt vặt.

---

## PHẦN E — Editor dùng hằng ngày

- Mở VSCode → Open Folder → project → Claude Code. Mọi việc gõ tiếng Việt tự nhiên.
- **Dựng video:** `/dung-video` + đường dẫn folder chứa script (`.txt`) + voice (`.mp3/.wav`)
  + brief (niche, tone, nhấn gì). **Cổng MẮT/TAI trong CapCut vẫn do editor quyết** — Claude
  không tự phán đạt.
- **Thêm niche mới / nạp footage / nạp nhạc:** editor TỰ LÀM từ máy mình (sổ chung Postgres) —
  khuôn prompt thêm niche ở `prompt them niche moi.txt`. Khuyến cáo nhẹ: tránh 2 mẻ nạp vào
  CÙNG niche đúng cùng lúc (A4.3 — vì file kho, không phải vì sổ).
- **Gặp lỗi:** dán NGUYÊN VĂN lỗi vào chat. Fix xong mà Claude chưa tự ghi chép → nhắc:
  *"ghi chép bàn giao theo CLAUDE.md §7"*.
- **Dựng video SONG SONG nhiều máy: ĐƯỢC** (từ G2-M4 2026-07-16 — sổ Postgres ghi đồng thời,
  GLM key riêng từng editor). Máy gốc phải đang BẬT (sổ + kho đều nằm đó).
- Job đang chạy mà ổ F: đứt (máy gốc tắt/mạng rớt) → job chết giữa chừng: map lại F:, chạy
  lại đúng stage đang dở (project.json resume được — NT1).

### E1. Hai công tắc SFX (đợt 2026-07-18) — editor bật/tắt MỖI LẦN DỰNG

**Cả hai MẶC ĐỊNH TẮT — không gõ gì thì không có gì bật.** Gõ cờ nào bật cờ đó:

```bash
autoedit assemble <project>                    # mặc định: CẢ HAI TẮT (chỉ SFX kho cũ)
autoedit assemble <project> --epidemic         # + dùng SFX Epidemic
autoedit assemble <project> --sfx-llm          # + NÃO chấm tiếng cho cảnh bảng luật mù chữ
autoedit run <project> --epidemic --sfx-llm    # cả pipeline, ghép được cả hai
```

| Cờ | Mặc định | Khi nào dùng |
|---|---|---|
| `--epidemic` | **TẮT** (user chốt 2026-07-18) | Editor muốn thử SFX Epidemic cho bài này. **Kho vẫn giữ nguyên file** — không gõ cờ chỉ là không chọn tới, gõ vào là có ngay. |
| `--sfx-llm` | TẮT | Bài có nhiều cảnh mà máy để im (làng mạc, khu dân cư, công trường…) → bật cho NÃO chấm thêm. Tốn ~1 lượt gọi NÃO/bài. Lỗi mạng thì tự bỏ qua, KHÔNG chặn dựng. |

Soi kết quả: `report.html` mục SFX chủ thể — cột nguồn `kho` (bảng luật) vs `llm` (NÃO chấm).

### E2. Nạp THÊM SFX Epidemic vào kho (cần `EPIDEMIC_API_KEY`)

```bash
autoedit epidemic-sfx --niche life-in --want "camel" --dry-run   # LUÔN xem trước
autoedit epidemic-sfx --niche life-in --want "market=souk market:4" --target 4
```
**★ Luật nạp: theo NHU CẦU BÀI, KHÔNG theo độ mỏng của kho.** Xem `report.html` bài vừa
dựng, kind nào dùng nhiều thì nạp thêm kind đó. (Bài học thật: nạp 6 kind "mỏng nhất" →
**0/115 lượt dùng** vì bài không có cảnh nào cần chúng.)
Kho nằm trên `F:\AutoEdit\ambient\<niche>` — **dùng chung**, nạp xong mọi máy có ngay.
Chi tiết + 6 bẫy: `MO_TA_VAN_HANH_EPIDEMIC_SFX.md`.

---

## PHẦN F — Sự cố biết trước

| Hiện tượng | Nguyên nhân thường gặp | Xử lý |
|---|---|---|
| `F:\` không mở được / hỏi mật khẩu lại | Máy gốc tắt/ngủ · đổi mật khẩu `editor1` · map không persistent | Bật máy gốc; map lại B1 (tick Remember) |
| Job chết giữa chừng kèm lỗi đọc file `F:\...` | Đứt kết nối ổ mạng giữa job | Map lại F: → chạy lại stage đang dở (resume NT1) |
| Kho local 0 kết quả dù `F:\AutoEdit` mở được | Máy chưa `set-data-root` (đang đọc sổ rỗng `~\AutoEdit` tự sinh) | Chạy lại C6; kiểm `~\.autoedit\machine.json::data_root` = `F:\AutoEdit` |
| Lỗi kết nối sổ (`connection refused` / `could not translate host name "DESKTOP-98SCPHI"`) | Máy gốc tắt/ngủ · service PostgreSQL không chạy · hostname không resolve | Bật máy gốc; trên máy gốc kiểm service `postgresql-x64-17` Running; ping lại — vẫn tắc thì báo user (KHÔNG tự đổi sang IP) |
| `database is locked` khi nạp/dựng | Máy này CHƯA `set-db-url` (đang rơi về SQLite trên F: — chỉ còn là mốc lui) | Chạy C6b trỏ sổ Postgres; kiểm `~\.autoedit\machine.json::db_url` |
| Sổ cache.db nghi hỏng (lỗi `malformed`) | Chỉ xảy ra ở lưng SQLite mốc-lui (sổ thật Postgres không dính) | Không đụng job hằng ngày; báo user máy gốc xử (backup `F:\AutoEdit\backup\`) |
| Pipeline báo không tìm thấy `claude` khi đạo diễn | CLI npm global chưa cài / terminal cũ | `npm install -g @anthropic-ai/claude-code` → mở VSCode mới |
| `align` lần đầu đứng rất lâu | Tải model whisper ~500MB | Bình thường — chờ, cần mạng |
| GLM 429/timeout liên tục | Máy gốc đang chạy job (key chung) / mạng | Chờ + thử lại; server mặc định `api.z.ai` |
| pytest fail hàng loạt ngay sau cài | 90% ffmpeg thiếu PATH | C1 winget lại, mở terminal mới |
| CapCut preview ĐEN / crash khi click footage | Vi phạm C1–C5 hoặc CapCut khác đời schema | KHÔNG tự sửa lung tung — CLAUDE.md §4, ghi nhật ký editor, báo user |
| Dựng chậm bất thường ở stage source | Wi-Fi / mạng 100Mbps | Cắm dây gigabit cả 2 máy (A2) |
| `epidemic-sfx` báo *"Thiếu EPIDEMIC_API_KEY"* | `.env` máy này chưa có biến mới (D3 `/XF .env` giữ nguyên `.env` cũ — key mới KHÔNG tự sang) | Copy dòng `EPIDEMIC_API_KEY=…` từ `F:\BO_CAI_MAY_EDITOR\tool edit padoma\autoedit\.env` sang `autoedit\.env` của mình. **Dựng video vẫn chạy bình thường khi thiếu key** — SFX đã nằm trong kho F: |
| `epidemic-sfx` báo *"Key bị từ chối (HTTP 401)"* | Key Epidemic **hết hạn 30 ngày** | Báo user máy gốc tạo key mới → làm tươi bộ cài → chép lại 1 dòng. KHÔNG tự đăng ký key khác |
| `--sfx-llm` chạy mà không thêm tiếng nào | Bảng luật đã quyết hết (không còn cảnh mù chữ) — ĐÚNG, không phải lỗi | Bình thường. Tầng NÃO chỉ điền chỗ bảng luật bó tay, KHÔNG lật quyết định của bảng luật |
| Draft mang sang máy khác không mở | — | Draft xuất mặc định PORTABLE (`MO_TA_VAN_HANH_PORTABLE.md`) |

**Editor KHÔNG cùng mạng LAN (làm từ xa):** mô hình ổ F: chung KHÔNG khả thi (băng thông) —
quay về phương án copy kho 76GB vào máy editor (robocopy giữ mtime) + rewrite path `F:`→ổ mới
trong cache.db (tiền lệ milestone KHO-F) — hỏi Claude Code máy gốc dựng lại hướng dẫn v1 từ git.

---

## PHẦN G — Lộ trình sổ dùng chung

**G1 ✅ XONG 2026-07-15 (user duyệt):** `set-data-root` — cache.db + music + sfx của mọi máy
trỏ chung `F:\AutoEdit` (machine.json; máy chưa set giữ nguyên `~\AutoEdit` như cũ). Kèm:
backup tự động sổ trước mỗi mẻ `library-index`/`library-ingest` vào `F:\AutoEdit\backup\`
(giữ 10 bản) + connect chờ khóa 30s. Rủi ro còn lại: SQLite trên SMB khi 2 máy GHI đúng cùng
lúc — đỡ bằng luật A4.3 + backup; bản C: cũ máy gốc niêm phong `AutoEdit.pre-G1-backup`.

**G2 — ✅ M1→M4 XONG (2026-07-16): SỔ THẬT LÀ POSTGRESQL TRÊN MÁY GỐC, LAN-only** (PGDATA
`D:\QQ SQL` — không share, khác đĩa kho; VPS bỏ hẳn). M3: máy gốc flip + video thật DS1-086
dựng trọn trên PG, user duyệt mắt+tai. **M4: máy editor đầu tiên nối qua hostname
`DESKTOP-98SCPHI` + test ghi song song 2 máy ĐẠT (600 lệnh ghi đồng thời, 0 lỗi) → LUẬT
1-JOB ĐÃ GỠ** — nhiều máy dựng song song. Đường lui vĩnh viễn: `set-db-url --clear` → về
SQLite G1 (`F:\AutoEdit\cache.db` đóng băng). Còn M5: pg_dump hằng ngày sang
`F:\AutoEdit\backup\pg\`. Chi tiết: **`MO_TA_VAN_HANH_G2_DB_SERVER.md`**.
