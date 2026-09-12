"""BH24: test chuỗi xanh KHÔNG chứng minh JS chạy được — phải mở Chrome thật."""
from playwright.sync_api import sync_playwright

DUONG = "file:///F:/RenderY_v2/autoedit/autoedit/web/static/index.html"
HAM = ["ofPhanTichLai", "ofDoLaiKhay", "ofXuatThat", "ofNap", "ofVeAll", "ofBaoChiXem"]

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page()
    loi = []
    pg.on("pageerror", lambda e: loi.append(f"PAGEERROR {e}"))
    pg.on("console", lambda m: loi.append(f"CONSOLE {m.type}: {m.text}")
          if m.type == "error" else None)
    pg.goto(DUONG, wait_until="load")
    pg.wait_for_timeout(1200)
    for h in HAM:
        kq = pg.evaluate(f"typeof {h}")
        print(f"  typeof {h:16} = {kq}")
    nut = pg.evaluate(
        "Array.from(document.querySelectorAll('button')).filter(b=>b.textContent.includes"
        "('Phân tích lại')).map(b=>({chu:b.textContent.trim(),goi:b.getAttribute('onclick')}))")
    print("  nut tim thay:", nut)
    print("  loi trang:", [x for x in loi if "fetch" not in x.lower()][:5] or "KHONG CO")
    b.close()
