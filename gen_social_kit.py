# pinterest-kit/gen_social_kit.py
# 全サイトの記事から Pinterest 投稿文を生成し、サイトごとの CSV と投稿カレンダーを書き出す。
#
# 仕様の正本: Obsidian「Projects/アフィリエイト/Pinterest運用仕様.md」
#   §5-2 タイトルは100字上限・フィードで見えるのは前半50〜60字 → キーワードを前半に置く
#   §5-3 説明文は800字上限・「結論の一文 → 誰向け → 分かること → ハッシュタグ3〜5個」
#   §6-2 サイト別の週次配分  §6-3 投稿時刻
#   §6-4 1記事につき最大3本。画像・タイトル・説明文をすべて作り直し、1本ごとに1週間空ける
#   §11-5 案A  2026-08-07 に商品型サイトを1記事3バリアント（v1 選び方 / v2 価格帯 / v3 用途別）へ
#         拡張した。同一記事の3本は「全 v1 → 全 v2 → 全 v3」の順に並べるので、カレンダー上で
#         自動的に在庫1周ぶん（picknavi なら約2.7週）離れる＝§6-4 の「1週間空ける」を満たす
#
# 実行: python3 gen_social_kit.py
# 出力: out/<site>/social_kit.csv, out/投稿カレンダー.csv

from __future__ import annotations
import argparse
import csv
import re
import sys
from pathlib import Path

import yaml

from sites import SITES, SHIFTY_TOPICS, OUT
# バリアント数とタイトルの規則は gen_pins.py と共有する（画像と文言をズラさないため）
from variants import PRODUCTS_NEEDED, title_head, variant_title, variants_for

TITLE_MAX = 100      # Pinterest のタイトル上限
TITLE_VISIBLE = 55   # フィードで見える目安（50〜60字）
DESC_MAX = 800       # Pinterest の説明文上限

# §6-3 投稿時刻。米国データ由来なので日本での最適値は未検証（暫定の優先順）。
# 4本目の 15:00 は picknavi を週14本に増やして 1日4本の日ができたときだけ使う。
POST_TIMES = ["21:00", "12:00", "18:00", "15:00"]
DAYS_PER_WEEK = 7


def read_frontmatter(path: Path) -> dict | None:
    try:
        parts = path.read_text(encoding="utf-8").split("---", 2)
        return yaml.safe_load(parts[1]) or {}
    except Exception:
        return None


def clip(s: str, n: int) -> str:
    """1行に潰して n 文字で切る（タイトル・単一段落用）。"""
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def clip_block(s: str, n: int) -> str:
    """改行を保ったまま n 文字で切る。説明文は段落構成そのものが読みやすさなので潰さない。"""
    s = str(s).strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def pin_title(raw_title: str) -> str:
    """タイトルは100字上限。前半55字にキーワードが入る前提で、頭は削らず末尾だけ落とす。"""
    return clip(raw_title, TITLE_MAX)


# 楽天の商品名の先頭に付く出品者の販促文（【楽天1位】＼81%OFF＆P2倍で2,174円！／ 等）を落とす。
# 画像に焼き込まれたバッジを避ける案E と同じ理由で、説明文にも持ち込まない。
# 価格を含む文字列はピンの寿命（2〜3年）に対して必ず陳腐化するので特に除く。
PROMO_PATTERNS = [
    re.compile(r"＼[^／]*／"),          # ＼81%OFF＆P2倍で2,174円！／
    re.compile(r"【[^】]*】"),          # 【楽天1位】【数量限定1380円→1000円】
    re.compile(r"^楽天(市場)?(ランキング)?\s*\d*\s*位"),
]


def clean_name(name: str) -> str:
    s = str(name)
    for pat in PROMO_PATTERNS:
        s = pat.sub("", s)
    s = s.split("|")[0].split("　")[0]
    return " ".join(s.split()).strip(" 　-–—/／、,")


def hashtags_for(site: dict, variant: int) -> list[str]:
    """バリアントごとに別のタグを使う（フレッシュ判定③・§2-3）。未定義なら共通タグ。"""
    sets = site.get("hashtag_sets")
    if not sets:
        return site["hashtags"]
    return sets[(variant - 1) % len(sets)]


def what_you_learn(fm: dict) -> list[str]:
    """記事から「この記事でわかること」を最大3点。事実は記事データから取り、創作しない。"""
    points: list[str] = []
    for s in (fm.get("services") or [])[:3]:
        hl = (s or {}).get("highlight")
        if hl:
            points.append(str(hl))
    if not points:
        for p in (fm.get("products") or [])[:3]:
            band = (p or {}).get("priceBand")
            name = (p or {}).get("name")
            if name:
                points.append(f"{clip(clean_name(name), 26)}{f'（{band}）' if band else ''}")
    return points


def pin_description(fm: dict, site: dict, variant: int = 1) -> str:
    """結論の一文 → 誰向け → 分かること → ハッシュタグ。キーワードの羅列はしない（§3-4）。
    v2・v3 は §11-5 案A の切り口に合わせて本文を丸ごと組み直す（v1 の文をコピーしない）。"""
    products = fm.get("products") or []
    head = title_head(str(fm.get("title") or ""))
    n = PRODUCTS_NEEDED.get(variant, 1)
    blocks: list[str] = []

    if variant == 2:
        blocks.append(f"「{head}」で取り上げた{n}製品を、価格帯で並べ直しました。")
        rows = []
        for p in products[:n]:
            if not p:
                continue
            band = p.get("priceBand")
            name = clip(clean_name(p.get("name") or ""), 30)
            rows.append(f"・{name}（{band}）" if band else f"・{name}")
        if rows:
            blocks.append("価格帯で見ると:\n" + "\n".join(rows))
    elif variant == 3:
        blocks.append(f"「{head}」の{n}製品を、どんな人に向くかで整理しました。")
        rows = [f"・{clip(clean_name(p.get('name') or ''), 22)}: {clip(p.get('target') or '', 55)}"
                for p in products[:n] if p and p.get("target")]
        if rows:
            blocks.append("用途から選ぶなら:\n" + "\n".join(rows))
    else:
        desc = (fm.get("description") or "").strip()
        if desc:
            blocks.append(clip(desc, 300))

        target = None
        for s in (fm.get("services") or []):
            if (s or {}).get("target"):
                target = str(s["target"]).strip()
                break
        if target:
            blocks.append(f"こんな人向け: {clip(target, 90)}")

        pts = what_you_learn(fm)
        if pts:
            blocks.append("この記事でわかること:\n" + "\n".join(f"・{p}" for p in pts))

    if site.get("ymyl_note"):
        blocks.append(site["ymyl_note"])

    blocks.append(" ".join(hashtags_for(site, variant)))
    return clip_block("\n\n".join(blocks), DESC_MAX)


def mmdd(fm: dict) -> str:
    """公開日(date)を MMDD に。投稿文ファイル名の先頭に付けて新着を見分けやすくする
    （退役した rakuten-affiliate-blog/scripts/gen_social_kit.py の命名を引き継ぐ）。"""
    d = fm.get("date")
    s = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d or "")
    parts = s.split("-")
    return f"{parts[1]}{parts[2]}" if len(parts) >= 3 else "0000"


def pins_index(site_key: str) -> set[str] | None:
    """生成済みピンのファイル名一覧。まだ1枚も無ければ None を返す。
    None のときは存在チェックをしない（gen_pins.py より先に実行された場合に全部消えないため）。
    ピンがあるときは、案C の台帳に弾かれて実在しない画像を CSV が参照しないよう突き合わせる
    ——CSV は人間が投稿するときの手順書なので、指す先が無い行を残してはいけない。"""
    d = OUT / site_key / "pins"
    files = {f.name for f in d.glob("*.jpg")} if d.is_dir() else set()
    return files or None


def collect(site_key: str, site: dict) -> list[dict]:
    rows: list[dict] = []
    have = pins_index(site_key)

    if site_key == "shifty":
        for t in SHIFTY_TOPICS:
            desc = clip(t["description"], 300) + "\n\n" + " ".join(site["hashtags"])
            rows.append({
                "サイト": site["name"],
                "バリアント": "v1",
                "カテゴリ": t["category"],
                "記事タイトル": t["title"],
                "URL": site["url"] + t["path"],
                "ピンタイトル": pin_title(t["title"]),
                "ピン説明文": clip_block(desc, DESC_MAX),
                "推奨ボード": f'{site["name"]}／{t["category"]}',
                "画像ファイル": f'{t["slug"]}_v1.jpg',
                "タイトル文字数": len(pin_title(t["title"])),
                "前半55字": clip(t["title"], TITLE_VISIBLE),
                "_prefix": "",
                "_slug": f'{t["slug"]}_v1',
            })
        return rows

    art_dir: Path | None = site["articles"]
    if not art_dir or not art_dir.exists():
        print(f"[SKIP] {site_key}: 記事ディレクトリが無い ({art_dir})")
        return rows

    only = site.get("only_categories")
    # バリアントごとにまとめて並べる（v1 を全記事ぶん出し切ってから v2 に移る）。
    # こうすると同一記事の2本目が在庫1周ぶん後ろに回り、§6-4 の「1本ごとに1週間空ける」を
    # カレンダー側で意識せずに満たせる。
    by_variant: dict[int, list[dict]] = {}
    # .mdx も拾う（Astro コンポーネントを使う記事は拡張子だけが変わる）。
    # The Japan Desk で "*.md" だけを見ていたために記事が丸ごと落ちた事例があるため揃えてある。
    for p in sorted(list(art_dir.glob("*.md")) + list(art_dir.glob("*.mdx"))):
        fm = read_frontmatter(p)
        if fm is None:
            print(f"[SKIP] {p.name}: frontmatter を読めない")
            continue
        if fm.get("draft") or fm.get("noindex"):
            continue
        cslug = fm.get("categorySlug") or ""
        if only and cslug not in only:
            continue

        title = str(fm.get("title") or p.stem)
        products = fm.get("products") or []
        vs = variants_for(products) if (site["pin_style"] == "product" and products) else [1]

        for v in vs:
            img = f"{p.stem}_v{v}.jpg"
            if have is not None and img not in have:
                print(f"[SKIP] {img}: ピン画像が無い（案Cの台帳に弾かれた可能性）")
                continue
            vtitle = variant_title(title, fm, v) if v != 1 else title
            by_variant.setdefault(v, []).append({
                "サイト": site["name"],
                "バリアント": f"v{v}",
                "カテゴリ": fm.get("category") or "",
                "記事タイトル": title,
                "URL": f'{site["url"]}/articles/{p.stem}/',
                "ピンタイトル": pin_title(vtitle),
                "ピン説明文": pin_description(fm, site, v),
                "推奨ボード": f'{site["name"]}／{fm.get("category") or "その他"}',
                "画像ファイル": img,
                "タイトル文字数": len(pin_title(vtitle)),
                "前半55字": clip(vtitle, TITLE_VISIBLE),
                "_prefix": mmdd(fm),
                "_slug": f"{p.stem}_v{v}",
            })

    for v in sorted(by_variant):
        rows.extend(by_variant[v])
    return rows


def public_fields(row: dict) -> list[str]:
    """"_" 始まりは投稿文ファイル名の組み立てにだけ使う内部キー。CSV の列には出さない。"""
    return [k for k in row if not k.startswith("_")]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=public_fields(rows[0]), extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_posts(site_key: str, site: dict, rows: list[dict]) -> int:
    """1ピン＝1テキストファイル。スマホからコピペするときCSVより扱いやすいので、
    退役した rakuten-affiliate-blog 側スクリプトの成果物（Drive の「投稿文」フォルダ）を引き継ぐ。
    ファイル名は MMDD_<slug>_v<n>.txt。画像は本文中に明示するので名前で対応付ける必要はない。"""
    d = OUT / site_key / "posts"
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.txt"):   # 記事が消えたときに旧ファイルを残さない
        old.unlink()
    for r in rows:
        name = f'{r["_prefix"]}_{r["_slug"]}' if r["_prefix"] else r["_slug"]
        body = (
            f'{r["ピンタイトル"]}\n\n'
            f'■ Pinterest 説明文（コピペ用）\n{r["ピン説明文"]}\n\n'
        )
        if site.get("x_template"):
            body += f'■ X 投稿文（コピペ用）\n{x_text(site, r)}\n\n'
        body += (
            f'■ 推奨ボード\n{r["推奨ボード"]}\n\n'
            f'■ 記事リンク\n{r["URL"]}\n\n'
            f'■ 画像\npins/{r["画像ファイル"]}\n'
        )
        (d / f"{name}.txt").write_text(body, encoding="utf-8")
    return len(rows)


def x_text(site: dict, row: dict) -> str:
    """X の手動投稿文。退役した旧スクリプトが出していたので、成果物を減らさないために引き継ぐ。
    テンプレを持つサイト（picknavi）だけに出す。X への自動投稿は別系統（post_to_x.py）。"""
    cat = row.get("カテゴリ") or ""
    tag = f"【{cat}】" if cat else ""
    body = site["x_template"].format(
        tag=tag, title=row["記事タイトル"], url=row["URL"],
        hashtags=" ".join(site["hashtags"][:2]),
    )
    return body[:275]


def write_calendar(per_site: dict[str, list[dict]]) -> int:
    """§6-2 の週次配分どおりに、1日3本（POST_TIMES）で並べた投稿カレンダーを作る。
    同じ記事を2度出さない（重複ピンの減点を避けるため §3-2）。日付は入れず「第N週・M日目」で表す
    （開始日を決めるのは人間の判断なので、ここでは相対の順序だけを固定する）。"""
    queues = {k: list(v) for k, v in per_site.items()}
    rows: list[dict] = []
    week = 1
    while any(queues.values()):
        # その週の割り当て本数をサイトごとに決め、サイト横断のラウンドロビンで並べる
        # （同じ日に同じサイトばかり並ぶと、ボードの露出が偏るため）
        budget = {k: min(SITES[k]["weekly"], len(queues.get(k, []))) for k in SITES}
        week_items: list[dict] = []
        while any(budget.values()):
            for key in SITES:
                if budget[key] > 0 and queues.get(key):
                    week_items.append(queues[key].pop(0))
                    budget[key] -= 1
        if not week_items:
            break
        # その週の本数を7日に均す（週21本なら3本/日、週25本なら3〜4本/日になる）。
        # 時刻は POST_TIMES の優先順で、その日の何本目かに応じて割り当てる。
        n = len(week_items)
        seq: dict[int, int] = {}
        for i, item in enumerate(week_items):
            day = i * DAYS_PER_WEEK // n + 1
            seq[day] = seq.get(day, 0) + 1
            rows.append({
                "第N週": week,
                "曜日目": day,
                "投稿時刻": POST_TIMES[(seq[day] - 1) % len(POST_TIMES)],
                **item,
            })
        week += 1
        if week > 200:  # 暴走止め
            break

    write_csv(OUT / "投稿カレンダー.csv", rows)
    return len(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", help="1サイトだけ生成する（キー名）")
    ap.add_argument("--no-calendar", action="store_true",
                    help="投稿カレンダーを書かない。カレンダーは §6-2 の週次配分を全サイト横断で"
                         "並べるものなので、1サイトしか見えない CI で書くと偏った表になる")
    args = ap.parse_args()

    targets = {args.site: SITES[args.site]} if args.site else SITES
    per_site: dict[str, list[dict]] = {}
    total = 0
    over_title = 0

    for key, site in targets.items():
        rows = collect(key, site)
        per_site[key] = rows
        total += len(rows)
        over_title += sum(1 for r in rows if r["タイトル文字数"] > TITLE_MAX)

        if rows:
            write_csv(OUT / key / "social_kit.csv", rows)
            write_posts(key, site, rows)
        print(f"{site['name']:<12} {len(rows):>3} 本  週{site['weekly']}本配分 -> {len(rows)/max(site['weekly'],1):.1f}週分")

    if total == 0:
        print("投稿文が0件。記事ディレクトリのパスを確認すること。")
        return 1

    n = 0
    if not args.no_calendar and not args.site:
        n = write_calendar(per_site)
    print(f"\n合計 {total} 本の投稿文 / カレンダー {n} 行 -> {OUT}")
    if over_title:
        print(f"[WARN] タイトルが100字を超えた行が {over_title} 件ある")
    return 0


if __name__ == "__main__":
    sys.exit(main())
