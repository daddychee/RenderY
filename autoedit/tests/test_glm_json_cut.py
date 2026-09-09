"""GLM trả JSON CỤT: HTTP 200 nhưng nội dung dở — không có thử lại (09/09).

Chương C9 tập LI106 (haint) không tự sinh auto. Đo ra:
  - hợp đồng ghi `GÁN NGHĨA HỎNG (GLM không trả được LopOut hợp lệ:
    Invalid JSON: EOF while parsing)` -> khay **0/29 khối** -> cổng Auto đẩy
    sang Đồng kiểm (cổng chặn ĐÚNG, không phải nó sai);
  - KHÔNG phải do chương dài: C6 có **37 khối** (nhiều hơn C9) mà khay phủ
    37/37;
  - chạy lại Phân tích một lượt là qua: 0/29 -> **29/29**, tự về diện Auto.

Gốc: cơ chế thử lại đặt SAI TẦNG. `_goi()` thử lại khi mạng lỗi/5xx, nhưng
`complete()` đọc JSON **sau** khi `_goi` đã thành công — HTTP 200 với nội dung
cụt thì rơi thẳng xuống `raise`, không thử lại lần nào. Cụt một lần là mất trọn
lớp nghĩa của cả chương và người dựng phải làm tay 29 khối.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel


class _Ra(BaseModel):
    ten: str
    so: int


def _tra(text: str, finish: str = "stop") -> dict:
    return {"choices": [{"message": {"content": text}, "finish_reason": finish}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}}


@pytest.fixture
def glm(monkeypatch):
    from autoedit.director.glm_client import GLMDirectorClient

    monkeypatch.setenv("GLM_API_KEY", "khoa-gia")
    c = GLMDirectorClient()
    monkeypatch.setattr(c, "_log", lambda *a, **k: None)
    return c


def test_json_CUT_duoc_thu_lai(glm, monkeypatch):
    """Lần 1 cụt, lần 2 lành -> phải ra kết quả, không ném lỗi."""
    goi = []

    def gia(messages):
        goi.append(1)
        if len(goi) == 1:
            return _tra('{"ten": "abc", "so": 1', finish="length")   # CỤT
        return _tra('{"ten": "abc", "so": 1}')

    monkeypatch.setattr(glm, "_goi", gia)
    kq, _ = glm.complete("sys", "user", _Ra)
    assert kq.ten == "abc" and kq.so == 1
    assert len(goi) == 2, f"không thử lại: gọi {len(goi)} lần"


def test_cut_MAI_thi_bao_loi_kem_finish_reason(glm, monkeypatch):
    """Hỏng thật thì vẫn phải ném — nhưng nói rõ `finish_reason`, để lần sau
    biết ngay là cụt vì hết hạn mức token hay model trả sai khuôn (BH1)."""
    monkeypatch.setattr(glm, "_goi",
                        lambda m: _tra('{"ten": "abc", "so": 1', finish="length"))
    with pytest.raises(Exception) as e:
        glm.complete("sys", "user", _Ra)
    chi = str(e.value)
    assert "length" in chi, f"lỗi không nói finish_reason: {chi[:160]}"


def test_json_lanh_thi_KHONG_goi_lai(glm, monkeypatch):
    """Thử lại là tốn tiền — chỉ khi cần."""
    goi = []
    monkeypatch.setattr(glm, "_goi",
                        lambda m: (goi.append(1), _tra('{"ten": "x", "so": 2}'))[1])
    kq, _ = glm.complete("sys", "user", _Ra)
    assert kq.so == 2 and len(goi) == 1


def test_rac_giua_danh_sach_van_don_duoc_khong_can_goi_lai(glm, monkeypatch):
    """Đường dọn rác cũ (bug 02/09: phần tử '' giữa list) phải còn nguyên và
    KHÔNG được kéo theo một lượt gọi thừa."""
    class _Ds(BaseModel):
        muc: list[_Ra]

    goi = []
    monkeypatch.setattr(glm, "_goi", lambda m: (goi.append(1), _tra(
        '{"muc": [{"ten": "a", "so": 1}, "", {"ten": "b", "so": 2}]}'))[1])
    kq, _ = glm.complete("sys", "user", _Ds)
    assert [x.ten for x in kq.muc] == ["a", "b"] and len(goi) == 1


def test_noi_dung_RONG_van_bao_nhu_cu(glm, monkeypatch):
    """Trả rỗng là ca khác (đã có nhánh riêng) — không được đổi hành vi."""
    monkeypatch.setattr(glm, "_goi", lambda m: _tra("", finish="content_filter"))
    with pytest.raises(ValueError) as e:
        glm.complete("sys", "user", _Ra)
    assert "RỖNG" in str(e.value) and "content_filter" in str(e.value)
