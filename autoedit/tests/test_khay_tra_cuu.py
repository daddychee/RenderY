r"""VIỆC E — khay tra cứu PA B trong popup double-click.

User chốt 09/09: *"Tôi chọn phương án B. Nhưng nếu có nhiều hơn 21 video 1 lượt
hiển thị thì sẽ chuyển sang trang thứ 2."*

Mockup chốt: `scratchpad/ui_o_tra_cuu.html` (khối `#pa-B`). Số đo lấy TỪ MOCKUP,
không tự đặt:

| Thành phần | Mockup |
|---|---|
| khung xem trên | `flex:0 0 236px` |
| bảng thông tin phải | `flex:0 0 254px` |
| lưới thẻ | `repeat(auto-fill, minmax(150px, 1fr))`, `gap:8px` |
| nút lọc nguồn | `Tất cả N` · Ref · Envato · Pexels · Pixabay (kèm số đếm) |
| lọc nhanh | `⚑ có neo` · `≥ 5s` · `chưa dùng` |
| nhãn thẻ | nguồn · độ dài giây · đã dùng |
| nút Hút | `⛏ Hút thêm (~12s)`, LUÔN HIỆN |

KIỂM TRƯỚC KHI CODE (10/09) — đã đo trên production, KHÔNG phải xây mới:

* `/api/sotra` đã trả đủ `dai_s`, `geo`, `da_dung`, `tap`, `so_ban`, và
  `het` + `offset_tiep` cho phân trang. Không phải đụng server cho phần tra cứu.
* Mã tra cứu ĐÃ VIẾT ở `index.html` (`ofTimDebounce`, nhánh `OF_TIM_KQ`),
  nhưng `#of-tim` **không tồn tại trong HTML** — mọi `getElementById` bọc
  `if (_oti)` nên hỏng ÂM THẦM, nhánh này chưa từng chạy.
* Nút Hút gác bằng `_duoc_nghien_cuu_kenh` (manager/owner) — cửa đó viết cho
  `nap-ref` (tốn LLM thật). Hút tốn **0đ, ~12s**, là việc người dựng cần làm
  ngay lúc gặp khay mỏng → phải có cửa riêng theo LEVEL, đúng khuôn
  `duoc_dang_nhap_nha` (bài học vòng 12).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

INDEX = Path("autoedit/web/static/index.html")
MOCKUP = Path(r"C:\Users\ADMINI~1\AppData\Local\Temp\claude\f--RenderY-v2"
              r"\127aa072-c467-4914-849a-8a3bf884f19e\scratchpad\ui_o_tra_cuu.html")


def _h() -> str:
    return INDEX.read_text(encoding="utf-8")


# ───────────────────────── quyền hút ─────────────────────────

@pytest.fixture
def client(monkeypatch):
    from autoedit.web import server

    monkeypatch.setattr(server, "_trust_proxy", lambda r: True)
    return TestClient(server.app)


def _me(client, level: int, vai: str = "editor") -> dict:
    r = client.get("/api/me", headers={"X-Remote-User": "haint",
                                       "X-Forwarded-Host": "crm.outliery",
                                       "X-Remote-Level": str(level),
                                       "X-Remote-Role": vai})
    assert r.status_code == 200, r.text
    return r.json()


def test_nguoi_dung_level_2_DUOC_hut(client):
    """Hút tốn 0đ / ~12s — người dựng gặp khay mỏng phải tự hút được ngay.

    Cửa cũ `_duoc_nghien_cuu_kenh` (manager/owner) viết cho `nap-ref` vốn tốn
    lượt LLM thật; dùng nhờ cho `hut` là chặn oan (đúng lỗi vòng 12: cửa viết
    cho việc KHÁC).
    """
    assert _me(client, 2)["hut_nguon"] is True


def test_level_1_KHONG_duoc_hut(client):
    assert _me(client, 1, vai="")["hut_nguon"] is False


def test_endpoint_hut_nhan_level_2(client):
    """Cửa trên endpoint phải khớp cửa `/api/me` — lệch nhau là nút hiện mà
    bấm vào ăn 403 (kiểu lỗi vòng 12 nhưng ngược chiều)."""
    r = client.post("/api/sotra/hut", json={"tu_khoa": []},
                    headers={"X-Remote-User": "haint",
                             "X-Forwarded-Host": "crm.outliery",
                             "X-Remote-Level": "2", "X-Remote-Role": "editor"})
    # 422 = qua cửa quyền rồi mới kêu thiếu từ khoá. 403 = vẫn bị chặn.
    assert r.status_code != 403, f"level 2 vẫn bị chặn hút: {r.text[:120]}"


# ───────────────────────── khung PA B ─────────────────────────

def test_o_tim_TON_TAI_trong_html():
    """Gốc rễ việc E: mã tra cứu đã viết xong nhưng `#of-tim` không có trong
    HTML nên nhánh đó chưa từng chạy — hỏng âm thầm suốt."""
    h = _h()
    assert re.search(r'id="of-tim"', h), (
        "thiếu <input id=of-tim> — ofTimDebounce() không bao giờ có gì để đọc")
    assert re.search(r'id="of-tim-nhan"', h), "thiếu ô đếm kết quả #of-tim-nhan"


def test_o_tim_NAM_TRONG_popup_khong_nam_ngoai():
    """User chốt: *"Nó phải nằm trong phần popup mở ra click đúp vào video chứ
    không nằm ở ngoài"*. Đặt nhầm chỗ = đúng lỗi `of-noi-xuat` đã mắc."""
    h = _h()
    i = h.find('id="of-trim-cs"')
    j = h.find('id="man-gen"')          # khối ngay sau popup
    assert 0 < i < j, "không xác định được phạm vi popup"
    assert 'id="of-tim"' in h[i:j], "ô tìm nằm NGOÀI popup double-click"


def test_khung_xem_va_bang_thong_tin_dung_so_do_mockup():
    """Số đo lấy từ mockup đã chốt, không tự đặt lại."""
    h = _h()
    assert re.search(r"#of-trim-cs .tren\s*\{[^}]*flex:\s*0 0 236px", h), \
        "khung xem trên không đúng 236px như mockup"
    assert re.search(r"#of-rv-meta\s*\{[^}]*flex:\s*0 0 254px", h), \
        "bảng thông tin phải không đúng 254px như mockup"


def test_luoi_the_dung_grid_mockup():
    h = _h()
    assert re.search(r"#of-tim-luoi\s*\{[^}]*grid-template-columns:\s*"
                     r"repeat\(auto-fill,\s*minmax\(150px,\s*1fr\)\)", h), \
        "lưới thẻ không đúng minmax(150px,1fr) như mockup"


def test_co_du_4_nut_loc_nguon_va_3_loc_nhanh():
    h = _h()
    for ten in ("Ref", "Envato", "Pexels", "Pixabay"):
        assert ten in h, f"thiếu nút lọc nguồn {ten}"
    for ten in ("⚑ có neo", "≥ 5s", "chưa dùng"):
        assert ten in h, f"thiếu nút lọc nhanh «{ten}»"


def test_nut_hut_LUON_HIEN_khong_an_theo_dieu_kien():
    """Bài học vòng 3: `st-hut-nut` ẩn khi ô trống khiến user tưởng không có
    chức năng. Nút phải luôn thấy; không đủ quyền thì nói rõ, không giấu."""
    h = _h()
    i = h.find('id="of-tim-hut"')
    assert i > 0, "thiếu nút Hút thêm trong popup"
    the = h[i - 200:i + 260]
    assert "hidden" not in the, f"nút Hút bị ẩn theo điều kiện: {the[:160]}"
    assert "~12s" in the, "nút Hút không ghi thời gian chờ (trạng thái nói thật)"


# ───────────────────────── phân trang 21 ─────────────────────────

def test_phan_trang_21_moi_trang():
    """User chốt 09/09: hơn 21 clip thì sang trang 2."""
    h = _h()
    assert re.search(r"OF_TIM_MOI_TRANG\s*=\s*21", h), \
        "thiếu hằng số 21 clip/trang"


def test_dung_offset_cua_API_khong_tu_cat_client():
    """API đã có `offset`/`het`/`offset_tiep` — cắt ở client là tải 200 clip
    rồi vứt 179, và đếm kết quả sẽ sai."""
    h = _h()
    i = h.find("function ofTimGoi")
    assert i > 0, "thiếu hàm gọi tra cứu có phân trang"
    khoi = h[i:i + 900]
    assert "offset=" in khoi, "không truyền offset cho API"
    assert "limit=" in khoi, "không truyền limit cho API"


def test_nhan_the_co_nguon_va_do_dai():
    """Mockup: nhãn thẻ = nguồn · độ dài giây · đã dùng."""
    h = _h()
    i = h.find("function ofTimThe")
    assert i > 0, "thiếu hàm dựng thẻ kết quả"
    khoi = h[i:i + 900]
    assert "dai_s" in khoi, "thẻ không hiện độ dài giây"
    assert "da_dung" in khoi, "thẻ không hiện dấu «đã dùng»"


def test_icon_toi_gian_khong_dung_emoji_nhieu_mau():
    """Nguyên tắc thiết kế đã chốt: ký tự đơn sắc, KHÔNG emoji nhiều màu."""
    h = _h()
    i = h.find('id="of-trim-cs"')
    j = h.find('id="man-gen"')
    trong = h[i:j]
    for xau in ("🔍", "📁", "🎬", "✅", "❌"):
        assert xau not in trong, f"dùng emoji nhiều màu «{xau}» trong popup"


def test_KHONG_con_ma_mo_coi_cua_cot_TUONG_TU():
    """Bỏ cột "Tương tự" mà quên gỡ `ofGoiY` là popup VỠ ngay khi mở:
    `document.getElementById('of-goiy-ds').innerHTML` ném lỗi vì phần tử đã
    bị xoá khỏi HTML.

    Đây đúng loại lỗi chỉ mở trình duyệt mới thấy — test kiểm chuỗi không bắt
    được, vì cả hàm lẫn lời gọi đều còn nguyên trong file.
    """
    h = _h()
    assert 'id="of-goiy-ds"' not in h, "HTML cột Tương tự chưa gỡ hết"
    assert "ofGoiY" not in h, (
        "còn hàm/lời gọi `ofGoiY` trong khi phần tử #of-goiy-ds đã xoá — "
        "mở popup là ném lỗi JS")


def test_bang_thong_tin_duoc_DIEN_khi_mo_popup():
    """Bảng phải (254px) thay chỗ cột Tương tự — phải có hàm điền nội dung,
    không thì nó là ô trống chiếm 254px vô ích."""
    h = _h()
    assert "ofRvMeta" in h, "thiếu hàm điền bảng thông tin bên phải"
    i = h.find("function ofRvMeta")
    khoi = h[i:i + 1400]
    for truong in ("nguon", "dai_s"):
        assert truong in khoi, f"bảng thông tin không hiện «{truong}»"


def test_bang_thong_tin_lay_do_dai_TU_VIDEO_khi_clip_khong_co():
    """NHÌN ẢNH THẬT 10/09 mới thấy: bảng ghi độ dài «—» trong khi tiêu đề
    popup ghi rõ «0.0 – 15.7s (15.7s)». Clip `kho:*` không có cột `dai_s`,
    nhưng thẻ <video> đã đo được độ dài thật.

    Dữ liệu CÓ mà không hiện là bảng vô dụng — đúng thứ chỉ mở trình duyệt
    mới phát hiện (BH13).
    """
    h = _h()
    i = h.find("function ofRvMeta")
    khoi = h[i:i + 1200]
    assert "OF_RV_DAI" in khoi, (
        "bảng thông tin không dùng độ dài đã đo từ video — clip kho/ref sẽ "
        "luôn hiện «—» dù video dài 15.7s")


def test_phan_trang_KHONG_bat_nut_Sau_khi_da_het():
    """Nhìn ảnh thật: ở trang 2 nút «Sau ›» vẫn bật dù chỉ còn 21 kết quả.

    `het` của API dựa trên số bản ghi trả về; phải khoá nút khi trang hiện tại
    trả về ÍT HƠN một trang đầy — nếu không người dựng bấm sang trang rỗng.
    """
    h = _h()
    i = h.find("async function ofTimGoi")
    khoi = h[i:i + 1400]
    assert "OF_TIM_MOI_TRANG" in khoi and "length <" in khoi, (
        "không suy `het` từ số bản ghi thật của trang — nút Sau sẽ bật khi "
        "đã hết clip")
