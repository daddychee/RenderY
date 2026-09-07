# New Sequence V2 — flow đã chốt 07/09/2026

> **Trạng thái: CHỐT THIẾT KẾ, CHƯA CODE.** User duyệt từng điểm trong phiên
> 07/09. Ghi lại để không phải bàn lại.

## Vì sao đổi

Form hiện có 7 ô, trong đó **Phương án dựng** (stock / AI / tự quay) là ô thừa:
mọi video đưa vào đều đi qua cùng một luồng phân tích dựa trên kịch bản + voice.
Việc phân biệt nguồn thuộc về lúc *hiển thị trong Offline*, không phải lúc nộp.

## Cấu trúc thư mục — áp dụng SAU LI103

```
RenderY/
  H.mp3   H.txt                      <- hook
  C1.mp3  C1.txt  ...  C15           <- chương, đặt PHẲNG, không thư mục con
  E.mp3   E.txt                      <- kết
  ref 1.mp4  ref 1.srt  ...          <- ref cả tập (phim mẫu)
  Rec/                               <- footage TỰ QUAY (user chốt tên này)
```

**Bắt buộc nhận CẢ HAI kiểu**: LI103 và mọi tập trước đó đang dùng thư mục con
(`C1/`, `C2/`… — đo 07/09), phải chạy lại được nguyên vẹn. Quy ước phẳng chỉ áp
dụng cho tập nộp từ sau LI103.

**Luật phân biệt nguồn (không mơ hồ):**

| Nằm ở | Là gì | Vào Library với |
|---|---|---|
| `ref *.mp4` ở gốc | phim mẫu của tập | `nguon='ref'` |
| trong `Rec/` | footage tự quay | `nguon='kho'` |
| `H` / `C<số>` / `E` + `.txt`+`.mp3` | chương | (không vào Library) |
| file lẻ khác | bỏ qua | — |

## Ba kiểu chạy — MỘT đường, một tham số

User chốt 07/09: cả ba đi chung **đường Offline**, không còn nhánh code thứ hai.
Khác nhau duy nhất ở chỗ *chương nào cần người duyệt*, biểu đạt bằng mốc AVD:

| Kiểu chạy | Mốc AVD | Hành vi |
|---|---|---|
| **Manual** | ∞ | mọi chương vào Offline, người duyệt khối rồi Online |
| **AVD Mode** | mốc thật (vd 6 phút) | chương trước mốc đồng kiểm · sau mốc tự chạy tới timeline |
| **Auto** | 0 | mọi chương tự chạy tới timeline cuối |

**AVD Mode là kiểu dùng hàng ngày**: nhân sự nộp tập trước khi về, máy chuẩn bị
qua đêm; sáng hôm sau có sẵn khối Offline cho phần đầu (nơi cần bàn tay người
nhất) và timeline đã dựng xong cho phần sau.

Cơ chế đã có sẵn trong `offline/runner.py`:

```python
dong_kiem = (avd_s <= 0) or (mo_dau_tap_s < avd_s)
bo_nguon  = () if dong_kiem else ("envato",)     # chương auto ĐÃ loại Envato
```

Chỉ cần cho phép biểu đạt cả ∞ (Manual) lẫn 0 (Auto) qua một ô duy nhất.

### Vì sao Auto không có Envato (user chốt 07/09)

5 editor cùng chạy Auto thì mọi hạn mức ngày đều bị vượt dễ dàng. Nặng hơn:
**máy chạy qua đêm mà tài khoản bị chặn giữa chừng thì sáng hôm sau không có
timeline nào để chỉnh** — hỏng một lần là mất trọn một ngày sản xuất. Envato chỉ
sống ở đường Manual/đồng kiểm, nơi số lượt tải bằng đúng số clip người thật sự
chọn. Đo 2 ngày đầu: 22 và 31 clip/ngày, đều từ đường Manual.

Hệ quả đã chấp nhận: kho Envato 5.167 clip trong Library **không dùng được cho
chương Auto**. Đổi lấy sự an toàn của ca đêm.

## Ép nhịp — bỏ logic Padoma, dùng Framing Insight

User chốt 07/09: *"Logic ép nhịp cũ của Padoma không còn đúng. Việc ép nhịp sẽ
dùng guide từ Framing Insight."*

Framing Insight (`kenh/hoso.py`) đã đo sẵn từ kênh ref — ví dụ GoDoc, hội tụ 5
video:

```
than_trung_vi 4.73s · than_ty_le_nhanh 6% · than_ty_le_hold 38%
hook_trung_vi 4.98s · hook_kieu "em"
nhip_curve    [14, 10, 11, 11, 12, 12, ...]   <- mật độ cắt theo trục thời gian
bung_chu_ky_s 397.5                            <- chu kỳ tăng nhịp giữ chân
loai_canh     tu_quay 42.5% · b_roll 57.5%
mo_ta         "shot dài, không nổ cắt, để cảnh tự kể chuyện"
```

Đường Offline chia khối theo guide này. Tầng `nhip/ep.py` (dự báo shot_count +
kẹp sàn của Padoma) **không port sang**.

> Ghi chú cho lần sau: cảnh báo "ĐO LẠI SAU DỰNG … LỆCH TO" chỉ có nghĩa khi
> project CÓ kênh ref. Chạy trần (không `--kenh-ref`) thì nó so với nền trung
> tính 3.0s và luôn kêu — 07/09 tôi đã đọc nhầm dấu hiệu này một lần.

## Overlay text + SFX — KHÔNG port

User chốt 07/09: không dùng bản của pipeline cũ, sẽ xây bản riêng sau. Đường
Offline giữ nguyên phạm vi hiện tại: hình + voice + nhạc/ducking + bản sạch.

## Form New Sequence sau khi đổi — 6 ô

| Ô | Đổi gì |
|---|---|
| **Niche** | giữ, đổi nhãn từ "Kênh / niche" thành **Niche** (chỉ còn vai trò KHO: thư viện local, SFX, DNA nghỉ — không đụng nhịp) |
| ~~Phương án dựng~~ | **BỎ** — xem mục dưới |
| **Kiểu chạy** | 3 lựa chọn **Manual / AVD Mode / Auto**; chọn AVD Mode mới hiện ô nhập số phút. Ô "AVD của tập" cũ gộp vào đây |
| Địa danh tập | giữ nguyên |
| Retention tập trước | giữ nguyên |
| Framing Insight | giữ nguyên — nay là nguồn duy nhất của nhịp |

### "Phương án dựng" đi đâu

Ô này đang gánh ba việc; bỏ nó phải trả lại từng việc về đúng chỗ:

1. **Chọn nguồn** → không cần nữa: mọi nguồn cùng chảy vào khay, Offline chỉ
   cần *ghi rõ* clip đến từ đâu (Envato / Pexels / Pixabay / ref / Rec / AI).
2. **Bật-tắt gen ảnh AI** → chuyển xuống **từng khối trong Offline** (đã có sẵn
   3 lựa chọn gen / ảnh tự đưa / bỏ). Quyết định "cảnh này không có footage
   thật, phải gen" chỉ nhìn được khi đã thấy khối.
3. **Chọn nhánh pipeline** → thay bằng ô Kiểu chạy.

## Pipeline cũ đi về đâu

Không xoá — đóng băng ở cổng riêng (port 9119, checkout riêng, venv riêng) để
team có đường chạy ổn định trong lúc tool chính được sửa. Nghiệm thu 07/09:
C12 chạy trọn 6 stage, mã thoát 0, **908s**, draft CapCut sinh ra bình thường.
DB dùng chung; ràng buộc kèm theo: sửa schema **chỉ được thêm cột**.

## Việc phải làm, theo thứ tự

1. **Ép nhịp theo Framing Insight vào đường Offline** — điều kiện cần để Auto/AVD
   Mode dùng được thật; thiếu nó thì draft auto không có tiết tấu của kênh
2. **Ba kiểu chạy** — một tham số mốc AVD + ô Kiểu chạy 3 lựa chọn trên form
3. `doc_chuong` nhận cấu trúc phẳng + `Rec/` (giữ nguyên đường thư mục cũ)
4. Form: bỏ Phương án dựng, đổi nhãn Niche
5. Offline: hiện nhãn nguồn trên từng ứng viên; đưa lựa chọn gen AI về từng khối

## Nền đã có (khỏi làm lại)

- `dong_kiem` + `bo_nguon=("envato",)` — gate AVD và loại Envato khỏi chương auto
- `chi_chuan_bi` — công tắc hiện tại, sẽ được thay bằng ô Kiểu chạy
- `kenh/hoso.HoSoKenh` + `ap_vao_nhip` — Framing Insight đã đo và áp được
- `nguon='kho'` — đã có trong `NGUON_HOP_LE`, dùng thẳng cho `Rec/`
- `sotra.db.ma_tap_tu_duong_dan` — suy mã tập, một nguồn sự thật (07/09)
- `web/worker._nap_ref_nen` — nạp ref lúc nộp tập, chạy nền (07/09)
