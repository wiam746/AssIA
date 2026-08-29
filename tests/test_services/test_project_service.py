"""Tests du service de gestion des projets (ProjetService)."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from services.projet_service import ProjetService
from models.database import Projet

@pytest.fixture
def mock_db():
    db = MagicMock()
    query_mock = MagicMock()
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    db.query.return_value = query_mock
    return db

@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.suggest_next_steps = AsyncMock(return_value="Suggestions d'étapes de test")
    return agent

@pytest.mark.asyncio
async def test_get_project_suggestions(mock_db, mock_agent):
    project = Projet(id="proj-1", name="Projet de test", description="Description de test", status="actif")
    
    # Configure mock_db to return our project when queried
    mock_db.query().filter().first.return_value = project
    
    service = ProjetService(db=mock_db, project_agent=mock_agent)
    suggestions = await service.suggest_next_steps("proj-1")
    
    assert suggestions == "Suggestions d'étapes de test"
    mock_agent.suggest_next_steps.assert_called_once_with(
        name="Projet de test",
        description="Description de test",
        status="actif"
    )
