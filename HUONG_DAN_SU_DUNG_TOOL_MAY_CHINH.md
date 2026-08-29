# HƯỚNG DẪN SỬ DỤNG TOOL — MÁY CHÍNH (PADOMA)

> File anh em: `HUONG_DAN_SU_DUNG_TOOL.md` (bản cho editor — chỉ dựng video). File này
> dành cho **máy chính** (máy của bạn) — làm MỌI VIỆC máy editor không làm: mở niche mới,
> nạp kho, cấu hình máy, bàn giao/nhân bản máy, ghi chép hệ thống.
>
> **Vẫn thao tác qua trò chuyện với Claude Code** như máy editor — khác biệt là máy chính
> còn được giao thêm các việc "hậu trường" dưới đây mà máy editor không nên tự làm.

---

## 0. Máy chính khác máy editor ở đâu

```
MÁY CHÍNH (bạn)                                  MÁY EDITOR
chuẩn tri thức — mọi quyết định/luật mới          vận hành hằng ngày: chỉ dựng video
mở niche, nạp kho, nạp nhạc/SFX                   (xem HUONG_DAN_SU_DUNG_TOOL.md)
cấu hình máy, bàn giao, nhân bản
ghi chép: NHAT_KY_BUILD.md + memory + BAN_DO_TRI_THUC.md
```

Dựng 1 video trên máy chính giống **hệt** máy editor — xem `HUONG_DAN_SU_DUNG_TOOL.md`,
không lặp lại ở đây.

---

## 1. Cài đặt / đăng ký máy (chỉ 1 lần, hoặc khi máy đổi ổ đĩa)

Chi tiết đầy đủ từng bước (Python, `uv sync`, `.env`, thư mục dữ liệu) ở
`autoedit/CLAUDE.md` mục "WINDOWS SETUP" — nói Claude Code "setup máy" là nó tự chạy hết.
Tóm tắt việc cần có sau khi xong:

| Việc | Vì sao | Chạy lại khi nào |
|---|---|---|
| `uv sync` + `.env` điền API key | Cài dependency + key Pexels/GLM/Serper | Chỉ 1 lần/máy |
| `register-machine` | Đọc 1 draft CapCut thật trên máy để biết version/path CapCut | 1 lần/máy, và **sau mỗi lần CapCut tự update** |
| `demo-draft` | Sinh 1 draft test — mở CapCut kiểm không đen/không relink | Sau `register-machine` và sau mỗi update CapCut |

---

## 2. Cấu hình đường dẫn máy (mỗi máy 1 lần, ghi vào `machine.json` — nhớ vĩnh viễn)

| Lệnh | Đặt cái gì | Khi nào cần |
|---|---|---|
| `set-library-root <folder>` | Gốc thư viện footage (mỗi niche 1 folder con) | Máy có ổ riêng chứa kho footage (vd `F:\FOOTAGE`) |
| `set-draft-root <folder>` | Nơi xuất draft CapCut mới (vd `E:\CapCut Drafts`) | Muốn draft ra ổ khác thay vì folder CapCut mặc định |
| `set-data-root <folder>` | Gốc dữ liệu chung: sổ tag (`cache.db`) + nhạc + SFX (vd `F:\AutoEdit`) | Nhiều máy cùng dùng chung 1 kho qua LAN (mô hình máy editor) |
| `set-db-url <postgres-url>` | Sổ chuyển từ SQLite → PostgreSQL trên máy chính | Muốn nhiều máy **ghi sổ đồng thời an toàn** (dựng song song) — `--clear` để lùi lại SQLite |

Sau `set-draft-root`, nhớ trỏ **CapCut → Settings → Draft location** cùng folder đó thì mới
thấy draft mới xuất hiện trong CapCut.

---

## 3. Mở niche/kênh mới

Việc này có checklist riêng, giao thẳng cho Claude Code làm hộ theo
**`HUONG_DAN_NAP_NICHE_MOI.md`** — bạn chỉ cần chuẩn bị: tên niche, folder video mẫu editor
thật (càng nhiều draft càng chuẩn), có music-sync/world-lock/nhạc riêng hay không (không rõ
thì để Claude Code đề xuất). Bên trong, Claude Code sẽ tự chạy các lệnh nạp/học kho
(`editor-learn`, nạp ambient, viết `subject_rules.yaml`...) theo đúng 7 bước trong file đó —
bạn không cần nhớ lệnh, chỉ cần **gác đúng các mục "Gác" ghi trong file** (vd file
`subject_rules.yaml` thiếu = SFX rơi về bảng mặc định sai loài, bài học life-in).

---

## 4. Nạp thêm dữ liệu vào kho đã có (video mẫu, nhạc, SFX)

### 4.1. Nạp thêm video mẫu (viral hoặc của công ty) vào 1 niche đã mở
Nói với Claude Code: niche nào + đường dẫn folder draft CapCut đã tách cảnh. Nó sẽ chạy
`library-ingest <niche> "<folder draft>"` — mặc định `--source-class own` (kho công ty);
video mẫu của **kênh khác** phải nói rõ để khai `--source-class viral` (áp luật bóp/zoom/
điểm nhô riêng cho nguồn ngoài — người khai quyết, máy không tự suy).

> Nếu chỉ để dùng **1 lần cho đúng 1 bài** (không cần nạp hẳn vào kho) — đó là việc của PHA 1
> dựng video (`--ref`), không phải mục này. Xem `HUONG_DAN_SU_DUNG_TOOL.md` mục 4.1.

### 4.2. Nạp nhạc nền / SFX / ambient
Editor có thể **lọc file + đặt tên** theo đúng quy ước (`HUONG_DAN_EDITOR_GOM_SFX_NHAC.md`),
nhưng **nạp vào tool** là việc máy chính: nói với Claude Code folder vừa gom, nó chạy
`music-import`/`sfx-import`/`ambient-import` tương ứng. Tên file sai quy ước (thiếu `__mood`,
mood tự chế...) → tool bỏ qua im lặng, nên kiểm lại theo bảng mood trong file gom trước khi nạp.

---

## 5. Ghi công kênh nguồn (khi kho đã có video mẫu nhiều kênh khác nhau)

- `channel-audit` — liệt kê folder nguồn nào **chưa** gán tên kênh.
- `channel-set "<prefix folder/file>" "<Tên Kênh>"` — điền tay (mẻ viral có YouTube ID thì
  tool tự lấy tên kênh qua yt-dlp, chỉ cần điền tay phần còn thiếu).

Chỉ cần khi bật `--credit` lúc dựng video (ghi công kênh nguồn trên footage).

---

## 6. Bàn giao / vận hành máy editor

Xem toàn bộ quy trình ở `HUONG_DAN_CAI_DAT_MAY_EDITOR.md`. Việc lặp lại mỗi khi máy chính
sửa bug/thêm luật MỚI (không chỉ lần bàn giao đầu):
1. Mirror memory file mới/sửa vào `BAN_GIAO\memory_moi\`.
2. Thêm entry vào `BAN_GIAO\NHAT_KY_MAY_EDITOR.md`.
3. `git commit` rồi `git bundle create BAN_GIAO/padoma_editor.bundle --all`.

Đây là **kênh DUY NHẤT** đưa tri thức mới sang máy editor — bỏ bước này là tri thức mất khi
gộp máy. Dựng video song song nhiều máy là AN TOÀN (sổ Postgres dùng chung) — chỉ tránh 2 máy
cùng nạp kho vào **cùng 1 niche** đúng lúc.

---

## 7. Nhân bản toàn bộ máy chính sang máy chính khác

Khác bàn giao máy editor (máy editor dùng CHUNG kho qua LAN) — nhân bản máy chính tạo ra
**kho riêng + sổ Postgres riêng + code riêng**, xem đầy đủ ở `HUONG_DAN_COPY_MAY_GOC.md`
(3 khối phải mang: code+memory, sổ PostgreSQL, kho `F:\AutoEdit`). Lưu ý: đây là ảnh chụp 1
thời điểm — 2 máy chính sau khi tách sẽ lệch kho/sổ dần theo thời gian, không tự đồng bộ lại.

---

## 8. Hệ thống ghi chép bắt buộc (sau MỌI tính năng mới / bug fix / nâng cấp)

1. **`NHAT_KY_BUILD.md`** — cập nhật bảng milestone + entry (đổi gì / vì sao / verify / số pytest).
2. **Memory Claude Code** (`~/.claude/projects/.../memory/`) — 1 file/quyết định sâu +
   1 dòng index vào `MEMORY.md`.
3. **`BAN_DO_TRI_THUC.md`** — thêm dòng khi tìm ra nguồn kiến thức mới (module cũ dùng lại được).
4. **`git commit`** local sau mỗi milestone đạt (KHÔNG push GitHub — chỉ backup máy).

Đây không phải việc "làm cho có" — đây là nguồn sự thật duy nhất khi bàn giao/nhân bản máy
(mục 6–7 ở trên đều đọc lại từ đây).

---

## 9. Sự cố thường gặp riêng của máy chính

| Hiện tượng | Xử lý |
|---|---|
| `source` báo thiếu `PEXELS_API_KEY` | Kiểm `.env` trong `autoedit/` đã điền key thật chưa |
| `channel-audit` báo nhiều folder chưa gán kênh | Bình thường nếu chưa `--credit` bao giờ — chỉ cần điền trước khi bật ghi công |
| `set-db-url` báo "đã lưu nhưng CHƯA kết nối được" | Kiểm PostgreSQL service đã chạy (`postgresql-x64-17`) — vẫn lưu URL, chỉ chưa dùng được ngay |
| 2 máy cùng nạp 1 niche cùng lúc | Không hỏng sổ (Postgres ghi đồng thời an toàn) nhưng nên so le tay để đỡ trùng việc — xem `HUONG_DAN_CAI_DAT_MAY_EDITOR.md` A4.3 |
