from fastapi import FastAPI
from routes import admin
from routes.order import cart,order,wishlist
from routes.seller import seller, seller_order,forgot_pwd_seller
from routes.user import user_order,forgot_pwd_user,address,user
from routes.product import category,product_up_del,product
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
  CORSMiddleware,
#  allow_origins=["http://localhost:5500","http://127.0.0.1:5500","http://localhost:3000"], # or ["*"] for quick test
  allow_origins=["*"], # or ["*"] for quick test
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(user.router, tags=["User"])
app.include_router(forgot_pwd_user.router, tags=["User"])
app.include_router(address.router, tags=["User-Address"])
app.include_router(user_order.router, tags=["User-Order"])

app.include_router(cart.router, tags=["Cart"])
app.include_router(wishlist.router, tags=["Wishlist"])

app.include_router(order.router, tags=["Create-Order"])

app.include_router(seller.router, tags=["Seller"])
app.include_router(forgot_pwd_seller.router, tags=["Seller"])
app.include_router(product.router, tags=["Product"])
app.include_router(product_up_del.router, tags=["Crud-Product"])
app.include_router(seller_order.router, tags=["Seller-Order"])

app.include_router(admin.router, tags=["Admin"])
app.include_router(category.router, tags=["Category"])


@app.get("/",)
def home():
    return {"message": "Hospital API Running"}