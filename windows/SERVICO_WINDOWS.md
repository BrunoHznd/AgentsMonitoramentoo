# 🔧 Como Configurar o Agente como Serviço do Windows

Este tutorial mostra como instalar o agente de monitoramento como um **serviço do Windows** que inicia automaticamente quando o computador liga, mesmo após reinicializações.

---

## 📋 **Por Que Usar Como Serviço?**

✅ **Inicia automaticamente** quando o Windows liga  
✅ **Roda em segundo plano** sem janela de console  
✅ **Continua rodando** mesmo se você fizer logoff  
✅ **Reinicia automaticamente** se o agente travar  
✅ **Logs automáticos** salvos em arquivo  

---

## 🚀 **Instalação Automática (Recomendado)**

### **Passo 1: Baixar o Agente**

```powershell
# Baixar do GitHub
git clone https://github.com/BrunoHznd/AgentsMonitoramentoo.git
cd AgentsMonitoramentoo\windows
```

### **Passo 2: Configurar o Agente**

Edite o arquivo `agent.json`:

```json
{
  "site": "site-exemplo",
  "server": "http://92.113.38.123:9000",
  "token": "",
  "interval_sec": 5,
  "loop": true,
  "cameras": []
}
```

**Importante:** Configure o IP correto do servidor central!

### **Passo 3: Executar o Instalador**

1. **Abra PowerShell como Administrador:**
   - Pressione `Win + X`
   - Selecione **"Windows PowerShell (Admin)"** ou **"Terminal (Admin)"**

2. **Navegue até a pasta do agente:**
   ```powershell
   cd C:\caminho\para\AgentsMonitoramentoo\windows
   ```

3. **Execute o script de instalação:**
   ```powershell
   .\instalar_servico.ps1
   ```

4. **Aguarde a instalação:**
   ```
   ============================================
     Instalador do Agente de Monitoramento    
   ============================================
   
   [1/6] Verificando Python...
         Python encontrado: C:\Python310\python.exe
         Versao: Python 3.10.0
   
   [2/6] Baixando NSSM...
         Baixando de: https://nssm.cc/release/nssm-2.24.zip
         NSSM baixado com sucesso!
   
   [3/6] Verificando servico existente...
   
   [4/6] Instalando servico...
   
   [5/6] Configurando servico...
   
   [6/6] Iniciando servico...
   
   ============================================
     INSTALACAO CONCLUIDA COM SUCESSO!        
   ============================================
   
   Servico instalado: MonitoramentoAgente
   Status: Rodando
   Inicio automatico: Sim
   ```

### **Pronto!** 🎉

O agente agora está rodando como serviço e iniciará automaticamente quando o Windows ligar.

---

## 🔍 **Verificar Status do Serviço**

### **Via PowerShell:**

```powershell
# Ver status
sc query MonitoramentoAgente

# Ou usando Get-Service
Get-Service MonitoramentoAgente
```

### **Via Gerenciador de Serviços:**

1. Pressione `Win + R`
2. Digite `services.msc` e pressione Enter
3. Procure por **"Agente de Monitoramento de Cameras"**
4. Verifique se está **"Em execução"** e **"Automático"**

---

## 📊 **Ver Logs do Agente**

Os logs são salvos automaticamente na pasta do agente:

```powershell
# Ver log de saída (stdout)
notepad agent_log.txt

# Ver log de erros (stderr)
notepad agent_error.txt

# Ou abrir a pasta
explorer .
```

**Logs em tempo real:**

```powershell
# PowerShell
Get-Content agent_log.txt -Wait -Tail 20

# Ou use um editor que atualiza automaticamente
```

---

## 🛠️ **Gerenciar o Serviço**

### **Parar o Serviço:**

```powershell
sc stop MonitoramentoAgente
```

Ou:

```powershell
Stop-Service MonitoramentoAgente
```

### **Iniciar o Serviço:**

```powershell
sc start MonitoramentoAgente
```

Ou:

```powershell
Start-Service MonitoramentoAgente
```

### **Reiniciar o Serviço:**

```powershell
Restart-Service MonitoramentoAgente
```

### **Desinstalar o Serviço:**

Execute o script de desinstalação:

```powershell
.\desinstalar_servico.ps1
```

Ou manualmente:

```powershell
# Parar o serviço
sc stop MonitoramentoAgente

# Remover o serviço
sc delete MonitoramentoAgente
```

---

## 🔧 **Instalação Manual (Avançado)**

Se preferir instalar manualmente sem usar o script automático:

### **1. Baixar NSSM**

```powershell
# Baixar de https://nssm.cc/download
# Extrair nssm.exe para a pasta do agente
```

### **2. Instalar o Serviço**

```powershell
# Encontrar caminho do Python
$pythonPath = (Get-Command python).Source

# Instalar serviço
.\nssm.exe install MonitoramentoAgente $pythonPath "C:\caminho\para\agent.py"
```

### **3. Configurar o Serviço**

```powershell
# Nome de exibição
.\nssm.exe set MonitoramentoAgente DisplayName "Agente de Monitoramento de Cameras"

# Descrição
.\nssm.exe set MonitoramentoAgente Description "Monitora cameras IP e envia relatorios"

# Início automático
.\nssm.exe set MonitoramentoAgente Start SERVICE_AUTO_START

# Diretório de trabalho
.\nssm.exe set MonitoramentoAgente AppDirectory "C:\caminho\para\windows"

# Logs
.\nssm.exe set MonitoramentoAgente AppStdout "C:\caminho\para\windows\agent_log.txt"
.\nssm.exe set MonitoramentoAgente AppStderr "C:\caminho\para\windows\agent_error.txt"

# Rotação de logs (1MB)
.\nssm.exe set MonitoramentoAgente AppRotateFiles 1
.\nssm.exe set MonitoramentoAgente AppRotateBytes 1048576
```

### **4. Iniciar o Serviço**

```powershell
.\nssm.exe start MonitoramentoAgente
```

---

## 🐛 **Solução de Problemas**

### **Erro: "Este script precisa ser executado como Administrador"**

**Solução:**
1. Feche o PowerShell
2. Clique com botão direito no PowerShell
3. Selecione **"Executar como Administrador"**
4. Execute o script novamente

### **Erro: "Python não encontrado"**

**Solução:**
1. Instale Python de https://www.python.org/downloads/
2. Durante a instalação, marque **"Add Python to PATH"**
3. Reinicie o PowerShell
4. Execute o script novamente

### **Serviço não inicia**

**Verificar:**

```powershell
# Ver logs de erro
notepad agent_error.txt

# Ver eventos do Windows
eventvwr.msc
# Vá em: Windows Logs > Application
# Procure por erros do MonitoramentoAgente
```

**Causas comuns:**
- Arquivo `agent.json` mal configurado
- Python não instalado corretamente
- Servidor central inacessível
- Firewall bloqueando conexão

### **Serviço para sozinho**

**Configurar reinício automático:**

```powershell
# Via NSSM
.\nssm.exe set MonitoramentoAgente AppExit Default Restart
.\nssm.exe set MonitoramentoAgente AppRestartDelay 5000  # 5 segundos
```

Ou via `services.msc`:
1. Clique com botão direito no serviço
2. Propriedades > Recuperação
3. Configure ações de falha para **"Reiniciar o Serviço"**

### **Atualizar o agente**

Quando houver uma nova versão:

```powershell
# 1. Parar o serviço
sc stop MonitoramentoAgente

# 2. Atualizar arquivos
git pull

# 3. Iniciar o serviço
sc start MonitoramentoAgente
```

**Nota:** O agente tem auto-update, então normalmente não precisa fazer isso manualmente!

---

## 📝 **Checklist de Instalação**

- [ ] Python 3.7+ instalado
- [ ] Arquivo `agent.json` configurado com IP correto do servidor
- [ ] PowerShell aberto como Administrador
- [ ] Script `instalar_servico.ps1` executado
- [ ] Serviço aparece em `services.msc`
- [ ] Status do serviço: **"Em execução"**
- [ ] Tipo de inicialização: **"Automático"**
- [ ] Logs sendo gerados em `agent_log.txt`
- [ ] Agente aparece no dashboard para aprovação

---

## 🎯 **Comandos Rápidos**

```powershell
# Ver status
sc query MonitoramentoAgente

# Parar
sc stop MonitoramentoAgente

# Iniciar
sc start MonitoramentoAgente

# Reiniciar
Restart-Service MonitoramentoAgente

# Ver logs
Get-Content agent_log.txt -Wait -Tail 20

# Desinstalar
.\desinstalar_servico.ps1
```

---

## 🔐 **Segurança**

O serviço roda por padrão com a conta **"Sistema Local"**, que tem privilégios elevados. Para maior segurança:

### **Criar conta de serviço dedicada:**

1. Crie um usuário Windows específico para o serviço
2. Configure o serviço para usar essa conta:

```powershell
# Via services.msc
# Propriedades > Fazer logon > Esta conta
# Digite: DOMINIO\usuario_servico
```

---

## 📚 **Recursos Adicionais**

- **NSSM:** https://nssm.cc/
- **Documentação NSSM:** https://nssm.cc/usage
- **Serviços do Windows:** https://docs.microsoft.com/windows/win32/services/

---

## ✅ **Resumo**

| Ação | Comando |
|------|---------|
| **Instalar** | `.\instalar_servico.ps1` |
| **Desinstalar** | `.\desinstalar_servico.ps1` |
| **Ver status** | `sc query MonitoramentoAgente` |
| **Parar** | `sc stop MonitoramentoAgente` |
| **Iniciar** | `sc start MonitoramentoAgente` |
| **Ver logs** | `notepad agent_log.txt` |

---

**Versão:** 1.0.0  
**Última Atualização:** 24/02/2026  
**Compatibilidade:** Windows 10/11, Windows Server 2016+
