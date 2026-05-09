# sprint help

Show available commands with usage guidance. Help the user find the right command for their situation.

## Output

Present the following table:

```
何をしたいですか？

【セットアップ】
  sprint init       ロードマップの初期化・既存mdからの移行
  sprint roadmap    VISIONからロードマップを一括生成

【スプリントの実行（順番に実行）】
  sprint plan       次のスプリントを計画する
  sprint prototype  GUIのHTMLモックを生成してレビュー
  sprint run        スプリントを実装する
  sprint verify     テスト・レビューで品質を確認する
  sprint demo       動くプログラムでデモする
  sprint refine     UIを見ながら微調整する
  sprint done       スプリントを完了してコミット・プッシュ

【いつでも使える】
  sprint hotfix     小さな修正を素早く（計画・レビュー不要）
  sprint propose    新しい機能のアイデアをロードマップに追加
  sprint auto       1スプリントを全自動で実行
  sprint help       このヘルプを表示

💡 コマンドを覚えなくても、やりたいことを自然に伝えれば
   適切なコマンドが自動で選ばれます。
   例: 「ちょっと直して」→ hotfix / 「機能追加したい」→ propose
```

If the user asks about a specific command (e.g., "sprint help prototype"), read the corresponding reference file and present a brief summary of that command.
