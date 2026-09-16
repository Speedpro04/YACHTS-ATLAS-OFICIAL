# Yachts Atlas — Product Requirements Document (PRD)

## 1. Visão Geral do Produto

O **Yachts Atlas** é uma infraestrutura de dados e um registro digital imutável para ativos náuticos (iates, lanchas, veleiros, jet-skis). Ele atua como um repositório centralizado onde toda a documentação, histórico de manutenção e certificações do ativo são armazenados de forma segura e com integridade criptográfica.

Recentemente, a plataforma expandiu seu foco para um **modelo B2B2C**, capacitando **Marinas e Clubes Náuticos** a gerenciarem as frotas de seus clientes. Ao centralizar essas informações, o Yachts Atlas não apenas facilita a gestão diária, mas aumenta o valor de revenda do ativo ao garantir um dossiê completo e auditável.

---

## 2. Problema e Solução

### O Problema
Atualmente, a documentação de ativos náuticos é fragmentada e desorganizada (papéis físicos, e-mails, pendrives). Na hora da venda ou do acionamento de seguro, a falta de histórico estruturado resulta em:
- Desvalorização do ativo em 10% a 30%.
- Atrasos na transferência e due diligence.
- Manutenções duplicadas ou esquecidas.

### A Solução
Um ambiente digital onde o proprietário e a Marina podem manter um **histórico único e verificável**. Cada documento inserido recebe um *hash* criptográfico (SHA-256), garantindo sua integridade. O sistema permite gerar um **Dossiê Automático**, provando o histórico de cuidados do barco, aumentando instantaneamente sua liquidez e valor no mercado.

---

## 3. Personas e Casos de Uso

### 3.1. Personas
1. **A Marina / Clube Náutico (B2B):** Precisa gerenciar a frota sob seus cuidados, monitorar os vencimentos de documentos dos clientes e oferecer um serviço de valor agregado premium.
2. **O Proprietário do Ativo (B2C):** Quer proteger seu investimento, ter acesso rápido aos documentos para fiscalização e maximizar o valor de revenda através do Dossiê.
3. **Brokers / Seguradoras:** Interessados na due diligence e validação do risco do ativo, confiando na integridade dos dados gerados.

### 3.2. Casos de Uso Principais
- **Gestão de Frota pela Marina:** Visualização em painel do status de dezenas de iates simultaneamente.
- **Dossier Certification:** A Marina ou o proprietário gera um certificado digital/PDF autenticado compilando todos os dados, vistorias e documentos de um iate antes de sua venda.
- **Validação de Integridade:** Um comprador acessa a plataforma para verificar se o laudo de manutenção não sofreu alterações desde que foi emitido.

---

## 4. Modelo de Negócios e Precificação

O Yachts Atlas atua com diferentes fluxos de receita (Stripe integration):

**1. Assinatura para Marinas (B2B2C):**
- **Plano Marina Standard:** ~$250/mês para gestão de frota, dashboard agregador, API e painel white-label. Permite que a Marina ofereça o sistema aos seus clientes.

**2. Geração de Dossiê / Certificação (Pagamento Avulso):**
Cobrança dinâmica baseada no tamanho do barco (pés):
- **Compact (até 39 pés):** $200
- **Executive (40 a 79 pés):** $400
- **Superyacht (80+ pés):** $600

**3. ROI dos Dossiês (B2B2C):**
- **Regra comercial padrão:** split de receita/ROI dos dossiês em **50/50** entre Yachts Atlas e Marina parceira.

---

## 5. Requisitos Funcionais (Épicos e Histórias)

### Épico 1: Gestão B2B de Marinas
- **RF01:** O sistema deve permitir o cadastro de contas corporativas (Marinas).
- **RF02:** A Marina deve ter um dashboard exibindo métricas da frota gerenciada (total de ativos, pés totais, alertas de documentos vencendo).
- **RF03:** A Marina deve poder convidar (onboarding) proprietários para o ecossistema.
- **RF11:** O sistema deve oferecer um **Checklist de Segurança Digital** para marinheiros.
- **RF12:** O sistema deve gerar **Alertas de Manutenção Preditiva** (motores, extintores, balsas) integrados à agenda da marina.
- **RF14:** A condição de **Marina Fundadora vale enquanto a assinatura estiver ativa** (decidido em 15/09/2026). Cancelar é um movimento de três partes, todas automáticas no webhook da Stripe:
  1. o acesso cai;
  2. a vaga volta para as 4 do estado — ela é o argumento da campanha, e vaga presa por quem já saiu é venda que some do estoque sem ninguém notar;
  3. a conta deixa de ser fundadora. Voltando ao Programa, entra pelo **valor oficial** (US$ 250 / R$ 1.250), não pelo de lançamento.
- **RF34:** O **reajuste do 13º mês sai na moeda da assinatura**: fundadora que paga em real vai de **R$ 1.000 para R$ 1.250**; em dólar, de US$ 200 para US$ 250. Quem executa é a própria Stripe, por cronograma criado no pagamento, na data de cada Marina. Até 16/09/2026 a segunda fase saía fixa em dólar, a Stripe recusava cronograma com duas moedas e o reajuste nunca era agendado — cada fundadora brasileira ficaria em R$ 1.000 para sempre. Moeda sem preço oficial definido **não cai no dólar**: falha e avisa o fundador para agendar na mão. O real existe só na Stripe; o site continua mostrando o preço em dólar.
- **RF13:** Uma Marina deve poder **indicar outra Marina**. A indicada recebe uma abordagem em dois toques — **e-mail primeiro, WhatsApp em seguida** — com o nome de quem indicou, sem preço e com saída explícita ("responda SAIR").
  - O disparo **nunca é automático**: sai por gatilho humano, depois de uma carência e de um ensaio (`dry_run`) que mostra os dois textos antes de qualquer envio. Disparo comercial sem ninguém olhando é o caminho curto para o número ou o domínio serem denunciados.
  - Cada canal tem estado próprio (`email_status`, `whatsapp_status`): um lead pode ter o e-mail entregue e o WhatsApp recusado sem que o lote seguinte repita o que já saiu.
  - O WhatsApp sai pela **instância de prospecção**, nunca pela transacional — que entrega código de acesso e régua de cobrança, e não pode cair junto num ban.

### Épico 2: Gestão de Ativos
- **RF04:** O sistema deve permitir o cadastro de ativos especificando tipo (iate, lancha, etc), marca, modelo, ano de fabricação e comprimento em pés.
- **RF05:** O sistema deve exibir a Classificação do ativo (Bronze, Silver, Gold) com base na completude de suas informações.

### Épico 3: Gestão de Documentos e Integridade
- **RF06:** Usuários e Marinas devem poder fazer upload de documentos e laudos.
- **RF07:** O backend deve gerar um Hash SHA-256 para o arquivo no momento do upload.
- **RF08:** O sistema deve verificar a validade de documentos temporais (ex: seguros) e exibir status (ativo, vencendo, vencido).
- **RF15:** **Selar um serviço aprova as fotos dele, no mesmo ato.** Quem sela é o escritório, com as fotos à vista na mesa de trabalho — selar É a revisão da evidência. Separar os dois atos só garantia que o segundo fosse esquecido, e o serviço ia ao dossiê sem a prova (ensaio de 15/09/2026).
- **RF16:** A **cobertura fotográfica conta apenas o que entra no dossiê.** Foto pendente aparece na galeria — o revisor precisa vê-la — mas não soma na barra, que prometia uma cobertura que o PDF não entregava.
- **RF29:** O **cadastro da embarcação é visível depois de salvo**. Primeiro card do Painel Técnico do ativo, antes de Documentação: **Dados da Embarcação**, com especificações e motorização do barco e nome, CPF/CNPJ (mascarado), e-mail e WhatsApp do proprietário. Até 15/09/2026 o formulário coletava tudo isso e nenhuma tela voltava a mostrar; o e-mail do dono, que é a chave dele para o Portal, não aparecia nem no PDF, e três barcos sem e-mail não davam sinal nenhum de que aqueles donos nunca entrariam. É card, não categoria: não tem registro, não tem estado e **não entra na Conformidade**; o rodapé avisa "Proprietário sem e-mail". Para a Marina, a tela diz se o dono **já visitou o Portal**, quando e quantas vezes.
- **RF32:** A Marina **corrige os dados do proprietário** no próprio card — nome, CPF/CNPJ, e-mail e WhatsApp. O contato muda com o tempo e era só onde o Portal se destrancava: sem e-mail, o dono nunca entra. Apagar o e-mail **desfaz o vínculo** e leva nome, documento e telefone junto (barco vendido não guarda a identidade de quem vendeu); a tela avisa antes, e o botão passa a dizer "Remover vínculo". O documento é **mascarado na entrada** e reenviar o mascarado não o estraga. No Portal do Proprietário não há botão de editar: quem afirma de quem é o barco é a Marina. Editar as **especificações do barco** continua pendente — não existe rota para isso.
- **RF33:** **Transferência de propriedade entra no Dossiê Atlas.** Barco vendido que continua na mesma Marina muda de dono e não muda de histórico — e a seção "02 — Histórico de Proprietários" só se enchia à mão. Ao salvar, a Marina diz o que aconteceu: **correção de cadastro** (e-mail digitado errado) não gera registro nenhum, porque erro de digitação não é elo de cadeia e encheria a prova de ruído; **transferência** grava dois elos — fecha o dono anterior com "até DD/MM/AAAA" e abre o novo com "desde DD/MM/AAAA", junto do tipo (Compra e Venda, Herança, Doação). **O período não é inventado**: a plataforma não sabe quando o dono anterior comprou o barco, só quando ele saiu. Se a Marina já lançou a cadeia à mão, o elo do antigo não é duplicado. Os registros são **imutáveis** como os demais: data errada se corrige por retificação com motivo.
- **RF30:** A visita ao Portal é **medida por nós** (`portal_acessos`), e não pelo Auth. A primeira versão lia `auth.users.last_sign_in_at` e a revisão derrubou por dois motivos: aquele campo guarda a última **validação de código**, e a sessão do navegador se renova sozinha — o dono podia abrir o Portal todo dia e a Marina continuar lendo a data do primeiro acesso; e achar aquela conta exigia **varrer o Auth por e-mail**, o que permitia a uma Marina gravar o e-mail de qualquer pessoa no próprio barco para descobrir se ela tem conta na plataforma, justo o que `/owner/codigo` evita ao responder sempre "enviado". Agora a pergunta é **por ativo**, e falha de banco **não vira "nunca entrou"**: mentir para menos faria a Marina cobrar um cliente que já usa o Portal.
- **RF31:** O **Portal mostra todas as embarcações do dono**, com troca entre elas. Mostrava só a primeira da lista e as outras sumiam sem aviso — quem tem dois barcos na mesma Marina não tinha como chegar no segundo.
- **RF28:** Os cards do **Painel Técnico do Dashboard filtram a frota** pela categoria. Até 15/09/2026 eles mandavam a categoria na navegação e **nenhuma tela lia** — os oito abriam a mesma lista, e a seção prometia "acesso rápido às categorias" entregando "vai para a frota". Não é possível "abrir a categoria" numa lista de dez barcos (categoria vive dentro do ativo); no nível da frota o que faz sentido é filtrar quais embarcações têm registro naquele sistema. O filtro aparece como etiqueta com contagem e saída — filtro invisível faz a Marina achar que perdeu metade da frota. Vazio por filtro tem texto próprio, diferente de frota vazia.
- **RF27:** **Não existe Dossiê Compact, Executive ou Superyacht.** O Dossiê Atlas é ÚNICO; o que varia é o porte (8 faixas, US$ 100 a US$ 1.500) e quais seções se aplicam ao ativo. As três classes viviam num componente que nenhuma tela importava, e de lá tinham vazado para os dados estruturados do site — que anunciavam ao Google três produtos inexistentes, com US$ 600 para 80+ pés onde a tabela real cobra até US$ 1.500. Em 16/09/2026 saiu também a etiqueta da classe nos cards do painel e no banner do Portal: o campo nunca veio do banco, e a tela mostrava COMMON.UNDEFINED num e um retângulo vazio no outro.
- **RF26:** O **Dossiê Atlas não é card do Painel Técnico**. Aquela grade são categorias da embarcação; dossiê é um ato. O botão de emitir fica no **fim** da tela do ativo, depois do conteúdo — emitir é a conclusão de ter olhado o que existe, e cada emissão gasta uma das 4 do ano. O botão dentro do gerador é deliberadamente mais discreto: quem chegou lá já decidiu.
- **RF25:** O produto tem **um nome: Dossiê Atlas**. Dentro do sistema ele era chamado de vinte formas — "Dossiê de Custódia", "Dossiê Criptografado", "Dossiê de Integridade", "relatório Dossiê" — e as únicas três ocorrências de "Dossiê Atlas" estavam na página de venda. É o nome que a Marina repete ao proprietário e ao comprador; chamado de seis jeitos, ela não fixa nenhum. Onde o produto é **nomeado** (menu, abas, títulos, botões de ação) vai o nome completo; onde o contexto já está estabelecido ("saldo", "cobertura") o genérico permanece, porque repetir a marca em cada linha vira eco.
- **RF23:** O painel lista as **emissões de dossiê** — uma linha por emissão, com data, hora, protocolo e a impressão digital do arquivo. Nunca agrupada por embarcação: o mesmo barco pode ser emitido mais de uma vez no mesmo dia, o protocolo identifica a EMBARCAÇÃO (vem igual nas duas linhas), e quem separa é a hora e o hash. Agrupar faria duas emissões legítimas parecerem contagem em dobro.
- **RF24:** A Marina pode **anotar quanto cobrou** por cada emissão, e corrigir depois sem trava. **Não é receita da plataforma**: o dossiê é combinado entre o dono da Marina e o dono do ativo e pago direto na conta dela — 100% é dela. O Atlas guarda o número que ela digitou, para o controle dela; não cobra, não intermedeia e não concilia. O rótulo na tela diz "informado pela Marina", nunca "faturamento". **Faturamento não aparece em tela nenhuma** (decisão de 15/09/2026): exibir dinheiro que não é nosso significaria declarar e pagar imposto sobre receita alheia.
- **RF22:** A **Conformidade do painel e a do dossiê saem da mesma função**. O cabeçalho da embarcação lia um campo que nenhum caminho do backend produzia, e por isso dizia "nenhum sistema avaliado" para toda embarcação — enquanto o PDF da mesma embarcação imprimia "Motor: conforme". Painel e dossiê discordando, e a errada era a tela de todo dia.
- **RF21:** **Órfã é a foto sem registro em lugar nenhum.** O serviço vive em três estados — na fila do Pré-Data, na mesa, e selado — e a foto é dele nos três. A mesa só enxergava o do meio, então foto de serviço ainda na fila e foto de serviço já selado eram as duas anunciadas como "sem registro que as explique", com o registro visível na aba ao lado.
- **RF20:** **Selado sai da mesa de trabalho** — imagem e texto. A mesa mostra o que espera trabalho; serviço selado virou prova e mora no Painel Técnico e no dossiê. "Órfã" passa a significar foto sem registro em lugar nenhum — nem rascunho, nem selo —, e não apenas "não achei o rascunho", que era verdade para toda foto de serviço recém-selado.
- **RF19:** A foto é arquivada na **categoria da galeria**, traduzida na escrita. A ficha organiza o serviço (`casco`) e a galeria organiza a foto (`casco_exterior`); onde os dois nomes divergem, a foto caía em "Outros" — e o painel e o dossiê passavam a discordar sobre a mesma imagem. Um teste lê as fichas do frontend e exige que cada uma tenha prateleira na galeria.
- **RF18:** As telas de revisão desenham **miniatura**, não o original. A foto sobe sem compressão e continua sendo a prova (decisão 3.3 do PRD do Atlas Pré-Data); a miniatura é derivada, tem caminho próprio (`<caminho>.mini.jpg`), nunca é hasheada e não entra no dossiê. Sem ela, conferir três fotos de um serviço custava 10 MB de download por visita.
- **RF17:** O dossiê **imprime todo campo preenchido na ficha**, com o rótulo que a Marina viu no formulário. A grade fixa por categoria cobre os principais; o restante entra logo abaixo. Campo preenchido que não chega ao documento é trabalho jogado fora.

### Épico 4: Geração de Dossiês de Certificação
- **RF09:** O sistema deve calcular o preço da geração do dossiê baseado no comprimento em pés do ativo cadastrado.
- **RF10:** Após o pagamento (checkout via Stripe), o sistema deve compilar os dados do ativo, documentos, linha do tempo e hashes em um relatório PDF premium.

---

## 6. Requisitos Não-Funcionais

- **RNF01 (Segurança):** Todos os uploads devem passar por verificação. O sistema deve aderir ao OWASP Top 10 e os dados sensíveis devem ser encriptados no banco de dados.
- **RNF02 (Integridade):** A verificação de hashes de arquivos deve ocorrer em tempo de execução para atestar "nenhuma adulteração".
- **RNF03 (Performance):** A renderização inicial do dashboard das Marinas deve ocorrer em menos de 2 segundos.
- **RNF04 (Integração de Pagamentos):** Transações financeiras e gestão de assinaturas não serão feitas no banco local, delegando-se a conformidade PCI-DSS ao provedor Stripe.

---

## 7. Arquitetura e Stack Tecnológica

O sistema utiliza uma arquitetura moderna distribuída em microsserviços/serviços desacoplados:

- **Frontend:** React + Vite, Tailwind CSS (Design system premium focado em UX).
- **Backend:** Python + FastAPI (Alta performance, tipagem forte, assíncrono).
- **Banco de Dados:** Supabase (PostgreSQL) para dados relacionais e gerenciamento de permissões (RLS - Row Level Security).
- **Storage:** Supabase Storage para armazenamento de arquivos e imagens.
- **Autenticação:** Supabase Auth (Suporte a B2B/B2C tokens).
- **Pagamentos:** Stripe Checkout.
- **Infraestrutura / Deploy:** Docker gerenciado via EasyPanel.

---

## 8. Cronograma e Fases de Lançamento (Roadmap)

- **Fase 1 (MVP - Concluído/Atual):** Cadastro de ativos, upload de documentos, hash SHA-256, login, dashboard básico.
- **Fase 2 (B2B Pivot):** Implementação de perfis de Marina, dashboard de métricas de frota, precificação dinâmica por pés.
- **Fase 3 (Monetização e Escala):** Checkout Stripe da geração de dossiês premium ($200/$400/$600), envio automático de alertas e expansão de parcerias white-label.

---

**Autor:** Equipe de Produto Yachts Atlas  
**Data:** Maio de 2026  
**Status:** Rascunho / Em validação
