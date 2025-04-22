import streamlit as st
from db import execute_query
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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

def login(email, password):
    try:
        hashed = hash_password(password)
        user = execute_query(
            "SELECT * FROM users WHERE email = %s AND password = %s",
            (email, hashed),
            fetch=True
        )
        if user:
            return user[0]
        st.error("Invalid email or password")
        return None
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return None

def get_current_user():
    if "user" in st.session_state:
        return st.session_state["user"]
    return None
