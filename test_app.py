import streamlit as st

st.title("Binary Options Trading Bot - Test Page")

st.write("If you can see this, Streamlit is working correctly!")

# Display some basic UI elements
st.header("Basic UI Test")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Input Test")
    name = st.text_input("Enter your name")
    if name:
        st.write(f"Hello, {name}!")
    
    number = st.number_input("Enter a number", min_value=0, max_value=100, value=50)
    st.write(f"You entered: {number}")

with col2:
    st.subheader("Widget Test")
    option = st.selectbox("Choose an option", ["Option 1", "Option 2", "Option 3"])
    st.write(f"You selected: {option}")
    
    if st.button("Click me!"):
        st.success("Button clicked!")

# Test a simple chart
st.header("Chart Test")
import pandas as pd
import numpy as np

chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['A', 'B', 'C']
)

st.line_chart(chart_data)