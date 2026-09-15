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
    return ra


def ranh(dong: list[dict], i: int) -> list[dict]:
    """Bật/tắt ranh đoạn sau dòng `i`."""
    ra = copy.deepcopy(dong)
    if 0 <= i < len(ra):
        ra[i]["het"] = 0 if ra[i]["het"] else 1
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
