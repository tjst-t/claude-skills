# design-flow

The three-phase dialogue for `design start`. The point of writing this down is that Claude must NOT collapse Phase 1 into "ask the VISION template questions." Doing so defeats the purpose of this skill.

---

## Phase 1 — 発散 (Divergence)

**Goal**: Build a picture of what the user is trying to create. Output of this phase is *Claude's internal understanding*, not files.

**Do NOT** ask:
- "What is your tech stack?" (premature)
- "Who are the target users?" (too structured, the user may not know yet)
- "What's out of scope?" (cannot answer before the in-scope is clear)

**Do** ask, in flowing conversation:

- 「どんなアプリ / システムを作りたいですか? ふわっとしたままで大丈夫です」
- 「それを作りたいと思った背景は何ですか?」
- 「今これを使う人は、何ができなくて困っていますか? (本人/他人/未来の自分)」
- 「もしできあがったら、どんな瞬間で『これ作って良かった』と思いますか?」
- 「複雑になりそうだなと感じている部分はありますか?」
- 「似たプロダクトはありますか? 何が違いますか?」

Listen for:
- **Verbs the user repeats** — those are the core actions of the system
- **Nouns the user uses casually** — those are candidate domain entities
- **Frustrations** — those are the problem statement
- **What the user assumes you'll just know** — those are the implicit constraints, surface them in Phase 2

**Phase 1 exit signal**: You can write a 2-3 sentence description of the system that names the actors, the main verb, and the value. If you can't, keep asking.

---

## Phase 2 — 収束 (Convergence)

**Goal**: Confirm your understanding, then probe the gaps that block design.

### Step 2.1 — Reflect back

```
「整理するとこういうことかなと思っています:

  {1-2 paragraph summary in the user's own vocabulary}

合っていますか? 違っていれば修正してください。」
```

Iterate until the user confirms. If the user keeps adding new dimensions, you may need to drop back to Phase 1 — that's fine.

### Step 2.2 — Surface the gaps

Once the summary is confirmed, ask only the questions whose answers you cannot infer. Batch them. Examples:

**Scope boundaries** (almost always needed):
- 「今回作るのは {X, Y, Z} の範囲、という理解で合っていますか?」
- 「逆に、絶対に今回はやらない、と決めておきたいことはありますか?」

**Reference products** (high leverage — improves later UI/UX autonomy a lot):
- 「『〜みたいな感じ』というのがあれば教えてください。UIでも操作感でも。」

**Hard constraints** (only if applicable):
- 「既存のシステムやデータと統合する必要がありますか?」
- 「使いたい / 使わなければならない技術はありますか?」
- 「デプロイ先や運用環境に制約はありますか?」

**Non-functional targets** (only if the system has them — not every project does):
- 「同時に何人くらい使う想定ですか?」
- 「データを失うことがどれくらい致命的ですか? (バックアップ / 整合性の強さ)」
- 「応答速度に期待値はありますか?」
- 「セキュリティ要件はありますか? (個人情報 / 認証 / 監査)」

**Decision points the user has opinions on** (these become ADRs):
- 「すでに『これはこうしたい』と決めていることはありますか? なぜそう決めたかも教えてください。」

**Decision points the user is unsure about** (these are the most valuable ADRs):
- 「逆に、まだ迷っている / Claudeと相談しながら決めたい部分はありますか?」

### Step 2.3 — ADR exploration (for each unresolved load-bearing decision)

For each load-bearing decision the user is unsure about, walk through it together:

1. **Frame the forces**: 「この判断は {A, B} のトレードオフですね。」
2. **List the alternatives** (Claude proposes 2-3, the user can add more)
3. **Discuss consequences** of each — easier / harder, what locks in
4. **Estimate reversibility cost** — low (refactor a Sprint) / medium (multi-Sprint refactor) / high (significant migration) / one-way door (essentially permanent)
5. **Pick** — if there's a clear winner, recommend it and let the user confirm. If genuinely 50/50, mark the ADR `tentative: true` and surface it again at the next milestone.

This is the most important part of the skill — do not rush it.

**Phase 2 exit signal**: You have enough to draft VISION, DESIGN_PRINCIPLES, domain, system, non-functional, and the initial ADR set. If any of these would be mostly empty or guess-filled, go back and ask more.

---

## Phase 3 — 構造化 (Structuring)

**Goal**: Convert the conversation into structured artifacts. The user confirms each before writing.

### Order (matters because later ones reference earlier ones)

1. **VISION.json** — draft → confirm → write
2. **DESIGN_PRINCIPLES.json** — draft → confirm → write
3. **DESIGN/domain.json** — draft → confirm → write
4. **DESIGN/system.json** — draft → confirm → write (references domain entities)
5. **DESIGN/non-functional.json** — draft → confirm → write
6. **DESIGN/adr/ADR-NNNN-*.json** — one ADR at a time, in the order they were discussed
7. **DESIGN/data.json** — only if applicable (stateful, distributed, external protocols)

### Drafting style

- Use the user's own vocabulary, not generic terms
- Prefer concrete examples in `consequences` fields over abstract assertions
- For ADR `context`: 1-2 paragraphs of prose. For `alternatives`: a list of 2-4 named options with one-line trade-off each. For `decision`: a single sentence. For `consequences`: bullet list, both positive and negative.
- Keep each artifact lean. The reader of these files (often Claude itself in future sessions) is looking for orientation, not exhaustive specification.

### Confirmation pattern

For each artifact, present the draft inline (don't write the file yet):

```
「{artifact name} のドラフトです:

  {draft contents}

このまま書き出して良いですか? 修正があれば指摘してください。」
```

After confirmation, write the file. Then move to the next artifact.

### ADR numbering

For each ADR:

```bash
# Determine next number
next=$(ls docs/DESIGN/adr/ 2>/dev/null | grep -oE '^ADR-[0-9]+' | sort -V | tail -1 | sed 's/ADR-0*//' || echo 0)
next=$((${next:-0} + 1))
printf -v fname "ADR-%04d-%s.json" "$next" "$kebab_title"
```

Title is kebab-case, derived from the decision (e.g., `event-sourcing-for-orders`, `postgres-not-mongo`, `sync-write-async-read`).

### Final summary

After all files are written:

```
「DESIGN完了:

  - VISION / DESIGN_PRINCIPLES 作成
  - ドメインエンティティ: N個
  - システムコンポーネント: K個
  - ADR: M個 (うち {tentative} は未確定として残しています)
  - 非機能要件: {perf / availability / security} 定義済み

次のステップ:
  - `autopilot setup` で残りのセットアップ (CLAUDE.md, ARCHITECTURE.md, ROADMAP.json)
  - もしくは `project-init` → `sprint roadmap` で手動セットアップ」
```

---

## Backfill mode

When DESIGN/ exists but VISION.json and/or DESIGN_PRINCIPLES.json are missing, do NOT run Phase 1. The user has already done the discovery work — it's encoded in DESIGN/. Your job is to reconstruct the missing top-level files from the existing artifacts and write only what's missing.

### Step B.1 — Read all of DESIGN/

```bash
# Read the structural files
jq '.' docs/DESIGN/domain.json
jq '.' docs/DESIGN/system.json
[ -f docs/DESIGN/non-functional.json ] && jq '.' docs/DESIGN/non-functional.json
[ -f docs/DESIGN/data.json ] && jq '.' docs/DESIGN/data.json

# Read all ADRs (these encode tradeoffs and principles)
for f in docs/DESIGN/adr/*.json; do jq '.' "$f"; done
```

### Step B.2 — Derive VISION.json (if missing)

Map fields to sources. Be honest: derive what is derivable, ask the user only for what is not.

| VISION field | Source in DESIGN/ | Fallback |
|---|---|---|
| `summary` | system.json overall purpose + domain.json's main entities — synthesize one sentence | Ask |
| `target_users` | Scan ADR `context` fields for "for {role}" or "user of type X". Look at domain.json entity definitions for actor-like entities. | Ask if no signal |
| `problem` | ADRs' `context` sections often state the problem | Ask if no signal |
| `success_criteria` | non-functional.json's measurable targets (perf, availability) + ADR consequences marked `+ ...` that name observable outcomes | Ask |
| `out_of_scope` | ADRs' `alternatives` where the rejected option was rejected because "X is not needed" / "out of scope" — these are explicit non-goals | Ask |
| `tech_constraints` | system.json `external_dependencies` (with `swappable: false`) + components' `language_or_stack` | — |
| `design_references` | Rarely present in DESIGN/ | Ask |

### Step B.3 — Derive DESIGN_PRINCIPLES.json (if missing)

The hardest field is `priority_rules`. These are inferred from the **pattern of choices across ADRs**, not from any single ADR.

Heuristic for `priority_rules`:

1. List each ADR's `decision` and `alternatives`. For each rejected alternative, ask: "what did this trade off?"
2. Group rejections by theme:
   - Rejected "more flexible/configurable" → priority leans `simplicity > flexibility`
   - Rejected "more performant/scalable" → priority leans `correctness > performance` or `current-fit > future-fit`
   - Rejected "more isolated/decoupled" → priority leans `cohesion > decoupling at current scale`
   - Rejected "more abstracted" → priority leans `concreteness > abstraction`
   - Rejected "existing library/service" in favor of custom → priority leans `control > convention`
   - Rejected "custom" in favor of existing → priority leans `convention > control`
3. Surface 3-5 themes that appear in 2+ ADRs. These become `priority_rules`.

Other fields:

| PRINCIPLES field | Source in DESIGN/ | Fallback |
|---|---|---|
| `priority_rules` | Pattern across ADRs (above) | Ask user to confirm/adjust the derived set |
| `coding_conventions` | Not in DESIGN/ | Ask, or leave empty (CLAUDE.md will own these later) |
| `ui_ux` | Not in DESIGN/ | Ask if there's a UI, else empty |
| `architecture` | system.json boundaries + ADR decisions about structural choices | — |
| `forbidden` | Scan ADRs for "must never X", "cannot Y", or non-functional security constraints stated absolutely | Ask if no signal |

### Step B.4 — Present drafts + ask only for gaps

Present the derived VISION and PRINCIPLES as drafts. Mark each field with its source:

```
VISION.json (draft, from DESIGN/):
  summary: "..."                              [derived from system.json]
  target_users: ["..."]                       [derived from ADR-0001 context]
  problem: "..."                              [derived from ADR-0001 context]
  success_criteria: ["..."]                   [derived from non-functional.json]
  out_of_scope: ["..."]                       [derived from ADR-0003 alternatives]
  tech_constraints: ["..."]                   [derived from system.json]
  design_references: []                       [NOT IN DESIGN/ — please provide]

DESIGN_PRINCIPLES.json (draft, from ADR patterns):
  priority_rules:
    1. simplicity > flexibility               [pattern in ADR-0002, ADR-0005]
    2. correctness > performance              [pattern in ADR-0003, ADR-0004]
    ...
  coding_conventions: []                      [NOT IN DESIGN/ — please provide or skip]
  ...
```

Then in one batch, ask the user:

1. To confirm or correct the derived values (especially the priority_rules, which are inference-based)
2. To fill in the gaps (design_references, coding_conventions, ui_ux)

### Step B.5 — Write only missing files

Do NOT touch DESIGN/ in backfill mode — it is the input, not the output. Write only `docs/VISION.json` and/or `docs/DESIGN_PRINCIPLES.json` (whichever is missing).

### Step B.6 — Summarize and return

```
「Backfill完了:

  - docs/VISION.json: 作成 (DESIGN/から{N}フィールド派生, {M}フィールドはユーザー入力)
  - docs/DESIGN_PRINCIPLES.json: 作成 (ADR{N}件からpriority_rules{M}件を抽出)

次のステップ: `autopilot setup` でCLAUDE.md/ARCHITECTURE.md/ROADMAP.jsonを生成」
```

### Why this is safer than "stop and ask user to fill manually"

- Discards no information already encoded in DESIGN/ — those artifacts represent real design work
- The user's review is on a concrete draft, not a blank form (much easier to react to)
- The `priority_rules` inferred from ADR patterns are often more accurate than what a user would write from scratch, because they reflect actual choices made, not aspirational rules

## Anti-patterns to avoid

- **Filling in fields when the user hasn't said anything**: If the user has no opinion on availability targets, write `not specified` and add a tentative ADR or leave the field omitted. Do not invent.
- **Asking 20 questions at once**: Batch related questions, but keep each batch focused (3-5 questions). The user gets lost otherwise.
- **Treating the templates as forms**: The templates are *output shapes*, not *input questionnaires*. Phase 1 conversation feeds the templates, not the other way around.
- **Skipping Phase 1**: If you go straight to "tell me your VISION", you've reimplemented `autopilot setup` Phase 1. The whole point of this skill is the dialogue before the structure.
- **Over-ADR'ing**: If you find yourself writing more than ~10 ADRs in the initial pass, you're capturing decisions that should live in `sprint plan`. Use the scope discriminator (in SKILL.md) ruthlessly.
