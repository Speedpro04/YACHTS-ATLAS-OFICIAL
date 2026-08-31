"""
Yachts Atlas — Dado pessoal: o que não se guarda não vaza.

Fonte ÚNICA do mascaramento de documento. Antes a função vivia dentro de
`dossie_data` como privada, e o mascaramento acontecia só na SAÍDA — o CPF
completo era gravado no banco e escondido na hora de imprimir. Em 31/08/2026
o fundador decidiu o contrário: mascarar na ENTRADA, e nunca guardar o
documento inteiro.

POR QUE NÃO GUARDAR
-------------------
Levantado em 31/08/2026: o documento completo era gravado e **nunca usado**.
Entra pelo formulário do painel (campo opcional), e o único lugar que o
consome — o dossiê — já o imprime mascarado. Não há validação, busca,
cobrança nem verificação de identidade que precise dos dígitos escondidos.

Guardar dado pessoal sem uso é assumir risco de vazamento sem contrapartida.
É o princípio da minimização (LGPD, art. 6º, III), e é o argumento mais
simples de sustentar numa auditoria: não protegemos o dado — nós não o
temos.

O QUE FICA
----------
O suficiente para IDENTIFICAR o titular ao lado do nome dele, que é para o
que o documento serve no dossiê:

    CPF   123.456.789-00        ->  ***.456.789-**
    CNPJ  12.345.678/0001-90    ->  12.345.678/****-**

No CNPJ a raiz é preservada de propósito: são os oito primeiros dígitos que
identificam a empresa; a ordem do estabelecimento e o verificador não
acrescentam identificação e só aumentam o estrago se vazarem.

SE UM DIA PRECISAR DO COMPLETO
------------------------------
Não dá para "desmascarar" — o dado terá sido descartado na entrada, e é essa
a intenção. Precisar do documento inteiro (contrato, cobrança, verificação)
significa coletá-lo no momento em que for usado, com base legal própria, e
guardá-lo cifrado (`pgcrypto`, já instalado). Não significa voltar a gravar
por precaução.
"""
from typing import Optional


def mascarar_documento(doc: Optional[str]) -> Optional[str]:
    """CPF/CNPJ com o miolo escondido, preservando o que identifica.

    Idempotente: aplicar duas vezes não estraga o valor — um documento já
    mascarado não tem os 11 ou 14 dígitos e cai no caminho genérico, que
    preserva os quatro últimos. Isso importa porque a mesma função roda na
    gravação e no backfill.

    Devolve None para entrada vazia ou curta demais para identificar alguém.
    """
    if not doc:
        return None

    texto = str(doc).strip()
    # Já mascarado: devolve como está, em vez de mascarar o mascarado.
    if "*" in texto:
        return texto

    digitos = "".join(c for c in texto if c.isdigit())

    if len(digitos) == 11:   # CPF
        return f"***.{digitos[3:6]}.{digitos[6:9]}-**"
    if len(digitos) == 14:   # CNPJ — a raiz identifica a empresa, o resto não
        return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/****-**"
    if len(digitos) > 4:
        return f"{'*' * (len(digitos) - 4)}{digitos[-4:]}"

    # Menos de 5 dígitos não identifica ninguém e provavelmente é digitação
    # incompleta. Guardar um fragmento não serve para nada e ainda é dado
    # pessoal: descarta.
    return None
