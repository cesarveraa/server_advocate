# firebase_client.py

import os
import json
from functools import lru_cache

from google.cloud import firestore
from google.oauth2.service_account import Credentials

@lru_cache()
def get_firestore_client() -> firestore.Client:
    # 1) Determina la ruta del JSON de credenciales
    cred_path = os.getenv("FIREBASE_CREDENTIALS_FILE", "serviceAccountKey.json")
    if not os.path.isfile(cred_path):
        raise FileNotFoundError(
            f"No se encontró el archivo de credenciales de Firebase en: {cred_path}"
        )

    # 2) Carga el JSON
    with open(cred_path, "r", encoding="utf-8") as f:
        sa_info = json.load(f)

    # 3) Crea un objeto Credentials a partir del JSON
    creds = Credentials.from_service_account_info(sa_info)

    # 4) Inicializa el cliente de Firestore indicando las credenciales y el project_id
    project_id = sa_info.get("project_id")
    if not project_id:
        raise KeyError("El JSON de credenciales no contiene 'project_id'")

    return firestore.Client(credentials=creds, project=project_id)
