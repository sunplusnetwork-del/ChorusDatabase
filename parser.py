#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

VOICING_BRACKET_RE = re.compile(r"[\[［【](混声|男声|女声|同声|児童)[\]］】]")
PIECE_LINE_RE = re.compile(r"^(?P<code>[GMFEＧＭＦＥ][0-9０-９]+)\s*(?P<rest>.+)$")
_FULLWIDTH_CODE_MAP = str.maketrans("ＧＭＦＥ０１２３４５６７８９", "GMFE0123456789")

def normalize_piece_code(code):
    return code.translate(_FULLWIDTH_CODE_MAP)

COLLECTION_RE = re.compile(r"[（(][「｢](?P<collection>[^」｢]+)[」｢｣](?:から|より)[）)]")
ORIGINAL_AUTHOR_RE = re.compile(r"[（(]原文[:：](?P<original>[^）)]+)[）)]")
CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")

_PARTICLES = {"da", "di", "de", "del", "della", "dei", "von", "van",
              "der", "den", "le", "la", "do", "dos", "das", "y"}
_CAP_WORD_RE = re.compile(r"^[A-ZÀ-ÝŒ][\wÀ-ÖØ-öø-ÿ''\-\.]*$")

_SEGMENT_MARKERS = [
    ("詩曲", "both"), ("訳詩", "translator"), ("編曲", "arranger"),
    ("採譜", "transcriber"), ("詩", "lyricist"), ("曲", "composer"),
]

def has_cjk(s):
    return bool(CJK_RE.search(s))

def normalize(text):
    return text.replace("\u3000", " ").strip()

def classify_segment(seg):
    seg = seg.strip()
    for marker, kind in _SEGMENT_MARKERS:
        if seg.endswith(marker):
            return kind, seg[: -len(marker)].strip()
    return "unknown", seg

def split_title_and_name(body):
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

def parse_piece_line(code, rest):
    rest = normalize(rest)
    result = {
        "piece_code": normalize_piece_code(code),
        "title": None, "collection": None, "lyricist": None,
        "original_author": None, "composer": None,
        "is_arrangement": False, "raw_text": rest,
        "notes": None, "confidence": 0.0,
    }

    m = COLLECTION_RE.search(rest)
    if m:
        result["collection"] = m.group("collection")
        rest = normalize(rest[: m.start()] + rest[m.end():])

    m = ORIGINAL_AUTHOR_RE.search(rest)
    if m:
        result["original_author"] = m.group("original")
        rest = normalize(rest[: m.start()] + rest[m.end():])

    # ／がない場合のみ括弧囲み形式を試みる（受賞情報括弧への誤マッチ防止）
    wrap_m = None
    if "／" not in rest:
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
        segments = [s.strip() for s in rest.split("／") if s.strip()]
        if not segments:
            result["title"] = rest
            result["confidence"] = 0.2
            return result
        classified = [classify_segment(s) for s in segments]
        kind0, val0 = classified[0]
        if kind0 == "unknown":
            title = val0
            title_confidence = 1.0
            credit_segments = classified[1:]
        else:
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


def parse_block(text):
    """<br>由来の継続行を結合してからパースする"""
    merged_lines = []
    in_piece_section = False

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("※") and in_piece_section:
            break
        if VOICING_BRACKET_RE.match(line):
            in_piece_section = True
            merged_lines.append(line)
        elif PIECE_LINE_RE.match(line):
            in_piece_section = True
            merged_lines.append(line)
        elif in_piece_section and merged_lines:
            prev = merged_lines[-1]
            last_c = prev[-1] if prev else ""
            first_c = line[0] if line else ""
            sep = "" if (has_cjk(last_c) or has_cjk(first_c)) else " "
            merged_lines[-1] = prev + sep + line

    pieces = []
    current_voicing = None
    for line in merged_lines:
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
    "マジャール語": "hu", "日本語": "ja", "アイヌ語": None,
}

def extract_footnote_metadata(text):
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
