"""Lấy số liệu và toàn bộ bình luận video YouTube qua YouTube Data API v3.

py -3 cong-cu/lay_binh_luan.py <link|mã> [<link|mã> ...] [--ra <thư mục>] [--toi-da <số bình luận gốc>]

Key: file trong YT_KEYS_FILE của .env, mỗi dòng một key; hết hạn mức hay key lỗi thì xoay key kế. Không in key.
Ra mỗi video: <mã>.json (số liệu + bình luận đủ trường) và <mã>.txt (gọn, xếp theo lượt thích).
Mặc định ra ./binh-luan/. Chi phí: 1 đơn vị mỗi 100 bình luận gốc.
"""
import argparse, json, os, re, sys, urllib.error, urllib.parse, urllib.request

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://www.googleapis.com/youtube/v3/"


def doc_key():
    duong = None
    for dong in open(os.path.join(GOC, ".env"), encoding="utf-8"):
        if dong.startswith("YT_KEYS_FILE="):
            duong = dong.split("=", 1)[1].strip().strip('"')
    if not duong or not os.path.exists(duong):
        sys.exit("LỖI: không thấy file key (YT_KEYS_FILE trong .env)")
    keys = list(dict.fromkeys(re.findall(r"AIza[0-9A-Za-z_-]{35}", open(duong, encoding="utf-8").read())))
    if not keys:
        sys.exit("LỖI: file key không có key nào")
    return keys


class Goi:
    def __init__(self, keys):
        self.keys, self.i = keys, 0

    def __call__(self, ten, **ts):
        while self.i < len(self.keys):
            url = API + ten + "?" + urllib.parse.urlencode({**ts, "key": self.keys[self.i]})
            try:
                return json.load(urllib.request.urlopen(url, timeout=60))
            except urllib.error.HTTPError as e:
                try:
                    ly_do = json.load(e)["error"]["errors"][0]["reason"]
                except Exception:
                    ly_do = ""
                if e.code == 403 and ly_do == "commentsDisabled":
                    return None
                if e.code in (400, 403) and ly_do in ("quotaExceeded", "forbidden", "keyInvalid", "accessNotConfigured", "dailyLimitExceeded", "badRequest"):
                    self.i += 1
                    continue
                raise SystemExit(f"LỖI {e.code} {ly_do} khi gọi {ten}")
        sys.exit("LỖI: mọi key đều hết hạn mức hoặc lỗi")


def ma_video(s):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([0-9A-Za-z_-]{11})", s)
    return m.group(1) if m else s.strip()


def lay(goi, vid, toi_da):
    v = goi("videos", part="snippet,statistics,contentDetails", id=vid)
    if not v or not v.get("items"):
        print(vid, "LỖI không thấy video")
        return None
    it = v["items"][0]
    bl, trang = [], None
    while True:
        ts = {"part": "snippet,replies", "videoId": vid, "maxResults": 100, "order": "relevance", "textFormat": "plainText"}
        if trang:
            ts["pageToken"] = trang
        d = goi("commentThreads", **ts)
        if d is None:
            break
        for t in d.get("items", []):
            g = t["snippet"]["topLevelComment"]["snippet"]
            bl.append({"tac_gia": g["authorDisplayName"], "chu": g["textDisplay"], "thich": g.get("likeCount", 0),
                       "ngay": g["publishedAt"], "so_tra_loi": t["snippet"].get("totalReplyCount", 0),
                       "tra_loi": [{"tac_gia": r["snippet"]["authorDisplayName"], "chu": r["snippet"]["textDisplay"],
                                    "thich": r["snippet"].get("likeCount", 0)} for r in t.get("replies", {}).get("comments", [])]})
            if bl[-1]["so_tra_loi"] > len(bl[-1]["tra_loi"]):
                bl[-1]["tra_loi"], tr = [], None
                while True:
                    ts2 = {"part": "snippet", "parentId": t["id"], "maxResults": 100, "textFormat": "plainText"}
                    if tr:
                        ts2["pageToken"] = tr
                    r = goi("comments", **ts2) or {}
                    bl[-1]["tra_loi"] += [{"tac_gia": c["snippet"]["authorDisplayName"], "chu": c["snippet"]["textDisplay"],
                                           "thich": c["snippet"].get("likeCount", 0)} for c in r.get("items", [])]
                    tr = r.get("nextPageToken")
                    if not tr:
                        break
        trang = d.get("nextPageToken")
        if not trang or (toi_da and len(bl) >= toi_da):
            break
    return {"ma": vid, "tieu_de": it["snippet"]["title"], "kenh": it["snippet"]["channelTitle"],
            "ngay_dang": it["snippet"]["publishedAt"], "thoi_luong": it["contentDetails"]["duration"],
            "so_lieu": it["statistics"], "mo_ta": it["snippet"].get("description", ""),
            "tag": it["snippet"].get("tags", []), "binh_luan": bl}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video", nargs="+")
    p.add_argument("--ra", default="binh-luan")
    p.add_argument("--toi-da", type=int, default=0)
    a = p.parse_args()
    os.makedirs(a.ra, exist_ok=True)
    goi = Goi(doc_key())
    for s in a.video:
        vid = ma_video(s)
        kq = lay(goi, vid, a.toi_da)
        if not kq:
            continue
        json.dump(kq, open(os.path.join(a.ra, vid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        sl = kq["so_lieu"]
        with open(os.path.join(a.ra, vid + ".txt"), "w", encoding="utf-8") as f:
            f.write(f"# {kq['tieu_de']} | {kq['kenh']} | {kq['ngay_dang'][:10]} | view {sl.get('viewCount')} like {sl.get('likeCount')} bl {sl.get('commentCount')}\n")
            for b in sorted(kq["binh_luan"], key=lambda x: -x["thich"]):
                f.write(f"[{b['thich']}] {b['tac_gia']}: {' '.join(b['chu'].split())[:400]}\n")
                for r in b["tra_loi"]:
                    f.write(f"  ↳[{r['thich']}] {r['tac_gia']}: {' '.join(r['chu'].split())[:300]}\n")
        so_tl = sum(len(b["tra_loi"]) for b in kq["binh_luan"])
        print(f"{vid}: {len(kq['binh_luan'])} gốc + {so_tl} trả lời / {sl.get('commentCount')} | view {sl.get('viewCount')} | {kq['tieu_de'][:60]}")


if __name__ == "__main__":
    main()
