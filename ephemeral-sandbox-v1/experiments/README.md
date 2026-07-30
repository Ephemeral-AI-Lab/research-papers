# Experiments

This directory is the provenance root for paper measurements.

- `protocols/` — preregistered RQ1–RQ5 protocols, workloads, baselines, metrics, seeds/repeats, stopping rules, and acceptance policy.
- `runs/` — immutable run manifests, raw logs/events/samples, exact commands, environment records, binary/image digests, and failures.
- `analysis/` — deterministic aggregation, uncertainty, tables, and plot generation.

Pilot runs must be labeled `exploratory` and kept separate from final runs. Final runs must name the annotated `paper-v1-freeze` source tag, frozen benchmark commit, hardware, OS/kernel/filesystem, runtime configuration, model/tool versions, seeds, and analysis commit.
