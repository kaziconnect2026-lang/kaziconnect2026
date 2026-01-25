# Kazi Links - Product Requirements Document

## Overview
Kazi Links is a PWA marketplace platform connecting clients with skilled professionals (barbers, electricians, plumbers, tattoo artists, etc.) in the East African market. "Kazi" means "work" in Swahili.

## Architecture
- **Frontend**: React with Tailwind CSS, Shadcn UI components
- **Backend**: FastAPI with Python
- **Database**: MongoDB
- **AI**: Gemini 3 Flash for intelligent matching
- **Payments**: M-Pesa integration (MOCKED for demo)

## User Personas
1. **Clients**: Individuals/businesses seeking skilled professionals
2. **Professionals**: Service providers (barbers, electricians, plumbers, etc.)
3. **Admin**: Platform administrators managing users and transactions

## Core Requirements (Static)
- Role-based authentication (Client, Professional, Admin)
- Professional portfolio management
- Job posting and search
- AI-powered matching algorithm
- Booking management system
- M-Pesa escrow payment (20% platform fee)
- Rating and review system
- Location-based search
- Real-time availability toggle

## What's Been Implemented (December 2024)

### Backend APIs
- ✅ User authentication (register, login, JWT tokens)
- ✅ Professional profile CRUD
- ✅ Job posting system
- ✅ Booking management
- ✅ Payment/escrow system (MOCKED M-Pesa)
- ✅ AI matching endpoint (Gemini 3 Flash)
- ✅ Review system
- ✅ Admin statistics and user management
- ✅ Dashboard data endpoints

### Frontend Pages
- ✅ Landing page with categories and search
- ✅ Login/Register with role selection
- ✅ Client Dashboard with quick actions
- ✅ Professional Dashboard with availability toggle
- ✅ Admin Dashboard with statistics, users, transactions
- ✅ Search Professionals with AI matching
- ✅ Professional Profile with booking flow
- ✅ Post Job page
- ✅ Create/Edit Professional Profile
- ✅ Bookings management

### Design System
- ✅ Nairobi Gold (#F59E0B) primary color
- ✅ Rift Valley Slate (#0F172A) secondary
- ✅ Savanna Green (#10B981) accent
- ✅ Outfit + DM Sans typography
- ✅ Mobile-first responsive design
- ✅ PWA manifest for installability

## Prioritized Backlog

### P0 - Critical (MVP Complete)
- ✅ User authentication
- ✅ Professional profiles
- ✅ Job posting
- ✅ Booking system
- ✅ Payment escrow (MOCKED)
- ✅ Admin dashboard

### P1 - High Priority
- [ ] Real M-Pesa integration (Daraja API)
- [ ] Push notifications
- [ ] Dispute resolution system
- [ ] Professional verification badges
- [ ] Location-based filtering with GPS

### P2 - Medium Priority
- [ ] Chat/messaging between client and professional
- [ ] Calendar integration for availability
- [ ] Invoice generation
- [ ] Service history export
- [ ] Multi-language support (Swahili, English)

### P3 - Nice to Have
- [ ] Video portfolio for professionals
- [ ] Group bookings
- [ ] Subscription plans for professionals
- [ ] Referral program
- [ ] Dark mode toggle

## Next Tasks
1. Implement real M-Pesa Daraja API integration
2. Add push notifications for booking updates
3. Build dispute resolution center in admin panel
4. Add professional verification workflow
5. Implement real-time chat feature
