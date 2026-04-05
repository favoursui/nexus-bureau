from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

# --- Task Models ---
class TaskCreate(BaseModel):
    user_input: str

class TaskResponse(BaseModel):
    id: UUID4
    user_input: str
    status: str  # "pending" | "running" | "completed" | "failed"
    created_at: datetime

# --- Transaction Models ---
class TransactionCreate(BaseModel):
    task_id: UUID4
    api_url: str
    amount: float
    currency: str = "USDC"
    stellar_hash: str

class TransactionResponse(BaseModel):
    id: UUID4
    task_id: UUID4
    api_url: str
    amount: float
    currency: str
    stellar_hash: str
    created_at: datetime

# --- Result Models ---
class ResultCreate(BaseModel):
    task_id: UUID4
    summary: str
    sources: list[str]

class ResultResponse(BaseModel):
    id: UUID4
    task_id: UUID4
    summary: str
    sources: list[str]
    created_at: datetime