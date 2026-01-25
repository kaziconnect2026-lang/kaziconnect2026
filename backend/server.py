from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from enum import Enum
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'kazi-links-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Emergent LLM Key for AI matching
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Create the main app
app = FastAPI(title="Kazi Links API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============= ENUMS =============
class UserRole(str, Enum):
    CLIENT = "client"
    PROFESSIONAL = "professional"
    ADMIN = "admin"

class JobStatus(str, Enum):
    OPEN = "open"
    MATCHED = "matched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    ESCROW = "escrow"
    RELEASED = "released"
    REFUNDED = "refunded"

class PricingType(str, Enum):
    HOURLY = "hourly"
    PROJECT = "project"
    BOTH = "both"

# ============= MODELS =============
class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: str
    role: UserRole
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: str
    role: UserRole
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    is_active: bool = True

class BidStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class Bid(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    professional_id: str
    proposed_price: float
    message: str
    estimated_hours: Optional[float] = None
    status: BidStatus = BidStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BidCreate(BaseModel):
    job_id: str
    proposed_price: float
    message: str
    estimated_hours: Optional[float] = None

class ProfessionalProfile(BaseModel):
    user_id: str
    profession: str
    bio: str
    skills: List[str]
    hourly_rate: Optional[float] = None
    project_rate_min: Optional[float] = None
    project_rate_max: Optional[float] = None
    pricing_type: PricingType
    experience_years: int
    portfolio_images: List[str] = []
    availability: bool = True
    rating: float = 0.0
    total_reviews: int = 0
    total_jobs: int = 0
    total_earnings: float = 0.0

class ProfessionalProfileCreate(BaseModel):
    profession: str
    bio: str
    skills: List[str]
    hourly_rate: Optional[float] = None
    project_rate_min: Optional[float] = None
    project_rate_max: Optional[float] = None
    pricing_type: PricingType
    experience_years: int
    portfolio_images: List[str] = []

class JobPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    title: str
    description: str
    category: str
    budget: float
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: JobStatus = JobStatus.OPEN
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    matched_professional_id: Optional[str] = None

class JobPostCreate(BaseModel):
    title: str
    description: str
    category: str
    budget: float
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    professional_id: str
    job_id: Optional[str] = None
    service_description: str
    scheduled_date: datetime
    estimated_hours: Optional[float] = None
    agreed_price: float
    status: BookingStatus = BookingStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class BookingCreate(BaseModel):
    professional_id: str
    job_id: Optional[str] = None
    service_description: str
    scheduled_date: datetime
    estimated_hours: Optional[float] = None
    agreed_price: float

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: str
    client_id: str
    professional_id: str
    amount: float
    platform_fee: float
    professional_amount: float
    status: PaymentStatus = PaymentStatus.PENDING
    mpesa_transaction_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    released_at: Optional[datetime] = None

class PaymentCreate(BaseModel):
    booking_id: str
    phone_number: str

class Review(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: str
    client_id: str
    professional_id: str
    rating: int
    comment: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReviewCreate(BaseModel):
    booking_id: str
    professional_id: str
    rating: int
    comment: str

class MatchRequest(BaseModel):
    job_description: str
    category: str
    location: str
    budget: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ============= HELPER FUNCTIONS =============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, role: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_role(required_roles: List[UserRole]):
    async def role_checker(user = Depends(get_current_user)):
        if user["role"] not in [r.value for r in required_roles]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

# ============= PROFESSIONAL CATEGORIES =============
PROFESSIONAL_CATEGORIES = [
    {"id": "barber", "name": "Barber", "icon": "scissors", "image": "https://images.unsplash.com/photo-1599641078447-229873aedbc8?crop=entropy&cs=srgb&fm=jpg&q=85"},
    {"id": "electrician", "name": "Electrician", "icon": "zap", "image": "https://images.unsplash.com/photo-1621905252507-b35492cc74b4?crop=entropy&cs=srgb&fm=jpg&q=85"},
    {"id": "plumber", "name": "Plumber", "icon": "droplet", "image": "https://images.pexels.com/photos/8486978/pexels-photo-8486978.jpeg"},
    {"id": "tattoo_artist", "name": "Tattoo Artist", "icon": "pen-tool", "image": "https://images.unsplash.com/photo-1753259789341-808371092e19?crop=entropy&cs=srgb&fm=jpg&q=85"},
    {"id": "mechanic", "name": "Mechanic", "icon": "wrench", "image": "https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?crop=entropy&cs=srgb&fm=jpg&q=85"},
    {"id": "painter", "name": "Painter", "icon": "paintbrush", "image": "https://images.unsplash.com/photo-1562259949-e8e7689d7828?crop=entropy&cs=srgb&fm=jpg&q=85"},
    {"id": "carpenter", "name": "Carpenter", "icon": "hammer", "image": "https://images.unsplash.com/photo-1504148455328-c376907d081c?crop=entropy&cs=srgb&fm=jpg&q=85"},
    {"id": "cleaner", "name": "Cleaner", "icon": "sparkles", "image": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?crop=entropy&cs=srgb&fm=jpg&q=85"},
]

# ============= ROOT ENDPOINT =============
# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Welcome to Kazi Links API"}

# ============= AUTH ENDPOINTS =============
@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if email exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "phone": user_data.phone,
        "role": user_data.role.value,
        "location": user_data.location,
        "latitude": user_data.latitude,
        "longitude": user_data.longitude,
        "password_hash": hash_password(user_data.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, user_data.role.value)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=user_data.email,
            name=user_data.name,
            phone=user_data.phone,
            role=user_data.role,
            location=user_data.location,
            latitude=user_data.latitude,
            longitude=user_data.longitude,
            created_at=datetime.now(timezone.utc)
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["role"])
    
    created_at = user.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            phone=user["phone"],
            role=UserRole(user["role"]),
            location=user.get("location"),
            latitude=user.get("latitude"),
            longitude=user.get("longitude"),
            created_at=created_at
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user = Depends(get_current_user)):
    created_at = user.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        phone=user["phone"],
        role=UserRole(user["role"]),
        location=user.get("location"),
        latitude=user.get("latitude"),
        longitude=user.get("longitude"),
        created_at=created_at
    )

# ============= CATEGORIES ENDPOINT =============
@api_router.get("/categories")
async def get_categories():
    return PROFESSIONAL_CATEGORIES

# ============= PROFESSIONAL PROFILE ENDPOINTS =============
@api_router.post("/professionals/profile")
async def create_professional_profile(profile_data: ProfessionalProfileCreate, user = Depends(get_current_user)):
    if user["role"] != "professional":
        raise HTTPException(status_code=403, detail="Only professionals can create profiles")
    
    existing = await db.professional_profiles.find_one({"user_id": user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    profile_doc = {
        "user_id": user["id"],
        **profile_data.model_dump(),
        "availability": True,
        "rating": 0.0,
        "total_reviews": 0,
        "total_jobs": 0,
        "total_earnings": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.professional_profiles.insert_one(profile_doc)
    return {"message": "Profile created successfully", "profile": {k: v for k, v in profile_doc.items() if k != "_id"}}

@api_router.get("/professionals/profile")
async def get_my_profile(user = Depends(get_current_user)):
    if user["role"] != "professional":
        raise HTTPException(status_code=403, detail="Only professionals have profiles")
    
    profile = await db.professional_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile

@api_router.put("/professionals/profile")
async def update_professional_profile(profile_data: ProfessionalProfileCreate, user = Depends(get_current_user)):
    if user["role"] != "professional":
        raise HTTPException(status_code=403, detail="Only professionals can update profiles")
    
    result = await db.professional_profiles.update_one(
        {"user_id": user["id"]},
        {"$set": profile_data.model_dump()}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {"message": "Profile updated successfully"}

@api_router.put("/professionals/availability")
async def toggle_availability(available: bool, user = Depends(get_current_user)):
    if user["role"] != "professional":
        raise HTTPException(status_code=403, detail="Only professionals can update availability")
    
    await db.professional_profiles.update_one(
        {"user_id": user["id"]},
        {"$set": {"availability": available}}
    )
    
    return {"message": "Availability updated", "availability": available}

@api_router.get("/professionals/search")
async def search_professionals(
    category: Optional[str] = None,
    location: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_rate: Optional[float] = None
):
    query = {"availability": True}
    
    if category:
        query["profession"] = {"$regex": category, "$options": "i"}
    
    professionals = await db.professional_profiles.find(query, {"_id": 0}).to_list(100)
    
    # Enrich with user data
    enriched = []
    for prof in professionals:
        user = await db.users.find_one({"id": prof["user_id"]}, {"_id": 0, "password_hash": 0})
        if user:
            prof["user"] = user
            if min_rating and prof.get("rating", 0) < min_rating:
                continue
            if max_rate and prof.get("hourly_rate", 0) > max_rate:
                continue
            enriched.append(prof)
    
    return enriched

@api_router.get("/professionals/{professional_id}")
async def get_professional_detail(professional_id: str):
    profile = await db.professional_profiles.find_one({"user_id": professional_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    user = await db.users.find_one({"id": professional_id}, {"_id": 0, "password_hash": 0})
    profile["user"] = user
    
    # Get reviews
    reviews = await db.reviews.find({"professional_id": professional_id}, {"_id": 0}).to_list(50)
    profile["reviews"] = reviews
    
    return profile

# ============= JOB POSTING ENDPOINTS =============
@api_router.post("/jobs")
async def create_job(job_data: JobPostCreate, user = Depends(get_current_user)):
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can post jobs")
    
    job_id = str(uuid.uuid4())
    job_doc = {
        "id": job_id,
        "client_id": user["id"],
        **job_data.model_dump(),
        "status": JobStatus.OPEN.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "matched_professional_id": None
    }
    
    await db.jobs.insert_one(job_doc)
    return {"message": "Job posted successfully", "job": {k: v for k, v in job_doc.items() if k != "_id"}}

@api_router.get("/jobs")
async def get_jobs(
    status: Optional[str] = None,
    category: Optional[str] = None,
    user = Depends(get_current_user)
):
    query = {}
    
    if user["role"] == "client":
        query["client_id"] = user["id"]
    elif status:
        query["status"] = status
    
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    
    jobs = await db.jobs.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with bid count for client jobs
    for job in jobs:
        bid_count = await db.bids.count_documents({"job_id": job["id"]})
        job["bid_count"] = bid_count
    
    return jobs

@api_router.get("/jobs/available")
async def get_available_jobs(category: Optional[str] = None, user = Depends(get_current_user)):
    """Get available jobs for professionals to bid on"""
    query = {"status": JobStatus.OPEN.value}
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    
    jobs = await db.jobs.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with client info and check if user already bid
    for job in jobs:
        client = await db.users.find_one({"id": job["client_id"]}, {"_id": 0, "password_hash": 0})
        job["client"] = client
        # Check if current professional already bid on this job
        existing_bid = await db.bids.find_one({"job_id": job["id"], "professional_id": user["id"]})
        job["has_bid"] = existing_bid is not None
        job["bid_count"] = await db.bids.count_documents({"job_id": job["id"]})
    
    return jobs

@api_router.get("/jobs/{job_id}")
async def get_job_detail(job_id: str, user = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    client = await db.users.find_one({"id": job["client_id"]}, {"_id": 0, "password_hash": 0})
    job["client"] = client
    
    # Get bids for this job (only if client owns the job)
    if user["role"] == "client" and job["client_id"] == user["id"]:
        bids = await db.bids.find({"job_id": job_id}, {"_id": 0}).to_list(50)
        for bid in bids:
            pro_user = await db.users.find_one({"id": bid["professional_id"]}, {"_id": 0, "password_hash": 0})
            pro_profile = await db.professional_profiles.find_one({"user_id": bid["professional_id"]}, {"_id": 0})
            bid["professional"] = pro_user
            bid["profile"] = pro_profile
        job["bids"] = bids
    
    return job

# ============= BIDDING ENDPOINTS =============
@api_router.post("/bids")
async def create_bid(bid_data: BidCreate, user = Depends(get_current_user)):
    """Professional submits a bid for a job"""
    if user["role"] != "professional":
        raise HTTPException(status_code=403, detail="Only professionals can submit bids")
    
    # Check if job exists and is open
    job = await db.jobs.find_one({"id": bid_data.job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != JobStatus.OPEN.value:
        raise HTTPException(status_code=400, detail="Job is no longer accepting bids")
    
    # Check if professional already bid on this job
    existing_bid = await db.bids.find_one({"job_id": bid_data.job_id, "professional_id": user["id"]})
    if existing_bid:
        raise HTTPException(status_code=400, detail="You have already submitted a bid for this job")
    
    # Check if professional has a profile
    profile = await db.professional_profiles.find_one({"user_id": user["id"]})
    if not profile:
        raise HTTPException(status_code=400, detail="Please create a profile before bidding")
    
    bid_id = str(uuid.uuid4())
    bid_doc = {
        "id": bid_id,
        "job_id": bid_data.job_id,
        "professional_id": user["id"],
        "proposed_price": bid_data.proposed_price,
        "message": bid_data.message,
        "estimated_hours": bid_data.estimated_hours,
        "status": BidStatus.PENDING.value,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bids.insert_one(bid_doc)
    return {"message": "Bid submitted successfully", "bid": {k: v for k, v in bid_doc.items() if k != "_id"}}

@api_router.get("/bids/my")
async def get_my_bids(user = Depends(get_current_user)):
    """Get all bids submitted by the professional"""
    if user["role"] != "professional":
        raise HTTPException(status_code=403, detail="Only professionals can view their bids")
    
    bids = await db.bids.find({"professional_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with job details
    for bid in bids:
        job = await db.jobs.find_one({"id": bid["job_id"]}, {"_id": 0})
        if job:
            client = await db.users.find_one({"id": job["client_id"]}, {"_id": 0, "password_hash": 0})
            job["client"] = client
        bid["job"] = job
    
    return bids

@api_router.get("/bids/job/{job_id}")
async def get_job_bids(job_id: str, user = Depends(get_current_user)):
    """Get all bids for a specific job (client only)"""
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if user["role"] == "client" and job["client_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to view bids for this job")
    
    bids = await db.bids.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    for bid in bids:
        pro_user = await db.users.find_one({"id": bid["professional_id"]}, {"_id": 0, "password_hash": 0})
        pro_profile = await db.professional_profiles.find_one({"user_id": bid["professional_id"]}, {"_id": 0})
        bid["professional"] = pro_user
        bid["profile"] = pro_profile
    
    return bids

@api_router.put("/bids/{bid_id}/accept")
async def accept_bid(bid_id: str, user = Depends(get_current_user)):
    """Client accepts a bid, creating a booking"""
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can accept bids")
    
    bid = await db.bids.find_one({"id": bid_id})
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    job = await db.jobs.find_one({"id": bid["job_id"]})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["client_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update bid status
    await db.bids.update_one({"id": bid_id}, {"$set": {"status": BidStatus.ACCEPTED.value}})
    
    # Reject all other bids for this job
    await db.bids.update_many(
        {"job_id": bid["job_id"], "id": {"$ne": bid_id}},
        {"$set": {"status": BidStatus.REJECTED.value}}
    )
    
    # Update job status
    await db.jobs.update_one(
        {"id": bid["job_id"]},
        {"$set": {"status": JobStatus.MATCHED.value, "matched_professional_id": bid["professional_id"]}}
    )
    
    # Create booking
    booking_id = str(uuid.uuid4())
    booking_doc = {
        "id": booking_id,
        "client_id": user["id"],
        "professional_id": bid["professional_id"],
        "job_id": bid["job_id"],
        "service_description": job["title"],
        "scheduled_date": datetime.now(timezone.utc).isoformat(),  # Default to now, client can update
        "estimated_hours": bid.get("estimated_hours"),
        "agreed_price": bid["proposed_price"],
        "status": BookingStatus.PENDING.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    
    await db.bookings.insert_one(booking_doc)
    
    return {
        "message": "Bid accepted and booking created",
        "booking": {k: v for k, v in booking_doc.items() if k != "_id"}
    }

@api_router.put("/bids/{bid_id}/reject")
async def reject_bid(bid_id: str, user = Depends(get_current_user)):
    """Client rejects a bid"""
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can reject bids")
    
    bid = await db.bids.find_one({"id": bid_id})
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    job = await db.jobs.find_one({"id": bid["job_id"]})
    if job["client_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.bids.update_one({"id": bid_id}, {"$set": {"status": BidStatus.REJECTED.value}})
    return {"message": "Bid rejected"}

# ============= AI MATCHING ENDPOINT =============
@api_router.post("/match")
async def ai_match_professionals(match_request: MatchRequest, user = Depends(get_current_user)):
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can request matches")
    
    # Get available professionals in the category
    professionals = await db.professional_profiles.find(
        {"availability": True, "profession": {"$regex": match_request.category, "$options": "i"}},
        {"_id": 0}
    ).to_list(50)
    
    if not professionals:
        return {"matches": [], "message": "No professionals available in this category"}
    
    # Enrich with user data
    for prof in professionals:
        user_data = await db.users.find_one({"id": prof["user_id"]}, {"_id": 0, "password_hash": 0})
        prof["user"] = user_data
    
    # Use AI for intelligent matching if we have the key
    if EMERGENT_LLM_KEY:
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"match-{uuid.uuid4()}",
                system_message="""You are an AI assistant for Kazi Links, a professional services marketplace.
                Your task is to rank professionals based on job requirements.
                Consider: skills match, location proximity, ratings, pricing, and experience.
                Return a JSON array of professional IDs in order of best match, with a brief reason for each."""
            ).with_model("gemini", "gemini-3-flash-preview")
            
            prof_summary = "\n".join([
                f"ID: {p['user_id']}, Name: {p['user'].get('name', 'N/A')}, "
                f"Skills: {', '.join(p.get('skills', []))}, "
                f"Rating: {p.get('rating', 0)}/5, "
                f"Rate: KSh {p.get('hourly_rate', 'N/A')}/hr, "
                f"Experience: {p.get('experience_years', 0)} years, "
                f"Location: {p['user'].get('location', 'N/A')}"
                for p in professionals
            ])
            
            user_message = UserMessage(
                text=f"""Job Requirements:
                - Description: {match_request.job_description}
                - Category: {match_request.category}
                - Location: {match_request.location}
                - Budget: KSh {match_request.budget}
                
                Available Professionals:
                {prof_summary}
                
                Rank these professionals from best to worst match. Return only a JSON array like:
                [{{"id": "user_id", "rank": 1, "match_score": 95, "reason": "Best match because..."}}]"""
            )
            
            response = await chat.send_message(user_message)
            
            # Parse AI response and sort professionals
            import json
            try:
                # Extract JSON from response
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                if json_start >= 0 and json_end > json_start:
                    rankings = json.loads(response[json_start:json_end])
                    
                    # Sort professionals by AI ranking
                    ranked_ids = {r["id"]: r for r in rankings}
                    sorted_professionals = sorted(
                        professionals,
                        key=lambda p: ranked_ids.get(p["user_id"], {}).get("rank", 999)
                    )
                    
                    # Add match info
                    for prof in sorted_professionals:
                        if prof["user_id"] in ranked_ids:
                            prof["match_score"] = ranked_ids[prof["user_id"]].get("match_score", 0)
                            prof["match_reason"] = ranked_ids[prof["user_id"]].get("reason", "")
                    
                    return {"matches": sorted_professionals[:10], "ai_powered": True}
            except json.JSONDecodeError:
                logger.warning("Could not parse AI response, using fallback ranking")
        except Exception as e:
            logger.error(f"AI matching error: {e}")
    
    # Fallback: Sort by rating
    sorted_professionals = sorted(professionals, key=lambda p: p.get("rating", 0), reverse=True)
    return {"matches": sorted_professionals[:10], "ai_powered": False}

# ============= BOOKING ENDPOINTS =============
@api_router.post("/bookings")
async def create_booking(booking_data: BookingCreate, user = Depends(get_current_user)):
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can create bookings")
    
    # Verify professional exists and is available
    professional = await db.professional_profiles.find_one({"user_id": booking_data.professional_id})
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    booking_id = str(uuid.uuid4())
    booking_doc = {
        "id": booking_id,
        "client_id": user["id"],
        **booking_data.model_dump(),
        "scheduled_date": booking_data.scheduled_date.isoformat(),
        "status": BookingStatus.PENDING.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "reviewed": False
    }
    
    await db.bookings.insert_one(booking_doc)
    return {"message": "Booking created successfully", "booking": {k: v for k, v in booking_doc.items() if k != "_id"}}

@api_router.post("/bookings/rebook/{professional_id}")
async def rebook_professional(professional_id: str, booking_data: BookingCreate, user = Depends(get_current_user)):
    """Re-book a professional from a previous completed booking"""
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can create bookings")
    
    # Verify professional exists
    professional = await db.professional_profiles.find_one({"user_id": professional_id})
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    booking_id = str(uuid.uuid4())
    booking_doc = {
        "id": booking_id,
        "client_id": user["id"],
        "professional_id": professional_id,
        "job_id": booking_data.job_id,
        "service_description": booking_data.service_description,
        "scheduled_date": booking_data.scheduled_date.isoformat(),
        "estimated_hours": booking_data.estimated_hours,
        "agreed_price": booking_data.agreed_price,
        "status": BookingStatus.PENDING.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "reviewed": False
    }
    
    await db.bookings.insert_one(booking_doc)
    return {"message": "Re-booking created successfully", "booking": {k: v for k, v in booking_doc.items() if k != "_id"}}

@api_router.get("/bookings")
async def get_bookings(status: Optional[str] = None, user = Depends(get_current_user)):
    if user["role"] == "client":
        query = {"client_id": user["id"]}
    else:
        query = {"professional_id": user["id"]}
    
    if status:
        query["status"] = status
    
    bookings = await db.bookings.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with user data and check if reviewed
    for booking in bookings:
        if user["role"] == "client":
            prof_user = await db.users.find_one({"id": booking["professional_id"]}, {"_id": 0, "password_hash": 0})
            prof_profile = await db.professional_profiles.find_one({"user_id": booking["professional_id"]}, {"_id": 0})
            booking["professional"] = prof_user
            booking["professional_profile"] = prof_profile
            # Check if client has already reviewed this booking
            existing_review = await db.reviews.find_one({"booking_id": booking["id"]})
            booking["reviewed"] = existing_review is not None
        else:
            client = await db.users.find_one({"id": booking["client_id"]}, {"_id": 0, "password_hash": 0})
            booking["client"] = client
        
        # Get payment status
        payment = await db.payments.find_one({"booking_id": booking["id"]}, {"_id": 0})
        booking["payment"] = payment
    
    return bookings

@api_router.get("/bookings/{booking_id}")
async def get_booking_detail(booking_id: str, user = Depends(get_current_user)):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Verify permission
    if user["role"] == "client" and booking["client_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    if user["role"] == "professional" and booking["professional_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Enrich
    prof_user = await db.users.find_one({"id": booking["professional_id"]}, {"_id": 0, "password_hash": 0})
    client = await db.users.find_one({"id": booking["client_id"]}, {"_id": 0, "password_hash": 0})
    booking["professional"] = prof_user
    booking["client"] = client
    
    # Check if reviewed
    existing_review = await db.reviews.find_one({"booking_id": booking["id"]})
    booking["reviewed"] = existing_review is not None
    if existing_review:
        booking["review"] = {k: v for k, v in existing_review.items() if k != "_id"}
    
    return booking

@api_router.put("/bookings/{booking_id}/status")
async def update_booking_status(booking_id: str, status: BookingStatus, user = Depends(get_current_user)):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Verify permission
    if user["role"] == "professional" and booking["professional_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    if user["role"] == "client" and booking["client_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {"status": status.value}
    if status == BookingStatus.COMPLETED:
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.bookings.update_one({"id": booking_id}, {"$set": update_data})
    return {"message": f"Booking status updated to {status.value}"}

# ============= PAYMENT ENDPOINTS (M-PESA MOCK) =============
PLATFORM_FEE_PERCENTAGE = 20

@api_router.post("/payments/initiate")
async def initiate_payment(payment_data: PaymentCreate, user = Depends(get_current_user)):
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can initiate payments")
    
    booking = await db.bookings.find_one({"id": payment_data.booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["client_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Calculate fees
    amount = booking["agreed_price"]
    platform_fee = amount * (PLATFORM_FEE_PERCENTAGE / 100)
    professional_amount = amount - platform_fee
    
    payment_id = str(uuid.uuid4())
    payment_doc = {
        "id": payment_id,
        "booking_id": payment_data.booking_id,
        "client_id": user["id"],
        "professional_id": booking["professional_id"],
        "amount": amount,
        "platform_fee": platform_fee,
        "professional_amount": professional_amount,
        "status": PaymentStatus.ESCROW.value,  # MOCK: Simulate successful escrow
        "mpesa_transaction_id": f"MPESA{uuid.uuid4().hex[:10].upper()}",  # MOCK transaction ID
        "created_at": datetime.now(timezone.utc).isoformat(),
        "released_at": None
    }
    
    await db.payments.insert_one(payment_doc)
    
    # Update booking status
    await db.bookings.update_one({"id": payment_data.booking_id}, {"$set": {"status": BookingStatus.CONFIRMED.value}})
    
    return {
        "message": "Payment processed and held in escrow (MOCK)",
        "payment": {k: v for k, v in payment_doc.items() if k != "_id"},
        "note": "M-Pesa integration is MOCKED for demo purposes"
    }

@api_router.post("/payments/{payment_id}/release")
async def release_payment(payment_id: str, user = Depends(get_current_user)):
    payment = await db.payments.find_one({"id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment["client_id"] != user["id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if payment["status"] != PaymentStatus.ESCROW.value:
        raise HTTPException(status_code=400, detail="Payment not in escrow")
    
    # Release payment to professional
    await db.payments.update_one(
        {"id": payment_id},
        {"$set": {"status": PaymentStatus.RELEASED.value, "released_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Update professional earnings
    await db.professional_profiles.update_one(
        {"user_id": payment["professional_id"]},
        {"$inc": {"total_earnings": payment["professional_amount"], "total_jobs": 1}}
    )
    
    return {"message": "Payment released to professional (MOCK)", "amount_released": payment["professional_amount"]}

@api_router.get("/payments")
async def get_payments(user = Depends(get_current_user)):
    if user["role"] == "client":
        query = {"client_id": user["id"]}
    elif user["role"] == "professional":
        query = {"professional_id": user["id"]}
    else:
        query = {}
    
    payments = await db.payments.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return payments

# ============= REVIEW ENDPOINTS =============
@api_router.post("/reviews")
async def create_review(review_data: ReviewCreate, user = Depends(get_current_user)):
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can create reviews")
    
    # Verify booking exists and is completed
    booking = await db.bookings.find_one({"id": review_data.booking_id, "client_id": user["id"]})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    review_id = str(uuid.uuid4())
    review_doc = {
        "id": review_id,
        "booking_id": review_data.booking_id,
        "client_id": user["id"],
        "professional_id": review_data.professional_id,
        "rating": review_data.rating,
        "comment": review_data.comment,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.reviews.insert_one(review_doc)
    
    # Update professional rating
    reviews = await db.reviews.find({"professional_id": review_data.professional_id}).to_list(1000)
    avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
    
    await db.professional_profiles.update_one(
        {"user_id": review_data.professional_id},
        {"$set": {"rating": round(avg_rating, 1), "total_reviews": len(reviews)}}
    )
    
    return {"message": "Review submitted successfully"}

@api_router.get("/reviews/{professional_id}")
async def get_professional_reviews(professional_id: str):
    reviews = await db.reviews.find({"professional_id": professional_id}, {"_id": 0}).to_list(100)
    
    # Enrich with client names
    for review in reviews:
        client = await db.users.find_one({"id": review["client_id"]}, {"name": 1, "_id": 0})
        review["client_name"] = client["name"] if client else "Anonymous"
    
    return reviews

# ============= ADMIN ENDPOINTS =============
@api_router.get("/admin/stats")
async def get_admin_stats(user = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_users = await db.users.count_documents({})
    total_clients = await db.users.count_documents({"role": "client"})
    total_professionals = await db.users.count_documents({"role": "professional"})
    total_jobs = await db.jobs.count_documents({})
    total_bookings = await db.bookings.count_documents({})
    completed_bookings = await db.bookings.count_documents({"status": "completed"})
    
    # Calculate total revenue
    payments = await db.payments.find({"status": PaymentStatus.RELEASED.value}).to_list(10000)
    total_revenue = sum(p["platform_fee"] for p in payments)
    total_transactions = sum(p["amount"] for p in payments)
    
    return {
        "total_users": total_users,
        "total_clients": total_clients,
        "total_professionals": total_professionals,
        "total_jobs": total_jobs,
        "total_bookings": total_bookings,
        "completed_bookings": completed_bookings,
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "platform_fee_percentage": PLATFORM_FEE_PERCENTAGE
    }

@api_router.get("/admin/users")
async def get_all_users(role: Optional[str] = None, user = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if role:
        query["role"] = role
    
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@api_router.get("/admin/transactions")
async def get_all_transactions(user = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    payments = await db.payments.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich with user data
    for payment in payments:
        client = await db.users.find_one({"id": payment["client_id"]}, {"name": 1, "_id": 0})
        prof = await db.users.find_one({"id": payment["professional_id"]}, {"name": 1, "_id": 0})
        payment["client_name"] = client["name"] if client else "Unknown"
        payment["professional_name"] = prof["name"] if prof else "Unknown"
    
    return payments

# ============= DASHBOARD DATA =============
@api_router.get("/dashboard/client")
async def get_client_dashboard(user = Depends(get_current_user)):
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Client access required")
    
    active_bookings = await db.bookings.find(
        {"client_id": user["id"], "status": {"$in": ["pending", "confirmed", "in_progress"]}},
        {"_id": 0}
    ).to_list(10)
    
    # Enrich bookings
    for booking in active_bookings:
        prof_user = await db.users.find_one({"id": booking["professional_id"]}, {"_id": 0, "password_hash": 0})
        booking["professional"] = prof_user
    
    recent_jobs = await db.jobs.find({"client_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(5)
    
    # Add bid count to jobs
    for job in recent_jobs:
        job["bid_count"] = await db.bids.count_documents({"job_id": job["id"]})
    
    payments = await db.payments.find({"client_id": user["id"]}, {"_id": 0}).to_list(100)
    total_spent = sum(p["amount"] for p in payments if p["status"] == PaymentStatus.RELEASED.value)
    
    # Get completed bookings that need review
    completed_bookings = await db.bookings.find(
        {"client_id": user["id"], "status": "completed"},
        {"_id": 0}
    ).to_list(10)
    
    for booking in completed_bookings:
        prof_user = await db.users.find_one({"id": booking["professional_id"]}, {"_id": 0, "password_hash": 0})
        booking["professional"] = prof_user
        existing_review = await db.reviews.find_one({"booking_id": booking["id"]})
        booking["reviewed"] = existing_review is not None
    
    # Filter to only unreviewed ones
    pending_reviews = [b for b in completed_bookings if not b.get("reviewed", False)]
    
    return {
        "active_bookings": active_bookings,
        "recent_jobs": recent_jobs,
        "total_spent": total_spent,
        "total_bookings": len(payments),
        "pending_reviews": pending_reviews
    }

@api_router.get("/dashboard/professional")
async def get_professional_dashboard(user = Depends(get_current_user)):
    if user["role"] != "professional":
        raise HTTPException(status_code=403, detail="Professional access required")
    
    profile = await db.professional_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    
    upcoming_bookings = await db.bookings.find(
        {"professional_id": user["id"], "status": {"$in": ["pending", "confirmed"]}},
        {"_id": 0}
    ).to_list(10)
    
    # Enrich bookings
    for booking in upcoming_bookings:
        client = await db.users.find_one({"id": booking["client_id"]}, {"_id": 0, "password_hash": 0})
        booking["client"] = client
    
    # Get all payments for earnings calculation
    payments = await db.payments.find({"professional_id": user["id"]}, {"_id": 0}).to_list(1000)
    total_earnings = sum(p["professional_amount"] for p in payments if p["status"] == PaymentStatus.RELEASED.value)
    pending_earnings = sum(p["professional_amount"] for p in payments if p["status"] == PaymentStatus.ESCROW.value)
    total_platform_commission = sum(p["platform_fee"] for p in payments if p["status"] == PaymentStatus.RELEASED.value)
    
    # Weekly earnings breakdown (last 7 days)
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=7)
    
    weekly_earnings = []
    weekly_commission = []
    daily_labels = []
    
    for i in range(7):
        day = week_start + timedelta(days=i+1)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        day_payments = [
            p for p in payments 
            if p["status"] == PaymentStatus.RELEASED.value 
            and p.get("released_at")
            and day_start.isoformat() <= p["released_at"] <= day_end.isoformat()
        ]
        
        day_earnings = sum(p["professional_amount"] for p in day_payments)
        day_commission = sum(p["platform_fee"] for p in day_payments)
        
        weekly_earnings.append(day_earnings)
        weekly_commission.append(day_commission)
        daily_labels.append(day.strftime("%a"))
    
    # Get pending bids count
    pending_bids = await db.bids.count_documents({"professional_id": user["id"], "status": "pending"})
    accepted_bids = await db.bids.count_documents({"professional_id": user["id"], "status": "accepted"})
    
    # Get available jobs count in professional's category
    if profile:
        available_jobs = await db.jobs.count_documents({
            "status": JobStatus.OPEN.value,
            "category": {"$regex": profile.get("profession", ""), "$options": "i"}
        })
    else:
        available_jobs = 0
    
    # Recent reviews
    reviews = await db.reviews.find({"professional_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(5)
    
    return {
        "profile": profile,
        "upcoming_bookings": upcoming_bookings,
        "total_earnings": total_earnings,
        "pending_earnings": pending_earnings,
        "total_platform_commission": total_platform_commission,
        "total_jobs": profile["total_jobs"] if profile else 0,
        "rating": profile["rating"] if profile else 0,
        "total_reviews": profile["total_reviews"] if profile else 0,
        "recent_reviews": reviews,
        "weekly_earnings": {
            "labels": daily_labels,
            "earnings": weekly_earnings,
            "commissions": weekly_commission,
            "total_week_earnings": sum(weekly_earnings),
            "total_week_commission": sum(weekly_commission)
        },
        "bids": {
            "pending": pending_bids,
            "accepted": accepted_bids
        },
        "available_jobs": available_jobs
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
