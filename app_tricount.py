import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from api_tricount import build_data
data = build_data()


st.set_page_config(layout="wide")
st.title("Tricount Dashboard")
st.write("""
<style>
button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
    # font-weight: bold;
    font-size: 24px;
}
</style>
""", unsafe_allow_html=True)


tab3, tab2, tab1 = st.tabs(["2023", "2022", "2021"])

with tab3:
    st.dataframe(data.loc[2023,1,:].style.format("{:.2f}"))
