# -*- coding: utf-8 -*-
"""NẠP tiếng hook (impact/whoosh/click) vào kho ambient PER-NICHE — bước B3 quy trình.

Sửa 3 hằng NICHE / SRC / FOLDER_KIND bên dưới rồi chạy từ folder autoedit/:
    uv run python "..\\scripts\\nap_hook_sfx.py"

- File gốc editor GIỮ NGUYÊN (nguồn nằm NGOÀI folder kho → import không dọn raw/).
- normalize C4 (WAV PCM 48k) + ghi records ambient_library.yaml (truy nguồn) tự động.
- KHÔNG nạp ~/AutoEdit/sfx toàn cục — kho đó là rotation overlay-SFX MỌI niche.

Đã chạy: deepsea 2026-07-13, space 2026-07-14 (cùng nguồn F:\\DEEPSEA\\SOUNDEFFECT).
"""
import tempfile
from pathlib import Path

import yaml

from autoedit.ambient.library import import_from_manifest, library_status, niche_dir

NICHE = "space"                          # kho đích F:\AutoEdit\ambient\<NICHE>
SRC = Path(r"F:\DEEPSEA\SOUNDEFFECT")    # folder SFX editor (mỗi folder con = 1 loại)
FOLDER_KIND = [("Tiếng BOOM", "impact"), ("WHOSH", "whoosh"),
               ("Underwater Whoosh", "whoosh"), ("CLICK", "click"),
               ("CAMERA", "click")]      # folder editor -> kind kho (impact|whoosh|click)

npath = niche_dir(NICHE)
with tempfile.TemporaryDirectory() as tmp:
    for folder, kind in FOLDER_KIND:
        d = SRC / folder
        entries = [{"file": f.name, "kind": kind, "title": f.stem.strip(), "artlist_url": ""}
                   for f in sorted(d.iterdir()) if f.is_file()]
        mf = Path(tmp) / f"manifest_{kind}_{abs(hash(folder))}.yaml"
        mf.write_text(yaml.safe_dump({"ambient": entries}, allow_unicode=True,
                                     sort_keys=False), encoding="utf-8")
        r = import_from_manifest(mf, d, npath)
        print(f"{folder} -> {kind}: nhap {len(r.imported)}, loi {len(r.failed)}")
        for f, err in r.failed:
            print("   FAIL", f, err)

st = library_status(npath)
print(f"\nkho {NICHE} sau nap:", {k: st[k] for k in ("impact", "whoosh", "click") if k in st})
