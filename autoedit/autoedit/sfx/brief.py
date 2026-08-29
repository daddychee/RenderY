"""Sinh brief paste vào Cowork (Claude-in-Chrome trên Artlist) để tải SFX."""

from __future__ import annotations

COWORK_BRIEF = """\
# Nhiệm vụ: tải SFX từ Artlist cho thư viện video AutoEdit

Bạn đang đăng nhập Artlist (có bản quyền) trong Chrome. Hãy tải các sound effect NGẮN
(ưu tiên ≤1.5 giây) cho thư viện điểm nhấn video. MỖI LOẠI tải 2-3 file khác nhau:

| loại (kind) | dùng cho | từ khóa tìm trên Artlist |
|---|---|---|
| cash   | hiện giá tiền ("$2")        | cash register, coin, ka-ching, money ding |
| impact | từ khóa nhấn ("FREE")        | impact, boom, deep hit, slam |
| pop    | số liệu ("45 ngày")          | pop, ui pop, bubble pop, tap |
| whoosh | chuyển cảnh/chương           | whoosh, swoosh, transition |
| riser  | dựng căng trước cao trào     | riser, build up, rise |

Yêu cầu:
- File ngắn, gọn, KHÔNG nhạc nền (chỉ tiếng động).
- Tải về thư mục mặc định của Chrome (~/Downloads).
- GIỮ NGUYÊN tên file Artlist khi tải (để truy ngược license).

Sau khi tải xong, tạo file **~/Downloads/sfx_manifest.yaml** liệt kê MỖI file đã tải
một dòng (đúng tên file thật vừa tải về):

```yaml
sfx:
  - {file: "Cash Register Ding.wav", kind: cash, artlist_url: "https://artlist.io/sfx/...", title: "Cash Register Ding"}
  - {file: "Coin Drop.wav", kind: cash, artlist_url: "https://artlist.io/sfx/...", title: "Coin Drop"}
  - {file: "Deep Boom Impact.wav", kind: impact, artlist_url: "https://artlist.io/sfx/...", title: "Deep Boom"}
  - {file: "UI Pop.wav", kind: pop, artlist_url: "https://artlist.io/sfx/...", title: "UI Pop"}
```

Quan trọng: `kind` PHẢI là một trong: cash, impact, pop, whoosh, riser. `file` đúng tên
file đã tải về ~/Downloads. Mỗi file một dòng.

Xong rồi báo lại, tôi sẽ chạy `autoedit sfx-import` để nạp vào thư viện.
"""


def write_brief(path) -> None:
    from pathlib import Path

    Path(path).write_text(COWORK_BRIEF, encoding="utf-8")
