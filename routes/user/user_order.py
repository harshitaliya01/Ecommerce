from utils.security import get_current_user
from fastapi import APIRouter, HTTPException,Depends
from utils.check import chk_user
from datetime import datetime
from bson import ObjectId
from db.db import db

router = APIRouter()

@router.get("/my/orders/")
async def get_my_orders(current_user = Depends(get_current_user)):
    try:
        user = await chk_user(current_user)

        orders = await db.order.find({"user": user["_id"]}).to_list(length=None)
        formatted_orders = []

        for o in orders:
            formatted_orders.append({
                "id": str(o["_id"]),
                "user": str(o["user"]),
                "seller": str(o["seller"]),
                "items": o.get("items", []),
                "total": o.get("total", 0),
                "final_total": o.get("final_total", 0),
                "status": o.get("status"),
                "address": o.get("address"),
                "created_at": o["created_at"].isoformat() if o.get("created_at") else None
            })

        return {"orders": formatted_orders}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/order/{order_id}/cancel")
async def cancel_order(order_id: str, current_user = Depends(get_current_user)):
    try:
        user = await chk_user(current_user)

        order = await db.order.find_one({"_id": ObjectId(order_id), "user": user["_id"]})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.get("status") != "pending":
            raise HTTPException(
                status_code=400,
                detail="You can cancel order only when status is 'pending'"
            )

        for item in order.get("items", []):
            pid_str = item.get("item_id")
            qty = int(item.get("quantity", 0))
            if not pid_str or qty <= 0:
                continue

            try:
                pid = ObjectId(pid_str)
            except Exception:
                continue

            await db.product.update_one(
                {"_id": pid},
                {"$inc": {"stock": qty}}
            )

        await db.order.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "cancelled by buyer", "cancelled_at": datetime.utcnow()}}
        )

        updated = await db.order.find_one({"_id": ObjectId(order_id)})

        clean_items = []
        for it in updated.get("items", []):
            clean_items.append({
                **it,
                "item_id": str(it.get("item_id")),
            })

        order_response = {
            "id": str(updated["_id"]),
            "user": str(updated["user"]),
            "seller": str(updated["seller"]) if updated.get("seller") else None,
            "items": clean_items,
            "total": float(updated.get("total", 0.0)),
            "final_total": float(updated.get("final_total", 0.0)),
            "status": updated.get("status"),
            "address": updated.get("address"),
            "created_at": updated["created_at"].isoformat() if updated.get("created_at") else None,
            "cancelled_at": updated["cancelled_at"].isoformat() if updated.get("cancelled_at") else None,
        }

        return {"msg": "Order cancelled successfully", "order": order_response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/order/{order_id}/return")
async def return_order(order_id: str, current_user = Depends(get_current_user)):
    try:
        user = await chk_user(current_user)
        
        order = await db.order.find_one({"_id": ObjectId(order_id), "user": user["_id"]})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail="You can return order only when status is 'completed'"
            )

        for item in order.get("items", []):
            pid_str = item.get("item_id")
            qty = int(item.get("quantity", 0))
            if not pid_str or qty <= 0:
                continue

            try:
                pid = ObjectId(pid_str)
            except Exception:
                continue

            await db.product.update_one(
                {"_id": pid},
                {"$inc": {"stock": qty}}
            )

        await db.order.update_one(
            {"_id": ObjectId(order_id)},
            {
                "$set": {
                    "status": "return",
                    "returned_at": datetime.utcnow()
                }
            }
        )
        updated = await db.order.find_one({"_id": ObjectId(order_id)})

        clean_items = []
        for it in updated.get("items", []):
            clean_items.append({
                **it,
                "item_id": str(it.get("item_id")),
            })

        order_response = {
            "id": str(updated["_id"]),
            "user": str(updated["user"]),
            "seller": str(updated["seller"]) if updated.get("seller") else None,
            "items": clean_items,
            "total": float(updated.get("total", 0.0)),
            "final_total": float(updated.get("final_total", 0.0)),
            "status": updated.get("status"),
            "address": updated.get("address"),
            "created_at": updated["created_at"].isoformat() if updated.get("created_at") else None,
            "returned_at": updated["returned_at"].isoformat() if updated.get("returned_at") else None,
        }

        return {"msg": "Order returned successfully", "order": order_response}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))