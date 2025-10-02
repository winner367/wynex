import streamlit as st
import hashlib
import json
import os
import time
from datetime import datetime
from deriv_oauth import redirect_to_deriv_signup
from auth_utils import register_user, login_user, get_current_user
import requests
from urllib.parse import urlencode, urlparse, parse_qs

# Define paths
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Helper functions
def hash_password(password):
    """Hash a password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def save_users_to_file():
    """Save users data to file"""
    if 'users' in st.session_state:
        with open(USERS_FILE, 'w') as f:
            json.dump(st.session_state.users, f)

def load_users_from_file():
    """Load users data from file"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def _ensure_users_initialized():
    """Ensure st.session_state.users exists and seed default admin if empty."""
    if 'users' not in st.session_state:
        st.session_state.users = load_users_from_file()
        if not st.session_state.users:
            st.session_state.users = {
                "williamsamoe2023@gmail.com": {
                    "email": "williamsamoe2023@gmail.com",
                    "password": hash_password("12345678"),
                    "name": "Admin User",
                    "role": "admin",
                    "created_at": datetime.now().isoformat()
                }
            }
            save_users_to_file()

# Authentication functions
def create_user(email, password, name, role="user"):
    """Create a new user and persist to database; mirror to session users for UI."""
    _ensure_users_initialized()
    # Persist via DB-backed auth
    if register_user(email, password, name, role):
        # Mirror to session store for legacy UI flows
        st.session_state.users[email] = {
            "email": email,
            "password": hash_password(password),
            "name": name,
            "role": role,
            "created_at": datetime.now().isoformat()
        }
        save_users_to_file()
        return True
    return False

def authenticate_user(email, password):
    """Authenticate a user using DB-backed auth; set session fields for UI."""
    _ensure_users_initialized()
    if not login_user(email, password):
        return False
    # Populate UI session details from DB profile
    user = get_current_user()
    if user:
        st.session_state.current_user_name = user.get("name", email)
        st.session_state.current_user_role = user.get("role", "user")
        # Keep a mirror record for legacy UIs
        if email not in st.session_state.users:
            st.session_state.users[email] = {
                "email": email,
                "password": hash_password(password),
                "name": st.session_state.current_user_name,
                "role": st.session_state.current_user_role,
                "created_at": datetime.now().isoformat()
            }
            save_users_to_file()
    return True

def verify_password(email, password):
    """Verify a user's password"""
    if email not in st.session_state.users:
        return False
        
    user = st.session_state.users[email]
    return user["password"] == hash_password(password)

def logout():
    """Log out the current user"""
    if 'is_authenticated' in st.session_state:
        del st.session_state.is_authenticated
    if 'current_user' in st.session_state:
        del st.session_state.current_user
    if 'current_user_name' in st.session_state:
        del st.session_state.current_user_name
    if 'current_user_role' in st.session_state:
        del st.session_state.current_user_role

# UI Components
def show_login_ui():
    """Display the login UI and handle login attempts"""
    _ensure_users_initialized()
    st.sidebar.header("Login")
    email = st.sidebar.text_input("Email", key="login_email")
    password = st.sidebar.text_input("Password", type="password", key="login_password")

    admin_email = "williamsamoe2023@gmail.com"

    # Unified local account login for all users
    if st.sidebar.button("Login", key="login_button"):
        if authenticate_user(email, password):
            st.sidebar.success("Login successful!")
            return True
        else:
            st.sidebar.error("Invalid email or password")
    return False

def show_register_ui():
    """Display the registration UI and handle registration attempts"""
    _ensure_users_initialized()
    st.sidebar.header("Register")
    
    name = st.sidebar.text_input("Name", key="register_name")
    email = st.sidebar.text_input("Email", key="register_email")
    password = st.sidebar.text_input("Password", type="password", key="register_password")
    confirm_password = st.sidebar.text_input("Confirm Password", type="password", key="register_confirm")
    
    if st.sidebar.button("Register", key="register_button"):
        # Validate inputs
        if not name or not email or not password:
            st.sidebar.error("All fields are required")
            return False
            
        if password != confirm_password:
            st.sidebar.error("Passwords don't match")
            return False
            
        # Check if user already exists
        if 'users' in st.session_state and email in st.session_state.users:
            st.sidebar.error("User already exists")
            return False
            
        # Create user with role 'user'
        if create_user(email, password, name, "user"):
            st.sidebar.success("Registration successful!")
            
            # Auto-login the user
            if authenticate_user(email, password):
                # Redirect to Deriv signup quietly in the background
                redirect_to_deriv_signup()
                return True
            
    return False

def show_auth_ui():
    """Display authentication UI (login/register) and handle auth operations"""
    _ensure_users_initialized()
    # Check if already logged in
    if st.session_state.get('is_authenticated', False):
        return True
        
    # Tabs for login/register
    auth_tab = st.sidebar.radio("", ["Login", "Register"])
    
    if auth_tab == "Login":
        return show_login_ui()
    else:
        return show_register_ui()

def show_admin_panel():
    """Display admin panel for user management"""
    st.title("Admin Panel")
    
    # Check if the current user is an admin
    if not st.session_state.get('is_authenticated', False) or st.session_state.get('current_user_role', '') != 'admin':
        st.error("You don't have permission to access the admin panel")
        return
        
    st.header("User Management")
    
    # List all users
    users = st.session_state.users
    user_list = []
    
    for email, user_data in users.items():
        user_list.append({
            "Email": email,
            "Name": user_data.get("name", "Unknown"),
            "Role": user_data.get("role", "user"),
            "Created": user_data.get("created_at", "Unknown")
        })
        
    st.table(user_list)
    
    # Create new user form
    st.header("Create New User")
    
    with st.form("create_user_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["user", "admin"])
        
        submitted = st.form_submit_button("Create User")
        
        if submitted:
            if not name or not email or not password:
                st.error("All fields are required")
            elif email in users:
                st.error("User already exists")
            else:
                create_user(email, password, name, role)
                st.success(f"Created user: {email}")
                st.rerun()
                
    # Delete user form
    st.header("Delete User")
    
    with st.form("delete_user_form"):
        user_to_delete = st.selectbox("Select User", list(users.keys()))
        confirm_delete = st.checkbox("I confirm that I want to delete this user")
        
        submitted = st.form_submit_button("Delete User")
        
        if submitted:
            if not confirm_delete:
                st.error("Please confirm deletion")
            elif user_to_delete == st.session_state.current_user:
                st.error("You cannot delete your own account")
            else:
                del st.session_state.users[user_to_delete]
                save_users_to_file()
                st.success(f"Deleted user: {user_to_delete}")
                st.rerun()

def show_user_profile():
    """Display the user profile page"""
    if 'current_user' not in st.session_state:
        st.error("You must be logged in to view your profile")
        return
        
    user_email = st.session_state.current_user
    user_data = st.session_state.users.get(user_email, {})
    
    st.title("Your Profile")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Display avatar (placeholder)
        st.image("https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y", width=150)
        
    with col2:
        st.header(user_data.get('name', 'Unknown User'))
        st.subheader(user_email)
        st.text(f"Role: {user_data.get('role', 'user').capitalize()}")
        
    # Change password section
    st.markdown("---")
    st.header("Change Password")
    
    current_password = st.text_input("Current Password", type="password", key="current_password")
    new_password = st.text_input("New Password", type="password", key="new_password")
    confirm_new_password = st.text_input("Confirm New Password", type="password", key="confirm_new_password")
    
    if st.button("Change Password", key="change_password_button"):
        # Verify current password
        if not verify_password(user_email, current_password):
            st.error("Current password is incorrect")
        elif new_password != confirm_new_password:
            st.error("New passwords don't match")
        elif len(new_password) < 6:
            st.error("New password must be at least 6 characters")
        else:
            # Update password in session state
            st.session_state.users[user_email]['password'] = hash_password(new_password)
            save_users_to_file()
            st.success("Password updated successfully")
            st.rerun()

DERIV_APP_ID = "105016"
DERIV_REDIRECT_URI = "https://www.winnerprinter.top"
DERIV_OAUTH_URL = f"https://oauth.deriv.com/oauth2/authorize?app_id={DERIV_APP_ID}&redirect_uri={DERIV_REDIRECT_URI}"
DERIV_API_URL = "wss://ws.binaryws.com/websockets/v3?app_id=105016"

def show_deriv_oauth_button():
    st.markdown(f"[Login or Create Account with Deriv.com]({DERIV_OAUTH_URL})", unsafe_allow_html=True)

# --- OAuth Callback Handler (call from API Configuration page) ---
def handle_deriv_oauth_callback():
    # Parse the query params for 'code' (if redirected back)
    query_params = st.query_params
    if 'code' in query_params:
        code = query_params.get('code')
        # Exchange code for token (Deriv uses implicit grant, so code is token)
        token = code  # For Deriv, the code is the token
        st.session_state['deriv_token'] = token
        st.success("Successfully authenticated with Deriv!")
        # Fetch account balances
        fetch_and_display_balances(token)
        # Set session state for user authentication
        st.session_state.is_authenticated = True
        st.session_state.current_user = f"deriv_user_{token[:8]}"
        st.session_state.current_user_name = "Deriv User"
        st.session_state.current_user_role = "user"
        st.success("Login successful! Redirecting to dashboard...")
        st.rerun()
        return True
    return False

def fetch_and_display_balances(token):
    import websocket
    import threading
    balances = {'demo': None, 'real': None}
    result_holder = {'done': False}
    
    def on_message(ws, message):
        data = json.loads(message)
        if 'authorize' in data:
            # After auth, request balance
            ws.send(json.dumps({"balance": 1, "account": "all"}))
        elif 'balance' in data:
            # Parse balances
            acc_type = data['balance'].get('account_type', 'unknown')
            balance = data['balance'].get('balance', 0)
            if acc_type == 'virtual':
                balances['demo'] = balance
            elif acc_type == 'real':
                balances['real'] = balance
            # If both received, close
            if balances['demo'] is not None and balances['real'] is not None:
                result_holder['done'] = True
                ws.close()
    def on_open(ws):
        ws.send(json.dumps({"authorize": token}))
    def on_error(ws, error):
        st.error(f"WebSocket error: {error}")
        result_holder['done'] = True
    def on_close(ws, *args):
        result_holder['done'] = True
    ws = websocket.WebSocketApp(
        DERIV_API_URL,
        on_message=on_message,
        on_open=on_open,
        on_error=on_error,
        on_close=on_close
    )
    thread = threading.Thread(target=ws.run_forever)
    thread.start()
    # Wait for balances or timeout
    import time
    timeout = 10
    start = time.time()
    while not result_holder['done'] and time.time() - start < timeout:
        time.sleep(0.1)
    # Display balances
    st.info(f"Demo Account Balance: {balances['demo']}")
    st.info(f"Real Account Balance: {balances['real']}")

 # Callback is invoked from pages that perform OAuth linking

def show_admin_login_ui():
    st.header("Admin Login")
    email = st.text_input("Admin Email", key="admin_email")
    password = st.text_input("Admin Password", type="password", key="admin_password")
    
    # Admin credentials
    admin_email = "williamsamoe2023@gmail.com"
    admin_password = "12345678"
    
    if st.button("Login as Admin"):
        if email == admin_email and password == admin_password:
            # Set session state for admin
            st.session_state.is_authenticated = True
            st.session_state.current_user = email
            st.session_state.current_user_role = "admin"
            st.session_state.current_user_name = "Admin User"
            st.session_state.page = 'admin'  # Set page to admin dashboard
            st.success("Admin login successful!")
            st.rerun()
        else:
            st.error("Invalid admin credentials. Please use the correct admin email and password.")

def show_user_login_ui():
    st.header("User Login")
    DERIV_APP_ID = "105016"
    DERIV_REDIRECT_URI = "https://www.winnerprinter.top"
    DERIV_OAUTH_URL = f"https://oauth.deriv.com/oauth2/authorize?app_id={DERIV_APP_ID}&redirect_uri={DERIV_REDIRECT_URI}"
    
    st.markdown(f"[Login or Create Account with Deriv.com]({DERIV_OAUTH_URL})", unsafe_allow_html=True)
    
    # Handle OAuth callback
    query_params = st.query_params
    if 'code' in query_params:
        token = query_params.get('code')
        st.session_state.is_authenticated = True
        st.session_state.current_user = f"deriv_user_{token[:8]}"
        st.session_state.current_user_role = "user"
        st.session_state.current_user_name = "Deriv User"
        st.session_state.page = 'dashboard'  # Set page to user dashboard
        st.success("User login successful!")
        st.rerun()

def show_user_dashboard():
    if not st.session_state.get('is_authenticated', False):
        st.error("Please login first")
        return
        
    st.title("User Dashboard")
    st.write(f"Welcome, {st.session_state.current_user_name}!")
    
    # Add user dashboard content here
    st.subheader("Trading Dashboard")
    st.write("Your trading dashboard content will appear here.")

def show_admin_panel():
    if not st.session_state.get('is_authenticated', False) or st.session_state.get('current_user_role') != 'admin':
        st.error("Admin access required")
        return
        
    st.title("Admin Dashboard")
    st.write(f"Welcome, {st.session_state.current_user_name}!")
    
    # Add admin dashboard content here
    st.subheader("Admin Controls")
    st.write("Your admin controls will appear here.")