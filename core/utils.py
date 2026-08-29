"""Fonctions utilitaires transverses reutilisees dans plusieurs modules du projet."""

import hashlib
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from slugify import slugify


def generate_uuid() -> str:
    """Genere un identifiant unique (UUID4) sous forme de chaine."""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Retourne l'horodatage UTC courant, timezone-aware."""
    return datetime.now(timezone.utc)


def slugify_filename(filename: str) -> str:
    """
    Normalise un nom de fichier pour un stockage sur disque sans risque
    (accents, espaces, caracteres speciaux), en conservant l'extension.
    """
    path = Path(filename)
    stem = slugify(path.stem) or "fichier"
    suffix = path.suffix.lower()
    return f"{stem}{suffix}"


def unique_storage_filename(filename: str) -> str:
    """Genere un nom de fichier unique (prefixe UUID court) pour eviter les collisions."""
    safe_name = slugify_filename(filename)
    short_id = generate_uuid().split("-")[0]
    return f"{short_id}_{safe_name}"


def compute_file_hash(file_path: str | Path, algorithm: str = "sha256") -> str:
    """Calcule le hash d'un fichier (utile pour detecter les doublons a l'upload)."""
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            hasher.update(block)
    return hasher.hexdigest()


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Tronque un texte a une longueur maximale, en ajoutant un suffixe si tronque."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)].rstrip() + suffix


def normalize_whitespace(text: str) -> str:
    """Remplace toute sequence d'espaces/retours a la ligne par un seul espace."""
    return re.sub(r"\s+", " ", text).strip()


def clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Retire les cles dont la valeur est None (utile avant un update partiel en BDD)."""
    return {key: value for key, value in data.items() if value is not None}


def bytes_to_human_readable(size_bytes: int) -> str:
    """Convertit une taille en octets en une chaine lisible (Ko, Mo, Go...)."""
    size: float = float(size_bytes)
    for unit in ("o", "Ko", "Mo", "Go", "To"):
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} Po"


def parse_bool_env(value: Optional[str], default: bool = False) -> bool:
    """Parse une chaine issue d'une variable d'environnement en booleen."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
