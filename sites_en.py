# pinterest-kit/sites_en.py
# 英語圏サイト（The Japan Desk）の Pinterest 設定。
#
# ★日本語5サイト（sites.py）とは Pinterest アカウントも Drive フォルダも別系統。
#   混ぜないこと。ボード・ハッシュタグ・投稿文はすべて英語。
#
# 仕様の共通部分（画像1000×1500・タイトル100字・説明文800字・重複ピン禁止）は
# Obsidian「Projects/アフィリエイト/Pinterest運用仕様.md」に従う。
# 頻度だけはこのサイト固有の事情（新規アカウント＋新規ドメイン）で別に決めている。

from pathlib import Path

CC = Path("/Users/hiroshi/Documents/Claude Code")

EN_SITES = {
    "thejapandesk": {
        "name": "The Japan Desk",
        "url": "https://thejapandesk.net",
        "articles": CC / "thejapandesk" / "content" / "articles",
        # 実サイトの配色（src/styles/global.css）に合わせる: 藍 #2d4a6b / 朱 #c8402f
        "brand": (45, 74, 107),
        "brand2": (90, 125, 165),
        "accent": (200, 64, 47),
        "tagline": "Authentic Japan, explained from the inside.",
        # 2026-08-07 に 2本/日（週14本）へ。C型（情報図版）を1本目、A型（活字）を2本目に置く。
        # 新規アカウント＋新規ドメインでこの本数はスパムフィルタ上は攻めた設定なので、
        # 初月はリーチの落ち込みを見て、鈍ったら 1本/日 へ戻すこと。
        "per_day": 2,
        "weekly": 14,
        "pin_style": "c+a",
    },
}

# pillar → ボード名とハッシュタグ。ボードは Pinterest 側で先に作っておく。
PILLARS = {
    "craft": {
        "board": "Japanese Craft & Goods",
        "label": "Japanese Craft",
        "hashtags": ["#JapaneseCraft", "#MadeInJapan", "#JapaneseDesign"],
    },
    "learn-japanese": {
        "board": "Learning Japanese",
        "label": "Learn Japanese",
        "hashtags": ["#LearnJapanese", "#JapaneseLanguage", "#StudyJapanese"],
    },
    "japan-travel": {
        "board": "Japan Travel",
        "label": "Japan Travel",
        "hashtags": ["#JapanTravel", "#JapanTrip", "#TravelJapan"],
    },
    # 2026-08-07 追加。山・川・渓谷・温泉・紅葉など自然系。
    # 旅行(japan-travel)から分けたのは、Pinterest 側のキーワードが「行き方・パス・予算」ではなく
    # 「景色・時期・アクセス」で、同じボードに混ぜるとどちらのテーマ権威も濁るため（仕様 §5-4）。
    # ★記事はまだ0本。1本入るまでこのボードのピンは生成されない（Pinterest 側でも先に作らないこと）。
    "japan-nature": {
        "board": "Japan Nature & Outdoors",
        "label": "Japan Nature",
        "hashtags": ["#JapanNature", "#JapanOutdoors", "#JapanHiking"],
    },
}

# 投稿時刻。日本語側と同じく米国データ由来だが、こちらは読者が実際に英語圏（US/UK/AU/CA）
# なので、米国東部の夕方〜夜に当たる時刻をJSTに直して使う。運用後に実測で上書きすること。
POST_TIMES_JST = ["09:00", "11:00", "22:00"]
