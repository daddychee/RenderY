"""Mỗi shot một video + đồng nhất phối cảnh (docs/SPEC_DONG_NHAT_PHOI_CANH.md).

Đo thật 29/10 trên DM001 P031 lần 4 (`ghep_dm4.py`): ảnh khung đầu cắt từ ảnh
dàn cảnh theo luật 180° cho phông 3/3, hướng nhìn 3/3. Test giữ chữ prompt sát
bản đã đo; chỗ khác bản đo (câu Image 1, "near {O}") ghi rõ ở từng test.
"""

from __future__ import annotations

from autoedit.treatment import dich, drama
from autoedit.treatment.tai_san import LOI_REF

T = ("Hattie cảm ơn Nia\n"
     "Thoại: Hattie (chậm): \"I asked Marcus to send you up. You paid for my tea with your tips. Nobody does that.\"\n"
     "Thoại: Nia (ngượng): \"Ma'am, it was only ten dollars.\"\n"
     "Thoại: Hattie: \"It was more than that.\"")
LT = drama.loi_thoai(T)
CHU_N = ("Beautiful Black woman about 29, slim, warm brown skin, large expressive eyes, long box braids tied low, wearing "
         "dark blue jeans, a white t-shirt and a worn mustard knit cardigan.")
CHU_H = ("a dignified 80-year-old Black woman, small and upright, deep brown skin, kind sharp eyes behind gold-rimmed "
         "glasses, silver hair in a low bun, wearing a plain grey wool cardigan over a cream blouse, a faded canvas tote "
         "bag on her right shoulder.")
GIONG_H = ("Hattie's voice: a woman of about 80, low and raspy, slow and deliberate pace, a warm Southern American "
           "accent, natural, not exaggerated, not a comedy voice.")
NGUOI = {"Hattie": {"ma": "nv01", "ten": "Hattie", "chu": CHU_H, "tieng": GIONG_H},
         "Nia": {"ma": "nv02_d2", "ten": "Nia · dạng 2", "chu": CHU_N, "tieng": ""}}
TIENG = {"Hattie": GIONG_H}
LOOK = "Warm interior daylight in an 18th-floor hotel suite."
NEN = ("a faint steady hum of the suite's climate system, the muffled distant murmur of the city far below through "
       "thick glass, the soft dead quiet of a carpeted high-floor room.")
CHO = ("Where they sit: Nia on the low wooden bench by the windows, Hattie at the right end of the cream sofa, to Nia's "
       "right; they face each other across the round coffee table. Seated people stay seated.")
PD = {
    "look": LOOK, "nen": NEN, "truc": "Hattie sits on the sofa on the right side of the frame.",
    "giu": ("Hattie wears a plain grey wool cardigan over a cream blouse, gold-rimmed glasses, and a faded canvas tote "
            "bag on her right shoulder; Nia wears dark blue jeans, a white t-shirt, and a worn mustard knit cardigan."),
    "ben": {"Nia": "trai", "Hattie": "phai"},
    "phong": {"Nia": "the floor-to-ceiling windows, the sheer curtains and the hazy city",
              "Hattie": ("the slim dark wooden console with the framed botanical prints and the tall taupe wall panel. "
                         "No window behind Hattie.")},
    "cho": CHO,
    "vi_tri": {"Nia": "on the low wooden bench right by the floor-to-ceiling windows",
               "Hattie": "at the right end of the cream sofa"},
    "dan": "Wide shot, eye level: Nia on the bench on the left, Hattie on the sofa on the right",
    "shots": [
        {"cach": "", "mat": "Hattie settles her gaze warmly toward Nia, mouth closed", "am": ""},
        {"cach": ("Slow and deliberate, even spacing between phrases, a small pause after 'send you up' and again "
                  "after 'with your tips', gentle weight landing on 'Nobody does that'"),
         "mat": ("Hattie tilts her head and leans in, eyes steady and kind behind her glasses, the faintest knowing "
                 "lift at the corner of her mouth, settling into quiet certainty"),
         "am": "faint creak of the sofa cushion as she leans"},
        {"cach": "Quiet and a little flustered", "mat": "Nia blinks, glances down then back up", "am": ""},
        {"cach": "Low and gentle", "mat": "Hattie's features soften", "am": "quiet room tone"},
    ],
}
SH = [
    {"co": "MS", "goc": "eye", "cd": "static", "cau": [], "co_mat": ["Hattie", "Nia"]},
    {"co": "MCU", "goc": "ots", "cd": "push_in", "cau": [0], "co_mat": ["Nia", "Hattie"]},
    {"co": "CU", "goc": "eye", "cd": "static", "cau": [1], "co_mat": ["Nia"]},
    {"co": "MCU", "goc": "eye", "cd": "static", "cau": [2], "co_mat": ["Hattie"]},
]
KH2 = ("medium close-up, over-the-shoulder shot, from behind a second person's shoulder in the foreground: Nia's "
       "shoulder and the back of her braided head fill the lower left foreground, Hattie facing the camera beyond it "
       "on the right as she leans forward from the sofa.")
MAY2 = "The camera pushes in slowly and steadily toward the subject."
SHEET = [LOI_REF["nhan_vat"].format(i=i) for i in (2, 3)]


# ───────────────────────────── chọn người, giây, cắt ─────────────────────────
def test_khung_cat_theo_ben_do_p031():
    assert drama.khung_cat("trai") == (0.115, 0.30, 0.515, 0.70)
    assert drama.khung_cat("phai") == (0.56, 0.30, 0.96, 0.70)
    assert drama.khung_cat("giua") == drama.khung_cat("la") == (0.30, 0.30, 0.70, 0.70)
    assert set(drama.BEN) == {"trai", "phai", "giua"}


def test_cat_master_ti_le_anh_goc_kep_trong_vung_khong_vien(tmp_path):
    """Ảnh 400x200, viền đen phải 30 px, trên 10 px. Nội dung: R = x, G = y nên
    điểm góc của mảnh cắt cho biết chính xác chỗ cắt trong ảnh gốc."""
    from PIL import Image

    a = Image.new("RGB", (400, 200))
    a.putdata([(x % 256, y, 200) if x < 370 and y >= 10 else (0, 0, 0) for y in range(200) for x in range(400)])
    a.save(tmp_path / "m.png")
    # Khung trong vùng sạch: đúng toạ độ trên ảnh gốc (trang kéo khung trên ảnh gốc)
    ra = drama.cat_master(tmp_path / "m.png", drama.khung_cat("trai"), tmp_path / "con" / "cat.png")
    b = Image.open(ra)
    assert ra == tmp_path / "con" / "cat.png"
    assert b.getpixel((0, 0))[:2] == (46, 60) and b.size == (206 - 46, 140 - 60)
    # Khung chạm mép phải và mép trên: kẹp vào x < 370, y >= 10, không dính viền đen
    b = Image.open(drama.cat_master(tmp_path / "m.png", (0.6, 0.0, 1.0, 1.0), tmp_path / "mep.png"))
    assert b.getpixel((0, 0))[:2] == (240, 10) and b.size == (370 - 240, 200 - 10)
    assert b.getextrema()[2] == (200, 200)


def test_chu_the_thu_tu_uu_tien():
    assert drama.chu_the(SH[1], LT) == "Hattie"                         # người nói, có trong khung
    assert drama.chu_the(dict(SH[1], huong="nia"), LT) == "Nia"         # người dựng chọn thắng, giữ chữ co_mat
    assert drama.chu_the(dict(SH[1], huong="Gloria"), LT) == "Hattie"   # `huong` ngoài khung: bỏ qua
    assert drama.chu_the(dict(SH[2], cau=[0]), LT) == "Nia"             # người nói ngoài khung: người duy nhất
    assert drama.chu_the(SH[0], LT) == ""                               # hai người, không ai nói
    assert drama.chu_the({"co_mat": []}, LT) == ""


# Shot qua vai thật của DM002 C1 (29/10): chữ `t` do Breakdown chép từ `Hình:`. Trước khi sửa,
# 8/13 shot qua vai chọn trúng người TIỀN CẢNH (người nói quay lưng) hoặc rỗng (shot im → app gửi
# nguyên ảnh dàn cảnh, P004 shot 4: Evelyn bị kéo ra sát Hattie).
def _qv(t: str, co_mat: list[str], cau=(), **them) -> dict:
    return dict({"co": "MS", "goc": "ots", "cd": "static", "t": t, "co_mat": co_mat, "cau": list(cau)}, **them)


def _lt(*ten: str) -> list[dict]:
    return drama.loi_thoai("\n".join(f'Thoại: {n}: "Line {i}."' for i, n in enumerate(ten)))


QUA_VAI_DM2 = [  # (sid, shot, lt, người máy phải hướng tới)
    ("s56840b", _qv("Qua vai Evelyn ở tiền cảnh, máy nhìn Hattie; Evelyn nghiêng đầu cười thương hại.",
                    ["Hattie", "Evelyn"]), [], "Hattie"),
    ("sbf3a4f", _qv("Qua vai Brooke, Hattie ngồi bên trái khung, bàn tay trái xoa thái dương, mặt nhăn nhẹ vì đau đầu.",
                    ["Hattie", "Brooke"]), [], "Hattie"),
    ("sb956d7", _qv("Qua vai Nia bên trái khung, tay phải Brooke từ bên phải chộp lấy mấy tờ tiền nhàu khỏi mặt bàn "
                    "trải khăn trắng.", ["Brooke", "Nia"]), [], "Brooke"),
    ("s34b697", _qv("Qua vai Nia nhìn về Hattie, Nia đặt hộp thuốc huyết áp vào tay phải Hattie, Hattie khẽ gật đầu "
                    "nhận.", ["Nia", "Hattie"], [0]), _lt("Nia"), "Hattie"),
    ("s7a1cbc", _qv("Qua vai Brooke, khung đổ xuống phía Nia ở dưới; Brooke buông câu lạnh lùng gạn hỏi, Nia ngẩng "
                    "lên đón ánh nhìn và giữ nét bình thản.", ["Nia", "Brooke"], [1]), _lt("Nia", "Brooke"), "Nia"),
    ("s99c069", _qv("Qua vai Julian ở tiền cảnh bên trái khung, nhìn xuống Brooke đứng bên phải, mặt tái mét.",
                    ["Julian", "Brooke"], [0]), _lt("Julian"), "Brooke"),
    ("sd57079", _qv("Qua vai Nia nhìn về phía Tasha; Tasha nhổm lên, mắt sáng, vẫy tay phải gọi cô lại; Nia đáp lại "
                    "với vẻ lo lắng.", ["Nia", "Tasha"], [1]), _lt("Tasha", "Nia"), "Tasha"),
    # đang đúng, phải giữ: ba người (người nói ở xa) và người nói ở xa
    ("sdb4ab3", _qv("Trung qua vai Brooke ở tiền cảnh, Hattie đứng bên trái khung, Nia cúi nửa người, tay phải rút mấy "
                    "tờ tiền lẻ nhàu từ túi tạp dề.", ["Nia", "Hattie", "Brooke"], [0]), _lt("Nia"), "Nia"),
    ("sd104eb", _qv("Qua vai Brooke nhìn xuống, Hattie ngẩng lên nói chậm.", ["Hattie", "Brooke"], [0]),
     _lt("Hattie"), "Hattie"),
]


def test_chu_the_qua_vai_bo_nguoi_tien_canh_dm002():
    sai = [(sid, drama.chu_the(s, lt), dung) for sid, s, lt, dung in QUA_VAI_DM2 if drama.chu_the(s, lt) != dung]
    assert sai == []
    s = QUA_VAI_DM2[0][1]
    assert drama.chu_the(dict(s, huong="evelyn"), []) == "Evelyn"      # người dựng chọn vẫn thắng
    assert drama.chu_the(dict(s, goc="eye"), []) == ""                 # không qua vai: luật cũ
    # qua vai chỉ có người tiền cảnh trong khung (sda3228 nhìn ra cửa kính): không bịa chủ thể
    assert drama.chu_the(_qv("Qua vai Brooke ở tiền cảnh, nhìn ra cánh cửa kính phía sau.", ["Brooke"]), []) == ""
    assert drama.nguoi_tien_canh(QUA_VAI_DM2[7][1]) == "Brooke"
    assert drama.nguoi_tien_canh(_qv("Qua vai Gloria, máy nhìn Nia.", ["Nia"])) == ""   # X ngoài khung
    assert drama.nguoi_tien_canh(SH[1]) == ""                          # P031 chưa có `t`: luật cũ (người nói)


def test_nhac_qua_vai_khi_chua_ro_may_huong_toi():
    assert drama.nhac_qua_vai(_qv("Qua vai Brooke ở tiền cảnh, nhìn ra cánh cửa kính phía sau.", ["Brooke"]), [])
    assert drama.nhac_qua_vai(SH[1], LT)                               # không đọc được "Qua vai X"
    assert drama.nhac_qua_vai(QUA_VAI_DM2[0][1], []) == []
    assert drama.nhac_qua_vai(dict(SH[1], huong="Hattie"), LT) == []   # người dựng đã chọn
    assert drama.nhac_qua_vai(SH[0], LT) == []                         # không qua vai


BEN_NHA_HANG = {"Hattie": "trai", "Brooke": "giua", "Evelyn": "phai"}          # DM002 C1 dòng 0
BEN_4 = {"Hattie": "trai", "Nia": "giua", "Brooke": "phai", "Evelyn": "phai"}   # DM002 C1 dòng 1


def test_nhac_khung_dinh_nguoi_ngoai_shot_qua_vai():
    """P004 shot 4 (29/10): khung mặc định của Hattie dính Brooke đứng giữa, model biến Brooke thành
    Evelyn đứng cạnh Hattie. Kéo khung Hattie x 0–0,335 thì ảnh đạt. Shot một người không nhắc:
    7/7 ảnh Hattie một mình ở DM002 vẫn sạch dù mảnh cắt dính Brooke."""
    pd = {"ben": BEN_NHA_HANG}
    s4 = QUA_VAI_DM2[0][1]
    assert drama.nhac_khung(pd, s4, []) and "Brooke" in drama.nhac_khung(pd, s4, [])[0]
    assert drama.nhac_khung(dict(pd, cat={"Hattie": [0.0, 0.34, 0.335, 0.675]}), s4, []) == []
    assert drama.nhac_khung(dict(pd, cat={"Brooke": [0.62, 0.3, 0.9, 0.7]}), s4, []) == []   # Brooke kéo sang phải
    assert drama.nhac_khung(pd, QUA_VAI_DM2[8][1], _lt("Hattie")) == []      # sd104eb: Evelyn ở xa bên phải
    assert drama.nhac_khung(pd, _qv("Cận Hattie.", ["Hattie"], goc="eye"), []) == []   # một người
    assert drama.nhac_khung({"ben": PD["ben"]}, SH[1], LT) == []             # P031 hai người
    # hai người cùng bên phải (sb956d7: máy hướng Brooke, Evelyn cũng "phai")
    assert "Evelyn" in drama.nhac_khung({"ben": BEN_4}, QUA_VAI_DM2[2][1], [])[0]


def test_anh_qua_vai_may_sau_nguoi_tien_canh_vai_phia_may():
    """P004 shot 4 (s56840b): mảnh cắt quanh Hattie, máy sau vai TRÁI Evelyn. Evelyn bên phải ảnh
    dàn cảnh, quay mặt sang trái nên tay phải chỉ ra xa máy; vai phía máy dàn cảnh là vai trái.
    Ba người (sdb4ab3): máy sau vai người tiền cảnh (Brooke), không phải người đầu `co_mat`."""
    pd = {"ben": {"Hattie": "trai", "Brooke": "giua", "Evelyn": "phai"}, "shots": [{}]}
    p = drama.prompt_anh_shot(pd, QUA_VAI_DM2[0][1], 0, "", {"Hattie": {"chu": "H."}, "Evelyn": {"chu": "E."}}, [], "")
    assert "Image 1 is a crop of the master wide shot of this scene, around Hattie." in p
    assert "just behind Evelyn's left shoulder, angled toward Hattie." in p
    assert "Hattie looks at Evelyn, toward the right of the frame, not at the camera." in p
    pd3 = {"ben": {"Hattie": "trai", "Nia": "giua", "Brooke": "phai"}, "shots": [{}]}
    s3, lt3 = QUA_VAI_DM2[7][1], QUA_VAI_DM2[7][2]
    p3 = drama.prompt_anh_shot(pd3, s3, 0, 'Thoại: Nia: "Line 0."', {}, [], "")
    assert drama.chu_the(s3, lt3) == "Nia" and "just behind Brooke's left shoulder, angled toward Nia." in p3


def test_ca_canh_chi_khi_nhieu_nguoi_khong_qua_vai():
    assert drama.ca_canh(SH[0])
    assert not drama.ca_canh(SH[1])
    assert not drama.ca_canh(SH[2])


def test_giay_shot():
    assert drama.giay_shot(SH[1], LT) == 10     # 18 từ: 18/3 + 1 = 7 > 5
    assert drama.giay_shot(SH[2], LT) == 6      # 6 từ
    assert drama.giay_shot(SH[0], LT) == 6      # im
    assert drama.giay_shot(dict(SH[2], gi="15"), LT) == 15
    assert drama.giay_shot(dict(SH[1], gi="7"), LT) == 10      # giây lạ: tự tính
    assert drama.giay_shot(dict(SH[2], gi="x"), LT) == 6


def test_nhac_lap_khi_ta_phong():
    assert drama.nhac_lap("Nia's face fills the frame, a soft blur of the sofa and window light behind her")
    assert drama.nhac_lap("Nia's face fills the frame on the left-of-center") == []
    assert drama.nhac_lap("") == []


# ───────────────────────────── prompt ảnh ─────────────────────────────────────
def test_anh_qua_vai_sat_ban_do():
    """P031 shot 2 (`ghep_dm4.py`): câu Image 1 khác — bản đo viết tay thêm
    ", the inner wall behind her" (phông đã có ở câu "Behind Hattie"). Câu vai cũng
    khác: bản đo ghi "Nia's left shoulder" là NGƯỢC hình học (Nia bên trái, nhìn sang
    phải → vai phía máy là vai phải; sửa 29/10, DM002 đo cho thấy model bỏ qua chữ vai)."""
    p = drama.prompt_anh_shot(PD, SH[1], 1, T, NGUOI, [], KH2)
    assert p == (
        "Medium close-up, over-the-shoulder shot, from behind a second person's shoulder in the foreground: Nia's "
        "shoulder and the back of her braided head fill the lower left foreground, Hattie facing the camera beyond it "
        "on the right as she leans forward from the sofa. Hattie tilts her head and leans in, eyes steady and kind "
        "behind her glasses, the faintest knowing lift at the corner of her mouth, settling into quiet certainty. "
        "Hattie looks at Nia, toward the left of the frame, not at the camera. Photorealistic film still, 16:9.\n\n"
        "Image 1 is a crop of the master wide shot of this scene: Hattie at the right end of the cream sofa. Keep this "
        f"exact room, background and light; it is the same moment. {SHEET[0]} {SHEET[1]}\n\n"
        "Camera position: on the same side of the room as the master shot, just behind Nia's right shoulder, angled "
        "toward Hattie. Behind Hattie: the slim dark wooden console with the framed botanical prints and the tall "
        f"taupe wall panel, exactly as in Image 1. No window behind Hattie. {CHO}\n\n"
        f"Nia: {CHU_N} Hattie: {CHU_H} Keep consistent: Nia wears dark blue jeans, a white t-shirt, and a worn "
        "mustard knit cardigan; Hattie wears a plain grey wool cardigan over a cream blouse, gold-rimmed glasses, and "
        "a faded canvas tote bag on her right shoulder. Exactly one Nia and one Hattie in frame, nobody else.\n\n"
        f"{LOOK}")
    assert "right side of the frame" not in p        # L6: câu `truc` không vào


def test_anh_mot_nguoi_huong_nhin_va_nguoi_ngoai_khung():
    """Shot 3/4: S bên trái nhìn phải, người kia ngoài khung bên phải, và ngược lại.
    Câu Image 1 đúng chữ bản đo; câu máy: bản đo "near Hattie's end of the sofa"."""
    p3 = drama.prompt_anh_shot(PD, SH[2], 2, T, NGUOI, [], "close-up, eye level: Nia's face fills the frame.")
    assert ("Image 1 is a crop of the master wide shot of this scene: Nia on the low wooden bench right by the "
            "floor-to-ceiling windows. Keep this exact room, background and light; it is the same moment.") in p3
    assert "Nia looks toward Hattie, just off the right edge of the frame, not at the camera." in p3
    assert ("Camera position: on the same side of the room as the master shot, near Hattie's place at the right end "
            "of the cream sofa, angled toward Nia. "
            "Behind Nia: the floor-to-ceiling windows, the sheer curtains and the hazy city, exactly as in Image 1. "
            "Hattie is off-screen to the right and does not appear. " + CHO) in p3
    assert "Exactly one Nia in frame, nobody else." in p3
    assert p3.count("Image 2") == 1 and "Image 3" not in p3
    p4 = drama.prompt_anh_shot(PD, SH[3], 3, T, NGUOI, [], "medium close-up, eye level: Hattie on the right.")
    assert "Hattie looks toward Nia, just off the left edge of the frame, not at the camera." in p4
    assert "No window behind Hattie. Nia is off-screen to the left and does not appear." in p4


def test_anh_vang_vi_tri_roi_ve_chu_chung():
    pd = {k: v for k, v in PD.items() if k != "vi_tri"}
    p = drama.prompt_anh_shot(pd, SH[2], 2, T, NGUOI, [], "close-up: Nia.")
    assert "Image 1 is a crop of the master wide shot of this scene, around Nia. Keep this exact room" in p
    assert "master shot, near Hattie, angled toward Nia." in p


def test_anh_nguoi_o_giua_nhin_ve_phia_nguoi_kia():
    pd = dict(PD, ben={"Nia": "giua", "Hattie": "trai"})
    p = drama.prompt_anh_shot(pd, SH[2], 2, T, NGUOI, [], "close-up: Nia.")
    assert "Nia looks toward Hattie, just off the left edge of the frame" in p
    # Qua vai: Hattie bên trái nhìn phải nên máy sau vai PHẢI (vai phía máy dàn cảnh);
    # Nia (giữa) nhìn về Hattie, sang trái
    q = drama.prompt_anh_shot(pd, dict(SH[1], cau=[1]), 1, T, NGUOI, [], "ots.")
    assert "just behind Hattie's right shoulder, angled toward Nia." in q
    assert "Nia looks at Hattie, toward the left of the frame" in q


def test_anh_ca_canh_dung_nguyen_anh_dan_canh():
    p = drama.prompt_anh_shot(PD, SH[0], 0, T, NGUOI, [], "medium shot, eye level: both seated.")
    assert LOI_REF["truong_doan"].format(i=1) in p
    assert "crop" not in p and "Camera position" not in p and "looks" not in p
    assert CHO in p and "Exactly one Hattie and one Nia in frame, nobody else." in p


def test_anh_thu_tu_anh_gui_tam_theo_co_mat_roi_do_vat():
    do = [{"ma": "do06", "loai": "dao_cu", "ten": "clipboard"}]
    s = dict(SH[1], co_mat=["Nia", "Gloria", "Hattie"])          # Gloria không có tấm: không có ảnh
    p = drama.prompt_anh_shot(PD, s, 1, T, NGUOI, do, KH2)
    assert f"{SHEET[0]} {SHEET[1]} {LOI_REF['dao_cu'].format(i=4)}" in p
    assert "Image 5" not in p


# ───────────────────────────── prompt video ───────────────────────────────────
def test_video_qua_vai_giong_het_ban_do():
    """P031 shot 2: video lần 4 = khuôn `ghep_dm.py` + câu hướng nhìn sau dòng mặt/thân."""
    p = drama.prompt_video_shot(PD, SH[1], 1, T, NGUOI, TIENG, [], KH2, MAY2, drama.giay_shot(SH[1], LT))
    assert p == (
        "The camera pushes in slowly and steadily toward the subject. Medium close-up, over-the-shoulder shot, from "
        "behind a second person's shoulder in the foreground: Nia's shoulder and the back of her braided head fill the "
        "lower left foreground, Hattie facing the camera beyond it on the right as she leans forward from the sofa. "
        "Continue this camera move for the full 10 seconds.\n"
        "Hattie tilts her head and leans in, eyes steady and kind behind her glasses, the faintest knowing lift at the "
        "corner of her mouth, settling into quiet certainty.\n"
        "Hattie looks at Nia, toward the left of the frame, not at the camera.\n"
        "SPEAKER: Hattie. LINE: \"I asked Marcus to send you up. You paid for my tea with your tips. Nobody does "
        "that.\"\n"
        "DELIVERY: Slow and deliberate, even spacing between phrases, a small pause after 'send you up' and again "
        "after 'with your tips', gentle weight landing on 'Nobody does that'.\n"
        "Nia: silent, lips closed.\n"
        f"{drama.IM}\n{drama.MOT}\n\n"
        f"{GIONG_H}\n"
        "Sound: a faint steady hum of the suite's climate system, the muffled distant murmur of the city far below "
        "through thick glass, the soft dead quiet of a carpeted high-floor room; faint creak of the sofa cushion as she "
        "leans.\n"
        f"Dialogue: only this LINE, spoken once, in English, by Hattie. {drama.CHOT}")


def test_video_nguoi_noi_ngoai_khung_va_shot_im():
    s = dict(SH[2], cau=[0])                   # cận Nia, Hattie nói từ ngoài khung
    p = drama.prompt_video_shot(PD, s, 2, T, NGUOI, TIENG, [], "close-up: Nia.", "The camera holds perfectly still.", 6)
    assert "Nia looks toward Hattie, just off the right edge of the frame, not at the camera.\nSPEAKER: Hattie, " \
           "standing just off frame" in p
    assert "Nia: silent, lips closed." in p
    im = drama.prompt_video_shot(PD, dict(SH[3], cau=[]), 3, T, NGUOI, TIENG, [], "mcu: Hattie.", "", 6)
    assert im.split("\n")[0] == "Mcu: Hattie. Continue this camera move for the full 6 seconds."
    assert drama.IM_CAM in im and "SPEAKER" not in im and GIONG_H not in im
    assert im.endswith(f"Sound: {NEN.rstrip('.')}; quiet room tone.\nNo dialogue in this shot. {drama.CHOT}")


def test_video_dat_ten_cho_dong_mat_khi_llm_khong_ghi():
    pd = dict(PD, shots=[dict(x) for x in PD["shots"]])
    pd["shots"][2]["mat"] = "Blinks, glances down then back up"
    p = drama.prompt_video_shot(pd, SH[2], 2, T, NGUOI, TIENG, [], "close-up: Nia.", MAY2, 6)
    assert "\nNia: blinks, glances down then back up.\nNia looks toward Hattie" in p


# ───────────────────────────── ảnh dàn cảnh ───────────────────────────────────
def test_prompt_dan_canh():
    noi = {"ma": "noi02", "loai": "boi_canh", "ten": "Suite 1801"}
    p = drama.prompt_dan_canh(PD, [NGUOI["Hattie"], NGUOI["Nia"]], noi)
    khoi = p.split("\n\n")
    assert khoi[0] == PD["dan"] + ". Photorealistic film still, 16:9."
    assert khoi[1] == " ".join([LOI_REF["boi_canh"].format(i=1)] + SHEET)
    assert khoi[2] == ("Behind Hattie: the slim dark wooden console with the framed botanical prints and the tall "
                       "taupe wall panel. No window behind Hattie. Behind Nia: the floor-to-ceiling windows, the sheer "
                       f"curtains and the hazy city. {CHO}")
    assert khoi[3] == f"Hattie: {CHU_H} Nia: {CHU_N} Exactly one Hattie and one Nia, nobody else."
    assert khoi[4] == LOOK
    # Không có nơi chốn: tấm người đánh số từ 1
    assert drama.prompt_dan_canh(PD, [NGUOI["Nia"]], None).split("\n\n")[1] == LOI_REF["nhan_vat"].format(i=1)


# ───────────────────────────── lệnh LLM ───────────────────────────────────────
def test_lenh_llm_khop_hop_dong():
    for k in ('"ben"', '"phong"', '"cho"', '"vi_tri"', '"dan"'):
        assert k in dich.LENH_DRAMA_CANH
    assert "thứ sau lưng" not in dich.LENH_DRAMA_CLIP.split("`lap`")[1].split("KHÔNG tả phông")[0]
    assert "KHÔNG tả phông" in dich.LENH_DRAMA_CLIP


def test_khung_mac_dinh_hai_nguoi_giu_hop_da_do():
    pd = {"ben": {"Nia": "trai", "Hattie": "phai"}, "hang": ["Nia", "Hattie"]}
    assert drama.khung_mac_dinh(pd, "Nia") == drama.khung_cat("trai")
    assert drama.khung_mac_dinh(pd, "Hattie") == drama.khung_cat("phai")


def test_khung_mac_dinh_bon_nguoi_chia_theo_thu_tu_trai_phai():
    """C005 thật (29/10): hộp theo `ben` cắt mất nửa Nia, hộp Hattie dính Julian. Tâm
    từng người đo trên ảnh dàn cảnh: hộp mỗi người chứa tâm mình, không chứa tâm người
    bên cạnh, nằm trong ảnh, rộng = cao (16:9 trên ảnh 16:9)."""
    tam = {"Miles": 0.085, "Nia": 0.365, "Hattie": 0.70, "Julian": 0.86}
    pd = {"ben": {"Miles": "trai", "Nia": "giua", "Hattie": "giua", "Julian": "phai"}, "hang": list(tam)}
    ten = list(tam)
    for i, n in enumerate(ten):
        x0, y0, x1, y1 = drama.khung_mac_dinh(pd, n)
        assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1 and abs((x1 - x0) - (y1 - y0)) < 1e-3
        assert x0 < tam[n] < x1, n
        for m in ten[max(i - 1, 0):i] + ten[i + 1:i + 2]:
            assert not x0 < tam[m] < x1, (n, m)


HANG_4 = ["Hattie", "Nia", "Brooke", "Evelyn"]                     # DM002 C1 dòng 1, trái → phải
TAM_4 = {"Hattie": 0.125, "Nia": 0.30, "Brooke": 0.59, "Evelyn": 0.87}   # đo trên ảnh dàn cảnh 29/10


def test_khung_bon_nguoi_dm002_dong1_va_khung_cua_cung_mot_cho():
    """Cảnh 4 người thật: khung theo `ben` của Nia ("giua" 0,30–0,70) trùm Brooke (đo ảnh 29/10). Khung theo
    `hang` chứa tâm mình, không chứa tâm người khác. `khung_cua` (nhắc) = khung app cắt thật."""
    pd = {"ben": BEN_4, "hang": HANG_4}
    assert drama.khung_cat(BEN_4["Nia"])[0] < TAM_4["Brooke"] < drama.khung_cat(BEN_4["Nia"])[2]
    for n in HANG_4:
        x0, _, x1, _ = drama.khung_cua(pd, n)
        assert drama.khung_cua(pd, n) == drama.khung_mac_dinh(pd, n)
        assert [m for m, t in TAM_4.items() if x0 < t < x1] == [n], n
    assert drama.khung_cua(dict(pd, cat={"Nia": [0.2, 0.1, 0.45, 0.5]}), "Nia") == (0.2, 0.1, 0.45, 0.5)


def test_nhac_khung_tinh_cho_dung_theo_hang():
    """sb956d7 (máy hướng Brooke, Evelyn ngoài shot): chưa có `hang` thì khung "phai" trùm Evelyn → nhắc;
    có `hang` thì khung Brooke 0,48–0,77, Evelyn ở 0,875 → không nhắc."""
    s = QUA_VAI_DM2[2][1]
    assert drama.nhac_khung({"ben": BEN_4}, s, [])
    assert drama.nhac_khung({"ben": BEN_4, "hang": HANG_4}, s, []) == []


def test_khung_mac_dinh_ten_ngoai_hang_ve_ben():
    pd = {"ben": {"Nia": "trai"}, "hang": ["A", "B", "C"]}
    assert drama.khung_mac_dinh(pd, "Nia") == drama.khung_cat("trai")
    assert '"hang"' in dich.LENH_DRAMA_CANH
