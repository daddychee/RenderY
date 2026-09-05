r"""MÔ TẢ PHONG CÁCH — bản đọc được do LLM viết TỪ SỐ ĐO (Framing Insight).

Khuôn Author Extract "Mô tả giọng + hướng dẫn dùng" (user chỉ đích 05/09, kèm
ảnh UI): sau khi Python đo xong, MỘT lượt LLM viết bản nhận diện phong cách
cho người đọc — 3 khối NHẬN RA / GIAO VIỆC / DỰNG THEO, mỗi ý phải bám số đo.

Luật sắt (chép từ AE): model CHỈ được đọc số đo Python đã đo — không được bịa
kiến thức riêng về kênh, không suy đoán nội dung video. Footer UI ghi rõ điều
này cho người dùng biết mà soi lại.

Đây là tầng HIỂN THỊ cho người — KHÔNG nhét vào prompt director chia beat
(user chốt 05/09: việc đó để sau khi test ổn).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MoTaPhongCach(BaseModel):
    """Schema bản mô tả — khối UI khớp AE, 4 mặt phân tích user chốt 05/09:
    'đường hình, âm nhạc, nhịp độ, năng lượng — cứ làm thô trước'."""

    # ---- NHẬN RA PHONG CÁCH ----
    la_gi: str                                    # 1-2 câu: phong cách này là gì
    ky_thuat: list[str] = Field(default_factory=list)   # 3-5 kỹ thuật đặc trưng, kèm số
    # ---- PHÂN TÍCH CÁCH DỰNG (4 mặt) ----
    nhip_do: str = ""                             # hook/thân/bùng cắt thế nào
    duong_hinh: str = ""                          # phối loại cảnh: tự quay/b-roll/đồ hoạ/AI
    am_nhac: str = ""                             # nhạc kiểu gì, cao trào đặt đâu
    nang_luong: str = ""                          # năng lượng tổng thể lên xuống ra sao
    # ---- GIAO VIỆC ----
    hop_voi: str = ""                             # dùng cho nội dung gì
    khong_hop: str = ""                           # không hợp với gì (kèm số vì sao)
    mood: str = ""                                # mood cần set
    # ---- DỰNG THEO ----
    chi_lenh: list[str] = Field(default_factory=list)   # 3 chỉ lệnh khi dựng


_SYSTEM = """Bạn là đạo diễn dựng phim documentary/faceless kỳ cựu. Dưới đây là
SỐ ĐO máy đo được từ các video của một kênh YouTube mẫu (nhịp cắt, nhạc, tỷ
trọng loại cảnh). Viết bản NHẬN DIỆN PHONG CÁCH DỰNG bằng tiếng Việt cho editor
đọc, theo đúng schema. Bốn mặt phải phân tích: NHỊP ĐỘ (cắt), ĐƯỜNG HÌNH
(phối loại cảnh), ÂM NHẠC, NĂNG LƯỢNG (tổng thể lên xuống).

LUẬT SẮT: chỉ được suy từ SỐ ĐO cho sẵn — KHÔNG dùng hiểu biết riêng về kênh,
KHÔNG đoán nội dung video. Mỗi kỹ thuật/nhận định phải dẫn kèm con số làm bằng
chứng (vd "hook cắt trung vị 0.7s — dày gấp 3 thân"). Số 0 hoặc thiếu nghĩa là
KHÔNG ĐO ĐƯỢC — bỏ qua, đừng bịa.

Chú giải số đo: hook = 90 giây đầu; than = phần còn lại; trung_vi tính bằng
giây/shot; ty_le_nhanh = tỉ lệ shot ≤2s; ty_le_hold = tỉ lệ shot ≥5s;
bung_chu_ky_s = chu kỳ (giây) giữa các đợt dồn cắt; nhac_vi_tri_drop = cao trào
nhạc nằm ở đâu trong bài (0..1); nhac_do_dong = dải động dB (to = nhạc sóng,
nhỏ = nhạc phẳng); loai_canh = tỷ trọng thời lượng (tu_quay/b_roll/do_hoa/
ai_render). hook_kieu: no = nổ dày ngay giây đầu, leo = dồn dần, em = giữ đều.

chi_lenh: đúng 3 chỉ lệnh máy-làm-được (số cụ thể), như "Giữ trung vị thân
quanh 2.1s, tối đa 50% shot vượt 2s"."""


def sinh_mo_ta(hs, llm=None) -> dict:
    """HoSoKenh -> dict MoTaPhongCach. Ném lỗi khi LLM chết — caller fail-open."""
    import json
    from dataclasses import asdict

    if llm is None:
        from autoedit.director.glm_client import GLMDirectorClient

        llm = GLMDirectorClient()
    so_do = {k: v for k, v in asdict(hs).items()
             if k not in ("mo_ta", "nguon", "link") and v not in ("", [], {}, None)}
    kq, _ = llm.complete(_SYSTEM, json.dumps(so_do, ensure_ascii=False),
                         MoTaPhongCach)
    return kq.model_dump()
