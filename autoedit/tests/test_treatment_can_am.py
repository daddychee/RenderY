"""Cân âm khi tải ở Storage (user 30/10: "sửa lệch to nhỏ"). Mỗi shot một video Grok nên to nhỏ
khác nhau — bản C cùng một người lệch tới 17 dB. Shot có thoại vào ZIP bằng bản cân về -16 LUFS;
shot im giữ nguyên; file gốc không đụng. Video thật tạo bằng ffmpeg, không mạng."""

from __future__ import annotations

import hashlib
import io
import os
import re
import shutil
import subprocess
import time
import zipfile

import pytest

import autoedit.treatment.app as mapp
from test_treatment_kho_video import _san

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="máy không có ffmpeg")


def _video(p, db):
    """Video 3 giây, tiếng sin ở `db` (sin gốc ≈ -21 LUFS; -12 ra ≈ -33 như shot nhỏ nhất bản C; None = im)."""
    p.parent.mkdir(parents=True, exist_ok=True)
    am = f"sine=frequency=440:duration=3,volume={db}dB" if db is not None else "anullsrc=r=44100:cl=mono"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=gray:s=160x90:d=3",
                    "-f", "lavfi", "-i", am, "-t", "3", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(p)], check=True)
    t = time.time() - 100
    os.utime(p, (t, t))
    return p


def _lufs(p):
    e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(p), "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True, errors="replace").stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1])


def _md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


def test_can_am_ve_muc_thoai_goc_khong_doi(tmp_path):
    nho, to = _video(tmp_path / "nho.mp4", -12), _video(tmp_path / "to.mp4", 9)
    m = _md5(nho)
    a, b = mapp.can_am(nho, tmp_path / "nho-am.mp4"), mapp.can_am(to, tmp_path / "to-am.mp4")
    assert abs(_lufs(nho) - _lufs(to)) > 15, "mẫu phải lệch như bản C"
    assert abs(_lufs(a) - mapp.MUC_THOAI) < 1 and abs(_lufs(b) - mapp.MUC_THOAI) < 1
    assert _md5(nho) == m, "file gốc không đụng"


def test_can_am_shot_im_tra_file_goc(tmp_path):
    im = _video(tmp_path / "im.mp4", None)
    assert mapp.can_am(im, tmp_path / "im-am.mp4") == im


def test_zip_shot_thoai_ra_ban_can_am_lan_sau_dung_lai(tmp_path):
    kho, c, (p1, _, _) = _san(tmp_path)
    ds = c.get("/api/tap/D1/kho-video").json()["ds"]
    assert [x["thoai"] for x in ds] == [True, True, False, True], "clip cả cũ không cân"
    goc = _video(kho.duong_video("D1", ds[0]["khoa"]), -12)
    m = _md5(goc)
    r = c.get("/api/tap/D1/kho-video.zip?ch=C1")
    assert r.status_code == 200, r.text
    z = zipfile.ZipFile(io.BytesIO(r.content))
    ra = tmp_path / "ra.mp4"
    ra.write_bytes(z.read(ds[0]["ten"]))
    assert abs(_lufs(ra) - mapp.MUC_THOAI) < 1, "shot thoại đã cân"
    assert z.read(ds[1]["ten"]) == kho.duong_video("D1", ds[1]["khoa"]).read_bytes(), \
        "file hỏng (MP4 giả) thì gửi nguyên gốc, không chết cả lần tải"
    assert _md5(goc) == m
    ban = goc.with_name(goc.stem + "-am.mp4")
    t = ban.stat().st_mtime
    assert c.get("/api/tap/D1/kho-video.zip?ch=C1").status_code == 200
    assert ban.stat().st_mtime == t, "lần tải sau dùng lại bản cân"
    assert "-am" not in "".join(x["ten"] for x in c.get("/api/tap/D1/kho-video").json()["ds"]), "bản cân không lọt danh sách"
