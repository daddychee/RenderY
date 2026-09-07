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
