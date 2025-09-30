import json
import os
import streamlit as st
from datetime import datetime
import hashlib

# Define file paths
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

def initialize_storage():
    """Initialize the data storage directory and files"""
    # Create data directory if it doesn't exist
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Create users file if it doesn't exist
    if not os.path.exists(USERS_FILE):
        # Create default admin user
        admin_password = hash_password("admin123")
        users_data = {
            "admin@example.com": {
                "password": admin_password,
                "name": "Admin User",
                "role": "admin",
                "last_login": None,
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Save to file
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=2)
    
    # Load users into session state
    load_users()

def hash_password(password):
    """Hash a password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from file into session state"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            
            # Convert date strings to datetime objects
            for email, user_data in users.items():
                if user_data.get('last_login'):
                    try:
                        user_data['last_login'] = datetime.fromisoformat(user_data['last_login'])
                    except:
                        user_data['last_login'] = None
            
            # Store in session state
            st.session_state.users = users
    else:
        st.session_state.users = {}

def save_users():
    """Save users from session state to file"""
    if 'users' in st.session_state:
        users_to_save = st.session_state.users.copy()
        
        # Convert datetime objects to strings for JSON serialization
        for email, user_data in users_to_save.items():
            if user_data.get('last_login') and isinstance(user_data['last_login'], datetime):
                user_data['last_login'] = user_data['last_login'].isoformat()
        
        # Save to file
        with open(USERS_FILE, 'w') as f:
            json.dump(users_to_save, f, indent=2)

def save_user_data(email, user_data):
    """Save data for a specific user"""
    if 'users' in st.session_state:
        st.session_state.users[email] = user_data
        save_users()

def save_deriv_token(email, token_data):
    """Save Deriv token for a user"""
    if 'users' in st.session_state and email in st.session_state.users:
        user_data = st.session_state.users[email]
        user_data['deriv_token'] = token_data
        save_user_data(email, user_data)