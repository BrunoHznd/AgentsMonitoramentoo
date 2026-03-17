#!/usr/bin/env python3
"""
Login usando cookies exportados do navegador
"""

import os
import json
from pathlib import Path
from instagrapi import Client

cookies_file = Path(__file__).parent / "cookies.json"

if not cookies_file.exists():
    print("❌ Arquivo cookies.json não encontrado!")
    print()
    print("Siga os passos:")
    print("1. Faça login no Instagram pelo navegador")
    print("2. Instale extensão EditThisCookie ou Cookie-Editor")
    print("3. Exporte os cookies")
    print("4. Salve em: agents/instagram/cookies.json")
    print()
    print("Veja: SOLUCAO_ALTERNATIVA.md")
    exit(1)

try:
    with open(cookies_file) as f:
        cookies_data = json.load(f)
    
    client = Client()
    
    # Converter cookies do formato do navegador para o formato do instagrapi
    cookies_dict = {}
    for cookie in cookies_data:
        if isinstance(cookie, dict) and "name" in cookie and "value" in cookie:
            cookies_dict[cookie["name"]] = cookie["value"]
    
    # Extrair cookies importantes
    sessionid = cookies_dict.get("sessionid")
    csrftoken = cookies_dict.get("csrftoken")
    ds_user_id = cookies_dict.get("ds_user_id")
    
    if not sessionid:
        print("❌ Cookie 'sessionid' não encontrado!")
        print("   Faça login novamente no navegador e exporte cookies novos")
        exit(1)
    
    print("🔄 Carregando cookies...")
    
    # Configurar cookies manualmente
    client.set_settings({
        "cookies": cookies_dict,
        "user_id": ds_user_id if ds_user_id else None
    })
    
    print("✅ Cookies carregados!")
    
    # Testar se está logado
    try:
        user_id = client.user_id
        if not user_id and ds_user_id:
            user_id = int(ds_user_id)
            client.user_id = user_id
        
        if user_id:
            user_info = client.user_info(user_id)
            print(f"✅ Logado como: @{user_info.username}")
            print(f"📝 Nome: {user_info.full_name}")
            print(f"🆔 User ID: {user_id}")
            
            # Salvar sessão
            client.dump_settings("session.json")
            print("💾 Sessão salva em session.json!")
            print()
            print("🎉 Agora você pode usar o simple_test.py normalmente!")
        else:
            print("❌ Não foi possível obter user_id dos cookies")
            print("   Tente fazer login novamente no navegador")
    except Exception as test_error:
        print(f"⚠️ Erro ao testar login: {test_error}")
        print("   Mas os cookies foram salvos. Tente executar simple_test.py")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    print()
    print("Verifique se o arquivo cookies.json está no formato correto")
