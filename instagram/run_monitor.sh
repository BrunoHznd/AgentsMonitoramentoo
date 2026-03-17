#!/bin/bash
# Script para executar o monitor de bots do Instagram

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🤖 Instagram Bot Monitor"
echo "========================"
echo ""

# Verificar se .env existe
if [ ! -f "../../.env" ]; then
    echo "❌ Erro: Arquivo .env não encontrado!"
    echo "   Copie .env.example para .env e configure as variáveis."
    exit 1
fi

# Verificar se instagrapi está instalado
if ! python3 -c "import instagrapi" 2>/dev/null; then
    echo "❌ Erro: instagrapi não está instalado!"
    echo "   Execute: pip install instagrapi"
    exit 1
fi

# Carregar variáveis do .env
export $(grep -v '^#' ../../.env | xargs)

# Verificar variáveis obrigatórias
if [ -z "$INSTAGRAM_MONITOR_USERNAME" ] || [ -z "$INSTAGRAM_MONITOR_PASSWORD" ] || [ -z "$INSTAGRAM_BOT_USERNAME" ]; then
    echo "❌ Erro: Variáveis obrigatórias não configuradas!"
    echo ""
    echo "Configure no arquivo .env:"
    echo "  INSTAGRAM_MONITOR_USERNAME=sua_conta_teste"
    echo "  INSTAGRAM_MONITOR_PASSWORD=sua_senha"
    echo "  INSTAGRAM_BOT_USERNAME=nome_do_bot"
    exit 1
fi

echo "✅ Configuração validada"
echo ""
echo "📋 Configuração:"
echo "   Monitor: @$INSTAGRAM_MONITOR_USERNAME"
echo "   Bot alvo: @$INSTAGRAM_BOT_USERNAME"
echo "   Mensagem: ${INSTAGRAM_TEST_MESSAGE:-Bom dia}"
echo "   Loop: ${INSTAGRAM_MONITOR_LOOP:-false}"
echo ""

# Executar monitor
echo "🚀 Iniciando monitor..."
echo ""

python3 instagram_bot_monitor.py
