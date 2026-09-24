"""Bàn kịch bản — trang phục vụ ở `/` phải là trang THẬT, không phải bản mẫu.

Bản mẫu (scratchpad) mang dữ liệu giả nhúng thẳng trong JS để duyệt giao diện.
Nếu bản đó lọt lên máy chủ thì team gõ cả buổi rồi mất trắng khi đóng tab — nên
canh bằng test tĩnh: không còn mảng dữ liệu nhúng, và có gọi API thật.

Hai cơ chế đã đo tận tay ở bản mẫu, canh để không ai vô tình gỡ:
  - SỐ THỨ TỰ vẽ bằng CSS counter (`.en::before`), không nằm trong văn bản của
    trang. Đổi sang <span> là số lại dính vào bản copy đem đi ren voice — đúng
    nỗi khổ trên Google Sheet mà tool này sinh ra để chữa.
  - Dấu ✅❌🕐 đặt `user-select:none` vì cùng lý do.
"""

from __future__ import annotations

from pathlib import Path

import pytest

TRANG = (Path(__file__).resolve().parents[1]
         / "autoedit" / "treatment" / "static" / "treatment.html")


@pytest.fixture(scope="module")
def html() -> str:
    return TRANG.read_text(encoding="utf-8")


def test_khong_con_du_lieu_gia_nhung_trong_trang(html):
    for dau in ("var TAP = [", "var TAP=[", "Mossavar-Rahmani", "thanhdn đang sửa"):
        assert dau not in html, f"trang còn dữ liệu bản mẫu: {dau!r}"


def test_co_goi_api_that(html):
    for duong in ("/api/tap", "fetch("):
        assert duong in html, f"trang chưa gọi API: {duong!r}"


def test_co_giu_va_nha_khoa(html):
    """2-3 người làm cùng lúc: không giữ khoá thì hai người ghi đè nhau."""
    assert "/giu" in html and "/nha" in html


def test_co_tu_luu(html):
    assert "luuNgay" in html or "tuLuu" in html
def test_khong_tro_vao_o_da_xoa(html):
    """Đo 16/09 trên Chrome: console nổ 6 lần `Cannot set properties of null` vì
    `vePhai()` còn trỏ vào #cDoan — ô đó đã bị thay khi dựng thẻ citation thật.
    Test xanh vẫn không thấy: lỗi này chỉ hiện khi mở trình duyệt."""
    import re as _re
    co = set(_re.findall(r'id="([\w-]+)"', html))
    goi = set(_re.findall(r'getElementById\("([\w-]+)"\)', html))
    assert goi <= co, f"trang gọi id không tồn tại: {sorted(goi - co)}"
def test_nhan_hien_thi_la_Treatment(html):
    """User đổi tên tool 23/09: Factcheck -> Treatment. Nhãn trên trang phải đổi
    theo, không để tên cũ sót lại ở chỗ người dùng nhìn thấy."""
    assert "<title>Treatment" in html
    assert "· Treatment" in html
    assert "Factcheck" not in html and "factcheck" not in html


# ------------------- sửa 23/09 theo yêu cầu user ----------------------------
def test_o_nguon_tu_dien_giong_treatment(html):
    """User chốt 23/09: "không cần dùng LLM để tìm Citation nữa, team sẽ tự tìm"
    và "Citation giống cơ chế của treatment, có ô để điền thông tin"."""
    assert "ctOo" in html, "phải có ô nhập nguồn cho từng dòng"
    assert "/kiem" not in html, "bỏ hẳn đường kiểm chứng tự động"
    assert "Kiểm đoạn này" not in html


def test_khong_con_o_khoa_LLM_cho_citation(html):
    """Bỏ phần cài khoá phục vụ tra nguồn tự động."""
    assert "s-serper" not in html and "Serper" not in html


def test_co_gom_cum_va_bang_mau(html):
    """Gom câu thành cụm + tô màu (user chốt 23/09)."""
    assert "gomCum" in html and "boCum" in html
    for m in ("#d9a94c", "#3fae63", "#4c8fe0", "#a274d6", "#e08b4c", "#dd6b9a"):
        assert m in html, m


def test_bam_dong_co_truyen_phim_shift(html):
    """Gom cụm nhiều dòng = bấm dòng đầu, giữ Shift bấm dòng cuối. Đo trên Chrome
    23/09: quên truyền `event.shiftKey` thì Shift vô tác dụng và chỉ tô được MỘT
    dòng — nhìn qua tưởng chạy đúng."""
    assert "event.shiftKey" in html


def test_khong_con_tab_cai_dat_khoa(html):
    """Luật General (user chốt 23/09): khoá do Owner đặt ở General › API Keys,
    app KHÔNG có cửa sửa khoá — kể cả vai cao nhất."""
    for x in ("pane-s", "tb-s", "napCaiDat", "luuCaiDat", "s-key", "/api/cai-dat"):
        assert x not in html, x


def test_trang_bao_che_do_chi_xem(html):
    """Người chỉ xem phải BIẾT ngay, không phải gõ cả buổi rồi mới thấy 403 —
    và các nút ghi phải mờ đi. Cửa gác thật vẫn ở máy chủ."""
    assert "sua_duoc" in html
    assert "chỉ xem" in html.lower()
    assert "SUA_DUOC" in html, "trang phải giữ cờ quyền để tắt các nút ghi"


# ---------------- bố cục: một màn hình, mỗi cột cuộn riêng (23/09) ----------
def test_khung_cao_dung_mot_man_hinh(html):
    """Đo 23/09 trên SE001/C1: bấm dòng 18 thì thanh trên (−1771px), bảng màu
    (−1707px) và panel Treatment (−1663px) đều RA NGOÀI màn hình — làm nửa dưới
    chương là mất sạch công cụ. Vì `body{min-height:100%}` cho trang phình theo
    nội dung nên cả trang cuộn như tờ giấy, không cột nào cuộn riêng.

    Khung phải cao đúng một màn hình để CHỈ cột giữa cuộn.
    """
    goc = html.replace(" ", "").replace("\n", "")
    assert "body{margin:0" in goc and "height:100%;overflow:hidden" in goc, \
        "body phải khoá đúng chiều cao màn hình"
    than = goc[goc.index("<body") if "<body" in goc else 0:]
    assert "body{margin:0" in goc
    assert "min-height:100%;display:flex" not in goc, "min-height làm trang phình theo nội dung"
    _ = than
    assert ".cot{background:var(--bg);overflow:auto" in goc, "mỗi cột tự cuộn"


def test_bang_mau_nam_o_COT_PHAI_canh_treatment(html):
    """User chốt 23/09: bảng màu cụm sang cột phụ bên Treatment, thành một cụm
    công cụ đứng yên — cuộn tới dòng nào cũng với tới được."""
    i_tab = html.index('id="tb-c"')                 # tab Citation — chắc chắn cột phải
    i_cot3 = html.rindex('<div class="cot">', 0, i_tab)   # đầu cột phải
    i_mau = html.index('id="bangMau"')
    assert i_mau > i_cot3, "bảng màu phải nằm TRONG cột phải"
    assert i_mau < i_tab, "và nằm trên khối tab — cụm công cụ đọc từ trên xuống"


# ---------------------- xuống dòng trong ô nhiều dòng ------------------------
# Đo thật 23/09 trong Chrome: gõ 3 dòng vào ô Treatment rồi thoát ra vào lại thì
# thành "Dong motDong haiDong ba" — DÍNH CHỮ, mất cả chỗ xuống dòng.
# Gốc: Enter trong contenteditable đẻ ra <div>, và `textContent` nối text các thẻ
# lại KHÔNG chèn "\n" (đo: textContent -> "Dong motDong haiDong ba",
# innerText -> "Dong mot\nDong hai\nDong ba"). Ba ô nhiều dòng đều đọc sai kiểu
# đó, nên canh cả ba.
_O_NHIEU_DONG = ("tOo", "ctOo", "outline")


def _than_blur(html: str, ma_o: str) -> str:
    """Đoạn JS trong listener blur của ô đó."""
    mo = html.index('getElementById("%s").addEventListener("blur"' % ma_o)
    return html[mo:html.index("});", mo)]


@pytest.mark.parametrize("ma_o", _O_NHIEU_DONG)
def test_o_nhieu_dong_doc_bang_innerText(html, ma_o):
    than = _than_blur(html, ma_o)
    assert "textContent" not in than, (
        f"ô {ma_o} còn đọc bằng textContent — Enter đẻ ra <div> và textContent "
        "nối liền chữ, người gõ xong thoát ra là dính dòng")
    assert "docChu(" in than, f"ô {ma_o} phải đọc qua docChu() để giữ xuống dòng"


def test_co_ham_docChu_giu_xuong_dong(html):
    """Một chỗ duy nhất biết cách đọc chữ nhiều dòng — ba ô dùng chung."""
    assert "function docChu(" in html
    i = html.index("function docChu(")
    than = html[i:i + 700]
    assert "innerText" in than, "docChu phải dùng innerText (textContent mất \n)"


def test_dan_nhieu_dong_vao_mot_dong_thi_CHE_RA(html):
    """Đo Chrome 23/09: dán 3 dòng từ Word vào một dòng kịch bản thì trình duyệt
    nhét <div> vào ô, `textContent` nối liền -> "Alpha oneBravo twoCharlie three"
    ĐI THẲNG vào bản .txt đem ren voice. Đúng thứ tool này sinh ra để chữa.

    Nên trang phải TỰ nhận việc dán: chặn dán mặc định, cắt theo xuống dòng, đẻ
    ra đúng số DÒNG — một dòng là một nhịp, không phải một cục chữ.
    """
    neo = 'getElementById("script").addEventListener("paste"'
    assert neo in html, "cột kịch bản chưa nhận việc dán"
    than = html[html.index(neo):]
    than = than[:than.index("}, false);")]
    assert "preventDefault()" in than, "phải chặn dán mặc định (nó đẻ ra <div>)"
    assert "splice" in than, "dán nhiều dòng phải đẻ ra dòng mới, không dồn một cục"


def test_so_thu_tu_chay_LIEN_tu_H_den_E(html):
    """User chốt 24/09: đánh số câu nối tiếp H -> C1..Cn -> E, KHÔNG đánh lại
    từ 1 mỗi khi sang chương. Số vẽ bằng CSS counter, nên mỗi khối chương phải
    được đặt mốc đếm = tổng số dòng của các chương ĐỨNG TRƯỚC nó.
    """
    goc = html.replace(" ", "").replace(chr(10), "")
    assert "counter-reset:dong" in goc
    assert "counter-reset:dong'+truoc+'" in goc or 'counter-reset:dong"+truoc+"' in goc, \
        "khối chương phải mang mốc đếm riêng, không thì chương nào cũng đếm lại từ 1"


def test_trang_cu_dang_mo_biet_co_ban_moi(html):
    """Đo thật 24/09: bản vá lên máy chủ tối hôm trước, nhưng tab của người dùng
    mở từ trước đó vẫn chạy JS CŨ — 14:39 hôm sau vẫn ghi ra chữ dính. Trang nạp
    JS đúng một lần lúc mở, nên phải tự biết mình đã cũ mà bảo người ta tải lại.
    """
    assert "BAN_TRANG" in html, "trang chưa giữ số hiệu bản mình đang chạy"
    assert "Tải lại" in html, "chưa có lời nhắc tải lại khi máy chủ đã có bản mới"


def test_hoi_lai_dinh_ky_mang_chop_thi_KHONG_ha_quyen(html):
    """Trang hỏi lại `/api/toi` mỗi phút để biết có bản mới. Một lượt hỏng mạng
    KHÔNG được kéo người đang sửa xuống chế độ chỉ xem: nút biến mất giữa lúc gõ
    trong khi quyền chẳng đổi gì."""
    i = html.index("async function aiDay(")
    than = html[i:html.index("async function khaiTen(", i)]
    assert "if(BAN_TRANG) return;" in than, \
        "catch của aiDay phải bỏ qua khi đây là lượt hỏi lại, không hạ quyền"
