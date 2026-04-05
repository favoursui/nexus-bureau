from stellar_sdk import Keypair, Server, TransactionBuilder, Network, Asset
from stellar_sdk.exceptions import NotFoundError
from app.config import get_settings

settings = get_settings()

# Network config
if settings.STELLAR_NETWORK == "testnet":
    HORIZON_URL = "https://horizon-testnet.stellar.org"
    NETWORK_PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE
else:
    HORIZON_URL = "https://horizon.stellar.org"
    NETWORK_PASSPHRASE = Network.PUBLIC_NETWORK_PASSPHRASE

server = Server(HORIZON_URL)


def get_keypair() -> Keypair:
    """Load agent keypair from env"""
    return Keypair.from_secret(settings.STELLAR_SECRET_KEY)


def get_public_key() -> str:
    """Get agent's public key"""
    return get_keypair().public_key


def get_balance() -> dict:
    """Fetch agent wallet balances"""
    try:
        account = server.accounts().account_id(get_public_key()).call()
        balances = {
            b["asset_type"] if b["asset_type"] == "native"
            else b["asset_code"]: b["balance"]
            for b in account["balances"]
        }
        return balances
    except NotFoundError:
        raise Exception("Agent wallet not found — is it funded on testnet?")


def send_payment(
    destination: str,
    amount: str,
    asset_code: str = "XLM",
    asset_issuer: str = None
) -> str:
    """
    Send a payment and return the transaction hash.
    Used by x402_client to pay for API access.
    """
    keypair = get_keypair()
    account = server.load_account(keypair.public_key)

    # Asset type
    if asset_code == "XLM":
        asset = Asset.native()
    else:
        asset = Asset(asset_code, asset_issuer)

    transaction = (
        TransactionBuilder(
            source_account=account,
            network_passphrase=NETWORK_PASSPHRASE,
            base_fee=100
        )
        .append_payment_op(
            destination=destination,
            asset=asset,
            amount=amount
        )
        .set_timeout(30)
        .build()
    )

    transaction.sign(keypair)
    response = server.submit_transaction(transaction)

    return response["hash"]  # stellar transaction hash