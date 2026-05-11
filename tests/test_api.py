"""Backend API tests for the Activities platform.

All tests follow the Arrange-Act-Assert (AAA) pattern:
- Arrange: prepare test data and context
- Act: execute the action being tested
- Assert: validate the expected outcome
"""

import pytest
from src.app import activities


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirects_to_static_index_html(self, client):
        """GET / should redirect to /static/index.html."""
        # Arrange
        # (no setup needed)

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    """Tests for retrieving all available activities."""

    def test_get_activities_returns_all_activities(self, client):
        """GET /activities should return a dict of all activities with full details."""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        for activity_name in expected_activities:
            assert activity_name in data
            assert "description" in data[activity_name]
            assert "schedule" in data[activity_name]
            assert "max_participants" in data[activity_name]
            assert "participants" in data[activity_name]
            assert isinstance(data[activity_name]["participants"], list)

    def test_get_activities_response_structure_valid(self, client):
        """Response structure should be consistent across all activities."""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_details in data.items():
            assert set(activity_details.keys()) == required_fields
            assert isinstance(activity_details["max_participants"], int)
            assert isinstance(activity_details["participants"], list)


class TestSignupForActivity:
    """Tests for signing up a student for an activity."""

    def test_signup_valid_activity_valid_email(self, client):
        """POST /activities/{activity}/signup should add student to participants."""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_signup_invalid_activity_returns_404(self, client):
        """POST /activities/{invalid_activity}/signup should return 404."""
        # Arrange
        invalid_activity = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
        assert invalid_activity not in activities

    def test_signup_duplicate_email_returns_400(self, client):
        """POST /activities/{activity}/signup with already-signed-up email should return 400."""
        # Arrange
        activity_name = "Chess Club"
        existing_email = activities[activity_name]["participants"][0]

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_email}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_preserves_existing_participants(self, client):
        """Adding a new student should not affect existing participants."""
        # Arrange
        activity_name = "Programming Class"
        original_participants = activities[activity_name]["participants"].copy()
        new_email = "another@mergington.edu"

        # Act
        client.post(f"/activities/{activity_name}/signup?email={new_email}")

        # Assert
        for original_participant in original_participants:
            assert original_participant in activities[activity_name]["participants"]
        assert new_email in activities[activity_name]["participants"]

    def test_signup_multiple_different_students_same_activity(self, client):
        """Multiple different students should be able to sign up for the same activity."""
        # Arrange
        activity_name = "Gym Class"
        emails = ["student1@mergington.edu", "student2@mergington.edu"]

        # Act
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}"
            )
            assert response.status_code == 200

        # Assert
        for email in emails:
            assert email in activities[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for unregistering a student from an activity."""

    def test_unregister_valid_activity_valid_email(self, client):
        """DELETE /activities/{activity}/signup should remove student from participants."""
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = activities[activity_name]["participants"][0]

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email_to_remove}"
        )

        # Assert
        assert response.status_code == 200
        assert email_to_remove not in activities[activity_name]["participants"]
        data = response.json()
        assert "message" in data
        assert email_to_remove in data["message"]
        assert "Unregistered" in data["message"]

    def test_unregister_invalid_activity_returns_404(self, client):
        """DELETE /activities/{invalid_activity}/signup should return 404."""
        # Arrange
        invalid_activity = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_email_not_in_activity_returns_404(self, client):
        """DELETE with email not in activity should return 404."""
        # Arrange
        activity_name = "Chess Club"
        non_participant_email = "notinactivity@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={non_participant_email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Student not found" in data["detail"]

    def test_unregister_preserves_other_participants(self, client):
        """Removing one student should not affect other participants."""
        # Arrange
        activity_name = "Programming Class"
        email_to_remove = activities[activity_name]["participants"][0]
        other_participants = [
            p for p in activities[activity_name]["participants"]
            if p != email_to_remove
        ]

        # Act
        client.delete(
            f"/activities/{activity_name}/signup?email={email_to_remove}"
        )

        # Assert
        for other_participant in other_participants:
            assert other_participant in activities[activity_name]["participants"]
        assert email_to_remove not in activities[activity_name]["participants"]


class TestActivityNameCaseSensitivity:
    """Tests for case-sensitivity behavior in activity names."""

    def test_activity_name_is_case_sensitive(self, client):
        """Activity names should be treated as case-sensitive (exact match required)."""
        # Arrange
        valid_activity = "Chess Club"
        wrong_case_activity = "chess club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{wrong_case_activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert email not in activities[valid_activity]["participants"]


class TestDataIntegrity:
    """Tests to verify data integrity and invariants."""

    def test_participants_list_format_remains_list(self, client):
        """Participants should always remain a list, never become other type."""
        # Arrange
        activity_name = "Chess Club"
        email = "integrity@mergington.edu"

        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert isinstance(activities[activity_name]["participants"], list)

    def test_max_participants_unchanged_after_signup(self, client):
        """max_participants should not change after signup/unregister."""
        # Arrange
        activity_name = "Gym Class"
        original_max = activities[activity_name]["max_participants"]
        email = "student@mergington.edu"

        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert activities[activity_name]["max_participants"] == original_max

    def test_other_activities_unaffected_by_signup(self, client):
        """Signing up for one activity should not affect other activities."""
        # Arrange
        activity_1 = "Chess Club"
        activity_2 = "Programming Class"
        original_activity_2_participants = activities[activity_2]["participants"].copy()
        email = "student@mergington.edu"

        # Act
        client.post(f"/activities/{activity_1}/signup?email={email}")

        # Assert
        assert activities[activity_2]["participants"] == original_activity_2_participants
