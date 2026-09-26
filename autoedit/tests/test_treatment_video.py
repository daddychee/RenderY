"""Treatment — GEN VIDEO bằng Seedance, sau cổng duyệt ảnh.

Luật ghim từ `aigen/duyet.py` (user chốt 03/09) và đã dựng sẵn cổng từ 25/09:
**tiền video chỉ đốt SAU khi ảnh được duyệt**. Ảnh rẻ, video đắt hơn nhiều lần.

Đo thật trên ARK 26/09 trước khi viết dòng code nào:

  - `seedance-1-0-lite-i2v` — khoá này KHÔNG có quyền (HTTP 404). Model chạy
    được là `dreamina-seedance-2-0-mini`: 720p · 16:9 · 24fps · mp4.
  - Trần độ dài: 15s nhận, 20/30/60 bị từ chối `InvalidParameter`. User chốt
    26/09: "cố định theo mức tối đa của nhà cung cấp" -> 15 giây.
  - Tiền tính bằng `completion_tokens`, tuyến tính: 21.600 token/giây + 900.
  - `generate_audio` mặc định BẬT và đã làm hỏng một task thật:
    `OutputAudioSensitiveContentDetected.PolicyViolation`. Tắt đi thì KHÔNG rẻ
    hơn (vẫn 108.900 token cho 5s) nhưng mất hẳn kiểu hỏng đó — mà dây chuyền
    này dùng voice riêng nên không cần tiếng của model.

Sinh video là việc CHẬM (đo: 70-150 giây một clip). Không giữ một request HTTP
treo suốt thời gian đó: đóng tab hay rớt mạng là mất dấu task mà tiền vẫn tiêu.
Nên tách hai nhịp — tạo task rồi trả về ngay, trang tự hỏi lại.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64


class VeAnhGia:
    def gen_anh(self, prompt, dich, ref=None):
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(PNG)
        return dich


class VeVideoGia:
    """Thay Seedance. Giữ lại mọi tham số để test soi được."""

    def __init__(self, trang_thai="succeeded", loi=""):
        self.goi = []
        self.trang_thai_tra = trang_thai
        self.loi = loi

    def bat_dau(self, prompt, anh, giay, am):
        self.goi.append({"prompt": prompt, "anh": anh, "giay": giay, "am": am})
        return "task-gia-1"

    def trang_thai(self, tid):
        d = {"status": self.trang_thai_tra}
        if self.trang_thai_tra == "succeeded":
            d["video_url"] = "https://vi-du/" + tid + ".mp4"
        if self.loi:
            d["loi"] = self.loi
        return d

    def tai_ve(self, url, dich):
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(MP4)
        return dich


def _bo(tmp_path, vv=None, duyet=True):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "K-129")
    kho.luu_so("SE001", [
        {"ma": "toi", "loai": "tong", "ten": "Tối", "chu": "DARK LOOK",
         "tb": "Shot on ARRI"},
        {"ma": "k129", "loai": "dao_cu", "ten": "Tàu K-129",
         "chu": "Soviet Golf-II submarine"}])
    kho.dat_tong_tap("SE001", "toi")
    c = TestClient(tao_app(kho, ve_anh=VeAnhGia(), ve_video=vv or VeVideoGia()))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "Voice one.", "vi": "", "het": 0,
         "canh": [{"t": "Tàu lướt đáy biển", "pa": "EN still", "pv": "EN motion",
                   "co": "MS", "goc": "low angle", "cd": "slow push in",
                   "sfx": "hull groan", "ts": ["k129"]}]}]})
    ma = kho.doc("SE001", "H")["dong"][0]["canh"][0]["id"]
    if duyet:
        c.post(f"/api/tap/SE001/H/canh/{ma}/anh")
        c.post(f"/api/tap/SE001/H/canh/{ma}/duyet")
    return c, kho, ma


def _canh(kho):
    return kho.doc("SE001", "H")["dong"][0]["canh"][0]


# ───────────────────────────────────────────────── cổng duyệt
def test_CHUA_DUYET_anh_thi_tu_choi(tmp_path):
    """Cổng này là cả lý do nó tồn tại: không duyệt mà vẫn dựng được thì cái
    cổng chỉ là trang trí."""
    c, kho, ma = _bo(tmp_path, duyet=False)
    c.post(f"/api/tap/SE001/H/canh/{ma}/anh")          # có ảnh nhưng CHƯA duyệt
    r = c.post(f"/api/tap/SE001/H/canh/{ma}/video")
    assert r.status_code == 400
    assert "duyệt" in r.json()["detail"].lower()


def test_chua_co_anh_thi_tu_choi(tmp_path):
    c, kho, ma = _bo(tmp_path, duyet=False)
    assert c.post(f"/api/tap/SE001/H/canh/{ma}/video").status_code == 400


# ───────────────────────────────────────────────── tạo task
def test_sinh_video_luu_TASK_ID_vao_canh(tmp_path):
    """Không lưu task id thì đóng tab là mất dấu một clip đã trả tiền."""
    c, kho, ma = _bo(tmp_path)
    r = c.post(f"/api/tap/SE001/H/canh/{ma}/video")
    assert r.status_code == 200, r.text
    assert r.json()["vid"] == "task-gia-1"
    assert _canh(kho)["vid"] == "task-gia-1"


def test_gui_ANH_DA_DUYET_lam_dau_vao(tmp_path):
    """Image-to-video: sai ảnh đầu vào là clip chẳng liên quan gì tới cảnh."""
    vv = VeVideoGia()
    c, kho, ma = _bo(tmp_path, vv)
    c.post(f"/api/tap/SE001/H/canh/{ma}/video")
    assert vv.goi[0]["anh"] == kho.duong_anh("SE001", ma)
    assert vv.goi[0]["anh"].read_bytes() == PNG


def test_dung_15_GIAY_va_TAT_AUDIO(tmp_path):
    """15s = trần nhà cung cấp (đo 26/09: 20s bị từ chối). Audio tắt vì dây
    chuyền dùng voice riêng, và vì bật thì dính bộ lọc bản quyền."""
    vv = VeVideoGia()
    c, kho, ma = _bo(tmp_path, vv)
    c.post(f"/api/tap/SE001/H/canh/{ma}/video")
    assert vv.goi[0]["giay"] == 15
    assert vv.goi[0]["am"] is False


def test_gui_PROMPT_VIDEO_DAY_DU(tmp_path):
    """Đúng cái người dùng đọc trong hộp: chuyển động + cỡ cảnh + góc máy +
    mô tả asset + tông + thiết bị + tiếng động."""
    vv = VeVideoGia()
    c, kho, ma = _bo(tmp_path, vv)
    c.post(f"/api/tap/SE001/H/canh/{ma}/video")
    p = vv.goi[0]["prompt"]
    assert "EN motion" in p
    assert "slow push in" in p                    # chuyển động máy của cảnh
    assert "medium shot" in p.lower()             # cỡ cảnh dịch ra chữ
    assert "low angle" in p
    assert "Soviet Golf-II submarine" in p        # mô tả asset
    assert "DARK LOOK" in p and "Shot on ARRI" in p
    assert "hull groan" in p                      # tiếng động


def test_canh_chua_co_prompt_video_thi_tu_choi(tmp_path):
    c, kho, ma = _bo(tmp_path)
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0].pop("pv")
    kho.luu("SE001", "H", d, "", "thu")
    assert c.post(f"/api/tap/SE001/H/canh/{ma}/video").status_code == 400


# ───────────────────────────────────────────────── hỏi lại / tải về
def test_hoi_lai_khi_XONG_thi_tai_ve_va_XOA_task_id(tmp_path):
    c, kho, ma = _bo(tmp_path)
    c.post(f"/api/tap/SE001/H/canh/{ma}/video")
    r = c.post(f"/api/tap/SE001/H/canh/{ma}/video-kiem")
    assert r.status_code == 200, r.text
    assert r.json()["trang_thai"] == "xong"
    assert kho.duong_video("SE001", ma).read_bytes() == MP4
    assert "vid" not in _canh(kho), "xong rồi thì đừng hỏi lại nữa"


def test_hoi_lai_khi_DANG_CHAY_thi_bao_dang_chay(tmp_path):
    c, kho, ma = _bo(tmp_path, VeVideoGia(trang_thai="running"))
    c.post(f"/api/tap/SE001/H/canh/{ma}/video")
    r = c.post(f"/api/tap/SE001/H/canh/{ma}/video-kiem")
    assert r.json()["trang_thai"] == "dang"
    assert _canh(kho)["vid"] == "task-gia-1", "chưa xong thì giữ task id"


def test_hoi_lai_khi_HONG_thi_bao_ro_va_xoa_task_id(tmp_path):
    """Task hỏng mà giữ id thì trang treo mãi ở 'đang dựng'. Đo thật 26/09:
    có task hỏng vì bộ lọc bản quyền âm thanh."""
    c, kho, ma = _bo(tmp_path, VeVideoGia(trang_thai="failed",
                                          loi="PolicyViolation"))
    c.post(f"/api/tap/SE001/H/canh/{ma}/video")
    r = c.post(f"/api/tap/SE001/H/canh/{ma}/video-kiem")
    assert r.json()["trang_thai"] == "hong"
    assert "PolicyViolation" in r.json()["loi"]
    assert "vid" not in _canh(kho)


def test_hoi_lai_khi_CHUA_TAO_task(tmp_path):
    c, kho, ma = _bo(tmp_path)
    assert c.post(f"/api/tap/SE001/H/canh/{ma}/video-kiem").json()["trang_thai"] == "chua"


# ───────────────────────────────────────────────── xem lại
def test_xem_video_tra_file(tmp_path):
    c, kho, ma = _bo(tmp_path)
    c.post(f"/api/tap/SE001/H/canh/{ma}/video")
    c.post(f"/api/tap/SE001/H/canh/{ma}/video-kiem")
    r = c.get(f"/api/tap/SE001/H/canh/{ma}/video")
    assert r.status_code == 200 and r.content == MP4


def test_chua_co_video_thi_404(tmp_path):
    c, kho, ma = _bo(tmp_path)
    assert c.get(f"/api/tap/SE001/H/canh/{ma}/video").status_code == 404


def test_duong_video_chan_ky_tu_la(tmp_path):
    """`ma` đi thẳng vào tên file — cùng luật với `duong_anh`."""
    kho = Kho(tmp_path / "k.db")
    with pytest.raises(ValueError):
        kho.duong_video("SE001", "../../thoat")


# ───────────────────────────────────────────────── quyền / cổng
def test_L2_khong_sinh_video_duoc(tmp_path):
    c, kho, ma = _bo(tmp_path)
    xem = TestClient(tao_app(kho, ve_video=VeVideoGia()))
    xem.headers.update({"X-Remote-User": "nhanvien"})
    assert xem.post(f"/api/tap/SE001/H/canh/{ma}/video").status_code == 403


def test_chua_bat_bo_video_thi_503(tmp_path):
    c, kho, ma = _bo(tmp_path)
    t = TestClient(tao_app(kho))
    t.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    assert t.post(f"/api/tap/SE001/H/canh/{ma}/video").status_code == 503


def test_nguoi_khac_giu_chuong_thi_409(tmp_path):
    c, kho, ma = _bo(tmp_path)
    kho.giu("SE001", "H", "nguoi_khac")
    r = c.post(f"/api/tap/SE001/H/canh/{ma}/video")
    assert r.status_code == 409
    assert "nguoi_khac" in r.json()["detail"]


def test_bo_video_nga_thi_502(tmp_path):
    class Nga:
        def bat_dau(self, prompt, anh, giay, am):
            raise RuntimeError("ARK ngã")

    c, kho, ma = _bo(tmp_path)
    t = TestClient(tao_app(kho, ve_anh=VeAnhGia(), ve_video=Nga()))
    t.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    assert t.post(f"/api/tap/SE001/H/canh/{ma}/video").status_code == 502


def test_doc_chuong_DANH_DAU_canh_da_co_video(tmp_path):
    """Cùng khuôn với `anh`: không lưu vào cảnh mà suy ra từ mtime file lúc đọc
    chương — và giá trị là mtime nên nó CŨNG là tem phiên bản cho đường phát."""
    c, kho, ma = _bo(tmp_path)
    assert "video" not in c.get("/api/tap/SE001/H").json()["dong"][0]["canh"][0]
    c.post(f"/api/tap/SE001/H/canh/{ma}/video")
    c.post(f"/api/tap/SE001/H/canh/{ma}/video-kiem")
    v = c.get("/api/tap/SE001/H").json()["dong"][0]["canh"][0].get("video")
    assert v and v.isdigit()


def test_prompt_video_may_chu_KHOP_cong_thuc_cua_trang(tmp_path):
    """Chốt chặn của cả đợt: prompt ẢNH từng có hai bản dựng ở hai tầng rồi trôi
    khỏi nhau — người dùng duyệt một đằng, máy gửi một nẻo, và không gì trên màn
    hình lộ ra. Ở đây dựng lại ĐÚNG công thức của `promptVideo()` bên trang rồi
    so từng chữ."""
    vv = VeVideoGia()
    c, kho, ma = _bo(tmp_path, vv)
    c.post(f"/api/tap/SE001/H/canh/{ma}/video")

    x = _canh(kho)
    so = {y["ma"]: y for y in kho.ds_so("SE001")}
    mo_ta = "".join("%s: %s\n" % (so[m]["ten"], so[m]["chu"])
                    for m in (x.get("ts") or []) if so.get(m, {}).get("chu"))
    if mo_ta:
        mo_ta += "\n"
    may = "Medium shot, low angle"
    tong = so["toi"]["chu"] + " " + so["toi"]["tb"]
    cho_doi = (x["pv"] + "\nCamera: " + x["cd"] + ". " + may + "."
               + "\nOne continuous shot, no cuts.\n\n" + mo_ta + tong
               + " Sound: " + x["sfx"] + ". No background music.")
    assert vv.goi[0]["prompt"] == cho_doi


# ─────────────────── NỐI cảnh liền nhau: khung cuối clip trước -> khung đầu
# User chốt 26/09: "các cảnh liên tiếp nhau cho phép lưu sử dụng hình cuối của
# video trước làm đầu của video sau".
#
# Mạnh hơn hẳn việc chỉ dùng chung asset: nó cho NỐI LIỀN thật sự chứ không chỉ
# giống nhau. Nhưng đổi lại clip mới KHÔNG còn bắt đầu từ tấm ảnh đã duyệt của
# chính cảnh đó — nên phải là lựa chọn BẤM TAY từng cảnh, không bao giờ tự động.


def _hai_canh(tmp_path, vv=None):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "K-129")
    c = TestClient(tao_app(kho, ve_anh=VeAnhGia(), ve_video=vv or VeVideoGia()))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "V.", "vi": "", "het": 0, "canh": [
            {"t": "Bàn tay đóng cửa xếp", "pa": "EN a", "pv": "EN motion a"},
            {"t": "Thang máy đi xuống", "pa": "EN b", "pv": "EN motion b"}]}]})
    cs = kho.doc("SE001", "H")["dong"][0]["canh"]
    for x in cs:
        c.post(f"/api/tap/SE001/H/canh/{x['id']}/anh")
        c.post(f"/api/tap/SE001/H/canh/{x['id']}/duyet")
    return c, kho, cs[0]["id"], cs[1]["id"]


def test_NOI_thi_dung_KHUNG_CUOI_cua_clip_truoc(tmp_path, monkeypatch):
    import autoedit.treatment.app as mapp

    lay = {}

    def gia(video, dich):
        lay["tu"] = video
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(b"KHUNG-CUOI")
        return dich

    monkeypatch.setattr(mapp, "khung_cuoi", gia)
    vv = VeVideoGia()
    c, kho, m1, m2 = _hai_canh(tmp_path, vv)
    c.post(f"/api/tap/SE001/H/canh/{m1}/video")
    c.post(f"/api/tap/SE001/H/canh/{m1}/video-kiem")      # cảnh 1 có video
    vv.goi.clear()
    r = c.post(f"/api/tap/SE001/H/canh/{m2}/video", json={"noi": True})
    assert r.status_code == 200, r.text
    assert lay["tu"] == kho.duong_video("SE001", m1), "phải trích từ clip cảnh TRƯỚC"
    assert vv.goi[0]["anh"].read_bytes() == b"KHUNG-CUOI", (
        "đầu vào phải là khung cuối, không phải ảnh đã duyệt của cảnh này")


def test_noi_ma_canh_truoc_CHUA_CO_VIDEO_thi_tu_choi(tmp_path):
    c, kho, m1, m2 = _hai_canh(tmp_path)
    r = c.post(f"/api/tap/SE001/H/canh/{m2}/video", json={"noi": True})
    assert r.status_code == 400
    assert "cảnh trước" in r.json()["detail"].lower()


def test_noi_o_CANH_DAU_thi_tu_choi(tmp_path):
    c, kho, m1, m2 = _hai_canh(tmp_path)
    r = c.post(f"/api/tap/SE001/H/canh/{m1}/video", json={"noi": True})
    assert r.status_code == 400


def test_KHONG_noi_thi_van_dung_anh_da_duyet(tmp_path):
    """Mặc định không đổi: clip bắt đầu từ đúng tấm ảnh người ta đã duyệt."""
    vv = VeVideoGia()
    c, kho, m1, m2 = _hai_canh(tmp_path, vv)
    c.post(f"/api/tap/SE001/H/canh/{m2}/video")
    assert vv.goi[0]["anh"] == kho.duong_anh("SE001", m2)


def test_khung_cuoi_lay_dung_CUOI_clip():
    """Lấy khung ở `-sseof` (đếm ngược từ cuối) chứ không phải khung đầu."""
    import inspect

    import autoedit.treatment.app as mapp

    nguon = inspect.getsource(mapp.khung_cuoi)
    assert "-sseof" in nguon
