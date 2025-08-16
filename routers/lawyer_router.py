# routers/lawyers.py
import os
from typing import List, Union, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.cloud.firestore import SERVER_TIMESTAMP

from firebase_client import get_firestore_client
from models.lawyer_model import LawyerProfile

IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "https://crea-tendencia-images.vercel.app")
IMAGES_PREFIX = os.getenv("IMAGES_PREFIX", "/images")

router = APIRouter(tags=["lawyers"])
COL = "lawyers"

# Solo estas claves se transforman a URL
IMAGE_KEYS = {"backgroundImage", "photo", "icon", "logo"}

def replace_image_ids_with_urls(node: Union[dict, list]):
    if isinstance(node, list):
        for item in node:
            if isinstance(item, (dict, list)):
                replace_image_ids_with_urls(item)
        return node

    if isinstance(node, dict):
        for k, v in list(node.items()):
            if isinstance(v, (dict, list)):
                replace_image_ids_with_urls(v)
            elif isinstance(v, str) and k in IMAGE_KEYS:
                # si ya es URL absoluta, no tocar
                if v.startswith(("http://", "https://", "data:", "blob:")):
                    continue
                # si parece un ID (sin slash), conviértelo
                if "/" not in v:
                    node[k] = f"{IMAGE_BASE_URL}{IMAGES_PREFIX}/{v}"
        return node

# ------- NUEVO: modelos para upsert por code -------
class UpsertBody(BaseModel):
    # En tu panel envías body: { "data": ContentData }
    data: dict
    # opcionalmente permite setear timestamps/otros
    # otros: Optional[dict] = None
# ---------------------------------------------------

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

# ------- NUEVO: PUT /{code} para tu panel de admin -------
@router.put("/{code}")
async def upsert_lawyer_data(code: str, body: UpsertBody):
    """
    Upsert por code con body { "data": { ... } }.
    No depende de LawyerProfile completo; útil para tu AdminPanel.
    """
    db = get_firestore_client()
    ref = db.collection(COL).document(code)
    snap = ref.get()

    to_set = {
        "code": code,
        "data": body.data,
        "updated_at": SERVER_TIMESTAMP,
    }
    if not snap.exists:
        to_set["created_at"] = SERVER_TIMESTAMP

    # merge=True evita pisar campos no incluidos
    ref.set(to_set, merge=True)

    # Devuelve el documento actualizado
    doc = ref.get()
    data = doc.to_dict() or {}
    replace_image_ids_with_urls(data)
    # Si LawyerProfile exige campos; si falta algo, devuelve raw:
    try:
        return LawyerProfile(**data)
    except Exception:
        return data
# ---------------------------------------------------------

# (Opcional) POST /{code} para evitar 405 si alguna vez usas POST
@router.post("/{code}")
async def upsert_lawyer_data_post(code: str, body: UpsertBody):
    return await upsert_lawyer_data(code, body)
