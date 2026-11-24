"""Shared pytest fixtures."""

import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def _no_api_key_by_default():
    """Run tests with RAG_API_KEY unset, even if it is set in .env.

    Tests that need a key (tests/test_auth.py) set settings.API_KEY themselves.
    """
    original = settings.API_KEY
    settings.API_KEY = None
    yield
    settings.API_KEY = original
