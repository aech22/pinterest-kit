# pinterest-kit/gen_pins.py
# 全サイトの記事から Pinterest 用のピン画像を生成する。
#
# 仕様の正本: Obsidian「Projects/アフィリエイト/Pinterest運用仕様.md」§5-1
#   1000 × 1500 px（2:3）／20MB以下／JPG・PNG・WEBP
#   主要テキストは上部〜中央。下端10%にはロゴ・CTA を置かない
#   画像と文言を一致させる（ズレるとミックスシグナルでリーチが落ちる）
#
# 2026-08-07 に §11-5 の案A〜案E を実装した。
#   案A: 商品型サイトは1記事から v1/v2/v3 の3レイアウトを作る（供給3倍＋テンプレ反復の緩和）
#   案B: 楽天サムネを ?_ex=800x800 で取得する（従来は400x400のままカード内で余白だらけだった）
#   案C: 出力バイトの SHA-256 を out/<site>/pins_ledger.json に記録し、
#        別ファイル名で同一バイトが出たら [DUP] として書き込まない（重複ピンの機械的な防止）
#   案D: 背景グラデの色相を categorySlug 由来で ±15° 振り、フッタのタグラインを記事ごとに回す
#   案E: 焼き込みバッジ（「81%OFF」等）の少ない商品を主役スロットに選び、必要なら周縁をトリムする
#
# 実行: python3 gen_pins.py [--site picknavi] [--limit 5] [--no-ledger]
# 出力: out/<site>/pins/<slug>_v{1,2,3}.jpg

from __future__ import annotations
import argparse
import colorsys
import hashlib
import io
import json
import os
import sys
from pathlib import Path

import requests
import yaml
from PIL import Image, ImageDraw, ImageFont

from sites import SITES, SHIFTY_TOPICS, OUT
# バリアント数とタイトルの規則は gen_social_kit.py と共有する（画像と文言をズラさないため）
from variants import variant_title, variants_for

W, H = 1000, 1500          # §5-1 2:3
BOTTOM_SAFE = int(H * 0.10)  # 下端10%は空けておく
FOOTER_Y = H - BOTTOM_SAFE - 46
WHITE = (255, 255, 255)
# OUT は sites.py が持つ（PINKIT_OUT で差し替え可能。既定は pinterest-kit/out）
LEDGER_NAME = "pins_ledger.json"

# Linux(GitHub Actions: fonts-noto-cjk) / macOS の両対応
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


# --- 案D: 記事ごとの色・タグラインの振り分け -------------------------------------

def stable_hash(s: str) -> int:
    """Python の hash() はプロセスごとに salt が変わり再現しないので md5 を使う。
    再現性は案C（同一バイトの検出）の前提でもある。"""
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:8], 16)


def shift_hue(rgb: tuple[int, int, int], deg: float) -> tuple[int, int, int]:
    r, g, b = (c / 255 for c in rgb)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb((h + deg / 360.0) % 1.0, l, s)
    return tuple(int(round(c * 255)) for c in (r, g, b))


HUE_RANGE = 8  # ±この角度だけ色相を振る


def brand_colors(site: dict, seed: str) -> tuple[tuple, tuple]:
    """ブランド色を seed（categorySlug 等）由来で ±8° 振る。
    ランダムではなく決定値なので、同カテゴリのピンはボード内で色が揃う。

    案D の初案は ±15° だったが、picknavi のブランド色は色相 14°（赤寄りのオレンジ）で、
    -15° 振ると (255,60,53) ＝ ほぼ赤になりブランド色として認識できなくなる（実測）。
    「ブランド認知を壊さない範囲で」という案Dの条件を満たすため ±8° に狭めた。"""
    deg = stable_hash(seed) % (HUE_RANGE * 2 + 1) - HUE_RANGE
    return shift_hue(site["brand"], deg), shift_hue(site["brand2"], deg)


def pick_tagline(site: dict, seed: str) -> str:
    tls = site.get("taglines") or [site["tagline"]]
    return tls[stable_hash(seed) % len(tls)]


def variant_tagline(site: dict, variant: int) -> str:
    """商品型のフッタは切り口（v1 選び方 / v2 価格帯 / v3 用途別）に対応させる。
    ハッシュで散らすと「用途別のピンに価格帯のタグライン」が出てしまい、
    §5-1 の「画像と文言の一致」に反する。"""
    tls = site.get("taglines") or [site["tagline"]]
    return tls[(variant - 1) % len(tls)]


def vgradient(w: int, h: int, c1, c2) -> Image.Image:
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    return img


# --- テキスト組み --------------------------------------------------------------

def wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int, max_lines: int) -> list[str]:
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) <= max_w:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
            if len(lines) == max_lines:
                return lines
    if cur:
        lines.append(cur)
    lines = lines[:max_lines]
    lines = apply_kinsoku(lines)
    # 最終行が1〜2文字だけ（句点や助詞1文字）になると見た目が崩れるので前の行にぶら下げる。
    # わずかに max_w を超えるが、余白の範囲に収まる。
    if len(lines) > 1 and len(lines[-1]) <= 2:
        lines[-2] += lines[-1]
        lines.pop()
    return lines


# 行頭に来てはいけない文字（行頭禁則）。該当したら前の行の末尾1文字を次の行へ送る（追い出し）。
KINSOKU_START = "、。，．・？！ー〜）］｝」』】〉》”’ゝゞヽヾっゃゅょッャュョぁぃぅぇぉァィゥェォ:;）"


def apply_kinsoku(lines: list[str]) -> list[str]:
    out = [list(ln) for ln in lines]
    for i in range(1, len(out)):
        # 1行に何度も送ることはないので上限を付けて無限ループを防ぐ
        for _ in range(3):
            if out[i] and out[i][0] in KINSOKU_START and len(out[i - 1]) > 1:
                out[i].insert(0, out[i - 1].pop())
            else:
                break
    return ["".join(ln) for ln in out if ln]


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_w: int, band_h: int,
             sizes: list[int], max_lines: int) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    """指定の高さ(band_h)に収まる最大のフォントサイズを選び、(font, lines, 行送り) を返す。
    フォントを落としても収まらないときは最小サイズで行数を切る。"""
    for size in sizes:
        font = load_font(size)
        lh = int(size * 1.32)
        lines = wrap(draw, text, font, max_w, max_lines)
        if len(lines) * lh <= band_h:
            return font, lines, lh
    size = sizes[-1]
    font = load_font(size)
    lh = int(size * 1.32)
    return font, wrap(draw, text, font, max_w, max(1, band_h // lh)), lh


def draw_lines(draw, lines, font, lh, x, y, fill) -> int:
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=fill)
        y += lh
    return y


# --- 案B: 商品画像の取得（高解像度＋キャッシュ） ---------------------------------

_FETCH_CACHE: dict[str, Image.Image | None] = {}


def hires_url(url: str) -> str:
    """楽天サムネイルのサイズ指定を 800x800 に上げる（実測で 800×800 が返ることを確認済み）。
    カード内寸は最大 800×620 なので、400×400 のままだと拡大されず余白だらけになる。"""
    return url.replace("_ex=400x400", "_ex=800x800")


def fetch_image(url: str) -> Image.Image | None:
    if not url:
        return None
    if url in _FETCH_CACHE:
        return _FETCH_CACHE[url]
    img = None
    # 高解像度 → 失敗したら元のURLへフォールバック
    for u in dict.fromkeys([hires_url(url), url]):
        try:
            r = requests.get(u, timeout=20)
            if r.status_code == 200:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                break
        except Exception:
            continue
    _FETCH_CACHE[url] = img
    return img


# --- 案E: 焼き込みバッジ（「81%OFF」「楽天1位」等）の回避 -------------------------

BADGE_TRIM = 0.08      # トリムする比率（片側）
BADGE_THRESHOLD = 0.06  # この比率を超えたらトリムする


def badge_score(img: Image.Image) -> float:
    """画像の周縁部にある「高彩度の赤〜橙」の割合。出品者が入れた販促バッジの代理指標。
    バッジは四隅・上下端に置かれることが多いので、中央60%を除いた領域だけを見る。"""
    hsv = img.convert("HSV").resize((80, 80))
    px = hsv.load()
    warm = total = 0
    for y in range(80):
        for x in range(80):
            if 16 <= x < 64 and 16 <= y < 64:   # 中央60%は商品本体なので除外
                continue
            h, s, v = px[x, y]
            total += 1
            if s > 128 and v > 128 and (h < 30 or h > 235):
                warm += 1
    return warm / total if total else 0.0


def trim_badges(img: Image.Image) -> Image.Image:
    """周縁のバッジを枠外へ追い出す。商品本体は中央にあるのが通例なので、
    片側 8% までの控えめなトリムに留める（切りすぎて商品を欠かないため）。"""
    if badge_score(img) <= BADGE_THRESHOLD:
        return img
    dx, dy = int(img.width * BADGE_TRIM), int(img.height * BADGE_TRIM)
    return img.crop((dx, dy, img.width - dx, img.height - dy))


def load_products(products: list, n: int) -> list[Image.Image]:
    """先頭 n 件の商品画像を取得し、バッジの少ない順に並べ替えて返す。
    「どの n 件を使うか」は rank 順のまま変えない（CSV の説明文と集合を一致させるため）。
    並べ替えるのは主役スロットに置く1枚を選ぶためだけ。"""
    imgs = []
    for p in (products or [])[:n]:
        u = (p or {}).get("image", "")
        im = fetch_image(u)
        if im is not None:
            imgs.append(trim_badges(im))
    imgs.sort(key=badge_score)
    return imgs


# --- 共通パーツ ----------------------------------------------------------------

def draw_header(draw: ImageDraw.ImageDraw, site: dict, category: str, brand: tuple) -> None:
    draw.text((70, 70), site["name"], font=load_font(46), fill=WHITE)
    if category:
        f = load_font(34)
        cw = draw.textlength(category, font=f)
        draw.rounded_rectangle([70, 150, 70 + cw + 56, 210], radius=30, fill=WHITE)
        draw.text((98, 160), category, font=f, fill=brand)


def draw_footer(draw: ImageDraw.ImageDraw, tagline: str) -> None:
    # 下端10%より上に置く（切れ対策・§5-1）
    draw.text((70, FOOTER_Y), tagline, font=load_font(32), fill=WHITE)


def paste_card(canvas: Image.Image, draw: ImageDraw.ImageDraw, box: list[int],
               img: Image.Image | None, pad: int = 40, radius: int = 40) -> None:
    """白い角丸カードを置き、あれば商品画像を中央に貼る。"""
    draw.rounded_rectangle(box, radius=radius, fill=WHITE)
    if img is None:
        return
    inner_w, inner_h = box[2] - box[0] - pad * 2, box[3] - box[1] - pad * 2
    im = img.copy()
    im.thumbnail((inner_w, inner_h), Image.LANCZOS)
    canvas.paste(im, (box[0] + ((box[2] - box[0]) - im.width) // 2,
                      box[1] + ((box[3] - box[1]) - im.height) // 2))


# --- 案A: 3レイアウト -----------------------------------------------------------

def render_product_pin(site: dict, title: str, category: str, products: list,
                       variant: int, seed: str) -> Image.Image:
    """variant 1/2/3 で見た目の異なるピンを描く。使う商品点数も 1/2/3 と変える。"""
    brand, brand2 = brand_colors(site, seed)
    canvas = vgradient(W, H, brand, brand2)
    draw = ImageDraw.Draw(canvas)
    draw_header(draw, site, category, brand)
    imgs = load_products(products, {1: 1, 2: 2, 3: 3}[variant])

    if variant == 1:
        # 現行レイアウト: 上に大きな商品カード、下にタイトル
        card = [60, 250, W - 60, 950]
        paste_card(canvas, draw, card, imgs[0] if imgs else None)
        top = card[3] + 60
        f, lines, lh = fit_text(draw, title, W - 140, (FOOTER_Y - 40) - top, [58, 52, 46, 40], 4)
        draw_lines(draw, lines, f, lh, 70, top, WHITE)

    elif variant == 2:
        # タイトル先出し型: 上部にタイトルを大きく、下に商品2点を横並び
        f, lines, lh = fit_text(draw, title, W - 140, 410, [76, 66, 58, 50], 4)
        draw_lines(draw, lines, f, lh, 70, 250, WHITE)
        for i, box in enumerate([[60, 700, 490, 1250], [510, 700, 940, 1250]]):
            paste_card(canvas, draw, box, imgs[i] if i < len(imgs) else None, pad=30, radius=32)

    else:
        # モザイク型: 小さめのタイトル帯＋商品3点（1大2小）
        f, lines, lh = fit_text(draw, title, W - 140, 180, [50, 44, 40], 3)
        draw_lines(draw, lines, f, lh, 70, 250, WHITE)
        paste_card(canvas, draw, [60, 460, W - 60, 880], imgs[0] if imgs else None, pad=30)
        for i, box in enumerate([[60, 900, 490, 1250], [510, 900, 940, 1250]], start=1):
            paste_card(canvas, draw, box, imgs[i] if i < len(imgs) else None, pad=30, radius=32)

    draw_footer(draw, variant_tagline(site, variant))
    return canvas


def render_text_pin(site: dict, title: str, category: str, lead: str, seed: str) -> Image.Image:
    """商品画像を持たないサイト（ASP系・Shifty）向けのタイポグラフィ型。
    主要テキストを上部〜中央に置く（§5-1）。案A のバリアントは商品写真を前提にするので
    ここでは作らない（v1 のみ）。"""
    brand, brand2 = brand_colors(site, seed)
    canvas = vgradient(W, H, brand, brand2)
    draw = ImageDraw.Draw(canvas)
    draw_header(draw, site, category, brand)

    # 中央: 白カードにタイトル＋リード。カードの高さは中身に合わせて決める（余白の間延びを防ぐ）
    pad, inner_w = 60, W - 120 - 120
    top = 300
    max_bottom = FOOTER_Y - 60

    f_title, t_lines, t_lh = fit_text(draw, title, inner_w, 5 * 82, [60, 54, 48], 5)
    f_lead, l_lines, l_lh = fit_text(draw, lead, inner_w, 6 * 52, [36, 32, 28], 6)

    body_h = pad + len(t_lines) * t_lh + 20 + 8 + 50 + len(l_lines) * l_lh + pad
    card = [60, top, W - 60, min(top + body_h, max_bottom)]
    draw.rounded_rectangle(card, radius=40, fill=WHITE)

    y = draw_lines(draw, t_lines, f_title, t_lh, card[0] + pad, card[1] + pad, (35, 48, 58))

    # タイトルとリードの間に区切り線
    y += 20
    draw.rounded_rectangle([card[0] + pad, y, card[0] + pad + 100, y + 8], radius=4, fill=brand)
    y += 50

    for ln in l_lines:
        if y + l_lh > card[3] - pad:
            break
        draw.text((card[0] + pad, y), ln, font=f_lead, fill=(90, 100, 110))
        y += l_lh

    draw_footer(draw, pick_tagline(site, seed))
    return canvas


# --- 案C: 同一バイトの再出力を防ぐ台帳 -------------------------------------------

class Ledger:
    """生成したピンの SHA-256 を記録する。別ファイル名で同一バイトが出たら重複ピンなので弾く。
    gen_pins.py の描画は決定論的（乱数・時刻を使わない）ので、この照合が意味を持つ。"""

    def __init__(self, path: Path, enabled: bool = True):
        self.path, self.enabled = path, enabled
        self.data: dict[str, str] = {}
        if enabled and path.exists():
            try:
                self.data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                self.data = {}

    def check(self, digest: str, name: str) -> str | None:
        """同じバイト列を別名で既に出していれば、その既存ファイル名を返す。"""
        if not self.enabled:
            return None
        owner = self.data.get(digest)
        return owner if owner and owner != name else None

    def record(self, digest: str, name: str) -> None:
        if self.enabled:
            self.data[digest] = name

    def save(self) -> None:
        if self.enabled:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2),
                                 encoding="utf-8")


def emit(canvas: Image.Image, out_path: Path, ledger: Ledger) -> str:
    """JPEG にしてから台帳と突き合わせ、新しいバイト列のときだけ書き出す。
    戻り値: "new" / "same" / "dup"（dup は別名の既存ピンと同一バイト）"""
    buf = io.BytesIO()
    canvas.save(buf, "JPEG", quality=85)
    raw = buf.getvalue()
    digest = hashlib.sha256(raw).hexdigest()

    owner = ledger.check(digest, out_path.name)
    if owner:
        print(f"  [DUP] {out_path.name}: {owner} と同一バイト。書き込まない")
        return "dup"

    unchanged = out_path.exists() and hashlib.sha256(out_path.read_bytes()).hexdigest() == digest
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(raw)
    ledger.record(digest, out_path.name)
    return "same" if unchanged else "new"


# --- 記事の読み込みとビルド ------------------------------------------------------

def read_frontmatter(path: Path) -> dict | None:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1]) or {}
    except Exception:
        return None


def build_site(key: str, site: dict, limit: int | None, use_ledger: bool) -> dict[str, int]:
    out_dir = OUT / key / "pins"
    ledger = Ledger(OUT / key / LEDGER_NAME, use_ledger)
    stat = {"new": 0, "same": 0, "dup": 0, "skip": 0}

    def run(fn, name: str) -> None:
        try:
            stat[emit(fn(), out_dir / name, ledger)] += 1
        except Exception as e:
            print(f"  [SKIP] {name}: {type(e).__name__}: {e}")
            stat["skip"] += 1

    if key == "shifty":
        for t in SHIFTY_TOPICS[: limit or None]:
            run(lambda t=t: render_text_pin(site, t["title"], t["category"],
                                            t["description"], t["slug"]),
                f'{t["slug"]}_v1.jpg')
        ledger.save()
        return stat

    art_dir: Path | None = site["articles"]
    if not art_dir or not art_dir.exists():
        print(f"  [SKIP] 記事ディレクトリが無い: {art_dir}")
        return stat

    only = site.get("only_categories")
    done = 0
    # .mdx も拾う（gen_social_kit.py と同じ理由。片方だけ拾うと CSV と画像がズレる）
    for p in sorted(list(art_dir.glob("*.md")) + list(art_dir.glob("*.mdx"))):
        if limit and done >= limit:
            break
        fm = read_frontmatter(p)
        if fm is None or fm.get("draft") or fm.get("noindex"):
            continue
        if only and (fm.get("categorySlug") or "") not in only:
            continue

        title = str(fm.get("title") or p.stem)
        category = str(fm.get("category") or "")
        products = fm.get("products") or []
        # 案D: 同カテゴリでは色を揃えたいので seed はカテゴリ由来にする
        seed = str(fm.get("categorySlug") or category or p.stem)

        if site["pin_style"] == "product" and products:
            for v in variants_for(products):
                run(lambda v=v: render_product_pin(site, variant_title(title, fm, v),
                                                   category, products, v, seed),
                    f"{p.stem}_v{v}.jpg")
        else:
            run(lambda: render_text_pin(site, title, category,
                                        str(fm.get("description") or ""), seed),
                f"{p.stem}_v1.jpg")
        done += 1

    ledger.save()
    return stat


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", help="1サイトだけ生成する（キー名）")
    ap.add_argument("--limit", type=int, help="1サイトあたりの生成上限（記事数）")
    ap.add_argument("--no-ledger", action="store_true", help="案Cの重複台帳を使わない")
    args = ap.parse_args()

    targets = {args.site: SITES[args.site]} if args.site else SITES
    total = dict.fromkeys(["new", "same", "dup", "skip"], 0)
    for key, site in targets.items():
        print(f"=== {site['name']} ===")
        st = build_site(key, site, args.limit, not args.no_ledger)
        for k in total:
            total[k] += st[k]
        print(f"  新規 {st['new']} / 変化なし {st['same']} / 重複弾き {st['dup']} / スキップ {st['skip']}")

    # 仕様チェック: 全ファイルが 1000x1500・20MB以下であること
    bad = []
    for f in sorted(OUT.glob("*/pins/*.jpg")):
        with Image.open(f) as im:
            if im.size != (W, H):
                bad.append(f"{f.name}: size={im.size}")
        if f.stat().st_size > 20 * 1024 * 1024:
            bad.append(f"{f.name}: {f.stat().st_size} bytes > 20MB")

    print(f"\n合計 新規{total['new']} / 変化なし{total['same']} / 重複弾き{total['dup']} -> {OUT}")
    if bad:
        print("[NG] 仕様違反:")
        for b in bad:
            print("  " + b)
        return 1
    print("[OK] 全ファイルが 1000x1500・20MB以下")
    return 0


if __name__ == "__main__":
    sys.exit(main())
