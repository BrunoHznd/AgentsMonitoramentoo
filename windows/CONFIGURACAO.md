# 🚀 Configuração do Agente de Monitoramento

## 📋 Pré-requisitos

- Python 3.7 ou superior instalado
- Conexão com o servidor central (IP: `92.113.38.123:9000`)
- Acesso à rede onde as câmeras estão instaladas

---

## ⚙️ Configuração Inicial

### 1. Baixar o Agente

```bash
git clone https://github.com/BrunoHznd/AgentsMonitoramentoo.git
cd AgentsMonitoramentoo/windows
```

### 2. Editar o Arquivo de Configuração

Abra o arquivo `agent.json` e configure:

```json
{
  "site": "nome-do-seu-site",
  "server": "http://92.113.38.123:9000",
  "token": "",
  "interval_sec": 5,
  "loop": true,
  "cameras": []
}
```

**Importante:**
- ✅ **site**: Deixe como está - será definido após aprovação no dashboard
- ✅ **server**: Use `http://92.113.38.123:9000` (IP do servidor central)
- ✅ **token**: Deixe vazio inicialmente
- ✅ **interval_sec**: Intervalo de envio de dados (5 segundos recomendado)
- ✅ **cameras**: Deixe vazio - será configurado pelo servidor

### 3. Executar o Agente

**Windows (PowerShell):**
```powershell
python agent.py
```

Ou use o script:
```powershell
.\run_agent.ps1
```

**Linux:**
```bash
python3 agent.py
```

---

## 🔐 Aprovação do Agente

### Primeira Execução

Quando você executar o agente pela primeira vez, verá:

```
[agent] Novo agent_id gerado para hostname 'SEU-PC': abc123...
[agent] register denied: {'ok': False, 'reason': 'pending_approval'}
```

**Isso é normal!** O agente está aguardando aprovação.

### Aprovar no Dashboard

1. Acesse o dashboard: `http://92.113.38.123` (ou o IP do servidor)
2. Vá para a aba **"Localidades"**
3. Role até **"Agentes Pendentes de Aprovação"**
4. Você verá seu agente listado com o hostname do PC
5. Digite um **nome único** para o site (ex: `loja-centro`, `galpao-norte`)
6. Clique em **"Aprovar"**

**⚠️ IMPORTANTE:** Cada agente deve ter um **site único**. Não use o mesmo nome para dois agentes diferentes!

---

## 🎯 Identificação Única por PC

O agente gera automaticamente um `agent_id` único baseado no **hostname** da máquina. Isso significa:

✅ **Você pode copiar os arquivos** para outros PCs sem problemas
✅ **Cada PC terá um ID diferente** automaticamente
✅ **Não há conflito** entre agentes em máquinas diferentes
✅ **Cada agente aparece separadamente** no dashboard

---

## 📝 Configuração de Câmeras

Após a aprovação, você pode configurar as câmeras de duas formas:

### Opção 1: Via Dashboard (Recomendado)

1. Acesse a aba **"Localidades"**
2. Encontre seu site aprovado
3. Clique em **"Adicionar IPs"**
4. Configure o prefixo de rede e sufixos das câmeras

### Opção 2: Via Arquivo JSON (Local)

Edite `agent.json`:

```json
{
  "site": "seu-site",
  "server": "http://92.113.38.123:9000",
  "token": "",
  "interval_sec": 5,
  "loop": true,
  "cameras": [
    {"name": "Camera 1", "ip": "192.168.1.100"},
    {"name": "Camera 2", "ip": "192.168.1.101"}
  ]
}
```

---

## 🔄 Auto-Atualização

O agente verifica automaticamente por atualizações no servidor a cada execução. Quando uma nova versão está disponível:

1. O agente baixa a nova versão
2. Faz backup da versão atual
3. Substitui o arquivo
4. Reinicia automaticamente

**Você não precisa fazer nada!** O agente se atualiza sozinho.

---

## 🐛 Solução de Problemas

### Erro: "Failed to establish a new connection"

**Causa:** O agente não consegue se conectar ao servidor.

**Solução:**
1. Verifique se o IP do servidor está correto em `agent.json`
2. Teste a conexão: `ping 92.113.38.123`
3. Verifique se a porta 9000 está acessível
4. Verifique firewall/antivírus

### Erro: "register denied: pending_approval"

**Causa:** O agente ainda não foi aprovado no dashboard.

**Solução:**
1. Acesse o dashboard
2. Vá para "Localidades"
3. Aprove o agente pendente

### Dois agentes aparecem como um só

**Causa:** Você copiou o arquivo `agent_state.json` junto com o agente.

**Solução:**
1. Delete o arquivo `agent_state.json` no segundo PC
2. Reinicie o agente
3. Um novo `agent_id` será gerado automaticamente

---

## 📊 Monitoramento

Após aprovação, o agente começará a enviar dados automaticamente:

- ✅ Status das câmeras (online/offline)
- ✅ Testes de rede (DNS, HTTP)
- ✅ Velocidade de internet (download/upload)
- ✅ Ping para câmeras
- ✅ MAC address das câmeras

Todos os dados aparecem em tempo real no dashboard!

---

## 🆘 Suporte

Se tiver problemas:

1. Verifique os logs do agente no console
2. Verifique o arquivo `agent_state.json` (contém o `agent_id`)
3. Acesse o dashboard e veja se o agente está listado
4. Entre em contato com o administrador do sistema

---

## 📌 Checklist de Instalação

- [ ] Python instalado
- [ ] Repositório clonado
- [ ] `agent.json` configurado com IP correto do servidor
- [ ] Agente executado pela primeira vez
- [ ] Agente aprovado no dashboard com site único
- [ ] Câmeras configuradas
- [ ] Dados aparecendo no dashboard

---

**Versão do Agente:** 1.0.0  
**Última Atualização:** 24/02/2026
