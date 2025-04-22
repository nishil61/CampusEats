import razorpay
import streamlit as st
import mysql.connector
from datetime import datetime
import json
import os

# Get Razorpay credentials from environment variables
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_Y8mpoQXD52pv3L')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'Aj2MgIxIaYHpnyq8JHH83ToG')

# Initialize Razorpay client
try:
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    # Test the connection
    client.payment.all()
except razorpay.errors.BadRequestError as e:
    st.error("Invalid Razorpay credentials. Please check your API keys.")
    st.stop()
except Exception as e:
    st.error(f"Error initializing Razorpay client: {str(e)}")
    st.stop()

def create_payment_order(amount, order_id):
    try:
        # Convert amount to paise (Razorpay uses smallest currency unit)
        amount_paise = int(amount * 100)
        
        # Create order in Razorpay
        order = client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'payment_capture': 1,
            'notes': {
                'order_id': order_id
            }
        })
        
        return order['id']
    except razorpay.errors.BadRequestError as e:
        st.error(f"Invalid request to Razorpay: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error creating payment order: {str(e)}")
        return None

def verify_payment(payment_id, order_id):
    try:
        # Verify payment with Razorpay
        payment = client.payment.fetch(payment_id)
        
        if payment['status'] == 'captured':
            # Update order status in database
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="canteen1"
            )
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE orders SET status = 'completed' WHERE id = %s",
                (order_id,)
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
        return False
        
    except razorpay.errors.BadRequestError as e:
        st.error(f"Invalid payment verification request: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Error verifying payment: {e}")
        return False

def initiate_payment(amount, order_id):
    try:
        # Create Razorpay order
        data = {
            "amount": int(amount * 100),  # Convert to paise
            "currency": "INR",
            "receipt": f"order_{order_id}",
            "payment_capture": 1
        }
        
        order = client.order.create(data=data)
        
        # Get order items and client details from database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="canteen1"
        )
        cursor = conn.cursor()
        
        # Get order items
        cursor.execute("""
            SELECT mi.name, oi.quantity, oi.price_at_time
            FROM order_items oi
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE oi.order_id = %s
        """, (order_id,))
        order_items = cursor.fetchall()
        
        # Get client details
        cursor.execute("""
            SELECT u.name, u.email, u.role
            FROM users u
            JOIN orders o ON u.id = o.user_id
            WHERE o.id = %s
        """, (order_id,))
        client_details = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Prepare line items for invoice
        line_items = []
        for item in order_items:
            line_items.append({
                "name": item[0],  # item name
                "description": f"Quantity: {item[1]}",  # quantity
                "amount": int(item[2] * 100),  # price in paise
                "currency": "INR",
                "quantity": item[1]  # quantity
            })
        
        # Create invoice
        invoice_data = {
            "type": "invoice",
            "description": f"Order #{order_id}",
            "customer": {
                "name": client_details[0],  # client name
                "email": client_details[1],  # client email
                "contact": client_details[2]  # client role
            },
            "line_items": line_items,
            "sms_notify": 1,
            "email_notify": 1,
            "currency": "INR",
            "notes": {
                "order_id": str(order_id),
                "customer_name": client_details[0],
                "customer_role": client_details[2],
                "order_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "payment_status": "Paid",
                "amount_paid": f"₹{amount:.2f}"
            }
        }
        
        invoice = client.invoice.create(data=invoice_data)
        
        # Create payment button with success popup and invoice download
        st.markdown(f"""
        <script>
        function showSuccessPopup() {{
            alert('Order placed successfully! You will be redirected to payment page.');
        }}
        </script>
        
        <form action="https://api.razorpay.com/v1/checkout/embedded" method="POST" onsubmit="showSuccessPopup()">
            <input type="hidden" name="key_id" value="{RAZORPAY_KEY_ID}">
            <input type="hidden" name="order_id" value="{order['id']}">
            <input type="hidden" name="name" value="Canteen Order">
            <input type="hidden" name="description" value="Order #{order_id}">
            <input type="hidden" name="amount" value="{amount * 100}">
            <input type="hidden" name="currency" value="INR">
            <input type="hidden" name="prefill[name]" value="{client_details[0]}">
            <input type="hidden" name="prefill[email]" value="{client_details[1]}">
            <input type="hidden" name="theme[color]" value="#F37254">
            <button type="submit" style="background-color: #F37254; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">
                Pay Now
            </button>
        </form>
        
        <div style="margin-top: 20px;">
            <a href="{invoice['short_url']}" target="_blank" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                Download Invoice
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        return order['id']
        
    except razorpay.errors.BadRequestError as e:
        st.error(f"Invalid payment request: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error initiating payment: {e}")
        return None 