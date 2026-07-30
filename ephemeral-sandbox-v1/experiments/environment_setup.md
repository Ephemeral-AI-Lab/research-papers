# Fast environment setup and first-step verification

**Status:** Final-host verification pending  
**Protocol:** [`../experiment_inventory.md`](../experiment_inventory.md)  
**Preflight:** [`scripts/verify_environment.sh`](scripts/verify_environment.sh)

## Principle

The measurement host consumes prebuilt artifacts. It is not a build machine.
The experiment begins by verifying the environment, not by compiling the
product, building a container image, installing web assets, or repairing the
host.

The warm, network-free preflight target is 60 seconds or less. A failure stops
the experiment and is repaired outside the measurement window.

## One selected environment

| Setting | Required value |
|---|---|
| Host | Dedicated Ubuntu Server 24.04 LTS, Linux x86-64 |
| Capacity | At least 8 vCPU, 16 GiB RAM, 100 GiB local NVMe-backed storage |
| Filesystem | ext4 for the paper, product, and benchmark-state paths |
| Cgroup | v2 |
| Runtime | Docker Engine with a reachable server |
| Python | CPython 3.13 |
| Product branch | `main`, clean |
| Sandbox image | `ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf` |
| Sandbox profile | `standard`: 1 vCPU, 512 MiB maximum, 256 PIDs |
| Network | `shared` |
| Benchmark client | `direct_client` |
| Workspace | `paper-100m`: 4,000 files, 100 MiB, maximum depth 100 |

Use native Linux for final numbers. Windows, WSL 2, and Docker Desktop may be
used for editing or non-performance checks but are not the selected measurement
environment.

## Required prebuilt layout

The product checkout must already contain:

```text
ephemeral-sandbox/
|-- target/release/
|   |-- sandbox-gateway
|   `-- sandbox-catalog-export
`-- dist/
    |-- sandbox-daemon-linux-amd64
    `-- git/
        |-- linux-amd64.tar
        `-- linux-arm64.tar
```

The benchmark gateway verifies these paths and refuses symlinks or unsafe,
non-executable files. Preserve the product source commit alongside the
prebuilt bundle so the binary hashes can be tied to a revision.

## Off-clock staging

Complete these actions before the measurement window:

1. Provision the Ubuntu host and Docker Engine.
2. Copy or unpack the clean product checkout and its prebuilt release bundle.
3. Copy or clone the paper checkout containing the paper-local benchmark.
4. Pull the exact image digest once:

   ```sh
   docker pull \
     ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf
   ```

5. Create the benchmark environment once:

   ```sh
   cd /absolute/path/to/research-papers/ephemeral-sandbox-v1
   python3.13 -m venv .venv
   . .venv/bin/activate
   python -m pip install -e "./benchmark[test]"
   ```

6. Confirm the product and paper revisions are the intended revisions.
7. Reboot or otherwise quiesce the host after staging if provisioning caused
   material background activity.

Do not include staging time in benchmark latency. Record it separately if
reproducibility accounting needs it.

## Forbidden during the measurement window

Do not run:

- `cargo build`, `cargo test`, or release packaging;
- `docker build`;
- `npm install`, `npm ci`, or a web build;
- `apt install`, `pip install`, or `uv sync`;
- `git pull`, branch switching, rebasing, or source edits;
- an image pull;
- unrelated workloads or background CI.

If any prerequisite is missing, stop and repair the staged bundle. Do not let a
measurement run silently include compilation, installation, or network fetches.

## First step: network-free preflight

From the paper directory:

```sh
export PRODUCT_ROOT=/absolute/path/to/ephemeral-sandbox
export PRODUCT_BIN_DIR="$PRODUCT_ROOT/target/release"
export IMAGE_REFERENCE='ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf'

mkdir -p experiments/runs/PREFLIGHT_RUN_ID

bash experiments/scripts/verify_environment.sh \
  2>&1 | tee experiments/runs/PREFLIGHT_RUN_ID/environment-preflight.txt
```

The script is read-only except for benchmark-owned `.benchmark-state`
initialization performed by `sandbox-benchmark validate`. It does not build,
install, or pull anything.

## Preflight acceptance

All items must pass:

- [ ] Linux x86-64.
- [ ] Ubuntu 24.04.
- [ ] At least 8 logical CPUs.
- [ ] At least 15 GiB reported usable memory.
- [ ] ext4 at the paper and product roots.
- [ ] Cgroup v2 controllers available.
- [ ] Docker server reachable.
- [ ] Exact pinned image already present and `linux/amd64`.
- [ ] Product checkout on clean `main`.
- [ ] `sandbox-gateway` and `sandbox-catalog-export` are executable.
- [ ] Linux AMD64 daemon is executable ELF.
- [ ] Both fixed Git toolchain archives exist and are non-empty.
- [ ] CPython 3.13 paper virtual environment exists.
- [ ] `paper-env-smoke` validates against the prebuilt product catalog.
- [ ] `paper-100m` resolves to 4,000 files, 104,857,600 bytes, depth 100.
- [ ] Warm preflight completes in 60 seconds or less.

The script prints the product commit, product dirty state, Docker version,
image identity, binary hashes, fixture hash, plan hash, and elapsed time. Archive
the complete output.

## Second step: minimal live smoke

Only after preflight passes:

```sh
. .venv/bin/activate

sandbox-benchmark run \
  --test-repository-root "$PWD" \
  --product-root "$PRODUCT_ROOT" \
  --product-bin-dir "$PRODUCT_BIN_DIR" \
  --plan paper-env-smoke
```

The smoke preset uses the small fixture so the environment is verified quickly.
It executes one prepared-session no-op command and one prepared-sandbox session
creation. Smoke results are exploratory and never enter paper tables.

Accept the live environment only if:

- the campaign completes;
- operation verification passes;
- cleanup restores the baseline;
- no benchmark-owned containers, processes, or runtime paths leak;
- wall time is at most 3 minutes.

## Warm-state policy

The good pass uses a warm, pre-staged environment:

- image present locally;
- Python environment already installed;
- product binaries already placed;
- fixture cache may be materialized by the exploratory pilot;
- no manual host page-cache drop;
- no source or configuration changes between preflight and run.

This policy avoids mixing network, package installation, product compilation,
and first-time fixture construction into operation measurements. Record the
policy in Table 1.

## Good-pass command

After the protocol and commits are frozen:

```sh
bash experiments/scripts/verify_environment.sh \
  2>&1 | tee experiments/runs/GOOD_PASS_RUN_ID/environment-preflight.txt

. .venv/bin/activate

sandbox-benchmark run \
  --test-repository-root "$PWD" \
  --product-root "$PRODUCT_ROOT" \
  --product-bin-dir "$PRODUCT_BIN_DIR" \
  --plan paper-good-pass
```

Do not run the good pass until every Phase 3 instrumentation item in
[`../experiment_inventory.md`](../experiment_inventory.md) is resolved.

## Current verification state

Verified on 2026-07-30:

- the registry exposes the selected Linux AMD64 Ubuntu manifest digest;
- Docker Desktop 29.0.1 exposes a Linux AMD64 engine with cgroup v2 and the
  `overlayfs` storage driver;
- the exact pinned image is present locally and reports `linux/amd64`;
- a disposable-container probe enforced the planned 1 vCPU, 512 MiB, and
  256-PID limits;
- a disposable privileged probe mounted, copied up, wrote through, and
  unmounted nested OverlayFS when given a separate `tmpfs` backing store;
- a container-to-Windows bind-mount write/read round trip passed;
- the paper-local profile loads as 4,000 files, 100 MiB, depth 100;
- the profile's deterministic fixture identity is
  `sha256:9484b132c8a35afd18bc37383759d0fe6d45dd4700b42a99336aed535e651cc7`;
- the two depth-bound tests pass under Python 3.13.

Not verified:

- the selected final Ubuntu host;
- local presence of the pinned image on that host;
- final product binaries and hashes;
- ext4, cgroup, and Docker readiness on that host;
- a live smoke or measured campaign.

The current Windows workstation remains a development and capability-check
environment, not the selected measurement host. Docker Desktop now works, but
the checkout is on a WSL `9p` mount, the WSL distribution is Ubuntu 26.04, and
the prebuilt Linux product bundle is incomplete.

### Current workstation Gate 1 score

After Docker Desktop was started, the 2026-07-30 audit passed 7 of 15 strict
acceptance items (about 47%), not 70%:

| Gate item | Current workstation |
|---|---|
| Linux x86-64 | Partial: Linux AMD64 is available through Docker Desktop/WSL 2, not the selected native host |
| Ubuntu 24.04 | Fail: WSL distribution reports Ubuntu 26.04 |
| At least 8 CPUs | Pass: 48 exposed |
| At least 15 GiB memory | Pass: approximately 62.8 GiB exposed |
| ext4 paper/product roots | Fail: Windows checkout is mounted through WSL `9p` |
| Cgroup v2 | Pass |
| Docker server | Pass: client/server 29.0.1, Linux AMD64, `overlayfs`, cgroup v2 |
| Pinned image local | Pass: exact digest, Linux AMD64 |
| Clean product `main` | Pass |
| Gateway/catalog binaries | Fail: missing |
| Daemon and Git archives | Fail: daemon present; both archives missing |
| Linux CPython 3.13 environment | Fail: WSL Python is 3.14; Python 3.13 exists only in the Windows venv |
| Product-catalog plan validation | Fail: exporter binary missing |
| `paper-100m` profile | Pass |
| Preflight within 60 seconds | Not run because prerequisites fail |

The Docker substrate is now sufficiently validated to support continued
development: resource controls, the pinned image, nested OverlayFS on an
appropriate backing store, and bind mounts all passed. A direct nested
OverlayFS attempt on the container's existing overlay root failed, as expected
for overlay-on-overlay; therefore the successful `tmpfs`-backed probe does not
replace a live product smoke using the product's real storage layout.

The benchmark configuration is also validated by profile checks, focused tests,
planner expansion, Python 3.13 imports, and shell syntax. Confidence that the
design can run after staging the required Linux bundle is moderate to high.
Confidence in this workstation as a paper-grade measurement host is still low:
the strict gate is 7/15, and no end-to-end sandbox has been launched.
