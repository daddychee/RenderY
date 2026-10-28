r"""Thư mục ra của một phim bóc: <THU_MUC_KHO_BIEN_KICH>/<tên>, tạo sẵn tai-ve/, in đường dẫn.
THU_MUC_KHO_BIEN_KICH lấy từ biến môi trường, rồi `.env` ở gốc thư mục (repo chính hay "skill bien kich"), mặc định F:\gen_video_data\kho-bien-kich.
Chạy: py -3 <thư mục skill>/thu_muc.py <tên>"""
import os
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[3]
TEN_BIEN, MAC_DINH = "THU_MUC_KHO_BIEN_KICH", r"F:\gen_video_data\kho-bien-kich"


def thu_muc_kho() -> Path:
    if os.environ.get(TEN_BIEN):
        return Path(os.environ[TEN_BIEN])
    f = GOC / ".env"
    if f.exists():
        for dong in f.read_text(encoding="utf-8").splitlines():
            if dong.startswith(TEN_BIEN + "="):
                return Path(dong.split("=", 1)[1].strip().strip('"'))
    return Path(MAC_DINH)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        sys.exit("Chạy: py -3 thu_muc.py <tên>")
    r = thu_muc_kho() / sys.argv[1]
    (r / "tai-ve").mkdir(parents=True, exist_ok=True)
    print(r)
