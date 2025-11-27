from fastapi import APIRouter, HTTPException
from models.models import ForgotPasswordRequest, ResetPasswordWithOTP
from datetime import datetime, timedelta
from utils.mail import send_otp_email,generate_otp
from db.db import db
from utils.security import hash_password, create_access_token
import os

router = APIRouter()

@router.post("/user/forgot-password/request/")
async def forgot_password_request(payload: ForgotPasswordRequest):
    try:
        user = await db.user.find_one({"email": payload.email})
        if not user:
            # same behavior style as resend_otp
            raise HTTPException(status_code=400, detail="Email not registered")

        if not user.get("is_verified"):
            raise HTTPException(status_code=400, detail="Email not verified")

        otp = generate_otp()
        otp_expiry = datetime.utcnow() + timedelta(
            minutes=int(os.getenv("OTP_EXPIRE_MINUTES", "10"))
        )
        await db.user.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "reset_otp": otp,
                    "reset_otp_expires_at": otp_expiry,
                }
            },
        )

        # send OTP to email
        await send_otp_email(payload.email, otp)

        return {
            "msg": "Password reset OTP sent to your email",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@router.post("/user/forgot-password/verify/")
async def forgot_password_verify(payload: ResetPasswordWithOTP):
    try:
        user = await db.user.find_one({"email": payload.email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.get("is_verified"):
            raise HTTPException(status_code=400, detail="Email not verified")

        # check reset OTP
        if user.get("reset_otp") != payload.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP...")

        # check expiry
        expires_at = user.get("reset_otp_expires_at")
        if not expires_at or expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="OTP expired...")

        # hash new password
        new_hashed_pw = hash_password(payload.new_password)

        # update password and clear reset fields
        await db.user.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"password": new_hashed_pw},
                "$unset": {
                    "reset_otp": "",
                    "reset_otp_expires_at": "",
                },
            },
        )

        # optional: give token immediately after reset
        access_token = create_access_token({"email": payload.email})

        return {
            "msg": "Password reset successfully",
            "access_token": access_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

