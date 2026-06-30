# autopilot help

Show available commands with usage guidance.

## Output

Present the following:

```
何をしたいですか？

【セットアップ】
  autopilot setup    VISION/PRINCIPLES作成 → project-init → ロードマップ生成
                     既存プロジェクトにも対応（整合性チェック + マイルストーン付与）

【実行】
  autopilot start    複数スプリントを自律実行（マイルストーンで停止してレビュー）
                     GUIがあればプロトタイプレビュー → 承認後に実装開始

【マイルストーン後のレビュー】
  autopilot review   修正・追加要望を①〜④に分類して適切な機構へ振り分け（冪等）
                     ①AC違反 ②小修正 ③新スコープ ④方向転換
                     comprehension-report.md を読んでから実行するのが前提

【確認】
  autopilot status   進捗・直近の妥協(compromises)・ADR状況・残留worktreeを表示
  autopilot help     このヘルプを表示

💡 始め方:
   新規プロジェクト → autopilot setup → autopilot start
   既存プロジェクト → autopilot setup（VISION/PRINCIPLES追加）→ autopilot start
   マイルストーン到達後、触って気づいたら autopilot review を何度でも
   詳しくは /autopilot help setup で確認
```

If the user asks about a specific command (e.g., "autopilot help setup"), read the relevant section of SKILL.md or reference file and present a brief summary.
