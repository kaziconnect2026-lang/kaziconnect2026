"""
Kazi Links PWA - Comprehensive Backend API Tests
Tests cover: Registration, Login, Jobs, Bidding, Bookings, Payments, Reviews, Re-booking, Dashboard
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
API_URL = f"{BASE_URL}/api"

# Test data with unique identifiers
TEST_CLIENT_EMAIL = f"test_client_{uuid.uuid4().hex[:8]}@test.com"
TEST_PRO_EMAIL = f"test_pro_{uuid.uuid4().hex[:8]}@test.com"
TEST_PASSWORD = "password123"

class TestAuthEndpoints:
    """Authentication endpoint tests - Registration and Login"""
    
    client_token = None
    client_id = None
    pro_token = None
    pro_id = None
    
    def test_01_register_client(self):
        """Test client registration"""
        response = requests.post(f"{API_URL}/auth/register", json={
            "email": TEST_CLIENT_EMAIL,
            "name": "Test Client",
            "phone": "+254700000001",
            "role": "client",
            "location": "Nairobi",
            "password": TEST_PASSWORD
        })
        print(f"Client registration response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_CLIENT_EMAIL
        assert data["user"]["role"] == "client"
        
        TestAuthEndpoints.client_token = data["access_token"]
        TestAuthEndpoints.client_id = data["user"]["id"]
        print(f"Client registered successfully: {TestAuthEndpoints.client_id}")
    
    def test_02_register_professional(self):
        """Test professional registration"""
        response = requests.post(f"{API_URL}/auth/register", json={
            "email": TEST_PRO_EMAIL,
            "name": "Test Professional",
            "phone": "+254700000002",
            "role": "professional",
            "location": "Nairobi",
            "password": TEST_PASSWORD
        })
        print(f"Professional registration response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "professional"
        
        TestAuthEndpoints.pro_token = data["access_token"]
        TestAuthEndpoints.pro_id = data["user"]["id"]
        print(f"Professional registered successfully: {TestAuthEndpoints.pro_id}")
    
    def test_03_login_client(self):
        """Test client login"""
        response = requests.post(f"{API_URL}/auth/login", json={
            "email": TEST_CLIENT_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "client"
        print("Client login successful")
    
    def test_04_login_professional(self):
        """Test professional login"""
        response = requests.post(f"{API_URL}/auth/login", json={
            "email": TEST_PRO_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "professional"
        print("Professional login successful")
    
    def test_05_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{API_URL}/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("Invalid login correctly rejected")
    
    def test_06_get_current_user(self):
        """Test get current user endpoint"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.client_token}"}
        response = requests.get(f"{API_URL}/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_CLIENT_EMAIL
        print("Get current user successful")


class TestProfessionalProfile:
    """Professional profile creation and management tests"""
    
    def test_01_create_professional_profile(self):
        """Test professional profile creation"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.pro_token}"}
        response = requests.post(f"{API_URL}/professionals/profile", headers=headers, json={
            "profession": "Electrician",
            "bio": "Experienced electrician with 5 years of experience",
            "skills": ["Wiring", "Installation", "Repairs"],
            "hourly_rate": 500,
            "project_rate_min": 2000,
            "project_rate_max": 10000,
            "pricing_type": "both",
            "experience_years": 5,
            "portfolio_images": []
        })
        print(f"Profile creation response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "profile" in data
        assert data["profile"]["profession"] == "Electrician"
        print("Professional profile created successfully")
    
    def test_02_get_professional_profile(self):
        """Test get professional profile"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.pro_token}"}
        response = requests.get(f"{API_URL}/professionals/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["profession"] == "Electrician"
        print("Get professional profile successful")
    
    def test_03_update_availability(self):
        """Test toggle availability"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.pro_token}"}
        response = requests.put(f"{API_URL}/professionals/availability?available=true", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["availability"] == True
        print("Availability updated successfully")
    
    def test_04_search_professionals(self):
        """Test search professionals"""
        response = requests.get(f"{API_URL}/professionals/search?category=electrician")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Search returned {len(data)} professionals")


class TestJobPosting:
    """Job posting and management tests"""
    
    job_id = None
    
    def test_01_create_job(self):
        """Test job creation by client"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.client_token}"}
        response = requests.post(f"{API_URL}/jobs", headers=headers, json={
            "title": "Fix electrical wiring",
            "description": "Need to fix faulty wiring in my house",
            "category": "Electrician",
            "budget": 5000,
            "location": "Nairobi, Westlands"
        })
        print(f"Job creation response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "job" in data
        assert data["job"]["title"] == "Fix electrical wiring"
        assert data["job"]["status"] == "open"
        
        TestJobPosting.job_id = data["job"]["id"]
        print(f"Job created successfully: {TestJobPosting.job_id}")
    
    def test_02_get_client_jobs(self):
        """Test get jobs for client"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.client_token}"}
        response = requests.get(f"{API_URL}/jobs", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"Client has {len(data)} jobs")
    
    def test_03_get_available_jobs_for_professional(self):
        """Test get available jobs for professional to bid on"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.pro_token}"}
        response = requests.get(f"{API_URL}/jobs/available", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check that our job is in the list
        job_ids = [job["id"] for job in data]
        assert TestJobPosting.job_id in job_ids, "Created job should be in available jobs"
        print(f"Found {len(data)} available jobs")
    
    def test_04_get_job_detail(self):
        """Test get job detail"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.client_token}"}
        response = requests.get(f"{API_URL}/jobs/{TestJobPosting.job_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TestJobPosting.job_id
        assert data["title"] == "Fix electrical wiring"
        print("Job detail retrieved successfully")


class TestBiddingSystem:
    """Bidding system tests - Professional bids on jobs"""
    
    bid_id = None
    
    def test_01_professional_submits_bid(self):
        """Test professional submitting a bid for a job"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.pro_token}"}
        response = requests.post(f"{API_URL}/bids", headers=headers, json={
            "job_id": TestJobPosting.job_id,
            "proposed_price": 4500,
            "message": "I can fix this issue. I have experience with similar wiring problems.",
            "estimated_hours": 3
        })
        print(f"Bid submission response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "bid" in data
        assert data["bid"]["proposed_price"] == 4500
        assert data["bid"]["status"] == "pending"
        
        TestBiddingSystem.bid_id = data["bid"]["id"]
        print(f"Bid submitted successfully: {TestBiddingSystem.bid_id}")
    
    def test_02_professional_cannot_bid_twice(self):
        """Test that professional cannot bid twice on same job"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.pro_token}"}
        response = requests.post(f"{API_URL}/bids", headers=headers, json={
            "job_id": TestJobPosting.job_id,
            "proposed_price": 4000,
            "message": "Another bid attempt",
            "estimated_hours": 2
        })
        assert response.status_code == 400
        print("Duplicate bid correctly rejected")
    
    def test_03_get_my_bids(self):
        """Test professional gets their submitted bids"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.pro_token}"}
        response = requests.get(f"{API_URL}/bids/my", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check bid has job details
        assert "job" in data[0]
        print(f"Professional has {len(data)} bids")
    
    def test_04_client_views_job_bids(self):
        """Test client views bids on their job"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.client_token}"}
        response = requests.get(f"{API_URL}/bids/job/{TestJobPosting.job_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check bid has professional details
        assert "professional" in data[0]
        assert "profile" in data[0]
        print(f"Job has {len(data)} bids")
    
    def test_05_client_accepts_bid(self):
        """Test client accepts a bid - creates booking"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.client_token}"}
        response = requests.put(f"{API_URL}/bids/{TestBiddingSystem.bid_id}/accept", headers=headers)
        print(f"Accept bid response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "booking" in data
        assert data["booking"]["agreed_price"] == 4500
        assert data["booking"]["status"] == "pending"
        
        # Store booking ID for later tests
        TestBiddingSystem.booking_id = data["booking"]["id"]
        print(f"Bid accepted, booking created: {TestBiddingSystem.booking_id}")


class TestBookingsAndPayments:
    """Booking management and payment tests"""
    
    payment_id = None
    
    def test_01_get_client_bookings(self):
        """Test client gets their bookings"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.client_token}"}
        response = requests.get(f"{API_URL}/bookings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check booking has professional details
        assert "professional" in data[0]
        print(f"Client has {len(data)} bookings")
    
    def test_02_get_professional_bookings(self):
        """Test professional gets their bookings"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.pro_token}"}
        response = requests.get(f"{API_URL}/bookings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check booking has client details
        assert "client" in data[0]
        print(f"Professional has {len(data)} bookings")
    
    def test_03_initiate_payment(self):
        """Test client initiates payment (MOCKED M-Pesa)"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.client_token}"}
        response = requests.post(f"{API_URL}/payments/initiate", headers=headers, json={
            "booking_id": TestBiddingSystem.booking_id,
            "phone_number": "+254700000001"
        })
        print(f"Payment initiation response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "payment" in data
        assert data["payment"]["status"] == "escrow"
        assert "mpesa_transaction_id" in data["payment"]
        
        TestBookingsAndPayments.payment_id = data["payment"]["id"]
        print(f"Payment initiated (MOCKED): {TestBookingsAndPayments.payment_id}")
    
    def test_04_professional_starts_work(self):
        """Test professional starts work on booking"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.pro_token}"}
        response = requests.put(
            f"{API_URL}/bookings/{TestBiddingSystem.booking_id}/status?status=in_progress",
            headers=headers
        )
        assert response.status_code == 200
        print("Professional started work")
    
    def test_05_professional_completes_work(self):
        """Test professional completes work"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.pro_token}"}
        response = requests.put(
            f"{API_URL}/bookings/{TestBiddingSystem.booking_id}/status?status=completed",
            headers=headers
        )
        assert response.status_code == 200
        print("Professional completed work")
    
    def test_06_client_releases_payment(self):
        """Test client releases payment to professional"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.client_token}"}
        response = requests.post(
            f"{API_URL}/payments/{TestBookingsAndPayments.payment_id}/release",
            headers=headers
        )
        print(f"Payment release response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "amount_released" in data
        # 80% of 4500 = 3600 (20% platform fee)
        assert data["amount_released"] == 3600
        print(f"Payment released: KSh {data['amount_released']}")


class TestReviewSystem:
    """Review and rating system tests"""
    
    def test_01_client_submits_review(self):
        """Test client submits review for completed booking"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.client_token}"}
        response = requests.post(f"{API_URL}/reviews", headers=headers, json={
            "booking_id": TestBiddingSystem.booking_id,
            "professional_id": TestAuthEndpoints.pro_id,
            "rating": 5,
            "comment": "Excellent work! Very professional and timely."
        })
        print(f"Review submission response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("Review submitted successfully")
    
    def test_02_get_professional_reviews(self):
        """Test get reviews for a professional"""
        response = requests.get(f"{API_URL}/reviews/{TestAuthEndpoints.pro_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["rating"] == 5
        assert "client_name" in data[0]
        print(f"Professional has {len(data)} reviews")
    
    def test_03_verify_professional_rating_updated(self):
        """Test that professional's rating is updated after review"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.pro_token}"}
        response = requests.get(f"{API_URL}/professionals/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5.0
        assert data["total_reviews"] == 1
        print(f"Professional rating: {data['rating']}/5 ({data['total_reviews']} reviews)")


class TestRebooking:
    """Re-booking feature tests"""
    
    def test_01_client_rebooks_professional(self):
        """Test client re-books a professional"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.client_token}"}
        scheduled_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        response = requests.post(
            f"{API_URL}/bookings/rebook/{TestAuthEndpoints.pro_id}",
            headers=headers,
            json={
                "professional_id": TestAuthEndpoints.pro_id,
                "service_description": "Follow-up electrical inspection",
                "scheduled_date": scheduled_date,
                "estimated_hours": 2,
                "agreed_price": 3000
            }
        )
        print(f"Rebook response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "booking" in data
        assert data["booking"]["service_description"] == "Follow-up electrical inspection"
        assert data["booking"]["agreed_price"] == 3000
        print("Re-booking created successfully")


class TestDashboards:
    """Dashboard data tests"""
    
    def test_01_client_dashboard(self):
        """Test client dashboard data"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.client_token}"}
        response = requests.get(f"{API_URL}/dashboard/client", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check dashboard has expected fields
        assert "active_bookings" in data
        assert "recent_jobs" in data
        assert "total_spent" in data
        print(f"Client dashboard - Total spent: KSh {data['total_spent']}")
    
    def test_02_professional_dashboard(self):
        """Test professional dashboard data with weekly earnings"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.pro_token}"}
        response = requests.get(f"{API_URL}/dashboard/professional", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check dashboard has expected fields
        assert "profile" in data
        assert "upcoming_bookings" in data
        assert "total_earnings" in data
        assert "weekly_earnings" in data
        assert "total_platform_commission" in data
        
        # Check weekly earnings structure
        weekly = data["weekly_earnings"]
        assert "labels" in weekly
        assert "earnings" in weekly
        assert "commissions" in weekly
        assert "total_week_earnings" in weekly
        assert "total_week_commission" in weekly
        
        print(f"Professional dashboard - Total earnings: KSh {data['total_earnings']}")
        print(f"Weekly earnings: KSh {weekly['total_week_earnings']}")
        print(f"Platform commission: KSh {data['total_platform_commission']}")
    
    def test_03_professional_dashboard_bids_info(self):
        """Test professional dashboard includes bid information"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.pro_token}"}
        response = requests.get(f"{API_URL}/dashboard/professional", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check bids info
        assert "bids" in data
        assert "pending" in data["bids"]
        assert "accepted" in data["bids"]
        assert "rejected" in data["bids"]
        print(f"Bids - Pending: {data['bids']['pending']}, Accepted: {data['bids']['accepted']}")


class TestCategories:
    """Categories endpoint tests"""
    
    def test_01_get_categories(self):
        """Test get all categories"""
        response = requests.get(f"{API_URL}/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 8
        
        # Check category structure
        category = data[0]
        assert "id" in category
        assert "name" in category
        assert "icon" in category
        assert "image" in category
        print(f"Found {len(data)} categories")


class TestAIMatching:
    """AI matching endpoint tests"""
    
    def test_01_ai_match_professionals(self):
        """Test AI matching with Gemini 3 Flash"""
        headers = {"Authorization": f"Bearer {TestAuthEndpoints.client_token}"}
        response = requests.post(f"{API_URL}/match", headers=headers, json={
            "job_description": "Need electrical wiring fixed in my house",
            "category": "Electrician",
            "location": "Nairobi",
            "budget": 5000
        })
        print(f"AI matching response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "matches" in data
        print(f"AI matching returned {len(data['matches'])} matches, AI powered: {data.get('ai_powered', False)}")


# Run tests in order
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
