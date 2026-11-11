#Requires -Version 5.1
<#
AIWallet Release Lab — one-time GitHub publication, run on the owner's Windows PC.
Downloads the official GitHub CLI only if it is not installed; pins its SHA-256.
GitHub login happens ONLY in the official browser/device flow. Never copies a token,
password, cookie, or OTP into the repository, an output file, or ChatGPT.
#>
[CmdletBinding()]
param([switch]$NoRelease)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$Owner = 'muhammadzakyasshidqy-commits'
$RepoName = 'aiwallet-release-lab'
$RepoFull = "$Owner/$RepoName"
$Version = 'v0.9.0'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Assets = Join-Path $Root 'release-assets'
$Bundle = Join-Path $Assets 'AIWallet_ReleaseLab_v0.9.0.git.bundle'
$Source = Join-Path $Assets 'aiwallet-release-lab-v0.9.0.zip'
$Wheel = Join-Path $Assets 'aiwallet_release_lab-0.9.0-py3-none-any.whl'
$Zipapp = Join-Path $Assets 'releaselab-0.9.0.pyz'
$Checksums = Join-Path $Assets 'SHA256SUMS.txt'
$WorkRoot = Join-Path $env:LOCALAPPDATA 'AIWallet\GitHubPublisher'
$RepoDir = Join-Path $WorkRoot 'source-to-publish'
$ResultFile = Join-Path $Root 'PUBLISH_RESULT.json'
$GhVersion = '2.103.3'
$GhPackage = 'gh_2.103.3_windows_amd64.zip'
$GhUrl = 'https://github.com/cli/cli/releases/download/v2.103.3/gh_2.103.3_windows_amd64.zip'
$GhExpectedSha256 = '98d0cfa794721665d7973dd728c78aff7bd836d58f10f6d7a03568eccb0a22e0'

function Check-Exit([string]$Operation) {
  if ($LASTEXITCODE -ne 0) { throw "$Operation gagal (exit code $LASTEXITCODE). Tidak ada force-push yang dilakukan." }
}
function Portable-Gh {
  $installed = Get-Command 'gh.exe' -ErrorAction SilentlyContinue
  if ($null -ne $installed) { return $installed.Source }
  if (-not [Environment]::Is64BitOperatingSystem) { throw 'Paket GitHub CLI yang diverifikasi hanya untuk Windows x64.' }
  $cliRoot = Join-Path $WorkRoot 'GitHubCLI'
  $found = @(Get-ChildItem $cliRoot -Recurse -Filter 'gh.exe' -ErrorAction SilentlyContinue | Select-Object -First 1)
  if ($found.Count -gt 0) { return $found[0].FullName }
  New-Item -ItemType Directory -Path $cliRoot -Force | Out-Null
  $download = Join-Path $WorkRoot $GhPackage
  Write-Host 'Mengambil GitHub CLI resmi dan memverifikasi SHA-256…'
  Invoke-WebRequest -Uri $GhUrl -OutFile $download -UseBasicParsing -MaximumRedirection 6
  $actual = (Get-FileHash -Path $download -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actual -ne $GhExpectedSha256) {
    Remove-Item -LiteralPath $download -Force -ErrorAction SilentlyContinue
    throw "SHA-256 GitHub CLI tidak cocok. Instalasi dibatalkan."
  }
  Expand-Archive -LiteralPath $download -DestinationPath $cliRoot -Force
  Remove-Item -LiteralPath $download -Force -ErrorAction SilentlyContinue
  $found = @(Get-ChildItem $cliRoot -Recurse -Filter 'gh.exe' -ErrorAction SilentlyContinue | Select-Object -First 1)
  if ($found.Count -eq 0) { throw 'gh.exe tidak ditemukan dalam arsip resmi.' }
  return $found[0].FullName
}

Write-Host 'AIWallet Release Lab — Publikasi GitHub' -ForegroundColor Green
Write-Host 'Target:' $RepoFull '|' $Version
Write-Host 'GitHub login hanya melalui website resmi. Tidak ada biaya langganan.'
foreach ($file in @($Bundle,$Source,$Wheel,$Zipapp,$Checksums)) {
  if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "File paket tidak ada: $file" }
}
# Verify every source/release file against the checksums shipped in this archive.
# A mismatch must stop BEFORE login, repository creation or publication.
$Expected = @{}
foreach ($line in @(Get-Content -LiteralPath $Checksums)) {
  if ($line -match '^([a-fA-F0-9]{64})  (.+)$') {
    $Expected[$Matches[2]] = $Matches[1].ToLowerInvariant()
  }
}
foreach ($file in @($Bundle,$Source,$Wheel,$Zipapp)) {
  $name = Split-Path -Leaf $file
  if (-not $Expected.ContainsKey($name)) { throw "Checksum wajib tidak tersedia: $name" }
  $actual = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actual -ne $Expected[$name]) { throw "Checksum rilis tidak cocok: $name" }
}
Write-Host 'Empat artefak rilis cocok dengan SHA-256 paket.' -ForegroundColor Green
$gitCmd = Get-Command 'git.exe' -ErrorAction SilentlyContinue
if ($null -eq $gitCmd) { throw 'Git for Windows belum tersedia. Instal Git gratis dari https://git-scm.com/download/win lalu jalankan launcher ini lagi.' }
$Git = $gitCmd.Source
New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null
$Gh = Portable-Gh
& $Gh --version | Select-Object -First 1
Check-Exit 'GitHub CLI'

# Only the user's GitHub CLI and credential manager handle the OAuth token.
& $Gh auth status --hostname github.com *> $null
if ($LASTEXITCODE -ne 0) {
  Write-Host ''
  Write-Host 'Masuk ke GitHub pada browser yang terbuka. Kode hanya untuk github.com/login/device.' -ForegroundColor Yellow
  Write-Host 'Tekan Enter bila GitHub CLI meminta konfirmasi pembukaan browser.'
  & $Gh auth login --hostname github.com --git-protocol https --scopes 'repo,workflow' --web --clipboard
  Check-Exit 'GitHub login'
}
$LoggedIn = (& $Gh api user --jq '.login' | Out-String).Trim()
Check-Exit 'Identifikasi akun GitHub'
if ($LoggedIn -cne $Owner) {
  throw "Akun GitHub aktif '$LoggedIn', bukan '$Owner'. Ganti akun pada GitHub CLI lalu jalankan kembali."
}
Write-Host "GitHub tervalidasi: $LoggedIn" -ForegroundColor Green

# Clone a bundled, fixed-source repository; never touch the user's other repos.
if (Test-Path -LiteralPath $RepoDir) {
  $saved = Join-Path $RepoDir '.git'
  if (-not (Test-Path $saved)) { throw 'Folder kerja sudah ada tetapi bukan repositori Git; tidak ditimpa.' }
  $head = (& $Git -C $RepoDir rev-parse --abbrev-ref HEAD | Out-String).Trim()
  Check-Exit 'Periksa checkout sebelumnya'
  if ($head -ne 'main') { throw 'Checkout tidak berada pada branch main. Tidak diubah.' }
  $existingTag = (& $Git -C $RepoDir tag --list $Version | Out-String).Trim()
  if ($existingTag -ne $Version) { throw 'Checkout lokal bukan versi yang diharapkan. Tidak ditimpa.' }
} else {
  & $Git clone --quiet -- $Bundle $RepoDir
  Check-Exit 'Impor bundle sumber Git'
}
& $Git -C $RepoDir bundle verify $Bundle *> $null
Check-Exit 'Verifikasi Git bundle'
& $Git -C $RepoDir rev-parse --verify "refs/tags/$Version" *> $null
Check-Exit 'Verifikasi tag rilis'
$dirty = (& $Git -C $RepoDir status --porcelain | Out-String).Trim()
Check-Exit 'Verifikasi working tree'
if ($dirty.Length -gt 0) { throw 'Working tree berisi perubahan yang tidak dikenal. Tidak akan dipublikasikan.' }

$Remote = "https://github.com/$RepoFull.git"
& $Git -C $RepoDir remote set-url origin $Remote
Check-Exit 'Menetapkan target repositori'
& $Gh auth setup-git --hostname github.com
Check-Exit 'Menyiapkan credential helper GitHub CLI'

& $Gh repo view $RepoFull --json 'nameWithOwner' --jq '.nameWithOwner' *> $null
if ($LASTEXITCODE -ne 0) {
  Write-Host 'Membuat repositori GitHub PUBLIC khusus Release Lab.'
  & $Gh repo create $RepoFull --public --description 'Open-source local-first video export QC, editorial review and release gates' --disable-wiki
  Check-Exit 'Membuat repositori GitHub'
}
# Never overwrite existing remote history or bypass protection.
$ExistingMain = (& $Git -C $RepoDir ls-remote --heads origin main | Out-String).Trim()
Check-Exit 'Periksa remote main'
$LocalMain = (& $Git -C $RepoDir rev-parse HEAD | Out-String).Trim()
Check-Exit 'Baca local main'
if ($ExistingMain.Length -gt 0 -and (-not $ExistingMain.StartsWith($LocalMain))) {
  throw 'Target main sudah memiliki commit yang berbeda. Tidak akan force-push/menimpa; pemeriksaan manual diperlukan.'
}
Write-Host 'Mengunggah source dan riwayat Git…'
& $Git -C $RepoDir push --set-upstream origin main
Check-Exit 'Git push main'
& $Git -C $RepoDir push origin --tags
Check-Exit 'Git push tags'

$RemoteHead = (& $Gh api "repos/$RepoFull/commits/main" --jq '.sha' | Out-String).Trim()
Check-Exit 'Verifikasi commit publik'
if ($RemoteHead -ne $LocalMain) { throw 'GitHub main tidak sesuai dengan sumber bundle. Tidak dapat dinyatakan berhasil.' }
$ReleaseLink = "https://github.com/$RepoFull/releases/tag/$Version"
$existingRelease = (& $Gh release view $Version --repo $RepoFull --json url --jq '.url' 2>$null | Out-String).Trim()
if ($NoRelease) { Write-Host 'GitHub Release dilewati oleh opsi NoRelease.' }
elseif ($existingRelease.Length -gt 0) { $ReleaseLink=$existingRelease; Write-Host 'GitHub Release sudah ada. Tidak diduplikasi.' }
else {
  Write-Host 'Membuat GitHub Release dengan berkas dan checksum…'
  & $Gh release create $Version $Source $Wheel $Zipapp $Checksums --repo $RepoFull --verify-tag --title 'AIWallet Release Lab v0.9.0' --notes 'Local-first Apache-2.0 video export QC. Free self-hosted core; optional customer-managed cloud interest has separate, not-yet-active billing. No paid license or automatic customer charge.'
  Check-Exit 'GitHub Release'
}

# Verify remote assets + CI status without assuming the tests already passed.
$releases = @(& $Gh release view $Version --repo $RepoFull --json assets --jq '.assets[].name' 2>$null)
$missing = @($Source,$Wheel,$Zipapp,$Checksums | ForEach-Object { Split-Path $_ -Leaf } | Where-Object { $_ -notin $releases })
if (-not $NoRelease -and $missing.Count -gt 0) { throw 'GitHub Release ada, tetapi aset belum lengkap: '+($missing -join ', ') }
$CI = 'pending_or_unverified'; $CIUrl = ''
for ($attempt=0; $attempt -lt 24; $attempt++) {
  $runsRaw=(& $Gh run list --repo $RepoFull --workflow 'ci.yml' --limit 5 --json 'status,conclusion,url,headSha' 2>$null | Out-String).Trim()
  if ($LASTEXITCODE -eq 0 -and $runsRaw.StartsWith('[')) {
    $runs=@(ConvertFrom-Json $runsRaw | Where-Object { $_.headSha -eq $LocalMain })
    if ($runs.Count -gt 0) {
      $CIUrl=$runs[0].url
      if ($runs[0].status -eq 'completed') {
        $CI=if($runs[0].conclusion -eq 'success'){'passed'}else{'failed'}
        break
      }
    }
  }
  Start-Sleep -Seconds 10
}
$receipt=[ordered]@{
  product='AIWallet Release Lab'; version=$Version; owner=$Owner;
  repo="https://github.com/$RepoFull"; release=$ReleaseLink;
  main_sha=$LocalMain; ci_status=$CI; ci_url=$CIUrl;
  paid_subscription_purchased_by_owner=$false;
  github_permissions='user-authorized CLI web login';
  published_at_utc=[DateTime]::UtcNow.ToString('o')
}
$receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ResultFile -Encoding UTF8
Write-Host ''
Write-Host 'PUBLIKASI REPO BERHASIL:' "https://github.com/$RepoFull" -ForegroundColor Green
Write-Host 'CI STATUS:' $CI
Write-Host 'Bukti non-rahasia:' $ResultFile
Start-Process "https://github.com/$RepoFull"
if ($CI -eq 'failed') { throw 'Repositori sudah terbit tetapi pengujian Actions gagal. Perbaiki CI sebelum menyatakan rilis lulus.' }
