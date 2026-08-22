# pinterest-kit/gen_en_kit.py
# The Japan Desk（英語圏）用の Pinterest 投稿文とピン画像を生成する。
#
# ★日本語5サイト（gen_social_kit.py / gen_pins.py）とは出力先を完全に分ける。
#   Pinterest アカウントも Drive フォルダも別系統のため、out_en/ 配下に出す。
#
# 2026-08-07 に「C＋A の2本立て」へ変更した（それ以前は1記事1枚の活字ピンのみ）。
#   C型 = 情報図版（記事の裏取り済みデータを表・タイムライン・リストで見せる）… 毎日1本目
#   A型 = 活字（記事を代表する数字を主役に）                                  … 毎日2本目
# 1日2投稿で公開記事が15本のため、同じ記事の再登場は7〜8日おきになるよう並べる
# （同一URLへの再ピンは1週間空ける、が運用仕様 §3 の規定）。
#
# 実行: python3 gen_en_kit.py
# 出力: out_en/thejapandesk/social_kit.csv, out_en/thejapandesk/pins/*.jpg,
#       out_en/thejapandesk/posts/*.txt, out_en/thejapandesk/posting_calendar.csv
#
# ファイル名は picknavi と同じく「記事の date（MMDD）＋ slug ＋ 型」。
# 画像と投稿文が同じ名前で並ぶので、Drive 上で1本ぶんを取り違えずに拾える。

from __future__ import annotations
import csv
import os
import re
import sys
from pathlib import Path

import yaml

from render_en import W, H, make_pin_a, make_pin_c, make_pin_photo
from pin_data_en import PIN_DATA
from sites_en import EN_SITES, PILLARS, POST_TIMES_JST
from photo_map_en import DATA_ONLY_PILLARS, PHOTO_SHARE, WANTED_FOLDERS, folders_for
from photos_en import PhotoPool

OUT = Path(__file__).resolve().parent / "out_en"

TITLE_MAX = 100
TITLE_VISIBLE = 55
DESC_MAX = 800

# 記事に [VERIFY] マーカーが残っていたら、その記事はピンにしない（未確定の数値を配らないため）。
VERIFY_RE = re.compile(r"\[VERIFY", re.I)


def read_article(path: Path) -> tuple[dict, str] | None:
    try:
        parts = path.read_text(encoding="utf-8").split("---", 2)
        return (yaml.safe_load(parts[1]) or {}), parts[2]
    except Exception:
        return None


def mmdd(fm: dict) -> str:
    """記事の date を MMDD にする。ファイル名の先頭に付けて新着を見分けやすくする
    （picknavi の gen_pins.py / gen_social_kit.py と同じ規則）。"""
    d = fm.get("date")
    s = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
    parts = s.split("-")
    return f"{parts[1]}{parts[2]}" if len(parts) >= 3 else "0000"


def clip(s: str, n: int) -> str:
    """英語なので単語の途中で切らない（語中で切れた「…」は読み手に雑に見える）。"""
    s = " ".join(str(s).split())
    if len(s) <= n:
        return s
    cut = s[: n - 1]
    sp = cut.rfind(" ")
    if sp > n * 0.6:
        cut = cut[:sp]
    return cut.rstrip(" ,;:—-") + "…"


def clip_block(s: str, n: int) -> str:
    s = str(s).strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def whats_inside(body: str, limit: int = 3) -> list[str]:
    """記事のH2見出しから「中身」を最大3点。見出しは記事の実体なので創作にならない。"""
    out: list[str] = []
    for line in body.splitlines():
        if not line.startswith("## "):
            continue
        h = line[3:].strip()
        if VERIFY_RE.search(h):
            continue
        h = re.sub(r"^\d+[.)]\s*", "", h)
        h = re.sub(r"\s*\([^)]*\)\s*$", "", h)
        h = h.strip(" —-–:")
        if h and len(h) > 3:
            out.append(clip(h, 60))
        if len(out) >= limit:
            break
    return out


def lead_clause(title: str, n: int = 46) -> str:
    """記事タイトルの先頭節。C型ピンのタイトル前半に置いてキーワードを先頭50字に入れる。"""
    head = re.split(r"[:：—–\(]", title)[0].strip().rstrip("?？")
    return clip(head, n)


def graphic_bullets(c: dict, limit: int = 4) -> list[str]:
    """図版に載っている項目名を説明文にも出す。画像とテキストの一致（運用仕様 §3-4）のため。"""
    kind = c.get("kind", "table")
    if kind == "timeline":
        src = [f"{a} — {b}" for a, b in c.get("steps", [])]
    elif kind == "list":
        src = [f"{a}: {b}" for a, b in c.get("items", [])]
    else:
        src = [" — ".join(str(x) for x in r[:2]) for r in c.get("rows", [])]
    return [clip(s, 64) for s in src[:limit]]


def build_articles(site: dict) -> list[dict]:
    arts: list[dict] = []
    art_dir: Path = site["articles"]
    if not art_dir.exists():
        print(f"[SKIP] 記事ディレクトリが無い: {art_dir}")
        return arts

    # .mdx も拾う。Astro のコンポーネントを使う記事は .mdx になり、拡張子だけが変わる
    # ——2026-08-09 に 7-day-japan-itinerary が .md → .mdx へ変わった結果、"*.md" だけを
    # 見ていたこのループから記事が丸ごと落ち、ピンが黙って2本減っていた（2026-08-12 に検出）。
    files = sorted(list(art_dir.glob("*.md")) + list(art_dir.glob("*.mdx")))
    for p in files:
        got = read_article(p)
        if got is None:
            print(f"[SKIP] {p.name}: frontmatter を読めない")
            continue
        fm, body = got
        if fm.get("draft"):
            continue                     # 停止中のピラー（craft）はここで落ちる

        pillar = str(fm.get("pillar") or "")
        pconf = PILLARS.get(pillar)
        if not pconf:
            print(f"[SKIP] {p.name}: 未知の pillar '{pillar}'")
            continue

        title = str(fm.get("title") or p.stem)
        slug = str(fm.get("slug") or p.stem)
        desc = str(fm.get("description") or "").strip()

        if VERIFY_RE.search(title) or VERIFY_RE.search(desc) or VERIFY_RE.search(body):
            print(f"[SKIP] {slug}: 記事に [VERIFY] が残っている")
            continue
        # 語学ピラーはデータ図版で固定なので図版データが必須。
        # それ以外は写真ピンで作れるため、図版データが無くても対象に含める。
        if pillar in DATA_ONLY_PILLARS and slug not in PIN_DATA:
            print(f"[SKIP] {slug}: 語学ピラーだが pin_data_en.py に図版データが無い")
            continue

        arts.append({
            "pillar": pillar, "board": pconf["board"], "hashtags": " ".join(pconf["hashtags"]),
            "title": title, "slug": slug, "desc": desc, "mmdd": mmdd(fm),
            "url": f'{site["url"]}/{pillar}/{slug}/',
            "inside": whats_inside(body),
        })
    return arts


def assign_styles(arts: list[dict], pool) -> tuple[dict[str, list[str]], dict[str, object], list[str]]:
    """記事ごとに2枚ぶんの型を決め、写真ピンには**その場で写真を予約する**。

    ・語学ピラー = C（情報図版）＋ A（活字）で固定
    ・それ以外  = 写真ベースを PHOTO_SHARE（既定0.8）、残りを C型
    ・写真が取れなかったスロットはデータ図版へ退避する
      （**季節違いの写真を当てるくらいなら図版のほうがまし**、という判断）

    決め方は記事の順番だけで決まる（乱数なし）ので、再実行しても同じ割り当てになる。
    予約をこの場で行うのは、後段の描画まで待つと「在庫があると判断したのに
    他の記事が先に取っていた」というズレが出るため。
    """
    styles: dict[str, list[str]] = {}
    photos: dict[str, object] = {}
    missing: list[str] = []
    n = 0                                   # 語学以外のピン通し番号
    step = max(1, round(1 / max(1e-9, 1 - PHOTO_SHARE)))   # 0.8 なら 5枚に1枚がC型

    for art in arts:
        slug = art["slug"]
        if art["pillar"] in DATA_ONLY_PILLARS:
            styles[slug] = ["C", "A"] if slug in PIN_DATA else []
            continue

        folders = folders_for(slug)
        pair: list[str] = []
        for i in range(2):
            n += 1
            stem = f'{art["mmdd"]}_{slug}-p{i + 1}'
            want_c = (n % step == 0) and slug in PIN_DATA and "C" not in pair
            if want_c:
                pair.append("C")
                continue
            photo = pool.take(stem, folders) if folders else None
            if photo is not None:
                photos[stem] = photo
                pair.append("P")
                continue
            # 写真が無い。図版へ退避する（同じ型を2枚出すと文面が重複するので C→A の順）
            missing.append(
                f'{slug} ({stem}): '
                + (f'対応フォルダ {folders} に未使用の写真が無い' if folders
                   else '写真フォルダの対応が photo_map_en.py に無い'))
            if slug in PIN_DATA:
                pair.append("A" if "C" in pair else "C")
        styles[slug] = pair
    return styles, photos, missing


def rows_for(art: dict, styles: list[str]) -> list[dict]:
    """1記事から2行。**同じURLの2ピンで文面を共有しない**（重複ピンは減点対象）。"""
    d = PIN_DATA.get(art["slug"], {})
    inside = art["inside"]
    rows = []

    for i, style in enumerate(styles):
        suffix = {"C": "c", "A": "a"}.get(style, f"p{i + 1}")
        stem = f'{art["mmdd"]}_{art["slug"]}-{suffix}'

        if style == "C":
            c = d["c"]
            title = clip(f'{lead_clause(art["title"])}: {c["title"]}', TITLE_MAX)
            blocks = [c["verdict"],
                      "In this graphic:\n" + "\n".join(f"• {b}" for b in graphic_bullets(c))]
            if c.get("source"):
                blocks.append(f'Figures from {c["source"]}, checked August 2026.')
        elif style == "A":
            title = clip(art["title"], TITLE_MAX)
            blocks = []
            if art["desc"]:
                blocks.append(clip(art["desc"], 300))
            if inside:
                blocks.append("What's inside:\n" + "\n".join(f"• {h}" for h in inside))
        else:                                # 写真ピン
            # 1枚目は記事タイトル、2枚目は記事内の見出しを主役にして文面を分ける
            if i == 0 or not inside:
                title = clip(art["title"], TITLE_MAX)
                blocks = ([clip(art["desc"], 300)] if art["desc"] else []) + \
                         (["What's inside:\n" + "\n".join(f"• {h}" for h in inside)] if inside else [])
            else:
                title = clip(f'{lead_clause(art["title"])}: {inside[0]}', TITLE_MAX)
                blocks = ["In this guide:\n" + "\n".join(f"• {h}" for h in inside)] + \
                         ([clip(art["desc"], 300)] if art["desc"] else [])

        blocks.append(art["hashtags"])
        rows.append({
            **{k: art[k] for k in ("pillar", "board", "url")},
            "style": style, "slot": i + 1, "article_title": art["title"],
            "pin_title": title, "pin_description": clip_block("\n\n".join(blocks), DESC_MAX),
            "image_file": f"{stem}.jpg", "post_file": f"{stem}.txt",
            "title_len": len(title), "first_55": clip(title, TITLE_VISIBLE),
        })
    return rows


STYLE_LABEL = {"C": "C型・情報図版", "A": "A型・活字", "P": "写真"}


def write_posts(dir_: Path, rows: list[dict]) -> int:
    """1ピン＝1テキストファイル。Pinterest の投稿欄へそのままコピペできる形にする
    （picknavi の「投稿文」フォルダと同じ役割。画像とファイル名が一対一で並ぶ）。"""
    dir_.mkdir(parents=True, exist_ok=True)
    keep = {r["post_file"] for r in rows}
    if PRUNE:
        for old in dir_.glob("*.txt"):
            if old.name not in keep:
                old.unlink()
                print(f"  [削除] 対象外の旧投稿文: {old.name}")

    created = 0
    for r in rows:
        if (dir_ / r["post_file"]).exists():
            continue          # 既出の投稿文は触らない（不変方針）
        created += 1
        body = (
            f'{r["article_title"]}\n'
            f'（{STYLE_LABEL.get(r["style"], r["style"])}）\n\n'
            f'■ ボード\n{r["board"]}\n\n'
            f'■ ピンタイトル（コピペ用）\n{r["pin_title"]}\n\n'
            f'■ ピン説明文（コピペ用）\n{r["pin_description"]}\n\n'
            f'■ リンク先URL\n{r["url"]}\n\n'
            f'■ 画像\npins/{r["image_file"]}\n'
        )
        (dir_ / r["post_file"]).write_text(body, encoding="utf-8")
    print(f"  投稿文: 新規 {created} / 既存据え置き {len(rows) - created}")
    return len(rows)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


# 【不変方針 2026-08-22】一度出した投稿文・投稿画像は作り直さない。
# Pinterest は予約投稿・投稿済みの中身を後から差し替えられないので、手元の素材だけが
# 新しくなると「配ったものと手元が食い違う」状態になる。だから既存ファイルには触れず、
# 新しい記事のぶんだけを足す。掃除が必要なときだけ人が KIT_PRUNE=1 を付けて実行する。
PRUNE = os.environ.get("KIT_PRUNE") == "1"


def write_csv_preserving(path: Path, rows: list[dict], key: str = "image_file") -> None:
    """索引CSVを「既存行は一字も変えず・新規行だけ追記」で書き直す。

    CSVはピンタイトルと説明文（＝投稿文そのもの）を持つため丸ごと上書きすると
    投稿済みの文面が変わる。逆に凍結すると新しいピンが索引に載らない。
    そこで image_file をキーに、既に載っている行はそのまま残して新しい行だけ足す。
    今回生成されなかった過去の行も、予約投稿に組み込み済みかもしれないので末尾に残す。
    """
    if not rows:
        return
    header = list(rows[0].keys())
    old: dict[str, dict] = {}
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                k = (r.get(key) or "").strip()
                if k:
                    old[k] = r

    merged, seen = [], set()
    for r in rows:
        k = (r.get(key) or "").strip()
        prev = old.get(k)
        # 既存行は維持。列が増えていたら新しい列だけ新値で埋める。
        merged.append({c: (prev[c] if prev and c in prev else r.get(c, "")) for c in header})
        seen.add(k)
    leftover = [r for k, r in old.items() if k not in seen]
    merged.extend({c: r.get(c, "") for c in header} for r in leftover)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(merged)
    added = len(seen - set(old))
    print(f"  CSV: 既存 {len(old)} 行を据え置き / 新規 {added} 行を追記 / 生成対象外で残した行 {len(leftover)}")


def write_calendar(path: Path, arts: list[dict], by_key: dict, per_day: int) -> list[dict]:
    """1日目: 記事1のC＋記事8のA、2日目: 記事2のC＋記事9のA … と半周ずらす。
    こうすると同じ記事のCとAが7〜8日離れ、同一URLへの再ピン間隔の規定を満たす。"""
    n = len(arts)
    offset = n // 2 + (n % 2)          # 15本なら8
    times = [POST_TIMES_JST[0], POST_TIMES_JST[-1]][:per_day]

    out: list[dict] = []
    for day in range(n):
        # 型ではなく「その記事の1枚目／2枚目」で選ぶ。写真ピンが混ざっても同じ間隔が保てる
        picks = [(1, arts[day]), (2, arts[(day + offset) % n])]
        for slot, (which, art) in enumerate(picks[:per_day]):
            row = by_key.get((art["slug"], which))
            if row is None:          # 写真が無くて作れなかったピン。カレンダーからも落とす
                continue
            out.append({"day": day + 1, "slot": slot + 1, "time_jst": times[slot], **row})
    write_csv(path, out)
    return out


def main() -> int:
    total = 0
    for key, site in EN_SITES.items():
        print(f"=== {site['name']} ===")
        arts = build_articles(site)
        if not arts:
            print("  対象記事が0件"); return 1

        pool = PhotoPool()
        styles, photos, missing = assign_styles(arts, pool)
        rows: list[dict] = []
        by_key: dict[tuple, dict] = {}
        for art in arts:
            for r in rows_for(art, styles[art["slug"]]):
                rows.append(r)
                by_key[(art["slug"], r["slot"])] = r

        d = OUT / key
        write_csv_preserving(d / "social_kit.csv", rows)

        # 生成対象から外れた旧ピンの掃除。既定では消さない——予約投稿に組み込み済みの
        # 素材を消しうるため。停止したピラーのぶんを落としたいときだけ KIT_PRUNE=1 を付ける。
        pin_dir = d / "pins"
        pin_dir.mkdir(parents=True, exist_ok=True)
        keep = {r["image_file"] for r in rows}
        if PRUNE:
            for old in pin_dir.glob("*.jpg"):
                if old.name not in keep:
                    old.unlink()
                    print(f"  [削除] 対象外の旧ピン: {old.name}")

        for art in arts:
            data = PIN_DATA.get(art["slug"], {})
            for r in rows_for(art, styles[art["slug"]]):
                stem = r["image_file"][:-4]
                if (pin_dir / r["image_file"]).exists():
                    continue      # 既出のピンは作り直さない（不変方針）
                if r["style"] == "C":
                    make_pin_c(data["c"], pin_dir / r["image_file"])
                elif r["style"] == "A":
                    make_pin_a(data["a"], pin_dir / r["image_file"])
                else:
                    make_pin_photo(photos[stem], {"title": r["article_title"],
                                           "sub": clip(art["desc"], 70),
                                           "eyebrow": PILLARS[art["pillar"]]["label"]},
                                   pin_dir / r["image_file"])
                total += 1
        pool.save()

        # CSV は実際に生成できたピンだけにする（画像の無い行を残すと投稿時に事故る）
        made = {f.name for f in pin_dir.glob("*.jpg")}
        rows = [r for r in rows if r["image_file"] in made]
        by_key = {k: v for k, v in by_key.items() if v["image_file"] in made}
        write_csv_preserving(d / "social_kit.csv", rows)

        for w in pool.warnings:
            print("  " + w)
        if missing:
            print("\n  [要写真] 写真ピンを作れなかったもの:")
            for m in missing:
                print("    - " + m)
            print("    → assets_en/thejapandesk/ に写真を足すか photo_map_en.py の対応を直す")
        stock = pool.stock()
        empty = [n for n, (free, tot) in stock.items() if tot == 0]
        low = [f"{n} 残{free}/{tot}" for n, (free, tot) in sorted(stock.items()) if 0 < free <= 2]
        print(f'\n  写真在庫: 未使用 {sum(f for f, _ in stock.values())} / 総数 {sum(t for _, t in stock.values())} 枚')
        if low:
            print("  残り少ないフォルダ: " + " / ".join(low))
        if empty:
            print("  空のフォルダ: " + " / ".join(f"{n}（{WANTED_FOLDERS.get(n, '')}）" for n in empty))

        posts = write_posts(d / "posts", rows)

        per_day = int(site.get("per_day", 2))
        cal = write_calendar(d / "posting_calendar.csv", arts, by_key, per_day)
        print(f"  記事 {len(arts)} 本 / 投稿文 {posts} 本 / ピン画像 {total} 枚 / "
              f"カレンダー {len(cal)} 行（{per_day}本/日 → {len(cal) / per_day:.0f}日分）")

    # 仕様チェック
    from PIL import Image
    bad = []
    for f in sorted(OUT.glob("*/pins/*.jpg")):
        with Image.open(f) as im:
            if im.size != (W, H):
                bad.append(f"{f.name}: size={im.size}")
        if f.stat().st_size > 20 * 1024 * 1024:
            bad.append(f"{f.name}: 20MB 超")

    # 同一URLの2ピンで文面が重複していないか（重複ピンは減点対象）＋ CSV・画像・投稿文の対応
    seen: dict[str, set] = {}
    for p in sorted(OUT.glob("*/social_kit.csv")):
        with p.open(encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                s = seen.setdefault(r["url"], set())
                if r["pin_description"] in s:
                    bad.append(f'{r["image_file"]}: 同一URLで説明文が重複')
                s.add(r["pin_description"])
                if not (p.parent / "pins" / r["image_file"]).exists():
                    bad.append(f'{r["image_file"]}: CSVが参照する画像が無い')
                if not (p.parent / "posts" / r["post_file"]).exists():
                    bad.append(f'{r["post_file"]}: CSVが参照する投稿文が無い')

    print(f"\n合計 {total} 枚 -> {OUT}")
    if bad:
        print("[NG] 仕様違反:")
        for b in bad:
            print("  " + b)
        return 1
    print("[OK] 1000x1500・20MB以下・同一URLの文面重複なし")

    # 生成したものを Drive へ反映する。手でコピーする工程が残っていたせいで、
    # 2026-08-12 版の Drive と 8/18 版のローカルが10日ぶんずれていた（温泉記事のピンが
    # Drive に届いていなかった）。Drive が止まっていれば見送るだけで、生成は失敗させない。
    if os.environ.get("SKIP_DRIVE_SYNC") != "1":
        print()
        try:
            from sync_drive_en import main as sync_drive
            sync_drive()
        except Exception as e:
            print(f"[警告] Drive への反映に失敗（生成物は {OUT} に残っている）: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
