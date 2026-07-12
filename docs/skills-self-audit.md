# claude-skills 自己チェック指示書

## 目的

claude-skills を管理する Agent が、SKILL 群を「静的な規約集」ではなく「運用で育つ法体系」として維持するための自己監査を実施する。本ドキュメントは、その背景となる統治モデルと、監査すべき 4 つの観点を定義する。

---

## 背景: このリポジトリが前提とする統治モデル

本プロジェクトでは、人間(PO)が単独で複数の大規模プロダクトを AI Agent 群に開発させている。PO は仕様・実装・アーキテクチャの全量を把握しない。品質は悉皆検査ではなく、以下の階層構造で担保する。

| 層 | 担うもの | PO の関与 |
|---|---|---|
| 振る舞い(デモ) | 成果物が意図と合っているか | 直接レビュー |
| 不変条件 | 破ってはいけないことの機械検証 | 定義のみ |
| 検証システム | テスト・レビューの多段構造(implementer ≠ tester ≠ reviewer) | 抜き取り監査 |
| アーキテクチャ | 不可逆な決定(ADR) | ADR のみ判断 |
| SKILL/ハーネス | 上記すべての基準を成文化した「法典」 | **主業務: 立法と改訂** |

この構造では、人間組織における「信頼できる中間管理層」を SKILL とハーネスで代替する。したがって SKILL の品質と鮮度が、システム全体の品質上限を決める。SKILL は放置すると陳腐化し、かつ**自分の陳腐化を自分で検知できない**。この欠陥を補うのが本監査の役割である。

---

## 自己チェック項目

### 1. SKILL 改訂ループの制度化(最重要)

**問い: 失敗や手戻りが発生したとき、それが SKILL への diff に変換される回路が存在するか。**

この回路は `skills/autopilot/references/skill-retrospective.md` として実装されている(milestone ごとに `docs/sprint-logs/{SprintID}/skill-retrospective.md` を生成し、batch 内の各 compromise / overlooked / reopen を task-local か SKILL 欠陥かに分類、欠陥には diff 提案 or 見送り理由を出す)。本監査はその出力を横断で読み、PO 承認へ通す roll-up 層。

- [ ] milestone の `skill-retrospective.md` が生成され、各 signal について「task-local か SKILL 欠陥か」の分類と、欠陥には「diff 提案 or 見送り理由」が**空欄なく**埋まっているか(空欄 = 「タスクを直して終わり」の兆候そのもの)
- [ ] retrospective に載らずに「タスクを直して終わり」になった失敗・手戻りがないか。あれば遡って「どの SKILL の欠陥か」を問い、retrospective に起票する
- [ ] 長期間更新されていない SKILL が実態と乖離していないか。改訂日は手書きメタで持たず(腐るため)git から導出する:
  ```bash
  # 各 SKILL/reference の最終更新日を古い順に。N ヶ月(例: 6)以上のものを実運用と突き合わせる
  git ls-files 'skills/**/*.md' | while read -r f; do echo "$(git log -1 --format=%cs -- "$f") $f"; done | sort
  ```

**基準:** 失敗が SKILL に還元されない状態が 2 sprint 以上続いたら、ループが機能していないとみなし PO に報告する。retrospective の **Deferred** セクションに同じ欠陥が 2 milestone 以上滞留していれば、`autopilot status` がこれを表面化する。

### 2. 検証網の健全性テスト

**問い: 検証システム(hooks、machine verdict、独立 verifier、forbidden categories チェック)が実際に違反を検知できることを、定期的に確認しているか。**

hook 層の自動テストは `hooks/tests/test_hooks.py`(seeded-violation スイート — 既知違反を混入して各 hook の検知を確認)として実装済み。実行パス全体を確かめるドリル手順は `hooks/README.md` → 「Seeded-violation drill」。

- [ ] `python3 hooks/tests/test_hooks.py` が緑か。hook に検知パターンを足したら対応する seed も足したか(足さないと網が嘘になる)
- [ ] 実行パス全体の「seeded-violation drill」を直近の自己監査サイクルで実施した記録があるか。なければ実施する
- [ ] 検知に失敗したケース(自動テストの red、またはドリルで violation がすり抜けた)があれば、その穴を検証側 SKILL/hook の欠陥として項目 1 の retrospective に乗せているか

**基準:** 自動テストは常時緑、ドリルは最低 sprint(または自己監査サイクル)ごとに 1 回。検知率が下がっていれば法典の執行力が緩んでいるサインとして扱う。

### 3. 「基準外の違和感」の吸い上げ口

**問い: 定義済みルールに違反していないが何かおかしい、という情報が PO に届く経路があるか。**

この経路は実装済み: implementer が `sprint run` Step 1 で concerns(`[{note, theme}]`)を返し、独立 verifier が `verification-report.json` の `concerns[]`(category 5 — sensor であってゲートではない)に統合、milestone の `skill-retrospective.md` が recurring theme を拾う。

- [ ] concerns が各ロールの成果物に**必須キー**として存在するか(implementer = `sprint run` 返却、reviewer = verifier の `verification-report.json` `concerns[]`)。空配列は正当な回答だが、キーの欠落は不可(「何もおかしくないか?」を必ず一度問わせる)
- [ ] 空欄率が高すぎないか。`concerns[]` がほぼ全 Sprint・全ロールで空なら、それはセンサーが機能していない=eliciting プロンプトが弱い兆候であり、「何も無い」証明ではない。プロンプト側を改善対象にする(retrospective の count 行が空欄率を表示する)
- [ ] 同じ `theme` で 2+ Sprint 繰り返す concern を、新しい AC / 不変条件 / 規約の候補として retrospective(項目 1)に接続しているか。単発の concern は diff にせずログのみ

**基準:** 網の目にないものは静かに通過する。この欄は完全な対策ではなくセンサーであり、空欄率が高すぎる場合はプロンプト側の改善対象とする。

### 4. デモレビューのコスト最小化

**問い: PO が成果物を「触れる状態」で受け取れることが Definition of Done に含まれているか。**

- [ ] DoD に以下が含まれているか: 動作確認可能な状態(デプロイ済み URL、または 1 コマンドで起動する再現手順)、変更の要点サマリ、必要に応じてスクリーンショット/録画。「触れる状態」の一次窓口は milestone の `comprehension-report.md` →「How to run it」節と `sprint done` の最終サマリ(`skills/sprint/references/sprint-done.md`)
- [ ] 直近の成果物で、PO がセットアップ・環境構築に時間を使った事例がないか。あれば DoD の欠陥として項目 1 の retrospective に乗せる

**基準:** PO のレビュー帯域がシステム全体の Velocity の分母である。PO がレビュー以外の作業に時間を使った瞬間、帯域が漏れているとみなす。

---

## 実施要領

1. 本チェックを **sprint ごとに 1 回** 実施する
2. 結果は各項目について「充足 / 部分的 / 欠落」の 3 段階で判定し、欠落項目には是正のための SKILL diff 案を添える
3. 判定と diff 案をまとめて PO に報告する。PO の承認をもって SKILL に反映する(SKILL 自体の改訂は不可逆な決定に準じるため、Agent の独断で行わない)
4. 3 回連続で全項目「充足」となった場合、本チェックリスト自体の陳腐化を疑い、チェック項目の見直しを PO に提案する

## 判断に迷ったときの原則

- SKILL は自分の陳腐化を検知できない。疑わしきは PO に報告する
- 「タスクの修正」で閉じそうになったら、必ず「どの SKILL の欠陥か」を一度問う
- 検証を厳しくすることと、PO のレビュー帯域を守ることが衝突したら、PO に判断を仰ぐ(自動で検証を弱めない)