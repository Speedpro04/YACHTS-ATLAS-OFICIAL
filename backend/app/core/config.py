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

    # Modelo de cobrança DEFINITIVO — só dois preços, nada além disto:
    #   • 20 marinas de lançamento   → $200/mês  (link de pagamento de $200)
    #   • até 120 marinas restantes  → $250/mês  (link de pagamento de $250)
    # Total: 140 marinas. Sem outros valores.
    LAUNCH_SLOTS: int = 20             # marinas de lançamento a $200 (= 5 UFs x 4)
    LAUNCH_SLOTS_PER_STATE: int = 4    # 4 fundadoras por estado (ver LAUNCH_STATES)
    LAUNCH_PRICE_MONTHLY: int = 200    # preço das 20 de lançamento
    # Moeda dos dois links de marina. Existe porque o webhook reconhece a
    # fundadora PELO VALOR, e comparar numero sem moeda e armadilha: a conta
    # Stripe e da Axos Hub e recebe os eventos de todos os produtos da casa.
    # Um produto qualquer a R$ 200,00/mes — preco comum — cairia no portao de
    # US$ 200 e seria tratado como marina fundadora.
    PRICE_CURRENCY: str = "usd"
    TRADITIONAL_SLOTS: int = 120       # marinas restantes a $250 (teto)
    TRADITIONAL_PRICE_MONTHLY: int = 250

    # Os mesmos precos cobrados em real, travados em 5,00 (ver BRL_TAXA_TRAVADA).
    # Numero redondo de proposito: "multiplica por 5" e conta que o gerente faz
    # de cabeca, e clareza numa venda de 20 vagas vale mais que 3% de cambio.
    LAUNCH_PRICE_MONTHLY_BRL: int = 1000
    TRADITIONAL_PRICE_MONTHLY_BRL: int = 1250

    # Meses de dossiê 100% integral de cada oferta. Nenhum código lê estes dois
    # hoje: eles existem para o modelo de cobrança ficar escrito INTEIRO aqui,
    # ao lado dos preços, e não metade aqui e metade nos documentos — que era o
    # caso do prazo da oficial. O e-mail de boas-vindas é neutro de propósito e
    # não declara oferta (ver email_service._welcome_html).
    LAUNCH_DOSSIER_BONUS_MONTHS: int = 18      # fundadora ($200)
    TRADITIONAL_DOSSIER_MONTHS: int = 12       # oficial ($250)

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
    # Três horas, e não um dia: com 4 vagas por estado, curioso segurando vaga
    # bloqueia comprador real. O prazo é dito à marina no cadastro — prazo que
    # o cliente não conhece é armadilha.
    MINUTOS_DE_RESERVA_VAGA: int = 180

    # O preço de fundadora vale 12 meses. No 13º a assinatura passa a $250 —
    # correção monetária combinada na venda, não é surpresa para a marina.
    # Quem executa é a própria Stripe (subscription schedule anexado no
    # pagamento), então não depende de rotina nossa rodando um ano depois.
    LAUNCH_PRICE_MONTHS: int = 12

    # Links de pagamento. Ficam em env para trocar de conta Stripe sem rebuild,
    # e aqui no config para não existirem dois links do mesmo preço no sistema.
    # DESATIVADOS no painel em 26/08/2026, quando os precos em real entraram.
    # As URLs continuam existindo e respondem "The link is no longer active" —
    # pior que nao existir, porque parecem funcionar. Vazio e a verdade, e
    # link_de_checkout nunca oferece caminho vazio. Recriar aqui quando houver
    # venda fora do Brasil.
    STRIPE_LINK_MARINA_FUNDADORA: str = os.getenv("STRIPE_LINK_MARINA_FUNDADORA", "")
    STRIPE_LINK_MARINA_OFICIAL: str = os.getenv("STRIPE_LINK_MARINA_OFICIAL", "")

    # Os mesmos dois programas cobrados em real. A marina brasileira paga sem
    # IOF, sem taxa de compra internacional, e com bandeira nacional (Elo,
    # Hipercard) — que em dolar simplesmente nao passa. O preco anunciado nas
    # paginas continua sendo o dolar; o real e forma de pagamento, nao oferta.
    #
    # Vazio enquanto o link nao existir: link vazio nao identifica programa
    # nenhum (ver _programa_do_checkout), entao a ausencia e inofensiva.
    STRIPE_LINK_MARINA_FUNDADORA_BRL: str = os.getenv(
        "STRIPE_LINK_MARINA_FUNDADORA_BRL",
        "https://buy.stripe.com/8x2bJ10uFe281O9eeY1wY0b",   # R$ 1.000/mes
    )
    STRIPE_LINK_MARINA_OFICIAL_BRL: str = os.getenv(
        "STRIPE_LINK_MARINA_OFICIAL_BRL",
        "https://buy.stripe.com/fZu9ATcdn0bi2Sd5Is1wY0c",   # R$ 1.250/mes
    )

    # Cambio travado no link em real. Congela por 12 meses (o prazo do preco de
    # fundadora), entao nao acompanha o dolar. Acima de 5,50 a defasagem passa
    # de 10% e vale criar preco novo — ninguem avisa, tem que olhar.
    BRL_TAXA_TRAVADA: float = 5.00
    BRL_TAXA_REVISAR_ACIMA_DE: float = 5.50

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
