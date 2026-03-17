#!/usr/bin/env python3
"""
Instagram Bot Monitor usando Instagrapi
Monitora bots do Instagram enviando mensagens de teste e verificando respostas.

AVISO: Este script usa métodos não oficiais e pode resultar em:
- Banimento da conta
- Bloqueio de IP
- Captcha constante

Use APENAS com contas de teste dedicadas!
"""

import os
import sys
import json
import time
import random
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

try:
    from instagrapi import Client
    from instagrapi.exceptions import (
        LoginRequired,
        ChallengeRequired,
        TwoFactorRequired,
        RateLimitError,
        ClientError
    )
except ImportError:
    print("❌ Erro: instagrapi não instalado. Execute: pip install instagrapi")
    sys.exit(1)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
AGENT_VERSION = "1.0.0"
SESSION_FILE = Path(__file__).parent / "instagram_session.json"
STATE_FILE = Path(__file__).parent / "instagram_state.json"
LOG_FILE = Path(__file__).parent / "instagram_monitor.log"

# Rate limiting - CRÍTICO para evitar ban
MAX_MESSAGES_PER_HOUR = 15
MAX_MESSAGES_PER_DAY = 100
MIN_DELAY_BETWEEN_MESSAGES = 120  # 2 minutos
MAX_DELAY_BETWEEN_MESSAGES = 300  # 5 minutos

# Timeouts
LOGIN_TIMEOUT = 30
MESSAGE_TIMEOUT = 20
RESPONSE_WAIT_TIMEOUT = 30
RESPONSE_CHECK_INTERVAL = 3


class RateLimiter:
    """Gerencia rate limiting para evitar banimento"""
    
    def __init__(self):
        self.state_file = STATE_FILE
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Carrega estado do rate limiter"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "messages_sent_hour": [],
            "messages_sent_day": [],
            "last_message_time": None
        }
    
    def _save_state(self):
        """Salva estado do rate limiter"""
        try:
            self.state_file.write_text(
                json.dumps(self.state, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            print(f"⚠️ Erro ao salvar estado: {e}")
    
    def _clean_old_timestamps(self):
        """Remove timestamps antigos"""
        now = time.time()
        hour_ago = now - 3600
        day_ago = now - 86400
        
        self.state["messages_sent_hour"] = [
            ts for ts in self.state["messages_sent_hour"] if ts > hour_ago
        ]
        self.state["messages_sent_day"] = [
            ts for ts in self.state["messages_sent_day"] if ts > day_ago
        ]
    
    def can_send_message(self) -> tuple[bool, Optional[str]]:
        """Verifica se pode enviar mensagem"""
        self._clean_old_timestamps()
        
        # Verificar limite por hora
        if len(self.state["messages_sent_hour"]) >= MAX_MESSAGES_PER_HOUR:
            return False, f"Limite de {MAX_MESSAGES_PER_HOUR} mensagens/hora atingido"
        
        # Verificar limite por dia
        if len(self.state["messages_sent_day"]) >= MAX_MESSAGES_PER_DAY:
            return False, f"Limite de {MAX_MESSAGES_PER_DAY} mensagens/dia atingido"
        
        # Verificar delay mínimo desde última mensagem
        if self.state["last_message_time"]:
            time_since_last = time.time() - self.state["last_message_time"]
            if time_since_last < MIN_DELAY_BETWEEN_MESSAGES:
                wait_time = int(MIN_DELAY_BETWEEN_MESSAGES - time_since_last)
                return False, f"Aguarde {wait_time}s antes de enviar próxima mensagem"
        
        return True, None
    
    def record_message_sent(self):
        """Registra que uma mensagem foi enviada"""
        now = time.time()
        self.state["messages_sent_hour"].append(now)
        self.state["messages_sent_day"].append(now)
        self.state["last_message_time"] = now
        self._save_state()
    
    def get_random_delay(self) -> int:
        """Retorna delay aleatório entre mensagens (comportamento humano)"""
        return random.randint(MIN_DELAY_BETWEEN_MESSAGES, MAX_DELAY_BETWEEN_MESSAGES)


class InstagramBotMonitor:
    """Monitor de bots do Instagram"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.client = Client()
        self.rate_limiter = RateLimiter()
        self.logged_in = False
        
        # Configurar client com delays mais humanos
        self.client.delay_range = [2, 5]  # Delay aleatório entre requisições
    
    def _log(self, level: str, message: str, data: Optional[Dict] = None):
        """Log estruturado"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "data": data or {}
        }
        
        # Console
        emoji = {"INFO": "ℹ️", "WARN": "⚠️", "ERROR": "❌", "SUCCESS": "✅"}.get(level, "📝")
        print(f"{emoji} [{level}] {message}")
        if data:
            print(f"   {json.dumps(data, ensure_ascii=False)}")
        
        # Arquivo
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception:
            pass
    
    def login(self) -> bool:
        """Faz login no Instagram com sessão persistente"""
        try:
            self._log("INFO", "Iniciando login", {"username": self.username})
            
            # Tentar carregar sessão salva
            if SESSION_FILE.exists():
                try:
                    self._log("INFO", "Tentando carregar sessão salva")
                    self.client.load_settings(str(SESSION_FILE))
                    self.client.login(self.username, self.password)
                    self._log("SUCCESS", "Login com sessão salva")
                    self.logged_in = True
                    return True
                except Exception as e:
                    self._log("WARN", "Sessão salva inválida, fazendo login novo", {"error": str(e)})
            
            # Login novo
            self._log("INFO", "Fazendo login novo")
            self.client.login(self.username, self.password)
            
            # Salvar sessão
            self.client.dump_settings(str(SESSION_FILE))
            self._log("SUCCESS", "Login realizado e sessão salva")
            
            self.logged_in = True
            return True
            
        except TwoFactorRequired:
            self._log("ERROR", "2FA ativado. Desative ou use senha de app")
            return False
        except ChallengeRequired as e:
            self._log("ERROR", "Challenge requerido. Instagram detectou atividade suspeita", {"error": str(e)})
            return False
        except LoginRequired:
            self._log("ERROR", "Login falhou. Verifique credenciais")
            return False
        except Exception as e:
            self._log("ERROR", "Erro no login", {"error": str(e)})
            return False
    
    def send_message(self, username_destino: str, mensagem: str) -> Optional[Dict[str, Any]]:
        """Envia mensagem para um usuário"""
        if not self.logged_in:
            self._log("ERROR", "Não está logado")
            return None
        
        # Verificar rate limit
        can_send, reason = self.rate_limiter.can_send_message()
        if not can_send:
            self._log("WARN", "Rate limit atingido", {"reason": reason})
            return {"success": False, "error": reason, "rate_limited": True}
        
        try:
            self._log("INFO", "Enviando mensagem", {
                "to": username_destino,
                "message": mensagem[:50] + "..." if len(mensagem) > 50 else mensagem
            })
            
            # Buscar ID do usuário
            user_id = self.client.user_id_from_username(username_destino)
            
            # Delay aleatório antes de enviar (comportamento humano)
            time.sleep(random.uniform(1, 3))
            
            # Enviar mensagem
            result = self.client.direct_send(mensagem, [user_id])
            
            # Registrar mensagem enviada
            self.rate_limiter.record_message_sent()
            
            self._log("SUCCESS", "Mensagem enviada", {
                "to": username_destino,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return {
                "success": True,
                "message_sent": mensagem,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": str(result)
            }
            
        except RateLimitError:
            self._log("ERROR", "Rate limit do Instagram atingido. Aguarde 1 hora")
            return {"success": False, "error": "Instagram rate limit", "rate_limited": True}
        except ClientError as e:
            self._log("ERROR", "Erro do cliente Instagram", {"error": str(e)})
            return {"success": False, "error": str(e)}
        except Exception as e:
            self._log("ERROR", "Erro ao enviar mensagem", {"error": str(e)})
            return {"success": False, "error": str(e)}
    
    def wait_for_response(self, username_destino: str, timeout: int = RESPONSE_WAIT_TIMEOUT) -> Optional[Dict[str, Any]]:
        """Aguarda resposta do bot"""
        if not self.logged_in:
            self._log("ERROR", "Não está logado")
            return None
        
        try:
            user_id = self.client.user_id_from_username(username_destino)
            
            # Pegar última mensagem antes de aguardar
            thread = self.client.direct_thread(user_id)
            last_msg_id = thread.messages[0].id if thread.messages else None
            
            self._log("INFO", "Aguardando resposta", {
                "from": username_destino,
                "timeout": timeout
            })
            
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                # Delay entre verificações
                time.sleep(RESPONSE_CHECK_INTERVAL)
                
                # Verificar novas mensagens
                thread = self.client.direct_thread(user_id)
                
                if thread.messages:
                    latest_msg = thread.messages[0]
                    
                    # Se é uma nova mensagem e não é nossa
                    if latest_msg.id != last_msg_id and latest_msg.user_id != self.client.user_id:
                        elapsed = time.time() - start_time
                        
                        self._log("SUCCESS", "Resposta recebida", {
                            "from": username_destino,
                            "response_time": f"{elapsed:.1f}s",
                            "text": latest_msg.text[:100] if latest_msg.text else "[mídia]"
                        })
                        
                        return {
                            "success": True,
                            "response_received": latest_msg.text or "[mídia]",
                            "response_time_sec": round(elapsed, 2),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
            
            self._log("WARN", "Timeout: Nenhuma resposta", {
                "from": username_destino,
                "timeout": timeout
            })
            
            return {
                "success": False,
                "response_received": None,
                "response_time_sec": None,
                "timeout": True
            }
            
        except Exception as e:
            self._log("ERROR", "Erro ao aguardar resposta", {"error": str(e)})
            return {"success": False, "error": str(e)}
    
    def test_bot(self, bot_username: str, test_message: str = "Bom dia") -> Dict[str, Any]:
        """Testa bot: envia mensagem e aguarda resposta"""
        self._log("INFO", "Iniciando teste de bot", {
            "bot": bot_username,
            "message": test_message
        })
        
        result = {
            "bot_username": bot_username,
            "test_message": test_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": False,
            "bot_working": False,
            "response_time_sec": None,
            "response_text": None,
            "error": None
        }
        
        # Enviar mensagem
        send_result = self.send_message(bot_username, test_message)
        
        if not send_result or not send_result.get("success"):
            result["error"] = send_result.get("error") if send_result else "Falha ao enviar mensagem"
            result["rate_limited"] = send_result.get("rate_limited", False) if send_result else False
            self._log("ERROR", "Teste falhou: erro ao enviar mensagem")
            return result
        
        # Aguardar resposta
        response_result = self.wait_for_response(bot_username)
        
        if response_result and response_result.get("success"):
            result["success"] = True
            result["bot_working"] = True
            result["response_time_sec"] = response_result.get("response_time_sec")
            result["response_text"] = response_result.get("response_received")
            self._log("SUCCESS", "Bot está funcionando", {
                "response_time": f"{result['response_time_sec']}s"
            })
        else:
            result["success"] = True  # Mensagem foi enviada
            result["bot_working"] = False  # Mas bot não respondeu
            result["error"] = "Bot não respondeu no timeout"
            self._log("WARN", "Bot não está respondendo")
        
        return result
    
    def logout(self):
        """Faz logout"""
        try:
            self.client.logout()
            self.logged_in = False
            self._log("INFO", "Logout realizado")
        except Exception as e:
            self._log("WARN", "Erro no logout", {"error": str(e)})


def send_report_to_server(report: Dict[str, Any]) -> bool:
    """Envia relatório para o servidor backend"""
    server_url = os.getenv("AGENT_SERVER", "http://localhost:9000")
    token = os.getenv("AGENT_TOKEN")
    site = os.getenv("INSTAGRAM_SITE_NAME", "instagram_bot")
    
    if not server_url:
        print("⚠️ AGENT_SERVER não configurado, pulando envio ao servidor")
        return False
    
    try:
        endpoint = f"{server_url.rstrip('/')}/api/agent/report"
        
        payload = {
            "site": site,
            "timestamp": report["timestamp"],
            "agent_version": AGENT_VERSION,
            "instagram_bot": report
        }
        
        headers = {}
        if token:
            headers["X-Agent-Token"] = token
        
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Relatório enviado ao servidor: {endpoint}")
            return True
        else:
            print(f"⚠️ Servidor retornou status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️ Erro ao enviar relatório ao servidor: {e}")
        return False


def main():
    """Função principal"""
    print("\n" + "="*70)
    print("🤖 INSTAGRAM BOT MONITOR")
    print(f"   Versão: {AGENT_VERSION}")
    print("="*70 + "\n")
    
    # Carregar configurações
    username = os.getenv("INSTAGRAM_MONITOR_USERNAME")
    password = os.getenv("INSTAGRAM_MONITOR_PASSWORD")
    bot_username = os.getenv("INSTAGRAM_BOT_USERNAME")
    test_message = os.getenv("INSTAGRAM_TEST_MESSAGE", "Bom dia")
    loop_mode = os.getenv("INSTAGRAM_MONITOR_LOOP", "false").lower() in ("1", "true", "yes")
    interval_sec = int(os.getenv("INSTAGRAM_MONITOR_INTERVAL_SEC", "1800"))  # 30 min padrão
    
    # Validar configurações
    if not username or not password:
        print("❌ Erro: INSTAGRAM_MONITOR_USERNAME e INSTAGRAM_MONITOR_PASSWORD são obrigatórios")
        print("   Configure no arquivo .env")
        sys.exit(1)
    
    if not bot_username:
        print("❌ Erro: INSTAGRAM_BOT_USERNAME é obrigatório")
        print("   Configure no arquivo .env")
        sys.exit(1)
    
    print(f"📋 Configuração:")
    print(f"   Conta monitor: @{username}")
    print(f"   Bot alvo: @{bot_username}")
    print(f"   Mensagem teste: '{test_message}'")
    print(f"   Modo loop: {'Sim' if loop_mode else 'Não'}")
    if loop_mode:
        print(f"   Intervalo: {interval_sec}s ({interval_sec//60} min)")
    print()
    
    # Criar monitor
    monitor = InstagramBotMonitor(username, password)
    
    # Login
    if not monitor.login():
        print("\n❌ Falha no login. Verifique:")
        print("   - Credenciais corretas")
        print("   - 2FA desativado ou use senha de app")
        print("   - Conta não bloqueada")
        sys.exit(1)
    
    print()
    
    # Executar teste(s)
    try:
        while True:
            print(f"⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            print("-" * 70)
            
            # Testar bot
            result = monitor.test_bot(bot_username, test_message)
            
            # Mostrar resultado
            print("\n📊 RESULTADO DO TESTE:")
            print(f"   Bot funcionando: {'✅ SIM' if result['bot_working'] else '❌ NÃO'}")
            if result['bot_working']:
                print(f"   Tempo de resposta: {result['response_time_sec']}s")
                print(f"   Resposta: {result['response_text'][:100]}")
            else:
                print(f"   Erro: {result.get('error', 'Desconhecido')}")
            
            # Enviar ao servidor
            print()
            send_report_to_server(result)
            
            # Sair se não for modo loop
            if not loop_mode:
                break
            
            # Aguardar próximo ciclo
            next_delay = monitor.rate_limiter.get_random_delay()
            actual_delay = max(interval_sec, next_delay)
            
            print(f"\n💤 Aguardando {actual_delay}s até próximo teste...")
            print(f"   (Próximo teste: {(datetime.now() + timedelta(seconds=actual_delay)).strftime('%H:%M:%S')})")
            print("="*70 + "\n")
            
            time.sleep(actual_delay)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoramento interrompido pelo usuário")
    finally:
        monitor.logout()
    
    print("\n✅ Monitor finalizado")
    sys.exit(0 if result.get('bot_working') else 1)


if __name__ == "__main__":
    main()
