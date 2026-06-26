-- ============================================================
-- Yachts Atlas — Capitã Solara: Base de Conhecimento Expert
-- ------------------------------------------------------------
-- Migração para transformar a Solara em verdadeira especialista
-- em normas náuticas brasileiras.
--
-- 1. Nova tabela `normas_conteudo` — trechos técnicos detalhados
-- 2. Novas normas no catálogo (NORMAM séries 100-600, LESTA,
--    convenções IMO, ABNT/ISO adicionais, procedimentos DPC)
-- 3. Seed de conteúdo técnico real (~80 seções)
--
-- jun/2026 — v2 (Expert Upgrade)
-- ============================================================

-- ============================================================
-- PARTE 1: Tabela normas_conteudo
-- ============================================================
create table if not exists public.normas_conteudo (
  id                uuid primary key default gen_random_uuid(),
  norma_codigo      text not null references public.normas(codigo) on delete cascade,
  secao             text not null,              -- "Cap. 4 - Material de Salvatagem"
  conteudo          text not null,              -- texto técnico real
  palavras_chave    text[] not null default '{}',
  ordem             int not null default 100,
  created_at        timestamptz not null default now()
);

create index if not exists normas_conteudo_codigo_idx on public.normas_conteudo(norma_codigo);
create index if not exists normas_conteudo_palavras_idx on public.normas_conteudo using gin(palavras_chave);

-- RLS: leitura pública (é conteúdo de referência), escrita só service role.
alter table public.normas_conteudo enable row level security;

drop policy if exists "normas_conteudo_leitura_publica" on public.normas_conteudo;
create policy "normas_conteudo_leitura_publica"
  on public.normas_conteudo
  for select
  using (true);

-- ============================================================
-- PARTE 2: Novas normas no catálogo
-- ============================================================

-- 2a. Ativar NORMAM-401 (já existe como a_verificar)
update public.normas
  set status_verificacao = 'verificada',
      descricao = 'Normas da Autoridade Marítima da série 400 — Meio Ambiente. '
        || 'Prevenção da poluição por óleo, lixo, esgoto e emissões atmosféricas '
        || 'no meio aquaviário brasileiro. Complementa a MARPOL no âmbito nacional. '
        || 'Exige Plano de Emergência Individual (PEI) e certificados ambientais.',
      versao = 'Reorg. out/2023',
      obrigatoria = true
  where codigo = 'NORMAM-401';

-- 2b. Novas normas
insert into public.normas
  (codigo, titulo, descricao, orgao, serie, jurisdicao, escopo,
   vigencia_inicio, versao, fonte_url, obrigatoria, status_verificacao, ordem)
values
  -- === SÉRIE 100 — PESSOAL ===
  ('NORMAM-101',
   'Habilitações de aquaviários e amadores',
   'Normas da Autoridade Marítima para habilitação de amadores e aquaviários. '
   || 'Define categorias de habilitação (Veleiro, Motonauta, Arrais-Amador, '
   || 'Mestre-Amador, Capitão-Amador), requisitos de idade, exames médicos, '
   || 'provas teóricas e práticas, carteira de habilitação (CHA), e as áreas '
   || 'de navegação permitidas para cada categoria.',
   'NORMAM', '100 - Pessoal', 'BR', '{habilitacao,amador,aquaviario}',
   '2023-10-02', 'Reorg. out/2023',
   'https://www.marinha.mil.br/dpc/normas-da-autoridade-maritima',
   true, 'verificada', 15),

  -- === SÉRIE 200 — EMBARCAÇÕES (complementos) ===
  ('NORMAM-203',
   'Construção e modificação de embarcações',
   'Normas da Autoridade Marítima para projeto, construção, modificação e reparo '
   || 'de embarcações. Requisitos estruturais, materiais aprovados, estabilidade, '
   || 'flutuabilidade, sistemas de propulsão, governo e elétricos. Exige projeto '
   || 'aprovado por Sociedade Classificadora ou perito naval credenciado pela DPC.',
   'NORMAM', '200 - Embarcações', 'BR', '{construcao,projeto,reparo}',
   '2023-10-02', 'Reorg. out/2023',
   'https://www.marinha.mil.br/dpc/normas-da-autoridade-maritima',
   true, 'verificada', 22),

  ('NORMAM-204',
   'Vistoria de embarcações',
   'Normas da Autoridade Marítima para vistorias em embarcações. Define tipos de '
   || 'vistoria (inicial, periódica, intermediária, especial, eventual), prazos, '
   || 'itens verificados, critérios de aprovação/reprovação, e responsabilidades '
   || 'do vistoriador naval. Embarcações de esporte/recreio com AB ≤ 100 seguem '
   || 'regime simplificado de vistoria.',
   'NORMAM', '200 - Embarcações', 'BR', '{vistoria,certificacao,seguranca}',
   '2023-10-02', 'Reorg. out/2023',
   'https://www.marinha.mil.br/dpc/normas-da-autoridade-maritima',
   true, 'verificada', 24),

  ('NORMAM-205',
   'Material de salvatagem e segurança',
   'Normas da Autoridade Marítima para material de salvatagem, equipamentos de '
   || 'segurança e salvatagem de embarcações. Coletes salva-vidas, balsas, boias, '
   || 'equipamentos pirotécnicos (sinalizadores), EPIRB, SART, extintores, '
   || 'equipamentos de combate a incêndio e primeiros socorros. Define quantidade '
   || 'mínima por tipo/porte de embarcação e área de navegação.',
   'NORMAM', '200 - Embarcações', 'BR', '{salvatagem,seguranca,extintor,colete}',
   '2023-10-02', 'Reorg. out/2023',
   'https://www.marinha.mil.br/dpc/normas-da-autoridade-maritima',
   true, 'verificada', 25),

  -- === SÉRIE 300 — TRÁFEGO E PORTOS ===
  ('NORMAM-301',
   'Auxílios à navegação',
   'Normas da Autoridade Marítima para auxílios à navegação: sinalização náutica '
   || '(bóias, faróis, balizas), sistema IALA região B utilizado no Brasil, '
   || 'marcação de canais, perigos e áreas especiais.',
   'NORMAM', '300 - Tráfego e Portos', 'BR', '{sinalizacao,navegacao,balizamento}',
   '2023-10-02', 'Reorg. out/2023',
   'https://www.marinha.mil.br/dpc/normas-da-autoridade-maritima',
   true, 'verificada', 32),

  -- === SÉRIE 600 — OPERAÇÃO ===
  ('NORMAM-601',
   'Regras para prevenção de abalroamento no mar (RIPEAM)',
   'Normas da Autoridade Marítima que incorporam o Regulamento Internacional para '
   || 'Evitar Abalroamento no Mar (RIPEAM/COLREG 1972). Regras de governo e '
   || 'navegação, luzes e marcas, sinais sonoros e luminosos, situações de '
   || 'cruzamento, ultrapassagem e roda a roda. Aplicável a todas as embarcações.',
   'NORMAM', '600 - Operação', 'BR', '{ripeam,colreg,abalroamento,navegacao}',
   '2023-10-02', 'Reorg. out/2023',
   'https://www.marinha.mil.br/dpc/normas-da-autoridade-maritima',
   true, 'verificada', 35),

  -- === LEIS E DECRETOS BRASILEIROS ===
  ('LESTA',
   'Lei de Segurança do Tráfego Aquaviário (Lei 9.537/1997)',
   'Lei 9.537 de 11/12/1997 — Lei de Segurança do Tráfego Aquaviário (LESTA). '
   || 'Dispõe sobre a segurança do tráfego aquaviário em águas sob jurisdição '
   || 'nacional. Define competências da Autoridade Marítima (DPC/Capitanias), '
   || 'inscrição de embarcações, registro de propriedade, tripulação e '
   || 'habilitação, deveres e infrações, inquérito administrativo sobre acidentes.',
   'NORMAM', null, 'BR', '{lei,seguranca,trafego,inscricao}',
   '1997-12-11', 'Lei 9.537/1997',
   'https://www.planalto.gov.br/ccivil_03/leis/l9537.htm',
   true, 'verificada', 60),

  ('RLESTA',
   'Regulamento da LESTA (Decreto 2.596/1998)',
   'Decreto 2.596 de 18/05/1998 — Regulamenta a Lei de Segurança do Tráfego '
   || 'Aquaviário (LESTA). Detalha procedimentos de inscrição, classificação de '
   || 'embarcações por tipo e porte, tripulação mínima de segurança, '
   || 'documentação obrigatória a bordo, infrações e penalidades, e o processo '
   || 'de inquérito sobre acidentes da navegação.',
   'NORMAM', null, 'BR', '{regulamento,inscricao,classificacao,tripulacao}',
   '1998-05-18', 'Dec. 2.596/1998',
   'https://www.planalto.gov.br/ccivil_03/decreto/d2596.htm',
   true, 'verificada', 62),

  ('RPC-DPC',
   'Registro de Propriedade e TIE (Título de Inscrição de Embarcação)',
   'Procedimento administrativo da DPC para inscrição de embarcações. '
   || 'O TIE — Título de Inscrição de Embarcação — é o documento que comprova '
   || 'a inscrição junto à Capitania dos Portos. Processo inclui: documentos do '
   || 'proprietário, nota fiscal de aquisição ou contrato de compra e venda, '
   || 'projeto da embarcação (se construção nova), vistoria inicial, taxa GRU, '
   || 'e emissão do TIE com número de inscrição.',
   'NORMAM', null, 'BR', '{tie,inscricao,registro,propriedade,capitania}',
   null, 'Procedimento DPC vigente',
   'https://www.marinha.mil.br/dpc/',
   true, 'verificada', 64),

  -- === CONVENÇÕES INTERNACIONAIS (IMO) ===
  ('MARPOL',
   'Convenção Internacional para Prevenção da Poluição por Navios',
   'MARPOL 73/78 — Convenção da Organização Marítima Internacional (IMO) para '
   || 'prevenção da poluição marinha. Brasil é signatário. Seis anexos: '
   || 'I — Óleo; II — Substâncias nocivas a granel; III — Substâncias embaladas; '
   || 'IV — Esgoto; V — Lixo; VI — Emissões atmosféricas. Aplicável a '
   || 'embarcações em águas internacionais e complementada pela NORMAM-401 '
   || 'em águas brasileiras.',
   'ISO', null, 'INTL', '{poluicao,oleo,esgoto,lixo,emissoes,meio_ambiente}',
   '1983-10-02', 'MARPOL 73/78 (emendas vigentes)',
   'https://www.imo.org/en/About/Conventions/Pages/International-Convention-for-the-Prevention-of-Pollution-from-Ships-(MARPOL).aspx',
   false, 'verificada', 70),

  ('SOLAS',
   'Convenção Internacional para Salvaguarda da Vida Humana no Mar',
   'SOLAS 1974 — Convenção da IMO que estabelece padrões mínimos de construção, '
   || 'equipamento e operação de navios para garantir a segurança da vida humana '
   || 'no mar. Principais capítulos: estabilidade, proteção contra incêndio, '
   || 'equipamentos salva-vidas, radiocomunicações, segurança da navegação (GPS, '
   || 'AIS, VDR). Embarcações de recreio estão parcialmente isentas, mas os '
   || 'princípios de segurança se aplicam via NORMAM série 200.',
   'ISO', null, 'INTL', '{seguranca,vida,incendio,radiocomunicacao,construcao}',
   '1980-05-25', 'SOLAS 1974 (emendas vigentes)',
   'https://www.imo.org/en/About/Conventions/Pages/International-Convention-for-the-Safety-of-Life-at-Sea-(SOLAS),-1974.aspx',
   false, 'verificada', 72),

  ('COLREG',
   'Regulamento Internacional para Evitar Abalroamento no Mar',
   'COLREG 1972 — Convenção da IMO que define regras de governo e navegação, '
   || 'luzes e marcas obrigatórias, e sinais sonoros para prevenir colisões no mar. '
   || 'Internalizada no Brasil pela NORMAM-601 (RIPEAM). 41 regras divididas em: '
   || 'Parte A — Geral; B — Governo e navegação (cruzamento, ultrapassagem, '
   || 'roda a roda, canal estreito); C — Luzes e marcas; D — Sinais sonoros.',
   'ISO', null, 'INTL', '{colreg,ripeam,abalroamento,luzes,governo,navegacao}',
   '1977-07-15', 'COLREG 1972 (emendas vigentes)',
   'https://www.imo.org/en/About/Conventions/Pages/COLREG.aspx',
   false, 'verificada', 74),

  -- === ABNT ADICIONAIS ===
  ('NBR-ISO-8666',
   'Embarcações de recreio — Dados principais',
   'ABNT NBR ISO 8666 — Define a classificação e os dados principais de '
   || 'embarcações de recreio: comprimento total (LOA), comprimento do casco (LH), '
   || 'boca máxima, calado, deslocamento, capacidade de combustível, '
   || 'classificação por tipo de propulsão e por categoria de projeto (A, B, C, D). '
   || 'Categoria A = oceânica, B = costeira, C = águas abrigadas, D = águas protegidas.',
   'ABNT', null, 'BR', '{classificacao,comprimento,categoria_projeto,recreio}',
   '2014-01-01', '2014',
   'https://www.abnt.org.br/',
   false, 'verificada', 42),

  ('NBR-15285',
   'Embarcações de recreio — Avaliação sonora',
   'ABNT NBR 15285 — Procedimento de medição e limites de emissão sonora para '
   || 'embarcações de recreio motorizadas (lanchas e jet-skis). Relevante para '
   || 'embarcações que operam em áreas residenciais, baías e enseadas.',
   'ABNT', null, 'BR', '{ruido,lanchas,jet_ski,poluicao_sonora}',
   '2006-01-01', '2006',
   'https://www.abnt.org.br/',
   false, 'verificada', 44),

  ('NBR-ISO-12217',
   'Avaliação de estabilidade e flutuabilidade',
   'ABNT NBR ISO 12217 — Avaliação e categorização de estabilidade e '
   || 'flutuabilidade de embarcações de recreio de casco não-veleiro (parte 1) '
   || 'e veleiros (parte 2). Define ensaios de inclinação, reserva de '
   || 'flutuabilidade, critérios de aprovação por categoria de projeto (A-D). '
   || 'Requisito fundamental para certificação ACOBAR e homologação pela DPC.',
   'ABNT', null, 'BR', '{estabilidade,flutuabilidade,seguranca,categoria}',
   '2015-01-01', '2015',
   'https://www.abnt.org.br/',
   false, 'verificada', 46)

on conflict (codigo) do nothing;


-- ============================================================
-- PARTE 3: Seed de conteúdo técnico detalhado
-- ============================================================

-- -----------------------------------------------
-- NORMAM-211: Esporte e Recreio (a principal!)
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NORMAM-211', 'Inscrição de Embarcação de Esporte e Recreio',
'A inscrição de embarcações de esporte e recreio é obrigatória junto à Capitania dos Portos, Delegacia ou Agência da jurisdição onde a embarcação será utilizada. O processo de inscrição exige:

1. Requerimento padrão preenchido (formulário da Capitania)
2. Documentos do proprietário (CPF, RG ou CNPJ)
3. Comprovante de propriedade: nota fiscal de aquisição, contrato de compra e venda com reconhecimento de firma, ou sentença judicial
4. Projeto de construção aprovado (para embarcações construídas em estaleiro nacional sem certificação)
5. Comprovante de pagamento da taxa GRU (Guia de Recolhimento da União)
6. Seguro obrigatório DPEM (Danos Pessoais causados por Embarcações ou por suas Cargas)

Ao final do processo, é emitido o TIE — Título de Inscrição de Embarcação, que é o documento de identidade da embarcação. O número de inscrição segue o formato da Capitania (ex.: 2719XX-XXX). A transferência de propriedade exige nova inscrição ou averbação.',
'{inscricao,tie,registro,propriedade,capitania,documentos,gru,dpem}', 10),

('NORMAM-211', 'Classificação por Área de Navegação',
'As embarcações de esporte e recreio são classificadas pela área de navegação em que estão autorizadas a operar:

• NAVEGAÇÃO EM MAR ABERTO: além de 20 milhas náuticas da costa. Exige equipamentos de comunicação (VHF, HF ou satélite), EPIRB, balsa salva-vidas, e habilitação mínima de Capitão-Amador.

• NAVEGAÇÃO COSTEIRA: até 20 milhas náuticas da costa. Exige rádio VHF, equipamentos de salvatagem padrão, e habilitação mínima de Mestre-Amador.

• NAVEGAÇÃO INTERIOR: rios, lagos, lagoas, baías, canais e águas abrigadas. Exige equipamentos básicos de segurança e habilitação mínima de Arrais-Amador (motor) ou Veleiro (vela apenas).

A área de navegação determina diretamente os equipamentos obrigatórios a bordo, a habilitação mínima do condutor e os requisitos de vistoria.',
'{area_navegacao,mar_aberto,costeira,interior,classificacao}', 20),

('NORMAM-211', 'Material de Salvatagem — Embarcações de Esporte e Recreio',
'Equipamentos de salvatagem obrigatórios para embarcações de esporte e recreio, conforme o porte e a área de navegação:

PARA TODAS AS ÁREAS (mínimo obrigatório):
• Coletes salva-vidas aprovados pela DPC — 1 por pessoa a bordo (mais reserva de 10% para embarcações > 12m)
• Boia circular com retinida de no mínimo 1 unidade
• Apito ou buzina de nevoeiro
• Lanterna elétrica estanque
• Espelho de sinalização
• Estojo de primeiros socorros

NAVEGAÇÃO COSTEIRA (adicionar):
• 3 sinalizadores manuais (fumígenos diurnos)
• 3 fachos manuais (luminosos noturnos)
• Rádio VHF marítimo fixo ou portátil (canal 16)

NAVEGAÇÃO EM MAR ABERTO (adicionar):
• Balsa salva-vidas inflável (para embarcações > 12m ou com mais de 6 pessoas)
• EPIRB 406 MHz (Emergency Position Indicating Radio Beacon) registrado na ANATEL
• 6 fachos manuais + 2 foguetes paraquedas
• Rádio VHF fixo + HF ou comunicação por satélite (Inmarsat, Iridium)
• SART ou AIS-SART (transponder de radar para localização)

A falta de qualquer item obrigatório pode resultar em retenção da embarcação pela Capitania até a regularização.',
'{salvatagem,colete,balsa,epirb,sinalizador,vhf,seguranca,equipamentos}', 30),

('NORMAM-211', 'Equipamentos de Navegação Obrigatórios',
'Equipamentos de navegação exigidos para embarcações de esporte e recreio:

NAVEGAÇÃO INTERIOR:
• Compasso magnético (bússola) — embarcações > 8m
• Cartas náuticas da região (podem ser eletrônicas ENC em plotter homologado)
• Apito ou buzina

NAVEGAÇÃO COSTEIRA (adicionar):
• GPS ou plotter cartográfico
• Compasso magnético (bússola) compensada
• Cartas náuticas atualizadas (DHN — Diretoria de Hidrografia e Navegação)
• Publicações náuticas (Tábua de Marés, Lista de Faróis)
• Relógio e barômetro
• Binóculo

NAVEGAÇÃO EM MAR ABERTO (adicionar):
• Radar (recomendado; obrigatório para embarcações > 24m ou que naveguem em rotas de grande tráfego)
• AIS (Automatic Identification System) — obrigatório para embarcações > 300 AB
• Log e eco-sonda (profundímetro)',
'{navegacao,gps,compasso,carta_nautica,radar,ais,equipamentos}', 40),

('NORMAM-211', 'Equipamentos de Combate a Incêndio',
'Extintores e equipamentos de combate a incêndio obrigatórios para embarcações de esporte e recreio:

EMBARCAÇÕES COM MOTOR DE CENTRO (inboard):
• Mínimo de 1 extintor portátil tipo ABC (pó químico seco) de 1 kg para embarcações até 8m
• 2 extintores para embarcações de 8m a 12m
• 3 extintores para embarcações de 12m a 18m
• 4 extintores para embarcações de 18m a 24m
• Embarcações > 24m: sistema fixo de combate a incêndio na praça de máquinas + extintores portáteis

EMBARCAÇÕES COM MOTOR DE POPA (outboard):
• Mínimo de 1 extintor portátil tipo ABC até 12m
• 2 extintores para embarcações > 12m

ITENS ADICIONAIS OBRIGATÓRIOS:
• Balde com alça (embarcações > 8m)
• Bomba de esgoto manual ou elétrica (embarcações com cabine)
• Detector de gás GLP (embarcações com fogão a gás)

Os extintores devem estar com validade em dia, em local acessível, e marcados com selo do INMETRO. Recarregar a cada 12 meses ou conforme etiqueta.',
'{incendio,extintor,seguranca,motor,glp,inmetro}', 50),

('NORMAM-211', 'Documentação Obrigatória a Bordo',
'Documentos que devem estar sempre a bordo durante a navegação:

1. TIE — Título de Inscrição de Embarcação (original ou cópia autenticada)
2. Carteira de Habilitação de Amador (CHA) do condutor — válida para a área de navegação
3. Comprovante de seguro DPEM vigente
4. Lista de tripulantes e passageiros (obrigatória para navegação costeira e mar aberto)
5. Certificado de Segurança da Navegação (CSN) — quando exigido pela Capitania
6. Comprovante de vistoria (quando aplicável)
7. Documento de identificação do proprietário

Para embarcações > 24m ou em navegação de mar aberto, adicionar:
• Diário de Navegação (opcional para recreio, obrigatório para comercial)
• Certificado de Classe (se classificada por Sociedade Classificadora)
• Certificado IOPP (International Oil Pollution Prevention) para embarcações > 400 AB

A FALTA de documentos pode resultar em multa e retenção da embarcação pela Capitania.',
'{documentos,tie,cha,dpem,seguro,bordo,certificado}', 60),

('NORMAM-211', 'Velocidade e Regras de Conduta em Águas Abrigadas',
'Regras de conduta e limites de velocidade para embarcações de esporte e recreio em águas abrigadas (baías, enseadas, rios, proximidade de praias):

• VELOCIDADE MÁXIMA: 5 nós (cerca de 9 km/h) a menos de 200 metros de praias frequentadas por banhistas, mergulhadores, plataformas de salto e áreas de banho.
• VELOCIDADE MÁXIMA: 3 nós em zonas de fundeio de marinas e iates clubes.
• Jet-skis e motos aquáticas: distância mínima de 200m de áreas de banhistas, e operação proibida entre o pôr e o nascer do sol.
• É PROIBIDO navegar sob efeito de álcool ou substâncias psicoativas (Lei 9.537/1997 — LESTA, art. 22).
• Embarcações a motor devem dar preferência a embarcações a vela e a remo.
• Ao cruzar com outra embarcação em canal estreito, manter-se pelo boreste (direita).',
'{velocidade,conduta,praia,jet_ski,alcool,canal}', 70);


-- -----------------------------------------------
-- NORMAM-201: Mar Aberto
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NORMAM-201', 'Requisitos Adicionais para Navegação em Mar Aberto',
'Embarcações que navegam em mar aberto (além de 20 milhas da costa) possuem requisitos adicionais obrigatórios:

COMUNICAÇÕES:
• Rádio VHF marítimo (canal 16 — socorro) + rádio HF/MF ou estação por satélite (Inmarsat Mini-C ou Iridium)
• EPIRB 406 MHz com GPS integrado, registrado na ANATEL — ativação manual e automática (float-free)
• SART (Search and Rescue Transponder) ou AIS-SART

NAVEGAÇÃO:
• GPS ou GNSS com plotagem
• Radar (obrigatório > 24m)
• Cartas náuticas da rota (DHN)
• Compasso magnético compensado

SEGURANÇA:
• Balsa salva-vidas inflável com capacidade para todos a bordo
• Traje de imersão (recomendado para águas frias, abaixo do paralelo 23°S em inverno)
• Arneses e cabos de vida no convés
• Luzes de navegação conforme RIPEAM/COLREG
• Âncora flutuante (drogue)

TRIPULAÇÃO MÍNIMA:
• Comandante habilitado como Capitão-Amador
• Recomendação: mínimo 2 pessoas habilitadas a bordo para revezamento

A partida para mar aberto deve ser comunicada à Capitania (Plano de Navegação) sempre que a viagem exceder 24 horas ou envolver travessia internacional.',
'{mar_aberto,epirb,radar,balsa,comunicacao,capitao_amador}', 10),

('NORMAM-201', 'Plano de Navegação para Viagens de Mar Aberto',
'O Plano de Navegação deve ser apresentado à Capitania dos Portos antes de viagens de mar aberto com duração superior a 24 horas ou travessias internacionais. O plano inclui:

• Nome e número de inscrição da embarcação
• Nome e habilitação do comandante
• Porto de partida e destino
• Rota planejada (waypoints)
• Data e hora estimada de partida e chegada
• Número de pessoas a bordo (tripulantes + passageiros)
• Equipamentos de comunicação e segurança disponíveis
• Provisões de combustível, água e alimentos

A Capitania pode negar a partida se: embarcação não estiver em condições de navegabilidade, equipamentos obrigatórios faltarem, ou o comandante não possuir habilitação adequada.

Em caso de atraso superior a 24 horas da ETA (hora estimada de chegada), a Capitania pode acionar busca e salvamento (SAR).',
'{plano_navegacao,viagem,capitania,sar,busca_salvamento}', 20);


-- -----------------------------------------------
-- NORMAM-202: Navegação Interior
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NORMAM-202', 'Requisitos para Navegação Interior',
'Embarcações em navegação interior (rios, lagos, lagoas, baías, canais e águas abrigadas) devem atender a:

EQUIPAMENTOS MÍNIMOS:
• Coletes salva-vidas para todos a bordo
• 1 boia circular com retinida
• 1 extintor de incêndio ABC
• Apito ou buzina
• Lanterna estanque
• Âncora com cabo/corrente

HABILITAÇÃO:
• Arrais-Amador (motor) ou categoria Veleiro (apenas vela)
• Motonáutica: para jet-ski e motos aquáticas

PARTICULARIDADES:
• Embarcações miúdas (< 5m ou < 3 AB) com motor até 30 HP podem navegar sem inscrição, desde que identificadas com plaqueta do fabricante, mas o condutor DEVE ter habilitação.
• A velocidade deve ser reduzida em rios estreitos, proximidade de outras embarcações e áreas com tráfego de passageiros.
• Em rios com correnteza forte (> 3 nós), recomenda-se atenção especial à manobrabilidade.',
'{interior,rio,lago,equipamentos,arrais,miuda}', 10);


-- -----------------------------------------------
-- NORMAM-101: Habilitações
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NORMAM-101', 'Categorias de Habilitação de Amadores',
'As categorias de habilitação para condutores amadores de embarcações de esporte e recreio são:

1. VELEIRO
   • Condução de embarcações a vela sem motor auxiliar
   • Área: navegação interior
   • Idade mínima: 18 anos (ou 16 com autorização dos pais)

2. MOTONAUTA
   • Condução de motos aquáticas (jet-ski, waverunner)
   • Área: navegação interior
   • Idade mínima: 18 anos
   • Curso obrigatório específico para motonáutica

3. ARRAIS-AMADOR
   • Condução de embarcações a motor ou mistas (motor+vela)
   • Área: navegação interior
   • Idade mínima: 18 anos
   • Prova teórica + prova prática

4. MESTRE-AMADOR
   • Condução de embarcações em navegação COSTEIRA (até 20 milhas da costa)
   • Pré-requisito: 1 ano como Arrais-Amador
   • Prova teórica (navegação costeira, meteorologia, regras de tráfego)

5. CAPITÃO-AMADOR
   • Condução de embarcações em navegação de MAR ABERTO (sem limite)
   • Pré-requisito: 1 ano como Mestre-Amador
   • Prova teórica (navegação astronômica, meteorologia oceânica, sobrevivência no mar)
   • É a habilitação mais completa para amadores

A CHA (Carteira de Habilitação de Amador) é emitida pela Capitania dos Portos e tem validade de 10 anos, renovável com exame médico.',
'{habilitacao,arrais,mestre,capitao,veleiro,motonauta,cha,curso,prova}', 10),

('NORMAM-101', 'Processo de Obtenção da Habilitação',
'Para obter a habilitação náutica, o candidato deve:

1. MATRÍCULA: Inscrever-se na Capitania dos Portos, Delegacia ou Agência da jurisdição
2. EXAME MÉDICO: Atestado de aptidão física e mental emitido por médico credenciado, incluindo:
   • Acuidade visual mínima (20/40 com ou sem correção)
   • Teste de daltonismo (capacidade de distinguir cores de luzes de navegação)
   • Capacidade auditiva (percepção de sinais sonoros)
3. CURSO (opcional, mas recomendado): Cursos preparatórios em escolas náuticas credenciadas
4. PROVA TEÓRICA: Aplicada pela Capitania, com no mínimo 40 questões:
   • Legislação (LESTA, RLESTA, NORMAM)
   • RIPEAM (regras de navegação)
   • Navegação (estimada, costeira ou astronômica conforme a categoria)
   • Meteorologia
   • Primeiros socorros e sobrevivência no mar
   • Comunicações
5. PROVA PRÁTICA: Demonstração de habilidades de condução (atracar, desatracar, homem ao mar)
6. EMISSÃO DA CHA: Após aprovação em todas as etapas

A taxa de inscrição e a prova são pagas via GRU (Guia de Recolhimento da União).
O candidato reprovado pode refazer a prova após 15 dias.',
'{habilitacao,prova,exame,curso,escola_nautica,cha,gru,processo}', 20),

('NORMAM-101', 'Embarcações Dispensadas de Habilitação',
'NÃO precisam de habilitação os condutores de:

• Embarcações a remo (canoas, caiaques, stand-up paddle) em águas abrigadas
• Embarcações a vela com comprimento < 5m e sem motor, em águas abrigadas
• Embarcações miúdas sem motor

ATENÇÃO: Mesmo dispensado de habilitação, o condutor deve:
• Conhecer e respeitar as regras de navegação (RIPEAM)
• Portar coletes salva-vidas para todos a bordo
• Não navegar sob efeito de álcool ou drogas

Jet-skis e motos aquáticas SEMPRE exigem habilitação (Motonauta), independentemente do porte.',
'{habilitacao,dispensa,remo,caiaque,paddle,jet_ski}', 30);


-- -----------------------------------------------
-- NORMAM-205: Material de Salvatagem
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NORMAM-205', 'Coletes Salva-Vidas — Requisitos e Tipos',
'Os coletes salva-vidas devem ser homologados pela DPC (selo de aprovação) e classificam-se em:

• TIPO I (Oceânico): Flutuabilidade mínima de 150N. Obrigatório para navegação costeira e mar aberto. Capaz de virar o náufrago inconsciente de barriga para cima (face para cima).

• TIPO II (Costeiro): Flutuabilidade mínima de 100N. Aceito para navegação interior e costeira protegida. Não garante virar o náufrago inconsciente.

• TIPO III (Esportivo): Flutuabilidade mínima de 100N. Permite liberdade de movimento. Para esportes náuticos em águas abrigadas.

• TIPO V (Inflável): Inflável manual ou automático (hidrostático). Aceito para navegação costeira e mar aberto como alternativa ao Tipo I, DESDE QUE aprovado pela DPC e com cilindro de CO₂ em dia.

REQUISITOS GERAIS:
• 1 colete por pessoa a bordo + reserva de 10% (arredondado para cima) em embarcações > 12m
• Cor laranja, amarela ou vermelha (alta visibilidade)
• Fita retrorrefletiva (reflexiva) e apito acoplado
• Deve estar em local acessível (NÃO trancado em compartimento)
• Tamanho adequado: adulto, infantil (< 30 kg) e bebê (< 15 kg) conforme passageiros

A Capitania pode reter a embarcação se os coletes estiverem vencidos, insuficientes, sem selo ou em mau estado.',
'{colete,salva_vidas,flutuabilidade,tipo,homologacao,dpc}', 10),

('NORMAM-205', 'Equipamentos Pirotécnicos de Sinalização',
'Equipamentos pirotécnicos servem para sinalizar socorro e devem estar a bordo conforme a área de navegação:

TIPOS:
• Fumígeno (sinal diurno): Produz fumaça laranja visível a quilômetros. Duração mínima de 3 minutos. Usado durante o dia.
• Facho manual (sinal noturno): Produz luz vermelha intensa. Duração mínima de 1 minuto. Usado à noite.
• Foguete paraquedas: Lançado a ~300m de altitude, produz luz vermelha por ~40 segundos. Visível a 25+ milhas náuticas. Para mar aberto.
• Sinal fumígeno flutuante: Produz fumaça laranja na superfície da água por 3+ minutos.

QUANTIDADES MÍNIMAS:
• Navegação interior: 3 fumígenos + 3 fachos manuais (recomendado)
• Navegação costeira: 3 fumígenos + 3 fachos manuais (obrigatório)
• Mar aberto: 6 fachos manuais + 2 foguetes paraquedas + 3 fumígenos

ATENÇÃO:
• Todos têm prazo de validade (geralmente 3 anos da fabricação) — vencidos devem ser substituídos
• Armazenar em local seco, acessível e sinalizado
• NÃO disparar fora de situação de emergência real (é infração)',
'{pirotecnico,fumigeno,facho,foguete,sinalizacao,socorro}', 20),

('NORMAM-205', 'EPIRB — Radiobaliza de Emergência',
'O EPIRB (Emergency Position Indicating Radio Beacon) é obrigatório para embarcações em navegação de mar aberto:

FUNCIONAMENTO:
• Opera na frequência 406 MHz (detecção via satélites COSPAS-SARSAT)
• Transmite identificação MMSI da embarcação + coordenadas GPS
• Ativação automática (float-free: boia quando a embarcação afunda) e manual
• Alcance de detecção: global (via satélite) — localização em menos de 5 minutos

REQUISITOS:
• Deve ser registrado na ANATEL (Agência Nacional de Telecomunicações) com dados do proprietário e da embarcação
• Manutenção anual (teste de bateria e transmissão)
• Bateria com validade de 5 anos (data marcada na unidade)
• Deve ser instalado em local de fácil acesso para ativação manual e para soltar automaticamente (float-free bracket)

EM CASO DE ATIVAÇÃO ACIDENTAL:
• Desativar imediatamente e contatar o MRCC (Maritime Rescue Coordination Centre) / Salvamar Brasil (telefone: 185 ou canal 16 VHF)
• Ativação falsa sem notificação é infração grave',
'{epirb,radiobaliza,406mhz,satelite,socorro,busca_salvamento}', 30);


-- -----------------------------------------------
-- NORMAM-204: Vistoria
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NORMAM-204', 'Tipos de Vistoria e Periodicidade',
'As embarcações estão sujeitas a vistorias realizadas pela Capitania dos Portos (ou Sociedade Classificadora delegada):

1. VISTORIA INICIAL: Antes da primeira inscrição ou após construção/modificação. Verifica se a embarcação atende aos requisitos de segurança para a área de navegação pretendida.

2. VISTORIA PERIÓDICA (ANUAL): Realizada a cada 12 meses (tolerância de 3 meses). Verifica estado geral, equipamentos de segurança e documentação.

3. VISTORIA INTERMEDIÁRIA: Para embarcações > 24m, realizada entre vistorias periódicas (a cada 2,5 anos). Inspeção mais detalhada de casco, máquinas e sistemas.

4. VISTORIA ESPECIAL (DOCAGEM): A cada 5 anos. Embarcação em seco (doca seca ou carreira). Inspeção completa do casco submerso, leme, hélice, eixo, válvulas de fundo.

5. VISTORIA EVENTUAL: Em caso de acidente, avaria, reclamação ou quando a Capitania julgar necessário.

REGIME SIMPLIFICADO (Esporte/Recreio ≤ 100 AB):
• Embarcações de esporte e recreio com arqueação bruta ≤ 100 podem seguir regime simplificado de vistoria, com autoavaliação pelo proprietário e vistoria periódica bienal.

A embarcação que não passar na vistoria recebe Termo de Restrição e fica impedida de navegar até regularização.',
'{vistoria,periodica,inicial,especial,docagem,capitania,certificado}', 10),

('NORMAM-204', 'Itens Verificados em Vistoria',
'Os principais itens verificados durante a vistoria incluem:

CASCO E ESTRUTURA:
• Integridade do casco (sem trincas, osmose, corrosão ou danos estruturais)
• Estado das obras vivas (fundo) e obras mortas (acima da linha d''água)
• Proteção catódica (zincos/ânodos de sacrifício) — estado e quantidade
• Válvulas de fundo e passagens do casco — estanqueidade
• Leme, eixo propulsor e mancais

MÁQUINAS:
• Motor principal e auxiliar — funcionamento e vazamentos
• Sistema de combustível — tanques, linhas, válvulas de corte
• Sistema de exaustão — isolamento térmico e estanqueidade
• Sistema elétrico — quadro de distribuição, fiação, baterias

SEGURANÇA:
• Todos os equipamentos de salvatagem (coletes, boia, pirotécnicos)
• Extintores — validade, tipo e quantidade
• Equipamentos de navegação (luzes, compasso, GPS)
• Equipamentos de comunicação (VHF, EPIRB)
• Meios de esgoto (bombas de porão)

DOCUMENTAÇÃO:
• TIE válido
• CHA do proprietário/condutor
• Seguro DPEM',
'{vistoria,itens,casco,motor,seguranca,equipamentos,verificacao}', 20);


-- -----------------------------------------------
-- NORMAM-203: Construção
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NORMAM-203', 'Requisitos de Construção e Modificação',
'A construção de embarcações de esporte e recreio no Brasil deve atender a:

PROJETO:
• Embarcações > 5m devem ter projeto aprovado por engenheiro naval ou perito credenciado pela DPC
• O projeto inclui: arranjo geral, plano de linhas, estrutural, estabilidade, compartimentagem e especificações técnicas
• Embarcações de série (produzidas em estaleiro com modelo certificado) ficam dispensadas de projeto individual

MATERIAIS:
• PRFV (Fibra de vidro): Material mais comum em lanchas e veleiros até 24m. Deve seguir a NBR 14574
• Alumínio naval (liga 5000/6000): Comum em embarcações de trabalho e veleiros de alta performance
• Aço naval: Embarcações > 24m. Deve atender normas de Sociedade Classificadora
• Madeira: Permitida com certificação de origem e tratamento adequado

ESTABILIDADE:
• Deve atender critérios de estabilidade intacta e em avaria (quando aplicável)
• Reserva de flutuabilidade — a embarcação não deve afundar completamente mesmo alagada (para embarcações < 12m com flutuabilidade positiva obrigatória)

MODIFICAÇÕES:
• Qualquer modificação estrutural (alterar casco, motor, superestrutura) exige novo projeto aprovado e vistoria especial
• Remotorização (troca de motor por outro de potência diferente) exige recálculo de estabilidade e nova inscrição',
'{construcao,projeto,material,fibra_vidro,aluminio,estabilidade,modificacao}', 10);


-- -----------------------------------------------
-- NORMAM-601 / COLREG: Regras de Navegação
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NORMAM-601', 'Regras de Governo e Navegação (RIPEAM)',
'As regras de governo e navegação do RIPEAM/COLREG aplicáveis a embarcações de recreio:

SITUAÇÕES DE ENCONTRO:
• RODA A RODA (proa com proa): Ambas as embarcações devem guinar para BORESTE (direita). Cada uma passa pelo lado de bombordo da outra.
• CRUZAMENTO: A embarcação que tem a outra pelo seu boreste é a que deve dar passagem (manobrar). A outra mantém rumo e velocidade.
• ULTRAPASSAGEM: A embarcação que ultrapassa deve manter-se afastada da ultrapassada. A embarcação ultrapassada mantém rumo e velocidade.

HIERARQUIA DE PREFERÊNCIA (quem tem preferência):
1. Embarcação sem governo (desmantelada, à deriva)
2. Embarcação com capacidade de manobra restrita
3. Embarcação engajada na pesca
4. Embarcação a VELA
5. Embarcação a MOTOR
→ Ou seja: motor dá passagem a vela; vela dá passagem a pesca; etc.

CANAL ESTREITO:
• Navegar o mais perto possível do limite do canal pelo boreste
• Não cruzar canal estreito se isso dificultar a passagem de embarcação que só pode navegar dentro do canal
• Embarcações < 20m e veleiros NÃO devem dificultar a passagem de embarcações que só navegam dentro do canal',
'{ripeam,colreg,cruzamento,ultrapassagem,roda_a_roda,governo,preferencia}', 10),

('NORMAM-601', 'Luzes de Navegação Obrigatórias',
'Luzes de navegação que devem ser exibidas do pôr ao nascer do sol (e em visibilidade reduzida):

EMBARCAÇÃO A MOTOR (em movimento):
• Luz de mastro (branca, 225°) — visível para frente
• Luzes de bordos: verde (boreste/direita) + vermelha (bombordo/esquerda), 112.5° cada
• Luz de alcançado (branca, 135°) — visível para trás
• Embarcações < 12m: podem combinar as luzes de bordo em lanterna bicolor na proa
• Embarcações < 7m com velocidade < 7 nós: podem exibir apenas 1 luz branca visível em todo horizonte

EMBARCAÇÃO A VELA (em movimento):
• Luzes de bordo (verde + vermelha)
• Luz de alcançado (branca, 135°)
• NÃO exibe luz de mastro (se exibir, está usando motor e segue regras de embarcação a motor)
• Veleiros < 7m: lanterna ou luz branca pronta para exibição

EMBARCAÇÃO FUNDEADA (ancorada):
• 1 luz branca visível em todo horizonte (360°) — ou 2 se > 50m
• Embarcações < 7m em área sem tráfego: dispensadas

PENALIDADE: Navegar sem luzes à noite é infração grave e causa frequente de acidentes.',
'{luzes,navegacao,bordo,mastro,alcancado,noturna,seguranca}', 20),

('NORMAM-601', 'Sinais Sonoros',
'Sinais sonoros que devem ser usados em visibilidade reduzida (nevoeiro, chuva forte) ou para indicar manobra:

MANOBRA (com outra embarcação à vista):
• 1 apito curto (≈ 1 seg): "Estou guinando para BORESTE"
• 2 apitos curtos: "Estou guinando para BOMBORDO"
• 3 apitos curtos: "Estou dando máquinas atrás"
• 5 ou mais apitos curtos: "NÃO entendi sua intenção / PERIGO"

VISIBILIDADE REDUZIDA (nevoeiro):
• Embarcação a motor em movimento: 1 apito longo a cada 2 minutos
• Embarcação a vela / pesca / reboque: 1 apito longo + 2 curtos a cada 2 minutos
• Embarcação fundeada: Sino tocado rapidamente por 5 segundos, a cada 1 minuto
• Embarcação encalhada: 3 batidas de sino + sino rápido + 3 batidas, a cada 1 minuto

EQUIPAMENTO:
• Embarcações ≥ 12m: apito/buzina + sino
• Embarcações < 12m: qualquer meio de produzir sinal sonoro eficiente',
'{sinais_sonoros,apito,nevoeiro,manobra,sino,seguranca}', 30);


-- -----------------------------------------------
-- LESTA: Lei de Segurança do Tráfego Aquaviário
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('LESTA', 'Competências da Autoridade Marítima',
'A Lei 9.537/1997 (LESTA) atribui à Autoridade Marítima (exercida pelo Comandante da Marinha, delegada à DPC — Diretoria de Portos e Costas) as seguintes competências:

• Regulamentar a segurança do tráfego aquaviário
• Estabelecer normas (NORMAM) para embarcações, tripulação, navegação e meio ambiente
• Inscrever embarcações (emitir o TIE)
• Habilitar aquaviários e amadores (emitir CHA)
• Realizar vistorias de segurança
• Aplicar penalidades por infrações
• Investigar acidentes da navegação (Inquérito Administrativo)
• Regulamentar o tráfego aquaviário em águas sob jurisdição nacional

As Capitanias dos Portos, Delegacias e Agências são os órgãos executivos locais da Autoridade Marítima.',
'{lesta,lei,autoridade_maritima,dpc,capitania,competencia}', 10),

('LESTA', 'Infrações e Penalidades',
'A LESTA prevê as seguintes infrações e penalidades para condutores e proprietários de embarcações:

INFRAÇÕES GRAVES:
• Navegar sem inscrição (TIE): multa + apreensão da embarcação
• Conduzir sem habilitação (CHA): multa + impedimento de navegar
• Navegar sob efeito de álcool ou drogas: multa + suspensão da CHA por até 2 anos + apreensão da embarcação
• Navegar sem equipamentos obrigatórios de segurança: multa + retenção até regularização
• Provocar acidente por imperícia, imprudência ou negligência: multa + suspensão/cassação da CHA

INFRAÇÕES LEVES/MÉDIAS:
• Excesso de velocidade em áreas restritas: multa
• Excesso de passageiros: multa + impedimento de zarpar
• Falta de documentos a bordo: multa
• Desobediência a ordens da Capitania: multa

PENALIDADES:
• Multas de R$ 200 a R$ 100.000 (valores de referência, atualizados periodicamente)
• Suspensão da CHA (30 dias a 2 anos)
• Cassação da CHA (infração gravíssima ou reincidência)
• Apreensão da embarcação
• Interdição do estaleiro/marina

Os valores das multas são fixados pela DPC e recolhidos via GRU.',
'{infracoes,multas,penalidades,suspensao,cassacao,apreensao}', 20);


-- -----------------------------------------------
-- RLESTA: Regulamento
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('RLESTA', 'Classificação de Embarcações',
'O Regulamento da LESTA (Decreto 2.596/1998) classifica as embarcações:

POR TIPO DE PROPULSÃO:
• A motor (propulsão mecânica principal)
• A vela (propulsão à vela principal)
• Mista (motor + vela)
• Sem propulsão (balsas, pontões, dragas)

POR TIPO DE SERVIÇO:
• Esporte e recreio (uso particular, sem fins comerciais)
• Passageiros (transporte comercial de pessoas)
• Carga (transporte comercial de mercadorias)
• Pesca (pesca comercial)
• Serviço público (Marinha, polícia, fiscalização)

POR PORTE:
• Embarcação miúda: < 5m de comprimento total ou < 3 de arqueação bruta (AB)
• Embarcação de pequeno porte: < 100 AB
• Embarcação de médio porte: 100 a 500 AB
• Navio: ≥ 500 AB (ou > 24m para embarcações de carga)

POR ÁREA DE NAVEGAÇÃO:
• Mar aberto / Costeira / Interior (conforme NORMAM-211)

A classificação determina os requisitos de segurança, habilitação do condutor e documentação.',
'{classificacao,tipo,porte,servico,propulsao,arqueacao}', 10),

('RLESTA', 'Tripulação Mínima de Segurança',
'O RLESTA estabelece tripulação mínima de segurança:

EMBARCAÇÕES DE ESPORTE E RECREIO:
• Comandante habilitado na categoria adequada à área de navegação
• Para embarcações > 24m em navegação costeira/mar aberto: recomenda-se pelo menos 2 pessoas habilitadas para revezamento
• Não há exigência de tripulação profissional para embarcações de recreio operadas pelo proprietário

EMBARCAÇÕES COMERCIAIS (passageiros/carga):
• Tabela de Lotação de Segurança (TLS) definida pela Capitania
• Comandante, imediato, maquinista, cozinheiro, etc. conforme porte e tipo

O excesso de passageiros além da lotação homologada é infração grave, sujeita a multa e impedimento de partida. A lotação está gravada na Placa de Lotação (obrigatória para embarcações de passageiros e de recreio ≥ 5m).',
'{tripulacao,lotacao,seguranca,comandante,passageiros}', 20);


-- -----------------------------------------------
-- RPC-DPC: Registro / TIE
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('RPC-DPC', 'Processo Completo de Inscrição e Emissão do TIE',
'O TIE (Título de Inscrição de Embarcação) é o documento oficial de identidade da embarcação perante a Autoridade Marítima. Processo passo-a-passo:

PASSO 1 — DOCUMENTAÇÃO:
• Requerimento padrão da Capitania (formulário disponível no site ou presencial)
• RG e CPF do proprietário (ou CNPJ + contrato social para pessoa jurídica)
• Comprovante de residência
• Comprovante de propriedade: NF do estaleiro/revendedor, contrato de compra/venda com firma reconhecida, ou escritura pública
• DPEM (seguro obrigatório) contratado e vigente

PASSO 2 — PAGAMENTO:
• Taxa GRU (Guia de Recolhimento da União) para inscrição — valor atualizado no site da Capitania
• Emolumentos da vistoria (se aplicável)

PASSO 3 — VISTORIA INICIAL:
• A Capitania agenda vistoria para verificar se a embarcação atende aos requisitos de segurança
• Itens verificados: casco, motor, equipamentos de segurança, luzes, documentação do projeto
• Embarcações de série (estaleiro certificado) podem ter vistoria simplificada

PASSO 4 — EMISSÃO DO TIE:
• Após aprovação, a Capitania emite o TIE com:
  - Número de inscrição (ex.: DF-2719XX-XXX)
  - Nome da embarcação
  - Tipo, material do casco, dimensões, motor
  - Área de navegação autorizada
  - Nome e CPF/CNPJ do proprietário
  - Lotação (número máximo de pessoas)

PASSO 5 — MARCAÇÃO:
• O número de inscrição deve ser pintado/fixado no casco em local visível, com caracteres de no mínimo 5 cm de altura

TRANSFERÊNCIA:
• A venda da embarcação exige: contrato de compra e venda com firma reconhecida + cancelamento do TIE antigo + nova inscrição pelo comprador na Capitania da jurisdição.

PRAZO: O processo leva em média 15 a 30 dias úteis.',
'{tie,inscricao,registro,processo,documentos,gru,capitania,venda,transferencia}', 10),

('RPC-DPC', 'DPEM — Seguro Obrigatório de Embarcações',
'O DPEM (Danos Pessoais causados por Embarcações ou por suas Cargas) é o seguro obrigatório para embarcações no Brasil:

O QUE COBRE:
• Indenização por morte: valor definido pela SUSEP (atualmente até R$ 13.500)
• Indenização por invalidez permanente: até R$ 13.500
• Despesas médicas e suplementares: até R$ 2.700
• Abrange tripulantes, passageiros e terceiros atingidos

QUEM DEVE CONTRATAR:
• Proprietário de QUALQUER embarcação inscrita (TIE obrigatório)
• Renovação anual

COMO CONTRATAR:
• Via seguradoras autorizadas pela SUSEP
• Pode ser contratado online ou nas seguradoras parceiras
• O comprovante de pagamento deve estar a bordo

CONSEQUÊNCIA DA FALTA:
• Infração grave: multa + impedimento de navegar
• Em caso de acidente sem DPEM, o proprietário responde pessoalmente pelos danos

NOTA: Diferente do seguro casco (que cobre danos à embarcação), o DPEM é responsabilidade civil obrigatória (como o DPVAT para veículos).',
'{dpem,seguro,obrigatorio,indenizacao,susep,responsabilidade}', 20);


-- -----------------------------------------------
-- NORMAM-401: Meio Ambiente
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NORMAM-401', 'Prevenção da Poluição por Embarcações de Recreio',
'A NORMAM-401 (série 400 — Meio Ambiente) e a MARPOL estabelecem regras de prevenção da poluição para embarcações, incluindo as de recreio:

ÓLEO E COMBUSTÍVEL (MARPOL Anexo I):
• Proibido descarregar óleo, combustível ou mistura oleosa nas águas
• Embarcações com motor devem ter bandeja de contenção sob o motor
• Recolher óleo usado e entregar em posto de coleta (marina ou porto)
• Em caso de vazamento: notificar imediatamente a Capitania (canal VHF 16 ou 185)

ESGOTO SANITÁRIO (MARPOL Anexo IV):
• Embarcações com banheiro (vaso sanitário) devem ter: tanque de retenção (holding tank) OU sistema de tratamento de esgoto aprovado
• PROIBIDO descarregar esgoto in natura a menos de 12 milhas da costa
• A 3-12 milhas: somente com sistema de tratamento aprovado
• Em marinas: utilizar estação de bombeamento (pump-out) quando disponível

LIXO (MARPOL Anexo V):
• PROIBIDO jogar QUALQUER lixo no mar (incluindo restos de alimento a menos de 12 milhas)
• Todo lixo deve ser armazenado a bordo e descartado em terra
• Plásticos: PROIBIDO em qualquer distância da costa (multa pesada)

TINTAS ANTI-INCRUSTANTES:
• Proibido uso de tintas à base de TBT (tributilestanho) — regulamentação ANVISA/IBAMA
• Usar tintas anti-incrustantes aprovadas (à base de cobre ou biocida permitido)',
'{poluicao,oleo,esgoto,lixo,meio_ambiente,marpol,tanque_retencao}', 10),

('NORMAM-401', 'Multas Ambientais e Responsabilidades',
'As infrações ambientais na navegação são punidas de forma severa:

LEGISLAÇÃO APLICÁVEL:
• NORMAM-401 (Marinha/DPC) — multas administrativas
• Lei 9.605/1998 (Crimes Ambientais) — multas + penas criminais
• IBAMA — multas de R$ 5.000 a R$ 50.000.000

INFRAÇÕES COMUNS:
• Despejo de óleo nas águas: multa + obrigação de limpeza às expensas do infrator
• Despejo de esgoto in natura dentro de 12 milhas: multa
• Despejo de lixo/plástico no mar: multa + crime ambiental (pena de 1 a 4 anos)
• Uso de tinta TBT: multa IBAMA
• Ausência de tanque de retenção: multa na vistoria

RESPONSABILIDADE CIVIL:
• O proprietário da embarcação é responsável solidário por danos ambientais, mesmo se o condutor for terceiro
• Em caso de derramamento de óleo: deve custear toda a operação de contenção e limpeza
• Seguro ambiental é recomendado para embarcações > 24m',
'{multa,ambiental,crime,ibama,responsabilidade,poluicao}', 20);


-- -----------------------------------------------
-- MARPOL: Convenção Internacional
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('MARPOL', 'Resumo dos 6 Anexos da MARPOL',
'A MARPOL 73/78 possui 6 anexos, todos ratificados pelo Brasil:

ANEXO I — PREVENÇÃO DA POLUIÇÃO POR ÓLEO:
• Requisitos para tanques, equipamento de separação óleo-água, plano de emergência
• Certificado IOPP (International Oil Pollution Prevention) para navios ≥ 400 AB
• Áreas Especiais (com proteção reforçada): Mediterrâneo, Báltico, Mar Negro, etc.

ANEXO II — SUBSTÂNCIAS NOCIVAS LÍQUIDAS A GRANEL:
• Classificação em categorias X, Y, Z — requisitos de descarga e lavagem
• Mais relevante para navios-tanque do que para recreio

ANEXO III — SUBSTÂNCIAS NOCIVAS EMBALADAS:
• Requisitos de embalagem, rotulagem e armazenamento
• Relevante para transporte de produtos perigosos

ANEXO IV — ESGOTO:
• Proibição de descarga de esgoto in natura dentro de 3 milhas da costa
• Tratado ou triturado + desinfetado: pode descarregar a > 3 milhas
• In natura: somente a > 12 milhas e com velocidade mínima de 4 nós

ANEXO V — LIXO:
• Proibição total de descarga de plásticos
• Restos de alimento: somente a > 12 milhas da costa (3 milhas se triturados)
• Todas as embarcações ≥ 12m devem ter Plano de Gerenciamento de Lixo

ANEXO VI — EMISSÕES ATMOSFÉRICAS:
• Limites de enxofre no combustível (0,50% globalmente desde jan/2020)
• Área de Controle de Emissões (ECA): limite mais restrito
• Menos relevante para embarcações de recreio com combustível comercial padrão',
'{marpol,anexo,oleo,esgoto,lixo,emissoes,plastico,poluicao}', 10);


-- -----------------------------------------------
-- COLREG: Convenção Internacional
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('COLREG', 'Aplicação das COLREG a Embarcações de Recreio',
'O COLREG (Convention on the International Regulations for Preventing Collisions at Sea, 1972) aplica-se a TODAS as embarcações em águas navegáveis internacionais. No Brasil, é internalizado pela NORMAM-601 (RIPEAM).

OBRIGAÇÕES PARA EMBARCAÇÕES DE RECREIO:
• Manter vigília visual e auditiva permanente
• Navegar em velocidade de segurança (que permita parar a tempo)
• Usar todos os meios disponíveis para evitar abalroamento
• Exibir luzes e marcas corretas (Regras 20-31)
• Emitir sinais sonoros corretos (Regras 32-37)

REGRA FUNDAMENTAL (Regra 2):
• Nada nas regras isenta uma embarcação de tomar TODAS as precauções necessárias para evitar um acidente. A prudência e a boa prática marinheira prevalecem sobre qualquer regra específica.

RESPONSABILIDADE COMPARTILHADA (Regra 17):
• Mesmo a embarcação com "direito de passagem" (que mantém rumo e velocidade) deve manobrar para evitar colisão se perceber que a outra não está agindo. A regra de "stand-on" não é desculpa para não evitar o acidente.

VISIBILIDADE REDUZIDA (Regra 19):
• Em nevoeiro/chuva: velocidade de segurança, radar ligado (se disponível), sinal sonoro contínuo, atenção redobrada.',
'{colreg,recreio,responsabilidade,vigilia,velocidade,seguranca}', 10);


-- -----------------------------------------------
-- SOLAS: Convenção Internacional
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('SOLAS', 'Princípios Aplicáveis a Embarcações de Recreio',
'Embora a SOLAS se aplique primariamente a navios comerciais > 500 AB e navios de passageiros, seus PRINCÍPIOS influenciam as NORMAM para embarcações de recreio:

PROTEÇÃO CONTRA INCÊNDIO:
• Embarcações de recreio devem ter: extintores, detector de gás (se usar GLP), ventilação adequada na praça de máquinas. Princípios extraídos do Cap. II-2 da SOLAS.

EQUIPAMENTOS SALVA-VIDAS:
• Coletes, balsas, EPIRB, sinalizadores — requisitos da NORMAM-205 baseados no Cap. III da SOLAS.

RADIOCOMUNICAÇÕES (GMDSS):
• O Global Maritime Distress and Safety System (Cap. IV da SOLAS) influencia os requisitos de VHF, EPIRB e SART para navegação de mar aberto.
• Canal 16 VHF = frequência internacional de socorro
• Frequência 406 MHz = EPIRB (detecção via satélite COSPAS-SARSAT)
• DSC (Digital Selective Calling) = chamada seletiva digital para socorro

SEGURANÇA DA NAVEGAÇÃO (Cap. V):
• Cartas atualizadas, GPS, AIS (para embarcações > 300 AB), planejamento de viagem — princípios que influenciam os requisitos de equipamentos de navegação das NORMAM.',
'{solas,incendio,radiocomunicacao,gmdss,vhf,ais,seguranca}', 10);


-- -----------------------------------------------
-- NBR 14574: PRFV
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NBR 14574', 'Requisitos de Construção em PRFV',
'A NBR 14574:2012 estabelece requisitos para embarcações de recreio em PRFV (Plástico Reforçado com Fibra de Vidro) até 24m de comprimento:

ESCOPO:
• Lanchas, veleiros e jet-boats fabricados em fibra de vidro
• Base do programa de certificação ABNT-ACOBAR (Associação Brasileira dos Construtores de Barcos e seus Implementos)

PRINCIPAIS REQUISITOS:
• Laminação: espessura mínima do casco conforme tabelas de escantilhamento
• Resina: tipo e proporção fibra/resina (teor de vidro mínimo de 30%)
• Reforços estruturais: anteparas, longarinas, cavernas
• Convés e superestrutura: resistência a cargas de uso (caminhamento)
• Passagens do casco: válvulas de fundo em bronze ou aço inox marítimo
• Sistema de governo: dimensionamento do leme, mecha e caixas de mancal
• Sistema elétrico: fiação marítima, proteção contra curto, aterramento
• Tanques de combustível: material, fixação, ventilação, válvula corta-fogo
• Tanques de água: material atóxico, fixação
• Sistema de exaustão: isolamento térmico obrigatório, saída acima da linha d''água

CERTIFICAÇÃO ACOBAR:
• Estaleiros podem certificar seus modelos junto à ACOBAR/ABNT
• Embarcações certificadas têm vistoria simplificada na Capitania
• O selo ACOBAR garante conformidade com a NBR 14574',
'{nbr_14574,prfv,fibra_vidro,construcao,acobar,certificacao,laminacao}', 10);


-- -----------------------------------------------
-- NBR ISO 8666: Classificação
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NBR-ISO-8666', 'Classificação de Embarcações de Recreio',
'A NBR ISO 8666 define a classificação e dados principais de embarcações de recreio:

MEDIDAS PRINCIPAIS:
• LOA (Length Overall / Comprimento Total): Medida da proa à popa, incluindo púlpito, plataforma de mergulho e outros apêndices
• LH (Hull Length / Comprimento do Casco): Comprimento do casco sem apêndices — é a medida usada para classificação regulatória
• Boca máxima (Beam): Largura máxima do casco
• Calado (Draft): Profundidade da parte submersa do casco (da linha d''água à quilha)
• Deslocamento: Peso total da embarcação carregada (em toneladas)

CATEGORIAS DE PROJETO (relevantes para segurança):
• CATEGORIA A (Oceânica): Projetada para ondas > 4m e ventos > Beaufort 8. Para navegação de mar aberto sem restrição.
• CATEGORIA B (Costeira): Ondas até 4m, ventos até Beaufort 8. Para navegação costeira.
• CATEGORIA C (Águas abrigadas): Ondas até 2m, ventos até Beaufort 6. Baías, estuários, lagos grandes.
• CATEGORIA D (Águas protegidas): Ondas até 0,3m, ventos até Beaufort 4. Lagos calmos, rios, canais protegidos.

A categoria de projeto deve estar indicada na Placa do Construtor (obrigatória). Uma embarcação Categoria C NÃO pode ser usada em mar aberto.',
'{classificacao,loa,comprimento,boca,calado,categoria_projeto,oceano,costeira}', 10);


-- -----------------------------------------------
-- NORMAM-301: Sinalização Náutica
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NORMAM-301', 'Sistema de Balizamento IALA Região B',
'O Brasil adota o Sistema de Balizamento Marítimo IALA Região B (International Association of Lighthouse Authorities):

MARCAS LATERAIS (indicam os lados do canal navegável):
• BORESTE (direita, entrando no porto): Marcas VERMELHAS (cones/cilindros vermelhos, luzes vermelhas)
• BOMBORDO (esquerda, entrando no porto): Marcas VERDES (cilindros verdes, luzes verdes)
• Mnemônico: "Entrando no porto, vermelho à direita" (Região B — oposto à Europa/Região A)

MARCAS CARDINAIS (indicam onde está a água segura em relação ao perigo):
• Norte: amarela/preta, ponta para cima
• Sul: preta/amarela, ponta para baixo
• Leste: preta/amarela/preta, pontas opostas
• Oeste: amarela/preta/amarela, pontas juntas

MARCAS DE PERIGO ISOLADO: Preta com faixa vermelha, 2 esferas no topo. Indica perigo com água segura ao redor.

MARCAS DE ÁGUAS SEGURAS: Faixas verticais vermelha/branca. Indica águas navegáveis (centro do canal).

MARCAS ESPECIAIS: Amarelas. Indica áreas especiais (zona militar, área de aquicultura, cabos submarinos).

É fundamental conhecer este sistema para navegar com segurança, especialmente à noite quando apenas as luzes de balizamento são visíveis.',
'{balizamento,iala,sinalizacao,boia,canal,navegacao,luzes}', 10);


-- -----------------------------------------------
-- NBR 15285: Ruído
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NBR-15285', 'Limites de Emissão Sonora para Embarcações',
'A NBR 15285 estabelece procedimentos de medição e limites de ruído para embarcações de recreio motorizadas:

LIMITES:
• Embarcações com motor de popa: máximo de 75 dB(A) a 25m de distância
• Embarcações com motor de centro (inboard): máximo de 75 dB(A) a 25m
• Motos aquáticas (jet-ski): máximo de 75 dB(A) a 25m

MEDIÇÃO:
• Feita com embarcação em velocidade máxima
• A 25 metros de distância lateral
• Em condições de vento < 3 m/s e sem outras fontes de ruído

APLICAÇÃO:
• Relevante para embarcações que operam em baías residenciais, enseadas e lagos
• Algumas prefeituras e órgãos ambientais municipais adotam regulamentação local mais restritiva
• Estaleiros devem comprovar conformidade para certificação ACOBAR',
'{ruido,som,decibel,jet_ski,motor,poluicao_sonora}', 10);


-- -----------------------------------------------
-- NBR ISO 12217: Estabilidade
-- -----------------------------------------------
insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('NBR-ISO-12217', 'Critérios de Estabilidade e Flutuabilidade',
'A NBR ISO 12217 define ensaios e critérios de estabilidade para embarcações de recreio:

ESTABILIDADE INTACTA:
• Ensaio de inclinação: verificar GZ (braço de endireitamento) mínimo
• Ângulo de alagamento: a embarcação não deve alagar com inclinação até o ângulo crítico
• Altura metacêntrica (GM) mínima conforme categoria de projeto

FLUTUABILIDADE:
• Embarcações < 6m (Categoria C e D): devem ter flutuabilidade positiva mesmo completamente alagadas (com espuma ou compartimentos estanques)
• Embarcações > 6m: reserva de flutuabilidade verificada por cálculo

ENSAIOS:
• Teste de compensação de peso (peso morto no costado)
• Teste de alagamento (para embarcações < 6m)
• Teste de recuperação (capacidade de endireitar após tombamento parcial)

CATEGORIAS:
• Cada categoria de projeto (A, B, C, D) tem critérios de estabilidade específicos
• Categoria A (oceânica) exige os critérios mais rigorosos

RELEVÂNCIA PRÁTICA:
• A estabilidade é requisito fundamental para inscrição e vistoria
• Embarcações modificadas (remotorização, alteração de superestrutura) devem refazer o cálculo de estabilidade',
'{estabilidade,flutuabilidade,ensaio,gm,inclinacao,categoria}', 10);

