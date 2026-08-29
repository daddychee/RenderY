# HƯỚNG DẪN COPY MÁY GỐC → MÁY GỐC MỚI (bản đầy đủ: code + SQL + kho footage)

> **Dùng khi:** nhân bản TOÀN BỘ hệ thống máy gốc PADOMA sang một máy gốc khác — khác với
> `HUONG_DAN_CAI_DAT_MAY_EDITOR.md` (máy editor chỉ VẬN HÀNH, dùng chung kho + sổ qua LAN).
> Máy gốc mới có **kho RIÊNG (copy F:) + sổ PostgreSQL RIÊNG (restore từ D:) + code RIÊNG**.
>
> ⚠ **Copy là ẢNH CHỤP 1 thời điểm, không phải đồng bộ.** Sau khi tách, 2 máy gốc nạp kho /
> ghi sổ độc lập → kho và sổ sẽ LỆCH NHAU dần. Nếu ý định là "máy mới THAY máy cũ" xem §7.

**3 khối dữ liệu phải mang đi:**

| Khối | Ở máy gốc cũ | Đích trên máy mới | Cỡ ước tính |
|---|---|---|---|
| Code + docs + memory | `C:\Users\NBPC\Documents\Claude\Projects\tool edit padoma` + memory Claude | `...\Documents\Claude\Projects\tool edit padoma` (giữ đúng tên folder) | nhỏ (~vài trăm MB, bỏ .venv) |
| Sổ PostgreSQL | PGDATA `D:\QQ SQL` (service `postgresql-x64-17`, db `autoedit`) | Postgres 17 cài mới + restore dump | vài GB |
| Kho footage + nhạc + SFX + sổ SQLite mốc-lui | `F:\AutoEdit` (toàn bộ) | **BẮT BUỘC đúng `F:\AutoEdit`** trên máy mới | ~100GB+ (kho 20k+ asset) |

---

## §0. Yêu cầu máy mới TRƯỚC khi copy

1. Windows 10/11, dung lượng đĩa đủ 3 khối trên.
2. **Phải có 1 ổ mang chữ `F:`** (đổi chữ ổ trong Disk Management nếu cần) — mọi path trong
   sổ tag là `F:\AutoEdit\...`, sai chữ ổ là kho "0 kết quả". KHÔNG rewrite path trong sổ.
3. Ổ LOCAL còn trống ≥100GB cho draft xuất (máy cũ dùng `E:\CapCut Drafts`; máy mới đặt đâu
   cũng được — sẽ `set-draft-root` ở §5, đây là cấu hình THEO MÁY).
4. Cả 2 máy cắm mạng DÂY gigabit nếu copy qua LAN (100GB+ qua Wi-Fi rất lâu); hoặc dùng ổ
   cứng rời trung gian.
5. **TẠM DỪNG mọi job dựng/nạp kho trên máy cũ trong lúc copy** — để 3 khối chụp cùng 1
   thời điểm, sổ và file kho khớp nhau.

---

## §1. Copy CODE + memory (máy cũ → máy mới)

```powershell
# 1a. Xuất memory Claude mới nhất vào project (để mang theo cùng code)
robocopy "$env:USERPROFILE\.claude\projects\c--Users-NBPC-Documents-Claude-Projects-tool-edit-padoma\memory" "C:\Users\NBPC\Documents\Claude\Projects\tool edit padoma\BAN_GIAO\memory_goc" /MIR

# 1b. Copy project (bỏ .venv — sẽ uv sync lại; giữ .env, giữ git history, giữ projects\ nếu muốn mang video cũ)
robocopy "C:\Users\NBPC\Documents\Claude\Projects\tool edit padoma" "<đích, vd \\MAY-MOI\share\tool edit padoma>" /E /XD ".venv" "__pycache__" ".pytest_cache" /COPY:DAT
```

- **`.env` COPY NGUYÊN** (khác máy editor): máy gốc mới cần đủ key Pexels / Google CSE /
  Serper / EPIDEMIC. Riêng **GLM key nên tạo KEY MỚI riêng cho máy này** nếu 2 máy gốc sẽ
  chạy song song (luật ≤3 luồng/key — dùng chung là giành nhau, y hệt luật editor A4.1).
- `autoedit\projects\` (video đã dựng) là TÙY CHỌN — muốn gọn thì thêm `"projects"` vào `/XD`.
- **KHÔNG copy `machine.json`** (`~\.autoedit\machine.json`) — file này THEO MÁY (chứa donor
  profile + device_id CapCut của máy cũ). Máy mới tự tạo ở §5.
- Trên máy mới, đặt folder vào `C:\Users\<user>\Documents\Claude\Projects\tool edit padoma`.

---

## §2. Copy KHO `F:\AutoEdit` (khối nặng nhất — chạy trước, lâu nhất)

```powershell
# chạy trên máy cũ, đích là ổ F: máy mới (share/map ổ hoặc ổ rời trung gian)
robocopy "F:\AutoEdit" "<đích F:\AutoEdit máy mới>" /MIR /COPY:DAT /DCOPY:T /R:2 /W:5 /MT:16 /LOG:"$env:TEMP\copy_kho.log" /TEE
```

- `/COPY:DAT /DCOPY:T` giữ nguyên **mtime** (tiền lệ milestone KHO-F: mtime lệch là sổ nghi file đổi).
- Trong `F:\AutoEdit` đã bao gồm: `library\` (kho footage) + `music\` + `sfx\` + `ambient\` +
  `cache.db` (SQLite mốc-lui — GIỮ, không xóa) + `backup\`.
- Xong đối chiếu nhanh: tổng số file + tổng dung lượng 2 bên phải khớp
  (`(Get-ChildItem F:\AutoEdit -Recurse -File | Measure-Object Length -Sum)` mỗi bên).
- **Tùy chọn** nếu máy mới cũng sẽ bàn giao cho editor: copy thêm `F:\BO_CAI_MAY_EDITOR\` và
  tạo `F:\BAN_GIAO_TU_EDITOR\` rỗng.

---

## §3. Copy SỔ PostgreSQL (khuyến nghị: pg_dump → restore, KHÔNG copy thô PGDATA)

> Phương án dump/restore an toàn hơn copy thô folder `D:\QQ SQL` (copy thô đòi đúng từng
> phiên bản binary + phải dừng service + dễ hỏng khó thấy; dump/restore luôn ra sổ sạch).
> Password của role `autoedit`: xem `~\.autoedit\machine.json::db_url` trên máy cũ —
> KHÔNG ghi vào file này.

**Trên máy gốc CŨ** (sau khi đã dừng job — §0.5):

```powershell
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -h localhost -U autoedit -d autoedit -F c -f "F:\AutoEdit\backup\pg\autoedit_full.dump"
```
(dump đặt trong `F:\AutoEdit\backup\pg\` → tự đi theo mẻ copy §2, khỏi chép riêng.)

**Trên máy gốc MỚI:**

1. Cài **PostgreSQL 17** (cùng đời major với máy cũ — installer từ postgresql.org/EDB).
   PGDATA đặt đâu tùy máy (máy cũ để `D:\QQ SQL` — khác đĩa kho là được). Nghe **LAN-only**
   y máy cũ: `listen_addresses` + `pg_hba.conf` chỉ mở dải LAN, KHÔNG mở internet.
2. Tạo role + database (nhập password CŨ để db_url các nơi giữ nguyên khuôn):
   ```powershell
   & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "CREATE ROLE autoedit LOGIN PASSWORD '<password cũ>';"
   & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "CREATE DATABASE autoedit OWNER autoedit;"
   ```
3. Restore:
   ```powershell
   & "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" -h localhost -U autoedit -d autoedit "F:\AutoEdit\backup\pg\autoedit_full.dump"
   ```
4. Kiểm: `psql -U autoedit -d autoedit -c "\dt"` thấy bảng; đếm 1 bảng chính (vd assets) so
   với máy cũ phải bằng nhau.

---

## §4. Cài phần mềm trên máy mới (y PHẦN B + C1/C1b hướng dẫn máy editor)

Cài tay: **Node.js LTS** → **VSCode** → **Claude Code** (extension + CLI global
`npm install -g @anthropic-ai/claude-code`, đăng nhập) → **CapCut** (ưu tiên đúng đời 8.8.0;
mở tạo 1 project trống làm donor cho §5).

Rồi mở VSCode → Open Folder `tool edit padoma` → Claude Code, dán:

```
Đây là MÁY GỐC MỚI nhân bản từ máy gốc PADOMA. Đọc HUONG_DAN_COPY_MAY_GOC.md, thực hiện
§4 (phần tự cài) → §5 → §6 tuần tự. Bước nào fail → dừng, báo nguyên nhân, KHÔNG nhảy bước.
```

Claude Code tự làm tiếp:
- Kiểm/cài `python` (≥3.11) · `git` · `ffmpeg` qua winget (C1 hướng dẫn editor).
- **MSVC C++ Build Tools** (bắt buộc — madmom build từ nguồn, C1b hướng dẫn editor).
- Trong `autoedit\`: `pip install uv` → `uv sync` → kiểm `uv run autoedit --help` +
  `uv run python -c "import madmom; print(madmom.__version__)"` → `0.17.dev0`.
- **Nạp memory:** copy toàn bộ `BAN_GIAO\memory_goc\` (kể cả `MEMORY.md`) vào thư mục memory
  của Claude Code trên máy mới (đường dẫn ghi trong system prompt phiên đó — slug theo
  username máy mới, KHÔNG bê nguyên path máy cũ). Thiếu bước này = mất toàn bộ bài học.

---

## §5. Tạo `machine.json` máy mới (chạy trong `autoedit\`)

```powershell
uv run autoedit register-machine --donor "<path draft trống vừa tạo trong %LOCALAPPDATA%\CapCut\...\com.lveditor.draft>"
uv run autoedit set-library-root "F:\AutoEdit\library"
uv run autoedit set-data-root "F:\AutoEdit"
uv run autoedit set-draft-root "<ổ local còn trống ≥100GB, vd E:\CapCut Drafts>"
uv run autoedit set-db-url "host=localhost port=5432 dbname=autoedit user=autoedit password=<password>"
```

(`set-db-url` tự test kết nối — fail là §3 chưa xong. Máy GỐC dùng `localhost`, khác máy
editor trỏ hostname.)

---

## §6. Kiểm tra nghiệm thu (theo thứ tự, fail bước nào dừng bước đó)

1. `uv run pytest -q` trong `autoedit\` — mốc 2026-07-21: **703 pass** (cao hơn nếu máy cũ
   đã thêm test). Fail hàng loạt → nghi số 1: ffmpeg thiếu PATH.
2. `uv run autoedit library-search` 1 query niche `deepsea` → trả kết quả path `F:\...`
   (chứng minh sổ Postgres + kho F: + chữ ổ đều đúng).
3. `uv run autoedit music-list` → liệt kê pool nhạc.
4. Smoke pipeline với folder mẫu đi kèm project:
   ```powershell
   uv run autoedit new --script "..\voice test travel\script.txt" --voice "..\voice test travel\voice.mp3" --channel travel
   uv run autoedit align <project_dir>    # lần đầu tải model whisper ~500MB — bình thường
   uv run autoedit direct-context <project_dir>
   ```
5. Dựng 1 video thật end-to-end → mở draft trong CapCut máy mới → **cổng MẮT + TAI do user
   quyết** (Claude không tự phán đạt). Draft xuất vốn PORTABLE nên mở được ngay.

---

## §7. Quyết định còn lại của USER (máy không tự chọn)

1. **GLM key:** máy mới dùng key riêng hay chung? Khuyến nghị RIÊNG nếu 2 máy chạy song song.
2. **Máy mới có THAY máy cũ làm chuẩn cho các máy editor không?** Nếu CÓ:
   - Editor đang trỏ sổ qua hostname `DESKTOP-98SCPHI`. Chọn 1 trong 2: đổi hostname máy mới
     thành đúng tên đó (máy cũ phải rời mạng trước), HOẶC chạy lại `set-db-url` trỏ hostname
     mới trên TỪNG máy editor.
   - Share lại ổ F: trên máy mới (tài khoản `editor1`, share name `F` — A1 hướng dẫn editor)
     và máy mới phải Sleep = Never (A2).
   - Máy cũ sau đó KHÔNG nạp kho/ghi sổ nữa (tránh 2 "chuẩn" lệch nhau).
   Nếu KHÔNG thay (2 máy gốc độc lập): chấp nhận kho + sổ 2 bên lệch dần từ ngày copy.
3. **Đồng bộ tri thức 2 chiều về sau:** chưa có cơ chế — tri thức mới (memory, NHAT_KY, code)
   phát sinh ở máy nào nằm máy đó. Cần thì dùng lại kênh `BAN_GIAO\` + git bundle như mô hình
   editor (PHẦN D hướng dẫn editor).
