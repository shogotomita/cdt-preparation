# NotebookLM 用エクスポート

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

再生成する場合は、リポジトリルートで:

```bash
python3 scripts/export_notebooklm_markdown.py
```
