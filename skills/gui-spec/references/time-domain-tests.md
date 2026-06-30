# Time-domain AC Tests

Some acceptance criteria are about WHAT happens DURING an action, not just the final state — animation, smooth scroll, transition, debounce/throttle, lazy render, fade, slide, progression, or async layout coordination (Shiki / mermaid / image loading). For these, a final-state-only assertion is insufficient: a mid-flight regression (animation stops short, transition stutters, debounced action fires twice) can pass a final-state check if some later mechanism (instant pin, retry, fallback) ends up at the right state anyway. The user sees the broken motion; the test doesn't.

This document is referenced by `gui-spec` Phase 4, `sprint-verify` Phase 1, and `sprint-fix` (formerly `sprint-hotfix`).

## When to mark an AC as time-domain

Trigger words in the AC: animation, smooth scroll, transition, debounce, throttle, lazy render, fade, slide, progression. If the AC is about a static result (button click → modal appears, form submit → URL changes), it is NOT time-domain — final-state testing is fine.

## AC schema for time-domain

Tag the AC `description` field with `[time-domain]` and break the requirement into three parts:

- **trigger**: the user action under test (click, scroll, focus, ...)
- **progression**: the time series the assertion is *about* (sampled state at fixed ms offsets, monotonic constraints, threshold by t=N ms, etc.)
- **final**: the steady-state condition

Example:

> `AC-Sb1e4d8-1-3 [time-domain]`: **trigger**: 500-turn conversation, click ↓ button (smooth scroll). **progression**: `scrollTop` sampled every 100ms must be monotonically non-decreasing during 0–1500ms; at t=500ms `scrollTop` must exceed 50% of final `scrollTop` (proves animation actually progresses, not stuck). **final**: at t=2500ms, `scrollHeight − scrollTop − clientHeight < 4`.

## Playwright test shape

Time-domain tests include a progression sampler in addition to the final assertion. The sampler runs INSIDE `page.evaluate` (in the browser, not from Node) so the loop does not pay Playwright IPC latency between samples — otherwise a 100ms cadence drifts to 200–300ms and the time domain shifts under you.

For a working example, see `test-examples.md` "Time-domain Test Example".

## Forbidden pattern

A time-domain AC must NOT be tested only as:

```typescript
await page.getByTestId('scroll-to-bottom').click();
await page.waitForTimeout(5000);  // generous final wait
const gap = await page.evaluate(() => {
  const el = document.querySelector('[data-testid="scroll-container"]')!;
  return el.scrollHeight - el.scrollTop - el.clientHeight;
});
expect(gap).toBeLessThan(4);
```

This passes even when the smooth animation stalls mid-way and a later fallback (interval pin, instant snap, retry) ends up at the right state. The user-visible motion remains broken. `sprint verify` rejects this pattern.

## Fix workflow for time-domain bugs

If the bug involves animation, smooth scroll, transition, debounce/throttle, or async-render coordination, the regular `sprint fix` flow is insufficient — final-state-only tests routinely pass while the user-visible motion is broken.

1. **Mark or add the AC as `[time-domain]`** using the schema above. If the AC doesn't exist yet, write it first; if it exists without the tag, add the tag and break it into the three parts.
2. **Write the progression-sampling Playwright test BEFORE touching the implementation.** The test must assert both intermediate progression and final convergence. See `test-examples.md` "Time-domain Test Example" for the template.
3. **Verify the new test FAILS against the broken implementation.** If it passes against the broken state, the test is wrong (likely a final-state-only assertion that lets the bug slip through). Iterate on the test until it reproduces the user-visible regression.
4. **Implement the fix.** Iterate until the test passes.
5. Continue with the regular `sprint fix` flow (commit, optional ROADMAP log).

This workflow exists because UI time-domain regressions (animation stops short, scroll lands in the wrong place, transition stutters) routinely pass final-state-only tests — past incidents needed 10+ iterations to root-cause when the test gap was filled only at the end. A 100ms-cadence sampler reveals stuck states at first sight.
