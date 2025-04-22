import streamlit as st
from auth import login, signup, get_current_user
from ui import client_ui, admin_ui

st.set_page_config(page_title="Campus Eats", page_icon="🍽")

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
                    st.rerun()
                else:
                    st.error("Signup failed. Please try again.")
        
        else:  # Login
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            if st.button("Login"):
                user = login(email, password)
                if user:
                    st.session_state["user"] = user
                    st.success(f"Logged in as {user['role']}")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    
    else:
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
