"""
Package de configuration de l'application.

Expose l'instance `settings`, unique source de verite pour toute
la configuration lue depuis le fichier .env.
"""

from config.settings import settings

__all__ = ["settings"]
