import streamlit as st
from datetime import datetime
st.set_page_config(layout="wide", page_title="Trading results")
import plotly.graph_objects as go

from api import *

@st.experimental_memo 
def get_data():
    print("""
    # ------------------------------------
    # Fetch trades, build calculated trades
    # for Trading Dashboard 
    # ------------------------------------
    """)
    trades_unit = fetch_data()
    trades_date = convert_to_time(trades_unit)
    trades_unit = compute_stats(trades_unit)
    trades_date = compute_stats(trades_date.reset_index(), all_stats=False).set_index(('Date', '.'))
    return trades_unit, trades_date

trades_unit, trades_date = get_data()


print("""
    # ------------------------------------
    # Build Streamlit Web page
    # of Trading Dashboard 
    # ------------------------------------
""")
st.title("Trading Dashboard")

manage_axis, _, manage_graph = st.columns([5,1,5])

with manage_axis:
    st.subheader("Manage horizontal axis")
    start_date = datetime(trades_date.index.min().year, trades_date.index.min().month, trades_date.index.min().day)
    ended_date = datetime(trades_date.index.max().year, trades_date.index.max().month, trades_date.index.max().day)
    date = st.slider("Slider to filter data", value=(start_date, ended_date), format="YY-MM-DD", label_visibility='collapsed')
    axis = st.radio("Horizontal axis graph", ['per Trade', 'per Date'], horizontal=True, key="Horizontal axis", label_visibility='hidden')
    if axis == 'per Trade':
        trades = trades_unit.loc[(trades_unit['Date', '.'] > date[0]) & (trades_unit['Date', '.'] < date[1])]
    elif axis == 'per Date':
        trades = trades_date.loc[date[0]:date[1]]
    else: 
        print("Horizontal axis ERROR")

with manage_graph:
    st.subheader("Choose period results")
    PERIOD = ['Globally', 'Yearly', 'Monthly', 'Weekly']
    periods = []
    for period in PERIOD:
        if st.checkbox(period):
            periods.append(period)
        


fig = go.Figure(go.Bar(x=trades.index.to_list(), y=trades[('Gain', 'Globally')].to_list(), name='Trades'))
for col in trades['Balance'].columns.get_level_values(0):
    for period in periods:
        if period in col:
            fig.add_trace(go.Scatter(x=trades.index.to_list(), y=trades[('Balance', col)].to_list(), name=col.replace('_', ' ')))
st.plotly_chart(fig, use_container_width=True)

stats = pd.DataFrame()
s = trades.ffill().iloc[-1]
for metric, period in trades.columns:
    for p in ['Globally', 'Yearly', 'Monthly', 'Weekly']:
        if p in period and metric in ['Count', 'Balance', 'CountTP', 'RateTP', 'PayoffTP', 'CountBE', 'RateBE', 'PayoffBE', 'CountSL', 'RateSL', 'PayoffSL']:
            stats.loc[period, metric] = s[(metric, period)]
stats['WinRate'] = stats['RateTP']
stats['PayoffRatio'] = stats['PayoffTP'] / -stats['PayoffSL']