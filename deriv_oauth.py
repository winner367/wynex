import streamlit as st
import requests
import json
import secrets
from typing import Dict, Any, Optional, Tuple
from auth_api import auth_api

# Constants
OAUTH_BASE_URL = "https://oauth.deriv.com/oauth2/authorize"
TOKEN_URL = "https://oauth.deriv.com/oauth2/token"
APP_ID = "71514"  # Your Deriv App ID
REDIRECT_URI = "https://ce51-102-219-210-201.ngrok-free.app/oauth/callback"
SCOPES = "read trade admin payments"

class DerivOAuth:
    def __init__(self):
        self.app_id = "71514"  # Your Deriv App ID
        self.redirect_uri = "http://localhost:8501/callback"  # Must match your app's redirect URI
        
    def get_auth_url(self) -> str:
        """Generate the OAuth authorization URL"""
        return (
            "https://oauth.deriv.com/oauth2/authorize?"
            f"app_id={self.app_id}&"
            f"l=EN&"
            f"brand=deriv&"
            f"redirect_uri={self.redirect_uri}"
        )
    
    def redirect_to_oauth(self):
        """Redirect user to Deriv OAuth page"""
        auth_url = self.get_auth_url()
        st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
    
    def handle_oauth_callback(self, code: str) -> Optional[Dict]:
        """Handle OAuth callback and get access token"""
        try:
            # Exchange code for token
            token_url = "https://oauth.deriv.com/oauth2/token"
            response = requests.post(token_url, data={
                'grant_type': 'authorization_code',
                'code': code,
                'app_id': self.app_id,
                'redirect_uri': self.redirect_uri
            })
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data
            return None
            
        except Exception as e:
            st.error(f"Error during OAuth: {str(e)}")
            return None

def generate_oauth_url(state: str = None) -> Tuple[str, str]:
    """
    Generate the OAuth URL for Deriv authentication
    
    Args:
        state: Optional state parameter for CSRF protection
        
    Returns:
        Tuple of (oauth_url, state)
    """
    if state is None:
        state = secrets.token_hex(16)
        
    params = {
        "app_id": APP_ID,
        "l": "EN",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state
    }
    
    # Build the query string
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    oauth_url = f"{OAUTH_BASE_URL}?{query_string}"
    
    return oauth_url, state

def redirect_to_deriv_signup():
    """Redirect user to Deriv signup page silently"""
    # Store state in session for verification when the user returns
    state = secrets.token_hex(16)
    st.session_state.oauth_state = state
    
    # First, redirect to the Deriv signup page
    signup_url = "https://hub.deriv.com/tradershub/signup"
    
    # Create JavaScript to redirect the user
    js = f"""
    <script>
    window.location.href = "{signup_url}";
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)

def redirect_to_oauth():
    """Redirect user to Deriv OAuth authorization silently"""
    # Generate OAuth URL and state
    oauth_url, state = generate_oauth_url()
    
    # Store state in session for verification when the user returns
    st.session_state.oauth_state = state
    
    # Create JavaScript to redirect the user
    js = f"""
    <script>
    window.location.href = "{oauth_url}";
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)

def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """
    Exchange an authorization code for an access token
    
    Args:
        code: The authorization code from Deriv
        
    Returns:
        Dictionary with token information or error
    """
    data = {
        "grant_type": "authorization_code",
        "client_id": APP_ID,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    try:
        response = requests.post(TOKEN_URL, data=data)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def handle_oauth_flow():
    """Handle the complete OAuth flow"""
    # Use the query_params API
    if 'code' in st.experimental_get_query_params():
        code = st.experimental_get_query_params()['code']
        oauth = DerivOAuth()
        token_data = oauth.handle_oauth_callback(code)
        
        if token_data:
            # Store token in user's profile
            current_user = auth_api.get_current_user()
            if current_user:
                auth_api.update_deriv_token(current_user['email'], token_data)
                
                # Fetch account balances
                balances = fetch_account_balances(token_data['access_token'])
                if balances:
                    auth_api.update_account_balances(current_user['email'], balances)
                
                # Clear query parameters and redirect to main page
                st.experimental_get_query_params().clear()
                st.rerun()
            else:
                st.error("User not authenticated")
        else:
            st.error("Failed to get access token")

def check_oauth_callback() -> bool:
    """
    Check if the current request is an OAuth callback and handle it
    
    Returns:
        True if this was an OAuth callback and it was handled successfully
    """
    query_params = st.experimental_get_query_params()
    if 'code' in query_params or 'error' in query_params:
        token_info = handle_oauth_callback()
        return token_info is not None
    
    return False

def handle_oauth_callback() -> Optional[Dict[str, Any]]:
    """
    Handle the OAuth callback from Deriv
    
    Returns:
        Token information if successful, None otherwise
    """
    # Check for errors
    if 'error' in st.experimental_get_query_params():
        st.error(f"OAuth error: {st.experimental_get_query_params()['error']}")
        return None
    
    # Check for authorization code
    if 'code' not in st.experimental_get_query_params():
        return None
    
    # Verify state parameter to prevent CSRF attacks
    state = st.experimental_get_query_params().get('state')
    saved_state = st.session_state.get('oauth_state')
    
    if not state or state != saved_state:
        st.error("Invalid state parameter")
        return None
    
    # Exchange code for token
    code = st.experimental_get_query_params()['code']
    token_info = exchange_code_for_token(code)
    
    if 'error' in token_info:
        st.error(f"Token error: {token_info['error']}")
        return None
    
    # Clear the state parameter
    if 'oauth_state' in st.session_state:
        del st.session_state.oauth_state
    
    # Store the token info in session state
    st.session_state.deriv_token = token_info
    st.session_state.deriv_connected = True
    
    return token_info

def is_connected_to_deriv() -> bool:
    """
    Check if the user is connected to Deriv
    
    Returns:
        True if connected to Deriv
    """
    return bool(st.session_state.get('deriv_token')) and bool(st.session_state.get('deriv_connected', False))

def get_token() -> Optional[str]:
    """
    Get the Deriv access token if available
    
    Returns:
        Access token if available, None otherwise
    """
    token_info = st.session_state.get('deriv_token')
    if token_info and 'access_token' in token_info:
        return token_info['access_token']
    return None

def disconnect_from_deriv():
    """Disconnect from Deriv by removing the token"""
    if 'deriv_token' in st.session_state:
        del st.session_state.deriv_token
    
    st.session_state.deriv_connected = False
    
    # Also remove from user data
    if (is_authenticated := st.session_state.get('is_authenticated', False)) and 'current_user' in st.session_state:
        user_email = st.session_state.current_user
        if 'users' in st.session_state and user_email in st.session_state.users:
            if 'deriv_token' in st.session_state.users[user_email]:
                del st.session_state.users[user_email]['deriv_token']

def fetch_account_balances(access_token: str) -> Optional[Dict]:
    """Fetch account balances from Deriv API"""
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Get list of accounts
        accounts_url = "https://api.deriv.com/api/v3/accounts"
        response = requests.get(accounts_url, headers=headers)
        
        if response.status_code == 200:
            accounts_data = response.json()
            
            # Process account balances
            balances = {
                'demo': {},
                'real': {}
            }
            
            for account in accounts_data.get('accounts', []):
                account_type = 'demo' if account.get('is_virtual') else 'real'
                account_id = account.get('loginid')
                
                if account_id:
                    balances[account_type][account_id] = {
                        'balance': account.get('balance', 0.0),
                        'currency': account.get('currency', 'USD'),
                        'name': account.get('account_type', 'Unknown')
                    }
            
            return balances
            
        return None
        
    except Exception as e:
        st.error(f"Error fetching account balances: {str(e)}")
        return None

def get_current_balance(account_type: str = 'demo') -> float:
    """Get current balance for specified account type"""
    current_user = auth_api.get_current_user()
    if not current_user or not current_user.get('account_balances'):
        return 0.0
        
    balances = current_user.get('account_balances', {}).get(account_type, {})
    if not balances:
        return 0.0
        
    # Return the sum of all account balances for the specified type
    return sum(account.get('balance', 0.0) for account in balances.values())

def is_deriv_connected() -> bool:
    """Check if user is connected to Deriv"""
    current_user = auth_api.get_current_user()
    return bool(current_user and current_user.get('deriv_token'))