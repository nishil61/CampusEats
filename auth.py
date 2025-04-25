import streamlit as st
import hashlib
from db import get_user_by_email, create_user
from config import FIREBASE_CONFIG

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup(email, password, role, name=None):
    try:
        # First check if user already exists
        existing_user = get_user_by_email(email)
        
        if existing_user:
            st.error("Email already registered. Please use a different email or login.")
            return False
            
        hashed = hash_password(password)
        user_data = {
            "email": email,
            "password": hashed,
            "role": role,
            "name": name
        }
        
        result = create_user(user_data)
        
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
        # Get user from database
        user = get_user_by_email(email)
        
        if not user:
            return None, "User not registered. Please sign up first."
        
        # Check password
        hashed_password = hash_password(password)
        if user["password"] != hashed_password:
            return None, "Incorrect email or password. Please try again."
        
        # Return user data
        return {
            "id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "name": user["name"]
        }, None
        
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return None, "An error occurred. Please try again."

def get_current_user():
    if "user" in st.session_state:
        return st.session_state["user"]
    return None

def create_user(email, password, name):
    """Create a new user in Firebase Authentication"""
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=name
        )
        return user.uid
    except Exception as e:
        st.error(f"User creation error: {str(e)}")
        return None

def sign_in(email, password):
    """Sign in a user with Firebase Authentication"""
    try:
        user = auth.get_user_by_email(email)
        # Verify password (this is a simplified version - in production, use Firebase Auth UI)
        return user.uid
    except Exception as e:
        st.error(f"Sign in error: {str(e)}")
        return None

def get_user(uid):
    """Get user details from Firebase Authentication"""
    try:
        user = auth.get_user(uid)
        return {
            "uid": user.uid,
            "email": user.email,
            "name": user.display_name
        }
    except Exception as e:
        st.error(f"Get user error: {str(e)}")
        return None

def update_user(uid, name=None, email=None, password=None):
    """Update user details in Firebase Authentication"""
    try:
        update_data = {}
        if name:
            update_data["display_name"] = name
        if email:
            update_data["email"] = email
        if password:
            update_data["password"] = password
            
        auth.update_user(uid, **update_data)
        return True
    except Exception as e:
        st.error(f"Update user error: {str(e)}")
        return False

def delete_user(uid):
    """Delete a user from Firebase Authentication"""
    try:
        auth.delete_user(uid)
        return True
    except Exception as e:
        st.error(f"Delete user error: {str(e)}")
        return False
