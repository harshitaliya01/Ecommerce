from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form,Request, Query
from db.db import db,supabase
from utils.security import get_current_user
from utils.check import chk_seller
from uuid import uuid4

router = APIRouter()

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
        ext = photo.filename.split(".")[-1].lower()
        file_path = f"products/{uuid4()}.{ext}" 
        file_bytes = await photo.read()
    # 4. upload to Supabase Storage
        try:
            upload_res = supabase.storage.from_("product-image").upload(
                file_path,
                file_bytes,
                {"content-type": photo.content_type},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to upload image1")
        if isinstance(upload_res, dict) and upload_res.get("error"):
            raise HTTPException(status_code=500, detail="Failed to upload image2")
      
        image_url = supabase.storage.from_("product-image").get_public_url(file_path)
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
async def list_product(request:Request,current_user = Depends(get_current_user),page: int = Query(1, ge=1),size: int = Query(10, ge=1, le=50)):
    try:
        seller = await chk_seller(current_user)

        products = await db.product.find(
        {"seller": seller["_id"]}
        ).sort("created_at", -1).to_list(length=None)
        start = (page - 1) * size
        end = start + size
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

        data = results[start:end]
        return {
        "page": page,
        "size": size,
        "total": len(results),
        "items": data,
        }

    except Exception as e:
        return str(e)
    

@router.get("/all/products/")
async def list_product(request:Request,page: int = Query(1, ge=1),size: int = Query(10, ge=1, le=50)):
    try:
        products = await db.product.find().to_list()
        start = (page - 1) * size
        end = start + size
        PRODUCTS = []
        for p in products:
            PRODUCTS.append({
            "id": str(p["_id"]),
            "name": p.get("name"),
            "price": p.get("price"),
            "description": p.get("description"),
            "category":p.get("category"),
            "image_url": p.get("image_url"),
            })
        data = PRODUCTS[start:end]
        return {
        "page": page,
        "size": size,
        "total": len(PRODUCTS),
        "items": data,
        }

    except Exception as e:
        return str(e)
    
    
