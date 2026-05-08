"""
Tests for the Mergington High School API.
All tests follow the Arrange-Act-Assert (AAA) pattern.
"""

import copy
import pytest
from fastapi.testclient import TestClient
import src.app as app_module
from src.app import app

INITIAL_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Competitive basketball league and practice",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 15,
        "participants": ["james@mergington.edu"],
    },
    "Tennis Club": {
        "description": "Tennis training and friendly matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
        "max_participants": 10,
        "participants": ["lucas@mergington.edu", "ava@mergington.edu"],
    },
    "Art Studio": {
        "description": "Painting, drawing, and visual art techniques",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 18,
        "participants": ["isabella@mergington.edu"],
    },
    "Music Band": {
        "description": "Learn instruments and perform in school concerts",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 25,
        "participants": ["noah@mergington.edu", "mia@mergington.edu"],
    },
    "Debate Club": {
        "description": "Develop argumentation and public speaking skills",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 16,
        "participants": ["alexander@mergington.edu"],
    },
    "Science Club": {
        "description": "Explore STEM topics through hands-on experiments",
        "schedule": "Mondays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["charlotte@mergington.edu", "benjamin@mergington.edu"],
    },
}


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its initial state after each test."""
    original = copy.deepcopy(INITIAL_ACTIVITIES)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_redirect_root(client):
    # Arrange — no setup needed, root endpoint requires no parameters

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all(client):
    # Arrange — activities are pre-loaded in the app

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 9


def test_get_activities_structure(client):
    # Arrange
    required_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    data = response.json()
    for name, details in data.items():
        assert required_fields.issubset(details.keys()), (
            f"Activity '{name}' is missing required fields"
        )


def test_get_activities_no_cache_headers(client):
    # Arrange — no parameters needed

    # Act
    response = client.get("/activities")

    # Assert
    cache_control = response.headers.get("cache-control", "")
    assert "no-store" in cache_control


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success(client):
    # Arrange
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email},
    )

    # Assert
    assert response.status_code == 200
    assert new_email in app_module.activities[activity_name]["participants"]


def test_signup_activity_not_found(client):
    # Arrange
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_email(client):
    # Arrange — michael is already in Chess Club (see INITIAL_ACTIVITIES)
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_max_participants(client):
    # Arrange — fill Tennis Club (max 10) up to the limit; it starts with 2 participants
    activity_name = "Tennis Club"
    for i in range(8):
        app_module.activities[activity_name]["participants"].append(
            f"filler{i}@mergington.edu"
        )

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "overflow@mergington.edu"},
    )

    # Assert — should be rejected once the limit is reached
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/participants/{email}
# ---------------------------------------------------------------------------

def test_unregister_success(client):
    # Arrange — michael is registered in Chess Club
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants/{email}"
    )

    # Assert
    assert response.status_code == 200
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_not_registered(client):
    # Arrange
    activity_name = "Chess Club"
    email = "nobody@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants/{email}"
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not registered for this activity"


def test_unregister_activity_not_found(client):
    # Arrange
    activity_name = "Ghost Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants/{email}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
