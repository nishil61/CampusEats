import streamlit as st
from auth import login, signup, get_current_user
from ui import customer_ui, vendor_ui

def main():
    st.title("Campus Eats")
    
    # Initialize session state
    if "user" not in st.session_state:
        st.session_state.user = None
    
    # Sidebar for login/signup
    with st.sidebar:
        st.header("Account")
        
        if st.session_state.user is None:
            # Login/Signup form
            choice = st.radio("Choose an option", ["Login", "Sign Up"])
            
            if choice == "Login":
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                
                if st.button("Login"):
                    user, error = login(email, password)
                    if user:
                        st.session_state.user = user
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error(error)
            
            else:  # Sign Up
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                role = st.selectbox("Role", ["user", "vendor"])  # Only show user and vendor options
                
                if st.button("Sign Up"):
                    if signup(email, password, role):
                        st.success("Account created successfully! Please login.")
        
        else:  # User is logged in
            st.write(f"Welcome, {st.session_state.user['name']}!")
            if st.button("Logout"):
                st.session_state.user = None
                st.rerun()
    
    # Main content area
    if st.session_state.user is None:
        st.info("Please login or sign up to continue.")
    else:
        # Show appropriate UI based on user role
        if st.session_state.user["role"] == "customer":
            customer_ui()
        elif st.session_state.user["role"] == "vendor":
            vendor_ui()
        elif st.session_state.user["role"] == "admin":
            vendor_ui()  # Admin will use the same UI as vendors for now

if __name__ == "__main__":
    main() 