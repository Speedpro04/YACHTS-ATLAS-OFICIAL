# Programa de Prova Social e Lançamento

## Objetivo

Estruturar um piloto com **3 vagas limitadas** para gerar prova social real antes do lançamento comercial do Yachts Atlas.

A ideia central é simples:

- liberar o uso do sistema por **6 meses**
- coletar casos reais, depoimentos, imagens e resultados
- usar esse material nas **landing pages de lançamento** e na **page principal**
- iniciar a cobrança de **USD 250/mês** após o prazo combinado

Isso posiciona o produto como um **programa fundador / acesso antecipado**, e não como um teste solto sem compromisso.

---

## Tese Comercial

O objetivo não é apenas colocar três pessoas usando o sistema.
O objetivo é transformar essas três contas em:

- prova social
- estudo de caso
- narrativa de valor
- base de conversão para lançamento

Se essas contas forem bem escolhidas, elas podem sustentar:

- screenshots reais para LP
- depoimentos
- prints de dashboards
- antes e depois da organização documental
- métricas de economia de tempo e ganho operacional

---

## Estrutura da Oferta

### Vagas

- **3 vagas apenas**
- seleção manual
- foco em perfis com alto potencial de gerar histórias fortes

### Duração

- **6 meses de uso gratuito**
- ao final do período, entrada automática no plano pago

### Valor posterior

- **USD 250/mês**
- valor comunicado desde o início
- sem surpresa para o cliente

### Posicionamento

Em vez de falar apenas “3 vagas gratuitas”, usar a narrativa:

- **Programa fundador**
- **Acesso antecipado**
- **Vagas limitadas para parceiros pioneiros**

Isso protege o posicionamento de valor do produto.

---

## Regras do Programa

1. O acesso é liberado por 6 meses a partir da data de inscrição.
2. Durante o piloto, a conta deve ser usada de forma real.
3. O uso pode ser sem restrição estrutural no banco de dados, desde que o controle comercial seja aplicado pela camada de aplicação.
4. A cobrança deve iniciar automaticamente após o prazo.
5. Após o vencimento, o acesso da conta deve ficar travado até a ativação da cobrança ou regularização manual.
6. A conta piloto deve autorizar uso de marca, depoimentos e resultados para materiais comerciais.

---

## Regra de Cobrança

O controle principal deve ser baseado na **data de inscrição**.

### Fluxo

- registrar `signed_up_at`
- calcular `billing_starts_at = signed_up_at + 6 months`
- scheduler diario verifica contas que chegaram ao prazo
- ao atingir a data, mudar o status para cobrança ativa
- executar a tentativa de cobrança no valor de **USD 250/mês**
- se a cobrança não for confirmada, manter o acesso travado

### Observação operacional

Na prática, isso significa:

- **não travar o banco de dados**
- manter o modelo de dados livre para registrar uso, arquivos, historico e dossiês
- aplicar a regra comercial no scheduler e no fluxo de billing
- aplicar o bloqueio de acesso na camada de aplicação após o vencimento

Assim o sistema continua flexível internamente, mas a disciplina comercial fica garantida.

---

## O que Coletar Durante os 6 Meses

Para cada conta piloto, registrar:

- nome da marina ou parceiro
- contexto de uso
- dores resolvidas
- tempo economizado
- quantidade de documentos organizados
- quantidade de dossiês gerados
- capturas de tela de uso real
- depoimento curto e depoimento longo
- resultado operacional percebido

Esses dados alimentam:

- LP de lançamento
- home principal
- sequência comercial
- proposta para novas marinas

---

## Como Usar na Página de Lançamento

As 3 contas piloto devem virar material de conversão com três vânculos:

1. **Prova visual**
   - telas reais do sistema
   - dashboard em uso
   - fluxos de documento e dossiê

2. **Prova narrativa**
   - história do parceiro
   - problema antes
   - mudança depois

3. **Prova de resultado**
   - organização
   - ganho de velocidade
   - valorização do ativo
   - redução de retrabalho

---

## Critérios de Seleção das 3 Vagas

Selecionar parceiros que tenham:

- operação ativa
- volume real de documentos ou ativos
- capacidade de responder rápido
- interesse em aparecer como caso público
- perfil alinhado com o posicionamento premium

Evitar perfis que:

- queiram apenas “testar por curiosidade”
- não tenham operação real
- não queiram fornecer feedback
- não autorizem uso de prova social

---

## Linha do Tempo

### Fase 1

- selecionar as 3 contas
- configurar acesso
- registrar data de inscrição
- alinhar expectativa comercial

### Fase 2

- acompanhar o uso durante 6 meses
- coletar depoimentos e métricas
- documentar antes e depois

### Fase 3

- preparar LPs com a prova social
- abrir lançamento oficial
- ativar cobrança de USD 250/mês

---

## Recomendação Estratégica

A melhor leitura para esse modelo é:

- **não vender como gratuito**
- vender como **acesso antecipado com entrada limitada**
- deixar claro desde o início que existe conversão para pago
- tratar os 6 meses como período de construção de caso e validação, não como benefício aberto

Isso tende a trazer parceiros mais alinhados e aumenta a qualidade da prova social.

---

## Resultado Esperado

Se a execução for boa, o programa deve gerar:

- 3 cases reais
- 3 conjuntos de depoimentos
- 1 narrativa forte de lançamento
- 1 base de precificação validada
- 1 funil inicial com autoridade

Em resumo: usar 6 meses para comprar clareza, confiança e lastro comercial antes de escalar.
