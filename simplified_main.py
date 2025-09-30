import streamlit as st
import pandas as pd
import numpy as np
import traceback
import sys
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(
    page_title="Binary Options Trading Bot",
    page_icon="📈",
    layout="wide"
)

# Page title
st.title("Binary Options Trading Bot")

# Initialize session state if needed
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
    
if 'auth' not in st.session_state:
    st.session_state.auth = {
        'logged_in': False,
        'user': None
    }

# Initialize mock market data
markets = {
    'R_10': {'name': 'Volatility 10 Index', 'volatility': 0.7, 'speed': 0.8},
    'R_25': {'name': 'Volatility 25 Index', 'volatility': 0.85, 'speed': 0.7},
    'R_50': {'name': 'Volatility 50 Index', 'volatility': 0.9, 'speed': 0.6},
    'R_75': {'name': 'Volatility 75 Index', 'volatility': 0.95, 'speed': 0.5},
    'R_100': {'name': 'Volatility 100 Index', 'volatility': 1.0, 'speed': 0.4},
}

# Create tabs for the main interface
tabs = st.tabs([
    "Dashboard", 
    "API Configuration", 
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
        st.metric(
            label="Demo Account", 
            value="$1,000.00", 
            delta="+$0.00"
        )
    
    with status_col3:
        st.subheader("Today's P/L")
        st.metric(
            label="Profit/Loss", 
            value="$0.00", 
            delta="0.00%"
        )
    
    # Recent trades
    st.subheader("Recent Trades")
    
    # Mock trade data
    if not st.session_state.trades:
        # Create some sample trades
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

# API Configuration Tab
with tabs[1]:
    st.header("API Configuration")
    
    # Connection status
    st.subheader("Connection Status")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        is_connected = st.session_state.get('deriv_connected', False)
        conn_status = "Connected" if is_connected else "Disconnected"
        conn_color = "green" if is_connected else "red"
        st.markdown(f"<h3 style='color: {conn_color};'>● {conn_status}</h3>", unsafe_allow_html=True)
    
    with col2:
        if is_connected:
            if st.button("Disconnect", key="disconnect_button"):
                st.session_state.deriv_connected = False
                st.rerun()
        else:
            if st.button("Connect", key="connect_button"):
                st.session_state.deriv_connected = True
                st.rerun()
    
    # API settings
    st.subheader("API Settings")
    
    api_key = st.text_input(
        "API Key", 
        value=st.session_state.get('api_key', ''),
        type="password",
        help="Enter your Deriv API key"
    )
    
    demo_account = st.checkbox(
        "Use Demo Account", 
        value=True,
        help="Trade with virtual funds"
    )
    
    # Save API settings
    if st.button("Save API Settings", key="save_api_settings"):
        st.session_state.api_key = api_key
        st.session_state.demo_account = demo_account
        st.success("API settings saved successfully!")

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
        
        # Generate sample digit history
        digit_history = list(np.random.randint(0, 10, size=20))
        
        st.write("Recent Digits:")
        # Display digits in a horizontal bar
        st.write(" ".join([str(d) for d in digit_history[-10:]]))
        
        # Probability calculation
        even_count = sum(1 for d in digit_history[-10:] if d % 2 == 0)
        even_prob = even_count / 10
        odd_prob = 1 - even_prob
        
        # Display probabilities
        prob_df = pd.DataFrame({
            'Type': ['DIGITEVEN', 'DIGITODD'],
            'Probability': [even_prob, odd_prob],
            'Confidence': [0.7, 0.7],
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
            # Create simulation results
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
                
            # Calculate potential maximum loss
            max_possible_loss = base_stake * (multiplier ** max_steps - 1) / (multiplier - 1)
                
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
    
    # Bot status
    is_active = st.session_state.bot_config.get('is_active', False)
    
    status_col1, status_col2 = st.columns([3, 1])
    
    with status_col1:
        st.subheader("Bot Status")
        status_text = "Active" if is_active else "Inactive"
        status_color = "green" if is_active else "red"
        st.markdown(f"<h3 style='color: {status_color};'>● {status_text}</h3>", unsafe_allow_html=True)
        
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
    
    # Bot configuration
    st.subheader("Trading Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        market = st.selectbox(
            "Trading Market",
            options=list(markets.keys()),
            index=0,
            key="trading_market"
        )
        
        trade_type = st.selectbox(
            "Trade Type",
            options=["DIGITEVEN", "DIGITODD", "AUTO"],
            index=0,
            key="trade_type"
        )
        
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
        st.session_state.bot_config.update({
            'market': market,
            'trade_type': trade_type,
            'base_stake': base_stake,
            'stake_multiplier': stake_multiplier,
            'probability_threshold': probability_threshold,
            'confidence_threshold': confidence_threshold,
            'risk_tolerance': risk_tolerance,
            'cooldown_period': cooldown_period
        })
        
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
            options=list(markets.keys()),
            default=list(markets.keys()),
            key="performance_markets"
        )
    
    # Key performance metrics
    st.subheader("Key Performance Metrics")
    
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
    
    # Performance chart
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
    
    # Trade statistics
    st.subheader("Detailed Trade Statistics")
    
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
            int(total_trades * win_rate),
            total_trades - int(total_trades * win_rate),
            f"{win_rate:.2%}",
            "$1.95",
            "$1.00",
            "1.87",
            "9.5%",
            "34s",
            "5",
            "3"
        ]
    }
    
    # Display statistics table
    st.table(pd.DataFrame(stats_data))
    
    # Market performance
    st.subheader("Market Performance")
    
    # Create market data
    market_data = []
    for market_id, market_info in markets.items():
        market_trades = np.random.randint(10, 50)
        market_winrate = np.random.uniform(0.48, 0.58)
        market_profit = np.random.normal(20, 10)
        
        market_data.append({
            'Market': market_id,
            'Name': market_info['name'],
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