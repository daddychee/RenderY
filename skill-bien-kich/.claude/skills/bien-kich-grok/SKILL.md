---
name: bien-kich-grok
description: Viết kịch bản phim drama nhiều thoại gen cả phim bằng Grok (loại drama_thoai, mọi clip `Grok 15s`, độ dài thật chọn trên treatment, Spec 69; tránh hành động nặng, tối đa 4 người rõ mặt mỗi clip): bảng hỏi, dàn ý, anh/chị duyệt, trợ lý viết và soát từng phần 10 phút, gộp ra kich-ban.md dán vào treatment (AI Generation). Dùng khi anh/chị nói "drama Grok", "kịch bản cho Grok", "phim gen bằng Grok", hoặc gõ /bien-kich-grok.
model: claude-opus-5-5
---

# Biên kịch drama cho Grok: từ đề bài tới `kich-ban.md`

Mức suy nghĩ medium (khác thì `/effort medium`). Đối số: ý tưởng phim (bước 1), hay `<mã> tiếp`: đọc `BAN-GIAO.md` của phim, làm tiếp bước ghi ở đó.

Bản này là `/bien-kich-drama` (`.claude/skills/bien-kich-drama/SKILL.md`) viết cho Grok: câu chuyện giữ nguyên (khung `kien-thuc/khung/drama-da-den.md`, mở phim, gieo gặt), chỉ đổi máy, cách chia clip, cú máy, hành động, số người, đồ, ánh sáng. Chỗ ghi "như drama bước n" thì Read đúng mục bước đó của skill drama. Khuôn, clip ở `kien-thuc/grok-drama.md` (thay mục 2, 3, 4, 8, 9 của `drama-thoai.md`; mục 1, 5, 6, 7 dùng chung). Máy kiểm: `cong-cu/dan_y_drama.py`, `cong-cu/kiem_drama.py` (tự nhận kịch bản Grok từ dòng `Máy: Grok`).

**Kết quả:** `<THU_MUC_PHIM>/<mã>/kich-ban.md`, gộp từ `kich-ban/00-dan-y.md`, `phan-01.md`…, không sửa tay. Anh/chị dán vào **treatment** (AI Generation, cổng 9121): tạo tập, chọn loại **2 = Drama có thoại**, dán cả file ở màn Kịch bản; phần mới viết thêm thì bấm **⇪ Dán lại kịch bản** (clip cùng mã P giữ video và độ dài đã chọn).

**Token:** như drama (chat chính không Read `phan-NN.md`, quá 20 trợ lý thì ghi `BAN-GIAO.md`, báo anh/chị mở chat mới gõ `/bien-kich-grok <mã> tiếp`).

## Bước 1. Bảng hỏi, hai lượt

Như drama bước 1, khác:
- **Hợp Grok:** drama sống bằng lời, giấy tờ, mặt người nói và nghe; nơi ít người (nhà, bếp, văn phòng, xe). Ý tưởng cần đánh nhau, rượt đuổi, cứu người, tiệc đông, sảnh đông: nói nhẹ "Grok làm hỏng cảnh hành động và đám đông; phim này hợp Seedance (`/bien-kich-drama`)", rồi đề xuất bản bớt hành động hay đổi skill.
- Lượt 1: mỗi ý ghi thêm cú lật làm bằng gì (câu nói, giấy tờ, vật đưa ra), không bằng xô đẩy.
- Lượt 2: câu 6 (trận) thành **xung đột thân thể**: mặc định không; cần thì chỉ chạm nhẹ một động tác (`grok-drama.md` mục 9). Bỏ câu 7 (mức Seedance). Tiền gen: Grok qua Seedvis 108 credit mỗi clip, 6/10/15 giây cùng giá.

## Bước 2. Dàn ý `kich-ban/00-dan-y.md`

Đọc thêm như drama bước 2, cộng `kien-thuc/grok-drama.md` trọn file. Khuôn như drama bước 2, chỉ khác ba dòng đầu (không dòng `Seedance:`):

```
# <Tên phim>
Loại phim: drama_thoai
Thể loại: drama-da-den · Độ dài: 70 phút · Tỉ lệ: 16:9
```

- **Mốc, Mở phim, Gieo và gặt, Phần** như drama bước 2. "Cú xô đỉnh nhục" của khung (điều 4) thành lời nhục, đồ bị ném, bị giật; cách thắng là chứng cứ, lời, người có quyền.
- **Nơi:** ít người, ở lâu; nơi trong nhà có nguồn sáng rõ (Một câu tả ghi đèn, cửa sổ); cảnh đêm ghi `đêm` ở tiêu đề cảnh.
- **Cụm cố định** như drama; người đổi đồ (khoác áo người khác, cởi áo khoác, bỏ mũ) từ 3 cảnh trở lên thì dòng `dạng` cho cả người mặc và người cho mượn (`grok-drama.md` mục 3 điều 6).

**Tự soát điều máy không kiểm:** như drama bước 2, thêm: không mốc nào cần đánh, xô ngã, lôi kéo, ngã, lửa; mỗi cảnh tối đa 4 người rõ mặt cùng lúc, người thứ năm trở đi chỉ là lưng hay bóng mờ. Rồi `py -3 cong-cu/dan_y_drama.py kiem <phim>/kich-ban` tới hết LỖI.

## Bước 3. Duyệt

Như drama bước 3 (báo tối đa 18 dòng, ghi `BAN-GIAO.md`), bỏ dòng mức Seedance và trận; thêm cảnh đông người nhất (ai rõ mặt) và xung đột thân thể (nếu có).

## Bước 4. Viết rồi soát từng phần

Như drama bước 4 (mặc định dừng sau phần 1, lần lượt viết n, soát n), đổi trợ lý: viết `subagent_type: viet-phan-grok`, soát `subagent_type: soat-phan-grok`, lời giao y khuôn drama. Sau mỗi trợ lý tự chạy `py -3 cong-cu/kiem_drama.py <file phần>` (dòng tóm tắt phải bắt đầu `Phần n · Grok:`) và `py -3 cong-cu/dan_y_drama.py phan <file phần>`; còn LỖI thì giao lại đúng trợ lý kèm dòng lỗi.

## Bước 5. Gộp

Như drama bước 5, khác dòng báo: tiền gen = số clip × 108 credit (Seedvis); kèm NHẮC Grok còn giữ (hành động, số người, ô, đám đông) và vì sao. Ghi `BAN-GIAO.md`.

**Sửa sau khi dán:** như drama, trợ lý `soat-phan-grok`. Điều đáng nhớ (clip Grok editor phải gen lại vì gì) ghi `BAN-GIAO.md` mục "Đề xuất bài học".
