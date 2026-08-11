# pinterest-kit/photos_en.py
# 写真ピン用の在庫管理。**同じピンには常に同じ写真を割り当てる**のが最重要の性質。
#
# なぜ固定するのか: Pinterest の「フレッシュピン」判定はアップロード済みの画像かどうかで決まる。
# 生成のたびに写真がシャッフルされると、既に投稿したピンの画像が差し替わり、
# 「同じURLに違う画像」「同じ写真が別のピンにも」の両方が起きる。台帳で固定して防ぐ。
#
# 台帳 state_en/used_photos.json:
#   { "<ピンのファイル名(拡張子なし)>": {"sha": "<写真の中身のSHA-256>", "src": "<フォルダ/ファイル名>"} }
# 判定は**中身のハッシュ**なので、写真をリネームしても二重使用を検出できる。

from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets_en" / "thejapandesk"
STATE = ROOT / "state_en" / "used_photos.json"
EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class PhotoPool:
    def __init__(self) -> None:
        self.ledger: dict[str, dict] = json.loads(STATE.read_text()) if STATE.exists() else {}
        # 相対パスで持つ。`kyoto` と `kyoto/autumn` のどちらの指定でも前方一致で解決できる
        self.files: list[str] = []
        self.sha: dict[str, str] = {}
        if ASSETS.exists():
            for f in sorted(ASSETS.rglob("*")):
                if f.suffix.lower() not in EXTS:
                    continue
                rel = str(f.relative_to(ASSETS))
                self.files.append(rel)
                self.sha[rel] = _sha(f)
        self.by_sha: dict[str, str] = {v: k for k, v in self.sha.items()}
        self.used: set[str] = {v["sha"] for v in self.ledger.values()}
        self.warnings: list[str] = []

    @staticmethod
    def _in(rel: str, folders: list[str]) -> bool:
        return any(rel == f or rel.startswith(f.rstrip("/") + "/") for f in folders)

    def take(self, pin_stem: str, folders: list[str]) -> Path | None:
        """pin_stem に割り当てる写真を返す。既に割り当て済みで、かつその写真が
        **今の対応表の範囲内にあるなら**それを再利用する（再実行しても同じ絵になる）。
        対応表を直して範囲外になった場合は割り当てを外して選び直す。"""
        rec = self.ledger.get(pin_stem)
        if rec:
            hit = self.by_sha.get(rec["sha"])
            if hit and self._in(hit, folders):
                return ASSETS / hit
            if hit:
                self.warnings.append(
                    f"[再割当] {pin_stem}: {hit} は対応表の {folders} の外になったので選び直す")
            else:
                self.warnings.append(
                    f"[写真消失] {pin_stem} に割り当てていた {rec['src']} が見つからない。選び直す")
            self.used.discard(rec["sha"])
            del self.ledger[pin_stem]

        for folder in folders:                    # 対応表の順に探す
            for rel in self.files:
                if not self._in(rel, folder if isinstance(folder, list) else [folder]):
                    continue
                s = self.sha[rel]
                if s in self.used:
                    continue
                self.used.add(s)
                self.ledger[pin_stem] = {"sha": s, "src": rel}
                return ASSETS / rel
        return None

    def available(self, folders: list[str], own_stems: list[str]) -> int:
        """folders 内で使える枚数。**自分自身に割り当て済みのぶんは空きとして数える**
        （再実行時に「もう使われている」と判定して自分の写真を失わないため）。"""
        mine = {self.ledger[s]["sha"] for s in own_stems if s in self.ledger}
        return sum(1 for r in self.files
                   if self._in(r, folders) and (self.sha[r] not in self.used or self.sha[r] in mine))

    def stock(self) -> dict[str, tuple[int, int]]:
        """トップレベルのフォルダ名 -> (未使用, 総数)"""
        out: dict[str, list[int]] = {}
        for d in sorted(p for p in ASSETS.iterdir() if p.is_dir()):
            rels = [r for r in self.files if self._in(r, [d.name])]
            out[d.name] = [sum(1 for r in rels if self.sha[r] not in self.used), len(rels)]
        return {k: (v[0], v[1]) for k, v in out.items()}

    def save(self) -> None:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(self.ledger, ensure_ascii=False, indent=1, sort_keys=True))
