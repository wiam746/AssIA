"""
Configuration partagée pour la suite de tests AssIA.

Fournit les fixtures pytest utilisées par l'ensemble des tests :
- Client HTTP de test FastAPI
- Session de base de données en mémoire isolée
- Utilisateur de test authentifié (token factice)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from models.database import Base, get_db, User

# -----------------------------------------------------------------------
# Base de données de test — SQLite en mémoire, isolation totale
# -----------------------------------------------------------------------

from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Remplace la dépendance get_db par une session de test en mémoire."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


@pytest.fixture(autouse=True)
def setup_test_database():
    """Crée les tables avant chaque test et les supprime après."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Fournit une session de base de données de test."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session):
    """Crée et retourne un utilisateur de test dans la base de données."""
    user = User(
        id="test-user-id-12345",
        email="test@example.com",
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def client(test_user):
    """
    Retourne un TestClient FastAPI avec :
    - La dépendance get_db surchargée vers la DB de test
    - L'authentification mockée pour retourner test_user
    """
    app.dependency_overrides[get_db] = override_get_db

    # Mocker l'authentification pour éviter Keycloak en tests
    from api.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: test_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
