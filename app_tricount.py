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

column = {}
checks = {}
with st.sidebar:
    for col in ['Total', 'Lucie', 'Vincent']:
        column[col] = st.checkbox(col, value=True)
    st.markdown('---')
    for period in detail.keys():
        checks[period] = st.checkbox(period)

columns = [column for column, check in column.items() if check==True]
periods = [period for period, check in checks.items() if check==True]

if len(periods) == 0:
    st.write('Tick the periods')
else:
    # st.table(result[periods].style.format("{:.2f}"))

    cols = st.columns(len(periods))
    for i, col in enumerate(cols):
        with col:
            st.subheader(periods[i])
            df = detail[periods[i]][columns].sort_index().replace(0, pd.NA)
            st.table(df.style.format("{:.0f}").highlight_null(props="color: transparent;"))

            st.table(detail[periods[i]][columns].sort_index().replace(0, pd.NA).assign(hack='').set_index('hack').style.format("{:.0f}").highlight_null(props="color: transparent;"))
