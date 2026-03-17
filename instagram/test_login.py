#!/usr/bin/env python3
"""
Teste de login no Instagram para debug
"""

import os
from dotenv import load_dotenv
from instagrapi import Client

load_dotenv()

username = os.getenv("INSTAGRAM_MONITOR_USERNAME", "").strip()
password = os.getenv("INSTAGRAM_MONITOR_PASSWORD", "").strip()

print(f"Tentando login com:")
print(f"  Username: {username}")
print(f"  Password: {'*' * len(password)}")
print()

if not username or not password:
    print("❌ Username ou password não configurados no .env")
    exit(1)

# Remover @ se tiver
username = username.lstrip('@')

client = Client()
client.delay_range = [1, 3]

try:
    print("🔐 Tentando login...")
    client.login(username, password)
    print("✅ Login bem-sucedido!")
    
    # Salvar sessão
    session_file = "session.json"
    client.dump_settings(session_file)
    print(f"✅ Sessão salva em {session_file}")
    
    # Testar pegando info do usuário
    user_info = client.user_info_by_username(username)
    print(f"✅ Usuário: @{user_info.username} - {user_info.full_name}")
    
except Exception as e:
    print(f"❌ Erro no login: {e}")
    print()
    print("Possíveis causas:")
    print("  1. Senha incorreta")
    print("  2. 2FA ativado (desative ou use senha de app)")
    print("  3. Instagram bloqueou login de apps não oficiais")
    print("  4. Conta requer verificação")
    print()
    print("Tente:")
    print("  - Fazer login manual no app do Instagram")
    print("  - Desativar 2FA temporariamente")
    print("  - Usar uma conta diferente")
