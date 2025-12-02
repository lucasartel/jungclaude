# Guia de Testes - Jung AI (v1.0)

## Status da Implementação

✅ **COMPLETO**: Sistema de exportação de PDF dos relatórios psicométricos
✅ **COMPLETO**: Sistema de autenticação segura com bcrypt
⏳ **PENDENTE**: Testes com usuários reais (aguardando dados psicométricos)

---

## 1. Teste de Autenticação Segura

### Credenciais Geradas

**Usuário**: `admin`
**Senha**: `SenhaSegura2025JungAdmin!`
**Hash bcrypt**: `$2b$12$mip61jYiyzNz9F8AfzsUUOi8gdbYrnqRXu4H1xXV2SMdYhSrhLXNa`

### Configuração no Railway

1. Acesse o projeto no Railway
2. Navegue até **Variables**
3. Adicione/edite as seguintes variáveis:
   ```
   ADMIN_USER=admin
   ADMIN_PASSWORD=$2b$12$mip61jYiyzNz9F8AfzsUUOi8gdbYrnqRXu4H1xXV2SMdYhSrhLXNa
   ```
4. Salve e aguarde o redeploy automático

### Como Testar

1. **Acesse o admin web**: `https://seu-projeto.railway.app/admin`
2. **Login com credenciais antigas (deve falhar)**:
   - Usuário: `admin`
   - Senha: `admin`
   - **Resultado esperado**: ❌ Erro 401 - Credenciais inválidas

3. **Login com credenciais novas (deve funcionar)**:
   - Usuário: `admin`
   - Senha: `SenhaSegura2025JungAdmin!`
   - **Resultado esperado**: ✅ Acesso concedido ao dashboard

### Verificação de Segurança

- ✅ Senha hashada com bcrypt (12 rounds)
- ✅ Comparação timing-safe (previne timing attacks)
- ✅ Hash nunca commitado em código (apenas em variáveis de ambiente)
- ✅ Log de tentativas de autenticação (username apenas, sem senhas)

---

## 2. Teste de Exportação de PDF

### Pré-requisitos

Para testar a exportação de PDF, você precisa de **usuários com dados psicométricos**. Os dados psicométricos são gerados automaticamente após:

- ✅ Mínimo de **10 conversas** com o bot
- ✅ Análise psicométrica completa executada

### Como Verificar se Há Dados Disponíveis

Execute no servidor Railway ou localmente:

```bash
python -c "
import sqlite3
from pathlib import Path

db = sqlite3.connect('data/jung_hybrid.db')
cursor = db.cursor()

cursor.execute('''
    SELECT
        u.user_name,
        u.user_id,
        COUNT(c.id) as conversas,
        p.analysis_date
    FROM users u
    LEFT JOIN conversations c ON u.user_id = c.user_id
    LEFT JOIN user_psychometrics p ON u.user_id = p.user_id
    WHERE p.user_id IS NOT NULL
    GROUP BY u.user_id
''')

users = cursor.fetchall()
for user in users:
    print(f'{user[0]} ({user[1]}): {user[2]} conversas - Análise: {user[3]}')

db.close()
"
```

### Passos para Testar

1. **Acesse a página de psicometria de um usuário**:
   ```
   https://seu-projeto.railway.app/admin/user/{user_id}/psychometrics
   ```

2. **Clique no botão verde "📥 Baixar PDF"**

3. **Verifique o conteúdo do PDF**:
   - ✅ Página de capa com nome do usuário e data
   - ✅ Seção Big Five (OCEAN) com scores e descrições
   - ✅ Seção VARK (estilos de aprendizagem)
   - ✅ Seção EQ (inteligência emocional)
   - ✅ Seção Schwartz Values (valores pessoais)
   - ✅ Rodapé com confidencialidade e LGPD
   - ✅ Formatação profissional (tabelas, cores, branding)

### Exemplo de Usuário com Dados (Simulado)

Se não houver usuários com dados psicométricos, você pode simular adicionando dados manualmente no banco:

```python
# SOMENTE PARA TESTES - NÃO USAR EM PRODUÇÃO
import sqlite3
from datetime import datetime

db = sqlite3.connect('data/jung_hybrid.db')
cursor = db.cursor()

# Adicionar dados psicométricos de teste
cursor.execute('''
    INSERT INTO user_psychometrics (
        user_id, version,
        openness_score, openness_level, openness_description,
        conscientiousness_score, conscientiousness_level, conscientiousness_description,
        extraversion_score, extraversion_level, extraversion_description,
        agreeableness_score, agreeableness_level, agreeableness_description,
        neuroticism_score, neuroticism_level, neuroticism_description,
        big_five_confidence, big_five_interpretation,
        eq_self_awareness, eq_self_management, eq_social_awareness, eq_relationship_management, eq_overall,
        eq_leadership_potential, eq_details,
        vark_visual, vark_auditory, vark_reading, vark_kinesthetic, vark_dominant, vark_recommended_training,
        schwartz_values, schwartz_top_3, schwartz_cultural_fit, schwartz_retention_risk,
        executive_summary, analysis_date, conversations_analyzed, last_updated
    ) VALUES (
        'test_user_123', 1,
        85, 'Alto', 'Mente aberta e criativa',
        75, 'Moderado-Alto', 'Organizado e confiável',
        60, 'Moderado', 'Equilibrado entre introversão e extroversão',
        80, 'Alto', 'Empático e colaborativo',
        40, 'Moderado-Baixo', 'Emocionalmente estável',
        90, 'Perfil analítico e criativo',
        85, 80, 75, 70, 77,
        'Alto potencial de liderança colaborativa', 'Excelente autoconsciência',
        70, 60, 80, 50, 'Visual', 'Recomenda-se uso de diagramas e mapas mentais',
        '{"universalismo": 85, "autodireção": 80, "benevolência": 75}',
        'Universalismo, Autodireção, Benevolência',
        'Alto alinhamento com culturas inovadoras',
        'Baixo - valores alinhados',
        'Profissional com alto potencial analítico e criativo',
        ?, 15, ?
    )
''', (datetime.now(), datetime.now()))

db.commit()
db.close()
```

---

## 3. Checklist Completo de Testes

### Autenticação

- [ ] Login com credenciais antigas falha (admin/admin)
- [ ] Login com novas credenciais funciona
- [ ] Tentativas de login inválidas são logadas
- [ ] Após logout, precisa fazer login novamente
- [ ] Hash bcrypt configurado no Railway (não em código)

### PDF Export

- [ ] Botão "Baixar PDF" aparece na página de psicometria
- [ ] PDF é gerado sem erros
- [ ] Nome do arquivo segue padrão: `relatorio_psicometrico_NomeUsuario_YYYYMMDD.pdf`
- [ ] PDF contém todas as 4 análises (Big Five, VARK, EQ, Schwartz)
- [ ] Formatação está profissional e legível
- [ ] Rodapé com informações de confidencialidade está presente
- [ ] Logo e branding da Jung AI estão corretos

### Fluxo Completo (E2E)

- [ ] Usuário conversa com bot (mínimo 10 conversas)
- [ ] Análise psicométrica é gerada automaticamente
- [ ] Admin acessa painel web com autenticação segura
- [ ] Admin visualiza dados psicométricos do usuário
- [ ] Admin exporta PDF com sucesso
- [ ] PDF pode ser aberto e lido corretamente

---

## 4. Problemas Conhecidos e Soluções

### Problema: "No module named 'ReportLab'"

**Solução**: Instalar dependência
```bash
pip install reportlab
```

Já está incluído em `requirements.txt`, mas certifique-se de que o Railway executou `pip install -r requirements.txt`.

### Problema: "User has no psychometric data"

**Solução**: O usuário precisa ter pelo menos 10 conversas para que a análise psicométrica seja gerada. Verifique com:

```python
SELECT COUNT(*) FROM conversations WHERE user_id = 'seu_user_id';
```

### Problema: PDF está vazio ou incompleto

**Solução**: Verifique se todos os campos psicométricos estão preenchidos no banco:

```sql
SELECT * FROM user_psychometrics WHERE user_id = 'seu_user_id';
```

Se algum campo estiver NULL, a análise psicométrica pode precisar ser re-executada.

---

## 5. Próximos Passos

Após completar os testes acima:

1. **Coletar feedback de 3-5 usuários internos**
   - Qualidade das análises psicométricas
   - Usabilidade do PDF
   - Sugestões de melhorias

2. **Implementar sistema de evidências**
   - Mostrar trechos de conversas que suportam cada score
   - Link para conversas originais

3. **Dashboard para RH**
   - Comparação entre candidatos
   - Filtros por características
   - Exportação em lote

4. **Validar decisão sobre sistema de ruminação**
   - Avaliar se há demanda real
   - Testar com usuários beta

---

## 6. Contatos e Suporte

**Repositório**: [GitHub - jungclaude](https://github.com/lucasartel/jungclaude)
**Ambiente de Produção**: Railway
**Última atualização**: 2025-12-01

---

**Status Atual**: ✅ Código completo e funcionando | ⏳ Aguardando dados de usuários para testes completos
