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
Instância separada, com número próprio (`Marinas-Indicadas`, +55 12 99758-8791), no mesmo servidor Evolution. `enviar_whatsapp(..., prospeccao=True)` escolhe a instância; quem chama sem o parâmetro continua exatamente como antes — os três chamadores existentes não mudaram uma linha.

**Sem `EVOLUTION_INSTANCE_PROSPECCAO` configurada, a prospecção não envia — e de propósito não cai na transacional.** Um fallback "esperto" ali seria a forma mais fácil de, num dia de disparo, derrubar login e cobrança sem ninguém perceber.

Token **de instância**, não a chave global: um token de instância só alcança a própria instância, então se ele vazar a transacional continua fora de alcance.

### Sem IA na saída, de propósito
A mensagem é **template fixo** (`prospeccao_service.py`). Ela carrega condição comercial — "12 meses", "100%" — e texto gerado a cada envio seria risco de prometer o que não foi combinado, além de sinal de bot para o WhatsApp, que classifica por padrão. Os números vivem em **constantes do módulo**: não vêm de banco, não vêm de modelo, não são digitados na hora.

Quando houver IA aqui, ela entra na **resposta**, não na saída. E chave de API separada **não reduz alucinação** — é o mesmo modelo e os mesmos pesos; serve para separar custo e limitar vazamento.

### Ritmo é preservação de ativo
Lote de 20, 45 segundos entre envios. Número novo em rajada é o padrão que o WhatsApp bane. O número é o ativo mais frágil da operação.

**Princípio a repetir:** canal que carrega autenticação ou dinheiro não divide identidade com canal de marketing. O que é barato de separar antes é caríssimo de separar depois de banido.

---

## 24. O mesmo formulário em dois lugares, e por que o código não pode ser o mesmo
**Data:** 22/08/2026

Os botões "Indicar para outra marina" da página de **Lançamento** mandavam o visitante para a Oficial. Era largar uma marina aquecida no meio do funil — e numa página onde o preço é outro. Agora o formulário de indicação abre ali mesmo.

### Idêntico para quem vê, diferente por baixo
A Oficial é **React com CSS Modules**; o Lançamento é **um `index.html` com CSS e JS inline**. Não há como reaproveitar o componente. O que foi replicado foi o *resultado*: as regras de `MarinaParceira.module.css` reescritas à mão, escopadas em `#indicaModal` para não encostar no modal de cadastro, que segue com o estilo de caixa.

Isso é dívida assumida com olhos abertos: **mudar o formulário agora exige mudar nos dois lugares.** O custo de unificar (transformar a LP estática em build React) é maior que o de manter dois, enquanto forem dois.

### CORS não existe porque o nginx o evita
O `nginx.conf` do Lançamento expõe a API da Oficial **por caminho exato** — o navegador vê `/api/...` como same-origin e CORS nunca entra na conversa. Quem faz a chamada cross-origin é o nginx, e servidor não tem CORS.

A consequência prática, que custa caro se esquecida: **endpoint novo exige bloco novo no `nginx.conf`.** Sem ele, o formulário envia, o navegador barra, e a marina não vê erro nenhum — o pior desfecho possível, porque ela acha que indicou.

### O `<select>` que denunciou a diferença
O formulário da Oficial tem um `select` de porte da frota. A LP nunca tivera um — só `input` — então não havia CSS para ele, e o navegador desenhou a caixa branca padrão no meio de um formulário escuro. Só apareceu **no screenshot**; nenhum teste pegaria isso.

**Padrão a repetir:** ao replicar um componente entre stacks, conferir os elementos que a stack de destino nunca usou. O CSS existente cobre o que já existia, não o que chegou.

### Falha de rede não pode virar sucesso
O envio mostra erro e reabilita o botão. Não esconde o formulário, não mostra "Indicação recebida". Marina que acha que indicou e não indicou é pior que marina que viu um erro — mesma família do selo que mentia (§22) e do score que falhava em silêncio.

---

## 25. A indicação era o único fluxo que chegava calado
**Data:** 22/08/2026

Cinco indicações reais entraram em `marina_leads` e ninguém soube. O endpoint gravava e respondia — só isso. Dossiê pedido, cadastro de marina, régua de cobrança e agenda **todos** avisam o fundador; a indicação era a única exceção, e ninguém tinha reparado porque a ausência de aviso é indistinguível de "não chegou indicação nenhuma".

Agora `POST /leads/marina` chama `notificar_fundador` com quem indicou, quem foi indicado, contato, frota e origem. Best-effort: a indicação já está gravada quando o aviso sai, então falhar em avisar não pode derrubar nada.

### O alerta saía do número que ele deveria vigiar
`ALERTA_WHATSAPP` era `5512978138934` — exatamente o número conectado à instância `Programa-Atlas`. Ou seja, o aviso era **mensagem para si mesmo**: caía no chat "mensagem para você mesmo", fácil de não ver, e saía pelo mesmo canal que deveria monitorar.

Isso não é teórico. Foi o que aconteceu neste mesmo dia: a chave da Evolution foi rotacionada, o WhatsApp parou, e o aviso de que o WhatsApp parou iria... por WhatsApp. O canal caiu em silêncio e só apareceu quando o código de login não chegou.

Passou para `5512991187251`, um número **de fora** do sistema. No dia em que a `Programa-Atlas` cair, a `Marinas-Indicadas` ainda consegue contar.

**Princípio:** canal de alerta não pode ser o mesmo que ele monitora, nem sair do próprio número que recebe.

### Por que NÃO existe scheduler de 24/48h ainda
Foi proposto e recusado por ordem, não por mérito. O scheduler precisaria saber se a marina **já foi contatada** — e isso o sistema não observa: contato manual (ligação, mensagem na mão) não registra nada. Um alarme que cobra por lead já resolvido é um alarme que se aprende a ignorar, e aí ele falha justamente quando importa.

Esse estado vira automático de graça quando o disparo funcionar (`whatsapp_status = 'enviado'`). Construir o scheduler antes disso é construir um botão "já cuidei" só para alimentar o próprio alarme — sintoma, não causa. Ver [[23]].

### Duas correções que só apareceram no uso real
- **DDI**: o insert usava um `_so_digitos` escrito no mesmo dia, que só removia caracteres. `(48) 99123-4567` virava `48991234567`, sem o `55` — fora do contrato que o comentário da própria coluna declarava. `normalizar_telefone` já existia e era a função certa desde o início.
- **Origem**: o mesmo formulário roda na Oficial e no Lançamento, e as indicações chegavam idênticas. Agora cada front declara a origem e o backend valida contra lista fechada — valor fora dela vira `desconhecida`, porque o campo vem do navegador e um POST direto manda o que quiser.

**Padrão a repetir:** ao criar um fluxo novo, conferir se ele avisa alguém. Gravar no banco não é entregar — é só guardar.

---

## 26. O dossiê falava das fotos e não as mostrava
**Data:** 23/08/2026

O fundador mandou o PDF real (Marlin Sea, 19 páginas) e pediu "uma olhadinha". A análise achou defeitos que só aparecem lendo o documento como um **comprador** leria — não como quem escreveu o código.

### 20 imagens, 19 eram a mesma logo
A seção "Registro Fotográfico Certificado" dizia *"8 imagens seladas e geolocalizadas"* e entregava uma **tabela de contagem**. Nenhuma foto. Num produto cujo principal argumento é "até 430 imagens datadas e geolocalizadas", falar delas sem mostrá-las esvazia o argumento inteiro.

Agora entram todas, com data, marca de geo e **prefixo do hash** — é o que separa "uma foto" de "esta foto, selada nesta data, conferível contra o painel".

### O desempenho era o risco, não o layout
Primeira versão: **102 s para 8 fotos**. Duas causas, as duas invisíveis sem medir:

1. **O PDF é montado duas vezes** (a 1ª mede em que página cai cada seção) e cada foto baixava duas vezes. Com 430 fotos seriam **860 downloads**.
2. **Cada download abria conexão TLS nova.** Um arquivo de 11 KB levava os mesmos 4,7 s que um de 803 KB — o custo era o aperto de mão, não o tamanho.

Cache entre as passadas + cliente httpx compartilhado: **102 s → 11 s**. Sem isso, a capacidade de 430 fotos que o site anuncia seria impraticável.

### "GOLD · 100%" num barco com a proa furada
O Índice de Segurança olhava 8 categorias e **casco, operação e sinistros não estavam entre elas**. Os dois registros em atenção do Marlin Sea — *"impacto com objeto submerso — proa bombordo"* e *"saída ao mar — retorno com avaria"* — ficavam fora da conta. Daí 100%.

Agora são 12 categorias, e **sinistro/casco em atenção valem 0, não 50**: casco furado não é meio-termo. O índice caiu para **86%**, que é a verdade.

Saíram `documentacao` e `dossie` da lista: não são categorias de REGISTRO (documento vive em outra tabela), então davam "NÃO AVALIADO" eterno ao lado de "29 documentos selados", parecendo defeito do sistema.

### R$ 2,5 mi que eram R$ 89,3 mil
A capa somava a **apólice de R$ 2,4 mi** no mesmo campo `valor` de uma revisão de R$ 9.800, e anunciava *"investido no ativo"*. O gasto real era **R$ 89,3 mil — inflado 27 vezes**. Seguro é cobertura, não investimento: viraram dois tiles, mais um terceiro com o custo médio mensal (R$ 4,7 mil), que é a primeira conta que um comprador faz.

### "Classificação GOLD" não significa o que parece
A fórmula é 50% abrangência de categorias + 25% volume de manutenção + 15% documentos. **Zero sobre a condição do barco** — um casco furado pontua igual a um intacto com o mesmo tanto de registro. Virou **"Índice de Custódia: GOLD"**, que é o que ele mede, e para de contradizer a própria FAQ do site ("o Atlas não inspeciona").

### O QR não lia em metade dos leitores
Polaridade invertida — dourado claro sobre navy escuro, quando a ISO/IEC 18004 exige módulos escuros sobre fundo claro. Testado com zxing **sobre o PDF real**: leitor sem detecção de inversão (ZXing/ZBar padrão, Android de fabricante, app de vistoria) **não lia**; iPhone e Google Lens liam. Invertido, os dois leem.

Isso vai para **papel impresso**: QR ilegível em dossiê já emitido não tem correção retroativa.

### O card pedia o que não fornecia
Mandava *"informe o protocolo e o código"* e mostrava **só o código**. A API exige **três** coisas — protocolo, código e data de emissão — e a data não era sequer mencionada. Ninguém conseguiria verificar seguindo a instrução impressa.

**Padrão a repetir:** ler o próprio produto como o cliente lê. Todos esses defeitos passavam em teste, não quebravam nada, e estavam errados.

---

## 27. Quase nada faltava — só não chegava ao documento
**Data:** 23/08/2026

Perguntado "temos algo a mais para acrescentar?", o método que rendeu foi **procurar o que o sistema já sabe e não diz** — em vez de inventar seções.

O que se achou, tudo já selado no banco:

- **21 documentos PDF** — notas fiscais, laudos, apólices — que **nunca apareciam**. A seção "Documentação Legal e Fiscal" listava só itens de checklist em texto. A capa afirmava um valor investido sem exibir um comprovante sequer. Virou a seção **Comprovação Fiscal e Documental**, com hash por linha.
- **`natureza_manutencao`** — campo OBRIGATÓRIO na ficha, nunca usado. O Marlin Sea tem **100% preventiva**. É o indicador que seguradora usa para precificar risco e comprador usa para estimar gasto. Virou **Perfil de Manutenção**.
- **Cinco datas de validade** no JSONB dos registros. O extintor **vence em 38 dias** e ninguém sabia. Virou **Vencimentos & Conformidade**, com faixa de 90 dias — o prazo em que ainda dá para renovar sem correria.
- **Dez colunas de especificação** (boca, calado, casco, motorização) que existiam no banco, não eram declaradas no schema, não eram coletadas no painel e não chegavam ao dossiê. `create_ativo` fazia `getattr("largura")` num modelo sem o campo: **código morto que parecia vivo**.
- **Identidade do proprietário** não existia como campo. As duas colunas que havia são chave de ACESSO ao Portal, não identidade — por isso o dossiê de um ativo de alto valor não dizia de quem era o barco.

### O painel dizia "Sem registro" com 21 PDFs guardados
Os cards de Documentação e Fotos contavam só a tabela `registros`, e esses dois vivem em `documentos`. A marina subia o arquivo, via o painel dizer que não havia nada, e não tinha como saber se o upload funcionou.

### Tipo declarado ≠ tipo do banco
`potencia_motor` e `capacidade_tanque` são **integer**, e foram declarados como texto. O Postgres recusava com *"invalid input syntax for type integer"* — erro que só apareceria **na hora de a marina salvar**, com ela olhando a tela. Conferir contra `information_schema` antes de declarar deixou de ser opcional.

**Princípio:** antes de projetar campo novo, listar o que a tabela já guarda e o produto não usa. Neste dossiê, a resposta foi "quase tudo".

---

## 28. A instrução impressa mandava para uma porta que não existia
**Data:** 23/08/2026

O dossiê impresso diz, em letras claras: *"Sem câmera: acesse o endereço e informe protocolo, código e data de emissão"*.

Esse endereço **não existia**. `App.tsx` declarava só `/verificar/:protocolo`, e a página de resultado, faltando qualquer parâmetro, respondia:

> *"Link incompleto. Use o QR Code impresso no dossiê ou informe o protocolo e o código de verificação."*

**Pedindo para "informar" sem oferecer um único campo para informar.**

### Por que isso é pior do que parece
Quem lê o dossiê é comprador, corretor e perito de seguradora — com o papel na mão e um leitor de QR que pode simplesmente não abrir. A pessoa segue a instrução, digita o endereço, e encontra uma tela que repete o pedido sem atender. Nesse momento ela conclui que a verificação é decorativa — e a verificação **é o produto**.

Mesma família do "responda SAIR" (§25): prometer um caminho e não construí-lo.

### A tela não valida nada
Ela monta a MESMA URL que o QR carrega e entrega para a página de resultado, que já existia e funcionava. **Uma porta de entrada, não uma segunda implementação** — duas rotas verificando por caminhos diferentes divergiriam no primeiro ajuste.

E normaliza o que a pessoa digita: protocolo para maiúscula, código para minúscula, data de barra para hífen. O PDF imprime `22/08/2026` e o QR usa `22-08-2026`; transformar um detalhe de formato em "documento não localizado" seria a mensagem mais desanimadora possível para quem está justamente conferindo autenticidade.

**Padrão a repetir:** toda instrução impressa num artefato que não se pode corrigir depois precisa ser testada como o leitor a executaria — não como quem a escreveu imagina.

---

## 29. O QR provava a origem, não a integridade
**Data:** 23/08/2026

Perguntado "para que serve realmente o QR code?", a resposta honesta expôs uma lacuna que ninguém tinha visto.

A assinatura é `HMAC-SHA256(protocolo + data de emissão)`. Ela prova que **o documento nasceu no Yachts Atlas** — sem o segredo não se fabrica um código válido. Mas ela **não cobre o conteúdo do PDF**.

### O ataque que isso permitia
Quem recebesse um dossiê legítimo — o próprio dono querendo vender mais caro, um corretor, qualquer um a quem foi entregue — podia abrir o PDF e mudar "Investido: R$ 89,3 mil" para "R$ 340 mil", apagar a seção de sinistros, subir o índice de segurança. **O QR continuaria validando**, porque protocolo e data não mudaram.

Fabricar do zero era impossível (exige o segredo). Adulterar um legítimo, não.

### O que fecha: a plataforma lembrar o que emitiu
`dossie_saidas` registrava **para quem** o dossiê foi, nunca **o que** foi. Sem o original, não havia com que comparar.

Entra `dossie_emitidos`: o **SHA-256 dos bytes do PDF entregue**, gravado na emissão. Quem tem o documento em mãos calcula o hash do próprio arquivo e compara com o que a verificação informa. Bateu, é o original; não bateu, foi mexido depois. Testado: **um único byte trocado muda o hash inteiro**.

A plataforma não guarda o arquivo — guarda a impressão digital dele. Barato de armazenar, impossível de falsificar.

### Imutabilidade no BANCO, não na aplicação
A tabela tem trigger que recusa `UPDATE` e `DELETE`, como `registros`. Testado: tentar alterar o hash levanta exceção; tentar apagar, também. **Nem a `service_role` consegue** — para remover a linha de teste foi preciso desligar o gatilho por SQL.

É o mesmo princípio que já regia os registros selados: *capacidade que não existe não pode ser abusada*. De nada adianta prometer imutabilidade e deixar a aplicação com poder de reescrever.

### Lista, não valor único
A verificação devolve **todos** os hashes do protocolo. O mesmo ativo pode ter mais de uma via legítima (reemissão depois de novo registro selado), e mostrar só a última faria o portador de uma via anterior concluir, erradamente, que o documento dele foi adulterado.

### O aviso no PDF é parte da defesa
O dossiê traz, no quadro de verificação, uma linha em corpo pequeno: *"A verificação também informa a impressão digital (SHA-256) deste arquivo. Documento alterado após a emissão não confere com a impressão registrada."*

Não é informação de serviço — é dissuasão. **Ninguém edita um documento sabendo que a cópia pode ser confrontada com a original em dois segundos.** O aviso trabalha antes da fraude, não depois.

Uma linha só, dentro do quadro que já existe: o dossiê é o produto e não pode virar folheto do serviço de verificação.

**Diretriz do fundador, registrada:** *"Temos que ser imutáveis. Essa é a base de trabalho do Programa Atlas — onde você achar que pode ser alterado ou fraudado, me fala e resolvemos juntos."* Vale como instrução permanente: apontar toda superfície adulterável que aparecer, mesmo sem ser perguntado.

---

## 30. A contra-prova: o arquivo não sai do computador de quem verifica
**Data:** 23/08/2026

Com a impressão digital de cada emissão registrada (§29), faltava a porta: um lugar onde **qualquer pessoa** confere um PDF sem precisar de conta, de conhecimento técnico ou de permissão.

`/conferir` faz isso. E a decisão de projeto que importa: **o navegador calcula o SHA-256 localmente (Web Crypto) e envia só os 64 caracteres.** O documento nunca é transmitido.

Isso resolve o problema de confiança na ordem certa: **ninguém deveria precisar entregar um documento sigiloso a um terceiro só para descobrir se ele é legítimo.** De quebra é instantâneo e não custa banda — um dossiê com 430 fotos passa de 20 MB, e fazer upload disso a cada conferência seria caro para os dois lados.

A garantia de privacidade aparece na tela **antes** da área de upload, de propósito: é a primeira dúvida de quem vai jogar um documento sigiloso num site.

### "Não corresponde" não é erro HTTP
O endpoint devolve **200 com `corresponde: false`**, não 404. "Não corresponde" é uma resposta legítima e é **metade do serviço** — devolver erro faria o front tratar como falha e mostrar "algo deu errado" onde deveria mostrar um veredito.

### E não corresponder não é acusar
A tela diz, quando não bate: *"Isso não significa necessariamente fraude: o arquivo pode ter sido reimpresso, convertido ou salvo por outro programa, o que altera os bytes sem mudar o conteúdo visível."*

É verdade e importa. Um PDF que passou por impressora virtual tem outros bytes e o mesmo conteúdo. Sem essa ressalva, a ferramenta acusaria gente inocente — e uma ferramenta que gera acusação falsa deixa de ser usada.

### Por que gratuita
O efeito antifraude vem da **existência** da conferência, não do preço: ninguém adultera um documento que qualquer um confere em dois segundos. Cobrar aqui mataria exatamente o que faz funcionar.

O pago é outro produto — o **laudo assinado**, para quem precisa *provar a terceiro* (seguradora em análise de sinistro, advogado em disputa). Referência de US$ 40, registrada no PRD. Uma não canibaliza a outra: quem confere de graça queria **saber**; quem paga precisa **provar**, e print de tela não vale em processo.

### O preço não vai no PDF
O dossiê é imutável depois de emitido — e **tudo que muda com o tempo não pode ser impresso**. Um dossiê com "US$ 40" continuaria dizendo isso depois do reajuste, sem correção possível. O preço vive na página de verificação, que é dinâmica.

No PDF fica só uma linha, em corpo pequeno, que **não vende nada**: avisa que a impressão digital pode ser conferida. É dissuasão, não propaganda — trabalha antes da fraude, não depois.

---

## 31. O segredo do QR saiu do repositório e foi para produção
**Data:** 23/08/2026

O `VERIFICACAO_SECRET` era o bloqueador mais antigo do PRD e o mais grave: faltando a variável, o código caía no literal `yachts-atlas-verificacao-dev` — **que está publicado no repositório público**. Qualquer pessoa calculava a assinatura e fabricava um dossiê falso com QR que validava.

Trocado em 23/08/2026, com uma janela que não se repete: `dossie_saidas` estava **zerada**. Nenhum dossiê real havia sido emitido, então a troca não invalidou o QR de ninguém. **Depois da primeira emissão real essa janela fecha para sempre** — rotacionar o segredo mata todo QR já impresso, e papel não se atualiza.

Confirmado contra produção, não suposto:

| Assinatura gerada com | Produção responde |
|---|---|
| literal de desenvolvimento (o do repo) | **404 — recusado** |
| segredo novo | **200 — aceito** |

**Se um dia for preciso rotacionar, versione em vez de trocar**: incluir a versão do segredo na URL do QR e manter as anteriores válidas para os documentos já emitidos. Trocar direto é a única operação irreversível desta parte do sistema.

**Padrão a repetir:** segredo com fallback para literal é bomba-relógio — o app sobe, funciona, e ninguém percebe que a proteção não existe. O aviso no log não basta: ninguém lê log. Onde o fallback for perigoso, o certo é **recusar subir** (foi o que se fez com a instância de prospecção, §23).


---

## 32. O dia que se perdeu porque o sistema não sabia dizer o que faltava
**Data:** 23/08/2026

Indicações entrando, e-mail chegando, WhatsApp mudo. Um dia inteiro de suposição — culpei o hífen, culpei o deploy, culpei a variável, li o log errado (era o do Evolution, não o do Atlas). Nada disso era diagnóstico: era chute com aparência de análise.

Quando finalmente **perguntei em vez de deduzir**, a resposta veio em dois segundos:

```
Programa-Atlas    -> HTTP 200  state: open
Marinas-Indicadas -> HTTP 200  state: open
```

As duas instâncias de pé, os dois tokens válidos. O Evolution nunca foi o problema.

**A causa real do custo não foi a variável perdida — foi o sistema não conseguir dizer que ela faltava.** `notificar_fundador` pula canal mal configurado em silêncio, de propósito: falhar em avisar não pode derrubar o pagamento que gerou o aviso. Mas em produção isso deixa *"a variável sumiu no deploy"* **idêntico** a *"não havia o que avisar"*.

Pior: o logger raiz estava em WARNING, então o `logger.info("WhatsApp enviado para ...")` do envio **bem-sucedido** também não aparecia. Sucesso e "nem tentei" tinham a mesma aparência no log — **nenhuma linha**. Não havia como distinguir os dois, e eu passei horas tentando.

O que mudou (`app/services/diagnostico_avisos.py`):

1. **Conferência no boot** — a cada deploy o app confere variáveis + estado real da instância e escreve no log. Faltou algo, sai em **ERROR** com o nome da variável. Nunca levanta: diagnóstico que derruba o boot é pior que o defeito.
2. **`/api/v1/admin/diagnostico-avisos`** passou a chamar a mesma função. Duas cópias da mesma checagem divergem, e a errada é sempre a que ninguém olha.
3. **Fim do pulo mudo** — `ALERTA_WHATSAPP` vazio agora registra WARNING com o título do aviso perdido.
4. **`logging.basicConfig(level=INFO)`** em `main.py`.

**Detalhe de configuração que ficou:** `ALERTA_WHATSAPP` estava **fora do bloco do WhatsApp** no EasyPanel, solta no meio do arquivo. Todas as irmãs juntas, ela sozinha — e foi ela que se perdeu numa edição. Variável de um mesmo assunto mora junta.

**Token de instância da Evolution:** 32 caracteres + 3 hífens = **35 no total**. Um caractere a mais (o `+` que veio colado junto numa cópia) vira 401 mudo. Conferir tamanho é mais rápido que conferir conteúdo.

**Padrão a repetir:** quando eu me pegar deduzindo pela terceira vez, o defeito não é mais o bug — é a falta de observabilidade. Parar de investigar e **construir o instrumento** sai mais barato que a quarta hipótese. E o instrumento precisa rodar **sozinho**, no caminho que já se percorre (o log do deploy): ferramenta que só responde quando alguém suspeita não serve para o caso em que ninguém suspeitou.

---

## 33. A trilha de auditoria tinha zero linhas desde sempre
**Data:** 23/08/2026

Apareceu por acaso, no log que a gente estava lendo por outro motivo:

```
Error creating audit log: new row violates row-level security policy
for table "audit_logs"  (42501)
```

Repetido a cada abertura de documento ou de ativo. `select count(*) from audit_logs` → **0**. Não quebrou naquele dia: **nunca funcionou**.

Três defeitos empilhados, e cada um sozinho já bastava:

1. **Cliente errado.** `audit_service` conectava com a chave anônima. A tabela tem RLS ligado e só políticas de SELECT — nenhuma de INSERT. Toda gravação recusada.
2. **Tipo errado.** `user_id` é `uuid`; 11 pontos do código mandam `system`, `anonymous`, `maintenance-admin`, `unknown`. Mesmo com o cliente certo, morreriam em `invalid input syntax for type uuid`.
3. **Sem imutabilidade.** `registros`, `documentos` e `dossie_emitidos` têm gatilho append-only. `audit_logs` não tinha.

O terceiro era o mais perigoso **na hora de consertar**: ligar a gravação sem proteger a tabela criaria algo pior que o vazio — um registro que **parece prova** e pode ser reescrito por quem tem a chave de serviço. Por isso o gatilho veio primeiro, e só depois a gravação.

**A falta de política de INSERT não é o defeito e ficou como está.** Se o navegador pudesse escrever ali, qualquer um forjaria "fulano acessou o dossiê tal". Quem escreve é o backend, com a chave de serviço — que passa por cima do RLS mas **não** passa por cima de gatilho. Essa distinção é o desenho, não um acaso.

O ator textual passou a viver em `metadata.ator`, com `user_id` nulo: quem fez a ação continua registrado, só não finge ser usuário cadastrado.

Provado contra produção, não suposto: UPDATE e DELETE recusados pelo gatilho, e a primeira linha da trilha é a própria ativação dela.

**Padrão a repetir (é o mesmo do §32, no mesmo dia):** `except` que engole erro para não derrubar o fluxo principal é decisão certa e cria um ponto cego por construção. Onde houver um desses, alguma coisa precisa **perguntar em voz alta se aquilo está funcionando** — senão "nunca funcionou" fica indistinguível de "não houve o que registrar". Dois sistemas caíram nisso no mesmo dia por motivos diferentes: o aviso ao fundador e a auditoria.

**Aberto, não tocado:** `POST /auth/maintenance/login` respondeu **503** em produção — falta `MAINTENANCE_USERNAME`/`PASSWORD` ou `MAINTENANCE_JWT_SECRET`. É acesso do fundador; avisar, nunca mexer sem ordem dele.

---

## 34. O bloqueador nº 1 morreu — e quase morreu pela metade
**Data:** 23/08/2026 (aberto desde 16/07/2026 — 38 dias)

O `SUPABASE_JWT_SECRET` estava publicado no commit `15ac4be` e continuava sendo o valor em uso. Quem tivesse o valor forjava `{"sub":"maintenance-admin"}` e virava `platform_admin` sem senha.

Fechado. A chave legada HS256 foi **revogada** no dashboard:

```
REVOGADO · 267D9897-1B04-42D4-B7C3-1C2972049C57
Legado HS256 (Segredo Compartilhado) · ultima rotacao: 4 meses antes
```

**A lição do dia está no "quase".** São três botões na tela do Supabase e é fácil parar no segundo:

| Botão | O que faz de verdade |
|---|---|
| Migrate JWT secret | importa o legado para o sistema novo. Não muda nada. |
| Rotate keys | passa a **assinar** com a chave nova. O segredo vazado **continua sendo aceito**. |
| **Revoke key** | **é este que mata.** Sem ele, girar foi teatro. |

Parar no "girar" dá a sensação exata de resolvido — a tela mostra chave nova, tudo verde — enquanto o buraco segue aberto. Foi o ponto que mais precisou de atenção no dia.

**O que tornou o revoke seguro, verificado antes e não suposto:**

1. `SUPABASE_JWT_SECRET` não era usado por **nenhum** código (só definição em `config.py` e comentários).
2. `SUPABASE_KEY` e `SUPABASE_SERVICE_KEY` são do formato novo (`sb_publishable_` / `sb_secret_`), **independentes** da chave de assinatura. Na conta antiga, `anon` e `service_role` *eram* JWTs assinados pelo segredo — ali, revogar derrubaria o backend inteiro.
3. O backend não confere assinatura localmente: pergunta ao Supabase via `auth.get_user(token)` ([security.py](backend/app/core/security.py)).
4. O frontend não tem sequer biblioteca de JWT no `package.json`.
5. A Edge Function `verify-owner-secret` (`verify_jwt: true`) é **órfã** — o portal do armador usa código de uso único por e-mail/WhatsApp, ninguém a chama.

**Ordem que se impôs no dia:** consertar primeiro a porta que não abria (login de manutenção em 503 por falta de `MAINTENANCE_USERNAME`/`PASSWORD` em produção), só depois trocar as fechaduras. Não faz sentido mexer em chave de segurança sem ter acesso administrativo funcionando.

**Achado de brinde:** o `.gitignore` tinha `.env`, `.env.local`, `.env.*.local` e `*.env` — e **nenhuma** dessas pega `.env.backup-antes-da-troca`. Um backup meu ficou uma hora no diretório com a senha antiga dentro, a um `git add -A` de repetir o vazamento de julho. Corrigido com `.env.*` + `!.env.example`, **testado com nomes reais** — a primeira verificação que escrevi deu falso positivo porque procurou o texto `.env.*` e o encontrou dentro de `.env.*.local`.

**Padrão a repetir:** ler a regra não é testar a regra. Errei nisso duas vezes no mesmo dia (aqui e no `normalizar_telefone`, que eu disse ter consertado um caso que ele não cobre). Quando a conclusão importa, executar vale mais que inspecionar.

---

## 35. O cofre que era vitrine
**Data:** 23/08/2026

O balde `media` do Supabase Storage estava **público**. 51 arquivos, 10 MB, com documento de cliente dentro — nota fiscal, apólice, laudo. Qualquer um com o endereço baixava sem autenticar nenhuma.

Numa plataforma vendida como **custódia**, isso não é um bug de configuração: é a contradição da proposta.

**O que tornou a correção mais que "virar a chave":** as URLs públicas estavam **gravadas** em `documentos.url_arquivo` (36 de 68 registros). Fechar o balde sem mexer no código quebraria o painel e o dossiê no mesmo instante — desfazendo o conserto das fotos de 22/08.

O que se conferiu antes de escrever qualquer linha:

- **`storage_path` existe nos 68 documentos.** É a fonte confiável; a URL é derivada. Deu para assinar na leitura sem depender do que estava gravado.
- **As 29 evidências dos registros selados não guardam URL nenhuma.** Era o maior receio: registro selado é imutável, e URL pública dentro dele seria prova visual quebrada sem possibilidade de correção. Não havia.
- **O frontend não monta URL.** Lê `url_arquivo` em quatro telas e pronto. Mantendo o nome do campo, zero mudança no front.

**Assinar na leitura, nunca regravar o banco.** Link assinado vence; gravá-lo seria guardar algo que expira num lugar que não expira — o defeito voltaria em oito horas, e ninguém ligaria os pontos.

**Ordem obrigatória: código primeiro, balde depois.** Invertido, o sistema quebra no instante da mudança.

**Fechado no mesmo dia**, e a prova vale mais que a descrição:

```
ANTES   curl na URL publica, sem login  ->  HTTP 200, 11.689 bytes baixados
DEPOIS  mesma URL, cache furado         ->  HTTP 400 {"error":"Bucket not found"}
DOSSIE  8 fotos, 8 assinadas, 8 baixam  ->  nenhuma regressao
```

**Resíduo:** o Smart CDN da Cloudflare seguiu servindo cópias em cache (`CF-Cache-Status: HIT`) dos arquivos já buscados publicamente antes. Isso quase me fez concluir que o fechamento falhou — a URL crua respondia 200 depois do `public=false`. O que separou cache de falha real foi acrescentar um parâmetro qualquer à URL: cache miss, vai à origem, 400. **Sem esse teste eu teria revertido uma mudança que estava certa.**

**Padrão a repetir:** antes de fechar uma porta que está aberta há tempo, mapear **quem já está passando por ela**. O trabalho do dia foi 80% mapeamento e 20% código — e o mapeamento é que evitou quebrar o dossiê pela segunda vez na mesma semana.

---

## 36. As molduras vazias eram um andaime que ficou de pé
**Data:** 23/08/2026

O Marcos apontou quatro caixas azuis vazias na seção fotográfica do dossiê, cada uma com selo "SELADA SHA-256" em cima, o nome da categoria embaixo e **nada no meio**:

```python
moldura = Table([[selo], [""], [Paragraph(label)]],
                rowHeights=[5*mm, 24*mm, 7*mm])
                            #     ↑ 24 mm de nada
```

Não era bug: era **lugar reservado**. Foram desenhadas quando o PDF ainda não mostrava imagem nenhuma, para o dossiê não ter um buraco onde as fotos deveriam estar. Em 22/08 as fotos passaram a sair de verdade e as molduras deveriam ter saído junto — ficaram, e viraram um terço de página de caixa vazia repetindo o que a tabela de contagem, no fim da mesma seção, já dizia melhor.

Removidas (43 linhas). Ao tirá-las, a tabela sobrou **sozinha numa página inteira** — defeito novo criado pela correção. Movida para antes da galeria: resumo primeiro, imagens depois, que é a ordem certa de qualquer jeito.

**Padrão a repetir:** quando uma capacidade nova entra, procurar o andaime que existia para disfarçar a ausência dela. Andaime esquecido não parece andaime — parece defeito.

**Resolvido na mesma conversa:** o fundador aprovou criar a categoria — `Segurança & Salvatagem`, mínimo 30, capacidade de **430 → 460**. Sobre manter 430 nas páginas públicas: *"a mais não tem problema, menos é ruim"*.

A causa raiz não era a categoria faltando; era o número morar em **quatro** lugares (`coberturaFotos.ts`, `Ativos.tsx` com a lista inteira duplicada, `dossie_data.py`, e o `conhecimento_produto.json` da Solara). `Ativos.tsx` passou a importar da config em vez de manter cópia. O quarto lugar **só apareceu porque um teste quebrou** — `test_conhecimento_esta_em_dia_com_o_codigo`. Sem ele, a Solara ensinaria 430 às marinas enquanto o painel oferecia 460, com convicção e sem ninguém perceber. É o melhor teste do repositório e não é sobre código: é sobre o produto não mentir para si mesmo.

**Registro do estado anterior:** existia foto gravada como `galeria_seguranca`, mas `seguranca` **não estava** em `COBERTURA_CATS` (a lista de 9 do painel, cujos mínimos somam exatamente os 430 de `MAX_FOTOS`). O painel joga essa foto em "Outros" via `normalizarCategoria`; o dossiê a mostrava como "Seguranca", sem cedilha. Mapeei o rótulo no `GALERIA_LABELS` para o documento não imprimir errado, **mas painel e dossiê continuam discordando** — e acertar isso mexe no 430, número que aparece nos dois. Decisão do Marcos, não minha.

---

## 37. Três vias, três linhas idênticas
**Data:** 23/08/2026

Na página pública de verificação (destino do QR), as impressões digitais dos dossiês emitidos apareciam assim:

```
EMITIDO EM 23/08/2026    70361d97...
EMITIDO EM 23/08/2026    48241862...
EMITIDO EM 23/08/2026    bc56d782...
```

Três vias legítimas — reemissão é normal, cada nova emissão gera hash novo — mas **nada as distinguia**. Quem estivesse com uma delas na mão sabia apenas que "uma das três deveria bater". Num documento que vai para seguradora e comprador, isso lê como desleixo.

A informação existia o tempo todo: `created_at` guarda 19:48, 10:19 e 09:41. Só o `emitido_em` (que é `DATE`) estava sendo mostrado, cortado em 10 caracteres.

**Cuidado que a correção exigiu:** a hora vem de `created_at`, **nunca** de `emitido_em`. O `emitido_em` é o campo coberto pela assinatura HMAC do QR (`protocolo + data`) — mexer no formato dele quebraria a verificação de todo dossiê já impresso. Aqui é só apresentação.

**Fuso fixo `-03:00` em vez de `ZoneInfo("America/Sao_Paulo")`:** o Brasil não tem horário de verão desde 2019, e o `ZoneInfo` depende do pacote `tzdata`, que existe no contêiner e pode faltar na máquina local. Data de emissão que aparece diferente em dois lugares é o tipo de coisa que faz um perito desconfiar do documento inteiro.

Hora ausente ou corrompida cai na data sozinha, sem quebrar a verificação.

**Segunda armadilha na mesma tela, achada porque o Marcos emitiu uma quarta via:** a lista tem `limit(5)`, e o texto diz *"a sua precisa bater com uma delas"*. Passando de cinco, essa frase vira mentira — o portador de uma via antiga não acha a dele e conclui que o documento é falso. A contra-prova (`/verificar/documento/{hash}`) **nunca teve esse limite**: busca por hash em todas as emissões. O que faltava era a página dizer isso. Agora informa quantas existem ao todo e aponta para a conferência automática.

**Padrão a repetir:** limite de exibição em lista é decisão de UI até o momento em que um texto ao lado faz afirmação sobre o conjunto inteiro. Aí vira afirmação falsa — e num documento de custódia, afirmação falsa é o pior defeito possível.

---

## 38. A ponta solta da cadeia: quem recebeu o dossiê
**Data:** 24/08/2026

`dossie_saidas` registra **quem recebeu o dossiê de um cliente** — nome, e-mail, finalidade, IP, quando. Corretor, comprador, seguradora. É a resposta para *"quem viu o histórico do meu barco?"*, pergunta que um armador ou um advogado faz um dia.

Não tinha proteção nenhuma. Quem tivesse a chave de serviço apagava a linha (o dossiê nunca foi entregue a ninguém) ou trocava o destinatário (passou a ter ido para outra pessoa). Sem deixar rastro. Todo o resto da cadeia era imutável — `registros`, `documentos`, `dossie_emitidos`, `audit_logs` — e essa ponta, a mais cara numa disputa, ficava solta.

Fechada junto com mais quatro, em **dois níveis**, e a distinção é o ponto:

- **append-only** (`dossie_saidas`, `integridade_logs`): o fato não muda. Uma entrega aconteceu; não se desfaz.
- **só DELETE bloqueado** (`payments`, `subscriptions`, `lgpd_solicitacoes`, `dossie_solicitacoes`): têm ciclo de vida legítimo — pendente → atendida. Travar UPDATE quebraria o fluxo.

**Decisão deliberada em `payments`/`subscriptions`:** o código só faz INSERT e SELECT nelas (conferido por grep). Mesmo assim ficou só o DELETE. O webhook do Stripe é território de terceiro, e o Marcos ia rodar um teste de pagamento real na mesma manhã — travar UPDATE ali trocaria uma garantia por um risco de perder a manhã. A garantia que importa (pagamento não pode ser apagado) ficou de pé; a trava de UPDATE espera o ensaio mostrar o que o webhook realmente faz.

**Momento certo:** as cinco estavam com **zero linhas**. Proteção aplicada antes do primeiro dado real existir.

**Gatilho, nunca RLS:** a chave de serviço passa por cima de RLS e **não** passa por cima de gatilho. Capacidade que não existe não pode ser abusada — o mesmo raciocínio de [[imutabilidade-registros]].

**Padrão a repetir:** imutabilidade não é um interruptor, são dois. Antes de travar uma tabela, perguntar se o que ela guarda é *fato consumado* ou *estado em curso*. Travar estado em curso quebra o produto; deixar fato consumado aberto esvazia a promessa.

---

## 39. O limitador que se desligava sozinho
**Data:** 24/08/2026

Fui atacar o item "5 policies de INSERT abertas" do checklist do piloto. **O item estava errado** — as policies estão corretas. O buraco era uma camada acima.

Sete rotas aceitavam POST sem autenticação e sem limite nenhum. Seis eram risco de spam. A sétima era outra coisa:

```
POST /dossie/acesso/{solicitacao_id}    confere a SENHA-MESTRA e devolve o PDF
```

Força bruta ilimitada na senha que libera o dossiê de um cliente para terceiros. Sem barreira e sem rastro.

**E o detalhe que fecha o quadro:** o único limitador do sistema, o do chatbot, começava assim:

```python
redis = get_redis()
if redis is None:
    return True   # sem Redis, não bloqueia
```

Produção **nunca teve `REDIS_URL`** — o boot registra "cache desativado" desde sempre. Então o sistema tinha um limitador, ele aparecia no código, tinha até variável de configuração (`CHATBOT_RATE_LIMIT_PER_MIN`)… e nunca limitou nada.

**Padrão a repetir:** dependência opcional não pode desligar controle de segurança. Cache pode degradar em silêncio; limite de taxa, não. Quando a dependência cai é exatamente quando o sistema está sob estresse — e é o pior momento possível para o portão abrir sozinho. `app/core/limite_taxa.py` faz o contrário: Redis quando houver, memória do processo sempre.

Três detalhes que só aparecem fazendo:

1. **IP vem do `X-Forwarded-For`.** Atrás do nginx, `request.client.host` é sempre o IP interno do contêiner — o limitador trataria o mundo inteiro como um visitante só e bloquearia todos ao primeiro abuso.
2. **Teto de chaves em memória.** Atacante trocando de IP a cada requisição transformaria o limitador em vazamento de memória: trocaria um problema por um pior.
3. **`por_rota` no formulário de senha.** Sem isso, o atacante dilui as tentativas trocando de link de solicitação e o balde por IP nunca enche.

**Barrar não é o mesmo que enxergar.** O limite impede a força bruta; a auditoria (ligada ontem) é o que a torna visível. Senha-mestra incorreta agora vira `UNAUTHORIZED_ACCESS` em `audit_logs`, com IP e solicitação. Sem isso, mil tentativas e nenhuma tentativa têm a mesma aparência depois do fato — que é o mesmo defeito de §32 e §33, numa terceira roupa.

---

## 40. A ambiguidade que nenhum algoritmo resolve
**Data:** 24/08/2026

O `5555978138934` de ontem não tinha conserto no backend, e eu errei ao dizer que tinha. `55978138934` — DDI sem DDD — é **estruturalmente idêntico** a um celular legítimo do DDD 55 (Santa Maria/RS): dois dígitos de DDD + nove começando em 9. As duas leituras são válidas. Não existe regra que escolha certo.

A correção foi de interface: **`+55` virou rótulo fixo ao lado do campo**, fora do input, com máscara `(12) 97813-8934`.

O caso crítico continua produzindo o mesmo número — e isso está certo:

```
digitou 55978138934  →  tela: +55 (55) 97813-8934  →  backend: 5555978138934
```

**O que mudou é que a pessoa vê.** Quem quis dizer DDD 12 lê "(55)" e corrige na hora. Antes, o campo mostrava exatamente o que foi digitado e a corrupção acontecia no servidor, calada.

**Padrão a repetir:** quando um dado é genuinamente ambíguo, não invente regra para desempatar — **devolva a ambiguidade para quem sabe a resposta.** Regra que adivinha erra em silêncio; interface que mostra deixa a pessoa corrigir. Vale para telefone, endereço, data, unidade de medida.

**Furo achado ao aplicar:** nos dois formulários do Lançamento a validação só checava se o campo estava *preenchido*. `(12) 978` está preenchido — passaria no laço de obrigatórios e o envio mandaria string vazia, porque a função de envio recusa incompleto. A indicação chegaria **sem telefone**, e é por ele que a marina indicada é abordada. Preenchido não é o mesmo que completo.

Verificado em navegador real (servidor HTTP, DOM, evento `input`, quatro casos) — o snapshot estático do arquivo local não executa JS e teria dado falsa confiança.

---

## 41. Metade do checklist estava resolvido, e ninguém tinha marcado
**Data:** 24/08/2026

Fui atacar quatro itens abertos do `CHECKLIST-PILOTO-3-MARINAS.md`. Dois **já estavam feitos** e um estava **errado no diagnóstico**:

- *"5 policies de INSERT abertas"* — **errado**. As policies estão corretas (`user_role='admin'` nas de broker/seguradora, `auth.uid()` nas de ativo/documento/registro, e as tabelas de formulário público sem policy de propósito). O buraco real era falta de limite de taxa na API — outra camada (§39).
- *"Automatizar build do frontend antes do deploy"* — **já feito**. O Dockerfile tem estágio `frontend-builder` com `npm run build`, e como esse script começa com `tsc`, erro de tipo derruba o deploy em vez de subir frontend quebrado.
- *"Higiene: duas cópias"* — real, mas inofensivo.

**Padrão a repetir:** checklist envelhece calado. Antes de trabalhar em item antigo, **conferir o estado real** — o custo de verificar é minutos, o de reimplementar algo pronto é uma tarde. E item marcado como aberto pode estar não só resolvido, mas mal diagnosticado desde o começo.

**Sobre verificar o que está publicado:** o bundle em produção embute `sb_publishable_…` (formato novo). Fui olhar o JS servido de verdade, não a variável de ambiente — chave certa no `.env` não prova chave certa no ar.

**Resíduo achado de brinde:** três artefatos de build versionados em `frontend/dist/`, commitados **antes** de `dist/` entrar no `.gitignore`. `.gitignore` não desrastreia o que já está rastreado — regra nova só vale para arquivo novo. Vale lembrar disso toda vez que se acrescenta uma regra de ignore achando que ela limpa o passado.

**A pasta duplicada `C:\YACHTS-ATLAS-OFICIAL`** (com H antes do T, a cópia velha) está 2 meses atrás, sem `.env`, e não tem **nenhum** commit que a viva não tenha. As duas alterações não commitadas eram um `dist/index.html` com diferença só de fim de linha e a exclusão de um `public/sitemap.xml` que ficou obsoleto quando o `prerender.mjs` passou a gerar o sitemap no build, com `lastmod` fresco. Nada a salvar — mas apagar pasta é irreversível e é decisão do Marcos.

---

## 40. Varri metade da classe. De novo.
**Data:** 24/08/2026

Ontem o Marcos me corrigiu por guardar o achado do `dossie_saidas` em vez de falar na hora. Gravei a lição em `varrer-a-classe-inteira-na-hora`. **Hoje repeti o erro noutra forma:** blindei os formulários públicos com limite de taxa e **não olhei o módulo de autenticação**.

Ficaram sem limite:

```
POST /auth/login              forca bruta na senha das marinas
POST /auth/maintenance/login  forca bruta no acesso de admin do fundador
POST /auth/signup             criacao de conta em massa
```

São **mais graves** que as sete que eu protegi. `/auth/login` guarda as contas que têm documento de cliente dentro. `/auth/maintenance/login` é a mesma porta que passamos dois dias recuperando.

Só apareceram porque o Marcos foi mexer no "Confirm email" do Supabase e eu fui conferir qual endpoint o cadastro usa. **Achado por acaso, não por método** — que é exatamente o que a lição de ontem existia para evitar.

**A falha do meu método:** eu varri a classe *"formulários públicos"*, que foi como o problema me chegou. A classe certa era *"rotas que aceitam POST sem autenticação"* — e autenticação é a parte mais sensível dela, não uma categoria à parte. Definir a classe pelo enunciado do problema, e não pelo mecanismo, deixa buraco por construção.

**Padrão a repetir:** ao varrer, listar por **mecanismo** (o que a rota aceita, quem pode chamar), nunca por assunto. `grep "@router.post"` em tudo e olhar quais não têm `Depends` de auth — leva trinta segundos e não depende de eu lembrar das categorias certas.

**De passagem:** `/auth/signup` não é chamado por nada no frontend. Rota pública que cria conta, sem uso. Limitada a 3/hora por ora; o certo é remover depois de confirmar que nenhum chamador externo depende dela.

---

## 41. Apertar a regra no servidor sem contar para a tela
**Data:** 24/08/2026

Endurecemos a política de senha no Supabase (mínimo 10, minúscula, maiúscula, dígito). O Marcos, olhando por cima do meu ombro, disse: *"precisa colocar na página de cadastro essa informação"*.

Ele estava certo, e o problema era maior do que informação faltando: a regra vivia em **três lugares com três valores**.

```
Supabase Auth          6  ->  10 + composicao
RegistroMarina.tsx     6      (Oficial)
index.html             8      (Lancamento)
```

Apertar só o servidor cria o pior dos mundos: a marina digita algo que a tela **aceita**, o servidor **recusa**, e a mensagem que volta é genérica. A pessoa não sabe se errou o e-mail, a senha ou o CNPJ.

No Lançamento isso é pior que suporte — o cadastro acontece **a um passo do pagamento**. Senha recusada ali é venda perdida.

Corrigido nas duas páginas, com os requisitos **à vista, marcando sozinhos** conforme digita. E a regra virou constante única no topo de cada arquivo, com o texto da tela derivando dela.

**Padrão a repetir:** validação existe em camadas (tela, servidor, banco) e elas divergem em silêncio — nada quebra, o sistema só passa a recusar coisas sem explicar. Ao mudar uma, procurar as outras **no mesmo movimento**. É a mesma lição de §40 numa terceira roupa: a classe não era "senha", era "todo lugar que valida senha".

---

## 42. A mensagem existia, o envio existia, ninguém puxava o gatilho
**Data:** 24/08/2026

O Marcos perguntou por que a mensagem de prospecção não chegava na marina indicada. A resposta não era um defeito — era uma ausência.

```
prospeccao_service.py   MENSAGEM_1, montar_mensagem, disparar_lote,
                        blocklist, opt-out por "SAIR" — tudo pronto
        ↓
disparar_lote()         chamado APENAS de dentro do proprio arquivo,
                        no bloco `if __name__ == "__main__"`
        ↓
agenda.py               roda cobranca e aviso ao fundador. Prospeccao, nao.
```

Software completo e desconectado. Ninguém tinha percebido porque não havia erro: um serviço que nunca roda não falha.

**O achado que valeu mais que o conserto:** os 7 leads estavam todos em `whatsapp_status = 'pendente'` — ou seja, **na fila**. Ligar o gatilho sem olhar teria mandado abordagem comercial para `5555978138934`, o número fantasma de DDD 55 que a gente identificou no dia anterior. Um estranho no Rio Grande do Sul recebendo mensagem de venda do Yachts Atlas.

Marcados como `teste_nao_enviar` — **não apagados**. Apagar seria a única operação irreversível da mesa, e por nada em troca: marcar tira da fila, preserva o histórico e dá para voltar atrás.

**Decisão do Marcos, contra a minha recomendação:** disparo automático (eu sugeri botão manual, por risco de banimento). Ele escolheu automático com carência. Implementado com três travas em variável de ambiente, e uma delas é a que reconcilia as duas posições: **`PROSPECCAO_AUTOMATICA` começa `false`**. O deploy não abre a torneira; ele abre quando quiser, e fecha na hora se der errado, sem esperar build.

**A carência (5 min em teste, 30 em produção) não é atraso técnico — é a janela de cancelamento.** Mensagem enviada não volta; lead na fila, sim. Formular assim mudou o que ela é: de "espera" para "salvaguarda".

**Padrão a repetir:** ao ligar qualquer rotina que fale com terceiros, olhar primeiro **o que já está na fila**. A fila acumulou durante todo o tempo em que o gatilho não existia, e ninguém a curou — porque enquanto nada disparava, o conteúdo dela não tinha consequência.

---

## 43. O e-mail tinha o nome na mão e foi perguntar para quem não sabia
**Data:** 24/08/2026

O ensaio ponta a ponta funcionou: cadastro → R$ 1,00 → webhook → acesso liberado → login → auditoria. O que não funcionou foi o que chegou na caixa de entrada: **"Olá, bem-vindo à Atlas."**, sem o nome de quem acabou de pagar.

A causa é o tipo de coisa que só aparece lendo a ordem das linhas:

```
webhook ACHA o usuario  →  usa so o .id para gravar em payments
        ↓
monta o e-mail          →  vai buscar o nome no metadata do LINK
        ↓
Payment Link e URL fixa →  metadata vazio  →  "Ola" pelado
```

Ele tinha a marina na mão e jogou fora tudo menos o `id`. E o lugar onde foi procurar é o único que **não pode** ter a resposta: metadata de Payment Link é o mesmo para todo mundo que paga por aquele link — por definição não é por cliente.

**Padrão a repetir:** quando um dado vem vazio, antes de arranjar outra fonte, perguntar **se a fonte atual poderia ter aquilo**. Campo compartilhado nunca guarda dado individual. Ordenei as três fontes por confiabilidade (cadastro → link → titular do checkout) em vez de trocar uma pela outra.

### O e-mail promete o que não controla

O rodapé dizia *"o recibo é enviado separadamente pela nossa processadora"*. Fui conferir: **estava desligado** na Stripe. O e-mail prometia uma coisa que não ia acontecer, e ninguém saberia — quem não recebe recibo não reclama, só desconfia.

Junto veio o achado maior: `_handle_invoice_paid` **não manda e-mail nenhum**. Renovação é silenciosa. Sem o recibo da Stripe, uma marina de US$ 250/mês recebia **um único e-mail no ano inteiro** — as outras onze cobranças no cartão, sem uma linha.

Ligado o recibo (e o de reembolso). Não conflita com a decisão de 21/08 de desligar os e-mails de cobrança: a régua do Atlas fala quando o pagamento **falha**, o recibo quando **dá certo**. Nunca disparam juntos.

### A conta é da empresa mestre, e o webhook é por conta

Foi o Marcos citar de passagem que existe outro produto na mesma conta Stripe para o buraco aparecer. Endpoint de webhook assina **tipo de evento**, não produto — links separados e endpoints separados não separam nada.

Duas travas saíram daí, e as duas são a mesma lição em roupas diferentes:

- A linha que libera acesso exigia `user_id`; **a que mandava o e-mail, não.** Cliente de outro produto receberia "seu acesso está liberado" com botão para um login que não é dele.
- `valor_pago == 200` **ignorava a moeda**. R$ 200,00 e US$ 200,00 são o mesmo `200.0` em ponto flutuante. Qualquer produto da casa a R$ 200/mês seria lido como marina fundadora.

**Padrão a repetir:** número sem unidade não identifica coisa nenhuma. Comparação de preço carrega a moeda junto, sempre — e quando duas linhas vizinhas decidem sobre o mesmo evento, elas precisam da **mesma** condição de guarda. Guarda que existe numa e falta na outra é o defeito esperando a ocasião.

### O que eu escrevi e o Marcos mandou desfazer

Pus a oferta contratada no corpo do e-mail — preço, prazo travado, meses de dossiê — argumentando que a campanha sai do ar e o e-mail fica, então ele provaria o acordo no 13º mês. O Marcos respondeu: *"o ideal é deixar o e-mail neutro, para servir para as duas, simples assim."*

Ele estava certo, e por um motivo mais forte que o dele: **para escrever a oferta, o e-mail tem de ADIVINHAR qual das duas foi vendida.** O metadata `programa` vem vazio nos Payment Links, então a única pista é o valor pago. Quando essa inferência erra, o e-mail não fica genérico — fica **errado, por escrito, no primeiro contato depois do cartão**. Fundadora lida como oficial receberia "dossiê 12 meses" tendo comprado 18.

**Padrão a repetir:** antes de pôr um dado num texto que vira comprovante, perguntar **de onde ele vem**. Dado inferido não deveria virar afirmação — vira, no máximo, decisão interna reversível. Não afirmar é melhor que afirmar errado, e o custo dos dois é assimétrico: silêncio se conserta com um segundo e-mail, contrato errado por escrito não.

Os prazos de dossiê ficaram no config mesmo sem leitor, porque o da oficial (12 meses) **não existia em lugar nenhum do código** — o modelo de cobrança escrito pela metade é o defeito que sobra.

### Do painel, no mesmo dia

Descoberto ao conferir o que o cliente vê: o extrato do cartão mostra o nome da **empresa mestre**, não o do produto. Marina que não reconhece a cobrança contesta, e chargeback em recorrente internacional cobra taxa e mancha o índice da conta. Descritor por produto (`AXOSHUB* YACHTSATLAS`) resolve sem tocar na estrutura societária. **Ainda aberto.**

---

## 44. Três dias caçando um defeito que era o teste de anteontem
**Data:** 25/08/2026

O Marcos estava desde sábado atrás de por que a abordagem não chegava na marina indicada. Chegou a perguntar se valia reconstruir o disparo em cima do ATLAS-SHOP.

Não havia defeito. O número que faz papel de cliente em **todos** os ensaios (`5512991187251`) respondeu **SAIR** no teste de opt-out de 23/08 e entrou na blocklist. De lá em diante toda indicação para ele virou `bloqueado`.

```
23/08  testa opt-out  ->  numero entra na blocklist
24/08  Marina Omega         -> bloqueado
24/08  Marina Porto Feliz   -> bloqueado
25/08  remove da blocklist, lead volta a 'pendente'
       06:13:54  enviado
```

Nenhuma linha de código mudou entre "não chega" e "chegou".

**Por que demorou três dias:** o sistema estava **acertando**. Respeitar opt-out não é falha — não levanta erro, não grava `whatsapp_erro`, não dispara alerta. O silêncio do acerto é idêntico ao silêncio da quebra, e foi nesse vão que o fim de semana foi embora. É a mesma família de §32 e §33, com uma diferença cruel: ali o sistema não sabia dizer o que faltava; aqui ele não tinha **por que** dizer nada.

**Padrão a repetir:** antes de procurar defeito num envio, olhar **o que o próprio sistema já decidiu sobre aquele destinatário**. Blocklist, status da fila, marcação de teste — dez segundos de SQL. Estado que suprime ação de propósito precisa ser o primeiro lugar a olhar, não o último, justamente porque ele não reclama.

**Padrão de ensaio:** não testar opt-out com o número que faz papel de cliente. O opt-out é permanente por natureza — é essa a graça dele — então ele envenena todos os testes seguintes daquele número. Ou usa número descartável, ou limpa a blocklist logo depois.

### Onde o agente conversacional tem lugar de verdade

A pergunta do Marcos sobre trazer o ATLAS-SHOP para cá estava mirando o alvo errado, mas o incômodo era legítimo. O disparo não precisa de LLM: precisa de fila, carência e opt-out, que já existem e funcionam — e mais peça conversacional só aumenta risco de banimento, que é por número.

O buraco está **depois**: o webhook de resposta faz `if not _quer_sair(texto): return`. Qualquer resposta que não seja "SAIR" morre ali, sem aviso a ninguém. Marina interessada respondendo "quanto custa?" fala com a parede.

**Primeiro toque simples, resposta inteligente.** É esse o recorte.

### De passagem

`PROSPECCAO_AUTOMATICA` já está ligada em produção — quem escreve `bloqueado` é o próprio `disparar_lote`, então o laço rodava o tempo todo. E o aviso ao fundador já saía pela instância `Marinas-Indicadas`, não pela transacional: restam só o código de acesso do armador e a régua de cobrança na `Programa-Atlas`.

---

## 45. O `required` que o próprio formulário desligou
**Data:** 25/08/2026

Segunda marina de teste cadastrada e paga — e o `telefone` foi para o banco **vazio**. O Marcos disse "culpa minha, esqueci de preencher". Não era.

O campo tem `required`. Só que o formulário tem quatro etapas e **só a etapa atual existe no DOM**:

```
input phone  ->  {step === 1 && (...)}
etapa 4      ->  o campo ja saiu da pagina
required     ->  o navegador nao valida o que nao esta la
handleSubmit ->  so conferia a senha
```

O atributo estava ali, visível no código, parecendo proteção. Não protegia nada desde que o formulário virou multi-etapa.

**Padrão a repetir:** validação de navegador (`required`, `pattern`, `type=email`) só vale enquanto o campo está renderizado. Formulário em etapas com renderização condicional **anula todas elas** no momento do envio. Em multi-etapa, a validação mora no submit — o atributo vira decoração.

**Padrão mais geral, que é o que dói:** "existe no código" não é o mesmo que "roda". Vale para o `required` daqui, para o `disparar_lote` que ninguém chamava (§42) e para a trilha de auditoria que existia e nunca gravou (§33). Três formas do mesmo defeito: código presente, caminho morto.

### Terceira vez que a mesma regra se divide entre telas

A regra do telefone — `+55` como rótulo fixo, máscara, recusa de incompleto — foi escrita em 24/08 e aplicada na `MarinaParceira` e na LP de Lançamento. **Não chegou ao `RegistroMarina`**, que é a página do cadastro PAGO.

Antes disso foi a senha (6 numa tela, 8 na outra, 10 no servidor) e o preço. Sempre o mesmo desenho: a regra nasce dentro da página onde o problema apareceu, e as outras páginas não sabem dela.

Agora vive em `frontend/src/utils/telefone.ts` e as quatro telas importam. **A correção não é "aplicar nos outros lugares" — é tirar a regra de dentro da tela.** Enquanto ela morar na página, a próxima página nasce sem.

### Uma decisão de produto no meio

Mínimo passou de 10 para **11 dígitos**. O número serve para WhatsApp, e fixo não recebe: aceitar 10 grava contato que nunca funciona, e falha em silêncio — a Evolution aceita a chamada e não entrega. O `1299187251` que o Marcos digitou (celular com um dígito a menos) passava como fixo válido.

Custo aceito: marina que só tenha fixo não se cadastra. Toda marina tem celular — é a premissa do produto.

### O que funcionou

O e-mail de boas-vindas chegou **com o nome**: *"Olá, Amazon Marina, bem-vindo à Atlas."* O conserto de ontem está em produção. E o recibo e a fatura da Stripe chegaram separados, como o Marcos queria.

---

## 46. A régua que qualquer cadastro pela metade alcançava
**Data:** 25/08/2026

O Marcos gerou o primeiro dossiê completo, viu sair **Ouro**, e a reação foi: *"o bronze poderia ser até 60, tá muito baixa essa régua"*. Estava certo — Prata começava em 50, ou seja, metade das categorias preenchidas já valia selo.

```
antes    Bronze < 50    Prata 50-79    Ouro >= 80
agora    Bronze < 60    Prata 60-89    Ouro >= 90
```

**A janela para mexer nisso era hoje.** Nenhum dossiê real foi selado ainda, e o PDF guarda a classificação **impressa**. Depois do primeiro cliente, mudar a régua faz o papel na mão dele contradizer a tela — e não há como recolher PDF emitido. Preço pago: o ativo de teste com 87 deixa de ser Ouro.

**Padrão a repetir:** parâmetro que sai impresso num documento imutável tem janela de ajuste que **fecha** — e ela fecha no primeiro cliente, não no lançamento. Antes de emitir o primeiro documento de verdade, revisar toda constante que vai aparecer nele.

### O que o selo faz com o comportamento

O Marcos resumiu o mecanismo melhor que eu: *"isso forçará a preencher os cadastros"*. É o desenho — a nota sobe conforme alimenta, então alimenta.

O que eu acrescentei, e importa: **incentivo para preencher é também incentivo para inventar.** Marina parada em 85 querendo Ouro pode lançar uma manutenção que nunca houve. Registro falso, selado, imutável, dentro do produto que vende custódia confiável — é o pior estrago possível, e é auto-infligido pelo próprio incentivo.

O que segura é a exigência de **prova** nas fichas (horímetro, peça trocada com foto, nota fiscal, executante). Conclusão prática: **nunca afrouxar upload obrigatório para facilitar a subida do score.** Score fácil de subir é score que o broker para de olhar — e aí o selo inteiro perde a função.

### O jetski não alcança Ouro com folga

Perguntado se jetski merecia tratamento diferente, fui ver. O painel **já** trata: esconde as abas `interior` e `pintura` para jet ski. O score **não** — continua contando as duas nas 10 categorias fixas.

```
jetski impecavel  ->  abrangencia 8/10  ->  40 + 25 + 15 + 10 = 90
```

Exatamente na linha do Ouro, sem margem nenhuma, por duas categorias que a própria tela decidiu que não existem para ele.

O veleiro foi resolvido (`CAT_ALIAS = {"velame": "motor"}`). O jetski não. **A mesma regra em dois lugares, terceira vez esta semana** — e o comentário no topo do `asset_score_service` literalmente pede "manter SEMPRE em concordância com o painel". Pedido em comentário não é mecanismo: o que não é uma fonte só, diverge.

Fica anotado para consertar medindo a abrangência contra as categorias **aplicáveis ao tipo**.

### O selo em duas línguas, cada tela na sua

Ao conferir a página pública de verificação num celular, o Marcos viu **"ÍNDICE DE CUSTÓDIA: GOLD"** e perguntou se o Claude tinha trocado para "Ouro" sem permissão. Fui ao git antes de responder, e a resposta é: **não**.

```
asset_score_service   retorna gold/silver/bronze desde que o score existe
Verificacao.tsx       nunca teve traducao — sempre mostrou o valor cru
nenhum codigo         grava "ouro" ou "prata"
AtivoHub.tsx          traduz gold -> Ouro na TELA, desde 26/06/2026
```

O dado nunca mudou. O que havia eram **duas apresentações do mesmo valor**: "Ouro" no painel da marina, "GOLD" na página que o comprador abre pelo QR.

**Padrão a repetir:** antes de aceitar ou negar "isso mudou", ir ao histórico. `git log -S"texto"` responde em segundos de onde veio cada string, e evita tanto a defesa injusta quanto a culpa aceita por engano. O Marcos estava certo no fato central — sempre foi inglês — e a divergência era de tela, não de dado.

Decidido: **inglês nas duas pontas** (`Gold` · `Silver` · `Bronze`). Selo é nome de grau; se a marina fala "Ouro" e o comprador lê "GOLD", os dois não estão falando da mesma coisa. Quatro ativos de demonstração com `ouro`/`prata` gravados à mão no banco foram normalizados.

---

## 47. O painel chamava toda marina pelo mesmo nome
**Data:** 25/08/2026

A Amazon Marina pagou, entrou no painel pela primeira vez, e foi recebida por **"Marina Hub — Fleet Excellence"**. O Marcos: *"aqui era pra ser Amazon Marina"*.

Não era leitura errada de campo. Era `t('common.marina_hub')` — **string de tradução fixa**. O painel nunca leu o nome de ninguém; toda marina que entrasse veria o mesmo título, desde sempre.

O contraste é o que incomoda: **o e-mail de boas-vindas, enviado minutos antes, já dizia "Olá, Amazon Marina"**. O dado estava em `user_metadata.marina`. O e-mail foi buscar; o painel não. Conserto de ontem numa ponta, defeito de sempre na outra.

**Padrão a repetir:** texto que *parece* nome próprio na interface merece desconfiança — "Marina Hub" lê como nome de cliente e é rótulo genérico. Ao conferir uma tela, perguntar de cada nome exibido: **isso veio do banco ou está escrito no código?** Rótulo disfarçado de dado passa despercebido justamente porque parece certo.

Corrigido em três lugares: o título do painel e as **duas** ocorrências no relatório de frota — que é documento que a marina baixa e manda para terceiro, então lá o nome errado sai da tela e vai para a mão de outra pessoa.

### O achado maior, que continua aberto

Investigando isso, o Marcos disse que tinha indicado pela "Marina Hub" e fui ver onde a indicação era guardada. Não era guardada em lugar nenhum.

```python
minha = supabase.table("marinas_lancamento").select("slot").ilike("email", data.email)
if not minha.data:
    return          # descarta o texto e segue
```

`marinas_lancamento` tem **20 linhas e zero e-mails preenchidos**. A busca nunca acha ninguém, o `return` cai **sempre** — para toda marina que se cadastra pelo Oficial, não só nos testes.

E o comentário da própria função promete o contrário: *"o texto cru fica guardado como ela digitou (…) nada disso pode ser descartado por não casar com um registro"*. A primeira linha do corpo faz exatamente o descarte que o comentário proíbe.

**Padrão a repetir:** comentário que descreve intenção não prova comportamento — e quando os dois divergem, o comentário é o que engana, porque quem lê para de conferir. Ao auditar função com docstring forte, ler o corpo **primeiro** e a documentação depois.

O peso disso: é o motor de crescimento de 20 → 40 marinas jogando fora o vínculo no **único** momento em que ele existe. Depois do cadastro ninguém lembra quem indicou quem — foi essa a razão de o campo ter sido criado em 21/08 (§15), e ele nasceu sem destino.

---

## 48. O teste estava verde porque construía o mundo que o código esperava
**Data:** 25/08/2026

Consertada a indicação que era descartada em todo cadastro do Oficial (§47). O conserto em si é trivial — inverter a ordem: gravar o texto cru no cadastro da marina primeiro, tentar casar com fundadora depois. O que vale guardar é **por que ninguém viu antes**.

Existia um teste chamado `test_o_que_ela_digitou_fica_guardado`, com docstring dizendo *"vale inclusive quando não casa com registro nenhum — perder o dado não tem conserto"*. Ele estava **verde**. E a produção descartava 100% das indicações.

O motivo está no cenário:

```python
def _cenario():
    return _Banco([
        {"slot": 1, "email": "fundadora@marina.com", ...},
        {"slot": 7, "email": "nova@marina.com",  ...},   # <- a marina do teste
    ])
```

Em produção, `marinas_lancamento` tem 20 linhas e **nenhuma** com e-mail. O fixture deu e-mail à linha da marina que se cadastra — construiu o mundo em que a função funciona, em vez do mundo que existe. O teste provava a promessa dentro do cenário onde a promessa já valia.

**Padrão a repetir:** um fixture é uma **afirmação sobre a realidade**, e ninguém a revisa. Ao escrever cenário de teste, perguntar de cada campo preenchido: *isso está preenchido em produção?* Uma consulta ao banco real responde em segundos e é a diferença entre teste que protege e teste que decora.

**Sinal de alerta específico:** teste verde + defeito real na mesma função é quase sempre fixture otimista, não lógica errada. Antes de duvidar do código, duvidar do mundo que o teste montou.

Acrescentado o teste do caso real — marina fora do lançamento, banco sem correspondência — que falha com o código antigo (o `update_user_by_id` nunca era chamado).

**Terceiro sintoma da mesma doença desta semana:** comentário que promete (§47), fixture que assume (aqui) e `required` que não valida (§45) são todos "o código diz uma coisa e o sistema faz outra". Nos três casos a documentação era mais confiável que o comportamento — e por isso ninguém foi conferir.

---

## 49. O barco não tinha onde ter nome
**Data:** 25/08/2026

Fui montar três embarcações de teste com nome próprio ("Lady Cristy") e descobri que **não dá para nomear barco nenhum pela tela**.

```
nome_reg  lido em 7 telas   dossie · verificacao publica · painel · portal do armador · listagens
          escrito em        nenhum lugar
```

A coluna existe no banco. Não estava declarada no `AtivoBase` nem no formulário. Todo barco caía no `marca + modelo` — daí o dossiê de um iate se apresentar como *"Marlin Sea Focus"*, que é fabricante e modelo, não nome. Os únicos ativos com nome eram os de demonstração, inseridos à mão via SQL.

**É a segunda vez que esse defeito exato acontece no mesmo arquivo.** O comentário do próprio `AtivoBase`, escrito quando consertaram largura e calado, descreve:

> *"As colunas existem no banco desde sempre e NENHUMA era declarada aqui — o getattr lia None e o dado nunca era gravado. Código morto que parecia vivo."*

Consertaram as dez colunas de especificação e **não olharam o resto da tabela**. O nome ficou.

**Padrão a repetir:** ao achar coluna do banco que o schema não declara, não consertar só a que apareceu — **listar a tabela inteira** e conferir campo a campo o que é lido, o que é escrito e o que é só exibido. `information_schema.columns` contra o modelo Pydantic responde de uma vez. É a mesma lição de varrer-a-classe-inteira, na dimensão "coluna que existe mas ninguém preenche".

**Sintoma que identifica a família:** dado que aparece bonito nas telas de demonstração e vazio no uso real. A demonstração foi populada à mão, então ela nunca passa pelo caminho que está quebrado — e é justamente ela que todo mundo olha para conferir se está funcionando.

Fechado nas quatro pontas (schema, insert, formulário, reset do formulário). O reset só apareceu porque o `tsc` reclamou de campo faltando — validação de tipo pegando o que revisão de olho não pega.

---

## 50. Pagador e custodiante têm de ser pessoas diferentes
**Data:** 25/08/2026

Conversa de desenho, não de código: quem pode mandar foto do celular para o cofre. Decidido **gerente e encarregado da marina; o dono do ativo só lê.**

O Marcos chegou sozinho na dúvida certa — *"o dono do ativo está correto isso? acho que não, hein!"* — e depois no motivo comercial: *"pq quem paga é a marina"*. Os dois argumentos, o de integridade e o de negócio, chegaram no mesmo lugar. Quando isso acontece, a decisão costuma estar certa.

**O princípio que ficou:** autoridade de selo não vem de quem paga nem de quem é dono — vem de ser **independente do resultado**. O armador vende o barco; o dossiê forma o preço. Ele alimentando o próprio histórico transforma o documento em declaração do vendedor, que é justamente o que o mercado já ignora e o que o Atlas existe para substituir.

Ele testou o princípio: *"se ele arcar com a contratação pessoal aí muda a história, correto?"* Meia resposta — pagar muda os **direitos de cliente** (relatório, portal, suporte), não muda **quem sela**. Pagador e custodiante são papéis distintos, e o produto só funciona enquanto forem pessoas distintas.

**Padrão a repetir:** ao decidir permissão, perguntar não "quem paga?" nem "de quem é a coisa?", mas **"quem perde se o registro for falso?"**. Quem tem interesse no resultado não assina o resultado.

**O custo de abrir a porta não é caso a caso.** Bastaria o comprador saber que o dono *podia* contribuir para que todo dossiê ficasse sob suspeita — inclusive os que ele nunca tocou. Credibilidade se avalia pela regra, não pela exceção. Vale para qualquer decisão futura sobre quem escreve no cofre.

### O risco técnico que a decisão evita

Se o material do armador caísse direto em `documentos`, quebraria duas coisas prontas: `asset_score_service:114` e `dossie_data:441` leem a tabela **sem filtro nenhum**. Ele inflaria a nota da marina (8 fotos levam de Silver a Gold) e entraria no PDF selado sem ninguém aceitar.

A forma certa já existe no próprio sistema — `registros_rascunho` × `registros`. Entrada em tabela separada, aceitar move para `documentos`. Assim **nenhum consumidor muda**, porque `documentos` continua significando "está no cofre".

**Padrão a repetir:** quando um novo caminho de escrita aparece, perguntar o que a tabela de destino **significa hoje** para quem já lê dela. Acrescentar linha com sentido diferente na mesma tabela é como acrescentar um segundo vocabulário numa coluna — e hoje já apareceram dois desses (`gold`/`ouro`, `verified`/`validado`).

---

## 51. O quinto componente pronto que ninguém tinha ligado
**Data:** 25/08/2026

O Marcos perguntou como, no futuro, a foto do celular chegaria ao banco e que ferramentas seriam necessárias. Fui olhar antes de responder e achei `SecureCameraUpload.tsx` — completo, com `capture="environment"` (abre a câmera traseira do celular), preview, tratamento de erro. **Nenhum arquivo o importava.**

Quinto caso do mesmo padrão **no mesmo dia**:

```
required inerte no formulario multi-etapa   (§45)
disparar_lote sem chamador                  (§42)
indicacao com return antes de gravar        (§47)
nome_reg lido em 7 telas, escrito em zero   (§49)
SecureCameraUpload sem nenhum import        (aqui)
```

**Padrão que já dá para nomear:** neste projeto, o defeito dominante não é código errado — é **código certo desconectado**. Construído, testado de perto, e nunca plugado. Não aparece em log, não quebra teste, não gera erro. Só não acontece.

**Como procurar de propósito, em vez de por acaso:** para cada componente em `components/`, `grep -rn "NomeDoComponente" src` e ver quem importa. Para cada função de serviço, o mesmo. Leva minutos e devolve a lista inteira — em vez de descobrir um por vez, sempre por acidente, sempre em cima da hora.

### A ordem que o Marcos corrigiu

Eu propus escrever o texto nas LPs primeiro e ligar a câmera depois. Ele cortou: *"eu digo deixar funcional primeiro e depois ajusta as LPs, pq aí já sabemos que está realmente funcional!"*

Ele estava certo, e o dia já tinha dado duas provas: o rodapé do e-mail prometia um recibo que estava **desligado** na Stripe, e a etapa 4 do cadastro promete um **vídeo que não existe**. Página que afirma antes de existir vira dívida silenciosa — ninguém reclama, e a promessa fica falsa até alguém reparar.

**Padrão a repetir:** construir → verificar → anunciar. Nunca a ordem inversa, e nunca as duas ao mesmo tempo.

### De brinde, a coordenada

`latitude`, `longitude` e `geo_fonte` já existiam na tabela e no endpoint; ninguém mandava. Agora a foto sobe com onde e quando foi tirada — dado que **não tem como ser reconstruído depois** e que vale muito num dossiê de custódia.

Best-effort de propósito: sem permissão, sem sinal ou passando de 5 s, sobe sem coordenada. Registro sem geo é bom; registro que não sobe porque o GPS demorou não serve para nada.
