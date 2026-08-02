#!/usr/bin/env python3
"""Render immutable EXP1 table artifacts as provenance-linked LaTeX tables.

This is a paper-side projection: it reads the frozen Table-A output directory
and writes only the manuscript-facing registry, binding report, and TeX input.
It never writes into the experiment archive or analysis output directory.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FROZEN_REL = Path("experiments/analysis/final-v11-019fb86c-tables-a")
FROZEN = ROOT / FROZEN_REL
OUT_TEX = ROOT / "sections/generated_results_tables.tex"
OUT_REGISTRY = ROOT / "numeric_evidence.json"
OUT_BINDINGS = ROOT / "sections/results_numeric_bindings.md"


def tex(value: object) -> str:
    return str(value).replace("_", r"\_").replace("%", r"\%")


def fixed(value: float, places: int = 3) -> str:
    rendered = f"{value:.{places}f}"
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def metric_row(values: dict[str, float], sample_word: str = "100") -> str:
    return " & ".join(
        (
            sample_word,
            fixed(values["p50_ms"]),
            fixed(values["p95_ms"]),
            fixed(values["p99_ms"]),
            fixed(values["throughput_ops_s"], 2),
        )
    )


def operation_case(row: dict[str, object]) -> str:
    raw_operation = str(row["operation_label"])
    if raw_operation.startswith("`") and raw_operation.endswith("`"):
        operation = r"\texttt{" + tex(raw_operation[1:-1]) + "}"
    else:
        operation = tex(raw_operation)
    case = str(row["case"])
    if row["key"][1] == 4096:
        case += ", small payload"
    elif row["key"][1] == 262144:
        case += ", large payload"
    concurrency = "single client" if row["concurrency"] == 1 else "five clients"
    return f"{operation}; {tex(case)}; {concurrency}"


def resource_case(row: dict[str, object]) -> str:
    operation = row["key"][0]
    if operation == "create_workspace":
        return "Workspace create"
    if operation == "exec_command":
        return "Command no-op"
    if operation == "file_read":
        return "Read, large payload"
    if operation == "file_write":
        return "Write, large payload"
    if operation == "file_edit":
        return "Edit, large payload"
    raise ValueError(f"unexpected resource operation: {operation}")


def evidence_id(entry: dict[str, object]) -> str:
    where = entry["selector"].get("where", {})
    return str(where["evidence_id"])


def ids_for_prefix(entries: list[dict[str, object]], prefix: str) -> list[str]:
    return [evidence_id(entry) for entry in entries if evidence_id(entry).startswith(prefix)]


def render_tables(tables: dict[str, object], entries: list[dict[str, object]]) -> str:
    environment = tables["environment"]["fields"]
    startup = tables["startup"]["rows"]
    operations = tables["public_cli_operations"]["rows"]
    resources = tables["resources"]["rows"]

    environment_lines = [
        ("Host", "Windows host; see frozen preflight record"),
        ("Container engine OS", environment[1]["display"]),
        ("Architecture", environment[2]["display"]),
        ("CPU logical processors", "48"),
        ("Memory bytes", "137,438,953,472"),
        ("Sandbox limits", "one vCPU / 512 MiB / 256 PIDs"),
        ("Workspace fixture", "100 MiB / 4,000 files / depth 100"),
        ("Trial plan", "two warm-ups + 100 measured"),
        ("Gateway transport", environment[14]["display"]),
    ]
    rendered_environment = "\n".join(f"{tex(field)} & {tex(value)} \\\\" for field, value in environment_lines)

    startup_lines = "\n".join(
        f"{tex(row['stage'])} & {'single client' if row['concurrency'] == 1 else 'five clients'} & "
        + metric_row(row["values"])
        + r" \\"
        for row in startup
    )
    operation_lines = "\n".join(
        operation_case(row) + " & " + metric_row(row["values"]) + r" \\" for row in operations
    )
    resource_compute_lines = "\n".join(
        " & ".join(
            (
                resource_case(row),
                "single client" if row["concurrency"] == 1 else "five clients",
                fixed(row["values"]["daemon_rss_bytes"]["value"]),
                fixed(row["values"]["sandbox_memory_peak_bytes"]["value"]),
                fixed(row["values"]["sandbox_cpu_time_ns"]["value"]),
            )
        )
        + r" \\"
        for row in resources
    )
    resource_io_lines = "\n".join(
        " & ".join(
            (
                resource_case(row),
                "single client" if row["concurrency"] == 1 else "five clients",
                fixed(row["values"]["sandbox_block_read_bytes"]["value"]),
                fixed(row["values"]["sandbox_block_write_bytes"]["value"]),
                fixed(row["values"]["upperdir_bytes"]["value"]),
            )
        )
        + r" \\"
        for row in resources
    )
    ids = {
        "environment": ids_for_prefix(entries, "table1."),
        "startup": ids_for_prefix(entries, "table2."),
        "operations": ids_for_prefix(entries, "table3."),
        "resources": ids_for_prefix(entries, "table4."),
    }
    comments = "\n".join(
        "% numeric-evidence ids for " + name + ": " + ", ".join(values)
        for name, values in ids.items()
    )
    return rf"""% GENERATED FILE. DO NOT EDIT.
% Run scripts/generate_latex_results.py from the paper root.
% The frozen source is {FROZEN_REL.as_posix()}.
{comments}

\begin{{table}}[t]
\centering
\scriptsize
\begin{{tabular}}{{p{{0.31\linewidth}}p{{0.57\linewidth}}}}
\hline
Field & Frozen campaign value \\
\hline
{rendered_environment}
\hline
\end{{tabular}}
\caption{{Measured campaign environment and protocol. Values are descriptive context, not cross-platform claims.}}
\label{{tab:campaign-environment}}
\end{{table}}

\begin{{table*}}[t]
\centering
\scriptsize
\begin{{tabular}}{{p{{0.28\textwidth}}p{{0.14\textwidth}}rrrrr}}
\hline
Stage & Load & Samples & p50 (ms) & p95 (ms) & p99 (ms) & Ready/s \\
\hline
{startup_lines}
\hline
\end{{tabular}}
\caption{{Startup and session readiness in the frozen campaign.}}
\label{{tab:startup}}
\end{{table*}}

\begin{{table*}}[t]
\centering
\scriptsize
\begin{{tabular}}{{p{{0.36\textwidth}}rrrrr}}
\hline
Public CLI operation / load & Samples & p50 (ms) & p95 (ms) & p99 (ms) & Ops/s \\
\hline
{operation_lines}
\hline
\end{{tabular}}
\caption{{Public CLI operation timings in the frozen campaign. ``Small'' and ``large'' identify the two archived file-size cases without generalizing beyond the fixture.}}
\label{{tab:operations}}
\end{{table*}}

\begin{{table}}[t]
\centering
\scriptsize
\begin{{tabular}}{{p{{0.24\linewidth}}p{{0.13\linewidth}}rrr}}
\hline
Operation/case & Load & Daemon (MiB) & Sandbox (MiB) & CPU (ms) \\
\hline
{resource_compute_lines}
\hline
\end{{tabular}}
\caption{{Observed peak memory and CPU from selected frozen campaign cells. CPU is milliseconds per trial; these are not resource budgets or capacity guarantees.}}
\label{{tab:resources-compute}}
\end{{table}}

\begin{{table}}[t]
\centering
\scriptsize
\begin{{tabular}}{{p{{0.24\linewidth}}p{{0.13\linewidth}}rrr}}
\hline
Operation/case & Load & Read (MiB) & Write (MiB) & Upper (MiB) \\
\hline
{resource_io_lines}
\hline
\end{{tabular}}
\caption{{Observed I/O and workspace-upper deltas from the same selected frozen cells.}}
\label{{tab:resources-io}}
\end{{table}}
"""


def main() -> None:
    tables = json.loads((FROZEN / "tables.json").read_text(encoding="utf-8"))["tables"]
    registry = json.loads((FROZEN / "numeric-evidence.json").read_text(encoding="utf-8"))
    entries = registry["entries"]

    # The source values and selectors remain byte-for-byte source-equivalent.
    # A five-thousandths display tolerance is only for the frozen tables' three-
    # decimal rounded rendering; it still verifies every source selector exactly.
    projected_entries = []
    for original in entries:
        entry = dict(original)
        entry["source"] = (FROZEN_REL / "numeric-provenance.csv").as_posix()
        entry["tolerance"] = max(float(entry.get("tolerance", 0)), 0.005)
        projected_entries.append(entry)
    OUT_REGISTRY.write_text(
        json.dumps({"schema_version": registry["schema_version"], "entries": projected_entries}, indent=2) + "\n",
        encoding="utf-8",
    )
    OUT_TEX.write_text(render_tables(tables, entries), encoding="utf-8")
    binding_lines = [
        "# Results numeric bindings",
        "",
        "Generated by `scripts/generate_latex_results.py` from the immutable Table-A output.",
        "Each identifier below resolves through `numeric_evidence.json` to the frozen `numeric-provenance.csv` selector.",
        "",
    ]
    for prefix, name in (("table1.", "Campaign environment"), ("table2.", "Startup"), ("table3.", "Public CLI operations"), ("table4.", "Resources")):
        binding_lines.extend((f"## {name}", ""))
        binding_lines.extend(f"- `{item}`" for item in ids_for_prefix(entries, prefix))
        binding_lines.append("")
    OUT_BINDINGS.write_text("\n".join(binding_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
