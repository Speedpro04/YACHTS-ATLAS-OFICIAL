- [x] **REV-18 — O título vivia em dois arquivos: um deles virou espelho declarado**: em 30/08 (`2c912b8`) os dois foram **sincronizados**, o que pela regra *uma fonte por fato* não é conserto — é adiamento. O fundador cobrou a consequência: *"título deve ser apenas [um]. Temos que decidir."* Ao ir fechar, apareceu que o `prerender.mjs:80` **já regrava o próprio `dist/index.html`** a partir do `seo-data.json`, e o prerender está dentro do `npm run build` — ou seja, o JSON **já ganhava sempre** e o texto do `index.html` de origem nunca chegava ao ar. O defeito não era divergência de valor: era **um valor decorativo que não avisava que era**. Quem editasse ali não veria efeito nenhum, que foi exatamente o que aconteceu na segunda. Entrou um comentário de 9 linhas antes do `<title>` listando as **12 tags que o build sobrescreve** (title, description, keywords, robots, canonical, og:title/description/url/image/image:alt, twitter:title/description) e as **11 que são fonte de verdade ali** (og:type, og:site_name, og:locale, og:image:width/height, twitter:card, twitter:image, twitter:image:alt, author, theme-color, hreflang e o JSON-LD) — assimetria que ninguém tinha mapeado e que explica por que `og:image` é espelho mas `twitter:image` não é. **Descartada a Opção B** (build quebrar na divergência): protege um cenário que não existe, já que o prerender não é passo opcional. A primeira versão do comentário citava o incidente de 30/08 com data — cortado, porque o comentário **vai para o HTML público** e histórico interno não é conteúdo de página. Build com **0 avisos do prerender**: as 12 tags encontradas, e `/`, `/frota` e `/sobre` conferidas contra o JSON.
- [x] **REV-18 — `Programa Fundador` vira `Programa Atlas` no title de `/termos-fundadores`**: única linha aprovada da revisão de títulos. Troca nome genérico por nome de marca sem gastar caractere (42 → 39). A rota é `noindex`, então o ganho é de consistência, não de busca. O `<h1>` da página (`TermosFundadores.tsx:9`) **continua** "Termos do Programa Fundador" — fica fora do pedido, que era title e mais nada.
- [x] **REV-18 — "Marina" virou nome próprio em todo o texto que o visitante lê**: decisão do fundador — a palavra passa a ser termo da marca, não substantivo comum. **97 trocas em 23 arquivos** de `frontend/src` mais **10 no `index.html`** (title, description, keywords, og/twitter e o FAQ em JSON-LD). O trabalho todo foi separar *texto* de *código*: uma troca cega quebraria o campo `name="marina"` do formulário de indicação, a rota `/marina-parceira`, as chaves `marina_nome`/`contrato_marina`, o endpoint `/leads/marina` e a chave de i18n `benefit_marina_text`. Duas travas fazem o corte — regex que recusa `marina` colada a `@ . / - _` (por isso `contato@marina.com.br` e `https://www.marina.com.br` seguem minúsculos: e-mail e domínio não têm maiúscula) e um leitor de comentário que ignora `//`, `/* */` e `{/* */}`. **A primeira tentativa não tinha o leitor de comentário e foi jogada fora**: reescreveu 53 linhas de comentário, e uma delas — o comentário do `Dashboard.tsx:16`, que diz qual campo o cadastro grava no metadata — passou a nomear um campo que não existe com essa grafia. Comentário não é página; ficou como estava.
- [x] **REV-18 — "Programa Atlas" e "Dossiê" entram no SEO**: acrescentados na frente das **10 listas de `keywords`** do `seo-data.json` (default + 9 rotas) e na do `index.html`. Como o `prerender.mjs` lê desse mesmo JSON, as **7 rotas pré-renderizadas** e o `sitemap.xml` saem com os termos sem tocar em mais nada. Fica registrado o limite do que isso compra: `<meta name="keywords"` **não pesa mais no Google** — o que pesa é title, description e H1. Nesses os dois termos ainda não entraram de propósito: *Programa Atlas* aparece só no corpo de duas páginas (alertas de norma na Oficial e a chamada de indicação da Marina Parceira) e *Dossiê* já está no title de duas rotas. Levar os termos para os títulos é reescrever a chamada da marca — decisão do fundador, não foi pedida.
- [x] **REV-17 — A headline mudou de frase, e a medição do REV-14 não valia mais**: o fundador trocou a parte B de *"Onde está registrada?"* para *"Mas onde ficam registrados seus dados hoje?"* — e pediu 78px. A frase que ele escreveu vinha com **"fica registrados"**, erro de concordância (o sujeito é *seus dados*, plural), corrigido para **"ficam"**; ele também escreve com espaço antes do `?`, e pediu explicitamente a forma correta no produto. O que a medição pegou: o texto novo tem **o dobro do antigo** (43 contra 21 caracteres), e a calibragem de celular do REV-14 — 15% da tela, feita para a frase curta — tinha ido para **26,5% em 7 linhas**. `2.25rem` → **`1.85rem`** devolve **14,9% no iPhone 14**, e todos os aparelhos daquele REV voltaram ao patamar de antes (SE 375 18,9%, Android 360 20,5%, 15 Pro Max 13,5%), CTA na dobra e zero scroll horizontal. No desktop, 88px punha o CTA **82px fora da dobra**; 78px faz a parte B cair de 3 para 2 linhas e o CTA fecha com folga
- [x] **REV-17 — A separação entre as duas frases, e a armadilha que ela abriu**: parte A é uma afirmação e parte B é uma pergunta, mas o `<br />` as separava com a **mesma entrelinha** que separa as linhas *dentro* de cada uma — o bloco lia como um parágrafo só e a pergunta perdia o efeito de virada. Trocado por `block mt-3 md:mt-4`. **O `block` quebrou o dourado**: aquele texto é `bg-clip-text`, o degradê é pintado dentro da CAIXA e recortado na forma das letras, e como bloco a caixa passou a ter a altura da entrelinha — que no desktop é `0.95`, **menor que 1**. O descendente do "j" de "hoje?" caía **7px fora da área pintada** e sumia. Resolvido com `pb-[0.14em] -mb-[0.14em]`: o padding estende a caixa de pintura, a margem negativa devolve o mesmo tanto no layout. Como inline isso não acontecia, porque a caixa seguia as métricas da fonte — **é uma armadilha específica de `bg-clip-text` + `block` + entrelinha abaixo de 1**
- [x] **REV-17 — O mesmo padrão em duas outras páginas, e por que não nas outras duas**: aplicado em `Sobre` (*"Documentado uma vez." / "Verdadeiro para sempre."*) e `MarinaParceira` (*"Sua indicação." / "Sua receita."*) — duas frases completas, mesma virada. A `Sobre` caiu **na mesma armadilha do `bg-clip-text`** e levou o mesmo `pb`/`-mb`: medido, o "p" de "sempre." ia a 64,5px numa caixa de 60px. **Não** aplicado em `Frota` (*"A Excelência em" / "Movimento."*) nem em `Segurança` (*"Segurança em" / "Criptografia Pura."*): ali o `<br />` quebra o meio de **uma única oração**, e dar respiro afastaria palavras da mesma frase. O efeito que funciona vem de separar dois pensamentos, não duas linhas. Na `MarinaParceira` o padding não foi preciso: o dourado ali é **cor sólida**, não `bg-clip-text`
- [x] **REV-17 — A logo estourava o header nas duas pontas, e ninguém tinha visto**: o arquivo é **quadrado (500×500)**, mas o `<img>` declarava `180×60` — proporção que não existe, fazendo o navegador reservar o espaço errado antes de carregar. Pior: a logo era dimensionada pela **largura** com `h-auto`, então a altura virava igual à largura — **130px dentro de um header de 96px** no celular e **180px dentro de 166px** no desktop. Ela vazava por cima do hero nos dois casos; o fundador viu no celular. Agora é presa pela **altura** (`h-full w-auto`), que torna o transbordo impossível por construção. Celular em **96px**, o maior possível sem invadir (ele pediu *"perto de invadir a primeira dobra"*): ela vai de `-0,5px` a `95,5px` numa faixa que acaba em 96px. Desktop mantido em **180px**, ultrapassando a faixa **de propósito** — é o tamanho que ele quis de volta. Não aumentar `--header-h` para "consertar" isso: a 1440×900 o CTA fecha a dobra com 4px
- [x] **REV-17 — O "ROLAR" estava POR CIMA do botão, não colado nele**: o indicador é `absolute bottom-10` e o conteúdo do hero é centralizado — não havia nada reservando o espaço dele. Quando a headline cresceu, o conteúdo desceu e o vão entre o CTA e o "ROLAR" ficou em **−62px**: o indicador começava 62px **acima** do fim do botão. `py-[50px]` → `pt-[50px] pb-[140px]` (40px de recuo + 72px de altura do indicador + 28px de respiro). Vão agora: **28px no desktop, 92px no celular**, CTA na dobra nos dois
- [x] **REV-17 — Menu do celular de 24 para 32px**: calibrado a olho pelo fundador em quatro passos (26 → 28 → 30 → 32), cada um conferido na tela. Fica registrado o que **não** foi feito: a área de toque continua do tamanho exato do ícone, porque o botão não tem padding — **32×32 contra os 44×44 da Apple e 48×48 do Android**. É o botão que abre o menu inteiro no celular. O botão também **não tem `aria-label`**: para leitor de tela é um botão sem nome
- [x] **REV-14 — A página Oficial vendia para quem não compra**: a copy falava com o **armador** em todas as seções principais — "Seu iate não é apenas um ativo", CTA "Proteger meu Ativo", "blinda a história do seu ativo", "vale até 20% mais", "reduza o tempo de venda em 60%". Só que quem assina os **US$ 250/mês é a marina**, e ela aparecia apenas no bloco de indicação e numa pergunta do FAQ. 41 textos reescritos para falar com quem paga, sem mexer em estrutura, componente ou preço
- [x] **REV-14 — Três incoerências que o reposicionamento revelou**: a página de Segurança dizia *"cada **proprietário** recebe uma chave... você e as **entidades autorizadas** (marinas, seguradoras)"* — tratando a marina como terceiro autorizado pelo dono, enquanto a landing afirma o oposto na mesma visita (*"a custódia é da marina"*). Não era desalinhamento de tom: as duas afirmações **se contradiziam**. Junto: o Sobre dizia "custodiamos a verdade do seu ativo", e o Portal do Proprietário estampava *"Seu Ativo. **Seu Controle**"* — contradizendo o próprio `readOnly` da tela, onde o armador só consulta
- [x] **REV-14 — O SEO estava em dois lugares e divergindo**: o `index.html` foi ajustado para falar com marina, mas existe `frontend/src/seo/seo-data.json`, que o `SeoMeta.tsx` aplica em runtime (`document.title = title`) e **sobrescrevia**. Dava para ver acontecendo: a aba mostrava o título novo e três segundos depois voltava ao antigo. Décima ocorrência do padrão "mesma regra em dois lugares" neste projeto
- [x] **REV-14 — "Dossiê Yachts Atlas" → "Dossiê Atlas"**: decisão do fundador — *"é mais fácil de falar, guardar e mais fácil de pegar no mundo náutico"*. Seis ocorrências no Oficial (incluindo o título de metadados do PDF, que aparece na aba do leitor) e três no Lançamento. **Só onde a expressão aparecia literalmente**: a capa e o cabeçalho do documento seguem "Dossiê de Custódia e Conformidade Náutica" — o nome comercial é um, o título formal é outro, e é o formal que sustenta o peso perante Autoridade Marítima e seguradora
- [x] **REV-16 — A última porta que ainda destruía histórico foi fechada**: `registros` e `documentos` já recusavam DELETE por gatilho, e `registros` recusa até UPDATE (só a redação LGPD passa, com seis travas). Mas **`ativos` não tinha nenhum** — um DELETE ali levava os registros junto, **em cascata**, contornando por cima toda a imutabilidade construída embaixo. Cadeia de custódia com porta aberta na tabela-pai não é cadeia de custódia, e é a primeira coisa que um auditor de SOC 2 procura. Aplicado em produção e **provado lá**: DELETE recusado, mensagem ensinando o caminho, 14 ativos antes e 14 depois. Risco zero — ninguém apagava ativo (nenhum `.delete()` sobre `ativos` no backend nem no frontend) e o substituto já existia e já era usado: `arquivado_em`, com 6 dos 14 ativos arquivados por ele
- [x] **REV-16 — A trilha de auditoria passou a responder perguntas**: `audit_logs` guardava tudo o que SOC 2 / ISO 27001 / SUSEP pedem — quem, o quê, quando, de onde, com que resultado — e tinha **184 linhas gravadas**. Só que nada sabia interrogá-la: `audit_service` listava os eventos de UM usuário em ordem cronológica, e auditoria não se responde com lista cronológica. Novo `services/auditoria_relatorio.py` (Polars) e `GET /api/v1/auditoria/{relatorio,exportar}`, ambos exigindo admin da plataforma. A primeira execução já respondeu o que exigia SQL na mão: **14 "Invalid signature", 9 "Invalid maintenance credentials", 1 "File validation failed"**, com série por dia e IP de origem
- [x] **REV-16 — Polars entrou em UM lugar, e está escrito por quê**: medido em 30/08 — 188 registros, 96 documentos, 14 ativos. Nessa escala o DataFrame custa mais que o laço, e por isso `dossie_data` e `asset_score_service` **continuam em Python puro**. `audit_logs` é a exceção porque é a única tabela que cresce sem parar (append-only, e a SUSEP fala em reter de 5 a 10 anos), as perguntas são agregação pura, e a saída precisa virar arquivo — Polars escreve CSV e Parquet sem dependência nova. O motivo está no cabeçalho do módulo para ninguém "corrigir" a ausência depois achando que foi esquecimento
- [x] **REV-16 — Três pendências do PRD estavam desatualizadas e guiavam decisão errada**: o bucket `media` consta como "hoje é público" e está **privado**; `audit_logs` consta com "insert falhando por RLS" e tem **184 linhas**; e o docstring do `backfill_embeddings.py` dizia `text-embedding-ada-002` enquanto o código sempre usou `text-embedding-3-small` — se alguém acreditasse e re-rodasse o backfill, o corpus e a consulta passariam a viver em espaços vetoriais diferentes e a Solara responderia lixo com cara de resposta
- [x] **REV-15 — Lançamento e Oficial diziam números diferentes sobre o mesmo produto**: a capacidade fotográfica aparecia como **460** no sistema (`MAX_FOTOS`, soma dos mínimos de `COBERTURA_CATS`), **430** no Oficial e **400** no Lançamento — três números para o mesmo fato, e nenhum dos dois anunciados batia com o código. Decisão do fundador: **460**, o que o sistema realmente faz. E a correção foi de raiz: a landing do Oficial passa a **ler a constante** em vez de repetir o número à mão, então não há mais como divergir
- [x] **REV-15 — "16 seções padronizadas" não correspondia a nada**: o Lançamento anunciava 16. O gerador tem 11 seções fixas numeradas mais uma por categoria com registro (máximo teórico de 22), e o dossiê real do Ferretti 780 — 19 páginas, bem preenchido — saiu com **10**. O número sempre varia, porque a regra do documento é "seção sem dado não é renderizada". Trocado por **"Estrutura padronizada"**: diz que é organizado e uniforme, sem prometer uma contagem que o sistema não garante
- [x] **REV-15 — As vagas se contradiziam dentro do Oficial**: `referral_slots` dizia "Apenas **14** vagas disponíveis" e a Marina Parceira anunciava "Meta pública: **120** vagas", em duas passagens — contra as **20** fundadoras do modelo definitivo, que é o que o Lançamento já dizia. O fundador mandou tirar as 120 (*"nem era pra colocar isso"*) e fixar 20. A `referral_slots` era **chave órfã** — não renderizada em lugar nenhum, guardando número errado para quem fosse usá-la depois
- [x] **REV-15 — Os três filtros de copy aplicados também ao Lançamento**: *"A marina guarda **dados soltos** em planilhas, papel e mensagens. Cada troca de responsável **recomeça do zero**"* (supõe falha), *"Sem histórico verificável, **o iate vale menos**"* (fala com o armador, não com a marina), *"vêm exigências extras, **prêmios maiores** e demora na apólice"* (alarme). E uma contradição interna: a página usa **WhatsApp como canal oficial de contato** ("Falar no WhatsApp", botão de conversão) e, em dois outros lugares, como símbolo de bagunça. Os canais de contato ficaram intactos
- [x] **REV-14 — Headline calibrada por medição, aparelho a aparelho**: a headline nova é bem mais longa que a antiga, e no celular ocupava **32% da tela** em 7 linhas. O fundador pediu **15%**. Medindo, a proporção pula de 13% para 17% ao mexer só no corpo da fonte — porque a headline salta de 4 para 5 linhas. O ponto foi achado pela **entrelinha**, que no celular estava em 0,95 (apertada demais para leitura em tela pequena): `2.25rem` + `leading-[1.05]` dá exatamente 15% no iPhone 14, mantendo 4 linhas. De `sm` para cima nada muda. Conferido em iPhone SE (23%), Android 360px (19%), iPhone 14 (15%), 15 (14%) e 15 Pro Max (13%) — **CTA dentro da dobra e zero scroll horizontal em todos**
- [x] **REV-14 — Três filtros de copy que passam a valer para tudo**: sem citar empresa do mesmo ramo, sem supor falha de quem lê, sem alarme. A primeira versão da copy — escrita por mim — violava os três: "o que a sua marina entrega e **a vizinha** não" (reprovado como *vulgar*), "sua equipe **para de caçar papel**", "vira **palavra contra palavra**", "o que sua operação **já paga em retrabalho e cliente perdido**", "o registro não pode viver num **grupo de WhatsApp, numa gaveta e na memória do encarregado**". Saiu também do onboarding a frase pré-existente *"marinas que não oferecem segurança digital estão perdendo espaço para o futuro"*
- [x] **REV-13 — "Crítico (Avaria Estrutural)" chegava ao dossiê como CONFORME**: `STATUS_ENUM` no `FichaServicoForm` traduzia **três** textos exatos — 'Concluído', 'Pendente', 'Atenção' — e todo o resto caía em `|| 'registrado'`. Só que as fichas oferecem **sete** conjuntos de rótulos: casco, velame, pintura, interior, seguro e sinistro não usam nenhuma dessas três palavras sozinhas. **14 dos 17 rótulos do sistema** viravam 'registrado', que em `_saude_por_categoria` cai no `else: st = "ok"` — CONFORME, peso 100. Pior: o agravamento criado em REV-06 (casco e sinistro em atenção valem 0) **nunca chegou a disparar uma única vez**, porque o status jamais chegava como 'atencao'. A trava existia e estava desligada na origem. Agora a leitura é por prefixo, não por igualdade
- [x] **REV-13 — Nove números da capa param de prometer o que não medem**: capa dizia **28 documentos** e a pág. 4 listava 10 (o tile somava fotos com documentos); **"Investido no ativo"** somava *prejuízo estimado* de sinistro e *estimativa de reparo* de casco com gasto real — o R$ 2,5 mi voltando por outro campo; **"Hashes íntegros 100%"** contava coluna preenchida por trigger e prometia uma conferência que a emissão não faz; **custo/mês** dividia o gasto histórico pela idade do **cadastro**; **horímetro** era o `max()` de quatro máquinas diferentes; **vencimentos** guardava a data mais distante por campo e escondia a CHA vencida, sempre a favor do barco; **linha do tempo** misturava data de serviço e de cadastro (no Ferretti, os 13 marcos saíram todos em "08/2026"); a capa prometia **13 registros** e o corpo detalhava 12; e a data sob cada foto era a do **upload**, impressa ao lado do GEO — o gêmeo do defeito que já foi corrigido pela metade
- [x] **REV-13 — O cabeçalho do dossiê volta a ser copiável**: o letter-spacing quebrava a extração de texto — saía `P r o t o c o l o   Y A - I A T E`, que lido corrido vira **"YA HATE"**. Foi exatamente assim que um revisor externo relatou "protocolo corrompido" e "CNPJ divergente" num PDF impresso corretamente. Medido: o extrator desiste quando *tracking ÷ corpo da fonte* ≥ 0,15, e os quatro textos do cabeçalho estavam acima. Teto de 0,14 no `draw_tracked`; marca e assinatura seguem decorativas. Quem depende disso: o comprador que **copia o protocolo** para colar no verificador, o Ctrl+F, o leitor de tela
- [x] **REV-13 — Galeria com celas iguais e textos legíveis**: cada foto entrava com a altura que tinha, e uma imagem em retrato no meio da linha abria buraco — nas páginas 15 e 16 do dossiê do Ferretti sobrava de **um terço a 40% de página em branco**. Agora cela 4:3 fixa, com a imagem encaixada inteira (*contain*, nunca recorte: num dossiê de custódia a foto é evidência e cortar pode cortar a avaria). Junto, por reclamação de legibilidade: `WHITE_FAINT` estava em **2,88:1** e `GOLD_DIM` em 3,66:1 contra a superfície — abaixo do mínimo de 4,5:1, e carregando justamente o texto miúdo de 5,5 a 7 pt. Ambos agora em 4,6:1, mesmo matiz
- [x] **REV-13 — O painel para de chamar de "Saúde" o que não mede saúde**: `[ Gold ] [ Saúde 91% ]` eram **o mesmo número** exibido duas vezes — o score de abrangência, que não lê o `status` de nenhum registro. Um barco com sinistro aberto pontuava igual a um impecável. Agora `[ Índice de Custódia: Gold ]` (o rótulo que o dossiê e a página pública já usavam) e, no lugar do número repetido, a **Conformidade** com o denominador, calculada do `health_status` que já chegava e ninguém usava. Clicar abre o critério dos dois
- [x] **REV-13 — 22 testes novos, e um deles achou defeito enquanto era escrito**: `test_dossie_numeros_e_selo.py`. O teste que confere se todo rótulo do formulário tem regra **falhou na primeira execução** e apontou quatro que eu não tinha visto, todos da ficha de sinistro — inclusive **'Nao reparado'**, que saía CONFORME. Os testes que mais valem são de **contrato entre as pontas**: rótulo novo sem regra quebra; leitura por igualdade exata quebra; conformidade voltando a ser barra quebra; segundo CNPJ no código quebra
- [x] **REV-12 — O DOSSIÊ-ATLAS para de imprimir quadrado preto no nome do dono**: o gerador usava as fontes base-14 do PDF (Helvetica, Times-Bold), que só conhecem Latin-1. Fora dele o ReportLab troca o caractere **sem erro e sem log** — `Dvořák` saía `Dvo■ák`, `Łukasz` saía `■ukasz`, num documento selado por SHA-256 que afirma integridade. Agora Arial e Times New Roman (mesmas medidas: **+0,01%** de largura no pior texto real, layout intacto) e `fonts-liberation` no Dockerfile, porque produção é Debian e não tem fonte da Microsoft. Junto: **`logger` era usado e nunca importado** — `NameError` dentro do próprio `except` derrubava a emissão inteira quando uma foto falhava, justo o caso que o "Imagem indisponível" existia para tratar
- [x] **REV-12 — O critério do Índice sai do código e entra no documento**: o dossiê estampava CONFORME / ATENÇÃO / CRÍTICO / NÃO AVALIADO e um percentual, e **em nenhum lugar dizia como aquilo foi decidido**. Nova seção **"Como Ler Este Índice"** com a tabela de pesos, o cálculo, os agravamentos (casco, sinistros, EPIRB sem ANATEL) e as retificações — mais uma linha curta sob a grade, porque quem lê no celular não vai à página 12. Ideia do Marcos
- [x] **REV-12 — CONFORMIDADE deixa de ser barra**: ela é quase sempre 100% (só entra na conta o que tem registro) e a linha cheia de ponta a ponta afirmava "completo" antes de a legenda ser lida. Deixá-la fina e dourada (REV-06) não bastou — **forma vence cor**. Virou número e frase: *"Calculado sobre 3 de 11 sistemas — 8 sistemas sem registro não entram na conta."* Barra fica só para a cobertura, que é o que varia
- [x] **REV-11 — Duas caixas que pareciam upload e não eram**: no formulário de Novo Registro de Serviço havia duas áreas com borda tracejada, ícone e cursor de mão — "Clique para adicionar fotos" e "Clique para adicionar recibos" — e o componente **não tinha nenhum `<input type="file">`**. Clicar não fazia nada, nem dava erro. Está atrás do login (rota `registros/:ativoId`), então quem esbarrava era a marina **já paga**, no primeiro serviço que fosse registrar. Numa tela que promete cofre imutável, botão que não responde é pior que botão ausente. Trocadas por uma linha que diz onde o upload funciona de verdade
- [x] **REV-10 — A marina pagou e ficou sem a vaga**: no teste de 27/08 a Antioquia Marina preencheu o cadastro, o sistema reservou uma das 4 vagas de SP no nome dela, ela pagou — e a vaga continuou `reservado`, vencendo em 3 horas. Pagamento, acesso e e-mail saíram certos; **só a vaga ficou para trás, sem erro em lugar nenhum**. O código só sabia perguntar "veio do link certo?" e "o valor bate?", e nenhuma das duas responde nada num link de teste. Agora existe uma terceira pergunta que não depende de configuração: **"tem vaga reservada nesse e-mail?"** — a reserva foi criada pelo próprio cadastro, minutos antes
- [x] **REV-09 — A marina brasileira paga em real, e a vaga de fundadora para de depender do valor**: em 19/08/2026 um Visa recusou uma cobrança de US$ 250 com **"moeda não aceita"** — cartão brasileiro costuma vir com compra internacional bloqueada, e Elo/Hipercard são nacionais, em dólar não passam de jeito nenhum. O preço anunciado continua em dólar; o servidor escolhe o link em real quando a UF é brasileira. Junto foi o defeito que isso teria criado: a vaga de fundadora era reconhecida por `moeda == usd E valor == 200`, então pagamento em real entraria **sem ocupar vaga e sem os 18 meses de dossiê**. Agora vem do **link de origem**
- [x] **REV-08 — WEBP entra, e as oito listas de arquivo viram uma**: cada tela decidia sozinha o que aceitava, e elas discordavam — a Documentação e a ficha de serviço recusavam WEBP, a galeria recusava, o cadastro de categoria aceitava qualquer imagem. A mesma foto subia numa tela e era barrada na outra, sem explicação. Agora tudo vem de `utils/arquivos.ts`, e o texto da tela deriva da lista (não dá para prometer um formato que o seletor recusa). Duas exceções ficaram, ditas no código: o botão **Fotografar** (`capture` — quem decide é a câmera do celular) e a conferência de dossiê (só PDF, porque é o que ela confere)
- [x] **REV-07 — GEO no dossiê passa a significar o que o leitor entende**: a marca GEO vinha da posição do NAVEGADOR no instante do envio, não da foto. No teste do Dom Rafael, 14 imagens baixadas da internet foram seladas em **-22.9206, -45.4517** — o escritório de quem as enviou — e o PDF marcava GEO ao lado delas. Agora o servidor lê a coordenada de dentro da própria imagem (EXIF, Pillow); a do aparelho só entra na câmera ao vivo, onde as duas são a mesma coisa. Sem coordenada confiável, **nenhuma** — `documentos` é append-only, e o errado ficaria selado para sempre. Some junto um dado pessoal que ninguém pediu: o endereço do funcionário em todo arquivo que ele subisse
- [x] **REV-05 — Aviso ao fundador sai pela instância de marinas**, não pela transacional: a transacional entrega o código de acesso, que é autenticação — quanto menos tráfego passar por ela, menor a chance de o login cair junto com outra coisa
- [x] **REV-06 — As fotos entram no dossiê**: eram 20 imagens no PDF e **19 eram a mesma logo**. A seção "Registro Fotográfico Certificado" dizia "8 imagens seladas e geolocalizadas" e mostrava uma tabela de contagem. Agora entram todas, com data, marca de geo e prefixo do hash. **Desempenho era o risco real**: 102 s para 8 fotos, porque o PDF é montado 2× (cada foto baixava 2×) e cada download abria conexão TLS nova — 11 KB levava os mesmos 4,7 s que 803 KB. Cache + cliente compartilhado: **102 s → 11 s**
- [x] **REV-06 — Índice de Segurança para de mentir**: dizia 100% num barco que furou a proa. O cálculo olhava 8 categorias e **casco, operação e sinistros ficavam de fora** — justo onde estavam os dois registros em atenção. Agora 12 categorias, e sinistro/casco em atenção valem 0, não 50. Caiu para **86%**
- [x] **REV-06 — "Investido" separado de "cobertura"**: a apólice de R$ 2,4 mi era somada no mesmo campo de uma revisão de R$ 9.800, e a capa anunciava "R$ 2,5 mi investido no ativo" — o gasto real era **R$ 89,3 mil, inflado 27×**. Três tiles agora: investido, cobertura e **custo médio/mês (R$ 4,7 mil)**
- [x] **REV-06 — "Classificação GOLD" → "Índice de Custódia: GOLD"**: a fórmula mede abrangência de registro, nada sobre a condição do ativo — o rótulo antigo fazia o comprador ler como estado do barco, contradizendo a FAQ do próprio site ("o Atlas não inspeciona")
- [x] **REV-06 — QR com polaridade corrigida**: era dourado claro sobre navy escuro; testado com zxing **sobre o PDF real**, leitor sem detecção de inversão (ZXing/ZBar padrão, Android de fabricante, app de vistoria) **não lia**. Agora módulos escuros sobre branco e lê nos dois. Vai para papel impresso — não tem correção retroativa
- [x] **REV-06 — Card de verificação entrega o que pede**: mandava "informe o protocolo e o código" e mostrava só o código; a API exige **três** dados e a data de emissão nem era citada. Agora PROTOCOLO · CÓDIGO · EMISSÃO lado a lado
- [x] **REV-06 — Três seções novas, todas de dado já selado**: **Comprovação Fiscal** (21 documentos com hash — as notas fiscais estavam no cofre desde sempre e nunca apareciam), **Perfil de Manutenção** (preventiva × corretiva — o indicador que seguradora usa para precificar risco; o Marlin Sea é 100% preventiva) e **Vencimentos & Conformidade** (o extintor vence em 38 dias e ninguém sabia)
- [x] **REV-06 — Titular da Custódia**: o campo não existia. `proprietario_email`/`_telefone` são chave de ACESSO ao Portal, não identidade — por isso o dossiê de um ativo de alto valor não dizia de quem era o barco. Nome + documento **mascarado** (`***.456.789-**`); contato NÃO vai ao documento, que circula entre corretor, comprador e seguradora
- [x] **REV-06 — Especificações e motorização**: dez colunas existiam no banco, **nenhuma** era declarada no schema (`create_ativo` fazia `getattr` num campo inexistente — código morto que parecia vivo), nenhuma era coletada no painel e nenhuma chegava ao dossiê. Tipos conferidos contra `information_schema`: `potencia_motor` é integer e estava declarado texto
- [x] **REV-06 — Painel contava a tabela errada**: cards de Documentação e Fotos diziam "Sem registro" com 21 PDFs e 8 fotos guardados — a contagem lia só `registros`, e esses dois vivem em `documentos`
- [x] **REV-06 — Tipografia do dossiê**: +1pt em todos os estilos de corpo e entrelinha de 1,45× para 1,6×. Documento lido impresso, por quem não conhece o conteúdo
- [x] **REV-06 — Entrada manual da verificação** (`/verificar`): o dossiê impresso manda "sem câmera, acesse o endereço e informe protocolo, código e data" — e esse endereço **não existia**. `App.tsx` só declarava `/verificar/:protocolo`, e a página respondia "Link incompleto. [...] informe o protocolo" **sem um único campo para informar**. Agora há formulário com os três dados, que normaliza o que a pessoa digita (maiúscula no protocolo, minúscula no código, barra → hífen na data) e monta a mesma URL do QR. Quem lê o dossiê é perito e corretor, com papel na mão e leitor que pode não abrir
- [x] **REV-06 — Impressão digital do dossiê emitido** (`dossie_emitidos`): a assinatura do QR cobre **protocolo + data**, não o conteúdo — quem recebesse um dossiê legítimo podia editar valores, apagar o histórico de sinistros, e o QR continuaria dizendo "autêntico". A plataforma passa a registrar o **SHA-256 dos bytes de cada PDF emitido**; quem tem o documento confere o próprio hash contra o que a verificação informa. Tabela **append-only por trigger no banco** (UPDATE e DELETE recusados, nem a `service_role` passa) — testado. A página de verificação mostra a impressão digital e como conferi-la (`shasum` / `certutil`)

## Manutenção Preditiva Semanal
Rotina de verificação em [CHECKLIST-SEMANAL.md](CHECKLIST-SEMANAL.md), ordenada por criticidade — do que derruba o negócio ao que só previne problema futuro. Existe porque **o sistema falha em silêncio**: webhook que parou, e-mail que virou spam, WhatsApp que desconectou. Nada disso apita, e a marina só descobre quando já custou dinheiro ou confiança.

Para rodar: abrir uma sessão e pedir *"roda o checklist semanal"* — as consultas ao banco e aos logs são executadas e só o que estiver fora do normal é reportado. Itens marcados com 👤 dependem do fundador (EasyPanel, Stripe, celular).

## Pendências / Próximos Passos
1. **Revisar gestão de segredos** — rotação das chaves de serviço pendente (decisão do fundador). *A imutabilidade dos registros já protege contra adulteração.*
2. **Desligar o auto-deploy** do EasyPanel (push em `master` reconstrói prod sozinho) — passar para deploy manual.
3. ~~**`VERIFICACAO_SECRET` em produção**~~ — **RESOLVIDO em 23/08/2026.** Segredo forte configurado no EasyPanel e confirmado contra produção: assinatura gerada com o literal de desenvolvimento (o que está no repositório público) passou a ser **recusada com 404**, e a gerada com o segredo novo é aceita. Fabricar dossiê falso com QR que valida deixou de ser possível. **Não trocar mais**: a partir da primeira emissão real, rotacionar invalida todo QR já impresso — versionar a assinatura em vez de trocar.
4. ~~**Privacidade do bucket `media`**~~ — **RESOLVIDO.** Conferido no Supabase em 30/08/2026: `storage.buckets` reporta `media` como **privado**. O texto anterior ("hoje é público") estava desatualizado e vinha guiando decisão errada.
5. **Soft-delete de ativo** — para imutabilidade **total** (hoje DELETE de ativo apaga registros em cascata).
6. ~~**`audit_logs`**~~ — **RESOLVIDO em 23/08/2026** e conferido em 30/08: a tabela tem **184 linhas** gravadas. O insert passou a usar a chave de serviço (`get_supabase_admin`), que passa por cima do RLS mas **não** passa por cima de gatilho — `trg_audit_logs_imutavel` recusa UPDATE e DELETE. O RLS continua só com política de SELECT, e isso está certo: trilha que o navegador pode escrever é trilha forjável.
7. **Higiene de repositório** — imagens grandes (6–12 MB) e arquivos avulsos na raiz; duas cópias locais do repo (com/sem "H").
8. **Portar dossiê premium p/ produção** — o layout premium hoje está só no kit local (`dossie-exemplo/`); levar para `dossie_pdf.py` quando aprovado.
9. **Traduzir os modelos de e-mail do Supabase** — ainda em inglês ("Reset Your Password"). Marca brasileira mandando e-mail em inglês com link de senha é padrão clássico de phishing, e pesou no spam junto com o DKIM que faltava.
10. **Validar o `verifyOtp` do Portal do Proprietário** contra a Supabase real — é o único ponto do fluxo que não dá para testar sem conta de verdade.
11. ~~**Limite de 4 dossiês/ano cobrava do cliente errado**~~ — **RESOLVIDO em 31/08/2026.** A cota somava toda linha de `dossie_emitidos`, e essa tabela ganha uma linha a cada geração de PDF — inclusive as de canal `acesso_link`, gravadas **toda vez** que o destinatário reabre o link já liberado. Um comprador que abrisse o dossiê quatro vezes esgotava o ano da marina, que pagou e ficava trancada fora do próprio ativo sem ter emitido nada. E a via do link nunca consultou a cota: o terceiro seguia baixando **depois** do bloqueio, enquanto o dono não conseguia mais emitir — o limite valia só para quem paga. O conserto separa duas perguntas que a mesma contagem misturava: *quantos dossiês a marina emitiu* (cota) e *quantas vezes o PDF foi baixado* (custódia). `dossie_emitidos` continua registrando tudo, com o hash de cada entrega; a cota passa a ler emissões pelo painel mais pedidos liberados, **um por pedido**. A cobrança mudou de lugar: quem gasta é `liberar_solicitacao`, o ato em que a marina decide entregar. 8 testes em `test_cota_do_dossie.py`.
12. **Suporte humano é estratégia enquanto forem 20–40 marinas** — a Solara responde o "onde"; o fundador responde o "por quê". Automatizar o resto cedo demais deixa surdo o sinal que corrige a interface. Revisar quando a mesma pergunta chegar 20 vezes ou a resposta demorar mais de um dia.
13. ~~**`alertas.py` órfão**~~ — **REMOVIDO em 31/08/2026**, por decisão do fundador. Não saiu por estar obsoleto, e sim por estar errado de um jeito que só apareceria em produção: o varredor lia `registros` **sem filtro de marina** e mandava tudo para um endereço fixo (`yachtsatlas@gmail.com`) — vencimento de barco da marina A chegava numa caixa que não é da marina A. Os quatro endpoints estavam registrados com prefixo duplo (`/api/v1/alertas/alertas/…`), prova de que nunca foram chamados, e exigiam token de admin de plataforma, então nenhum agendador externo alcançava — e nenhum foi configurado. Saíram junto `cron_vencimentos.py` (órfão) e, de `alert_service.py`, `check_vencimentos`, `process_alerts`, `get_alert_message`, `ALERT_PERIODS` e `ALERT_EMAIL`; o módulo caiu de 198 para 78 linhas e ficou só com `send_email_alert`, que a liberação do dossiê usa de verdade. **Alerta de vencimento continua sendo boa ideia** — quando voltar, cada marina recebe o do próprio ativo, no padrão do `cron_cobranca`, que já resolve idempotência e janela. Nenhum dos 4 acessos de manutenção do fundador foi tocado.
14. ~~**Decidir o que a nota do ativo significa**~~ — **DECIDIDO em 31/08/2026:** ela mede **completude do registro**, não condição da embarcação, e por isso se chama **Índice de Custódia**. A Yachts Atlas não inspeciona barco — custodia o registro que a marina lançou, e é isso que ela pode sustentar diante de uma seguradora. O Marlin Sea interditado pontuar alto deixa de ser contradição: o **registro** dele é completo, e a **Conformidade**, exibida ao lado com denominador, é que conta o estado. Ver item 20.
15. **Marina não consegue cancelar sozinha** — não há botão no painel; hoje ela pede por e-mail/WhatsApp. Decisão consciente enquanto forem 20 marinas.
16. ~~**Opt-out da prospecção**~~ — **resolvido em 22/08/2026** (`api/v1/whatsapp.py`). Falta apenas apontar o webhook na Evolution, na instância `Marinas-Indicadas`, evento `MESSAGES_UPSERT`.
17. **Vínculo da indicação depende de digitação** — quem indica escreve o nome da própria marina em campo livre (`marina_leads.source`). O casamento com a indicante é manual, como já era no cadastro. Vira problema quando o volume passar de algumas dezenas.
18. **Scheduler de 24/48h para indicação não contatada** — proposto e adiado por ordem, não por mérito: ele precisa saber se a marina **já foi contatada**, e contato manual não registra nada hoje. Alarme que cobra por lead já resolvido é alarme que se aprende a ignorar. O estado vira automático quando o disparo funcionar (`whatsapp_status = 'enviado'`) — fazer depois do item 16.
19. ~~**Oficial não valida formato de e-mail no navegador**~~ — **JÁ ESTAVA RESOLVIDO** (commit `aa0ef12`, 25/08/2026): Oficial (`RegistroMarina`), Lançamento (`MarinaParceira`), `SejaParceiro`, `SolicitarDossie` e `Login` usam o mesmo `emailValido`. A pendência ficou aberta por falta de baixa, não por falta de conserto — conferido em 31/08.
20. ~~**Três fórmulas diferentes chamadas de "saúde"**~~ — **RESOLVIDO em 31/08/2026.** Não foram fundidas: foram **desambiguadas**. Eram três fatos legítimos e diferentes usando o mesmo nome — fundir apagaria perguntas que o produto responde. Ficou um nome para cada: **Índice de Custódia** (`asset_score_service`, ponderado 50/25/15/10) = *quão completo é o registro*; **Conformidade** (`dossie_data._prontidao`, média dos estados) = *como estão os itens registrados*; **Perfil de Manutenção** (por seção no PDF) = *programada × corretiva*. O painel já usava os dois primeiros; o dossiê imprimia **“Indicador de Saúde — Manutenção: 65% Preventiva / 35% Corretiva”**, que não é saúde nem índice — um casco perfeito atendido só na quebra pontua mal ali, e um casco comprometido com plano preventivo em dia pontua bem. O comprador lia condição da embarcação onde havia hábito de manutenção. Junto, o docstring de `_prontidao` afirmava ser *“a mesma fórmula do painel”* e não era — o comentário convidava o próximo a uniformizar duas contas distintas. 6 testes em `test_vocabulario_do_indice.py`.
21. ~~**`AssetHealthDashboard.tsx` não é renderizado em lugar nenhum**~~ — **REMOVIDO em 31/08/2026** (267 linhas, zero imports). Era a terceira conta, com um terceiro nome (*Índice de Segurança*), e cinco comentários do backend a apontavam como a referência que espelham — mandando o próximo leitor para um arquivo morto. As cinco referências passaram a apontar para o `AtivoHub`, que é o painel vivo, e o `HEALTH_BUCKETS` do `asset_score_service`, que é a fonte real das 8 categorias. O *saiba mais* do índice não se perdeu: o `AtivoHub` tem o dele, que abre o critério ao clicar na Conformidade.
22. **Classificação do serviço deveria ser exigida no painel** — hoje o dossiê imprime *"natureza não classificada em N registro(s)"*. O relatório de terceiro pediu travar a emissão; **não fazer isso** — contradiz o princípio de mostrar a lacuna com honestidade e joga o problema no suporte. Exigir na criação do registro, e deixar o dossiê contar a verdade sobre o passado.
23. **Data de captura da foto** — a legenda diz "SELADO EM" porque a única data que existe é a do upload. Ler `DateTimeOriginal` do EXIF (o `exif_service` já abre a imagem, mas lê **apenas** o bloco GPS `0x8825`) exige coluna nova em `documentos` e backfill. Enquanto não existir, o dossiê não pode afirmar quando a foto foi tirada.
24. ~~**A verificação nunca recalcula hash nenhum**~~ — **RESOLVIDO em 31/08/2026.** `fn_registro_hash_esperado` recalcula o hash de cada registro pela fórmula da sua própria `hash_versao` (v1 tem oito campos; v2 acrescenta `retifica_id` e `motivo_retificacao`), e `fn_verificar_integridade_ativo` compara com o selo gravado. **O recálculo mora no Postgres, não em Python** — a fórmula usa `dados::text` (JSONB) e `created_at::text`, cuja serialização segue regras próprias do banco; replicar em Python e errar um espaço faria os 188 registros aparecerem como adulterados. Conferido antes de escrever: **141/141 na v2 e 47/47 na v1**. Testado contra adulteração real (status trocado, JSONB alterado, título reescrito): os três detectados, e registro v1 conferido sem falso positivo. A rota devolve `integro: null` quando o recálculo não roda — nunca `false`, que acusaria quem talvez esteja limpo. Só assim a frase impressa no PDF ("a plataforma recalcula os hashes") passou a ser verdade.
25. **Vencimentos precisam de discriminador por item** — a dedup é por CAMPO, e o mesmo campo serve seis extintores e a habilitação de vários condutores. Hoje o que é substituído e estava vencido é **contado e avisado** na seção, mas não listado. A solução completa é uma chave que identifique o item (qual extintor, qual condutor).
26. **Varredura do dossiê ficou pela metade** — as lentes de *números* e *ausência/fallback* rodaram e renderam os nove achados de REV-13. Faltaram quatro: **cadeia de custódia**, **o comprador lendo o PDF**, **privacidade/LGPD no documento** e **a mesma informação em dois lugares**. Rodar quando houver folga de sessão.
27. ~~**CPF/CNPJ do proprietário em texto plano**~~ — **RESOLVIDO em 31/08/2026 por MINIMIZAÇÃO, não por criptografia.** O levantamento mostrou que o documento completo era gravado e **nunca usado**: entra pelo formulário (campo opcional) e o único consumidor — o dossiê — já o imprimia mascarado. Não havia validação, busca, cobrança nem verificação que precisasse dos dígitos escondidos. Decisão do fundador: **não guardar**. Agora o mascaramento acontece na ENTRADA (`core/pii.py`, chamado nos dois caminhos de escrita de `api/v1/ativos.py`), e o backfill mascarou os 7 existentes — **zero documentos em claro no banco**. Guardar dado pessoal sem uso é risco de vazamento sem contrapartida (LGPD art. 6º, III), e numa auditoria "não temos o dado" sustenta melhor que "o dado está protegido". Se um dia for preciso o documento inteiro, ele deve ser coletado no momento do uso, com base legal própria, e guardado cifrado — não gravado por precaução.
28. ~~**Consentimento do titular para compartilhar**~~ — **RESOLVIDO em 31/08/2026.** A plataforma já registrava **para quem** o dossiê foi, quando e para quê (`dossie_solicitacoes` + `dossie_saidas`); faltava o outro lado — o armador ter dito que pode. Trilha sem base legal responde metade da pergunta da LGPD, e é a metade que uma seguradora pede primeiro. **Onde é colhido:** uma vez, na ficha da embarcação (decisão do fundador) — pedir aprovação a cada envio mataria a promessa de velocidade, com o comprador esperando no píer. **Como é guardado:** tabela própria `ativo_consentimentos`, **append-only** (`trg_ativo_consentimentos_imutavel` recusa UPDATE e DELETE), RLS deny-all. Não foi coluna em `ativos` por dois motivos: `ativos` aceita UPDATE, e a data poderia ser alterada em silêncio; e consentimento tem história — retirar é um evento `revogado`, nunca um apagamento (LGPD art. 8º, §5º). Nome e documento do titular são **fotografados** na linha, porque barco troca de dono. O termo é versionado e gravado inteiro: a auditoria precisa saber com o que se concordou **naquela data**. **Onde a trava age:** só em `liberar_solicitacao` (409) — a marina baixar o dossiê do próprio cliente não é compartilhamento. Falha de leitura devolve `None` e **recusa** (503): recusar é reversível, entregar não é. 12 testes em `test_consentimento_do_titular.py`.

    ⚠️ **Consequência operacional:** ativos já cadastrados **não têm consentimento**, então liberar dossiê para terceiro fica bloqueado até a marina registrar a autorização na ficha da embarcação. Isso é o comportamento correto, e não um efeito colateral — mas precisa ser dito no treinamento das 20 fundadoras.

28b. ~~**O registro da saída é `best-effort` e pode não acontecer**~~ — **RESOLVIDO em 31/08/2026.** O insert em `dossie_saidas` saiu do `try/except: pass`, passou a acontecer **antes** da geração do PDF e agora **recusa a entrega** (503) se falhar: num livro-razão o registro é o produto, não efeito colateral. A escolha é conservadora de propósito — o solicitante repete em segundos; um compartilhamento sem rastro não se conserta. A tabela também ganhou gatilho append-only (`trg_dossie_saidas_imutavel`), como `dossie_emitidos` já tinha: livro-razão que aceita UPDATE ou DELETE não é livro-razão. **E um bug junto:** `_registrar_emissao` lia `sol.get("destinatario_email")`, campo que **não existe** em `dossie_solicitacoes` (lá é `solicitante_email`) — gravava `None` sempre, e a impressão digital do PDF ia ao banco sem identificar quem recebeu, justamente na via em que o documento sai do controle da marina.
29. **Isolamento por usuário, não por organização** — não existe `tenant_id`/`marina_id`; o RLS filtra por `auth.uid() = usuario_id`. Funciona hoje (uma marina = uma conta), mas quebra quando uma marina pedir três acessos, e o documento de estratégia pede `tenant_id` explicitamente para SUSEP.
30. ~~**13 tabelas com RLS sem política**~~ — **RESOLVIDO em 31/08/2026** (`migration_documenta_deny_all.sql`). As 13 têm agora `COMMENT ON TABLE` explicando que RLS sem política é **deny all** — a configuração mais restritiva possível, não a menos — e que são tabelas de backend puro, lidas só pelo servidor com chave de serviço. O auditor lê a justificativa em `\d+ tabela`. O script **varre o schema** em vez de listar nomes: tabela nova com deny-all recebe a nota mesmo que ninguém volte no arquivo. De quebra, 7 tabelas ganharam a descrição que nunca tiveram.
31. **Proteção contra senha vazada — BLOQUEADA PELO PLANO** — fica em Authentication → Attack Protection (não em Policies). Em 30/08/2026 o toggle foi ligado e o advisor continuou reportando desabilitado: a organização está no plano **Free**, e o recurso exige **Pro**. Não é impeditivo isolado — o restante da política de senha já é sólido (mínimo de 10 caracteres, exige maiúscula/minúscula/dígito, troca de senha pede sessão recente e senha atual, troca de e-mail confirma nos dois endereços). Entra junto com o upgrade, que virá antes da certificação por outro motivo: **PITR também é Pro**, e esse é exigência dura de auditoria.
32. **Email OTP expira em 1 hora (3600 s)** — o código de acesso do Portal do Proprietário fica válido por 60 minutos. A prática usual é 5 a 15 minutos; um auditor aponta. O contrapeso é operacional: encurtar significa que o armador que demora a abrir o e-mail precisa pedir outro código, e isso vira ligação para a marina. 1800 s (30 min) já melhora muito e mantém folga. **Decisão de produto do fundador.**
33. ~~**Landing carrega o app inteiro**~~ — **RESOLVIDO em 31/08/2026.** Era um arquivo único de **853 KB** sem `React.lazy` em rota nenhuma. Duas mudanças: (1) as 28 rotas passaram a carregar sob demanda — só a `LandingPage` ficou estática, de propósito, porque é a rota de entrada e `lazy` nela trocaria peso por um round-trip antes do primeiro pixel; (2) o `AuthProvider`, que envolve a aplicação inteira, passou a importar o Supabase **dentro do `useEffect`** — antes o cliente de banco entrava no chunk de toda visita, inclusive de quem só ia ler a landing ou conferir um QR. **853 KB → 278 KB de entrada, 67% menos.** Verificado no navegador: `/app` sem sessão vai direto para `/login` e fica lá (14 amostras em 3 s, zero oscilação) — o risco do import dinâmico era exatamente o painel piscar como deslogado, e não acontece porque a checagem de sessão já era assíncrona e o `loading` já segurava.
34. **Curadoria do registro fotográfico** — panfleto de fornecedor e arte promocional com texto sobreposto entram no dossiê hoje. Cada foto sai com data, GEO e hash: o selo afirma *"isto é evidência"*, e quando aparece embaixo de um folder ele deixa de valer para **todas** as fotos. Fazer a parte barata (diretriz no upload + campo dizendo o que a foto é); **não** tentar detecção automática agora — o erro caro é o inverso, barrar a foto legítima do casco às 18h de sexta.
35. ~~**Menu do cabeçalho colidia em tablet**~~ — **RESOLVIDO em 31/08/2026.** O menu completo abria a partir de `md` (768px), mas tem cinco links com 40px entre eles, mais três botões de região, mais o botão do cofre — não cabia, e "PORTAL DO PROPRIETÁRIO" passava **por baixo** de "ACESSAR COFRE": dois elementos clicáveis sobrepostos, no cabeçalho. Corte movido para `lg` (1024px); de 768 a 1023 entra o menu recolhido, que já trazia os mesmos cinco links, as três regiões e o cofre. O painel do menu também estava em `md:hidden` e foi junto — sem isso o botão apareceria e o painel não abriria. Medido: **zero pares sobrepostos** em 768px e 1440px.

36. ~~**Fila vazia custava 1.400 consultas por dia**~~ — **RESOLVIDO em 31/08/2026**, achado no log de produção que o fundador colou. A agenda de prospecção consultava o Supabase no intervalo fixo (60s por variável de ambiente, herdada do ensaio de 25/08) mesmo com a fila vazia — horas seguidas devolvendo `{'enviados': 0, …}`. Agora a espera **dobra a cada volta vazia** até um teto (`PROSPECCAO_INTERVALO_OCIOSO_SEGUNDOS`, 600s) e volta ao ritmo normal assim que aparece lead. Não atrasa ninguém de forma relevante: o lead só fica elegível depois da carência, e o pior caso é carência + teto. Junto, o `prospeccao_service` registrava o resumo em INFO **incondicional**, anulando o silêncio que o `agenda.py` já pretendia no próprio comentário — passou a INFO só quando houve envio, falha ou bloqueio, e DEBUG no resto. 9 testes em `test_recuo_da_prospeccao.py`.

37. **Produção está sem cache** — `REDIS_URL não definido — cache desativado` em toda subida. Não é erro, e com 8 ativos não se nota; passa a doer quando as 20 fundadoras estiverem consultando painel e dossiê ao mesmo tempo. Decidir se entra Redis ou se o cache sai do código — hoje há a infraestrutura de um recurso que nunca é usado.

38. **`supervisord` roda como root** — `Supervisor is running as root. Privileges were not dropped because no user is specified in the config file.` Um processo comprometido dentro do contêiner teria root. Corrigir antes de a plataforma ter dado de marinas reais dentro: basta `user=` no `supervisord.conf` e um usuário não privilegiado no Dockerfile. Item de segurança, não de funcionalidade — não bloqueia o lançamento, mas é o tipo de coisa que uma auditoria de seguradora pergunta.

39. ~~**Duas funções novas sem `search_path`, e uma vazando entre marinas**~~ — **RESOLVIDO em 31/08/2026**, achado ao rodar o linter de segurança do Supabase quando o fundador perguntou se o sistema estava pronto para auditoria. Dos 5 WARN, **dois eram do mesmo dia**: `fn_consentimento_vigente` e `fn_ativo_consentimentos_imutavel` nasceram sem `search_path` fixo, sendo que **toda** função anterior do projeto já usava `search_path=""` — padrão estabelecido que não foi seguido. O terceiro era mais sério: `fn_verificar_integridade_ativo` é `SECURITY DEFINER` (de propósito, para ler `registros` apesar do RLS) e tinha EXECUTE concedido a `authenticated` — **qualquer marina logada podia chamar `/rest/v1/rpc/…` com o ID de um ativo de outra marina** e receber quantos registros conferem, quantos divergem e se a cadeia está íntegra. Não expõe conteúdo, mas confirma a existência do ativo e revela o estado da custódia alheia. Revogado de `authenticated`, `anon` e `public`; o backend usa a chave de serviço, que ignora grant, então a página pública do QR e o painel não foram afetados (conferido: a função segue devolvendo 16/16 conferem para o Marlin Sea). Migrações salvas em `migration_endurece_funcoes.sql` e `migration_consentimento_do_titular.sql` — esta última **não tinha sido salva no repositório**, só aplicada no banco. Linter: de 5 WARN para 2.

40. ~~**Os 14 `rls_enabled_no_policy` do linter precisam de explicação escrita**~~ — **RESOLVIDO em 31/08/2026**: `conformidade/03-nota-tecnica-rls-deny-all.md`. Não são defeito, e sim a configuração mais restritiva possível — RLS ligada sem política nega tudo para `anon` e `authenticated`, que são justamente os papéis alcançáveis pela API pública. O documento explica as duas razões do desenho (a autorização real é mais rica que uma política SQL; e **um único caminho de entrada é auditável, dois não são**), lista as 14 tabelas com o motivo de cada uma, dá as duas consultas para o auditor conferir sem acreditar no texto, e é honesto sobre o que a configuração **não** resolve.

41. **Prazo de retenção não definido** — não existe prazo declarado nem rotina de expurgo em lugar nenhum (verificado em 31/08/2026: as únicas referências a tempo de vida no código são caches técnicos). Três perguntas precisam de resposta **do fundador**: (a) marina que cancela — por quanto tempo o histórico custodiado permanece? Há tensão real: a promessa do produto é permanência, e apagar destruiria o valor que a marina pagou para constituir, mas *"para sempre"* também não se sustenta perante a ANPD sem justificativa; (b) lead comercial nunca convertido; (c) `audit_logs` — finalidade de segurança tem prazo. Seção 6 do registro de operações está marcada `[A DEFINIR]` até isso ser respondido.

42. **Encarregado (DPO) não designado** — a LGPD (art. 41) exige que a identidade seja **divulgada publicamente**, então o nome e o e-mail escolhidos aparecerão na página de privacidade. Decisão do fundador. Seção 8 do registro de operações está marcada `[A DEFINIR]`.

## Contra-prova de Autenticidade

**A versão gratuita está no ar** em `/conferir`: qualquer pessoa arrasta o PDF e descobre se ele corresponde a um dossiê emitido. O **arquivo não sai do computador** — o navegador calcula o SHA-256 (Web Crypto) e envia só os 64 caracteres. Ninguém deveria precisar entregar um documento sigiloso a um terceiro para descobrir se ele é legítimo.

`dossie_emitidos` guarda o SHA-256 de cada emissão, append-only por trigger no banco.

- **Gratuita (feita)** — sobe o PDF, recebe "autêntico / não corresponde". É a melhor propaganda que o Atlas pode ter: o corretor entende o produto inteiro em dois segundos, sem explicação. E o efeito antifraude vem da **existência** do serviço, não do preço — ninguém adultera documento que pode ser conferido.
- **Paga (depois)** — **Laudo de Autenticidade** em PDF, assinado, para quem precisa *provar a terceiro*: seguradora em análise de sinistro, advogado em disputa, comprador desconfiado. Custo marginal quase zero (é consulta a hash), em momento de alta urgência e alto valor.

**Preço de referência (a confirmar quando houver volume): US$ 40 por laudo · US$ 300 no pacote de 10** (US$ 30 cada, para seguradora e corretora que verificam com frequência).

Ancorado nos preços do próprio produto — dossiê de entrada US$ 100, adicional US$ 150 — o laudo é serviço EM CIMA do dossiê e não pode chegar perto dele, senão parece cobrança em duplicata. Abaixo de US$ 20 perde credibilidade: num documento destinado a seguradora ou processo, preço baixo demais faz duvidar do peso dele. Acima de US$ 50 sai da faixa de decisão imediata e vira algo que se pensa, compara e adia — o oposto do que se quer num momento de urgência. Número redondo, não US$ 39,90: a marca é institucional e linguagem de varejo destoa de um laudo com CNPJ e selo SHA-256.

A consulta gratuita NUNCA é cobrada. O valor dela é ser grátis e sem atrito — é ela que espalha o produto e faz o efeito antifraude funcionar.

Ordem recomendada: gratuita primeiro (**feita**). Serviço pago sem base de documentos emitidos não tem o que verificar — hoje o laudo teria pouquíssimo o que atestar.

---

## Expansão Internacional (3 Versões)
Estratégia multi-região pensada **desde a arquitetura**: o mesmo DNA (custódia selada + dossiê imutável + SHA-256) replicado em **3 sistemas independentes**, cada um com idioma, banco, subdomínio e conformidade regulatória próprios. As **portas de entrada** já vivem no header (botões dourados `Latan-Atlas · USA-Atlas · Europa-Atlas`), hoje como placeholders visuais a partir da constante `REGIOES` (`Header.tsx`).

| Versão | Mercado | Idioma | Subdomínio | Banco (Supabase) | Normas / Conformidade | Repositório |
|---|---|---|---|---|---|---|
| **Latan-Atlas** | América Latina | Espanhol (LatAm) | próprio | novo (isolado) | normas do continente (por país) | separado |
| **USA-Atlas** | Estados Unidos | Inglês americano | próprio | novo (isolado) | USCG / ABYC / NMMA | separado |
| **Europa-Atlas** | Europa | Inglês britânico | próprio | novo (isolado) | RCD (2013/53/UE) / ISO | separado |

**Faseamento:**
1. Concluir o deploy e a validação da versão BR (`master` → produção).
2. Cada versão nasce em **repositório SEPARADO** (não misturar com o app principal), com **banco Supabase próprio**, **subdomínio dedicado** e tradução do RAG/normas (Capitã Solara) para a localidade.
3. Aplicar a **conformidade regulatória de cada continente** no corpus de normas e nos textos legais do dossiê.
4. Ligar cada botão do header ao seu subdomínio de destino.

> Princípio: reaproveitar o núcleo (painel config-driven + imutabilidade + dossiê PDF) e trocar apenas a camada de idioma, dados e conformidade por região.

### A trilha de auditoria nunca gravou (23/08/2026)

`audit_logs` tinha **0 linhas desde a criação**. Não quebrou — nunca funcionou. Três defeitos empilhados:

1. **O serviço usava a chave anônima.** A tabela tem RLS ligado e **só políticas de SELECT** — nenhuma de INSERT. Toda gravação voltava `42501` e era engolida pelo `except` (correto: auditoria falhando não pode derrubar o acesso de uma marina; o efeito, porém, foi silêncio total).
2. **`user_id` é `uuid`, e 11 pontos do código mandavam texto** — `system`, `anonymous`, `maintenance-admin`, `unknown`. Mesmo com o cliente certo, essas chamadas morreriam em `invalid input syntax for type uuid`.
3. **A tabela não era append-only.** `registros`, `documentos` e `dossie_emitidos` têm gatilho; `audit_logs` não tinha.

Corrigido: cliente de serviço + ator textual preservado em `metadata.ator` (com `user_id` nulo) + gatilho `trg_audit_logs_imutavel` recusando UPDATE e DELETE.

**A ausência de política de INSERT ficou como está, de propósito.** Cliente nenhum deve escrever aqui — se o navegador pudesse inserir, qualquer um forjaria "fulano acessou o dossiê tal", e trilha forjável não é prova. Quem escreve é o backend, com a chave de serviço, que passa por cima do RLS mas **não** passa por cima de gatilho.

> Por que importa comercialmente: a trilha é a resposta a *"quem abriu este dossiê, quando, de qual IP"* — a pergunta que uma seguradora faz. É o lastro do **Laudo de Autenticidade (US$ 40)**.

### Cofre privado — o balde `media` (23/08/2026)

O balde `media` do Supabase Storage estava **público**: 51 arquivos, 10 MB, incluindo documento de cliente (nota fiscal, apólice, laudo). Qualquer pessoa com o endereço baixava **sem autenticar**.

A correção não é só virar a chave do balde — as URLs públicas estão gravadas em `documentos.url_arquivo` e quebrariam junto. O desenho:

| Onde | Antes | Depois |
|---|---|---|
| Listagem de documentos (painel + portal do armador) | `url_arquivo` gravada | link **assinado na leitura** |
| Documento único | `url_arquivo` gravada | link assinado |
| Fotos do dossiê (PDF) | `url_arquivo` gravada | link assinado em lote |
| Download pelo painel | já era assinado | inalterado |

**Assinar na leitura e não regravar o banco**, por três razões: `storage_path` existe em 100% dos documentos e `url_arquivo` só em parte (36 de 68); link assinado vence, e gravá-lo no banco seria guardar algo que expira num lugar que não expira; e o frontend lê `url_arquivo` em quatro telas — mantendo o nome do campo, ele não muda uma linha.

Validade do link: **8 horas** — cobre uma jornada de trabalho sem recarregar a página, e mesmo assim morre no mesmo dia. Link assinado vazado expõe **um arquivo**; o balde público expõe todos.

**FECHADO em 23/08/2026**, na ordem: código em produção → conferido com o balde ainda aberto (painel servindo `/object/sign/`) → balde fechado → conferido de novo.

| | Antes | Depois |
|---|---|---|
| Baixar documento de cliente sem autenticação | `HTTP 200` | `HTTP 400 NoSuchBucket` |
| Dossiê: fotos montadas | 8, URL pública | 8, todas assinadas, todas baixam |
| Alcance de um link vazado | o balde inteiro | um arquivo, por 8 horas |

Resíduo conhecido: o Smart CDN da Cloudflare continua servindo cópias já em cache dos arquivos que haviam sido buscados publicamente antes (`CF-Cache-Status: HIT`). Não é exposição nova — são os mesmos endereços que já estavam abertos — e envelhece sozinho. Requisição com parâmetro novo (cache miss) já vai à origem e recebe 400.

**Ordem obrigatória:** o código vai a produção **primeiro**, o balde fecha **depois**. Invertido, o painel para de mostrar documento e o dossiê sai sem foto no instante da mudança.

Sem fallback: `get_presigned_url` não cai mais para URL pública quando a assinatura falha. Com o balde privado, esse fallback devolveria um endereço que responde 400 — um link que parece bom e não abre, descoberto na frente do comprador ou do perito.

### Registro Fotográfico — molduras vazias removidas (23/08/2026)

A seção 15 abria com uma grade de molduras: selo "SELADA SHA-256" em cima, nome da categoria embaixo, **24 mm de vazio no meio**. Eram lugar reservado da época em que o PDF não mostrava imagem alguma. Com as fotos saindo de verdade desde 22/08, viraram um terço de página de caixa vazia repetindo a tabela de contagem que já existia na mesma seção.

Removidas. A tabela `Categoria | Imagens` passou para **antes** da galeria (resumo primeiro, imagens depois) — sozinha no fim, ela ocupava uma página inteira para quatro linhas.

**Resolvido no mesmo dia — capacidade fotográfica passou de 430 para 460.** Existia foto gravada como `galeria_seguranca` sem a categoria existir na configuração: o painel a jogava em "Outros", o dossiê imprimia "Seguranca" sem cedilha. Com o aval do fundador, **`Segurança & Salvatagem` virou a 10ª categoria** (mínimo 30) — salvatagem é item que seguradora e perito olham primeiro.

O número **público das páginas continua 430**, por decisão do fundador: *"a mais não tem problema, menos é ruim"*. Prometer 430 e entregar 460 é seguro; o inverso não seria.

O 430 vivia em **quatro** lugares, e essa duplicação foi a causa raiz:

| Fonte | Antes | Agora |
|---|---|---|
| `config/coberturaFotos.ts` | `COBERTURA_CATS` + `MAX_FOTOS` | **fonte única** |
| `pages/Ativos.tsx` | lista e número **duplicados** | importa da config |
| `services/dossie_data.py` | espelho manual | `MAX_FOTOS = 460` |
| `conhecimento_produto.json` (Solara) | gerado do front | regenerado |

O último só apareceu porque `test_conhecimento_esta_em_dia_com_o_codigo` quebrou. Sem esse teste, a Capitã Solara ensinaria "430 fotos" às marinas enquanto o painel oferecia 460 — com convicção e sem ninguém perceber.

### Verificação pública — hora da emissão (23/08/2026)

Reemissão é legítima (o dossiê é atualizado a cada novo registro selado) e cada via tem hash próprio. A página do QR listava todas — mas só com a data, então três vias do mesmo dia apareciam como três linhas idênticas. O portador sabia apenas que "uma das três deveria bater".

A lista mostra as **5 vias mais recentes**. Passando disso, a página avisa quantas existem ao todo e aponta para a conferência automática — que **não tem esse limite**: `/verificar/documento/{hash}` busca a impressão digital em todas as emissões. Sem esse aviso, o portador de uma via antiga não encontraria a dele na lista e concluiria que o documento é falso, que é o oposto do que a verificação existe para fazer.

Passou a mostrar `DD/MM/AAAA · HH:MM`, com a hora vinda de `created_at`. **Nunca de `emitido_em`**: aquele é o campo coberto pela assinatura HMAC do QR (`protocolo + data de emissão`), e mexer nele invalidaria todo QR já impresso. Fuso fixo `-03:00` em vez de `ZoneInfo`, que depende de `tzdata` e pode faltar fora do contêiner.

### Cadeia de custódia fechada — imutabilidade nas tabelas de registro (24/08/2026)

Cinco tabelas registravam fato e não tinham proteção nenhuma. A mais grave: **`dossie_saidas`**, que guarda **quem recebeu o dossiê de um cliente** (nome, e-mail, finalidade, IP, quando). Todo o resto da cadeia era imutável e essa ponta ficava solta — justamente a que responde *"para quem foi"*, que numa disputa é a pergunta mais cara.

Aplicado em duas camadas, com gatilho (não RLS: **a chave de serviço passa por cima de RLS e não passa por cima de gatilho**):

| Nível | Tabelas | Por quê |
|---|---|---|
| **append-only** (UPDATE + DELETE) | `dossie_saidas`, `integridade_logs` | o fato não muda depois de registrado — uma entrega aconteceu, não se desfaz |
| **só DELETE bloqueado** | `payments`, `subscriptions`, `lgpd_solicitacoes`, `dossie_solicitacoes` | têm ciclo de vida legítimo (pendente → atendida/liberada) ou dependem do webhook do Stripe, que é território de terceiro |

Sobre `payments`/`subscriptions`: hoje o código só faz INSERT e SELECT nelas, conferido. Ainda assim ficou só o bloqueio de DELETE — travar UPDATE às vésperas de um teste de pagamento real trocaria uma garantia por um risco. O que importa (pagamento não pode ser apagado) está garantido; a trava de UPDATE pode vir depois que o ensaio mostrar o que o webhook faz de verdade.

Todas estavam com **zero linhas** no momento da migração — nenhum dado existente correu risco.

**Estado completo da cadeia:** `registros`, `dossie_emitidos`, `audit_logs`, `dossie_saidas`, `integridade_logs` com UPDATE+DELETE bloqueados; `documentos` e as quatro acima com DELETE bloqueado. As demais tabelas (leads, brokers, profiles, normas, rascunhos) são mutáveis por natureza — travá-las seria errado.

### Limite de taxa nas rotas públicas (24/08/2026)

Sete rotas aceitavam POST sem autenticação e **sem limite nenhum**. A mais séria não era spam: `POST /dossie/acesso/{id}` confere a **senha-mestra** e devolve o PDF de um cliente — dava para tentar senha indefinidamente até acertar, sem barreira e sem rastro.

O checklist do piloto apontava "5 policies de INSERT abertas". **Estava errado:** as policies estão corretas (as de `brokers`/`broker_deals`/`insurance_companies` exigem `user_role = 'admin'`; as de `ativos`/`documentos`/`registros` exigem `auth.uid()`; as tabelas de formulário público não têm policy de propósito — só o backend escreve). O buraco era uma camada acima, na API.

Pior: o único limitador que existia, o do chatbot, começava com `if redis is None: return True` — e produção **nunca teve `REDIS_URL`**. Um limitador que se desliga quando a dependência opcional falta é um limitador que não existe justamente no dia em que a dependência cai.

`app/core/limite_taxa.py` — janela deslizante, **Redis quando houver, memória do processo sempre**:

| Rota | Teto | Por quê |
|---|---|---|
| `POST /dossie/acesso/{id}` | **5 / 15 min**, por IP **e** por solicitação | senha-mestra; `por_rota` impede diluir tentativas trocando de link |
| `POST /leads/marina/registrar` | 3 / min | cadastro cria conta |
| `/leads/marina`, `/leads/parceiro`, `/dossie/solicitar`, `/lgpd/solicitacoes` | 5 / min | formulários |
| `POST /parceiros/clique` | 30 / min | volume legítimo alto |
| `POST /auth/login` | **20 / 15 min** | força bruta na senha de quem guarda documento de cliente |
| `POST /auth/maintenance/login` | **5 / 15 min** | a porta de administrador da plataforma |
| `POST /auth/signup` | **3 / hora** | criar conta é evento raro por IP |

As três de `auth` ficaram de fora na primeira passada — o módulo de autenticação não foi varrido junto com os formulários públicos, e são justamente as mais graves. Corrigido em 24/08/2026, no mesmo dia.

Detalhes que importam: o IP vem do `X-Forwarded-For` (atrás do nginx, `request.client.host` é sempre o IP interno — o limitador trataria o mundo como um visitante só e bloquearia todos ao primeiro abuso); há teto de chaves em memória (atacante variando IP não pode virar vazamento); e Redis caindo **cai na memória**, nunca abre o portão.

Junto: **senha-mestra incorreta agora vira linha em `audit_logs`**. O limite *barra* a força bruta; a trilha é o que a torna *visível* — sem ela, mil tentativas e nenhuma tentativa têm a mesma aparência depois do fato.

Coberto por `tests/test_limite_taxa.py` (8 testes), incluindo o caso que originou tudo: **sem Redis, ainda limita**.

### WhatsApp: `+55` fixo fora do campo (24/08/2026)

O `5555978138934` gravado em 23/08 não era bug de código — era ambiguidade real. `55978138934` (DDI sem DDD) é **indistinguível** de um número legítimo do DDD 55 (Santa Maria/RS). Nenhum algoritmo resolve isso.

A correção é de interface, não de backend: o **`+55` virou rótulo fixo ao lado do campo**, e a marina digita só DDD + número, com máscara `(12) 97813-8934`.

| | |
|---|---|
| Colou `+55 12 97813-8934` | o `55` da frente é removido — senão viraria `+55 55 …` |
| Digitou `12978138934` | vira `(12) 97813-8934` |
| **Digitou `55978138934`** | mostra **`(55)`** na tela — quem quis DDD 12 vê e corrige |
| Incompleto (`12978`) | **recusado** com mensagem própria |

O terceiro caso é o ponto: a ambiguidade não desaparece por algoritmo, ela passa a ser **visível para quem sabe a resposta**. Antes o campo mostrava o que foi digitado e a corrupção acontecia no servidor, muda.

O envio manda `55` + dígitos (13 no total) — a única forma que o backend aceita sem inferir nada.

Aplicado nas duas páginas: `MarinaParceira.tsx` (Oficial) e os **dois** campos do Lançamento (cadastro de fundadora e indicação). Nos dois formulários do Lançamento havia um furo extra: a validação só checava campo *preenchido*, e `(12) 978` está preenchido — passaria e seria enviado vazio. Agora exige completude.

Verificado em navegador real (DOM, evento `input`, quatro casos), não só em teste de unidade.

### Higiene do repositório — o que o checklist do piloto errou (24/08/2026)

Três itens do `CHECKLIST-PILOTO-3-MARINAS.md` foram reabertos e **dois já estavam resolvidos**:

| Item do checklist | Realidade conferida |
|---|---|
| "5 policies de INSERT abertas" | ❌ **errado** — as policies estão corretas; o buraco era falta de limite de taxa na API |
| "Automatizar build do frontend antes do deploy" | ✅ **já feito** — o Dockerfile tem estágio `frontend-builder` com `npm run build`, que começa com `tsc`: erro de tipo derruba o deploy |
| "Higiene de repositório — DUAS cópias" | ⚠️ real, mas inofensiva — ver abaixo |

**Verificado no que está publicado**, não no que se supõe: o bundle em produção (`/assets/index-*.js`) embute `sb_publishable_…` — formato novo, seguro para ser público. Nenhum JWT legado viaja no frontend.

**A pasta duplicada** `C:\YACHTS-ATLAS-OFICIAL` (com H antes do T) está 2 meses atrás (último commit 25/06), sem `.env`, e **não tem nenhum commit que a viva não tenha**. As duas únicas alterações não commitadas eram um `dist/index.html` com diferença só de fim de linha e a exclusão de um `public/sitemap.xml` que virou obsoleto quando o `prerender.mjs` passou a gerar o sitemap no build. Nada a salvar.

**Resíduo encontrado no caminho:** três artefatos de build estavam **versionados** em `frontend/dist/` — commitados antes da regra `dist/` entrar no `.gitignore`, e `.gitignore` não desrastreia o que já está rastreado. Todos existem em `public/`, ninguém referencia `dist/`, e o Docker constrói do zero. Desrastreados.

### Política de senha — uma regra, três lugares (24/08/2026)

A regra da senha vivia em **três versões diferentes**, e nenhuma delas conversava com as outras:

| Onde | Exigia |
|---|---|
| Supabase Auth (servidor) | 6 caracteres, sem exigência de composição |
| `RegistroMarina.tsx` (Oficial) | 6 caracteres |
| `index.html` (Lançamento) | 8 caracteres |

Endurecida no Supabase para **mínimo 10 · minúscula · maiúscula · dígito**, mais "exigir senha atual ao trocar" e "troca só com login recente". A proteção contra senha vazada (HaveIBeenPwned) **não foi ligada — é exclusiva do plano Pro**.

Endurecer só o servidor criaria o pior dos mundos: a marina digita algo que a tela aceita e o servidor recusa com erro genérico, sem dizer qual campo. As duas páginas foram alinhadas à mesma regra, e passaram a **mostrar os requisitos marcando sozinhos** enquanto a pessoa digita.

Isso importa mais no Lançamento: lá o cadastro acontece **a um passo do pagamento**, e senha recusada nesse ponto é venda perdida, não suporte.

Em ambas, a regra é uma constante única no topo do arquivo (`SENHA_MINIMO` / `REGRAS_SENHA`) e o texto da tela deriva dela — mudar a regra no Supabase exige mudar um lugar por página, e a interface acompanha.

### Prospecção automática das marinas indicadas (24/08/2026)

A mensagem de abordagem existia, o envio existia, o opt-out existia — e **nada disparava**. `disparar_lote()` só era alcançável rodando o módulo como script; a `agenda.py` cuidava de cobrança e do aviso ao fundador, e nunca de prospecção. Por isso a marina indicada nunca recebia nada.

Ligado agora, com **três travas em variável de ambiente** (mudar não exige deploy):

| Variável | Padrão | O que faz |
|---|---|---|
| `PROSPECCAO_AUTOMATICA` | **`false`** | interruptor geral. Desligada, os leads ficam na fila e ninguém é abordado |
| `PROSPECCAO_CARENCIA_MINUTOS` | `30` | espera entre a indicação e a mensagem |
| `PROSPECCAO_INTERVALO_SEGUNDOS` | `180` | de quanto em quanto a agenda olha a fila |

**Por que começa desligada:** é a única rotina do sistema que fala com alguém que nunca pediu contato. Um deploy não pode começar a abordar gente por conta própria, e desligar tem de ser imediato — sem esperar build.

**A carência não é atraso técnico, é a janela de cancelamento.** Lead errado que entrar (número inválido, teste, marina que não devia ser abordada) pode sair da fila antes de virar mensagem. Mensagem enviada não volta; lead na fila, sim. Em 24/08/2026 havia **sete leads de teste em fila**, um deles apontando para `5555978138934` — um número no RS que ninguém digitou. Todos marcados como `teste_nao_enviar`.

Laço **separado** do da cobrança, de propósito: cadências diferentes (dias × minutos) e falha numa não pode calar a outra — cobrança parada é dinheiro que não entra, prospecção parada é venda que não acontece.

Duas rotas administrativas acompanham: `GET /leads/prospeccao/fila` (quem está na fila, e por que os outros não estão) e `POST /leads/prospeccao/disparar` — esta **em ensaio por padrão**, só `?enviar=true` fala com gente de verdade.

### O e-mail pós-pagamento (24/08/2026)

O e-mail de boas-vindas é a **primeira coisa que a marina recebe depois de pôr o cartão**, e por muito tempo é a única: `_handle_invoice_paid` (renovação) não envia nada. Quem paga US$ 250/mês por doze meses recebia **um e-mail no ano inteiro**.

Ele chegava sem o nome de quem pagou — *"Olá, bem-vindo à Atlas"*. O nome vinha do metadata do Payment Link, e Payment Link é URL fixa: não carrega metadata por cliente. O dado nunca faltou, faltava olhar onde estava. Agora vem em três degraus:

| Ordem | Fonte | Por quê |
|---|---|---|
| 1º | **cadastro** (`user_metadata.marina`) | onde a marina digitou o próprio nome; único que vale por cliente |
| 2º | metadata do link | é o MESMO para todo mundo que paga por ali — rede, não primeira escolha |
| 3º | titular do checkout | pode ser a pessoa e não a marina, mas é melhor que "Olá" pelado |

**O texto é NEUTRO quanto à oferta — um só serve o Lançamento e a Oficial.**

Chegou a descrever a oferta contratada (preço, prazo travado, meses de dossiê), com a ideia de servir de comprovante do acordo no 13º mês. Foi desfeito no mesmo dia, e a razão vale mais que a economia de código: para escrever a oferta, o e-mail teria de **adivinhar qual das duas foi vendida**. O metadata `programa` vem vazio nos Payment Links, então sobrava o valor pago como pista.

Inferência que erra aqui não deixa o texto vago — deixa o texto **errado, por escrito, no primeiro contato depois do cartão**. Uma fundadora lida como oficial receberia "dossiê 12 meses" tendo comprado 18. Não afirmar é melhor que afirmar errado.

O contrato vive no cadastro e no painel, que sabem a resposta. O e-mail confirma o pagamento e entrega o acesso — que é o que ele tem como saber sozinho.

Os prazos de dossiê das duas ofertas ficaram no `config.py` mesmo sem leitor (`LAUNCH_DOSSIER_BONUS_MONTHS`, `TRADITIONAL_DOSSIER_MONTHS`): o modelo de cobrança fica escrito inteiro ao lado dos preços, em vez de metade no código e metade nos documentos — que era o caso do prazo da oficial.

**Saiu a promessa de recibo.** O rodapé dizia *"o recibo é enviado separadamente pela nossa processadora"*, e o envio automático de recibo estava **desligado** na Stripe. Prometia o que não controlava. Trocado por *"Guarde este e-mail: ele é o registro do que foi contratado"* — e o recibo foi ligado no painel, junto com o de reembolsos.

### A conta Stripe é da Axos Hub, e o webhook é por conta (24/08/2026)

Endpoint de webhook assina **tipos de evento**, não produtos. A conta vende mais de um produto da casa, e o `POST /webhook` do Atlas recebe os eventos de todos eles. Duas travas nasceram daí:

**1. Saudação sem acesso.** A linha que libera o acesso exigia `user_id`; a que mandava o e-mail, não. Cliente de outro produto recebia *"Bem-vindo ao Yachts Atlas — seu acesso está liberado ⚓"*, com botão para um login que não é dele. Agora as duas exigem o mesmo: sem usuário no Atlas, não há acesso liberado e não há o que saudar.

**2. O portão dos US$ 200 ignorava a moeda.** `valor_pago == 200` é verdadeiro para **R$ 200,00** também — preço comum no Brasil. Qualquer produto da casa cobrado nesse valor cairia no reconhecimento de marina fundadora. A moeda entrou na comparação (`PRICE_CURRENCY`). O metadata `programa` continua valendo sozinho: ali a intenção foi **declarada**, não inferida.

### O que a marina vê depois de clicar em pagar (24/08/2026)

Ela sai do site para a Stripe e não volta. O aviso da etapa 4 do cadastro passou a dizer o que esperar:

> Após o pagamento, você recebe um **e-mail de confirmação** e seu acesso é liberado imediatamente.

Fica junto do que já estava ali (o vídeo e as 3 horas de reserva), no mesmo bloco — não em outro lugar da tela.

O **mesmo texto** entrou na LP de Lançamento, que vive em repositório separado (`C:\LANCAMENTO_YACHTS-ATLAS-PROMOCAO`, commit `e359c35`). Lá importa mais: o cadastro fica a um passo do pagamento. A regra de senha já se dividiu assim uma vez (6 aqui, 8 lá, 10 no servidor) — texto de pagamento vai nos dois, sempre.

### A prospecção funcionava; o ensaio é que estava contaminado (25/08/2026)

Três dias caçando defeito no disparo da mensagem para a marina indicada, e não havia defeito.

O número que faz papel de cliente em todos os ensaios (`5512991187251`) respondeu **SAIR** no teste de opt-out de 23/08 e entrou na `whatsapp_blocklist`. De lá em diante, **toda** indicação para esse número foi marcada `bloqueado` e nenhuma mensagem saiu. Comportamento correto — e silencioso, porque respeitar opt-out não é falha: não gera erro, não gera alerta, não deixa rastro que pareça problema.

A prova foi feita sem tocar em código. Removida a linha da blocklist e o lead devolvido a `pendente`, a mensagem saiu no primeiro ciclo do laço:

```
Marina Porto Feliz · 5512991187251
whatsapp_status = enviado · 25/08/2026 06:13:54 BRT · whatsapp_erro: nenhum
```

De passagem ficou provado que **`PROSPECCAO_AUTOMATICA` já está ligada em produção**: quem escreve `bloqueado` é o próprio `disparar_lote`, então o laço estava rodando o tempo todo. O que faltava não era o gatilho — era o número estar livre.

**Ordem de diagnóstico quando a mensagem não chegar** — dez segundos, antes de abrir qualquer código:

```sql
select * from public.whatsapp_blocklist;                                  -- alguém pediu SAIR?
select marina_name, whatsapp_status, whatsapp_erro from public.marina_leads;
```

`bloqueado` = opt-out respeitado · `teste_nao_enviar` = tirado da fila de propósito · `falhou` = aí sim há defeito, e o motivo está em `whatsapp_erro`.

**Lição de ensaio, não de código:** testar opt-out com o mesmo número que faz papel de cliente envenena todos os testes seguintes, e o sistema não tem como avisar — ele está fazendo o certo. Opt-out precisa de número descartável, ou a blocklist tem de ser limpa logo depois.

**O buraco que sobrou:** o webhook de resposta só age em "SAIR" (`if not _quer_sair(texto): return`). Marina que responder *"quanto custa?"* fala com a parede — a mensagem não vai a lugar nenhum e ninguém é avisado. É o único ponto onde um agente conversacional (ATLAS-SHOP / Vega) tem trabalho real; o primeiro toque não precisa dele.

### O campo obrigatório que não era obrigatório (25/08/2026)

Uma marina concluiu o cadastro, pagou e ficou com **`telefone` gravado vazio**. O telefone é por onde ela é atendida, recebe o código de acesso do armador e é abordada na prospecção. Nada reclamou.

O `input` do telefone tem `required`. O que não estava à vista:

```
input phone   vive dentro de  {step === 1 && (...)}
                              ↓
etapa 4       onde fica o botão de enviar, o campo NÃO existe mais no DOM
                              ↓
required      não valida o que não está na página — o atributo estava inerte
handleSubmit  só conferia a senha
```

Formulário em etapas com renderização condicional **desliga o `required` do navegador** sem avisar. A validação tem de estar no `handleSubmit`, não no atributo.

**A regra do telefone virou `utils/telefone.ts`, e some de dentro das páginas.** Ela já existia — `+55` como rótulo fixo, máscara, recusa de incompleto — e foi aplicada em 24/08 na `MarinaParceira` e na LP de Lançamento. Não chegou ao `RegistroMarina`, que é justamente **a página do cadastro pago**. É a terceira vez que uma regra se divide entre telas neste projeto (senha: 6/8/10; preço; agora telefone), e a primeira em que o prejuízo foi um cliente pagante sem contato.

Aplicada nos **quatro** formulários do Oficial:

| Formulário | O que ganhou |
|---|---|
| `RegistroMarina` (cadastro pago) | `+55` fixo, máscara, e-mail e telefone conferidos no envio |
| `MarinaParceira` (indicação) | passou a importar a regra em vez da cópia local |
| `SejaParceiro` | telefone virou obrigatório e completo; e-mail conferido |
| `SolicitarDossie` | telefone é opcional, mas se digitado tem de estar completo |

**Mínimo de 11 dígitos**, não 10. O número serve para WhatsApp, e fixo não recebe — aceitar 10 grava um contato que nunca vai funcionar, e o silêncio é total: a Evolution aceita a chamada e não entrega nada. `1299187251` (um celular com um dígito a menos) passava como fixo válido.

Verificado em navegador real: com o telefone vazio na etapa 4, o envio agora **para na página** com "WhatsApp incompleto" em vez de seguir para o Stripe. E `5512991187251` colado com DDI vira `(12) 99118-7251`, sem virar DDD 55.

### A régua do selo de saúde subiu (25/08/2026)

O Índice de Saúde do Ativo dá uma nota 0–100 e um selo. A régua era baixa demais: **metade das categorias preenchidas já dava Prata**, e 80 dava Ouro.

```
antes    Bronze < 50    Prata 50–79    Ouro ≥ 80
agora    Bronze < 60    Prata 60–89    Ouro ≥ 90
```

O selo é o que broker e seguradora vão olhar. Se um cadastro pela metade alcança Prata, o selo não distingue nada — e quem olha para de olhar.

**Feito agora porque depois não seria de graça.** Nenhum dossiê real foi selado ainda. O PDF emitido guarda a classificação **impressa**: mexer na régua depois faria o papel na mão da marina contradizer a tela. Custo aceito: o ativo de teste `YA-IATE-2015-3A38` (score 87) deixa de ser Ouro e vira Prata na próxima vez que o score for recalculado.

O que cada faixa exige, pela fórmula real (50% abrangência · 25% profundidade de manutenção · 15% documentos · 10% laudo de casco):

| Perfil | Score | Selo |
|---|---|---|
| 10 categorias, 6 manutenções, 8 docs verificados, laudo | 100 | Ouro |
| 8 categorias, 6 manutenções, 8 docs verificados, laudo | 90 | Ouro |
| 7 categorias, 6 manutenções, 8 docs verificados, laudo | 85 | Prata |
| 6 categorias, 4 manutenções, 4 docs (2 verificados), laudo | 62 | Prata |
| 5 categorias, 3 manutenções, 3 docs | 50 | Bronze |

**Por que a nota é o motor do cadastro:** ela sobe conforme a marina alimenta, então ela alimenta. O contrapeso é que incentivo para preencher também é incentivo para **inventar** — e registro falso, selado e imutável, dentro de um produto que vende custódia é o pior estrago possível. O que protege é a exigência de prova nas fichas de serviço (horímetro, peça trocada com foto, nota fiscal, quem executou). **Não afrouxar os uploads obrigatórios para facilitar a subida do score.**

**O selo é `Gold` · `Silver` · `Bronze`, em inglês, nas duas pontas.** É o valor que o banco guarda desde que o score existe, e o que a página pública de verificação sempre mostrou. O painel da marina traduzia para "Ouro/Prata" desde 26/06/2026 — então o **mesmo ativo** aparecia "Ouro" para a marina e "GOLD" para o comprador que escaneia o QR. Selo é nome de grau, não texto corrido: manter idêntico nas duas telas é o que permite marina e comprador falarem da mesma coisa. Quatro ativos de demonstração tinham `ouro`/`prata` gravados à mão no banco (nenhum código escreve isso) e foram normalizados para inglês, para não aparecer `OURO` no meio dos `GOLD` na página pública.

**Aberto e sabido — jetski não alcança Ouro com folga.** O painel esconde as abas `interior` e `pintura` para jet ski (`AtivoHub.tsx`), mas o score continua contando as duas nas 10 categorias-núcleo. Um jet ski impecável bate **exatamente 90**: sem nenhuma margem, por duas categorias que a própria tela decidiu que não existem para ele. O veleiro já foi tratado (`CAT_ALIAS = {"velame": "motor"}`); o jetski não. O conserto é medir a abrangência contra as categorias **aplicáveis ao tipo**, e é a mesma divisão de sempre: a lista de categorias vive no painel e no `asset_score_service`, e o comentário do próprio arquivo pede "manter SEMPRE em concordância com o painel".

### O painel chamava toda marina pelo mesmo nome (25/08/2026)

A marina paga US$ 250, entra no painel pela primeira vez, e é recebida por:

> **Marina Hub** — *Fleet Excellence.*

Não era o nome dela. Era `t('common.marina_hub')`, uma **string de tradução fixa** — o mesmo título para toda marina que entrasse, desde sempre. O painel nunca leu o nome de ninguém.

O contraste é o que dói: o e-mail de boas-vindas, enviado minutos antes, já dizia *"Olá, Amazon Marina"*. O dado estava no cadastro (`user_metadata.marina`), o e-mail foi buscar, o painel não.

Corrigido em três lugares — o título do painel e as duas ocorrências no **relatório de frota**, que é documento que a marina baixa e manda para terceiro. "Marina Hub" continua como último recurso, se o cadastro vier sem nome.

### A indicação era descartada em todo cadastro do Oficial (25/08/2026)

O formulário pergunta *"Alguma marina indicou o Yachts Atlas para você?"*. A resposta ia para o log e para lugar nenhum — **para toda marina, desde sempre**, não só nos testes.

`_registrar_indicacao` começava procurando quem se cadastrou em `marinas_lancamento`, pelo e-mail:

```python
if not minha.data:
    logger.info(f"... sem vaga de lancamento — texto nao gravado: {texto!r}")
    return
```

As 20 linhas dessa tabela têm **zero e-mails preenchidos**. A busca nunca achava ninguém e o `return` caía sempre. E o comentário da própria função prometia o oposto — *"o texto cru fica guardado como ela digitou (…) nada disso pode ser descartado"* — enquanto a primeira linha do corpo fazia o descarte.

É o motor de crescimento (20 → 40 marinas) perdendo o vínculo **no único momento em que ele existe**: depois do cadastro, ninguém lembra quem indicou quem, nem a indicante nem a indicada.

**Corrigido invertendo a ordem.** O texto cru agora vai primeiro para o **cadastro da própria marina** (`user_metadata.indicada_por`) — o único lugar que existe para toda marina, paga ou de lançamento. Só depois vem a tentativa de casar com uma fundadora, que virou bônus: falhar ali não perde mais nada.

Fica no `_registrar_indicacao` e não no `create_user` de propósito: assim também vale para quem volta numa **segunda tentativa** de checkout, quando a conta já existe e o `create_user` falha.

**O teste que existia passava.** `test_o_que_ela_digitou_fica_guardado` era verde enquanto a produção descartava tudo — porque o cenário dava e-mail à linha de lançamento da marina que se cadastrava. O fixture construía o mundo que o código esperava, em vez do mundo que existe. Acrescentado o teste do caso real: marina fora do lançamento, banco sem correspondência, e o texto tem de estar no cadastro mesmo assim.

### O barco não tinha onde ter nome (25/08/2026)

`nome_reg` é o **nome da embarcação** — o que está pintado na popa e escrito no Título de Inscrição. É o título do dossiê, da página pública de verificação e do Portal do Proprietário.

```
lido em     7 telas
escrito em  nenhum lugar
```

A coluna existia no banco, era exibida em toda parte, e **não era declarada no schema da API nem coletada no formulário**. Toda embarcação caía no `marca + modelo` — por isso o dossiê de um iate se apresentava como *"Marlin Sea Focus"* em vez do nome do barco. Os únicos ativos com nome eram os de demonstração, inseridos à mão.

É o mesmo defeito que largura e calado tiveram, e que o comentário do próprio `AtivoBase` descreve: *"as colunas existem no banco desde sempre e NENHUMA era declarada aqui — o getattr lia None e o dado nunca era gravado. Código morto que parecia vivo."* Corrigiram para as especificações e não notaram que o **nome** tinha o problema idêntico.

Fechado nas quatro pontas: `AtivoBase.nome_reg`, o insert em `create_ativo`, o campo no formulário (logo depois do tipo, antes da marca) e o reset do formulário — este último só apareceu porque o `tsc` reclamou.

Continua **opcional**: barco sem nome registrado segue caindo no `marca + modelo`, que é o comportamento que sempre existiu.

### Quem pode alimentar o cofre pelo celular (decidido em 25/08/2026)

Foto tirada no píer precisa chegar ao cofre. A pergunta era quem pode mandar — e a resposta separa **entrada** de **custódia**.

```
gerente da marina        envia e SELA
encarregado da marina    envia
dono do ativo            SÓ LÊ
```

**Não é limitação técnica — é o que dá valor ao selo.** A autoridade do registro não vem de quem paga nem de quem é dono: vem de ser **independente do resultado**. O armador é quem vende o barco, e o dossiê é o que forma o preço. Se ele alimentasse o próprio histórico, o documento viraria declaração do vendedor — exatamente o que o mercado já ignora, e o que o Atlas existe para substituir.

O custo de abrir essa porta não seria caso a caso: **bastaria o comprador saber que o dono podia contribuir para que todo dossiê ficasse sob suspeita**, inclusive os que ele nunca tocou. Credibilidade se avalia pela regra, não pela exceção.

E há a razão comercial, que chega na mesma conclusão: **quem paga é a marina.** Ela assina, fica com 100% do dossiê e é a reputação dela que o selo carrega. Dar escrita ao armador seria suporte sem receita, além de sujar a cadeia de quem é cliente.

**Quando o armador tiver material** — foto de viagem, ocorrência longe do píer — ele manda por fora (WhatsApp, e-mail) e o gerente decide se entra. O filtro humano no meio **é** o produto: é o gerente dizendo "isto eu assumo como registro". Quando entrar, a `observacao` diz de onde veio ("fotos fornecidas pelo proprietário"), e o dossiê fica fiel: distingue o que a marina observou do que recebeu.

**O que existe hoje e o que falta:**

| Papel | Telefone | Escopo |
|---|---|---|
| Gerente da marina | `user_metadata.telefone` | por marina — **já existe** |
| Encarregado | — | por marina — **falta** |
| Dono do ativo | `ativos.proprietario_telefone` | por barco — já existe, para contato e código do Portal (não para enviar) |

### Auditoria de prontidão para seguradora e certificação — 30/08/2026

O fundador definiu a direção: *"conferir o sistema e deixá-lo 100% pronto para receber essas futuras implementações — API Supabase para seguradoras, certificações e auditorias externas, SUSEP e outras."*

Auditei o banco de produção contra o checklist do documento de estratégia (SOC 2 / ISO 27001 / SUSEP). O resultado foi melhor do que o próprio PRD sugeria — e três pendências dele estavam **desatualizadas**, o que é pior que pendência aberta: documentação errada guia decisão errada.

**O que já passa, e com folga:**

| requisito | estado real |
|---|---|
| Trilha de auditoria imutável | `audit_logs` com gatilho que recusa UPDATE e DELETE; **184 linhas gravando** |
| Registro append-only | `registros` recusa UPDATE **e** DELETE |
| Criptografia disponível | `pgcrypto` e `supabase_vault` instalados, nos schemas corretos |
| RLS | habilitado em **todas** as tabelas |
| Dados sensíveis fora do público | bucket `media` **privado** |
| Soft delete | `ativos.arquivado_em`, **em uso**: 6 dos 14 arquivados |

**A imutabilidade é o ponto mais forte do sistema.** `fn_registros_imutavel` bloqueia UPDATE por padrão e abre **uma** exceção — redação LGPD — com seis travas: exige flag de sessão, só apaga campos de uma lista fechada de dez, exige vínculo com a solicitação do titular, preserva o hash original em `hash_pre_redacao`, e proíbe alterar `status`, `titulo`, `categoria` e `checklist` **mesmo na redação**.

Isso encerra em definitivo a dúvida de 28/08 sobre corrigir os status antigos por `UPDATE`: `status` é imutável até na exceção. **Retificação é o único caminho** — e o motivo é mais forte do que se sabia quando a recomendação foi dada.

**O que ainda falta**, em ordem de esforço (a ordem que o fundador pediu — do mais fácil ao mais difícil):

1. ~~Gatilho de DELETE em `ativos`~~ — **feito nesta rodada**
2. Proteção contra senha vazada (HaveIBeenPwned) — configuração no painel, 1 minuto, do fundador
3. Documentar por que 13 tabelas têm RLS **sem política** (é deny-all, e é seguro — mas o auditor vai perguntar)
4. **CPF/CNPJ do proprietário está em texto plano** — 7 ativos têm `proprietario_documento`, os 7 em claro. O `pgcrypto` está instalado e **não é usado**. O dossiê já mascara na exibição, mas o banco está aberto. É o item que reprova numa auditoria LGPD
5. **A verificação nunca recalcula hash** — responde "íntegro" conferindo se a coluna está preenchida, e ela é preenchida por gatilho, então dá 100% sempre. É o coração da promessa ("dados confiáveis") e o único item que impede a conversa com seguradora
6. **Não existe base legal registrada para compartilhar** — há `lgpd_solicitacoes` (direito do titular), mas nenhuma tabela de consentimento. No dia em que o dossiê for por API para uma seguradora, a pergunta é: com que autorização do armador?
7. Isolamento é por **usuário**, não por organização — não há `tenant_id`. Funciona hoje (uma marina = uma conta; 6 contas, 4 donos distintos), mas quebra quando uma marina pedir três acessos

**Padrão a repetir:** auditar contra o banco de PRODUÇÃO, não contra os arquivos de migration do repositório. Duas das descobertas mais importantes do dia — o gatilho de UPDATE que existe em `registros` e o bucket que já é privado — não apareciam no `grep` dos `.sql`, porque o repositório não é o estado do sistema.

### A trilha existia e ninguém sabia perguntar nada a ela — 30/08/2026

`audit_logs` tinha 184 linhas com ação, autor, IP, user-agent, horário, severidade, resultado e detalhe em JSONB. Tudo o que uma auditoria pede. Mas o único jeito de consultar era `audit_service.get_user_audit_logs` — os eventos de **um** usuário, em ordem cronológica.

Auditoria não pergunta em ordem cronológica. Ela pergunta *"quantas tentativas falharam no trimestre, e de quais IPs?"*, *"houve pico em algum dia?"*, *"me exporte a trilha"*. A primeira execução do relatório novo respondeu, em segundos, o que antes exigia abrir o banco e escrever SQL: **14 "Invalid signature"** (os PDFs de teste gerados com o segredo de desenvolvimento), **9 "Invalid maintenance credentials"** em 23–24/08 e **1 "File validation failed"**.

**O relatório conta, não julga.** Marcar "suspeito" no lugar do auditor é inventar conclusão — as 14 assinaturas inválidas teriam virado investigação de ataque, e eram teste nosso.

**Padrão a repetir:** dado guardado não é dado disponível. Antes de coletar mais coisa, perguntar se alguém consegue interrogar o que já está lá.

### As duas páginas contando histórias diferentes do mesmo produto — 30/08/2026

Depois de reposicionar o Oficial, o fundador levantou o ponto certo: *"essa já é mais focada para Marinas, mas verifique e ajuste conforme a Oficial, para não terem discordâncias entre si, correto meu argumento?"*

Correto — **com uma exceção que precisa ficar registrada**: preço e prazo **devem** divergir. Lançamento é US$ 200 com 18 meses de dossiê; Oficial é US$ 250 com 12 meses, e os 18 não podem aparecer lá. Alinhar isso quebraria a oferta. O alinhamento é de **tom, vocabulário e afirmação de fato** — nunca de número comercial.

Comparando as duas página a página, apareceram três divergências factuais:

**1. A capacidade fotográfica tinha três valores.**

| onde | número |
|---|---|
| `MAX_FOTOS` no backend (soma dos mínimos de `COBERTURA_CATS`) | **460** |
| Oficial — landing, painel, FAQ | 430 |
| Lançamento | 400 |

O comentário do próprio backend chamava 430 de *"principal argumento de venda"* enquanto o código permitia 460. O fundador escolheu **460**, e a correção foi de raiz: a landing agora **importa `MAX_FOTOS`** e interpola no texto. Número de venda escrito à mão em três arquivos diverge — é só questão de tempo.

**2. "16 seções padronizadas" não era o máximo, nem o que sai, nem o número de categorias.** O gerador tem 11 seções fixas numeradas mais uma por categoria com registro; o Ferretti 780 real produziu 10. O documento tem uma regra central — *seção sem dado não é renderizada* — que garante que esse número **sempre** vai variar. Virou "Estrutura padronizada".

**3. As vagas se contradiziam dentro do próprio Oficial:** 14 numa chave, 120 em duas passagens, contra as 20 do modelo. As 120 saíram por ordem direta (*"nem era pra colocar isso"*).

**Padrão a repetir:** duas superfícies que vendem o mesmo produto precisam de **uma fonte por fato**. Onde o número existe no código, o texto lê o código. Onde não dá para ler (HTML estático do Lançamento), o número entra na varredura de coerência — porque ele vai divergir sozinho.

**E o padrão de copy que se confirmou:** os três filtros do fundador (alto nível, sem ofensa, sem falar de empresa do mesmo ramo) não eram sobre o Oficial — são da marca. O Lançamento violava os três, e um deles de forma constrangedora: usava **WhatsApp como canal oficial de conversão** e, dois blocos abaixo, como símbolo de desorganização.

### A página vendia para quem não paga — 30/08/2026

O Marcos: *"Nossas páginas estão focadas no Ativo e no armador, mas esquecemos que trabalharemos com as MARINAS do BRASIL e depois ao redor do globo."*

Ele está certo, e o desalinhamento era total. A home dizia **"Seu iate não é apenas um ativo"**, o botão dizia **"Proteger meu Ativo"**, e os quatro benefícios eram todos do dono: valorização de 20%, liquidez, prêmio de seguro menor. A marina — que assina os US$ 250/mês — aparecia no bloco de indicação e numa pergunta do FAQ.

**Uma ressalva foi levantada antes de escrever, e mudou o texto.** Veio junto um PDF de terceiro propondo headlines de *"elimine o gargalo operacional"*, *"automatize minha marina"*, *"movimentações, agendas e processos"*. O Atlas **não faz** gestão de pátio, agenda de vaga nem movimentação: vender isso seria a mesma armadilha que passamos a semana consertando no dossiê — prometer mais do que se entrega. O ângulo B2B honesto já estava no produto: a marina **se protege e retém o cliente**.

**Padrão a repetir:** antes de reposicionar uma página, listar o que o produto REALMENTE faz e recusar o que ele não faz — inclusive quando a sugestão vem em documento formatado. Copy é promessa; promessa não cumprida vira churn.

### Reposicionar revelou contradições que ninguém tinha visto — 30/08/2026

Trocar o interlocutor expôs afirmações que **se contradiziam dentro do mesmo site**:

- A página de Segurança dizia *"cada **proprietário** recebe uma chave... somente você e as **entidades autorizadas** (marinas, seguradoras)"* — a marina como terceiro autorizado pelo dono. A home afirma o inverso: *"A custódia é da marina; o proprietário apenas consulta."* Um visitante lia as duas na mesma visita.
- O **Portal do Proprietário** estampava *"Seu Ativo. **Seu Controle**"* — e a tela é `readOnly`. A própria página, mais abaixo, explica que quem emite é a marina.
- O **SEO** vivia em dois arquivos. O `index.html` foi corrigido, mas `seo/seo-data.json` sobrescrevia em runtime via `SeoMeta.tsx`. Dava para ver na aba: título novo e, três segundos depois, o antigo de volta.

**Padrão a repetir:** mudança de posicionamento é uma boa varredura de coerência. O que estava contraditório antes ficou visível quando o interlocutor mudou — e o `seo-data.json` teria anulado o trabalho em silêncio, sem erro nenhum.

### Três filtros de copy, dados pelo fundador — 30/08/2026

Nas palavras dele: *"Trabalhamos em alto nível, sem ofensas, [sem] falar de equipes do mesmo ramo"* e *"não temos que falar ou supor terceiros, FALAMOS DO NOSSO VALOR E DE NOSSA QUALIDADE DE SERVIÇO."*

A primeira versão da copy — escrita por mim — violava os três:

| escrito | reprovado por |
|---|---|
| "o que a sua marina entrega e **a vizinha** não" | *vulgar*; comparar é linguagem de comércio de bairro |
| "Sua marina cuida de milhões. **E anota tudo num caderno**" | *humilhante*; a provocação virou deboche |
| "sua equipe **para de caçar papel**" | supõe que ela caça |
| "vira **palavra contra palavra**" | supõe conflito na marina |
| "o que sua operação **já paga em retrabalho e cliente perdido**" | supõe prejuízo |
| "não pode viver num **grupo de WhatsApp, numa gaveta**" | descreve uma marina malfeita |

O mesmo ganho, dito pelo lado do que **entregamos**: "A hora que a equipe deixa de perder" virou **"Tudo em um lugar só"**; "Prova do seu lado na discussão" virou **"Prova documental do serviço"**; "Cliente que não troca de marina" virou **"Relação que se aprofunda"**.

Saiu também uma frase pré-existente do onboarding: *"Marinas que não oferecem segurança digital estão perdendo espaço para o futuro"* — fala de empresas do mesmo ramo e ainda ameaça.

**Padrão a repetir:** o público é dono de marina de alto padrão. Ofensa velada, comparação e alarme rebaixam a marca **antes** de qualquer argumento. E quando quiser criar tensão, **pergunte em vez de afirmar** — a headline aprovada é *"Sua marina cuida de milhões em ativos. Cada um com uma história. **Mas onde ficam registrados seus dados hoje?**"* (a pergunta foi reescrita no REV-17; a técnica — perguntar em vez de afirmar — é a mesma). Quem responde chega sozinho à conclusão, sem ter sido acusado de nada. Foi ideia dele pôr a pergunta, e ele notou que é a mesma técnica que usa comigo: pergunta em vez de ordem.

### A trava que existia e estava desligada na origem — 28/08/2026

Em REV-06 o `_saude_por_categoria` ganhou uma regra dura: em **casco** e **sinistros**, "atenção" não é ressalva, é fato grave — vale **0**, não 50. Foi escrita para impedir um "GOLD · 100%" num barco que bateu em objeto submerso.

Ela nunca disparou. Nem uma vez.

O `STATUS_ENUM` do `FichaServicoForm` traduzia três textos **exatos** para o valor que o banco guarda:

```ts
{ 'Concluído': 'concluido', 'Pendente': 'pendente', 'Atenção': 'atencao' }
```

E as fichas oferecem **sete** conjuntos de rótulos. Seis não usam nenhuma dessas três palavras sozinhas:

| ficha | rótulo oferecido | virava |
|---|---|---|
| casco | `Crítico (Avaria Estrutural)` | `registrado` |
| pintura | `Crítico (Sem proteção/craca)` | `registrado` |
| seguro | `Vencida` | `registrado` |
| sinistro | `Nao reparado` | `registrado` |

`registrado` não é `atencao` nem `pendente`, então cai no `else: st = "ok"`. O operador marcava **AVARIA ESTRUTURAL** e o dossiê imprimia **CASCO · CONFORME, peso 100**.

**Padrão a repetir:** quando um `map[chave] || padrao` traduz entrada de formulário, o padrão precisa ser o **conservador**, nunca o favorável. Aqui o fallback era 'registrado', que a jusante significava "sem problema" — um rótulo que ninguém previu virava notícia boa. Se o fallback fosse "não avaliado", a mesma falha teria aparecido como buraco, e buraco a gente vê.

**E o segundo padrão, que é maior:** uma regra de negócio dura foi escrita, revisada e documentada **três semanas antes**, e estava inerte porque o dado nunca chegava na forma que ela esperava. Não bastou testar a regra; faltava testar o **caminho** até ela. Toda trava merece a pergunta: *qual entrada real faz isso disparar, e ela existe?*

### O teste achou o defeito enquanto era escrito — 28/08/2026

O Marcos pediu testes automatizados para o que é crítico. Como não há runner no frontend, o teste lê `servicosCategorias.ts` e `FichaServicoForm.tsx` **como texto** e confere que todo rótulo oferecido cai numa regra conhecida.

Falhou na primeira execução, com quatro rótulos que a correção anterior — que eu já tinha dado por completa — não cobria:

```
Nao reparado                           →  registrado
Reparo parcial - pendencias em aberto  →  registrado
Reparado com ressalva tecnica          →  registrado
```

São da ficha de **sinistro**, que tem vocabulário próprio. Um sinistro *não reparado* saía CONFORME, na categoria que o dossiê trata como fato grave.

Tem um detalhe que só um teste pega: `Totalmente reparado - sem ressalva` e `Reparado com ressalva tecnica` compartilham a palavra *ressalva* com sentidos **opostos**. A regra precisa testar `sem ressalva` **antes** de `ressalva`.

**Padrão a repetir:** teste de **contrato entre as pontas** vale mais que teste de função. Estes não verificam o que o código faz hoje — verificam que o defeito não volta: rótulo novo sem regra quebra o teste; a leitura voltando a ser por igualdade exata quebra; a conformidade voltando a ser barra quebra; um segundo CNPJ aparecendo no código quebra. É a sexta vez que "a mesma regra em dois lugares" custa caro neste projeto, e a primeira em que existe alguém vigiando as duas pontas.

### Nove números que prometiam mais do que mediam — 28/08/2026

Uma varredura sobre o dossiê emitido do Ferretti 780 e sobre o gerador. Todos do mesmo tipo — *campo certo, lido como outra coisa*:

- **capa: 28 documentos**, pág. 4: 10, pág. 14: 18 imagens. `len(documentos)` somava as duas espécies e publicava com o nome de uma. E a chave interna chamava-se `imagens` enquanto o rótulo impresso dizia "Documentos".
- **"Investido no ativo"** somava `valor` de casco e sinistros — onde o campo é *"Estimativa de custo de reparo estrutural"* e *"Estimativa inicial de prejuízo"*. Dinheiro que ninguém gastou, anunciado como benfeitoria. É o R$ 2,5 mi da apólice voltando por outra porta: **excluir por categoria não bastou — o que decide é a natureza do valor**.
- **"Hashes íntegros 100%"**: conta quantos registros têm a coluna preenchida, e a coluna é escrita por trigger no INSERT — nunca é nula, então dá 100% sempre. Nada é recalculado no caminho `montar_dados → gerar_pdf`. Virou **"Registros com selo"**, que é o que a conta faz.
- **"Custo médio / mês"** dividia o gasto pelo tempo de **cadastro**. No onboarding normal a marina sobe anos de histórico na primeira semana: trinta dias depois o dossiê imprimia a década como mensalidade. Numerador de dez anos, denominador de um mês.
- **"Horímetro atual"** era `max()` de todas as leituras — e o campo existe em fichas de motor, gerador e equipamento. O Ferretti tem quatro (1.480, 1.476, 1.120, 1.095). `max()` é o **maior**, não o mais recente: um zero a mais digitado uma vez ficaria sendo o horímetro do barco para sempre.
- **Vencimentos** deduplicava por campo guardando a data **mais distante**. Mas o mesmo campo serve seis extintores e a habilitação de condutores diferentes: com três condutores e duas CHA vencidas, saía **uma** linha, "Em dia", com a validade do único regular. O viés era sempre para o lado favorável.
- **Linha do tempo** misturava data do serviço e data de cadastro na mesma coluna. No Ferretti os treze marcos saíram todos em "08/2026" — cronologia sugerindo que revisão de 500 h, docagem, laudo e apólice aconteceram no mesmo mês, num documento cujo produto **é** o histórico.
- **Capa: 13 registros; corpo: 12.** A seção 03 imprime só itens de `checklist`, e "documentacao" já entrava em `categorias_tratadas` — registro de documentação sem checklist sumia dos dois lados. Faltava a *Renovação do Título de Inscrição*, justamente um documento da Capitania.
- **Data sob a foto** era `uploaded_at`, impressa ao lado de GEO e do hash. Lado a lado as três se leem como propriedades da **foto**. GEO foi corrigido em 26/08 e passou a sair do EXIF; a data não — metade do par consertada, metade prometendo o mesmo. Passa a dizer **"SELADO EM"**.

**Padrão a repetir:** antes de publicar um número, escrever a frase que o descreve **com o denominador dentro**. Se a frase precisa de uma ressalva para ser verdadeira, a ressalva vai no documento — ou o número não vai.

### O revisor externo estava certo pelo motivo errado, duas vezes — 28/08/2026

Os itens 1 e 2 do relatório de terceiro (CNPJ divergente, protocolo corrompido) não existiam no documento impresso. Mas o **texto extraído** do PDF saía assim:

```
P r o t o c o l o   Y A - I A T E - 2 0 2 0 - E C D D
A X O S  H U B  ·  C N P J  2 6 . 9 9 8 . 5 7 1 / 0 0 0 1 - 5 0
```

`Y A - I A T E` lido corrido vira **"YA HATE"** — exatamente o que o relatório escreveu. E o CNPJ soletrado é onde ele perdeu os dígitos.

Medido: o extrator desiste de juntar as letras quando *tracking ÷ corpo da fonte* ≥ **0,15**. Os quatro textos do cabeçalho estavam acima (o rodapé em 0,20; a marca em 0,23). Teto de 0,14 no `draw_tracked`, com escape `decorativo=True` para a marca e a assinatura, que ninguém copia.

Não é preciosismo: **o comprador que copia o protocolo para colar na página de verificação copiava lixo**, o Ctrl+F não achava nada, e o leitor de tela soletrava.

**Padrão a repetir:** quando um relatório externo erra o sintoma mas nomeia uma categoria plausível, investigar a **categoria**. Foi assim nas duas vezes hoje — "falha de codificação" levou à fonte base-14 imprimindo quadrado preto, e "protocolo corrompido" levou ao letter-spacing. O que não existia era a descrição; o que existia era pior.

### O relatório de melhorias, e o defeito que ele não viu — 28/08/2026

O Marcos trouxe um **Relatório de Melhorias** de terceiro sobre o dossiê, com cinco itens. Conferi um por um contra o código e contra três PDFs já gerados, antes de mexer em qualquer coisa. **Três dos cinco não existem** — e os dois marcados como prioridade Alta estão entre eles:

| # | apontado | verificação |
|---|---|---|
| 1 | CNPJ divergente (`/0001-10` × `/0001-50`) | **não procede** — uma única string em 7 arquivos, e o PDF extrai `/0001-50` |
| 2 | Protocolo corrompido: `"ProtocolЬ ХАНАТЕ-2020-ECDD"` | **não procede** — sai `Protocolo YA-EXEMPLO-2026-0001`, limpo. Os caracteres cirílicos são assinatura de OCR ruim |
| 3 | Imagens esticadas → aplicar `object-fit: cover` | **não procede** — o gerador é ReportLab, não HTML; e `_celula_foto` já calcula `alt = larg * (ph/pw)` |
| 4 | Travar emissão sem classificação de serviço | procede o fato, **não a solução** — ver abaixo |
| 5 | Panfleto de fornecedor no registro fotográfico | **procede**, e vale mais do que "Baixa" |

**Padrão a repetir:** relatório de terceiro é hipótese, não diagnóstico — conferir contra o código **e** contra o artefato real antes de abrir editor. Mexer em código que está certo é como se criam defeitos, e três consertos aqui teriam custado tempo para não corrigir nada.

**Sobre o item 4:** o dossiê inteiro é construído sobre mostrar a lacuna com honestidade — é o mesmo princípio do "NÃO AVALIADO" e do "3 de 11 sistemas". Travar a emissão contradiz isso e joga o problema no suporte. O lugar certo é o **painel**, exigindo a classificação na criação do registro; o dossiê continua contando a verdade sobre o passado. Fica em Pendências.

### O quadrado preto no nome do proprietário — 28/08/2026

Investigando o item 2 (que não existia), apareceu um defeito real e maior, em outro lugar.

O gerador usava as fontes **base-14** do formato PDF — Helvetica e Times-Bold. Elas não exigem arquivo, e é por isso que estavam ali. Só conhecem **Latin-1**. Fora dele o ReportLab substitui o caractere **sem lançar exceção e sem escrever no log**:

```
Dvořák            →  Dvo■ák
Łukasz Wałęsa     →  ■ukasz Wa■■sa
İstanbul Yıldız   →  ■stanbul Y■ld■z
```

Atinge nome do barco, do proprietário, da marina e a descrição digitada pelo técnico. O `SERIF` — que imprime o **nome da embarcação**, o maior texto do documento — tinha o mesmo problema, e quase passou despercebido por estar em outra constante.

O que torna isso pior do que um erro de exibição: o documento sai **selado por SHA-256 e com QR de verificação**, ou seja, afirmando integridade. O selo não protege a verdade; carimba o erro.

**A escolha da fonte foi medida, não opinada.** Arial cobre todos os casos e tem as **mesmas medidas** da Helvetica — `+0,01%` de largura no pior texto real do dossiê, layout intacto. Verdana (+10,5%) e Tahoma (−3,5%) moveriam quebras de linha; DejaVu nem cobre tudo.

O Marcos decidiu **Arial**, e que a troca fica **só no dossiê** — o frontend não encosta. Como produção é um container Debian sem fonte da Microsoft, existe uma cadeia: **Arial** (dev, Windows) → **Liberation Sans** (produção, mesmas medidas, licença livre, instalada via `fonts-liberation` no Dockerfile) → base-14 como último recurso, **gritando em `logger.error`** — se cair ali, o quadrado preto volta. Emoji fica de fora: nenhuma fonte de texto tem `⚓`, e o gerador agora **avisa antes de emitir** quando encontra um caractere sem glifo.

**Padrão a repetir:** quando o relatório aponta a categoria certa pelo motivo errado, a categoria ainda merece investigação. "Falha de codificação de caracteres" estava certo; o lugar não.

**E o achado de tabela:** `logger` era chamado no `except` de download de foto e **nunca tinha sido importado**. Uma foto que não baixasse levantava `NameError` dentro do próprio tratamento de erro e derrubava a emissão do dossiê inteiro — exatamente o caso que a mensagem *"Imagem indisponível no momento da emissão — registro selado permanece íntegro"*, logo abaixo, existia para tratar com elegância. Tratamento de erro que nunca foi exercitado não é tratamento de erro.

### Critério invisível é opinião; critério publicado é metodologia — 28/08/2026

Pergunta do Marcos: *"sobre a saúde da embarcação, pq não colocar um saiba mais explicando como é analisado a saúde do ATIVO"*.

O dossiê estampava oito caixas coloridas — CONFORME, ATENÇÃO, CRÍTICO, NÃO AVALIADO — e um percentual, e **em nenhum lugar dizia como aquilo foi decidido**. A regra existe em `dossie_data._saude_por_categoria` e é boa: conforme 100, atenção 50, crítico 0; sinistro aberto e casco em atenção valem zero; EPIRB com ANATEL pendente idem; categoria sem registro sai da média. **Só que ela vivia apenas no código.**

Nasceu a seção **"Como Ler Este Índice"** (não numerada, junto ao Termo de Custódia), que abre delimitando o que o índice **não** é — não é vistoria, não é laudo pericial, não é avaliação de valor de mercado — e segue com a tabela de pesos, o cálculo, os agravamentos e as retificações. Sob a grade da primeira página ficou uma linha curta com o essencial e a remissão, porque o comprador que olha no celular não vai à página 12.

**Padrão a repetir:** número que sustenta decisão de compra precisa vir com o critério **dentro do mesmo documento**. É o que permite à marina defender o número na frente do comprador em vez de telefonar para a plataforma. E o texto publicado **espelha código** — está anotado nas duas pontas que mexer na regra obriga a corrigir a seção, porque **critério publicado errado é pior do que critério não publicado**.

### A segunda barra ainda enganava — 28/08/2026

Observação do Marcos sobre o desenho de REV-06: *"a segunda barra do dossiê-atlas que indica 100%, pode ser que traga alguma confusão"*.

Ele está certo, e a correção anterior tinha ficado no meio do caminho. A `CONFORMIDADE` já era fina e dourada em vez de verde, com legenda embaixo — mas continuava sendo **uma barra cheia de ponta a ponta com "100%" ao lado**. Num barco com 3 de 11 sistemas avaliados, a coisa visualmente mais afirmativa da página era ela.

**Forma vence cor.** Uma linha cheia comunica "completo" antes de qualquer legenda de 5,5pt ser lida, e o leitor típico é o comprador no celular, com pressa. Suavizar a cor não resolve o que a forma promete.

A barra saiu. Virou número e frase:

```
COBERTURA DE VERIFICAÇÃO   ▬▬▬───────────────   27%
3 DE 11 SISTEMAS COM REGISTRO

CONFORMIDADE                                    100%
Calculado sobre 3 de 11 sistemas — 8 sistemas sem registro não entram na conta.
```

A frase foi escrita para ser verdadeira em **qualquer** percentual — testados 100% sobre 3 de 11, 100% sobre 10 de 11 (singular: *"1 sistema sem registro não entra"*), 100% com tudo avaliado, e **38%** sobre 4 de 11. Dizer *"os 3 sistemas estão conformes"* seria a mesma armadilha entrando por outra porta: frase que só funciona no caso bom.

Com a segunda barra fora, `GaugeBar` ficou com um parâmetro `principal` sem uso — removido junto com os ramos de cor e tamanho que dependiam dele. Está escrito na docstring **por que** a conformidade não tem barra e que já se tentou resolver com cor, para ninguém "consertar de volta" daqui a seis meses.

**Padrão a repetir:** quando um indicador engana, checar se a correção mexeu na **forma** ou só na cor. Cor é modificador; forma é afirmação.

### "E se eu quiser sair, meus dados vão comigo?" — a resposta — 28/08/2026

É a primeira pergunta que um gestor cauteloso faz antes de colocar anos de papel no sistema de outra pessoa. A resposta tem três partes, e elas são diferentes entre si.

**Levar os dados: sim.** Hoje não existe botão de exportação — dá para montar à mão consultando o banco, o que resolve um caso isolado em meia hora. Virar rotina exige a exportação de verdade: ativos, registros, documentos e os links dos arquivos. **Um dia de trabalho, primeira coisa depois do lançamento.** Enquanto não existir, a frase "você pode sair quando quiser" vale pela metade: a assinatura ela cancela sozinha, os dados não vêm junto.

**Apagar dado pessoal: sim.** Nome do condutor, habilitação, CHA. Existe o mecanismo (`fn_lgpd_redigir`): apaga o campo de uma lista fechada, preserva o hash original em `hash_pre_redacao`, e **o dossiê declara que houve redação**. Apagar em silêncio seria adulterar o histórico — o oposto do que o produto promete.

**Apagar o histórico das embarcações: não.** `registros` e `documentos` são append-only; o banco recusa DELETE até para o service_role.

E o motivo que vale ter na ponta da língua não é técnico:

> **O registro do barco não é só da marina.** O dono do iate tem um dossiê na mão, com QR, e aquele QR confere contra esses registros. Se a marina sai e o histórico é apagado, o dossiê que o armador pagou vira papel morto — e ele não teve nada a ver com a briga. A marina é a **guardiã** do histórico, não a dona dele.

A frase do Marcos, na conversa que originou isto: *"ela é cliente sim, ela pode sair a qualquer momento."*

E a resposta completa, para a reunião:

> Seus dados você leva quando quiser. Dado pessoal, a gente apaga se você pedir. O histórico das embarcações fica — porque ele é dos donos dos barcos, e o dossiê que eles têm na mão precisa continuar valendo.

**Por que isso vende melhor que trava.** Retenção por dado preso funciona por um tempo e vira mágoa: marina que fica porque sair dói é refém, não cliente. Dizer "leve seus dados" tira o medo de assinar, e sobra a retenção que interessa — ela continua porque o dossiê rende.

### As caixas que pareciam upload — 27/08/2026

`RegistroForm` mostrava duas áreas de upload que não eram upload:

```
Fotos do Serviço (Antes/Depois)     "Clique para adicionar fotos"     JPG, PNG - Máx 10MB
Recibos e Comprovantes              "Clique para adicionar recibos"   PDF, JPG - Máx 10MB
```

Borda tracejada, ícone, `cursor-pointer`, efeito de hover. E **nenhum `<input type="file">` no componente inteiro** — clicar não abria nada e não dava erro. A `interface` do componente até declarava `fotos?: string[]` e `recibos?: string[]`, campos que o `handleSubmit` nunca enviou: alguém previu o upload e parou no meio.

Mesmo padrão de sempre — código correto que nunca foi ligado —, só que aqui a parte que faltou era a que o usuário toca.

**Onde aparecia:** rota `registros/:ativoId`, atrás do login. Não é a marina prospectando que esbarrava; é a marina **já paga**, no primeiro serviço que fosse registrar. Gravidade menor que uma página de venda, mas pior em outro sentido: numa tela que promete cofre imutável, botão que não responde é o tipo de coisa que faz duvidar do resto.

**Por que não ligar em vez de remover:** o hash é por documento, não por registro, então o arquivo precisaria subir antes de o registro existir. É obra maior que o prazo. As duas caixas viraram uma linha que diz onde o upload funciona de verdade — a ficha do ativo, em Documentação.

### A vaga de fundadora que ninguém ativava — 27/08/2026

O teste que a gente vinha adiando finalmente rodou, e achou o buraco na primeira tentativa.

**O que aconteceu.** A Antioquia Marina preencheu o cadastro da Lançamento. O sistema criou o login, reservou uma das 4 vagas de SP no nome dela e mandou para o checkout em real. Ela pagou R$ 1,00 pelo link de teste. Resultado:

```
pagamento registrado        sim
acesso liberado             sim
e-mail de boas-vindas       sim, com o nome da marina
vaga de fundadora           NÃO — continuou "reservado", vencendo em 3h
```

Do ponto de vista do sistema, **tinha sido um sucesso**. Nenhum erro, nenhum log, nada. Numa venda real: a marina paga preço de fundadora, entra no sistema, e a vaga dela volta para a fila algumas horas depois. Ela só descobre quando for cobrar os 18 meses de dossiê.

**A causa era estreiteza de vista.** O código sabia fazer duas perguntas:

```
metadata.programa está marcado?     depende de 4 links marcados à mão no painel
veio de um link conhecido?          depende do link estar na configuração
```

O link de teste não tinha metadata (chegou `{}`) e não estava na configuração. As duas responderam "não sei", e o código — corretamente — **não chutou**. Chutar ali daria vaga de fundadora para qualquer compra da casa.

**Mas havia uma terceira prova, na frente dele.** Existia uma linha em `marinas_fundadoras` com aquele e-mail e status `reservado`, criada pelo próprio cadastro minutos antes. Não é inferência sobre o pagamento — é um fato já gravado.

```
1. metadata.programa                 intenção declarada, ganha de tudo
2. link de origem                    sobrevive a troca de preço e de moeda
3. reserva neste e-mail              não depende de configuração nenhuma   ← nova
```

Cada uma existe porque a anterior pode faltar. A terceira é a rede embaixo das outras duas.

#### Não existe a 21ª vaga

São 20, sendo 4 por estado, anunciadas na página. Eram 7 e o Marcos subiu para 20 — mas subir o número é decisão dele, não algo que o sistema faz no calor de um pagamento. As palavras dele: *"são apenas 20 vagas, não dá pra ficar abrindo vagas."*

Isso decide o caso da **reserva vencida**. As 3 horas existem para ninguém parar em cima de uma vaga sem pagar; passado o prazo, ela volta para a fila (`fn_vagas_fundadoras_ocupadas` só conta reserva dentro do prazo) — **mas a linha continua no banco**. Honrar essa linha sem olhar o estado criaria a quinta fundadora de SP.

| Situação | O que acontece |
|---|---|
| Reserva no prazo | ativa |
| Vencida, estado com espaço | ativa e registra em WARNING |
| Vencida, estado lotado | **não ativa** e registra em ERROR — devolver a diferença |
| Não consegue contar as vagas | **não ativa** — na dúvida, não arrisca a quinta |

O último caso é deliberado: sem saber quantas estão ocupadas, o silêncio é mais barato que a quinta vaga. Vale a regra que já estava escrita no código desde antes: *"cobrar US$ 200 de quem não tem vaga cria uma obrigação impossível"*.

**Nada disso derruba o pagamento.** Banco fora do ar, data ilegível, e-mail vazio — tudo cai em "não é fundadora" e o acesso sai do mesmo jeito. Perder a ativação é ruim; derrubar o webhook é pior, porque aí nem o acesso a marina recebe.

11 testes cobrem o caso do defeito, a ordem das três provas, o prazo vencido nas duas direções, a contagem indisponível, o banco fora do ar e data ilegível.

### Moeda: o preço é em dólar, a cobrança da marina brasileira é em real — 26/08/2026

**A evidência que abriu o assunto.** Em 19/08/2026, uma cobrança real de **US$ 250,00** foi recusada com o motivo **"Moeda não aceita"**. Dois minutos depois, o mesmo cartão pagou **R$ 1,00** sem problema. Não é o Stripe nem a conta: é o banco emissor recusando cobrança em moeda estrangeira — cartão brasileiro costuma vir com compra internacional **bloqueada por padrão**, e quem desbloqueia é o titular, no app do banco. Gerente de marina não faz isso no meio do checkout; ele fecha a aba.

**E venda perdida assim não aparece em lugar nenhum.** Não chega e-mail, não entra no painel. Some.

**O diagnóstico levou duas hipóteses erradas antes da certa.** Primeiro achei que Adaptive Pricing não valia para assinatura — a própria tela do Stripe desmentiu, mostrando "Adaptive Pricing: Ativado" num preço recorrente. A resposta estava num dado que eu já tinha na tela e não tinha lido:

```
USD 200.00   outras moedas: nenhuma
USD 250.00   outras moedas: nenhuma
```

**Não existia real cadastrado para converter.** Os dois preços do Atlas eram os únicos em dólar de uma conta cheia de preços em real — por isso eram os únicos que apareciam em dólar.

**A decisão do Marcos:** o projeto é em dólar desde o início e continua. O real é **forma de pagamento, não oferta diferente** — as páginas seguem anunciando US$ 200 e US$ 250.

| | dólar | real | trava |
|---|---|---|---|
| Lançamento | US$ 200/mês | R$ 1.000/mês | 5,00 |
| Oficial | US$ 250/mês | R$ 1.250/mês | 5,00 |

Números redondos de propósito, decisão dele: *"multiplica por 5"* é conta que o gerente faz de cabeça, e clareza numa venda de 20 vagas vale mais que os 3% de câmbio. Travar em 5,00 com o dólar a 5,15 custa cerca de **$1.400** nas 20 fundadoras ao longo dos 12 meses — e a resposta dele encerrou o assunto: *"cara hj eu não ganho nada"*. 3% de zero é zero.

**A marina não escolhe moeda.** O formulário já coleta a UF (preenchida pelo CEP), e o servidor escolhe o link — `leads._checkout`. Escolha é onde a pessoa erra ou desiste; e a explicação do valor já está escrita na descrição do próprio link do Stripe. Link em real ainda não criado cai no dólar: melhor cobrar na moeda de sempre que mandar a marina para uma URL que não existe.

**Duas coisas que ninguém tinha contado na decisão:**

- **O IOF não é taxa do Stripe.** São 4,38% de imposto federal, cobrados pelo banco do cliente. Um "$250" vira ~R$ 1.450 na fatura, e a marina não pensa "IOF" — pensa que foi cobrada a mais. Primeira fatura é onde a confiança nasce ou morre.
- **Bandeiras — o que se sabe e o que não.** **Elo e Hipercard são bandeiras nacionais e só funcionam em real**: isso é fato, e é um ganho que a cobrança em real destrava — cartão empresarial de banco brasileiro é Elo com frequência. **Se estão habilitadas na conta, não foi verificado.** Tentei concluir pelos ícones do checkout e errei nas duas direções — a fileira de ícones é amostra, não a lista de bandeiras aceitas. Conferir em **Configurações → Pagamentos → Formas de pagamento**, que é onde a resposta mora.

#### O defeito que a venda em real teria criado

A vaga de fundadora era reconhecida assim:

```
metadata.programa == "marina_fundadora"    OU    moeda == usd E valor == 200
```

Pagamento em real chega como `brl 1000`. **Falha nos dois.** A marina pagaria, entraria no sistema, e não ocuparia vaga nem ganharia os 18 meses de dossiê — sem erro nenhum em lugar algum. Pagou e não recebeu.

**E o sintoma já estava no banco desde 19/08, visível, sem ninguém ter lido:**

```
marinas_fundadoras
  Marina Pereira            20/08    stripe_checkout: null
  Marco Henrique Pereira    19/08    stripe_checkout: null
```

Campo vazio nas duas significa que **nenhuma veio de pagamento**. O caminho *pagar → ocupar vaga* nunca rodou inteiro, nem uma vez, em nenhuma moeda.

**Agora o programa vem do link de origem** (`stripe_service._programa_do_checkout`), em duas provas: primeiro `metadata.programa`, se o link tiver sido marcado no painel; depois de qual link o checkout veio, resolvido pela API e guardado em memória. A segunda existe porque a primeira depende de quatro links marcados à mão — e um esquecido significa marina que paga e não vira fundadora, em silêncio.

O `usd 200` virou último recurso, só para checkout que não vem de Payment Link. Continua exigindo dólar: `R$ 200` e `US$ 200` são o mesmo `200.0` e valem coisas bem diferentes, e a conta é da Axos Hub, que vende outros produtos no mesmo webhook.

#### Os links em dólar morreram — e três caminhos apontavam para eles

Criados os preços em real, os produtos em dólar foram **desativados no painel**. As URLs continuam existindo e respondem:

```
The link is no longer active.
```

Pior que não existir, porque parecem funcionar: quem clica não recebe erro do nosso lado, recebe uma página branca do Stripe. Conferido nos quatro links — os dois em dólar mortos, os dois em real vivos.

**Três lugares mandavam gente para lá**, e nenhum sabia:

| Onde | Quem cai lá |
|---|---|
| `leads._checkout` | marina de fora do Brasil |
| `acesso._link_do_checkout` | marina bloqueada querendo voltar |
| `index.html` da Lançamento (3 cópias) | quem está sem JavaScript |

O terceiro tinha o link escrito **três vezes** no mesmo arquivo: dois `href` de botão e uma constante no JS. Terceira aparição do padrão "uma regra, N cópias" no projeto.

**A escolha do link virou peça única** — `app/core/precos.py`. Regra: marina brasileira prefere real, o resto prefere dólar, mas **link vazio nunca é oferecido**. Sem nada configurado devolve `("", "")` e quem monta a tela omite o botão. URL vazia é ruim; URL morta é pior.

Os dois links em dólar estão **vazios na configuração** — é a verdade de hoje. Recriar quando houver venda fora do Brasil; enquanto isso, todo caminho cai no que está vivo. Decisão do Marcos ao ver a lista: *"não tem fora do Brasil hj"*.

#### Aberto

- **O câmbio congela.** O valor em real não acompanha o dólar. Enquanto estiver abaixo de **5,50** a defasagem é pequena; acima disso já são 10% e vale criar preço novo. **Ninguém avisa** — preço congelado não reclama, só vai ficando defasado em silêncio. Régua em `config.BRL_TAXA_REVISAR_ACIMA_DE`. Trocar o preço **não mexe em quem já assinou**, e para as fundadoras isso está certo: o preço delas é fixo por 12 meses, é o que foi prometido.
- **Um Payment Link errado, em Avulso**, foi criado durante os testes e precisa ser desativado no painel. Ele cobra R$ 1.250 **uma vez** — quem comprar por ele fica com acesso vitalício por um pagamento só, e a descrição diz "Assinatura mensal", então a razão seria dela.
- **As cinco faixas de dossiê avulso** (US$ 100 a 400, do dono do ativo) continuam só em dólar. Não urge: as fundadoras têm dossiê 100% incluso por 18 meses, então esses links quase não são usados no começo.
- **Marcar os quatro links** com `programa` no painel. Não é mais obrigatório — o reconhecimento pelo link cobre —, mas é a prova mais forte das duas.

### Que arquivo o cofre aceita — 26/08/2026

Marcos, testando o envio: *"WEBP TMB NÃO PODE"*. Não era só o WEBP — era que **ninguém mandava** na regra. Havia **oito** listas de tipo de arquivo espalhadas, cada tela com a sua:

| Tela | Aceitava | WEBP |
|---|---|---|
| Documentação | `.pdf,.jpg,.jpeg,.png` | não |
| Galeria de cobertura | `image/png,image/jpeg` | não |
| Vitrine e galeria do cadastro | `image/png,image/jpeg` | não |
| Cofre do ativo | `.pdf,.jpg,.jpeg,.png` | não |
| Ficha de serviço (`DOC` e `IMG`) | `.pdf,image/png,image/jpeg` | não |
| Cadastro de categoria | `image/*,.pdf` | sim |

Mesmo arquivo, resposta diferente conforme a porta. A marina não tinha como entender: subia a foto num lugar e era recusada no outro, sem mensagem nenhuma — o seletor simplesmente não mostrava o arquivo.

**WEBP entra porque é foto como qualquer outra.** Mostra o documento igual a um JPG, e é o que celular e site mais produzem hoje. Recusar não protegia nada: fazia a marina converter arquivo à mão.

Agora tudo sai de `utils/arquivos.ts`, e **o texto da tela deriva da lista** — não dá mais para a tela prometer um formato que o seletor recusa, que é o defeito de origem. Vai tipo E extensão juntos: seletor do Windows e de Android antigo às vezes ignora o tipo e só olha o final do nome.

Duas listas ficaram de fora, e agora está dito no código por quê: o botão **Fotografar** usa `image/*` porque com `capture` quem decide o formato é a câmera do celular, e a **conferência de dossiê** aceita só PDF porque é o que ela confere.

**Segunda vez que o mesmo padrão aparece**, depois das cinco validações de telefone: uma regra de negócio copiada em N telas, divergindo em silêncio. Vale procurar as irmãs sempre que uma dessas for corrigida.

**Aberto, achado na varredura:**

- **`RegistroForm` tem duas caixas de upload que não são upload.** Dizem "Clique para adicionar fotos" e "Clique para adicionar recibos", com borda tracejada e cursor de mão — e o componente **não tem nenhum `<input type="file">`**. Clicar não faz nada. Está montado em `Registros.tsx:219`
- **O limite de 10 MB é só texto.** A tela promete "até 10MB" e nada no navegador confere tamanho
- **O servidor não valida tipo nenhum**: `documentos.py` grava o `content_type` que chegar. A lista do navegador é conforto, não segurança

**Feito em 25/08/2026 — a câmera do celular ligada.** O `SecureCameraUpload` existia completo, com `capture="environment"` (abre a câmera traseira), e **nenhum arquivo o importava**. Quinto caso do mesmo padrão no mesmo dia: componente pronto, caminho morto. Plugado no cabeçalho do ativo (`AtivoHub`), como botão **Fotografar**, e escondido quando `readOnly` — que é o Portal do Proprietário. A regra de custódia deixa de ser combinado e passa a ser o que a tela faz.

Junto foi a **coordenada**: as colunas `latitude`/`longitude`/`geo_fonte` e o endpoint já aceitavam geo, e ninguém mandava. Best-effort de propósito: sem permissão, sem sinal ou passando de 5 s, a foto sobe sem coordenada. Registro sem geo é bom; registro que não sobe porque o GPS demorou não serve para nada.

**Corrigido em 26/08/2026 — o que a coordenada descrevia estava errado.** O parágrafo acima dizia "a foto sobe com onde e quando". Não era a foto: era **o navegador**, no instante do envio. Para foto tirada no píer os dois valores coincidem e ninguém nota. Para arquivo vindo do disco, o que ia para o selo era o endereço de quem clicou em enviar.

Apareceu no teste do Dom Rafael: 14 imagens baixadas da internet, todas seladas em **-22.9206, -45.4517**, e o PDF marcando **GEO** ao lado de cada uma. Mesma família do `100%` ao lado do `BRONZE` e do `Nº de Registro` com o nome do barco — o dado existe, e significa outra coisa para quem lê. Num documento que se vende como custódia, é a pior espécie de defeito: não parece defeito.

**A regra agora** (toda em `exif_service.geo_para_selar`, com teste):

| Origem | O que vai para o selo | `geo_fonte` |
|---|---|---|
| Imagem com coordenada dentro (EXIF) | a da imagem — descreve a foto | `exif` |
| Botão **Fotografar** (câmera ao vivo) | a do aparelho — ali é o mesmo lugar | `captura` |
| Arquivo do disco sem EXIF | **nada** | — |

Três decisões que sustentam isso. **A leitura é no servidor**, não no navegador: pega os quatro caminhos de upload de uma vez, e o cliente não consegue mentir sobre o que estava na foto. **A fonte declarada pelo cliente é lista fechada** — só `captura`; o `dispositivo` das versões antigas é descartado, inclusive na janela de deploy, onde uma captura pode perder a coordenada. Perder é barato; selar errado não tem volta, porque `documentos` não aceita UPDATE nem DELETE. **Na dúvida, vazio**: `(0,0)`, latitude fora do mapa, arquivo corrompido, PDF — tudo cai em nada, e nada derruba o upload.

Efeito colateral bom: some um dado pessoal que ninguém pediu. Antes, um funcionário que subisse dez fotos de casa deixava dez registros do endereço dele numa tabela append-only. Agora fica gravado onde a **foto** foi tirada, não onde a **pessoa** estava.

**As 14 linhas erradas continuam lá**, com `geo_fonte = 'dispositivo'` — append-only vale também para o que eu mesmo escrevi errado. São de embarcação de teste (`Dom Rafael (TESTE)`), então não vão para nenhum dossiê real. O rótulo antigo, aliás, ficou útil: distingue o que foi gravado sob a regra velha.

**Aberto:** a **data** tem o mesmo problema em escala menor. O dossiê mostra `uploaded_at` — quando o arquivo subiu, não quando a foto foi tirada. O EXIF traz isso (`DateTimeOriginal`) e a leitura já está feita; falta uma coluna `data_captura`, que é migração. Menor porque a data de upload é uma afirmação verdadeira sobre o arquivo; a coordenada não era.

**Só então as LPs.** O texto sobre custódia entrou nas duas páginas **depois** de a regra existir e ser verificável — não antes. É a lição de duas armadilhas do próprio dia: o rodapé do e-mail prometia um recibo que estava desligado na Stripe, e a etapa 4 do cadastro promete um vídeo que não existe. Página só afirma o que já foi visto funcionando.

**Adiado para depois do lançamento — decisão do Marcos em 26/08/2026:** *"essa função de fotos pelo WhatsApp ficará para depois do lançamento, pq isso requer tempo e trabalho bem tranquilo."*

Não existe nada dela hoje. O webhook do WhatsApp lê texto e age numa única palavra ("SAIR"); foto ele ignora. Para funcionar faltam cinco pedaços: receber a mídia da Evolution, saber de qual embarcação é, guardar numa área de entrada separada, uma tela para o gerente aceitar ou descartar, e a lista de números autorizados a enviar. Um a dois dias — pelo caminho da caixa de entrada, que dispensa o pedaço mais caro (descobrir o barco na hora).

**Não é bloqueio de lançamento.** O botão **Fotografar** já cobre o caso principal: a marina fotografa no píer e a imagem vai direto para o cofre, com data e local. O WhatsApp serve para quem **não tem acesso ao sistema** — armador, terceiro, funcionário sem conta. É comodidade.

E há um argumento de sequência: construir antes de ter marina usando é adivinhar como elas vão querer mandar foto. Com duas ou três marinas reais, isso se descobre em uma semana.

### O desenho da entrada de fotos, para quando chegar a hora (26/08/2026)

Desenho fechado com o Marcos, para que construir depois seja executar e não decidir de novo.

**A ideia é dele, e nestas palavras:** *"um separador e tratamento dessas imagens antes de entrar no sistema — identificação de marina, embarcação, transformá-las em URLs e depois entrar no sistema."*

É uma **sala de espera**: a foto chega, é tratada e identificada, e só entra no cofre quando alguém aceita.

**O que a sala resolve**

| Etapa | Quem faz |
|---|---|
| Identificar a **marina** | automático — o número de quem enviou pertence a uma marina |
| Identificar a **embarcação** | o gerente escolhe; uma marina tem muitos barcos e o sistema não adivinha |
| Encolher a imagem | automático — foto de celular tem 3 a 12 MB, e marina no píer com sinal ruim desiste no meio |
| Ler data e local | automático — a foto já carrega isso, e é informação que ninguém recria depois |
| Aceitar ou descartar | o gerente, num clique |

A marina automática e o barco manual é o recorte que economiza mais trabalho: a foto chega já na caixa certa, e sobra um clique. Exigir código na legenda transfere o esforço para quem envia e produz erro de digitação.

**Por que a sala é obrigatória, e não conveniência.** Se a foto caísse direto em `documentos`, ela inflaria a nota da marina e entraria no PDF selado sem ninguém ter conferido — os dois consumidores (`asset_score_service`, `dossie_data`) leem a tabela inteira, sem filtro. A forma já existe no sistema, em `registros_rascunho` × `registros`. Aceitar é que move para `documentos`, e **aceitar é o selo**.

**Qual número recebe**

```
agora        978138934   o mesmo que envia o código de acesso — já fala só com cliente
mais tarde   número próprio, quando a foto passar o código em volume
nunca        997588791   é o da abordagem comercial
```

O `997588791` faz contato frio com marina que nunca pediu — é o número com maior chance de ser bloqueado, porque bloqueio vem de denúncia de spam. Se a foto entrasse por ele, uma queda levaria junto a prospecção **e** o canal das marinas que já pagam.

O `978138934` é seguro quanto a isso, mas carrega o **login do armador**. O risco lá não é bloqueio, é fila: muita foto ao mesmo tempo pode atrasar um código de acesso. **O gatilho para separar é medível** — quando chegar mais foto do que código por dia.

**Quem pode enviar:** gerente e encarregado da marina, conforme a decisão de custódia acima. Falta no banco o telefone do encarregado — o do gerente já existe.

**Aberto, e é o que quebraria se feito errado:** o material que chega **não pode cair direto em `documentos`**. Hoje estar naquela tabela significa "está no cofre", e os dois consumidores não filtram nada — `asset_score_service:114` e `dossie_data:441` leem tudo. Material não aceito inflaria a nota da marina e entraria no PDF selado. A forma certa já existe no sistema, nos registros: uma tabela de **entrada** separada, e aceitar move para `documentos`. Assim nenhum consumidor muda — `documentos` continua significando o que sempre significou.

### O login não sabia dizer que o e-mail estava torto (25/08/2026)

`simarkobrasil@gmailcom` — faltando o ponto antes do "com". A tela respondeu **"E-mail ou senha incorretos"**, a mesma mensagem de senha errada. O caminho natural de quem lê isso é ir redefinir uma senha que estava certa.

O `type="email"` do navegador **não pega esse caso**: pelo padrão HTML, `alguem@gmailcom` é válido — domínio sem ponto passa.

A conferência de formato passou a rodar **antes** de chamar a API, no login e na redefinição de senha. Na redefinição o estrago era pior: e-mail torto fazia o link sair para um endereço inexistente e a tela ainda respondia *"link enviado, verifique seu e-mail"* — a pessoa esperando uma mensagem que nunca chegaria.

**Por que conferir formato não abre brecha de segurança:** ela não revela se a conta existe. Isso valeria para "este e-mail não está cadastrado", que é enumeração de usuário — e é justamente por isso que essa mensagem não está lá.

Usa o mesmo `emailValido` dos quatro formulários, de `utils/telefone`. É a sexta tela a herdar a regra, e nenhuma tem cópia própria.

Verificado em navegador real: e-mail malformado para na página sem chamar a API; e-mail válido com senha errada segue para o servidor e recebe o erro de credenciais.

### O limite de 4 dossiês morava no navegador (26/08/2026)

A regra é **4 emissões por ano, por embarcação**. Ela vivia inteira no `localStorage`, numa chave por ativo — e por isso não era regra.

Apareceu assim: a Marina Alfa emitiu três dossiês, e as três telas abertas continuaram mostrando **"4/4 restantes"**. Cada navegador conta sozinho.

```
Chrome   emitiu 3   →  anotou   →  mostrou 3 restantes
Edge     nada       →  em branco →  mostra 4 restantes
banco    3 emissões, com hash e hora  ←  ninguém perguntava a ele
```

**Duas consequências, e a segunda é a grave:**

1. O número na tela não era confiável — mudava conforme a janela.
2. **O limite não existia.** Trocar de navegador, limpar os dados do site ou apagar uma chave no console liberava emissão sem fim. `GET /dossie/{id}/pdf` gerava sem perguntar quantos já tinham saído.

**Por que a tela é o conserto, e não só o banco.** O Marcos resumiu: *"internamente pode até ser, mas o gerente sempre verá que ainda tem possibilidade de gerar mais um dossiê"*. Quem decide o que a marina faz é o número exibido — ela lê "ainda pode" e promete o dossiê ao cliente. Banco certo com tela errada é, para quem usa, um sistema errado.

Fechado nas duas pontas:

```
GET /dossie/{id}/saldo   a tela pergunta ao servidor         → o número vira verdade
GET /dossie/{id}/pdf     recusa com 429 acima do limite      → o pedido vira limite
DOSSIE_LIMITE_ANUAL      variável de ambiente (padrão 4)     → sobe durante ensaios,
                                                                sem deploy
```

A recusa diz **até quando**: a vaga abre 12 meses depois da emissão mais antiga ainda na janela. Recusar sem data é pior que recusar — a marina precisa responder ao cliente.

Conferido contra o banco real: os três ativos da Marina Alfa com 1 usado e 3 restantes; os da Amazon Marina com 4/4, porque nunca emitiram. Mesmo número em qualquer navegador.

**O teste achou um defeito enquanto era escrito:** `get_supabase_admin()` estava fora do `try`. Cliente falhando ao ser criado derrubava a **emissão inteira**, não só a contagem — apurar saldo é acessório, gerar o dossiê é o que a marina veio fazer.

**E a regra estava em DUAS telas.** Corrigido o detalhe do ativo (`AtivoHub`), a **listagem** (`SolicitacoesDossie`) continuou mostrando "4/4 restantes" logo depois de emitir — tinha sua própria cópia do mesmo `localStorage`. Sexta vez que a mesma regra vive em dois lugares neste projeto (senha 6/8/10, preço, telefone, categorias, selo em duas línguas, agora o limite). As duas passaram a ler `GET /dossie/{id}/saldo`, e o teto (`4 / Ano`) também vem do servidor — número escrito na tela envelhece calado quando a regra muda.

Enquanto o servidor não responde, os cards mostram **"—"**. O estado inicial era `remaining: 4`, o que fazia a tela afirmar "4 restantes" por um instante antes de saber — a mesma mentira que o conserto elimina, só que mais curta.

### O selo partia a palavra ao meio (26/08/2026)

**"ÍNDICE DE CUSTÓDIA: SILV / ER"** — na primeira página do PDF, logo abaixo do nome da embarcação.

A caixa era um `Table` de **62 mm fixos**. Nenhum dos três graus cabia:

| Selo | Largura necessária | Na caixa de 62 mm |
|---|---|---|
| GOLD | 65,0 mm | 2 linhas |
| SILVER | 69,1 mm | 2 linhas |
| BRONZE | 71,0 mm | 2 linhas |

E a quebra saiu **dentro da palavra** por um motivo contraintuitivo: `track()` usa espaço não-quebrável para produzir o letter-spacing, então o ReportLab não podia quebrar entre as letras — sem ponto de quebra legítimo e sem largura, ele partiu no meio.

Agora **a caixa acompanha o texto**, medido com `stringWidth`, com teto de 150 mm. E o grau sai **2 pt maior** que o rótulo (7 → 9): é ele que se procura na página.

O mesmo tratamento foi para a página pública de verificação (10px → 12px, rótulo e grau com `whitespace-nowrap`), que tinha o mesmo risco — sétima vez que a mesma regra visual precisa existir em dois lugares neste projeto.

### Quatro acertos na capa do dossiê (26/08/2026)

Ajustes pedidos pelo Marcos olhando o PDF pronto — todos de leitura, nenhum de layout por layout.

**Barras finas e iguais.** As duas com 1,5 de espessura. A diferença entre elas segue existindo pela cor, pelo tamanho do número e pela ordem; espessura era redundância que roubava atenção do texto.

**Barras suaves.** A linha sai misturada ao fundo (`blend(cor, NAVY, 0.72)`) — ela indica, não alarma. **O rótulo continua na cor cheia**: letra suavizada junto ficaria ilegível, e é o texto que informa.

**"1 Dia em custódia", não "1 MESES".** O cálculo era `max(1, round(dias / 30.44))` — um dia virava um mês, e o rótulo saía no plural. Agora conta em dias enquanto não fecha 30, com singular e plural corretos. O dia da entrada conta como o primeiro: "0 dias" está certo pelo relógio e parece defeito na tela.

Junto: **custo médio/mês só aparece depois de fechar um mês.** Antes dividia o gasto total por "1 mês" e anunciava tudo como mensalidade.

**A linha "Nº de Registro" some quando não há dado.** Ela caía no nome da embarcação (`rgp or nome_reg`) e repetia "Netuno II (TESTE)" logo abaixo do campo NOME. Num documento que cita LESTA e NORMAM, campo legal preenchido com valor de outro tipo é pior que campo vazio.

### Dois números que se contradiziam na mesma página (26/08/2026)

O dossiê do Netuno II — selo **BRONZE** — trazia logo abaixo **"ÍNDICE DE SEGURANÇA 100%"**, com a barra verde cheia. E, mais abaixo, cinco de oito sistemas marcados **NÃO AVALIADO**.

O número está certo pela fórmula: `_prontidao` tira da média as categorias sem dado (`if st == "na": continue`), então quatro sistemas conformes de quatro avaliados dão 100%. **Certo pela definição e falso para quem lê.** É a mesma armadilha que motivou renomear "Classificação" para "Índice de Custódia": o número dizia uma coisa e era entendido como outra.

A primeira tentativa foi pôr o denominador como legenda da mesma barra. O Marcos propôs melhor: **duas barras**, porque são duas perguntas diferentes.

```
COBERTURA DE VERIFICAÇÃO                     36%     ← varia, escala de cor, mais grossa
4 DE 11 SISTEMAS COM REGISTRO

CONFORMIDADE                                100%     ← quase sempre 100%, dourada, fina
4 SISTEMAS VERIFICADOS
```

A de cima responde *"quanto foi olhado?"*; a de baixo, *"o que foi olhado está bom?"*.

**A ordem é deliberada, e o argumento é dele:** o olho pousa primeiro no topo, e verde é lido como "está tudo bem" antes de qualquer texto ser processado. Com o 100% em cima, o leitor conclui que o barco está íntegro e só depois descobre que sete sistemas nunca foram olhados. A barra que **varia** vem primeiro porque é ela que carrega a informação.

Pelo mesmo motivo a de baixo saiu **dourada em vez de verde** e mais fina: ela é quase sempre 100% — só entra na conta o que tem registro — então não informa nada sozinha e não pode competir por atenção.

```
Netuno II     36%  vermelha   4 de 11
Dom Rafael    73%  âmbar      8 de 11
```

**Regra que fica:** percentual sem denominador promete mais do que mediu. E quando o denominador é informação própria, ele merece indicador próprio — não legenda. Num documento que sustenta preço de ativo, hierarquia visual é conteúdo, não layout.

### O dossiê não olhava o tipo da embarcação (26/08/2026)

O mesmo Netuno II — um Fibrafort Focker 305, **lancha a motor** — saía com a linha **"VELAME & RIGGING · NÃO AVALIADO"**.

`SAUDE_CATEGORIAS` era uma lista fixa de 12, igual para todo mundo. O painel já tratava disso (`AtivoHub.categorias()`: veleiro troca motor por velame, jet ski esconde interior e pintura) e o dossiê não — **oitava vez que a mesma regra existe em dois lugares neste projeto.**

Não é só estética: categoria que nunca poderá ser preenchida vira buraco permanente na conta e faz o barco parecer incompleto por algo que não existe nele.

```
iate · lancha · barco_pesca    11 categorias   sem velame
veleiro                        11 categorias   velame no lugar de motor
jetski                          9 categorias   sem velame, interior nem pintura
tipo desconhecido              cai no barco a motor — nunca inventa velame
```

`categorias_do_tipo()` é agora a fonte única, com quatro testes de regressão. **Fica aberto o mesmo conserto no `asset_score_service`**, que continua contando as 10 fixas — é por isso que um jet ski impecável bate exatamente 90 e nunca sobra folga para o Ouro.

## Acesso ao Dossiê
- **Marina (autenticada)**: opera, edita e sela; acessa o dossiê dos próprios ativos (dados + PDF).
- **Armador (Portal do Proprietário)**: entra com o **próprio e-mail** + código de uso único (e-mail e WhatsApp), enxerga **somente os barcos com o e-mail dele** e **apenas lê**. Nunca usa a conta da marina — do contrário veria a frota inteira dela. O primeiro contato é feito **pela marina**, não pelo sistema.
- **Terceiros (broker/comprador/seguradora)**: pedem por formulário aberto (`POST /dossie/solicitar`) → Yachts Atlas libera manualmente → acesso por página mobile protegida por **senha-mestra**; saídas registradas em `dossie_saidas`.

## Flags de Ambiente
- `ALLOWED_ORIGINS` — CORS (inclui `yachtsatlas.online`).
- `MAINTENANCE_USERNAME/PASSWORD/MASTER_TOKEN`, `MAINTENANCE_BYPASS_ENABLED`, `DOSSIER_MASTER_PASSWORD` — acesso de manutenção/admin (**nunca remover sem confirmação do fundador**).
- `SUPABASE_URL`, `SUPABASE_KEY` (publishable), `SUPABASE_SERVICE_KEY` (secret), `SUPABASE_JWT_SECRET`, `OPENAI_API_KEY`, `STRIPE_*`.
- `SUPABASE_JWT_SECRET` — **não é mais usado por código nenhum** e a chave legada HS256 foi **revogada no Supabase em 23/08/2026** (ver `LUZ-VERMELHA-JWT.md`). A variável segue definida em `config.py` só por compatibilidade; pode sair numa limpeza futura.
- `MAINTENANCE_JWT_SECRET` — assina o crachá do login de manutenção. **Sem fallback de propósito**: faltando a variável, o login de manutenção desliga em vez de voltar a assinar com o segredo vazado. O `MAINTENANCE_MASTER_TOKEN` não passa por aqui e continua abrindo o acesso.
- `VERIFICACAO_SECRET` — assina o QR de autenticidade do dossiê. **Sem ela o código cai no literal de desenvolvimento, que está no repositório público.** Trocar depois de emitir o primeiro dossiê invalida todos os QR já impressos.
- **E-mail (Hostinger, domínio próprio):** `EMAIL_SENDER` (`contato@yachtsatlas.online`), `EMAIL_PASSWORD`, `EMAIL_SMTP_HOST` (`smtp.hostinger.com`), `EMAIL_SMTP_PORT` (465), `EMAIL_REMETENTE_COBRANCA` (alias `cobranca@`).
- **WhatsApp (Evolution):** `WHATSAPP_PROVIDER`, `EVOLUTION_BASE_URL`, `EVOLUTION_INSTANCE` (transacional: código de acesso e cobrança), `EVOLUTION_API_KEY` (token DA instância transacional), `AUTHENTICATION_API_KEY` (chave global do servidor Evolution — só fallback), `DDI_PADRAO`, `WHATSAPP_WEBHOOK_TOKEN`.
- **Prospecção/avisos (instância SEPARADA):** `EVOLUTION_INSTANCE_PROSPECCAO` (`Marinas-Indicadas`) e `EVOLUTION_API_KEY_PROSPECCAO`. Número distinto do transacional de propósito: banimento é por número, e disparo comercial não pode derrubar o login do armador junto. Token da instância = **32 caracteres + 3 hífens = 35 no total**; qualquer caractere a mais (um `+` colado por engano, por exemplo) vira 401 silencioso.
- **Avisos ao fundador:** `ALERTA_WHATSAPP` (número que recebe) e `ALERTA_EMAIL`. **Manter `ALERTA_WHATSAPP` dentro do bloco do WhatsApp**, junto das outras — solta no meio do arquivo ela já se perdeu num deploy (23/08/2026) e ninguém percebeu por horas.

### Por que o aviso não chegou — nunca mais por adivinhação (23/08/2026)

`notificar_fundador` é best-effort por construção: canal mal configurado é **pulado**, não levantado — falhar em avisar não pode derrubar o pagamento que gerou o aviso. O preço disso é um ponto cego: em produção, "a variável sumiu no deploy" fica **idêntico** a "não havia o que avisar". Custou um dia inteiro, com indicações entrando, e-mail chegando e WhatsApp mudo.

Três travas, em `app/services/diagnostico_avisos.py`:

1. **Conferência no boot** — a cada deploy a aplicação confere os dois canais (variáveis + `connectionState` real da instância) e escreve o resultado no log. Falta alguma coisa, sai em **ERROR**, com o nome da variável: o log de deploy é lido de relance, e INFO no meio de cem linhas se perde. Nunca levanta — diagnóstico que derruba o boot é pior que o defeito que ele diagnostica.
2. **`GET /api/v1/admin/diagnostico-avisos`** — sob demanda, com token de admin. Mesma lógica, um módulo só: duas cópias divergem, e a errada é sempre a que ninguém está olhando. Não envia nada; segredos saem mascarados.
3. **Fim do pulo mudo** — `ALERTA_WHATSAPP` vazio agora registra WARNING com o título do aviso que não saiu. Era exatamente ali que morava o silêncio.

Junto: `logging.basicConfig(level=INFO)` em `main.py`. Sem isso o logger raiz ficava em WARNING e todo `logger.info` da aplicação sumia — inclusive o `WhatsApp enviado para ...` do envio bem-sucedido. Sucesso e "nem tentei" tinham a **mesma aparência** no log de produção: nenhuma linha.
- **Links de pagamento:** `STRIPE_LINK_MARINA_FUNDADORA` ($200) e `STRIPE_LINK_MARINA_OFICIAL` ($250) — ambos na conta do CNPJ.
