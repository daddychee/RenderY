"""Hai luật user chốt 30/10 sau bản thử C (DM002 C1): (1) tiếng của ai thì hình người đó,
(2) phối cảnh đúng. Đóng gói vào tool:
  - dán kịch bản giữ khối đầu cảnh (Mở cảnh, Vào, Máy dàn cảnh, …) vào ô `vi`;
  - Breakdown: shot `Hình:` ghi "một cú liền" đặt 10 giây;
  - thẻ shot nhắc luật 1 (không chặn — luật cứng 5);
  - shot NGƯỜI VÀO (cảnh nối cảnh trước cùng phim trường, lần đầu người mới hiện, khung nhiều
    người): ảnh khung đầu vẽ trên ảnh dàn cảnh cảnh TRƯỚC, người mới đứng ở cửa.
Đồ giả, không mạng.
"""

from __future__ import annotations

import pathlib

import autoedit.treatment.app as mapp
from autoedit.treatment import drama as md
from test_treatment_chay_chuong import TAM
from test_treatment_cum_canh import CUM, KtCum, _bd_va_prompt, _dan
from test_treatment_drama import KICH_BAN
from test_treatment_drama_api import VeAnhGia, _bo, _ve_du_ref

KHOI = """Mở cảnh: Tasha trái · Marcus phải
Máy dàn cảnh: nhìn từ cửa vào phòng; cửa sổ lớn bên trái
Tóm tắt: Marcus buộc tội Tasha lấy nhẫn.
Tiến trình:
1. (N01) Marcus giơ hộp nhẫn rỗng; Tasha nói mình chỉ đi lấy nước."""
# C001 Tasha, Marcus; C002 cùng phòng cùng buổi, Ruth vào (CUM), shot 1 viết theo luật người vào
VAO = CUM.replace("Hình: shot 1 trung ba người bên bàn bếp. Shot 2 cận Marcus.",
                  "Hình: shot 1 toàn theo hướng máy dàn cảnh, máy đứng yên, một cú liền: Ruth đã đứng trong "
                  "khung cửa, thấy trọn người, đi tới đứng cạnh giường. Shot 2 cận Tasha. Shot 3 cận Marcus.")
assert VAO != CUM


def test_dung_code_cua_cay_dang_test():
    goc = pathlib.Path(__file__).resolve().parents[1]
    assert pathlib.Path(mapp.__file__).resolve().is_relative_to(goc), mapp.__file__


# ═══════ dán: khối đầu cảnh vào ô vi ══════════════════════════════════════════════
def test_dan_giu_khoi_dau_canh_trong_vi():
    r = md.tach_tap(KICH_BAN.replace("Có mặt: Tasha, Marcus\n\n### P001", f"Có mặt: Tasha, Marcus\n{KHOI}\n\n### P001"))
    assert not r["loi"], r["loi"]
    vi = r["chuong"][0]["dong"][0]["vi"]
    assert vi == "Có mặt: Tasha, Marcus\n" + KHOI, vi
    assert r["chuong"][1]["dong"][0]["vi"] == "Có mặt: Tasha, Marcus", "cảnh không có khối: như cũ"


def test_dan_bo_nhac_thieu_cu_may_vi_luat_2():
    from autoedit.treatment import kiem_drama as kd
    assert any("không có cú máy hay góc có ý đồ" in x for _, x in kd.kiem(KICH_BAN)[1]), "mẫu phải chạm nhắc này"
    assert not any("cú máy" in x for x in md.tach_tap(KICH_BAN)["nhac"])


# ═══════ Breakdown: "một cú liền" = 10 giây ═══════════════════════════════════════
def test_shot_lien_theo_doan_shot_n_cua_hinh():
    t = "P1 · x\nHình: shot 1 cận A. Shot 2 toàn, một cú liền: B đi tới. Shot 3 cận B.\nThoại: A: \"Hi.\""
    assert md.shot_lien(t, 3) == [1]
    assert md.shot_lien(t, 2) == [], "Breakdown chia khác số đoạn: không đoán"
    assert md.shot_lien("P1\nHình: toàn, một cú liền: B đi tới.", 1) == [0]
    assert md.shot_lien("P1\nHình: shot 1 cận A. Shot 2 cận B.", 2) == []


# ═══════ luật 1 ═══════════════════════════════════════════════════════════════════
LT = [{"ten": "Brooke", "cau": "Wrong place.", "nghi": False}, {"ten": "Hattie", "cau": "Mine.", "nghi": False}]
THAY = {"Brooke", "Hattie"}


def test_luat1_khung_chi_nguoi_noi_hay_qua_vai_nguoi_nghe():
    assert md.nhac_luat1({"cau": [], "co_mat": ["Brooke", "Hattie"]}, LT, THAY) == [], "shot im"
    assert md.nhac_luat1({"cau": [0], "co_mat": ["Brooke"]}, LT, THAY) == []
    ots = {"cau": [1], "goc": "ots", "co_mat": ["Brooke", "Hattie"], "t": "Qua vai Brooke, Hattie rõ mặt"}
    assert md.nhac_luat1(ots, LT, THAY) == []
    assert "quay lưng" in md.nhac_luat1(dict(ots, cau=[0]), LT, THAY)[0], "người nói ở tiền cảnh"
    assert "cùng nói" in md.nhac_luat1({"cau": [0, 1], "co_mat": ["Brooke", "Hattie"]}, LT, THAY)[0]
    assert "khung có cả Hattie" in md.nhac_luat1({"cau": [0], "goc": "eye", "co_mat": ["Brooke", "Hattie"]},
                                                  LT, THAY)[0]


def test_luat1_cau_phat_tren_mat_nguoi_khac_tru_nguoi_vang_mat():
    assert "phát trên mặt Hattie" in md.nhac_luat1({"cau": [0], "co_mat": ["Hattie"]}, LT, THAY)[0]
    assert md.nhac_luat1({"cau": [0], "co_mat": ["Hattie"]}, LT, {"Hattie"}) == [], "điện thoại: không có trong clip"


# ═══════ shot người vào ═══════════════════════════════════════════════════════════
def test_prompt_vao_nguoi_moi_dung_o_cua_nguoi_cu_giu_cho():
    nguoi = [{"ten": "Tasha", "chu": "woman 28"}, {"ten": "Ruth · dạng 2", "chu": "woman 75"}]
    pd = {"vi_tri": {"Ruth": "in the armchair", "Tasha": "by the window"}, "phong": {"Ruth": "the tall window"}}
    p = md.prompt_vao(pd, nguoi, ["Tasha"], {}, ["Ruth"], [{"loai": "dao_cu", "ten": "Hộp nhẫn"}])
    assert p.startswith("Image 1 is the master wide shot of this same room a few moments earlier.")
    assert f"Add Ruth {md.CUA}, {md.RO_NGUOI}." in p and "armchair" not in p and "Behind Ruth" not in p
    assert "Tasha stays exactly where they are in Image 1" in p
    assert "Image 4 shows an object" in p, "đồ vật sau tấm người"
    assert "Exactly one Tasha and one Ruth, nobody else." in p
    p = md.prompt_vao(dict(pd, vao={"ruth": "standing in the white door on the left."}), nguoi, ["Tasha"], {}, ["Ruth"])
    assert f"Add Ruth standing in the white door on the left, {md.RO_NGUOI}." in p, "câu cửa LLM viết"


class KtVao(KtCum):
    """Breakdown giả của C002: shot toàn có Ruth (người mới), rồi cận từng người nói. `sai`: câu của
    Marcus đặt lên cận Tasha (luật 1)."""

    def __init__(self, sai=False):
        super().__init__()
        self.sai = sai

    def drama_canh(self, than):
        ra = super().drama_canh(than)
        return dict(ra, vao={"Ruth": "standing in the open hospital room door"}) if than.startswith("CẢNH: C002") else ra

    def drama_breakdown(self, than):
        if "P003" not in than:
            return super().drama_breakdown(than)
        return {"shots": [{"t": "toàn, Ruth vào", "co": "WS", "goc": "eye", "cd": "static", "cau": [],
                           "co_mat": ["Tasha", "Marcus", "Ruth"]},
                          {"t": "cận Tasha", "co": "CU", "goc": "eye", "cd": "static", "cau": [0], "co_mat": ["Tasha"]},
                          {"t": "cận", "co": "CU", "goc": "eye", "cd": "static", "cau": [1],
                           "co_mat": ["Tasha" if self.sai else "Marcus"]}]}


def _san(tmp_path, kt, va=None, kich_ban=VAO):
    kho, c = _bo(tmp_path, kt=kt, va=va)
    assert c.post("/api/tap", json={"ma": "D1", "ten": "Hộp nhẫn", "loai": "drama"}).status_code == 200
    assert c.post("/api/tap/D1/drama", json={"text": kich_ban}).status_code == 200
    _ve_du_ref(kho, TAM)
    _bd_va_prompt(c, 0, 1)
    clip = kho.doc("D1", "C1")["dong"][1]["canh"][0]
    return kho, c, clip["id"], md.doc_sh(clip["sh"])


def test_shot_nguoi_vao_ve_tren_anh_dan_canh_canh_truoc(tmp_path):
    va = VeAnhGia()
    kho, c, ma, sh = _san(tmp_path, KtVao(), va)
    assert [s.get("gi") for s in sh] == ["10", None, None], "Breakdown: một cú liền = 10 giây"
    for i in (0, 1):
        assert c.post(f"/api/tap/D1/C1/dong/{i}/dan-canh").status_code == 200
        assert c.post(f"/api/tap/D1/C1/dong/{i}/dan-canh/duyet").status_code == 200
    ds = c.get(f"/api/tap/D1/C1/canh/{ma}/shot").json()
    assert ds[0]["giay"] == 10
    assert any("shot người vào" in x for x in ds[0]["nhac"]) and not any("người vào" in x for x in ds[1]["nhac"])
    p = c.get(f"/api/tap/D1/C1/canh/{ma}/shot/{sh[0]['sid']}/prompt").json()["anh"]
    assert p.startswith("Image 1 is the master wide shot of this same room")
    assert f"Add Ruth standing in the open hospital room door, {md.RO_NGUOI}." in p, "câu cửa LLM viết, lưu ở pd"
    n = len(va.goi)
    assert c.post(f"/api/tap/D1/C1/canh/{ma}/shot/{sh[0]['sid']}/anh").status_code == 200
    g = va.goi[n]
    assert g["prompt"] == p, "thấy gì gửi nấy"
    assert g["ref"][0] == kho.ref_dang_co("D1", _dan(c, 0)["td"]), "Image 1 = ảnh dàn cảnh cảnh TRƯỚC"
    assert len(g["ref"]) == 4, "ảnh trước + tấm Tasha, Marcus, Ruth"
    assert c.post(f"/api/tap/D1/C1/canh/{ma}/shot/{sh[1]['sid']}/anh").status_code == 200
    assert va.goi[-1]["ref"][0].name.endswith("-cat.png"), "shot sau: mảnh cắt ảnh dàn cảnh cảnh này như cũ"


def test_canh_dau_cum_khong_co_shot_nguoi_vao(tmp_path):
    kb = VAO.replace("phòng VIP bệnh viện · sáng · N02", "phòng VIP bệnh viện · tối · N02")
    kho, c, ma, _ = _san(tmp_path, KtVao(), kich_ban=kb)
    assert not any("người vào" in x for d in c.get(f"/api/tap/D1/C1/canh/{ma}/shot").json() for x in d["nhac"])


def test_the_shot_nhac_luat1(tmp_path):
    kho, c, ma, _ = _san(tmp_path, KtVao(sai=True))
    ds = c.get(f"/api/tap/D1/C1/canh/{ma}/shot").json()
    assert any("câu của Marcus phát trên mặt Tasha" in x for x in ds[2]["nhac"]), ds[2]["nhac"]
    assert not any("phát trên mặt" in x for x in ds[1]["nhac"])
