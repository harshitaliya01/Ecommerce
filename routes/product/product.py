import os
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form,Request
from db.db import db
from utils.security import get_current_user
from utils.check import chk_seller

router = APIRouter()

import os, re
UPLOAD_DIR = "uploads"
for fn in os.listdir(UPLOAD_DIR):
    if fn.endswith('"}') or fn.endswith("'}"):
        clean = re.sub(r'["\'}]+$', '', fn)
        os.rename(os.path.join(UPLOAD_DIR, fn), os.path.join(UPLOAD_DIR, clean))
        print("Renamed", fn, "->", clean)

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/product/add/")
async def register_product(request:Request,
    name: str = Form(...),
    price: float = Form(...),
    discount: float = Form(...),
    stock: int = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    photo: UploadFile = File(...),
    current_user = Depends(get_current_user)

):
    try:
        seller = await chk_seller(current_user)

        chk_category = await db.category.find_one({"category":category})
        if not chk_category:
            raise HTTPException(status_code=400, detail="Add Avilable Category")
        # Validate image
        if not photo.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files allowed")

        # Extract extension (jpg/png/webp etc.)
        ext = os.path.splitext(photo.filename)[1]

        # Create unique filename
        unique_filename = f"{uuid4().hex}{ext}"

        # Full path
        image_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Save file
        content = await photo.read()
        with open(image_path, "wb") as f:
            f.write(content)
        # Save product in MongoDB

        image_filename = unique_filename

        if image_filename:
            try:
                image_url = request.url_for("uploads", path=image_filename)
              
            except:
                image_url = f"/uploads/{image_filename}"
              
        else:
            image_url = None
        product_doc = {
            "seller": seller["_id"],
            "name": name,
            "price": price,
            "discount":f"{discount}%",
            "final_price":price-((price*discount)/100),
            "stock":stock,
            "description": description,
            "category": category,
            "image_url": str(image_url)
        }

        res = await db.product.insert_one(product_doc)
        created = await db.product.find_one({"_id": res.inserted_id})

        return {
            "msg": "Product Add Success",
            "product": {
                "id": str(created["_id"]),
                "name": created["name"],
                "price": created["price"],
                "discount":created["discount"],
                "stock":created["stock"],
                "final_price":created["final_price"],
                "description": created["description"],
                "category": created["category"],
                "image_url": created["image_url"]
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/")
async def list_product(request:Request,current_user = Depends(get_current_user)):
    try:
        seller = await chk_seller(current_user)

        products = await db.product.find(
        {"seller": seller["_id"]}
        ).sort("created_at", -1).to_list(length=None)

        results = []
        for p in products:
            results.append({
            "id": str(p["_id"]),
            "name": p.get("name"),
            "price": p.get("price"),
            "description": p.get("description"),
            "category":p.get("category"),
            "image_url": p.get("image_url"),
            })

        return {"products": results}

    except Exception as e:
        return str(e)
    