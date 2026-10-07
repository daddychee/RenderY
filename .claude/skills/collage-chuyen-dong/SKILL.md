---
name: collage-chuyen-dong
description: Làm chuyển động collage art / 2.5D / kiểu Vox từ ảnh tĩnh (Master Frame AI, ảnh collage) bằng Python — tách layer, camera 3D có parallax, nối nhiều khung trong một đoạn thoại, nét vẽ tay, giấy xé, hậu kỳ Vox — xuất video. Dùng khi user đưa ảnh và muốn video chuyển động collage/parallax, hoặc đưa video mẫu collage để học thêm kỹ thuật.
---

# Chuyển động collage / 2.5D (không cần After Effects)

Đầu vào: 1..n ảnh (Master Frame AI hoặc ảnh collage) + thời lượng (voice hoặc số giây).
Đầu ra: video (mp4). Toàn bộ chạy LOCAL bằng Python, mặc định **0 credit**.
Danh mục + thông số: [ky-thuat.md](ky-thuat.md).
Clip chuẩn user đã duyệt (06/10/2026): `F:\AutoEdit\collage_test\out_CA\ca1_sang_ca2.mp4`.

**User chốt 06/10: BỎ After Effects.** Vox là một "nhà video" trong flow treatment (node Video,
model `VOX…`) — không làm UI riêng; cả đội editor dùng; độ dài = giây voice phân cảnh / số cảnh.

## Code sản phẩm (trong repo)
- `autoedit/autoedit/collage/dung.py` — động cơ torch (CPU/GPU cùng code), camera chung, sắp lớp
  xa→gần (`tang` để ép), z-buffer, lộ mép. `nhip.py` — lò xo, VOT_DAU, posterize, wiggle.
- `collage/mau.py` — mẫu "VOX · Chiều sâu" (Depth Anything + mã camera `cd` của treatment) và
  "VOX · Pop-up 2.5D" (`dung_popup`: vật NẢY ngắn 12% + phóng 92→100% — trồi 0,75 khung làm lộ
  vùng LaMa vá, đo thật 06/10).
- `collage/tach.py` — tách tự động: mảng gần (Otsu độ sâu) -> điểm -> SAM 2.1 small (transformers,
  tiền xử lý TỰ LÀM vì processor đòi torchvision) -> chọn phương án MÉP GÃY độ sâu rõ nhất; loại mask
  chạm cả trái+phải (mặt biển/đất); cờ `khong_tach_duoc_vat` / `diem_sam_thap` / `mep_yeu`.
  `tach_theo_diem`: editor bấm (1 vào vật, 0 không phải vật), không gắn cờ. Đo 5 cảnh: tốt ~3/5.
- `collage/kho_tach.py` — bản tách lưu THEO CẢNH (`<goc>/canh/<tập>/<mã>/`), bỏ khi ảnh đổi (băm).
- Treatment: `vox-tach` (POST điểm tỉ lệ 0..1 -> dựng lại đúng cảnh), `/vox-tach/xem`, `/api/tap/{tap}/vox-co`
  (▲ trên thẻ). Icon trang CHỈ dấu hình học đơn sắc — ⚠ bị test cấm, dùng ▲.
- `collage/hang_doi.py` (SQLite riêng, chia lượt theo người) · `collage/tho.py` (thợ dựng, tiến trình riêng).
- `aigen/vox.py` — nhà VOX, 4 hàm như Seedvis; `treatment/app.py::_VeVideo` chuyển hướng `VOX…`/`vox-…`.
- Test: `test_collage_*`, `test_aigen_vox`, `test_treatment_vox(_chrome)`; mốc vàng ca1→ca2 ở
  `F:\AutoEdit\collage\vang\` (PSNR ~59 dB). Cổng thử: kho chép `backup()` ở `F:\AutoEdit\collage\thu_9131\`.
- Code thử nghiệm cũ (cv2, chưa vào repo): `F:\AutoEdit\collage_test\` — `ky_thuat.py` (cọ, giấy xé, Vox…).

## Môi trường (venv RIÊNG — không cài vào venv dự án)
- `F:\AutoEdit\collage_test\.venv_seg` (Python 3.13, torch CPU + ultralytics + transformers +
  simple-lama-inpainting). Dựng lại nếu mất:
  `uv venv .venv_seg --python 3.13` → `uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`
  → `uv pip install ultralytics transformers` → `uv pip install --no-deps simple-lama-inpainting`
  (KHÔNG bỏ `--no-deps`: gói đòi pillow 9.5, build hỏng trên Python 3.13).
- Đặt `UV_CACHE_DIR` và `HF_HOME` trên ổ F. Luôn `PYTHONUTF8=1` (thiếu là chết ở `print` tiếng Việt).
- ffmpeg: `C:\OutlierY\tools\ffmpeg\bin\ffmpeg.exe`. Tải YouTube: `python -m yt_dlp` của venv dự án +
  PATH có `C:\OutlierY\tools\deno`; `--download-sections` bị TREO → tải cả file video-only rồi cắt.
- Model: SAM 2.1-L (`sam2.1_l.pt`, tự tải), **Depth Anything V2 SMALL** (Apache 2.0 — Base/Large là
  CC-BY-NC, CẤM dùng cho video thương mại), LaMa (big-lama, tự tải).

## Quy trình
1. **Hỏi trước khi làm** (LUẬT CỨNG 2 của dự án): khung hình (16:9 hay theo tỉ lệ ảnh), thời lượng,
   phong cách (mượt + motion blur như ca1→ca2, hay giật 12 fps kiểu Vox). Có tiêu credit → báo giá trước.
2. **Tách layer** (chi tiết bảng 1 ky-thuat.md):
   - SAM 2 + `multimask_output=True`, chọn mask LỚN NHẤT có điểm ≥ 0,8×max. Không multimask = mất phần
     tối (vai áo, chân vật). ultralytics không đưa tham số ra → bọc `sam.predictor.inference`.
   - Điểm gợi ý do PYTHON đo: có nền sạch → lấy từ mảng |gốc − nền| (distance transform); không có →
     đọc toạ độ trên ảnh kẻ lưới. Giữ mảng liền lớn nhất (bỏ lốm đốm).
   - Vá nền sau vật: LaMa. Lỗ to giữa TRỜI → nội suy màu trời theo từng hàng (LaMa ra mảng xám).
     Vật tròn/đối xứng bị che → vẽ nốt bằng soi gương.
   - Độ sâu nền: Depth Anything. Trời/mây phẳng → đặt hằng số, đừng tin bản đồ.
3. **Dựng cảnh** — MỘT camera pinhole cho mọi lớp: `xo = F*(X*Z0 - tx)/(Z - Tz) + pan`.
   Bù scale để khung đầu khớp ảnh gốc. Nền có độ sâu từng pixel (giải ngược 3 vòng).
   Z-buffer: mảnh `z_test` bị nền gần hơn che (núi che bưởi). **Sắp lớp xa→gần trước khi ghép.**
4. **Biên đạo** (bảng 2–5 ky-thuat.md): nhịp lò xo / vọt-đậu, giữ theo lượng chữ, nối khung.
   Nối hai cảnh bằng VẬT CHUNG: camera bám vật lúc lia vút, cắt ở đỉnh tốc độ; vị trí + cỡ vật ở điểm
   cắt TÍNH BẰNG CHÍNH công thức chiếu của cảnh sau (viết tay từng lệch ~70 px, 11% cỡ).
5. **Kiểm + đo trước khi báo "xong"** (bắt buộc, có số):
   - Lộ mép nền = 0,00% ngoài lúc lia vút (đo theo từng khung, tìm đúng khung lỗi rồi mới sửa).
   - Vật nối cảnh: (x, y, rộng) cuối cảnh trước == đầu cảnh sau.
   - Đo nhịp/parallax bằng `do_parallax_nhip.py`, so với mẫu; soi 8–16 khung bằng mắt.
   - Chế độ `--xem` (8 khung) trước khi render cả clip — rẻ hơn nhiều.

## Luật đo (đã từng tự lừa mình)
- Parallax đo bằng phần flow DƯ sau khi khớp zoom+pan, **chỉ trong đoạn CHỈ-CAMERA** (vật tự chạy làm
  thước ra số ảo). Tỉ lệ vô nghĩa khi chuyển động nhỏ — dùng px/khung tuyệt đối, mức nhiễu ~0,1.
- Tốc độ dùng TRUNG BÌNH flow (trung vị = 0 khi phần lớn khung đứng yên).
- Video mẫu đăng LẶP KHUNG → gộp theo cửa sổ 1/12 s trước khi tìm đỉnh.
- Đổi tiêu cự trên tấm phẳng = phóng đều, KHÔNG ra parallax. Parallax chỉ đến từ camera DỊCH.
- Kết quả chưa đạt thì nói thẳng con số chênh với mẫu — user đã bác clip "chỉ scale" (v2).

## Giới hạn đã biết
- Parallax mạnh cần ẢNH DƯ MÉP: 1 Master Frame chỉ dư ~65–210 px → lệch tầng ~10x yếu hơn mẫu
  Parallaxer. Muốn mạnh: tạo ảnh rộng hơn khung 20–30% và nhiều tầng.
- Render CPU chậm (80–115 s / 1 s video có motion blur hoặc glow/echo/DOF). Chưa tối ưu.
- Tách layer AI trả phí đã đo (06/10): fal Qwen-Image-Layered $0,05/ảnh nhưng layer 864x480, tiền
  cảnh mép khung dính nền; Seedvis Nano Banana Pro nền sạch rất tốt, khớp 0 px, 8 credit (~185đ)/ảnh,
  tài khoản DÙNG CHUNG production — hỏi trước khi tiêu.

## Mở rộng kỹ thuật
User đưa mẫu (link + mốc giây + 1 câu mô tả) → tải, lấy phụ đề (video hướng dẫn), soi khung, đo flow →
thêm hàng vào ky-thuat.md + hàm vào `ky_thuat.py` + 1 clip thử + 1 phép kiểm. User duyệt mới giữ.
Mẫu đã học: xem bảng "Nguồn" cuối ky-thuat.md.
