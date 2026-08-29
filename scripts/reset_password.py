"""
Script utilitaire : remet à zéro le mot de passe d'un utilisateur Keycloak
via l'API Admin. A lancer depuis la racine du projet :
    PYTHONPATH=. .venv/bin/python scripts/reset_password.py <email> <nouveau_mdp>
"""
import asyncio
import sys
import httpx
from config.settings import settings
from api.auth import _get_admin_token


async def main(email: str, new_password: str) -> None:
    admin_token = await _get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    users_url = f"{settings.keycloak_server_url}/admin/realms/{settings.keycloak_realm}/users"

    async with httpx.AsyncClient() as client:
        # Chercher l'utilisateur par email
        resp = await client.get(f"{users_url}?email={email}&exact=true", headers=headers)
        users = resp.json()
        if not users:
            print(f"Aucun utilisateur trouve avec l'email : {email}")
            return

        user = users[0]
        user_id = user["id"]
        username = user.get("username")
        print(f"Utilisateur trouve : {username} ({email}) — ID: {user_id}")

        # Reset password
        pwd_resp = await client.put(
            f"{users_url}/{user_id}/reset-password",
            json={"type": "password", "value": new_password, "temporary": False},
            headers=headers,
        )
        if pwd_resp.status_code in (200, 204):
            print(f"Mot de passe mis a jour avec succes pour {email}.")
        else:
            print(f"Echec : {pwd_resp.status_code} {pwd_resp.text}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: PYTHONPATH=. .venv/bin/python scripts/reset_password.py <email> <nouveau_mdp>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
