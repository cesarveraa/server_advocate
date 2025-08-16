# routers/lawyers.py
import os
from fastapi import APIRouter, HTTPException
from typing import List, Union
from firebase_client import get_firestore_client
from models.lawyer_model import LawyerProfile

IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "https://crea-tendencia-images.vercel.app")
IMAGES_PREFIX = os.getenv("IMAGES_PREFIX", "/images")

router = APIRouter(tags=["lawyers"])
COL = "lawyers"

# 👇 Solo estas claves se transforman a URL
IMAGE_KEYS = {"backgroundImage", "photo", "icon", "logo"}

def replace_image_ids_with_urls(node: Union[dict, list]):
    if isinstance(node, list):
        for i, item in enumerate(node):
            if isinstance(item, (dict, list)):
                replace_image_ids_with_urls(item)
        return node

    if isinstance(node, dict):
        for k, v in list(node.items()):
            if isinstance(v, dict) or isinstance(v, list):
                replace_image_ids_with_urls(v)
            elif isinstance(v, str) and k in IMAGE_KEYS:
                # si ya es URL absoluta, no tocar
                if v.startswith(("http://", "https://", "data:", "blob:")):
                    continue
                # si parece un ID (sin slash), conviértelo
                if "/" not in v:
                    node[k] = f"{IMAGE_BASE_URL}{IMAGES_PREFIX}/{v}"
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
    replace_image_ids_with_urls(data)  # ✅ ahora no toca títulos/textos
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
