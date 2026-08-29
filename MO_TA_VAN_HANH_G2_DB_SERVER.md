# MÔ TẢ VẬN HÀNH — G2: SỔ DỮ LIỆU LÊN DATABASE SERVER (PostgreSQL trên máy gốc, LAN)

> Trạng thái: **✅ DUYỆT 2026-07-15** — user ủy quyền ("không hiểu nhiều nên nhờ bạn kiểm tra
> kỹ, tự quyết định một cách cẩn trọng"), Claude tự rà vòng 2 (§8) và quyết GO. User chốt thêm:
> **BỎ hẳn VPS** (mọi thứ trong LAN) + dữ liệu Postgres đặt **`D:\QQ SQL`** (đổi từ F: cùng
> ngày sau khi hiểu rủi ro — hướng TỐT HƠN: D: không share nên khỏi khóa NTFS, và là đĩa vật
> lý khác kho footage nên không giành I/O lúc dựng).
> Tiền đề: G1 đã đóng (sổ SQLite dùng chung `F:\AutoEdit\cache.db`, backup tự động, luật 1-job).
>
> **Tiến độ: M1 ✅ · M2 ✅ · M3 ✅ · M4 ✅ ĐẠT 2026-07-16 — SỔ THẬT = POSTGRES, NHIỀU MÁY
> GHI SONG SONG, LUẬT 1-JOB ĐÃ GỠ.** M3: máy gốc flip + video thật DS1-086 dựng trọn trên PG
> + user duyệt mắt+tai. M4: máy editor đầu tiên nối qua hostname `DESKTOP-98SCPHI` (IP là
> DHCP) + test ghi song song 2 máy 600 lệnh 0 lỗi (`scripts\test_ghi_song_song.py`) + gỡ
> luật 1-job (HUONG_DAN + CLAUDE.md §7 cùng lúc). SQLite `F:\AutoEdit\cache.db` ĐÓNG BĂNG =
> mốc lui (`set-db-url --clear`). **Còn M5:** pg_dump hằng ngày → `F:\AutoEdit\backup\pg\`
> + dọn `AutoEdit.pre-G1-backup`.

---

## 1. Bài toán & quyết định đã chốt

G1 dùng chung 1 file SQLite qua ổ mạng SMB — chạy được nhưng **2 máy GHI đúng cùng lúc là vùng
rủi ro hỏng file** (giới hạn bản chất của SQLite trên ổ mạng, không sửa bằng code được). Vì vậy
đang phải giữ luật "2 máy không 2 mẻ nạp cùng lúc + giai đoạn đầu 1 job/lúc".

**G2 = chuyển SỔ (các bảng trong cache.db) sang PostgreSQL chạy trên MÁY GỐC.** Nhiều máy
đọc/ghi đồng thời an toàn tuyệt đối → gỡ hẳn luật 1-job, nhiều editor dựng + nạp song song.

**Vì sao máy gốc chứ không VPS (đã chốt 2026-07-15):** mỗi video bắn hàng nghìn truy vấn sổ —
LAN <1ms/truy vấn vs VPS internet 20–80ms (cộng dồn nhiều phút/video) + đứt mạng là đứng; kho
footage vốn nằm máy gốc nên máy gốc đằng nào cũng phải bật — server tại chỗ KHÔNG thêm điểm
chết mới. **User chốt BỎ hẳn VPS** — backup hằng ngày bằng pg_dump sang **ổ D:** (đĩa vật lý
KHÁC — E:/F: cùng 1 đĩa, dump để trên F: là chết chùm khi hỏng đĩa).

Kho FILE (footage/nhạc/SFX trên `F:\AutoEdit`) **không đổi** — vẫn SMB như G1. G2 chỉ dời SỔ.
**Dữ liệu Postgres (PGDATA): `D:\QQ SQL`** (user chốt, đổi từ F: 2026-07-15): D: KHÔNG share
(editor không thể đụng qua mạng — khỏi khóa NTFS) + đĩa vật lý KHÁC kho footage (E:/F: cùng
1 đĩa) → database không giành I/O với việc đọc footage lúc dựng; D: trống 385GB, db <1GB.
Backup đảo chiều: pg_dump hằng ngày → `F:\AutoEdit\backup\pg\` (vẫn đúng nguyên tắc 2 đĩa khác nhau).

```
                      MÁY GỐC (PADOMA)
              ┌───────────────────────────────┐
  MÁY EDITOR  │  PostgreSQL :5432 (LAN-only)  │
  ────────────┤    PGDATA = D:\QQ SQL (không  ├──► pg_dump hằng ngày
   dựng + nạp │    share) · db "autoedit" = SỔ│    → F:\AutoEdit\backup\pg\
  song song   │  F:\AutoEdit = kho FILE (SMB) │    (đĩa khác PGDATA)
              └───────────────────────────────┘
```

## 2. Phạm vi đụng chạm (đo 2026-07-15)

- ~**32 điểm gọi SQL / 10 file**: `library/db.py` (15 — trung tâm) · sourcer `usage/entity/
  pexels/local/breath/runner` · `library/stock_tags.py` · `library/dna.py` · `ambient/schedule.py`.
- **49 chỗ dính đặc sản SQLite / 11 file**: placeholder `?` · `INSERT OR REPLACE` · `executescript`
  · `PRAGMA`/`ALTER` trong `_migrate` · `sqlite3.Row` · hàm `lower()` Python tự cắm (Unicode
  tiếng Việt — Postgres lower() vốn chuẩn Unicode, khỏi cắm) · `LIKE` (SQLite mù hoa-thường
  ASCII, Postgres phân biệt → phải rà từng query).
- **531 test hiện có** dựng conn SQLite tạm ("mọi hàm nhận conn") — TÀI SẢN phải giữ nguyên.

## 3. Kiến trúc code: LỚP ĐỆM 2 LƯNG (dual-backend)

**KHÔNG bỏ SQLite.** Thêm lớp đệm mỏng trong `db.py`:

- `connect()` đọc cấu hình mới `db_url` (ưu tiên: env `AUTOEDIT_DB_URL` > machine.json
  `db_url` > **rỗng = SQLite tại data_root như G1** — đúng khuôn resolver 4 nấc đã có).
- `db_url` đặt → trả kết nối Postgres (psycopg) bọc shim: dịch placeholder `?`→`%s`, row truy
  cập theo tên như sqlite3.Row, `INSERT OR REPLACE`→`ON CONFLICT`, schema/migrate 2 nhánh.
- Lợi: **531 test cũ chạy SQLite y nguyên** (0 sửa test) · máy nào chưa trỏ db_url vẫn chạy G1
  · ĐƯỜNG LUI mọi lúc = xóa db_url.
- Giá phải trả (nói thẳng): 2 nhánh SQL phải nuôi — kiểm soát bằng bộ **test parity** (mục 4,
  M1) chạy CÙNG câu query lên cả 2 lưng, so kết quả.

> 📌 **LỆCH SO VỚI BẢN GỐC (M1 code 2026-07-15 — 3 điểm, đều theo hướng chắc hơn):**
> ① Shim KHÔNG dịch `INSERT OR REPLACE` bằng parse SQL (đoán conflict-target dễ sai) — 4
> callsite (pexels · entity serper/cse · stock_tags) viết lại thẳng `ON CONFLICT..DO UPDATE`,
> cú pháp CẢ 2 lưng hiểu (SQLite ≥3.24, Python 3.11 kèm 3.37+); 531 test cũ vẫn gác các query này.
> ② Bẫy MỚI bắt khi code: `REAL` của Postgres là float 4-byte (~7 chữ số) — mtime epoch ~1.7e9
> mất sạch phần lẻ → `needs_index` so 1e-6 sẽ bắt vision-tag lại oan CẢ KHO. Schema PG dịch
> `REAL` → `DOUBLE PRECISION` (parity test mtime precision gác).
> ③ Chốt an toàn thêm: `connect(db_path=...)` tường minh → LUÔN SQLite, không nhìn resolver —
> máy đã flip Postgres không kéo nổi 531 test cũ + script di trú sang sổ thật (có test guard).
> Test parity dùng env RIÊNG `AUTOEDIT_TEST_PG_URL` (db test), cố ý KHÔNG dùng AUTOEDIT_DB_URL.

## 4. Các mảnh & cổng (P4 — không nhảy cóc, mỗi mảnh có đường lui)

| Mảnh | Việc | Cổng đạt | Đường lui |
|---|---|---|---|
| **M0** | Mô tả này | user DUYỆT | — |
| **M1 — lớp đệm** ✅ 2026-07-15 | resolver db_url + shim psycopg + rà 32 điểm SQL (từng query: placeholder/LIKE/REPLACE) + **test parity** (mỗi hàm db chạy 2 lưng so kết quả, Postgres skip nếu không có server) + CLI `set-db-url`/`--clear` + tie-break `id DESC` 4 query chọn lọc | ✅ ĐẠT: FULL pytest **541 pass / 8 skip, 0 sửa test cũ** (8 skip = parity PG chờ server M2); parity lưng PG sẽ xanh nốt ở cổng M2 | chưa ai trỏ db_url — production không đổi gì |
| **M2 — dựng server + di trú dữ liệu** ✅ 2026-07-15 | PostgreSQL 17.10 service `postgresql-x64-17` Automatic + restart-on-fail, **PGDATA `D:\QQ SQL`**; pg_hba + firewall CHỈ `192.168.1.0/24` scram; role `autoedit`; db `autoedit` + `autoedit_test` (UTF8, **locale ICU** → lower() Unicode thật); `scripts\migrate_g2.py`: pre-flight typeof/NUL → copy 4 bảng GIỮ id + setval (chạy lúc 0 job) → verify 3 tầng; DSN keyword (password có `@!#` phá dạng URL) | ✅ ĐẠT: đếm khớp 100% (**34.196 asset · 5.167 usage · 4.555 search_cache · 1.205 stock_tags**) + mẫu 500 dòng/bảng × từng cột lệch 0 + 20 truy vấn chọn lọc thật × 4 niche 2 lưng giống hệt + FULL pytest **549/549 0 skip** (8 parity PG hết skip) | PG chỉ là bản sao — sổ thật vẫn SQLite (`--wipe` copy lại được từ đầu) |
| **M3 — máy gốc chuyển** ✅ ĐÓNG TRỌN 2026-07-16 | máy gốc `set-db-url` localhost → smoke backend postgres + count/search 4 niche khớp SQLite + pytest 549/549 sau flip; pg_dump mốc; **video thật DS1-086 orca** (deepsea music-sync, fan-out 11 agent sonnet, 298 beat) dựng TRỌN trên PG | ✅ SỐ: source 50,3' **0 lỗi db**, sổ PG ghi đúng qua shim (+325 asset_usage/319 search_cache/167 stock_tags) · ✅ **MẮT+TAI: user DUYỆT 2026-07-16** (draft `DS1_086_ORCA_20260716_024058`) | `set-db-url --clear` → SQLite (đã ĐÓNG BĂNG từ flip = mốc lui) |
| **M4 — editor vào + gỡ luật** ✅ ĐẠT 2026-07-16 | máy editor đầu tiên: `set-db-url` qua **hostname `DESKTOP-98SCPHI`** (IP là DHCP) đi đường LAN pg_hba/scram + **test ghi song song 2 máy** `scripts\test_ghi_song_song.py` (db `autoedit_test`, ghi qua shim thật: barrier tự đồng bộ qua PG → mỗi máy 200 insert khóa riêng + 100 upsert tranh chấp CÙNG khóa) + gỡ luật 1-job (HUONG_DAN A4.3/C6b/E/F/G + CLAUDE.md §7 sửa CÙNG LÚC) | ✅ 600 lệnh ghi đồng thời **0 lỗi**, mỗi máy thấy đủ 200/200 dòng máy kia, khóa tranh chấp không hỏng. 📌 LỆCH cổng gốc: thay "2 mẻ nạp + 2 video cùng lúc" bằng test ghi tổng hợp CÓ TRANH CHẤP (đụng độ sổ mạnh hơn); video song song thật = theo dõi vận hành (sự cố PHẦN F đỡ) | editor `set-db-url --clear` → G1 (chấp nhận lại luật 1-job) |
| **M5 — phụ, sau** | pg_dump hằng ngày → **`F:\AutoEdit\backup\pg\`** (đĩa vật lý khác PGDATA D:; VPS ĐÃ BỎ theo user); xóa `AutoEdit.pre-G1-backup` C: | backup tự chạy 7 ngày liền, khôi phục thử 1 lần thành công | — |

Ước lượng công: M1 lớn nhất (nửa ngày–1 ngày code+test), M2 nửa ngày, M3–M4 mỗi mảnh 1 buổi
kèm video test. Làm TUẦN TỰ, mỗi mảnh chờ user xác nhận như mọi milestone.

## 5. Rà chồng chéo (P5 — G2 đụng ai?)

- **G1 `data_root`**: KHÔNG gỡ — vẫn quản kho file + vị trí SQLite fallback. 2 tầng không
  ngược chiều: db_url quản SỔ, data_root quản FILE.
- **`backup_cache_db()` trước mẻ nạp (G1)**: giữ nguyên cho lưng SQLite; lưng Postgres dùng
  pg_dump (M5) — backup không chạy chéo lưng (backup SQLite khi đang chạy PG là backup mốc lui,
  vẫn đúng vai, không lật gì).
- **Luật 1-job / 2-máy-không-2-mẻ-nạp**: TẦNG BỊ GỠ — chỉ gỡ SAU cổng M4, sửa hướng dẫn +
  CLAUDE.md §7 cùng lúc (tránh 2 nguồn luật vênh nhau).
- **Họ luật LỌC-TRONG-SQL-trước-limit (FOOTAGE-084)**: mọi query port sang PG phải giữ NGUYÊN
  ngữ nghĩa lọc/limit — test parity chính là lưới bắt hồi quy này.
- **`connect(timeout=30)` (G1)**: chỉ nghĩa với SQLite; shim PG dùng timeout kết nối riêng — không đụng.
- **Bộ cài/bootstrap**: C6 thêm 1 lệnh khi M4 xong; trước đó editor mới vào vẫn chạy G1 bình thường.
- **Cổng tempo/music/pacing**: không đụng — G2 thuần tầng lưu trữ, KHÔNG đổi logic chấm/veto/pick.

## 6. Rủi ro thật & cách đỡ

| Rủi ro | Đỡ |
|---|---|
| 2 nhánh SQL trôi lệch theo thời gian | test parity chạy trong FULL suite (PG skip khi vắng server, máy gốc luôn có) |
| Pick đổi sau flip do ORDER BY hòa điểm khác nhau | M1 rà + thêm tie-break tường minh (id) cho query chọn lọc; M3 so pick 2 lưng |
| Postgres service chết → editor đứng | service auto-start + restart-on-fail; sự cố = xóa db_url về G1 trong 1 phút |
| Bảo mật cổng 5432 trong LAN | password + `pg_hba.conf` chỉ subnet văn phòng + firewall Windows; KHÔNG mở ra internet |
| Di trú sót dòng | verify đếm 100% từng bảng + so mẫu; sổ SQLite giữ nguyên làm chứng |
| Hỏng đĩa D: mất PGDATA | pg_dump hằng ngày sang F: (đĩa khác, M5); dump trên F: share bị xóa nhầm chỉ mất bản sao — PGDATA D: không share |

## 7. Việc cần từ user (khi bắt đầu M2)

1. Đặt password Postgres (tôi sinh gợi ý, anh giữ 1 bản).
2. Xác nhận subnet mạng văn phòng (để khóa firewall/pg_hba) — tôi tự dò rồi anh gật là được.

## 8. Kết quả TỰ RÀ vòng 2 (user ủy quyền duyệt — các điểm đã kiểm và chốt cách xử)

1. **Vị trí PGDATA:** bản đầu user chọn `F:\QQ SQL` — tôi bắt 2 rủi ro (ổ share quyền ghi →
   editor xóa nhầm được; cùng đĩa kho → giành I/O); user đổi sang **`D:\QQ SQL`** cùng ngày —
   sạch cả 2 rủi ro, khỏi cần khóa NTFS.
2. **E:/F: cùng đĩa vật lý** (sổ cũ kho-library-o-F) → PGDATA ở D: thì dump hằng ngày đảo
   chiều sang `F:\AutoEdit\backup\pg\` (vẫn 2 đĩa khác nhau).
3. **lower() tiếng Việt:** SQLite phải cắm hàm Python (db.py:131) vì lower() gốc chỉ hạ ASCII;
   Postgres lower() chuẩn Unicode sẵn — parity test M1 PHẢI có ca 'TƯ TRỊ'→'tư trị' để chứng minh.
4. **LIKE:** SQLite mù hoa-thường ASCII, PG phân biệt → M1 rà từng query LIKE, chuẩn hóa
   lower() hai vế (không dùng ILIKE — giữ 1 cú pháp chạy được cả 2 lưng).
5. **Transaction:** sqlite3 autocommit kiểu riêng, psycopg mặc định mở transaction → shim đặt
   autocommit tương đương + giữ nguyên các chỗ `conn.commit()` tường minh; parity test có ca
   ghi-rồi-đọc-lại.
6. **ORDER BY hòa điểm đổi pick:** M1 thêm tie-break `id` tường minh vào các query chọn lọc
   (search_assets/signature/find_*) — sửa này áp cho CẢ lưng SQLite nên phải qua FULL pytest.
7. **Password nằm plaintext trong machine.json (db_url):** chấp nhận trong LAN văn phòng —
   ngang mức `.env` hiện tại; KHÔNG mở 5432 ra internet.
8. **Đa luồng:** giữ nguyên kỷ luật "SQLite main thread" hiện có cho conn PG (tag_jobs vốn đã
   dồn ghi về main thread từ PB4) — không nới trong G2.
