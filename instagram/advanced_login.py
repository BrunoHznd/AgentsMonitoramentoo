#!/usr/bin/env python3
"""
Login avançado com configurações para evitar detecção
"""

import os
import time
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    TwoFactorRequired,
    BadPassword,
    PleaseWaitFewMinutes
)

load_dotenv()

username = os.getenv("INSTAGRAM_MONITOR_USERNAME", "").strip()
password = os.getenv("INSTAGRAM_MONITOR_PASSWORD", "").strip()

print(f"🔐 Tentando login avançado")
print(f"   Username: {username}")
print()

if not username or not password:
    print("❌ Configure INSTAGRAM_MONITOR_USERNAME e INSTAGRAM_MONITOR_PASSWORD no .env")
    exit(1)

# Remover @ se tiver
username = username.lstrip('@')

# Criar cliente com configurações mais realistas
client = Client()

# Configurar device settings (simular dispositivo real)
client.set_device({
    "app_version": "269.0.0.18.75",
    "android_version": 26,
    "android_release": "8.0.0",
    "dpi": "480dpi",
    "resolution": "1080x1920",
    "manufacturer": "Samsung",
    "device": "SM-G950F",
    "model": "Galaxy S8",
    "cpu": "samsungexynos8895",
    "version_code": "314665256"
})

# Delays mais humanos
client.delay_range = [1, 3]

session_file = "session.json"

try:
    # Remover sessão antiga
    if os.path.exists(session_file):
        os.remove(session_file)
        print("🗑️  Sessão antiga removida")
    
    print("⏳ Fazendo login (pode demorar 10-15 segundos)...")
    
    # Tentar login
    client.login(username, password)
    
    print("✅ Login bem-sucedido!")
    
    # Salvar sessão
    client.dump_settings(session_file)
    print(f"💾 Sessão salva em {session_file}")
    
    # Testar pegando info
    user_info = client.user_info_by_username(username)
    print(f"👤 Logado como: @{user_info.username}")
    print(f"📝 Nome: {user_info.full_name}")
    print(f"👥 Seguidores: {user_info.follower_count}")
    
except BadPassword:
    print("❌ Senha incorreta!")
    print("   Verifique a senha no .env")
    
except TwoFactorRequired:
    print("❌ 2FA está ativado!")
    print("   Desative a autenticação de dois fatores ou use senha de app")
    
except ChallengeRequired as e:
    print("❌ Instagram requer verificação!")
    print(f"   {e}")
    print()
    print("   Faça login manual no app/navegador e complete a verificação")
    
except PleaseWaitFewMinutes:
    print("❌ Instagram pediu para aguardar alguns minutos")
    print("   Muitas tentativas de login. Aguarde 15-30 minutos")
    
except Exception as e:
    error_msg = str(e)
    print(f"❌ Erro: {error_msg}")
    print()
    
    if "can't find an account" in error_msg.lower():
        print("💡 Possíveis soluções:")
        print("   1. Verifique se o username está correto (sem @)")
        print("   2. Tente fazer login manual no Instagram primeiro")
        print("   3. A conta pode estar suspensa ou desativada")
        print("   4. Use uma conta mais antiga (contas novas são bloqueadas)")
    elif "checkpoint" in error_msg.lower():
        print("💡 Instagram detectou atividade suspeita")
        print("   Faça login manual e complete a verificação")
    else:
        print("💡 Tente:")
        print("   - Aguardar alguns minutos")
        print("   - Fazer login manual no Instagram")
        print("   - Usar uma conta diferente")
