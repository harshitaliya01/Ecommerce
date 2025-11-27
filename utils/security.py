from passlib.context import CryptContext
from typing import Optional
from jose import jwt
# pip install python-jose[cryptography]
from datetime import timedelta,datetime
import os
from db.db import db
from fastapi import Depends, HTTPException
from fastapi.security import  HTTPBearer, HTTPAuthorizationCredentials

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
auth_scheme = HTTPBearer()

def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password Cannot Be Empty Or None")
    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    password = password[:72]
    return pwd_context.hash(password)

def verify_password(plain_password,hashed_password):
    return pwd_context.verify(plain_password,hashed_password)

def create_access_token(data:dict,expires_delta:Optional[timedelta] = None):
    try:
        to_encode = data.copy()
        ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp":expire})
        return jwt.encode(to_encode,os.getenv("SECRET_KEY"),algorithm=os.getenv("ALGORITHM"))
    except Exception as e:
        return str(e)

def decode_access_token(token:str):
    try:
        return jwt.decode(token,os.getenv("SECRET_KEY"),algorithm=os.getenv("ALGORITHM"))
    except Exception as e:
        return None
    

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token,os.getenv("SECRET_KEY"), algorithms=os.getenv("ALGORITHM"))
        email = payload.get("email")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"email": email}