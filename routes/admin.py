from models.models import AdminLogin, Admin
from utils.security import hash_password,create_access_token,verify_password
from utils.mail import send_otp_email,generate_otp
from fastapi import APIRouter, HTTPException
import os
from db.db import db
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/admin/register/{admin_secret}/")
async def register_admin(admin: Admin,admin_secret:str):
    try:

        admin_secret_env = os.getenv("ADMIN_SECRET_KEY")

        if not admin_secret_env:
            raise HTTPException(
                status_code=500,
                detail="Admin secret key is not configured on the server."
            )

        if admin_secret != admin_secret_env:
            raise HTTPException(
                status_code=403,
                detail="Invalid admin secret key."
            )

        existing = await db.user.find_one({"email": admin.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email Already Registered")

        hashed_pw = hash_password(admin.password)

        otp = generate_otp()
        otp_expiry = datetime.utcnow() + timedelta(
            minutes=int(os.getenv("OTP_EXPIRE_MINUTES", "10"))
        )

        doc = {
            "name": admin.name,
            "email": admin.email,
            "password": hashed_pw,
            "role": "admin",
            "is_verified": False,
            "email_otp": otp,
            "email_otp_expires_at": otp_expiry,
        }

        res = await db.user.insert_one(doc)
        created = await db.user.find_one({"_id": res.inserted_id})

        await send_otp_email(admin.email, otp)

        admin_data = {
            "id": str(created["_id"]),
            "name": created["name"],
            "email": created["email"],
            "role": created["role"],
            "is_verified": created["is_verified"],
        }

        return {
            "msg": "admin registered, OTP sent to your email",
            "admin": admin_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/admin/login/")
async def login(usertry: AdminLogin):
    try:
        user = await db.user.find_one({"email": usertry.email})
        if not user or not verify_password(usertry.password, user["password"]):
            raise HTTPException(status_code=400, detail="Incorrect credentials-password")

        if not user.get("is_verified", False):
            raise HTTPException(
                status_code=400,
                detail="Please verify your email with OTP before login",
            )

        token = create_access_token({"email": usertry.email})
        return {"message": "Success Login", "access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))