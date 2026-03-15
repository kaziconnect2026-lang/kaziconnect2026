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

## Features Implemented (February 2026)

### ✅ Core Authentication
- User registration with role selection (client/professional/admin)
- JWT-based login
- Protected routes per role

### ✅ Admin Dashboard (NEW)
- **Overview Tab**:
  - Total Users, Platform Revenue, Total Jobs, Avg Rating stat cards
  - Daily Revenue chart (last 7 days)
  - Daily Bookings chart (last 7 days)
  - Pending Bookings, In Progress, Bid Acceptance Rate, Active Pros cards
  - Top Rated Professionals list
  - Top Earners list
- **Users Tab**:
  - Full user management with search and filter
  - Role-based filtering (All/Clients/Professionals/Admins)
  - Activate/Deactivate users with toggle switches
  - User stats (Clients, Professionals, Active Pros)
- **Financials Tab**:
  - Total Transactions, Platform Revenue, Escrow Balance, Wallet Deposits
  - Booking Status Breakdown (Pending/Confirmed/In Progress/Completed/Cancelled)
  - Bid Statistics (Total/Pending/Accepted/Acceptance Rate)
- **Activity Tab**:
  - Recent Bookings list
  - Recent Jobs Posted list
  - Jobs by Category breakdown
  - New Users chart (last 7 days)

### ✅ Wallet System
- Deposit funds via M-Pesa (MOCKED)
- Withdraw to M-Pesa (MOCKED)
- Real-time balance tracking
- Transaction history

### ✅ Professional Profile
- Create/edit profile with profession, bio, skills, rates
- ID Number field for verification
- Experience years and portfolio
- Availability toggle
- Rating and review tracking

### ✅ Job Filtering by Profession
- Professionals only see jobs matching their category
- Geolocation-based job matching (location priority)

### ✅ Bidding System
- Professionals browse available jobs (filtered by category)
- Submit bids with proposed price, hours, message
- AI Bid Suggestions via Gemini 3 Flash
- Track bid status (pending/accepted/rejected)

### ✅ Client Journey
- Post jobs with title, description, category, budget, location
- View bids received on jobs
- Accept bid (creates booking automatically)
- Make payment (held in escrow)
- Release payment after job completion
- Rate professionals (1-5 stars with comment)
- Re-book professionals from completed bookings

### ✅ Push Notifications
- Subscribe/unsubscribe from push notifications
- Alerts for new jobs in professional's category
- Alerts when bid is accepted
- In-app notification center

### ✅ Earnings Dashboard
- Total earnings tracking
- Pending earnings (in escrow)
- Weekly earnings chart
- Platform commission breakdown (20%)

## API Endpoints

### Admin (NEW)
- `GET /api/admin/stats` - Comprehensive platform statistics
- `GET /api/admin/dashboard` - Dashboard data with charts and recent activity
- `GET /api/admin/users` - List users with search/filter/pagination
- `PUT /api/admin/users/{id}/status` - Activate/deactivate users

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### User Profile
- `PUT /api/users/profile` - Update user profile
- `POST /api/users/profile-photo` - Update profile photo

### Wallet
- `GET /api/wallet/balance` - Get wallet balance
- `GET /api/wallet/transactions` - Get transaction history
- `POST /api/wallet/deposit` - Deposit via M-Pesa (MOCKED)
- `POST /api/wallet/withdraw` - Withdraw to M-Pesa (MOCKED)

### Notifications
- `POST /api/notifications/subscribe` - Subscribe to push
- `DELETE /api/notifications/unsubscribe` - Unsubscribe
- `GET /api/notifications` - Get notifications list
- `PUT /api/notifications/{id}/read` - Mark as read

### Professionals
- `POST /api/professionals/profile` - Create profile
- `GET /api/professionals/profile` - Get own profile
- `PUT /api/professionals/profile` - Update profile
- `PUT /api/professionals/availability` - Toggle availability
- `GET /api/professionals/search` - Search professionals
- `GET /api/professionals/{id}` - Get professional details

### Jobs
- `POST /api/jobs` - Post new job
- `GET /api/jobs` - Get user's jobs
- `GET /api/jobs/available` - Get available jobs (filtered)
- `GET /api/jobs/{id}` - Get job details

### Bids
- `POST /api/bids` - Submit bid
- `POST /api/bids/ai-suggest` - Get AI bid suggestion
- `GET /api/bids/my` - Get own bids
- `GET /api/bids/job/{job_id}` - Get bids for job
- `PUT /api/bids/{id}/accept` - Accept bid
- `PUT /api/bids/{id}/reject` - Reject bid

### Bookings
- `POST /api/bookings` - Create booking
- `POST /api/bookings/rebook/{professional_id}` - Re-book professional
- `GET /api/bookings` - Get user's bookings
- `PUT /api/bookings/{id}/status` - Update status

### Payments
- `POST /api/payments/initiate` - Initiate payment (MOCKED)
- `POST /api/payments/{id}/release` - Release payment
- `GET /api/payments` - Get user's payments

### Reviews
- `POST /api/reviews` - Submit review
- `GET /api/reviews/{professional_id}` - Get professional reviews

### AI Matching
- `POST /api/match` - Get AI-powered professional matches

## Database Collections
- `users` - User accounts (includes wallet_balance, profile_photo)
- `professional_profiles` - Professional details (includes id_number)
- `jobs` - Job postings
- `bids` - Bid submissions
- `bookings` - Service bookings
- `payments` - Payment records
- `reviews` - Client reviews
- `wallet_transactions` - Deposit/withdrawal history
- `push_subscriptions` - Push notification subscriptions
- `notifications` - In-app notifications

## MOCKED APIs
- **M-Pesa Wallet Deposit**: `/api/wallet/deposit` - Instant success
- **M-Pesa Wallet Withdrawal**: `/api/wallet/withdraw` - Instant success
- **M-Pesa Payment**: `/api/payments/initiate` - Goes directly to escrow

## Test Credentials
- **Admin**: admin@kazilinks.com / admin123
- **Client**: client@test.com / password123
- **Professional**: pro@test.com / password123

## Platform Metrics (Current)
- Total Users: 62
- Clients: 27
- Professionals: 32
- Active Professionals: 20
- Platform Revenue: KSh 81,859
- Total Transactions: KSh 409,295
- Escrow Balance: KSh 50,455
- Total Bookings: 35
- Bid Acceptance Rate: 58.3%
- Average Rating: 5/5

## Roadmap (Backlog)

### P1 - High Priority
- Real M-Pesa integration
- Profile photo upload (currently URL only)
- Real push notifications via FCM
- Export reports to CSV/PDF

### P2 - Medium Priority
- In-app messaging/chat
- Portfolio image uploads
- Advanced search filters
- Email notifications
- Service packages

### P3 - Future
- Native mobile app (React Native)
- Subscription plans for professionals
- Multi-language support (Swahili + English)
- Referral program
- Dispute resolution system

## Test Results (Latest)
- **Backend**: 100% (23/23 admin tests passed)
- **Frontend**: 100% (All 4 tabs working)
