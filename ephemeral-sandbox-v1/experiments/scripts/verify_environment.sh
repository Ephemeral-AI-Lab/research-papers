#!/usr/bin/env bash
set -euo pipefail

started_seconds="$(date +%s)"
script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
paper_root="$(cd -- "${script_directory}/../.." && pwd -P)"

: "${PRODUCT_ROOT:?Set PRODUCT_ROOT to the absolute ephemeral-sandbox checkout}"
: "${PRODUCT_BIN_DIR:?Set PRODUCT_BIN_DIR to its prebuilt executable directory}"

expected_hostname="eos-benchmark-ubuntu24"
expected_paper_root="/srv/eos-benchmark/paper"
expected_product_root="/srv/eos-benchmark/product"
expected_product_bin_dir="${expected_product_root}/target/release"
expected_product_commit="b22862550e0a7cb4fe61ce581831e9244cc492b5"
expected_docker_version="29.0.1"
expected_image_reference="ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf"
expected_catalog_sha256="c841597bab53612a2f424088264a0fce383b54ded480050d99fbed1c529ac8ba"
expected_gateway_sha256="f1f8420bfa6ea6370d90fbf8428c432fe6f1031b0cb7cc7d32ac543dc8be2faf"
expected_daemon_sha256="a55d4775b992c02d603ca294746fb314e99d59774732ab7b8e7bf24ef010fb22"
expected_manager_cli_sha256="0be4f0c26f8f50b76b175d04cfeec61529a605bcda9ffcd6782a09096ba2983f"
expected_runtime_cli_sha256="e9ac5f6c7a5f9c07a3de166b320e7d6065fa9480a7f18d6d59114337d15e28e7"
expected_observability_cli_sha256="6b2dae2369344cbb3960a76f6ccdfa869a7aa9b7a7a255f8a634f4a52d5cfdb5"
image_reference="${IMAGE_REFERENCE:-$expected_image_reference}"
maximum_seconds="${MAX_PREFLIGHT_SECONDS:-60}"
minimum_memory_bytes=$((15 * 1024 * 1024 * 1024))
minimum_storage_bytes=$((100 * 1024 * 1024 * 1024))
minimum_available_storage_bytes=$((20 * 1024 * 1024 * 1024))

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

for command_name in awk date df docker file findmnt git grep head hostname lsblk mktemp nproc od realpath sed sha256sum systemd-detect-virt tr uname; do
    require_command "$command_name"
done

[[ "$(uname -s)" == "Linux" ]] || fail "host is not Linux"
pass "host operating system is Linux"

[[ "$(uname -m)" == "x86_64" ]] || fail "host architecture is not x86_64"
pass "host architecture is x86_64"

[[ "$(hostname -s)" == "$expected_hostname" ]] ||
    fail "logical hostname is not ${expected_hostname}"
pass "logical hostname is ${expected_hostname}"

if grep -Eiq '(microsoft|wsl)' /proc/sys/kernel/osrelease /proc/version; then
    fail "WSL is not an eligible final host"
fi
if systemd-detect-virt --container >/dev/null 2>&1; then
    fail "a container is not an eligible final host"
fi
virtualization="$(systemd-detect-virt 2>/dev/null || true)"
pass "host is neither WSL nor a container; virtualization=${virtualization:-none}"

[[ -r /etc/os-release ]] || fail "/etc/os-release is unavailable"
# shellcheck disable=SC1091
. /etc/os-release
[[ "${ID:-}" == "ubuntu" && "${VERSION_ID:-}" == "24.04" ]] ||
    fail "host is not Ubuntu 24.04"
pass "host distribution is Ubuntu 24.04"

resolved_product_root="$(realpath -e -- "$PRODUCT_ROOT")"
resolved_product_bin_dir="$(realpath -e -- "$PRODUCT_BIN_DIR")"
[[ "$paper_root" == "$expected_paper_root" ]] ||
    fail "paper root is not ${expected_paper_root}"
[[ "$resolved_product_root" == "$expected_product_root" ]] ||
    fail "product root is not ${expected_product_root}"
[[ "$resolved_product_bin_dir" == "$expected_product_bin_dir" ]] ||
    fail "product binary directory is not ${expected_product_bin_dir}"
pass "paper, product, and binary paths match the selected environment"

cpu_count="$(nproc)"
[[ "$cpu_count" -ge 8 ]] || fail "host exposes fewer than 8 logical CPUs"
pass "logical CPU count is ${cpu_count}"

memory_bytes="$(awk '/^MemTotal:/ {print $2 * 1024}' /proc/meminfo | awk '{printf "%.0f", $1}')"
[[ "$memory_bytes" -ge "$minimum_memory_bytes" ]] ||
    fail "host exposes less than 15 GiB usable memory"
pass "usable memory bytes are ${memory_bytes}"

paper_filesystem="$(findmnt -n -o FSTYPE --target "$paper_root")"
product_filesystem="$(findmnt -n -o FSTYPE --target "$resolved_product_root")"
[[ "$paper_filesystem" == "ext4" ]] || fail "paper root is not on ext4"
[[ "$product_filesystem" == "ext4" ]] || fail "product root is not on ext4"
pass "paper and product roots are on ext4"

for storage_path in "$paper_root" "$resolved_product_root"; do
    storage_size="$(
        df -B1 --output=size -- "$storage_path" |
            awk 'NR == 2 {gsub(/[[:space:]]/, "", $1); print $1}'
    )"
    [[ "$storage_size" =~ ^[0-9]+$ && "$storage_size" -ge "$minimum_storage_bytes" ]] ||
        fail "filesystem containing ${storage_path} is smaller than 100 GiB"
    storage_source="$(findmnt -n -o SOURCE --target "$storage_path")"
    backing_record="$(lsblk -s -n -o NAME,TYPE,ROTA,TRAN -- "$storage_source" 2>/dev/null)" ||
        fail "cannot inspect storage backing for ${storage_path}"
    if ! awk '
        $2 == "disk" && $3 == "0" && ($4 == "nvme" || $1 ~ /^nvme/) { found = 1 }
        END { exit found ? 0 : 1 }
    ' <<<"$backing_record"; then
        fail "storage containing ${storage_path} is not provably NVMe-backed"
    fi
    backing_evidence="$(
        awk '
            BEGIN { separator = "" }
            {
                printf "%s%s:%s:rota=%s:transport=%s",
                    separator, $1, $2, $3, ($4 == "" ? "unknown" : $4)
                separator = ","
            }
        ' <<<"$backing_record"
    )"
    pass "storage path=${storage_path} size_bytes=${storage_size} source=${storage_source} backing=${backing_evidence}"
done
pass "paper and product filesystems are at least 100 GiB and NVMe-backed"

[[ -r /sys/fs/cgroup/cgroup.controllers ]] ||
    fail "cgroup v2 controllers are unavailable"
cgroup_controllers="$(< /sys/fs/cgroup/cgroup.controllers)"
for controller in cpu memory pids; do
    grep -qw "$controller" <<<"$cgroup_controllers" ||
        fail "cgroup v2 ${controller} controller is unavailable"
done
pass "cgroup v2 cpu, memory, and pids controllers are available"

docker_record="$(
    docker info --format \
        '{{.ServerVersion}}|{{.OSType}}|{{.Architecture}}|{{.Driver}}|{{.CgroupVersion}}' \
        2>/dev/null
)" ||
    fail "Docker server is unreachable"
IFS='|' read -r docker_version docker_os docker_architecture docker_driver docker_cgroup_version \
    <<<"$docker_record"
[[ "$docker_version" == "$expected_docker_version" ]] ||
    fail "Docker server version is not ${expected_docker_version}"
[[ "$docker_os" == "linux" ]] || fail "Docker server operating system is not Linux"
[[ "$docker_architecture" == "x86_64" || "$docker_architecture" == "amd64" ]] ||
    fail "Docker server architecture is not AMD64"
[[ "$docker_driver" == "overlayfs" ]] || fail "Docker storage driver is not overlayfs"
[[ "$docker_cgroup_version" == "2" ]] || fail "Docker does not use cgroup v2"
pass "Docker ${docker_version} is Linux AMD64 with overlayfs and cgroup v2"

[[ "$image_reference" =~ @sha256:[0-9a-f]{64}$ ]] ||
    fail "IMAGE_REFERENCE is not pinned by a full sha256 digest"
[[ "$image_reference" == "$expected_image_reference" ]] ||
    fail "IMAGE_REFERENCE differs from the protocol-pinned image"

image_platform="$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$image_reference" 2>/dev/null)" ||
    fail "pinned image is not present locally; stage it before measurement"
[[ "$image_platform" == "linux/amd64" ]] ||
    fail "pinned image platform is not linux/amd64"
image_id="$(docker image inspect --format '{{.Id}}' "$image_reference")"
image_digest="${image_reference##*@}"
image_repo_digests="$(docker image inspect --format '{{join .RepoDigests "\n"}}' "$image_reference")"
grep -Eq "(^|/)ubuntu@${image_digest}$" <<<"$image_repo_digests" ||
    fail "local image RepoDigests do not contain the protocol-pinned manifest"
pass "pinned image is present as ${image_id} with manifest ${image_digest}"

[[ -d "$resolved_product_root/.git" ]] || fail "PRODUCT_ROOT is not a Git checkout"
product_branch="$(git -C "$resolved_product_root" branch --show-current)"
[[ "$product_branch" == "main" ]] || fail "product checkout is not on main"
product_status="$(git -C "$resolved_product_root" status --porcelain=v1)"
[[ -z "$product_status" ]] || fail "product checkout is dirty"
product_commit="$(git -C "$resolved_product_root" rev-parse HEAD)"
[[ "$product_commit" == "$expected_product_commit" ]] ||
    fail "product commit is not ${expected_product_commit}"
pass "product checkout is clean main at the selected commit ${product_commit}"

catalog_binary="${resolved_product_bin_dir}/sandbox-catalog-export"
gateway_binary="${resolved_product_bin_dir}/sandbox-gateway"
manager_cli_binary="${resolved_product_bin_dir}/sandbox-manager-cli"
runtime_cli_binary="${resolved_product_bin_dir}/sandbox-runtime-cli"
observability_cli_binary="${resolved_product_bin_dir}/sandbox-observability-cli"
daemon_binary="${resolved_product_root}/dist/sandbox-daemon-linux-amd64"

require_executable "$catalog_binary"
require_executable "$gateway_binary"
require_executable "$manager_cli_binary"
require_executable "$runtime_cli_binary"
require_executable "$observability_cli_binary"
require_executable "$daemon_binary"

for binary_path in \
    "$catalog_binary" \
    "$gateway_binary" \
    "$manager_cli_binary" \
    "$runtime_cli_binary" \
    "$observability_cli_binary" \
    "$daemon_binary"
do
    binary_record="$(file -b -- "$binary_path")"
    grep -q 'ELF 64-bit' <<<"$binary_record" ||
        fail "prebuilt artifact is not ELF64: ${binary_path}"
    grep -q 'x86-64' <<<"$binary_record" ||
        fail "prebuilt artifact is not x86-64: ${binary_path}"
done
catalog_sha256="$(sha256sum "$catalog_binary" | awk '{print $1}')"
gateway_sha256="$(sha256sum "$gateway_binary" | awk '{print $1}')"
manager_cli_sha256="$(sha256sum "$manager_cli_binary" | awk '{print $1}')"
runtime_cli_sha256="$(sha256sum "$runtime_cli_binary" | awk '{print $1}')"
observability_cli_sha256="$(sha256sum "$observability_cli_binary" | awk '{print $1}')"
daemon_sha256="$(sha256sum "$daemon_binary" | awk '{print $1}')"
[[ "$catalog_sha256" == "$expected_catalog_sha256" ]] ||
    fail "catalog exporter hash differs from the staged bundle"
[[ "$gateway_sha256" == "$expected_gateway_sha256" ]] ||
    fail "gateway hash differs from the staged bundle"
[[ "$manager_cli_sha256" == "$expected_manager_cli_sha256" ]] ||
    fail "manager CLI hash differs from the staged v0.1.4 bundle"
[[ "$runtime_cli_sha256" == "$expected_runtime_cli_sha256" ]] ||
    fail "runtime CLI hash differs from the staged v0.1.4 bundle"
[[ "$observability_cli_sha256" == "$expected_observability_cli_sha256" ]] ||
    fail "observability CLI hash differs from the staged v0.1.4 bundle"
[[ "$daemon_sha256" == "$expected_daemon_sha256" ]] ||
    fail "daemon hash differs from the staged bundle"
pass "prebuilt Linux AMD64 artifact hashes match the selected bundle"

manager_help="$("$manager_cli_binary" help 2>&1)" ||
    fail "manager CLI help failed"
runtime_help="$("$runtime_cli_binary" --sandbox-id preflight-only help 2>&1)" ||
    fail "runtime CLI help failed"
observability_help="$("$observability_cli_binary" help 2>&1)" ||
    fail "observability CLI help failed"
for operation in list_docker_images create_sandbox destroy_sandbox; do
    grep -qw "$operation" <<<"$manager_help" ||
        fail "manager CLI does not expose ${operation}"
done
for operation in exec_command file_read file_write file_edit; do
    grep -qw "$operation" <<<"$runtime_help" ||
        fail "runtime CLI does not expose ${operation}"
done
grep -qw snapshot <<<"$observability_help" ||
    fail "observability CLI does not expose snapshot"
pass "product CLI catalogs expose the required environment-smoke operations"

benchmark_python="${paper_root}/.venv/bin/python"
[[ -x "$benchmark_python" ]] ||
    fail "paper virtual-environment Python is missing or not executable"
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

available_free_space_bytes="$(
    df -B1 --output=avail -- "$paper_root" |
        awk 'NR == 2 {gsub(/[[:space:]]/, "", $1); print $1}'
)"
[[ "$available_free_space_bytes" =~ ^[0-9]+$ &&
    "$available_free_space_bytes" -ge "$minimum_available_storage_bytes" ]] ||
    fail "paper filesystem has less than 20 GiB available"
pass "paper filesystem has at least 20 GiB available"

cpu_model="$(awk -F: '/^model name/ {sub(/^[[:space:]]+/, "", $2); print $2; exit}' /proc/cpuinfo)"
paper_source_commit="$(
    git -C "$paper_root" rev-parse HEAD 2>/dev/null ||
        printf 'snapshot-without-git-metadata'
)"
printf 'INFO\thostname=%s\n' "$expected_hostname"
printf 'INFO\tkernel=%s\n' "$(uname -r)"
printf 'INFO\tvirtualization=%s\n' "${virtualization:-none}"
printf 'INFO\tcpu_model=%s\n' "${cpu_model:-unknown}"
printf 'INFO\tlogical_cpus=%s\n' "$cpu_count"
printf 'INFO\tmemory_bytes=%s\n' "$memory_bytes"
printf 'INFO\tpaper_filesystem=%s\n' "$paper_filesystem"
printf 'INFO\tproduct_filesystem=%s\n' "$product_filesystem"
printf 'INFO\tpaper_source_commit=%s\n' "$paper_source_commit"
printf 'INFO\tproduct_commit=%s\n' "$product_commit"
printf 'INFO\tdocker_version=%s\n' "$docker_version"
printf 'INFO\tdocker_storage_driver=%s\n' "$docker_driver"
printf 'INFO\tdocker_cgroup_version=%s\n' "$docker_cgroup_version"
printf 'INFO\timage_reference=%s\n' "$image_reference"
printf 'INFO\timage_id=%s\n' "$image_id"
printf 'INFO\tcatalog_sha256=%s\n' "$catalog_sha256"
printf 'INFO\tgateway_sha256=%s\n' "$gateway_sha256"
printf 'INFO\tmanager_cli_sha256=%s\n' "$manager_cli_sha256"
printf 'INFO\truntime_cli_sha256=%s\n' "$runtime_cli_sha256"
printf 'INFO\tobservability_cli_sha256=%s\n' "$observability_cli_sha256"
printf 'INFO\tdaemon_sha256=%s\n' "$daemon_sha256"
printf 'INFO\tworkspace_fixture_hash=%s\n' "$profile_record"
printf 'INFO\tavailable_free_space_bytes=%s\n' "$available_free_space_bytes"

elapsed_seconds="$(( $(date +%s) - started_seconds ))"
[[ "$elapsed_seconds" -le "$maximum_seconds" ]] ||
    fail "preflight took ${elapsed_seconds}s, above the ${maximum_seconds}s budget"
pass "network-free preflight completed in ${elapsed_seconds}s"
