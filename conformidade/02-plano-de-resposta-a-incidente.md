# Plano de Resposta a Incidente de Segurança

**Yachts Atlas — AXOS HUB · CNPJ 26.998.571/0001-50**
LGPD, art. 48. Versão 1 — 31/08/2026.

> **Escrito para a realidade de hoje: uma empresa de uma pessoa.**
> Um plano que finge ter turno de plantão e comitê de crise é pior que nenhum
> plano — na hora do incidente ninguém o segue, e depois ele prova que a
> empresa disse o que não fazia. Este descreve o que **uma pessoa** consegue
> executar. Quando houver equipe, ele muda.

---

## 1. O que conta como incidente

Qualquer evento que comprometa **confidencialidade, integridade ou
disponibilidade** de dado pessoal. Na prática, para esta plataforma:

| Tipo | Exemplo concreto aqui |
|---|---|
| **Acesso indevido** | credencial de marina usada por terceiro; chave de serviço vazada em repositório ou log |
| **Vazamento** | dossiê entregue a destinatário errado; bucket `media` exposto |
| **Cruzamento entre marinas** | uma marina alcançando dado de outra — o risco estrutural desta arquitetura |
| **Adulteração** | divergência entre o conteúdo de um registro e seu selo SHA-256 |
| **Indisponibilidade prolongada** | banco ou aplicação fora por tempo que impeça a marina de trabalhar |
| **Perda** | exclusão de dado que deveria ser imutável |

**Um caso merece destaque:** a adulteração de registro é, para esta empresa, o
incidente mais grave possível — não pelo volume de dado exposto, mas porque
destrói a única coisa que o produto vende. Ele tem seção própria (5).

## 2. Como um incidente chega até nós

- **Verificação de integridade divergente** — `fn_verificar_integridade_ativo`
  devolvendo `integro = false` para qualquer ativo. É o sinal mais forte.
- **Linter de segurança do Supabase** — deve ser rodado a cada mudança de
  esquema. Foi assim que se descobriu, em 31/08/2026, que
  `fn_verificar_integridade_ativo` era executável por qualquer usuário
  autenticado.
- **Trilha de auditoria** — `audit_logs` registra IP, conta e ação; o relatório
  administrativo (`/api/v1/auditoria/relatorio`) permite olhar o conjunto.
- **Aviso de terceiro** — marina, armador, pesquisador ou o próprio Supabase.
- **Log da aplicação** — erros repetidos, 403 em série, picos de tráfego.

## 3. As primeiras duas horas

Nesta ordem. Não pule a contenção para investigar — dado que continua saindo
enquanto se investiga é dano que se escolheu permitir.

**1. Conter.** Corte o caminho antes de entender a causa.
   - credencial suspeita → revogar a chave e rotacionar
   - conta comprometida → desativar no Supabase Auth
   - função ou rota vazando → revogar `EXECUTE` ou derrubar a rota
   - vazamento em massa em curso → tirar a aplicação do ar é aceitável

**2. Preservar.** Antes de consertar, guarde a prova.
   - exportar `audit_logs` e `integridade_logs` da janela do incidente
   - anotar hora, o que foi visto e o que foi feito, **em ordem**
   - **não apagar nada** — nem log ruidoso, nem linha suspeita

**3. Medir.** Responda três perguntas com número, não com impressão.
   - **quais titulares?** (marinas, armadores, solicitantes — quantos)
   - **quais dados?** (contato? documento? histórico técnico? arquivo?)
   - **por quanto tempo esteve exposto?**

**4. Avisar quem opera.** O fundador é quem decide. Não existe escalonamento
   interno hoje — e fingir que existe seria mentir num documento de
   conformidade.

## 4. Comunicação

**Prazo.** A LGPD exige comunicação à ANPD e aos titulares em **prazo
razoável**; a orientação da própria ANPD trabalha com **3 dias úteis** a
partir do conhecimento. Trate 3 dias úteis como o prazo, não como o teto.

**Quando comunicar.** Quando houver risco ou dano relevante ao titular. Na
dúvida, comunique — a omissão pesa mais que o excesso.

**Aos titulares**, diga sem rodeio: o que aconteceu, quais dados, quando, o
que já foi feito, o que a pessoa deve fazer. Sem eufemismo. Uma marina que
descobre depois que foi poupada da verdade não volta.

**À ANPD**, pelo canal oficial, com a medição da seção 3.

**Contato de origem:** `contato@yachtsatlas.online` — e o encarregado, quando
designado (ver `01-registro-de-operacoes-de-tratamento.md`, seção 8).

## 5. Incidente de integridade — procedimento específico

Se a verificação apontar `integro = false`:

1. **Não corrija o registro.** A divergência é a prova. Alterar o conteúdo
   para "bater" com o selo destruiria a evidência e seria, ele mesmo, um ato
   de adulteração.
2. **Identifique o alcance:** `fn_verificar_integridade_ativo` devolve
   `conferem`, `divergem` e `sem_selo` por ativo. Rode em todos os ativos, não
   só no que acusou.
3. **Verifique se foi redação LGPD legítima.** `registros.redigido_em`,
   `redigido_campos`, `hash_pre_redacao` e `lgpd_solicitacao` distinguem uma
   redação autorizada de uma adulteração. Uma redação legítima **não** deve
   aparecer como divergência — se aparecer, o defeito é no recálculo.
4. **Preserve o par de hashes** (anterior e atual) antes de qualquer ação.
5. **Comunique a marina afetada** mesmo que o dado não tenha vazado. Ela
   entregou dossiês a terceiros com base naquele selo; precisa saber.
6. **Avalie os dossiês já emitidos** daquele ativo em `dossie_emitidos` e
   `dossie_saidas` — quem recebeu documento assinado sobre um registro agora
   duvidoso.

## 6. Depois

**Post-mortem escrito, sempre**, mesmo em incidente pequeno, mesmo sem
vazamento. Quatro perguntas:

1. O que aconteceu, em ordem cronológica?
2. Por que o sistema permitiu?
3. Por que não foi detectado antes?
4. O que muda para que não se repita — em **código ou configuração**, não em
   intenção?

A resposta da pergunta 4 vira item numerado no `PRD.md` e, quando couber,
teste automatizado. Correção sem teste é promessa; teste é o que impede a
regressão de voltar em silêncio.

## 7. O que este plano ainda não tem

Dito aqui para que ninguém descubra na hora errada:

- **Sem monitoramento ativo.** Nada avisa sozinho que a integridade divergiu —
  a verificação roda quando alguém pede. Um trabalho agendado que varra os
  ativos e alerte é o próximo passo natural.
- **Sem plano de continuidade testado.** Existe backup gerenciado pelo
  Supabase; **a restauração nunca foi ensaiada**. Backup não testado é
  esperança, não é backup.
- **Sem segunda pessoa.** Se o fundador estiver indisponível, não há quem
  execute este plano. É consequência aceita do estágio da empresa, não um
  descuido — mas precisa estar escrito.
