## 🛠 Admin APIs (`routes/admin.py`)

* **POST `/admin/register/{admin_secret}/`** – Register a new admin using a secret admin key.
* **POST `/admin/login/`** – Admin login and get JWT access token.
* * **POST `/user/verify-otp/`** – Verify OTP for user registration.
* **POST `/user/resend/otp/`** – Resend registration OTP to user.
* * **POST `/user/forgot-password/request/`** – Request password reset (send OTP/link to user).
* **POST `/user/forgot-password/verify/`** – Verify OTP and reset user password.

---

## 👤 User Auth & Profile APIs (`routes/user/user.py`)

* **POST `/user/register/`** – Register a normal user/customer.
* **POST `/user/verify-otp/`** – Verify OTP for user registration.
* **POST `/user/resend/otp/`** – Resend registration OTP to user.
* **POST `/user/login/`** – User login and get JWT access token.

---

## 👤 User Forgot Password APIs (`routes/user/forgot_pwd_user.py`)

* **POST `/user/forgot-password/request/`** – Request password reset (send OTP/link to user).
* **POST `/user/forgot-password/verify/`** – Verify OTP and reset user password.

---

## 📍 User Address APIs (`routes/user/address.py`)

* **POST `/add/address/`** – Add a new delivery address for the logged-in user.
* **GET `/show/address/`** – Get all saved addresses of the logged-in user.
* **PUT `/update/address/{address_id}`** – Update an existing address by its ID.

---

## 📦 User Order APIs (`routes/user/user_order.py`)

* **GET `/my/orders/`** – Get all orders of the logged-in user.
* **PATCH `/order/{order_id}/cancel`** – Request cancellation of a specific order.
* **PATCH `/order/{order_id}/return`** – Request return of a specific order.

---

## 🧾 Seller Auth APIs (`routes/seller/seller.py`)

* **POST `/seller/register/`** – Register a new seller account.
* **POST `/seller/verify-otp/`** – Verify OTP for seller registration.
* **POST `/seller/resend/otp/`** – Resend seller registration OTP.
* **POST `/seller/login/`** – Seller login and get JWT access token.

---

## 🧾 Seller Forgot Password APIs (`routes/seller/forgot_pwd_seller.py`)

* **POST `/seller/forgot-password/request/`** – Request password reset for seller (send OTP/link).
* **POST `/seller/forgot-password/verify/`** – Verify OTP and reset seller password.

---

## 🧾 Seller Order APIs (`routes/seller/seller_order.py`)

* **GET `/seller/orders/`** – Get all orders related to the logged-in seller’s products.
* **PATCH `/seller/order/{order_id}/shipped`** – Mark a specific order as *shipped* by seller.
* **PATCH `/seller/order/{order_id}/completed`** – Mark a specific order as *completed/delivered*.

---

## 🛍 Product APIs (`routes/product/product.py`, `product_up_del.py`)

* **POST `/product/add/`** – Seller adds a new product with details and image (Supabase upload).
* **GET `/products/`** – Seller gets a list of their own products.
* **PUT `/product/update/{product_id}/`** – Seller updates product details and/or image.
* **DELETE `/product/delete/{product_id}/`** – Seller deletes a product and its image.

---

## 🗂 Category APIs (`routes/product/category.py`)

* **POST `/add/category/`** – Admin creates a new product category.
* **GET `/categories/`** – Get all available product categories.
* **PUT `/update/category/{category_id}/`** – Admin updates a specific category.
* **DELETE `/delete/category/{category_id}/`** – Admin deletes a specific category.

---

## 🛒 Cart APIs (`routes/order/cart.py`)

* **POST `/add/item/{product_id}/`** – Add a product to the logged-in user’s cart (or increase qty).
* **DELETE `/remove/item/{product_id}/`** – Remove a specific product from the user’s cart.
* **DELETE `/cart/delete/`** – Clear the entire cart of the user.
* **GET `/cart/`** – Get all cart items and totals for the user.
* **PATCH `/cart/update/{product_id}/`** – Update quantity of a specific product in the cart.

---

## ❤️ Wishlist APIs (`routes/order/wishlist.py`)

* **POST `/add/item/wish_list/{product_id}/`** – Add a product to the user’s wishlist.
* **GET `/get/wishlist/`** – Get all wishlist items of the logged-in user.
* **DELETE `/remove/item/wish_list/{product_id}/`** – Remove a specific product from the wishlist.

---

## 📦 Order Creation API (`routes/order/order.py`)

* **POST `/create/order/`** – Create order(s) from the current user’s cart, split by seller, and save to DB.
