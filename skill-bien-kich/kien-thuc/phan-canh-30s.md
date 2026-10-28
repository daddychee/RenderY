# Phim clip 30 giây (Spec 55, Spec 71 K)

Chỉ đọc khi dòng đầu `00-nhip.md` có `Clip: 30s` (Mango: clip luôn 30 giây, có tiếng, tối đa 9 ảnh). `phan-canh.md` vẫn giữ trọn; mọi số "clip" ở đó, ở `phan-clip.md`, `tran-danh.md` và khung đọc theo **đơn vị 15 giây**: cảnh 30s là 2, cảnh 10s hay 15s là 1.

## Cảnh 30 giây: một khoảnh khắc liền

Một nơi, một lúc, không ngắt thời gian. Cảnh chở một hay hai nấc (khối A rồi khối B); nấc sau **do nấc trước gây ra** (hệ quả, phản ứng, đáp lời, nấc nguy kế), nối được bằng "vì A nên B" trên màn hình. Chỗ chuyển nấc nằm đâu do nhịp quyết, không buộc giây 15. Hai việc rời trong một cảnh thì clip hay mất phần sau, tự bịa chuyện.
- **Ô Mục đích:** loại từng khối nối bằng ` + `, việc hai khối ngăn bằng ` → `. Một việc kéo cả hai khối thì một loại (máy tính 2 đơn vị). Vế việc vẫn không `;`, "rồi", "và".
- **Ô Bối cảnh:** đúng một mã `DDxx`.
- **Shot:** 6–9 shot hard cut (cảnh trận: `tran-danh.md`), shot 2–5 giây, dài nhất 6 giây (lặng sau câu đắt, hạ nhịp), **shot đầu tối đa 4 giây**; không cú máy liền quá 6 giây.
- **Cắt theo chuyện, không theo đồng hồ:** mỗi lần cắt có cớ (ánh nhìn dẫn sang, động tác nối qua shot sau, câu nói xong thì sang mặt người nghe, hậu quả của cú vừa rồi); không chia hai nửa bằng nhau. Nút **Tách cảnh** trên web tự chia lại theo giây editor chọn.
- **Mỗi nấc một neo** ở đúng mốc giây: câu thoại, tiếng nổi, vật hay động tác lớn. Nấc sau không chỉ là mặt nhìn.
- **Thoại:** tối đa 4 câu, 40 từ, câu 12 từ, 2 người nói (3 khi cả cảnh đứng yên nói chuyện); vẫn 3 từ một giây. Câu đắt có 2–3 giây lặng sau trong cùng shot hay shot liền sau. Khung ghi "mỗi clip N câu" đọc "mỗi 15 giây".
- **Ảnh:** tối đa 3 nhân vật rõ mặt, 1 nơi, 2 vật gieo/gặt; đám đông, người phụ không tên không tính.

Mẫu (chỉ các ô khác cảnh 15s):
```
## P21 · Lá thư · 30s · N13
- Mục đích kể chuyện: việc + sau đỉnh · lá thư báo tin con trai mất → người cha ngồi sụp xuống bậc cửa  |  Bối cảnh, thời điểm: DD04 hiên nhà, chiều mưa  |  …
- Cách dựng: 8 shot hard cut
- Hành động theo nhịp: 0–3s trung rộng: … → 3–6s cận … → 6–10s đặc tả … → 10–14s cận NV07: "Tôi rất tiếc, thưa ông." → 14–19s trung: … → 19–23s đặc tả … → 23–27s cận NV03: "Nó mới mười chín tuổi." → 27–30s trung rộng, *lùi ra*: …
```

## Số đổi theo đơn vị

| Luật | Phim 15s | Phim 30s |
|---|---|---|
| Khoảnh khắc lớn | 2 clip | 1 cảnh 30s `lớn 1/1 <tên>`, khối B đi tiếp khối A (lựa chọn: A giằng xé, B quyết có lời) |
| `sau đỉnh` vỡ bằng thân thể (chạm) | 1 clip | khối A (từ 12 giây, ba nhịp) của cảnh kế cùng nơi, hay một cảnh 30s |
| Vòng phản ứng sau cú lật | clip 10s | khối B của cảnh lật (`việc + sau đỉnh`): 3 cận không thoại 3–4 giây rồi một shot trung. `Sau đỉnh` mức 4–5 cũng là khối B cảnh đỉnh hay khối A cảnh kế |
| Cú lật lớn nhất | 6 clip (tối thiểu 4) | 3 cảnh 30s liền (tối thiểu 2): `lật 1/3` chạm đáy (A trong nhân vật, B người thân gào) · `lật 2/3` nhớ lý do + bùng · `lật 3/3` phá ra + lộ diện, có câu nói ra |
| Clip nối | clip 10s | khối A của cảnh 30s đầu ở nơi mới (`nối + việc`): 6–10 giây toàn cảnh, người tới; ô Bối cảnh chỉ mã nơi đích |
| Trận | mỗi clip một đổi thế | cảnh 30s hai lần đổi thế (2–4 đòn mỗi lần), không buộc chia ở giây 15 (`tran-danh.md`) |

## Cảnh 10/15 giây xen (Seedvis)

Chỉ bốn chỗ, tổng tối đa 20% giây phim, viết như phim 15s: (1) móc `N01` 2–3 cảnh 15s theo `moc-mo-phim.md`, cảnh hạ nhịp liền sau 15s; (2) nối đường đi đổi nơi trong lúc đi (`DD03 → DD06`); (3) một shot liền dài hơn 6 giây; (4) cảnh bộ lọc Mango chặn mãi (web đã tự gen lại mà vẫn hỏng), khi viết lại.

**Máy** (`dem_phan_canh.py`): LỖI cảnh 30s hơn một mã nơi; CẢNH BÁO shot đầu, shot dài, số shot, thoại, quá 3 mã NV, cảnh 15s quá 20%.
