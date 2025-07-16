# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.lawyer_router import router as lawyers_router

app = FastAPI(
    title="API de Perfiles de Abogados",
    version="1.0.0",
    description="Guarda y sirve la configuración de cada abogado o firma"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    lawyers_router,
    prefix="/lawyers",
    tags=["lawyers"],
)

@app.get("/")
async def root():
    return {"message": "Andea Legal API ✔️"}
