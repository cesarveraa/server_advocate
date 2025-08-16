# firebase_client.py
import os
import json
from functools import lru_cache
from typing import Dict, Any, Optional

from google.cloud import firestore
from google.oauth2.service_account import Credentials


def _build_sa_info_from_env() -> Dict[str, Any]:
    """
    Construye el dict de credenciales de servicio de Firebase a partir de .env.

    Soporta dos formas:
    1) FIREBASE_SERVICE_ACCOUNT_JSON = '{...}' (JSON completo)
    2) Variables por campo (FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, etc.)
    """
    # Opción A: JSON completo en una sola variable
    raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if raw_json:
        try:
            # Si viene con comillas escapadas, normalízalo
            if isinstance(raw_json, str) and raw_json.strip().startswith("{"):
                sa_info = json.loads(raw_json)
                return sa_info
        except Exception as e:
            raise ValueError(f"FIREBASE_SERVICE_ACCOUNT_JSON inválido: {e}")

    # Opción B: variables separadas
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    private_key_id = os.getenv("FIREBASE_PRIVATE_KEY_ID")
    private_key = os.getenv("FIREBASE_PRIVATE_KEY")
    client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
    client_id = os.getenv("FIREBASE_CLIENT_ID")
    universe_domain = os.getenv("FIREBASE_UNIVERSE_DOMAIN", "googleapis.com")

    # Validación mínima
    required = {
        "FIREBASE_PROJECT_ID": project_id,
        "FIREBASE_PRIVATE_KEY_ID": private_key_id,
        "FIREBASE_PRIVATE_KEY": private_key,
        "FIREBASE_CLIENT_EMAIL": client_email,
        "FIREBASE_CLIENT_ID": client_id,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise EnvironmentError(
            "Faltan variables de entorno para Firebase: " + ", ".join(missing) +
            ". Alternativamente, define FIREBASE_SERVICE_ACCOUNT_JSON."
        )

    # La private_key suele venir con \n escapados; los convertimos a saltos reales
    private_key = private_key.replace("\\n", "\n")

    # Endpoints OAuth por defecto (no suelen cambiar)
    auth_uri = os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
    token_uri = os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token")
    auth_provider_x509_cert_url = os.getenv(
        "FIREBASE_AUTH_PROVIDER_X509_CERT_URL",
        "https://www.googleapis.com/oauth2/v1/certs",
    )
    client_x509_cert_url = os.getenv("FIREBASE_CLIENT_X509_CERT_URL")

    sa_info = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": private_key_id,
        "private_key": private_key,
        "client_email": client_email,
        "client_id": client_id,
        "auth_uri": auth_uri,
        "token_uri": token_uri,
        "auth_provider_x509_cert_url": auth_provider_x509_cert_url,
        "client_x509_cert_url": client_x509_cert_url,
        "universe_domain": universe_domain,
    }
    return sa_info


@lru_cache()
def get_firestore_client() -> firestore.Client:
    """
    Crea el cliente de Firestore usando credenciales de servicio
    construidas desde variables de entorno.
    """
    sa_info = _build_sa_info_from_env()

    project_id = sa_info.get("project_id")
    if not project_id:
        raise KeyError("Las credenciales no incluyen 'project_id'.")

    creds = Credentials.from_service_account_info(sa_info)
    return firestore.Client(credentials=creds, project=project_id)
