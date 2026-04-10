from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from app.agent.tools import fetch_paywalled_content, search_web, summarize_content, get_crypto_price, fetch_market_data
from app.services.task_service import create_task, update_task_status
from app.services.transaction_service import get_transactions_by_task
from app.db.models import TaskCreate
from app.db.supabase import get_supabase
from app.config import get_settings

settings = get_settings()


# --- System Prompt ---

system_prompt = f"""
You are an Economic Agent — an AI that can autonomously pay for data and services
using the Stellar blockchain via the x402 payment protocol.

Today's date is {datetime.now().strftime("%B %d, %Y")}.

You have access to a Nexus Market API that requires x402 micro-payments:
- fetch_market_data("price/BTC") → get Bitcoin price (costs 0.01 XLM)
- fetch_market_data("price/ETH") → get Ethereum price (costs 0.01 XLM)
- fetch_market_data("price/XLM") → get Stellar price (costs 0.01 XLM)
- fetch_market_data("price/SOL") → get Solana price (costs 0.01 XLM)
- fetch_market_data("news") → get latest crypto news (costs 0.02 XLM)
- fetch_market_data("weather/Lagos") → get weather data (costs 0.01 XLM)
- fetch_market_data("sentiment/BTC") → get market sentiment (costs 0.05 XLM)

STRICT RULES:
- For price, news, weather, sentiment → ALWAYS use fetch_market_data first
- For other current events → use search_web first
- NEVER answer from memory for current data
- Always show payment details and Stellar transaction hash in your answer
- Always include how much was paid and for what
"""

# --- Tools ---

tools = [search_web, fetch_paywalled_content, summarize_content, get_crypto_price, fetch_market_data]

def get_llm(fallback_index: int = 0):
    """
    Returns LLM based on fallback index.
    Tries each provider in order until one works.
    """
    providers = []

    # Build provider chain from .env
    if settings.OPENAI_API_KEY:
        providers.append({
            "name": "OpenAI",
            "model": settings.OPENAI_MODEL,
            "llm": ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0,
                api_key=settings.OPENAI_API_KEY
            )
        })

    if settings.GROQ_API_KEY:
        providers.append({
            "name": "Groq",
            "model": settings.GROQ_MODEL,
            "llm": ChatGroq(
                model=settings.GROQ_MODEL,
                temperature=0,
                api_key=settings.GROQ_API_KEY
            )
        })

    if settings.GROQ_API_KEY and settings.GROQ_MODEL_2:
        providers.append({
            "name": "Groq (model 2)",
            "model": settings.GROQ_MODEL_2,
            "llm": ChatGroq(
                model=settings.GROQ_MODEL_2,
                temperature=0,
                api_key=settings.GROQ_API_KEY
            )
        })

    if settings.TOGETHER_API_KEY:
        from langchain_together import ChatTogether
        providers.append({
            "name": "Together AI",
            "model": settings.TOGETHER_MODEL,
            "llm": ChatTogether(
                model=settings.TOGETHER_MODEL,
                temperature=0,
                api_key=settings.TOGETHER_API_KEY
            )
        })

    if not providers:
        raise Exception("No AI provider configured. Set at least one API key in .env")

    if fallback_index >= len(providers):
        raise Exception("All AI providers exhausted. Please check your API keys and quotas.")

    p = providers[fallback_index]
    print(f"⚡ Using {p['name']} ({p['model']})")
    return p["llm"], fallback_index


def build_agent(use_fallback: bool = False):
    """Build agent executor with the appropriate LLM."""
    llm = get_llm(use_fallback)
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt
    )


async def run_agent(user_input: str) -> dict:
    supabase = get_supabase()
    task = await create_task(TaskCreate(user_input=user_input))
    task_id = str(task.id)

    FALLBACK_KEYWORDS = [
    "insufficient_quota", "quota", "billing",
    "rate_limit", "rate limit", "authentication",
    "invalid_api_key", "decommissioned", "deprecated",
    "overloaded", "capacity", "tool_use_failed",
    "failed_generation", "failed to call a function"
]

    try:
        await update_task_status(task_id, "running")

        fallback_index = 0
        result = None

        while result is None:
            try:
                llm, fallback_index = get_llm(fallback_index)
                agent_executor = create_react_agent(
                    model=llm,
                    tools=tools,
                    prompt=system_prompt
                )
                result = await agent_executor.ainvoke({
                    "messages": [
                        {
                            "role": "user",
                            "content": f"{user_input}\n\n[task_id: {task_id}]"
                        }
                    ]
                })

            except Exception as e:
                err = str(e).lower()
                if "all ai providers exhausted" in err:
                    raise Exception("All AI providers exhausted. Please wait and try again.")
                if any(k in err for k in FALLBACK_KEYWORDS):
                    print(f"⚠️ Provider failed: {e}. Trying next...")
                    fallback_index += 1
                else:
                    raise e

        final_answer = result["messages"][-1].content

        transactions = await get_transactions_by_task(task_id)
        sources = [tx.api_url for tx in transactions]

        supabase.table("results").insert({
            "task_id": task_id,
            "summary": final_answer,
            "sources": sources
        }).execute()

        await update_task_status(task_id, "completed")

        return {
            "task_id": task_id,
            "status": "completed",
            "answer": final_answer,
            "transactions": [
                {
                    "api_url": tx.api_url,
                    "amount": tx.amount,
                    "currency": tx.currency,
                    "stellar_hash": tx.stellar_hash,
                    "explorer_url": f"https://stellar.expert/explorer/testnet/tx/{tx.stellar_hash}"
                }
                for tx in transactions
            ]
        }
    
    except Exception as e:
        await update_task_status(task_id, "failed")
        raise Exception(f"Agent run failed: {str(e)}")