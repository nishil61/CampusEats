import streamlit as st
from auth import login, signup, get_current_user
from ui import client_ui, admin_ui
import mysql.connector
from payment import verify_payment
import time

st.set_page_config(page_title="Campus Eats", page_icon="🍽")

def show_notification(title, body):
    # Show balloons for visual feedback
    st.balloons()
    
    # Create a container for the notification
    with st.container():
        # Add some spacing
        st.write("")
        st.write("")
        
        # Show the notification message
        st.markdown(f"""
        <div style='text-align: center; padding: 20px; background-color: #4CAF50; color: white; border-radius: 5px; margin: 20px 0;'>
            <h3 style='margin: 0;'>{title}</h3>
            <p style='margin: 10px 0; font-size: 16px;'>{body}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add some spacing
        st.write("")
        st.write("")

def check_payment_status(order_id):
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="canteen1"
        )
        cursor = conn.cursor()
        
        # Get order details
        cursor.execute("""
            SELECT razorpay_order_id, status
            FROM orders
            WHERE id = %s
        """, (order_id,))
        
        order = cursor.fetchone()
        if not order:
            return {"status": "error", "message": "Order not found"}
        
        razorpay_order_id, status = order
        
        if status == "paid":
            return {"status": "paid"}
        
        # Check payment status with Razorpay
        if razorpay_order_id:
            payment_status = verify_payment(razorpay_order_id)
            if payment_status:
                # Update order status
                cursor.execute("""
                    UPDATE orders
                    SET status = 'paid'
                    WHERE id = %s
                """, (order_id,))
                conn.commit()
                return {"status": "paid"}
        
        return {"status": "pending"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def main():
    if "user" not in st.session_state:
        st.title("🍽 Campus Eats")
        mode = st.radio("Login or Signup", ["Login", "Signup"])
        
        if mode == "Signup":
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["client", "admin"])
            
            if st.button("Create Account"):
                if signup(email, password, role, name):
                    show_notification(
                        "🎉 Account Created Successfully!",
                        "Please login with your credentials to continue."
                    )
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Signup failed. Please try again.")
        
        else:  # Login
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            if st.button("Login"):
                user, error_message = login(email, password)
                if user:
                    st.session_state["user"] = user
                    show_notification(
                        "👋 Welcome Back!",
                        f"Hello, {user['name'] or user['email']}! You have successfully logged in."
                    )
                    time.sleep(2)
                    st.rerun()
                else:
                    # Show specific error message based on the error
                    st.error(error_message)
    
    else:
        # User is logged in, show the appropriate UI
        user = get_current_user()
        st.sidebar.title(f"Welcome, {user['name'] or user['email']}")
        
        if st.sidebar.button("Logout"):
            del st.session_state["user"]
            st.rerun()
        
        if user["role"] == "admin":
            admin_ui()
        else:  # client
            client_ui()

if __name__ == "__main__":
    main()
