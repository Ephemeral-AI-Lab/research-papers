# EXP1 resource observations

> **FROZEN FINAL CANDIDATE.** Values are archive-derived and may be used only after the remaining paper evidence/build gates pass.

| Operation/case | Concurrency | Peak daemon RSS (MiB) | Peak sandbox memory (MiB) | Sandbox CPU (ms/trial) | Block read (MiB/trial) | Block write (MiB/trial) | Workspace allocated delta (MiB) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Workspace create, 100 MiB/depth 100 | 1 | 25.5 | 28.172 | 30.471 | 0 | 0.011 | 0.004 |
| Workspace create, 100 MiB/depth 100 | 5 | 34.125 | 43.527 | 79.502 | 0 | 0.027 | 0.02 |
| `exec_command`, no-op | 1 | 13.875 | 20.031 | 35.003 | 0 | 0.001 | 0 |
| `exec_command`, no-op | 5 | 13.125 | 21.555 | 63.077 | 0 | 0.003 | 0 |
| Read, 256 KiB | 5 | 14.473 | 14.977 | 38.431 | 0 | 0 | 0 |
| Write, 256 KiB | 5 | 51.043 | 54.27 | 95.115 | 0 | 1.251 | 1.258 |
| Edit, 256 KiB | 5 | 62.602 | 66.715 | 148.732 | 0 | 1.251 | 1.258 |
