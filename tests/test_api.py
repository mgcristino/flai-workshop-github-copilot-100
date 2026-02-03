"""
Tests for the High School Management System API
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the activities database before each test"""
    # Store the original state
    original_participants = {
        "Soccer Team": ["alex@mergington.edu", "ryan@mergington.edu"],
        "Basketball Club": ["sarah@mergington.edu", "james@mergington.edu"],
        "Drama Club": ["emily@mergington.edu", "lucas@mergington.edu"],
        "Art Studio": ["lily@mergington.edu", "noah@mergington.edu"],
        "Science Olympiad": ["ava@mergington.edu", "ethan@mergington.edu"],
        "Debate Team": ["isabella@mergington.edu", "mason@mergington.edu"],
        "Chess Club": ["michael@mergington.edu", "daniel@mergington.edu"],
        "Programming Class": ["emma@mergington.edu", "sophia@mergington.edu"],
        "Gym Class": ["john@mergington.edu", "olivia@mergington.edu"]
    }
    
    # Reset to original state before each test
    for activity_name, participants in original_participants.items():
        if activity_name in activities:
            activities[activity_name]["participants"] = participants.copy()
    
    yield
    
    # Clean up after each test
    for activity_name, participants in original_participants.items():
        if activity_name in activities:
            activities[activity_name]["participants"] = participants.copy()


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that the root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify we have the expected activities
        assert "Soccer Team" in data
        assert "Basketball Club" in data
        assert "Drama Club" in data
        assert "Art Studio" in data
        assert "Science Olympiad" in data
        assert "Debate Team" in data
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_structure(self, client):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Check one activity for proper structure
        soccer = data["Soccer Team"]
        assert "description" in soccer
        assert "schedule" in soccer
        assert "max_participants" in soccer
        assert "participants" in soccer
        assert isinstance(soccer["participants"], list)


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_existing_activity(self, client):
        """Test successful signup for an existing activity"""
        email = "newstudent@mergington.edu"
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Soccer Team" in data["message"]
        
        # Verify the student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Soccer Team"]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_duplicate_signup(self, client):
        """Test that signing up twice for the same activity returns 400"""
        email = "alex@mergington.edu"  # Already in Soccer Team
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_multiple_students_can_signup(self, client):
        """Test that multiple students can sign up for the same activity"""
        students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in students:
            response = client.post(
                "/activities/Chess Club/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all students were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        for email in students:
            assert email in activities_data["Chess Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_from_activity(self, client):
        """Test successful unregistration from an activity"""
        email = "alex@mergington.edu"  # Already in Soccer Team
        response = client.delete(
            "/activities/Soccer Team/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Soccer Team" in data["message"]
        
        # Verify the student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Soccer Team"]["participants"]
    
    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregister from a non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_when_not_signed_up(self, client):
        """Test unregistering when not signed up returns 400"""
        email = "notsignedup@mergington.edu"
        response = client.delete(
            "/activities/Soccer Team/unregister",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_signup_and_unregister_workflow(self, client):
        """Test the complete workflow of signing up and unregistering"""
        email = "workflow@mergington.edu"
        activity = "Drama Club"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signed up
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""
    
    def test_activity_name_with_spaces(self, client):
        """Test that activity names with spaces work correctly"""
        email = "newstudent@mergington.edu"
        response = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    def test_multiple_operations_on_different_activities(self, client):
        """Test that operations on different activities don't interfere"""
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Sign up for different activities
        response1 = client.post(
            "/activities/Soccer Team/signup",
            params={"email": email1}
        )
        response2 = client.post(
            "/activities/Basketball Club/signup",
            params={"email": email2}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify they're in different activities
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email1 in data["Soccer Team"]["participants"]
        assert email1 not in data["Basketball Club"]["participants"]
        assert email2 in data["Basketball Club"]["participants"]
        assert email2 not in data["Soccer Team"]["participants"]
