"""Chặn họ bug OptionInfo — đã tái diễn 3 lần (13/06, 17/07, 30/08).

Gọi thẳng một lệnh typer từ Python (vd `make` gọi `run` gọi `assemble`) thì tham số
không truyền GIỮ NGUYÊN đối tượng OptionInfo thay vì giá trị mặc định. Hậu quả:
  - đem nhân/chia -> TypeError giết job (30/08: chết ở assemble sau 47 phút);
  - OptionInfo luôn truthy -> cờ mặc-định-TẮT tự bật (17/07: bật ghi công ngoài ý muốn).

Hai lần trước vá bằng `isinstance` TẠI CHỖ DÙNG nên chỗ khác vẫn hở. Test này canh
ở CỬA VÀO: mọi lệnh bị gọi trực tiếp phải mang @_mac_dinh_that.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import typer

from autoedit import cli
from autoedit.cli import _mac_dinh_that

CLI_PY = Path(cli.__file__)


def test_bom_gia_tri_that_thay_optioninfo():
    @_mac_dinh_that
    def lenh(a: str, speed: float = typer.Option(0.9, "--speed"),
             co: bool = typer.Option(False, "--co")):
        return speed, co

    speed, co = lenh("x")
    assert speed == 0.9 and isinstance(speed, float)
    assert 2 * speed == 1.8          # chính phép nhân từng nổ ở assembler.py:491
    assert co is False               # KHÔNG phải OptionInfo truthy


def test_giu_nguyen_tham_so_bat_buoc():
    """`...` = bắt buộc: phải để typer báo 'Missing option', không tự bịa None."""
    @_mac_dinh_that
    def lenh(bb: str = typer.Option(..., "--bb")):
        return bb

    assert lenh(bb="co") == "co"
    assert lenh().__class__.__name__ == "OptionInfo"


def test_tham_so_truyen_vao_khong_bi_de():
    @_mac_dinh_that
    def lenh(speed: float = typer.Option(0.9, "--speed")):
        return speed

    assert lenh(speed=1.5) == 1.5


def _lenh_typer() -> dict[str, set[str]]:
    """Tên lệnh -> tập tham số có default là typer.Option/Argument."""
    tree = ast.parse(CLI_PY.read_text(encoding="utf-8"))
    ra: dict[str, set[str]] = {}
    for n in tree.body:
        if not isinstance(n, ast.FunctionDef):
            continue
        ds = n.args.defaults
        ten_ds = [a.arg for a in n.args.args[-len(ds):]] if ds else []
        opts = {t for t, d in zip(ten_ds, ds)
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                and d.func.attr in ("Option", "Argument")}
        if opts:
            ra[n.name] = opts
    return ra


def test_moi_lenh_bi_goi_truc_tiep_deu_co_decorator():
    """Rào chặn: thêm lời gọi lệnh mới mà quên decorator -> test này đỏ."""
    lenh = _lenh_typer()
    tree = ast.parse(CLI_PY.read_text(encoding="utf-8"))
    bi_goi = {n.func.id for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in lenh}
    assert bi_goi, "không thấy lệnh nào gọi trực tiếp — kiểm tra lại bộ dò"

    thieu = []
    for ten in sorted(bi_goi):
        fn = getattr(cli, ten, None)
        # có decorator thì functools.wraps để lại __wrapped__
        if fn is None or not hasattr(fn, "__wrapped__"):
            thieu.append(ten)
    assert not thieu, (
        f"Lệnh bị gọi trực tiếp nhưng THIẾU @_mac_dinh_that: {thieu}. "
        f"Thiếu là tái diễn bug OptionInfo (xem docstring file này)."
    )


def test_khong_lenh_nao_con_nhan_optioninfo_khi_goi_thieu():
    """Với mọi lệnh có decorator: gọi thiếu -> tham số phải là giá trị thật."""
    for ten, _ in _lenh_typer().items():
        fn = getattr(cli, ten, None)
        if fn is None or not hasattr(fn, "__wrapped__"):
            continue
        sig = inspect.signature(fn.__wrapped__)
        for ts in sig.parameters.values():
            m = ts.default
            if m.__class__.__name__ in ("OptionInfo", "ArgumentInfo"):
                that = getattr(m, "default", None)
                assert that is ... or that.__class__.__name__ not in ("OptionInfo", "ArgumentInfo")
