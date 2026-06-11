"""
Yachts Atlas — Stripe Payment Service
Complete payment processing with Stripe
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
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
            "monthly": 250,
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
    
    def _get_or_create_price(
        self,
        amount: int,
        currency: str,
        recurring: bool,
        product_name: str
    ) -> str:
        """
        Get existing price or create new one
        """
        try:
            # Search for existing price
            prices = stripe.Price.list(
                amount=amount,
                currency=currency,
                type='recurring' if recurring else 'one_time',
                limit=1
            )
            
            if prices.data:
                return prices.data[0].id
            
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
            }
            
            if recurring:
                price_data['recurring'] = {
                    'interval': 'month',
                    'interval_count': 1
                }
            
            price = stripe.Price.create(**price_data)
            
            logger.info(f"Created new price {price.id} for {product_name}")
            return price.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating price: {str(e)}")
            raise Exception(f"Failed to create price: {str(e)}")
    
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
    
    def _handle_checkout_completed(self, session: stripe.checkout.Session) -> Dict[str, Any]:
        """Handle checkout session completed"""
        metadata = session.metadata
        user_id = metadata.get('user_id')
        plan_type = metadata.get('plan_type')
        payment_type = metadata.get('payment_type', 'subscription')

        logger.info(f"Checkout completed for user {user_id}, plan {plan_type}")

        # Persiste o pagamento — é isso que libera o dossiê e dá rastreio financeiro
        try:
            from app.core.supabase import get_supabase_admin
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
            logger.error(f"Falha ao persistir pagamento do checkout {session.id}: {e}")

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
    
    def _handle_subscription_updated(self, subscription: stripe.Subscription) -> Dict[str, Any]:
        """Handle subscription updated"""
        metadata = subscription.metadata
        user_id = metadata.get('user_id')
        plan_type = metadata.get('plan_type')
        
        logger.info(f"Subscription updated for user {user_id}, plan {plan_type}, status {subscription.status}")
        
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
        
        return {
            "status": "cancelled",
            "user_id": user_id,
            "plan_type": plan_type,
            "subscription_id": subscription.id
        }
    
    def _handle_invoice_paid(self, invoice: stripe.Invoice) -> Dict[str, Any]:
        """Handle invoice paid"""
        subscription_id = invoice.subscription
        customer_id = invoice.customer
        amount_paid = invoice.amount_paid / 100  # Convert from cents
        
        logger.info(f"Invoice paid for subscription {subscription_id}, amount ${amount_paid}")
        
        return {
            "status": "paid",
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "amount_paid": amount_paid,
            "currency": invoice.currency
        }
    
    def _handle_invoice_payment_failed(self, invoice: stripe.Invoice) -> Dict[str, Any]:
        """Handle invoice payment failed"""
        subscription_id = invoice.subscription
        customer_id = invoice.customer
        
        logger.warning(f"Invoice payment failed for subscription {subscription_id}")
        
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
            subscription = stripe.Subscription.delete(
                subscription_id,
                at_period_end=at_period_end
            )
            
            logger.info(f"Subscription {subscription_id} cancelled")
            
            return {
                "status": "cancelled",
                "subscription_id": subscription_id,
                "cancel_at_period_end": at_period_end,
                "canceled_at": subscription.canceled_at
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {str(e)}")
            raise Exception(f"Failed to cancel subscription: {str(e)}")
    
    def get_pricing_plans(self) -> Dict[str, Any]:
        """Get all available pricing plans"""
        return {
            "plans": {
                plan_type.value: {
                    "monthly": config["monthly"],
                    "name": config["name"],
                    "features": config["features"]
                }
                for plan_type, config in self.PRICING.items()
            },
            "dossiers": {
                level.value: price
                for level, price in self.DOSSIER_PRICING.items()
            },
            "dossier_roi_split_ratio": self.DOSSIER_ROI_SPLIT_RATIO,
            "currency": "USD"
        }


def get_stripe_service() -> StripeService:
    """Factory function to get StripeService instance"""
    return StripeService()
