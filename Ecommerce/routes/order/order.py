from fastapi import APIRouter, Depends, HTTPException
from utils.security import get_current_user
from db.db import db
from utils.check import chk_user
from bson import ObjectId
from datetime import datetime
from typing import Dict, List, Tuple
from utils.order_email import send_order_emails  # 👈 add this


router = APIRouter()

@router.post("/create/order/")
async def create_orders(current_user=Depends(get_current_user)):
    try:
        user = await chk_user(current_user)

        # 1) Check address
        user_address = await db.user_address.find_one({"user": ObjectId(user["_id"])})
        if not user_address or not user_address.get("address") or not user_address.get("mobile_no"):
            raise HTTPException(
                status_code=400,
                detail="Add your address & phone number before placing order"
            )

        # 2) Get all items from cart
        cart_items = await db.cart.find({"user": ObjectId(user["_id"])}).to_list(length=None)
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # Group structure: { seller_id_str: { "seller_id": ObjectId, "items": [...], "total": float, "final_total": float } }
        seller_groups: Dict[str, Dict] = {}
        stock_updates: List[Tuple[str, int]] = []

        # 3) Build groups per seller & check stock
        for item in cart_items:
            pid_str = item.get("item_id")
            qty = int(item.get("quantity", 0))

            if qty <= 0:
                continue

            product = await db.product.find_one({"_id": ObjectId(pid_str)})
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {pid_str} not found")

            # seller from product
            seller_id = product.get("seller")
            if not seller_id:
                raise HTTPException(status_code=500, detail="Product missing seller info")

            # Stock check
            if product.get("stock", 0) < qty:
                raise HTTPException(
                    status_code=400,
                    detail=f"{product.get('name', '')} insufficient stock"
                )

            # Snapshot for this item (stored in order)
            item_snapshot = {
                "item_id": pid_str,
                "quantity": qty,
                "price": float(item.get("price", 0)),
                "final_price": float(item.get("final_price", 0)),
                "title": product.get("title", product.get("name")),
            }

            seller_key = str(seller_id)
            if seller_key not in seller_groups:
                seller_groups[seller_key] = {
                    "seller_id": seller_id,
                    "items": [],
                    "total": 0.0,
                    "final_total": 0.0,
                }

            seller_groups[seller_key]["items"].append(item_snapshot)
            seller_groups[seller_key]["total"] += item_snapshot["price"] * qty
            seller_groups[seller_key]["final_total"] += item_snapshot["final_price"] * qty

            stock_updates.append((pid_str, qty))

        if not seller_groups:
            raise HTTPException(status_code=400, detail="No valid items in cart")

        # Optional grand total if you want it
        grand_final_total = sum(group["final_total"] for group in seller_groups.values())
        if grand_final_total <= 0:
            raise HTTPException(status_code=400, detail="Invalid order amount")

        # 4) Decrease stock with rollback on failure (for all products together)
        updated_products: List[Tuple[str, int]] = []
        for pid_str, qty in stock_updates:
            updated = await db.product.update_one(
                {"_id": ObjectId(pid_str), "stock": {"$gte": qty}},
                {"$inc": {"stock": -qty}}
            )

            if updated.modified_count == 0:
                # rollback previous stock changes
                for roll_pid, roll_qty in updated_products:
                    await db.product.update_one(
                        {"_id": ObjectId(roll_pid)},
                        {"$inc": {"stock": roll_qty}}
                    )
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock issue with product {pid_str}"
                )

            updated_products.append((pid_str, qty))

        # 5) Create ONE order per seller (multi-seller) with payment_pending
        address_snapshot = {
            "mobile_no": user_address.get("mobile_no"),
            "address": user_address.get("address"),
        }

        created_orders = []

        for seller_key, group in seller_groups.items():
            order_doc = {
                "user": user["_id"],
                "seller": group["seller_id"],        # important: seller-wise order
                "items": group["items"],
                "total": float(group["total"]),
                "final_total": float(group["final_total"]),
                "address": address_snapshot,
                "status": "pending",
                "created_at": datetime.utcnow(),
            }

            res = await db.order.insert_one(order_doc)

            created_orders.append({
                "id": str(res.inserted_id),
                "seller": seller_key,
                "items": group["items"],
                "total": group["total"],
                "final_total": group["final_total"],
                "status": "pending",
                "address": address_snapshot,
                "created_at": datetime.utcnow().isoformat()
            })

                # 6) Clear cart
                # 6) Clear cart
        await db.cart.delete_many({"user": ObjectId(user["_id"])})

        # 7) Send emails to user + sellers (async)
        await send_order_emails(
            user=user,
            orders=created_orders,
            grand_final_total=grand_final_total,
        )

        # 8) Return all seller-wise orders
        return {
            "msg": "Orders created",
            "orders": created_orders,
            "grand_final_total": grand_final_total
        }



    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
