from typing import List, Dict, Any
from datetime import datetime

from bson import ObjectId
from fastapi_mail import FastMail, MessageSchema, MessageType

from db.db import db
from utils.config import conf

fm = FastMail(conf)  

# ---------- low level HTML email sender (uses your conf) ----------

async def _send_html_email(to_email: str, subject: str, html: str):
    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=html,
        subtype=MessageType.html,
    )
    await fm.send_message(message)


# ---------- email templates (HTML, mobile friendly) ----------

def _build_user_email_html(user: Dict[str, Any], orders: List[Dict[str, Any]], grand_final_total: float) -> str:
    """Create a nice mobile-friendly HTML email for the buyer."""
    user_name = user.get("name") or user.get("full_name") or "there"
    order_date = datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC")

    # Build per-order sections
    order_blocks = []
    for o in orders:
        items_html = ""
        for it in o.get("items", []):
            items_html += f"""
            <tr>
              <td style="padding: 8px 4px; font-size: 14px;">{it.get("title","")}</td>
              <td style="padding: 8px 4px; text-align:center; font-size: 14px;">{it.get("quantity",0)}</td>
              <td style="padding: 8px 4px; text-align:right; font-size: 14px;">₹{float(it.get("final_price",0)):.2f}</td>
            </tr>
            """

        order_block = f"""
        <div style="margin-bottom: 18px; border:1px solid #eeeeee; border-radius:8px; padding:12px;">
          <div style="font-size: 14px; font-weight: 600; margin-bottom: 6px;">
            Order ID: {o.get("id","")}  •  Status: {o.get("status","pending").title()}
          </div>
          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
            <thead>
              <tr>
                <th align="left" style="padding: 6px 4px; font-size: 13px; border-bottom:1px solid #f0f0f0;">Item</th>
                <th align="center" style="padding: 6px 4px; font-size: 13px; border-bottom:1px solid #f0f0f0;">Qty</th>
                <th align="right" style="padding: 6px 4px; font-size: 13px; border-bottom:1px solid #f0f0f0;">Price</th>
              </tr>
            </thead>
            <tbody>
              {items_html}
            </tbody>
          </table>
          <div style="text-align:right; margin-top:10px; font-size: 14px;">
            <div>Subtotal: <strong>₹{float(o.get("final_total",0)):.2f}</strong></div>
          </div>
        </div>
        """
        order_blocks.append(order_block)

    orders_html = "\n".join(order_blocks)

    address = None
    if orders:
        address = orders[0].get("address") or {}
    address_line = ""
    if address:
        address_line = f"""
        <div style="font-size: 13px; color:#555555; line-height:1.4; margin-top:10px;">
          <div><strong>Delivery to:</strong></div>
          <div>{address.get("address","")}</div>
          <div>📱 {address.get("mobile_no","")}</div>
        </div>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Order Confirmation</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
</head>
<body style="margin:0; padding:0; background-color:#f5f5f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f5f5; padding:16px 8px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px; background:#ffffff; border-radius:12px; overflow:hidden;">
          <!-- Header -->
          <tr>
            <td style="padding:16px 20px; background:linear-gradient(135deg,#2563eb,#1d4ed8); color:#ffffff;">
              <div style="font-size:18px; font-weight:600;">Thank you for your order, {user_name} 👋</div>
              <div style="font-size:13px; opacity:0.9; margin-top:4px;">We’ve received your order and it’s currently pending.</div>
              <div style="font-size:12px; opacity:0.8; margin-top:4px;">{order_date}</div>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:16px 20px;">
              <p style="font-size:14px; margin:0 0 10px 0;">
                We’ve created separate orders for each seller. You’ll receive updates as items are packed and shipped.
              </p>

              {address_line}

              <div style="margin-top:16px;">
                {orders_html}
              </div>

              <div style="margin-top:10px; padding:10px 12px; background:#f9fafb; border-radius:8px; font-size:14px;">
                <div style="display:flex; justify-content:space-between;">
                  <span style="font-weight:600;">Grand Total</span>
                  <span style="font-weight:700; color:#16a34a;">₹{grand_final_total:.2f}</span>
                </div>
              </div>

              <p style="font-size:12px; color:#777777; margin-top:16px;">
                If you have any questions, just reply to this email and our support team will help you out.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:12px 20px; background:#0f172a; color:#9ca3af; font-size:11px; text-align:center;">
              &copy; {datetime.utcnow().year} Your Store. All rights reserved.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    return html


def _build_seller_email_html(seller_name: str, user: Dict[str, Any], order: Dict[str, Any]) -> str:
    """Create HTML email for each seller about their order."""
    buyer_name = user.get("name") or user.get("full_name") or user.get("email") or "Customer"
    buyer_email = user.get("email", "")
    created_at = order.get("created_at") or datetime.utcnow().isoformat()
    address = order.get("address") or {}
    if isinstance(created_at, str):
        created_str = created_at
    else:
        created_str = created_at.strftime("%d %b %Y, %I:%M %p UTC")

    items_html = ""
    for it in order.get("items", []):
        items_html += f"""
        <tr>
          <td style="padding: 8px 4px; font-size: 14px;">{it.get("title","")}</td>
          <td style="padding: 8px 4px; text-align:center; font-size: 14px;">{it.get("quantity",0)}</td>
          <td style="padding: 8px 4px; text-align:right; font-size: 14px;">₹{float(it.get("final_price",0)):.2f}</td>
        </tr>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>New Order Received</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
</head>
<body style="margin:0; padding:0; background-color:#f5f5f5; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f5f5; padding:16px 8px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px; background:#ffffff; border-radius:12px; overflow:hidden;">
          <!-- Header -->
          <tr>
            <td style="padding:16px 20px; background:#0f766e; color:#ffffff;">
              <div style="font-size:18px; font-weight:600;">New order received 🚀</div>
              <div style="font-size:13px; opacity:0.9; margin-top:4px;">
                Hi {seller_name}, a new order has been placed for your products.
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:16px 20px;">
              <div style="font-size:14px; margin-bottom:10px;">
                <strong>Order ID:</strong> {order.get("id","")}<br/>
                <strong>Date:</strong> {created_str}<br/>
                <strong>Status:</strong> {order.get("status","pending").title()}
              </div>

              <div style="margin-bottom:12px; font-size:13px; color:#444;">
                <strong>Buyer details:</strong><br/>
                Name: {buyer_name}<br/>
                Email: {buyer_email}<br/>
                Phone: {address.get("mobile_no","")}<br/>
                Address: {address.get("address","")}
              </div>

              <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse; margin-top:8px;">
                <thead>
                  <tr>
                    <th align="left" style="padding: 6px 4px; font-size: 13px; border-bottom:1px solid #f0f0f0;">Item</th>
                    <th align="center" style="padding: 6px 4px; font-size: 13px; border-bottom:1px solid #f0f0f0;">Qty</th>
                    <th align="right" style="padding: 6px 4px; font-size: 13px; border-bottom:1px solid #f0f0f0;">Price</th>
                  </tr>
                </thead>
                <tbody>
                  {items_html}
                </tbody>
              </table>

              <div style="text-align:right; margin-top:10px; font-size:14px;">
                <div>Total: <strong>₹{float(order.get("final_total",0)):.2f}</strong></div>
              </div>

              <p style="font-size:12px; color:#777; margin-top:16px;">
                Please pack and dispatch the items as per your usual shipping process.
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding:12px 20px; background:#111827; color:#9ca3af; font-size:11px; text-align:center;">
              &copy; {datetime.utcnow().year} Your Store. Seller notification.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    return html


# ---------- main function to call from your order route ----------

async def send_order_emails(user: Dict[str, Any], orders: List[Dict[str, Any]], grand_final_total: float):
    """
    High-level helper:
    - Send ONE email to user with all seller-wise orders.
    - Send ONE email to each seller with only their order.
    """
    user_email = user.get("email")
    if not user_email:
        return

    # 1) Email to user
    user_html = _build_user_email_html(user, orders, grand_final_total)
    await _send_html_email(
        to_email=user_email,
        subject="Your order has been placed successfully ✅",
        html=user_html,
    )

    # 2) Emails to sellers (1 per seller)
    # orders[i]["seller"] is seller_id as string in your created_orders
    seller_ids = {o["seller"] for o in orders if o.get("seller")}
    seller_map: Dict[str, Dict[str, str]] = {}

    for sid in seller_ids:
        try:
            seller_doc = await db.seller.find_one({"_id": ObjectId(sid)})
        except Exception:
            seller_doc = None

        if seller_doc and seller_doc.get("email"):
            seller_map[str(sid)] = {
                "email": seller_doc["email"],
                "name": seller_doc.get("store_name") or seller_doc.get("name") or "Seller",
            }

    for o in orders:
        seller_key = str(o.get("seller"))
        seller_info = seller_map.get(seller_key)
        if not seller_info:
            continue

        seller_html = _build_seller_email_html(
            seller_name=seller_info["name"],
            user=user,
            order=o,
        )
        await _send_html_email(
            to_email=seller_info["email"],
            subject=f"New order received - {o.get('id','')}",
            html=seller_html,
        )
