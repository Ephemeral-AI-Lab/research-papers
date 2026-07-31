# Environment qualification

**Status:** base environment qualified; v1.1 IPC qualification passed on 2026-07-31

**Scope:** environment correctness only; no performance experiment

**Current qualifier:** [`scripts/qualify_windows_docker_environment.ps1`](scripts/qualify_windows_docker_environment.ps1)

## Active EXP1 v1.1 treatment

The base host, Docker, image, limits, fixture, and native CLI boundary remain
as qualified below. The active experiment treatment is amended by
[`exp1-v1.1-protocol-amendment.md`](exp1-v1.1-protocol-amendment.md):

- product `main` candidate
  `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`;
- staged package
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-5c48dae1`;
- native Windows named-pipe transport using
  `npipe://./pipe/<unique-name>`;
- canonical `--gateway-endpoint` CLI option;
- one isolated endpoint per gateway execution block, with no retry, TCP
  fallback, or host network mutation.

The exact package hashes and preregistered 25,000-invocation gate are in the
amendment. The TCP examples and v0.1.4 package identities below are retained
only as the historical v1.0 environment record; they are not commands or
inputs for v1.1.

The v1.1 qualifier passed all workload, identity, event-log, owned-TCP,
resource-growth, and cleanup gates. Its retained archive is
`experiments\diagnostics\exp1-v11-ipc-qualification-718cf58dace44dba83bed54601854bc9.zip`,
SHA-256
`2c4f87dc5bb123157f76e6be58b769bafef8943aba36ee8e9202601b50e62a02`.
The archive is qualification-only and supplies no manuscript performance
value.

## Historical v1.0 environment record (do not execute for v1.1)

Everything below this heading records the accepted v1.0 base-environment
qualification. It remains evidence for the unchanged host, Docker, image, and
native-CLI boundary, but its v0.1.4 package, loopback endpoint, and commands are
not active v1.1 inputs. Use the amendment and the active-treatment block above
for v1.1.

### Historical v1.0 selected environment

The selected host is the current native Windows workstation. Docker Desktop
provides the Linux container engine, and the pinned Ubuntu image is the sandbox
guest. Ubuntu is not the host operating system.

| Setting | Qualified value |
|---|---|
| Computer | `DESKTOP-OLP1ADS` |
| Host OS | Native 64-bit Windows, build 26200 |
| Host capacity | 48 logical CPUs, 137,438,953,472 bytes physical memory |
| Host filesystem | NTFS for paper, product, package, workspace, and evidence paths |
| Docker | Docker Desktop client/server 29.0.1 |
| Docker engine | Linux AMD64, `overlayfs`, cgroup v2 |
| Product checkout | clean `main` at `b22862550e0a7cb4fe61ce581831e9244cc492b5` |
| Product release | annotated `v0.1.4`, official Windows AMD64 package |
| Product path | `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox` |
| Paper path | `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1` |
| Staged package | `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-v0.1.4` |
| Workspace base repository | `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\workspace-base\ephemeral-sandbox-v0.1.4` |
| Sandbox image | `ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf` |
| Client boundary | Native `sandbox-manager-cli.exe`, `sandbox-runtime-cli.exe`, and `sandbox-observability-cli.exe` |
| Gateway | Native `sandbox-gateway.exe` |
| Sandbox daemon | Linux x86-64 daemon uploaded into Docker containers |
| Python | Not required by the environment qualifier |

This contract supersedes the earlier native-Ubuntu,
`eos-benchmark-ubuntu24`, ext4, CPython 3.13, SSH, and Linux-transfer-bundle
assumptions. Those assumptions resulted from confusing the Ubuntu sandbox image
with the host.

### Historical v1.0 execution boundary

The qualified control flow is:

1. native Windows PowerShell launches the released Windows gateway;
2. the native Windows manager CLI creates and destroys Docker sandboxes;
3. the native Windows runtime CLI executes commands and file operations;
4. the native Windows observability CLI requests snapshots;
5. Docker Desktop runs the pinned Linux AMD64 Ubuntu sandbox image;
6. the released Linux AMD64 sandbox daemon runs inside each container.

No direct Python gateway client is used. Docker CLI calls in the qualifier are
limited to engine/image inspection, before/after resource auditing, and removal
of shared-base volumes carrying the qualifier's unique gateway-instance label.
Sandbox lifecycle operations themselves use the product manager CLI.

### Historical v1.0 sandbox-creation inputs

The accepted v1.0 qualification used these exact repository-backed inputs:

```powershell
$package = 'C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-v0.1.4'
$workspaceBaseRepo = 'C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\workspace-base\ephemeral-sandbox-v0.1.4'
$image = 'ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf'
$gatewaySocket = '127.0.0.1:7878'

$gateway = "$package\bin\sandbox-gateway.exe"
$managerCli = "$package\bin\sandbox-manager-cli.exe"
$runtimeCli = "$package\bin\sandbox-runtime-cli.exe"
$observabilityCli = "$package\bin\sandbox-observability-cli.exe"
$daemon = "$package\dist\sandbox-daemon-linux-amd64"
```

The workspace base repository is a source-only clean clone:

- branch `main`;
- commit `b22862550e0a7cb4fe61ce581831e9244cc492b5`;
- annotated tag `v0.1.4` resolves to the same commit;
- Git status clean;
- no `target` directory.

Use this clone—not the build checkout, paper repository, or
`Ephemeral-AI-Lab` parent directory—as the value of
`--workspace-bind-root`. This avoids copying the staged binary package and
other generated artifacts into the sandbox shared-base cache.

#### Historical v1.0 gateway launch

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File "$package\bin\start-sandbox-windows-docker-gateway.ps1" `
  -GatewaySocket $gatewaySocket

$gatewayToken = (
  Get-Content -LiteralPath "$HOME\.ephemeral-sandbox\gateway.token" -Raw
).Trim()
```

#### Historical v1.0 manager-CLI sandbox creation

```powershell
$created = & $managerCli `
  --gateway-socket $gatewaySocket `
  --gateway-auth-token $gatewayToken `
  create_sandbox `
  --image $image `
  --workspace-bind-root $workspaceBaseRepo |
  ConvertFrom-Json

$sandboxId = $created.id
```

The accepted create response must report a nonempty sandbox ID, state `ready`,
and the workspace root above. All subsequent operations use that sandbox ID:

```powershell
& $runtimeCli `
  --gateway-socket $gatewaySocket `
  --gateway-auth-token $gatewayToken `
  --sandbox-id $sandboxId `
  exec_command 'pwd && git rev-parse HEAD && git status --short'

& $observabilityCli `
  --gateway-socket $gatewaySocket `
  --gateway-auth-token $gatewayToken `
  snapshot `
  --sandbox-id $sandboxId
```

Destroy the sandbox through the manager CLI:

```powershell
& $managerCli `
  --gateway-socket $gatewaySocket `
  --gateway-auth-token $gatewayToken `
  destroy_sandbox `
  --sandbox-id $sandboxId
```

The strict environment qualifier intentionally uses two tiny isolated fixture
workspaces under its artifact directory instead of the full base repository.
Those fixtures validate the environment and CLI boundary. The source-only base
repository above is the canonical workspace for repo-backed sandbox creation
after qualification.

### Historical v1.0 pinned release package

Official archive:

`C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\v0.1.4-windows-release-input\ephemeral-sandbox-windows-amd64.zip`

Archive SHA-256:

`9f2327578c186897578f0d502893d894aed52be27306f43f75afa3205eba9fdb`

| Package artifact | SHA-256 |
|---|---|
| `bin\sandbox-gateway.exe` | `3a96bedcfa9857bd3881155d758ec2d969f6265456ec3b2878eb6dbb26dc9368` |
| `bin\sandbox-manager-cli.exe` | `b43ec520edc2f436adc8aa7e8b2b50680bb9021883fe23d79a85b17afd2e10fe` |
| `bin\sandbox-runtime-cli.exe` | `df99f2993a7a9e305d33b656fa239b9e11b61a9e2da6e8dfc2f29ae8953067d4` |
| `bin\sandbox-observability-cli.exe` | `0e0471e52750805570876a6244868764c44e166ec653627b9ebd490176e2fcbe` |
| `config\windows-amd64.yml` | `0f0efd15e5111851054e0f7c1ce0f3eaebb3b3047c1b9e2322544036f5daf5db` |
| `dist\sandbox-daemon-linux-amd64` | `2da4395cd835e5325bc3e55b9c2f3b67565ea7c698fce5e086167ec4a2092a39` |

The staged package is under ignored `target/`; the product Git checkout
therefore remains clean.

### Historical v1.0 qualification command

The accepted v1.0 qualifier used this command shape with a new, empty artifact
directory. It must not be reused for the v1.1 IPC gate:

```powershell
$paper = 'C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1'
$artifact = 'C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\diagnostics\qualification-windows-docker-rerun'

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File "$paper\experiments\scripts\qualify_windows_docker_environment.ps1" `
  -ArtifactDirectory $artifact
```

The qualifier performs these strict checks before starting a sandbox:

- native 64-bit Windows host and exact computer name;
- Windows 11-class build, CPU, memory, NTFS capacity, and free space;
- clean product `main` at the selected commit;
- official archive and per-file hashes;
- x64 PE gateway and CLI binaries plus x86-64 ELF daemon;
- required manager/runtime/observability CLI catalogs;
- Docker Desktop server 29.0.1 with Linux AMD64, `overlayfs`, and cgroup v2;
- exact pinned Ubuntu Linux AMD64 image present locally.

It then runs two independent CLI-controlled batches. Each batch validates:

1. `list_docker_images`;
2. `create_sandbox`;
3. `exec_command`;
4. `file_write`;
5. `file_read`;
6. `file_edit`;
7. a second `file_read`;
8. observability `snapshot`;
9. `destroy_sandbox`;
10. post-destroy `list_sandboxes`.

Acceptance requires:

- 2/2 completed batches with distinct sandbox IDs;
- 20 successful product-CLI calls;
- strict response and file-content correctness;
- empty product-CLI stderr;
- zero gateway warnings, errors, or panics;
- no authentication-token leak;
- unchanged global EOS-owned resource/process baseline;
- zero containers or volumes owned by the qualifier's gateway instance;
- completion within 180 seconds.

### Accepted v1.0 base-environment evidence

Accepted artifact directory:

`C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\diagnostics\qualification-windows-docker-20260730-final-6`

Summary:

`windows-docker-cli-env-summary.json`

Archived evidence:

`C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\diagnostics\qualification-windows-docker-20260730-final-6.zip`

Archive SHA-256:

`eea981665b031846677046d4c211e71ad144f8a32507c09058923241d4d0f7f9`

Observed qualification result:

- target `windows_docker_desktop`;
- client cohort `product_cli`;
- 2/2 completed batches;
- 20 validated operations;
- correctness `pass`;
- zero warnings and failures;
- cleanup `pass`;
- ten seconds elapsed;
- zero resources remaining for gateway instance
  `cli-env-windows-20260730T031621Z-34036`.

The elapsed time is an environment-gate observation only. It is not a
performance result and must not enter a paper table.

### Base-environment verdict from the v1.0 qualifier

**GO:** the selected Windows plus Docker Desktop environment is qualified for
CLI-controlled sandbox work.

No native Ubuntu host, SSH exposure, Linux handoff bundle, CPython 3.13
environment, pilot, or performance run is required to close this environment
task.
