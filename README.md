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

## CI から呼ぶ（picknavi・2026-08-12〜）

picknavi は **rakuten-affiliate-blog の日次ワークフローがこのリポジトリを clone して実行する**。
記事が毎日 bot に追加・更新されるため、手元での再生成では追随できないため。

```yaml
env:
  PINKIT_OUT:               ${{ github.workspace }}/social
  PINKIT_ARTICLES_PICKNAVI: ${{ github.workspace }}/content/articles
run: |
  git clone --depth 1 -q https://github.com/aech22/pinterest-kit.git "$RUNNER_TEMP/pinterest-kit"
  python "$RUNNER_TEMP/pinterest-kit/gen_pins.py" --site picknavi
  python "$RUNNER_TEMP/pinterest-kit/gen_social_kit.py" --site picknavi --no-calendar
```

| 環境変数 | 用途 | 既定 |
|---|---|---|
| `PINKIT_CC` | 全リポジトリの親ディレクトリ | `~/Documents/Claude Code` |
| `PINKIT_ARTICLES_<KEY>` | サイト個別の記事ディレクトリ | `sites.py` の値 |
| `PINKIT_OUT` | 出力ルート | `pinterest-kit/out` |

- CI では対象リポジトリ1つしかチェックアウトされないが、記事ディレクトリの無いサイトは
  `[SKIP]` されるので単一サイト実行がそのまま成立する
- `--no-calendar` を付ける。投稿カレンダーは**全サイト横断**の週次配分表なので、
  1サイトしか見えない CI で書くと偏った表になる
- **重複台帳は CI では持ち回さない。** 毎回すべての記事を生成し直すので「別ファイル名で同一バイト」
  の検出はその1回の実行の中で完結する（台帳は実行中メモリ上に全ピンぶん積まれる）
- **他5サイト＋Shifty は従来どおり手元で全サイト実行する**（カレンダーもそこで作る）

## 出力

```
out/
├── 投稿カレンダー.csv        ← 週次配分どおりに並べた投稿順（第N週・曜日目・投稿時刻つき）
├── picknavi/
│   ├── social_kit.csv        ← ピンタイトル・説明文・推奨ボード・画像ファイル名
│   ├── pins_ledger.json      ← 出力済みピンの SHA-256 台帳（案C・重複アップロードの防止）
│   └── pins/*_v{1,2}.jpg     ← 1000×1500 のピン画像（**1記事1枚**。_v2 は商品2点の記事だけ）
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
| `variants.py` | 1記事から作るピンの本数とレイアウト（写真1枚 / 2枚）の判定。**画像と文言をズラさないため gen_pins.py と gen_social_kit.py の両方が参照する** |
| `gen_en_kit.py` | The Japan Desk（英語）専用。写真ピン＋データ図版を作る。設定は `sites_en.py` |
| `photo_map_en.py` | **記事 → 使ってよい写真フォルダ**の対応表と、写真8割／C型2割の配分。語学はデータ図版で固定 |
| `photos_en.py` | 写真の在庫管理と使用済み台帳（`state_en/used_photos.json`）。中身のハッシュで二重使用を防ぐ |
| `render_en.py` | 英語ピンの描画（A型・C型・写真型） |
| `sync_drive_en.py` | The Japan Desk の生成物をマウント済み Google Drive へ反映する。`gen_en_kit.py` の最後から自動で走る。**既存ファイルは上書きも削除もせず、新しいぶんだけ足す**（`SKIP_DRIVE_SYNC=1` で抑止・`TJD_DRIVE_DIR` で宛先変更） |
| `assets_en/thejapandesk/` | 写真の置き場。フォルダを細分化すると記事との対応精度が上がる（README参照） |

## 設計の要点

- **事実は記事データから取り、創作しない。** 説明文は記事の `description` / `services[].target` / `services[].highlight` / `products[].name` から組み立てる（アフィリサイト全体の「事実とLLM生成物を分離する」方針に合わせている）
- **1記事につき1ピン**（2026-08-18〜）。写真の枚数だけを記事の形に合わせる——**まとめ記事（商品3点以上）は写真1枚、2種比較（商品ちょうど2点）は写真2枚**。判定は `variants.py` の `layouts_for()` が持ち、商品点数だけを見る（タイトルの「比較」等では判別できない。まとめ記事のタイトルにも入るため）。タイトルと説明文は記事のものをそのまま使う
- それ以前は §11-5 案A に従って1記事3ピン（v1 選び方 / v2 価格帯 / v3 用途別）を出し、切り口ごとに文言まで作り直していた。**3本に戻すなら `layouts_for()` を直すだけでよい**（3枚のモザイク描画は `gen_pins.py` に残してある）
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
