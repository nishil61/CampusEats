import streamlit as st
from db import execute_query
import hashlib
import mysql.connector
from config import DB_CONFIG
import time

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_vendor_email(email):
    vendor_emails = {
        "feefafoo@campuseats.com": "Fee Fa Foo",
        "mechcafe@campuseats.com": "Mech Cafe",
        "poornima@campuseats.com": "Poornima Kitchen",
        "nescafe@campuseats.com": "Nescafe"
    }
    return email in vendor_emails, vendor_emails.get(email)

def signup(email, password, role, name=None):
    try:
        # First check if user already exists
        existing_user = execute_query(
            "SELECT * FROM users WHERE email = %s",
            (email,),
            fetch=True
        )
        
        if existing_user:
            st.error("Email already registered. Please use a different email or login.")
            return False
            
        # For vendors, validate the email
        if role == "vendor":
            is_valid, vendor_name = validate_vendor_email(email)
            if not is_valid:
                st.error("Invalid vendor email. Please use the correct vendor email address.")
                return False
            name = vendor_name  # Set the vendor name from the email mapping
            
        hashed = hash_password(password)
        result = execute_query(
            "INSERT INTO users (email, password, role, name) VALUES (%s, %s, %s, %s)",
            (email, hashed, role, name)
        )
        
        if result is None:
            st.error("Failed to create account. Please try again.")
            return False
            
        st.success("Account created successfully! Please login.")
        return True
        
    except Exception as e:
        st.error(f"Signup failed: {str(e)}")
        return False

def show_signup_form():
    st.title("Sign Up")
    with st.form("signup_form"):
        st.markdown("""
        <style>
        .signup-form {
            max-width: 400px;
            margin: 0 auto;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)
        
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Role", ["user", "vendor"])  # Only show user and vendor options
        
        submit = st.form_submit_button("Sign Up")
        
        if submit:
            if password != confirm_password:
                st.error("Passwords do not match!")
            else:
                signup(email, password, role, name)

def login(email=None, password=None):
    # If email and password are provided, use the original login logic
    if email is not None and password is not None:
        try:
            # Connect to database
            conn = mysql.connector.connect(**DB_CONFIG)
            db_executor = conn.cursor()
            
            # Check if user exists
            db_executor.execute(
                "SELECT id, name, role, password FROM users WHERE email = %s",
                (email,)
            )
            user = db_executor.fetchone()
            
            if user and user[3] == hash_password(password):  # Check hashed password
                return {
                    "id": user[0],
                    "name": user[1],
                    "email": email,
                    "role": user[2]
                }, None
            else:
                return None, "Invalid email or password"
            
            db_executor.close()
            conn.close()
        except mysql.connector.Error as e:
            return None, f"An error occurred. Please try again. Error: {str(e)}"
    
    # If no parameters provided, show the Streamlit UI
    st.title("Login")
    
    # Add a container for the login form
    with st.container():
        # Add a form for login
        with st.form("login_form"):
            st.markdown("""
            <style>
            .login-form {
                max-width: 400px;
                margin: 0 auto;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            </style>
            """, unsafe_allow_html=True)
            
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            # Create two columns for buttons
            col1, col2 = st.columns(2)
            
            with col1:
                submit = st.form_submit_button("Login", use_container_width=True)
            
            with col2:
                if st.form_submit_button("Forgot Password?", use_container_width=True):
                    st.session_state.show_forgot_password = True
            
            if submit:
                try:
                    # Connect to database
                    conn = mysql.connector.connect(**DB_CONFIG)
                    db_executor = conn.cursor()
                    
                    # Check if user exists
                    db_executor.execute(
                        "SELECT id, name, role, password FROM users WHERE email = %s",
                        (email,)
                    )
                    user = db_executor.fetchone()
                    
                    if user and user[3] == hash_password(password):  # Check hashed password
                        st.session_state.user = {
                            "id": user[0],
                            "name": user[1],
                            "email": email,
                            "role": user[2]
                        }
                        # Show success notification with balloons
                        st.balloons()
                        st.markdown(f"""
                        <div style='text-align: center; padding: 20px; background-color: #4CAF50; color: white; border-radius: 5px; margin: 20px 0;'>
                            <h3 style='margin: 0;'>👋 Welcome Back!</h3>
                            <p style='margin: 10px 0; font-size: 16px;'>Hello, {user[1] or email}! You have successfully logged in.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
                    
                    db_executor.close()
                    conn.close()
                except mysql.connector.Error as e:
                    st.error(f"An error occurred. Please try again. Error: {str(e)}")
    
    # Show forgot password form if button is clicked
    if st.session_state.get('show_forgot_password'):
        with st.container():
            st.subheader("Reset Password")
            with st.form("forgot_password_form"):
                st.markdown("""
                <style>
                .reset-form {
                    max-width: 400px;
                    margin: 0 auto;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }
                </style>
                """, unsafe_allow_html=True)
                
                reset_email = st.text_input("Enter your email")
                new_password = st.text_input("Enter new password", type="password")
                confirm_password = st.text_input("Confirm new password", type="password")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    reset_submit = st.form_submit_button("Reset Password", use_container_width=True)
                
                with col4:
                    if st.form_submit_button("Back to Login", use_container_width=True):
                        st.session_state.show_forgot_password = False
                        st.rerun()
                
                if reset_submit:
                    if new_password != confirm_password:
                        st.error("Passwords do not match!")
                    else:
                        try:
                            # Connect to database
                            conn = mysql.connector.connect(**DB_CONFIG)
                            db_executor = conn.cursor()
                            
                            # Check if email exists
                            db_executor.execute(
                                "SELECT id FROM users WHERE email = %s",
                                (reset_email,)
                            )
                            user = db_executor.fetchone()
                            
                            if user:
                                # Hash the new password before storing
                                hashed_password = hash_password(new_password)
                                
                                # Update password with hashed version
                                db_executor.execute(
                                    "UPDATE users SET password = %s WHERE email = %s",
                                    (hashed_password, reset_email)
                                )
                                conn.commit()
                                # Show success notification with balloons
                                st.balloons()
                                st.markdown(f"""
                                <div style='text-align: center; padding: 20px; background-color: #4CAF50; color: white; border-radius: 5px; margin: 20px 0;'>
                                    <h3 style='margin: 0;'>🎉 Password Reset Successful!</h3>
                                    <p style='margin: 10px 0; font-size: 16px;'>Please login with your new password.</p>
                                </div>
                                """, unsafe_allow_html=True)
                                st.session_state.show_forgot_password = False
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("Email not found in our records.")
                            
                            db_executor.close()
                            conn.close()
                        except mysql.connector.Error as e:
                            st.error(f"An error occurred. Please try again. Error: {str(e)}")

def get_current_user():
    if "user" in st.session_state:
        return st.session_state["user"]
    return None
