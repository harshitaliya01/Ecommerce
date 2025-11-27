from db.db import db
from fastapi import HTTPException

async def chk_user(current_user):
    user = await db.user.find_one({"email": current_user["email"]})
    if not user or user.get("role") != "user":
        raise HTTPException(status_code=400, detail="You can not perform this action")
    return user

async def chk_seller(current_user):
    seller = await db.seller.find_one({"email": current_user["email"]})
    if not seller or seller.get("role") != "seller":
        raise HTTPException(status_code=400, detail="You can not perform this action")
    return seller