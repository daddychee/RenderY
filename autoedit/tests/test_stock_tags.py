"""Test M3b — vision-tag pick stock (MO_TA_SFX_HOAN_THIEN §4a).

Tagger fake (không mạng); db thật qua db.connect (schema stock_tags đi cùng).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from autoedit.ambient.schedule import db_scene_lookup, db_subject_lookup
from autoedit.library.db import connect
from autoedit.library.stock_tags import stock_keys_to_tag, tag_project_stock
from autoedit.library.vision import AssetTags
from autoedit.project import Inputs, Project, ShotPick


class FakeTagger:
    model = "fake-v"

    def __init__(self):
        self.calls: list[str] = []

    def tag(self, media_path: Path) -> AssetTags:
        self.calls.append(media_path.name)
        return AssetTags(
            subject="rocket launch", description="A rocket lifting off the pad.",
            shot_size="wide", scene_type="space", mood=["epic"],
            has_people=False, tags=["rocket", "launch", "smoke"],
        )


def _project(tmp_path, shots) -> Project:
    return Project(
        project_id="t", title="t", created_at="2026-07-10", project_dir=str(tmp_path),
        inputs=Inputs(script_path="s", voice_path="v", original_script_path="s",
                      original_voice_path="v", script_text="x"),
        niche="space", shots=shots,
    )


def _pick(bid, key, path) -> ShotPick:
    return ShotPick(beat_id=bid, asset_path=path, asset_key=key, source="pexels")


def test_tag_project_stock_dedup_skip_and_persist(tmp_path):
    (tmp_path / "assets").mkdir()
    for n in ("a.mp4", "e.jpg"):
        (tmp_path / "assets" / n).write_bytes(b"x")
    project = _project(tmp_path, [
        _pick(1, "pexels:100", "assets/a.mp4"),
        _pick(2, "pexels:100", "assets/a.mp4"),          # trùng key -> tag 1 lần
        _pick(3, "local:F:/lib/x.mp4", "assets/l.mp4"),  # local -> skip
        _pick(4, "chart:4", "assets/c.mp4"),             # chart -> skip
        _pick(5, "entity-cache:e1", "assets/e.jpg"),
        _pick(6, "pexels:200", "assets/missing.mp4"),    # file mất -> failed, mẻ vẫn chạy
    ])
    assert set(stock_keys_to_tag(project)) == {"pexels:100", "entity-cache:e1", "pexels:200"}

    conn = connect(tmp_path / "cache.db")
    fake = FakeTagger()
    st = tag_project_stock(project, tmp_path, conn, tagger_factory=lambda k: fake)
    assert st["tagged"] == 2 and st["cached"] == 0
    assert [k for k, _ in st["failed"]] == ["pexels:200"]
    assert sorted(fake.calls) == ["a.mp4", "e.jpg"]

    row = conn.execute("SELECT * FROM stock_tags WHERE asset_key='pexels:100'").fetchone()
    assert row["scene_type"] == "space" and row["media_type"] == "video"
    assert json.loads(row["tags"]) == ["rocket", "launch", "smoke"]

    # chạy lại: cache hit hết (trừ file mất — vẫn failed, không đốt call cho key đã có)
    st2 = tag_project_stock(project, tmp_path, conn, tagger_factory=lambda k: fake)
    assert st2["tagged"] == 0 and st2["cached"] == 2
    assert len(fake.calls) == 2  # không call thêm cho key đã tag


def test_lookups_read_stock_tags(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "a.mp4").write_bytes(b"x")
    project = _project(tmp_path, [_pick(1, "pexels:100", "assets/a.mp4")])
    conn = connect(tmp_path / "cache.db")
    tag_project_stock(project, tmp_path, conn, tagger_factory=lambda k: FakeTagger())

    assert db_scene_lookup(conn)("pexels:100") == "space"
    text, shot, _subj = db_subject_lookup(conn)("pexels:100")
    assert "rocket" in text and "lifting off" in text and shot == "wide"
    assert db_scene_lookup(conn)("pexels:999") == ""     # chưa tag -> mù
    assert db_subject_lookup(conn)("pexels:999") == ("", "", "")


def test_lookups_fail_open_without_table():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    assert db_scene_lookup(conn)("pexels:1") == ""
    assert db_subject_lookup(conn)("pexels:1") == ("", "", "")
