"""Nút BREAKDOWN (Owner 27/09): người viết direction vắn tắt cho phân cảnh, LLM
viết lại chi tiết + đặt góc · cỡ · máy, ghi THẲNG vào cảnh của dòng — không bảng
duyệt, sai thì sửa tay như sửa prompt. Lệnh = đúng lệnh đã đo ở trang ⑮.
"""

from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment import app as mapp
from autoedit.treatment import dong as mdong
from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho

HTML = pathlib.Path(mapp.__file__).parent / "static" / "treatment.html"


class BreakdownGia:
    def __init__(self, tra=None):
        self.goi = []
        self.tra = tra if tra is not None else [
            {"t": "Tàu ngầm K-129 lừ lừ đi dưới biển, chỉ thấy một phần vỏ.", "co": "MS", "goc": "low", "cd": "truck_left", "ly_do": "..."},
            {"t": "Mũi tàu xé nước, máy tiến dần về chóp mũi.", "co": "cu", "goc": "eye", "cd": "push_in"},
            {"t": "Cánh quạt đuôi tàu quay trong nước.", "co": "ECU", "goc": "low", "cd": "arc"},
            {"t": "Tàu trôi ra khỏi khung, còn lại khối nước trống.", "co": "WS", "goc": "high", "cd": "static"},
        ]

    def ky_thuat(self, muc, tai_san):
        return [{"id": m["id"], "lap": "x", "pa": "EN", "pv": "EN", "sfx": "s"} for m in muc]

    def breakdown(self, voice, y, giay, tai_san):
        self.goi.append({"voice": voice, "y": list(y), "giay": giay, "tai_san": [t["ten"] for t in tai_san]})
        return self.tra


def _bo(tmp_path, kt=None):
    kho = Kho(tmp_path / "k.db")
    kho.tao_tap("SE001", "K-129")
    kt = kt or BreakdownGia()
    c = TestClient(tao_app(kho, ky_thuat=kt))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "In the spring of 1968, a Soviet submarine vanished somewhere in the depths of the Pacific, carrying ninety-eight men. Not one of them ever came home.",
         "vi": "", "het": 0,
         "canh": [{"t": "Tàu ngầm dưới biển. Không show trọn tàu.", "co": "CU", "goc": "eye", "cd": "slow push in",
                   "pa": "OLD EN", "pv": "OLD PV", "lap": "old", "pat": "tay", "duyet": "1", "ts": ["as1"], "td": "td1",
                   "tong": "t1", "mda": "gpt-image-2"},
                  {"t": "Focus vào mũi"},
                  {"t": "Tàu ngầm out frame", "pa": "OLD2"}]}]})
    return c, kho, kt


def _canh(kho):
    return mdong.doc_canh(kho.doc("SE001", "H")["dong"][0])


def test_breakdown_MOI_Y_MOT_CU_ghi_thang_vao_canh_cung_vi_tri(tmp_path):
    """Owner: mỗi ý một cú. LLM trả 4 cho 3 ý -> chỉ 3 cảnh được viết lại, cú thừa bỏ."""
    c, kho, kt = _bo(tmp_path)
    cu = _canh(kho)
    r = c.post("/api/tap/SE001/H/dong/0/breakdown")
    assert r.status_code == 200 and r.json() == {"ok": True, "so_cu": 3, "so_y": 3}
    moi = _canh(kho)
    assert len(moi) == 3, "không đẻ thêm cảnh"
    assert [x["t"] for x in moi] == [t["t"] for t in kt.tra[:3]]
    assert [(x.get("co"), x.get("goc"), x.get("cd")) for x in moi] == [
        ("MS", "low", "truck_left"), ("CU", "eye", "push_in"), ("ECU", "low", "arc")]
    # cảnh giữ id + ts/td/tong/mda (ảnh/video đã vẽ không mất dấu); bỏ prompt cũ + con dấu duyệt
    assert [x["id"] for x in moi] == [x["id"] for x in cu]
    assert moi[0]["ts"] == ["as1"] and moi[0]["td"] == "td1" and moi[0]["tong"] == "t1" and moi[0]["mda"] == "gpt-image-2"
    for khoa in ("pa", "pv", "lap", "pat", "duyet"):
        assert khoa not in moi[0], khoa
    assert "pa" not in moi[2]


def test_LLM_tra_THIEU_thi_y_con_lai_giu_nguyen(tmp_path):
    kt = BreakdownGia([{"t": "Cú một.", "co": "WS", "goc": "low", "cd": "track"}])
    c, kho, _ = _bo(tmp_path, kt)
    cu = _canh(kho)
    assert c.post("/api/tap/SE001/H/dong/0/breakdown").json() == {"ok": True, "so_cu": 1, "so_y": 3}
    moi = _canh(kho)
    assert moi[0]["t"] == "Cú một." and moi[1] == cu[1] and moi[2] == cu[2]


def test_LLM_nhan_dung_direction_theo_thu_tu_voice_giay_va_asset(tmp_path):
    c, kho, kt = _bo(tmp_path)
    kho.luu_so("SE001", [{"ma": "as1", "loai": "nhan_vat", "ten": "Thuyền trưởng Kobzar"},
                         {"ma": "td1", "loai": "truong_doan", "ten": "Khoang lái"},
                         {"ma": "tg", "loai": "tong", "ten": "Lạnh"}])
    c.post("/api/tap/SE001/H/dong/0/breakdown")
    g = kt.goi[0]
    assert g["y"] == ["Tàu ngầm dưới biển. Không show trọn tàu.", "Focus vào mũi", "Tàu ngầm out frame"]
    assert g["voice"].startswith("In the spring of 1968") and g["giay"] == 10     # 26 từ / 2,6
    assert g["tai_san"] == ["Thuyền trưởng Kobzar"], "chỉ người/vật/bối cảnh — không đưa trường đoạn, tone"


def test_ma_la_thi_bo_chu_khong_gui_chu_tu_do(tmp_path):
    kt = BreakdownGia([{"t": "Một cú.", "co": "Wide", "goc": "dutch", "cd": "handheld"}])
    c, kho, _ = _bo(tmp_path, kt)
    assert c.post("/api/tap/SE001/H/dong/0/breakdown").status_code == 200
    x = _canh(kho)[0]
    assert x["t"] == "Một cú." and "co" not in x and "goc" not in x and "cd" not in x


def test_LLM_tra_rong_thi_502_va_khong_doi_gi(tmp_path):
    c, kho, _ = _bo(tmp_path, BreakdownGia([]))
    truoc = _canh(kho)
    assert c.post("/api/tap/SE001/H/dong/0/breakdown").status_code == 502
    assert _canh(kho) == truoc


def test_can_quyen_sua_va_dong_phai_co_direction(tmp_path):
    c, kho, _ = _bo(tmp_path)
    assert c.post("/api/tap/SE001/H/dong/9/breakdown").status_code == 404
    c2 = TestClient(tao_app(kho, ky_thuat=BreakdownGia()))
    c2.headers.update({"X-Remote-User": "xem", "X-Remote-Actions": ""})
    assert c2.post("/api/tap/SE001/H/dong/0/breakdown").status_code == 403


def test_lenh_la_lenh_da_do_va_mang_du_ba_bang_ma():
    l = mapp._LENH_BREAKDOWN
    for chu in ("TRUNG THÀNH", "KHÔNG bịa", "MỖI Ý = ĐÚNG MỘT CÚ MÁY", "KHÔNG chọn theo thứ tự bảng",
                "Hai cú liền nhau không cùng cỡ", "không quá 1/3 số cú là static"):
        assert chu in l, chu
    for chu in ("không quá 6", "N/3,5"):
        assert chu not in l, chu
    for chu in ():
        assert chu in l, chu
    for bang in (mapp.CO_CHU, mapp.GOC_CHU, mapp.CD_CHU):
        for k, v in bang.items():
            assert f"{k}: {v}" in l, k
    than = mapp._than_breakdown("V", ["a", "b"], 7, [{"ten": "X", "loai": "dao_cu"}])
    assert "1) a\n2) b" in than and "~7 giây" in than and "- X (vật)" in than


def test_trang_co_MOT_nut_breakdown_CA_CHUONG_goi_tung_phan_canh():
    html = HTML.read_text(encoding="utf-8")
    assert html.count("breakdownChuong(") == 2 and 'id="nutBreakdown"' in html     # nút + hàm
    assert "breakdownDong(" not in html, "Owner: một nút cho cả chương, không có nút theo phân cảnh"
    i = html.index('id="nutBreakdown"')
    assert "chi-sua" in html[i - 60:i], "người chỉ xem không thấy nút"
    j = html.index("async function breakdownChuong(")
    t = html[j:html.index(chr(10) + "}", j)]
    assert "/dong/" in t and '"/breakdown"' in t and "for(" in t, "gọi máy chủ từng phân cảnh, không một request cả chương"
    assert "confirm(" in t and "luuNgay()" in t and "taiLaiChuong(" in t and "SUA_DUOC" in t
    assert "hong" in t, "phân cảnh hỏng phải được báo, không nuốt"
