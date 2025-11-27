from fastapi import APIRouter, Depends, HTTPException
from utils.check import chk_user
from utils.security import get_current_user
from db.db import db
from bson import ObjectId

router = APIRouter()


@router.post("/add/item/wish_list/{product_id}/")
async def add_item_in_cart(product_id: str, current_user = Depends(get_current_user)):
    try:
        
        user = await chk_user(current_user)

        existing_wishlist = await db.wishlist.find_one({"user": ObjectId(user["_id"])})
        if existing_wishlist:
            item_exists = next(
                (item for item in existing_wishlist.get("items", []) if item["item_id"] == product_id),
                None
            )
            if item_exists:
                return {"msg": "Product Already In Wishlist"}
            await db.wishlist.update_one({"user": user["_id"]},
                {"$push": {"items": {"item_id": product_id}}}
            )
            return {"msg": "Product Add Success",}
        else:
            product_doc = {
                "user": user["_id"],
                "items": [{"item_id": product_id}]}
            res = await db.wishlist.insert_one(product_doc)
            created = await db.wishlist.find_one({"_id": res.inserted_id})
            return {"msg": "Product Add Success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/get/wishlist/")
async def get_wishlist(current_user = Depends(get_current_user)):
    try:
        user = await chk_user(current_user)

        wishlist = await db.wishlist.find_one({"user": ObjectId(user["_id"])})
        if not wishlist or not wishlist.get("items"):
            return {"msg": "Wishlist is empty", "items": []}

        product_ids = []
        for it in wishlist.get("items", []):
            pid_str = it.get("item_id")
            if not pid_str:
                continue
            try:
                product_ids.append(ObjectId(pid_str))
            except Exception:
                continue

        if not product_ids:
            return {"msg": "Wishlist is empty", "items": []}

        products = await db.product.find({"_id": {"$in": product_ids}}).to_list(length=None)

        items = []
        for p in products:
            items.append({
                "id": str(p["_id"]),
                "title": p.get("title") or p.get("name"),
                "price": float(p.get("price", 0.0)),
                "final_price": float(p.get("final_price", p.get("price", 0.0))),
                "image_url":p.get("image_url")
            })

        return {
            "msg": "Wishlist fetched successfully",
            "items": items
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.delete("/remove/item/wish_list/{product_id}/")
async def remove_item_from_cart(product_id: str, current_user = Depends(get_current_user)):
    try:
        user = await chk_user(current_user)

        wishlist_doc = await db.wishlist.find_one({"user": ObjectId(user["_id"])})
        if not wishlist_doc:
            raise HTTPException(status_code=404, detail="Wishlist not found")

        item_exists = next((it for it in wishlist_doc.get("items", []) if it["item_id"] == product_id), None)

        if not item_exists:
            raise HTTPException(status_code=404, detail="Item not found in cart")
        
        await db.wishlist.update_one(
            {"user": ObjectId(user["_id"])},
            {"$pull": {"items": {"item_id": product_id}}}
        )

        updated_wishlist = await db.wishlist.find_one({"user": ObjectId(user["_id"])})

        if not updated_wishlist or len(updated_wishlist.get("items", [])) == 0:
            await db.wishlist.delete_one({"user": ObjectId(user["_id"])})
            return {"msg": "Item removed. wishlist is empty and has been deleted."}
        return {"msg": "Item removed from wishlist"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))