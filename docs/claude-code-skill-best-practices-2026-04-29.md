# Claude Code Custom Skill Best Practices

> Snapshot: 2026-04-29
> Sources: Official Claude Code documentation (code.claude.com), Anthropic platform docs (platform.claude.com)

---

## Table of Contents

1. [SKILL.md 構造とフロントマター](#1-skillmd-構造とフロントマター)
2. [スキルの種類](#2-スキルの種類)
3. [スキルの配置場所と優先順位](#3-スキルの配置場所と優先順位)
4. [プロンプト記述のベストプラクティス](#4-プロンプト記述のベストプラクティス)
5. [ファイル構成パターン](#5-ファイル構成パターン)
6. [コンテキスト管理](#6-コンテキスト管理)
7. [スキル間連携パターン](#7-スキル間連携パターン)
8. [allowed-tools パラメータ](#8-allowed-tools-パラメータ)
9. [動的コンテンツ注入（バッククォート構文）](#9-動的コンテンツ注入バッククォート構文)
10. [サイズガイドラインと制限](#10-サイズガイドラインと制限)
11. [アンチパターンと一般的な間違い](#11-アンチパターンと一般的な間違い)
12. [最近の機能追加](#12-最近の機能追加)
13. [参考リソース](#13-参考リソース)

---

## 1. SKILL.md 構造とフロントマター

### 基本構造

```yaml
---
name: my-skill
description: What this skill does and when to use it
---

Markdown content with instructions...
```

### フロントマター全フィールド

| フィールド | 必須 | 上限 | 説明 |
|-----------|------|------|------|
| `name` | Yes | 64文字 | 小文字・数字・ハイフンのみ。`/slash-command` 名になる。XMLタグや予約語（"anthropic", "claude"）不可 |
| `description` | Yes | 1,024文字 | スキルの内容と使用タイミング。先頭に重要なユースケースを配置。スキル検出に使用される |
| `when_to_use` | No | - | descriptionに追加される補足コンテキスト。トリガーフレーズやリクエスト例。description + when_to_use で1,536文字に切り詰められる |
| `argument-hint` | No | - | オートコンプリートに表示。例: `[issue-number]`, `[filename] [format]` |
| `arguments` | No | - | 名前付き位置引数。`$name` で参照。スペース区切り文字列またはYAMLリスト |
| `disable-model-invocation` | No | - | `true` でClaudeの自動読み込みを防止。手動 `/name` 呼び出しのみ。サブエージェントへのプリロードも防止 |
| `user-invocable` | No | - | `false` で `/` メニューから非表示。バックグラウンド知識用 |
| `allowed-tools` | No | - | スキルアクティブ時に許可不要で使えるツール。スペース区切りまたはYAMLリスト |
| `model` | No | - | モデル上書き: `sonnet`, `opus`, `haiku`, フルモデルID, `inherit` |
| `effort` | No | - | 推論レベル上書き: `low`, `medium`, `high`, `xhigh`, `max` |
| `context` | No | - | `fork` で隔離サブエージェントコンテキストで実行 |
| `agent` | No | - | `context: fork` 時のサブエージェントタイプ: `Explore`, `Plan`, `general-purpose` |
| `paths` | No | - | スキルが有効化されるglobパターン。マッチするファイル操作時のみ自動読み込み |
| `shell` | No | - | `!command` 用シェル: `bash`(デフォルト) or `powershell` |
| `hooks` | No | - | スキルライフサイクルにスコープされたフック |
| `skills` | No | - | サブエージェントにプリロードするスキル名のリスト |

### 文字列置換変数

| 変数 | 説明 |
|------|------|
| `$ARGUMENTS` | スキル呼び出し時の全引数 |
| `$ARGUMENTS[N]` | 0ベースインデックスで特定引数にアクセス |
| `$N` | `$ARGUMENTS[N]` のショートハンド |
| `$name` | `arguments` フロントマターで定義された名前付き引数 |
| `${CLAUDE_SESSION_ID}` | 現在のセッションID |
| `${CLAUDE_EFFORT}` | 現在の推論レベル |
| `${CLAUDE_SKILL_DIR}` | SKILL.md が存在するディレクトリ |

---

## 2. スキルの種類

### Reference（参照型）
現在の作業に適用する知識。コーディング規約、パターン、ドメイン知識。常時利用可能。

```yaml
---
name: api-conventions
description: API design patterns for this codebase
---
When writing API endpoints...
```

### Task（タスク型）
副作用を伴うステップバイステップの指示。デプロイ、コミット、コード生成。`disable-model-invocation: true` で自動トリガー防止推奨。

```yaml
---
name: deploy
description: Deploy the application to production
disable-model-invocation: true
---
Deploy the application...
```

### Background（バックグラウンド型）
Claudeが知っておくべきだがユーザーが直接呼び出す必要のない知識。`user-invocable: false` で `/` メニューから非表示。

```yaml
---
name: legacy-system-context
description: How our legacy authentication system works
user-invocable: false
---
Our legacy auth handles...
```

---

## 3. スキルの配置場所と優先順位

### 配置階層

| 場所 | パス | スコープ |
|------|------|---------|
| Enterprise | 管理設定 | 組織全体 |
| Personal | `~/.claude/skills/<name>/SKILL.md` | 全プロジェクト（個人） |
| Project | `.claude/skills/<name>/SKILL.md` | 現プロジェクトのみ |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | プラグイン有効な場所 |

**優先順位**: Enterprise > Personal > Project

- プラグインスキルは `plugin-name:skill-name` の名前空間を使用
- `--add-dir` 内の `.claude/skills/` も自動読み込みされる
- 編集は即座に反映される（ライブ検出）
- モノレポのネストされた `.claude/skills/` も自動発見

---

## 4. プロンプト記述のベストプラクティス

### Standing Instructions（常時適用指示）で書く

スキルコンテンツは呼び出し時に1回だけ会話に入り、以降再読み込みされない。一度きりのステップではなく、タスク全体に適用される指示として書く。

**良い例:**
```markdown
When refactoring code:
- Preserve all public APIs
- Run tests after each change
```

**悪い例:**
```markdown
Step 1: Read the file
Step 2: Make changes
```

### Description の書き方

- **三人称で書く**: "Processes Excel files"（"I can help you" ではない）
- **先頭に重要なユースケース**: 1,536文字で切り詰められるため
- **具体的なトリガー用語を含める**: "Use when working with PDF files, spreadsheets, .xlsx files"
- **what と when の両方**: 何をするかと、いつ使うか

**良い例:**
```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

**悪い例:**
```yaml
description: Helps with documents
```

### 自己完結型プロンプト

- 会話の前コンテキストを前提としない
- 必要なコンテキストはスキル内に含める
- サポートファイルは明示的に参照する

---

## 5. ファイル構成パターン

### 基本構造

```
my-skill/
├── SKILL.md           # メイン指示（必須、500行以内推奨）
├── references/        # 詳細ドキュメント（オンデマンド読み込み）
│   ├── detailed-api.md
│   └── examples.md
├── scripts/           # 実行可能スクリプト
│   └── validate.sh
└── templates/         # テンプレートファイル
    └── output.md
```

### Progressive Disclosure（段階的開示）パターン

SKILL.md を概要に留め、詳細は別ファイルに分離:

```markdown
# Quick start
Basic instructions here...

## Advanced features
**Form filling**: See [references/forms.md](references/forms.md)
**API reference**: See [references/api.md](references/api.md)
```

### ガイドライン

- 参照ファイルは **SKILL.md から1階層** に留める（深いネスト禁止）
- 100行を超えるファイルには **目次** を付ける
- パスは **フォワードスラッシュのみ** 使用
- ファイル名は **説明的に**: `form_validation_rules.md`（`doc2.md` ではない）
- **ドメインまたは機能** で整理

---

## 6. コンテキスト管理

### スキルコンテンツのライフサイクル

| タイミング | 何がロードされるか |
|-----------|-------------------|
| 起動時 | スキルメタデータ（name, description）のみ |
| 呼び出し時 | SKILL.md 全文が会話に入る（セッション中維持） |
| 自動圧縮時 | 各スキル先頭5,000トークンを保持、全スキル合計25,000トークン上限 |

### Description のトークン予算

- コンテキストウィンドウの1%（最低8,000文字）
- 個別スキル: name + description + when_to_use で1,536文字上限
- `SLASH_COMMAND_TOOL_CHAR_BUDGET` 環境変数で上限変更可能

### コンテキスト節約のコツ

- `disable-model-invocation: true` でdescriptionすらコンテキストから除外
- サブエージェントを使って調査をメインコンテキストから隔離
- CLAUDE.md を肥大化させずスキルに分離

---

## 7. スキル間連携パターン

### パターン1: スキルから別スキルを参照

スキルが直接他のスキルを呼び出すことはできないが、指示に「Skill tool で呼び出せ」と書ける:

```markdown
After implementation, invoke `/review` via the Skill tool.
```

### パターン2: サブエージェントにスキルをプリロード

```yaml
---
name: researcher
skills:
  - api-conventions
  - error-handling-patterns
---
```

`skills` フィールドでサブエージェントの起動時にスキル全文を注入。`disable-model-invocation: true` のスキルはプリロード不可。

### パターン3: `context: fork` でサブエージェント実行

```yaml
---
name: deep-research
context: fork
agent: Explore
---
Research $ARGUMENTS thoroughly...
```

スキルコンテンツがサブエージェントのプロンプトになる。

---

## 8. allowed-tools パラメータ

スキルアクティブ時にユーザー許可なしで使えるツールを事前承認。ツールを制限するのではなく、追加の許可を付与する。

### 書式

```yaml
# スペース区切り
allowed-tools: Read Grep Bash(git *)

# YAMLリスト
allowed-tools:
  - Read
  - Grep
  - Bash(git add *)
  - Bash(git commit *)
```

### パターン構文（Bashのみ）

```yaml
allowed-tools: Bash(git add *) Bash(git commit *) Bash(npm *)
```

`*` は任意の文字列にマッチ。

### 注意点

- Claude Code CLI でのみ動作（SDKでは非対応）
- deny ルールは上書きしない
- 許可リスト外のツールも引き続き使用可能（通常の許可フローに従う）

---

## 9. 動的コンテンツ注入（バッククォート構文）

`` !`<command>` `` 構文でシェルコマンドをスキル送信前に実行し、出力でプレースホルダを置換。

### インライン形式

```markdown
Current branch: !`git branch --show-current`
PR diff: !`gh pr diff`
```

### 複数行形式

````markdown
```!
node --version
npm --version
git status --short
```
````

### 重要

- **前処理**: Claudeが実行するのではなく、スキル読み込み時に自動実行
- コマンドの出力がそのまま置換される
- `"disableSkillShellExecution": true` でポリシー的に無効化可能

---

## 10. サイズガイドラインと制限

| 項目 | 制限 | 備考 |
|------|------|------|
| スキル名 | 64文字 | 小文字、数字、ハイフンのみ |
| Description | 1,024文字 | 個別フィールド |
| Description + when_to_use | 1,536文字 | スキル一覧での表示上限 |
| SKILL.md 本体 | 500行推奨 | 詳細は別ファイルに分離 |
| スキル一覧予算 | コンテキストの1%（最低8,000文字） | `SLASH_COMMAND_TOOL_CHAR_BUDGET` で変更可 |
| 圧縮後保持 | 5,000トークン/スキル | 先頭部分が保持される |
| 圧縮後合計 | 25,000トークン | 最新呼び出しスキルから優先 |

---

## 11. アンチパターンと一般的な間違い

### コンテキスト関連

| 問題 | 対策 |
|------|------|
| 無関係なタスクが蓄積 | `/clear` でリセット |
| 何度も修正を繰り返す | 2回修正しても直らなければ `/clear` して最初から |
| CLAUDE.md が肥大化 | ルールを厳選、必要ならフックに変換 |
| 検証なしで信頼 | テスト・スクリプト・スクリーンショットで常に検証 |
| 無限探索 | スコープを絞るかサブエージェントを使う |

### スキル設計関連

| 問題 | 対策 |
|------|------|
| 複数のアプローチを提示 | デフォルトアプローチを1つ示し、特殊ケース用のエスケープハッチ |
| Claudeの知識を過信 | プロジェクト固有の情報は明示的に含める |
| 曖昧なdescription | 先頭にキーユースケース、具体的なトリガー用語を含める |
| 例がない | 入出力ペアで期待するスタイルを示す |
| 深いファイルネスト | 参照は1階層に留める |
| Windowsスタイルのパス | フォワードスラッシュのみ使用 |

---

## 12. 最近の機能追加

### Extended Thinking サポート

スキル内に "ultrathink" を含めると拡張思考が有効化:

```markdown
This skill uses ultrathink for deep analysis...
```

### スキル内フック

フロントマターでスキルライフサイクルにスコープされたフックを定義可能:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
```

### サブエージェントへのスキルプリロード

```yaml
skills:
  - api-conventions
  - error-handling-patterns
```

起動時にスキル全文を注入。`disable-model-invocation: true` のスキルはプリロード不可。

### Model / Effort 上書き

```yaml
model: opus
effort: max
```

モデル解決順序: 環境変数 > 呼び出し時パラメータ > スキルfrontmatter > メイン会話モデル

---

## 13. 参考リソース

- [Skills Documentation](https://code.claude.com/docs/en/skills.md) — スキル公式リファレンス
- [Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — ベストプラクティス
- [How Claude Code Works](https://code.claude.com/docs/en/how-claude-code-works.md) — コンテキスト管理、エージェントループ
- [Tools Reference](https://code.claude.com/docs/en/tools-reference.md) — ツールリファレンス
- [Sub-agents Documentation](https://code.claude.com/docs/en/sub-agents.md) — サブエージェント
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference.md) — プラグインスキル
