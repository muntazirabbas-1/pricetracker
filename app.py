from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import hashlib, uuid
from datetime import datetime, timedelta
from functools import wraps
import random
from pymongo import MongoClient
from bson import ObjectId
import os
from email_notifier import send_price_drop_email, check_and_notify
from scraper import scrape_product, refresh_price
from dotenv import load_dotenv
load_dotenv()
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.secret_key = "pricetracker_secret_2024"

# ── MongoDB Connection ─────────────────────────────────────────
# Change this URI to your MongoDB Atlas string if needed:
# e.g. "mongodb+srv://username:password@cluster.mongodb.net/pricetracker"
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["pricetracker"]

users_col    = db["users"]
products_col = db["products"]

# ── Email / SMTP Config ────────────────────────────────────────
# Set these as env vars before running:
#   Windows:   set SMTP_EMAIL=you@gmail.com
#              set SMTP_PASSWORD=your-app-password
#   Mac/Linux: export SMTP_EMAIL=you@gmail.com
#              export SMTP_PASSWORD=your-app-password
# Get a Gmail App Password at: https://myaccount.google.com/apppasswords
SMTP_EMAIL    = os.environ.get("SMTP_EMAIL", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# ── Helpers ────────────────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def generate_price_history(base_price, days=30):
    history = []
    price = base_price
    for i in range(days, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        change = random.uniform(-0.04, 0.05)
        price = round(price * (1 + change), 2)
        history.append({"date": date, "price": price})
    history[-1]["price"] = base_price
    return history

def get_deal_score(history):
    if len(history) < 5:
        return 50
    prices = [h["price"] for h in history]
    current = prices[-1]
    mn, mx = min(prices), max(prices)
    if mx == mn:
        return 50
    return max(0, min(100, int(100 - ((current - mn) / (mx - mn)) * 100)))

from sklearn.linear_model import LinearRegression
import numpy as np

def get_ai_recommendation(history):
    if len(history) < 7:
        return "neutral"          # not enough data yet
    
    prices = [h["price"] for h in history]
    X = np.array(range(len(prices))).reshape(-1, 1)
    y = np.array(prices)
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict next 7 days
    future = np.array(range(len(prices), len(prices) + 7)).reshape(-1, 1)
    predicted = model.predict(future)
    
    trend = predicted[-1] - predicted[0]   # going up or down?
    current = prices[-1]
    avg = sum(prices) / len(prices)
    
    if trend < 0 and current <= avg:
        return "buy"          # price dropping + currently cheap
    elif trend > 0:
        return "wait"         # price is rising
    elif trend < 0:
        return "buy_soon"     # price dropping but not cheap yet
    else:
        return "neutral"

def serialize(doc):
    """Convert MongoDB _id ObjectId to string."""
    if doc is None:
        return None
    doc = dict(doc)
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

# ── Seed Demo Data ─────────────────────────────────────────────
def seed_data():
    if users_col.count_documents({"username": "Ali"}) == 0:
        users_col.insert_one({
            "username": "Ali",
            "password": hash_pw("Ali123"),
            "name": "WaveRider",
            "email": "Ali@pricetrack.com",
            "created_at": datetime.now()
        })

    if products_col.count_documents({"owner": "Ali"}) == 0:
        sample = [
            {"name": "Samsung Galaxy S24 Ultra", "platform": "Daraz",  "base_price": 189000, "target_price": 175000, "category": "Phones"},
            {"name": "iPhone 15 Pro Max",         "platform": "Amazon", "base_price": 299000, "target_price": 280000, "category": "Phones"},
            {"name": "Sony WH-1000XM5",           "platform": "Daraz",  "base_price": 62500,  "target_price": 55000,  "category": "Audio"},
            {"name": "MacBook Air M2",             "platform": "Apple",  "base_price": 379000, "target_price": 350000, "category": "Laptops"},
            {"name": "Logitech MX Master 3S",     "platform": "Daraz",  "base_price": 18200,  "target_price": 16000,  "category": "Accessories"},
            {"name": "iPad Pro 12.9 M2",           "platform": "Amazon", "base_price": 245000, "target_price": 220000, "category": "Tablets"},
        ]
        docs = []
        for p in sample:
            history = generate_price_history(p["base_price"])
            current = history[-1]["price"]
            prev    = history[-2]["price"] if len(history) > 1 else current
            docs.append({
                "pid":           str(uuid.uuid4())[:8],
                "name":          p["name"],
                "platform":      p["platform"],
                "url":           "#",
                "base_price":    p["base_price"],
                "current_price": current,
                "target_price":  p["target_price"],
                "category":      p["category"],
                "owner":         "Ali",
                "history":       history,
                "deal_score":    get_deal_score(history),
                "recommendation":get_ai_recommendation(history),
                "price_change":  round(((current - prev) / prev) * 100, 2),
                "created_at":    datetime.now()
            })
        products_col.insert_many(docs)

seed_data()

# ── Auth Routes ────────────────────────────────────────────────
@app.route("/")
def index():
    return redirect(url_for("dashboard") if "user" in session else url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = users_col.find_one({"username": username, "password": hash_pw(password)})
        if user:
            session["user"] = username
            session["name"] = user["name"]
            return redirect(url_for("dashboard"))
        flash("Invalid credentials. Try Ali / Ali123")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip()
        if users_col.find_one({"username": username}):
            flash("Username already taken.")
        else:
            users_col.insert_one({
                "username": username, "password": hash_pw(password),
                "name": name, "email": email, "created_at": datetime.now()
            })
            session["user"] = username
            session["name"] = name
            return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Page Routes ────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html",
                           username=session.get("name", "User"),
                           now_hour=datetime.now().hour)

@app.route("/watchlist")
@login_required
def watchlist():
    return render_template("watchlist.html", username=session.get("name", "User"))

@app.route("/analytics")
@login_required
def analytics():
    return render_template("analytics.html", username=session.get("name", "User"))

@app.route("/alerts")
@login_required
def alerts():
    return render_template("alerts.html", username=session.get("name", "User"))

@app.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    scrape_error = None
    scraped_name  = None
    scraped_price = None

    if request.method == "POST":
        url      = request.form.get("url", "").strip()
        manual_price = request.form.get("price", "").strip()

        # ── Step 1: Try to scrape price from URL ──────────────
        if url and url != "#":
            result = scrape_product(url)
            if result["price"]:
                base         = result["price"]
                scraped_name = result["name"]  # auto-fill name if scraped
            elif manual_price:
                # Scraping failed — fall back to manually entered price
                base         = float(manual_price)
                scrape_error = f"Auto-scrape failed ({result['error']}) — used your manual price instead."
            else:
                scrape_error = result["error"] or "Could not scrape price. Please enter it manually."
                return render_template("add_product.html",
                                       username=session.get("name", "User"),
                                       scrape_error=scrape_error)
        elif manual_price:
            base = float(manual_price)
        else:
            scrape_error = "Please provide a product URL or enter the price manually."
            return render_template("add_product.html",
                                   username=session.get("name", "User"),
                                   scrape_error=scrape_error)

        # ── Step 2: Use scraped name or form name ─────────────
        product_name = request.form.get("name", "").strip()
        if not product_name and scraped_name:
            product_name = scraped_name
        if not product_name:
            product_name = "Unnamed Product"

        # ── Step 3: Build history & store in MongoDB ──────────
        history = generate_price_history(base)
        current = history[-1]["price"]
        prev    = history[-2]["price"] if len(history) > 1 else current

        products_col.insert_one({
            "pid":            str(uuid.uuid4())[:8],
            "name":           product_name,
            "platform":       request.form.get("platform", "Other"),
            "url":            url or "#",
            "base_price":     base,
            "current_price":  current,
            "target_price":   float(request.form.get("target_price", round(base * 0.9, 2))),
            "category":       request.form.get("category", "Other"),
            "owner":          session["user"],
            "history":        history,
            "deal_score":     get_deal_score(history),
            "recommendation": get_ai_recommendation(history),
            "price_change":   round(((current - prev) / prev) * 100, 2),
            "created_at":     datetime.now(),
            "last_scraped":   datetime.now() if url and url != "#" else None,
        })

        check_and_notify(products_col, users_col)
        return redirect(url_for("watchlist"))

    return render_template("add_product.html",
                           username=session.get("name", "User"),
                           scrape_error=scrape_error)

@app.route("/delete_product/<pid>", methods=["POST"])
@login_required
def delete_product(pid):
    products_col.delete_one({"pid": pid, "owner": session["user"]})
    return redirect(url_for("watchlist"))


@app.route("/api/notify_test", methods=["POST"])
@login_required
def notify_test():
    user = users_col.find_one({"username": session["user"]})
    if not user or not user.get("email"):
        return jsonify({"ok": False, "error": "No email address saved in your settings."})
    ok, err = send_price_drop_email(
        to_email="test@example.com" if not user.get("email") else user["email"],
        to_name=user["name"],
        product_name="Test Product — Sony WH-1000XM5",
        current_price=54500,
        target_price=55000,
        platform="Daraz",
        savings=8000,
        deal_score=82,
        recommendation="buy",
    )
    if ok:
        return jsonify({"ok": True, "message": f"Test email sent to {user['email']}"})
    return jsonify({"ok": False, "error": err})

@app.route("/api/check_alerts")
@login_required
def api_check_alerts():
    count = check_and_notify(products_col, users_col)
    return jsonify({"notified": count})

# ── API Endpoints ──────────────────────────────────────────────
def scheduled_refresh():
    products = list(products_col.find({}))
    for product in products:
        url = product.get("url", "")
        if not url or url == "#":
            continue
        new_price = refresh_price(url)
        if not new_price:
            continue
        old_price    = product["current_price"]
        price_change = round(((new_price - old_price) / old_price) * 100, 2)
        today        = datetime.now().strftime("%Y-%m-%d")
        new_history  = (product.get("history", []) + [{"date": today, "price": new_price}])[-31:]
        products_col.update_one(
            {"_id": product["_id"]},
            {"$set": {
                "current_price":  new_price,
                "price_change":   price_change,
                "history":        new_history,
                "deal_score":     get_deal_score(new_history),
                "recommendation": get_ai_recommendation(new_history),
                "last_scraped":   datetime.now(),
            }}
        )
    check_and_notify(products_col, users_col)
    
@app.route("/api/dashboard")
@login_required
def api_dashboard():
    user         = session["user"]
    user_products = [serialize(p) for p in products_col.find({"owner": user})]

    total_saved  = sum(max(0, p["base_price"] - p["current_price"]) for p in user_products)
    targets_hit  = sum(1 for p in user_products if p["current_price"] <= p["target_price"])
    alerts_count = sum(1 for p in user_products if p["current_price"] <= p["target_price"] or p["price_change"] < -3)
    avg_score    = int(sum(p["deal_score"] for p in user_products) / len(user_products)) if user_products else 0

    recent_alerts = []
    for p in user_products:
        if p["price_change"] < -2:
            recent_alerts.append({"product": p["name"], "message": f"Price dropped {abs(p['price_change']):.1f}%", "type": "success", "time": "Just now"})
        elif p["current_price"] <= p["target_price"]:
            recent_alerts.append({"product": p["name"], "message": "Hit your target price!", "type": "success", "time": "Today"})
        elif p["price_change"] > 2:
            recent_alerts.append({"product": p["name"], "message": f"Price rising {p['price_change']:.1f}% — buy soon", "type": "warning", "time": "Today"})

    return jsonify({
        "total_products": len(user_products),
        "total_saved":    round(total_saved, 2),
        "targets_hit":    targets_hit,
        "active_alerts":  alerts_count,
        "deal_score":     avg_score,
        "products":       user_products,
        "recent_alerts":  recent_alerts[:5],
        "targets_total":  len(user_products),
    })

@app.route("/api/products")
@login_required
def api_products():
    docs = [serialize(p) for p in products_col.find({"owner": session["user"]})]
    return jsonify(docs)

@app.route("/api/product/<pid>/history")
@login_required
def api_product_history(pid):
    p = products_col.find_one({"pid": pid, "owner": session["user"]})
    return jsonify(p["history"] if p else [])

@app.route("/api/analytics")
@login_required
def api_analytics():
    user_products = [serialize(p) for p in products_col.find({"owner": session["user"]})]
    categories, platforms = {}, {}
    for p in user_products:
        cat = p.get("category", "Other")
        plt = p.get("platform", "Other")
        categories[cat] = categories.get(cat, 0) + 1
        platforms[plt]  = platforms.get(plt, 0) + 1
    return jsonify({"categories": categories, "platforms": platforms, "products": user_products})

# ── Email Settings & Notifications ────────────────────────────
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = session["user"]
    user_doc = users_col.find_one({"username": user})
    msg = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_email":
            new_email = request.form.get("email", "").strip()
            notify_on = request.form.get("email_notifications") == "on"
            users_col.update_one(
                {"username": user},
                {"$set": {"email": new_email, "email_notifications": notify_on}}
            )
            msg = {"type": "success", "text": "Settings saved successfully!"}
            user_doc = users_col.find_one({"username": user})

        elif action == "test_email":
            # Send a test email to the user's current email
            email = user_doc.get("email", "")
            if not email:
                msg = {"type": "error", "text": "No email address saved. Please save your email first."}
            else:
                from email_notifier import send_price_drop_email
                # Build a fake product for the test
                test_product = {
                    "name": "Test Product — Sony WH-1000XM5",
                    "platform": "Daraz",
                    "base_price": 62500,
                    "current_price": 54999,
                    "target_price": 55000,
                    "price_change": -8.1,
                    "recommendation": "buy",
                }
                result = send_price_drop_email(email, user_doc.get("name", user), test_product)
                if result["success"]:
                    msg = {"type": "success", "text": f"Test email sent to {email}!"}
                else:
                    msg = {"type": "error", "text": f"Failed: {result['error']}"}

        elif action == "run_check":
            # Manually trigger the notification checker
            from email_notifier import check_and_notify
            sent = check_and_notify(users_col, products_col)
            if sent:
                msg = {"type": "success", "text": f"Checked products. {len(sent)} notification(s) sent."}
            else:
                msg = {"type": "info", "text": "Checked all products. No new alerts triggered."}

    return render_template("settings.html",
                           username=session.get("name", "User"),
                           user_doc=user_doc,
                           msg=msg,
                           smtp_configured=bool(SMTP_EMAIL and SMTP_PASSWORD))

@app.route("/api/notify_check")
@login_required
def api_notify_check():
    """API endpoint to trigger notification check (can be called by a cron job)."""
    from email_notifier import check_and_notify
    sent = check_and_notify(users_col, products_col)
    return jsonify({"checked": True, "notifications_sent": len(sent), "details": sent})

@app.route("/api/scrape_preview", methods=["POST"])
@login_required
def api_scrape_preview():
    """Called by the Test button on Add Product page — returns scraped price without saving."""
    data = request.get_json()
    url  = (data or {}).get("url", "").strip()
    if not url:
        return jsonify({"price": None, "error": "No URL provided."})
    result = scrape_product(url)
    return jsonify(result)


@app.route("/api/refresh_price/<pid>", methods=["POST"])
@login_required
def api_refresh_price(pid):
    """
    Re-scrape the current price for a single product and update MongoDB.
    Called from the Watchlist page 'Refresh' button.
    """
    product = products_col.find_one({"pid": pid, "owner": session["user"]})
    if not product:
        return jsonify({"ok": False, "error": "Product not found."})

    url = product.get("url", "")
    if not url or url == "#":
        return jsonify({"ok": False, "error": "No URL saved for this product. Edit the product to add a URL."})

    new_price = refresh_price(url)
    if not new_price:
        return jsonify({"ok": False, "error": "Could not scrape price. The website may have changed its layout."})

    old_price = product["current_price"]
    price_change = round(((new_price - old_price) / old_price) * 100, 2)

    # Append new price to history
    today = datetime.now().strftime("%Y-%m-%d")
    new_history = product.get("history", []) + [{"date": today, "price": new_price}]

    # Keep only last 31 entries
    new_history = new_history[-31:]

    new_score = get_deal_score(new_history)
    new_rec   = get_ai_recommendation(new_history)

    products_col.update_one(
        {"pid": pid, "owner": session["user"]},
        {"$set": {
            "current_price":  new_price,
            "price_change":   price_change,
            "history":        new_history,
            "deal_score":     new_score,
            "recommendation": new_rec,
            "last_scraped":   datetime.now(),
            "email_notified": False if new_price <= product.get("target_price", 0) else product.get("email_notified", False),
        }}
    )

    # Fire email alert if target hit
    check_and_notify(products_col, users_col)

    return jsonify({
        "ok":           True,
        "new_price":    new_price,
        "price_change": price_change,
        "deal_score":   new_score,
        "recommendation": new_rec,
    })


@app.route("/api/refresh_all", methods=["POST"])
@login_required
def api_refresh_all():
    """Re-scrape prices for all products belonging to the current user."""
    products = list(products_col.find({"owner": session["user"]}))
    updated, failed = 0, 0

    for product in products:
        url = product.get("url", "")
        if not url or url == "#":
            failed += 1
            continue

        new_price = refresh_price(url)
        if not new_price:
            failed += 1
            continue

        old_price    = product["current_price"]
        price_change = round(((new_price - old_price) / old_price) * 100, 2)
        today        = datetime.now().strftime("%Y-%m-%d")
        new_history  = (product.get("history", []) + [{"date": today, "price": new_price}])[-31:]

        products_col.update_one(
            {"_id": product["_id"]},
            {"$set": {
                "current_price":  new_price,
                "price_change":   price_change,
                "history":        new_history,
                "deal_score":     get_deal_score(new_history),
                "recommendation": get_ai_recommendation(new_history),
                "last_scraped":   datetime.now(),
            }}
        )
        updated += 1

    check_and_notify(products_col, users_col)
    return jsonify({"ok": True, "updated": updated, "failed": failed})
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_refresh, "interval", hours=6)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True, port=5000)

