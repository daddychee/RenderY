# -*- coding: utf-8 -*-
"""Nhạc staging life-in → pool ~/AutoEdit/music/tracks (mẫu deepsea: mood TỪ TÊN).
COPY-only. 3 nhóm: IMPORT (map tường minh) · SKIP (rác/trùng pool, ghi lý do) ·
STAGING (tên mù chờ tai user). Chạy xong in bảng tổng."""
import shutil
from pathlib import Path

SRC = Path(r"F:\AutoEdit\music_editor")
DST = Path.home() / "AutoEdit" / "music" / "tracks"

# filename staging -> ("Artist - Title __mood.ext") — mood theo prefix editor + nghĩa title
IMPORT = {
 "Adam Dib - It Comes at Night.wav": "Adam Dib - It Comes at Night __dark.wav",
 "Adam Dib - Pieces of the Puzzle - No Choir.mp3": "Adam Dib - Pieces of the Puzzle - No Choir __mysterious.mp3",
 "Adam Dib - Where the Light Returns - No Backing Vocals.mp3": "Adam Dib - Where the Light Returns - No Backing Vocals __hopeful.mp3",
 "adventure - Lance Conrad - Pursuit Predation.wav": "Lance Conrad - Pursuit Predation __tense.wav",
 "Alon Ohana - Songbirds.mp3": "Alon Ohana - Songbirds __peaceful.mp3",
 "Alon Peretz - Asturias.mp3": "Alon Peretz - Asturias __nostalgic.mp3",
 "Altamera - Frunza Verde Foi Marunte feat Catrinele.mp3": "Altamera - Frunza Verde Foi Marunte feat Catrinele __nostalgic.mp3",
 "Assaf Ayalon - Hands Free.mp3": "Assaf Ayalon - Hands Free __uplifting.mp3",
 "Assaf Ayalon - The Light Descends.mp3": "Assaf Ayalon - The Light Descends __dreamy.mp3",
 "Bara Matahari Pagi - The Lost Planet.wav": "Bara Matahari Pagi - The Lost Planet __mysterious.wav",
 "Ben Aylon - Finya.mp3": "Ben Aylon - Finya __determined.mp3",
 "Borden Lulu - The Southern Lake.mp3": "Borden Lulu - The Southern Lake __peaceful.mp3",
 "Borrtex - Do What You Love.mp3": "Borrtex - Do What You Love __inspiring.mp3",
 "Borrtex - Hustle Harder.mp3": "Borrtex - Hustle Harder __determined.mp3",
 "CLASSICAL Anthony Vega - Behind the Mountain.wav": "Anthony Vega - Behind the Mountain __peaceful.wav",
 "CLASSICAL Ian Post - Jingle Bells.wav": "Ian Post - Jingle Bells __happy.wav",
 "Dan Ayalon - Biniciler Riders.wav": "Dan Ayalon - Biniciler Riders __determined.wav",
 "Daniel Magen - Letting Go.mp3": "Daniel Magen - Letting Go __sad.mp3",
 "Dimitrix - Stinky Sax.mp3": "Dimitrix - Stinky Sax __playful.mp3",
 "DOCUMENT Tristan Barton - The Racer.wav": "Tristan Barton - The Racer __serious.wav",
 "DOCUMENT TURPAK - Now or Never.wav": "TURPAK - Now or Never __determined.wav",
 "Dr Paranoid - The Hope Lounge.mp3": "Dr Paranoid - The Hope Lounge __hopeful.mp3",
 "Elad Perez - Hey Hey.mp3": "Elad Perez - Hey Hey __happy.mp3",
 "Elijah Aaron - Homebound.mp3": "Elijah Aaron - Homebound __nostalgic.mp3",
 "epic Sam Lux - Celestial Rush.wav": "Sam Lux - Celestial Rush __epic.wav",
 "EVOE - Fathoms.wav": "EVOE - Fathoms __mysterious.wav",
 "EVOE - Passage.mp3": "EVOE - Passage __mysterious.mp3",
 "FableForte - Shadowed Dunes.mp3": "FableForte - Shadowed Dunes __mysterious.mp3",
 "fantasy FableForte - Monuments of the Ancients.wav": "FableForte - Monuments of the Ancients __epic.wav",
 "fantasy Will Van De Crommert - My One Safe Haven.wav": "Will Van De Crommert - My One Safe Haven __dreamy.wav",
 "Fast Ardie Son - Omega.wav": "Ardie Son - Omega __determined.wav",
 "Flint - Peach Jam.mp3": "Flint - Peach Jam __playful.mp3",
 "folk Elad Perez - Beautiful Day.wav": "Elad Perez - Beautiful Day __happy.wav",
 "folk To The Valley - Gold Dust - Instrumental version.wav": "To The Valley - Gold Dust - Instrumental version __nostalgic.wav",
 "Foster - Open up My Heart - Instrumental version.mp3": "Foster - Open up My Heart - Instrumental version __romantic.mp3",
 "Gal Lev - Left Behind.mp3": "Gal Lev - Left Behind __sad.mp3",
 "Hans Johnson - Blessings.wav": "Hans Johnson - Blessings __hopeful.wav",
 "Hans Johnson - Simon My Brother.wav": "Hans Johnson - Simon My Brother __nostalgic.wav",
 "Itay Kashti - United.mp3": "Itay Kashti - United __inspiring.mp3",
 "Jimmy Svensson - Boot Sequence.wav": "Jimmy Svensson - Boot Sequence __tense.wav",
 "Jozeque - Afterlife.mp3": "Jozeque - Afterlife __mysterious.mp3",
 "Kyle Preston - Tribal War Victory.wav": "Kyle Preston - Tribal War Victory __epic.wav",
 "Lance Conrad - Featherlight.wav": "Lance Conrad - Featherlight __peaceful.wav",
 "Le Marigold - Aaraam.mp3": "Le Marigold - Aaraam __peaceful.mp3",
 "light Ketil Lien - Distant Skyline.wav": "Ketil Lien - Distant Skyline __peaceful.wav",
 "Liron Meyuhas - Tornado.mp3": "Liron Meyuhas - Tornado __tense.mp3",
 "Mahesh Vinayakram - Guruvea SHARANAM - Instrumental version (3).mp3": "Mahesh Vinayakram - Guruvea SHARANAM - Instrumental version __peaceful.mp3",
 "Marco Martini - Quantum Edge.mp3": "Marco Martini - Quantum Edge __suspenseful.mp3",
 "Marko Maksimovic - The Eiffel Tickle.wav": "Marko Maksimovic - The Eiffel Tickle __playful.wav",
 "Noam Zaguri - Driving Home.mp3": "Noam Zaguri - Driving Home __nostalgic.mp3",
 "Onyx Music - Samarkhand Pulse.mp3": "Onyx Music - Samarkhand Pulse __mysterious.mp3",
 "Out of Flux - finallyfree - No Brass.mp3": "Out of Flux - finallyfree - No Brass __uplifting.mp3",
 "Patrick Sebag - Hours.mp3": "Patrick Sebag - Hours __dreamy.mp3",
 "PERSIAN idokay - Market District.wav": "idokay - Market District __playful.wav",
 "PERSIAN Onyx Music - Home.wav": "Onyx Music - Home __nostalgic.wav",
 "Raz Burg - Un Atardecer Ardiente - Instrumental Version.mp3": "Raz Burg - Un Atardecer Ardiente - Instrumental Version __romantic.mp3",
 "Rex Banner - Cheers.mp3": "Rex Banner - Cheers __happy.mp3",
 "Risian - Imagine a World.mp3": "Risian - Imagine a World __inspiring.mp3",
 "Roberto Prado - The Time is Now (1).mp3": "Roberto Prado - The Time is Now __determined.mp3",
 "Roie Shpigler - Clarity.wav": "Roie Shpigler - Clarity __peaceful.wav",
 "Roie Shpigler - Fata Morgana.mp3": "Roie Shpigler - Fata Morgana __mysterious.mp3",
 "Roie Shpigler - Organic Reflections.mp3": "Roie Shpigler - Organic Reflections __dreamy.mp3",
 "Roie Shpigler - Sleepwalker - No Backing Vocals.mp3": "Roie Shpigler - Sleepwalker - No Backing Vocals __dreamy.mp3",
 "Romeo - Deep Lake.wav": "Romeo - Deep Lake __peaceful.wav",
 "Romeo - Rivulet - Creative Cut - Piano.mp3": "Romeo - Rivulet - Creative Cut - Piano __peaceful.mp3",
 "Sahara - Baghdad Nights.mp3": "Sahara - Baghdad Nights __mysterious.mp3",
 "SAD - Michael FK - Immersion.wav": "Michael FK - Immersion __sad.wav",
 "SAD Angelika Conrad - Sepia.wav": "Angelika Conrad - Sepia __sad.wav",
 "sad Philip Daniel - Pyramid Lung.wav": "Philip Daniel - Pyramid Lung __sad.wav",
 "SHYLIFE - The Colors of Magic.mp3": "SHYLIFE - The Colors of Magic __dreamy.mp3",
 "slow - doc Borrtex - The Real Heroes.wav": "Borrtex - The Real Heroes __serious.wav",
 "SLOW - DOC Hans Johnson - Earth Analog.wav": "Hans Johnson - Earth Analog __serious.wav",
 "Solis - Oscillating Form.wav": "Solis - Oscillating Form __mysterious.wav",
 "Steven Beddall - Departure.mp3": "Steven Beddall - Departure __nostalgic.mp3",
 "Suraj Nepal - Purity.mp3": "Suraj Nepal - Purity __peaceful.mp3",
 "The Cliff - Goes Without Saying.mp3": "The Cliff - Goes Without Saying __uplifting.mp3",
 "The Magnetic Buzz - Time to Run.wav": "The Magnetic Buzz - Time to Run __tense.wav",
 "The Pack - A Cigar and Glass of Wine.mp3": "The Pack - A Cigar and Glass of Wine __playful.mp3",
 "Tiko Tiko - Against All Odds.mp3": "Tiko Tiko - Against All Odds __determined.mp3",
 "Timothy Shortell - Turning Tides - Instrumental version.wav": "Timothy Shortell - Turning Tides - Instrumental version __inspiring.wav",
 "travel Zac Nelson - Encounter.wav": "Zac Nelson - Encounter __uplifting.wav",
 "Ty Simon - Tea Time.mp3": "Ty Simon - Tea Time __playful.mp3",
 "Will Van De Crommert - Water and Stone.wav": "Will Van De Crommert - Water and Stone __peaceful.wav",
 "Ziv Moran - Return.mp3": "Ziv Moran - Return __hopeful.mp3",
 "Ziv Moran - Still On.mp3": "Ziv Moran - Still On __determined.mp3",
}

SKIP = {  # filename -> lý do (KHÔNG copy)
 "Adam Dib - Where the Light Returns.wav": "variant có vocals của bản No Backing Vocals — tránh cặp trùng",
 "Lance Conrad - Pursuit Predation.mp3": "trùng bản wav (prefix adventure)",
 "Dodo Danciu - Scarlett.wav": "pool đã có 'Scarlett - Creative Cut - Dreamy' — tránh trùng-bài-khác-tên",
 "EPIC - Matthias Förster - No Regrets - No Backing Vocals.wav": "pool đã có 'No Regrets'",
 "folk Ziv Moran - Wild Grace.wav": "pool đã có",
 "Peter Matri - Invasion.wav": "pool đã có 'Invasion (1)'",
 "Yair Cohen - Our Home.mp3": "pool đã có",
 "Ziv Moran - EVERGREEN - Short version.mp3": "pool đã có + parser bỏ 'short version'",
 "lumine wave - Empires Fall.mp3": "pool đã có 'Creative Cut - Piano' — tránh trùng-bài-khác-tên",
 "RD72.1.mp3": "voice REAL72", "RD72.2.mp3": "voice REAL72", "RD72.3.mp3": "voice REAL72",
 "RD72.4.mp3": "voice REAL72", "RD72.5.mp3": "voice REAL72", "RD72.6.mp3": "voice REAL72",
 "RD76-1.mp4": "file voice/video", "REAL -  RD63.mp4": "file voice/video",
 "REAL - RD06.mp4.mp4": "file voice/video", "REAL - RD10.mp4.mp4": "file voice/video",
 "REAL - RD13.mp4.mp4": "file voice/video", "REAL - RD21.mp4.mp4": "file voice/video",
 "REAL - RD28.mp4.mp4": "file voice/video", "REAL - RD29.mp4.mp4": "file voice/video",
 "REAL - RD36.mp4.mp4": "file voice/video", "real - rd56.mp4": "file voice/video",
 "Các kiểu cài sẵn của tôi11##385C4063-CF9A-4602-BAA7-0EB83DE8BB1F.aac": "preset editor",
 "Các kiểu cài sẵn của tôi11##53AB3278-95ED-4083-8862-AA7B8CE47475.aac": "preset editor",
 "Các kiểu cài sẵn của tôi11##94D9082E-B42C-4a8f-B7F9-B1743F37C535.aac": "preset editor",
 "Các kiểu cài sẵn của tôi12##62F9DBE1-DDE5-412d-B485-1F8EB104C188.aac": "preset editor",
 "Lars Bork Andersen - Darker Days - Dramatic Motion - BO-000193-1 - ID-133189 - Brass and Woodwinds - 100 Bpm - F#m.wav": "stem — pool có bản full",
 "Lars Bork Andersen - Darker Days - Dramatic Motion - BO-000193-1 - ID-133189 - Percussion - 100 Bpm - F#m.wav": "stem",
 "Lars Bork Andersen - Darker Days - Dramatic Motion - BO-000193-1 - ID-133189 - Piano - 100 Bpm - F#m.wav": "stem",
 "Lars Bork Andersen - Darker Days - Dramatic Motion - BO-000193-1 - ID-133189 - SFX - 100 Bpm - F#m.wav": "stem",
 "Lars Bork Andersen - Darker Days - Dramatic Motion - BO-000193-1 - ID-133189 - Synths 1 - 100 Bpm - F#m.wav": "stem",
 "Lars Bork Andersen - Darker Days - Dramatic Motion - BO-000193-1 - ID-133189 - Synths 2 - 100 Bpm - F#m.wav": "stem",
}

HOLD = {  # tên mù — GIỮ staging chờ tai user
 "chill music##62F9DBE1-DDE5-412d-B485-1F8EB104C188.aac",
 "SLOW JAPAN.mp3", "SUMO.mp3",
}

existing = {p.stem.split("__")[0].strip().lower() for p in DST.glob("*") if p.is_file()}
copied, skipped, held, unmapped, dup_pool = [], [], [], [], []
seen_dst = set()
for f in sorted(SRC.rglob("*")):
    if not f.is_file() or "REAL" not in f.parent.name:
        continue
    name = f.name
    if name in HOLD:
        held.append(name); continue
    if name in SKIP:
        skipped.append((name, SKIP[name])); continue
    if name not in IMPORT:
        unmapped.append(name); continue
    dst_name = IMPORT[name]
    base = dst_name.rsplit("__", 1)[0].strip().lower().rstrip()
    base = dst_name.split("__")[0].strip().lower()
    if base in existing:
        dup_pool.append(name); continue
    if dst_name in seen_dst:
        continue  # cùng bài xuất hiện ở nhiều draft folder
    shutil.copy2(f, DST / dst_name)
    seen_dst.add(dst_name)
    copied.append(dst_name)

print(f"COPY vào pool: {len(copied)}")
print(f"SKIP (rác/trùng): {len(skipped)} | trùng pool phát hiện lúc chạy: {len(dup_pool)}")
print(f"GIỮ STAGING chờ tai: {len(held)} -> {sorted(held)}")
if dup_pool:
    print("Trùng pool:", dup_pool)
if unmapped:
    print(f"!! CHƯA MAP ({len(unmapped)}):")
    for n in sorted(set(unmapped)):
        print("   ", n)
