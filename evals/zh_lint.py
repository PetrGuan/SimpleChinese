"""Conservative Chinese text measurements, not a readability or authorship judge."""

import re


SLOP = ("值得注意的是", "总而言之", "综上所述", "希望对你有帮助", "好问题", "意义重大", "至关重要", "无缝赋能")
FENCE = re.compile(r"^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$", re.M | re.S)
INLINE = re.compile(r"(`+)(.+?)\1")
BULLET = re.compile(r"^\s*(?:\d+[.)]|[-+*])\s+")
TOKENS = re.compile(
    r"[\u3400-\u9fff〇]|"
    r"\d+(?:[.:]\d+)*(?:\s*(?:毫秒|分钟|小时|秒|天|字节|份|台|个|项|核|页|行|次|MB|GB|KB|ms|%))?|"
    r"[A-Za-z]+(?:[._/-][A-Za-z0-9]+)*"
)


def plain_code(text, atom=""):
    return INLINE.sub(atom, FENCE.sub("", text))


def collapse_parentheses(text):
    out, depth = [], 0
    for char in text:
        if char in "（(":
            if depth == 0:
                out.append("〇")
            depth += 1
        elif char in "）)" and depth:
            depth -= 1
        elif not depth:
            out.append(char)
    # An unmatched bracket must not hide the rest of a sentence.
    return "".join(out) if depth == 0 else text


def count_units(text):
    text = collapse_parentheses(plain_code(text, "〇"))
    return len(TOKENS.findall(text))


def sentences(text):
    text = plain_code(text, "〇")
    text = re.sub(r"^#{1,6}\s+.*$", "", text, flags=re.M)
    text = re.sub(r"^\s*(?:\d+[.)]|[-+*])\s+", "", text, flags=re.M)
    text = collapse_parentheses(text)
    return [part.strip() for part in re.split(r"[。！？!?\n]+|(?<!\d)\.(?=\s|$)", text) if count_units(part)]


def list_items(text):
    groups, current = [], None
    for line in FENCE.sub("", text).splitlines():
        if BULLET.match(line):
            if current is not None:
                groups.append(current)
            current = BULLET.sub("", line)
        elif current is not None and line.startswith(("  ", "\t")) and line.strip():
            current += " " + line.strip()
        else:
            if current is not None:
                groups.append(current)
                current = None
    if current is not None:
        groups.append(current)
    return groups


def measure(text, scenario):
    visible = text
    for literal in sorted(scenario.get("protected", []), key=len, reverse=True):
        visible = visible.replace(literal, "")
    visible = plain_code(visible)
    lengths = [count_units(part) for part in sentences(text)]
    strict_text = text
    for literal in scenario.get("protected", []):
        # Preserve warning/error wording even if it exceeds a strict limit.
        if literal.startswith(("警告：", "请确认：")) or "Error:" in literal:
            strict_text = strict_text.replace(literal, "")
    strict = scenario["register"] == "document" and scenario["mode"] == "strict"
    limit = 30 if scenario["kind"] == "procedure" else 40
    return {
        "output_chars": len(text.strip()),
        "sentences": len(lengths),
        "mean_sentence_units": sum(lengths) / len(lengths) if lengths else None,
        "em_dashes": len(re.findall("——|—", visible)),
        "bold_spans": len(re.findall(r"\*\*[^*\n]+\*\*|__[^_\n]+__", visible)),
        "headings": len(re.findall(r"^#{1,6}\s", visible, re.M)),
        "list_items": len(list_items(text)),
        "exclamations": len(re.findall("[!！]", visible)),
        "slop_candidates": sum(visible.count(term) for term in SLOP),
        "missing_spaces": len(re.findall(r"[\u3400-\u9fff][A-Za-z0-9]|[A-Za-z0-9][\u3400-\u9fff]", visible)),
        "parenthetical_explanations": len(re.findall(r"（[^）]*）|\([^)]*\)", plain_code(text))),
        "protected_missing": [literal for literal in scenario.get("protected", []) if literal not in text],
        "strict_sentence_over_limit": sum(count_units(part) > limit for part in sentences(strict_text)) if strict else None,
        "strict_list_over_limit": sum(count_units(item) > limit for item in list_items(strict_text)) if strict else None,
    }
