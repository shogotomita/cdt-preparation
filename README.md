# 国内旅行業務取扱管理者 過去問学習

年度 × 科目（旅行業法 / 約款 / 実務）ごとに過去問を演習し、正答率をブラウザに保存する学習アプリです。各科目 **60%** 以上を目指せます。

## 使い方

```bash
npm install
npm run dev
```

ブラウザで表示された URL を開きます。

## 問題データの追加

1. `public/data/questions/_template.json`（または `sample-*.json`）をコピーして、例: `public/data/questions/2024-hou.json` を作成
2. 問題・選択肢・正解・解説を記入
3. `public/data/index.json` に年度・科目を登録（`sample-*.json` は参考用のため index には載せない）

```json
{
  "id": "2024",
  "label": "令和6年度",
  "subjects": [
    {
      "subject": "hou",
      "file": "questions/2024-hou.json",
      "questionCount": 40
    },
    {
      "subject": "yakkan",
      "file": "questions/2024-yakkan.json",
      "questionCount": 40
    },
    {
      "subject": "jitsumu",
      "file": "questions/2024-jitsumu.json",
      "questionCount": 40
    }
  ]
}
```

### 科目 ID

| id | 科目 |
|----|------|
| `hou` | 旅行業法・施行規則 |
| `yakkan` | 約款 |
| `jitsumu` | 国内旅行実務 |

### 問題 JSON の形

```json
{
  "questions": [
    {
      "id": "2024-hou-01",
      "number": 1,
      "year": "2024",
      "subject": "hou",
      "stem": "問題文",
      "images": ["/images/2024/jitsumu/q51-1.webp"],
      "choices": [
        { "key": "A", "text": "...", "explanation": "なぜ正解/不正解か" },
        { "key": "B", "text": "...", "explanation": "..." },
        { "key": "C", "text": "...", "explanation": "..." },
        { "key": "D", "text": "...", "explanation": "..." }
      ],
      "correctKeys": ["B"],
      "overallExplanation": "【前提知識】\n...\n\n【解説】\n..."
    }
  ]
}
```

- `images`（任意）: 問題文中に表示する図。パスは `public` 配下をルートにした絶対パス（例: `/images/2025/jitsumu/q51.png`）。表示時に Vite の `base` を付与するので GitHub Pages のサブパスでも解決する
- 問題文 `stem` 内の `<図>` の位置に画像を差し込む（`tmp.md` の `<図>` と同じ）。マーカーが無い場合は問題文の直後に表示する
- 下線付き箇所は `stem` 内で `<u>文言</u>` と書く（例: `（ａ）<u>保津峡</u>`）
- 生スクショは `raw/<年度>-<科目>/` に置き（gitignore 済み）、図部分だけを `public/images/...` に切り出して参照する

解説の書き方・品質基準は [docs/explanation-guidelines.md](docs/explanation-guidelines.md) を参照してください。

## 正答率

- ブラウザの `localStorage` に保存（端末・ブラウザごと）
- **年度 × 科目** 単位で集計（直近の解答ベース）
- ホームと結果画面に合格ライン（60%）を表示
- 「苦手だけ」モードで不正解・未解答を優先復習

## GitHub Pages への公開

1. このリポジトリを GitHub に push
2. Settings → Pages → Source を **GitHub Actions** に設定
3. `main` への push で `.github/workflows/deploy.yml` がデプロイ

ローカル確認:

```bash
npm run build && npm run preview
```
