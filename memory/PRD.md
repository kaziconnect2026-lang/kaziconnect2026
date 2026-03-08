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
- User registration with role selection (client/professional)
- JWT-based login
- Protected routes per role

### ✅ Wallet System (NEW)
- **Deposit**: Add funds to wallet via M-Pesa (MOCKED)
- **Withdrawal**: Withdraw to M-Pesa (MOCKED)
- **Balance tracking**: Real-time wallet balance
- **Transaction history**: Full deposit/withdrawal history

### ✅ Professional Profile
- Create/edit profile with profession, bio, skills, rates
- **ID Number field**: For verification purposes
- Experience years and portfolio
- Availability toggle
- Rating and review tracking

### ✅ Job Filtering by Profession (NEW)
- Professionals only see jobs matching their category
- Plumber sees plumbing jobs, electrician sees electrician jobs
- Geolocation-based job matching (location priority)

### ✅ Bidding System
- Professionals browse available jobs (filtered by their category)
- Submit bids with proposed price, hours, message
- **AI Bid Suggestions**: Gemini 3 Flash generates competitive bid recommendations
- Track bid status (pending/accepted/rejected)

### ✅ Client Journey
- Post jobs with title, description, category, budget, location
- View bids received on jobs
- Accept bid (creates booking automatically)
- Make payment (held in escrow)
- Release payment after job completion
- Rate professionals (1-5 stars with comment)
- Re-book professionals from completed bookings

### ✅ Push Notifications (NEW)
- Subscribe/unsubscribe from push notifications
- Alerts for new jobs in professional's category
- Alerts when bid is accepted
- In-app notification center

### ✅ Earnings Dashboard
- Total earnings tracking
- Pending earnings (in escrow)
- Weekly earnings chart
- Platform commission breakdown (20%)
- Bid statistics

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### User Profile
- `PUT /api/users/profile` - Update user profile
- `POST /api/users/profile-photo` - Update profile photo

### Wallet (NEW)
- `GET /api/wallet/balance` - Get wallet balance
- `GET /api/wallet/transactions` - Get transaction history
- `POST /api/wallet/deposit` - Deposit via M-Pesa (MOCKED)
- `POST /api/wallet/withdraw` - Withdraw to M-Pesa (MOCKED)

### Notifications (NEW)
- `POST /api/notifications/subscribe` - Subscribe to push
- `DELETE /api/notifications/unsubscribe` - Unsubscribe
- `GET /api/notifications` - Get notifications list
- `PUT /api/notifications/{id}/read` - Mark as read

### Professionals
- `POST /api/professionals/profile` - Create profile (includes id_number)
- `GET /api/professionals/profile` - Get own profile
- `PUT /api/professionals/profile` - Update profile
- `PUT /api/professionals/availability` - Toggle availability
- `GET /api/professionals/search` - Search professionals
- `GET /api/professionals/{id}` - Get professional details

### Jobs
- `POST /api/jobs` - Post new job (sends notifications to matching pros)
- `GET /api/jobs` - Get user's jobs
- `GET /api/jobs/available` - Get available jobs (filtered by profession & location)
- `GET /api/jobs/{id}` - Get job details

### Bids
- `POST /api/bids` - Submit bid
- `POST /api/bids/ai-suggest` - Get AI bid suggestion (NEW)
- `GET /api/bids/my` - Get own bids
- `GET /api/bids/job/{job_id}` - Get bids for job
- `PUT /api/bids/{id}/accept` - Accept bid (sends notification)
- `PUT /api/bids/{id}/reject` - Reject bid

### Bookings
- `POST /api/bookings` - Create booking
- `POST /api/bookings/rebook/{professional_id}` - Re-book professional
- `GET /api/bookings` - Get user's bookings
- `GET /api/bookings/{id}` - Get booking details
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

### Dashboard
- `GET /api/dashboard/client` - Client dashboard data
- `GET /api/dashboard/professional` - Professional dashboard data

## Database Collections
- `users` - User accounts (includes wallet_balance, profile_photo)
- `professional_profiles` - Professional details (includes id_number)
- `jobs` - Job postings
- `bids` - Bid submissions
- `bookings` - Service bookings
- `payments` - Payment records
- `reviews` - Client reviews
- `wallet_transactions` - Deposit/withdrawal history (NEW)
- `push_subscriptions` - Push notification subscriptions (NEW)
- `notifications` - In-app notifications (NEW)

## File Structure
```
/app/
├── backend/
│   ├── server.py - All API endpoints
│   ├── tests/ - Pytest test files
│   ├── .env - Environment variables
│   └── requirements.txt - Python dependencies
└── frontend/
    ├── src/
    │   ├── context/AuthContext.js - Auth state management
    │   ├── pages/
    │   │   ├── LandingPage.js
    │   │   ├── LoginPage.js
    │   │   ├── RegisterPage.js
    │   │   ├── ClientDashboard.js
    │   │   ├── ProfessionalDashboard.js
    │   │   ├── AdminDashboard.js
    │   │   ├── SearchProfessionals.js
    │   │   ├── ProfessionalProfile.js
    │   │   ├── PostJob.js
    │   │   ├── CreateProfile.js (with ID number)
    │   │   ├── Bookings.js
    │   │   ├── AvailableJobs.js (AI suggestions)
    │   │   ├── MyBids.js
    │   │   ├── JobBids.js
    │   │   ├── WalletPage.js (NEW)
    │   │   └── NotificationsPage.js (NEW)
    │   └── components/ui/ - Shadcn components
    └── .env - Frontend environment variables
```

## MOCKED APIs
- **M-Pesa Wallet Deposit**: `/api/wallet/deposit` - Instant success
- **M-Pesa Wallet Withdrawal**: `/api/wallet/withdraw` - Instant success  
- **M-Pesa Payment**: `/api/payments/initiate` - Goes directly to escrow

## Roadmap (Backlog)

### P1 - High Priority
- Admin dashboard implementation
- Real M-Pesa integration
- Profile photo upload (currently URL only)
- Real push notifications via FCM

### P2 - Medium Priority
- In-app messaging/chat between clients and professionals
- Portfolio image uploads
- Advanced search filters
- Email notifications
- Service packages with fixed prices

### P3 - Future
- Native mobile app (React Native)
- Subscription plans for professionals
- Analytics dashboard
- Multi-language support (Swahili + English)
- Referral program
- Dispute resolution system

## Testing
- Backend: pytest with comprehensive API tests
- Frontend: Playwright screenshots and manual testing
- Test reports: `/app/test_reports/iteration_*.json`

## Test Results (Latest)
- **Backend**: 100% (21/21 new feature tests passed)
- **Frontend**: 100% (All major flows working)
