# claude-skills リファクタリング仕様書 v0.5

**対象リポジトリ**: `tjst-t/claude-skills`
**作成日**: 2026-05-16
**改訂**:
- v0.1: 初版（autopilot主役化、4分類レビュー）
- v0.2: review 冪等性を明示
- v0.3: design スキル統合（全面改訂）
- v0.4: Loop Engineering（Addy Osmani）からの反映：verifier sub-agent + comprehension-report
- v0.5: 後方互換性ポリシーと既存プロジェクト移行ガイドを追加

**目的**: 現状の複雑化したスキル/コマンド体系を、Takumi の実利用パターンと Anthropic「How Claude Code works in large codebases」ベストプラクティスに合わせて再設計する。本ドキュメントは Claude Code 側で実装作業を行うためのハンドオフ仕様。

---

## 1. 背景と動機

### 1.1 現状の問題

- **コマンド数が多すぎる**: sprint skill だけで 13 コマンド。どの場面でどれを使うか開発者本人が悩む。
- **実利用との乖離**: 当初 plan→run→verify→done を毎回叩く前提だったが、面倒で `autopilot` を作成。以降は autopilot がメイン使用で、sprint の個別コマンドはほぼ使われていない。
- **トリガーフレーズの過剰**: 「ちょっと直して」「バグ修正」等で sprint skill がフル発動。軽い修正に ceremony を噛ませる必要はない。
- **スキル間の重複**: `autopilot` skill と `sprint auto` コマンドの実質重複、`gui-spec` が sprint からしか呼ばれないのに独立スキルになっている。
- **load-bearing decisions の置き場所がなかった**（design スキル新設で解決済み）。

### 1.2 重要な気づき

- **autopilot が本来の「sprint」だった**: plan/run/verify/done という分割はそもそも過剰だった。1コマンドで回せる粒度こそが正しい設計。
- **design スキルの追加で 4 層構造が完成した**: load-bearing decisions (design) → 初期化 (project-init) → atomic 実行 (sprint) → orchestration (autopilot) と責務が明快に分かれる。
- **2 層構造（sprint + autopilot）の維持は正解**: 抽象レベルが本質的に違うため統合すべきではない。同様の理由で design も独立を維持。

---

## 2. 設計方針（決定事項）

### 2.1 スキル構造：4 層

| 層 | スキル | 責務 | 起動頻度 |
|---|---|---|---|
| 設計 | **design** | load-bearing decisions の明文化（VISION/ADR/domain/system） | 低（プロジェクト開始時、大型変更時） |
| 初期化 | **project-init** | プロジェクトの初期セットアップ | 極低（プロジェクトごとに 1 回） |
| エンジン | **sprint** | 1 フェーズの atomic な実行 | 中（autopilot から呼ばれる、たまに直接） |
| オーケストレータ | **autopilot** | 状態遷移・繰り返し・分岐判断・レビュー司令塔 | 高（メイン操作） |

統合せずに 4 層維持する理由：それぞれが異なる抽象レベルの責務を担っており、1 スキルに同居させると SKILL.md が肥大化して Claude のコンテキスト効率が悪化する。

### 2.2 ユーザ接点の反転

| | Before | After |
|---|---|---|
| 主役として露出 | sprint（13 コマンド） | **autopilot**（メイン）、design（複雑案件のみ） |
| 裏方 | autopilot | sprint（autopilot から呼ばれる、または明示的な debug 用） |

### 2.3 「止まる前提の sprint × 自走する autopilot」の実現方法

**案A（採用）**: sprint に `--auto` フラグを追加。autopilot は常に `--auto` 付きで sprint を呼ぶ。

- デフォルトの sprint = 迷ったら止まる
- `sprint <cmd> --auto` = 迷ったら decision log に記録して自己判断で進む
- decision logging 仕組みは既存の `docs/sprint-logs/{SprintID}/decisions.json` を流用

### 2.4 autopilot の実行範囲と停止条件

#### 自走範囲
- **マイルストーン境界まで**自走（既存仕様維持）
- マイルストーン到達で必ず停止し、`autopilot review` を提案

#### GUI Story の扱い
- 既存仕様を維持：autopilot 開始前に、次マイルストーンまでに含まれる GUI Story 全ての prototype を作成
- プロトタイプ承認後に autopilot を開始

#### 自己判断の禁止カテゴリ

| カテゴリ | 例 | 挙動 |
|---|---|---|
| テストの実質的な無効化 | `it.skip`, `xtest`, `@pytest.mark.skip` の追加、`expect(true).toBe(true)` への書き換え | **完走後にまとめて通知** |
| アサーションの緩和 | `toEqual` → `toBeTruthy`、具体値 → 任意値 | 完走後にまとめて通知 |
| Acceptance criteria の削除/緩和 | ROADMAP.json から AC 削除、文言を緩める | **即時停止** |
| エラーの握りつぶし | `try { ... } catch {}`、`// @ts-ignore`、`# noqa` の新規追加 | 完走後にまとめて通知 |
| 型安全性の放棄 | `any` への変更、`as` キャスト乱用 | 完走後にまとめて通知 |
| 破壊的 Git 操作 | `push --force`, `reset --hard origin`, branch 削除 | **即時停止** |
| ROADMAP の status 虚偽記載 | テスト失敗のまま `status: "done"` | **即時停止** |
| **ADR への暗黙の違反** | 既存 ADR の Decision に反する実装を `decisions.json` 経由で正当化 | **即時停止**（ADR amendment を要求） |

判断基準：
- **即時停止** = それ以降の作業の前提を壊すもの（AC 改竄、Git 破壊、ADR 違反）
- **完走後通知** = ローカルな妥協で、後でレビュー可能なもの

### 2.5 完走後通知の構造化（compromises.json）

マイルストーン到達時に、Takumi に対して categorized & actionable な形で提示する。

ファイル: `docs/sprint-logs/{SprintID}/compromises.json`

```json
{
  "milestone_summary": {
    "stopped_at": "milestone_M02",
    "compromises": [
      {
        "type": "test_assertion_weakened",
        "severity": "medium",
        "story": "S003",
        "file": "tests/auth.spec.ts",
        "rationale": "OAuth provider のmock複雑化を回避",
        "diff_summary": "expect(token).toBe('xyz') → expect(token).toBeTruthy()",
        "recommended_action": "OAuth mock を別Storyで整備して厳密化",
        "adr_ref": "none"
      }
    ],
    "blockers_encountered": [],
    "scope_changes": []
  }
}
```

`type` の enum 候補：`test_skipped` / `test_assertion_weakened` / `error_swallowed` / `type_safety_relaxed` / `acceptance_criteria_modified`

`severity` の enum: `low` / `medium` / `high`

`adr_ref`: 妥協が ADR に関係する場合は ADR-NNNN、無関係なら `"none"`

### 2.6 防御アーキテクチャ：3 層防御 + verifier sub-agent

#### 2.6.1 3 層防御

| 層 | 機構 | 役割 | 実装優先度 |
|---|---|---|---|
| L1 | autopilot プロンプト内の禁止リスト | Claude 自身が回避する第一線 | **高（最優先）** |
| L2 | sprint verify フェーズの自動チェック（diff scan） | 違反を検出。`test-discipline.md` Rule 6 を拡張 | 中 |
| L3 | PostToolUse hook | Edit ツール経由の skip 追加等を決定論的にブロック | 低（中長期） |

#### 2.6.2 verifier sub-agent（maker と checker の分離）

L1〜L3 はすべて「実装した autopilot 自身」が検出する仕組みで、self-grading bias の問題がある。Loop Engineering（Addy Osmani）が指摘する通り、**実装したエージェントは自分の成果物の評価が甘くなる**。

これに対応するため、**実装とは独立した verifier sub-agent** を導入する。`sprint verify --auto` 時、autopilot とは別の Claude セッション（read-only、別プロンプト、可能であれば別モデルや異なる reasoning effort）が以下を検証：

| 検証対象 | 内容 |
|---|---|
| Acceptance criteria | ROADMAP.json の AC を満たしているか実コードと突き合わせ |
| 禁止カテゴリ違反 | §2.4 の禁止カテゴリ表に従って diff 全体を scan |
| ADR 整合性 | 該当 ADR の Decision に反する実装が無いか |
| compromises の網羅性 | autopilot 自身が記録した妥協以外に、見逃した妥協が無いか |

verifier sub-agent の出力 = `compromises.json` の **信頼ソース**。autopilot 自身の自己申告と verifier の判定を突き合わせて、両者が食い違う場合は verifier 側を採用、かつ「autopilot による見逃し」として明示記録する。

これにより、L1（autopilot 自身の禁止リスト）の信頼性が verifier の独立検証で底上げされる構造になる。

実装上の注意：
- verifier sub-agent は **read-only**（書き込み権限を持たない）
- verifier のプロンプトは「**疑い深く、批判的に、自己保身せず検証する**」スタンスを明示
- verifier の判定は `docs/sprint-logs/{SprintID}/verification-report.json` に保存
- トークンコストが上がるため、`sprint verify` のデフォルトは現状通り（同一セッション）とし、`--with-verifier` フラグまたは `autopilot` 経由の場合のみ自動で verifier 起動

### 2.7 マイルストーンレビュー時の修正要望の扱い

autopilot がマイルストーン到達で停止した後、ユーザが「修正したい」「追加したい」と言った時の処理を定義する。

#### 2.7.1 修正要望の 4 分類

| # | 種別 | 判定基準 | 例 | 扱い |
|---|---|---|---|---|
| ① | **AC 違反** | 既存 AC が実は満たされていなかった | 「ログイン成功時にトークン保存」AC に対し、実は localStorage に保存されていなかった | 該当 Sprint を `in_progress` に戻して修正 |
| ② | **AC 範囲外・小修正** | AC は満たしているが UX/細部の調整。1〜2 タスク程度 | 「ボタンの色変えたい」「エラーメッセージの文言調整」 | 補修 Story 追加（配置はユーザ選択） |
| ③ | **AC 範囲外・新スコープ** | Story 単位以上の新機能/改善 | 「ログイン履歴を見られるようにしたい」 | 次 Sprint に追加 or backlog |
| ④ | **方向転換** | ROADMAP 全体の見直しが必要、load-bearing decision に影響 | 「認証方式を OAuth から magic link に変える」 | DESIGN/ がある場合は ADR 経由、無い場合は `sprint roadmap` 再実行 |

#### 2.7.2 既存スキルへの委譲

新コマンドは原則作らない。既存の部品で 4 分類すべてをカバー可能：

| 分類 | 委譲先 |
|---|---|
| ① AC 違反 | `sprint verify` の失敗扱い → `sprint run` で修正 |
| ② 小修正 | `sprint fix`（旧 hotfix）相当の処理 |
| ③ 新スコープ | `sprint idea`（旧 propose） → 次の `sprint plan` で取り込み |
| ④ 方向転換 (DESIGN/ あり) | `design adr` で新 ADR or 既存 ADR の supersede → `sprint roadmap` 再実行 |
| ④ 方向転換 (DESIGN/ なし) | `sprint roadmap` 再実行 |

足りないのは「**要望を聞いて分類し、適切な部品に振り分ける司令塔**」。これを `autopilot review` として新設する。

#### 2.7.3 `autopilot review` の動作フロー

```
[マイルストーン到達 → compromises.json 提示]
        ↓
autopilot が「review しますか？」と自動提案
        ↓
ユーザ Yes
        ↓
autopilot review 起動
        ↓
1. ROADMAP.json + compromises.json + 直近 Sprint 状態 + DESIGN/ を読込
2. ユーザの要望を聞く（複数まとめて受け取り）
3. 各要望を ①〜④ に分類して提案
4. ④ かつ DESIGN/ あり の場合、ADR 影響範囲も併せて提示
        ↓
分類提案テーブルをユーザに提示
        ↓
ユーザ承認 → 各要望を該当機構に振り分けて実行
        ↓
ROADMAP.json（および必要なら ADR）更新 → 次の autopilot 実行可能状態に
```

**review は冪等で、マイルストーン境界に複数回挟める**：

```
[マイルストーン到達]
  → review #1 → 修正実行
  → ユーザが触って気付く
  → review #2 → 修正実行
  → ユーザが触って気付く
  → review #3 → 修正実行
  → ...（納得するまで繰り返し）
  → autopilot 再開
  → 次マイルストーン到達
  → review #1 ...
```

1 セッションの review 内で「思いついたら追加」を許す対話状態管理は**持たせない**。代わりに `autopilot review` を何度でも呼べる冪等コマンドとして設計する。

#### 2.7.4 分類判別ロジック（SKILL.md 内に明示すべき判定木）

```
要望を受け取る
  ↓
Q0: DESIGN/ に該当する ADR や VISION 項目はあるか？
  YES → ADR 影響を併記
  NO  → 進む
  ↓
Q1: 既存の AC で本来カバーされるべき内容か？
  YES → ① AC 違反
  NO  → Q2
  ↓
Q2: 1〜2 タスクで完結する小規模な改善か？
  YES → ② 小修正
  NO  → Q3
  ↓
Q3: 既存 ROADMAP の方向性および ADR と整合するか？
  YES → ③ 新スコープ
  NO  → ④ 方向転換
```

判定が曖昧なときの保守的ルール：
- **① か ② で迷ったら ① 寄りで提案**（AC 見落としを残すリスクの方が大きい）
- **② か ③ で迷ったら ③ 寄りで提案**（直近 Sprint を汚さない方が安全）
- **③ か ④ で迷ったら ④ 寄りで提案**（load-bearing decision の見落としを避ける）

#### 2.7.5 Sprint 再オープンの仕様（① の詳細）

| 状態変化 | 内容 |
|---|---|
| Sprint status | `done` → `in_progress` に戻す |
| 該当 AC status | `pass` → `fail` に戻し、`reopened_at: <timestamp>` を追加 |
| 補修タスク追加 | 該当 Story の `tasks` に修正タスクを追記、または fix-Story を追加 |
| sprint-logs | `docs/sprint-logs/{SprintID}/reopen.json` を追加（理由・タイミング記録） |
| 進捗カウント | `progress.done` を再計算 |

`reopen.json` のスキーマ案：
```json
{
  "sprint_id": "S004",
  "reopened_at": "2026-05-16T10:00:00Z",
  "triggered_by": "milestone_review",
  "milestone": "M02",
  "reason": "AC 違反: ログイン成功時にトークンが localStorage に保存されていなかった",
  "affected_acceptance_criteria": ["AC-S004-3"],
  "added_stories": [],
  "added_tasks": [
    {"story": "S004-2", "task_id": "T-fix-001", "description": "localStorage へのトークン保存処理を追加"}
  ]
}
```

#### 2.7.6 補修 Story 追加の仕様（② の詳細）

done 済み Sprint に Story を追加するのは agile の現実としてはよくある。**ユーザに配置を選ばせる**：

| 配置先 | 動作 |
|---|---|
| 直近 done 済み Sprint（デフォルト） | 該当 Sprint の `stories` に追加。`added_in_review: <milestone>` フィールド付き |
| 次 Sprint | 次 Sprint（または新規 Sprint）に追加 |

`added_in_review` フィールドにより、「後付けで追加された Story」と「元から計画された Story」が履歴上区別できる。

```json
{
  "sprints": {
    "S005": {
      "title": "ログイン UI 調整",
      "status": "done",
      "stories": {
        "S005-1": { "...": "元から計画された Story" },
        "S005-fix-1": {
          "title": "ボタン色をブランドカラーに変更",
          "status": "todo",
          "added_in_review": "M02"
        }
      }
    }
  }
}
```

#### 2.7.7 方向転換の仕様（④ の詳細、DESIGN/ ありの場合）

DESIGN/ が存在する場合、④ 方向転換は以下のフローで処理：

```
1. autopilot review が ④ と分類
2. design refresh を内部実行し、整合性チェック
   - 既存 ADR との矛盾
   - broken links（変更で参照されなくなる entity 等）
3. 影響範囲をユーザに提示
4. ユーザ承認後、design adr で新 ADR 追加 or supersede
5. sprint roadmap 再実行（必要なら）
6. 後続 Sprint の ROADMAP.json 更新
```

DESIGN/ が無い場合は従来通り `sprint roadmap` 再実行のみ。

#### 2.7.8 Comprehension report の自動生成

Loop Engineering（Addy Osmani）が警告する **comprehension debt** に対応するため、マイルストーン到達時に「何が変わったか」のユーザ向け要約レポートを自動生成する。

これは「autopilot が高速に変更を積むほど、ユーザの理解が追いつかなくなる」問題への明示的な対抗装置。`autopilot review` を実行する**前に**ユーザがこのレポートを読むことを前提とする。

ファイル: `docs/sprint-logs/{SprintID}/comprehension-report.md`

**レポート構造（4 セクション固定）**:

| セクション | 内容 |
|---|---|
| **What changed** | 主要な変更点を**意味単位**で記述（ファイル単位の diff ではなく、「認証フローが OAuth から magic link に変わった」のような抽象度） |
| **Why this way** | 採用された設計判断と却下された代替案。`decisions.json` の human-readable サマリ。ADR が新規作成された場合はそれも参照 |
| **What to verify** | ユーザが目で確認すべき箇所。特に `compromises.json` の severity=high 項目と、verifier sub-agent が指摘した違反 |
| **What was assumed** | 暗黙の前提（後で破綻しうるもの）。autopilot が「とりあえずこれで」と判断した可逆な選択肢のうち、影響範囲が広いもの |

**生成タイミング**:
- マイルストーン到達時、`compromises.json` 生成の直後に自動実行
- autopilot は完走後に「review を始める前に comprehension-report.md を読んでください」とユーザに明示
- `autopilot review` の最初のステップとして、このレポートが存在するか確認し、無ければ生成

**意図的な設計選択**:
- Markdown 形式（JSON ではない）: 人間が読むためのドキュメントなので、機械処理よりも可読性を優先
- ファイル単位の diff ではなく**意味単位**: ユーザの理解を深めるのが目的であり、diff は git で見れば十分
- レポート自体は autopilot が生成するが、内容の正確性は verifier sub-agent (§2.6.2) が別途検証する選択肢を残す（将来拡張）

### 2.8 design スキルの位置づけと既存スキルとの統合

#### 2.8.1 design スキルのスコープ

「load-bearing decisions のみ」を扱うスキル。詳細は `skills/design/SKILL.md` の `## Scope discriminator` を参照（4 条件 OR：複数 Sprint をまたぐ / 非可逆 / 他が依存する契約 / 実質的トレードオフ）。

#### 2.8.2 design と autopilot review の責務分担

| | スコープ | 出力 | 起動 |
|---|---|---|---|
| `design refresh` | DESIGN/ 内の整合性（ADR 間矛盾、broken links） | レポート（自動修正なし） | ユーザ明示 or autopilot review 内部呼び出し（④ 方向転換時） |
| `autopilot review` | マイルストーン後のユーザ要望分類 | 4 分類 → 各機構へ振り分け | マイルストーン到達後 |

互いに排他ではなく、④ 方向転換時には autopilot review が design refresh を内部実行する関係。

#### 2.8.3 design スキルの修正要点

現状の `skills/design/SKILL.md` には以下の改善余地がある（v0.3 で追記）：

1. **トリガー過剰**: 「アプリ作りたい」「新規プロジェクト」等の広いトリガーは削減し、「複雑な」「本格的な」などの複雑性示唆語を必須化、または明示コマンドのみ起動に変更
2. **スキーマの owner 不整合**: `../autopilot/references/VISION_SCHEMA.json` を参照しているが、論理的には design が owner であるべき。スキーマを design 配下に移管（autopilot からは参照する）
3. **autopilot review との連携明記**: ④ 方向転換時のフローを SKILL.md に追記
4. **ADR 必要性チェックの自動化**: sprint plan 中に load-bearing decision が出てきた場合、Claude が自動で「ADR 必要では？」と提案するフローを明示

詳細は §5 Phase 1 のタスクで実装する。

### 2.9 後方互換性ポリシー

このリファクタリングを既存プロジェクト（既に ROADMAP.json や DESIGN/ を持つプロジェクト）に適用したとき、**既存データは無傷で引き継げる**ことを設計原則とする。

#### 2.9.1 基本原則

| 原則 | 内容 |
|---|---|
| **既存ファイルは書き換えない** | リファクタ実装時、既存の ROADMAP.json / VISION.json / DESIGN/ / sprint-logs/ を自動変換しない |
| **新フィールドは optional** | スキーマ拡張で追加されるフィールドはすべて optional。存在しなくてもデフォルト値で動作する |
| **新規ファイルは on-demand** | compromises.json / reopen.json / verification-report.json / comprehension-report.md は、必要になった時点で生成。既存 Sprint に遡って作らない |
| **過去への遡及適用はしない** | done 済み Sprint への新ルール適用は手動対応。自動で書き換えない |

#### 2.9.2 スキーマ拡張の互換性

| 拡張箇所 | 追加フィールド | 既存ファイルへの挙動 |
|---|---|---|
| ROADMAP.json: Story | `added_in_review`, `reopened_at` | フィールド無しでも正常読み込み。「元から計画された Story」として解釈 |
| ROADMAP.json: Sprint | `corrections` 配列 | 無ければ空配列扱い |
| ROADMAP.json: AC | `reopened_at` | 無ければ `pass` 状態の通常 AC として扱う |
| sprint-logs/{SprintID}/ | `compromises.json` | 無ければ「妥協なし」または「過去 Sprint で記録対象外」と表示 |
| sprint-logs/{SprintID}/ | `reopen.json` | 無ければ「再オープン履歴なし」 |
| sprint-logs/{SprintID}/ | `verification-report.json` | 無ければ「verifier 未実行」と表示 |
| sprint-logs/{SprintID}/ | `comprehension-report.md` | 無ければ `autopilot review` 起動時に生成。過去 Sprint には遡って生成しない |
| ADR | （現状維持、拡張なし） | 影響なし |

#### 2.9.3 実装ガイドライン

Claude Code がスキルを実装するときに守るべき具体的ルール：

1. **JSON 読み込み時の防御的プログラミング**: `roadmap.stories[id].added_in_review` のようなアクセスは optional chaining や default 値で守る
2. **新フィールドの書き出し条件**: 値が意味を持つ場合のみ書き出す。null や空配列でフィールドを増やさない
3. **既存ファイル変換コマンドを作らない**: `sprint migrate` のような一括変換コマンドを実装しない。データの非可逆変更を避ける
4. **ユーザがおせっかいを断れる**: もし Claude が「既存 ROADMAP.json を新スキーマに合わせて整理しましょうか？」と提案する場合、デフォルトは **No**。明示承認後のみ実行
5. **スキーマバージョン管理は当面しない**: 各 JSON にバージョンフィールドを入れるのは複雑性を増やすため避ける。後方互換は「フィールド追加のみ、削除しない」というルールで担保

#### 2.9.4 移行時の挙動

既存プロジェクトで新スキルを起動した場合の動作：

| シナリオ | 挙動 |
|---|---|
| 既存 ROADMAP.json を `autopilot status` で読む | 正常に表示。新フィールドが無い箇所は「-」または「N/A」 |
| 既存 done Sprint に対して `autopilot review` を呼ぶ | 「この Sprint の compromises.json / comprehension-report.md は存在しません。新ルールは次の Sprint から適用されます」と表示 |
| 既存 in_progress Sprint で `sprint verify --auto` を呼ぶ | 通常通り動作。verifier sub-agent も起動 |
| 既存 DESIGN/ がある状態で `autopilot review` ④ が発火 | design refresh を通常通り実行 |
| ROADMAP.json はあるが VISION.json が無い | autopilot setup 相当の簡易 VISION を生成 or design start を提案 |

#### 2.9.5 過去 Sprint への遡及適用の扱い

「過去 Sprint も実は AC 違反だったのでは？」とユーザが後から気付いた場合：

- **自動修正はしない**。Claude が勝手に過去 Sprint を `in_progress` に戻すことは禁止
- ユーザが明示的に「Sprint S004 を再オープンしたい」と指示した場合のみ、§2.7.5 のフローを適用
- その際 `reopen.json` の `triggered_by` は `manual_retroactive` とし、自動レビュー由来と区別する

---

## 3. コマンド体系の再設計

### 3.1 外向きコマンド（ユーザが直接叩く）

| コマンド | 役割 | 旧コマンドとの対応 |
|---|---|---|
| `project init` | プロジェクト初期セットアップ | 維持 |
| `design start` | load-bearing decisions の対話的設計 | 維持 |
| `design adr` | 新規 ADR 追加 | 維持 |
| `design refresh` | DESIGN/ 整合性チェック | 維持 |
| `design status` | DESIGN/ 状態表示 | 維持 |
| `autopilot` | 次のマイルストーンまで自走（メイン操作） | `sprint auto` を拡張 |
| `autopilot review` | マイルストーン到達後の修正要望を分類・振り分け（冪等） | 新規（§2.7 参照） |
| `autopilot status` | 現在の進捗・直近の compromises を表示 | 新規 |
| `sprint fix` | 一発修正（sprint ceremony 不要） | `sprint hotfix` をリネーム |
| `sprint idea` | アイデア収集して backlog へ | `sprint propose` をリネーム |
| `sprint roadmap` | VISION/DESIGN からロードマップ生成/再生成 | 維持 |

### 3.2 内部コマンド（autopilot から呼ばれる、ユーザは通常使わない）

`sprint plan`, `sprint prototype`, `sprint run`, `sprint verify`, `sprint demo`, `sprint refine`, `sprint done`, `sprint init`

これらは **削除しない**。SKILL.md の `when_to_use` から自動発火トリガーを外して、明示的に `sprint <command>` とタイプされた時のみ動作する。debug/manual override 用に残す。

### 3.3 トリガーフレーズの整理

#### sprint skill の when_to_use
```yaml
when_to_use: ユーザが「sprint <command>」と明示的にタイプした場合のみ発火。
            通常は autopilot 経由で呼ばれる。
```

削除すべき現在のトリガー：
- 「ここ直して」「ちょっと直して」「バグ修正」 → autopilot か `sprint fix` 側へ
- 「モック見せて」「プロトタイプ」 → autopilot 内部工程なので外向き語彙から削除
- 「次のスプリント」「スプリント開始」「機能追加したい」 → autopilot 側へ移管

#### autopilot skill の when_to_use（拡張）
```yaml
when_to_use: プロジェクト進行に関するあらゆる依頼。
            「次のスプリント」「進めて」「自走して」「機能追加したい」
            「こういうの欲しい」「次のマイルストーンまで」など。
            マイルストーン到達後の修正要望もここで受け付ける（review モードへ）。
```

#### design skill の when_to_use（絞り込み）
```yaml
when_to_use: load-bearing decisions（複数 Sprint をまたぐ／非可逆／他が依存する契約／
            実質的トレードオフ）を扱う必要がある場合のみ。
            「複雑な」「本格的な」「load-bearing」「アーキテクチャ」「設計判断」等の
            複雑性示唆語を含む依頼、または design <command> の明示呼び出しのみ起動。
            軽い「アプリ作りたい」「アイデアある」程度では起動しない。
```

---

## 4. スキル統合・廃止

| スキル | 扱い | 理由 |
|---|---|---|
| `project-init` | **維持** | 役割が明確、初回のみ使用 |
| `design` | **維持（中身は微修正）** | load-bearing decisions の owner として独立必要 |
| `sprint` | **維持（中身は再編）** | エンジン層として必須 |
| `autopilot` | **維持（主役に昇格）** | オーケストレーション責務は独立必要 |
| `gui-spec` | **`sprint/references/gui-spec.md` に降格** | sprint plan からしか呼ばれない。独立スキルである必要なし。`when_to_use` の自動発火を消す |

---

## 5. 実装タスク（Claude Code 向け作業項目）

実装は以下の順序で進める。各タスクは独立して commit 可能。

### Phase 1: 仕様の明文化（破壊的変更なし、最優先）

#### T1. `autopilot/SKILL.md` に「禁止カテゴリ」セクションを追加
- 場所: `## Constraints and Forbidden Actions` セクションを新設
- 内容: 本ドキュメント §2.4 の表をベースに記述
- 即時停止 / 完走後通知の二段階を明示
- `compromises.json` への記録方法を記述
- **ADR への暗黙の違反**を即時停止カテゴリに含めること

#### T2. `references/COMPROMISES_SCHEMA.json` を新規作成
- 場所: `skills/autopilot/references/COMPROMISES_SCHEMA.json`
- 内容: 本ドキュメント §2.5 のスキーマを JSON Schema 形式で記述
- `type`, `severity` の enum 値を確定
- `adr_ref` フィールドも含める
- **後方互換性 (§2.9)**: 既存 Sprint の sprint-logs/ に compromises.json が無い場合は「妥協なし」と表示し、過去に遡って生成しない

#### T3. `references/test-discipline.md` の Rule 6 を拡張
- 既存の「what you ship is what you test」を強化
- diff scan で検出する違反パターンを明文化（テスト skip、アサーション緩和等）
- 検出時の挙動（log → compromises.json）を記述

#### T4. `autopilot/SKILL.md` に `autopilot review` セクションを追加
- 場所: `## Commands` テーブルおよび `## Review Mode` セクションを新設
- 内容: 本ドキュメント §2.7 全体（4 分類、判別ロジック、Sprint 再オープン、補修 Story 配置、方向転換フロー）
- マイルストーン到達時に自動で「review しますか？」を提案するフローも記述
- 既存スキル（sprint verify / sprint fix / sprint idea / sprint roadmap / design adr / design refresh）への委譲方法を明示
- **冪等性要件**: 毎回の呼び出しで ROADMAP.json と compromises.json と DESIGN/ の最新状態を読み直すこと。前回の review 結果に依存する内部状態は持たないこと

#### T5. `references/REOPEN_SCHEMA.json` を新規作成
- 場所: `skills/sprint/references/REOPEN_SCHEMA.json`
- 内容: 本ドキュメント §2.7.5 の reopen.json スキーマを JSON Schema 形式で記述
- ROADMAP_SCHEMA.json 側にも `added_in_review`, `reopened_at` フィールドを追加して整合させる
- **後方互換性 (§2.9)**: 追加フィールドはすべて optional。既存 ROADMAP.json に `added_in_review` や `reopened_at` が無い Story / AC は、それぞれ「元から計画された Story」「pass 状態の通常 AC」として扱う
- `triggered_by` の enum に `manual_retroactive` を含める（過去 Sprint への遡及適用用、§2.9.5）

#### T6. `design/SKILL.md` のトリガー絞り込み
- 場所: SKILL.md の `when_to_use` フィールド
- 内容: 本ドキュメント §3.3 design skill 部分の通り
- 削除: 「アプリ作りたい」「新規プロジェクト」「アイデア相談」「ふわっとした」など広すぎるトリガー
- 残す: 「複雑な」「本格的な」「load-bearing」「アーキテクチャを固めたい」など複雑性示唆語、および明示コマンド

#### T7. `design/SKILL.md` に `autopilot review` 連携を明記
- 場所: `## Connection to sprint and autopilot` セクションを拡張
- 内容:
  - autopilot review が ④ 方向転換と分類した場合、内部で `design refresh` を呼び出す
  - その後 `design adr` で新 ADR or supersede
  - 最終的に `sprint roadmap` 再実行へ
- ADR 必要性自動チェック: sprint plan 中に load-bearing decision の兆候を Claude が検出したら、「ADR が必要では？」とユーザに確認するフロー
- `references/adr-template.md` に「ADR を要求すべき兆候」の判別基準を厳密化（次のタスク T8 で実施）

#### T8. `references/adr-template.md` に「ADR を要求すべき兆候」を追加
- sprint plan 中の判断で以下に該当したら ADR 提案：
  - 同一の問題に対し複数の選択肢があり、判断結果が他 Story にも影響する
  - データ構造・API 契約・プロトコルを定義しようとしている
  - 「とりあえずこれで行こう」と決めた判断が、後で変更困難になる可能性が高い
- 該当しない場合は decisions.json への記録のみで OK（autonomous decision）

#### T9. スキーマ owner の整理
- 移動: `skills/autopilot/references/VISION_SCHEMA.json` → `skills/design/references/VISION_SCHEMA.json`
- 移動: `skills/autopilot/references/DESIGN_PRINCIPLES_SCHEMA.json` → `skills/design/references/DESIGN_PRINCIPLES_SCHEMA.json`
- 更新: `autopilot/SKILL.md` 内の参照を新しいパスに変更
- 理由: VISION と DESIGN_PRINCIPLES は design スキルが生成・所有するため、設計の owner と schema の owner を一致させる
- 注意: autopilot setup の簡易 VISION 生成機能は維持。ただし「より厳密な版を design が生成する」関係を明示

#### T22. verifier sub-agent の導入（§2.6.2）
- 新規ファイル: `skills/sprint/references/verifier-agent.md`
  - verifier sub-agent のプロンプト全文（「疑い深く、批判的に、自己保身せず検証する」スタンス）
  - 検証対象: AC 達成、禁止カテゴリ違反、ADR 整合性、compromises 網羅性
  - read-only 制約の明示
- 新規ファイル: `skills/sprint/references/VERIFICATION_REPORT_SCHEMA.json`
  - `docs/sprint-logs/{SprintID}/verification-report.json` のスキーマ
  - autopilot 自己申告 vs verifier 判定の食い違いを記録するフィールドを含む
- `sprint/SKILL.md` 更新: `sprint verify` に `--with-verifier` フラグを追加
  - デフォルトは現状通り（同一セッション）
  - `--with-verifier` 時は別 Claude セッションを spawn して検証
- `autopilot/SKILL.md` 更新: `--auto` 経由の sprint verify では自動で `--with-verifier` を有効化
- compromises.json 更新ルール: verifier 判定が autopilot 自己申告と食い違う場合、verifier 側を採用し「autopilot による見逃し」として明示記録

#### T23. comprehension-report.md の自動生成（§2.7.8）
- 新規ファイル: `skills/autopilot/references/comprehension-report-template.md`
  - 4 セクション固定構造（What changed / Why this way / What to verify / What was assumed）
  - 各セクションの記述ガイドライン（意味単位、可読性優先）
- `autopilot/SKILL.md` 更新:
  - マイルストーン到達時、compromises.json 生成の直後に comprehension-report.md を自動生成
  - 完走後にユーザへ「review 前に comprehension-report.md を読んでください」と明示
- `autopilot review` の起動フロー更新:
  - 最初のステップとして comprehension-report.md の存在確認
  - 無ければその場で生成してからユーザ要望を聞く
- 出力先: `docs/sprint-logs/{SprintID}/comprehension-report.md`

### Phase 2: コマンド体系の再編（後方互換維持）

#### T10. `sprint` コマンドに `--auto` フラグを追加
- 各 sprint コマンド（plan/run/verify/done/etc.）が `--auto` フラグを受け取る
- `--auto` 時の挙動：迷ったら decision log に記録して自己判断で進む
- 既存 `sprint auto` コマンドは Phase 3 で削除予定だが当面維持

#### T11. `autopilot/SKILL.md` を「主役」想定に書き換え
- `when_to_use` を §3.3 の通りに拡張
- ユーザ意図トリガー（「進めて」「機能追加したい」等）を sprint から移管
- 内部実装は sprint を `--auto` 付きで呼ぶ形に統一

#### T12. `sprint/SKILL.md` の `when_to_use` を狭める
- §3.3 の通り「明示的にタイプされた場合のみ」に変更
- 「ちょっと直して」「バグ修正」等の広いトリガーを削除
- ただし `sprint fix`（旧 hotfix）と `sprint idea`（旧 propose）は外向き継続

#### T13. コマンドリネーム
- `sprint hotfix` → `sprint fix`（旧名は alias として残す or deprecation warning）
- `sprint propose` → `sprint idea`（同上）

#### T14. `autopilot status` コマンドを新規実装
- 現在の Sprint 進捗を表示
- 直近マイルストーンの compromises.json サマリを表示
- ROADMAP.json の主要指標（progress.percentage 等）を表示
- DESIGN/ がある場合は ADR 数・open question 数も表示

### Phase 3: スキル統合（破壊的変更あり、段階的に）

#### T15. `gui-spec` skill を sprint/references/ に降格
- `gui-spec/SKILL.md` の内容を `skills/sprint/references/gui-spec.md` に移動
- `gui-spec/` ディレクトリと `install.sh` のシンボリックリンク作成を削除
- sprint plan / sprint prototype の reference 参照を更新

#### T16. `sprint auto` コマンドの deprecation
- `autopilot` コマンドに完全移行
- 当面は alias として残し、warning を出す

### Phase 4: README 更新 + 移行ガイド

#### T17. ルート README を新構造で書き換え
- 主役を autopilot に変更
- 外向きコマンド一覧を中心に説明（§3.1 の表）
- スキル 4 層構造（design / project-init / sprint / autopilot）を明示
- design は「複雑な案件のみ」と位置づけを明示
- sprint の個別コマンドは「Advanced/Debug 用」セクションに格下げ

#### T24. 既存プロジェクト移行ガイドを作成
- 新規ファイル: `docs/MIGRATION.md`（リポジトリルートではなく `docs/` 配下に置き、README から参照）
- 内容（本ドキュメント §2.9 に基づく）:
  - 後方互換性ポリシーの要約（既存ファイルは触らない、新フィールドは optional、過去には遡及適用しない）
  - 移行手順（バックアップ → 新スキル install → `autopilot status` で動作確認 → 次 Sprint から新ルール適用）
  - シナリオ別の挙動表（§2.9.4）
  - 過去 Sprint への手動遡及適用の手順（`triggered_by: manual_retroactive`、§2.9.5）
  - トラブルシューティング（既存 ROADMAP.json で新スキルが正しく動かない場合の確認項目）
- README からのリンク追加: 「既存プロジェクトで使う場合は MIGRATION.md を参照」

### Phase 5: 中長期（必要に応じて）

#### T18. PostToolUse hook の実装
- Edit/Write ツール経由での test skip やアサーション弱体化を検知してブロック
- Claude Code の hooks 機構を使用
- L3 防御層として実装

#### T19. Stop hook の実装
- Sprint done 時に ARCHITECTURE.md / DESIGN/ の更新提案を生成
- Anthropic 記事の「self-improving setup」パターンを実装

#### T20. 設定レビューの定期化
- README に「設定レビュー: 3〜6 ヶ月ごと、または大型モデルリリース後」を明記
- 棚卸し候補（モデル進化で不要になった指示）の発見手順を簡潔に記載

#### T21. Claude Code 公式 Plugin format への移行
- skills + hooks + (optional MCP) を 1 パッケージとして配布できる構造に移行
- 将来の組織展開（NTT 東社内 marketplace 等）の布石

---

## 6. 設計判断の根拠（Why の記録）

### なぜスキルを統合せず 4 層を維持するのか
抽象レベルが本質的に異なるため。「load-bearing decisions」「初期化」「フェーズ実行」「フェーズ間の状態遷移」は別の認知的タスク。1 スキルに同居させると SKILL.md が肥大化し、Claude のコンテキスト効率も悪化する。

### なぜ `sprint auto` を `autopilot` に置き換えるのか
- ユーザ接点として `autopilot` の方が意図を表している
- `sprint --auto` フラグと `autopilot` コマンドが両立すると、どちらを使うべきか迷う
- 「auto は別モードではなく autopilot 本来の姿」という整理

### なぜ「即時停止」と「完走後通知」を分けるのか
- 即時停止カテゴリ（AC 改竄、Git 破壊、ADR 違反）は **後段の全作業の前提を壊す**ため、続行が無意味
- 通知カテゴリ（テスト緩和等）は **ローカルな妥協** であり、autopilot が止まると全体が止まる方が損失大きい。マイルストーン到達時にまとめてレビューすれば足りる

### なぜトリガーフレーズを大幅削減するのか
- 「ちょっと直して」で sprint ceremony が起動するのは over-engineering
- スキルの誤発火は信頼を毀損する（不要な ROADMAP 更新等が走るリスク）
- 記事のベストプラクティス: 「Skills can also be scoped to specific paths so they only activate in the relevant part of the codebase」と整合

### なぜ `gui-spec` を独立スキルから降格させるのか
- sprint plan からしか呼ばれていない（独立性の必要なし）
- 独立スキルだと auto-discovery で誤発火するリスクがある
- references/ に置けば sprint plan の reference として明示的にロードされる

### なぜマイルストーンレビューに新コマンドではなく「司令塔」を作るのか
- 既存の sprint verify / sprint fix / sprint idea / sprint roadmap / design adr で 4 分類すべてカバーできる
- 新規実装を追加するより、既存部品の組み合わせ方を定義する方が変更面積が小さい
- ユーザが覚えるべきは `autopilot review` だけ。内部の分類は Claude が判断

### なぜ done 済み Sprint への Story 追加を許すのか
- agile の現実として、「リリース後に細かい修正が積まれる」は普通に起こる
- 「補修は次 Sprint で」と強制すると、Sprint のスコープが不明確になり、history 上「いつの修正か」が曖昧になる
- `added_in_review` フィールドで「後付け」を明示すれば、履歴の正確性は保てる

### なぜ review を「対話状態を持つ」のではなく「冪等な再呼び出し」で実現するのか
- 1 セッション内で「思いついたら追加」のような対話状態を持たせると、Claude 側の状態管理が爆発する（要望リスト、分類結果、未確定項目、修正実行履歴...）
- 代わりに `autopilot review` を冪等に設計すれば、何度呼び出しても同じ振る舞いになり、「触る→気付く→review 再実行」を素直にループできる
- 各 review 呼び出しは ROADMAP.json と compromises.json と DESIGN/ の最新状態を読み直すので、前回の修正結果を踏まえた分類が自動でできる

### なぜ判別が曖昧なときに「① 寄り」「③ 寄り」「④ 寄り」と異なる方向のバイアスをかけるのか
- ① と ② の境界: AC 違反を見逃すと品質が下がる。多少過剰に拾う方が安全（保守的）
- ② と ③ の境界: 直近 Sprint に小修正を詰め込みすぎると Sprint の意味が薄れる。新スコープなら別 Sprint に分離（保守的）
- ③ と ④ の境界: load-bearing decision の見落としを避ける（保守的）
- いずれも「**判断ミスのコストが大きい方**を避ける」原則で統一

### なぜ design スキルの owner にスキーマを移管するのか
- 現状 `autopilot/references/VISION_SCHEMA.json` を design が参照しているのは「設計の owner」と「schema の owner」が逆転している状態
- スキーマ重複や drift のリスクがある
- design を source of truth にして、autopilot 側は「design が無い場合のみ簡易版を生成」する関係に整理する方がクリーン

### なぜ ④ 方向転換時に design refresh を内部実行するのか
- DESIGN/ がある場合、ROADMAP だけ変えると ADR との整合性が崩れる
- ADR は append-only なので、矛盾が生じたら新 ADR で supersede する手続きが必要
- これを自動で起こすことで、ユーザは「方向転換したい」と言うだけで設計ドキュメントの整合性が保たれる

### なぜ verifier sub-agent を導入するのか（Loop Engineering v0.4）
- Addy Osmani の Loop Engineering 記事が指摘する通り、「実装したエージェントは自分の成果物を甘く採点する」という self-grading bias は本質的な問題
- 現状の `sprint verify` は実装と同じ Claude セッションが verify するため、autopilot が「妥協ではない」と判断した違反は記録されない
- L1（プロンプト）〜 L3（hook）の 3 層防御はすべて「autopilot 自身」が検出する仕組みで、独立した第三者視点が無かった
- read-only の verifier sub-agent を別セッションで spawn し、批判的スタンスで検証することで、L1 の信頼性を底上げする
- トークンコストはかかるが、`--auto`（無人運転）時のみ有効化することでバランスを取る

### なぜ comprehension-report.md を自動生成するのか（Loop Engineering v0.4）
- Loop Engineering が「便利になりすぎることへの警告」として強調する **comprehension debt**（理解の負債）への直接の対策
- autopilot がマイルストーンまで全部やってしまうと、ユーザが「何が変わったか」を理解しないまま review に進む可能性がある
- diff を git で見れば差分は分かるが、**意味単位の変化**（「認証フローが変わった」「あの仕様前提が破棄された」）は人間向けに別途文書化が必要
- review 前にこのレポートを読むことを慣行化することで、「loop は理解の道具であって、理解の代替ではない」という思想を構造で担保する
- Markdown 形式で人間向けに最適化し、機械処理が必要な情報（compromises.json、decisions.json）とは責務を分ける

### なぜ既存データを書き換えず後方互換を維持するのか（v0.5）
- 既存プロジェクトは ROADMAP.json / DESIGN/ / sprint-logs/ という形で多くの履歴と判断を蓄積している。これらは Takumi の知的資産であり、リファクタのために変換するのは本末転倒
- 自動変換は不可逆な変更を伴うため、移行失敗時のリカバリが難しい
- 「新フィールドは optional、過去には遡及しない」というルールは単純で、Claude Code に実装させやすい
- スキーマバージョン管理を導入しない代わりに「フィールド追加のみ、削除しない」という規律で互換性を担保する設計の単純さを優先

### なぜ過去 Sprint への自動遡及適用をしないのか（v0.5）
- 「過去も実は AC 違反だったかも」という指摘は重要だが、autopilot が勝手に過去を書き換えると、git 履歴と ROADMAP.json の整合が崩れる
- 過去の判断は当時の文脈で行われたものであり、現時点の基準で機械的に再評価するのは誤りを生む可能性が高い
- 必要なら **ユーザの明示指示**で `manual_retroactive` として記録する余地を残しておけば十分
- これにより「過去は守る、未来は厳しく」という運用ポリシーが構造的に支えられる

---

## 7. 未決事項・将来の検討課題

| 項目 | メモ |
|---|---|
| MCP server との統合 | GitHub Issues/Projects と ROADMAP.json を双方向同期する MCP があるとチーム展開しやすい。優先度低 |
| プラグイン化 | Claude Code 公式 Plugin format への移行（T21）。skills + hooks + MCP を 1 パッケージで配布できる。組織展開時に検討 |
| 設定レビューの自動化 | 古くなった指示の検出。難易度高、当面は手動 |
| autopilot の並列実行 | 独立 Story の worktree 並列実行は既存。マイルストーン単位の並列はスコープ外 |
| ADR 必要性チェックの精度向上 | T8 の判別基準は初版。実運用でブラッシュアップ予定 |
| design start の長尺対話の中断対応 | 3-phase dialogue の途中で保存・中断・再開する仕組みが必要かもしれない |
| **`autopilot --until <goal>` オプション** (Loop Engineering 由来) | Addy Osmani の `/goal` 相当。「マイルストーンまで」固定ではなく、検証可能なゴール条件を渡せるようにする。例: `autopilot --until "no high-severity compromises remain"`。verifier sub-agent (T22) が判定ロジックを担う。Phase 5 で検討 |
| **Plugin format 移行の優先度格上げ** (Loop Engineering 由来) | T21 は現状 Phase 5 だが、Loop Engineering は Plugins/Connectors を 5 要素の一つとしており、hooks や MCP との統合単位として重要。実用上の必要性が見えたら Phase 3 への格上げを検討 |
| **`autopilot review` 内の maker/checker 分離** (Loop Engineering 由来) | review の 4 分類判定も autopilot 自身がやっている。分類 agent と整合性検証 agent を分離すれば self-grading bias がさらに減るが、効果は限定的。T22 の verifier sub-agent パターンの応用として将来検討 |
| **「Loop は理解の道具であって理解の代替ではない」思想の明文化** (Loop Engineering 由来) | Addy Osmani の核心的警告 ("Two people can build the exact same loop and get completely opposite results")。Takumi 個人利用では暗黙でも問題ないが、NTT 東で組織展開する場合は README または別ドキュメントで明文化が必要。誤用防止のガバナンス文書として |
| **スキーマバージョニング** (v0.5 関連) | 現状は「フィールド追加のみ、削除しない」というルールで互換性を担保しているが、将来フィールド削除や型変更が必要になった場合、各 JSON にバージョンフィールドを導入する必要が出る。それまでは導入しない |
| **過去 Sprint への遡及適用の半自動化** (v0.5 関連) | 現状は完全手動（`manual_retroactive`）だが、頻度が高くなったら「過去 Sprint を一括チェックするバッチ」のようなツールが欲しくなるかもしれない。実用上の必要性が見えてから検討 |
| **MIGRATION.md の継続メンテ** (v0.5 関連) | スキル仕様が更新されるたびに MIGRATION.md も更新が必要。3〜6 ヶ月のレビュー時に必ず読み直す運用ルール化を検討 |

---

## 8. このセッションでの会話の文脈サマリ（Claude Code への申し送り）

このリファクタリングは、Anthropic の記事「How Claude Code works in large codebases: Best practices and where to start」(2026-05-14) を Takumi が読み、現状の `tjst-t/claude-skills` をベストプラクティスに照らして点検したことから始まった。

### 議論の流れ
1. **初期評価**: progressive disclosure 実装やトークン意識は記事推奨と整合。Hooks 欠落・トリガー過剰・gui-spec 独立性などにギャップあり。
2. **実利用パターンの聴取**: 「autopilot が主、個別 sprint コマンドはほぼ使わない」「自己判断で進めてほしい、ただしテストスキップ等は NG」「マイルストーンまで自走、GUI は prototype 承認後」と判明。
3. **2 層構造の維持決定**: sprint（エンジン）+ autopilot（オーケストレータ）の抽象レベル差は本質的。統合せず、`--auto` フラグで橋渡し。
4. **マイルストーンレビュー設計**: 4 分類フレームワークと `autopilot review` 司令塔を新設。新コマンドではなく既存スキルへの委譲で実現。
5. **冪等性の明確化**: review を冪等にすることで「触りながら気付く」インタラクティブ実利用を状態管理なしで実現。
6. **design スキルの統合**: 後から push された design スキルを 4 層目として正式に組み込み、autopilot review との連携・スキーマ owner 整理・トリガー絞り込みを追加。
7. **Loop Engineering からの反映 (v0.4)**: Addy Osmani の Loop Engineering 記事を読み、self-grading bias と comprehension debt への対策が claude-skills に欠けていることを確認。verifier sub-agent（T22）と comprehension-report.md（T23）を Phase 1 に追加。残りの示唆（`/goal` 相当、Plugin 格上げ、review 内の maker/checker 分離、思想的警告の明文化）は §7 未決事項にメモとして記録。
8. **後方互換性ポリシーの明文化 (v0.5)**: 既存プロジェクトの ROADMAP.json / DESIGN/ / sprint-logs/ を引き継げることを保証する設計原則（§2.9）を追加。新フィールドは optional、過去への遡及適用はしない、自動変換コマンドを作らない、を明示。既存プロジェクト移行ガイド（T24, MIGRATION.md）を Phase 4 に追加。

### 設計の核となる思想
- **抽象レベルに応じたスキル分離**（4 層）
- **ユーザの語彙を主役に、内部工程は隠す**（autopilot 主役、sprint 内部化）
- **冪等な再呼び出しで状態管理を回避**（autopilot review）
- **load-bearing decisions を明示的に管理**（design + ADR）
- **判断ミスのコストが大きい方に寄せる保守的バイアス**（分類判定）
- **maker と checker の分離で self-grading bias を回避**（verifier sub-agent、v0.4 追加）
- **理解を構造で担保する**（comprehension-report.md、v0.4 追加）
- **既存資産を守る、未来を厳しくする**（後方互換性ポリシー、v0.5 追加）