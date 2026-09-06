r"""Dịch lời từng khối sang TIẾNG VIỆT — hiển thị dưới lời gốc trong màn Offline.

User chốt 08/09: panel khối không cần chip từ khóa (đó là dữ liệu máy tra
Library, người duyệt không đọc) — thứ người cần là LỜI GỐC + BẢN DỊCH để biết
đoạn này đang nói gì mà chọn hình cho đúng.

1 lượt GLM/chương (rẻ, ~$0.01), lưu thẳng vào offline.json (khoi[].dich) nên
mở lại không gọi lại. Fail-open: dịch lỗi -> dich rỗng, UI chỉ hiện lời gốc.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CauDich(BaseModel):
    i: int
    vi: str


class BanDich(BaseModel):
    cau: list[CauDich] = Field(default_factory=list)


_SYS = """Dịch từng dòng phụ đề sang TIẾNG VIỆT tự nhiên, giữ đúng ý và giọng
kể của phim tài liệu. Giữ nguyên tên riêng/địa danh và con số. Mỗi dòng dịch
gọn như phụ đề (không thêm giải thích). Trả đúng index `i` của dòng gốc."""

LO = 50          # số dòng mỗi lượt gọi — dài quá LLM hay bỏ sót cuối


def dich_khoi(loi: list[str], llm=None, log=None) -> dict[int, str]:
    """[lời từng khối] -> {index: bản dịch}. Không ném lỗi (fail-open)."""
    def ghi(m):
        if log:
            log(m)

    can = [(i, t.strip()) for i, t in enumerate(loi) if t and t.strip()]
    if not can:
        return {}
    if llm is None:
        try:
            from autoedit.director.glm_client import GLMDirectorClient

            llm = GLMDirectorClient()
        except Exception as exc:  # noqa: BLE001
            ghi(f"offline-dịch: thiếu khoá ({str(exc)[:60]}) — bỏ qua")
            return {}

    ra: dict[int, str] = {}
    for lo in range(0, len(can), LO):
        cum = can[lo:lo + LO]
        body = "\n".join(f"[{n}] {t}" for n, (_i, t) in enumerate(cum))
        try:
            kq, _ = llm.complete(_SYS, body, BanDich)
        except Exception as exc:  # noqa: BLE001 — 1 lô hỏng không giết cả chương
            ghi(f"offline-dịch: lô {lo} lỗi ({str(exc)[:60]})")
            continue
        for c in kq.cau:
            if 0 <= c.i < len(cum) and c.vi.strip():
                ra[cum[c.i][0]] = c.vi.strip()[:300]
    ghi(f"offline-dịch: {len(ra)}/{len(can)} khối có bản dịch")
    return ra
