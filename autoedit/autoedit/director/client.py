"""Client Claude API cho LLM đạo diễn — interface tách rời để test bằng fake.

- structured output qua messages.parse(output_format=PydanticModel) — API ép schema
- temperature=0 (tái lập tương đối, RA_SOAT 2.7); không có seed
- log mọi request/response vào project_dir/llm_log/ để truy vết
- trả usage để runner ghi CostEntry (rủi ro chi phí — KE_HOACH mục 6)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol, TypeVar

from pydantic import BaseModel


def _clean_json(text: str) -> str:
    """Làm sạch JSON model trả về để parser nghiêm ngặt nuốt được.

    Xử lý các lỗi cú pháp vặt model hay sinh ở output dài:
    - bọc trong code fence ```json ... ```
    - chữ thừa trước/sau object
    - trailing comma: dấu , ngay trước } hoặc ] (nguyên nhân lỗi gốc)
    """
    text = text.strip()
    # bỏ code fence nếu có
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    # cắt lấy từ { đầu tiên tới } cuối cùng (bỏ lời dẫn nếu model thêm)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    # bỏ trailing comma trước } hoặc ] — kể cả khi có khoảng trắng/xuống dòng
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return text

DEFAULT_MODEL = "claude-sonnet-4-6"
# Giá claude-sonnet-4-6 (USD / 1M token, tra 11/06/2026) — cập nhật khi đổi model
PRICE_INPUT_PER_M = 3.0
PRICE_OUTPUT_PER_M = 15.0
WEB_SEARCH_USD = 0.01          # phí web search tool: $10 / 1.000 lượt (Anthropic)

T = TypeVar("T", bound=BaseModel)


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    web_searches: int = 0      # số lượt web search (tính phí riêng ngoài token)
    cache_read_input_tokens: int = 0       # token đọc từ cache (rẻ ~0.1x)
    cache_creation_input_tokens: int = 0   # token ghi vào cache (~1.25x)

    @property
    def usd(self) -> float:
        return (
            self.input_tokens * PRICE_INPUT_PER_M
            + self.cache_read_input_tokens * PRICE_INPUT_PER_M * 0.1      # đọc cache: 10% giá input
            + self.cache_creation_input_tokens * PRICE_INPUT_PER_M * 1.25  # ghi cache: 125% giá input
            + self.output_tokens * PRICE_OUTPUT_PER_M
        ) / 1_000_000 + self.web_searches * WEB_SEARCH_USD


class DirectorClient(Protocol):
    """Backend LLM. Mọi backend trả (object đã validate, usage)."""

    model: str

    def complete(self, system: str, user: str, output_model: type[T],
                 context: str | None = None) -> tuple[T, Usage]: ...

    def complete_grounded(self, system: str, user: str, output_model: type[T]) -> tuple[T, Usage]:
        """Như complete nhưng tra WEB trước để lấy số thật + nguồn (stage enrich)."""
        ...


class ClaudeDirectorClient:
    """Backend thật: Anthropic API, key từ .env (python-dotenv)."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        log_dir: Optional[Path] = None,
        max_tokens: int = 16000,
        cache_prompts: bool = True,
    ) -> None:
        from dotenv import load_dotenv

        load_dotenv()  # tìm .env từ cwd lên trên — không bao giờ hardcode key
        import anthropic

        self._client = anthropic.Anthropic()
        self.model = model
        self.max_tokens = max_tokens
        self.log_dir = log_dir
        # Prompt caching: cache system prompt (luật đạo diễn ~3000 token lặp lại mỗi chương).
        # KHÔNG đổi nội dung gửi đi -> output y nguyên, chỉ rẻ hơn. Tắt được để A/B test.
        self.cache_prompts = cache_prompts
        self._call_count = 0

    def _system_arg(self, system: str):
        """System prompt, kèm cache_control nếu bật caching. Cùng NỘI DUNG dù bật/tắt."""
        if self.cache_prompts:
            return [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        return system

    def _user_content(self, user: str, context: str | None):
        """Nội dung message user. Có context (vd TOÀN VĂN script) -> đặt thành KHỐI riêng
        đứng trước, gắn cache_control khi bật caching. Khối này GIỐNG NHAU mọi chương nên
        được cache, các chương sau đọc lại ~0.1x giá (xem prompts.full_script_context)."""
        if not context:
            return user
        ctx_block = {"type": "text", "text": context}
        if self.cache_prompts:
            ctx_block["cache_control"] = {"type": "ephemeral"}
        return [ctx_block, {"type": "text", "text": user}]

    def complete(self, system: str, user: str, output_model: type[T],
                 context: str | None = None) -> tuple[T, Usage]:
        try:
            response = self._client.messages.parse(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0,
                system=self._system_arg(system),
                messages=[{"role": "user", "content": self._user_content(user, context)}],
                output_format=output_model,
            )
            parsed = response.parsed_output
            if parsed is None:
                raise ValueError(
                    f"LLM không trả được {output_model.__name__} hợp lệ "
                    f"(stop_reason={response.stop_reason})"
                )
            usage = Usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                cache_read_input_tokens=getattr(response.usage, "cache_read_input_tokens", 0) or 0,
                cache_creation_input_tokens=getattr(response.usage, "cache_creation_input_tokens", 0) or 0,
            )
        except Exception:
            # messages.parse() dùng parser JSON nghiêm ngặt, crash khi model sinh
            # JSON hơi lệch chuẩn (trailing comma...). Fallback: lấy JSON thô,
            # làm sạch rồi validate tay.
            parsed, usage = self._complete_repair(system, user, output_model, context)
        self._log(system, user, output_model.__name__, parsed, usage)
        return parsed, usage

    def _complete_repair(self, system: str, user: str, output_model: type[T],
                         context: str | None = None) -> tuple[T, Usage]:
        """Đường lui khi messages.parse() vỡ vì JSON lệch chuẩn.

        Gọi messages.create() để lấy text thô → _clean_json() → validate bằng
        Pydantic. Không dùng output_format nên không bị parser SDK chặn trước.
        """
        schema = json.dumps(output_model.model_json_schema(), ensure_ascii=False)
        system2 = (
            system
            + "\n\nReturn ONLY one valid JSON object matching this schema. "
            "No prose, no markdown, no code fences, and NO trailing commas.\n"
            "Schema:\n" + schema
        )
        r = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=0,
            system=system2,
            messages=[{"role": "user", "content": self._user_content(user, context)}],
        )
        text = "".join(b.text for b in r.content if getattr(b, "type", None) == "text")
        cleaned = _clean_json(text)
        try:
            parsed = output_model.model_validate_json(cleaned)
        except Exception as exc:
            raise ValueError(
                f"LLM không trả được {output_model.__name__} hợp lệ kể cả sau khi "
                f"làm sạch JSON: {exc}"
            ) from exc
        usage = Usage(
            input_tokens=r.usage.input_tokens,
            output_tokens=r.usage.output_tokens,
        )
        return parsed, usage

    def complete_grounded(self, system: str, user: str, output_model: type[T]) -> tuple[T, Usage]:
        """2 pass: (1) web_search gom số thật + nguồn; (2) parse structured từ findings.
        Tách web search (free-form) khỏi structured output để chắc cú."""
        try:
            r1 = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system + "\n\nUSE web_search to find any REAL numbers needed; "
                "report findings WITH their source names. Do not invent numbers.",
                messages=[{"role": "user", "content": user}],
                tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
            )
        except Exception as exc:  # tool chưa bật / lỗi mạng -> báo rõ, KHÔNG bịa số
            raise RuntimeError(
                f"web_search không khả dụng ({exc}) — stage enrich cần web search để lấy "
                "số thật. Bật web search cho API key hoặc bỏ qua enrich."
            ) from exc
        findings = "".join(
            b.text for b in r1.content if getattr(b, "type", None) == "text"
        )
        # đếm lượt search (tính phí $0.01/lượt): ưu tiên server_tool_use, fallback đếm block
        n_search = 0
        stu = getattr(r1.usage, "server_tool_use", None)
        if stu is not None:
            n_search = getattr(stu, "web_search_requests", 0) or 0
        if not n_search:
            n_search = sum(1 for b in r1.content
                           if getattr(b, "type", None) == "web_search_tool_result")
        u1 = Usage(r1.usage.input_tokens, r1.usage.output_tokens, web_searches=n_search)
        # Pass 2: ép schema từ findings (số + nguồn đã có)
        user2 = (
            user + "\n\nWEB RESEARCH FINDINGS (dùng các số THẬT + ghi nguồn vào "
            f"source_note):\n{findings}"
        )
        parsed, u2 = self.complete(system, user2, output_model)
        return parsed, Usage(u1.input_tokens + u2.input_tokens,
                             u1.output_tokens + u2.output_tokens,
                             web_searches=u1.web_searches)

    def _log(self, system: str, user: str, schema: str, parsed: BaseModel, usage: Usage) -> None:
        """Lưu prompt + response để truy vết/so sánh khi tinh chỉnh prompt (2.7)."""
        if self.log_dir is None:
            return
        self._call_count += 1
        self.log_dir.mkdir(parents=True, exist_ok=True)
        path = self.log_dir / f"direct_{self._call_count:02d}_{schema}.json"
        path.write_text(
            json.dumps(
                {
                    "model": self.model,
                    "schema": schema,
                    "usage": {"input": usage.input_tokens, "output": usage.output_tokens,
                              "usd": round(usage.usd, 6)},
                    "system": system,
                    "user": user,
                    "response": parsed.model_dump(mode="json"),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
