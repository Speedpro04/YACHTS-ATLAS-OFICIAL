# Memória de Decisões de Arquitetura — Yachts Atlas

Este documento centraliza as decisões de negócio e arquitetura tomadas ao longo do projeto. O objetivo é manter o alinhamento da plataforma como um software *High Ticket*, com forte foco na geração de valor para seguradoras, compradores e marinas.

---

## 1. Inteligência de Risco: Manutenção Preditiva vs Corretiva
**Data da Decisão:** 04/07/2026

### O Problema
Um logbook cronológico simples de manutenção ("Troca de óleo", "Troca de Bomba") é puramente descritivo e obriga a seguradora a interpretar os dados manualmente.

### A Solução "High Ticket"
Implementou-se no Frontend (`servicosCategorias.ts` -> `FICHA_MANUTENCAO`) a separação obrigatória da **Natureza da Manutenção**:
1. **Preditiva / Preventiva (Programada)**
2. **Corretiva (Reparo / Falha)**

Junto a isso, o **Sistema Náutico Afetado** foi padronizado utilizando terminologia náutica formal (ex: *Propulsão e Linha de Eixo*, *Faina de Porão*, *Geração e Distribuição de Energia*).

### Reflexo no Dossiê (PDF)
O script de montagem do PDF (`dossie_pdf.py`) foi programado para:
- **Calcular o Indicador de Saúde da Manutenção:** Mostra, logo no início da aba, a porcentagem de manutenções preventivas programadas versus corretivas. (Ex: "85% Preventiva / 15% Corretiva"). Seguradoras buscam a "parede verde" de preventivas.
- **Auditoria de Recorrência (Alerta):** Se o sistema detectar `Corretiva` acontecendo `> 1` vez no **mesmo subsistema** (ex: *Faina de Porão*), o Dossiê injeta um aviso de alerta vermelho, informando a seguradora que aquele sistema específico exige auditoria. Isso entrega extrema transparência e confiabilidade, elevando o valor do logbook auditado e protegendo o negócio de fraudes.

## 2. Padrão Tecnológico SHA-256 e Imutabilidade
**Data da Decisão:** Lançamento da Arquitetura WORM
- Todos os arquivos enviados (Documentos, Fotos, e Vídeos — incluindo aba *Casco* e *Diário de Bordo*) têm o hash **SHA-256** extraído pelo Frontend no exato momento do upload e anexado ao metadado do payload.
- As tabelas que recebem esses dados possuem regras restritas de banco (PostgreSQL) travando `UPDATE`. Dessa forma, o registro é um *Append-Only Log* perfeito, sustentando a promessa comercial de um **Cofre Digital Imutável**.

---

## 3. Aba Elétrica: Instrumentação Naval Completa (NORMAM / ANATEL / RIPEAM)
**Data da Decisão:** 04/07/2026

### O Problema
A aba Elétrica original era genérica — um checkbox de "todos operacionais". Embarcações modernas de alto valor possuem dezenas de equipamentos eletrônicos regulamentados, e nenhuma plataforma no Brasil registrava isso de forma auditável.

### Solução Implementada
A `FICHA_ELETRICA` foi expandida para ser o **registro técnico mais completo de eletrônica náutica do mercado brasileiro**, cobrindo:

#### Elétrica de Potência
- Tipo, tensão, capacidade (Ah) e estado do banco de baterias
- Status do alternador e carregador de bordo (Shore Power)
- Gerador de bordo com horímetro próprio
- Painel elétrico e disjuntores
- Teste de isolamento galvânico / fuga de corrente

#### Instrumentação e Eletrônicos (Normas Aplicadas)
- **VHF DSC** — Obrigatório por **NORMAM-02/DPC**. Registra modelo, MMSI e status do Canal 16 (monitoramento obrigatório por lei durante toda a navegação).
- **EPIRB / PLB** — Radiobaliza: registra marca, número de série, validade da bateria e status do **cadastro ANATEL** (obrigatório). O PDF do Dossiê emite alerta automático se a EPIRB estiver sem cadastro ANATEL — embarcação em situação irregular.
- **AIS Classe B** — Transponder de identificação automática: registra MMSI e status de transmissão.
- **GPS / Ploter** — Marca, modelo e status das cartas náuticas (atualizadas/desatualizadas).
- **Sonda / Ecobatímetro** — Status operacional.
- **Piloto Automático** — Status testado em manobra.
- **Radar de Navegação** — Status operacional.
- **Luzes de Navegação** — Conformidade com **RIPEAM/COLREGS 1972** (Regulamento Internacional para Evitar Abalroamentos no Mar): mastro, bordo (BB/BE), popa e âncora.

#### Alertas Automáticos no Dossiê PDF
Além da inteligência Preditiva/Corretiva (herdada da Manutenção), a aba Elétrica gera alertas específicos de compliance:
1. **⚠ NORMAM/ANATEL:** Se EPIRB instalada sem cadastro ANATEL — aviso vermelho no PDF.
2. **⚠ NORMAM-02/DPC:** Se VHF Canal 16 não monitorado — aviso vermelho no PDF.
3. **Indicador de Saúde Colorido:** Verde (≥70% preventiva), Laranja (40-69%), Vermelho (<40%).

---

## 4. Estratégia de Onboarding VIP & Apresentação do Painel (Vídeo Screencast + Supabase)
**Data da Decisão:** 13/08/2026

### O Problema
No mercado náutico de alto padrão, proprietários de marinas e armadores não compram soluções "às cegas". Apresentações estáticas ou e-mails genéricos pós-cadastro possuem baixa taxa de conversão. É necessário mostrar o produto "rodando" para gerar confiança imediata.

### A Solução Comercial & Tecnológica
1. **Vídeo de Demonstração (Screencast / Walkthrough):**
   - Gravação de tela (estilo Loom ou OBS) conduzida pelo próprio fundador.
   - O formato permite mostrar na prática a navegação no **Painel Técnico** (Motor, Elétrica, Documentação, etc.), demonstrando a facilidade de uso, as métricas de frota (Compliance) e a geração do Relatório Executivo PDF em tempo real.
   - Esse formato gera extrema autenticidade e prova social do software funcionando.
2. **Hospedagem e Restrição de Segurança no Supabase:**
   - O arquivo de vídeo é mantido em um Bucket Privado no Supabase Storage (`marina-exclusive-videos`).
   - A visualização é restrita através de **Signed URLs** com expiração curta (ex: 15 min) e validação de regras de acesso (RLS / Usuários autenticados no Onboarding), impedindo o vazamento ou download desautorizado do conteúdo.
3. **Fluxo de Onboarding VIP (Gatilho Pós-Pré-Cadastro):**
   - Logo após o preenchimento do pré-cadastro da marina (página de sucesso / onboarding), o proprietário é direcionado automaticamente para a página VIP com o player de vídeo incorporado, gerando impacto e autoridade imediata antes do contato comercial.

---

## 5. Acesso Pago: só entra quem pagou, 20 dias de atraso cortam
**Data da Decisão:** 19/08/2026

### O Problema
A recorrência é o produto, mas **nada no sistema dependia dela**. A marina se cadastrava e usava o Atlas sem pagar; quem cancelava seguia dentro para sempre. O campo `pagamento` era escrito no cadastro e **nunca lido por ninguém**.

### A Solução
`app/core/acesso.py` concentra a regra, e ela é **fail-open**: barra somente quem está EXPLICITAMENTE marcado como `pendente`, `cancelado` ou inadimplente. Conta sem a chave `pagamento` — manutenção, admin, marinas do piloto gratuito — passa direto. Um defeito ali tem que errar deixando entrar quem não devia, **nunca trancando do lado de fora quem paga**.

**O corte dos 20 dias é calculado na LEITURA, não por rotina agendada.** Duas consequências que motivaram a escolha:
- não depende de um cron estar de pé um mês depois;
- o religamento é automático — o webhook apaga `inadimplente_desde` e o acesso volta na requisição seguinte, sem ninguém rodar nada.

A data guardada é a da **primeira** recusa (`preservar=("inadimplente_desde",)`): o Stripe tenta várias vezes, e sem isso cada tentativa empurraria o corte para frente e ele nunca aconteceria.

**O porteiro roda em toda requisição, não só no login** — o login do frontend fala direto com o Supabase e nunca passou pelo backend. O `PrivateRoute` pergunta ao backend antes de montar o painel e mostra a tela de regularização, com o link do preço que a marina contratou.

### Validado em produção
Ciclo completo testado com cartão real (link recorrente de R$ 1,00): não pagou → não entra · pagou → entra · 20 dias em atraso → cortado · regularizou → volta sozinho · cancelou → acesso revogado.

---

## 6. O preço de fundadora é da CAMPANHA, não do estado da marina
**Data da Decisão:** 19/08/2026

### O Problema
`_oferta_marina` reservava vaga fundadora olhando **só a UF**. Marina de SC/SP/RJ/ES/BA recebia o link de US$ 200 tendo chegado de onde tivesse chegado — inclusive pelo site Oficial. Isso quebrava justamente a **indicação**, que é o motor do programa: a fundadora manda o link do Oficial para outra marina do mesmo estado, e a indicada — que deve entrar por US$ 250 — entrava por US$ 200 e consumia uma das 20 vagas.

### A Solução
A oferta é decidida pela **origem** do cadastro (`ORIGENS_DE_LANCAMENTO` em `leads.py`):
- **Lançamento** (campanha) → US$ 200, enquanto houver vaga no estado;
- **Oficial** (qualquer outra origem) → US$ 250, sempre.

Origem ausente ou desconhecida cai no Oficial **de propósito**: cobrar a mais de quem merecia menos se conserta devolvendo a diferença; queimar uma das 20 vagas com quem não veio da campanha não se conserta — não existe 5ª vaga em estado nenhum. Fora da campanha, a reserva nem chega a ser chamada.

**Vocabulário:** as duas frentes se chamam **Lançamento** (`lancamento.yachtsatlas.online`, repositório próprio, só US$ 200) e **Oficial** (`yachtsatlas.online`, só US$ 250). Não usar "LP" — apaga a diferença justo onde ela custa dinheiro.

---

## 7. Portal do Proprietário: duas contas, nunca a mesma porta
**Data da Decisão:** 20/08/2026

### O Problema
O portal nascia errado: era **o login da MARINA com uma etapa a mais** (a palavra secreta). Dar acesso ao dono significaria emprestar a credencial dela — e aí o armador enxergaria **a frota inteira, de todos os clientes**. Pior: `ativos` tinha uma única coluna de dono (`usuario_id`) e a listagem filtra por ela, então não havia sequer como mostrar só o barco dele.

### A Solução
O barco passa a guardar `proprietario_email` e `proprietario_telefone`. São dois caminhos para o mesmo ativo:

| | Chave | Pode |
|---|---|---|
| Marina | `usuario_id` | opera, edita, sela |
| Armador | `proprietario_email` | **só lê** |

O armador digita o e-mail, recebe um **código de uso único por e-mail E WhatsApp**, e entra. Não cria senha e não tem o que esquecer: o segredo passa a ser a caixa dele. **Não usar CPF nem nome da embarcação como credencial** — os dois estão no próprio dossiê e circulam com ele para comprador, corretor e seguradora.

O código é gerado pelo próprio Supabase (`admin.generate_link`) — a validação continua sendo dele; o sistema apenas escolhe o carteiro.

**Leitura-apenas por construção:** `get_ativo_autorizado` ganhou `incluir_proprietario`, que **só os endpoints de LEITURA passam**. Upload de foto e troca de categoria seguem exigindo `usuario_id`. O padrão é restritivo para que endpoint novo nasça proibido — esquecer de liberar é um chamado de suporte; esquecer de proibir é o armador escrevendo no dossiê que deveria ser prova independente dele.

**O primeiro contato é da marina, não do sistema.** O dono confia na marina onde deixa o barco, não numa plataforma que nunca ouviu falar — mensagem fria de número desconhecido falando do barco dele parece golpe, e o número bloqueado é o mesmo usado depois para cobrança. O sistema só responde a quem digitou o próprio e-mail. A explicação e a mensagem pronta para copiar ficam **no cadastro do barco**, onde a dúvida da marina nasce.

---

## 8. Avisos: WhatsApp e e-mail, pelo domínio próprio
**Data da Decisão:** 19–20/08/2026

- **Telegram removido.** Os avisos operacionais saem por **WhatsApp (Evolution API) e e-mail**, via `notify_service.notificar_fundador` — pelos dois, porque saber que uma marina parou de pagar não pode depender de um canal só estar de pé naquele dia.
- **WhatsApp atrás de um adaptador** (`whatsapp_service.py`): quem chama pede `enviar_whatsapp()` e não sabe quem entrega. Trocar Evolution por outro provedor é uma função nova e uma linha no despacho.
- **E-mail saiu do Gmail.** Remetente é `contato@yachtsatlas.online` via `smtp.hostinger.com`. Sair de um `@gmail.com` para caixa corporativa de marina é caminho curto para o spam — e cobrança que cai no spam é dinheiro que não entra. **SPF, DKIM e DMARC configurados** (o DKIM faltava e era o motivo de a recuperação de senha cair no spam com aviso de phishing).
- **`send_email` aceita remetente diferente do login**: a cobrança assina como `cobranca@yachtsatlas.online` (alias, sem senha própria) com `Reply-To` para a caixa real. A marina reconhece o assunto antes de abrir, e a resposta cai etiquetada no mesmo lugar — sem segunda conta para vigiar.

---

## 9. Régua de cobrança com registro do que já saiu
**Data da Decisão:** 19/08/2026

Avisos nos dias **0, 7, 15, 19 e 20** desde a primeira recusa, por e-mail e WhatsApp. O que já foi enviado fica em `avisos_cobranca` no `user_metadata`, e sem esse registro a régua tem os dois defeitos clássicos:
- rodar duas vezes no mesmo dia manda o mesmo aviso duas vezes ao cliente;
- ficar um dia sem rodar perde aquele aviso para sempre, porque a janela "faltam exatamente 7 dias" passou e não volta.

Envia-se o **marco vencido mais recente** que ainda não saiu: repetir a execução não duplica nada, e uma rotina parada três dias manda um aviso — não três de uma vez na caixa dela.

O cron (`python -m app.services.cron_cobranca`) **só avisa**. O corte é do porteiro, na leitura — a rotina pode falhar, atrasar ou ficar dias sem rodar sem que ninguém seja cortado por engano nem deixe de ser cortado.

---

## 10. Capitã Solara também responde sobre o produto
**Data da Decisão:** 21/08/2026

### O Problema
A Solara sabia normas — corpo grande, externo e estável, que vive no RAG. Mas a marina também pergunta *"onde coloco a foto do casco?"*, e isso o RAG não responde: é conhecimento **nosso**, pequeno e que muda toda semana.

### Por que NO PROMPT, e não no RAG
RAG existe para corpus grande demais para caber no contexto. O produto não é isso: são 18 categorias, 9 tipos de foto e meia dúzia de fluxos. Cabe inteiro no prompt — e ali está **sempre presente**, inclusive quando a pergunta mistura os dois mundos (*"preciso registrar a EPIRB, onde ponho isso no sistema?"*). Um roteador seria obrigado a escolher um lado e perderia metade da resposta; sem ele, a exigência vem da norma e o caminho vem do produto, numa resposta só.

Mesma receita já usada no ATLAS-SHOP, onde todo o conhecimento da Vega chega pelo `system_prompt`.

### Por que é GERADO do código, e não escrito à mão
Norma envelhece devagar; produto muda toda semana — no mesmo dia, "Casco / Exterior" virou "Integridade do Casco" e nasceu "Fotos da Embarcação". Texto manual sobre telas que mudam vira mentira em duas semanas, **dita com convicção**, porque ninguém revisa o que a IA respondeu para uma marina.

As listas saem de `dossieCategorias.ts` e `coberturaFotos.ts`. Escritos à mão só os FLUXOS ("como cadastrar", "como selar"), que são o desenho do produto e mudam devagar.

Como a imagem de produção não leva o frontend, a extração roda no repositório e o resultado é commitado — e `test_solara_suporte.py` extrai de novo e compara. Mudou categoria e ninguém regenerou: **a suíte quebra antes do deploy**. Regenerar: `python -m app.services.conhecimento_produto`.

### As três travas
- **Não inventa tela.** Caminho fora do conhecimento → ela diz que não sabe. Mandar a marina clicar num menu inexistente é pior que não responder: ela procura, não acha e conclui que o sistema está quebrado.
- **Não escancara o escopo.** A detecção exige forma de pergunta **E** palavra do produto. Só a palavra abriria para qualquer conversa que mencione barco; só o "como" abriria para o mundo inteiro. *"Como faço um bolo de cenoura?"* tem a forma e não passa.
- **Degrada sem cair.** Sumindo o conhecimento gerado, ela segue atendendo normas. Perder o suporte de produto é um chamado; perder a Solara é o painel sem assistente.

### Suporte humano continua sendo estratégia
Com 20–40 marinas, **as perguntas de suporte são a pesquisa de produto**. A Solara responde o "ONDE" (factual, uma resposta certa, que depois da terceira vez não ensina mais nada); o fundador responde o "POR QUÊ" (*"isso não faz sentido"*, *"achei confuso"*) — que é o sinal que a percepção de usuário dele precisa receber.

Por isso a tabela `solara_perguntas`: não é métrica de atendimento, é mapa do que está confuso. Pergunta que chega vinte vezes não é caso de suporte, é **tela que precisa mudar**. E `respondida = false` é o sinal mais valioso — ou falta documentação, ou o produto não faz algo que a marina esperava.

**Cobrança não terá LLM.** São 1–2 casos por mês, e é o momento em que se descobre POR QUE a marina está saindo. Uma LLM resolveria o pagamento e perderia a informação.

---

## 11. Sessão renovada não pode derrubar a tela
**Data da Decisão:** 21/08/2026

O `PrivateRoute` observava o **objeto** da sessão (`useEffect(..., [session])`). O Supabase renova o token sempre que a aba volta ao foco e entrega um objeto novo — mesmo usuário, identidade diferente. Resultado: spinner de tela cheia e nova ida ao backend **a cada troca de aba**, como se a página recarregasse.

Agora observa o **id do usuário**, que é estável. Quem pode usar o Atlas não muda porque um token foi renovado; muda quando troca o usuário.

Efeito colateral aceito: corte por inadimplência no meio da sessão não aparece mais na hora — mas o porteiro do backend recusa cada requisição de qualquer forma, e a tela de regularização aparece na navegação seguinte. Piscar a cada troca de aba, todo dia, para toda marina, custa mais que isso.

Na mesma linha, a conversa da Solara passou a sobreviver à navegação (`sessionStorage`): o `session_id` já ficava guardado, então o backend mantinha o contexto — mas a tela recomeçava do zero e quem estava no meio de uma dúvida perdia o fio.

---

## 12. Quem se cadastra e quem paga precisam ser a mesma pessoa
**Data da Decisão:** 21/08/2026

### O Problema (o mais caro que este sistema podia ter)
**A marina pagava e continuava sem acesso.**

O Payment Link é uma URL fixa e não carrega metadata. Sem identificação nela, o webhook só tinha o e-mail do checkout para descobrir de quem era o pagamento — e a **carteira Link da Stripe usa o e-mail da carteira**, que raramente é o mesmo que a marina digitou no cadastro.

Quando os dois não batiam:
- `user_id` ficava nulo;
- o pagamento **não** era gravado em `payments`;
- e `_marcar_pagamento_confirmado` **não** rodava — o acesso continuava `pendente`.

Não é hipótese: aconteceu no teste com cartão real. A tabela `payments` estava **vazia** enquanto a cobrança tinha sido feita e a marina fundadora tinha sido cadastrada.

### A Solução
O backend passa a devolver o link **com a identidade colada**:

```
<payment-link>?client_reference_id=<user_id>&prefilled_email=<email>
```

`client_reference_id` volta no evento do Stripe e **não depende de qual e-mail ela usou para pagar**. O webhook lê ele **antes** de tentar pelo e-mail — as duas metades são necessárias: de nada adianta o link carregar o id se o webhook continuar procurando só pela carteira.

`prefilled_email` ainda ajuda: reduz a divergência e poupa digitação no celular.

Se a criação da conta falhar, o link sai sem o id e sobra o caminho antigo (casar por e-mail) — pior, mas melhor que impedir a marina de pagar.

### Como isso passou despercebido
O teste com cartão real **funcionou**: a marina fundadora foi cadastrada e o e-mail saiu. O que ninguém conferiu foi se a linha existia em `payments`. O sintoma só apareceria com a marina reclamando que pagou e não entra — depois do lançamento.

Está no [CHECKLIST-SEMANAL.md](CHECKLIST-SEMANAL.md), item 1.2, exatamente por isso.

---

## 13. A régua de cobrança roda dentro da aplicação, não num cron externo
**Data da Decisão:** 21/08/2026

### O Problema
O caminho clássico seria agendar `python -m app.services.cron_cobranca` no servidor. Funciona — até o dia em que para de funcionar.

**Cron externo é a coisa mais silenciosa que existe numa operação de uma pessoa só:** some numa migração de servidor, quebra quando o caminho do Python muda, para quando alguém recria o container. E ninguém percebe, porque **não avisar é indistinguível de "não havia ninguém devendo"**. O erro só aparece na conversa mais cara possível — a marina cortada dizendo que nunca foi avisada.

### A Solução
`app/services/agenda.py`, ligada no startup do FastAPI. Se o Atlas está no ar, a régua está rodando; se o Atlas caiu, já existe um problema maior e mais visível.

**O que torna isso seguro é a régua já ser idempotente:** `marco_devido` consulta os avisos enviados, então rodar duas vezes no mesmo dia não duplica nada, e ficar dias parada não perde aviso (envia o marco vencido mais recente). O pior caso de uma reexecução é uma consulta a mais.

Detalhes que importam:
- **Marca no cache** (`cobranca:ultimo_dia_processado`) evita reprocessar a cada reinício — em dia de deploy seriam várias execuções seguidas.
- **Sem cache disponível, ela RODA.** Repetir custa uma consulta; não rodar custa uma marina cortada sem aviso.
- **`asyncio.to_thread`**: a régua faz I/O bloqueante (Supabase, SMTP, WhatsApp). No event loop, travaria as requisições das marinas enquanto varre a base.
- **Nunca derruba a aplicação.** Quem paga continua usando o sistema mesmo se a cobrança falhar.

### O que NÃO mudou
O corte continua sendo do porteiro, na leitura (`core/acesso.py`). A agenda **só avisa** — pode falhar, atrasar ou ficar dias parada sem que ninguém seja cortado por engano nem deixe de ser cortado. Há teste que guarda essa fronteira: se alguém mover o corte para a agenda, a suíte quebra.

---

## 14. Stripe: assinatura não paga, nunca cancelada
**Data da Decisão:** 21/08/2026

A conta estava configurada para **cancelar a assinatura** quando todas as tentativas de cobrança falhassem. Isso quebraria o religamento automático que sustenta o modelo: assinatura cancelada não existe mais, então a marina regulariza e **não há o que cobrar** — o webhook nunca chega, o acesso não volta, e cada caso vira recadastro manual.

Agora: **"marcar a assinatura como não paga"** + **"deixar a fatura vencida"**. A assinatura continua viva e cobrável; o corte é do porteiro aos 20 dias; o pagamento reativa sozinho.

Junto:
- **E-mails de cobrança da Stripe: desligados.** A régua própria é em português e com a marca do Atlas; os dois juntos fariam a marina receber duas cobranças diferentes pela mesma fatura.
- **Aviso de cartão a vencer: ligado**, apontando para a página hospedada pela Stripe. Age ANTES da falha e não conflita com a régua — cartão vencido é das causas mais bobas de perder cliente que queria ficar. O link personalizado (`axoshub.com`) estava errado ali: o e-mail vai para quem precisa **atualizar o cartão**, e essa tela não existe no Atlas.

---

## 15. Quem indicou quem só pode ser capturado no cadastro
**Data da Decisão:** 21/08/2026

### O Problema
A página `/marina-parceira` promete há tempos: *"Marinas parceiras que indicam novos membros participam dos dossiês gerados pela indicada durante o período fundador."*

E o banco tinha as colunas para isso — `indicacoes_feitas`, `indicada_por_slot`, `bonus_dossie_liberado`. Mas **nenhuma linha do backend escrevia nelas**, e o formulário de cadastro **nem perguntava quem indicou**.

Promessa pública, motor de crescimento (20 → 40 marinas), e nada registrando.

### Por que era urgente e não perfeccionismo
**O vínculo só existe no momento do cadastro.** Depois ninguém lembra quem indicou quem — nem a fundadora, nem a indicada — e não há como reconstruir a partir do banco. Descoberto na véspera de gravar o vídeo que ia amplificar essa promessa.

### A Solução
Campo opcional no cadastro ("Alguma marina indicou o Yachts Atlas para você?") e `_registrar_indicacao` em `leads.py`, com duas camadas:

1. **O texto cru sempre fica guardado** (`indicada_por_texto`), do jeito que ela digitou. A marina escreve o que lembra: um nome, um e-mail com typo, "falei com o João lá da náutica". Nada disso pode ser descartado por não casar com um registro.
2. **Se casar** — por e-mail ou por nome — o vínculo vira `indicada_por_slot` e a contagem da indicante sobe.

O que não casar, o fundador resolve à mão olhando o texto. Com 20 marinas é trabalho de minutos; perder o dado não tem conserto.

**Nunca credita vínculo por adivinhação:** creditar a indicação errada é pior que não creditar — vira dinheiro para quem não trouxe ninguém, enquanto o certo continua sem receber. E ninguém indica a si mesma.

**Best-effort:** falhar aqui não impede a marina de se cadastrar e pagar. O vínculo se resolve depois; a venda perdida, não.

### O que ficou manual, de propósito
A **liberação do bônus** (`bonus_dossie_liberado`) continua sendo decisão sua. Com 20 fundadoras e 1 indicação cada, controlar isso é trivial — e automatizar antes de ver o comportamento real seria construir no escuro.

---

## 16. Sinistro tem ficha própria, com antes e depois
**Data da Decisão:** 21/08/2026

### O Problema
A aba **mais grave** do sistema era a **mais pobre**: "Sinistros & Reparos" tinha quatro campos — data, evento, reparo, valor — para o assunto que mais pesa numa negociação e numa apólice. E o tema aparecia espalhado em outros dois lugares (avaria no Diário de Bordo, "histórico de sinistros" como texto livre no Seguro), sem nenhum deles ser o lugar de verdade.

Pior: o registro capturava um **estado**, não um **evento com desfecho**. A marina registrava a avaria e, meses depois, outra vistoria "Excelente". Dois registros soltos, nada ligando um ao outro.

### Por que isso é caro
**"Este barco teve um rombo no casco" derruba o valor.**
**"Teve um rombo, reparado pelo estaleiro X, com laminação de Y, laudo anexado e vistoriado" preserva** — às vezes aumenta, porque prova que a estrutura foi auditada de perto.

O dossiê não vale por esconder sinistro. Vale por **provar que ele foi resolvido direito**. Sem o desfecho, ele só carrega a má notícia.

### Por que na aba de Sinistros, e não na do Casco
Primeiro tentativa foi dividir a ficha do Casco em avaria/reparo. **Estava errado**, e o fundador viu antes de commitar: *"pode ocorrer vários tipos de sinistros"*.

Sinistro raramente fica num sistema só. Encalhe atinge casco, hélice, eixo e leme; incêndio na casa de máquinas atinge motor, elétrica e interior; alagamento atinge tudo. Uma ficha presa ao casco resolveria justamente o caso que, quando acontece de verdade, transborda dele.

Por isso os **sistemas atingidos são caixas independentes**, não escolha única — é essa lista que diz ao perito e ao comprador o tamanho real do evento.

E o **Casco continua simples**: vistoria de rotina é o uso normal daquela aba (osmose, gelcoat, cavernas, espessura). Sem avaria, o gerente preenche a vistoria e pronto. Empurrar campos de sinistro para lá faria toda vistoria carregar o peso de um evento que quase nunca aconteceu.

### Dois registros selados, nunca um editado
`resolve_id` liga o reparo à ocorrência. **Não é `retifica_id`**: retificar é "eu estava errado", resolver é "aquilo aconteceu e acabou". Misturar faria o dossiê mostrar um rombo real como se fosse erro de digitação.

A ocorrência é lacrada quando aconteceu; o reparo, quando terminou. **É essa trava que dá força ao "antes"** — ele foi selado quando ninguém sabia ainda como ia terminar. Se a marina registrasse tudo depois do conserto, um comprador desconfiado diria: *"você escreveu isso já sabendo o desfecho"*.

### O par de fotos é o coração da ficha
As duas obrigatórias, cada uma no seu momento, com a instrução explícita de **guardar o ângulo**: a comparação — mesma proa, mesmo ponto de vista — é o que transforma "teve um sinistro" em "teve um sinistro e foi resolvido assim".

---

## 17. Marlin Sea Focus é o ativo de demonstração
**Data:** 21/08/2026 · **Ativo:** `YA-IATE-2015-3A38`

Iate 38 pés, 2015, preenchido com **dados fictícios** para gerar o primeiro dossiê completo de ponta a ponta — algo que nunca tinha sido feito (`dossie_saidas` estava zerada).

**16 registros selados em 11 categorias**, cobrindo jan/2025 a jun/2026, e **25 documentos** no cofre (11 PDFs + fotos), todos com SHA-256.

### A história que ele conta, e por que ela foi construída assim
Não é uma lista de registros soltos: é uma **linha do tempo com desfecho**, montada para exercitar exatamente o que dá valor ao dossiê.

- **2025** — manutenção preventiva regular (250h, ânodos), vistoria de fundo com estrutura íntegra, auditoria elétrica completa (VHF Canal 16, EPIRB com ANATEL, AIS, RIPEAM), salvatagem conforme NORMAM.
- **14/03/2026** — impacto com objeto submerso: perfuração de 22 cm na proa. Capitania acionada, seguro comunicado, embarcação interditada. **Selado naquele dia, com status `atencao`** — sem saber ainda como terminaria.
- **28/04/2026** — reparo estrutural: laminado com chanfro 12:1, 8 camadas em resina epóxi a vácuo, **espessura final de 20mm contra 19mm do original**. Aponta para a ocorrência via `resolve_id`.
- **06/05/2026** — vistoria independente, contratada pelo proprietário, aprovando sem ressalva.
- **19/06/2026** — revisão de 500h, de volta à operação.

É a demonstração do argumento central: *"teve um rombo"* viraria problema; *"teve um rombo, e olha como foi resolvido"* vira **prova de cuidado**.

### Como foi preenchido
Registros inseridos direto no banco (mais rápido que digitar 13 fichas), documentos enviados ao Storage com o mesmo caminho e a mesma sanitização de nome do endpoint da aplicação. **Ressalva conhecida:** por não passar pela tela, este preenchimento não testa o formulário — defeito de campo que não salva ou validação que trava não seria pego por aqui.

Tudo marcado como fictício — prestador "Estaleiro Teste", CNPJ `00.000.000/0001-00`, nomes com "(ficticio)" — para ninguém confundir com dado real depois. **Serve também como ativo de demonstração** para o vídeo e para mostrar a marinas.

---

## 18. A nota do ativo não se mexia
**Data da Decisão:** 21/08/2026

### O Problema
O Marlin Sea tinha **16 registros selados e 25 documentos**, e o painel mostrava **"Bronze · Saúde 0%"**. Descoberto pelo fundador olhando a tela.

O cálculo funcionava — a mesma conta dava **87 (Ouro)**. O que não acontecia era a **atualização**: `calcular_saude_ativo` persiste em `ativos.progresso` e `ativos.classificacao`, mas só rodava em `GET /ativos/{id}/progresso`, e **o frontend nunca chamava esse endpoint**. O selo lia o valor gravado no cadastro e nunca mais tocado.

### Por que era grave
A nota existe para criar um incentivo: *vale a pena alimentar o cofre*. Se ela não se mexe quando a marina trabalha, **vira enfeite** — e no dossiê sairia um número contradizendo o próprio conteúdo do documento.

Agora recalcula ao selar registro. Best-effort: falhar não pode impedir o selo. O registro é o produto; a nota é derivada e pode ser recalculada depois.

### Como a nota funciona (para não reinventar depois)
| Peso | Mede | Máximo em |
|---|---|---|
| 50% | abrangência | 1 registro em cada uma das 10 categorias-núcleo |
| 25% | profundidade | 6+ registros de manutenção/motor |
| 15% | documentos | 8+ documentos com integridade verificada |
| 10% | estrutural | ter registro de casco |

Bronze <50 · Prata 50–79 · Ouro 80+

**Atenção:** documento é gravado com status **`verified`** (não "validado") — é esse valor que a taxa de verificação procura. Gravar diferente faz o documento valer metade dos pontos.

### Duas ressalvas registradas, sem decisão ainda
**A escala é generosa e pouco discriminante.** Preencher as 10 abas uma vez com 8 documentos já dá **83 → Ouro**. O Marlin Sea, com 18 meses de histórico, deu 87 — só 4 pontos acima do mínimo bem feito. Bronze só acontece com quem mal usou o sistema, então a classificação diferencia pouco numa negociação.

**E a nota não mede saúde: mede volume de cadastro.** Em nenhum momento ela pergunta se está tudo bem. O Marlin Sea teve um rombo no casco e ficou interditado — nota 87, Ouro. O `_health_map` até olha status (aba com registro em "atenção" fica amarela), mas **o score ignora**: dá para ter duas abas amarelas e Ouro ao mesmo tempo.

Um comprador lê "Ouro" e entende *"barco excelente"*, não *"dossiê completo"*.

Caminhos possíveis, a decidir: **(A)** renomear para *Índice de Custódia* / *Completude do Dossiê* — honesto, e coerente com o PRD, que diz que o Yachts Atlas **não inspeciona a embarcação**; ou **(B)** fazer a nota penalizar registro em atenção, sinistro sem desfecho e documento vencido. A inclinação é (A): dar nota de saúde a um ativo que não se vistoriou é assumir responsabilidade que não é da plataforma.

---

## 19. O histórico selado estava aberto para qualquer conta
**Data da Decisão:** 21/08/2026

### O Problema
Nenhum endpoint de `registros` verificava autorização. Nem para ler, nem para escrever.

`GET /registros/{ativo_id}` devolvia os registros selados de **qualquer barco** para **qualquer conta autenticada**, bastando o id — e o id é previsível (`YA-IATE-2015-3A38`). Trocando os dígitos finais, uma marina varria os clientes das outras.

E escrever também passava: `_owner_do_ativo` apenas **descobria** de quem era o ativo para preencher o campo — nunca perguntou se quem pedia tinha direito. Dava para selar registro no barco de outra marina, e **selar é irreversível**.

Isso tornava inútil a trava construída em `core/authz.py`: ela protegia os documentos, e os registros passavam por fora — justamente na tabela que é o produto.

### Como apareceu
O fundador reclamou que o armador **não conseguia abrir nada** no Portal do Proprietário. Investigando por que o portal não lia, apareceu que qualquer um lia.

### A regra, agora em nove endpoints
- **Ler** (`_pode_ler`) — a marina dona **e** o armador (`incluir_proprietario=True`). Ver o próprio barco é direito do dono.
- **Escrever** (`_so_a_marina`) — só a marina. Criação, retificação, rascunho, edição, descarte e selagem.

Rascunho também é da marina: é trabalho em andamento, ainda não selado, e o dono não vê o que ela está digitando.

Os endpoints que recebem o id do RASCUNHO precisam de um salto a mais (`_ativo_do_rascunho`) — sem ele, a checagem seria feita contra um id que não é de ativo nenhum e passaria batido.

### O teste que mais importa
`test_todo_endpoint_tem_alguma_guarda` varre o módulo e exige guarda em cada `@router`. Os testes por endpoint cobrem o que existe hoje; esse cobre **o que alguém acrescentar amanhã**.

E há um teste guardando a distinção entre as duas guardas: se virarem a mesma coisa, ou o dono perde o portal, ou passa a escrever no dossiê que deveria ser prova independente dele.

---

## 20. Portal do Proprietário: ver é direito do dono
**Data da Decisão:** 21/08/2026

O portal entregava pouco, e o fundador listou três coisas — todas certas:

**A capa mostrava o barco de outra pessoa.** A imagem estava fixa no código (`/boat-picture-light.jpg`, foto de banco). O armador abria o portal justamente no momento em que deveria reconhecer o próprio barco. Agora usa a foto do cofre — vitrine primeiro, que é a escolhida pela marina para apresentar o ativo.

**A nota de saúde não aparecia.** A marina via "Ouro · 87%", o dono não via nada. E há um ângulo comercial: essa nota é a prova de que a marina está fazendo bem o trabalho dela — **mostrar ao armador reforça a marina**, não a expõe.

**Ele não conseguia abrir nada** — o que levou ao achado de segurança acima ([[o histórico selado estava aberto]]).

Limpo de passagem um resquício de maquete: a página priorizava um ativo chamado "Wolverine" na listagem. Com o backend já filtrando por `proprietario_email`, a lista do armador só tem os barcos dele — não há o que escolher.

**Corrigido também:** os documentos que inseri direto no banco ficaram sem `url_arquivo`, e sem ela a foto não renderiza. O endpoint de upload preenche esse campo; a inserção manual não. É exatamente a classe de defeito que preencher pelo banco não pega — ressalva já registrada em [[Marlin Sea Focus]].

---

## 21. Ficha criada sem aba é trabalho invisível
**Data:** 21/08/2026

A ficha rica de Sinistros foi escrita, registrada em `SERVICOS` e testada — e a **aba nunca foi acrescentada** à lista de categorias do `AtivoHub`. Nem a marina nem o armador conseguiam chegar nela, e os dois registros de sinistro do ativo de demonstração ficaram invisíveis no painel.

Nada quebrava. Nenhum teste falhava. A funcionalidade simplesmente **não existia para quem usa**.

É o defeito mais silencioso que este código permite: o backend aceita, o banco guarda, os testes passam, e a tela não tem a porta.

`test_painel_abas.py` fecha isso — toda ficha registrada em `SERVICOS` precisa ter aba correspondente. Quebrou? Acrescentar a categoria em `categorias()`.

---

## 22. O selo mostrava "Ouro · 0%"
**Data da Decisão:** 21/08/2026

Classificação gravada, percentual zerado — **contradição visível na tela**, e sem nenhuma pista de onde vinha.

O motivo de não dar para investigar era um `except Exception: pass` na persistência do score. Se o `UPDATE` falhasse, ninguém ficava sabendo: o cálculo devolvia o número certo, a tela mostrava outro, e o log ficava mudo.

Agora a falha vai para o log com o score que deveria ter sido gravado. O comportamento não muda — falhar ali continua não derrubando o cálculo, porque quem chamou recebe o valor correto de qualquer forma.

**Selo errado é pior que selo ausente:** ele contradiz o próprio conteúdo do dossiê, e é a primeira coisa que o armador vê ao abrir o portal.

**Padrão a repetir:** `except: pass` é aceitável quando a falha é irrelevante; quando ela produz um resultado *visível e errado*, tem que gritar no log.

---

## 23. Prospecção nunca divide o número com o transacional
**Data:** 22/08/2026

O Protocolo Genesis virou o **programa de indicação**: marina indica marina, e os dossiês da indicada são receita da indicante por 12 meses. Para abordar a indicada, o formulário passou a pedir o **WhatsApp** dela (coluna nova em `marina_leads`).

O pedido inicial era disparar por esse canal. O canal já existia — e é o mesmo que entrega **código de acesso do armador** (`owner.py`) e a **régua de cobrança** (`cobranca_service.py`).

### O Problema
`EVOLUTION_INSTANCE` era um valor único. Plugar prospecção ali colocaria disparo de vendas no mesmo número que o login e a cobrança. WhatsApp bane por denúncia de spam, e ban é **por número**: uma denúncia derrubaria os três fluxos de uma vez. O armador não entra, o inadimplente não é avisado, e nada disso apita.

### A Solução
Instância separada, com número próprio (`Marinas-Indicadas`, +55 12 97813-8934), no mesmo servidor Evolution. `enviar_whatsapp(..., prospeccao=True)` escolhe a instância; quem chama sem o parâmetro continua exatamente como antes — os três chamadores existentes não mudaram uma linha.

**Sem `EVOLUTION_INSTANCE_PROSPECCAO` configurada, a prospecção não envia — e de propósito não cai na transacional.** Um fallback "esperto" ali seria a forma mais fácil de, num dia de disparo, derrubar login e cobrança sem ninguém perceber.

Token **de instância**, não a chave global: um token de instância só alcança a própria instância, então se ele vazar a transacional continua fora de alcance.

### Sem IA na saída, de propósito
A mensagem é **template fixo** (`prospeccao_service.py`). Ela carrega condição comercial — "12 meses", "100%" — e texto gerado a cada envio seria risco de prometer o que não foi combinado, além de sinal de bot para o WhatsApp, que classifica por padrão. Os números vivem em **constantes do módulo**: não vêm de banco, não vêm de modelo, não são digitados na hora.

Quando houver IA aqui, ela entra na **resposta**, não na saída. E chave de API separada **não reduz alucinação** — é o mesmo modelo e os mesmos pesos; serve para separar custo e limitar vazamento.

### Ritmo é preservação de ativo
Lote de 20, 45 segundos entre envios. Número novo em rajada é o padrão que o WhatsApp bane. O número é o ativo mais frágil da operação.

**Princípio a repetir:** canal que carrega autenticação ou dinheiro não divide identidade com canal de marketing. O que é barato de separar antes é caríssimo de separar depois de banido.

