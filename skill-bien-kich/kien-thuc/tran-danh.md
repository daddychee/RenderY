# Trận đánh (Spec 39 A)

Đọc khi bảng nhịp có nhịp trận (đánh, rượt, săn, bắt, quái vật tấn công), trước khi viết bảng phân clip và cảnh trận.

## Số clip

Mỗi clip trận chở **đúng một lần đổi thế**: bên thắng thế đổi, hay tình thế xấu hẳn đi. Clip ghi loại `việc`. Nhiều lần đổi thế trong một clip là trận nhồi.

| Cỡ | Là gì | Clip `việc` tối thiểu | Trần |
|---|---|---|---|
| xô xát | va chạm ngắn, chưa phân thắng thua lớn | 3 | 4 |
| chính | trận đổi tình thế của hồi | 6 | 10 |
| cuối | đỉnh phim | 10 | 16 |

- `lật`, `sau đỉnh` cộng thêm ngoài trần. Trận cuối có cú lật lớn nhất thì chuỗi `lật` nằm trong trận.
- Clip trận **không tính vào ngân sách** 6 clip mỗi phút; máy tự trừ.
- Bảng phân clip ghi: `việc 8 (trận chính T1)`.
- **Phim `Clip: 30s`:** cảnh trận 30s chở **hai lần đổi thế** (2–4 đòn mỗi lần), không buộc chia ở giây 15; số ở bảng trên tính bằng đơn vị 15 giây (chính 6–10 = 3–5 cảnh 30s). Bảng phân clip ghi số cảnh: `việc 4 (trận chính T1)` là 8 đơn vị. Khối thiết kế trận một dòng mỗi lần đổi thế (mục dưới). Cảnh trận 30s: 12–14 shot, mỗi shot 2–3 giây; giữa trận một cảnh rộng cho thấy lại ai đứng đâu, đặt ở chỗ trận đổi thế; cảnh cuối trận dừng khi người chính còn đang làm một động tác, không đứng thở.

## Bậc

Đặt cược → chạm đầu → leo thang (lặp được: nhanh hơn, mạnh hơn, không gian hẹp hơn, cái giá lớn hơn) → đảo thế → cú đỉnh → hậu quả.
- **Đảo thế có lý do người xem thấy**: người thân gọi, lời hứa, ký ức, vết thương của người mình thương. Không thắng nhờ ngoại lực (sét, nước cuốn, kẻ địch tự sơ hở).
- Kẻ thua không gục quá nhanh; cái chết có một clip dư âm.
- Hậu quả thấy cái giá: thương tích, đồ mất, người ngã; kẻ ác thua có phản ứng; người thân phản ứng.

## Khối thiết kế trận

Trong hồi, **ngay trước cảnh đầu trận**. Ví dụ đã điền trọn (trận chính, 6 clip việc, một clip nối giữa trận); chép khuôn này, không lấy khối trận cũ làm mẫu:

```
## Thiết kế trận T1: Vây mộ · cỡ chính · P09–P16
- Hai bên: NV01 (lối đánh: LD03; tay trái, không đá) đấu NV05 + 3 người phụ (PH1 áo choàng đỏ, PH2 mũ sắt, PH3 cầm giáo)
- Kết cục: NV01 thắng, mất khăn, rách vai trái; NV05 bỏ chạy
- Nơi: DD03 nghĩa trang tuyết. Lúc đầu: NV01 giữa hai bia, bọn kia vây ba phía; lối thoát: cổng sắt phía bắc
- Đồ môi trường: xích cổng (P11), bia đổ (P14)
- Lý do đảo thế: nghe tiếng con gọi (P13)
| Cảnh | Bậc | Câu hỏi kịch tính | Đổi thế | Cú đỉnh | Cuối cảnh |
|---|---|---|---|---|---|
| P09 | đặt cược | Bọn chúng có tìm ra mộ? | ba người phụ vây kín mộ | | NV01 giữa hai bia; còn 3 người phụ đứng |
| P10 | chạm đầu | Cô có giữ được mộ? | cô quật PH1 xuống tuyết, NV05 dồn cô về phía cổng | | NV01 lùi sát cổng; còn 2 người phụ đứng |
| P11 | leo thang | Cô có thoát qua cổng? | PH2 quấn xích cổng khóa lối thoát | | NV01 bị kẹt giữa cổng và bia; còn 2 người phụ đứng |
| P12 | nối | – | – | | NV01 chạy dọc hàng bia về phía mộ; còn 2 người phụ đứng |
| P13 | đảo thế | Cô còn sức đứng dậy? | nghe con gọi, cô ôm hông PH2 quật xuống, khóa tay | | NV01 đứng trên mộ, vai trái rách; còn 1 người phụ đứng |
| P14 | cú đỉnh | Cô có hạ được NV05? | cô bắt chân NV05 quật vào bia, bia đổ | TP109 | NV05 nằm cạnh bia đổ; PH3 lùi, giáo chĩa xuống; còn 1 người phụ đứng |
| P15 | hậu quả | NV05 có quay lại? | NV05 bò dậy, bỏ chạy qua cổng | | NV01 quỳ, mất khăn; còn 1 người phụ đứng |
| P16 | sau đỉnh | – | – | | NV01 ôm con bên mộ; PH3 ngồi bệt; còn 0 người phụ đứng |
```

- **Mọi cảnh trong Pa–Pb có một dòng**, kể cả clip `nối`, `sau đỉnh` nằm giữa hay cuối trận (ô Bậc ghi loại, ô Câu hỏi và Đổi thế ghi `–`). Phim `Clip: 30s`: cảnh 30s có **hai dòng**, cột Cảnh ghi giây của từng lần đổi thế (`P09 0–17`, `P09 17–30`), mỗi dòng một lần đổi thế và `còn N người phụ đứng`.
- **Hai bên:** lối đánh chọn từ `thu-vien-hanh-dong.md` mục Lối đánh, ghi mã; mỗi người phụ một nét riêng thấy được và một loại vũ khí riêng (hai kẻ cùng kiểu mũ hay cùng loại vũ khí thì model đổi vũ khí, nhân bản người). Lối đánh ghi gì thì cảnh đánh đúng thế ấy (ghi "túm, húc" thì cảnh không đấm).
- **Cú đỉnh:** chọn từ mục Cú đỉnh, ghi mã TP; mỗi cú một lần cả phim. Chưa có cú hợp thì tả bằng lời.
- **Đồ môi trường:** mỗi món dùng một lần (một món ở một dòng Đổi thế), ghi cảnh dùng, phải có ở nơi đánh (sẽ thành ảnh nơi chốn). Không có trong ảnh thì model tự dựng ra.
- **Lý do đảo thế:** bắt buộc với cỡ chính và cuối.
- **Cuối cảnh:** vị trí, thương tích, vũ khí, `còn N người phụ đứng`. Đầu cảnh sau là cuối cảnh trước. Người phụ tăng thì ô Đổi thế ghi ai vào.
- **Đổi thế:** một lần mỗi dòng, không dùng `;`.

## Nối trước và sau

- Clip đầu trận hay clip `nối` ngay trước cho thấy toàn cảnh nơi đánh: ai ở đâu, đủ đồ môi trường sẽ dùng.
- Cảnh trận viết theo khuôn thường; "Hành động theo nhịp" cho thấy đòn trúng và hậu quả, người phụ ngã từng người một.
- Trạng thái cuối trận thành dòng của `## Bảng trạng thái liên tục`, từ cảnh cuối trận.

## Tránh

Cả trận trong một hai clip; trận toàn đỡ; vồ từ trên cao xuống; hất nước che mắt; tự viết tia lửa, sàn nứt, mảnh vỡ bay (prompt lo phần vật lý).
