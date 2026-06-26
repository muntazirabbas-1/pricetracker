

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


EMAIL_SENDER   = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_HOST     = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT     = int(os.environ.get("EMAIL_PORT", 587))


def _send_email(to_address: str, subject: str, html_body: str) -> dict:
    """
    Low-level send. Returns {"success": True} or {"success": False, "error": "..."}.
    """
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return {"success": False, "error": "Email credentials not configured. Set EMAIL_SENDER and EMAIL_PASSWORD environment variables."}

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"PriceTrack Pro <{EMAIL_SENDER}>"
        msg["To"]      = to_address
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_address, msg.as_string())

        return {"success": True}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "error": "Authentication failed. Check EMAIL_SENDER and EMAIL_PASSWORD."}
    except smtplib.SMTPException as e:
        return {"success": False, "error": f"SMTP error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _email_template(title: str, preheader: str, body_html: str) -> str:
    """Shared branded HTML email wrapper."""
    year = datetime.now().year
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f4f3ef;font-family:'Helvetica Neue',Arial,sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;">{preheader}</div>
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f3ef;padding:32px 16px;">
  <tr><td align="center">
    <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">

      <!-- Header -->
      <tr><td style="background:#1a7a5e;border-radius:12px 12px 0 0;padding:24px 32px;text-align:center;">
        <div style="display:inline-flex;align-items:center;gap:10px;">
          <span style="font-size:24px;">📈</span>
          <span style="font-family:Georgia,serif;font-size:20px;font-weight:700;color:#ffffff;letter-spacing:-0.3px;">PriceTrack Pro</span>
        </div>
      </td></tr>

      <!-- Body -->
      <tr><td style="background:#ffffff;padding:32px;border-left:1px solid #e8e6df;border-right:1px solid #e8e6df;">
        {body_html}
      </td></tr>

      <!-- Footer -->
      <tr><td style="background:#f8f7f3;border:1px solid #e8e6df;border-top:none;border-radius:0 0 12px 12px;padding:20px 32px;text-align:center;">
        <p style="font-size:12px;color:#9b9890;margin:0 0 6px;">
          You're receiving this because you track products on PriceTrack Pro.
        </p>
        <p style="font-size:12px;color:#9b9890;margin:0;">© {year} PriceTrack Pro. All rights reserved.</p>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""


def send_price_drop_alert(to_email: str, user_name: str, product_name: str,
                           platform: str, current_price: float, target_price: float,
                           base_price: float, deal_score: int, recommendation: str) -> dict:
    """Send a price-drop-to-target alert email."""
    saved    = base_price - current_price
    drop_pct = round(((base_price - current_price) / base_price) * 100, 1)

    rec_map = {
        "buy":      ("🔥 Buy Now",  "#1a7a5e"),
        "buy_soon": ("⚡ Buy Soon", "#c97a1a"),
        "wait":     ("⏳ Wait",     "#c0392b"),
        "neutral":  ("📊 Monitor",  "#6b6860"),
    }
    rec_label, rec_color = rec_map.get(recommendation, ("📊 Monitor", "#6b6860"))

    score_color = "#1a7a5e" if deal_score >= 70 else ("#c97a1a" if deal_score >= 40 else "#c0392b")

    body = f"""
      <h1 style="font-size:24px;font-weight:700;color:#1a1916;margin:0 0 6px;">🎯 Target Price Reached!</h1>
      <p style="font-size:15px;color:#6b6860;margin:0 0 28px;">Great news, {user_name}! A product you're tracking just hit your target price.</p>

      <!-- Product card -->
      <div style="background:#f8f7f3;border:1px solid #e8e6df;border-radius:10px;padding:24px;margin-bottom:24px;">
        <div style="font-size:18px;font-weight:700;color:#1a1916;margin-bottom:16px;line-height:1.3;">{product_name}</div>
        <div style="display:flex;flex-wrap:wrap;gap:12px;margin-bottom:16px;">
          <div style="background:#ffffff;border:1px solid #e8e6df;border-radius:8px;padding:12px 16px;flex:1;min-width:110px;text-align:center;">
            <div style="font-size:11px;color:#9b9890;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Current Price</div>
            <div style="font-size:20px;font-weight:700;color:#1a7a5e;">PKR {int(current_price):,}</div>
          </div>
          <div style="background:#ffffff;border:1px solid #e8e6df;border-radius:8px;padding:12px 16px;flex:1;min-width:110px;text-align:center;">
            <div style="font-size:11px;color:#9b9890;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Your Target</div>
            <div style="font-size:20px;font-weight:700;color:#1a5fa8;">PKR {int(target_price):,}</div>
          </div>
          <div style="background:#ffffff;border:1px solid #e8e6df;border-radius:8px;padding:12px 16px;flex:1;min-width:110px;text-align:center;">
            <div style="font-size:11px;color:#9b9890;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">You Save</div>
            <div style="font-size:20px;font-weight:700;color:#c97a1a;">PKR {int(saved):,}</div>
          </div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <span style="background:#e8f5f0;color:#0f5240;font-size:12px;font-weight:600;padding:4px 12px;border-radius:20px;">↓ {drop_pct}% from original</span>
          <span style="background:{rec_color}18;color:{rec_color};font-size:12px;font-weight:600;padding:4px 12px;border-radius:20px;">{rec_label}</span>
          <span style="background:{score_color}18;color:{score_color};font-size:12px;font-weight:600;padding:4px 12px;border-radius:20px;">Deal Score: {deal_score}/100</span>
          <span style="background:#f4f3ef;color:#6b6860;font-size:12px;padding:4px 12px;border-radius:20px;">📦 {platform}</span>
        </div>
      </div>

      <p style="font-size:14px;color:#6b6860;margin:0 0 24px;line-height:1.7;">
        Our AI has analyzed the price history and rates this as a <strong style="color:{rec_color};">{rec_label}</strong> opportunity.
        Prices can change quickly — act fast if you want to grab this deal!
      </p>

      <div style="text-align:center;">
        <a href="http://localhost:5000/watchlist" style="display:inline-block;background:#1a7a5e;color:#ffffff;font-size:14px;font-weight:600;padding:13px 32px;border-radius:8px;text-decoration:none;">View in Dashboard →</a>
      </div>
    """

    html    = _email_template(f"Target Price Reached — {product_name}", f"{product_name} just hit PKR {int(current_price):,}!", body)
    subject = f"🎯 Target Hit! {product_name} is now PKR {int(current_price):,}"
    return _send_email(to_email, subject, html)


def send_price_drop_notification(to_email: str, user_name: str, product_name: str,
                                  platform: str, current_price: float, drop_pct: float,
                                  target_price: float, deal_score: int) -> dict:
    """Send a significant price drop notification (even if target not yet hit)."""
    gap     = target_price - current_price
    gap_msg = f"Only PKR {int(abs(gap)):,} away from your target!" if gap > 0 else "Already below your target!"
    score_color = "#1a7a5e" if deal_score >= 70 else ("#c97a1a" if deal_score >= 40 else "#c0392b")

    body = f"""
      <h1 style="font-size:24px;font-weight:700;color:#1a1916;margin:0 0 6px;">📉 Significant Price Drop!</h1>
      <p style="font-size:15px;color:#6b6860;margin:0 0 28px;">Hey {user_name}, prices are falling on a product you're watching.</p>

      <div style="background:#f8f7f3;border:1px solid #e8e6df;border-radius:10px;padding:24px;margin-bottom:24px;">
        <div style="font-size:17px;font-weight:700;color:#1a1916;margin-bottom:16px;">{product_name}</div>
        <div style="display:flex;flex-wrap:wrap;gap:12px;margin-bottom:14px;">
          <div style="background:#ffffff;border:1px solid #e8e6df;border-radius:8px;padding:12px 16px;flex:1;min-width:120px;text-align:center;">
            <div style="font-size:11px;color:#9b9890;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Current Price</div>
            <div style="font-size:20px;font-weight:700;color:#1a7a5e;">PKR {int(current_price):,}</div>
          </div>
          <div style="background:#ffffff;border:1px solid #e8e6df;border-radius:8px;padding:12px 16px;flex:1;min-width:120px;text-align:center;">
            <div style="font-size:11px;color:#9b9890;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Price Drop</div>
            <div style="font-size:20px;font-weight:700;color:#1a7a5e;">↓ {drop_pct:.1f}%</div>
          </div>
          <div style="background:#ffffff;border:1px solid #e8e6df;border-radius:8px;padding:12px 16px;flex:1;min-width:120px;text-align:center;">
            <div style="font-size:11px;color:#9b9890;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Deal Score</div>
            <div style="font-size:20px;font-weight:700;color:{score_color};">{deal_score}</div>
          </div>
        </div>
        <p style="font-size:13px;color:#1a7a5e;font-weight:600;margin:0;">{gap_msg}</p>
      </div>

      <div style="text-align:center;">
        <a href="http://localhost:5000/watchlist" style="display:inline-block;background:#1a7a5e;color:#ffffff;font-size:14px;font-weight:600;padding:13px 32px;border-radius:8px;text-decoration:none;">View in Dashboard →</a>
      </div>
    """

    html    = _email_template(f"Price Drop — {product_name}", f"{product_name} dropped {drop_pct:.1f}%", body)
    subject = f"📉 Price Drop Alert: {product_name} dropped {drop_pct:.1f}%"
    return _send_email(to_email, subject, html)


def send_welcome_email(to_email: str, user_name: str) -> dict:
    """Send a welcome email after registration."""
    body = f"""
      <h1 style="font-size:26px;font-weight:700;color:#1a1916;margin:0 0 8px;">Welcome, {user_name}! 👋</h1>
      <p style="font-size:15px;color:#6b6860;margin:0 0 24px;line-height:1.7;">
        Your PriceTrack Pro account is ready. Start tracking products and let our AI alert you when prices drop.
      </p>
      <div style="background:#e8f5f0;border-radius:10px;padding:20px 24px;margin-bottom:24px;">
        <div style="font-size:14px;font-weight:600;color:#0f5240;margin-bottom:12px;">✨ What you can do:</div>
        <ul style="margin:0;padding-left:20px;color:#1a7a5e;font-size:14px;line-height:2;">
          <li>Track unlimited products across Daraz, Amazon, and more</li>
          <li>Get AI-powered deal scores and buy/wait signals</li>
          <li>Receive email alerts when prices hit your target</li>
          <li>View 30-day price history charts</li>
        </ul>
      </div>
      <div style="text-align:center;">
        <a href="http://localhost:5000/dashboard" style="display:inline-block;background:#1a7a5e;color:#ffffff;font-size:14px;font-weight:600;padding:13px 32px;border-radius:8px;text-decoration:none;">Go to Dashboard →</a>
      </div>
    """
    html    = _email_template("Welcome to PriceTrack Pro", "Your price tracking journey starts now!", body)
    subject = "🎉 Welcome to PriceTrack Pro!"
    return _send_email(to_email, subject, html)


def send_test_email(to_email: str) -> dict:
    """Send a test email to verify SMTP config works."""
    body = """
      <h1 style="font-size:22px;font-weight:700;color:#1a1916;margin:0 0 12px;">✅ Email Setup Confirmed</h1>
      <p style="font-size:15px;color:#6b6860;line-height:1.7;margin:0 0 20px;">
        Your SMTP configuration is working correctly. PriceTrack Pro will now send you
        email alerts whenever a tracked product hits your target price.
      </p>
      <div style="background:#e8f5f0;border-radius:8px;padding:16px 20px;">
        <p style="font-size:13px;color:#0f5240;margin:0;font-weight:600;">You'll receive alerts for:</p>
        <ul style="color:#1a7a5e;font-size:13px;margin:8px 0 0;padding-left:18px;line-height:1.9;">
          <li>Target price reached</li>
          <li>Significant price drops (&gt;5%)</li>
          <li>Price surge warnings</li>
        </ul>
      </div>
    """
    html    = _email_template("Test Email — PriceTrack Pro", "Email notifications are working!", body)
    subject = "✅ PriceTrack Pro — Email Test Successful"
    return _send_email(to_email, subject, html)
