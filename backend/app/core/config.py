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

    # Email Configuration for Alerts
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "yachtsatlas@gmail.com")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_SMTP_HOST: str = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "465"))

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
    TRADITIONAL_SLOTS: int = 120       # marinas restantes a $250 (teto)
    TRADITIONAL_PRICE_MONTHLY: int = 250
    LAUNCH_DOSSIER_BONUS_MONTHS: int = 18

    # O preço de fundadora vale 12 meses. No 13º a assinatura passa a $250 —
    # correção monetária combinada na venda, não é surpresa para a marina.
    # Quem executa é a própria Stripe (subscription schedule anexado no
    # pagamento), então não depende de rotina nossa rodando um ano depois.
    LAUNCH_PRICE_MONTHS: int = 12

    # Links de pagamento. Ficam em env para trocar de conta Stripe sem rebuild,
    # e aqui no config para não existirem dois links do mesmo preço no sistema.
    STRIPE_LINK_MARINA_FUNDADORA: str = os.getenv(
        "STRIPE_LINK_MARINA_FUNDADORA",
        "https://buy.stripe.com/28EeVdb9jf6c8cx7QA1wY00",
    )
    STRIPE_LINK_MARINA_OFICIAL: str = os.getenv(
        "STRIPE_LINK_MARINA_OFICIAL",
        "https://buy.stripe.com/7sY7sL4KVbU02Sd7QA1wY01",
    )

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
    # DDI usado quando a marina digita o telefone sem ele. As 20 fundadoras são
    # todas brasileiras (SC/SP/RJ/ES/BA); as versões LATAM/USA/EURO rodam em
    # instalações separadas, com o DDI delas.
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
