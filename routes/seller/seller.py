from fastapi import APIRouter, HTTPException, Form
from datetime import datetime, timedelta
from models.models import SellerVerifyOTP , Seller, SellerLogin
from utils.security import hash_password, create_access_token, verify_password
from utils.mail import generate_otp, send_otp_email
from pydantic import EmailStr
from typing import Optional
from db.db import db
import os  

router = APIRouter()

@router.post("/seller/register/")
async def register(user: Seller):
    try:
        existing = await db.seller.find_one({"email": user.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email Already Registered")

        hashed_pw = hash_password(user.password)
        otp = generate_otp()
        otp_expiry = datetime.utcnow() + timedelta(minutes=int(os.getenv("OTP_EXPIRE_MINUTES")))

        doc = {
            "business_name": user.business_name,
            "email": user.email,
            "gst_no": user.gst_no,
            "password": hashed_pw,
            "role": "seller",
            "is_verified": False,
            "email_otp": otp,
            "email_otp_expires_at": otp_expiry,
        }

        res = await db.seller.insert_one(doc)
        created = await db.seller.find_one({"_id": res.inserted_id})

        # send OTP to seller email
        await send_otp_email(user.email, otp)  # this uses your real email logic

        user_data = {
            "id": str(created["_id"]),
            "business_name": created["business_name"],
            "gst_no": created["gst_no"],
            "email": created["email"],
            "is_verified": created["is_verified"],
        }

        return {
            "msg": "seller registered, OTP sent to your email",
            "seller": user_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/seller/verify-otp/")
async def verify_seller_otp(data: SellerVerifyOTP):
    try:
        user = await db.seller.find_one({"email": data.email})
        if not user:
            raise HTTPException(status_code=404, detail="Seller not found")

        if user.get("is_verified"):
            return {"message": "Seller email already verified"}

        # check OTP
        if user.get("email_otp") != data.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # check expiry
        expires_at = user.get("email_otp_expires_at")
        if not expires_at or expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="OTP expired")

        # mark as verified & clear OTP
        await db.seller.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"is_verified": True},
                "$unset": {"email_otp": "", "email_otp_expires_at": ""},
            },
        )

        # give token after successful verification
        access_token = create_access_token({"email": data.email})

        return {
            "message": "Seller email verified successfully",
            "access_token": access_token,
            "token_type": "bearer",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/seller/resend/otp/")
async def seller_resend_otp(email: Optional[EmailStr] = Form(...)):
    try:
        existing = await db.seller.find_one({"email": email})

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

        await db.seller.update_one({"email": email}, {"$set": doc})
        created = await db.seller.find_one({"email": email})


        # send OTP to email
        await send_otp_email(email, otp)

        user_data = {
            "id": str(created["_id"]),
            "business_name": created["business_name"],
            "email": created["email"],
            "is_verified": created["is_verified"],
        }

        return {
            "msg": "registered, OTP sent to your email",
            "user": user_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@router.post("/seller/login/")
async def login(usertry: SellerLogin):
    try:
        user = await db.seller.find_one({"email": usertry.email})
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
