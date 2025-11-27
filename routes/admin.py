from models.models import AdminLogin
from utils.security import hash_password,create_access_token,verify_password
from fastapi import APIRouter, HTTPException
import os
from db.db import db

router = APIRouter()

@router.post("/admin/login/")
async def login(admintry:AdminLogin):
    try:
        user = await db.user.find_one({"email":admintry.email})
        if not user or not verify_password(admintry.password, user["password"]):
            raise HTTPException(status_code=400, detail="Incorrect credentials-password")
        token = create_access_token({"email": admintry.email})
        return {"message":"Success Login","access_token": token, "token_type": "bearer"}
    except Exception as e:
        return str(e)