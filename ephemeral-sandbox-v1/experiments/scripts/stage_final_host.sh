#!/usr/bin/env bash
set -euo pipefail

paper_root="/srv/eos-benchmark/paper"
product_root="/srv/eos-benchmark/product"
product_bin_dir="${product_root}/target/release"
expected_hostname="eos-benchmark-ubuntu24"
expected_product_commit="b22862550e0a7cb4fe61ce581831e9244cc492b5"
expected_docker_version="29.0.1"
image_reference="ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf"
expected_catalog_sha256="c841597bab53612a2f424088264a0fce383b54ded480050d99fbed1c529ac8ba"
expected_gateway_sha256="f1f8420bfa6ea6370d90fbf8428c432fe6f1031b0cb7cc7d32ac543dc8be2faf"
expected_daemon_sha256="a55d4775b992c02d603ca294746fb314e99d59774732ab7b8e7bf24ef010fb22"
expected_manager_cli_sha256="0be4f0c26f8f50b76b175d04cfeec61529a605bcda9ffcd6782a09096ba2983f"
expected_runtime_cli_sha256="e9ac5f6c7a5f9c07a3de166b320e7d6065fa9480a7f18d6d59114337d15e28e7"
expected_observability_cli_sha256="6b2dae2369344cbb3960a76f6ccdfa869a7aa9b7a7a255f8a634f4a52d5cfdb5"

fail() {
    printf 'FAIL\t%s\n' "$1" >&2
    exit 1
}

[[ "$(id -u)" -ne 0 ]] || fail "run staging as the benchmark user, not root"
[[ "$(hostname -s)" == "$expected_hostname" ]] ||
    fail "logical hostname is not ${expected_hostname}"
[[ "$(pwd -P)" == "$paper_root" ]] || fail "run from ${paper_root}"
[[ -d "$product_root/.git" ]] || fail "product checkout is missing"
[[ "$(git -C "$product_root" branch --show-current)" == "main" ]] ||
    fail "product checkout is not on main"
[[ -z "$(git -C "$product_root" status --porcelain=v1)" ]] ||
    fail "product checkout is dirty"
[[ "$(git -C "$product_root" rev-parse HEAD)" == "$expected_product_commit" ]] ||
    fail "product checkout is not at the selected commit"
[[ "$(docker version --format '{{.Server.Version}}' 2>/dev/null)" == "$expected_docker_version" ]] ||
    fail "Docker server is not ${expected_docker_version}"
command -v python3.13 >/dev/null 2>&1 || fail "python3.13 is unavailable"
[[ "$(python3.13 --version 2>&1)" == Python\ 3.13.* ]] ||
    fail "python3.13 does not report CPython 3.13"

catalog_binary="${product_bin_dir}/sandbox-catalog-export"
gateway_binary="${product_bin_dir}/sandbox-gateway"
manager_cli_binary="${product_bin_dir}/sandbox-manager-cli"
runtime_cli_binary="${product_bin_dir}/sandbox-runtime-cli"
observability_cli_binary="${product_bin_dir}/sandbox-observability-cli"
daemon_binary="${product_root}/dist/sandbox-daemon-linux-amd64"
for artifact in \
    "$catalog_binary" \
    "$gateway_binary" \
    "$manager_cli_binary" \
    "$runtime_cli_binary" \
    "$observability_cli_binary" \
    "$daemon_binary"
do
    [[ -f "$artifact" && ! -L "$artifact" && -s "$artifact" ]] ||
        fail "staged artifact is missing or unsafe: ${artifact}"
    chmod 0755 -- "$artifact"
done
[[ "$(sha256sum "$catalog_binary" | awk '{print $1}')" == "$expected_catalog_sha256" ]] ||
    fail "catalog exporter hash mismatch"
[[ "$(sha256sum "$gateway_binary" | awk '{print $1}')" == "$expected_gateway_sha256" ]] ||
    fail "gateway hash mismatch"
[[ "$(sha256sum "$manager_cli_binary" | awk '{print $1}')" == "$expected_manager_cli_sha256" ]] ||
    fail "manager CLI hash mismatch"
[[ "$(sha256sum "$runtime_cli_binary" | awk '{print $1}')" == "$expected_runtime_cli_sha256" ]] ||
    fail "runtime CLI hash mismatch"
[[ "$(sha256sum "$observability_cli_binary" | awk '{print $1}')" == "$expected_observability_cli_sha256" ]] ||
    fail "observability CLI hash mismatch"
[[ "$(sha256sum "$daemon_binary" | awk '{print $1}')" == "$expected_daemon_sha256" ]] ||
    fail "daemon hash mismatch"

docker pull "$image_reference"
[[ "$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$image_reference")" == "linux/amd64" ]] ||
    fail "staged image platform is not linux/amd64"

if [[ ! -d .venv ]]; then
    python3.13 -m venv .venv
fi
[[ "$(.venv/bin/python --version 2>&1)" == Python\ 3.13.* ]] ||
    fail "existing paper virtual environment is not CPython 3.13"
.venv/bin/python -m pip install --require-hashes \
    -r experiments/final-host-requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e ./benchmark

printf 'PASS\toff-clock staging completed\n'
printf 'INFO\tproduct_commit=%s\n' "$expected_product_commit"
printf 'INFO\timage_reference=%s\n' "$image_reference"
printf 'INFO\tclient_cohort=product_cli\n'
printf 'INFO\tpython=%s\n' "$(.venv/bin/python --version 2>&1)"
printf 'INFO\tpip=%s\n' "$(.venv/bin/python -m pip --version)"
printf 'INFO\tnext=bash experiments/scripts/qualify_final_host.sh\n'
