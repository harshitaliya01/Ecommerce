from fastapi import APIRouter, Depends , HTTPException
from utils.security import get_current_user
from utils.check import chk_seller
from db.db import db
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.get("/seller/orders/")
async def get_seller_orders(current_user = Depends(get_current_user)):
    try:
        seller = await chk_seller(current_user)

        # 2) Get only orders that belong to this seller
        orders = await db.order.find({"seller": seller["_id"]}).to_list(length=None)
        print(orders)
        seller_orders = []
        for o in orders:
            # make sure items are JSON-safe
            clean_items = []
            for it in o.get("items", []):
                clean_items.append({
                    **it,
                    "item_id": str(it.get("item_id")),  # force string
                })

            seller_orders.append({
                "id": str(o["_id"]),
                "user": str(o["user"]),
                "seller": str(o["seller"]),
                "items": clean_items,
                "total": float(o.get("total", 0.0)),
                "final_total": float(o.get("final_total", 0.0)),
                "status": o.get("status"),
                "address": o.get("address"),
                "created_at": o["created_at"].isoformat() if o.get("created_at") else None,
            })

        return {"orders": seller_orders}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

ALLOWED_STATUSES = {"pending", "shipped", "completed", "cancelled", "return"}

async def _check_seller_owns_order(order, seller):

    item_ids = [ObjectId(it["item_id"]) for it in order.get("items", [])]
 
    if not item_ids:
        raise HTTPException(status_code=400, detail="Order has no items")
 
    products = await db.product.find({"_id": {"$in": item_ids}}).to_list(length=None)
    product_map = {p["_id"]: p for p in products}

    for it in order.get("items", []):
        pid = ObjectId(it["item_id"])
        product = product_map.get(pid)

        if not product:
            raise HTTPException(status_code=404, detail=f"Product {pid} not found for this order")

        # IMPORTANT: assumes product has a 'seller' field = ObjectId of seller user
        if product.get("seller") != seller["_id"]:
            raise HTTPException(
                status_code=403,
                detail="You cannot modify this order because it contains items from another seller",
            )


async def _update_order_status(order_id: str, new_status: str, current_user):
    # 1) seller check
    seller = await chk_seller(current_user)

    if new_status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    # 2) get order
    try:
        oid = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order id")

    order = await db.order.find_one({"_id": oid})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 3) make sure this seller owns all items in this order
    await _check_seller_owns_order(order, seller)

    # 4) update status
    result = await db.order.find_one({"_id": oid})

    if result["status"] == "cancelled by buyer":
        raise HTTPException(status_code=400, detail="Order Cancelled By Buyer You Can Not Now Shipped Or Completed")
  
    if result["status"] == "return":
        raise HTTPException(status_code=400, detail="Order return By Buyer You Can Not Now Shipped Or Completed")
    
    result = await db.order.update_one(
        {"_id": oid},
        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update order status")

    return {"msg": f"Order status updated to {new_status}"}


@router.patch("/seller/order/{order_id}/shipped")
async def mark_order_shipped(order_id: str, current_user = Depends(get_current_user)):
    return await _update_order_status(order_id, "shipped", current_user)


@router.patch("/seller/order/{order_id}/completed")
async def mark_order_completed(order_id: str, current_user = Depends(get_current_user)):
    return await _update_order_status(order_id, "completed", current_user)
