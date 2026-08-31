# Registro das Operações de Tratamento de Dados Pessoais

**Yachts Atlas — AXOS HUB · CNPJ 26.998.571/0001-50**
Documento exigido pela LGPD, art. 37.
Versão 1 — 31/08/2026.

> **⚠️ ESTE DOCUMENTO AINDA NÃO ESTÁ COMPLETO.**
> Dois campos dependem de decisão do controlador e estão marcados como
> `[A DEFINIR]` ao longo do texto: o **prazo de retenção** (seção 6) e o
> **encarregado pelo tratamento** (seção 8). Enquanto estiverem em branco,
> este registro **não** deve ser apresentado a uma autoridade ou auditoria
> como documento final.

---

## 1. Quem é o controlador

A Yachts Atlas, operada pela AXOS HUB, é **controladora** dos dados de suas
clientes (as marinas) e das pessoas que se cadastram nos formulários públicos.

Em relação aos dados do **armador** e das pessoas citadas no histórico técnico
de uma embarcação, a Yachts Atlas atua como **operadora**: quem determina o
tratamento é a marina depositária, que mantém a relação contratual com o
armador. Esta distinção importa — ela define a quem o titular se dirige
primeiro e quem responde pelo quê.

## 2. O que a plataforma faz, em uma frase

A Yachts Atlas mantém a **custódia digital** do histórico documental de
embarcações: registros lançados pela marina, selados por hash SHA-256, que
podem ser reunidos num Dossiê de Custódia e compartilhados com terceiros
identificados pela marina.

**A plataforma não inspeciona embarcações.** Ela atesta a integridade e a
completude do registro, não a condição do bem. Isso limita o escopo do que
ela afirma e, portanto, do que trata.

## 3. Categorias de titulares

| Titular | Quem é | Onde os dados ficam |
|---|---|---|
| **Usuário da marina** | quem opera o painel | `profiles` |
| **Armador** | dono da embarcação | `ativos.proprietario_*`, `ativo_consentimentos` |
| **Pessoa citada no histórico** | condutor, técnico, responsável por manuseio | `registros.dados` |
| **Solicitante de dossiê** | comprador, corretor, seguradora, perito | `dossie_solicitacoes`, `dossie_saidas` |
| **Contato comercial** | marina prospectada ou indicada, parceiro | `marina_leads`, `leads_fundadoras`, `partner_leads`, `vega_leads` |
| **Visitante identificável por registro técnico** | quem acessa o sistema | `audit_logs` (IP e user-agent) |

## 4. Inventário — 22 tabelas com dado pessoal

| Tabela | Dados pessoais |
|---|---|
| `profiles` | e-mail, nome, telefone, whatsapp |
| `ativos` | nome, e-mail, telefone e documento do proprietário |
| `ativo_consentimentos` | nome e documento do titular (fotografados na data) |
| `registros` (campo `dados`) | condutor, habilitação, nº e validade do CHA, responsável pelo manuseio, quem lançou, quem rebocou, responsável, nome do técnico, quem enviou |
| `documentos` | nome do arquivo (pode conter nome de pessoa) |
| `dossie_solicitacoes` | nome, e-mail e telefone do solicitante |
| `dossie_saidas` | nome e e-mail do destinatário |
| `lgpd_solicitacoes` | nome e contato do titular requerente |
| `audit_logs` | endereço IP, user-agent |
| `integridade_logs` | endereço IP, user-agent |
| `marina_leads` | nome do contato, e-mail, whatsapp |
| `leads_fundadoras` | nome do contato, whatsapp, e-mail, CNPJ, endereço |
| `marinas_fundadoras` · `marinas_lancamento` | nome da marina, e-mail, telefone |
| `pagamentos_lancamento` | e-mail |
| `founder_program_spots` | nome do contato, e-mail, telefone |
| `brokers` | e-mail, whatsapp |
| `insurance_companies` | CNPJ, e-mail |
| `partner_leads` · `partner_clicks` | e-mail, telefone, user-agent |
| `vega_leads` · `vega_mensagens` | telefone, nome |
| `whatsapp_blocklist` | telefone |

Além do banco, o **armazenamento de arquivos** (bucket `media`, privado)
guarda documentos e fotografias enviados pela marina, que podem conter dado
pessoal em seu conteúdo.

## 5. Finalidade e base legal

| Operação | Finalidade | Base legal (art. 7º) |
|---|---|---|
| Cadastro e operação do painel | executar o contrato com a marina | **V** — execução de contrato |
| Registro do histórico técnico | constituir a custódia documental que é o produto | **V** — execução de contrato |
| Dados do armador no ativo | identificar o titular do bem custodiado | **V**, via a marina controladora |
| **Compartilhamento do dossiê com terceiro** | avaliação, seguro, vistoria ou transação | **I — consentimento do titular**, registrado em `ativo_consentimentos` |
| Trilha de auditoria (IP, user-agent) | segurança da informação e prova de acesso | **IX** — legítimo interesse |
| Prospecção comercial de marinas | oferta de serviço a pessoa jurídica | **IX** — legítimo interesse, com opt-out |
| Cobrança e pagamento | executar o contrato | **V** |

## 6. Retenção e eliminação

> **[A DEFINIR — decisão do controlador]**
>
> Hoje **não existe prazo de retenção declarado nem rotina de expurgo** em
> nenhuma parte do sistema. Verificado em 31/08/2026: as únicas referências a
> tempo de vida no código são caches técnicos, sem relação com dado pessoal.
>
> Três perguntas precisam de resposta antes que esta seção exista:
>
> 1. **Marina que cancela a assinatura** — por quanto tempo o histórico
>    custodiado permanece? Há uma tensão real aqui: a promessa do produto é
>    permanência, e apagar o histórico destruiria o valor que a marina pagou
>    para constituir. Mas "para sempre" também não se sustenta perante a ANPD
>    sem justificativa.
> 2. **Lead comercial não convertido** — quanto tempo um contato prospectado
>    e nunca respondido fica em `marina_leads`?
> 3. **Trilha de auditoria** — por quanto tempo IP e user-agent ficam em
>    `audit_logs`? A finalidade é segurança, e finalidade de segurança tem
>    prazo.

**O que já existe:** ativo não é excluído, é **arquivado**
(`arquivado_em`, `arquivado_por`, `arquivado_motivo`) — o gatilho
`trg_ativos_no_delete` recusa DELETE.

## 7. Direito do titular (art. 18)

Implementado em `backend/app/api/v1/lgpd.py` e na função de banco
`fn_lgpd_redigir`. Quatro tipos de pedido são aceitos: **eliminação, acesso,
correção e portabilidade**.

**O problema que este desenho resolve.** A tabela `registros` é *append-only*:
UPDATE e DELETE são recusados pelo banco inclusive para a chave de serviço, e é
isso que sustenta a promessa de custódia. Mas o histórico guarda nome de
condutor, habilitação e número de CHA — gente identificável. Diante de um
pedido de eliminação, *"é imutável, não posso"* não se sustenta.

**A saída não foi afrouxar a imutabilidade**, e sim abrir uma porta estreita e
autovalidada:

- só apaga campos de uma **lista fechada** de dez: `condutor`, `habilitacao`,
  `cha_numero`, `cha_validade`, `resp_manuseio`, `quem_lancou`, `quem_reboque`,
  `responsavel`, `tecnico_nome`, `enviado_por`;
- **exige vínculo** com uma solicitação registrada e não recusada;
- **recusa redação dupla** — um registro já redigido não é tocado de novo;
- **preserva o selo original** em `hash_pre_redacao` e recalcula o novo com a
  mesma fórmula;
- **marca o registro** com data, campos removidos e a solicitação que a
  originou;
- substitui o valor por `[removido a pedido do titular — LGPD art. 18]`, e o
  **dossiê declara a redação**. Apagar em silêncio seria adulterar o histórico
  — o oposto do que o produto promete.

Atender a solicitação é **ato administrativo da plataforma**, não do dono do
ativo: `_exige_admin` recusa qualquer outro papel.

## 8. Encarregado (DPO)

> **[A DEFINIR — decisão do controlador]**
>
> Nome, e-mail de contato e forma de acionamento. A LGPD (art. 41) exige que a
> identidade do encarregado seja **divulgada publicamente**, o que significa
> que o dado escolhido aparecerá na página de privacidade.

## 9. Medidas de segurança adotadas

**Controle de acesso ao banco.** RLS habilitada em todas as tabelas com dado
pessoal, sem política — o padrão *deny-all*: nada é alcançável pela API
pública. Todo acesso passa pelo backend, que autentica antes e usa a chave de
serviço. Ver a nota técnica `03-nota-tecnica-rls-deny-all.md`, que existe
porque o verificador do Supabase sinaliza essa configuração em INFO e um
auditor lendo a saída crua vai perguntar.

**Minimização.** CPF e CNPJ do proprietário são **mascarados** em toda saída
(`backend/app/core/pii.py`) — inclusive na linha de consentimento, para que o
documento não volte a existir em texto plano numa segunda tabela.

**Integridade.** Todo registro é selado com SHA-256 no momento da gravação. A
verificação pública **recalcula** os hashes contra o conteúdo (função
`fn_verificar_integridade_ativo`) — não apenas confere se a coluna está
preenchida.

**Imutabilidade.** `registros`, `dossie_saidas` e `ativo_consentimentos` são
append-only por gatilho. Correção se faz por **retificação**, com o original
visível ao lado.

**Rastro de compartilhamento.** Toda saída do dossiê grava destinatário,
finalidade, canal, data e IP em `dossie_saidas`, e o registro é **condição**
da entrega: se não for possível gravá-lo, a entrega é recusada (503).

**Isolamento de função.** Desde 31/08/2026, `fn_verificar_integridade_ativo`
não é mais executável por usuário autenticado — antes, uma marina logada podia
consultar o estado de custódia de ativo de outra.

## 10. Lacunas conhecidas nesta data

Registradas aqui por honestidade, e no `PRD.md` com número:

1. **Retenção não definida** (seção 6) — item 41.
2. **Encarregado não designado** (seção 8) — item 42.
3. **Proteção contra senha vazada desligada** — bloqueada pelo plano gratuito
   do Supabase; requer plano Pro. Item 31.
4. **OTP de acesso do proprietário expira em 1 hora** — longo para a
   finalidade. Item 32.
5. **Isolamento é por usuário, não por organização** — hoje não há dado
   cruzando entre marinas, mas o modelo não o impede estruturalmente. Item 29.
6. **`supervisord` roda como root** no contêiner de produção. Item 38.
