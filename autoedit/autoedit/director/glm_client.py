r"""Backend LLM đạo diễn chạy GLM (z.ai) — API metered, KHÔNG qua Claude Code.

Cắm vào Protocol DirectorClient (client.py): run_direct/schema/validator/prompts giữ
NGUYÊN. Đo thật 30/08/2026 trên đúng prompt ChapterBeats của job LI093 (6090 token
vào), so với backend claude-code đang dùng:

    claude -p (subscription)          ~120 s/lần, $1.31 cho 8 lần của 1 hook
    GLM-5.3                              7.8 s/lần, 5/5 hợp lệ

HAI ĐIỀU BẮT BUỘC, cả hai đều tìm ra bằng đo chứ không suy đoán:

1. `reasoning_effort="low"`. GLM-5.3 luôn bật thinking; API từ chối
   `thinking={"type":"disabled"}` (mã 1210) và cũng từ chối cả low/high/max mà chính
   nó gợi ý. Chỉ `reasoning_effort` mới thật sự tắt (reasoning_tokens = 0). Không
   đặt thì nó nuốt trọn max_tokens vào phần suy nghĩ: 88 s và JSON CỤT.

2. Schema nhồi vào PROMPT, không dựa vào `response_format`. GLM nhận
   `response_format={"type":"json_schema"}` nhưng KHÔNG ép theo — đo 10 lần với
   json_schema/json_object đều 0/10 hợp lệ (thiếu trường energy/visual_level/
   search_queries). Cùng prompt + schema dán vào cuối: 5/5.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, TypeVar

from pydantic import BaseModel

from autoedit.director.client import Usage, _clean_json

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = "glm-5.3"
# Server QUỐC TẾ (cùng khuôn library/vision.py: đo thật nhanh hơn open.bigmodel.cn
# từ VN). Đổi được bằng env nếu z.ai chặn.
GLM_URL = os.getenv("GLM_API_URL", "https://api.z.ai/api/paas/v4/chat/completions")

# Giá GLM-5.3 (USD / 1M token) — dùng để BÁO chi phí, không ảnh hưởng kết quả dựng.
PRICE_INPUT_PER_M = 0.6
PRICE_OUTPUT_PER_M = 2.2

_YEU_CAU_JSON = (
    "\n\n## BẮT BUỘC ĐỊNH DẠNG\n"
    "Trả về DUY NHẤT một object JSON hợp lệ đúng schema dưới đây. Không thiếu trường "
    "nào, không thêm chữ nào ngoài JSON, không markdown, không dấu phẩy thừa.\n"
    "Schema:\n"
)


def _don_rac(x):
    """Bỏ phần tử RÁC trong mọi danh sách lồng nhau (đệ quy).

    Rác = chuỗi rỗng/None nằm giữa các object hợp lệ. GLM sinh ra khi trả danh sách
    dài (đo 02/09: verdicts[7] = '' trong lượt chấm 20 beat). Chỉ bỏ phần tử VÔ
    NGHĨA — không đụng tới dữ liệu thật, nên không che được lỗi nội dung.
    """
    if isinstance(x, list):
        return [_don_rac(v) for v in x
                if not (v is None or (isinstance(v, str) and not v.strip()))]
    if isinstance(x, dict):
        return {k: _don_rac(v) for k, v in x.items()}
    return x


class GLMDirectorClient:
    """Backend đạo diễn qua GLM API. Trả (object đã validate, usage)."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        log_dir: Optional[Path] = None,
        max_tokens: int = 16000,
        api_key: Optional[str] = None,
        timeout: int = 300,
        retries: int = 3,
    ) -> None:
        key = api_key or os.getenv("GLM_API_KEY") or os.getenv("LLM_API_KEY")
        if not key:
            raise RuntimeError(
                "Thiếu khoá GLM — đặt GLM_API_KEY (hoặc LLM_API_KEY). Trên máy chủ, "
                "khoá lấy từ két V3: General › API Keys › rendery › chia_beat."
            )
        self._key = key
        self.model = model
        self.max_tokens = max_tokens
        self.log_dir = log_dir
        self.timeout = timeout
        self.retries = retries
        self._call_count = 0

    # ---------------------------------------------------------------- gọi API
    def _goi(self, messages: list[dict]) -> dict:
        body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0,
            # xem docstring: KHÔNG bỏ dòng này
            "reasoning_effort": "low",
            "response_format": {"type": "json_object"},
        }
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        loi: Exception | None = None
        for lan in range(self.retries):
            req = urllib.request.Request(
                GLM_URL, data=data, method="POST",
                headers={"Authorization": f"Bearer {self._key}",
                         "Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                chi_tiet = exc.read().decode("utf-8", "replace")[:300]
                loi = RuntimeError(f"GLM HTTP {exc.code}: {chi_tiet}")
                # 4xx (trừ 429) là lỗi yêu cầu — thử lại cũng vậy
                if 400 <= exc.code < 500 and exc.code != 429:
                    raise loi from exc
            except Exception as exc:      # mạng chập chờn / timeout
                loi = exc
            if lan < self.retries - 1:
                time.sleep(2 ** lan)
        raise RuntimeError(f"GLM lỗi sau {self.retries} lần: {loi}")

    def complete(self, system: str, user: str, output_model: type[T],
                 context: str | None = None) -> tuple[T, Usage]:
        schema = json.dumps(output_model.model_json_schema(), ensure_ascii=False)
        noi_dung = "\n\n".join(x for x in (context, user) if x)
        messages = [
            {"role": "system", "content": system + _YEU_CAU_JSON + schema},
            {"role": "user", "content": noi_dung},
        ]
        r = self._goi(messages)
        text = (r["choices"][0]["message"].get("content") or "").strip()
        if not text:
            raise ValueError(
                f"GLM trả nội dung RỖNG cho {output_model.__name__} "
                f"(finish_reason={r['choices'][0].get('finish_reason')})"
            )
        try:
            parsed = output_model.model_validate_json(_clean_json(text))
        except Exception as exc:
            # GLM thỉnh thoảng chèn PHẦN TỬ RÁC vào danh sách — đo thật 02/09:
            # `verdicts[7]` là chuỗi rỗng '' giữa các object hợp lệ, giết cả lượt
            # chấm 20 beat. Lỗi HÌNH THỨC, không phải nội dung: dọn rồi validate lại
            # còn hơn vứt bỏ 19 phán quyết đúng.
            try:
                parsed = output_model.model_validate(
                    _don_rac(json.loads(_clean_json(text))))
            except Exception:
                raise ValueError(
                    f"GLM không trả được {output_model.__name__} hợp lệ: {exc}"
                ) from exc

        u = r.get("usage") or {}
        usage = Usage(input_tokens=int(u.get("prompt_tokens") or 0),
                      output_tokens=int(u.get("completion_tokens") or 0),
                      price_input_per_m=PRICE_INPUT_PER_M,
                      price_output_per_m=PRICE_OUTPUT_PER_M)
        self._log(system, noi_dung, output_model.__name__, parsed, usage)
        return parsed, usage

    def complete_grounded(self, system: str, user: str, output_model: type[T]) -> tuple[T, Usage]:
        """GLM không có web search tool — chạy như complete (stage enrich mất phần
        tra web). Enrich vốn PHẢI duyệt tay trước khi render nên không âm thầm sai."""
        return self.complete(system, user, output_model)

    def _log(self, system: str, user: str, schema: str, parsed: BaseModel, usage: Usage) -> None:
        if self.log_dir is None:
            return
        self._call_count += 1
        self.log_dir.mkdir(parents=True, exist_ok=True)
        path = self.log_dir / f"direct_glm_{self._call_count:02d}_{schema}.json"
        path.write_text(
            json.dumps({"engine": "glm", "model": self.model, "schema": schema,
                        "usage": {"input": usage.input_tokens,
                                  "output": usage.output_tokens, "usd": round(usage.usd, 6)},
                        "system": system, "user": user,
                        "response": parsed.model_dump(mode="json")},
                       indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
