"""
Yachts Atlas — Stripe Payment Service
Complete payment processing with Stripe
"""
import calendar
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum

import stripe
from app.core.config import settings


logger = logging.getLogger(__name__)


class PlanType(str, Enum):
    """Subscription plan types"""
    FREE = "free"
    MARINA = "marina"  # B2B - Marinas
    ENTERPRISE = "enterprise"  # B2B - Grandes redes


class StripeService:
    """Premium Stripe service for payment processing.

    A plataforma cobra UMA coisa: a assinatura mensal da Marina. O dossie e
    pago pelo dono do barco direto a Marina, e 100% dessa receita e dela —
    nao passa por aqui, nao e dividido, e nao existe repasse a calcular.
    """
    
    # Pricing configuration (in USD) - B2B2C Model
    # Marinas pay monthly, resell to asset owners
    PRICING = {
        PlanType.FREE: {
            "monthly": 0,
            "name": "Free Tier",
            "features": ["1 asset", "Basic tracking", "Community support"]
        },
        PlanType.MARINA: {
            # UM preco para toda marina, fundadora ou nao (ver
            # config.PRECO_MENSAL_USD). O que distingue a fundadora sao os 18
            # meses de dossie 100% dela, nao o valor da assinatura.
            "monthly": settings.PRECO_MENSAL_USD,
            "name": "Marina Standard",
            "features": ["Unlimited assets", "Fleet management", "Priority support", "API access", "Real-time monitoring", "Audit reports", "White-label ready"]
        },
        PlanType.ENTERPRISE: {
            "monthly": 500,
            "name": "Enterprise",
            "features": ["Unlimited assets", "Multi-location management", "24/7 dedicated support", "White-label", "Full API access", "Custom integrations", "SLA guarantee"]
        }
    }
    
    def __init__(self):
        if not settings.STRIPE_SECRET_KEY:
            logger.warning("Stripe secret key not configured")
        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            logger.info("StripeService initialized")
    
    def create_checkout_session(
        self,
        user_id: str,
        plan_type: PlanType,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create Stripe checkout session for subscription
        """
        try:
            plan_config = self.PRICING[plan_type]
            
            # Create or get price
            price_id = self._get_or_create_price(
                amount=plan_config["monthly"] * 100,  # Convert to cents
                currency="usd",
                recurring=True,
                product_name=plan_config["name"]
            )
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=metadata.get('email') if metadata else None,
                metadata={
                    'user_id': user_id,
                    'plan_type': plan_type.value,
                    **(metadata or {})
                },
                subscription_data={
                    'metadata': {
                        'user_id': user_id,
                        'plan_type': plan_type.value
                    }
                }
            )
            
            logger.info(f"Created checkout session {session.id} for user {user_id}, plan {plan_type.value}")
            
            return {
                "session_id": session.id,
                "url": session.url,
                "plan_type": plan_type.value,
                "amount": plan_config["monthly"]
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {str(e)}")
            raise Exception(f"Failed to create checkout session: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            raise Exception(f"Failed to create checkout session: {str(e)}")
    
    def create_onboarding_checkout(
        self,
        email: str,
        marina_id: str,
        success_url: str,
        cancel_url: str,
        plan_type: PlanType = PlanType.MARINA
    ) -> Dict[str, Any]:
        """
        Create Stripe checkout session for marina onboarding
        """
        try:
            plan_config = self.PRICING[plan_type]
            
            # Create or get price
            price_id = self._get_or_create_price(
                amount=plan_config["monthly"] * 100,  # Convert to cents
                currency="usd",
                recurring=True,
                product_name=plan_config["name"]
            )
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=email,
                metadata={
                    'marina_id': marina_id,
                    'plan_type': plan_type.value,
                    'is_onboarding': 'true'
                },
                subscription_data={
                    'metadata': {
                        'marina_id': marina_id,
                        'plan_type': plan_type.value
                    }
                }
            )
            
            logger.info(f"Created onboarding checkout session {session.id} for marina {marina_id}")
            
            return {
                "session_id": session.id,
                "url": session.url,
                "amount": plan_config["monthly"]
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise Exception(f"Failed to create checkout session: {str(e)}")
    @staticmethod
    def _lookup_key(amount: int, currency: str, recurring: bool) -> str:
        """Chave estavel do preco — e por ela que reencontramos o price ja criado."""
        return f"ya_{'rec' if recurring else 'once'}_{currency.lower()}_{amount}"

    def _get_or_create_price(
        self,
        amount: int,
        currency: str,
        recurring: bool,
        product_name: str
    ) -> str:
        """
        Reaproveita o price existente ou cria um novo.

        A busca e por lookup_key porque `Price.list` NAO aceita filtro de valor:
        mandar `amount=` devolve 400 "Received unknown parameter: amount" e
        derrubava todo checkout criado pela API. O lookup_key e unico na conta,
        entao tambem impede criar um produto novo a cada chamada.
        """
        lookup_key = self._lookup_key(amount, currency, recurring)
        try:
            existentes = stripe.Price.list(lookup_keys=[lookup_key], active=True, limit=1)
            if existentes.data:
                return existentes.data[0].id

            # Create new product
            product = stripe.Product.create(
                name=product_name,
                description=f"{product_name} - Yachts Atlas"
            )
            
            # Create new price
            price_data = {
                'product': product.id,
                'unit_amount': amount,
                'currency': currency,
                'lookup_key': lookup_key,
            }
            
            if recurring:
                price_data['recurring'] = {
                    'interval': 'month',
                    'interval_count': 1
                }
            
            price = stripe.Price.create(**price_data)
            
            logger.info(f"Created new price {price.id} ({lookup_key}) for {product_name}")
            return price.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating price: {str(e)}")
            raise Exception(f"Failed to create price: {str(e)}")
    
    @staticmethod
    def _avisar_pagamento_sem_vaga(email: Optional[str], motivo: Optional[str], checkout_id: str) -> None:
        """Alguém assinou pela campanha fundadora sem ter vaga — decisão é humana.

        Com o preço único o dinheiro está certo: ela pagou o mesmo que todas as
        outras. O que está em aberto é o BÔNUS — os 18 meses de dossiê 100% da
        fundadora, que existem para 4 marinas por estado e nada mais. Honrar
        uma quinta é tirar de quem ainda vai entrar; não honrar sem avisar é
        vender uma coisa e entregar outra. Por isso vai para o humano.
        """
        try:
            from app.services.notify_service import notificar_fundador
            notificar_fundador(
                "Assinou como fundadora sem vaga no estado",
                f"{email or 'sem e-mail'} — motivo: {motivo or 'desconhecido'}.\n"
                f"Checkout {checkout_id}.\n"
                f"A assinatura está ativa a US$ {settings.PRECO_MENSAL_USD}/mês — "
                f"o preço está correto, é o mesmo de todas.\n"
                f"Em aberto: os {settings.LAUNCH_DOSSIER_BONUS_MONTHS} meses de "
                f"dossiê 100% da fundadora. Decida: honrar o bônus como "
                f"exceção, manter os {settings.TRADITIONAL_DOSSIER_MONTHS} meses "
                f"padrão (e avisar a marina) ou reembolsar.",
            )
        except Exception as e:
            logger.error(f"Falha ao avisar sobre pagamento sem vaga ({checkout_id}): {e}")

    # ------------------------------------------------------------------
    # O REAJUSTE DO 13º MÊS
    #
    # Até 13/10/2026 isto era um DEGRAU FIXO agendado na Stripe: 12 meses no
    # preço de fundadora e, no 13º, o preço oficial (US$ 250 / R$ 1.250). Dava
    # para agendar porque o valor da segunda fase já era conhecido no dia da
    # venda.
    #
    # O preço agora é um só — US$ 140 / R$ 697,00 — e a correção do 13º mês é
    # IPCA + 15%, um número que NÃO EXISTE no dia da venda. Não há o que
    # agendar: cronograma com valor inventado cobraria o errado com a
    # autoridade de um automatismo, e um degrau de US$ 140 para US$ 140 só
    # serviria para fingir que a regra está implementada.
    #
    # O que o sistema faz é guardar a REGRA e a DATA junto da marina — no
    # metadata do acesso dela e, quando é fundadora, na linha dela em
    # `marinas_fundadoras` — e avisar o fundador. Aplicar o reajuste é ato
    # comercial: tem aviso prévio à marina antes de entrar na fatura, e é
    # exatamente o tipo de coisa que ninguém quer que aconteça sozinha de
    # madrugada.
    @staticmethod
    def _preco_na_moeda(moeda: Optional[str]) -> tuple[int, str]:
        """(valor cheio, moeda) da assinatura nesta moeda — para o texto do aviso.

        Moeda desconhecida levanta em vez de cair no dólar: dizer "R$ 697,00"
        para quem paga em euro é o mesmo defeito que o código antigo tinha ao
        contrário, quando prometia US$ 250 a quem assinava em real.
        """
        m = (moeda or "").strip().lower()
        if m == "brl":
            return settings.PRECO_MENSAL_BRL, "brl"
        if m == "usd":
            return settings.PRECO_MENSAL_USD, "usd"
        raise ValueError(f"sem preço definido para a moeda '{moeda}'")

    @classmethod
    def _rotulo_do_reajuste(cls, moeda: Optional[str]) -> str:
        """A regra em uma linha, na moeda que a Marina paga."""
        indice = settings.REAJUSTE_INDICE.upper()
        regra = f"{indice} + {settings.REAJUSTE_PERCENTUAL}%"
        try:
            valor, m = cls._preco_na_moeda(moeda)
        except ValueError:
            return regra
        simbolo = "R$" if m == "brl" else "US$"
        return f"{simbolo} {valor:,}".replace(",", ".") + f" corrigido por {regra}"

    @staticmethod
    def _mais_meses(quando: datetime, meses: int) -> datetime:
        """Mesma data, `meses` meses depois.

        Dia 31 em mês de 30 não existe: cai no último dia do mês, que é como
        a própria Stripe trata o aniversário da assinatura.
        """
        total = quando.month - 1 + meses
        ano = quando.year + total // 12
        mes = total % 12 + 1
        return quando.replace(
            year=ano, month=mes, day=min(quando.day, calendar.monthrange(ano, mes)[1])
        )

    def _registrar_reajuste_do_13o_mes(
        self,
        subscription_id: str,
        usuario_id: Optional[str] = None,
        email: Optional[str] = None,
    ) -> None:
        """
        Grava QUANDO e COMO esta assinatura será corrigida — e avisa o fundador.

        A data é a de CADA marina, contada da assinatura dela: quem assinou em
        outubro vence em outubro, quem assinou em dezembro vence em dezembro.
        Guardada junto do acesso (user_metadata) para a régua existir para toda
        marina, e não só para as fundadoras — o preço travado por 12 meses vale
        para todas desde que o preço passou a ser um só.

        Best-effort, como todo o resto do webhook: o pagamento já aconteceu, e
        falhar aqui não pode derrubar o evento. Se falhar, o fundador é avisado
        para anotar na mão — o preço do esquecimento é um ano inteiro de
        assinatura sem correção.
        """
        moeda = None
        try:
            assinatura = stripe.Subscription.retrieve(subscription_id)

            def _campo(nome):
                if isinstance(assinatura, dict):
                    return assinatura.get(nome)
                return getattr(assinatura, nome, None)

            moeda = _campo("currency")

            # `start_date` é quando a assinatura começou — é dela que o
            # aniversário nasce. `created` e `current_period_start` servem de
            # rede; sem nenhum, hoje é a melhor aproximação que existe, e o log
            # diz que foi aproximação.
            inicio_ts = _campo("start_date") or _campo("created") or _campo("current_period_start")
            if inicio_ts:
                inicio = datetime.fromtimestamp(int(inicio_ts), tz=timezone.utc)
            else:
                inicio = datetime.now(timezone.utc)
                logger.warning(
                    f"Assinatura {subscription_id} sem data de início na Stripe — "
                    "o vencimento do preço travado foi contado de hoje"
                )

            vence_em = self._mais_meses(inicio, settings.PRECO_TRAVADO_MESES)

            regra = {
                "preco_travado_ate": vence_em.isoformat(),
                "reajuste_indice": settings.REAJUSTE_INDICE,
                "reajuste_percentual": settings.REAJUSTE_PERCENTUAL,
            }

            if usuario_id:
                self._atualizar_metadata(usuario_id, dict(regra))

            # A fundadora tem linha própria, e é lá que o comercial olha quando
            # vai montar a carta de reajuste. `email` é a chave da tabela.
            if email:
                try:
                    from app.core.supabase import get_supabase_admin
                    get_supabase_admin().table("marinas_fundadoras").update({
                        **regra,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }).eq("email", email.strip().lower()).execute()
                except Exception as e:
                    # Não é fundadora, ou a linha ainda não existe: a régua do
                    # metadata já está gravada, que é o que o sistema lê.
                    logger.info(
                        f"Reajuste não gravado em marinas_fundadoras para {email}: {e}"
                    )

            logger.info(
                f"Reajuste registrado para {subscription_id}: "
                f"{settings.PRECO_TRAVADO_MESES} meses travados até "
                f"{vence_em.date().isoformat()}, depois "
                f"{self._rotulo_do_reajuste(moeda)}"
            )
        except Exception as e:
            logger.error(f"Falha ao registrar o reajuste de {subscription_id}: {e}")
            try:
                from app.services.notify_service import notificar_fundador
                notificar_fundador(
                    "Reajuste do 13º mês não registrado",
                    f"Assinatura {subscription_id} ficou sem a data de "
                    f"vencimento do preço travado ({self._rotulo_do_reajuste(moeda)}).\n"
                    "Anote na mão: sem isso, ninguém lembra de corrigir e ela "
                    "fica um ano a mais no preço de entrada.",
                )
            except Exception:
                pass
    def verify_webhook_signature(
        self,
        payload: bytes,
        sig_header: str
    ) -> stripe.Event:
        """
        Verify Stripe webhook signature
        """
        try:
            if not settings.STRIPE_WEBHOOK_SECRET:
                logger.warning("Stripe webhook secret not configured")
                raise Exception("Webhook secret not configured")
            
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
            
            logger.info(f"Verified webhook event: {event.type}")
            return event
            
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            raise Exception("Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            raise Exception("Invalid signature")
    
    def handle_webhook_event(self, event: stripe.Event) -> Dict[str, Any]:
        """
        Handle Stripe webhook events
        """
        try:
            event_type = event.type
            data = event.data.object
            
            logger.info(f"Handling webhook event: {event_type}")
            
            if event_type == 'checkout.session.completed':
                return self._handle_checkout_completed(data)
            elif event_type == 'customer.subscription.created':
                return self._handle_subscription_created(data)
            elif event_type == 'customer.subscription.updated':
                return self._handle_subscription_updated(data)
            elif event_type == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(data)
            elif event_type == 'invoice.paid':
                return self._handle_invoice_paid(data)
            elif event_type == 'invoice.payment_failed':
                return self._handle_invoice_payment_failed(data)
            else:
                logger.info(f"Unhandled event type: {event_type}")
                return {"status": "ignored", "event_type": event_type}
                
        except Exception as e:
            logger.error(f"Error handling webhook event: {str(e)}")
            raise Exception(f"Failed to handle webhook event: {str(e)}")
    
    @staticmethod
    def _e_duplicata(erro: Exception) -> bool:
        """
        Colisao de chave unica no Postgres (SQLSTATE 23505).

        O postgrest devolve o codigo tanto num atributo `code` quanto no texto
        do erro, dependendo da versao do cliente — por isso olhamos os dois.
        """
        if getattr(erro, "code", None) == "23505":
            return True
        texto = str(erro).lower()
        return "23505" in texto or "duplicate key" in texto

    @staticmethod
    def _email_do_checkout(session: stripe.checkout.Session, metadata: Optional[Dict[str, Any]]) -> Optional[str]:
        """E-mail do cliente, venha ele de onde vier no checkout."""
        detalhes = getattr(session, "customer_details", None)
        email = None
        if detalhes:
            email = detalhes.get("email") if isinstance(detalhes, dict) else getattr(detalhes, "email", None)
        return email or (metadata or {}).get("email") or getattr(session, "customer_email", None)

    @staticmethod
    def _nome_da_marina(
        user_id: Optional[str],
        metadata: Optional[Dict[str, Any]],
        session: stripe.checkout.Session,
    ) -> Optional[str]:
        """
        O nome que vai no e-mail de boas-vindas, do mais confiavel ao menos.

        1. O CADASTRO — onde a marina digitou o proprio nome. E o unico que
           vale por cliente, e por isso vem primeiro.
        2. O metadata do link, se houver. Payment Link e URL fixa: o metadata
           dele e o MESMO para todo mundo que paga por ali. Serve de rede,
           nunca de primeira escolha.
        3. O titular do checkout. Pode ser a pessoa em vez da marina, mas e
           melhor que um "Ola" pelado.

        So o item 2 era consultado, e ele vem vazio nos Payment Links — por
        isso o primeiro e-mail depois de US$ 250 chegava sem o nome de quem
        acabou de pagar. O dado nunca faltou; faltava olhar onde ele estava.
        """
        if user_id:
            try:
                from app.core.supabase import get_supabase_admin
                atual = get_supabase_admin().auth.admin.get_user_by_id(user_id)
                usuario = getattr(atual, "user", None) or atual
                meta = getattr(usuario, "user_metadata", None) or {}
                do_cadastro = meta.get("marina") or meta.get("nome")
                if do_cadastro and str(do_cadastro).strip():
                    return str(do_cadastro).strip()
            except Exception as e:
                logger.error(f"Falha ao ler o nome da marina {user_id}: {e}")

        do_link = (metadata or {}).get("marina_nome") or (metadata or {}).get("nome")
        if do_link and str(do_link).strip():
            return str(do_link).strip()

        detalhes = getattr(session, "customer_details", None)
        if detalhes:
            do_checkout = (detalhes.get("name") if isinstance(detalhes, dict)
                           else getattr(detalhes, "name", None))
            if do_checkout and str(do_checkout).strip():
                return str(do_checkout).strip()
        return None

    @staticmethod
    def _atualizar_metadata(
        user_id: str,
        mudancas: Dict[str, Any],
        preservar: tuple = (),
    ) -> None:
        """
        Escreve chaves no user_metadata sem perder o que ja estava la.

        O update do Auth TROCA o objeto inteiro — gravar so a chave nova
        apagaria nome, telefone e marina. Por isso le antes e mescla.

        Valor None apaga a chave. Chave listada em `preservar` so e escrita se
        ainda nao existir: e assim que `inadimplente_desde` guarda a data da
        PRIMEIRA cobranca recusada, e nao a da ultima — o Stripe tenta varias
        vezes, e a cada tentativa o prazo de 20 dias voltaria para o zero.
        """
        try:
            from app.core.supabase import get_supabase_admin
            admin = get_supabase_admin().auth.admin
            atual = admin.get_user_by_id(user_id)
            usuario = getattr(atual, "user", None) or atual
            meta = dict(getattr(usuario, "user_metadata", None) or {})
            for chave, valor in mudancas.items():
                if chave in preservar and meta.get(chave):
                    continue
                if valor is None:
                    meta.pop(chave, None)
                else:
                    meta[chave] = valor
            admin.update_user_by_id(user_id, {"user_metadata": meta})
        except Exception as e:
            logger.error(f"Falha ao atualizar acesso do usuario {user_id}: {e}")

    @classmethod
    def _marcar_pagamento_confirmado(cls, user_id: str) -> None:
        """
        Libera o acesso: 'pendente' vira 'pago' e a inadimplencia e zerada.

        A conta nasce pendente no cadastro (leads._criar_acesso_marina_paga).
        Limpar `inadimplente_desde` aqui e o que faz o religamento ser
        automatico — a marina que estava cortada volta a usar o sistema na
        requisicao seguinte ao pagamento, sem ninguem mexer em nada.
        """
        cls._atualizar_metadata(user_id, {
            "pagamento": "pago",
            "inadimplente_desde": None,
            "fatura_url": None,
            # Zera a régua: se a marina atrasar de novo daqui a seis meses, o
            # ciclo de avisos recomeça do dia 0 em vez de ficar mudo por já ter
            # "avisado tudo" na vez anterior.
            "avisos_cobranca": None,
        })
        logger.info(f"Pagamento confirmado no acesso do usuario {user_id}")

    @staticmethod
    def _usuario_da_assinatura(subscription_id: str) -> Optional[str]:
        """
        Descobre de quem e a assinatura pelo checkout que a originou.

        Eventos de fatura e de assinatura nao carregam o id do Supabase — so
        o checkout inicial carrega. E por ele que se chega no dono para cortar
        ou religar o acesso.
        """
        try:
            from app.core.supabase import get_supabase_admin
            origem = (
                get_supabase_admin()
                .table("payments")
                .select("usuario_id")
                .eq("stripe_subscription_id", subscription_id)
                .order("created_at", desc=False)
                .limit(1)
                .execute()
            )
            return (origem.data or [{}])[0].get("usuario_id")
        except Exception as e:
            logger.error(f"Falha ao achar o dono da assinatura {subscription_id}: {e}")
            return None

    # plink -> url. Payment Link nao troca de URL depois de criado, entao uma
    # consulta por link basta para a vida do processo.
    _URL_DO_LINK: Dict[str, str] = {}

    def _url_do_payment_link(self, session) -> Optional[str]:
        """
        A URL do Payment Link que originou este checkout, ou None.

        O evento traz so o id (`plink_...`), e o que temos guardado na
        configuracao sao as URLs. Best-effort: falhando a consulta, devolve None
        e quem chama cai nas outras provas.
        """
        plink = getattr(session, "payment_link", None)
        if not plink:
            return None
        plink_id = plink if isinstance(plink, str) else getattr(plink, "id", None)
        if not plink_id:
            return None
        if plink_id in self._URL_DO_LINK:
            return self._URL_DO_LINK[plink_id]
        try:
            url = stripe.PaymentLink.retrieve(plink_id).url
        except Exception as e:
            logger.warning(f"Nao consegui ler o Payment Link {plink_id}: {e}")
            return None
        self._URL_DO_LINK[plink_id] = url
        return url

    @staticmethod
    def _programas_por_link() -> Dict[str, str]:
        """
        De qual link veio -> qual programa.

        Link nao configurado fica de fora: string vazia como chave casaria com
        qualquer coisa e daria vaga de fundadora para quem nao comprou.
        """
        pares = (
            (settings.STRIPE_LINK_MARINA_FUNDADORA, "marina_fundadora"),
            (settings.STRIPE_LINK_MARINA_FUNDADORA_BRL, "marina_fundadora"),
            (settings.STRIPE_LINK_MARINA_OFICIAL, "marina_oficial"),
            (settings.STRIPE_LINK_MARINA_OFICIAL_BRL, "marina_oficial"),
        )
        return {u.strip(): programa for u, programa in pares if u and u.strip()}

    @staticmethod
    def _tem_reserva_de_fundadora(email: Optional[str]) -> bool:
        """
        Existe vaga de fundadora reservada em nome deste e-mail?

        E a prova mais forte das tres, e a unica que nao depende de configuracao:
        a reserva foi criada pelo NOSSO cadastro, minutos antes, com este mesmo
        e-mail. Nao e inferencia sobre o pagamento — e um fato que ja esta no
        banco.

        Foi o que faltou em 27/08/2026: a Antioquia Marina pagou, recebeu acesso,
        e a vaga dela continuou "reservado" — vencendo em tres horas (o prazo da
        epoca; hoje sao 12h, ver REV-20). O sistema
        tinha a linha na frente dele e nao olhou, porque so sabia perguntar
        "veio do link certo?" e "o valor bate?".

        Best-effort: banco fora do ar devolve False e o pagamento segue. Perder a
        ativacao e ruim; derrubar o webhook e pior, porque ai nem o acesso sai.
        """
        if not email or not email.strip():
            return False
        try:
            from app.core.supabase import get_supabase_admin
            res = (
                get_supabase_admin()
                .table("marinas_fundadoras")
                .select("id,status,uf,reservado_ate")
                .ilike("email", email.strip())
                .neq("status", "ativo")
                .limit(1)
                .execute()
            )
        except Exception as e:
            logger.error(f"Falha ao checar reserva de fundadora de {email}: {e}")
            return False

        linha = (res.data or [None])[0]
        if not linha:
            return False

        # Prazo vencido: a vaga ja voltou para a fila (fn_vagas_fundadoras_ocupadas
        # so conta reserva dentro do prazo), mas a LINHA continua aqui. As 12 horas
        # existem justamente para ninguem parar em cima de uma das 20 vagas sem
        # pagar — honrar reserva vencida sem olhar o estado furaria isso.
        #
        # Sao 20 vagas e ponto: 4 por estado, anunciadas na pagina. Nao existe 5a.
        # Entao reserva vencida so vale se o estado ainda tiver espaco. Encheu, ela
        # NAO vira fundadora — e o sistema grita, porque aquele pagamento veio a
        # preco de fundadora e a diferenca tem que ser devolvida por gente, nao
        # resolvida no escuro.
        if not StripeService._reserva_ainda_de_pe(linha, email):
            return False
        return True

    @staticmethod
    def _reserva_ainda_de_pe(linha: dict, email: str) -> bool:
        """Reserva dentro do prazo, ou vencida mas com vaga sobrando no estado."""
        from datetime import datetime, timezone

        prazo_txt = str(linha.get("reservado_ate") or "")
        if not prazo_txt:
            return True
        try:
            prazo = datetime.fromisoformat(prazo_txt.replace("Z", "+00:00"))
        except ValueError:
            # Data ilegivel nao pode tirar a vaga de quem pagou dentro do prazo.
            return True
        if prazo >= datetime.now(timezone.utc):
            return True

        uf = (linha.get("uf") or "").upper()
        try:
            from app.core.supabase import get_supabase_admin
            ocupadas = (
                get_supabase_admin()
                .rpc("fn_vagas_fundadoras_ocupadas", {"p_uf": uf})
                .execute()
            ).data or 0
        except Exception as e:
            # Sem saber quantas estao ocupadas, nao arrisca a 5a vaga.
            logger.error(f"VAGA FUNDADORA: nao consegui contar as vagas de {uf} ({e}). "
                         f"{email} pagou com reserva vencida e NAO foi ativada.")
            return False

        if int(ocupadas) >= settings.LAUNCH_SLOTS_PER_STATE:
            logger.error(
                f"VAGA FUNDADORA PERDIDA: {email} pagou depois de {prazo.isoformat()} "
                f"e as {settings.LAUNCH_SLOTS_PER_STATE} vagas de {uf} ja estavam "
                "ocupadas. NAO foi ativada como fundadora — devolver a diferenca "
                "para o preco oficial."
            )
            return False

        logger.warning(
            f"VAGA FUNDADORA FORA DO PRAZO: {email} pagou depois de {prazo.isoformat()}, "
            f"mas {uf} ainda tinha vaga. Ativada."
        )
        return True

    def _programa_do_checkout(self, session, metadata: Optional[dict],
                              email: Optional[str] = None) -> Optional[str]:
        """
        Qual programa foi comprado — sem depender de moeda nem de valor.

        Tres provas, nesta ordem:

        1. `metadata.programa`, se o Payment Link foi marcado no painel. E
           intencao declarada, ganha de tudo.
        2. De qual link o checkout veio. Funciona sem ninguem configurar nada,
           e sobrevive a troca de preco e de moeda.
        3. Vaga de fundadora reservada em nome deste e-mail. Nao depende de
           configuracao nenhuma: quem criou a reserva foi o nosso proprio
           cadastro, minutos antes.

        Cada uma existe porque a anterior pode faltar. A 1 depende de quatro
        links marcados a mao. A 2 depende de o link estar na configuracao — e
        um link de teste, ou um link novo que ninguem registrou, passa batido.
        A 3 e a rede embaixo das duas, e foi ela que faltou quando a Antioquia
        Marina pagou e ficou sem vaga.
        """
        declarado = (metadata or {}).get("programa")
        if declarado:
            return declarado
        url = self._url_do_payment_link(session)
        if url:
            do_link = self._programas_por_link().get(url.strip())
            if do_link:
                return do_link
        if self._tem_reserva_de_fundadora(email):
            return "marina_fundadora"
        return None

    def _handle_checkout_completed(self, session: stripe.checkout.Session) -> Dict[str, Any]:
        """Handle checkout session completed"""
        metadata = session.metadata
        user_id = metadata.get('user_id')
        plan_type = metadata.get('plan_type')
        payment_type = metadata.get('payment_type', 'subscription')

        # Payment Link nao carrega user_id no metadata. Como payments.usuario_id
        # e NOT NULL, sem resolver pelo e-mail o pagamento da marina simplesmente
        # nao era gravado: o insert estourava e sobrava so a linha de log.
        # Assinatura (marina) x pagamento avulso (dossie). O dossie e vendido
        # por Payment Link proprio, sem metadata, e nada impede uma faixa de
        # dossie de cair no mesmo valor da assinatura — sem esta distincao a
        # compra de um dossie ocuparia vaga fundadora e liberaria acesso de
        # marina. Ja aconteceu quando a assinatura custava US$ 200, o mesmo
        # que a faixa de 36-45 pes.
        e_assinatura = (
            getattr(session, "mode", None) == "subscription"
            or bool(getattr(session, "subscription", None))
        )

        # `client_reference_id` viaja no link que o backend entregou à marina e
        # NÃO depende de qual e-mail ela usou para pagar. Vem antes do e-mail
        # de propósito: a carteira Link da Stripe usa o endereço da carteira,
        # que raramente é o mesmo do cadastro — e quando os dois divergiam, o
        # pagamento ficava órfão e o acesso não era liberado. Ver
        # `_link_com_identidade` em api/v1/leads.py.
        if not user_id:
            user_id = getattr(session, "client_reference_id", None) or None
            if user_id:
                logger.info(f"Checkout {session.id}: pagador identificado pelo link")

        cliente_email = self._email_do_checkout(session, metadata)
        if not user_id and cliente_email:
            from app.core.supabase import buscar_usuario_por_email
            encontrado = buscar_usuario_por_email(cliente_email)
            user_id = getattr(encontrado, "id", None) if encontrado is not None else None
            if not user_id:
                logger.warning(
                    f"Checkout {session.id}: nenhum usuario com o e-mail {cliente_email} — "
                    "pagamento ficara sem vinculo"
                )

        logger.info(f"Checkout completed for user {user_id}, plan {plan_type}")

        # Persiste o pagamento — é isso que libera o dossiê e dá rastreio financeiro
        try:
            from app.core.supabase import get_supabase_admin
            if not user_id:
                raise ValueError("checkout sem usuario vinculado (usuario_id e NOT NULL)")
            get_supabase_admin().table("payments").insert({
                "usuario_id": user_id,
                "stripe_checkout_session_id": session.id,
                "stripe_payment_intent_id": getattr(session, "payment_intent", None),
                "stripe_subscription_id": getattr(session, "subscription", None),
                "amount": (session.amount_total or 0) / 100,
                "currency": session.currency,
                "status": "completed",
                "payment_type": payment_type,
                "plan_type": plan_type,
                "dossier_level": metadata.get("dossier_level"),
                "ativo_id": metadata.get("ativo_id"),
                "metadata": dict(metadata) if metadata else {},
            }).execute()
        except Exception as e:
            # stripe_checkout_session_id e UNIQUE: colisao significa que o
            # Stripe reentregou o mesmo evento. Sair aqui evita reenviar o
            # e-mail de boas-vindas e reprocessar a vaga fundadora a cada retry.
            if self._e_duplicata(e):
                logger.info(f"Checkout {session.id} ja processado — reentrega ignorada")
                return {
                    "status": "duplicate",
                    "user_id": user_id,
                    "session_id": session.id,
                }
            logger.error(f"Falha ao persistir pagamento do checkout {session.id}: {e}")

        # Libera o acesso que foi criado pendente no cadastro.
        if user_id and payment_type != "dossier" and e_assinatura:
            self._marcar_pagamento_confirmado(user_id)

        # E-mail de boas-vindas da MARCA (best-effort, nunca derruba o webhook).
        # E o "obrigado" da Yachts Atlas no momento exato da liberacao do acesso.
        # Texto NEUTRO quanto a oferta — serve o Lancamento e a Oficial sem
        # depender de adivinhar qual das duas foi vendida. Ver a nota em
        # email_service._welcome_html.
        #
        # `user_id` e obrigatorio aqui pelo mesmo motivo que na linha acima: a
        # conta Stripe e da Axos Hub e vende mais de um produto, e o webhook e
        # POR CONTA — nao da para filtrar por produto. Sem esta trava, um
        # cliente de outro produto da casa recebia "Bem-vindo à Yachts Atlas,
        # seu acesso esta liberado" com botao para um login que nao e dele.
        # Sem usuario no Atlas, nao ha acesso liberado e nao ha o que saudar.
        if user_id and payment_type != "dossier" and e_assinatura:
            try:
                from app.services.email_service import send_welcome_email
                send_welcome_email(
                    cliente_email,
                    nome=self._nome_da_marina(user_id, metadata, session),
                )
            except Exception as e:
                logger.error(f"Falha ao enviar e-mail de boas-vindas ({session.id}): {e}")

        # Programa Marinas Fundadoras: cadastra/ocupa a vaga automaticamente,
        # keyado pelo e-mail do cliente. Best-effort — nunca derruba o webhook.
        #
        # QUEM comprou vem do link de origem, nao do valor pago — ver
        # _programa_do_checkout. Foi o que a venda em real quebrou: a marina
        # brasileira paga R$ 1.000, a regra procurava `usd 200`, e ela entrava
        # no sistema sem ocupar vaga nem ganhar os 18 meses de dossie. Pagou e
        # nao recebeu, sem erro nenhum aparecendo em lugar algum.
        programa = self._programa_do_checkout(session, metadata, cliente_email)

        # DUAS PERGUNTAS DIFERENTES, QUE O VALOR PAGO SOZINHO JA RESPONDEU ERRADO
        #
        # 1. "Esta assinatura e nossa?" — para gravar os 12 meses de preco
        #    travado. O valor serve: assinatura em dolar no nosso preco e
        #    nossa, venha de onde vier. Continua exigindo dolar porque numero
        #    solto nao identifica preco — R$ 140,00 e US$ 140,00 sao o mesmo
        #    `140.0` e valem coisas bem diferentes, e a conta e da Axos Hub,
        #    que vende outros produtos no mesmo webhook.
        #
        # 2. "Esta marina ganha VAGA de fundadora?" — o valor NAO serve, e
        #    desde 13/10/2026 nunca mais serviu: fundadora e oficial pagam o
        #    mesmo US$ 140. Antes US$ 200 queria dizer "campanha" e US$ 250,
        #    "site"; hoje o valor nao diz de onde a marina veio. Quem diz e o
        #    LINK ou o metadata (ver _programa_do_checkout).
        #
        # Enquanto as duas perguntas dividiam a mesma resposta, toda marina
        # Oficial que pagasse em dolar entraria ocupando uma das 4 vagas do
        # estado dela — justamente o que o programa suspenso nao deve mais
        # distribuir.
        valor_pago = (session.amount_total or 0) / 100
        moeda = (getattr(session, "currency", None) or "").lower()

        e_nossa_assinatura = (
            e_assinatura
            and payment_type != "dossier"
            and (programa in ("marina_fundadora", "marina_oficial")
                 or (programa is None
                     and moeda == settings.PRICE_CURRENCY
                     and valor_pago == float(settings.PRECO_MENSAL_USD)))
        )

        # PROGRAMA FUNDADOR SUSPENSO (14/10/2026): o cadastro nao oferece mais
        # vaga a ninguem (ver leads._oferta_marina). Este caminho continua de
        # pe e so dispara com prova EXPLICITA — metadata `programa` marcado no
        # painel, ou o link da campanha preenchido em
        # STRIPE_LINK_MARINA_FUNDADORA. Preencher aquela variavel e, hoje, a
        # forma de religar o programa pelo lado do pagamento.
        e_fundadora = programa == "marina_fundadora"

        if e_fundadora:
            try:
                from app.core.supabase import get_supabase_admin
                marina_email = cliente_email
                if marina_email:
                    _res = get_supabase_admin().rpc("cadastrar_marina_fundadora", {
                        "p_email": marina_email,
                        "p_marina_nome": metadata.get("marina_nome"),
                        "p_responsavel": metadata.get("responsavel"),
                        "p_telefone": metadata.get("telefone"),
                        "p_uf": metadata.get("uf"),
                        "p_stripe_checkout": session.id,
                    }).execute()
                    # Retorno: {modo:'fundadora', slot, ...} ou {modo:'tradicional', ...}
                    # (tradicional = as 20 vagas fundadoras esgotaram; marina segue no fluxo padrao)
                    _r = _res.data if isinstance(_res.data, dict) else {}
                    logger.info(f"Cadastro marina {marina_email}: modo={_r.get('modo')} slot={_r.get('slot')} (checkout {session.id})")

                    if _r.get("modo") == "tradicional":
                        # Assinou pela campanha e nao ha vaga no estado para
                        # honrar. O link e uma URL publica e estatica: quem
                        # tiver ela na mao assina por ali mesmo depois de as 4
                        # vagas do estado esgotarem. O dinheiro esta certo — o
                        # preco e o mesmo para todas —, mas os 18 meses de
                        # dossie 100% ficam em aberto, e isso nao pode passar
                        # despercebido.
                        self._avisar_pagamento_sem_vaga(
                            marina_email, _r.get("motivo"), session.id
                        )
                else:
                    logger.warning(f"Checkout fundadora {session.id} sem e-mail — cadastro nao realizado")
            except Exception as e:
                logger.error(f"Falha ao cadastrar marina fundadora ({session.id}): {e}")

        # Deixa gravado quando o preco travado desta marina vence e por qual
        # regra ele sobe. Vale para TODA marina, fundadora ou nao: desde que o
        # preco passou a ser um so, os 12 meses travados sao de todas. Antes
        # isto acontecia dentro do fluxo da fundadora, porque so ela tinha
        # degrau de preco combinado.
        #
        # So para assinatura RECONHECIDA como nossa (ver as duas perguntas la
        # em cima). A conta Stripe e da Axos Hub e recebe os eventos de todos
        # os produtos da casa: gravar "preco travado ate" em cima de um
        # pagamento que nao sabemos qual preco travou seria inventar uma data
        # — e a carta de reajuste sai dessa data.
        if e_nossa_assinatura and getattr(session, "subscription", None):
            self._registrar_reajuste_do_13o_mes(
                session.subscription, usuario_id=user_id, email=cliente_email
            )

        return {
            "status": "completed",
            "user_id": user_id,
            "plan_type": plan_type,
            "payment_type": payment_type,
            "session_id": session.id,
            "customer_id": session.customer,
            "subscription_id": session.subscription
        }
    
    def _handle_subscription_created(self, subscription: stripe.Subscription) -> Dict[str, Any]:
        """Handle subscription created"""
        metadata = subscription.metadata
        user_id = metadata.get('user_id')
        plan_type = metadata.get('plan_type')
        
        logger.info(f"Subscription created for user {user_id}, plan {plan_type}")
        
        return {
            "status": "created",
            "user_id": user_id,
            "plan_type": plan_type,
            "subscription_id": subscription.id,
            "customer_id": subscription.customer,
            "status": subscription.status
        }
    
    # Situacoes em que a Stripe considera a assinatura encerrada. O corte por
    # atraso e nosso (20 dias, ver acesso.py); estas aqui sao terminais — nao
    # existe mais cobranca automatica para religar sozinha.
    STATUS_ENCERRADOS = ("canceled", "unpaid", "incomplete_expired")

    @staticmethod
    def _devolver_vaga_fundadora(usuario_id: str) -> None:
        """Solta a vaga de fundadora que esta marina ocupava.

        Sao 4 por estado, e elas sao o argumento inteiro da campanha. Enquanto
        isto nao existia, marina que cancelava levava a vaga junto: o contador
        publico anunciava 19 de 20, e a vaga que voce podia vender ficava
        guardada para quem ja tinha saido — calada, sem ninguem notar.

        Best-effort, como todo o resto do webhook: falhar aqui nao pode
        derrubar o processamento do evento. O pior caso e a vaga continuar
        presa, que e exatamente o estado de hoje.
        """
        try:
            from app.core.supabase import get_supabase_admin
            supabase = get_supabase_admin()

            # `marinas_fundadoras` e chaveada por e-mail, nao por usuario_id.
            resposta = supabase.auth.admin.get_user_by_id(usuario_id)
            usuario = getattr(resposta, "user", None) or resposta
            email = (getattr(usuario, "email", None) or "").strip().lower()
            if not email:
                logger.warning(
                    f"Sem e-mail para o usuario {usuario_id} — a vaga fundadora "
                    "nao foi devolvida"
                )
                return

            supabase.table("marinas_fundadoras").update({
                "status": "cancelado",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("email", email).eq("status", "ativo").execute()
            logger.info(f"Vaga fundadora devolvida a fila: {email}")
        except Exception as e:
            logger.error(f"Falha ao devolver a vaga fundadora de {usuario_id}: {e}")

    def _bloquear_por_assinatura_encerrada(self, subscription_id: str, motivo: str) -> None:
        """Encerra a assinatura: tira o acesso, a vaga e a condicao de fundadora.

        Sao tres movimentos, e por muito tempo so o primeiro acontecia.

        A regra de negocio (decidida em 15/09/2026) e que a condicao de
        fundadora vale ENQUANTO a assinatura estiver ativa. Quem sai devolve o
        lugar; se voltar, entra pela porta normal, no valor oficial. Sem o
        `oferta -> oficial` daqui, a marina que cancelou clicava em "Assinar
        novamente" e recebia de volta o link de fundadora — pagando o preco de
        lancamento por uma vaga que ela mesma tinha liberado.
        """
        usuario_id = self._usuario_da_assinatura(subscription_id)
        if not usuario_id:
            logger.warning(
                f"Assinatura {subscription_id} encerrada ({motivo}), mas sem "
                "checkout de origem — nenhum acesso foi revogado"
            )
            return

        self._atualizar_metadata(usuario_id, {
            "pagamento": "cancelado",
            "oferta": "oficial",
            "preco_mensal": settings.PRECO_MENSAL_USD,
        })
        self._devolver_vaga_fundadora(usuario_id)
        logger.info(f"Acesso revogado ({motivo}): assinatura {subscription_id}")

    def _handle_subscription_updated(self, subscription: stripe.Subscription) -> Dict[str, Any]:
        """Handle subscription updated"""
        metadata = subscription.metadata
        user_id = metadata.get('user_id')
        plan_type = metadata.get('plan_type')

        logger.info(f"Subscription updated for user {user_id}, plan {plan_type}, status {subscription.status}")

        # Só reage ao que encerra a assinatura. O religamento fica por conta do
        # invoice.paid — este evento dispara a cada mudancinha da assinatura, e
        # reescrever o acesso em todas elas seria ruído e risco à toa.
        if subscription.status in self.STATUS_ENCERRADOS:
            self._bloquear_por_assinatura_encerrada(
                subscription.id, f"status={subscription.status}"
            )

        return {
            "status": "updated",
            "user_id": user_id,
            "plan_type": plan_type,
            "subscription_id": subscription.id,
            "status": subscription.status
        }
    
    def _handle_subscription_deleted(self, subscription: stripe.Subscription) -> Dict[str, Any]:
        """Handle subscription deleted/cancelled"""
        metadata = subscription.metadata
        user_id = metadata.get('user_id')
        plan_type = metadata.get('plan_type')
        
        logger.info(f"Subscription deleted for user {user_id}, plan {plan_type}")

        # Cancelamento voluntario chega aqui so no fim do periodo ja pago — ate
        # la a marina continua usando o que comprou, como tem que ser.
        self._bloquear_por_assinatura_encerrada(subscription.id, "assinatura cancelada")

        return {
            "status": "cancelled",
            "user_id": user_id,
            "plan_type": plan_type,
            "subscription_id": subscription.id
        }
    
    @staticmethod
    def _extract_subscription_id(invoice: stripe.Invoice) -> Optional[str]:
        """
        Le o id da assinatura da invoice em qualquer versao da API.

        Ate 2025-03-31.basil a Stripe expunha `invoice.subscription`. Depois
        disso o campo saiu e virou `invoice.parent.subscription_details.subscription`.
        A conta nova ja nasce numa versao recente, entao aceitamos os dois
        formatos — senao a renovacao mensal quebra silenciosamente.
        """
        def _as_id(value):
            if not value:
                return None
            return value if isinstance(value, str) else getattr(value, "id", None)

        legado = _as_id(getattr(invoice, "subscription", None))
        if legado:
            return legado

        parent = getattr(invoice, "parent", None)
        detalhes = getattr(parent, "subscription_details", None) if parent else None
        return _as_id(getattr(detalhes, "subscription", None) if detalhes else None)

    def _registrar_renovacao(
        self,
        invoice: stripe.Invoice,
        subscription_id: str,
        amount_paid: float
    ) -> None:
        """
        Grava a renovacao mensal em payments.

        A recorrencia e o produto: sem isto o banco so conhece o primeiro mes de
        cada marina e nao da para saber quem esta adimplente. A invoice nao
        carrega o id do Supabase, entao o usuario vem da linha do checkout
        original da mesma assinatura.
        """
        try:
            from app.core.supabase import get_supabase_admin
            admin = get_supabase_admin()
            origem = (
                admin.table("payments")
                .select("usuario_id, plan_type, payment_type")
                .eq("stripe_subscription_id", subscription_id)
                .order("created_at", desc=False)
                .limit(1)
                .execute()
            )
            base = (origem.data or [{}])[0]
            usuario_id = base.get("usuario_id")
            if not usuario_id:
                logger.warning(
                    f"Renovacao da assinatura {subscription_id} sem checkout de "
                    "origem — nao foi gravada"
                )
                return

            admin.table("payments").insert({
                "usuario_id": usuario_id,
                "stripe_invoice_id": invoice.id,
                "stripe_subscription_id": subscription_id,
                "amount": amount_paid,
                "currency": invoice.currency,
                "status": "completed",
                "payment_type": base.get("payment_type") or "subscription",
                "plan_type": base.get("plan_type"),
                "metadata": {"billing_reason": getattr(invoice, "billing_reason", None)},
            }).execute()
            logger.info(f"Renovacao registrada: assinatura {subscription_id}, ${amount_paid}")
        except Exception as e:
            if self._e_duplicata(e):
                logger.info(f"Renovacao da invoice {invoice.id} ja registrada")
            else:
                logger.error(
                    f"Falha ao registrar renovacao da assinatura {subscription_id}: {e}"
                )

    def _handle_invoice_paid(self, invoice: stripe.Invoice) -> Dict[str, Any]:
        """Handle invoice paid"""
        subscription_id = self._extract_subscription_id(invoice)
        customer_id = invoice.customer
        amount_paid = invoice.amount_paid / 100  # Convert from cents
        billing_reason = getattr(invoice, "billing_reason", None)

        logger.info(f"Invoice paid for subscription {subscription_id}, amount ${amount_paid}")

        # 'subscription_create' e a primeira fatura, que ja entrou em payments
        # pelo checkout.session.completed — gravar de novo contaria o mesmo
        # dinheiro duas vezes. So as renovacoes passam daqui.
        if subscription_id and billing_reason != "subscription_create":
            self._registrar_renovacao(invoice, subscription_id, amount_paid)

            # Pagou, volta a funcionar — sem ninguem apertar nada. Se a marina
            # estava cortada, o acesso volta na proxima requisicao dela.
            usuario_id = self._usuario_da_assinatura(subscription_id)
            if usuario_id:
                self._marcar_pagamento_confirmado(usuario_id)

        return {
            "status": "paid",
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "amount_paid": amount_paid,
            "currency": invoice.currency
        }
    
    def _handle_invoice_payment_failed(self, invoice: stripe.Invoice) -> Dict[str, Any]:
        """Handle invoice payment failed"""
        subscription_id = self._extract_subscription_id(invoice)
        customer_id = invoice.customer

        logger.warning(f"Invoice payment failed for subscription {subscription_id}")

        # Comeca a contar os 20 dias. `preservar` garante que a data seja a da
        # PRIMEIRA recusa: o Stripe tenta de novo varias vezes, e sem isso cada
        # tentativa empurraria o corte para frente e ele nunca aconteceria.
        # A marina segue usando o sistema durante o prazo — quem corta e o
        # porteiro (app/core/acesso.py), ao ver a data ficar velha demais.
        usuario_id = self._usuario_da_assinatura(subscription_id) if subscription_id else None
        if usuario_id:
            self._atualizar_metadata(
                usuario_id,
                {
                    "inadimplente_desde": datetime.now(timezone.utc).isoformat(),
                    "fatura_url": getattr(invoice, "hosted_invoice_url", None),
                },
                preservar=("inadimplente_desde",),
            )
            # Aviso do dia 0 sai agora, não na madrugada seguinte: quanto antes
            # a marina souber do cartão recusado, mais barato é resolver.
            try:
                from app.services.cobranca_service import avisar_primeira_recusa
                avisar_primeira_recusa(usuario_id)
            except Exception as e:
                logger.error(f"Falha ao avisar da primeira recusa ({usuario_id}): {e}")

        # Recorrencia falhando em silencio = marina perdida sem ninguem saber.
        try:
            from app.services.notify_service import notificar_fundador
            notificar_fundador(
                "Falha no pagamento",
                f"Assinatura {subscription_id} — tentativa {invoice.attempt_count}.\n"
                f"Cliente Stripe: {customer_id}\n"
                f"Acesso é cortado após {settings.DIAS_ATE_CORTE_INADIMPLENCIA} "
                "dias da primeira recusa.",
            )
        except Exception as e:
            logger.error(f"Falha ao avisar sobre pagamento recusado: {e}")

        return {
            "status": "failed",
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "attempt_count": invoice.attempt_count
        }
    
    def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription status from Stripe"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                "status": subscription.status,
                "current_period_end": subscription.current_period_end,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "items": [
                    {
                        "price_id": item.price.id,
                        "quantity": item.quantity
                    }
                    for item in subscription.items.data
                ]
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving subscription: {str(e)}")
            raise Exception(f"Failed to retrieve subscription: {str(e)}")
    
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> Dict[str, Any]:
        """Cancel subscription"""
        try:
            # `Subscription.delete` nao aceita at_period_end — a API responde
            # "Received unknown parameter". Cancelar no fim do ciclo e um
            # update (cancel_at_period_end); delete e o cancelamento imediato.
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)
            
            logger.info(f"Subscription {subscription_id} cancelled")
            
            return {
                "status": "cancelled",
                "subscription_id": subscription_id,
                "cancel_at_period_end": at_period_end,
                "canceled_at": getattr(subscription, "canceled_at", None),
                "cancel_at": getattr(subscription, "cancel_at", None)
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {str(e)}")
            raise Exception(f"Failed to cancel subscription: {str(e)}")
    
    def get_pricing_plans(self) -> Dict[str, Any]:
        """
        Planos ativos na plataforma. Modelo atual: uma única recorrência B2B
        de US$ 140/mês (Marina) — mesmo valor para fundadora e para quem chega
        pelo site —, travada por 12 meses e corrigida depois por IPCA + 15%. O
        dossiê não é vendido pela plataforma — vai direto marina <-> dono —
        então não aparece aqui.
        """
        marina = self.PRICING[PlanType.MARINA]
        return {
            "plans": {
                PlanType.MARINA.value: {
                    "monthly": marina["monthly"],
                    "name": marina["name"],
                    "features": marina["features"],
                }
            },
            "currency": "USD"
        }


def get_stripe_service() -> StripeService:
    """Factory function to get StripeService instance"""
    return StripeService()
