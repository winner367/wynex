import streamlit as st
import pandas as pd
import numpy as np
import traceback
import sys

st.set_page_config(
    page_title="Binary Options Trading Bot",
    page_icon="📈",
    layout="wide"
)

st.title("Binary Options Trading Bot - Debug Mode")

# Try importing the components
try:
    from probability_calculator import ProbabilityCalculator, MarketAnalyzer
    st.success("✅ Successfully imported probability_calculator")
except Exception as e:
    st.error(f"❌ Error importing probability_calculator: {str(e)}")
    st.code(traceback.format_exc())
    
try:
    from strategy_engine import StrategyEngine
    st.success("✅ Successfully imported strategy_engine")
except Exception as e:
    st.error(f"❌ Error importing strategy_engine: {str(e)}")
    st.code(traceback.format_exc())
    
try:
    from bot_config_parser import BotConfigParser
    st.success("✅ Successfully imported bot_config_parser")
except Exception as e:
    st.error(f"❌ Error importing bot_config_parser: {str(e)}")
    st.code(traceback.format_exc())
    
try:
    from broker_api import create_broker_api
    st.success("✅ Successfully imported broker_api")
except Exception as e:
    st.error(f"❌ Error importing broker_api: {str(e)}")
    st.code(traceback.format_exc())
    
try:
    from utils import generate_robot_svg, apply_conditional_formatting
    st.success("✅ Successfully imported utils")
except Exception as e:
    st.error(f"❌ Error importing utils: {str(e)}")
    st.code(traceback.format_exc())
    
try:
    from auth_utils import is_authenticated, is_admin, get_current_user, login_user, register_user, verify_token
    st.success("✅ Successfully imported auth_utils")
except Exception as e:
    st.error(f"❌ Error importing auth_api: {str(e)}")
    st.code(traceback.format_exc())
    
try:
    from auth_pages import show_auth_ui, show_admin_panel
    st.success("✅ Successfully imported auth_pages")
except Exception as e:
    st.error(f"❌ Error importing auth_pages: {str(e)}")
    st.code(traceback.format_exc())

# Try initializing components
st.header("Component Initialization")

try:
    prob_calc = ProbabilityCalculator()
    st.success("✅ Successfully initialized ProbabilityCalculator")
except Exception as e:
    st.error(f"❌ Error initializing ProbabilityCalculator: {str(e)}")
    st.code(traceback.format_exc())
    
try:
    market_analyzer = MarketAnalyzer()
    st.success("✅ Successfully initialized MarketAnalyzer")
except Exception as e:
    st.error(f"❌ Error initializing MarketAnalyzer: {str(e)}")
    st.code(traceback.format_exc())
    
try:
    strategy_engine = StrategyEngine()
    st.success("✅ Successfully initialized StrategyEngine")
except Exception as e:
    st.error(f"❌ Error initializing StrategyEngine: {str(e)}")
    st.code(traceback.format_exc())
    
try:
    bot_config_parser = BotConfigParser()
    st.success("✅ Successfully initialized BotConfigParser")
except Exception as e:
    st.error(f"❌ Error initializing BotConfigParser: {str(e)}")
    st.code(traceback.format_exc())

# Package versions
st.header("Package Versions")
package_info = {
    "Python": sys.version,
    "Streamlit": st.__version__,
    "Pandas": pd.__version__,
    "NumPy": np.__version__
}

st.table(pd.DataFrame(list(package_info.items()), columns=["Package", "Version"]))

# Try creating some basic UI elements to make sure they work
st.header("Basic UI Test")

try:
    tabs = st.tabs(["Tab 1", "Tab 2", "Tab 3"])
    with tabs[0]:
        st.write("This is tab 1")
    with tabs[1]:
        st.write("This is tab 2")
    with tabs[2]:
        st.write("This is tab 3")
    st.success("✅ Successfully created tabs")
except Exception as e:
    st.error(f"❌ Error creating tabs: {str(e)}")
    st.code(traceback.format_exc())

try:
    col1, col2 = st.columns(2)
    with col1:
        st.write("Column 1")
    with col2:
        st.write("Column 2")
    st.success("✅ Successfully created columns")
except Exception as e:
    st.error(f"❌ Error creating columns: {str(e)}")
    st.code(traceback.format_exc())

st.header("Next Steps")
st.info("If all components initialize successfully, please proceed to run the main application.")