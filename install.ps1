# Installer mandiri: tidak butuh Python/conda/ffmpeg yang sudah ada di sistem.
# Semua (Miniforge, env, repo, model) masuk ke folder ini -> hapus folder = bersih total.
# Jalankan:  powershell -ExecutionPolicy Bypass -File .\install.ps1
$ErrorActionPreference = "Stop"
$Root    = $PSScriptRoot
$Tools   = Join-Path $Root "tools"
$Conda   = Join-Path $Tools "miniforge"
$CondaExe= Join-Path $Conda "Scripts\conda.exe"
$Apps    = Join-Path $Root "apps"
$Envs    = Join-Path $Root "envs"

# Versi dikunci supaya hasil sama setelah install ulang
$FF_TAG    = "3.9.1"
$SVC_COMMIT= "51383efd921027683c89e5348211d93ff12ac2a8"

function Step($m) { Write-Host "`n=== $m ===" -ForegroundColor Cyan }
function Run($exe, $argv) { & $exe @argv; if ($LASTEXITCODE -ne 0) { throw "Gagal: $exe $($argv -join ' ')" } }

New-Item -ItemType Directory -Force $Tools, $Apps, $Envs | Out-Null

Step "1/6 Miniforge (conda lokal)"
if (-not (Test-Path $CondaExe)) {
    $inst = Join-Path $Tools "miniforge-installer.exe"
    Invoke-WebRequest "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe" -OutFile $inst
    Start-Process $inst -ArgumentList "/InstallationType=JustMe","/RegisterPython=0","/AddToPath=0","/S","/D=$Conda" -Wait
    Remove-Item $inst
}

Step "2/6 Clone FaceFusion & Seed-VC (versi terkunci)"
if (-not (Test-Path "$Apps\facefusion")) {
    Run git @("clone","--depth","1","--branch",$FF_TAG,"https://github.com/facefusion/facefusion.git","$Apps\facefusion")
}
if (-not (Test-Path "$Apps\seed-vc")) {
    Run git @("clone","https://github.com/Plachtaa/seed-vc.git","$Apps\seed-vc")
    Run git @("-C","$Apps\seed-vc","checkout",$SVC_COMMIT)
}

Step "3/6 Env FaceFusion (Python 3.12 + ffmpeg + CUDA runtime)"
if (-not (Test-Path "$Envs\facefusion\python.exe")) {
    Run $CondaExe @("create","-y","-p","$Envs\facefusion","-c","conda-forge","python=3.12","ffmpeg","cuda-runtime=12.9.1","cudnn=9.*")
}
Push-Location "$Apps\facefusion"
Run "$Envs\facefusion\python.exe" @("install.py","cuda@12","--skip-conda")
Pop-Location

Step "4/6 Env Seed-VC (Python 3.10 + PyTorch CUDA 12.1)"
if (-not (Test-Path "$Envs\seedvc\python.exe")) {
    Run $CondaExe @("create","-y","-p","$Envs\seedvc","-c","conda-forge","python=3.10")
}
$py = "$Envs\seedvc\python.exe"
Run $py @("-m","pip","install","torch==2.4.0","torchvision==0.19.0","torchaudio==2.4.0","--index-url","https://download.pytorch.org/whl/cu121")
Run $py @("-m","pip","install","-r","$Root\requirements-seedvc.txt")

Step "5/6 Download model (supaya run pertama tidak menunggu)"
Run $py @("$Root\run.py","--prefetch")

Step "6/6 Selesai"
Write-Host "Tes:  $Envs\facefusion\python.exe run.py --photo face.png --voice suara.wav --video video.mp4 --output hasil.mp4" -ForegroundColor Green
