from fastapi import APIRouter, HTTPException
from app.agent.orchestrator import run_agent
from app.services.task_service import get_task, get_all_tasks
from app.db.models import TaskCreate, TaskResponse
from app.stellar.wallet import get_balance, get_public_key

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=dict)
async def create_task(task: TaskCreate):
    """
    Create and run a new agent task.
    This is the main endpoint the frontend calls.
    """
    try:
        result = await run_agent(task.user_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[TaskResponse])
async def list_tasks():
    """
    Fetch all tasks ordered by most recent.
    """
    try:
        return await get_all_tasks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_single_task(task_id: str):
    """
    Fetch a single task by ID.
    """
    try:
        return await get_task(task_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/wallet/info")
async def wallet_info():
    """
    Get agent wallet public key and balances.
    Useful for the frontend dashboard.
    """
    try:
        return {
            "public_key": get_public_key(),
            "balances": get_balance(),
            "network": "testnet"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))