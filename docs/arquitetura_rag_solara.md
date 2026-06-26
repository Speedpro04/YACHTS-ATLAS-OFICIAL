# Arquitetura RAG: Capitã Solara (Expert Edition)

Este documento detalha a arquitetura de **Retrieval-Augmented Generation (RAG)** utilizada pela Capitã Solara para responder dúvidas sobre normas náuticas com altíssima precisão e performance escalável.

## Visão Geral

A Capitã Solara utiliza um motor de busca semântica em duas vias principais:
1. **Pipeline de Dados (Ingestão):** Processamento rápido em lote usando `polars`.
2. **Motor de Busca (Recuperação):** Busca vetorial nativa no banco de dados usando a extensão `pgvector` do PostgreSQL.

A combinação dessas tecnologias garante que o sistema seja extremamente eficiente, não importa se temos 100 ou 100.000 seções de normas técnicas cadastradas.

---

## 1. Pipeline de Dados: Velocidade Extrema com `polars`

Para transformar os textos brutos das normas em vetores matemáticos (embeddings), utilizamos a biblioteca **`polars`**.

**Por que `polars`?**
- Escrito em Rust, é projetado para processamento paralelo e vetorizado.
- Evita o alto consumo de memória do `pandas` ao processar grandes volumes de texto (como manuais e regulamentos marítimos).
- Permite processar e enviar requisições à OpenAI (para gerar embeddings) em lotes (*batches*) de forma limpa e muito performática.

### Fluxo de Ingestão:
1. O `polars` consulta a tabela `normas_conteudo` no Supabase e carrega todas as normas que ainda não possuem embeddings (`embedding IS NULL`).
2. O DataFrame organiza os textos combinando `titulo`, `secao` e `conteudo` para otimizar o contexto semântico.
3. Os dados são enviados para a API da OpenAI (`text-embedding-3-small`).
4. Os vetores gerados são injetados de volta no Supabase rapidamente.

---

## 2. Motor de Busca Vetorial: `pgvector` no Supabase

Em vez de baixar todos os vetores para a memória do servidor Python e calcular o Cosseno manualmente, a busca agora é delegada ao **banco de dados PostgreSQL**.

**Por que `pgvector`?**
- **Zero Overhead de Rede:** Não precisamos trafegar gigabytes de dados vetoriais entre o banco e a API Python.
- **Índices HNSW (Hierarchical Navigable Small World):** O Supabase utiliza um índice HNSW para a coluna de embeddings. Em vez de escanear a tabela inteira (busca linear), ele navega por grafos matemáticos para encontrar a resposta em milissegundos.
- **Segurança (Fail-Closed):** A função de busca (`match_normas_conteudo`) possui regras de negócio embutidas: só retorna resultados de normas que estão ativas e verificadas (`status_verificacao = 'verificada'`).

### Fluxo de Recuperação (RAG):
1. O usuário faz uma pergunta no chat da Capitã Solara.
2. O backend (`chatbot_service.py`) passa pelos *Guard Rails* de segurança.
3. Gera um único embedding da pergunta usando a OpenAI.
4. Chama a Remote Procedure Call (RPC) `match_normas_conteudo` no Supabase.
5. O Supabase calcula a similaridade cosseno nativamente no banco de dados e retorna as 5 seções mais relevantes.
6. A Capitã Solara usa esse contexto para gerar a resposta.

---

## Benefícios do Novo Padrão (Expert Upgrade)

* **Agilidade na Resposta:** O LLM recebe o contexto exato e restrito à pergunta, respondendo de forma afiada.
* **Redução de Custos:** `polars` processa dados com menos memória, e `pgvector` elimina a necessidade de escalar a RAM do servidor Python.
* **Escalabilidade Infinita:** Se no futuro adicionarmos apostilas de Arrais, Mestre e Capitão, a busca continuará ocorrendo em frações de segundo graças ao índice HNSW.
