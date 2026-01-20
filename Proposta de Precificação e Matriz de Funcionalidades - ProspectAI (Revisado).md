# Proposta de Precificação e Matriz de Funcionalidades - ProspectAI (Revisado)

## 1. Estrutura de Precificação

Com base na análise de mercado de ferramentas de prospecção e automação [1] [2] [3], o modelo de precificação mais adequado para o **ProspectAI** é o **Tiered Pricing (Preços em Camadas)**, com o volume de prospecção e o acesso a funcionalidades avançadas (como a API Oficial do WhatsApp e múltiplos Agentes de IA) como principais diferenciais.

Propomos quatro planos: **Free**, **Starter**, **Pro** e **Scale**.

| Plano | Preço Sugerido (Mensal) | Público-Alvo | Principal Diferencial |
| :--- | :--- | :--- | :--- |
| **Free** | R$ 0 | Teste e Microempreendedor | Acesso limitado para testar a qualidade da busca e do Agente de IA. |
| **Starter** | R$ 199,90 | Empreendedor Individual/Freelancer | Volume de prospecção moderado e acesso a 1 Agente de IA. |
| **Pro** | R$ 399,90 | Pequena Agência/Empresa | Alto volume de prospecção, múltiplos Agentes de IA e API Oficial do WhatsApp. |
| **Scale** | R$ 799,90 | Agência de Grande Volume/Empresa | Volume ilimitado, todos os recursos avançados e suporte prioritário. |

*Nota: Os preços são sugestões baseadas em benchmarks brasileiros (como o Dispara.ai [3]) e internacionais (como o Apollo.io [2]), e devem ser ajustados após testes de mercado.*

---

## 2. Matriz de Funcionalidades por Plano

A tabela a seguir detalha quais funcionalidades do SaaS estarão disponíveis em cada plano, utilizando os módulos definidos no planejamento inicial. **O uso do Agente de IA (LLM) é incluído em todos os planos pagos e limitado apenas pelo volume de prospecção e o número de Agentes que podem ser criados.**

| Funcionalidade | Free | Starter | Pro | Scale |
| :--- | :--- | :--- | :--- | :--- |
| **Busca e Prospecção** | | | | |
| Busca Google (Localização/Nicho) | ✅ | ✅ | ✅ | ✅ |
| Busca Instagram (Seguidores/Atividade) | ✅ | ✅ | ✅ | ✅ |
| Filtros Avançados de Qualificação | ❌ | ✅ | ✅ | ✅ |
| **Limite de Prospects Encontrados/Mês** | 50 | 500 | 2.000 | Ilimitado |
| **Agentes de IA (LLM)** | | | | |
| Criação de Agente (Personalidade/Tom) | 1 | 1 | 5 | Ilimitado |
| Reutilização de Agentes | ❌ | ✅ | ✅ | ✅ |
| **Uso do Agente de IA (Geração de Mensagens)** | Incluído | Incluído | Incluído | Incluído |
| **Gestão de Campanhas** | | | | |
| Campanhas Ativas Simultâneas | 1 | 3 | 10 | Ilimitado |
| Edição de Planos de Atendimento | ✅ | ✅ | ✅ | ✅ |
| **Canais de Contato** | | | | |
| Instagram Direct (Via Scraping/API Não Oficial) | ✅ | ✅ | ✅ | ✅ |
| WhatsApp (Via API Não Oficial/Simulação) | ❌ | ✅ | ✅ | ✅ |
| **WhatsApp Business API Oficial (Meta)** | ❌ | ❌ | ✅ | ✅ |
| **Dashboard e Relatórios** | | | | |
| Dashboard Básico (KPIs) | ✅ | ✅ | ✅ | ✅ |
| Histórico de Interações (CRM Básico) | ✅ | ✅ | ✅ | ✅ |
| Relatórios de Funil de Conversão | ❌ | ✅ | ✅ | ✅ |
| Comparativo de Performance entre Campanhas | ❌ | ❌ | ✅ | ✅ |
| **Suporte e Segurança** | | | | |
| Suporte Padrão (Email) | ❌ | ✅ | ✅ | ✅ |
| Suporte Prioritário (Chat/Telefone) | ❌ | ❌ | ❌ | ✅ |
| Integração com CRM (HubSpot, Pipedrive) | ❌ | ❌ | ✅ | ✅ |
| SSO (Single Sign-On) | ❌ | ❌ | ❌ | ✅ |

---

## 3. Detalhamento dos Planos (Revisado)

### Plano Free (R$ 0/mês)

O objetivo é permitir que o usuário teste a qualidade da prospecção e da IA antes de se comprometer.

- **Limite de Busca:** 50 prospects encontrados por mês.
- **Agentes:** 1 Agente de IA básico. **O uso do Agente de IA para gerar mensagens está incluído e limitado ao volume de prospecção.**
- **Canal:** Apenas Instagram Direct (via scraping/API não oficial).
- **Relatórios:** Acesso apenas ao Dashboard Básico (total de envios, total de respostas).
- **Restrições:** Não inclui a API Oficial do WhatsApp, filtros avançados de busca ou suporte.

### Plano Starter (R$ 199,90/mês)

Ideal para o empreendedor que está começando a automatizar sua prospecção e precisa de um volume moderado de leads.

- **Limite de Busca:** 500 prospects encontrados por mês.
- **Agentes:** 1 Agente de IA. **O uso do Agente de IA para gerar mensagens está incluído e limitado ao volume de prospecção.**
- **Canais:** Instagram Direct e WhatsApp (via simulação/API não oficial).
- **Relatórios:** Relatórios de Funil de Conversão.
- **Benefício Chave:** Acesso aos Filtros Avançados de Qualificação.

### Plano Pro (R$ 399,90/mês)

Plano mais popular, focado em pequenas agências e empresas que buscam escala e profissionalismo.

- **Limite de Busca:** 2.000 prospects encontrados por mês.
- **Agentes:** 5 Agentes de IA (permite testar diferentes abordagens). **O uso do Agente de IA para gerar mensagens está incluído e limitado ao volume de prospecção.**
- **Benefício Chave:** **Acesso à API Oficial do WhatsApp Business (Meta)**, garantindo maior segurança e confiabilidade no envio.
- **Recursos Avançados:** Comparativo de Campanhas e Integração com CRM.

### Plano Scale (R$ 799,90/mês)

Destinado a grandes agências e empresas com alto volume de prospecção e necessidades de segurança e suporte de nível Enterprise.

- **Limite de Busca:** Ilimitado.
- **Agentes:** Ilimitado. **O uso do Agente de IA para gerar mensagens está incluído e ilimitado.**
- **Recursos Exclusivos:** Suporte Prioritário, SSO (Single Sign-On) e relatórios customizados.
- **Benefício Chave:** Todos os recursos da plataforma sem restrições de volume.

---

## 4. Estratégia de Monetização Adicional (Revisado)

Para otimizar a receita e alinhar o custo ao valor entregue, sugere-se a implementação de um modelo de **Pay-as-you-go** apenas para o volume de prospecção excedente.

| Item | Preço Sugerido (Adicional) |
| :--- | :--- |
| **Pacote de 500 Prospects Adicionais** | R$ 99,90 |
| **Usuário Adicional (Plano Pro/Scale)** | R$ 49,90/mês |

---

## Referências

[1] PhantomBuster. *Pricing | PhantomBuster*. [Online]. Disponível em: `https://www.phantombuster.com/pricing`
[2] Apollo.io. *Apollo.io Pricing Plans | Sales Intelligence Platform Pricing*. [Online]. Disponível em: `https://www.apollo.io/pricing`
[3] Dispara.ai. *Nossos Planos - Dispara Aí*. [Online]. Disponível em: `https://dispara.ai/nossos-planos/`
