"""
Yachts Atlas — Stripe Payment Service
Complete payment processing with Stripe
"""
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


class DossierLevel(str, Enum):
    """Dossier certification levels"""
    COMPACT = "compact"
    EXECUTIVE = "executive"
    SUPERYACHT = "superyacht"


class StripeService:
    """Premium Stripe service for payment processing"""
    DOSSIER_ROI_SPLIT_RATIO = 0.5
    
    # Pricing configuration (in USD) - B2B2C Model
    # Marinas pay monthly, resell to asset owners
    PRICING = {
        PlanType.FREE: {
            "monthly": 0,
            "name": "Free Tier",
            "features": ["1 asset", "Basic tracking", "Community support"]
        },
        PlanType.MARINA: {
            # Preco oficial da recorrencia (as 20 fundadoras pagam
            # settings.LAUNCH_PRICE_MONTHLY, decidido em leads._oferta_marina).
            "monthly": settings.TRADITIONAL_PRICE_MONTHLY,
            "name": "Marina Standard",
            "features": ["Unlimited assets", "Fleet management", "Priority support", "API access", "Real-time monitoring", "Audit reports", "White-label ready"]
        },
        PlanType.ENTERPRISE: {
            "monthly": 500,
            "name": "Enterprise",
            "features": ["Unlimited assets", "Multi-location management", "24/7 dedicated support", "White-label", "Full API access", "Custom integrations", "SLA guarantee"]
        }
    }
    
    # Dossier pricing (one-time) - Sold directly to asset owners
    DOSSIER_PRICING = {
        DossierLevel.COMPACT: 200,
        DossierLevel.EXECUTIVE: 400,
        DossierLevel.SUPERYACHT: 600
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
    def create_dossier_checkout_session(
        self,
        user_id: str,
        dossier_level: DossierLevel,
        ativo_id: str,
        success_url: str,
        cancel_url: str,
        marina_stripe_account_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create Stripe checkout session for dossier certification (one-time payment)
        With 50/50 split between platform and marina
        """
        try:
            amount = self.DOSSIER_PRICING[dossier_level]
            
            # Create or get price
            price_id = self._get_or_create_price(
                amount=amount * 100,  # Convert to cents
                currency="usd",
                recurring=False,
                product_name=f"Dossier {dossier_level.value.capitalize()} Certification"
            )
            
            # Base session parameters
            session_params = {
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': price_id,
                    'quantity': 1,
                }],
                'mode': 'payment',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'customer_email': metadata.get('email') if metadata else None,
                'metadata': {
                    'user_id': user_id,
                    'dossier_level': dossier_level.value,
                    'ativo_id': ativo_id,
                    'payment_type': 'dossier',
                    'split_enabled': 'true' if marina_stripe_account_id else 'false',
                    **(metadata or {})
                }
            }

            # Implement 50/50 Revenue Split if Marina Account is provided
            if marina_stripe_account_id:
                # Stripe Connect: Marina receives 50% directly
                split_amount = int((amount * 100) * self.DOSSIER_ROI_SPLIT_RATIO)
                session_params['payment_intent_data'] = {
                    'transfer_data': {
                        'destination': marina_stripe_account_id,
                        'amount': split_amount
                    }
                }
                logger.info(f"Split payment configured: 50% (${amount/2}) to marina {marina_stripe_account_id}")

            # Create checkout session
            session = stripe.checkout.Session.create(**session_params)
            
            logger.info(f"Created dossier checkout session {session.id} for user {user_id}, level {dossier_level.value}")
            
            return {
                "session_id": session.id,
                "url": session.url,
                "dossier_level": dossier_level.value,
                "ativo_id": ativo_id,
                "amount": amount,
                "split_active": bool(marina_stripe_account_id)
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating dossier checkout session: {str(e)}")
            raise Exception(f"Failed to create dossier checkout session: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating dossier checkout session: {str(e)}")
            raise Exception(f"Failed to create dossier checkout session: {str(e)}")
    
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
        """Alguém pagou o preço de fundadora sem ter vaga — decisão é humana."""
        try:
            from app.services.notify_service import notificar_fundador
            notificar_fundador(
                f"Pagou ${settings.LAUNCH_PRICE_MONTHLY} sem vaga fundadora",
                f"{email or 'sem e-mail'} — motivo: {motivo or 'desconhecido'}.\n"
                f"Checkout {checkout_id}.\n"
                f"A assinatura está ativa a ${settings.LAUNCH_PRICE_MONTHLY}/mês. "
                f"Decida: honrar como fundadora, migrar para "
                f"${settings.TRADITIONAL_PRICE_MONTHLY} ou reembolsar.",
            )
        except Exception as e:
            logger.error(f"Falha ao avisar sobre pagamento sem vaga ({checkout_id}): {e}")

    @staticmethod
    def _id_do_preco(item: Any) -> Optional[str]:
        """O preço de um item de fase vem como id ou como objeto, conforme a versão."""
        preco = item.get("price") if isinstance(item, dict) else getattr(item, "price", None)
        if isinstance(preco, str):
            return preco
        if isinstance(preco, dict):
            return preco.get("id")
        return getattr(preco, "id", None)

    def _agendar_correcao_do_13o_mes(self, subscription_id: str) -> None:
        """
        Deixa agendado na Stripe: 12 meses a $200, depois $250.

        Combinado na venda — a fundadora paga o preço de lançamento por um ano
        e entra na tabela oficial no 13º mês. Quem executa é a própria Stripe,
        na data de CADA marina: quem assinou em outubro vira em outubro, quem
        assinou em dezembro vira em dezembro. Não existe rotina nossa para
        rodar — nem para alguém esquecer de rodar — um ano depois.

        Best-effort: o pagamento já aconteceu, e falhar aqui não pode derrubar
        o webhook. Se falhar, o Telegram avisa para ser feito no painel.
        """
        try:
            preco_oficial = self._get_or_create_price(
                amount=settings.TRADITIONAL_PRICE_MONTHLY * 100,
                currency="usd",
                recurring=True,
                product_name=self.PRICING[PlanType.MARINA]["name"],
            )

            # O cronograma nasce da assinatura que já existe, então a primeira
            # fase precisa repetir os itens que ela já tem — é o que ancora a
            # troca no aniversário certo em vez de recomeçar o ciclo hoje.
            agenda = stripe.SubscriptionSchedule.create(from_subscription=subscription_id)
            itens_atuais = [
                {"price": self._id_do_preco(item), "quantity": item.get("quantity", 1) or 1}
                for item in agenda.phases[0]["items"]
            ]
            if not all(item["price"] for item in itens_atuais):
                raise ValueError("não consegui ler o preço atual da assinatura")

            stripe.SubscriptionSchedule.modify(
                agenda.id,
                end_behavior="release",
                phases=[
                    {"items": itens_atuais, "iterations": settings.LAUNCH_PRICE_MONTHS},
                    {"items": [{"price": preco_oficial, "quantity": 1}]},
                ],
            )
            logger.info(
                f"Correção do 13º mês agendada para {subscription_id}: "
                f"{settings.LAUNCH_PRICE_MONTHS} meses a ${settings.LAUNCH_PRICE_MONTHLY}, "
                f"depois ${settings.TRADITIONAL_PRICE_MONTHLY}"
            )
        except Exception as e:
            logger.error(f"Falha ao agendar o 13º mês de {subscription_id}: {e}")
            try:
                from app.services.notify_service import notificar_fundador
                notificar_fundador(
                    "Reajuste do 13º mês não agendado",
                    f"Assinatura {subscription_id} ficou sem o cronograma de "
                    f"${settings.LAUNCH_PRICE_MONTHLY} → ${settings.TRADITIONAL_PRICE_MONTHLY}.\n"
                    "Agende na mão no painel da Stripe, senão ela paga o preço "
                    "de fundadora para sempre.",
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
        # por Payment Link proprio, sem metadata, e a faixa de 36-45 pes custa
        # os mesmos US$ 200 da marina fundadora — sem esta distincao a compra de
        # um dossie ocuparia vaga fundadora e liberaria acesso de marina.
        e_assinatura = (
            getattr(session, "mode", None) == "subscription"
            or bool(getattr(session, "subscription", None))
        )

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
        # O recibo financeiro fica a cargo da processadora; este é o "obrigado"
        # do Yachts Atlas no exato momento da liberação do acesso.
        if payment_type != "dossier" and e_assinatura:
            try:
                from app.services.email_service import send_welcome_email
                nome = metadata.get("marina_nome") or metadata.get("nome")
                send_welcome_email(cliente_email, nome=nome)
            except Exception as e:
                logger.error(f"Falha ao enviar e-mail de boas-vindas ({session.id}): {e}")

        # Programa Marinas Fundadoras: cadastra/ocupa a vaga automaticamente,
        # keyado pelo e-mail do cliente. Best-effort — nunca derruba o webhook.
        #
        # O metadata `programa` so chega se o Payment Link tiver sido configurado
        # com ele no painel do Stripe. Faltando ele, a vaga nunca era ocupada,
        # marinas_fundadoras ficava em zero e _oferta_marina continuaria
        # mandando TODA marina seguinte para o link de US$ 200 — as 20 vagas
        # nunca esgotavam. Por isso o valor pago tambem vale como prova: uma
        # assinatura de US$ 200/mes e, por definicao, preco de fundadora.
        valor_pago = (session.amount_total or 0) / 100
        e_fundadora = (
            (metadata or {}).get("programa") == "marina_fundadora"
            or (e_assinatura
                and payment_type != "dossier"
                and valor_pago == float(settings.LAUNCH_PRICE_MONTHLY))
        )
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
                        # Pagou $200 e nao ha vaga para honrar. O link de $200 e
                        # uma URL publica e estatica: quem tiver ela na mao paga
                        # esse valor mesmo depois das 20 esgotarem. Isso nao pode
                        # passar despercebido — e uma assinatura recorrente a
                        # menos $50/mes para sempre.
                        self._avisar_pagamento_sem_vaga(
                            marina_email, _r.get("motivo"), session.id
                        )
                    elif getattr(session, "subscription", None):
                        self._agendar_correcao_do_13o_mes(session.subscription)
                else:
                    logger.warning(f"Checkout fundadora {session.id} sem e-mail — cadastro nao realizado")
            except Exception as e:
                logger.error(f"Falha ao cadastrar marina fundadora ({session.id}): {e}")

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

    def _bloquear_por_assinatura_encerrada(self, subscription_id: str, motivo: str) -> None:
        """Tira o acesso de quem nao tem mais assinatura ativa."""
        usuario_id = self._usuario_da_assinatura(subscription_id)
        if not usuario_id:
            logger.warning(
                f"Assinatura {subscription_id} encerrada ({motivo}), mas sem "
                "checkout de origem — nenhum acesso foi revogado"
            )
            return
        self._atualizar_metadata(usuario_id, {"pagamento": "cancelado"})
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
        de $250/mês (Marina), com as 20 primeiras marinas a $200/mês. O dossiê
        não é vendido pela plataforma — vai direto marina <-> dono — então não
        aparece aqui.
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
