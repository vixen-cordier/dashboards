import streamlit as st
from datetime import datetime
st.set_page_config(layout="wide", page_title="Trading results")
import plotly.graph_objects as go

from api import *

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
    st.subheader("Manage axis")
    date_range = trades['Date']
    start_date = datetime(trades['Date'].min().year, trades['Date'].min().month, trades['Date'].min().day)
    ended_date = datetime(trades['Date'].max().year, trades['Date'].max().month, trades['Date'].max().day)
    date_range = st.slider("Date slider to filter data", value=(start_date, ended_date), format="YY-MM-DD", label_visibility='collapsed')
    h_axis = st.radio("Horizontal axis graph", ['per Trade', 'per Date'], horizontal=True, key="Horizontal axis")
    v_axis = st.radio("Vertical axis graph", ['in €', 'in %', 'in RR' ], horizontal=True, key="Vertical axis")
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
      
if h_axis == 'per Trade':
    trades_graph = compute_stats(trades_filtered)
elif h_axis == 'per Date':
    trades_graph = convert_to_time(trades_filtered)
    trades_graph = compute_stats(trades_graph.reset_index(), only_balances=True).set_index(('Date', '.'))
else: 
    print("Horizontal axis ERROR")
print("trades_graph:", trades_graph.shape)

fig = go.Figure(go.Bar(x=trades_graph.index.to_list(), y=trades_graph[('Gain', 'Globally')].to_list(), name='Trades'))
for col in trades_graph['Balance'].columns.get_level_values(0):
    for period in periods:
        if period in col:
            fig.add_trace(go.Scatter(x=trades_graph.index.to_list(), y=trades_graph[('Balance', col)].to_list(), name=col.replace('_', ' ')))
st.plotly_chart(fig, use_container_width=True)  


st.subheader("Stats")
print("""\n
    #################
    ##### STATS #####
    #################
""")

trades_stats = compute_stats(trades_filtered).ffill().iloc[-1]
METRICS = [m+r for r in ['TP', 'BE', 'SL'] for m in ['Count', 'Rate', 'Payoff']]
stats = pd.DataFrame(columns=['Balance', 'Count', 'WinRate', 'PayoffRatio', *METRICS])

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
    