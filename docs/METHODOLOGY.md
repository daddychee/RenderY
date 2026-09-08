# METHODOLOGY — cách làm việc của RenderY

> **Tài liệu SỐNG.** Cập nhật mỗi khi rút được bài học mới, không viết một lần
> rồi bỏ. Lý do user nêu thẳng 07/09/2026: *"anh đã nhớ nhớ quên quên rất
> nhiều, ảnh hưởng tới công việc của chúng ta."*
>
> Nguyên tắc gốc (Karpathy 4 điều · Ponytail thang leo 7 bậc) nằm ở
> `CLAUDE.md`, **không chép lại ở đây**. File này chỉ ghi thứ đã trả giá bằng
> lỗi thật trên chính tool này.

## Bảng mốc

| Ngày | Chốt gì | Ai quyết |
|---|---|---|
| 07/09/2026 | Lập file. 6 bài học rút từ 164 commit + đo thật trên LI103/LI104 | user yêu cầu, Claude rà |
| 07/09 tối | Thêm BH7 (test gọi mạng) — lộ ra khi chạy bộ test của bậc 1 | đo thật |

---

## Sáu bài học — mỗi cái đã trả giá bằng lỗi thật

### BH1. Bỏ qua lỗi mà không kêu = tự tắt tính năng trong im lặng

Fail-open cứu được job khỏi chết cả tập, nên vẫn giữ. Nhưng **fail-open không
có chuông** thì tính năng biến mất mà không ai biết.

Đã trả giá 5 lần: GLM chết → khay ứng viên rỗng, editor bấm "Đổ video" không ra
gì (06/09) · `FrozenInstanceError` nằm im trong `retention/ap_vao_ho_so` bị
fail-open nuốt (05/09) · nạp ref lỗi → bỏ qua · `_mo_dau_tap_s` không thấy
thư mục → trả 0 → mọi chương thành đồng kiểm (06/09) · tham số dựng rớt sạch
với job nhiều chương (07/09, xem `SEQUENCE.md`).

**LUẬT:** mọi nhánh `except` fail-open phải đẩy một dòng vào `hd["canh_bao"]`
của hợp đồng, và UI phải hiện dòng đó. Kênh này đã có sẵn — chỉ chưa dùng
nhất quán.

### BH2. "Bắt buộc nhập" ở form là kiểm tra rẻ nhất và vô dụng nhất

Form chặn không cho nộp khi thiếu Framing Insight, kèm chữ *"nhịp chia khối lấy
từ hồ sơ kênh này"*. Đo 07/09: giá trị đó **không tới nơi** với job nhiều
chương, và hợp đồng ghi `framing: {}`. Người dùng đã làm đúng phần của mình,
máy vẫn chạy sai, không báo.

**LUẬT:** với mỗi tham số người nhập, phải kiểm ở **đầu ra** chứ không ở ô nhập
— một test đi trọn đường *form → job → hợp đồng*, assert giá trị có mặt trong
`offline.json`.

### BH3. Kênh phát hiện lỗi chủ đạo đang là MẮT USER — phải đổi

Đếm trên 164 commit: **11 commit** ghi rõ "user bắt / user báo", riêng ngày
06/09 có **85 commit** vá liên tiếp. Nghĩa là sản phẩm được kiểm bằng người
dùng trong lúc vận hành, không phải bằng máy trước khi giao.

Luật cứng #4 nói *"Python đo"* — nhưng chưa có công cụ đo nào cho **đầu ra**.

**LUẬT:** mỗi năng lực mới phải kèm một phép đo chạy được trên dữ liệu thật,
in ra số. Không có số thì không tuyên bố xong.

### BH4. Một khái niệm suy ở hai nơi thì chắc chắn lệch

Mã tập suy bằng hai regex ở hai chỗ → worker nạp ref dưới `LI104`, Offline tra
`LI104 TOOL`, rào geo chặn nhầm ref của chính tập mình (07/09). Đã gom về
`sotra.db.ma_tap_tu_duong_dan`.

Cùng bệnh vẫn còn: *"chương này bắt đầu ở giây thứ mấy của tập"* tính bằng cách
quét thư mục, trong khi thời lượng voice **đã được đo lúc align**.

**LUẬT:** một khái niệm — một hàm. Nơi khác gọi, không tự suy lại.

### BH5. Số mặc định âm thầm nguy hiểm hơn báo lỗi

`avd_phut or 6` · `than or 0` (tắt luôn gợi ý chẻ khối) · energy nhạc rơi về
"medium". Máy chạy trơn tru bằng số bịa, và không ai biết mình đang xem kết quả
của tham số nào.

**LUẬT:** thiếu tham số bắt buộc thì **dừng và nói**, không tự điền số rồi chạy
tiếp. Số mặc định chỉ được phép ở tham số không bắt buộc.

### BH6. Phiên làm việc dài = vừa quên vừa hết hạn mức

Phiên 29/08 → 07/09 chạy liền 10 ngày: 24.789 dòng transcript, 64 MB, đỉnh
**999.711 token** (sát trần 1M), mỗi lượt hỏi nhỏ vẫn nạp lại hơn 300K token.
Kết cục 15:38 ngày 07/09 chạm hạn mức phiên và treo giữa chừng; 4 câu user gõ
chưa bao giờ được gửi đi.

**LUẬT:** cắt phiên theo ngày. Mỗi việc xong thì commit + ghi tài liệu **ngay**
— để phiên bị cắt ngang lúc nào cũng không mất gì.

### BH7. Test đi ra mạng thì không phải test

`do_kenh` có sẵn chỗ tiêm cho test (docstring ghi thẳng *"goi_vision tiêm được
cho test"*), nhưng **7/8 chỗ gọi trong `test_kenh.py` không dùng**. Hệ quả: mỗi
lượt chạy bộ test là một lượt gọi GLM vision THẬT — tốn tiền, và 07/09 một lượt
treo cứng ở `create_connection` (tìm ra bằng `py-spy dump` tiến trình đứng im).

Nguy hơn tiền: hai lượt "xanh" trước đó xanh vì **may mắn gọi được mạng**, không
phải vì bộ test độc lập.

**LUẬT:** test không được chạm mạng. Có sẵn chỗ tiêm mà không dùng thì coi như
chưa có. Bộ test chạy được khi rút dây mạng mới là bộ test thật.

### BH8. Log ghi ra file bị ĐỆM — đừng đọc tiến độ để đoán tốc độ

07/09 khuya: theo dõi `pytest > file.txt` thấy tiến độ "đứng yên" hàng chục
phút, kết luận máy chậm, thậm chí giết nhầm tiến trình vì tưởng chạy trùng.
Sự thật: pytest tự báo **303 giây** — đúng như mọi lượt. Ghi ra file (không
phải màn hình) thì stdout đệm theo khối, chữ hiện thành từng cụm.

**LUẬT:** tiến độ trong file log KHÔNG phải thước đo tốc độ. Muốn biết nhanh
chậm thì đọc con số tổng do chính công cụ in ra lúc kết thúc, hoặc đo bằng
`time`. Đừng suy luận từ số dấu chấm.

---

## Quy trình một đợt (user chốt 07/09)

```
1. Viết/cập nhật tài liệu TRƯỚC          <- kết luận không nằm trong đầu ai
2. Chạy bộ test lấy MỐC XANH             <- không xanh thì chưa được code
3. Viết code tối thiểu cho đúng việc đó  <- Karpathy #2, #3
4. Nghiệm thu bằng SỐ trên dữ liệu thật  <- BH3
5. Commit riêng từng đợt + cập nhật đúng 1 tài liệu
```

**Không tự nhận "xong" khi chưa chạy.** Test xanh chỉ nói code không gãy; nó
không nói tính năng tới được tay người dùng (BH2).

## BH9 — Lớp giao diện KHÔNG còn là vùng mù: Playwright + Chrome thật

**Bài học:** BH3 ghi "mắt user là kênh phát hiện lỗi duy nhất" cho JS, vì máy không có
Node. Điều đó ĐÚNG nhưng chưa đầy đủ — máy có sẵn **Playwright + Chrome thật** (cài từ
R5b cho Envato). Nạp được trình duyệt thật thì test được JS thật.

**Cách làm (xem `tests/test_preview_trinh_duyet.py`):** trích **nguyên văn** hàm cần
kiểm từ `index.html` bằng khớp ngoặc, nhét vào một trang tối thiểu với đồ giả cho
những gì nó gọi, rồi chạy trong Chrome. Không chép lại logic sang test — chép là test
xanh trên bản sao trong khi bản đang ship vẫn hỏng.

**Vì sao cần:** lỗi 08/09 "preview đen dù timeline có hình" nằm trọn trong 6 dòng JS.
Không có cách chạy thì chỉ còn suy luận, mà suy luận thì không phân biệt được ba giả
thuyết đều nghe hợp lý (server không trả video / thẻ video sai src / callback bị huỷ).
Chạy thật trong Chrome chỉ ra ngay giả thuyết thứ ba.

**Kèm theo — đọc log máy chủ TRƯỚC khi đoán:** `prod.log` cho thấy 121 lượt
`/api/sotra/khuc` đều **206**. Một dòng grep loại sạch nửa số giả thuyết trước khi
viết dòng test đầu tiên.
