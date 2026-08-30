# UX: 正答率表示 + 回答保持

## Goal
1. 科目カードの正答率・バーが「解答済みのうち」ではなく「科目全体（correct/total）」基準になるようにする（1/25正解で100%・満タンに見えない）
2. 演習中に戻る／目次ジャンプしても解答を保持。全問終了→結果で全体正答率確認→結果画面の手動リセットまで消えない

## Plan
- [x] `calcSubjectAccuracy`: rate = correct / total（未解答は正解に含めない）。answered=0 のとき null
- [x] `latestAttempt` を export + `calcQueueSessionStats` 追加
- [x] `QuizPage`: 問題切替時に最新 attempt から selected/submitted を復元。再提出不可
- [x] 結果遷移時のセッション集計を progress（localStorage）から算出
- [x] `npm run build` / `npm run lint` で検証

## Review
- ブランチ: `fix/quiz-accuracy-and-answer-retention`
- 正答率: 1問正解/25問 → **4%**（バーも同比率）。合格線60%との比較が科目全体基準に
- 回答保持: 目次・戻るで直近解答を復元し解説表示のまま。変更は結果の「この科目の記録をリセット」まで不可
- 結果の「今回のセッション」も correct/total 表示に統一
- 検証: `npm run lint`（既存 warning のみ）/ `npm run build` 成功
