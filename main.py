import streamlit as st

# Set page config FIRST - must be the first Streamlit command
st.set_page_config(
    page_title="Trading Analyzer",
    page_icon="📈",
    layout="wide"
)

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import time
import secrets
import threading
import os
import websocket
from probability_calculator import ProbabilityCalculator, MarketAnalyzer
from strategy_engine import StrategyEngine
from bot_config_parser import BotConfigParser
from broker_api import create_broker_api
from utils import generate_robot_svg, apply_conditional_formatting
from auth_utils import (
    auth_api, 
    UserRole, 
    initialize_auth_state,
    login_user,
    register_user,
    verify_token
)
from admin_dashboard import show_admin_dashboard
from deriv_oauth import DerivOAuth, handle_oauth_flow, is_deriv_connected, get_current_balance, check_oauth_callback, get_token
from auth_pages import show_admin_login_ui, show_user_login_ui, show_admin_panel, show_user_dashboard
from ai_bot_trading import VolatilityAutoScanner, MultiStrategySignalEngine, SmartRiskEngine, LearningMemorySystem

# Function to show Deriv connection status
def show_deriv_status():
    """Display Deriv connection status in the sidebar"""
    if st.session_state.get('deriv_connected', False):
        st.sidebar.success("Connected to Deriv")
        if 'account_info' in st.session_state:
            account_info = st.session_state.account_info
            st.sidebar.markdown("### Account Info")
            st.sidebar.markdown(f"**Balance:** ${account_info.get('balance', 0.0):.2f}")
            st.sidebar.markdown(f"**Account Type:** {'Demo' if account_info.get('is_demo', True) else 'Real'}")
            st.sidebar.markdown(f"**Account ID:** {account_info.get('id', 'Unknown')}")
            
            # Fetch and display available balances
            try:
                if hasattr(st.session_state, 'broker_api'):
                    balances = st.session_state.broker_api.get_available_balances()
                    if balances:
                        st.sidebar.markdown("### Available Balances")
                        for currency, amount in balances.items():
                            st.sidebar.markdown(f"**{currency}:** ${amount:.2f}")
            except Exception as e:
                st.sidebar.error(f"Error fetching balances: {str(e)}")
    else:
        st.sidebar.warning("Not connected to Deriv")
        if st.sidebar.button("Connect to Deriv", key="connect_deriv_btn"):
            # Redirect to Deriv OAuth with proper parameters
            app_id = "105016"
            base_url = "https://05fd-102-219-210-201.ngrok-free.app/callback"
            redirect_uri = f"{base_url}/dashboard"  # Redirect directly to dashboard
            
            # Construct OAuth URL with all required parameters
            oauth_params = {
                "app_id": app_id,
                "l": "EN",  # Language
                "brand": "deriv",  # Brand
                "date_first_contact": datetime.now().strftime("%Y-%m-%d"),  # First contact date
                "signup_device": "desktop",  # Signup device
                "redirect_uri": redirect_uri
            }
            
            # Build the OAuth URL
            oauth_url = "https://oauth.deriv.com/oauth2/authorize?" + "&".join(
                f"{key}={value}" for key, value in oauth_params.items()
            )
            
            # Redirect to OAuth
            st.markdown(f'<meta http-equiv="refresh" content="0;url={oauth_url}">', unsafe_allow_html=True)

# Function to fetch and update balances
def update_balances():
    """Fetch and update available balances"""
    if st.session_state.get('deriv_connected', False) and hasattr(st.session_state, 'broker_api'):
        try:
            balances = st.session_state.broker_api.get_available_balances()
            st.session_state.available_balances = balances
            return balances
        except Exception as e:
            st.error(f"Error fetching balances: {str(e)}")
            return None
    return None

# Function to show user dashboard
def show_user_dashboard():
    """Display the user dashboard"""
    # Title and description with logo
    col1, col2 = st.columns([1, 6])

    with col1:
        st.markdown(generate_robot_svg(), unsafe_allow_html=True)

    with col2:
        st.title("Trading Dashboard")
        st.markdown("""
        Monitor and analyze your trading performance with our advanced tools.
        """)
    
    # Create tab layout
    tabs = st.tabs([
        "Trading",
        "Market Analysis",
        "Strategy",
        "Risk Management",
        "AI Bot Trading",
        "Bot Management",
        "Performance Analysis",
        "AI Bot Live"
    ])

    # Trading Tab
    with tabs[0]:
        st.header("Trading")
        
        # Check if connected to Deriv
        if not st.session_state.get('deriv_connected', False):
            st.info("Please connect your Deriv account in the Profile section to start trading")
        else:
            # Trading interface
            st.subheader("Active Trading")
            
            # Market selection
            market = st.selectbox(
                "Select Market",
                ["R_10", "R_25", "R_50", "R_75", "R_100"],
                key="market_selector"
            )
            
            # Trade type selection
            trade_type = st.selectbox(
                "Select Trade Type",
                ["DIGITEVEN", "DIGITODD", "DIGITOVER", "DIGITUNDER"],
                key="trade_type_selector"
            )
            
            # Stake amount
            stake = st.number_input(
                "Stake Amount",
                min_value=1.0,
                max_value=1000.0,
                value=1.0,
                step=1.0,
                key="stake_input"
            )
            
            # Place trade button
            if st.button("Place Trade", key="place_trade_btn"):
                if st.session_state.get('deriv_connected', False):
                    try:
                        # Place trade logic here
                        st.success("Trade placed successfully!")
                    except Exception as e:
                        st.error(f"Error placing trade: {str(e)}")
                else:
                    st.error("Please connect your Deriv account first")
            
            # Recent trades
            st.subheader("Recent Trades")
            if st.session_state.trade_history:
                trade_df = pd.DataFrame(st.session_state.trade_history)
                st.dataframe(trade_df.tail(10), use_container_width=True)
            else:
                st.info("No recent trades")

    # Market Analysis Tab
    with tabs[1]:
        st.header("Market Analysis")
        # Market analysis content

    # Strategy Tab
    with tabs[2]:
        st.header("Strategy")
        # Strategy content

    # Risk Management Tab
    with tabs[3]:
        st.header("Risk Management")
        # Risk management content

    # AI Bot Trading Tab
    with tabs[4]:
        st.header("AI Bot Trading")
        # AI bot trading content

    # Bot Management Tab
    with tabs[5]:
        st.header("Bot Management")
        # Bot management content

    # Performance Analysis Tab
    with tabs[6]:
        st.header("Performance Analysis")
        # Performance analysis content

    # AI Bot Live Tab
    with tabs[7]:
        st.header("AI Bot Live")
        # AI bot live content

# Function to show user profile
def show_user_profile():
    """Display user profile information"""
    st.title("My Profile")
    
    # Deriv Connection Section
    st.markdown("### Deriv Account Connection")
    
    if not st.session_state.get('deriv_connected', False):
        st.warning("Not connected to Deriv")
        st.markdown("""
        Connect your Deriv account to:
        - Access your trading account information
        - View your account balances
        - Monitor your trading performance
        - Execute trades (if enabled)
        """)
        
        if st.button("Connect to Deriv", key="profile_connect_deriv"):
            # Redirect to Deriv OAuth with proper parameters
            app_id = "105016"
            base_url = "https://05fd-102-219-210-201.ngrok-free.app/callback"
            redirect_uri = f"{base_url}/dashboard"
            
            # Construct OAuth URL with all required parameters
            oauth_params = {
                "app_id": app_id,
                "l": "EN",
                "brand": "deriv",
                "date_first_contact": datetime.now().strftime("%Y-%m-%d"),
                "signup_device": "desktop",
                "redirect_uri": redirect_uri
            }
            
            # Build the OAuth URL
            oauth_url = "https://oauth.deriv.com/oauth2/authorize?" + "&".join(
                f"{key}={value}" for key, value in oauth_params.items()
            )
            
            # Redirect to OAuth
            st.markdown(f'<meta http-equiv="refresh" content="0;url={oauth_url}">', unsafe_allow_html=True)
    else:
        st.success("Connected to Deriv")
        
        # Show account information
        if 'account_info' in st.session_state:
            account_info = st.session_state.account_info
            
            # Account Details
            st.markdown("#### Account Details")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Account ID:** {account_info.get('id', 'Unknown')}")
                st.markdown(f"**Account Type:** {'Demo' if account_info.get('is_demo', True) else 'Real'}")
                st.markdown(f"**Balance:** ${account_info.get('balance', 0.0):.2f}")
            
            with col2:
                st.markdown(f"**Name:** {account_info.get('name', 'Unknown')}")
                st.markdown(f"**Email:** {account_info.get('email', 'Unknown')}")
                st.markdown(f"**Currency:** {account_info.get('currency', 'USD')}")
            
            # Account Switching
            if hasattr(st.session_state.broker_api, 'accounts') and st.session_state.broker_api.accounts:
                st.markdown("#### Available Accounts")
                
                # Separate Demo and Real accounts
                demo_accounts = []
                real_accounts = []
                
                for account in st.session_state.broker_api.accounts:
                    account_id = account.get('loginid', 'Unknown')
                    account_type = "Demo" if account.get('is_virtual', True) else "Real"
                    currency = account.get('currency', 'USD')
                    balance = account.get('balance', 0.0)
                    account_info = f"{account_id} ({currency} - ${balance:.2f})"
                    
                    if account.get('is_virtual', True):
                        demo_accounts.append((account_id, account_info))
                    else:
                        real_accounts.append((account_id, account_info))
                
                # Display Demo Accounts
                if demo_accounts:
                    st.markdown("##### Demo Accounts")
                    demo_cols = st.columns([3, 1])
                    with demo_cols[0]:
                        selected_demo = st.selectbox(
                            "Select Demo Account",
                            range(len(demo_accounts)),
                            format_func=lambda i: demo_accounts[i][1],
                            key="profile_demo_account_selector"
                        )
                    with demo_cols[1]:
                        if st.button("Switch to Demo", key="profile_switch_demo_btn"):
                            selected_id = demo_accounts[selected_demo][0]
                            if st.session_state.broker_api.switch_account(selected_id):
                                st.success(f"Switched to demo account {selected_id}")
                                account_info = st.session_state.broker_api.get_account_info()
                                st.session_state.account_info = account_info
                                st.rerun()
                            else:
                                st.error("Failed to switch to demo account")
                
                # Display Real Accounts
                if real_accounts:
                    st.markdown("##### Real Accounts")
                    real_cols = st.columns([3, 1])
                    with real_cols[0]:
                        selected_real = st.selectbox(
                            "Select Real Account",
                            range(len(real_accounts)),
                            format_func=lambda i: real_accounts[i][1],
                            key="profile_real_account_selector"
                        )
                    with real_cols[1]:
                        if st.button("Switch to Real", key="profile_switch_real_btn"):
                            selected_id = real_accounts[selected_real][0]
                            if st.session_state.broker_api.switch_account(selected_id):
                                st.success(f"Switched to real account {selected_id}")
                                account_info = st.session_state.broker_api.get_account_info()
                                st.session_state.account_info = account_info
                                st.rerun()
                            else:
                                st.error("Failed to switch to real account")
        
        # Disconnect Deriv
        st.markdown("---")
        if st.button("Disconnect Deriv Account", key="profile_disconnect_deriv"):
            st.session_state.deriv_connected = False
            st.session_state.broker_api = None
            st.session_state.account_info = None
            st.rerun()

# Function to display the main application
def main():
    # Initialize session state variables
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    if 'available_balances' not in st.session_state:
        st.session_state.available_balances = {}
    if 'deriv_connected' not in st.session_state:
        st.session_state.deriv_connected = False
    if 'account_info' not in st.session_state:
        st.session_state.account_info = None
    if 'broker_api' not in st.session_state:
        st.session_state.broker_api = None

    # Navigation
    st.sidebar.markdown("## Navigation")
    
    # Navigation buttons
    if st.sidebar.button("📊 Trading Dashboard", key="nav_dashboard_btn"):
        st.session_state.page = 'dashboard'
        st.rerun()
        
    if st.sidebar.button("👤 My Profile", key="nav_profile_btn"):
        st.session_state.page = 'profile'
        st.rerun()
    
    # Show Deriv connection status in sidebar
    show_deriv_status()
    
    # Update balances periodically if connected
    if st.session_state.get('deriv_connected', False):
        update_balances()
    
    # Display trading dashboard by default
    show_user_dashboard()

# Check for OAuth callback before anything else
if check_oauth_callback():
    # Try to connect with the obtained token
    token = get_token()
    if token:
        app_id = "105016"
        try:
            broker_api = create_broker_api("deriv", app_id=app_id)
            if broker_api.connect_with_token(token):
                st.session_state.broker_api = broker_api
                st.session_state.deriv_connected = True
                
                # Get and store account info
                account_info = broker_api.get_account_info()
                st.session_state.account_info = account_info
                
                # Set page to dashboard and rerun
                st.session_state.page = 'dashboard'
                st.rerun()
        except Exception as e:
            st.error(f"Error connecting to Deriv: {str(e)}")
            # Set page to dashboard even if there's an error
            st.session_state.page = 'dashboard'
            st.rerun()

if __name__ == "__main__":
    main()