# Experiments

This directory is the provenance root for paper measurements.

- [`../experiment_inventory.md`](../experiment_inventory.md) — focused
  practical-performance protocol, phase gates, and acceptance tracker.
- [`environment_setup.md`](environment_setup.md) — one-time staging, fast
  first-step verification, smoke, and good-pass commands.
- [`scripts/verify_environment.sh`](scripts/verify_environment.sh) —
  network-free preflight; it never builds, installs, or pulls.
- [`expected_tables.md`](expected_tables.md) — four final table schemas plus
  clearly labeled simulated previews.
- [`experiment_log.md`](experiment_log.md) — append-only attempts, failures,
  amendments, and run dispositions.
- `protocols/` — preregistered RQ1–RQ5 protocols, workloads, baselines, metrics, seeds/repeats, stopping rules, and acceptance policy.
- `runs/` — immutable run manifests, raw logs/events/samples, exact commands, environment records, binary/image digests, and failures.
- `analysis/` — deterministic aggregation, uncertainty, tables, and plot generation.

Pilot runs must be labeled `exploratory` and kept separate from final runs. Final runs must name the annotated `paper-v1-freeze` source tag, frozen benchmark commit, hardware, OS/kernel/filesystem, runtime configuration, model/tool versions, seeds, and analysis commit.
