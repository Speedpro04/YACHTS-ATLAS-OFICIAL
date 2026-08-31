# Nota Técnica — por que 14 tabelas têm RLS sem política

**Yachts Atlas — AXOS HUB**
Versão 1 — 31/08/2026.

> **Para que este documento existe.** O verificador de segurança do Supabase
> lista 14 avisos `rls_enabled_no_policy` neste projeto. Eles **não** são
> defeito: são a configuração mais restritiva possível, adotada de propósito.
> Mas o verificador os sinaliza porque a mesma configuração apareceria se
> alguém tivesse **esquecido** de criar a política — a ferramenta não
> distingue intenção de esquecimento.
>
> Um auditor lendo a saída crua vai perguntar. Esta é a resposta, escrita
> antes da pergunta.

---

## 1. O que a configuração faz

No Postgres, uma tabela com *Row Level Security* **habilitada** e **nenhuma
política** não devolve linha alguma para papéis sujeitos a RLS. Não é
"permissivo por omissão" — é o contrário: **nega tudo por omissão**.

No Supabase, os papéis sujeitos a RLS são `anon` (visitante) e `authenticated`
(usuário logado), que são exatamente os papéis alcançáveis pela API REST
pública. O papel `service_role` **contorna** RLS por definição.

Portanto, nas 14 tabelas listadas:

- **pela API pública, com chave anônima: nada.**
- **pela API pública, com JWT de usuário logado: nada.**
- **pelo backend, com a chave de serviço: acesso total** — depois de o backend
  ter autenticado o usuário e verificado a autorização em código.

## 2. Por que este desenho, e não políticas por linha

Duas razões, e a segunda é a que mais importa numa auditoria.

**Primeira — a autorização real é mais rica que uma política SQL.** Quem pode
ver um ativo não é uma condição simples de coluna: é o dono, ou a marina, ou o
armador entrando pelo Portal do Proprietário (reconhecido por e-mail, com
permissão apenas de leitura), ou o administrador de plataforma. Essa regra vive
em `backend/app/core/authz.py`, testada, com o padrão de **nascer restrito**:

> `incluir_proprietario` é `False` por padrão de propósito — um endpoint novo
> nasce fechado até alguém decidir o contrário. É mais seguro esquecer de
> liberar do que esquecer de proibir.

**Segunda — um único caminho de entrada é auditável; dois não são.** Com
deny-all, existe exatamente **um** caminho até o dado: o backend. Todo acesso
passa por autenticação, autorização e pela trilha em `audit_logs`, que registra
conta, IP e ação. Se houvesse políticas RLS permitindo leitura direta pela API,
haveria um segundo caminho — legítimo, porém **fora da trilha**. Numa
plataforma cujo produto é justamente provar quem acessou o quê, um caminho não
registrado seria uma contradição com o que se vende.

## 3. As tabelas

| Tabela | Por que nada deve alcançá-la pela API pública |
|---|---|
| `ativo_consentimentos` | base legal do compartilhamento; append-only |
| `dossie_saidas` | livro-razão de quem recebeu cada dossiê |
| `dossie_solicitacoes` | pedidos com nome, e-mail e telefone de terceiros |
| `dossie_emitidos` | impressão digital de cada PDF emitido |
| `lgpd_solicitacoes` | pedidos de titulares exercendo direitos |
| `marinas_fundadoras` · `marinas_lancamento` | contratos e contatos de clientes |
| `pagamentos_lancamento` | vínculo entre pagamento e e-mail |
| `partner_leads` · `partner_clicks` | contatos e telemetria de parceiros |
| `vega_leads` · `vega_mensagens` | contatos e conversas de prospecção |
| `whatsapp_blocklist` | quem pediu para não ser contatado |
| `solara_perguntas` | perguntas feitas à assistente |

Nenhuma delas tem caso de uso em que o navegador precise ler direto do banco.
As que **têm** esse caso — `ativos`, `registros` — possuem políticas próprias
(3 e 2, respectivamente), porque ali a leitura direta é intencional e a regra
cabe em SQL.

## 4. Como verificar esta afirmação

Quem auditar não precisa acreditar no texto. Duas conferências:

**No catálogo do banco** — confirma que RLS está ligada e que não há política:

```sql
select c.relname, c.relrowsecurity as rls_ligada,
       (select count(*) from pg_policies p where p.tablename = c.relname) as politicas
from pg_class c join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relrowsecurity
order by politicas, c.relname;
```

**Pela API, na prática** — uma requisição à REST do Supabase com a chave
anônima contra qualquer uma das 14 tabelas deve voltar vazia. É o teste que um
atacante faria, e o resultado é o mesmo.

## 5. O que esta configuração NÃO resolve

Honestidade sobre o alcance, para que ninguém leia mais do que está escrito:

- **Não substitui a autorização em código.** Se o backend errar a checagem, a
  chave de serviço passa por cima de tudo. O deny-all fecha a porta da frente;
  quem guarda a porta de dentro é `authz.py` e seus testes.
- **Não isola marina de marina no modelo de dados.** O isolamento hoje é por
  usuário e aplicado em código, não por organização no esquema — pendência 29
  do `PRD.md`. Foi por uma falha desse tipo, e não de RLS, que em 31/08/2026 se
  descobriu que `fn_verificar_integridade_ativo` era executável por qualquer
  usuário autenticado, permitindo consultar o estado de custódia de ativo
  alheio. Corrigido no mesmo dia por revogação de `EXECUTE`.
- **Não protege o armazenamento de arquivos.** O bucket `media` é privado e tem
  regra própria; não é regido por RLS de tabela.

## 6. Os dois avisos que sobraram, e por quê

Depois da correção de 31/08/2026, o verificador saiu de 5 para 2 avisos de
nível WARN:

| Aviso | Situação |
|---|---|
| `extension_in_public` — extensão `vector` no schema `public` | Em uso pelo RAG da assistente. Mover o schema de uma extensão em produção exige recriar os índices vetoriais; risco maior que o benefício neste momento. Reavaliar na próxima manutenção de banco. |
| `auth_leaked_password_protection` — desligada | **Bloqueada pelo plano gratuito do Supabase.** Requer plano Pro. Decisão comercial do controlador, registrada como item 31 do `PRD.md`. |
