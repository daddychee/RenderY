r"""SINH ĐỀ XUẤT hồ sơ ngách từ pool Radary (QĐ18, user chốt 18/09/2026).

**LUẬT CỨNG 4 — Python đo, LLM hiểu/sinh, không đảo vai.** Cụ thể ở đây:

* **Python quyết** ngách có lọc theo người không, bằng tỉ lệ tiêu đề nhắc tới
  người. Đo thật trên pool 18/09 (600 tiêu đề mỗi ngách):

      X FILE 16.3% · COOKING 8.5% · STORM 11.2% · SPACE 19.8%
      LIFE IN 29.3%  ||  RETIREMENT 50.0% · SENIOR HEALTH 60.3%

  Ngưỡng 40% nằm giữa khoảng trống thật giữa 29.3% và 50.0%.
* **LLM chỉ sinh TỪ VỰNG** — quay cái gì. Nó không lật được cờ `loc_nguoi`.

**Giá trị nhân vật là BỘ ĐÓNG.** Kho chỉ biết `tuoi` ∈ {none, older, young,
mixed, middle, child} và `chung_toc` ∈ {none, white, unclear, asian, black,
mixed, latino} (đo 18/09). LLM trả "elderly" nghe rất hợp lý mà lọc ra đúng 0
clip — nên lọc lại bằng code, dặn trong prompt không đủ.

Máy chỉ ĐỀ XUẤT. Lưu là việc của `ngach_ho_so.luu()` sau khi người bấm Duyệt.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from autoedit.ngach_ho_so import _sach_tu

# Ngưỡng tách ngách-người khỏi ngách-đồ-vật. Xem bảng số đo ở docstring.
NGUONG_LOC_NGUOI = 0.40
TRAN_VAT_THE = 24

# Dấu hiệu "tiêu đề này nói về người". Cố ý rộng: đếm để ƯỚC LƯỢNG tỉ lệ, sai
# lệch vài phần trăm không đổi kết luận khi khe hở giữa hai nhóm là 20 điểm.
TU_NGUOI = frozenset((
    "man", "men", "woman", "women", "people", "person", "guy", "girl", "boy",
    "kid", "kids", "child", "children", "family", "families", "grandma",
    "grandpa", "grandmother", "grandfather", "senior", "seniors", "elderly",
    "retiree", "retirees", "couple", "mom", "dad", "mother", "father",
    "wife", "husband", "he", "she", "his", "her", "they", "you", "your",
    "i", "we", "my", "worker", "workers", "farmer", "doctor", "nurse",
    "teacher", "villager", "villagers", "american", "americans"))

# Bộ đóng — đo từ chính kho 18/09.
TUOI_HOP_LE = frozenset(("none", "older", "young", "mixed", "middle", "child"))
CHUNG_TOC_HOP_LE = frozenset(
    ("none", "white", "unclear", "asian", "black", "mixed", "latino"))

_SYSTEM = """Bạn đọc TIÊU ĐỀ video của một ngách YouTube và rút ra ngách đó QUAY CÁI GÌ.

Trả `vat_the`: 12-24 cụm từ khoá TIẾNG ANH để tra kho footage stock.
- Mỗi cụm 1-3 từ, là VẬT THỂ hoặc CẢNH QUAY CỤ THỂ nhìn thấy được
  (đúng: "duct tape", "forklift", "factory line" — sai: "history", "science",
  "curiosity", "explained").
- Không lặp lại tên ngách. Không từ kỹ thuật dựng (slow motion, overlay, b-roll).

Chỉ khi được bảo ngách này LỌC THEO NGƯỜI thì mới trả thêm:
- `tuoi`: chọn trong none, older, young, mixed, middle, child
- `chung_toc`: chọn trong none, white, unclear, asian, black, mixed, latino
Không được chế giá trị khác — kho chỉ biết đúng các chữ trên."""


class DeXuat(BaseModel):
    vat_the: list[str] = Field(default_factory=list)
    tuoi: list[str] = Field(default_factory=list)
    chung_toc: list[str] = Field(default_factory=list)
    ghi_chu: str = ""


def do_nguoi(tieu_de: list[str]) -> dict:
    """Bao nhiêu tiêu đề nhắc tới người — SỐ ĐO, không phải ý kiến của LLM."""
    td = [str(t) for t in (tieu_de or []) if str(t).strip()]
    n = sum(1 for t in td
            if TU_NGUOI & set(re.findall(r"[a-z']+", t.lower())))
    return {"co_nguoi": n, "tong": len(td),
            "ty_le": round(n / len(td), 4) if td else 0.0}


def nen_loc_nguoi(ty_le: float) -> bool:
    return float(ty_le) >= NGUONG_LOC_NGUOI


def _llm():
    from autoedit.director.glm_client import GLMDirectorClient

    return GLMDirectorClient()


def de_xuat(ten: str, tieu_de: list[str], llm=None) -> dict:
    """Pool -> ĐỀ XUẤT hồ sơ. KHÔNG lưu — người bấm Duyệt mới lưu."""
    td = [str(t).strip() for t in (tieu_de or []) if str(t).strip()]
    if not td:
        raise ValueError(f"Ngách «{ten}» chưa có pool trong Radary — "
                         "không có tiêu đề nào để đọc")
    do = do_nguoi(td)
    loc = nen_loc_nguoi(do["ty_le"])
    if llm is None:
        llm = _llm()
    loi = (f"NGÁCH: {ten}\n"
           f"NGÁCH NÀY {'LỌC THEO NGƯỜI' if loc else 'KHÔNG lọc theo người'} "
           f"(đo: {do['co_nguoi']}/{do['tong']} tiêu đề nhắc tới người).\n\n"
           "TIÊU ĐỀ VIDEO CỦA NGÁCH:\n" + "\n".join(f"- {t}" for t in td))
    kq, _ = llm.complete(_SYSTEM, loi, DeXuat)

    nhan_vat: dict[str, list[str]] = {}
    if loc:
        for truong, bo in (("tuoi", TUOI_HOP_LE),
                           ("chung_toc", CHUNG_TOC_HOP_LE)):
            gia = [x for x in _sach_tu(getattr(kq, truong, [])) if x in bo]
            if gia:
                nhan_vat[truong] = gia
    return {"loc_nguoi": loc, "nhan_vat": nhan_vat,
            "vat_the": _sach_tu(kq.vat_the)[:TRAN_VAT_THE],
            "do_nguoi": do, "ghi_chu": (kq.ghi_chu or "").strip()}
