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
    df = pd.DataFrame(rows).transpose()[['Value', 'Invested', 'Cash', 'PnL', 'Deposited']]
    st.dataframe(df.style.format("{:.0f} €"), use_container_width=True)


def datatable_asset(s: pd.Series, ptf):
    rows = {}
    for (ptf, classs, asset, _) in s.loc[pd.IndexSlice[ptf, ['Commodities', 'Cryptocurrency', 'Equities', 'Fixed Income'], :, 'Market']].index:
        rows[classs, asset] = {
            'Market': assets.loc[asset]['PriceFmt'].format(s[ptf, classs, asset, 'Market']),
            'PRU': assets.loc[asset]['PriceFmt'].format(s[ptf, classs, asset, 'PRU']),
            'Position': assets.loc[asset]['PositionFmt'].format(s[ptf, classs, asset, 'Position']),
            'Value': assets.loc[asset]['ValueFmt'].format(s[ptf, classs, asset, 'Value']),
            'Invested': assets.loc[asset]['ValueFmt'].format(s[ptf, classs, asset, 'Invested']),
            'PnL': assets.loc[asset]['ValueFmt'].format(s[ptf, classs, asset, 'PnL']),
        }
    df = pd.DataFrame(rows).transpose()[['Market', 'PRU', 'Position', 'Value', 'Invested', 'PnL']]
    st.dataframe(df, use_container_width=True)


def scatter_ptf(df, ptf):
    rows = {
        'Value': df.loc[:, pd.IndexSlice[ptf, ['Cash', 'Commodities', 'Cryptocurrency', 'Equities', 'Fixed Income'], 'All', 'ValueEUR']].sum(axis=1),
        'Invested': df.loc[:, pd.IndexSlice[ptf, ['Commodities', 'Cryptocurrency', 'Equities', 'Fixed Income'], 'All', 'InvestedEUR']].sum(axis=1),
        'Cash': df.loc[:, pd.IndexSlice[ptf, 'Cash', 'All', 'ValueEUR']],
        'PnL': df.loc[:, pd.IndexSlice[ptf, ['Cash', 'Commodities', 'Cryptocurrency', 'Equities', 'Fixed Income'], 'All', 'PnLEUR']].sum(axis=1),
        'Deposited': -df.loc[:, pd.IndexSlice[ptf, 'Deposit', 'All', 'InvestedEUR']],
    }
    fig = go.Figure()
    for metric in rows:
        fig.add_trace(go.Scatter(x=rows[metric].index, y=rows[metric].values, name=metric))
    st.plotly_chart(fig, use_container_width=True)


def scatter_asset(df, ptf, metric):
    fig = go.Figure()
    for (ptf, classs, asset, _) in df.iloc[-1].loc[pd.IndexSlice[ptf, ['Commodities', 'Cryptocurrency', 'Equities', 'Fixed Income'], :, metric]].index:
        fig.add_trace(go.Scatter(x=df.index, y=df[ptf, classs, asset, metric].values, name=asset))
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

    # st.header("Portfolio repartition")
    # pie_col, _, lin_col = st.columns([2, 1, 4])
    # with pie_col:
    #     pie_ptf(data.iloc[-1], ['ZEN', 'DMA'])
    # with lin_col:
    #     stack_ptf(data, ['ZEN', 'DMA'])

    # st.header("Portfolio performance")
    # bar_ptf(data.iloc[-1], ['All', 'ZEN', 'DMA'])


with zen_tab:
    st.header("ZEN overview")
    datatable_ptf(data.iloc[-1], ['ZEN'])
    scatter_ptf(data, 'ZEN')
    
    st.header("ZEN assets")
    datatable_asset(data.iloc[-1], 'ZEN')
    metric = st.radio('Metric: ', ['Value', 'Invested', 'PnL'], horizontal=True, key=f'ZEN asset graph')
    scatter_asset(data, 'ZEN', metric)

    # st.header("ZEN repartition")
    # pie_col, _, lin_col = st.columns([2, 1, 4])
    # with pie_col:
    #     pie_asset(data.iloc[-1], 'ZEN')
    # with lin_col:
    #     stack_asset(data, 'ZEN')

    # st.header("ZEN performance")
    # bar_asset(data.iloc[-1], 'ZEN')
