"""
Orizon Portal Routes

Serves signup, login, and profile pages.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from . import TEMPLATES_DIR, STATIC_DIR

logger = logging.getLogger(__name__)

router = APIRouter(tags=["portal"])


def read_template(name: str) -> str:
    """Read an HTML template file."""
    template_path = TEMPLATES_DIR / name
    if template_path.exists():
        return template_path.read_text()
    raise FileNotFoundError(f"Template not found: {name}")


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Serve the signup page."""
    return HTMLResponse(content=read_template("signup.html"))


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page."""
    return HTMLResponse(content=read_template("login.html"))


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Serve the profile page."""
    return HTMLResponse(content=read_template("profile.html"))


def setup_static_files(app):
    """Mount static files directory."""
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
        logger.info(f"Mounted static files from {STATIC_DIR}")
    else:
        logger.warning(f"Static directory not found: {STATIC_DIR}")
