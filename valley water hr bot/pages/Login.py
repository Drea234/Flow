# login.py
import streamlit as st
import os
import time
from datetime import datetime
import hashlib
from utils.user_auth import UserAuth, login_user, logout_user



# Custom CSS for styling with company logo support
st.markdown("""
<style>
    /* Hide the sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Hide the navigation menu */
    header[data-testid="stHeader"] {
        display: none;
    }
    
    /* Custom title styling */
    .main-title {
        text-align: center;
        font-size: 2.5rem !important;
        margin-bottom: 1rem;
    }
    
    .title-valley {
        color: #5cab44 !important;
    }
    
    .title-water {
        color: #1c8ccc !important;
    }
    
    .subtitle {
        text-align: center;
        font-size: 1.5rem !important;
        margin-bottom: 2rem;
        color: #505050;
    }
    
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        background-color: #f8f9fa;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Custom button styling */
    .stButton > button {
        width: 100%;
        background-color: #1c8ccc !important;
        color: white !important;
    }
    
    .stButton > button:hover {
        background-color: #176fa8 !important;
        color: white !important;
    }
    
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        text-align: center;
        padding: 1rem;
        background-color: #f8f9fa;
        font-size: 0.8rem;
        color: #6c757d;
        border-top: 1px solid #eaeaea;
    }
    
    /* Center logo */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 2rem;
    }
    
    .logo-container img {
        display: block;
        margin: 0 auto;
    }
    
    /* Center the entire login form */
    .stForm {
        display: flex;
        flex-direction: column;
        align-items: stretch;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Initialize auth
    auth = UserAuth()
    
    # Check if user is already logged in
    if "logged_in" in st.session_state and st.session_state.logged_in:
        st.switch_page("pages/employee_portal.py")
    
    # App header with styled title
    st.markdown("""
    <h1 class='main-title'>
        <span style='color: black;'>AI-Powered</span>
        <span class='title-valley'>Valley</span>
        <span class='title-water'>Water</span>
        <span style='color: black;'>HR Assistant</span>
    </h1>
    """, unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>FLOW</p>", unsafe_allow_html=True)
    
    # Center column for login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Login container
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        
        # Company logo - centered
        st.markdown("<div class='logo-container'>", unsafe_allow_html=True)
        # Check if company logo exists, otherwise use placeholder
        if os.path.exists("assets/valley_water_logo.png"):
            st.image("assets/valley_water_logo.png", width=200)
        else:
            st.image("https://via.placeholder.com/200x80?text=Valley+Water", width=200)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Login form
        st.subheader("Employee Login")
        
        employee_id = st.text_input("Employee ID")
        password = st.text_input("Password", type="password")
        
        # Login button
        if st.button("Log In", type="primary"):
            if not employee_id or not password:
                st.error("Please enter both employee ID and password")
            else:
                # Attempt login
                if auth.authenticate(employee_id, password):
                    # Get employee data
                    employee_data = auth.get_employee_data(employee_id)
                    is_admin = auth.is_admin(employee_id)
                    
                    if employee_data:
                        # Set session state
                        login_user(employee_id, employee_data, is_admin)
                        st.session_state.login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Success message with loading spinner
                        with st.spinner("Logging in..."):
                            st.success(f"Welcome, {employee_data['name']}!")
                            time.sleep(1)  # Brief delay for user experience
                            st.switch_page("pages/employee_portal.py")
                    else:
                        st.error("Employee data not found. Please contact HR.")
                else:
                    st.error("Invalid employee ID or password. Please try again.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Help links below login form
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("<div style='text-align: center;'><a href='#'>Forgot Password?</a></div>", unsafe_allow_html=True)
        with col_b:
            st.markdown("<div style='text-align: center;'><a href='#'>Need Help?</a></div>", unsafe_allow_html=True)
    
    # Developer options (in production, you'd remove this)
    with st.expander("Developer Options", expanded=False):
        st.caption("Quick login options for testing")
        
        test_users = [
            ("test", "Test User (Admin)"),
            ("EMP12345", "Regular Employee")
        ]
        
        selected_test_user = st.selectbox("Select a test user:", test_users)
        test_id = selected_test_user[0]
        
        if st.button("Quick Login"):
            # Use test credentials
            if test_id == "test":
                test_password = "test"
            else:
                # For demo purposes, password is last 5 chars of ID
                test_password = "12345"
            
            if auth.authenticate(test_id, test_password):
                employee_data = auth.get_employee_data(test_id)
                is_admin = auth.is_admin(test_id)
                
                if employee_data:
                    # Set session state
                    login_user(test_id, employee_data, is_admin)
                    st.session_state.login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    with st.spinner(f"Logging in as {employee_data['name']}..."):
                        st.success(f"Welcome, {employee_data['name']}!")
                        time.sleep(1)
                        st.switch_page("pages/employee_portal.py")
    
    # Footer
    st.markdown("<div class='footer'>© 2025 Valley Water HR Assistant | Developed by Team Sapphire</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()