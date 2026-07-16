# Done 判定ガード — 由来と監査経緯 (rationale)

`sprint-done-judgment.md` の**実行時には読まない**ファイル。ガードがなぜ存在するかの出自を保存する。読むのは self-audit (`docs/skills-self-audit.md`) やガード自体を改訂する時だけ — 通常の verify / done でこのファイルを読み込むのは token の無駄。

## 全体の由来

- 8 ガードは 2026-05-17 の Hydra Phase 1 監査 (`docs/audit/2026-05-17-phase1-readiness.md`) で発見された 6 つの「偽 done」パターン (user_review_required bypass / nil-injection mock / mock-mode smoke / priority_rule 9 例外の不正適用 / 呼出経路欠落 / 先送りコメント残置) に対する執行レイヤとして導入された。
- Guard 7 (ADR conformance) は Sprint 7.11.6 (S7ee8f4) で audit 2026-05-23 RC-5 への一次対応として追加。
- Guard 8 (destructive multi-version test) は Sprint 7.11.10 (S38c457) で audit 2026-05-23 RC-5 への完全対応として追加。

## Guard 7 の拡張経緯

Sprint 7.11.10 (S38c457) で 6 件の Accepted ADR (ADR-0004 / 0014 / 0015 / 0016 / 0027 / 0032) に `machine_check:` セクションを retrofit 済。方針: Guard 7 は **ADR 文書から直接 pattern を読む** 形式に統一していく。7.1 の legacy 表は既存 audit との連続性のため残置され、`.claude/guards.json` の `adr_checks` に転記して機械実行する。

## Guard 8 の由来

audit 2026-05-23 RC-5 で「ADR-0014 違反 (write x2 → 同一物理キー上書き) が Sprint 2 から約 7 sprint silent 残置」が摘発された。原因は write x2 → v1/v2 独立性を verify する自動テストの欠如。Guard 8 はこの欠如を Sprint 完了ゲートで検知する (test-discipline.md Rule 8 と連動)。

## 二重リファレンスの解消 (2026-07-16)

かつて `autopilot/references/autopilot-done-judgment.md` に同内容の複製を「skill 間の独立性のため」維持していたが、autopilot は既に `../sprint/references/` を多数直接参照しており独立性の前提は成立していなかった。複製は同期コストと token を二重に払うだけなので、`sprint-done-judgment.md` を唯一の正典とし、autopilot 側はポインタに置き換えた。

## 機械化 (2026-07-16)

Guards 2 / 3 / 6 / 7 と forbidden-degradation スキャン (test-discipline Rule 6) の grep 実行は `hooks/run-guards.py` に移管された (`guards-run.json` に機械記録)。動機は run-verify.py と同じ: モデルが grep を「実行し忘れる / 読み違える」余地を消しつつ、実装セッション・verifier・done ゲートの 3 箇所で同じ grep をモデル価格で再実行していた token 消費を 1 回の機械実行に畳む。モデルに残るのは各 hit の処置判断 (policy) のみ。
