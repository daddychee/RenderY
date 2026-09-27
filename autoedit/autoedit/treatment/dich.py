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
- `nhan_vat`: người hoặc sinh vật xuất hiện nhiều lần.
- `dao_cu`: VẬT có hình dáng cố định, lặp qua nhiều cảnh và phải trông giống \
nhau — kể cả PHƯƠNG TIỆN và máy móc lớn (tàu, tàu ngầm, máy bay, cần cẩu). \
Vật xuất hiện đúng một lần thì bỏ qua.
- `boi_canh`: NƠI CHỐN — chỗ người ta đứng trong đó hoặc nhìn ra từ đó. Ánh \
sáng và chất của môi trường thuộc về đây, KHÔNG thuộc về mood.

Ranh giới `boi_canh` phải giữ chặt: một con tàu, một cỗ máy, một phương tiện \
KHÔNG BAO GIỜ là bối cảnh, dù nó to đến đâu — nó là `dao_cu`. BÊN TRONG nó thì \
mới là bối cảnh, và phải tách thành mục riêng ("khoang tàu", "phòng điều \
khiển"). Xếp nhầm là hỏng: mỗi loại đi theo một luật dựng ảnh khác hẳn.

Luật:
- Chỉ nêu thứ THỰC SỰ có trong kịch bản. Không bịa.
- NGƯỠNG KHÔNG PHẢI LÀ TẦN SUẤT. Một vật chỉ xuất hiện HAI lần nhưng ở hai \
khoảnh khắc LIỀN KỀ nhau trong mạch kể thì VẪN PHẢI gọi tên — hai khung hình \
cạnh nhau chiếu cùng một vật mà khác nhau là lộ ngay. Đây là ca nguy hiểm nhất, \
đừng bỏ qua vì nó "ít lặp lại".
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
# Trần nhà cung cấp, đo 26/09: 20 s bị từ chối. MỘT nguồn cho cả máy chủ lẫn
# trang: đo 27/09 ba nơi hai con số (lệnh LLM 5 s · máy chủ 15 s · trang 5 s)
# là lý do `pv` viết cho 5 giây rồi 5 giây cuối clip đứng hình.
GIAY_VIDEO = 15

# Việc sinh prompt có thể dùng model KHÁC việc dịch: Owner thêm việc này ở
# General › API Keys › Theo app › Treatment. Chưa thêm thì dùng chung `dich`.
VIEC_SINH_PROMPT = "sinh_prompt"

_LENH_KY_THUAT_MAU = """Bạn là đạo diễn hình cho kênh video tư liệu (stock/AI footage + voice over).

Bạn nhận một loạt CẢNH. Mỗi cảnh có: lời đọc của phân cảnh (voice), mô tả cảnh \
bằng tiếng Việt do biên kịch viết, vị trí của nó trong phân cảnh, KHUNG HÌNH \
người dựng ĐÃ CHỌN (cỡ cảnh + góc máy, bằng tiếng Anh), và ASSET đã gán cho cảnh \
(nếu có).

KHUNG LÀ CỦA NGƯỜI DỰNG, BẠN KHÔNG ĐỔI. Đo thật 27/09: để LLM chọn cỡ, góc, máy \
thì nó chép danh sách ví dụ theo đúng thứ tự liệt kê — đó không phải quyết định \
dựng hình. Mọi chữ bạn viết phải NHẤT QUÁN với khung đã cho: cỡ cận thì tả chi \
tiết ở tầm cận, góc từ trên thì mọi thứ nhìn từ trên xuống, POV thì người nhìn \
không xuất hiện trong khung. Đo 27/09: chữ tả từ dưới nhìn lên ghép với khung \
"top-down" thì ảnh vẫn từ dưới, 0/3; chữ viết theo khung thì 3/3.

ASSET ĐÃ CÓ CHỖ LO RỒI — ĐỪNG TẢ LẠI. Hệ thống tự ghim asset vào lượt vẽ, bằng \
ẢNH THAM CHIẾU hoặc bằng chính đoạn mô tả bạn đang đọc. Nên trong `pa` bạn KHÔNG tả lại chúng. Gọi nó bằng một cụm danh \
từ ngắn ("the captain", "the elevator gate"). Không nhắc lại chất liệu, màu sơn, \
niên đại, trang phục, tuổi, kết cấu hay chi tiết ngoại hình của asset.

Với MỖI cảnh, trả về:
- `lap`: CÁI GÌ LẤP KHUNG — tiếng Anh, 8-15 từ, đúng cỡ đã cho. Cỡ cận: "the \
captain's face and cap, the rung and his gripping hand at the frame edge". Cỡ \
rộng: "the captain full-length on the ladder, the hatch and compartment above \
him". Hệ thống ghép thành câu ĐẦU prompt: "{khung}: {lap}."
  MÔI TRƯỜNG PHẢI CÓ MẶT NGAY TRONG `lap` khi nó không hiển nhiên — dưới nước, \
ban đêm, trong mưa, trong khói, ngoài không gian — bằng một từ rõ ("submerged \
underwater", "at night in heavy rain"). Đo 27/09, cảnh 11.3: tàu ngầm "đã chìm \
hẳn" mà `lap` chỉ ghi "against open water" thì ảnh ra tàu nổi trên mặt biển, chân \
vịt lơ lửng trong không khí — ảnh tham chiếu của vật là nền trắng, không mang \
môi trường nào, và câu đầu là câu nhà AI nghe to nhất. Có luật này: 6/6 dưới nước.
- `pa`: BỐN đoạn tiếng Anh nối liền, theo thứ tự, tả khung hình tĩnh:
  1. chủ thể + HÀNH ĐỘNG cụ thể đang xảy ra — cơ học của động tác (tay nào nắm \
đâu, chân ở bậc nào, thân nghiêng thế nào), 20-35 từ. Không phải trạng thái \
chung chung như "climbing" hay "standing".
  2. VỊ TRÍ chủ thể trong khung và thứ gì quanh nó ở đâu, theo đúng góc máy, \
8-15 từ. Cỡ cận thì nêu cả thứ ở sau lưng chủ thể (đo 27/09: khung chật mà không \
nói nền là nền trắng của ảnh tham chiếu rò vào).
  3. ÁNH SÁNG: NGUỒN sáng ở đâu, chiếu hướng nào, soi vào đâu, 8-15 từ. CẤM mọi \
từ chỉ màu, bảng màu, nhiệt độ màu, độ tương phản, grade — việc đó của khối tông \
ghép phía sau. Đo 26/09: "muted cold blue-grey tones" trong `pa` làm hai cảnh \
cạnh nhau lệch màu hẳn.
  4. một CHI TIẾT chỉ có ở khoảnh khắc này, 5-12 từ.
  Không có trần số từ: thà dài mà cụ thể còn hơn ngắn mà rỗng — đo 26/09, `pa` \
24 từ ra chân dung đặt dáng, 61 từ ra đúng hành động 3/3. Bối cảnh CHỈ tả khi \
cảnh không có asset nào lo phần đó. KHÔNG câu nào về phong cách hay mood.
- `pv`: chuyển động của CHỦ THỂ cho một clip liền mạch __GIAY__ giây, chia 2-3 \
nhịp CÓ MỐC GIÂY ("__NHIP__"), hành động phải còn tới giây \
cuối — đo 27/09, viết cho 5 s thì 5 s cuối clip đứng hình. KHÔNG tả chuyển động \
MÁY: người dựng chọn riêng, hệ thống ghép vào đầu prompt.
- `sfx`: gợi ý tiếng động, tiếng Anh ngắn.

Luật:
- Lời đọc mang ẩn dụ thì ĐỪNG quay chữ bề mặt của ẩn dụ — bám chủ thể thật của \
câu chuyện. Đây là lỗi sai nghĩa nặng nhất.
- Trả ĐÚNG số mục, ĐÚNG thứ tự như nhận vào. Không gộp, không bỏ.

Trả về JSON: {"canh": [{"id": "...", "lap": "...", "pa": "...", "pv": "...", \
"sfx": "..."}]}"""


def lenh_ky_thuat(giay: int = GIAY_VIDEO) -> str:
    """Lệnh theo ĐỘ DÀI CLIP của nhà đang dùng: ModelArk 15 s, Seedvis (Omni
    Flash / Veo) 8 s. Nhịp chia ba theo số giây đó."""
    g = int(giay or GIAY_VIDEO)
    a, b = round(g / 3), round(2 * g / 3)
    nhip = "0-%d s: … %d-%d s: … %d-%d s: …" % (a, a, b, b, g)
    return _LENH_KY_THUAT_MAU.replace("__GIAY__", str(g)).replace("__NHIP__", nhip)


_LENH_KY_THUAT = lenh_ky_thuat(GIAY_VIDEO)


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

    def __init__(self, viec: str = VIEC) -> None:
        # Két chia theo VIỆC. Việc nào Owner chưa cấp thì rơi về `dich` — để
        # đổi model cho riêng việc sinh prompt (user 27/09) mà không bắt cấp
        # lại cả bốn việc, và không chết vì một việc chưa ai cấp.
        cd = (doc_ket_viec(viec) or {}) if viec != VIEC else {}
        if not cd.get("key"):
            cd = doc_ket_viec() or {}
        self.viec = viec
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
            # Dừng đúng chỗ khối JSON đóng lại. Cách cũ cắt tới dấu `}` CUỐI
            # CÙNG, nên model viết thêm một câu có dấu `}` phía sau là ôm luôn
            # câu đó vào rồi nghẹn. Đo thật 26/09 trên cả kịch bản SE001:
            # 1/6 lượt chết `Extra data: line 1 column 4184` — mà đây là lượt
            # gọi đắt nhất của tool (~9.100 token), chết là mất trọn lượt tiền.
            return json.JSONDecoder().raw_decode(noi, noi.index("{"))[0]
        except (KeyError, IndexError, ValueError) as exc:
            raise DichLoi(f"{self.model} trả về không đọc được: {exc}") from exc

    def ky_thuat(self, muc: list[dict], tai_san: list[dict]) -> list[dict]:
        """Một lô cảnh -> cột kỹ thuật + prompt tiếng Anh. Kiểm SỐ LƯỢNG trước
        khi trả: lệch một mục là lệch hết phần còn lại của chương."""
        # Nhãn phải nói rõ đây là asset CỦA CẢNH NÀY. Nhãn cũ ("SỔ TÀI SẢN")
        # làm LLM tưởng được đưa cả danh mục để tự chọn lấy — đúng thứ user đã
        # bỏ ngày 25/09 ("Không để LLM tự nhớ"): người chọn, máy không đoán.
        so = "\n".join("- %s (%s): %s" % (t["ma"], t["ten"], t.get("chu", ""))
                        for t in tai_san) or "(cảnh này chưa gán asset nào)"
        than = ("ASSET ĐÃ GÁN CHO CẢNH (đừng tả lại trong `pa`):\n" + so +
                "\n\nCÁC CẢNH:\n") + json.dumps(
            muc, ensure_ascii=False, indent=1)
        # KHÔNG chốt số lượng ở đây: đo thật 24/09 trên C1, claude-sonnet-5 gửi 8
        # trả 7 — chốt số lượng thì cả chương dừng vì một mục bị nuốt. Tầng app
        # khớp theo MÃ, mục nào thiếu thì cảnh đó để trống, bấm lại chạy tiếp.
        # Độ dài clip đi trong từng mục (app đặt theo nhà đang dùng), để lệnh
        # nói đúng số giây và chia nhịp theo số đó.
        giay = (muc[0].get("giay") if muc else None) or GIAY_VIDEO
        ra = self.goi(lenh_ky_thuat(giay), than).get("canh") or []
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
