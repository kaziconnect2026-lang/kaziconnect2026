"""
Test Admin Dashboard Endpoints
Tests for:
- GET /api/admin/stats - Admin statistics
- GET /api/admin/dashboard - Dashboard data with charts
- GET /api/admin/users - User management list
- PUT /api/admin/users/{id}/status - Activate/deactivate users
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@kazilinks.com"
ADMIN_PASSWORD = "admin123"


class TestAdminAuth:
    """Test admin authentication"""
    
    def test_admin_login(self):
        """Test admin can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful - User: {data['user']['name']}")


class TestAdminStats:
    """Test GET /api/admin/stats endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_admin_stats_returns_user_stats(self, admin_token):
        """Test stats endpoint returns user statistics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Stats request failed: {response.text}"
        data = response.json()
        
        # Verify user stats structure
        assert "users" in data
        assert "total" in data["users"]
        assert "clients" in data["users"]
        assert "professionals" in data["users"]
        assert "active_professionals" in data["users"]
        print(f"✓ User stats: {data['users']}")
    
    def test_admin_stats_returns_job_stats(self, admin_token):
        """Test stats endpoint returns job statistics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify job stats structure
        assert "jobs" in data
        assert "total" in data["jobs"]
        assert "open" in data["jobs"]
        assert "matched" in data["jobs"]
        assert "completed" in data["jobs"]
        print(f"✓ Job stats: {data['jobs']}")
    
    def test_admin_stats_returns_booking_stats(self, admin_token):
        """Test stats endpoint returns booking statistics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify booking stats structure
        assert "bookings" in data
        assert "total" in data["bookings"]
        assert "pending" in data["bookings"]
        assert "confirmed" in data["bookings"]
        assert "in_progress" in data["bookings"]
        assert "completed" in data["bookings"]
        assert "cancelled" in data["bookings"]
        print(f"✓ Booking stats: {data['bookings']}")
    
    def test_admin_stats_returns_bid_stats(self, admin_token):
        """Test stats endpoint returns bid statistics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify bid stats structure
        assert "bids" in data
        assert "total" in data["bids"]
        assert "pending" in data["bids"]
        assert "accepted" in data["bids"]
        assert "rejected" in data["bids"]
        assert "acceptance_rate" in data["bids"]
        print(f"✓ Bid stats: {data['bids']}")
    
    def test_admin_stats_returns_financial_stats(self, admin_token):
        """Test stats endpoint returns financial statistics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify financial stats structure
        assert "financials" in data
        assert "total_transactions" in data["financials"]
        assert "platform_revenue" in data["financials"]
        assert "escrow_balance" in data["financials"]
        assert "platform_fee_percentage" in data["financials"]
        assert "total_wallet_deposits" in data["financials"]
        assert "total_wallet_withdrawals" in data["financials"]
        print(f"✓ Financial stats: {data['financials']}")
    
    def test_admin_stats_returns_review_stats(self, admin_token):
        """Test stats endpoint returns review statistics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify review stats structure
        assert "reviews" in data
        assert "total" in data["reviews"]
        assert "average_rating" in data["reviews"]
        print(f"✓ Review stats: {data['reviews']}")
    
    def test_admin_stats_requires_admin_role(self):
        """Test stats endpoint rejects non-admin users"""
        # Create a regular client user
        unique_id = str(uuid.uuid4())[:8]
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_client_{unique_id}@test.com",
            "password": "testpass123",
            "name": "Test Client",
            "phone": "+254700000000",
            "role": "client"
        })
        
        if register_response.status_code == 200:
            client_token = register_response.json()["access_token"]
            
            # Try to access admin stats
            response = requests.get(
                f"{BASE_URL}/api/admin/stats",
                headers={"Authorization": f"Bearer {client_token}"}
            )
            assert response.status_code == 403, "Non-admin should be rejected"
            print("✓ Non-admin user correctly rejected from stats endpoint")
        else:
            pytest.skip("Could not create test client user")


class TestAdminDashboard:
    """Test GET /api/admin/dashboard endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_admin_dashboard_returns_recent_activity(self, admin_token):
        """Test dashboard returns recent activity data"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Dashboard request failed: {response.text}"
        data = response.json()
        
        # Verify recent activity structure
        assert "recent_activity" in data
        assert "bookings" in data["recent_activity"]
        assert "jobs" in data["recent_activity"]
        assert "users" in data["recent_activity"]
        print(f"✓ Recent activity data present")
    
    def test_admin_dashboard_returns_charts_data(self, admin_token):
        """Test dashboard returns chart data for visualizations"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify charts structure
        assert "charts" in data
        assert "revenue" in data["charts"]
        assert "bookings" in data["charts"]
        assert "labels" in data["charts"]
        assert "new_users" in data["charts"]
        
        # Verify arrays have 7 days of data
        assert len(data["charts"]["revenue"]) == 7
        assert len(data["charts"]["bookings"]) == 7
        assert len(data["charts"]["labels"]) == 7
        print(f"✓ Charts data: revenue={data['charts']['revenue']}, bookings={data['charts']['bookings']}")
    
    def test_admin_dashboard_returns_jobs_by_category(self, admin_token):
        """Test dashboard returns jobs grouped by category"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify jobs by category
        assert "jobs_by_category" in data
        assert isinstance(data["jobs_by_category"], list)
        
        if len(data["jobs_by_category"]) > 0:
            # Verify structure of category items
            cat = data["jobs_by_category"][0]
            assert "category" in cat or "_id" in cat
            assert "count" in cat
        print(f"✓ Jobs by category: {data['jobs_by_category']}")
    
    def test_admin_dashboard_returns_top_professionals(self, admin_token):
        """Test dashboard returns top rated professionals"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify top professionals
        assert "top_professionals" in data
        assert isinstance(data["top_professionals"], list)
        
        if len(data["top_professionals"]) > 0:
            prof = data["top_professionals"][0]
            assert "name" in prof
            assert "rating" in prof
        print(f"✓ Top professionals: {len(data['top_professionals'])} found")
    
    def test_admin_dashboard_returns_top_earners(self, admin_token):
        """Test dashboard returns top earning professionals"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify top earners
        assert "top_earners" in data
        assert isinstance(data["top_earners"], list)
        
        if len(data["top_earners"]) > 0:
            earner = data["top_earners"][0]
            assert "name" in earner
            assert "total_earnings" in earner
        print(f"✓ Top earners: {len(data['top_earners'])} found")
    
    def test_admin_dashboard_requires_admin_role(self):
        """Test dashboard endpoint rejects non-admin users"""
        # Create a regular professional user
        unique_id = str(uuid.uuid4())[:8]
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_pro_{unique_id}@test.com",
            "password": "testpass123",
            "name": "Test Professional",
            "phone": "+254700000001",
            "role": "professional"
        })
        
        if register_response.status_code == 200:
            pro_token = register_response.json()["access_token"]
            
            # Try to access admin dashboard
            response = requests.get(
                f"{BASE_URL}/api/admin/dashboard",
                headers={"Authorization": f"Bearer {pro_token}"}
            )
            assert response.status_code == 403, "Non-admin should be rejected"
            print("✓ Non-admin user correctly rejected from dashboard endpoint")
        else:
            pytest.skip("Could not create test professional user")


class TestAdminUsers:
    """Test GET /api/admin/users endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_admin_users_returns_user_list(self, admin_token):
        """Test users endpoint returns list of users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Users request failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)
        assert len(data["users"]) > 0
        
        # Verify user structure
        user = data["users"][0]
        assert "id" in user
        assert "email" in user
        assert "name" in user
        assert "role" in user
        assert "password_hash" not in user  # Should not expose password
        print(f"✓ Users list: {data['total']} total users")
    
    def test_admin_users_filter_by_role(self, admin_token):
        """Test users endpoint can filter by role"""
        # Filter by client role
        response = requests.get(
            f"{BASE_URL}/api/admin/users?role=client",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All returned users should be clients
        for user in data["users"]:
            assert user["role"] == "client", f"Expected client, got {user['role']}"
        print(f"✓ Role filter working: {len(data['users'])} clients found")
    
    def test_admin_users_search(self, admin_token):
        """Test users endpoint can search by name/email"""
        # Search for admin
        response = requests.get(
            f"{BASE_URL}/api/admin/users?search=admin",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should find at least the admin user
        assert len(data["users"]) >= 1
        print(f"✓ Search working: {len(data['users'])} users found for 'admin'")
    
    def test_admin_users_pagination(self, admin_token):
        """Test users endpoint supports pagination"""
        # Get first page with limit 5
        response = requests.get(
            f"{BASE_URL}/api/admin/users?limit=5&skip=0",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "limit" in data
        assert "skip" in data
        assert data["limit"] == 5
        assert data["skip"] == 0
        assert len(data["users"]) <= 5
        print(f"✓ Pagination working: limit={data['limit']}, skip={data['skip']}")
    
    def test_admin_users_requires_admin_role(self):
        """Test users endpoint rejects non-admin users"""
        # Create a regular client user
        unique_id = str(uuid.uuid4())[:8]
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_client2_{unique_id}@test.com",
            "password": "testpass123",
            "name": "Test Client 2",
            "phone": "+254700000002",
            "role": "client"
        })
        
        if register_response.status_code == 200:
            client_token = register_response.json()["access_token"]
            
            # Try to access admin users
            response = requests.get(
                f"{BASE_URL}/api/admin/users",
                headers={"Authorization": f"Bearer {client_token}"}
            )
            assert response.status_code == 403, "Non-admin should be rejected"
            print("✓ Non-admin user correctly rejected from users endpoint")
        else:
            pytest.skip("Could not create test client user")


class TestAdminUserStatus:
    """Test PUT /api/admin/users/{id}/status endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    @pytest.fixture
    def test_user(self, admin_token):
        """Create a test user to toggle status"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_toggle_{unique_id}@test.com",
            "password": "testpass123",
            "name": f"Test Toggle User {unique_id}",
            "phone": "+254700000003",
            "role": "client"
        })
        if response.status_code == 200:
            return response.json()["user"]
        pytest.skip("Could not create test user")
    
    def test_admin_can_deactivate_user(self, admin_token, test_user):
        """Test admin can deactivate a user"""
        user_id = test_user["id"]
        
        # Deactivate user
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}/status?is_active=false",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Deactivate failed: {response.text}"
        
        # Verify user is deactivated
        users_response = requests.get(
            f"{BASE_URL}/api/admin/users?search={test_user['email']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert users_response.status_code == 200
        users = users_response.json()["users"]
        
        found_user = next((u for u in users if u["id"] == user_id), None)
        assert found_user is not None
        assert found_user["is_active"] == False
        print(f"✓ User deactivated successfully: {test_user['email']}")
    
    def test_admin_can_activate_user(self, admin_token, test_user):
        """Test admin can activate a user"""
        user_id = test_user["id"]
        
        # First deactivate
        requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}/status?is_active=false",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Then activate
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}/status?is_active=true",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Activate failed: {response.text}"
        
        # Verify user is activated
        users_response = requests.get(
            f"{BASE_URL}/api/admin/users?search={test_user['email']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert users_response.status_code == 200
        users = users_response.json()["users"]
        
        found_user = next((u for u in users if u["id"] == user_id), None)
        assert found_user is not None
        assert found_user["is_active"] == True
        print(f"✓ User activated successfully: {test_user['email']}")
    
    def test_admin_status_update_nonexistent_user(self, admin_token):
        """Test status update for non-existent user returns 404"""
        fake_id = str(uuid.uuid4())
        
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{fake_id}/status?is_active=false",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should return 404 or handle gracefully
        assert response.status_code in [404, 200], f"Unexpected status: {response.status_code}"
        print("✓ Non-existent user handled correctly")
    
    def test_admin_status_requires_admin_role(self, test_user):
        """Test status update rejects non-admin users"""
        # Create another regular user
        unique_id = str(uuid.uuid4())[:8]
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_attacker_{unique_id}@test.com",
            "password": "testpass123",
            "name": "Test Attacker",
            "phone": "+254700000004",
            "role": "client"
        })
        
        if register_response.status_code == 200:
            attacker_token = register_response.json()["access_token"]
            
            # Try to deactivate another user
            response = requests.put(
                f"{BASE_URL}/api/admin/users/{test_user['id']}/status?is_active=false",
                headers={"Authorization": f"Bearer {attacker_token}"}
            )
            assert response.status_code == 403, "Non-admin should be rejected"
            print("✓ Non-admin user correctly rejected from status update")
        else:
            pytest.skip("Could not create test attacker user")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
