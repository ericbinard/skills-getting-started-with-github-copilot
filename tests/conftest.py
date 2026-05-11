"""Shared test fixtures for the Activities API."""

import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src.app import app, activities


# Store the initial state of activities
INITIAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset in-memory activities to initial state before each test.
    
    This ensures test isolation—each test starts with identical, predictable state
    and no test can pollute another via shared in-memory state.
    """
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))
    yield


@pytest.fixture
def client():
    """Provide a TestClient for making HTTP requests to the FastAPI app."""
    return TestClient(app)
