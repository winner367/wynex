import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from auth_api import auth_api, UserRole

def format_datetime(dt):
    if isinstance(dt, str):
        try:
            return datetime.fromisoformat(dt).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return dt
    elif isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)

def show_admin_dashboard():
    if not auth_api.is_admin():
        st.error("Access denied. Admin privileges required.")
        return

    st.title("Admin Dashboard")
    
    # Navigation
    admin_pages = ["User Management", "Performance Analytics", "System Settings"]
    selected_page = st.sidebar.selectbox("Admin Navigation", admin_pages)
    
    if selected_page == "User Management":
        show_user_management()
    elif selected_page == "Performance Analytics":
        show_performance_analytics()
    else:
        show_system_settings()

def show_user_management():
    st.header("User Management")
    
    # Get all users
    users = auth_api.get_all_users()
    
    # Convert users to DataFrame for display
    user_table = []
    for user in users:
        user_table.append({
            'Email': user['email'],
            'Name': user['name'],
            'Role': user['role'],
            'Status': 'Active' if user.get('is_active', True) else 'Suspended',
            'Last Login': format_datetime(user.get('last_login')),
            'Created At': format_datetime(user.get('created_at'))
        })
    
    df = pd.DataFrame(user_table)
    
    # User actions
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.dataframe(df, use_container_width=True)
    
    with col2:
        st.subheader("User Actions")
        selected_email = st.selectbox("Select User", [user['email'] for user in users])
        
        if st.button("Suspend User"):
            if selected_email == auth_api.get_current_user()['email']:
                st.error("Cannot suspend your own account!")
            else:
                auth_api.suspend_user(selected_email)
                st.success(f"User {selected_email} has been suspended")
                st.rerun()
        
        if st.button("Activate User"):
            auth_api.activate_user(selected_email)
            st.success(f"User {selected_email} has been activated")
            st.rerun()
        
        if st.button("Reset Password"):
            # In production, implement secure password reset
            st.warning("Password reset functionality not implemented")

def show_performance_analytics():
    st.header("Performance Analytics")
    
    # Get all users
    users = auth_api.get_all_users()
    
    # Aggregate performance data
    performance_data = []
    for user in users:
        if user['performance_metrics']:
            metrics = user['performance_metrics']
            performance_data.append({
                'User': user['email'],
                'Total Trades': metrics['total_trades'],
                'Win Rate': metrics['win_rate'],
                'Profit/Loss': metrics['profit_loss'],
                'Last Trade': metrics['last_trade_date']
            })
    
    if performance_data:
        df = pd.DataFrame(performance_data)
        
        # Overall statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Users", len(users))
        with col2:
            st.metric("Active Traders", len([u for u in users if u['is_active']]))
        with col3:
            total_profit = sum(u['performance_metrics']['profit_loss'] for u in users if u['performance_metrics'])
            st.metric("Total System Profit/Loss", f"${total_profit:,.2f}")
        
        # Performance charts
        st.subheader("User Performance Comparison")
        fig = px.bar(df, x='User', y='Profit/Loss', title='User Profit/Loss Comparison')
        st.plotly_chart(fig, use_container_width=True)
        
        fig = px.scatter(df, x='Total Trades', y='Win Rate', 
                        size='Profit/Loss', hover_data=['User'],
                        title='Trading Performance Analysis')
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed performance table
        st.subheader("Detailed Performance Metrics")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No performance data available yet")

def show_system_settings():
    st.header("System Settings")
    
    # Risk Management Settings
    st.subheader("Risk Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_daily_loss = st.number_input(
            "Maximum Daily Loss ($)",
            min_value=0.0,
            value=100.0,
            step=10.0
        )
        
        max_position_size = st.number_input(
            "Maximum Position Size ($)",
            min_value=0.0,
            value=1000.0,
            step=100.0
        )
    
    with col2:
        max_trades_per_day = st.number_input(
            "Maximum Trades per Day",
            min_value=0,
            value=20,
            step=1
        )
        
        required_win_rate = st.slider(
            "Minimum Required Win Rate",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            format="%.2f"
        )
    
    # API Settings
    st.subheader("API Configuration")
    
    deriv_app_id = st.text_input(
        "Deriv App ID",
        value="71514",
        type="password"
    )
    
    # Save settings
    if st.button("Save Settings"):
        # In production, implement settings storage
        st.success("Settings saved successfully!")

# Add back button functionality
def add_back_button():
    if st.sidebar.button("← Back"):
        # Get the current page from session state
        current_page = st.session_state.get('admin_page', 'User Management')
        # Find the previous page
        pages = ["User Management", "Performance Analytics", "System Settings"]
        current_index = pages.index(current_page)
        if current_index > 0:
            st.session_state.admin_page = pages[current_index - 1]
            st.rerun() 