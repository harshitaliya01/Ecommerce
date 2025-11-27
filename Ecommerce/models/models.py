from pydantic import BaseModel,EmailStr, Field


class Admin(BaseModel):
    name:str
    email:EmailStr
    password:str

class AdminLogin(BaseModel):
    email:EmailStr
    password:str

class User(BaseModel):
    name:str
    email:EmailStr
    password:str

class UserLogin(BaseModel):
    email:EmailStr
    password:str

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str

class UserAddress(BaseModel):
    mobile_no:str
    address:str

class Seller(BaseModel):
    business_name:str
    email:EmailStr
    password:str
    gst_no:str

class SellerLogin(BaseModel):
    email:EmailStr
    password:str

class SellerVerifyOTP(BaseModel):
    email: EmailStr
    otp: str

class Product(BaseModel):
    name:str
    price:int
    description:str
    discount:int

class Cart(BaseModel):
    quantity:int

class Category(BaseModel):
    category : str


    

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordWithOTP(BaseModel):
    email: EmailStr
    otp: str
    new_password: str