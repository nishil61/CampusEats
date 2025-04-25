import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "campus_eats")

# Firebase Configuration
FIREBASE_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY", "YOUR_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", "YOUR_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", "YOUR_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "YOUR_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "YOUR_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID", "YOUR_APP_ID")
}

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "YOUR_RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "YOUR_RAZORPAY_KEY_SECRET")

# Application Settings
APP_NAME = "Campus Eats"
APP_VERSION = "1.0.0"
DEBUG = True

# Collections
USERS_COLLECTION = "users"
MENU_ITEMS_COLLECTION = "menu_items"
ORDERS_COLLECTION = "orders"
ORDER_ITEMS_COLLECTION = "order_items"
VENDORS_COLLECTION = "vendors"

# Session Configuration
SESSION_EXPIRY = 3600  # 1 hour in seconds

# UI Configuration
THEME_COLOR = "#FF4B2B"
SECONDARY_COLOR = "#FF416C"
BACKGROUND_COLOR = "#F8F9FA"

# Order Status
ORDER_STATUS = {
    "PENDING": "pending",
    "CONFIRMED": "confirmed",
    "PREPARING": "preparing",
    "READY": "ready",
    "PICKED_UP": "picked_up",
    "COMPLETED": "completed",
    "CANCELLED": "cancelled"
}

# Payment Status
PAYMENT_STATUS = {
    "PENDING": "pending",
    "SUCCESS": "success",
    "FAILED": "failed"
} 