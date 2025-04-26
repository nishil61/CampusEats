import razorpay
import streamlit as st
import mysql.connector
from datetime import datetime
import json
import os
from config import DB_CONFIG, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
import time

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
            conn = mysql.connector.connect(**DB_CONFIG)
            db_executor = conn.cursor()
            
            db_executor.execute(
                "UPDATE orders SET status = 'completed' WHERE id = %s",
                (order_id,)
            )
            
            conn.commit()
            db_executor.close()
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
        # Connect to database
        conn = mysql.connector.connect(**DB_CONFIG)
        db_executor = conn.cursor()
        
        # Get client details
        db_executor.execute("""
            SELECT u.name, u.email, u.role
            FROM users u
            JOIN orders o ON u.id = o.user_id
            WHERE o.id = %s
        """, (order_id,))
        
        client_details = db_executor.fetchone()
        if not client_details:
            st.error("Client details not found")
            return None
            
        # Create Razorpay order
        data = {
            "amount": int(amount * 100),  # Convert to paise
            "currency": "INR",
            "receipt": f"order_{order_id}",
            "payment_capture": 1,
            "notes": {
                "order_id": str(order_id)
            }
        }
        
        order = client.order.create(data=data)
        if not order:
            return None
        
        # Get order items for invoice
        db_executor.execute("""
            SELECT m.name, oi.quantity, oi.price_at_time, v.name as vendor_name
            FROM order_items oi
            JOIN menu_items m ON oi.menu_item_id = m.id
            JOIN vendors v ON m.vendor_id = v.id
            WHERE oi.order_id = %s
        """, (order_id,))
        
        order_items = db_executor.fetchall()
        
        # Prepare line items for invoice
        line_items = []
        for item in order_items:
            line_items.append({
                "name": f"{item[0]} (from {item[3]})",  # Include vendor name in item name
                "quantity": item[1],
                "amount": int(item[2] * 100),  # Convert to paise
                "currency": "INR"
            })
        
        # Create invoice
        invoice_data = {
            "type": "invoice",
            "description": f"Invoice for Order #{order_id}",
            "customer": {
                "name": client_details[0],
                "email": client_details[1],
            },
            "line_items": line_items,
            "notes": {
                "order_id": str(order_id)
            },
            "currency": "INR"
        }
        
        # Try to create the invoice
        try:
            invoice = client.invoice.create(data=invoice_data)
            
            # Store the invoice URL in session state so we can access it later
            if 'invoices' not in st.session_state:
                st.session_state.invoices = {}
            
            st.session_state.invoices[str(order_id)] = invoice['short_url']
            
        except Exception as e:
            st.error(f"Error creating invoice: {str(e)}")
            return order['id']  # Return order ID even if invoice creation fails
        
        # Show success message
        st.success("🎉 Payment initiated successfully! Please complete the payment to confirm your order.")
        
        # Display single Pay Now button
        try:
            invoice_url = invoice['short_url']
            st.markdown(f'<a href="{invoice_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold;">Pay Now</button></a>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error displaying payment button: {str(e)}")
        
        st.balloons()
        st.snow()
        
        return order['id']
        
    except razorpay.errors.BadRequestError as e:
        st.error(f"Invalid payment request: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error initiating payment: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return None
    finally:
        if 'db_executor' in locals():
            db_executor.close()
        if 'conn' in locals():
            conn.close() 