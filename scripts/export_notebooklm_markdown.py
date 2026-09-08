#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export past-question explanations to subject Markdown for NotebookLM."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public" / "data" / "questions"
OUT = ROOT / "docs" / "notebooklm"

KEY_JP = {"A": "ア", "B": "イ", "C": "ウ", "D": "エ"}

SUBJECTS = {
    "hou": {
        "title": "旅行業法・施行規則",
        "file": "01-hou-旅行業法.md",
        "blurb": (
            "国内旅行業務取扱管理者試験の「旅行業法・施行規則」科目向けの学習素材です。"
            "各年度の過去問について、正解・全体解説・選択肢の根拠をまとめています。"
            "条文の趣旨、登録区分、標識、取引条件の説明、禁止行為、管理者制度などが出題の中心です。"
        ),
    },
    "yakkan": {
        "title": "旅行業約款",
        "file": "02-yakkan-約款.md",
        "blurb": (
            "国内旅行業務取扱管理者試験の「約款」科目向けの学習素材です。"
            "募集型・受注型企画旅行、特別補償規程、旅程保証、変更補償金、"
            "手配旅行・渡航手続代行・旅行相談など、約款上の成立・解除・責任・補償の論点が中心です。"
        ),
    },
    "jitsumu": {
        "title": "国内旅行実務",
        "file": "03-jitsumu-国内旅行実務.md",
        "blurb": (
            "国内旅行業務取扱管理者試験の「国内旅行実務」科目向けの学習素材です。"
            "貸切バス運賃、宿泊約款、JR運賃・料金、航空、フェリー、観光地理・世界遺産・モデルコースなど、"
            "計算と知識の両面が出ます。計算問題は過程ごと読んでください。"
        ),
    },
}

YEAR_LABEL = {
    "2025": "令和7年度（2025）",
    "2024": "令和6年度（2024）",
    "2023": "令和5年度（2023）",
    "2022": "令和4年度（2022）",
    "2021": "令和3年度（2021）",
}


def clean_text(s: str) -> str:
    s = s.replace("<図>", "（図あり）")
    s = re.sub(r"</?u>", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def stem_summary(stem: str, limit: int = 180) -> str:
    text = clean_text(stem)
    first = text.split("\n\n")[0].replace("\n", "")
    if len(first) > limit:
        return first[: limit - 1] + "…"
    return first


def correct_label(keys: list[str]) -> str:
    if not keys:
        return "（未設定）"
    return "・".join(f"{KEY_JP.get(k, k)}（{k}）" for k in keys)


def load_year_subject(year: str, subject: str):
    path = DATA / f"{year}-{subject}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))["questions"]


def render_question(q: dict) -> str:
    disp = q.get("displayNumber") or q.get("number")
    lines = [
        f"### 問{disp}",
        "",
        f"**正解:** {correct_label(q.get('correctKeys') or [])}",
        "",
        f"**出題の要旨:** {stem_summary(q.get('stem') or '')}",
        "",
        "**全体解説:**",
        "",
        clean_text(q.get("overallExplanation") or "（解説なし）"),
        "",
        "**選択肢メモ:**",
        "",
    ]
    for ch in q.get("choices") or []:
        key = ch.get("key", "?")
        jp = KEY_JP.get(key, key)
        mark = "✓" if key in (q.get("correctKeys") or []) else "×"
        expl = clean_text(ch.get("explanation") or "")
        lines.append(f"- {mark} {jp}（{key}）: {expl}")
    lines.append("")
    return "\n".join(lines)


def build_subject_md(subject: str) -> str:
    meta = SUBJECTS[subject]
    parts = [
        f"# {meta['title']} — 過去問解説まとめ",
        "",
        meta["blurb"],
        "",
        "この資料は、国内旅行業務取扱管理者試験の学習用に整理した解説集です。"
        "ポッドキャスト化するときは、条文番号の暗唱より"
        "「制度の考え方・ひっかけの型・計算の手順」を優先してください。",
        "",
        "---",
        "",
    ]
    for year in ["2025", "2024", "2023", "2022", "2021"]:
        qs = load_year_subject(year, subject)
        if not qs:
            continue
        parts.append(f"## {YEAR_LABEL[year]}")
        parts.append("")
        parts.append(f"全{len(qs)}問。以下、各問の正解・全体解説・選択肢根拠です。")
        parts.append("")
        for q in qs:
            parts.append(render_question(q))
        parts.append("---")
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


BRIEF = """# NotebookLM ポッドキャスト用指示文

このノートにアップロードした Markdown は、国内旅行業務取扱管理者試験の**科目別・過去問解説集**です。
この指示に従って Audio Overview（ポッドキャスト）を生成してください。

---

## 番組のゴール

聞き手が通勤・家事のあいだに聞いても、
「試験で問われる制度の骨格」「ひっかけの型」「計算の手順」が頭に残る学習ポッドキャストにする。

暗記の羅列ではなく、**理解して再現できる説明**を優先する。

---

## ホストの役割（2人想定）

- **ホストA（進行・聞き手）**: 受験生目線。難しい語を言い換えてもらう。たまに「それひっかけ？」「数字は？」と確認する。
- **ホストB（解説役）**: 講師。条文・約款・実務ルールを正確に。結論→理由→ひっかけ、の順で話す。

口調は丁寧で明るく、押し売り感のない勉強仲間トーン。専門用語は初出で一言かみ砕く。

---

## 構成（1本あたり 15〜25分目安）

1. **導入（1分）**  
   科目名と今日のテーマを宣言。合格ライン60%を意識した復習だと伝える。

2. **今日の地図（1〜2分）**  
   この回で扱う論点を3〜5個だけ予告（例: 登録区分／標識／特別補償／貸切バスの点呼時間）。

3. **本編（本体）**  
   年度順に全部を読み上げない。  
   **論点ごとに横断**してよい（例: 「特別補償は令和3〜7で繰り返し出る。共通ルールは…。年度ごとのひっかけは…」）。  
   各トピックは次の型で:
   - 結論（何が正解の考え方か）
   - 根拠（制度・数字・計算手順）
   - ひっかけ（似た語・近い数字・例外の取り違え）
   - 一言定着フレーズ（覚え方）

4. **計算が出る回**  
   公式 → 代入する数字 → 途中式 → 答え、の順。  
   聞き手が頭の中で追えるよう、一度に数字を並べすぎない。

5. **クロージング（1〜2分）**  
   今日の定着フレーズを3つ復唱。次回へのつなぎ（任意）。

---

## やってほしいこと

- 正解肢の記号（ア〜エ）より、**中身のルール**を話す
- 「不正解はなぜダメか」を短く対比する（紛らわしい肢があるとき）
- 同じ論点が複数年度にあるときはまとめて「頻出パターン」として話す
- 地理・固有名詞は、位置関係や覚え方のフックを一言添える
- 資料中の「（図あり）」は、図の中身を推測で埋めない。図が必要な計算は「図の数値を使って…」と述べ、解説に書かれた式を優先する

---

## やめてほしいこと

- 問題文の丸読みや、全選択肢の機械的読み上げ
- 解説にない条文番号・金額・期限の創作
- 「覚えれば終わり」だけで理由を省略すること
- 過度なギャグや、試験と無関係な雑談で尺を稼ぐこと
- 時事・政治・宗教など試験と無関係な話題

---

## トーンと速度

- 重要数字（日数・金額・時間・％）は少しゆっくり、一拍置いて言う
- 専門語のあとに日常語の言い換えを挟む（例: 「旅程保証、つまり計画どおり運べなかったときの手当て」）
- 1トピックを長くしすぎず、区切りで「ここまでのポイントは〜」と短くまとめる

---

## 科目別の強調ポイント

アップロードしたファイルに応じて、特に次を厚めに。

### 旅行業法（`01-hou-*.md`）
登録種別、営業保証金・弁済業務保証金、管理者、標識、禁止行為、取引条件の説明・書面、広告、外貨業務など。  
「似た用語のすり替え」がひっかけの定番。

### 約款（`02-yakkan-*.md`）
契約の成立時期、取消料、旅程保証と変更補償金、特別補償（死亡・後遺障害・入院・携帯品）、手配・相談契約の責任。  
「起算日」「何が補償対象か／対象外か」を明確に。

### 国内旅行実務（`03-jitsumu-*.md`）
貸切バス（点呼時間・回送・深夜早朝）、宿泊約款の計算、JR・航空・フェリー、地理・遺産・コース。  
計算は必ず手順を声に出す。地理は「キーワード→地名」の対応を優先。

---

## 出力イメージ（冒頭の例）

> 「今日は国内旅行業務取扱管理者の〔科目名〕、頻出テーマ復習です。  
> 合格ラインは60%。今日は暗記というより、ひっかけに負けない考え方を一緒に確認しましょう。  
> まずは今日の地図から…」

このトーンで、アップロード資料の内容だけを根拠に番組を作成してください。
"""

README = """# NotebookLM 用エクスポート

国内旅行業務取扱管理者試験の過去問解説を、科目別にまとめた Markdown です。

## ファイル

| ファイル | 内容 |
|----------|------|
| `00-podcast-brief.md` | NotebookLM に貼るポッドキャスト指示文 |
| `01-hou-旅行業法.md` | 旅行業法・施行規則（令和3〜7） |
| `02-yakkan-約款.md` | 約款（令和3〜7） |
| `03-jitsumu-国内旅行実務.md` | 国内旅行実務（令和3〜7） |

## NotebookLM での使い方（推奨）

1. 科目ごとにノートを分ける（法／約款／実務で3本の番組にする）
2. その科目の `0x-*.md` と `00-podcast-brief.md` をアップロード
3. Chat に `00-podcast-brief.md` の指示を貼る、または「この brief どおりに Audio Overview を作って」と依頼
4. Audio Overview を生成

再生成:

```bash
python3 scripts/export_notebooklm_markdown.py
```
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for sid, meta in SUBJECTS.items():
        text = build_subject_md(sid)
        path = OUT / meta["file"]
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({len(text):,} chars)")
    (OUT / "00-podcast-brief.md").write_text(BRIEF, encoding="utf-8")
    (OUT / "README.md").write_text(README, encoding="utf-8")
    print("wrote docs/notebooklm/00-podcast-brief.md")
    print("wrote docs/notebooklm/README.md")


if __name__ == "__main__":
    main()
