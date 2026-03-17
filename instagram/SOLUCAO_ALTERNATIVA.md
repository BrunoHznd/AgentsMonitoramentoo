# 🔧 Solução Alternativa - Login com Cookies

O Instagram está bloqueando login via instagrapi. Use esta solução alternativa.

## 📋 Método: Exportar Cookies do Navegador

### **Passo 1: Instalar Extensão**

1. Abra o navegador (Chrome/Firefox)
2. Instale a extensão **"EditThisCookie"** ou **"Cookie-Editor"**
   - Chrome: https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg
   - Firefox: https://addons.mozilla.org/firefox/addon/cookie-editor/

### **Passo 2: Fazer Login Manual**

1. Acesse https://www.instagram.com/
2. Faça login com **testesdiariosbots**
3. Complete qualquer verificação que pedir

### **Passo 3: Exportar Cookies**

1. Com o Instagram aberto e logado
2. Clique no ícone da extensão de cookies
3. Clique em "Export" ou "Export Cookies"
4. Copie o JSON gerado

### **Passo 4: Salvar Cookies**

Crie o arquivo `cookies.json` em `/root/Desktop/monitoramento/agents/instagram/`:

```json
{
  "cookies": [
    // Cole aqui os cookies exportados
  ]
}
```

### **Passo 5: Usar Script com Cookies**

Execute:
```bash
cd /root/Desktop/monitoramento/agents/instagram
python3 login_with_cookies.py
```

---

## 🎯 Alternativa Mais Simples: Usar Conta Antiga

Se você tiver uma conta do Instagram **mais antiga** (criada há mais de 1 mês), ela tem mais chances de funcionar.

**Requisitos:**
- Conta criada há pelo menos 1 mês
- Tem alguns posts/seguidores
- Nunca foi suspensa
- 2FA desativado

---

## ⚠️ Por que o Instagram Bloqueia?

1. **Contas novas** (< 1 semana) são bloqueadas
2. **Apps não oficiais** são detectados
3. **Muitas tentativas** de login
4. **Sem atividade humana** (posts, stories, etc)

---

## 💡 Recomendação Final

**Opção 1:** Use conta antiga existente (mais fácil)
**Opção 2:** Aguarde 1-2 semanas com a conta nova
**Opção 3:** Use cookies do navegador (método acima)

Qual opção você prefere?
