"""CLI AutoEdit (typer).

M0: `new` — tạo project từ script + voice.
M1: `register-machine` — đăng ký donor draft CapCut cho máy này.
    `demo-draft` — sinh draft demo mở được trong CapCut (bài test Gate 1).
M2: `align` — voice ↔ script, timestamp từng từ vào project.json.
M3: `direct` — LLM đạo diễn chia beat (2 pass, structured output, tốn API).
M3.5: `library-init` / `library-index` / `library-search` — thư viện niche + cache.db.
P1.4: `sfx-init` / `sfx-import` / `sfx-list` — thư viện SFX (Cowork tải Artlist).
F9: `direct-context` / `direct-ingest` — đường phiên sống L2b sâu (Claude Code đạo diễn,
    ỐNG xuất ngữ cảnh + gác draft; đường `direct` cũ giữ nguyên làm fallback).
M4: `cut` — cắt voice theo beat + hình thở (ffmpeg, hệ tọa độ kép).
M5: `source` — tải footage theo route (local/Pexels/Google CSE/graphic).
M6: `assemble` — ráp draft CapCut 3 track; `run` — chạy mọi stage còn thiếu.

Các lệnh tương lai (làm ở milestone sau):
  run               chạy full pipeline align->...->draft (M6)
  resume            chạy tiếp từ stage đang dở (dùng project.json.stages)
  music-add         thêm nhạc vào thư viện nội bộ + auto-tag (Phase 1)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from autoedit.project import create_project

app = typer.Typer(
    add_completion=False,
    help="AutoEdit — script + voice -> CapCut draft (PADOMA MEDIA).",
)


@app.callback()
def _root() -> None:
    """Giữ app ở dạng multi-command để các lệnh có tên (vd `autoedit new`)."""


@app.command()
def new(
    script: Path = typer.Option(..., "--script", help="File script .txt (tiếng Anh)."),
    voice: Path = typer.Option(..., "--voice", help="File voice .mp3/.wav (ElevenLabs)."),
    out: Path = typer.Option(Path("projects"), "--out", help="Thư mục chứa các project."),
    title: Optional[str] = typer.Option(None, "--title", help="Tên video (mặc định: tên file script)."),
    brief: Optional[str] = typer.Option(None, "--brief", help="Creative brief / chỉ đạo hình ảnh."),
    channel: Optional[str] = typer.Option(None, "--channel", help="Tên kênh (channel profile)."),
    srt: Optional[Path] = typer.Option(None, "--srt", help="File .srt kèm voice (align đọc thẳng, khỏi nhận dạng)."),
) -> None:
    """Tạo project mới từ script + voice, ghi project.json (nguồn sự thật)."""
    try:
        project = create_project(
            script=script,
            voice=voice,
            out_dir=out,
            title=title,
            brief=brief,
            channel=channel,
            srt=srt,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    dur = project.inputs.voice_duration_sec
    dur_str = f"{dur:.1f}s" if dur is not None else "không đọc được (ffprobe?)"

    typer.secho(f"✓ Tạo project: {project.project_id}", fg=typer.colors.GREEN)
    typer.echo(f"  project.json : {project.project_dir}/project.json")
    typer.echo(f"  voice        : {dur_str}")
    typer.echo(f"  script       : {len(project.inputs.script_text)} ký tự")
    typer.echo("  stage tiếp theo: align (M2)")


_TEXT_EXTS = (".txt", ".md", ".rtf")
_AUDIO_EXTS = (".mp3", ".wav", ".m4a", ".aac", ".flac")


def _pick_input(folder: Path, exts: tuple[str, ...], preferred_stem: str):
    """Chọn 1 file theo ĐUÔI (tên bất kỳ): ưu tiên stem chuẩn (script/voice), không thì
    nếu chỉ có 1 file đúng đuôi → lấy luôn. Nhiều file → heuristic (ưu .txt, rồi to nhất).
    Trả (path, lý-do): ok | none | many."""
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts]
    # Ưu tiên 1: tên chuẩn
    for p in files:
        if p.stem.lower() == preferred_stem:
            return p, "ok"
    if len(files) == 1:
        return files[0], "ok"
    if not files:
        return None, "none"
    # Nhiều file: với script ưu .txt hơn .rtf/.md; với audio không phân biệt → chọn lớn nhất
    priority_ext = ".txt" if preferred_stem == "script" else None
    candidates = [p for p in files if p.suffix.lower() == priority_ext] if priority_ext else files
    if not candidates:
        candidates = files
    picked = max(candidates, key=lambda p: p.stat().st_size)
    return picked, "ok"


def _find_one(folder: Path, names: tuple[str, ...]) -> Optional[Path]:
    """[giữ tương thích] Tìm file khớp đúng tên (không phân biệt hoa thường)."""
    low = {p.name.lower(): p for p in folder.iterdir() if p.is_file()}
    for n in names:
        if n in low:
            return low[n]
    return None


def _rtf_to_txt(rtf: Path) -> Path:
    """Chuyển .rtf -> .txt bằng textutil (macOS) — bỏ bước convert tay."""
    import subprocess
    out = rtf.with_suffix(".txt")
    subprocess.run(["textutil", "-convert", "txt", "-output", str(out), str(rtf)],
                   check=True, capture_output=True)
    return out


@app.command()
def make(
    folder: Path = typer.Argument(..., help="Folder 1 video/chương: script.txt + voice.mp3 (+ voice.srt nếu có)."),
    channel: str = typer.Option("", "--channel", help="Tên kênh/niche (dùng thư viện footage của kênh)."),
    enrich: bool = typer.Option(False, "--enrich", help="Sinh biểu đồ/thẻ bổ sung (cần duyệt thêm)."),
    whisper_model: str = typer.Option("small", "--whisper-model", help="Model align."),
    director_model: str = typer.Option("claude-sonnet-4-6", "--director-model"),
    language: str = typer.Option("auto", "--language"),
    align_backend: str = typer.Option("auto", "--align-backend",
                                      help="Nguồn timestamp: auto (có .srt thì đọc) | srt | whisper."),
    music_sync: bool = typer.Option(False, "--music-sync", help="Bật gói MUSIC SYNC (stage music: nhạc hook to + snap accent + đổi nhạc neo cut)."),
) -> None:
    """1 LỆNH dựng FULL 1 video/chương: tạo project + chạy hết pipeline + mở report.html.

    Folder cần script (txt/rtf/md) + voice (mp3/wav/m4a). Có thêm .srt thì align đọc
    thẳng file đó (tức thì) thay vì nhận dạng lại. Nhạc/SFX tự dùng thư viện.
    """
    import subprocess

    from autoedit.project import Project, Stage, create_project

    folder = folder.expanduser()
    if not folder.is_dir():
        typer.secho(f"Lỗi: không thấy folder {folder}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    script, sr = _pick_input(folder, _TEXT_EXTS, "script")
    voice, vr = _pick_input(folder, _AUDIO_EXTS, "voice")
    if script is None or voice is None:
        missing = []
        if script is None:
            missing.append("file kịch bản (.txt/.rtf/.md)")
        if voice is None:
            missing.append("file giọng (.mp3/.wav/.m4a)")
        msg = f"Lỗi: không tìm thấy {' và '.join(missing)} trong folder."
        typer.secho(msg, fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    if script.suffix.lower() == ".rtf":
        try:
            script = _rtf_to_txt(script)
        except Exception as exc:
            typer.secho(f"Lỗi chuyển .rtf: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    srt_src = _pick_input(folder, (".srt",), voice.stem)[0]

    try:
        project = create_project(script=script, voice=voice, out_dir=Path("projects"),
                                 title=folder.name, channel=channel or None, srt=srt_src)
    except (FileNotFoundError, ValueError) as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if srt_src is not None:
        typer.echo(f"  ✓ Thấy {srt_src.name} — align đọc thẳng file này (không nhận dạng lại)")

    typer.secho(f"✓ Bắt đầu dựng '{folder.name}' (vài phút — đừng tắt)...", fg=typer.colors.CYAN)
    # chạy hết pipeline (run đã gồm REPORT cuối). Truyền tham số tường minh (bug OptionInfo).
    # .srt đã copy vào project cạnh voice -> aligner tự tìm, không cần truyền srt=.
    run(Path(project.project_dir), niche=channel, music=None, model=whisper_model,
        language=language, align_backend=align_backend,
        director_model=director_model, with_enrich=enrich,
        music_sync=music_sync if isinstance(music_sync, bool) else False)

    project = Project.load(project.project_dir)
    if project.report_path:
        import sys as _sys
        if _sys.platform == "win32":
            import os as _os
            _os.startfile(project.report_path)
        else:
            subprocess.run(["open", project.report_path], check=False)
    typer.secho("\n✅ XONG! Mở CapCut (draft mới đã xuất hiện) + report.html vừa bật để kiểm.",
                fg=typer.colors.GREEN)


@app.command(name="make-launcher")
def make_launcher_cmd(
    channel: str = typer.Option(..., "--channel", help="Tên kênh/niche nhúng vào launcher."),
    out: Path = typer.Option(..., "--out", help="File .command sẽ tạo (vd ~/Desktop/Dung-NghiHuu.command)."),
) -> None:
    """Tạo file .command DOUBLE-CLICK cho 1 kênh: staff bấm → chọn folder video → tool dựng hết.
    KHÔNG cần gõ lệnh. Mỗi kênh tạo 1 launcher (kỹ thuật làm 1 lần, giao cho staff)."""
    import shutil
    repo = Path(__file__).resolve().parents[1]   # thư mục autoedit/ (có pyproject)
    uv = shutil.which("uv") or "/opt/homebrew/bin/uv"  # nhúng path tuyệt đối (shell double-click không có PATH)
    uv_dir = str(Path(uv).parent)
    body = f'''#!/bin/bash
# Double-click chạy: shell mới KHÔNG có PATH như Terminal -> nhúng đường dẫn uv tuyệt đối.
export PATH="{uv_dir}:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "{repo}" || exit 1
FOLDER=$(osascript -e 'POSIX path of (choose folder with prompt "Chon folder video (co script + voice):")') || exit 0
echo "Dang dung video tu: $FOLDER"
echo "(vai phut, dung tat cua so nay)"
if "{uv}" run autoedit make "$FOLDER" --channel "{channel}"; then
  echo ""
  echo "===== XONG. Mo CapCut + report.html de kiem. Bam Enter de dong. ====="
else
  echo ""
  echo "===== CO LOI khi dung. Chup man hinh gui ky thuat. Bam Enter de dong. ====="
fi
read _
'''
    out = out.expanduser()
    out.write_text(body, encoding="utf-8")
    out.chmod(0o755)
    typer.secho(f"✓ Launcher cho kênh '{channel}': {out}", fg=typer.colors.GREEN)
    typer.echo("  Giao cho staff: double-click file này → chọn folder video → đợi → mở CapCut.")


@app.command(name="make-launcher-win")
def make_launcher_win_cmd(
    channel: str = typer.Option(..., "--channel", help="Tên kênh/niche nhúng vào launcher."),
    out: Path = typer.Option(..., "--out", help="File .bat sẽ tạo (vd %USERPROFILE%\\Desktop\\DungNghiHuu.bat)."),
) -> None:
    """Tạo file .bat DOUBLE-CLICK cho Windows: staff bấm → hộp chọn folder → tool dựng hết.
    KHÔNG cần gõ lệnh. Mỗi kênh tạo 1 launcher (kỹ thuật làm 1 lần, giao cho staff)."""
    import shutil
    repo = Path(__file__).resolve().parents[1]
    uv_path = shutil.which("uv") or ""
    if not uv_path:
        python_dir = Path(__file__).resolve().parents[3] / "Scripts"
        uv_path = str(python_dir / "uv.exe")

    body = f"""@echo off
chcp 65001 >nul
title AutoEdit — Dung video kenh {channel}
cd /d "{repo}"

echo Chon folder video (co script.txt + voice.mp3)...
for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Chon folder video (co script.txt + voice.mp3):'; $d.RootFolder='MyComputer'; if($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){{$d.SelectedPath}}"`) do set FOLDER=%%F

if not defined FOLDER (
    echo Da huy. Bam phim bat ky de dong.
    pause >nul
    exit /b 0
)

echo.
echo Dang dung video tu: %FOLDER%
echo Vui long doi vai phut, KHONG tat cua so nay...
echo.

set PYTHONUTF8=1
"{uv_path}" run autoedit make "%FOLDER%" --channel "{channel}"

if %errorlevel%==0 (
    echo.
    echo ========================================================
    echo  XONG! Mo CapCut va report.html de kiem tra.
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo  CO LOI. Chup man hinh nay va gui cho ky thuat.
    echo ========================================================
)
echo Bam phim bat ky de dong cua so...
pause >nul
"""
    out = out.expanduser()
    out.write_text(body, encoding="utf-8")
    typer.secho(f"✓ Launcher Windows cho kênh '{channel}': {out}", fg=typer.colors.GREEN)
    typer.echo("  Giao cho staff: double-click file .bat → chọn folder video → đợi → mở CapCut.")


@app.command(name="register-machine")
def register_machine_cmd(
    donor: Optional[Path] = typer.Option(
        None,
        "--donor",
        help="Folder draft THẬT do CapCut máy này tạo (vd .../com.lveditor.draft/0428). "
        "Bỏ trống: tự chọn draft sửa gần nhất.",
    ),
) -> None:
    """Đăng ký máy này với CapCut: trích platform/version/root từ donor draft."""
    from autoedit.packager.machine import find_default_donor, register_machine

    if donor is None:
        donor = find_default_donor()
        if donor is None:
            typer.secho(
                "Không tìm thấy draft CapCut nào trên máy. Mở CapCut tạo 1 draft bất kỳ "
                "rồi chạy lại, hoặc chỉ định --donor.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)
        typer.echo(f"Dùng donor tự chọn (draft sửa gần nhất): {donor.name}")

    try:
        profile = register_machine(donor)
    except (FileNotFoundError, ValueError) as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.secho("✓ Đã đăng ký máy", fg=typer.colors.GREEN)
    typer.echo(f"  donor        : {profile.donor_name}")
    typer.echo(f"  capcut_root  : {profile.capcut_root}")
    typer.echo(f"  CapCut       : {profile.capcut_app_version}"
               f" (new_version {profile.content_overrides.get('new_version')})")
    typer.echo("  Lưu ý: tắt auto-update CapCut; sau mỗi update chạy lại `autoedit demo-draft` để re-test.")


@app.command(name="demo-draft")
def demo_draft_cmd(
    name: str = typer.Option("PADOMA_AUTOEDIT_DEMO", "--name", help="Tên draft (ASCII)."),
    assets: Optional[Path] = typer.Option(
        None, "--assets", help="Folder asset mẫu (mặc định: capcut_test/assets ở folder cha repo)."
    ),
    overwrite: bool = typer.Option(False, "--overwrite", help="Đè draft trùng tên."),
) -> None:
    """Sinh draft demo vào folder CapCut của máy — mở CapCut lên kiểm tra."""
    from autoedit.packager.demo import build_demo_content
    from autoedit.packager.machine import MachineProfile
    from autoedit.packager.packager import PackageError, package_draft

    if assets is None:
        # repo nằm trong folder dự án: <dự án>/autoedit/autoedit/cli.py
        assets = Path(__file__).resolve().parents[2] / "capcut_test" / "assets"

    try:
        profile = MachineProfile.load()
        content = build_demo_content(assets)
        draft_dir = package_draft(content, name, profile, overwrite=overwrite)
    except (FileNotFoundError, PackageError) as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.secho(f"✓ Đã sinh draft: {draft_dir}", fg=typer.colors.GREEN)
    typer.echo("  Mở CapCut → draft phải xuất hiện và mở được, có 2 shot video + voice + nhạc + text.")


@app.command()
def align(
    project_dir: Path = typer.Argument(..., help="Folder project (chứa project.json)."),
    model: str = typer.Option("small", "--model", help="Cỡ model faster-whisper: tiny/base/small/medium."),
    language: str = typer.Option("auto", "--language", help="Ngôn ngữ voice: auto/en/vi..."),
    backend: str = typer.Option("auto", "--backend",
                                help="Nguồn timestamp: auto (có .srt thì đọc, không thì whisper) | srt | whisper."),
    srt: Optional[Path] = typer.Option(None, "--srt", help="Đường dẫn .srt (mặc định tìm cạnh file voice)."),
) -> None:
    """Stage 1: align voice với script, timestamp từng từ.

    Có .srt sẵn -> đọc thẳng (tức thì, chữ là chữ THẬT của kịch bản).
    Không có -> nhận dạng bằng faster-whisper (chạy CPU, vài phút/video 10p).
    """
    from autoedit.align.runner import run_align
    from autoedit.align.srt_file import SrtAligner
    from autoedit.project import Project, Stage

    if backend not in ("auto", "srt", "whisper"):
        typer.secho(f"Lỗi: --backend phải là auto|srt|whisper (nhận '{backend}')",
                    fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    try:
        project = Project.load(project_dir)
    except FileNotFoundError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    voice_path = Path(project.project_dir) / project.inputs.voice_path
    srt_aligner = SrtAligner(srt_path=srt)
    use_srt = backend == "srt" or (backend == "auto" and srt_aligner.find_srt(voice_path) is not None)

    if use_srt:
        aligner = srt_aligner
        typer.echo(f"Align {project.project_id} (đọc .srt có sẵn)...")
    else:
        # Import trong nhánh: faster-whisper là dependency OPTIONAL, luồng .srt không cần
        try:
            from autoedit.align.whisper_local import FasterWhisperAligner
        except ImportError as exc:
            typer.secho(f"Lỗi: cần faster-whisper để nhận dạng ({exc}). Cài `pip install faster-whisper`, "
                        f"hoặc đặt file .srt cạnh voice rồi chạy lại.", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        aligner = FasterWhisperAligner(model_size=model, language=language)
        typer.echo(f"Align {project.project_id} (model {model}, lang {language}, CPU "
                   f"{aligner.cpu_threads} luồng, beam {aligner.beam_size})...")
        typer.echo("  ⏳ Đang nghe audio + khớp từng từ — vài phút (video càng dài càng lâu), đừng tắt cửa sổ.")

    try:
        project = run_align(project, aligner)
    except (FileNotFoundError, ValueError) as exc:
        typer.secho(f"Lỗi align: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    record = project.stages[Stage.ALIGN]
    n_interp = sum(1 for w in project.transcript if w.interpolated)
    typer.secho(f"✓ Align xong: {len(project.transcript)} từ ({n_interp} nội suy)", fg=typer.colors.GREEN)
    typer.echo(f"  transcript.json: {project_dir}/transcript.json")
    for w in record.warnings:
        typer.secho(f"  ⚠ {w}", fg=typer.colors.YELLOW)


@app.command()
def direct(
    project_dir: Path = typer.Argument(..., help="Folder project (đã align)."),
    model: str = typer.Option("claude-sonnet-4-6", "--model", help="Model (claude-code: alias 'sonnet'/'opus' hoặc tên đầy đủ)."),
    engine: str = typer.Option(
        "claude-code", "--engine",
        help="claude-code = qua Claude Code subscription (mặc định, không key); api = Anthropic API key.",
    ),
) -> None:
    """Stage 2: LLM đạo diễn chia beat — 2 pass. Mặc định qua Claude Code (subscription)."""
    from collections import Counter

    from autoedit.director.runner import run_direct
    from autoedit.project import Project, Stage

    try:
        project = Project.load(project_dir)
    except FileNotFoundError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    log_dir = Path(project_dir) / "llm_log"
    if engine == "claude-code":
        from autoedit.director.cc_client import ClaudeCodeDirectorClient
        client = ClaudeCodeDirectorClient(model=model, log_dir=log_dir)
    else:
        from autoedit.director.client import ClaudeDirectorClient
        client = ClaudeDirectorClient(model=model, log_dir=log_dir)
    typer.echo(f"Direct {project.project_id} (engine={engine}, {model}, 2 pass)...")
    n_cost = len(project.cost_log)

    def show(done: int, total: int, label: str) -> None:
        typer.echo(f"  [{done}/{total}] {label}")

    try:
        project = run_direct(project, client, on_progress=show)
    except RuntimeError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    record = project.stages[Stage.DIRECT]
    levels = Counter(b.visual_level for b in project.beats)
    routes = Counter(b.sourcing_route for b in project.beats)
    n_anchor_free = sum(1 for b in project.beats if not b.visual_anchor)
    n_chapters = len((project.outline or {}).get("chapters", []))
    typer.secho(
        f"✓ Direct xong: {n_chapters} chương, {len(project.beats)} beat, "
        f"chi phí direct ${_run_cost(project, n_cost)}",
        fg=typer.colors.GREEN,
    )
    n_overlay = sum(len(b.overlays) for b in project.beats)
    typer.echo(f"  sourcing_route: {dict(routes)}  (slot tự do: {n_anchor_free})")
    typer.echo(f"  visual_level : {dict(levels)}  | overlay: {n_overlay}")
    typer.echo(f"  beats.json   : {project_dir}/beats.json  ← REVIEW BẰNG MẮT (gate M3)")
    typer.echo(f"  llm_log      : {project_dir}/llm_log/")
    for w in record.warnings:
        typer.secho(f"  ⚠ {w}", fg=typer.colors.YELLOW)


def _run_cost(project, n_before: int) -> float:
    """Chi phí RIÊNG của lần chạy này = các entry cost_log thêm sau n_before."""
    return round(sum(c.usd for c in project.cost_log[n_before:]), 4)


@app.command(name="direct-context")
def direct_context_cmd(
    project_dir: Path = typer.Argument(..., help="Folder project (đã align)."),
    niche: str = typer.Option(
        "", "--niche",
        help="Niche kho local cho khối TỪ VỰNG KHO (C4) — mặc định lấy từ channel của project."),
    boost: Optional[list[str]] = typer.Option(
        None, "--boost",
        help="Cảnh dạng X khán giả thích 'X@scope' (lặp được) — dính vào project.json; "
             "NÃO đan X vào concept + phễu source tự cộng điểm (MO_TA_VAN_HANH_BOOST.md). "
             "Khai Ở ĐÂY (trước direct) mới ăn trọn cả 2 tầng."),
) -> None:
    """L2b sâu mảnh 1: xuất direct_context.md — transcript đánh số [i]word + bảng ràng
    buộc cứng + từ vựng kho local (C4) + chữ ký pacing DNA (DNA-D1 Mảnh A), cho phiên
    Claude Code tự đạo diễn (không gọi API)."""
    from autoedit.director.live import write_direct_context
    from autoedit.project import Project

    try:
        project = Project.load(project_dir)
        # BOOST: khuôn --ref/--boost của source (dính + chống OptionInfo bug B2);
        # khai tại direct-context = ĐÚNG THỜI ĐIỂM (NÃO chưa chạy)
        if isinstance(boost, list) and boost:
            project.inputs.boosts = [str(b) for b in boost]
            project.save()
        eff_niche = niche or project.inputs.channel or ""
        path = write_direct_context(project, niche=eff_niche)
    except (FileNotFoundError, RuntimeError) as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.secho(f"✓ Đã ghi {path}", fg=typer.colors.GREEN)
    ctx_text = path.read_text(encoding="utf-8")
    if eff_niche:
        has_vocab = "TỪ VỰNG KHO LOCAL" in ctx_text
        typer.echo(f"  Từ vựng kho '{eff_niche}': {'✓ kèm trong context' if has_vocab else '— kho rỗng/không db, bỏ khối (fail-open)'}")
    if "SỞ THÍCH KHÁN GIẢ" in ctx_text:
        typer.echo("  BOOST khán giả: ✓ khối SỞ THÍCH trong context (NÃO sẽ đan X vào concept)")
        has_dna = "CHỮ KÝ PACING NICHE" in ctx_text
        typer.echo(f"  DNA pacing '{eff_niche}': {'✓ kèm trong context' if has_dna else '— không dna.json, bỏ khối (fail-open)'}")
    typer.echo("  → Phiên sống đọc foundation + file này, viết director_draft.json cùng folder,")
    typer.echo(f"    rồi chạy: autoedit direct-ingest {project_dir}")


@app.command(name="direct-ingest")
def direct_ingest_cmd(
    project_dir: Path = typer.Argument(..., help="Folder project (đã align)."),
    draft: Optional[Path] = typer.Option(
        None, "--draft", help="File draft (mặc định <project_dir>/director_draft.json)."
    ),
) -> None:
    """L2b sâu mảnh 3: nhận director_draft.json, chạy NGUYÊN battery validator direct cũ.
    Lỗi → in danh sách + exit 1, KHÔNG ghi gì; pass → hậu xử lý y đường cũ, ghi beats."""
    from autoedit.director.live import run_direct_ingest
    from autoedit.project import Project, Stage

    try:
        project = Project.load(project_dir)
        project, errors = run_direct_ingest(project, draft)
    except (FileNotFoundError, RuntimeError) as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    if errors:
        typer.secho(
            f"✗ Draft bị TRẢ VỀ — {len(errors)} lỗi, CHƯA ghi gì vào project.json:",
            fg=typer.colors.RED,
        )
        for e in errors:
            typer.echo(f"  - {e}")
        raise typer.Exit(code=1)

    record = project.stages[Stage.DIRECT]
    n_chapters = len((project.outline or {}).get("chapters", []))
    typer.secho(
        f"✓ Ingest xong: {n_chapters} chương, {len(project.beats)} beat "
        "(đường phiên sống — $0 API)",
        fg=typer.colors.GREEN,
    )
    typer.echo(f"  beats.json   : {project_dir}/beats.json  ← REVIEW BẰNG MẮT")
    for w in record.warnings:
        typer.secho(f"  ⚠ {w}", fg=typer.colors.YELLOW)


@app.command()
def enrich(
    project_dir: Path = typer.Argument(..., help="Folder project (đã direct)."),
    model: str = typer.Option("claude-sonnet-4-6", "--model", help="Model Claude API."),
    web: bool = typer.Option(False, "--web", help="Tra WEB lấy số có nguồn (đắt ~$0.4); mặc định dùng kiến thức Claude (rẻ)."),
) -> None:
    """Stage ENRICH (P2B): LLM sinh chart bổ sung + thẻ chữ.
    Mặc định dùng KIẾN THỨC nội tại Claude (rẻ, số 'minh hoạ'); --web để tra nguồn thật.
    Mọi bổ sung CHƯA duyệt — xem enrich_review.json rồi `enrich-approve`."""
    from autoedit.director.client import ClaudeDirectorClient
    from autoedit.director.enrich import run_enrich
    from autoedit.project import Project, Stage

    try:
        project = Project.load(project_dir)
    except FileNotFoundError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    client = ClaudeDirectorClient(model=model, log_dir=Path(project_dir) / "llm_log")
    mode = "web-grounded" if web else "kiến thức nội tại"
    typer.echo(f"Enrich {project.project_id} ({model}, {mode})...")
    n_cost = len(project.cost_log)
    try:
        project = run_enrich(project, client, use_web=web)
    except RuntimeError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    record = project.stages[Stage.ENRICH]
    n_chart = sum(1 for b in project.beats
                  if b.graphic_spec and b.graphic_spec.data_origin == "supplementary")
    n_card = sum(1 for b in project.beats if b.info_card)
    typer.secho(
        f"✓ Enrich xong: {n_chart} chart bổ sung + {n_card} thẻ chữ "
        f"(chi phí lần này ${_run_cost(project, n_cost)})",
        fg=typer.colors.GREEN,
    )
    typer.echo(f"  enrich_review.json: {project_dir}/enrich_review.json ← KIỂM SỐ/NGUỒN")
    typer.secho("  → Duyệt: autoedit enrich-approve <project_dir> --beat N [--beat M] hoặc --all",
                fg=typer.colors.CYAN)
    for w in record.warnings:
        typer.secho(f"  ⚠ {w}", fg=typer.colors.YELLOW)


@app.command(name="enrich-approve")
def enrich_approve(
    project_dir: Path = typer.Argument(..., help="Folder project (đã enrich)."),
    beat: list[int] = typer.Option([], "--beat", help="beat_id duyệt (lặp lại được)."),
    approve_all: bool = typer.Option(False, "--all", help="Duyệt TẤT cả bổ sung."),
) -> None:
    """Duyệt nội dung bổ sung -> approved=true (render ở source/assemble). Mặc định in trạng thái."""
    from autoedit.project import Project

    try:
        project = Project.load(project_dir)
    except FileNotFoundError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    targets = set(beat)
    n = 0
    for b in project.beats:
        items = []
        if b.graphic_spec and b.graphic_spec.data_origin == "supplementary":
            items.append(("chart", b.graphic_spec))
        if b.info_card:
            items.append(("card", b.info_card))
        for kind, obj in items:
            if approve_all or b.beat_id in targets:
                if not obj.approved:
                    obj.approved = True
                    n += 1
                    typer.secho(f"  ✓ duyệt beat {b.beat_id} [{kind}]", fg=typer.colors.GREEN)
            else:
                flag = "✓" if obj.approved else "○"
                typer.echo(f"  {flag} beat {b.beat_id} [{kind}] approved={obj.approved}")
    if n:
        project.save()
        typer.secho(f"Đã duyệt {n} mục. Chạy lại: autoedit source ... && autoedit assemble ...",
                    fg=typer.colors.CYAN)
    elif not (approve_all or targets):
        typer.echo("(Chưa duyệt gì — thêm --beat N hoặc --all để duyệt)")


@app.command()
def cut(
    project_dir: Path = typer.Argument(..., help="Folder project (đã direct)."),
) -> None:
    """Stage 3: cắt voice theo beat từ WAV master, snap điểm lặng, fade chống click.

    Thời lượng hình thở do LLM đạo diễn quyết per-beat (hook ngắn dày, thân bài thưa).
    """
    from autoedit.cutter.runner import run_cut
    from autoedit.project import Project, Stage

    try:
        project = Project.load(project_dir)
        project = run_cut(project)
    except (FileNotFoundError, RuntimeError) as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    record = project.stages[Stage.CUT]
    src_total = sum(s.source_end - s.source_start for s in project.segments)
    tl_total = project.segments[-1].timeline_end if project.segments else 0
    n_breath = sum(1 for s in project.segments if s.breathing_after > 0)
    typer.secho(
        f"✓ Cut xong: {len(project.segments)} segment, {n_breath} hình thở, "
        f"voice {src_total:.1f}s -> timeline {tl_total:.1f}s",
        fg=typer.colors.GREEN,
    )
    typer.echo(f"  segments  : {project_dir}/segments/  ← NGHE KIỂM TRA (gate M4) — xem INDEX.txt")
    for w in record.warnings:
        typer.secho(f"  ⚠ {w}", fg=typer.colors.YELLOW)


@app.command(name="insert")
def insert_cmd(
    project_dir: Path = typer.Argument(..., help="Folder project (đã direct)."),
    after_beat: Optional[int] = typer.Option(
        None, "--after-beat", help="Chèn SAU beat này (số beat xem report/INDEX)."),
    after_chapter: Optional[int] = typer.Option(
        None, "--after-chapter", help="Chèn sau beat CUỐI chương này (thay --after-beat)."),
    dur: Optional[float] = typer.Option(
        None, "--dur", help="Độ dài đoạn chèn (giây) — editor quyết, không trần."),
    note: str = typer.Option("", "--note", help="Ghi chú nội dung đoạn (report hiện lại)."),
    music: Optional[Path] = typer.Option(
        None, "--music",
        help="NHIP-M3: bài nhạc editor đưa cho đoạn chèn — THAY nhạc chương từ mép "
             "vào Δ tới HẾT chương (phương án B). Bỏ trống = dùng nhạc chương như cũ."),
    pace: str = typer.Option(
        "medium", "--pace",
        help="A′ shuffle (e2 §5): mật độ hình giữ lâu trong Δ — fast (ít hold, dồn dập) "
             "/ medium / slow (nhiều hold). Editor biết nhạc + nội dung thì chỉnh."),
    shuffle_seed: int = typer.Option(
        0, "--shuffle-seed",
        help="Đổi cách xáo RUN+HOLD (0 = tự sinh từ beat+tên bài, dựng lại y hệt). "
             "Nghe chưa ưng cách xáo -> khai số khác rồi assemble lại."),
    footage: Optional[Path] = typer.Option(
        None, "--footage",
        help="M4c: folder clip editor đưa cho Δ — copy vào project + GLM tag cỡ cảnh, "
             "source đắp vào lưới (HOLD=cảnh rộng, RUN=cận). Khai lại beat = khai lại cả cờ này."),
    prompt: str = typer.Option(
        "", "--prompt",
        help="M4c: prompt tiếng Việt cho KHO đắp bù ô còn thiếu (vd \"thiên nhiên hùng "
             "vĩ liên quan chương 1 và hình ảnh phụ nữ\") — NÃO dịch sang query kho ngay lúc khai."),
    remove: Optional[int] = typer.Option(
        None, "--remove", help="XÓA đoạn chèn đã khai sau beat này."),
) -> None:
    """NHIP-M2: khai ĐOẠN CHÈN Δ giây vào timeline (sau hình thở của beat). Không tham
    số -> liệt kê. Khai xong PHẢI chạy lại: cut -> music (nếu music-sync) -> source ->
    assemble. M2: máy giữ chỗ bằng slug; footage/nhạc đoạn chèn là mốc M4/M3."""
    from autoedit.project import InsertSpec, Project

    try:
        project = Project.load(project_dir)
    except FileNotFoundError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if remove is not None:
        before = len(project.inserts)
        project.inserts = [i for i in project.inserts if i.after_beat != remove]
        if len(project.inserts) == before:
            typer.secho(f"Không có đoạn chèn nào sau beat {remove}.", fg=typer.colors.YELLOW)
            raise typer.Exit(code=1)
        project.save()
        typer.secho(f"✓ Đã xóa đoạn chèn sau beat {remove}. Chạy lại từ `autoedit cut`.",
                    fg=typer.colors.GREEN)
        return

    if after_beat is None and after_chapter is None:
        if not project.inserts:
            typer.echo("(Chưa khai đoạn chèn nào — thêm --after-beat/--after-chapter + --dur)")
        for i in project.inserts:
            typer.echo(f"  sau beat {i.after_beat}: {i.dur:.1f}s"
                       + (f" — {i.note}" if i.note else "")
                       + (f" ♪ {Path(i.music).name}" if i.music else "")
                       + (f" 🎞 {len(i.footage_clips)} clip editor" if i.footage_clips else "")
                       + (f" 🔍 kho: {' · '.join(i.footage_queries)}" if i.footage_queries else ""))
        return

    if after_beat is not None and after_chapter is not None:
        typer.secho("Lỗi: chỉ một trong --after-beat / --after-chapter.",
                    fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    if dur is None or dur <= 0:
        typer.secho("Lỗi: cần --dur > 0 (giây).", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    if not project.beats:
        typer.secho("Lỗi: project chưa có beats — chạy `autoedit direct` trước.",
                    fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if after_chapter is not None:
        ch_beats = [b for b in project.beats if b.chapter == after_chapter]
        if not ch_beats:
            typer.secho(f"Lỗi: không có beat nào thuộc chương {after_chapter}.",
                        fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        after_beat = ch_beats[-1].beat_id
    by_id = {b.beat_id: b for b in project.beats}
    if after_beat not in by_id:
        typer.secho(f"Lỗi: beat {after_beat} không tồn tại.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    if after_beat == project.beats[-1].beat_id:
        typer.secho("Lỗi: không chèn sau beat CUỐI video (outro editor tự kéo trong CapCut).",
                    fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    # NHIP-M3: kiểm file NGAY lúc khai — path sai mà im lặng thì tới assemble mới lộ
    # (loại lỗi "hỏng-mà-vẫn-chạy": Δ vẫn dựng, chỉ mất bài editor)
    music_path = ""
    rhythm: dict = {}
    downbeat_info: dict = {}
    if music is not None:
        if not music.is_file():
            typer.secho(f"Lỗi: không thấy file nhạc {music}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        music_path = str(music.resolve())
        # NHIP-M4: đo nhịp NGAY LÚC KHAI — bài ngoài kho không có record để tra. Đo 1
        # lần ở đây (~vài giây) thay vì mỗi lần assemble. Lỗi đọc file -> fail-open:
        # Δ vẫn dựng, chỉ mất lưới beat (cảnh báo rõ để editor biết vì sao).
        typer.echo(f"  … đo nhịp {music.name} (librosa)")
        try:
            from autoedit.music.analyze import analyze_rhythm
            rhythm = analyze_rhythm(music)
        except Exception as exc:
            typer.secho(f"  ⚠ không đo được nhịp ({exc}) — Δ giữ 1 hình, không cắt theo nhịp",
                        fg=typer.colors.YELLOW)
        # NHIP-M4b (foundation e2): downbeat + meter bằng madmom RNN — librosa mù pha
        # (GT1/GT4 bàn giao M4: lưới trôi 46ms + nhóm cứng 4 beat trên bài nhịp 3).
        # GIỮ RIÊNG khỏi `rhythm`: analyze_rhythm cũng có key "downbeats" (librosa
        # nhóm-4 SAI trên nhịp 3) — trộn vào là madmom lỗi xong vẫn lưu đồ sai.
        # Lỗi (madmom chưa cài/file hỏng) -> fail-open: lưới librosa cũ vẫn chạy.
        typer.echo("  … đo downbeat (madmom RNN, ~10-30s)")
        try:
            from autoedit.music.analyze import analyze_downbeats
            downbeat_info = analyze_downbeats(music)
        except Exception as exc:
            downbeat_info = {}
            typer.secho(f"  ⚠ không đo được downbeat ({exc}) — lưới Δ dùng beat librosa "
                        "(kém pha hơn, foundation e2 khuyên cài madmom)",
                        fg=typer.colors.YELLOW)

    # M4c: footage editor + prompt kho — xử lý NGAY LÚC KHAI (cùng triết lý nhạc M3:
    # folder sai/GLM chết thì editor biết liền, không im tới assemble mới lộ).
    footage_dir = ""
    footage_clips: list = []
    footage_queries: list[str] = []
    if footage is not None:
        if not footage.is_dir():
            typer.secho(f"Lỗi: không thấy folder footage {footage}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        from autoedit.sourcer.insert_fill import ingest_insert_footage

        tagger = None
        try:
            from autoedit.library.vision import GLMVisionTagger, glm_api_keys
            keys = glm_api_keys()
            if keys:
                tagger = GLMVisionTagger(api_key=keys[0])
        except Exception:
            tagger = None
        if tagger is None:
            typer.secho("  ⚠ không có GLM key — clip không tag cỡ cảnh (ô HOLD/RUN đắp mù)",
                        fg=typer.colors.YELLOW)
        typer.echo(f"  … copy + tag cỡ cảnh folder {footage.name} (GLM)")
        footage_clips, tag_warns = ingest_insert_footage(
            footage, project_dir, tagger, context=note or prompt)
        for w in tag_warns:
            typer.secho(f"  ⚠ {w}", fg=typer.colors.YELLOW)
        if not footage_clips:
            typer.secho(f"Lỗi: folder {footage} không có file video/ảnh nào.",
                        fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        footage_dir = str(footage.resolve())
        wide = sum(1 for c in footage_clips if c.shot_size in ("wide", "aerial"))
        typer.secho(f"  ✓ {len(footage_clips)} clip editor ({wide} cảnh rộng, "
                    f"{len(footage_clips) - wide} cận/khác)", fg=typer.colors.GREEN)
    if prompt.strip():
        # NÃO dịch prompt -> query kho (NT4: chỉ NGHĨA, kèm vocab tag thật của kho C4).
        # Lỗi -> fail-open: kho đắp bù TẮT (ô thiếu giữ slug), khai lại để thử lại.
        typer.echo("  … NÃO dịch prompt kho đắp bù (1 call)")
        try:
            from autoedit.director.cc_client import ClaudeCodeDirectorClient
            from autoedit.sourcer.insert_fill import queries_from_prompt

            vocab_lines = ""
            try:
                if project.niche:
                    from autoedit.library.db import connect, vocab_for_niche
                    v = vocab_for_niche(connect(), project.niche)
                    vocab_lines = ", ".join(t for t, _ in v["tags"][:30])
            except Exception:
                pass
            footage_queries = queries_from_prompt(
                prompt.strip(), vocab_lines, ClaudeCodeDirectorClient(thinking=False))
            typer.secho("  ✓ query kho: " + " · ".join(footage_queries), fg=typer.colors.GREEN)
        except Exception as exc:
            typer.secho(f"  ⚠ NÃO dịch prompt lỗi ({exc}) — kho đắp bù TẮT, ô thiếu "
                        "giữ slug (khai lại insert để thử lại)", fg=typer.colors.YELLOW)

    from autoedit.cutter.pause import _ends_sentence
    replaced = any(i.after_beat == after_beat for i in project.inserts)
    project.inserts = [i for i in project.inserts if i.after_beat != after_beat]
    bt = list(rhythm.get("beat_times") or [])
    bs = list(rhythm.get("beat_strength") or [])
    # BPM suy từ CHÍNH beat_times: `analyze_rhythm` (M0) chỉ đo nhịp, key "bpm" thuộc
    # `analyze_track` (mood/energy/sections) nên không có ở đây — đọc nó ra 0.0.
    # Trung vị chống outlier ở mép bài (beat đầu/cuối hay lệch).
    bpm = 0.0
    if len(bt) > 1:
        import statistics
        per = statistics.median(b - a for a, b in zip(bt, bt[1:]))
        bpm = round(60.0 / per, 1) if per > 0 else 0.0
    project.inserts.append(InsertSpec(
        after_beat=after_beat, dur=dur, note=note, music=music_path,
        music_beats=bt, music_beat_strength=bs if len(bs) == len(bt) else [],
        music_bpm=bpm, music_tier=str(rhythm.get("beat_tier") or ""),
        music_downbeats=list(downbeat_info.get("downbeats") or []),
        music_meter=int(downbeat_info.get("meter") or 0),
        music_pace=pace if pace in ("fast", "medium", "slow") else "medium",
        shuffle_seed=shuffle_seed,
        footage_dir=footage_dir, footage_prompt=prompt.strip(),
        footage_queries=footage_queries, footage_clips=footage_clips,
    ))
    project.inserts.sort(key=lambda i: i.after_beat)
    project.save()
    verb = "Đã SỬA" if replaced else "Đã khai"
    typer.secho(f"✓ {verb} đoạn chèn {dur:.1f}s sau beat {after_beat}"
                + (f" (cuối chương {after_chapter})" if after_chapter is not None else ""),
                fg=typer.colors.GREEN)
    if music_path:
        typer.secho(f"  ♪ nhạc editor: {Path(music_path).name} — THAY nhạc chương "
                    f"{by_id[after_beat].chapter} từ đoạn chèn tới hết chương (phương án B)",
                    fg=typer.colors.GREEN)
        if bt:
            tier = str(rhythm.get("beat_tier") or "?")
            msg = f"  ♪ nhịp: {bpm:.1f} BPM, {len(bt)} beat, tier {tier}"
            downs = list(downbeat_info.get("downbeats") or [])
            meter = int(downbeat_info.get("meter") or 0)
            if tier in ("A", "B") and len(downs) >= 2 and meter in (3, 4):
                # lưới CÔNG THỨC (foundation e2): nhịp 3 cắt phách 1 (1 bar/hình),
                # nhịp 4 cắt phách 1&3 (nửa bar/hình) — bội số nếu ngắn hơn sàn
                import statistics
                bar = statistics.median(b - a for a, b in zip(downs, downs[1:]))
                base = bar if meter == 3 else bar / 2
                from autoedit.packager.coverage import INSERT_TARGET_SHOT
                mult = max(1, round(INSERT_TARGET_SHOT / base))
                shot = base * mult
                msg += (f" · madmom: nhịp {meter}, {len(downs)} downbeat, ô nhịp {bar:.2f}s"
                        f" → lưới công thức unit {shot:.2f}s + shuffle RUN+HOLD"
                        f" (pace {pace}, hold {shot * 2:.0f}s)")
            elif tier in ("A", "B") and bpm > 0:
                from autoedit.packager.coverage import INSERT_TARGET_SHOT
                k = max(2, round(INSERT_TARGET_SHOT / (60.0 / bpm)))
                shot = k * 60.0 / bpm
                msg += (f" → cắt ~{k} beat/hình (~{shot:.1f}s), Δ {dur:.0f}s ≈ {int(dur / shot)} hình"
                        " (⚠ lưới librosa — không có downbeat madmom)")
            else:
                msg += " → tier C (ambient): KHÔNG cắt theo nhịp, Δ giữ 1 hình"
            typer.secho(msg, fg=typer.colors.CYAN)
    if not _ends_sentence(by_id[after_beat].text):
        typer.secho(f"  ⚠ beat {after_beat} không kết thúc bằng dấu câu — đoạn chèn sẽ "
                    "ngắt giữa ý nói; cân nhắc chọn beat kết câu/cuối chương",
                    fg=typer.colors.YELLOW)
    typer.secho("  Chạy lại: autoedit cut -> music (nếu music-sync) -> source -> assemble "
                "(timeline đổi, music_plan cũ sẽ tự xóa).", fg=typer.colors.CYAN)


@app.command(name="music")
def music_cmd(
    project_dir: Path = typer.Argument(..., help="Folder project (đã cut)."),
    lib: Optional[Path] = typer.Option(None, "--lib", help="Thư viện nhạc (mặc định ~/AutoEdit/music)."),
    niche: str = typer.Option(
        "", "--niche",
        help="Niche có pool nhạc RIÊNG (vd life-in) — music chạy TRƯỚC source nên "
             "project.niche thường chưa có, PHẢI truyền tay cho niche pool riêng."),
    sync_targets: str = typer.Option(
        "accent", "--sync-targets",
        help="M4 thử nghiệm: 'grid' = hook snap theo DOWNBEAT (tier A) thay accent. Mặc định accent."),
) -> None:
    """MUSIC SYNC M1 — stage music (OPTIONAL, giữa cut và source): chọn nhạc per-chapter
    TRƯỚC assemble (thuật toán cũ nguyên vẹn) + neo offset vào accent/downbeat.
    Không chạy stage này thì assemble tự chọn nhạc như cũ."""
    from autoedit.music.library import music_root_for
    from autoedit.music.plan import run_music
    from autoedit.project import Project, Stage

    st = sync_targets if isinstance(sync_targets, str) else "accent"
    nch = niche if isinstance(niche, str) else ""
    if st not in ("accent", "grid"):
        typer.secho(f"Lỗi: --sync-targets phải là accent|grid (nhận '{st}')",
                    fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    try:
        project = Project.load(project_dir)
        # pool nhạc theo niche: --lib thắng; rồi --niche/project.niche có pool riêng
        # -> CHỈ pool đó; còn lại pool chung (music_root_for)
        lib_root = lib if isinstance(lib, (str, Path)) and lib \
            else music_root_for(nch or project.niche)
        typer.echo(f"  pool nhạc: {lib_root}")
        project.music_sync_targets = st
        project = run_music(project, Path(lib_root))
    except (FileNotFoundError, RuntimeError) as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    record = project.stages[Stage.MUSIC]
    typer.secho(f"✓ Music plan: {len(project.music_plan)} chương", fg=typer.colors.GREEN)
    for p in project.music_plan:
        typer.echo(f"  ch{p.chapter_id}: {Path(p.file).stem} [{p.beat_tier}] "
                   f"offset {p.start_offset:.2f}s — {p.anchor_note}")
    for w in record.warnings:
        typer.secho(f"  ⚠ {w}", fg=typer.colors.YELLOW)


@app.command()
def source(
    project_dir: Path = typer.Argument(..., help="Folder project (đã cut)."),
    niche: str = typer.Option("", "--niche", help="Niche thư viện local (P6), vd retirement-abroad."),
    library_root: Optional[Path] = typer.Option(
        None, "--library-root", help="Ghi đè thư mục thư viện (mặc định lấy từ machine.json)."),
    rank: bool = typer.Option(
        True, "--rank/--no-rank",
        help="Phễu c5: NÃO chấm ứng viên (1 call/beat, qua Claude Code). --no-rank = heuristic cũ."),
    rank_model: str = typer.Option(
        "claude-sonnet-4-6", "--rank-model", help="Model NÃO chấm phễu (alias 'sonnet'/'opus' được)."),
    ref: Optional[list[Path]] = typer.Option(
        None, "--ref",
        help="Folder/video NGUỒN MẪU CỦA BÀI (lặp được) — cảnh từ nguồn này được chèn "
             "pool (match nới) + bonus phễu + trần viral 15% thay 8%. Khai 1 lần, "
             "dính vào project.json cho các lần chạy sau."),
    boost: Optional[list[str]] = typer.Option(
        None, "--boost",
        help="Cảnh dạng X khán giả thích, 'X@scope' (lặp được; scope all|hook|ch<N>, "
             "mặc định all; X = tiếng Anh theo từ vựng tag kho, vd 'beautiful woman'). "
             "Chèn cảnh KHO + bonus phễu; cộng với audience_bias của niche. Dính vào "
             "project.json. MO_TA_VAN_HANH_BOOST.md"),
) -> None:
    """Stage 4: tải footage theo sourcing_route — local -> Pexels; entity -> Google CSE.
    Chọn qua PHỄU c5 (2 veto + NÃO chấm + sàn 3 + kill-log — MO_TA_VAN_HANH_PHEU_C5.md)."""
    import os

    from dotenv import load_dotenv

    from autoedit.library import db
    from autoedit.library.profile import resolve_library_root
    from autoedit.project import Project, Stage, StageStatus
    from autoedit.sourcer.entity import GoogleCSEClient, SerperEntityClient
    from autoedit.sourcer.pexels import PexelsClient, collect_pexels_keys
    from autoedit.sourcer.runner import run_source

    # khi run() gọi trực tiếp, library_root là OptionInfo (không phải str/Path) -> coi như None
    root = resolve_library_root(library_root if isinstance(library_root, (str, Path)) else None)
    load_dotenv()
    pexels_keys = collect_pexels_keys()
    if not pexels_keys:
        typer.secho("Lỗi: thiếu PEXELS_API_KEY trong .env", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.echo(f"  Pexels: {len(pexels_keys)} key (xoay vòng khi hết hạn mức ~200 query/giờ/key)")

    conn = db.connect()
    stock = PexelsClient(pexels_keys, conn=conn)
    entity = None
    for client_cls in (SerperEntityClient, GoogleCSEClient):  # Serper chính, CSE legacy
        try:
            entity = client_cls(conn=conn)
            break
        except RuntimeError:
            continue
    if entity is None:
        typer.secho(
            "⚠ Route entity tắt: thiếu SERPER_API_KEY (serper.dev, 2.500 query free) "
            "— beat entity sẽ là needs_human", fg=typer.colors.YELLOW,
        )

    # khi run() gọi trực tiếp, rank/rank_model là OptionInfo -> lấy mặc định (bug B2)
    use_rank = rank if isinstance(rank, bool) else True
    rmodel = rank_model if isinstance(rank_model, str) else "claude-sonnet-4-6"
    brain = None
    gate = None
    if use_rank:
        from autoedit.director.cc_client import ClaudeCodeDirectorClient
        # PA-1+2 (2026-07-07): batch ~10 beat/call + tắt thinking — sonnet là trần model
        brain = ClaudeCodeDirectorClient(model=rmodel, log_dir=Path(project_dir) / "llm_log",
                                         thinking=False)
        typer.echo(f"  Phễu c5: NÃO chấm qua Claude Code ({rmodel}), batch ~10 beat/call, thinking OFF")
        # C5 đợt 5: mắt vision soi lead-pick mọi beat qua phễu (fail-open, tắt khi thiếu key)
        try:
            from autoedit.ranker.visiongate import VisionGate
            gate = VisionGate()
            typer.echo("  C5 vision gate: GLM-4.6V soi lead-pick KHO LOCAL (1 frame 960px, demote tối đa 1 lần/beat)")
        except Exception as exc:
            typer.secho(f"  C5 vision gate TẮT ({exc})", fg=typer.colors.YELLOW)

    def show(i: int, total: int, beat) -> None:
        typer.echo(f"  [{i}/{total}] beat {beat.beat_id} [{beat.sourcing_route}] {beat.visual_concept[:42]}")

    try:
        project = Project.load(project_dir)
        # REF: --ref khai mới -> ghi đè vào project (dính); không khai -> dùng bản đã khai
        # (run() gọi trực tiếp thì ref là OptionInfo -> coi như không khai, bug B2)
        if isinstance(ref, list) and ref:
            project.inputs.ref_sources = [str(p) for p in ref]
        ref_sources = project.inputs.ref_sources
        if ref_sources:
            typer.echo(f"  REF nguồn mẫu của bài: {len(ref_sources)} prefix — trần viral 15%")
        # BOOST: cùng khuôn --ref (dính + chống OptionInfo bug B2). audience_bias của
        # niche merge TRONG run_source (chokepoint) — ở đây chỉ lo phần khai per-video.
        if isinstance(boost, list) and boost:
            project.inputs.boosts = [str(b) for b in boost]
            direct_rec = project.stages.get(Stage.DIRECT)
            if direct_rec is not None and direct_rec.status == StageStatus.DONE:
                typer.secho(
                    "  ⚠ BOOST khai SAU direct — NÃO viết concept chưa biết X (tầng chèn"
                    "+bonus vẫn ăn); muốn NÃO đan X vào concept: chạy lại direct",
                    fg=typer.colors.YELLOW)
        if project.inputs.boosts:
            typer.echo(f"  BOOST khán giả: {len(project.inputs.boosts)} khai — chèn kho + bonus phễu")
        project = run_source(project, conn, stock, entity, niche=niche,
                             library_root=root, on_progress=show, brain=brain, gate=gate,
                             ref_sources=ref_sources, boosts=project.inputs.boosts)
    except (FileNotFoundError, RuntimeError) as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    from collections import Counter

    record = project.stages[Stage.SOURCE]
    by_status = Counter(s.status for s in project.shots)
    by_source = Counter(s.source for s in project.shots if s.asset_path)
    typer.secho(
        f"✓ Source xong: {len(project.shots)} beat — {dict(by_status)}",
        fg=typer.colors.GREEN,
    )
    typer.echo(f"  nguồn asset : {dict(by_source)}")
    typer.echo(f"  assets      : {project_dir}/assets/")
    for s in project.shots:
        flag = " ⚠licensing" if s.licensing_flag else ""
        typer.echo(f"  b{s.beat_id:02d} [{s.status}/{s.source}]{flag} {s.asset_path or s.note[:60]}")
    for w in project.stages[Stage.RANK].warnings:  # kill-log tổng phễu c5
        typer.echo(f"  {w}")
    for w in record.warnings:
        typer.secho(f"  ⚠ {w}", fg=typer.colors.YELLOW)


@app.command()
def assemble(
    project_dir: Path = typer.Argument(..., help="Folder project (đã source)."),
    music: Optional[Path] = typer.Option(None, "--music", help="1 file nhạc cố định (override tay)."),
    music_lib: Optional[Path] = typer.Option(None, "--music-lib", help="Thư viện nhạc → tự chọn theo mood chương."),
    sfx_dir: Optional[Path] = typer.Option(None, "--sfx-dir", help="Thư mục SFX (mặc định ~/AutoEdit/sfx/)."),
    footage_speed: Optional[float] = typer.Option(
        None, "--footage-speed", min=0.5, max=2.0,
        help="Tốc độ phát footage video (mặc định 0.9 = chậm 10%; 1.0 = tốc độ gốc)."),
    credit: bool = typer.Option(
        False, "--credit",
        help="VD4 ghi công: gắn TÊN KÊNH nguồn (cột source_channel trong sổ) ở 1 trong "
             "4 góc màn hình cho từng miếng footage — cần kho đã điền kênh "
             "(library-ingest --channel / channel-set)."),
    epidemic: bool = typer.Option(
        False, "--epidemic",
        help="BẬT SFX nguồn Epidemic Sound cho lần dựng này (mặc định TẮT — user chốt "
             "2026-07-18). Kho vẫn giữ nguyên file, bật là dùng được ngay."),
    sfx_llm: bool = typer.Option(
        False, "--sfx-llm",
        help="NÃO chấm tiếng chủ thể cho cảnh BẢNG LUẬT MÙ CHỮ (subject viết chữ tự do "
             "như 'Omani village' — cảnh phố thật mà không từ khóa nào lọt bảng, hiện "
             "đang im oan). Chỉ chấm phần đuôi đó, 1 call/mẻ; lỗi -> giữ bảng luật."),
) -> None:
    """Stage 6: ráp draft CapCut (video + voice + nhạc + overlay text/SFX) — mở trong CapCut.
    Nhạc: --music (1 file loop) HOẶC --music-lib (tự chọn theo mood từng chương)."""
    from autoedit.music.library import music_root_for
    from autoedit.packager.assembler import run_assemble
    from autoedit.packager.machine import MachineProfile
    from autoedit.project import Project, Stage
    from autoedit.sfx.library import SFX_ROOT

    if sfx_dir is None and SFX_ROOT.is_dir():
        sfx_dir = SFX_ROOT  # mặc định dùng thư viện SFX (P1.4)
    # fallback: thiếu kind trong thư viện -> sfx demo (đỡ trống tiếng)
    sfx_fallback = Path(__file__).resolve().parents[2] / "capcut_test" / "assets" / "sfx.mp3"
    try:
        profile = MachineProfile.load()
        project = Project.load(project_dir)
        # OptionInfo khi gọi trực tiếp (bug 13/06) -> coi như không tắt
        # OptionInfo khi gọi trực tiếp (bug 13/06) -> `is True` coi như KHÔNG bật.
        # Cả 2 cờ giờ cùng chiều "mặc định tắt, gõ cờ mới bật" — không còn phủ định kép.
        project.use_epidemic_sfx = epidemic is True
        project.sfx_llm = sfx_llm is True
        if music is None and music_lib is None:
            # mặc định auto từ thư viện nhạc — pool theo NICHE (music_root_for):
            # niche có pool riêng -> CHỈ pool đó; còn lại pool chung như cũ
            auto_lib = music_root_for(project.niche)
            if auto_lib.is_dir():
                music_lib = auto_lib
        project = run_assemble(project, profile, music_path=music,
                               sfx_dir=sfx_dir, sfx_fallback=sfx_fallback, music_lib=music_lib,
                               footage_speed=footage_speed, credit=credit)
    except (FileNotFoundError, RuntimeError) as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    record = project.stages[Stage.ASSEMBLE]
    typer.secho(f"✓ Draft đã sinh: {project.draft_path}", fg=typer.colors.GREEN)
    typer.echo("  Mở CapCut → draft phải xuất hiện, xem được video nháp hoàn chỉnh (gate Phase 0).")
    for w in record.warnings:
        typer.secho(f"  ⚠ {w}", fg=typer.colors.YELLOW)


@app.command()
def report(
    project_dir: Path = typer.Argument(..., help="Folder project (đã source/assemble)."),
) -> None:
    """Stage 7: sinh report.html bàn giao editor (checklist 20% cuối) — CHỈ đọc project.json."""
    from autoedit.project import Project
    from autoedit.report.runner import run_report

    try:
        project = run_report(Project.load(project_dir))
    except (FileNotFoundError, RuntimeError) as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.secho(f"✓ Report: {project.report_path}", fg=typer.colors.GREEN)
    typer.echo(f"  Mở bằng trình duyệt: open {project.report_path}")


@app.command()
def run(
    project_dir: Path = typer.Argument(..., help="Folder project (tạo bằng `new`)."),
    niche: str = typer.Option("", "--niche", help="Niche thư viện local cho stage source."),
    music: Optional[Path] = typer.Option(None, "--music", help="File nhạc nền cho stage assemble."),
    model: str = typer.Option("small", "--whisper-model", help="Model faster-whisper cho align."),
    language: str = typer.Option("auto", "--language", help="Ngôn ngữ voice: auto/en/vi..."),
    align_backend: str = typer.Option("auto", "--align-backend",
                                      help="Nguồn timestamp stage align: auto | srt | whisper."),
    srt: Optional[Path] = typer.Option(None, "--srt", help="Đường dẫn .srt cho stage align."),
    director_model: str = typer.Option("claude-sonnet-4-6", "--director-model", help="Model LLM đạo diễn."),
    with_enrich: bool = typer.Option(False, "--enrich", help="Chèn stage enrich (web-grounded; bổ sung CẦN duyệt mới render)."),
    music_sync: bool = typer.Option(False, "--music-sync", help="MUSIC SYNC: chèn stage music (chọn nhạc + neo accent TRƯỚC assemble). Mặc định TẮT."),
    footage_speed: Optional[float] = typer.Option(
        None, "--footage-speed", min=0.5, max=2.0,
        help="Tốc độ phát footage video ở stage assemble (mặc định 0.9 = chậm 10%)."),
    epidemic: bool = typer.Option(
        False, "--epidemic",
        help="BẬT SFX nguồn Epidemic Sound cho lần dựng này (mặc định TẮT)."),
    sfx_llm: bool = typer.Option(
        False, "--sfx-llm",
        help="NÃO chấm tiếng chủ thể cho cảnh bảng luật MÙ CHỮ (xem `assemble --sfx-llm`)."),
) -> None:
    """Chạy MỌI stage còn thiếu theo thứ tự: align → direct → [enrich] → cut → [music] → source → assemble.

    Resume từ project.json (nguyên tắc #1): stage nào DONE thì bỏ qua.
    --enrich: sinh bổ sung (chart web-grounded + thẻ chữ) — KHÔNG render tới khi `enrich-approve`.
    --music-sync: bật gói MUSIC SYNC (mặc định TẮT — không bật thì assemble tự chọn nhạc như cũ).
    """
    from autoedit.project import Project, Stage, StageStatus

    try:
        project = Project.load(project_dir)
    except FileNotFoundError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    def done(stage: Stage) -> bool:
        rec = project.stages.get(stage)  # .get: project.json cũ thiếu key stage mới (music)
        return rec is not None and rec.status == StageStatus.DONE

    order = [Stage.ALIGN, Stage.DIRECT]
    if with_enrich:
        order.append(Stage.ENRICH)
    order.append(Stage.CUT)
    if music_sync is True:  # OptionInfo khi gọi trực tiếp -> coi như tắt (bug B2)
        order.append(Stage.MUSIC)
    order += [Stage.SOURCE, Stage.ASSEMBLE, Stage.REPORT]
    plan = [s for s in order if not done(s)]
    if not plan:
        typer.echo("Mọi stage đã xong — draft tại: " + (project.draft_path or "?"))
        return
    typer.echo("Pipeline sẽ chạy: " + " → ".join(s.value for s in plan))

    # LƯU Ý: gọi hàm lệnh typer trực tiếp thì PHẢI truyền đủ tham số tường minh —
    # default typer.Option chỉ được resolve qua CLI (bug OptionInfo 13/06)
    n_stage = len(plan)
    import time as _time
    t0 = _time.time()
    for si, stage in enumerate(plan, start=1):
        elapsed = int(_time.time() - t0)
        typer.secho(f"\n━━ [{si}/{n_stage}] {stage.value}  (đã chạy {elapsed//60}m{elapsed%60:02d}s) ━━", bold=True)
        if stage == Stage.ALIGN:
            align(project_dir, model=model, language=language, backend=align_backend, srt=srt)
        elif stage == Stage.DIRECT:
            direct(project_dir, model=director_model, engine="claude-code")
        elif stage == Stage.ENRICH:
            enrich(project_dir, model=director_model)
        elif stage == Stage.CUT:
            cut(project_dir)
        elif stage == Stage.MUSIC:
            # truyền niche tường minh (bug OptionInfo 13/06) — pool nhạc riêng của niche
            music_cmd(project_dir, lib=None, niche=niche)
        elif stage == Stage.SOURCE:
            source(project_dir, niche=niche)
        elif stage == Stage.ASSEMBLE:
            # credit=False tường minh (bug OptionInfo 13/06 — thiếu thì nhận OptionInfo
            # truthy -> bật ghi công VD4 ngoài ý muốn; phát hiện khi rà P5 2026-07-17)
            assemble(project_dir, music=music, music_lib=None, sfx_dir=None,
                     footage_speed=footage_speed, credit=False,
                     epidemic=epidemic is True, sfx_llm=sfx_llm is True)
        elif stage == Stage.REPORT:
            report(project_dir)

    typer.secho("\n✓ Pipeline hoàn tất — mở CapCut + report.html kiểm tra.", fg=typer.colors.GREEN)


@app.command(name="set-library-root")
def set_library_root_cmd(
    path: Path = typer.Argument(..., help="Folder thư viện footage, vd F:\\FOOTAGE."),
) -> None:
    """Đặt thư mục thư viện footage cho máy này (ghi vào machine.json — nhớ vĩnh viễn).

    Sau lệnh này, mọi `library-index` / `source` / `make` tự dùng folder này, editor
    không phải gõ gì. Footage để ở ổ lớn (F:) thay vì ổ C."""
    from autoedit.packager.machine import set_library_root

    path = path.expanduser()
    if not path.is_dir():
        typer.secho(f"⚠ Folder chưa tồn tại: {path} (vẫn lưu — tạo trước khi index).",
                    fg=typer.colors.YELLOW)
    try:
        set_library_root(path)
    except FileNotFoundError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.secho(f"✓ Thư viện footage: {path}", fg=typer.colors.GREEN)
    typer.echo(f"  Mỗi niche là 1 folder con, vd {path}\\<niche>/. Chạy library-index <niche> để tag.")


@app.command(name="set-draft-root")
def set_draft_root_cmd(
    path: Path = typer.Argument(..., help="Folder xuất draft mới, vd E:\\CapCut Drafts."),
) -> None:
    """Đặt folder XUẤT draft CapCut cho máy này (ghi vào machine.json — nhớ vĩnh viễn).

    Draft mới sẽ ghi vào đây thay vì com.lveditor.draft (donor/register-machine không
    đổi). Muốn thấy draft trong CapCut máy này: Settings CapCut → Draft location trỏ
    cùng folder. Draft sinh ra đã PORTABLE — copy nguyên folder sang máy editor là mở."""
    from autoedit.packager.machine import set_draft_out_root

    path = path.expanduser()
    if not path.is_dir():
        typer.secho(f"⚠ Folder chưa tồn tại: {path} (vẫn lưu — sẽ tự tạo khi sinh draft).",
                    fg=typer.colors.YELLOW)
    try:
        set_draft_out_root(path)
    except FileNotFoundError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.secho(f"✓ Folder xuất draft: {path}", fg=typer.colors.GREEN)


@app.command(name="set-data-root")
def set_data_root_cmd(
    path: Path = typer.Argument(..., help="Gốc dữ liệu chung (cache.db + music + sfx), vd F:\\AutoEdit."),
) -> None:
    """G1: đặt gốc dữ liệu chung cho máy này (ghi machine.json — nhớ vĩnh viễn).

    Sau lệnh này cache.db + music/ + sfx/ đọc/ghi tại <path> thay vì ~\\AutoEdit —
    nhiều máy trỏ cùng 1 chỗ trên ổ mạng = sổ tag + sổ đã-dùng DÙNG CHUNG.
    Nhớ: process đang chạy không tự đổi — mở terminal/job mới sau khi set."""
    from autoedit.packager.machine import set_data_root

    path = path.expanduser()
    for sub in ("cache.db", "music", "sfx"):
        if not (path / sub).exists():
            typer.secho(f"⚠ Chưa thấy {path / sub} — kiểm đã copy dữ liệu tới đó chưa.",
                        fg=typer.colors.YELLOW)
    try:
        set_data_root(path)
    except FileNotFoundError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.secho(f"✓ Gốc dữ liệu chung: {path}", fg=typer.colors.GREEN)


@app.command(name="set-db-url")
def set_db_url_cmd(
    url: str = typer.Argument("", help="postgresql://user:pass@host:5432/autoedit"),
    clear: bool = typer.Option(False, "--clear", help="Xóa db_url — SỔ về SQLite tại data_root (đường lui G2)."),
) -> None:
    """G2: đặt URL Postgres cho SỔ của máy này (ghi machine.json — nhớ vĩnh viễn).

    Sau lệnh này mọi process MỚI đọc/ghi sổ (asset/usage/search cache/stock tags)
    trên Postgres; kho FILE (footage/nhạc/SFX) vẫn theo data_root như G1.
    Đường lui bất kỳ lúc nào: `autoedit set-db-url --clear` — về SQLite ngay."""
    from autoedit.library import db
    from autoedit.packager.machine import set_db_url

    if not clear and not url:
        typer.secho("Cần URL (hoặc --clear để về SQLite).", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    try:
        set_db_url("" if clear else url)
    except FileNotFoundError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    if clear:
        typer.secho("✓ Đã xóa db_url — sổ về SQLite tại data_root (G1).", fg=typer.colors.GREEN)
        return
    try:  # thử kết nối ngay cho biết sống/chết (fail vẫn lưu — server có thể chưa bật)
        db.connect(db_url=url).close()
        typer.secho(f"✓ Sổ Postgres: {url} (kết nối OK)", fg=typer.colors.GREEN)
    except Exception as exc:
        typer.secho(f"⚠ Đã lưu nhưng CHƯA kết nối được: {exc}", fg=typer.colors.YELLOW)


@app.command(name="library-init")
def library_init_cmd(
    niche: str = typer.Argument(..., help="Tên niche (ASCII slug, vd retirement-abroad)."),
    library_root: Optional[Path] = typer.Option(
        None, "--library-root", help="Ghi đè thư mục thư viện (mặc định lấy từ machine.json)."),
) -> None:
    """Scaffold <library_root>/<niche>/ + niche_profile.yaml mẫu (người điền tiếp)."""
    from autoedit.library.profile import init_niche, resolve_library_root

    root = resolve_library_root(library_root)
    d = init_niche(niche, root=root)
    typer.secho(f"✓ Niche '{niche}' tại {d}", fg=typer.colors.GREEN)
    typer.echo("  1. Điền niche_profile.yaml (safe_pool / audience_bias / banned)")
    typer.echo("  2. Bỏ footage chữ ký vào signature/, chủ đề con vào folder riêng")
    typer.echo(f"  3. Chạy: autoedit library-index {niche}")


def _vision_taggers(engine: str, model: Optional[str], angle: bool) -> list:
    """Dựng list tagger theo engine. GLM: 1 tagger/key (PB3-B2 multi-key round-robin,
    GLM_API_KEY + GLM_API_KEY_2..9); claude: 1 tagger."""
    from autoedit.library.vision import (
        DEFAULT_GLM_VISION_MODEL,
        DEFAULT_VISION_MODEL,
        ClaudeVisionTagger,
        GLMVisionTagger,
        glm_api_keys,
    )

    if engine == "glm":
        keys = glm_api_keys()
        if not keys:
            typer.secho("Lỗi: thiếu GLM_API_KEY trong .env (bigmodel.cn).",
                        fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        return [GLMVisionTagger(model=model or DEFAULT_GLM_VISION_MODEL,
                                api_key=k, want_angle=angle) for k in keys]
    if engine == "claude":
        return [ClaudeVisionTagger(model=model or DEFAULT_VISION_MODEL, want_angle=angle)]
    typer.secho(f"Lỗi: --engine phải là glm hoặc claude (nhận '{engine}').",
                fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1)


@app.command(name="library-index")
def library_index_cmd(
    niche: str = typer.Argument(..., help="Tên niche đã init."),
    engine: str = typer.Option(
        "glm", "--engine", help="glm (GLM-4.6V native, mặc định — CLAUDE.md §5) | claude (fallback)."),
    model: Optional[str] = typer.Option(
        None, "--model", help="Ghi đè model vision (mặc định theo engine)."),
    angle: bool = typer.Option(
        False, "--angle", help="Mẻ thử camera_angle (c7): tag thêm góc máy để đo tin cậy."),
    library_root: Optional[Path] = typer.Option(
        None, "--library-root", help="Ghi đè thư mục thư viện (mặc định lấy từ machine.json)."),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Chạy thử: dừng sau khi tag MỚI N file (đo chi phí trước khi chạy full)."),
) -> None:
    """Tag mọi footage trong thư viện niche bằng vision LLM → cache.db (file đổi mới tag lại)."""
    from autoedit.library import db
    from autoedit.library.indexer import WORKERS_PER_KEY, index_niche
    from autoedit.library.profile import NicheProfile, niche_dir, resolve_library_root

    d = niche_dir(niche, root=resolve_library_root(library_root))
    try:
        NicheProfile.load(d)  # bắt buộc có profile trước khi index
    except FileNotFoundError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    taggers = _vision_taggers(engine, model, angle)
    if (b := db.backup_cache_db()):  # G1: sổ có thể dùng chung trên ổ mạng
        typer.echo(f"  backup sổ trước mẻ: {b}")
    conn = db.connect()
    typer.echo(f"Index {d} (vision {engine}, {len(taggers)} key × {WORKERS_PER_KEY} luồng)... "
               "Ctrl+C ngắt an toàn, chạy lại sẽ tiếp tục chỗ cũ.")

    def show(i: int, total: int, path) -> None:
        typer.echo(f"  [{i}/{total}] {path.name}")

    result = index_niche(conn, niche, d, taggers, on_progress=show, limit=limit,
                         stagger_s=2.0)
    typer.secho(
        f"✓ Tag mới {len(result.indexed)}, đổi chỗ {result.moved} (giữ tag cũ), "
        f"bỏ qua {result.skipped} (không đổi), dọn {result.pruned} dòng chết, "
        f"lỗi {len(result.failed)} — tổng trong db: {db.count_assets(conn, niche)}",
        fg=typer.colors.GREEN,
    )
    for path, err in result.failed:
        typer.secho(f"  ⚠ {path}: {err}", fg=typer.colors.YELLOW)


@app.command(name="library-ingest")
def library_ingest_cmd(
    niche: str = typer.Argument(..., help="Tên niche đã init (đích trong thư viện)."),
    draft: Path = typer.Argument(..., help="Folder draft CapCut NGUỒN (chỉ đọc), "
                                           "vd 'E:\\PROJECT NHAN BAN\\SPACE 1\\SP1 - 003'."),
    engine: str = typer.Option(
        "glm", "--engine", help="glm (mặc định) | claude (fallback)."),
    model: Optional[str] = typer.Option(None, "--model", help="Ghi đè model vision."),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Chạy thử: chỉ xử lý N cảnh đầu."),
    source_class: str = typer.Option(
        "own", "--source-class",
        help="own (mặc định — kho editor công ty) | viral (nguồn kênh khác, c8+ytref: "
             "cờ điểm nhô + >20s bỏ trừ điểm nhô + bóp 6s + zoom 112% + nhãn db)."),
    topic: str = typer.Option(
        "", "--topic",
        help="ytref §3i: 1 dòng chủ đề bộ nguồn (vd 'the Moon, lunar exploration') — "
             "vào prompt vision cùng bậc tiêu đề nguồn; dùng khi tên file là mã số."),
    channel: str = typer.Option(
        "", "--channel",
        help="VD4 ghi công: KÊNH nguồn của cả mẻ (explicit thắng). Không khai + mẻ viral "
             "có YouTube ID -> tự lấy tên kênh yt-dlp từng file nguồn."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Chỉ đọc + đếm cảnh (viral: soi luôn YouTube ID/heatmap/"
                                 "điểm nhô), KHÔNG cắt/tag."),
    retag: bool = typer.Option(
        False, "--retag", help="TCF M2: ÉP tag lại cảnh đã có trong db (hồi tố tag "
                               "bối cảnh) — không cắt lại clip, đè tag cũ; chạy đúng "
                               "--source-class như mẻ gốc."),
    library_root: Optional[Path] = typer.Option(
        None, "--library-root", help="Ghi đè thư mục thư viện (mặc định machine.json)."),
) -> None:
    """PB4: nạp draft CapCut nguồn → cắt cảnh theo mép editor (C4) → tag → cache.db.

    Draft nguồn CHỈ ĐỌC. Clip cắt vào <niche>/nap/<tên draft>/. Chạy lại tự resume
    (clip đã cắt không cắt lại, asset đã tag không tag lại)."""
    from autoedit.library import db
    from autoedit.library.indexer import WORKERS_PER_KEY
    from autoedit.library.ingest import (
        CONTEXT_FILE, MIN_SCENE_S, VIRAL_DROP_S, VIRAL_MAX_S, VIRAL_ZOOM,
        apply_viral_rules, ingest_draft, read_draft_context, read_draft_scenes,
        youtube_infos_for)
    from autoedit.library.profile import NicheProfile, niche_dir, resolve_library_root

    if source_class not in ("own", "viral"):
        typer.secho(f"Lỗi: --source-class '{source_class}' — chỉ nhận own | viral.",
                    fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    if not (draft / "draft_content.json").is_file():
        typer.secho(f"Lỗi: không thấy draft_content.json trong {draft}",
                    fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    d = niche_dir(niche, root=resolve_library_root(library_root))
    try:
        NicheProfile.load(d)
    except FileNotFoundError as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if dry_run:
        scenes, stats = read_draft_scenes(draft)
        total_s = sum(s.duration for s in scenes)
        n_voice = sum(1 for s in scenes if s.has_voice == 1)
        typer.echo(f"Draft {draft.name}: {stats['segments']} segment video/photo "
                   f"→ {len(scenes)} cảnh thành asset ({total_s:.0f}s nguồn, "
                   f"{n_voice} cảnh có voice)")
        typer.echo(f"  Bỏ: thiếu file {stats['missing_file']} · cache CapCut "
                   f"{stats['cache_material']} · <{MIN_SCENE_S:.0f}s {stats['too_short']} · "
                   f"trùng {stats['duplicate']} · thiếu source range {stats['no_source_range']}")
        # spec TCF: soi file bối cảnh editor trước khi tốn tiền (văn hóa PB6)
        ctx = read_draft_context(draft)
        if ctx.topic or ctx.chapters:
            typer.echo(f"  Bối cảnh '{CONTEXT_FILE}': tiêu đề \"{ctx.topic[:70]}\" · "
                       f"{len(ctx.chapters)} chapter"
                       + ("" if not ctx.chapters else " (" + " · ".join(
                           f"{int(c['start_time']) // 60}:{int(c['start_time']) % 60:02d} "
                           f"{c['title'][:30]}" for c in ctx.chapters[:2]) + " ...)"))
        elif source_class == "own" and not topic:
            typer.secho(f"  ⚠ own thiếu chủ đề: không thấy '{CONTEXT_FILE}' và không có "
                        "--topic — tag sẽ mù chủ đề như cũ", fg=typer.colors.YELLOW)
        if source_class == "viral":
            # ytref: soi thật ID + heatmap + cờ (vài giây/video, không cắt/tag gì)
            from autoedit.library.ingest import yt_chapter_gate
            infos, warns = youtube_infos_for(scenes)
            ch_ok, ch_warns = yt_chapter_gate(scenes, infos)  # MO_TA_TCF_FILE_NGUON §1
            for src, info in infos.items():
                gate = "" if not info.chapters else (
                    "" if src in ch_ok else " ⚠ TRƯỢT MỐC (sẽ bỏ → tcf file nguồn)")
                kenh = channel or info.channel
                typer.echo(f"  ▸ {Path(src).name}: ID {info.video_id} · "
                           f"\"{info.title}\" · kênh \"{kenh or '?'}\" · "
                           f"heatmap {'CÓ' if info.heatmap_available else 'không'} "
                           f"({len(info.peaks)} đỉnh) · {len(info.chapters)} chapters{gate}")
            warns.extend(ch_warns)
            scenes = apply_viral_rules(scenes, stats, infos, warns)
            typer.echo(f"  Viral c8+ytref: bỏ >{VIRAL_DROP_S:.0f}s {stats['too_long']} · "
                       f"bóp 6s {stats['squeezed_6s']} · cờ điểm nhô {stats['peak_scenes']} cảnh / "
                       f"{stats['peak_total']} đỉnh / {stats['peak_videos']} video · "
                       f"zoom {VIRAL_ZOOM:.0%} nướng chết")
            for w in warns:
                typer.secho(f"  ⚠ {w}", fg=typer.colors.YELLOW)
        return

    taggers = _vision_taggers(engine, model, angle=False)  # c7: camera_angle KHÔNG tag đại trà
    if (b := db.backup_cache_db()):  # G1: sổ có thể dùng chung trên ổ mạng
        typer.echo(f"  backup sổ trước mẻ: {b}")
    conn = db.connect()
    typer.echo(f"Nạp {draft.name} → {d / 'nap'} (vision {engine}, "
               f"{len(taggers)} key × {WORKERS_PER_KEY} luồng"
               + (", nhãn VIRAL c8" if source_class == "viral" else "") + ")... "
               "Ctrl+C ngắt an toàn, chạy lại tiếp tục chỗ cũ.")

    def show(i: int, total: int, path) -> None:
        typer.echo(f"  [{i}/{total}] {path.name}")

    result = ingest_draft(conn, niche, d, draft, taggers, on_progress=show,
                          limit=limit, stagger_s=2.0, source_class=source_class,
                          topic=topic, retag=retag, channel=channel)
    st = result.stats
    typer.secho(
        f"✓ {result.scenes} cảnh: cắt mới {result.cut_new}, clip có sẵn {result.cut_reused}, "
        f"tag mới {len(result.indexed)}, đã trong db {result.skipped_db}, "
        f"lỗi {len(result.failed)} — tổng niche trong db: {db.count_assets(conn, niche)}",
        fg=typer.colors.GREEN)
    typer.echo(f"  Bỏ khi đọc draft: thiếu file {st['missing_file']} · cache CapCut "
               f"{st['cache_material']} · quá ngắn {st['too_short']} · trùng {st['duplicate']}")
    if source_class == "viral":
        typer.echo(f"  Viral c8: bóp 6s {st.get('squeezed_6s', 0)} cảnh · "
                   f"bỏ >{VIRAL_DROP_S:.0f}s {st.get('too_long', 0)} · zoom {VIRAL_ZOOM:.0%}")
        typer.echo(f"  Điểm nhô (ytref §3h): {st.get('peak_scenes', 0)} cảnh gắn cờ / "
                   f"{st.get('peak_total', 0)} đỉnh / {st.get('peak_videos', 0)} video có heatmap")
    for w in st.get("warnings", []):  # spec TCF: own giờ cũng có warning (thiếu chủ đề)
        typer.secho(f"  ⚠ {w}", fg=typer.colors.YELLOW)
    for path, err in result.failed:
        typer.secho(f"  ⚠ {path}: {err}", fg=typer.colors.YELLOW)


@app.command(name="channel-audit")
def channel_audit_cmd(
    niche: Optional[str] = typer.Option(None, "--niche", help="Chỉ soát 1 niche."),
) -> None:
    """VD4 ghi công: liệt kê FOLDER nguồn (thư mục cha source_video) + số asset + kênh
    đã điền — nhìn là biết folder nào còn thiếu để `channel-set`."""
    from autoedit.library import db

    groups = db.source_video_folders(db.connect(), niche=niche)
    if not groups:
        typer.echo("Kho chưa có asset nào mang source_video (chỉ mẻ ống nạp mới có).")
        return
    missing = 0
    cur_niche = None
    for g in groups:
        if g["niche"] != cur_niche:
            cur_niche = g["niche"]
            typer.echo(f"═══ niche {cur_niche} ═══")
        chans = [c for c in g["channels"] if c]
        if not chans:
            missing += 1
            typer.secho(f"  ✗ {g['folder']}  ({g['assets']} asset) — CHƯA có kênh",
                        fg=typer.colors.YELLOW)
        else:
            mixed = " ⚠ lẫn asset chưa điền" if "" in g["channels"] else ""
            typer.echo(f"  ✓ {g['folder']}  ({g['assets']} asset) — {', '.join(chans)}{mixed}")
    typer.echo(f"Tổng: {len(groups)} folder nguồn, {missing} chưa có kênh. "
               "Điền: uv run autoedit channel-set \"<folder>\" \"<Tên Kênh>\"")


@app.command(name="channel-set")
def channel_set_cmd(
    prefix: str = typer.Argument(..., help="Prefix đường dẫn FILE/FOLDER nguồn "
                                           "(so đầu chuỗi source_video, không phân hoa-thường)."),
    channel: str = typer.Argument(..., help="Tên kênh nguồn (chuỗi rỗng '' = xóa kênh)."),
    niche: Optional[str] = typer.Option(None, "--niche", help="Chỉ áp trong 1 niche."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Chỉ đếm asset trúng, KHÔNG ghi."),
) -> None:
    """VD4 ghi công: backfill kênh nguồn cho asset ĐÃ NẠP theo prefix source_video —
    người khai, máy không suy (luật own-vs-viral). Chạy lại đè được (sửa kênh sai)."""
    from autoedit.library import db

    n = db.set_source_channel(db.connect(), prefix, channel, niche=niche, dry_run=dry_run)
    if n == 0:
        typer.secho(f"0 asset có source_video bắt đầu bằng '{prefix}'"
                    + (f" trong niche {niche}" if niche else "")
                    + " — soát lại bằng channel-audit.", fg=typer.colors.YELLOW)
        return
    if dry_run:
        typer.echo(f"[dry-run] {n} asset sẽ được gán kênh \"{channel}\".")
    else:
        typer.secho(f"✓ {n} asset đã gán kênh \"{channel}\".", fg=typer.colors.GREEN)


@app.command(name="library-dna")
def library_dna_cmd(
    niche: str = typer.Argument(..., help="Tên niche đã nạp."),
    draft: list[Path] = typer.Option(
        ..., "--draft", help="Folder draft CapCut nguồn ĐÃ NẠP (lặp lại được nhiều lần)."),
) -> None:
    """PB5: thống kê DNA đợt 1 (d1 pacing · d2 thở · c7 cỡ cảnh · c6 chữ ký) — 0 token,
    chạy lại được mỗi khi nạp thêm draft. Ghi kèm dna.json cho validator/NÃO đọc (§2a)."""
    from autoedit.library import db
    from autoedit.library.dna import compute_dna, save_dna
    from autoedit.library.profile import niche_dir, resolve_library_root

    for d in draft:
        if not (d / "draft_content.json").is_file():
            typer.secho(f"Lỗi: không thấy draft_content.json trong {d}",
                        fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
    dna = compute_dna(db.connect(), niche, list(draft))
    p, b, g, s = dna["pacing"], dna["breathing"], dna["shot_grammar"], dna["signature"]

    def line(txt: str = "") -> None:
        typer.echo(txt)

    def fstat(st: dict) -> str:
        return (f"n={st['n']}, trung bình {st['mean']}s, trung vị {st['median']}s, "
                f"lệch chuẩn {st['std']}, min {st['min']} / max {st['max']}")

    line(f"═══ DNA niche '{niche}' — {dna['drafts']} draft, timeline {dna['timeline_min']} phút ═══")
    line("\n— d1 PACING —")
    line(f"  Mật độ cắt: {p['cuts_per_min']} cut/phút ({p['shots']} shot)")
    mega = p["mega_segments"]
    if mega["n"]:
        line(f"  Mega-segment >30s: {mega['n']} khúc ({mega['total_s']:.0f}s) — "
             "BỎ khỏi thống kê pacing (luật user 2026-07-07)")
    line(f"  Độ dài shot: {fstat(p['shot_len'])}")
    line(f"  Hold (≥5s): {p['holds']['n']} shot = {p['holds']['share']:.0%}, trung vị {p['holds']['median_s']}s")
    for name, st in p["by_quarter"].items():
        line(f"  {name}: trung vị {st['median']}s ({st['n']} shot)")
    line(f"  45s đầu (hook): trung vị {p['hook45']['median']}s ({p['hook45']['n']} shot)")
    line("\n— d2 HÌNH THỞ —")
    line(f"  {b['windows']} ô thở / {b['voice_min']} phút thoại = {b['per_min_voice']} ô/phút")
    mega_b = b["mega_windows"]
    if mega_b["n"]:
        line(f"  Ô thở >60s: {mega_b['n']} khúc ({mega_b['total_s']:.0f}s) — "
             "BỎ khỏi thống kê d2 (luật user 2026-07-07)")
    line(f"  Độ dài ô thở: {fstat(b['len'])}")
    line(f"  Footage trong ô thở: {b['scene_types']} · cỡ cảnh {b['shot_sizes']}")
    spw = b["shots_per_window"]
    line(f"  Shot/ô thở: trung bình {spw['mean']}, trung vị {spw['median']:.0f}, "
         f"max {spw['max']:.0f} (chuỗi nhiều shot hiếm)" if spw["n"] else "  Shot/ô thở: —")
    line("\n— c7 CỠ CẢNH —")
    line(f"  Phân bố: {g['distribution']}")
    cad = g["cu_cadence"]
    line(f"  Nhịp đặc tả: {'1 close-up mỗi ' + str(cad) + ' shot' if cad else 'KHÔNG có close-up'}")
    line("  Chuỗi 3-shot hay gặp: " + "; ".join(f"{c} (×{n})" for c, n in g["top_chains"]))
    line("\n— c6 CHỮ KÝ (gợi ý signature/) —")
    line("  Loại cảnh: " + ", ".join(f"{t}×{n}" for t, n in s["top_scene_types"]))
    line("  Chủ thể lặp: " + ", ".join(f"{t}×{n}" for t, n in s["top_subjects"] if n > 1))
    line("  Hook mở bằng: " + ", ".join(f"{t}×{n}" for t, n in s["hook_opens_with"]))
    dna_path = save_dna(dna, niche_dir(niche, root=resolve_library_root(None)), list(draft))
    line(f"\n✓ dna.json: {dna_path} (pacing validator + NÃO direct đọc từ đây)")


@app.command(name="pause-dna")
def pause_dna_cmd(
    niche: str = typer.Argument(..., help="Tên niche (folder trong library) nhận DNA."),
    draft: list[Path] = typer.Option(
        ..., "--draft",
        help="Folder draft CapCut EDITOR DỰNG (lặp lại được). CẤM draft viral — "
             "nhịp tách cảnh ≠ nhịp dựng editor (luật c8)."),
    script: list[Path] = typer.Option(
        [], "--script",
        help="File script gốc .txt, ghép với --draft THEO THỨ TỰ. Thiếu -> phân loại "
             "điểm cắt theo whisper-only (kém chính xác — whisper hay mất dấu)."),
    language: str = typer.Option("en", "--language", help="Ngôn ngữ voice (faster-whisper)."),
    force: bool = typer.Option(
        False, "--force",
        help="Đè pause_dna.json đã có (tự backup trước). Mặc định KHÔNG đè bản đã "
             "duyệt — ghi pause_dna.new.json cạnh bên để so."),
) -> None:
    """C7: học DNA nhịp nghỉ + lớp hình thở từ draft editor -> pause_dna.json của niche
    (`load_pause_dna`/`load_breath_dna` của stage cut đọc). Transcript cache bền tại
    <library>/<niche>/pause_scan_cache/ — chạy lại không tốn transcribe."""
    import json

    from autoedit.library import pause_scan as ps
    from autoedit.library.profile import niche_dir, resolve_library_root

    for d in draft:
        if not (d / "draft_content.json").is_file():
            typer.secho(f"Lỗi: không thấy draft_content.json trong {d}",
                        fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
    niche_d = niche_dir(niche, root=resolve_library_root(None))
    cache_dir = niche_d / "pause_scan_cache"
    per_draft: dict[str, dict] = {}
    n_no_script = 0
    for i, d in enumerate(draft):
        label = ps.draft_label(d)
        typer.echo(f"=== {label} ===")
        script_text = ""
        if i < len(script):
            script_text = script[i].read_text(encoding="utf-8")
        else:
            n_no_script += 1
            typer.secho("  (không --script — phân loại whisper-only)", fg=typer.colors.YELLOW)
        r = ps.scan_draft(d, script_text, ps.make_whisper_words(d, cache_dir, language),
                          echo=typer.echo)
        per_draft[label] = r
        rows_path = cache_dir / f"rows_{label}.json"
        rows_path.write_text(json.dumps({k: r[k] for k in ("rows", "holes")},
                                        ensure_ascii=False, indent=1), encoding="utf-8")
    note = f"{n_no_script} draft whisper-only." if n_no_script else ""
    dna = ps.compute_pause_dna(per_draft, meta_note=note)

    p = dna["pooled"]
    typer.echo(f"\n═══ pause-DNA '{niche}' — {len(per_draft)} draft, "
               f"{p['tl_minutes']} phút, chèn +{p['insert_ratio_pct']}% ═══")
    for kind, k in p["kinds"].items():
        if k["nghe_ra"]:
            typer.echo(f"  {kind:12s} {k['per_min']:>5}/ph  nghe-ra p50={k['nghe_ra']['p50']} "
                       f"(p25={k['nghe_ra']['p25']} p75={k['nghe_ra']['p75']})")
    m = p["breath_measured"]
    typer.echo(f"  Lớp Ô ({p['holes']['n']} ô ≥1,5s): hình thở {m['n_breath']} · "
               f"passive {m['n_passive']} · montage {m['n_montage']} · khác {m['n_other']}")
    if m["footage"]:
        typer.echo(f"  Hình thở: footage p50={m['footage']['p50']}s "
                   f"(p10={m['footage']['p10']} p90={m['footage']['p90']} "
                   f"max={m['footage']['max']}) · hold p50={m['hold']['p50']}s")
    typer.echo(f"  Phân bố k (số miếng/ô — backlog §6.5): {m['k_dist'] or '—'}")
    if "footage_anchors" not in p["breath"]:
        typer.secho(f"  ⚠ <{ps.MIN_ANCHOR_N} ô thở đo được — không xuất anchors, "
                    "cut sẽ fallback hằng space", fg=typer.colors.YELLOW)

    out, status = ps.save_pause_dna(dna, niche_d, force=force)
    if status == "new":
        typer.secho(f"\n⚠ pause_dna.json đã có (bản duyệt) — KHÔNG đè. Bản mới: {out}"
                    f"\n  So xong muốn thay: chạy lại với --force (tự backup).",
                    fg=typer.colors.YELLOW)
    elif status == "forced":
        typer.echo(f"\n✓ Đã đè {out} (backup pause_dna.backup-*.json cạnh bên)")
    else:
        typer.echo(f"\n✓ {out} (stage cut load_pause_dna/load_breath_dna đọc từ đây)")


@app.command(name="tcf-gen")
def tcf_gen_cmd(
    niche: str = typer.Argument(..., help="Niche (cache transcribe dùng chung pause-dna)."),
    draft: list[Path] = typer.Option(
        ..., "--draft",
        help="Folder draft CapCut editor own (lặp lại được). Máy sinh file "
             "'topic + chapter video.txt' TRONG folder draft từ voice."),
    language: str = typer.Option("en", "--language", help="Ngôn ngữ voice (faster-whisper)."),
    model: str = typer.Option("sonnet", "--model", help="Model claude -p đặt title/chapter."),
    force: bool = typer.Option(False, "--force", help="Đè file TCF đã có."),
) -> None:
    """Sinh 'topic + chapter video.txt' cho draft editor own bằng phân tích voice
    (transcribe → NÃO đặt title + chia chapter theo TIMELINE). Cache transcribe bền tại
    <library>/<niche>/pause_scan_cache/ — pause-dna dùng lại, không tốn 2 lần."""
    import re

    from autoedit.director.cc_client import ClaudeCodeDirectorClient
    from autoedit.library import pause_scan as ps
    from autoedit.library import tcf_gen as tg
    from autoedit.library.profile import niche_dir, resolve_library_root

    for d in draft:
        if not (d / "draft_content.json").is_file():
            typer.secho(f"Lỗi: không thấy draft_content.json trong {d}",
                        fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
    cache_dir = niche_dir(niche, root=resolve_library_root(None)) / "pause_scan_cache"
    client = ClaudeCodeDirectorClient(model=model, thinking=False)
    n_err = 0
    for d in draft:
        typer.echo(f"=== {ps.draft_label(d)} ===")
        try:
            out, status = tg.generate_tcf(
                d, client, ps.make_whisper_words(d, cache_dir, language),
                force=force, echo=typer.echo)
        except Exception as exc:  # 1 draft hỏng không chặn cả mẻ — báo đỏ, chạy tiếp
            n_err += 1
            typer.secho(f"  ✗ {exc}", fg=typer.colors.RED)
            continue
        if status == "skip":
            typer.echo(f"  → đã có TCF, skip (--force để đè)")
        else:
            head = out.read_text(encoding="utf-8").splitlines()
            n_ch = sum(1 for x in head if re.match(r"^\d+:\d{2} ", x))
            typer.secho(f"  ✓ {head[0]}  ({n_ch} chapter) → {out.name}",
                        fg=typer.colors.GREEN)
    if n_err:
        typer.secho(f"\n⚠ {n_err}/{len(draft)} draft lỗi — xem log đỏ ở trên",
                    fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)


@app.command(name="library-search")
def library_search_cmd(
    niche: str = typer.Argument(..., help="Tên niche."),
    query: str = typer.Argument(..., help="Từ khóa, vd 'beach aerial'."),
) -> None:
    """Tìm asset đã index trong cache.db (bài kiểm tra M3.5)."""
    from autoedit.library import db

    conn = db.connect()
    rows = db.search_assets(conn, niche, query)
    if not rows:
        typer.secho(f"Không có kết quả cho '{query}' trong niche '{niche}'.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    for r in rows:
        folder = r.get("folder_path") or r["category"]
        dur = f", {r['duration']:.1f}s" if r.get("duration") else ""
        voice = {1: ", voice", 0: ", thở"}.get(r.get("has_voice"), "")
        typer.echo(f"[{folder}/{r['media_type']}] {r['path']}")
        typer.echo(f"   {r['subject']} — {r['description'][:80]} "
                   f"({r['shot_size']}, {r['scene_type']}, {r['mood']}{dur}{voice}, "
                   f"tags: {', '.join(r['tags'][:6])})")


@app.command(name="sfx-init")
def sfx_init_cmd() -> None:
    """P1.4: tạo ~/AutoEdit/sfx/ + ghi brief để dán vào Cowork (tải Artlist)."""
    from autoedit.sfx.brief import write_brief
    from autoedit.sfx.library import SFX_ROOT

    SFX_ROOT.mkdir(parents=True, exist_ok=True)
    brief = SFX_ROOT / "COWORK_BRIEF.md"
    write_brief(brief)
    typer.secho(f"✓ Thư viện SFX: {SFX_ROOT}", fg=typer.colors.GREEN)
    typer.echo(f"  Brief cho Cowork: {brief}")
    typer.echo("  1. Mở file brief, dán nội dung vào Cowork (đã login Artlist trong Chrome)")
    typer.echo("  2. Cowork tải SFX + ghi ~/Downloads/sfx_manifest.yaml")
    typer.echo("  3. Chạy: autoedit sfx-import --manifest ~/Downloads/sfx_manifest.yaml")


@app.command(name="sfx-import")
def sfx_import_cmd(
    manifest: Path = typer.Option(..., "--manifest", help="File sfx_manifest.yaml Cowork tạo."),
    from_dir: Path = typer.Option(
        Path("~/Downloads").expanduser(), "--from", help="Thư mục chứa file đã tải."
    ),
) -> None:
    """P1.4: nhập SFX từ manifest Cowork vào thư viện (chuẩn hóa WAV)."""
    from autoedit.sfx.library import import_from_manifest, library_status

    if not manifest.is_file():
        typer.secho(f"Lỗi: không thấy manifest {manifest}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    result = import_from_manifest(manifest, from_dir)
    typer.secho(f"✓ Nhập {len(result.imported)} SFX, lỗi {len(result.failed)}", fg=typer.colors.GREEN)
    for line in result.imported:
        typer.echo(f"  + {line}")
    for f, err in result.failed:
        typer.secho(f"  ⚠ {f}: {err}", fg=typer.colors.YELLOW)
    typer.echo(f"  thư viện: {library_status()}")


@app.command(name="sfx-list")
def sfx_list_cmd() -> None:
    """Hiện thư viện SFX: mỗi loại mấy biến thể."""
    from autoedit.sfx.library import SFX_ROOT, library_status

    if not SFX_ROOT.is_dir():
        typer.secho("Chưa có thư viện SFX — chạy `autoedit sfx-init`.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    for kind, n in library_status().items():
        typer.echo(f"  {kind:8s}: {n} biến thể")


@app.command(name="ambient-import")
def ambient_import_cmd(
    niche: str = typer.Option(..., "--niche", help="Niche (folder trong ambient root, vd space)."),
    manifest: Optional[Path] = typer.Option(
        None, "--manifest", help="Mặc định <ambient_root>/<niche>/ambient_manifest.yaml."),
    from_dir: Optional[Path] = typer.Option(
        None, "--from", help="Thư mục chứa file thô (mặc định = chính folder niche)."),
) -> None:
    """C1: nhập ambient từ manifest vào <ambient_root>/<niche>/ (chuẩn hóa WAV PCM 48k)."""
    from autoedit.ambient.library import import_from_manifest, library_status, niche_dir

    npath = niche_dir(niche)
    manifest = manifest or (npath / "ambient_manifest.yaml")
    if not manifest.is_file():
        typer.secho(f"Lỗi: không thấy manifest {manifest}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    result = import_from_manifest(manifest, from_dir or npath, npath)
    typer.secho(f"✓ Nhập {len(result.imported)} ambient, lỗi {len(result.failed)}",
                fg=typer.colors.GREEN)
    for line in result.imported:
        typer.echo(f"  + {line}")
    for f, err in result.failed:
        typer.secho(f"  ⚠ {f}: {err}", fg=typer.colors.YELLOW)
    typer.echo(f"  thư viện {npath}: {library_status(npath)}")


@app.command(name="ambient-list")
def ambient_list_cmd(
    niche: str = typer.Option(..., "--niche", help="Niche cần xem."),
) -> None:
    """Hiện thư viện ambient của 1 niche: mỗi loại cảnh mấy biến thể."""
    from autoedit.ambient.library import library_status, niche_dir

    npath = niche_dir(niche)
    status = library_status(npath)
    if not status:
        typer.secho(f"Chưa có ambient cho niche '{niche}' ({npath}) — tầng ambient sẽ tắt.",
                    fg=typer.colors.YELLOW)
        raise typer.Exit(code=0)
    for kind, n in status.items():
        typer.echo(f"  {kind:20s}: {n} biến thể")


@app.command(name="epidemic-sfx")
def epidemic_sfx_cmd(
    niche: str = typer.Option(..., "--niche", help="Niche đích (folder trong ambient root)."),
    want: list[str] = typer.Option(
        ..., "--want", help="Kind cần lấy: 'camel' | 'camel=camel grunt' | 'camel=camel:5' "
                            "(kind=term:số_file). Lặp cờ nhiều lần."),
    filetype: str = typer.Option("MP3", "--filetype", help="MP3 (nhẹ, mặc định) hoặc WAV (gốc 24bit)."),
    min_s: float = typer.Option(1.0, "--min-s", help="Bỏ SFX ngắn hơn (giây)."),
    max_s: float = typer.Option(30.0, "--max-s", help="Bỏ SFX dài hơn (giây)."),
    target: Optional[int] = typer.Option(
        None, "--target", help="Kind đã có ≥ ngần này biến thể thì bỏ qua (chạy lại không tải trùng)."),
    loose: bool = typer.Option(
        False, "--loose", help="TẮT lưới loài (mặc định loại kết quả lệch loài — "
                               "tìm penguin ra tiếng vịt). Bật khi cố ý gom rộng."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Chỉ xem sẽ lấy gì, KHÔNG tải."),
) -> None:
    """Nạp SFX trả phí từ Epidemic Sound vào kho ambient của niche (chuẩn hóa WAV PCM 48k).

    Cần EPIDEMIC_API_KEY trong .env, tạo từ tài khoản TRẢ PHÍ (key free search được
    nhưng không tải được). Key hết hạn 30 ngày.
    """
    from autoedit.ambient.epidemic import EpidemicError
    from autoedit.ambient.epidemic_fetch import fetch_to_niche, parse_plan
    from autoedit.ambient.library import library_status, niche_dir

    if filetype.upper() not in ("MP3", "WAV"):
        typer.secho("Lỗi: --filetype chỉ nhận MP3 hoặc WAV", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    npath = niche_dir(niche)
    plans = parse_plan(list(want))
    typer.secho(f"=== Epidemic SFX -> {npath} ({len(plans)} kind, {filetype}) ===",
                fg=typer.colors.CYAN)
    try:
        res = fetch_to_niche(plans, npath, filetype=filetype.upper(), min_s=min_s,
                             max_s=max_s, target_per_kind=target, dry_run=dry_run,
                             strict=not loose)
    except EpidemicError as exc:
        typer.secho(f"Lỗi Epidemic: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    for line in res.downloaded:
        typer.echo(f"  {'~' if dry_run else '↓'} {line}")
    for line in res.rejected:
        typer.secho(f"  ✗ lệch loài: {line}", fg=typer.colors.MAGENTA)
    for line in res.skipped:
        typer.secho(f"  = bỏ qua {line}", fg=typer.colors.BLUE)
    for kind, err in res.failed:
        typer.secho(f"  ⚠ {kind}: {err}", fg=typer.colors.YELLOW)
    if dry_run:
        typer.secho(f"(dry-run: {len(res.downloaded)} file sẽ tải, chưa đụng kho)",
                    fg=typer.colors.CYAN)
        raise typer.Exit(code=0)
    for line in res.imported:
        typer.echo(f"  + {line}")
    for f, err in res.import_failed:
        typer.secho(f"  ⚠ nạp {f}: {err}", fg=typer.colors.YELLOW)
    typer.secho(f"✓ Tải {len(res.downloaded)}, nạp kho {len(res.imported)}, "
                f"lỗi {len(res.failed) + len(res.import_failed)}", fg=typer.colors.GREEN)
    typer.echo(f"  thư viện {npath}: {library_status(npath)}")


@app.command(name="tag-stock")
def tag_stock_cmd(
    project_dir: Path = typer.Argument(..., help="Folder project (chứa project.json)."),
) -> None:
    """M3b: vision-tag các pick STOCK/ENTITY của project (chạy tay cho project cũ/retag).

    Tag lưu vĩnh viễn cache.db::stock_tags theo asset_key — video sau tái dùng miễn phí.
    """
    from autoedit.library.db import connect
    from autoedit.library.stock_tags import tag_project_stock
    from autoedit.project import Project

    project = Project.load(project_dir)
    conn = connect()
    try:
        st = tag_project_stock(project, Path(project.project_dir), conn)
    finally:
        conn.close()
    typer.secho(f"✓ Tag stock: {st['tagged']} mới, {st['cached']} đã có (cache)",
                fg=typer.colors.GREEN)
    for key, reason in st["failed"]:
        typer.secho(f"  ✗ {key}: {reason}", fg=typer.colors.YELLOW)


@app.command(name="editor-learn")
def editor_learn_cmd(
    draft_dir: Path = typer.Argument(..., help="Folder draft CapCut editor (chứa draft_content.json)."),
    niche: str = typer.Option(..., "--niche", help="Niche kho ambient nhận file (vd space)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Chỉ báo cáo, không copy/ghi gì."),
) -> None:
    """S4/M5: học SFX + nhạc từ draft editor thật (COPY-only — luật đứng 2026-07-10).

    Quét DNA âm thanh (PB10/PB11/PB13) cộng dồn editor_dna.json + mót file audio mới
    thành manifest chờ ambient-import/sfx-import; nhạc vào staging music_editor/<draft>/
    (KHÔNG vào pool chọn nhạc). Không ghi gì vào folder draft.
    """
    from autoedit.ambient import schedule as amb
    from autoedit.ambient.library import niche_dir
    from autoedit.editor_learn import dna as dnamod
    from autoedit.editor_learn.mine import (
        HOLD_DIR,
        SFX_STAGING,
        SFX_STAGING_MANIFEST,
        mine_draft,
    )
    from autoedit.library.profile import resolve_library_root
    from autoedit.sfx.library import SFX_ROOT

    if not (draft_dir / "draft_content.json").is_file():
        typer.secho(f"Lỗi: không thấy draft_content.json trong {draft_dir}",
                    fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    d = dnamod.scan_draft(draft_dir)
    typer.secho(f"=== DNA âm thanh: {d.draft} ({d.duration_s/60:.1f}' · "
                f"voice {d.voice_span[0]:.0f}–{d.voice_span[1]:.0f}s) ===",
                fg=typer.colors.CYAN)

    import statistics

    def _stats(vols: list[float]) -> str:
        if not vols:
            return "—"
        m = statistics.median(vols)
        return f"n={len(vols)} median {m:.2f} ({dnamod.db(m):+.1f}dB)"

    typer.echo(f"  nhạc/drone (đoạn >{dnamod.SFX_SEG_MAX:.0f}s): {_stats(d.music_vols)}")
    typer.echo(f"  SFX đè voice (bỏ whoosh):     {_stats(d.sfx_vols['voiced'])}")
    typer.echo(f"  SFX không voice (bỏ whoosh):  {_stats(d.sfx_vols['novoice'])}")
    typer.echo(f"  SFX lai 15–60% (bỏ whoosh):   {_stats(d.sfx_vols['mixed'])}")
    if d.whoosh_n:
        typer.echo(f"  whoosh: {d.whoosh_n} (~{d.whoosh_per_min():.1f}/phút) · "
                   f"dur med {statistics.median(d.whoosh_durs):.2f}s · "
                   f"vol med {statistics.median(d.whoosh_vols):.2f} · "
                   f"sát cut ≤{dnamod.NEAR_CUT_S}s: {d.whoosh_near_cut}/{d.whoosh_n} · "
                   f"cut trong whoosh: {d.cuts_inside_whoosh}/{d.whoosh_n} "
                   f"({d.cuts_n} cut)")

    profile_path = dnamod.default_profile_path()
    if dry_run:
        profile = dnamod.load_profile(profile_path)
        profile["drafts"][d.draft] = {"sfx_vols": d.sfx_vols, "music_vols": d.music_vols}
    else:
        profile = dnamod.update_profile(profile_path, d)
    pooled = dnamod.pooled_stats(profile)
    typer.echo(f"  Hồ sơ cộng dồn ({pooled['n_drafts']} draft — {profile_path}):")
    for key, const, label in (("voiced", amb.SUBJECT_VOL, "SUBJECT_VOL"),
                              ("novoice", amb.SUBJECT_BREATH_VOL, "SUBJECT_BREATH_VOL")):
        g = pooled[key]
        if g["median"] is not None:
            typer.echo(f"    SFX {key:7s}: median {g['median']:.2f} "
                       f"({dnamod.db(g['median']):+.1f}dB, n={g['n']}) — máy {label}="
                       f"{const} ({dnamod.db(const):+.1f}dB)")
    typer.echo("    (số máy CHỈ đổi khi user yêu cầu — V10 đã chốt bằng tai)")

    npath = niche_dir(niche)
    music_root = resolve_library_root().parent / "music_editor"
    res = mine_draft(draft_dir, npath, SFX_ROOT, music_root, dry_run=dry_run)
    tag = " (dry-run — chưa copy gì)" if dry_run else ""
    typer.secho(f"=== Mót file{tag}: ambient {len(res.ambient)} · sfx {len(res.sfx)} · "
                f"nhạc {len(res.music)} · hold {len(res.hold)} · đã biết {len(res.known)} · "
                f"voice {len(res.voice)} ===", fg=typer.colors.CYAN)
    for kind, f in res.ambient:
        typer.echo(f"  ambient {kind:16s} <- {f}")
    for kind, f in res.sfx:
        typer.echo(f"  sfx     {kind:16s} <- {f}")
    for f in res.music:
        typer.echo(f"  nhạc -> {music_root / d.draft}: {f}")
    for f in res.hold:
        typer.echo(f"  hold -> raw/{HOLD_DIR}: {f}")
    for f in res.missing:
        typer.secho(f"  ⚠ không thấy file media: {f}", fg=typer.colors.YELLOW)
    if res.ambient and not dry_run:
        typer.echo(f"  Nạp ambient: autoedit ambient-import --niche {niche}")
    if res.sfx and not dry_run:
        typer.echo(f"  Nạp sfx: autoedit sfx-import --manifest "
                   f"\"{SFX_ROOT / SFX_STAGING / SFX_STAGING_MANIFEST}\" "
                   f"--from \"{SFX_ROOT / SFX_STAGING}\"")
    if res.music and not dry_run:
        typer.echo("  Nhạc nằm STAGING chờ user gọi — KHÔNG tự vào pool chọn nhạc.")


@app.command(name="music-init")
def music_init_cmd(
    lib: Optional[Path] = typer.Option(None, "--lib", help="Thư mục thư viện nhạc (mặc định <data_root>/music)."),
) -> None:
    """Tạo thư viện nhạc. Editor gắn mood ngay trong TÊN FILE: `Artist - Title __mood.mp3`."""
    from autoedit.music.library import MUSIC_ROOT, TRACKS_DIR

    lib = lib or MUSIC_ROOT

    (lib / TRACKS_DIR).mkdir(parents=True, exist_ok=True)
    typer.secho(f"✓ Thư viện nhạc: {lib}", fg=typer.colors.GREEN)
    typer.echo(f"  1. Tải nhạc KHÔNG LỜI (Artlist) vào {lib}/{TRACKS_DIR}/")
    typer.echo("  2. ĐỔI TÊN file gắn mood: 'Artist - Title __mood.mp3' (nhiều mood: '__a __b')")
    typer.echo(f"  3. Chạy: autoedit music-import --lib {lib}  (tool đọc mood từ tên + đo nhịp)")


@app.command(name="music-import")
def music_import_cmd(
    lib: Optional[Path] = typer.Option(None, "--lib", help="Thư mục thư viện nhạc (mặc định <data_root>/music)."),
    manifest: Optional[Path] = typer.Option(None, "--manifest", help="Dùng manifest YAML có sẵn thay vì đọc tên file."),
    reanalyze: bool = typer.Option(False, "--reanalyze", help="Phân tích librosa lại cho mọi bài (bỏ cache index)."),
) -> None:
    """Nạp nhạc: gắn mood TỪ TÊN FILE (`Artist - Title __mood`) + librosa (energy/sections) → music_index.json.
    Mặc định đọc tên file; --manifest để dùng file YAML viết tay."""
    from autoedit.music.library import MUSIC_ROOT, import_from_filenames, import_manifest, library_status

    lib = lib or MUSIC_ROOT

    if manifest is not None:
        if not manifest.is_file():
            typer.secho(f"Lỗi: không thấy {manifest}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        typer.echo(f"Nạp nhạc từ manifest {manifest} (librosa — hơi lâu)...")
        res = import_manifest(manifest, lib, reanalyze=reanalyze)
    else:
        typer.echo(f"Nạp nhạc từ TÊN FILE trong {lib}/tracks (librosa — hơi lâu)...")
        res = import_from_filenames(lib, reanalyze=reanalyze)
    typer.secho(f"✓ Nạp {len(res.imported)} bài, lỗi {len(res.failed)}", fg=typer.colors.GREEN)
    for f, err in res.failed:
        typer.secho(f"  ⚠ {f}: {err}", fg=typer.colors.YELLOW)
    if res.unknown_tags:
        typer.secho(f"  ⚠ tag lạ (bỏ qua, bổ sung map nếu cần): {sorted(res.unknown_tags)}",
                    fg=typer.colors.YELLOW)
    typer.echo(f"  thư viện: {library_status(lib)}")


@app.command(name="music-analyze")
def music_analyze_cmd(
    lib: Optional[Path] = typer.Option(None, "--lib", help="Thư mục thư viện nhạc (mặc định <data_root>/music)."),
    regrid: bool = typer.Option(False, "--regrid", help="Đo lại nhịp/accent cho MỌI bài (backfill MUSIC SYNC M0)."),
) -> None:
    """MUSIC SYNC M0: in phân bố tier nhịp A/B/C của pool (để chốt ngưỡng 🔸).
    --regrid = chạy librosa lại toàn bộ (backfill 1 lần cho record cũ thiếu grid)."""
    from autoedit.music.analyze import TIER_A_QUALITY, TIER_B_QUALITY
    from autoedit.music.library import MUSIC_ROOT, _load_index, regrid_index

    lib = lib or MUSIC_ROOT

    if regrid:
        typer.echo(f"Đo nhịp/accent lại toàn bộ {lib} (librosa — hơi lâu)...")
        rows, failed = regrid_index(lib)
        for f, err in failed:
            typer.secho(f"  ⚠ {f}: {err}", fg=typer.colors.YELLOW)
    else:
        rows = _load_index(lib)
    if not rows:
        typer.secho("Index rỗng — chạy music-import trước.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    graded = [r for r in rows if r.get("beat_tier")]
    for r in sorted(graded, key=lambda r: -r.get("beat_quality", 0)):
        typer.echo(f"  {r.get('beat_tier')} q={r.get('beat_quality', 0):5.2f} "
                   f"beat={len(r.get('beat_times') or []):4d} acc={len(r.get('accents') or []):3d}"
                   f"  {r['file']}")
    tiers = {t: sum(1 for r in graded if r.get("beat_tier") == t) for t in "ABC"}
    missing = len(rows) - len(graded)
    typer.secho(f"✓ {len(rows)} bài | tier A={tiers['A']} B={tiers['B']} C={tiers['C']}"
                + (f" | CHƯA có grid={missing} (chạy --regrid)" if missing else ""),
                fg=typer.colors.GREEN)
    qs = sorted(r.get("beat_quality", 0) for r in graded)
    if qs:
        import statistics
        typer.echo(f"  quality: min={qs[0]:.2f} | p25={qs[len(qs)//4]:.2f} | "
                   f"median={statistics.median(qs):.2f} | p75={qs[3*len(qs)//4]:.2f} | max={qs[-1]:.2f}"
                   f"  (ngưỡng hiện tại 🔸: B≥{TIER_B_QUALITY}, A≥{TIER_A_QUALITY})")


@app.command(name="music-list")
def music_list_cmd(
    lib: Optional[Path] = typer.Option(None, "--lib", help="Thư mục thư viện nhạc (mặc định <data_root>/music)."),
    mood: str = typer.Option("", "--mood", help="Lọc theo mood."),
    energy: str = typer.Option("", "--energy", help="Lọc theo energy: low/medium/high."),
) -> None:
    """Liệt kê nhạc trong thư viện (lọc theo mood/energy)."""
    from autoedit.music.library import MUSIC_ROOT, list_tracks

    lib = lib or MUSIC_ROOT

    rows = list_tracks(lib, mood=mood, energy=energy)
    if not rows:
        typer.secho("Không có bài khớp.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    for r in rows:
        typer.echo(f"  {r['file']}")
        typer.echo(f"     mood={r.get('mood')} | {r.get('tempo_class')} {r.get('bpm')}bpm "
                   f"| energy={r.get('energy')} | {r.get('duration_sec')}s | vocals={r.get('vocals')}")


@app.command(name="demo-overlay")
def demo_overlay_cmd(
    name: str = typer.Option("PADOMA_OVERLAY_DEMO", "--name", help="Tên draft (ASCII)."),
    assets: Optional[Path] = typer.Option(
        None, "--assets", help="Folder asset mẫu (mặc định capcut_test/assets)."
    ),
    overwrite: bool = typer.Option(False, "--overwrite", help="Đè draft trùng tên."),
) -> None:
    """P1.1 derisk: sinh draft có text overlay keyframe + SFX — mở CapCut xác nhận."""
    from autoedit.overlay.demo import build_overlay_demo_content
    from autoedit.packager.machine import MachineProfile
    from autoedit.packager.packager import PackageError, package_draft

    if assets is None:
        assets = Path(__file__).resolve().parents[2] / "capcut_test" / "assets"
    try:
        profile = MachineProfile.load()
        content = build_overlay_demo_content(assets)
        draft_dir = package_draft(content, name, profile, overwrite=overwrite)
    except (FileNotFoundError, PackageError) as exc:
        typer.secho(f"Lỗi: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.secho(f"✓ Đã sinh draft overlay: {draft_dir}", fg=typer.colors.GREEN)
    typer.echo("  Mở CapCut → giây 1.5 chữ '$2' phải POP lên (phình rồi về) + nghe SFX,")
    typer.echo("  KHÔNG bắt relink, không lỗi format. Đây là gate P1.1.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
