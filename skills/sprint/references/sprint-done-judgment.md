# Sprint Done 判定ガード (8 ガード)

Sprint 内の Story を `done` に確定する前に、以下 8 ガードを **全て** 通過する必要がある。
いずれか 1 つでも fail した場合、`status: needs_user_review` に留めるか、`partial` で Story を未完扱いとし、後続 Sprint または fix Sprint で対応する。

本ファイルが done 判定の**唯一の正典**。autopilot 側の `autopilot-done-judgment.md` はここへのポインタ (複製は 2026-07-16 に解消)。各ガードの由来・監査経緯は `done-judgment-rationale.md` — 実行時に読む必要はない。

**機械実行との分担**: Guards 2 / 3 / 6 / 7 (と設定済みの 5 / 8) の grep は `hooks/run-guards.py` が実行し `guards-run.json` に事実を記録する (`sprint verify` Phase 1 step 0)。モデルが行うのは各 hit への policy 適用 (処置判断) と、Guards 1 / 4 / 5 / 8 の適用可否判断のみ。grep をモデルが手で再実行するのは欠陥。

---

## Sprint 単位の事前条件 (rolling-wave): coarse Sprint は done 不可

per-Story ガード (Guard 1–8) を評価する **前** に、Sprint 単位の precondition を満たすこと:

- Sprint の `detail_level` が `"coarse"`、または `stories` が空 `{}` の場合、その Sprint は詳細化の地平より先の placeholder であり、**`done` にも `partial` にも遷移させてはならない**。
- coarse Sprint は story が 0 件なので per-Story ガードは 1 度も発火せず、放置すると「Story 0 件 → 全 Story done とみなす → Sprint 即 done」というサイレント偽完了が成立してしまう。これを塞ぐのが本 precondition。
- 対応: `sprint plan` §1.1 / `sprint auto` phase 1 の elaboration ゲートで、実行前に必ず Stories を詰めて `detail_level` を `"detailed"` に反転する。elaboration を経ていない coarse Sprint が done ゲートに到達した場合はバグ — done を拒否し、elaboration に差し戻す。
- 後方互換: `detail_level` フィールドが無い (legacy / pre-rolling-wave) Sprint は `"detailed"` とみなし、本 precondition は素通り。

---

## Guard 1: user_review_required の自動 done 禁止

Story の `user_review_required: true` フィールドが含まれる場合:

- `status: done` への自動遷移を **禁止**
- `status: needs_user_review` に固定し、autopilot は次の Sprint へ進めるが、ROADMAP 上はこの Story は未完扱い
- ユーザの明示承認 (sprint demo 後の手動 status 変更) でのみ `done` に遷移可能

実装: sprint auto / sprint done で Story を done に書き換える前に `user_review_required` フラグを読み、true なら `needs_user_review` を書く。

---

## Guard 2: nil-injection mock 検出

Story の主要実装ファイルに以下 anti-pattern が出現する場合、verify で警告:

```regex
if [a-zA-Z_]+\.[A-Z][a-zA-Z]* != nil \{
    [a-zA-Z_]+\.[A-Z][a-zA-Z]*\.[A-Z]
```

- 「Story が宣言する依存性 (例: Vault, DNS, Mon, Ansible)」が **複数同時に** この nil-guard パターンで囲まれている場合、構造的に「実機接続は省略可能」になっている疑い
- nil-guard 自体は不正ではないが、Story の AC に「実依存への呼出」が含まれる場合は、`tests/acceptance/devvm/` 配下のテストが **実依存ありで pass する** ことを別途確認しなければならない

実装: `run-guards.py` の `guard2_nil_injection` が Sprint diff の追加行を機械スキャンする。モデルは `guards-run.json` の hit を Story 単位に振り分け、同一 Story で 3 個以上なら警告を `verification-results.json` に記録し、ユーザ承認 (sprint demo) 必須とする。

---

## Guard 3: Mock モードでの実機検証扱い禁止

priority_rule 9 「dev VM 実機 deploy + smoke test」要件を満たすテストは、以下を含んではならない:

- `os.Setenv("MOCK", ...)` / `MOCK=true` env
- `--fake-*` / `-fake-*` CLI フラグ
- `DRY_RUN=1` 環境変数 (実機破壊回避以外の用途、例えば smoke で書込を伴わない場合に `DRY_RUN` を使うのは禁止)
- `proxy_fuse_fake_core: true` / その他 `*_fake_*: true` / `*_mock_*: true` 系の defaults
- in-process FakeCore / InMemoryStore の利用

これらを含むテストは priority_rule 9 を満たさず、別途「実本番モードでの smoke」が必要。

実装: `run-guards.py` の `guard3_mock_mode_smoke` (smoke dir とマーカーは `.claude/guards.json` の `smoke_dir` / `mock_markers`、既定は `tests/acceptance/devvm/` と上記リスト)。hit があればモデルが warn + 該当 Story の `priority_rule_9_satisfied: false` を記録。

---

## Guard 4: priority_rule 9 例外条項の厳格適用

Story の `review_reason` または `decisions.json` の rationale が priority_rule 9 例外条項を主張する場合、以下の **障害シナリオ識別子** を含むことを必須:

| 識別子 | 想定シナリオ |
|---|---|
| `kill-9` | プロセス強制終了 |
| `停電` / `power-loss` | VM/サーバ停電 |
| `ネットワーク遮断` / `network-partition` | NW セグメント分断 |
| `Shamir-unseal` | Vault 5-of-3 unseal 訓練 |
| `disk-full` | ディスクフル状態 |
| `OOM` | Out-Of-Memory kill |
| `プロセスクラッシュ` / `process-crash` | アプリ panic / segfault |

これら識別子のいずれも含まない `review_reason` は **例外条項の不正適用** と判定し、通常の実機 smoke 要件を課す。

実装: sprint verify で Story の `review_reason` 文字列を上記 keyword list と照合。マッチゼロなら `priority_rule_9_exception_invalid: true` を記録し、Guard 3 通過を要求。

---

## Guard 5: 呼出経路の存在検証

Story の AC または user_story が「複数サービス間の結合」を含む場合 (API + Workflow の両方を言及、backend への trigger を約束、等)、以下 grep を実行し全てヒット必須:

| 結合 | grep パターン |
|---|---|
| Storage Core → Temporal Workflow trigger | `ExecuteWorkflow\|SignalWorkflow` in `internal/server/` or `cmd/storage-core/` |
| Admin API → Vault | `Vault.*Issue\|vault.Client.*Write` |
| Workflow Worker → Storage Core (audit) | `storagecore.Client\|core.AppendAudit` |
| Proxy FUSE → Storage Core (real, not fake) | `corecli\.New\(.*\bhttp\b` in `cmd/proxy-fuse/` |
| Admin API → DNS / Prometheus / Ansible | 該当 Story の依存性で定義する具体 SDK 名 |

ヒットゼロは「呼出経路がコード上に存在しない」を意味し、Story done 不可。

実装: sprint verify で AC ごとに「結合キーワード」と「該当 grep」のマッピング表を定義し、unmatch を `unsatisfied_call_path: [...]` に記録。

---

## Guard 6: 先送りコメント残置検出

実装ファイル (Story が変更した `cmd/` `internal/` `ansible/`) に以下が残っている場合、Story done 不可:

```
// TODO.*Phase [0-9]
// Sprint [0-9].*で.*実装
// Sprint [0-9].*で.*追加
// 未実装.*Phase
// (Phase|Sprint).*で.*replace
# TODO.*Phase [0-9]
# Sprint [0-9].*で.*実装
```

ROADMAP の backlog に明示的に積まれていて、その backlog item に該当コメントの行番号が記載されているケースのみ、許容。

実装: `run-guards.py` の `guard6_deferred_comments` が diff 追加行を機械スキャンする (対象 path は `.claude/guards.json` の `deferred_comment_paths`、既定 `cmd/` `internal/` `ansible/`)。モデルは各 hit に対応する backlog entry (コメント行番号への参照付き) を照合し、無ければ Story done 不可。

---

## Guard 7: ADR conformance grep

Story が `internal/` または `cmd/` 配下のファイルを変更した場合、関連 Accepted ADR の **machine-checkable invariant** (禁止 grep / 必須 grep) を実行し、全件 pass を要求する。

### 7.1 Sprint 7.11.6 (S7ee8f4) で追加された invariant

| ADR | 種類 | 対象 | パターン | 期待 |
|---|---|---|---|---|
| **ADR-0014** §"物理キー" | forbidden_grep | `internal/server/`, `cmd/storage-core/`, `cmd/workflow-worker/`, `internal/workflow/` | `"tenants/" *\+\|fmt\.Sprintf\("tenants/[^"]*"` | ヒットゼロ (直接組立禁止, identity.NewPhysicalKey 経由のみ) |
| **ADR-0033** | required_grep | `internal/identity/` | `func NewPhysicalKey` | ヒット 1 以上 (typed constructor の存在を保証) |
| **ADR-0034** §category C | forbidden_grep | `internal/proxyfuse/`, `cmd/proxy-fuse/` | `corecli\.IsNotFound(\|corecli\.IsNeedRestore(\|corecli\.IsAlreadyExists(\|corecli\.IsNotEmpty(` | ヒットゼロ (bool helper 直接利用禁止、AsCoreError + Kind switch 経由のみ — Sprint 7.11.8 RC-3) |
| **ADR-0034** §category C | required_grep | `internal/proxyfuse/fs.go` | `corecli\.AsCoreError\|corecli\.IsKind` | ヒット 1 以上 (Kind switch エントリ点の存在保証) |

ヒットがある場合は `verification-results.json` の `guard7_adr_conformance` に該当箇所を記録し、対応 ADR id を併記する。Story が legitimate な exception (例: identity.go 自身の String() 実装) を含む場合は `decisions.json` の `guard7_exceptions` に明示する.

### 7.2 拡張ポリシー

Guard 7 は **ADR 文書から直接 pattern を読む** 形式 (`machine_check:` JSON ブロック) に統一していく。7.1 表は legacy — プロジェクトの `.claude/guards.json` `adr_checks` に転記して機械実行する。両方が pass しなければならない。(拡張の経緯は `done-judgment-rationale.md`)

実装: `run-guards.py` の `guard7_adr_machine_checks` — (a) `.claude/guards.json` `adr_checks` と (b) ADR 文書内の `machine_check:` JSON ブロックの両方を機械実行して `guards-run.json` に記録。hit は、`decisions.json` `guard7_exceptions` に記録された正当な例外を除き、Story done 不可。モデルは `touched_adrs` の各 ADR が (a)(b) のどちらかでカバーされていることを確認する。

---

## Guard 8: Destructive multi-version test 存在検証

Story が data path (`internal/server/`, `internal/proxyfuse/`, `cmd/storage-core/`, `cmd/proxy-fuse/`, `cmd/workflow-worker/`, `internal/workflow/`, `internal/identity/`) を touch した場合、以下のいずれかの destructive scenario test が **存在し、かつ最新 verification-results.json で pass している** ことを要求する:

| シナリオ | grep target | 期待 |
|---|---|---|
| **write x2 で v1/v2 独立** | `tests/acceptance/devvm/multi_version_destructive_test.go` に `version_no\s*=\s*1` と `version_no\s*=\s*2` の両方が含まれる |最低 1 ファイルでヒット (data path に物理キーが触れる Sprint では必須) |
| **Demote → Recall byte verify** | `tests/acceptance/devvm/multi_version_destructive_test.go` または同 dir 配下に `Demote.*Recall\|Recall.*Demote` + `bytes\.Equal\|sha256\.Sum256` のペア | ヒット 1 以上 |
| **Restart 整合** | `tests/acceptance/devvm/` 配下に proxy-fuse / storage-core プロセスの再起動 → state 一致を verify する test (`restart\|kill -9\|systemctl restart`) | ヒット 1 以上 (priority_rule 9 例外条項 trigger 可) |

実装: `run-guards.py` の `guard8_destructive_tests` (`.claude/guards.json` の `data_paths` / `destructive_test_dir` / `destructive_patterns` で宣言)。data path に diff が触れていて destructive test が欠如していれば hit — Story done 不可 (test-discipline.md Rule 8 と整合)。存在に加えて、そのテストが最新の machine verdict (`verify-run.json`) で pass していることはモデルが確認する。(由来: `done-judgment-rationale.md`)

例外: Story の `user_story` が「Sprint プロセス強化」「ドキュメント retrofit」のような meta な性質を持ち、production code path を一切実装しない場合は n/a 扱い (decisions.json の guard8_rationale に明示)。

---

## ガード結果の記録形式

各 Story のガード評価結果は `verification-results.json` の `done_judgment` フィールドに格納する:

```json
{
  "story_id": "S5225ae-5",
  "done_judgment": {
    "guard1_user_review_required_not_done": "pass | fail",
    "guard2_nil_injection_mock": "pass | fail | warn",
    "guard3_mock_mode_not_real_smoke": "pass | fail",
    "guard4_priority_rule_9_exception_valid": "pass | fail | n/a",
    "guard5_call_path_grep": "pass | fail",
    "guard6_deferred_comment_clean": "pass | fail",
    "guard7_adr_conformance": "pass | fail | warn",
    "guard8_destructive_multi_version_test": "pass | fail | n/a",
    "overall": "ok | needs_user_review"
  }
}
```

`overall: needs_user_review` の Story は sprint done で done 不可。
