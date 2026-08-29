"""
Point d'entree de l'application FastAPI.

Assemble la configuration, l'initialisation de la base de donnees, les
middlewares (CORS) et l'ensemble des routers metier.
"""

import logging
import logging.config
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import auth as auth_routes
from api.routes import chat as chat_routes
from api.routes import documents as documents_routes
from api.routes import emails as emails_routes
from api.routes import incidents as incidents_routes
from api.routes import projets as projets_routes
from api.routes import reunions as reunions_routes
from config.settings import settings
from core.llm.factory import get_llm_provider
from core.vector_store.factory import get_vector_store_provider
from models.database import init_db
from models.schemas import HealthCheckResponse

_LOGGING_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "logging.yaml"


def _configure_logging() -> None:
    """Charge la configuration de logging depuis config/logging.yaml, si presente."""
    if _LOGGING_CONFIG_PATH.exists():
        Path("./logs").mkdir(parents=True, exist_ok=True)
        with open(_LOGGING_CONFIG_PATH, "r", encoding="utf-8") as f:
            logging_config = yaml.safe_load(f)
        logging.config.dictConfig(logging_config)
    else:
        logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise les ressources au demarrage et les libere a l'arret de l'application."""
    _configure_logging()
    logger = logging.getLogger("api.main")

    logger.info("Demarrage de %s (env=%s)", settings.app_name, settings.app_env)
    init_db()

    logger.info("Provider LLM actif : %s", settings.llm_provider)
    logger.info("Provider vector store actif : %s", settings.vector_store_provider)

    yield

    logger.info("Arret de %s", settings.app_name)


app = FastAPI(
    title="AssIA - API",
    description=(
        "API de l'assistant interne base sur un pipeline RAG : chat, gestion de "
        "reunions, incidents, projets et emails."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------------
# Enregistrement des routers metier, tous prefixes par /api
# ----------------------------------------------------------------------

API_PREFIX = "/api"

app.include_router(auth_routes.router, prefix=API_PREFIX)
app.include_router(chat_routes.router, prefix=API_PREFIX)
app.include_router(documents_routes.router, prefix=API_PREFIX)
app.include_router(reunions_routes.router, prefix=API_PREFIX)
app.include_router(incidents_routes.router, prefix=API_PREFIX)
app.include_router(projets_routes.router, prefix=API_PREFIX)
app.include_router(emails_routes.router, prefix=API_PREFIX)


@app.get("/", tags=["Health"])
async def root() -> dict:
    """Endpoint racine simple, utile pour verifier que l'API repond."""
    return {"app": settings.app_name, "status": "running"}


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check() -> HealthCheckResponse:
    """Verifie l'etat de sante de l'application et de ses dependances (LLM, vector store)."""
    status_value = "ok"

    try:
        get_llm_provider()
    except Exception:
        status_value = "degraded"

    try:
        get_vector_store_provider()
    except Exception:
        status_value = "degraded"

    return HealthCheckResponse(
        status=status_value,
        llm_provider=settings.llm_provider,
        vector_store_provider=settings.vector_store_provider,
    )
