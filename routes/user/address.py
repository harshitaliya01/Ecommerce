from models.models import UserAddress
from utils.security import get_current_user
from utils.check import chk_user
from fastapi import APIRouter, HTTPException,Depends,Form
from typing import Optional
from bson import ObjectId

from db.db import db

router = APIRouter()

@router.post("/add/address/")
async def add_address(address:UserAddress, current_user= Depends(get_current_user)):
    try:
        user = await chk_user(current_user)

        existing = await db.user_address.find_one({"user":ObjectId(user["_id"])})
        if existing:
            raise HTTPException(status_code=400,detail="You Already Add Address...")
        doc = {
                "user":user["_id"],
                "mobile_no": address.mobile_no,
                "address":address.address
            }
       
        res = await db.user_address.insert_one(doc)
        created = await db.user_address.find_one({"_id":res.inserted_id})
        address_data = {
                "id":str(created["_id"]),
                "mobile_no":created["mobile_no"],
                "address":created["address"],
            }
        return {"msg": "add succesful","address": address_data}
    
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))   
    

@router.get("/show/address/")
async def show_address(current_user = Depends(get_current_user)):
    try:
        user = await chk_user(current_user)

        address = await db.user_address.find_one({"user": ObjectId(user["_id"])})

        if not address:
            raise HTTPException(status_code=404, detail="Address not found")

        address_data = {
            "id": str(address["_id"]),
            "mobile_no": address.get("mobile_no"),
            "address": address.get("address"),
        }

        return {"address": address_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.put("/update/address/{address_id}")
async def update_address(
    address_id: str,
    address: Optional[str] = Form(None),
    mobile_no:Optional[str] = Form(None),
    current_user = Depends(get_current_user)
):
    try:
        user = await chk_user(current_user)

        existing = await db.user_address.find_one({"_id": ObjectId(address_id), "user": user["_id"]})
        if not existing:
            raise HTTPException(status_code=404, detail="Address not found")

        update_fields = {}

        if address is not None:
            update_fields["address"] = address

        if mobile_no is not None:
            update_fields["mobile_no"] = mobile_no

        if update_fields:
            await db.user_address.update_one({"_id": ObjectId(address_id)}, {"$set": update_fields})
        
        updated = await db.user_address.find_one({"_id":  ObjectId(address_id)})

        result_data = {
            "id": str(updated["_id"]),
            "mobile_no": updated["mobile_no"],
            "address": updated["address"]
        }

        return {"msg": "address updated successfully", "address": result_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
