# 20 — Normas Náuticas, Capitã Solara (IA) e Cache Redis

> Entrega de 19/06/2026. Camada de **conformidade regulatória** do Yachts Atlas:
> catálogo de normas náuticas, assistente de IA com guard rails fortes, cache
> Redis e diferenciação visual do portal do armador.

---

## 1. Visão geral

Esta entrega adiciona ao sistema a **camada de conformidade** que amarra o que já
existia (alertas, asset score, dossiê, checklist) sob um conceito único: o ativo
está organizado **segundo as normas náuticas**.

Componentes entregues:

1. **Catálogo de Normas** (tabela `normas` + endpoint + aba no sistema)
2. **Capitã Solara** — assistente de IA (chatbot RAG) com guard rails fortes
3. **Cache Redis** — camada de velocidade resiliente
4. **LP** — seção de conformidade + anúncio da IA
5. **Portal do Armador** — novo tom de azul para diferenciação visual

---

## 2. Catálogo de Normas

### Tabela `public.normas`
Migration: [`migration_normas_nauticas.sql`](../migration_normas_nauticas.sql)

Dado de **referência**: leitura pública (RLS), escrita só pelo backend (service role).
A RLS expõe **apenas** normas `verificada` + `ativo` — impossível mostrar ao cliente
uma norma não confirmada.

### Normas brasileiras verificadas (jun/2026)
Todas conferidas em fonte oficial (Marinha/DPC e ABNT):

| Código | Órgão | Escopo | Status |
| --- | --- | --- | --- |
| NORMAM-211 | Marinha (DPC) | Esporte e recreio (ex-NORMAM-03, reorg. out/2023) | ✅ verificada |
| NORMAM-201 | Marinha (DPC) | Mar aberto (Mod.2/2024) | ✅ verificada |
| NORMAM-202 | Marinha (DPC) | Navegação interior (Mod.1/2024) | ✅ verificada |
| NBR 14574 | ABNT | Recreio em fibra ≤24m (base do Selo ABNT-ACOBAR) | ✅ verificada |
| NORMAM-401 | Marinha (DPC) | Meio ambiente | ⚠️ a_verificar (oculta) |

> **Correção importante:** as NORMAM foram reorganizadas em 8 séries em 02/10/2023.
> A série 200 (Embarcações) e 400 (Meio Ambiente) são as relevantes aqui.

### Pendências de verificação
- **NORMAM-401**: confirmar escopo exato antes de publicar (hoje `a_verificar`).
- **NBR 11101**: descartada — o "termos náuticos" não teve confirmação em fonte oficial.

### Endpoint
`GET /api/v1/normas/` — lista normas verificadas/ativas, ordenadas. Cacheado no Redis.

### Frontend
- Aba **Normas** no sidebar do sistema (ícone de balança).
- Página `NormasTecnicas.tsx` — catálogo agrupado por órgão (NORMAM/ABNT/ISO).

---

## 3. Capitã Solara — Assistente de IA (chatbot RAG)

Assistente flutuante (popup premium, navy/dourado) presente em todo o sistema,
montado no `Layout`. Avatar: `frontend/public/capita-solara.png`.

### Arquitetura RAG
- **Modelo de conversa:** `gpt-5-mini` (OpenAI)
- **Embeddings:** `text-embedding-3-small`
- **Busca semântica:** em Python, com embeddings das normas cacheados no Redis
  (para o tamanho atual do catálogo; migrar para pgvector quando crescer — troca
  localizada em `chatbot_service.retrieve()`).

### Fluxo de uma pergunta
```
guard rail ENTRADA → rate limit (Redis) → recupera normas (RAG) →
guard rail ESCOPO (tem norma relevante? senão recusa) →
gpt-5-mini (responde só com o contexto) → guard rail SAÍDA (limpa PII) →
resposta + fontes citadas
```

### Arquivos
- `backend/app/services/chatbot_service.py` — orquestração RAG + OpenAI + sessão
- `backend/app/api/v1/chatbot.py` — endpoint `POST /api/v1/chatbot/ask`
- `frontend/src/components/CapitaSolara.tsx` — popup

---

## 4. Guard rails do chatbot (segurança forte)

Princípio: **a defesa mais forte é arquitetural, não baseada em prompt.**
Arquivo: `backend/app/services/chatbot_guardrails.py`
Testes: `backend/tests/test_chatbot_guardrails.py` (10 testes, todos passando).

| Restrição | Como é garantida | Força |
| --- | --- | --- |
| Somente normas | Só responde com norma relevante (score ≥ 0.35) + system prompt | 🧱 camadas |
| Nada de dados pessoais | PII removida na entrada e na saída; contexto nunca recebe PII | 🧱 + 🔒 |
| Não sondar outras marinas | Bloqueio na entrada + fonte de dados é só a tabela `normas` | 🔒 arquitetural |
| Não alterar dados | O bot não tem nenhuma ferramenta de escrita — só lê | 🔒 arquitetural |
| Forçar tudo | Fail-closed: na dúvida, bloqueia. 5 camadas. | ✅ |

---

## 5. Cache Redis

Arquivo: `backend/app/core/cache.py`. **Regra de ouro: o cache nunca derruba o app.**
Se o Redis estiver indisponível, tudo degrada em silêncio (só perde velocidade).

- Helpers: `cache_get_json`, `cache_set_json`, `cache_delete`, decorator `@cached`.
- Usos: catálogo de normas, embeddings das normas, memória de sessão e rate limit
  da Capitã.

---

## 6. Landing Page

- Nova seção **"Conformidade Regulatória"** (NORMAM, ABNT, ISO, alertas).
- Banner **"Uma IA para verificação de normas e conformidade"**.
- FAQ: "O dossiê segue as normas náuticas?".
- **Disclaimer honesto** (protege juridicamente): o Atlas *organiza e acompanha*
  a conformidade; a emissão de certificados oficiais cabe aos órgãos competentes.

---

## 7. Portal do Armador — diferenciação visual

Fundo alterado do navy quase-preto (`#010c20`) para um **gradiente azul mais claro**
(`#0d3056 → #0b2a4a`), com header e gradientes ajustados. Dá identidade própria ao
portal do proprietário, distinta do resto do sistema.

---

## 8. Variáveis de ambiente (EasyPanel)

Adicionadas nesta entrega (secrets **só** em env — repo é público):

| Variável | Função |
| --- | --- |
| `REDIS_URL` | Conexão Redis (cache) |
| `REDIS_DEFAULT_TTL` | TTL padrão do cache (opcional, default 3600) |
| `OPENAI_API_KEY` | Chave da OpenAI (chatbot) |
| `OPENAI_CHAT_MODEL` | Modelo de conversa (default `gpt-5-mini`) |
| `OPENAI_EMBEDDING_MODEL` | Modelo de embeddings (default `text-embedding-3-small`) |
| `CHATBOT_RATE_LIMIT_PER_MIN` | Limite anti-abuso (default 15) |
| `CHATBOT_MIN_RELEVANCE` | Score mínimo p/ responder (default 0.35) |

---

## 9. Próximos passos

- [ ] Smoke test da Capitã ao vivo (confirmar `gpt-5-mini` e `max_completion_tokens`).
- [ ] Confirmar escopo da NORMAM-401 e ativar (`verificada`).
- [ ] Normas internacionais (ISO/ABYC/CE) — fases LATAM/EUA.
- [ ] Migrar busca semântica para pgvector quando o catálogo crescer.
- [ ] Certificação da plataforma: ISO 27001 (dados) primeiro — terreno já sendo arado
      (auditoria, controle de acesso, RLS).
