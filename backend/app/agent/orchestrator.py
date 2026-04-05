from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from app.agent.tools import fetch_paywalled_content, search_web, summarize_content
from app.services.task_service import create_task, update_task_status
from app.services.transaction_service import get_transactions_by_task
from app.db.models import TaskCreate
from app.db.supabase import get_supabase
from app.config import get_settings

settings = get_settings()


# LLM
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=settings.OPENAI_API_KEY
)


# Tools
tools = [search_web, fetch_paywalled_content, summarize_content]


# System Prompt
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


# Agent
agent_executor = create_react_agent(
    model=llm,
    tools=tools,
    prompt=system_prompt
)


async def run_agent(user_input: str) -> dict:
    """
    Main entry point to run the agent.
    Creates a task, runs the agent, saves results, returns response.
    """
    supabase = get_supabase()

    # Create task in Supabase
    task = await create_task(TaskCreate(user_input=user_input))
    task_id = str(task.id)

    try:
        # Update status to running
        await update_task_status(task_id, "running")

        # Run the agent
        result = await agent_executor.ainvoke({
            "messages": [
                {
                    "role": "user",
                    "content": f"{user_input}\n\n[task_id: {task_id}]"
                }
            ]
        })

        final_answer = result["messages"][-1].content

        # Save result to Supabase
        transactions = await get_transactions_by_task(task_id)
        sources = [tx.api_url for tx in transactions]

        supabase.table("results").insert({
            "task_id": task_id,
            "summary": final_answer,
            "sources": sources
        }).execute()

        # Update status to completed
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