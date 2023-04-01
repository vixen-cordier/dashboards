import streamlit as st
st.set_page_config(layout="wide", page_title="Trading results")
import plotly.graph_objects as go

from api import *

@st.experimental_memo 
def get_data():
    return build_data()

trades = get_data()

st.title("Trading Dashboard")

fig = go.Figure(go.Bar(x=trades.index.to_list(), y=trades['Gain'].to_list()))
st.plotly_chart(fig, use_container_width=True)