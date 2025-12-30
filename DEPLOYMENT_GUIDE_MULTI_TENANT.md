# 🚀 Guia de Deployment - Sistema Multi-Tenant

## ✅ Status Atual

**Código pronto para deploy!** Todos os arquivos do sistema multi-tenant foram criados e enviados ao Railway.

---

## 📋 Checklist Pré-Deploy

- [x] Schema multi-tenant criado ([admin_web/database/multi_tenant_schema.py](admin_web/database/multi_tenant_schema.py))
- [x] Script SQL de migração criado ([migrations/multi_tenant_migration.sql](migrations/multi_tenant_migration.sql))
- [x] Sistema de autenticação implementado (AuthManager, SessionManager, PermissionManager)
- [x] Middleware de autorização criado ([admin_web/auth/middleware.py](admin_web/auth/middleware.py))
- [x] Template de login criado ([admin_web/templates/auth/login.html](admin_web/templates/auth/login.html))
- [x] Rotas de autenticação criadas ([admin_web/routes/auth_routes.py](admin_web/routes/auth_routes.py))
- [x] Sistema de migração web criado ([migrations/run_migration_web.py](migrations/run_migration_web.py))
- [x] Rota temporária de migração criada ([admin_web/routes/migration_route.py](admin_web/routes/migration_route.py))
- [x] Rota de migração integrada em [main.py](main.py)
- [x] Código commitado e enviado ao GitHub
- [x] Deploy automático ativado no Railway

---

## 🎯 Passo a Passo de Execução

### **FASE 1: Aguardar Deploy no Railway**

1. **Verificar logs do Railway**
   - Acesse o dashboard do Railway
   - Aguarde o build completar (pode levar 2-3 minutos)
   - Verifique se há erros nos logs

2. **Confirmar que a aplicação subiu**
   - Acesse: `https://seu-app.railway.app/health`
   - Deve retornar: `{"status": "healthy", ...}`

3. **Confirmar que a rota de migração está ativa**
   - Procure nos logs do Railway por:
     ```
     ✅ Rota de migração multi-tenant carregada
     ⚠️  LEMBRETE: Remover migration_route após executar a migração!
     ```

---

### **FASE 2: Executar Migração via Browser**

4. **Acessar formulário de migração**
   - URL: `https://seu-app.railway.app/admin/run-migration`
   - Você verá uma página bonita com gradiente roxo
   - Leia os avisos com atenção

5. **Preencher o formulário**

   **Email do Usuário Master:**
   - Use seu email real
   - Exemplo: `seu@email.com`
   - Este será seu login no sistema

   **Senha do Usuário Master:**
   - Escolha uma senha FORTE (mínimo 8 caracteres)
   - Exemplo: `SenhaForte123!`
   - **IMPORTANTE:** Anote esta senha em local seguro!

   **Nome Completo:**
   - Seu nome ou "Master Admin"
   - Este campo é opcional

6. **Executar a migração**
   - Clique em "Executar Migração"
   - Aguarde 10-30 segundos (não feche a página!)
   - Você verá uma animação de loading

7. **Verificar resultado**

   **Se deu certo:**
   - Página mostrará logs em verde
   - Mensagem: "🎉 Migração concluída com sucesso!"
   - Resumo:
     ```
     ✅ Backup criado
     ✅ 5 tabelas criadas
     ✅ Usuários migrados para organização Default
     ✅ Usuário Master criado
     ✅ Validação OK
     ```

   **Se deu errado:**
   - Página mostrará logs em vermelho
   - Erro detalhado será exibido
   - Backup será restaurado automaticamente
   - Você pode tentar novamente

---

### **FASE 3: Testar Login**

8. **Acessar página de login**
   - URL: `https://seu-app.railway.app/admin/login`
   - Você verá uma página limpa com logo "🧠 JungAgent"

9. **Fazer login**
   - Digite o email que você criou
   - Digite a senha que você criou
   - Clique em "Entrar"

10. **Verificar redirecionamento**
    - Como Master Admin, você será redirecionado para:
      - `/admin/master/dashboard` (ainda não implementado)
    - **IMPORTANTE:** Você verá erro 404 porque o dashboard ainda não existe
    - Isso é NORMAL! Significa que o login funcionou!

---

### **FASE 4: Remover Rota de Migração (CRÍTICO!)**

⚠️ **MUITO IMPORTANTE:** A rota de migração é um **risco de segurança grave**. Ela permite que qualquer pessoa execute a migração novamente e crie usuários master!

11. **Editar [main.py](main.py:1072-1079)**
    - Remover ou comentar estas linhas:
    ```python
    # ⚠️ TEMPORÁRIO: Rota de migração multi-tenant (REMOVER APÓS MIGRAÇÃO!)
    try:
        from admin_web.routes.migration_route import router as migration_router
        app.include_router(migration_router)
        logger.info("✅ Rota de migração multi-tenant carregada")
        logger.warning("⚠️  LEMBRETE: Remover migration_route após executar a migração!")
    except Exception as e:
        logger.warning(f"⚠️  Rota de migração não disponível: {e}")
    ```

12. **Fazer commit e push**
    ```bash
    git add main.py
    git commit -m "security: Remove temporary migration route after successful migration"
    git push
    ```

13. **Aguardar novo deploy no Railway**
    - Deploy automático será ativado
    - Aguarde 2-3 minutos

14. **Confirmar remoção**
    - Tente acessar: `https://seu-app.railway.app/admin/run-migration`
    - Deve retornar erro 404
    - Isso é bom! Significa que a rota foi removida com sucesso

---

## 🔍 Validação Final

### ✅ Sistema funcionando se:

- [ ] `/health` retorna status healthy
- [ ] `/admin/login` mostra página de login
- [ ] Login com credenciais master funciona
- [ ] Cookie de sessão é criado (verificar no DevTools)
- [ ] Após login, você é redirecionado para `/admin/master/dashboard`
- [ ] Rota `/admin/run-migration` retorna 404 (após remoção)

### 🗄️ Banco de Dados

Para verificar se a migração funcionou:

1. **Conectar ao banco Railway**
   ```bash
   railway connect
   sqlite3 /app/jung_memory.db
   ```

2. **Verificar tabelas criadas**
   ```sql
   .tables
   -- Deve mostrar: organizations, admin_users, user_organization_mapping, admin_sessions, audit_log
   ```

3. **Verificar organização default**
   ```sql
   SELECT * FROM organizations;
   -- Deve mostrar: org_id=default, org_name=Default
   ```

4. **Verificar usuário master**
   ```sql
   SELECT admin_id, email, full_name, role FROM admin_users;
   -- Deve mostrar seu email com role=master
   ```

5. **Verificar usuários migrados**
   ```sql
   SELECT COUNT(*) FROM user_organization_mapping WHERE org_id = 'default';
   -- Deve mostrar número de usuários do sistema
   ```

---

## 🛠️ Próximas Implementações

Após validar que o sistema multi-tenant está funcionando:

### **Fase 2: Dashboards**

1. **Master Dashboard** ([admin_web/routes/master_routes.py](admin_web/routes/master_routes.py))
   - Listar todas as organizações
   - Criar/editar/deletar organizações
   - Listar todos os admins
   - Criar org admins para organizações
   - Ver estatísticas globais

2. **Org Admin Dashboard** ([admin_web/routes/org_routes.py](admin_web/routes/org_routes.py))
   - Ver usuários da organização
   - Ver estatísticas de conversas
   - Exportar relatórios
   - Gerenciar time

### **Fase 3: Visualizações**

- Perfil psicométrico de usuários
- Histórico de conversas
- Jung Mind (já implementado, apenas integrar)
- Sistema de evidências

### **Fase 4: Recursos Avançados**

- Webhooks para eventos
- API pública com autenticação JWT
- Sistema de billing (Stripe)
- Limites por organização (quotas)

---

## 📞 Troubleshooting

### **Problema: Página de migração não carrega**

**Causa:** Rota não foi incluída corretamente
**Solução:** Verificar logs do Railway. Deve aparecer:
```
✅ Rota de migração multi-tenant carregada
```

Se não aparecer, verificar se o arquivo [migrations/run_migration_web.py](migrations/run_migration_web.py) foi enviado ao Railway.

---

### **Problema: Migração retorna erro "Migration failed"**

**Causa:** Banco de dados já tem tabelas multi-tenant
**Solução:** Se você já rodou a migração antes, ela falhará. Verifique:
```sql
.tables
-- Se aparecer 'organizations', a migração já foi executada
```

Para resetar (CUIDADO - APAGA DADOS!):
```sql
DROP TABLE IF EXISTS organizations;
DROP TABLE IF EXISTS admin_users;
DROP TABLE IF EXISTS user_organization_mapping;
DROP TABLE IF EXISTS admin_sessions;
DROP TABLE IF EXISTS audit_log;
```

Depois rode a migração novamente.

---

### **Problema: Login não funciona (credenciais incorretas)**

**Possíveis causas:**

1. **Email digitado errado** - Verifique capitalização
2. **Senha digitada errada** - Verifique Caps Lock
3. **Usuário master não foi criado** - Verifique no banco:
   ```sql
   SELECT * FROM admin_users;
   ```

**Solução:** Se o usuário não existe, rode a migração novamente.

---

### **Problema: Após login, erro 404**

**Isso é NORMAL!** O dashboard ainda não foi implementado. Significa que:
- ✅ Login funcionou
- ✅ Sessão foi criada
- ✅ Cookie foi definido
- ❌ Dashboard não existe ainda

**Para confirmar que o login funcionou:**
1. Abra DevTools (F12) → Application → Cookies
2. Procure por `session_id`
3. Se existir, o login funcionou!

---

### **Problema: Erro "bcrypt module not found"**

**Causa:** Biblioteca bcrypt não está instalada
**Solução:** Verificar se `bcrypt>=4.0.0` está em [requirements.txt](requirements.txt)

Se não estiver, adicione:
```
bcrypt>=4.0.0
```

Depois commit e push.

---

### **Problema: Erro de permissão no banco de dados**

**Causa:** Railway pode ter restrições de escrita
**Solução:** Verificar que `DATABASE_PATH` está definido corretamente. O Railway usa `/app/jung_memory.db` por padrão.

---

## 📊 Estrutura das Tabelas

### **organizations**
```sql
org_id TEXT PRIMARY KEY              -- UUID da org
org_name TEXT NOT NULL                -- Nome da org
org_slug TEXT UNIQUE                  -- Slug para URLs
is_active BOOLEAN DEFAULT 1           -- Org ativa?
max_users INTEGER DEFAULT 100         -- Limite de usuários
created_at DATETIME                   -- Data de criação
```

### **admin_users**
```sql
admin_id TEXT PRIMARY KEY             -- UUID do admin
email TEXT UNIQUE NOT NULL            -- Email de login
password_hash TEXT NOT NULL           -- bcrypt hash
full_name TEXT                        -- Nome completo
role TEXT NOT NULL                    -- master ou org_admin
org_id TEXT                           -- NULL se master
is_active BOOLEAN DEFAULT 1           -- Admin ativo?
created_at DATETIME                   -- Data de criação
last_login DATETIME                   -- Último login
```

### **user_organization_mapping**
```sql
id INTEGER PRIMARY KEY                -- ID sequencial
user_id TEXT NOT NULL                 -- ID do usuário (users table)
org_id TEXT NOT NULL                  -- ID da org
joined_at DATETIME                    -- Data de vínculo
```

### **admin_sessions**
```sql
session_id TEXT PRIMARY KEY           -- UUID da sessão
admin_id TEXT NOT NULL                -- ID do admin
ip_address TEXT                       -- IP do login
user_agent TEXT                       -- Browser
created_at DATETIME                   -- Criação da sessão
expires_at DATETIME                   -- Expiração (24h)
is_active BOOLEAN DEFAULT 1           -- Sessão ativa?
last_activity DATETIME                -- Última atividade
```

### **audit_log**
```sql
id INTEGER PRIMARY KEY                -- ID sequencial
admin_id TEXT                         -- ID do admin
action TEXT NOT NULL                  -- Ação executada
resource_type TEXT                    -- Tipo de recurso
resource_id TEXT                      -- ID do recurso
details TEXT                          -- JSON com detalhes
ip_address TEXT                       -- IP da ação
timestamp DATETIME                    -- Quando aconteceu
```

---

## 🎯 Resumo Executivo

### **Você está em:** Fase 1 - Deployment Inicial

**Próximos passos:**
1. ⏳ Aguardar deploy no Railway
2. 🌐 Acessar `/admin/run-migration`
3. ✍️ Preencher formulário e criar Master Admin
4. 🔒 Testar login em `/admin/login`
5. 🗑️ Remover rota de migração
6. ✅ Validar sistema

**Depois disso:**
- Implementar Master Dashboard
- Implementar Org Admin Dashboard
- Integrar visualizações existentes

---

## 📚 Documentação Completa

Para entender toda a arquitetura, leia:
- [docs/MULTI_TENANT_IMPLEMENTATION.md](docs/MULTI_TENANT_IMPLEMENTATION.md) - Documentação técnica completa

---

## 🆘 Suporte

Se encontrar problemas:

1. **Verificar logs do Railway** - 90% dos problemas aparecem lá
2. **Verificar se bcrypt está instalado** - `pip list | grep bcrypt`
3. **Verificar estrutura do banco** - `.tables` no SQLite
4. **Verificar se a migração rodou** - Procurar por "🎉 Migração concluída"

---

**Sucesso! 🎉** Você está pronto para transformar o JungAgent em um SaaS multi-tenant completo!
