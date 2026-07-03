# Melhorias no Painel Técnico e Geração de Dossiês (REV-01)
*Yachts Atlas — Protocolo de Custódia e Conformidade*

Este documento formaliza as especificações e melhorias aprovadas para o Painel Técnico e o motor de geração de Dossiês de Custódia Náutica.

---

## 1. Aba de Bombas de Drenagem / Porão (`drenagem`)

Como embarcações de lazer e comerciais de alto valor permanecem constantemente expostas ao meio aquático, o monitoramento preventivo do sistema de esgotamento e porão é de segurança crítica.

### Especificação de Campos
- **Fabricante**: Fabricante da bomba de porão (Rule, Johnson Pump, Attwood, Jabsco...).
- **Modelo**: Modelo específico (ex: Rule-Mate 2000 GPH).
- **Zona / Compartimento**: Localização física da bomba (`Proa`, `Sala de Máquinas`, `Popa`, `Meio / Cabines`, `Outra`).
- **Vazão (GPH)**: Vazão nominal em galões por hora (ex: 2000 GPH).
- **Teste do Automático (Float Switch)**: Status operacional (`Operacional`, `Avaria / Falha`, `Não possui automático`).
- **Alarme de Nível Alto (High Water Alarm)**: Status operacional do alarme independente de inundação (`Instalado e Operacional`, `Instalado com Falha`, `Não possui alarme instalado`).
- **Fiação e Conexões**: Estado visual e elétrico (`Excelente (Estanque)`, `Bom`, `Atenção (Marcas de Oxidação)`, `Crítico (Exposta / Curto)`).
- **Filtro / Ralo de Sucção**: Condição física (`Limpo / Desobstruído`, `Necessita Limpeza (Parcialmente obstruído)`, `Obstruído / Danificado`).
- **Observações**: Campo aberto para detalhar testes de vazão e tempos de resposta.

### Evidências Obrigatórias
1. **Foto da bomba instalada**: Foto nítida mostrando a bomba de porão montada na respectiva zona, o automático e a vedação da fiação.
2. **Vídeo de teste de funcionamento**: Vídeo de até 3 minutos comprovando o acionamento mecânico manual da boia (automático) e a respectiva sucção/resposta do alarme de nível alto.

---

## 2. Checklist NORMAM-211/212 (Aba de Segurança)

Adequação às exigências da Marinha do Brasil (DPC - Diretoria de Portos e Costas) para garantir conformidade regulatória nas fiscalizações (Capitanias e Delegacias).

### Estruturação de Campos (Checklist Interativo)
Os campos abaixo utilizam o novo componente gráfico `checkbox` do formulário, operando com **trava forte` de preenchimento (`required: true`) para garantir que o selo de segurança só seja emitido sob conformidade total de salvatagem:

- **Coletes Homologados**: Coletes em quantidade e classes adequadas para a lotação máxima permitida da embarcação.
- **Boia Circular com Retinida**: Boia circular homologada, com cabo retinida flutuante sem emendas e em bom estado de conservação.
- **Sinalizadores Pirotécnicos**: Fogos de artifício e sinalizadores de socorro homologados dentro do prazo de validade.
- **Extintores de Incêndio**: Extintores portáteis com carga pressurizada, lacre intacto e validade vigente, distribuídos nas posições regulamentares.
- **Esgotamento de Porão**: Bombas de esgotamento manuais e automáticas testadas e operando normalmente.
- **Equipamento de Fundeio (Âncora e Cabos)**: Âncora adequada ao porte da embarcação, amarras e cabos em bom estado e com comprimento regulamentar.
- **Kit de Primeiros Socorros**: Estojo de primeiros socorros abastecido com medicamentos válidos e materiais de emergência.
- **Luzes de Navegação e Sinalização**: Luzes de bordo (BB/BE), alcançado e mastro operacionais para navegação em período noturno.
- **Buzina e Refletor de Radar**: Dispositivos sonoros de sinalização e refletor de radar instalados e funcionais.
- **Rádio VHF/HF e Equipamento de Salvaguarda**: Transceptor homologado ativo, com DSC funcional e antenas em perfeito estado.

---

## 3. Fluxo de Geração de Dossiê

Para profissionalizar o ecossistema, o acesso ao gerador de dossiês foi unificado tanto no painel interno de cada ativo quanto na área administrativa de controle da marina.

### Modificações no Layout e Sidebar
1. **Sidebar Navigation**: O item anteriormente chamado "Dossiês" passa a ser denominado **"Gerar Dossiê"** (mantendo o ícone `FileCheck`).
2. **Página de Solicitações**: A página `/app/solicitacoes-dossie` agora possui duas abas principais:
   * **Aba 1: Gerar Dossiê**: Apresenta barra de pesquisa de embarcações para acesso e emissão imediata do PDF.
   * **Aba 2: Pedidos de Acesso**: Lista as solicitações de liberação externa feitas por brokers ou compradores terceiros.
3. **Painel Técnico do Ativo (AtivoHub)**: A aba "Dossiê" do técnico renderiza o mesmo controle de emissão rápida com acompanhamento do limite.

---

## 4. Política de Limite de Emissão de Dossiês (4/Ano)

Para evitar descontrole de versões e garantir o valor de auditoria do documento náutico, a plataforma limita a geração a **4 PDFs de Dossiê por ano (últimos 365 dias) por ativo**.

### Regras de Negócio e Auditoria
- **Persistência**: As datas e horas de geração são persistidas de forma segura.
- **Contabilidade Móvel**: O sistema avalia os últimos 365 dias. Caso existam 4 registros de geração nesse período, o botão de download é bloqueado.
- **Feedback Visual**: Quando bloqueado, o sistema substitui o controle de download por um alerta dourado informando:
  * "Limite anual de 4 dossiês atingido para esta embarcação."
  * "Próximo dossiê disponível em: DD/MM/AAAA" (calculado a partir da data de expiração da primeira das quatro gerações).

---

## 5. Ficha de Manutenção Especializada (`manutencao`)

Substitui a ficha genérica por uma estrutura focada em consumíveis e especificações mecânicas marítimas reais.

### Especificação de Campos Adicionados
- **Óleo do Motor**: Registro de marca, viscosidade (SAE 15W-40, 25W-40 Marine, etc.), tipo (Mineral, Sintético, OEM) e classificação API (CI-4, CJ-4, CK-4 para diesel moderno Tier 4).
- **Filtros e Separadores**: Part number e marca dos filtros de óleo e combustível, além de controle para o filtro de ar e o separador de água (Racor).
- **Sistema SCR e Emissões (Conformidade MARPOL Anexo VI / IMO Tier III)**: Controle estrito de presença de catalisador SCR. Inclui validação de Certificado EIAPP, monitoramento de alarmes de NOx, registro de manutenção/descarbonização do injetor de ureia e controle do volume (litros) e marca certificada (ISO 22241 / Inmetro) do Arla 32 abastecido.
- **Impeller e Zincos**: Comprovação de troca do rotor da bomba de água salgada (impeller) e dos ânodos de sacrifício (zincos) para proteção galvânica.

### Evidências Fotográficas Especiais
- **Foto do óleo drenado**: Para acompanhamento preventivo (cor, presença de contaminação por água doce/salgada ou limalha metálica).
- **Foto dos filtros removidos e novos**: Comprovação visual da troca.
- **Foto do horímetro**: Para registro imutável das horas do motor.

---

## 6. Ficha de Elétrica e Eletrônica (`eletrica`)
Registra o estado dos componentes de energia e navegação a bordo, expostos à oxidação galvânica e salinidade.
- **Banco de Baterias**: Tensão do banco (V), estado geral (teste de carga) e data.
- **Gerador de Bordo**: Fabricante, modelo e horímetro dedicado de funcionamento.
- **Isolamento Galvânico**: Registro de fugas de corrente elétrica (anti-corrosão).
- **Navegação**: Status operacional de GPS, Radar, Sondas e Piloto Automático.
- **Evidências**: Foto do painel elétrico principal aberto e laudo de baterias.

---

## 7. Ficha de Mastro e Velame (`velame`) — *Veleiros*
Vistoria estrutural e de impulsão crítica para a mastreação e velaria.
- **Cabos de Rigging**: Idade do rigging de aço (anos) e status contra micro-trincas/corrosão.
- **Velas**: Estado do tecido e costuras (Mestra, Genoa) e proteção UV.
- **Equipamentos de Convés**: Status de lubrificação de catracas e enrolador de genoa.
- **Evidências**: Foto da mastreação e fotos das velas esticadas.

---

## 8. Ficha de Pintura e Limpeza de Fundo (`pintura`)
Acompanhamento hidrodinâmico e anti-corrosão do casco no seco.
- **Antifouling (Tinta de Fundo)**: Tipo de tinta, marca, demãos e data no seco.
- **Costado e Polimento**: Registro de polimento e proteção do Gelcoat.
- **Ânodos de Sacrifício**: Registro de troca completa ou parcial dos ânodos (zincos).
- **Evidências**: Foto do casco no seco e fotos adicionais do polimento/pintura.

---

## 9. Ficha de Interior e Conforto (`interior`)
Garantia de habitabilidade das cabines e funcionamento da infraestrutura interna.
- **Ar Condicionado**: Limpeza de filtros/bandejas e status de carga de gás (gelando).
- **Dessalinizador**: Vazão real (L/h) e horômetro de uso das membranas.
- **Saneamento**: Status das bombas de esgoto interno, sanitário vácuo/manual e trituradores.
- **Estofados e Madeiras**: Status de conservação contra mofo e umidade.
- **Evidências**: Foto geral do salão/cabines e foto dos equipamentos (ar/dessalinizador).


