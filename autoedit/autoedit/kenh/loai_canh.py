r"""Tầng 3 Hồ Sơ Kênh — TỶ TRỌNG LOẠI CẢNH, chấm bằng GLM vision (Đợt B).

"Học thứ tự ưu tiên nguồn từ kênh ref" = đo kênh đó dùng bao nhiêu % mỗi LOẠI
cảnh, rồi map thành hạn mức nguồn khi dựng (Đợt C):

    tu_quay  — người thật trước máy / cầm tay / vlog / phỏng vấn (PA3 ưu tiên)
    b_roll   — cảnh quay chuyên nghiệp kiểu stock (Pexels/kho)
    do_hoa   — đồ hoạ / bản đồ / chữ / chart / animation 2D
    ai_render— cảnh dựng 3D/AI-render (PA2 aigen nhắm loại này)

Cách đo (quyết 05/09): 8 khung TRẢI ĐỀU mỗi video (extract_frames có sẵn của
library/vision) — tỷ trọng theo THỜI LƯỢNG đúng nghĩa hơn theo shot, và không
tốn thêm lượt dò điểm cắt. Cả 8 khung đi MỘT request GLM (GLM-4.6V nhận nhiều
ảnh/message — tagger kho đã gửi 2 ảnh/lượt từ lâu), 1 video = 1 lượt gọi.

Fail-open toàn tập: thiếu key GLM / API chết -> loai_canh={} + log, hồ sơ kênh
vẫn có 2 tầng nhịp+nhạc. Ghi SỔ GỌI NỀN viec="do_kenh" (bài học 03/09: rendery
gọi LLM không ghi sổ, giám sát mù).
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

CAC_LOAI = ("tu_quay", "b_roll", "do_hoa", "ai_render")
SO_KHUNG = 8

_SYSTEM = """Bạn phân loại khung hình video documentary/faceless. Với MỖI ảnh
được đánh số, chọn ĐÚNG MỘT loại:
- "tu_quay": người thật trước máy quay / cầm tay / vlog / phỏng vấn / cảnh đời thường tự quay
- "b_roll": cảnh quay chuyên nghiệp kiểu stock (thiên nhiên, thành phố, drone, close-up sản phẩm)
- "do_hoa": đồ hoạ, bản đồ, chữ lớn, chart, animation 2D, màn hình máy tính
- "ai_render": cảnh render 3D hoặc ảnh/video do AI sinh (bề mặt quá mượt, ánh sáng phi thực)

Trả DUY NHẤT JSON: {"phan_loai": ["<loại ảnh 1>", "<loại ảnh 2>", ...]} đúng
thứ tự ảnh, đủ số phần tử bằng số ảnh, không thêm chữ nào khác."""


def _goi_glm(body: dict, api_key: str, timeout: float = 120.0) -> dict:
    """HTTP call tách riêng để test stub được (khuôn GLMVisionTagger._post)."""
    from autoedit.library.vision import glm_api_url

    req = urllib.request.Request(
        glm_api_url(), data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": "Bearer " + api_key,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def cham_loai_canh(frames: list[bytes], goi=None, log=None) -> dict[str, float]:
    """[jpeg bytes] -> {loại: tỉ trọng 0..1}. Rỗng nếu không chấm được (fail-open).

    `goi` tiêm được để test không mạng (nhận body dict, trả response dict)."""
    from autoedit import so_goi_nen
    from autoedit.library.vision import (DEFAULT_GLM_VISION_MODEL, _clean_json,
                                         glm_api_keys, shrink_for_api)

    def ghi(m):
        if log:
            log(m)

    if not frames:
        return {}
    keys = glm_api_keys()
    if not keys and goi is None:
        ghi("kenh: thiếu GLM_API_KEY — bỏ tầng loại cảnh (hồ sơ vẫn có nhịp+nhạc)")
        return {}
    content: list[dict] = []
    for i, f in enumerate(frames, start=1):
        content.append({"type": "image_url", "image_url": {
            "url": "data:image/jpeg;base64,"
                   + base64.standard_b64encode(shrink_for_api(f)).decode()}})
        content.append({"type": "text", "text": f"(ảnh {i})"})
    content.append({"type": "text",
                    "text": f"Phân loại {len(frames)} ảnh trên. Chỉ trả JSON."})
    body = {"model": DEFAULT_GLM_VISION_MODEL, "temperature": 0, "max_tokens": 400,
            "thinking": {"type": "disabled"},
            "messages": [{"role": "system", "content": _SYSTEM},
                         {"role": "user", "content": content}]}
    goi_that = goi or (lambda b: _goi_glm(b, keys[0]))
    last: Exception | None = None
    t0 = time.time()
    for lan in range(3):
        try:
            d = goi_that(body)
            text = ((d.get("choices") or [{}])[0].get("message", {})
                    .get("content") or "").strip()
            ds = json.loads(_clean_json(text)).get("phan_loai", [])
            hop_le = [x for x in ds if x in CAC_LOAI]
            if not hop_le:
                raise ValueError(f"GLM trả loại lạ: {ds[:4]}")
            so_goi_nen.ghi("llm", duoi=(keys[0][-4:] if keys else "stub"), ok=True,
                           viec="do_kenh", ms=(time.time() - t0) * 1000)
            n = len(hop_le)
            return {loai: round(hop_le.count(loai) / n, 3) for loai in CAC_LOAI}
        except urllib.error.HTTPError as exc:  # 4xx dai dẳng không retry mù
            last = exc
            if exc.code == 429 and lan < 2:
                time.sleep(2.0 * (lan + 1))
                continue
            break
        except Exception as exc:  # noqa: BLE001 — JSON vỡ/đứt kết nối -> retry
            last = exc
            if lan < 2:
                time.sleep(1.0 * (lan + 1))
                continue
    so_goi_nen.ghi("llm", duoi=(keys[0][-4:] if keys else "stub"), ok=False,
                   ma_loi=str(last)[:200], viec="do_kenh",
                   ms=(time.time() - t0) * 1000)
    ghi(f"kenh: chấm loại cảnh lỗi ({str(last)[:120]}) — bỏ tầng này")
    return {}


def do_loai_canh(videos: list[Path], goi=None, log=None) -> dict[str, float]:
    """Nhiều video -> tỷ trọng loại cảnh GỘP (trung bình các video chấm được)."""
    from statistics import fmean

    from autoedit.library.vision import extract_frames

    ket_qua: list[dict[str, float]] = []
    for v in videos:
        try:
            frames = extract_frames(v, n=SO_KHUNG)
        except Exception as exc:  # noqa: BLE001 — video hỏng không giết cả kênh
            if log:
                log(f"kenh: {v.name} rút khung lỗi ({exc}) — bỏ")
            continue
        ty_trong = cham_loai_canh(frames, goi=goi, log=log)
        if ty_trong:
            ket_qua.append(ty_trong)
    if not ket_qua:
        return {}
    return {loai: round(fmean(k.get(loai, 0.0) for k in ket_qua), 3)
            for loai in CAC_LOAI}
