#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parser.py の回帰テスト。全日本合唱連盟「合唱名曲シリーズ」課題曲集、
No.48〜No.53（2018〜2025年度、計72曲）の実データを fixture として使用する。

実行方法:
    cd crawler && python3 test_parser.py

将来 parser.py を改修する際は、このテストを通してから commit / PR すること。
低信頼度（confidence < 0.6）として扱われるケースは「壊れている」のではなく
「自動分離を諦めて人間のレビューに委ねている」意図的な仕様。72曲中8曲が
これに該当するが、いずれも以下のような構造的に確実な判定が不可能なケース
であることを確認済み（詳細は README.md の「confidenceについて」を参照）:
  - ドイツ語タイトルの曲（独語は名詞を全て大文字で書くため、欧文タイトルと
    人名の境界が正規表現だけでは判定不能）
  - 採譜者・原典（アイヌ民謡、古今和歌集など）が人名と別に記載されている曲
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parser import parse_block, extract_footnote_metadata  # noqa: E402
from fixtures.raw_editions import EDITIONS  # noqa: E402


def by_code(results, code):
    for r in results:
        if r["piece_code"] == code:
            return r
    raise KeyError(code)


def run():
    failures = []

    def check(label, cond):
        if not cond:
            failures.append(label)

    all_results = {}
    for no, ed in EDITIONS.items():
        all_results[no] = parse_block(ed["text"])
        check(f"No.{no}: 曲数が12件である", len(all_results[no]) == 12)

    # --- No.53（2025年度）：日本語は高信頼度、欧文は意図的に低信頼度 ---
    r53 = all_results[53]
    g3 = by_code(r53, "G3")
    check("No.53 G3 title", g3["title"] == "秋の午後")
    check("No.53 G3 collection", g3["collection"] == "光る砂漠")
    check("No.53 G3 composer", g3["composer"] == "萩原英彦")
    check("No.53 G3 confidence高い", g3["confidence"] >= 0.9)

    f4 = by_code(r53, "F4")
    check("No.53 F4 original_author", f4["original_author"] == "Heinrich Heine")
    check("No.53 F4 composer", f4["composer"] == "平木悟")

    g1 = by_code(r53, "G1")
    check("No.53 G1 composer(欧文/区切り無し)", g1["composer"] == "Giovannni Pierluigi da Palestrina")

    m2 = by_code(r53, "M2")
    check("No.53 M2 composerは正しい", m2["composer"] == "Hugo Wolf")
    check("No.53 M2 confidenceは低い(独語タイトルの罠)", m2["confidence"] < 0.6)

    # --- No.52（2023年度）：title／lyricist詩／composer曲 の3分割形式 ---
    r52 = all_results[52]
    f3 = by_code(r52, "F3")
    check("No.52 F3 title", f3["title"] == "ねむの花")
    check("No.52 F3 lyricist", f3["lyricist"] == "壺田花子")
    check("No.52 F3 composer", f3["composer"] == "中田喜直")
    check("No.52 F3 confidence高い", f3["confidence"] >= 0.9)

    m3 = by_code(r52, "M3")
    check("No.52 M3 訳詩(original_author)", m3["original_author"] == "Paul Verlaine")
    check("No.52 M3 lyricist(訳者が採用される)", m3["lyricist"] == "堀口大學")
    check("No.52 M3 composer", m3["composer"] == "南 弘明")

    g2 = by_code(r52, "G2")
    check("No.52 G2 編曲フラグ", g2["is_arrangement"] is True)
    check("No.52 G2 composer(編曲者)", g2["composer"] == "Brian Trant")

    g4 = by_code(r52, "G4")
    check("No.52 G4 詩曲(同一人物)", g4["lyricist"] == g4["composer"] == "村本晋也")

    # --- No.50/49（title／lyricist 詩 composer 曲 のスペース連結形式） ---
    r50 = all_results[50]
    g3_50 = by_code(r50, "G3")
    check("No.50 G3 lyricist(スペース連結)", g3_50["lyricist"] == "阪田寛夫")
    check("No.50 G3 composer(スペース連結)", g3_50["composer"] == "大中 恩")
    check("No.50 G3 confidence高い", g3_50["confidence"] >= 0.9)

    r49 = all_results[49]
    g3_49 = by_code(r49, "G3")
    check("No.49 G3 lyricist", g3_49["lyricist"] == "岸田衿子")
    check("No.49 G3 composer", g3_49["composer"] == "津田 元")

    # --- No.48（2018年度）：全体を括弧で囲む旧形式 ---
    r48 = all_results[48]
    check("No.48 全曲検出", len(r48) == 12)
    g1_48 = by_code(r48, "G1")
    check("No.48 G1 title(括弧形式)", g1_48["title"] == "Ave Maria")
    check("No.48 G1 composer(括弧形式)", g1_48["composer"] == "Tomás Luis de Victoria")
    check("No.48 G1 confidence高い", g1_48["confidence"] >= 0.9)

    g3_48 = by_code(r48, "G3")
    check("No.48 G3 title(括弧形式+収録曲集)", g3_48["title"] == "蜂が一ぴき…")
    check("No.48 G3 collection", g3_48["collection"] == "無声慟哭")
    check("No.48 G3 lyricist", g3_48["lyricist"] == "宮沢賢治")
    check("No.48 G3 composer", g3_48["composer"] == "林 光")

    # --- No.51：採譜者・出典のみ（人名でない）segmentの扱い ---
    r51 = all_results[51]
    m3_51 = by_code(r51, "M3")
    check("No.51 M3 composerは正しい", m3_51["composer"] == "清水脩")
    check("No.51 M3 notesに採譜者が記録される", "近藤鏡二郎" in (m3_51["notes"] or ""))
    check("No.51 M3 confidenceは低い(採譜者ありのため要レビュー)", m3_51["confidence"] < 0.6)

    # --- 全体の品質指標：高信頼度の割合がある程度を維持していること ---
    all_pieces = [p for results in all_results.values() for p in results]
    high_conf = sum(1 for p in all_pieces if p["confidence"] >= 0.9)
    check(f"高信頼度(>=0.9)が72曲中50曲以上 (実際: {high_conf})", high_conf >= 50)

    # --- 脚注（言語・伴奏）抽出 ---
    fn53 = extract_footnote_metadata(EDITIONS[53]["text"])
    check("No.53 脚注 G1=la", fn53["language"].get("G1") == "la")
    check("No.53 脚注 G2=de", fn53["language"].get("G2") == "de")
    check("No.53 脚注 G3=ピアノ伴奏", fn53["accompaniment"].get("G3") == "ピアノ伴奏")

    fn50 = extract_footnote_metadata(EDITIONS[50]["text"])
    check("No.50 脚注 F3=無伴奏(例外注記)", fn50["accompaniment"].get("F3") == "無伴奏")

    if failures:
        print(f"FAILED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        total = sum(len(r) for r in all_results.values())
        print(f"OK: {total}曲（6エディション）すべて期待通り")


if __name__ == "__main__":
    run()
