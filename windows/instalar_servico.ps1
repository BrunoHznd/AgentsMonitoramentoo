# ============================================================================
# Script de Instalação do Agente de Monitoramento como Serviço do Windows
# ============================================================================
# Este script instala o agente Python como um serviço do Windows usando NSSM
# O serviço iniciará automaticamente quando o computador ligar
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
Write-Host "  Instalador do Agente de Monitoramento    " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Configurações
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$SERVICE_NAME = "MonitoramentoAgente"
$SERVICE_DISPLAY_NAME = "Agente de Monitoramento de Cameras"
$SERVICE_DESCRIPTION = "Monitora cameras IP e envia relatorios para o servidor central"
$PYTHON_SCRIPT = Join-Path $SCRIPT_DIR "agent.py"
$NSSM_DIR = Join-Path $SCRIPT_DIR "nssm"
$NSSM_EXE = Join-Path $NSSM_DIR "nssm.exe"

# Detectar arquitetura do sistema (32 ou 64 bits)
if ([Environment]::Is64BitOperatingSystem) {
    $NSSM_URL = "https://nssm.cc/release/nssm-2.24.zip"
    $ARCH = "win64"
} else {
    $NSSM_URL = "https://nssm.cc/release/nssm-2.24.zip"
    $ARCH = "win32"
}

Write-Host "[1/6] Verificando Python..." -ForegroundColor Yellow
# Encontrar Python
$pythonCmd = $null
$pythonPaths = @("python", "python3", "py")
foreach ($cmd in $pythonPaths) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = (Get-Command $cmd).Source
            Write-Host "      Python encontrado: $pythonCmd" -ForegroundColor Green
            Write-Host "      Versao: $version" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-Host "ERRO: Python nao encontrado!" -ForegroundColor Red
    Write-Host "Instale Python 3.7+ de https://www.python.org/downloads/" -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar se agent.py existe
if (-not (Test-Path $PYTHON_SCRIPT)) {
    Write-Host "ERRO: agent.py nao encontrado em: $PYTHON_SCRIPT" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[2/6] Baixando NSSM (Non-Sucking Service Manager)..." -ForegroundColor Yellow
# Baixar NSSM se não existir
if (-not (Test-Path $NSSM_EXE)) {
    $NSSM_ZIP = Join-Path $env:TEMP "nssm.zip"
    try {
        Write-Host "      Baixando de: $NSSM_URL" -ForegroundColor Gray
        Invoke-WebRequest -Uri $NSSM_URL -OutFile $NSSM_ZIP -UseBasicParsing
        
        Write-Host "      Extraindo..." -ForegroundColor Gray
        Expand-Archive -Path $NSSM_ZIP -DestinationPath $env:TEMP -Force
        
        # Copiar nssm.exe correto para o diretório do script
        New-Item -ItemType Directory -Force -Path $NSSM_DIR | Out-Null
        Copy-Item -Path "$env:TEMP\nssm-2.24\$ARCH\nssm.exe" -Destination $NSSM_EXE -Force
        
        Remove-Item $NSSM_ZIP -Force
        Write-Host "      NSSM baixado com sucesso!" -ForegroundColor Green
    } catch {
        Write-Host "ERRO ao baixar NSSM: $_" -ForegroundColor Red
        pause
        exit 1
    }
} else {
    Write-Host "      NSSM ja existe!" -ForegroundColor Green
}

Write-Host "[3/6] Verificando servico existente..." -ForegroundColor Yellow
# Verificar se o serviço já existe
$existingService = Get-Service -Name $SERVICE_NAME -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "      Servico '$SERVICE_NAME' ja existe!" -ForegroundColor Yellow
    Write-Host "      Parando servico..." -ForegroundColor Gray
    & $NSSM_EXE stop $SERVICE_NAME
    Start-Sleep -Seconds 2
    
    Write-Host "      Removendo servico antigo..." -ForegroundColor Gray
    & $NSSM_EXE remove $SERVICE_NAME confirm
    Start-Sleep -Seconds 2
}

Write-Host "[4/6] Instalando servico..." -ForegroundColor Yellow
# Instalar o serviço
& $NSSM_EXE install $SERVICE_NAME $pythonCmd $PYTHON_SCRIPT

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO ao instalar servico!" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[5/6] Configurando servico..." -ForegroundColor Yellow
# Configurar o serviço
& $NSSM_EXE set $SERVICE_NAME DisplayName $SERVICE_DISPLAY_NAME
& $NSSM_EXE set $SERVICE_NAME Description $SERVICE_DESCRIPTION
& $NSSM_EXE set $SERVICE_NAME Start SERVICE_AUTO_START
& $NSSM_EXE set $SERVICE_NAME AppDirectory $SCRIPT_DIR
& $NSSM_EXE set $SERVICE_NAME AppStdout "$SCRIPT_DIR\agent_log.txt"
& $NSSM_EXE set $SERVICE_NAME AppStderr "$SCRIPT_DIR\agent_error.txt"
& $NSSM_EXE set $SERVICE_NAME AppRotateFiles 1
& $NSSM_EXE set $SERVICE_NAME AppRotateBytes 1048576  # 1MB

Write-Host "[6/6] Iniciando servico..." -ForegroundColor Yellow
# Iniciar o serviço
& $NSSM_EXE start $SERVICE_NAME

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  INSTALACAO CONCLUIDA COM SUCESSO!        " -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Servico instalado: $SERVICE_NAME" -ForegroundColor Cyan
    Write-Host "Nome de exibicao: $SERVICE_DISPLAY_NAME" -ForegroundColor Cyan
    Write-Host "Status: Rodando" -ForegroundColor Green
    Write-Host "Inicio automatico: Sim" -ForegroundColor Green
    Write-Host ""
    Write-Host "Logs disponiveis em:" -ForegroundColor Yellow
    Write-Host "  - $SCRIPT_DIR\agent_log.txt" -ForegroundColor Gray
    Write-Host "  - $SCRIPT_DIR\agent_error.txt" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Comandos uteis:" -ForegroundColor Yellow
    Write-Host "  Ver status:   sc query $SERVICE_NAME" -ForegroundColor Gray
    Write-Host "  Parar:        sc stop $SERVICE_NAME" -ForegroundColor Gray
    Write-Host "  Iniciar:      sc start $SERVICE_NAME" -ForegroundColor Gray
    Write-Host "  Desinstalar:  .\desinstalar_servico.ps1" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "ERRO ao iniciar servico!" -ForegroundColor Red
    Write-Host "Verifique os logs em: $SCRIPT_DIR" -ForegroundColor Yellow
}

pause
