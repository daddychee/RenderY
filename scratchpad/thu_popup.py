r"""Nghiem thu popup Export bang Chrome THAT (BH9) — khong kiem chuoi.

Nap index.html cua BAN DEV qua file://, goi thang ofXkHong/ofXkHoi roi DO bang
getComputedStyle + dem the that. Bat loi JS: file hong cu phap thi thay ngay.
"""
import sys, json
from pathlib import Path
from playwright.sync_api import sync_playwright

SRC = Path(r"F:/RenderY_v2/autoedit/autoedit/web/static/index.html").resolve()

def main() -> int:
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        pg = b.new_page(viewport={"width": 1500, "height": 950})
        loi = []
        pg.on("pageerror", lambda e: loi.append(f"PAGEERROR {e}"))
        pg.on("console", lambda m: loi.append(m.text) if m.type == "error" else None)
        pg.goto(SRC.as_uri(), wait_until="domcontentloaded")
        pg.wait_for_timeout(900)

        print("== CU PHAP JS ==")
        co = pg.evaluate("() => [typeof ofXkHong, typeof ofXkHoi, typeof ofToiHong, typeof esc]")
        print("  ofXkHong/ofXkHoi/ofToiHong/esc:", co)
        if any(x != "function" for x in co):
            print("  !! ham chua nap duoc — co the loi cu phap"); print(loi[:3]); b.close(); return 2

        # ── (a) link chet: 8 mieng -> cat 5 + "… va 3 mieng nua" ──
        pg.evaluate("""() => ofXkHong([...Array(8)].map((_, i) =>
            ({mieng: i * 3, tieu_de: 'Clip thu ' + i, ly_do: 'link chết'})))""")
        pg.wait_for_timeout(300)
        d = pg.evaluate("""() => {
            const g = s => document.querySelector(s)
            const hop = g('#of-xk .hopc')
            return {hien: g('#of-xk').classList.contains('show'),
                    dong: document.querySelectorAll('#of-xk-ds .it').length,
                    them: (g('#of-xk-ds .them') || {}).textContent || '',
                    vien: getComputedStyle(hop).borderColor,
                    cao: Math.round(g('#of-xk-ds').getBoundingClientRect().height),
                    cuon: g('#of-xk-ds').scrollHeight > g('#of-xk-ds').clientHeight,
                    nut: [...document.querySelectorAll('#of-xk .ft button')].map(x => x.textContent.trim())}
        }""")
        print("\n== (a) LINK CHET ==")
        print(f"  hien: {d['hien']} | dong: {d['dong']} (mockup 5) | «{d['them'].strip()}»")
        print(f"  vien hop: {d['vien']} | cao ds: {d['cao']}px (mockup <=190) | cuon duoc: {d['cuon']}")
        print(f"  nut: {d['nut']}")

        # ── (a) watermark: mau khac + CHI nut Dong ──
        pg.evaluate("""() => ofXkHong([{mieng: 4, tieu_de: 'Envato clip', ly_do: 'watermark'}])""")
        pg.wait_for_timeout(300)
        w = pg.evaluate("""() => ({
            vien: getComputedStyle(document.querySelector('#of-xk .hopc')).borderColor,
            nut: [...document.querySelectorAll('#of-xk .ft button')].map(x => x.textContent.trim()),
            caidat: document.querySelector('#of-xk').innerHTML.includes('Mở Cài đặt')})""")
        print("\n== (a) WATERMARK ==")
        print(f"  vien hop: {w['vien']} | nut: {w['nut']} | co nut 'Mo Cai dat': {w['caidat']}")

        # ── (b)+(c) xac nhan: nut KHOA toi khi tich ──
        pg.evaluate("""() => { window._DA = null; ofXkHoi(33, 'LI106', 'F:\\NAS\\Drafts',
                                                          noi => { window._DA = noi }) }""")
        pg.wait_for_timeout(300)
        t1 = pg.evaluate("""() => ({khoa: document.getElementById('of-xk-di').disabled,
            noi: document.getElementById('of-xk-noi').value,
            cochon: !!document.getElementById('of-xk-tat'),
            tat: document.querySelector('#of-xk').innerHTML.includes('Tắt CapCut'),
            ghide: document.querySelector('#of-xk').innerHTML.includes('ghi đè'),
            chon_tm: document.querySelector('#of-xk').innerHTML.includes('Chọn')})""")
        print("\n== (b)+(c) XAC NHAN ==")
        print(f"  nut Xuat KHOA khi chua tich: {t1['khoa']} (phai True)")
        print(f"  o noi xuat: «{t1['noi']}» | co o tich: {t1['cochon']}")
        print(f"  noi 'Tat CapCut': {t1['tat']} | noi 'ghi de': {t1['ghide']} | co nut Chon thu muc: {t1['chon_tm']}")

        pg.check("#of-xk-tat"); pg.wait_for_timeout(200)
        t2 = pg.evaluate("() => document.getElementById('of-xk-di').disabled")
        print(f"  sau khi tich -> khoa: {t2} (phai False)")
        pg.fill("#of-xk-noi", "Z:/moi/cho"); pg.click("#of-xk-di"); pg.wait_for_timeout(300)
        t3 = pg.evaluate("() => ({da: window._DA, con_hien: document.getElementById('of-xk').classList.contains('show')})")
        print(f"  bam Xuat -> callback nhan: «{t3['da']}» | hop da dong: {not t3['con_hien']}")

        pg.evaluate("""() => ofXkHong([{mieng: 2, tieu_de: 'x', ly_do: 'link chết'}])""")
        pg.wait_for_timeout(200)
        pg.screenshot(path="F:/RenderY_v2/scratchpad/thu_popup.png")
        print("\nanh: scratchpad/thu_popup.png")
        if loi: print("\n!! LOI JS:", loi[:4])
        b.close()
        return 0 if not loi else 1

sys.exit(main())
