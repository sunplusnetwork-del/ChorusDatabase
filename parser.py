def parse_block(text: str):
    """声部見出しで区切られた複数行のテキストをまとめてパースする"""
    # <br>由来の改行で分断された継続行を前の行に結合する
    merged_lines = []
    in_piece_section = False

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # ※脚注行に達したら声部セクション終了（正誤表等の混入防止）
        if line.startswith("※") and in_piece_section:
            break
        if VOICING_BRACKET_RE.match(line):
            in_piece_section = True
            merged_lines.append(line)
        elif PIECE_LINE_RE.match(line):
            in_piece_section = True
            merged_lines.append(line)
        elif in_piece_section and merged_lines:
            # 継続行を結合（欧文の単語境界には空白を補う）
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
