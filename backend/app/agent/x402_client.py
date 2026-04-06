import httpx
from app.stellar.wallet import send_payment, get_keypair
from app.config import get_settings

settings = get_settings()

# Stellar's hosted x402 facilitator
X402_FACILITATOR = "https://x402.org/facilitator"


class X402PaymentError(Exception):
    pass


class X402Client:
    """
    Handles the x402 payment flow using Stellar's x402 facilitator:
    1. Makes API request
    2. If 402 Payment Required → sends payment details to facilitator
    3. Facilitator verifies & returns payment proof
    4. Retries original request with payment proof header
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)

    async def fetch(self, url: str) -> dict:
        """
        Fetch a resource, handling x402 payment if required.
        """
        # Step 1: Initial request
        response = await self.client.get(url)

        # Step 2: Handle 402 Payment Required
        if response.status_code == 402:
            payment_info = self._parse_payment_details(response)

            # Step 3: Pay via Stellar
            stellar_hash = await self._pay(payment_info)

            # Step 4: Verify with facilitator
            payment_proof = await self._verify_with_facilitator(
                url=url,
                stellar_hash=stellar_hash,
                payment_info=payment_info
            )

            # Step 5: Retry with payment proof
            paid_response = await self.client.get(
                url,
                headers={
                    "X-Payment": payment_proof,
                    "X-Payment-Hash": stellar_hash
                }
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
        Parse payment details from 402 response.
        x402 standard sends payment info in headers or body.
        """
        # Try headers first
        amount = response.headers.get("X-Payment-Amount")
        currency = response.headers.get("X-Payment-Currency", "XLM")
        destination = response.headers.get("X-Payment-Destination")
        network = response.headers.get("X-Payment-Network", "testnet")

        # Fallback to response body
        if not amount or not destination:
            try:
                body = response.json()
                amount = body.get("amount", "0.01")
                currency = body.get("currency", "XLM")
                destination = body.get("destination")
                network = body.get("network", "testnet")
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
            "destination": destination,
            "network": network
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

    async def _verify_with_facilitator(
        self,
        url: str,
        stellar_hash: str,
        payment_info: dict
    ) -> str:
        """
        Verify payment with Stellar's x402 facilitator.
        Facilitator checks the transaction on chain and returns proof.
        """
        try:
            keypair = get_keypair()

            payload = {
                "transaction_hash": stellar_hash,
                "resource_url": url,
                "amount": payment_info["amount"],
                "currency": payment_info["currency"],
                "destination": payment_info["destination"],
                "network": payment_info.get("network", "testnet"),
                "payer_public_key": keypair.public_key
            }

            facilitator_response = await self.client.post(
                f"{X402_FACILITATOR}/verify",
                json=payload,
                timeout=15
            )

            if facilitator_response.status_code == 200:
                data = facilitator_response.json()
                # Return proof token from facilitator
                return data.get("payment_proof", stellar_hash)
            else:
                # Fallback to just using the hash as proof
                # Some x402 APIs accept the raw Stellar hash
                return stellar_hash

        except Exception:
            # If facilitator is unreachable, fall back to raw hash
            return stellar_hash

    async def close(self):
        await self.client.aclose()