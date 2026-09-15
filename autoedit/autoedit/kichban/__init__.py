"""Bàn kịch bản — công cụ biên kịch đứng TRƯỚC dây chuyền dựng.

Giai đoạn 1 (user chốt 15/09/2026) KHÔNG nối vào đâu cả: team dán kịch bản tiếng
Anh vào, tự chia chương, tự xuống dòng theo mạch dựng, rồi copy bản .txt sạch đem
đi ren voice. Không đọc NAS, không đụng `jobs.db`, không import `autoedit.web` —
chạy tiến trình riêng, cổng riêng, để sự cố ở đây không chạm dây chuyền dựng
đang chạy production.

Vì sao nằm trong package `autoedit`: `test.bat` quét cả suite một lượt, và QĐ4
(SEQUENCE.md) hoãn việc đổi tên package. Cách ly nằm ở chỗ KHÔNG import lẫn nhau,
không phải ở chỗ để thư mục.
"""
