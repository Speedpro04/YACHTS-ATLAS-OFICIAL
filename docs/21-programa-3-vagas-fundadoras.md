# Yachts Atlas — Programa das 3 Vagas Fundadoras

## Objetivo

Criar 3 vagas limitadas para uso inicial do Yachts Atlas com foco em prova social, coleta de cases e preparação do lançamento comercial.

O programa existe para transformar os primeiros usuários em material real de venda, com histórico, depoimentos, imagens e métricas.

---

## Oferta

- 3 vagas apenas
- acesso por 6 meses a partir da data de inscrição
- cobrança automática de USD 250/mês após o vencimento
- acesso travado se a cobrança não for confirmada
- foco em parceiros com operação real e potencial de case público

---

## Posicionamento

O programa deve ser comunicado como:

- acesso antecipado
- programa fundador
- vagas limitadas para parceiros pioneiros

Evitar tratar como “free” aberto. A proposta é exclusiva e ligada a uma relação comercial futura desde o começo.

---

## Regras Operacionais

1. Registrar a data de inscrição de cada conta.
2. Calcular a data de término com base em 6 meses.
3. Rodar um scheduler diário para localizar contas vencendo.
4. No vencimento, iniciar a cobrança em USD 250/mês.
5. Se a cobrança falhar, travar o acesso da conta.
6. Manter o banco sem restrição estrutural artificial para os dados do produto.
7. Aplicar a trava na camada de aplicação.

---

## Estrutura de Dados Mínima

Campos recomendados para a conta piloto:

- `signed_up_at`
- `billing_starts_at`
- `billing_status`
- `access_status`
- `pilot_program = true`
- `pilot_end_at`
- `pilot_case_notes`

Esses campos permitem governar o ciclo comercial sem restringir o modelo de dados do produto.

---

## Fluxo de Cobrança

### Durante os 6 meses

- conta ativa
- acesso liberado
- coleta de uso e prova social
- acompanhamento de métricas e depoimentos

### Após o vencimento

- alterar status para cobrança ativa
- tentar cobrança mensal de USD 250
- se a cobrança for confirmada, liberar acesso normal
- se a cobrança não for confirmada, travar o acesso até regularização

---

## Critérios de Seleção

As 3 vagas devem ir para perfis que tenham:

- operação real
- uso recorrente
- disposição para dar feedback
- potencial de virar case comercial
- abertura para autorizar uso de marca e depoimentos

Evitar perfis que só querem testar sem compromisso ou sem contexto real.

---

## O que Coletar

Durante o piloto, registrar:

- nome do parceiro
- contexto da operação
- dor principal antes do uso
- valor percebido após o uso
- imagens da interface em uso
- depoimentos curtos e longos
- métricas de organização e produtividade

Esses materiais devem alimentar:

- home principal
- landing page de lançamento
- propostas comerciais
- social proof em apresentações

---

## Execução Recomendada

### Passo 1

- selecionar os 3 parceiros
- confirmar elegibilidade
- alinhar expectativa de cobrança futura

### Passo 2

- registrar a data de inscrição
- ativar o acesso
- iniciar a coleta de evidências

### Passo 3

- acompanhar o uso por 6 meses
- documentar resultados
- preparar materiais de lançamento

### Passo 4

- ativar cobrança no vencimento
- bloquear acesso se necessário
- transformar os casos em prova social pública

---

## Observação Estratégica

O programa só funciona bem se houver disciplina:

- oferta clara desde o início
- prazo real
- cobrança automática
- bloqueio após vencimento se não houver regularização

Essa disciplina protege o valor do produto e evita que o piloto vire acesso gratuito indefinido.

