#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assert past-exam (jitsumu) geography proper nouns are independent flashcards.

hooks-only does NOT count (潮来-on-十二橋めぐり regression).
Castle formal names may resolve via alias-card hooks (犬山城 → 白帝城).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEO_PATH = ROOT / "public" / "data" / "geography.json"
QUESTIONS = ROOT / "public" / "data" / "questions"

GEO_FILTER = re.compile(
    r"温泉|祭|まつり|名産|特産|郷土|世界遺産|国立公園|ラムサール|城|寺|神社|焼|漬|そば|"
    r"くんち|御柱|ねぶた|組合せ|所在|市場|高原|滝|渓谷|運河|湾|岬|美術館|記念館"
)
# JR/fare questions often include 学習メモ and must stay out of geo coverage.
NON_GEO = re.compile(r"営業キロ|特急券|JR券|特大荷物|払いもどし|運賃計算|自由席|指定席特急")

CASTLE_ALIAS = {
    "犬山城": "白帝城",
    "松江城": "千鳥城",
    "丸岡城": "霞ヶ城",
    "広島城": "鯉城",
    "岡山城": "烏城",
    "姫路城": "白鷺城",
    "仙台城": "青葉城",
    "会津若松城": "鶴ヶ城",
}

PLACE_SUFFIX = re.compile(
    r"(温泉|高原|市場|神社|大社|寺|院|城|公園|美術館|記念館|聖堂|湖|沼|岬|岳|山|"
    r"峡|渓|滝|島|湾|祭|まつり|農場|遺跡|庭園|橋|崎|浦|峠|洞|窯|焼|鍋|汁|そば|"
    r"うどん|めし|寿司|寿し|園|宮|館|塔|門|宿|倉|港|村|町|市|運河|半島|古墳群)$"
)

BAD = re.compile(
    r"(料金|円|％|%|営業|キロ|特急|割引|旅客|乗車券|約款|法第|条|正解|不正解|"
    r"次のうち|それぞれ|である|であり|について|場合|とき|できる|できない|"
    r"と同じ|を選び|以下の|設問|持ち込む|購入)"
)

NOISE = {
    "ジャパン",
    "スタジオ",
    "ユニバーサル",
    "ヨコ",
    "タテ",
    "九州",
    "山陽",
    "山陰",
    "東海道",
    "路線",
    "精錬から運搬",
    "姫路城や",
}

MUST = [
    "後生掛温泉",
    "湯涌温泉",
    "朝里川温泉",
    "安比高原",
    "五大堂",
    "蓮台寺温泉",
    "潮来",
    "近江町市場",
    "錦市場",
    "二条市場",
    "黒門市場",
    "ひきずり",
    "小樽運河",
    "湯西川温泉",
    "霧降高原",
    "西沢渓谷",
    "知覧",
    "ユニバーサル・スタジオ・ジャパン",
    "神戸ハーバーランド",
]


def normalize(s: str) -> str:
    s = s.strip().strip("「」『』・")
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"^[ア-エA-D]\.", "", s)
    s = re.sub(r"^[ア-エ](?=[一-龥])", "", s)
    # stem fragments: (c)姫路城や → 姫路城
    s = re.sub(r"[やをがにはの]$", "", s)
    return s


def is_proper(name: str) -> bool:
    if name in NOISE:
        return False
    if len(name) < 2 or len(name) > 24:
        return False
    if BAD.search(name):
        return False
    if re.search(r"[をはがにでのと、。]", name):
        return False
    if name.endswith(("県", "府", "都")) and len(name) <= 4:
        return False
    if name in {"北海道", "東京", "大阪", "京都"}:
        return False
    # combo leftovers with box-drawing dash should have been split
    if "─" in name or "－" in name:
        return False
    if PLACE_SUFFIX.search(name):
        return True
    if re.fullmatch(r"[一-龥ァ-ヶぁ-んー]{2,10}", name):
        return True
    # dotted facility names
    if "・" in name and re.fullmatch(r"[一-龥ァ-ヶぁ-んー・]{5,24}", name):
        return True
    return False


def load_labels(geo: dict) -> tuple[set[str], dict[str, str]]:
    labels: set[str] = set()
    hook_to_label: dict[str, str] = {}
    for pref in geo["prefectures"]:
        for f in pref["facts"]:
            labels.add(f["label"])
            for h in f.get("hooks") or []:
                hook_to_label.setdefault(h, f["label"])
    return labels, hook_to_label


def covered(name: str, labels: set[str], hook_to_label: dict[str, str]) -> str | None:
    if name in labels:
        return "CARD"
    alias = CASTLE_ALIAS.get(name)
    if alias and alias in labels:
        return f"ALIAS:{alias}"
    variants = [
        name.replace("ノ", "の"),
        name.replace("の", "ノ"),
        name.replace("ヶ", "ケ"),
        name.replace("ケ", "ヶ"),
    ]
    for v in variants:
        if v != name and v in labels:
            return f"CARD:{v}"
    if name == "芦原温泉" and "あわら温泉" in labels:
        return "CARD:あわら温泉"

    # Parenthetical / compound fuzzy: 玉取祭 ↔ 玉取祭(玉せせり), 立石寺 ↔ 山寺(立石寺)
    for lab in labels:
        if name == lab:
            return "CARD"
        # strip (...)
        base = re.sub(r"[（(][^）)]+[）)]", "", lab)
        if name == base or name in lab or lab in name:
            if min(len(name), len(lab)) >= 2:
                # avoid tiny accidental overlaps (市 in 市場)
                if len(name) >= 3 or len(lab) >= 3:
                    if name in lab or lab in name or name == base:
                        return f"FUZZY:{lab}"
        # compound with ・ or ―
        for sep in ("・", "―", "─"):
            if sep in lab:
                parts = lab.split(sep)
                if name in parts or any(name in p or p in name for p in parts if len(p) >= 2):
                    return f"FUZZY:{lab}"
    return None


def collect_names() -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for path in sorted(QUESTIONS.glob("20*-jitsumu.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for q in data["questions"]:
            stem = q.get("stem") or ""
            overall = q.get("overallExplanation") or ""
            chunks = [stem, overall]
            for c in q.get("choices") or []:
                chunks.append(c.get("text") or "")
                chunks.append(c.get("explanation") or "")
            blob = "\n".join(chunks)
            if not GEO_FILTER.search(blob) or NON_GEO.search(blob):
                continue
            qid = q["id"]

            for m in re.finditer(r"[（(][a-dａ-ｄ][）)]\s*([^\s（）()、。\n]{2,20})", stem):
                name = normalize(m.group(1))
                if is_proper(name):
                    found.setdefault(name, []).append(qid)

            for c in q.get("choices") or []:
                text = c.get("text") or ""
                parts = re.split(r"\s*[―—–─－]\s*", text)
                for part in parts:
                    piece = normalize(part)
                    if not piece:
                        continue
                    # Keep facility names with middle dots intact
                    if is_proper(piece):
                        found.setdefault(piece, []).append(qid)
    return found


def main() -> int:
    geo = json.loads(GEO_PATH.read_text(encoding="utf-8"))
    labels, hook_to_label = load_labels(geo)
    names = collect_names()

    missing: list[tuple[str, str]] = []
    hook_only: list[tuple[str, str]] = []

    required = set(MUST) | set(names)
    for name in sorted(required):
        status = covered(name, labels, hook_to_label)
        if status:
            continue
        if name in hook_to_label:
            hook_only.append((name, hook_to_label[name]))
        else:
            src = ",".join(names.get(name, ["must"])[:3])
            missing.append((name, src))

    chiran_prefs = [
        p["name"]
        for p in geo["prefectures"]
        for f in p["facts"]
        if f["label"] == "知覧"
    ]
    chiran_ok = chiran_prefs == ["鹿児島県"]

    print(f"checked={len(required)} labels={len(labels)}")
    if missing:
        print(f"MISSING ({len(missing)}):")
        for n, src in missing:
            print(f"  {n}  [{src}]")
    if hook_only:
        print(f"HOOK_ONLY ({len(hook_only)}):")
        for n, host in hook_only:
            print(f"  {n}  (on {host})")
    if not chiran_ok:
        print(f"CHIRAN_PREF_BUG: {chiran_prefs!r} (expected ['鹿児島県'])")

    if missing or hook_only or not chiran_ok:
        return 1
    print("OK: past-exam geography coverage")
    return 0


if __name__ == "__main__":
    sys.exit(main())
