# pinterest-kit/sites.py
# Pinterest 投稿の対象サイト定義。ここ1箇所を直せば全スクリプトに反映される。
#
# 仕様の正本: Obsidian「Projects/アフィリエイト/Pinterest運用仕様.md」
# weekly は §6-2「我々の配分（週25本＝1日3〜4本）」の値。変えるときは仕様書も直す。
#
# hashtag_sets / taglines は §11-5 案A・案D の対応（2026-08-07）。
#   hashtag_sets: バリアント v1/v2/v3 で別のタグを使う。フレッシュ判定③「前のピンから
#     テキストをコピーしていない」を満たすため、同一記事の3本でタグまで変える。
#   taglines: フッタ帯は全ピンで100%一致していた（実測）ので回して固定率を下げる。ただし商品型は
#     バリアントの切り口（v1 選び方 / v2 価格帯 / v3 用途別）と対応させる——footer の文言が
#     ピンの中身とズレると §5-1 の「画像と文言の一致」に反しミックスシグナルになるため。
# どちらも未定義なら hashtags / tagline にフォールバックする。

# 2026-08-12: GitHub Actions（rakuten-affiliate-blog の日次ジョブ）から呼べるようにするため、
# 記事の在りかと出力先を環境変数で差せるようにした。既定値は従来のローカルパスなので、
# 環境変数を設定しなければ手元の挙動は一切変わらない。
#   PINKIT_CC             … 全リポジトリの親ディレクトリ（既定: ~/Documents/Claude Code）
#   PINKIT_ARTICLES_<KEY> … サイト個別の記事ディレクトリ（例 PINKIT_ARTICLES_PICKNAVI）
#   PINKIT_OUT            … 出力ルート（既定: pinterest-kit/out）
# CI では対象リポジトリ1つしかチェックアウトされないので、他サイトは記事ディレクトリが
# 存在せず gen_* 側が [SKIP] する＝単一サイト実行がそのまま成立する。

import os
from pathlib import Path

CC = Path(os.environ.get("PINKIT_CC") or "/Users/hiroshi/Documents/Claude Code")

OUT = Path(os.environ.get("PINKIT_OUT") or (Path(__file__).resolve().parent / "out"))

SITES = {
    "picknavi": {
        "name": "picknavi",
        "url": "https://picknavi.net",
        "articles": CC / "rakuten-affiliate-blog" / "content" / "articles",
        "brand": (255, 107, 53),
        "brand2": (255, 154, 90),
        "tagline": "写真・価格・レビューで比較",
        "hashtags": ["#おすすめ", "#比較", "#買ってよかった"],
        "hashtag_sets": [
            ["#おすすめ", "#比較", "#買ってよかった"],
            ["#プチプラ", "#価格比較", "#お買い物メモ"],
            ["#用途別", "#選び方", "#暮らしの道具"],
        ],
        "taglines": ["写真・価格・レビューで比較", "価格帯から選べる比較記事", "用途から選べる比較記事"],
        # 2026-08-07: 1日2投稿へ変更（週14本）。
        # 注意: 記事の供給は DAILY_NEW_LIMIT=1（rakuten-affiliate-blog/scripts/config.py）＝週7本しかない。
        # 在庫38本を食い切ると供給不足になるので、1記事あたり複数バリエーションのピンが要る（仕様書 §6-4）。
        "weekly": 14,
        # 投稿文テキストに X の手動投稿文も併記する（退役した rakuten-affiliate-blog 側
        # スクリプトが出していた成果物を減らさないため）。X への自動投稿は別系統（post_to_x.py）。
        "x_template": "{tag}{title}\n楽天で売れている商品を写真・価格・レビューで比較👇\n{url}\n{hashtags}",
        # 記事に商品画像があるので商品カード型のピンを作る
        "pin_style": "product",
        # カテゴリ制限なし（全記事が対象）
        "only_categories": None,
    },
    "gagetnavi": {
        "name": "ガジェナビ",
        "url": "https://gagetnavi.net",
        "articles": CC / "gadget-affiliate-blog" / "content" / "articles",
        "brand": (37, 99, 235),
        "brand2": (96, 165, 250),
        "tagline": "スペックと価格で選ぶ",
        "hashtags": ["#ガジェット", "#デスク環境", "#買ってよかった"],
        "hashtag_sets": [
            ["#ガジェット", "#デスク環境", "#買ってよかった"],
            ["#デスクツアー", "#価格比較", "#作業環境"],
            ["#スマートホーム", "#選び方", "#家電レビュー"],
        ],
        "taglines": ["スペックと価格で選ぶ", "価格帯から選べる比較記事", "用途から選べる比較記事"],
        "weekly": 2,
        "pin_style": "product",
        # 仕様書 §4: 男性寄りジャンルは属性が合わない。
        # 「デスクツアー」文脈で女性層にも届くカテゴリだけに絞る。
        "only_categories": ["pc-peripheral", "smart-home", "home-gadget", "wearable"],
    },
    "codenavi": {
        "name": "コドナビ",
        "url": "https://code-navi.net",
        "articles": CC / "school-affiliate-blog" / "content" / "articles",
        "brand": (13, 148, 136),
        "brand2": (45, 212, 191),
        "tagline": "スクール・転職・資格を比較",
        "hashtags": ["#スキルアップ", "#転職活動", "#学び直し"],
        "taglines": ["スクール・転職・資格を比較", "費用と期間で比べる"],
        "weekly": 3,
        "pin_style": "text",
        "only_categories": None,
    },
    "shikakunavi": {
        "name": "シカクナビ",
        "url": "https://aech22.github.io/shikaku-affiliate-blog",
        "articles": CC / "shikaku-affiliate-blog" / "content" / "articles",
        "brand": (147, 51, 234),
        "brand2": (192, 132, 252),
        "tagline": "資格の講座を費用と特徴で比較",
        "hashtags": ["#資格勉強", "#勉強垢", "#学び直し"],
        "taglines": ["資格の講座を費用と特徴で比較", "費用と学習期間で比べる"],
        "weekly": 3,
        "pin_style": "text",
        "only_categories": None,
    },
    "toushinavi": {
        "name": "トウシナビ",
        "url": "https://aech22.github.io/invest-affiliate-blog",
        "articles": CC / "invest-affiliate-blog" / "content" / "articles",
        "brand": (22, 163, 74),
        "brand2": (74, 222, 128),
        "tagline": "投資が学べるスクールを比較",
        "hashtags": ["#投資の勉強", "#資産形成", "#家計管理"],
        "taglines": ["投資が学べるスクールを比較", "学べる内容と費用で比べる"],
        "weekly": 2,
        "pin_style": "text",
        "only_categories": None,
        # YMYL: 断定的な利益表現を書かないための注意書き（CSV に列として出す）
        "ymyl_note": "元本割れの可能性があります。特定の投資を推奨するものではありません。",
    },
    "shifty": {
        "name": "Shifty",
        "url": "https://shiftyshifty.app",
        # Shifty は Astro の記事コレクションを持たないので、下の SHIFTY_TOPICS を使う。
        # Shifty リポジトリには一切書き込まない（依頼なしの変更を避けるため）。
        "articles": None,
        "brand": (248, 112, 54),
        "brand2": (255, 168, 120),
        "tagline": "飲食店のシフト管理アプリ",
        "hashtags": ["#飲食店", "#シフト管理", "#店舗運営"],
        "taglines": ["飲食店のシフト管理アプリ", "URLを配るだけのシフト収集"],
        "weekly": 1,
        "pin_style": "text",
        "only_categories": None,
    },
}

# サイト個別の記事ディレクトリを環境変数で上書きする（CI 用）。
# 例: PINKIT_ARTICLES_PICKNAVI=$GITHUB_WORKSPACE/content/articles
for _key, _site in SITES.items():
    _override = os.environ.get(f"PINKIT_ARTICLES_{_key.upper()}")
    if _override:
        _site["articles"] = Path(_override)

# Shifty のピン題材。記事が無いので実務の課題ベースで用意する。
# 仕様書 §4 のとおり Pinterest との相性は低い想定。3ヶ月（〜2026-11-05）で流入ゼロなら停止する。
SHIFTY_TOPICS = [
    {
        "slug": "shifty_01_line_excel",
        "title": "シフト希望の集計、LINEとExcelの往復をやめる方法",
        "description": "スタッフから届く希望シフトをLINEで集めてExcelに手入力していると、転記ミスと「言った言わない」が必ず起きます。URLを配るだけで希望を集め、そのままシフト表にできる仕組みに変えると、この往復がまるごと消えます。",
        "category": "シフト管理",
        "path": "/",
    },
    {
        "slug": "shifty_02_jitan",
        "title": "シフト表の作成時間を毎月数時間減らす手順",
        "description": "シフト作成が終わらない原因の多くは「作る作業」ではなく「集める作業」にあります。希望の提出期限・提出状況・未提出者の把握を仕組み側に持たせると、実際に手を動かす時間だけが残ります。",
        "category": "業務効率化",
        "path": "/",
    },
    {
        "slug": "shifty_03_no_install",
        "title": "アプリのインストール不要でスタッフが希望シフトを出せる仕組み",
        "description": "スタッフにアプリを入れてもらう運用は、入れ替わりのある飲食店では続きません。URLを開くだけで提出でき、会員登録もインストールも要らない形にすると、新人が入った初日から使えます。",
        "category": "シフト管理",
        "path": "/",
    },
    {
        "slug": "shifty_04_muryou",
        "title": "無料で使えるシフト管理の始め方",
        "description": "有料ツールを導入する前に、まず「希望を集めてシフト表を出す」ところだけを無料で試すと、自店に必要な機能が具体的に分かります。スタッフ20名・期間1件までなら無料のまま運用できます。",
        "category": "シフト管理",
        "path": "/blog/shift-kanri-muryou.html",
    },
]
