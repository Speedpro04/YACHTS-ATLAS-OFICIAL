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

**Feito em 25/08/2026 — a câmera do celular ligada.** O `SecureCameraUpload` existia completo, com `capture="environment"` (abre a câmera traseira), e **nenhum arquivo o importava**. Quinto caso do mesmo padrão no mesmo dia: componente pronto, caminho morto. Plugado no cabeçalho do ativo (`AtivoHub`), como botão **Fotografar**, e escondido quando `readOnly` — que é o Portal do Proprietário. A regra de custódia deixa de ser combinado e passa a ser o que a tela faz.

Junto foi a **coordenada**: as colunas `latitude`/`longitude`/`geo_fonte` e o endpoint já aceitavam geo, e ninguém mandava. Agora a foto sobe com onde e quando — dado que ninguém reconstrói depois. Best-effort de propósito: sem permissão, sem sinal ou passando de 5 s, a foto sobe sem coordenada. Registro sem geo é bom; registro que não sobe porque o GPS demorou não serve para nada.

**Só então as LPs.** O texto sobre custódia entrou nas duas páginas **depois** de a regra existir e ser verificável — não antes. É a lição de duas armadilhas do próprio dia: o rodapé do e-mail prometia um recibo que estava desligado na Stripe, e a etapa 4 do cadastro promete um vídeo que não existe. Página só afirma o que já foi visto funcionando.

**Adiado para depois do lançamento — decisão do Marcos em 26/08/2026:** *"essa função de fotos pelo WhatsApp ficará para depois do lançamento, pq isso requer tempo e trabalho bem tranquilo."*

Não existe nada dela hoje. O webhook do WhatsApp lê texto e age numa única palavra ("SAIR"); foto ele ignora. Para funcionar faltam cinco pedaços: receber a mídia da Evolution, saber de qual embarcação é, guardar numa área de entrada separada, uma tela para o gerente aceitar ou descartar, e a lista de números autorizados a enviar. Um a dois dias — pelo caminho da caixa de entrada, que dispensa o pedaço mais caro (descobrir o barco na hora).

**Não é bloqueio de lançamento.** O botão **Fotografar** já cobre o caso principal: a marina fotografa no píer e a imagem vai direto para o cofre, com data e local. O WhatsApp serve para quem **não tem acesso ao sistema** — armador, terceiro, funcionário sem conta. É comodidade.

E há um argumento de sequência: construir antes de ter marina usando é adivinhar como elas vão querer mandar foto. Com duas ou três marinas reais, isso se descobre em uma semana.

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
