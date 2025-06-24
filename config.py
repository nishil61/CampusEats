import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': 'mainline.proxy.rlwy.net',
    'port': 17254,
    'user': 'root',
    'password': 'dCPjCVlAHJUJdmrVHfDhOZlBMqKKpysk',
    'database': 'railway'
}

# Razorpay configuration
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_Y8mpoQXD52pv3L')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'Aj2MgIxIaYHpnyq8JHH83ToG') 