import streamlit as st
import os
from payment import client

def razorpay_button(amount, order_id, razorpay_order_id, user_name, user_email):
    # Get invoice URL for the order
    try:
        invoices = client.invoice.all()
        for invoice in invoices['items']:
            if invoice['notes'].get('order_id') == str(order_id):
                invoice_url = invoice['short_url']
                # Display a single Pay Now button that links to the invoice
                st.markdown(f"""
                    <a href="{invoice_url}" target="_blank">
                        <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold;">
                            Pay Now
                        </button>
                    </a>
                """, unsafe_allow_html=True)
                return
        
        # If no invoice found, create a link to the Razorpay checkout
        st.markdown(f"""
            <a href="https://checkout.razorpay.com/v1/checkout.js?key={os.getenv('RAZORPAY_KEY_ID')}&order_id={razorpay_order_id}" target="_blank">
                <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold;">
                    Pay Now
                </button>
            </a>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error finding invoice: {str(e)}")
        # Fallback to direct Razorpay checkout
        st.markdown(f"""
            <a href="https://checkout.razorpay.com/v1/checkout.js?key={os.getenv('RAZORPAY_KEY_ID')}&order_id={razorpay_order_id}" target="_blank">
                <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold;">
                    Pay Now
                </button>
            </a>
        """, unsafe_allow_html=True) 