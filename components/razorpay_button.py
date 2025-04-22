import streamlit as st
import os

def razorpay_button(amount, order_id, razorpay_order_id, user_name, user_email):
    st.markdown("""
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
        <div id="razorpay-payment">
            <script>
                var options = {
                    "key": "%s",
                    "amount": "%d",
                    "currency": "INR",
                    "name": "Food Order",
                    "description": "Order #%d",
                    "order_id": "%s",
                    "handler": function (response){
                        window.location.href = "/payment_success?order_id=%d&payment_id=" + response.razorpay_payment_id;
                    },
                    "prefill": {
                        "name": "%s",
                        "email": "%s"
                    },
                    "theme": {
                        "color": "#F37254"
                    }
                };
                var rzp1 = new Razorpay(options);
                rzp1.open();
            </script>
        </div>
    """ % (
        os.getenv('RAZORPAY_KEY_ID'),
        int(amount * 100),
        order_id,
        razorpay_order_id,
        order_id,
        user_name,
        user_email
    ), unsafe_allow_html=True) 