# CLAUDE.md — AutoEdit (autoedit package)

> Tài liệu đầy đủ về dự án ở `../CLAUDE.md` (folder cha). Đọc file đó trước khi code bất kỳ tính năng nào.

---

## WINDOWS SETUP — Làm ngay khi mở project lần đầu

Khi người dùng yêu cầu "setup" hoặc "cài đặt", hãy thực hiện tuần tự các bước sau bằng Bash/terminal. Dừng lại báo cáo nếu bước nào thất bại.

### Bước 1 — Kiểm tra Python ≥ 3.11
```bash
python --version
```
- Nếu < 3.11: thông báo cài Python 3.11+ tại python.org, dừng lại.
- Nếu ≥ 3.11: tiếp tục.

### Bước 2 — Kiểm tra và cài `uv`
```bash
uv --version
```
Nếu chưa có:
```powershell
pip install uv
```

### Bước 3 — Cài dependencies
Chạy từ folder `autoedit/` (folder chứa `pyproject.toml`):
```bash
uv sync
```
Kiểm tra thành công:
```bash
uv run autoedit --help
```
Phải in ra danh sách lệnh. Nếu lỗi import → đọc traceback, sửa trước khi tiếp.

### Bước 4 — Tạo file `.env`
Kiểm tra `.env` đã tồn tại chưa:
```bash
# Windows PowerShell
Test-Path .env
```
Nếu chưa có: copy từ folder cha:
```powershell
Copy-Item "..\.env" ".env"
```
Nếu folder cha cũng không có, tạo `.env` với nội dung:
```
PEXELS_API_KEY=<điền key>
GOOGLE_CSE_KEY=<điền key>
GOOGLE_CSE_CX=<điền key>
SERPER_API_KEY=<điền key>
GLM_API_KEY=<điền key>
```
> API keys thật đang ở `../.env` — copy từ đó.
> **KHÔNG cần ANTHROPIC_API_KEY** — NÃO chạy qua Claude Code subscription (user chốt
> 2026-07-09, key cũ đã xóa). Chỉ cần nếu dùng fallback `--engine api`/`--engine claude`.

### Bước 5 — Chạy test
```bash
uv run pytest -q
```
- Mục tiêu: ≥ 125/130 pass.
- Test fail liên quan `textutil` hoặc `osascript` → **bình thường** (Mac-only, xem Bước 7).
- Test fail khác → đọc traceback và sửa.

### Bước 6 — Tạo thư mục AutoEdit
```powershell
New-Item -ItemType Directory -Force "$HOME\AutoEdit\music"
New-Item -ItemType Directory -Force "$HOME\AutoEdit\sfx"
New-Item -ItemType Directory -Force "$HOME\AutoEdit\library"
```

### Bước 7 — register-machine cho CapCut Windows
CapCut Windows lưu draft ở:
```
C:\Users\<username>\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft\
```
Cần có ít nhất 1 draft thật trong CapCut (mở CapCut → tạo project mới bất kỳ → lưu).

Tìm folder draft:
```powershell
$capcut = "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft"
Get-ChildItem $capcut | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```
Lấy tên folder draft gần nhất, rồi:
```bash
uv run autoedit register-machine --donor "<đường dẫn đầy đủ tới folder draft>"
```
Thành công khi thấy: `✓ Machine profile đã lưu tại ~/.autoedit/machine.json`

### Bước 8 — Test pipeline nhanh (không cần CapCut)
```bash
uv run autoedit new --script samples/script.txt --voice samples/voice.mp3
```
Copy project ID từ output, rồi:
```bash
uv run autoedit align projects/<ID>
uv run autoedit direct projects/<ID>
```
Nếu `align` và `direct` chạy không lỗi → pipeline hoạt động.

---

## Lưu ý Windows-specific (đọc khi gặp lỗi)

### `textutil` — không có trên Windows
Lệnh `autoedit rtf-to-txt` dùng `textutil` (macOS). Thay thế trên Windows:
- Convert thủ công: mở `.rtf` bằng WordPad → Save As `.txt`
- Hoặc dùng LibreOffice CLI: `soffice --headless --convert-to txt file.rtf`
- Khi code: thêm nhánh Windows vào `cli.py` hàm `rtf_to_txt_cmd`:
  ```python
  import platform
  if platform.system() == "Windows":
      # dùng win32com hoặc subprocess gọi LibreOffice
  ```

### `osascript` / `make-launcher` — không có trên Windows
Lệnh `autoedit make-launcher` sinh file `.command` (macOS bash). Trên Windows bỏ qua.
Thay thế: tạo file `.bat` hoặc `.ps1` tương đương nếu cần.

### CapCut draft path
- **Mac**: `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/`
- **Windows**: `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\`

File `autoedit/packager/machine.py` dòng 35 hardcode Mac path. Khi cần Windows:
```python
import platform
if platform.system() == "Windows":
    CAPCUT_DRAFT_ROOT = Path(os.environ["LOCALAPPDATA"]) / "CapCut/User Data/Projects/com.lveditor.draft"
else:
    CAPCUT_DRAFT_ROOT = Path("~/Movies/CapCut/User Data/Projects/com.lveditor.draft").expanduser()
```

### `~/AutoEdit/` path
`Path("~/AutoEdit/...").expanduser()` trên Windows → `C:\Users\<username>\AutoEdit\` — hoạt động đúng, không cần sửa.

---

## Quy trình dev hàng ngày

```bash
# Chạy test trước khi commit
uv run pytest -q

# Chạy 1 video mẫu end-to-end
uv run autoedit make <folder_chứa_script_và_voice> --channel retirement-abroad

# Xem report
# report.html tự mở sau khi make xong
```

## Kiến trúc nhanh (đọc ../CLAUDE.md để đầy đủ)

```
autoedit/
├── cli.py              # Entry point typer — mọi lệnh CLI
├── project.py          # create_project, load_project — project.json
├── align/              # M2: faster-whisper → timestamp từng từ
├── director/           # M3: LLM Claude → beats + enrich
├── cutter/             # M4: ffmpeg cắt voice + hình thở
├── sourcer/            # M5: local library / Pexels / Serper entity
├── ranker/             # M5: chấm điểm + veto footage
├── packager/           # M6: pycapcut → draft CapCut
│   ├── machine.py      # register-machine, donor profile
│   ├── assembler.py    # ráp 3 track audio/video/text
│   └── charts.py       # render matplotlib → video
├── music/              # M-N: chọn nhạc theo mood chương
├── library/            # M3.5: thư viện niche + cache.db
├── sfx/                # P1.4: thư viện SFX
├── overlay/            # P1: text overlay + kinetic
└── report/             # M7: report.html bàn giao editor
```
