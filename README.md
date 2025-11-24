# 🛒 E-Commerce Backend (FastAPI + MongoDB)
### Multi-Vendor | JWT Auth | Cart System | Multi-Seller Orders | Email Notifications

---

## 📌 Overview

This project is a **production-ready Multi-Vendor E-Commerce Backend** built using **FastAPI**, **MongoDB**, **JWT Authentication**, and **FastAPI-Mail**.  
It implements a complete marketplace workflow — user registration, seller onboarding, product management, cart system, multi-seller checkout, stock locking, and email notifications.

The backend is **clean, scalable, modular**, and fully ready to integrate with mobile or web frontends.

---

## 🚀 Key Features

### 🔐 Authentication & Authorization
- Buyer and Seller registration  
- Login using email & password  
- JWT-based authentication  
- Secure password hashing  
- Role-based permissions  

---

### 👤 User (Buyer) Module
- Create/update user profile  
- Manage delivery addresses  
- Add/update/delete items in cart  
- View order history  
- Receive order confirmation emails  

---

### 🛍️ Seller Module
- Seller registration & verification  
- Seller login with JWT token  
- Add or update products  
- Track seller-wise orders  
- Email notification for every new order  

---

### 📦 Product Management
- Add new products with images, stock & pricing  
- Seller-specific product ownership  
- Stock validation on checkout  
- Offers & discounted pricing  
- Snapshot storage during order creation  

---

### 🛒 Cart System
- Add items to cart  
- Update quantity  
- Remove items  
- Auto-calculate discounted price  
- Buyer-only access & isolation  

---

### 🧾 Order System (Multi-Vendor Architecture)
Your backend supports a **true marketplace** checkout flow.

#### ✔ Core Highlights
- Splits a single checkout into **multiple orders (1 per seller)**  
- Validates stock for each product  
- Uses **atomic stock reduction**  
- Performs full rollback on failure  
- Saves item snapshot (title, price, quantity)  
- Saves address snapshot  
- Stores seller ID per order  

#### Status Flow  
`pending → accepted → packed → shipped → delivered`

---

### ✉️ Email Notifications (FastAPI-Mail)
Powered by your configuration:

```python
MAIL = os.getenv("MAIL")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

conf = ConnectionConfig(
    MAIL_USERNAME=MAIL,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)