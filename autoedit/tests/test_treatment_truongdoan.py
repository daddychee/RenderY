"""Treatment — TRƯỜNG ĐOẠN: một nhóm cú máy cùng một không gian, một khung MASTER.

Vì sao có lớp này (user chốt 26/09): *"Tool của tôi dùng để làm film. Trong một
bộ phim thì các cảnh, nhân vật xuất hiện lặp lại liên tục. Asset ban đầu chỉ
đáp ứng việc duy trì đồng nhất cho bối cảnh và nhân vật, nhưng không giúp đồng
nhất các cỡ cảnh và ý đồ kịch bản."*

Đo thật 26/09, 12 lượt Seedream (trang ⑦) rồi 9 lượt nữa (trang ⑧): **khung
master là thứ làm hết việc.** Cùng một căn phòng, cùng ánh sáng, cùng vòng cung
bàn, giữ nguyên qua hai cỡ cảnh khác hẳn nhau và qua 21/21 tấm. Cách cắt ref thì
không đo ra lợi ích nào — nên đợt "cắt ô ref theo hướng" đã bị xoá khỏi kế hoạch.

Trường đoạn **KHÔNG phải loại đối tượng thứ tư**. User chốt: đối tượng chỉ có ba
— người, vật, bối cảnh. Trường đoạn là một NHÓM CÚ MÁY, nên nó đi chung bảng sổ
với `loai="truong_doan"` y như `tong` và `nhan_su` đã đi chung từ trước, và nó
KHÔNG hiện trên màn Asset.

Đi chung bảng là được không mất gì: `ds_so`, `luu_so` và cả đường tải ref đều
không kiểm loại, nên tạo / đặt tên / tải master / phục vụ / xoá chạy sẵn.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from autoedit.treatment import dong as mdong
from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


class VeGia:
    def __init__(self):
        self.goi = []
        self.ref = []

    def gen_anh(self, prompt, dich, ref=None):
        self.goi.append(prompt)
        self.ref.append(list(ref or []))
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(PNG)
        return dich


def _bo(tmp_path, ve=None):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "K-129")
    c = TestClient(tao_app(kho, ve_anh=ve or VeGia()))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "Voice.", "vi": "", "het": 0,
         "canh": [{"t": "Cận bàn tay", "pa": "EN close on the hand"}]}]})
    return c, kho


def _ma(kho):
    return kho.doc("SE001", "H")["dong"][0]["canh"][0]["id"]


def _co_ref(kho, ma):
    t = kho.duong_ref("SE001", ma, ".png")
    t.parent.mkdir(parents=True, exist_ok=True)
    t.write_bytes(PNG)
    return t


def _dat_canh(kho, **khoa):
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0].update(khoa)
    kho.luu("SE001", "H", d, "", "thu")


# ═══════ sổ nhận thêm một loại hàng KHÔNG phải đối tượng ══════════════════════
def test_so_nhan_loai_truong_doan(tmp_path):
    """Đi chung bảng sổ, không đẻ bảng riêng — `tong` và `nhan_su` đã có tiền lệ."""
    kho = Kho(tmp_path / "k.db")
    kho.tao_tap("SE001", "K-129")
    kho.luu_so("SE001", [{"ma": "hop_bao", "loai": "truong_doan",
                          "ten": "Họp báo ở Washington",
                          "chu": "Bục bên trái, phóng viên vòng cung, cửa sau lưng."}])
    ds = kho.ds_so("SE001")
    assert [x["loai"] for x in ds] == ["truong_doan"]
    assert ds[0]["ten"] == "Họp báo ở Washington"
    assert ds[0]["chu"].startswith("Bục bên trái")


def test_master_dung_CHUNG_duong_ref_co_san(tmp_path):
    """Khung master chỉ là "một ảnh mà nhiều cảnh trỏ tới" — đúng hình dạng một
    ref. Không viết đường tải riêng: `ds_so` tự báo `ref`/`ref_v`."""
    kho = Kho(tmp_path / "k.db")
    kho.tao_tap("SE001", "K-129")
    kho.luu_so("SE001", [{"ma": "hop_bao", "loai": "truong_doan", "ten": "Họp báo"}])
    assert kho.ds_so("SE001")[0]["ref"] is False
    _co_ref(kho, "hop_bao")
    x = kho.ds_so("SE001")[0]
    assert x["ref"] is True and x["ref_v"] > 0


# ═══════ cảnh trỏ về trường đoạn của nó ══════════════════════════════════════
def test_canh_giu_duoc_khoa_td_qua_mot_vong_ghi_doc():
    """`td` phải nằm trong KHOA_CANH, không thì nó rụng ngay vòng ghi đầu tiên."""
    assert "td" in mdong.KHOA_CANH
    d = mdong.ghi_canh({}, [{"id": "c1", "t": "Cận", "td": "hop_bao"}])
    assert mdong.doc_canh(d)[0]["td"] == "hop_bao"


# ═══════ đường vẽ: master đi kèm ═════════════════════════════════════════════
def test_master_cua_truong_doan_di_KEM_luot_ve(tmp_path):
    """Đây là cả lý do tồn tại của lớp này."""
    ve = VeGia()
    c, kho = _bo(tmp_path, ve)
    kho.luu_so("SE001", [{"ma": "hop_bao", "loai": "truong_doan", "ten": "Họp báo"}])
    m = _co_ref(kho, "hop_bao")
    _dat_canh(kho, td="hop_bao")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert ve.ref[0] == [m], "cảnh có trường đoạn thì master phải đi kèm lượt vẽ"


def test_master_di_TRUOC_ref_cua_asset(tmp_path):
    """Thứ tự đúng bằng thứ tự đã ĐO: phép đo trần số ref (trang ⑧) chạy
    [master, ref, ref...] và giữ được ba nhận dạng cùng lúc. Đừng đảo thứ tự
    của một cấu hình đã đo mà không đo lại."""
    ve = VeGia()
    c, kho = _bo(tmp_path, ve)
    kho.luu_so("SE001", [
        {"ma": "hop_bao", "loai": "truong_doan", "ten": "Họp báo"},
        {"ma": "hughes", "loai": "nhan_vat", "ten": "Hughes", "chu": "a tall man"}])
    m = _co_ref(kho, "hop_bao")
    a = _co_ref(kho, "hughes")
    _dat_canh(kho, td="hop_bao", ts=["hughes"])
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert ve.ref[0] == [m, a], "master đứng trước, ref asset theo sau"


def test_truong_doan_CHUA_co_master_thi_khong_chan(tmp_path):
    """Gán trường đoạn rồi mà chưa kịp vẽ master là chuyện thường giữa chừng.
    Lúc đó rơi về đúng hành vi cũ, y như asset chưa có ref — không chặn."""
    ve = VeGia()
    c, kho = _bo(tmp_path, ve)
    kho.luu_so("SE001", [{"ma": "hop_bao", "loai": "truong_doan", "ten": "Họp báo"}])
    _dat_canh(kho, td="hop_bao")
    r = c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert r.status_code == 200 and ve.ref[0] == []


def test_canh_KHONG_gan_truong_doan_thi_khong_doi_gi(tmp_path):
    """Hành vi cũ phải nguyên vẹn cho mọi cảnh chưa dùng lớp này."""
    ve = VeGia()
    c, kho = _bo(tmp_path, ve)
    kho.luu_so("SE001", [{"ma": "hughes", "loai": "nhan_vat", "ten": "Hughes"}])
    a = _co_ref(kho, "hughes")
    _dat_canh(kho, ts=["hughes"])
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert ve.ref[0] == [a]


def test_td_tro_vao_ma_KHONG_CO_trong_so_thi_bo_qua(tmp_path):
    """Xoá trường đoạn khỏi sổ trong lúc cảnh còn trỏ vào nó — không được nổ."""
    ve = VeGia()
    c, kho = _bo(tmp_path, ve)
    _dat_canh(kho, td="da_xoa_roi")
    r = c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert r.status_code == 200 and ve.ref[0] == []
