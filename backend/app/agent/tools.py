from langchain.tools import tool
from app.agent.x402_client import X402Client, X402PaymentError
from app.services.transaction_service import log_transaction
from app.db.models import TransactionCreate
import httpx
import uuid


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

        # Log transaction to Supabase if payment was made
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
async def search_web(query: str) -> dict:
    """
    Search the web for URLs relevant to the user's query.
    Returns a list of URLs to fetch content from.
    Use this first to find sources before fetching them.
    """
    try:
        # Using DuckDuckGo — no API key needed
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1
                }
            )
            data = response.json()

            results = []

            # Related topics
            for topic in data.get("RelatedTopics", [])[:5]:
                if "FirstURL" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "url": topic["FirstURL"]
                    })

            return {
                "success": True,
                "results": results,
                "query": query
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


@tool
async def summarize_content(content: str, query: str) -> str:
    """
    Summarize raw content in the context of the user's original query.
    Use this after fetching content to extract the most relevant info.
    """
    # This gets called by LangChain — the LLM handles the actual summarization
    # We just clean up the content before passing it back
    if not content:
        return "No content to summarize."

    # Trim to avoid token overflow
    trimmed = content[:4000] if len(content) > 4000 else content

    return f"""
    Please summarize the following content in relation to the query: "{query}"

    Content:
    {trimmed}
    """

@tool
async def get_crypto_price(symbol: str) -> dict:
    """
    Get real-time cryptocurrency price.
    Use this for any crypto price questions.
    Symbol examples: BTC, ETH, SOL, XLM
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": symbol.lower().replace("btc", "bitcoin").replace("eth", "ethereum").replace("sol", "solana").replace("xlm", "stellar"),
                    "vs_currencies": "usd"
                }
            )
            data = response.json()
            return {
                "success": True,
                "symbol": symbol.upper(),
                "price_usd": list(data.values())[0]["usd"] if data else None
            }
    except Exception as e:
        return {"success": False, "error": str(e)}