# One-command deploy: build image -> push to ECR -> sam deploy.
# Run from the backend folder:  .\deploy.ps1
# Secrets are read from .env (never printed). The Gmail app password is read from NODEMAILER_PASS / EMAIL_HOST_PASSWORD.
param(
    [string]$LiteMode = 'true',
    [string]$MemoryMb = '512',
    [string]$FrontendOrigin = 'https://verif-ai-frontend.vercel.app',
    [string]$BudgetEmail = 'kenchitomeldan@gmail.com',
    [string]$Region = 'us-east-1'
)
$ErrorActionPreference = 'Continue'
$env:Path += ";C:\Program Files\Docker\Docker\resources\bin;C:\Program Files\Amazon\AWSCLIV2;C:\Program Files\Amazon\AWSSAMCLI\bin"
$env:SAM_CLI_TELEMETRY = '0'
Set-Location $PSScriptRoot

function Get-EnvVal($k) {
    $l = Select-String -Path .env -Pattern "^$k=(.*)$" | Select-Object -First 1
    if (-not $l) { return '' }
    $v = $l.Matches[0].Groups[1].Value.Trim()
    if ($v.Length -ge 2 -and (($v[0] -eq '"' -and $v[-1] -eq '"') -or ($v[0] -eq "'" -and $v[-1] -eq "'"))) { $v = $v.Substring(1, $v.Length - 2) }
    $v
}

$account = aws sts get-caller-identity --query Account --output text
$repo = "$account.dkr.ecr.$Region.amazonaws.com/verfai-backend"
$tag = 'v' + (Get-Date -Format 'yyyyMMdd-HHmmss')
$image = "${repo}:$tag"

aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$account.dkr.ecr.$Region.amazonaws.com" | Out-Null
docker build --provenance=false -t $image .
if ($LASTEXITCODE -ne 0) { throw 'docker build failed' }
docker push $image
if ($LASTEXITCODE -ne 0) { throw 'docker push failed' }

$emailPass = Get-EnvVal 'EMAIL_HOST_PASSWORD'
if (-not $emailPass) { $emailPass = Get-EnvVal 'NODEMAILER_PASS' }
$emailUser = Get-EnvVal 'EMAIL_HOST_USER'
if (-not $emailUser) { $emailUser = Get-EnvVal 'NODEMAILER_USER' }

$params = @(
    "ImageUri=$image", "FrontendOrigin=$FrontendOrigin", "BudgetEmail=$BudgetEmail",
    "LiteMode=$LiteMode", "MemoryMb=$MemoryMb",
    "DjangoSecretKey=$(Get-EnvVal 'DJANGO_SECRET_KEY')", "JwtSecretKey=$(Get-EnvVal 'JWT_SECRET_KEY')",
    "MongoUri=$(Get-EnvVal 'MONGODB_URI')", "GeminiApiKey=$(Get-EnvVal 'GEMINI_API_KEY')",
    "EmailUser=$emailUser", "EmailAppPassword=$emailPass"
) | ForEach-Object { $i = $_.IndexOf('='); $_.Substring(0, $i) + '="' + $_.Substring($i + 1) + '"' }

sam deploy --template-file template.yaml --stack-name verfai --region $Region --capabilities CAPABILITY_IAM `
    --resolve-s3 --image-repository $repo --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides @params
if ($LASTEXITCODE -ne 0) { throw 'sam deploy failed' }
Write-Host "Deployed $tag"
