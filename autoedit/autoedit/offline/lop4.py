r"""Gán NGHĨA 4 LỚP cho từng khối — 1 lượt GLM/chương. Beat LLM KHÔNG đặt ranh
(ranh là của hơi thở người đọc, khoi.py); ở đây chỉ gán nghĩa lên khối có sẵn.

4 lớp tập-giao (user chốt 06/09 — "câu tủ lạnh nhận được cảnh phố xá"):
  L0 chủ thể tập (hằng số video, CỬA bắt buộc khi tra)
  L1 trực chỉ > L2 ngữ cảnh > L3 không khí (đường thoát, luôn phải có)
Phép thử object: "máy quay chĩa vào đâu?" (45%->80% đúng object khi đo 06/09).
Neo địa lý bắt buộc trừ khi câu nói rõ về nơi khác.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LopKhoi(BaseModel):
    khoi: int
    truc_chi: list[str] = Field(default_factory=list)
    ngu_canh: list[str] = Field(default_factory=list)
    khong_khi: list[str] = Field(default_factory=list)
    neo: bool = True
    mood: str = ""
    truu_tuong: bool = False


class LopOut(BaseModel):
    chu_the_tap: list[str] = Field(description="4-6 từ khóa HẰNG SỐ cả video")
    khoi: list[LopKhoi]


_SYS = """Bạn là đạo diễn phim tài liệu du lịch về {DIA_DANH}. Với MỖI khối lời,
sinh 4 LỚP hình ảnh để tra footage — các TẬP HỢP GIAO NHAU, không phải 1 object:

truc_chi  — 1-2 vật thể/cảnh nói THẲNG trong câu, QUAY ĐƯỢC (phép thử: máy quay
            chĩa vào đâu?). Khái niệm kinh tế (wage/cost) -> quy về vật mang nó
            (cash in hand, grocery basket, price tag).
ngu_canh  — 2-3 cảnh cùng TRƯỜNG NGHĨA, không nói thẳng ("grocery shopping",
            "market vegetable stall").
khong_khi — 2-3 cảnh NỀN thuộc thế giới video, hợp mood — ĐƯỜNG THOÁT khi
            truc_chi/ngu_canh nghèo, luôn phải có.

Mỗi mục 2-4 từ TIẾNG ANH. neo=true trừ khi câu nói rõ về nơi khác.
mood: 1 từ (calm/tense/warm/grand/busy...). truu_tuong=true khi câu không có
vật thể nào quay được (cho phép ẩn dụ)."""


def gan_lop(khoi_loi: list[str], dia_danh: str = "", llm=None) -> LopOut:
    """[lời từng khối] -> LopOut. `llm` tiêm được (test không mạng)."""
    if llm is None:
        from autoedit.director.glm_client import GLMDirectorClient

        llm = GLMDirectorClient()
    body = "\n".join(f"[{i}] {loi}" for i, loi in enumerate(khoi_loi))
    kq, _ = llm.complete(_SYS.replace("{DIA_DANH}", dia_danh or "địa danh trong lời"),
                         body, LopOut)
    # khối LLM bỏ sót -> khối trừu tượng (fail-soft, không giết pha 1)
    co = {o.khoi for o in kq.khoi}
    for i in range(len(khoi_loi)):
        if i not in co:
            kq.khoi.append(LopKhoi(khoi=i, truu_tuong=True))
    kq.khoi.sort(key=lambda o: o.khoi)
    return kq
