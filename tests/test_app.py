"""Tests for the FastAPI application endpoints."""

import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_get_all_activities(self, client):
        """Test retrieving all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Basketball Team" in data
        assert "Chess Club" in data

    def test_activity_structure(self, client):
        """Test that activities have the correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_participants_are_strings(self, client):
        """Test that participant emails are strings."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            for participant in activity_details["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_successful_signup(self, client):
        """Test successfully signing up for an activity."""
        response = client.post(
            "/activities/Basketball Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Basketball Team" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity."""
        # Get initial participants count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Basketball Team"]["participants"])
        
        # Sign up
        client.post(
            "/activities/Basketball Team/signup?email=newstudent2@mergington.edu"
        )
        
        # Check that participant was added
        final_response = client.get("/activities")
        final_count = len(final_response.json()["Basketball Team"]["participants"])
        
        assert final_count == initial_count + 1
        assert "newstudent2@mergington.edu" in final_response.json()["Basketball Team"]["participants"]

    def test_signup_nonexistent_activity(self, client):
        """Test signing up for an activity that doesn't exist."""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_duplicate_signup(self, client):
        """Test signing up for an activity twice with the same email."""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response2.status_code == 400
        
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_multiple_activities(self, client):
        """Test signing up for multiple different activities."""
        email = "multiactivity@mergington.edu"
        
        # Sign up for two activities
        response1 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify both signups worked
        activities = client.get("/activities").json()
        assert email in activities["Basketball Team"]["participants"]
        assert email in activities["Chess Club"]["participants"]


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""

    def test_successful_unregister(self, client):
        """Test successfully unregistering from an activity."""
        email = "james@mergington.edu"  # Already registered in Basketball Team
        
        response = client.delete(
            f"/activities/Basketball Team/unregister?email={email}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant."""
        email = "james@mergington.edu"
        
        # Verify initially registered
        initial_response = client.get("/activities")
        assert email in initial_response.json()["Basketball Team"]["participants"]
        
        # Unregister
        client.delete(
            f"/activities/Basketball Team/unregister?email={email}"
        )
        
        # Verify unregistered
        final_response = client.get("/activities")
        assert email not in final_response.json()["Basketball Team"]["participants"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from an activity that doesn't exist."""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_registered(self, client):
        """Test unregistering someone who isn't registered."""
        response = client.delete(
            "/activities/Basketball Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_multiple_times(self, client):
        """Test that unregistering twice fails."""
        email = "alex@mergington.edu"  # Already registered in Basketball Team
        
        # First unregister should succeed
        response1 = client.delete(
            f"/activities/Basketball Team/unregister?email={email}"
        )
        assert response1.status_code == 200
        
        # Second unregister should fail
        response2 = client.delete(
            f"/activities/Basketball Team/unregister?email={email}"
        )
        assert response2.status_code == 400


class TestSignupAndUnregisterWorkflow:
    """Tests for signup and unregister workflows together."""

    def test_signup_then_unregister(self, client):
        """Test the workflow of signing up and then unregistering."""
        email = "workflow@mergington.edu"
        activity = "Basketball Team"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signed up
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]

    def test_signup_unregister_signup_again(self, client):
        """Test signing up, unregistering, and signing up again."""
        email = "reregister@mergington.edu"
        activity = "Tennis Club"
        
        # First signup
        response1 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response2.status_code == 200
        
        # Second signup (should succeed)
        response3 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response3.status_code == 200
        
        # Verify finally registered
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
