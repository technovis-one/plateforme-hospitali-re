"""Intégration serveur Daily : aucune clé ni donnée médicale dans le navigateur."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)


class DailyServiceError(Exception):
    """Erreur Daily non sensible, sûre à afficher à l’utilisateur."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def daily_is_configured() -> bool:
    return bool(os.environ.get("DAILY_API_KEY", "").strip())


def _api_request(method: str, path: str, payload: dict | None = None) -> dict | None:
    api_key = os.environ.get("DAILY_API_KEY", "").strip()
    if not api_key:
        raise DailyServiceError("Le service d’appel n’est pas encore configuré.")

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"https://api.daily.co/v1{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=12) as response:
            raw = response.read(1_000_000)
    except HTTPError as exc:
        # Lire uniquement le code d'erreur documenté; ne jamais journaliser la clé ou le corps brut.
        if exc.code == 404 and method == "GET":
            return None
        try:
            error_body = json.loads(exc.read(4096).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, OSError):
            error_body = {}
        raw_code = error_body.get("error", "") if isinstance(error_body, dict) else ""
        error_code = raw_code if isinstance(raw_code, str) and re.fullmatch(r"[a-z0-9-]{1,64}", raw_code) else "unknown"
        raw_info = error_body.get("info", "") if isinstance(error_body, dict) else ""
        allowed_fields = (
            "max_participants",
            "enable_shared_chat_history",
            "enable_chat",
            "eject_at_room_exp",
            "start_video_off",
            "start_audio_off",
            "enable_screenshare",
            "enable_prejoin_ui",
            "enable_recording_ui",
            "room_name",
            "user_name",
            "user_id",
            "exp",
            "nbf",
        )
        error_field = "unknown"
        if isinstance(raw_info, str):
            info_lower = raw_info.lower()
            error_field = next((field for field in allowed_fields if field in info_lower), "unknown")
        if method == "GET" and path.startswith("/rooms/"):
            operation = "lecture-salle"
        else:
            operation = {
                ("POST", "/rooms"): "creation-salle",
                ("POST", "/meeting-tokens"): "creation-jeton",
            }.get((method, path), "requete-api")
        logger.warning(
            "Daily API refused request: status=%s operation=%s error=%s",
            exc.code,
            operation,
            error_code,
            extra={"field": error_field},
        )
        messages = {
            400: "Daily a refusé les paramètres de la demande (HTTP 400). Vérifie le code Daily indiqué dans le terminal du serveur; cela peut venir d’une option ou d’une limite non acceptée par le compte.",
            401: "Daily a rejeté l’authentification (HTTP 401). Vérifie que DAILY_API_KEY est la clé API du domaine Daily et que le serveur a été relancé dans la même fenêtre PowerShell.",
            403: "La clé Daily est reconnue, mais le compte ne permet pas cette opération ou cette option (HTTP 403). Vérifie le domaine et les fonctions accessibles dans le compte Daily.",
            429: "Daily limite temporairement les demandes (HTTP 429). Attends quelques instants avant de réessayer.",
        }
        message = messages.get(
            exc.code,
            f"Daily n’a pas pu traiter la demande (HTTP {exc.code}). Vérifie le code d’erreur non sensible affiché dans le terminal du serveur.",
        )
        raise DailyServiceError(
            message,
            status=exc.code,
        ) from None
    except (URLError, TimeoutError, OSError):
        raise DailyServiceError(
            "Le service d’appel est momentanément injoignable. Réessaie dans quelques instants."
        ) from None

    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise DailyServiceError("Le service d’appel a renvoyé une réponse invalide.") from None
    if not isinstance(result, dict):
        raise DailyServiceError("Le service d’appel a renvoyé une réponse invalide.")
    return result


def _room_name(appointment) -> str:
    secret = str(settings.SECRET_KEY).encode("utf-8")
    schedule = f"{appointment.date.isoformat()}T{appointment.heure.isoformat()}"
    digest = hmac.new(secret, f"novahospito:rdv:{appointment.pk}:{schedule}".encode(), hashlib.sha256).hexdigest()[:32]
    return f"nh-rdv-{digest}"


def _validate_room(room: dict | None) -> str:
    if not room or room.get("privacy") != "private":
        raise DailyServiceError("La salle de téléconsultation n’est pas disponible en mode privé.")
    url = room.get("url")
    config = room.get("config") or {}
    if not isinstance(url, str) or not url.startswith("https://"):
        raise DailyServiceError("La configuration de la salle de téléconsultation est invalide.")
    if config.get("enable_chat") is not True:
        raise DailyServiceError("La messagerie de cette salle n’est pas activée.")
    if config.get("max_participants") != 2:
        raise DailyServiceError("La salle Daily n’a pas confirmé la limite de deux participants. Vérifie le forfait et la configuration du compte.")
    return url


def create_meeting_access(appointment, role: str, starts_at, ends_at) -> tuple[str, str]:
    """Réutilise une salle privée opaque et crée un jeton limité à cette salle et à ce rendez-vous."""
    if role not in {"patient", "medecin"}:
        raise DailyServiceError("Ce profil n’est pas autorisé à rejoindre la téléconsultation.")

    room_name = _room_name(appointment)
    room_path = f"/rooms/{quote(room_name, safe='')}"
    room = _api_request("GET", room_path)
    if room is None:
        room_payload = {
            "name": room_name,
            "privacy": "private",
            "properties": {
                "nbf": int(starts_at.timestamp()),
                "exp": int(ends_at.timestamp()),
                "eject_at_room_exp": True,
                "max_participants": 2,
                "enable_chat": True,
                "enable_shared_chat_history": False,
                "start_video_off": True,
                "start_audio_off": True,
                "enable_screenshare": False,
            },
        }
        try:
            room = _api_request("POST", "/rooms", room_payload)
        except DailyServiceError as exc:
            # Une seconde connexion peut avoir créé la même salle après notre GET.
            if exc.status not in {400, 409}:
                raise
            existing_room = _api_request("GET", room_path)
            if existing_room is None:
                raise
            room = existing_room
    room_url = _validate_room(room)

    user_label = "Médecin" if role == "medecin" else "Patient"
    token_payload = {
        "properties": {
            "room_name": room_name,
            "user_name": user_label,
            "user_id": str(uuid.uuid4()),
            "exp": int(ends_at.timestamp()),
            "eject_at_token_exp": True,
            "is_owner": role == "medecin",
            "start_video_off": True,
            "start_audio_off": True,
            "enable_screenshare": False,
            "enable_prejoin_ui": True,
            "enable_recording_ui": False,
        }
    }
    token_result = _api_request("POST", "/meeting-tokens", token_payload)
    token = (token_result or {}).get("token")
    if not isinstance(token, str) or not token:
        raise DailyServiceError("Le service d’appel n’a pas délivré de jeton valide.")
    return room_url, token
