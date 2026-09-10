r"""VIỆC 1 (11/09) — popup Export timeline thay `alert()` chữ trần.

User chốt 11/09 sau khi duyệt mockup:
* (a) có clip stock không lấy được link -> **CHẶN**, hiện danh sách, yêu cầu làm lại
* (b) sạch rồi -> báo **tắt CapCut trước**, xác nhận mới xuất
* (c) đường dẫn xuất: **chỉ dán tay** (bỏ nút chọn thư mục — trình duyệt không
  trả đường dẫn thật, `showDirectoryPicker` chỉ cho handle; backend không có
  route duyệt ổ đĩa và không mở)
* watermark: **chỉ hiện thông báo**, KHÔNG nút "Mở Cài đặt" (trang đó không tồn tại)

Mockup chốt: `scratchpad/ui_popup_export.html`. Số đo/nhãn lấy TỪ MOCKUP:

| Thành phần | Mockup |
|---|---|
| khuôn hộp | `.modal` + `.modal-bg` CÓ SẴN (index.html:524-530) — không dựng khuôn mới |
| danh sách miếng hỏng | `#of-xk-ds`, cuộn `max-height:190px`, mỗi dòng `miếng N · tiêu đề · lý do` |
| cắt danh sách | 5 dòng + "… và N miếng nữa" |
| hộp cảnh báo | link chết = `--bad`, watermark = `--warn` (màu có nghĩa cố định) |
| nút hộp (a) | link chết: `⌖ Tới miếng hỏng đầu tiên` · watermark: chỉ `Đóng` |
| ô xác nhận | `#of-xk-tat` — nút Xuất KHOÁ tới khi tích |
| ô đường dẫn | `#of-xk-noi`, chỉ dán tay, KHÔNG nút chọn |

KIỂM TRƯỚC KHI CODE (11/09) — đã đo trên production:
* `soat_truoc_pha` (thay_mau.py:89) ĐÃ trả `[{mieng, id, tieu_de, ly_do}]`, và
  `server.py:1245` đã raise 409 `{ghi_chu, hong}` phân biệt watermark. **Không
  đụng backend** — việc này thuần frontend.
* `modal()` (index.html:1074) đã có; `#of-noi-xuat` (index.html:823) đã có ô dán.
* KHÔNG có trang Cài đặt trong index.html -> không vẽ nút dẫn tới chỗ trống.
"""

from __future__ import annotations

import re
from pathlib import Path

INDEX = Path("autoedit/web/static/index.html")
MOCKUP = Path("../scratchpad/ui_popup_export.html")


def _h() -> str:
    return INDEX.read_text(encoding="utf-8")


def _m() -> str:
    return MOCKUP.read_text(encoding="utf-8")


# ───────────────────────── mockup phải nằm cạnh code ─────────────────────────

def test_mockup_ton_tai_de_doi_chieu():
    """BH20: 'khớp mockup' phải đối chiếu từng dòng -> mockup phải trong repo."""
    assert MOCKUP.is_file(), f"thiếu mockup đối chiếu: {MOCKUP}"


def test_mockup_da_bo_nut_chon_va_nut_cai_dat():
    m = _m()
    assert "Chọn…" not in m, "user chốt bỏ nút chọn thư mục"
    assert 'class="chinh">⚙ Mở Cài đặt' not in m, "user chốt bỏ nút Mở Cài đặt"


# ───────────────────────────── khung popup ─────────────────────────────

def test_co_hop_thoai_xuat_trong_html():
    h = _h()
    assert 'id="of-xk"' in h, "chưa có hộp thoại Export"
    assert 'id="of-xk-ds"' in h, "chưa có vùng danh sách miếng hỏng"
    assert 'id="of-xk-tat"' in h, "chưa có ô xác nhận đã tắt CapCut"
    assert 'id="of-xk-noi"' in h, "chưa có ô nơi xuất trong hộp thoại"
    assert 'id="of-xk-di"' in h, "chưa có nút Xuất trong hộp thoại"


def test_dung_lai_khuon_modal_co_san():
    """Nguyên tắc 'fewest files/khái niệm': không dựng khuôn hộp thoại thứ hai."""
    h = _h()
    i = h.index('id="of-xk"')
    assert "modal" in h[max(0, i - 400):i + 400], "hộp Export không dùng khuôn .modal có sẵn"


def test_khong_co_nut_chon_thu_muc():
    h = _h()
    assert "showDirectoryPicker" not in h, "trình duyệt không trả đường dẫn thật"
    assert "webkitdirectory" not in h


def test_khong_co_nut_mo_cai_dat():
    h = _h()
    # chỉ cấm NÚT; câu "Vào Cài đặt → đăng nhập lại" là thông báo, được phép
    assert "Mở Cài đặt</button>" not in h, "user chốt: chỉ hiện thông báo, không nút"


# ───────────────────────────── hàm dựng nội dung ─────────────────────────────

def test_co_ham_dung_hop_va_ham_mo():
    h = _h()
    assert "function ofXkHong(" in h, "thiếu hàm dựng hộp (a) — miếng hỏng"
    assert "function ofXkHoi(" in h, "thiếu hàm dựng hộp (b+c) — xác nhận xuất"


def test_alert_cu_da_bi_thay():
    """`alert()` chữ trần: không bấm được vào miếng, không cuộn, không tô màu."""
    h = _h()
    i = h.index("async function ofDoiPha()")
    than = h[i:i + 6000]
    # `alert('Lỗi: ...')` cuối nhánh catch giữ nguyên (lỗi mạng/500 — ngoài phạm
    # vi việc 1). Cấm đúng cái alert() LIỆT KÊ MIẾNG HỎNG mà hộp thoại vừa thay.
    assert "DÍNH WATERMARK" not in h, "vẫn còn alert() liệt kê miếng hỏng"
    assert "ofXkHong(" in than, "nhánh 409 chưa gọi hộp thoại mới"
    assert "ofXkHoi(" in than, "luồng xuất chưa hỏi xác nhận"


# ───────────────────────── luật hiển thị lấy từ mockup ─────────────────────────

def test_cat_danh_sach_5_dong_nhu_mockup():
    h = _h()
    i = h.index("function ofXkHong(")
    than = h[i:i + 2600]
    assert re.search(r"slice\(0,\s*5\)", than), "mockup cắt 5 dòng rồi '… và N miếng nữa'"
    assert "miếng nữa" in than


def test_hai_ly_do_hai_mau_va_hai_nut():
    """Màu có nghĩa cố định: link chết = --bad, watermark = --warn."""
    h = _h()
    i = h.index("function ofXkHong(")
    than = h[i:i + 2600]
    assert "watermark" in than.lower(), "chưa phân biệt watermark"
    assert "--warn" in than and "--bad" in than, "hai lý do phải ra hai màu"
    assert "Tới miếng hỏng" in than, "link chết phải có nút nhảy tới miếng"


def test_nut_xuat_khoa_toi_khi_tich_o_xac_nhan():
    h = _h()
    i = h.index("function ofXkHoi(")
    than = h[i:i + 2600]
    assert "of-xk-tat" in than and "disabled" in than, \
        "nút Xuất phải khoá tới khi tích 'Tôi đã tắt CapCut'"


def test_hop_xac_nhan_noi_ro_tat_capcut_va_ghi_de():
    h = _h()
    i = h.index("function ofXkHoi(")
    than = h[i:i + 2600]
    assert "Tắt CapCut" in than, "phải nói rõ tắt CapCut trước"
    assert "ghi đè" in than, "phải nói rõ lý do: tool ghi đè thư mục draft"


def test_hien_ten_draft_se_ghi_vao():
    """BH20 — dòng này CÓ trong mockup, lần đầu code tôi bỏ sót.

    Tên hiện tại là `OFF_<project_id>` (thay_mau.py:765). Tên `OFF_<tập>_<chương>`
    là VIỆC 2, chưa làm — không hứa tên chưa tồn tại.
    """
    h = _h()
    i = h.index("function ofXkHoi(")
    than = h[i:i + 2600]
    assert "Sẽ ghi vào" in than, "mockup có dòng cho biết sẽ ghi vào thư mục nào"
    assert "OFF_${esc(OF_PID)}" in than, "phải hiện tên draft THẬT đang dùng"


def test_moi_chuoi_chen_vao_html_deu_qua_esc():
    """Đường dẫn/tiêu đề do người dán — chèn thẳng vào innerHTML là lỗ XSS.

    Chỉ soát BIẾN NGOÀI (tiêu đề clip, lý do, nơi xuất, project id). Các mảnh
    HTML tự dựng (`dong`, `con`, `nhac`, `nut`) đã esc bên trong rồi.
    """
    h = _h()
    NGOAI = ("x.tieu_de", "x.ly_do", "noi_cu", "OF_PID", "ten_draft")
    for ten in ("function ofXkHong(", "function ofXkHoi("):
        than = h[h.index(ten):h.index(ten) + 2600]
        for bien in re.findall(r"\$\{([^}]*)\}", than):
            for ng in NGOAI:
                if ng in bien and "esc(" not in bien:
                    assert False, f"{ten}: `${{{bien.strip()}}}` chưa qua esc()"


def test_lo_xss_that_bi_bat():
    """Kiểm chính cái test trên: bỏ esc() đi thì nó phải kêu."""
    xau = "`<div>${x.tieu_de}</div>`"
    assert "esc(" not in xau and "x.tieu_de" in xau
