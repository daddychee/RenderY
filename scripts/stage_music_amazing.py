# -*- coding: utf-8 -*-
"""Nhạc staging đợt 2 (AMAZING + REAL77a, 2026-07-16) → pool <data_root>/music/tracks.
Mẫu y đợt 1 (stage_music_life_in.py): mood TỪ TÊN, COPY-only, 3 nhóm IMPORT/SKIP/HOLD.
Khác đợt 1: DST đọc từ resolver MUSIC_ROOT (sau G1 data_root = F:\\AutoEdit)."""
import shutil
from pathlib import Path

from autoedit.music.library import MUSIC_ROOT

SRC = Path(r"F:\AutoEdit\music_editor")
DST = MUSIC_ROOT / "tracks"

NEW_DIRS = {"AM32", "AMZ 35", "AMZ 38", "AMZ 40", "AMZ 42", "AMZ33",
            "Bài AM19", "Bài AMZ20", "Bài AMZ31", "Bài AMZ45", "Bài AMZ999"}

# filename staging -> "Artist - Title __mood.ext" (mood theo nghĩa title, vocab pool)
IMPORT = {
 "1-Kyle Preston - Illustris Simulation.mp3": "Kyle Preston - Illustris Simulation __mysterious.mp3",
 "1-Kyle Preston - Lightless Voids.mp3": "Kyle Preston - Lightless Voids __dark.mp3",
 "1-Ofrin - Winner - Instrumental version.mp3": "Ofrin - Winner - Instrumental version __determined.mp3",
 "1-Orkestra Severni - Sirba a la Oscar Freylach.mp3": "Orkestra Severni - Sirba a la Oscar Freylach __playful.mp3",
 "1-Ziv Moran - Santa Lucia.mp3": "Ziv Moran - Santa Lucia __nostalgic.mp3",
 "10-Amos Ever Hadani - Miguel - Instrumental version.mp3": "Amos Ever Hadani - Miguel - Instrumental version __romantic.mp3",
 "10-BalloonPlanet - Choosing You - Instrumental version.mp3": "BalloonPlanet - Choosing You - Instrumental version __romantic.mp3",
 "10-DaniHaDani - Don’t Look Back.mp3": "DaniHaDani - Don't Look Back __determined.mp3",
 "10-Team Callahan - Full Circle - Instrumental version.mp3": "Team Callahan - Full Circle - Instrumental version __hopeful.mp3",
 "11-Kyle J Hartman - Celestial - No Backing Vocals.mp3": "Kyle J Hartman - Celestial - No Backing Vocals __dreamy.mp3",
 "11-Laurel Violet - There.mp3": "Laurel Violet - There __dreamy.mp3",
 "11-Semo - Insomniacs Dream.mp3": "Semo - Insomniacs Dream __dreamy.mp3",
 "11-Ziv Moran - Long Strokes.mp3": "Ziv Moran - Long Strokes __peaceful.mp3",
 "12-ANBR - Red Dress.mp3": "ANBR - Red Dress __romantic.mp3",
 "12-Ikoliks - Cool My Night.mp3": "Ikoliks - Cool My Night __playful.mp3",
 "12-Milli2nd - VITAMIN C - Instrumental version.mp3": "Milli2nd - VITAMIN C - Instrumental version __happy.mp3",
 "12-Muted - Spongy Hammer.mp3": "Muted - Spongy Hammer __playful.mp3",
 "12-Veaceslav Draganov - Passion.mp3": "Veaceslav Draganov - Passion __romantic.mp3",
 "13-Avni Vibes - Summer Groove.mp3": "Avni Vibes - Summer Groove __happy.mp3",
 "13-Ben Fox - Think About Lights - Instrumental version.mp3": "Ben Fox - Think About Lights - Instrumental version __hopeful.mp3",
 "13-Francesco DAndrea - Rise Again.mp3": "Francesco DAndrea - Rise Again __inspiring.mp3",
 "13-Oliver Michael - The End.mp3": "Oliver Michael - The End __sad.mp3",
 "13-Tristan Barton - Run - Instrumental version.mp3": "Tristan Barton - Run - Instrumental version __tense.mp3",
 "14-Captain Joz - Starlight Dreams.mp3": "Captain Joz - Starlight Dreams __dreamy.mp3",
 "14-Jean-Miles Carter - Gladys Aylward.mp3": "Jean-Miles Carter - Gladys Aylward __nostalgic.mp3",
 "14-Muted - Zoom Out.mp3": "Muted - Zoom Out __dreamy.mp3",
 "14-Ziv Moran - Timberline.mp3": "Ziv Moran - Timberline __peaceful.mp3",
 "15-Glories - Of Good Fortunes.mp3": "Glories - Of Good Fortunes __hopeful.mp3",
 "15-Semo - Chemtrails.mp3": "Semo - Chemtrails __mysterious.mp3",
 "2-IamDayLight - Seine River.mp3": "IamDayLight - Seine River __romantic.mp3",
 "2-SPEARFISHER - Chicken Coop.mp3": "SPEARFISHER - Chicken Coop __playful.mp3",
 "2-The Days - The After Glow - Instrumental version.mp3": "The Days - The After Glow - Instrumental version __dreamy.mp3",
 "2-Zac Nelson - Lucky Day - Instrumental version.mp3": "Zac Nelson - Lucky Day - Instrumental version __happy.mp3",
 "3-Ace - Do You Wanna Know.mp3": "Ace - Do You Wanna Know __playful.mp3",
 "3-Anthony Lazaro - Cold - Instrumental version.mp3": "Anthony Lazaro - Cold - Instrumental version __sad.mp3",
 "3-DaniHaDani - Lev 1.mp3": "DaniHaDani - Lev 1 __dreamy.mp3",
 "3-Low Light - Always - Instrumental version.mp3": "Low Light - Always - Instrumental version __romantic.mp3",
 "3-Moody Bear - Cloud Line - Instrumental version.mp3": "Moody Bear - Cloud Line - Instrumental version __dreamy.mp3",
 "4-BoDleasons - Next Level Vision.mp3": "BoDleasons - Next Level Vision __determined.mp3",
 "4-Daniel Pratt - Willow Tree - Instrumental version.mp3": "Daniel Pratt - Willow Tree - Instrumental version __peaceful.mp3",
 "4-Yarin Primak - Shtetl House - No Backing Vocals.mp3": "Yarin Primak - Shtetl House - No Backing Vocals __nostalgic.mp3",
 "4-Yehezkel Raz - A Journeys Epilogue - Instrumental version.mp3": "Yehezkel Raz - A Journeys Epilogue - Instrumental version __nostalgic.mp3",
 "5-Adrián Berenguer - Potencial.mp3": "Adrián Berenguer - Potencial __inspiring.mp3",
 "5-Ian Post - Prelude in C Major Bach.mp3": "Ian Post - Prelude in C Major Bach __peaceful.mp3",
 "5-Louis Adrien - March to Victory.mp3": "Louis Adrien - March to Victory __epic.mp3",
 "5-Muted - Singular Unusual.mp3": "Muted - Singular Unusual __mysterious.mp3",
 "5-Raz  Afla - Time - Instrumental version.mp3": "Raz Afla - Time - Instrumental version __dreamy.mp3",
 "6-Eldar Kedem - Rise  Fall - Instrumental version.mp3": "Eldar Kedem - Rise Fall - Instrumental version __serious.mp3",
 "6-Elifas Sonaru - Date Night on a Ferris Wheel.mp3": "Elifas Sonaru - Date Night on a Ferris Wheel __romantic.mp3",
 "6-Novembers - Night Flight.mp3": "Novembers - Night Flight __dreamy.mp3",
 "6-Oren Tsor - Valley Shine.mp3": "Oren Tsor - Valley Shine __uplifting.mp3",
 "7-Just for Kicks - Crème Brûlée.mp3": "Just for Kicks - Crème Brûlée __playful.mp3",
 "7-Le Marigold - Serenity.mp3": "Le Marigold - Serenity __peaceful.mp3",
 "7-Tony Petersen - Gas Can Rag.mp3": "Tony Petersen - Gas Can Rag __playful.mp3",
 "7-Vens Adams - Smiling with the Sun - Stripped Version.mp3": "Vens Adams - Smiling with the Sun - Stripped Version __happy.mp3",
 "8-Blackbard - Eldensvampbildning - Stripped Version.mp3": "Blackbard - Eldensvampbildning - Stripped Version __mysterious.mp3",
 "8-Itai Argaman - Heavens.mp3": "Itai Argaman - Heavens __dreamy.mp3",
 "8-Mansij - Lonely Mind.mp3": "Mansij - Lonely Mind __sad.mp3",
 "8-Michael Shynes - Born Again - Instrumental version.mp3": "Michael Shynes - Born Again - Instrumental version __hopeful.mp3",
 "8-Rex Banner - Blast.mp3": "Rex Banner - Blast __determined.mp3",
 "9-Louis Island - Glad You Came - Instrumental version.mp3": "Louis Island - Glad You Came - Instrumental version __happy.mp3",
 "9-MRMUSTACHE - Kitty Kate - Instrumental version.mp3": "MRMUSTACHE - Kitty Kate - Instrumental version __playful.mp3",
 "9-Wheres LuLu - Start a War - Instrumental version.mp3": "Wheres LuLu - Start a War - Instrumental version __tense.mp3",
 "9-Yehezkel Raz - Corals Under the Sun.mp3": "Yehezkel Raz - Corals Under the Sun __peaceful.mp3",
 "Ben Fox - Closer Levels.mp3": "Ben Fox - Closer Levels __uplifting.mp3",
 "Ben Fox - Higher Love.mp3": "Ben Fox - Higher Love __uplifting.mp3",
 "Ben Fox - Tokyo Nights.mp3": "Ben Fox - Tokyo Nights __dreamy.mp3",
 "Ben Fox - Words.mp3": "Ben Fox - Words __hopeful.mp3",
 "Dodo Danciu - Seth.mp3": "Dodo Danciu - Seth __mysterious.mp3",
 "Elia Azarzar - March of the Damned - No Backing Vocals.mp3": "Elia Azarzar - March of the Damned - No Backing Vocals __dark.mp3",
 "Novembers - Look at This.mp3": "Novembers - Look at This __uplifting.mp3",
 "TURPAK - Rising Star.mp3": "TURPAK - Rising Star __inspiring.mp3",
 "h1-Evert Z - Café Français.mp3": "Evert Z - Café Français __playful.mp3",
 "h2-Assaf Ayalon - The Beat of the Land.mp3": "Assaf Ayalon - The Beat of the Land __determined.mp3",
 "h2-Risian - Stampede.mp3": "Risian - Stampede __epic.mp3",
 "h5-Itai Argaman - Wishful Thinking.mp3": "Itai Argaman - Wishful Thinking __hopeful.mp3",
}

SKIP = {  # filename -> lý do (KHÔNG copy)
 "9-Dodo Danciu - Scarlett.mp3": "pool đã có 'Scarlett - Creative Cut - Dreamy' — tránh trùng-bài-khác-tên (y ca SKIP đợt 1)",
 "6-IamDayLight - Seine River.mp3": "trùng nội bộ staging với bản 2- (AMZ 38 vs AMZ 40) — giữ 1 bản",
}

HOLD = set()  # đợt này không có tên mù

existing = {p.stem.split("__")[0].strip().lower() for p in DST.glob("*") if p.is_file()}
copied, skipped, held, unmapped, dup_pool = [], [], [], [], []
seen_dst = set()
for f in sorted(SRC.rglob("*")):
    if not f.is_file() or f.parent.name not in NEW_DIRS:
        continue
    name = f.name
    if name in HOLD:
        held.append(name); continue
    if name in SKIP:
        skipped.append((name, SKIP[name])); continue
    if name not in IMPORT:
        unmapped.append(name); continue
    dst_name = IMPORT[name]
    base = dst_name.split("__")[0].strip().lower()
    if base in existing:
        dup_pool.append(name); continue
    if dst_name in seen_dst:
        continue
    shutil.copy2(f, DST / dst_name)
    seen_dst.add(dst_name)
    copied.append(dst_name)

print(f"COPY vào pool: {len(copied)}")
print(f"SKIP (trùng): {len(skipped)} | trùng pool phát hiện lúc chạy: {len(dup_pool)}")
print(f"GIỮ STAGING chờ tai: {len(held)}")
if dup_pool:
    print("Trùng pool:", dup_pool)
if unmapped:
    print(f"!! CHƯA MAP ({len(unmapped)}):")
    for n in sorted(set(unmapped)):
        print("   ", n)
