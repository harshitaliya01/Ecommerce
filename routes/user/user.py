from fastapi import APIRouter, HTTPException, Form
from models.models import UserLogin,User,VerifyOTP, ForgotPasswordRequest, ResetPasswordWithOTP
from datetime import datetime, timedelta
from utils.mail import send_otp_email,generate_otp
from db.db import db
from pydantic import EmailStr
from typing import Optional
from utils.security import hash_password, verify_password, create_access_token
import os

router = APIRouter()

@router.post("/user/register/")
async def register(user: User):
    try:
        existing = await db.user.find_one({"email": user.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email Already Registered")

        hashed_pw = hash_password(user.password)
        otp = generate_otp()
        otp_expiry = datetime.utcnow() + timedelta(minutes=int(os.getenv("OTP_EXPIRE_MINUTES")))

        doc = {
            "name": user.name,
            "email": user.email,
            "password": hashed_pw,
            "role": "user",
            "is_verified": False,
            "email_otp": otp,
            "email_otp_expires_at": otp_expiry,
        }

    
        res = await db.user.insert_one(doc)
    
        created = await db.user.find_one({"_id": res.inserted_id})
    

        # send OTP to email
        await send_otp_email(user.email, otp)

        user_data = {
            "id": str(created["_id"]),
            "name": created["name"],
            "email": created["email"],
            "is_verified": created["is_verified"],
        }

        return {
            "msg": "registered, OTP sent to your email",
            "user": user_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))







@router.post("/user/verify-otp/")
async def verify_otp(data: VerifyOTP):
    try:
        user = await db.user.find_one({"email": data.email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.get("is_verified"):
            return {"message": "Email already verified"}

        # check OTP
        if user.get("email_otp") != data.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # check expiry
        expires_at = user.get("email_otp_expires_at")
        if not expires_at or expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="OTP expired")

        # mark as verified and clear OTP fields
        await db.user.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"is_verified": True},
                "$unset": {"email_otp": "", "email_otp_expires_at": ""},
            },
        )

        # optional: give token after successful verification
        access_token = create_access_token({"email": data.email})

        return {
            "message": "Email verified successfully",
            "access_token": access_token,
            "token_type": "bearer",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/resend/otp/")
async def resend_otp(email: Optional[EmailStr] = Form(...)):
    try:
        existing = await db.user.find_one({"email": email})

        if not existing:
            raise HTTPException(status_code=400,detail="Email Not Registered")
        
        if existing["is_verified"] == True:
            raise HTTPException(status_code=400, detail="Email Already Verified")

        otp = generate_otp()
        otp_expiry = datetime.utcnow() + timedelta(minutes=int(os.getenv("OTP_EXPIRE_MINUTES")))
        doc = {
            "is_verified": False,
            "email_otp": otp,
            "email_otp_expires_at": otp_expiry,
        }

        await db.user.update_one({"email": email}, {"$set": doc})
        created = await db.user.find_one({"email": email})


        # send OTP to email
        await send_otp_email(email, otp)

        user_data = {
            "id": str(created["_id"]),
            "name": created["name"],
            "email": created["email"],
            "is_verified": created["is_verified"],
        }

        return {
            "msg": "registered, OTP sent to your email",
            "user": user_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/login/")
async def login(usertry: UserLogin):
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