# 🔄 Como Alternar Entre Grok e Claude

## 📋 Visão Geral

O sistema agora suporta alternância fácil entre dois provedores de LLM:

- **Grok (xAI)** - Modelo atual: `grok-4-fast-reasoning`
- **Claude (Anthropic)** - Modelo: `claude-3-5-haiku-20241022` (mais barato)

A alternância é feita via variável de ambiente `LLM_PROVIDER` no arquivo `.env`.

---

## ⚡ Como Alternar (Passo a Passo)

### **Opção 1: Usar Grok (Padrão Atual)**

1. Abra o arquivo `.env`
2. Adicione ou edite a linha:
   ```env
   LLM_PROVIDER=grok
   ```
3. Salve o arquivo
4. Reinicie o bot (no Railway, basta fazer um novo deploy ou usar o botão "Restart")

✅ **Resultado:** Todas as respostas usarão Grok (xAI)

---

### **Opção 2: Usar Claude**

1. Abra o arquivo `.env`
2. Adicione ou edite a linha:
   ```env
   LLM_PROVIDER=claude
   ```
3. Salve o arquivo
4. Reinicie o bot (no Railway, basta fazer um novo deploy ou usar o botão "Restart")

✅ **Resultado:** Todas as respostas usarão Claude (Anthropic)

---

## 🔧 Configuração do `.env`

Seu arquivo `.env` deve ter estas variáveis:

```env
# LLM Provider (grok ou claude)
LLM_PROVIDER=grok

# API Keys
XAI_API_KEY=xai-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Outras variáveis (OpenAI para embeddings, Telegram, etc.)
OPENAI_API_KEY=sk-proj-your-key-here
TELEGRAM_BOT_TOKEN=your-token-here
```

---

## 📊 Comparação: Grok vs Claude

| Característica | Grok | Claude |
|----------------|------|--------|
| **Modelo** | grok-4-fast-reasoning | claude-3-5-haiku-20241022 |
| **Custo** | Médio | **Mais barato** |
| **Velocidade** | Rápido | **Muito rápido** |
| **Contexto** | Até 128k tokens | Até 200k tokens |
| **Qualidade** | Excelente | Excelente |
| **Uso atual** | ✅ Padrão | Alternativa |

---

## 🚀 Deploy no Railway

### Se você alterar no `.env` local:

1. **Edite o `.env` local**:
   ```env
   LLM_PROVIDER=claude  # ou grok
   ```

2. **Commit e push**:
   ```bash
   git add .env
   git commit -m "config: Switch to Claude provider"
   git push
   ```

3. **Railway fará deploy automático**

### Se você alterar direto no Railway:

1. Acesse o dashboard do Railway
2. Vá em **Variables**
3. Adicione ou edite a variável:
   - Nome: `LLM_PROVIDER`
   - Valor: `claude` (ou `grok`)
4. Clique em **Restart** (ou aguarde deploy automático)

---

## 📝 Exemplo de Uso no Código

O código já foi atualizado automaticamente! A função `send_to_xai()` agora usa a abstração:

```python
from jung_core import send_to_xai

# Isso automaticamente usa Grok ou Claude conforme LLM_PROVIDER
response = send_to_xai(
    prompt="Explique arquétipos junguianos",
    temperature=0.7,
    max_tokens=2000
)
```

**Não é necessário alterar NENHUM código!** Apenas mude a variável `LLM_PROVIDER` no `.env`.

---

## 🔍 Como Verificar Qual LLM Está Ativo

Após iniciar o bot, veja os logs:

**Se estiver usando Grok:**
```
✅ GrokProvider inicializado (modelo: grok-4-fast-reasoning)
✅ LLM Provider ativado: Grok (grok-4-fast-reasoning)
```

**Se estiver usando Claude:**
```
✅ ClaudeProvider inicializado (modelo: claude-3-5-haiku-20241022)
✅ LLM Provider ativado: Claude (claude-3-5-haiku-20241022)
```

---

## ⚠️ Requisitos

### Para usar Claude:

1. **Biblioteca Anthropic instalada:**
   ```bash
   pip install anthropic>=0.40.0
   ```

   (Já adicionada ao `requirements.txt` - Railway instala automaticamente)

2. **API Key válida no `.env`:**
   ```env
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

### Para usar Grok:

1. **API Key válida no `.env`:**
   ```env
   XAI_API_KEY=xai-...
   ```

---

## 🐛 Solução de Problemas

### Erro: "ANTHROPIC_API_KEY não encontrado"

**Causa:** Você configurou `LLM_PROVIDER=claude` mas não tem a chave da API.

**Solução:**
1. Adicione `ANTHROPIC_API_KEY` no `.env`
2. Ou volte para Grok: `LLM_PROVIDER=grok`

### Erro: "XAI_API_KEY não encontrado"

**Causa:** Você configurou `LLM_PROVIDER=grok` mas não tem a chave da API.

**Solução:**
1. Adicione `XAI_API_KEY` no `.env`
2. Ou mude para Claude: `LLM_PROVIDER=claude`

### Erro: "Biblioteca 'anthropic' não instalada"

**Causa:** Você não instalou a biblioteca anthropic.

**Solução:**
```bash
pip install anthropic
```

Ou no Railway, adicione ao `requirements.txt`:
```
anthropic>=0.40.0
```

---

## 💰 Recomendação de Uso

### Para Produção (Usuários Reais):
- **Recomendado:** Claude Haiku (`LLM_PROVIDER=claude`)
- **Motivo:** Mais barato, resposta rápida, qualidade excelente

### Para Testes/Desenvolvimento:
- **Recomendado:** Grok (`LLM_PROVIDER=grok`)
- **Motivo:** Modelo que você já conhece bem

### Para Economizar Custos:
- **Use Claude** - Modelo Haiku é significativamente mais barato

---

## 📦 Arquivos Alterados

1. **`llm_providers.py`** (NOVO) - Abstração de provedores LLM
2. **`jung_core.py`** - Função `send_to_xai()` atualizada
3. **`requirements.txt`** - Adicionada biblioteca `anthropic`
4. **`.env`** - Nova variável `LLM_PROVIDER`

**Nenhum outro arquivo foi modificado!** O resto do código continua funcionando normalmente.

---

## ✅ Checklist de Deploy

- [ ] Biblioteca `anthropic` instalada (`pip install anthropic`)
- [ ] Variável `LLM_PROVIDER` adicionada ao `.env` (Railway Variables)
- [ ] API Keys válidas para ambos os provedores (Grok e Claude)
- [ ] Bot reiniciado após mudança de variável
- [ ] Logs verificados para confirmar provider ativo

---

## 🎯 Resumo Ultra-Rápido

**Quer usar Claude?**
```env
LLM_PROVIDER=claude
```

**Quer usar Grok?**
```env
LLM_PROVIDER=grok
```

**É só isso!** Reinicie o bot e pronto. 🚀

---

**Última atualização:** 2025-11-27
**Autor:** Sistema Jung Claude
