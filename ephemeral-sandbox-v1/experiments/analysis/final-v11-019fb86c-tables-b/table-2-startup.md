# EXP1 startup and workspace creation

> **FROZEN FINAL CANDIDATE.** Values are archive-derived and may be used only after the remaining paper evidence/build gates pass.

| Stage | Concurrent creates | Samples | p50 (ms) | p95 (ms) | p99 (ms) | Throughput (ready/s) |
| --- | --- | --- | --- | --- | --- | --- |
| Sandbox create + base mount | 1 | 100 | 1659.811 | 1749.739 | 1794.902 | 0.62 |
| Session create to ready | 1 | 100 | 32.897 | 35.685 | 36.096 | 30.36 |
| Session create to ready | 5 | 100 | 109.119 | 120.107 | 131.588 | 45.32 |
| First no-op command | 1 | 100 | 26.719 | 28.291 | 28.996 | 37.28 |
