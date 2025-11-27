from fastapi import APIRouter,Depends,HTTPException
from utils.security import get_current_user
from db.db import db
from bson import ObjectId
from models.models import Category

router = APIRouter()

@router.post("/add/category/")
async def add_category(category: Category, current_user= Depends(get_current_user)):
    try:
        user = await db.user.find_one({"email": current_user["email"]})
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=400, detail="You can not perform this action")
        
        existing = await db.category.find_one({"category":category.category})
        if existing:
            raise HTTPException(status_code=400,detail="This Category Is Already Avilable")
        
        doc = {"category": category.category}
       
        res = await db.category.insert_one(doc)
        created = await db.category.find_one({"_id":res.inserted_id})
        category_data = {
                "id":str(created["_id"]),
                "category":created["category"]
            }
        return {"msg": "add succesful","category": category_data}
    
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))   



@router.get("/categories/")
async def get_all_categories(current_user=Depends(get_current_user)):
    try:
        user = await db.user.find_one({"email": current_user["email"]})
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=400, detail="You can not perform this action")
        
        categories = await db.category.find().to_list(length=None)

        data = []
        for c in categories:
            data.append({
                "id": str(c["_id"]),
                "category": c.get("category", "")
            })

        return {"categories": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update/category/{category_id}/")
async def update_category(category_id: str, category: Category, current_user = Depends(get_current_user)):
    try:
        admin = await db.user.find_one({"email": current_user["email"]})
        if not admin or admin.get("role") != "admin":
            raise HTTPException(status_code=400, detail="You can not perform this action")

        existing_cat = await db.category.find_one({"_id": ObjectId(category_id)})
        if not existing_cat:
            raise HTTPException(status_code=404, detail="Category not found")

        duplicate = await db.category.find_one({
            "category": category.category,
            "_id": {"$ne": ObjectId(category_id)}
        })
        if duplicate:
            raise HTTPException(status_code=400, detail="This Category is already available")

        await db.category.update_one(
            {"_id": ObjectId(category_id)},
            {"$set": {"category": category.category}}
        )

        updated = await db.category.find_one({"_id": ObjectId(category_id)})

        category_data = {
            "id": str(updated["_id"]),
            "category": updated["category"],
        }

        return {"msg": "Category updated successfully", "category": category_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.delete("/delete/category/{category_id}/")
async def delete_category(category_id: str, current_user = Depends(get_current_user)):
    try:
        admin = await db.user.find_one({"email": current_user["email"]})
        if not admin or admin.get("role") != "admin":
            raise HTTPException(status_code=400, detail="You can not perform this action")

        existing = await db.category.find_one({"_id": ObjectId(category_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Category not found")

        await db.category.delete_one({"_id": ObjectId(category_id)})

        return {"msg": "Category deleted successfully", "id": category_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
