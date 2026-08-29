"""Tests du service de gestion des réunions (ReunionService)."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from services.reunion_service import ReunionService
from models.database import Reunion
from agents.meeting_agent import MeetingAnalysis

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
    analysis = MeetingAnalysis(
        objet="Synchro Hebdo",
        summary="Résumé de la réunion",
        decisions="Décision A, Décision B",
        actions="Action 1 pour Alice, Action 2 pour Bob",
        prochaine_reunion="Mardi 10h"
    )
    agent.process_meeting = AsyncMock(return_value=analysis)
    return agent

@pytest.mark.asyncio
async def test_create_reunion(mock_db, mock_agent):
    service = ReunionService(db=mock_db, meeting_agent=mock_agent)
    
    reunion = await service.create_reunion(
        title="Synchro Hebdo",
        raw_content="Notes de réunion...",
        participants="Alice, Bob",
        created_by="user-1"
    )
    
    assert reunion is not None
    assert reunion.title == "Synchro Hebdo"
    assert reunion.summary == "Résumé de la réunion"
    assert reunion.decisions == "Décision A, Décision B"
    assert reunion.actions == "Action 1 pour Alice, Action 2 pour Bob"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
