"""Drama thoại (user chốt 27/10): kịch bản hai tầng khuôn Padoma -> tập treatment.

Luật đi theo đo thật 27/10 (scratchpad drama_thu, Grok 1.5 + tấm GPT Image 2):
thoại đúng 12/12, cắt cứng 5/5 khi prompt theo khuôn [REFERENCES] … [KEEP] và
mỗi shot đúng một SPEAKER/LINE hay NO LINE. Python ghép khuôn và CHÈN NGUYÊN
VĂN câu thoại của kịch bản; LLM chỉ viết ý, cú máy, cách nói.
"""

from __future__ import annotations

import json

import pytest

from autoedit.treatment import drama

KICH_BAN = """# Chiếc hộp nhẫn rỗng
Loại phim: drama_thoai
Thể loại: drama-da-den · Độ dài: 20 phút · Tỉ lệ: 16:9
Trả tựa ở: N02

## Nhân vật và bối cảnh
| Tên (dùng ở Khung) | Vai | Tuổi, ngoại hình một câu | Giọng (tuổi, độ trầm, chất giọng) |
|---|---|---|---|
| Tasha (she) | người chăm bệnh | 28 tuổi, tóc tết dài, áo len đỏ rượu | nữ 28 tuổi, trung, trong, hơi khàn, giọng Chicago |
| Marcus (he) | con trai bà Ruth | 45 tuổi, vest xám | nam 45 tuổi, trầm, gọn, giọng Atlanta |
### Nơi
| Nơi (tên dùng ở tiêu đề cảnh) | Một câu tả |
|---|---|
| phòng VIP bệnh viện | phòng bệnh riêng, giường trắng, cửa sổ lớn bên hông |
| bếp nhà Tasha | bếp nhỏ, đèn trần vàng |

## Cụm cố định
| Mã | Tên | Cụm tiếng Anh (nguyên văn) | Ghi chú |
|---|---|---|---|
| NV01 | Tasha (she) | Beautiful Black woman about 28, long dark box braids tied back, burgundy knit cardigan over a plain black top | N01–N02 |
| NV01 | Tasha (she), dạng 2 | Beautiful Black woman about 28, long dark box braids loose, grey hoodie | N03 |
| NV02 | Marcus (he) | Black man about 45, short fade haircut, trimmed beard greying at the chin, charcoal grey suit, white shirt, no tie | |

# Phần 1 · Hộp nhẫn rỗng · 1 phút

## C001 · phòng VIP bệnh viện · sáng · N01
Có mặt: Tasha, Marcus

### P001 · Marcus buộc tội Tasha
Máy: Grok 15s
Khung: Tasha, Marcus
Hình: shot 1 qua vai Tasha, Marcus bên phải khung giơ hộp nhẫn rỗng. Shot 2 qua vai Marcus, Tasha bên trái khung, mắt mở to.
Thoại: Marcus (gằn, buộc tội): "Only you were in this room."
Thoại: Tasha (sững rồi nhỏ mà chắc): "I went for water. Five minutes."

### P002 · Tasha nghĩ
Máy: Grok 15s
Khung: Tasha
Hình: cận Tasha, môi khép, nuốt khan; máy đẩy vào chậm.
Lời nghĩ: Tasha: "He already decided."

## Ghi chú nối
Sáng hôm sau.

# Phần 2 · Về nhà · 1 phút

## C002 · bếp nhà Tasha · tối · N03
Có mặt: Tasha, Marcus

### P003 · Marcus gọi tới
Máy: Grok 15s
Khung: Tasha
Hình: trung Tasha đứng bên bàn bếp nghe điện thoại, góc thấp.
Thoại: Marcus (lạnh): "Bring it back tonight."
"""


def test_kich_ban_mau_dung_khuon_padoma():
    """Mẫu test phải qua chính máy kiểm của Padoma — mẫu sai là test xanh giả."""
    from autoedit.treatment import kiem_drama
    loi, _, phim = kiem_drama.kiem(KICH_BAN)
    assert not loi, loi
    assert phim["grok"]


# ═══════ tách tập: phần -> chương Cn, cảnh -> dòng, clip -> cảnh treatment ═══════
def test_tach_tap_phan_thanh_chuong_canh_thanh_dong_clip_thanh_canh():
    r = drama.tach_tap(KICH_BAN)
    assert not r["loi"]
    assert [c["ma"] for c in r["chuong"]] == ["C1", "C2"]
    c1 = r["chuong"][0]
    assert c1["outline"].startswith("Phần 1 · Hộp nhẫn rỗng")
    assert "Sáng hôm sau." in c1["outline"]
    d = c1["dong"][0]
    assert d["en"] == "C001 · phòng VIP bệnh viện · sáng · N01"
    assert d["vi"] == "Có mặt: Tasha, Marcus"
    p1, p2 = d["canh"]
    assert p1["pm"] == "P001" and p1["gi"] == "15"
    assert p1["t"].splitlines()[0] == "Marcus buộc tội Tasha"
    assert 'Thoại: Marcus (gằn, buộc tội): "Only you were in this room."' in p1["t"]
    assert "Máy:" not in p1["t"], "độ dài là trường riêng `gi`, đổi trên treatment"
    # ảnh gửi đi: nơi chốn trước, rồi nhân vật theo Khung (khuôn đo 27/10)
    assert p1["ts"] == ["noi01", "nv01", "nv02"]
    assert p2["ts"] == ["noi01", "nv01"]


def test_bo_do_theo_moc_cua_canh():
    """Cụm `dạng 2` ghi mốc N03: cảnh N03 phải gửi tấm của bộ đồ đó."""
    r = drama.tach_tap(KICH_BAN)
    p3 = r["chuong"][1]["dong"][0]["canh"][0]
    assert p3["ts"] == ["noi02", "nv01_d2"]


def test_so_tai_san_tu_kich_ban():
    so = {x["ma"]: x for x in drama.tach_tap(KICH_BAN)["so"]}
    t = so["nv01"]
    assert t["loai"] == "nhan_vat" and t["ten"] == "Tasha"
    assert t["chu"].startswith("Beautiful Black woman about 28, long dark box braids tied back")
    assert t["tieng"].startswith("nữ 28 tuổi")
    assert so["nv01_d2"]["ten"] == "Tasha · dạng 2" and "grey hoodie" in so["nv01_d2"]["chu"]
    assert so["nv01_d2"]["tieng"] == t["tieng"], "đổi đồ không đổi giọng"
    n = so["noi01"]
    assert n["loai"] == "boi_canh" and n["ten"] == "phòng VIP bệnh viện"
    assert n["yc"] == "phòng bệnh riêng, giường trắng, cửa sổ lớn bên hông"


def test_kich_ban_loi_thi_tra_loi_khong_tach():
    hong = KICH_BAN.replace("Máy: Grok 15s\nKhung: Tasha\nHình: cận", "Máy: Grok 20s\nKhung: Tasha\nHình: cận")
    r = drama.tach_tap(hong)
    assert r["loi"] and any("P002" in x for x in r["loi"])
    assert r["chuong"] == []


def test_nhan_vat_o_khung_khong_co_trong_cum_la_loi():
    hong = KICH_BAN.replace("Có mặt: Tasha, Marcus\n\n### P003", "Có mặt: Tasha, Marcus, Dee\n\n### P003") \
                   .replace("Khung: Tasha\nHình: trung", "Khung: Tasha, Dee\nHình: trung")
    r = drama.tach_tap(hong)
    assert any("Dee" in x for x in r["loi"])


# ═══════ dán lại: giữ mã/video/độ dài đã chọn theo mã clip P ═══════════════════
def test_dan_lai_giu_id_video_do_dai_va_asset_tay():
    r = drama.tach_tap(KICH_BAN)
    cu = r["chuong"][0]["dong"]
    cu[0]["canh"][0].update(id="cabc", gi="10", vid="task1", pvt="tay", ts=["noi01", "nv01", "nv02", "hop_nhan"])
    moi = drama.tach_tap(KICH_BAN.replace("Five minutes.", "Five minutes, sir."))["chuong"][0]["dong"]
    ra = drama.ghep_lai({"C1": cu}, moi, {"noi01", "noi02", "nv01", "nv01_d2", "nv02"})
    c = ra[0]["canh"][0]
    assert c["id"] == "cabc" and c["gi"] == "10" and c["vid"] == "task1" and c["pvt"] == "tay"
    assert "Five minutes, sir." in c["t"]
    assert c["v"] == "1", "chữ đổi thì tăng v — tab cũ tự lưu không đè được chữ mới"
    assert c["ts"] == ["noi01", "nv01", "nv02", "hop_nhan"], "đồ vật người dựng gán tay phải còn"


# ═══════ thoại trong chữ clip + trần từ theo độ dài đã chọn ═══════════════════
def test_loi_thoai_doc_tu_chu_clip():
    t = drama.tach_tap(KICH_BAN)["chuong"][0]["dong"][0]["canh"]
    ds = drama.loi_thoai(t[0]["t"])
    assert [(x["ten"], x["cau"], x["nghi"]) for x in ds] == [
        ("Marcus", "Only you were in this room.", False),
        ("Tasha", "I went for water. Five minutes.", False)]
    assert drama.loi_thoai(t[1]["t"])[0] == {"ten": "Tasha", "cach": "", "cau": "He already decided.", "nghi": True}


def test_nhac_tran_tu_theo_giay():
    t = drama.tach_tap(KICH_BAN)["chuong"][0]["dong"][0]["canh"][0]["t"]
    assert drama.so_tu(t) == 12  # 6 + 6
    assert drama.nhac_clip(t, 15) == []
    assert drama.nhac_clip(t, 6) == [], "12 từ <= 18"
    dai = t + '\nThoại: Tasha (run): "' + " ".join(["word"] * 10) + '"'
    assert any("22 từ" in x and "tối đa 18" in x for x in drama.nhac_clip(dai, 6))


# ═══════ chia giây shot: PYTHON đo, không để LLM viết mốc ═════════════════════
def test_chia_giay_lien_tu_0_toi_het_shot_noi_dai_hon():
    moc = drama.chia_giay([6, 13, 3, 3], 15)
    assert moc[0][0] == 0 and moc[-1][1] == 15
    assert all(a < b for a, b in moc) and all(moc[i][1] == moc[i + 1][0] for i in range(3))
    dai = [b - a for a, b in moc]
    assert dai[1] == max(dai), "shot 13 từ phải dài nhất"
    assert all(x >= 2.5 for x in dai)
    assert drama.chia_giay([0], 10) == [(0, 10)]


# ═══════ ghép prompt khuôn Grok ════════════════════════════════════════════════
ANH = [{"loai": "boi_canh", "ten": "phòng VIP bệnh viện", "chu": "a private VIP hospital room"},
       {"loai": "nhan_vat", "ten": "Tasha", "chu": "Black woman about 28."},
       {"loai": "nhan_vat", "ten": "Marcus", "chu": "Black man about 45."},
       {"loai": "dao_cu", "ten": "hộp nhẫn", "chu": "a small red velvet ring box"}]
TIENG = {"Tasha": "Tasha's voice: a woman of about 28, medium pitch.",
         "Marcus": "Marcus's voice: a man of about 45, low pitch."}
PD = {"look": "Soft grey window light.", "truc": "Tasha always frame left, Marcus always frame right.",
      "nen": "quiet hum of air vents", "y": "The audience must feel the injustice.",
      "size": "SIZE: Tasha is a grown woman of ordinary adult height.",
      "giu": "Tasha in the burgundy cardigan; Marcus in the charcoal suit",
      "shots": [{"khung": "over-the-shoulder shot from behind Tasha, Marcus in focus frame right", "cau": 0,
                 "cach": "low and hard", "mat": "he steps close, jaw tight", "am": "a footstep"},
                {"khung": "close-up of Tasha frame left", "cau": 1, "cach": "stunned, then firm",
                 "mat": "her eyes wide", "am": ""}]}


def _p1():
    return drama.tach_tap(KICH_BAN)["chuong"][0]["dong"][0]["canh"][0]["t"]


def test_prompt_khuon_grok_du_khoi_dung_thu_tu():
    p = drama.prompt_clip(PD, _p1(), ANH, TIENG, 15)
    khoi = ["[REFERENCES]", "[SCENE AND INTENT]", "[LOOK]", "[SHOTS]", "[SOUND]", "[KEEP]"]
    assert [p.index(k) for k in khoi] == sorted(p.index(k) for k in khoi)
    assert "Image 1 shows the location" in p and "it is not the first frame" in p
    assert "Image 2 is the character sheet of Tasha, Image 3 the character sheet of Marcus" in p
    assert "Image 4 shows a small red velvet ring box" in p
    assert "There is exactly one Tasha and one Marcus in this scene. Nobody else appears." in p
    assert "Hard cuts only between shots, no dissolves" in p


def test_prompt_cau_thoai_NGUYEN_VAN_tu_kich_ban_va_nguoi_kia_im():
    p = drama.prompt_clip(PD, _p1(), ANH, TIENG, 15)
    assert 'SPEAKER: Marcus. LINE: "Only you were in this room."' in p
    assert 'SPEAKER: Tasha. LINE: "I went for water. Five minutes."' in p
    assert "Tasha: silent, lips closed." in p and "Marcus: silent, lips closed." in p
    assert "Shot 1 (0-" in p and "-15s)" in p
    assert "Marcus's voice: a man of about 45" in p and "Tasha's voice" in p


def test_doi_giay_thi_moc_shot_doi_khong_can_LLM():
    p10 = drama.prompt_clip(PD, _p1(), ANH, TIENG, 10)
    assert "-10s)" in p10 and "-15s)" not in p10


def test_loi_nghi_va_nguoi_noi_ngoai_khung():
    t2 = drama.tach_tap(KICH_BAN)["chuong"][0]["dong"][0]["canh"][1]["t"]
    pd = dict(PD, shots=[{"khung": "close-up of Tasha", "cau": 0, "cach": "quiet", "mat": "she swallows", "am": ""}])
    p = drama.prompt_clip(pd, t2, ANH[:2], TIENG, 15)
    assert "Tasha's inner voice, voice-over, Tasha's lips do not move" in p
    assert "No narration, no melodic music" in p and "no voice-over" not in p
    t3 = drama.tach_tap(KICH_BAN)["chuong"][1]["dong"][0]["canh"][0]["t"]
    p = drama.prompt_clip(pd, t3, ANH[:2], TIENG, 15)
    assert "SPEAKER: Marcus, standing just off frame" in p and "not a voice-over" in p
    assert "Tasha: silent, lips closed." in p


def test_kiem_pd_bat_LLM_chia_thoai_sai():
    t = _p1()
    assert drama.kiem_pd(PD, t) == []
    thieu = dict(PD, shots=PD["shots"][:1])
    assert any("thiếu" in x for x in drama.kiem_pd(thieu, t))
    dao = dict(PD, shots=[dict(PD["shots"][0], cau=1), dict(PD["shots"][1], cau=0)])
    assert drama.kiem_pd(dao, t)
    gop_sai = dict(PD, shots=[dict(PD["shots"][0], cau=[0, 1])])
    assert any("hai người" in x for x in drama.kiem_pd(gop_sai, t))
    assert any("dolly zoom" in x for x in drama.kiem_pd(
        dict(PD, shots=[dict(PD["shots"][0], khung="a dolly zoom on Marcus"), PD["shots"][1]]), t))


def test_nhac_ten_nguyen_chu_khong_phan_biet_hoa_thuong():
    assert drama.nhac_ten("Ruth's chair stays empty; derek on the right.", ["Ruth", "Nia", "Derek"]) == ["Ruth", "Derek"]
    assert drama.nhac_ten("Truthful grey light.", ["Ruth"]) == []


def test_tieng_anh_hay_viet():
    assert drama.la_tieng_viet("nữ 28 tuổi, trung") and not drama.la_tieng_viet("Tasha's voice: a woman")


def test_prompt_noi_cho_do_vat_chi_cau_dau_va_cum_nhan_dang_cham_cau():
    """Chạy thật 28/10: mô tả nơi chốn 100+ từ (kèm "Light:" trùng [LOOK]) chèn
    nguyên vào [REFERENCES], và hai cụm nhận dạng dính nhau "…left eye Marcus:"."""
    anh = [{"loai": "boi_canh", "ten": "phòng", "chu": "A private hospital room with a bed. Light: grey daylight."},
           {"loai": "nhan_vat", "ten": "Tasha", "chu": "Black woman about 28, a mole under her left eye"},
           {"loai": "nhan_vat", "ten": "Marcus", "chu": "Black man about 45"},
           {"loai": "dao_cu", "ten": "hộp", "chu": "A small ring box. The interior is empty."}]
    p = drama.prompt_clip(PD, _p1(), anh, TIENG, 15)
    assert "Image 1 shows the location, a private hospital room with a bed: use it" in p
    assert "grey daylight" not in p.split("[SCENE AND INTENT]")[0]
    assert "Tasha: Black woman about 28, a mole under her left eye. Marcus: Black man about 45." in p
    assert "Image 4 shows a small ring box: use this reference" in p


def test_chia_giay_shot_im_khong_bi_ep_duoi_2_5_giay():
    """Chạy thật 28/10, P003: câu 19 từ + shot im + câu 15 từ trong 15 giây ra shot
    im 2 giây (7-9s) — co giãn tỉ lệ ép luôn mức tối thiểu."""
    for tu, giay in (([19, 0, 15], 15), ([6, 13, 3, 3], 15), ([0, 0, 0], 10), ([30], 10), ([5, 0], 6)):
        moc = drama.chia_giay(tu, giay)
        dai = [b - a for a, b in moc]
        assert moc[0][0] == 0 and moc[-1][1] == giay and all(moc[i][1] == moc[i + 1][0] for i in range(len(moc) - 1))
        assert all(x >= 2.5 for x in dai), (tu, giay, moc)
        assert all((x * 2) % 1 == 0 for x in dai), "mốc tròn 0,5 giây"
    assert len(drama.chia_giay([3, 3, 3], 6)) == 3, "không đủ chỗ thì vẫn chia (trang đã nhắc)"
