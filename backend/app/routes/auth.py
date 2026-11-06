import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

import bcrypt
from jose import jwt, JWTError
from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# JWT Configuration
JWT_SECRET = os.environ.get("FINSIGHT_JWT_SECRET", "finsight-secure-local-jwt-token-signing-secret-key-32b-salt")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer(auto_error=False)

class LoginRequest(BaseModel):
    email: str
    password: str

# Demo Accounts with pre-computed bcrypt password hashes
# judge@finsight.local -> JudgePassword2024!
# arjun@techcorp.in -> ArjunSecure2024
# rahul@delivery.in -> RahulDelivery2024
# ananya@university.edu -> StudentLife2024
DEMO_USERS = {
    "judge@finsight.local": {
        "name": "Hackathon Judge",
        "role": "Auditor & Evaluator",
        "password_hash": "$2b$10$98lKJgTVWHq.5phmvbFdbeExj8W5z0iuGjNbs5Vin5AN7pHidoWVm"
    },
    "arjun@techcorp.in": {
        "name": "Arjun Verma",
        "role": "Salaried Professional",
        "password_hash": "$2b$10$Ru24.6ZcbIUahs/X7Wz5uema5ShKh3d0Gsq4lIoNPugQwCRqI20MC"
    },
    "rahul@delivery.in": {
        "name": "Rahul Sharma",
        "role": "Gig Economy Partner",
        "password_hash": "$2b$10$tc84/QKmHJbyMXwqpgbwfeks7IvUzh66x1JQc5zMBajMKcLD.AYci"
    },
    "ananya@university.edu": {
        "name": "Ananya Sen",
        "role": "College Student",
        "password_hash": "$2b$10$dZ1s4Z6ZIJt.Wutwn1NT/utsaSh4sgWpWfnj/Mm4Mrc9ngLTpzvHG"
    }
}

# In-memory store for custom local users registered during the active session
CUSTOM_LOCAL_USERS: Dict[str, Dict[str, Any]] = {}

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(10)).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create cryptographically signed JWT token using HMAC-SHA256."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4())
    })
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and verify signed JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired authentication token: {str(e)}"
        )

def require_authenticated_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency that enforces JWT authentication on protected routes.
    Rejects requests missing or carrying an invalid Bearer token.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication credentials required. Please provide a valid Bearer token."
        )
    return decode_access_token(credentials.credentials)

@router.post("/login")
def login(req: LoginRequest) -> Dict[str, Any]:
    """
    Real local authentication endpoint.
    Verifies passwords using bcrypt and returns signed JWT tokens.
    Supports preset demo users and auto-enrolled custom local testers.
    """
    email_clean = req.email.strip().lower()
    if not email_clean:
        raise HTTPException(status_code=400, detail="Email is required.")
    if not req.password:
        raise HTTPException(status_code=400, detail="Password is required.")

    # 1. Match Demo Accounts
    if email_clean in DEMO_USERS:
        demo = DEMO_USERS[email_clean]
        if not verify_password(req.password, demo["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid password for demo account.")
        user_info = {
            "email": email_clean,
            "name": demo["name"],
            "role": demo["role"]
        }
    # 2. Match or Register Custom Local User
    elif email_clean in CUSTOM_LOCAL_USERS:
        cust = CUSTOM_LOCAL_USERS[email_clean]
        if not verify_password(req.password, cust["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid password for local account.")
        user_info = {
            "email": email_clean,
            "name": cust["name"],
            "role": cust["role"]
        }
    else:
        # First-time enrollment for custom local evaluation
        name_part = email_clean.split("@")[0].replace(".", " ").title()
        pw_hash = hash_password(req.password)
        CUSTOM_LOCAL_USERS[email_clean] = {
            "name": name_part,
            "role": "Local Auditor",
            "password_hash": pw_hash
        }
        user_info = {
            "email": email_clean,
            "name": name_part,
            "role": "Local Auditor"
        }

    # Generate signed JWT token
    token = create_access_token({
        "sub": email_clean,
        "name": user_info["name"],
        "role": user_info["role"],
        "auth_type": "local_bcrypt_jwt"
    })

    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": email_clean,
            "name": user_info["name"],
            "role": user_info["role"],
            "session_mode": "Local Encrypted Session (Bcrypt + JWT)"
        }
    }

@router.get("/me")
def get_current_user(user: Dict[str, Any] = Depends(require_authenticated_user)) -> Dict[str, Any]:
    """Returns local active session status for the authenticated token."""
    return {
        "authenticated": True,
        "user": user
    }
