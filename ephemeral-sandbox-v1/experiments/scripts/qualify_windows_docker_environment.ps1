[CmdletBinding()]
param(
    [string]$PaperRoot = "",
    [string]$ProductRoot = "",
    [string]$PackageRoot = "",
    [string]$ArtifactDirectory = "",
    [string]$ExpectedComputerName = "DESKTOP-OLP1ADS",
    [string]$ImageReference = "ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf",
    [int]$MaximumSeconds = 180
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$expectedProductCommit = "b22862550e0a7cb4fe61ce581831e9244cc492b5"
$expectedDockerVersion = "29.0.1"
$expectedReleaseArchiveSha256 = "9f2327578c186897578f0d502893d894aed52be27306f43f75afa3205eba9fdb"
$expectedHashes = [ordered]@{
    "bin\sandbox-gateway.exe" = "3a96bedcfa9857bd3881155d758ec2d969f6265456ec3b2878eb6dbb26dc9368"
    "bin\sandbox-manager-cli.exe" = "b43ec520edc2f436adc8aa7e8b2b50680bb9021883fe23d79a85b17afd2e10fe"
    "bin\sandbox-runtime-cli.exe" = "df99f2993a7a9e305d33b656fa239b9e11b61a9e2da6e8dfc2f29ae8953067d4"
    "bin\sandbox-observability-cli.exe" = "0e0471e52750805570876a6244868764c44e166ec653627b9ebd490176e2fcbe"
    "config\windows-amd64.yml" = "0f0efd15e5111851054e0f7c1ce0f3eaebb3b3047c1b9e2322544036f5daf5db"
    "dist\sandbox-daemon-linux-amd64" = "2da4395cd835e5325bc3e55b9c2f3b67565ea7c698fce5e086167ec4a2092a39"
}

if (-not $PaperRoot) {
    $PaperRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
}
$PaperRoot = (Resolve-Path -LiteralPath $PaperRoot).Path
if (-not $ProductRoot) {
    $ProductRoot = Join-Path $PaperRoot "..\..\ephemeral-sandbox"
}
$ProductRoot = (Resolve-Path -LiteralPath $ProductRoot).Path
if (-not $PackageRoot) {
    $PackageRoot = Join-Path $ProductRoot "target\windows-v0.1.4"
}
$PackageRoot = (Resolve-Path -LiteralPath $PackageRoot).Path
if (-not $ArtifactDirectory) {
    $qualificationId = "qualification-windows-docker-$([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))"
    $ArtifactDirectory = Join-Path $PaperRoot "experiments\runs\$qualificationId"
}
$ArtifactDirectory = [System.IO.Path]::GetFullPath($ArtifactDirectory)
if (Test-Path -LiteralPath $ArtifactDirectory) {
    if ((Get-ChildItem -Force -LiteralPath $ArtifactDirectory | Measure-Object).Count -ne 0) {
        throw "ArtifactDirectory must not exist or must be empty: $ArtifactDirectory"
    }
} else {
    New-Item -ItemType Directory -Path $ArtifactDirectory | Out-Null
}

$startedAt = [DateTime]::UtcNow
$preflightLog = Join-Path $ArtifactDirectory "environment-preflight.txt"
$gatewayStdout = Join-Path $ArtifactDirectory "gateway.stdout.log"
$gatewayStderr = Join-Path $ArtifactDirectory "gateway.stderr.log"
$gatewayPidFile = Join-Path $ArtifactDirectory "gateway.pid"
$gatewayConfig = Join-Path $ArtifactDirectory "effective-windows-docker.yml"
$gatewayRegistry = Join-Path $ArtifactDirectory "gateway-registry.json"
$summaryPath = Join-Path $ArtifactDirectory "windows-docker-cli-env-summary.json"
$beforeStatePath = Join-Path $ArtifactDirectory "owned-state-before.txt"
$afterStatePath = Join-Path $ArtifactDirectory "owned-state-after.txt"
$gatewayInstanceId = "cli-env-windows-$([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))-$PID"
$authToken = [guid]::NewGuid().ToString("N")
$gatewayProcess = $null
$activeSandboxId = $null
$batchSandboxIds = [System.Collections.Generic.List[string]]::new()
$cleanupErrors = [System.Collections.Generic.List[string]]::new()
$primaryError = $null
$originalSharedBaseCache = $env:EOS_SHARED_BASE_CACHE

function Write-Record([string]$Kind, [string]$Message) {
    $line = "$Kind`t$Message"
    Write-Host $line
    Add-Content -LiteralPath $preflightLog -Value $line -Encoding utf8
}

function Pass([string]$Message) {
    Write-Record "PASS" $Message
}

function Info([string]$Message) {
    Write-Record "INFO" $Message
}

function Fail([string]$Message) {
    Write-Record "FAIL" $Message
    throw $Message
}

function Quote-ProcessArgument([string]$Value) {
    if ($Value -match '[\s"]') {
        return '"' + ($Value -replace '"', '\"') + '"'
    }
    return $Value
}

function Assert-X64Pe([string]$Path) {
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 128 -or $bytes[0] -ne 0x4d -or $bytes[1] -ne 0x5a) {
        Fail "not a valid PE executable: $Path"
    }
    $peOffset = [BitConverter]::ToInt32($bytes, 0x3c)
    if ($peOffset -lt 0 -or $peOffset + 6 -gt $bytes.Length) {
        Fail "invalid PE header offset: $Path"
    }
    if (
        $bytes[$peOffset] -ne 0x50 -or
        $bytes[$peOffset + 1] -ne 0x45 -or
        $bytes[$peOffset + 2] -ne 0 -or
        $bytes[$peOffset + 3] -ne 0
    ) {
        Fail "missing PE signature: $Path"
    }
    $machine = [BitConverter]::ToUInt16($bytes, $peOffset + 4)
    if ($machine -ne 0x8664) {
        Fail "PE executable is not x64: $Path"
    }
}

function Assert-X64Elf([string]$Path) {
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if (
        $bytes.Length -lt 20 -or
        $bytes[0] -ne 0x7f -or
        $bytes[1] -ne 0x45 -or
        $bytes[2] -ne 0x4c -or
        $bytes[3] -ne 0x46 -or
        $bytes[4] -ne 2
    ) {
        Fail "daemon is not ELF64: $Path"
    }
    $machine = [BitConverter]::ToUInt16($bytes, 18)
    if ($machine -ne 0x3e) {
        Fail "daemon ELF is not x86-64: $Path"
    }
}

function Get-FreeTcpSocket {
    $listener = [System.Net.Sockets.TcpListener]::new(
        [System.Net.IPAddress]::Loopback,
        0
    )
    $listener.Start()
    try {
        $port = ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
    } finally {
        $listener.Stop()
    }
    return "127.0.0.1:$port"
}

function Get-OwnedState {
    $records = [System.Collections.Generic.List[string]]::new()
    @(& docker ps -aq --filter "label=eos.gateway_instance_id") |
        Where-Object { $_ } |
        ForEach-Object { $records.Add("container`t$_") }
    @(& docker volume ls -q --filter "label=eos.gateway_instance_id") |
        Where-Object { $_ } |
        ForEach-Object { $records.Add("volume`t$_") }
    Get-Process -Name "sandbox-gateway" -ErrorAction SilentlyContinue |
        ForEach-Object { $records.Add("process`t$($_.Id)") }
    return @($records | Sort-Object)
}

function Invoke-ProductCli(
    [string]$RecordName,
    [string]$Executable,
    [string[]]$Arguments
) {
    $stdoutPath = Join-Path $ArtifactDirectory "$RecordName.json"
    $stderrPath = Join-Path $ArtifactDirectory "$RecordName.stderr"
    $output = @(& $Executable @Arguments 2> $stderrPath)
    $exitCode = $LASTEXITCODE
    ($output -join [Environment]::NewLine) |
        Set-Content -LiteralPath $stdoutPath -Encoding utf8
    if ($exitCode -ne 0) {
        Fail "$RecordName exited with code $exitCode"
    }
    if ((Get-Item -LiteralPath $stderrPath).Length -ne 0) {
        Fail "$RecordName emitted stderr"
    }
    $raw = Get-Content -Raw -LiteralPath $stdoutPath
    try {
        return $raw | ConvertFrom-Json
    } catch {
        Fail "$RecordName did not produce valid JSON"
    }
}

function Invoke-ManagerCli([string]$RecordName, [string[]]$Arguments) {
    $prefix = @(
        "--gateway-socket", $gatewaySocket,
        "--gateway-auth-token", $authToken
    )
    return Invoke-ProductCli $RecordName $managerCli ($prefix + $Arguments)
}

function Invoke-RuntimeCli(
    [string]$RecordName,
    [string]$SandboxId,
    [string[]]$Arguments
) {
    $prefix = @(
        "--gateway-socket", $gatewaySocket,
        "--gateway-auth-token", $authToken,
        "--sandbox-id", $SandboxId
    )
    return Invoke-ProductCli $RecordName $runtimeCli ($prefix + $Arguments)
}

function Invoke-ObservabilityCli(
    [string]$RecordName,
    [string]$SandboxId
) {
    $arguments = @(
        "--gateway-socket", $gatewaySocket,
        "--gateway-auth-token", $authToken,
        "snapshot",
        "--sandbox-id", $SandboxId
    )
    return Invoke-ProductCli $RecordName $observabilityCli $arguments
}

function Stop-QualificationGateway {
    if ($null -eq $gatewayProcess) {
        return
    }
    $process = Get-Process -Id $gatewayProcess.Id -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $process.Id -ErrorAction SilentlyContinue
        try {
            Wait-Process -Id $process.Id -Timeout 5 -ErrorAction Stop
        } catch {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
    $script:gatewayProcess = $null
}

function Remove-QualificationVolumes {
    $volumes = @(
        & docker volume ls -q `
            --filter "label=eos.gateway_instance_id=$gatewayInstanceId"
    ) | Where-Object { $_ }
    foreach ($volume in $volumes) {
        $record = @(& docker volume inspect $volume | ConvertFrom-Json)[0]
        $actualGatewayId = $record.Labels."eos.gateway_instance_id"
        if ($actualGatewayId -ne $gatewayInstanceId) {
            throw "refusing cleanup of volume with mismatched owner: $volume"
        }
        & docker volume rm -- $volume |
            Add-Content -LiteralPath (Join-Path $ArtifactDirectory "owned-volume-cleanup.stdout") -Encoding utf8
        if ($LASTEXITCODE -ne 0) {
            throw "failed to remove qualification-owned volume: $volume"
        }
    }
}

function Cleanup-Qualification {
    if ($activeSandboxId) {
        try {
            $cleanupStdout = Join-Path $ArtifactDirectory "cleanup-destroy.json"
            $cleanupStderr = Join-Path $ArtifactDirectory "cleanup-destroy.stderr"
            $arguments = @(
                "--gateway-socket", $gatewaySocket,
                "--gateway-auth-token", $authToken,
                "destroy_sandbox",
                "--sandbox-id", $activeSandboxId
            )
            $output = @(& $managerCli @arguments 2> $cleanupStderr)
            ($output -join [Environment]::NewLine) |
                Set-Content -LiteralPath $cleanupStdout -Encoding utf8
            if ($LASTEXITCODE -ne 0) {
                $cleanupErrors.Add("product CLI failed to destroy active sandbox $activeSandboxId")
            }
        } catch {
            $cleanupErrors.Add("cleanup destroy exception: $($_.Exception.Message)")
        }
        $script:activeSandboxId = $null
    }
    Stop-QualificationGateway
    try {
        Remove-QualificationVolumes
    } catch {
        $cleanupErrors.Add($_.Exception.Message)
    }
    $ownedContainers = @(@(
        & docker ps -aq `
            --filter "label=eos.gateway_instance_id=$gatewayInstanceId"
    ) | Where-Object { $_ })
    $ownedVolumes = @(@(
        & docker volume ls -q `
            --filter "label=eos.gateway_instance_id=$gatewayInstanceId"
    ) | Where-Object { $_ })
    if ($ownedContainers.Count -ne 0) {
        $cleanupErrors.Add("qualification gateway left $($ownedContainers.Count) container(s)")
    }
    if ($ownedVolumes.Count -ne 0) {
        $cleanupErrors.Add("qualification gateway left $($ownedVolumes.Count) volume(s)")
    }
    if ($null -eq $originalSharedBaseCache) {
        Remove-Item Env:EOS_SHARED_BASE_CACHE -ErrorAction SilentlyContinue
    } else {
        $env:EOS_SHARED_BASE_CACHE = $originalSharedBaseCache
    }
}

$gateway = Join-Path $PackageRoot "bin\sandbox-gateway.exe"
$managerCli = Join-Path $PackageRoot "bin\sandbox-manager-cli.exe"
$runtimeCli = Join-Path $PackageRoot "bin\sandbox-runtime-cli.exe"
$observabilityCli = Join-Path $PackageRoot "bin\sandbox-observability-cli.exe"
$daemon = Join-Path $PackageRoot "dist\sandbox-daemon-linux-amd64"
$templateConfig = Join-Path $PackageRoot "config\windows-amd64.yml"
$releaseArchive = Join-Path (
    Split-Path -Parent $ProductRoot
) "final-host-staging\v0.1.4-windows-release-input\ephemeral-sandbox-windows-amd64.zip"
$gatewaySocket = Get-FreeTcpSocket

try {
    $beforeState = @(Get-OwnedState)
    $beforeState | Set-Content -LiteralPath $beforeStatePath -Encoding utf8

    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        Fail "qualification host is not Windows"
    }
    if (-not [Environment]::Is64BitOperatingSystem) {
        Fail "Windows host is not 64-bit"
    }
    if ($env:COMPUTERNAME -ne $ExpectedComputerName) {
        Fail "computer name is not $ExpectedComputerName"
    }
    $os = Get-CimInstance Win32_OperatingSystem
    $buildNumber = [int]$os.BuildNumber
    if ($buildNumber -lt 22000) {
        Fail "Windows build is older than the Windows 11 baseline"
    }
    Pass "native Windows x64 host $ExpectedComputerName uses build $buildNumber"

    $computer = Get-CimInstance Win32_ComputerSystem
    if ([int]$computer.NumberOfLogicalProcessors -lt 8) {
        Fail "host exposes fewer than 8 logical processors"
    }
    if ([int64]$computer.TotalPhysicalMemory -lt 15GB) {
        Fail "host exposes less than 15 GiB physical memory"
    }
    Pass "host capacity is $($computer.NumberOfLogicalProcessors) logical CPUs and $($computer.TotalPhysicalMemory) bytes memory"

    foreach ($root in @($PaperRoot, $ProductRoot, $PackageRoot)) {
        $drive = [System.IO.Path]::GetPathRoot($root).TrimEnd("\").TrimEnd(":")
        $volume = Get-Volume -DriveLetter $drive
        if ($volume.FileSystem -ne "NTFS") {
            Fail "host path is not on NTFS: $root"
        }
        if ([int64]$volume.Size -lt 100GB) {
            Fail "host filesystem is smaller than 100 GiB: $root"
        }
        if ([int64]$volume.SizeRemaining -lt 20GB) {
            Fail "host filesystem has less than 20 GiB free: $root"
        }
    }
    Pass "paper, product, and package roots are on NTFS with required capacity"

    $branch = (& git -C $ProductRoot branch --show-current).Trim()
    $commit = (& git -C $ProductRoot rev-parse HEAD).Trim()
    $status = @(& git -C $ProductRoot status --porcelain=v1)
    if ($branch -ne "main" -or $commit -ne $expectedProductCommit -or $status.Count -ne 0) {
        Fail "product checkout is not clean main at $expectedProductCommit"
    }
    Pass "product checkout is clean main at $commit"

    if (-not (Test-Path -LiteralPath $releaseArchive -PathType Leaf)) {
        Fail "official Windows release archive is missing"
    }
    $releaseArchiveHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $releaseArchive).Hash.ToLowerInvariant()
    if ($releaseArchiveHash -ne $expectedReleaseArchiveSha256) {
        Fail "official Windows release archive hash mismatch"
    }
    Pass "official v0.1.4 Windows archive hash matches"

    foreach ($relativePath in $expectedHashes.Keys) {
        $path = Join-Path $PackageRoot $relativePath
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            Fail "release payload is missing: $relativePath"
        }
        $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHashes[$relativePath]) {
            Fail "release payload hash mismatch: $relativePath"
        }
    }
    foreach ($path in @($gateway, $managerCli, $runtimeCli, $observabilityCli)) {
        Assert-X64Pe $path
    }
    Assert-X64Elf $daemon
    Pass "native x64 gateway/CLIs and Linux x86-64 daemon match the v0.1.4 package"

    $managerHelp = @(& $managerCli help 2>&1) -join "`n"
    $runtimeHelp = @(& $runtimeCli --sandbox-id preflight-only help 2>&1) -join "`n"
    $observabilityHelp = @(& $observabilityCli help 2>&1) -join "`n"
    foreach ($operation in @("list_docker_images", "create_sandbox", "destroy_sandbox")) {
        if ($managerHelp -notmatch "(?m)\b$operation\b") {
            Fail "manager CLI does not expose $operation"
        }
    }
    foreach ($operation in @("exec_command", "file_read", "file_write", "file_edit")) {
        if ($runtimeHelp -notmatch "(?m)\b$operation\b") {
            Fail "runtime CLI does not expose $operation"
        }
    }
    if ($observabilityHelp -notmatch "(?m)\bsnapshot\b") {
        Fail "observability CLI does not expose snapshot"
    }
    Pass "native product CLI catalogs expose every smoke operation"

    $dockerRecord = (& docker info --format "{{.ServerVersion}}|{{.OSType}}|{{.Architecture}}|{{.Driver}}|{{.CgroupVersion}}|{{.OperatingSystem}}").Trim()
    if ($LASTEXITCODE -ne 0) {
        Fail "Docker Desktop engine is unreachable"
    }
    $dockerFields = $dockerRecord.Split("|")
    if (
        $dockerFields.Count -ne 6 -or
        $dockerFields[0] -ne $expectedDockerVersion -or
        $dockerFields[1] -ne "linux" -or
        $dockerFields[2] -notin @("x86_64", "amd64") -or
        $dockerFields[3] -ne "overlayfs" -or
        $dockerFields[4] -ne "2" -or
        $dockerFields[5] -notmatch "Docker Desktop"
    ) {
        Fail "Docker Desktop engine does not match the selected contract: $dockerRecord"
    }
    Pass "Docker Desktop $expectedDockerVersion provides Linux AMD64, overlayfs, and cgroup v2"

    if ($ImageReference -notmatch '@sha256:[0-9a-f]{64}$') {
        Fail "sandbox image is not pinned by a full digest"
    }
    $image = @(& docker image inspect $ImageReference | ConvertFrom-Json)[0]
    if ($image.Os -ne "linux" -or $image.Architecture -notin @("amd64", "x86_64")) {
        Fail "pinned image is not Linux AMD64"
    }
    if ($image.RepoDigests -notcontains "ubuntu@$($ImageReference.Split('@')[1])") {
        Fail "local image RepoDigests do not contain the pinned manifest"
    }
    Pass "exact pinned Ubuntu sandbox image is present locally"

    $quotedArtifactDirectory = "'" + ($ArtifactDirectory -replace "'", "''") + "'"
    $quotedRegistry = "'" + ($gatewayRegistry -replace "'", "''") + "'"
    $quotedDaemon = "'" + ($daemon -replace "'", "''") + "'"
    $quotedDaemonConfig = "'" + ($templateConfig -replace "'", "''") + "'"
    $config = Get-Content -Raw -LiteralPath $templateConfig
    $managerHeader = @"
manager:
  registry_path: $quotedRegistry
  workspace_roots:
    - $quotedArtifactDirectory
"@
    $config = [regex]::Replace($config, "(?m)^manager:\r?\n", "$managerHeader`r`n")
    $config = [regex]::Replace(
        $config,
        "(?m)^    daemon_binary_path:.*$",
        "    daemon_binary_path: $quotedDaemon"
    )
    $config = [regex]::Replace(
        $config,
        "(?m)^    daemon_config_yaml_path:.*$",
        "    daemon_config_yaml_path: $quotedDaemonConfig"
    )
    $config = [regex]::Replace(
        $config,
        "(?m)^    gateway_instance_id:.*$",
        "    gateway_instance_id: $gatewayInstanceId"
    )
    [System.IO.File]::WriteAllText(
        $gatewayConfig,
        $config,
        [System.Text.UTF8Encoding]::new($false)
    )

    $env:EOS_SHARED_BASE_CACHE = Join-Path $ArtifactDirectory "shared-base-cache"
    $gatewayArguments = @(
        "serve",
        "--backend", "docker",
        "--config-yaml", $gatewayConfig,
        "--gateway-socket", $gatewaySocket,
        "--auth-token", $authToken,
        "--pid-file", $gatewayPidFile
    )
    $argumentLine = ($gatewayArguments | ForEach-Object { Quote-ProcessArgument $_ }) -join " "
    $gatewayProcess = Start-Process `
        -FilePath $gateway `
        -ArgumentList $argumentLine `
        -WorkingDirectory $PackageRoot `
        -RedirectStandardOutput $gatewayStdout `
        -RedirectStandardError $gatewayStderr `
        -WindowStyle Hidden `
        -PassThru

    $ready = $false
    for ($attempt = 0; $attempt -lt 120; $attempt++) {
        if ($gatewayProcess.HasExited) {
            Fail "native Windows gateway exited during startup"
        }
        $readinessStderr = Join-Path $ArtifactDirectory "gateway-readiness.stderr"
        $savedErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $readinessOutput = @(
                & $managerCli `
                    --gateway-socket $gatewaySocket `
                    --gateway-auth-token $authToken `
                    list_docker_images 2> $readinessStderr
            )
            $readinessExitCode = $LASTEXITCODE
        } finally {
            $ErrorActionPreference = $savedErrorActionPreference
        }
        if ($readinessExitCode -eq 0) {
            ($readinessOutput -join [Environment]::NewLine) |
                Set-Content -LiteralPath (Join-Path $ArtifactDirectory "gateway-readiness.json") -Encoding utf8
            $ready = $true
            break
        }
        Start-Sleep -Milliseconds 250
    }
    if (-not $ready) {
        Fail "native Windows gateway did not become CLI-ready within 30 seconds"
    }
    if ((Get-Item -LiteralPath (Join-Path $ArtifactDirectory "gateway-readiness.stderr")).Length -ne 0) {
        Fail "final gateway readiness check emitted stderr"
    }
    Pass "native Windows gateway became ready for native product CLIs"

    for ($batch = 1; $batch -le 2; $batch++) {
        $batchLabel = "{0:D2}" -f $batch
        $workspace = Join-Path $ArtifactDirectory "cli-workspace-batch-$batchLabel"
        New-Item -ItemType Directory -Path (Join-Path $workspace "src") -Force | Out-Null
        Set-Content -LiteralPath (Join-Path $workspace "README.txt") -Value "CLI_ENV_WINDOWS_BATCH_$batchLabel fixture" -Encoding utf8
        Set-Content -LiteralPath (Join-Path $workspace "src\main.txt") -Value "initial fixture" -Encoding utf8

        $null = Invoke-ManagerCli "batch-$batchLabel-00-list-images" @("list_docker_images")
        $created = Invoke-ManagerCli "batch-$batchLabel-01-create-sandbox" @(
            "create_sandbox",
            "--image", $ImageReference,
            "--workspace-bind-root", $workspace
        )
        if (-not $created.id) {
            Fail "batch $batchLabel create_sandbox response has no sandbox ID"
        }
        $activeSandboxId = [string]$created.id
        $returnedWorkspace = [string]$created.workspace_root
        if ($returnedWorkspace.StartsWith("\\?\")) {
            $returnedWorkspace = $returnedWorkspace.Substring(4)
        }
        if (
            $created.state -ne "ready" -or
            -not [string]::Equals(
                [System.IO.Path]::GetFullPath($returnedWorkspace),
                [System.IO.Path]::GetFullPath($workspace),
                [System.StringComparison]::OrdinalIgnoreCase
            )
        ) {
            Fail "batch $batchLabel create_sandbox response failed strict validation"
        }

        $executed = Invoke-RuntimeCli "batch-$batchLabel-02-exec-command" $activeSandboxId @(
            "--request-id", "cli-env-windows-$batchLabel-exec",
            "exec_command",
            "--timeout-ms", "30000",
            'printf "CLI_ENV_EXEC_OK\n"; test -f README.txt; cat README.txt'
        )
        if (
            $executed.status -ne "ok" -or
            [int]$executed.exit_code -ne 0 -or
            ($executed | ConvertTo-Json -Depth 100) -notmatch "CLI_ENV_EXEC_OK" -or
            ($executed | ConvertTo-Json -Depth 100) -notmatch "CLI_ENV_WINDOWS_BATCH_$batchLabel"
        ) {
            Fail "batch $batchLabel exec_command response failed strict validation"
        }

        $null = Invoke-RuntimeCli "batch-$batchLabel-03-file-write" $activeSandboxId @(
            "--request-id", "cli-env-windows-$batchLabel-write",
            "file_write",
            "--path", "cli-smoke.txt",
            "--content", "CLI_ENV_FILE_ALPHA"
        )
        $readAlpha = Invoke-RuntimeCli "batch-$batchLabel-04-file-read-alpha" $activeSandboxId @(
            "--request-id", "cli-env-windows-$batchLabel-read-alpha",
            "file_read",
            "--path", "cli-smoke.txt",
            "--limit", "10"
        )
        if (($readAlpha | ConvertTo-Json -Depth 100) -notmatch "CLI_ENV_FILE_ALPHA") {
            Fail "batch $batchLabel first file_read failed correctness"
        }
        $null = Invoke-RuntimeCli "batch-$batchLabel-05-file-edit" $activeSandboxId @(
            "--request-id", "cli-env-windows-$batchLabel-edit",
            "file_edit",
            "--path", "cli-smoke.txt",
            "--edits", '[{\"old_string\":\"ALPHA\",\"new_string\":\"OMEGA\"}]'
        )
        $readOmega = Invoke-RuntimeCli "batch-$batchLabel-06-file-read-omega" $activeSandboxId @(
            "--request-id", "cli-env-windows-$batchLabel-read-omega",
            "file_read",
            "--path", "cli-smoke.txt",
            "--limit", "10"
        )
        $readOmegaText = $readOmega | ConvertTo-Json -Depth 100
        if ($readOmegaText -notmatch "CLI_ENV_FILE_OMEGA" -or $readOmegaText -match "CLI_ENV_FILE_ALPHA") {
            Fail "batch $batchLabel second file_read failed correctness"
        }

        $snapshot = Invoke-ObservabilityCli "batch-$batchLabel-07-observability-snapshot" $activeSandboxId
        if (($snapshot | ConvertTo-Json -Depth 100) -notmatch [regex]::Escape($activeSandboxId)) {
            Fail "batch $batchLabel snapshot does not identify the sandbox"
        }
        $destroyed = Invoke-ManagerCli "batch-$batchLabel-08-destroy-sandbox" @(
            "destroy_sandbox",
            "--sandbox-id", $activeSandboxId
        )
        if ($destroyed.id -ne $activeSandboxId) {
            Fail "batch $batchLabel destroy_sandbox response failed strict validation"
        }
        $destroyedSandboxId = $activeSandboxId
        $activeSandboxId = $null
        $listed = Invoke-ManagerCli "batch-$batchLabel-09-list-sandboxes-after" @("list_sandboxes")
        if (($listed | ConvertTo-Json -Depth 100) -match [regex]::Escape($destroyedSandboxId)) {
            Fail "batch $batchLabel sandbox remains in manager listing after destroy"
        }
        $batchSandboxIds.Add($destroyedSandboxId)
        Pass "product-CLI batch $batchLabel completed and destroyed sandbox $destroyedSandboxId"
    }
} catch {
    $primaryError = $_
} finally {
    Cleanup-Qualification
}

if ($primaryError) {
    Fail "qualification failed: $($primaryError.Exception.Message)"
}
if ($cleanupErrors.Count -ne 0) {
    Fail "qualification cleanup failed: $($cleanupErrors -join '; ')"
}

$afterState = @(Get-OwnedState)
$afterState | Set-Content -LiteralPath $afterStatePath -Encoding utf8
$beforeStateText = @(Get-Content -LiteralPath $beforeStatePath -ErrorAction SilentlyContinue)
$afterStateText = @(Get-Content -LiteralPath $afterStatePath -ErrorAction SilentlyContinue)
$stateDifference = Compare-Object -ReferenceObject $beforeStateText -DifferenceObject $afterStateText
$stateDifference |
    Out-String |
    Set-Content -LiteralPath (Join-Path $ArtifactDirectory "owned-state-diff.txt") -Encoding utf8
if ($stateDifference) {
    Fail "global EOS-owned Docker/process baseline changed"
}

$nonemptyCliStderr = @(
    Get-ChildItem -File -LiteralPath $ArtifactDirectory -Filter "batch-*.stderr" |
        Where-Object { $_.Length -ne 0 }
)
if ($nonemptyCliStderr.Count -ne 0) {
    Fail "one or more native product CLI stderr files are nonempty"
}

$gatewayLogText = @(
    Get-Content -Raw -LiteralPath $gatewayStdout -ErrorAction SilentlyContinue
    Get-Content -Raw -LiteralPath $gatewayStderr -ErrorAction SilentlyContinue
) -join "`n"
if ($gatewayLogText -match '(?im)"level"\s*:\s*"(warn|error)"|(^|[^a-z])(WARN|ERROR|PANIC)([^a-z]|$)') {
    Fail "native gateway log contains a warning, error, or panic"
}

$tokenLeakFiles = [System.Collections.Generic.List[string]]::new()
Get-ChildItem -File -LiteralPath $ArtifactDirectory |
    Where-Object { $_.Extension -in @(".txt", ".json", ".log", ".stderr", ".stdout", ".yml") } |
    ForEach-Object {
        $content = Get-Content -Raw -LiteralPath $_.FullName -ErrorAction SilentlyContinue
        if ($content -and $content.Contains($authToken)) {
            $redacted = $content.Replace($authToken, "[REDACTED]")
            Set-Content -LiteralPath $_.FullName -Value $redacted -Encoding utf8
            $tokenLeakFiles.Add($_.FullName)
        }
    }
if ($tokenLeakFiles.Count -ne 0) {
    Fail "gateway authentication token appeared in archived output and was redacted"
}

$elapsedSeconds = [int][Math]::Ceiling(([DateTime]::UtcNow - $startedAt).TotalSeconds)
if ($elapsedSeconds -gt $MaximumSeconds) {
    Fail "qualification exceeded the $MaximumSeconds-second budget"
}

$operationSequence = @(
    "list_docker_images",
    "create_sandbox",
    "exec_command",
    "file_write",
    "file_read",
    "file_edit",
    "file_read",
    "snapshot",
    "destroy_sandbox",
    "list_sandboxes"
)
$summary = [ordered]@{
    schema_version = 1
    qualification_target = "windows_docker_desktop"
    client_cohort = "product_cli"
    state = "completed"
    correctness = "pass"
    completed_batches = 2
    total_batches = 2
    operation_count = 20
    operation_sequence = $operationSequence
    warning_count = 0
    failure_count = 0
    cleanup = "pass"
    elapsed_seconds = $elapsedSeconds
    computer_name = $ExpectedComputerName
    windows_build = $buildNumber
    docker_version = $expectedDockerVersion
    docker_engine = "linux/amd64"
    docker_storage_driver = "overlayfs"
    docker_cgroup_version = "2"
    image_reference = $ImageReference
    product_commit = $expectedProductCommit
    release_archive_sha256 = $expectedReleaseArchiveSha256
    gateway_instance_id = $gatewayInstanceId
    sandbox_ids = @($batchSandboxIds)
    batches = @(
        for ($index = 0; $index -lt $batchSandboxIds.Count; $index++) {
            [ordered]@{
                batch_index = $index + 1
                sandbox_id = $batchSandboxIds[$index]
                state = "completed"
                correctness = "pass"
                operation_count = 10
                cleanup = "pass"
            }
        }
    )
    artifact_sha256 = $expectedHashes
}
$summary |
    ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath $summaryPath -Encoding utf8

Pass "Windows Docker Desktop environment qualification completed"
Info "summary=$summaryPath"
Info "artifact_directory=$ArtifactDirectory"
Info "elapsed_seconds=$elapsedSeconds"
