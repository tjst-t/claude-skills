# Test Discipline

The single source of truth for what counts as a valid test in this skill. `sprint plan`, `sprint run`, `sprint verify`, `sprint done`, `sprint auto`, and `gui-spec` all defer to this document. When something here changes, no other file needs to change.

## The Eight Rules

### 1. Every Story has a user scenario

Before `sprint run` begins, every Story must have one of:
- `docs/sprint-logs/{SprintID}/scenario-{StoryID}.json` — for `cli` / `api` / `library` / `mixed` Stories. Format: see `story-scenarios.md`.
- `docs/sprint-logs/{SprintID}/gui-spec-{StoryID}.json` — for `gui` Stories. Produced by `gui-spec`.

A scenario is the literal step-by-step sequence of actions the user performs through their real entry point, and the observations the user makes after each step. Every acceptance criterion must be exercised by at least one scenario step.

### 2. Tests drive the user's entry point — never a layer below

| Story type | The test must drive | Forbidden |
|---|---|---|
| `cli` | A subprocess of the real built binary, asserting on stdout / stderr / exit code / files | importing internal packages, invoking `main()` in-process |
| `api` | A real HTTP client against the running server, with the same auth a real consumer uses | calling handler functions directly, single-handler `httptest.ResponseRecorder`, bypassing routing or middleware |
| `gui` | A real Playwright browser (Chromium/Firefox/WebKit) against the real frontend, with traffic flowing to the real backend | `page.route()`, MSW, `setupServer`, `fetch.mockImplementation`, `vi.mock`, `jest.mock` on any network surface; `page.evaluate` to bypass UI interactions for non-time-domain steps; injecting auth tokens into storage as the *only* auth path |
| `library` | A separate consumer-style program that imports only the package's public API | reaching into unexported symbols |
| `mixed` | Each declared entry point has its own scenario block, all of which execute | omitting any block |

Layer-internal tests (unit tests against an internal handler, a fake transport, etc.) are fine as supplementary coverage but never replace the scenario-driven E2E.

### 3. No silent skips

Every acceptance criterion's test must complete with status `pass` in the most recent `verification-results.json`. The following all count as **NOT executed** and block the Sprint:

- `test.skip(...)` / `it.skip(...)` / conditional skip annotations
- File excluded from the run config
- Test marked `pending`
- "Verified manually" / "tested with curl" / "inspected the diff" — none of these are tests
- Any AC without a corresponding test entry in `verification-results.json`

If a test genuinely cannot run (missing credentials, undocumented business rule, environment Claude Code cannot provision), this is a `needs_human` escalation logged to `failures.json`. It is **never** an autonomous decision to skip.

### 4. GUI E2E observes UI state, not intermediate state

The `*.e2e.spec.ts` for every GUI Story must:
- Launch a real Playwright browser context
- Issue user actions through user-observable affordances (`page.click`, `page.fill`, `page.keyboard.press`, navigation via the rendered UI)
- Include at least one assertion on **user-visible UI state that depends on the backend round-trip** (rendered list item, success toast, updated badge, URL change). Asserting only on a loading spinner or pre-network state does not qualify.
- Exercise the real login UI at least once per session (a `loginViaUI` helper is fine); pure storage-injection auth is rejected unless a separate test covers login end-to-end.

Verification via grep, run by `sprint verify`:
```
page.route(   MSW   setupServer   fetch.mockImplementation   vi.mock   jest.mock
```
Any hit on the network surface in an `*.e2e.spec.ts` is rejected.

### 5. Status reflects reality

- A Story's `status: "done"` requires all its scenario steps to have been executed in a passing test in the most recent run.
- An AC's `status: "pass"` in ROADMAP.json requires at least one passing test entry in `verification-results.json` that lists the AC in its `acceptance_criteria` field.
- A Sprint's `status: "done"` requires all of the above for every Story it contains, plus `summary.skip == 0` and `summary.fail == 0` in `verification-results.json`.

Writing `pass` / `done` for tests that did not actually run in this Sprint is forbidden. `verification-results.json` is a record of executed verifications, not an aspirational checklist.

### 6. What you ship is what you test

Rules 1–5 ensure that everything *declared* (AC, scenarios) is tested. Rule 6 ensures that everything *implemented* is tested — including behaviors a sub-agent added "for completeness" without an AC. The Sprint's diff is the source of truth for what was implemented; every user-observable surface added in that diff must be exercised by a passing test in this Sprint's `verification-results.json`.

A "user-observable surface" added in the Sprint is anything a user could reach through their entry point. Examples:

- **API**: a new HTTP route registered in the router (`GET /api/v1/foo`, `POST /api/v1/bar`), or a new field added to an existing route's request/response
- **CLI**: a new subcommand, a new flag, a new positional argument, or a new output mode (verbose, json, etc.)
- **GUI**: a new screen / page route, a new interactive component (button, form, modal, drawer), a new visible state (empty / error / loading variants exposed to the user)
- **Library**: a new exported function, type, or constant

Internal helpers (unexported functions, private classes, internal modules not reachable from a user entry point) are NOT individually required to have dedicated tests — they're covered transitively by the tests that drive the user surface.

**During `sprint verify`**, scan the Sprint's diff against its base branch and enumerate every user-observable surface added. For each, confirm at least one passing test in `verification-results.json` exercises it:

- API route: a test issues a real HTTP request to that exact path+method
- CLI flag: a test spawns the binary with that flag and asserts on the resulting output
- GUI screen / component: a real-browser test navigates to it / clicks it
- Library export: a consumer-style test imports and calls it

If an addition is untested, the resolution is **one of**: (a) add an AC + scenario step + test in this Sprint, (b) revert the addition as out-of-scope, or (c) escalate as `needs_human` if Claude Code genuinely cannot decide. Silently shipping untested user-observable behavior is forbidden.

**During `sprint run`**, each implementation sub-agent must report a "user-observable additions" list alongside its results, so `sprint verify` has a head start instead of rediscovering everything from scratch.

### 7. 実機検証は本番モードで

priority_rule 9 「dev VM 実機 deploy + smoke test」要件を満たすテストは、本番と同じモード/フラグ/設定で実行されなければならない。

許容されない fake/mock:
- `MOCK=true` 環境変数
- `--fake-core` / `--mock-*` CLI フラグ
- `DRY_RUN=1` (実 destructive コマンド回避以外の用途で使うのは禁止)
- `proxy_fuse_fake_core: true` / `*_fake_*: true` 等の Ansible defaults
- in-process FakeCore / InMemoryStore (本番では CloudNativePG-backed 等が前提)

許容される dry-run:
- backup script (`meta-snapshot-export.sh DRY_RUN=1` で「実行するコマンドを echo するだけ」) を **smoke test の verify 用に呼ぶ** こと自体は OK
- ただしそれが「本番 backup が動いた証拠」にはならない。実 destructive コマンドが実行された証跡 (snapshot ファイル生成、S3 bucket への upload 等) が別途必要

priority_rule 9 例外条項を主張する Story は、`review_reason` に以下の障害シナリオ識別子の **いずれか** を含むこと:

`kill-9` / `停電` / `power-loss` / `ネットワーク遮断` / `network-partition` / `Shamir-unseal` / `disk-full` / `OOM` / `プロセスクラッシュ` / `process-crash`

これらのいずれも含まない `review_reason` は例外条項の不正適用であり、通常の実機 smoke 要件を課す。

由来: 2026-05-17 監査で Sprint 7 が `DRY_RUN=1` の harness 通過を「DR 訓練 done」と判定していたケースが Rule 7 違反として摘発された (`docs/audit/2026-05-17-phase1-readiness.md`)。

### 8. Data path Sprint は destructive multi-version scenario を必須化

「データロス禁止」 (priority_rule 1) を機械的に検証するため、data path (`internal/server/`, `internal/proxyfuse/`, `cmd/storage-core/`, `cmd/proxy-fuse/`, `cmd/workflow-worker/`, `internal/workflow/`, `internal/identity/`) を touch する Sprint は、以下 3 つの destructive scenario test を **最低 1 件** 持たねばならない:

| シナリオ | 期待される verification |
|---|---|
| **write x2 で v1/v2 独立** | 同一 (tenant, key) に 2 回 write を行い、それぞれ独立した version_no = 1, version_no = 2 として物理的に保存されることを確認 (同一物理キー上書き禁止 — ADR-0014 違反検出) |
| **Demote → Recall byte verify** | hot+cold な object を Demote → cold-only にし、その後 Recall して、Recall 直後の GetObject の sha256 / bytes.Equal が write 時と一致することを verify (cold tier round-trip でのデータ corruption 検出) |
| **Restart 整合** | proxy-fuse / storage-core のいずれかを `kill -9` / `systemctl restart` し、再起動後に state (committed objects / WAL replay 結果) が再起動前と一致することを verify (in-memory state の永続化漏れ検出) |

`tests/acceptance/devvm/multi_version_destructive_test.go` および同 dir 配下の test がこの責務を担う。

由来: 2026-05-23 audit RC-5 で「ADR-0014 違反 (write x2 → 同一物理キー上書き) が Sprint 2 から約 7 sprint silent 残置」が摘発された。原因は write x2 → v1/v2 独立性を verify する自動テストが欠如していたこと。Sprint 完了ゲート Guard 8 (`sprint-done-judgment.md`) と連動し、data path Sprint で destructive test が無ければ Story done 不可とする。

例外: Story が「Sprint プロセス強化」「ドキュメント retrofit」「ADR 文書追加」のような meta な性質を持ち、production code path を一切実装しない場合は n/a 扱い。decisions.json の `guard8_rationale` に明示すること。

## What disqualifies a test

A test does not count toward Sprint completion if it:

- Calls internal functions / handlers / packages instead of the user's entry point (Rule 2)
- Skips, comments out, or `TODO`-s any step in the scenario (Rule 1)
- Asserts only on a synthetic intermediate (mocked DB row, in-memory struct, loading state) instead of what the user observes (Rule 4)
- Stops short of the `expected` of any scenario step (Rule 1)
- Uses `page.route()` / MSW / fake fetch on the network path of a GUI E2E (Rule 2, Rule 4)
- Bypasses auth, routing, middleware, or serialization that real consumers must go through (Rule 2)
- For CLI: invokes via `go run` or chained build steps that bypass the produced artifact in a way the user wouldn't (Rule 2)

A Sprint also fails the gate if (Rule 6):

- The Sprint's diff introduces a user-observable surface (new route, new flag, new screen, new export) that no test in `verification-results.json` exercises

A Sprint also fails the gate if (Rule 7):

- A Story claims priority_rule 9 satisfaction but its smoke test runs under `MOCK=true`, `--fake-*`, `DRY_RUN=1`, in-process FakeCore / InMemoryStore, or `*_fake_*: true` defaults — and the Story is NOT a valid priority_rule 9 exception (障害シナリオ identifier in `review_reason`)

A Sprint also fails the gate if (Rule 8):

- The Sprint touches a data path directory (`internal/server/`, `internal/proxyfuse/`, `cmd/storage-core/`, `cmd/proxy-fuse/`, `cmd/workflow-worker/`, `internal/workflow/`, `internal/identity/`) but `tests/acceptance/devvm/` does NOT contain at least one passing destructive multi-version test (write x2 → v1/v2 独立、Demote→Recall byte verify、Restart 整合 のいずれか) — and the Sprint is NOT a documented `guard8_rationale: n/a` meta Sprint

If the only feasible way to make a test pass — or to cover an addition — is to violate one of these, escalate as `needs_human`. Do not weaken the test, do not silently ship the untested addition.

## Escalation

When a rule cannot be satisfied:
1. Log the diagnosis to `docs/sprint-logs/{SprintID}/failures.json` (what was tried, what failed, why Claude Code cannot resolve it).
2. Mark the affected Story `blocked` with a `needs_human` reason via `jq` mutation (see SKILL.md "Writes").
3. The Sprint stays `partial` / `in_progress`, NOT `done`. The user (or autopilot milestone review) handles it.
