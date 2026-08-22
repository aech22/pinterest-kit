#!/usr/bin/env python3
# pinterest-kit/sync_drive_en.py
# The Japan Desk の投稿キット（out_en/thejapandesk）を、マウント済みの Google Drive
# フォルダへ反映する。gen_en_kit.py の最後から呼ばれるので、生成すれば自動で上がる。
#
# なぜ OAuth（picknavi の gdrive_upload.py）ではなくマウント経由なのか:
#   picknavi は GitHub Actions から上げるので OAuth が要る。一方 The Japan Desk の
#   ピン生成は写真素材（assets_en・167MB・配布権が自明でないため .gitignore 済み）を
#   使うので CI では動かせず、生成は必ずローカルで走る。ローカルなら Drive デスクトップの
#   マウントへ普通のファイルコピーで届き、認証情報を1つも増やさずに済む。
#   さらに OAuth の drive.file スコープは「アプリが作ったファイル」しか触れないため、
#   手作業で作られた既存の投稿キットフォルダには書き込めない。マウント経由にはその制約が無い。
#
# 【不変方針】既にあるファイルは絶対に上書きしない。Pinterest は予約投稿・投稿済みの
#   中身を後から差し替えられないので、配ったものと手元が食い違う原因になる。
#   新しいファイルを足すだけ。削除もしない。
from __future__ import annotations
import csv, os, shutil, subprocess, sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "out_en" / "thejapandesk"
DEFAULT_DIR_NAME = "thejapandesk_Pinterest投稿キット"
# ローカルの posts/ は Drive 上では「投稿文」という名前で運用されている
SUBDIR_MAP = {"pins": "pins", "posts": "投稿文"}
CSV_FILES = {"social_kit.csv": "image_file", "posting_calendar.csv": None}


def find_drive_dir() -> Path | None:
    """マウント済みDrive内の投稿キットフォルダを探す。TJD_DRIVE_DIR で明示指定もできる。"""
    override = os.environ.get("TJD_DRIVE_DIR")
    if override:
        p = Path(override).expanduser()
        return p if p.is_dir() else None
    base = Path.home() / "Library" / "CloudStorage"
    for account in sorted(base.glob("GoogleDrive-*")):
        for root in ("マイドライブ", "My Drive"):
            cand = account / root / DEFAULT_DIR_NAME
            if cand.is_dir():
                return cand
    return None


def drive_is_running() -> bool:
    """Driveデスクトップが動いているか。

    止まっているとマウントは「最後に同期した時点の抜け殻」になり、そこへ書いても
    同期されないまま取り残されうる。取り残しは黙って起きるので、走っていないなら
    何もせずに理由を告げて終わる方が安全。
    """
    return subprocess.run(["pgrep", "-x", "Google Drive"],
                          capture_output=True).returncode == 0


def copy_new(src_dir: Path, dst_dir: Path) -> tuple[int, int]:
    """src にあって dst に無いファイルだけをコピーする。戻り値は (新規, 据え置き)。"""
    dst_dir.mkdir(parents=True, exist_ok=True)
    added = kept = 0
    for f in sorted(src_dir.iterdir()):
        if f.name.startswith(".") or not f.is_file():
            continue
        target = dst_dir / f.name
        if target.exists():
            kept += 1
            continue
        shutil.copy2(f, target)
        # コピー直後にサイズを突き合わせる。マウント越しの書き込みは静かに失敗しうる
        if target.stat().st_size != f.stat().st_size:
            raise IOError(f"コピー後のサイズが一致しない: {target}")
        print(f"  + {f.name}")
        added += 1
    return added, kept


def merge_csv(src: Path, dst: Path, key: str) -> None:
    """既存行を一字も変えずに残し、新しい行だけ追記する。

    social_kit.csv はピンタイトルと説明文（＝投稿文そのもの）を持つので、丸ごと
    置き換えると投稿済みの文面が変わる。逆に触らなければ新しいピンが索引に載らない。
    """
    with src.open(encoding="utf-8-sig", newline="") as f:
        new_rows = list(csv.DictReader(f))
    if not new_rows:
        return
    header = list(new_rows[0].keys())
    # キー列が無いまま進むと、既存行を1つも認識できないまま上書きして投稿済みの文面を失う。
    # 列名の取り違え（実際に一度やった）を書き込み前に止める。
    if key not in header:
        print(f"  [中止] {src.name}: キー列 '{key}' が無い（列: {', '.join(header)}）")
        return
    old: dict[str, dict] = {}
    if dst.exists():
        with dst.open(encoding="utf-8-sig", newline="") as f:
            rd = csv.DictReader(f)
            if key not in (rd.fieldnames or []):
                print(f"  [中止] 既存 {dst.name} にキー列 '{key}' が無いため触らない")
                return
            for r in rd:
                k = (r.get(key) or "").strip()
                if k:
                    old[k] = r
    merged, seen = [], set()
    for r in new_rows:
        k = (r.get(key) or "").strip()
        prev = old.get(k)
        merged.append({c: (prev[c] if prev and c in prev else r.get(c, "")) for c in header})
        seen.add(k)
    leftover = [r for k, r in old.items() if k not in seen]
    merged.extend({c: r.get(c, "") for c in header} for r in leftover)
    with dst.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(merged)
    print(f"  {dst.name}: 既存 {len(old)} 行を据え置き / 新規 {len(seen - set(old))} 行を追記 "
          f"/ 生成対象外で残した行 {len(leftover)}")


def main() -> int:
    if not SRC.is_dir():
        print(f"[SKIP] 生成物が無い: {SRC}")
        return 0
    dst = find_drive_dir()
    if dst is None:
        print(f"[SKIP] Drive上の「{DEFAULT_DIR_NAME}」が見つからない"
              "（TJD_DRIVE_DIR で明示指定できる）")
        return 0
    # 宛先を明示指定しているときはデーモン確認を省く。マウント以外（検証用の一時ディレクトリ、
    # 別の同期ツールの監視フォルダ等）を指している可能性があり、Drive の起動は前提にならない。
    if not os.environ.get("TJD_DRIVE_DIR") and not drive_is_running():
        print("[SKIP] Google Drive デスクトップが起動していないため反映を見送る。")
        print("       起動したまま `python3 sync_drive_en.py` を実行すれば追いつく。")
        return 0

    print(f"Drive へ反映: {dst}")
    total_added = total_kept = 0
    for local_name, drive_name in SUBDIR_MAP.items():
        src_dir = SRC / local_name
        if not src_dir.is_dir():
            continue
        a, k = copy_new(src_dir, dst / drive_name)
        print(f"  {drive_name}: 新規 {a} / 既存据え置き {k}")
        total_added += a
        total_kept += k

    for name, key in CSV_FILES.items():
        src_csv = SRC / name
        if not src_csv.exists():
            continue
        if key:
            merge_csv(src_csv, dst / name, key)
        else:
            # カレンダーは毎回すべて組み直す配分表で、投稿済みの文面を持たない
            shutil.copy2(src_csv, dst / name)
            print(f"  {name}: 更新（配分表なので毎回作り直す）")

    print(f"完了: 新規 {total_added} ファイル / 既存 {total_kept} ファイルはそのまま")
    return 0


if __name__ == "__main__":
    sys.exit(main())
