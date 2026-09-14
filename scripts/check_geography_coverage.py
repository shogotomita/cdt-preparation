#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assert past-exam (jitsumu) geography proper nouns are independent flashcards
under the correct prefecture.

hooks-only does NOT count. Castle formal names may resolve via alias cards.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEO_PATH = ROOT / "public" / "data" / "geography.json"
QUESTIONS = ROOT / "public" / "data" / "questions"
BUILD = ROOT / "scripts" / "build_geography_data.py"


def _load_build():
    spec = importlib.util.spec_from_file_location("build_geography_data", BUILD)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


build = _load_build()

GEO_FILTER = re.compile(
    r"温泉|祭|まつり|名産|特産|郷土|世界遺産|国立公園|ラムサール|城|寺|神社|焼|漬|そば|"
    r"くんち|御柱|ねぶた|組合せ|所在|市場|高原|滝|渓谷|運河|湾|岬|美術館|記念館"
)
NON_GEO = re.compile(r"営業キロ|特急券|JR券|特大荷物|払いもどし|運賃計算|自由席特急")

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
    return build.normalize_label(s)


def is_proper(name: str) -> bool:
    if name in NOISE:
        return False
    if "─" in name or "－" in name:
        return False
    return build.is_card_label(name)


def load_cards(geo: dict) -> dict[str, list[str]]:
    """label → list of pref ids where it appears."""
    out: dict[str, list[str]] = {}
    for pref in geo["prefectures"]:
        for f in pref["facts"]:
            out.setdefault(f["label"], []).append(pref["id"])
    return out


def load_hook_hosts(geo: dict) -> dict[str, tuple[str, str]]:
    """hook → (label, pref_id)"""
    out: dict[str, tuple[str, str]] = {}
    for pref in geo["prefectures"]:
        for f in pref["facts"]:
            for h in f.get("hooks") or []:
                out.setdefault(h, (f["label"], pref["id"]))
    return out


def find_card(name: str, cards: dict[str, list[str]]) -> tuple[str, str] | None:
    """Return (matched_label, pref_id) if covered."""
    if name in cards:
        return name, cards[name][0]
    alias = CASTLE_ALIAS.get(name)
    if alias and alias in cards:
        return alias, cards[alias][0]
    for v in (
        name.replace("ノ", "の"),
        name.replace("の", "ノ"),
        name.replace("ヶ", "ケ"),
        name.replace("ケ", "ヶ"),
    ):
        if v != name and v in cards:
            return v, cards[v][0]
    if name == "芦原温泉" and "あわら温泉" in cards:
        return "あわら温泉", cards["あわら温泉"][0]

    for lab, prefs in cards.items():
        base = re.sub(r"[（(][^）)]+[）)]", "", lab)
        if name == base or (len(name) >= 3 and (name in lab or lab in name)):
            return lab, prefs[0]
        for sep in ("・", "―", "─"):
            if sep in lab:
                parts = lab.split(sep)
                if name in parts or any(name in p or p in name for p in parts if len(p) >= 2):
                    return lab, prefs[0]
    return None


def expected_from_curated() -> dict[str, str]:
    """label → pref_id from CURATED (last write wins)."""
    out: dict[str, str] = {}
    for pref_id, _typ, label, _hooks in build.CURATED:
        out[label] = pref_id
    return out


def expected_from_choices() -> dict[str, str]:
    """Strict choice→pref expectations (same rules as extract_from_choice)."""
    out: dict[str, str] = {}
    for path in sorted(QUESTIONS.glob("20*-jitsumu.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for q in data["questions"]:
            blob = "\n".join(
                [q.get("stem") or "", q.get("overallExplanation") or ""]
                + [c.get("text") or "" for c in q.get("choices") or []]
                + [c.get("explanation") or "" for c in q.get("choices") or []]
            )
            if not GEO_FILTER.search(blob) or NON_GEO.search(blob):
                continue
            for c in q.get("choices") or []:
                text = c.get("text") or ""
                expl = c.get("explanation") or ""
                if re.search(r"[―—–─－]", text):
                    continue
                label = normalize(text)
                if not is_proper(label):
                    continue
                pref_id = None
                m = re.match(r"(?:正解|不正解)[。．]([一-龥ぁ-んァ-ヶA-Za-z0-9]{2,8})[。．]", expl)
                if m:
                    pref_id = build.resolve_loc_token(m.group(1))
                if not pref_id:
                    m = re.match(r"(?:正解|不正解)[。．]([一-龥ぁ-んァ-ヶA-Za-z0-9]{2,8})の", expl)
                    if m:
                        pref_id = build.resolve_loc_token(m.group(1))
                if not pref_id:
                    m2 = re.search(r"いずれも([一-龥ぁ-んァ-ヶ]{2,8})", expl)
                    if m2:
                        pref_id = build.resolve_loc_token(m2.group(1))
                if not pref_id:
                    m3 = re.search(re.escape(label) + r"(?:は|が)([一-龥ぁ-んァ-ヶA-Za-z0-9]{2,8})", expl)
                    if m3:
                        tok = m3.group(1)
                        pref_id = build.resolve_loc_token(tok) or build.resolve_loc_token(
                            re.sub(r"(側|県|府|都|道)$", "", tok)
                        )
                if pref_id:
                    out[label] = pref_id
    return out


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
            for m in re.finditer(
                r"(?<!下線)[（(][a-dａ-ｄ][）)]\s*([一-龥ぁ-んァ-ヶA-Za-z0-9・ー]{2,16})",
                stem,
            ):
                name = normalize(m.group(1))
                if is_proper(name) and not name.startswith("と"):
                    found.setdefault(name, []).append(qid)
            for c in q.get("choices") or []:
                text = c.get("text") or ""
                for part in re.split(r"\s*[―—–─－]\s*", text):
                    piece = normalize(part)
                    if is_proper(piece):
                        found.setdefault(piece, []).append(qid)
    return found


def main() -> int:
    geo = json.loads(GEO_PATH.read_text(encoding="utf-8"))
    cards = load_cards(geo)
    hooks = load_hook_hosts(geo)
    names = collect_names()
    curated_exp = expected_from_curated()
    choice_exp = expected_from_choices()

    missing: list[tuple[str, str]] = []
    hook_only: list[tuple[str, str]] = []
    wrong_pref: list[tuple[str, str, str]] = []

    required = set(MUST) | set(names)
    for name in sorted(required):
        hit = find_card(name, cards)
        if not hit:
            if name in hooks:
                hook_only.append((name, hooks[name][0]))
            else:
                missing.append((name, ",".join(names.get(name, ["must"])[:3])))
            continue
        matched, pref_id = hit
        expected = choice_exp.get(name) or curated_exp.get(name) or curated_exp.get(matched)
        if expected and pref_id != expected:
            wrong_pref.append((name, pref_id, expected))

    # Curated labels must sit in their declared prefecture
    for label, exp in curated_exp.items():
        if label not in cards:
            continue
        if exp not in cards[label]:
            wrong_pref.append((label, ",".join(cards[label]), exp))

    # No sentence-like auto labels (official heritage names may contain 、)
    sentence_labels: list[str] = []
    for pref in geo["prefectures"]:
        for f in pref["facts"]:
            lab = f["label"]
            if re.search(r"。|所在する|である|園内|エリアに", lab):
                sentence_labels.append(f"{pref['id']}:{lab}")

    chiran_prefs = [
        p["name"]
        for p in geo["prefectures"]
        for f in p["facts"]
        if f["label"] == "知覧"
    ]
    chiran_ok = chiran_prefs == ["鹿児島県"]

    print(f"checked={len(required)} labels={len(cards)}")
    if missing:
        print(f"MISSING ({len(missing)}):")
        for n, src in missing:
            print(f"  {n}  [{src}]")
    if hook_only:
        print(f"HOOK_ONLY ({len(hook_only)}):")
        for n, host in hook_only:
            print(f"  {n}  (on {host})")
    if wrong_pref:
        print(f"WRONG_PREF ({len(wrong_pref)}):")
        for n, got, exp in wrong_pref:
            print(f"  {n}  got={got} expected={exp}")
    if sentence_labels:
        print(f"SENTENCE_LABELS ({len(sentence_labels)}):")
        for s in sentence_labels[:20]:
            print(f"  {s}")
    if not chiran_ok:
        print(f"CHIRAN_PREF_BUG: {chiran_prefs!r}")

    if missing or hook_only or wrong_pref or sentence_labels or not chiran_ok:
        return 1
    print("OK: past-exam geography coverage")
    return 0


if __name__ == "__main__":
    sys.exit(main())
