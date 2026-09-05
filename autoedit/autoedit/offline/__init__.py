"""OFFLINE — bản dựng nháp duyệt đường dây (user đặt tên 07/09, như offline
edit trong nghề dựng: chốt cấu trúc + hình trên bản nhẹ trước khi online).

Đợt 2 flow Đường Dây. Hai pha:
  PHA 1 chốt KHỐI — ranh cắt theo hơi thở người đọc (giao 2 bằng chứng:
         silence đo audio + mốc từ transcript; nghiệm thu RMS 06/09), khoảng
         thở là khối trắng riêng, +1s/−1s là thao tác ÂM THANH thật.
  PHA 2 đổ VIDEO — ứng viên 4 lớp từ Library, khay 4 khu (★Envato ★Ref ưu
         tiên), luật 60s + chốt neo 30s + cấm 3 khối L3 liền.

Hợp đồng: `offline.json` trong project dir — màn Offline (đợt 4) đọc-ghi,
thay máu (đợt 5) thi hành. Voice là mốc bất biến; chỉ im lặng được chèn/thu.
"""
