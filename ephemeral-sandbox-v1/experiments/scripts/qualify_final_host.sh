#!/usr/bin/env bash
set -euo pipefail

script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
paper_root="$(cd -- "${script_directory}/../.." && pwd -P)"
product_root="/srv/eos-benchmark/product"
product_bin_dir="${product_root}/target/release"
image_reference="ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf"
qualification_id="qualification-$(date -u +%Y%m%dT%H%M%SZ)"
qualification_directory="${paper_root}/experiments/runs/${qualification_id}"
preflight_log="${qualification_directory}/environment-preflight.txt"
smoke_stdout="${qualification_directory}/cli-env-smoke-driver.stdout"
smoke_stderr="${qualification_directory}/cli-env-smoke-driver.stderr"
smoke_summary="${qualification_directory}/cli-env-smoke-summary.json"
smoke_elapsed="${qualification_directory}/cli-env-smoke-elapsed-seconds.txt"

fail() {
    printf 'FAIL\t%s\n' "$1" >&2
    exit 1
}

snapshot_owned_state() {
    local output="$1"
    {
        find "${paper_root}/.benchmark-state/runtime" -mindepth 1 -maxdepth 1 -printf 'runtime\t%f\n' 2>/dev/null || true
        find "${paper_root}/.benchmark-state/runs" -mindepth 1 -maxdepth 1 -printf 'run\t%f\n' 2>/dev/null || true
        docker ps -aq --filter label=eos.gateway_instance_id 2>/dev/null |
            sed 's/^/container\t/'
        docker volume ls -q --filter label=eos.gateway_instance_id 2>/dev/null |
            sed 's/^/volume\t/'
        ps -eo pid=,args= |
            awk -v binary="${product_bin_dir}/sandbox-gateway" \
                'index($0, binary) && index($0, " serve ") {print "process\t" $0}'
    } | sort >"$output"
}

[[ "$paper_root" == "/srv/eos-benchmark/paper" ]] ||
    fail "qualification must run from /srv/eos-benchmark/paper"
mkdir -p -- "$qualification_directory"
before_state="$(mktemp)"
after_state="$(mktemp)"
evidence_finalized=0

finalize_on_exit() {
    local status="$?"
    trap - EXIT
    set +e
    if [[ "$evidence_finalized" -eq 0 && -f "$before_state" ]]; then
        snapshot_owned_state "$after_state"
        diff -u -- "$before_state" "$after_state" \
            >"${qualification_directory}/leak-diff.txt"
    fi
    rm -f -- "$before_state" "$after_state"
    exit "$status"
}

trap finalize_on_exit EXIT
snapshot_owned_state "$before_state"
if [[ -s "$before_state" ]]; then
    cp -- "$before_state" "${qualification_directory}/preexisting-owned-state.txt"
    fail "pre-existing benchmark-owned process, runtime, container, or volume state is not allowed"
fi

export PRODUCT_ROOT="$product_root"
export PRODUCT_BIN_DIR="$product_bin_dir"
export IMAGE_REFERENCE="$image_reference"
export PAPER_ROOT="$paper_root"
export PYTHON_BIN="${paper_root}/.venv/bin/python"

bash "${script_directory}/verify_environment.sh" 2>&1 | tee "$preflight_log"

smoke_started="$(date +%s)"
if ! bash "${script_directory}/cli_environment_smoke.sh" \
    "$qualification_directory" >"$smoke_stdout" 2>"$smoke_stderr"; then
    fail "CLI-only environment smoke failed; inspect archived stdout and stderr"
fi
smoke_seconds="$(( $(date +%s) - smoke_started ))"
printf '%s\n' "$smoke_seconds" >"$smoke_elapsed"
[[ "$smoke_seconds" -le 180 ]] ||
    fail "CLI-only environment smoke exceeded the 180-second acceptance budget"
[[ ! -s "$smoke_stderr" ]] ||
    fail "CLI-only environment smoke emitted stderr output"

sandbox_ids="$(
    "${paper_root}/.venv/bin/python" - "$smoke_summary" <<'PY'
import json
import os
import sys

value = json.loads(open(sys.argv[1], encoding="utf-8").read())
assert value["client_cohort"] == "product_cli"
assert value["state"] == "completed"
assert value["correctness"] == "pass"
assert value["completed_batches"] == 2
assert value["total_batches"] == 2
assert value["operation_count"] == 20
assert value["warning_count"] == 0
assert value["failure_count"] == 0
assert value["cleanup"] == "pass"
assert value["elapsed_seconds"] <= 180
assert value["image_reference"] == os.environ["IMAGE_REFERENCE"]
assert value["gateway_instance_id"].startswith("cli-env-smoke-")
operation_sequence = [
    "list_docker_images",
    "create_sandbox",
    "exec_command",
    "file_write",
    "file_read",
    "file_edit",
    "file_read",
    "snapshot",
    "destroy_sandbox",
    "list_sandboxes",
]
assert value["operation_sequence"] == operation_sequence
assert len(value["batches"]) == 2
assert len(value["sandbox_ids"]) == 2
assert len(set(value["sandbox_ids"])) == 2
for index, batch in enumerate(value["batches"], start=1):
    assert batch["batch_index"] == index
    assert batch["sandbox_id"] == value["sandbox_ids"][index - 1]
    assert batch["state"] == "completed"
    assert batch["correctness"] == "pass"
    assert batch["operation_count"] == len(operation_sequence)
    assert batch["cleanup"] == "pass"
print(",".join(value["sandbox_ids"]))
PY
)" || fail "CLI-only environment smoke summary failed strict acceptance"

snapshot_owned_state "$after_state"
if ! diff -u -- "$before_state" "$after_state" >"${qualification_directory}/leak-diff.txt"; then
    fail "benchmark-owned process, runtime, container, or volume baseline changed"
fi
[[ ! -s "$after_state" ]] ||
    fail "CLI-only environment smoke left benchmark-owned state behind"
evidence_finalized=1

printf 'PASS\tfinal-host qualification completed\n'
printf 'INFO\tqualification_id=%s\n' "$qualification_id"
printf 'INFO\tclient_cohort=product_cli\n'
printf 'INFO\tsandbox_ids=%s\n' "$sandbox_ids"
printf 'INFO\tsmoke_elapsed_seconds=%s\n' "$smoke_seconds"
printf 'INFO\tartifact_directory=%s\n' "$qualification_directory"
