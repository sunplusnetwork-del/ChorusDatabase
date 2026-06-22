#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全日本合唱連盟「合唱名曲シリーズ（課題曲集）」の各エディションページを
直接巡回して課題曲データを抽出し、data/songs.json に追記するクローラー。

v2: エディションは https://jcanet.or.jp/Public/meikyoku/meikyoku-No{n}.htm
    という個別ページに分かれていることが（青森県合唱連盟・埼玉合唱連盟の
    告知ページからの逆引きで）確認できた。"過去の収録曲"のような単一の
    集約ページをパースする方式から、エディション番号を直接指定して
    1ページ＝1エディションとして取得する方式に変更している。

設計方針:
- 既存レコードは絶対に上書きしない（id が一致したものはスキップ）。
  これにより、コミュニティのPRで人間が手作業修正したデータを、
  次回の自動クロールが踏みつぶさない。
- confidence < 0.6 のレコードには needs_review: true を立てる。
- 通常運用（cronによる週次実行）では直近数エディションのみ再取得する
  （全エディションを毎週再取得するのは無駄なため）。
  初回セットアップ時は --start-no 1 --end-no 53 のように指定して
  全件バックフィルする想定。

既知の制約（README.md にも記載）:
  全日本合唱連盟サイトは Shift-JIS (cp932) で配信されており、
  Content-Type に charset が明示されていないため、明示的に cp932 で
  デコードする。また小学校編（E1〜E6等）は通常版（G/M/F）と異なる
  「全体を括弧で囲む」表記の亜種を使っており、parser.py は未対応。
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parser import parse_block, extract_footnote_metadata  # noqa: E402

EDITION_URL_TEMPLATE = "https://jcanet.or.jp/Public/meikyoku/meikyoku-No{n}.htm"
INDEX_URL = "https://jcanet.or.jp/Public/meikyoku/meikyoku-index.htm"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "songs.json"

# 2026年6月時点で確認できている最新号。--end-no 省略時のフォールバック。
# meikyoku-index.htm から自動検出できればそちらを優先する。
DEFAULT_LATEST_NO = 53
DEFAULT_LOOKBACK = 3  # 通常運用時、最新からさかのぼって再取得する件数

CATEGORY_LABEL = {"G": "混声", "M": "男声", "F": "女声", "E": "同声・児童"}


def fetch_html(url: str) -> str:
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; JCA-Choral-DB-Bot/1.0; "
                                 "+https://github.com/)"},
        timeout=30,
    )
    resp.raise_for_status()
    # サイトは charset 未指定の Shift-JIS で配信されているため明示的に指定する
    return resp.content.decode("cp932", errors="replace")


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    return soup.get_text("\n")


def discover_latest_edition_no(index_text: str):
    m = re.search(r"合唱名曲シリーズ\s*No\.?\s*(\d+)", index_text)
    return int(m.group(1)) if m else None


def extract_publication_year(text: str):
    """
    「発行日：2025年3月10日」のような表記、無ければ「2025年度」のような
    表記から発行年（≒その年度の課題曲集として使われる年）を推定する。
    確実な情報源ではないため best-effort。
    """
    m = re.search(r"発行[日]?[：:]?\s*(\d{4})年", text)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d{4})年度", text)
    if m:
        return int(m.group(1))
    return None


def make_id(edition_no, piece_code, title, composer) -> str:
    if edition_no and piece_code:
        return f"jca-no{edition_no}-{piece_code}"
    basis = f"{title}|{composer}".strip("|")
    h = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:10]
    return f"auto-{h}"


def to_song_record(piece: dict, *, edition_no: int, contest_year,
                    source_url: str, now: str, footnotes: dict) -> dict:
    code = piece["piece_code"]
    record_id = make_id(edition_no, code, piece["title"], piece["composer"])
    return {
        "id": record_id,
        "title": piece["title"],
        "title_yomi": None,
        "composer": piece["composer"],
        "lyricist": piece["lyricist"],
        "original_author": piece["original_author"],
        "arranger": piece["composer"] if piece["is_arrangement"] else None,
        "is_arrangement": piece["is_arrangement"],
        "collection": piece["collection"],
        "voicing_category": piece["voicing_category"] or CATEGORY_LABEL.get(code[0]),
        "voicing_detail": None,
        "language": footnotes.get("language", {}).get(code),
        "accompaniment": footnotes.get("accompaniment", {}).get(code),
        "source_type": "コンクール課題曲",
        "source_detail": {
            "contest_year": contest_year,
            "contest_round": None,
            "edition_no": edition_no,
            "piece_code": code,
        },
        "publisher": "全日本合唱連盟",
        "tags": [],
        "notes": piece["notes"],
        "needs_review": piece["confidence"] < 0.6,
        "confidence": piece["confidence"],
        "sources": [
            {"url": source_url, "retrieved_at": now, "raw_text": piece["raw_text"]}
        ],
        "created_at": now,
        "updated_at": now,
    }


def load_existing() -> list:
    if DATA_PATH.exists():
        with open(DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save(records: list):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
        f.write("\n")


def merge(existing: list, new_records: list):
    """既存レコードは一切上書きしない。新規IDのみ追加する。"""
    existing_ids = {r["id"] for r in existing}
    added = []
    for rec in new_records:
        if rec["id"] not in existing_ids:
            existing.append(rec)
            existing_ids.add(rec["id"])
            added.append(rec)
    return existing, added


def run(*, start_no=None, end_no=None, dry_run=False, save_raw_dir=None):
    if end_no is None:
        try:
            idx_text = extract_text(fetch_html(INDEX_URL))
            end_no = discover_latest_edition_no(idx_text) or DEFAULT_LATEST_NO
        except requests.RequestException as e:
            print(f"index取得失敗、デフォルト値 No.{DEFAULT_LATEST_NO} を使用: {e}",
                  file=sys.stderr)
            end_no = DEFAULT_LATEST_NO

    if start_no is None:
        start_no = max(1, end_no - DEFAULT_LOOKBACK + 1)

    now = datetime.now(timezone.utc).isoformat()
    new_records = []
    fetched, failed = 0, 0

    for n in range(start_no, end_no + 1):
        url = EDITION_URL_TEMPLATE.format(n=n)
        try:
            html = fetch_html(url)
        except requests.RequestException as e:
            print(f"No.{n}: 取得失敗（スキップ）: {e}", file=sys.stderr)
            failed += 1
            continue

        text = extract_text(html)
        if save_raw_dir:
            Path(save_raw_dir).mkdir(parents=True, exist_ok=True)
            (Path(save_raw_dir) / f"No{n}.txt").write_text(text, encoding="utf-8")

        pieces = parse_block(text)
        if not pieces:
            # G/M/F以外の構成（小学校編など）の可能性が高いのでスキップ
            print(f"No.{n}: 曲目を検出できず（スキップ; 小学校編など別フォーマットの可能性）")
            continue

        footnotes = extract_footnote_metadata(text)
        contest_year = extract_publication_year(text)
        fetched += 1

        for piece in pieces:
            new_records.append(to_song_record(
                piece, edition_no=n, contest_year=contest_year,
                source_url=url, now=now, footnotes=footnotes,
            ))

    print(f"取得成功: {fetched}エディション / 取得失敗: {failed}エディション")
    print(f"抽出曲数: {len(new_records)}")

    if dry_run:
        print("\n--- dry-run: 抽出結果（先頭15件） ---")
        for r in new_records[:15]:
            print(f"  [{r['id']}] {r['title']!r} / {r['composer']!r} "
                  f"(confidence={r['confidence']}, needs_review={r['needs_review']})")
        print("\ndry-run のため data/songs.json への書き込みは行っていません。")
        return new_records

    existing = load_existing()
    merged, added = merge(existing, new_records)
    save(merged)

    print(f"新規追加: {len(added)}件")
    print(f"うち要レビュー（confidence<0.6）: {sum(1 for r in added if r['needs_review'])}件")
    return added


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start-no", type=int, default=None,
                     help="開始エディション番号（省略時は最新からDEFAULT_LOOKBACK件）")
    ap.add_argument("--end-no", type=int, default=None,
                     help="終了エディション番号（省略時はmeikyoku-index.htmから自動検出）")
    ap.add_argument("--dry-run", action="store_true",
                     help="data/songs.json に書き込まず結果を表示するのみ")
    ap.add_argument("--save-raw-dir", metavar="DIR",
                     help="各エディションの抽出テキストをDIR配下に保存する（構造確認用）")
    args = ap.parse_args()

    try:
        run(start_no=args.start_no, end_no=args.end_no,
            dry_run=args.dry_run, save_raw_dir=args.save_raw_dir)
    except requests.RequestException as e:
        print(f"致命的な取得エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
