"""Apply canonical Chinese renderings of proper names across translation files.

Usage: python3 harmonize.py NN [NN ...]
Plain string replacement (variant -> canonical) over the whole file, then the caller re-validates.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from paths import *  # noqa: E402,F401,F403

CANON = {
    "德瑞帕努姆": "德雷帕努姆",
    "戈尔贡": "戈耳工",
    "利泰尔努姆": "利特尔努姆",
    "利特努姆": "利特尔努姆",
    "卢克蕾提娅": "卢克莱提娅",
    "美杜莎": "墨杜萨",
    "麦罗埃": "墨罗埃",
    "梅曾提乌斯": "墨赞提乌斯",
    "弥诺斯": "米诺斯",
    "波吕丢刻斯": "波卢克斯",
    "萨莫奈": "萨谟奈",
    "苏维托尼乌斯": "苏埃托尼乌斯",
    "希凯斯": "叙凯斯",
    "塔尔索斯": "塔尔苏斯",
    "伊俄": "伊娥",
    "克桑提波斯": "克桑提普斯",
    "卡利俄珀": "卡利俄佩",
    "利利拜乌姆": "利利巴厄姆",
    "安奇塞斯": "安喀塞斯",
    "贝罗娜": "贝洛娜",
    "欧里波斯": "欧里浦斯",
    "马克西姆斯": "马克西穆斯",
    "萨卢斯特": "撒路斯提乌斯",
    "图内塔": "突尼斯",
}

if __name__ == "__main__":
    for nn in sys.argv[1:]:
        p = TRANSLATION / f"{nn}.txt"
        t = p.read_text(encoding="utf-8")
        counts = {}
        for a, b in CANON.items():
            c = t.count(a)
            if c:
                t = t.replace(a, b)
                counts[a] = c
        p.write_text(t, encoding="utf-8")
        print(nn, counts)
