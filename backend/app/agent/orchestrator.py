from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from app.agent.tools import fetch_paywalled_content, search_web, summarize_content, get_crypto_price
from app.services.task_service import create_task, update_task_status
from app.services.transaction_service import get_transactions_by_task
from app.db.models import TaskCreate
from app.db.supabase import get_supabase
from app.config import get_settings

settings = get_settings()


# --- System Prompt ---
system_prompt = """
You are an Economic Agent — an AI that can autonomously pay for data and services
using the Stellar blockchain via the x402 payment protocol.

Your job is to:
1. Understand the user's request
2. Search for relevant sources using search_web
3. Fetch content from those sources using fetch_paywalled_content
   - If a source requires payment (402), you will automatically pay using Stellar
   - Always pass the task_id when fetching content
4. Summarize the results using summarize_content
5. Return a clean, structured final answer with sources and payment info

Rules:
- Always search before fetching
- Never fetch more than 5 URLs per task (cost control)
- Always include stellar transaction hashes in your final answer if payments were made
- Be transparent about what you paid for and how much
- If a payment fails, skip that source and try the next one
"""

# --- Tools ---

tools = [search_web, fetch_paywalled_content, summarize_content, get_crypto_price]

def get_llm(use_fallback: bool = False):
    """
    Returns OpenAI by default.
    Falls back to Groq if use_fallback=True or no OpenAI key.
    """
    if use_fallback or not settings.OPENAI_API_KEY:
        if not settings.GROQ_API_KEY:
            raise Exception("No AI provider available. Set OPENAI_API_KEY or GROQ_API_KEY.")
        print(f"⚡ Using Groq fallback ({settings.GROQ_MODEL})")
        return ChatGroq(
            model=settings.GROQ_MODEL,
            temperature=0,
            api_key=settings.GROQ_API_KEY
        )

    print(f"⚡ Using OpenAI ({settings.OPENAI_MODEL})")
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    )


def build_agent(use_fallback: bool = False):
    """Build agent executor with the appropriate LLM."""
    llm = get_llm(use_fallback)
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt
    )


async def run_agent(user_input: str) -> dict:
    """
    Main entry point to run the agent.
    Tries OpenAI first, falls back to Groq on quota/auth errors.
    """
    supabase = get_supabase()

    # --- Create task in Supabase ---
    task = await create_task(TaskCreate(user_input=user_input))
    task_id = str(task.id)

    try:
        await update_task_status(task_id, "running")

        # --- Try OpenAI first ---
        try:
            agent_executor = build_agent(use_fallback=False)
            result = await agent_executor.ainvoke({
                "messages": [
                    {
                        "role": "user",
                        "content": f"{user_input}\n\n[task_id: {task_id}]"
                    }
                ]
            })

        except Exception as openai_err:
            err_str = str(openai_err).lower()

            # Check if it's a quota or auth error
            if any(keyword in err_str for keyword in [
                "insufficient_quota",
                "quota",
                "billing",
                "rate_limit",
                "authentication",
                "invalid_api_key"
            ]):
                print(f"⚠️ OpenAI failed ({openai_err}), switching to Groq...")
                agent_executor = build_agent(use_fallback=True)
                result = await agent_executor.ainvoke({
                    "messages": [
                        {
                            "role": "user",
                            "content": f"{user_input}\n\n[task_id: {task_id}]"
                        }
                    ]
                })
            else:
                # Not a quota error, re-raise
                raise openai_err

        final_answer = result["messages"][-1].content

        # --- Save result to Supabase ---
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
                    "stellar_hash": tx.stellar_hash
                }
                for tx in transactions
            ]
        }

    except Exception as e:
        await update_task_status(task_id, "failed")
        raise Exception(f"Agent run failed: {str(e)}")