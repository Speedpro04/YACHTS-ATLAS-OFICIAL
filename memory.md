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
