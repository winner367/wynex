import streamlit as st
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import json
import secrets
import bcrypt
import jwt
from dataclasses import dataclass
from enum import Enum
from database import db

class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"
    SUSPENDED = "suspended"

@dataclass
class UserProfile:
    email: str
    name: str
    role: UserRole
    created_at: datetime
    last_login: datetime
    deriv_token: Optional[Dict] = None
    account_balances: Dict = None
    is_active: bool = True
    performance_metrics: Dict = None

class AuthAPI:
    def __init__(self):
        if 'current_user' not in st.session_state:
            st.session_state.current_user = None

    def create_user(self, email: str, password: str, name: str, role: UserRole = UserRole.USER) -> bool:
        return db.create_user(email, name, password, role.value)

    def login(self, email: str, password: str) -> bool:
        user_data = db.verify_user(email, password)
        if user_data and user_data['is_active']:
            st.session_state.current_user = email
            st.session_state.is_authenticated = True
            return True
        return False

    def logout(self):
        st.session_state.current_user = None
        st.session_state.is_authenticated = False
        if 'deriv_token' in st.session_state:
            del st.session_state.deriv_token

    def is_authenticated(self) -> bool:
        """Check if the user is authenticated"""
        # First make sure we have the required session variables
        if ('current_user' not in st.session_state or 
            'is_authenticated' not in st.session_state):
            return False
            
        # Make sure we have both a current user set and the authenticated flag is True
        if (st.session_state.current_user is None or 
            not st.session_state.is_authenticated):
            return False
        
        # For extra security, verify the user exists in the database
        user_data = db.get_user(st.session_state.current_user)
        if not user_data:
            # User doesn't exist in the database, clear session state
            st.session_state.current_user = None
            st.session_state.is_authenticated = False
            return False
            
        # Verify user is active
        if not user_data.get('is_active', False):
            # User is not active, clear session state
            st.session_state.current_user = None
            st.session_state.is_authenticated = False
            return False
        
        return True

    def is_admin(self) -> bool:
        if not self.is_authenticated():
            return False
        user_data = db.get_user(st.session_state.current_user)
        return user_data and user_data['role'] == 'admin'

    def get_current_user(self) -> Optional[Dict]:
        if not self.is_authenticated():
            return None
        return db.get_user(st.session_state.current_user)

    def update_user_profile(self, email: str, updates: Dict) -> bool:
        return db.update_user(email, updates)

    def suspend_user(self, email: str) -> bool:
        return db.update_user(email, {'is_active': False, 'role': UserRole.SUSPENDED.value})

    def activate_user(self, email: str) -> bool:
        return db.update_user(email, {'is_active': True, 'role': UserRole.USER.value})

    def get_all_users(self) -> List[Dict]:
        return db.get_all_users()

    def update_deriv_token(self, email: str, token: Dict):
        db.update_user(email, {'deriv_token': token})

    def update_account_balances(self, email: str, balances: Dict):
        db.update_user(email, {'account_balances': balances})

    def update_performance_metrics(self, email: str, metrics: Dict):
        db.update_user(email, {'performance_metrics': metrics})

# Initialize the auth system
auth_api = AuthAPI()

def initialize_auth_state():
    """Initialize authentication state in session state"""
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
        
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
        
    if 'auth_tokens' not in st.session_state:
        st.session_state.auth_tokens = {}

def hash_password(password: str) -> str:
    """Hash a password securely"""
    return hashlib.sha256(password.encode()).hexdigest()

def save_users():
    """Placeholder for saving users - session state only for now"""
    # Save is handled by session state persistence
    pass

def save_user_data(email: str, data: Dict[str, Any]):
    """Placeholder for saving user data - session state only for now"""
    if 'users' in st.session_state and email in st.session_state.users:
        st.session_state.users[email] = data
    pass

def authenticate_user(email: str, password: str) -> bool:
    """Authenticate a user with email and password"""
    initialize_auth_state()
    
    if email not in st.session_state.users:
        return False
    
    user = st.session_state.users[email]
    hashed_password = hash_password(password)
    
    if user["password"] == hashed_password:
        # Set current user if authentication successful
        st.session_state.current_user = email
        st.session_state.is_authenticated = True
        
        # Update last login time
        st.session_state.users[email]["last_login"] = datetime.now()
        save_users()
        
        # Generate auth token
        token = generate_auth_token(email)
        
        return True
    
    return False

def generate_auth_token(email: str) -> str:
    """Generate an authentication token for a user"""
    token = hashlib.sha256(f"{email}:{datetime.now().isoformat()}".encode()).hexdigest()
    expiry = datetime.now() + timedelta(hours=24)
    
    st.session_state.auth_tokens[token] = {
        "email": email,
        "expiry": expiry
    }
    
    return token

def validate_token(token: str) -> bool:
    """Validate an authentication token"""
    if token not in st.session_state.auth_tokens:
        return False
    
    token_info = st.session_state.auth_tokens[token]
    if token_info["expiry"] < datetime.now():
        # Token has expired, remove it
        del st.session_state.auth_tokens[token]
        return False
    
    # Set current user from token
    st.session_state.current_user = token_info["email"]
    st.session_state.is_authenticated = True
    
    return True

def create_user(email: str, password: str, name: str, role: str = "user") -> bool:
    """Create a new user"""
    initialize_auth_state()
    
    if email in st.session_state.users:
        return False  # User already exists
    
    hashed_password = hash_password(password)
    
    st.session_state.users[email] = {
        "password": hashed_password,
        "name": name,
        "role": role,
        "last_login": None,
        "created_at": datetime.now().isoformat()
    }
    
    # Save user data to persistent storage
    save_users()
    
    return True

def update_user(email: str, data: Dict[str, Any]) -> bool:
    """Update user information"""
    initialize_auth_state()
    
    if email not in st.session_state.users:
        return False
    
    user = st.session_state.users[email]
    
    # Update user data
    if "name" in data:
        user["name"] = data["name"]
    
    if "role" in data:
        user["role"] = data["role"]
    
    if "password" in data and data["password"]:
        user["password"] = hash_password(data["password"])
    
    # Save changes
    save_user_data(email, user)
    
    return True

def delete_user(email: str) -> bool:
    """Delete a user"""
    initialize_auth_state()
    
    if email not in st.session_state.users or email == "admin@example.com":
        return False  # Can't delete admin or non-existent user
    
    del st.session_state.users[email]
    
    # Clean up any tokens for this user
    tokens_to_delete = []
    for token, info in st.session_state.auth_tokens.items():
        if info["email"] == email:
            tokens_to_delete.append(token)
    
    for token in tokens_to_delete:
        del st.session_state.auth_tokens[token]
    
    # Save changes
    save_users()
    
    return True

def get_all_users() -> List[Dict[str, Any]]:
    """Get a list of all users"""
    initialize_auth_state()
    
    users = []
    for email, user_data in st.session_state.users.items():
        user_info = {
            "email": email,
            "name": user_data["name"],
            "role": user_data["role"],
            "last_login": user_data["last_login"]
        }
        users.append(user_info)
    
    return users

# --- REMOVE OR COMMENT OUT THE FOLLOWING STANDALONE FUNCTIONS ---
# def is_authenticated() -> bool:
#     ...
# def is_admin() -> bool:
#     ...
# def get_current_user() -> Optional[Dict[str, Any]]:
#     ...
# def logout() -> None:
#     ...
# (and any other session-based auth functions at the bottom of this file)