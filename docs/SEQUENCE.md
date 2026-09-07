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
| ⏳ **3b. Cho clip CHẢY TIẾP qua ranh khối** | luật chọn phân biệt "lặp" (cấm) với "chảy tiếp" (cho, khi khối ngắn hơn chuẩn kênh và nguồn còn đủ dài); chỗ ráp cắt **một đoạn liên tục** + miếng sau nối đúng chỗ miếng trước dừng | C2: 43 shot/median 3,24s (**−32%**) → 32 shot/median 4,71s (**0%**), số clip phải tải giảm 26% |
| **4. Cấu trúc phẳng + `Rec/`** | **6 chỗ** (5 chỗ kế hoạch cũ + `_mo_dau_tap_s`) | LI103 phẳng → 17 chương đúng thứ tự · LI104 thư mục → y hệt hôm nay · gộp 1 file cả tập → vẫn bị chặn |
| **5. Form 6 ô** | bỏ "Phương án dựng", ô Kiểu chạy, đổi nhãn Niche | ảnh chụp 2 trạng thái + `test_smoke_ui` xanh |

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
kéo thành 4,7s — khi đó vẫn đổi hình như cũ. Con số 32 đã tính điều này.

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
