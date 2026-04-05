from fastapi import APIRouter, HTTPException
from app.services.transaction_service import (
    get_transactions_by_task,
    get_all_transactions
)
from app.db.models import TransactionResponse

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=list[TransactionResponse])
async def list_all_transactions():
    """
    Fetch all transactions across all tasks.
    Used by the frontend live transaction feed.
    """
    try:
        return await get_all_transactions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=list[TransactionResponse])
async def list_transactions_by_task(task_id: str):
    """
    Fetch all transactions for a specific task.
    Used to show payment log per task.
    """
    try:
        return await get_transactions_by_task(task_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))