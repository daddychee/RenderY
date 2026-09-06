r"""Đọc NỘI DUNG cảnh ref bằng GLM-4.6V — gộp LÔ nhiều ảnh mỗi lần gọi.

Vì sao đọc hình chứ không dựa phụ đề (đo 06/09, 70 cảnh >=2s trong 300s ref):
  - 11% cảnh KHÔNG có phụ đề nào chồng lên -> từ khóa rỗng, chết trong kho.
    Mà đó thường là b-roll đẹp nhất (giây 14: phụ nữ đi xe máy giữa phố
    Guayaquil taxi vàng — hình phố xá Ecuador hoàn hảo).
  - 19% cảnh có >=3 câu chồng -> trộn nhiều ý; 7% chỉ có câu vô nghĩa.
  - Phụ đề ref là tiếng Bulgaria: dựa vào nó thì VẪN phải gọi LLM để dịch, tức
    không tiết kiệm được lần gọi nào mà kết quả tệ hơn.

Trục `vat_the` (thêm sau vòng thử v1): bắt liệt kê vật thể nhìn thấy rõ. Đo:
88 -> 127 từ khóa (+44%), bắt được đúng thứ v1 sót — "bananas" trong thùng
Burberry (ma túy giấu trong chuối xuất khẩu, chính là nội dung lời thoại) và
"tennis court" ở biệt thự. Chi phí gần như không đổi.

Chi phí đo thật: lô 12 ảnh 512px = 3.181 token vào / 679 ra, 9-17s/lô.
Cả tập 638 cảnh ~ 54 lô ~ $0.18.

Giới hạn đã biết (không giấu): GLM đọc `geo` chỉ ra 3/12 cảnh và nhận `aerial`
1/12 — nhắc thẳng trong prompt cũng không sửa được. Vì vậy `geo` cấp TẬP được
gắn cứng bởi nap_ref_tap (cả file ref quay ở một nước), GLM chỉ bổ sung chi tiết.
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

LO = 12                 # ảnh mỗi lần gọi
RONG_ANH = 512          # 512x288 = 197 token/ảnh
MODEL = "glm-4.6v"
CHO_LO_S = 1.0          # nghỉ giữa 2 lô, tránh dồn API

_SYS = """Bạn xem các KHUNG HÌNH trích từ phim tài liệu. Với MỖI ảnh, ghi ĐÚNG
những gì NHÌN THẤY — không suy diễn từ lời thoại.

QUAN TRỌNG — hãy kể ĐỦ VẬT THỂ trong hình, kể cả thứ ở hậu cảnh hoặc cầm trên
tay. Editor tra kho bằng chính những vật đó (ví dụ thấy thùng hàng có chuối thì
phải ghi cả "bananas", không chỉ ghi "box").

Mỗi ảnh trả 1 object, các trục (tiếng Anh, chữ thường):
  subject : chủ thể chính máy quay chĩa vào (1-4 từ)
  vat_the : LIỆT KÊ 3-6 vật thể nhìn thấy rõ, cách nhau bằng dấu phẩy
  action  : đang làm gì
  setting : nơi chốn
  geo     : dấu hiệu địa lý NHÌN THẤY: chữ trên biển hiệu/thùng hàng, biển số,
            kiến trúc, cây cối đặc trưng, cờ. Không thấy thì để ""
  people  : số người + vai
  shot    : cỡ cảnh — wide / medium / close / aerial / handheld.
            Nhìn từ trên cao xuống = aerial (không phải wide)
  mood    : không khí
Thêm:
  khop    : 0-3 — hình MINH HOẠ cho lời thoại kèm theo tốt đến đâu?
            3=đúng hẳn, 2=liên quan, 1=chỉ chung không khí, 0=lệch hẳn

Trả DUY NHẤT JSON: {"canh":[{"i":1,"subject":"...","vat_the":"...","action":"...",
"setting":"...","geo":"...","people":"...","shot":"...","mood":"...","khop":2}]}"""


@dataclass
class DocRa:
    i: int
    subject: str = ""
    vat_the: str = ""
    action: str = ""
    setting: str = ""
    geo: str = ""
    people: str = ""
    shot: str = ""
    mood: str = ""
    khop: int = 0


def trich_anh(video: Path, t0: float, t1: float, dich: Path,
              rong: int = RONG_ANH) -> Path | None:
    """1 JPEG giữa cảnh — 15KB/ảnh (đo thật). Đã có thì dùng lại."""
    if dich.is_file() and dich.stat().st_size > 0:
        return dich
    dich.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{(t0 + t1) / 2:.2f}", "-i", str(video),
         "-frames:v", "1", "-vf", f"scale={rong}:-2", "-q:v", "6", "-y", str(dich)],
        capture_output=True, text=True)
    return dich if (r.returncode == 0 and dich.is_file()) else None


def _khoa() -> str:
    from autoedit.library.vision import glm_api_keys

    k = glm_api_keys()
    if not k:
        raise RuntimeError(
            "Thiếu khoá GLM — két V3: General › API Keys › rendery › chia_beat.")
    return k[0]


def _go_json(txt: str) -> dict:
    s = (txt or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
    return json.loads(s[s.index("{"):s.rindex("}") + 1])


def doc_lo(anh_loi: list[tuple[Path, str]], timeout: float = 300.0) -> list[DocRa]:
    """[(ảnh, lời thoại quanh cảnh)] -> [DocRa]. Một lần gọi cho cả lô."""
    import requests

    from autoedit.library.vision import glm_api_url

    ct: list[dict] = []
    for j, (anh, loi) in enumerate(anh_loi, 1):
        b64 = base64.b64encode(anh.read_bytes()).decode()
        ct.append({"type": "text",
                   "text": f"--- Ảnh {j} · lời thoại lúc đó: {loi or '(không có lời)'}"})
        ct.append({"type": "image_url",
                   "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    r = requests.post(
        glm_api_url(), timeout=timeout,
        headers={"Authorization": f"Bearer {_khoa()}", "Content-Type": "application/json"},
        json={"model": MODEL, "max_tokens": 4000, "temperature": 0.2,
              "thinking": {"type": "disabled"},
              "messages": [{"role": "system", "content": _SYS},
                           {"role": "user", "content": ct}]})
    r.raise_for_status()
    d = r.json()
    kq = _go_json(d["choices"][0]["message"]["content"])
    ra: dict[int, DocRa] = {}
    for c in (kq.get("canh") or []):
        if not isinstance(c, dict):
            continue
        try:
            i = int(c.get("i") or 0)
        except (TypeError, ValueError):
            continue
        if 1 <= i <= len(anh_loi):
            ra[i] = DocRa(
                i=i, subject=str(c.get("subject") or "").strip(),
                vat_the=str(c.get("vat_the") or "").strip(),
                action=str(c.get("action") or "").strip(),
                setting=str(c.get("setting") or "").strip(),
                geo=str(c.get("geo") or "").strip(),
                people=str(c.get("people") or "").strip(),
                shot=str(c.get("shot") or "").strip(),
                mood=str(c.get("mood") or "").strip(),
                khop=max(0, min(3, int(c.get("khop") or 0))))
    # GLM bỏ sót ảnh nào thì trả object rỗng cho ảnh đó — KHÔNG lệch chỉ số
    return [ra.get(j, DocRa(i=j)) for j in range(1, len(anh_loi) + 1)]


def doc_nhieu(anh_loi: list[tuple[Path, str]], lo: int = LO,
              log=None, goi=None) -> list[DocRa]:
    """Chia lô, gọi lần lượt. Lô hỏng KHÔNG giết cả tập (fail-soft)."""
    goi = goi or doc_lo
    ra: list[DocRa] = []
    for b in range(0, len(anh_loi), lo):
        phan = anh_loi[b:b + lo]
        try:
            kq = goi(phan)
        except Exception as e:                       # noqa: BLE001 — fail-soft
            if log:
                log(f"sotra: lô {b // lo + 1} đọc hỏng ({str(e)[:80]}) — bỏ qua")
            kq = [DocRa(i=j + 1) for j in range(len(phan))]
        ra.extend(kq)
        if log:
            log(f"sotra: đọc hình {min(b + lo, len(anh_loi))}/{len(anh_loi)} cảnh")
        if b + lo < len(anh_loi):
            time.sleep(CHO_LO_S)
    return ra
