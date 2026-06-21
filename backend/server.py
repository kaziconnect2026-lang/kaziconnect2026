from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import re
import logging
import secrets
import hashlib
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from enum import Enum
from emergentintegrations.llm.chat import LlmChat, UserMessage
from fastapi import Request
import mpesa_service
import storage_service
import email_service

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

# ============= SEMANTIC SEARCH INTENT MAP =============
# Lightweight keyword → profession mapping for deterministic semantic search.
# Each entry maps a primary keyword to {tokens: synonyms, professions: matching profession-name keywords}.
# Used by /api/professionals/search to interpret phrases like "need nails done", "windshield broken",
# "leaky tap", "haircut" without an LLM call.
PROFESSION_INTENT_MAP = {
    "nails":      {"tokens": ["nail", "manicure", "pedicure", "polish", "acrylic", "gel"], "professions": ["nail technician"]},
    "hair":       {"tokens": ["braid", "braids", "weave", "weaves", "salon", "dread", "dreadlocks"], "professions": ["hairdresser"]},
    "haircut":    {"tokens": ["shave", "fade", "trim", "beard", "cut"], "professions": ["barber"]},
    "barber":     {"tokens": ["beard"], "professions": ["barber"]},
    "windshield": {"tokens": ["windscreen", "car glass", "auto glass"], "professions": ["car mechanic", "car electrician"]},
    "car":        {"tokens": ["engine", "brake", "brakes", "transmission", "exhaust", "clutch"], "professions": ["car mechanic"]},
    "tire":       {"tokens": ["tyre", "puncture", "wheel"], "professions": ["tire repair"]},
    "leak":       {"tokens": ["leaking", "leaks", "drip", "dripping", "burst"], "professions": ["plumber"]},
    "sink":       {"tokens": ["faucet", "tap", "basin"], "professions": ["plumber"]},
    "toilet":     {"tokens": ["wc", "loo", "flush"], "professions": ["plumber"]},
    "pipe":       {"tokens": ["pipes", "plumbing", "drain", "drainage", "sewer"], "professions": ["plumber"]},
    "wiring":     {"tokens": ["wire", "wires", "socket", "sockets", "outlet", "outlets", "breaker"], "professions": ["electrician"]},
    "power":      {"tokens": ["electric", "electrical", "electricity", "blackout", "fuse"], "professions": ["electrician"]},
    "lights":     {"tokens": ["lighting", "bulb", "lamp"], "professions": ["electrician"]},
    "paint":      {"tokens": ["painting", "wall", "walls", "ceiling", "repaint"], "professions": ["painter"]},
    "wood":       {"tokens": ["furniture", "cabinet", "cabinets", "shelf", "shelves", "wardrobe"], "professions": ["carpenter"]},
    "clean":      {"tokens": ["cleaning", "vacuum", "scrub", "deep clean"], "professions": ["cleaner"]},
    "window":     {"tokens": ["windows"], "professions": ["window cleaner"]},
    "tattoo":     {"tokens": ["ink", "tat"], "professions": ["tattoo artist"]},
    "massage":    {"tokens": ["spa", "therapy"], "professions": ["massage therapist"]},
    "chef":       {"tokens": ["cook", "cooking", "meal", "catering"], "professions": ["chef", "private chef", "caterer"]},
    "tutor":      {"tokens": ["tuition", "lesson", "coach", "teach", "teacher"], "professions": ["tutor"]},
    "photo":      {"tokens": ["photography", "photoshoot", "shoot", "headshot"], "professions": ["photographer"]},
    "video":      {"tokens": ["videography", "filming", "shoot", "recording"], "professions": ["videographer", "video director"]},
    "dj":         {"tokens": ["deejay", "music"], "professions": ["dj"]},
    "event":      {"tokens": ["party", "celebration", "function"], "professions": ["event planner", "event decorator"]},
    "wedding":    {"tokens": ["bride", "groom"], "professions": ["wedding planner"]},
    "delivery":   {"tokens": ["courier", "ship"], "professions": ["delivery rider", "courier"]},
    "boda":       {"tokens": ["bodaboda", "motorbike", "rider"], "professions": ["bodaboda rider"]},
    "guard":      {"tokens": ["security", "bouncer"], "professions": ["security guard", "bodyguard"]},
    "nanny":      {"tokens": ["babysitter", "babysit"], "professions": ["nanny"]},
    "maid":       {"tokens": ["housemaid", "housekeeper", "house help"], "professions": ["housemaid", "house helper"]},
    "tile":       {"tokens": ["tiles", "tiling"], "professions": ["tiler"]},
    "weld":       {"tokens": ["welding", "metal", "gate"], "professions": ["welder"]},
    "mason":      {"tokens": ["masonry", "fundi", "block", "brick"], "professions": ["mason"]},
    "roof":       {"tokens": ["roofing", "iron sheets"], "professions": ["roofing specialist"]},
    "ac":         {"tokens": ["aircon", "air-con", "cooling"], "professions": ["appliance repair"]},
    "fridge":     {"tokens": ["refrigerator", "freezer"], "professions": ["appliance repair"]},
    "phone":      {"tokens": ["mobile", "smartphone"], "professions": ["electronics repair"]},
    "laptop":     {"tokens": ["computer", "pc"], "professions": ["electronics repair", "it support"]},
    "tv":         {"tokens": ["television"], "professions": ["electronics repair"]},
    "cctv":       {"tokens": ["camera", "surveillance"], "professions": ["cctv installer"]},
    "wifi":       {"tokens": ["internet", "router", "network"], "professions": ["wifi installer", "it support"]},
    "solar":      {"tokens": ["panel"], "professions": ["solar installer"]},
}

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

class LedgerEntryType(str, Enum):
    DEPOSIT = "deposit"                    # User deposits to wallet
    WITHDRAWAL = "withdrawal"              # User withdraws from wallet
    ESCROW_IN = "escrow_in"               # Client pays for booking (into escrow)
    ESCROW_OUT = "escrow_out"             # Payment released from escrow
    PLATFORM_FEE = "platform_fee"         # Platform commission deducted
    PROFESSIONAL_PAYOUT = "professional_payout"  # Professional receives payment
    REFUND = "refund"                     # Refund to client
    ADJUSTMENT = "adjustment"             # Manual adjustment by admin

# ============= ID GENERATION HELPERS =============
async def generate_client_id():
    """Generate unique client ID: CL-XXXXX"""
    count = await db.users.count_documents({"role": "client"})
    return f"CL-{str(count + 1).zfill(5)}"

async def generate_professional_id():
    """Generate unique professional ID: PR-XXXXX"""
    count = await db.users.count_documents({"role": "professional"})
    return f"PR-{str(count + 1).zfill(5)}"

async def generate_job_id():
    """Generate unique job ID: JOB-XXXXX"""
    count = await db.jobs.count_documents({})
    return f"JOB-{str(count + 1).zfill(5)}"

async def generate_booking_id():
    """Generate unique booking ID: BK-XXXXX"""
    count = await db.bookings.count_documents({})
    return f"BK-{str(count + 1).zfill(5)}"

async def generate_transaction_id():
    """Generate unique transaction ID: TXN-XXXXX"""
    count = await db.ledger.count_documents({})
    return f"TXN-{str(count + 1).zfill(6)}"

async def generate_payment_id():
    """Generate unique payment ID: PAY-XXXXX"""
    count = await db.payments.count_documents({})
    return f"PAY-{str(count + 1).zfill(5)}"

# ============= LEDGER FUNCTIONS =============
async def create_ledger_entry(
    entry_type: LedgerEntryType,
    user_id: str,
    amount: float,
    description: str,
    reference_id: str = None,
    reference_type: str = None,
    related_user_id: str = None,
    metadata: dict = None
):
    """Create a ledger entry to track all financial transactions"""
    transaction_id = await generate_transaction_id()
    
    # Get user's current wallet balance
    user = await db.users.find_one({"id": user_id}, {"wallet_balance": 1})
    balance_before = user.get("wallet_balance", 0.0) if user else 0.0
    
    # Calculate balance after based on entry type
    if entry_type in [LedgerEntryType.DEPOSIT, LedgerEntryType.PROFESSIONAL_PAYOUT, LedgerEntryType.REFUND]:
        balance_after = balance_before + amount
    elif entry_type in [LedgerEntryType.WITHDRAWAL, LedgerEntryType.ESCROW_IN]:
        balance_after = balance_before - amount
    else:
        balance_after = balance_before  # For platform fees and escrow_out, no wallet change
    
    ledger_entry = {
        "id": str(uuid.uuid4()),
        "transaction_id": transaction_id,
        "entry_type": entry_type.value,
        "user_id": user_id,
        "related_user_id": related_user_id,
        "amount": amount,
        "balance_before": balance_before,
        "balance_after": balance_after,
        "description": description,
        "reference_id": reference_id,
        "reference_type": reference_type,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed"
    }
    
    await db.ledger.insert_one(ledger_entry)
    
    return {k: v for k, v in ledger_entry.items() if k != "_id"}

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
    display_id: Optional[str] = None
    email: str
    name: str
    phone: str
    role: UserRole
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    is_active: bool = True
    wallet_balance: float = 0.0
    profile_photo: Optional[str] = None

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    profile_photo: Optional[str] = None

# Wallet Models
class WalletTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # "deposit" or "withdrawal"
    amount: float
    status: str = "completed"  # "pending", "completed", "failed"
    reference: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DepositRequest(BaseModel):
    amount: float
    phone_number: Optional[str] = None  # Ignored — server uses the user's registered phone


class WithdrawalRequest(BaseModel):
    amount: float
    phone_number: Optional[str] = None  # Ignored — server uses the user's registered phone

# Push Notification Models
class PushSubscription(BaseModel):
    user_id: str
    endpoint: str
    keys: dict
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PushSubscriptionCreate(BaseModel):
    endpoint: str
    keys: dict

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
    id_number: Optional[str] = None  # National ID number
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
    id_number: Optional[str] = None  # National ID number

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
    phone_number: Optional[str] = None  # Ignored — server uses the user's registered phone

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
    job_description: Optional[str] = None
    query: Optional[str] = None  # Free-text natural language query
    category: Optional[str] = None
    location: Optional[str] = None
    budget: Optional[float] = None
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


optional_security = HTTPBearer(auto_error=False)

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
):
    """Return current user if a valid token is provided; otherwise None."""
    if credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        return user
    except Exception:
        return None


PHONE_VISIBILITY_BOOKING_STATUSES = ["confirmed", "in_progress", "completed"]


async def _has_active_booking(client_id: str, professional_id: str) -> bool:
    """Check if the client has any booking with the professional that is confirmed or beyond."""
    booking = await db.bookings.find_one({
        "client_id": client_id,
        "professional_id": professional_id,
        "status": {"$in": PHONE_VISIBILITY_BOOKING_STATUSES},
    })
    return booking is not None


_KYC_PRIVATE_FIELDS = {
    "id_front_path", "id_back_path",
    "id_verification_notes", "id_verified_by",
    "id_verified_at", "id_uploaded_at",
    "id_verification_status",
}


def _strip_phone(user_doc: dict) -> dict:
    """Return a copy of the user dict without the phone field and private KYC metadata.

    `id_verified` (boolean trust signal) is kept; everything else KYC-related is removed.
    """
    if not user_doc:
        return user_doc
    safe = {
        k: v for k, v in user_doc.items()
        if k != "phone" and k not in _KYC_PRIVATE_FIELDS
    }
    return safe

async def require_role(required_roles: List[UserRole]):
    async def role_checker(user = Depends(get_current_user)):
        if user["role"] not in [r.value for r in required_roles]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

# ============= PROFESSIONAL CATEGORIES =============
PROFESSIONAL_CATEGORIES = [
    # Home Services
    {"id": "cleaner", "name": "Cleaner", "icon": "sparkles", "group": "Home Services"},
    {"id": "window_cleaner", "name": "Window Cleaner", "icon": "sparkles", "group": "Home Services"},
    {"id": "carpet_cleaner", "name": "Carpet Cleaner", "icon": "sparkles", "group": "Home Services"},
    {"id": "laundry_washer", "name": "Laundry Washer", "icon": "shirt", "group": "Home Services"},
    {"id": "swimming_pool_cleaner", "name": "Swimming Pool Cleaner", "icon": "waves", "group": "Home Services"},
    {"id": "landscaper", "name": "Landscaper / Gardener", "icon": "trees", "group": "Home Services"},
    {"id": "painter", "name": "Painter", "icon": "paintbrush", "group": "Home Services"},
    {"id": "interior_decorator", "name": "Interior Decorator", "icon": "lamp", "group": "Home Services"},
    {"id": "plastering_specialist", "name": "Plastering Specialist", "icon": "brick-wall", "group": "Home Services"},
    {"id": "tiler", "name": "Tiler", "icon": "grid-3x3", "group": "Home Services"},
    {"id": "welder", "name": "Welder", "icon": "flame", "group": "Home Services"},
    {"id": "borehole_drilling", "name": "Borehole Drilling Expert", "icon": "droplet", "group": "Home Services"},
    
    # Repair & Technical Services
    {"id": "tv_repair", "name": "TV Repair Technician", "icon": "tv", "group": "Repair & Technical"},
    {"id": "phone_repair", "name": "Phone Repair Technician", "icon": "smartphone", "group": "Repair & Technical"},
    {"id": "laptop_repair", "name": "Laptop Repair Technician", "icon": "laptop", "group": "Repair & Technical"},
    {"id": "electronics_repair", "name": "Electronics Repair Technician", "icon": "cpu", "group": "Repair & Technical"},
    {"id": "sound_system_installer", "name": "Sound System Installer", "icon": "speaker", "group": "Repair & Technical"},
    {"id": "cctv_installer", "name": "CCTV Installer", "icon": "video", "group": "Repair & Technical"},
    {"id": "solar_installer", "name": "Solar Power Installer", "icon": "sun", "group": "Repair & Technical"},
    {"id": "wifi_installer", "name": "Internet / WiFi Installer", "icon": "wifi", "group": "Repair & Technical"},
    {"id": "cable_technician", "name": "Cable Technician", "icon": "cable", "group": "Repair & Technical"},
    {"id": "appliance_repair", "name": "Appliance Repair Technician", "icon": "refrigerator", "group": "Repair & Technical"},
    {"id": "generator_technician", "name": "Generator Technician", "icon": "zap", "group": "Repair & Technical"},
    
    # Construction & Handyman
    {"id": "mason", "name": "Mason / Fundi", "icon": "building", "group": "Construction & Handyman"},
    {"id": "carpenter", "name": "Carpenter", "icon": "hammer", "group": "Construction & Handyman"},
    {"id": "foreman", "name": "Foreman", "icon": "hard-hat", "group": "Construction & Handyman"},
    {"id": "plumber", "name": "Plumber", "icon": "droplet", "group": "Construction & Handyman"},
    {"id": "electrician", "name": "Electrician", "icon": "zap", "group": "Construction & Handyman"},
    {"id": "roofing_specialist", "name": "Roofing Specialist", "icon": "home", "group": "Construction & Handyman"},
    {"id": "steel_fixer", "name": "Steel Fixer", "icon": "construction", "group": "Construction & Handyman"},
    {"id": "construction_manager", "name": "Construction Manager", "icon": "clipboard-list", "group": "Construction & Handyman"},
    
    # Education & Tutoring
    {"id": "english_tutor", "name": "English Tutor", "icon": "book-open", "group": "Education & Tutoring"},
    {"id": "math_tutor", "name": "Math Tutor", "icon": "calculator", "group": "Education & Tutoring"},
    {"id": "kiswahili_tutor", "name": "Kiswahili Tutor", "icon": "book", "group": "Education & Tutoring"},
    {"id": "primary_tutor", "name": "Primary School Tutor", "icon": "school", "group": "Education & Tutoring"},
    {"id": "high_school_tutor", "name": "High School Tutor", "icon": "graduation-cap", "group": "Education & Tutoring"},
    {"id": "university_tutor", "name": "University Tutor", "icon": "university", "group": "Education & Tutoring"},
    {"id": "academic_writer", "name": "Academic Writer", "icon": "pen", "group": "Education & Tutoring"},
    {"id": "proposal_writer", "name": "Proposal Writer", "icon": "file-text", "group": "Education & Tutoring"},
    {"id": "research_assistant", "name": "Research Assistant", "icon": "search", "group": "Education & Tutoring"},
    
    # Creative & Media
    {"id": "video_director", "name": "Video Director", "icon": "clapperboard", "group": "Creative & Media"},
    {"id": "script_writer", "name": "Script Writer", "icon": "scroll", "group": "Creative & Media"},
    {"id": "videographer", "name": "Videographer", "icon": "video", "group": "Creative & Media"},
    {"id": "photographer", "name": "Photographer", "icon": "camera", "group": "Creative & Media"},
    {"id": "cameraman", "name": "Cameraman", "icon": "video", "group": "Creative & Media"},
    {"id": "lighting_technician", "name": "Lighting Technician", "icon": "lightbulb", "group": "Creative & Media"},
    {"id": "makeup_artist", "name": "Makeup Artist", "icon": "palette", "group": "Creative & Media"},
    {"id": "content_creator", "name": "Content Creator", "icon": "share-2", "group": "Creative & Media"},
    {"id": "influencer", "name": "Influencer", "icon": "star", "group": "Creative & Media"},
    {"id": "graphic_designer", "name": "Graphic Designer", "icon": "pen-tool", "group": "Creative & Media"},
    {"id": "animator", "name": "Animator", "icon": "film", "group": "Creative & Media"},
    {"id": "voice_over_artist", "name": "Voice Over Artist", "icon": "mic", "group": "Creative & Media"},
    
    # Event & Entertainment
    {"id": "event_planner", "name": "Event Planner", "icon": "calendar-check", "group": "Event & Entertainment"},
    {"id": "dj", "name": "DJ", "icon": "disc", "group": "Event & Entertainment"},
    {"id": "comedian", "name": "Comedian", "icon": "smile", "group": "Event & Entertainment"},
    {"id": "mc_host", "name": "MC / Host", "icon": "mic", "group": "Event & Entertainment"},
    {"id": "caterer", "name": "Caterer", "icon": "utensils", "group": "Event & Entertainment"},
    {"id": "private_chef", "name": "Private Chef", "icon": "chef-hat", "group": "Event & Entertainment"},
    {"id": "waiter", "name": "Waiter", "icon": "coffee", "group": "Event & Entertainment"},
    {"id": "wedding_planner", "name": "Wedding Planner", "icon": "heart", "group": "Event & Entertainment"},
    {"id": "event_decorator", "name": "Event Decorator", "icon": "sparkles", "group": "Event & Entertainment"},
    
    # Transport & Delivery
    {"id": "courier", "name": "Courier", "icon": "package", "group": "Transport & Delivery"},
    {"id": "delivery_rider", "name": "Delivery Rider", "icon": "bike", "group": "Transport & Delivery"},
    {"id": "bodaboda_rider", "name": "Bodaboda Rider", "icon": "bike", "group": "Transport & Delivery"},
    {"id": "personal_driver", "name": "Personal Driver", "icon": "car", "group": "Transport & Delivery"},
    {"id": "truck_driver", "name": "Truck Driver", "icon": "truck", "group": "Transport & Delivery"},
    {"id": "bus_driver", "name": "Bus Driver", "icon": "bus", "group": "Transport & Delivery"},
    {"id": "taxi_driver", "name": "Taxi Driver", "icon": "car", "group": "Transport & Delivery"},
    {"id": "tour_guide", "name": "Tour Guide", "icon": "map", "group": "Transport & Delivery"},
    {"id": "movers", "name": "Movers", "icon": "truck", "group": "Transport & Delivery"},
    
    # Automotive Services
    {"id": "car_mechanic", "name": "Car Mechanic", "icon": "wrench", "group": "Automotive Services"},
    {"id": "motorcycle_mechanic", "name": "Motorcycle Mechanic", "icon": "wrench", "group": "Automotive Services"},
    {"id": "tire_repair", "name": "Tire Repair Technician", "icon": "circle", "group": "Automotive Services"},
    {"id": "car_electrician", "name": "Car Electrician", "icon": "zap", "group": "Automotive Services"},
    {"id": "car_wash", "name": "Car Wash Service", "icon": "droplets", "group": "Automotive Services"},
    
    # Health & Wellness
    {"id": "nutritionist", "name": "Nutritionist", "icon": "apple", "group": "Health & Wellness"},
    {"id": "diet_planner", "name": "Diet Planner", "icon": "salad", "group": "Health & Wellness"},
    {"id": "personal_trainer", "name": "Personal Trainer", "icon": "dumbbell", "group": "Health & Wellness"},
    {"id": "boxing_trainer", "name": "Boxing Trainer", "icon": "dumbbell", "group": "Health & Wellness"},
    {"id": "karate_trainer", "name": "Karate Trainer", "icon": "shield", "group": "Health & Wellness"},
    {"id": "physiotherapist", "name": "Physiotherapist", "icon": "activity", "group": "Health & Wellness"},
    {"id": "nurse", "name": "Nurse", "icon": "stethoscope", "group": "Health & Wellness"},
    {"id": "dentist", "name": "Dentist", "icon": "smile", "group": "Health & Wellness"},
    
    # Beauty & Personal Care
    {"id": "hairdresser", "name": "Hairdresser", "icon": "scissors", "group": "Beauty & Personal Care"},
    {"id": "nail_technician", "name": "Nail Technician", "icon": "sparkles", "group": "Beauty & Personal Care"},
    {"id": "barber", "name": "Barber", "icon": "scissors", "group": "Beauty & Personal Care"},
    {"id": "massage_therapist", "name": "Massage Therapist", "icon": "heart-pulse", "group": "Beauty & Personal Care"},
    {"id": "hina_artist", "name": "Hina Artist", "icon": "palette", "group": "Beauty & Personal Care"},
    
    # Technology & Digital Services
    {"id": "web_developer", "name": "Web Developer", "icon": "globe", "group": "Technology & Digital"},
    {"id": "software_engineer", "name": "Software Engineer", "icon": "code", "group": "Technology & Digital"},
    {"id": "mobile_app_developer", "name": "Mobile App Developer", "icon": "smartphone", "group": "Technology & Digital"},
    {"id": "ai_specialist", "name": "AI Specialist", "icon": "brain", "group": "Technology & Digital"},
    {"id": "data_scientist", "name": "Data Scientist", "icon": "bar-chart", "group": "Technology & Digital"},
    {"id": "prompt_engineer", "name": "Prompt Engineer", "icon": "message-square", "group": "Technology & Digital"},
    {"id": "cybersecurity_specialist", "name": "Cybersecurity Specialist", "icon": "shield", "group": "Technology & Digital"},
    {"id": "it_support", "name": "IT Support Technician", "icon": "headphones", "group": "Technology & Digital"},
    {"id": "cloud_engineer", "name": "Cloud Engineer", "icon": "cloud", "group": "Technology & Digital"},
    
    # Business & Professional Services
    {"id": "financial_auditor", "name": "Financial Auditor", "icon": "file-check", "group": "Business & Professional"},
    {"id": "accountant", "name": "Accountant", "icon": "calculator", "group": "Business & Professional"},
    {"id": "business_consultant", "name": "Business Consultant", "icon": "briefcase", "group": "Business & Professional"},
    {"id": "digital_marketer", "name": "Digital Marketer", "icon": "megaphone", "group": "Business & Professional"},
    {"id": "market_researcher", "name": "Market Researcher", "icon": "search", "group": "Business & Professional"},
    {"id": "market_analyst", "name": "Market Analyst", "icon": "trending-up", "group": "Business & Professional"},
    {"id": "real_estate_agent", "name": "Real Estate Agent", "icon": "home", "group": "Business & Professional"},
    {"id": "cleaning_agency", "name": "Cleaning Agency", "icon": "building", "group": "Business & Professional"},
    {"id": "property_manager", "name": "Property Manager", "icon": "key", "group": "Business & Professional"},
    
    # Security Services
    {"id": "bodyguard", "name": "Bodyguard", "icon": "shield", "group": "Security Services"},
    {"id": "security_guard", "name": "Security Guard", "icon": "shield-check", "group": "Security Services"},
    {"id": "private_investigator", "name": "Private Investigator", "icon": "search", "group": "Security Services"},
    {"id": "dog_trainer", "name": "Dog Trainer", "icon": "dog", "group": "Security Services"},
    
    # Domestic Services
    {"id": "housemaid", "name": "Housemaid / House Helper", "icon": "home", "group": "Domestic Services"},
    {"id": "chef", "name": "Chef", "icon": "chef-hat", "group": "Domestic Services"},
    {"id": "nanny", "name": "Nanny", "icon": "baby", "group": "Domestic Services"},
    {"id": "elderly_caregiver", "name": "Elderly Caregiver", "icon": "heart", "group": "Domestic Services"},
    
    # Film Production Crew
    {"id": "director", "name": "Director", "icon": "clapperboard", "group": "Film Production Crew"},
    {"id": "producer", "name": "Producer", "icon": "film", "group": "Film Production Crew"},
    {"id": "film_cameraman", "name": "Cameraman", "icon": "video", "group": "Film Production Crew"},
    {"id": "film_lighting", "name": "Lighting Technician", "icon": "lightbulb", "group": "Film Production Crew"},
    {"id": "film_extras", "name": "Film Extras", "icon": "users", "group": "Film Production Crew"},
    {"id": "transport_crew", "name": "Transport Crew", "icon": "truck", "group": "Film Production Crew"},
    
    # Legacy/Other
    {"id": "tattoo_artist", "name": "Tattoo Artist", "icon": "pen-tool", "group": "Beauty & Personal Care"},
]

# Featured categories for landing page with images
FEATURED_CATEGORIES = [
    {"id": "barber", "name": "Barber", "icon": "scissors", "image": "https://images.unsplash.com/photo-1599641078447-229873aedbc8?crop=entropy&cs=srgb&fm=jpg&q=85", "group": "Beauty & Personal Care"},
    {"id": "electrician", "name": "Electrician", "icon": "zap", "image": "https://images.unsplash.com/photo-1621905252507-b35492cc74b4?crop=entropy&cs=srgb&fm=jpg&q=85", "group": "Construction & Handyman"},
    {"id": "plumber", "name": "Plumber", "icon": "droplet", "image": "https://images.pexels.com/photos/8486978/pexels-photo-8486978.jpeg", "group": "Construction & Handyman"},
    {"id": "cleaner", "name": "Cleaner", "icon": "sparkles", "image": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?crop=entropy&cs=srgb&fm=jpg&q=85", "group": "Home Services"},
    {"id": "carpenter", "name": "Carpenter", "icon": "hammer", "image": "https://images.unsplash.com/photo-1504148455328-c376907d081c?crop=entropy&cs=srgb&fm=jpg&q=85", "group": "Construction & Handyman"},
    {"id": "painter", "name": "Painter", "icon": "paintbrush", "image": "https://images.unsplash.com/photo-1562259949-e8e7689d7828?crop=entropy&cs=srgb&fm=jpg&q=85", "group": "Home Services"},
    {"id": "car_mechanic", "name": "Car Mechanic", "icon": "wrench", "image": "https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?crop=entropy&cs=srgb&fm=jpg&q=85", "group": "Automotive Services"},
    {"id": "photographer", "name": "Photographer", "icon": "camera", "image": "https://images.unsplash.com/photo-1554048612-b6a482bc67e5?crop=entropy&cs=srgb&fm=jpg&q=85", "group": "Creative & Media"},
]

# ============= ROOT ENDPOINT =============
# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Welcome to Kazi Links API"}

# ============= AUTH ENDPOINTS =============
# ============= REGISTRATION PAYWALL =============
# Clients must pay a small M-Pesa Account Verification Fee, professionals a registration fee.
# The user record is created ONLY after M-Pesa callback confirms payment.

class RegistrationPaymentRequest(UserBase):
    password: str


@api_router.post("/auth/register-with-payment")
async def register_with_payment(payload: RegistrationPaymentRequest):
    """Start registration: validates, sends an STK push to the user's phone, and
    stores a pending registration. The user record is only created when the
    M-Pesa callback confirms success.
    """
    # Email uniqueness check
    existing = await db.users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    pending = await db.registration_payments.find_one({
        "email": payload.email,
        "status": "pending",
    })
    if pending:
        raise HTTPException(
            status_code=400,
            detail="A pending registration already exists for this email. Please complete the M-Pesa prompt or wait a few minutes.",
        )

    # Validate phone
    if not payload.phone:
        raise HTTPException(status_code=400, detail="Phone number is required")
    phone = mpesa_service.normalize_phone(payload.phone)
    if not phone.startswith("254") or len(phone) != 12:
        raise HTTPException(
            status_code=400,
            detail="Enter a valid Kenyan phone number (e.g. 2547XXXXXXXX or 07XXXXXXXX).",
        )

    # Determine fee
    if payload.role == UserRole.PROFESSIONAL:
        amount = PROFESSIONAL_REGISTRATION_FEE
        fee_type = "professional_registration"
        fee_label = "Kazi Links Pro Registration"
    elif payload.role == UserRole.CLIENT:
        amount = CLIENT_REGISTRATION_FEE
        fee_type = "client_verification"
        fee_label = "Kazi Links Account Verification"
    else:
        raise HTTPException(status_code=400, detail="Admin registration is not allowed via this endpoint")

    reg_id = str(uuid.uuid4())
    reg_ref = f"REG-{reg_id[:8].upper()}"

    # Initiate STK Push first — only persist if Daraja accepts the request
    try:
        stk_result = await mpesa_service.stk_push(
            phone_number=phone,
            amount=int(amount),
            account_reference=reg_ref,
            transaction_desc=fee_label[:13],  # M-Pesa caps to ~13 chars
        )
    except Exception as e:
        logger.exception("Registration STK push failed")
        raise HTTPException(status_code=502, detail=f"Could not start M-Pesa payment: {e}")

    record = {
        "id": reg_id,
        "reference": reg_ref,
        "fee_type": fee_type,
        "amount": float(amount),
        "status": "pending",
        "name": payload.name,
        "email": payload.email,
        "phone": phone,
        "role": payload.role.value,
        "location": payload.location,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "password_hash": hash_password(payload.password),  # held until verification
        "checkout_request_id": stk_result.get("CheckoutRequestID"),
        "merchant_request_id": stk_result.get("MerchantRequestID"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.registration_payments.insert_one(record)

    return {
        "message": f"M-Pesa prompt sent to {phone}. Enter your PIN to complete registration.",
        "registration_id": reg_id,
        "checkout_request_id": record["checkout_request_id"],
        "reference": reg_ref,
        "amount": float(amount),
        "fee_type": fee_type,
        "phone": phone,
    }


@api_router.get("/auth/registration-status")
async def registration_status(checkout_request_id: str):
    """Poll endpoint. Returns the current status of a pending registration.
    When status='completed', also returns an access_token + user so the
    frontend can sign the user straight in.
    """
    record = await db.registration_payments.find_one(
        {"checkout_request_id": checkout_request_id},
        {"_id": 0, "password_hash": 0},
    )
    if not record:
        raise HTTPException(status_code=404, detail="Unknown registration")
    response = {
        "status": record.get("status", "pending"),
        "amount": record.get("amount"),
        "fee_type": record.get("fee_type"),
        "reference": record.get("reference"),
        "failure_reason": record.get("failure_reason"),
        "mpesa_receipt": record.get("mpesa_receipt"),
    }
    if record.get("status") == "completed" and record.get("user_id"):
        user = await db.users.find_one({"id": record["user_id"]}, {"_id": 0, "password_hash": 0})
        if user:
            response["access_token"] = create_token(user["id"], user["role"])
            created_at = user.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            response["user"] = UserResponse(
                id=user["id"],
                display_id=user.get("display_id"),
                email=user["email"],
                name=user["name"],
                phone=user["phone"],
                role=UserRole(user["role"]),
                location=user.get("location"),
                latitude=user.get("latitude"),
                longitude=user.get("longitude"),
                created_at=created_at,
                wallet_balance=user.get("wallet_balance", 0.0),
                profile_photo=user.get("profile_photo"),
            ).model_dump(mode="json")
    return response


@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if email exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    
    # Generate role-specific display ID
    if user_data.role == UserRole.CLIENT:
        display_id = await generate_client_id()
    elif user_data.role == UserRole.PROFESSIONAL:
        display_id = await generate_professional_id()
    else:
        display_id = f"ADM-{str(uuid.uuid4())[:5].upper()}"
    
    user_doc = {
        "id": user_id,
        "display_id": display_id,
        "email": user_data.email,
        "name": user_data.name,
        "phone": user_data.phone,
        "role": user_data.role.value,
        "location": user_data.location,
        "latitude": user_data.latitude,
        "longitude": user_data.longitude,
        "password_hash": hash_password(user_data.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True,
        "wallet_balance": 0.0,
        "profile_photo": None
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, user_data.role.value)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            display_id=display_id,
            email=user_data.email,
            name=user_data.name,
            phone=user_data.phone,
            role=user_data.role,
            location=user_data.location,
            latitude=user_data.latitude,
            longitude=user_data.longitude,
            created_at=datetime.now(timezone.utc),
            wallet_balance=0.0,
            profile_photo=None
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
            display_id=user.get("display_id"),
            email=user["email"],
            name=user["name"],
            phone=user["phone"],
            role=UserRole(user["role"]),
            location=user.get("location"),
            latitude=user.get("latitude"),
            longitude=user.get("longitude"),
            created_at=created_at,
            wallet_balance=user.get("wallet_balance", 0.0),
            profile_photo=user.get("profile_photo")
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user = Depends(get_current_user)):
    created_at = user.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    
    return UserResponse(
        id=user["id"],
        display_id=user.get("display_id"),
        email=user["email"],
        name=user["name"],
        phone=user["phone"],
        role=UserRole(user["role"]),
        location=user.get("location"),
        latitude=user.get("latitude"),
        longitude=user.get("longitude"),
        created_at=created_at,
        wallet_balance=user.get("wallet_balance", 0.0),
        profile_photo=user.get("profile_photo")
    )

# ============= USER PROFILE ENDPOINTS =============
@api_router.put("/users/profile")
async def update_user_profile(profile_update: UserProfileUpdate, user = Depends(get_current_user)):
    """Update user profile including photo"""
    update_data = {k: v for k, v in profile_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await db.users.update_one({"id": user["id"]}, {"$set": update_data})
    return {"message": "Profile updated successfully"}

@api_router.post("/users/profile-photo")
async def upload_profile_photo(photo_url: str, user = Depends(get_current_user)):
    """Store profile photo URL (base64 data URL or external URL)"""
    await db.users.update_one({"id": user["id"]}, {"$set": {"profile_photo": photo_url}})
    return {"message": "Profile photo updated", "photo_url": photo_url}

# ============= WALLET ENDPOINTS =============
@api_router.get("/wallet/balance")
async def get_wallet_balance(user = Depends(get_current_user)):
    """Get user's wallet balance"""
    balance = user.get("wallet_balance", 0.0)
    return {"balance": balance}

@api_router.get("/wallet/transactions")
async def get_wallet_transactions(user = Depends(get_current_user)):
    """Get user's wallet transaction history"""
    transactions = await db.wallet_transactions.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return transactions

@api_router.post("/wallet/deposit")
async def deposit_to_wallet(deposit: DepositRequest, user = Depends(get_current_user)):
    """Deposit money to wallet via M-Pesa STK Push (Lipa Na M-Pesa Online).
    
    Phone number is always taken from the user's registered profile — clients/pros
    cannot deposit from any other number.
    """
    if deposit.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if deposit.amount > 100000:
        raise HTTPException(status_code=400, detail="Maximum deposit is KSh 100,000")

    registered_phone = (user.get("phone") or "").strip()
    if not registered_phone:
        raise HTTPException(
            status_code=400,
            detail="No registered phone number on file. Please update your profile before depositing.",
        )

    phone = mpesa_service.normalize_phone(registered_phone)
    if not phone.startswith("254") or len(phone) != 12:
        raise HTTPException(
            status_code=400,
            detail="Your registered phone number is invalid. Please update it in your profile (format 2547XXXXXXXX or 07XXXXXXXX).",
        )

    # Generate transaction reference
    txn_id = await generate_transaction_id()
    reference = f"DEP-{txn_id}"

    # Initiate STK Push with Safaricom
    try:
        stk_response = await mpesa_service.stk_push(
            phone_number=phone,
            amount=deposit.amount,
            account_reference=reference,
            transaction_desc="Wallet Deposit",
        )
    except Exception as e:
        logger.exception("M-Pesa STK push failed for user %s", user["id"])
        raise HTTPException(status_code=502, detail=f"M-Pesa request failed: {str(e)}")

    checkout_request_id = stk_response.get("CheckoutRequestID")
    merchant_request_id = stk_response.get("MerchantRequestID")

    # Persist pending transaction. Wallet balance and ledger entry are only updated after Safaricom callback confirms success.
    transaction_doc = {
        "id": str(uuid.uuid4()),
        "transaction_id": txn_id,
        "user_id": user["id"],
        "user_display_id": user.get("display_id"),
        "type": "deposit",
        "amount": deposit.amount,
        "status": "pending",
        "reference": reference,
        "phone_number": phone,
        "checkout_request_id": checkout_request_id,
        "merchant_request_id": merchant_request_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.wallet_transactions.insert_one(transaction_doc)

    return {
        "message": "STK Push sent. Check your phone and enter your M-Pesa PIN to complete the deposit.",
        "transaction_id": txn_id,
        "checkout_request_id": checkout_request_id,
        "merchant_request_id": merchant_request_id,
        "customer_message": stk_response.get("CustomerMessage"),
        "amount": deposit.amount,
        "status": "pending",
    }


@api_router.get("/wallet/deposit/status/{checkout_request_id}")
async def get_deposit_status(checkout_request_id: str, user = Depends(get_current_user)):
    """Poll the status of an M-Pesa deposit transaction by CheckoutRequestID."""
    txn = await db.wallet_transactions.find_one(
        {"checkout_request_id": checkout_request_id, "user_id": user["id"]},
        {"_id": 0},
    )
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # If still pending and older than ~10s, query Safaricom directly as fallback
    if txn.get("status") == "pending":
        try:
            created_at = datetime.fromisoformat(txn["created_at"])
            if datetime.now(timezone.utc) - created_at > timedelta(seconds=10):
                query_resp = await mpesa_service.query_stk_status(checkout_request_id)
                # Result codes: "0" success, "1032" cancelled, "1037" timeout, "1" insufficient funds, etc.
                result_code = query_resp.get("ResultCode")
                if result_code is not None and str(result_code) != "0" and str(result_code) != "1037":
                    # Mark as failed if Safaricom says it definitively failed (not still in progress)
                    if str(result_code) not in ["1037", ""]:
                        await db.wallet_transactions.update_one(
                            {"checkout_request_id": checkout_request_id, "status": "pending"},
                            {"$set": {
                                "status": "failed",
                                "failure_code": str(result_code),
                                "failure_reason": query_resp.get("ResultDesc"),
                                "failed_at": datetime.now(timezone.utc).isoformat(),
                            }},
                        )
        except Exception:
            pass  # Polling fallback is best-effort

        txn = await db.wallet_transactions.find_one(
            {"checkout_request_id": checkout_request_id, "user_id": user["id"]},
            {"_id": 0},
        )

    new_balance = (await db.users.find_one({"id": user["id"]}, {"_id": 0, "wallet_balance": 1}) or {}).get("wallet_balance", 0.0)

    return {
        "status": txn.get("status"),
        "amount": txn.get("amount"),
        "mpesa_receipt": txn.get("mpesa_receipt"),
        "failure_reason": txn.get("failure_reason"),
        "new_balance": new_balance,
    }


@api_router.post("/mpesa/callback/{secret}")
async def mpesa_callback(secret: str, request: Request):
    """
    Safaricom M-Pesa STK Push callback endpoint.
    Always returns 200 OK to prevent Safaricom retries; processing logged & idempotent.
    """
    expected_secret = os.environ.get("MPESA_CALLBACK_SECRET", "")
    if not expected_secret or secret != expected_secret:
        logger.warning("M-Pesa callback received with invalid secret: %s", secret)
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    try:
        payload = await request.json()
    except Exception:
        logger.warning("M-Pesa callback received with invalid JSON")
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    logger.info("M-Pesa callback received: %s", payload)

    parsed = mpesa_service.parse_callback(payload)
    checkout_request_id = parsed.get("checkout_request_id")
    if not checkout_request_id:
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    # First, check if this is a REGISTRATION PAYMENT (paywall) STK response
    reg = await db.registration_payments.find_one({"checkout_request_id": checkout_request_id})
    if reg:
        if reg.get("status") != "pending":
            return {"ResultCode": 0, "ResultDesc": "Accepted"}
        if parsed.get("result_code") == 0:
            # Success — create the user record now
            user_id = str(uuid.uuid4())
            if reg["role"] == UserRole.CLIENT.value:
                display_id = await generate_client_id()
            elif reg["role"] == UserRole.PROFESSIONAL.value:
                display_id = await generate_professional_id()
            else:
                display_id = f"USR-{user_id[:5].upper()}"
            user_doc = {
                "id": user_id,
                "display_id": display_id,
                "email": reg["email"],
                "name": reg["name"],
                "phone": reg["phone"],
                "role": reg["role"],
                "location": reg.get("location"),
                "latitude": reg.get("latitude"),
                "longitude": reg.get("longitude"),
                "password_hash": reg["password_hash"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True,
                "wallet_balance": 0.0,
                "profile_photo": None,
                "registration_fee_paid": reg["amount"],
                "registration_paid_at": datetime.now(timezone.utc).isoformat(),
                "registration_mpesa_receipt": parsed.get("mpesa_receipt"),
            }
            try:
                await db.users.insert_one(user_doc)
            except Exception as e:
                logger.exception("Failed to create user from registration payment")
                await db.registration_payments.update_one(
                    {"id": reg["id"]},
                    {"$set": {"status": "failed", "failure_reason": f"User creation failed: {e}"}},
                )
                return {"ResultCode": 0, "ResultDesc": "Accepted"}

            await db.registration_payments.update_one(
                {"id": reg["id"]},
                {"$set": {
                    "status": "completed",
                    "user_id": user_id,
                    "user_display_id": display_id,
                    "mpesa_receipt": parsed.get("mpesa_receipt"),
                    "mpesa_transaction_id": parsed.get("mpesa_receipt"),
                    "mpesa_transaction_date": parsed.get("transaction_date"),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }},
            )
            # Ledger entry — platform revenue
            try:
                await create_ledger_entry(
                    entry_type=LedgerEntryType.PLATFORM_FEE,
                    user_id=user_id,
                    amount=float(reg["amount"]),
                    description=(
                        "Account verification fee" if reg["fee_type"] == "client_verification"
                        else "Professional registration fee"
                    ),
                    reference_id=reg["reference"],
                    reference_type=reg["fee_type"],
                    metadata={
                        "phone": reg["phone"],
                        "mpesa_receipt": parsed.get("mpesa_receipt"),
                        "checkout_request_id": checkout_request_id,
                        "role": reg["role"],
                    },
                )
            except Exception:
                logger.exception("Ledger entry for registration fee failed (non-fatal)")
            logger.info("Registration completed via M-Pesa: %s (%s) → user=%s", reg["email"], reg["fee_type"], user_id)
        else:
            await db.registration_payments.update_one(
                {"id": reg["id"]},
                {"$set": {
                    "status": "failed",
                    "failure_code": str(parsed.get("result_code")),
                    "failure_reason": parsed.get("result_desc"),
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                }},
            )
            logger.info("Registration M-Pesa payment failed: %s — %s", checkout_request_id, parsed.get("result_desc"))
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    # Next, check if this is a BOOKING-ESCROW top-up rather than a plain wallet deposit
    payment_doc = await db.payments.find_one({"checkout_request_id": checkout_request_id})
    if payment_doc:
        # Idempotency
        if payment_doc.get("status") != "awaiting_topup":
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

        if parsed.get("result_code") == 0:
            # Success: payment now fully held in escrow
            await db.payments.update_one(
                {"id": payment_doc["id"]},
                {"$set": {
                    "status": PaymentStatus.ESCROW.value,
                    "mpesa_receipt": parsed.get("mpesa_receipt"),
                    "mpesa_transaction_id": parsed.get("mpesa_receipt") or payment_doc.get("mpesa_transaction_id"),
                    "mpesa_transaction_date": parsed.get("transaction_date"),
                    "topup_completed_at": datetime.now(timezone.utc).isoformat(),
                }},
            )
            topup_amount = float(payment_doc.get("topup_required") or 0)
            await create_ledger_entry(
                entry_type=LedgerEntryType.ESCROW_IN,
                user_id=payment_doc["client_id"],
                amount=topup_amount,
                description=f"Booking payment (M-Pesa top-up) {payment_doc.get('booking_display_id', '')}",
                reference_id=payment_doc.get("display_id"),
                reference_type="payment_topup",
                related_user_id=payment_doc.get("professional_id"),
                metadata={
                    "booking_id": payment_doc.get("booking_id"),
                    "phone": payment_doc.get("topup_phone"),
                    "mpesa_receipt": parsed.get("mpesa_receipt"),
                    "checkout_request_id": checkout_request_id,
                    "topup_amount": topup_amount,
                },
            )
            await db.bookings.update_one(
                {"id": payment_doc["booking_id"]},
                {"$set": {"status": BookingStatus.CONFIRMED.value}},
            )
            logger.info("Booking escrow funded: %s KSh %s", checkout_request_id, topup_amount)
        else:
            # Failure: refund wallet portion + mark payment failed
            wallet_used = float(payment_doc.get("wallet_used") or 0)
            if wallet_used > 0:
                await db.users.update_one(
                    {"id": payment_doc["client_id"]},
                    {"$inc": {"wallet_balance": wallet_used}},
                )
            await db.payments.update_one(
                {"id": payment_doc["id"]},
                {"$set": {
                    "status": "failed",
                    "failure_code": str(parsed.get("result_code")),
                    "failure_reason": parsed.get("result_desc"),
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                }},
            )
            logger.info("Booking escrow top-up failed: %s — %s; refunded wallet KSh %s",
                        checkout_request_id, parsed.get("result_desc"), wallet_used)
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    # Otherwise this is a plain wallet deposit — original flow
    txn = await db.wallet_transactions.find_one({"checkout_request_id": checkout_request_id})
    if not txn:
        logger.warning("M-Pesa callback for unknown CheckoutRequestID: %s", checkout_request_id)
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    if txn.get("status") != "pending":
        logger.info("M-Pesa callback already processed for %s", checkout_request_id)
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    if parsed.get("result_code") == 0:
        # Success path
        confirmed_amount = parsed.get("amount") or txn["amount"]
        await db.wallet_transactions.update_one(
            {"checkout_request_id": checkout_request_id, "status": "pending"},
            {"$set": {
                "status": "completed",
                "amount": confirmed_amount,
                "mpesa_receipt": parsed.get("mpesa_receipt"),
                "mpesa_transaction_date": parsed.get("transaction_date"),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }},
        )

        # Create immutable ledger entry and credit wallet
        await create_ledger_entry(
            entry_type=LedgerEntryType.DEPOSIT,
            user_id=txn["user_id"],
            amount=confirmed_amount,
            description=f"Wallet deposit via M-Pesa from {txn.get('phone_number')}",
            reference_id=txn.get("transaction_id"),
            reference_type="wallet_deposit",
            metadata={
                "phone_number": txn.get("phone_number"),
                "mpesa_receipt": parsed.get("mpesa_receipt"),
                "checkout_request_id": checkout_request_id,
            },
        )

        await db.users.update_one(
            {"id": txn["user_id"]},
            {"$inc": {"wallet_balance": confirmed_amount}},
        )
        logger.info("M-Pesa deposit completed: %s KSh %s", checkout_request_id, confirmed_amount)
    else:
        # Failure / cancellation path
        await db.wallet_transactions.update_one(
            {"checkout_request_id": checkout_request_id, "status": "pending"},
            {"$set": {
                "status": "failed",
                "failure_code": str(parsed.get("result_code")),
                "failure_reason": parsed.get("result_desc"),
                "failed_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        logger.info("M-Pesa deposit failed: %s - %s", checkout_request_id, parsed.get("result_desc"))

    return {"ResultCode": 0, "ResultDesc": "Accepted"}

@api_router.get("/wallet/withdraw-quote")
async def withdraw_quote(amount: float, user = Depends(get_current_user)):
    """Return the fee breakdown for a proposed withdrawal so the UI can show it
    before the user confirms.
    """
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    fb = _calc_withdrawal_total(amount, role=user.get("role", "client"))
    wallet_balance = float(user.get("wallet_balance") or 0)
    return {
        **fb,
        "wallet_balance": round(wallet_balance, 2),
        "sufficient_funds": fb["gross"] <= wallet_balance,
    }


@api_router.post("/wallet/withdraw")
async def withdraw_from_wallet(withdrawal: WithdrawalRequest, user = Depends(get_current_user)):
    """Withdraw money from wallet (M-Pesa - MOCKED).
    
    Phone number is always taken from the user's registered profile — clients/pros
    cannot withdraw to any other number.
    """
    if withdrawal.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    fee_breakdown = _calc_withdrawal_total(withdrawal.amount, role=user.get("role", "client"))
    gross = fee_breakdown["gross"]

    current_balance = float(user.get("wallet_balance", 0.0))
    if gross > current_balance:
        if user.get("role") == "professional":
            fee_desc = f"KSh {int(PROFESSIONAL_WITHDRAWAL_FIXED_FEE)} fixed fee"
        else:
            fee_desc = f"3% + KSh {int(WITHDRAWAL_FIXED_FEE)} fees"
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient wallet balance. You need KSh {gross:,.2f} (KSh {fee_breakdown['amount']:,.2f}"
                f" + {fee_desc}) but have KSh {current_balance:,.2f}."
            ),
        )

    registered_phone = (user.get("phone") or "").strip()
    if not registered_phone:
        raise HTTPException(
            status_code=400,
            detail="No registered phone number on file. Please update your profile before withdrawing.",
        )

    phone = mpesa_service.normalize_phone(registered_phone)
    if not phone.startswith("254") or len(phone) != 12:
        raise HTTPException(
            status_code=400,
            detail="Your registered phone number is invalid. Please update it in your profile (format 2547XXXXXXXX or 07XXXXXXXX).",
        )

    # Generate transaction ID
    txn_id = await generate_transaction_id()

    # Create wallet transaction record (records the AMOUNT sent to M-Pesa; fee fields are separate)
    transaction_id = str(uuid.uuid4())
    transaction_doc = {
        "id": transaction_id,
        "transaction_id": txn_id,
        "user_id": user["id"],
        "user_display_id": user.get("display_id"),
        "type": "withdrawal",
        "amount": fee_breakdown["amount"],                        # Net to user via M-Pesa
        "fee_percent": WITHDRAWAL_FEE_PERCENT,
        "fee_amount": fee_breakdown["withdrawal_fee_amount"],     # 3% of amount
        "fixed_fee": fee_breakdown["fixed_fee"],                  # KSh 20
        "fee_total": fee_breakdown["fee_total"],
        "gross_amount": gross,                                    # Total deducted from wallet
        "status": "completed",  # MOCKED - instant success
        "reference": f"MPESA-WD-{txn_id}",
        "phone_number": phone,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.wallet_transactions.insert_one(transaction_doc)

    # Ledger entry for the net withdrawal (money leaving platform → user M-Pesa)
    await create_ledger_entry(
        entry_type=LedgerEntryType.WITHDRAWAL,
        user_id=user["id"],
        amount=fee_breakdown["amount"],
        description=f"Wallet withdrawal to M-Pesa {phone}",
        reference_id=txn_id,
        reference_type="wallet_withdrawal",
        metadata={
            "phone_number": phone,
            "mpesa_ref": transaction_doc["reference"],
            "fee_amount": fee_breakdown["withdrawal_fee_amount"],
            "fixed_fee": fee_breakdown["fixed_fee"],
            "gross": gross,
        },
    )

    # Ledger entry for the fee (platform revenue)
    fee_desc_text = (
        f"Withdrawal fee (KSh {int(PROFESSIONAL_WITHDRAWAL_FIXED_FEE)})"
        if user.get("role") == "professional"
        else f"Withdrawal fee (3% + KSh {int(WITHDRAWAL_FIXED_FEE)})"
    )
    await create_ledger_entry(
        entry_type=LedgerEntryType.PLATFORM_FEE,
        user_id=user["id"],
        amount=fee_breakdown["fee_total"],
        description=fee_desc_text,
        reference_id=txn_id,
        reference_type="withdrawal_fee",
        metadata={
            "fee_percent": WITHDRAWAL_FEE_PERCENT,
            "fee_amount": fee_breakdown["withdrawal_fee_amount"],
            "fixed_fee": fee_breakdown["fixed_fee"],
            "wallet_txn_id": txn_id,
        },
    )

    # Deduct the GROSS amount (amount + fees) from the wallet
    await db.users.update_one(
        {"id": user["id"]},
        {"$inc": {"wallet_balance": -gross}},
    )

    # Get new balance
    updated_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})

    return {
        "message": "Withdrawal successful (MOCKED) - Sent to M-Pesa",
        "transaction_id": txn_id,
        "amount": fee_breakdown["amount"],
        "fee_amount": fee_breakdown["withdrawal_fee_amount"],
        "fixed_fee": fee_breakdown["fixed_fee"],
        "fee_total": fee_breakdown["fee_total"],
        "gross_charged": gross,
        "new_balance": updated_user.get("wallet_balance", 0.0),
    }

# ============= PUSH NOTIFICATION ENDPOINTS =============
@api_router.post("/notifications/subscribe")
async def subscribe_to_push(subscription: PushSubscriptionCreate, user = Depends(get_current_user)):
    """Subscribe user to push notifications"""
    # Check if subscription exists
    existing = await db.push_subscriptions.find_one({
        "user_id": user["id"],
        "endpoint": subscription.endpoint
    })
    
    if existing:
        return {"message": "Already subscribed"}
    
    sub_doc = {
        "user_id": user["id"],
        "endpoint": subscription.endpoint,
        "keys": subscription.keys,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.push_subscriptions.insert_one(sub_doc)
    return {"message": "Successfully subscribed to notifications"}

@api_router.delete("/notifications/unsubscribe")
async def unsubscribe_from_push(endpoint: str, user = Depends(get_current_user)):
    """Unsubscribe from push notifications"""
    await db.push_subscriptions.delete_one({
        "user_id": user["id"],
        "endpoint": endpoint
    })
    return {"message": "Unsubscribed from notifications"}

async def send_push_notification(user_id: str, title: str, body: str, data: dict = None):
    """Send push notification to a user (helper function)"""
    # Get user's subscriptions
    subscriptions = await db.push_subscriptions.find({"user_id": user_id}, {"_id": 0}).to_list(10)
    
    # Store notification in database
    notification_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title,
        "body": body,
        "data": data or {},
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification_doc)
    
    # In production, you would send to push service here
    # For now, we just store in database
    return len(subscriptions)

@api_router.get("/notifications")
async def get_notifications(user = Depends(get_current_user)):
    """Get user's notifications"""
    notifications = await db.notifications.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return notifications

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user = Depends(get_current_user)):
    """Mark notification as read"""
    await db.notifications.update_one(
        {"id": notification_id, "user_id": user["id"]},
        {"$set": {"read": True}}
    )
    return {"message": "Notification marked as read"}

# ============= CATEGORIES ENDPOINT =============
@api_router.get("/categories")
async def get_categories():
    return sorted(PROFESSIONAL_CATEGORIES, key=lambda c: c.get("name", "").lower())

@api_router.get("/categories/grouped")
async def get_categories_grouped():
    """Get categories organized by group, sorted alphabetically within each group."""
    groups = {}
    for cat in PROFESSIONAL_CATEGORIES:
        group = cat.get("group", "Other")
        if group not in groups:
            groups[group] = []
        groups[group].append(cat)
    for group in groups:
        groups[group].sort(key=lambda c: c.get("name", "").lower())
    # Return groups sorted alphabetically by group name as well
    return {k: groups[k] for k in sorted(groups.keys(), key=str.lower)}

@api_router.get("/categories/featured")
async def get_featured_categories():
    """Get featured categories with images for landing page"""
    return FEATURED_CATEGORIES

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

def _apply_sort(results, sort_by):
    """Apply user-selected sort. Falls back to rating desc when sort_by is unknown."""
    sort_by = (sort_by or "best_match").lower()
    if sort_by == "rating":
        results.sort(key=lambda p: (p.get("rating") or 0, p.get("total_reviews") or 0), reverse=True)
    elif sort_by == "experience":
        results.sort(key=lambda p: p.get("experience_years") or 0, reverse=True)
    elif sort_by == "reviews":
        results.sort(key=lambda p: p.get("total_reviews") or 0, reverse=True)
    elif sort_by == "price_low":
        results.sort(key=lambda p: p.get("hourly_rate") or 9_999_999)
    elif sort_by == "price_high":
        results.sort(key=lambda p: p.get("hourly_rate") or 0, reverse=True)
    else:
        # best_match: keep current ordering if it was scored; otherwise sort by rating
        if results and "_score" not in results[0]:
            results.sort(key=lambda p: (p.get("rating") or 0, p.get("total_reviews") or 0), reverse=True)
    return results


@api_router.get("/professionals/search")
async def search_professionals(
    q: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_rate: Optional[float] = None,
    sort_by: Optional[str] = "best_match",
):
    """Search professionals by name, category, location, rating, rate, or semantic intent.

    Free-text search supports:
      - Exact substring (name / profession / skills / bio)
      - Token-based weighted scoring across fields
      - Lightweight semantic intent (e.g. "need nails done" → Nail Technician,
        "windshield" → Car Mechanic, "leak" → Plumber). No AI call — fast & deterministic.

    sort_by accepts: best_match (default — text+rating tie-breaker), rating, experience,
    reviews, price_low, price_high.
    """
    q_trim = (q or "").strip()
    q_lower = q_trim.lower()
    location_lower = (location or "").strip().lower()
    category_in = (category or "").strip().lower()

    # Map category id (snake_case) → profession name regex (e.g. 'tattoo_artist' → 'tattoo artist')
    category_regex = None
    if category_in:
        category_regex = category_in.replace("_", " ").replace("-", " ")

    # Tokenize free-text query
    raw_tokens = [t for t in re.findall(r"\w+", q_lower) if len(t) > 1]

    # Lightweight semantic intent: keyword → list of profession keywords to expand search
    expanded_profession_keywords = set()
    expanded_categories = set()  # for matching against profession field
    for tok in raw_tokens:
        for prof_kw, expansions in PROFESSION_INTENT_MAP.items():
            if tok == prof_kw or tok in expansions["tokens"]:
                for p in expansions["professions"]:
                    expanded_profession_keywords.add(p.lower())
                    expanded_categories.add(p.lower())
                break

    # Build base Mongo query: category filter narrows aggressively; otherwise broad
    base_query = {"availability": True}
    # Words too generic to use as a profession-name fallback alone
    _GENERIC_TAIL_WORDS = {"technician", "specialist", "expert", "installer", "service",
                           "agency", "manager", "assistant", "engineer"}

    profession_or_clauses = []
    for kw in expanded_profession_keywords:
        profession_or_clauses.append({"profession": {"$regex": kw, "$options": "i"}})
        # Also try the last word alone (e.g. 'car mechanic' → 'mechanic') unless too generic
        parts = kw.split()
        if len(parts) > 1 and parts[-1] not in _GENERIC_TAIL_WORDS:
            profession_or_clauses.append({"profession": {"$regex": parts[-1], "$options": "i"}})

    if category_regex:
        # Try the full phrase first
        category_or = [{"profession": {"$regex": category_regex, "$options": "i"}}]
        # Add last-word fallback so 'car mechanic' also finds 'Mechanic', 'private chef' finds 'Chef', etc.
        cat_parts = category_regex.split()
        if len(cat_parts) > 1 and cat_parts[-1] not in _GENERIC_TAIL_WORDS:
            category_or.append({"profession": {"$regex": cat_parts[-1], "$options": "i"}})
        base_query["$or"] = category_or
    elif profession_or_clauses:
        base_query["$or"] = profession_or_clauses

    profs = await db.professional_profiles.find(base_query, {"_id": 0}).to_list(300)

    # If semantic narrowing produced nothing, broaden so q can still match by name/skills/bio
    if not profs and expanded_profession_keywords and not category_regex:
        broad_query = {"availability": True}
        profs = await db.professional_profiles.find(broad_query, {"_id": 0}).to_list(300)

    # Enrich with user data
    enriched = []
    for prof in profs:
        u = await db.users.find_one({"id": prof["user_id"]}, {"_id": 0, "password_hash": 0})
        if not u:
            continue
        prof["user"] = _strip_phone(u)
        enriched.append(prof)

    # Apply location, rating, rate filters
    if location_lower:
        enriched = [p for p in enriched if location_lower in (p["user"].get("location") or "").lower()]
    if min_rating is not None:
        enriched = [p for p in enriched if (p.get("rating") or 0) >= float(min_rating)]
    if max_rate is not None:
        enriched = [p for p in enriched if (p.get("hourly_rate") or 0) <= float(max_rate)]

    # If a free-text query is present, score each candidate; otherwise rank by rating
    if q_trim:
        def _score(p):
            u = p["user"]
            name = (u.get("name") or "").lower()
            username = (u.get("username") or "").lower()
            display_id = (u.get("display_id") or "").lower()
            profession = (p.get("profession") or "").lower()
            skills = " ".join(p.get("skills") or []).lower()
            bio = (p.get("bio") or "").lower()
            haystack = f"{name} {username} {display_id} {profession} {skills} {bio}"

            score = 0
            # Whole-query substring match (highest signal)
            if q_lower and q_lower in haystack:
                score += 50
            # Per-token weighted match
            for tok in raw_tokens:
                if tok in name:        score += 8
                if tok in username:    score += 5
                if tok in display_id:  score += 5
                if tok in profession:  score += 6
                if tok in skills:      score += 4
                if tok in bio:         score += 2
            # Semantic intent: synonyms mapped to professions/skills
            for sem_kw in expanded_profession_keywords:
                if sem_kw in profession:
                    score += 20
                elif sem_kw in skills or sem_kw in bio:
                    score += 8
                else:
                    # Also try the last word of multi-word profession (e.g. 'mechanic' from 'car mechanic')
                    parts = sem_kw.split()
                    if len(parts) > 1 and parts[-1] not in _GENERIC_TAIL_WORDS and parts[-1] in profession:
                        score += 12
            # Tie-breaker: small rating boost ONLY when we already have a real content match
            if score > 0:
                score += min((p.get("rating") or 0) * 1.5, 7.5)
            return score

        for p in enriched:
            p["_score"] = _score(p)

        matched = [p for p in enriched if p["_score"] > 0]
        # If query had no token hits but the user applied real filters (category/location), still show filter results
        if not matched and (category_regex or location_lower):
            matched = enriched

        # Sort by score desc, then rating desc
        matched.sort(key=lambda p: (p["_score"], p.get("rating") or 0), reverse=True)
        for p in matched:
            p.pop("_score", None)
        return _apply_sort(matched, sort_by)

    # No free-text — sort by rating (or whatever user asked)
    return _apply_sort(enriched, sort_by)

@api_router.get("/professionals/{professional_id}")
async def get_professional_detail(
    professional_id: str,
    requester = Depends(get_optional_user),
):
    profile = await db.professional_profiles.find_one({"user_id": professional_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")

    user = await db.users.find_one({"id": professional_id}, {"_id": 0, "password_hash": 0})

    # Phone is only visible if requester has a confirmed/in_progress/completed booking with this pro,
    # OR if the requester IS the professional themselves, OR an admin.
    can_see_phone = False
    if requester:
        if requester.get("id") == professional_id or requester.get("role") == "admin":
            can_see_phone = True
        elif await _has_active_booking(requester["id"], professional_id):
            can_see_phone = True

    profile["user"] = user if can_see_phone else _strip_phone(user)
    profile["phone_visible"] = can_see_phone

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
    job_display_id = await generate_job_id()
    
    job_doc = {
        "id": job_id,
        "display_id": job_display_id,
        "client_id": user["id"],
        "client_display_id": user.get("display_id"),
        **job_data.model_dump(),
        "status": JobStatus.OPEN.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "matched_professional_id": None
    }
    
    await db.jobs.insert_one(job_doc)
    
    # Send push notifications to professionals in matching category
    matching_profiles = await db.professional_profiles.find({
        "profession": {"$regex": job_data.category, "$options": "i"},
        "availability": True
    }).to_list(100)
    
    for profile in matching_profiles:
        await send_push_notification(
            user_id=profile["user_id"],
            title="New Job Alert! 🔔",
            body=f"New {job_data.category} job posted: {job_data.title} - KSh {job_data.budget}",
            data={"type": "new_job", "job_id": job_id, "job_display_id": job_display_id}
        )
    
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

def _profession_to_category_clauses(profession: str) -> list:
    """Build a Mongo $or list of category regexes that match how categories are
    typically stored (e.g. 'car_mechanic', 'mc_host', 'tattoo_artist') from a
    profession display name (e.g. 'Car Mechanic', 'MC / Host', 'Tattoo Artist').
    Also matches the last meaningful word alone (e.g. 'Mechanic') so that a
    'Car Mechanic' pro still sees jobs categorised plainly as 'mechanic'.
    """
    if not profession:
        return []
    # Tokenize: keep word-chars only
    tokens = [t.lower() for t in re.findall(r"\w+", profession) if t]
    if not tokens:
        return []
    GENERIC_TAILS = {"technician", "specialist", "expert", "installer", "service",
                     "agency", "manager", "assistant", "engineer"}
    clauses = []
    # Full slug with flexible separator: 'car mechanic' → /car[\s_-]?mechanic/i
    if len(tokens) > 1:
        sep_pattern = r"[\s_\-/]*"
        full_re = sep_pattern.join(re.escape(t) for t in tokens)
        clauses.append({"category": {"$regex": full_re, "$options": "i"}})
        # Last meaningful word fallback
        tail = tokens[-1]
        if tail not in GENERIC_TAILS:
            clauses.append({"category": {"$regex": r"\b" + re.escape(tail) + r"\b", "$options": "i"}})
    else:
        clauses.append({"category": {"$regex": r"\b" + re.escape(tokens[0]) + r"\b", "$options": "i"}})
    return clauses


@api_router.get("/jobs/available")
async def get_available_jobs(
    category: Optional[str] = None, 
    location: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Get available jobs for professionals to bid on - filtered by their profession category and location"""
    if user["role"] != "professional":
        raise HTTPException(status_code=403, detail="Only professionals can view available jobs")
    
    # Get professional's profile to filter by their category
    profile = await db.professional_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    
    query = {"status": JobStatus.OPEN.value}
    
    # Filter jobs by professional's category/profession
    if profile and profile.get("profession"):
        # Map profession to matching job categories. Multi-word professions like
        # "Car Mechanic", "MC / Host", "Tattoo Artist" need to match categories
        # stored as "car_mechanic", "mc_host", "tattoo_artist", etc.
        profession = profile["profession"].strip()
        prof_or = _profession_to_category_clauses(profession)
        if prof_or:
            query["$or"] = prof_or
    elif category:
        query["category"] = {"$regex": re.escape(category), "$options": "i"}
    
    # Filter by location if user has location set
    user_location = user.get("location")
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    elif user_location:
        # Show jobs in user's area first (but don't exclude others)
        pass
    
    jobs = await db.jobs.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Sort jobs by location proximity if user has location
    if user_location:
        def location_match_score(job):
            job_loc = job.get("location", "").lower()
            user_loc = user_location.lower()
            if user_loc in job_loc or job_loc in user_loc:
                return 0  # Same location - highest priority
            return 1
        jobs.sort(key=location_match_score)
    
    # Enrich with client info and check if user already bid
    for job in jobs:
        client = await db.users.find_one({"id": job["client_id"]}, {"_id": 0, "password_hash": 0})
        job["client"] = client
        # Check if current professional already bid on this job
        existing_bid = await db.bids.find_one({"job_id": job["id"], "professional_id": user["id"]})
        job["has_bid"] = existing_bid is not None
        job["bid_count"] = await db.bids.count_documents({"job_id": job["id"]})
        # Calculate location match
        if user_location:
            job["location_match"] = user_location.lower() in job.get("location", "").lower()
    
    return {"jobs": jobs, "profession": profile.get("profession") if profile else None, "user_location": user_location}

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

@api_router.post("/bids/ai-suggest")
async def get_ai_bid_suggestion(job_id: str, user = Depends(get_current_user)):
    """Get AI-powered bid suggestion for a job"""
    if user["role"] != "professional":
        raise HTTPException(status_code=403, detail="Only professionals can get bid suggestions")
    
    # Get job details
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get professional's profile
    profile = await db.professional_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=400, detail="Please create a profile first")
    
    # Get professional's past successful bids
    past_bids = await db.bids.find({
        "professional_id": user["id"],
        "status": "accepted"
    }, {"_id": 0}).to_list(10)
    
    if not EMERGENT_LLM_KEY:
        # Fallback suggestion without AI
        suggested_price = job["budget"] * 0.9  # 10% below budget
        return {
            "suggested_price": round(suggested_price, 0),
            "suggested_hours": None,
            "suggested_message": f"Hello! I'm an experienced {profile.get('profession', 'professional')} with {profile.get('experience_years', 0)} years of experience. I'm interested in your {job['title']} project and can deliver quality work within your budget.",
            "ai_powered": False
        }
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"bid-suggest-{uuid.uuid4()}",
            system_message="""You are an AI assistant helping professionals write winning bids on Kazi Links marketplace.
            Analyze the job requirements and professional's profile to suggest:
            1. A competitive price (typically 5-15% below budget for better chances)
            2. Estimated hours based on job complexity
            3. A personalized, professional message that highlights relevant experience
            Return JSON format: {"price": number, "hours": number, "message": "string"}"""
        ).with_model("gemini", "gemini-3-flash-preview")
        
        past_bid_info = ""
        if past_bids:
            avg_price = sum(b["proposed_price"] for b in past_bids) / len(past_bids)
            past_bid_info = f"Average winning bid price: KSh {avg_price:.0f}"
        
        user_message = UserMessage(
            text=f"""Job Details:
            - Title: {job['title']}
            - Description: {job['description']}
            - Category: {job['category']}
            - Budget: KSh {job['budget']}
            - Location: {job['location']}
            
            Professional Profile:
            - Name: {user.get('name', 'Professional')}
            - Profession: {profile.get('profession', 'N/A')}
            - Experience: {profile.get('experience_years', 0)} years
            - Skills: {', '.join(profile.get('skills', []))}
            - Hourly Rate: KSh {profile.get('hourly_rate', 'N/A')}
            - Rating: {profile.get('rating', 0)}/5 ({profile.get('total_reviews', 0)} reviews)
            {past_bid_info}
            
            Generate a competitive bid suggestion. Return ONLY valid JSON."""
        )
        
        response = await chat.send_message(user_message)
        
        # Parse AI response
        import json
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                suggestion = json.loads(response[json_start:json_end])
                return {
                    "suggested_price": suggestion.get("price", job["budget"] * 0.9),
                    "suggested_hours": suggestion.get("hours"),
                    "suggested_message": suggestion.get("message", ""),
                    "ai_powered": True
                }
        except json.JSONDecodeError:
            logger.warning("Could not parse AI bid suggestion")
    except Exception as e:
        logger.error(f"AI bid suggestion error: {e}")
    
    # Fallback
    return {
        "suggested_price": round(job["budget"] * 0.9, 0),
        "suggested_hours": None,
        "suggested_message": f"Hello! I'm an experienced {profile.get('profession', 'professional')} with {profile.get('experience_years', 0)} years of experience. I'm interested in your project and ready to deliver quality work.",
        "ai_powered": False
    }

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
    
    # Send push notification to professional
    await send_push_notification(
        user_id=bid["professional_id"],
        title="Bid Accepted! 🎉",
        body=f"Your bid for '{job['title']}' has been accepted! Check your bookings.",
        data={"type": "bid_accepted", "booking_id": booking_id}
    )
    
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

    # Combine all natural-language signals from the request into one query string
    raw_query = " ".join([
        (match_request.query or "").strip(),
        (match_request.job_description or "").strip(),
    ]).strip()

    if not raw_query and not match_request.category:
        raise HTTPException(status_code=400, detail="Please describe what you need or provide a category")

    # === Step 1: Use Gemini Flash to extract structured intent from the natural-language query ===
    parsed_intent = {
        "name": None,
        "profession": match_request.category if isinstance(match_request.category, str) else None,
        "skills": [],
        "location": match_request.location if isinstance(match_request.location, str) else None,
        "summary": raw_query,
    }

    if raw_query and EMERGENT_LLM_KEY:
        try:
            parser_chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"match-parse-{uuid.uuid4()}",
                system_message=(
                    "You are an intent parser for a Kenyan services marketplace called Kazi Links. "
                    "Given a user's free-text search, extract structured filters. "
                    "Return ONLY a strict JSON object with keys: name (string|null - person's first or full name if mentioned), "
                    "profession (string|null - the trade or job title like 'plumber', 'mechanic', 'electrician', 'barber'), "
                    "skills (array of short skill keywords like ['fix sink', 'leak repair']), "
                    "location (string|null - city, suburb, or 'near me'). "
                    "Do not include explanations, only the JSON."
                ),
            ).with_model("gemini", "gemini-3-flash-preview")

            parse_resp = await parser_chat.send_message(
                UserMessage(text=f"User search: \"{raw_query}\"\nReturn JSON only.")
            )
            import json as _json
            j_start = parse_resp.find("{")
            j_end = parse_resp.rfind("}") + 1
            if j_start >= 0 and j_end > j_start:
                extracted = _json.loads(parse_resp[j_start:j_end])
                if isinstance(extracted, dict):
                    name_val = extracted.get("name")
                    if isinstance(name_val, str) and name_val.strip():
                        parsed_intent["name"] = name_val.strip()
                    prof_val = extracted.get("profession")
                    if isinstance(prof_val, str) and prof_val.strip():
                        parsed_intent["profession"] = prof_val.strip()
                    skills_val = extracted.get("skills") or []
                    if isinstance(skills_val, list):
                        parsed_intent["skills"] = [s.strip() for s in skills_val if isinstance(s, str) and s.strip()]
                    loc_val = extracted.get("location")
                    if isinstance(loc_val, str) and loc_val.strip() and loc_val.strip().lower() != "near me":
                        parsed_intent["location"] = loc_val.strip()
        except Exception as e:
            logger.warning(f"AI intent parsing failed, using fallback: {e}")

    # === Step 2: Build a broad MongoDB query using extracted filters (OR across signals) ===
    or_clauses = []
    profession = parsed_intent["profession"]
    if isinstance(profession, str) and profession:
        or_clauses.append({"profession": {"$regex": profession, "$options": "i"}})
        or_clauses.append({"skills": {"$regex": profession, "$options": "i"}})
        or_clauses.append({"bio": {"$regex": profession, "$options": "i"}})
    for skill in parsed_intent["skills"]:
        if isinstance(skill, str) and len(skill) > 1:
            or_clauses.append({"skills": {"$regex": skill, "$options": "i"}})
            or_clauses.append({"bio": {"$regex": skill, "$options": "i"}})
            or_clauses.append({"profession": {"$regex": skill, "$options": "i"}})

    if isinstance(raw_query, str) and len(raw_query) > 1:
        or_clauses.append({"profession": {"$regex": raw_query, "$options": "i"}})
        or_clauses.append({"bio": {"$regex": raw_query, "$options": "i"}})
        or_clauses.append({"skills": {"$regex": raw_query, "$options": "i"}})

    db_query = {"availability": True}
    if or_clauses:
        db_query["$or"] = or_clauses

    professionals = await db.professional_profiles.find(db_query, {"_id": 0}).to_list(80)

    # Enrich with user data; also do post-filter for name and location since those live on the user doc
    name_q = (parsed_intent["name"] or "").lower().strip()
    loc_q = (parsed_intent["location"] or "").lower().strip()
    enriched = []
    for prof in professionals:
        u = await db.users.find_one({"id": prof["user_id"]}, {"_id": 0, "password_hash": 0})
        if not u:
            continue
        prof["user"] = _strip_phone(u)
        enriched.append(prof)

    if name_q:
        enriched = [
            p for p in enriched
            if name_q in (p["user"].get("name") or "").lower()
            or name_q in (p["user"].get("username") or "").lower()
            or name_q in (p["user"].get("display_id") or "").lower()
        ]

    if loc_q:
        with_loc = [p for p in enriched if loc_q in (p["user"].get("location") or "").lower()]
        if with_loc:
            enriched = with_loc

    # Permissive name fallback (search by name across all available pros if name was extracted but no matches)
    if not enriched and name_q:
        all_pros = await db.professional_profiles.find({"availability": True}, {"_id": 0}).to_list(200)
        for prof in all_pros:
            u = await db.users.find_one({"id": prof["user_id"]}, {"_id": 0, "password_hash": 0})
            if not u:
                continue
            user_name = (u.get("name") or "").lower()
            user_uname = (u.get("username") or "").lower()
            if name_q in user_name or name_q in user_uname:
                prof["user"] = _strip_phone(u)
                enriched.append(prof)

    if not enriched:
        return {
            "matches": [],
            "ai_powered": bool(EMERGENT_LLM_KEY),
            "intent": parsed_intent,
            "message": "No professionals matched your search. Try a different keyword, profession, or location.",
        }

    # === Step 3: Hybrid deterministic scoring (BM25-style lexical + quality signals) ===
    # Best-fit for this marketplace: text relevance + rating quality (Bayesian) +
    # experience + activity + location + availability. AI then refines top candidates.

    raw_tokens = [t.lower() for t in re.findall(r"\w+", raw_query) if len(t) > 1]
    intent_tokens = list({
        *raw_tokens,
        *[t for s in parsed_intent["skills"] for t in re.findall(r"\w+", s.lower()) if len(t) > 1],
        *([parsed_intent["profession"].lower()] if parsed_intent["profession"] else []),
    })
    name_q = (parsed_intent["name"] or "").lower().strip()
    loc_q = (parsed_intent["location"] or "").lower().strip()

    # Global rating mean for Bayesian smoothing
    rating_stats = await db.professional_profiles.aggregate([
        {"$match": {"total_reviews": {"$gt": 0}}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}}},
    ]).to_list(1)
    global_avg_rating = float(rating_stats[0]["avg"]) if rating_stats else 3.5

    def _score(prof):
        u = prof["user"]
        profession_t = (prof.get("profession") or "").lower()
        skills_t = " ".join(prof.get("skills") or []).lower()
        bio_t = (prof.get("bio") or "").lower()
        name_t = (u.get("name") or "").lower()
        user_loc_t = (u.get("location") or "").lower()

        # Text relevance (max 40) — weighted: profession 3, name 3, skills 2, bio 1
        text_hits = 0
        max_per_token = 9  # 3+3+2+1
        for tok in intent_tokens:
            if not tok:
                continue
            if tok in profession_t:
                text_hits += 3
            if tok in name_t:
                text_hits += 3
            if tok in skills_t:
                text_hits += 2
            if tok in bio_t:
                text_hits += 1
        denom = max_per_token * max(len(intent_tokens), 1)
        text_score = min(40.0, (text_hits / denom) * 40.0) if denom else 0.0
        # Explicit name match short-circuit (very high signal)
        if name_q and name_q in name_t:
            text_score = max(text_score, 38.0)

        # Bayesian rating (max 20) — smooths new pros toward global mean
        rating = float(prof.get("rating") or 0)
        n_reviews = int(prof.get("total_reviews") or 0)
        C = 5
        bayes = (rating * n_reviews + global_avg_rating * C) / max(n_reviews + C, 1)
        rating_score = (bayes / 5.0) * 20.0

        # Experience (max 10)
        exp_years = float(prof.get("experience_years") or 0)
        experience_score = min(exp_years / 10.0, 1.0) * 10.0

        # Activity (max 10)
        total_jobs = int(prof.get("total_jobs") or 0)
        activity_score = min(total_jobs / 30.0, 1.0) * 10.0

        # Location (max 15)
        if loc_q:
            if loc_q == user_loc_t and user_loc_t:
                location_score = 15.0
            elif user_loc_t and (loc_q in user_loc_t or user_loc_t in loc_q):
                location_score = 8.0
            else:
                location_score = 0.0
        else:
            location_score = 6.0  # neutral when no location preference

        # Availability (max 5)
        availability_score = 5.0 if prof.get("availability") else 0.0

        breakdown = {
            "text": round(text_score, 1),
            "rating": round(rating_score, 1),
            "experience": round(experience_score, 1),
            "activity": round(activity_score, 1),
            "location": round(location_score, 1),
            "availability": round(availability_score, 1),
        }
        total = sum(breakdown.values())
        return round(total, 1), breakdown

    for p in enriched:
        det_score, breakdown = _score(p)
        p["_deterministic_score"] = det_score
        p["_score_breakdown"] = breakdown

    enriched.sort(key=lambda p: p["_deterministic_score"], reverse=True)
    top_candidates = enriched[:20]

    # === Step 4: AI refinement on top candidates — gives a tailored relevance score + reason ===
    ai_used = False
    ai_score_map = {}  # user_id -> {"ai_score": 0-100, "reason": str}
    if raw_query and EMERGENT_LLM_KEY and len(top_candidates) >= 1:
        try:
            ranker = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"match-rank-{uuid.uuid4()}",
                system_message=(
                    "You evaluate how well each service professional matches a user's natural-language "
                    "search for a Kenyan services marketplace. For each candidate, output a JSON object "
                    "with: id (string, the user_id), ai_score (integer 0-100 — how relevant for THIS "
                    "user's specific need), reason (short, friendly, max 18 words, explains why this pro fits)."
                    " Return ONLY a JSON array."
                ),
            ).with_model("gemini", "gemini-3-flash-preview")

            prof_summary = "\n".join([
                f"- ID:{p['user_id']} | Name:{p['user'].get('name','')} | "
                f"Profession:{p.get('profession','')} | Skills:{', '.join(p.get('skills') or [])[:120]} | "
                f"Bio:{(p.get('bio') or '')[:140]} | Rating:{p.get('rating',0)}/5 ({p.get('total_reviews',0)} reviews) | "
                f"Rate:KSh {p.get('hourly_rate','N/A')}/hr | Exp:{p.get('experience_years',0)}y | "
                f"Location:{p['user'].get('location','')}"
                for p in top_candidates
            ])

            rank_resp = await ranker.send_message(UserMessage(text=(
                f"User search: \"{raw_query}\"\n"
                f"Extracted intent: {parsed_intent}\n\n"
                f"Candidates:\n{prof_summary}\n\n"
                'Return a JSON array: [{"id":"<user_id>","ai_score":0-100,"reason":"<short reason>"}]'
            )))

            import json as _json
            j_start = rank_resp.find("[")
            j_end = rank_resp.rfind("]") + 1
            if j_start >= 0 and j_end > j_start:
                rankings = _json.loads(rank_resp[j_start:j_end])
                for r in rankings:
                    if not isinstance(r, dict):
                        continue
                    rid = r.get("id")
                    if not rid:
                        continue
                    ai_score_map[rid] = {
                        "ai_score": max(0, min(100, int(r.get("ai_score", r.get("match_score", 0)) or 0))),
                        "reason": (r.get("reason") or "")[:200],
                    }
                ai_used = bool(ai_score_map)
        except Exception as e:
            logger.warning(f"AI hybrid refinement failed, using deterministic only: {e}")

    # === Step 5: Blend deterministic (60%) + AI (40%) into final match_score ===
    def _fallback_reason(p):
        bits = []
        prof_name = p.get("profession") or "Professional"
        bits.append(prof_name)
        if p.get("rating"):
            bits.append(f"{p['rating']:.1f}★ ({p.get('total_reviews', 0)} reviews)")
        if p.get("experience_years"):
            bits.append(f"{p['experience_years']}y experience")
        loc = (p["user"].get("location") or "").strip()
        if loc:
            bits.append(f"in {loc}")
        return " · ".join(bits)

    for p in top_candidates:
        det_norm = p["_deterministic_score"]  # already 0-100
        ai_entry = ai_score_map.get(p["user_id"])
        if ai_entry:
            final = round(0.6 * det_norm + 0.4 * ai_entry["ai_score"])
            reason = ai_entry["reason"] or _fallback_reason(p)
        else:
            final = round(det_norm)
            reason = _fallback_reason(p)
        p["match_score"] = max(0, min(100, final))
        p["match_reason"] = reason
        p["score_breakdown"] = p.pop("_score_breakdown")
        p.pop("_deterministic_score", None)

    top_candidates.sort(key=lambda p: (p["match_score"], p.get("rating") or 0), reverse=True)

    return {
        "matches": top_candidates[:15],
        "ai_powered": ai_used,
        "hybrid": True,
        "intent": parsed_intent,
        "scoring": {
            "algorithm": "hybrid_bm25_bayesian_ai",
            "weights": {
                "deterministic": 0.6,
                "ai_refinement": 0.4,
                "components": {
                    "text_relevance": 40,
                    "rating_bayesian": 20,
                    "location": 15,
                    "experience": 10,
                    "activity": 10,
                    "availability": 5,
                },
            },
            "global_avg_rating": round(global_avg_rating, 2),
        },
    }

# ============= BOOKING ENDPOINTS =============
@api_router.post("/bookings")
async def create_booking(booking_data: BookingCreate, user = Depends(get_current_user)):
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can create bookings")
    
    # Verify professional exists and is available
    professional = await db.professional_profiles.find_one({"user_id": booking_data.professional_id})
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    pro_user = await db.users.find_one({"id": booking_data.professional_id}, {"display_id": 1})
    
    booking_id = str(uuid.uuid4())
    booking_display_id = await generate_booking_id()
    
    booking_doc = {
        "id": booking_id,
        "display_id": booking_display_id,
        "client_id": user["id"],
        "client_display_id": user.get("display_id"),
        "professional_display_id": pro_user.get("display_id") if pro_user else None,
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

# ============= PAYMENT ENDPOINTS (M-PESA) =============
PLATFORM_FEE_PERCENTAGE = 20             # Commission charged on completed job to professional payout
BOOKING_FEE_PERCENT = 1.5                # Client-side booking platform fee (% of service price)
BOOKING_FIXED_FEE = 20                   # Client-side booking fixed fee (KSh)
WITHDRAWAL_FEE_PERCENT = 3               # Client-side withdrawal fee (% of withdrawal amount)
WITHDRAWAL_FIXED_FEE = 20                # Client-side withdrawal fixed fee (KSh)
PROFESSIONAL_WITHDRAWAL_FIXED_FEE = 15   # Professional flat withdrawal fee (KSh, no %)
CLIENT_REGISTRATION_FEE = 20             # M-Pesa account verification fee for clients
PROFESSIONAL_REGISTRATION_FEE = 2000     # Registration fee for professionals


def _calc_booking_total(service_amount: float) -> dict:
    """Booking total = service + 1.5% of service + KSh 20."""
    service_amount = round(float(service_amount or 0), 2)
    percent_fee = round(service_amount * (BOOKING_FEE_PERCENT / 100), 2)
    fixed_fee = float(BOOKING_FIXED_FEE)
    total = round(service_amount + percent_fee + fixed_fee, 2)
    return {
        "service_amount": service_amount,
        "platform_fee_percent": BOOKING_FEE_PERCENT,
        "platform_fee_amount": percent_fee,
        "fixed_fee": fixed_fee,
        "total": total,
    }


def _calc_withdrawal_total(withdrawal_amount: float, role: str = "client") -> dict:
    """Withdrawal breakdown.

    - **Client**: amount + 3% + KSh 20 fixed
    - **Professional**: amount + KSh 15 fixed (no percentage)

    Returns the gross (total wallet deduction) and the fee components.
    """
    amount = round(float(withdrawal_amount or 0), 2)
    if role == "professional":
        percent_fee = 0.0
        fixed_fee = float(PROFESSIONAL_WITHDRAWAL_FIXED_FEE)
        fee_percent_applied = 0.0
    else:
        percent_fee = round(amount * (WITHDRAWAL_FEE_PERCENT / 100), 2)
        fixed_fee = float(WITHDRAWAL_FIXED_FEE)
        fee_percent_applied = float(WITHDRAWAL_FEE_PERCENT)
    fee_total = round(percent_fee + fixed_fee, 2)
    gross = round(amount + fee_total, 2)
    return {
        "amount": amount,
        "withdrawal_fee_percent": fee_percent_applied,
        "withdrawal_fee_amount": percent_fee,
        "fixed_fee": fixed_fee,
        "fee_total": fee_total,
        "gross": gross,
        "role_applied": role,
    }


@api_router.get("/payments/quote")
async def quote_booking_payment(booking_id: str, user = Depends(get_current_user)):
    """Return the full charge breakdown for a booking + whether the client's
    wallet covers it or needs an M-Pesa top-up (and how much).
    """
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can quote a payment")

    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["client_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    breakdown = _calc_booking_total(booking["agreed_price"])
    wallet_balance = round(float(user.get("wallet_balance") or 0), 2)
    total = breakdown["total"]
    use_wallet = min(wallet_balance, total)
    topup_required = round(max(total - use_wallet, 0), 2)
    return {
        **breakdown,
        "wallet_balance": wallet_balance,
        "wallet_used": round(use_wallet, 2),
        "topup_required": topup_required,
        "fully_covered_by_wallet": topup_required == 0,
    }


@api_router.post("/payments/initiate")
async def initiate_payment(payment_data: PaymentCreate, user = Depends(get_current_user)):
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can initiate payments")

    booking = await db.bookings.find_one({"id": payment_data.booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["client_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Block double-pay only if it's already funded; allow retry for failed/awaiting_topup
    existing = await db.payments.find_one({
        "booking_id": payment_data.booking_id,
        "status": PaymentStatus.ESCROW.value,
    })
    if existing:
        raise HTTPException(status_code=400, detail="This booking is already paid")

    # Clean up prior failed/awaiting_topup attempts so the retry starts fresh.
    # For 'awaiting_topup' rows, refund any wallet portion that was reserved.
    stale = await db.payments.find({
        "booking_id": payment_data.booking_id,
        "status": {"$in": ["awaiting_topup", "failed"]},
    }).to_list(20)
    for s in stale:
        if s.get("status") == "awaiting_topup" and float(s.get("wallet_used") or 0) > 0:
            await db.users.update_one(
                {"id": s["client_id"]},
                {"$inc": {"wallet_balance": float(s["wallet_used"])}},
            )
        await db.payments.update_one(
            {"id": s["id"]},
            {"$set": {
                "status": "cancelled_retry",
                "cancelled_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
    # Re-fetch user to get the refreshed wallet balance after any refund above
    if stale:
        user = await db.users.find_one({"id": user["id"]}, {"_id": 0}) or user

    # Fee breakdown
    service_amount = float(booking["agreed_price"])
    breakdown = _calc_booking_total(service_amount)
    total = breakdown["total"]

    # Existing platform commission on payout (unchanged behaviour for the professional side)
    professional_amount = round(service_amount - service_amount * (PLATFORM_FEE_PERCENTAGE / 100), 2)
    pro_platform_fee = round(service_amount - professional_amount, 2)

    wallet_balance = round(float(user.get("wallet_balance") or 0), 2)
    wallet_used = round(min(wallet_balance, total), 2)
    topup_required = round(max(total - wallet_used, 0), 2)

    payment_id = str(uuid.uuid4())
    payment_display_id = await generate_payment_id()
    now_iso = datetime.now(timezone.utc).isoformat()

    payment_doc = {
        "id": payment_id,
        "display_id": payment_display_id,
        "booking_id": payment_data.booking_id,
        "booking_display_id": booking.get("display_id"),
        "client_id": user["id"],
        "client_display_id": user.get("display_id"),
        "professional_id": booking["professional_id"],
        "professional_display_id": booking.get("professional_display_id"),
        # Money flow
        "amount": service_amount,                              # service price
        "booking_fee_percent": BOOKING_FEE_PERCENT,
        "booking_fee_amount": breakdown["platform_fee_amount"],
        "booking_fixed_fee": breakdown["fixed_fee"],
        "client_charge_total": total,                          # what the client actually pays
        "wallet_used": wallet_used,
        "topup_required": topup_required,
        # Payout side (unchanged)
        "platform_fee": pro_platform_fee,                      # 20% professional commission
        "professional_amount": professional_amount,
        "status": PaymentStatus.ESCROW.value if topup_required == 0 else "awaiting_topup",
        "created_at": now_iso,
        "released_at": None,
    }

    # CASE A: fully covered by wallet → deduct immediately and move to escrow
    if topup_required == 0:
        await db.users.update_one(
            {"id": user["id"]},
            {"$inc": {"wallet_balance": -total}},
        )
        await db.payments.insert_one(payment_doc)
        await create_ledger_entry(
            entry_type=LedgerEntryType.ESCROW_IN,
            user_id=user["id"],
            amount=total,
            description=f"Booking payment (wallet) {booking.get('display_id', payment_data.booking_id)} - {booking.get('service_description', 'Service')}",
            reference_id=payment_display_id,
            reference_type="payment",
            related_user_id=booking["professional_id"],
            metadata={
                "booking_id": payment_data.booking_id,
                "booking_display_id": booking.get("display_id"),
                "professional_id": booking["professional_id"],
                "service_amount": service_amount,
                "booking_fee_amount": breakdown["platform_fee_amount"],
                "booking_fixed_fee": breakdown["fixed_fee"],
                "wallet_used": wallet_used,
                "topup_required": 0,
            },
        )
        await db.bookings.update_one(
            {"id": payment_data.booking_id},
            {"$set": {"status": BookingStatus.CONFIRMED.value}},
        )
        return {
            "message": "Payment held in escrow",
            "payment": {k: v for k, v in payment_doc.items() if k != "_id"},
            "topup_required": 0,
        }

    # CASE B: not fully covered → trigger STK Push for the shortfall
    # Validate registered phone first
    registered_phone = (user.get("phone") or "").strip()
    if not registered_phone:
        raise HTTPException(
            status_code=400,
            detail="No registered phone number on file. Please update your profile before paying.",
        )
    phone = mpesa_service.normalize_phone(registered_phone)
    if not phone.startswith("254") or len(phone) != 12:
        raise HTTPException(
            status_code=400,
            detail="Your registered phone number is invalid. Please update it in your profile (format 2547XXXXXXXX or 07XXXXXXXX).",
        )

    # Reserve the wallet portion now (debit immediately so user can't double-spend)
    if wallet_used > 0:
        await db.users.update_one(
            {"id": user["id"]},
            {"$inc": {"wallet_balance": -wallet_used}},
        )

    try:
        stk_result = await mpesa_service.stk_push(
            phone_number=phone,
            amount=int(round(topup_required)),
            account_reference=payment_display_id,
            transaction_desc=f"Kazi Links booking {booking.get('display_id', '')[:20]}",
        )
    except Exception as e:
        # Rollback wallet reservation
        if wallet_used > 0:
            await db.users.update_one({"id": user["id"]}, {"$inc": {"wallet_balance": wallet_used}})
        logger.exception("STK push failed")
        raise HTTPException(status_code=502, detail=f"M-Pesa is currently unavailable. Please try again. ({e})")

    payment_doc["checkout_request_id"] = stk_result.get("CheckoutRequestID")
    payment_doc["merchant_request_id"] = stk_result.get("MerchantRequestID")
    payment_doc["topup_phone"] = phone
    await db.payments.insert_one(payment_doc)

    # Pending ledger entry — confirmed by mpesa callback
    await create_ledger_entry(
        entry_type=LedgerEntryType.ESCROW_IN,
        user_id=user["id"],
        amount=wallet_used,
        description=f"Booking payment (wallet portion) {booking.get('display_id', payment_data.booking_id)}",
        reference_id=payment_display_id,
        reference_type="payment_wallet_portion",
        related_user_id=booking["professional_id"],
        metadata={
            "booking_id": payment_data.booking_id,
            "wallet_used": wallet_used,
            "topup_required": topup_required,
            "phone": phone,
            "checkout_request_id": payment_doc["checkout_request_id"],
        },
    )

    return {
        "message": "Wallet portion held. Enter your M-Pesa PIN on the prompt to complete payment.",
        "payment": {k: v for k, v in payment_doc.items() if k != "_id"},
        "topup_required": topup_required,
        "checkout_request_id": payment_doc["checkout_request_id"],
        "phone": phone,
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
    released_at = datetime.now(timezone.utc).isoformat()
    await db.payments.update_one(
        {"id": payment_id},
        {"$set": {"status": PaymentStatus.RELEASED.value, "released_at": released_at}}
    )
    
    # Create ledger entry for escrow release
    await create_ledger_entry(
        entry_type=LedgerEntryType.ESCROW_OUT,
        user_id=payment["client_id"],
        amount=payment["amount"],
        description=f"Escrow released for payment {payment.get('display_id', payment_id)}",
        reference_id=payment.get("display_id", payment_id),
        reference_type="payment_release",
        related_user_id=payment["professional_id"]
    )
    
    # Create ledger entry for platform fee
    await create_ledger_entry(
        entry_type=LedgerEntryType.PLATFORM_FEE,
        user_id="platform",
        amount=payment["platform_fee"],
        description=f"Platform commission (20%) from payment {payment.get('display_id', payment_id)}",
        reference_id=payment.get("display_id", payment_id),
        reference_type="platform_fee",
        related_user_id=payment["professional_id"],
        metadata={
            "client_id": payment["client_id"],
            "professional_id": payment["professional_id"],
            "total_amount": payment["amount"]
        }
    )
    
    # Create ledger entry for professional payout
    await create_ledger_entry(
        entry_type=LedgerEntryType.PROFESSIONAL_PAYOUT,
        user_id=payment["professional_id"],
        amount=payment["professional_amount"],
        description=f"Payout from booking - {payment.get('display_id', payment_id)}",
        reference_id=payment.get("display_id", payment_id),
        reference_type="professional_payout",
        related_user_id=payment["client_id"],
        metadata={
            "total_amount": payment["amount"],
            "platform_fee": payment["platform_fee"]
        }
    )
    
    # Update professional wallet and earnings
    await db.users.update_one(
        {"id": payment["professional_id"]},
        {"$inc": {"wallet_balance": payment["professional_amount"]}}
    )
    
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
    
    # User stats
    total_users = await db.users.count_documents({})
    total_clients = await db.users.count_documents({"role": "client"})
    total_professionals = await db.users.count_documents({"role": "professional"})
    active_professionals = await db.professional_profiles.count_documents({"availability": True})
    
    # Job stats
    total_jobs = await db.jobs.count_documents({})
    open_jobs = await db.jobs.count_documents({"status": "open"})
    matched_jobs = await db.jobs.count_documents({"status": "matched"})
    completed_jobs = await db.jobs.count_documents({"status": "completed"})
    
    # Booking stats
    total_bookings = await db.bookings.count_documents({})
    pending_bookings = await db.bookings.count_documents({"status": "pending"})
    confirmed_bookings = await db.bookings.count_documents({"status": "confirmed"})
    in_progress_bookings = await db.bookings.count_documents({"status": "in_progress"})
    completed_bookings = await db.bookings.count_documents({"status": "completed"})
    cancelled_bookings = await db.bookings.count_documents({"status": "cancelled"})
    
    # Bid stats
    total_bids = await db.bids.count_documents({})
    pending_bids = await db.bids.count_documents({"status": "pending"})
    accepted_bids = await db.bids.count_documents({"status": "accepted"})
    rejected_bids = await db.bids.count_documents({"status": "rejected"})
    
    # Calculate total revenue and transactions
    all_payments = await db.payments.find({}, {"_id": 0}).to_list(10000)
    released_payments = [p for p in all_payments if p["status"] == PaymentStatus.RELEASED.value]
    escrow_payments = [p for p in all_payments if p["status"] == PaymentStatus.ESCROW.value]
    
    total_revenue = sum(p["platform_fee"] for p in released_payments)
    total_transactions = sum(p["amount"] for p in released_payments)
    escrow_balance = sum(p["amount"] for p in escrow_payments)
    
    # Wallet stats
    wallet_deposits = await db.wallet_transactions.find({"type": "deposit", "status": "completed"}).to_list(10000)
    wallet_withdrawals = await db.wallet_transactions.find({"type": "withdrawal", "status": "completed"}).to_list(10000)
    total_deposits = sum(t["amount"] for t in wallet_deposits)
    total_withdrawals = sum(t["amount"] for t in wallet_withdrawals)
    
    # Review stats
    total_reviews = await db.reviews.count_documents({})
    all_reviews = await db.reviews.find({}, {"rating": 1, "_id": 0}).to_list(10000)
    avg_platform_rating = sum(r["rating"] for r in all_reviews) / len(all_reviews) if all_reviews else 0
    
    return {
        "users": {
            "total": total_users,
            "clients": total_clients,
            "professionals": total_professionals,
            "active_professionals": active_professionals
        },
        "jobs": {
            "total": total_jobs,
            "open": open_jobs,
            "matched": matched_jobs,
            "completed": completed_jobs
        },
        "bookings": {
            "total": total_bookings,
            "pending": pending_bookings,
            "confirmed": confirmed_bookings,
            "in_progress": in_progress_bookings,
            "completed": completed_bookings,
            "cancelled": cancelled_bookings
        },
        "bids": {
            "total": total_bids,
            "pending": pending_bids,
            "accepted": accepted_bids,
            "rejected": rejected_bids,
            "acceptance_rate": round((accepted_bids / total_bids * 100) if total_bids > 0 else 0, 1)
        },
        "financials": {
            "total_transactions": total_transactions,
            "platform_revenue": total_revenue,
            "escrow_balance": escrow_balance,
            "platform_fee_percentage": PLATFORM_FEE_PERCENTAGE,
            "total_wallet_deposits": total_deposits,
            "total_wallet_withdrawals": total_withdrawals
        },
        "reviews": {
            "total": total_reviews,
            "average_rating": round(avg_platform_rating, 2)
        }
    }

@api_router.get("/admin/dashboard")
async def get_admin_dashboard(user = Depends(get_current_user)):
    """Comprehensive admin dashboard data"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    now = datetime.now(timezone.utc)
    
    # Get stats from last 30 days
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    
    # Recent activity
    recent_users = await db.users.find(
        {"created_at": {"$gte": thirty_days_ago}}, 
        {"_id": 0, "password_hash": 0}
    ).sort("created_at", -1).to_list(10)
    
    recent_jobs = await db.jobs.find(
        {"created_at": {"$gte": thirty_days_ago}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    
    recent_bookings = await db.bookings.find(
        {"created_at": {"$gte": thirty_days_ago}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    
    # Enrich recent bookings
    for booking in recent_bookings:
        client = await db.users.find_one({"id": booking["client_id"]}, {"name": 1, "_id": 0})
        pro = await db.users.find_one({"id": booking["professional_id"]}, {"name": 1, "_id": 0})
        booking["client_name"] = client["name"] if client else "Unknown"
        booking["professional_name"] = pro["name"] if pro else "Unknown"
    
    recent_payments = await db.payments.find(
        {"created_at": {"$gte": thirty_days_ago}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    
    # Daily revenue for last 7 days
    daily_revenue = []
    daily_labels = []
    daily_bookings = []
    daily_users = []
    
    for i in range(7):
        day = now - timedelta(days=6-i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Revenue
        day_payments = await db.payments.find({
            "status": PaymentStatus.RELEASED.value,
            "released_at": {"$gte": day_start.isoformat(), "$lte": day_end.isoformat()}
        }).to_list(1000)
        daily_revenue.append(sum(p["platform_fee"] for p in day_payments))
        
        # Bookings
        day_bookings = await db.bookings.count_documents({
            "created_at": {"$gte": day_start.isoformat(), "$lte": day_end.isoformat()}
        })
        daily_bookings.append(day_bookings)
        
        # New users
        day_users = await db.users.count_documents({
            "created_at": {"$gte": day_start.isoformat(), "$lte": day_end.isoformat()}
        })
        daily_users.append(day_users)
        
        daily_labels.append(day.strftime("%a"))
    
    # Jobs by category
    jobs_pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    jobs_by_category = await db.jobs.aggregate(jobs_pipeline).to_list(10)
    
    # Top professionals by rating
    top_professionals = await db.professional_profiles.find(
        {"total_reviews": {"$gt": 0}},
        {"_id": 0}
    ).sort("rating", -1).to_list(10)
    
    for prof in top_professionals:
        user_data = await db.users.find_one({"id": prof["user_id"]}, {"name": 1, "email": 1, "_id": 0})
        prof["name"] = user_data["name"] if user_data else "Unknown"
        prof["email"] = user_data["email"] if user_data else ""
    
    # Top earners
    top_earners = await db.professional_profiles.find(
        {"total_earnings": {"$gt": 0}},
        {"_id": 0}
    ).sort("total_earnings", -1).to_list(10)
    
    for prof in top_earners:
        user_data = await db.users.find_one({"id": prof["user_id"]}, {"name": 1, "_id": 0})
        prof["name"] = user_data["name"] if user_data else "Unknown"
    
    return {
        "recent_activity": {
            "users": recent_users,
            "jobs": recent_jobs,
            "bookings": recent_bookings,
            "payments": recent_payments
        },
        "charts": {
            "labels": daily_labels,
            "revenue": daily_revenue,
            "bookings": daily_bookings,
            "new_users": daily_users
        },
        "jobs_by_category": [{"category": j["_id"], "count": j["count"]} for j in jobs_by_category],
        "top_professionals": top_professionals[:5],
        "top_earners": top_earners[:5]
    }

@api_router.get("/admin/users")
async def get_all_users(
    role: Optional[str] = None, 
    search: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    user = Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if role:
        query["role"] = role
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.users.count_documents(query)
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with profile data for professionals
    for u in users:
        if u["role"] == "professional":
            profile = await db.professional_profiles.find_one({"user_id": u["id"]}, {"_id": 0})
            u["profile"] = profile
    
    return {"users": users, "total": total, "limit": limit, "skip": skip}

@api_router.put("/admin/users/{user_id}/status")
async def update_user_status(user_id: str, is_active: bool, user = Depends(get_current_user)):
    """Activate or deactivate a user"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.users.update_one({"id": user_id}, {"$set": {"is_active": is_active}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}

@api_router.get("/admin/transactions")
async def get_all_transactions(user = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    payments = await db.payments.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich with user data
    for payment in payments:
        client = await db.users.find_one({"id": payment["client_id"]}, {"name": 1, "display_id": 1, "_id": 0})
        prof = await db.users.find_one({"id": payment["professional_id"]}, {"name": 1, "display_id": 1, "_id": 0})
        payment["client_name"] = client["name"] if client else "Unknown"
        payment["client_display_id"] = client.get("display_id") if client else None
        payment["professional_name"] = prof["name"] if prof else "Unknown"
        payment["professional_display_id"] = prof.get("display_id") if prof else None
    
    return payments


@api_router.get("/admin/registration-payments")
async def admin_registration_payments(
    role: Optional[str] = None,           # 'client' | 'professional'
    status: Optional[str] = None,         # 'pending' | 'completed' | 'failed'
    q: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 200,
    skip: int = 0,
    user = Depends(get_current_user),
):
    """Admin: list every registration paywall payment (client verification + pro registration)
    with summary totals.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    query: dict = {}
    if role in ("client", "professional"):
        query["role"] = role
    if status in ("pending", "completed", "failed"):
        query["status"] = status
    if date_from or date_to:
        rng: dict = {}
        if date_from:
            rng["$gte"] = date_from
        if date_to:
            rng["$lte"] = date_to if "T" in date_to else f"{date_to}T23:59:59.999Z"
        query["created_at"] = rng
    if q:
        q_clean = q.strip()
        if q_clean:
            query["$or"] = [
                {"name": {"$regex": q_clean, "$options": "i"}},
                {"email": {"$regex": q_clean, "$options": "i"}},
                {"phone": {"$regex": q_clean.replace("+", "").replace(" ", ""), "$options": "i"}},
                {"reference": {"$regex": q_clean, "$options": "i"}},
                {"mpesa_receipt": {"$regex": q_clean, "$options": "i"}},
                {"checkout_request_id": {"$regex": q_clean, "$options": "i"}},
                {"user_display_id": {"$regex": q_clean, "$options": "i"}},
            ]

    total = await db.registration_payments.count_documents(query)
    cursor = (
        db.registration_payments.find(query, {"_id": 0, "password_hash": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    rows = await cursor.to_list(limit)

    # Aggregations (computed across the FULL filtered set)
    pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": {"role": "$role", "status": "$status"},
                "count": {"$sum": 1},
                "total": {"$sum": "$amount"},
            }
        },
    ]
    agg = await db.registration_payments.aggregate(pipeline).to_list(50)
    summary = {
        "client_completed": {"count": 0, "total": 0.0},
        "client_pending": {"count": 0, "total": 0.0},
        "client_failed": {"count": 0, "total": 0.0},
        "professional_completed": {"count": 0, "total": 0.0},
        "professional_pending": {"count": 0, "total": 0.0},
        "professional_failed": {"count": 0, "total": 0.0},
    }
    for row in agg:
        r = (row["_id"] or {}).get("role")
        s = (row["_id"] or {}).get("status")
        key = f"{r}_{s}" if r and s else None
        if key in summary:
            summary[key] = {"count": row["count"], "total": round(row["total"], 2)}
    summary["total_revenue"] = round(
        summary["client_completed"]["total"] + summary["professional_completed"]["total"], 2
    )
    summary["total_transactions"] = total

    return {
        "registrations": rows,
        "summary": summary,
        "pagination": {"total": total, "limit": limit, "skip": skip},
        "filters": {"role": role, "status": status, "q": q, "date_from": date_from, "date_to": date_to},
        "fees": {
            "client_verification": CLIENT_REGISTRATION_FEE,
            "professional_registration": PROFESSIONAL_REGISTRATION_FEE,
        },
    }


@api_router.get("/admin/mpesa-transactions")
async def admin_mpesa_transactions(
    type: Optional[str] = None,           # 'deposit' | 'withdrawal'
    status: Optional[str] = None,         # 'completed' | 'pending' | 'failed'
    q: Optional[str] = None,              # search by user name/email/phone/mpesa ref/transaction_id
    date_from: Optional[str] = None,      # ISO date inclusive
    date_to: Optional[str] = None,        # ISO date inclusive
    limit: int = 200,
    skip: int = 0,
    user = Depends(get_current_user),
):
    """Admin: full M-Pesa deposit + withdrawal ledger across the platform with
    user enrichment, summary totals, and filtering. Powers the
    `Platform Finances` admin page.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    query: dict = {}
    if type in ("deposit", "withdrawal"):
        query["type"] = type
    if status in ("completed", "pending", "failed"):
        query["status"] = status
    if date_from or date_to:
        rng: dict = {}
        if date_from:
            rng["$gte"] = date_from
        if date_to:
            # Make 'to' inclusive of the whole day if only YYYY-MM-DD is sent
            rng["$lte"] = date_to if "T" in date_to else f"{date_to}T23:59:59.999Z"
        query["created_at"] = rng

    # If text-search, try to also match user_id by resolving emails/names first
    user_id_matches = []
    if q:
        q_clean = q.strip()
        if q_clean:
            users_found = await db.users.find(
                {
                    "$or": [
                        {"name": {"$regex": q_clean, "$options": "i"}},
                        {"email": {"$regex": q_clean, "$options": "i"}},
                        {"display_id": {"$regex": q_clean, "$options": "i"}},
                    ]
                },
                {"_id": 0, "id": 1},
            ).to_list(200)
            user_id_matches = [u["id"] for u in users_found]

            or_clauses = [
                {"reference": {"$regex": q_clean, "$options": "i"}},
                {"mpesa_receipt": {"$regex": q_clean, "$options": "i"}},
                {"transaction_id": {"$regex": q_clean, "$options": "i"}},
                {"phone_number": {"$regex": q_clean.replace("+", "").replace(" ", ""), "$options": "i"}},
                {"checkout_request_id": {"$regex": q_clean, "$options": "i"}},
            ]
            if user_id_matches:
                or_clauses.append({"user_id": {"$in": user_id_matches}})
            query["$or"] = or_clauses

    total = await db.wallet_transactions.count_documents(query)
    cursor = db.wallet_transactions.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    txns = await cursor.to_list(limit)

    # Enrich with user data
    user_cache: dict = {}
    for t in txns:
        uid = t.get("user_id")
        if uid and uid not in user_cache:
            u = await db.users.find_one(
                {"id": uid},
                {"_id": 0, "name": 1, "email": 1, "display_id": 1, "role": 1, "phone": 1},
            )
            user_cache[uid] = u
        u = user_cache.get(uid) or {}
        t["user_name"] = u.get("name", "Unknown")
        t["user_email"] = u.get("email")
        t["user_display_id"] = u.get("display_id")
        t["user_role"] = u.get("role")
        t["user_phone"] = u.get("phone")

    # Summary totals (computed over the FULL filtered set, not just the page)
    pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": {"type": "$type", "status": "$status"},
                "count": {"$sum": 1},
                "total": {"$sum": "$amount"},
            }
        },
    ]
    agg = await db.wallet_transactions.aggregate(pipeline).to_list(50)
    summary = {
        "deposits_completed": {"count": 0, "total": 0.0},
        "deposits_pending": {"count": 0, "total": 0.0},
        "deposits_failed": {"count": 0, "total": 0.0},
        "withdrawals_completed": {"count": 0, "total": 0.0},
        "withdrawals_pending": {"count": 0, "total": 0.0},
        "withdrawals_failed": {"count": 0, "total": 0.0},
    }
    for row in agg:
        t = (row["_id"] or {}).get("type")
        s = (row["_id"] or {}).get("status")
        key = f"{t}s_{s}" if t and s else None
        if key in summary:
            summary[key] = {"count": row["count"], "total": round(row["total"], 2)}
    net_flow = round(
        summary["deposits_completed"]["total"] - summary["withdrawals_completed"]["total"],
        2,
    )
    summary["net_flow"] = net_flow
    summary["total_transactions"] = total

    return {
        "transactions": txns,
        "summary": summary,
        "pagination": {"total": total, "limit": limit, "skip": skip},
        "filters": {"type": type, "status": status, "q": q, "date_from": date_from, "date_to": date_to},
    }


@api_router.get("/admin/ledger")
async def get_ledger(
    entry_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    user = Depends(get_current_user)
):
    """Get all ledger entries with optional filtering"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if entry_type:
        query["entry_type"] = entry_type
    if user_id:
        query["$or"] = [{"user_id": user_id}, {"related_user_id": user_id}]
    
    total = await db.ledger.count_documents(query)
    entries = await db.ledger.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with user names
    for entry in entries:
        if entry.get("user_id") and entry["user_id"] != "platform":
            u = await db.users.find_one({"id": entry["user_id"]}, {"name": 1, "display_id": 1, "_id": 0})
            entry["user_name"] = u["name"] if u else "Unknown"
            entry["user_display_id"] = u.get("display_id") if u else None
        elif entry.get("user_id") == "platform":
            entry["user_name"] = "Platform"
            entry["user_display_id"] = "PLATFORM"
        
        if entry.get("related_user_id"):
            ru = await db.users.find_one({"id": entry["related_user_id"]}, {"name": 1, "display_id": 1, "_id": 0})
            entry["related_user_name"] = ru["name"] if ru else "Unknown"
            entry["related_user_display_id"] = ru.get("display_id") if ru else None
    
    # Calculate summary stats
    all_entries = await db.ledger.find({}, {"_id": 0}).to_list(10000)
    
    summary = {
        "total_deposits": sum(e["amount"] for e in all_entries if e["entry_type"] == "deposit"),
        "total_withdrawals": sum(e["amount"] for e in all_entries if e["entry_type"] == "withdrawal"),
        "total_escrow_in": sum(e["amount"] for e in all_entries if e["entry_type"] == "escrow_in"),
        "total_escrow_out": sum(e["amount"] for e in all_entries if e["entry_type"] == "escrow_out"),
        "total_platform_fees": sum(e["amount"] for e in all_entries if e["entry_type"] == "platform_fee"),
        "total_professional_payouts": sum(e["amount"] for e in all_entries if e["entry_type"] == "professional_payout"),
        "entry_counts": {
            "deposit": len([e for e in all_entries if e["entry_type"] == "deposit"]),
            "withdrawal": len([e for e in all_entries if e["entry_type"] == "withdrawal"]),
            "escrow_in": len([e for e in all_entries if e["entry_type"] == "escrow_in"]),
            "escrow_out": len([e for e in all_entries if e["entry_type"] == "escrow_out"]),
            "platform_fee": len([e for e in all_entries if e["entry_type"] == "platform_fee"]),
            "professional_payout": len([e for e in all_entries if e["entry_type"] == "professional_payout"])
        }
    }
    
    return {
        "entries": entries,
        "total": total,
        "limit": limit,
        "skip": skip,
        "summary": summary
    }

@api_router.get("/admin/ledger/user/{user_id}")
async def get_user_ledger(user_id: str, user = Depends(get_current_user)):
    """Get all ledger entries for a specific user"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    entries = await db.ledger.find(
        {"$or": [{"user_id": user_id}, {"related_user_id": user_id}]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    # Get user info
    target_user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    
    # Calculate user's ledger summary
    credits = sum(e["amount"] for e in entries if e["user_id"] == user_id and e["entry_type"] in ["deposit", "professional_payout", "refund"])
    debits = sum(e["amount"] for e in entries if e["user_id"] == user_id and e["entry_type"] in ["withdrawal", "escrow_in"])
    
    return {
        "user": target_user,
        "entries": entries,
        "summary": {
            "total_credits": credits,
            "total_debits": debits,
            "net_balance": credits - debits,
            "current_wallet_balance": target_user.get("wallet_balance", 0) if target_user else 0
        }
    }

@api_router.get("/ledger/my")
async def get_my_ledger(user = Depends(get_current_user)):
    """Get current user's ledger entries"""
    entries = await db.ledger.find(
        {"$or": [{"user_id": user["id"]}, {"related_user_id": user["id"]}]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with related user names
    for entry in entries:
        if entry.get("related_user_id"):
            ru = await db.users.find_one({"id": entry["related_user_id"]}, {"name": 1, "display_id": 1, "_id": 0})
            entry["related_user_name"] = ru["name"] if ru else "Unknown"
            entry["related_user_display_id"] = ru.get("display_id") if ru else None
    
    # Calculate summary
    credits = sum(e["amount"] for e in entries if e["user_id"] == user["id"] and e["entry_type"] in ["deposit", "professional_payout", "refund"])
    debits = sum(e["amount"] for e in entries if e["user_id"] == user["id"] and e["entry_type"] in ["withdrawal", "escrow_in"])
    
    return {
        "entries": entries,
        "summary": {
            "total_credits": credits,
            "total_debits": debits,
            "current_balance": user.get("wallet_balance", 0)
        }
    }

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


# ============= CHAT / MESSAGING =============

class StartConversationRequest(BaseModel):
    other_user_id: str


class SendMessageRequest(BaseModel):
    content: Optional[str] = ""
    attachment_paths: Optional[List[str]] = []  # paths returned from /chat/attachments upload


async def _get_or_create_conversation(user_a: dict, user_b: dict) -> dict:
    """Return existing conversation between two users (client + professional), or create one."""
    # Determine roles
    if user_a["role"] == "client" and user_b["role"] == "professional":
        client_id, professional_id = user_a["id"], user_b["id"]
    elif user_a["role"] == "professional" and user_b["role"] == "client":
        client_id, professional_id = user_b["id"], user_a["id"]
    else:
        raise HTTPException(status_code=400, detail="Conversations are only between a client and a professional")

    convo = await db.conversations.find_one(
        {"client_id": client_id, "professional_id": professional_id},
        {"_id": 0},
    )
    if convo:
        return convo

    now = datetime.now(timezone.utc).isoformat()
    convo = {
        "id": str(uuid.uuid4()),
        "client_id": client_id,
        "professional_id": professional_id,
        "last_message_at": now,
        "last_message_preview": "",
        "last_sender_id": None,
        "unread_client": 0,
        "unread_professional": 0,
        "created_at": now,
        "updated_at": now,
    }
    await db.conversations.insert_one(convo)
    return convo


@api_router.post("/conversations")
async def start_conversation(req: StartConversationRequest, user = Depends(get_current_user)):
    if user["role"] not in ["client", "professional"]:
        raise HTTPException(status_code=403, detail="Only clients and professionals can start chats")
    if req.other_user_id == user["id"]:
        raise HTTPException(status_code=400, detail="You cannot start a chat with yourself")

    other = await db.users.find_one({"id": req.other_user_id}, {"_id": 0, "password_hash": 0})
    if not other:
        raise HTTPException(status_code=404, detail="User not found")

    convo = await _get_or_create_conversation(user, other)
    return convo


@api_router.get("/conversations")
async def list_conversations(user = Depends(get_current_user)):
    if user["role"] == "admin":
        raise HTTPException(status_code=400, detail="Admins use /admin/conversations")

    field = "client_id" if user["role"] == "client" else "professional_id"
    convos = await db.conversations.find({field: user["id"]}, {"_id": 0}).sort("last_message_at", -1).to_list(200)

    # Enrich with the other participant's public info
    enriched = []
    for c in convos:
        other_id = c["professional_id"] if user["role"] == "client" else c["client_id"]
        other = await db.users.find_one({"id": other_id}, {"_id": 0, "password_hash": 0, "phone": 0})
        c["other_user"] = other
        c["unread"] = c.get("unread_client" if user["role"] == "client" else "unread_professional", 0)
        enriched.append(c)
    return enriched


@api_router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str, user = Depends(get_current_user)):
    convo = await db.conversations.find_one({"id": conv_id}, {"_id": 0})
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if user["role"] != "admin" and user["id"] not in (convo["client_id"], convo["professional_id"]):
        raise HTTPException(status_code=403, detail="Not a participant in this conversation")

    other_id = convo["professional_id"] if user["id"] == convo["client_id"] else convo["client_id"]
    other = await db.users.find_one({"id": other_id}, {"_id": 0, "password_hash": 0, "phone": 0})
    convo["other_user"] = other
    return convo


@api_router.get("/conversations/{conv_id}/messages")
async def list_messages(conv_id: str, user = Depends(get_current_user), limit: int = 100):
    convo = await db.conversations.find_one({"id": conv_id}, {"_id": 0})
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if user["role"] != "admin" and user["id"] not in (convo["client_id"], convo["professional_id"]):
        raise HTTPException(status_code=403, detail="Not a participant in this conversation")

    msgs = await db.messages.find({"conversation_id": conv_id}, {"_id": 0}).sort("created_at", 1).to_list(limit)

    # Mark as read for this user (except admin viewing)
    if user["role"] != "admin":
        unread_field = "unread_client" if user["id"] == convo["client_id"] else "unread_professional"
        await db.conversations.update_one({"id": conv_id}, {"$set": {unread_field: 0}})

    return msgs


@api_router.post("/conversations/{conv_id}/messages")
async def send_message(conv_id: str, req: SendMessageRequest, user = Depends(get_current_user)):
    convo = await db.conversations.find_one({"id": conv_id}, {"_id": 0})
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if user["id"] not in (convo["client_id"], convo["professional_id"]):
        raise HTTPException(status_code=403, detail="Not a participant in this conversation")

    content = (req.content or "").strip()
    attachment_paths = req.attachment_paths or []
    if not content and not attachment_paths:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(content) > 4000:
        raise HTTPException(status_code=400, detail="Message too long (max 4000 chars)")
    if len(attachment_paths) > 6:
        raise HTTPException(status_code=400, detail="Max 6 attachments per message")

    # Validate that the attachment paths belong to this user (uploaded by them under their chat folder)
    valid_attachments = []
    for path in attachment_paths:
        attachment_doc = await db.chat_attachments.find_one({"path": path, "uploader_id": user["id"]}, {"_id": 0})
        if not attachment_doc:
            raise HTTPException(status_code=400, detail=f"Invalid attachment: {path}")
        # Bind attachment to conversation for serve-time auth
        await db.chat_attachments.update_one(
            {"path": path},
            {"$set": {"conversation_id": conv_id}},
        )
        valid_attachments.append({
            "path": path,
            "filename": attachment_doc.get("filename"),
            "content_type": attachment_doc.get("content_type"),
            "size": attachment_doc.get("size"),
        })

    now = datetime.now(timezone.utc).isoformat()
    msg = {
        "id": str(uuid.uuid4()),
        "conversation_id": conv_id,
        "sender_id": user["id"],
        "sender_name": user.get("name"),
        "sender_role": user["role"],
        "content": content,
        "attachments": valid_attachments,
        "created_at": now,
    }
    await db.messages.insert_one(msg)
    msg.pop("_id", None)

    # Update conversation summary + unread counter for the OTHER side
    if user["id"] == convo["client_id"]:
        inc_field = "unread_professional"
    else:
        inc_field = "unread_client"

    preview = content if content else f"[{len(valid_attachments)} attachment{'s' if len(valid_attachments)>1 else ''}]"
    await db.conversations.update_one(
        {"id": conv_id},
        {
            "$set": {
                "last_message_at": now,
                "last_message_preview": preview[:120],
                "last_sender_id": user["id"],
                "updated_at": now,
            },
            "$inc": {inc_field: 1},
        },
    )

    # Best-effort in-app notification for recipient
    recipient_id = convo["professional_id"] if user["id"] == convo["client_id"] else convo["client_id"]
    try:
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": recipient_id,
            "type": "new_message",
            "title": f"New message from {user.get('name', 'someone')}",
            "body": preview[:160],
            "data": {"conversation_id": conv_id},
            "read": False,
            "created_at": now,
        })
    except Exception:
        pass

    return msg


# ============= CHAT ATTACHMENTS (upload + serve) =============

@api_router.post("/chat/attachments")
async def upload_chat_attachment(file: UploadFile = File(...), user = Depends(get_current_user)):
    if user["role"] not in ["client", "professional"]:
        raise HTTPException(status_code=403, detail="Only clients and professionals can upload chat attachments")

    data = await file.read()
    try:
        ext = storage_service.validate_upload(file.filename or "", len(data))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    content_type = file.content_type or storage_service.get_content_type(file.filename or f"file.{ext}")
    path = storage_service.build_chat_path(user["id"], file.filename or f"file.{ext}")
    try:
        storage_service.put_object(path, data, content_type)
    except Exception as e:
        logger.exception("Chat attachment upload failed")
        raise HTTPException(status_code=502, detail=f"Failed to upload file: {e}")

    record = {
        "id": str(uuid.uuid4()),
        "path": path,
        "filename": file.filename,
        "content_type": content_type,
        "size": len(data),
        "uploader_id": user["id"],
        "conversation_id": None,  # bound when message is sent
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.chat_attachments.insert_one(record)
    record.pop("_id", None)
    return {
        "path": path,
        "filename": record["filename"],
        "content_type": content_type,
        "size": record["size"],
        "url": f"/api/files/chat/{path}",
    }


@api_router.get("/files/chat/{path:path}")
async def get_chat_attachment(path: str, user = Depends(get_current_user)):
    record = await db.chat_attachments.find_one({"path": path}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    # Auth: uploader, conversation participant, or admin can view
    can_view = (
        user["role"] == "admin"
        or record["uploader_id"] == user["id"]
    )
    if not can_view and record.get("conversation_id"):
        convo = await db.conversations.find_one({"id": record["conversation_id"]}, {"_id": 0})
        if convo and user["id"] in (convo["client_id"], convo["professional_id"]):
            can_view = True
    if not can_view:
        raise HTTPException(status_code=403, detail="You don't have access to this file")

    try:
        content, content_type = storage_service.get_object(path)
    except Exception as e:
        logger.exception("Chat attachment download failed")
        raise HTTPException(status_code=502, detail=f"Failed to fetch file: {e}")
    return Response(content=content, media_type=content_type)


# ============= KYC / ID VERIFICATION =============

@api_router.post("/kyc/upload-id")
async def upload_id_photo(
    side: str = Form(...),
    file: UploadFile = File(...),
    user = Depends(get_current_user),
):
    """Upload front/back of national ID. Stores in object storage and updates user record.
    
    Both clients and professionals can upload ID for verification. Admins later flip
    `id_verified` after reviewing both sides in the Admin → Users panel.
    """
    if side not in ("front", "back"):
        raise HTTPException(status_code=400, detail="side must be 'front' or 'back'")

    data = await file.read()
    try:
        ext = storage_service.validate_kyc_image(file.filename or "", len(data))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    content_type = file.content_type or storage_service.get_content_type(file.filename or f"id.{ext}")
    path = storage_service.build_kyc_path(user["id"], side, file.filename or f"id.{ext}")
    try:
        storage_service.put_object(path, data, content_type)
    except Exception as e:
        logger.exception("KYC upload failed")
        raise HTTPException(status_code=502, detail=f"Failed to upload ID photo: {e}")

    record = {
        "user_id": user["id"],
        "side": side,
        "path": path,
        "filename": file.filename,
        "content_type": content_type,
        "size": len(data),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    # Track every upload (audit trail)
    await db.kyc_uploads.insert_one(record)
    record.pop("_id", None)

    # Mark the user's current KYC document for this side; reset verification when re-uploaded
    field = "id_front_path" if side == "front" else "id_back_path"
    await db.users.update_one(
        {"id": user["id"]},
        {
            "$set": {
                field: path,
                "id_verified": False,
                "id_verification_status": "pending",
                "id_uploaded_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )

    return {
        "side": side,
        "path": path,
        "url": f"/api/files/kyc/{path}",
        "status": "pending",
    }


@api_router.get("/kyc/status")
async def get_my_kyc_status(user = Depends(get_current_user)):
    """Return the current user's KYC progress and verification state."""
    me = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0}) or {}
    return {
        "id_verified": bool(me.get("id_verified")),
        "id_verification_status": me.get("id_verification_status", "not_started"),
        "id_front_uploaded": bool(me.get("id_front_path")),
        "id_back_uploaded": bool(me.get("id_back_path")),
        "id_front_url": f"/api/files/kyc/{me['id_front_path']}" if me.get("id_front_path") else None,
        "id_back_url": f"/api/files/kyc/{me['id_back_path']}" if me.get("id_back_path") else None,
        "id_uploaded_at": me.get("id_uploaded_at"),
        "id_verified_at": me.get("id_verified_at"),
        "id_verification_notes": me.get("id_verification_notes"),
    }


@api_router.get("/files/kyc/{path:path}")
async def get_kyc_file(path: str, user = Depends(get_current_user)):
    """Serve KYC photos. Only the uploader or an admin can view."""
    record = await db.kyc_uploads.find_one({"path": path}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    if user["role"] != "admin" and record["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You don't have access to this file")
    try:
        content, content_type = storage_service.get_object(path)
    except Exception as e:
        logger.exception("KYC file download failed")
        raise HTTPException(status_code=502, detail=f"Failed to fetch file: {e}")
    return Response(content=content, media_type=content_type)


class KYCVerifyRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


@api_router.get("/admin/kyc/pending")
async def admin_list_pending_kyc(user = Depends(get_current_user), limit: int = 200):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    users = await db.users.find(
        {"id_verification_status": "pending"},
        {"_id": 0, "password_hash": 0},
    ).sort("id_uploaded_at", -1).to_list(limit)
    return users


@api_router.get("/admin/kyc/{user_id}")
async def admin_get_user_kyc(user_id: str, user = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    target = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user": target,
        "id_front_url": f"/api/files/kyc/{target['id_front_path']}" if target.get("id_front_path") else None,
        "id_back_url": f"/api/files/kyc/{target['id_back_path']}" if target.get("id_back_path") else None,
    }


@api_router.post("/admin/kyc/{user_id}/verify")
async def admin_verify_kyc(user_id: str, req: KYCVerifyRequest, user = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if not target.get("id_front_path") or not target.get("id_back_path"):
        raise HTTPException(status_code=400, detail="User has not uploaded both front and back ID photos")

    new_status = "verified" if req.approved else "rejected"
    update = {
        "id_verified": req.approved,
        "id_verification_status": new_status,
        "id_verification_notes": req.notes,
        "id_verified_at": datetime.now(timezone.utc).isoformat(),
        "id_verified_by": user["id"],
    }
    await db.users.update_one({"id": user_id}, {"$set": update})

    # Best-effort notify the user
    try:
        await send_push_notification(
            user_id=user_id,
            title="ID Verification " + ("Approved" if req.approved else "Rejected"),
            body=req.notes or ("Your ID has been verified." if req.approved else "Please re-upload clearer ID photos."),
            data={"type": "kyc_result", "approved": req.approved},
        )
    except Exception:
        pass

    return {"user_id": user_id, "id_verified": req.approved, "status": new_status}


# ============= ADMIN CHAT MODERATION =============

@api_router.get("/admin/conversations")
async def admin_list_conversations(user = Depends(get_current_user), limit: int = 200):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    convos = await db.conversations.find({}, {"_id": 0}).sort("last_message_at", -1).to_list(limit)
    for c in convos:
        client_user = await db.users.find_one({"id": c["client_id"]}, {"_id": 0, "password_hash": 0})
        pro_user = await db.users.find_one({"id": c["professional_id"]}, {"_id": 0, "password_hash": 0})
        c["client"] = client_user
        c["professional"] = pro_user
        c["message_count"] = await db.messages.count_documents({"conversation_id": c["id"]})
    return convos


# ============= PASSWORD RESET =============

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=128)


def _hash_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


@api_router.post("/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    """Always returns 200 to prevent email enumeration."""
    generic_response = {
        "message": "If an account exists for that email, a password reset link has been sent.",
    }

    target = await db.users.find_one({"email": req.email.lower()}, {"_id": 0})
    if not target:
        return generic_response

    # Generate token, hash it for storage, send raw token via email
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_reset_token(raw_token)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()

    await db.users.update_one(
        {"id": target["id"]},
        {"$set": {
            "reset_token_hash": token_hash,
            "reset_token_expires": expires_at,
        }},
    )

    frontend_base = os.environ.get("FRONTEND_BASE_URL", "").rstrip("/")
    reset_link = f"{frontend_base}/reset-password?token={raw_token}"

    if not os.environ.get("RESEND_API_KEY"):
        # Email service not yet configured — surface the link in logs only (never to the API response)
        logger.warning(
            "RESEND_API_KEY is not set; password reset link generated but email cannot be sent. "
            "Reset link (DEV ONLY): %s", reset_link,
        )
        return generic_response

    try:
        html = email_service.password_reset_html(target.get("name", ""), reset_link)
        await email_service.send_email(
            to=target["email"],
            subject="Reset your Kazi Links password",
            html=html,
        )
    except Exception as e:
        logger.exception("Failed to send password reset email: %s", e)
        # Still return generic success — don't leak email-send failures to caller

    return generic_response


@api_router.post("/auth/reset-password")
async def reset_password(req: ResetPasswordRequest):
    token_hash = _hash_reset_token(req.token)
    target = await db.users.find_one({"reset_token_hash": token_hash}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    expires_str = target.get("reset_token_expires")
    if not expires_str:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    try:
        expires_at = datetime.fromisoformat(expires_str)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    if datetime.now(timezone.utc) > expires_at:
        # Clean up expired token
        await db.users.update_one(
            {"id": target["id"]},
            {"$unset": {"reset_token_hash": "", "reset_token_expires": ""}},
        )
        raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")

    # Hash new password and invalidate token
    new_hash = bcrypt.hashpw(req.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    await db.users.update_one(
        {"id": target["id"]},
        {
            "$set": {"password_hash": new_hash},
            "$unset": {"reset_token_hash": "", "reset_token_expires": ""},
        },
    )

    return {"message": "Password has been reset successfully. You can now log in with your new password."}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def init_services():
    try:
        storage_service.init_storage()
    except Exception as e:
        logger.warning("Object storage init failed at startup (will retry on first use): %s", e)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
