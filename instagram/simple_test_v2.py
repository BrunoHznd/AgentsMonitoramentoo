#!/usr/bin/env python3
"""
Teste de bots do Instagram - Versão 2
Usa abordagem alternativa para enviar mensagens
"""

import os
import sys
import time
from dotenv import load_dotenv

try:
    from instagrapi import Client
    from instagrapi.exceptions import ClientError
except ImportError:
    print("❌ Erro: instagrapi não instalado. Execute: pip install instagrapi")
    sys.exit(1)

load_dotenv()

RESPONSE_TIMEOUT = 30

def test_bot_v2(client, bot_username):
    """Testa um bot usando abordagem alternativa"""
    try:
        print(f"\n🤖 Testando @{bot_username}")
        
        # Buscar user_id do bot
        print(f"🔍 Buscando informações de @{bot_username}...")
        time.sleep(2)
        
        try:
            user_id = client.user_id_from_username(bot_username)
            print(f"✅ User ID encontrado: {user_id}")
        except Exception as e:
            return {
                "bot_username": bot_username,
                "ok": False,
                "error": f"Não foi possível encontrar @{bot_username}",
                "message": f"❌ @{bot_username}: Usuário não encontrado"
            }
        
        # Tentar enviar mensagem diretamente
        print(f"📤 Enviando mensagem...")
        time.sleep(2)
        
        try:
            # Método 1: Enviar para user_id
            client.direct_send("Bom dia", [user_id])
            print(f"✅ Mensagem enviada!")
            
            # Aguardar resposta
            print(f"⏳ Aguardando {RESPONSE_TIMEOUT}s por resposta...")
            start_time = time.time()
            
            # Aguardar sem verificar constantemente
            time.sleep(RESPONSE_TIMEOUT)
            
            # Verificar UMA vez
            print(f"🔍 Verificando resposta...")
            time.sleep(2)
            
            try:
                thread = client.direct_thread(user_id)
                
                if thread and thread.messages:
                    # Pegar as 3 últimas mensagens
                    recent_msgs = thread.messages[:3]
                    
                    # Procurar resposta do bot (não nossa mensagem)
                    for msg in recent_msgs:
                        if msg.user_id != client.user_id:
                            response_text = msg.text or "[mídia]"
                            elapsed = time.time() - start_time
                            
                            return {
                                "bot_username": bot_username,
                                "ok": True,
                                "bot_working": True,
                                "response_time_sec": round(elapsed, 1),
                                "response_text": response_text[:100],
                                "message": f"✅ @{bot_username}: Respondeu - {response_text[:50]}"
                            }
                    
                    # Não encontrou resposta do bot
                    return {
                        "bot_username": bot_username,
                        "ok": True,
                        "bot_working": False,
                        "message": f"⚠️ @{bot_username}: Não respondeu em {RESPONSE_TIMEOUT}s"
                    }
                else:
                    return {
                        "bot_username": bot_username,
                        "ok": True,
                        "bot_working": False,
                        "message": f"⚠️ @{bot_username}: Thread vazia"
                    }
                    
            except Exception as thread_error:
                # Erro ao verificar thread, mas mensagem foi enviada
                return {
                    "bot_username": bot_username,
                    "ok": True,
                    "bot_working": None,
                    "message": f"⚠️ @{bot_username}: Mensagem enviada, mas não foi possível verificar resposta"
                }
                
        except ClientError as e:
            error_msg = str(e)
            if "400" in error_msg or "Bad Request" in error_msg:
                return {
                    "bot_username": bot_username,
                    "ok": False,
                    "error": "Instagram bloqueou envio de mensagens",
                    "message": f"❌ @{bot_username}: Instagram bloqueou DMs (erro 400)"
                }
            raise
            
    except Exception as e:
        error_msg = str(e)[:100]
        return {
            "bot_username": bot_username,
            "ok": False,
            "error": error_msg,
            "message": f"❌ @{bot_username}: {error_msg}"
        }


def test_instagram_bots_v2():
    """Testa múltiplos bots - Versão 2"""
    
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
        client.delay_range = [2, 5]
        
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
            result = test_bot_v2(client, bot_username)
            results.append(result)
            
            # Delay entre bots
            if i < len(bot_usernames) - 1:
                print(f"\n⏳ Aguardando 20s antes do próximo bot...")
                time.sleep(20)
        
        # Resumo
        total = len(results)
        working = sum(1 for r in results if r.get("bot_working") == True)
        
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
    result = test_instagram_bots_v2()
    print(result.get("message", result.get("error", "Erro desconhecido")))
    sys.exit(0 if result.get("ok") else 1)
