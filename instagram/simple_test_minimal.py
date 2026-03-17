#!/usr/bin/env python3
"""
Teste MÍNIMO de bots do Instagram
Apenas envia mensagem e aguarda - SEM buscar user_id ou verificar respostas constantemente
"""

import os
import sys
import time
from dotenv import load_dotenv

try:
    from instagrapi import Client
except ImportError:
    print("❌ Erro: instagrapi não instalado. Execute: pip install instagrapi")
    sys.exit(1)

load_dotenv()

# Timeout para aguardar resposta (em segundos)
RESPONSE_TIMEOUT = 30

def test_instagram_bots_minimal():
    """Testa múltiplos bots do Instagram - VERSÃO MÍNIMA"""
    
    # Configurações
    bot_usernames_str = os.getenv("INSTAGRAM_BOT_USERNAME", "")
    bot_usernames = [b.strip() for b in bot_usernames_str.split(",") if b.strip()]
    
    if not bot_usernames:
        return {
            "ok": False,
            "error": "Nenhum bot configurado. Configure INSTAGRAM_BOT_USERNAME no .env"
        }
    
    try:
        # Carregar sessão
        client = Client()
        client.delay_range = [2, 5]  # Delays maiores
        
        session_file = os.path.join(os.path.dirname(__file__), "session.json")
        
        if not os.path.exists(session_file):
            return {
                "ok": False,
                "error": "Sessão não encontrada",
                "message": "❌ Execute: python3 login_with_cookies.py"
            }
        
        print("🔄 Carregando sessão...")
        client.load_settings(session_file)
        print("✅ Sessão carregada!")
        
        # Testar cada bot
        results = []
        
        for i, bot_username in enumerate(bot_usernames):
            print(f"\n🤖 Bot {i+1}/{len(bot_usernames)}: @{bot_username}")
            
            try:
                # APENAS enviar mensagem - sem buscar user_id
                # Usar threads existentes (menos requisições)
                print(f"📤 Enviando mensagem para @{bot_username}...")
                
                # Pegar threads (1 requisição apenas)
                threads = client.direct_threads(amount=20)
                
                # Procurar thread com o bot
                bot_thread = None
                for thread in threads:
                    for user in thread.users:
                        if user.username == bot_username:
                            bot_thread = thread
                            break
                    if bot_thread:
                        break
                
                if not bot_thread:
                    results.append({
                        "bot_username": bot_username,
                        "ok": False,
                        "error": "Thread não encontrada",
                        "message": f"⚠️ @{bot_username}: Nenhuma conversa anterior encontrada"
                    })
                    continue
                
                # Enviar mensagem
                client.direct_send("Bom dia", thread_ids=[bot_thread.id])
                print(f"✅ Mensagem enviada!")
                
                # Aguardar sem verificar (evita requisições)
                print(f"⏳ Aguardando {RESPONSE_TIMEOUT}s...")
                time.sleep(RESPONSE_TIMEOUT)
                
                # Verificar UMA VEZ apenas
                print("🔍 Verificando resposta...")
                updated_thread = client.direct_thread(bot_thread.id)
                
                # Pegar última mensagem
                if updated_thread.messages:
                    latest = updated_thread.messages[0]
                    if latest.user_id != client.user_id:
                        response_text = latest.text or "[mídia]"
                        results.append({
                            "bot_username": bot_username,
                            "ok": True,
                            "bot_working": True,
                            "response_text": response_text[:100],
                            "message": f"✅ @{bot_username}: Respondeu - {response_text[:50]}"
                        })
                    else:
                        results.append({
                            "bot_username": bot_username,
                            "ok": True,
                            "bot_working": False,
                            "message": f"⚠️ @{bot_username}: Não respondeu em {RESPONSE_TIMEOUT}s"
                        })
                else:
                    results.append({
                        "bot_username": bot_username,
                        "ok": True,
                        "bot_working": False,
                        "message": f"⚠️ @{bot_username}: Sem mensagens"
                    })
                
            except Exception as e:
                error_msg = str(e)[:100]
                results.append({
                    "bot_username": bot_username,
                    "ok": False,
                    "error": error_msg,
                    "message": f"❌ @{bot_username}: {error_msg}"
                })
            
            # Delay entre bots
            if i < len(bot_usernames) - 1:
                print(f"\n⏳ Aguardando 15s antes do próximo bot...")
                time.sleep(15)
        
        # Resumo
        total = len(results)
        working = sum(1 for r in results if r.get("bot_working"))
        
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
    result = test_instagram_bots_minimal()
    print(result.get("message", result.get("error", "Erro desconhecido")))
    sys.exit(0 if result.get("ok") else 1)
