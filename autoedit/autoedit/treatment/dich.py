r"""Dịch cột tiếng Việt — CHỈ để đội đọc hiểu, không đi xuống dây chuyền dựng.

Bản tiếng Anh mới là kịch bản thật (đem đi ren voice, đem đi align). Bản dịch là
cột phụ, nên ở đây fail thì báo lỗi rồi thôi — tuyệt đối không được đụng vào cột
tiếng Anh (test `test_dich_hong_thi_khong_mat_chu` khoá điều đó).

KHOÁ LẤY TỪ KÉT CỦA GENERAL, app KHÔNG giữ sổ khoá riêng (user chốt 23/09, luật
`docs/APPS.md` bước 5): Owner nhập khoá ở **General › API Keys**, cấp cho việc
`dich` của app `treatment`, chọn nhà cung cấp + model ở đó. Két trả kèm cả
`base_url` (đường A, 23/09) nên đổi nhà (glm → grok → mwapi/Claude) là app gọi
đúng địa chỉ mới, không phải sửa một dòng code nào.

Dịch THEO DÒNG, giữ đúng số dòng: hai cột phải nằm ngang hàng thì chỉ vào dòng
nào mới ra đúng nguồn/treatment của dòng đó. LLM trả thiếu/thừa dòng là hỏng cả
màn hình, nên kiểm số lượng trước khi trả.
"""

from __future__ import annotations

import json

SLUG = "treatment"
VIEC = "dich"

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36")

_CAU_LENH = """Bạn dịch kịch bản video sang tiếng Việt cho ĐỘI DỰNG ĐỌC HIỂU.

Luật:
- Dịch TỪNG DÒNG, giữ ĐÚNG số dòng và ĐÚNG thứ tự. Không gộp, không tách, không bỏ.
- Văn nói tự nhiên, giữ nguyên con số / đơn vị / tên riêng / tên nghiên cứu.
- Không thêm lời bình, không thêm chú thích.

Trả về JSON: {"dong": ["bản dịch dòng 1", "bản dịch dòng 2", ...]}"""


_LENH_TAI_SAN = """Bạn là trợ lý dựng storyboard. Dưới đây là TOÀN BỘ \
kịch bản tiếng Anh của một tập phim tư liệu.

VIỆC 1 — GỌI TÊN những thứ phải trông GIỐNG NHAU ở mọi cảnh:
- `nhan_vat`: người, sinh vật, phương tiện xuất hiện nhiều lần.
- `boi_canh`: nơi chốn / môi trường lặp lại. Ánh sáng và chất của môi trường \
thuộc về đây, KHÔNG thuộc về mood.
- `dao_cu`: CHỈ nêu khi một vật lặp qua nhiều cảnh và phải trông giống nhau. \
Vật xuất hiện đúng một lần thì bỏ qua.

Luật:
- Chỉ nêu thứ THỰC SỰ có trong kịch bản. Không bịa.
- Gộp mọi cách gọi khác nhau của cùng một thứ làm MỘT mục.
- `ten`: tiếng Việt, ngắn, đúng cách đội gọi.
- `ly_do`: một câu TIẾNG VIỆT nói vì sao thứ này cần nhất quán, dẫn chi tiết \
có thật trong kịch bản.
- TUYỆT ĐỐI KHÔNG viết mô tả nhận dạng. Người dùng sẽ đưa yêu cầu riêng cho \
từng mục ở bước sau, mô tả sinh từ yêu cầu đó.

VIỆC 2 — ĐỀ XUẤT MOOD cho cả tập, dựa trên việc hiểu kịch bản:
- `ten`: tên gọi ngắn bằng TIẾNG VIỆT.
- `chu`: đoạn TIẾNG ANH sẽ ghép vào cuối MỌI prompt ảnh và video. Nêu: \
photorealistic hay không, mood, mức tương phản, bảng màu, và một câu giữ nhất \
quán giữa các cảnh. KHÔNG nêu ánh sáng của một môi trường cụ thể — cái đó \
thuộc về bối cảnh.
- `tb`: đoạn TIẾNG ANH về thiết bị — thân máy, dòng ống kính, chất phim.
- `ly_do`: một câu TIẾNG VIỆT dẫn căn cứ có thật trong kịch bản.

Trả về JSON: {"tai_san": [{"loai": "...", "ten": "...", "ly_do": "..."}], \
"mood": {"ten": "...", "chu": "...", "tb": "...", "ly_do": "..."}}"""


# Ngữ pháp cỡ cảnh và luật chống sai nghĩa lấy từ `director/prompts.py` — bộ
# đạo diễn của padoma đã chạy thật, không viết lại từ đầu.
_LENH_KY_THUAT = """Bạn là đạo diễn hình cho kênh video tư liệu (stock/AI footage + voice over).

Bạn nhận một loạt CẢNH. Mỗi cảnh có: lời đọc của phân cảnh (voice), mô tả cảnh \
bằng tiếng Việt do biên kịch viết, vị trí của nó trong phân cảnh, và MÔ TẢ CÁC \
ASSET người dùng đã chọn cho cảnh đó (nếu có). Bám mô tả asset khi tả chủ thể — \
đó là thứ giữ nhân vật giống nhau giữa các cảnh.

Với MỖI cảnh, trả về:
- `pa`: prompt TIẾNG ANH tả khung hình tĩnh của cảnh đó. Tả cái NHÌN THẤY: chủ \
thể, hành động, bối cảnh, ánh sáng, chất liệu. KHÔNG thêm câu về phong cách hay \
mood — phần đó hệ thống tự ghép.
- `pv`: prompt TIẾNG ANH tả CHUYỂN ĐỘNG cho một clip liền mạch 5 giây, không \
chuyển cảnh. Chuyển động ĐƠN GIẢN thôi.
- `co`: cỡ cảnh, chỉ nhận WS | MS | CU | ECU | AERIAL
- `goc`: góc máy, tiếng Anh ngắn (eye level, low angle, top down…)
- `cd`: chuyển động camera, tiếng Anh ngắn (static, slow push in, pan left…)
- `sfx`: gợi ý tiếng động, tiếng Anh ngắn

Luật:
- Cỡ cảnh: wide mở đầu/tả bối cảnh · medium kể chuyện · close-up nhấn cảm xúc. \
KHÔNG cho 3 cảnh liền nhau cùng một cỡ.
- Lời đọc mang ẩn dụ thì ĐỪNG quay chữ bề mặt của ẩn dụ — bám chủ thể thật của \
câu chuyện. Đây là lỗi sai nghĩa nặng nhất.
- Trả ĐÚNG số mục, ĐÚNG thứ tự như nhận vào. Không gộp, không bỏ.

Trả về JSON: {"canh": [{"id": "...", "pa": "...", "pv": "...", "co": "...", \
"goc": "...", "cd": "...", "sfx": "..."}]}"""


_LENH_ASSET = """Bạn viết HỒ SƠ NHẬN DẠNG cho một tài sản trong storyboard.

Bạn nhận: loại, tên, YÊU CẦU CỦA ĐẠO DIỄN (tiếng Việt), và mood của cả tập.

Trả về:
- `chu`: mô tả nhận dạng bằng TIẾNG ANH, 1-3 câu. Chỉ nêu đặc điểm NHÌN THẤY \
giữ cho ảnh nhất quán: hình dáng, chất liệu, màu, niên đại, dấu hiệu riêng. \
Đoạn này đính vào MỌI prompt cảnh dùng tài sản này, nên phải ngắn và đặc.
- `pr`: prompt TIẾNG ANH sinh ẢNH THAM CHIẾU, dùng một lần.
  · Với nhân vật (`nhan_vat`) và đạo cụ (`dao_cu`): MỘT khung hình chứa NHIỀU \
GÓC đặt cạnh nhau — toàn thân, ba góc: chính diện, bên hông, sau lưng. NỀN \
TRẮNG trơn liền mạch hoặc NỀN XANH chroma key. Ánh sáng studio đều, không đổ \
bóng, photorealistic, đúng niên đại.
  · Với bối cảnh (`boi_canh`): một khung tả không gian, photorealistic. KHÔNG \
tách nền — bối cảnh phải thấy cả không gian chứ không phải bản cắt rời.
  · Mọi loại: tả khung hình theo hướng THU NHỎ CHỦ THỂ — chủ thể cao khoảng \
một nửa khung, chừa nhiều nền trống quanh mép, nhìn từ xa. Đo thật 26/09: câu \
cấm "nothing cropped" KHÔNG ăn thua, Seedream vẫn cắt cụt đầu càng cẩu; phải \
bảo nó lùi máy ra thì mới lọt khung.

Luật:
- BÁM YÊU CẦU CỦA ĐẠO DIỄN. Yêu cầu nói gì thì giữ nguyên cái đó, không thay \
bằng ý mình, không "cải thiện".
- Yêu cầu bỏ trống chỗ nào thì tự điền cho hợp lý và hợp mood, nhưng tuyệt đối \
không bịa chi tiết mâu thuẫn với yêu cầu.
- `pr` KHÔNG ghép mood tối / ánh sáng của tập. Ref là bản mặt của tài sản để \
đem đi tham chiếu, không phải một cảnh trong phim. Ghép "dark mood" vào là ref \
tối om, tách nền không ra, đem làm tham chiếu thì hỏng.

Trả về JSON: {"chu": "...", "pr": "..."}"""


class DichLoi(RuntimeError):
    """Không dịch được — cột tiếng Anh giữ nguyên, người dùng bấm lại sau."""


def doc_ket_viec(viec: str = VIEC) -> dict:
    """{key, model, base_url} mà Owner đã cấp cho việc `dich` của app NÀY.

    Hỏi thẳng két bằng SLUG CỦA CHÍNH MÌNH, không đi nhờ `web/ket_v3` của RenderY:
    module đó ghi cứng `SLUG = "rendery"` nên cấp phát của Treatment không bao giờ
    thấy (đo 23/09: cấp phát đúng rồi mà app vẫn báo "chưa cấp").

    Chưa cấp / gateway chết -> {} và người dùng nhận câu lỗi chỉ thẳng chỗ bấm.
    Không nuốt: đây là cột phụ, hỏng thì chỉ mất bản dịch.
    """
    import os

    import requests

    goc = os.getenv("TREATMENT_GATEWAY", "http://127.0.0.1:9000")
    tnb = os.getenv("OUTLIERY_TOKEN_NOI_BO", "").strip()
    try:
        r = requests.get(f"{goc}/api/cau-hinh/api-khoa/{SLUG}",
                         headers={"X-Noi-Bo": tnb} if tnb else {}, timeout=5)
        if r.status_code != 200:
            return {}
        muc = r.json().get(viec) or {}
    except Exception:  # noqa: BLE001 — gateway chết thì vẫn phải mở được bàn
        return {}
    ds = muc.get("khoa") or []
    if not ds:
        return {}
    return {"key": ds[0].get("key", ""), "base_url": ds[0].get("base_url", ""),
            "model": muc.get("model", "")}


def dia_chi_chat(url: str) -> str:
    """Địa chỉ gốc của nhà -> endpoint chat kiểu OpenAI.

    Két trả gốc (`https://api.mwapi.dev/v1`); ai đã dán sẵn đường đầy đủ thì giữ.
    """
    u = (url or "").strip().rstrip("/")
    if not u:
        return ""
    if u.endswith("/chat/completions"):
        return u
    return u + "/chat/completions"


def than_goi(model: str, he: str, than: str) -> dict:
    """Thân request kiểu OpenAI, kèm tham số RIÊNG của từng nhà.

    `reasoning_effort` là của GLM và với GLM là BẮT BUỘC (không đặt thì nó nuốt
    trọn max_tokens vào phần suy nghĩ rồi trả JSON cụt — bài học ghi trong
    `director/glm_client.py`). Cổng khác thì trả 400, nên chỉ gửi khi là glm.
    """
    d = {"model": model,
         "messages": [{"role": "system", "content": he},
                      {"role": "user", "content": than}]}
    if model.lower().startswith("glm"):
        d["reasoning_effort"] = "low"
    return d


class LLM:
    """Một lượt gọi LLM kiểu OpenAI, cấu hình lấy từ két mỗi lần khởi tạo."""

    def __init__(self) -> None:
        cd = doc_ket_viec() or {}
        self.key = cd.get("key", "")
        self.model = cd.get("model") or "claude-sonnet-5"
        self.url = dia_chi_chat(cd.get("base_url", ""))

    def goi(self, he: str, than: str) -> dict:
        """Đi bằng `requests`, KHÔNG phải urllib. Đo 16/09 trên máy chủ này:
        cùng khoá cùng thân, `requests` -> 200, urllib -> 403 `error code 1010`
        (Cloudflare chặn User-Agent của urllib). Trước đó máy còn chết
        `CERTIFICATE_VERIFY_FAILED` vì nằm sau lớp chặn TLS."""
        import requests

        if not self.key or not self.url:
            raise DichLoi("Chưa có khoá cho việc dịch — Owner cấp ở "
                          "General › API Keys › tab Theo app › Treatment.")
        try:
            r = requests.post(self.url, timeout=180,
                              json=than_goi(self.model, he, than),
                              headers={"Authorization": f"Bearer {self.key}",
                                       "Content-Type": "application/json",
                                       "User-Agent": _UA})
        except Exception as exc:  # noqa: BLE001
            raise DichLoi(f"Gọi {self.model} hỏng: {exc}") from exc
        if r.status_code != 200:
            raise DichLoi(f"Gọi {self.model} hỏng: HTTP {r.status_code} — {r.text[:160]}")
        try:
            noi = r.json()["choices"][0]["message"]["content"]
            return json.loads(noi[noi.index("{"):noi.rindex("}") + 1])
        except (KeyError, IndexError, ValueError) as exc:
            raise DichLoi(f"{self.model} trả về không đọc được: {exc}") from exc

    def ky_thuat(self, muc: list[dict], tai_san: list[dict]) -> list[dict]:
        """Một lô cảnh -> cột kỹ thuật + prompt tiếng Anh. Kiểm SỐ LƯỢNG trước
        khi trả: lệch một mục là lệch hết phần còn lại của chương."""
        so = "\n".join("- %s (%s): %s" % (t["ma"], t["ten"], t.get("chu", ""))
                        for t in tai_san) or "(sổ tài sản trống)"
        than = "SỔ TÀI SẢN:\n" + so + "\n\nCÁC CẢNH:\n" + json.dumps(
            muc, ensure_ascii=False, indent=1)
        # KHÔNG chốt số lượng ở đây: đo thật 24/09 trên C1, claude-sonnet-5 gửi 8
        # trả 7 — chốt số lượng thì cả chương dừng vì một mục bị nuốt. Tầng app
        # khớp theo MÃ, mục nào thiếu thì cảnh đó để trống, bấm lại chạy tiếp.
        ra = self.goi(_LENH_KY_THUAT, than).get("canh") or []
        return [x for x in ra if isinstance(x, dict)]

    def sinh_asset(self, muc: dict, tong: str) -> dict:
        """Một tài sản + YÊU CẦU của người dùng -> hồ sơ nhận dạng + prompt ref.

        Yêu cầu đi TRƯỚC mọi thứ khác trong thân: cái LLM đoán từ kịch bản là
        một con cá mập chung chung, cái đội cần là con cá mập trong đầu đạo
        diễn (user chốt 25/09).
        """
        than = ("YÊU CẦU CỦA ĐẠO DIỄN:" + chr(10) + (muc.get("yc") or "") +
                chr(10) * 2 + "TÀI SẢN: %s (%s)" % (muc.get("ten", ""),
                                                    muc.get("loai", "")) +
                chr(10) * 2 + "MOOD CỦA CẢ TẬP:" + chr(10) + (tong or "(chưa đặt)"))
        ra = self.goi(_LENH_ASSET, than)
        return {"chu": str(ra.get("chu") or "").strip(),
                "pr": str(ra.get("pr") or "").strip()}

    def goi_y(self, kich_ban: str) -> dict:
        """CẢ kịch bản tiếng Anh -> {tai_san, mood}, MỘT lượt gọi.

        Không chia lô nữa: đo 25/09 trên SE001, toàn bộ `en` là 36.542 ký tự
        (~9.100 token) — lọt một lượt thoải mái. Chia lô thì mỗi lô chỉ thấy
        một khúc truyện, mà mood là nhận định về CẢ tập; hỏi từng khúc rồi ghép
        lại chỉ ra một đống mâu thuẫn.

        Tầng app lọc hình dạng: ở đây trả nguyên, hỏng mục nào bỏ mục đó chứ
        không giết cả lượt — mất một mục còn hơn mất cả bảng đề xuất.
        """
        ra = self.goi(_LENH_TAI_SAN, kich_ban)
        return ra if isinstance(ra, dict) else {}

    def dich(self, cau: list[str]) -> list[str]:
        than = "\n".join(f"[{i}] {c}" for i, c in enumerate(cau))
        ra = self.goi(_CAU_LENH, than).get("dong") or []
        if len(ra) != len(cau):
            raise DichLoi(f"{self.model} trả {len(ra)} dòng trong khi gửi {len(cau)} "
                          "— hai cột sẽ lệch hàng.")
        return [str(x) for x in ra]
