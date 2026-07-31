# EXP1 public CLI operations

> **FROZEN FINAL CANDIDATE.** Values are archive-derived and may be used only after the remaining paper evidence/build gates pass.

| Operation | Case | Payload/file size | Concurrency | Samples | p50 (ms) | p95 (ms) | p99 (ms) | Throughput (ops/s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `exec_command` | no-op | -- | 1 | 100 | 26.719 | 28.291 | 28.996 | 37.28 |
| `exec_command` | no-op | -- | 5 | 100 | 45.998 | 53.282 | 60.092 | 107.61 |
| `exec_command` | fixture read | 4 KiB | 1 | 100 | 27.235 | 28.938 | 32.666 | 36.44 |
| `exec_command` | fixture read | 4 KiB | 5 | 100 | 45.441 | 50.973 | 56.303 | 108.88 |
| Read | snapshot | 4 KiB | 1 | 100 | 11.425 | 15.773 | 19.964 | 85 |
| Read | snapshot | 4 KiB | 5 | 100 | 26.575 | 30.592 | 39.738 | 185.3 |
| Read | snapshot | 256 KiB | 1 | 100 | 20.781 | 24.367 | 25.484 | 47.68 |
| Read | snapshot | 256 KiB | 5 | 100 | 37.788 | 57.794 | 60.156 | 125.54 |
| Write | session-local | 4 KiB | 1 | 100 | 38.813 | 41.384 | 51.562 | 25.55 |
| Write | session-local | 4 KiB | 5 | 100 | 108.756 | 111.98 | 116.067 | 46 |
| Write | session-local | 256 KiB | 1 | 100 | 45.066 | 49.947 | 53.544 | 22.03 |
| Write | session-local | 256 KiB | 5 | 100 | 125.969 | 137.255 | 147.374 | 39.35 |
| Edit | one replacement | 4 KiB | 1 | 100 | 38.647 | 42.615 | 46.878 | 25.61 |
| Edit | one replacement | 4 KiB | 5 | 100 | 134.61 | 141.758 | 146.725 | 37.22 |
| Edit | one replacement | 256 KiB | 1 | 100 | 48.935 | 53.329 | 63.097 | 20.17 |
| Edit | one replacement | 256 KiB | 5 | 100 | 187.357 | 208.008 | 294.392 | 26.36 |
