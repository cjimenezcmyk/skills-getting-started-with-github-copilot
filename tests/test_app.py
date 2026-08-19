from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def client():
    return TestClient(app)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activity = response.json()["Chess Club"]
    assert activity["description"]
    assert activity["schedule"]
    assert activity["max_participants"] == 12
    assert "michael@mergington.edu" in activity["participants"]


def test_signup_adds_participant(client):
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Chess Club"
    }
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Student is already signed up for this activity"
    )


def test_remove_participant(client):
    email = "michael@mergington.edu"

    response = client.delete(
        f"/activities/Chess Club/participants/{email}"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Removed {email} from Chess Club"
    }
    assert email not in activities["Chess Club"]["participants"]


def test_remove_participant_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/participants/student@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_rejects_unknown_participant(client):
    response = client.delete(
        "/activities/Chess Club/participants/unknown@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_removed_participant_can_sign_up_again(client):
    email = "michael@mergington.edu"

    remove_response = client.delete(
        f"/activities/Chess Club/participants/{email}"
    )
    signup_response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert remove_response.status_code == 200
    assert signup_response.status_code == 200
    assert email in activities["Chess Club"]["participants"]