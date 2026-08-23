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
3. **`VERIFICACAO_SECRET` em produção (BLOQUEIA O LANÇAMENTO)** — sem ele o código cai no literal de desenvolvimento, que está no repositório público. **Verificado em 21/08: produção aceitou uma assinatura forjada com esse literal** — qualquer um pode fabricar um dossiê falso com QR que valida. Configurar **antes do primeiro dossiê**; trocar depois invalida todo QR já emitido.
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

## Acesso ao Dossiê
- **Marina (autenticada)**: opera, edita e sela; acessa o dossiê dos próprios ativos (dados + PDF).
- **Armador (Portal do Proprietário)**: entra com o **próprio e-mail** + código de uso único (e-mail e WhatsApp), enxerga **somente os barcos com o e-mail dele** e **apenas lê**. Nunca usa a conta da marina — do contrário veria a frota inteira dela. O primeiro contato é feito **pela marina**, não pelo sistema.
- **Terceiros (broker/comprador/seguradora)**: pedem por formulário aberto (`POST /dossie/solicitar`) → Yachts Atlas libera manualmente → acesso por página mobile protegida por **senha-mestra**; saídas registradas em `dossie_saidas`.

## Flags de Ambiente
- `ALLOWED_ORIGINS` — CORS (inclui `yachtsatlas.online`).
- `MAINTENANCE_USERNAME/PASSWORD/MASTER_TOKEN`, `MAINTENANCE_BYPASS_ENABLED`, `DOSSIER_MASTER_PASSWORD` — acesso de manutenção/admin (**nunca remover sem confirmação do fundador**).
- `SUPABASE_URL`, `SUPABASE_KEY` (publishable), `SUPABASE_SERVICE_KEY` (secret), `SUPABASE_JWT_SECRET`, `OPENAI_API_KEY`, `STRIPE_*`.
- `VERIFICACAO_SECRET` — assina o QR de autenticidade do dossiê. **Sem ela o código cai no literal de desenvolvimento, que está no repositório público.** Trocar depois de emitir o primeiro dossiê invalida todos os QR já impressos.
- **E-mail (Hostinger, domínio próprio):** `EMAIL_SENDER` (`contato@yachtsatlas.online`), `EMAIL_PASSWORD`, `EMAIL_SMTP_HOST` (`smtp.hostinger.com`), `EMAIL_SMTP_PORT` (465), `EMAIL_REMETENTE_COBRANCA` (alias `cobranca@`).
- **WhatsApp (Evolution):** `WHATSAPP_PROVIDER`, `EVOLUTION_BASE_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE`, `DDI_PADRAO`.
- **Avisos ao fundador:** `ALERTA_WHATSAPP` (número que recebe), `ALERTA_EMAIL`.
- **Links de pagamento:** `STRIPE_LINK_MARINA_FUNDADORA` ($200) e `STRIPE_LINK_MARINA_OFICIAL` ($250) — ambos na conta do CNPJ.
