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
| **0. Nối ống + cây thước** (½ ngày) | job ghi 1 hàng/chương (bỏ `project_id` nối chuỗi) · thiếu `kenh_ref` → cảnh báo đỏ trong hợp đồng, không chạy im · lệnh `kiem-hop-dong` in bảng đo | Phân tích lại 1 chương LI103 → hợp đồng có `framing.ten='godoc-travel-doc'`, `avd_s=420`, địa danh đúng |
| **1. Ô Kiểu chạy** | enum `manual/avd/auto`; `dong_kiem` suy từ enum · `_mo_dau_tap_s` lấy thời lượng đã đo lúc align, hết phụ thuộc hình dạng thư mục | 3 kiểu × chương giữa tập → `dong_kiem` đúng cả 3; chạy được trên cả thư mục lẫn phẳng |
| **2. Đo Auto** (phép đo, không phải việc) | chạy `kiem-hop-dong` với `bo_nguon=('envato',)` trên 3 chương LI103 | biết % khối có ứng viên; dưới 50% thì bàn lại QĐ5 trước khi cho chạy đêm |
| **3. Dải hình theo Framing** | hàm thuần `chia_hinh(khoi, hoso) -> hinh[]`: khối > 1,6×`than` chẻ thành `ceil(dur/than)` miếng, ưu tiên **ranh mềm có sẵn**, chừa tỉ lệ `hold`, sàn 0,7s. KHÔNG đụng dải voice | median miếng hình ≈ `than` ±20% · không còn miếng > 12s · người vẫn chẻ/gộp tay được |
| **4. Cấu trúc phẳng + `Rec/`** | **6 chỗ** (5 chỗ kế hoạch cũ + `_mo_dau_tap_s`) | LI103 phẳng → 17 chương đúng thứ tự · LI104 thư mục → y hệt hôm nay · gộp 1 file cả tập → vẫn bị chặn |
| **5. Form 6 ô** | bỏ "Phương án dựng", ô Kiểu chạy, đổi nhãn Niche | ảnh chụp 2 trạng thái + `test_smoke_ui` xanh |

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
