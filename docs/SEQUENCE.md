# SEQUENCE — New Sequence: luồng, tham số, thứ tự việc

> **Tài liệu SỐNG** — mọi kết luận đã chốt về New Sequence nằm ở đây.
> Thay thế `FLOW_NEW_SEQUENCE_V2.md` (bản chốt sáng 07/09, giữ lại để truy vết;
> bảng "Auto = 0" trong đó **SAI**, xem PH4).

## Bảng mốc

| Ngày | Chốt gì | Ai quyết |
|---|---|---|
| 06/09 | AVD chia hai hệ: chương đồng kiểm / chương auto · Auto không đốt Envato | user |
| 07/09 sáng | Cấu trúc phẳng + `Rec/` · 3 kiểu chạy · bỏ ép nhịp Padoma · form 6 ô | user |
| 07/09 chiều | Rà lại bằng số → **chèn bậc 0 "nối ống"**, hoãn đổi tên package, chia hình bắt đầu bằng 2 con số | user duyệt sau phản biện |
| 07/09 tối | Bậc 0 XONG (`3c5af46`) · bậc 1 XONG · gom hết ở cổng dev rồi mới đẩy production một lượt | user chốt |
| 07/09 khuya | Bậc 2 + vá nhãn ref (`3e4277b`) · 3a (`ccf16b4`) · 3b (`b9504b3`) · **bậc 4 + 5 XONG** — hết 5 bậc | user: "cố gắng done app tối nay" |

---

## Luồng thật hôm nay (đọc từ mã, không từ trí nhớ)

```
Nộp tập -> 1 JOB cho CẢ TẬP -> make --chi-chuan-bi (align + voice_master, KHÔNG dựng)
                               \-> nạp ref của tập, chạy nền
Người bấm "Phân tích" TỪNG chương -> offline/runner.phan_tich():
    cắt KHỐI theo HƠI THỞ (im lặng >= 0,5s)          khoi.py
    4 lớp nghĩa (GLM) + dịch tiếng Việt              lop4 / dich   (fail-open)
    đổ ứng viên từ Library (rào geo + rào tập)       dung.do_ung_vien
    DẢI HÌNH sinh 1-1 với khối                       hinh.sinh_tu_khoi
-> pha1 -> người duyệt/chẻ/khoá sổ -> Online -> draft CapCut
```

**Điểm mấu chốt:** nhịp của video được quyết ở **dải HÌNH**, mà dải hình hiện
sinh 1-1 từ hơi thở người đọc voice. Framing Insight không tham gia vào đó.

---

## Năm phát hiện đo được 07/09 — nền của mọi việc phía dưới

### PH1. Tham số dựng RỚT SẠCH với job nhiều chương (bug đang sống)

`web/worker.py:234` ghi `project_id=",".join(ids)` — job LI103 có `project_id`
là chuỗi **326 ký tự** nối 17 mã chương. `web/server.py:751` lại tra
`WHERE project_id=?` bằng **một** mã chương.

| Tra thử | Kết quả |
|---|---|
| `c2-20260907-050547` (LI103, nộp cả tập) | **KHÔNG KHỚP** |
| `h-20260905-104130` (nộp lẻ 1 chương) | khớp job 19 |

Job 21 có `kenh_ref='godoc-travel-doc'`, `avd_phut=7`, `uu_tien_nguon='ref'`.
Hợp đồng sinh ra: `framing: {}`, `dong_kiem: True`. **Mất im lặng.**

Hậu quả thật trên LI103: cả 17 chương phải người duyệt (AVD 7 phút vô hiệu) ·
ref vừa nạp 69 phút không được cộng điểm ưu tiên · rào địa danh không bật
(`geo_tap` rỗng thì `tra()` không lọc gì).

### PH2. Framing Insight: bắt buộc nhập, gần như không tác dụng

Cả hồ sơ kênh chỉ dùng **một** số `than_trung_vi`, và chỉ để bật một cờ gợi ý:
`goi_y_che = (dài khối) > than × 1,6` (`offline/khoi.py:88`).
Đếm trên 4 hợp đồng thật: cờ đó bật **0 lần**.
`nhip_curve` (24 bucket), `hold`, `hook_kieu`, `bung_chu_ky_s` — đo xong, cache
xong, **không ai đọc**.

### PH3. Nhịp hiện tại là nhịp thở người đọc voice, không phải nhịp kênh

| Hợp đồng | Framing | Median khối | p90 | Dài nhất | Hình/Khối |
|---|---|---|---|---|---|
| LI103 · C2 (07/09) | `{}` | **2,18s** | 3,69 | 4,74 | 43/43 |
| LI104 · C7 | `{}` | **3,82s** | 9,56 | **18,19s** | 32/30 |
| LI104 · C8 | `{}` | **4,08s** | 8,59 | 13,92s | 34/34 |
| H (05/09) | godoc `than 4,73` | 2,86s | 5,19 | 5,90 | 22/17 |

Chênh gần **2×** giữa hai tập; một chương có shot **18 giây**. Đây đúng căn
bệnh `nhip/ep.py` sinh ra để chữa ở pipeline cũ (docstring ghi: đo 02/09 hai
chương cùng tập ra nhịp cụm 6,5× và 2,3×). Đường Offline thừa hưởng nguyên căn
bệnh vì bỏ tầng ép mà chưa dựng tầng thay thế.

### PH4. "Auto = 0" SAI so với mã

```python
dong_kiem = (avd_s <= 0) or (mo_dau_tap_s < avd_s)     # offline/runner.py:189
```

`avd_s = 0` → **Manual toàn tập**. `∞` → cũng Manual. **Auto không biểu đạt
được bằng bất kỳ con số nào.** Sửa bằng cách bỏ sentinel, dùng ô riêng (QĐ1).

### PH5. Cấu trúc phẳng sẽ làm hỏng thêm một chỗ nữa

`web/server.py:724 _mo_dau_tap_s()` duyệt `ch.path.iterdir()` tìm audio **trong
thư mục chương**. Phẳng → không thấy → `return 0.0` → mọi chương đồng kiểm →
Auto chết, không báo. Kế hoạch cũ liệt kê 5 chỗ, **thiếu đúng chỗ này → 6 chỗ**.

---

## Quyết định đã chốt 07/09 chiều

**QĐ1 — Ba kiểu chạy khai báo TƯỜNG MINH, không dùng sentinel.**
Ô `kieu_chay` = `manual | avd | auto`; `avd_phut` chỉ có nghĩa khi
`kieu_chay='avd'`. Lý do: `avd_s=0` đang mang hai nghĩa chồng nhau ("chưa khai"
và "Auto") — chính là cách đẻ ra PH4.

**QĐ2 — "Bỏ `nhip/ep.py`" là mô tả SAI việc, không làm.**
File đó đường Offline **không hề dùng**; chỉ pipeline cũ gọi (4 chỗ:
`cutter/runner`, `music/plan`, `nhip/do_draft`, `packager/assembler`). Xoá =
phá đường dự phòng của team, đổi lại không được gì. Việc thật là **THÊM** tầng
chia dải hình theo Framing.

**QĐ3 — Chia hình bắt đầu bằng HAI con số, chưa dùng đồ thị nhịp.**
Dùng `than_trung_vi` (chẻ khối dài) + `than_ty_le_hold` (chừa phần giữ lâu).
Chưa dùng `nhip_curve` vì nó mô tả nhịp **theo vị trí trong video hoàn chỉnh** →
muốn áp phải biết chương nằm ở phút thứ mấy của tập — đúng con số đang hỏng
(PH1) và sắp hỏng lại (PH5). Không xây thứ tinh vi lên trên số chưa đáng tin.

**QĐ4 — Hoãn đổi tên package `autoedit` → `rendery`.**
Rủi ro pháp lý nằm ở **cái người ngoài nhìn thấy** (nhãn hiển thị, tài liệu,
chuỗi "PADOMA") — phần đó rẻ, làm khi rảnh. Tên thư mục code bên trong không ai
thấy; đổi nó chạm 148 file, có 3 chỗ gọi nhau bằng **chuỗi** (`"-m",
"autoedit.cli"`), và xong xuôi thì tool vẫn chạy y hệt. Team đang chờ dùng.

**QĐ5 — Auto phải ĐO trước khi hứa.**
Auto loại Envato → chỉ còn ref + kho + Pexels/Pixabay. Máy đã có chốt an toàn:
khay phủ < 50% khối thì Auto **không tự khoá sổ**. Nếu tỉ lệ thật dưới ngưỡng,
ca đêm chạy xong **không giao gì** — vẫn mất buổi sáng, đúng rủi ro mà việc bỏ
Envato định tránh.

---

## Thứ tự việc — 5 bậc, mỗi bậc một cổng bằng SỐ

| Bậc | Làm gì | Cổng nghiệm thu |
|---|---|---|
| ✅ **0. Nối ống + cây thước** | tham số về **hồ sơ chương** (`project.json`), bảng `jobs` chỉ còn lưới đỡ — không đụng schema `jobs` nên pipeline cũ ở cổng riêng không hề hấn · thiếu `kenh_ref` → cảnh báo đỏ trong hợp đồng, không chạy im · lệnh `kiem-hop-dong` in bảng đo | Phân tích lại 1 chương LI103 → hợp đồng có `framing.ten='godoc-travel-doc'`, `avd_s=420`, địa danh đúng |
| ✅ **1. Ô Kiểu chạy** | enum `manual/avd/auto` trong hồ sơ chương; `dong_kiem` suy từ enum ở **một hàm duy nhất** `tinh_dong_kiem()`; giá trị lạ thì DỪNG | 3 kiểu × chương giữa tập (mở ở phút 10, mốc 7 phút) → `dong_kiem` đúng cả 3 · `manual` và `auto` cùng `avd_s=0` vẫn ra hai kết quả khác nhau (chỗ bản cũ bó tay) |
| ✅ **2. Đo Auto** | `kiem-hop-dong --nhu-auto` — tra lại Library bỏ Envato, dùng lớp nghĩa ĐÃ LƯU nên không gọi lại LLM | đo 5 hợp đồng thật: **0/5 dưới ngưỡng 50%**, xem kết quả bên dưới |
| ✅ **3a. Chẻ khối dài theo Framing** | `hinh.che_mot_khoi`: khối > 1,6×`than` chẻ thành `round(span/than)` miếng, **né về ranh mềm có sẵn**, chừa quota `hold`, sàn 0,7s, trần giữ 2,5×. KHÔNG đụng dải voice | C7: shot dài nhất 18,4s → **10,4s**, lệch −7% → **−4%** · C8: 14,7s → 11,7s, +1% → −4% · không còn miếng > 12s |
| ✅ **3b. Cho clip CHẢY TIẾP qua ranh khối** | luật chọn phân biệt "lặp" (cấm) với "chảy tiếp" (cho); chỗ ráp cắt tiếp đúng chỗ miếng trước dừng, **đo file thật** trước khi cho tiếp | C2 đo thật: 43 → **33 shot** · median 3,24s → **4,57s** · lệch −32% → **−3%** · clip phải tải 36 → 31 |
| ✅ **4. Cấu trúc phẳng** | `Chuong` mang thẳng `script/voice/srt` · `doc_chuong` thêm nhánh gom file lẻ · `make --script/--voice` · worker truyền file khi chương phẳng · `_mo_dau_tap_s` nhận cả hai kiểu | tập phẳng dựng từ file thật LI103 → 5 chương đúng thứ tự, `ref 1.mp4` không bị nhầm là voice · kiểu thư mục chạy y hệt · có cả hai kiểu → thư mục thắng, không nhân đôi · gộp 1 voice cả tập → vẫn chặn |
| ✅ **5. Form 6 ô** | bỏ "Phương án dựng" · ô **Kiểu chạy** 3 lựa chọn, ô mốc AVD nằm TRONG lựa chọn AVD Mode · nhãn "Kênh / niche" → **Niche** · form luôn gửi `chi_chuan_bi=true` (3 kiểu chung một đường Offline) | form thật trên cổng dev phục vụ đúng 3 lựa chọn + nhãn Niche; 4 test khoá hành vi + `test_smoke_ui` xanh |

### Bậc 4 — 6 chỗ, và chỗ thứ 6 là chỗ kế hoạch cũ bỏ sót

| Chỗ | Sửa gì |
|---|---|
| `chapters.Chuong` | thêm `script`/`voice`/`srt` + cờ `phang`; kiểu thư mục để None (make tự dò như cũ) |
| `chapters.doc_chuong` | thêm nhánh `_chuong_phang` gom file lẻ theo tên; **chỉ chạy khi không có thư mục chương** → có cả hai kiểu thì thư mục thắng |
| luật "gộp cả tập" | file phẳng đúng quy ước KHÔNG bị tính là gộp; `ref *.mp4` không bị nhầm là voice |
| `cli.make` | `--script`/`--voice` tường minh; title lấy từ tên file (`C1`) chứ không phải tên thư mục (`RenderY`) |
| `worker` | `chapters_of` trả `Chuong`; chương phẳng thì truyền file thẳng — để `make` tự dò trong thư mục chứa 17 chương là vớ nhầm |
| **`server._mo_dau_tap_s`** | **chỗ kế hoạch cũ THIẾU (PH5)** — chương phẳng nhận theo tên file voice thay vì tên thư mục. Hỏng ở đây là Auto chết mà không báo |

### Vì sao cần 3b — chẻ thôi chưa đủ (đo 07/09 tối)

Chẻ chỉ chữa được chương có khối DÀI. Chương C2 của LI103 lệch −32% vì khối quá
NGẮN: median khối 2,18s trong khi kênh giữ shot 4,73s — không có gì để chẻ.

Gốc bệnh không nằm ở chỗ chia dữ liệu mà ở **luật chọn**: điều "cùng một clip
không xuất hiện 2 lần trong 60s" (chống lặp) vô tình ép **đổi hình mỗi hơi thở**.
Người đọc thở 2,2s/lần thì video cắt 2,2s/lần, bất kể kênh ref giữ 4,7s.

Ba đường đã cân (user chọn C, 07/09 tối):

| | Cách | Vì sao chọn / bỏ |
|---|---|---|
| A | Giữ nguyên | Đúng cái bệnh đang chữa — bỏ |
| B | Cho 1 miếng trải nhiều khối | Đúng mô hình nhưng **phá bất biến "mỗi khối luôn có ≥1 miếng"** — bất biến sinh từ lỗi thật 08/09, đang gánh toàn bộ logic nút +/−1s. Không đụng |
| **C** | **Clip chảy tiếp qua ranh khối** | Bất biến còn nguyên, UI không phải sửa. Chỉ đổi luật chọn + chỗ ráp |

Đo trên C2: **43 shot → 32 shot · median 3,24s → 4,71s (lệch 0%) · số clip phải
tìm/tải giảm 26%** (ít lượt Envato, ít ô placeholder).

Giới hạn đã lường: chỉ chảy tiếp được khi clip nguồn CÒN ĐỦ DÀI; clip 3s không
kéo thành 4,7s — khi đó vẫn đổi hình như cũ.

**Hai chỗ chặn lộ ra khi chạy thật (07/09 tối) — bản đầu KHÔNG chảy tiếp lần nào:**

| Chặn | Đo được | Sửa |
|---|---|---|
| Điều kiện "nguồn còn đủ dài" | **39/39** clip kho **không ghi `dai_s`** → luôn coi như hết nguồn | Lạc quan lúc CHỌN, **đo file thật lúc RÁP** (`con_du_nguon`); hụt thì quay về clip riêng |
| Điều kiện "clip phải có trong khay khối kế" | chỉ **8/39** chỗ có — mỗi khối tra Library bằng từ khóa riêng | Chảy tiếp là quyết định về TIMELINE, không phải về khay → đưa clip đang chiếu vào **đầu khay** khối đó, editor thấy đúng thứ đang chiếu và đổi được |

Kèm theo, vá một lỗ do chính 3a tạo ra: miếng chẻ thêm trước đó **không có clip
nào** → mỗi lần chẻ là một lỗ trên timeline. Nay miếng chẻ là phần chảy tiếp của
chính clip đang chiếu, và vẫn giữ khay để nếu chảy tiếp hụt thì còn clip đắp.

### Kết quả bậc 2 — Auto có giao được hàng không? (đo 07/09 tối)

Đo bằng `kiem-hop-dong --nhu-auto` trên 5 hợp đồng thật (4 production + 1 dev):

| Chương | Đồng kiểm | Nếu AUTO (bỏ Envato) | Mất |
|---|---|---|---|
| LI103 · C2 (prod) | 42/43 · 98% | **42/43 · 98%** | 1 khối |
| LI103 · C2 (dev, có Framing + geo) | 43/43 · 100% | **41/43 · 95%** | 2 khối |
| LI104 · C7 | 30/30 · 100% | **19/30 · 63%** | **11 khối** |
| LI104 · C8 | 33/34 · 97% | **33/34 · 97%** | 0 |
| H (05/09) | 17/17 · 100% | **15/17 · 88%** | 2 khối |

**Phủ trung bình 87% · 0/5 chương dưới ngưỡng 50%.**

**Kết luận cho QĐ5:** nỗi lo *"ca đêm chạy xong sáng ra trắng tay"* **KHÔNG đúng**
— mọi chương đo được đều vượt xa ngưỡng tự khoá sổ, tức Auto sẽ giao timeline.

**Nhưng đừng đọc thành "Auto ngang đồng kiểm".** Vượt ngưỡng chỉ nghĩa là máy
CHỊU giao; khối mất ứng viên vẫn rơi về placeholder. Chương nào tựa nhiều vào
Envato thì hụt thật: C7 rớt từ 100% xuống 63%, mất 11/30 khối. Chương tựa vào
`kho`/`ref` (C8, C2 của LI103) gần như không suy suyển.

→ Auto dùng được cho ca đêm. Chỗ cần theo dõi là **chương nào đang sống nhờ
Envato** — chạy `--nhu-auto` trước khi bật đêm là biết ngay.

### PH7. Suất giữ chỗ REF lấy nhầm tập — khay ref RỖNG (user bắt 07/09 khuya)

Chạy thật chương H của LI103: panel "REF CỦA TEAM" trắng trơn, dù kho có 1.995
cảnh ref của tập, **1.768 cảnh khớp từ khoá**.

Không phải rào geo (ref LI103 đều mang geo `afghanistan`), cũng không phải rào
tập (luật "ref tập khác không sang tập này" viết đúng). Thủ phạm là câu lấy ref:

```sql
SELECT * FROM clip WHERE nguon='ref' AND trang_thai='song' LIMIT 600
```

**Không lọc tập, không sắp xếp** → lấy 600 dòng ĐẦU BẢNG, mà đầu bảng là tập nạp
TRƯỚC. Đo: 600 dòng đó **toàn LI100**. Ref LI103 nằm ngoài cửa sổ, không bao giờ
được xét; rồi rào tập loại nốt LI100 → khay trống.

Cơ chế giữ chỗ này sinh ra để ref khỏi bị FTS bỏ rơi, và **đúng khi kho có MỘT
tập**. LI103 là tập thứ hai nên vỡ — nghĩa là nó vỡ đúng lúc kho bắt đầu có giá
trị. Vá: lọc theo tập ngay trong câu lấy.

Đo lại trên kho thật, chương H: khối 1 · 5 · 10 đều từ **ref 0 → ref 2**.

> Test lần đầu XANH GIẢ vì kho giả quá nhỏ (mọi thứ lọt cửa sổ). Phải làm đầy
> CẢ HAI cửa sổ (800 của FTS + 600 của suất giữ chỗ) mới tái hiện được lỗi.

### PH6. Footage ĐÃ GIAO bị ghi vào Library dưới nhãn `ref` (sửa 07/09 tối)

`nap_ref_tap` quét `rglob("*.mp4")` — mọi file mp4 nằm sâu bất kỳ trong thư mục
tập — nên nuốt luôn thư mục kết quả do chính tool sinh ra.

| Nằm ở | Cảnh ghi sai | Là gì |
|---|---|---|
| `Compose Timeline/*/draft/materials/` | 42 | footage đã tải, đóng vào draft |
| `Compose Timeline/*/footage/` | 79 | footage đã tải, giao cho editor |
| **Tổng trên kho production** | **121** | toàn bộ của LI103, tên `b###_…` |

Soi từng dòng: **không một ref thật nào** nằm trong nhóm này. Hai cái sai: tốn
GLM đọc lại hình clip vốn đã ở trong kho, và **sổ nguồn gốc ghi sai** — clip mua
Envato thành "phim mẫu của tập", đúng chỗ dự án đụng ranh giới pháp lý.

**Vá:** chỉ nhận file tên `ref*` và không chui vào thư mục kết quả — đúng luật
đã chốt sáng 07/09 (*"`ref *.mp4` ở gốc"*). Đo trên thư mục thật: LI103 nhận
đúng 5 ref / loại 73 file; LI104 nhận 0 / loại 224 (tập đó vốn không có ref —
khớp điều user báo ở LI104).

**Dọn:** lệnh `don-ref-nham` (mặc định CHỈ LIỆT KÊ, `--xoa` mới gỡ). Đã dọn 121
cảnh trên kho dev; **file video không bị đụng**, chỉ gỡ dòng sổ + ảnh thu nhỏ do
Library sinh. Kho production dọn khi đẩy bản này sang.

> 4 test cũ đỏ vì fixture đặt tên `r.mp4` — không theo quy ước. Đổi tên fixture
> cho khớp luật thật, KHÔNG nới luật để chiều test.

### Điều chỉnh phạm vi bậc 1 (07/09 tối)

Việc *"tính mốc bắt đầu chương không phụ thuộc hình dạng thư mục"* chuyển sang
**bậc 4**: nó dính chặt với cấu trúc phẳng, làm sớm là sửa mù rồi sửa lại. Bậc 1
chỉ giữ phần khai báo kiểu chạy — và thêm một chỗ **chạy thật mới lộ ra**:

> `make` có nhánh "chương này chuẩn bị rồi — dùng lại" và nhánh đó `return` sớm,
> nên tham số mới KHÔNG tới đâu. Nộp lại tập sau khi sửa Framing/AVD thì chương
> cũ giữ nguyên số cũ, im lặng — đúng họ nhà lỗi PH1. Nay cả hai nhánh gọi chung
> `_gan_tham_so_dung()` (BH4: một khái niệm, một hàm). Cũng vì `return` sớm mà
> giá trị `--kieu-chay` sai lọt qua khâu kiểm; nay kiểm TRƯỚC nhánh dùng lại.

**Chưa làm:** đổi tên package (QĐ4) · xoá `nhip/ep.py` (QĐ2) · overlay/SFX ·
kế hoạch "nạp tiếp" 5 đợt (`KE_HOACH_NAP_TIEP_TAP.md` — dự phòng đường dài).

---

## Cấu trúc thư mục nhận vào (giữ nguyên chốt 07/09 sáng)

```
RenderY/
  H.mp3  H.txt · C1.mp3 C1.txt … C15 · E.mp3 E.txt   <- chương, đặt PHẲNG
  ref 1.mp4  ref 1.srt …                             <- ref cả tập
  Rec/                                               <- footage tự quay
```

| Nằm ở | Là gì | Vào Library với |
|---|---|---|
| `ref *.mp4` ở gốc | phim mẫu của tập | `nguon='ref'` |
| trong `Rec/` | footage tự quay | `nguon='kho'` |
| `H` / `C<số>` / `E` + `.txt`+`.mp3` | chương | (không vào Library) |
| file lẻ khác | bỏ qua | — |

**Bắt buộc nhận CẢ HAI kiểu**: tập cũ dùng thư mục con (LI104) phải chạy nguyên vẹn.

## PH8 — Auto vỡ khi tập không có ref (đo 07/09/2026)

Đo trên hợp đồng thật, `do_ung_vien` với luật hiện hành (geo gate cứng + suất ref sàn):

| Tập | Auto hiện tại (bỏ envato) | Auto nếu tập chưa có ref |
|---|---|---|
| C1 (36 khối) | 36/36 khối · 648 ứng viên · **100% ref** | **0/36 khối** |
| H (14 khối) | 14/14 khối · 252 ứng viên · **100% ref** | **0/14 khối** |

Kho hiện tại: envato 5149 · ref 3736 · pexels 2716 · pixabay 427 · kho 64.

**Kết luận:** Auto đang xanh 100% **chỉ vì hai tập này có ref**. Sau khi áp chính sách
lưu trữ đã chốt (chỉ ref là vĩnh viễn; envato/pexels/pixabay là preview theo lượt dựng,
xoá khi user đóng job), kho thường trực còn **mỗi ref**. Tập mới chưa có ref →
khay rỗng tuyệt đối → **Auto không dựng được**. Đây đúng là điều user phát hiện.

Nguyên nhân là **hai luật cùng lúc**, không phải một:
1. Geo gate cứng loại stock không khớp địa danh.
2. Stock thành tạm thời → không tích luỹ qua các tập.

Auto không có người chọn nên không thể "hút preview rồi để người dựng lọc".

## PH9 — Kho stock KHÔNG phải thư viện chung, nó là CẶN của các tập cũ (đo 08/09/2026)

Chạy thật chương H (LI103, Afghanistan) 3 lượt ra draft CapCut, rồi đếm kho.

**Khớp địa danh theo nguồn:**

| Nguồn | Tổng | Có geo | Khớp Afghanistan |
|---|---:|---:|---:|
| ref | 3.736 | 79% | **2.002** |
| envato | 5.149 | 38% | **0** |
| pexels | 2.716 | 55% | **0** |
| pixabay | 427 | 10% | 4 |

**Stock trong kho phủ ở đâu:** ecuador 1.951 · oman 665 · andes 454 · india 196 ·
quito 136 · amazon 118 · nepal 108 — tức **đúng các tập đã làm**. Chỉ 90 địa danh.
Kho stock không phải thư viện đa dụng, nó là **cặn của những tập đã dựng**. Tập mới
về nước mới thì stock trong kho đóng góp ~0.

**Đo độ chính xác trên 9 khối MÁY tự chọn của chương H:**

| | Khay cũ (chưa có cửa geo) | Khay theo luật mới |
|---|---|---|
| Nguồn | envato 6 · kho 3 | **ref 9** |
| Khớp geo | **0/9** (1 clip geo=`usa`, còn lại trống) | **9/9** |
| Ví dụ hỏng | "Sixth street in **New York** City" cho câu về Afghanistan | — |
| Thời gian dựng | 104s | **38s** |
| Cảnh báo watermark | 3 | 1 |

**Kết luận:** dựng auto phải chạy trên **ref**, không phải stock. Stock chỉ đúng khi
tập nói về nước mà stock sẵn có — mà đó lại là những nước đã làm rồi. Điều này KHỚP
với cách user làm thật: *"kịch bản của tôi phát triển lên từ video ref"*.

→ **Điều kiện của Auto = tập CÓ ref.** Đây là lời giải cho PH8: Auto không vỡ,
Auto chỉ đổi điều kiện đầu vào. Tập chưa có ref thì Auto phải TỪ CHỐI và đẩy sang
Đồng kiểm, chứ không dựng bừa bằng stock lệch địa danh.

**Ngược lại — ref không phải lúc nào cũng hơn:** khối "Girls are not even allowed to
go to school" khay cũ cho "an empty school classroom" (đúng hơn), khay ref cho
"girls walking". Nên vẫn giữ stock KHỚP GEO trong khay, không loại theo nguồn.

## QĐ6–QĐ9 — Quyết định user chốt 08/09/2026

| # | Quyết định | Vì sao |
|---|---|---|
| QĐ6 | **"Dò lại khay" ĐƯỢC đổi lựa chọn của MÁY**, giữ nguyên lựa chọn của NGƯỜI | Đo PH9: chương H phải xoá tay lựa chọn máy thì khay mới mới có tác dụng. UI phải ghi rõ "đã làm mới N khối máy chọn" |
| QĐ7 | **Ngưỡng Auto = 60%** khối có ứng viên khớp geo | Dưới ngưỡng → từ chối, đẩy sang Đồng kiểm. User chọn nới rộng để Auto chạy được nhiều tập, chấp nhận phải đắp thêm |
| QĐ8 | **Hoãn nguồn ảnh + Ken Burns** (đợt 4) tới khi có khoá API | Đợt 1–3 chạy hoàn toàn offline trên ref + kho sẵn có |
| QĐ9 | Thứ tự thi công: **đợt 1 → 2 → 3** | Cổng Auto (đợt 3) dựa trên khay; khay còn lỗi ở đợt 1 thì đo nhầm |

**Đợt 1 (đang làm):** (1) `do_lai_khay` làm mới lựa chọn máy · (2) nối sổ nguồn gốc R6
vào đường Offline.

## Đợt 1 — xong 08/09/2026

**Việc 1 — `do_lai_khay` làm mới lựa chọn của MÁY (QĐ6).**
Chọn lại bằng chính `chon_mac_dinh` nên vẫn theo luật 60s + chảy tiếp (BH4).
Endpoint trả thêm `so_may_doi`, toast nói rõ số khối bị làm mới.

Nghiệm thu trên hợp đồng thật chương H (bản trước khi chữa tay):
9 miếng máy đổi từ envato/kho lệch geo sang ref khớp geo · 6 miếng người giữ nguyên ·
báo cáo 9 = thực tế 9.

**Bẫy bắt được ngay trong lúc làm:** cờ `nguoi_sua` **chỉ nằm ở MIẾNG**, khối không
mang gì (đo chương H: `khoi` 0/14 cờ, `hinh` 6/15). Xét cờ ở khối thì cả 14 khối đều
thành "máy" — báo 14 trong khi thực tế 9, và lựa chọn khối lệch hẳn lựa chọn miếng.
Nay khối được coi là CỦA NGƯỜI nếu chính nó **hoặc miếng bất kỳ của nó** có cờ.

**Việc 2 — sổ nguồn gốc đi cùng draft Offline.**
`sourcebook.viet_so_offline(hd, dung_id, draft_dir)` — một MIẾNG một dòng, bọc
try/except (mất sổ chứ không mất draft). Thêm tiền tố Sổ Tra vào bảng nhóm:
`ref`→refvid · `kho`/`rec`→local · `aigen`→aigen. Thiếu bảng này thì mọi clip đường
Offline rơi vào "other" và sổ mất ý nghĩa pháp lý.

Chương H thật: `nguon_footage.json` 15 clip — **refvid 84% · sub 10% · local 6%**.

**Lỗi thứ ba, phát hiện khi viết test cho việc 2:** `relocate` đánh số theo MIẾNG
nhưng vòng ghi `su_kien` duyệt theo KHỐI. Test thu nhỏ (3 miếng / 2 khối) cho thấy sổ
chỉ ghi **1/3** — miếng chảy tiếp không vào sổ lần nào vì nhánh chảy tiếp `continue`
trước khi đặt `dung_id`. Nay duyệt theo miếng, và miếng chảy tiếp ghi tên clip nó
đang dùng tiếp.

## QĐ10–QĐ11 (user chốt 08/09) + Đợt 2

| # | Quyết định | Vì sao |
|---|---|---|
| QĐ10 | **Hoãn dọn 5.102 preview envato** tới khi nối xong "hút theo lượt dựng" | Đo thật: chương **C2 bỏ trống địa danh** đang sống bằng 265 preview envato. Chương CÓ địa danh (C1 432 ứng viên, H 168) thì envato đã bị cửa geo loại sạch — xoá không mất gì. Xoá trước khi có đường hút mới là rút khay của C2. Công cụ `don-kho` đã xong, chạy lúc nào cũng được |
| QĐ11 | **Địa danh BẮT BUỘC khi nộp tập** | Không khai thì cửa geo không có gì để so, và bẫy "chợ Trung Quốc cho tập Afghanistan" quay lại. Chặn ở form + ở API (sau kiểm thư mục, để lỗi 404 vẫn là 404) |

**Đợt 2 đã xong:** cột `tam_tap` trên `clip` · `phien_hut(ma_tap=)` đóng dấu clip MỚI ·
`dong_job(conn, tap)` giữ clip đã tải hoặc đã lên timeline · cột `dong`/`dong_at` trên
`jobs` · endpoint `POST /api/jobs/{id}/dong` + nút "đóng job" ngoài Overview ·
lệnh `don-kho` (mặc định chỉ đếm).

**Còn lại của đợt 2:** nối "hút preview theo lượt dựng" (truyền `ma_tap` vào `phien_hut`
từ màn hình Offline), rồi mới chạy `don-kho --xoa`.

**Hai lỗi bắt được trong lúc làm:**
1. Nhánh UPDATE của `them_clip` ghi đè MỌI cột bằng dữ liệu lượt hút, mà lượt hút không
   mang `path_local` — **hút lại một clip ĐÃ TẢI là mất đường dẫn file**. Mà luật giữ/dọn
   lại đọc đúng cột đó.
2. Nút "đóng job" tôi viết gọi `toast()` trong khi cả file chỉ có `toastOf()` — bấm là
   ReferenceError. Máy không có Node (BH3) nên thêm **rào tĩnh**: mọi `onclick="tên("`
   phải có `function tên(` trong file.

## Đợt 3 — Cổng Auto (08/09)

`runner.NGUONG_AUTO = 0.6` + `du_khay_cho_auto(ung_vien)`. Chương khai `auto` mà khay
phủ dưới 60% khối thì **chuyển sang Đồng kiểm** kèm cảnh báo nói rõ tỉ lệ và lý do
thường gặp (tập chưa có ref, hoặc stock lệch địa danh bị loại).

Auto cố tình bỏ envato để không đốt hạn mức license; khi cổng đẩy chương sang Đồng kiểm
thì **dò lại khay đầy đủ** — giữ khay Auto là bắt người chọn trong đúng cái rổ vừa bị
kết luận là quá mỏng.

**Đo trên 7 chương thật (khay Auto, bỏ envato):**

| Chương | Địa danh | Phủ | Kết quả |
|---|---|---|---|
| C1 | Afghanistan | 36/36 · 100% | Auto chạy |
| C2 | *(trống)* | 43/43 · 100% | Auto chạy |
| C3 | Afghanistan | 43/43 · 100% | Auto chạy |
| C7 | *(trống)* | 17/30 · **57%** | **→ Đồng kiểm** |
| C8 | tibet china | 25/34 · 74% | Auto chạy |
| H (cũ) | *(trống)* | 17/17 · 100% | Auto chạy |
| H | Afghanistan | 14/14 · 100% | Auto chạy |

Ngưỡng 60% chặn đúng 1/7 chương. Nếu chọn 80% thì C8 (74%) cũng bị chặn — đó chính là
khác biệt thực tế giữa hai phương án user cân nhắc.

## Rà cuối tuỳ chọn (08/09) — `tests/test_ma_tran_tuy_chon.py`

Rà theo hai trục, 51 test:

**Dọc** — form → JobRequest → opts hàng đợi → cờ `make`. Cả 11 tuỳ chọn đi trọn đường
(bật riêng và bật cùng lúc); opts rỗng KHÔNG đẻ ra cờ lạ; mọi cờ worker sinh ra đều có
thật trên `make --help` (đối chiếu `--help` thật, không chép tay). Tách
`worker.co_lenh(opts)` thành hàm thuần để test được — đây là họ nhà lỗi PH1.

**Ngang** — ma trận `kieu_chay` × vị trí chương (12 tổ hợp) và × độ dày khay (6 tổ hợp).
Mốc AVD: chương bắt đầu ĐÚNG mốc thì tự chạy, trước mốc thì duyệt. Cổng Auto chỉ đụng
chương đang định tự chạy, không lấn sang chương của người.

**Dây chuyền Auto đầu-cuối** (`test_cong_auto.py`): bấm Phân tích → tự khoá sổ → tự chạy
Online. Khay rỗng thì DỪNG và báo, không giao draft rác kèm nhãn "✓ xong".

**Lỗi bắt được:** máy chủ giữ rào auto riêng `co_hinh < tong_k * 0.5` trong khi cổng ở
runner là 60%. Cổng runner chặn trước nên nhánh 50% đã thành **code chết** mà đọc vào vẫn
tưởng đang bảo vệ điều gì đó (BH4). Gộp về `runner.du_khay_cho_auto` — một hàm, một số.

**Không phải lỗi nhưng cần biết:** `uu_tien_nguon` KHÔNG có ô chọn trên giao diện, luôn
là mặc định `"ref"` của JobRequest. Đã kiểm giá trị hợp lệ và có tác dụng thật (ref đứng
đầu khay). Muốn đổi theo tập thì phải thêm ô.

## Lỗi preview đen (user báo 08/09) — `tests/test_preview_trinh_duyet.py`

**Triệu chứng:** timeline có hình chảy vào, PREVIEW đen.

**Bằng chứng trước khi sửa:** `/api/sotra/khuc` cho 6/6 miếng của C5 đều ra file khúc có
thật; `prod.log` ghi **121 lượt `/khuc` đều 206**. Dữ liệu CÓ, chỉ không được hiện.

**Nguyên nhân:** hai thẻ `<video>` thay phiên để tránh chớp đen. `ofVeAll` chạy lại liên
tục; lần vẽ sau rơi vào nhánh "đang hiện đúng clip rồi" → gọi `ofNapKe` nạp ngầm shot kế
→ hàm này chọn **thẻ đang ẩn**, đúng thẻ đang chờ nạp clip HIỆN TẠI, ghi đè `src` bằng
clip kế và **xoá `onloadeddata`**. Callback bật hình bị huỷ → cả hai thẻ ở lại `hidden`
→ đen vĩnh viễn. Vá: `ofNapKe` không đụng thẻ có `_src === ofVeXem._key`.

**Đường thứ hai cũng ra màn đen** (test riêng bắt được): clip hỏng thì `onloadeddata`
KHÔNG BAO GIỜ bắn, hai thẻ ẩn mãi mà không ai biết vì sao (BH1). Vá: `onerror` rơi về
khung hình tĩnh của clip.

**Thu hoạch lớn hơn bản vá:** lớp giao diện từ nay test được — xem METHODOLOGY BH9.

## Lỗi "đổi hình xong F5 lại về mặc định" (user báo 08/09)

User báo team gặp, còn user tự thử thì KHÔNG bị. Đo ra **hai** lỗi khác nhau.

### Lỗi 1 — `lam_tuoi_ref` không dời `chon` theo khay mới

`api_offline_doc` gọi `lam_tuoi_ref` ngay lúc ĐỌC hợp đồng rồi ghi đè file. Hàm đó dựng
lại `uv` (bỏ mục ref hỏng, thêm mục tươi) nhưng **giữ nguyên `chon`** — mục hỏng đứng
TRƯỚC mục đang chọn thì chỉ số tụt một bậc, `chon` trỏ sang clip khác.

Test tái hiện: chọn `r:2`, sau khi làm tươi thành `r:5`. Đã vá (`_thay` trả thêm chỉ số
mới; mục bị loại hẳn thì trả `-1` chứ không trỏ bừa).

**Nhưng đo trên 9 hợp đồng thật với code CŨ: 0 miếng bị dính.** Kho đang sạch nên lỗi
chưa nổ. Vá vì nó là bẫy đang nằm chờ — KHÔNG phải vì nó giải thích báo cáo của team.

### Lỗi 2 — cái team thật sự gặp: quyền sửa báo quá muộn

`nguoi_tao` của 9 hợp đồng: **5 chương LI103 mang `'bot'`** (cả tập nộp dưới tên đó),
C2 `thanhdn`, C7/C8/H-cũ trống. Luật "quyền sequence = người nộp tập" (chốt 07/09) vì
thế khoá cửa với mọi người trừ admin. User là admin nên thử không bị.

Luật ĐÚNG, cách hỏng thì SAI: giao diện cho đổi hình, hình hiện lên, **700ms sau**
autosave mới ăn 403 — toast chớp rồi trôi, người dựng chỉnh tiếp cả loạt rồi F5 mất sạch.

Vá: `GET /api/offline/{id}` trả `duoc_sua` + `chu_sequence`; UI đọc lúc NẠP, chặn ngay
tại chỗ bấm và nói rõ ai mới sửa được.

### Xử lý dữ liệu (user chốt 08/09)

*"Tập này anh mở cho thanhdn giúp tôi, còn từ các tập sau thì vẫn theo rule đã bàn."*
Đổi `nguoi_tao` của 5 chương LI103 từ `bot` sang `thanhdn` (sao lưu
`.truoc-mo-quyen-1224`, ghi atomic). Khớp thực tế: job 21 nộp cùng thư mục LI103 là của
thanhdn, job 22 mới là của `bot`. **Không đụng luật** — tập sau vẫn theo người nộp.

Nghiệm thu qua đúng đường server gác quyền: 6/6 chương LI103 → thanhdn `True`,
người khác `False`, admin `True`.

## Ngách lấy từ DANH BẠ NỀN của CRM (user chốt 08/09)

**Vấn đề:** ô Niche đang nhập tay tự do. Hậu quả đo được: Library có **cả `Life In` lẫn
`life-in`** — hai thư mục cho cùng một ngách.

**Khảo sát (CRM đã chuyển sang ổ D — bản trên ổ C là bản cũ, tôi tìm nhầm ở đó trước):**

| | |
|---|---|
| Sổ ngách | `D:\AI AGENT OUTLIERY\data\nen\danh_ba.db`, bảng `ngach` |
| Đọc qua | `nen.common.danh_ba.liet_ke("ngach")` — thư viện, **không có API HTTP** |
| Cột | `ma`, `ten_chuan`, `trang_thai`, `ghi_chu`, `tao_luc` — **không có cột "cần địa danh"** |
| Số ngách | 13: LIFE IN · LIVING IN · TRAVEL DOCUMENTARY · SENIOR HEALTH · HEALTHY EATING · COOKING · RETIREMENT · OLD · OLD NEWBIE · INVESTIGATION · SPACE · STORM · SCI-FI |

**Quyết định (user chốt 08/09):**

| # | Quyết định | Vì sao |
|---|---|---|
| QĐ12 | Đọc **thẳng `danh_ba.db` ở chế độ chỉ-đọc**, đường dẫn khai trong `.env` (`RENDERY_DANH_BA`) | Không phụ thuộc CRM có chạy hay không, và không thể ghi nhầm vào dữ liệu của app khác |
| QĐ13 | Cờ "ngách cần địa danh" **đặt trong RenderY** (sửa được ở trang Cài đặt) | Danh bạ nền là của chung; RenderY ghi vào đó là lấn sân |
| QĐ14 | Ngách cần địa danh: **LIFE IN · LIVING IN · TRAVEL DOCUMENTARY** | Ba ngách gắn trực tiếp với một vùng địa lý |

**Đo trước khi code:** cửa geo trong `tra()` **đã tự tắt** khi `geo_tap` rỗng (`gt` rỗng →
bỏ qua cả hai điều kiện lọc). Nên "ngách không cần địa danh thì không lọc theo vùng"
KHÔNG phải viết thêm gì ở tầng tra cứu — chỉ cần cho phép bỏ trống địa danh đúng chỗ.

### Nối ngách — đã làm xong 08/09

`autoedit/ngach.py` — đọc `danh_ba.db` bằng `sqlite3` chế độ **`mode=ro`** (rào thật:
mọi lệnh ghi ném `OperationalError`, có test khoá). Đường dẫn ở `RENDERY_DANH_BA`,
bộ ngách cần địa danh ở `RENDERY_NGACH_GEO` — cả hai thêm vào whitelist trang Cài đặt.

| Hàm | Việc |
|---|---|
| `liet_ke()` | 13 ngách + cờ `can_dia_danh` |
| `hop_le(x)` | ngách có THẬT trong danh bạ không (nhận cả mã lẫn tên) |
| `can_dia_danh(x)` | ngách này có bắt buộc khai địa danh không |
| `doc_duoc()` | có đọc được sổ không — UI cần biết để nói rõ khi rỗng |

**Fail-open có chủ ý:** CRM tắt / ổ D chưa gắn → `liet_ke()` rỗng, `hop_le()` cho qua,
UI lùi về ô gõ tay. Một app khác chết KHÔNG được kéo cả RenderY chết theo. **Nhưng**
`can_dia_danh()` khi đó trả True — đang mù thì giữ luật chặt; nới lỏng lúc mù là mở lại
đúng bẫy "chợ Trung Quốc cho tập Afghanistan".

**Nghiệm thu trên danh bạ THẬT:** 13 ngách, đúng 3 ngách cần địa danh
(LIFE IN · LIVING IN · TRAVEL DOCUMENTARY). `life-in` gõ tay **bị từ chối**;
`Life In` và `cooking` được nhận; `cooking` **không đòi địa danh**.

**Test cũ phải sửa theo:** 11 test nộp job không kèm ngách — nay ngách là bắt buộc.
Nhân tiện trỏ `RENDERY_DANH_BA` sang đường dẫn không tồn tại trong các fixture đó:
test phải KÍN, không được đọc danh bạ thật của CRM trên ổ D.
