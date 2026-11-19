<#
.SYNOPSIS
  Applies the AKS Argo CD Application with real secrets injected (nothing secret goes to disk or Git).

.DESCRIPTION
  Reads argocd/application-aks.yaml, replaces the SECRETS-PLACEHOLDER line with Helm parameters
  built from values you type in, and pipes the result straight into `kubectl apply`.
  The secrets end up only inside the Application object in the AKS cluster.

  Allowed characters in passwords / secret key: letters, digits, "_" and "-" (they are used
  inside a database URL and passed as Helm parameters, so symbols like @ : / , \ would break them).

.PARAMETER DryRun
  Print the YAML with secrets masked and exit. Applies nothing.
#>
param(
    [switch]$DryRun,
    [string]$AdminUsername,
    [string]$AdminPassword,
    [string]$PostgresPassword,
    [string]$SecretKey
)

$ErrorActionPreference = 'Stop'
$template = Join-Path $PSScriptRoot 'application-aks.yaml'
$pattern = '^[A-Za-z0-9_-]+$'

function Read-Secret([string]$prompt) {
    $s = Read-Host -Prompt $prompt -AsSecureString
    $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
    try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}

function New-RandomSecret([int]$length = 32) {
    $chars = [char[]](48..57 + 65..90 + 97..122)
    -join (1..$length | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
}

if (-not $AdminUsername)    { $AdminUsername = Read-Host -Prompt 'App admin username' }
if (-not $AdminPassword)    { $AdminPassword = Read-Secret 'App admin password (min 12 chars)' }
if (-not $PostgresPassword) {
    $PostgresPassword = Read-Secret 'Postgres password (min 12 chars, empty = generate a random one)'
    if (-not $PostgresPassword) { $PostgresPassword = New-RandomSecret; Write-Host 'Generated a random Postgres password.' }
}
if (-not $SecretKey) {
    $SecretKey = Read-Secret 'App SECRET_KEY (min 32 chars, empty = generate a random one)'
    if (-not $SecretKey) { $SecretKey = New-RandomSecret 48; Write-Host 'Generated a random SECRET_KEY.' }
}

foreach ($item in @(
        @{ n = 'admin username'; v = $AdminUsername; min = 3 },
        @{ n = 'admin password'; v = $AdminPassword; min = 12 },
        @{ n = 'postgres password'; v = $PostgresPassword; min = 12 },
        @{ n = 'secret key'; v = $SecretKey; min = 32 })) {
    if ($item.v.Length -lt $item.min -or $item.v -notmatch $pattern) {
        throw "Invalid $($item.n): use at least $($item.min) characters, only letters, digits, '_' and '-'."
    }
}

function Param-Block([bool]$mask) {
    $pairs = [ordered]@{
        'secrets.adminUsername' = $AdminUsername
        'secrets.adminPassword' = $AdminPassword
        'secrets.secretKey'     = $SecretKey
        'postgres.password'     = $PostgresPassword
    }
    $lines = @('      parameters:')
    foreach ($k in $pairs.Keys) {
        $val = if ($mask -and $k -ne 'secrets.adminUsername') { '********' } else { $pairs[$k] }
        $lines += "        - name: $k"
        $lines += "          value: `"$val`""
        $lines += '          forceString: true'
    }
    $lines -join "`n"
}

$yaml = Get-Content $template -Raw
if ($yaml -notmatch '(?m)^\s*# SECRETS-PLACEHOLDER.*$') { throw 'SECRETS-PLACEHOLDER line not found in application-aks.yaml' }

if ($DryRun) {
    Write-Host '--- DRY RUN (secrets masked, nothing applied) ---'
    $yaml -replace '(?m)^\s*# SECRETS-PLACEHOLDER.*$', (Param-Block $true)
    return
}

# Real apply: the YAML with secrets goes through the pipe only.
$real = $yaml -replace '(?m)^\s*# SECRETS-PLACEHOLDER.*$', (Param-Block $false)
$ctx = kubectl config current-context
if ($ctx -ne 'aks-todo') { throw "kubectl context is '$ctx', expected 'aks-todo'. Run: kubectl config use-context aks-todo" }
$real | kubectl apply -f -
Write-Host 'Applied. Watch it with: kubectl get applications -n argocd'
