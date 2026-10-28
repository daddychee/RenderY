# Nâng cấp `/bien-kich` theo cách làm của drama (chốt 2026-10-04)

Áp cho niche fantasy-drama và sinh-vat-bao-ve (đang làm thật, Seedance 100%), và mọi niche loại phim thường sau này. Drama (`/bien-kich-drama`) không đổi.

## Điều đã chốt với anh/chị

- Một skill `/bien-kich` dựng lại theo kiểu drama; phần riêng niche nằm ở `kien-thuc/khung/<niche>.md`.
- Phần dài **khoảng 7 phút** (5–9), viết rồi soát từng phần, lần lượt; **mặc định dừng sau phần 1** để gen thử.
- Hợp đồng khán giả mỗi niche do editor nhập theo `HUONG-DAN-HOP-DONG-KHAN-GIA.md`; khi chưa có, khung mục 0 để chỗ trống và skill hỏi ở bảng hỏi.
- Không còn phim đang viết dở theo khuôn cũ: bỏ chat 1, chat 2, file trợ lý cũ. Không chép `.agents/`, `.codex/`, `AGENTS.md`.

## Giữ nguyên (web đọc, không đổi được ở đây)

Khuôn web loại phim thường (`cong-cu/luat_kich_ban.py`, bản chép): phần đầu có `# Tên`, dòng `Thể loại: … · Dài: … · Lời bình: …`, `## Bảng nhịp` (cột Mã N01 liên tục, Mức 1–5), `## Mô típ`, `## Cụm cố định`; mỗi hồi `# Hồi n: tên`, cảnh `## Pxx · tên · 15s · Nyy`, cuối hồi `## Bảng trạng thái liên tục` và `## Để viết hồi sau`. Khuôn cảnh, loại clip, ngân sách 6 clip mỗi phút, bảng phân clip, `dem_phan_canh.py`, `kiem_kich_ban.py` (gộp), `danh_lai_ma.py` giữ.

## Khuôn `00-nhip.md` mới (giao ước giữa các phiên)

Thêm ba mục, bỏ hai cột:

```
# <Tên phim>
Thể loại: fantasy-drama · Dài: 30 phút · Lời bình: <tiếng, giọng> · Thoại: <ít | nhiều>
## Tựa và thumbnail
Tựa: <tựa YouTube tiếng Anh>
Thumbnail: <ai, mặc gì, đang làm gì>
Phim mẫu: <tựa, link> · Thủ pháp giữ: <…> · Khác phim mẫu ở: <nơi, vật, hành động chính>
Trả tựa ở: N02
## Logline
## Cảm xúc chủ đạo
## Khoảnh khắc chạm
## Ba hồi
## Bảng nhịp
| Mã | % | Loại | Cảnh | Sự kiện | Vì nhịp | Cảm xúc khán giả | Mức |
## Bảng phân clip
## Gieo và gặt
| Mã | Loại | Điều | Gieo ở (bằng gì) | Gặt ở |
| G01 | lật | Sinh vật nhớ tiếng còi của cô bé | N03, cô thổi còi | N24 |
## Thang vùi dập
## Mô típ
## Cụm cố định
## Phần
| Phần | Hồi | Nhịp | Phút | Clip |
| 1 | 1 | N01–N06 | 6,5 | 39 |
```

- **Bảng nhịp bỏ cột Gieo và Trả ở**; logic gieo, gặt sang bảng Gieo và gặt (web bỏ qua mục lạ; kiểm Gieo/Trả của web chỉ chạy khi có cột).
- **Gieo và gặt:** loại `lật`, `dẫn sai`, `phi lý`, `vết`, `biết`, `vật` (như drama). Gieo ở bắt đầu bằng mã nhịp; Gặt ở: `N05`, `N26, N29`, `tới N06` (vết), `—` (phi lý). Mỗi trận một dòng `lật` "thắng nhờ …". `vết` ghi trái, phải của chính nhân vật (hay cả người, hai bên). `dẫn sai` mỗi phần nên có (NHẮC, không LỖI: niche ít thoại khó làm).
- **Mô típ giữ** (vật, âm thanh, câu lặp 3–4 lần; bàn tay ở sinh-vat-bao-ve).
- **Trả tựa ở:** mã nhịp nơi điều tựa và thumbnail hứa hiện ra; phút tối đa do khung ghi (mục 0); máy chỉ kiểm mã có thật.
- **Phần:** 5–9 phút (phút = clip / 6), cắt ở ranh giới nhịp, không trùm hai hồi (hồi dưới 5 phút gộp với phần kề thì phần ghi hai hồi, như cũ). Nhịp nào cũng thuộc đúng một phần.
- Cột Sự kiện của Bảng nhịp tối đa 2 câu; mã kho `KBxx` ghi cuối ô như cũ, cả phần khoảng 6 mã.
- Nhịp quay lại mạch đã vắng quá 2 nhịp: cuối Sự kiện ghi `(nhắc: <điều>)`.

## File hồi: thêm một dòng

Cuối `## Để viết hồi sau` của hồi đang viết, mỗi phần một dòng: `- Gieo, gặt phần <n>: G01 P003, G04 P021` (mã G và cảnh nơi gieo hay gặt trong phần). Mục này vẫn tối đa 30 dòng, ghi đè mỗi phần.

## Phiên và file của từng phiên (chỉ sửa file của mình)

| Phiên | File |
|---|---|
| A · khung | `kien-thuc/khung/fantasy-drama.md`, `kien-thuc/khung/sinh-vat-bao-ve.md` |
| B · luật cảnh | `kien-thuc/phan-canh.md`, `kien-thuc/soat-phan-canh.md`, `kien-thuc/phan-clip.md` |
| C · công cụ | `cong-cu/dan_y.py` (mới), `cong-cu/test_dan_y.py` (mới), `cong-cu/doc_phan.py`, `cong-cu/dem_phan_canh.py` (chỉ nếu cần cho cột Gieo bỏ) |
| D · skill (chat chính) | `.claude/skills/bien-kich/`, `.claude/agents/viet-phan.md`, `soat-phan.md`, `CLAUDE.md`, `NHAT-KY.md`, `HUONG-DAN-PHIM.md` |

Mỗi phiên cuối việc ghi `kinh-nghiem/nang-cap-bien-kich/bao-cao-X.md` (tối đa 15 dòng: đã làm gì, tên mục và lệnh thật, token, điều lệch kế hoạch). Không ghi `NHAT-KY.md`, không commit, không sửa bản chép (`tu-web/`, `kho/`, `luat_kich_ban.py`, `muc_luc.py`, `luat_kho_bien_kich.py`).

## Ngân sách token (đo bằng `python cong-cu/muc_luc.py`)

| Thứ | Đích |
|---|---|
| Mỗi khung | ≤ 6.000 (mục 0–1 ≤ 2.000) |
| `SKILL.md` | ≤ 5.000 |
| Mỗi trợ lý | ≤ 2.500 |
| `doc_phan.py` một phần | ≤ 9.000 |
| Trợ lý viết đọc trước khi viết | ≤ 28.000 (phần có trận ≤ 35.000) |
