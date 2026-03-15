import requests
import sys
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

class KaziLinksAPITester:
    def __init__(self, base_url="https://local-experts-27.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.client_token = None
        self.professional_token = None
        self.admin_token = None
        self.test_data = {}
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
            self.failed_tests.append(f"{name}: {details}")

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    token: Optional[str] = None, expected_status: int = 200) -> tuple[bool, Dict]:
        """Make HTTP request and return success status and response data"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"status_code": response.status_code, "text": response.text}
            
            return success, response_data

        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, data = self.make_request('GET', '')
        self.log_test("Root endpoint", success and "message" in data, 
                     f"Expected welcome message, got: {data}")
        return success

    def test_categories_endpoint(self):
        """Test categories endpoint"""
        success, data = self.make_request('GET', 'categories')
        categories_valid = success and isinstance(data, list) and len(data) > 0
        if categories_valid:
            # Check if categories have required fields
            first_cat = data[0]
            has_required_fields = all(field in first_cat for field in ['id', 'name', 'icon', 'image'])
            categories_valid = has_required_fields
        
        self.log_test("Categories endpoint", categories_valid, 
                     f"Expected list of categories with required fields, got: {type(data)}")
        return success and categories_valid

    def test_user_registration(self):
        """Test user registration for both client and professional"""
        timestamp = datetime.now().strftime("%H%M%S")
        
        # Test client registration
        client_data = {
            "name": f"Test Client {timestamp}",
            "email": f"client{timestamp}@test.com",
            "phone": "+254712345678",
            "password": "testpass123",
            "role": "client",
            "location": "Nairobi, Kenya"
        }
        
        success, response = self.make_request('POST', 'auth/register', client_data, expected_status=200)
        client_registered = success and "access_token" in response and "user" in response
        
        if client_registered:
            self.client_token = response["access_token"]
            self.test_data["client"] = response["user"]
        
        self.log_test("Client registration", client_registered, 
                     f"Expected token and user data, got: {list(response.keys()) if isinstance(response, dict) else response}")

        # Test professional registration
        prof_data = {
            "name": f"Test Professional {timestamp}",
            "email": f"prof{timestamp}@test.com",
            "phone": "+254712345679",
            "password": "testpass123",
            "role": "professional",
            "location": "Nairobi, Kenya"
        }
        
        success, response = self.make_request('POST', 'auth/register', prof_data, expected_status=200)
        prof_registered = success and "access_token" in response and "user" in response
        
        if prof_registered:
            self.professional_token = response["access_token"]
            self.test_data["professional"] = response["user"]
        
        self.log_test("Professional registration", prof_registered,
                     f"Expected token and user data, got: {list(response.keys()) if isinstance(response, dict) else response}")

        return client_registered and prof_registered

    def test_user_login(self):
        """Test user login"""
        if not self.test_data.get("client"):
            return False
            
        login_data = {
            "email": self.test_data["client"]["email"],
            "password": "testpass123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, expected_status=200)
        login_success = success and "access_token" in response and "user" in response
        
        self.log_test("User login", login_success,
                     f"Expected token and user data, got: {list(response.keys()) if isinstance(response, dict) else response}")
        return login_success

    def test_auth_me_endpoint(self):
        """Test /auth/me endpoint with token"""
        if not self.client_token:
            return False
            
        success, response = self.make_request('GET', 'auth/me', token=self.client_token)
        me_success = success and "id" in response and "email" in response
        
        self.log_test("Auth me endpoint", me_success,
                     f"Expected user data, got: {list(response.keys()) if isinstance(response, dict) else response}")
        return me_success

    def test_professional_profile_creation(self):
        """Test professional profile creation"""
        if not self.professional_token:
            return False
            
        profile_data = {
            "profession": "barber",
            "bio": "Experienced barber with 5+ years of expertise",
            "skills": ["Hair cutting", "Beard trimming", "Hair styling"],
            "hourly_rate": 1500.0,
            "pricing_type": "hourly",
            "experience_years": 5,
            "portfolio_images": ["https://example.com/image1.jpg"]
        }
        
        success, response = self.make_request('POST', 'professionals/profile', 
                                            profile_data, token=self.professional_token, expected_status=200)
        profile_created = success and "message" in response
        
        self.log_test("Professional profile creation", profile_created,
                     f"Expected success message, got: {response}")
        return profile_created

    def test_professional_profile_retrieval(self):
        """Test getting professional profile"""
        if not self.professional_token:
            return False
            
        success, response = self.make_request('GET', 'professionals/profile', 
                                            token=self.professional_token)
        profile_retrieved = success and "profession" in response and "bio" in response
        
        self.log_test("Professional profile retrieval", profile_retrieved,
                     f"Expected profile data, got: {list(response.keys()) if isinstance(response, dict) else response}")
        return profile_retrieved

    def test_search_professionals(self):
        """Test searching professionals"""
        success, response = self.make_request('GET', 'professionals/search')
        search_success = success and isinstance(response, list)
        
        self.log_test("Search professionals", search_success,
                     f"Expected list of professionals, got: {type(response)}")
        return search_success

    def test_job_posting(self):
        """Test job posting by client"""
        if not self.client_token:
            return False
            
        job_data = {
            "title": "Need a professional barber",
            "description": "Looking for an experienced barber for a haircut and beard trim",
            "category": "barber",
            "budget": 2000.0,
            "location": "Nairobi CBD"
        }
        
        success, response = self.make_request('POST', 'jobs', job_data, 
                                            token=self.client_token, expected_status=200)
        job_posted = success and "message" in response and "job" in response
        
        if job_posted:
            self.test_data["job_id"] = response["job"]["id"]
        
        self.log_test("Job posting", job_posted,
                     f"Expected job creation confirmation, got: {response}")
        return job_posted

    def test_get_jobs(self):
        """Test getting jobs"""
        if not self.client_token:
            return False
            
        success, response = self.make_request('GET', 'jobs', token=self.client_token)
        jobs_retrieved = success and isinstance(response, list)
        
        self.log_test("Get jobs", jobs_retrieved,
                     f"Expected list of jobs, got: {type(response)}")
        return jobs_retrieved

    def test_booking_creation(self):
        """Test booking creation"""
        if not self.client_token or not self.test_data.get("professional"):
            return False
            
        booking_data = {
            "professional_id": self.test_data["professional"]["id"],
            "service_description": "Haircut and beard trim",
            "scheduled_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "estimated_hours": 1.5,
            "agreed_price": 2000.0
        }
        
        success, response = self.make_request('POST', 'bookings', booking_data,
                                            token=self.client_token, expected_status=200)
        booking_created = success and "message" in response and "booking" in response
        
        if booking_created:
            self.test_data["booking_id"] = response["booking"]["id"]
        
        self.log_test("Booking creation", booking_created,
                     f"Expected booking confirmation, got: {response}")
        return booking_created

    def test_get_bookings(self):
        """Test getting bookings"""
        if not self.client_token:
            return False
            
        success, response = self.make_request('GET', 'bookings', token=self.client_token)
        bookings_retrieved = success and isinstance(response, list)
        
        self.log_test("Get bookings", bookings_retrieved,
                     f"Expected list of bookings, got: {type(response)}")
        return bookings_retrieved

    def test_payment_initiation(self):
        """Test payment initiation (MOCKED M-Pesa)"""
        if not self.client_token or not self.test_data.get("booking_id"):
            return False
            
        payment_data = {
            "booking_id": self.test_data["booking_id"],
            "phone_number": "+254712345678"
        }
        
        success, response = self.make_request('POST', 'payments/initiate', payment_data,
                                            token=self.client_token, expected_status=200)
        payment_initiated = success and "message" in response and "MOCK" in response.get("note", "")
        
        if payment_initiated:
            self.test_data["payment_id"] = response["payment"]["id"]
        
        self.log_test("Payment initiation (MOCKED)", payment_initiated,
                     f"Expected MOCKED payment confirmation, got: {response}")
        return payment_initiated

    def test_ai_matching(self):
        """Test AI matching functionality"""
        if not self.client_token:
            return False
            
        match_data = {
            "job_description": "I need a skilled barber for a professional haircut",
            "category": "barber",
            "location": "Nairobi",
            "budget": 2000.0
        }
        
        success, response = self.make_request('POST', 'match', match_data,
                                            token=self.client_token, expected_status=200)
        matching_success = success and "matches" in response
        
        self.log_test("AI matching", matching_success,
                     f"Expected matches array, got: {list(response.keys()) if isinstance(response, dict) else response}")
        return matching_success

    def test_client_dashboard(self):
        """Test client dashboard data"""
        if not self.client_token:
            return False
            
        success, response = self.make_request('GET', 'dashboard/client', token=self.client_token)
        dashboard_success = success and isinstance(response, dict)
        
        self.log_test("Client dashboard", dashboard_success,
                     f"Expected dashboard data object, got: {type(response)}")
        return dashboard_success

    def test_professional_dashboard(self):
        """Test professional dashboard data"""
        if not self.professional_token:
            return False
            
        success, response = self.make_request('GET', 'dashboard/professional', token=self.professional_token)
        dashboard_success = success and isinstance(response, dict)
        
        self.log_test("Professional dashboard", dashboard_success,
                     f"Expected dashboard data object, got: {type(response)}")
        return dashboard_success

    def test_availability_toggle(self):
        """Test professional availability toggle"""
        if not self.professional_token:
            return False
            
        success, response = self.make_request('PUT', 'professionals/availability?available=false',
                                            token=self.professional_token)
        toggle_success = success and "availability" in response
        
        self.log_test("Availability toggle", toggle_success,
                     f"Expected availability confirmation, got: {response}")
        return toggle_success

    def create_admin_user(self):
        """Create admin user for testing"""
        timestamp = datetime.now().strftime("%H%M%S")
        admin_data = {
            "name": f"Test Admin {timestamp}",
            "email": f"admin{timestamp}@test.com",
            "phone": "+254712345680",
            "password": "testpass123",
            "role": "admin",
            "location": "Nairobi, Kenya"
        }
        
        success, response = self.make_request('POST', 'auth/register', admin_data, expected_status=200)
        if success and "access_token" in response:
            self.admin_token = response["access_token"]
            return True
        return False

    def test_admin_stats(self):
        """Test admin statistics endpoint"""
        if not self.admin_token:
            if not self.create_admin_user():
                return False
            
        success, response = self.make_request('GET', 'admin/stats', token=self.admin_token)
        stats_success = success and "total_users" in response and "total_revenue" in response
        
        self.log_test("Admin stats", stats_success,
                     f"Expected stats object with totals, got: {list(response.keys()) if isinstance(response, dict) else response}")
        return stats_success

    def test_admin_users(self):
        """Test admin users endpoint"""
        if not self.admin_token:
            return False
            
        success, response = self.make_request('GET', 'admin/users', token=self.admin_token)
        users_success = success and isinstance(response, list)
        
        self.log_test("Admin users", users_success,
                     f"Expected list of users, got: {type(response)}")
        return users_success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Kazi Links API Tests...")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)

        # Basic endpoint tests
        self.test_root_endpoint()
        self.test_categories_endpoint()

        # Authentication tests
        self.test_user_registration()
        self.test_user_login()
        self.test_auth_me_endpoint()

        # Professional profile tests
        self.test_professional_profile_creation()
        self.test_professional_profile_retrieval()
        self.test_search_professionals()
        self.test_availability_toggle()

        # Job and booking tests
        self.test_job_posting()
        self.test_get_jobs()
        self.test_booking_creation()
        self.test_get_bookings()

        # Payment tests (MOCKED)
        self.test_payment_initiation()

        # AI and dashboard tests
        self.test_ai_matching()
        self.test_client_dashboard()
        self.test_professional_dashboard()

        # Admin tests
        self.test_admin_stats()
        self.test_admin_users()

        # Print results
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for failure in self.failed_tests:
                print(f"   • {failure}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✨ Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = KaziLinksAPITester()
    
    try:
        all_passed = tester.run_all_tests()
        return 0 if all_passed else 1
    except Exception as e:
        print(f"💥 Test execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())