"""
Orizon Portal Module

Serves the external user portal with:
- Signup/Login pages
- Profile management
- API key management
"""

from pathlib import Path

# Portal paths
PORTAL_DIR = Path(__file__).parent
TEMPLATES_DIR = PORTAL_DIR / "templates"
STATIC_DIR = PORTAL_DIR / "static"

__all__ = [
    "PORTAL_DIR",
    "TEMPLATES_DIR",
    "STATIC_DIR",
]
