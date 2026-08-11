# pinterest-kit/variants.py
# 同一記事から作るピンのバリアント定義。gen_pins.py（画像）と gen_social_kit.py（文言）が
# 同じ規則を使う必要があるので、ここ1箇所に置く。
#
# 仕様の正本: Obsidian「Projects/アフィリエイト/Pinterest運用仕様.md」§6-4・§11-5 案A
#   1記事につき最大3本。画像・タイトル・説明文をすべて作り直し、1本ごとに1週間空ける。
#
# 切り口は3つ。事実（商品名・価格帯・想定ユーザー）は記事の frontmatter から取り、創作しない
# （AFFILIATE.md「LLM に事実を書かせない」）。
#   v1 選び方   … 記事タイトルそのまま。商品1点
#   v2 価格帯   … 価格帯ラベルで比較。商品2点
#   v3 用途別   … 各商品の target で整理。商品3点
#
# 価格の「円」表記をタイトル・説明文に出さないのは意図的。ピンの寿命は2〜3年ある一方で
# 楽天の価格は毎日変わるため、数字を焼き付けると時間が経つほど嘘になる。
# 変動しにくい priceBand ラベルだけを使う。

from __future__ import annotations

TITLE_MAX = 100  # Pinterest のタイトル上限（§5-2）

# バリアントごとに必要な商品点数
PRODUCTS_NEEDED = {1: 1, 2: 2, 3: 3}


def variants_for(products: list | None) -> list[int]:
    """商品点数で作れるバリアントを決める。4点ある記事は v1〜v3 の3本、2点なら v1・v2 の2本。"""
    n = len(products or [])
    return [v for v, need in sorted(PRODUCTS_NEEDED.items()) if n >= need]


def title_head(title: str) -> str:
    """記事タイトルの主題部。picknavi の記事は「主題｜補足」の形なので前半を取る。
    キーワードは前半に入っている（§5-2）ので、ここを残せば検索意図から外れない。"""
    head = str(title).split("｜")[0].split("|")[0].strip()
    return head or str(title).strip()


def price_bands(products: list, n: int) -> list[str]:
    """先頭 n 件の priceBand を重複を除いて出現順に返す。"""
    out: list[str] = []
    for p in (products or [])[:n]:
        b = (p or {}).get("priceBand")
        if b and b not in out:
            out.append(str(b))
    return out


def clip(s: str, n: int) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def variant_title(title: str, fm: dict, variant: int) -> str:
    """バリアントごとにタイトルを作り直す（フレッシュ判定③）。
    v1 は記事タイトルそのまま、v2・v3 は主題部を残して切り口だけ差し替える。"""
    if variant == 1:
        return clip(title, TITLE_MAX)

    products = fm.get("products") or []
    head = title_head(title)
    n = PRODUCTS_NEEDED[variant]

    if variant == 2:
        bands = price_bands(products, n)
        tail = f"{'・'.join(bands)}の{n}製品を比較" if bands else f"{n}製品を価格帯で比較"
    else:
        tail = f"用途別に選ぶ{n}製品"
    return clip(f"{head}｜{tail}", TITLE_MAX)
