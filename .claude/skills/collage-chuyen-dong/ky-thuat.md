# Danh mục kỹ thuật — thông số mặc định

Hàm = trong `F:\AutoEdit\collage_test\ky_thuat.py` (hoặc script mẫu ghi rõ). Trạng thái: ✅ đã dùng
trong clip thật · 🧪 đã có hàm, chưa vào clip duyệt · 🆕 chưa làm.

## 1. Tách layer
| Kỹ thuật | Cách / hàm | Thông số | |
|---|---|---|---|
| Cắt vật | SAM 2.1-L multimask (`chuan_bi_ca.py: cat`) | chọn mask lớn nhất, điểm ≥ 0,8×max | ✅ |
| Điểm gợi ý từ dữ liệu | mảng \|gốc − nền sạch\| → distance transform | 6 điểm/vật, ngưỡng chênh 0,16 | ✅ |
| Vá nền | LaMa | nới mask 25 px | ✅ |
| Vá trời lỗ to | `lap_troi`: nội suy theo hàng | trời = độ sâu ≤ p30 + 0,05 (trời = 0,00 đúng p30) | ✅ |
| Vẽ nốt vật đối xứng | `ve_not_buoi`: soi gương dọc→ngang→tâm, còn sót → inpaint | — | ✅ |
| Độ sâu | Depth Anything V2 Small → Z = 1/(v(1/Zn − 1/Zf) + 1/Zf) | ca1: Zn 3, Zf 40 | ✅ |

## 2. Camera + không gian
| Kỹ thuật | Cách | Thông số | |
|---|---|---|---|
| Camera chung | `xo = F*(X*Z0 − tx)/(Z − Tz) + pan` | dịch (tx,ty,Tz) = parallax; pan = xoay nhỏ | ✅ |
| Cẩu máy | pan_y + ty cùng lúc | ca1: pan 200→−150, ty −300→150 | ✅ |
| Dolly zoom | Tz lùi + F tăng giữ cỡ chủ thể | F = (Z_cđ − Tz)/(Z_cđ − Tz0) | 🧪 |
| Z-buffer | alpha mảnh × clip((Z_nền − Z_mảnh)/(0,06 Z_mảnh) + 0,5) | đặt Z vật bị che = 1,25 × p90 độ sâu vật che | ✅ |
| Dư mép khi hãm | phóng F 15% lúc vào cảnh, lùi chậm hơn cú hãm | cần F ≥ (H/2 + \|py\|)/(MH/2) | ✅ |
| Phản chiếu mép lúc lia vút | BORDER_REFLECT khi \|py\| > vùng dư | motion blur che | ✅ |
| Z kiểu AE (Vox) | Z = (z_AE + 2666,7)/1000 | nền 15000 · bụi 8000 · chữ năm 8500 · người 2500 · chữ 0 | 🧪 |
| Lấy nét theo camera | mờ σ = 20·\|1/d − 1/d_nét\| | nét: chữ năm → người → mặt phẳng chú thích | 🧪 |

## 3. Nhịp
| Kỹ thuật | Hàm | Thông số | Nguồn đo | |
|---|---|---|---|---|
| Lò xo bật–đậu | `lo_xo(zeta, t90)` | vào 0,3 s, zeta 0,6–0,85 (vượt đà nhẹ) | Rockefeller | ✅ |
| Vọt–đậu (Vox) | `VOT_DAU = bezier(0.2,0,0.05,1)` | cú 0,85 s, đỉnh 0,11 s | demo Vox: đỉnh 0,08–0,17 s | 🧪 |
| Giữ theo lượng chữ | `giu_theo_chu` | 0,7 + 0,035×ký tự, kẹp 1–2,2 s | Vox 16:00 | 🧪 |
| Xuất phát lệch | — | 0,2–0,4 s giữa các mảnh; số lệch 6 khung | Vox 22:00 | ✅ |
| Motion blur | lấy mẫu trong cửa trập 180° | số mẫu theo quãng dịch, trần 12–16 | AE | ✅ |
| Posterize | `posterize(t, fps)` | toàn cảnh 12 fps (Vox) · glow/chớp 6 · rung nét 3 | Vox 38:00 | 🧪 |
| Wiggle | `nhieu_muot(seed, hz, t)` | rung máy 1 Hz 10 px | Vox 36:00 | 🧪 |

## 4. Nối khung / chuyển cảnh
| Kỹ thuật | Cách | | |
|---|---|---|---|
| Vật chung nối cảnh | camera bám vật lúc lia vút, cắt ở đỉnh tốc độ, đích tính bằng phép chiếu cảnh sau | ca1→ca2 | ✅ |
| Mọc từ sau vật che | dịch mảnh xuống + Z-buffer | bưởi sau núi | ✅ |
| Tiền cảnh quét qua | dải giấy Z 1,8 giữa đường bay camera | collage 3 trạm | ✅ |
| Trạm trên canvas rộng | mảnh đặt theo trạm; mảnh xa thuộc 1 trạm PHẢI có vào/ra | lỗi trăng hiện mọi trạm | ✅ |
| Camera tham quan cụm chú thích | key (t, Cx, Cy, Tz), cụm chiếm ~62% bề ngang | Vox | 🧪 |
| Giấy xé làm mặt nạ | `GiayXe(w,h,seed,truc,thoi_gian)` — xé từ giữa, mép 3 tầng răng cưa + viền xơ | Vox 23:30 | 🧪 |
| Chớp màu trước khi hiện | bản `to_mau` vàng xé trước 6 khung | Vox 25:30 | 🧪 |

## 5. Chất liệu collage + chữ
| Kỹ thuật | Hàm | Thông số | |
|---|---|---|---|
| Viền giấy trắng + bóng | `collage_chuyen_dong.py: thanh_manh` | viền 7 px răng cưa, bóng lệch (14, 9) blur 9 | ✅ |
| Dải giấy xé / nền giấy | `dai_giay`, `giay_nen` | — | ✅ |
| Nét cọ hiện dần (Trim Paths) | `NetCo(diem, be_day, mau, seed).anh(tien_do, t)` | so ngưỡng bản đồ độ dài cung, mép trim 3 px | 🧪 |
| Gạch chân tay | `duong_gach` | cong 2%, vượt đầu 4%, run tay | 🧪 |
| Vòng khoanh tay | `vong_khoanh` | 2,1–2,4 vòng, méo 10/6/3%, không khép | 🧪 |
| Rung nét (boil) | 3 texture xoay vòng posterize 3 | — | 🧪 |
| Chữ năm khổng lồ kẹp sau chủ thể | Libre Caslon Display, kem, sáng 70%, blend lighten | 100% làm chú thích khó đọc | 🧪 |
| Lấp lánh trong chữ | `lap_lanh` | mật độ đốm 6% | 🧪 |
| Vệt đuôi (Echo) | vẽ 10 bản trước đó, cách 1/48 s, đậm 0,3 | 0,5 = răng lược | 🧪 |
| Khối số liệu | nhãn đậm trong hộp kem + dòng phụ + số Display | — | 🧪 |
| Tritone ảnh cũ | `tritone` | tối/giữa/sáng nâu-sepia-kem | 🧪 |
| Glow | `glow` (bloom 3 tầng) | — | 🧪 |
| Grain | `grain` + `overlay` | cường độ 1,2, cỡ 1,3, overlay 33% | 🧪 |
| Lưới / bụi | `luoi`, `bui` | lưới 60 px 12% · bụi screen 45% chập chờn | 🧪 |
| Chớp sáng máy chiếu | curves gamma 0,8 × độ mờ posterize 6 | — | 🧪 |

## Nguồn
| Mẫu | Dạy gì | Thông số đo |
|---|---|---|
| MagnatesMedia "Rockefeller" youtube fNh_GyRbJDA từ 0:50 | pop-up 2.5D, giữ nền thay nhân vật | camera 1–5 px/khung; bật 0,3 s đậu 1–1,5 s |
| Parallaxer V2 youtube sOWZgSLndE4 ~4:31 | bay xuyên ~10 lớp vẽ riêng | lệch tầng 14–23 px/khung |
| createdaley "Edit Like Vox" youtube sgYxZAEEPCY (44') | thiết kế + AE kiểu Vox (bảng đầy đủ: `ref3/TONG_KET_KY_THUAT.md`) | 4 cú/10 s, đỉnh 0,08–0,17 s, zoom 20–79 %/s |

## Việc còn mở
- Zoom tour Vox nhẹ hơn mẫu (16–29 vs 20–79 %/s) → cho camera lao sâu hơn.
- Thời lượng cú di chuyển nên co giãn theo quãng (cú ngắn bị đỉnh muộn 0,5 s).
- Tối ưu render (cache glow/echo, DOF chỉ khi σ đổi).
- Luật né chồng chéo chú thích ở toàn cảnh.
