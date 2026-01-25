# Kazi Links - Product Requirements Document

## Original Problem Statement
Build a platform named "Kazi Links" where clients can find and hire skilled professionals like barbers, electricians, and plumbers based on location, proximity, and ratings.

## Technology Stack
- **Frontend**: React (Progressive Web App), TailwindCSS, Shadcn/UI
- **Backend**: FastAPI, MongoDB
- **Authentication**: JWT (JSON Web Tokens)
- **AI**: Gemini 3 Flash for professional matching (via Emergent LLM Key)
- **Payments**: M-Pesa with escrow (MOCKED for demo)

## Platform Commission
- **20% platform fee** on all transactions
- Professionals receive 80% of agreed price
- Funds held in escrow until job completion

## User Roles

### Clients
- Register and login
- Post jobs with category, budget, location
- Search professionals by category, rating
- Use AI matching to find best professionals
- View and accept/reject bids from professionals
- Make payments (escrow)
- Release payment on job completion
- Rate and review professionals
- Re-book professionals from completed jobs

### Professionals
- Register and create profile
- Set skills, bio, hourly/project rates
- Browse available jobs
- Submit bids with proposed price and message
- Track submitted bids (pending/accepted/rejected)
- Manage bookings
- Start work and mark jobs complete
- View earnings dashboard with:
  - Total earnings
  - Pending earnings
  - Weekly earnings chart
  - Platform commission breakdown

### Admin
- Platform oversight
- User management
- Transaction monitoring

## Features Implemented (January 2026)

### ✅ Core Authentication
- User registration with role selection (client/professional)
- JWT-based login
- Protected routes per role

### ✅ Client Journey
- Post jobs with title, description, category, budget, location
- View bids received on jobs
- Accept bid (creates booking automatically)
- Make payment (held in escrow)
- Release payment after job completion
- Rate professionals (1-5 stars with comment)
- Re-book professionals from completed bookings

### ✅ Professional Journey
- Create profile with profession, bio, skills, rates
- Browse available jobs by category
- Submit bids with proposed price, estimated hours, message
- Track bid status (pending/accepted/rejected)
- Manage bookings (start work, mark complete)
- View earnings dashboard with weekly chart
- See platform commission breakdown

### ✅ AI Matching
- Gemini 3 Flash integration for intelligent professional matching
- Considers skills, rating, experience, location, pricing
- Returns match scores with reasons

### ✅ Payment System (MOCKED)
- M-Pesa STK push simulation
- Escrow system
- Payment release to professionals
- Commission calculation

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Categories
- `GET /api/categories` - List professional categories

### Professionals
- `POST /api/professionals/profile` - Create profile
- `GET /api/professionals/profile` - Get own profile
- `PUT /api/professionals/profile` - Update profile
- `PUT /api/professionals/availability` - Toggle availability
- `GET /api/professionals/search` - Search professionals
- `GET /api/professionals/{id}` - Get professional details

### Jobs
- `POST /api/jobs` - Post new job (client)
- `GET /api/jobs` - Get user's jobs
- `GET /api/jobs/available` - Get available jobs (professional)
- `GET /api/jobs/{id}` - Get job details

### Bids
- `POST /api/bids` - Submit bid (professional)
- `GET /api/bids/my` - Get own bids (professional)
- `GET /api/bids/job/{job_id}` - Get bids for job (client)
- `PUT /api/bids/{id}/accept` - Accept bid (client)
- `PUT /api/bids/{id}/reject` - Reject bid (client)

### Bookings
- `POST /api/bookings` - Create booking
- `POST /api/bookings/rebook/{professional_id}` - Re-book professional
- `GET /api/bookings` - Get user's bookings
- `PUT /api/bookings/{id}/status` - Update booking status

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

### Admin
- `GET /api/admin/stats` - Platform statistics
- `GET /api/admin/users` - All users
- `GET /api/admin/transactions` - All transactions

## Database Collections
- `users` - User accounts
- `professional_profiles` - Professional details
- `jobs` - Job postings
- `bids` - Bid submissions
- `bookings` - Service bookings
- `payments` - Payment records
- `reviews` - Client reviews

## File Structure
```
/app/
├── backend/
│   ├── server.py - All API endpoints
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
    │   │   ├── CreateProfile.js
    │   │   ├── Bookings.js
    │   │   ├── AvailableJobs.js - Professional job browsing
    │   │   ├── MyBids.js - Professional bid tracking
    │   │   └── JobBids.js - Client views bids
    │   └── components/ui/ - Shadcn components
    └── .env - Frontend environment variables
```

## Roadmap (Backlog)

### P1 - High Priority
- Admin dashboard implementation
- Real M-Pesa integration
- Location-based search with geolocation
- Push notifications

### P2 - Medium Priority
- Chat/messaging between clients and professionals
- Portfolio image uploads
- Advanced search filters
- Email notifications

### P3 - Future
- Native mobile app (React Native)
- Subscription plans for professionals
- Analytics dashboard
- Multi-language support

## Testing
- Backend: pytest with comprehensive API tests
- Frontend: Manual testing with Playwright screenshots
- Test reports: `/app/test_reports/iteration_*.json`

## MOCKED APIs
- **M-Pesa Payment**: `/api/payments/initiate` - STK push is mocked, payments go directly to escrow status
