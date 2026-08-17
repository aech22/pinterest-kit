# pinterest-kit/variants.py
# 1記事から作るピンの本数とレイアウトを決める。gen_pins.py（画像）と gen_social_kit.py（文言）が
# 同じ規則を使う必要があるので、ここ1箇所に置く。
#
# 仕様の正本: Obsidian「Projects/アフィリエイト/Pinterest運用仕様.md」§6-4・§11-5
#
# 2026-08-18 変更: **1記事につき1本だけ作る**。
# それ以前は §11-5 案A に従って v1 選び方（商品1点）/ v2 価格帯（商品2点）/ v3 用途別（商品3点）の
# 3本を出しており、商品4点の記事は毎回3枚のピンになっていた。これを1本に戻し、
# **写真の枚数だけを記事の形に合わせる**。
#
#   商品3点以上（まとめ記事）  … 写真1枚（従来の v1 レイアウト）
#   商品ちょうど2点（2種比較） … 写真2枚（従来の v2 レイアウト）
#   商品1点                    … 写真1枚
#
# 商品点数を判定材料にするのは、これが記事の形そのものだから（picknavi の記事は「4選」なら
# products が4点、2種比較なら2点になる）。タイトル文字列の「比較」等では判別できない
# ——まとめ記事のタイトルにも「比較ポイント」が入るため。
# 3点を並べる v3 レイアウトは、どの記事の形にも対応しないので既定では使わない
# （描画コードは gen_pins.py に残してある。使いたくなったら layouts_for を直すだけでよい）。
#
# タイトルと説明文は**記事のものをそのまま使う**。3本出していた頃は「同じ記事の2本目・3本目が
# 前のピンのコピーに見えないように」切り口ごとに書き直していたが（フレッシュ判定③）、
# 1本になった以上その必要はなく、記事タイトルをそのまま出すほうが検索意図に合う。

from __future__ import annotations

import hashlib

TITLE_MAX = 100  # Pinterest のタイトル上限（§5-2）

# レイアウト番号 -> ピンに載せる商品写真の枚数。
# ピン画像のファイル名の接尾辞 `_v{n}` もこの番号を使う。番号の意味は変わったが番号自体は
# 変えていない——まとめ記事は従来どおり `_v1.jpg` のままで、既に投稿済みのピンと
# ファイル名がぶつからない（案C の重複台帳もそのまま使える）。
PHOTOS_PER_LAYOUT = {1: 1, 2: 2, 3: 3}


def layouts_for(products: list | None) -> list[int]:
    """1記事から作るピンのレイアウトを返す。要素数がそのままピンの本数になる（＝常に1本）。"""
    n = len(products or [])
    if n <= 0:
        return []
    return [2] if n == 2 else [1]


def photos_label(layout: int) -> str:
    """CSV の「レイアウト」列の表示。商品写真を持たないピンは呼び出し側が「テキスト」と書く。"""
    return f"写真{PHOTOS_PER_LAYOUT.get(layout, 1)}枚"


def stable_hash(s: str) -> int:
    """Python の hash() はプロセスごとに salt が変わり再現しないので md5 を使う。
    再現性は案C（同一バイトの検出）の前提でもある。"""
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:8], 16)


def clip(s: str, n: int) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def pin_title(title: str) -> str:
    """ピンのタイトルは記事タイトルそのまま（100字上限で末尾だけ落とす）。"""
    return clip(title, TITLE_MAX)
