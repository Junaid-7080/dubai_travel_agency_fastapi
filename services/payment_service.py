# ===== services/payment_service.py =====
import stripe
import requests
from typing import Dict, Any, Optional
from config import settings
import logging

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.stripe_secret_key

class PaymentService:
    
    async def create_stripe_payment_intent(self, amount: float, currency: str = "AED", metadata: Dict = None) -> Dict[str, Any]:
        """Create Stripe payment intent"""
        try:
            # Convert AED to fils (Stripe works with smallest currency unit)
            amount_in_fils = int(amount * 100)
            
            intent = stripe.PaymentIntent.create(
                amount=amount_in_fils,
                currency=currency.lower(),
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True},
            )
            
            return {
                "success": True,
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "status": intent.status
            }
            
        except Exception as e:
            logger.error(f"Stripe payment intent creation failed: {e}")
            return {"success": False, "error": str(e)}

    async def confirm_stripe_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm Stripe payment status"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                "success": True,
                "status": intent.status,
                "amount_received": intent.amount_received / 100,  # Convert back from fils
                "charges": intent.charges.data
            }
            
        except Exception as e:
            logger.error(f"Stripe payment confirmation failed: {e}")
            return {"success": False, "error": str(e)}

    async def create_paypal_order(self, amount: float, currency: str = "USD", return_url: str = None) -> Dict[str, Any]:
        """Create PayPal order (simplified implementation)"""
        try:
            # PayPal API endpoint
            url = "https://api.sandbox.paypal.com/v2/checkout/orders"
            
            # Get PayPal access token (simplified)
            auth_response = requests.post(
                "https://api.sandbox.paypal.com/v1/oauth2/token",
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "en_US",
                },
                data="grant_type=client_credentials",
                auth=(settings.paypal_client_id, settings.paypal_client_secret)
            )
            
            if auth_response.status_code != 200:
                return {"success": False, "error": "PayPal authentication failed"}
            
            access_token = auth_response.json().get("access_token")
            
            # Create order
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": currency,
                        "value": str(amount)
                    }
                }],
                "application_context": {
                    "return_url": return_url or "https://yoursite.com/success",
                    "cancel_url": "https://yoursite.com/cancel"
                }
            }
            
            response = requests.post(
                url,
                json=order_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}",
                }
            )
            
            if response.status_code == 201:
                order = response.json()
                return {
                    "success": True,
                    "order_id": order["id"],
                    "approval_url": next(
                        link["href"] for link in order["links"] 
                        if link["rel"] == "approve"
                    )
                }
            else:
                return {"success": False, "error": "PayPal order creation failed"}
                
        except Exception as e:
            logger.error(f"PayPal order creation failed: {e}")
            return {"success": False, "error": str(e)}

    async def create_paytabs_payment(self, amount: float, currency: str = "AED", customer_email: str = None) -> Dict[str, Any]:
        """Create PayTabs payment page (simplified implementation)"""
        try:
            url = "https://secure.paytabs.sa/payment/request"
            
            payload = {
                "profile_id": settings.paytabs_merchant_id,
                "tran_type": "sale",
                "tran_class": "ecom",
                "cart_description": "Dubai Travel Agency Booking",
                "cart_currency": currency,
                "cart_amount": amount,
                "customer_email": customer_email or "customer@example.com",
                "return": "https://yoursite.com/payment/return",
                "callback": "https://yoursite.com/payment/callback"
            }
            
            headers = {
                "Authorization": settings.paytabs_secret_key,
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "payment_url": result.get("redirect_url"),
                    "tran_ref": result.get("tran_ref")
                }
            else:
                return {"success": False, "error": "PayTabs payment creation failed"}
                
        except Exception as e:
            logger.error(f"PayTabs payment creation failed: {e}")
            return {"success": False, "error": str(e)}

    async def process_payment(self, payment_method: str, amount: float, metadata: Dict = None) -> Dict[str, Any]:
        """Process payment based on method"""
        if payment_method == "stripe":
            return await self.create_stripe_payment_intent(amount, metadata=metadata)
        elif payment_method == "paypal":
            return await self.create_paypal_order(amount)
        elif payment_method == "paytabs":
            return await self.create_paytabs_payment(amount, customer_email=metadata.get("email"))
        else:
            return {"success": False, "error": "Unsupported payment method"}

# Initialize payment service
payment_service = PaymentService()