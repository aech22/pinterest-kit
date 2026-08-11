# pinterest-kit/render_en.py
# The Japan Desk（英語圏）のピン画像レンダラ。2つの型を持つ。
#
#   C型 = 情報図版（table / timeline / list）… 記事の裏取り済みデータをそのまま図にする。
#         Pinterest の最重要シグナルは「保存」で、保存されるのは後で見返す情報のため。
#   A型 = 活字（数字を主役にした組み）… 素材ゼロで作れる。数値を持たない記事も埋められる。
#
# ★同一記事に2枚作るので、C と A で「違う数字・違う切り口」を使うこと（pin_data_en.py 側の責任）。
#   画像もテキストも作り直さないと Pinterest のフレッシュピン判定を満たさず、重複ピンとして減点される。
#
# フォントは macOS 前提（このキットは手元実行のみ。CI では動かさない）。
# Georgia Bold = 見出しのセリフ、Avenir Next = ラベル・表・数値。

from __future__ import annotations
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1000, 1500
BOTTOM_SAFE = 150          # 下端10%にはロゴ・CTAを置かない（運用仕様 §5-1）

# 配色（サイト src/styles/global.css と揃える）
INDIGO      = (33, 56, 79)
INDIGO_DEEP = (22, 34, 47)
VERMILION   = (200, 64, 47)
PAPER       = (244, 242, 237)
INK         = (22, 34, 47)
INK_SOFT    = (107, 118, 132)
RULE        = (217, 213, 204)
WHITE       = (255, 255, 255)
SKY         = (159, 189, 216)
SKY_DIM     = (127, 163, 198)

_SERIF_B = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
_SERIF_R = "/System/Library/Fonts/Supplemental/Georgia.ttf"
_SANS    = "/System/Library/Fonts/Avenir Next.ttc"
_SANS_IDX = {"bold": 0, "demi": 2, "medium": 5}

_cache: dict[tuple, ImageFont.FreeTypeFont] = {}


def serif(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    key = ("serif", size, bold)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(_SERIF_B if bold else _SERIF_R, size)
    return _cache[key]


def sans(size: int, weight: str = "demi") -> ImageFont.FreeTypeFont:
    key = ("sans", size, weight)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(_SANS, size, index=_SANS_IDX[weight])
    return _cache[key]


def wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int, max_lines: int) -> list[str]:
    """英語は語単位で折り返す（文字単位だと "ICOC|A" のように語が割れる）。"""
    lines: list[str] = []
    cur = ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
            continue
        if cur:
            lines.append(cur)
            if len(lines) == max_lines:
                return lines
        cur = word
    if cur:
        lines.append(cur)
    return lines[:max_lines]


def fit(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int,
        sizes: list[int], max_lines: int, font_of=serif, lh_ratio: float = 1.14):
    """max_w × max_h に収まる最大サイズを選ぶ。収まらなければ最小サイズで返す。"""
    for size in sizes:
        font = font_of(size)
        lh = int(size * lh_ratio)
        lines = wrap(draw, text, font, max_w, max_lines)
        if len(lines) * lh <= max_h and all(draw.textlength(l, font=font) <= max_w for l in lines):
            return font, lines, lh
    font = font_of(sizes[-1])
    lh = int(sizes[-1] * lh_ratio)
    return font, wrap(draw, text, font, max_w, max_lines), lh


def tracked(draw: ImageDraw.ImageDraw, xy, text: str, font, fill, track: int = 0) -> float:
    """字送りを足して描く（大文字ラベルは字間を開けないと詰まって見える）。"""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + track
    return x - track - xy[0]


def tracked_w(draw: ImageDraw.ImageDraw, text: str, font, track: int = 0) -> float:
    return sum(draw.textlength(c, font=font) for c in text) + track * max(0, len(text) - 1)


# --------------------------------------------------------------------------- A型

def make_pin_a(d: dict, out_path: Path) -> None:
    """活字型。記事を代表する数字を主役に、キャンバス全体を使う。"""
    img = Image.new("RGB", (W, H), INDIGO)
    draw = ImageDraw.Draw(img)

    # 上端から下端へわずかに沈める（単色だと印刷物のように平坦に見えるため）
    for y in range(H):
        t = y / H
        draw.line([(0, y), (W, y)],
                  fill=tuple(int(INDIGO[i] + (INDIGO_DEEP[i] - INDIGO[i]) * t * 0.55) for i in range(3)))

    M = 78
    draw.text((M, 68), "The Japan Desk", font=sans(40, "bold"), fill=SKY)

    # 数字。桁数で入るサイズが変わるので幅から逆算する
    num = str(d["num"])
    size = 380
    while size > 120 and draw.textlength(num, font=serif(size)) > W - M * 2:
        size -= 10
    f_num = serif(size)
    y = 190
    draw.text((M - int(size * 0.03), y), num, font=f_num, fill=WHITE)
    # 送りは実測のbboxで取る。カンマ・¥の下ひげがあると size 比の概算では単位ラベルに食い込む
    y = draw.textbbox((M, y), num, font=f_num)[3] + 26

    tracked(draw, (M, y), str(d["unit"]).upper(), sans(42, "bold"), (232, 146, 127), track=7)
    y += 96

    draw.rectangle([M, y, M + 190, y + 7], fill=VERMILION)
    y += 62

    # 補足の位置を先に決め、見出しは残りの高さを使い切るサイズを選ぶ（中段が空かないように）
    sub_lines = [s for s in str(d.get("sub", "")).split("\n") if s.strip()][:2]
    sub_top = H - BOTTOM_SAFE - 28 - len(sub_lines) * 48
    avail = sub_top - 56 - y

    f_t, t_lines, t_lh = fit(draw, d["title"], W - M * 2, avail,
                             [116, 104, 92, 82, 74, 66, 58], 5)
    for ln in t_lines:
        draw.text((M, y), ln, font=f_t, fill=WHITE)
        y += t_lh

    f_s = sans(34, "medium")
    sy = sub_top
    for ln in sub_lines:
        draw.text((M, sy), ln, font=f_s, fill=SKY_DIM)
        sy += 48

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=88)


# --------------------------------------------------------------------------- C型

def _c_header(draw: ImageDraw.ImageDraw, d: dict, M: int) -> int:
    tracked(draw, (M, 84), str(d["eyebrow"]).upper(), sans(27, "bold"), VERMILION, track=5)
    y = 138
    f_t, lines, lh = fit(draw, d["title"], W - M * 2, 3 * 86, [72, 64, 56, 50], 3)
    for ln in lines:
        draw.text((M, y), ln, font=f_t, fill=INK)
        y += lh
    return y + 40


def _c_footer(draw: ImageDraw.ImageDraw, d: dict, M: int) -> None:
    """結論の帯＋出典。帯は下端セーフゾーンの直上に固定する。"""
    verdict = str(d.get("verdict", "")).strip()
    source = str(d.get("source", "")).strip()

    foot_y = H - BOTTOM_SAFE - 34
    tracked(draw, (M, foot_y), "THE JAPAN DESK", sans(26, "bold"), INK_SOFT, track=4)

    if not verdict:
        return
    f_v, v_lines, v_lh = fit(draw, verdict, W - M * 2 - 72, 2 * 46, [34, 30, 27], 2,
                             font_of=lambda s: sans(s, "bold"), lh_ratio=1.34)
    box_h = 40 + len(v_lines) * v_lh + (34 if source else 0) + 40
    box_top = foot_y - 46 - box_h
    draw.rectangle([M, box_top, W - M, box_top + box_h], fill=INK)

    y = box_top + 40
    for ln in v_lines:
        draw.text((M + 36, y), ln, font=f_v, fill=WHITE)
        y += v_lh
    if source:
        draw.text((M + 36, y + 6), f"Source: {source}", font=sans(24, "medium"), fill=SKY)


def _c_body_top_bottom(draw: ImageDraw.ImageDraw, d: dict, M: int) -> tuple[int, int]:
    top = _c_header(draw, d, M)
    verdict = str(d.get("verdict", "")).strip()
    if verdict:
        f_v, v_lines, v_lh = fit(draw, verdict, W - M * 2 - 72, 2 * 46, [34, 30, 27], 2,
                                 font_of=lambda s: sans(s, "bold"), lh_ratio=1.34)
        box_h = 40 + len(v_lines) * v_lh + (34 if d.get("source") else 0) + 40
        bottom = H - BOTTOM_SAFE - 34 - 46 - box_h - 44
    else:
        bottom = H - BOTTOM_SAFE - 34 - 44
    return top, bottom


def _draw_table(draw: ImageDraw.ImageDraw, d: dict, M: int, top: int, bottom: int) -> None:
    cols = d["columns"]
    rows = d["rows"]
    hl = d.get("highlight_col")
    n = len(cols)
    table_w = W - M * 2
    GUT = 26

    avail = bottom - top - 50
    row_h = int(avail / max(1, len(rows)))

    # 列幅は等分ではなく実測で割り付ける。等分にすると、内容の長い列が
    # 隣の列へはみ出して文字が重なる（2〜3列目は右寄せのため左へあふれる）。
    def measure(size: int) -> tuple[list[float], bool]:
        ws = []
        for i in range(n):
            # ハイライト列は太字で描くので、幅も太字で測る（demi で測ると隣の列へはみ出す）
            f = sans(size, "bold" if (hl is not None and i == hl) else "demi")
            cells = [str(r[i]) for r in rows if i < len(r)]
            ws.append(max([draw.textlength(c, font=f) for c in cells] or [0]))
        first_cap = table_w * 0.46
        ws[0] = min(ws[0], first_cap)              # 1列目だけは頭打ちして2行に折る
        return ws, sum(ws) + GUT * (n - 1) <= table_w

    size = int(min(40, row_h * 0.30))
    while size > 22:
        widths, ok = measure(size)
        if ok:
            break
        size -= 2
    widths, _ = measure(size)

    # 余った幅は列間に配って表を左右いっぱいに張る
    slack = table_w - sum(widths) - GUT * (n - 1)
    gut = GUT + (slack / (n - 1) if n > 1 and slack > 0 else 0)

    def col_x(i: int) -> tuple[float, float]:
        left = M + sum(widths[:i]) + gut * i
        return left, left + widths[i]

    f_h = sans(25, "bold")
    y = top
    for i, c in enumerate(cols):
        left, right = col_x(i)
        label = str(c).upper()
        if i == 0:
            tracked(draw, (left, y), label, f_h, INK_SOFT, track=3)
        else:
            tracked(draw, (right - tracked_w(draw, label, f_h, 3), y), label, f_h, INK_SOFT, track=3)
    y += 46
    draw.rectangle([M, y, W - M, y + 4], fill=INK)
    y += 4

    first_w = widths[0]
    f_c = sans(size, "demi")
    f_c_hl = sans(size, "bold")

    for r in rows:
        cy = y + int(row_h * 0.30)
        for i, cell in enumerate(r[:n]):
            left, right = col_x(i)
            hot = (hl is not None and i == hl)
            f = f_c_hl if hot else f_c
            fill = VERMILION if hot else INK
            text = str(cell)
            if i == 0:
                lines = wrap(draw, text, f, first_w, 2)
                yy = cy - (len(lines) - 1) * 22
                for ln in lines:
                    draw.text((left, yy), ln, font=f, fill=fill)
                    yy += 44
            else:
                draw.text((right - draw.textlength(text, font=f), cy), text, font=f, fill=fill)
        y += row_h
        draw.rectangle([M, y - 2, W - M, y], fill=RULE)


def _draw_timeline(draw: ImageDraw.ImageDraw, d: dict, M: int, top: int, bottom: int) -> None:
    steps = d["steps"]
    avail = bottom - top
    step_h = int(avail / max(1, len(steps)))
    rail_x = M + 16
    draw.rectangle([rail_x - 2, top + 18, rail_x + 2, top + step_h * (len(steps) - 1) + 22], fill=RULE)

    f_l = sans(27, "bold")
    f_r = sans(min(42, int(step_h * 0.26)), "demi")
    y = top
    for i, (left_t, right_t) in enumerate(steps):
        draw.ellipse([rail_x - 13, y + 8, rail_x + 13, y + 34],
                     fill=VERMILION if i == 0 else INK)
        tracked(draw, (rail_x + 42, y + 10), str(left_t).upper(), f_l, INK_SOFT, track=3)
        lines = wrap(draw, str(right_t), f_r, W - M - (rail_x + 42) - 20, 2)
        yy = y + 50
        for ln in lines:
            draw.text((rail_x + 42, yy), ln, font=f_r, fill=INK)
            yy += int(f_r.size * 1.24)
        y += step_h


def _draw_list(draw: ImageDraw.ImageDraw, d: dict, M: int, top: int, bottom: int) -> None:
    items = d["items"]
    avail = bottom - top
    item_h = int(avail / max(1, len(items)))
    f_h = sans(min(42, int(item_h * 0.27)), "bold")
    f_n = sans(min(31, int(item_h * 0.20)), "medium")

    y = top
    for head, note in items:
        draw.rectangle([M, y + 10, M + 8, y + item_h - 26], fill=VERMILION)
        draw.text((M + 32, y + 6), str(head), font=f_h, fill=INK)
        lines = wrap(draw, str(note), f_n, W - M * 2 - 32, 2)
        yy = y + 8 + int(f_h.size * 1.22)
        for ln in lines:
            draw.text((M + 32, yy), ln, font=f_n, fill=INK_SOFT)
            yy += int(f_n.size * 1.28)
        y += item_h
        draw.rectangle([M, y - 14, W - M, y - 12], fill=RULE)


def make_pin_c(d: dict, out_path: Path) -> None:
    """情報図版型。記事の裏取り済みデータを表・タイムライン・リストで見せる。"""
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    M = 72

    top, bottom = _c_body_top_bottom(draw, d, M)
    kind = d.get("kind", "table")
    if kind == "timeline":
        _draw_timeline(draw, d, M, top, bottom)
    elif kind == "list":
        _draw_list(draw, d, M, top, bottom)
    else:
        _draw_table(draw, d, M, top, bottom)
    _c_footer(draw, d, M)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=88)


# --------------------------------------------------------------------------- P型（写真）

def _cover(im: Image.Image) -> Image.Image:
    """1000×1500 に合わせる。assets_en の写真は 2:3 で書き出してある前提だが、
    比率が違うものが混ざっても中央基準で切って必ず 2:3 にする。"""
    im = im.convert("RGB")
    sw, sh = im.size
    scale = max(W / sw, H / sh)
    im = im.resize((max(W, int(sw * scale + 0.5)), max(H, int(sh * scale + 0.5))), Image.LANCZOS)
    nw, nh = im.size
    left, top = (nw - W) // 2, (nh - H) // 2
    return im.crop((left, top, left + W, top + H))


def make_pin_photo(photo_path: Path, d: dict, out_path: Path) -> None:
    """写真型。写真を主役にし、下1/3に暗いグラデーションを敷いて文字を載せる。

    上部にロゴを置かないのは、assets_en の写真が「上1/3が単調なもの」を選ぶ前提ではなく、
    2:3 で書き出しただけのものだから。**下から重ねるほうが被写体を殺さない。**
    """
    img = _cover(Image.open(photo_path))

    # 下から上へ抜ける黒のグラデ。文字の可読性はここだけで確保する（写真に色は足さない）
    grad = Image.new("L", (1, H))
    for y in range(H):
        t = y / H
        # 下62%を暗く落とす。明るい空や砂地の写真でも白文字が読めるだけの濃度を確保する
        # （0.45始まり・指数1.5では、青空が入った写真で見出し上部が沈まなかった）
        a = 0 if t < 0.38 else ((t - 0.38) / 0.62) ** 1.15 * 238
        grad.putpixel((0, y), int(a))
    img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, grad.resize((W, H)))

    draw = ImageDraw.Draw(img)
    M = 78

    # 下端から積み上げる。BOTTOM_SAFE より下には置かない（運用仕様 §5-1）
    y_bottom = H - BOTTOM_SAFE

    brand_f = sans(34, "bold")
    draw.text((M, y_bottom), "The Japan Desk", font=brand_f, fill=SKY)

    sub = str(d.get("sub", "")).strip()
    sub_f = sans(33, "medium")
    y_sub = y_bottom - 26 - (44 if sub else 0)
    if sub:
        # 文字数ではなく実測幅で切る（英語は語ごとの幅差が大きく、字数だと右端をはみ出す）
        max_w = W - M * 2
        if draw.textlength(sub, font=sub_f) > max_w:
            words = sub.split()
            while words and draw.textlength(" ".join(words) + "…", font=sub_f) > max_w:
                words.pop()
            sub = " ".join(words) + "…"
        draw.text((M, y_sub), sub, font=sub_f, fill=(214, 222, 231))

    # 見出しは残りの高さいっぱいまで大きくする（写真の上に小さく載せると読まれない）
    top_limit = int(H * 0.44)
    avail = y_sub - 34 - top_limit
    f_t, lines, lh = fit(draw, d["title"], W - M * 2, avail,
                         [104, 94, 84, 76, 68, 60, 54], 5)
    y = y_sub - 34 - len(lines) * lh
    for ln in lines:
        draw.text((M, y), ln, font=f_t, fill=WHITE)
        y += lh

    # 見出しの上に細い朱の罫。写真とテキストの境目を作る
    draw.rectangle([M, y_sub - 34 - len(lines) * lh - 40, M + 150, y_sub - 34 - len(lines) * lh - 33],
                   fill=VERMILION)

    eyebrow = str(d.get("eyebrow", "")).upper()
    if eyebrow:
        tracked(draw, (M, y_sub - 34 - len(lines) * lh - 96), eyebrow, sans(26, "bold"), (236, 176, 162), track=5)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=88)
