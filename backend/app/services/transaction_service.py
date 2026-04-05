from app.db.supabase import get_supabase
from app.db.models import TransactionCreate, TransactionResponse


async def log_transaction(transaction: TransactionCreate) -> TransactionResponse:
    """
    Log a completed x402 payment to Supabase.
    Called every time the agent makes a payment.
    """
    supabase = get_supabase()

    try:
        response = (
            supabase.table("transactions")
            .insert({
                "task_id": str(transaction.task_id),
                "api_url": transaction.api_url,
                "amount": transaction.amount,
                "currency": transaction.currency,
                "stellar_hash": transaction.stellar_hash
            })
            .execute()
        )

        data = response.data[0]
        return TransactionResponse(**data)

    except Exception as e:
        raise Exception(f"Failed to log transaction: {str(e)}")


async def get_transactions_by_task(task_id: str) -> list[TransactionResponse]:
    """
    Fetch all transactions for a specific task.
    Used by the frontend live log to show payment history.
    """
    supabase = get_supabase()

    try:
        response = (
            supabase.table("transactions")
            .select("*")
            .eq("task_id", task_id)
            .order("created_at", desc=False)
            .execute()
        )

        return [TransactionResponse(**tx) for tx in response.data]

    except Exception as e:
        raise Exception(f"Failed to fetch transactions: {str(e)}")


async def get_all_transactions() -> list[TransactionResponse]:
    """
    Fetch all transactions across all tasks.
    Used by the frontend dashboard.
    """
    supabase = get_supabase()

    try:
        response = (
            supabase.table("transactions")
            .select("*")
            .order("created_at", desc=False)
            .execute()
        )

        return [TransactionResponse(**tx) for tx in response.data]

    except Exception as e:
        raise Exception(f"Failed to fetch all transactions: {str(e)}")