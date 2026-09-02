"""Mã HTTP nào đáng THỬ LẠI — một chỗ định nghĩa, mọi nơi gọi API dùng chung.

31/08: job LI093 chết ở chương C9 vì Pexels trả **504 Gateway Timeout** mà danh sách
retry chỉ liệt kê (500, 502, 503). 504 rơi xuống `raise_for_status()` -> vỡ cả job
sau 3 chương đã dựng xong. Cùng lúc đó vision.py và visiongate.py cũng thiếu 504 y
hệt — ba bản sao chép tay của cùng một danh sách, sót cùng một mã.

Nguyên tắc: đây đều là lỗi TẠM THỜI phía server hoặc hạ tầng mạng, khác hẳn 4xx
(yêu cầu sai — thử lại cũng vậy). Thiếu một mã trong danh sách nghĩa là một sự cố
mạng thoáng qua giết nguyên một job dài.

    408 Request Timeout      520 Cloudflare: unknown error
    429 Too Many Requests    521 Cloudflare: origin down
    500 Internal Error       522 Cloudflare: connection timeout
    502 Bad Gateway          523 Cloudflare: origin unreachable
    503 Unavailable          524 Cloudflare: origin timeout
    504 Gateway Timeout      529 (Anthropic/GLM) overloaded
"""

from __future__ import annotations

# Lỗi tạm phía server/hạ tầng — CHỜ rồi thử lại.
MA_THU_LAI = frozenset({408, 425, 429, 500, 502, 503, 504, 507, 509,
                        520, 521, 522, 523, 524, 529})

# 429 = hết hạn mức: có nhiều khoá thì XOAY KHOÁ hiệu quả hơn là ngồi chờ.
MA_HET_HAN_MUC = frozenset({429})


def nen_thu_lai(ma: int) -> bool:
    """True nếu mã HTTP này là lỗi TẠM — chờ rồi gọi lại thì có cơ hội thành công."""
    return ma in MA_THU_LAI
