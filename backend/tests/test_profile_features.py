"""
Test suite for Client Profile and Professional Profile Photo Upload features
Tests:
- Client profile page API endpoints
- Profile update functionality
- Profile photo upload for both clients and professionals
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hire-skilled-pros.preview.emergentagent.com').rstrip('/')

class TestClientProfileFeatures:
    """Tests for client profile page functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as client
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "client@test.com",
            "password": "password"
        })
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.client_user = login_response.json().get("user")
        else:
            pytest.skip("Client login failed")
    
    def test_client_login_success(self):
        """Test client can login successfully"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "client@test.com",
            "password": "password"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "client"
    
    def test_get_current_user_profile(self):
        """Test GET /api/auth/me returns user profile with all fields"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        
        data = response.json()
        # Verify all required fields are present
        assert "id" in data
        assert "email" in data
        assert "name" in data
        assert "phone" in data
        assert "role" in data
        assert "location" in data
        assert "wallet_balance" in data
        assert "profile_photo" in data
        assert data["role"] == "client"
    
    def test_update_user_profile(self):
        """Test PUT /api/users/profile updates user profile"""
        update_data = {
            "name": "Test Client Profile Update",
            "phone": "+254711111111",
            "location": "Nairobi, Kenya"
        }
        
        response = self.session.put(f"{BASE_URL}/api/users/profile", json=update_data)
        assert response.status_code == 200
        assert response.json()["message"] == "Profile updated successfully"
        
        # Verify update persisted
        verify_response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert verify_response.status_code == 200
        user_data = verify_response.json()
        assert user_data["name"] == "Test Client Profile Update"
        assert user_data["phone"] == "+254711111111"
        assert user_data["location"] == "Nairobi, Kenya"
    
    def test_update_profile_empty_data_rejected(self):
        """Test PUT /api/users/profile rejects empty update"""
        response = self.session.put(f"{BASE_URL}/api/users/profile", json={})
        assert response.status_code == 400
        assert "No data to update" in response.json().get("detail", "")
    
    def test_upload_profile_photo(self):
        """Test POST /api/users/profile-photo uploads photo URL"""
        test_photo_url = "https://example.com/test-client-photo.jpg"
        
        response = self.session.post(
            f"{BASE_URL}/api/users/profile-photo?photo_url={test_photo_url}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Profile photo updated"
        assert data["photo_url"] == test_photo_url
        
        # Verify photo persisted
        verify_response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert verify_response.status_code == 200
        assert verify_response.json()["profile_photo"] == test_photo_url
    
    def test_upload_profile_photo_base64(self):
        """Test POST /api/users/profile-photo with base64 data URL"""
        # Small base64 test image
        base64_photo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        import urllib.parse
        encoded_url = urllib.parse.quote(base64_photo, safe='')
        
        response = self.session.post(
            f"{BASE_URL}/api/users/profile-photo?photo_url={encoded_url}"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Profile photo updated"
    
    def test_client_dashboard_endpoint(self):
        """Test GET /api/dashboard/client returns dashboard data"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/client")
        assert response.status_code == 200
        
        data = response.json()
        # Verify dashboard structure
        assert "active_bookings" in data
        assert "recent_jobs" in data
        assert "total_spent" in data
        assert "total_bookings" in data


class TestProfessionalProfilePhotoFeatures:
    """Tests for professional profile photo upload functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test professional session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as professional
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "pro@test.com",
            "password": "password"
        })
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.pro_user = login_response.json().get("user")
        else:
            pytest.skip("Professional login failed")
    
    def test_professional_login_success(self):
        """Test professional can login successfully"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "pro@test.com",
            "password": "password"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "professional"
    
    def test_professional_get_profile(self):
        """Test GET /api/auth/me returns professional profile with photo field"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        
        data = response.json()
        assert "profile_photo" in data
        assert data["role"] == "professional"
    
    def test_professional_upload_profile_photo(self):
        """Test POST /api/users/profile-photo for professional"""
        test_photo_url = "https://example.com/test-pro-photo.jpg"
        
        response = self.session.post(
            f"{BASE_URL}/api/users/profile-photo?photo_url={test_photo_url}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Profile photo updated"
        assert data["photo_url"] == test_photo_url
        
        # Verify photo persisted
        verify_response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert verify_response.status_code == 200
        assert verify_response.json()["profile_photo"] == test_photo_url
    
    def test_professional_profile_exists(self):
        """Test GET /api/professionals/profile returns professional profile"""
        response = self.session.get(f"{BASE_URL}/api/professionals/profile")
        # May return 404 if no profile created yet, or 200 if exists
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "profession" in data
            assert "bio" in data
            assert "skills" in data


class TestProfileAuthorizationAndEdgeCases:
    """Tests for authorization and edge cases"""
    
    def test_profile_update_requires_auth(self):
        """Test PUT /api/users/profile requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.put(f"{BASE_URL}/api/users/profile", json={
            "name": "Unauthorized Update"
        })
        assert response.status_code in [401, 403]
    
    def test_profile_photo_upload_requires_auth(self):
        """Test POST /api/users/profile-photo requires authentication"""
        session = requests.Session()
        
        response = session.post(
            f"{BASE_URL}/api/users/profile-photo?photo_url=https://example.com/photo.jpg"
        )
        assert response.status_code in [401, 403]
    
    def test_client_dashboard_requires_client_role(self):
        """Test GET /api/dashboard/client requires client role"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as professional
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "pro@test.com",
            "password": "password"
        })
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            session.headers.update({"Authorization": f"Bearer {token}"})
            
            # Try to access client dashboard
            response = session.get(f"{BASE_URL}/api/dashboard/client")
            assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
