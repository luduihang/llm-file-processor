# Progress

> Rolling session summaries, newest first.

<!-- session-in-progress:start=2026-10-07T08:49:55.390Z -->
## 2026-10-07 17:27 — 2 failures — cause is clear: CLI tests use `retries=1`, so a failing file consum... _(in progress)_
2 failures — cause is clear: CLI tests use `retries=1`, so a failing file consumes 2 provider calls (initial + 1 retry), and the finite outcomes list runs out. The retry logic is already tested in T-005; the CLI tests should use `retries=0` to decouple:
<!-- end-session-in-progress -->
