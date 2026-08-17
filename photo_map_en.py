# pinterest-kit/photo_map_en.py
# 記事 → 使ってよい写真フォルダ の対応表と、写真ピン／データ図版ピンの配分方針。
#
# ★この表が「写真と記事が食い違わない」ことの担保。フォルダを細分化するほど精度が上がる。
#   フォルダ名は assets_en/thejapandesk/ 配下の**パス接頭辞**として解決され、再帰的に拾う。
#   つまり `kyoto` と書けば `kyoto/` 以下すべて、`kyoto/autumn` と書けばその小分けだけ、が対象になる。
#   → 季節や被写体で分けたくなったら、**コードを触らずフォルダを切るだけでよい。**
#
# ⚠️ 対応表に無い記事、または対応フォルダに未使用の写真が1枚も無い記事は、
#    生成時に [要写真] として名指しで警告される。黙って別の写真が使われることはない。

# データ図版で固定するピラー。語学は「机・ノート・勉強風景」の写真在庫が薄く、
# また比較記事は数字を出したほうが刺さるため、写真ベースに載せない（2026-08-08 決定）。
DATA_ONLY_PILLARS = {"learn-japanese"}

# 語学以外のピンのうち、写真ベースにする割合。残りは C型（情報図版）。
# 1.0 にすると全部写真、0.0 にすると全部データ図版になる。
PHOTO_SHARE = 0.8

# 記事slug → 写真フォルダ（優先順）。上から順に未使用の写真を探す。
ARTICLE_PHOTOS = {
    # --- 旅程
    "7-day-japan-itinerary":        ["tokyo", "kyoto", "osaka"],
    "2-week-japan-itinerary":       ["kyoto", "kanazawa-hokuriku", "hiroshima-setouchi", "tokyo"],
    "1-month-japan-itinerary":      ["hokkaido", "kyushu", "hiroshima-setouchi", "kyoto", "tokyo"],
    "2-months-in-japan-long-stay":  ["street-night", "tokyo", "osaka"],
    # --- 実務
    "is-jr-pass-worth-it-2026":     ["train-shinkansen", "station-ic"],
    "suica-pasmo-icoca-guide":      ["station-ic", "street-night"],
    "best-esim-for-japan":          ["street-night", "tokyo"],
    "japan-packing-list":           ["station-ic", "street-night"],
    "cheapest-time-to-fly-to-japan": ["tokyo", "street-night"],
    "best-klook-tours-tokyo":       ["tokyo", "temple-shrine", "street-night"],
    "japan-souvenirs-worth-buying": ["kyoto", "kanazawa-hokuriku"],
    # --- 体験・自然
    "japanese-culture-experiences-worth-booking": ["temple-shrine", "kyoto", "osaka"],
    "japan-highway-bus-and-ferry-guide":          ["hakone-fuji", "kanazawa-hokuriku", "hokkaido", "kyushu"],
    # ★季節が主題の記事は**季節サブフォルダだけ**を指す。
    #   在庫が無ければ [要写真] で警告が出る。夏の写真が黙って紅葉記事に入るのを防ぐため、
    #   親フォルダ（temple-shrine 等）へのフォールバックは意図的に書いていない。
    "japan-autumn-foliage-guide": ["temple-shrine/autumn", "kyoto/autumn", "hakone-fuji/autumn"],
    # 温泉記事は季節が主題ではないので通年の宿・温泉街の写真でよい
    "japan-onsen-towns-worth-the-detour": ["ryokan-onsen", "street-night", "kyushu"],
    # --- 工芸（craft・現在draft）。再開したときにそのまま効くよう先に書いておく
    "arita-vs-mino-vs-hasami":            ["kyushu"],
    "japanese-dinnerware-sets":           ["kyoto"],
    "edo-kiriko-whiskey-glasses":         ["tokyo"],
    "best-japanese-chef-knives-beginners": ["kyoto"],
    "gyuto-vs-santoku":                   ["kyoto"],
    "best-japanese-fountain-pens":        ["tokyo"],
    "best-japanese-bonsai-starter-kits":  ["temple-shrine"],
}

# まだ在庫が無く、写真を足すと効く場所。生成時の警告と突き合わせて撮影・書き出しの優先順位にする。
WANTED_FOLDERS = {
    "train-shinkansen": "新幹線・在来線の車内と車窓。JRパス記事の主役",
    "food": "食事。旅程記事の見せ場になるが1枚も無い",
    "study-desk": "机・ノート・カフェでの勉強。語学ピラー用（現状はデータ図版で固定中）",
    "airport": "空港ターミナル・搭乗口。航空券記事に対応するフォルダが無い",
    "craft-shop": "工芸品店・市場・土産物。お土産記事と工芸ピラーに対応するフォルダが無い",
}


def folders_for(slug: str) -> list[str]:
    return ARTICLE_PHOTOS.get(slug, [])
