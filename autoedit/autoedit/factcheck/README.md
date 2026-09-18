# Factcheck — bàn kịch bản + kiểm chứng nguồn

Một module của RenderY (`autoedit/factcheck/`), chạy **tiến trình riêng ở cổng
9121** để restart nó không cắt UI của người đang dựng ở 9118.

Công cụ biên kịch đứng **trước** dây chuyền dựng video. Team dán kịch bản tiếng
Anh vào, tự chia chương, tự xuống dòng theo mạch dựng, rồi copy bản `.txt` sạch
đem đi ren voice. Mỗi đoạn đáng ngờ bôi đen là kiểm chứng được nguồn.

## Chạy

```
chay.bat              # http://192.168.1.250:9121  (hoặc 127.0.0.1:9121)
test.bat              # 141 test
```

Yêu cầu: Python 3.11+ với `fastapi`, `uvicorn`, `requests`, `pytest`.
Máy chủ OutlierY dùng sẵn venv của RenderY (`F:\RenderY\autoedit\.venv`).

## Ba việc nó làm

| | |
|---|---|
| **Nhập & chia dòng** | Dán kịch bản → mỗi lần xuống dòng là một dòng, dòng trống là ranh đoạn. **Enter** chẻ dòng · **Backspace** đầu dòng gộp lên · **Ctrl+Enter** ranh đoạn · **Ctrl+Z** hoàn tác. Chỗ xuống dòng là chỗ người đọc voice sẽ nghỉ — tức là nhịp của video |
| **Dịch** | Cột tiếng Việt cho team đọc hiểu, chỉ dịch dòng còn thiếu. Bản tiếng Anh mới là kịch bản thật |
| **Kiểm chứng** | Bôi đen một đoạn → tra nguồn → ✅ ĐÚNG (kèm citation) hoặc ❌ SAI/CHƯA KẾT LUẬN (kèm lý do phải làm gì) |

Copy `.txt` **không dính số thứ tự** (số vẽ bằng CSS, không nằm trong văn bản)
và tự dọn rác `""` mà Google Sheet để lại.

## Kiểm chứng hoạt động thế nào

```
LLM sinh truy vấn  →  PYTHON tra (Europe PMC + Serper)
                   →  PYTHON loại mọi tên miền ngoài danh sách uy tín
                   →  PYTHON tải trang
                   →  LLM đọc CHỮ ĐÃ TẢI, chọn trích đoạn làm bằng chứng
                   →  PYTHON soi lại: trích đoạn có THẬT trong trang không
```

**LLM không bao giờ tự đưa URL.** Đó là chỗ nó bịa nhiều nhất: link trông rất
thật, mở ra là 404 hoặc nội dung khác hẳn. Nó chỉ được chọn trong số trang Python
đã tải, và mọi trích dẫn đều bị soi lại.

**Luật cứng:** dấu ✅ chỉ đóng khi có **ít nhất một nguồn hạng 1–2 mà Python đã
kiểm** — link sống + trích đoạn có thật trong trang. LLM nói đúng mà không nguồn
nào kiểm được thì rơi xuống ❌. Không có luật này thì ✅ chỉ là lời LLM tự khen
mình, tệ hơn không có tool vì người viết sẽ thôi tự đọc nguồn.

Nguồn xếp 3 hạng (`factcheck/nguon.py`): hạng 1 bài bình duyệt / cơ quan nhà nước
/ hồ sơ chính thức · hạng 2 báo uy tín · hạng 3 bách khoa, trang phổ thông (chỉ
để tra ngược ra bài gốc, **không** đủ làm bằng chứng). Tên miền lạ bị từ chối —
thà bắt kiểm tay còn hơn đóng dấu ✅ cho một blog.

Mỗi nguồn được dùng làm bằng chứng đều **lưu bản chụp** tại thời điểm kiểm
(`<kho>/bangchung/`), vì link chết sau 6–12 tháng là chuyện thường.

## Cấu hình

Tab **⚙** trong app: địa chỉ · khoá · model kiểm chứng · model dịch.
Thứ tự đọc: **cài đặt trong app → két khoá OutlierY → biến môi trường**.
Bỏ trống ô Khoá là tự dùng khoá của hệ.

Biến môi trường:

| | |
|---|---|
| `KICHBAN_DB` | file SQLite (mặc định `~/.rendery/kichban.db`; máy chủ dùng `F:\AutoEdit\kichban\kichban.db`) |
| `KICHBAN_TRUST_PROXY=1` | chỉ tin `X-Remote-User` khi client là loopback (đặt sau cổng CRM) |
| `SERPER_API_KEY` | tra Google; thiếu thì chỉ còn kênh Europe PMC |

## Danh tính và khoá chương

Chưa nối cổng CRM thì người dùng **tự khai tên** (lưu cookie). Đây **không phải
xác thực** — trong mạng nội bộ ai cũng khai được tên bất kỳ; nó đủ để hai người
biết ai đang giữ chương nào. Nối vào CRM thì header `X-Remote-User` thắng.

Khoá theo **chương**, gác ở **tầng ghi**: người thứ hai mở tab cũ bấm lưu cũng
không phá được việc của người thứ nhất. Mỗi chương giữ **12 bản lùi**.

## Tách tới đâu

Là module của RenderY nhưng **không dính tầng dựng**: chỉ được dùng lại đúng hai
thứ — luật tên chương (`web/chapters.py`) và két khoá (`web/ket_v3.py`). Có test
quét mã canh điều đó (`test_factcheck_app.py::test_khong_dinh_gi_toi_day_chuyen_dung`),
nên sập bên này không kéo theo 9118.

Kho dữ liệu riêng (`kichban.db`), tiến trình riêng, cổng riêng.

## Bẫy đã trả giá — đừng giẫm lại

- **Mọi lượt gọi ra ngoài đi bằng `requests`, không phải `urllib`.** Máy chủ nằm
  sau lớp chặn TLS: urllib chết `CERTIFICATE_VERIFY_FAILED` với mọi trang https.
  Cloudflare của nhà cung cấp LLM cũng chặn User-Agent của urllib (`error 1010`).
- **Nhà xuất bản chặn bot**: `ahajournals.org`, `nhlbi.nih.gov` trả 403. Không đi
  cửa sau — đi cửa chính: Europe PMC theo DOI/PMID trong chính URL đó.
- **Luật nhân quả phải hẹp**: câu chỉ *tường thuật* kết quả nghiên cứu là ĐÚNG,
  chỉ bác khi câu *khẳng định nguyên nhân*. Luật rộng quá thì tool kêu oan gần
  hết bài và team thôi tin nó.
- **Sửa JS phải mở Chrome thật.** Test chuỗi xanh vẫn có thể JS chết: đã dính hai
  lần (mất con trỏ khi bấm dòng; `getElementById` trỏ vào ô đã xoá).
