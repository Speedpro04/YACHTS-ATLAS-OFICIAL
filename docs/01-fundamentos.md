# Yachts Atlas — Fundamentos do Produto

## 1. Frase Central

**"O registro digital imutável para proprietários de ativos náuticos — manutenção, documentação e valor agregado em um só lugar."**

---

## 2. O Que É o Yachts Atlas

Infraestrutura de dados para ativos náuticos. Não é SaaS. Não é uma marina virtual. Não é um marketplace.

É um repositório centralizado onde o dono do ativo armazena, organiza e protege tudo que sustenta o valor e a legalidade do seu iate, lancha, veleiro ou jet-ski.

**Resumo:** Sistema de registro de histórico digital com integridade cryptográfica.

---

## 3. O Que O Yachts Atlas NÃO É

| NÃO É | PORQUÊ |
|---|---|
| Marina virtual | Não gerencia vagas, água, energia ou atendimento |
| Marketplace | Não vende itens, não faz intermediação |
| SaaS tradicional | Não cobra assinatura mensal por acesso |
| Rede social | Não tem feed,/posts ou engajamento |
| Aplicativo de gestão operacional | Não controla horários de saída, Crew, combustible |

---

## 4. Problema Exato Que Resolve

**Hoje, o dono de um ativo náutico tem:**

- Documentos espalhados (e-mail, papel, Google Drive, HD externo)
- Sem versão controle (não sabe qual documento é o mais recente)
- Sem proof de integridade (ninguém garante que o arquivo não foi alterado)
- Difícil de transferir na venda (documentação incompleta = preço menor)
- Sem histórico centralizado de manutenções
- Seguros e certidões vencerem sem aviso

**O Yachts Atlas resolve:**
> Um lugar único, íntegro e auditável para tudo que envolve o ativo — do documento de origem à última manutenção.

---

## 5. Para Quem Existe

### Donos de Ativos Náuticos

- Proprietários de iates (10m+)
- Proprietários de lanchas (5m-12m)
- Proprietários de veleiros
- Proprietários de jet-skis
- Proprietários de barcos de pesca esportiva

### Ecossistema

- Marinas e clubes náuticos (gestão de múltiplos ativos)
- Seguradoras (consulta de histórico)
- Corretores e consultores de venda (due diligence)
- Técnicos e yards (histórico de manutenção)
- Inspetores e surveyors

---

## 6. O Que Acontece Sem o Yachts Atlas

- **_na venda_**: Documentação incompletaubaixa o valor do ativo em 10-30%
- **_no seguro_**: Dificuldade em comprovar estado de conservação
- **_na manutenção_**: Sem histórico = serviços重复idos ou negligenciados
- **_na transferência_**: Novo dono herda "caos documental"
- **na fiscalização_**: Problemas com документаção irregular
- **em caso de sinistro_**: Prova difícil de responsabilidade e valor

---

## 7. Proposta de Valor

| Para o Dono | Valor Entregue |
|---|---|
| Gestão documental | Tudo em um só lugar, organizado por ativo |
| Integridade | Hash cryptográfico em cada arquivo = proof de que não foi alterado |
| Histórico | Linha do tempo completa: desde a fabricação até hoje |
| Valor residual | Documentação completa = ativo vale mais na venda |
| Conformidade | LGPD compliant, dados seguros |
| Portabilidade | Exporta tudo se quiser sair |

---

## 8. Nome do Produto

**Yachts Atlas**

- Atlas = mapa, referência, aquilo que sustenta a navegação
- Yachts = foco em ativos náuticos (ampliável depois)
- Sólido, profissional, sem frescura

---

## 10. Stack Técnica

| Componente | Tecnologia |
|---|---|
| Backend | FastAPI |
| Banco de dados | Supabase (PostgreSQL) |
| Armazenamento | Supabase Storage |
| Análise de dados | Polars |
| Notificações WhatsApp | Evolution API |
| Frontend | Vite + Tailwind CSS |
| Infraestrutura | EasyPanel + Docker |
| Infraestrutura | A definir |

---

## 11. Repositório

**GitHub:** https://github.com/Speedpro04/yachts-atlas.git

---

## 12. Área de Uploads

Área designada para upload de documentos, imagens, PDFs e arquivos relacionados ao ativo.

**Tipos aceitos:**
- PDF, JPG, PNG, HEIC
- Documentos de registro (RGP, documento, certidões)
- Relatórios de inspeção (survey)
- Fotos e vídeos do ativo
- Notas fiscais e recibos

---

## 13. Versão

v0.1 — Fundamentos (rascunho inicial)

---

## 14. Data

2026-04-22