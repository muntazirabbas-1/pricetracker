# PriceTrack Pro

A professional AI-powered price tracker built with Flask + MongoDB.

## Features
- User authentication (register / login with hashed passwords)
- MongoDB database — users & products collections
- Multi-product tracking with 30-day price history
- AI deal score + buy/wait/hold recommendation
- Interactive charts (Chart.js) — sparklines, trends, analytics
- Price drop & surge smart alerts
- Dark mode, fully responsive

## Setup

### 1. Install MongoDB (choose one)

**Option A — Local MongoDB:**
- Download: https://www.mongodb.com/try/download/community
- Start service: `mongod` (or via MongoDB Compass)

**Option B — MongoDB Atlas (cloud, free tier):**
- Create free cluster at https://cloud.mongodb.com
- Get your connection string, e.g.:
  `mongodb+srv://username:password@cluster.mongodb.net/pricetracker`
- Set environment variable before running:
  Windows:  `set MONGO_URI=your_connection_string`
  Mac/Linux: `export MONGO_URI=your_connection_string`


**Environment Variables

 This project uses a `.env` file to store sensitive information such as database connection strings, API keys, and email credentials.
 For security reasons, the `.env` file is **not included** in this repository.
 Create a `.env` file in the project's root directory and add the required environment variables with your own credentials before running the application.
**Example:**
 ```env
  MONGO_URI=your_mongodb_connection_string
  SMTP_EMAIL=your_email@example.com
  SMTP_PASSWORD=your_email_app_password
  ```



### 2. Install Python dependencies
```
pip install -r requirements.txt
```

### 3. Run the app
```
python app.py
```

### 4. Open in browser
```
http://localhost:5000
```

## Demo Login
- Username: `demo`
- Password: `demo123`

## MongoDB Collections
| Collection | Purpose |
|---|---|
| `users` | Stores username, hashed password, name, email |
| `products` | Stores tracked products, price history, deal score, AI recommendation |

## Project Structure
```
pricetracker/
├── app.py                  ← Flask + PyMongo backend
├── requirements.txt        ← flask, pymongo
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── watchlist.html
│   ├── analytics.html
│   ├── alerts.html
│   └── add_product.html
└── static/
    ├── css/main.css
    └── js/main.js
```

## Tech Stack
- Backend: Python Flask + PyMongo
- Database: MongoDB
- Frontend: HTML5, CSS3, Vanilla JS
- Charts: Chart.js 4
- Icons: Font Awesome 6
- Fonts: Syne + DM Sans
