#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate public/data/questions/2023-yakkan.json from OCR tmp.md (Reiwa 5 / 2023)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "public/data/questions/tmp.md"
OUT = ROOT / "public/data/questions/2023-yakkan.json"

KEY = {"ア": "A", "イ": "B", "ウ": "C", "エ": "D"}

# Exam Q26–50 ← section-local answers (ア=A … エ=D)
ANSWERS: dict[int, list[str]] = {
    26: ["D"],  # 1(1) エ
    27: ["B"],  # 1(2) イ
    28: ["B"],  # 1(3) イ
    29: ["B"],  # 1(4) イ
    30: ["A"],  # 1(5) ア
    31: ["D"],  # 1(6) エ
    32: ["A"],  # 1(7) ア
    33: ["B"],  # 1(8) イ
    34: ["C"],  # 1(9) ウ
    35: ["B"],  # 1(10) イ
    36: ["C"],  # 1(11) ウ
    37: ["D"],  # 1(12) エ
    38: ["C"],  # 1(13) ウ
    39: ["D"],  # 1(14) エ
    40: ["D"],  # 1(15) エ
    41: ["C"],  # 1(16) ウ
    42: ["C"],  # 1(17) ウ
    43: ["D"],  # 1(18) エ
    44: ["A"],  # 1(19) ア
    45: ["A"],  # 1(20) ア
    46: ["D"],  # 2 エ
    47: ["A"],  # 3 ア
    48: ["C"],  # 4 ウ
    49: ["A"],  # 5 ア
    50: ["B"],  # 6 イ
}


def ocr_fix(raw: str) -> str:
    """Apply known OCR fixes from Reiwa-5 yakkan scan."""
    s = raw
    # Control chars (OCR stand-ins for １ / 「 / 」)
    s = s.replace("\x02つ", "１つ")
    s = s.replace("\x03", "「")
    s = s.replace("\x04", "」")
    # Garbled 募集型 at Q1: "1 集型" → "1 募集型" (keep question number)
    s = s.replace("1 集型", "1 募集型")
    # Unify dash in article titles
    s = s.replace("−", "－")
    # Missing inpatient-days digit in Q17-b (unreadable in OCR)
    s = re.sub(r"傷害による\s*日間の入院", "傷害による○日間の入院", s)
    # Halfwidth "1つ" → fullwidth (match other year JSONs)
    s = s.replace("1つ", "１つ")
    # Collapse OCR spaces around Arabic numerals in Japanese prose
    s = re.sub(r" +(?=\d)", "", s)
    s = re.sub(r"(?<=\d) +(?=\d)", "", s)
    s = re.sub(r"(?<=\d) +(?=[日月年月日人目円万泊])", "", s)
    # Fullwidth ideographic space → normal space for splitting, then strip later
    s = s.replace("\u3000", " ")
    return s


def soft_join(text: str) -> str:
    """Join mid-sentence line wraps; keep breaks before ａ–ｄ / （注 / ア–エ."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ""
    result = lines[0]
    for ln in lines[1:]:
        if re.match(r"^[ａｂｃｄ][.．]", ln) or re.match(r"^（注", ln) or re.match(
            r"^[ア-エ][.．]", ln
        ):
            result += "\n" + ln
        else:
            result += ln
    return result


def parse_choices(body: str) -> list[dict]:
    """Extract ア–エ choice bodies (no leading ア. prefix)."""
    joined = soft_join(body)
    choices: dict[str, str] = {}
    for m in re.finditer(r"([ア-エ])[.．]\s*(.*?)(?=(?:[ア-エ][.．])|$)", joined, re.S):
        key = KEY[m.group(1)]
        text = soft_join(m.group(2))
        text = re.sub(r"[ \t]+", "", text.strip())
        # Combo answers like "ａ，ｄ"
        if re.fullmatch(r"[ａｂｃｄ，、]+", text):
            text = text.replace("、", "，")
        choices[key] = text
    if len(choices) != 4:
        raise ValueError(f"expected 4 choices, got {sorted(choices)} in: {joined[:120]!r}")
    return [
        {"key": k, "text": choices[k], "explanation": ""}
        for k in ("A", "B", "C", "D")
    ]


def split_stem_and_choice_body(block: str) -> tuple[str, str]:
    """Split question block into stem (incl. ａ–ｄ) and raw choice region."""
    joined = soft_join(block)
    # First ア. that starts the A–D options (not mid-word)
    m = re.search(r"(?:^|\n)(ア[.．])", joined)
    if not m:
        # Combo line may start mid-flow after ｄ item without newline
        m = re.search(r"(ア[.．]\s*[ａｂｃｄ])", joined)
        if m:
            idx = m.start()
            stem = joined[:idx].strip()
            choice_body = joined[idx:].strip()
            return stem, choice_body
        raise ValueError(f"no ア. choice marker in block: {joined[:80]!r}")
    idx = m.start(1)
    stem = joined[:idx].strip()
    choice_body = joined[idx:].strip()
    return stem, choice_body


def normalize_stem(stem: str) -> str:
    """Final stem cleanup; keep newlines before ａ–ｄ and notes."""
    stem = soft_join(stem)
    parts: list[str] = []
    for chunk in stem.split("\n"):
        chunk = re.sub(r"[ \t]+", "", chunk.strip())
        if not chunk:
            continue
        # Restore conventional space after ａ.–ｄ. markers
        chunk = re.sub(r"^([ａｂｃｄ])[.．]", r"\1. ", chunk)
        parts.append(chunk)
    return "\n".join(parts)


def make_question(number: int, stem: str, choices: list[dict]) -> dict:
    return {
        "id": f"2023-yakkan-{number}",
        "number": number,
        "year": "2023",
        "subject": "yakkan",
        "stem": stem,
        "choices": choices,
        "overallExplanation": "",
        "correctKeys": list(ANSWERS[number]),
    }


def parse_section1(body: str) -> list[dict]:
    """Parse sub-questions 1–20 → exam numbers 26–45."""
    # Question starts: N + space + known stem openers
    starts = list(
        re.finditer(
            r"(?m)^([1-9]|1[0-9]|20)\s+(?=募集|受注|手配|旅行)",
            body,
        )
    )
    if len(starts) != 20:
        found = [int(m.group(1)) for m in starts]
        raise ValueError(f"expected 20 section-1 questions, found {len(starts)}: {found}")

    questions: list[dict] = []
    for i, m in enumerate(starts):
        local_n = int(m.group(1))
        start = m.end()  # after "N "
        end = starts[i + 1].start() if i + 1 < len(starts) else len(body)
        block = body[start:end].strip()
        # Drop leading number remnant if any
        stem_raw, choice_raw = split_stem_and_choice_body(block)
        stem = normalize_stem(stem_raw)
        choices = parse_choices(choice_raw)
        exam_n = 25 + local_n  # 1→26 … 20→45
        questions.append(make_question(exam_n, stem, choices))
    return questions


def parse_section_other(body: str) -> list[dict]:
    """Parse sections 2.–6. → exam numbers 46–50."""
    starts = list(re.finditer(r"(?m)^([2-6])\.\s*", body))
    if len(starts) != 5:
        raise ValueError(f"expected sections 2–6, found {len(starts)}")

    questions: list[dict] = []
    for i, m in enumerate(starts):
        sec = int(m.group(1))
        start = m.end()
        end = starts[i + 1].start() if i + 1 < len(starts) else len(body)
        block = body[start:end].strip()
        stem_raw, choice_raw = split_stem_and_choice_body(block)
        stem = normalize_stem(stem_raw)
        choices = parse_choices(choice_raw)
        exam_n = 44 + sec  # 2→46 … 6→50
        questions.append(make_question(exam_n, stem, choices))
    return questions


def main() -> None:
    raw = TMP.read_text(encoding="utf-8")
    text = ocr_fix(raw)

    # Drop title + intro under "1. 標準旅行業約款…" (intro may soft-wrap)
    text = re.sub(
        r"^旅行業約款、運送約款及び宿泊約款\s*",
        "",
        text,
        count=1,
    )
    text = re.sub(
        r"^1\.\s*標準旅行業約款に関する以下の各設問について、該当する答を、選択肢の中からそれぞれ１つ選びな\s*さい。\s*",
        "",
        text,
        count=1,
        flags=re.M,
    )

    # Split section 1 (Q1–20) from sections 2–6
    m = re.search(r"(?m)^2\.\s*一般貸切", text)
    if not m:
        raise ValueError("could not find section 2 (一般貸切…)")
    section1 = text[: m.start()]
    section_other = text[m.start() :]

    questions = parse_section1(section1) + parse_section_other(section_other)
    if len(questions) != 25:
        raise ValueError(f"expected 25 questions, got {len(questions)}")
    nums = [q["number"] for q in questions]
    if nums != list(range(26, 51)):
        raise ValueError(f"bad numbers: {nums}")

    out = {"questions": questions}
    OUT.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(questions)} questions → {OUT}")


if __name__ == "__main__":
    main()
