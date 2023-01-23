

import streamlit as st
import plotly.graph_objects as go

import pandas as pd
idx = pd.IndexSlice

from api import build_data
data = build_data()


st.set_page_config(layout="wide")
st.title("Portfolio Dashboard")
st.write("""
<style>
button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
    font-weight: bold;
    font-size: 32px;
}
</style>
""", unsafe_allow_html=True)



def datatable_ptf(data, ptfs):
    df = data[['ValueEUR', 'InvestedEUR', 'CashEUR', 'PnLEUR', 'DepositEUR']]
    s = df.iloc[-1]
    rows = {}
    for ptf in ptfs:
        rows[ptf] = s[:, ptf, 'All']
    st.dataframe(pd.concat(rows, axis=1).transpose().style.format("{:.0f}"), use_container_width=True)

def datatable_asset(data, ptf):
    # df = data[['Cotation', 'Currency', 'PRU', 'Amount', 'ValueEUR', 'InvestedEUR', 'PnLEUR']]
    df = data[['PRU', 'Amount', 'ValueEUR', 'InvestedEUR', 'PnLEUR']]
    s = df.iloc[-1]
    rows = {}
    for asset in s['ValueEUR', ptf, :].index[0:-1]:
        rows[asset] = s[:, ptf, asset]
    st.dataframe(pd.concat(rows, axis=1).transpose().style.format("{:.0f}"), use_container_width=True)


def scatter_ptf(df, ptf):
    metrics = ['ValueEUR', 'InvestedEUR', 'CashEUR', 'PnLEUR', 'DepositEUR']
    fig = go.Figure()
    for metric in metrics:
        fig.add_trace(go.Scatter(x=df.index, y=df[metric, ptf, 'All'], name=metric))
    st.plotly_chart(fig, use_container_width=True)

def scatter_asset(df, ptf):
    assets = df.iloc[-1].loc[idx['ValueEUR', ptf, :]].index
    fig = go.Figure()
    for asset in assets:
        fig.add_trace(go.Scatter(x=df.index, y=df['ValueEUR', ptf, asset], name=asset))
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
    assets = s.loc[idx['ValueEUR', ptf, :]].index[0:-1]
    value = []
    label = []
    for asset in assets:
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
    for asset in df.iloc[-1]['ValueEUR', ptf, :].index[0:-1]:
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
    for asset in s['ValueEUR', ptf, :].index[0:-1]:
        value.append(s['PnLEUR', ptf, asset])
        label.append(asset)
    fig = go.Figure(go.Bar(x=value, y=label, orientation='h'))
    st.plotly_chart(fig, use_container_width=True)




all_tab, zen_tab, dma_tab = st.tabs(["All", "ZEN", "DMA"])

with all_tab:
    st.header("Portfolio overview")
    datatable_ptf(data, ['All', 'ZEN', 'DMA'])
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
    datatable_ptf(data, ['ZEN'])
    scatter_ptf(data, 'ZEN')
    datatable_asset(data, 'ZEN')
    scatter_asset(data, 'ZEN')

    st.header("ZEN repartition")
    pie_col, _, lin_col = st.columns([2, 1, 4])
    with pie_col:
        pie_asset(data.iloc[-1], 'ZEN')
    with lin_col:
        stack_asset(data, 'ZEN')

    st.header("ZEN performance")
    bar_asset(data.iloc[-1], 'ZEN')
