r"""TAG 7 TRỤC tầng 1 — bóc từ TIÊU ĐỀ, miễn phí, chạy cho MỌI clip khi hút.

Khung 7 trục (chốt 06/09): subject·action·setting·geo·people·shot·mood.
Tầng này heuristic (từ điển + luật) — đủ cho FTS + lọc nguồn/neo; tầng 2
vision-tag (đắt) chỉ chạy cho clip lọt vào khay/được chốt (đợt sau).
Chuẩn hóa: tiếng Anh, lowercase, danh từ số ít khi bóc được.
"""

from __future__ import annotations

import re

# geo 3 cấp: từ khóa -> (cấp1, cấp2, cấp3) — mở rộng dần theo niche
_GEO = {
    "ecuador": ("ecuador", "", ""), "ecuadorian": ("ecuador", "", ""),
    "quito": ("ecuador", "andes", "quito"), "cuenca": ("ecuador", "andes", "cuenca"),
    "otavalo": ("ecuador", "andes", "otavalo"), "banos": ("ecuador", "andes", "banos"),
    "guayaquil": ("ecuador", "coast", "guayaquil"),
    "galapagos": ("ecuador", "coast", "galapagos"),
    "cotopaxi": ("ecuador", "andes", "cotopaxi"),
    "chimborazo": ("ecuador", "andes", "chimborazo"),
    "andes": ("ecuador", "andes", ""), "andean": ("ecuador", "andes", ""),
    "amazon": ("ecuador", "amazon", ""),
    "latin america": ("latin america", "", ""), "south america": ("south america", "", ""),
    "peru": ("peru", "", ""), "colombia": ("colombia", "", ""),
    "usa": ("usa", "", ""), "america": ("usa", "", ""), "american": ("usa", "", ""),
}
# THẾ GIỚI (07/09): từ điển cũ chỉ 19 mục toàn Ecuador — di sản ngách đầu tiên.
# Hệ quả đo được: tiêu đề ghi thẳng "Kabul street market Afghanistan" vẫn ra geo
# RỖNG, mà luật rào cho geo rỗng đi qua như trung tính -> núi Bolivia và ruộng
# bậc thang Inca chảy vào tập Afghanistan. Thêm nước + thành phố lớn để tiêu đề
# nào có nhắc địa danh thì đọc ra được; không nhắc thì vẫn rỗng, KHÔNG bịa.
for _n in ("afghanistan pakistan india nepal bhutan bangladesh srilanka china japan korea "
           "vietnam thailand laos cambodia myanmar burma indonesia malaysia singapore "
           "philippines mongolia kazakhstan uzbekistan iran iraq syria turkey lebanon "
           "jordan israel palestine yemen oman qatar kuwait bahrain egypt libya tunisia "
           "algeria morocco sudan ethiopia kenya tanzania uganda rwanda nigeria ghana "
           "senegal somalia congo angola zambia zimbabwe botswana namibia mozambique "
           "madagascar russia ukraine poland germany france spain portugal italy greece "
           "albania serbia croatia romania bulgaria hungary austria switzerland belgium "
           "netherlands denmark sweden norway finland iceland ireland scotland wales "
           "england britain canada guatemala honduras nicaragua panama venezuela bolivia "
           "chile argentina uruguay paraguay brazil cuba jamaica haiti australia fiji "
           "tibet").split():
    _GEO.setdefault(_n, (_n, "", ""))
for _tp, _nuoc in {"kabul": "afghanistan", "kandahar": "afghanistan",
                   "herat": "afghanistan", "delhi": "india", "mumbai": "india",
                   "bombay": "india", "karachi": "pakistan", "lahore": "pakistan",
                   "beijing": "china", "shanghai": "china", "tokyo": "japan",
                   "kyoto": "japan", "seoul": "korea", "bangkok": "thailand",
                   "hanoi": "vietnam", "jakarta": "indonesia", "manila": "philippines",
                   "istanbul": "turkey", "tehran": "iran", "baghdad": "iraq",
                   "dubai": "emirates", "cairo": "egypt", "nairobi": "kenya",
                   "lagos": "nigeria", "moscow": "russia", "paris": "france",
                   "london": "england", "berlin": "germany", "rome": "italy",
                   "madrid": "spain", "lisbon": "portugal", "athens": "greece",
                   "vienna": "austria", "prague": "czech", "warsaw": "poland",
                   "toronto": "canada", "sydney": "australia",
                   "melbourne": "australia"}.items():
    _GEO.setdefault(_tp, (_nuoc, "", _tp))
for _v, _nuoc in {"himalaya": "nepal", "himalayas": "nepal", "hindu kush": "afghanistan",
                  "sahara": "africa", "alps": "switzerland"}.items():
    _GEO.setdefault(_v, (_nuoc, _v, ""))
_SETTING = ("market", "street", "kitchen", "home", "house", "village", "plaza",
            "square", "jungle", "rainforest", "mountain", "volcano", "beach",
            "coast", "city", "town", "road", "supermarket", "store", "shop",
            "office", "farm", "field", "river", "waterfall", "festival", "church")
_PEOPLE = ("woman", "man", "girl", "boy", "child", "children", "family",
           "vendor", "farmer", "worker", "crowd", "people", "indigenous",
           "tourist", "dancer", "fisherman", "seller")
_SHOT = {"aerial": "aerial", "drone": "aerial", "close-up": "close-up",
         "close up": "close-up", "closeup": "close-up", "wide": "wide",
         "panorama": "wide", "panoramic": "wide", "portrait": "close-up",
         "pov": "pov", "timelapse": "timelapse", "time lapse": "timelapse",
         "slow motion": "slow-motion", "macro": "close-up"}
_MOOD = ("sunset", "sunrise", "night", "morning", "golden hour", "rain",
         "fog", "mist", "storm", "sunny", "dramatic", "peaceful", "busy",
         "colorful", "dark", "vibrant")
_ACTION_DUOI = ("ing",)   # động từ -ing trong tiêu đề stock ("buying", "walking")
_BO = {"stock", "video", "footage", "view", "background", "shot", "scene",
       "the", "and", "with", "over", "from", "into", "onto", "near", "his",
       "her", "their", "this", "that"}


def tag_tu_tieu_de(tieu_de: str) -> dict:
    """Tiêu đề -> dict 7 trục (chuỗi, phẩy ngăn cách; thiếu = '')."""
    chu = (tieu_de or "").lower()
    tokens = re.findall(r"[a-z][a-z-]+", chu)

    geo = ""
    for tu, (c1, c2, c3) in _GEO.items():
        if tu in chu:
            moi = ">".join(x for x in (c1, c2, c3) if x)
            if len(moi) > len(geo):        # lấy cái CỤ THỂ nhất (quito > ecuador)
                geo = moi

    setting = ",".join(dict.fromkeys(t for t in tokens if t in _SETTING))
    people = ",".join(dict.fromkeys(t for t in tokens if t in _PEOPLE))
    shot = ",".join(dict.fromkeys(v for k, v in _SHOT.items() if k in chu))
    mood = ",".join(dict.fromkeys(m for m in _MOOD if m in chu))
    action = ",".join(dict.fromkeys(
        t for t in tokens
        if t.endswith(_ACTION_DUOI) and len(t) > 5 and t not in _BO))[:60]

    # subject = các danh từ "đắt" còn lại (không thuộc trục nào, không từ rác)
    da_dung = set((setting + "," + people + "," + action).split(",")) | _BO
    da_dung |= {t for t in tokens if any(t in k for k in _GEO)}
    subject = ",".join(dict.fromkeys(
        t for t in tokens if t not in da_dung and len(t) > 3))[:80]

    return {"subject": subject, "action": action, "setting": setting,
            "geo": geo, "people": people, "shot": shot, "mood": mood,
            "tag_nguon": "tieu_de"}
