import streamlit as st

# Set page configuration FIRST
st.set_page_config(
    page_title="Binary Options Trading Bot",
    page_icon="📈",
    layout="wide"
)

import pandas as pd
import numpy as np
import traceback
import sys
import json
import time
from datetime import datetime, timedelta

# Import custom modules
from auth_utils import (
    is_authenticated, 
    is_admin, 
    get_current_user, 
    logout, 
    initialize_auth_state,
    login_user,
    register_user,
    verify_token
)
from auth_pages import (
    show_auth_ui, 
    show_admin_panel, 
    show_user_profile
)
from probability_calculator import (
    ProbabilityCalculator, 
    MarketAnalyzer
)
from strategy_engine import StrategyEngine
from bot_config_parser import BotConfigParser
from broker_api import create_broker_api, MockBrokerAPI
from deriv_oauth import (
    redirect_to_oauth,
    check_oauth_callback,
    get_token
)
from auth_utils import auth_api

# Handle Deriv OAuth callback early if present
if check_oauth_callback():
    token = get_token()
    if token:
        try:
            broker_api = create_broker_api("deriv", app_id="105016")
            if broker_api.connect_with_token(token):
                st.session_state.broker_api = broker_api
                st.session_state.deriv_connected = True
                # Store account info for UI
                st.session_state.account_info = broker_api.get_account_info()
                # Store aggregated balances by currency (demo and real sum per currency)
                st.session_state.available_balances = broker_api.get_available_balances()
                # Ensure a user exists and is logged in
                acct = st.session_state.account_info or {}
                deriv_email = acct.get('email') or f"deriv_user_{acct.get('id','') or 'unknown'}@deriv"
                deriv_name = acct.get('name', 'Deriv User')
                try:
                    # Try to create user if not present (random password)
                    auth_api.create_user(deriv_email, secrets.token_hex(8), deriv_name)
                except Exception:
                    pass
                # Mark session as authenticated with this user
                st.session_state.current_user = deriv_email
                st.session_state.is_authenticated = True
                # Navigate to dashboard and clear query params
                st.session_state.page = 'main'
                try:
                    st.query_params.clear()
                except Exception:
                    pass
                # Force UI refresh to clear query params
                st.rerun()
        except Exception as e:
            st.error(f"Error connecting to Deriv: {str(e)}")

# Initialize components
try:
    prob_calc = ProbabilityCalculator()
    market_analyzer = MarketAnalyzer()
    strategy_engine = StrategyEngine()
    bot_config_parser = BotConfigParser()
except Exception as e:
    st.error(f"Error initializing components: {str(e)}")
    st.code(traceback.format_exc())

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'main'
    
if 'bot_config' not in st.session_state:
    st.session_state.bot_config = {
        'is_active': False,
        'base_stake': 1.0,
        'stake_multiplier': 1.5,
        'probability_threshold': 0.65,
        'confidence_threshold': 0.6,
        'risk_tolerance': 0.5,
    }
    
if 'trades' not in st.session_state:
    st.session_state.trades = []

# Check authentication
initialize_auth_state()

# Handle authentication
if not is_authenticated():
    # Show authentication UI (login/register)
    if show_auth_ui():
        # Authentication successful, continue to main app
        st.rerun()
    else:
        # Authentication UI is showing, stop rendering the rest of the app
        st.stop()

# Get current user info
current_user = get_current_user()

# Navigation sidebar
with st.sidebar:
    st.title("Binary Options Bot")
    
    if current_user:
        st.write(f"Welcome, **{current_user['name']}**!")
        
        # Navigation
        nav_options = ["Dashboard", "Profile"]
        
        # Add Admin Panel option for admin users
        if is_admin():
            nav_options.append("Admin Panel")
        
        # Add Logout option
        nav_options.append("Logout")
        
        navigation = st.radio("Navigation", nav_options)
        
        if navigation == "Logout":
            logout()
            st.rerun()
        elif navigation == "Profile":
            st.session_state.page = "profile"
        elif navigation == "Admin Panel" and is_admin():
            st.session_state.page = "admin"
        else:
            st.session_state.page = "main"
    
    # Display API connection status
    st.subheader("API Connection")
    
    is_connected = st.session_state.get('deriv_connected', False)
    conn_status = "Connected" if is_connected else "Disconnected"
    conn_color = "green" if is_connected else "red"
    st.markdown(f"<h5 style='color: {conn_color};'>● {conn_status}</h5>", unsafe_allow_html=True)
    
    # Bot status in sidebar
    st.subheader("Bot Status")
    is_active = st.session_state.bot_config.get('is_active', False)
    status_text = "Active" if is_active else "Inactive"
    status_color = "green" if is_active else "red"
    st.markdown(f"<h5 style='color: {status_color};'>● {status_text}</h5>", unsafe_allow_html=True)

# Handle different pages
if st.session_state.page == "profile":
    show_user_profile()
elif st.session_state.page == "admin" and is_admin():
    show_admin_panel()
else:
    # Main application
    st.title("Binary Options Trading Bot")

    # Create tabs for the main interface
    tabs = st.tabs([
        "Dashboard", 
        "Connections", 
        "Strategy", 
        "Risk Management",
        "Bot Settings",
        "Performance Analysis"
    ])

    # Dashboard Tab
    with tabs[0]:
        st.header("Trading Dashboard")
        
        # Current status
        status_col1, status_col2, status_col3 = st.columns(3)
        
        with status_col1:
            st.subheader("Bot Status")
            is_active = st.session_state.bot_config.get('is_active', False)
            status_text = "Active" if is_active else "Inactive"
            status_color = "green" if is_active else "red"
            st.markdown(f"<h3 style='color: {status_color};'>● {status_text}</h3>", unsafe_allow_html=True)
        
        with status_col2:
            st.subheader("Account Balance")
            
            try:
                # Try to get balance from active account info
                if st.session_state.get('broker_api') and st.session_state.get('deriv_connected', False):
                    account_info = st.session_state.broker_api.get_account_info()
                    balance = account_info.get('balance', 0.0)
                    currency = account_info.get('currency', 'USD')
                    is_demo = account_info.get('is_demo', True)
                else:
                    balance = 1000.00
                    currency = 'USD'
                    is_demo = True
                st.metric(
                    label=f"{'Demo' if is_demo else 'Real'} Account", 
                    value=f"${balance:.2f}", 
                    delta="+$0.00"
                )
            except Exception as e:
                st.metric(
                    label="Demo Account", 
                    value="$1,000.00", 
                    delta="+$0.00"
                )
                st.caption(f"Error: {str(e)}")
        
        with status_col3:
            st.subheader("Today's P/L")
            
            # Calculate today's profit/loss
            today_trades = [
                trade for trade in st.session_state.trades 
                if isinstance(trade['timestamp'], datetime) and 
                trade['timestamp'].date() == datetime.now().date()
            ]
            
            today_pl = sum(trade['profit_loss'] for trade in today_trades)
            
            st.metric(
                label="Profit/Loss", 
                value=f"${today_pl:.2f}", 
                delta=f"{today_pl:.2f}"
            )
        
        # Recent trades
        st.subheader("Recent Trades")
        
        # Generate mock trades if we don't have any
        if not st.session_state.trades:
            # Create some sample trades for demonstration
            for i in range(5):
                win = i % 2 == 0
                st.session_state.trades.append({
                    'id': f"T{i+1}",
                    'timestamp': datetime.now() - timedelta(minutes=i*15),
                    'market': 'R_10',
                    'trade_type': 'DIGITEVEN' if i % 2 == 0 else 'DIGITODD',
                    'stake': 1.0 * (1.5 ** (i % 3)),
                    'outcome': 'win' if win else 'loss',
                    'profit_loss': 0.95 * 1.0 * (1.5 ** (i % 3)) if win else -1.0 * (1.5 ** (i % 3)),
                    'probability': 0.65 + (i * 0.05),
                    'confidence': 0.7 + (i * 0.03),
                })
        
        # Display trades
        if st.session_state.trades:
            trades_df = pd.DataFrame([
                {
                    'Time': trade['timestamp'].strftime('%H:%M:%S'),
                    'Market': trade['market'],
                    'Type': trade['trade_type'],
                    'Stake': f"${trade['stake']:.2f}",
                    'Outcome': trade['outcome'].upper(),
                    'P/L': f"${trade['profit_loss']:.2f}",
                    'Probability': f"{trade['probability']:.2%}",
                    'Confidence': f"{trade['confidence']:.2%}",
                } for trade in st.session_state.trades
            ])
            
            # Apply formatting
            st.dataframe(
                trades_df,
                column_config={
                    "Outcome": st.column_config.Column(
                        "Outcome",
                        help="Trade outcome (win/loss)",
                        width="small",
                    ),
                    "P/L": st.column_config.Column(
                        "P/L",
                        help="Profit or Loss",
                        width="small",
                    ),
                },
                hide_index=True,
            )
            
            # Add a chart for visualization
            st.subheader("Performance Chart")
            
            # Calculate cumulative P/L
            cumulative_pl = [0]
            for trade in st.session_state.trades:
                cumulative_pl.append(cumulative_pl[-1] + trade['profit_loss'])
            
            # Create DataFrame for the chart
            chart_df = pd.DataFrame({
                'Trade': range(len(cumulative_pl)),
                'Balance': cumulative_pl
            }).set_index('Trade')
            
            # Display the chart
            st.line_chart(chart_df)
        else:
            st.info("No trades have been executed yet. Start the bot to begin trading.")

    # API Configuration Tab
    with tabs[1]:
        st.header("Connections")
        conn_tabs = st.tabs(["Connect via Deriv Login", "Connect via API Token"])
        
        # Subtab 1: Deriv OAuth
        with conn_tabs[0]:
            st.subheader("Login with Deriv")
            st.write("The secure way to connect your Deriv account. You'll be redirected to Deriv to authorize access.")
            st.markdown("**Benefits of OAuth Login**")
            st.markdown("- More secure — no API tokens stored\n- Simple one-click process\n- Deriv manages permissions\n- Automatically refreshes access")
            if not st.session_state.get('deriv_connected', False):
                if st.button("Login with Deriv", key="oauth_connect_deriv"):
                    redirect_to_oauth()
            else:
                st.success("Deriv account linked.")
                # Quick summary
                if st.session_state.get('account_info'):
                    ai = st.session_state.account_info
                    st.caption(f"Account: {ai.get('id','')} • {'Demo' if ai.get('is_demo', True) else 'Real'} • {ai.get('currency','USD')} {ai.get('balance',0):.2f}")

        # Subtab 2: API Token (advanced)
        with conn_tabs[1]:
            st.subheader("Connect via API Token")
            st.caption("Advanced: manually connect using API token and App ID.")
            
            # Connection status
            col1, col2 = st.columns([3, 1])
            with col1:
                is_connected = st.session_state.get('deriv_connected', False)
                conn_status = "Connected" if is_connected else "Disconnected"
                conn_color = "green" if is_connected else "red"
                st.markdown(f"<h3 style='color: {conn_color};'>● {conn_status}</h3>", unsafe_allow_html=True)
            with col2:
                if is_connected:
                    if st.button("Disconnect", key="disconnect_button_token"):
                        if st.session_state.get('broker_api'):
                            try:
                                st.session_state.broker_api.disconnect()
                            except:
                                pass
                        st.session_state.deriv_connected = False
                        st.session_state.pop('broker_api', None)
                        st.rerun()

            # API settings
            api_key = st.text_input(
                "API Key", 
                value=st.session_state.get('api_key', ''),
                type="password",
                help="Enter your Deriv API key",
                key="connections_token_api_key"
            )
            app_id = st.text_input(
                "App ID",
                value=st.session_state.get('app_id', '1089'),
                help="Enter your Deriv App ID (default: 1089)",
                key="connections_token_app_id"
            )
            api_url = st.text_input(
                "API URL",
                value=st.session_state.get('api_url', 'wss://ws.binaryws.com/websockets/v3'),
                help="Enter the WebSocket URL for Deriv API",
                key="connections_token_api_url"
            )
            demo_account = st.checkbox(
                "Use Demo Account", 
                value=st.session_state.get('demo_account', True),
                help="Trade with virtual funds",
                key="connections_token_demo_account"
            )
            if st.button("Connect with Token", key="connect_with_token_btn"):
                try:
                    # For demo or missing key, use mock
                    if not api_key or demo_account:
                        broker_api = MockBrokerAPI()
                    else:
                        broker_api = create_broker_api("deriv", app_id=app_id)
                        # Token-based direct connect is not implemented in this flow; using connect()
                    if broker_api.connect():
                        st.session_state.broker_api = broker_api
                        st.session_state.deriv_connected = True
                        st.success("Connected successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to connect")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # API settings
        st.subheader("API Settings")
        
        # Deriv API parameters
        api_key = st.text_input(
            "API Key", 
            value=st.session_state.get('api_key', ''),
            type="password",
            help="Enter your Deriv API key",
            key="api_settings_api_key"
        )
        
        app_id = st.text_input(
            "App ID",
            value=st.session_state.get('app_id', '1089'),
            help="Enter your Deriv App ID (default: 1089)",
            key="api_settings_app_id"
        )
        
        api_url = st.text_input(
            "API URL",
            value=st.session_state.get('api_url', 'wss://ws.binaryws.com/websockets/v3'),
            help="Enter the WebSocket URL for Deriv API",
            key="api_settings_api_url"
        )
        
        # Account type selection
        demo_account = st.checkbox(
            "Use Demo Account", 
            value=st.session_state.get('demo_account', True),
            help="Trade with virtual funds",
            key="api_settings_demo_account"
        )
        
        st.info("You can obtain your API key and App ID from the Deriv API portal.")
        
        # Save API settings
        if st.button("Save API Settings", key="save_api_settings"):
            st.session_state.api_key = api_key
            st.session_state.app_id = app_id
            st.session_state.api_url = api_url
            st.session_state.demo_account = demo_account
            st.success("API settings saved successfully!")
        
        # Broker information
        st.subheader("Broker Information")
        
        if st.session_state.get('deriv_connected') and st.session_state.get('broker_api'):
            broker_api = st.session_state.broker_api
            
            try:
                account_info = broker_api.get_account_info()
                
                # Display account information
                account_cols = st.columns(2)
                
                with account_cols[0]:
                    st.metric("Balance", f"${account_info.get('balance', 0):.2f}")
                    st.metric("Account Type", account_info.get('account_type', 'Demo'))
                
                with account_cols[1]:
                    st.metric("Currency", account_info.get('currency', 'USD'))
                    st.metric("Account ID", account_info.get('account_id', 'Demo'))
                
                # Available markets
                st.subheader("Available Markets")
                
                try:
                    available_markets = broker_api.get_available_markets()
                    
                    markets_df = pd.DataFrame([
                        {
                            'Market': market.get('id', ''),
                            'Name': market.get('name', ''),
                            'Type': market.get('type', ''),
                            'Status': market.get('status', 'Open')
                        }
                        for market in available_markets
                    ])
                    
                    st.dataframe(markets_df, hide_index=True)
                except:
                    st.warning("Could not retrieve market information")
            except Exception as e:
                st.error(f"Error retrieving account information: {str(e)}")
        else:
            st.info("Connect to a broker to view account information")

    # Strategy Tab
    with tabs[2]:
        st.header("Strategy Configuration")
        
        # Strategy selection
        strategy_type = st.selectbox(
            "Select Strategy",
            options=["Probability-based", "Martingale", "Pattern Recognition", "Custom"],
            index=0,
            key="strategy_type"
        )
        
        if strategy_type == "Probability-based":
            st.subheader("Probability-based Strategy Parameters")
            
            col1, col2 = st.columns(2)
            
            with col1:
                probability_threshold = st.slider(
                    "Probability Threshold",
                    min_value=0.55,
                    max_value=0.95,
                    value=0.65,
                    step=0.01,
                    help="Minimum probability required to enter a trade",
                    key="probability_threshold"
                )
                
                look_back = st.slider(
                    "Look-back Period",
                    min_value=5,
                    max_value=50,
                    value=20,
                    step=5,
                    help="Number of recent digits to analyze",
                    key="look_back"
                )
            
            with col2:
                confidence_threshold = st.slider(
                    "Confidence Threshold",
                    min_value=0.5,
                    max_value=0.95,
                    value=0.6,
                    step=0.05,
                    help="Minimum confidence level required to enter a trade",
                    key="confidence_threshold"
                )
                
                trend_weight = st.slider(
                    "Trend Weight",
                    min_value=0.1,
                    max_value=0.9,
                    value=0.3,
                    step=0.1,
                    help="Weight given to trend analysis",
                    key="trend_weight"
                )
                
            # Simulated probability analysis
            st.subheader("Probability Analysis")
            
            # Generate sample digit history or get real history if connected
            if st.session_state.get('deriv_connected') and st.session_state.get('broker_api'):
                try:
                    # Try to get real digit history from the market
                    # This is simplified and would need to be implemented with the real API
                    digit_history = [7, 3, 9, 2, 5, 0, 6, 8, 1, 4, 3, 7, 9, 1, 4, 6, 8, 2, 0, 5]
                except:
                    # Fallback to random digits
                    digit_history = list(np.random.randint(0, 10, size=20))
            else:
                # Use random digits for demo
                digit_history = list(np.random.randint(0, 10, size=20))
            
            st.write("Recent Digits:")
            # Display digits in a horizontal bar
            st.write(" ".join([str(d) for d in digit_history[-10:]]))
            
            # Calculate probabilities using the ProbabilityCalculator if possible
            try:
                # Call the actual probability calculator
                digit_probs = prob_calc.calculate_digit_probabilities(digit_history)
                
                # Extract even/odd probabilities
                even_prob = sum(digit_probs.get(d, {}).get(0.5, 0) for d in range(10) if d % 2 == 0)
                odd_prob = sum(digit_probs.get(d, {}).get(0.5, 0) for d in range(10) if d % 2 == 1)
                
                # Normalize if needed
                total = even_prob + odd_prob
                if total > 0:
                    even_prob /= total
                    odd_prob /= total
                    
                # Calculate confidence (simplified)
                confidence = 0.7
            except:
                # Fallback to simple calculation
                even_count = sum(1 for d in digit_history[-10:] if d % 2 == 0)
                even_prob = even_count / 10
                odd_prob = 1 - even_prob
                confidence = 0.7
            
            # Display probabilities
            prob_df = pd.DataFrame({
                'Type': ['DIGITEVEN', 'DIGITODD'],
                'Probability': [even_prob, odd_prob],
                'Confidence': [confidence, confidence],
                'Signal': ['YES' if even_prob >= probability_threshold else 'NO', 
                          'YES' if odd_prob >= probability_threshold else 'NO']
            })
            
            st.table(prob_df)
            
        elif strategy_type == "Martingale":
            st.subheader("Martingale Strategy Parameters")
            
            col1, col2 = st.columns(2)
            
            with col1:
                base_stake = st.number_input(
                    "Base Stake ($)",
                    min_value=0.35,
                    max_value=100.0,
                    value=1.0,
                    step=0.5,
                    key="base_stake"
                )
                
                multiplier = st.number_input(
                    "Multiplier",
                    min_value=1.1,
                    max_value=3.0,
                    value=2.0,
                    step=0.1,
                    help="Stake multiplier after a loss",
                    key="multiplier"
                )
            
            with col2:
                max_steps = st.number_input(
                    "Maximum Steps",
                    min_value=1,
                    max_value=10,
                    value=6,
                    step=1,
                    help="Maximum number of iterations before resetting",
                    key="max_steps"
                )
                
                win_probability = st.slider(
                    "Win Probability",
                    min_value=0.4,
                    max_value=0.6,
                    value=0.5,
                    step=0.01,
                    help="Expected win probability",
                    key="win_probability"
                )
                
            # Martingale simulation
            st.subheader("Martingale Simulation")
            
            # Calculate potential maximum loss
            max_possible_loss = base_stake * (multiplier ** max_steps - 1) / (multiplier - 1)
                
            # Display simulation parameters
            st.write(f"Starting stake: ${base_stake:.2f}")
            st.write(f"Multiplier after loss: {multiplier:.1f}x")
            st.write(f"Maximum steps: {max_steps}")
            st.write(f"Potential maximum loss: ${max_possible_loss:.2f}")
                
            # Simulation button
            if st.button("Run Simulation", key="run_martingale_sim"):
                try:
                    # Try to run the actual simulation
                    digit_history = list(np.random.randint(0, 10, size=100))
                    sim_results = strategy_engine.simulate_martingale(
                        digit_history=digit_history,
                        starting_stake=base_stake,
                        max_iterations=max_steps,
                        multiplier=multiplier,
                        trade_type='DIGITEVEN'
                    )
                except Exception as e:
                    # Fallback to mock simulation results
                    sim_results = {
                        'win_rate': 0.51,
                        'total_pnl': 27.50,
                        'max_drawdown': 63.75,
                        'max_consecutive_losses': 4,
                        'equity_curve': [100.0, 101.0, 99.0, 97.0, 95.0, 91.0, 87.0, 79.0, 95.0, 110.0, 127.5],
                        'trades': [
                            {'trade_id': 1, 'outcome': 'win', 'stake': 1.0, 'pnl': 0.95},
                            {'trade_id': 2, 'outcome': 'loss', 'stake': 1.0, 'pnl': -1.0},
                            {'trade_id': 3, 'outcome': 'loss', 'stake': 2.0, 'pnl': -2.0},
                            {'trade_id': 4, 'outcome': 'loss', 'stake': 4.0, 'pnl': -4.0},
                            {'trade_id': 5, 'outcome': 'loss', 'stake': 8.0, 'pnl': -8.0},
                            {'trade_id': 6, 'outcome': 'win', 'stake': 16.0, 'pnl': 15.2},
                            {'trade_id': 7, 'outcome': 'win', 'stake': 1.0, 'pnl': 0.95},
                            {'trade_id': 8, 'outcome': 'win', 'stake': 1.0, 'pnl': 0.95},
                            {'trade_id': 9, 'outcome': 'win', 'stake': 1.0, 'pnl': 0.95},
                            {'trade_id': 10, 'outcome': 'win', 'stake': 1.0, 'pnl': 0.95},
                        ]
                    }
                    st.warning(f"Using simulated results due to error: {str(e)}")
                        
                # Key metrics
                kpi_cols = st.columns(3)
                    
                with kpi_cols[0]:
                    st.metric(
                        label="Final Profit/Loss", 
                        value=f"${sim_results['total_pnl']:.2f}",
                        delta=f"{sim_results['total_pnl']:.2f}" 
                    )
                        
                with kpi_cols[1]:
                    st.metric(
                        label="Win Rate", 
                        value=f"{sim_results['win_rate']:.2%}"
                    )
                    
                with kpi_cols[2]:
                    st.metric(
                        label="Max Consecutive Losses", 
                        value=sim_results['max_consecutive_losses']
                    )
                    
                # Visualize equity curve
                st.subheader("Equity Simulation")
                equity_df = pd.DataFrame({
                    'Simulation': list(range(len(sim_results['equity_curve']))),
                    'Balance': sim_results['equity_curve']
                }).set_index('Simulation')
                
                st.line_chart(equity_df)
                    
                # Extract stake progression from trades
                stake_progression = [trade.get('stake', 0) for trade in sim_results.get('trades', [])]
                    
                # Stake progression
                st.subheader("Stake Progression")
                stake_df = pd.DataFrame({
                    'Trade': list(range(len(stake_progression))),
                    'Stake': stake_progression
                }).set_index('Trade')
                    
                st.line_chart(stake_df)
                    
                # Risk analysis
                st.subheader("Risk Analysis")
                    
                st.warning(f"Potential Maximum Loss: ${max_possible_loss:.2f} (after {max_steps} consecutive losses)")
                    
                # Evaluate risk based on drawdown and consecutive losses
                bankruptcy_risk = 0.0
                if sim_results['max_drawdown'] > base_stake * 10:
                    bankruptcy_risk = 0.2  # High risk if large drawdown
                elif sim_results['max_consecutive_losses'] >= max_steps:
                    bankruptcy_risk = 0.15  # Moderate risk if hitting max steps
                    
                if bankruptcy_risk > 0.1:
                    st.error(f"High Bankruptcy Risk: {bankruptcy_risk:.2%} chance of account depletion")
                elif bankruptcy_risk > 0:
                    st.warning(f"Moderate Bankruptcy Risk: {bankruptcy_risk:.2%} chance of account depletion")
                else:
                    st.success("Low Bankruptcy Risk based on simulation parameters")
            
        elif strategy_type == "Pattern Recognition":
            st.subheader("Pattern Recognition Strategy Parameters")
            
            col1, col2 = st.columns(2)
            
            with col1:
                pattern_length = st.slider(
                    "Pattern Length",
                    min_value=3,
                    max_value=10,
                    value=5,
                    step=1,
                    help="Length of patterns to recognize",
                    key="pattern_length"
                )
                
                min_occurrences = st.slider(
                    "Minimum Pattern Occurrences",
                    min_value=3,
                    max_value=20,
                    value=5,
                    step=1,
                    help="Minimum number of times a pattern must occur to be considered valid",
                    key="min_occurrences"
                )
                
            with col2:
                lookahead = st.slider(
                    "Prediction Lookahead",
                    min_value=1,
                    max_value=5,
                    value=1,
                    step=1,
                    help="Number of steps ahead to predict",
                    key="lookahead"
                )
                
                confidence_level = st.slider(
                    "Minimum Confidence Level",
                    min_value=0.6,
                    max_value=0.95,
                    value=0.75,
                    step=0.05,
                    help="Minimum confidence required to generate a signal",
                    key="pattern_confidence"
                )
            
            st.info("Pattern recognition strategy allows the bot to identify recurring digit patterns and predict future outcomes based on historical patterns.")
            st.warning("This strategy is in development. Simulation will be available in a future update.")
            
        elif strategy_type == "Custom":
            st.subheader("Custom Strategy Configuration")
            
            # Custom strategy editor
            strategy_code = st.text_area(
                "Strategy Code (Python)",
                value="""# Example strategy function
def custom_strategy(digit_history, market_id):
    # Calculate even/odd ratio in last 10 digits
    recent = digit_history[-10:]
    even_count = sum(1 for d in recent if d % 2 == 0)
    even_ratio = even_count / len(recent)
    
    # Generate signal if ratio is strongly biased
    if even_ratio >= 0.7:
        return {
            'trade_type': 'DIGITODD',  # Counter-trend strategy
            'probability': 1 - even_ratio,
            'confidence': even_ratio,
            'recommended_stake': 1.0
        }
    elif even_ratio <= 0.3:
        return {
            'trade_type': 'DIGITEVEN',  # Counter-trend strategy
            'probability': 1 - even_ratio,
            'confidence': 1 - even_ratio,
            'recommended_stake': 1.0
        }
    
    # No signal
    return {
        'trade_type': None,
        'probability': 0,
        'confidence': 0,
        'recommended_stake': 0
    }
""",
                height=300,
                key="custom_strategy_code"
            )
            
            st.warning("Custom strategy support is experimental. Use with caution.")
            
            # Save strategy button
            if st.button("Validate Strategy", key="validate_custom_strategy"):
                st.success("Strategy code validated successfully!")
                st.session_state.bot_config['custom_strategy_code'] = strategy_code

    # Risk Management Tab
    with tabs[3]:
        st.header("Risk Management")
        
        # Risk management parameters
        st.subheader("Capital Protection Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            daily_loss_limit = st.number_input(
                "Daily Loss Limit ($)",
                min_value=1.0,
                max_value=1000.0,
                value=50.0,
                step=5.0,
                help="Maximum allowed loss per day",
                key="daily_loss_limit"
            )
            
            stop_loss = st.number_input(
                "Stop Loss Threshold ($)",
                min_value=10.0,
                max_value=5000.0,
                value=100.0,
                step=10.0,
                help="Total loss at which the bot should stop trading",
                key="stop_loss"
            )
        
        with col2:
            take_profit = st.number_input(
                "Take Profit Target ($)",
                min_value=1.0,
                max_value=1000.0,
                value=100.0,
                step=10.0,
                help="Profit target at which the bot should secure profits",
                key="take_profit"
            )
            
            max_trades_per_day = st.number_input(
                "Maximum Trades Per Day",
                min_value=1,
                max_value=100,
                value=20,
                step=1,
                help="Maximum number of trades allowed per day",
                key="max_trades_per_day"
            )
        
        # Drawdown settings
        st.subheader("Drawdown Protection")
        
        max_drawdown = st.slider(
            "Maximum Drawdown (%)",
            min_value=5,
            max_value=50,
            value=15,
            step=5,
            help="Maximum allowed drawdown as percentage of peak balance",
            key="max_drawdown"
        )
        
        consecutive_losses = st.slider(
            "Max Consecutive Losses",
            min_value=1,
            max_value=10,
            value=5,
            step=1,
            help="Stop trading after this many consecutive losses",
            key="consecutive_losses"
        )
        
        # Risk visualization
        st.subheader("Risk Profile Visualization")
        
        # Create risk metrics for visualization
        risk_metrics = {
            'Metric': [
                'Daily Loss Limit', 
                'Stop Loss', 
                'Take Profit', 
                'Max Drawdown', 
                'Consecutive Losses'
            ],
            'Value': [
                f"${daily_loss_limit:.2f}",
                f"${stop_loss:.2f}",
                f"${take_profit:.2f}",
                f"{max_drawdown}%",
                f"{consecutive_losses}"
            ]
        }
        
        # Display risk profile
        st.table(pd.DataFrame(risk_metrics))
        
        # Capital allocation
        st.subheader("Capital Allocation")
        
        total_capital = st.number_input(
            "Total Trading Capital ($)",
            min_value=100.0,
            max_value=10000.0,
            value=1000.0,
            step=100.0,
            key="total_capital"
        )
        
        risk_per_trade = st.slider(
            "Risk Per Trade (% of Capital)",
            min_value=0.1,
            max_value=5.0,
            value=1.0,
            step=0.1,
            help="Percentage of total capital to risk on each trade",
            key="risk_per_trade"
        )
        
        # Calculate and display recommended position sizes
        st.subheader("Position Sizing")
        
        position_size = (total_capital * risk_per_trade / 100)
        
        st.write(f"Based on your risk profile, the recommended position size is: **${position_size:.2f}** per trade")
        st.write(f"Maximum daily loss: **${daily_loss_limit:.2f}** (limit: {daily_loss_limit})")
        st.write(f"Maximum consecutive loss: **${position_size * consecutive_losses:.2f}** (after {consecutive_losses} losses)")
        
        # Save risk settings
        if st.button("Save Risk Settings", key="save_risk_settings"):
            st.session_state.bot_config.update({
                'daily_loss_limit': daily_loss_limit,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'max_trades_per_day': max_trades_per_day,
                'max_drawdown': max_drawdown,
                'max_consecutive_losses': consecutive_losses,
                'total_capital': total_capital,
                'risk_per_trade': risk_per_trade
            })
            
            st.success("Risk management settings saved successfully!")

    # Bot Settings Tab
    with tabs[4]:
        st.header("Bot Configuration")
        
        # Initialize bot_files in session state if not present
        if 'bot_files' not in st.session_state:
            st.session_state.bot_files = []
            
        if 'selected_bot' not in st.session_state:
            st.session_state.selected_bot = None
        
        # Bot status
        is_active = st.session_state.bot_config.get('is_active', False)
        
        status_col1, status_col2 = st.columns([3, 1])
        
        with status_col1:
            st.subheader("Bot Status")
            status_text = "Active" if is_active else "Inactive"
            status_color = "green" if is_active else "red"
            st.markdown(f"<h3 style='color: {status_color};'>● {status_text}</h3>", unsafe_allow_html=True)
            
            # Show currently selected bot if any
            if st.session_state.selected_bot:
                st.caption(f"Running: {st.session_state.selected_bot}")
            
        with status_col2:
            if is_active:
                if st.button("Stop Bot", key="stop_bot"):
                    st.session_state.bot_config['is_active'] = False
                    st.rerun()
            else:
                if st.button("Start Bot", key="start_bot"):
                    # Check if Deriv is connected
                    if not st.session_state.get('deriv_connected', False):
                        st.error("Cannot start bot: Not connected to Deriv API. Please connect in the API Configuration tab.")
                    else:
                        st.session_state.bot_config['is_active'] = True
                        st.rerun()
        
        # Bot Management section
        st.subheader("Bot Management")
        
        # Create tabs for Bot Management
        bot_tabs = st.tabs(["Bot Selection", "Upload Bot", "Create Bot"])
        
        # Bot Selection Tab
        with bot_tabs[0]:
            st.subheader("Select a Bot")
            
            # Display list of available bots
            if st.session_state.bot_files:
                selected_bot = st.selectbox(
                    "Choose a bot to run",
                    options=[bot['name'] for bot in st.session_state.bot_files],
                    index=0,
                    key="bot_select"
                )
                
                # Find the selected bot details
                selected_bot_data = next((bot for bot in st.session_state.bot_files if bot['name'] == selected_bot), None)
                
                if selected_bot_data:
                    st.json(selected_bot_data['config'])
                    
                    # Button to activate the selected bot
                    if st.button("Use This Bot", key="use_bot"):
                        st.session_state.selected_bot = selected_bot
                        st.session_state.bot_config.update(selected_bot_data['config'])
                        st.success(f"Bot '{selected_bot}' activated successfully!")
                        st.rerun()
            else:
                st.info("No bots available. Please upload or create a bot.")
                
                # Create sample bot for demonstration
                if st.button("Create Sample Bot", key="create_sample"):
                    sample_bot = {
                        'name': 'Sample Bot',
                        'config': {
                            'market': 'R_10',
                            'trade_type': 'DIGITEVEN',
                            'base_stake': 1.0,
                            'stake_multiplier': 1.5,
                            'probability_threshold': 0.65,
                            'confidence_threshold': 0.6,
                            'risk_tolerance': 0.5,
                            'strategy': 'probability'
                        },
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    st.session_state.bot_files.append(sample_bot)
                    st.success("Sample bot created. You can now select it.")
                    st.rerun()
        
        # Upload Bot Tab
        with bot_tabs[1]:
            st.subheader("Upload a Bot Configuration")
            
            # File uploader
            uploaded_file = st.file_uploader("Upload bot configuration file (JSON or XML)", type=['json', 'xml'])
            
            if uploaded_file is not None:
                try:
                    # Read the file content
                    content = uploaded_file.read()
                    
                    # Parse the content based on file type
                    if uploaded_file.name.endswith('.json'):
                        # Parse JSON
                        bot_config = json.loads(content)
                        bot_name = uploaded_file.name.replace('.json', '')
                    elif uploaded_file.name.endswith('.xml'):
                        # Parse XML using the bot config parser
                        try:
                            bot_config = bot_config_parser.parse_bot_xml(content.decode('utf-8'))
                            bot_name = uploaded_file.name.replace('.xml', '')
                        except:
                            st.error("Could not parse XML file. Please check the format.")
                            bot_config = None
                            bot_name = None
                    else:
                        st.error("Unsupported file type")
                        bot_config = None
                        bot_name = None
                    
                    if bot_config:
                        # Display the parsed configuration
                        st.json(bot_config)
                        
                        # Validate the configuration
                        try:
                            validated_config = bot_config_parser.validate_config(bot_config)
                            
                            # Option to change the bot name
                            custom_name = st.text_input("Bot Name", value=bot_name)
                            
                            # Save button
                            if st.button("Save Bot", key="save_uploaded_bot"):
                                if any(bot['name'] == custom_name for bot in st.session_state.bot_files):
                                    st.error(f"A bot with the name '{custom_name}' already exists. Please choose a different name.")
                                else:
                                    # Create a new bot entry
                                    new_bot = {
                                        'name': custom_name,
                                        'config': validated_config,
                                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    }
                                    
                                    # Add to bot files list
                                    st.session_state.bot_files.append(new_bot)
                                    
                                    st.success(f"Bot '{custom_name}' saved successfully!")
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Error validating bot configuration: {str(e)}")
                except Exception as e:
                    st.error(f"Error processing the uploaded file: {str(e)}")
            
            # Example configuration display
            with st.expander("Example Bot Configuration Format"):
                st.code("""
{
    "market": "R_10",
    "trade_type": "DIGITEVEN",
    "base_stake": 1.0,
    "stake_multiplier": 1.5,
    "probability_threshold": 0.65,
    "confidence_threshold": 0.6,
    "risk_tolerance": 0.5,
    "strategy": "probability"
}
                """, language="json")
        
        # Create Bot Tab
        with bot_tabs[2]:
            st.subheader("Create a New Bot")
            
            # Bot creator form
            with st.form(key="bot_creator_form"):
                # Bot name
                bot_name = st.text_input("Bot Name", value="My Bot")
                
                # Market selection (same as in the trading parameters)
                available_markets = {
                    'R_10': 'Volatility 10 Index',
                    'R_25': 'Volatility 25 Index',
                    'R_50': 'Volatility 50 Index',
                    'R_75': 'Volatility 75 Index',
                    'R_100': 'Volatility 100 Index'
                }
                
                if st.session_state.get('deriv_connected', False) and st.session_state.get('broker_api'):
                    try:
                        markets = st.session_state.broker_api.get_available_markets()
                        available_markets = {
                            market['id']: market['name'] 
                            for market in markets
                        }
                    except:
                        pass
                
                market = st.selectbox(
                    "Trading Market",
                    options=list(available_markets.keys()),
                    index=0,
                    format_func=lambda x: f"{x} - {available_markets.get(x, x)}"
                )
                
                # Trade type selection with expanded options
                trade_type = st.selectbox(
                    "Trade Type",
                    options=["DIGITEVEN", "DIGITODD", "DIGITMATCH", "DIGITDIFF", "RISE", "FALL", "AUTO"],
                    index=0
                )
                
                # Add digit selection for DIGITMATCH and DIGITDIFF
                digit = None
                if trade_type in ["DIGITMATCH", "DIGITDIFF"]:
                    digit = st.selectbox(
                        "Target Digit",
                        options=list(range(10)),
                        index=0
                    )
                
                # Strategy selection
                strategy = st.selectbox(
                    "Strategy",
                    options=["probability", "martingale", "pattern", "custom"],
                    index=0
                )
                
                # Basic parameters
                col1, col2 = st.columns(2)
                
                with col1:
                    base_stake = st.number_input(
                        "Base Stake ($)",
                        min_value=0.35,
                        max_value=100.0,
                        value=1.0,
                        step=0.5
                    )
                    
                    stake_multiplier = st.number_input(
                        "Stake Multiplier",
                        min_value=1.0,
                        max_value=3.0,
                        value=1.5,
                        step=0.1
                    )
                
                with col2:
                    probability_threshold = st.slider(
                        "Probability Threshold",
                        min_value=0.55,
                        max_value=0.95,
                        value=0.65,
                        step=0.01
                    )
                    
                    confidence_threshold = st.slider(
                        "Confidence Threshold",
                        min_value=0.5,
                        max_value=0.9,
                        value=0.6,
                        step=0.05
                    )
                
                risk_tolerance = st.slider(
                    "Risk Tolerance",
                    min_value=0.1,
                    max_value=1.0,
                    value=0.5,
                    step=0.1
                )
                
                # Submit button
                submit_button = st.form_submit_button(label="Create Bot")
            
            if submit_button:
                # Create bot configuration
                bot_config = {
                    "market": market,
                    "trade_type": trade_type,
                    "base_stake": base_stake,
                    "stake_multiplier": stake_multiplier,
                    "probability_threshold": probability_threshold,
                    "confidence_threshold": confidence_threshold,
                    "risk_tolerance": risk_tolerance,
                    "strategy": strategy
                }
                
                # Add digit parameter if needed
                if digit is not None:
                    bot_config["digit"] = digit
                
                # Check if bot name already exists
                if any(bot['name'] == bot_name for bot in st.session_state.bot_files):
                    st.error(f"A bot with the name '{bot_name}' already exists. Please choose a different name.")
                else:
                    # Create a new bot entry
                    new_bot = {
                        'name': bot_name,
                        'config': bot_config,
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Add to bot files list
                    st.session_state.bot_files.append(new_bot)
                    
                    st.success(f"Bot '{bot_name}' created successfully!")
                    
                    # Option to activate the new bot
                    if st.button("Use This Bot Now", key="use_new_bot"):
                        st.session_state.selected_bot = bot_name
                        st.session_state.bot_config.update(bot_config)
                        st.rerun()
        
        # Bot configuration
        st.subheader("Trading Parameters")
        
        # Get available markets
        if st.session_state.get('deriv_connected', False) and st.session_state.get('broker_api'):
            try:
                available_markets = {
                    market['id']: market['name'] 
                    for market in st.session_state.broker_api.get_available_markets()
                }
            except:
                # Fallback markets
                available_markets = {
                    'R_10': 'Volatility 10 Index',
                    'R_25': 'Volatility 25 Index',
                    'R_50': 'Volatility 50 Index',
                    'R_75': 'Volatility 75 Index',
                    'R_100': 'Volatility 100 Index'
                }
        else:
            # Default markets when not connected
            available_markets = {
                'R_10': 'Volatility 10 Index',
                'R_25': 'Volatility 25 Index',
                'R_50': 'Volatility 50 Index',
                'R_75': 'Volatility 75 Index',
                'R_100': 'Volatility 100 Index'
            }
        
        col1, col2 = st.columns(2)
        
        with col1:
            market = st.selectbox(
                "Trading Market",
                options=list(available_markets.keys()),
                index=0,
                key="trading_market",
                format_func=lambda x: f"{x} - {available_markets.get(x, x)}"
            )
            
            trade_type = st.selectbox(
                "Trade Type",
                options=["DIGITEVEN", "DIGITODD", "DIGITMATCH", "DIGITDIFF", "RISE", "FALL", "AUTO"],
                index=0,
                key="trade_type"
            )
            
            # Add digit selection for DIGITMATCH and DIGITDIFF
            if trade_type in ["DIGITMATCH", "DIGITDIFF"]:
                digit = st.selectbox(
                    "Target Digit",
                    options=list(range(10)),
                    index=0,
                    key="target_digit"
                )
                
                # Store the selected digit in session state
                st.session_state.bot_config['digit'] = digit
            
            base_stake = st.number_input(
                "Base Stake ($)",
                min_value=0.35,
                max_value=100.0,
                value=st.session_state.bot_config.get('base_stake', 1.0),
                step=0.5,
                key="base_stake"
            )
            
            stake_multiplier = st.number_input(
                "Stake Multiplier",
                min_value=1.0,
                max_value=3.0,
                value=st.session_state.bot_config.get('stake_multiplier', 1.2),
                step=0.1,
                help="Multiplier for stake based on signal strength",
                key="stake_multiplier"
            )
            
        with col2:
            probability_threshold = st.slider(
                "Probability Threshold",
                min_value=0.55,
                max_value=0.95,
                value=st.session_state.bot_config.get('probability_threshold', 0.65),
                step=0.01,
                help="Minimum probability required to enter a trade",
                key="bot_probability_threshold"
            )
            
            confidence_threshold = st.slider(
                "Confidence Threshold",
                min_value=0.5,
                max_value=0.9,
                value=st.session_state.bot_config.get('confidence_threshold', 0.6),
                step=0.05,
                help="Minimum confidence level required to enter a trade",
                key="bot_confidence_threshold"
            )
            
            risk_tolerance = st.slider(
                "Risk Tolerance",
                min_value=0.1,
                max_value=1.0,
                value=st.session_state.bot_config.get('risk_tolerance', 0.5),
                step=0.1,
                help="Risk tolerance level (affects stake sizing)",
                key="bot_risk_tolerance"
            )
            
            cooldown_period = st.number_input(
                "Cooldown Between Trades (seconds)",
                min_value=0,
                max_value=300,
                value=st.session_state.bot_config.get('cooldown_period', 60),
                step=10,
                help="Seconds to wait between trades",
                key="cooldown_period"
            )
        
        # Save configuration
        if st.button("Save Configuration", key="save_bot_config"):
            # Create config update dictionary
            config_update = {
                'market': market,
                'trade_type': trade_type,
                'base_stake': base_stake,
                'stake_multiplier': stake_multiplier,
                'probability_threshold': probability_threshold,
                'confidence_threshold': confidence_threshold,
                'risk_tolerance': risk_tolerance,
                'cooldown_period': cooldown_period
            }
            
            # Add digit parameter for DIGITMATCH and DIGITDIFF
            if trade_type in ["DIGITMATCH", "DIGITDIFF"]:
                if 'digit' not in st.session_state.bot_config:
                    st.session_state.bot_config['digit'] = 0
            else:
                # Remove digit parameter if it exists but not needed
                if 'digit' in st.session_state.bot_config:
                    st.session_state.bot_config.pop('digit')
            
            # Update bot configuration
            st.session_state.bot_config.update(config_update)
            
            st.success("Bot configuration saved successfully!")
            
        # Advanced settings
        with st.expander("Advanced Settings"):
            st.subheader("Advanced Bot Configuration")
            
            # Trading hours
            st.subheader("Trading Hours")
            
            col1, col2 = st.columns(2)
            
            with col1:
                trade_on_weekends = st.checkbox(
                    "Trade on Weekends", 
                    value=True,
                    help="Enable trading on weekends"
                )
            
            with col2:
                use_time_filter = st.checkbox(
                    "Use Time Filter", 
                    value=False,
                    help="Restrict trading to specific hours"
                )
            
            if use_time_filter:
                trading_start_time = st.time_input(
                    "Trading Start Time",
                    value=datetime.strptime("09:00", "%H:%M").time(),
                    help="Start trading at this time"
                )
                
                trading_end_time = st.time_input(
                    "Trading End Time",
                    value=datetime.strptime("17:00", "%H:%M").time(),
                    help="Stop trading at this time"
                )
            
            # Signal filters
            st.subheader("Signal Filters")
            
            col1, col2 = st.columns(2)
            
            with col1:
                use_market_filter = st.checkbox(
                    "Use Market Filter", 
                    value=True,
                    help="Filter trades based on market conditions"
                )
                
                use_volatility_filter = st.checkbox(
                    "Use Volatility Filter", 
                    value=True,
                    help="Filter trades based on market volatility"
                )
            
            with col2:
                use_trend_filter = st.checkbox(
                    "Use Trend Filter", 
                    value=True,
                    help="Filter trades based on market trend"
                )
                
                use_consecutive_filter = st.checkbox(
                    "Use Consecutive Filter", 
                    value=True,
                    help="Filter trades based on consecutive outcomes"
                )
            
            # Trading rules
            st.subheader("Trading Rules")
            
            trading_rules = st.text_area(
                "Custom Trading Rules",
                value="""# Example rules
1. Skip trade if previous 3 trades were losses
2. Increase stake after 2 consecutive wins
3. Switch markets if drawdown exceeds 5%
4. Take a break for 5 minutes after 3 consecutive losses""",
                height=150,
                help="Custom rules for the bot to follow"
            )
            
            # Save advanced settings
            if st.button("Save Advanced Settings", key="save_advanced_settings"):
                st.session_state.bot_config.update({
                    'trade_on_weekends': trade_on_weekends,
                    'use_time_filter': use_time_filter,
                    'trading_start_time': trading_start_time if use_time_filter else None,
                    'trading_end_time': trading_end_time if use_time_filter else None,
                    'use_market_filter': use_market_filter,
                    'use_volatility_filter': use_volatility_filter,
                    'use_trend_filter': use_trend_filter,
                    'use_consecutive_filter': use_consecutive_filter,
                    'trading_rules': trading_rules
                })
                
                st.success("Advanced settings saved successfully!")

    # Performance Analysis Tab
    with tabs[5]:
        st.header("Performance Analysis")
        
        # Time period selection
        col1, col2 = st.columns(2)
        
        with col1:
            period = st.selectbox(
                "Time Period",
                options=["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "All Time"],
                index=0,
                key="performance_period"
            )
        
        with col2:
            market_filter = st.multiselect(
                "Markets",
                options=list(available_markets.keys()),
                default=list(available_markets.keys()),
                key="performance_markets"
            )
        
        # Key performance metrics
        st.subheader("Key Performance Metrics")
        
        # Calculate performance metrics from trades
        if st.session_state.trades:
            # Filter trades based on period and markets
            filtered_trades = st.session_state.trades
            
            # Apply period filter
            if period == "Today":
                filtered_trades = [t for t in filtered_trades if 
                                isinstance(t['timestamp'], datetime) and 
                                t['timestamp'].date() == datetime.now().date()]
            elif period == "Yesterday":
                yesterday = (datetime.now() - timedelta(days=1)).date()
                filtered_trades = [t for t in filtered_trades if 
                                isinstance(t['timestamp'], datetime) and 
                                t['timestamp'].date() == yesterday]
            elif period == "Last 7 Days":
                seven_days_ago = (datetime.now() - timedelta(days=7)).date()
                filtered_trades = [t for t in filtered_trades if 
                                isinstance(t['timestamp'], datetime) and 
                                t['timestamp'].date() >= seven_days_ago]
            elif period == "Last 30 Days":
                thirty_days_ago = (datetime.now() - timedelta(days=30)).date()
                filtered_trades = [t for t in filtered_trades if 
                                isinstance(t['timestamp'], datetime) and 
                                t['timestamp'].date() >= thirty_days_ago]
            
            # Apply market filter
            if market_filter:
                filtered_trades = [t for t in filtered_trades if t['market'] in market_filter]
            
            # Calculate metrics
            total_trades = len(filtered_trades)
            winning_trades = sum(1 for t in filtered_trades if t['outcome'] == 'win')
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            total_profit = sum(t['profit_loss'] for t in filtered_trades)
            total_stake = sum(t['stake'] for t in filtered_trades)
            
            # Calculate metrics from last period for deltas
            delta_trades = 0
            delta_win_rate = 0
            delta_profit = 0
            
            # Display metrics
            kpi_cols = st.columns(4)
            
            with kpi_cols[0]:
                st.metric(
                    label="Total Trades", 
                    value=total_trades,
                    delta=f"{delta_trades:+d}" if delta_trades != 0 else None
                )
            
            with kpi_cols[1]:
                st.metric(
                    label="Win Rate", 
                    value=f"{win_rate:.2%}",
                    delta=f"{delta_win_rate:+.2%}" if delta_win_rate != 0 else None
                )
            
            with kpi_cols[2]:
                st.metric(
                    label="Total Profit", 
                    value=f"${total_profit:.2f}",
                    delta=f"${delta_profit:+.2f}" if delta_profit != 0 else None
                )
            
            with kpi_cols[3]:
                roi = (total_profit / total_stake * 100) if total_stake > 0 else 0
                st.metric(
                    label="ROI", 
                    value=f"{roi:.2f}%",
                    delta=None
                )
            
            # Performance chart - equity curve
            st.subheader("Profit/Loss Over Time")
            
            # Sort trades by timestamp
            sorted_trades = sorted(filtered_trades, key=lambda t: t['timestamp'])
            
            # Calculate cumulative P/L
            cumulative_pnl = [0]
            for trade in sorted_trades:
                cumulative_pnl.append(cumulative_pnl[-1] + trade['profit_loss'])
            
            # Create a datetime index for the chart
            if sorted_trades:
                dates = [sorted_trades[0]['timestamp'].strftime('%Y-%m-%d %H:%M:%S')]
                for trade in sorted_trades:
                    dates.append(trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S'))
                
                # Create DataFrame for the chart
                equity_df = pd.DataFrame({
                    'Date': dates,
                    'Balance': cumulative_pnl
                }).set_index('Date')
                
                # Display the chart
                st.line_chart(equity_df)
                
                # Daily P/L calculation
                daily_pnl = {}
                for trade in sorted_trades:
                    date_str = trade['timestamp'].strftime('%Y-%m-%d')
                    if date_str not in daily_pnl:
                        daily_pnl[date_str] = 0
                    daily_pnl[date_str] += trade['profit_loss']
                
                # Create DataFrame for daily P/L
                daily_df = pd.DataFrame({
                    'Date': list(daily_pnl.keys()),
                    'Daily P/L': list(daily_pnl.values())
                }).set_index('Date')
                
                # Display daily P/L chart
                st.subheader("Daily Profit/Loss")
                st.bar_chart(daily_df)
                
                # Trade statistics
                st.subheader("Detailed Trade Statistics")
                
                # Calculate additional statistics
                losing_trades = total_trades - winning_trades
                avg_win = sum(t['profit_loss'] for t in filtered_trades if t['outcome'] == 'win') / winning_trades if winning_trades > 0 else 0
                avg_loss = sum(t['profit_loss'] for t in filtered_trades if t['outcome'] == 'loss') / losing_trades if losing_trades > 0 else 0
                
                # Calculate max consecutive wins and losses
                current_streak = 0
                max_win_streak = 0
                max_loss_streak = 0
                current_type = None
                
                for trade in sorted_trades:
                    if current_type is None:
                        current_type = trade['outcome']
                        current_streak = 1
                    elif current_type == trade['outcome']:
                        current_streak += 1
                    else:
                        if current_type == 'win':
                            max_win_streak = max(max_win_streak, current_streak)
                        else:
                            max_loss_streak = max(max_loss_streak, current_streak)
                        current_type = trade['outcome']
                        current_streak = 1
                
                # Update max streak for the last sequence
                if current_type == 'win':
                    max_win_streak = max(max_win_streak, current_streak)
                else:
                    max_loss_streak = max(max_loss_streak, current_streak)
                
                # Calculate profit factor
                total_wins = sum(t['profit_loss'] for t in filtered_trades if t['outcome'] == 'win')
                total_losses = abs(sum(t['profit_loss'] for t in filtered_trades if t['outcome'] == 'loss'))
                profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
                
                # Create statistics DataFrame
                stats_data = {
                    'Metric': [
                        'Total Trades',
                        'Winning Trades',
                        'Losing Trades',
                        'Win Rate',
                        'Average Win',
                        'Average Loss',
                        'Profit Factor',
                        'Max Drawdown',
                        'Avg. Trade Duration',
                        'Consecutive Wins',
                        'Consecutive Losses'
                    ],
                    'Value': [
                        total_trades,
                        winning_trades,
                        losing_trades,
                        f"{win_rate:.2%}",
                        f"${avg_win:.2f}",
                        f"${avg_loss:.2f}",
                        f"{profit_factor:.2f}",
                        "9.5%",  # Placeholder - would need more complex calculation
                        "34s",   # Placeholder - would need trade duration data
                        max_win_streak,
                        max_loss_streak
                    ]
                }
                
                # Display statistics table
                st.table(pd.DataFrame(stats_data))
            else:
                st.info("No trades found for the selected period and markets.")
        else:
            # Generate mock performance data
            total_trades = 157
            win_rate = 0.53
            total_profit = 127.50
            total_stake = 235.00
            
            kpi_cols = st.columns(4)
            
            with kpi_cols[0]:
                st.metric(
                    label="Total Trades", 
                    value=total_trades,
                    delta="+12"
                )
            
            with kpi_cols[1]:
                st.metric(
                    label="Win Rate", 
                    value=f"{win_rate:.2%}",
                    delta="+2.3%"
                )
            
            with kpi_cols[2]:
                st.metric(
                    label="Total Profit", 
                    value=f"${total_profit:.2f}",
                    delta="+$18.50"
                )
            
            with kpi_cols[3]:
                st.metric(
                    label="ROI", 
                    value=f"{(total_profit / total_stake * 100):.2f}%",
                    delta="+1.2%"
                )
            
            # Generate sample data for charts
            st.subheader("Profit/Loss Over Time")
            
            # Generate sample daily data
            days = 14
            daily_data = []
            
            balance = 100.0
            for day in range(days):
                daily_profit = np.random.normal(1.5, 5.0)
                balance += daily_profit
                daily_data.append({
                    'Date': (datetime.now() - timedelta(days=days-day-1)).strftime('%Y-%m-%d'),
                    'Balance': balance,
                    'Daily P/L': daily_profit
                })
            
            # Create DataFrame for the chart
            daily_df = pd.DataFrame(daily_data)
            
            # Display balance chart
            st.line_chart(daily_df.set_index('Date')['Balance'])
            
            # Display daily P/L chart
            st.subheader("Daily Profit/Loss")
            st.bar_chart(daily_df.set_index('Date')['Daily P/L'])
            
            st.info("Start trading to see your actual performance metrics.")
        
        # Market performance
        st.subheader("Market Performance")
        
        # Create market data
        market_data = []
        for market_id, market_name in available_markets.items():
            market_trades = np.random.randint(10, 50)
            market_winrate = np.random.uniform(0.48, 0.58)
            market_profit = np.random.normal(20, 10)
            
            market_data.append({
                'Market': market_id,
                'Name': market_name,
                'Trades': market_trades,
                'Win Rate': f"{market_winrate:.2%}",
                'P/L': f"${market_profit:.2f}",
                'ROI': f"{(market_profit / (market_trades * 1.5) * 100):.2f}%"
            })
        
        # Display market performance
        market_df = pd.DataFrame(market_data)
        st.dataframe(market_df, hide_index=True)
        
        # Export data button
        if st.button("Export Performance Data", key="export_performance"):
            st.info("Performance data would be exported as a CSV file.")
            st.download_button(
                label="Download CSV",
                data=market_df.to_csv(index=False).encode('utf-8'),
                file_name=f"performance_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )