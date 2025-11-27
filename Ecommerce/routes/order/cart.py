from fastapi import APIRouter, Depends, HTTPException
from models.models import Cart
from utils.security import get_current_user
from utils.check import chk_user
from utils.utility import cart_total_save
from db.db import db
from bson import ObjectId

router = APIRouter()

@router.post("/add/item/{product_id}/")
async def add_item(cart: Cart, product_id: str, current_user=Depends(get_current_user)):
    try:
        user = await chk_user(current_user)

        product = await db.product.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        existing = await db.cart.find_one({"user": user["_id"], "item_id": product_id})

        if existing:
            await db.cart.update_one(
                {"user": user["_id"], "item_id": product_id},
                {"$set": {"quantity": cart.quantity}}
            )
        else:
            await db.cart.insert_one({
                "user": user["_id"],
                "item_id": product_id,
                "quantity": cart.quantity,
                "price": product["price"],
                "final_price": product["final_price"]
            })

        total, final = await cart_total_save(user["_id"])

        return {"msg": "Product added", "total": total, "with_discount": final}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/remove/item/{product_id}/")
async def remove_item(product_id: str, current_user=Depends(get_current_user)):
    try:
        user = await chk_user(current_user)

        result = await db.cart.delete_one({"user": user["_id"], "item_id": product_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item not found")

        total, final = await cart_total_save(user["_id"])
        return {"msg": "Item removed", "total": total, "with_discount": final}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cart/delete/")
async def clear_cart(current_user=Depends(get_current_user)):
    user = await chk_user(current_user)
    await db.cart.delete_many({"user": user["_id"]})
    return {"msg": "Cart cleared"}
    

@router.get("/cart/")
async def get_cart(current_user=Depends(get_current_user)):
    user =  await chk_user(current_user)

    cursor = db.cart.find({"user": user["_id"]})
    cart = await cursor.to_list(length=None)

    carts = []
    for o in cart:
        product = await db.product.find_one({"_id": ObjectId(o.get("item_id"))})
        carts.append({
            "id": str(o["_id"]),
            "product_name":product.get("name"),
            "product_price":product.get("price"),
            "image_url": product.get("image_url"),
            })
    total, final = await cart_total_save(user["_id"])

    print("0")
    return {
        "items": carts,
        "total": total,
        "with_discount": final
    }


@router.patch("/cart/update/{product_id}/")
async def update_cart_quantity(product_id: str, cart: Cart, current_user=Depends(get_current_user)):
    try:
        user = await chk_user(current_user)

        # Check product exists in cart
        existing = await db.cart.find_one({"user": user["_id"], "item_id": product_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Item Not found in cart.")

        # Update only quantity
        await db.cart.update_one(
            {"user": user["_id"], "item_id": product_id},
            {"$set": {"quantity": cart.quantity}}
        )
        total, final = await cart_total_save(user["_id"])

        return {
            "msg": "Cart updated successfully",
            "total": total,
            "with_discount": final
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
