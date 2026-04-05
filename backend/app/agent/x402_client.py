import httpx
from app.stellar.wallet import send_payment
from app.config import get_settings

settings = get_settings()


class X402PaymentError(Exception):
    """Raised when x402 payment fails"""
    pass


class X402Client:
    """
    Handles the x402 payment flow:
    1. Makes API request
    2. If 402 Payment Required → parses payment details
    3. Signs & submits Stellar payment
    4. Retries original request with payment proof
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)

    async def fetch(self, url: str) -> dict:
        """
        Fetch a resource, handling x402 payment if required.
        Returns dict with response data and payment info.
        """
        # Step 1: Initial request
        response = await self.client.get(url)

        # Step 2: Handle 402 Payment Required
        if response.status_code == 402:
            payment_info = self._parse_payment_details(response)
            stellar_hash = await self._pay(payment_info)

            # --- Step 3: Retry with payment proof ---
            paid_response = await self.client.get(
                url,
                headers={"X-Payment": stellar_hash}
            )

            if paid_response.status_code != 200:
                raise X402PaymentError(
                    f"Payment sent but access denied. Hash: {stellar_hash}"
                )

            return {
                "data": paid_response.json(),
                "paid": True,
                "amount": payment_info["amount"],
                "currency": payment_info["currency"],
                "stellar_hash": stellar_hash,
                "api_url": url
            }

        # --- No payment needed ---
        if response.status_code == 200:
            return {
                "data": response.json(),
                "paid": False,
                "amount": 0,
                "currency": None,
                "stellar_hash": None,
                "api_url": url
            }

        raise X402PaymentError(
            f"Unexpected response {response.status_code} from {url}"
        )

    def _parse_payment_details(self, response: httpx.Response) -> dict:
        """
        Parse payment details from 402 response headers.
        x402 standard sends payment info in headers or body.
        """
        # Try headers first
        amount = response.headers.get("X-Payment-Amount")
        currency = response.headers.get("X-Payment-Currency", "XLM")
        destination = response.headers.get("X-Payment-Destination")

        # Fallback to response body
        if not amount or not destination:
            try:
                body = response.json()
                amount = body.get("amount", "0.01")
                currency = body.get("currency", "XLM")
                destination = body.get("destination")
            except Exception:
                raise X402PaymentError(
                    "Could not parse payment details from 402 response"
                )

        if not destination:
            raise X402PaymentError(
                "No payment destination found in 402 response"
            )

        return {
            "amount": str(amount),
            "currency": currency,
            "destination": destination
        }

    async def _pay(self, payment_info: dict) -> str:
        """
        Submit Stellar payment and return transaction hash.
        """
        try:
            stellar_hash = send_payment(
                destination=payment_info["destination"],
                amount=payment_info["amount"],
                asset_code=payment_info["currency"]
            )
            return stellar_hash
        except Exception as e:
            raise X402PaymentError(f"Stellar payment failed: {str(e)}")

    async def close(self):
        await self.client.aclose()