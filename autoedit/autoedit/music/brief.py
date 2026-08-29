"""[LEGACY 14/06] Brief Cowork lấy tag mood từ Artlist.

KHÔNG còn là luồng chính: cào mood Artlist chập chờn → đã chuyển sang gắn mood TRONG TÊN FILE
(`Artist - Title __mood.mp3`, xem music/naming.py). Giữ file này để tham khảo, không gọi trong CLI.
"""

from __future__ import annotations

COWORK_BRIEF = """\
# Nhiệm vụ: lấy TAG nhạc từ Artlist cho thư viện AutoEdit

Bạn đang đăng nhập Artlist trong Chrome. Các bản nhạc (KHÔNG lời, instrumental) đã được tải
sẵn vào thư mục `MusicLibrary/tracks/`. Việc của bạn: mở trang Artlist của TỪNG bài, đọc tag,
và ghi vào một file YAML để tool dùng.

Với mỗi file nhạc trong `tracks/`:
1. Tìm/mở đúng trang bài đó trên Artlist (tên file dạng "Artist - Title").
2. Đọc các tag trang hiển thị: Mood, Genre, Vocals, BPM, Video Theme, Instruments.
3. Ghi 1 mục vào file `MusicLibrary/music_manifest.yaml` (tạo nếu chưa có).

Định dạng music_manifest.yaml:
```yaml
tracks:
  - file: "Roie Shpigler - Northland.mp3"      # đúng tên file thật trong tracks/
    artlist_url: "https://artlist.io/royalty-free-music/song/.../12345"
    title: "Northland"
    artist: "Roie Shpigler"
    vocals: instrumental                         # GẦN NHƯ LUÔN instrumental
    mood: [peaceful, hopeful, nostalgic]         # 1-3 tag mood của Artlist
    genre: [cinematic, ambient]
    video_theme: [travel, documentary]
    instruments: [piano, strings]
    bpm: 92                                       # nếu trang có ghi (không thì bỏ)
```

QUAN TRỌNG — chỉ dùng tag trong danh sách CHUẨN dưới (đổi tag Artlist gần nghĩa về đây):
- mood: epic, uplifting, inspiring, hopeful, happy, playful, peaceful, dreamy, romantic,
  nostalgic, mysterious, suspenseful, tense, dark, sad, angry, scary, serious, determined
- genre: cinematic, ambient, electronic, acoustic, classical, hip_hop, rock, pop, folk,
  jazz, world, lo_fi
- vocals: instrumental, vocal_samples (nếu có người hát rõ lời thì BÁO — KHÔNG dùng cho nền)
- video_theme: documentary, true_crime, travel, technology, business_finance, history,
  nature, lifestyle, motivational

Không cần ghi energy/sections — tool tự phân tích từ file. Xong báo lại, tôi chạy
`autoedit music-import` để nạp.
"""


def write_brief(path) -> None:
    from pathlib import Path

    Path(path).write_text(COWORK_BRIEF, encoding="utf-8")
