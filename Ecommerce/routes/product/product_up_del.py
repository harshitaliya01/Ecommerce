import os
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form,Request
from db.db import db
from utils.security import get_current_user
from utils.check import chk_seller
from typing import Optional
from bson import ObjectId

router = APIRouter()

import os, re
UPLOAD_DIR = "uploads"
for fn in os.listdir(UPLOAD_DIR):
    if fn.endswith('"}') or fn.endswith("'}"):
        clean = re.sub(r'["\'}]+$', '', fn)
        os.rename(os.path.join(UPLOAD_DIR, fn), os.path.join(UPLOAD_DIR, clean))
        print("Renamed", fn, "->", clean)

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.put("/product/update/{product_id}/")
async def update_product(
    product_id: str,
    request: Request,
    name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    discount: Optional[float] = Form(None),   # as percentage number, e.g. 10
    stock: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),  # optional new photo
    current_user = Depends(get_current_user)
):
    try:
        seller = await chk_seller(current_user)

        product = await db.product.find_one({"_id":ObjectId(product_id)})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if str(product.get("seller")) != str(seller["_id"]):
            raise HTTPException(status_code=403, detail="You are not the owner of this product")

        update_fields = {}

        if name is not None:
            update_fields["name"] = name
        if price is not None:
            update_fields["price"] = float(price)
        if discount is not None:
            update_fields["discount"] = f"{discount}%"
        if stock is not None:
            update_fields["stock"] = int(stock)
        if description is not None:
            update_fields["description"] = description
        if category is not None:
            chk_category = await db.category.find_one({"category":category})
            if not chk_category:
                raise HTTPException(status_code=400, detail="Add Avilable Category")
            update_fields["category"] = category

        if photo is not None:
            if not (photo.content_type and photo.content_type.startswith("image/")):
                raise HTTPException(status_code=400, detail="Only image files allowed for photo")

            try:
                old_image_url = product.get("image_url")
                if old_image_url:
                    old_filename = os.path.basename(old_image_url)
                    old_path = os.path.join(UPLOAD_DIR, old_filename)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception:
                            pass

            except Exception:
                pass

            # save new image
            ext = os.path.splitext(photo.filename)[1]
            unique_filename = f"{uuid4().hex}{ext}"
            image_path = os.path.join(UPLOAD_DIR, unique_filename)

            content = await photo.read()
            # ensure upload dir exists
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            with open(image_path, "wb") as f:
                f.write(content)
                
            try:
                image_url = request.url_for("uploads", path=unique_filename)
            except Exception:
                image_url = f"/uploads/{unique_filename}"

            update_fields["image_url"] = str(image_url)

        # if price or discount changed (or both), recalc final_price
        # Use updated values if present, otherwise fall back to existing product values
        new_price = update_fields.get("price", product.get("price", 0.0))
        # parse discount value: stored as "10%" in DB
        if "discount" in update_fields:
            # update_fields["discount"] is like "10%"
            try:
                disc_val = float(str(update_fields["discount"]).rstrip("%"))
            except Exception:
                disc_val = 0.0
        else:
            # get existing discount string like "10%" => parse number
            try:
                disc_val = float(str(product.get("discount", "0")).rstrip("%"))
            except Exception:
                disc_val = 0.0

        try:
            final_price = float(new_price) - ((float(new_price) * float(disc_val)) / 100.0)
        except Exception:
            final_price = float(new_price)

        update_fields["final_price"] = final_price

        if update_fields:
            await db.product.update_one({"_id": ObjectId(product_id)}, {"$set": update_fields})

        updated = await db.product.find_one({"_id": ObjectId(product_id)})

        return {
            "msg": "Product updated successfully",
            "product": {
                "id": str(updated["_id"]),
                "name": updated.get("name"),
                "price": updated.get("price"),
                "discount": updated.get("discount"),
                "stock": updated.get("stock"),
                "final_price": updated.get("final_price"),
                "description": updated.get("description"),
                "category": updated.get("category"),
                "image_url": updated.get("image_url")
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/product/delete/{product_id}/")
async def delete_product(product_id: str, current_user=Depends(get_current_user)):
    try:
        seller = await chk_seller(current_user)

        product = await db.product.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if str(product.get("seller")) != str(seller["_id"]):
            raise HTTPException(status_code=403, detail="You are not the owner of this product")

        # Delete image from uploads folder
        image_url = product.get("image_url")
        if image_url:
            filename = os.path.basename(image_url)
            path = os.path.join(UPLOAD_DIR, filename)

            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass

        await db.product.delete_one({"_id": ObjectId(product_id)})

        return {"msg": "Product deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
