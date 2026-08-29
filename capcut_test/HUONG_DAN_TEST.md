# Hướng dẫn test draft CapCut (Phase 0 — bài test quan trọng nhất)

Mục đích: kiểm tra **bản CapCut công ty đang dùng có mở được draft do tool sinh ra không**. Kết quả quyết định kiến trúc xuất file của AutoEdit.

## Draft test chứa gì
Timeline 15 giây mô phỏng đúng cấu trúc tool sẽ sinh: 2 đoạn voice có **khoảng hình thở** ở giữa (giây 2.5–5), nhạc nền có **keyframe volume** (tự to lên lúc hình thở, nhỏ lại khi voice quay lại), 3 shot footage ở layer 1, **layer 2 picture-in-picture** góc phải trên (giây 8–10) kèm SFX và chữ "$2", 1 dòng text ở đầu, fade-out cuối video. (Hình ảnh/âm thanh là file test máy tự sinh — màu và tiếng bíp, không phải footage thật.)

## Cách test

### Nếu test trên máy Mac này
1. Mở CapCut → Settings (⚙️) → **Draft location** — ghi nhớ đường dẫn folder draft
2. Copy folder `ban_mac/PADOMA_TEST` vào folder draft đó
3. Khởi động lại CapCut (hoặc vào rồi thoát một draft có sẵn để refresh danh sách)
4. Mở draft **PADOMA_TEST**

### Nếu test trên máy edit Windows
1. Copy folder `assets` vào ổ C, thành đúng đường dẫn: `C:\PADOMA_TEST\assets\` (bắt buộc đúng vị trí này)
2. Mở CapCut → Settings → **Draft location** — ghi nhớ đường dẫn (thường là `C:\Users\<tên>\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft\`)
3. Copy folder `ban_windows\PADOMA_TEST` vào folder draft đó
4. Khởi động lại CapCut → mở draft **PADOMA_TEST**

## Checklist kết quả (chụp màn hình gửi lại)
- [ ] Draft PADOMA_TEST có xuất hiện trong danh sách project?
- [ ] Mở được, không báo lỗi/crash?
- [ ] Thấy đủ 6 track: 2 video, 1 text, 3 audio?
- [ ] Voice có khoảng trống giây 2.5–5 (hình thở)?
- [ ] Nhạc nền nghe được volume thay đổi (to lên ở giây 3–4.5)?
- [ ] Layer 2 (khung đỏ nhỏ góc phải trên) + chữ "$2" xuất hiện ở giây 8?
- [ ] Kéo thả, sửa được các segment bình thường?

## Đọc kết quả
- **Tất cả ✅** → bản CapCut hiện tại dùng được, Phase 0 cứ thế triển khai.
- **Draft không hiện / mở bị lỗi** → bản CapCut mới đã chặn draft ngoài. Phương án: cài thêm một bản CapCut cũ hơn để test lại (tôi sẽ hướng dẫn chọn version), hoặc chuyển kiến trúc sang DaVinci Resolve.
- **Mở được nhưng thiếu track/keyframe** → ghi lại thiếu gì, tôi điều chỉnh cách sinh draft.
