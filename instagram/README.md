# 🤖 Monitor de Bots do Instagram

Sistema de monitoramento automático de bots do Instagram usando **instagrapi**.

## ⚠️ **AVISO CRÍTICO**

Este monitor usa métodos **NÃO OFICIAIS** que **VIOLAM os Termos de Serviço do Instagram**.

**Riscos:**
- ❌ **Banimento permanente** da conta
- ❌ **Bloqueio de IP**
- ❌ **Captcha constante**
- ❌ **Limitação de funcionalidades**

**USE APENAS:**
- ✅ Conta de teste dedicada (não sua conta pessoal!)
- ✅ Ambiente de desenvolvimento/teste
- ✅ Com conhecimento dos riscos

---

## 📋 **Requisitos**

### **1. Conta de Teste do Instagram**

Crie uma conta **NOVA** e **DEDICADA** apenas para monitoramento:

```
Username: conta_teste_monitor_123
Email: teste.monitor@seudominio.com
Senha: senha_forte_aqui
```

**IMPORTANTE:**
- Não use sua conta pessoal
- Não use conta de produção
- Use conta descartável
- Desative 2FA (ou use senha de app)

### **2. Dependências Python**

```bash
pip install instagrapi==2.1.2
```

---

## 🚀 **Instalação**

### **1. Instalar Dependências**

```bash
cd /root/Desktop/monitoramento
pip install -r requirements.txt
```

### **2. Configurar Variáveis de Ambiente**

Edite o arquivo `.env`:

```bash
# Instagram Bot Monitor
INSTAGRAM_MONITOR_USERNAME=sua_conta_teste_monitor
INSTAGRAM_MONITOR_PASSWORD=senha_da_conta_teste
INSTAGRAM_BOT_USERNAME=nome_do_bot_a_monitorar
INSTAGRAM_TEST_MESSAGE=Bom dia
INSTAGRAM_MONITOR_LOOP=true
INSTAGRAM_MONITOR_INTERVAL_SEC=1800
INSTAGRAM_SITE_NAME=instagram_bot

# Backend (se quiser enviar relatórios)
AGENT_SERVER=http://localhost:9000
AGENT_TOKEN=seu_token_aqui
```

### **3. Testar Manualmente**

```bash
cd agents/instagram
python instagram_bot_monitor.py
```

---

## 📊 **Como Funciona**

### **Fluxo de Monitoramento**

1. **Login** na conta de teste usando instagrapi
2. **Enviar mensagem** de teste para o bot (ex: "Bom dia")
3. **Aguardar resposta** por 30 segundos
4. **Verificar** se bot respondeu
5. **Enviar relatório** ao servidor backend
6. **Aguardar intervalo** (30 min padrão)
7. **Repetir** (se modo loop ativado)

### **Rate Limiting (Proteção contra Ban)**

O sistema implementa **rate limiting rigoroso**:

- ✅ Máximo **15 mensagens/hora**
- ✅ Máximo **100 mensagens/dia**
- ✅ Delay mínimo **2 minutos** entre mensagens
- ✅ Delay aleatório **2-5 minutos** (comportamento humano)
- ✅ Sessão persistente (evita logins repetidos)

### **Detecção de Problemas**

O monitor detecta:

- ❌ Bot não responde (timeout 30s)
- ❌ Erro ao enviar mensagem
- ❌ Rate limit do Instagram atingido
- ❌ Challenge/Captcha requerido
- ❌ Conta bloqueada

---

## 🔧 **Configuração Avançada**

### **Modo Loop (Monitoramento Contínuo)**

```bash
# .env
INSTAGRAM_MONITOR_LOOP=true
INSTAGRAM_MONITOR_INTERVAL_SEC=1800  # 30 minutos
```

### **Modo Single (Teste Único)**

```bash
# .env
INSTAGRAM_MONITOR_LOOP=false
```

### **Ajustar Mensagem de Teste**

```bash
# .env
INSTAGRAM_TEST_MESSAGE=Olá, tudo bem?
```

### **Múltiplos Bots**

Para monitorar múltiplos bots, crie múltiplas instâncias com contas diferentes:

```bash
# Bot 1
INSTAGRAM_MONITOR_USERNAME=teste_monitor_1
INSTAGRAM_BOT_USERNAME=bot_1

# Bot 2 (em outro servidor/container)
INSTAGRAM_MONITOR_USERNAME=teste_monitor_2
INSTAGRAM_BOT_USERNAME=bot_2
```

---

## 📡 **Integração com Backend**

### **Endpoints da API**

#### **1. Receber Relatório**
```http
POST /api/instagram/report
Content-Type: application/json
X-Agent-Token: seu_token

{
  "bot_username": "nome_do_bot",
  "timestamp": "2026-02-26T13:00:00Z",
  "success": true,
  "bot_working": true,
  "response_time_sec": 2.5,
  "response_text": "Olá! Como posso ajudar?",
  "test_message": "Bom dia"
}
```

#### **2. Consultar Status**
```http
GET /api/instagram/nome_do_bot/status
```

Resposta:
```json
{
  "bot_username": "nome_do_bot",
  "bot_working": true,
  "last_test": "2026-02-26T13:00:00Z",
  "response_time_sec": 2.5,
  "response_text": "Olá! Como posso ajudar?",
  "has_open_incident": false,
  "incident": null
}
```

#### **3. Listar Todos os Relatórios**
```http
GET /api/instagram/reports
```

#### **4. Health Check (Bot ID 2)**
```http
GET /api/bots/2/health
```

---

## 🚨 **Sistema de Incidentes**

### **Abertura Automática**

Incidente é aberto quando:
- Bot não responde em teste
- Tipo: `instagram_bot_offline`
- Severidade: `high`

### **Fechamento Automático**

Incidente é fechado quando:
- Bot volta a responder
- Duração é calculada automaticamente

### **Consultar Incidentes**

```http
GET /api/incidents?site=instagram_bot
```

---

## 📝 **Logs e Debugging**

### **Logs do Monitor**

```bash
tail -f agents/instagram/instagram_monitor.log
```

Formato JSON:
```json
{
  "timestamp": "2026-02-26T13:00:00Z",
  "level": "INFO",
  "message": "Mensagem enviada",
  "data": {
    "to": "nome_do_bot",
    "message": "Bom dia"
  }
}
```

### **Estado do Rate Limiter**

```bash
cat agents/instagram/instagram_state.json
```

```json
{
  "messages_sent_hour": [1709035200.5, 1709035320.8],
  "messages_sent_day": [1709035200.5, 1709035320.8],
  "last_message_time": 1709035320.8
}
```

### **Sessão do Instagram**

```bash
cat agents/instagram/instagram_session.json
```

---

## 🛠️ **Troubleshooting**

### **Erro: "Challenge Required"**

```
Solução:
1. Instagram detectou atividade suspeita
2. Aguarde 24 horas
3. Faça login manual no app do Instagram
4. Complete o desafio (código SMS, reconhecimento facial, etc)
5. Tente novamente
```

### **Erro: "Login Failed"**

```
Solução:
1. Verifique username e senha
2. Desative 2FA temporariamente
3. Use senha de app se tiver 2FA
4. Verifique se conta não está bloqueada
```

### **Erro: "Rate Limit"**

```
Solução:
1. Sistema de rate limiting interno ativado
2. Aguarde o tempo indicado
3. Reduza INSTAGRAM_MONITOR_INTERVAL_SEC
4. Verifique instagram_state.json
```

### **Erro: "Instagram Rate Limit"**

```
Solução:
1. Instagram bloqueou temporariamente
2. Aguarde 1-2 horas
3. Reduza frequência de testes
4. Use conta diferente
```

### **Bot Não Responde**

```
Verificar:
1. Bot está realmente online?
2. Bot responde manualmente pelo app?
3. Timeout de 30s é suficiente?
4. Mensagem de teste está correta?
```

---

## 🔒 **Boas Práticas de Segurança**

### **1. Conta Dedicada**
```bash
# ✅ CORRETO
INSTAGRAM_MONITOR_USERNAME=teste_monitor_bot_123

# ❌ ERRADO
INSTAGRAM_MONITOR_USERNAME=minha_conta_pessoal
```

### **2. Delays Aleatórios**
O sistema já implementa delays aleatórios automaticamente.

### **3. Limite de Mensagens**
Não altere os limites de rate limiting sem necessidade.

### **4. Monitoramento de Logs**
Monitore logs para detectar problemas cedo:

```bash
# Alertar se muitos erros
grep -i "error" agents/instagram/instagram_monitor.log | tail -20
```

### **5. Backup de Sessão**
Faça backup da sessão para evitar logins repetidos:

```bash
cp agents/instagram/instagram_session.json agents/instagram/instagram_session.backup.json
```

---

## 📈 **Métricas e Analytics**

### **Dados Coletados**

- ✅ Status do bot (online/offline)
- ✅ Tempo de resposta (segundos)
- ✅ Texto da resposta
- ✅ Timestamp de cada teste
- ✅ Taxa de sucesso
- ✅ Incidentes (abertura/fechamento)

### **Análise de Disponibilidade**

```python
# Calcular uptime
import json

with open('server/data/instagram_bot_reports.json') as f:
    reports = json.load(f)

total_tests = len(reports)
successful_tests = sum(1 for r in reports.values() if r.get('bot_working'))
uptime_percentage = (successful_tests / total_tests) * 100

print(f"Uptime: {uptime_percentage:.2f}%")
```

---

## 🚀 **Executar como Serviço**

### **Linux (systemd)**

Crie `/etc/systemd/system/instagram-monitor.service`:

```ini
[Unit]
Description=Instagram Bot Monitor
After=network.target

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/root/Desktop/monitoramento/agents/instagram
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 instagram_bot_monitor.py
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
```

Ativar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable instagram-monitor
sudo systemctl start instagram-monitor
sudo systemctl status instagram-monitor
```

### **Windows (Task Scheduler)**

Use o PowerShell para criar tarefa agendada:

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "instagram_bot_monitor.py" -WorkingDirectory "C:\monitoramento\agents\instagram"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "InstagramBotMonitor" -Action $action -Trigger $trigger -RunLevel Highest
```

---

## 📚 **Referências**

- [Instagrapi Documentation](https://github.com/adw0rd/instagrapi)
- [Instagram Terms of Service](https://help.instagram.com/581066165581870)
- [Rate Limiting Best Practices](https://developers.facebook.com/docs/graph-api/overview/rate-limiting)

---

## ⚖️ **Disclaimer Legal**

Este software é fornecido "como está", sem garantias de qualquer tipo. O uso deste software é de sua inteira responsabilidade. Os desenvolvedores não se responsabilizam por:

- Banimento de contas
- Bloqueio de IPs
- Violação de Termos de Serviço
- Qualquer dano direto ou indireto

**USE POR SUA CONTA E RISCO.**

---

**Versão:** 1.0.0  
**Data:** 26/02/2026  
**Autor:** Sistema de Monitoramento
