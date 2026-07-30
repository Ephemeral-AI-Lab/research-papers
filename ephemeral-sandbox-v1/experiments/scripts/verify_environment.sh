#!/usr/bin/env bash
set -euo pipefail

started_seconds="$(date +%s)"
script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
paper_root="$(cd -- "${script_directory}/../.." && pwd -P)"

: "${PRODUCT_ROOT:?Set PRODUCT_ROOT to the absolute ephemeral-sandbox checkout}"
: "${PRODUCT_BIN_DIR:?Set PRODUCT_BIN_DIR to its prebuilt executable directory}"

image_reference="${IMAGE_REFERENCE:-ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf}"
preset="${BENCHMARK_PRESET:-paper-env-smoke}"
maximum_seconds="${MAX_PREFLIGHT_SECONDS:-60}"
minimum_memory_bytes=$((15 * 1024 * 1024 * 1024))

pass() {
    printf 'PASS\t%s\n' "$1"
}

fail() {
    printf 'FAIL\t%s\n' "$1" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "missing command: $1"
}

require_regular_file() {
    local path="$1"
    [[ -f "$path" && ! -L "$path" && -s "$path" ]] ||
        fail "missing, empty, or unsafe regular file: $path"
}

require_executable() {
    local path="$1"
    require_regular_file "$path"
    [[ -x "$path" ]] || fail "file is not executable: $path"
}

for command_name in awk date docker findmnt git head mktemp nproc od sha256sum tr uname; do
    require_command "$command_name"
done

[[ "$(uname -s)" == "Linux" ]] || fail "host is not Linux"
pass "host operating system is Linux"

[[ "$(uname -m)" == "x86_64" ]] || fail "host architecture is not x86_64"
pass "host architecture is x86_64"

[[ -r /etc/os-release ]] || fail "/etc/os-release is unavailable"
# shellcheck disable=SC1091
. /etc/os-release
[[ "${ID:-}" == "ubuntu" && "${VERSION_ID:-}" == "24.04" ]] ||
    fail "host is not Ubuntu 24.04"
pass "host distribution is Ubuntu 24.04"

cpu_count="$(nproc)"
[[ "$cpu_count" -ge 8 ]] || fail "host exposes fewer than 8 logical CPUs"
pass "logical CPU count is ${cpu_count}"

memory_bytes="$(awk '/^MemTotal:/ {print $2 * 1024}' /proc/meminfo | awk '{printf "%.0f", $1}')"
[[ "$memory_bytes" -ge "$minimum_memory_bytes" ]] ||
    fail "host exposes less than 15 GiB usable memory"
pass "usable memory bytes are ${memory_bytes}"

paper_filesystem="$(findmnt -n -o FSTYPE --target "$paper_root")"
product_filesystem="$(findmnt -n -o FSTYPE --target "$PRODUCT_ROOT")"
[[ "$paper_filesystem" == "ext4" ]] || fail "paper root is not on ext4"
[[ "$product_filesystem" == "ext4" ]] || fail "product root is not on ext4"
pass "paper and product roots are on ext4"

[[ -r /sys/fs/cgroup/cgroup.controllers ]] || fail "cgroup v2 controllers are unavailable"
pass "cgroup v2 is available"

docker_version="$(docker version --format '{{.Server.Version}}' 2>/dev/null)" ||
    fail "Docker server is unreachable"
[[ -n "$docker_version" ]] || fail "Docker server version is empty"
pass "Docker server version is ${docker_version}"

[[ "$image_reference" =~ @sha256:[0-9a-f]{64}$ ]] ||
    fail "IMAGE_REFERENCE is not pinned by a full sha256 digest"

image_platform="$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$image_reference" 2>/dev/null)" ||
    fail "pinned image is not present locally; stage it before measurement"
[[ "$image_platform" == "linux/amd64" ]] ||
    fail "pinned image platform is not linux/amd64"
image_id="$(docker image inspect --format '{{.Id}}' "$image_reference")"
pass "pinned image is present as ${image_id}"

[[ -d "$PRODUCT_ROOT/.git" ]] || fail "PRODUCT_ROOT is not a Git checkout"
product_branch="$(git -C "$PRODUCT_ROOT" branch --show-current)"
[[ "$product_branch" == "main" ]] || fail "product checkout is not on main"
product_status="$(git -C "$PRODUCT_ROOT" status --porcelain=v1)"
[[ -z "$product_status" ]] || fail "product checkout is dirty"
product_commit="$(git -C "$PRODUCT_ROOT" rev-parse HEAD)"
pass "product checkout is clean main at ${product_commit}"

catalog_binary="${PRODUCT_BIN_DIR}/sandbox-catalog-export"
gateway_binary="${PRODUCT_BIN_DIR}/sandbox-gateway"
daemon_binary="${PRODUCT_ROOT}/dist/sandbox-daemon-linux-amd64"
git_amd64="${PRODUCT_ROOT}/dist/git/linux-amd64.tar"
git_arm64="${PRODUCT_ROOT}/dist/git/linux-arm64.tar"

require_executable "$catalog_binary"
require_executable "$gateway_binary"
require_executable "$daemon_binary"
require_regular_file "$git_amd64"
require_regular_file "$git_arm64"

daemon_magic="$(head -c 4 "$daemon_binary" | od -An -t x1 | tr -d ' \n')"
[[ "$daemon_magic" == "7f454c46" ]] || fail "Linux daemon is not an ELF executable"
pass "all prebuilt product artifacts are present and safe"

benchmark_python="${paper_root}/.venv/bin/python"
benchmark_cli="${paper_root}/.venv/bin/sandbox-benchmark"
require_executable "$benchmark_python"
require_executable "$benchmark_cli"
python_version="$("$benchmark_python" --version 2>&1)"
case "$python_version" in
    "Python 3.13."*)
        ;;
    *)
        fail "paper virtual environment is not CPython 3.13"
        ;;
esac
pass "benchmark virtual environment uses ${python_version}"

profile_record="$(
    PAPER_ROOT="$paper_root" "$benchmark_python" - <<'PY'
import os
from pathlib import Path

from benchmark_lab.fixtures import (
    _MAXIMUM_DEPTH,
    _relative_path,
    _validated_fixture_dimensions,
    workspace_fixture_identity,
)
from benchmark_lab.planning import load_workspace_profiles

root = Path(os.environ["PAPER_ROOT"])
profile = load_workspace_profiles(
    root / "benchmark" / "defaults" / "workspace-profiles"
)["paper-100m"]
fixture = profile["fixture"]
assert _MAXIMUM_DEPTH == 499
assert _validated_fixture_dimensions(fixture) == (4000, 104857600, 100)
assert len(_relative_path(99, 100).parent.parts) == 100
_, digest = workspace_fixture_identity(profile, 20260712)
print(digest)
PY
)"
pass "paper workspace profile is valid as ${profile_record}"

plan_json="$(mktemp)"
trap 'rm -f -- "$plan_json"' EXIT

"$benchmark_cli" validate \
    --test-repository-root "$paper_root" \
    --product-root "$PRODUCT_ROOT" \
    --product-bin-dir "$PRODUCT_BIN_DIR" \
    --plan "$preset" >"$plan_json"

plan_record="$(
    "$benchmark_python" - "$plan_json" <<'PY'
import json
import sys

value = json.loads(open(sys.argv[1], encoding="utf-8").read())
assert value["runnable"] is True
print(
    f'plan_hash={value["plan_hash"]} '
    f'cells={value["estimates"]["cell_count"]} '
    f'trials={value["estimates"]["trial_batch_count"]}'
)
PY
)"
pass "benchmark preset validates: ${plan_record}"

printf 'INFO\tkernel=%s\n' "$(uname -r)"
printf 'INFO\tproduct_commit=%s\n' "$product_commit"
printf 'INFO\timage_reference=%s\n' "$image_reference"
printf 'INFO\timage_id=%s\n' "$image_id"
printf 'INFO\tcatalog_sha256=%s\n' "$(sha256sum "$catalog_binary" | awk '{print $1}')"
printf 'INFO\tgateway_sha256=%s\n' "$(sha256sum "$gateway_binary" | awk '{print $1}')"
printf 'INFO\tdaemon_sha256=%s\n' "$(sha256sum "$daemon_binary" | awk '{print $1}')"
printf 'INFO\tworkspace_fixture_hash=%s\n' "$profile_record"

elapsed_seconds="$(( $(date +%s) - started_seconds ))"
[[ "$elapsed_seconds" -le "$maximum_seconds" ]] ||
    fail "preflight took ${elapsed_seconds}s, above the ${maximum_seconds}s budget"
pass "network-free preflight completed in ${elapsed_seconds}s"
