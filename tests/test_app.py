import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_root_redirect():
    # Arrange
    path = "/"

    # Act
    resp = client.get(path, follow_redirects=False)

    # Assert
    assert resp.status_code in (301, 302, 307, 308)
    assert resp.headers.get("location") == "/static/index.html"


def test_get_activities():
    # Arrange
    path = "/activities"

    # Act
    resp = client.get(path)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_success():
    # Arrange
    activity = "Chess Club"
    email = "teststudent@example.com"
    path = f"/activities/{quote(activity)}/signup"

    # Act
    resp = client.post(path, params={"email": email})

    # Assert
    assert resp.status_code == 200
    assert email in activities[activity]["participants"]
    assert resp.json()["message"] == f"Signed up {email} for {activity}"


def test_signup_duplicate():
    # Arrange
    activity = "Chess Club"
    email = activities[activity]["participants"][0]
    path = f"/activities/{quote(activity)}/signup"

    # Act
    resp = client.post(path, params={"email": email})

    # Assert
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Student already signed up"


def test_signup_nonexistent_activity():
    # Act
    resp = client.post(f"/activities/{quote('NoSuchActivity')}/signup", params={"email": "x@y.com"})

    # Assert
    assert resp.status_code == 404


def test_remove_participant_success():
    # Arrange
    activity = "Chess Club"
    email = "remove.me@example.com"
    activities[activity]["participants"].append(email)
    path = f"/activities/{quote(activity)}/participants"

    # Act
    resp = client.delete(path, params={"email": email})

    # Assert
    assert resp.status_code == 200
    assert email not in activities[activity]["participants"]


def test_remove_participant_not_found():
    # Arrange
    activity = "Chess Club"
    path = f"/activities/{quote(activity)}/participants"

    # Act
    resp = client.delete(path, params={"email": "missing@example.com"})

    # Assert
    assert resp.status_code == 404
