# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.lawyer_router import router as lawyers_router
# main.py

ALLOWED_ORIGINS = [
    "https://advocate-sample-weld.vercel.app",  # tu frontend en prod
    "http://localhost:3000",                    # dev local
]
app = FastAPI(
    title="API de Perfiles de Abogados",
    version="1.0.0",
    description="Guarda y sirve la configuración de cada abogado o firma"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,    # NO "*"
    allow_credentials=True,           # sólo si usas cookies/autorización
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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
