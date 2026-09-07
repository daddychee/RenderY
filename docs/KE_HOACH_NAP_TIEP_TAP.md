# Kế hoạch: NẠP TIẾP nội dung cho tập đã có sequence

> **Trạng thái: ĐÃ CHỐT THIẾT KẾ — CHƯA LÀM.** User duyệt kế hoạch 07/09/2026,
> yêu cầu lưu lại, chưa thực thi. Đây là dự phòng đường dài, không gấp.

## Vì sao cần

Hiện nộp lại một tập đã nộp thì:

| Bước | Hành vi hiện tại | Hệ quả |
|---|---|---|
| Nộp folder tập | Worker duyệt **tất cả** chương trong `RenderY/` | Chương đã dựng xong cũng chạy lại |
| Mỗi chương | Tạo `project_id` MỚI | Sequence cũ bị nhân bản, chip chương hiện 2-3 bản |
| Đầu job | `_don_giao()` xoá kết quả giao lần trước | **Draft + footage đã giao của cả tập bị xoá** |
| Chi phí | Chạy lại toàn bộ | Tốn LLM + thời gian cho chương không cần |

Tức là **không có đường "nạp tiếp"** — chỉ có "làm lại từ đầu", và nó phá kết quả cũ.

Bốn tình huống thực tế: viết dần (thêm C2 C3) · sửa kịch bản một chương ·
ref về muộn · chương dựng hỏng cần chạy lại riêng.

## Thiết kế đã chốt

### Một cửa vào, một nút (user chốt 07/09)

KHÔNG thêm dropdown chọn tập, KHÔNG thêm nút Update riêng. User dán đường dẫn
như hiện nay → bấm **Kiểm tra** → máy quét một lượt → **popup** báo trạng thái:

**Tập mới**
```
LI106 — tập mới, 5 chương: H · C1 · C2 · C3 · E
⚠ C2 chưa có .srt (tool tự nhận giọng, chậm hơn)
→ Chọn tùy chọn dựng bên dưới rồi bấm Start
```

**Tập đã có**
```
LI104 — đã có 4 sequence. Cập nhật lần này:
  + C5, C6      chương MỚI          → sẽ dựng
  ↻ C3.1        bản update của C3   → thay sequence C3 (đang pha 2, 18 shot chỉnh tay)
  ✓ H, C1, E    không đổi           → giữ nguyên
  ♪ Ref 1.mp4   mới                 → nạp vào Library (~20 phút, chạy nền)
→ Bấm Cập nhật
```

### Quy ước phiên bản: `C3.1`

`C3.1` là bản update của `C3`; `C3.2` là bản update của `C3.1`. File cũ KHÔNG
xoá trên NAS (truy vết được), máy tự biết bản nào mới nhất.

Sáu điểm đã chốt:

1. **Thứ tự** — `C3.1` xếp đúng chỗ C3 (giữa C2 và C4). Máy lấy **bản cao nhất**,
   bản thấp hơn bỏ qua hoàn toàn; nhảy cóc vẫn được (có C3 + C3.2 → chạy C3.2).
2. **Hook/End cũng có biến thể** — `H.1`, `E.1` cùng luật (kịch bản hook hay bị
   viết lại nhất).
3. **Bản update là TOÀN CHƯƠNG**, không phải phần thêm — `C3.1` phải chứa đủ
   script + voice của cả chương; máy dựng lại trọn chương từ nó. Phải nói rõ với
   team vì tên "update" dễ hiểu nhầm là "bổ sung".
4. **Sequence cũ khi bị thay**: THAY HẲN (user chốt) — ẩn khỏi chip chương,
   KHÔNG xoá file (còn tra được); draft đã giao của chương đó thì dọn.
5. **Lưới an toàn**: sequence đang dựng dở (pha 2 / đã khoá sổ / có shot chỉnh
   tay) → popup nói thẳng số shot sẽ mất, bắt xác nhận. Sequence pha 1 chưa ai
   đụng → thay thẳng, không hỏi.
6. **Sửa thẳng mà quên đổi tên** → so NGÀY SỬA file với mốc lúc dựng; mới hơn mà
   không có bản `.1` → **chỉ cảnh báo**, không tự dựng lại.

### Phạm vi — cố ý giữ hẹp

Chỉ làm: quét lại thư mục + nhận diện phiên bản + popup. KHÔNG làm lịch sử
phiên bản, so sánh diff, khôi phục bản cũ — nghe hay nhưng sẽ không ai dùng mà
phải bảo trì mãi.

## Đợt 0 — NHẬN CẤU TRÚC PHẲNG (user nêu 07/09, ưu tiên hơn 5 đợt dưới)

Thực tế LI103: team đặt file THẲNG trong `RenderY/`, không tạo thư mục chương:

```
RenderY/
  H.mp3   H.txt              <- hook
  C1.mp3  C1.txt  ... C15    <- 15 chuong
  E.mp3   E.txt              <- ket
  ref 1..5 (.mp4 + .srt)     <- ref ca tap (da co luat rieng)
```

Cách này RÕ RÀNG HƠN cách thư mục (17 chương nhìn một màn hình là thấy hết) và
bắt tạo 17 thư mục chỉ để chứa 2 file mỗi cái là việc vô nghĩa. Hiện `doc_chuong`
chỉ duyệt thư mục con nên báo "RenderY trống" + "voice/script nằm thẳng — không
được gộp cả tập" (cảnh báo đúng cho trường hợp GỘP 1 file, sai cho trường hợp
này vì tên file đã tách chương rõ ràng).

**Phạm vi — 5 chỗ, `doc_chuong` là lõi (sai là không nộp được tập nào):**

| Chỗ | Hiện tại | Cần |
|---|---|---|
| `chapters.doc_chuong` | chỉ duyệt thư mục con | thêm nhánh gom file lẻ theo tên gốc |
| `chapters.Chuong` | chỉ mang path thư mục | mang thẳng script/voice/srt |
| `cli.make` | nhận folder, tự dò `_pick_input` | nhận file tường minh |
| `worker` | truyền folder chương | truyền file |
| `runner._thu_muc_nas` + `nap_ref_cua_tap` | suy thư mục chương | phẳng thì thư mục chương = `RenderY/` |

**Luật nhận diện (không mơ hồ):** file có tên khớp quy ước chương (`H`, `C<số>`,
`E`, kèm biến thể `.1` `.2`) VÀ có đủ cặp .txt + .mp3 -> là một chương. File
`ref *` -> ref. File lẻ khác -> bỏ qua như cũ.

**Bắt buộc: hỗ trợ CẢ HAI kiểu** — tập cũ dùng thư mục (LI104) phải chạy nguyên.

**Cổng:** LI103 phẳng -> nhận đúng 17 chương đúng thứ tự H·C1..C15·E + 5 ref ·
LI104 thư mục -> chạy y hệt hôm nay · thư mục CÓ CẢ hai kiểu -> ưu tiên thư mục,
không nhân đôi chương · gộp thật (1 file voice cả tập) -> vẫn bị chặn như cũ.

> 07/09: user quyết SẮP TAY trước cho LI103, fix sau. Không đụng NAS.

## Kế hoạch thực thi — 5 đợt, mỗi đợt một cổng

### Đợt 1 — Quy ước phiên bản (nền của mọi thứ)
`phan_tich_ten` nhận thêm `H.1` · `C3.1` · `E.2`, trả thêm số phiên bản.

**Cổng:** `C3` không có `.1` → chạy y hệt hôm nay (không phá gì đang chạy) ·
có `C3`+`C3.1` → chỉ lấy C3.1 · nhảy cóc `C3`+`C3.2` → lấy C3.2 · `H.1` thay
`H` · tên rác (`C3.x`, `C.1`) vẫn bị từ chối · **toàn bộ test cũ xanh nguyên**.

> RỦI RO CAO NHẤT của cả kế hoạch: đây là lõi đọc chương, sai là KHÔNG NỘP
> ĐƯỢC TẬP NÀO. Đợt 1 chỉ *thêm* khả năng, không đổi hành vi cũ.

### Đợt 2 — Phát hiện sửa thầm
So ngày sửa `script`/`voice` từng chương với mốc lúc dựng sequence.

**Cổng:** chạm file bằng tay → cảnh báo hiện · file cũ → im lặng · chương chưa
dựng → không cảnh báo (vô nghĩa).

### Đợt 3 — API trạng thái tập
`/api/kiem-tap` trả thêm: tập mới hay đã có · từng chương (mới / có bản update /
không đổi / sửa thầm) · **số shot đã chỉnh tay** của sequence sắp bị thay · ref
mới chưa nạp.

**Cổng:** gọi trên LI104 thật → nhận đúng 4 chương đã có; tạo giả `C3.1` → báo
"thay sequence C3, đang pha 2, N shot chỉnh tay" với N đếm đúng.

### Đợt 4 — Popup
Bấm Kiểm tra → popup; tập mới như cũ; tập đã có: bảng thay đổi + nút **Cập nhật**;
sequence sắp bị thay mà có công sức → dòng đỏ + bắt xác nhận.

**Cổng:** ảnh chụp hai trạng thái popup + `test_smoke_ui` xanh.

### Đợt 5 — Worker chạy chọn lọc
Chỉ dựng chương được chọn · `_don_giao` chỉ dọn chương đó (hiện đang xoá kết quả
CẢ TẬP) · sequence bị thay đánh dấu ẩn khỏi chip chương, không xoá file.

**Cổng:** thêm `C3.1` vào LI104 → chỉ C3.1 chạy, H/C7/c8 không bị đụng, draft
của chúng còn nguyên; chip chương hiện C3.1 thay C3.

## Lưu ý khi bắt tay làm

1. **Team đang dùng thật** — đợt 1 và 5 đụng lõi. Làm khi **không có job nào
   chạy**; mỗi đợt commit riêng để lùi được một bước.
2. **Dùng bản sao LI104 ở thư mục tạm** để thử `C3.1`, không đụng NAS thật.
3. Việc này **không giúp gì cho tập đang dựng** — là dự phòng đường dài. Có sự
   cố với tập đang chạy thì ưu tiên đó trước, kế hoạch này gác lại.

## Nền đã có sẵn (khỏi làm lại)

- `chapters.doc_chuong` / `phan_tich_ten` — đọc + sắp thứ tự chương
- `runner._thu_muc_nas` — suy đường dẫn NAS của chương từ `project.json`
- `/api/offline/tap-list` — nhóm sequence theo mã tập (đã chạy)
- `nap_ref_cua_tap` — nạp ref, gọi trong `phan_tich`
- `worker.chapters_of` + vòng lặp chương + `_don_giao` — chỗ cần sửa ở đợt 5
- `hd["hinh"][*]["nguoi_sua"]` — đếm shot chỉnh tay cho lưới an toàn
