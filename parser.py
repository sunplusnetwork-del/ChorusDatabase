#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全日本合唱連盟「合唱名曲シリーズ（課題曲集）」テキストのパーサー。
クローラー本体（jca_meikyoku_crawler.py）から import して使う。

v2: 2018〜2025年度（No.48〜No.53）の実データ6エディション分で検証済み。
表記が年度によってかなり揺れることが判明したため、「／」区切りの各セグメントを
末尾マーカー（詩／訳詩／曲／編曲／詩曲／採譜）で分類する方式に書き換えてある。

対応できていないもの（既知の制約）:
- 小学校編（E1〜E6等）は「（作詞者 詩／作曲者 曲）」のように全体を更に
  外側の括弧で囲む別フォーマットを使っており、本パーサーは未対応。
  混声・男声・女声（G/M/F）のレギュラー版のみが対象。
"""
import re

# --- 声部見出し（全角／半角どちらの括弧にも対応） ---
VOICING_BRACKET_RE = re.compile(r"[\[［【](混声|男声|女声|同声|児童)[\]］】]")

# --- 曲目1行のパターン（全角コード Ｇ１ にも対応、後で半角に正規化する） ---
PIECE_LINE_RE = re.compile(r"^(?P<code>[GMFEＧＭＦＥ][0-9０-９]+)\s*(?P<rest>.+)$")
_FULLWIDTH_CODE_MAP = str.maketrans("ＧＭＦＥ０１２３４５６７８９", "GMFE0123456789")


def normalize_piece_code(code: str) -> str:
    return code.translate(_FULLWIDTH_CODE_MAP)


# --- 曲集名・原詩注記（全角/半角の括弧・かぎ括弧どちらにも対応） ---
COLLECTION_RE = re.compile(r"[（(][「｢](?P<collection>[^」｢]+)[」｢｣](?:から|より)[）)]")
ORIGINAL_AUTHOR_RE = re.compile(r"[（(]原文[:：](?P<original>[^）)]+)[）)]")

CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")

_PARTICLES = {"da", "di", "de", "del", "della", "dei", "von", "van",
              "der", "den", "le", "la", "do", "dos", "das", "y"}
_CAP_WORD_RE = re.compile(r"^[A-ZÀ-ÝŒ][\wÀ-ÖØ-öø-ÿ''\-\.]*$")

# --- ／で区切られた1セグメントの末尾マーカー判定 ---
# 判定順序が重要：より長い・より具体的なマーカーを先にチェックする
# （例: "訳詩"は"詩"でも終わるので、先に"訳詩"を確認しないと誤判定する）
_SEGMENT_MARKERS = [
    ("詩曲", "both"),
    ("訳詩", "translator"),
    ("編曲", "arranger"),
    ("採譜", "transcriber"),
    ("詩", "lyricist"),
    ("曲", "composer"),
]


def has_cjk(s: str) -> bool:
    return bool(CJK_RE.search(s))


def normalize(text: str) -> str:
    """全角スペース統一・NFKC正規化はしない（人名の表記揺れを壊すため、空白のみ統一）"""
    return text.replace("\u3000", " ").strip()


def classify_segment(seg: str):
    """
    ／で分割した1セグメントの末尾マーカーを判定し (kind, name) を返す。
    kind: 'lyricist' | 'translator' | 'composer' | 'arranger' | 'both' |
          'transcriber' | 'unknown'（マーカーなし＝主にタイトル本体）
    """
    seg = seg.strip()
    for marker, kind in _SEGMENT_MARKERS:
        if seg.endswith(marker):
            return kind, seg[: -len(marker)].strip()
    return "unknown", seg


def split_title_and_name(body: str):
    """
    body から「曲名」と「人名」を分離する（／の無い1セグメント内で、
    タイトルと人名がスペースだけで連結されている場合に使う）。

    信頼性の方針:
    - 末尾の1単語が漢字仮名を含む（＝日本語人名）場合は、スペース無しの
      1トークンとして確実に分離できるため、高い confidence を返す。
    - 末尾が欧文の場合、複数語からなる人名の境界判定は正規表現だけでは
      原理的に確実ではない（ドイツ語は名詞をすべて大文字で書くため、
      "Das edle Herz" のようなタイトルと人名の判別が構造的に不可能な
      ケースがある）。そのため欧文の場合は best-effort 推定とし、
      confidence を意図的に低めに設定して人間によるPR修正を前提とする。
    """
    tokens = [t for t in body.split(" ") if t]
    if not tokens:
        return None, None, 0.3

    last_token = tokens[-1]
    if has_cjk(last_token):
        name = last_token
        title = " ".join(tokens[:-1]).strip()
        return title or None, name, 0.95

    if not _CAP_WORD_RE.match(last_token):
        return None, None, 0.4

    boundary = len(tokens) - 1
    i = len(tokens) - 2
    while i >= 0 and (tokens[i] in _PARTICLES or _CAP_WORD_RE.match(tokens[i])):
        boundary = i
        i -= 1

    if boundary == 0:
        return None, None, 0.4

    title = " ".join(tokens[:boundary]).strip()
    name = " ".join(tokens[boundary:]).strip()
    return title or None, name, 0.5


def parse_piece_line(code: str, rest: str):
    """1行分の曲情報をパースする。"""
    rest = normalize(rest)
    result = {
        "piece_code": normalize_piece_code(code),
        "title": None,
        "collection": None,
        "lyricist": None,
        "original_author": None,
        "composer": None,
        "is_arrangement": False,
        "raw_text": rest,
        "notes": None,
        "confidence": 0.0,
    }

    m = COLLECTION_RE.search(rest)
    if m:
        result["collection"] = m.group("collection")
        rest = normalize(rest[: m.start()] + rest[m.end():])

    m = ORIGINAL_AUTHOR_RE.search(rest)
    if m:
        result["original_author"] = m.group("original")
        rest = normalize(rest[: m.start()] + rest[m.end():])

    # --- 古い年度（No.48以前など）で使われる「全体を括弧で囲む」形式に対応 ---
    # 例: "Ave Maria （Tomás Luis de Victoria 曲）"
    #     "蜂が一ぴき…（「無声慟哭」から） （宮沢賢治 詩／林 光 曲）"
    # 末尾が "（...詩|曲...）" で終わっている場合のみ、この形式とみなす
    # （"Dies sanctificatus（1563）" のように曲名側の付帯括弧で終わる行とは、
    # 　末尾が閉じ括弧で終わるかどうかでは区別できないため、括弧内に
    # 　詩／曲系のマーカーが含まれているかどうかで判定する）
    wrap_m = re.search(r"[（(](?P<credit>[^（）()]*(?:詩|曲)[^（）()]*)[）)]\s*$", rest)
    if wrap_m:
        title = normalize(rest[: wrap_m.start()])
        credit_text = wrap_m.group("credit")
        segments = [s.strip() for s in credit_text.split("／") if s.strip()]
        classified = [classify_segment(s) for s in segments]
        result["title"] = title or None
        title_confidence = 1.0
        credit_segments = classified
    else:
        title = None
        title_confidence = None
        credit_segments = None

    if credit_segments is None:
        segments = [s.strip() for s in rest.split("／") if s.strip()]
        if not segments:
            result["title"] = rest
            result["confidence"] = 0.2
            return result

        classified = [classify_segment(s) for s in segments]
        kind0, val0 = classified[0]

        if kind0 == "unknown":
            # ／で綺麗にタイトルと人名が分かれている（多くの年度のスタイル）
            title = val0
            title_confidence = 1.0
            credit_segments = classified[1:]
        else:
            # 先頭セグメント自体にマーカーが付いている＝タイトルと人名が
            # スペースだけで連結されている（2025年度などのスタイル）
            title, name, title_confidence = split_title_and_name(val0)
            if title is None:
                title = val0
            credit_segments = [(kind0, name)] + classified[1:]

        result["title"] = title

    lyricist = None
    composer = None
    original_author = result["original_author"]
    is_arrangement = False
    notes_parts = []
    unknown_extra = []
    pending_original = None

    for kind, name in credit_segments:
        if name is None:
            unknown_extra.append("(分離不能)")
            continue
        if kind == "lyricist":
            pending_original = name
            lyricist = name
        elif kind == "translator":
            original_author = pending_original or original_author
            lyricist = name
            pending_original = None
        elif kind == "composer":
            composer = name
        elif kind == "arranger":
            composer = name
            is_arrangement = True
        elif kind == "both":
            lyricist = name
            composer = name
        elif kind == "transcriber":
            notes_parts.append(f"採譜: {name}")
        else:
            unknown_extra.append(name)

    result["lyricist"] = lyricist
    result["composer"] = composer
    result["original_author"] = original_author
    result["is_arrangement"] = is_arrangement

    # --- 「composer名の中に “○○ 詩 ○○” が埋め込まれている」パターンの救済 ---
    # 例: "阪田寛夫 詩 大中 恩"（／ ではなくスペースで詩と曲が連結される年度がある）
    # 「詩」の前後に明示的な空白がある場合のみ分離する
    # （"ドイツ語訳詩"のような複合語の "詩" を誤って分離しないため）
    if lyricist is None and composer:
        embedded = re.match(r"^(?P<lyr>.+?)\s詩\s(?P<comp>.+)$", composer)
        if embedded:
            result["lyricist"] = embedded.group("lyr").strip()
            result["composer"] = embedded.group("comp").strip()

    if notes_parts:
        result["notes"] = "; ".join(notes_parts)

    confidence = title_confidence
    if composer is None:
        confidence = min(confidence, 0.3)
    if unknown_extra:
        confidence = min(confidence, 0.5)

    result["confidence"] = round(confidence, 2)
    return result


def parse_block(text: str):
    """声部見出しで区切られた複数行のテキストをまとめてパースする"""
    pieces = []
    current_voicing = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        vm = VOICING_BRACKET_RE.match(line)
        if vm:
            current_voicing = vm.group(1)
            continue
        pm = PIECE_LINE_RE.match(line)
        if pm:
            parsed = parse_piece_line(pm.group("code"), pm.group("rest"))
            parsed["voicing_category"] = current_voicing
            pieces.append(parsed)
    return pieces


# --- 脚注（言語・伴奏）の抽出 ---
_CODE = r"[GMFEＧＭＦＥ][0-9０-９]+"
LANG_FOOTNOTE_RE = re.compile(
    rf"(?P<codes>(?:{_CODE}[、,]?)+)は(?P<lang>ラテン語|ドイツ語|フランス語|イタリア語|"
    rf"英語|スウェーデン語|フィンランド語|マジャール語|日本語|アイヌ語)"
)
ACCOMP_FOOTNOTE_RE = re.compile(
    rf"(?P<codes>(?:{_CODE}[、,]?)+)は(?P<accomp>ピアノ伴奏|無伴奏)"
)

_LANG_TO_ISO = {
    "ラテン語": "la", "ドイツ語": "de", "フランス語": "fr", "イタリア語": "it",
    "英語": "en", "スウェーデン語": "sv", "フィンランド語": "fi",
    "マジャール語": "hu", "日本語": "ja", "アイヌ語": None,  # ISO 639-1に無いためNone
}


def extract_footnote_metadata(text: str):
    """
    ブロック本文中の「※G1、M1、F1はラテン語」のような脚注から、
    曲記号ごとの言語・伴奏情報を抽出する。
    戻り値: {"language": {code: iso}, "accompaniment": {code: "ピアノ伴奏"|"無伴奏"}}
    """
    language = {}
    accompaniment = {}

    for m in LANG_FOOTNOTE_RE.finditer(text):
        codes = [normalize_piece_code(c) for c in re.findall(_CODE, m.group("codes"))]
        iso = _LANG_TO_ISO.get(m.group("lang"))
        for c in codes:
            language[c] = iso if iso else m.group("lang")

    for m in ACCOMP_FOOTNOTE_RE.finditer(text):
        codes = [normalize_piece_code(c) for c in re.findall(_CODE, m.group("codes"))]
        for c in codes:
            accompaniment[c] = m.group("accomp")

    return {"language": language, "accompaniment": accompaniment}
