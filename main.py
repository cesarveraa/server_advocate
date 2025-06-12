# main.py
from fastapi import FastAPI
from routers.lawyer_router import router as lawyers_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="API de Perfiles de Abogados",
    version="1.0.0",
    description="Guarda y sirve la configuración de cada abogado o firma"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # o ["*"] para todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lawyers_router)

@app.get("/")
async def root():
    return {"message": "Andea Legal API ✔️"}
