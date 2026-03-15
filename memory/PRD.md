# Kazi Links - Product Requirements Document

## Original Problem Statement
Build a platform named "Kazi Links" where clients can find and hire skilled professionals like barbers, electricians, and plumbers based on location, proximity, and ratings.

## Technology Stack
- **Frontend**: React (Progressive Web App), TailwindCSS, Shadcn/UI
- **Backend**: FastAPI, MongoDB
- **Authentication**: JWT (JSON Web Tokens)
- **AI**: Gemini 3 Flash for professional matching & bid suggestions (via Emergent LLM Key)
- **Payments**: M-Pesa with escrow (MOCKED for demo)

## Platform Commission
- **20% platform fee** on all transactions
- Professionals receive 80% of agreed price
- Funds held in escrow until job completion

## Identification System (NEW)
All entities have unique display IDs for easy reference:
- **Clients**: `CL-XXXXX` (e.g., CL-00001)
- **Professionals**: `PR-XXXXX` (e.g., PR-00001)
- **Jobs**: `JOB-XXXXX` (e.g., JOB-00001)
- **Bookings**: `BK-XXXXX` (e.g., BK-00001)
- **Payments**: `PAY-XXXXX` (e.g., PAY-00001)
- **Transactions**: `TXN-XXXXXX` (e.g., TXN-000001)

## Ledger System (NEW)
Comprehensive financial tracking with synchronized wallet operations:

### Ledger Entry Types
- `deposit`: User deposits to wallet via M-Pesa
- `withdrawal`: User withdraws from wallet to M-Pesa
- `escrow_in`: Client pays for booking (funds held in escrow)
- `escrow_out`: Payment released from escrow
- `platform_fee`: Platform commission (20%) deducted
- `professional_payout`: Professional receives payment

### Ledger Entry Fields
- `transaction_id`: Unique ID (TXN-XXXXXX)
- `entry_type`: Type of transaction
- `user_id` / `user_display_id`: User making transaction
- `related_user_id`: Related party (for payments)
- `amount`: Transaction amount
- `balance_before` / `balance_after`: Wallet balance tracking
- `description`: Human-readable description
- `reference_id` / `reference_type`: Link to source transaction
- `metadata`: Additional context (phone numbers, refs, etc.)
- `created_at`: Timestamp

## Professional Categories (NEW - 121 Categories in 15 Groups)

### Category Groups
1. **Home Services** (12): Cleaner, Window Cleaner, Carpet Cleaner, Laundry Washer, Swimming Pool Cleaner, Landscaper/Gardener, Painter, Interior Decorator, Plastering Specialist, Tiler, Welder, Borehole Drilling Expert
2. **Repair & Technical** (11): TV/Phone/Laptop/Electronics Repair, Sound System/CCTV/Solar/WiFi Installer, Cable/Appliance/Generator Technician
3. **Construction & Handyman** (8): Mason/Fundi, Carpenter, Foreman, Plumber, Electrician, Roofing Specialist, Steel Fixer, Construction Manager
4. **Education & Tutoring** (9): English/Math/Kiswahili Tutors, Primary/High School/University Tutors, Academic/Proposal Writers, Research Assistant
5. **Creative & Media** (12): Video Director, Script Writer, Videographer, Photographer, Cameraman, Lighting Technician, Makeup Artist, Content Creator, Influencer, Graphic Designer, Animator, Voice Over Artist
6. **Event & Entertainment** (9): Event Planner, DJ, Comedian, MC/Host, Caterer, Private Chef, Waiter, Wedding Planner, Event Decorator
7. **Transport & Delivery** (9): Courier, Delivery Rider, Bodaboda Rider, Personal/Truck/Bus/Taxi Driver, Tour Guide, Movers
8. **Automotive Services** (5): Car/Motorcycle Mechanic, Tire Repair, Car Electrician, Car Wash
9. **Health & Wellness** (8): Nutritionist, Diet Planner, Personal/Boxing/Karate Trainer, Physiotherapist, Nurse, Dentist
10. **Beauty & Personal Care** (6): Hairdresser, Nail Technician, Barber, Massage Therapist, Hina Artist, Tattoo Artist
11. **Technology & Digital** (9): Web/Mobile App/Software Developer, AI Specialist, Data Scientist, Prompt Engineer, Cybersecurity Specialist, IT Support, Cloud Engineer
12. **Business & Professional** (9): Financial Auditor, Accountant, Business Consultant, Digital Marketer, Market Researcher/Analyst, Real Estate Agent, Cleaning Agency, Property Manager
13. **Security Services** (4): Bodyguard, Security Guard, Private Investigator, Dog Trainer
14. **Domestic Services** (4): Housemaid/House Helper, Chef, Nanny, Elderly Caregiver
15. **Film Production Crew** (6): Director, Producer, Cameraman, Lighting Technician, Film Extras, Transport Crew

### API Endpoints
- `GET /api/categories` - All 121 categories (flat list)
- `GET /api/categories/grouped` - Categories organized by group
- `GET /api/categories/featured` - 8 featured categories with images for landing page

## Features Implemented

### ✅ Core Authentication
- User registration with role selection (client/professional/admin)
- Automatic display ID generation (CL-/PR-/ADM-)
- JWT-based login
- Protected routes per role

### ✅ Wallet System with Ledger Integration
- Deposit funds via M-Pesa (MOCKED) - creates ledger entry
- Withdraw to M-Pesa (MOCKED) - creates ledger entry
- Real-time balance tracking with before/after
- Full transaction history with TXN-XXXXXX IDs
- User can view own ledger via `/api/ledger/my`

### ✅ Admin Dashboard
- **Overview Tab**: Stats, charts, top performers
- **Users Tab**: User management with search/filter/toggle
- **Financials Tab**: Transaction breakdown, bid statistics
- **Activity Tab**: Recent events
- **Ledger Link**: Navigate to full ledger view

### ✅ Admin Ledger Page (NEW)
- Summary cards: Deposits, Withdrawals, Escrow In/Out, Platform Fees, Pro Payouts
- Transaction table with all ledger entries
- Search by ID, user, description
- Filter by entry type
- User display IDs visible throughout
- Amount color coding (green for credits, red for debits)

### ✅ Professional Profile
- Create/edit profile with profession, bio, skills, rates
- ID Number field for verification
- Experience years and portfolio
- Availability toggle
- **Profile photo upload** (NEW) - Upload profile photo from CreateProfile page

### ✅ Client Profile Page (NEW)
- View and edit personal information (name, phone, location)
- Profile photo upload with camera button
- Stats display (jobs posted, bookings, total spent)
- Member since date
- Quick links to wallet and bookings
- Edit mode toggle with save/cancel
- Accessible from sidebar navigation at `/client/profile`

### ✅ Job System
- Jobs get unique display IDs (JOB-XXXXX)
- Filtered by professional's category
- Geolocation-based matching

### ✅ Bidding System
- AI-powered bid suggestions via Gemini 3 Flash
- Track bid status

### ✅ Booking & Payment Flow
- Bookings get unique display IDs (BK-XXXXX)
- Payments get unique display IDs (PAY-XXXXX)
- Payment initiation creates `escrow_in` ledger entry
- Payment release creates 3 ledger entries:
  - `escrow_out`: Releases funds from escrow
  - `platform_fee`: 20% commission to platform
  - `professional_payout`: 80% to professional's wallet

### ✅ Push Notifications
- Alerts for new jobs and bid acceptance
- In-app notification center

## API Endpoints

### Ledger (NEW)
- `GET /api/admin/ledger` - Full ledger with filters (admin only)
- `GET /api/admin/ledger/user/{user_id}` - User-specific ledger (admin only)
- `GET /api/ledger/my` - Current user's ledger entries

### Admin
- `GET /api/admin/stats` - Platform statistics
- `GET /api/admin/dashboard` - Dashboard data with charts
- `GET /api/admin/users` - User management
- `PUT /api/admin/users/{id}/status` - Activate/deactivate users
- `GET /api/admin/transactions` - All payments

### Authentication
- `POST /api/auth/register` - Registration (generates display_id)
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Current user (includes display_id)

### User Profile (NEW)
- `PUT /api/users/profile` - Update user profile (name, phone, location)
- `POST /api/users/profile-photo` - Upload profile photo (base64 or URL)

### Wallet
- `GET /api/wallet/balance` - Get balance
- `GET /api/wallet/transactions` - Transaction history
- `POST /api/wallet/deposit` - Deposit (creates ledger entry)
- `POST /api/wallet/withdraw` - Withdraw (creates ledger entry)

### Jobs, Bookings, Payments
- All create operations generate display IDs
- Payment operations create corresponding ledger entries

## Database Collections
- `users` - User accounts (includes display_id, wallet_balance)
- `professional_profiles` - Professional details (includes id_number)
- `jobs` - Job postings (includes display_id)
- `bids` - Bid submissions
- `bookings` - Bookings (includes display_id)
- `payments` - Payments (includes display_id)
- `reviews` - Client reviews
- `wallet_transactions` - Wallet deposit/withdrawal records
- `ledger` - **NEW**: Complete financial ledger
- `push_subscriptions` - Push notification subscriptions
- `notifications` - In-app notifications

## MOCKED APIs
All M-Pesa operations are mocked with instant success:
- Wallet Deposit: Creates ledger entry immediately
- Wallet Withdrawal: Creates ledger entry immediately
- Payment Initiation: Creates escrow_in ledger entry immediately
- Payment Release: Creates escrow_out, platform_fee, professional_payout entries

## Test Results (Latest - March 2026)
- **Backend**: 100% (14/14 profile tests passed)
- **Frontend**: 100% (All profile UI elements working)

## Test Credentials
- **Admin**: admin@kazilinks.com / admin123
- **Client**: client@test.com / password
- **Professional**: pro@test.com / password

## Ledger Summary Observed
- Total Deposits: KSh 22,500
- Total Withdrawals: KSh 3,000
- Total Escrow In: KSh 10,000
- Total Escrow Out: KSh 5,000
- Total Platform Fees: KSh 1,000
- Total Pro Payouts: KSh 4,000

## Roadmap (Backlog)

### P0 - Critical (Refactoring)
- Backend `server.py` refactoring (2000+ lines) into modular structure:
  - `/app/backend/routes/` - API endpoints
  - `/app/backend/models/` - Pydantic models
  - `/app/backend/services/` - Business logic

### P1 - High Priority
- Real M-Pesa integration (deposits)
- Export ledger to CSV/PDF
- Real push notifications via FCM
- ID photo upload for professional verification

### P2 - Medium Priority
- In-app messaging/chat
- Email notifications
- Advanced reporting
- Map-based geolocation search

### P3 - Future
- Native mobile app
- Multi-language support
- Dispute resolution system
