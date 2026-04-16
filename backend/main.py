from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.main import router as pm_router
from api.v1_router import router as v1_router

app = FastAPI(
    title="NJM OS API",
    description="Backend de orquestación multi-agente: Agente CEO y Agente PM",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pm_router)
app.include_router(v1_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "njm-os-backend"}
