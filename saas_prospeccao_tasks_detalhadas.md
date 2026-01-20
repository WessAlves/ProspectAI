# Tasks Detalhadas e Dependências - SaaS de Prospecção

**Autor:** Manus AI
**Data:** 07 de Janeiro de 2026

---

## Visão Geral

Este documento detalha todas as tasks necessárias para o desenvolvimento do MVP, organizadas por fase, com suas dependências, estimativas de tempo e responsáveis sugeridos. Cada task foi projetada para ser granular o suficiente para ser atribuída e rastreada individualmente.

---

## Fase 1: Setup e Fundação (Semanas 1-2)

### 1.1. Backend - Infraestrutura Base

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| BE-001 | Criar repositório Git e estrutura de pastas do backend | - | 2h | Backend Dev |
| BE-002 | Configurar ambiente virtual Python e requirements.txt | BE-001 | 1h | Backend Dev |
| BE-003 | Inicializar projeto FastAPI com main.py e estrutura modular | BE-002 | 3h | Backend Dev |
| BE-004 | Configurar SQLAlchemy e criar base.py com BaseModel | BE-003 | 4h | Backend Dev |
| BE-005 | Configurar Alembic para migrations | BE-004 | 2h | Backend Dev |
| BE-006 | Criar modelo User no banco de dados | BE-005 | 3h | Backend Dev |
| BE-007 | Implementar hashing de senha com passlib | BE-006 | 2h | Backend Dev |
| BE-008 | Implementar geração e validação de JWT | BE-007 | 4h | Backend Dev |
| BE-009 | Criar endpoints de registro e login | BE-008 | 4h | Backend Dev |
| BE-010 | Configurar CORS e middlewares de segurança | BE-003 | 2h | Backend Dev |
| BE-011 | Criar arquivo .env.example e configurar python-dotenv | BE-003 | 1h | Backend Dev |
| BE-012 | Implementar endpoint de health check | BE-003 | 1h | Backend Dev |
| BE-013 | Criar testes unitários para autenticação | BE-009 | 3h | Backend Dev |

**Total Estimado:** 32 horas

---

### 1.2. Frontend - Infraestrutura Base

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| FE-001 | Criar repositório Git e inicializar projeto Vite + React + TS | - | 2h | Frontend Dev |
| FE-002 | Configurar TailwindCSS e arquivo de configuração | FE-001 | 2h | Frontend Dev |
| FE-003 | Instalar e configurar shadcn/ui | FE-002 | 2h | Frontend Dev |
| FE-004 | Configurar React Router v6 com rotas básicas | FE-001 | 3h | Frontend Dev |
| FE-005 | Criar layout base (AppLayout com sidebar e header) | FE-004 | 4h | Frontend Dev |
| FE-006 | Configurar Axios e criar serviço de API | FE-001 | 3h | Frontend Dev |
| FE-007 | Configurar React Query (TanStack Query) | FE-006 | 2h | Frontend Dev |
| FE-008 | Configurar Zustand para estado global | FE-001 | 2h | Frontend Dev |
| FE-009 | Criar página de login com formulário | FE-004, FE-005 | 4h | Frontend Dev |
| FE-010 | Criar página de registro com formulário | FE-009 | 3h | Frontend Dev |
| FE-011 | Implementar lógica de autenticação e armazenamento de token | FE-006, FE-008 | 4h | Frontend Dev |
| FE-012 | Criar ProtectedRoute para rotas autenticadas | FE-004, FE-011 | 2h | Frontend Dev |
| FE-013 | Configurar ESLint e Prettier | FE-001 | 1h | Frontend Dev |

**Total Estimado:** 34 horas

---

### 1.3. DevOps - Infraestrutura

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| DO-001 | Criar Dockerfile para backend | BE-003 | 2h | DevOps |
| DO-002 | Criar Dockerfile para frontend | FE-001 | 2h | DevOps |
| DO-003 | Criar docker-compose.yml com todos os serviços | DO-001, DO-002 | 4h | DevOps |
| DO-004 | Configurar PostgreSQL no Docker Compose | DO-003 | 1h | DevOps |
| DO-005 | Configurar Redis no Docker Compose | DO-003 | 1h | DevOps |
| DO-006 | Criar workflow GitHub Actions para testes backend | BE-013 | 3h | DevOps |
| DO-007 | Criar workflow GitHub Actions para testes frontend | FE-013 | 3h | DevOps |
| DO-008 | Configurar black, flake8 e mypy no CI | DO-006 | 2h | DevOps |
| DO-009 | Escrever README.md com instruções de setup | DO-003 | 2h | DevOps |

**Total Estimado:** 20 horas

**Total Fase 1:** 86 horas (~2 semanas com 1 dev full-time)

---

## Fase 2: Agentes e Planos (Semanas 3-4)

### 2.1. Backend - Agentes LLM

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| BE-101 | Criar modelo Agent no banco de dados | BE-006 | 3h | Backend Dev |
| BE-102 | Criar migration para tabela agents | BE-101 | 1h | Backend Dev |
| BE-103 | Criar schemas Pydantic para Agent (Create, Update, Response) | BE-101 | 2h | Backend Dev |
| BE-104 | Implementar endpoint POST /agents (criar agente) | BE-103 | 3h | Backend Dev |
| BE-105 | Implementar endpoint GET /agents (listar agentes do usuário) | BE-103 | 2h | Backend Dev |
| BE-106 | Implementar endpoint GET /agents/{id} (detalhes do agente) | BE-103 | 2h | Backend Dev |
| BE-107 | Implementar endpoint PUT /agents/{id} (atualizar agente) | BE-103 | 3h | Backend Dev |
| BE-108 | Implementar endpoint DELETE /agents/{id} (deletar agente) | BE-103 | 2h | Backend Dev |
| BE-109 | Criar serviço de integração com OpenAI API | BE-011 | 4h | Backend Dev |
| BE-110 | Implementar endpoint POST /agents/{id}/test (testar geração) | BE-109 | 3h | Backend Dev |
| BE-111 | Adicionar validações de negócio (limites por plano) | BE-104 | 2h | Backend Dev |
| BE-112 | Criar testes unitários para CRUD de agentes | BE-108 | 4h | Backend Dev |

**Total Estimado:** 31 horas

---

### 2.2. Backend - Planos de Serviço

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| BE-201 | Criar modelo ServicePlan no banco de dados | BE-006 | 3h | Backend Dev |
| BE-202 | Criar migration para tabela service_plans | BE-201 | 1h | Backend Dev |
| BE-203 | Criar schemas Pydantic para ServicePlan | BE-201 | 2h | Backend Dev |
| BE-204 | Implementar CRUD completo para planos | BE-203 | 6h | Backend Dev |
| BE-205 | Adicionar validações e regras de negócio | BE-204 | 2h | Backend Dev |
| BE-206 | Criar testes unitários para planos | BE-204 | 3h | Backend Dev |

**Total Estimado:** 17 horas

---

### 2.3. Frontend - Agentes

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| FE-101 | Criar página de listagem de agentes | FE-012 | 4h | Frontend Dev |
| FE-102 | Criar componente AgentCard para exibir agente | FE-101 | 2h | Frontend Dev |
| FE-103 | Criar formulário de criação de agente com React Hook Form | FE-101 | 5h | Frontend Dev |
| FE-104 | Adicionar validação com Zod no formulário | FE-103 | 2h | Frontend Dev |
| FE-105 | Implementar modal/página de edição de agente | FE-103 | 3h | Frontend Dev |
| FE-106 | Criar funcionalidade de preview de mensagem | BE-110 | 4h | Frontend Dev |
| FE-107 | Implementar delete com confirmação | FE-101 | 2h | Frontend Dev |
| FE-108 | Adicionar feedback visual (toasts, loading states) | FE-103 | 2h | Frontend Dev |

**Total Estimado:** 24 horas

---

### 2.4. Frontend - Planos

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| FE-201 | Criar página de listagem de planos | FE-012 | 3h | Frontend Dev |
| FE-202 | Criar formulário de criação/edição de plano | FE-201 | 4h | Frontend Dev |
| FE-203 | Adicionar validações no formulário | FE-202 | 2h | Frontend Dev |
| FE-204 | Implementar CRUD completo no frontend | FE-202 | 3h | Frontend Dev |

**Total Estimado:** 12 horas

**Total Fase 2:** 84 horas (~2 semanas com 1 dev full-time)

---

## Fase 3: Scraping e Busca (Semanas 5-7)

### 3.1. Backend - Infraestrutura de Workers

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| BE-301 | Configurar Celery com Redis como broker | DO-005 | 4h | Backend Dev |
| BE-302 | Criar estrutura de tasks em workers/ | BE-301 | 2h | Backend Dev |
| BE-303 | Implementar sistema de retry e error handling | BE-302 | 3h | Backend Dev |
| BE-304 | Configurar logging estruturado com structlog | BE-302 | 3h | Backend Dev |
| BE-305 | Criar modelo Prospect no banco de dados | BE-006 | 4h | Backend Dev |
| BE-306 | Criar migration para tabela prospects | BE-305 | 1h | Backend Dev |

**Total Estimado:** 17 horas

---

### 3.2. Backend - Google Scraper

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| BE-401 | Pesquisar e decidir método (API oficial vs scraping) | - | 4h | Backend Dev |
| BE-402 | Configurar Google Places API ou Playwright | BE-401 | 4h | Backend Dev |
| BE-403 | Implementar busca por localização e categoria | BE-402 | 6h | Backend Dev |
| BE-404 | Extrair dados: nome, endereço, telefone, website | BE-403 | 4h | Backend Dev |
| BE-405 | Implementar filtros (tem site, avaliações, etc) | BE-404 | 4h | Backend Dev |
| BE-406 | Tratar rate limiting e configurar proxies | BE-403 | 4h | Backend Dev |
| BE-407 | Criar Celery task para busca Google | BE-302, BE-405 | 3h | Backend Dev |
| BE-408 | Criar testes com dados mockados | BE-407 | 4h | Backend Dev |

**Total Estimado:** 33 horas

---

### 3.3. Backend - Instagram Scraper

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| BE-501 | Avaliar instagrapi vs Playwright | - | 4h | Backend Dev |
| BE-502 | Configurar biblioteca escolhida | BE-501 | 3h | Backend Dev |
| BE-503 | Criar modelo IntegratedAccount para credenciais | BE-006 | 3h | Backend Dev |
| BE-504 | Implementar autenticação de conta Instagram | BE-503 | 5h | Backend Dev |
| BE-505 | Implementar busca por hashtags e localização | BE-504 | 6h | Backend Dev |
| BE-506 | Extrair dados: username, followers, bio, último post | BE-505 | 5h | Backend Dev |
| BE-507 | Implementar filtros (seguidores, atividade) | BE-506 | 4h | Backend Dev |
| BE-508 | Tratar bloqueios e rate limiting | BE-505 | 5h | Backend Dev |
| BE-509 | Implementar rotação de contas (se necessário) | BE-508 | 4h | Backend Dev |
| BE-510 | Criar Celery task para busca Instagram | BE-302, BE-507 | 3h | Backend Dev |
| BE-511 | Criar testes | BE-510 | 4h | Backend Dev |

**Total Estimado:** 46 horas

---

### 3.4. Backend - Sistema de Qualificação

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| BE-601 | Criar sistema de scoring de prospects | BE-305 | 5h | Backend Dev |
| BE-602 | Implementar regras de qualificação configuráveis | BE-601 | 4h | Backend Dev |
| BE-603 | Implementar filtro de duplicados | BE-305 | 3h | Backend Dev |
| BE-604 | Criar endpoint GET /prospects (listar prospects) | BE-305 | 3h | Backend Dev |
| BE-605 | Adicionar filtros e paginação no endpoint | BE-604 | 3h | Backend Dev |

**Total Estimado:** 18 horas

**Total Fase 3:** 114 horas (~3 semanas com 1 dev full-time)

---

## Fase 4: Campanhas e Messaging (Semanas 8-11)

### 4.1. Backend - Campanhas

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| BE-701 | Criar modelo Campaign no banco de dados | BE-006, BE-101 | 4h | Backend Dev |
| BE-702 | Criar tabela associativa campaign_plans (N:N) | BE-701, BE-201 | 2h | Backend Dev |
| BE-703 | Criar migrations | BE-702 | 1h | Backend Dev |
| BE-704 | Criar schemas Pydantic para Campaign | BE-701 | 3h | Backend Dev |
| BE-705 | Implementar CRUD de campanhas | BE-704 | 8h | Backend Dev |
| BE-706 | Implementar lógica de configuração de busca (filtros) | BE-705 | 4h | Backend Dev |
| BE-707 | Implementar estados da campanha (draft, active, paused) | BE-705 | 3h | Backend Dev |
| BE-708 | Criar endpoint POST /campaigns/{id}/start | BE-707 | 3h | Backend Dev |
| BE-709 | Criar endpoint POST /campaigns/{id}/pause | BE-707 | 2h | Backend Dev |
| BE-710 | Adicionar validações de negócio | BE-705 | 3h | Backend Dev |
| BE-711 | Criar testes unitários | BE-710 | 4h | Backend Dev |

**Total Estimado:** 37 horas

---

### 4.2. Backend - WhatsApp Integration

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| BE-801 | Pesquisar provedor (Twilio, MessageBird, oficial) | - | 3h | Backend Dev |
| BE-802 | Configurar conta de teste no provedor escolhido | BE-801 | 2h | Backend Dev |
| BE-803 | Criar serviço whatsapp_service.py | BE-802 | 4h | Backend Dev |
| BE-804 | Implementar função de envio de mensagem | BE-803 | 4h | Backend Dev |
| BE-805 | Armazenar credenciais no IntegratedAccount | BE-503 | 2h | Backend Dev |
| BE-806 | Criar endpoint POST /webhooks/whatsapp | BE-804 | 4h | Backend Dev |
| BE-807 | Implementar processamento de status (sent, delivered, read) | BE-806 | 3h | Backend Dev |
| BE-808 | Implementar rate limiting específico para WhatsApp | BE-804 | 3h | Backend Dev |
| BE-809 | Criar testes com mock da API | BE-804 | 4h | Backend Dev |

**Total Estimado:** 29 horas

---

### 4.3. Backend - Instagram Direct Integration

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| BE-901 | Avaliar método (instagrapi vs API oficial) | - | 3h | Backend Dev |
| BE-902 | Configurar biblioteca e autenticação | BE-901, BE-504 | 3h | Backend Dev |
| BE-903 | Criar serviço instagram_service.py | BE-902 | 4h | Backend Dev |
| BE-904 | Implementar função de envio de DM | BE-903 | 5h | Backend Dev |
| BE-905 | Criar sistema de polling para receber respostas | BE-904 | 5h | Backend Dev |
| BE-906 | Tratar bloqueios e limitações | BE-904 | 4h | Backend Dev |
| BE-907 | Implementar rate limiting específico | BE-904 | 3h | Backend Dev |
| BE-908 | Criar testes | BE-904 | 4h | Backend Dev |

**Total Estimado:** 31 horas

---

### 4.4. Backend - Automação de Mensagens

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| BE-1001 | Criar modelo Message no banco de dados | BE-305 | 3h | Backend Dev |
| BE-1002 | Criar migration para tabela messages | BE-1001 | 1h | Backend Dev |
| BE-1003 | Criar Celery task process_campaign | BE-302, BE-708 | 5h | Backend Dev |
| BE-1004 | Implementar lógica de seleção de prospects | BE-1003 | 4h | Backend Dev |
| BE-1005 | Integrar com agente LLM para gerar mensagens | BE-1004, BE-109 | 5h | Backend Dev |
| BE-1006 | Implementar fila de envio com delays randomizados | BE-1005 | 4h | Backend Dev |
| BE-1007 | Criar sistema de retry para falhas | BE-1006 | 3h | Backend Dev |
| BE-1008 | Implementar follow-up automático (opcional) | BE-1007 | 5h | Backend Dev |
| BE-1009 | Adicionar logs detalhados | BE-1006 | 2h | Backend Dev |
| BE-1010 | Criar testes de integração | BE-1009 | 5h | Backend Dev |

**Total Estimado:** 37 horas

---

### 4.5. Frontend - Campanhas

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| FE-301 | Criar página de listagem de campanhas | FE-012 | 4h | Frontend Dev |
| FE-302 | Criar wizard multi-step de criação de campanha | FE-301 | 8h | Frontend Dev |
| FE-303 | Implementar step 1: Informações básicas | FE-302 | 3h | Frontend Dev |
| FE-304 | Implementar step 2: Seleção de agente | FE-302, FE-101 | 3h | Frontend Dev |
| FE-305 | Implementar step 3: Seleção de planos | FE-302, FE-201 | 3h | Frontend Dev |
| FE-306 | Implementar step 4: Configuração de filtros de busca | FE-302 | 5h | Frontend Dev |
| FE-307 | Adicionar preview de busca (quantos prospects) | FE-306 | 4h | Frontend Dev |
| FE-308 | Criar página de detalhes da campanha | FE-301 | 5h | Frontend Dev |
| FE-309 | Implementar controles (iniciar, pausar, parar) | FE-308 | 3h | Frontend Dev |
| FE-310 | Adicionar indicadores de progresso em tempo real | FE-308 | 5h | Frontend Dev |
| FE-311 | Configurar WebSocket para updates | FE-310 | 4h | Frontend Dev |

**Total Estimado:** 47 horas

**Total Fase 4:** 181 horas (~4 semanas com 1 dev full-time)

---

## Fase 5: Dashboard e Analytics (Semanas 12-14)

### 5.1. Backend - Analytics

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| BE-1101 | Criar modelo CampaignMetrics para agregação | BE-701 | 3h | Backend Dev |
| BE-1102 | Criar migration | BE-1101 | 1h | Backend Dev |
| BE-1103 | Criar Celery task para calcular métricas | BE-302, BE-1101 | 5h | Backend Dev |
| BE-1104 | Implementar endpoint GET /dashboard/overview | BE-1103 | 4h | Backend Dev |
| BE-1105 | Implementar endpoint GET /campaigns/{id}/metrics | BE-1103 | 4h | Backend Dev |
| BE-1106 | Implementar endpoint GET /campaigns/{id}/timeline | BE-1001 | 4h | Backend Dev |
| BE-1107 | Implementar endpoint GET /campaigns/compare | BE-1105 | 5h | Backend Dev |
| BE-1108 | Otimizar queries com agregações SQL | BE-1107 | 4h | Backend Dev |
| BE-1109 | Implementar cache de métricas com Redis | BE-1108 | 3h | Backend Dev |
| BE-1110 | Criar endpoint de exportação (CSV, JSON) | BE-1105 | 4h | Backend Dev |
| BE-1111 | Configurar WebSocket para updates em tempo real | BE-1109 | 5h | Backend Dev |

**Total Estimado:** 42 horas

---

### 5.2. Frontend - Dashboard

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| FE-401 | Criar página de dashboard principal | FE-012 | 4h | Frontend Dev |
| FE-402 | Implementar cards de KPIs (métricas principais) | FE-401, BE-1104 | 5h | Frontend Dev |
| FE-403 | Criar gráfico de funil de conversão com Recharts | FE-401, BE-1105 | 6h | Frontend Dev |
| FE-404 | Criar gráfico de timeline de atividades | FE-401, BE-1106 | 5h | Frontend Dev |
| FE-405 | Implementar gráfico de comparação de campanhas | FE-401, BE-1107 | 6h | Frontend Dev |
| FE-406 | Criar tabela de prospects com filtros e busca | FE-401, BE-604 | 6h | Frontend Dev |
| FE-407 | Adicionar visualização de histórico de mensagens | FE-406, BE-1001 | 5h | Frontend Dev |
| FE-408 | Implementar exportação de relatórios | FE-401, BE-1110 | 4h | Frontend Dev |
| FE-409 | Criar sistema de notificações (toast/sidebar) | FE-401 | 4h | Frontend Dev |
| FE-410 | Integrar WebSocket para updates em tempo real | FE-401, BE-1111 | 5h | Frontend Dev |
| FE-411 | Otimizar performance (React.memo, useMemo) | FE-410 | 4h | Frontend Dev |
| FE-412 | Implementar virtual scrolling para listas grandes | FE-406 | 4h | Frontend Dev |

**Total Estimado:** 58 horas

**Total Fase 5:** 100 horas (~3 semanas com 1 dev full-time)

---

## Fase 6: Refinamento e MVP Launch (Semanas 15-16)

### 6.1. Produto e UX

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| PD-001 | Criar fluxo de onboarding guiado | FE-012 | 6h | Frontend Dev |
| PD-002 | Adicionar tooltips e help texts em toda aplicação | - | 4h | Frontend Dev |
| PD-003 | Criar página de documentação/FAQ | - | 6h | Frontend Dev |
| PD-004 | Implementar tour interativo (intro.js ou similar) | PD-001 | 4h | Frontend Dev |
| PD-005 | Criar templates de agentes e campanhas | BE-101, BE-701 | 4h | Backend Dev |

**Total Estimado:** 24 horas

---

### 6.2. Qualidade e Testes

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| QA-001 | Criar testes E2E com Playwright para fluxo principal | FE-410 | 8h | QA/Dev |
| QA-002 | Realizar testes de carga com Locust | BE-1111 | 6h | DevOps |
| QA-003 | Auditoria de segurança (OWASP checklist) | - | 6h | Backend Dev |
| QA-004 | Revisar e corrigir bugs conhecidos | - | 8h | Team |
| QA-005 | Otimizar queries lentas identificadas | BE-1108 | 4h | Backend Dev |
| QA-006 | Reduzir bundle size do frontend | FE-411 | 4h | Frontend Dev |
| QA-007 | Implementar error boundaries no React | FE-401 | 3h | Frontend Dev |

**Total Estimado:** 39 horas

---

### 6.3. Compliance e Legal

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| LG-001 | Criar página de Termos de Uso | - | 4h | Product/Legal |
| LG-002 | Criar página de Política de Privacidade | - | 4h | Product/Legal |
| LG-003 | Implementar banner de consentimento LGPD | FE-012 | 3h | Frontend Dev |
| LG-004 | Adicionar opção de deletar conta | BE-006 | 4h | Backend Dev |
| LG-005 | Implementar exportação de dados pessoais | BE-1110 | 3h | Backend Dev |

**Total Estimado:** 18 horas

---

### 6.4. Deploy e Operações

| ID | Task | Dependências | Estimativa | Responsável |
|:---|:-----|:-------------|:-----------|:------------|
| OP-001 | Configurar ambiente de produção (AWS/GCP/DO) | - | 6h | DevOps |
| OP-002 | Setup de domínio e certificado SSL | OP-001 | 2h | DevOps |
| OP-003 | Configurar backups automáticos do PostgreSQL | OP-001 | 3h | DevOps |
| OP-004 | Setup de monitoramento (Sentry para errors) | OP-001 | 3h | DevOps |
| OP-005 | Configurar logs centralizados | OP-001 | 4h | DevOps |
| OP-006 | Criar runbook de operações e troubleshooting | OP-005 | 4h | DevOps |
| OP-007 | Realizar deploy para produção | OP-006 | 4h | DevOps |
| OP-008 | Executar smoke tests em produção | OP-007 | 2h | Team |
| OP-009 | Configurar alertas (email, Slack) | OP-004 | 3h | DevOps |

**Total Estimado:** 31 horas

**Total Fase 6:** 112 horas (~2 semanas com 1 dev full-time)

---

## Resumo de Horas por Fase

| Fase | Horas Estimadas | Semanas (40h) |
|:-----|:----------------|:--------------|
| Fase 1: Setup e Fundação | 86h | 2.2 |
| Fase 2: Agentes e Planos | 84h | 2.1 |
| Fase 3: Scraping e Busca | 114h | 2.9 |
| Fase 4: Campanhas e Messaging | 181h | 4.5 |
| Fase 5: Dashboard e Analytics | 100h | 2.5 |
| Fase 6: Refinamento e Launch | 112h | 2.8 |
| **TOTAL** | **677h** | **17 semanas** |

---

## Dependências Críticas

### Dependências Externas
- **OpenAI API:** Necessária a partir da Fase 2
- **WhatsApp Business API:** Necessária na Fase 4
- **Instagram APIs/Libraries:** Necessária nas Fases 3 e 4
- **Google APIs:** Necessária na Fase 3

### Dependências Internas (Bloqueantes)
- **BE-006 (Modelo User)** → Bloqueia toda autenticação e relacionamentos
- **BE-101 (Modelo Agent)** → Bloqueia Fase 4 (geração de mensagens)
- **BE-201 (Modelo ServicePlan)** → Bloqueia Fase 4 (campanhas)
- **BE-305 (Modelo Prospect)** → Bloqueia Fases 3 e 4
- **BE-302 (Celery Setup)** → Bloqueia todo processamento assíncrono

---

## Alocação de Recursos Recomendada

### Cenário 1: Time Completo (Mais Rápido)
- 1 Backend Developer (full-time)
- 1 Frontend Developer (full-time)
- 1 DevOps Engineer (part-time, 20h/semana)
- **Duração:** 12-14 semanas

### Cenário 2: Time Reduzido (Recomendado para MVP)
- 1 Full-Stack Developer Senior (full-time)
- 1 DevOps Engineer (part-time, 15h/semana)
- **Duração:** 16-20 semanas

### Cenário 3: Solo Developer (Mais Econômico)
- 1 Full-Stack Developer experiente (full-time)
- **Duração:** 20-24 semanas

---

## Ferramentas de Gestão Recomendadas

- **Gestão de Tasks:** Linear, Jira, ou GitHub Projects
- **Comunicação:** Slack ou Discord
- **Documentação:** Notion ou Confluence
- **Design:** Figma
- **Versionamento:** GitHub ou GitLab

---

## Próximos Passos

1. Importar estas tasks para a ferramenta de gestão escolhida
2. Atribuir responsáveis e priorizar
3. Configurar sprints de 1-2 semanas
4. Iniciar pela Fase 1, task BE-001
