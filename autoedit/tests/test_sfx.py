"""Test thư viện SFX (P1.4) — import manifest + variants + rotation. Không gọi Artlist."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

import pytest
import yaml

from autoedit.overlay.sfx import resolve_sfx_variants
from autoedit.sfx.library import import_from_manifest, library_status, list_variants


def _wav(path: Path, sec: float = 0.4) -> None:
    rate = 48000
    frames = bytearray()
    for i in range(int(sec * rate)):
        frames += struct.pack("<h", int(6000 * math.sin(2 * math.pi * 880 * i / rate)))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(bytes(frames))


@pytest.fixture
def downloads(tmp_path):
    d = tmp_path / "Downloads"; d.mkdir()
    _wav(d / "Cash Register Ding.wav")
    _wav(d / "Coin Drop.wav")
    _wav(d / "Deep Boom.wav")
    return d


def _manifest(path: Path, entries: list[dict]) -> Path:
    path.write_text(yaml.safe_dump({"sfx": entries}), encoding="utf-8")
    return path


def test_import_from_manifest(tmp_path, downloads):
    sfx_root = tmp_path / "sfx"
    man = _manifest(tmp_path / "m.yaml", [
        {"file": "Cash Register Ding.wav", "kind": "cash", "artlist_url": "https://artlist.io/a", "title": "Ding"},
        {"file": "Coin Drop.wav", "kind": "cash", "artlist_url": "https://artlist.io/b", "title": "Coin"},
        {"file": "Deep Boom.wav", "kind": "impact", "artlist_url": "https://artlist.io/c", "title": "Boom"},
    ])
    res = import_from_manifest(man, downloads, sfx_root)
    assert len(res.imported) == 3 and not res.failed
    # 2 biến thể cash, 1 impact, chuẩn hóa WAV
    assert [p.name for p in list_variants("cash", sfx_root)] == ["cash.wav", "cash_2.wav"]
    assert list_variants("impact", sfx_root)[0].name == "impact.wav"
    status = library_status(sfx_root)
    assert status["cash"] == 2 and status["impact"] == 1
    assert all(status[k] == 0 for k in status if k not in ("cash", "impact"))
    # manifest ghi lại artlist_url (truy ngược license)
    rec = yaml.safe_load((sfx_root / "sfx_manifest.yaml").read_text())["sfx"]
    assert any(r["artlist_url"] == "https://artlist.io/a" for r in rec)


def test_import_rejects_bad_kind_and_missing_file(tmp_path, downloads):
    sfx_root = tmp_path / "sfx"
    man = _manifest(tmp_path / "m.yaml", [
        {"file": "Cash Register Ding.wav", "kind": "explosion", "title": "x"},  # kind sai
        {"file": "khong_co.wav", "kind": "pop", "title": "y"},                  # thiếu file
    ])
    res = import_from_manifest(man, downloads, sfx_root)
    assert res.imported == []
    assert any("không hợp lệ" in r[1] for r in res.failed)
    assert any("không thấy file" in r[1] for r in res.failed)


def test_import_appends_not_overwrites(tmp_path, downloads):
    sfx_root = tmp_path / "sfx"
    m1 = _manifest(tmp_path / "m1.yaml", [{"file": "Cash Register Ding.wav", "kind": "cash", "title": "a"}])
    import_from_manifest(m1, downloads, sfx_root)
    m2 = _manifest(tmp_path / "m2.yaml", [{"file": "Coin Drop.wav", "kind": "cash", "title": "b"}])
    import_from_manifest(m2, downloads, sfx_root)
    assert library_status(sfx_root)["cash"] == 2  # nhập 2 lần -> cộng dồn


def test_resolve_variants_and_fallback(tmp_path, downloads):
    sfx_root = tmp_path / "sfx"
    import_from_manifest(
        _manifest(tmp_path / "m.yaml", [
            {"file": "Cash Register Ding.wav", "kind": "cash", "title": "a"},
            {"file": "Coin Drop.wav", "kind": "cash", "title": "b"},
        ]), downloads, sfx_root,
    )
    v = resolve_sfx_variants("cash", sfx_root)
    assert len(v) == 2
    # kind chưa có -> fallback
    fb = tmp_path / "fb.wav"; _wav(fb)
    assert resolve_sfx_variants("pop", sfx_root, fallback=fb) == [fb]
    assert resolve_sfx_variants("none", sfx_root, fallback=fb) == []
