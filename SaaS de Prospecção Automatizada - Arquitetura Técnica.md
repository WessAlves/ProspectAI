# SaaS de Prospecção Automatizada - Arquitetura Técnica

## 1. Stack Tecnológico

### 1.1 Frontend

**Framework Principal:**
- **React 18+** com TypeScript
- **Vite** como build tool (rápido e moderno)

**UI/UX:**
- **TailwindCSS** para estilização
- **shadcn/ui** ou **Ant Design** para componentes prontos
- **Recharts** ou **Chart.js** para gráficos e dashboards
- **React Query (TanStack Query)** para gerenciamento de estado servidor
- **Zustand** ou **Redux Toolkit** para estado global

**Roteamento e Navegação:**
- **React Router v6**

**Formulários:**
- **React Hook Form** + **Zod** para validação

**Comunicação em Tempo Real:**
- **Socket.io Client** para updates de campanhas em tempo real

---

### 1.2 Backend

**Framework Principal:**
- **FastAPI** (Python 3.11+) - assíncrono, rápido, com documentação automática

**Estrutura do Backend:**
```
backend/
├── app/
│   ├── main.py                 # Entry point
│   ├── config.py               # Configurações
│   ├── dependencies.py         # Injeção de dependências
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py
│   │   │   │   ├── campaigns.py
│   │   │   │   ├── agents.py
│   │   │   │   ├── plans.py
│   │   │   │   ├── prospects.py
│   │   │   │   ├── dashboard.py
│   │   │   │   └── integrations.py
│   │   │   └── router.py
│   ├── core/
│   │   ├── security.py         # JWT, hashing
│   │   ├── config.py
│   │   └── events.py           # Startup/shutdown
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models/
│   │       ├── user.py
│   │       ├── campaign.py
│   │       ├── agent.py
│   │       ├── plan.py
│   │       └── prospect.py
│   ├── schemas/                # Pydantic models
│   ├── services/               # Lógica de negócio
│   │   ├── scraping/
│   │   │   ├── google_scraper.py
│   │   │   └── instagram_scraper.py
│   │   ├── messaging/
│   │   │   ├── whatsapp_service.py
│   │   │   └── instagram_service.py
│   │   ├── llm/
│   │   │   └── agent_service.py
│   │   └── analytics/
│   │       └── dashboard_service.py
│   ├── workers/                # Celery tasks
│   │   ├── scraping_tasks.py
│   │   ├── messaging_tasks.py
│   │   └── analytics_tasks.py
│   └── utils/
│       ├── logger.py
│       └── helpers.py
├── tests/
├── alembic/                    # Migrations
├── requirements.txt
└── docker-compose.yml
```

**Bibliotecas Python Essenciais:**

**Core:**
- `fastapi` - Framework web
- `uvicorn[standard]` - ASGI server
- `pydantic` - Validação de dados
- `python-dotenv` - Variáveis de ambiente

**Banco de Dados:**
- `sqlalchemy` - ORM
- `alembic` - Migrations
- `asyncpg` - Driver PostgreSQL assíncrono
- `psycopg2-binary` - Driver PostgreSQL

**Autenticação:**
- `python-jose[cryptography]` - JWT
- `passlib[bcrypt]` - Hashing de senhas
- `python-multipart` - Form data

**Tasks Assíncronas:**
- `celery` - Task queue
- `redis` - Message broker e cache

**Scraping:**
- `playwright` - Browser automation (Instagram)
- `beautifulsoup4` - HTML parsing
- `httpx` - HTTP client assíncrono
- `selenium` - Alternativa para scraping

**APIs Externas:**
- `openai` - LLM integration
- `twilio` - WhatsApp Business API
- `google-api-python-client` - Google APIs
- `instagrapi` - Instagram API (não oficial)

**Utilidades:**
- `python-slugify` - Slugs
- `pillow` - Processamento de imagens
- `pandas` - Análise de dados
- `python-dateutil` - Manipulação de datas

---

### 1.3 Banco de Dados

**Banco Principal:**
- **PostgreSQL 15+** - Relacional, robusto, com suporte a JSON

**Esquema de Tabelas Principais:**

```sql
-- Usuários
users
├── id (UUID, PK)
├── email (VARCHAR, UNIQUE)
├── password_hash (VARCHAR)
├── full_name (VARCHAR)
├── plan_tier (ENUM: free, pro, enterprise)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

-- Agentes LLM
agents
├── id (UUID, PK)
├── user_id (UUID, FK -> users)
├── name (VARCHAR)
├── system_prompt (TEXT)
├── model_name (VARCHAR)
├── temperature (FLOAT)
├── max_tokens (INT)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

-- Planos/Serviços
service_plans
├── id (UUID, PK)
├── user_id (UUID, FK -> users)
├── name (VARCHAR)
├── description (TEXT)
├── price (DECIMAL)
├── features (JSONB)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

-- Campanhas
campaigns
├── id (UUID, PK)
├── user_id (UUID, FK -> users)
├── agent_id (UUID, FK -> agents)
├── name (VARCHAR)
├── status (ENUM: draft, active, paused, completed)
├── search_config (JSONB)
├── channel (ENUM: instagram, whatsapp)
├── rate_limit (INT)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

-- Associação Campanha-Planos (N:N)
campaign_plans
├── campaign_id (UUID, FK -> campaigns)
├── plan_id (UUID, FK -> service_plans)
└── PRIMARY KEY (campaign_id, plan_id)

-- Prospects
prospects
├── id (UUID, PK)
├── campaign_id (UUID, FK -> campaigns)
├── name (VARCHAR)
├── username (VARCHAR)
├── platform (ENUM: instagram, google)
├── profile_url (VARCHAR)
├── followers_count (INT)
├── has_website (BOOLEAN)
├── website_url (VARCHAR)
├── last_post_date (TIMESTAMP)
├── metadata (JSONB)
├── status (ENUM: found, contacted, replied, converted, ignored)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

-- Mensagens
messages
├── id (UUID, PK)
├── prospect_id (UUID, FK -> prospects)
├── campaign_id (UUID, FK -> campaigns)
├── content (TEXT)
├── direction (ENUM: outbound, inbound)
├── status (ENUM: pending, sent, delivered, read, failed)
├── sent_at (TIMESTAMP)
├── delivered_at (TIMESTAMP)
├── read_at (TIMESTAMP)
└── metadata (JSONB)

-- Contas Integradas
integrated_accounts
├── id (UUID, PK)
├── user_id (UUID, FK -> users)
├── platform (ENUM: instagram, whatsapp)
├── account_identifier (VARCHAR)
├── credentials (TEXT, encrypted)
├── status (ENUM: active, expired, blocked)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

-- Métricas de Campanha (agregadas)
campaign_metrics
├── id (UUID, PK)
├── campaign_id (UUID, FK -> campaigns)
├── date (DATE)
├── prospects_found (INT)
├── messages_sent (INT)
├── messages_delivered (INT)
├── messages_read (INT)
├── replies_received (INT)
├── conversions (INT)
└── updated_at (TIMESTAMP)
```

**Cache e Sessões:**
- **Redis** - Cache de queries, sessões, rate limiting

---

### 1.4 Infraestrutura

**Containerização:**
- **Docker** + **Docker Compose** para desenvolvimento
- **Kubernetes** para produção (opcional, dependendo da escala)

**Message Queue:**
- **Celery** com **Redis** como broker
- Workers dedicados para:
  - Scraping (Google/Instagram)
  - Envio de mensagens
  - Processamento de LLM
  - Agregação de métricas

**Armazenamento:**
- **AWS S3** ou **CloudFlare R2** para arquivos estáticos
- **PostgreSQL** para dados estruturados
- **Redis** para cache e filas

**Monitoramento:**
- **Sentry** para error tracking
- **Prometheus** + **Grafana** para métricas
- **ELK Stack** (Elasticsearch, Logstash, Kibana) para logs (opcional)

**CI/CD:**
- **GitHub Actions** ou **GitLab CI**
- Deploy automático para staging/production

---

## 2. Arquitetura do Sistema

### 2.1 Diagrama de Arquitetura (Alto Nível)

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│                  React + TypeScript + Vite                   │
│                      TailwindCSS + shadcn                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS/WSS
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      API GATEWAY                             │
│                   FastAPI + Uvicorn                          │
│                  (Authentication, Rate Limiting)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Campaign    │  │    Agent      │  │   Dashboard   │
│   Service     │  │   Service     │  │   Service     │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  PostgreSQL   │  │     Redis     │  │  Celery       │
│  (Database)   │  │  (Cache/Queue)│  │  Workers      │
└───────────────┘  └───────────────┘  └───────┬───────┘
                                              │
                    ┌─────────────────────────┼─────────────────┐
                    │                         │                 │
                    ▼                         ▼                 ▼
            ┌───────────────┐        ┌───────────────┐  ┌──────────────┐
            │   Scraping    │        │   Messaging   │  │     LLM      │
            │    Worker     │        │    Worker     │  │   Worker     │
            └───────┬───────┘        └───────┬───────┘  └──────┬───────┘
                    │                        │                 │
                    │                        │                 │
        ┌───────────┼────────────┐          │      ┌──────────┼────────┐
        │           │            │          │      │          │        │
        ▼           ▼            ▼          ▼      ▼          ▼        ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌────────────┐
│  Google  │ │Instagram │ │  Proxy   │ │  WhatsApp  │ │   OpenAI   │
│   API    │ │   API    │ │ Services │ │    API     │ │    API     │
└──────────┘ └──────────┘ └──────────┘ └────────────┘ └────────────┘
```

---

### 2.2 Fluxo de Dados - Criação de Campanha

```
1. Usuário cria campanha no Frontend
   ↓
2. POST /api/v1/campaigns (FastAPI)
   ↓
3. Validação e criação no PostgreSQL
   ↓
4. Dispara task Celery: scraping_tasks.execute_search
   ↓
5. Worker de Scraping:
   - Busca no Google (via API ou Playwright)
   - Busca no Instagram (via instagrapi ou Playwright)
   - Aplica filtros de qualificação
   ↓
6. Salva prospects no PostgreSQL
   ↓
7. Dispara task Celery: messaging_tasks.send_initial_messages
   ↓
8. Worker de Messaging:
   - Para cada prospect qualificado
   - Busca agente LLM configurado
   - Gera mensagem personalizada (OpenAI API)
   - Envia via WhatsApp ou Instagram Direct
   - Registra mensagem no banco
   ↓
9. Atualiza métricas em tempo real (Redis + PostgreSQL)
   ↓
10. Frontend recebe updates via WebSocket (Socket.io)
```

---

### 2.3 Fluxo de Dados - Processamento de Respostas

```
1. Webhook recebe resposta (WhatsApp/Instagram)
   ↓
2. POST /api/v1/webhooks/{platform}
   ↓
3. Identifica prospect e campanha
   ↓
4. Salva mensagem inbound no PostgreSQL
   ↓
5. Atualiza status do prospect (replied)
   ↓
6. Dispara task Celery: messaging_tasks.process_reply
   ↓
7. Worker de LLM:
   - Analisa sentimento da resposta
   - Decide se precisa follow-up
   - Gera resposta (se configurado)
   ↓
8. Se necessário, envia follow-up
   ↓
9. Atualiza dashboard em tempo real
```

---

## 3. Segurança

### 3.1 Autenticação e Autorização

**JWT (JSON Web Tokens):**
- Access token (curta duração: 15 min)
- Refresh token (longa duração: 7 dias)
- Armazenamento seguro no frontend (httpOnly cookies)

**OAuth 2.0:**
- Para integração com Instagram
- Para integração com Google

**RBAC (Role-Based Access Control):**
- Roles: admin, user, viewer
- Permissões granulares por recurso

---

### 3.2 Proteção de Dados

**Criptografia:**
- Credenciais de contas integradas: AES-256
- Comunicação: TLS 1.3
- Senhas: bcrypt com salt

**LGPD Compliance:**
- Consentimento explícito para armazenamento
- Direito ao esquecimento (soft delete)
- Portabilidade de dados (export JSON)
- Logs de acesso e modificações

---

### 3.3 Rate Limiting e Anti-Abuse

**API Rate Limiting:**
- Por IP: 100 req/min
- Por usuário: 1000 req/hora
- Implementação: Redis + FastAPI middleware

**Scraping Rate Limiting:**
- Instagram: max 50 perfis/hora por conta
- Google: max 100 buscas/dia
- Rotação de IPs via proxies

**Messaging Rate Limiting:**
- WhatsApp: max 1000 mensagens/dia (conforme plano)
- Instagram: max 50 DMs/hora por conta
- Intervalos randomizados entre envios

---

## 4. Escalabilidade

### 4.1 Estratégias de Escala

**Horizontal Scaling:**
- API: múltiplas instâncias atrás de load balancer
- Workers: auto-scaling baseado em tamanho da fila
- Database: read replicas para queries pesadas

**Vertical Scaling:**
- Database: upgrade de recursos conforme crescimento
- Redis: clustering para alta disponibilidade

**Caching Strategy:**
- Cache de queries frequentes (TTL: 5 min)
- Cache de resultados de scraping (TTL: 24h)
- Cache de métricas de dashboard (TTL: 1 min)

---

### 4.2 Performance Optimization

**Backend:**
- Queries assíncronas com asyncpg
- Índices otimizados no PostgreSQL
- Paginação em todas as listagens
- Lazy loading de relacionamentos

**Frontend:**
- Code splitting por rota
- Lazy loading de componentes
- Memoização de componentes pesados
- Virtual scrolling para listas grandes

**Workers:**
- Batch processing de mensagens
- Paralelização de scraping
- Connection pooling

---

## 5. Monitoramento e Observabilidade

### 5.1 Logs

**Estrutura de Logs:**
- Formato: JSON estruturado
- Níveis: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Contexto: user_id, campaign_id, request_id

**Ferramentas:**
- Python: `structlog`
- Centralização: CloudWatch, Datadog, ou ELK

---

### 5.2 Métricas

**Métricas de Sistema:**
- CPU, memória, disco
- Latência de requests
- Taxa de erro
- Throughput

**Métricas de Negócio:**
- Campanhas ativas
- Mensagens enviadas/hora
- Taxa de conversão
- Custo por lead

**Ferramentas:**
- Prometheus + Grafana
- Custom dashboards

---

### 5.3 Alertas

**Condições de Alerta:**
- Taxa de erro > 5%
- Latência > 2s (p95)
- Fila Celery > 1000 tasks
- Conta bloqueada (Instagram/WhatsApp)
- Custo LLM > threshold

**Canais:**
- Email
- Slack
- PagerDuty (para críticos)

---

## 6. DevOps e Deploy

### 6.1 Ambientes

**Development:**
- Docker Compose local
- Banco de dados local
- Mock de APIs externas

**Staging:**
- Infraestrutura idêntica a produção
- Dados sintéticos
- Testes de integração

**Production:**
- Multi-region (opcional)
- Auto-scaling
- Backups automáticos

---

### 6.2 CI/CD Pipeline

```
1. Push para GitHub
   ↓
2. GitHub Actions trigger
   ↓
3. Run tests (pytest)
   ↓
4. Run linters (black, flake8, mypy)
   ↓
5. Build Docker images
   ↓
6. Push to Container Registry
   ↓
7. Deploy to Staging
   ↓
8. Run E2E tests (Playwright)
   ↓
9. Manual approval
   ↓
10. Deploy to Production (blue-green)
```

---

## 7. Custos Estimados (Mensal)

**Infraestrutura:**
- VPS/Cloud (AWS, DigitalOcean): $50-200
- PostgreSQL managed: $30-100
- Redis managed: $20-50
- S3 storage: $10-30

**APIs Externas:**
- WhatsApp Business API: $0.005-0.01/msg
- OpenAI API: $0.002/1K tokens (GPT-4o-mini)
- Proxies: $50-200
- Google Maps API: $5/1000 requests

**Ferramentas:**
- Sentry: $26/mês (plano team)
- Monitoring: $20-50

**Total Estimado:** $200-700/mês (para começar)

