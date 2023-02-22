import pandas as pd
import streamlit as st
st.set_page_config(layout="wide", page_title="Portfolio Cordier")
import plotly.graph_objects as go

from api_portfolio import build_data

@st.experimental_memo
def get_data(): 
    return build_data()

data, assets = get_data()

st.title("Portfolio Dashboard")
st.write("""
<style>
button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
    # font-weight: bold;
    font-size: 24px;
}
</style>
""", unsafe_allow_html=True)


def datatable_ptf(s: pd.Series, ptfs):
    rows = {}
    for ptf in ptfs:
        rows[ptf] = {
            'Value': s.loc[pd.IndexSlice[ptf, ['Cash', 'Commodities', 'Cryptocurrency', 'Equities', 'Fixed Income'], 'All', 'ValueEUR']].sum(),
            'Invested': s.loc[pd.IndexSlice[ptf, ['Commodities', 'Cryptocurrency', 'Equities', 'Fixed Income'], 'All', 'InvestedEUR']].sum(),
            'Cash': s.loc[pd.IndexSlice[ptf, 'Cash', 'All', 'ValueEUR']],
            'PnL': s.loc[pd.IndexSlice[ptf, ['Cash', 'Commodities', 'Cryptocurrency', 'Equities', 'Fixed Income'], 'All', 'PnLEUR']].sum(),
            'Deposited': -s.loc[pd.IndexSlice[ptf, 'Deposit', 'All', 'InvestedEUR']],
        }
    st.dataframe(pd.DataFrame(rows).transpose().style.format("{:.0f} €"), use_container_width=True)


def datatable_asset(s: pd.Series, ptf):
    rows = {}
    for asset in np.unique(df.columns.get_level_values(1)):
        rows[ptf] = {
            'Value': s.loc[pd.IndexSlice[ptf, ['Cash', 'Commodities', 'Cryptocurrency', 'Equities', 'Fixed Income'], 'All', 'ValueEUR']].sum(),
            'Invested': s.loc[pd.IndexSlice[ptf, ['Commodities', 'Cryptocurrency', 'Equities', 'Fixed Income'], 'All', 'InvestedEUR']].sum(),
            'Cash': s.loc[pd.IndexSlice[ptf, 'Cash', 'All', 'ValueEUR']],
            'PnL': s.loc[pd.IndexSlice[ptf, ['Cash', 'Commodities', 'Cryptocurrency', 'Equities', 'Fixed Income'], 'All', 'PnLEUR']].sum(),
            'Deposited': -s.loc[pd.IndexSlice[ptf, 'Deposit', 'All', 'InvestedEUR']],
        }
    st.dataframe(pd.DataFrame(rows).transpose().style.format("{:.0f} €"), use_container_width=True)

    cols = ['Class', 'Market', 'PRU', 'Amount', 'Value', 'Invested', 'PnL']
    # s_fmt = s[['Format']] 
    s = s[cols]
    rows = {}
    for asset in s['Value', ptf, :].index:
        # print(asset)
        # print(s_fmt['Format', ptf, asset])
        rows[asset] = s[:, ptf, asset]#.map(str(s_fmt['Format', ptf, asset]).format)
    df = pd.concat(rows, axis=1).transpose()
    st.dataframe(df[cols].style
        .format({('Amount', 'Value', 'Invested', 'PnL'): '{:.0f}'})
        .highlight_null(props="color: transparent;")
        , use_container_width=True)
    # st.table(pd.concat(rows, axis=1).transpose().style.format("{:.0f}"))


def scatter_ptf(df, ptf):
    metrics = ['ValueEUR', 'InvestedEUR', 'CashEUR', 'PnLEUR', 'DepositedEUR']
    fig = go.Figure()
    for metric in metrics:
        fig.add_trace(go.Scatter(x=df.index, y=df[metric, ptf, 'All'], name=metric))
    st.plotly_chart(fig, use_container_width=True)

def scatter_asset(df, ptf, metric):
    fig = go.Figure()
    for asset in data[metric, ptf].columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[metric, ptf, asset], name=asset))
    st.plotly_chart(fig, use_container_width=True)


def pie_ptf(s, ptfs):
    value = []
    label = []
    for ptf in ptfs:
        value.append(s['ValueEUR', ptf, 'All'])
        label.append(ptf)
    value.append(s['CashEUR', 'All', 'All'])
    label.append('Cash')
    fig = go.Figure(go.Pie(values=value, labels=label))
    st.plotly_chart(fig, use_container_width=True)

def pie_asset(s, ptf):
    value = []
    label = []
    for asset in s['ValueEUR', ptf, :].index:
        if asset != 'All':
            value.append(s['ValueEUR', ptf, asset])
            label.append(asset)
    value.append(s['CashEUR', ptf, 'All'])
    label.append('Cash')
    fig = go.Figure(go.Pie(values=value, labels=label))
    st.plotly_chart(fig, use_container_width=True)


def stack_ptf(df, ptfs):
    fig = go.Figure()
    for ptf in ptfs:
        fig.add_trace(go.Scatter(x=df.index, y=df['ValueEUR', ptf, 'All'], name=ptf, stackgroup='one', groupnorm='percent'))
    fig.add_trace(go.Scatter(x=df.index, y=df['CashEUR', 'All', 'All'], name='Cash', stackgroup='one', groupnorm='percent'))
    st.plotly_chart(fig, use_container_width=True)

def stack_asset(df, ptf):
    fig = go.Figure()
    for asset in df['ValueEUR', ptf].columns:
        if asset != 'All':
            fig.add_trace(go.Scatter(x=df.index, y=df['ValueEUR', ptf, asset], name=asset, stackgroup='one', groupnorm='percent'))
    fig.add_trace(go.Scatter(x=df.index, y=df['CashEUR', ptf, 'All'], name='Cash', stackgroup='one', groupnorm='percent'))
    st.plotly_chart(fig, use_container_width=True)


def bar_ptf(s, ptfs):
    value = []
    label = []
    for ptf in ptfs:
        value.append(s['PnLEUR', ptf, 'All'])
        label.append(ptf)
    fig = go.Figure(go.Bar(x=value, y=label, orientation='h'))
    st.plotly_chart(fig, use_container_width=True)

def bar_asset(s, ptf):
    value = []
    label = []
    for asset in s['ValueEUR', ptf, :].index:
        if asset != 'All':
            value.append(s['PnLEUR', ptf, asset])
            label.append(asset)
    fig = go.Figure(go.Bar(x=value, y=label, orientation='h'))
    st.plotly_chart(fig, use_container_width=True)




all_tab, zen_tab, dma_tab = st.tabs(["All", "ZEN", "DMA"])

with all_tab:
    st.header("Portfolio overview")
    datatable_ptf(data.iloc[-1], ['All', 'ZEN', 'DMA'])
    scatter_ptf(data, 'All')

    st.header("Portfolio repartition")
    pie_col, _, lin_col = st.columns([2, 1, 4])
    with pie_col:
        pie_ptf(data.iloc[-1], ['ZEN', 'DMA'])
    with lin_col:
        stack_ptf(data, ['ZEN', 'DMA'])

    st.header("Portfolio performance")
    bar_ptf(data.iloc[-1], ['All', 'ZEN', 'DMA'])


with zen_tab:
    st.header("ZEN overview")
    datatable_ptf(data.iloc[-1], ['ZEN'])
    scatter_ptf(data, 'ZEN')
    
    st.header("ZEN assets")
    datatable_asset(data.iloc[-1], 'ZEN')
    metric = st.radio('Metric: ', ['ValueEUR', 'InvestedEUR', 'PnLEUR'], horizontal=True, key=f'ZEN asset graph')
    scatter_asset(data, 'ZEN', metric)

    st.header("ZEN repartition")
    pie_col, _, lin_col = st.columns([2, 1, 4])
    with pie_col:
        pie_asset(data.iloc[-1], 'ZEN')
    with lin_col:
        stack_asset(data, 'ZEN')

    st.header("ZEN performance")
    bar_asset(data.iloc[-1], 'ZEN')
