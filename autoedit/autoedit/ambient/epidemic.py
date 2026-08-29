"""Client Epidemic Sound MCP — tải SFX trả phí về kho ambient per-niche.

Kho SFX local mỏng (life-in 306 file, nhiều kind 0 file). Epidemic có ~250k SFX
tag chuẩn theo LOÀI/vật thể — đúng chỗ RD-89 hụt (lạc đà nghe tiếng chim).

ĐƯỜNG ĐI: search MCP -> tải MP3/WAV vào folder tạm -> sinh ambient_manifest.yaml
-> `ambient.library.import_from_manifest` (chuẩn hóa WAV PCM 48k, luật C4).
KHÔNG tự ghi vào kho: mọi luật đặt tên/biến thể/records nằm ở library.py, một chỗ.

3 BẪY (đo thật 2026-07-18):
- `term` nằm LỒNG trong `query` — để cấp trên cùng thì server LẶNG LẼ bỏ qua, trả
  danh sách mặc định (mọi term ra cùng kết quả). Không lỗi, không cảnh báo.
- assetUrl HẾT HẠN ~60s: lấy link xong phải tải NGAY, không cache lại được.
- API key hết hạn 30 NGÀY -> 401. Bắt riêng, báo cách tạo lại, đừng chết câm.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

MCP_URL = "https://www.epidemicsound.com/a/mcp-service/mcp"
PROTOCOL_VERSION = "2025-03-26"
DOWNLOAD_TIMEOUT = 180
KEY_HELP = ("Tạo key mới tại https://www.epidemicsound.com/account/api-keys "
            "(key Epidemic hết hạn sau 30 ngày) rồi cập nhật EPIDEMIC_API_KEY trong .env")


class EpidemicError(RuntimeError):
    """Lỗi gọi Epidemic — thông điệp đã tiếng Việt, CLI in thẳng."""


@dataclass
class SoundEffect:
    id: str
    title: str
    duration_s: float

    @property
    def slug(self) -> str:
        """Tên file thô an toàn — chỉ để đặt tên tạm, tên KHO do library._next_name lo.

        BẮT BUỘC gắn đuôi id: title Epidemic hay dài và trùng nhau ở phần đầu
        ("...Farmers Market, Vendors Shouting, People T|alking 01/02"), cắt 60 ký tự
        là RA CÙNG MỘT TÊN -> file sau ĐÈ file trước trong folder tạm -> nạp 2 bản y
        hệt vào kho (md5 trùng). Đã dính thật với market_8/9 + boat_9/10 (2026-07-18).
        """
        keep = [c if c.isalnum() else "_" for c in self.title.lower()]
        base = "".join(keep).strip("_")[:60] or "sfx"
        return f"{base}_{self.id[:8]}"


def api_key(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    from dotenv import load_dotenv

    load_dotenv()
    key = os.environ.get("EPIDEMIC_API_KEY", "").strip()
    if not key:
        raise EpidemicError(f"Thiếu EPIDEMIC_API_KEY trong .env. {KEY_HELP}")
    return key


class EpidemicClient:
    """Phiên MCP: initialize -> notifications/initialized -> tools/call."""

    def __init__(self, key: str | None = None) -> None:
        self.key = api_key(key)
        self._sid: str | None = None

    # --- tầng HTTP ---------------------------------------------------------
    def _post(self, payload: dict) -> tuple[str | None, str]:
        req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), method="POST")
        req.add_header("Authorization", f"Bearer {self.key}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        if self._sid:
            req.add_header("mcp-session-id", self._sid)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.headers.get("mcp-session-id"), r.read().decode()
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise EpidemicError(f"Key bị từ chối (HTTP {exc.code}). {KEY_HELP}") from exc
            raise EpidemicError(f"Epidemic HTTP {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise EpidemicError(f"Không nối được Epidemic: {exc.reason}") from exc

    @staticmethod
    def _parse_sse(text: str) -> dict:
        """Server trả SSE (`data: {...}`) chứ không phải JSON trần."""
        for line in text.splitlines():
            if line.startswith("data: "):
                try:
                    return json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
        return json.loads(text)

    def _session(self) -> None:
        if self._sid:
            return
        sid, _ = self._post({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                       "clientInfo": {"name": "autoedit", "version": "1.0"}},
        })
        self._sid = sid
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _tool(self, name: str, arguments: dict) -> dict:
        """Gọi tool MCP, bóc 2 lớp bọc (MCP content -> payload GraphQL)."""
        self._session()
        _, text = self._post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                              "params": {"name": name, "arguments": arguments}})
        env = self._parse_sse(text)
        if "error" in env:
            raise EpidemicError(f"MCP lỗi: {env['error'].get('message', env['error'])}")
        payload = json.loads(env["result"]["content"][0]["text"])
        if payload.get("errors"):
            msg = payload["errors"][0].get("message", "")
            if "permission" in msg.lower():
                raise EpidemicError(
                    f"Tài khoản không có quyền tải ({msg}). Key phải tạo từ tài khoản "
                    "Epidemic TRẢ PHÍ — key tài khoản free search được nhưng KHÔNG tải được.")
            raise EpidemicError(f"Epidemic từ chối: {msg}")
        return payload["data"]

    # --- tầng nghiệp vụ ----------------------------------------------------
    def search(self, term: str, limit: int = 10,
               min_s: float | None = None, max_s: float | None = None) -> list[SoundEffect]:
        """Tìm SFX theo term. BẪY: `term` phải lồng trong `query` (xem docstring module)."""
        args: dict = {"query": {"term": term}, "first": limit}
        if min_s is not None or max_s is not None:
            dur: dict = {}
            if min_s is not None:
                dur["min"] = int(min_s * 1000)
            if max_s is not None:
                dur["max"] = int(max_s * 1000)
            args["filter"] = {"duration": dur}
        data = self._tool("SearchSoundEffects", args)
        out = []
        for node in data["soundEffects"]["nodes"]:
            se = node["soundEffect"]
            out.append(SoundEffect(id=se["id"], title=se["title"],
                                   duration_s=se["audioFile"]["durationInMilliseconds"] / 1000))
        return out

    def download(self, effect: SoundEffect, dest: Path, filetype: str = "MP3") -> Path:
        """Lấy link + tải NGAY (link hết hạn ~60s). Trả đường dẫn file thô đã tải."""
        data = self._tool("DownloadSoundEffect",
                          {"id": effect.id, "options": {"fileType": filetype}})
        url = data["soundEffectDownload"]["assetUrl"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT) as r, dest.open("wb") as f:
                while chunk := r.read(1 << 16):
                    f.write(chunk)
        except Exception as exc:
            dest.unlink(missing_ok=True)  # không để lại file cụt cho ffmpeg nuốt
            raise EpidemicError(f"Tải '{effect.title}' lỗi: {exc}") from exc
        return dest
