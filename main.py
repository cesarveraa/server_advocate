# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 👇 importa AMBOS routers desde el archivo correcto
from routers.lawyers import router as lawyers_router, auth_router as lawyers_auth_router

ALLOWED_ORIGINS = [
    "https://advocate-sample-weld.vercel.app",
    "http://localhost:3000",
]

app = FastAPI(
    title="API de Perfiles de Abogados",
    version="1.0.0",
    description="Guarda y sirve la configuración de cada abogado o firma",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Rutas públicas → /lawyers/...
app.include_router(lawyers_router, prefix="/lawyers", tags=["lawyers"])

# Rutas autenticadas → /auth/...
# (el prefix="/auth" ya viene desde auth_router)
app.include_router(lawyers_auth_router)

@app.get("/")
async def root():

    return {"message": "Andea Legal API ✔️"}