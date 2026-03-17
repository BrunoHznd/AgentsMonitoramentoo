#!/usr/bin/env python3
"""
Apenas VERIFICA respostas dos bots (NÃO envia mensagens)
Use este script se o Instagram bloqueou o envio de DMs
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

try:
    from instagrapi import Client
except ImportError:
    print("❌ Erro: instagrapi não instalado")
    sys.exit(1)

load_dotenv()

def check_bot_response(client, bot_username):
    """Verifica se um bot respondeu recentemente (sem enviar mensagem)"""
    try:
        print(f"\n🔍 Verificando @{bot_username}...")
        time.sleep(2)
        
        # Buscar user_id
        try:
            user_id = client.user_id_from_username(bot_username)
        except Exception as e:
            if "429" in str(e):
                print(f"⚠️ Rate limit, aguardando 30s...")
                time.sleep(30)
                user_id = client.user_id_from_username(bot_username)
            else:
                raise
        
        # Pegar thread
        time.sleep(3)
        thread = client.direct_thread(user_id)
        
        if not thread or not thread.messages:
            return {
                "bot_username": bot_username,
                "ok": True,
                "has_recent_activity": False,
                "message": f"⚠️ @{bot_username}: Sem mensagens"
            }
        
        # Analisar últimas 5 mensagens
        recent_msgs = thread.messages[:5]
        
        bot_responses = []
        for msg in recent_msgs:
            if msg.user_id != client.user_id:  # Mensagem do bot
                bot_responses.append({
                    "text": msg.text or "[mídia]",
                    "timestamp": msg.timestamp
                })
        
        if bot_responses:
            latest = bot_responses[0]
            time_diff = datetime.now() - latest["timestamp"]
            minutes_ago = int(time_diff.total_seconds() / 60)
            
            return {
                "bot_username": bot_username,
                "ok": True,
                "has_recent_activity": True,
                "last_response_text": latest["text"][:100],
                "minutes_ago": minutes_ago,
                "message": f"✅ @{bot_username}: Última resposta há {minutes_ago} min - {latest['text'][:50]}"
            }
        else:
            return {
                "bot_username": bot_username,
                "ok": True,
                "has_recent_activity": False,
                "message": f"⚠️ @{bot_username}: Nenhuma resposta recente"
            }
            
    except Exception as e:
        error_msg = str(e)[:100]
        return {
            "bot_username": bot_username,
            "ok": False,
            "error": error_msg,
            "message": f"❌ @{bot_username}: {error_msg}"
        }


def check_instagram_bots():
    """Verifica respostas dos bots (sem enviar mensagens)"""
    
    bot_usernames_str = os.getenv("INSTAGRAM_BOT_USERNAME", "")
    bot_usernames = [b.strip() for b in bot_usernames_str.split(",") if b.strip()]
    
    if not bot_usernames:
        return {
            "ok": False,
            "error": "Nenhum bot configurado",
            "message": "❌ Configure INSTAGRAM_BOT_USERNAME no .env"
        }
    
    try:
        # Carregar sessão
        client = Client()
        client.delay_range = [3, 6]
        
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
        print("\n⚠️ MODO: Apenas verificação (sem enviar mensagens)")
        print("💡 Envie 'Bom dia' manualmente pelo app do Instagram para cada bot antes de executar este script\n")
        
        # Verificar cada bot
        results = []
        
        for i, bot_username in enumerate(bot_usernames):
            result = check_bot_response(client, bot_username)
            results.append(result)
            
            if i < len(bot_usernames) - 1:
                print(f"\n⏳ Aguardando 10s...")
                time.sleep(10)
        
        # Resumo
        total = len(results)
        active = sum(1 for r in results if r.get("has_recent_activity"))
        
        messages = [r["message"] for r in results]
        summary = f"\n📊 Resumo: {active}/{total} bots com atividade recente\n" + "\n".join(messages)
        
        return {
            "ok": True,
            "total_bots": total,
            "active_bots": active,
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
    print("=" * 60)
    print("VERIFICADOR DE RESPOSTAS - Instagram Bots")
    print("=" * 60)
    print("\n📝 INSTRUÇÕES:")
    print("1. Abra o Instagram no seu celular/navegador")
    print("2. Envie 'Bom dia' manualmente para cada bot")
    print("3. Aguarde as respostas")
    print("4. Execute este script para verificar\n")
    
    input("Pressione ENTER quando tiver enviado as mensagens manualmente...")
    
    result = check_instagram_bots()
    print(result.get("message", result.get("error", "Erro desconhecido")))
    sys.exit(0 if result.get("ok") else 1)
