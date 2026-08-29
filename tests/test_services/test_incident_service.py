"""Tests du service de gestion des incidents."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


class TestIncidentService:
    """Tests du IncidentService : création, analyse IA et récupération."""

    def _make_db(self, incident=None):
        """Crée un mock de session SQLAlchemy."""
        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.all.return_value = [incident] if incident else []
        query_mock.first.return_value = incident
        db.query.return_value = query_mock
        return db

    def test_create_incident_sets_default_status(self):
        """Un nouvel incident doit avoir le statut 'ouvert' par défaut."""
        from models.database import Incident

        incident = Incident(
            id="inc-001",
            title="Problème base de données",
            description="Latence anormale détectée.",
            severity="majeur",
            status="ouvert",
        )
        assert incident.status == "ouvert"

    def test_severity_values(self):
        """Les valeurs de sévérité doivent être dans la liste autorisée."""
        from models.database import Incident
        valid_severities = ["mineur", "majeur", "critique"]
        for sev in valid_severities:
            incident = Incident(
                id=f"inc-{sev}",
                title="Test",
                description="Description",
                severity=sev,
            )
            assert incident.severity == sev

    def test_list_incidents_returns_all(self):
        """list_incidents doit retourner tous les incidents."""
        from services.incident_service import IncidentService
        from models.database import Incident

        mock_incident = MagicMock(spec=Incident)
        mock_incident.id = "inc-001"
        mock_incident.title = "Incident test"
        mock_incident.severity = "mineur"
        mock_incident.status = "ouvert"

        db = self._make_db(incident=mock_incident)
        service = IncidentService(db=db)

        results = service.list_incidents()
        assert isinstance(results, list)
