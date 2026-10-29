r"""Luật tài sản khuôn Padoma (user chốt 27/10: "áp dụng cho cả 2" — narration
lẫn drama, chỉ tập MỚI, tập cũ giữ đường cũ). Hàm thuần + Pillow.

Câu ảnh chép NGUYÊN từ Padoma `docs/prompting/nguyen-tac/L2-phim-nhan-vat.md`
mục 7 và `khoi-anh-sang-phim.md` "Khuôn câu ảnh" (đã chạy đạt born-a-wolf
23/09). Đo phía mình 27/10: tấm GPT Image 2 theo khuôn này cho clip Grok cắt
cứng 5/5, Nano Banana Pro chồng mờ 2/2 → user chốt GPT Image 2.

  Người   : CẬN MẶT 1:1 -> TOÀN THÂN 9:16 (sửa từ ảnh cận) -> tấm gộp 4:3 có dải chữ
  Đồ vật  : nền trắng 1:1
  Nơi chốn: ảnh GỐC 16:9, không người
"""

from __future__ import annotations

import math
import re
from pathlib import Path

# Model vẽ asset khi CẢ tập lẫn General chưa chọn (user báo 28/10: đổi model ở General
# mà tool vẫn GPT2 — ghi cứng là lỗi; app đọc tập > General > hằng này).
MODEL_ANH = "gpt-image-2"
MODEL_DU_PHONG = "GEM_PIX_2"      # Nano Banana Pro: Padoma `bo_anh.MODEL_DU_PHONG` khi GPT Image 2 bảo trì
# Credit một ảnh Seedvis (Padoma TOM-TAT-API 19/10: tạo mới 4, sửa từ ảnh 5) và giây một
# ảnh GPT (đo 28/10: tấm nhân vật 69–89 s cho hai ảnh, ảnh khung đầu 62–129 s).
GIA_ANH, GIA_SUA, GIAY_ANH = 4, 5, 50
LUONG = 3                         # tài khoản Seedvis 4 việc cùng lúc: chừa một cho nút lẻ / video
# Padoma L2-phim-nhan-vat.md mục 7 "PHIÊN BẢN NGƯỜI": bộ đồ phụ sửa từ ảnh cận của bản gốc.
PHIEN_BAN = ("Same person as in the image, the same identity and face; only what the description "
             "below says is different.")
DAI = "FICTIONAL CHARACTER SHEET - AI GENERATED - NOT A REAL PERSON"
NEN_XAM = ("Plain mid-grey studio background, soft even light, no harsh shadows. Shot on a 50 mm lens at f/2.8, fine "
           "digital noise in the shadows, natural colour. No text, no labels, no watermark, no logo, not a cartoon, "
           "not CGI, not glossy, no beauty retouching.")
CAN_MAT = ("Realistic photograph, a very large sharp close-up portrait of the face, front view turned slightly to one "
           "side, neutral expression. The person: {mo_ta} " + NEN_XAM)
TOAN_THAN = ("Same person as in the image: the same face, hair, skin and blemishes. Realistic full-length photograph of "
             "this person standing straight facing the camera, arms relaxed at the sides, the whole body from the top "
             "of the head to the feet in frame, the face clearly visible. The person: {mo_ta} " + NEN_XAM)
DO_VAT = ("Product photograph of a real handmade object: {mo_ta} Plain pure white seamless background, soft even light. "
          "Shot on a 50 mm lens at f/2.8, natural colour. No text or letters except the exact words given in quotes in "
          "the description, copied letter for letter; no other names, no labels, no watermark, no logo, not a cartoon, "
          "not CGI.")
KHONG_TROI = "No orange, pink or purple anywhere in the sky or on the horizon, the sun is never visible."
NOI_GOC = ("Cinematic film still from a feature film, a wide shot: {mo_ta} " + KHONG_TROI + " No people, no animals, "
           "no text, no watermark, not a cartoon, not CGI. Shot on a real camera in a real place, fine film grain, "
           "ordinary imperfect composition.")
TI_LE = {"nhan_vat": "1:1", "dao_cu": "1:1", "boi_canh": "16:9"}
# Prompt ẢNH CẢNH của tập khuôn 2: mỗi ảnh tham chiếu đánh số kèm lời dặn lấy gì,
# bỏ gì (Padoma: "mỗi ảnh ghi lấy gì, bỏ gì"). Tấm nhân vật có dải chữ và một người
# chụp hai lần — không dặn thì model vẽ chữ hay đẻ hai người. Trang chép Y HỆT
# (`LOI_REF` trong treatment.html), test so từng chữ.
LOI_REF = {
    "truong_doan": "Image {i} is the master frame of this sequence: keep its space, layout and light.",
    "nhan_vat": ("Image {i} is a character sheet, one person shown twice (face close-up and full length): take the "
                 "face, hair, body and clothing; ignore the caption band and the grey background."),
    "dao_cu": "Image {i} shows an object: take its shape, material and colour; ignore the white background.",
    "boi_canh": "Image {i} shows the location: take the place and its light.",
}
# Đồ vật có ẢNH người (thẻ có ảnh, báo đăng ảnh, khung ảnh — user báo 29/10 DM002: thẻ của
# Richard da đen vẽ ra người da trắng): mô tả gọi TÊN nhân vật, máy gửi kèm ảnh cận mặt
# người đó. Chữ IN trên đồ nằm trong ngoặc kép ("RICHARD", 'NIA') nên không tính.
ANH_NGUOI = ("Image {i} is the face of {ten}: every photo or portrait of {ten} on the object shows exactly this "
             "person, the same face, skin tone, hair and age.")
_NGOAC = re.compile(r'"[^"]*"|(?<![A-Za-z])\'[^\']*\'(?![A-Za-z])')


def _cau(chu: str) -> str:
    s = (chu or "").strip()
    return s if s.endswith((".", "!", "?")) else s + "."


def pr_mau(loai: str, chu: str) -> str:
    """Prompt ảnh ĐẦU CHUỖI của một tài sản (người: ảnh cận mặt)."""
    mau = {"nhan_vat": CAN_MAT, "dao_cu": DO_VAT, "boi_canh": NOI_GOC}.get(loai)
    return mau.format(mo_ta=_cau(chu)) if mau and (chu or "").strip() else ""


def toan_than(chu: str) -> str:
    return TOAN_THAN.format(mo_ta=_cau(chu))


def goc_cua(ma: str) -> str:
    """`nv01_d2` (bộ đồ dạng 2, `drama.nhan_vat`) -> "nv01"; bản gốc -> ""."""
    m = re.fullmatch(r"(.+)_d\d+", ma or "")
    return m.group(1) if m else ""


def thieu_mo_ta(x: dict) -> bool:
    """Asset vẽ theo mô tả tiếng Anh mà chưa có: chữ Việt hay trống."""
    from autoedit.treatment.drama import la_tieng_viet

    chu = (x.get("chu") or "").strip()
    return not chu or la_tieng_viet(chu)


def ten_nhan_vat(so: list[dict]) -> list[str]:
    """Tên các nhân vật BẢN GỐC trong sổ (bộ đồ phụ cùng mặt, không tính riêng)."""
    return [x["ten"].split(" · ")[0].strip() for x in so if x["loai"] == "nhan_vat" and not goc_cua(x["ma"])]


def nguoi_trong_chu(chu: str, ten: list[str]) -> list[str]:
    """Tên trong `ten` mà `chu` gọi tới NGOÀI ngoặc kép, đúng chữ hoa, trọn tên, theo thứ tự
    xuất hiện."""
    s = _NGOAC.sub(" ", chu or "")
    co = [(m.start(), t) for t in ten for m in [re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", s)] if t and m]
    return [t for _, t in sorted(co)]


def nguoi_cua_do(so: list[dict], chu: str) -> list[dict]:
    """Mục sổ của những nhân vật mà mô tả đồ vật gọi tên — ảnh cận mặt của họ đi kèm lúc vẽ."""
    goc = {x["ten"].split(" · ")[0].strip(): x for x in so if x["loai"] == "nhan_vat" and not goc_cua(x["ma"])}
    return [goc[t] for t in nguoi_trong_chu(chu, list(goc))]


def ap_ra(n: int, ra) -> tuple[list[list[int]], dict[int, str]]:
    """Kết quả LLM rà đồ vật cả tập, đã kiểm: nhóm gộp (chỉ số trong [0, n), mỗi chỉ số một
    lần, nhóm từ 2 mục, mục đầu giữ tên và mô tả) và mô tả sửa (tiếng Anh, theo chỉ số)."""
    from autoedit.treatment.drama import la_tieng_viet

    def so(i):
        return int(i) if (isinstance(i, int) and not isinstance(i, bool)) or str(i).isdigit() else -1

    ra = ra if isinstance(ra, dict) else {}
    nhom, dung = [], set()
    for g in ra.get("nhom") or []:
        g = [i for i in dict.fromkeys(so(i) for i in (g if isinstance(g, list) else [])) if 0 <= i < n and i not in dung]
        if len(g) >= 2:
            nhom.append(g)
            dung.update(g)
    sua = {}
    for k, v in (ra.get("sua") if isinstance(ra.get("sua"), dict) else {}).items():
        v = str(v or "").strip()
        if 0 <= so(k) < n and v and not la_tieng_viet(v):
            sua[so(k)] = v
    return nhom, sua


def gia_anh(model: str, sua: bool) -> int:
    """GPT Image: 4 tạo mới, 5 sửa từ ảnh; Nano Banana: 4 cả hai (Padoma TOM-TAT-API)."""
    return GIA_SUA if sua and (model or "").startswith("gpt-image") else GIA_ANH


def ke_hoach(so: list[dict], co_anh: set[str], tim_do_vat: bool, model: str = MODEL_ANH,
             du_phong: str = MODEL_DU_PHONG) -> dict:
    """Việc của nút "Gen toàn bộ asset" trên sổ hiện tại. Đồ vật LLM sắp tìm thì chưa
    tính credit (chưa biết số)."""
    ma_so = {x["ma"] for x in so}
    ve = [x for x in so if x["loai"] in TI_LE and x["ma"] not in co_anh]
    phu = [x for x in ve if x["loai"] == "nhan_vat" and goc_cua(x["ma"]) in ma_so]
    goc = [x for x in ve if x["loai"] == "nhan_vat" and x not in phu]
    khac = [x for x in ve if x["loai"] != "nhan_vat"]
    co_nguoi = sum(1 for x in khac if x["loai"] == "dao_cu" and nguoi_cua_do(so, x.get("chu") or ""))
    anh = 2 * len(goc) + 2 * len(phu) + len(khac)

    def credit(m):     # đồ vật có ảnh người vẽ kèm ảnh mặt: giá ảnh SỬA
        return ((gia_anh(m, False) + gia_anh(m, True)) * len(goc) + 2 * gia_anh(m, True) * len(phu)
                + gia_anh(m, False) * (len(khac) - co_nguoi) + gia_anh(m, True) * co_nguoi)

    return {"do_vat": tim_do_vat,
            "mo_ta": sum(1 for x in so if x["loai"] in TI_LE and thieu_mo_ta(x) and (x.get("yc") or "").strip()),
            "nhan_vat": len(goc), "phu": len(phu),
            "noi": sum(1 for x in khac if x["loai"] == "boi_canh"),
            "dao_cu": sum(1 for x in khac if x["loai"] == "dao_cu"),
            "anh": anh, "credit": credit(model), "credit_du_phong": credit(du_phong),
            "phut": math.ceil(anh * GIAY_ANH / (60 * LUONG)) + (2 if tim_do_vat else 0)}


def ghep_tam(can: Path, toan: Path, dich: Path) -> Path:
    """Tấm gộp: cận trái, toàn thân phải, cao 1024, khổ 4:3, dải chữ ở đáy
    (Padoma `bo_anh._ghep_file`; tấm lệch 4:3 thì sửa ảnh về sau bị ép ngang)."""
    from PIL import Image, ImageDraw, ImageFont

    h, dai = 1024, 60
    hs = [Image.open(p).convert("RGB") for p in (can, toan)]
    hs = [x.resize((round(x.width * h / x.height), h)) for x in hs]
    rong = sum(x.width for x in hs)
    dai = max(dai, round(rong * 3 / 4) - h)
    tam = Image.new("RGB", (max(rong, round((h + dai) * 4 / 3)), h + dai), (20, 20, 20))
    x = (tam.width - rong) // 2
    for a in hs:
        tam.paste(a, (x, 0))
        x += a.width
    ve = ImageDraw.Draw(tam)
    try:
        font = ImageFont.truetype("arialbd.ttf", 30)
    except OSError:
        font = ImageFont.load_default(size=30)
    ve.text(((tam.width - ve.textlength(DAI, font=font)) / 2, h + (dai - 34) // 2), DAI,
            fill=(235, 235, 235), font=font)
    dich = Path(dich)
    dich.parent.mkdir(parents=True, exist_ok=True)
    tam.save(dich)
    return dich
