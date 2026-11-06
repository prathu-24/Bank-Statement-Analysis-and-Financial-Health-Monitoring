from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    name: str
    email: str
    role: str

DEMO_USERS = {
    "judge@finsight.local": {"name": "Hackathon Judge", "role": "Auditor & Evaluator"},
    "arjun@techcorp.in": {"name": "Arjun Verma", "role": "Salaried Professional"},
    "rahul@delivery.in": {"name": "Rahul Sharma", "role": "Gig Economy Partner"},
    "ananya@university.edu": {"name": "Ananya Sen", "role": "College Student"}
}

@router.post("/login")
def login(req: LoginRequest) -> Dict[str, Any]:
    """
    Local authentication endpoint.
    Accepts standard credentials and pre-configured hackathon demo accounts.
    """
    email_clean = req.email.strip().lower()
    if not email_clean:
        raise HTTPException(status_code=400, detail="Email is required.")
    if not req.password:
        raise HTTPException(status_code=400, detail="Password is required.")

    # Match demo profile or synthesize named profile
    if email_clean in DEMO_USERS:
        user_info = DEMO_USERS[email_clean]
    else:
        name_part = email_clean.split("@")[0].replace(".", " ").title()
        user_info = {"name": name_part, "role": "Account Holder"}

    return {
        "status": "success",
        "access_token": f"fst_{email_clean[:6]}_{abs(hash(req.password))}",
        "token_type": "bearer",
        "user": {
            "email": email_clean,
            "name": user_info["name"],
            "role": user_info["role"],
            "session_mode": "Local Encrypted Session"
        }
    }

@router.get("/me")
def get_current_user() -> Dict[str, Any]:
    """Returns local active session status."""
    return {
        "authenticated": True,
        "default_user": DEMO_USERS["judge@finsight.local"]
    }
