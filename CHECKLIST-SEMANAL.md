# Manutenção Preditiva Semanal — Yachts Atlas

> **Como usar:** abra uma sessão e diga *"roda o checklist semanal"*. Eu executo tudo que é consulta ao banco e aos logs, e te devolvo só o que estiver fora do normal. Os itens marcados com 👤 só você consegue conferir — eles não têm como ser automatizados de fora.

**Por que existe:** o sistema falha em silêncio. Webhook que parou, e-mail que virou spam, WhatsApp que desconectou — nada disso apita. A marina só descobre quando já custou dinheiro ou confiança. Este checklist é o apito.

**Regra de ouro:** um item do Nível 1 fora do lugar interrompe tudo — resolve ele antes de olhar o resto.

---

# 🔴 NÍVEL 1 — Existencial

*Se qualquer um destes estiver quebrado, o negócio para. Verifique primeiro, sempre.*

## 1.1 O site está no ar

**Por que importa:** óbvio, mas é o único item cuja falha você descobre por telefone, pela marina.

```bash
curl -s -o /dev/null -w "site: %{http_code} em %{time_total}s\n" https://yachtsatlas.online
```

**Normal:** `200`, abaixo de 3 segundos.
**Se falhar:** EasyPanel → o container está de pé? Reiniciar. Se voltar sozinho e cair de novo, olhar memória do servidor.

## 1.2 O pagamento está sendo registrado

**Por que importa:** este é o coração da recorrência. Se o webhook do Stripe parar, a marina paga e **o sistema não fica sabendo** — e o porteiro corta quem está em dia. É a pior falha possível: cliente pagando, sem acesso, com razão para cancelar.

```sql
select status, count(*) as qtd, max(created_at) as ultimo
from public.payments
where created_at > now() - interval '7 days'
group by status;
```

**Normal:** pelo menos um registro por marina ativa no mês. Silêncio total numa semana com marinas ativas é suspeito.
**Se estiver vazio:** conferir no painel da Stripe se os eventos estão sendo entregues (Developers → Webhooks → últimos envios). Falha de entrega aparece lá com o erro.

## 1.3 Ninguém foi cortado por engano

**Por que importa:** marina em dia sem acesso ao painel é o pior estrago de reputação que este sistema pode causar. Ela avisa as outras.

```sql
select u.email,
       coalesce(u.raw_user_meta_data->>'pagamento','(sem marcacao)') as pagamento,
       u.raw_user_meta_data->>'inadimplente_desde' as inadimplente_desde,
       case when u.raw_user_meta_data->>'inadimplente_desde' is not null
            then (now()::date - (u.raw_user_meta_data->>'inadimplente_desde')::timestamptz::date)
       end as dias_em_atraso,
       u.last_sign_in_at
from auth.users u order by u.created_at;
```

**Normal:** quem pagou está sem `inadimplente_desde`. Quem tem a marca, tem menos de 20 dias — ou foi cortado com razão.
**Atenção especial:** conta com `inadimplente_desde` **e** pagamento recente na tabela `payments` = webhook não limpou a marca. Corrigir na hora.

## 1.4 O backup existe 👤

**Por que importa:** a cadeia de custódia **é** o produto. Registro selado perdido não se recria — e o dossiê perde todo o valor jurídico e comercial.

**Onde:** painel do Supabase → Database → Backups.
**Normal:** backup diário dos últimos 7 dias listado.
**Se não houver:** o plano gratuito tem retenção curta. Vale considerar o upgrade **antes** da primeira marina real entrar, não depois.

---

# 🟠 NÍVEL 2 — Dinheiro e confiança

*Não derrubam o sistema, mas fazem dinheiro deixar de entrar e confiança se perder.*

## 2.1 O e-mail está chegando na caixa de entrada

**Por que importa:** cobrança no spam é dinheiro que não entra — e a marina jura que nunca foi avisada. Já aconteceu: o domínio era novo e sem DKIM, e a recuperação de senha caía com aviso de phishing.

```bash
nslookup -type=TXT yachtsatlas.online | grep -i spf
nslookup -type=TXT hostingermail1._domainkey.yachtsatlas.online | grep -i "p="
nslookup -type=TXT _dmarc.yachtsatlas.online | grep -i dmarc
```

**Normal:** os três respondem. SPF com `include`, DKIM com uma chave `p=`, DMARC presente.
**👤 E o teste que vale mais:** peça um código no Portal do Proprietário e veja **onde ele cai**. Caixa de entrada = tudo certo. Spam = a reputação regrediu; marque "não é spam" e observe na semana seguinte.

## 2.2 O WhatsApp está conectado

**Por que importa:** a instância cai sozinha — o WhatsApp derruba sessões antigas sem avisar. E quando cai, os avisos de cobrança param sem nenhum erro aparecer.

```bash
curl -s --max-time 20 -H "apikey: SUA_CHAVE" \
  "https://whatsapp.yachtsatlas.online/instance/connectionState/Programa-Atlas"
```

**Normal:** `{"instance":{"instanceName":"Programa-Atlas","state":"open"}}`
**Se vier `close` ou `connecting`:** abrir o painel da Evolution e parear de novo pelo QR.
**Também olhar o log da Evolution:** se `ChannelStartupService` aparecer a cada minuto, a conexão está instável mesmo dizendo "open" — foi o que o Redis desligado causava.

## 2.3 A régua de cobrança rodou

**Por que importa:** o cron **só avisa** — o corte acontece na leitura, então ninguém é cortado por engano se ele falhar. Mas se ele não rodar, a marina é cortada **sem nunca ter sido avisada**. Isso é indefensável numa conversa.

```bash
python -m app.services.cron_cobranca
```

**Normal:** ele é idempotente — rodar de novo não duplica aviso. Se listar avisos enviados, está funcionando.
**👤 Conferir também:** o agendador que roda isso 1x/dia está de pé? (Pendência conhecida — ver PRD.)

## 2.4 Dossiês emitidos — o termômetro do negócio

**Por que importa:** **este é o número mais importante do produto.** O dossiê é 100% receita da marina. Marina que assina e nunca emite não vê valor — e vai cancelar no mês 3, sem avisar. O silêncio aqui é o sinal mais antecipado de churn que existe.

```sql
select count(*) as dossies_semana, max(created_at) as ultimo
from public.dossie_saidas
where created_at > now() - interval '7 days';

select count(*) as registros_semana
from public.registros
where created_at > now() - interval '7 days';
```

**Normal:** marina ativa gera registros toda semana. Zero dossiê em um mês, com marina paga, é motivo de **ligar para ela** — não de esperar.

---

# 🟡 NÍVEL 3 — Saúde do produto

*O sistema funciona, mas aqui aparecem os problemas antes de virarem reclamação.*

## 3.1 Erros nos logs

**Por que importa:** erro que ninguém lê vira incidente daqui a três semanas.

Eu consulto os logs de autenticação, banco e storage do Supabase e te trago só o que for `error` ou `warning` da semana.

**👤 E no EasyPanel:** logs do container do Atlas. Procurar por `Traceback`, `500` e `Falha ao`.

## 3.2 O que a Solara não soube responder

**Por que importa:** **não é métrica de atendimento — é pesquisa de produto.** Pergunta que se repete não é caso de suporte, é tela que precisa mudar. E `respondida = false` é o sinal mais valioso: ou falta documentação, ou o produto não faz algo que a marina esperava que fizesse.

```sql
select pergunta, dominio, count(*) as vezes, max(criado_em) as ultima
from public.solara_perguntas
where criado_em > now() - interval '7 days'
group by pergunta, dominio
order by vezes desc, ultima desc
limit 30;

select pergunta, count(*) as vezes
from public.solara_perguntas
where respondida = false and criado_em > now() - interval '30 days'
group by pergunta order by vezes desc limit 20;
```

**Gatilho de decisão:** a mesma pergunta 20 vezes = **mudar a tela**, não melhorar a resposta.

## 3.3 Marinas paradas

**Por que importa:** quem parou de usar já decidiu cancelar — só não avisou ainda. É a janela para recuperar.

```sql
select u.email, u.last_sign_in_at,
       (now()::date - u.last_sign_in_at::date) as dias_sem_entrar
from auth.users u
where u.last_sign_in_at < now() - interval '14 days'
order by u.last_sign_in_at;
```

**Normal:** marina ativa entra várias vezes por semana.
**Mais de 14 dias sem entrar:** ligar. Não mandar e-mail — ligar.

## 3.4 Integridade dos registros selados

**Por que importa:** é a promessa central do produto. Se um hash não bater, o dossiê inteiro perde credibilidade — e é melhor descobrir antes que um comprador descubra.

```sql
select count(*) as registros_sem_hash
from public.registros where hash_sha256 is null;

select count(*) as verificacoes_invalidas
from public.integridade_logs
where valido = false and verificado_em > now() - interval '30 days';
```

**Normal:** zero nos dois. Qualquer número diferente de zero é investigação imediata.

---

# 🟢 NÍVEL 4 — Higiene e prevenção

*Nada quebra hoje. Mas é o que evita o problema do trimestre que vem.*

## 4.1 Trabalho não selado

**Por que importa:** rascunho parado é serviço que a marina fez, digitou e esqueceu de selar — logo, **não entra no dossiê e não vira valor**.

```sql
select ativo_id, categoria, titulo, updated_at
from public.registros_rascunho
where updated_at < now() - interval '7 days'
order by updated_at limit 20;
```

**Se houver:** avisar a marina. Ela vai agradecer.

## 4.2 Espaço e limites 👤

**Onde:** painel do Supabase → Settings → Usage.
**Olhar:** storage do bucket `media` (as fotos crescem rápido — até 430 por embarcação), tamanho do banco, e se algum limite do plano está perto.

## 4.3 Segredos e chaves

**Verificar se ainda são os certos e se nenhum vazou:**

- `VERIFICACAO_SECRET` — **nunca trocar depois do primeiro dossiê emitido** (invalida todo QR já impresso)
- `EVOLUTION_API_KEY` — quem tiver manda WhatsApp como você
- `EMAIL_PASSWORD` — senha da caixa Hostinger
- Chaves da Stripe e do Supabase

**Regra:** chave que apareceu em print, conversa ou repositório público deveria ser trocada. As do Yachts Atlas estão em repositório público **por decisão do fundador** — está registrado, não é esquecimento.

## 4.4 Dependências

```bash
cd backend && pip list --outdated | head -20
cd frontend && npm outdated | head -20
```

**Normal:** atualizar o que for correção de segurança. Versão maior (major) só com motivo — e nunca na semana de lançar nada.

---

# Registro das rodadas

| Data | Quem rodou | Nível 1 | Achados | Ações |
|---|---|---|---|---|
| | | | | |

> Preencha uma linha por semana. Em três meses, esta tabela mostra o que quebra com frequência — e é isso que merece ser consertado de vez, em vez de checado para sempre.
