# ============================================================================
# Script de Desinstalação do Agente de Monitoramento
# ============================================================================
# Remove o serviço do Windows instalado pelo script instalar_servico.ps1
# ============================================================================

# Verificar se está rodando como Administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERRO: Este script precisa ser executado como Administrador!" -ForegroundColor Red
    Write-Host "Clique com botão direito no PowerShell e selecione 'Executar como Administrador'" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Desinstalador do Agente de Monitoramento " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Configurações
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$SERVICE_NAME = "MonitoramentoAgente"
$NSSM_EXE = Join-Path $SCRIPT_DIR "nssm\nssm.exe"

# Verificar se NSSM existe
if (-not (Test-Path $NSSM_EXE)) {
    Write-Host "ERRO: NSSM nao encontrado em: $NSSM_EXE" -ForegroundColor Red
    Write-Host "O servico pode nao ter sido instalado com este script." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Tentando remover com 'sc delete'..." -ForegroundColor Yellow
    sc.exe delete $SERVICE_NAME
    pause
    exit 0
}

# Verificar se o serviço existe
$existingService = Get-Service -Name $SERVICE_NAME -ErrorAction SilentlyContinue
if (-not $existingService) {
    Write-Host "Servico '$SERVICE_NAME' nao encontrado!" -ForegroundColor Yellow
    Write-Host "O servico pode ja ter sido removido." -ForegroundColor Gray
    pause
    exit 0
}

Write-Host "Servico encontrado: $SERVICE_NAME" -ForegroundColor Green
Write-Host "Status: $($existingService.Status)" -ForegroundColor Gray
Write-Host ""

# Confirmar desinstalação
Write-Host "Deseja realmente desinstalar o servico? (S/N): " -ForegroundColor Yellow -NoNewline
$confirmacao = Read-Host
if ($confirmacao -ne "S" -and $confirmacao -ne "s") {
    Write-Host "Desinstalacao cancelada." -ForegroundColor Gray
    pause
    exit 0
}

Write-Host ""
Write-Host "[1/2] Parando servico..." -ForegroundColor Yellow
& $NSSM_EXE stop $SERVICE_NAME
Start-Sleep -Seconds 2

Write-Host "[2/2] Removendo servico..." -ForegroundColor Yellow
& $NSSM_EXE remove $SERVICE_NAME confirm

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  SERVICO REMOVIDO COM SUCESSO!            " -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "O servico '$SERVICE_NAME' foi desinstalado." -ForegroundColor Cyan
    Write-Host "Os arquivos do agente ainda estao em: $SCRIPT_DIR" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "ERRO ao remover servico!" -ForegroundColor Red
    Write-Host "Tente remover manualmente com: sc delete $SERVICE_NAME" -ForegroundColor Yellow
    Write-Host ""
}

pause
