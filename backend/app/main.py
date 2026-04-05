from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import tasks, transactions
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Nexus Pay — Agentic Bureau",
    description="An Economic Agent that pays for data using Stellar x402",
    version="1.0.0"
)

# --- CORS --- 
# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Routes ---
app.include_router(tasks.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "Nexus Pay",
        "status": "running",
        "network": settings.STELLAR_NETWORK
    }


@app.get("/health")
async def health():
    return {"status": "ok"}