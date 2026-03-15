"""
Test suite for Kazi Links Ledger System
Tests: Display IDs, Wallet transactions with ledger entries, Admin ledger endpoints
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDisplayIDGeneration:
    """Test unique ID generation for clients, professionals, jobs, bookings"""
    
    def test_client_registration_generates_display_id(self):
        """Register a client and verify CL-XXXXX display_id is generated"""
        unique_email = f"TEST_client_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "name": "Test Client Ledger",
            "phone": "+254700000001",
            "role": "client",
            "password": "test123"
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        # Verify display_id format CL-XXXXX
        assert "user" in data
        display_id = data["user"].get("display_id")
        assert display_id is not None, "display_id should be present"
        assert display_id.startswith("CL-"), f"Client display_id should start with CL-, got: {display_id}"
        assert len(display_id) == 8, f"Client display_id should be 8 chars (CL-XXXXX), got: {display_id}"
        print(f"✓ Client registered with display_id: {display_id}")
        
        # Store for cleanup
        self.__class__.test_client_token = data["access_token"]
        self.__class__.test_client_id = data["user"]["id"]
        self.__class__.test_client_display_id = display_id
    
    def test_professional_registration_generates_display_id(self):
        """Register a professional and verify PR-XXXXX display_id is generated"""
        unique_email = f"TEST_pro_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "name": "Test Professional Ledger",
            "phone": "+254700000002",
            "role": "professional",
            "password": "test123"
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        # Verify display_id format PR-XXXXX
        display_id = data["user"].get("display_id")
        assert display_id is not None, "display_id should be present"
        assert display_id.startswith("PR-"), f"Professional display_id should start with PR-, got: {display_id}"
        assert len(display_id) == 8, f"Professional display_id should be 8 chars (PR-XXXXX), got: {display_id}"
        print(f"✓ Professional registered with display_id: {display_id}")
        
        self.__class__.test_pro_token = data["access_token"]
        self.__class__.test_pro_id = data["user"]["id"]


class TestWalletLedgerIntegration:
    """Test wallet operations create proper ledger entries"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client"""
        # Register a test client
        unique_email = f"TEST_wallet_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "name": "Test Wallet User",
            "phone": "+254700000003",
            "role": "client",
            "password": "test123"
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.user_id = data["user"]["id"]
        self.display_id = data["user"]["display_id"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_deposit_creates_ledger_entry(self):
        """Deposit to wallet should create a ledger entry with TXN-XXXXXX"""
        deposit_amount = 5000
        response = requests.post(
            f"{BASE_URL}/api/wallet/deposit",
            json={"amount": deposit_amount, "phone_number": "+254712345678"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Deposit failed: {response.text}"
        data = response.json()
        
        # Verify transaction_id format TXN-XXXXXX
        txn_id = data.get("transaction_id")
        assert txn_id is not None, "transaction_id should be present"
        assert txn_id.startswith("TXN-"), f"Transaction ID should start with TXN-, got: {txn_id}"
        print(f"✓ Deposit created with transaction_id: {txn_id}")
        
        # Verify balance updated
        assert data["new_balance"] == deposit_amount
        
        # Verify ledger entry via /api/ledger/my
        ledger_response = requests.get(f"{BASE_URL}/api/ledger/my", headers=self.headers)
        assert ledger_response.status_code == 200
        ledger_data = ledger_response.json()
        
        # Find the deposit entry
        deposit_entries = [e for e in ledger_data["entries"] if e["entry_type"] == "deposit"]
        assert len(deposit_entries) > 0, "Deposit ledger entry should exist"
        
        latest_deposit = deposit_entries[0]
        assert latest_deposit["amount"] == deposit_amount
        assert latest_deposit["transaction_id"].startswith("TXN-")
        assert latest_deposit["balance_after"] == deposit_amount
        print(f"✓ Ledger entry verified: {latest_deposit['transaction_id']}")
    
    def test_withdrawal_creates_ledger_entry(self):
        """Withdrawal from wallet should create a ledger entry"""
        # First deposit
        requests.post(
            f"{BASE_URL}/api/wallet/deposit",
            json={"amount": 10000, "phone_number": "+254712345678"},
            headers=self.headers
        )
        
        # Then withdraw
        withdrawal_amount = 3000
        response = requests.post(
            f"{BASE_URL}/api/wallet/withdraw",
            json={"amount": withdrawal_amount, "phone_number": "+254712345678"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Withdrawal failed: {response.text}"
        data = response.json()
        
        # Verify transaction_id
        txn_id = data.get("transaction_id")
        assert txn_id is not None
        assert txn_id.startswith("TXN-")
        print(f"✓ Withdrawal created with transaction_id: {txn_id}")
        
        # Verify balance
        assert data["new_balance"] == 7000  # 10000 - 3000
        
        # Verify ledger entry
        ledger_response = requests.get(f"{BASE_URL}/api/ledger/my", headers=self.headers)
        ledger_data = ledger_response.json()
        
        withdrawal_entries = [e for e in ledger_data["entries"] if e["entry_type"] == "withdrawal"]
        assert len(withdrawal_entries) > 0, "Withdrawal ledger entry should exist"
        print(f"✓ Withdrawal ledger entry verified")
    
    def test_insufficient_balance_withdrawal_fails(self):
        """Withdrawal with insufficient balance should fail"""
        response = requests.post(
            f"{BASE_URL}/api/wallet/withdraw",
            json={"amount": 999999, "phone_number": "+254712345678"},
            headers=self.headers
        )
        assert response.status_code == 400
        assert "Insufficient" in response.json().get("detail", "")
        print("✓ Insufficient balance withdrawal correctly rejected")


class TestAdminLedgerEndpoints:
    """Test admin ledger endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@kazilinks.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["access_token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_admin_ledger_returns_entries_with_summary(self):
        """GET /api/admin/ledger should return entries and summary"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ledger?limit=50",
            headers=self.admin_headers
        )
        assert response.status_code == 200, f"Admin ledger failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "entries" in data, "Response should have entries"
        assert "summary" in data, "Response should have summary"
        assert "total" in data, "Response should have total count"
        
        # Verify summary fields
        summary = data["summary"]
        assert "total_deposits" in summary
        assert "total_withdrawals" in summary
        assert "total_escrow_in" in summary
        assert "total_escrow_out" in summary
        assert "total_platform_fees" in summary
        assert "total_professional_payouts" in summary
        assert "entry_counts" in summary
        
        print(f"✓ Admin ledger returned {data['total']} entries")
        print(f"  - Total deposits: KSh {summary['total_deposits']}")
        print(f"  - Total platform fees: KSh {summary['total_platform_fees']}")
    
    def test_admin_ledger_filter_by_type(self):
        """Admin ledger should filter by entry_type"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ledger?entry_type=deposit&limit=50",
            headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # All entries should be deposits
        for entry in data["entries"]:
            assert entry["entry_type"] == "deposit", f"Expected deposit, got {entry['entry_type']}"
        
        print(f"✓ Filter by type working - {len(data['entries'])} deposit entries")
    
    def test_admin_ledger_entries_have_transaction_ids(self):
        """All ledger entries should have TXN-XXXXXX transaction_id"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ledger?limit=20",
            headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for entry in data["entries"]:
            txn_id = entry.get("transaction_id")
            assert txn_id is not None, "Entry should have transaction_id"
            assert txn_id.startswith("TXN-"), f"Transaction ID should start with TXN-, got: {txn_id}"
        
        print(f"✓ All {len(data['entries'])} entries have valid TXN-XXXXXX IDs")
    
    def test_admin_ledger_entries_have_user_info(self):
        """Ledger entries should be enriched with user names and display IDs"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ledger?limit=20",
            headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for entry in data["entries"]:
            # User info should be present (except for platform entries)
            if entry.get("user_id") != "platform":
                assert "user_name" in entry, "Entry should have user_name"
                assert "user_display_id" in entry, "Entry should have user_display_id"
        
        print("✓ Ledger entries enriched with user info")
    
    def test_admin_ledger_user_specific(self):
        """GET /api/admin/ledger/user/{id} should return user-specific ledger"""
        # First get a user ID from the ledger
        response = requests.get(
            f"{BASE_URL}/api/admin/ledger?limit=5",
            headers=self.admin_headers
        )
        data = response.json()
        
        if data["entries"]:
            user_id = data["entries"][0].get("user_id")
            if user_id and user_id != "platform":
                user_ledger_response = requests.get(
                    f"{BASE_URL}/api/admin/ledger/user/{user_id}",
                    headers=self.admin_headers
                )
                assert user_ledger_response.status_code == 200
                user_data = user_ledger_response.json()
                
                assert "user" in user_data
                assert "entries" in user_data
                assert "summary" in user_data
                
                # Summary should have credits/debits
                assert "total_credits" in user_data["summary"]
                assert "total_debits" in user_data["summary"]
                assert "net_balance" in user_data["summary"]
                
                print(f"✓ User-specific ledger working for user {user_id}")
    
    def test_admin_ledger_requires_admin_role(self):
        """Non-admin users should get 403 on admin ledger endpoints"""
        # Register a regular client
        unique_email = f"TEST_nonadmin_{uuid.uuid4().hex[:8]}@test.com"
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "name": "Non Admin User",
            "phone": "+254700000099",
            "role": "client",
            "password": "test123"
        })
        client_token = reg_response.json()["access_token"]
        client_headers = {"Authorization": f"Bearer {client_token}"}
        
        # Try to access admin ledger
        response = requests.get(
            f"{BASE_URL}/api/admin/ledger",
            headers=client_headers
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Admin ledger correctly requires admin role")


class TestUserLedgerEndpoint:
    """Test user's own ledger endpoint"""
    
    def test_user_can_view_own_ledger(self):
        """GET /api/ledger/my should return user's ledger entries"""
        # Register and deposit
        unique_email = f"TEST_myled_{uuid.uuid4().hex[:8]}@test.com"
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "name": "My Ledger User",
            "phone": "+254700000088",
            "role": "client",
            "password": "test123"
        })
        token = reg_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make a deposit
        requests.post(
            f"{BASE_URL}/api/wallet/deposit",
            json={"amount": 2500, "phone_number": "+254712345678"},
            headers=headers
        )
        
        # Get my ledger
        response = requests.get(f"{BASE_URL}/api/ledger/my", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "entries" in data
        assert "summary" in data
        assert len(data["entries"]) > 0
        
        # Verify summary
        assert "total_credits" in data["summary"]
        assert "total_debits" in data["summary"]
        assert "current_balance" in data["summary"]
        
        print(f"✓ User ledger returned {len(data['entries'])} entries")
        print(f"  - Credits: KSh {data['summary']['total_credits']}")
        print(f"  - Current balance: KSh {data['summary']['current_balance']}")


class TestJobAndBookingDisplayIDs:
    """Test job and booking display ID generation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup client and professional"""
        # Register client
        client_email = f"TEST_jobclient_{uuid.uuid4().hex[:8]}@test.com"
        client_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": client_email,
            "name": "Job Test Client",
            "phone": "+254700000010",
            "role": "client",
            "password": "test123"
        })
        self.client_token = client_response.json()["access_token"]
        self.client_headers = {"Authorization": f"Bearer {self.client_token}"}
        
        # Register professional
        pro_email = f"TEST_jobpro_{uuid.uuid4().hex[:8]}@test.com"
        pro_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": pro_email,
            "name": "Job Test Pro",
            "phone": "+254700000011",
            "role": "professional",
            "password": "test123"
        })
        self.pro_token = pro_response.json()["access_token"]
        self.pro_id = pro_response.json()["user"]["id"]
        self.pro_headers = {"Authorization": f"Bearer {self.pro_token}"}
        
        # Create professional profile
        requests.post(f"{BASE_URL}/api/professionals/profile", json={
            "profession": "Electrician",
            "bio": "Test electrician",
            "skills": ["wiring", "repairs"],
            "hourly_rate": 500,
            "pricing_type": "hourly",
            "experience_years": 3
        }, headers=self.pro_headers)
    
    def test_job_creation_generates_display_id(self):
        """Job creation should generate JOB-XXXXX display_id"""
        response = requests.post(f"{BASE_URL}/api/jobs", json={
            "title": "Test Electrical Work",
            "description": "Need electrical repairs",
            "category": "Electrician",
            "budget": 5000,
            "location": "Nairobi"
        }, headers=self.client_headers)
        
        assert response.status_code == 200, f"Job creation failed: {response.text}"
        data = response.json()
        
        job = data.get("job", {})
        display_id = job.get("display_id")
        assert display_id is not None, "Job should have display_id"
        assert display_id.startswith("JOB-"), f"Job display_id should start with JOB-, got: {display_id}"
        print(f"✓ Job created with display_id: {display_id}")
        
        self.__class__.job_id = job["id"]
    
    def test_booking_creation_generates_display_id(self):
        """Booking creation should generate BK-XXXXX display_id"""
        response = requests.post(f"{BASE_URL}/api/bookings", json={
            "professional_id": self.pro_id,
            "service_description": "Test booking service",
            "scheduled_date": "2026-02-01T10:00:00Z",
            "agreed_price": 3000
        }, headers=self.client_headers)
        
        assert response.status_code == 200, f"Booking creation failed: {response.text}"
        data = response.json()
        
        booking = data.get("booking", {})
        display_id = booking.get("display_id")
        assert display_id is not None, "Booking should have display_id"
        assert display_id.startswith("BK-"), f"Booking display_id should start with BK-, got: {display_id}"
        print(f"✓ Booking created with display_id: {display_id}")


class TestPaymentLedgerFlow:
    """Test payment flow creates proper ledger entries"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup client, professional, and booking"""
        # Register client
        client_email = f"TEST_payclient_{uuid.uuid4().hex[:8]}@test.com"
        client_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": client_email,
            "name": "Payment Test Client",
            "phone": "+254700000020",
            "role": "client",
            "password": "test123"
        })
        self.client_token = client_response.json()["access_token"]
        self.client_id = client_response.json()["user"]["id"]
        self.client_headers = {"Authorization": f"Bearer {self.client_token}"}
        
        # Register professional
        pro_email = f"TEST_paypro_{uuid.uuid4().hex[:8]}@test.com"
        pro_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": pro_email,
            "name": "Payment Test Pro",
            "phone": "+254700000021",
            "role": "professional",
            "password": "test123"
        })
        self.pro_token = pro_response.json()["access_token"]
        self.pro_id = pro_response.json()["user"]["id"]
        self.pro_headers = {"Authorization": f"Bearer {self.pro_token}"}
        
        # Create professional profile
        requests.post(f"{BASE_URL}/api/professionals/profile", json={
            "profession": "Plumber",
            "bio": "Test plumber",
            "skills": ["plumbing", "repairs"],
            "hourly_rate": 600,
            "pricing_type": "hourly",
            "experience_years": 5
        }, headers=self.pro_headers)
        
        # Create booking
        booking_response = requests.post(f"{BASE_URL}/api/bookings", json={
            "professional_id": self.pro_id,
            "service_description": "Plumbing repair",
            "scheduled_date": "2026-02-15T14:00:00Z",
            "agreed_price": 5000
        }, headers=self.client_headers)
        self.booking_id = booking_response.json()["booking"]["id"]
        self.booking_display_id = booking_response.json()["booking"].get("display_id")
    
    def test_payment_initiation_creates_escrow_ledger_entry(self):
        """Payment initiation should create escrow_in ledger entry"""
        response = requests.post(f"{BASE_URL}/api/payments/initiate", json={
            "booking_id": self.booking_id,
            "phone_number": "+254712345678"
        }, headers=self.client_headers)
        
        assert response.status_code == 200, f"Payment initiation failed: {response.text}"
        data = response.json()
        
        payment = data.get("payment", {})
        payment_display_id = payment.get("display_id")
        assert payment_display_id is not None, "Payment should have display_id"
        assert payment_display_id.startswith("PAY-"), f"Payment display_id should start with PAY-, got: {payment_display_id}"
        print(f"✓ Payment initiated with display_id: {payment_display_id}")
        
        # Verify escrow_in ledger entry via admin
        admin_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@kazilinks.com",
            "password": "admin123"
        })
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        ledger_response = requests.get(
            f"{BASE_URL}/api/admin/ledger?entry_type=escrow_in&limit=10",
            headers=admin_headers
        )
        ledger_data = ledger_response.json()
        
        # Find our escrow entry
        escrow_entries = [e for e in ledger_data["entries"] if e.get("reference_id") == payment_display_id]
        assert len(escrow_entries) > 0, "Escrow_in ledger entry should exist"
        print(f"✓ Escrow_in ledger entry created")
        
        self.__class__.payment_id = payment["id"]
        self.__class__.admin_headers = admin_headers
    
    def test_payment_release_creates_multiple_ledger_entries(self):
        """Payment release should create escrow_out, platform_fee, professional_payout entries"""
        # First initiate payment
        init_response = requests.post(f"{BASE_URL}/api/payments/initiate", json={
            "booking_id": self.booking_id,
            "phone_number": "+254712345678"
        }, headers=self.client_headers)
        payment_id = init_response.json()["payment"]["id"]
        payment_display_id = init_response.json()["payment"]["display_id"]
        
        # Release payment
        release_response = requests.post(
            f"{BASE_URL}/api/payments/{payment_id}/release",
            headers=self.client_headers
        )
        assert release_response.status_code == 200, f"Payment release failed: {release_response.text}"
        print(f"✓ Payment released")
        
        # Verify ledger entries via admin
        admin_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@kazilinks.com",
            "password": "admin123"
        })
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        ledger_response = requests.get(
            f"{BASE_URL}/api/admin/ledger?limit=50",
            headers=admin_headers
        )
        ledger_data = ledger_response.json()
        
        # Find entries related to this payment
        related_entries = [e for e in ledger_data["entries"] if e.get("reference_id") == payment_display_id]
        entry_types = [e["entry_type"] for e in related_entries]
        
        # Should have escrow_out, platform_fee, professional_payout
        assert "escrow_out" in entry_types, "Should have escrow_out entry"
        assert "platform_fee" in entry_types, "Should have platform_fee entry"
        assert "professional_payout" in entry_types, "Should have professional_payout entry"
        
        print(f"✓ Payment release created ledger entries: {entry_types}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
