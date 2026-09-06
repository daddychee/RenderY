r"""LỚP NGHĨA — topic của beat, đọc TỪ LỜI, không đọc hình (đợt 2, 06/09).

Nguyên tắc chốt sau phản biện: lớp Hình (vat_the/subject — từ pixel) và lớp
Nghĩa (topic — từ lời kịch bản) là HAI HỆ RIÊNG. Ép chúng làm một là chỗ ẩn dụ
vỡ: cánh chim tag "bird" không bao giờ khớp câu "tự do tài chính".

Ở đây LLM CHỈ đọc lời beat — không đưa mô tả hình vào prompt, để nó không bị
kéo về tả vật. Lời ref Ecuador 100% tiếng Bulgaria (đo 06/09) nên dịch và gán
topic gộp một lần gọi (rẻ hơn hai lượt).

Karpathy: chạy lô nhỏ, NHÌN TẬN MẮT trước khi chạy hết; validate từng trường,
không tin LLM; đếm hỏng và dừng khi vượt ngưỡng — không nuốt im.
"""
from __future__ import annotations

import json
import re
import time

LO = 15                 # beat mỗi lần gọi
MODEL = "glm-4.6"       # thuần chữ, rẻ hơn bản vision
NGUONG_HONG = 0.30      # >30% lô hỏng -> DỪNG, không chạy tiếp mù

_SYS = """Bạn đọc LỜI THOẠI của từng đoạn phim tài liệu (có thể là tiếng Bulgaria,
Tây Ban Nha, Anh...). Với MỖI đoạn, trả:

  dich   : dịch sang tiếng Anh, 1 câu ngắn gọn giữ đúng ý
  topic  : 2-5 TỪ KHÓA CHỦ ĐỀ bằng tiếng Anh — đoạn này NÓI VỀ CÁI GÌ.
           Đây là chủ đề, KHÔNG phải vật thể nhìn thấy. Ví dụ đúng:
             "cocaine trafficking", "minimum wage", "police raid", "family life"
           Ví dụ SAI (tả vật): "man", "street", "building"
  an_du  : true nếu đoạn này nói bóng gió / trừu tượng (hình minh họa cho nó
           sẽ là ẩn dụ, không thể tra bằng vật thể); false nếu nói thẳng việc cụ thể

BẮT BUỘC: mọi giá trị tiếng ANH thường. Trả DUY NHẤT JSON:
{"beat":[{"i":1,"dich":"...","topic":"a, b, c","an_du":false}]}"""


def _khoa() -> str:
    from autoedit.sotra.doc_canh import _khoa as k

    return k()


def _go_json(txt: str) -> dict:
    s = (txt or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
    return json.loads(s[s.index("{"):s.rindex("}") + 1])


def doc_lo(loi_beats: list[str], timeout: float = 240.0) -> list[dict]:
    """[lời beat] -> [{dich, topic, an_du}] cùng thứ tự (thiếu -> dict rỗng)."""
    import requests

    from autoedit.library.vision import glm_api_url

    noi = "\n\n".join(f"--- Đoạn {j}: {l[:600]}" for j, l in enumerate(loi_beats, 1))
    khoa = _khoa()
    t0 = time.time()
    try:
        r = requests.post(
            glm_api_url(), timeout=timeout,
            headers={"Authorization": f"Bearer {khoa}",
                     "Content-Type": "application/json"},
            json={"model": MODEL, "max_tokens": 3000, "temperature": 0.2,
                  "thinking": {"type": "disabled"},
                  "messages": [{"role": "system", "content": _SYS},
                               {"role": "user", "content": noi}]})
        r.raise_for_status()
    except Exception as e:
        _ghi_so(khoa, False, str(e)[:200], t0)
        raise
    _ghi_so(khoa, True, "", t0)
    kq = _go_json(r.json()["choices"][0]["message"]["content"])
    ra: dict[int, dict] = {}
    for b in (kq.get("beat") or []):
        if not isinstance(b, dict):
            continue
        try:
            i = int(b.get("i") or 0)
        except (TypeError, ValueError):
            continue
        topic = str(b.get("topic") or "").strip().lower()
        # VALIDATE (bài học 06/09: GLM từng trả tiếng Việt dù prompt bảo Anh)
        if re.search(r"[àáâãèéêìíòóôõùúýăđĩũơưạảấầẩậắằẳẵặẹẻẽếềểệỉịọỏốồổỗộớờởợụủứừửữựỳỵỷỹ]",
                     topic):
            topic = ""
        if 1 <= i <= len(loi_beats):
            ra[i] = {"dich": str(b.get("dich") or "").strip(),
                     "topic": topic,
                     "an_du": 1 if b.get("an_du") else 0}
    return [ra.get(j, {}) for j in range(1, len(loi_beats) + 1)]


def _ghi_so(khoa: str, ok: bool, ma_loi: str, t0: float) -> None:
    try:
        from autoedit import so_goi_nen

        so_goi_nen.ghi("llm", duoi=khoa[-4:], ok=ok, ma_loi=ma_loi, model=MODEL,
                       viec="doc_hinh_ref", ms=(time.time() - t0) * 1000)
    except Exception:  # noqa: BLE001
        pass


def gan_nghia(conn, tap: str = "", gioi_han: int = 0, log=None, goi=None) -> dict:
    """Gán topic cho beat CHƯA có. Trả {xong, hong, bo_qua} — đếm thật, không nuốt."""
    goi = goi or doc_lo
    dk = "topic='' AND loi_goc!=''" + (" AND tap=?" if tap else "")
    rows = conn.execute(
        f"SELECT id, loi_goc FROM beat WHERE {dk} ORDER BY t0"
        + (f" LIMIT {int(gioi_han)}" if gioi_han else ""),
        (tap,) if tap else ()).fetchall()
    if not rows:
        return {"xong": 0, "hong": 0, "bo_qua": 0}
    xong = hong = bo_qua = 0
    for b in range(0, len(rows), LO):
        phan = rows[b:b + LO]
        try:
            kq = goi([r["loi_goc"] for r in phan])
        except Exception as exc:  # noqa: BLE001
            hong += len(phan)
            if log:
                log(f"nghia: lô {b // LO + 1} HỎNG ({str(exc)[:70]})")
            if hong / max(1, len(rows)) > NGUONG_HONG:
                if log:
                    log(f"nghia: DỪNG — hỏng {hong}/{len(rows)} vượt ngưỡng "
                        f"{int(NGUONG_HONG * 100)}%")
                break
            continue
        for r, d in zip(phan, kq):
            if not d.get("topic"):
                bo_qua += 1
                continue
            conn.execute("UPDATE beat SET loi_dich=?, topic=?, metaphor=? WHERE id=?",
                         (d.get("dich", ""), d["topic"], d.get("an_du", 0), r["id"]))
            xong += 1
        conn.commit()
        if log:
            log(f"nghia: {min(b + LO, len(rows))}/{len(rows)} beat "
                f"(gán {xong}, bỏ {bo_qua}, hỏng {hong})")
        time.sleep(1.0)
    return {"xong": xong, "hong": hong, "bo_qua": bo_qua}
