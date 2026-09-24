r"""Thao tác DÒNG của bàn kịch bản — hàm thuần, không DB, không mạng.

Đơn vị là DÒNG do người tự xuống, không phải CÂU tách bằng dấu chấm (user chốt
15/09): chỗ xuống dòng là chỗ người đọc voice sẽ nghỉ, tức là nhịp của video.
Nên ở đây không có thư viện tách câu nào cả — người chia, máy giữ nguyên.

Một dòng: {"en": str, "vi": str, "het": 0|1}
  het = 1  -> sau dòng này là RANH ĐOẠN (một dòng trống khi xuất .txt)
Các khoá khác (tt / doan — trạng thái fact-check) được mang theo nguyên vẹn khi
chẻ/gộp: hai thao tác đó không đổi một chữ nào nên kết luận cũ vẫn đúng.

Mọi hàm trả DANH SÁCH MỚI, không sửa danh sách của người gọi — UI có chồng hoàn
tác (Ctrl+Z) chụp trạng thái trước mỗi thao tác, mutate ngầm là hỏng chồng đó.
"""

from __future__ import annotations

import copy

# Rác escape CSV của Google Sheet. Đo thật 15/09 trên NAS: 16 chỗ trong 5/51 kịch
# bản (`So the ""diet"" label`). Chỉ dọn ở bản XUẤT — bản gốc giữ nguyên để người
# viết còn nhận ra chữ mình đã gõ.
_RAC = ('""', '"')


def nap(text: str) -> list[dict]:
    """Dán nguyên kịch bản -> danh sách dòng. Dòng trống = ranh đoạn dòng trước."""
    dong: list[dict] = []
    trong = False
    for raw in (text or "").splitlines():
        s = raw.strip()
        if not s:
            trong = True
            continue
        if trong and dong:
            dong[-1]["het"] = 1
        trong = False
        dong.append({"en": s, "vi": "", "het": 0})
    return dong


def che(dong: list[dict], i: int, off: int) -> list[dict]:
    """Chẻ dòng `i` tại vị trí con trỏ `off`. off ở cuối -> đẻ một dòng rỗng."""
    ra = copy.deepcopy(dong)
    if not (0 <= i < len(ra)):
        return ra
    d = ra[i]
    t = d["en"]
    truoc, sau = t[:off].rstrip(), t[off:].lstrip()
    moi = dict(d)
    moi["en"], moi["vi"] = sau, ""     # nửa dưới chưa có bản dịch riêng
    # Treatment đã viết là của Ý ĐÓ, mà ý đó nằm ở nửa trên. Nhân đôi sang cả
    # hai nửa là đẻ ra cảnh ma — đếm shot sai, đếm tiền sinh ảnh cũng sai.
    moi.pop("canh", None)
    moi.pop("tr", None)
    d["en"] = truoc
    moi["het"], d["het"] = d["het"], 0  # ranh đoạn thuộc về CUỐI đoạn
    ra.insert(i + 1, moi)
    return ra


def gop(dong: list[dict], i: int) -> list[dict]:
    """Gộp dòng `i` vào dòng trên. Nếu dòng trên có ranh đoạn thì CHỈ bỏ ranh đó
    — Backspace đầu dòng sau một dòng trống là xoá dòng trống, không phải dính
    hai đoạn vào nhau."""
    ra = copy.deepcopy(dong)
    if not (0 < i < len(ra)):
        return ra
    tren = ra[i - 1]
    if tren["het"]:
        tren["het"] = 0
        return ra
    d = ra.pop(i)
    tren["en"] = " ".join(x for x in (tren["en"].rstrip(), d["en"].lstrip()) if x)
    tren["vi"] = " ".join(x for x in (tren.get("vi", "").rstrip(),
                                      d.get("vi", "").lstrip()) if x)
    tren["het"] = d["het"]
    canh = doc_canh(tren) + doc_canh(d)
    tren.pop("tr", None)
    if canh:
        tren["canh"] = canh
    return ra


def ranh(dong: list[dict], i: int) -> list[dict]:
    """Bật/tắt ranh đoạn sau dòng `i`."""
    ra = copy.deepcopy(dong)
    if 0 <= i < len(ra):
        ra[i]["het"] = 0 if ra[i]["het"] else 1
    return ra


# ───────────────────────────────── CẢNH ──────────────────────────────────────
# Một dòng treatment = MỘT CẢNH (user chốt 24/09: *"một phân cảnh có 6 cảnh
# treatment là 6 dòng riêng biệt"*). Cảnh còn phải đeo cỡ cảnh / góc máy /
# chuyển động / SFX / tông nên nó là OBJECT, không phải một khúc chuỗi.
#
# Metadata gắn TRÊN TỪNG CẢNH, không giữ bảng theo chỉ số — cùng bài học của
# `cum`: chẻ/gộp là chuyện xảy ra suốt, bảng theo chỉ số thì lần nào cũng lệch.
# `ts` = danh sách MÃ tài sản dùng trong cảnh (trỏ vào sổ của tập). Sổ chỉ
# thay được bước "ném ref vào, ghi nhớ đặc điểm" nếu cảnh chỉ được vào sổ.
# `pa` / `pv` = prompt ẢNH và prompt VIDEO bằng TIẾNG ANH. Đội viết treatment
# bằng tiếng Việt, mà prompt gửi nhà AI phải tiếng Anh — ghép thẳng chữ Việt
# vào là nhà AI đọc lõm bõm rồi ra ảnh sai.
KHOA_CANH = ("t", "co", "goc", "cd", "sfx", "tong", "ts", "pa", "pv")


def doc_canh(d: dict) -> list[dict]:
    """Cảnh của một dòng, nhận CẢ dữ liệu cũ (`tr` là chuỗi) lẫn mới (`canh`).

    Không có bước migration chạy một lần: đang có người dùng thật trên
    production, đổi kho dưới chân họ là hỏng giữa buổi. Mỗi dòng tự nâng cấp
    khi được lưu lại.

    Chuỗi cũ tách theo XUỐNG DÒNG, KHÔNG đoán mốc `2)` `3)` để tách hộ: 28 ô
    đang dính là do lỗi đọc chữ cũ, user chốt tự sửa tay. Máy đoán hộ là sửa
    chữ của người viết.
    """
    tho = d.get("canh")
    if isinstance(tho, list):
        ra = []
        for x in tho:
            if not isinstance(x, dict):
                continue
            c = {k: str(x[k]) for k in KHOA_CANH if k != "ts" and x.get(k)}
            ts = x.get("ts")
            if isinstance(ts, list):        # chuỗi lọt vào đây là str() ra rác
                sach = [str(m).strip() for m in ts if isinstance(m, str) and m.strip()]
                if sach:
                    c["ts"] = sach
            if c.get("t", "").strip():
                c["t"] = c["t"].strip()
                ra.append(c)
        return ra
    return [{"t": x.strip()} for x in (d.get("tr") or "").split(chr(10)) if x.strip()]


def ghi_canh(d: dict, canh: list[dict]) -> dict:
    """DÒNG MỚI mang danh sách cảnh — hàm thuần, không sửa dòng của người gọi.

    Dọn luôn `tr` cũ: giữ cả hai thì sớm muộn có chỗ đọc nhầm bản cũ.
    Không cảnh nào thì XOÁ hẳn khoá, đừng để lại `canh: []` cho kho phình.
    """
    ra = copy.deepcopy(d)
    ra.pop("tr", None)
    sach = [c for c in doc_canh({"canh": canh})]
    if sach:
        ra["canh"] = sach
    else:
        ra.pop("canh", None)
    return ra


# Bảng màu CỤM (user chốt 23/09: "gom các câu thành 1 cụm, dùng màu đánh dấu").
# CỐ ĐỊNH, không cho nhập mã màu tự do: nhập bậy là UI vẽ ra thứ không đọc được
# trên nền tối. 6 màu — nhiều hơn thì mắt không phân biệt nổi trên một chương.
MAU_CUM = {
    1: ("Vàng", "#d9a94c"),
    2: ("Xanh lá", "#3fae63"),
    3: ("Xanh dương", "#4c8fe0"),
    4: ("Tím", "#a274d6"),
    5: ("Cam", "#e08b4c"),
    6: ("Hồng", "#dd6b9a"),
}


def gom_cum(dong: list[dict], tu: int, den: int, mau: int) -> list[dict]:
    """Gán các dòng [tu..den] vào một cụm màu. Hàm thuần.

    Cụm ghi THẲNG trên từng dòng (`cum` = số màu) chứ không giữ một bảng vùng
    riêng: chẻ/gộp dòng là chuyện xảy ra suốt, mà bảng vùng theo chỉ số thì lần
    nào chẻ cũng lệch. Ghi trên dòng thì chẻ ra hai nửa vẫn mang theo cụm.
    """
    if mau not in MAU_CUM:
        raise ValueError(f"Màu cụm '{mau}' không có trong bảng — "
                         f"chỉ nhận {', '.join(map(str, MAU_CUM))}.")
    ra = copy.deepcopy(dong)
    for i in range(max(0, tu), min(den, len(ra) - 1) + 1):
        ra[i]["cum"] = mau
    return ra


def bo_cum(dong: list[dict], tu: int, den: int) -> list[dict]:
    ra = copy.deepcopy(dong)
    for i in range(max(0, tu), min(den, len(ra) - 1) + 1):
        ra[i].pop("cum", None)
    return ra


def xuat(dong: list[dict], cot: str = "en") -> str:
    """Bản .txt đem đi ren voice: đúng các dòng đang thấy, ranh đoạn thành dòng
    trống, đã dọn rác `""`. Không có số thứ tự — số chỉ tồn tại trên UI (vẽ bằng
    CSS counter) nên không có đường nào lọt vào đây."""
    ra: list[str] = []
    for d in dong:
        ra.append((d.get(cot) or "").replace(*_RAC))
        if d.get("het"):
            ra.append("")
    while ra and not ra[-1]:
        ra.pop()
    return "\n".join(ra) + "\n" if ra else ""
