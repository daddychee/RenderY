"""Vision tagger — tag footage local cho kho + DNA (spec: MO_TA_VAN_HANH_TAG_GLM.md).

Schema tag = field GLM chấm (subject/description/shot_size/mood/scene_type/camera_angle/
has_people/tags) + field đo bằng CODE THUẦN 0 token (measure_colors — lớp rẻ C2b của b1).
Engine mặc định: GLM-4.6V native (CLAUDE.md §5, rẻ ~½ haiku); ClaudeVisionTagger giữ
làm fallback. Interface tách rời để test bằng fake.

Video: rút 2 frame (1/4 và 3/4 thời lượng) bằng ffmpeg -> gửi cùng 1 request; frame
rút 1 LẦN dùng chung cho vision + đo màu (indexer truyền qua tham số `images`).
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Literal, Protocol, get_args

from pydantic import BaseModel, Field, ValidationError, field_validator

from autoedit.music.library import MOOD  # vocabulary mood ĐÓNG 19 từ — footage/chương/nhạc chung
from autoedit.project import ffprobe_duration

from autoedit.httpx_ma import nen_thu_lai

DEFAULT_VISION_MODEL = "claude-haiku-4-5"
DEFAULT_GLM_VISION_MODEL = "glm-4.6v"
# Bài học nhan ban (memory glm-api-lessons): vision PHẢI đi endpoint NATIVE — endpoint
# Anthropic-compat NUỐT ẢNH -> GLM bịa mô tả. Và PHẢI tắt thinking (reasoning ăn hết
# max_tokens -> content rỗng/cụt; tắt -> rẻ ~10x, nhanh, chính xác hơn).
# 2026-07-10 (user phát hiện): GLM có server QUỐC TẾ api.z.ai — đo thật cùng key cùng
# call: 0,7s vs 2,2s server TQ, ít lỗi đứt kết nối hơn hẳn -> mặc định QUỐC TẾ;
# cần quay về TQ thì đặt env GLM_API_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions
GLM_NATIVE_URL = "https://api.z.ai/api/paas/v4/chat/completions"


def glm_api_url() -> str:
    """Endpoint GLM thực dùng — env GLM_API_URL đè được (đổi server không sửa code)."""
    return os.getenv("GLM_API_URL") or GLM_NATIVE_URL

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# Enum đóng (spec §3a) — thêm giá trị = sửa spec + user duyệt lại (thêm sau = tag lại kho)
SceneType = Literal[
    "nature_water", "nature_forest_field", "mountain_desert", "sky_cloud",
    "urban_street", "urban_landmark", "interior", "people_activity", "food",
    "animal_wildlife", "underwater", "space", "abstract_texture", "other",
]
CameraAngle = Literal["eye_level", "low_angle", "high_angle", "overhead", "unknown"]
SCENE_TYPES: tuple[str, ...] = get_args(SceneType)
CAMERA_ANGLES: tuple[str, ...] = get_args(CameraAngle)


class AssetTags(BaseModel):
    """Output vision LLM cho 1 asset."""

    subject: str = Field(description="Chủ thể chính, ngắn gọn, tiếng Anh")
    description: str = Field(description="1 câu mô tả cảnh, tiếng Anh")
    shot_size: Literal["wide", "medium", "close_up", "extreme_close_up", "aerial"]
    scene_type: SceneType = Field(description="Loại cảnh chủ đạo (phục vụ ambient e1 + đếm chữ ký c6)")
    mood: list[str] = Field(
        min_length=1, max_length=2,
        description="1-2 mood từ vocabulary đóng 19 từ của thư viện nhạc")
    camera_angle: CameraAngle = "unknown"  # c7: chỉ tag ở mẻ thử (--angle), mặc định unknown
    has_people: bool
    tags: list[str] = Field(description="5-10 keyword tìm kiếm, tiếng Anh, thường")

    @field_validator("mood")
    @classmethod
    def _mood_in_vocab(cls, v: list[str]) -> list[str]:
        # PB4: từ ngoài vocab thử phiên dịch qua _MOOD_SYNONYMS (tầng map free-text
        # SẴN CÓ của nhạc — không đẻ map mới, spec TAG_GLM §6) trước khi bác; GLM
        # khăng khăng 'appetizing'/'cozy' cho clip đồ ăn dù feedback-retry.
        from autoedit.music.select import _MOOD_SYNONYMS

        out: list[str] = []
        bad: list[str] = []
        for m in (m.strip().lower().replace(" ", "_") for m in v):
            if m in MOOD:
                out.append(m)
            elif m in _MOOD_SYNONYMS:
                out.append(sorted(_MOOD_SYNONYMS[m])[0])  # sorted: dịch ổn định
            else:
                bad.append(m)
        # Mẻ 4 life-in 2026-07-15: đuôi mood lạ DÀI vô hạn (craftsman/food/community...)
        # — 1 từ lạ đánh rớt CẢ asset = asset vô hình với phễu, tệ hơn giữ mood hợp lệ
        # còn lại. Từ lạ chỉ bị BỎ khi vẫn còn ≥1 mood hợp lệ; lạ toàn bộ mới bác
        # (giữ sức ép feedback-retry cho GLM).
        if bad and not out:
            raise ValueError(f"mood ngoài vocabulary 19 từ của nhạc: {bad}")
        return list(dict.fromkeys(out))[:2]  # dedup giữ thứ tự, tối đa 2


class VisionTagger(Protocol):
    def tag(self, media_path: Path, folder_context: str = "",
            images: list[bytes] | None = None, source_title: str = "",
            section_hint: str = "", topic: str = "") -> AssetTags: ...


def media_type_of(path: Path) -> str | None:
    if path.suffix.lower() in VIDEO_EXTS:
        return "video"
    if path.suffix.lower() in IMAGE_EXTS:
        return "image"
    return None


def glm_api_keys(env=None) -> list[str]:
    """GLM_API_KEY + GLM_API_KEY_2..9 — có bao nhiêu key dùng bấy nhiêu (PB3-B2:
    multi-key round-robin; key phải KHÁC tài khoản bigmodel, cùng tài khoản chung trần)."""
    if env is None:
        from dotenv import load_dotenv

        load_dotenv()
        env = os.environ
    keys = [env.get("GLM_API_KEY", "")]
    keys += [env.get(f"GLM_API_KEY_{i}", "") for i in range(2, 10)]
    return [k for k in keys if k]


def shrink_for_api(data: bytes, max_dim: int = 960, quality: int = 80) -> bytes:
    """Thu nhỏ frame TRƯỚC KHI gửi GLM (bug PB3-B2: upload 2 frame 1280px ~1MB/request
    chạy song song bị bigmodel cắt kết nối — SSLEOF/RemoteDisconnected; 960px/q80 còn
    83–175KB/request, đủ cho tag loại cảnh). Fail-open: bytes không decode được (test
    stub/file hỏng) trả nguyên — tagger cứ gửi, retry lo phần còn lại."""
    from PIL import Image

    try:
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.thumbnail((max_dim, max_dim))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()
    except Exception:
        return data


def extract_frames(video: Path, n: int = 2) -> list[bytes]:
    """Rút n frame JPEG trải đều (1/(n+1)...n/(n+1) thời lượng) bằng ffmpeg."""
    duration = ffprobe_duration(video) or 0.0
    frames: list[bytes] = []
    with tempfile.TemporaryDirectory() as td:
        for i in range(1, n + 1):
            ts = duration * i / (n + 1)
            out = Path(td) / f"f{i}.jpg"
            result = subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-ss", f"{ts:.2f}", "-i", str(video),
                 "-frames:v", "1", "-q:v", "4", "-vf", "scale='min(1280,iw)':-2", str(out)],
                capture_output=True, timeout=60,
            )
            if result.returncode == 0 and out.is_file():
                frames.append(out.read_bytes())
    if not frames:
        raise RuntimeError(f"ffmpeg không rút được frame từ {video}")
    return frames


def image_to_jpeg(image: Path, max_dim: int = 1280, quality: int = 85) -> bytes:
    """Đọc ảnh BẤT KỲ định dạng -> thu nhỏ cạnh dài ≤max_dim -> JPEG bytes.

    Ảnh gốc có thể 20-30MB (vượt trần 10MB của API) hoặc gắn sai đuôi (webp thực ra gif);
    PIL decode đúng định dạng thật + nén nhỏ lại nên gửi vision luôn hợp lệ.
    """
    from PIL import Image

    with Image.open(image) as im:
        im = im.convert("RGB")  # bỏ alpha/animation (gif -> frame đầu), chuẩn cho JPEG
        im.thumbnail((max_dim, max_dim))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()


def preview_images(media_path: Path) -> list[bytes]:
    """JPEG bytes đại diện asset (video: 2 frame, 1 nếu <2s — spec §3a; ảnh: 1) —
    rút 1 LẦN cho vision + đo màu."""
    mtype = media_type_of(media_path)
    if mtype == "video":
        # User chốt 2026-07-07 (sửa spec §3a): <10s = 1 frame GIỮA clip (cảnh cắt theo
        # mép editor gần như đồng nhất — 2 frame là trả tiền 2 lần cùng một hình);
        # ≥10s giữ 2 frame (clip dài mới có nguy cơ biến đổi nội dung).
        n = 1 if (ffprobe_duration(media_path) or 0.0) < 10.0 else 2
        return extract_frames(media_path, n=n)
    if mtype == "image":
        return [image_to_jpeg(media_path)]
    raise ValueError(f"Không hỗ trợ định dạng: {media_path}")


def measure_colors(images: list[bytes]) -> tuple[str, float, float]:
    """(dominant_color '#rrggbb', brightness 0-1, saturation 0-1) — trung bình các frame.

    Lớp RẺ C2b của b1: PIL thuần trên chính frame gửi vision, 0 token vision.
    """
    from PIL import Image, ImageStat

    if not images:
        raise ValueError("measure_colors cần ≥1 ảnh")
    r = g = b = s = v = 0.0
    for data in images:
        im = Image.open(io.BytesIO(data)).convert("RGB")
        mr, mg, mb = ImageStat.Stat(im).mean
        _, ms, mv = ImageStat.Stat(im.convert("HSV")).mean
        r, g, b, s, v = r + mr, g + mg, b + mb, s + ms, v + mv
    n = len(images)
    hexcolor = f"#{round(r / n):02x}{round(g / n):02x}{round(b / n):02x}"
    return hexcolor, round(v / n / 255, 3), round(s / n / 255, 3)


def _tag_instruction(mtype: str, folder_context: str, want_angle: bool,
                     source_title: str = "", section_hint: str = "",
                     topic: str = "") -> str:
    """Instruction chung cho cả 2 engine — schema Pydantic mới là hàng rào cuối."""
    text = (
        "Tag this stock footage asset for an internal video-editing library. "
        "Frames are from the same clip." if mtype == "video" else
        "Tag this image asset for an internal video-editing library."
    )
    text += (
        f"\n\nFor `mood` pick 1-2 words ONLY from: {', '.join(sorted(MOOD))}."
        f"\nFor `scene_type` pick the dominant setting from the allowed values."
    )
    # 2b (C đợt 1, 2026-07-09 — NHAT_KY §C6-DIEU-TRA): GLM từng nhìn 1 frame khối cầu
    # xám rỗ của Pluto và tag chắc nịch "moon" -> mọi tầng sau (match, phễu, veto V3)
    # sai theo. Luật không-đoán: không chắc thì dùng từ CHUNG, đừng nêu tên riêng.
    text += (
        "\n\nNever name a specific celestial body or landmark you cannot verify from "
        "the pixels alone. A grey cratered or hazy sphere could be the Moon, Pluto, "
        "Mercury or another body — unless it is unmistakable (Earth with continents, "
        "Saturn with rings), use generic terms like 'planet', 'cratered surface' or "
        "'celestial body' instead of guessing a name."
    )
    # 2a: tiêu đề video NGUỒN (clip cắt ra từ ống nạp) = gợi ý chủ đề mạnh — YẾU hơn
    # ground-truth folder bên dưới (tiêu đề nói về chủ đề video, không chắc từng cảnh).
    if source_title:
        text += (
            f"\n\nThis clip was cut from a source video titled: \"{source_title}\". "
            "Treat that title as a strong hint about the TOPIC. If the title names a "
            "specific celestial body or place, do NOT tag a DIFFERENT specific one "
            "unless it is unmistakably visible — prefer the title's subject or generic "
            "terms. If the title looks like an internal code or meaningless file name, "
            "ignore it."
        )
    # §3i-2 (ytref): chapter YouTube chứa cảnh — CÙNG BẬC tin cậy source_title (gợi ý
    # về ĐOẠN, không chắc từng cảnh; giải ca video nhiều thực thể theo chương).
    if section_hint:
        text += (
            f"\n\nWithin that source video, this clip falls in the chapter titled: "
            f"\"{section_hint}\". Treat it like the source title: a strong hint about "
            "this SECTION's subject, not a certainty for this exact clip — if the "
            "pixels clearly contradict it, describe what you see."
        )
    # §3i-3: 1 dòng chủ đề editor khai qua --topic (ca tên file là mã số) — cùng bậc
    # source_title, KHÔNG phải ground truth từng cảnh.
    if topic:
        text += (
            f"\n\nThe editor states this batch of source footage is about: \"{topic}\". "
            "Treat it with the same trust as a source-video title: a strong hint about "
            "the TOPIC, not a guarantee for every single clip."
        )
    if want_angle:
        text += ("\nFor `camera_angle` judge the camera height relative to the subject; "
                 "use \"unknown\" if unsure.")
    else:
        text += "\nSet `camera_angle` to \"unknown\"."
    if folder_context:
        # Folder do editor đặt = SỰ THẬT về địa danh/thực thể (vision không tự suy ra
        # từ pixel được). Bắc cầu ngôn ngữ: folder tiếng Việt -> tag tiếng Anh có địa danh.
        text += (
            f"\n\nThe editor filed this asset under the folder path: \"{folder_context}\". "
            "Treat that path as GROUND TRUTH for the location / entity / topic — the editor "
            "knows what it depicts even when you cannot identify the exact place from pixels "
            "alone. In subject, description and tags, INCLUDE the place/entity names from that "
            "path, normalized to English (e.g. a Vietnamese folder naming Cambodia -> add "
            "'Cambodia'). Still describe only what you actually SEE; never invent details."
        )
    return text


def _clean_json(text: str) -> str:
    """Làm sạch JSON model trả về (code fence, lời dẫn, trailing comma) — learn từ nhan ban."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start: end + 1]
    return re.sub(r",(\s*[}\]])", r"\1", text)


class GLMVisionTagger:
    """Tagger mặc định: GLM-4.6V qua endpoint NATIVE, thinking TẮT (xem chú thích GLM_NATIVE_URL).

    Schema nhét vào system, parse JSON tay + retry backoff (429/5xx/đứt kết nối/JSON vỡ).
    """

    def __init__(self, model: str = DEFAULT_GLM_VISION_MODEL, api_key: str | None = None,
                 timeout: float = 120.0, want_angle: bool = False) -> None:
        from dotenv import load_dotenv

        load_dotenv()
        self.model = model
        self.want_angle = want_angle
        self._timeout = timeout
        self._api_key = api_key or os.getenv("GLM_API_KEY")
        if not self._api_key:
            raise RuntimeError("Thiếu GLM_API_KEY trong .env (bigmodel.cn)")

    def tag(self, media_path: Path, folder_context: str = "",
            images: list[bytes] | None = None, source_title: str = "",
            section_hint: str = "", topic: str = "") -> AssetTags:
        mtype = media_type_of(media_path)
        if mtype is None:
            raise ValueError(f"Không hỗ trợ định dạng: {media_path}")
        imgs = images if images is not None else preview_images(media_path)
        # PB3-B2: LUÔN thu 960px trước khi gửi (frame gốc 1280px caller vẫn giữ để đo màu)
        imgs = [shrink_for_api(x) for x in imgs]
        schema = json.dumps(AssetTags.model_json_schema(), ensure_ascii=False)
        # Bug PB3: GLM-4.6V thỉnh thoảng CHÉP NGUYÊN SCHEMA thay vì trả instance —
        # NGẪU NHIÊN theo call (server không deterministic dù temperature=0). Chống echo
        # 2 lớp: ví dụ instance trong system + user text nói rõ "không chép schema"
        # (probe PB3: 0/8 pass trước fix -> 6/6 pass sau fix). Example build từ chính
        # AssetTags để schema đổi là example đổi theo (không lệch pha).
        example = AssetTags(
            subject="sunset beach",
            description="Waves rolling onto a sandy beach at sunset.",
            shot_size="wide", scene_type="nature_water", mood=["peaceful"],
            camera_angle="eye_level" if self.want_angle else "unknown",
            has_people=False, tags=["beach", "sunset", "waves", "sand", "ocean"],
        ).model_dump_json()
        system = (_tag_instruction(mtype, folder_context, self.want_angle, source_title,
                                   section_hint, topic)
                  + "\n\nReturn ONLY one valid JSON object matching this schema. "
                    "No prose/markdown/fences.\nSchema:\n" + schema
                  + "\n\nExample of a CORRECT output for a DIFFERENT asset (a beach clip) — "
                    "return the same SHAPE but with values for the actual asset:\n" + example)
        content: list[dict] = [
            {"type": "image_url",
             "image_url": {"url": "data:image/jpeg;base64,"
                                  + base64.standard_b64encode(img).decode("ascii")}}
            for img in imgs
        ]
        base_text = ("Tag the asset shown in the image(s) above. Output the JSON INSTANCE "
                     "with actual values describing THIS asset. "
                     "Do NOT output the schema itself.")
        content.append({"type": "text", "text": base_text})
        body = {
            "model": self.model, "temperature": 0, "max_tokens": 800,
            "thinking": {"type": "disabled"},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": content}],
        }
        last: Exception | None = None
        for attempt in range(4):
            try:
                d = self._post(body)
                msg = (d.get("choices") or [{}])[0].get("message", {}) or {}
                text = (msg.get("content") or "").strip()
                if not text:
                    raise ValueError("GLM vision trả content rỗng")
                return AssetTags.model_validate_json(_clean_json(text))
            except urllib.error.HTTPError as exc:
                last = exc
                if nen_thu_lai(exc.code) and attempt < 3:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                # 400 kèm body nói rõ lý do (PB4: contentFilter 1301 chặn frame "nhạy
                # cảm" — dai dẳng mọi key, KHÔNG retry được) -> đưa body vào lỗi cho
                # kill-log đọc được, khỏi mù "Bad Request".
                try:
                    detail = exc.read()[:200].decode("utf-8", "replace")
                except Exception:
                    detail = ""
                raise RuntimeError(f"GLM HTTP {exc.code} với {media_path.name}: "
                                   f"{detail or exc.reason}") from exc
            except ValidationError as exc:
                # Bug PB4: retry MÙ không cứu được lỗi model "khăng khăng" (vd clip đồ ăn
                # đòi mood 'appetizing'/'cozy' ngoài vocab 19 từ — fail đủ 4 lần, đốt 4 call).
                # Nhét CHÍNH lỗi validation vào lượt sau cho model tự sửa (feedback-retry).
                last = exc
                if attempt < 3:
                    content[-1]["text"] = (
                        base_text + "\n\nYour previous output failed validation:\n"
                        + str(exc)[:400]
                        + "\nReturn the corrected JSON instance (use ONLY allowed values).")
                    time.sleep(1.0 * (attempt + 1))
                    continue
            except Exception as exc:  # noqa: BLE001 — đứt kết nối / rỗng -> retry
                last = exc
                if attempt < 3:
                    time.sleep(1.0 * (attempt + 1))
                    continue
        raise RuntimeError(f"GLM vision thất bại sau 4 lần với {media_path.name}: {last!r}")

    def _post(self, body: dict) -> dict:
        """HTTP call tách riêng để test stub được."""
        req = urllib.request.Request(
            glm_api_url(), data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": "Bearer " + self._api_key,
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            return json.load(resp)


class ClaudeVisionTagger:
    """Fallback: Claude vision + structured output (cần ANTHROPIC_API_KEY)."""

    def __init__(self, model: str = DEFAULT_VISION_MODEL, want_angle: bool = False) -> None:
        from dotenv import load_dotenv

        load_dotenv()
        import anthropic

        self._client = anthropic.Anthropic()
        self.model = model
        self.want_angle = want_angle

    def tag(self, media_path: Path, folder_context: str = "",
            images: list[bytes] | None = None, source_title: str = "",
            section_hint: str = "", topic: str = "") -> AssetTags:
        mtype = media_type_of(media_path)
        if mtype is None:
            raise ValueError(f"Không hỗ trợ định dạng: {media_path}")
        imgs = images if images is not None else preview_images(media_path)

        # mọi ảnh gửi đi đều đã là JPEG (frame video hoặc ảnh đã chuẩn hoá)
        content: list[dict] = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(img).decode(),
                },
            }
            for img in imgs
        ]
        content.append({"type": "text",
                        "text": _tag_instruction(mtype, folder_context, self.want_angle,
                                                 source_title, section_hint, topic)})
        response = self._client.messages.parse(
            model=self.model,
            max_tokens=1024,
            temperature=0,
            messages=[{"role": "user", "content": content}],
            output_format=AssetTags,
        )
        if response.parsed_output is None:
            raise ValueError(f"Vision không tag được {media_path} (stop={response.stop_reason})")
        return response.parsed_output
