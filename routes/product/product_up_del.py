import os
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form,Request
from db.db import db, supabase, SUPABASE_URL
from utils.security import get_current_user
from utils.check import chk_seller
from typing import Optional
from bson import ObjectId

router = APIRouter()


def _get_file_path_from_url(image_url: str) -> Optional[str]:
    """
    Extracts the file path used in Supabase Storage from the public URL.
    Works when URL looks like:
    https://<project>.supabase.co/storage/v1/object/public/<bucket>/products/abc.png
    """
    # Standard public URL prefix
    prefix = f"{SUPABASE_URL}/storage/v1/object/public/product-image/"
    if image_url.startswith(prefix):
        return image_url[len(prefix):]
    # If for some reason you saved only path, just return it
    if not image_url.startswith("http"):
        return image_url
    return None


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

            # 1. delete old image from Supabase (if exists)
            old_image_url = product.get("image_url")
            if old_image_url:
                await _delete_image_from_supabase(old_image_url)

            # 2. upload new image
            ext = photo.filename.split(".")[-1].lower()
            file_path = f"products/{uuid4()}.{ext}"
            file_bytes = await photo.read()

            try:
                upload_res = supabase.storage.from_("product-image").upload(
                    file_path,
                    file_bytes,
                    {"content-type": photo.content_type},
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail="Failed to upload image")

            if isinstance(upload_res, dict) and upload_res.get("error"):
                raise HTTPException(status_code=500, detail="Failed to upload image")

            image_url = supabase.storage.from_("product-image").get_public_url(file_path)
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



async def _delete_image_from_supabase(image_url: str):
    """Delete a single image from Supabase Storage if possible."""
    if not image_url:
        return

    file_path = _get_file_path_from_url(image_url)
    if not file_path:
        return  # can't parse path, silently ignore

    try:
        res = supabase.storage.from_("product-image").remove([file_path])
        # Optional: check res for error depending on supabase-py version
    except Exception as e:
        print("Supabase delete error:", e)


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
            await _delete_image_from_supabase(image_url)

        # 2. delete product from MongoDB
        await db.product.delete_one({"_id": ObjectId(product_id)})

        return {"msg": "Product deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
