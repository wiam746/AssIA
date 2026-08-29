"""Tests du service de gestion des emails (EmailService)."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from services.email_service import EmailService
from models.database import EmailDraft

@pytest.fixture
def mock_db():
    db = MagicMock()
    # Mocking standard query results
    query_mock = MagicMock()
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.all.return_value = []
    query_mock.first.return_value = None
    db.query.return_value = query_mock
    return db

@pytest.fixture
def mock_agent():
    agent = MagicMock()
    # Simulate async call returning (subject, body) tuple
    agent.draft_email = AsyncMock(return_value=("Sujet test", "Contenu test"))
    agent.analyze_email = AsyncMock(return_value="Analyse test")
    return agent

@pytest.mark.asyncio
async def test_draft_email(mock_db, mock_agent):
    service = EmailService(db=mock_db, email_agent=mock_agent)
    
    draft = await service.draft_email(
        instructions="Rédiger un email de bienvenue",
        tone="professionnel",
        created_by="user-1"
    )
    
    assert draft is not None
    assert draft.subject == "Sujet test"
    assert draft.body == "Contenu test"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
