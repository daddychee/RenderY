"""Backend LLM đạo diễn ĐI QUA CLAUDE CODE (subscription, KHÔNG API key metered).

Cắm vào Protocol DirectorClient (client.py) — run_direct/schema/validator/prompts
giữ NGUYÊN. Đây là "đường ống chung" cho cả Level 2 (hội thoại) lẫn Level 1 (batch).

Cơ chế (đã kiểm thực nghiệm 2026-07-01, claude 2.1.89 trên Windows):
- `claude -p --output-format json --json-schema <schema> --tools "" --model <m>`
- prompt đẩy qua STDIN (không giới hạn độ dài dòng lệnh Windows).
- Kết quả đã validate nằm ở trường `structured_output`; token ở `usage`.
- ĐẢM BẢO subscription: xoá ANTHROPIC_API_KEY khỏi env con (nếu set, key ĐÈ OAuth →
  tính tiền metered). KHÔNG dùng --bare (bare ép auth chỉ bằng API key, tắt OAuth).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Optional, TypeVar

from pydantic import BaseModel

from autoedit.director.client import Usage, _clean_json

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = "sonnet"  # alias -> model Sonnet mới nhất (help claude: 'sonnet'/'opus'...)


class ClaudeCodeDirectorClient:
    """Backend đạo diễn qua Claude Code CLI. Trả (object đã validate, usage)."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        log_dir: Optional[Path] = None,
        claude_bin: str = "claude",
        timeout: int = 600,
        thinking: bool = True,
    ) -> None:
        self.model = model
        self.log_dir = log_dir
        self.claude_bin = claude_bin
        self.timeout = timeout
        # PA-2 (2026-07-07): phễu rank tắt thinking — đo thật 45 call: ~75% của 3.9k
        # output token/call là thinking; extraction có schema không cần (bài học GLM PB3).
        # Direct/enrich (chia beat — suy luận nặng) giữ thinking mặc định.
        self.thinking = thinking
        self._call_count = 0
        self._log_lock = threading.Lock()  # TOC-2: phễu gọi song song nhiều call

    # -- Protocol DirectorClient -------------------------------------------
    def complete(
        self, system: str, user: str, output_model: type[T], context: str | None = None
    ) -> tuple[T, Usage]:
        # Gộp system + (context = toàn văn script) + user vào 1 blob stdin. Ranh giới
        # system/user không quan trọng ở call completion; --json-schema đã ép cấu trúc.
        parts = [system]
        if context:
            parts.append(context)
        parts.append(user)
        prompt = "\n\n".join(parts)

        obj, usage = self._run(prompt, output_model.model_json_schema())
        parsed = output_model.model_validate(obj)
        self._log(prompt, output_model.__name__, parsed, usage)
        return parsed, usage

    def complete_grounded(
        self, system: str, user: str, output_model: type[T]
    ) -> tuple[T, Usage]:
        """Enrich web-grounded CHƯA hỗ trợ qua Claude Code (không cần cho A3).
        Chạy enrich KHÔNG --web (kiến thức nội tại) dùng complete() bình thường."""
        raise NotImplementedError(
            "web-grounded enrich chưa hỗ trợ qua Claude Code — chạy `enrich` không "
            "--web (kiến thức nội tại), hoặc bỏ qua stage enrich."
        )

    # -- nội bộ ------------------------------------------------------------
    def _invocation(self) -> list[str]:
        """Cách gọi Claude Code, tránh shim .cmd trên Windows.

        npm cài `claude` = batch shim claude.CMD. Chạy .cmd qua subprocess bị cmd.exe
        parse lại → JSON schema (đầy " { }) vỡ (lộ dạng lỗi "'build' is not recognized" —
        cmd.exe cắt vụn command line). Nên gọi THẲNG binary thật, bỏ qua shim:
        - Bản CLI mới (>=2.x) đóng gói native `bin/claude.exe` cạnh package — ưu tiên cái này.
        - Bản cũ hơn dùng `cli.js` chạy qua `node` — lùi về nếu không thấy .exe.
        Unix: `claude` chạy thẳng, không qua nhánh này."""
        exe = shutil.which(self.claude_bin)
        if exe and exe.lower().endswith((".cmd", ".bat")):
            pkg_dir = Path(exe).parent / "node_modules" / "@anthropic-ai" / "claude-code"
            native_exe = pkg_dir / "bin" / "claude.exe"
            if native_exe.is_file():
                return [str(native_exe)]
            cli_js = pkg_dir / "cli.js"
            node = shutil.which("node")
            if cli_js.is_file() and node:
                return [node, str(cli_js)]
        return [exe or self.claude_bin]

    def _run(self, prompt: str, schema: dict) -> tuple[dict, Usage]:
        cmd = [
            *self._invocation(), "-p",
            "--output-format", "json",
            "--json-schema", json.dumps(schema, ensure_ascii=False),
            "--tools", "",              # tắt mọi tool -> 1 phát, không lặp agentic
            "--model", self.model,
        ]
        env = dict(os.environ)
        env.pop("ANTHROPIC_API_KEY", None)  # ép subscription, không dùng key metered
        if not self.thinking:
            env["MAX_THINKING_TOKENS"] = "0"  # PA-2: tắt extended thinking cho call extraction

        try:
            r = subprocess.run(
                cmd, input=prompt, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=self.timeout, env=env,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"Không tìm thấy '{self.claude_bin}' — cài Claude Code + đăng nhập "
                "subscription (`claude` chạy tương tác được là đủ)."
            ) from exc

        if r.returncode != 0:
            raise RuntimeError(
                f"claude -p exit {r.returncode}: {(r.stderr or '')[:500]}"
            )

        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"claude -p trả stdout không phải JSON: {r.stdout[:500]}"
            ) from exc

        if data.get("is_error") or data.get("subtype") != "success":
            raise RuntimeError(f"claude -p báo lỗi: {data.get('result') or data}")

        obj = data.get("structured_output")
        if obj is None:  # đường lui: schema bị bỏ qua -> parse text 'result'
            obj = json.loads(_clean_json(data.get("result", "")))

        u = data.get("usage", {})
        usage = Usage(
            input_tokens=u.get("input_tokens", 0) or 0,
            output_tokens=u.get("output_tokens", 0) or 0,
            cache_read_input_tokens=u.get("cache_read_input_tokens", 0) or 0,
            cache_creation_input_tokens=u.get("cache_creation_input_tokens", 0) or 0,
        )
        return obj, usage

    def _log(self, prompt: str, schema: str, parsed: BaseModel, usage: Usage) -> None:
        if self.log_dir is None:
            return
        with self._log_lock:  # TOC-2: 2 thread cùng tăng count -> đè file nhau
            self._call_count += 1
            n = self._call_count
        self.log_dir.mkdir(parents=True, exist_ok=True)
        (self.log_dir / f"direct_cc_{n:02d}_{schema}.json").write_text(
            json.dumps(
                {
                    "engine": "claude-code",
                    "model": self.model,
                    "schema": schema,
                    "usage": {"input": usage.input_tokens, "output": usage.output_tokens},
                    "prompt": prompt,
                    "response": parsed.model_dump(mode="json"),
                },
                indent=2, ensure_ascii=False,
            ),
            encoding="utf-8",
        )
