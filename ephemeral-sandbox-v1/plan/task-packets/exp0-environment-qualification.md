# EXP0 environment qualification

**Status:** Complete
**Date:** 2026-07-30
**Scope:** Environment correctness only

## Objective

Qualify the native Windows workstation and Docker Desktop Linux engine using
only the released product CLIs for sandbox operations.

## Corrected environment boundary

- Host: native Windows x64, `DESKTOP-OLP1ADS`, build 26200.
- Container engine: Docker Desktop 29.0.1, Linux AMD64, `overlayfs`, cgroup v2.
- Sandbox guest: pinned Ubuntu 24.04 Linux AMD64 image.
- Product: clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`, release `v0.1.4`.
- Control path: native Windows gateway, manager CLI, runtime CLI, and
  observability CLI.
- Daemon: released Linux x86-64 artifact running inside Docker containers.
- Host storage: NTFS.
- Python: not required for environment qualification.

The earlier native-Ubuntu host contract was incorrect because it treated the
Ubuntu sandbox image as the host. It is superseded.

## Work completed

1. Downloaded and checksum-verified the official `v0.1.4` Windows AMD64
   release.
2. Staged the complete package under ignored
   `ephemeral-sandbox\target\windows-v0.1.4`; product Git remained clean.
3. Added a PowerShell-only strict qualifier for the Windows host, package,
   Docker Desktop engine, image, and CLI contracts.
4. Ran two independent product-CLI-controlled sandbox lifecycles.
5. Validated 20 CLI operations, response correctness, file correctness,
   observability, product-CLI destruction, warning/failure absence, token
   secrecy, and cleanup.
6. Archived the accepted artifact set.

## Accepted evidence

- Artifact directory:
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\diagnostics\qualification-windows-docker-20260730-final-6`
- Summary:
  `windows-docker-cli-env-summary.json`
- Archive:
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\diagnostics\qualification-windows-docker-20260730-final-6.zip`
- Archive SHA-256:
  `eea981665b031846677046d4c211e71ad144f8a32507c09058923241d4d0f7f9`

## Acceptance result

- Host/package/Docker/image preflight: pass.
- Client cohort: `product_cli`.
- Batches: 2/2.
- Validated operations: 20.
- Correctness: pass.
- Warnings/failures: 0/0.
- Cleanup: pass.
- Qualifier-owned containers/volumes after completion: 0/0.
- Elapsed time: 10 seconds, environment evidence only.

## Verdict

**GO.** The selected Windows plus Docker Desktop environment is qualified.
Nothing else is required for this environment-only task.
