# AutoEdit (PADOMA MEDIA)

Tool tự động dựng video YouTube bán content: script + voice ElevenLabs → CapCut draft nhiều track.
Xem `../CLAUDE.md`, `../PRD.md`, `../KE_HOACH_TRIEN_KHAI.md` ở folder cha để biết bối cảnh.

## Cài đặt
```bash
uv sync                      # cài dependency vào .venv
cp .env.example .env         # rồi điền API key thật
```

## Dùng (M0)
```bash
uv run autoedit new --script samples/script.txt --voice samples/voice.mp3
```
Lệnh tạo một folder project trong `projects/<id>/` với `project.json` — nguồn sự thật duy nhất của video đó.

## Test
```bash
uv run pytest -q
```
