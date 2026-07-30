#!/usr/bin/env bash
set -euo pipefail

started_seconds="$(date +%s)"
artifact_directory="${1:?usage: cli_environment_smoke.sh ARTIFACT_DIRECTORY}"
paper_root="${PAPER_ROOT:-/srv/eos-benchmark/paper}"
product_root="${PRODUCT_ROOT:-/srv/eos-benchmark/product}"
product_bin_dir="${PRODUCT_BIN_DIR:-${product_root}/target/release}"
python_bin="${PYTHON_BIN:-${paper_root}/.venv/bin/python}"
image_reference="${IMAGE_REFERENCE:-ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf}"
maximum_seconds="${MAX_CLI_SMOKE_SECONDS:-180}"

gateway_binary="${product_bin_dir}/sandbox-gateway"
manager_cli="${product_bin_dir}/sandbox-manager-cli"
runtime_cli="${product_bin_dir}/sandbox-runtime-cli"
observability_cli="${product_bin_dir}/sandbox-observability-cli"
daemon_binary="${product_root}/dist/sandbox-daemon-linux-amd64"
gateway_template="${paper_root}/benchmark/defaults/gateway.yml"

runtime_directory="${artifact_directory}/cli-runtime"
gateway_config="${runtime_directory}/effective-config.yml"
gateway_log="${artifact_directory}/gateway.log"
gateway_pid_file="${runtime_directory}/gateway.pid"
gateway_registry="${runtime_directory}/registry.json"
summary_file="${artifact_directory}/cli-env-smoke-summary.json"
gateway_instance_id="cli-env-smoke-$(date -u +%Y%m%dT%H%M%SZ)-$$"

gateway_pid=""
sandbox_id=""
gateway_token=""
batch_sandbox_ids=()

fail() {
    printf 'FAIL\t%s\n' "$1" >&2
    exit 1
}

require_executable() {
    [[ -f "$1" && ! -L "$1" && -x "$1" ]] ||
        fail "missing or unsafe executable: $1"
}

stop_gateway() {
    [[ -n "$gateway_pid" ]] || return 0
    if kill -0 "$gateway_pid" 2>/dev/null; then
        kill -TERM -- "-${gateway_pid}" 2>/dev/null ||
            kill -TERM "$gateway_pid" 2>/dev/null ||
            true
        for _ in $(seq 1 50); do
            kill -0 "$gateway_pid" 2>/dev/null || break
            sleep 0.1
        done
        if kill -0 "$gateway_pid" 2>/dev/null; then
            kill -KILL -- "-${gateway_pid}" 2>/dev/null ||
                kill -KILL "$gateway_pid" 2>/dev/null ||
                true
        fi
        wait "$gateway_pid" 2>/dev/null || true
    fi
    gateway_pid=""
}

cleanup_gateway_volumes() {
    local volume_name
    local volume_gateway_id
    local cleanup_stdout="${artifact_directory}/owned-volume-cleanup.stdout"
    local cleanup_stderr="${artifact_directory}/owned-volume-cleanup.stderr"
    : >"$cleanup_stdout"
    : >"$cleanup_stderr"
    while IFS= read -r volume_name; do
        [[ -n "$volume_name" ]] || continue
        volume_gateway_id="$(
            docker volume inspect \
                --format '{{ index .Labels "eos.gateway_instance_id" }}' \
                "$volume_name" 2>>"$cleanup_stderr"
        )" || return 1
        [[ "$volume_gateway_id" == "$gateway_instance_id" ]] || return 1
        docker volume rm -- "$volume_name" \
            >>"$cleanup_stdout" 2>>"$cleanup_stderr" || return 1
    done < <(
        docker volume ls -q \
            --filter "label=eos.gateway_instance_id=${gateway_instance_id}"
    )
}

require_no_owned_docker_resources() {
    local owned_containers
    local owned_volumes
    owned_containers="$(
        docker ps -aq \
            --filter "label=eos.gateway_instance_id=${gateway_instance_id}"
    )"
    owned_volumes="$(
        docker volume ls -q \
            --filter "label=eos.gateway_instance_id=${gateway_instance_id}"
    )"
    [[ -z "$owned_containers" && -z "$owned_volumes" ]]
}

cleanup_on_exit() {
    local status="$?"
    trap - EXIT INT TERM
    set +e
    if [[ -n "$sandbox_id" ]]; then
        "$manager_cli" destroy_sandbox --sandbox-id "$sandbox_id" \
            >"${artifact_directory}/cleanup-destroy.json" \
            2>"${artifact_directory}/cleanup-destroy.stderr"
        if [[ "$?" -ne 0 ]]; then
            status=1
        fi
    fi
    stop_gateway
    if ! cleanup_gateway_volumes; then
        status=1
    fi
    if ! require_no_owned_docker_resources; then
        status=1
    fi
    unset SANDBOX_GATEWAY_AUTH_TOKEN gateway_token
    exit "$status"
}

for executable in \
    "$gateway_binary" \
    "$manager_cli" \
    "$runtime_cli" \
    "$observability_cli" \
    "$daemon_binary"
do
    require_executable "$executable"
done
[[ -x "$python_bin" ]] ||
    fail "Python interpreter is missing or not executable: $python_bin"
for command_name in date docker find grep kill sed seq setsid sleep; do
    command -v "$command_name" >/dev/null 2>&1 ||
        fail "missing command: $command_name"
done
[[ -f "$gateway_template" && ! -L "$gateway_template" ]] ||
    fail "gateway configuration template is missing or unsafe"
[[ "$image_reference" =~ @sha256:[0-9a-f]{64}$ ]] ||
    fail "sandbox image is not pinned by a full sha256 digest"

mkdir -p -- "$artifact_directory" "$runtime_directory"
trap cleanup_on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

gateway_socket="$(
    "$python_bin" - <<'PY'
import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 0))
    host, port = sock.getsockname()
print(f"{host}:{port}")
PY
)"
gateway_token="$(
    "$python_bin" - <<'PY'
import secrets

print(secrets.token_urlsafe(48))
PY
)"
export SANDBOX_GATEWAY_SOCKET="$gateway_socket"
export SANDBOX_GATEWAY_AUTH_TOKEN="$gateway_token"
export EOS_SHARED_BASE_CACHE="${runtime_directory}/shared-base-cache"

PAPER_ROOT="$paper_root" \
GATEWAY_CONFIG="$gateway_config" \
GATEWAY_INSTANCE_ID="$gateway_instance_id" \
GATEWAY_PID_FILE="$gateway_pid_file" \
GATEWAY_REGISTRY="$gateway_registry" \
GATEWAY_SOCKET="$gateway_socket" \
QUALIFICATION_ROOT="$artifact_directory" \
DAEMON_BINARY="$daemon_binary" \
"$python_bin" - <<'PY'
import os
from pathlib import Path

import yaml

paper_root = Path(os.environ["PAPER_ROOT"])
template = paper_root / "benchmark" / "defaults" / "gateway.yml"
config = yaml.safe_load(template.read_text(encoding="utf-8"))
config["gateway"].update(
    {
        "bind_addr": os.environ["GATEWAY_SOCKET"],
        "pid_path": os.environ["GATEWAY_PID_FILE"],
        "max_concurrent_connections": 64,
    }
)
config["manager"].update(
    {
        "registry_path": os.environ["GATEWAY_REGISTRY"],
        "workspace_roots": [os.environ["QUALIFICATION_ROOT"]],
    }
)
config["manager"]["docker"].update(
    {
        "daemon_binary_path": os.environ["DAEMON_BINARY"],
        "daemon_config_yaml_path": os.environ["GATEWAY_CONFIG"],
        "gateway_instance_id": os.environ["GATEWAY_INSTANCE_ID"],
    }
)
Path(os.environ["GATEWAY_CONFIG"]).write_text(
    yaml.safe_dump(config, sort_keys=True),
    encoding="utf-8",
)
PY

setsid "$gateway_binary" serve \
    --backend docker \
    --config-yaml "$gateway_config" >"$gateway_log" 2>&1 &
gateway_pid="$!"

readiness_stdout="${artifact_directory}/gateway-readiness.json"
readiness_stderr="${artifact_directory}/gateway-readiness.stderr"
gateway_ready=0
for _ in $(seq 1 120); do
    if ! kill -0 "$gateway_pid" 2>/dev/null; then
        fail "sandbox gateway exited during startup; inspect gateway.log"
    fi
    if "$manager_cli" list_docker_images \
        >"$readiness_stdout" 2>"$readiness_stderr"; then
        gateway_ready=1
        break
    fi
    sleep 0.25
done
[[ "$gateway_ready" -eq 1 ]] ||
    fail "sandbox gateway did not become CLI-ready within 30 seconds"
[[ ! -s "$readiness_stderr" ]] ||
    fail "list_docker_images emitted stderr"

run_batch() {
    local batch_index="$1"
    local batch_label
    local batch_prefix
    local workspace_directory
    local fixture_marker
    local list_images_stdout
    local list_images_stderr
    local create_stdout
    local create_stderr
    local exec_stdout
    local exec_stderr
    local write_stdout
    local write_stderr
    local read_alpha_stdout
    local read_alpha_stderr
    local edit_stdout
    local edit_stderr
    local read_omega_stdout
    local read_omega_stderr
    local snapshot_stdout
    local snapshot_stderr
    local destroy_stdout
    local destroy_stderr
    local list_after_stdout
    local list_after_stderr
    local destroyed_sandbox_id

    printf -v batch_label '%02d' "$batch_index"
    batch_prefix="${artifact_directory}/batch-${batch_label}"
    workspace_directory="${artifact_directory}/cli-workspace-batch-${batch_label}"
    fixture_marker="CLI_ENV_BATCH_${batch_label}"
    mkdir -p -- "${workspace_directory}/src"
    printf '%s fixture\n' "$fixture_marker" >"${workspace_directory}/README.txt"
    printf 'initial fixture\n' >"${workspace_directory}/src/main.txt"

    list_images_stdout="${batch_prefix}-00-list-images.json"
    list_images_stderr="${batch_prefix}-00-list-images.stderr"
    "$manager_cli" list_docker_images \
        >"$list_images_stdout" 2>"$list_images_stderr"
    [[ ! -s "$list_images_stderr" ]] ||
        fail "batch ${batch_label} list_docker_images emitted stderr"

    create_stdout="${batch_prefix}-01-create-sandbox.json"
    create_stderr="${batch_prefix}-01-create-sandbox.stderr"
    "$manager_cli" create_sandbox \
        --image "$image_reference" \
        --workspace-bind-root "$workspace_directory" \
        >"$create_stdout" 2>"$create_stderr"
    [[ ! -s "$create_stderr" ]] ||
        fail "batch ${batch_label} create_sandbox emitted stderr"

    sandbox_id="$(
        EXPECTED_WORKSPACE="$workspace_directory" \
        "$python_bin" - "$create_stdout" <<'PY'
import json
import os
import sys

value = json.loads(open(sys.argv[1], encoding="utf-8").read())
assert isinstance(value, dict)
assert isinstance(value.get("id"), str) and value["id"]
assert value.get("state") == "ready"
assert value.get("workspace_root") == os.environ["EXPECTED_WORKSPACE"]
print(value["id"])
PY
    )" || fail "batch ${batch_label} create_sandbox response failed strict validation"

    exec_stdout="${batch_prefix}-02-exec-command.json"
    exec_stderr="${batch_prefix}-02-exec-command.stderr"
    "$runtime_cli" \
        --sandbox-id "$sandbox_id" \
        --request-id "cli-env-smoke-${batch_label}-exec" \
        exec_command \
        --timeout-ms 30000 \
        'printf "CLI_ENV_EXEC_OK\n"; test -f README.txt; cat README.txt' \
        >"$exec_stdout" 2>"$exec_stderr"
    [[ ! -s "$exec_stderr" ]] ||
        fail "batch ${batch_label} exec_command emitted stderr"

    write_stdout="${batch_prefix}-03-file-write.json"
    write_stderr="${batch_prefix}-03-file-write.stderr"
    "$runtime_cli" \
        --sandbox-id "$sandbox_id" \
        --request-id "cli-env-smoke-${batch_label}-write" \
        file_write \
        --path cli-smoke.txt \
        --content 'CLI_ENV_FILE_ALPHA' \
        >"$write_stdout" 2>"$write_stderr"
    [[ ! -s "$write_stderr" ]] ||
        fail "batch ${batch_label} file_write emitted stderr"

    read_alpha_stdout="${batch_prefix}-04-file-read-alpha.json"
    read_alpha_stderr="${batch_prefix}-04-file-read-alpha.stderr"
    "$runtime_cli" \
        --sandbox-id "$sandbox_id" \
        --request-id "cli-env-smoke-${batch_label}-read-alpha" \
        file_read \
        --path cli-smoke.txt \
        --limit 10 \
        >"$read_alpha_stdout" 2>"$read_alpha_stderr"
    [[ ! -s "$read_alpha_stderr" ]] ||
        fail "batch ${batch_label} first file_read emitted stderr"

    edit_stdout="${batch_prefix}-05-file-edit.json"
    edit_stderr="${batch_prefix}-05-file-edit.stderr"
    "$runtime_cli" \
        --sandbox-id "$sandbox_id" \
        --request-id "cli-env-smoke-${batch_label}-edit" \
        file_edit \
        --path cli-smoke.txt \
        --edits '[{"old_string":"ALPHA","new_string":"OMEGA"}]' \
        >"$edit_stdout" 2>"$edit_stderr"
    [[ ! -s "$edit_stderr" ]] ||
        fail "batch ${batch_label} file_edit emitted stderr"

    read_omega_stdout="${batch_prefix}-06-file-read-omega.json"
    read_omega_stderr="${batch_prefix}-06-file-read-omega.stderr"
    "$runtime_cli" \
        --sandbox-id "$sandbox_id" \
        --request-id "cli-env-smoke-${batch_label}-read-omega" \
        file_read \
        --path cli-smoke.txt \
        --limit 10 \
        >"$read_omega_stdout" 2>"$read_omega_stderr"
    [[ ! -s "$read_omega_stderr" ]] ||
        fail "batch ${batch_label} second file_read emitted stderr"

    snapshot_stdout="${batch_prefix}-07-observability-snapshot.json"
    snapshot_stderr="${batch_prefix}-07-observability-snapshot.stderr"
    "$observability_cli" snapshot \
        --sandbox-id "$sandbox_id" \
        >"$snapshot_stdout" 2>"$snapshot_stderr"
    [[ ! -s "$snapshot_stderr" ]] ||
        fail "batch ${batch_label} observability snapshot emitted stderr"

    SANDBOX_ID="$sandbox_id" \
    FIXTURE_MARKER="$fixture_marker" \
    "$python_bin" - \
        "$exec_stdout" \
        "$read_alpha_stdout" \
        "$read_omega_stdout" \
        "$snapshot_stdout" <<'PY'
import json
import os
import sys


def load(path: str) -> object:
    return json.loads(open(path, encoding="utf-8").read())


def strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in strings(item)]
    return []


command, alpha, omega, snapshot = map(load, sys.argv[1:])
assert isinstance(command, dict)
assert command.get("status") == "ok"
assert command.get("exit_code") == 0
command_text = "\n".join(strings(command))
assert "CLI_ENV_EXEC_OK" in command_text
assert os.environ["FIXTURE_MARKER"] in command_text
assert "CLI_ENV_FILE_ALPHA" in "\n".join(strings(alpha))
omega_text = "\n".join(strings(omega))
assert "CLI_ENV_FILE_OMEGA" in omega_text
assert "CLI_ENV_FILE_ALPHA" not in omega_text
assert os.environ["SANDBOX_ID"] in "\n".join(strings(snapshot))
PY

    destroy_stdout="${batch_prefix}-08-destroy-sandbox.json"
    destroy_stderr="${batch_prefix}-08-destroy-sandbox.stderr"
    "$manager_cli" destroy_sandbox \
        --sandbox-id "$sandbox_id" \
        >"$destroy_stdout" 2>"$destroy_stderr"
    [[ ! -s "$destroy_stderr" ]] ||
        fail "batch ${batch_label} destroy_sandbox emitted stderr"

    destroyed_sandbox_id="$sandbox_id"
    sandbox_id=""

    list_after_stdout="${batch_prefix}-09-list-sandboxes-after.json"
    list_after_stderr="${batch_prefix}-09-list-sandboxes-after.stderr"
    "$manager_cli" list_sandboxes \
        >"$list_after_stdout" 2>"$list_after_stderr"
    [[ ! -s "$list_after_stderr" ]] ||
        fail "batch ${batch_label} post-cleanup list_sandboxes emitted stderr"

    SANDBOX_ID="$destroyed_sandbox_id" \
    "$python_bin" - "$destroy_stdout" "$list_after_stdout" <<'PY'
import json
import os
import sys

destroyed = json.loads(open(sys.argv[1], encoding="utf-8").read())
listed = json.loads(open(sys.argv[2], encoding="utf-8").read())
assert destroyed.get("id") == os.environ["SANDBOX_ID"]
assert os.environ["SANDBOX_ID"] not in json.dumps(listed, sort_keys=True)
PY
    batch_sandbox_ids+=("$destroyed_sandbox_id")
}

run_batch 1
run_batch 2

stop_gateway
cleanup_gateway_volumes ||
    fail "failed to remove a Docker volume owned by the qualification gateway"
require_no_owned_docker_resources ||
    fail "the qualification gateway left a container or volume behind"

nonempty_stderr="$(
    find "$artifact_directory" -maxdepth 1 -type f -name '*.stderr' -size +0 -print
)"
[[ -z "$nonempty_stderr" ]] ||
    fail "one or more product CLI commands emitted stderr"
if grep -Eiq \
    '"level"[[:space:]]*:[[:space:]]*"(warn|error)"|(^|[^[:alpha:]])(WARN|ERROR|PANIC)([^[:alpha:]]|$)' \
    "$gateway_log"; then
    fail "gateway log contains a warning, error, or panic"
fi
token_leak_files="$(grep -rlF -- "$gateway_token" "$artifact_directory" || true)"
if [[ -n "$token_leak_files" ]]; then
    while IFS= read -r leaked_file; do
        sed -i "s/${gateway_token}/[REDACTED]/g" "$leaked_file"
    done <<<"$token_leak_files"
    fail "gateway authentication token appeared in archived output and was redacted"
fi

elapsed_seconds="$(( $(date +%s) - started_seconds ))"
[[ "$elapsed_seconds" -le "$maximum_seconds" ]] ||
    fail "CLI environment smoke took ${elapsed_seconds}s, above the ${maximum_seconds}s budget"

BATCH_1_ID="${batch_sandbox_ids[0]}" \
BATCH_2_ID="${batch_sandbox_ids[1]}" \
GATEWAY_INSTANCE_ID="$gateway_instance_id" \
IMAGE_REFERENCE="$image_reference" \
ELAPSED_SECONDS="$elapsed_seconds" \
"$python_bin" - "$summary_file" <<'PY'
import json
import os
import sys

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
batch_ids = [os.environ["BATCH_1_ID"], os.environ["BATCH_2_ID"]]
summary = {
    "schema_version": 1,
    "client_cohort": "product_cli",
    "state": "completed",
    "correctness": "pass",
    "completed_batches": 2,
    "total_batches": 2,
    "operation_count": 20,
    "warning_count": 0,
    "failure_count": 0,
    "cleanup": "pass",
    "elapsed_seconds": int(os.environ["ELAPSED_SECONDS"]),
    "gateway_instance_id": os.environ["GATEWAY_INSTANCE_ID"],
    "image_reference": os.environ["IMAGE_REFERENCE"],
    "operation_sequence": operation_sequence,
    "sandbox_ids": batch_ids,
    "batches": [
        {
            "batch_index": index,
            "sandbox_id": sandbox_id,
            "state": "completed",
            "correctness": "pass",
            "operation_count": len(operation_sequence),
            "cleanup": "pass",
        }
        for index, sandbox_id in enumerate(batch_ids, start=1)
    ],
}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(summary, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY

unset SANDBOX_GATEWAY_AUTH_TOKEN gateway_token
trap - EXIT INT TERM
printf 'PASS\tCLI-only environment smoke completed\n'
printf 'INFO\tsummary=%s\n' "$summary_file"
printf 'INFO\telapsed_seconds=%s\n' "$elapsed_seconds"
