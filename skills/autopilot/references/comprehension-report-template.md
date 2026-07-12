# comprehension-report template

The template and writing guide for `docs/sprint-logs/{SprintID}/comprehension-report.md`. autopilot generates this at every milestone boundary, immediately after `compromises.json`, as the direct countermeasure to **comprehension debt** (Loop Engineering, Addy Osmani): the faster autopilot stacks changes, the less the user understands what happened. The user is expected to read this report **before** running `autopilot review`.

## Why this exists (don't delete this intent)

- A git diff shows *what bytes changed*. This report explains *what it means* — "the auth flow moved from OAuth to magic link", not "47 files changed".
- The loop is a tool for understanding, **not a replacement for it**. This report is the structural guarantee that the user can still reason about the system after a milestone of autonomous work.

## Format rules

- **Markdown, not JSON.** This is for a human to read. Machine-readable detail lives in `compromises.json` / `decisions.json` / `verification-report.json`; do not duplicate it here.
- **Semantic units, not file lists.** Describe behavior changes at the level a product owner thinks in. If you catch yourself pasting a file path list, stop and abstract.
- **Five sections, fixed.** Always all five, in this order, even if a section is short ("No load-bearing assumptions this milestone."). "How to run it" comes first so the PO can open the app before reading what changed.

## Generation timing

- At milestone arrival, right after `compromises.json` is written.
- autopilot then tells the user, verbatim in spirit: *"review を始める前に `docs/sprint-logs/{SprintID}/comprehension-report.md` を読んでください。"*
- `autopilot review`'s first step re-checks that this file exists for the milestone's Sprints; if missing, it generates the report before asking the user for requests.

## Template

```markdown
# Comprehension Report — {Milestone label} (Sprints {list})

_Generated at milestone arrival. Read this before `autopilot review`._

## How to run it

<!-- The PO reviews by *touching* the app, not by reading a diff. Give the single
     fastest path to a running, interactive build: a deployed URL, or a 1-command
     start (`make serve` → http://localhost:PORT), plus the dev login if one is
     needed. If a step needs manual setup (env var, seed data), say so explicitly —
     that friction is a DoD defect worth a self-audit item 4 note. Keep it to the
     commands the PO actually types. -->
- e.g. `make serve` → http://localhost:5173 （dev ログイン: 右上「dev login」ボタン、トークン自動投入）
- e.g. デプロイ済み: https://staging.example.com （seed 済み。管理者は admin@example.com / dev トークン）

## What changed

<!-- Meaning-level summary of what the system now does that it didn't before.
     One bullet per semantic change. NOT a file diff. -->
- e.g. 認証フローが OAuth から magic link に変わった。ユーザはパスワード入力なしでメールのリンクからログインする。
- e.g. VM 一覧に「停止中のみ表示」フィルタが追加され、デフォルトで全件表示のまま。

## Why this way

<!-- The design choices that were made and the alternatives that were rejected.
     Human-readable summary of decisions.json. Reference any new ADR. -->
- e.g. magic link を選択（却下: OAuth 継続 — provider 障害時にログイン不能になるリスクを VISION の可用性目標が許さない）。→ ADR-0009 を新規作成。
- e.g. フィルタはクライアント側で実装（却下: API クエリパラメータ — 現状の一覧件数では over-engineering、reversibility_cost low）。

## What to verify

<!-- Where the user should look with their own eyes. Pull in:
     - compromises.json entries with severity == high
     - verifier (verification-report.json) findings with overlooked_by_autopilot == true or verdict fail/warn
     - anything where the test passed but the behavior is worth a human glance -->
- ⚠️ (high) `tests/auth.spec.ts`: トークン検証アサーションを緩めた。OAuth mock 整備までの暫定。
- ⚠️ (verifier overlooked) AC-Sa3f9c2-2-3: テストは pass だが localStorage への保存処理が実コードに無い。→ ① AC 違反候補。
- magic link メールの文面と有効期限（実際に届くメールを確認）。

## What was assumed

<!-- Implicit, reversible-but-wide-impact choices autopilot made as "とりあえずこれで".
     These are the things most likely to break later if the assumption was wrong. -->
- magic link の有効期限を 15 分と仮定（設定化していない）。要件があれば DESIGN_PRINCIPLES に追記。
- メール送信は既存の SMTP 設定を流用すると仮定。本番送信ドメインの DKIM 設定は未確認。
```

## Cross-references

- `compromises.json` — the machine-readable compromise list this report's "What to verify" section summarizes (severity=high items especially).
- `verification-report.json` — the verifier's independent findings; `overlooked_by_autopilot` items belong in "What to verify".
- `decisions.json` — the raw decision log behind "Why this way".
- The verifier sub-agent (`../../sprint/references/verifier-agent.md`) MAY, as a future extension, also verify the accuracy of this report; for now autopilot generates it and the verifier checks the underlying facts.
