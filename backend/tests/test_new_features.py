"""
Kazi Links PWA - New Features Tests
Tests cover: Wallet (deposit/withdraw), Notifications, ID number in profile, 
AI bid suggestions, Jobs filtered by profession, Geolocation filtering
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
API_URL = f"{BASE_URL}/api"

# Test data with unique identifiers
TEST_UUID = uuid.uuid4().hex[:8]
TEST_CLIENT_EMAIL = f"test_wallet_client_{TEST_UUID}@test.com"
TEST_PRO_EMAIL = f"test_wallet_pro_{TEST_UUID}@test.com"
TEST_PASSWORD = "password123"


class TestWalletFeatures:
    """Wallet system tests - Deposit, Withdraw, Balance, Transactions"""
    
    client_token = None
    client_id = None
    pro_token = None
    pro_id = None
    
    @pytest.fixture(autouse=True)
    def setup_users(self):
        """Setup test users if not already created"""
        if not TestWalletFeatures.client_token:
            # Register client
            response = requests.post(f"{API_URL}/auth/register", json={
                "email": TEST_CLIENT_EMAIL,
                "name": "Wallet Test Client",
                "phone": "+254712345678",
                "role": "client",
                "location": "Nairobi",
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestWalletFeatures.client_token = data["access_token"]
                TestWalletFeatures.client_id = data["user"]["id"]
            elif response.status_code == 400:  # Already exists
                login_resp = requests.post(f"{API_URL}/auth/login", json={
                    "email": TEST_CLIENT_EMAIL,
                    "password": TEST_PASSWORD
                })
                if login_resp.status_code == 200:
                    data = login_resp.json()
                    TestWalletFeatures.client_token = data["access_token"]
                    TestWalletFeatures.client_id = data["user"]["id"]
        
        if not TestWalletFeatures.pro_token:
            # Register professional
            response = requests.post(f"{API_URL}/auth/register", json={
                "email": TEST_PRO_EMAIL,
                "name": "Wallet Test Pro",
                "phone": "+254712345679",
                "role": "professional",
                "location": "Nairobi",
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestWalletFeatures.pro_token = data["access_token"]
                TestWalletFeatures.pro_id = data["user"]["id"]
            elif response.status_code == 400:  # Already exists
                login_resp = requests.post(f"{API_URL}/auth/login", json={
                    "email": TEST_PRO_EMAIL,
                    "password": TEST_PASSWORD
                })
                if login_resp.status_code == 200:
                    data = login_resp.json()
                    TestWalletFeatures.pro_token = data["access_token"]
                    TestWalletFeatures.pro_id = data["user"]["id"]
    
    def test_01_get_wallet_balance(self):
        """Test getting wallet balance"""
        headers = {"Authorization": f"Bearer {TestWalletFeatures.client_token}"}
        response = requests.get(f"{API_URL}/wallet/balance", headers=headers)
        
        print(f"Wallet balance response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "balance" in data
        assert isinstance(data["balance"], (int, float))
        print(f"Current balance: KSh {data['balance']}")
    
    def test_02_deposit_to_wallet(self):
        """Test depositing money to wallet (MOCKED M-Pesa)"""
        headers = {"Authorization": f"Bearer {TestWalletFeatures.client_token}"}
        deposit_amount = 5000
        
        response = requests.post(f"{API_URL}/wallet/deposit", headers=headers, json={
            "amount": deposit_amount,
            "phone_number": "254712345678"
        })
        
        print(f"Deposit response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "MOCKED" in data["message"]  # Verify it's mocked
        assert "transaction_id" in data
        assert "new_balance" in data
        assert data["amount"] == deposit_amount
        print(f"Deposited KSh {deposit_amount}, new balance: KSh {data['new_balance']}")
    
    def test_03_deposit_validation_negative_amount(self):
        """Test deposit validation - negative amount should fail"""
        headers = {"Authorization": f"Bearer {TestWalletFeatures.client_token}"}
        
        response = requests.post(f"{API_URL}/wallet/deposit", headers=headers, json={
            "amount": -100,
            "phone_number": "254712345678"
        })
        
        print(f"Negative deposit response: {response.status_code}")
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_04_deposit_validation_max_amount(self):
        """Test deposit validation - amount over 100,000 should fail"""
        headers = {"Authorization": f"Bearer {TestWalletFeatures.client_token}"}
        
        response = requests.post(f"{API_URL}/wallet/deposit", headers=headers, json={
            "amount": 150000,
            "phone_number": "254712345678"
        })
        
        print(f"Max deposit response: {response.status_code}")
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_05_withdraw_from_wallet(self):
        """Test withdrawing money from wallet (MOCKED M-Pesa)"""
        headers = {"Authorization": f"Bearer {TestWalletFeatures.client_token}"}
        
        # First check balance
        balance_resp = requests.get(f"{API_URL}/wallet/balance", headers=headers)
        current_balance = balance_resp.json()["balance"]
        
        if current_balance < 1000:
            # Deposit first
            requests.post(f"{API_URL}/wallet/deposit", headers=headers, json={
                "amount": 5000,
                "phone_number": "254712345678"
            })
        
        withdraw_amount = 1000
        response = requests.post(f"{API_URL}/wallet/withdraw", headers=headers, json={
            "amount": withdraw_amount,
            "phone_number": "254712345678"
        })
        
        print(f"Withdraw response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "MOCKED" in data["message"]  # Verify it's mocked
        assert "transaction_id" in data
        assert "new_balance" in data
        print(f"Withdrawn KSh {withdraw_amount}, new balance: KSh {data['new_balance']}")
    
    def test_06_withdraw_insufficient_balance(self):
        """Test withdrawal with insufficient balance"""
        headers = {"Authorization": f"Bearer {TestWalletFeatures.client_token}"}
        
        # Try to withdraw more than balance
        response = requests.post(f"{API_URL}/wallet/withdraw", headers=headers, json={
            "amount": 999999999,
            "phone_number": "254712345678"
        })
        
        print(f"Insufficient balance response: {response.status_code}")
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Insufficient" in response.json().get("detail", "")
    
    def test_07_get_wallet_transactions(self):
        """Test getting wallet transaction history"""
        headers = {"Authorization": f"Bearer {TestWalletFeatures.client_token}"}
        response = requests.get(f"{API_URL}/wallet/transactions", headers=headers)
        
        print(f"Transactions response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            tx = data[0]
            assert "id" in tx
            assert "type" in tx
            assert "amount" in tx
            assert "status" in tx
            assert "reference" in tx
            print(f"Found {len(data)} transactions")


class TestNotificationFeatures:
    """Notification system tests - Subscribe, Get notifications, Mark as read"""
    
    pro_token = None
    pro_id = None
    
    @pytest.fixture(autouse=True)
    def setup_user(self):
        """Setup test user if not already created"""
        if not TestNotificationFeatures.pro_token:
            email = f"test_notif_pro_{uuid.uuid4().hex[:8]}@test.com"
            response = requests.post(f"{API_URL}/auth/register", json={
                "email": email,
                "name": "Notification Test Pro",
                "phone": "+254712345680",
                "role": "professional",
                "location": "Nairobi",
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestNotificationFeatures.pro_token = data["access_token"]
                TestNotificationFeatures.pro_id = data["user"]["id"]
    
    def test_01_subscribe_to_push_notifications(self):
        """Test subscribing to push notifications"""
        headers = {"Authorization": f"Bearer {TestNotificationFeatures.pro_token}"}
        
        response = requests.post(f"{API_URL}/notifications/subscribe", headers=headers, json={
            "endpoint": f"demo-endpoint-{TestNotificationFeatures.pro_id}",
            "keys": {
                "p256dh": "demo-key",
                "auth": "demo-auth"
            }
        })
        
        print(f"Subscribe response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        print(f"Subscription result: {data['message']}")
    
    def test_02_subscribe_duplicate(self):
        """Test subscribing again (should return already subscribed)"""
        headers = {"Authorization": f"Bearer {TestNotificationFeatures.pro_token}"}
        
        response = requests.post(f"{API_URL}/notifications/subscribe", headers=headers, json={
            "endpoint": f"demo-endpoint-{TestNotificationFeatures.pro_id}",
            "keys": {
                "p256dh": "demo-key",
                "auth": "demo-auth"
            }
        })
        
        print(f"Duplicate subscribe response: {response.status_code}")
        assert response.status_code == 200
        assert "Already subscribed" in response.json().get("message", "")
    
    def test_03_get_notifications(self):
        """Test getting notifications list"""
        headers = {"Authorization": f"Bearer {TestNotificationFeatures.pro_token}"}
        
        response = requests.get(f"{API_URL}/notifications", headers=headers)
        
        print(f"Get notifications response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} notifications")
    
    def test_04_unsubscribe_from_push(self):
        """Test unsubscribing from push notifications"""
        headers = {"Authorization": f"Bearer {TestNotificationFeatures.pro_token}"}
        endpoint = f"demo-endpoint-{TestNotificationFeatures.pro_id}"
        
        response = requests.delete(
            f"{API_URL}/notifications/unsubscribe?endpoint={endpoint}", 
            headers=headers
        )
        
        print(f"Unsubscribe response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestProfessionalProfileWithIdNumber:
    """Test professional profile with ID number field"""
    
    pro_token = None
    pro_id = None
    
    @pytest.fixture(autouse=True)
    def setup_user(self):
        """Setup test user if not already created"""
        if not TestProfessionalProfileWithIdNumber.pro_token:
            email = f"test_idnum_pro_{uuid.uuid4().hex[:8]}@test.com"
            response = requests.post(f"{API_URL}/auth/register", json={
                "email": email,
                "name": "ID Number Test Pro",
                "phone": "+254712345681",
                "role": "professional",
                "location": "Nairobi",
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestProfessionalProfileWithIdNumber.pro_token = data["access_token"]
                TestProfessionalProfileWithIdNumber.pro_id = data["user"]["id"]
    
    def test_01_create_profile_with_id_number(self):
        """Test creating professional profile with ID number"""
        headers = {"Authorization": f"Bearer {TestProfessionalProfileWithIdNumber.pro_token}"}
        
        response = requests.post(f"{API_URL}/professionals/profile", headers=headers, json={
            "profession": "Plumber",
            "bio": "Experienced plumber with 10 years of experience",
            "skills": ["Pipe repair", "Installation", "Maintenance"],
            "hourly_rate": 500,
            "project_rate_min": 2000,
            "project_rate_max": 10000,
            "pricing_type": "both",
            "experience_years": 10,
            "portfolio_images": [],
            "id_number": "12345678"  # National ID number
        })
        
        print(f"Create profile response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "profile" in data
        assert data["profile"]["id_number"] == "12345678"
        print(f"Profile created with ID number: {data['profile']['id_number']}")
    
    def test_02_get_profile_with_id_number(self):
        """Test retrieving profile with ID number"""
        headers = {"Authorization": f"Bearer {TestProfessionalProfileWithIdNumber.pro_token}"}
        
        response = requests.get(f"{API_URL}/professionals/profile", headers=headers)
        
        print(f"Get profile response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id_number" in data
        assert data["id_number"] == "12345678"
        print(f"Profile retrieved with ID number: {data['id_number']}")
    
    def test_03_update_profile_id_number(self):
        """Test updating profile ID number"""
        headers = {"Authorization": f"Bearer {TestProfessionalProfileWithIdNumber.pro_token}"}
        
        response = requests.put(f"{API_URL}/professionals/profile", headers=headers, json={
            "profession": "Plumber",
            "bio": "Updated bio - Expert plumber",
            "skills": ["Pipe repair", "Installation", "Maintenance", "Emergency repairs"],
            "hourly_rate": 600,
            "project_rate_min": 2500,
            "project_rate_max": 12000,
            "pricing_type": "both",
            "experience_years": 11,
            "portfolio_images": [],
            "id_number": "87654321"  # Updated ID number
        })
        
        print(f"Update profile response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify update
        get_resp = requests.get(f"{API_URL}/professionals/profile", headers=headers)
        assert get_resp.json()["id_number"] == "87654321"
        print("Profile ID number updated successfully")


class TestJobsFilteredByProfession:
    """Test jobs filtered by professional's profession category"""
    
    client_token = None
    client_id = None
    plumber_token = None
    plumber_id = None
    electrician_token = None
    electrician_id = None
    job_id = None
    
    @pytest.fixture(autouse=True)
    def setup_users(self):
        """Setup test users"""
        test_uuid = uuid.uuid4().hex[:8]
        
        # Create client
        if not TestJobsFilteredByProfession.client_token:
            email = f"test_filter_client_{test_uuid}@test.com"
            response = requests.post(f"{API_URL}/auth/register", json={
                "email": email,
                "name": "Filter Test Client",
                "phone": "+254712345682",
                "role": "client",
                "location": "Nairobi",
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestJobsFilteredByProfession.client_token = data["access_token"]
                TestJobsFilteredByProfession.client_id = data["user"]["id"]
        
        # Create plumber professional
        if not TestJobsFilteredByProfession.plumber_token:
            email = f"test_plumber_{test_uuid}@test.com"
            response = requests.post(f"{API_URL}/auth/register", json={
                "email": email,
                "name": "Test Plumber",
                "phone": "+254712345683",
                "role": "professional",
                "location": "Nairobi",
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestJobsFilteredByProfession.plumber_token = data["access_token"]
                TestJobsFilteredByProfession.plumber_id = data["user"]["id"]
                
                # Create plumber profile
                headers = {"Authorization": f"Bearer {data['access_token']}"}
                requests.post(f"{API_URL}/professionals/profile", headers=headers, json={
                    "profession": "Plumber",
                    "bio": "Expert plumber",
                    "skills": ["Pipe repair"],
                    "hourly_rate": 500,
                    "pricing_type": "hourly",
                    "experience_years": 5
                })
        
        # Create electrician professional
        if not TestJobsFilteredByProfession.electrician_token:
            email = f"test_electrician_{test_uuid}@test.com"
            response = requests.post(f"{API_URL}/auth/register", json={
                "email": email,
                "name": "Test Electrician",
                "phone": "+254712345684",
                "role": "professional",
                "location": "Nairobi",
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestJobsFilteredByProfession.electrician_token = data["access_token"]
                TestJobsFilteredByProfession.electrician_id = data["user"]["id"]
                
                # Create electrician profile
                headers = {"Authorization": f"Bearer {data['access_token']}"}
                requests.post(f"{API_URL}/professionals/profile", headers=headers, json={
                    "profession": "Electrician",
                    "bio": "Expert electrician",
                    "skills": ["Wiring"],
                    "hourly_rate": 600,
                    "pricing_type": "hourly",
                    "experience_years": 7
                })
    
    def test_01_client_posts_plumbing_job(self):
        """Test client posting a plumbing job"""
        headers = {"Authorization": f"Bearer {TestJobsFilteredByProfession.client_token}"}
        
        response = requests.post(f"{API_URL}/jobs", headers=headers, json={
            "title": f"Fix leaking pipe - TEST_{uuid.uuid4().hex[:8]}",
            "description": "Need a plumber to fix a leaking pipe in the kitchen",
            "category": "Plumber",
            "budget": 3000,
            "location": "Nairobi, Westlands",
            "latitude": -1.2641,
            "longitude": 36.8034
        })
        
        print(f"Post job response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        TestJobsFilteredByProfession.job_id = data["job"]["id"]
        print(f"Job posted: {data['job']['title']}")
    
    def test_02_plumber_sees_plumbing_job(self):
        """Test that plumber can see plumbing jobs"""
        headers = {"Authorization": f"Bearer {TestJobsFilteredByProfession.plumber_token}"}
        
        response = requests.get(f"{API_URL}/jobs/available", headers=headers)
        
        print(f"Plumber available jobs response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "jobs" in data
        assert "profession" in data
        assert data["profession"] == "Plumber"
        
        # Check that plumber sees plumbing jobs
        jobs = data["jobs"]
        print(f"Plumber sees {len(jobs)} jobs")
        
        if len(jobs) > 0:
            # All jobs should be plumber category
            for job in jobs:
                assert "plumber" in job["category"].lower(), f"Expected plumber job, got {job['category']}"
    
    def test_03_electrician_does_not_see_plumbing_job(self):
        """Test that electrician does NOT see plumbing jobs"""
        headers = {"Authorization": f"Bearer {TestJobsFilteredByProfession.electrician_token}"}
        
        response = requests.get(f"{API_URL}/jobs/available", headers=headers)
        
        print(f"Electrician available jobs response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "jobs" in data
        assert "profession" in data
        assert data["profession"] == "Electrician"
        
        # Electrician should NOT see plumbing jobs
        jobs = data["jobs"]
        print(f"Electrician sees {len(jobs)} jobs")
        
        for job in jobs:
            assert "plumber" not in job["category"].lower(), f"Electrician should not see plumber jobs"


class TestAiBidSuggestion:
    """Test AI-powered bid suggestion endpoint"""
    
    client_token = None
    pro_token = None
    job_id = None
    
    @pytest.fixture(autouse=True)
    def setup_users_and_job(self):
        """Setup test users and job"""
        test_uuid = uuid.uuid4().hex[:8]
        
        # Create client
        if not TestAiBidSuggestion.client_token:
            email = f"test_ai_client_{test_uuid}@test.com"
            response = requests.post(f"{API_URL}/auth/register", json={
                "email": email,
                "name": "AI Test Client",
                "phone": "+254712345685",
                "role": "client",
                "location": "Nairobi",
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestAiBidSuggestion.client_token = data["access_token"]
        
        # Create professional
        if not TestAiBidSuggestion.pro_token:
            email = f"test_ai_pro_{test_uuid}@test.com"
            response = requests.post(f"{API_URL}/auth/register", json={
                "email": email,
                "name": "AI Test Pro",
                "phone": "+254712345686",
                "role": "professional",
                "location": "Nairobi",
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestAiBidSuggestion.pro_token = data["access_token"]
                
                # Create profile
                headers = {"Authorization": f"Bearer {data['access_token']}"}
                requests.post(f"{API_URL}/professionals/profile", headers=headers, json={
                    "profession": "Painter",
                    "bio": "Expert painter with 8 years experience",
                    "skills": ["Interior painting", "Exterior painting", "Wallpaper"],
                    "hourly_rate": 400,
                    "pricing_type": "both",
                    "experience_years": 8
                })
        
        # Create job
        if not TestAiBidSuggestion.job_id and TestAiBidSuggestion.client_token:
            headers = {"Authorization": f"Bearer {TestAiBidSuggestion.client_token}"}
            response = requests.post(f"{API_URL}/jobs", headers=headers, json={
                "title": f"Paint living room - TEST_{test_uuid}",
                "description": "Need to paint a 20x15 living room with two coats",
                "category": "Painter",
                "budget": 8000,
                "location": "Nairobi, Karen"
            })
            if response.status_code == 200:
                TestAiBidSuggestion.job_id = response.json()["job"]["id"]
    
    def test_01_get_ai_bid_suggestion(self):
        """Test getting AI-powered bid suggestion"""
        if not TestAiBidSuggestion.job_id or not TestAiBidSuggestion.pro_token:
            pytest.skip("Job or professional not created")
        
        headers = {"Authorization": f"Bearer {TestAiBidSuggestion.pro_token}"}
        
        response = requests.post(
            f"{API_URL}/bids/ai-suggest?job_id={TestAiBidSuggestion.job_id}",
            headers=headers
        )
        
        print(f"AI suggestion response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "suggested_price" in data
        assert "suggested_message" in data
        assert "ai_powered" in data
        
        print(f"AI Suggestion - Price: KSh {data['suggested_price']}, AI Powered: {data['ai_powered']}")
        print(f"Suggested message: {data['suggested_message'][:100]}...")
    
    def test_02_ai_suggestion_requires_profile(self):
        """Test that AI suggestion requires professional profile"""
        # Create a new professional without profile
        email = f"test_noprofile_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{API_URL}/auth/register", json={
            "email": email,
            "name": "No Profile Pro",
            "phone": "+254712345687",
            "role": "professional",
            "location": "Nairobi",
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip("Could not create test user")
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to get AI suggestion without profile
        response = requests.post(
            f"{API_URL}/bids/ai-suggest?job_id={TestAiBidSuggestion.job_id}",
            headers=headers
        )
        
        print(f"AI suggestion without profile response: {response.status_code}")
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "profile" in response.json().get("detail", "").lower()


class TestGeolocationFiltering:
    """Test geolocation filtering for jobs"""
    
    client_token = None
    pro_token = None
    
    @pytest.fixture(autouse=True)
    def setup_users(self):
        """Setup test users"""
        test_uuid = uuid.uuid4().hex[:8]
        
        if not TestGeolocationFiltering.client_token:
            email = f"test_geo_client_{test_uuid}@test.com"
            response = requests.post(f"{API_URL}/auth/register", json={
                "email": email,
                "name": "Geo Test Client",
                "phone": "+254712345688",
                "role": "client",
                "location": "Nairobi, Westlands",
                "latitude": -1.2641,
                "longitude": 36.8034,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                TestGeolocationFiltering.client_token = response.json()["access_token"]
        
        if not TestGeolocationFiltering.pro_token:
            email = f"test_geo_pro_{test_uuid}@test.com"
            response = requests.post(f"{API_URL}/auth/register", json={
                "email": email,
                "name": "Geo Test Pro",
                "phone": "+254712345689",
                "role": "professional",
                "location": "Nairobi, Westlands",
                "latitude": -1.2641,
                "longitude": 36.8034,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestGeolocationFiltering.pro_token = data["access_token"]
                
                # Create profile
                headers = {"Authorization": f"Bearer {data['access_token']}"}
                requests.post(f"{API_URL}/professionals/profile", headers=headers, json={
                    "profession": "Cleaner",
                    "bio": "Professional cleaner",
                    "skills": ["Deep cleaning"],
                    "hourly_rate": 300,
                    "pricing_type": "hourly",
                    "experience_years": 3
                })
    
    def test_01_post_job_with_geolocation(self):
        """Test posting job with geolocation data"""
        headers = {"Authorization": f"Bearer {TestGeolocationFiltering.client_token}"}
        
        response = requests.post(f"{API_URL}/jobs", headers=headers, json={
            "title": f"House cleaning - TEST_{uuid.uuid4().hex[:8]}",
            "description": "Need deep cleaning for 3 bedroom house",
            "category": "Cleaner",
            "budget": 5000,
            "location": "Nairobi, Westlands",
            "latitude": -1.2641,
            "longitude": 36.8034
        })
        
        print(f"Post job with geo response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["job"]["latitude"] == -1.2641
        assert data["job"]["longitude"] == 36.8034
        print("Job posted with geolocation data")
    
    def test_02_available_jobs_include_location_match(self):
        """Test that available jobs include location match info"""
        headers = {"Authorization": f"Bearer {TestGeolocationFiltering.pro_token}"}
        
        response = requests.get(f"{API_URL}/jobs/available", headers=headers)
        
        print(f"Available jobs response: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_location" in data
        print(f"User location: {data['user_location']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
