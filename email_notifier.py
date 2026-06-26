

import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_EMAIL    = os.environ.get("SMTP_EMAIL", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")


def _build_html(user_name, product):
    name      = product["name"]
    current   = f"PKR {int(product['current_price']):,}"
    target    = f"PKR {int(product['target_price']):,}"
    base      = f"PKR {int(product['base_price']):,}"
    saved     = f"PKR {int(product['base_price'] - product['current_price']):,}"
    platform  = product.get("platform", "")
    drop_pct  = abs(product.get("price_change", 0))
    sent_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    rec       = product.get("recommendation", "neutral")
    rec_map   = {"buy": "Buy Now", "buy_soon": "Buy Soon", "wait": "Wait", "neutral": "Monitor"}
    rec_label = rec_map.get(rec, "Monitor")

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Price Drop Alert</title></head>
<body style="margin:0;padding:0;background:#f4f3ef;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f3ef;padding:32px 0;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">

<tr><td style="background:#1a7a5e;border-radius:12px 12px 0 0;padding:28px 32px;text-align:center;">
  <div style="font-size:24px;font-weight:700;color:#fff;">&#128201; PriceTrack Pro</div>
  <p style="margin:6px 0 0;color:#a8e6d0;font-size:13px;">Price Drop Alert</p>
</td></tr>

<tr><td style="background:#ffffff;padding:32px;">
  <p style="margin:0 0 6px;font-size:16px;color:#1a1916;">Hi <strong>{user_name}</strong> &#128075;</p>
  <p style="margin:0 0 24px;font-size:14px;color:#6b6860;line-height:1.6;">
    A product on your watchlist has <strong style="color:#1a7a5e;">dropped to your target price</strong>!
  </p>

  <div style="background:#f8f7f3;border:1px solid #e8e6df;border-radius:10px;padding:20px;margin-bottom:24px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:600;text-transform:uppercase;color:#9b9890;">{platform}</p>
    <h2 style="margin:0 0 16px;font-size:18px;font-weight:700;color:#1a1916;">{name}</h2>
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="text-align:center;padding:12px;background:#e8f5f0;border-radius:8px;">
          <div style="font-size:11px;color:#0f5240;font-weight:600;text-transform:uppercase;margin-bottom:4px;">Current Price</div>
          <div style="font-size:24px;font-weight:700;color:#0f5240;">{current}</div>
        </td>
        <td width="14"></td>
        <td style="text-align:center;padding:12px;background:#f8f7f3;border:1px solid #e8e6df;border-radius:8px;">
          <div style="font-size:11px;color:#6b6860;font-weight:600;text-transform:uppercase;margin-bottom:4px;">Your Target</div>
          <div style="font-size:22px;font-weight:700;color:#1a1916;">{target}</div>
        </td>
      </tr>
    </table>
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:12px;">
      <tr>
        <td style="text-align:center;padding:10px;background:#f8f7f3;border:1px solid #e8e6df;border-radius:8px;">
          <div style="font-size:11px;color:#6b6860;margin-bottom:2px;">Original</div>
          <div style="font-size:13px;color:#9b9890;text-decoration:line-through;">{base}</div>
        </td>
        <td width="10"></td>
        <td style="text-align:center;padding:10px;background:#e8f5f0;border:1px solid #a8e6d0;border-radius:8px;">
          <div style="font-size:11px;color:#0f5240;margin-bottom:2px;">You Save</div>
          <div style="font-size:13px;font-weight:700;color:#0f5240;">{saved}</div>
        </td>
        <td width="10"></td>
        <td style="text-align:center;padding:10px;background:#fef3e2;border:1px solid #f5d69a;border-radius:8px;">
          <div style="font-size:11px;color:#7a4a0a;margin-bottom:2px;">AI Signal</div>
          <div style="font-size:13px;font-weight:700;color:#7a4a0a;">{rec_label}</div>
        </td>
      </tr>
    </table>
  </div>

  <div style="background:#e8f5f0;border-left:3px solid #1a7a5e;border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:24px;">
    <p style="margin:0;font-size:13px;color:#0f5240;">
      <strong>&#8595; {drop_pct:.1f}% drop detected</strong> — this is among the lowest prices tracked in the last 30 days.
    </p>
  </div>

  <div style="text-align:center;margin-bottom:24px;">
    <a href="http://localhost:5000/watchlist"
       style="display:inline-block;background:#1a7a5e;color:#fff;font-size:14px;font-weight:600;
              padding:13px 32px;border-radius:8px;text-decoration:none;">
      View Watchlist &#8594;
    </a>
  </div>

  <p style="margin:0;font-size:12px;color:#9b9890;text-align:center;">
    Sent by PriceTrack Pro on {sent_date}
  </p>
</td></tr>

<tr><td style="background:#f8f7f3;border:1px solid #e8e6df;border-top:none;border-radius:0 0 12px 12px;padding:14px 32px;text-align:center;">
  <p style="margin:0;font-size:11px;color:#9b9890;">You received this because you set a target price for this product.</p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def send_price_drop_email(to_email, user_name, product):
    """Send HTML email alert. Returns {"success": True/False, ...}"""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return {"success": False, "error": "SMTP not configured. Set SMTP_EMAIL and SMTP_PASSWORD env vars."}
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Price Drop Alert: {product['name']} hit your target!"
        msg["From"]    = f"PriceTrack Pro <{SMTP_EMAIL}>"
        msg["To"]      = to_email

        plain = (
            f"Hi {user_name},\n\n"
            f"{product['name']} hit your target price!\n\n"
            f"Current : PKR {int(product['current_price']):,}\n"
            f"Target  : PKR {int(product['target_price']):,}\n"
            f"Savings : PKR {int(product['base_price'] - product['current_price']):,}\n\n"
            f"http://localhost:5000/watchlist\n\n-- PriceTrack Pro"
        )
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(_build_html(user_name, product), "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_EMAIL, SMTP_PASSWORD)
            s.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        return {"success": True}

    except smtplib.SMTPAuthenticationError:
        return {"success": False, "error": "SMTP auth failed. Check your Gmail App Password."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_and_notify(users_col, products_col):
    """
    Scan all products. Send email if:
      current_price <= target_price AND email_notified != True
    Marks email_notified=True to avoid duplicate emails.
    Returns list of notification results.
    """
    sent = []
    for product in products_col.find({"email_notified": {"$ne": True}}):
        if product.get("current_price", 9e9) <= product.get("target_price", 0):
            owner    = product.get("owner")
            user_doc = users_col.find_one({"username": owner})
            if not user_doc or not user_doc.get("email"):
                continue
            result = send_price_drop_email(
                to_email  = user_doc["email"],
                user_name = user_doc.get("name", owner),
                product   = product,
            )
            products_col.update_one(
                {"_id": product["_id"]},
                {"$set": {
                    "email_notified": True,
                    "email_sent_at":  datetime.now(),
                    "email_result":   result
                }}
            )
            sent.append({"product": product["name"], "to": user_doc["email"], "result": result})
    return sent
