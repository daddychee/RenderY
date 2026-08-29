"""C5 vision gate — mắt vision soi TOP-PICK ngay trước khi chốt pick (C đợt 5).

Thiết kế đã duyệt: MO_TA_VAN_HANH_C5_VISION_GATE.md (user duyệt 2026-07-10). Nguyên tắc
user chốt (V123 §3c + filter-overload-guard): chỉ soi lead-pick; demote CHỈ khi
subject_match == "no" (phân vân KHÔNG veto — y luật c2); mood "no" chỉ warning, không
đụng pick; mọi lỗi API → caller fail-open nhận pick. KHÔNG phải cửa loại thứ 3: không
loại ai khỏi pool, chỉ đổi thứ tự tiêu thụ trong vòng tải (tối đa GATE_BUDGET verdict/beat).
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

from autoedit.library.vision import (
    DEFAULT_GLM_VISION_MODEL,
    _clean_json,
    extract_frames,
    glm_api_keys,
    glm_api_url,
    image_to_jpeg,
    media_type_of,
    shrink_for_api,
)
from autoedit.project import Beat

GATE_BUDGET = 2  # tối đa 2 verdict/beat: top-pick + đúng 1 ứng viên kế (user chốt V123 §3c)
# User chốt 2026-07-10 (sau đo tốc độ V11): CHỈ soi pick KHO LOCAL — đúng lớp lỗi đã
# chứng minh (tag GLM tự sinh lúc nạp: b60/b68); stock Pexels mô tả người viết, rủi ro
# thấp, bỏ soi tiết kiệm ~60 call + ~10 phút/video. Muốn mở lại PA-A: thêm "pexels".
GATE_SOURCES = ("local",)


class GateVerdict(BaseModel):
    """Phán quyết của mắt vision cho 1 frame vs 1 beat."""

    subject_match: Literal["yes", "no", "unsure"]  # "no" = demote (chỉ ca chắc chắn)
    mood_match: Literal["yes", "no", "unsure"]     # "no" = warning-only (đợt này)
    seen: str    # 1 câu tiếng Việt: frame THẬT SỰ có gì — editor đọc trong report
    reason: str  # 1 câu tiếng Việt: vì sao khớp/không


GATE_SYSTEM = """You are the LAST visual checker for ONE beat of a YouTube video. You see
ONE frame of the footage about to be locked in, what the beat NEEDS, and what the footage's
text tags CLAIM. Text tags may be WRONG (they were auto-generated) — trust the FRAME.

subject_match — does the frame plausibly show what the beat needs?
- "no" ONLY when the frame clearly shows a DIFFERENT subject / real entity / place /
  celestial body than the beat needs (beat needs an observatory, frame shows houses;
  beat needs the Moon, frame shows a red planet). Similar action or composition does
  NOT redeem a wrong entity.
- "unsure" when one frame cannot tell. NEVER answer "no" on doubt.
- "yes" when the subject fits — generic-but-compatible footage is a "yes".

mood_match — does the frame's feel (light, color, energy) fit the beat's mood?
Same discipline: "no" only when clearly opposite; doubt = "unsure".

"seen" = 1 câu tiếng Việt ngắn: frame THẬT SỰ chiếu gì.
"reason" = 1 câu tiếng Việt ngắn giải thích verdict. TỐI ĐA 15 TỪ mỗi câu.
"""

# Chống schema-echo PB3 (2 lớp): example instance trong system + user text "Do NOT
# output the schema". Example build từ chính GateVerdict — schema đổi là example đổi theo.
_EXAMPLE = GateVerdict(
    subject_match="no", mood_match="unsure",
    seen="Dãy nhà dân dưới trời sao, không có kính thiên văn.",
    reason="Beat cần đài quan sát, frame là khu dân cư.",
).model_dump_json()


class VisionGate:
    """Mắt GLM-4.6V cho C5 — endpoint NATIVE api.z.ai, thinking TẮT, 1 frame 960px.

    Cùng kỷ luật GLMVisionTagger (PB3/PB4): retry backoff 429/5xx, feedback-retry khi
    JSON sai schema, 400 content-filter nêu body rồi raise (không retry được).
    """

    def __init__(self, api_key: str | None = None,
                 model: str = DEFAULT_GLM_VISION_MODEL, timeout: float = 30.0) -> None:
        from dotenv import load_dotenv

        load_dotenv()
        self.model = model
        self._timeout = timeout
        # V11 lần 1: gate chết 3 lỗi đầu run (timeout + 429/1305 thoáng qua) trong khi
        # M3b multi-key chạy ngon — gate cũng phải XOAY KEY theo attempt, không tựa 1 key.
        self._keys = [api_key] if api_key else glm_api_keys()
        if not self._keys:
            raise RuntimeError("Thiếu GLM_API_KEY trong .env — C5 vision gate cần key GLM")

    def check(self, media_path: Path, beat: Beat, *, central_subject: str = "",
              video_subject: str = "", claim: str = "",
              images: list[bytes] | None = None) -> GateVerdict:
        """ĐÚNG 1 câu hỏi cho 1 frame vs 1 beat. Lỗi hết retry -> raise (caller fail-open)."""
        media_path = Path(media_path)
        imgs = images if images is not None else [self._frame(media_path)]
        img = shrink_for_api(imgs[0])
        # User chốt 2026-07-10 (đo tốc độ V11): KHÔNG gửi schema — verdict chỉ 4 key,
        # example là đủ; khối schema chính là mồi bệnh echo (GLM chép schema thay vì
        # trả instance, ~36s/ca vì đốt attempt). Pydantic vẫn gác output như cũ.
        system = (GATE_SYSTEM
                  + '\nReturn ONLY one JSON object with exactly the 4 keys '
                    '"subject_match", "mood_match", "seen", "reason". '
                    "No prose/markdown/fences.\n\nExample of a CORRECT output for a "
                    "DIFFERENT beat — same shape, values for THIS frame:\n" + _EXAMPLE)
        lines = [f"BEAT NEEDS — script sentence: {beat.text}",
                 f"Visual intent: {beat.visual_concept} (mood: {beat.mood})"]
        if central_subject:
            lines.append(f"Chapter central_subject: {central_subject}")
        if video_subject:
            lines.append(f"VIDEO SUBJECT (outer boundary): {video_subject}")
        if claim:
            lines.append(f"FOOTAGE TAGS CLAIM: {claim}")
        base_text = "\n".join(lines) + (
            "\n\nJudge the frame above against this beat. Output ONE JSON instance with "
            'exactly the 4 keys {"subject_match": ..., "mood_match": ..., "seen": ..., '
            '"reason": ...}. Do NOT output the schema itself.')
        content: list[dict] = [
            {"type": "image_url",
             "image_url": {"url": "data:image/jpeg;base64,"
                                  + base64.standard_b64encode(img).decode("ascii")}},
            {"type": "text", "text": base_text},
        ]
        body = {
            "model": self.model, "temperature": 0, "max_tokens": 300,
            "thinking": {"type": "disabled"},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": content}],
        }
        last: Exception | None = None
        for attempt in range(4):
            try:
                d = self._post(body, key=self._keys[attempt % len(self._keys)])
                msg = (d.get("choices") or [{}])[0].get("message", {}) or {}
                text = (msg.get("content") or "").strip()
                if not text:
                    raise ValueError("GLM vision trả content rỗng")
                return GateVerdict.model_validate_json(_clean_json(text))
            except urllib.error.HTTPError as exc:
                last = exc
                if exc.code in (429, 500, 502, 503, 529) and attempt < 3:
                    # 429/1305 "service busy" cần nguội LÂU hơn lỗi thường (V11 lần 1:
                    # 1.5-4.5s không đủ, chết cả 4 attempt) — key kế tiếp + 4/8/12s
                    time.sleep(4.0 * (attempt + 1))
                    continue
                try:
                    detail = exc.read()[:200].decode("utf-8", "replace")
                except Exception:
                    detail = ""
                raise RuntimeError(f"GLM HTTP {exc.code} với {media_path.name}: "
                                   f"{detail or exc.reason}") from exc
            except ValidationError as exc:
                last = exc
                if attempt < 3:
                    # Echo dai (smoke V11): retry phải CHÌA LẠI example instance —
                    # chỉ nêu lỗi thiếu-field thì model tiếp tục chép schema
                    content[-1]["text"] = (
                        base_text + "\n\nYour previous output failed validation:\n"
                        + str(exc)[:400]
                        + "\nDo NOT return the schema. Return ONLY a JSON instance "
                          "shaped like this example (values must describe THIS frame):\n"
                        + _EXAMPLE)
                    time.sleep(1.0 * (attempt + 1))
                    continue
            except Exception as exc:  # noqa: BLE001 — đứt kết nối / rỗng -> retry
                last = exc
                if attempt < 3:
                    time.sleep(1.0 * (attempt + 1))
                    continue
        raise RuntimeError(f"C5 gate thất bại sau 4 lần với {media_path.name}: {last!r}")

    @staticmethod
    def _frame(media_path: Path) -> bytes:
        """1 frame GIỮA clip (kỷ luật 1-frame PB6) / chính ảnh."""
        mtype = media_type_of(media_path)
        if mtype == "video":
            return extract_frames(media_path, n=1)[0]
        if mtype == "image":
            return image_to_jpeg(media_path)
        raise ValueError(f"Không hỗ trợ định dạng: {media_path}")

    def _post(self, body: dict, key: str | None = None) -> dict:
        """HTTP call tách riêng để test stub được (y GLMVisionTagger)."""
        req = urllib.request.Request(
            glm_api_url(), data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": "Bearer " + (key or self._keys[0]),
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            return json.load(resp)
