# Cài máy editor để viết kịch bản phim bằng `/bien-kich` và bóc phim mẫu bằng `/boc-phim-bien-kich`

Claude trên máy editor đọc file này khi editor nhờ "cài máy theo HUONG-DAN-CAI.md", rồi làm lần lượt. Không sửa file nào trong thư mục này. Phần A là việc anh/chị chủ dự án làm một lần trên máy chủ.

## A. Máy chủ: chia sẻ thư mục qua mạng LAN (anh/chị tự làm)

1. Không chia sẻ cả repo `D:\padoma\GEN VIDEO` (trong đó có `.env` chứa key Seedvis).
2. Chia sẻ thư mục `D:\padoma\GEN VIDEO\skill bien kich`: chuột phải > Properties > Sharing > Advanced Sharing > tick "Share this folder", tên chia sẻ `skill-bien-kich`, Permissions: tài khoản editor chỉ **Read**. Editor chỉ ghi vào ổ F:, không ghi vào thư mục này.
3. Tạo `.env` trong thư mục này từ `.env.example` (chỉ có đường dẫn thư mục phim và thư mục kho biên kịch, không key).
4. Giữ chia sẻ `F:\gen_video_data` (editor cần đọc-ghi `phim` và `kho-bien-kich`).
5. Trên máy editor, map ổ: `\<tên máy chủ>\skill-bien-kich` (ví dụ ổ `B:`), và `F:` như cũ.

## B. Máy editor (Claude làm)

### Bước 1. Xác nhận đang ở máy editor

Thư mục làm việc là ổ mạng hay đường dẫn mạng, không phải `D:\padoma\GEN VIDEO\skill bien kich`. Đang ở đó thì đây là máy chủ: dừng.

### Bước 2. File `.env`

Kiểm `.env` có tồn tại (không in nội dung). Chưa có thì báo editor nhắn chủ dự án. `THU_MUC_PHIM` và `THU_MUC_KHO_BIEN_KICH` phải trỏ đúng ổ F: của máy editor; máy editor map F: khác chữ thì editor đặt hai biến môi trường cùng tên trên máy mình (biến môi trường thắng `.env`).

### Bước 3. Ổ dữ liệu

```powershell
Test-Path "F:\gen_video_data\phim"
Test-Path "F:\gen_video_data\kho-bien-kich"
```

Phải ra hai `True`. Thử quyền ghi: tạo rồi xóa `F:\gen_video_data\phim\_thu_ghi.txt` và `F:\gen_video_data\kho-bien-kich\_thu_ghi.txt`. Không ghi được thì báo editor nhờ chủ dự án cấp quyền ghi.

### Bước 4. Python

```powershell
python --version
```

Cần 3.11 trở lên, chỉ Python thường, không cần thư viện thêm. Lệnh `py -3` cũng phải chạy (skill bóc phim dùng lệnh này); thiếu thì cài Python bản python.org, tick "py launcher".

### Bước 4b. yt-dlp và ffmpeg (chỉ cần cho `/boc-phim-bien-kich`)

```powershell
yt-dlp --version
ffmpeg -version
```

Thiếu cái nào thì cài bằng winget (không cần quyền quản trị), rồi mở lại terminal và chạy lại hai lệnh trên:

```powershell
winget install --id yt-dlp.yt-dlp -e
winget install --id Gyan.FFmpeg -e
```

Không cài được thì báo editor: vẫn viết kịch bản bằng `/bien-kich` bình thường, chỉ chưa bóc phim được.

### Bước 5. Chạy thử

```powershell
python cong-cu/muc_luc.py CLAUDE.md
python cong-cu/doc_kho.py KB01
py -3 .claude/skills/boc-phim-bien-kich/thu_muc.py _thu
```

Lệnh đầu in danh sách mục, lệnh hai in một mục kho, lệnh ba in `F:\gen_video_data\kho-bien-kich\_thu` là được; xóa thư mục `_thu` đó.

### Bước 6. Báo kết quả

Báo editor từng bước đạt hay không, và cách dùng:

1. Mở Claude Code ở thư mục này (ổ mạng), gõ `/bien-kich`. Claude hỏi hai lượt, ra dàn ý `00-nhip.md` để bạn duyệt, rồi viết và soát phần 1 (khoảng 7 phút), gộp và dừng để bạn gen thử; bảo "viết tiếp" thì làm phần sau. Chat đầy thì mở chat mới gõ `/bien-kich <mã> tiếp`. Xong thì mở `F:\gen_video_data\phim\<mã>\kich-ban.md`, chép hết, dán vào trang **Phim mới** trên web, đăng nhập bằng tài khoản riêng.
   Phim drama nhiều thoại (Veo xen Seedance): gõ `/bien-kich-drama` thay cho `/bien-kich`; bạn duyệt dàn ý, còn lại skill tự viết và soát từng phần 10 phút, rồi gộp ra `kich-ban.md` như trên. Dán thì chọn loại Drama thoại.
2. Mỗi phim một mã riêng, không trùng mã phim người khác đang làm.
3. Bóc phim mẫu vào kho biên kịch: gõ `/boc-phim-bien-kich <link YouTube> <tên ngắn>`. Xong thì nhắn chủ dự án tên thư mục và thể loại phim; file `muc.json` đã nằm ở ổ F:, không cần gửi.
4. Máy chủ tắt thì không làm được; mất mạng giữa chừng thì mở lại chat, gõ `/bien-kich <mã> tiếp`, việc đã ghi ở ổ F: không mất.
