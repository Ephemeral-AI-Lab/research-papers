param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,
    [string]$ProductRoot = ""
)

$ErrorActionPreference = "Stop"
$paperRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
if (-not $ProductRoot) {
    $ProductRoot = Join-Path $paperRoot "..\..\ephemeral-sandbox"
}
$product = (Resolve-Path -LiteralPath $ProductRoot).Path
$output = [System.IO.Path]::GetFullPath($OutputDirectory)

if (Test-Path -LiteralPath $output) {
    if ((Get-ChildItem -Force -LiteralPath $output | Measure-Object).Count -ne 0) {
        throw "OutputDirectory must not exist or must be empty: $output"
    }
} else {
    New-Item -ItemType Directory -Path $output | Out-Null
}

$expectedCommit = "b22862550e0a7cb4fe61ce581831e9244cc492b5"
$expectedHashes = @{
    "target/release/sandbox-gateway" = "f1f8420bfa6ea6370d90fbf8428c432fe6f1031b0cb7cc7d32ac543dc8be2faf"
    "target/release/sandbox-catalog-export" = "c841597bab53612a2f424088264a0fce383b54ded480050d99fbed1c529ac8ba"
    "target/release/sandbox-manager-cli" = "0be4f0c26f8f50b76b175d04cfeec61529a605bcda9ffcd6782a09096ba2983f"
    "target/release/sandbox-runtime-cli" = "e9ac5f6c7a5f9c07a3de166b320e7d6065fa9480a7f18d6d59114337d15e28e7"
    "target/release/sandbox-observability-cli" = "6b2dae2369344cbb3960a76f6ccdfa869a7aa9b7a7a255f8a634f4a52d5cfdb5"
    "dist/sandbox-daemon-linux-amd64" = "a55d4775b992c02d603ca294746fb314e99d59774732ab7b8e7bf24ef010fb22"
}

$branch = (& git -c core.longpaths=true -C $product branch --show-current).Trim()
$commit = (& git -c core.longpaths=true -C $product rev-parse HEAD).Trim()
$productStatus = @(& git -c core.longpaths=true -C $product status --porcelain=v1)
if ($LASTEXITCODE -ne 0 -or $branch -ne "main" -or $commit -ne $expectedCommit -or $productStatus.Count -ne 0) {
    throw "Product must be clean main at $expectedCommit"
}

foreach ($relative in $expectedHashes.Keys) {
    $path = Join-Path $product ($relative.Replace("/", "\"))
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing product artifact: $path"
    }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    if ($actual -ne $expectedHashes[$relative]) {
        throw "Product artifact hash mismatch: $relative"
    }
}

$productBundle = Join-Path $output "product-main.bundle"
& git -c core.longpaths=true -C $product bundle create $productBundle main
if ($LASTEXITCODE -ne 0) {
    throw "git bundle creation failed"
}

$artifactArchive = Join-Path $output "product-artifacts.tar.gz"
& tar.exe -czf $artifactArchive -C $product `
    "target/release/sandbox-gateway" `
    "target/release/sandbox-catalog-export" `
    "target/release/sandbox-manager-cli" `
    "target/release/sandbox-runtime-cli" `
    "target/release/sandbox-observability-cli" `
    "dist/sandbox-daemon-linux-amd64"
if ($LASTEXITCODE -ne 0) {
    throw "product artifact archive creation failed"
}

$paperArchive = Join-Path $output "paper-snapshot.tar.gz"
& tar.exe -czf $paperArchive `
    "--exclude=.venv" `
    "--exclude=.benchmark-state" `
    "--exclude=__pycache__" `
    "--exclude=.pytest_cache" `
    "--exclude=experiments/runs" `
    -C $paperRoot "."
if ($LASTEXITCODE -ne 0) {
    throw "paper snapshot archive creation failed"
}

$paperRepository = (Resolve-Path -LiteralPath (Join-Path $paperRoot "..")).Path
$paperCommit = (& git -c core.longpaths=true -C $paperRepository rev-parse HEAD).Trim()
$paperStatus = @(
    & git -c core.longpaths=true -C $paperRepository status --porcelain=v1 -- "ephemeral-sandbox-v1"
)
$archives = @{}
foreach ($path in @($productBundle, $artifactArchive, $paperArchive)) {
    $archives[[System.IO.Path]::GetFileName($path)] = @{
        bytes = (Get-Item -LiteralPath $path).Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    }
}
$manifest = @{
    schema_version = 1
    created_at_utc = [DateTime]::UtcNow.ToString("o")
    selected_host = "eos-benchmark-ubuntu24"
    selected_paths = @{
        product = "/srv/eos-benchmark/product"
        paper = "/srv/eos-benchmark/paper"
    }
    product = @{
        branch = $branch
        commit = $commit
        dirty = $false
        release_tag = "v0.1.4"
        linux_release_archive_sha256 = "308563ad38bc7a9c5000acd54251db872e2e6a58bf70846d14760fef2b0d713c"
        qualification_client_cohort = "product_cli"
        artifact_sha256 = $expectedHashes
    }
    paper = @{
        repository_commit = $paperCommit
        dirty = ($paperStatus.Count -ne 0)
        status = $paperStatus
    }
    archives = $archives
}
$manifest | ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath (Join-Path $output "bundle-manifest.json") -Encoding UTF8

@"
On eos-benchmark-ubuntu24, after copying this directory to an off-clock staging path:

sudo install -d -o "`$USER" -g "`$USER" /srv/eos-benchmark
git clone ./product-main.bundle /srv/eos-benchmark/product
mkdir /srv/eos-benchmark/paper
tar -xzf ./product-artifacts.tar.gz -C /srv/eos-benchmark/product
tar -xzf ./paper-snapshot.tar.gz -C /srv/eos-benchmark/paper
cd /srv/eos-benchmark/paper
bash experiments/scripts/stage_final_host.sh 2>&1 | tee staging-final-host.txt

After staging, quiesce or reboot the host if provisioning caused background activity.
Then run:

cd /srv/eos-benchmark/paper
bash experiments/scripts/qualify_final_host.sh
"@ | Set-Content -LiteralPath (Join-Path $output "HANDOFF.txt") -Encoding UTF8

Get-ChildItem -File -LiteralPath $output |
    Select-Object Name, Length, @{Name = "SHA256"; Expression = {
        (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
    }}
