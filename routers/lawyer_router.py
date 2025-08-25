# routers/lawyers.py
import os
from typing import List, Union, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from google.cloud.firestore import SERVER_TIMESTAMP
from firebase_admin import auth as fb_auth

from firebase_client import get_firestore_client
from models.lawyer_model import LawyerProfile

IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "https://crea-tendencia-images.vercel.app")
IMAGES_PREFIX = os.getenv("IMAGES_PREFIX", "/images")

# Router público (tuyo de siempre)
router = APIRouter(tags=["lawyers"])
# Router autenticado (para /auth/...)
auth_router = APIRouter(prefix="/auth", tags=["auth-lawyer"])

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

# ------- body para upsert por code (panel / link) -------
class UpsertBody(BaseModel):
    data: Optional[dict] = None          # ← opcional
    ownerUid: Optional[str] = None       # ← opcional (sólo en rutas internas)
# -------------------------------------------------------

# ========== PÚBLICO / ADMIN INTERNO (con INTERNAL_SECRET) ==========

# Crear/actualizar completo por profile → PROTEGIDO
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

# ========== AUTENTICADO (cookie idToken) ==========

from fastapi import Header

from fastapi import Header

def get_current_user(request: Request, authorization: str | None = Header(None)):
    # 1) cookie
    token = request.cookies.get("idToken")

    # 2) header (varias variantes, por si un proxy toca el casing)
    auth_header = authorization or request.headers.get("authorization") or request.headers.get("Authorization") or request.headers.get("x-authorization")
    if not token and auth_header:
        parts = auth_header.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()

    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized (missing token)")

    try:
        decoded = fb_auth.verify_id_token(token, clock_skew_seconds=60)
        return decoded
    except Exception as e:
        # registra para depurar si hiciera falta
        print("verify_id_token error:", repr(e))
        raise HTTPException(status_code=401, detail="Invalid token")



@auth_router.get("/me")
def me(user = Depends(get_current_user)):
    return {"uid": user["uid"], "email": user.get("email")}

@auth_router.get("/users/me/lawyer", response_model=LawyerProfile)
def get_my_lawyer(user = Depends(get_current_user)):
    db = get_firestore_client()
    q = db.collection(COL).where("ownerUid", "==", user["uid"]).limit(1).stream()
    doc = next(q, None)
    if not doc:
        # 404 de negocio (el router existe; sólo no hay página aún)
        raise HTTPException(status_code=404, detail="No tienes página aún")
    data = doc.to_dict() or {}
    replace_image_ids_with_urls(data)
    return LawyerProfile(**data)

@auth_router.put("/users/me/lawyer")
def upsert_my_lawyer(body: UpsertBody, user = Depends(get_current_user)):
    """
    Crea o actualiza la página del usuario autenticado.
    - Ignora body.ownerUid (si viene) y usa el UID del token.
    """
    db = get_firestore_client()
    existing = list(db.collection(COL).where("ownerUid", "==", user["uid"]).limit(1).stream())

    if existing:
        ref = db.collection(COL).document(existing[0].id)
        code = existing[0].id
    else:
        ref = db.collection(COL).document()
        code = ref.id

    to_set = {
        "code": code,
        "ownerUid": user["uid"],
        "ownerEmail": user.get("email"),
        "updated_at": SERVER_TIMESTAMP,
    }
    if body.data is not None:
        to_set["data"] = body.data

    snap = ref.get()
    if not snap.exists:
        to_set["created_at"] = SERVER_TIMESTAMP

    ref.set(to_set, merge=True)

    doc = ref.get()
    data = doc.to_dict() or {}
    replace_image_ids_with_urls(data)
    try:
        return LawyerProfile(**data)
    except Exception:
        return data

@auth_router.post("/users/me/lawyer/claim/{code}")
def claim_existing_page(code: str, user = Depends(get_current_user)):
    """
    Reclama una página existente.
    - Si no tiene owner, asigna el ownerUid actual.
    - Si ya tiene owner distinto, 409.
    """
    db = get_firestore_client()
    ref = db.collection(COL).document(code)
    snap = ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    current = snap.to_dict() or {}
    if current.get("ownerUid") and current["ownerUid"] != user["uid"]:
        raise HTTPException(status_code=409, detail="Esta página ya tiene dueño")

    ref.set({
        "ownerUid": user["uid"],
        "ownerEmail": user.get("email"),
        "updated_at": SERVER_TIMESTAMP,
    }, merge=True)

    data = ref.get().to_dict() or {}
    replace_image_ids_with_urls(data)
    try:
        return LawyerProfile(**data)
    except Exception:
        return data
