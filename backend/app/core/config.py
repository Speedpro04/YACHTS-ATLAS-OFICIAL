"""
Yachts Atlas — Core Configuration
"""
import json
import os
from functools import lru_cache

from pydantic_settings import BaseSettings


def _parse_allowed_origins(raw: str | None) -> list[str]:
    if not raw:
        return [
            "http://localhost:5173",
            "http://localhost:3000",
            "https://yachts.axoshub.com",
            "https://yachtsatlas.com",
            "https://www.yachtsatlas.com",
            "https://yachtsatlas.online",
            "https://www.yachtsatlas.online",
        ]

    raw = raw.strip()
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
        except json.JSONDecodeError:
            pass

    return [origin.strip() for origin in raw.split(",") if origin.strip()]


# Estados do programa fundador — 4 vagas em cada um. Fora daqui, a marina
# segue para a oferta oficial. Constante de módulo de propósito: campo lista
# em BaseSettings quebra ao ser lido do ambiente (ver ALLOWED_ORIGINS abaixo).
LAUNCH_STATES: tuple[str, ...] = ("SC", "SP", "RJ", "ES", "BA")


class Settings(BaseSettings):
    PROJECT_NAME: str = "Yachts Atlas"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    # Lido como STRING crua do ambiente (CSV ou JSON). Não usar list[str] aqui:
    # o pydantic-settings tenta json.loads em campos lista vindos de env e quebra
    # com valor separado por vírgula. A lista parseada fica em `cors_origins`.
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "")

    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    # LEGADO — não usar para assinar nada. Este valor está publicado no
    # histórico do Git (commit 15ac4be) e nunca foi rotacionado. Ficou aqui só
    # para não quebrar deploy que ainda o define; nenhum código o consome.
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")

    # Segredo do crachá do login de manutenção. Dedicado de propósito: o
    # SUPABASE_JWT_SECRET assinava isto e, vazado, permitia forjar
    # {"sub": "maintenance-admin"} e virar platform_admin sem senha.
    # Sem valor default — faltando, o login por usuário/senha desliga em vez de
    # assinar com segredo fraco. O MAINTENANCE_MASTER_TOKEN não passa por aqui.
    MAINTENANCE_JWT_SECRET: str = os.getenv("MAINTENANCE_JWT_SECRET", "")

    # Segredo da assinatura do QR de verificação do dossiê. Mesma história.
    # ATENÇÃO: trocar invalida os QR já emitidos. Versione em vez de trocar.
    VERIFICACAO_SECRET: str = os.getenv("VERIFICACAO_SECRET", "")

    # Redis — cache de velocidade. Secret só em variável de ambiente (repo público).
    # Se vazio ou indisponível, o app funciona normalmente (cache é opcional).
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    REDIS_DEFAULT_TTL: int = int(os.getenv("REDIS_DEFAULT_TTL", "3600"))

    # OpenAI — chatbot de normas (RAG). Secrets só em variável de ambiente.
    # Aceita os dois nomes de variável (OPENAI_API_KEY e o legado API_KEY_OPENAI)
    # para evitar erro de configuração no painel. Idem para o modelo (MODELO).
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY_OPENAI", "")
    OPENAI_CHAT_MODEL: str = (os.getenv("OPENAI_CHAT_MODEL") or os.getenv("MODELO") or "gpt-5-mini").lower()
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    # Chave própria da prospecção de marinas. NÃO existe para reduzir
    # alucinação — é a mesma OpenAI e o mesmo modelo; o que segura invenção é
    # prompt, contexto e guard rail de saída. Serve para (a) ver quanto a
    # prospecção custa separado do bot de normas e (b) limitar o estrago se
    # uma das duas vazar. Vazia = cai na chave principal.
    OPENAI_API_KEY_PROSPECCAO: str = (
        os.getenv("OPENAI_API_KEY_PROSPECCAO")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("API_KEY_OPENAI", "")
    )
    # Anti-abuso/sondagem: máximo de perguntas por usuário por minuto.
    CHATBOT_RATE_LIMIT_PER_MIN: int = int(os.getenv("CHATBOT_RATE_LIMIT_PER_MIN", "15"))
    # Score mínimo de similaridade para considerar que existe norma relevante.
    # Abaixo disso, o bot recusa em vez de "inventar" (anti-alucinação).
    # 0.40: calibrado para o RAG com pgvector (text-embedding-3-small). Acertos
    # válidos ficam >= 0.53; este piso corta a cauda fracamente relevante e
    # fortalece o guard rail de escopo sem barrar perguntas legítimas.
    CHATBOT_MIN_RELEVANCE: float = float(os.getenv("CHATBOT_MIN_RELEVANCE", "0.40"))

    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "yachts-docs")

    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_ID: str = os.getenv("STRIPE_PRICE_ID", "")
    MAINTENANCE_USERNAME: str = os.getenv("MAINTENANCE_USERNAME", "")
    MAINTENANCE_PASSWORD: str = os.getenv("MAINTENANCE_PASSWORD", "")
    MAINTENANCE_BYPASS_ENABLED: bool = os.getenv("MAINTENANCE_BYPASS_ENABLED", "false").lower() == "true"
    MAINTENANCE_MASTER_TOKEN: str = os.getenv("MAINTENANCE_MASTER_TOKEN", "")

    # Dossiê: quando true, o PDF só sai para ativo com pagamento concluído.
    # Mantido false — o dossiê não é mais vendido pela plataforma (vai direto
    # marina <-> dono). O dono/marina sempre acessa o próprio dossiê.
    DOSSIER_REQUIRE_PAYMENT: bool = os.getenv("DOSSIER_REQUIRE_PAYMENT", "false").lower() == "true"

    # Senha-mestra para liberação de dossiê a terceiros (broker/comprador/
    # seguradora) via link público no celular. Defina em variável de ambiente.
    DOSSIER_MASTER_PASSWORD: str = os.getenv("DOSSIER_MASTER_PASSWORD", "")

    # URL pública do site (usada em e-mails de liberação de dossiê)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://yachtsatlas.online")

    # E-mail. A caixa real fica na Hostinger, no proprio dominio: e ela que
    # autentica no SMTP e recebe as respostas. Sair de um @gmail.com para
    # caixa corporativa de marina e caminho curto para o spam — o dominio
    # proprio tem SPF e DKIM, e cobranca que cai no spam e dinheiro que nao
    # entra.
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "contato@yachtsatlas.online")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_SMTP_HOST: str = os.getenv("EMAIL_SMTP_HOST", "smtp.hostinger.com")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "465"))

    # Alias que assina as cobrancas. Entrega na mesma caixa do EMAIL_SENDER e
    # nao tem senha propria — quem faz login continua sendo a caixa real.
    # Serve para a marina reconhecer o assunto pelo remetente, e para voce
    # filtrar resposta de cobranca sem precisar de uma segunda conta.
    EMAIL_REMETENTE_COBRANCA: str = os.getenv(
        "EMAIL_REMETENTE_COBRANCA", "cobranca@yachtsatlas.online"
    )

    # Avisos operacionais para o fundador (pagamento recusado, vaga fundadora
    # paga sem vaga, resumo da cobrança, novo pedido de dossiê). Dois canais e
    # só dois — WhatsApp e e-mail. Ver notify_service.notificar_fundador.
    ALERTA_WHATSAPP: str = os.getenv("ALERTA_WHATSAPP", "")
    ALERTA_EMAIL: str = os.getenv("ALERTA_EMAIL", "")

    # Referral Program — real limit is 30 (frontend displays 14 for scarcity)
    # Modelo definitivo: marina que indica fica com 100% dos dossiês por 18 meses.
    # Após o 1º ano de operação: assinatura sobe p/ $300 e 100% do dossiê é da
    # marina permanentemente (negócio = recorrência mensal).
    REFERRAL_MAX_SLOTS: int = 30
    REFERRAL_DOSSIER_SHARE_PERCENT: int = 100  # 100% for referring marina
    REFERRAL_REWARD_MONTHS: int = 18
    REFERRAL_MIN_RETENTION_MONTHS: int = 3  # referred marina must stay 3 months

    # ------------------------------------------------------------------
    # Modelo de cobrança DEFINITIVO — UM preço, nada além disto:
    #   • US$ 140/mês        (a oferta anunciada)
    #   • R$ 697,00/mês      (a mesma assinatura cobrada em real)
    #   • travado por 12 meses a contar da assinatura de CADA marina
    #   • no 13º mês, correção por IPCA + 15% (ver REAJUSTE_*)
    #
    # ERA DOIS PREÇOS ATÉ 13/10/2026: US$ 200 para as 20 fundadoras e US$ 250
    # para as demais, com a fundadora subindo para US$ 250 no 13º mês. O
    # programa fundador CONTINUA — 4 vagas por estado, 18 meses de dossiê 100%
    # da marina —, mas a vantagem dele deixou de ser preço. Quem decidiu: o
    # fundador, e é por isso que `preco_mensal` não depende mais de qual oferta
    # a marina pegou.
    #
    # O ESPELHO NO FRONTEND é frontend/src/config/precoServico.ts (a primeira
    # dobra da home e a etapa de pagamento do cadastro). Mudou aqui, muda lá —
    # a tela não pode prometer o que a fatura não cumpre.
    PRECO_MENSAL_USD: int = 140
    PRECO_MENSAL_BRL: int = 697

    # Meses em que o valor não sobe. Contados por marina, da data da assinatura
    # dela — quem assinou em outubro vira em outubro.
    PRECO_TRAVADO_MESES: int = 12

    # A correção do 13º mês. NÃO é um valor fixo de propósito: o IPCA do
    # período só é conhecido na época, e por isso não existe degrau agendado
    # na Stripe (ver stripe_service._registrar_reajuste_do_13o_mes). O que o
    # sistema faz é guardar a regra e a data, e avisar o fundador quando chega
    # a hora de aplicar — com aviso prévio à marina, que é o combinado na
    # venda.
    REAJUSTE_INDICE: str = "ipca"
    REAJUSTE_PERCENTUAL: int = 15

    # Vagas. O teto de 20 fundadoras é CONSEQUÊNCIA das 4 por estado em 5
    # praças (SC/SP/RJ/ES/BA) — ver migration_vagas_fundadoras_por_estado.sql.
    LAUNCH_SLOTS: int = 20             # 20 fundadoras (= 5 UFs x 4)
    LAUNCH_SLOTS_PER_STATE: int = 4    # 4 fundadoras por estado (ver LAUNCH_STATES)
    TRADITIONAL_SLOTS: int = 120       # marinas além das fundadoras (teto)

    # Moeda do link em dólar. Existe porque o webhook ainda cai no VALOR quando
    # o checkout não veio de Payment Link, e comparar numero sem moeda e
    # armadilha: a conta Stripe e da Axos Hub e recebe os eventos de todos os
    # produtos da casa. Um produto qualquer a R$ 140,00/mes cairia no portao de
    # US$ 140 e seria tratado como marina.
    PRICE_CURRENCY: str = "usd"

    # Meses de dossiê 100% integral de cada oferta. Nenhum código lê estes dois
    # hoje: eles existem para o modelo de cobrança ficar escrito INTEIRO aqui,
    # ao lado dos preços, e não metade aqui e metade nos documentos — que era o
    # caso do prazo da oficial. Com o preço único, é AQUI que mora a diferença
    # entre ser fundadora e não ser. O e-mail de boas-vindas é neutro de
    # propósito e não declara oferta (ver email_service._welcome_html).
    LAUNCH_DOSSIER_BONUS_MONTHS: int = 18      # fundadora (4 por estado)
    TRADITIONAL_DOSSIER_MONTHS: int = 12       # demais marinas

    # Quantos dossiês cada ativo pode emitir por ano.
    #
    # Em variável de ambiente porque durante os ensaios o mesmo barco é usado
    # dezenas de vezes: sobe o número, testa, baixa de novo — sem deploy. O
    # padrão 4 é a regra comercial; mexer nele é exceção, não rotina.
    DOSSIE_LIMITE_ANUAL: int = int(os.getenv("DOSSIE_LIMITE_ANUAL", "4"))

    # Quanto tempo a vaga fundadora fica presa no nome da marina entre o
    # cadastro e o pagamento. Eram 60 min, suficiente enquanto o cadastro caía
    # direto no checkout; com o vídeo de apresentação no meio, quem sai para
    # pensar e volta perderia a vaga e pagaria $250 achando que pagaria $200.
    #
    # Doze horas, e não três: quem decide na marina quase nunca é quem preenche
    # o cadastro. O gerente precisa levar os $200/mês ao conselho ou ao dono de
    # verdade, e conselho que só se reúne à tarde não cabe em três horas. Meio
    # dia cobre o expediente inteiro sem prender a vaga de um dia para o outro —
    # com 4 vagas por estado, curioso segurando vaga bloqueia comprador real.
    #
    # Prazo curto NÃO protege de pagamento atrasado: o checkout do lançamento é
    # payment link da Stripe (buy.stripe.com) e vive 24h, fora do nosso alcance.
    # Quem cobre essa brecha é _avisar_pagamento_sem_vaga, que manda a decisão
    # para o humano em vez de estourar o cap do estado em silêncio.
    #
    # O prazo é dito à marina em RegistroMarina.tsx — prazo que o cliente não
    # conhece é armadilha. Mudou aqui, muda lá.
    MINUTOS_DE_RESERVA_VAGA: int = 720

    # Links de pagamento. Ficam em env para trocar de conta Stripe sem rebuild,
    # e aqui no config para não existirem dois links do mesmo preço no sistema.
    #
    # TODOS VAZIOS DESDE 13/10/2026, quando o preço virou US$ 140 / R$ 697,00.
    # Os links anteriores continuam ativos na Stripe cobrando a tabela velha
    # (R$ 1.000 e R$ 1.250), e link que cobra o preço errado é pior que link
    # que não existe: a marina lê R$ 697,00 na home, paga R$ 1.250 e tem razão
    # em pedir estorno. Vazio é a verdade, e `link_de_checkout` nunca oferece
    # caminho vazio — a tela de cadastro avisa e o cadastro fica salvo.
    #
    # PARA REABRIR A VENDA: criar na Stripe os Payment Links do preço novo
    # (US$ 140/mês e R$ 697,00/mês, recorrentes) e preencher estas quatro
    # variáveis de ambiente. Continuam sendo QUATRO, e não duas, mesmo com
    # preço único: é pelo link que o webhook sabe se a marina veio pela
    # campanha fundadora ou pelo site (ver _programa_do_checkout) — com preço
    # igual, o valor pago não diz mais de onde ela veio.
    STRIPE_LINK_MARINA_FUNDADORA: str = os.getenv("STRIPE_LINK_MARINA_FUNDADORA", "")
    STRIPE_LINK_MARINA_OFICIAL: str = os.getenv("STRIPE_LINK_MARINA_OFICIAL", "")

    # Os mesmos dois programas cobrados em real. A marina brasileira paga sem
    # IOF, sem taxa de compra internacional, e com bandeira nacional (Elo,
    # Hipercard) — que em dolar simplesmente nao passa. O preco anunciado nas
    # paginas continua sendo o dolar; o real e forma de pagamento, nao oferta.
    STRIPE_LINK_MARINA_FUNDADORA_BRL: str = os.getenv("STRIPE_LINK_MARINA_FUNDADORA_BRL", "")
    STRIPE_LINK_MARINA_OFICIAL_BRL: str = os.getenv("STRIPE_LINK_MARINA_OFICIAL_BRL", "")

    # Cambio implicito no preco em real: 697 / 140 = 4,98. Congela junto com o
    # preco (PRECO_TRAVADO_MESES), entao nao acompanha o dolar no meio do ano.
    # R$ 697 e ponto de preco, nao conta de cambio: "multiplica por 5" daria 700
    # redondo, e numero terminado em 7 vende melhor. Acima de 5,48 a defasagem
    # passa de 10% e vale rever o valor em real — ninguem avisa, tem que olhar.
    BRL_TAXA_TRAVADA: float = 4.98
    BRL_TAXA_REVISAR_ACIMA_DE: float = 5.48

    # Inadimplência: 20 dias após a primeira cobrança recusada o acesso é
    # cortado. Pagou, volta sozinho — ver app/core/acesso.py.
    DIAS_ATE_CORTE_INADIMPLENCIA: int = 20

    # WhatsApp. O provedor é trocável (Evolution hoje; Z-API ou a Cloud API da
    # Meta depois) — quem envia não é escolhido pelo código que pede o envio.
    # Vazio = canal desligado: o aviso sai só por e-mail, sem quebrar nada.
    WHATSAPP_PROVIDER: str = os.getenv("WHATSAPP_PROVIDER", "")
    EVOLUTION_BASE_URL: str = os.getenv("EVOLUTION_BASE_URL", "")
    EVOLUTION_API_KEY: str = os.getenv("EVOLUTION_API_KEY", "")
    EVOLUTION_INSTANCE: str = os.getenv("EVOLUTION_INSTANCE", "")
    # Chave GLOBAL do servidor Evolution. O nome e o mesmo que a propria
    # Evolution usa no container dela, de proposito: dois apelidos para a mesma
    # coisa no painel foi o que gerou EVOLUTION_API_KEY duplicada e derrubou o
    # envio do codigo de acesso em 22/08/2026.
    #
    # NAO e a primeira escolha para enviar. O caminho normal e o token DA
    # INSTANCIA (EVOLUTION_API_KEY / _PROSPECCAO), que so alcanca a propria
    # instancia — se vazar, o outro numero continua fora de alcance. A global
    # entra so quando o token da instancia nao estiver definido.
    #
    # Cair na global e seguro porque a chave nao escolhe o destino: quem
    # escolhe e a INSTANCIA, e essa nunca tem fallback.
    AUTHENTICATION_API_KEY: str = os.getenv("AUTHENTICATION_API_KEY", "")
    # Instância SEPARADA, com outro número, só para prospecção ativa (indicações
    # de marina abordadas via Evolution). Não é preciosismo: o número de cima
    # entrega código de login e régua de cobrança, e disparo de prospecção é o
    # que atrai denúncia de spam. Banido o número da prospecção, perde-se uma
    # linha de vendas; banido o transacional, cai login e cobrança junto.
    # Vazio = prospecção desligada (NÃO cai no transacional, de propósito).
    EVOLUTION_INSTANCE_PROSPECCAO: str = os.getenv("EVOLUTION_INSTANCE_PROSPECCAO", "")
    # Token DA INSTÂNCIA de prospecção. Preferível à chave global: um token de
    # instância só alcança a própria instância, então se ele vazar a
    # transacional (código de login, cobrança) continua fora de alcance.
    #
    # Vazio cai na AUTHENTICATION_API_KEY (global), que alcança qualquer
    # instância. NÃO cai na EVOLUTION_API_KEY: aquela é o token da instância
    # transacional e daria 401 aqui.
    EVOLUTION_API_KEY_PROSPECCAO: str = (
        os.getenv("EVOLUTION_API_KEY_PROSPECCAO")
        or os.getenv("AUTHENTICATION_API_KEY", "")
    )
    # Segredo do webhook que recebe as respostas do WhatsApp. O endpoint é
    # público por necessidade (a Evolution chama de fora), e o que ele faz é
    # escrever na blocklist. Sem segredo, qualquer um na internet bloqueia
    # qualquer número. Vazio = webhook DESLIGADO, não aberto: preferir não
    # receber opt-out a aceitar de quem for.
    WHATSAPP_WEBHOOK_TOKEN: str = os.getenv("WHATSAPP_WEBHOOK_TOKEN", "")

    # DDI usado quando a marina digita o telefone sem ele. As 20 fundadoras são
    # todas brasileiras (SC/SP/RJ/ES/BA); as versões LATAM/USA/EURO rodam em
    # instalações separadas, com o DDI delas.
    # ── Prospecção automática ──────────────────────────────────────────
    # Desligada por padrão, e isso é decisão de desenho, não excesso de
    # cautela: esta é a única rotina do sistema que fala com uma pessoa que
    # NUNCA pediu contato. Um deploy não pode começar a abordar gente sozinho
    # — quem liga é o fundador, e desligar tem de ser imediato, sem esperar
    # build. Por isso vive em variável de ambiente, não em código.
    PROSPECCAO_AUTOMATICA: bool = os.getenv("PROSPECCAO_AUTOMATICA", "").lower() in ("1", "true", "sim")

    # Carência entre a indicação e a mensagem. Não é atraso técnico: é a
    # JANELA DE CANCELAMENTO. Lead errado que entrar (número inválido, teste,
    # marina que não devia ser abordada) pode ser tirado da fila antes de
    # virar mensagem — e mensagem enviada não volta.
    PROSPECCAO_CARENCIA_MINUTOS: int = int(os.getenv("PROSPECCAO_CARENCIA_MINUTOS", "30"))

    # De quanto em quanto tempo a agenda olha a fila.
    PROSPECCAO_INTERVALO_SEGUNDOS: int = int(os.getenv("PROSPECCAO_INTERVALO_SEGUNDOS", "180"))

    # Teto do recuo quando a fila volta vazia. A agenda dobra a espera a cada
    # volta sem trabalho, ate este limite, e volta ao intervalo normal assim
    # que aparece um lead. Sem isso, uma fila vazia custava uma consulta ao
    # Supabase a cada 60s -- cerca de 1.400 por dia para nao achar nada.
    #
    # Nao atrasa ninguem de forma relevante: o lead so fica elegivel depois da
    # carencia, e o pior caso e carencia + este teto.
    PROSPECCAO_INTERVALO_OCIOSO_SEGUNDOS: int = int(
        os.getenv("PROSPECCAO_INTERVALO_OCIOSO_SEGUNDOS", "600"))

    DDI_PADRAO: str = os.getenv("DDI_PADRAO", "55")

    @property
    def cors_origins(self) -> list[str]:
        """Lista de origens permitidas (parseia o ALLOWED_ORIGINS — CSV ou JSON)."""
        return _parse_allowed_origins(self.ALLOWED_ORIGINS or None)

    class Config:
        # Caminho absoluto (backend/.env) — independe do diretório de trabalho
        # do processo que sobe o uvicorn (ex.: rodar a partir da raiz do repo).
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
