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
trades = {}

print("""
    # ------------------------------------
    # Build Streamlit Web page
    # of Trading Dashboard 
    # ------------------------------------
""")
st.title("Trading Dashboard")
st.write("""
<style>
button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
    # font-weight: bold;
    font-size: 24px;
}
</style>
""", unsafe_allow_html=True)


manage_axis, _, manage_graph = st.columns([5,1,5])

with manage_axis:
    st.subheader("Manage horizontal axis")
    start_date = datetime(trades_date.index.min().year, trades_date.index.min().month, trades_date.index.min().day)
    ended_date = datetime(trades_date.index.max().year, trades_date.index.max().month, trades_date.index.max().day)
    date = st.slider("Slider to filter data", value=(start_date, ended_date), format="YY-MM-DD", label_visibility='collapsed')
    # axis = st.radio("Horizontal axis graph", ['per Trade', 'per Date'], horizontal=True, key="Horizontal axis", label_visibility='hidden')
    # if axis == 'per Trade':
    trades['unit'] = trades_unit.loc[(trades_unit['Date', '.'] > date[0]) & (trades_unit['Date', '.'] < date[1])]
    # elif axis == 'per Date':
    trades['date'] = trades_date.loc[date[0]:date[1]]
    # else: 
    #     print("Horizontal axis ERROR")

with manage_graph:
    st.subheader("Choose period results")
    PERIOD = ['Globally', 'Yearly', 'Monthly', 'Weekly']
    periods = []
    for period in PERIOD:
        if st.checkbox(period):
            periods.append(period)


def show_graph(trades:pd.DataFrame):
    fig = go.Figure(go.Bar(x=trades.index.to_list(), y=trades[('Gain', 'Globally')].to_list(), name='Trades'))
    for col in trades['Balance'].columns.get_level_values(0):
        for period in periods:
            if period in col:
                fig.add_trace(go.Scatter(x=trades.index.to_list(), y=trades[('Balance', col)].to_list(), name=col.replace('_', ' ')))
    st.plotly_chart(fig, use_container_width=True)  

stats_tab, graph_unit, graph_date = st.tabs(['Statistics', 'Graph per Trade', 'Graph per Date'])
with graph_unit:
    show_graph(trades['unit'])
with graph_date:
    show_graph(trades['date'])
with stats_tab:
    COL = [m+r for r in ['TP', 'BE', 'SL'] for m in ['Count', 'Rate', 'Payoff']]
    stats = pd.DataFrame()
    s = trades['unit'].ffill().iloc[-1]
    for metric, period in s.index:
        print('', metric, period)
        for p in periods:
            if p in period and metric in ['Count', 'Balance', *COL]:
                print('  ', metric, period)
                if pd.notna(s[('Count', period)]):
                    print('    ', metric, period)
                    stats.loc[period, metric] = s[(metric, period)]
    
    print("\n", stats.columns, "\n\n")
    if stats.shape == (0,0):
        st.write("No data to display")
    else:
        stats['WinRate'] = "{:.2f %}".format(stats['RateTP'])
        stats['PayoffRatio'] = stats['PayoffTP'] / -stats['PayoffSL']
        stats['Balance'] = "{:.2f €}".format(stats['Balance'])
        for col in stats.columns:
            if 'Count' in col:
                stats[col] = "{:.0f}".format(stats[col])
            elif 'Rate' in col:
                stats[col] = "{:.2f %}".format(stats[col])
            elif 'Payoff' in col:
                stats[col] = "{:.2f %}".format(stats[col])
        st.dataframe(stats[['Balance', 'Count', 'WinRate', 'PayoffRatio', *COL]])