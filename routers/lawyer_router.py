# routers/lawyers.py
from fastapi import APIRouter, HTTPException
from typing import List
from firebase_client import get_firestore_client
from models.lawyer_model import LawyerProfile

router = APIRouter(prefix="/lawyers", tags=["lawyers"])
COL = "lawyers"

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
    return LawyerProfile(**doc.to_dict())

@router.get("/", response_model=List[LawyerProfile])
async def list_lawyers():
    db = get_firestore_client()
    return [LawyerProfile(**d.to_dict()) for d in db.collection(COL).stream()]
