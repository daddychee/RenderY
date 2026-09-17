r"""LỜI KHỐI BỊ CẮT CỨNG 200 KÝ TỰ — user chốt 17/09: "nâng trần để hiển thị
toàn bộ voice".

Lỗi user báo: *"Mất kịch bản hoặc mất bản dịch"*. Một trong hai nguồn mất chữ là
`khoi.py:84` cắt `[:200]`. Ảnh user gửi 13/09 đứt giữa chữ:

    "…and for some people, contribute to a higher r"

Khối dài hơn 200 ký tự thì phần sau biến mất khỏi hợp đồng — và vì `dich` dịch từ
`loi`, bản dịch cũng cụt theo. Không có đường nào lấy lại: `loi` là thứ được LƯU,
không phải thứ vẽ ra lúc hiển thị.

Đo trên 86 chương (17/09): nhiều khối ghi đúng 200 ký tự — dấu vết của trần này.
"""

from __future__ import annotations


def _tu(chu: str, t0: float, buoc: float = 0.25) -> list[dict]:
    """Chuỗi từ giả, mỗi từ `buoc` giây."""
    ra, t = [], t0
    for w in chu.split():
        ra.append({"text": w, "start": round(t, 2), "end": round(t + buoc, 2)})
        t += buoc
    return ra


def test_khoi_dai_GIU_DU_LOI_khong_cat_200():
    from autoedit.offline.khoi import cat_khoi

    dai = " ".join(f"tu{i:03d}" for i in range(120))      # ~720 ký tự
    words = _tu(dai, 0.0)
    het = words[-1]["end"]
    khoi, _dau = cat_khoi([], words, het)
    assert khoi, "không chia được khối nào"
    loi = khoi[0].loi
    assert len(loi) > 200, f"lời khối chỉ {len(loi)} ký tự — vẫn bị cắt"
    assert loi.endswith("tu119"), f"mất đuôi: …{loi[-24:]!r}"


def test_khoi_ngan_khong_doi_gi():
    from autoedit.offline.khoi import cat_khoi

    words = _tu("mot hai ba bon nam", 0.0)
    khoi, _dau = cat_khoi([], words, words[-1]["end"])
    assert khoi[0].loi == "mot hai ba bon nam"


def test_khong_con_tran_cung_trong_ma_nguon():
    """Trần nằm ở nơi GHI vào hợp đồng nên không có đường lấy lại — canh cho nó
    đừng quay lại dưới dạng khác."""
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1] / "autoedit" / "offline" / "khoi.py"
           ).read_text(encoding="utf-8")
    assert "[:200]" not in src, "vẫn còn cắt cứng 200 ký tự"
