# Briefing — Contador de vagas fundadoras na página de LANÇAMENTO

> Documento de passagem. Feito para ser lido numa pasta/sessão diferente,
> sem acesso ao backend. Tudo o que o backend precisava fazer **já está
> pronto e no ar** — o que falta é só consumir e exibir.
>
> Data: 18/08/2026

---

## 1. O que já existe (não precisa mexer no backend)

O backend já decide sozinho o preço de cada marina e já reserva a vaga.
A página de lançamento só precisa **ler e mostrar** o número.

Regras que o backend aplica hoje:

- **4 vagas fundadoras por estado**, em 5 estados: **SC, SP, RJ, ES, BA**
- Total: **20 vagas** (4 × 5). O 20 é consequência, não uma cota separada.
- Fundadora paga **US$ 200/mês**. Depois disso, **US$ 250/mês**.
- Marina de **qualquer outro estado** vai direto para os US$ 250.
- A vaga é **reservada no cadastro** e segurada por **60 minutos**. Se a
  marina não pagar nesse prazo, a vaga volta para o estado sozinha.
- Uma vaga conta como ocupada se estiver **paga** OU **reservada dentro do
  prazo**. É o mesmo número que decide o preço no checkout.

---

## 2. O endpoint

```
GET https://yachtsatlas.online/api/v1/leads/marina/vagas
```

Sem autenticação. Sem parâmetros.

**Resposta real (testada em produção hoje):**

```json
{
  "estados": ["SC", "SP", "RJ", "ES", "BA"],
  "total": 20,
  "ocupadas": 0,
  "restantes": 20,
  "vagas_por_estado": 4,
  "por_estado": {
    "SC": { "total": 4, "ocupadas": 0, "restantes": 4 },
    "SP": { "total": 4, "ocupadas": 0, "restantes": 4 },
    "RJ": { "total": 4, "ocupadas": 0, "restantes": 4 },
    "ES": { "total": 4, "ocupadas": 0, "restantes": 4 },
    "BA": { "total": 4, "ocupadas": 0, "restantes": 4 }
  }
}
```

Dá para montar tanto **"X de 20 vagas"** (usando `ocupadas` / `total`)
quanto **"restam 2 em SC"** (usando `por_estado.SC.restantes`).

---

## 3. 🚨 CORS — FAÇA ISTO PRIMEIRO, senão nada funciona

**A página de lançamento roda em `lancamento.yachtsatlas.online`, e esse
domínio NÃO está liberado no backend hoje.**

Para o navegador, subdomínio é origem diferente. O site principal funciona
porque o frontend chama `/api/v1` na mesma origem — CORS nem entra em cena.
Mas `lancamento.yachtsatlas.online` chamando `yachtsatlas.online` é
cross-origin e **vai ser bloqueado**.

O sintoma é um erro de CORS no console do navegador. Não é bug do endpoint:
ele responde 200 normalmente para quem tem permissão.

### Como resolver (não precisa mexer em código nem dar push)

No **EasyPanel**, no serviço do **backend**, edite a variável de ambiente
`ALLOWED_ORIGINS` e deixe assim:

```
["http://localhost:5173","http://localhost:3000","https://yachts.axoshub.com","https://yachtsatlas.com","https://www.yachtsatlas.com","https://yachtsatlas.online","https://www.yachtsatlas.online","https://lancamento.yachtsatlas.online"]
```

Depois **reinicie o backend**. É só isso — nenhum commit, nenhum deploy de
código.

> Valor atual em produção (para conferência): a lista tinha só
> `localhost:5173`, `yachts.axoshub.com`, `yachtsatlas.com` e
> `www.yachtsatlas.com`. Confira no EasyPanel antes de substituir, para não
> apagar algum domínio que tenha sido adicionado depois.

Em desenvolvimento local nas portas 5173 ou 3000 já funciona sem mexer em nada.

---

## 4. O que a página deve fazer quando a API falhar

Este é o ponto que exige critério. **Nunca mostre um número inventado.**

Se a chamada falhar ou demorar, escolha um destes, nessa ordem de preferência:

1. **Não mostrar o contador** (esconder o bloco inteiro). É o mais honesto.
2. Mostrar texto sem número: *"Vagas fundadoras limitadas"*.

**Não faça:** cair num número fixo tipo "12 de 20". A página estaria
prometendo uma vaga que o checkout pode negar — e o cliente descobre isso
só depois de preencher o formulário.

O backend já erra para o lado seguro: se ele não conseguir reservar a vaga,
manda a marina para o checkout de US$ 250, não para o de US$ 200.
A página precisa ter a mesma postura.

---

## 5. Cache

Não cacheie por muito tempo. As vagas mudam quando alguém paga, e um número
velho na tela é uma promessa que o checkout não honra.

Sugestão: no máximo **60 segundos**, ou simplesmente buscar a cada
carregamento da página. O endpoint é leve (uma função SQL, tabela de 20 linhas).

---

## 6. 🚫 Onde este contador NÃO pode aparecer

**Não colocar na página oficial.**

A página oficial anuncia apenas a mensalidade de **US$ 250** e não fala em
vagas fundadoras. O contador é exclusivo da página de **lançamento**.

---

## 7. Números velhos para revisar na LP

Se a sua página de lançamento tiver números escritos direto no código,
confira contra o modelo definitivo (4 por estado / 20 no total / US$ 200).

Na LP que está no repo principal (`/marina-parceira`) existem hoje três
números que não conversam entre si:

| Onde | O que diz | Situação |
|---|---|---|
| Chapéu do topo | "3 Vagas Fundadoras" | resquício do piloto antigo de 3 vagas grátis |
| Barra de progresso | "12 de 120 vagas ocupadas" | número fixo, inventado |
| Texto de apoio | "Meta pública: 120 vagas" | é outra coisa: a meta de longo prazo a US$ 250 |

O ideal é que **nenhum número de vaga fique escrito no código** — todos vêm
do endpoint. Aí a página nunca desencontra do banco.

Decisão de texto (é do fundador, não técnica): se o chapéu vira
"20 Vagas Fundadoras" e se a meta das 120 continua aparecendo.

---

## 8. Exemplo mínimo

```js
const [vagas, setVagas] = useState(null)

useEffect(() => {
  fetch('https://yachtsatlas.online/api/v1/leads/marina/vagas')
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .then(setVagas)
    .catch(() => setVagas(null))   // falhou: esconde o contador
}, [])

// Na renderização: só mostra se vagas existir.
{vagas && (
  <span>
    <strong>{vagas.ocupadas}</strong> de {vagas.total} vagas ocupadas
  </span>
)}
```

Para o corte por estado, depois que a marina escolher o estado:

```js
const restantesNoEstado = vagas?.por_estado?.[uf]?.restantes
// restantesNoEstado === undefined -> estado fora do programa (US$ 250)
```

Repare: se a UF não estiver em `por_estado`, é porque aquele estado **não faz
parte do programa fundador**. Nesse caso a marina paga US$ 250 — e a página
não deve prometer desconto nenhum para ela.

---

## 9. Resumo em uma linha

Busque `GET /api/v1/leads/marina/vagas`, mostre `ocupadas`/`total`
(ou o corte por estado), esconda o bloco se a chamada falhar, e não
replique nenhum número fixo no código.
