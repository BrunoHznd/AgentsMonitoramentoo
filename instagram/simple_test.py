#!/usr/bin/env python3
"""
Teste simples de bots do Instagram
Envia uma mensagem "Bom dia" e verifica se os bots respondem
Suporta múltiplos bots
"""

import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv

try:
    from instagrapi import Client
except ImportError:
    print("❌ Erro: instagrapi não instalado. Execute: pip install instagrapi")
    sys.exit(1)

load_dotenv()

# Timeout para aguardar resposta (em segundos)
RESPONSE_TIMEOUT = 30  # 30 segundos (maior que 5)

def test_single_bot(client, bot_username, timeout=RESPONSE_TIMEOUT):
    """Testa um bot específico"""
    try:
        # Buscar ID do bot
        user_id = client.user_id_from_username(bot_username)
        
        # Pegar última mensagem antes de enviar
        thread = client.direct_thread(user_id)
        last_msg_id = thread.messages[0].id if thread.messages else None
        
        # Enviar mensagem "Bom dia"
        start_time = time.time()
        client.direct_send("Bom dia", [user_id])
        
        # Aguardar resposta
        elapsed = 0
        while elapsed < timeout:
            time.sleep(2)  # Verificar a cada 2 segundos
            elapsed = time.time() - start_time
            
            # Verificar novas mensagens
            thread = client.direct_thread(user_id)
            
            if thread.messages:
                latest_msg = thread.messages[0]
                
                # Se é uma nova mensagem e não é nossa
                if latest_msg.id != last_msg_id and latest_msg.user_id != client.user_id:
                    response_time = round(elapsed, 1)
                    response_text = latest_msg.text or "[mídia]"
                    
                    return {
                        "bot_username": bot_username,
                        "ok": True,
                        "bot_working": True,
                        "response_time_sec": response_time,
                        "response_text": response_text[:100],
                        "message": f"✅ @{bot_username}: Respondeu em {response_time}s - {response_text[:50]}"
                    }
        
        # Timeout
        return {
            "bot_username": bot_username,
            "ok": True,
            "bot_working": False,
            "response_time_sec": None,
            "response_text": None,
            "message": f"⚠️ @{bot_username}: Não respondeu em {timeout}s"
        }
        
    except Exception as e:
        return {
            "bot_username": bot_username,
            "ok": False,
            "error": str(e),
            "message": f"❌ @{bot_username}: Erro - {str(e)}"
        }

def test_instagram_bots():
    """Testa múltiplos bots do Instagram"""
    
    # Configurações
    username_or_email = os.getenv("INSTAGRAM_MONITOR_USERNAME")
    password = os.getenv("INSTAGRAM_MONITOR_PASSWORD")
    
    # Suporta múltiplos bots separados por vírgula
    bot_usernames_str = os.getenv("INSTAGRAM_BOT_USERNAME", "")
    bot_usernames = [b.strip() for b in bot_usernames_str.split(",") if b.strip()]
    
    if not username_or_email or not password:
        return {
            "ok": False,
            "error": "Configuração incompleta. Verifique INSTAGRAM_MONITOR_USERNAME e INSTAGRAM_MONITOR_PASSWORD no .env"
        }
    
    if not bot_usernames:
        return {
            "ok": False,
            "error": "Nenhum bot configurado. Configure INSTAGRAM_BOT_USERNAME no .env (separe múltiplos bots por vírgula)"
        }
    
    try:
        # Login
        client = Client()
        client.delay_range = [1, 3]
        
        # Tentar carregar sessão
        session_file = os.path.join(os.path.dirname(__file__), "session.json")
        
        # Usar sessão existente (criada via cookies)
        if os.path.exists(session_file):
            try:
                print("🔄 Carregando sessão salva...")
                client.load_settings(session_file)
                # Não fazer login novamente, apenas usar a sessão
                print("✅ Sessão carregada!")
            except Exception as session_error:
                return {
                    "ok": False,
                    "error": f"Erro ao carregar sessão: {str(session_error)}",
                    "message": f"❌ Erro ao carregar sessão\n\nExecute: python3 login_with_cookies.py"
                }
        else:
            return {
                "ok": False,
                "error": "Sessão não encontrada",
                "message": "❌ Sessão não encontrada (session.json)\n\nExecute primeiro: python3 login_with_cookies.py"
            }
        
        # Testar cada bot
        results = []
        for i, bot_username in enumerate(bot_usernames):
            print(f"\n🤖 Testando bot {i+1}/{len(bot_usernames)}: @{bot_username}")
            result = test_single_bot(client, bot_username)
            results.append(result)
            
            # Delay maior entre testes para evitar rate limit
            if i < len(bot_usernames) - 1:
                print(f"⏳ Aguardando 10s antes do próximo bot...")
                time.sleep(10)
        
        # Resumo
        total = len(results)
        working = sum(1 for r in results if r.get("bot_working"))
        
        # Mensagens
        messages = [r["message"] for r in results]
        summary = f"\n📊 Resumo: {working}/{total} bots funcionando\n" + "\n".join(messages)
        
        return {
            "ok": True,
            "total_bots": total,
            "working_bots": working,
            "results": results,
            "message": summary
        }
            
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "message": f"❌ Erro: {str(e)}"
        }

if __name__ == "__main__":
    result = test_instagram_bots()
    print(result.get("message", result.get("error", "Erro desconhecido")))
    sys.exit(0 if result.get("ok") else 1)
