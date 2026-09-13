# E-mails do Supabase, em português

Os modelos de e-mail do Auth **não moram neste repositório** — são configuração
do projeto, em *Authentication → Emails* no painel do Supabase. Por isso este
arquivo: o texto fica versionado aqui, e o painel recebe uma cópia.

Saíam em inglês (*"Reset Your Password"*). Uma marca brasileira mandando link de
senha em inglês é o padrão clássico de phishing — e conta contra na entrega: foi
o que pesou no spam junto com o DKIM que faltava.

**Como aplicar:** painel do Supabase → projeto `Yachts_Atlas` → Authentication →
Emails → escolher o modelo → colar *Subject* e *Body* → Save. Um de cada vez.

**Variáveis** (deixar exatamente como estão, o Supabase substitui):
`{{ .ConfirmationURL }}`, `{{ .Token }}`, `{{ .TokenHash }}`, `{{ .SiteURL }}`,
`{{ .Email }}`, `{{ .Data }}`, `{{ .RedirectTo }}`.

**Só no modelo de troca de e-mail** existe `{{ .NewEmail }}`, e a diferença
importa: ali `{{ .Email }}` é o endereço **atual** e `{{ .NewEmail }}` é o
**novo**. Escrever "troca para {{ .Email }}" mandaria a pessoa confirmar o
endereço que ela está deixando.

Tom: sóbrio e direto. Sem emoji, sem exclamação, sem "clique aqui" — o botão diz
o que faz. Toda mensagem termina dizendo o que fazer se a pessoa não reconhecer
o pedido, porque é isso que separa um e-mail legítimo de um golpe aos olhos de
quem recebe.

---

## 1. Redefinição de senha (Reset Password)

**Subject:**

```
Redefinir a chave de acesso — Yachts Atlas
```

**Body:**

```html
<h2 style="font-family:Georgia,serif;color:#010c20;margin:0 0 16px">Redefinir a chave de acesso</h2>

<p style="font-family:Arial,sans-serif;color:#333;line-height:1.6">
  Recebemos um pedido para redefinir a chave de acesso da conta
  <strong>{{ .Email }}</strong> na Yachts Atlas.
</p>

<p style="font-family:Arial,sans-serif;color:#333;line-height:1.6">
  O link abaixo vale por uma hora e só pode ser usado uma vez.
</p>

<p style="margin:28px 0">
  <a href="{{ .ConfirmationURL }}"
     style="background:#c5a059;color:#010c20;font-family:Arial,sans-serif;font-weight:bold;
            text-decoration:none;padding:14px 28px;border-radius:2px;display:inline-block;
            letter-spacing:1px;text-transform:uppercase;font-size:13px">
    Definir nova chave
  </a>
</p>

<p style="font-family:Arial,sans-serif;color:#666;line-height:1.6;font-size:13px">
  Se não foi você que pediu, ignore esta mensagem — sua chave atual continua
  valendo e nada muda na sua conta.
</p>

<hr style="border:none;border-top:1px solid #e5e5e5;margin:28px 0">

<p style="font-family:Arial,sans-serif;color:#999;font-size:12px;line-height:1.6">
  Yachts Atlas — custódia digital de registros náuticos<br>
  Este e-mail foi enviado para {{ .Email }} porque existe uma conta com este
  endereço.
</p>
```

---

## 2. Confirmação de cadastro (Confirm signup)

**Subject:**

```
Confirme seu e-mail — Yachts Atlas
```

**Body:**

```html
<h2 style="font-family:Georgia,serif;color:#010c20;margin:0 0 16px">Confirme seu e-mail</h2>

<p style="font-family:Arial,sans-serif;color:#333;line-height:1.6">
  Falta um passo para sua conta na Yachts Atlas ficar ativa: confirmar que este
  endereço é seu.
</p>

<p style="margin:28px 0">
  <a href="{{ .ConfirmationURL }}"
     style="background:#c5a059;color:#010c20;font-family:Arial,sans-serif;font-weight:bold;
            text-decoration:none;padding:14px 28px;border-radius:2px;display:inline-block;
            letter-spacing:1px;text-transform:uppercase;font-size:13px">
    Confirmar e-mail
  </a>
</p>

<p style="font-family:Arial,sans-serif;color:#666;line-height:1.6;font-size:13px">
  Se você não criou conta na Yachts Atlas, ignore esta mensagem. Sem a
  confirmação, nada é ativado.
</p>

<hr style="border:none;border-top:1px solid #e5e5e5;margin:28px 0">

<p style="font-family:Arial,sans-serif;color:#999;font-size:12px;line-height:1.6">
  Yachts Atlas — custódia digital de registros náuticos
</p>
```

---

## 3. Código de acesso (Magic Link)

> **Atenção — este modelo NÃO é o do Portal do Proprietário.**
>
> O código que o armador recebe **não sai pelo Supabase**. O backend o gera com
> `generate_link({type: "magiclink"})`, tira o `email_otp` de dentro e entrega
> ele mesmo, por e-mail próprio (Hostinger) e WhatsApp — já em português, em
> `backend/app/api/v1/owner.py`. Mexer aqui não muda nada no Portal.
>
> Vale colar mesmo assim: é o que sai se alguém disparar um magic link por outro
> caminho, e e-mail em inglês saindo de uma marca brasileira é o problema que
> este arquivo existe para resolver.

**Subject:**

```
Seu acesso ao Portal do Proprietário — Yachts Atlas
```

**Body:**

```html
<h2 style="font-family:Georgia,serif;color:#010c20;margin:0 0 16px">Seu acesso ao Portal</h2>

<p style="font-family:Arial,sans-serif;color:#333;line-height:1.6">
  Use o link abaixo para entrar no Portal do Proprietário e consultar o
  histórico das suas embarcações.
</p>

<p style="margin:28px 0">
  <a href="{{ .ConfirmationURL }}"
     style="background:#c5a059;color:#010c20;font-family:Arial,sans-serif;font-weight:bold;
            text-decoration:none;padding:14px 28px;border-radius:2px;display:inline-block;
            letter-spacing:1px;text-transform:uppercase;font-size:13px">
    Entrar no Portal
  </a>
</p>

<p style="font-family:Arial,sans-serif;color:#333;line-height:1.6">
  Se preferir digitar, seu código é:
  <strong style="font-family:monospace;font-size:18px;letter-spacing:3px">{{ .Token }}</strong>
</p>

<p style="font-family:Arial,sans-serif;color:#666;line-height:1.6;font-size:13px">
  O link e o código valem por uma hora. Se não foi você que pediu, ignore esta
  mensagem — ninguém entra na sua conta sem este acesso.
</p>

<hr style="border:none;border-top:1px solid #e5e5e5;margin:28px 0">

<p style="font-family:Arial,sans-serif;color:#999;font-size:12px;line-height:1.6">
  Yachts Atlas — custódia digital de registros náuticos
</p>
```

---

## 4. Alteração de e-mail (Change Email Address)

**Subject:**

```
Confirme seu novo e-mail — Yachts Atlas
```

**Body:**

```html
<h2 style="font-family:Georgia,serif;color:#010c20;margin:0 0 16px">Confirme seu novo e-mail</h2>

<p style="font-family:Arial,sans-serif;color:#333;line-height:1.6">
  Foi pedida a troca do e-mail desta conta de <strong>{{ .Email }}</strong> para
  <strong>{{ .NewEmail }}</strong>. Para concluir, confirme que o novo endereço é seu.
</p>

<p style="margin:28px 0">
  <a href="{{ .ConfirmationURL }}"
     style="background:#c5a059;color:#010c20;font-family:Arial,sans-serif;font-weight:bold;
            text-decoration:none;padding:14px 28px;border-radius:2px;display:inline-block;
            letter-spacing:1px;text-transform:uppercase;font-size:13px">
    Confirmar novo e-mail
  </a>
</p>

<p style="font-family:Arial,sans-serif;color:#666;line-height:1.6;font-size:13px">
  Enquanto não for confirmado, o e-mail antigo continua valendo. Se não foi você,
  ignore esta mensagem e troque sua chave de acesso por precaução.
</p>

<hr style="border:none;border-top:1px solid #e5e5e5;margin:28px 0">

<p style="font-family:Arial,sans-serif;color:#999;font-size:12px;line-height:1.6">
  Yachts Atlas — custódia digital de registros náuticos
</p>
```

---

## 5. Convite (Invite user)

**Subject:**

```
Você foi convidado para a Yachts Atlas
```

**Body:**

```html
<h2 style="font-family:Georgia,serif;color:#010c20;margin:0 0 16px">Você foi convidado</h2>

<p style="font-family:Arial,sans-serif;color:#333;line-height:1.6">
  Uma conta na Yachts Atlas foi aberta para <strong>{{ .Email }}</strong>.
  Defina sua chave de acesso para começar.
</p>

<p style="margin:28px 0">
  <a href="{{ .ConfirmationURL }}"
     style="background:#c5a059;color:#010c20;font-family:Arial,sans-serif;font-weight:bold;
            text-decoration:none;padding:14px 28px;border-radius:2px;display:inline-block;
            letter-spacing:1px;text-transform:uppercase;font-size:13px">
    Definir chave de acesso
  </a>
</p>

<p style="font-family:Arial,sans-serif;color:#666;line-height:1.6;font-size:13px">
  Se você não esperava este convite, ignore esta mensagem.
</p>

<hr style="border:none;border-top:1px solid #e5e5e5;margin:28px 0">

<p style="font-family:Arial,sans-serif;color:#999;font-size:12px;line-height:1.6">
  Yachts Atlas — custódia digital de registros náuticos
</p>
```

---

## Depois de colar

Dispare um de cada, para o seu próprio e-mail, e confira três coisas:

1. **Chegou na caixa de entrada**, não no spam.
2. **O remetente** aparece como Yachts Atlas, não como `noreply@supabase.io`.
3. **O link funciona** e leva ao domínio certo.

O `verifyOtp` do Portal do Proprietário **não é testado por aqui** — ele tem
caminho próprio. Para validá-lo: Portal → entrar com o e-mail de um proprietário
cadastrado → o código chega por e-mail e WhatsApp → digitar. É a Pendência 10 do
PRD, e o único ponto do fluxo que não dá para testar sem conta de verdade.
