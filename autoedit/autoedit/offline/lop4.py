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


# HAI NHÁNH THEO NGÁCH (user chốt 12/09: "prompt sai là sai hết"). Nhánh chọn
# bằng ĐÚNG biến đã có — tập có khai địa danh hay không (QĐ14: chỉ LIFE IN,
# LIVING IN, TRAVEL DOCUMENTARY bắt buộc khai) — KHÔNG đẻ thêm khái niệm.
# A/B thật trên SH010: chương h 41% -> 18% clip du lịch trong khay, chương c1
# 52% -> 28%; từ khoá hai bên tương đương. Nhánh CÓ địa danh giữ nguyên từng
# chữ: ref của Life In đang gánh cả tập.
_MO_DAU_GEO = "Bạn là đạo diễn phim tài liệu du lịch về {DIA_DANH}."
_MO_DAU = "Bạn là đạo diễn phim tài liệu."
_NEO_GEO = "neo=true trừ khi câu nói rõ về nơi khác."
_NEO_KHONG = ("neo=true CHỈ khi câu gắn với một NƠI CHỐN cụ thể; "
              "video không gắn địa lý thì neo=false.")

_SYS = """{MO_DAU} Với MỖI khối lời,
sinh 4 LỚP hình ảnh để tra footage — các TẬP HỢP GIAO NHAU, không phải 1 object:

truc_chi  — 1-2 vật thể/cảnh nói THẲNG trong câu, QUAY ĐƯỢC (phép thử: máy quay
            chĩa vào đâu?). Khái niệm kinh tế (wage/cost) -> quy về vật mang nó
            (cash in hand, grocery basket, price tag).
ngu_canh  — 2-3 cảnh cùng TRƯỜNG NGHĨA, không nói thẳng ("grocery shopping",
            "market vegetable stall").
khong_khi — 2-3 cảnh NỀN thuộc thế giới video, hợp mood — ĐƯỜNG THOÁT khi
            truc_chi/ngu_canh nghèo, luôn phải có.

Mỗi mục 2-4 từ TIẾNG ANH. {LUAT_NEO}
mood: 1 từ (calm/tense/warm/grand/busy...). truu_tuong=true khi câu không có
vật thể nào quay được (cho phép ẩn dụ)."""


def cau_lenh(dia_danh: str = "") -> str:
    """Câu lệnh 4 lớp theo nhóm ngách — địa danh rỗng = ngách không gắn địa lý.

    Vì sao phải tách: câu cũ luôn mở đầu "đạo diễn phim tài liệu DU LỊCH về
    {DIA_DANH}" và địa danh rỗng thì thay bằng "địa danh trong lời", cộng luật
    `neo=true` mặc định -> đo trên SH010: neo bật 26/26 và 19/20 khối, cửa L0
    mở cho mọi clip CÓ nhãn geo (+2 điểm neo) nên kho du lịch tràn vào ngách
    sức khoẻ.
    """
    dd = (dia_danh or "").strip()
    mo_dau = _MO_DAU_GEO.replace("{DIA_DANH}", dd) if dd else _MO_DAU
    return (_SYS.replace("{MO_DAU}", mo_dau)
            .replace("{LUAT_NEO}", _NEO_GEO if dd else _NEO_KHONG))


def gan_lop(khoi_loi: list[str], dia_danh: str = "", llm=None) -> LopOut:
    """[lời từng khối] -> LopOut. `llm` tiêm được (test không mạng)."""
    if llm is None:
        from autoedit.director.glm_client import GLMDirectorClient

        llm = GLMDirectorClient()
    body = "\n".join(f"[{i}] {loi}" for i, loi in enumerate(khoi_loi))
    kq, _ = llm.complete(cau_lenh(dia_danh), body, LopOut)
    # khối LLM bỏ sót -> khối trừu tượng (fail-soft, không giết pha 1)
    co = {o.khoi for o in kq.khoi}
    for i in range(len(khoi_loi)):
        if i not in co:
            kq.khoi.append(LopKhoi(khoi=i, truu_tuong=True))
    kq.khoi.sort(key=lambda o: o.khoi)
    return kq
