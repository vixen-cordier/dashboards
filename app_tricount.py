import warnings
import numpy as np
import pandas as pd
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

people_x = {}
period_x = {}
with st.sidebar:
    for people in ['Total', 'Lucie', 'Vincent']:
        people_x[people] = st.checkbox(people, value=True)
    st.markdown('---')
    for period in detail.keys():
        period_x[period] = st.checkbox(period)

peoples = [people for people, check in people_x.items() if check==True]
periods = [period for period, check in period_x.items() if check==True]

if len(periods) == 0:
    st.write('Tick the periods')
else:
    for people in peoples:
        st.subheader(people)

        st.write("Synthèse")
        rows = {}
        for period in periods:
            rows[period] = result[period][people]
        df = pd.concat(rows, axis=1).transpose()
        st.table(df
            .style
            .format("{:.0f}")
            .highlight_null(props="color: transparent;")
            .bar(subset=df.columns, align='mid', color=['#d65f5f', '#5fba7d'])
        )

        st.write("Budget")
        rows = {}
        for period in periods:
            rows[period] = postes[period][people]
        df = pd.concat(rows, axis=1).transpose()
        st.table(df
            .style
            .format("{:.0f}")
            .highlight_null(props="color: transparent;")
            .bar(subset=df.columns, align='mid', color=['#d65f5f', '#5fba7d'])
        )

    st.subheader("Détails des catégories")
    rows = {}
    for i, period in enumerate(periods):
        if len(peoples) > 1:
            rows[i] = pd.Series(dtype='int')
        rows[period] = detail[period][peoples]
    st.table(pd.concat(rows, axis=1).style.format("{:.0f}").highlight_null(props="color: transparent;"))