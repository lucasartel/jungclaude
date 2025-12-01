# 🗺️ ROADMAP - Projeto Jung
## Planejamento Estratégico de Desenvolvimento

**Última atualização:** 2025-11-29
**Status atual:** Beta em testes internos

---

## 📊 Status Atual do Projeto

### ✅ Funcionalidades Implementadas

#### Core do Sistema
- ✅ Arquitetura híbrida (SQLite + ChromaDB)
- ✅ Sistema de embeddings com OpenAI
- ✅ Abstração de LLM providers (Grok/Claude)
- ✅ Desenvolvimento progressivo do agente
- ✅ Extração automática de fatos estruturados
- ✅ Detecção de padrões comportamentais

#### Bot Telegram
- ✅ Sistema de consentimento LGPD completo
- ✅ Comandos básicos (/start, /help, /stats, /mbti, /desenvolvimento)
- ✅ Histórico de conversas com contexto
- ✅ Sistema de reset de dados

#### Sistema Proativo
- ✅ Mensagens proativas personalizadas
- ✅ Scheduler com verificação a cada 30 minutos
- ✅ Cooldown entre mensagens (6h)
- ✅ Personalidades arquetípicas rotativas
- ✅ Correção de timezone (UTC)

#### Análises Psicométricas
- ✅ Big Five (OCEAN) com Claude Sonnet 4.5
- ✅ Inteligência Emocional (EQ)
- ✅ VARK (Estilos de Aprendizagem)
- ✅ Valores de Schwartz
- ✅ Parser robusto de JSON
- ✅ Cache de análises no banco

#### Interface Admin Web
- ✅ Dashboard de usuários
- ✅ Visualização de conversas
- ✅ Análises psicométricas
- ✅ Desenvolvimento do agente
- ✅ Autenticação básica (admin/admin)
- ✅ Endpoints de diagnóstico

#### DevOps
- ✅ Deploy automatizado no Railway
- ✅ Variáveis de ambiente configuradas
- ✅ Migrations de banco de dados
- ✅ Logs estruturados
- ✅ Endpoints de health check

---

## 🎯 Próximos Passos (Prioridades)

### 🔴 ALTA PRIORIDADE (Próximas 1-2 semanas)

#### 1. Preparação para Apresentação RH
**Prazo:** Urgente
**Objetivo:** Sistema pronto para demonstração profissional

**Tarefas:**
- [ ] **Relatórios PDF Exportáveis**
  - [ ] Criar template PDF profissional
  - [ ] Incluir todas as 4 análises psicométricas
  - [ ] Adicionar evidências concretas das conversas
  - [ ] Gráficos e visualizações
  - [ ] Logo e branding
  - [ ] Botão de download no admin web

- [ ] **Melhorias no Admin Web**
  - [ ] Dashboard de RH específico
  - [ ] Filtros e busca de usuários
  - [ ] Comparação entre candidatos
  - [ ] Autenticação robusta (trocar admin/admin)
  - [ ] Permissões por role (admin vs RH viewer)

- [ ] **Sistema de Evidências**
  - [ ] Mostrar citações literais que embasam scores
  - [ ] Destacar padrões linguísticos relevantes
  - [ ] Timeline de evolução de traits
  - [ ] Detecção de inconsistências (red flags)

#### 2. Testes Internos e Refinamento
**Prazo:** Esta semana
**Objetivo:** Validar com usuários reais antes do RH

**Tarefas:**
- [ ] Coletar feedback de 5-10 usuários internos
- [ ] Identificar bugs e edge cases
- [ ] Ajustar prompts baseado em feedback
- [ ] Medir tempo de resposta e performance
- [ ] Testar fluxo completo (onboarding → análise)

#### 3. Compliance LGPD
**Prazo:** Antes da apresentação RH
**Objetivo:** Garantir conformidade legal total

**Tarefas:**
- [ ] Revisar termos de consentimento com jurídico
- [ ] Implementar logs de auditoria
- [ ] Criar política de retenção de dados
- [ ] Adicionar opção de exportar dados pessoais
- [ ] Documentar processos de segurança

---

### 🟡 MÉDIA PRIORIDADE (2-4 semanas)

#### 4. Sistema de Rumination (Opcional)
**Referência:** `docs/SISTEMA_RUMINACAO_v1.md`
**Decisão:** Implementar APENAS após beta com RH

**Tarefas (SE aprovado após beta):**
- [ ] Implementar ciclos de rumination de 3 dias
- [ ] Sistema de latent insights
- [ ] Processo multi-passo de maturação
- [ ] Validação com dados reais de usuários
- [ ] A/B test: rumination vs análise direta

#### 5. Melhorias de Conversação
**Objetivo:** Conversas mais naturais e envolventes

**Tarefas:**
- [ ] Ajustar tamanho de respostas (já em 3-5 frases)
- [ ] Adicionar mais variação nas vozes arquetípicas
- [ ] Melhorar detecção de contexto emocional
- [ ] Implementar follow-up questions inteligentes
- [ ] Sistema de pequenos talk quando apropriado

#### 6. Dashboard de Métricas
**Objetivo:** Monitoramento de saúde do sistema

**Tarefas:**
- [ ] Taxa de engajamento (conversas/dia por usuário)
- [ ] Tempo médio de resposta
- [ ] Taxa de erro de LLM providers
- [ ] Custos de API (Grok vs Claude vs OpenAI)
- [ ] Qualidade das análises (feedback dos usuários)
- [ ] Alertas automáticos para anomalias

---

### 🟢 BAIXA PRIORIDADE (1-2 meses)

#### 7. Integrações Externas
**Tarefas:**
- [ ] LinkedIn para enriquecimento de perfil
- [ ] WhatsApp como canal alternativo
- [ ] Slack para empresas
- [ ] API pública para parceiros RH
- [ ] Webhook para notificações

#### 8. Multi-idioma
**Tarefas:**
- [ ] Suporte a Inglês
- [ ] Suporte a Espanhol
- [ ] Sistema de detecção automática de idioma
- [ ] Tradução de relatórios

#### 9. Mobile App
**Tarefas:**
- [ ] Avaliar necessidade (Telegram já é mobile)
- [ ] React Native ou Flutter
- [ ] Push notifications nativas
- [ ] Interface otimizada para mobile

---

## 🧪 Backlog Técnico

### Otimizações de Performance
- [ ] Implementar cache Redis para análises
- [ ] Otimizar queries SQL com índices
- [ ] Lazy loading no admin web
- [ ] Compressão de embeddings
- [ ] Rate limiting inteligente

### Melhorias de Código
- [ ] Adicionar testes unitários (pytest)
- [ ] Testes de integração end-to-end
- [ ] Refatorar jung_core.py (muito grande)
- [ ] Documentação de API com OpenAPI/Swagger
- [ ] Type hints completos

### Segurança
- [ ] Implementar rate limiting por usuário
- [ ] Criptografia de dados sensíveis no banco
- [ ] Rotação de tokens de API
- [ ] Pen test antes de escalar
- [ ] Backup automatizado do banco

---

## 📈 Métricas de Sucesso

### Para Beta com RH
- [ ] 20+ conversas por usuário de teste
- [ ] 90%+ de confiança nas análises Big Five
- [ ] Feedback positivo de 80%+ dos testadores
- [ ] Tempo de resposta < 3s
- [ ] Zero erros de parse JSON
- [ ] 100% de uptime durante demonstração

### Para Lançamento Público
- [ ] 100+ usuários ativos
- [ ] 50+ conversas médias por usuário
- [ ] NPS > 40
- [ ] Custo por análise < R$ 5
- [ ] 95% de precisão vs avaliações tradicionais

---

## 💡 Ideias Futuras (Exploratórias)

### Recursos Inovadores
- **Modo de Grupo:** Jung moderando conversas em grupo
- **Análise de Equipes:** Dinâmica e compatibilidade de times
- **Coaching Adaptativo:** Planos de desenvolvimento personalizados
- **Gamificação:** Badges e conquistas por autoconhecimento
- **Voice Interface:** Conversas por áudio

### Parcerias Estratégicas
- **RH Tech:** Gupy, Kenoby, Feedz
- **Universidades:** Pesquisa em psicologia computacional
- **Terapeutas:** Triagem e direcionamento
- **Empresas:** B2B para onboarding e desenvolvimento

---

## 🚨 Riscos e Mitigações

### Riscos Técnicos
| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| API limits (OpenAI/Claude) | Alto | Implementar fallbacks, rate limiting |
| Custo crescente de LLM | Alto | Otimizar prompts, usar modelos menores quando possível |
| Bugs em produção | Médio | Testes automatizados, rollback rápido |
| Perda de dados | Alto | Backups diários, replicação |

### Riscos de Negócio
| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Baixa adoção por RHs | Alto | Demonstrações práticas, casos de uso claros |
| Competição com avaliações tradicionais | Médio | Posicionar como complementar, não substituto |
| Questões éticas de IA em RH | Alto | Transparência total, LGPD rigoroso, auditorias |
| Viés algorítmico | Alto | Validação contínua, diverse testing |

---

## 📞 Decisões Pendentes

### Aguardando Definição do Usuário

1. **Apresentação RH:**
   - [ ] Data da apresentação?
   - [ ] Nome da empresa parceira?
   - [ ] Formato: presencial ou remoto?
   - [ ] Número de candidatos para demo?

2. **Modelo de Negócio:**
   - [ ] B2C (direto ao usuário) ou B2B (para empresas)?
   - [ ] Freemium ou apenas pago?
   - [ ] Preço por análise ou assinatura mensal?

3. **Roadmap de Rumination:**
   - [ ] Implementar antes ou depois do beta RH?
   - [ ] Testar em pequena escala primeiro?

4. **Infraestrutura:**
   - [ ] Continuar no Railway ou migrar (AWS, GCP)?
   - [ ] Adicionar CDN para admin web?

---

## 🎬 Ações Imediatas (Esta Semana)

### Segunda-feira
1. Implementar exportação de PDF dos relatórios
2. Melhorar autenticação do admin web

### Terça-feira
3. Adicionar sistema de evidências nas análises
4. Criar dashboard específico para RH

### Quarta-feira
5. Coletar feedback de 3-5 usuários internos
6. Ajustar prompts baseado em feedback

### Quinta-feira
7. Testes de ponta a ponta do fluxo completo
8. Correções de bugs identificados

### Sexta-feira
9. Revisão de compliance LGPD
10. Preparar apresentação/demo para RH

---

## 📚 Referências e Documentação

### Documentos Internos
- `docs/JUNG_APRESENTACAO_RH_v1.md` - Planejamento da apresentação
- `docs/SISTEMA_RUMINACAO_v1.md` - Sistema de insights latentes
- `docs/COMO_ALTERNAR_LLM.md` - Guia de troca de providers
- `README.md` - Setup e instalação

### Documentação Externa
- [Claude Models](https://platform.claude.com/docs/en/about-claude/models)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

---

## 🤝 Contribuindo para o Roadmap

Este roadmap é vivo e deve ser atualizado conforme:
- Feedback dos usuários
- Mudanças de prioridade de negócio
- Novas oportunidades técnicas
- Aprendizados do beta

**Como atualizar:**
1. Mover tarefas entre prioridades conforme necessário
2. Marcar ✅ tarefas concluídas
3. Adicionar novas ideias ao backlog
4. Revisar métricas mensalmente

---

**Última revisão:** 29/11/2025
**Próxima revisão:** Após beta com RH
