#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Format quiz stems across all question JSON files (idempotent)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public" / "data" / "questions"


def format_stem(stem: str) -> str:
    if not stem:
        return stem
    s = stem.replace("＜図＞", "<図>")
    s = re.sub(r"(選びなさい[。．])(?!\n)", r"\1\n\n", s)
    s = re.sub(r"(?<!\n)(?=[（(]注[0-9一二三四五六七八九十]*[）)])", "\n", s)
    s = re.sub(r"(?<!\n)(?=[＜<](?:行程|資料|図)[＞>])", "\n\n", s)
    s = re.sub(r"([＜<](?:行程|資料|図)[＞>])(?!\n)", r"\1\n", s)
    s = re.sub(r"(?<!\n)(?=<図>)", "\n\n", s)
    s = re.sub(r"(<図>)(?!\n)", r"\1\n", s)
    s = re.sub(r"(?<=[。．＞>])(?=[①-⑩])", "\n", s)
    s = re.sub(
        r"(?<!\n)(?=・(?:[0-9一二三四五六七八九十]+日|[12]日にわたる))",
        "\n",
        s,
    )
    s = re.sub(r"(?<!\n)(?=●)", "\n\n", s)
    if re.search(r"[＜<]資料[＞>]|●", s):
        for lab in (
            "基本宿泊料",
            "サービス料",
            "消費税",
            "入湯税",
            "チェックイン",
            "チェックアウト",
        ):
            s = re.sub(rf"(?<!\n)(?={re.escape(lab)}：)", "\n", s)
        s = re.sub(r"(?<!\n)(?=宿泊契約解除)", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def main() -> None:
    changed_files = 0
    changed_qs = 0
    for path in sorted(DATA.glob("*.json")):
        if path.name in {"index.json"} or path.name.startswith("_"):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        qs = data.get("questions")
        if not isinstance(qs, list):
            continue
        file_changed = False
        for q in qs:
            old = q.get("stem")
            if not isinstance(old, str):
                continue
            new = format_stem(old)
            if new != old:
                q["stem"] = new
                file_changed = True
                changed_qs += 1
        if file_changed:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            changed_files += 1
            print(f"updated {path.name}")
    print(f"done: {changed_qs} stems in {changed_files} files")


if __name__ == "__main__":
    main()
