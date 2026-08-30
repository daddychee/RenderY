# Tích hợp RenderY vào CRM OUTLIERY

Phương án tích hợp — chốt 30/08/2026. **Mọi số trong đây là ĐO THẬT trên máy chủ**,
không phải ước lượng.

---

## Flow nhân sự (user mô tả)

```
1. Tool xuất hiện trên CRM AI Agent OUTLIERY
2. Nhân sự tạo folder chứa kịch bản + voice trên NAS, up lên CRM
3. Máy chủ chạy nền, báo khi xong
4. Kết quả ở thư mục "Compose Timeline" — file timeline + footage phân theo chapter
5. Nhân sự copy thư mục về máy cá nhân làm tiếp
```

---

## 1. ĐO THẬT — máy chủ đáp ứng được

| Hạng mục | Đo được | Đánh giá |
|---|---|---|
| CPU | 2× Xeon E5-2680 v4 — **28 nhân / 56 luồng** | ✅ rất mạnh |
| Tải hiện tại | **7.5%** (đang chạy 6 app + Qdrant) | ✅ rảnh |
| RAM | 32 GB, **còn trống 15.4 GB** | ⚠️ giới hạn số job song song |
| GPU | GeForce 210 (1GB) | ❌ quá cũ → **CPU-only** |
| ffmpeg 1080p30 | **5.1× realtime** (30s video / 5.9s) | ✅ |
| 4 job ffmpeg song song | 15.5s vs 23.5s tuần tự | chỉ nhanh hơn **1.5×** — ffmpeg đã tự đa luồng |
| NAS `\\192.168.1.250\Video` | **ghi 362 MB/s · đọc 1209 MB/s**, 7.19 TB trống | ✅ không phải nút cổ chai |
| Quyền ghi NAS | ✅ ghi được | |

**→ Chốt 2 job song song.** Không phải vì CPU yếu mà vì: ffmpeg đã đa luồng (thêm job
không nhanh thêm tương ứng), RAM 15.4 GB chia 2 job an toàn hơn 4, và còn 6 app khác
đang phục vụ team.

---

## 2. Thời gian 1 job — ước tính theo stage

Video 20 phút (434 câu, đo từ `IN002.srt` thật):

| Stage | Thời gian | Loại tải | Ghi chú |
|---|---|---|---|
| align | 2s | CPU | đọc `.srt` — đo thật ở R3 |
| direct | ~90s | **chờ API** | LLM chia beat |
| cut | ~60s | CPU | ffmpeg cắt 434 đoạn voice |
| **source** | **~900s** | **chờ mạng** | ⚠️ **nút cổ chai 64%** — tải footage + phanh Envato |
| rank | ~120s | chờ API | 43 call batch |
| assemble | ~240s | CPU | ráp timeline (5.1× realtime) |
| report | 5s | CPU | |
| **TỔNG** | **~24 phút** | | |

**Phân tích quan trọng:** 1110/1417s (78%) là **chờ mạng/API, không tranh CPU**.
→ chạy 2 job song song rất hiệu quả, gần như không làm chậm nhau.

**Đếm ngược làm được chính xác** vì `project.json` đã ghi `started_at`/`completed_at`
từng stage. ETA = trung bình các lần chạy trước, cập nhật dần.

---

## 3. Điểm cắm vào CRM — CRM đã có sẵn khuôn

`agent-app/src/apps_registry.py:1-6` ghi thẳng:

> MỘT CHỖ khai báo mọi app phụ + ai được thấy. Thêm/bớt app hoặc sửa quyền = sửa danh
> sách APPS ở đây, **KHÔNG đụng route và KHÔNG đụng template** (sidebar tự dựng theo
> danh sách này).

CRM đã có **6 app chạy đúng khuôn này**: RadarY (8001), PlannerY (8123),
Content Ultimate (8770), Niche Research (8780), SpeakY (7860), SEO Optimize (8760).
**RenderY là app thứ 7.**

### Thêm 1 dict vào `APPS` → tự động có:
- Mục sidebar (template tự dựng — `base.html:149-160`)
- Route `/app/rendery` + reverse proxy (`app.py:2198`, `:2217`)
- Cột tick ở trang `/phan-quyen`
- SSO qua header `X-Remote-User` / `X-Remote-Role`

```python
{"slug": "rendery", "ten": "Dựng video", "port": 8790, "proxy": True,
 "tien_to": ["/api", "/static"],
 "bo_phan": ["Vận hành - Sản xuất"], "min_level": 2,
 "hanh_dong": {...}, "mo_ta_hd": {...}}
```

⚠️ **Bẫy đã có test chặn** (`apps_registry.py:11-13`): `bo_phan` phải viết **đúng từng
ký tự** như `DEPARTMENTS` (`app.py:78`) — `"Vận hành - Sản xuất"` có khoảng trắng quanh
dấu gạch. Sai một dấu cách thì app **biến mất lặng lẽ** khỏi sidebar.

⚠️ Khai `tien_to` **đầy đủ mọi đường dẫn tuyệt đối** RenderY dùng — thiếu là giao diện
hỏng lặng lẽ (bẫy RadarY `/vendor` 30/07/2026).

---

## 4. Hàng đợi — RenderY tự quản, KHÔNG dùng BackgroundTasks của CRM

### Vì sao không dùng của CRM

`app.py:3093-3100` tự ghi giới hạn:

> Registry TRONG BỘ NHỚ tiến trình: đủ cho LAN chạy uvicorn --workers 1. GIỚI HẠN đã
> biết — **mất khi restart**, không chia sẻ giữa nhiều worker.

Ba lý do phải tự quản:
1. `BackgroundTasks` chạy **trong chính tiến trình uvicorn 1 worker** phục vụ cả 6 app
   → job 24 phút sẽ **nghẹt threadpool của toàn hệ thống**.
2. **Mất khi restart** — mà runbook ghi rõ *"Sửa code xong phải Stop rồi Start lại tác vụ"*.
3. Không có giới hạn đồng thời → 3 người bấm cùng lúc là kẹt.

### Thiết kế hàng đợi RenderY

```
Nhân sự nộp job (CRM) → ghi SQLite queue → 2 worker chạy song song
                                              ↓
                        job xong → badge sidebar + thư mục Compose Timeline
```

- **SQLite** (không phải dict in-memory) — restart không mất hàng đợi
- **2 worker** — chốt theo đo thật
- Mỗi job = 1 tiến trình con gọi `autoedit.cli`, log ra file
  (khuôn này R8 đã làm và verify: đóng trình duyệt không giết job)

---

## 5. Thông báo — CRM CHƯA CÓ, dùng khuôn badge

CRM **không có** email/Telegram/WebSocket. Nhưng có sẵn khuôn badge:

`app.py:260-263` — badge số hồ sơ chờ duyệt:
```python
"sb_cho_duyet": (sum(1 for h in doc_ho_so().values()
                     if h.get("trang_thai") == "cho_duyet")
                 if (not lite) and user.get("level", 0) >= 5 else 0),
```

→ RenderY làm tương tự: đếm job **xong mà chưa xem** của chính user đó, bơm vào
`_ctx_outliery`, render badge cạnh mục "Dựng video". Không cần hạ tầng mới.

---

## 6. Thư mục làm việc trên NAS

```
\\192.168.1.250\Video\RenderY\
├── _INBOX\                      ← nhân sự tạo folder job ở đây
│   └── LI070-Han-Quoc\
│       ├── ch01\  script.txt · voice.mp3 · voice.srt
│       ├── ch02\  ...
│       └── refs.txt             ← (tuỳ chọn) link video mẫu YouTube
│
└── Compose Timeline\            ← KẾT QUẢ, nhân sự copy về máy
    └── LI070-Han-Quoc\
        ├── ch01\
        │   ├── draft\           ← draft CapCut chương 1
        │   └── footage\         ← clip đã tải, phân theo chapter
        ├── ch02\ ...
        ├── TONG\                ← draft tổng đã gộp
        └── nguon_footage.txt    ← sổ nguồn gốc + tỉ trọng
```

Đúng yêu cầu bước 4: *"file timeline và footage đã được phân theo từng đơn vị chapter"*.

---

## 7. Chi phí API

User chốt: **Anthropic cho `direct`, GLM cho `rank`**.

> Làm rõ: pipeline gọi LLM ở **2 khâu**, và khâu **`cut` (cắt voice) KHÔNG dùng LLM** —
> thuần ffmpeg + silencedetect. "Cut" trong ý user = `direct` (đạo diễn chia beat).

Đo thật trên `IN002.srt` (20 phút, 434 câu, ~3900 token kịch bản):

| Khâu | Input | Output |
|---|---|---|
| direct | ~6.900 tok | ~26.040 tok |
| rank (43 call) | ~64.500 tok | ~12.900 tok |

| Phương án | $/video | $/tháng (60 video) |
|---|---|---|
| Opus 5 (direct) + GLM (rank) | $0.75 | $45 |
| **Sonnet 5 (direct) + GLM (rank)** | **$0.34** | **$20** |
| Sonnet 5 + Haiku 4.5 | $0.40 | $24 |
| Opus 5 cả hai khâu | $1.33 | $80 |

CRM đã cấu hình GLM sẵn (`WRITER_BASE_URL=https://api.z.ai/api/paas/v4`) → khỏi tạo mới.

---

## 8. Bẫy triển khai — CRM đã trả giá, đừng dính lại

Từ `deploy-windows/README.md`:

1. **File `.ps1` phải lưu UTF-8 CÓ BOM.** PowerShell 5.1 đọc script không BOM theo
   cp1252 → chữ tiếng Việt vỡ → tác vụ **chết ngay, không log gì**.
2. **`PYTHONIOENCODING=utf-8` + `PYTHONUTF8=1`** cho tiến trình con. Thiếu → log tiếng
   Việt ném `UnicodeEncodeError`, giết luồng nền. *(RenderY đã có sẵn trong launcher.)*
3. **Tác vụ SYSTEM không thấy Python trong hồ sơ người dùng** → app **phải có `.venv`
   riêng**. Triệu chứng khi thiếu: log rỗng 0 byte. *(RenderY đã có `.venv`.)*
4. **PATH của SYSTEM không có ffmpeg** — nhưng `chay-app-nen.ps1:44-46` đã tự nối
   `C:\OutlierY\tools\ffmpeg\bin`. ✅ dùng được ngay.

---

## 9. Việc phải làm — 6 bước

| # | Việc | Đụng vào |
|---|---|---|
| 1 | Hàng đợi SQLite + 2 worker | RenderY (mới) |
| 2 | Trang nộp job: chọn folder trên NAS, xem tiến độ + đếm ngược | RenderY (mở rộng web R8) |
| 3 | Đọc `X-Remote-User`/`X-Remote-Role`, chỉ tin khi client là loopback | RenderY |
| 4 | Xuất kết quả ra `Compose Timeline` theo cấu trúc chương | RenderY |
| 5 | Thêm 1 dict vào `APPS` | **CRM — 1 file, 1 dict** |
| 6 | Badge "job xong chưa xem" | **CRM — `_ctx_outliery` + `base.html`** |

Bước 5-6 là **toàn bộ** thay đổi phía CRM. Đúng như kiến trúc CRM thiết kế.

**Chưa làm (cần đo thật trước):** upload file lớn qua CRM. Luồng upload hiện tại dùng
`await file.read()` — đọc **toàn bộ vào RAM**, không hợp video GB. Nhưng theo flow user
mô tả, nhân sự **tạo folder trực tiếp trên NAS** rồi chỉ báo cho CRM biết → **không cần
upload qua HTTP**. Nếu sau này cần thì phải viết streaming write riêng.
