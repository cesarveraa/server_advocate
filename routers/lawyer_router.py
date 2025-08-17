# routers/lawyers.py
import os
from typing import List, Union, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from google.cloud.firestore import SERVER_TIMESTAMP

from firebase_client import get_firestore_client
from models.lawyer_model import LawyerProfile

IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "https://crea-tendencia-images.vercel.app")
IMAGES_PREFIX = os.getenv("IMAGES_PREFIX", "/images")

router = APIRouter(tags=["lawyers"])
COL = "lawyers"

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")

def require_internal_secret(request: Request):
    """
    Protege rutas de escritura con un secreto interno.
    Si INTERNAL_SECRET no está definido, NO bloquea (útil en dev).
    """
    if not INTERNAL_SECRET:
        return
    hdr = request.headers.get("x-internal-secret")
    if hdr != INTERNAL_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

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

# ------- body para upsert por code -------
class UpsertBody(BaseModel):
    data: Optional[dict] = None          # ← ahora opcional
    ownerUid: Optional[str] = None       # ← NUEVO
# ----------------------------------------

# (opcional) crear/actualizar completo por profile → PROTEGIDO
@router.post("/", response_model=LawyerProfile, dependencies=[Depends(require_internal_secret)])
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

# PUT por code para tu panel / link → PROTEGIDO
@router.put("/{code}", dependencies=[Depends(require_internal_secret)])
async def upsert_lawyer_data(code: str, body: UpsertBody):
    """
    Upsert por code con body:
      - { "ownerUid": "<uid>" }
      - { "data": { ... } }
      - o ambos
    """
    db = get_firestore_client()
    ref = db.collection(COL).document(code)
    snap = ref.get()
    current = snap.to_dict() or {}

    # Si intentan poner un owner distinto al ya existente → 409
    if body.ownerUid is not None and current.get("ownerUid") and current["ownerUid"] != body.ownerUid:
        raise HTTPException(status_code=409, detail="Esta página ya tiene dueño")

    to_set = {
        "code": code,
        "updated_at": SERVER_TIMESTAMP,
    }
    if body.data is not None:
        to_set["data"] = body.data
    if body.ownerUid is not None:
        to_set["ownerUid"] = body.ownerUid
    if not snap.exists:
        to_set["created_at"] = SERVER_TIMESTAMP

    ref.set(to_set, merge=True)

    # Devuelve el documento actualizado
    doc = ref.get()
    data = doc.to_dict() or {}
    replace_image_ids_with_urls(data)
    try:
        return LawyerProfile(**data)
    except Exception:
        return data

# (Opcional) POST /{code} para upsert con POST → PROTEGIDO
@router.post("/{code}", dependencies=[Depends(require_internal_secret)])
async def upsert_lawyer_data_post(code: str, body: UpsertBody):
    return await upsert_lawyer_data(code, body)
