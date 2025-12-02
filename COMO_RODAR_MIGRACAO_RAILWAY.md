# Como Executar a Migração de Evidências no Railway

## Método Simples (Recomendado) - Via Endpoint POST

A migração agora pode ser executada **diretamente pelo navegador** através de um endpoint HTTP.

### Passo 1: Fazer Deploy do Código

```bash
git add .
git commit -m "feat: Add Evidence System 2.0 with migration endpoint"
git push
```

O Railway fará deploy automaticamente.

### Passo 2: Executar a Migração

**Opção A: Via cURL (Terminal/CMD)**

```bash
curl -X POST https://seu-projeto.railway.app/admin/migrate/evidence
```

**Opção B: Via Navegador (Postman/Insomnia)**

1. Abra Postman ou Insomnia
2. Crie uma requisição **POST**
3. URL: `https://seu-projeto.railway.app/admin/migrate/evidence`
4. Clique em "Send"

**Opção C: Via Python**

```python
import requests

url = "https://seu-projeto.railway.app/admin/migrate/evidence"
response = requests.post(url)
print(response.json())
```

**Opção D: Via PowerShell (Windows)**

```powershell
Invoke-WebRequest -Uri "https://seu-projeto.railway.app/admin/migrate/evidence" -Method POST
```

### Passo 3: Verificar Resultado

A resposta será um JSON:

**Sucesso (Primeira Execução)**:
```json
{
    "status": "success",
    "message": "Evidence System 2.0 migration executed successfully",
    "migration_executed": true,
    "changes": [
        "psychometric_evidence table created",
        "idx_evidence_user_dimension index created",
        "idx_evidence_conversation index created",
        "idx_evidence_version index created",
        "idx_evidence_direction index created",
        "conversations_used column added to user_psychometrics",
        "evidence_extracted column added to user_psychometrics",
        "evidence_extraction_date column added to user_psychometrics",
        "red_flags column added to user_psychometrics"
    ],
    "next_steps": [
        "1. Sistema de evidências está pronto",
        "2. Evidências serão extraídas on-demand quando visualizadas",
        "3. Cache automático para visualizações futuras"
    ]
}
```

**Sucesso (Já Executada)**:
```json
{
    "status": "success",
    "message": "Tabela 'psychometric_evidence' já existe. Nada a fazer.",
    "migration_executed": false
}
```

**Erro**:
```json
{
    "status": "error",
    "error": "Mensagem de erro detalhada",
    "message": "Migration failed - database rolled back"
}
```

### Passo 4: Testar o Sistema

Após a migração bem-sucedida:

1. Acesse: `https://seu-projeto.railway.app/admin`
2. Faça login com suas credenciais
3. Escolha um usuário com análise psicométrica
4. Clique em "Ver Evidências" em qualquer dimensão Big Five
5. Aguarde ~30s (primeira vez) para extração
6. Evidências aparecerão com citações literais

---

## Método Alternativo - Via Railway Console

Se preferir executar manualmente:

### Passo 1: Abrir Railway Console

1. Acesse [Railway Dashboard](https://railway.app/)
2. Selecione seu projeto
3. Clique na aba "Deploy"
4. Role para baixo e clique em "Shell" ou "Console"

### Passo 2: Executar Script Python

No console do Railway, execute:

```bash
python migrate_add_evidence_table.py
```

Saída esperada:
```
======================================================================
MIGRATION: Sistema de Evidências 2.0
======================================================================

Conectando ao banco: /data/jung_hybrid.db

Criando tabela 'psychometric_evidence'...
  [OK] Tabela criada com sucesso

Criando índices de performance...
  [OK] Índice: idx_evidence_user_dimension
  [OK] Índice: idx_evidence_conversation
  [OK] Índice: idx_evidence_version
  [OK] Índice: idx_evidence_direction

Atualizando tabela 'user_psychometrics'...
  [OK] Coluna 'conversations_used' adicionada
  [OK] Coluna 'evidence_extracted' adicionada
  [OK] Coluna 'evidence_extraction_date' adicionada
  [OK] Coluna 'red_flags' adicionada

======================================================================
MIGRACAO CONCLUIDA COM SUCESSO!
======================================================================

Sistema de Evidencias 2.0 esta pronto para uso.

Proximos passos:
1. Executar analises psicometricas normalmente
2. Evidencias serao extraidas on-demand quando visualizadas
3. Cache automatico para visualizacoes futuras
```

---

## Verificação de Logs

Para ver se a migração foi executada, verifique os logs do Railway:

```bash
railway logs
```

Procure por:
```
🔧 Executando migração do Sistema de Evidências 2.0...
  ✓ Tabela 'psychometric_evidence' criada
  ✓ Índice: idx_evidence_user_dimension
  ...
✅ Migração do Sistema de Evidências 2.0 concluída com sucesso!
```

---

## Troubleshooting

### Erro: "Migration failed - database rolled back"

**Possível Causa**: Tabela já existe ou erro de sintaxe SQL

**Solução**: Verifique os logs detalhados no Railway

### Erro: Connection timeout

**Possível Causa**: Servidor está sendo reiniciado

**Solução**: Aguarde 1-2 minutos e tente novamente

### Erro: 404 Not Found

**Possível Causa**: Deploy não foi concluído

**Solução**:
1. Verifique se o código foi commitado e pushed
2. Aguarde o deploy terminar no Railway
3. Verifique se a URL está correta

---

## FAQ

**P: Posso executar a migração múltiplas vezes?**
R: Sim! O endpoint verifica se a tabela já existe e não faz nada se já estiver criada.

**P: A migração vai apagar dados existentes?**
R: Não. Ela apenas cria novas tabelas e colunas. Dados existentes são preservados.

**P: Preciso parar o bot para executar a migração?**
R: Não. A migração pode ser executada com o bot rodando.

**P: E se algo der errado?**
R: A migração usa transações SQL. Se algo falhar, tudo é revertido (rollback).

---

## Próximos Passos Após Migração

1. ✅ Migração executada com sucesso
2. ✅ Sistema de evidências está ativo
3. ⏳ Testar com usuário real no admin web
4. ⏳ Verificar se extração on-demand funciona
5. ⏳ Confirmar cache está funcionando
6. ⏳ Implementar red flags (próxima tarefa)

---

**Criado**: 2025-12-02
**Última atualização**: 2025-12-02
