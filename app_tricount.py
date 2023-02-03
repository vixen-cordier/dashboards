from typing import Dict
import warnings
import pandas as pd
import gspread as gs 
import calendar as cd
import streamlit as st
import plotly.graph_objects as go
warnings.simplefilter(action='ignore', category=pd.core.common.SettingWithCopyWarning)

from api_tricount import *


@st.experimental_memo
def get_data():
    data, dict = fetch_data()
    data = build_data(data)
    detail = split_data(data, dict)
    postes, result = concat_data(detail, dict)
    return detail, postes, result

detail, postes, result = get_data()

print("""
    # --------------------------------- #
    # Build screen elements             #
    # --------------------------------- #
""")
# st.set_page_config(layout="wide")


st.title("Tricount Dashboard")

checks = {}
with st.sidebar:
    for period in detail.keys():
        checks[period] = st.checkbox(period)

periods = [period for period, check in checks.items() if check==True]

if len(periods) == 0:
    st.write('Tick the periods')
else:
    # st.table(result[periods].style.format("{:.2f}"))

    cols = st.columns(len(periods))
    for i, col in enumerate(cols):
        with col:
            st.header(periods[i])
            st.table(detail[periods[i]].style.format("{:.2f}"))