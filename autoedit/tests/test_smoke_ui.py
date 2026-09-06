# -*- coding: utf-8 -*-
r"""SMOKE UI — chặn loại lỗi pytest KHÔNG bao giờ thấy (bài học 06/09).

Hai lần trong một ngày, UI chết câm mà 100% test Python vẫn xanh:
  1. toastOf() ghi vào #of-stat đã bị xoá -> TypeError ở MỌI thao tác
  2. tham số `them` đổi tên nhưng thân hàm còn dùng -> lưới Library trắng

Cả hai đều là: JS chạm phần tử/biến KHÔNG TỒN TẠI. Test này quét tĩnh
index.html tìm đúng hai loại đó — không cần trình duyệt, chạy dưới 1 giây.

Nguyên tắc: CHỈ bắt cái chắc chắn nổ. Báo động giả làm test bị bỏ qua, tệ
hơn là không có test.
"""
import re
from pathlib import Path

import pytest

HTML = Path(__file__).resolve().parents[1] / "autoedit" / "web" / "static" / "index.html"

_KEYWORD_JS = {"if", "for", "while", "return", "typeof", "switch", "try",
               "new", "delete", "void", "in", "of", "do", "else"}
_TOAN_CUC = {"window", "document", "location", "history", "localStorage", "console",
             "navigator", "performance", "Math", "JSON", "Date", "Object", "Array",
             "String", "Number", "Boolean", "Promise", "fetch", "setTimeout",
             "clearTimeout", "setInterval", "clearInterval", "requestAnimationFrame",
             "alert", "prompt", "confirm", "URL", "Blob", "FormData", "Set", "Map",
             "Audio", "Image", "Event", "addEventListener", "sessionStorage"}


@pytest.fixture(scope="module")
def trang() -> str:
    return HTML.read_text(encoding="utf-8")


def _than_script(s: str) -> str:
    return s[s.index("<script>") + 8: s.rindex("</script>")]


def test_getElementById_dung_thang_deu_co_phan_tu_that(trang):
    """`getElementById('x').abc` — dùng THẲNG, thiếu phần tử là TypeError.

    Gọi rồi kiểm `if (el)` là hợp lệ, không tính.
    """
    co = set(re.findall(r'id="([\w-]+)"', trang))
    co |= set(re.findall(r"id=[\\]?['\"]([\w-]+)[\\]?['\"]", trang))   # id tạo động
    dung_thang = set(re.findall(
        r"getElementById\(['\"]([\w-]+)['\"]\)\s*[.\[]", trang))
    thieu = sorted(dung_thang - co)
    assert not thieu, f"JS dùng THẲNG phần tử KHÔNG tồn tại: {thieu}"


def test_bien_toan_cuc_cua_app_deu_duoc_khai(trang):
    """Bắt biến OF_*/ST_* dùng mà chưa khai ở đâu (đúng bug `them` 06/09)."""
    js = _than_script(trang)
    khai: set = set()
    for cum in re.findall(r"\b(?:let|const|var)\s+([^;\n]+)", js):
        for phan in cum.split(","):
            m = re.match(r"\s*([A-Za-z_$][\w$]*)", phan)
            if m:
                khai.add(m.group(1))
    khai |= set(re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)", js))
    dung = set(re.findall(r"\b(OF_[A-Z_0-9]+|ST_[A-Z_0-9]+)\b", js))
    thieu = sorted(dung - khai)
    assert not thieu, f"Biến toàn cục dùng mà chưa khai: {thieu}"


def test_ham_duoc_onclick_goi_deu_ton_tai(trang):
    """onclick="ham()" mà không có function ham = nút bấm không làm gì."""
    js = _than_script(trang)
    ham_co = set(re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)", js))
    ham_co |= set(re.findall(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"
                             r"(?:async\s*)?(?:\(|function)", js))
    goi = set(re.findall(r'on(?:click|change|input|mousedown)="\s*'
                         r'([A-Za-z_$][\w$]*)\(', trang))
    thieu = sorted(goi - ham_co - _KEYWORD_JS - _TOAN_CUC)
    assert not thieu, f"Nút gọi hàm KHÔNG tồn tại: {thieu}"


def test_ngoac_can_bang(trang):
    js = _than_script(trang)
    assert js.count("{") == js.count("}"), "lệch ngoặc nhọn"
    assert js.count("(") == js.count(")"), "lệch ngoặc tròn"
