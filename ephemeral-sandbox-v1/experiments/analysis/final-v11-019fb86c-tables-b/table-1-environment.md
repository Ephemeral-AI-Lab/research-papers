# EXP1 environment and workload

> **FROZEN FINAL CANDIDATE.** Values are archive-derived and may be used only after the remaining paper evidence/build gates pass.

| Field | Archived value | Evidence source |
| --- | --- | --- |
| Host OS | Microsoft Windows 11 ??? build 26200 | environment-preflight.txt#{"pointer":"/recorded_run_environment/host"} |
| Container engine OS | linux | environment-preflight.txt#{"pointer":"/docker/os_type"} |
| Architecture | x64 | environment-preflight.txt#{"pointer":"/recorded_run_environment/host/architecture"} |
| CPU | AMD Ryzen Threadripper 7960X 24-Cores / 48 logical processors | environment-preflight.txt#{"pointer":"/recorded_run_environment/host"} |
| Memory | 137,438,953,472 bytes | environment-preflight.txt#{"pointer":"/recorded_run_environment/host/total_memory_bytes"} |
| Storage | NTFS | environment-preflight.txt#{"pointer":"/recorded_run_environment/host"} |
| Docker Engine | 29.0.1 | environment-preflight.txt#{"pointer":"/docker/server_version"} |
| Cgroup | 2 | environment-preflight.txt#{"pointer":"/docker/cgroup_version"} |
| Product commit/tag | 5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8; annotated tag paper-v1.1-freeze | campaign-manifest.json#{"pointer":"/product"} |
| Benchmark commit | 1680b599129532f72e706b6acb12ef62c63759e2 | campaign-manifest.json#{"pointer":"/paper_git/commit"} |
| Sandbox image | ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf | campaign-manifest.json#{"pointer":"/image/requested"} |
| Sandbox limits | 1 vCPU / 512 MiB / 256 PIDs | environment-preflight.txt#{"pointer":"/sandbox_limits"} |
| Workspace | 100 MiB / 4000 files / depth 100 | fixture-manifest.json#{"pointer":"/identity/fixture"} |
| Client | product_cli | campaign-manifest.json#{"pointer":"/plan/client_cohort"} |
| Gateway transport | windows_named_pipe; local_only; per_execution_block | run-manifest.json#{"pointer":"/data/environment/gateway_transport","protocol_version":"v1.1"} |
| Seed | 20260712 | fixture-manifest.json#{"pointer":"/identity/seed"} |
| Trials | 2 warm-up + 100 measured | expanded-plan.json#{"pointer":"/data/cells/*/protocol"} |
