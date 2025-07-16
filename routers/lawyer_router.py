# routers/lawyers.py
import os
from fastapi import APIRouter, HTTPException
from typing import List
from firebase_client import get_firestore_client
from models.lawyer_model import LawyerProfile

# Apunta al dominio donde ya está tu servicio de imágenes
IMAGE_BASE_URL = os.getenv(
    "IMAGE_BASE_URL",
    "https://crea-tendencia-images.vercel.app"
)

router = APIRouter(tags=["lawyers"])
COL = "lawyers"


def replace_image_ids_with_urls(node: dict):
    for k, v in node.items():
        if isinstance(v, dict):
            replace_image_ids_with_urls(v)
        elif k.endswith("Image") and isinstance(v, str):
            # convierte el ID guardado en el payload a URL completa
            node[k] = f"{IMAGE_BASE_URL}/images/{v}"
    return node


@router.post("/", response_model=LawyerProfile)
async def create_or_update_lawyer(profile: LawyerProfile):
    db = get_firestore_client()
    db.collection(COL).document(profile.code).set(profile.dict())
    return profile


@router.get("/{code}", response_model=LawyerProfile)
async def get_lawyer(code: str):
    db = get_firestore_client()
    doc = db.collection(COL).document(code).get()
    if not doc.exists:
        raise HTTPException(404, "Perfil no encontrado")
    data = doc.to_dict()
    replace_image_ids_with_urls(data)
    return LawyerProfile(**data)


@router.get("/", response_model=List[LawyerProfile])
async def list_lawyers():
    db = get_firestore_client()
    out = []
    for snap in db.collection(COL).stream():
        d = snap.to_dict()
        replace_image_ids_with_urls(d)
        out.append(LawyerProfile(**d))
    return out
