-- ============================================================
-- Yachts Atlas — Capitã Solara: Enriquecimento de Normas BR
-- ------------------------------------------------------------
-- Novas seções práticas de normas náuticas brasileiras para o
-- RAG da Capitã Solara, focadas no dia a dia do navegante de
-- esporte e recreio: socorro/SALVAMAR, reboque, abastecimento
-- seguro, crianças a bordo, fundeio/atracação, praticagem,
-- avisos aos navegantes (DHN) e áreas ambientais sensíveis.
--
-- Idempotente: usa o índice único (norma_codigo, secao) criado
-- em migration_pgvector.sql. Após aplicar, rode o backfill de
-- embeddings (backend/backfill_embeddings.py).
--
-- jun/2026 — v3 (Enrichment)
-- ============================================================

insert into public.normas_conteudo (norma_codigo, secao, conteudo, palavras_chave, ordem) values

('LESTA', 'Como Acionar Socorro no Mar — SALVAMAR e Canal 16',
'Em emergência na água, o sistema de busca e salvamento (SAR) brasileiro é coordenado pela Marinha do Brasil (SALVAMAR BRASIL / MRCC).

COMO PEDIR SOCORRO:
• Telefone de emergência da Marinha: 185 (afundamento, encalhe, pessoa ao mar, socorro no mar)
• Rádio VHF: CANAL 16 — frequência internacional de chamada e socorro (156,8 MHz)
• DSC (Chamada Seletiva Digital): canal 70 — envia alerta com identificação (MMSI) e posição GPS automaticamente
• EPIRB 406 MHz: aciona via satélite quando não há outro meio

NÍVEIS DE CHAMADA POR RÁDIO:
• MAYDAY — perigo grave e iminente à vida ou à embarcação (repetir 3 vezes). Ex.: afundamento, incêndio, homem ao mar em risco.
• PAN-PAN — urgência sem perigo iminente de vida (ex.: pane sem deriva perigosa).
• SÉCURITÉ — mensagem de segurança (ex.: aviso de perigo à navegação).

O QUE INFORMAR: nome e inscrição da embarcação, posição (coordenadas ou referência), natureza da emergência, número de pessoas a bordo e tipo de auxílio necessário. Mantenha a calma, fale devagar e aguarde resposta da estação costeira ou de outra embarcação.',
'{socorro,salvamar,mrcc,canal_16,mayday,pan_pan,185,emergencia,sar}', 80),

('NORMAM-211', 'Reboque e Assistência entre Embarcações',
'Pane de motor ou perda de governo são situações comuns. Boas práticas de assistência e reboque:

EM CASO DE PANE:
• Se houver risco de ir contra pedras ou para a costa, FUNDEIE imediatamente para ganhar tempo.
• Sinalize sua situação (bandeira, rádio, sinais sonoros) e acione socorro se necessário (canal 16 / 185).
• Ligue as luzes de navegação ou de fundeio conforme a situação.

REBOQUE SEGURO:
• Use cabo de reboque resistente e elástico (absorve trancos); evite cabos de aço.
• Fixe o cabo em pontos estruturais firmes (cunhos, malaguetas reforçadas), nunca em balaústres frágeis.
• Mantenha pessoas LONGE do cabo sob tensão — se romper, o chicote pode ferir gravemente.
• Reboque em velocidade baixa e constante; comunique-se com a outra embarcação por rádio ou sinais combinados.
• Em águas abrigadas e bom tempo, embarcações de recreio podem prestar assistência mútua; em situação de risco real, priorize acionar o socorro oficial.

A boa prática marinheira e a obrigação de auxílio a quem está em perigo no mar são princípios da legislação e das convenções (SOLAS/COLREG).',
'{reboque,pane,assistencia,fundeio,cabo,socorro,seguranca}', 90),

('NORMAM-211', 'Abastecimento de Combustível com Segurança',
'O abastecimento é um dos momentos de MAIOR risco de incêndio e explosão a bordo, por causa do acúmulo de vapores de combustível. Procedimento seguro:

ANTES:
• Atraque firme e desligue o MOTOR e todos os equipamentos elétricos.
• Apague qualquer chama (fogão, cigarro) e proíba fumar nas proximidades.
• Feche escotilhas e vigias para os vapores não entrarem na cabine.
• Desembarque os passageiros, se possível.

DURANTE:
• Mantenha o bico da bomba em contato com o bocal do tanque (evita faísca estática).
• Não encha o tanque até a borda — deixe espaço para dilatação do combustível.
• Limpe imediatamente qualquer derramamento.

DEPOIS:
• Abra escotilhas e ventile o compartimento do motor.
• Ligue o EXAUSTOR/BLOWER da praça de máquinas por alguns minutos ANTES de dar a partida — isso expele os vapores de gasolina acumulados no porão.
• Cheire o porão; se sentir cheiro forte de combustível, NÃO dê a partida — investigue antes.

Embarcações a gasolina exigem ventilação adequada da praça de máquinas (princípio extraído da SOLAS e exigido em vistoria).',
'{combustivel,abastecimento,incendio,explosao,blower,ventilacao,seguranca}', 91),

('NORMAM-211', 'Crianças a Bordo e Coletes Infantis',
'A segurança de crianças a bordo exige atenção redobrada:

COLETES ADEQUADOS AO PESO:
• Bebê: colete específico para até ~15 kg, com apoio de cabeça e alça de resgate.
• Infantil: colete para até ~30 kg.
• O colete de adulto NÃO serve para criança — uma criança pode escorregar para fora dele na água.

BOAS PRÁTICAS:
• Crianças devem usar o colete o tempo todo enquanto a embarcação está em movimento ou em águas abertas.
• Experimente o colete em terra: levante a criança pelas alças dos ombros — se a cabeça escorregar, o colete é grande demais.
• Mantenha vigilância constante; defina um adulto responsável por cada criança.
• Ensine regras simples: sentar enquanto navega, segurar firme, não correr no convés molhado.

A quantidade de coletes a bordo deve ser suficiente e do tamanho correto para TODOS os ocupantes, incluindo crianças (requisito verificado em vistoria).',
'{crianca,colete_infantil,bebe,seguranca,salva_vidas,vigilancia}', 92),

('NORMAM-211', 'Fundeio e Atracação em Marina',
'Fundear (ancorar) e atracar com segurança protege a embarcação, as pessoas e o meio ambiente:

FUNDEIO:
• Escolha um fundo de boa tença (areia ou lama firme); evite fundo de pedra ou cascalho onde a âncora arrasta.
• Solte amarra/cabo suficiente: como regra prática, de 5 a 7 vezes a profundidade da água (quanto pior o tempo, mais amarra).
• Confira se a âncora "agarrou" observando pontos de referência em terra; se a embarcação arrastar, recolha e refundeie.
• Em fundeadouros de marina e iate clube, respeite o limite de 3 nós e mantenha distância das outras embarcações.

ATRACAÇÃO EM MARINA:
• Aproxime-se devagar, contra o vento ou a corrente, para ter controle.
• Prepare defensas (boias de proteção) e cabos de amarração antes de chegar.
• Use spring (cabo diagonal) para evitar que a embarcação avance ou recue na vaga.
• Respeite as orientações da marina e a sinalização do canal de acesso.

RESPONSABILIDADE: o condutor é responsável por manobras seguras; danos a outras embarcações ou ao píer podem gerar responsabilidade civil.',
'{fundeio,ancora,atracacao,marina,amarracao,defensa,manobra}', 93),

('NORMAM-301', 'Avisos aos Navegantes, Cartas e Publicações (DHN)',
'A Diretoria de Hidrografia e Navegação (DHN) da Marinha do Brasil é responsável pelas informações oficiais de segurança da navegação:

PRINCIPAIS PUBLICAÇÕES:
• Cartas Náuticas: representam profundidades, perigos, balizamento e a configuração da costa. Devem estar atualizadas.
• Avisos aos Navegantes: publicação periódica que corrige as cartas e informa mudanças (alteração de balizamento, novos perigos, obras).
• Avisos-Rádio Náuticos: alertas urgentes transmitidos por rádio (perigos recém-detectados, áreas interditadas, exercícios navais).
• Lista de Faróis: relação dos sinais luminosos da costa.
• Tábua das Marés: previsão de altura e horário das marés por porto.
• Cartas de Risco e Roteiro: descrição detalhada da costa, portos e canais.

PARA O NAVEGANTE DE RECREIO:
• Use sempre cartas e publicações atualizadas (em papel ou eletrônicas homologadas — ENC).
• Consulte a Tábua das Marés antes de navegar em áreas de pouca profundidade.
• Verifique os Avisos aos Navegantes da sua área antes de viagens mais longas.',
'{dhn,carta_nautica,avisos_navegantes,tabua_mares,farois,enc,navegacao}', 80),

('NORMAM-301', 'Praticagem — Quando o Prático é Obrigatório',
'A praticagem é o serviço prestado por um prático (profissional com conhecimento local) para auxiliar o comandante em manobras em zonas de difícil navegação (entrada de portos, canais, barras).

REGRA GERAL:
• A praticagem é OBRIGATÓRIA para navios de grande porte nas Zonas de Praticagem estabelecidas pela Autoridade Marítima, por questão de segurança e proteção ao meio ambiente.
• Embarcações de esporte e recreio, em geral, são DISPENSADAS de praticagem, por serem de pequeno porte.

ATENÇÃO:
• Mesmo dispensado, o condutor de recreio deve respeitar as regras locais da Zona de Praticagem, manter-se nos canais sinalizados e dar passagem a navios de grande porte com manobra restrita.
• Em algumas áreas específicas, a Capitania local pode estabelecer exigências próprias — consulte as normas da Capitania da jurisdição antes de navegar em portos comerciais movimentados.

Navios grandes têm manobra e parada limitadas; a embarcação de recreio deve sempre se manter afastada e nunca cruzar a proa de um navio em canal estreito.',
'{praticagem,pratico,zona_praticagem,porto,canal,navio,manobra}', 81),

('NORMAM-401', 'Fundeio em Áreas Ambientais Sensíveis (Recifes e APAs)',
'Além das regras de poluição, a navegação de recreio deve respeitar a proteção de ecossistemas sensíveis:

ÁREAS PROTEGIDAS:
• Unidades de Conservação marinhas e Áreas de Proteção Ambiental (APAs) são fiscalizadas pelo ICMBio e órgãos ambientais. Muitas têm regras próprias de acesso, velocidade e fundeio.
• Em parques e reservas marinhas, pode haver proibição de fundeio, limite de embarcações e exigência de uso de boias de amarração (poitas) fornecidas.

FUNDEIO RESPONSÁVEL:
• NÃO fundeie sobre recifes de coral, bancos de algas ou fundos sensíveis — a âncora destrói o ecossistema. Procure fundo de areia.
• Onde houver boias de amarração ecológicas instaladas, use-as em vez de lançar a âncora.
• Respeite a sinalização de áreas de mergulho, berçários e zonas de exclusão.

BOAS PRÁTICAS:
• Não descarte lixo, óleo ou esgoto nessas áreas (regras da NORMAM-401 e MARPOL se aplicam integralmente).
• Reduza a velocidade para proteger fauna (peixes-boi, tartarugas, golfinhos) e evitar ressaca que danifica as margens.

Infrações ambientais em UCs podem gerar multa e responsabilização criminal (Lei 9.605/1998).',
'{meio_ambiente,recife,coral,apa,icmbio,fundeio,unidade_conservacao,poita}', 30)

on conflict (norma_codigo, secao) do nothing;
