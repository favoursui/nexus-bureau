import httpx
import uuid
from langchain.tools import tool
from langchain_tavily import TavilySearch
from app.agent.x402_client import X402Client, X402PaymentError
from app.services.transaction_service import log_transaction
from app.db.models import TransactionCreate
from app.config import get_settings

settings = get_settings()

# ===== TAVILY SEARCH CLIENT =====
tavily_search = TavilySearch(
    max_results=5,
    api_key=settings.TAVILY_API_KEY
)


@tool
async def search_web(query: str) -> dict:
    """
    Search the web for current, real-time information.
    Use this for any question about current events, news, prices,
    people in positions, or anything that may have changed recently.
    Always use this BEFORE answering any factual question.
    """
    try:
        results = await tavily_search.ainvoke(query)

        if not results:
            return {
                "success": False,
                "results": [],
                "query": query,
                "error": "No results found"
            }

        return {
            "success": True,
            "results": results,
            "query": query
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "query": query
        }


@tool
async def fetch_paywalled_content(url: str, task_id: str) -> dict:
    """
    Fetch content from a URL, automatically handling x402 paywalls.
    Logs any payments made to Supabase.
    Use this to access paywalled APIs or data sources.
    """
    client = X402Client()
    try:
        result = await client.fetch(url)

        if result["paid"]:
            await log_transaction(
                TransactionCreate(
                    task_id=uuid.UUID(task_id),
                    api_url=result["api_url"],
                    amount=float(result["amount"]),
                    currency=result["currency"],
                    stellar_hash=result["stellar_hash"]
                )
            )

        return {
            "success": True,
            "data": result["data"],
            "paid": result["paid"],
            "stellar_hash": result["stellar_hash"]
        }

    except X402PaymentError as e:
        return {
            "success": False,
            "error": f"Payment failed: {str(e)}",
            "paid": False,
            "stellar_hash": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}",
            "paid": False,
            "stellar_hash": None
        }
    finally:
        await client.close()


@tool
async def get_crypto_price(symbol: str) -> dict:
    """
    Get real-time cryptocurrency price.
    Use this for any crypto price questions.
    Symbol examples: BTC, ETH, SOL, XLM
    """
    try:
        symbol_map = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "sol": "solana",
            "xlm": "stellar",
            "usdc": "usd-coin"
        }
        coin_id = symbol_map.get(symbol.lower(), symbol.lower())

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": "usd",
                    "include_24hr_change": "true"
                }
            )
            data = response.json()

            if not data:
                return {"success": False, "error": "Price not found"}

            price_data = list(data.values())[0]
            return {
                "success": True,
                "symbol": symbol.upper(),
                "price_usd": price_data.get("usd"),
                "change_24h": price_data.get("usd_24h_change")
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
async def summarize_content(content: str, query: str) -> str:
    """
    Summarize raw content in the context of the user's original query.
    Use this after fetching content to extract the most relevant info.
    """
    if not content:
        return "No content to summarize."
    trimmed = content[:4000] if len(content) > 4000 else content
    return f"""
    Please summarize the following content in relation to the query: "{query}"
    Content:
    {trimmed}
    """

@tool
async def fetch_market_data(endpoint: str) -> dict:
    """
    Fetch data from Nexus Market API which requires x402 payment.
    Available endpoints:
    - price/BTC, price/ETH, price/XLM, price/SOL
    - news
    - weather/Lagos, weather/London, weather/NewYork
    - sentiment/BTC, sentiment/ETH

    This tool will automatically handle x402 payment using Stellar.
    Always use this for price, news, weather, and sentiment data.
    """
    client = X402Client()
    try:
        url = f"http://127.0.0.1:8000/api/market/{endpoint}"
        result = await client.fetch(url)

        return {
            "success": True,
            "data": result["data"],
            "paid": result["paid"],
            "amount": result["amount"],
            "currency": result["currency"],
            "stellar_hash": result["stellar_hash"]
        }

    except X402PaymentError as e:
        return {
            "success": False,
            "error": f"Payment failed: {str(e)}",
            "paid": False
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "paid": False
        }
    finally:
        await client.close()