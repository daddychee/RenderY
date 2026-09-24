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
    """Tên tool: Factcheck -> Treatment (23/09) -> AI Generation -> TREATMENT
    (user trả lại 24/09: "Treatment và AI generation là 2 app riêng... yêu cầu
    anh trả lại tên cũ là treatment"). Gộp một app thì tên là Treatment."""
    assert "<title>Treatment" in html
    assert "· Treatment" in html
    assert "AI Generation" not in html
    assert "Factcheck" not in html and "factcheck" not in html


def test_tab_TREATMENT_o_cot_phai_GIU_NGUYEN_ten(html):
    """Đổi tên TOOL, không đổi tên CỘT. "Treatment" ở cột phải là tên một trong
    bốn cột UI gốc của user (Outline | English Script | Vietnamese | Treatment)
    — đổi nó là đội mất chỗ bám."""
    i = html.index('id="tb-t"')
    assert "Treatment" in html[i:i + 120]


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
# `tOo` đã thành KHỐI (24/09) nên không còn là một ô nhiều dòng;
# luật đọc-bằng-innerText của nó chuyển sang test_khoi_doc_bang_docChu.
_O_NHIEU_DONG = ("ctOo", "outline")


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


# ═══════════════ Treatment thành KHỐI — mỗi khối một cảnh (24/09) ════════════
# User chốt: *"ở khối treatment, sau mỗi lần enter thì sẽ tạo ra 1 khối dòng mới
# để nhập tiếp. Một phân cảnh có 6 cảnh treatment là 6 dòng riêng biệt"*.
# Và: *"đánh số cảnh dựa trên phân cảnh, ví dụ phân cảnh 4 sẽ có các cảnh
# 4.1 4.2"*.

def test_o_treatment_mot_cuc_da_thanh_KHOI(html):
    assert 'id="tOo"' not in html, "ô treatment một cục phải bỏ"
    assert 'id="tKhoi"' in html, "phải có chỗ chứa các khối cảnh"


def test_moi_khoi_la_mot_canh_va_co_ham_ve(html):
    assert "function veKhoi(" in html, "chưa có hàm vẽ các khối cảnh"
    assert "function docCanh(" in html, \
        "trang phải đọc được CẢ dữ liệu cũ (tr chuỗi) lẫn mới (canh)"


def test_ma_canh_danh_theo_PHAN_CANH(html):
    """Phân cảnh 4 -> cảnh 4.1, 4.2. Số phân cảnh là số câu chạy liền H→E, nên
    phải lấy qua `dongTruoc` chứ không phải chỉ số trong chương."""
    i = html.index("function veKhoi(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "soPhanCanh()" in than, "mã cảnh phải neo vào số phân cảnh"
    assert '"."' in than or "'.'" in than, "mã cảnh phải là <phân cảnh>.<thứ tự>"
    j = html.index("function soPhanCanh(")
    assert "dongTruoc(" in html[j:html.index(chr(10) + "}", j)],         "số phân cảnh phải chạy liền cả tập, không đếm lại mỗi chương"


def test_enter_trong_khoi_de_ra_khoi_moi(html):
    """Enter chẻ khối tại con trỏ; Backspace ở đầu khối gộp lên khối trên —
    cùng cơ chế với cột kịch bản đã chạy, người dùng không phải học cái mới."""
    i = html.index('getElementById("tKhoi").addEventListener("keydown"')
    than = html[i:html.index("}, false);", i)]
    assert '"Enter"' in than, "chưa bắt phím Enter trong khối"
    assert '"Backspace"' in than, "chưa bắt Backspace đầu khối"
    assert "preventDefault()" in than, "phải chặn hành vi mặc định của trình duyệt"
    assert "function cheKhoi(" in html and "function gopKhoi(" in html


def test_khoi_doc_bang_docChu(html):
    """Luật cũ vẫn đứng: đọc chữ trong ô contenteditable bằng innerText, không
    phải textContent — dán nhiều dòng vào một khối thì chữ không được dính."""
    i = html.index("function docKhoi(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "docChu(" in than and "textContent" not in than


def test_gui_len_may_chu_bang_khoa_canh(html):
    """Ghi kiểu mới (`canh`), không ghi lại `tr` — nếu không thì mỗi lần lưu là
    một lần tụt về mô hình cũ."""
    assert ".canh =" in html or '["canh"]' in html, "trang phải ghi khoá `canh`"
    assert "d.tr =" not in html, "không được ghi lại `tr` kiểu cũ nữa"


def test_nut_them_canh_chi_hien_khi_sua_duoc(html):
    assert "themCanh" in html, "phải có nút thêm cảnh"
    assert "SUA_DUOC" in html


def test_che_khoi_ve_lai_bang_DANH_SACH_VUA_DUNG(html):
    """Đo Chrome 24/09: Enter ở cuối khối không đẻ ra khối mới. Khối mới rỗng,
    mà `luuCanh` lọc bỏ cảnh rỗng (đúng — kho không nên chứa cảnh trống), nên
    khi `veKhoi` đọc LẠI từ kho thì khối vừa đẻ đã biến mất; con trỏ rơi về khối
    cũ và chữ gõ tiếp dính vào đó.

    Nên chỗ đang gõ phải vẽ bằng danh sách VỪA DỰNG, không phải bản đã lọc.
    """
    for ten in ("cheKhoi", "themCanh"):
        i = html.index("function %s(" % ten)
        than = html[i:html.index(chr(10) + "}", i)]
        assert "veKhoi(dongDangChon(), ds)" in than, (
            f"{ten} phải vẽ lại bằng danh sách vừa dựng — vẽ từ kho thì khối "
            "rỗng đang gõ dở biến mất")


def test_tro_khoi_vao_o_RONG_van_dat_duoc_con_tro(html):
    """Khối vừa đẻ chưa có text node nào. Không tạo thì `setStart` ném lỗi và
    con trỏ ở lại chỗ cũ — cùng cái bẫy `datCaret` đã xử."""
    i = html.index("function troKhoi(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "createTextNode" in than


# ═════════════ màn STORYBOARD — bảng thẻ (user duyệt UI 24/09) ═══════════════
# User chốt: *"chỉ cần bảng thẻ. click vào trong sẽ hiện ra prompt. đánh số cảnh
# dựa trên phân cảnh, ví dụ phân cảnh 4 sẽ có các cảnh 4.1 4.2"*.
# Bảng biểu là thứ đội đang chạy trốn khỏi Google Sheet, nên storyboard phải là
# TẤM BẢNG THẺ — và cái thẻ chính là vật chứa ảnh ở đợt 2.

def test_co_man_storyboard_rieng(html):
    assert 'id="manSb"' in html, "phải có màn storyboard"
    assert 'id="manKb"' in html, "màn kịch bản phải tách ra để đổi qua lại"
    assert "function doiMan(" in html


def test_the_canh_mang_ma_phan_canh(html):
    """Thẻ ghi 4.1, 4.2 — không phải S41."""
    i = html.index("function veTheCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "x.ma" in than, "thẻ phải in mã cảnh"
    j = html.index("function dungCanhTap(")
    assert '"." +' in html[j:html.index(chr(10) + "}", j)], \
        "mã cảnh phải là <phân cảnh>.<thứ tự trong phân cảnh>"


def test_bam_the_thi_bung_hop_prompt(html):
    assert 'id="hopCanh"' in html, "phải có hộp bung ra khi bấm thẻ"
    assert "function moCanh(" in html and "function dongCanh(" in html
    assert "Escape" in html, "Esc phải đóng hộp"
    assert "ArrowLeft" in html and "ArrowRight" in html, \
        "phím mũi tên đi giữa các cảnh — không phải đóng mở từng thẻ"


def test_prompt_ghep_boilerplate_THEO_TONG(html):
    """Hai đoạn boilerplate của user: cảnh dưới nước có thêm câu về ánh sáng tự
    nhiên dưới nước, cảnh trên cạn thì không."""
    assert "function promptAnh(" in html and "function promptVideo(" in html
    # Hai đoạn tông nay sống ở SỔ của tập (máy chủ đưa mặc định) — nội dung của
    # chúng canh ở test_treatment_so.py. Ở trang chỉ canh chỗ GHÉP.
    for ten in ("promptAnh", "promptVideo"):
        i = html.index("function %s(" % ten)
        than = html[i:html.index(chr(10) + "}", i)]
        assert "boiler(x.tong)" in than, f"{ten} phải ghép tông của CHÍNH cảnh đó"
    assert "No background music" in html, "prompt video phải cấm nhạc nền"
    assert "16:9" in html


def test_doi_tong_ghi_vao_CHINH_CANH(html):
    """Tông là thuộc tính của CẢNH (`canh[i].tong`), không phải biến rời — chẻ
    gộp cảnh thì nó phải đi theo, cùng bài học của `cum`."""
    i = html.index("function datTong(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert ".tong =" in than
    assert "ghiCanhVao(" in than, "đổi tông phải đi qua đường ghi cảnh"
    j = html.index("function ghiCanhVao(")
    assert "henLuu(" in html[j:html.index(chr(10) + "}", j)],         "đường ghi cảnh phải hẹn lưu — một đường ghi duy nhất cho cả hai màn"


def test_storyboard_ton_trong_quyen_chi_xem(html):
    """L2 mở được storyboard để đọc, nhưng không đổi được gì."""
    i = html.index("function moCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "SUA_DUOC" in than, "hộp cảnh phải đọc cờ quyền"


def test_vet_ca_tap_de_soat_tong(html):
    """Vệt cả tập: mỗi cảnh một ô, bấm là nhảy tới — chỗ soát mood/tone mà bảng
    98 dòng không làm được."""
    assert 'id="vetTap"' in html
    assert "function veVetTap(" in html


def test_canh_bao_voice_dai_hon_mot_clip(html):
    """Tool biết voice dài bao nhiêu (2,6 từ/giây) — Gemini thì không. Phân cảnh
    38 giây chia 5 cảnh là 7,6s/cảnh, dài hơn một clip i2v 5 giây."""
    assert "GIAY_CLIP" in html, "phải có hằng số độ dài một clip"
    i = html.index("GIAY_CLIP")
    assert "5" in html[i:i + 40]


def test_doi_man_phai_dat_display_chu_khong_phai_hidden(html):
    """Đo Chrome 24/09: bấm Storyboard mà màn Kịch bản vẫn nằm nguyên phía trên.
    Cả hai màn đều có display:flex (một cái inline, một cái trong CSS) nên thuộc
    tính  bị display đè — quy tắc [hidden]{display:none} thua."""
    i = html.index("async function doiMan(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "style.display" in than, "đổi màn phải đặt thẳng style.display"
    assert ".hidden =" not in than, "hidden bị display:flex đè, không ẩn được màn"


# ═══════════ việc 3: sổ tài sản · hồ sơ tông · phân nhân sự ══════════════════
def test_co_nut_mo_so_tai_san_va_tong(html):
    assert 'id="nutTaiSan"' in html and 'id="nutTong"' in html
    assert "function moSo(" in html


def test_boiler_doc_tu_SO_khong_ghi_cung_trong_trang(html):
    """Owner sửa tông trong sổ của tập thì mọi prompt phải ăn theo. Ghi cứng
    đoạn boilerplate trong trang nghĩa là đổi mood phải sửa code."""
    i = html.index("function boiler(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "soTheoMa(" in than, "boiler phải tra trong sổ của tập"
    assert "TONG_MAC_DINH" not in html, "boilerplate không được ghi cứng trong trang — nó sống ở sổ"


def test_prompt_dinh_MO_TA_TAI_SAN_cua_canh(html):
    """Đây là thứ thay hẳn bước 6 của user (ném ref vào Gemini rồi bảo nó ghi
    nhớ): API không có trí nhớ giữa các lượt, nên mô tả phải đi kèm mỗi prompt."""
    i = html.index("function promptAnh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "moTaTaiSan(" in than
    j = html.index("function moTaTaiSan(")
    assert "x.ts" in html[j:html.index(chr(10) + "}", j)]


def test_loc_theo_nhan_su_va_hien_ten_nguoi(html):
    """Cụm màu = phân nhân sự (user chốt 24/09)."""
    assert 'id="locNhanSu"' in html, "phải có bộ lọc nhân sự"
    assert "function tenNhanSu(" in html, "chấm màu phải kèm tên người"


def test_hop_canh_co_hang_gan_tai_san(html):
    i = html.index("function moCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "taiSanCuaCanh(" in than or "veTaiSanCanh(" in than


def test_dungCanhTap_mang_theo_TS(html):
    """Đo Chrome 24/09: gán tài sản vào cảnh thì `ts` xuống kho đúng, nhưng
    prompt KHÔNG đổi — vì `dungCanhTap()` dựng object cho màn storyboard mà quên
    chép `ts` sang, nên `moTaTaiSan` nhận undefined. Sổ thành quyển vở vô dụng."""
    i = html.index("function dungCanhTap(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "ts:" in than, "dungCanhTap phải chép `ts` sang, không thì prompt mất tài sản"


def test_luu_so_xong_thi_ve_lai_BO_LOC_nhan_su(html):
    """Đặt tên người cho cụm xong mà bộ lọc vẫn trống là không ai lọc được."""
    i = html.index("async function chotSo(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "veLocNhanSu()" in than


# ═══════════ ảnh ref của tài sản (user chốt 24/09: "tôi sẽ upload ref") ══════
def test_so_tai_san_co_cho_TAI_REF_LEN(html):
    assert 'type="file"' in html, "phải có ô chọn file ref"
    assert "function taiRef(" in html and "function xoaRef(" in html


def test_tai_san_co_HAI_o_chu_tach_bach(html):
    """`pr` = prompt TẠO ref (dùng một lần) · `chu` = mô tả nhận dạng (đính vào
    mọi prompt cảnh). Gộp làm một là dán nhầm cả đoạn 3-góc-nền-trắng vào từng
    cảnh."""
    assert 'data-pr="' in html, "phải có ô prompt tạo ref riêng"
    assert 'data-chu="' in html, "và ô mô tả riêng"
    i = html.index("function moTaTaiSan(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert ".chu" in than and ".pr" not in than,         "prompt cảnh chỉ đính MÔ TẢ, không đính prompt tạo ref"


def test_co_thanh_tien_do_cua_so(html):
    """Bước lập sổ phải có vạch đích, không thì người ta quên mình đang dở."""
    assert "function tienDoSo(" in html
    i = html.index("function tienDoSo(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "ref" in than, "phải đếm tài sản chưa có ref"


def test_hop_canh_hien_anh_ref_cua_tai_san_da_gan(html):
    """Đính ref vào lượt gen là việc tay ở đợt 1 — tool ít nhất phải chỉ rõ
    ẢNH NÀO, không bắt người ta nhớ."""
    i = html.index("function veTaiSanCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "duongRef(" in than, "hàng tài sản trong hộp cảnh phải hiện ảnh ref"
    assert "<img" in than, "hiện thật cái ảnh, không phải chỉ cái tên"


def test_so_co_nut_goi_ten_du_tai_san(html):
    """User chốt 24/09: "ông call đủ các asset, tôi sẽ upload ref"."""
    assert "function goiYTaiSan(" in html
    assert 'id="nutGoiY"' in html


def test_goi_y_phai_qua_buoc_DUYET(html):
    """Luật cứng #5: tool đề xuất, người duyệt. Tự nhận hết là sổ đầy rác sau
    một lần bấm nhầm."""
    assert "function nhanGoiY(" in html
    i = html.index("async function goiYTaiSan(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "luuSoLen()" not in than, "gợi ý xong không được tự lưu vào sổ"


# ═══════════ việc 4: LLM điền cột kỹ thuật + prompt tiếng Anh ════════════════
def test_prompt_dung_BAN_TIENG_ANH_khi_da_co(html):
    """Đội viết treatment tiếng Việt; prompt gửi nhà AI phải tiếng Anh. Có `pa`
    thì dùng `pa`, chưa có thì tạm dùng `t` và phải BÁO cho người dùng biết."""
    i = html.index("function promptAnh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "x.pa" in than, "prompt ảnh phải ưu tiên bản tiếng Anh"
    j = html.index("function promptVideo(")
    assert "x.pv" in html[j:html.index(chr(10) + "}", j)]


def test_bao_ro_khi_prompt_CHUA_DICH(html):
    """"chưa dịch" vốn đã nằm ở cột tiếng Việt nên kiểm chuỗi đó là XANH GIẢ.
    Canh đúng chỗ: hộp cảnh phải có cờ báo prompt còn là tiếng Việt."""
    i = html.index("function moCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "chuaDich" in than, "hộp cảnh phải báo prompt chưa qua LLM"
    j = html.index("function chuaDich(")
    assert "pa" in html[j:html.index(chr(10) + "}", j)]


def test_create_prompt_theo_TUNG_CANH(html):
    """User chốt 25/09: "đưa Sinh prompt về từng cảnh luôn. Đổi tên thành
    Create Prompt"."""
    assert "nutKyThuat" not in html and "sinhKyThuat" not in html
    assert "async function createPrompt(" in html
    i = html.index("function moCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "Create Prompt" in than


def test_the_canh_hien_cot_ky_thuat_da_dien(html):
    """Chip trên thẻ phải đổi từ 'góc máy —' sang giá trị thật, không thì điền
    xong nhìn vẫn y như chưa điền."""
    i = html.index("function veTheCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "x.goc" in than and "x.sfx" in than


def test_dong_hop_thi_QUEN_canh_dang_mo(html):
    """Đo Chrome 24/09: Esc đóng hộp rồi bấm "Sinh prompt" thì hộp TỰ BẬT LẠI —
    `dongCanh()` chỉ ẩn lớp phủ mà không quên `canhDangMo`, nên chỗ nào vẽ lại
    theo biến đó cũng dựng hộp dậy."""
    i = html.index("function dongCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert 'canhDangMo = ""' in than


def test_so_rong_thi_dung_bao_DU_REF(html):
    """Đo production 24/09: sổ chưa có gì mà thanh tiến độ báo "0 tài sản · đủ
    ref" — vô lý, và tệ hơn là nó bảo người ta rằng bước lập sổ đã xong."""
    i = html.index("function tienDoSo(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "chưa lập" in than


def test_the_canh_RONG_duoc_danh_dau(html):
    """Cảnh rỗng vẫn hiện thành thẻ (để hai màn khớp nhau), nhưng phải nhìn ra
    ngay là chưa có nội dung — không thì người ta tưởng thẻ hỏng."""
    i = html.index("function veTheCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "chưa có nội dung" in than


def test_sinh_prompt_KHONG_dem_canh_rong(html):
    """Nút sinh prompt bỏ qua cảnh rỗng — gửi cho LLM thì nó bịa nội dung."""
    i = html.index("function tienDoSo(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "c.t" in than, "đếm cảnh chưa gán phải bỏ qua cảnh rỗng"


def test_JS_va_PYTHON_cung_mot_luat_ve_canh_rong(html):
    """Vá tầng Python mà quên tầng JS thì DU trên trình duyệt vẫn lọc cảnh rỗng
    — đúng lỗi user báo vẫn còn (đo 24/09). Hai bên phải cùng luật: giữ cảnh
    rỗng khi còn ít nhất một cảnh có chữ."""
    for ten in ("docCanh", "ghiCanhVao"):
        i = html.index("function %s(" % ten)
        than = html[i:html.index(chr(10) + "}", i)]
        # cấm LỌC theo nội dung cảnh; TRIM nội dung thì vẫn đúng
        for k in range(len(than)):
            if than.startswith(".filter(", k):
                than_loc = than[k:k + 160]
                assert "c.t" not in than_loc.split(")")[0] + ")",                     f"{ten} còn lọc bỏ cảnh rỗng"
    i = html.index("function ghiCanhVao(")
    assert "some(" in html[i:html.index(chr(10) + "}", i)],         "ghiCanhVao phải kiểm CÒN cảnh nào có chữ không, thay vì lọc từng cảnh"


# ═══════════════════ icon: chỉ dấu hình học đơn sắc ═════════════════════════
# User chốt 24/09: "các icon chưa về đúng chuẩn minimalist". Emoji được hệ điều
# hành vẽ thành hình MÀU, mỗi máy một kiểu — nó phá bảng màu của tool và trông
# như dán sticker. Dấu hình học đơn sắc ăn theo `currentColor` nên luôn hợp nền.

_CAM = "✨⚠✎✗🔒👁🔖"


def test_trang_khong_dung_EMOJI_mau(html):
    thay = sorted({c for c in html if c in _CAM or 0x1F000 <= ord(c) <= 0x1FAFF})
    assert not thay, ("còn emoji màu trong trang: " +
                      " ".join("%s (U+%04X)" % (c, ord(c)) for c in thay))


def test_dau_X_dung_MOT_kieu(html):
    """✗ và ✕ trông gần giống nhau nhưng khác nét — dùng lẫn là trang nhìn lệch."""
    assert "✗" not in html


def test_dau_CO_NGUON_la_dau_tham_chieu(html):
    """Dòng có nguồn đánh dấu bằng ※ (reference mark) — đúng nghĩa, đơn sắc."""
    i = html.index('title="có nguồn"')
    assert "※" in html[i:i + 40]


# ═══════════════════ đợt 2: ảnh trên thẻ + cổng duyệt ═══════════════════════
def test_the_canh_HIEN_ANH_khi_da_sinh(html):
    """Ô 16:9 trên thẻ vốn để trống chờ đợt 2 — giờ đổ ảnh vào đúng chỗ đó."""
    i = html.index("function veTheCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "duongAnh(" in than and "<img" in than


def test_anh_neo_vao_MA_RIENG_cua_canh(html):
    """Neo vào số thứ tự thì chèn một cảnh phía trên là ảnh trỏ sang cảnh khác."""
    i = html.index("function duongAnh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "x.id" in than or "id" in than
    j = html.index("function dungCanhTap(")
    assert "id: cn.id" in html[j:html.index(chr(10) + "}", j)]


def test_co_nut_sinh_anh_va_duyet(html):
    assert "async function sinhAnh(" in html
    assert "async function duyetAnh(" in html


def test_KHONG_co_nut_sinh_hang_loat(html):
    """User chốt 25/09: "nút tạo ảnh / tạo video CHỈ xuất hiện trong từng cảnh,
    không phải nút sinh cho tất cả". Sinh hàng loạt là đốt tiền vào những cảnh
    chưa ai nhìn — mỗi cảnh phải là một quyết định."""
    assert "nutAnhChuong" not in html
    assert "sinhAnhChuong" not in html


def test_nhan_nut_anh_la_GEN_IMAGE(html):
    i = html.index("function moCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "Gen Image" in than
    assert "Sinh ảnh" not in than and "Sinh lại ảnh" not in than


def test_canh_da_duyet_duoc_danh_dau(html):
    i = html.index("function veTheCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "duyet" in than


def test_nhan_TAI_SAN_va_TONG_doi_sang_Asset_Tone(html):
    """User chốt 25/09: "tài sản đổi thành Asset", "tông đổi thành Tone"."""
    assert 'id="nutTaiSan"' in html and 'id="nutTong"' in html
    i = html.index('id="nutTaiSan"')
    assert "Asset" in html[i:i + 90] and "Tài sản</button>" not in html
    j = html.index('id="nutTong"')
    assert "Tone" in html[j:j + 90] and "Tông</button>" not in html


def test_dungCanhTap_chep_DU_MOI_KHOA(html):
    """Hai lần liên tiếp `dungCanhTap()` quên chép một khoá sang: `ts` (gán tài
    sản mà prompt không đổi) rồi `anh` (sinh ảnh xong mà thẻ vẫn trống). Cả hai
    đều im lặng — không lỗi console, chỉ là màn hình không đổi. Canh CẢ BỘ khoá
    thay vì thêm từng test một sau mỗi lần vấp."""
    i = html.index("function dungCanhTap(")
    than = html[i:html.index(chr(10) + "}", i)]
    for k in ("id", "t", "co", "goc", "cd", "sfx", "tong", "ts", "pa", "pv",
              "duyet", "anh"):
        assert (k + ":") in than, f"dungCanhTap quên chép khoá `{k}`"


def test_co_nut_SINH_REF_trong_so_tai_san(html):
    """User báo 25/09: "chưa có nút sinh ảnh ref"."""
    assert "async function sinhRef(" in html
    i = html.index("function oRef(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "sinhRef(" in than


def test_nut_sinh_ref_CHI_HIEN_khi_co_prompt_tao_ref(html):
    """Không có `pr` thì bấm chỉ tốn một vòng gọi rồi nhận 400."""
    i = html.index("function oRef(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "x.pr" in than


def test_hop_canh_sinh_duoc_REF_cua_tai_san_thieu(html):
    """User nói "khi click vào từng cảnh" — hàng tài sản trong hộp cảnh phải
    sinh được ref ngay tại chỗ, không bắt mở sổ rồi mò lại."""
    i = html.index("function veTaiSanCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "sinhRef(" in than


# ═══════════ báo ĐANG LÀM + bắt buộc có asset (user 25/09) ══════════════════
def test_moi_nut_sinh_deu_BAO_DANG_LAM(html):
    """User 25/09: "khi ấn nút thì không thấy có thông báo đang làm mà chỉ đến
    khi ảnh xuất hiện mới biết". Đổi chữ trên dòng trạng thái là quá kín — phải
    khoá nút và đổi chữ NGAY TRÊN NÚT."""
    i = html.index("async function banRon(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "disabled = true" in than and "textContent = chu" in than,         "banRon phải khoá nút VÀ đổi chữ trên nút"
    assert "finally" in than, "hỏng giữa chừng cũng phải mở khoá nút lại"
    for ten in ("sinhAnh", "createPrompt", "duyetAnh"):
        j = html.index("async function %s(" % ten)
        assert "banRon(" in html[j:html.index(chr(10) + "}", j)],             f"{ten} phải đi qua banRon"
    k = html.index("async function sinhRef(")
    than_ref = html[k:html.index(chr(10) + "}", k)]
    assert "Đang vẽ ref" in than_ref and "disabled = true" in than_ref


def test_gen_image_CANH_BAO_khi_canh_chua_gan_asset(html):
    """User 25/09: "vừa sinh thử 2 cảnh và hoàn toàn không khớp mood với kịch
    bản. Do đó tầm quan trọng của việc sinh asset phải được chú ý hơn và đảm bảo
    asset luôn được sử dụng trong prompt ảnh và video".

    Cảnh không gắn asset nào thì prompt không có ràng buộc nhất quán — ảnh ra
    tuỳ hứng. Không cấm (có cảnh thật sự không cần asset), nhưng phải HỎI."""
    i = html.index("async function sinhAnh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "confirm(" in than
    assert "asset" in than.lower()


def test_the_canh_danh_dau_CHUA_GAN_ASSET(html):
    i = html.index("function veTheCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "chưa gán asset" in than


def test_hop_canh_bao_ro_prompt_THIEU_ASSET(html):
    """Nhìn vào prompt phải thấy ngay nó có mô tả asset hay không."""
    i = html.index("function moCanh(")
    than = html[i:html.index(chr(10) + "}", i)]
    assert "chưa gán asset" in than


def test_bang_canh_bao_trong_hop_la_KHOI_CHU(html):
    """Đo Chrome 25/09: băng "chưa gán asset" mượn class `.khoa` (vốn
    display:flex cho băng khoá chương) nên chữ bị vỡ thành ba cột rời rạc:
    "Cảnh này | chưa gán asset | — prompt…". Băng chữ thì phải xếp dòng."""
    assert ".nhac{" in html, "cần class riêng cho băng nhắc trong hộp cảnh"
    i = html.index(".nhac{")
    assert "display:flex" not in html[i:i + 200]
    j = html.index("function moCanh(")
    than = html[j:html.index(chr(10) + "}", j)]
    assert 'class="nhac"' in than and 'class="khoa"' not in than
