# pinterest-kit

国内アフィリ5サイト＋Shifty の Pinterest 投稿文とピン画像を、**1箇所で**生成するツールキット。

各リポジトリにスクリプトを複製しない設計にしてある（picknavi の `gen_pins.py` を5箇所にコピーすると、仕様変更のたびに5箇所直すことになるため）。

**仕様の正本**: `/Users/hiroshi/Documents/Obsidian Vault/Projects/アフィリエイト/Pinterest運用仕様.md`
**共通ガイド**: `/Users/hiroshi/Documents/Obsidian Vault/Projects/アフィリエイト/AFFILIATE.md`

---

## 使い方

```bash
cd "/Users/hiroshi/Documents/Claude Code/pinterest-kit"
python3 gen_pins.py           # ピン画像 1000x1500（全サイト）
python3 gen_social_kit.py     # 投稿文CSV（全サイト）＋ 投稿カレンダー
```

**gen_pins.py を先に実行する。** gen_social_kit.py は実在するピン画像の行だけを CSV に出すため
（案C の重複台帳に弾かれた画像を CSV が参照しないようにする）。

1サイトだけ・少数だけ試すとき:

```bash
python3 gen_pins.py --site picknavi --limit 3
```

## 出力

```
out/
├── 投稿カレンダー.csv        ← 週次配分どおりに並べた投稿順（第N週・曜日目・投稿時刻つき）
├── picknavi/
│   ├── social_kit.csv        ← ピンタイトル・説明文・推奨ボード・画像ファイル名
│   ├── pins_ledger.json      ← 出力済みピンの SHA-256 台帳（案C・重複アップロードの防止）
│   └── pins/*_v{1,2,3}.jpg   ← 1000×1500 のピン画像（商品型は1記事3枚）
├── gagetnavi/ …
├── codenavi/ …
├── shikakunavi/ …
├── toushinavi/ …
└── shifty/ …
```

手動投稿するときは `social_kit.csv` からタイトル・説明文をコピペし、`pins/` の同名画像をアップロードする。

## ファイル

| ファイル | 役割 |
|---|---|
| `sites.py` | サイト定義（記事パス・ブランド色・URL・ハッシュタグ・週次本数・ピン形式）。**ここ1箇所を直せば全体に反映される** |
| `gen_social_kit.py` | 投稿文CSV＋投稿カレンダーの生成 |
| `gen_pins.py` | ピン画像の生成。生成後に 1000×1500・20MB以下を自己チェックする |
| `variants.py` | バリアント（v1 選び方 / v2 価格帯 / v3 用途別）の定義。**画像と文言をズラさないため gen_pins.py と gen_social_kit.py の両方が参照する** |
| `gen_en_kit.py` | The Japan Desk（英語）専用。写真ピン＋データ図版を作る。設定は `sites_en.py` |
| `photo_map_en.py` | **記事 → 使ってよい写真フォルダ**の対応表と、写真8割／C型2割の配分。語学はデータ図版で固定 |
| `photos_en.py` | 写真の在庫管理と使用済み台帳（`state_en/used_photos.json`）。中身のハッシュで二重使用を防ぐ |
| `render_en.py` | 英語ピンの描画（A型・C型・写真型） |
| `assets_en/thejapandesk/` | 写真の置き場。フォルダを細分化すると記事との対応精度が上がる（README参照） |

## 設計の要点

- **事実は記事データから取り、創作しない。** 説明文は記事の `description` / `services[].target` / `services[].highlight` / `products[].name` から組み立てる（アフィリサイト全体の「事実とLLM生成物を分離する」方針に合わせている）
- **商品型サイト（picknavi / ガジェナビ）は1記事から3ピンを出す**（仕様書 §6-4・§11-5 案A）。v1 選び方（商品1点・タイトル下）／ v2 価格帯（商品2点・タイトル上）／ v3 用途別（商品3点・モザイク）で、画像・タイトル・説明文・ハッシュタグをすべて作り直す。テキスト型サイトは v1 のみ
- **同一記事の3本は「全 v1 → 全 v2 → 全 v3」の順で並ぶ**ので、カレンダー上で自動的に在庫1周ぶん（picknavi なら2〜4週）離れる＝§6-4 の「1本ごとに1週間空ける」を人手で管理しなくてよい
- **価格の「円」表記をピン文面に出さない。** ピンの寿命は2〜3年ある一方で楽天の価格は毎日変わるため、数字を焼き付けると時間が経つほど嘘になる。変動しにくい `priceBand` ラベルだけを使う
- **ガジェナビはカテゴリを絞っている**（`only_categories`）。Pinterest の中心属性と合わないジャンルを外し、デスク周り・スマートホーム系だけを出す
- **トウシナビは YMYL**。`ymyl_note` が説明文の末尾に必ず入る
- **Shifty リポジトリには一切書き込まない。** 題材は `sites.py` の `SHIFTY_TOPICS` に持つ
- ピン画像は**日本語の禁則処理**（行頭に「、。ー」等を置かない）と**孤立行の解消**を実装済み

## 依存

`Pillow` / `PyYAML` / `requests`（いずれもローカル python に user install 済み）。

## 注意

- `out/` の画像・CSV は生成物なので消しても作り直せる。ただし **`pins_ledger.json` は消さないこと**——過去に出力したピンの SHA-256 台帳で、これが無いと重複アップロードを機械的に防げなくなる
- ピン画像を「フレッシュ」に保つ仕組みは案Cの台帳が担う。別のファイル名で同一バイトの画像が出ようとすると `[DUP]` を表示して書き込まない
- 台帳が `[DUP]` を出した記事はその回のピンが1枚減る。CSV も自動的にその行を落とすので、**CSV と `pins/` は常に一致する**
