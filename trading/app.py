import streamlit as st
from datetime import datetime
st.set_page_config(layout="wide", page_title="Trading results")
import plotly.graph_objects as go

from api import *

# @st.cache_data
@st.experimental_memo
def get_data():
    return fetch_data()

trades = get_data()

print("""
    # ------------------------------------
    # Build Streamlit Web page
    # of Trading Dashboard 
    # ------------------------------------
""")
st.write("""
<style>
button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
    # font-weight: bold;
    font-size: 24px;
}
</style>
""", unsafe_allow_html=True)

st.title("Trading Dashboard")
# title, refresh = st.columns([9, 1])
# with title:
#     st.title("Trading Dashboard")
# with refresh:
#     if st.button('Refresh'):
#         st.cache_data.clear()

manage_axis, _, manage_graph = st.columns([5,1,5])

with manage_axis:
    st.subheader("Manage axis")
    date_range = trades['Date']
    start_date = datetime(trades['Date'].min().year, trades['Date'].min().month, trades['Date'].min().day)
    ended_date = datetime(trades['Date'].max().year, trades['Date'].max().month, trades['Date'].max().day)
    date_range = st.slider("Date slider to filter data", value=(start_date, ended_date), format="YYYY-MM-DD")
    h_axis = st.radio("Horizontal axis graph", ['per Trade', 'per Date'], horizontal=True, key="Horizontal axis")
    v_axis = st.radio("Vertical axis graph", ['in €', 'in %', 'in RR'], horizontal=True, key="Vertical axis")
    trades_filtered = trades.loc[(trades['Date'] >= date_range[0]) & (trades['Date'] <= date_range[1])]

with manage_graph:
    st.subheader("Choose period results")
    periods = []
    for period in ['Globally', 'Yearly', 'Monthly', 'Weekly']:
        if st.checkbox(period):
            periods.append(period)

st.markdown('---')


st.subheader("Graph")
print("""\n
    #################
    ##### GRAPH #####
    #################
""")
trades_graph = trades_filtered.copy()
if h_axis == 'per Date':
    trades_graph = convert_to_time(trades_graph)

if v_axis == 'in €':
    print("Vertical axis in €")
elif v_axis == 'in %':
    print("Vertical axis in %")
    trades_graph['Gain'] = trades_graph['Gain'] / 10000 * 100
elif v_axis == 'in RR':
    print("Vertical axis in RR")
    trades_graph['Gain'] = trades_graph['Gain'] / trades_graph['Risque']
else: 
    print("Vertical axis ERROR")    
      
if h_axis == 'per Trade':
    print("Horizontal axis per Trade")
    trades_graph = compute_stats(trades_graph, only_balances=True)
elif h_axis == 'per Date':
    print("Horizontal axis per Date")
    trades_graph = compute_stats(trades_graph.reset_index(), only_balances=True).set_index(('Date', '.'))
else: 
    print("Horizontal axis ERROR")

print("trades_graph:", trades_graph.shape)

fig = go.Figure(go.Bar(x=trades_graph.index.to_list(), y=trades_graph[('Gain', 'Globally')].to_list(), name='Trades'))
for col in trades_graph['Balance'].columns.get_level_values(0):
    for period in periods:
        if period in col:
            fig.add_trace(go.Scatter(x=trades_graph.index.to_list(), y=trades_graph[('Balance', col)].to_list(), name=col.replace('_', ' ')))
if v_axis == 'in €':
    fig.update_yaxes(tickformat = '.0f', ticksuffix=' €', dtick = 50)
elif v_axis == 'in %':
    fig.update_yaxes(tickformat = '.1f', ticksuffix=' %', dtick = 0.5)
elif v_axis == 'in RR':
    fig.update_yaxes(tickformat = '.0f', ticksuffix=' RR', dtick = 1)
st.plotly_chart(fig, use_container_width=True)  


st.subheader("Stats")
print("""\n
    #################
    ##### STATS #####
    #################
""")

trades_stats = compute_stats(trades_filtered).ffill().iloc[-1]
STATS = [m+r for r in ['TP', 'BE', 'SL'] for m in ['Count', 'Rate', 'Payoff']]
stats = pd.DataFrame(columns=['Balance', 'Count', 'WinRate', 'PayoffRatio', *STATS])

for metric, period in trades_stats.index:
    if metric in stats.columns and period.split('_')[0] in periods:
        stats.loc[period, metric] = trades_stats[(metric, period)]

stats['WinRate'] = stats['RateTP']
stats['PayoffRatio'] = stats['PayoffTP'] / -stats['PayoffSL']

print("stats:", stats.shape)

st.table(stats.iloc[::-1].style
    .format({
        "Balance": "{:.0f} €",
        "Count": "{:.0f}",
        "WinRate": "{:.0%}",
        "PayoffRatio": "{:.2f}",
        "CountTP": "{:.0f}",
        "RateTP": "{:.0%}",
        "PayoffTP": "{:.0f} €",
        "CountBE": "{:.0f}",
        "RateBE": "{:.0%}",
        "PayoffBE": "{:.0f} €",
        "CountSL": "{:.0f}",
        "RateSL": "{:.0%}",
        "PayoffSL": "{:.0f} €",
    })
    .highlight_null(props="color: transparent;")
    .set_properties(**{'font-weight': 'bold'}, subset=['Balance', 'Count', 'WinRate', 'PayoffRatio'])
) 
    