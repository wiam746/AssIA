"""Tests des routes Chat — messages et conversations."""

from unittest.mock import AsyncMock, MagicMock, patch


def test_list_conversations_empty(client):
    """GET /api/chat/conversations retourne une liste vide pour un nouvel utilisateur."""
    response = client.get("/api/chat/conversations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_send_message_creates_conversation(client):
    """POST /api/chat/messages crée une conversation et retourne la réponse de l'assistant."""
    mock_answer = MagicMock()
    mock_answer.content = "Voici une réponse de test de l'assistant."
    mock_answer.sources = ["[Source: doc1] Contenu pertinent."]

    with patch(
        "api.routes.chat._chat_agent.answer",
        new_callable=AsyncMock,
        return_value=mock_answer,
    ):
        response = client.post(
            "/api/chat/messages",
            json={
                "message": "Quelles sont les décisions de la dernière réunion ?",
                "conversation_id": None,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "message" in data
    assert data["message"]["role"] == "assistant"
    assert data["message"]["content"] == "Voici une réponse de test de l'assistant."
    assert "sources" in data


def test_send_message_continues_conversation(client):
    """POST /api/chat/messages continue une conversation existante."""
    mock_answer = MagicMock()
    mock_answer.content = "Réponse de l'assistant."
    mock_answer.sources = []

    with patch(
        "api.routes.chat._chat_agent.answer",
        new_callable=AsyncMock,
        return_value=mock_answer,
    ):
        # Créer une conversation initiale
        r1 = client.post(
            "/api/chat/messages",
            json={"message": "Première question", "conversation_id": None},
        )
        conversation_id = r1.json()["conversation_id"]

        # Continuer la même conversation
        r2 = client.post(
            "/api/chat/messages",
            json={"message": "Deuxième question", "conversation_id": conversation_id},
        )

    assert r2.status_code == 200
    assert r2.json()["conversation_id"] == conversation_id


def test_get_conversation_detail(client):
    """GET /api/chat/conversations/{id} retourne la conversation avec ses messages."""
    mock_answer = MagicMock()
    mock_answer.content = "Réponse test"
    mock_answer.sources = []

    with patch(
        "api.routes.chat._chat_agent.answer",
        new_callable=AsyncMock,
        return_value=mock_answer,
    ):
        r = client.post(
            "/api/chat/messages",
            json={"message": "Test message", "conversation_id": None},
        )
        conv_id = r.json()["conversation_id"]

    response = client.get(f"/api/chat/conversations/{conv_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conv_id
    assert "messages" in data
    assert len(data["messages"]) >= 1


def test_delete_conversation(client):
    """DELETE /api/chat/conversations/{id} supprime la conversation."""
    mock_answer = MagicMock()
    mock_answer.content = "Réponse"
    mock_answer.sources = []

    with patch(
        "api.routes.chat._chat_agent.answer",
        new_callable=AsyncMock,
        return_value=mock_answer,
    ):
        r = client.post(
            "/api/chat/messages",
            json={"message": "Test", "conversation_id": None},
        )
        conv_id = r.json()["conversation_id"]

    delete_response = client.delete(f"/api/chat/conversations/{conv_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/chat/conversations/{conv_id}")
    assert get_response.status_code == 404


def test_get_nonexistent_conversation(client):
    """GET /api/chat/conversations/{id} retourne 404 pour un ID inexistant."""
    response = client.get("/api/chat/conversations/nonexistent-id-000")
    assert response.status_code == 404
