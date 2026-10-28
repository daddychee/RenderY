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

from pathlib import Path

MODEL_ANH = "gpt-image-2"
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


def _cau(chu: str) -> str:
    s = (chu or "").strip()
    return s if s.endswith((".", "!", "?")) else s + "."


def pr_mau(loai: str, chu: str) -> str:
    """Prompt ảnh ĐẦU CHUỖI của một tài sản (người: ảnh cận mặt)."""
    mau = {"nhan_vat": CAN_MAT, "dao_cu": DO_VAT, "boi_canh": NOI_GOC}.get(loai)
    return mau.format(mo_ta=_cau(chu)) if mau and (chu or "").strip() else ""


def toan_than(chu: str) -> str:
    return TOAN_THAN.format(mo_ta=_cau(chu))


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
