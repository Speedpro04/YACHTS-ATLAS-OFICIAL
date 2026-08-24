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
4. **Privacidade do bucket `media`** — hoje é público; mover documentos sensíveis p/ bucket privado + URL assinada (LGPD).
5. **Soft-delete de ativo** — para imutabilidade **total** (hoje DELETE de ativo apaga registros em cascata).
6. **`audit_logs`** — insert está falhando por RLS (`42501`); ajustar policy para a auditoria gravar de fato.
7. **Higiene de repositório** — imagens grandes (6–12 MB) e arquivos avulsos na raiz; duas cópias locais do repo (com/sem "H").
8. **Portar dossiê premium p/ produção** — o layout premium hoje está só no kit local (`dossie-exemplo/`); levar para `dossie_pdf.py` quando aprovado.
9. **Traduzir os modelos de e-mail do Supabase** — ainda em inglês ("Reset Your Password"). Marca brasileira mandando e-mail em inglês com link de senha é padrão clássico de phishing, e pesou no spam junto com o DKIM que faltava.
10. **Validar o `verifyOtp` do Portal do Proprietário** contra a Supabase real — é o único ponto do fluxo que não dá para testar sem conta de verdade.
11. **Limite de 4 dossiês/ano existe só no frontend** — sem checagem no servidor. Vira regra de verdade quando o 5º dossiê passar a ser cobrado.
12. **Suporte humano é estratégia enquanto forem 20–40 marinas** — a Solara responde o "onde"; o fundador responde o "por quê". Automatizar o resto cedo demais deixa surdo o sinal que corrige a interface. Revisar quando a mesma pergunta chegar 20 vezes ou a resposta demorar mais de um dia.
13. **`alertas.py` órfão** — endpoints de alerta de vencimento sem ninguém chamando, protegidos por admin (cron externo não alcança), sem idempotência e enviando para e-mail fixo. Remover ou reescrever no padrão do `cron_cobranca`.
14. **Decidir o que a nota do ativo significa** — hoje ela mede volume de cadastro, não saúde: o Marlin Sea teve um rombo, ficou interditado, e pontua 87 (Ouro). A escala também é pouco discriminante (preencher tudo uma vez já dá 83). Renomear para *Índice de Custódia* — coerente com o fato de a plataforma **não inspecionar** — ou fazer a nota penalizar atenção, sinistro em aberto e documento vencido.
15. **Marina não consegue cancelar sozinha** — não há botão no painel; hoje ela pede por e-mail/WhatsApp. Decisão consciente enquanto forem 20 marinas.
16. ~~**Opt-out da prospecção**~~ — **resolvido em 22/08/2026** (`api/v1/whatsapp.py`). Falta apenas apontar o webhook na Evolution, na instância `Marinas-Indicadas`, evento `MESSAGES_UPSERT`.
17. **Vínculo da indicação depende de digitação** — quem indica escreve o nome da própria marina em campo livre (`marina_leads.source`). O casamento com a indicante é manual, como já era no cadastro. Vira problema quando o volume passar de algumas dezenas.
18. **Scheduler de 24/48h para indicação não contatada** — proposto e adiado por ordem, não por mérito: ele precisa saber se a marina **já foi contatada**, e contato manual não registra nada hoje. Alarme que cobra por lead já resolvido é alarme que se aprende a ignorar. O estado vira automático quando o disparo funcionar (`whatsapp_status = 'enviado'`) — fazer depois do item 16.
19. **Oficial não valida formato de e-mail no navegador** — só checa se está preenchido; quem recusa é o `EmailStr` do backend, e a marina vê "Erro ao enviar" sem saber que o problema é o e-mail. O Lançamento já valida com mensagem específica.

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

Detalhes que importam: o IP vem do `X-Forwarded-For` (atrás do nginx, `request.client.host` é sempre o IP interno — o limitador trataria o mundo como um visitante só e bloquearia todos ao primeiro abuso); há teto de chaves em memória (atacante variando IP não pode virar vazamento); e Redis caindo **cai na memória**, nunca abre o portão.

Junto: **senha-mestra incorreta agora vira linha em `audit_logs`**. O limite *barra* a força bruta; a trilha é o que a torna *visível* — sem ela, mil tentativas e nenhuma tentativa têm a mesma aparência depois do fato.

Coberto por `tests/test_limite_taxa.py` (8 testes), incluindo o caso que originou tudo: **sem Redis, ainda limita**.

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
