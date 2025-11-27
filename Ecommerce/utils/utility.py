from db.db import db
from bson import ObjectId


async def cart_total_save(user_id):
    try:
        cart_items = await db.cart.find({"user": ObjectId(user_id)}).to_list(length=None)

        total = 0.0
        final = 0.0

        for item in cart_items:
            price = float(item.get("price", 0))
            f_price = float(item.get("final_price", 0))
            qty = float(item.get("quantity", 0))

            total += price * qty
            final += f_price * qty

        return total, final

    except Exception as e:
        raise Exception(str(e))
